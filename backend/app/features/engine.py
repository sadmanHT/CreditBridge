"""
Feature Engineering Engine for CreditBridge

SYSTEM ROLE:
You are implementing a production-grade feature engineering engine
for an AI credit platform.

PROJECT:
CreditBridge — Feature Store Engine.

TASK FOR COPILOT AGENT:
Implement a FeatureEngine that:
1. Accepts:
   - borrower profile
   - recent raw_events
2. Produces a feature dict:
   - mobile_activity_score
   - transaction_volume_30d
   - activity_consistency
3. Deterministic logic only
4. Version features as:
   feature_set = "core_behavioral"
   feature_version = "v1"
5. Store features into model_features table
6. No model logic here

This engine transforms raw borrower data and events into structured features
for downstream AI models. All transformations are deterministic and versioned
for reproducibility and auditability.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics
import logging
from app.core.supabase import supabase
from app.core.repository import log_audit_event
from supabase import Client

# Setup logging for data quality warnings
logger = logging.getLogger(__name__)


class DataQualityWarning(Exception):
    """Raised when data quality issues are detected but computation can continue."""
    pass


@dataclass
class FeatureSet:
    """
    Represents a computed feature set for a borrower.
    
    Attributes:
        borrower_id: UUID of the borrower
        feature_set: Name of the feature set (e.g., "core_behavioral")
        feature_version: Version of feature computation logic
        features: Dictionary of computed feature values
        computed_at: Timestamp when features were computed
        source_event_count: Number of events used for feature computation
    """
    borrower_id: str
    feature_set: str
    feature_version: str
    features: Dict[str, Any]
    computed_at: str
    source_event_count: int


class FeatureEngine:
    """
    Production-grade feature engineering engine for credit scoring.
    
    This engine provides deterministic feature extraction from borrower profiles
    and raw event streams. All features are versioned and stored in the model_features
    table for reproducibility and auditability.
    
    Version: 1.0.0
    Feature Set: core_behavioral
    Feature Version: v1
    
    Attributes:
        feature_set: Name of the feature set ("core_behavioral")
        feature_version: Version of feature computation logic ("v1")
        lookback_days: Number of days to look back for event aggregation (default: 30)
    """
    
    def __init__(self, lookback_days: int = 30, client: Optional[Client] = None):
        """
        Initialize the FeatureEngine.
        
        Args:
            lookback_days: Number of days to look back for event aggregation (default: 30)
            client: Optional custom Supabase client (useful for testing with service role)
        """
        self.feature_set = "core_behavioral"
        self.feature_version = "v1"
        self.lookback_days = lookback_days
        self.client = client or supabase
    
    def compute_features(
        self,
        borrower_id: str,
        borrower_profile: Dict[str, Any],
        raw_events: Optional[List[Dict[str, Any]]] = None
    ) -> FeatureSet:
        """
        Compute behavioral features for a borrower.
        
        This method orchestrates feature extraction from borrower profile and
        raw events, producing a versioned feature set ready for model consumption.
        
        Args:
            borrower_id: UUID of the borrower
            borrower_profile: Dictionary containing borrower profile data
            raw_events: Optional list of raw event dictionaries. If None, will fetch from database.
            
        Returns:
            FeatureSet containing computed features with metadata
            
        Raises:
            ValueError: If borrower_id is empty or borrower_profile is invalid
            Exception: If feature computation fails
            
        Example:
            >>> engine = FeatureEngine(lookback_days=30)
            >>> features = engine.compute_features(
            ...     borrower_id="abc-123",
            ...     borrower_profile={"id": "abc-123", "phone": "1234567890"},
            ...     raw_events=[...]
            ... )
            >>> print(features.features["mobile_activity_score"])
        """
        # Input validation
        if not borrower_id:
            raise ValueError("borrower_id cannot be None or empty")
        
        if not borrower_profile:
            raise ValueError("borrower_profile cannot be None or empty")
        
        try:
            # DATA QUALITY: Track warnings for low quality data
            data_quality_warnings = []
            
            # Fetch raw events if not provided
            if raw_events is None:
                try:
                    raw_events = self._fetch_raw_events(borrower_id)
                except Exception as e:
                    # SAFETY: Never crash on missing events - use empty list
                    logger.warning(
                        f"[FeatureEngine] Failed to fetch raw events for {borrower_id}: {e}. "
                        "Using empty event list."
                    )
                    raw_events = []
                    data_quality_warnings.append("raw_events_fetch_failed")
            
            # DATA QUALITY: Warn if no events available
            if not raw_events or len(raw_events) == 0:
                logger.warning(
                    f"[FeatureEngine] No raw events found for borrower {borrower_id}. "
                    "Features will be computed with minimal data."
                )
                data_quality_warnings.append("no_raw_events")
            
            # Filter events within lookback window
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
            recent_events = self._filter_events_by_date(raw_events, cutoff_date)
            
            # DATA QUALITY: Warn if very few recent events
            if len(recent_events) < 5:
                logger.warning(
                    f"[FeatureEngine] Low event count ({len(recent_events)}) for borrower {borrower_id}. "
                    "Feature quality may be degraded."
                )
                data_quality_warnings.append(f"low_event_count_{len(recent_events)}")
            
            # Compute individual features with error handling
            features = {}
            
            # Feature 1: Mobile Activity Score (0-100)
            try:
                features["mobile_activity_score"] = self._compute_mobile_activity_score(
                    borrower_profile, recent_events
                )
                # DATA QUALITY: Validate range
                if not (0 <= features["mobile_activity_score"] <= 100):
                    logger.error(
                        f"[FeatureEngine] mobile_activity_score out of range: "
                        f"{features['mobile_activity_score']}. Clamping to [0, 100]."
                    )
                    features["mobile_activity_score"] = max(0, min(100, features["mobile_activity_score"]))
                    data_quality_warnings.append("mobile_score_out_of_range")
            except Exception as e:
                # SAFETY: Never crash - use safe default
                logger.error(f"[FeatureEngine] Failed to compute mobile_activity_score: {e}. Using default 0.")
                features["mobile_activity_score"] = 0.0
                data_quality_warnings.append("mobile_score_computation_failed")
            
            # Feature 2: Transaction Volume (30 days)
            try:
                features["transaction_volume_30d"] = self._compute_transaction_volume(
                    recent_events
                )
                # DATA QUALITY: Validate non-negative
                if features["transaction_volume_30d"] < 0:
                    logger.error(
                        f"[FeatureEngine] Negative transaction_volume_30d: "
                        f"{features['transaction_volume_30d']}. Setting to 0."
                    )
                    features["transaction_volume_30d"] = 0.0
                    data_quality_warnings.append("negative_transaction_volume")
            except Exception as e:
                # SAFETY: Never crash - use safe default
                logger.error(f"[FeatureEngine] Failed to compute transaction_volume_30d: {e}. Using default 0.")
                features["transaction_volume_30d"] = 0.0
                data_quality_warnings.append("transaction_volume_computation_failed")
            
            # Feature 3: Activity Consistency Score (0-100)
            try:
                features["activity_consistency"] = self._compute_activity_consistency(
                    recent_events
                )
                # DATA QUALITY: Validate range
                if not (0 <= features["activity_consistency"] <= 100):
                    logger.error(
                        f"[FeatureEngine] activity_consistency out of range: "
                        f"{features['activity_consistency']}. Clamping to [0, 100]."
                    )
                    features["activity_consistency"] = max(0, min(100, features["activity_consistency"]))
                    data_quality_warnings.append("consistency_score_out_of_range")
            except Exception as e:
                # SAFETY: Never crash - use safe default
                logger.error(f"[FeatureEngine] Failed to compute activity_consistency: {e}. Using default 0.")
                features["activity_consistency"] = 0.0
                data_quality_warnings.append("consistency_computation_failed")
            
            # Add metadata features
            features["event_count"] = len(recent_events)
            features["lookback_days"] = self.lookback_days
            features["has_phone"] = bool(borrower_profile.get("phone"))
            
            # DATA QUALITY: Add warnings to metadata
            features["data_quality_warnings"] = data_quality_warnings
            features["data_quality_score"] = self._compute_data_quality_score(data_quality_warnings)
            
            # DATA QUALITY: Log summary if warnings present
            if data_quality_warnings:
                logger.warning(
                    f"[FeatureEngine] Data quality warnings for borrower {borrower_id}: "
                    f"{', '.join(data_quality_warnings)} "
                    f"(quality_score={features['data_quality_score']:.2f})"
                )
            
            # Create FeatureSet object
            feature_set = FeatureSet(
                borrower_id=borrower_id,
                feature_set=self.feature_set,
                feature_version=self.feature_version,
                features=features,
                computed_at=datetime.now(timezone.utc).isoformat(),
                source_event_count=len(recent_events)
            )
            
            return feature_set
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to compute features for borrower {borrower_id}: {str(e)}")
    
    def _fetch_raw_events(self, borrower_id: str) -> List[Dict[str, Any]]:
        """
        Fetch raw events for a borrower from the database.
        
        Args:
            borrower_id: UUID of the borrower
            
        Returns:
            List of raw event dictionaries
            
        Raises:
            Exception: If database query fails
        """
        try:
            response = self.client.table("raw_events").select("*").eq(
                "borrower_id", borrower_id
            ).order("created_at", desc=True).limit(1000).execute()
            
            return response.data or []
            
        except Exception as e:
            raise Exception(f"Failed to fetch raw events: {str(e)}")
    
    def _filter_events_by_date(
        self,
        events: List[Dict[str, Any]],
        cutoff_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Filter events to include only those after cutoff date.
        
        Args:
            events: List of event dictionaries
            cutoff_date: Cutoff datetime (events before this are excluded)
            
        Returns:
            Filtered list of events
        """
        filtered = []
        
        for event in events:
            created_at_str = event.get("created_at")
            if not created_at_str:
                continue
            
            try:
                # Parse ISO timestamp
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                
                if created_at >= cutoff_date:
                    filtered.append(event)
                    
            except Exception:
                # Skip events with invalid timestamps
                continue
        
        return filtered
    
    def _compute_mobile_activity_score(
        self,
        borrower_profile: Dict[str, Any],
        events: List[Dict[str, Any]]
    ) -> float:
        """
        Compute mobile activity score (0-100).
        
        This score combines:
        - Phone number presence (20 points)
        - Event count (up to 50 points, 1 point per event, capped at 50)
        - Mobile-specific event types (up to 30 points)
        
        Args:
            borrower_profile: Borrower profile dictionary
            events: List of recent event dictionaries
            
        Returns:
            Mobile activity score between 0 and 100
        """
        score = 0.0
        
        # Component 1: Phone number presence (20 points)
        if borrower_profile.get("phone"):
            score += 20.0
        
        # Component 2: Event count (up to 50 points)
        event_count_score = min(len(events), 50)
        score += event_count_score
        
        # Component 3: Mobile-specific events (up to 30 points)
        mobile_event_types = ["app_open", "location_update", "mobile_payment", "sms_verification"]
        mobile_event_count = sum(
            1 for event in events
            if event.get("event_type") in mobile_event_types
        )
        mobile_score = min(mobile_event_count * 3, 30)
        score += mobile_score
        
        # Ensure score is within [0, 100]
        return min(max(score, 0.0), 100.0)
    
    def _compute_transaction_volume(self, events: List[Dict[str, Any]]) -> float:
        """
        Compute total transaction volume over the lookback period.
        
        This sums all transaction amounts from events with event_type="transaction".
        
        Args:
            events: List of recent event dictionaries
            
        Returns:
            Total transaction volume (sum of amounts)
        """
        total_volume = 0.0
        
        for event in events:
            # Only process transaction events
            if event.get("event_type") != "transaction":
                continue
            
            # Extract amount from event_data
            event_data = event.get("event_data", {})
            amount = event_data.get("amount", 0)
            
            # Convert to float and add to total
            try:
                total_volume += float(amount)
            except (TypeError, ValueError):
                # Skip invalid amounts
                continue
        
        return total_volume
    
    def _compute_activity_consistency(self, events: List[Dict[str, Any]]) -> float:
        """
        Compute activity consistency score (0-100).
        
        This score measures how consistently a borrower generates events over time.
        Higher scores indicate more regular activity patterns.
        
        Algorithm:
        1. Group events by day
        2. Calculate standard deviation of daily event counts
        3. Convert to consistency score (lower stddev = higher consistency)
        
        Args:
            events: List of recent event dictionaries
            
        Returns:
            Activity consistency score between 0 and 100
        """
        if len(events) == 0:
            return 0.0
        
        if len(events) == 1:
            return 50.0  # Single event = moderate consistency
        
        try:
            # Group events by day
            events_by_day = {}
            
            for event in events:
                created_at_str = event.get("created_at")
                if not created_at_str:
                    continue
                
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    day_key = created_at.date().isoformat()
                    
                    if day_key not in events_by_day:
                        events_by_day[day_key] = 0
                    
                    events_by_day[day_key] += 1
                    
                except Exception:
                    continue
            
            # Calculate daily event counts
            daily_counts = list(events_by_day.values())
            
            if len(daily_counts) < 2:
                return 50.0  # All events on same day = moderate consistency
            
            # Calculate mean and standard deviation
            mean_count = statistics.mean(daily_counts)
            stddev_count = statistics.stdev(daily_counts)
            
            # Convert to consistency score
            # Lower stddev relative to mean = higher consistency
            if mean_count == 0:
                return 0.0
            
            coefficient_of_variation = stddev_count / mean_count
            
            # Map coefficient of variation to 0-100 scale
            # CV of 0 = 100 (perfect consistency)
            # CV of 2+ = 0 (very inconsistent)
            consistency_score = max(0, 100 - (coefficient_of_variation * 50))
            
            return min(max(consistency_score, 0.0), 100.0)
            
        except Exception:
            # Return default on error
            return 50.0
    
    def save_features(self, feature_set: FeatureSet) -> Dict[str, Any]:
        """
        Save computed features to model_features table.
        
        This method persists the feature set to the database for use by
        downstream ML models and for audit trail purposes.
        
        Args:
            feature_set: FeatureSet object containing computed features
            
        Returns:
            Dictionary containing:
            - feature_id: UUID of the saved feature record
            - borrower_id: Borrower UUID
            - feature_set: Feature set name
            - feature_version: Feature version
            - status: "saved"
            
        Raises:
            ValueError: If feature_set is None
            Exception: If database insertion fails
            
        Example:
            >>> engine = FeatureEngine()
            >>> features = engine.compute_features(...)
            >>> result = engine.save_features(features)
            >>> print(result["feature_id"])
        """
        if not feature_set:
            raise ValueError("feature_set cannot be None")
        
        try:
            # Prepare feature record for database
            feature_record = {
                "borrower_id": feature_set.borrower_id,
                "feature_set": feature_set.feature_set,
                "feature_version": feature_set.feature_version,
                "features": feature_set.features,
                "computed_at": feature_set.computed_at,
                "source_event_count": feature_set.source_event_count
            }
            
            # Insert into model_features table
            response = self.client.table("model_features").insert(feature_record).execute()
            
            if not response.data:
                raise Exception("Failed to insert features: No data returned from database")
            
            saved_feature = response.data[0]
            feature_id = saved_feature.get("id")
            
            # Log audit event for compliance
            log_audit_event(
                action="features_computed",
                entity_type="model_features",
                entity_id=feature_id,
                metadata={
                    "borrower_id": feature_set.borrower_id,
                    "feature_set": feature_set.feature_set,
                    "feature_version": feature_set.feature_version,
                    "source_event_count": feature_set.source_event_count,
                    "feature_names": list(feature_set.features.keys())
                }
            )
            
            return {
                "feature_id": feature_id,
                "borrower_id": feature_set.borrower_id,
                "feature_set": feature_set.feature_set,
                "feature_version": feature_set.feature_version,
                "computed_at": feature_set.computed_at,
                "status": "saved"
            }
            
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Failed to save features: {str(e)}")
    
    def _compute_data_quality_score(self, warnings: List[str]) -> float:
        """
        Compute data quality score from 0 (poor) to 1 (excellent).
        
        Each warning reduces the score. Critical warnings reduce more.
        
        Args:
            warnings: List of data quality warning strings
            
        Returns:
            Quality score between 0 and 1
        """
        if not warnings:
            return 1.0
        
        score = 1.0
        
        # Critical warnings (reduce by 0.3 each)
        critical = ["raw_events_fetch_failed", "no_raw_events"]
        for warning in warnings:
            if any(c in warning for c in critical):
                score -= 0.3
        
        # Major warnings (reduce by 0.2 each)
        major = ["computation_failed", "out_of_range"]
        for warning in warnings:
            if any(m in warning for m in major):
                score -= 0.2
        
        # Minor warnings (reduce by 0.1 each)
        minor = ["low_event_count"]
        for warning in warnings:
            if any(m in warning for m in minor):
                score -= 0.1
        
        # Ensure non-negative
        return max(0.0, score)
    
    def compute_and_save(
        self,
        borrower_id: str,
        borrower_profile: Dict[str, Any],
        raw_events: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Compute features and save to database in one operation.
        
        This is a convenience method that combines compute_features() and
        save_features() into a single call.
        
        Args:
            borrower_id: UUID of the borrower
            borrower_profile: Dictionary containing borrower profile data
            raw_events: Optional list of raw event dictionaries
            
        Returns:
            Dictionary containing save result with features included
            
        Raises:
            ValueError: If inputs are invalid
            Exception: If computation or save fails
            
        Example:
            >>> engine = FeatureEngine()
            >>> result = engine.compute_and_save(
            ...     borrower_id="abc-123",
            ...     borrower_profile={...}
            ... )
            >>> print(result["features"])
        """
        try:
            # Compute features
            feature_set = self.compute_features(
                borrower_id=borrower_id,
                borrower_profile=borrower_profile,
                raw_events=raw_events
            )
            
            # Save to database
            save_result = self.save_features(feature_set)
            
            # Add computed features to result
            save_result["features"] = feature_set.features
            save_result["source_event_count"] = feature_set.source_event_count
            
            return save_result
            
        except Exception as e:
            raise Exception(f"Failed to compute and save features: {str(e)}")

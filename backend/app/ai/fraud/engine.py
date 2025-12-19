"""
SYSTEM ROLE:
You are designing a centralized fraud detection engine.

PROJECT:
CreditBridge — Fraud Detection Engine.

TASK:
Implement a FraudEngine that:
1. Registers multiple FraudDetector instances
2. Executes all detectors per request
3. Aggregates results into combined_fraud_score, consolidated flags, merged explanation
4. Uses max-score or weighted strategy
5. Deterministic behavior only

Fraud Detection Engine

Central orchestration for multi-strategy fraud detection.

Architecture:
- Registers multiple fraud detectors (FraudDetector or BaseFraudDetector)
- Executes all detectors per request
- Aggregates results using max/avg/weighted strategies
- Provides unified fraud detection API

Features:
- Multi-detector orchestration
- Supports both FraudDetector (new) and BaseFraudDetector (legacy)
- Result aggregation with combined scores and consolidated flags
- Deterministic behavior
- Production-ready error handling
- Extensible for new detectors
"""

from typing import Dict, Any, List, Optional, Union
from .base import BaseFraudDetector, FraudDetector, FraudDetectionResult, FeatureCompatibilityError
from .rule_engine import RuleBasedFraudDetector
from .trustgraph_adapter import TrustGraphFraudDetector


class FraudEngine:
    """
    Central fraud detection engine.
    
    Orchestrates multiple fraud detectors and aggregates results.
    
    Supports Both Interfaces:
    - FraudDetector (new production-grade interface)
    - BaseFraudDetector (legacy backward compatibility)
    
    Features:
    - Multi-detector support (new and legacy)
    - Configurable aggregation strategy (max, avg, weighted)
    - Consolidated flags and merged explanations
    - Unified API
    - Deterministic behavior
    - Production-ready error handling
    """
    
    def __init__(
        self,
        detectors: Optional[List[Union[FraudDetector, BaseFraudDetector]]] = None,
        aggregation_strategy: str = "max"
    ):
        """
        Initialize fraud detection engine.
        
        Args:
            detectors: List of fraud detectors (FraudDetector or BaseFraudDetector).
                      If None, uses default detectors (both updated to FraudDetector interface).
            aggregation_strategy: How to aggregate results ("max", "avg", "weighted")
        """
        # Initialize detectors
        if detectors is None:
            self.detectors = [
                RuleBasedFraudDetector(),
                TrustGraphFraudDetector()
            ]
        else:
            self.detectors = detectors
        
        self.aggregation_strategy = aggregation_strategy
        self.engine_version = "2.0.0"
    
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate fraud risk using all registered detectors (convenience method).
        
        REQUIREMENT: Accepts feature vectors from ensemble and validates compatibility.
        Fails explicitly if features are missing or incompatible.
        
        Args:
            input_data: Input dictionary containing:
                - features: Engineered feature vector (dict, REQUIRED)
                - feature_set: Feature set name (str, REQUIRED)
                - feature_version: Feature version (str, REQUIRED)
                - borrower: Borrower profile (optional, for legacy support)
                - loan: Loan request details (optional)
                - context: Additional context (optional, e.g., trust_graph_data)
        
        Returns:
            Dict containing:
            - fraud_score: Combined fraud score (float 0.0-1.0)
            - flags: Consolidated flags (list[str])
            - explanation: Merged explanations (list[str])
        
        Raises:
            FeatureCompatibilityError: If features are missing or incompatible
        
        Example:
            >>> engine = FraudEngine()
            >>> result = engine.evaluate({
            ...     "features": {"transaction_volume_30d": 5000, "activity_consistency": 25},
            ...     "feature_set": "core_behavioral",
            ...     "feature_version": "v1",
            ...     "context": {"trust_graph_data": {...}}
            ... })
            >>> print(result["fraud_score"])
        """
        # ═══════════════════════════════════════════════════════════
        # VALIDATION: Ensure feature vector is present
        # ═══════════════════════════════════════════════════════════
        features = input_data.get("features")
        feature_set = input_data.get("feature_set")
        feature_version = input_data.get("feature_version")
        
        if not features:
            raise FeatureCompatibilityError(
                "Missing 'features' in input_data. "
                "FraudEngine requires engineered feature vectors, not raw data. "
                "Ensure features are computed and passed from ensemble."
            )
        
        if not isinstance(features, dict):
            raise FeatureCompatibilityError(
                f"Invalid features format. Expected dict, got {type(features).__name__}. "
                "Features must be a dictionary of feature_name: feature_value pairs."
            )
        
        if not feature_set or not feature_version:
            raise FeatureCompatibilityError(
                "Missing 'feature_set' or 'feature_version' in input_data. "
                f"Found: feature_set={feature_set}, feature_version={feature_version}. "
                "Both are required for feature compatibility validation."
            )
        
        # ═══════════════════════════════════════════════════════════
        # VALIDATION: Validate features against all detector requirements
        # ═══════════════════════════════════════════════════════════
        for detector in self.detectors:
            if isinstance(detector, FraudDetector) and hasattr(detector, 'validate_features'):
                try:
                    detector.validate_features(
                        features=features,
                        feature_set=feature_set,
                        feature_version=feature_version
                    )
                except Exception as e:
                    raise FeatureCompatibilityError(
                        f"Feature validation failed for {detector.name}: {str(e)}. "
                        "Ensure features match detector requirements."
                    )
        
        # ═══════════════════════════════════════════════════════════
        # EXECUTION: Pass feature vectors to all detectors
        # ═══════════════════════════════════════════════════════════
        # Extract components from input_data
        borrower_data = input_data.get("borrower", {})
        loan_data = input_data.get("loan", {})
        context = input_data.get("context", {})
        
        # Call detect_fraud with features included
        full_result = self.detect_fraud(
            borrower_data=borrower_data,
            loan_data=loan_data,
            context=context,
            features=features,
            feature_set=feature_set,
            feature_version=feature_version
        )
        
        # Return simplified format (new FraudDetector interface format)
        return {
            "fraud_score": full_result["combined_fraud_score"],
            "flags": full_result["consolidated_flags"],
            "explanation": full_result["merged_explanation"]
        }
    
    def detect_fraud(
        self,
        borrower_data: Dict[str, Any],
        loan_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        features: Optional[Dict[str, Any]] = None,
        feature_set: Optional[str] = None,
        feature_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect fraud using all registered detectors.
        
        REQUIREMENT: Accepts feature vectors and passes them to all detectors.
        Executes all detectors and aggregates results with consolidated flags
        and merged explanations.
        
        Args:
            borrower_data: Borrower profile (for legacy support)
            loan_data: Loan request details (for legacy support)
            context: Optional context data (e.g., trust_graph_data)
            features: Engineered feature vector (dict, REQUIRED for feature-driven detectors)
            feature_set: Feature set name (str, REQUIRED)
            feature_version: Feature version (str, REQUIRED)
        
        Returns:
            Dict containing:
            - combined_fraud_score: Aggregated fraud score (float 0.0-1.0)
            - consolidated_flags: All unique flags from detectors (list[str])
            - merged_explanation: All explanations combined (list[str])
            - is_fraud: Overall fraud determination (bool)
            - risk_level: Overall risk level (str)
            - confidence: Aggregated confidence (float)
            - detector_results: Individual detector results (list)
            - aggregation_details: Aggregation metadata (dict)
        """
        context = context or {}
        features = features or {}
        
        # Prepare input for new FraudDetector interface with features
        input_data = {
            "features": features,
            "feature_set": feature_set or "core_behavioral",
            "feature_version": feature_version or "v1",
            "borrower": borrower_data,
            "loan": loan_data,
            "context": context
        }
        
        # Add features to context for legacy detect() method
        context_with_features = {**context, "features": features}
        
        # Run all detectors (supports both FraudDetector and BaseFraudDetector)
        detector_results = []
        new_format_results = []  # Results from evaluate() method
        
        for detector in self.detectors:
            try:
                # Check if detector implements FraudDetector interface (has evaluate method)
                if isinstance(detector, FraudDetector) and hasattr(detector, 'evaluate'):
                    # Use new interface
                    result = detector.evaluate(input_data)
                    new_format_results.append({
                        "detector_name": detector.name,
                        "result": result
                    })
                    
                    # Also get legacy format for backward compatibility
                    # Pass features through context to avoid validation errors
                    legacy_result = detector.detect(borrower_data, loan_data, context_with_features)
                    detector_results.append(legacy_result)
                else:
                    # Use legacy interface
                    result = detector.detect(borrower_data, loan_data, context)
                    detector_results.append(result)
                    
                    # Convert to new format for aggregation
                    new_format_results.append({
                        "detector_name": detector.get_name(),
                        "result": {
                            "fraud_score": result.fraud_score,
                            "flags": [ind.get("type", "unknown") for ind in result.fraud_indicators],
                            "explanation": [ind.get("description", "") for ind in result.fraud_indicators]
                        }
                    })
            except Exception as e:
                # Log error and continue with other detectors
                print(f"Error in detector {getattr(detector, 'name', detector.get_name())}: {e}")
                continue
        
        # Aggregate results using new format
        aggregated = self._aggregate_results_new_format(new_format_results)
        
        # Legacy aggregation for backward compatibility fields
        legacy_aggregated = self._aggregate_results(detector_results) if detector_results else {
            "is_fraud": False,
            "fraud_score": 0.0,
            "risk_level": "low",
            "confidence": 0.0,
            "fraud_indicators": []
        }
        
        return {
            # New format (primary)
            "combined_fraud_score": aggregated["combined_fraud_score"],
            "consolidated_flags": aggregated["consolidated_flags"],
            "merged_explanation": aggregated["merged_explanation"],
            
            # Legacy fields (backward compatibility)
            "is_fraud": legacy_aggregated["is_fraud"],
            "fraud_score": legacy_aggregated["fraud_score"],  # Alias for combined_fraud_score
            "risk_level": legacy_aggregated["risk_level"],
            "confidence": legacy_aggregated["confidence"],
            "fraud_indicators": legacy_aggregated["fraud_indicators"],
            
            # Detailed results
            "detector_results": [r.to_dict() for r in detector_results] if detector_results else [],
            "detector_outputs": new_format_results,
            
            # Metadata
            "aggregation_details": {
                "strategy": self.aggregation_strategy,
                "num_detectors": len(self.detectors),
                "num_results": len(new_format_results),
                "engine_version": self.engine_version,
                "deterministic": True
            }
        }
    
    def _aggregate_results_new_format(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from new FraudDetector interface.
        
        Produces:
        - combined_fraud_score: Aggregated score
        - consolidated_flags: All unique flags
        - merged_explanation: All explanations
        
        Args:
            results: List of detector outputs with fraud_score, flags, explanation
        
        Returns:
            Aggregated result dict with combined_fraud_score, consolidated_flags, merged_explanation
        """
        if not results:
            return {
                "combined_fraud_score": 0.0,
                "consolidated_flags": [],
                "merged_explanation": []
            }
        
        # Extract all scores, flags, and explanations
        scores = [r["result"]["fraud_score"] for r in results]
        all_flags = []
        all_explanations = []
        
        for r in results:
            detector_name = r["detector_name"]
            result = r["result"]
            
            # Collect flags with detector prefix
            for flag in result.get("flags", []):
                all_flags.append(f"{detector_name}:{flag}")
            
            # Collect explanations with detector prefix
            for exp in result.get("explanation", []):
                all_explanations.append(f"[{detector_name}] {exp}")
        
        # Aggregate score based on strategy
        if self.aggregation_strategy == "max":
            combined_score = max(scores)
        elif self.aggregation_strategy == "avg":
            combined_score = sum(scores) / len(scores)
        elif self.aggregation_strategy == "weighted":
            # For weighted, use equal weights (can be enhanced later)
            combined_score = sum(scores) / len(scores)
        else:
            combined_score = max(scores)
        
        # Deduplicate flags while preserving order
        consolidated_flags = []
        seen = set()
        for flag in all_flags:
            if flag not in seen:
                consolidated_flags.append(flag)
                seen.add(flag)
        
        # Keep all explanations (no deduplication for explanations)
        merged_explanation = all_explanations
        
        return {
            "combined_fraud_score": combined_score,
            "consolidated_flags": consolidated_flags,
            "merged_explanation": merged_explanation
        }
    
    def _aggregate_results(self, results: List[FraudDetectionResult]) -> Dict[str, Any]:
        """
        Aggregate results from multiple detectors.
        
        Args:
            results: List of detector results
        
        Returns:
            Aggregated result dict
        """
        if not results:
            return {
                "is_fraud": False,
                "fraud_score": 0.0,
                "risk_level": "low",
                "confidence": 0.0,
                "fraud_indicators": []
            }
        
        if self.aggregation_strategy == "max":
            return self._aggregate_max(results)
        elif self.aggregation_strategy == "avg":
            return self._aggregate_average(results)
        elif self.aggregation_strategy == "weighted":
            return self._aggregate_weighted(results)
        else:
            # Default to max
            return self._aggregate_max(results)
    
    def _aggregate_max(self, results: List[FraudDetectionResult]) -> Dict[str, Any]:
        """
        Aggregate using maximum fraud score.
        
        Conservative approach: if any detector flags fraud, report it.
        """
        max_result = max(results, key=lambda r: r.fraud_score)
        
        # Collect all fraud indicators
        all_indicators = []
        for result in results:
            all_indicators.extend(result.fraud_indicators)
        
        return {
            "is_fraud": max_result.is_fraud,
            "fraud_score": max_result.fraud_score,
            "risk_level": max_result.risk_level,
            "confidence": max_result.confidence,
            "fraud_indicators": all_indicators
        }
    
    def _aggregate_average(self, results: List[FraudDetectionResult]) -> Dict[str, Any]:
        """
        Aggregate using average fraud score.
        
        Balanced approach: average scores across all detectors.
        """
        avg_score = sum(r.fraud_score for r in results) / len(results)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        # Determine overall fraud flag
        is_fraud = avg_score >= 0.6
        
        # Determine risk level
        risk_level = self._calculate_risk_level(avg_score)
        
        # Collect all fraud indicators
        all_indicators = []
        for result in results:
            all_indicators.extend(result.fraud_indicators)
        
        return {
            "is_fraud": is_fraud,
            "fraud_score": avg_score,
            "risk_level": risk_level,
            "confidence": avg_confidence,
            "fraud_indicators": all_indicators
        }
    
    def _aggregate_weighted(self, results: List[FraudDetectionResult]) -> Dict[str, Any]:
        """
        Aggregate using weighted average based on confidence.
        
        Advanced approach: weight by detector confidence.
        """
        total_weight = sum(r.confidence for r in results)
        
        if total_weight == 0:
            return self._aggregate_average(results)
        
        weighted_score = sum(
            r.fraud_score * r.confidence for r in results
        ) / total_weight
        
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        # Determine overall fraud flag
        is_fraud = weighted_score >= 0.6
        
        # Determine risk level
        risk_level = self._calculate_risk_level(weighted_score)
        
        # Collect all fraud indicators
        all_indicators = []
        for result in results:
            all_indicators.extend(result.fraud_indicators)
        
        return {
            "is_fraud": is_fraud,
            "fraud_score": weighted_score,
            "risk_level": risk_level,
            "confidence": avg_confidence,
            "fraud_indicators": all_indicators
        }
    
    def _calculate_risk_level(self, fraud_score: float) -> str:
        """Calculate risk level from fraud score."""
        if fraud_score >= 0.8:
            return "critical"
        elif fraud_score >= 0.6:
            return "high"
        elif fraud_score >= 0.3:
            return "medium"
        else:
            return "low"
    
    def register_detector(self, detector: Union[FraudDetector, BaseFraudDetector]) -> None:
        """
        Register a new fraud detector.
        
        Supports both FraudDetector (new) and BaseFraudDetector (legacy).
        
        Args:
            detector: Fraud detector to register (FraudDetector or BaseFraudDetector)
        """
        if not isinstance(detector, (FraudDetector, BaseFraudDetector)):
            raise TypeError("detector must be an instance of FraudDetector or BaseFraudDetector")
        
        self.detectors.append(detector)
    
    def get_registered_detectors(self) -> List[str]:
        """
        Get list of registered detector names.
        
        Returns:
            List of detector names
        """
        names = []
        for detector in self.detectors:
            if isinstance(detector, FraudDetector) and hasattr(detector, 'name'):
                names.append(detector.name)
            else:
                names.append(detector.get_name())
        return names


# Singleton instance
_global_fraud_engine: Optional[FraudEngine] = None


def get_fraud_engine(
    aggregation_strategy: str = "max"
) -> FraudEngine:
    """
    Get the global fraud detection engine.
    
    Lazy initialization with default detectors.
    
    Args:
        aggregation_strategy: How to aggregate results ("max", "avg", "weighted")
    
    Returns:
        FraudEngine: Singleton fraud engine instance
    """
    global _global_fraud_engine
    
    if _global_fraud_engine is None:
        _global_fraud_engine = FraudEngine(
            aggregation_strategy=aggregation_strategy
        )
    
    return _global_fraud_engine

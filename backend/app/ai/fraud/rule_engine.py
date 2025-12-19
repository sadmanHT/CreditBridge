"""
Rule-Based Fraud Detection Engine

SYSTEM ROLE:
Implementing feature-driven fraud detection for digital lending systems.

PROJECT:
CreditBridge — Fraud Rules Engine.

REQUIREMENTS:
- Class: RuleBasedFraudDetector
- Inherit from FraudDetector
- Feature-driven: Use engineered features only
- Simple, explainable rules:
  * Low transaction volume → risk
  * Low activity consistency → risk
- Return fraud_score, flags, explanation
- Deterministic logic only

Design:
- Feature-driven architecture (no raw data access)
- Deterministic rule evaluation
- Transparent and explainable
- Easy to audit and modify
- Production-ready with comprehensive logging
"""

from typing import Dict, Any, List, Optional
from .base import FraudDetector, BaseFraudDetector, FraudDetectionResult, FeatureCompatibilityError


class RuleBasedFraudDetector(FraudDetector, BaseFraudDetector):
    """
    Feature-driven rule-based fraud detector using deterministic rules.
    
    SYSTEM ROLE:
    Implements feature-driven fraud detection for digital lending systems.
    
    FUNCTIONAL REQUIREMENT:
    Operates ONLY on engineered features, not raw borrower/event data.
    
    Features:
    - Simple, explainable rules based on behavioral features
    - Low transaction volume detection
    - Low activity consistency detection
    - Deterministic logic only
    - Transparent rule evaluation
    
    Implements both FraudDetector (primary) and BaseFraudDetector (legacy).
    """
    
    def __init__(self, rules_config: Optional[Dict[str, Any]] = None):
        """
        Initialize feature-driven rule-based fraud detector.
        
        Args:
            rules_config: Optional configuration for rule thresholds
        """
        self.rules_config = rules_config or self._get_default_config()
        self.detector_version = "2.0.0"
    
    # ═══════════════════════════════════════════════════════════════════════
    # PRIMARY INTERFACE (FraudDetector) - Feature Compatibility
    # ═══════════════════════════════════════════════════════════════════════
    
    @property
    def name(self) -> str:
        """
        Get detector name (FraudDetector interface).
        
        Returns:
            str: Detector name with version
        """
        return f"RuleBasedFraudDetector-v{self.detector_version}"
    
    @property
    def required_feature_set(self) -> str:
        """Return required feature set name."""
        return "core_behavioral"
    
    @property
    def required_feature_version(self) -> str:
        """Return required feature version."""
        return "v1"
    
    @property
    def required_feature_keys(self) -> List[str]:
        """Return list of required feature keys."""
        return [
            "transaction_volume_30d",
            "activity_consistency"
        ]
    
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate fraud risk using feature-driven, deterministic rules.
        
        FUNCTIONAL REQUIREMENT: Operates ONLY on engineered features.
        
        RULES:
        1. Low transaction volume → risk (suspicious inactivity)
        2. Low activity consistency → risk (erratic behavior)
        
        Args:
            input_data: Dictionary containing:
                - "features": Engineered features (dict)
                - "feature_set": Feature set name (str)
                - "feature_version": Feature version (str)
        
        Returns:
            Dict with required format:
            {
                "fraud_score": float,     # 0.0–1.0
                "flags": list[str],       # Fraud flags
                "explanation": list[str]  # Human-readable explanations
            }
        """
        # Extract features
        features = input_data.get("features", {})
        feature_set = input_data.get("feature_set", "core_behavioral")
        feature_version = input_data.get("feature_version", "v1")
        
        # Validate feature compatibility
        self.validate_features(features, feature_set, feature_version)
        
        # Initialize result
        fraud_score = 0.0
        flags = []
        explanation = []
        
        # ═══════════════════════════════════════════════════════════
        # RULE 1: Low transaction volume (suspicious inactivity)
        # ═══════════════════════════════════════════════════════════
        transaction_volume = features.get("transaction_volume_30d", 0)
        
        low_volume_threshold = self.rules_config.get("low_volume_threshold", 1000)
        very_low_volume_threshold = self.rules_config.get("very_low_volume_threshold", 500)
        
        if transaction_volume < very_low_volume_threshold:
            fraud_score += 0.4
            flags.append("very_low_transaction_volume")
            explanation.append(
                f"transaction_volume_30d ({transaction_volume:.2f}) is suspiciously low "
                f"(< {very_low_volume_threshold}), indicating minimal economic activity"
            )
        elif transaction_volume < low_volume_threshold:
            fraud_score += 0.2
            flags.append("low_transaction_volume")
            explanation.append(
                f"transaction_volume_30d ({transaction_volume:.2f}) below normal threshold "
                f"({low_volume_threshold}), suggesting limited financial engagement"
            )
        
        # ═══════════════════════════════════════════════════════════
        # RULE 2: Low activity consistency (erratic behavior)
        # ═══════════════════════════════════════════════════════════
        activity_consistency = features.get("activity_consistency", 0)
        
        low_consistency_threshold = self.rules_config.get("low_consistency_threshold", 30)
        very_low_consistency_threshold = self.rules_config.get("very_low_consistency_threshold", 15)
        
        if activity_consistency < very_low_consistency_threshold:
            fraud_score += 0.4
            flags.append("very_low_activity_consistency")
            explanation.append(
                f"activity_consistency ({activity_consistency:.1f}) is critically low "
                f"(< {very_low_consistency_threshold}), indicating highly erratic behavior"
            )
        elif activity_consistency < low_consistency_threshold:
            fraud_score += 0.2
            flags.append("low_activity_consistency")
            explanation.append(
                f"activity_consistency ({activity_consistency:.1f}) below threshold "
                f"({low_consistency_threshold}), suggesting inconsistent behavior patterns"
            )
        
        # Clamp fraud_score to [0.0, 1.0]
        fraud_score = min(fraud_score, 1.0)
        
        return {
            "fraud_score": fraud_score,
            "flags": flags,
            "explanation": explanation
        }
    
    # ═══════════════════════════════════════════════════════════════════════
    # LEGACY INTERFACE (BaseFraudDetector)
    # ═══════════════════════════════════════════════════════════════════════
    
    def get_name(self) -> str:
        """Get detector name (legacy interface)."""
        return self.name
    
    def detect(
        self,
        borrower_data: Dict[str, Any],
        loan_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> FraudDetectionResult:
        """
        Detect fraud using feature-driven analysis (legacy interface).
        
        This method wraps the new evaluate() method for backward compatibility.
        Expects borrower_data to contain engineered features.
        
        Args:
            borrower_data: Borrower profile (can be empty if features provided via context)
            loan_data: Loan request details (can be empty)
            context: Optional context (application history, etc.)
        
        Returns:
            FraudDetectionResult: Detection result with indicators
        """
        # Extract engineered features from borrower_data or context
        engineered_features = borrower_data.get("engineered_features", {})
        if not engineered_features and context:
            # Try to get features from context (for FraudEngine invocation)
            engineered_features = context.get("features", {})
        
        if not engineered_features:
            raise ValueError(
                "Missing engineered features. "
                "Provide borrower_data with 'engineered_features' or context with 'features'"
            )
        
        # Prepare input for evaluate()
        input_data = {
            "features": engineered_features,
            "feature_set": borrower_data.get("feature_set", "core_behavioral"),
            "feature_version": borrower_data.get("feature_version", "v1")
        }
        
        # Call new evaluate() method
        eval_result = self.evaluate(input_data)
        
        # Convert to legacy FraudDetectionResult format
        fraud_score = eval_result["fraud_score"]
        flags = eval_result["flags"]
        explanations = eval_result["explanation"]
        
        # Determine if fraud detected
        fraud_threshold = self.rules_config.get("fraud_threshold", 0.6)
        is_fraud = fraud_score >= fraud_threshold
        
        # Calculate risk level
        risk_level = self.calculate_risk_level(fraud_score)
        
        # Calculate confidence based on number of flags
        confidence = min(0.5 + (len(flags) * 0.15), 1.0)
        
        # Convert flags to fraud_indicators format
        fraud_indicators = []
        for i, flag in enumerate(flags):
            explanation_text = explanations[i] if i < len(explanations) else ""
            fraud_indicators.append({
                "rule": flag,
                "description": explanation_text,
                "score": fraud_score / max(len(flags), 1),
                "weight": 1.0 / max(len(flags), 1)
            })
        
        return FraudDetectionResult(
            is_fraud=is_fraud,
            fraud_score=fraud_score,
            risk_level=risk_level,
            fraud_indicators=fraud_indicators,
            confidence=confidence,
            detector_name=self.get_name(),
            details={
                "rules_evaluated": 2,
                "rules_triggered": len(flags),
                "fraud_threshold": fraud_threshold,
                "flags": flags,
                "explanations": explanations
            }
        )
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default rule configuration.
        
        Returns:
            Dict with rule thresholds:
            - low_volume_threshold: Low transaction volume (1,000)
            - very_low_volume_threshold: Very low volume (500)
            - low_consistency_threshold: Low activity consistency (30)
            - very_low_consistency_threshold: Very low consistency (15)
            - fraud_threshold: Score threshold for fraud flag (0.6)
        """
        return {
            "low_volume_threshold": 1000,
            "very_low_volume_threshold": 500,
            "low_consistency_threshold": 30,
            "very_low_consistency_threshold": 15,
            "fraud_threshold": 0.6
        }

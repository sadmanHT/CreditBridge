"""
Credit Rule-Based Model for CreditBridge

SYSTEM ROLE:
Feature-driven credit scoring model that operates exclusively on
engineered features, not raw data.

PROJECT:
CreditBridge — Feature-driven Credit Model.

TASK:
Refactor RuleBasedCreditModel to operate ONLY on feature vectors.

Rule-based credit scoring model that uses deterministic logic
for transparent, explainable credit decisions based on engineered features.

Inherits from BaseModel to ensure consistent interface.
"""

from typing import Dict, List, Any
from datetime import datetime
from app.ai.models.base import BaseModel, FeatureCompatibilityError


class RuleBasedCreditModel(BaseModel):
    """
    Feature-driven rule-based credit scoring model.
    
    Uses transparent, deterministic rules to compute credit scores
    based on engineered features from the FeatureEngine:
    - mobile_activity_score: Mobile app engagement (0-100)
    - transaction_volume_30d: 30-day transaction volume
    - activity_consistency: Consistency of activity patterns (0-100)
    
    Features:
    - No ML black boxes (fully explainable)
    - Feature-driven (no raw data dependencies)
    - Fast computation (<5ms)
    - Regulatory compliant
    """
    
    @property
    def name(self) -> str:
        """Return model name and version."""
        return "RuleBasedCreditModel-v1.0"
    
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
            "mobile_activity_score",
            "transaction_volume_30d",
            "activity_consistency"
        ]
    
    def predict(self, input_data: dict) -> dict:
        """
        Compute credit score using feature-based rule logic.
        
        FUNCTIONAL REQUIREMENT: Operates ONLY on engineered features.
        
        Args:
            input_data: Dictionary containing:
                - "engineered_features" (preferred) or "features": Dict with:
                    - mobile_activity_score: float (0-100)
                    - transaction_volume_30d: float (>=0)
                    - activity_consistency: float (0-100)
                - "feature_set": Feature set name (for validation)
                - "feature_version": Feature version (for validation)
                - "loan_request" (optional): For loan-specific adjustments
        
        Returns:
            Dictionary with score, risk_level (0-100 score, risk mapping)
        """
        # Extract engineered features (support both key names for compatibility)
        features = input_data.get("engineered_features") or input_data.get("features", {})
        feature_set = input_data.get("feature_set", "core_behavioral")
        feature_version = input_data.get("feature_version", "v1")
        loan_request = input_data.get("loan_request", {})
        
        # Validate that we have features
        if not features:
            raise ValueError("No engineered features provided")
        
        # Validate feature compatibility (raises FeatureCompatibilityError or ValueError)
        self.validate_features(features, feature_set, feature_version)
        
        # Initialize base score and factors
        base_score = 50
        score = base_score
        factors = []
        
        # Add base score factor for transparency
        factors.append({
            "factor": "Base credit score",
            "impact": base_score,
            "explanation": "Starting baseline for all borrowers"
        })
        
        # FEATURE 1: Mobile Activity Score (0-100)
        # Higher mobile activity indicates engagement and digital literacy
        mobile_activity = features.get("mobile_activity_score", 0)
        mobile_factor = self._evaluate_mobile_activity(mobile_activity)
        score += mobile_factor["impact"]
        factors.append(mobile_factor)
        
        # FEATURE 2: Transaction Volume (30-day window)
        # Higher transaction volume indicates economic activity
        transaction_volume = features.get("transaction_volume_30d", 0)
        volume_factor = self._evaluate_transaction_volume(transaction_volume)
        score += volume_factor["impact"]
        factors.append(volume_factor)
        
        # FEATURE 3: Activity Consistency (0-100)
        # Higher consistency indicates stable behavior patterns
        activity_consistency = features.get("activity_consistency", 0)
        consistency_factor = self._evaluate_activity_consistency(activity_consistency)
        score += consistency_factor["impact"]
        factors.append(consistency_factor)
        
        # OPTIONAL: Loan Amount Adjustment (if loan_request provided)
        # This is feature-agnostic risk adjustment based on loan parameters
        if loan_request and "requested_amount" in loan_request:
            requested_amount = loan_request.get("requested_amount", 0)
            amount_factor = self._evaluate_loan_amount(requested_amount)
            score += amount_factor["impact"]
            factors.append(amount_factor)
        
        # Clamp score to valid range (0-100)
        final_score = self._clamp_score(score)
        
        # Determine risk level from score
        risk_level = self._determine_risk_level(final_score)
        
        # Store factors for explain() method
        self._last_factors = factors
        self._last_features = features
        
        # Return standardized format
        return {
            "score": final_score,
            "risk_level": risk_level
        }
    
    def _evaluate_mobile_activity(self, mobile_activity_score: float) -> Dict[str, Any]:
        """
        Evaluate mobile activity feature impact on credit score.
        
        Feature: mobile_activity_score (0-100)
        Higher scores indicate greater mobile engagement and digital literacy.
        
        Args:
            mobile_activity_score: Mobile activity score (0-100)
            
        Returns:
            Dictionary with factor details
        """
        if mobile_activity_score >= 75:
            return {
                "factor": "mobile_activity_score: High (75-100)",
                "impact": 15,
                "explanation": f"Strong mobile engagement ({mobile_activity_score:.1f}/100) indicates digital literacy and active participation"
            }
        elif mobile_activity_score >= 50:
            return {
                "factor": "mobile_activity_score: Moderate (50-74)",
                "impact": 10,
                "explanation": f"Moderate mobile engagement ({mobile_activity_score:.1f}/100) shows regular app usage"
            }
        elif mobile_activity_score >= 25:
            return {
                "factor": "mobile_activity_score: Low (25-49)",
                "impact": 5,
                "explanation": f"Limited mobile engagement ({mobile_activity_score:.1f}/100) suggests infrequent activity"
            }
        else:
            return {
                "factor": "mobile_activity_score: Minimal (0-24)",
                "impact": 0,
                "explanation": f"Minimal mobile engagement ({mobile_activity_score:.1f}/100) indicates low digital activity"
            }
    
    def _evaluate_transaction_volume(self, transaction_volume: float) -> Dict[str, Any]:
        """
        Evaluate transaction volume feature impact on credit score.
        
        Feature: transaction_volume_30d (monetary value)
        Higher volume indicates economic activity and ability to manage finances.
        
        Args:
            transaction_volume: 30-day transaction volume
            
        Returns:
            Dictionary with factor details
        """
        if transaction_volume >= 10000:
            return {
                "factor": "transaction_volume_30d: High (≥৳10,000)",
                "impact": 15,
                "explanation": f"High transaction volume (৳{transaction_volume:.2f}) demonstrates strong economic activity"
            }
        elif transaction_volume >= 5000:
            return {
                "factor": "transaction_volume_30d: Moderate (৳5,000-9,999)",
                "impact": 10,
                "explanation": f"Moderate transaction volume (৳{transaction_volume:.2f}) shows regular economic participation"
            }
        elif transaction_volume >= 1000:
            return {
                "factor": "transaction_volume_30d: Low (৳1,000-4,999)",
                "impact": 5,
                "explanation": f"Low transaction volume (৳{transaction_volume:.2f}) indicates limited financial activity"
            }
        else:
            return {
                "factor": "transaction_volume_30d: Minimal (<৳1,000)",
                "impact": 0,
                "explanation": f"Minimal transaction volume (৳{transaction_volume:.2f}) suggests very limited economic activity"
            }
    
    def _evaluate_activity_consistency(self, activity_consistency: float) -> Dict[str, Any]:
        """
        Evaluate activity consistency feature impact on credit score.
        
        Feature: activity_consistency (0-100)
        Higher consistency indicates stable, predictable behavior patterns.
        
        Args:
            activity_consistency: Activity consistency score (0-100)
            
        Returns:
            Dictionary with factor details
        """
        if activity_consistency >= 75:
            return {
                "factor": "activity_consistency: High (75-100)",
                "impact": 10,
                "explanation": f"High consistency ({activity_consistency:.1f}/100) indicates stable, predictable behavior"
            }
        elif activity_consistency >= 50:
            return {
                "factor": "activity_consistency: Moderate (50-74)",
                "impact": 5,
                "explanation": f"Moderate consistency ({activity_consistency:.1f}/100) shows reasonably stable patterns"
            }
        elif activity_consistency >= 25:
            return {
                "factor": "activity_consistency: Low (25-49)",
                "impact": 0,
                "explanation": f"Low consistency ({activity_consistency:.1f}/100) suggests irregular behavior patterns"
            }
        else:
            return {
                "factor": "activity_consistency: Minimal (0-24)",
                "impact": -5,
                "explanation": f"Minimal consistency ({activity_consistency:.1f}/100) indicates unpredictable behavior"
            }
    
    def _evaluate_loan_amount(self, requested_amount: float) -> Dict[str, Any]:
        """
        Evaluate loan amount risk adjustment (feature-agnostic).
        
        This is a risk adjustment based on loan parameters, not a feature.
        Smaller loans carry lower risk regardless of borrower features.
        
        Args:
            requested_amount: Requested loan amount
            
        Returns:
            Dictionary with factor details
        """
        if requested_amount < 10000:
            return {
                "factor": "Loan Amount: Small (< ৳10,000)",
                "impact": 5,
                "explanation": "Lower risk due to small loan size"
            }
        elif requested_amount < 25000:
            return {
                "factor": "Loan Amount: Medium (৳10,000 - ৳25,000)",
                "impact": 0,
                "explanation": "Moderate risk for medium-sized loan"
            }
        elif requested_amount < 50000:
            return {
                "factor": "Loan Amount: Standard (৳25,000 - ৳50,000)",
                "impact": -5,
                "explanation": "Standard risk level"
            }
        else:
            return {
                "factor": "Loan Amount: Large (> ৳50,000)",
                "impact": -10,
                "explanation": "Higher risk due to large loan size"
            }
    
    def _recommend_decision(self, credit_score: int) -> str:
        """Recommend decision based on score."""
        if credit_score >= 70:
            return "approved"
        elif credit_score >= 50:
            return "review"
        else:
            return "rejected"
    
    def _clamp_score(self, score: float) -> int:
        """Clamp score to 0-100 range."""
        return int(max(0, min(100, score)))
    
    def _determine_risk_level(self, score: int) -> str:
        """
        Determine risk level from score.
        
        Mapping:
        - 70-100: Low risk
        - 50-69: Medium risk
        - 0-49: High risk
        """
        if score >= 70:
            return "low"
        elif score >= 50:
            return "medium"
        else:
            return "high"
    
    def explain(self, input_data: dict, prediction: dict) -> dict:
        """
        Generate explanation for credit decision based on feature impacts.
        
        REQUIREMENT: Explanations must reference feature impacts, not raw data.
        Feature names are explicitly mentioned in explanations.
        
        Args:
            input_data: Original input data (with engineered features)
            prediction: Prediction result
        
        Returns:
            Explanation dictionary with feature-based reasoning
        """
        score = prediction.get("score", 0)
        risk_level = prediction.get("risk_level", "unknown")
        factors = getattr(self, '_last_factors', [])
        features = getattr(self, '_last_features', {})
        
        # Determine decision based on score
        if score >= 70:
            decision = "approved"
        elif score >= 50:
            decision = "review"
        else:
            decision = "rejected"
        
        # Build feature summary for explanation
        feature_summary = []
        if features:
            mobile_score = features.get("mobile_activity_score", 0)
            transaction_vol = features.get("transaction_volume_30d", 0)
            consistency = features.get("activity_consistency", 0)
            
            feature_summary.append(f"mobile_activity_score={mobile_score:.1f}")
            feature_summary.append(f"transaction_volume_30d=৳{transaction_vol:.2f}")
            feature_summary.append(f"activity_consistency={consistency:.1f}")
        
        summary = (
            f"Credit score of {score}/100 with {risk_level} risk resulted in '{decision}' decision. "
            f"Based on engineered features: {', '.join(feature_summary) if feature_summary else 'none'}"
        )
        
        return {
            "summary": summary,
            "factors": factors,
            "details": f"Decision based on {len(factors)} feature-driven scoring factors",
            "features_used": list(features.keys()) if features else []
        }
    
    def _error_response(self, error_msg: str) -> dict:
        """Generate error response."""
        return {
            "score": 0,
            "risk_level": "high",
            "error": error_msg
        }


# Singleton instance for module-level access
_credit_rule_model_instance = RuleBasedCreditModel()


def compute_credit_score(borrower: Dict[str, Any], loan_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Module-level function for backward compatibility.
    
    DEPRECATED: This function uses raw data. Consider using feature-driven approach.
    
    Args:
        borrower: Borrower profile dictionary (should contain engineered_features)
        loan_request: Loan request details dictionary
        
    Returns:
        Credit scoring result (with legacy key names)
    """
    input_data = {"borrower": borrower, "loan_request": loan_request}
    
    # Check if borrower has engineered features
    if "engineered_features" in borrower:
        input_data["engineered_features"] = borrower["engineered_features"]
    
    result = _credit_rule_model_instance.predict(input_data)
    
    # Convert to legacy format
    return {
        "credit_score": result.get("score", 0),
        "risk_level": result.get("risk_level", "high"),
        "factors": getattr(_credit_rule_model_instance, '_last_factors', []),
        "decision": _credit_rule_model_instance._recommend_decision(result.get("score", 0)),
        "confidence": 0.95,  # High confidence for rule-based model
        "model_metadata": {
            "model_name": _credit_rule_model_instance.name,
            "feature_driven": "engineered_features" in borrower
        }
    }

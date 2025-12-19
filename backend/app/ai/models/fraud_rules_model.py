"""
Fraud Detection Rules Model for CreditBridge

Rule-based fraud detection model using velocity checks,
pattern analysis, and anomaly scoring.

Inherits from BaseModel to ensure consistent interface.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
from app.ai.models.base import BaseModel


class FraudRulesModel(BaseModel):
    """
    Rule-based fraud detection model.
    
    Implements multi-layer fraud detection:
    - Layer 1: Velocity checks (rapid application patterns)
    - Layer 2: Anomaly detection (unusual loan amounts)
    - Layer 3: Pattern matching (duplicate data, suspicious IPs)
    
    Features:
    - Real-time fraud scoring
    - Transparent rule logic
    - No external services required
    - Regulatory compliant
    """
    
    @property
    def name(self) -> str:
        """Return model name and version."""
        return "FraudRulesModel-v1.0"
    
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
        # FraudRules operates on velocity/pattern data, not behavioral features
        # Return empty list since it doesn't require behavioral features
        return []
    
    def __init__(self):
        """Initialize fraud detection model."""
        self.risk_threshold = 0.7
        self.velocity_window_minutes = 60
        self.max_applications_per_hour = 3
        self.suspicious_amount_threshold = 100000
    
    def predict(self, input_data: dict) -> dict:
        """
        Detect fraud using rule-based checks.
        
        Args:
            input_data: Dictionary containing borrower and loan_request
        
        Returns:
            Dictionary with fraud_score, is_fraud, confidence, metadata
        """
        borrower = input_data.get("borrower", {})
        loan_request = input_data.get("loan_request", {})
        
        fraud_score = 0.0
        factors = []
        flags = []
        
        # Layer 1: Velocity checks
        velocity_result = self._check_velocity(borrower)
        fraud_score += velocity_result["score"]
        factors.extend(velocity_result["factors"])
        flags.extend(velocity_result["flags"])
        
        # Layer 2: Anomaly detection
        anomaly_result = self._check_anomalies(loan_request)
        fraud_score += anomaly_result["score"]
        factors.extend(anomaly_result["factors"])
        flags.extend(anomaly_result["flags"])
        
        # Layer 3: Pattern matching
        pattern_result = self._check_patterns(borrower, loan_request)
        fraud_score += pattern_result["score"]
        factors.extend(pattern_result["factors"])
        flags.extend(pattern_result["flags"])
        
        # Clamp fraud score to 0.0-1.0
        fraud_score = max(0.0, min(1.0, fraud_score))
        
        # Determine if fraudulent
        is_fraud = self._is_fraudulent(fraud_score)
        
        # Compute confidence
        confidence = self._compute_confidence(factors)
        
        # Build response
        return {
            "score": round(fraud_score, 3),
            "fraud_score": round(fraud_score, 3),
            "is_fraud": is_fraud,
            "decision": "rejected" if is_fraud else "approved",
            "confidence": confidence,
            "factors": factors,
            "flags": flags,
            "risk_level": self._get_risk_level(fraud_score),
            "metadata": {
                "model_name": self.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _check_velocity(self, borrower: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for velocity-based fraud (rapid applications).
        
        Args:
            borrower: Borrower profile
            
        Returns:
            Velocity check result
        """
        recent_apps = borrower.get("recent_applications", [])
        
        if not recent_apps:
            return {
                "score": 0.0,
                "factors": [{
                    "factor": "Velocity check",
                    "impact": 0.0,
                    "explanation": "No recent applications - normal"
                }],
                "flags": []
            }
        
        # Count applications in last hour
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(minutes=self.velocity_window_minutes)
        
        recent_count = len([
            app for app in recent_apps
            if datetime.fromisoformat(app.get("created_at", "1970-01-01")) > one_hour_ago
        ])
        
        if recent_count > self.max_applications_per_hour:
            return {
                "score": 0.5,
                "factors": [{
                    "factor": "Velocity violation",
                    "impact": 0.5,
                    "explanation": f"{recent_count} applications in last hour (max: {self.max_applications_per_hour})"
                }],
                "flags": ["HIGH_VELOCITY"]
            }
        else:
            return {
                "score": 0.0,
                "factors": [{
                    "factor": "Velocity check",
                    "impact": 0.0,
                    "explanation": f"{recent_count} applications in last hour - normal"
                }],
                "flags": []
            }
    
    def _check_anomalies(self, loan_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for anomalous loan amounts.
        
        Args:
            loan_request: Loan request details
            
        Returns:
            Anomaly check result
        """
        requested_amount = loan_request.get("requested_amount", 0)
        
        if requested_amount > self.suspicious_amount_threshold:
            return {
                "score": 0.3,
                "factors": [{
                    "factor": "Suspicious amount",
                    "impact": 0.3,
                    "explanation": f"Amount ৳{requested_amount:,.0f} exceeds threshold ৳{self.suspicious_amount_threshold:,.0f}"
                }],
                "flags": ["LARGE_AMOUNT"]
            }
        else:
            return {
                "score": 0.0,
                "factors": [{
                    "factor": "Amount check",
                    "impact": 0.0,
                    "explanation": f"Amount ৳{requested_amount:,.0f} within normal range"
                }],
                "flags": []
            }
    
    def _check_patterns(self, borrower: Dict[str, Any], loan_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for suspicious patterns.
        
        Args:
            borrower: Borrower profile
            loan_request: Loan request details
            
        Returns:
            Pattern check result
        """
        factors = []
        flags = []
        score = 0.0
        
        # Check for generic/suspicious loan purposes
        purpose = loan_request.get("purpose", "").lower()
        suspicious_purposes = ["urgent", "emergency", "immediate", "asap"]
        
        if any(keyword in purpose for keyword in suspicious_purposes):
            score += 0.2
            factors.append({
                "factor": "Suspicious purpose",
                "impact": 0.2,
                "explanation": f"Loan purpose contains urgent keywords: '{purpose}'"
            })
            flags.append("SUSPICIOUS_PURPOSE")
        
        # Check for suspicious IP (placeholder - needs real IP analysis)
        ip_address = borrower.get("ip_address", "")
        if ip_address and ip_address.startswith("10."):
            # Just an example - real implementation would check against blacklist
            score += 0.1
            factors.append({
                "factor": "IP check",
                "impact": 0.1,
                "explanation": f"IP address flagged: {ip_address}"
            })
            flags.append("SUSPICIOUS_IP")
        
        # Default: no pattern issues
        if not factors:
            factors.append({
                "factor": "Pattern check",
                "impact": 0.0,
                "explanation": "No suspicious patterns detected"
            })
        
        return {
            "score": score,
            "factors": factors,
            "flags": flags
        }
    
    def _compute_confidence(self, factors: List[Dict[str, Any]]) -> float:
        """
        Compute confidence in fraud detection.
        
        More factors = higher confidence.
        
        Args:
            factors: List of fraud factors
            
        Returns:
            Confidence score (0.0-1.0)
        """
        factor_count = len(factors)
        
        if factor_count >= 5:
            return 0.95
        elif factor_count >= 3:
            return 0.75
        elif factor_count >= 1:
            return 0.50
        else:
            return 0.0
    
    def _get_risk_level(self, fraud_score: float) -> str:
        """
        Map fraud score to risk level.
        
        Args:
            fraud_score: Fraud probability (0.0-1.0)
            
        Returns:
            Risk level string
        """
        if fraud_score >= 0.7:
            return "critical"
        elif fraud_score >= 0.4:
            return "high"
        elif fraud_score >= 0.2:
            return "medium"
        else:
            return "low"
    
    def explain(self, input_data: dict, prediction: dict) -> dict:
        """Generate explanation for fraud detection."""
        fraud_score = prediction.get("fraud_score", 0.0)
        is_fraud = prediction.get("is_fraud", False)
        flags = prediction.get("flags", [])
        factors = prediction.get("factors", [])
        
        if is_fraud:
            summary = f"FRAUD DETECTED: {fraud_score:.2f} fraud probability. Flags: {', '.join(flags)}"
        else:
            summary = f"No fraud detected. Fraud probability: {fraud_score:.2f}"
        
        return {
            "summary": summary,
            "factors": factors,
            "details": {"flags": flags, "fraud_score": fraud_score}
        }
    
    def _is_fraudulent(self, fraud_score: float) -> bool:
        """Check if fraud score exceeds threshold."""
        return fraud_score >= self.risk_threshold


# Singleton instance for module-level access
_fraud_rules_model_instance = FraudRulesModel()


def detect_fraud(borrower: Dict[str, Any], loan_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Module-level function for backward compatibility.
    
    Args:
        borrower: Borrower profile dictionary
        loan_request: Loan request details dictionary
        
    Returns:
        Fraud detection result
    """
    return _fraud_rules_model_instance.predict(borrower, loan_request)

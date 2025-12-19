"""
SYSTEM ROLE:
You are integrating TrustGraph AI into a fraud detection engine.

PROJECT:
CreditBridge — TrustGraph Fraud Adapter.

TASK:
Treat TrustGraph output as a feature-derived fraud signal.

TrustGraph Fraud Detection Adapter

Adapter for trust graph-based fraud detection using network analysis.

Features:
- Fraud ring detection via trust network
- Peer default pattern analysis
- Network-based risk assessment
- Feature-driven architecture (TrustGraph metrics as features)

Design:
- Adapter pattern for TrustGraphModel integration
- TrustGraph output treated as feature signals
- Complements rule-based detection
- Implements FraudDetector interface (production-grade)
- Maintains legacy BaseFraudDetector for backward compatibility

Requirements:
1. Class name: TrustGraphFraudDetector
2. Inherit from FraudDetector
3. Accept TrustGraph metrics as features
4. Map trust_score and flag_risk into fraud_score and flags
5. Preserve TrustGraph explanation

Output Format:
{
    "fraud_score": float (0.0-1.0),
    "flags": list[str],
    "explanation": list[str]
}
"""

from typing import Dict, Any, Optional, List
from .base import BaseFraudDetector, FraudDetector, FraudDetectionResult, FeatureCompatibilityError


class TrustGraphFraudDetector(FraudDetector, BaseFraudDetector):
    """
    Feature-driven trust graph-based fraud detector using network analysis.
    
    FUNCTIONAL REQUIREMENT:
    Treats TrustGraph output as feature-derived signals, not raw data.
    
    Adapter Pattern:
    - Accepts TrustGraph metrics as features
    - Maps trust_score → fraud_score
    - Maps flag_risk → fraud flags
    - Preserves TrustGraph explanations
    
    Features:
    - Fraud ring detection
    - Peer default analysis
    - Network connectivity assessment
    - Trust score validation
    
    Implements:
    - FraudDetector (primary production-grade interface)
    - BaseFraudDetector (legacy backward compatibility)
    """
    
    def __init__(self):
        """Initialize feature-driven trust graph fraud detector."""
        self.detector_version = "2.0.0"
    
    @property
    def name(self) -> str:
        """
        Get detector name.
        
        Returns:
            str: Detector identifier with version
        """
        return f"TrustGraphFraudDetector-v{self.detector_version}"
    
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
        """
        Return list of required feature keys.
        
        TrustGraph operates on trust network metrics (not behavioral features).
        Returns empty list since it doesn't require behavioral features.
        """
        return []
    
    def get_name(self) -> str:
        """Legacy method for backward compatibility."""
        return self.name
    
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate fraud risk using TrustGraph features.
        
        FUNCTIONAL REQUIREMENT:
        Treats TrustGraph output as feature-derived signals.
        
        ADAPTER LOGIC:
        1. Extract TrustGraph features from input
        2. Map trust_score → fraud_score (inverse relationship)
        3. Map flag_risk → fraud flags
        4. Preserve TrustGraph explanations
        
        Args:
            input_data: Input containing:
                - "features": dict (optional, for compatibility)
                - "feature_set": str (optional, for validation)
                - "feature_version": str (optional, for validation)
                - "context": dict with trust_graph_data (TrustGraph metrics)
        
        Returns:
            dict: {
                "fraud_score": float (0.0-1.0),
                "flags": list[str],
                "explanation": list[str]
            }
        """
        # Extract features and validate (if provided)
        features = input_data.get("features", {})
        feature_set = input_data.get("feature_set", "core_behavioral")
        feature_version = input_data.get("feature_version", "v1")
        
        # Validate feature compatibility (if features provided)
        if features:
            self.validate_features(features, feature_set, feature_version)
        
        # Extract TrustGraph features from context
        context = input_data.get("context", {})
        trust_graph_data = context.get("trust_graph_data")
        
        # Initialize output
        fraud_score = 0.0
        flags: List[str] = []
        explanation: List[str] = []
        
        # ADAPTER: Map TrustGraph features to fraud detection format
        if trust_graph_data:
            # Extract TrustGraph feature signals
            trust_score = trust_graph_data.get("trust_score", 1.0)
            flag_risk = trust_graph_data.get("flag_risk", False)
            default_rate = trust_graph_data.get("default_rate", 0.0)
            network_size = trust_graph_data.get("network_size", 0)
            
            # RULE 1: Map trust_score to fraud_score (inverse relationship)
            # trust_score: 1.0 (good) → fraud_score: 0.0 (safe)
            # trust_score: 0.0 (bad) → fraud_score: 1.0 (fraud)
            fraud_score = 1.0 - trust_score
            
            # RULE 2: Map flag_risk to flags
            if flag_risk:
                flags.append("fraud_ring_detected")
                explanation.append(
                    f"Potential fraud ring: {default_rate:.1%} of network peers defaulted "
                    f"(trust_score={trust_score:.2f})"
                )
            
            # RULE 3: Network isolation check
            if network_size == 0:
                fraud_score = max(fraud_score, 0.3)  # Minimum risk for isolated borrowers
                flags.append("network_isolation")
                explanation.append("Borrower has no network connections (higher risk)")
            
            # RULE 4: High default rate in network
            elif default_rate > 0.3:
                flags.append("high_peer_default_rate")
                explanation.append(
                    f"Elevated default rate ({default_rate:.1%}) in peer network"
                )
            
            # RULE 5: Low trust score
            if trust_score < 0.3:
                flags.append("very_low_trust_score")
                explanation.append(
                    f"Very low trust score ({trust_score:.2f}) in network"
                )
            elif trust_score < 0.5:
                flags.append("low_trust_score")
                explanation.append(
                    f"Low trust score ({trust_score:.2f}) in network"
                )
            
            # Add network size context
            if network_size > 0:
                explanation.append(
                    f"Network analysis based on {network_size} peer relationships"
                )
        else:
            # No trust graph data available
            fraud_score = 0.3  # Default moderate risk
            flags.append("no_trust_graph_data")
            explanation.append("No trust graph data available for borrower")
        
        # Ensure fraud_score is in [0.0, 1.0]
        fraud_score = max(0.0, min(1.0, fraud_score))
        
        return {
            "fraud_score": fraud_score,
            "flags": flags,
            "explanation": explanation
        }
    
    def detect(
        self,
        borrower_data: Dict[str, Any],
        loan_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> FraudDetectionResult:
        """
        Legacy detect method for backward compatibility.
        
        Wraps the new evaluate() method and converts output to FraudDetectionResult.
        Expects context to contain trust_graph_data (TrustGraph feature signals).
        
        Args:
            borrower_data: Borrower profile (can be empty if features in context)
            loan_data: Loan request details (can be empty)
            context: Required context with trust_graph_data (TrustGraph metrics)
        
        Returns:
            FraudDetectionResult: Detection result with network insights
        """
        # Initialize context
        context = context or {}
        
        # Prepare input for evaluate() method
        input_data = {
            "features": borrower_data.get("engineered_features", {}),
            "feature_set": borrower_data.get("feature_set", "core_behavioral"),
            "feature_version": borrower_data.get("feature_version", "v1"),
            "context": context
        }
        
        # Call new evaluate() method
        result = self.evaluate(input_data)
        
        # Extract results
        fraud_score = result["fraud_score"]
        flags = result["flags"]
        explanations = result["explanation"]
        
        # Convert flags to fraud_indicators format (legacy)
        fraud_indicators = []
        for flag in flags:
            fraud_indicators.append({
                "type": flag,
                "description": next(
                    (exp for exp in explanations if flag.replace("_", " ") in exp.lower()),
                    flag.replace("_", " ").title()
                )
            })
        
        # Determine if fraud detected
        fraud_threshold = 0.6
        is_fraud = fraud_score >= fraud_threshold
        
        # Calculate risk level
        risk_level = self.calculate_risk_level(fraud_score)
        
        # Get trust graph data for additional details
        trust_graph_data = context.get("trust_graph_data", {})
        network_size = trust_graph_data.get("network_size", 0)
        trust_score = trust_graph_data.get("trust_score", 0.0)
        
        # Calculate confidence based on network size
        confidence = min(0.4 + (network_size * 0.1), 0.9) if network_size > 0 else 0.3
        
        return FraudDetectionResult(
            is_fraud=is_fraud,
            fraud_score=fraud_score,
            risk_level=risk_level,
            fraud_indicators=fraud_indicators,
            confidence=confidence,
            detector_name=self.name,
            details={
                "network_size": network_size,
                "trust_score": trust_score,
                "flags": flags,
                "explanation": explanations
            }
        )

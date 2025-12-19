"""
TrustGraph Model for CreditBridge

Graph-based trust scoring model using peer relationship analysis.
Detects fraud rings and computes social trust scores.

Inherits from BaseModel to ensure consistent interface.
"""

from typing import Dict, List, Any
import math
from datetime import datetime
from app.ai.models.base import BaseModel


class TrustGraphModel(BaseModel):
    """
    TrustGraph model for social network trust analysis.
    
    [POC] Proof of concept implementation - production may use graph databases.
    
    Analyzes peer relationships to:
    - Compute trust scores (0.0-1.0)
    - Detect fraud rings (clusters of defaulting peers)
    - Identify trusted borrowers in communities
    
    Features:
    - Graph-based analysis (no external graph DB)
    - Logarithmic weight scaling for interactions
    - Fraud ring detection (>50% defaulted peers)
    - Privacy-preserving (only metadata used)
    """
    
    @property
    def name(self) -> str:
        """Return model name and version."""
        return "TrustGraphModel-v1.0-POC"
    
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
        # TrustGraph operates on relationship data, not behavioral features
        # Return empty list since it doesn't require behavioral features
        return []
    
    def __init__(self):
        """Initialize TrustGraph model."""
        self.fraud_threshold = 0.5
        self.base_trust = 0.5
    
    def predict(self, input_data: dict) -> dict:
        """
        Compute trust score from peer relationships.
        
        Args:
            input_data: Dictionary containing borrower with relationships
        
        Returns:
            Dictionary with trust_score, flag_risk, confidence, metadata
        """
        borrower = input_data.get("borrower", {})
        borrower_id = borrower.get("borrower_id", "unknown")
        relationships = borrower.get("relationships", [])
        
        # Compute trust score
        result = self._compute_trust_score(borrower_id, relationships)
        
        # Store detailed result for explain() method
        self._last_result = result
        
        # Return simplified format as per requirements
        return {
            "trust_score": result["trust_score"],
            "flag_risk": result["flag_risk"]
        }
    
    def _compute_trust_score(self, borrower_id: str, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Internal trust score computation.
        
        Args:
            borrower_id: Unique borrower identifier
            relationships: List of peer relationships
        
        Returns:
            Dictionary with trust analysis
        """
        # Initialize base trust
        trust_score = self.base_trust
        explanation = [f"Base trust score: {self.base_trust} (neutral starting point)"]
        
        # Handle no relationships
        if not relationships:
            explanation.append("[!] No peer relationships found (isolated borrower)")
            return {
                "trust_score": trust_score,
                "flag_risk": False,
                "explanation": explanation,
                "peer_analysis": {
                    "total_peers": 0,
                    "good_peers": 0,
                    "defaulted_peers": 0,
                    "total_interactions": 0
                }
            }
        
        # Analyze relationships
        total_peers = len(relationships)
        good_peers = 0
        defaulted_peers = 0
        total_interactions = 0
        trust_adjustment = 0.0
        
        for rel in relationships:
            peer_id = rel.get("peer_id", "unknown")
            interaction_count = rel.get("interaction_count", 0)
            peer_defaulted = rel.get("peer_defaulted", False)
            
            total_interactions += interaction_count
            
            # Logarithmic weight scaling
            weight = math.log(1 + interaction_count) / 10.0
            
            if peer_defaulted:
                defaulted_peers += 1
                trust_adjustment -= weight
                explanation.append(
                    f"[-] Defaulted peer (peer: {peer_id[:8]}..., "
                    f"{interaction_count} interactions): -{weight:.3f}"
                )
            else:
                good_peers += 1
                trust_adjustment += weight
                explanation.append(
                    f"[+] Reliable peer (peer: {peer_id[:8]}..., "
                    f"{interaction_count} interactions): +{weight:.3f}"
                )
        
        # Apply adjustment
        trust_score = self._clamp_trust(self.base_trust + trust_adjustment)
        explanation.append(f"Total adjustment: {trust_adjustment:+.3f}")
        explanation.append(f"Final trust score: {trust_score:.3f}")
        
        # Fraud ring detection
        defaulted_pct = (defaulted_peers / total_peers) * 100
        flag_risk = defaulted_pct > (self.fraud_threshold * 100)
        
        if flag_risk:
            explanation.append(
                f"[!!!] FRAUD RING ALERT: {defaulted_pct:.1f}% defaulted "
                f"({defaulted_peers}/{total_peers})"
            )
        else:
            explanation.append(
                f"[OK] {defaulted_pct:.1f}% defaulted - below threshold"
            )
        
        return {
            "trust_score": round(trust_score, 3),
            "flag_risk": flag_risk,
            "explanation": explanation,
            "peer_analysis": {
                "total_peers": total_peers,
                "good_peers": good_peers,
                "defaulted_peers": defaulted_peers,
                "defaulted_percentage": round(defaulted_pct, 2),
                "total_interactions": total_interactions
            }
        }
    
    def _compute_confidence(self, result: Dict[str, Any]) -> float:
        """
        Compute confidence based on peer count.
        
        More peers = higher confidence in trust score.
        
        Args:
            result: Trust computation result
            
        Returns:
            Confidence score (0.0-1.0)
        """
        total_peers = result["peer_analysis"]["total_peers"]
        
        if total_peers == 0:
            return 0.0
        elif total_peers < 3:
            return 0.5
        elif total_peers < 10:
            return 0.75
        else:
            return 0.95
    
    def _convert_explanation_to_factors(self, explanation: List[str]) -> List[Dict[str, Any]]:
        """
        Convert explanation lines to factor format.
        
        Args:
            explanation: List of explanation strings
            
        Returns:
            List of factor dictionaries
        """
        factors = []
        for line in explanation:
            if "[+]" in line:
                factors.append({
                    "factor": "Positive peer connection",
                    "impact": "+trust",
                    "explanation": line.replace("[+]", "").strip()
                })
            elif "[-]" in line:
                factors.append({
                    "factor": "Negative peer connection",
                    "impact": "-trust",
                    "explanation": line.replace("[-]", "").strip()
                })
            elif "[!!!]" in line:
                factors.append({
                    "factor": "FRAUD RING DETECTED",
                    "impact": "critical",
                    "explanation": line.replace("[!!!]", "").strip()
                })
        
        return factors
    
    def _clamp_trust(self, trust: float) -> float:
        """Clamp trust score to 0.0-1.0."""
        return max(0.0, min(1.0, trust))
    
    def explain(self, input_data: dict, prediction: dict) -> dict:
        """Generate explanation for trust score."""
        trust_score = prediction.get("trust_score", 0.5)
        flag_risk = prediction.get("flag_risk", False)
        
        # Retrieve detailed result from last prediction
        result = getattr(self, '_last_result', {})
        explanation = result.get("explanation", [])
        peer_analysis = result.get("peer_analysis", {})
        factors = self._convert_explanation_to_factors(explanation)
        
        if flag_risk:
            summary = f"FRAUD RING DETECTED: Trust score {trust_score:.3f} with fraud indicators"
        else:
            summary = f"Trust score: {trust_score:.3f}/1.0 based on peer network analysis"
        
        return {
            "summary": summary,
            "factors": factors,
            "details": peer_analysis,
            "explanation_lines": explanation
        }
    
    def integrate_with_credit(
        self,
        credit_score: int,
        trust_score: float,
        flag_risk: bool
    ) -> Dict[str, Any]:
        """
        Integrate trust score with credit score.
        
        Args:
            credit_score: Original credit score (0-100)
            trust_score: Trust score (0.0-1.0)
            flag_risk: Fraud ring flag
            
        Returns:
            Dictionary with integrated score and decision
        """
        if flag_risk:
            return {
                "adjusted_credit_score": credit_score,
                "decision_override": "reject",
                "explanation": "Fraud ring detected - application rejected"
            }
        
        # Trust-based adjustment
        if trust_score >= 0.7:
            adjustment = int((trust_score - 0.7) / 0.3 * 10)
            explanation = f"High trust ({trust_score:.2f}) → +{adjustment} points"
        elif trust_score <= 0.3:
            adjustment = -int((0.3 - trust_score) / 0.3 * 10)
            explanation = f"Low trust ({trust_score:.2f}) → {adjustment} points"
        else:
            adjustment = 0
            explanation = f"Medium trust ({trust_score:.2f}) → neutral"
        
        adjusted_score = max(0, min(100, credit_score + adjustment))
        
        return {
            "adjusted_credit_score": adjusted_score,
            "decision_override": None,
            "explanation": explanation
        }


# Singleton instance for module-level access
_trustgraph_model_instance = TrustGraphModel()


def compute_trust_score(borrower_id: str, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Module-level function for backward compatibility.
    
    Args:
        borrower_id: Unique borrower identifier
        relationships: List of peer relationships
        
    Returns:
        Trust scoring result
    """
    borrower = {
        "borrower_id": borrower_id,
        "relationships": relationships
    }
    return _trustgraph_model_instance._compute_trust_score(borrower_id, relationships)


def integrate_trust_with_credit(
    credit_score: int,
    trust_score: float,
    flag_risk: bool
) -> Dict[str, Any]:
    """
    Module-level function for trust-credit integration.
    
    Args:
        credit_score: Credit score (0-100)
        trust_score: Trust score (0.0-1.0)
        flag_risk: Fraud risk flag
        
    Returns:
        Integration result
    """
    return _trustgraph_model_instance.integrate_with_credit(credit_score, trust_score, flag_risk)

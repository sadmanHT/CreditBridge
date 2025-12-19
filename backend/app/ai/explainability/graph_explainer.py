"""
Graph-Based Model Explainer
Generates explanations for trust graph peer network analysis
"""

from typing import Dict, Any, List
from .base import BaseExplainer


class GraphExplainer(BaseExplainer):
    """
    Explainer for graph-based trust network models.
    
    Analyzes peer interactions, trust relationships, and network patterns
    to generate human-readable explanations of trust scores.
    
    Supports:
    - TrustGraphModel-v1.0-POC
    - Future graph-based variants
    """
    
    def supports(self, model_name: str) -> bool:
        """Check if this explainer supports the given model."""
        supported_models = [
            "TrustGraphModel",
            "TrustGraphModel-v1.0-POC",
            "GraphModel"
        ]
        return any(supported in model_name for supported in supported_models)
    
    def explain(self, input_data: dict, model_output: dict) -> dict:
        """
        Generate explanation for trust graph analysis.
        
        Args:
            input_data: Original input data (borrower with peers)
            model_output: Model prediction with trust_score and flag_risk
        
        Returns:
            Structured explanation with network analysis and trust factors
        """
        trust_score = model_output.get("trust_score", 0.0)
        flag_risk = model_output.get("flag_risk", False)
        
        # Extract network factors
        factors = self._extract_network_factors(input_data, trust_score, flag_risk)
        
        # Generate summary
        summary = self._generate_summary(trust_score, flag_risk, factors)
        
        # Calculate confidence based on network size
        confidence = self._calculate_confidence(input_data)
        
        return {
            "summary": summary,
            "factors": factors,
            "confidence": confidence,
            "trust_score": trust_score,
            "flag_risk": flag_risk,
            "details": {
                "method": "graph-based",
                "model": "TrustGraphModel-v1.0-POC",
                "network_analysis": "peer_interaction_weighting"
            },
            "method": "trust_graph"
        }
    
    def _extract_network_factors(self, input_data: dict, trust_score: float, flag_risk: bool) -> List[Dict[str, Any]]:
        """Extract and format network analysis factors."""
        factors = []
        
        borrower = input_data.get("borrower", {})
        peers = borrower.get("peers", [])
        
        # Network size factor
        num_peers = len(peers)
        if num_peers == 0:
            factors.append({
                "factor": "Network Size",
                "impact": "neutral",
                "explanation": "No peer network data available",
                "value": 0,
                "weight": 0.0
            })
        else:
            factors.append({
                "factor": "Network Size",
                "impact": "positive" if num_peers >= 3 else "neutral",
                "explanation": f"{num_peers} peer connection(s) analyzed",
                "value": num_peers,
                "weight": self._calculate_network_weight(num_peers)
            })
        
        # Peer performance analysis
        if peers:
            repaid_peers = [p for p in peers if p.get("repaid", False)]
            defaulted_peers = [p for p in peers if not p.get("repaid", False)]
            
            repaid_pct = (len(repaid_peers) / len(peers)) * 100 if peers else 0
            
            if repaid_pct >= 70:
                factors.append({
                    "factor": "Peer Repayment History",
                    "impact": "positive",
                    "explanation": f"{len(repaid_peers)}/{len(peers)} peers have good repayment history ({repaid_pct:.0f}%)",
                    "value": repaid_pct,
                    "weight": 0.4
                })
            elif repaid_pct >= 50:
                factors.append({
                    "factor": "Peer Repayment History",
                    "impact": "neutral",
                    "explanation": f"{len(repaid_peers)}/{len(peers)} peers have mixed history ({repaid_pct:.0f}%)",
                    "value": repaid_pct,
                    "weight": 0.2
                })
            else:
                factors.append({
                    "factor": "Peer Repayment History",
                    "impact": "negative",
                    "explanation": f"{len(repaid_peers)}/{len(peers)} peers have poor history ({repaid_pct:.0f}%)",
                    "value": repaid_pct,
                    "weight": -0.3
                })
        
        # Fraud ring detection
        if flag_risk:
            factors.append({
                "factor": "Fraud Ring Detection",
                "impact": "negative",
                "explanation": "High concentration of defaulted peers detected (>50%)",
                "value": True,
                "weight": -0.5
            })
        
        # Interaction strength
        if peers:
            total_interactions = sum(p.get("interactions", 0) for p in peers)
            avg_interactions = total_interactions / len(peers) if peers else 0
            
            if avg_interactions >= 10:
                factors.append({
                    "factor": "Interaction Strength",
                    "impact": "positive",
                    "explanation": f"Strong peer relationships (avg {avg_interactions:.1f} interactions)",
                    "value": avg_interactions,
                    "weight": 0.3
                })
            elif avg_interactions >= 5:
                factors.append({
                    "factor": "Interaction Strength",
                    "impact": "neutral",
                    "explanation": f"Moderate peer relationships (avg {avg_interactions:.1f} interactions)",
                    "value": avg_interactions,
                    "weight": 0.1
                })
            else:
                factors.append({
                    "factor": "Interaction Strength",
                    "impact": "weak",
                    "explanation": f"Limited peer interactions (avg {avg_interactions:.1f})",
                    "value": avg_interactions,
                    "weight": 0.05
                })
        
        return factors
    
    def _generate_summary(self, trust_score: float, flag_risk: bool, factors: List[dict]) -> str:
        """Generate human-readable summary."""
        risk_status = "FLAGGED FOR REVIEW" if flag_risk else "NORMAL"
        
        summary = f"Trust Score: {trust_score:.2f}/1.00 ({risk_status})"
        
        positive_factors = [f for f in factors if f.get("impact") == "positive"]
        negative_factors = [f for f in factors if f.get("impact") == "negative"]
        
        if positive_factors:
            summary += f" - {len(positive_factors)} positive signal(s)"
        if negative_factors:
            summary += f", {len(negative_factors)} risk signal(s)"
        
        return summary
    
    def _calculate_confidence(self, input_data: dict) -> float:
        """Calculate confidence based on network data quality."""
        borrower = input_data.get("borrower", {})
        peers = borrower.get("peers", [])
        
        if not peers:
            return 0.50  # Low confidence with no network data
        
        num_peers = len(peers)
        
        # More peers = higher confidence
        if num_peers >= 5:
            return 0.85
        elif num_peers >= 3:
            return 0.75
        elif num_peers >= 1:
            return 0.60
        else:
            return 0.50
    
    def _calculate_network_weight(self, num_peers: int) -> float:
        """Calculate network weight based on size (logarithmic scaling)."""
        import math
        if num_peers == 0:
            return 0.0
        # Same formula as TrustGraphModel
        return math.log(num_peers + 1) / 5.0

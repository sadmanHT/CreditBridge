"""
TrustGraph Model Explainer
Generates explanations for graph-based trust network analysis

SYSTEM ROLE:
Explainer for graph-based trust model.

PROJECT:
CreditBridge — TrustGraph Explainability.

IMPLEMENTATION:
- Converts peer network analysis into structured explanations
- Compatible with BaseExplainer interface
- Clean and readable output format
"""

from typing import Dict, Any, List
from .base import BaseExplainer


class TrustGraphExplainer(BaseExplainer):
    """
    Explainer for TrustGraph network analysis models.
    
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
            "TrustGraph",
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
            Structured explanation with graph insights and trust factors
        """
        trust_score = model_output.get("trust_score", 0.0)
        risk_flag = model_output.get("flag_risk", False)
        
        # Extract graph insights
        graph_insights = self._extract_graph_insights(input_data, trust_score, risk_flag)
        
        # Calculate confidence based on network size
        confidence = self._calculate_confidence(input_data)
        
        return {
            "type": "graph",
            "trust_score": trust_score,
            "risk_flag": risk_flag,
            "graph_insights": graph_insights,
            "confidence": confidence,
            "details": {
                "method": "graph-based",
                "model": "TrustGraphModel-v1.0-POC",
                "network_analysis": "peer_interaction_weighting"
            },
            "method": "trust_graph"
        }
    
    def _extract_graph_insights(self, input_data: dict, trust_score: float, risk_flag: bool) -> List[Dict[str, Any]]:
        """Extract and format graph-based insights."""
        insights = []
        
        borrower = input_data.get("borrower", {})
        peers = borrower.get("peers", [])
        
        # Network size insight
        num_peers = len(peers)
        if num_peers == 0:
            insights.append({
                "insight": "No peer network data available",
                "impact": "neutral",
                "value": 0,
                "weight": 0.0
            })
        else:
            network_weight = self._calculate_network_weight(num_peers)
            insights.append({
                "insight": f"{num_peers} peer connection(s) analyzed",
                "impact": "positive" if num_peers >= 3 else "neutral",
                "value": num_peers,
                "weight": network_weight
            })
        
        # Peer performance insight
        if peers:
            repaid_peers = [p for p in peers if p.get("repaid", False)]
            defaulted_peers = [p for p in peers if not p.get("repaid", False)]
            
            repaid_pct = (len(repaid_peers) / len(peers)) * 100 if peers else 0
            
            if repaid_pct >= 70:
                insights.append({
                    "insight": f"{len(repaid_peers)}/{len(peers)} peers have good repayment history ({repaid_pct:.0f}%)",
                    "impact": "positive",
                    "value": repaid_pct,
                    "weight": 0.4
                })
            elif repaid_pct >= 50:
                insights.append({
                    "insight": f"{len(repaid_peers)}/{len(peers)} peers have mixed history ({repaid_pct:.0f}%)",
                    "impact": "neutral",
                    "value": repaid_pct,
                    "weight": 0.2
                })
            else:
                insights.append({
                    "insight": f"{len(repaid_peers)}/{len(peers)} peers have poor history ({repaid_pct:.0f}%)",
                    "impact": "negative",
                    "value": repaid_pct,
                    "weight": -0.3
                })
        
        # Fraud ring detection insight
        if risk_flag:
            insights.append({
                "insight": "High concentration of defaulted peers detected (>50%)",
                "impact": "negative",
                "value": True,
                "weight": -0.5,
                "alert": "fraud_ring_detected"
            })
        
        # Interaction strength insight
        if peers:
            total_interactions = sum(p.get("interactions", 0) for p in peers)
            avg_interactions = total_interactions / len(peers) if peers else 0
            
            if avg_interactions >= 10:
                insights.append({
                    "insight": f"Strong peer relationships (avg {avg_interactions:.1f} interactions)",
                    "impact": "positive",
                    "value": avg_interactions,
                    "weight": 0.3
                })
            elif avg_interactions >= 5:
                insights.append({
                    "insight": f"Moderate peer relationships (avg {avg_interactions:.1f} interactions)",
                    "impact": "neutral",
                    "value": avg_interactions,
                    "weight": 0.1
                })
            else:
                insights.append({
                    "insight": f"Limited peer interactions (avg {avg_interactions:.1f})",
                    "impact": "weak",
                    "value": avg_interactions,
                    "weight": 0.05
                })
        
        return insights
    
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

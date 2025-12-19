"""
TrustGraph Module for CreditBridge

This module provides backward-compatible access to TrustGraph models.
New code should use app.ai.models.trustgraph_model directly.

Design Philosophy:
- Trust flows through social networks (like reputation)
- Fraudsters often form clusters (fraud rings)
- Good borrowers tend to connect with other good borrowers
- Simple, explainable logic for regulatory compliance

Key Concepts:
- Trust Score: 0.0 (no trust) to 1.0 (high trust)
- Peer Relationships: Transaction-like connections between borrowers
- Fraud Ring Detection: Clusters where >50% of peers defaulted

Design constraints:
- No external graph databases (in-memory computation)
- Deterministic and explainable
- Privacy-preserving (only uses relationship metadata)
- Free tier only (no paid services)
"""

from typing import Dict, List, Any
from app.ai.models.trustgraph_model import (
    compute_trust_score as _compute_trust_score,
    integrate_trust_with_credit as _integrate_trust_with_credit
)


def compute_trust_score(borrower_id: str, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Backward-compatible wrapper for trust scoring.
    
    Uses the new modular TrustGraphModel under the hood.
    
    Args:
        borrower_id (str): Unique borrower identifier (for logging/audit)
        relationships (list): List of peer relationships, each containing:
            - peer_id (str): Connected peer's unique identifier
            - interaction_count (int): Number of interactions/transactions
            - peer_defaulted (bool): Whether the peer defaulted on their loans
            
    Returns:
        dict: Trust analysis containing:
            - trust_score (float): Score from 0.0 to 1.0
            - flag_risk (bool): True if potential fraud ring detected
            - explanation (list): Human-readable reasons for the score
            - peer_analysis (dict): Summary statistics
    
    Example:
        >>> relationships = [
        ...     {"peer_id": "peer-1", "interaction_count": 5, "peer_defaulted": False},
        ...     {"peer_id": "peer-2", "interaction_count": 3, "peer_defaulted": False},
        ...     {"peer_id": "peer-3", "interaction_count": 2, "peer_defaulted": True}
        ... ]
        >>> result = compute_trust_score("borrower-123", relationships)
        >>> print(result["trust_score"])
        0.65
        >>> print(result["flag_risk"])
        False
    """
    return _compute_trust_score(borrower_id, relationships)


def integrate_trust_with_credit(
    credit_score: int,
    trust_score: float,
    flag_risk: bool
) -> Dict[str, Any]:
    """
    Backward-compatible wrapper for trust-credit integration.
    
    Uses the new modular TrustGraphModel under the hood.
    
    Args:
        credit_score (int): Original credit score (0-100)
        trust_score (float): Trust score from compute_trust_score (0.0-1.0)
        flag_risk (bool): Fraud ring risk flag
        
    Returns:
        dict: Integrated decision with:
            - adjusted_credit_score (int): Credit score after trust adjustment
            - decision_override (str|None): "reject" if fraud flagged, else None
            - explanation (str): Reason for adjustment
    """
    return _integrate_trust_with_credit(credit_score, trust_score, flag_risk)


# New modular architecture available at:
# - app.ai.models.trustgraph_model (graph-based trust scoring)
# - app.ai.ensemble (multi-model ensemble)
# - app.ai.registry (model management and versioning)
"""
Credit Scoring AI Module for CreditBridge

This module provides backward-compatible access to credit scoring models.
New code should use app.ai.models.credit_rule_model directly.

Current Implementation:
- Rule-based deterministic scoring (baseline)
- Transparent, explainable factors
- Fast computation for real-time API responses
- Future: XGBoost + SHAP integration

Design constraints:
- Free tier only (no paid ML services)
- No sensitive feature bias (gender-neutral)
- Audit-ready (log all model decisions)
- Deterministic and reproducible
"""

from typing import Dict, List, Any
from app.ai.models.credit_rule_model import compute_credit_score as _compute_credit_score


def compute_credit_score(borrower: Dict[str, Any], loan_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backward-compatible wrapper for credit scoring.
    
    Uses the new modular CreditRuleModel under the hood.
    
    Args:
        borrower (dict): Borrower profile containing:
            - gender (str): Gender of borrower (NOT used in scoring)
            - region (str): Geographic region
        loan_request (dict): Loan request details containing:
            - requested_amount (float): Loan amount requested
    
    Returns:
        dict: Credit decision containing:
            - credit_score (int): Score from 0-100
            - risk_level (str): "low", "medium", or "high"
            - factors (list): List of scoring factors with their impact
    
    Example:
        >>> borrower = {"gender": "female", "region": "Dhaka"}
        >>> loan_request = {"requested_amount": 10000}
        >>> result = compute_credit_score(borrower, loan_request)
        >>> print(result["credit_score"])
        65
    """
    return _compute_credit_score(borrower, loan_request)
    factors.insert(0, {
        "factor": "Base credit score",
        "impact": base_score,
        "explanation": "Starting baseline for all borrowers"
    })
    
    # Clamp score between 0 and 100
    final_score = max(0, min(100, int(score)))
    
    # Determine risk level based on final score
    if final_score >= 70:
        risk_level = "low"
    elif final_score >= 50:
        risk_level = "medium"
    else:
        risk_level = "high"
    
    # Return structured result
    return {
        "credit_score": final_score,
        "risk_level": risk_level,
        "factors": factors,
        "model_version": "rule-based-v1.0",
        "explanation": f"Credit score of {final_score} indicates {risk_level} risk based on {len(factors)} factors"
    }


def recommend_decision(credit_score: int, risk_level: str) -> str:
    """
    Recommend an approval decision based on credit score and risk level.
    
    This is a simple threshold-based recommendation.
    Final decisions should consider additional business logic and compliance rules.
    
    Args:
        credit_score (int): Computed credit score (0-100)
        risk_level (str): Risk level ("low", "medium", "high")
    
    Returns:
        str: Recommended decision ("approved", "review", "rejected")
    """
    if credit_score >= 70:
        return "approved"
    elif credit_score >= 50:
        return "review"  # Manual review required
    else:
        return "rejected"


# Future: XGBoost Model Integration
# TODO: Train XGBoost model with historical loan data
# TODO: Integrate SHAP explainability for ML predictions
# TODO: Add fraud detection using anomaly detection
# TODO: Implement A/B testing framework for model improvements


def recommend_decision(credit_score: int, risk_level: str) -> str:
    """
    Recommend an approval decision based on credit score and risk level.
    
    This is a simple threshold-based recommendation.
    Final decisions should consider additional business logic and compliance rules.
    
    Args:
        credit_score (int): Computed credit score (0-100)
        risk_level (str): Risk level ("low", "medium", "high")
    
    Returns:
        str: Recommended decision ("approved", "review", "rejected")
    """
    if credit_score >= 70:
        return "approved"
    elif credit_score >= 50:
        return "review"  # Manual review required
    else:
        return "rejected"


# New modular architecture available at:
# - app.ai.models.credit_rule_model (rule-based scoring)
# - app.ai.ensemble (multi-model ensemble)
# - app.ai.registry (model management and versioning)
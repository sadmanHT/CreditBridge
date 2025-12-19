"""
AI Models Package for CreditBridge

Contains all AI model implementations with a unified interface.
"""

from app.ai.models.base import BaseModel
from app.ai.models.credit_rule_model import RuleBasedCreditModel, compute_credit_score
from app.ai.models.trustgraph_model import TrustGraphModel, compute_trust_score, integrate_trust_with_credit
from app.ai.models.fraud_rules_model import FraudRulesModel, detect_fraud

__all__ = [
    # Base class
    "BaseModel",
    
    # Model classes
    "RuleBasedCreditModel",
    "TrustGraphModel",
    "FraudRulesModel",
    
    # Backward-compatible functions
    "compute_credit_score",
    "compute_trust_score",
    "integrate_trust_with_credit",
    "detect_fraud",
]

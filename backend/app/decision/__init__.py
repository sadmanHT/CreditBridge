"""
Decision Module

Central decision-making engine for credit approval.

Components:
- policy: Credit policies and thresholds
- rules: Pure function-based policy rules
- engine: Decision orchestration engine
"""

from .policy import CreditPolicy, get_default_policy, DecisionType, DecisionResult
from .rules import (
    RuleResult,
    REJECTION_RULES,
    REVIEW_RULES,
    APPROVAL_RULES,
)
from .engine import DecisionEngine, get_decision_engine, create_custom_engine

__all__ = [
    "CreditPolicy",
    "get_default_policy",
    "DecisionType",
    "DecisionResult",
    "RuleResult",
    "REJECTION_RULES",
    "REVIEW_RULES",
    "APPROVAL_RULES",
    "DecisionEngine",
    "get_decision_engine",
    "create_custom_engine"
]

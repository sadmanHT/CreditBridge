"""
Credit Decision Rules

Individual policy rules as pure functions for lending decisions.

SYSTEM ROLE:
You are implementing lending policy rules
for a microfinance AI system.

PROJECT:
CreditBridge — Lending Policy Rules.

RULES STRUCTURE:
- Pure functions accepting credit_result, fraud_result, fairness_flags
- Each rule returns: triggered (bool), reason (str)
- Deterministic, readable code
- No side effects

RULE TYPES:
- Critical fraud rejection rules
- Fraud review threshold rules
- Fairness bias detection rules
- Credit approval rules

OUTPUT:
Deterministic, explainable policy rules
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════
# Rule Result Type
# ═══════════════════════════════════════════════════════════

@dataclass
class RuleResult:
    """
    Individual rule evaluation result.
    
    Attributes:
        triggered: Whether the rule was triggered
        reason: Explanation of why the rule triggered
    """
    triggered: bool
    reason: str


# ═══════════════════════════════════════════════════════════
# FRAUD RULES
# ═══════════════════════════════════════════════════════════

def rule_critical_fraud_rejection(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str]
) -> RuleResult:
    """
    Reject if fraud score indicates critical risk (>= 0.8).
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
    
    Returns:
        RuleResult: Rule evaluation result
    """
    fraud_score = fraud_result.get("combined_fraud_score", 0.0)
    
    if fraud_score >= 0.8:
        return RuleResult(
            triggered=True,
            reason=f"Critical fraud risk detected (score: {fraud_score:.2f})"
        )
    
    return RuleResult(triggered=False, reason="")


def rule_high_fraud_review(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str]
) -> RuleResult:
    """
    Require manual review if fraud score is elevated (0.5-0.8).
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
    
    Returns:
        RuleResult: Rule evaluation result
    """
    fraud_score = fraud_result.get("combined_fraud_score", 0.0)
    
    if 0.5 <= fraud_score < 0.8:
        return RuleResult(
            triggered=True,
            reason=f"Elevated fraud risk requires review (score: {fraud_score:.2f})"
        )
    
    return RuleResult(triggered=False, reason="")


def rule_fraud_ring_detection(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str]
) -> RuleResult:
    """
    Reject if fraud ring detected.
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
    
    Returns:
        RuleResult: Rule evaluation result
    """
    fraud_flags = fraud_result.get("consolidated_flags", [])
    
    for flag in fraud_flags:
        if "fraud_ring" in flag.lower():
            return RuleResult(
                triggered=True,
                reason="Fraud ring pattern detected"
            )
    
    return RuleResult(triggered=False, reason="")


# ═══════════════════════════════════════════════════════════
# FAIRNESS RULES
# ═══════════════════════════════════════════════════════════

def rule_fairness_bias_review(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str]
) -> RuleResult:
    """
    Require manual review if fairness bias detected.
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
    
    Returns:
        RuleResult: Rule evaluation result
    """
    if fairness_flags:
        return RuleResult(
            triggered=True,
            reason=f"Fairness bias detected: {', '.join(fairness_flags)}"
        )
    
    return RuleResult(triggered=False, reason="")


# ═══════════════════════════════════════════════════════════
# CREDIT SCORE RULES
# ═══════════════════════════════════════════════════════════

def rule_credit_score_approval(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str],
    threshold: float = 70.0
) -> RuleResult:
    """
    Approve if credit score meets threshold AND no critical fraud.
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
        threshold: Minimum credit score for approval
    
    Returns:
        RuleResult: Rule evaluation result
    """
    credit_score = credit_result.get("final_credit_score", 0.0)
    fraud_score = fraud_result.get("combined_fraud_score", 0.0)
    
    # Check credit score threshold
    if credit_score < threshold:
        return RuleResult(triggered=False, reason="")
    
    # Check no critical fraud
    if fraud_score >= 0.8:
        return RuleResult(triggered=False, reason="")
    
    return RuleResult(
        triggered=True,
        reason=f"Credit score ({credit_score:.1f}) meets approval threshold with acceptable fraud risk"
    )


def rule_low_credit_score_rejection(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str],
    threshold: float = 50.0
) -> RuleResult:
    """
    Reject if credit score below minimum threshold.
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
        threshold: Minimum acceptable credit score
    
    Returns:
        RuleResult: Rule evaluation result
    """
    credit_score = credit_result.get("final_credit_score", 0.0)
    
    if credit_score < threshold:
        return RuleResult(
            triggered=True,
            reason=f"Credit score ({credit_score:.1f}) below minimum threshold ({threshold})"
        )
    
    return RuleResult(triggered=False, reason="")


def rule_borderline_credit_review(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str],
    min_threshold: float = 50.0,
    max_threshold: float = 70.0
) -> RuleResult:
    """
    Require manual review if credit score is borderline (50-70).
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
        min_threshold: Minimum score for review
        max_threshold: Maximum score for review
    
    Returns:
        RuleResult: Rule evaluation result
    """
    credit_score = credit_result.get("final_credit_score", 0.0)
    
    if min_threshold <= credit_score < max_threshold:
        return RuleResult(
            triggered=True,
            reason=f"Borderline credit score ({credit_score:.1f}) requires manual review"
        )
    
    return RuleResult(triggered=False, reason="")


# ═══════════════════════════════════════════════════════════
# COMBINED RULES
# ═══════════════════════════════════════════════════════════

def rule_high_value_loan_review(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str],
    loan_amount: float,
    threshold: float = 200000.0
) -> RuleResult:
    """
    Require manual review for high-value loans.
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
        loan_amount: Requested loan amount
        threshold: Amount requiring review
    
    Returns:
        RuleResult: Rule evaluation result
    """
    if loan_amount >= threshold:
        return RuleResult(
            triggered=True,
            reason=f"High-value loan ({loan_amount:,.0f}) requires manual review"
        )
    
    return RuleResult(triggered=False, reason="")


def rule_excessive_loan_amount_rejection(
    credit_result: Dict[str, Any],
    fraud_result: Dict[str, Any],
    fairness_flags: List[str],
    loan_amount: float,
    max_amount: float = 500000.0
) -> RuleResult:
    """
    Reject if loan amount exceeds policy maximum.
    
    Args:
        credit_result: Credit scoring result
        fraud_result: Fraud detection result
        fairness_flags: Fairness bias flags
        loan_amount: Requested loan amount
        max_amount: Maximum allowed amount
    
    Returns:
        RuleResult: Rule evaluation result
    """
    if loan_amount > max_amount:
        return RuleResult(
            triggered=True,
            reason=f"Requested amount ({loan_amount:,.0f}) exceeds maximum ({max_amount:,.0f})"
        )
    
    return RuleResult(triggered=False, reason="")


# ═══════════════════════════════════════════════════════════
# RULE REGISTRY
# ═══════════════════════════════════════════════════════════

# Critical rejection rules (highest priority)
REJECTION_RULES = [
    rule_critical_fraud_rejection,
    rule_fraud_ring_detection,
    rule_low_credit_score_rejection,
    rule_excessive_loan_amount_rejection,
]

# Manual review rules (medium priority)
REVIEW_RULES = [
    rule_high_fraud_review,
    rule_fairness_bias_review,
    rule_borderline_credit_review,
    rule_high_value_loan_review,
]

# Approval rules (lowest priority, checked last)
APPROVAL_RULES = [
    rule_credit_score_approval,
]




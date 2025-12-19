"""
Credit Decision Policy

Defines thresholds, limits, and policy parameters for credit decisions.

SYSTEM ROLE:
You are designing a formal decision policy framework
for a fintech lending platform.

PROJECT:
CreditBridge — Decision Policy Layer.

POLICY STRUCTURE:
- Decision type enums (APPROVE, REJECT, REVIEW)
- DecisionResult data structure
- Score thresholds for approval/rejection
- Loan amount limits
- Risk level definitions
- Override conditions

OUTPUT:
Clean, explicit policy definitions
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


# ═══════════════════════════════════════════════════════════
# Decision Type Constants
# ═══════════════════════════════════════════════════════════

class DecisionType(str, Enum):
    """
    Decision type enumeration.
    
    Defines the three possible credit decision outcomes.
    Note: Database constraint only allows 'approved' and 'rejected'.
    'REVIEW' is mapped to 'rejected' for database compatibility.
    """
    APPROVE = "approved"
    REJECT = "rejected"
    REVIEW = "rejected"  # Database doesn't have 'review' - map to 'rejected' for manual review


# ═══════════════════════════════════════════════════════════
# Decision Result Data Structure
# ═══════════════════════════════════════════════════════════

@dataclass
class DecisionResult:
    """
    Credit decision result data structure.
    
    Core policy object containing decision outcome and rationale.
    
    Attributes:
        decision: Final decision (APPROVE, REJECT, or REVIEW)
        reasons: List of reasons explaining the decision
        policy_version: Version of policy used for this decision
    """
    decision: str
    reasons: List[str] = field(default_factory=list)
    policy_version: str = "1.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Export result as dictionary."""
        return {
            "decision": self.decision,
            "reasons": self.reasons,
            "policy_version": self.policy_version
        }


@dataclass
class CreditPolicy:
    """
    Credit decision policy configuration.
    
    Defines thresholds and limits for credit approval decisions.
    
    Attributes:
        min_approval_score: Minimum credit score for auto-approval
        min_review_score: Minimum credit score for manual review
        max_loan_amount: Maximum loan amount allowed
        max_fraud_score: Maximum fraud score tolerated
        require_manual_review_above: Loan amount requiring manual review
    """
    
    # Credit score thresholds (0-100 scale)
    min_approval_score: float = 70.0
    min_review_score: float = 50.0
    
    # Loan amount limits (in local currency)
    max_loan_amount: float = 500000.0
    require_manual_review_above: float = 200000.0
    
    # Fraud score thresholds (0.0-1.0 scale)
    max_fraud_score: float = 0.6
    
    # Borrower eligibility
    min_age: int = 18
    max_age: int = 75
    min_employment_months: int = 6
    
    # Risk level definitions
    critical_risk_threshold: float = 0.8
    high_risk_threshold: float = 0.6
    medium_risk_threshold: float = 0.3
    
    # Velocity checks
    max_applications_per_month: int = 3
    min_days_between_applications: int = 7
    
    # Additional constraints
    min_employment_months: int = 6
    min_age: int = 18
    max_age: int = 70
    
    def validate_loan_amount(self, amount: float) -> bool:
        """
        Validate if loan amount is within policy limits.
        
        Args:
            amount: Requested loan amount
        
        Returns:
            bool: True if valid, False otherwise
        """
        return 0 < amount <= self.max_loan_amount
    
    def requires_manual_review(self, amount: float, credit_score: float, fraud_score: float) -> bool:
        """
        Determine if application requires manual review.
        
        Args:
            amount: Requested loan amount
            credit_score: Credit score (0-100)
            fraud_score: Fraud score (0.0-1.0)
        
        Returns:
            bool: True if manual review required
        """
        # High loan amount
        if amount >= self.require_manual_review_above:
            return True
        
        # Borderline credit score
        if self.min_review_score <= credit_score < self.min_approval_score:
            return True
        
        # Elevated fraud risk
        if 0.3 <= fraud_score < self.max_fraud_score:
            return True
        
        return False
    
    def get_decision_from_score(self, credit_score: float) -> str:
        """
        Get initial decision based on credit score.
        
        Args:
            credit_score: Credit score (0-100)
        
        Returns:
            str: Decision ("approved", "rejected")
            Note: No "review" option - database only supports approved/rejected
        """
        if credit_score >= self.min_approval_score:
            return "approved"
        else:
            return "rejected"
    
    def get_risk_level(self, fraud_score: float) -> str:
        """
        Get risk level from fraud score.
        
        Args:
            fraud_score: Fraud score (0.0-1.0)
        
        Returns:
            str: Risk level ("low", "medium", "high", "critical")
        """
        if fraud_score >= self.critical_risk_threshold:
            return "critical"
        elif fraud_score >= self.high_risk_threshold:
            return "high"
        elif fraud_score >= self.medium_risk_threshold:
            return "medium"
        else:
            return "low"
    
    def to_dict(self) -> Dict[str, Any]:
        """Export policy as dictionary."""
        return {
            "min_approval_score": self.min_approval_score,
            "min_review_score": self.min_review_score,
            "max_loan_amount": self.max_loan_amount,
            "require_manual_review_above": self.require_manual_review_above,
            "max_fraud_score": self.max_fraud_score,
            "critical_risk_threshold": self.critical_risk_threshold,
            "high_risk_threshold": self.high_risk_threshold,
            "medium_risk_threshold": self.medium_risk_threshold,
            "max_applications_per_month": self.max_applications_per_month,
            "min_days_between_applications": self.min_days_between_applications,
            "min_employment_months": self.min_employment_months,
            "min_age": self.min_age,
            "max_age": self.max_age
        }


# Default policy instance
_default_policy: Optional[CreditPolicy] = None


def get_default_policy() -> CreditPolicy:
    """
    Get the default credit policy.
    
    Singleton pattern for policy configuration.
    
    Returns:
        CreditPolicy: Default policy instance
    """
    global _default_policy
    
    if _default_policy is None:
        _default_policy = CreditPolicy()
    
    return _default_policy


def create_custom_policy(
    min_approval_score: float = 70.0,
    min_review_score: float = 50.0,
    max_loan_amount: float = 500000.0,
    **kwargs
) -> CreditPolicy:
    """
    Create a custom credit policy.
    
    Args:
        min_approval_score: Minimum score for approval
        min_review_score: Minimum score for review
        max_loan_amount: Maximum loan amount
        **kwargs: Additional policy parameters
    
    Returns:
        CreditPolicy: Custom policy instance
    """
    return CreditPolicy(
        min_approval_score=min_approval_score,
        min_review_score=min_review_score,
        max_loan_amount=max_loan_amount,
        **kwargs
    )

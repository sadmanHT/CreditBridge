"""
Credit Decision Engine

Orchestrates credit decisions by applying policy rules to AI signals.

SYSTEM ROLE:
You are designing a decision orchestration engine
for AI-driven lending.

PROJECT:
CreditBridge — Decision Engine.

ENGINE ARCHITECTURE:
1. Receives AI signals (credit scores, fraud scores, fairness flags)
2. Applies policy rules in defined order
3. Aggregates triggered reasons
4. Produces DecisionResult

CLEAR SEPARATION:
- AI signals: Input from ML models
- Policy decisions: Deterministic rule application

OUTPUT:
Production-quality orchestration code with versioned policy support
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .policy import CreditPolicy, get_default_policy, DecisionType, DecisionResult as PolicyDecisionResult
from .rules import (
    REJECTION_RULES,
    REVIEW_RULES,
    APPROVAL_RULES,
    RuleResult,
    rule_high_value_loan_review,
    rule_excessive_loan_amount_rejection,
)
from app.core.repository import save_decision_lineage


logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Credit decision orchestration engine.
    
    Applies policy rules to AI signals in deterministic order.
    
    Architecture:
    - Input: AI signals (credit_result, fraud_result, fairness_flags)
    - Processing: Sequential rule evaluation (REJECT → REVIEW → APPROVE)
    - Output: DecisionResult with aggregated reasons
    
    Features:
    - Deterministic rule application
    - Versioned policy support
    - Clear AI/policy separation
    - No AI logic inside engine
    """
    
    def __init__(self, policy: Optional[CreditPolicy] = None):
        """
        Initialize decision engine with policy.
        
        Args:
            policy: Credit policy. If None, uses default policy.
        """
        self.policy = policy or get_default_policy()
        self.engine_version = "2.0.0"
        self.policy_version = "1.0.0"
        logger.info(f"DecisionEngine initialized (v{self.engine_version}, policy v{self.policy_version})")
    
    def make_decision(
        self,
        credit_result: Dict[str, Any],
        fraud_result: Dict[str, Any],
        fairness_flags: Optional[List[str]] = None,
        loan_amount: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyDecisionResult:
        """
        Make credit decision by applying policy rules to AI signals.
        
        SAFETY OVERRIDES:
        - Forces REVIEW if credit_result or fraud_result are None/empty
        - Forces REVIEW if fraud_score is missing (None)
        - Ensures at least 1 reason per decision
        - Never approves without explicit policy rule trigger
        
        Args:
            credit_result: AI credit scoring result (contains final_credit_score)
            fraud_result: AI fraud detection result (contains combined_fraud_score, consolidated_flags)
            fairness_flags: Fairness bias flags from AI
            loan_amount: Requested loan amount
            context: Additional context
        
        Returns:
            PolicyDecisionResult: Decision with reasons and policy version
        """
        fairness_flags = fairness_flags or []
        context = context or {}
        loan_amount = loan_amount or context.get("loan_amount", 0)
        
        # ═══════════════════════════════════════════════════════════
        # SAFETY OVERRIDE 1: Validate critical inputs
        # ═══════════════════════════════════════════════════════════
        # Never proceed without valid AI signals - force REVIEW instead
        
        if not credit_result or not isinstance(credit_result, dict):
            logger.warning(
                "[DecisionEngine] SAFETY OVERRIDE: Missing or malformed credit_result. "
                "Forcing REVIEW decision."
            )
            return PolicyDecisionResult(
                decision=DecisionType.REVIEW,
                reasons=["Missing credit scoring result - requires manual review"],
                policy_version=self.policy_version
            )
        
        if not fraud_result or not isinstance(fraud_result, dict):
            logger.warning(
                "[DecisionEngine] SAFETY OVERRIDE: Missing or malformed fraud_result. "
                "Forcing REVIEW decision."
            )
            return PolicyDecisionResult(
                decision=DecisionType.REVIEW,
                reasons=["Missing fraud detection result - requires manual review"],
                policy_version=self.policy_version
            )
        
        # ═══════════════════════════════════════════════════════════
        # SAFETY OVERRIDE 2: Validate fraud_score availability
        # ═══════════════════════════════════════════════════════════
        # Fraud score is CRITICAL for safety - cannot approve without it
        
        # Try both keys for backwards compatibility
        fraud_score = fraud_result.get("fraud_score") or fraud_result.get("combined_fraud_score")
        if fraud_score is None:
            logger.warning(
                "[DecisionEngine] SAFETY OVERRIDE: Fraud score unavailable (None). "
                "Forcing REVIEW decision."
            )
            return PolicyDecisionResult(
                decision=DecisionType.REVIEW,
                reasons=["Fraud detection unavailable - requires manual review"],
                policy_version=self.policy_version
            )
        
        logger.info(
            f"[DecisionEngine] Processing decision: "
            f"credit_score={credit_result.get('final_credit_score', 0):.1f}, "
            f"fraud_score={fraud_score:.2f}"
        )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 1: Apply REJECTION rules (highest priority)
        # ═══════════════════════════════════════════════════════════
        rejection_reasons = []
        
        for rule in REJECTION_RULES:
            # Handle loan amount-specific rules
            if rule == rule_excessive_loan_amount_rejection:
                result = rule(credit_result, fraud_result, fairness_flags, loan_amount, self.policy.max_loan_amount)
            else:
                result = rule(credit_result, fraud_result, fairness_flags)
            
            if result.triggered:
                rejection_reasons.append(result.reason)
        
        if rejection_reasons:
            logger.info(f"[DecisionEngine] REJECTED: {len(rejection_reasons)} rule(s) triggered")
            return PolicyDecisionResult(
                decision=DecisionType.REJECT,
                reasons=rejection_reasons,
                policy_version=self.policy_version
            )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 2: Apply REVIEW rules (medium priority)
        # ═══════════════════════════════════════════════════════════
        review_reasons = []
        
        for rule in REVIEW_RULES:
            # Handle loan amount-specific rules
            if rule == rule_high_value_loan_review:
                result = rule(
                    credit_result, 
                    fraud_result, 
                    fairness_flags, 
                    loan_amount, 
                    self.policy.require_manual_review_above
                )
            else:
                result = rule(credit_result, fraud_result, fairness_flags)
            
            if result.triggered:
                review_reasons.append(result.reason)
        
        if review_reasons:
            logger.info(f"[DecisionEngine] REVIEW: {len(review_reasons)} rule(s) triggered")
            return PolicyDecisionResult(
                decision=DecisionType.REVIEW,
                reasons=review_reasons,
                policy_version=self.policy_version
            )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 3: Apply APPROVAL rules (lowest priority)
        # ═══════════════════════════════════════════════════════════
        approval_reasons = []
        
        for rule in APPROVAL_RULES:
            result = rule(credit_result, fraud_result, fairness_flags, self.policy.min_approval_score)
            
            if result.triggered:
                approval_reasons.append(result.reason)
        
        if approval_reasons:
            logger.info(f"[DecisionEngine] APPROVED: {len(approval_reasons)} rule(s) triggered")
            
            # ═══════════════════════════════════════════════════════════
            # SAFETY OVERRIDE 3: Never approve without explicit policy rule
            # ═══════════════════════════════════════════════════════════
            # Double-check that approval was triggered by actual policy rule
            # This prevents accidental approvals due to logic errors
            
            if not approval_reasons:
                logger.error(
                    "[DecisionEngine] SAFETY OVERRIDE: Approval path reached but no approval "
                    "reasons exist. This should never happen. Forcing REVIEW."
                )
                return PolicyDecisionResult(
                    decision=DecisionType.REVIEW,
                    reasons=["Approval logic error - requires manual review"],
                    policy_version=self.policy_version
                )
            
            return PolicyDecisionResult(
                decision=DecisionType.APPROVE,
                reasons=approval_reasons,
                policy_version=self.policy_version
            )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 4: Default to REVIEW if no rules triggered
        # ═══════════════════════════════════════════════════════════
        logger.warning("[DecisionEngine] No rules triggered, defaulting to REVIEW")
        
        # ═══════════════════════════════════════════════════════════
        # SAFETY OVERRIDE 4: Ensure at least one reason per decision
        # ═══════════════════════════════════════════════════════════
        # Every decision MUST have explainable reasons
        
        default_reasons = ["No definitive policy rule triggered - requires manual review"]
        
        return PolicyDecisionResult(
            decision=DecisionType.REVIEW,
            reasons=default_reasons,
            policy_version=self.policy_version
        )
    
    def save_lineage(
        self,
        decision_id: str,
        borrower_id: str,
        credit_result: Dict[str, Any],
        fraud_result: Dict[str, Any],
        fairness_flags: List[str],
        ensemble_output: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Construct and persist decision lineage for auditability.
        
        Args:
            decision_id: UUID of the credit decision
            borrower_id: UUID of the borrower
            credit_result: Credit scoring result
            fraud_result: Fraud detection result
            fairness_flags: Fairness bias flags
            ensemble_output: Complete ensemble output
            context: Additional context
        
        Returns:
            Dict: Created lineage record
        """
        context = context or {}
        
        # Construct data_sources payload
        data_sources = {
            "borrower_profile": True,
            "loan_request": True,
            "trust_graph": context.get("trust_graph_used", False),
            "credit_bureau": False,  # POC: not used yet
            "alternative_data": context.get("alternative_data_used", False)
        }
        
        # Construct models_used payload
        models_used = {
            "credit_scoring": {
                "model": "rule-based-v1.0",
                "version": "1.0.0",
                "score": credit_result.get("final_credit_score")
            },
            "fraud_detection": {
                "model": "fraud-engine",
                "version": "2.0.0",
                "score": fraud_result.get("combined_fraud_score"),
                "detectors": fraud_result.get("detector_outputs", [])
            },
            "trust_graph": {
                "model": "trustgraph-v1.0",
                "version": "1.0.0",
                "used": context.get("trust_graph_used", False)
            },
            "fairness_monitor": {
                "model": "fairness-v1.0",
                "version": "1.0.0",
                "flags": fairness_flags
            }
        }
        
        # Construct fraud_checks payload
        fraud_checks = {
            "fraud_score": fraud_result.get("combined_fraud_score", 0.0),
            "fraud_flags": fraud_result.get("consolidated_flags", []),
            "fraud_explanation": fraud_result.get("explanation", []),
            "aggregation_strategy": fraud_result.get("aggregation_strategy", "unknown"),
            "detector_count": len(fraud_result.get("detector_outputs", []))
        }
        
        # Persist lineage
        lineage_record = save_decision_lineage(
            decision_id=decision_id,
            borrower_id=borrower_id,
            data_sources=data_sources,
            models_used=models_used,
            policy_version=self.policy_version,
            fraud_checks=fraud_checks
        )
        
        logger.info(
            f"[DecisionEngine] Lineage saved: decision_id={decision_id}, "
            f"models={len(models_used)}, fraud_score={fraud_checks['fraud_score']:.2f}"
        )
        
        return lineage_record
    
    def make_decision_with_context(
        self,
        borrower: Dict[str, Any],
        loan_request: Dict[str, Any],
        ensemble_output: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make decision with full context (backward compatibility method).
        
        Extracts AI signals from ensemble output and calls make_decision().
        Then enriches result with metadata and explainability.
        
        Args:
            borrower: Borrower profile
            loan_request: Loan request details
            ensemble_output: Output from ModelEnsemble
            context: Additional context
        
        Returns:
            Dict: Complete decision with metadata and explainability
        """
        # Extract AI signals
        credit_result = {"final_credit_score": ensemble_output.get("final_credit_score", 0.0)}
        fraud_result = ensemble_output.get("fraud_result", {})
        fairness_flags = context.get("fairness_flags", []) if context else []
        loan_amount = loan_request.get("requested_amount", 0)
        
        # Make policy decision
        decision_result = self.make_decision(
            credit_result=credit_result,
            fraud_result=fraud_result,
            fairness_flags=fairness_flags,
            loan_amount=loan_amount,
            context=context
        )
        
        # Build enriched output
        output = {
            "decision": decision_result.decision,
            "reasons": decision_result.reasons,
            "policy_version": decision_result.policy_version,
            
            # AI signals (for transparency)
            "ai_signals": {
                "credit_score": credit_result["final_credit_score"],
                "fraud_score": fraud_result.get("combined_fraud_score", 0.0),
                "fraud_flags": fraud_result.get("consolidated_flags", []),
                "fairness_flags": fairness_flags
            },
            
            # Metadata
            "metadata": {
                "engine_version": self.engine_version,
                "policy_version": self.policy_version,
                "timestamp": datetime.utcnow().isoformat(),
                "borrower_id": borrower.get("id"),
                "loan_amount": loan_amount
            }
        }
        
        # Persist decision lineage if decision_id and borrower_id available in context
        if context:
            decision_id = context.get("decision_id")
            borrower_id = borrower.get("id")
            
            if decision_id and borrower_id:
                try:
                    self.save_lineage(
                        decision_id=str(decision_id),
                        borrower_id=str(borrower_id),
                        credit_result=credit_result,
                        fraud_result=fraud_result,
                        fairness_flags=fairness_flags,
                        ensemble_output=ensemble_output,
                        context=context
                    )
                except Exception as e:
                    logger.error(f"[DecisionEngine] Failed to save lineage: {str(e)}")
                    # Non-blocking: lineage failure should not prevent decision
        
        return output


# ═══════════════════════════════════════════════════════════
# Singleton pattern for global access
# ═══════════════════════════════════════════════════════════
_default_engine: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """
    Get default decision engine instance (singleton).
    
    Returns:
        DecisionEngine: Default engine
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = DecisionEngine()
    return _default_engine


def create_custom_engine(policy: CreditPolicy) -> DecisionEngine:
    """
    Create custom decision engine with specific policy.
    
    Args:
        policy: Custom credit policy
    
    Returns:
        DecisionEngine: Custom engine instance
    """
    return DecisionEngine(policy=policy)

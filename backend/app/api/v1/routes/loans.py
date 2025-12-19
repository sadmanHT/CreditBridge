"""
Loan Request Routes for CreditBridge

These endpoints allow authenticated borrowers to:
- Create loan requests
- View their own loan requests

Design constraints:
- JWT authentication via Supabase
- Borrowers can access ONLY their own data
- All actions must be audit-logged
- Free tier only (no background workers, no paid services)
- Background feature computation for non-blocking performance
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel
from typing import List
import logging
from app.core.supabase import supabase
from app.core.repository import create_loan_request, log_audit_event, save_credit_decision

# Setup logging
logger = logging.getLogger(__name__)
# Import rate limiting dependency AND get_current_user from deps.py
from app.api.deps import rate_limit_dependency, get_current_user as get_user_from_deps
# Import AI modules for credit scoring and explainability
from app.ai.credit_scoring import compute_credit_score
from app.ai.explainability import build_explanation
# Import TrustGraph AI for social network fraud detection
# Import Feature Engine for feature computation
from app.features.engine import FeatureEngine
from app.ai.trustgraph import compute_trust_score
# Import Fairness AI for bias monitoring and compliance
from app.ai.fairness import evaluate_fairness
# Import FraudEngine for fraud detection
from app.ai.fraud.engine import get_fraud_engine
# Import DecisionEngine for policy-based decision orchestration
from app.decision.engine import get_decision_engine
# Import background task runner for feature computation
from app.background.runner import trigger_feature_computation

router = APIRouter(prefix="/loans")


class LoanRequestCreate(BaseModel):
    requested_amount: float
    purpose: str


class DecisionOverride(BaseModel):
    decision_id: str
    action: str  # "APPROVE" | "REJECT" | "ESCALATE"
    reason: str


@router.post("/request", dependencies=[Depends(rate_limit_dependency)])
async def create_loan_request_endpoint(
    loan_request: LoanRequestCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    user_id: str = Depends(get_user_from_deps)
):
    """
    Create a new loan request with AI-powered credit decisioning.
    
    This endpoint performs the complete loan request flow:
    1. Fetch borrower profile
    2. Create loan request record
    3. Compute AI credit score
    4. Generate human-readable explanation
    5. Save credit decision to database
    6. Log all actions for audit compliance
    7. Trigger background feature computation (non-blocking)
    
    Args:
        loan_request: Loan request data (requested_amount, purpose)
        background_tasks: FastAPI BackgroundTasks for async feature computation
        user_id: Authenticated user ID from JWT token
        
    Returns:
        Complete response with loan request AND credit decision including:
        - loan_request: Created loan details
        - credit_decision: AI scoring result with explanation
        - background_task_queued: Confirmation that feature computation was triggered
        
    Raises:
        HTTPException: If borrower profile not found or creation fails
    """
    # SAFETY: Comprehensive error handling - never expose stack traces
    try:
        # Input validation
        if not loan_request.requested_amount or loan_request.requested_amount <= 0:
            logger.warning(
                f"[Loans API] Invalid loan amount: {loan_request.requested_amount} "
                f"from user {user_id}"
            )
            log_audit_event(
                action="invalid_loan_request",
                entity_type="loan_request",
                entity_id=None,
                metadata={"user_id": user_id, "reason": "invalid_amount"}
            )
            raise HTTPException(
                status_code=422,
                detail="Invalid loan amount. Amount must be greater than 0."
            )
        
        if not loan_request.purpose or len(loan_request.purpose.strip()) == 0:
            logger.warning(f"[Loans API] Empty loan purpose from user {user_id}")
            log_audit_event(
                action="invalid_loan_request",
                entity_type="loan_request",
                entity_id=None,
                metadata={"user_id": user_id, "reason": "empty_purpose"}
            )
            raise HTTPException(
                status_code=422,
                detail="Loan purpose cannot be empty."
            )
        
        # Step 1: Fetch borrower profile
        try:
            borrower_response = supabase.table("borrowers").select("*").eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"[Loans API] Database error fetching borrower for user {user_id}: {e}")
            log_audit_event(
                action="loan_request_failed",
                entity_type="loan_request",
                entity_id=None,
                metadata={"user_id": user_id, "error": "database_error", "stage": "fetch_borrower"}
            )
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable. Please try again later."
            )
        
        if not borrower_response.data:
            raise HTTPException(
                status_code=404,
                detail="Borrower profile not found. Please create your profile first."
            )
        
        borrower = borrower_response.data[0]
        borrower_id = borrower["id"]
        
        # Step 2: Create loan request in database
        loan = create_loan_request(
            borrower_id=borrower_id,
            requested_amount=loan_request.requested_amount,
            purpose=loan_request.purpose
        )
        
        loan_request_id = loan.get("id")
        
        # Step 3: Log initial loan request audit event
        log_audit_event(
            action="loan_requested",
            entity_type="loan_request",
            entity_id=loan_request_id,
            metadata={
                "borrower_id": borrower_id,
                "user_id": user_id,
                "requested_amount": loan_request.requested_amount,
                "purpose": loan_request.purpose
            }
        )
        
        # Step 3.5: Compute engineered features
        # This is required for the AI credit scoring model
        try:
            feature_engine = FeatureEngine(lookback_days=30)
            feature_set = feature_engine.compute_features(
                borrower_id=borrower_id,
                borrower_profile=borrower
            )
            # Add engineered features to borrower data
            borrower["engineered_features"] = feature_set.features
            logger.info(f"Computed {len(feature_set.features)} features for borrower {borrower_id}: {list(feature_set.features.keys())}")
        except Exception as e:
            logger.error(f"Feature computation failed for borrower {borrower_id}: {str(e)}", exc_info=True)
            # Don't use empty features - re-raise to see what's wrong
            raise HTTPException(
                status_code=500,
                detail=f"Feature computation failed: {str(e)}"
            )
        
        # Step 4: Compute AI Credit Score
        # Prepare borrower data for AI model (now includes engineered_features from Step 3.5)
        borrower_data = {
            "gender": borrower.get("gender"),
            "region": borrower.get("region"),
            "engineered_features": borrower.get("engineered_features", {})
        }
        
        # Prepare loan request data for AI model
        loan_data = {
            "requested_amount": loan_request.requested_amount
        }
        
        # Compute BASE credit score using rule-based AI engine
        score_result = compute_credit_score(borrower_data, loan_data)
        base_credit_score = score_result.get("credit_score", 0)
        
        # Step 5: Compute TrustGraph score (social network fraud detection)
        # POC: Using mocked peer relationship data for hackathon demonstration
        # In production, this would fetch real peer data from borrower_relationships table
        mock_relationships = [
            {
                "peer_id": f"mock_peer_{borrower_id}_1",
                "interaction_count": 8,
                "peer_defaulted": False
            },
            {
                "peer_id": f"mock_peer_{borrower_id}_2", 
                "interaction_count": 5,
                "peer_defaulted": False
            },
            {
                "peer_id": f"mock_peer_{borrower_id}_3",
                "interaction_count": 2,
                "peer_defaulted": False
            }
        ]
        
        # Compute trust score from peer network
        trust_result = compute_trust_score(borrower_id, mock_relationships)
        trust_score = trust_result.get("trust_score", 0.5)  # Default to neutral trust
        flag_risk = trust_result.get("flag_risk", False)
        
        # Step 6: Combine credit and trust scores
        # Formula: final_score = base_credit_score + (trust_score * 20)
        # This gives trust score up to 20 points of influence
        # Example: base_credit=70, trust=0.8 → final=70+(0.8*20)=86
        trust_boost = trust_score * 20
        final_score = base_credit_score + trust_boost
        
        # Clamp final score to maximum 100
        final_score = min(100, final_score)
        
        # Step 7: Run FraudEngine for comprehensive fraud detection
        fraud_engine = get_fraud_engine(aggregation_strategy="max")
        fraud_input = {
            "loan": {"requested_amount": loan_request.requested_amount},
            "borrower": borrower_data,
            "features": borrower.get("engineered_features", {}),  # Required by FraudEngine
            "feature_set": feature_set.feature_set,  # "core_behavioral"
            "feature_version": feature_set.feature_version,  # "v1"
            "trust_analysis": {
                "trust_score": trust_score,
                "flag_risk": flag_risk,
                "peer_analysis": trust_result.get("peer_analysis", {})
            }
        }
        fraud_result = fraud_engine.evaluate(fraud_input)
        
        # Step 8: Collect fairness flags (empty for now, will be populated by fairness monitoring)
        fairness_flags = []
        
        # Step 9: Prepare AI signals for DecisionEngine
        credit_result = {
            "final_credit_score": final_score,
            "base_credit_score": base_credit_score,
            "trust_boost": trust_boost,
            "risk_level": score_result.get("risk_level"),
            "factors": score_result.get("factors")
        }
        
        # Step 10: Invoke DecisionEngine (replaces inline if-else logic)
        decision_engine = get_decision_engine()
        decision_result = decision_engine.make_decision(
            credit_result=credit_result,
            fraud_result=fraud_result,
            fairness_flags=fairness_flags,
            loan_amount=loan_request.requested_amount,
            context={
                "borrower_id": borrower_id,
                "loan_request_id": loan_request_id
            }
        )
        
        # Step 11: Build comprehensive explanation
        explanation = build_explanation(score_result)
        
        # Append TrustGraph explanation to credit explanation
        combined_explanation = explanation.get("summary", "") + "\n\n--- TrustGraph Analysis ---\n"
        for trust_line in trust_result.get("explanation", []):
            combined_explanation += f"• {trust_line}\n"
        combined_explanation += f"\nTrust Score Boost: +{trust_boost:.1f} points (from trust_score={trust_score:.3f})"
        
        # Append fraud analysis
        combined_explanation += "\n\n--- Fraud Detection ---\n"
        combined_explanation += f"Fraud Score: {fraud_result['fraud_score']:.2f}\n"
        if fraud_result['flags']:
            combined_explanation += "Fraud Flags:\n"
            for flag in fraud_result['flags']:
                combined_explanation += f"• {flag}\n"
        
        # Append policy decision reasoning
        combined_explanation += "\n\n--- Policy Decision ---\n"
        combined_explanation += f"Decision: {decision_result.decision}\n"
        combined_explanation += "Reasons:\n"
        for reason in decision_result.reasons:
            combined_explanation += f"• {reason}\n"
        combined_explanation += f"Policy Version: {decision_result.policy_version}"
        
        # Step 12: Save DecisionResult to database
        credit_decision_record = save_credit_decision(
            loan_request_id=loan_request_id,
            credit_score=int(final_score),
            decision=decision_result.decision,  # From DecisionEngine
            explanation=combined_explanation,
            model_version=f"ensemble-v2.0+fraud-v2.0+decision-v{decision_result.policy_version}"
        )
        
        # Step 12b: Save decision lineage for auditability
        decision_id = credit_decision_record.get("id")
        if decision_id:
            try:
                # Prepare ensemble output for lineage
                ensemble_output = {
                    "final_credit_score": final_score,
                    "fraud_result": fraud_result
                }
                
                # Build context for lineage
                lineage_context = {
                    "decision_id": decision_id,
                    "trust_graph_used": True,
                    "alternative_data_used": False
                }
                
                # Use make_decision_with_context to trigger lineage saving
                # This will internally call save_lineage
                decision_engine_with_lineage = get_decision_engine()
                decision_engine_with_lineage.save_lineage(
                    decision_id=str(decision_id),
                    borrower_id=str(borrower_id),
                    credit_result=credit_result,
                    fraud_result=fraud_result,
                    fairness_flags=fairness_flags,
                    ensemble_output=ensemble_output,
                    context=lineage_context
                )
            except Exception as lineage_error:
                # Non-blocking: log error but continue
                print(f"[!!!] Lineage saving failed (non-blocking): {str(lineage_error)}")
                log_audit_event(
                    action="decision_lineage_failed",
                    entity_type="credit_decision",
                    entity_id=decision_id,
                    metadata={"error": str(lineage_error)}
                )
        
        # Step 13: Log comprehensive audit event with AI signals and policy decision
        log_audit_event(
            action="credit_decision_with_policy_engine",
            entity_type="credit_decision",
            entity_id=credit_decision_record.get("id"),
            metadata={
                "loan_request_id": loan_request_id,
                "borrower_id": borrower_id,
                # AI Signals
                "ai_signals": {
                    "base_credit_score": base_credit_score,
                    "trust_score": trust_score,
                    "trust_boost": trust_boost,
                    "final_credit_score": final_score,
                    "fraud_score": fraud_result["fraud_score"],
                    "fraud_flags": fraud_result["flags"],
                    "fairness_flags": fairness_flags,
                    "flag_risk": flag_risk,
                    "risk_level": score_result.get("risk_level")
                },
                # Policy Decision
                "policy_decision": {
                    "decision": decision_result.decision,
                    "reasons": decision_result.reasons,
                    "policy_version": decision_result.policy_version
                },
                # Model versions
                "model_versions": {
                    "credit": "rule-based-v1.0",
                    "trustgraph": "trustgraph-v1.0",
                    "fraud": "fraud-engine-v2.0",
                    "decision": f"decision-engine-v{decision_result.policy_version}"
                },
                # Context
                "factors": score_result.get("factors"),
                "peer_analysis": trust_result.get("peer_analysis"),
                "mock_data_used": True  # Flag for POC
            }
        )
        
        # Step 14: FAIRNESS MONITORING (POC - Hackathon Safe)
        # This evaluates fairness across recent decisions for bias detection
        # NOTE: Production systems would use batch evaluation with proper sampling
        # This is a lightweight, in-memory approach for demonstration purposes
        try:
            # Collect recent credit decisions for fairness analysis
            # POC: Fetch last 20 decisions to analyze approval patterns
            recent_decisions_response = supabase.table("credit_decisions")\
                .select("id, loan_request_id, decision, created_at")\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()
            
            if recent_decisions_response.data and len(recent_decisions_response.data) >= 3:
                # Need to join with loan_requests and borrowers to get demographics
                
                # Fetch loan_requests and borrower demographics
                fairness_data = []
                for decision_record in recent_decisions_response.data:
                    # Get associated loan_request using loan_request_id foreign key
                    loan_request_id_for_decision = decision_record.get("loan_request_id")
                    
                    if loan_request_id_for_decision:
                        loan_response = supabase.table("loan_requests")\
                            .select("borrower_id")\
                            .eq("id", loan_request_id_for_decision)\
                            .execute()
                        
                        if loan_response.data:
                            borrower_id_for_decision = loan_response.data[0].get("borrower_id")
                            
                            # Get borrower demographics
                            borrower_response = supabase.table("borrowers")\
                                .select("gender, region")\
                                .eq("id", borrower_id_for_decision)\
                                .execute()
                            
                            if borrower_response.data:
                                borrower_demo = borrower_response.data[0]
                                fairness_data.append({
                                    "gender": borrower_demo.get("gender", "unknown"),
                                    "region": borrower_demo.get("region", "unknown"),
                                    "decision": decision_record.get("decision")
                                })
                
                # Evaluate fairness if we have sufficient data
                if len(fairness_data) >= 3:
                    fairness_result = evaluate_fairness(fairness_data)
                    
                    # Prepare audit metadata
                    fairness_metadata = {
                        "sample_size": len(fairness_data),
                        "approval_rates": fairness_result.get("approval_rates"),
                        "disparate_impact": fairness_result.get("disparate_impact"),
                        "bias_detected": fairness_result.get("bias_detected"),
                        "fairness_notes": fairness_result.get("notes"),
                        "evaluation_timestamp": credit_decision_record.get("created_at")
                    }
                    
                    # Add human review flag if bias detected
                    if fairness_result.get("bias_detected"):
                        fairness_metadata["human_review_recommended"] = True
                        fairness_metadata["compliance_alert"] = "Disparate impact detected - review decision criteria"
                    
                    # Log fairness evaluation to audit_logs
                    log_audit_event(
                        action="fairness_evaluation",
                        entity_type="credit_decision",
                        entity_id=credit_decision_record.get("id"),
                        metadata=fairness_metadata
                    )
        
        except Exception as fairness_error:
            # Fairness monitoring should NOT block credit decisions
            # Log error but continue processing
            print(f"[!!!] Fairness monitoring failed (non-blocking): {str(fairness_error)}")
            log_audit_event(
                action="fairness_evaluation_failed",
                entity_type="credit_decision",
                entity_id=credit_decision_record.get("id"),
                metadata={
                    "error": str(fairness_error),
                    "note": "Fairness monitoring failure - does not affect credit decision"
                }
            )
        
        # Step 15: Trigger background feature computation (non-blocking)
        # TASK: After loan request is accepted, trigger background feature computation
        # This computes and stores features asynchronously without blocking the API response
        try:
            trigger_feature_computation(
                background_tasks=background_tasks,
                borrower_id=str(borrower_id),
                feature_set="core_behavioral",
                feature_version="v1"
            )
            background_task_queued = True
            
            # Log background task trigger
            log_audit_event(
                action="background_feature_computation_triggered",
                entity_type="loan_request",
                entity_id=loan_request_id,
                metadata={
                    "borrower_id": str(borrower_id),
                    "feature_set": "core_behavioral",
                    "feature_version": "v1",
                    "trigger_timestamp": credit_decision_record.get("created_at")
                }
            )
        except Exception as bg_error:
            # Background task failure should not block loan processing
            print(f"[!!!] Background feature computation trigger failed (non-blocking): {str(bg_error)}")
            background_task_queued = False
            log_audit_event(
                action="background_feature_computation_failed",
                entity_type="loan_request",
                entity_id=loan_request_id,
                metadata={"error": str(bg_error)}
            )
        
        # Step 16: Return comprehensive response with loan AND policy-based decision
        return {
            "loan_request": {
                **loan,
                "audit_logged": True
            },
            "credit_decision": {
                "id": credit_decision_record.get("id"),
                # AI Signals (for transparency)
                "ai_signals": {
                    "base_credit_score": base_credit_score,
                    "trust_score": trust_score,
                    "trust_boost": round(trust_boost, 1),
                    "final_credit_score": int(final_score),
                    "fraud_score": fraud_result["fraud_score"],
                    "fraud_flags": fraud_result["flags"],
                    "risk_level": score_result.get("risk_level"),
                    "flag_risk": flag_risk
                },
                # Policy Decision (from DecisionEngine)
                "policy_decision": {
                    "decision": decision_result.decision,
                    "reasons": decision_result.reasons,
                    "policy_version": decision_result.policy_version
                },
                # Explanations
                "explanation": {
                    "combined": combined_explanation,
                    "credit_factors": score_result.get("factors"),
                    "trust_analysis": trust_result.get("explanation"),
                    "fraud_analysis": fraud_result["explanation"],
                    "policy_reasons": decision_result.reasons,
                    "peer_network": trust_result.get("peer_analysis")
                },
                # Metadata
                "model_version": f"ensemble-v2.0+fraud-v2.0+decision-v{decision_result.policy_version}",
                "created_at": credit_decision_record.get("created_at"),
                "poc_note": "Using DecisionEngine for policy-based decisions with AI signals"
            },
            "background_task_queued": background_task_queued,
            "background_task_note": "Feature computation running in background" if background_task_queued else "Background task failed to queue"
        }
    
    # SAFETY: Map all errors to appropriate HTTP codes, never expose stack traces
    except HTTPException:
        # Re-raise HTTP exceptions as-is (already properly formatted)
        raise
    
    except ValueError as ve:
        # SAFETY: Invalid input data - map to HTTP 422
        error_msg = str(ve)
        logger.error(f"[Loans API] Validation error for user {user_id}: {error_msg}")
        log_audit_event(
            action="loan_request_failed",
            entity_type="loan_request",
            entity_id=None,
            metadata={
                "user_id": user_id,
                "error_type": "validation_error",
                "error": error_msg
            }
        )
        raise HTTPException(
            status_code=422,
            detail=f"Invalid input data: {error_msg}"
        )
    
    except ConnectionError as ce:
        # SAFETY: Database connection error - map to HTTP 503
        logger.error(f"[Loans API] Database connection error for user {user_id}: {ce}")
        log_audit_event(
            action="loan_request_failed",
            entity_type="loan_request",
            entity_id=None,
            metadata={
                "user_id": user_id,
                "error_type": "connection_error",
                "error": "database_unavailable"
            }
        )
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again later."
        )
    
    except Exception as e:
        # SAFETY: Catch-all for unexpected errors - map to HTTP 503
        # Log full error but return sanitized message
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(
            f"[Loans API] Unexpected error creating loan request for user {user_id}: "
            f"{error_type}: {error_msg}",
            exc_info=True  # Include full stack trace in logs
        )
        log_audit_event(
            action="loan_request_failed",
            entity_type="loan_request",
            entity_id=None,
            metadata={
                "user_id": user_id,
                "error_type": error_type,
                "error": "internal_server_error"
            }
        )
        raise HTTPException(
            status_code=503,
            detail="An error occurred processing your loan request. Our team has been notified."
        )


@router.get("/my")
async def get_my_loan_requests(user_id: str = Depends(get_user_from_deps)):
    """
    Retrieve all loan requests for the authenticated borrower.
    
    Args:
        user_id: Authenticated user ID from JWT token
        
    Returns:
        List of loan requests ordered by created_at descending
        
    Raises:
        HTTPException: If borrower profile not found or fetch fails
    """
    # SAFETY: Error handling with proper HTTP codes
    try:
        # Fetch borrower profile
        try:
            borrower_response = supabase.table("borrowers").select("*").eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"[Loans API] Database error fetching borrower for user {user_id}: {e}")
            log_audit_event(
                action="get_loans_failed",
                entity_type="loan_request",
                entity_id=None,
                metadata={"user_id": user_id, "error": "database_error", "stage": "fetch_borrower"}
            )
            raise HTTPException(
                status_code=503,
                detail="Database temporarily unavailable. Please try again later."
            )
        
        if not borrower_response.data:
            raise HTTPException(
                status_code=404,
                detail="Borrower profile not found. Please create your profile first."
            )
        
        borrower_id = borrower_response.data[0]["id"]
        
        # Fetch all loan requests for this borrower
        loans_response = supabase.table("loan_requests")\
            .select("*")\
            .eq("borrower_id", borrower_id)\
            .order("created_at", desc=True)\
            .execute()
        
        return {
            "total": len(loans_response.data),
            "loan_requests": loans_response.data
        }
    
    # SAFETY: Map errors appropriately
    except HTTPException:
        raise
    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            f"[Loans API] Unexpected error fetching loan requests for user {user_id}: "
            f"{error_type}: {str(e)}",
            exc_info=True
        )
        log_audit_event(
            action="get_loans_failed",
            entity_type="loan_request",
            entity_id=None,
            metadata={"user_id": user_id, "error_type": error_type}
        )
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve loan requests. Please try again later."
        )


@router.post("/override")
async def override_decision(
    override: DecisionOverride,
    user_id: str = Depends(get_user_from_deps)
):
    """
    Override an AI credit decision with manual officer approval/rejection.
    
    This endpoint allows loan officers to manually override AI decisions
    with proper justification for regulatory audit trails.
    
    Args:
        override: Override data (decision_id, action, reason)
        user_id: Authenticated user ID from JWT token
        
    Returns:
        Confirmation of override with audit trail
        
    Raises:
        HTTPException: If decision not found or override fails
    """
    try:
        # Validate action
        valid_actions = ["APPROVE", "REJECT", "ESCALATE"]
        if override.action not in valid_actions:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            )
        
        # Fetch the credit decision
        decision_response = supabase.table("credit_decisions")\
            .select("id, loan_request_id, decision, credit_score")\
            .eq("id", override.decision_id)\
            .execute()
        
        if not decision_response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Credit decision not found: {override.decision_id}"
            )
        
        decision = decision_response.data[0]
        original_decision = decision.get("decision")
        
        # Create override record in audit log
        override_record = {
            "decision_id": override.decision_id,
            "loan_request_id": decision.get("loan_request_id"),
            "original_decision": original_decision,
            "override_action": override.action.lower(),
            "override_reason": override.reason,
            "officer_id": user_id,
            "officer_timestamp": "now()"
        }
        
        # Update the credit decision with override
        # Map override actions to valid decision values (lowercase as per DB constraint)
        action_mapping = {
            "APPROVE": "approved",
            "REJECT": "rejected",
            "ESCALATE": "review"
        }
        
        update_data = {
            "decision": action_mapping.get(override.action, override.action.lower()),
            "explanation": f"[OFFICER OVERRIDE]\nOriginal Decision: {original_decision}\nOverride Action: {override.action}\nReason: {override.reason}\n\n--- Original Explanation ---\n" + decision.get("explanation", "")
        }
        
        update_response = supabase.table("credit_decisions")\
            .update(update_data)\
            .eq("id", override.decision_id)\
            .execute()
        
        # Log audit event
        log_audit_event(
            action="decision_override",
            entity_type="credit_decision",
            entity_id=override.decision_id,
            metadata={
                "officer_id": user_id,
                "original_decision": original_decision,
                "override_action": override.action,
                "reason": override.reason,
                "loan_request_id": decision.get("loan_request_id")
            }
        )
        
        logger.info(
            f"[Loans API] Decision {override.decision_id} overridden by officer {user_id}: "
            f"{original_decision} -> {override.action}"
        )
        
        return {
            "success": True,
            "decision_id": override.decision_id,
            "original_decision": original_decision,
            "override_action": override.action,
            "message": f"Decision successfully overridden to {override.action}",
            "audit_logged": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Loans API] Override failed: {str(e)}", exc_info=True)
        log_audit_event(
            action="decision_override_failed",
            entity_type="credit_decision",
            entity_id=override.decision_id,
            metadata={"error": str(e), "officer_id": user_id}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to override decision: {str(e)}"
        )

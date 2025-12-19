"""
Compliance and Explainability Routes for CreditBridge

These endpoints provide regulator-facing audit tools for inspecting
credit decisions, fairness outcomes, and audit trail logs.

SYSTEM ROLE:
You are a fintech compliance engineer building regulator-facing audit tools.

PROJECT:
CreditBridge — Explainable, Fair, and Auditable Credit Decision Platform.

PURPOSE:
Implement compliance and explainability endpoints that allow authorized users
to inspect credit decisions and fairness outcomes. This acts as an
ExplainChain-style ledger (POC) where every decision is traceable,
explainable, and auditable.

DESIGN PHILOSOPHY:
- Transparency: Every decision has a full audit trail
- Explainability: All AI decisions include human-readable explanations
- Fairness: Bias detection logs trigger human review recommendations
- Compliance: Read-only access to decision history for regulatory audits

AUTHOR: CreditBridge Compliance Team
DATE: December 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.core.supabase import supabase
from app.api.v1.routes.borrowers import get_current_user

router = APIRouter(prefix="/compliance")


@router.get("/decisions")
async def get_credit_decisions(
    limit: int = Query(default=20, ge=1, le=100, description="Number of decisions to retrieve"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    decision_filter: Optional[str] = Query(default=None, description="Filter by decision type: approved or rejected"),
    user_id: str = Depends(get_current_user)
):
    """
    Retrieve recent credit decisions for compliance and audit purposes.
    
    This endpoint provides a compliance-friendly view of all credit decisions
    made by the AI system, including full explanations and scoring breakdowns.
    
    **ExplainChain Ledger (POC):**
    Each credit decision is permanently logged with:
    - Unique decision ID (immutable record)
    - AI model version used
    - Complete credit score calculation
    - Human-readable explanation
    - Timestamp (audit trail)
    
    **Use Cases:**
    - Regulatory audits and compliance reviews
    - Internal quality assurance checks
    - Bias detection and fairness monitoring
    - Customer dispute resolution
    - Model performance analysis
    
    **Parameters:**
    - limit: Maximum number of decisions to return (1-100, default 20)
    - offset: Pagination offset for large result sets
    - decision_filter: Optional filter for "approved" or "rejected" decisions
    
    **Returns:**
    Compliance-structured JSON containing:
    - total: Total count of matching decisions
    - decisions: Array of credit decision records with:
        - id: Unique decision identifier
        - loan_request_id: Associated loan request
        - credit_score: Final credit score (0-100)
        - decision: approved or rejected
        - explanation: Full human-readable explanation
        - model_version: AI model version identifier
        - created_at: ISO timestamp
    
    **Security:**
    Requires valid JWT authentication. In production, this would be
    restricted to compliance officers and authorized auditors.
    
    **Example Response:**
    ```json
    {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "decisions": [
        {
          "id": "uuid-123",
          "loan_request_id": "uuid-456",
          "credit_score": 85,
          "decision": "approved",
          "explanation": "Your credit score is 65, indicating medium risk...",
          "model_version": "rule-based-v1.0+trustgraph-v1.0",
          "created_at": "2025-12-16T10:26:14.333025+00:00"
        }
      ]
    }
    ```
    """
    try:
        # Build query with optional decision filter
        query = supabase.table("credit_decisions")\
            .select("id, loan_request_id, credit_score, decision, explanation, model_version, created_at", count="exact")
        
        # Apply decision filter if provided
        if decision_filter:
            if decision_filter not in ["approved", "rejected"]:
                raise HTTPException(
                    status_code=400,
                    detail="decision_filter must be either 'approved' or 'rejected'"
                )
            query = query.eq("decision", decision_filter)
        
        # Execute query with pagination
        response = query\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Return compliance-structured response
        return {
            "compliance_report": "CreditBridge Decision Ledger",
            "total": response.count,
            "limit": limit,
            "offset": offset,
            "filter_applied": decision_filter,
            "decisions": response.data,
            "note": "Each decision includes full explainability for regulatory compliance"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve credit decisions: {str(e)}"
        )


@router.get("/audit-log")
async def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200, description="Number of audit logs to retrieve"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    action_filter: Optional[str] = Query(default=None, description="Filter by action type"),
    user_id: str = Depends(get_current_user)
):
    """
    Retrieve audit logs for compliance monitoring and investigation.
    
    This endpoint provides access to the complete audit trail of all
    system actions, including credit decisions, fairness evaluations,
    and user activities.
    
    **ExplainChain Audit Trail (POC):**
    Every significant system action is logged with:
    - Action type (loan_requested, credit_decision, fairness_evaluation, etc.)
    - Entity type and ID (what was affected)
    - Full metadata (detailed context)
    - Timestamp (immutable audit trail)
    
    **Key Action Types:**
    - `loan_requested`: New loan application submitted
    - `credit_decision_with_trustgraph`: AI credit decision made
    - `fairness_evaluation`: Bias monitoring check performed
    - `fairness_evaluation_failed`: Fairness check error (non-blocking)
    
    **Fairness Monitoring:**
    When `action = fairness_evaluation`, metadata includes:
    - `approval_rates`: Gender and regional approval statistics
    - `disparate_impact`: Female/male approval rate ratio
    - `bias_detected`: Boolean flag for regulatory threshold (0.80 rule)
    - `human_review_recommended`: Flag when bias is detected
    - `compliance_alert`: Human-readable alert message
    
    **Parameters:**
    - limit: Maximum number of logs to return (1-200, default 50)
    - offset: Pagination offset for large result sets
    - action_filter: Optional filter by action type (e.g., "fairness_evaluation")
    
    **Returns:**
    Compliance-structured JSON containing:
    - total: Total count of matching audit logs
    - audit_logs: Array of audit records with:
        - id: Unique log identifier
        - action: Action type performed
        - entity_type: Type of entity affected
        - entity_id: Unique identifier of affected entity
        - metadata: Full context and details (JSON)
        - created_at: ISO timestamp
    
    **Security:**
    Requires valid JWT authentication. Production systems would implement
    role-based access control (RBAC) to restrict to authorized personnel.
    
    **Example Response:**
    ```json
    {
      "total": 120,
      "limit": 50,
      "offset": 0,
      "audit_logs": [
        {
          "id": "uuid-789",
          "action": "fairness_evaluation",
          "entity_type": "credit_decision",
          "entity_id": "uuid-123",
          "metadata": {
            "sample_size": 6,
            "approval_rates": {...},
            "disparate_impact": 0.67,
            "bias_detected": true,
            "human_review_recommended": true
          },
          "created_at": "2025-12-16T10:40:02.454874+00:00"
        }
      ]
    }
    ```
    """
    try:
        # Build query with optional action filter
        query = supabase.table("audit_logs")\
            .select("id, action, entity_type, entity_id, metadata, created_at", count="exact")
        
        # Apply action filter if provided
        if action_filter:
            query = query.eq("action", action_filter)
        
        # Execute query with pagination
        response = query\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        # Analyze audit logs for compliance insights
        action_summary = {}
        fairness_alerts = 0
        
        for log in response.data:
            action = log.get("action", "unknown")
            action_summary[action] = action_summary.get(action, 0) + 1
            
            # Count fairness alerts where bias was detected
            if action == "fairness_evaluation":
                metadata = log.get("metadata", {})
                if metadata.get("bias_detected"):
                    fairness_alerts += 1
        
        # Return compliance-structured response with summary
        return {
            "compliance_report": "CreditBridge Audit Trail",
            "total": response.count,
            "limit": limit,
            "offset": offset,
            "filter_applied": action_filter,
            "audit_logs": response.data,
            "summary": {
                "actions_breakdown": action_summary,
                "fairness_alerts": fairness_alerts,
                "note": "Fairness alerts indicate bias detected requiring human review"
            },
            "explainchain_note": "Every action is permanently logged for regulatory compliance and transparency"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )


@router.get("/fairness-summary")
async def get_fairness_summary(
    user_id: str = Depends(get_current_user)
):
    """
    Get aggregated fairness monitoring summary for compliance reporting.
    
    This endpoint provides a high-level overview of fairness outcomes
    across all credit decisions, suitable for regulatory reporting
    and executive dashboards.
    
    **Compliance Purpose:**
    Demonstrates proactive bias monitoring and responsible AI governance.
    Shows commitment to fair lending practices and regulatory compliance.
    
    **Metrics Provided:**
    - Total fairness evaluations performed
    - Number of bias alerts triggered
    - Latest disparate impact ratios
    - Percentage of decisions flagged for human review
    
    **Returns:**
    Summary statistics including:
    - total_evaluations: Count of fairness checks performed
    - bias_alerts: Number of times bias was detected
    - human_reviews_recommended: Count of flagged decisions
    - latest_evaluation: Most recent fairness check results
    - compliance_status: Overall fairness health indicator
    
    **Example Response:**
    ```json
    {
      "fairness_summary": {
        "total_evaluations": 15,
        "bias_alerts": 3,
        "human_reviews_recommended": 3,
        "bias_alert_rate": 0.20,
        "latest_evaluation": {...},
        "compliance_status": "ALERT - Human review required"
      }
    }
    ```
    """
    try:
        # Fetch all fairness evaluation logs
        fairness_logs_response = supabase.table("audit_logs")\
            .select("*", count="exact")\
            .eq("action", "fairness_evaluation")\
            .order("created_at", desc=True)\
            .execute()
        
        total_evaluations = fairness_logs_response.count or 0
        bias_alerts = 0
        human_reviews_recommended = 0
        latest_evaluation = None
        
        # Analyze fairness logs
        for log in fairness_logs_response.data:
            metadata = log.get("metadata", {})
            
            if metadata.get("bias_detected"):
                bias_alerts += 1
            
            if metadata.get("human_review_recommended"):
                human_reviews_recommended += 1
            
            # Capture latest evaluation
            if latest_evaluation is None:
                latest_evaluation = {
                    "evaluation_timestamp": log.get("created_at"),
                    "sample_size": metadata.get("sample_size"),
                    "disparate_impact": metadata.get("disparate_impact"),
                    "bias_detected": metadata.get("bias_detected"),
                    "approval_rates": metadata.get("approval_rates")
                }
        
        # Calculate compliance metrics
        bias_alert_rate = (bias_alerts / total_evaluations) if total_evaluations > 0 else 0
        
        # Determine compliance status
        if bias_alerts == 0:
            compliance_status = "COMPLIANT - No bias detected"
        elif bias_alert_rate < 0.20:
            compliance_status = "MONITORING - Low bias rate detected"
        else:
            compliance_status = "ALERT - Human review required"
        
        return {
            "fairness_summary": {
                "total_evaluations": total_evaluations,
                "bias_alerts": bias_alerts,
                "human_reviews_recommended": human_reviews_recommended,
                "bias_alert_rate": round(bias_alert_rate, 2),
                "latest_evaluation": latest_evaluation,
                "compliance_status": compliance_status
            },
            "regulatory_note": "Disparate impact threshold: 0.80 (80% rule per EEOC guidelines)",
            "recommendation": "Regular monitoring ensures fair lending practices and regulatory compliance"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate fairness summary: {str(e)}"
        )

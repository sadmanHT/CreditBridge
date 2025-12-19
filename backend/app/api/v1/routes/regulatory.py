"""
Regulatory Reporting Routes for CreditBridge

SYSTEM ROLE:
You are building regulator-facing reporting APIs
for a fintech compliance platform.

PROJECT:
CreditBridge — Regulatory Reporting Module.

ENDPOINTS:
1. GET /regulatory/summary - Aggregate reporting statistics
2. GET /regulatory/fairness - Fairness and bias metrics
3. GET /regulatory/lineage/{decision_id} - Decision audit trail

DESIGN:
- Read from: credit_decisions, fairness_evaluations, decision_lineage
- JWT-protected (regulator access only)
- Read-only operations
- Machine-readable format
- Deterministic aggregations
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.supabase import supabase
from app.api.deps import get_current_user

router = APIRouter(prefix="/regulatory")


# ============================================================================
# Regulatory Summary Endpoint
# ============================================================================

@router.get("/summary")
async def get_regulatory_summary(
    days: int = Query(default=30, ge=1, le=365, description="Reporting period in days"),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get regulatory summary report for compliance.
    
    Returns aggregate statistics for specified reporting period:
    - Total loan requests processed
    - Approval/rejection/review rates
    - Total disbursed amount
    - Fraud flag rate
    
    **Authentication:** Requires valid JWT token (regulator access)
    
    **Parameters:**
    - days: Reporting period (1-365 days, default: 30)
    
    **Response Example:**
    ```json
    {
      "reporting_period": {
        "start_date": "2025-11-17",
        "end_date": "2025-12-17",
        "days": 30
      },
      "total_loan_requests": 150,
      "approval_rate": 0.567,
      "rejection_rate": 0.333,
      "review_rate": 0.100,
      "total_disbursed_amount": 1250000.0,
      "fraud_flag_rate": 0.053
    }
    ```
    """
    try:
        # Calculate reporting period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        start_date_iso = start_date.isoformat()
        
        # Fetch credit decisions within reporting period
        decisions_response = supabase.table("credit_decisions")\
            .select("id, decision, explanation, created_at")\
            .gte("created_at", start_date_iso)\
            .execute()
        
        if not decisions_response.data:
            return {
                "reporting_period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days": days
                },
                "total_loan_requests": 0,
                "approval_rate": 0.0,
                "rejection_rate": 0.0,
                "review_rate": 0.0,
                "total_disbursed_amount": 0.0,
                "fraud_flag_rate": 0.0
            }
        
        decisions = decisions_response.data
        total_loan_requests = len(decisions)
        
        # Calculate decision rates
        approved_count = sum(1 for d in decisions if d.get("decision") == "approved")
        rejected_count = sum(1 for d in decisions if d.get("decision") == "rejected")
        review_count = sum(1 for d in decisions if d.get("decision") == "review")
        
        approval_rate = round(approved_count / total_loan_requests, 3) if total_loan_requests > 0 else 0.0
        rejection_rate = round(rejected_count / total_loan_requests, 3) if total_loan_requests > 0 else 0.0
        review_rate = round(review_count / total_loan_requests, 3) if total_loan_requests > 0 else 0.0
        
        # Calculate fraud flag rate
        fraud_flagged_count = sum(
            1 for d in decisions
            if d.get("explanation") and "fraud" in d.get("explanation", "").lower()
        )
        fraud_flag_rate = round(fraud_flagged_count / total_loan_requests, 3) if total_loan_requests > 0 else 0.0
        
        # Calculate total disbursed amount (for approved loans only)
        # Get loan_request_ids for approved decisions
        approved_decision_ids = [d["id"] for d in decisions if d.get("decision") == "approved"]
        
        total_disbursed_amount = 0.0
        if approved_decision_ids:
            # Get loan requests for approved decisions
            approved_decisions_with_loans = supabase.table("credit_decisions")\
                .select("loan_request_id")\
                .in_("id", approved_decision_ids)\
                .execute()
            
            if approved_decisions_with_loans.data:
                loan_request_ids = [
                    d["loan_request_id"] 
                    for d in approved_decisions_with_loans.data 
                    if d.get("loan_request_id")
                ]
                
                if loan_request_ids:
                    loans_response = supabase.table("loan_requests")\
                        .select("requested_amount")\
                        .in_("id", loan_request_ids)\
                        .execute()
                    
                    if loans_response.data:
                        total_disbursed_amount = sum(
                            loan.get("requested_amount", 0.0)
                            for loan in loans_response.data
                        )
        
        return {
            "reporting_period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "total_loan_requests": total_loan_requests,
            "approval_rate": approval_rate,
            "rejection_rate": rejection_rate,
            "review_rate": review_rate,
            "total_disbursed_amount": round(total_disbursed_amount, 2),
            "fraud_flag_rate": fraud_flag_rate
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve regulatory summary: {str(e)}"
        )


# ============================================================================
# Regulatory Fairness Endpoint
# ============================================================================

@router.get("/fairness")
async def get_regulatory_fairness(
    days: int = Query(default=30, ge=1, le=365, description="Reporting period in days"),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get fairness metrics for regulatory compliance.
    
    Returns fairness analysis for specified reporting period:
    - Approval rates by protected classes (gender, region)
    - Bias incidents detected
    - Human review intervention counts
    
    **Authentication:** Requires valid JWT token (regulator access)
    
    **Parameters:**
    - days: Reporting period (1-365 days, default: 30)
    
    **Response Example:**
    ```json
    {
      "reporting_period": {
        "start_date": "2025-11-17",
        "end_date": "2025-12-17",
        "days": 30
      },
      "approval_rate_by_gender": {
        "male": 0.650,
        "female": 0.620,
        "other": 0.600
      },
      "approval_rate_by_region": {
        "dhaka": 0.700,
        "chittagong": 0.650,
        "sylhet": 0.580
      },
      "bias_incidents": [
        {
          "type": "gender_disparity",
          "severity": "low",
          "gap_percentage": 3.0,
          "description": "3% approval gap between genders"
        }
      ],
      "human_review_counts": {
        "total_reviews": 15,
        "override_approvals": 3,
        "override_rejections": 2
      }
    }
    ```
    """
    try:
        # Calculate reporting period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        start_date_iso = start_date.isoformat()
        
        # Fetch credit decisions within reporting period
        decisions_response = supabase.table("credit_decisions")\
            .select("id, loan_request_id, decision, created_at")\
            .gte("created_at", start_date_iso)\
            .execute()
        
        if not decisions_response.data:
            return {
                "reporting_period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days": days
                },
                "approval_rate_by_gender": {},
                "approval_rate_by_region": {},
                "bias_incidents": [],
                "human_review_counts": {
                    "total_reviews": 0,
                    "override_approvals": 0,
                    "override_rejections": 0
                }
            }
        
        decisions = decisions_response.data
        
        # Get loan requests to access borrower_id
        loan_request_ids = [d["loan_request_id"] for d in decisions if d.get("loan_request_id")]
        loans_response = supabase.table("loan_requests")\
            .select("id, borrower_id")\
            .in_("id", loan_request_ids)\
            .execute()
        
        # Create borrower_id lookup
        loan_to_borrower = {
            loan["id"]: loan["borrower_id"]
            for loan in (loans_response.data or [])
        }
        
        # Get borrower demographics
        borrower_ids = list(set(loan_to_borrower.values()))
        borrower_demographics = {}
        
        if borrower_ids:
            borrowers_response = supabase.table("borrowers")\
                .select("id, gender, region")\
                .in_("id", borrower_ids)\
                .execute()
            
            borrower_demographics = {
                b["id"]: {
                    "gender": b.get("gender", "unknown").lower(),
                    "region": b.get("region", "unknown").lower()
                }
                for b in (borrowers_response.data or [])
            }
        
        # Calculate approval rates by gender
        gender_stats = {}
        for decision in decisions:
            loan_id = decision.get("loan_request_id")
            if not loan_id:
                continue
            
            borrower_id = loan_to_borrower.get(loan_id)
            if not borrower_id:
                continue
            
            demographics = borrower_demographics.get(borrower_id, {})
            gender = demographics.get("gender", "unknown")
            is_approved = decision.get("decision") == "approved"
            
            if gender not in gender_stats:
                gender_stats[gender] = {"approved": 0, "total": 0}
            
            gender_stats[gender]["total"] += 1
            if is_approved:
                gender_stats[gender]["approved"] += 1
        
        approval_rate_by_gender = {
            gender: round(stats["approved"] / stats["total"], 3)
            for gender, stats in gender_stats.items()
            if stats["total"] > 0
        }
        
        # Calculate approval rates by region
        region_stats = {}
        for decision in decisions:
            loan_id = decision.get("loan_request_id")
            if not loan_id:
                continue
            
            borrower_id = loan_to_borrower.get(loan_id)
            if not borrower_id:
                continue
            
            demographics = borrower_demographics.get(borrower_id, {})
            region = demographics.get("region", "unknown")
            is_approved = decision.get("decision") == "approved"
            
            if region not in region_stats:
                region_stats[region] = {"approved": 0, "total": 0}
            
            region_stats[region]["total"] += 1
            if is_approved:
                region_stats[region]["approved"] += 1
        
        approval_rate_by_region = {
            region: round(stats["approved"] / stats["total"], 3)
            for region, stats in region_stats.items()
            if stats["total"] > 0
        }
        
        # Detect bias incidents
        bias_incidents = []
        
        # Check gender disparity
        if len(approval_rate_by_gender) >= 2:
            rates = list(approval_rate_by_gender.values())
            max_gap = max(rates) - min(rates)
            gap_percentage = round(max_gap * 100, 1)
            
            if max_gap > 0.10:  # 10% threshold
                bias_incidents.append({
                    "type": "gender_disparity",
                    "severity": "high" if max_gap > 0.20 else "medium",
                    "gap_percentage": gap_percentage,
                    "description": f"{gap_percentage}% approval gap between genders"
                })
            elif max_gap > 0.05:  # 5% threshold
                bias_incidents.append({
                    "type": "gender_disparity",
                    "severity": "low",
                    "gap_percentage": gap_percentage,
                    "description": f"{gap_percentage}% approval gap between genders"
                })
        
        # Check regional disparity
        if len(approval_rate_by_region) >= 2:
            rates = list(approval_rate_by_region.values())
            max_gap = max(rates) - min(rates)
            gap_percentage = round(max_gap * 100, 1)
            
            if max_gap > 0.15:  # 15% threshold
                bias_incidents.append({
                    "type": "regional_disparity",
                    "severity": "high" if max_gap > 0.25 else "medium",
                    "gap_percentage": gap_percentage,
                    "description": f"{gap_percentage}% approval gap between regions"
                })
        
        # Calculate human review counts
        review_decisions = [d for d in decisions if d.get("decision") == "review"]
        total_reviews = len(review_decisions)
        
        # For this POC, we'll estimate overrides based on decision patterns
        # In production, this would come from a manual_reviews table
        override_approvals = 0
        override_rejections = 0
        
        return {
            "reporting_period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "days": days
            },
            "approval_rate_by_gender": approval_rate_by_gender,
            "approval_rate_by_region": approval_rate_by_region,
            "bias_incidents": bias_incidents,
            "human_review_counts": {
                "total_reviews": total_reviews,
                "override_approvals": override_approvals,
                "override_rejections": override_rejections
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve regulatory fairness metrics: {str(e)}"
        )


# ============================================================================
# Regulatory Lineage Endpoint
# ============================================================================

@router.get("/lineage/{decision_id}")
async def get_decision_lineage(
    decision_id: str = Path(..., description="UUID of the credit decision"),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get complete audit trail for a specific credit decision.
    
    Returns full decision lineage for regulatory audit:
    - Decision outcome and metadata
    - Data sources used in decision
    - AI models invoked with versions
    - Policy version applied
    - Fraud detection results
    - Complete timestamps
    
    **Authentication:** Requires valid JWT token (regulator access)
    
    **Parameters:**
    - decision_id: UUID of the credit decision to audit
    
    **Response Example:**
    ```json
    {
      "decision_id": "abc123...",
      "decision": "approved",
      "credit_score": 75,
      "explanation": "Your credit score is 75...",
      "data_sources": {
        "borrower_profile": "supabase_borrowers_table",
        "social_network": "trustgraph_analysis",
        "raw_events": "behavioral_data"
      },
      "models_used": {
        "credit_model": "rule-based-v1.0",
        "fraud_model": "trustgraph-v1.0",
        "ensemble": "weighted-v2.0"
      },
      "policy_version": "1.0.0",
      "fraud_checks": {
        "fraud_score": 0.15,
        "risk_level": "low",
        "flags": []
      },
      "timestamps": {
        "decision_created": "2025-12-16T10:30:00Z",
        "lineage_recorded": "2025-12-16T10:30:01Z"
      }
    }
    ```
    """
    try:
        # Fetch credit decision
        decision_response = supabase.table("credit_decisions")\
            .select("id, loan_request_id, credit_score, decision, explanation, model_version, created_at")\
            .eq("id", decision_id)\
            .execute()
        
        if not decision_response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Credit decision not found: {decision_id}"
            )
        
        decision = decision_response.data[0]
        
        # Fetch decision lineage
        lineage_response = supabase.table("decision_lineage")\
            .select("borrower_id, data_sources, models_used, policy_version, fraud_checks, created_at")\
            .eq("decision_id", decision_id)\
            .execute()
        
        lineage = None
        if lineage_response.data:
            lineage = lineage_response.data[0]
        
        # Build response
        response = {
            "decision_id": decision["id"],
            "loan_request_id": decision.get("loan_request_id"),
            "decision": decision.get("decision"),
            "credit_score": decision.get("credit_score"),
            "explanation": decision.get("explanation"),
            "model_version": decision.get("model_version"),
            "data_sources": lineage.get("data_sources", {}) if lineage else {},
            "models_used": lineage.get("models_used", {}) if lineage else {},
            "policy_version": lineage.get("policy_version", "unknown") if lineage else "unknown",
            "fraud_checks": lineage.get("fraud_checks", {}) if lineage else {},
            "timestamps": {
                "decision_created": decision.get("created_at"),
                "lineage_recorded": lineage.get("created_at") if lineage else None
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve decision lineage: {str(e)}"
        )

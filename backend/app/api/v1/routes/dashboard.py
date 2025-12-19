"""
Dashboard API Routes for CreditBridge

SYSTEM ROLE:
You are implementing dashboard APIs
for microfinance officers and credit analysts.

PROJECT:
CreditBridge — Decision Dashboard Backend.

ENDPOINTS:
1. GET /dashboard/mfi/overview - Aggregate statistics
2. GET /dashboard/mfi/recent-decisions - Last 20 decisions
3. GET /dashboard/analyst/fairness - Fairness metrics
4. GET /dashboard/analyst/risk - Risk distributions

DESIGN:
- Read from: credit_decisions, fairness_evaluations, decision_lineage
- Efficient SQL aggregation via Supabase
- JWT-protected (read-only)
- No business logic, pure data retrieval
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.supabase import supabase
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard")


# ============================================================================
# MFI (Microfinance Officer) Dashboard Endpoints
# ============================================================================

@router.get("/mfi/overview")
async def get_mfi_overview(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get overview statistics for microfinance officers.
    
    Returns aggregate metrics:
    - Total loans processed
    - Approved/rejected/review counts
    - Average credit score
    - Flagged fraud count
    
    **Authentication:** Requires valid JWT token
    
    **Response Example:**
    ```json
    {
      "total_loans": 150,
      "approved_count": 85,
      "rejected_count": 50,
      "review_count": 15,
      "average_credit_score": 67.5,
      "flagged_fraud_count": 8
    }
    ```
    """
    try:
        # Fetch all credit decisions for aggregation
        response = supabase.table("credit_decisions")\
            .select("decision, credit_score, explanation")\
            .execute()
        
        if not response.data:
            # Return zeros if no data exists
            return {
                "total_loans": 0,
                "approved_count": 0,
                "rejected_count": 0,
                "review_count": 0,
                "average_credit_score": 0.0,
                "flagged_fraud_count": 0
            }
        
        decisions = response.data
        total_loans = len(decisions)
        
        # Count decisions by type
        approved_count = sum(1 for d in decisions if d.get("decision") == "approved")
        rejected_count = sum(1 for d in decisions if d.get("decision") == "rejected")
        review_count = sum(1 for d in decisions if d.get("decision") == "review")
        
        # Calculate average credit score
        credit_scores = [d.get("credit_score", 0) for d in decisions if d.get("credit_score") is not None]
        average_credit_score = round(sum(credit_scores) / len(credit_scores), 2) if credit_scores else 0.0
        
        # Count fraud flags (check if "fraud" keyword appears in explanation)
        flagged_fraud_count = sum(
            1 for d in decisions 
            if d.get("explanation") and "fraud" in d.get("explanation", "").lower()
        )
        
        return {
            "total_loans": total_loans,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "review_count": review_count,
            "average_credit_score": average_credit_score,
            "flagged_fraud_count": flagged_fraud_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve MFI overview: {str(e)}"
        )


@router.get("/mfi/recent-decisions")
async def get_recent_decisions(
    limit: int = Query(default=20, ge=1, le=100, description="Number of recent decisions to retrieve"),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get recent credit decisions for microfinance officers.
    
    Returns last N decisions with:
    - Decision outcome
    - Credit score
    - Fraud score (if available)
    - Timestamp
    
    **Authentication:** Requires valid JWT token
    
    **Parameters:**
    - limit: Number of decisions to return (1-100, default 20)
    
    **Response Example:**
    ```json
    {
      "count": 20,
      "decisions": [
        {
          "id": "uuid-123",
          "loan_request_id": "uuid-456",
          "decision": "approved",
          "credit_score": 75,
          "fraud_score": 0.15,
          "created_at": "2025-12-17T10:30:00Z"
        }
      ]
    }
    ```
    """
    try:
        # Fetch recent credit decisions with fraud data from decision_lineage
        decisions_response = supabase.table("credit_decisions")\
            .select("id, loan_request_id, decision, credit_score, created_at")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        
        if not decisions_response.data:
            return {
                "count": 0,
                "decisions": []
            }
        
        decisions = decisions_response.data
        
        # Enrich with fraud scores from decision_lineage
        decision_ids = [d["id"] for d in decisions]
        lineage_response = supabase.table("decision_lineage")\
            .select("decision_id, fraud_checks")\
            .in_("decision_id", decision_ids)\
            .execute()
        
        # Create fraud score lookup map
        fraud_scores = {}
        if lineage_response.data:
            for lineage in lineage_response.data:
                decision_id = lineage.get("decision_id")
                fraud_checks = lineage.get("fraud_checks", {})
                # Extract fraud score from fraud_checks
                fraud_score = fraud_checks.get("fraud_score", fraud_checks.get("score", 0.0))
                fraud_scores[decision_id] = fraud_score
        
        # Merge fraud scores into decisions
        enriched_decisions = []
        for decision in decisions:
            decision_id = decision["id"]
            enriched_decisions.append({
                "id": decision_id,
                "loan_request_id": decision.get("loan_request_id"),
                "decision": decision.get("decision"),
                "credit_score": decision.get("credit_score"),
                "fraud_score": fraud_scores.get(decision_id, 0.0),
                "created_at": decision.get("created_at")
            })
        
        return {
            "count": len(enriched_decisions),
            "decisions": enriched_decisions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent decisions: {str(e)}"
        )


# ============================================================================
# Analyst Dashboard Endpoints
# ============================================================================

@router.get("/analyst/fairness")
async def get_fairness_metrics(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get fairness metrics for credit analysts.
    
    Returns fairness analysis:
    - Approval rates by gender
    - Approval rates by region
    - Bias flags detected
    
    **Authentication:** Requires valid JWT token
    
    **Response Example:**
    ```json
    {
      "approval_rate_by_gender": {
        "male": 0.65,
        "female": 0.62,
        "other": 0.60
      },
      "approval_rate_by_region": {
        "dhaka": 0.70,
        "chittagong": 0.65,
        "sylhet": 0.58
      },
      "bias_flags": [
        {
          "type": "gender_disparity",
          "severity": "low",
          "description": "3% approval gap between genders"
        }
      ]
    }
    ```
    """
    try:
        # Fetch credit decisions with borrower demographics
        decisions_response = supabase.table("credit_decisions")\
            .select("id, loan_request_id, decision")\
            .execute()
        
        if not decisions_response.data:
            return {
                "approval_rate_by_gender": {},
                "approval_rate_by_region": {},
                "bias_flags": []
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
        if not borrower_ids:
            return {
                "approval_rate_by_gender": {},
                "approval_rate_by_region": {},
                "bias_flags": []
            }
        
        borrowers_response = supabase.table("borrowers")\
            .select("id, gender, region")\
            .in_("id", borrower_ids)\
            .execute()
        
        # Create borrower demographics lookup
        borrower_demographics = {
            b["id"]: {
                "gender": b.get("gender", "unknown"),
                "region": b.get("region", "unknown")
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
        
        # Detect bias flags
        bias_flags = []
        
        # Check gender disparity
        if len(approval_rate_by_gender) >= 2:
            rates = list(approval_rate_by_gender.values())
            max_gap = max(rates) - min(rates)
            if max_gap > 0.10:  # 10% threshold
                bias_flags.append({
                    "type": "gender_disparity",
                    "severity": "high" if max_gap > 0.20 else "medium",
                    "description": f"{int(max_gap * 100)}% approval gap between genders"
                })
            elif max_gap > 0.05:  # 5% threshold
                bias_flags.append({
                    "type": "gender_disparity",
                    "severity": "low",
                    "description": f"{int(max_gap * 100)}% approval gap between genders"
                })
        
        # Check regional disparity
        if len(approval_rate_by_region) >= 2:
            rates = list(approval_rate_by_region.values())
            max_gap = max(rates) - min(rates)
            if max_gap > 0.15:  # 15% threshold
                bias_flags.append({
                    "type": "regional_disparity",
                    "severity": "high" if max_gap > 0.25 else "medium",
                    "description": f"{int(max_gap * 100)}% approval gap between regions"
                })
        
        return {
            "approval_rate_by_gender": approval_rate_by_gender,
            "approval_rate_by_region": approval_rate_by_region,
            "bias_flags": bias_flags
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve fairness metrics: {str(e)}"
        )


@router.get("/analyst/risk")
async def get_risk_metrics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get risk distribution metrics for credit analysts.
    
    Returns risk analysis:
    - Credit score distribution (bucketed)
    - Fraud score distribution (bucketed)
    - Decision trends over time
    
    **Authentication:** Requires valid JWT token
    
    **Parameters:**
    - days: Number of days to analyze (1-365, default 30)
    
    **Response Example:**
    ```json
    {
      "credit_score_distribution": {
        "0-20": 5,
        "21-40": 12,
        "41-60": 28,
        "61-80": 35,
        "81-100": 20
      },
      "fraud_score_distribution": {
        "0.0-0.2": 85,
        "0.2-0.4": 10,
        "0.4-0.6": 3,
        "0.6-0.8": 1,
        "0.8-1.0": 1
      },
      "decision_trends_over_time": [
        {
          "date": "2025-12-10",
          "approved": 8,
          "rejected": 3,
          "review": 1
        }
      ]
    }
    ```
    """
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cutoff_iso = cutoff_date.isoformat()
        
        # Fetch credit decisions within time window
        decisions_response = supabase.table("credit_decisions")\
            .select("id, decision, credit_score, created_at")\
            .gte("created_at", cutoff_iso)\
            .execute()
        
        if not decisions_response.data:
            return {
                "credit_score_distribution": {},
                "fraud_score_distribution": {},
                "decision_trends_over_time": []
            }
        
        decisions = decisions_response.data
        
        # Build credit score distribution
        credit_buckets = {
            "0-20": 0,
            "21-40": 0,
            "41-60": 0,
            "61-80": 0,
            "81-100": 0
        }
        
        for decision in decisions:
            score = decision.get("credit_score", 0)
            if score <= 20:
                credit_buckets["0-20"] += 1
            elif score <= 40:
                credit_buckets["21-40"] += 1
            elif score <= 60:
                credit_buckets["41-60"] += 1
            elif score <= 80:
                credit_buckets["61-80"] += 1
            else:
                credit_buckets["81-100"] += 1
        
        # Fetch fraud scores from decision_lineage
        decision_ids = [d["id"] for d in decisions]
        lineage_response = supabase.table("decision_lineage")\
            .select("decision_id, fraud_checks")\
            .in_("decision_id", decision_ids)\
            .execute()
        
        # Build fraud score distribution
        fraud_buckets = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0
        }
        
        if lineage_response.data:
            for lineage in lineage_response.data:
                fraud_checks = lineage.get("fraud_checks", {})
                fraud_score = fraud_checks.get("fraud_score", fraud_checks.get("score", 0.0))
                
                if fraud_score < 0.2:
                    fraud_buckets["0.0-0.2"] += 1
                elif fraud_score < 0.4:
                    fraud_buckets["0.2-0.4"] += 1
                elif fraud_score < 0.6:
                    fraud_buckets["0.4-0.6"] += 1
                elif fraud_score < 0.8:
                    fraud_buckets["0.6-0.8"] += 1
                else:
                    fraud_buckets["0.8-1.0"] += 1
        
        # Build decision trends over time (daily aggregation)
        trends = {}
        for decision in decisions:
            created_at = decision.get("created_at")
            if not created_at:
                continue
            
            # Extract date (YYYY-MM-DD)
            date = created_at.split("T")[0]
            decision_type = decision.get("decision", "unknown")
            
            if date not in trends:
                trends[date] = {
                    "date": date,
                    "approved": 0,
                    "rejected": 0,
                    "review": 0
                }
            
            if decision_type == "approved":
                trends[date]["approved"] += 1
            elif decision_type == "rejected":
                trends[date]["rejected"] += 1
            elif decision_type == "review":
                trends[date]["review"] += 1
        
        # Sort trends by date
        decision_trends = sorted(trends.values(), key=lambda x: x["date"])
        
        return {
            "credit_score_distribution": credit_buckets,
            "fraud_score_distribution": fraud_buckets,
            "decision_trends_over_time": decision_trends
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve risk metrics: {str(e)}"
        )

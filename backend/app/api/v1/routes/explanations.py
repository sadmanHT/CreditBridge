"""
Borrower-Facing Explanation Routes for CreditBridge

These endpoints provide simple, human-readable explanations of credit decisions
for borrowers, promoting transparency and financial inclusion.

SYSTEM ROLE:
You are a fintech product engineer focused on user understanding and inclusion.

PROJECT:
CreditBridge — Explainable AI for Financial Inclusion.

PURPOSE:
Translate technical AI credit decisions into plain language that borrowers
can understand, regardless of their technical or financial literacy level.

DESIGN PHILOSOPHY:
- Simplicity: Avoid jargon, use everyday language
- Respect: Neutral tone, no judgment
- Inclusion: Support multiple languages for underserved communities
- Transparency: Clear explanations of why decisions were made

AUTHOR: CreditBridge User Experience Team
DATE: December 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.core.supabase import supabase
from app.api.v1.routes.borrowers import get_current_user
from app.ai.explainability import explain_ensemble_result, get_explainer_registry

router = APIRouter(prefix="/explanations")


@router.get("/loan/{loan_request_id}")
async def get_loan_explanation(
    loan_request_id: str,
    lang: str = Query(default="en", description="Language code: 'en' for English, 'bn' for Bangla"),
    user_id: str = Depends(get_current_user)
):
    """
    Get a simple, human-readable explanation of a credit decision.
    
    This endpoint takes a technical AI credit decision and translates it
    into plain language that any borrower can understand, regardless of
    their financial or technical literacy.
    
    **Financial Inclusion Focus:**
    Many borrowers in emerging markets have limited exposure to formal
    credit systems. This endpoint helps them understand:
    - Why they were approved or rejected
    - What factors influenced the decision
    - How trust networks affect their creditworthiness
    
    **Multilingual Support:**
    Supports English (en) and Bangla (bn) to serve Bangladesh's
    diverse population and promote financial literacy.
    
    **Parameters:**
    - loan_request_id: Unique identifier of the loan request
    - lang: Language code ('en' or 'bn')
    
    **Returns:**
    Plain-language explanation with:
    - summary: One-sentence overview
    - key_points: Bullet-point list of decision factors
    - language: Language code used
    - decision: approved or rejected
    - credit_score: Numeric score (simplified)
    
    **Security:**
    Borrowers can only access explanations for their own loan requests.
    
    **Example Response (English):**
    ```json
    {
      "summary": "Your loan was approved because you have a stable financial profile.",
      "key_points": [
        "You requested a manageable loan amount",
        "Your community trust network is strong",
        "No fraud indicators detected"
      ],
      "language": "en",
      "decision": "approved",
      "credit_score": 85
    }
    ```
    """
    try:
        # Step 1: Verify borrower owns this loan request
        borrower_response = supabase.table("borrowers")\
            .select("id")\
            .eq("user_id", user_id)\
            .execute()
        
        if not borrower_response.data:
            raise HTTPException(
                status_code=404,
                detail="Borrower profile not found"
            )
        
        borrower_id = borrower_response.data[0]["id"]
        
        # Step 2: Verify loan request belongs to this borrower
        loan_request_response = supabase.table("loan_requests")\
            .select("id, borrower_id, requested_amount, purpose")\
            .eq("id", loan_request_id)\
            .eq("borrower_id", borrower_id)\
            .execute()
        
        if not loan_request_response.data:
            raise HTTPException(
                status_code=404,
                detail="Loan request not found or access denied"
            )
        
        loan_request = loan_request_response.data[0]
        
        # Step 3: Fetch credit decision for this loan request
        credit_decision_response = supabase.table("credit_decisions")\
            .select("id, credit_score, decision, explanation, model_version, created_at")\
            .eq("loan_request_id", loan_request_id)\
            .execute()
        
        if not credit_decision_response.data:
            raise HTTPException(
                status_code=404,
                detail="Credit decision not found for this loan request"
            )
        
        credit_decision = credit_decision_response.data[0]
        
        # Step 4: Parse and simplify explanation
        raw_explanation = credit_decision.get("explanation", "")
        credit_score = credit_decision.get("credit_score", 0)
        decision = credit_decision.get("decision", "pending")
        
        # Step 5: Generate simple explanation based on language
        if lang == "bn":
            # Bangla version (static placeholders for hackathon)
            explanation_result = _generate_bangla_explanation(
                decision, credit_score, raw_explanation, loan_request
            )
        else:
            # English version (default)
            explanation_result = _generate_english_explanation(
                decision, credit_score, raw_explanation, loan_request
            )
        
        # Add metadata
        explanation_result["language"] = lang
        explanation_result["decision"] = decision
        explanation_result["credit_score"] = credit_score
        explanation_result["loan_amount"] = loan_request.get("requested_amount")
        explanation_result["loan_purpose"] = loan_request.get("purpose")
        
        return explanation_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )


def _generate_english_explanation(decision: str, credit_score: int, raw_explanation: str, loan_request: dict) -> dict:
    """
    Generate plain-English explanation for borrowers by parsing actual AI model features.
    
    Args:
        decision: approved or rejected
        credit_score: Numeric credit score (0-100)
        raw_explanation: Technical explanation from AI system
        loan_request: Loan request details
    
    Returns:
        Dictionary with summary and key_points
    """
    import re
    import json
    
    # Generate summary based on decision and score
    if decision == "approved":
        if credit_score >= 80:
            summary = f"Great news! Your loan was approved with a score of {credit_score}/100. You have a strong financial profile."
        elif credit_score >= 60:
            summary = f"Your loan was approved with a score of {credit_score}/100. Your financial profile meets our requirements."
        else:
            summary = f"Your loan was approved with a score of {credit_score}/100 based on your overall assessment."
    else:
        summary = f"We were unable to approve your loan at this time (score: {credit_score}/100). Please see the details below."
    
    # Parse actual AI features from raw_explanation
    key_points = []
    
    # Extract loan-specific details
    requested_amount = loan_request.get("requested_amount", 0)
    loan_purpose = loan_request.get("purpose", "general")
    
    # Parse feature importance from raw_explanation
    # Look for patterns like "feature_name: value" or "feature_name = value"
    
    # 1. Loan Amount Analysis
    if requested_amount:
        if requested_amount <= 5000:
            key_points.append(f"✓ Small loan amount (৳{requested_amount:,.0f}) reduces risk")
        elif requested_amount <= 15000:
            key_points.append(f"✓ Moderate loan amount (৳{requested_amount:,.0f}) is manageable")
        elif requested_amount <= 30000:
            key_points.append(f"• Loan amount (৳{requested_amount:,.0f}) requires good credit history")
        else:
            key_points.append(f"⚠ Large loan amount (৳{requested_amount:,.0f}) increases scrutiny")
    
    # 2. TrustGraph Score Analysis (parse from raw_explanation)
    trust_score_match = re.search(r'trust_score[:\s=]+([0-9.]+)', raw_explanation)
    if trust_score_match:
        trust_score = float(trust_score_match.group(1))
        if trust_score >= 0.9:
            key_points.append(f"✓ Excellent community trust network (score: {trust_score:.2f})")
        elif trust_score >= 0.7:
            key_points.append(f"✓ Good community connections (score: {trust_score:.2f})")
        elif trust_score >= 0.5:
            key_points.append(f"• Average community trust (score: {trust_score:.2f})")
        else:
            key_points.append(f"⚠ Limited community trust network (score: {trust_score:.2f})")
    elif "TrustGraph" in raw_explanation:
        # Fallback TrustGraph analysis
        if "[+]" in raw_explanation:
            key_points.append("✓ Positive community network connections detected")
        if "[-]" in raw_explanation or "[!!!]" in raw_explanation:
            key_points.append("⚠ Some concerns in your social network")
    
    # 3. Fraud Detection Results
    if "fraud" in raw_explanation.lower():
        if "no fraud" in raw_explanation.lower() or "[OK]" in raw_explanation:
            key_points.append("✓ No fraud indicators detected in your profile")
        elif "fraud ring" in raw_explanation.lower() or "[!!!]" in raw_explanation:
            key_points.append("⚠ Unusual patterns detected requiring further verification")
        else:
            key_points.append("• Standard fraud checks completed")
    
    # 4. Parse actual feature scores from ensemble explanation
    # Look for patterns like "monthly_income: 25000" or "employment_years: 3"
    income_match = re.search(r'(?:monthly_income|income)[:\s=]+([0-9]+)', raw_explanation)
    if income_match:
        income = int(income_match.group(1))
        if income >= 30000:
            key_points.append(f"✓ Strong income level (৳{income:,.0f}/month)")
        elif income >= 15000:
            key_points.append(f"✓ Stable income (৳{income:,.0f}/month)")
        else:
            key_points.append(f"• Income level (৳{income:,.0f}/month) noted")
    
    employment_match = re.search(r'(?:employment_years|job_years)[:\s=]+([0-9]+)', raw_explanation)
    if employment_match:
        years = int(employment_match.group(1))
        if years >= 5:
            key_points.append(f"✓ Long employment history ({years} years)")
        elif years >= 2:
            key_points.append(f"✓ Stable employment ({years} years)")
        else:
            key_points.append(f"• Recent employment ({years} year{'s' if years != 1 else ''})")
    
    # 5. Credit History Indicators
    if "credit_history" in raw_explanation.lower() or "payment_history" in raw_explanation.lower():
        if "good" in raw_explanation.lower() or "excellent" in raw_explanation.lower():
            key_points.append("✓ Good payment history on previous obligations")
        elif "poor" in raw_explanation.lower() or "late" in raw_explanation.lower():
            key_points.append("⚠ Some late payments in credit history")
        else:
            key_points.append("• Credit history reviewed")
    
    # 6. Debt-to-Income Ratio
    dti_match = re.search(r'(?:debt_to_income|dti)[:\s=]+([0-9.]+)', raw_explanation)
    if dti_match:
        dti = float(dti_match.group(1))
        if dti <= 0.3:
            key_points.append(f"✓ Low debt burden ({dti*100:.0f}% of income)")
        elif dti <= 0.5:
            key_points.append(f"• Moderate debt level ({dti*100:.0f}% of income)")
        else:
            key_points.append(f"⚠ High existing debt ({dti*100:.0f}% of income)")
    
    # 7. Loan Purpose Impact
    if loan_purpose:
        purpose_lower = loan_purpose.lower()
        if any(p in purpose_lower for p in ['business', 'education', 'medical', 'emergency']):
            key_points.append(f"✓ Loan purpose ({loan_purpose}) considered productive")
        elif 'personal' in purpose_lower or 'consumer' in purpose_lower:
            key_points.append(f"• Loan purpose: {loan_purpose}")
    
    # 8. Model Confidence
    confidence_match = re.search(r'confidence[:\s=]+([0-9.]+)', raw_explanation)
    if confidence_match:
        confidence = float(confidence_match.group(1))
        if confidence >= 0.8:
            key_points.append(f"✓ High model confidence ({confidence*100:.0f}%)")
        elif confidence >= 0.6:
            key_points.append(f"• Moderate model confidence ({confidence*100:.0f}%)")
    
    # Ensure we have at least 3 key points
    if len(key_points) < 3:
        # Add generic credit score feedback
        if credit_score >= 80:
            key_points.append("✓ Your overall credit score is excellent")
        elif credit_score >= 60:
            key_points.append("✓ Your credit score meets our minimum standards")
        elif credit_score >= 40:
            key_points.append("• Your credit score is in the moderate range")
        else:
            key_points.append("• Your credit score needs improvement")
    
    # Add decision-specific guidance
    if decision == "approved":
        key_points.append("✓ All requirements met for loan approval")
    else:
        key_points.append("• Consider improving the above factors and reapplying")
    
    return {
        "summary": summary,
        "key_points": key_points[:8],  # Limit to 8 most relevant points
        "helpful_tip": _get_helpful_tip(decision, credit_score)
    }


def _generate_bangla_explanation(decision: str, credit_score: int, raw_explanation: str, loan_request: dict) -> dict:
    """
    Generate Bangla explanation for borrowers.
    
    Note: For hackathon purposes, this uses static Bangla text.
    Production systems would use proper translation services.
    
    Args:
        decision: approved or rejected
        credit_score: Numeric credit score (0-100)
        raw_explanation: Technical explanation from AI system
        loan_request: Loan request details
    
    Returns:
        Dictionary with summary and key_points in Bangla
    """
    
    # Generate summary in Bangla
    if decision == "approved":
        if credit_score >= 80:
            summary = "সুসংবাদ! আপনার ঋণ অনুমোদিত হয়েছে কারণ আপনার আর্থিক প্রোফাইল খুব ভাল।"
        elif credit_score >= 60:
            summary = "আপনার ঋণ অনুমোদিত হয়েছে। আপনার আর্থিক প্রোফাইল আমাদের প্রয়োজন পূরণ করে।"
        else:
            summary = "আপনার সামগ্রিক মূল্যায়নের ভিত্তিতে আপনার ঋণ অনুমোদিত হয়েছে।"
    else:
        summary = "এই মুহূর্তে আমরা আপনার ঋণ অনুমোদন করতে পারিনি। বিস্তারিত দেখুন।"
    
    # Key points in Bangla
    key_points = []
    
    requested_amount = loan_request.get("requested_amount", 0)
    if requested_amount <= 10000:
        key_points.append("✓ আপনি একটি ছোট, পরিচালনাযোগ্য ঋণের পরিমাণ অনুরোধ করেছেন")
    elif requested_amount <= 30000:
        key_points.append("✓ আপনার ঋণের পরিমাণ যুক্তিসঙ্গত সীমার মধ্যে")
    
    # Check for TrustGraph
    if "TrustGraph" in raw_explanation or "trust_score" in raw_explanation:
        if "1.000" in raw_explanation or "[+]" in raw_explanation:
            key_points.append("✓ আপনার সামাজিক নেটওয়ার্ক বিশ্বস্ত")
        elif "[-]" in raw_explanation or "[!!!]" in raw_explanation:
            key_points.append("⚠ আপনার সামাজিক নেটওয়ার্কে কিছু সমস্যা পাওয়া গেছে")
    
    # Check fraud indicators
    if "[OK] Fraud ring check" in raw_explanation:
        key_points.append("✓ কোন প্রতারণা সূচক পাওয়া যায়নি")
    
    # Credit score level
    if credit_score >= 80:
        key_points.append("✓ আপনার ক্রেডিট স্কোর চমৎকার")
    elif credit_score >= 60:
        key_points.append("✓ আপনার ক্রেডিট স্কোর আমাদের মান পূরণ করে")
    
    # Decision-specific
    if decision == "approved":
        key_points.append("✓ ঋণ অনুমোদনের জন্য সমস্ত প্রয়োজন পূরণ হয়েছে")
    else:
        key_points.append("• অতিরিক্ত ডকুমেন্টেশন বা সময় সাহায্য করতে পারে")
    
    return {
        "summary": summary,
        "key_points": key_points,
        "helpful_tip": "আরও তথ্যের জন্য আমাদের সাথে যোগাযোগ করুন।" if decision == "rejected" else "ঋণ গ্রহণের জন্য ধন্যবাদ!"
    }


def _get_helpful_tip(decision: str, credit_score: int) -> str:
    """
    Provide helpful tips based on decision and score.
    
    Args:
        decision: approved or rejected
        credit_score: Credit score
    
    Returns:
        Helpful tip string
    """
    if decision == "approved":
        return "Please ensure timely repayment to maintain your good credit standing."
    else:
        if credit_score < 40:
            return "Building stronger relationships in your community may improve your future applications."
        elif credit_score < 60:
            return "Consider applying for a smaller loan amount or providing additional documentation."
        else:
            return "Please contact us to discuss alternative options or reapply in the future."


@router.get("/technical/{loan_request_id}")
async def get_technical_explanation(
    loan_request_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get detailed technical explanation with AI model insights.
    
    This endpoint provides comprehensive explainability data including:
    - Individual model explanations (credit scoring, trust graph, fraud detection)
    - Decision factors with impact analysis
    - Confidence scores and model methods
    - Overall ensemble summary
    
    **Use Cases:**
    - Loan officers reviewing credit decisions
    - Compliance and audit trails
    - Data analysts studying model performance
    - Developers debugging AI behavior
    
    **Parameters:**
    - loan_request_id: Unique identifier of the loan request
    
    **Returns:**
    Comprehensive explanation with:
    - overall_summary: High-level decision summary
    - confidence: Average confidence across models (0-1)
    - model_explanations: Detailed breakdown per model
    - prediction: Final scores and recommendations
    
    **Security:**
    Only authorized loan officers or borrowers can access explanations.
    
    **Example Response:**
    ```json
    {
      "overall_summary": "Final Credit Score: 65.00/100 | 4 positive, 1 negative factors",
      "confidence": 0.85,
      "prediction": {
        "final_score": 65.00,
        "fraud_flag": false,
        "recommendation": "approve"
      },
      "model_explanations": {
        "RuleBasedCreditModel-v1.0": {
          "summary": "Credit Score: 70/100 (Risk: MEDIUM) - 3 positive factor(s)",
          "confidence": 0.95,
          "method": "rule_based",
          "factors": [
            {
              "factor": "Loan Amount (Small)",
              "impact": "+20",
              "explanation": "Requesting $5,000 (low risk)",
              "value": 5000
            }
          ]
        },
        "TrustGraphModel-v1.0-POC": {
          "summary": "Trust Score: 0.75/1.00 (NORMAL) - 2 positive signals",
          "confidence": 0.75,
          "method": "trust_graph",
          "factors": [
            {
              "factor": "Network Size",
              "impact": "positive",
              "explanation": "5 peer connection(s) analyzed",
              "weight": 0.32
            }
          ]
        }
      }
    }
    ```
    """
    try:
        # Step 1: Verify borrower owns this loan request
        borrower_response = supabase.table("borrowers")\
            .select("id")\
            .eq("user_id", user_id)\
            .execute()
        
        if not borrower_response.data:
            raise HTTPException(
                status_code=404,
                detail="Borrower profile not found"
            )
        
        borrower_id = borrower_response.data[0]["id"]
        
        # Step 2: Get loan request
        loan_request_response = supabase.table("loan_requests")\
            .select("*")\
            .eq("id", loan_request_id)\
            .eq("borrower_id", borrower_id)\
            .execute()
        
        if not loan_request_response.data:
            raise HTTPException(
                status_code=404,
                detail="Loan request not found or access denied"
            )
        
        loan_request = loan_request_response.data[0]
        
        # Step 3: Get credit decision with model outputs
        credit_decision_response = supabase.table("credit_decisions")\
            .select("*")\
            .eq("loan_request_id", loan_request_id)\
            .execute()
        
        if not credit_decision_response.data:
            raise HTTPException(
                status_code=404,
                detail="Credit decision not found for this loan request"
            )
        
        credit_decision = credit_decision_response.data[0]
        
        # Step 4: Parse model outputs from stored decision
        # Note: In production, you'd re-run the ensemble here
        # For now, we'll generate explanations from stored data
        
        model_outputs = credit_decision.get("model_outputs", {})
        final_score = credit_decision.get("credit_score", 0)
        fraud_flag = credit_decision.get("fraud_flag", False)
        
        # If model_outputs is empty, create mock structure for explanation
        if not model_outputs:
            # Use stored explanation as fallback
            return {
                "overall_summary": f"Credit Score: {final_score}/100",
                "confidence": 0.80,
                "prediction": {
                    "final_score": final_score,
                    "fraud_flag": fraud_flag,
                    "recommendation": "approve" if final_score >= 60 and not fraud_flag else "review"
                },
                "explanation": credit_decision.get("explanation", "No detailed explanation available"),
                "note": "Detailed model explanations not available for this decision (legacy format)"
            }
        
        # Step 5: Generate comprehensive explanations using explainability system
        # Reconstruct input data for explainers
        input_data = {
            "borrower": {
                "id": borrower_id,
                "region": loan_request.get("region", "Unknown")
                # Add more borrower data as needed
            },
            "loan": {
                "requested_amount": loan_request.get("requested_amount", 0),
                "purpose": loan_request.get("purpose", "")
            }
        }
        
        # Create ensemble-style result structure
        ensemble_result = {
            "final_credit_score": final_score,
            "fraud_flag": fraud_flag,
            "model_outputs": model_outputs
        }
        
        # Generate comprehensive explanations
        explanation = explain_ensemble_result(input_data, ensemble_result)
        
        return {
            "overall_summary": explanation['overall_summary'],
            "confidence": explanation['confidence'],
            "prediction": {
                "final_score": explanation['final_score'],
                "fraud_flag": explanation['fraud_flag'],
                "recommendation": "approve" if explanation['final_score'] >= 60 and not explanation['fraud_flag'] else "review"
            },
            "model_explanations": explanation['model_explanations'],
            "metadata": {
                "loan_request_id": loan_request_id,
                "borrower_id": borrower_id,
                "decision_date": credit_decision.get("created_at"),
                "model_version": credit_decision.get("model_version"),
                **explanation.get('metadata', {})
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate technical explanation: {str(e)}"
        )

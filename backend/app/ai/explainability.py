"""
AI Explainability Module for CreditBridge

This module generates human-readable explanations for credit decisions.
Provides transparency and regulatory compliance for AI-driven lending.

Current Implementation:
- Rule-based explanation generation
- Natural language summaries
- Borrower-friendly language (no jargon)
- Future: SHAP values integration

Design constraints:
- Deterministic and reproducible
- Neutral and non-discriminatory language
- Compliance-ready output format
- Free tier only (no paid services)
"""

from typing import Dict, List, Any


def build_explanation(score_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert raw credit scoring output into human-readable explanations.
    
    This function transforms technical scoring factors into natural language
    that can be understood by borrowers, MFI officers, and compliance auditors.
    
    Args:
        score_result (dict): Output from compute_credit_score() containing:
            - credit_score (int): Score from 0-100
            - risk_level (str): "low", "medium", or "high"
            - factors (list): List of scoring factors with impact
    
    Returns:
        dict: Human-readable explanation containing:
            - summary (str): Short natural language summary
            - details (list): List of explanation points
            - borrower_message (str): Friendly message for borrower
            - recommendation (str): Action recommendation
    
    Example:
        >>> score_result = {
        ...     "credit_score": 65,
        ...     "risk_level": "medium",
        ...     "factors": [
        ...         {"factor": "Base credit score", "impact": 50},
        ...         {"factor": "Small loan amount", "impact": 15}
        ...     ]
        ... }
        >>> explanation = build_explanation(score_result)
        >>> print(explanation["summary"])
        Your credit score is 65, indicating medium risk level.
    """
    credit_score = score_result.get("credit_score", 0)
    risk_level = score_result.get("risk_level", "unknown")
    factors = score_result.get("factors", [])
    
    # Build natural language summary
    summary = f"Your credit score is {credit_score}, indicating {risk_level} risk level."
    
    # Build detailed explanation list
    details = []
    
    for factor in factors:
        factor_name = factor.get("factor", "Unknown factor")
        impact = factor.get("impact", 0)
        explanation = factor.get("explanation", "")
        
        # Skip base score from details (already in summary)
        if "base" in factor_name.lower():
            continue
        
        # Format impact with sign
        impact_sign = "+" if impact >= 0 else ""
        impact_str = f"{impact_sign}{impact}"
        
        # Create human-readable detail
        if impact > 0:
            detail = f"✓ {explanation} ({impact_str} points)"
        elif impact < 0:
            detail = f"⚠ {explanation} ({impact_str} points)"
        else:
            detail = f"• {explanation} (neutral)"
        
        details.append(detail)
    
    # Generate borrower-friendly message based on risk level
    if risk_level == "low":
        borrower_message = (
            "Great news! Your loan application shows low risk. "
            "You have a strong chance of approval."
        )
        recommendation = "Proceed with approval process"
        
    elif risk_level == "medium":
        borrower_message = (
            "Your loan application shows moderate risk. "
            "Our team will review your application carefully. "
            "You may be asked to provide additional information."
        )
        recommendation = "Manual review recommended"
        
    else:  # high risk
        borrower_message = (
            "Your loan application shows higher risk at this time. "
            "We recommend starting with a smaller loan amount to build your credit history. "
            "You can reapply after 3-6 months."
        )
        recommendation = "Consider smaller loan amount or reapply later"
    
    # Compile final explanation
    return {
        "summary": summary,
        "details": details,
        "borrower_message": borrower_message,
        "recommendation": recommendation,
        "credit_score": credit_score,
        "risk_level": risk_level
    }


def format_for_audit(score_result: Dict[str, Any], explanation: Dict[str, Any]) -> str:
    """
    Format credit decision for audit log in a structured way.
    
    This creates a compliance-ready text format that can be stored in
    audit logs and reviewed by regulators or compliance officers.
    
    Args:
        score_result (dict): Original scoring output
        explanation (dict): Human-readable explanation from build_explanation()
    
    Returns:
        str: Formatted audit-ready text
    
    Example:
        >>> audit_text = format_for_audit(score_result, explanation)
        >>> print(audit_text)
        CREDIT DECISION AUDIT LOG
        -------------------------
        Credit Score: 65
        Risk Level: medium
        Model Version: rule-based-v1.0
        ...
    """
    lines = [
        "CREDIT DECISION AUDIT LOG",
        "=" * 50,
        f"Credit Score: {score_result.get('credit_score', 'N/A')}",
        f"Risk Level: {score_result.get('risk_level', 'N/A')}",
        f"Model Version: {score_result.get('model_version', 'N/A')}",
        "",
        "SCORING FACTORS:",
        "-" * 50
    ]
    
    for factor in score_result.get("factors", []):
        factor_name = factor.get("factor", "Unknown")
        impact = factor.get("impact", 0)
        explanation_text = factor.get("explanation", "")
        
        lines.append(f"• {factor_name}: {impact:+d} points")
        lines.append(f"  Reason: {explanation_text}")
        lines.append("")
    
    lines.extend([
        "RECOMMENDATION:",
        "-" * 50,
        explanation.get("recommendation", "N/A"),
        "",
        "BORROWER MESSAGE:",
        "-" * 50,
        explanation.get("borrower_message", "N/A")
    ])
    
    return "\n".join(lines)


def format_for_mfi_officer(explanation: Dict[str, Any]) -> str:
    """
    Format explanation for MFI (Microfinance Institution) loan officers.
    
    Provides a concise summary suitable for quick decision-making by
    loan officers during borrower consultations.
    
    Args:
        explanation (dict): Human-readable explanation from build_explanation()
    
    Returns:
        str: Formatted text for MFI officers
    """
    score = explanation.get("credit_score", "N/A")
    risk = explanation.get("risk_level", "N/A")
    recommendation = explanation.get("recommendation", "N/A")
    
    lines = [
        f"📊 Credit Score: {score}/100",
        f"⚠️  Risk Level: {risk.upper()}",
        f"💡 Recommendation: {recommendation}",
        "",
        "Key Factors:"
    ]
    
    for detail in explanation.get("details", []):
        lines.append(f"  {detail}")
    
    return "\n".join(lines)


# Future: SHAP Integration
# TODO: Integrate SHAP values for ML model explanations
# TODO: Generate feature importance plots
# TODO: Add counterfactual explanations ("What if...")
# TODO: Multi-language support (Bengali, English)

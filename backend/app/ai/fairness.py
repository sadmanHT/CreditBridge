"""
Fairness and Bias Monitoring Module

This module provides utilities to evaluate fairness in credit decision systems
by analyzing approval rates across protected demographic groups.

SYSTEM ROLE:
You are an AI ethics engineer designing a fairness monitoring module
for a fintech credit decision system.

PROJECT:
CreditBridge — Responsible AI credit scoring platform.

PURPOSE:
Implement a lightweight fairness and bias monitoring utility
that evaluates whether credit decisions are disproportionately
affecting protected or sensitive groups.

AUTHOR: CreditBridge AI Team
DATE: December 2025
"""

from typing import List, Dict, Any


def evaluate_fairness(decisions: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Evaluate fairness in credit decisions by analyzing approval rates
    across gender and regional demographics.
    
    Args:
        decisions: List of decision records, each containing:
            - gender: "male" | "female" | "other"
            - region: Region name (e.g., "Dhaka", "Chattogram")
            - decision: "approved" | "rejected"
    
    Returns:
        Dictionary containing:
            - approval_rates: Breakdown by gender and region
            - disparate_impact: Female/male approval rate ratio
            - bias_detected: True if disparate impact < 0.80
            - notes: Human-readable fairness summary
    
    Fairness Metrics:
        - Disparate Impact Ratio: Measures whether one group's approval rate
          is substantially lower than another's. The 0.80 threshold (80% rule)
          is a common regulatory standard.
        - If female approval rate < 80% of male approval rate → bias detected
    
    Example:
        decisions = [
            {"gender": "male", "region": "Dhaka", "decision": "approved"},
            {"gender": "female", "region": "Dhaka", "decision": "rejected"}
        ]
        result = evaluate_fairness(decisions)
    """
    
    # Edge case: Empty decision list
    if not decisions:
        return {
            "approval_rates": {"gender": {}, "region": {}},
            "disparate_impact": None,
            "bias_detected": False,
            "notes": "No decisions to evaluate. Fairness analysis requires data."
        }
    
    # Initialize counters for gender-based analysis
    gender_totals = {}  # Total decisions per gender
    gender_approved = {}  # Approved decisions per gender
    
    # Initialize counters for region-based analysis
    region_totals = {}  # Total decisions per region
    region_approved = {}  # Approved decisions per region
    
    # Process each decision
    for decision_record in decisions:
        gender = decision_record.get("gender", "unknown")
        region = decision_record.get("region", "unknown")
        decision = decision_record.get("decision", "unknown")
        
        # Count by gender
        gender_totals[gender] = gender_totals.get(gender, 0) + 1
        if decision == "approved":
            gender_approved[gender] = gender_approved.get(gender, 0) + 1
        
        # Count by region
        region_totals[region] = region_totals.get(region, 0) + 1
        if decision == "approved":
            region_approved[region] = region_approved.get(region, 0) + 1
    
    # Calculate approval rates by gender
    gender_approval_rates = {}
    for gender in gender_totals:
        approved_count = gender_approved.get(gender, 0)
        total_count = gender_totals[gender]
        approval_rate = approved_count / total_count if total_count > 0 else 0.0
        gender_approval_rates[gender] = {
            "approved": approved_count,
            "total": total_count,
            "rate": round(approval_rate, 4)
        }
    
    # Calculate approval rates by region
    region_approval_rates = {}
    for region in region_totals:
        approved_count = region_approved.get(region, 0)
        total_count = region_totals[region]
        approval_rate = approved_count / total_count if total_count > 0 else 0.0
        region_approval_rates[region] = {
            "approved": approved_count,
            "total": total_count,
            "rate": round(approval_rate, 4)
        }
    
    # Calculate disparate impact ratio (female / male)
    # This measures whether female applicants are approved at a similar rate to male applicants
    disparate_impact = None
    bias_detected = False
    
    male_rate = gender_approval_rates.get("male", {}).get("rate", 0.0)
    female_rate = gender_approval_rates.get("female", {}).get("rate", 0.0)
    
    if male_rate > 0:
        # Disparate impact = (female approval rate) / (male approval rate)
        disparate_impact = female_rate / male_rate
        
        # 80% rule: If female rate is less than 80% of male rate, bias is detected
        if disparate_impact < 0.80:
            bias_detected = True
    
    # Generate human-readable notes
    notes = _generate_fairness_notes(
        gender_approval_rates,
        region_approval_rates,
        disparate_impact,
        bias_detected
    )
    
    # Return fairness evaluation result
    return {
        "approval_rates": {
            "gender": gender_approval_rates,
            "region": region_approval_rates
        },
        "disparate_impact": round(disparate_impact, 4) if disparate_impact is not None else None,
        "bias_detected": bias_detected,
        "notes": notes
    }


def _generate_fairness_notes(
    gender_rates: Dict[str, Dict[str, Any]],
    region_rates: Dict[str, Dict[str, Any]],
    disparate_impact: float,
    bias_detected: bool
) -> str:
    """
    Generate human-readable fairness analysis notes.
    
    Args:
        gender_rates: Approval rates by gender
        region_rates: Approval rates by region
        disparate_impact: Disparate impact ratio (female/male)
        bias_detected: Whether bias was detected
    
    Returns:
        Human-readable summary string
    """
    
    notes_parts = []
    
    # Gender fairness summary
    notes_parts.append("=== GENDER FAIRNESS ANALYSIS ===")
    for gender, stats in gender_rates.items():
        rate_pct = stats["rate"] * 100
        notes_parts.append(
            f"  {gender.capitalize()}: {stats['approved']}/{stats['total']} approved ({rate_pct:.1f}%)"
        )
    
    # Disparate impact analysis
    if disparate_impact is not None:
        notes_parts.append(f"\n  Disparate Impact Ratio: {disparate_impact:.4f}")
        if bias_detected:
            notes_parts.append(
                "  [!!!] BIAS DETECTED: Female approval rate is less than 80% of male approval rate."
            )
            notes_parts.append(
                "  Recommendation: Review decision criteria to ensure gender-neutral scoring."
            )
        else:
            notes_parts.append(
                "  [OK] No significant gender bias detected (ratio >= 0.80)."
            )
    else:
        notes_parts.append("\n  Disparate Impact: Unable to calculate (insufficient male data)")
    
    # Regional fairness summary
    notes_parts.append("\n=== REGIONAL FAIRNESS ANALYSIS ===")
    for region, stats in region_rates.items():
        rate_pct = stats["rate"] * 100
        notes_parts.append(
            f"  {region}: {stats['approved']}/{stats['total']} approved ({rate_pct:.1f}%)"
        )
    
    # Check for regional disparities
    if region_rates:
        rates = [stats["rate"] for stats in region_rates.values()]
        max_rate = max(rates)
        min_rate = min(rates)
        if max_rate > 0 and (min_rate / max_rate) < 0.80:
            notes_parts.append(
                "\n  [!] Regional disparity detected: Some regions have significantly lower approval rates."
            )
        else:
            notes_parts.append(
                "\n  [OK] No significant regional disparities detected."
            )
    
    return "\n".join(notes_parts)


# Example usage and testing
if __name__ == "__main__":
    # Test Case 1: Balanced fairness
    print("TEST CASE 1: Balanced Gender Distribution")
    print("=" * 60)
    balanced_decisions = [
        {"gender": "male", "region": "Dhaka", "decision": "approved"},
        {"gender": "male", "region": "Dhaka", "decision": "approved"},
        {"gender": "female", "region": "Dhaka", "decision": "approved"},
        {"gender": "female", "region": "Dhaka", "decision": "approved"},
        {"gender": "male", "region": "Chattogram", "decision": "rejected"},
        {"gender": "female", "region": "Chattogram", "decision": "rejected"}
    ]
    result1 = evaluate_fairness(balanced_decisions)
    print(f"Disparate Impact: {result1['disparate_impact']}")
    print(f"Bias Detected: {result1['bias_detected']}")
    print(result1['notes'])
    
    # Test Case 2: Bias detected
    print("\n\nTEST CASE 2: Gender Bias (Female Disadvantaged)")
    print("=" * 60)
    biased_decisions = [
        {"gender": "male", "region": "Dhaka", "decision": "approved"},
        {"gender": "male", "region": "Dhaka", "decision": "approved"},
        {"gender": "male", "region": "Dhaka", "decision": "approved"},
        {"gender": "male", "region": "Dhaka", "decision": "approved"},
        {"gender": "female", "region": "Dhaka", "decision": "approved"},
        {"gender": "female", "region": "Dhaka", "decision": "rejected"},
        {"gender": "female", "region": "Dhaka", "decision": "rejected"},
        {"gender": "female", "region": "Dhaka", "decision": "rejected"}
    ]
    result2 = evaluate_fairness(biased_decisions)
    print(f"Disparate Impact: {result2['disparate_impact']}")
    print(f"Bias Detected: {result2['bias_detected']}")
    print(result2['notes'])
    
    # Test Case 3: Regional disparity
    print("\n\nTEST CASE 3: Regional Disparity")
    print("=" * 60)
    regional_decisions = [
        {"gender": "male", "region": "Dhaka", "decision": "approved"},
        {"gender": "male", "region": "Dhaka", "decision": "approved"},
        {"gender": "female", "region": "Dhaka", "decision": "approved"},
        {"gender": "male", "region": "Sylhet", "decision": "rejected"},
        {"gender": "male", "region": "Sylhet", "decision": "rejected"},
        {"gender": "female", "region": "Sylhet", "decision": "rejected"}
    ]
    result3 = evaluate_fairness(regional_decisions)
    print(f"Bias Detected: {result3['bias_detected']}")
    print(result3['notes'])

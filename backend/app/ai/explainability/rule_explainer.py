"""
Rule-Based Model Explainer
Generates human-readable explanations for rule-based credit scoring models

SYSTEM ROLE:
Adapter-style explainer for rule-based credit model.

PROJECT:
CreditBridge — Rule-Based Explainability.

IMPLEMENTATION:
- Converts rule impacts into structured explanations
- No hardcoded text in controller layer
- Compatible with BaseExplainer interface
"""

from typing import Dict, Any, List
from .base import BaseExplainer


class RuleCreditExplainer(BaseExplainer):
    """
    Explainer for rule-based credit scoring models.
    
    Extracts decision factors from rule-based models and formats them
    into human-readable explanations with factor contributions.
    
    Supports:
    - RuleBasedCreditModel-v1.0
    - Future rule-based variants
    """
    
    def supports(self, model_name: str) -> bool:
        """Check if this explainer supports the given model."""
        supported_models = [
            "RuleBasedCreditModel",
            "RuleBasedCreditModel-v1.0",
            "CreditRuleModel"  # Legacy name
        ]
        return any(supported in model_name for supported in supported_models)
    
    def explain(self, input_data: dict, model_output: dict) -> dict:
        """
        Generate explanation for rule-based credit score.
        
        Args:
            input_data: Original input data (borrower, loan_request)
            model_output: Model prediction output with factors
        
        Returns:
            Structured explanation with factors, summary, and confidence
        """
        score = model_output.get("score", 0)
        risk_level = model_output.get("risk_level", "unknown")
        
        # Extract factors (if available from model's _last_factors)
        factors = self._extract_factors(input_data, model_output)
        
        # Generate summary
        summary = self._generate_summary(score, risk_level, factors)
        
        # Calculate confidence (rule-based models have high confidence)
        confidence = self._calculate_confidence(factors)
        
        return {
            "type": "rule_based",
            "factors": factors,
            "summary": summary,
            "confidence": confidence,
            "score": score,
            "risk_level": risk_level,
            "details": {
                "method": "rule-based",
                "model": "RuleBasedCreditModel-v1.0",
                "rules_applied": len(factors)
            },
            "method": "rule_based"
        }
    
    def _extract_factors(self, input_data: dict, model_output: dict) -> List[Dict[str, Any]]:
        """Extract and format decision factors."""
        factors = []
        
        # Base score
        factors.append({
            "factor": "Base Score",
            "impact": "+50",
            "explanation": "Starting baseline for all borrowers",
            "value": 50
        })
        
        # Loan amount impact
        borrower = input_data.get("borrower", {})
        loan = input_data.get("loan_request") or input_data.get("loan", {})
        amount = loan.get("requested_amount", 0)
        
        if amount < 5000:
            factors.append({
                "factor": "Loan Amount (Small)",
                "impact": "+20",
                "explanation": f"Requesting ${amount:,} (low risk)",
                "value": amount
            })
        elif amount > 50000:
            factors.append({
                "factor": "Loan Amount (Large)",
                "impact": "-10",
                "explanation": f"Requesting ${amount:,} (higher risk)",
                "value": amount
            })
        else:
            factors.append({
                "factor": "Loan Amount (Moderate)",
                "impact": "+0",
                "explanation": f"Requesting ${amount:,} (neutral)",
                "value": amount
            })
        
        # Region impact
        region = borrower.get("region", "").lower()
        if region in ["dhaka", "chattogram", "sylhet"]:
            factors.append({
                "factor": "Geographic Region",
                "impact": "+5",
                "explanation": f"Operating in {region.title()} (established market)",
                "value": region.title()
            })
        else:
            factors.append({
                "factor": "Geographic Region",
                "impact": "+0",
                "explanation": f"Operating in {region.title() if region else 'Unknown'} (standard)",
                "value": region.title() if region else "Unknown"
            })
        
        return factors
    
    def _generate_summary(self, score: int, risk_level: str, factors: List[dict]) -> str:
        """Generate human-readable summary."""
        positive_factors = [f for f in factors if "+" in f.get("impact", "") and f["impact"] != "+0"]
        negative_factors = [f for f in factors if "-" in f.get("impact", "")]
        
        summary = f"Credit Score: {score}/100 (Risk: {risk_level.upper()})"
        
        if positive_factors:
            summary += f" - {len(positive_factors)} positive factor(s)"
        if negative_factors:
            summary += f", {len(negative_factors)} negative factor(s)"
        
        return summary
    
    def _calculate_confidence(self, factors: List[dict]) -> float:
        """Calculate confidence level (rule-based models have high confidence)."""
        # Rule-based models have deterministic outputs
        # Confidence is high when multiple factors are considered
        num_factors = len(factors)
        
        if num_factors >= 3:
            return 0.95
        elif num_factors >= 2:
            return 0.85
        else:
            return 0.75


# Backward compatibility alias
RuleExplainer = RuleCreditExplainer

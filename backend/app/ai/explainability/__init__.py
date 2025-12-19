"""
Explainability Package for CreditBridge

Production-grade explainability layer for AI model decisions.
Provides consistent, human-readable explanations across all model types.

Architecture:
- BaseExplainer: Abstract interface for all explainers
- ExplainerRegistry: Automatic explainer routing based on model type
- Future: RuleExplainer, SHAPExplainer, LIMEExplainer, etc.

Usage:
    >>> from app.ai.explainability import BaseExplainer, ExplainerRegistry
    >>> registry = ExplainerRegistry()
    >>> explanation = registry.explain(model_name, input_data, model_output)
"""

from app.ai.explainability.base import BaseExplainer, ExplainerRegistry
from app.ai.explainability.rule_explainer import RuleCreditExplainer, RuleExplainer
from app.ai.explainability.graph_explainer import GraphExplainer
from app.ai.explainability.trustgraph_explainer import TrustGraphExplainer
from app.ai.explainability.engine import ExplainabilityEngine, get_explainability_engine
from app.ai.explainability.utils import (
    get_explainer_registry,
    explain_prediction,
    explain_ensemble_result,
    get_explanation
)


def build_explanation(score_result: dict) -> dict:
    """
    Legacy backward-compatible explanation builder.
    
    Converts old-style credit score results to explanation format.
    For new code, use explain_prediction() or explain_ensemble_result().
    
    Args:
        score_result: Dict with 'score' and optionally 'factors'
    
    Returns:
        Dict with 'summary' and 'key_points' keys
    """
    score = score_result.get("score", 0)
    factors = score_result.get("factors", [])
    
    # Generate summary
    if score >= 80:
        summary = f"Credit Score: {score}/100 - Strong creditworthiness"
    elif score >= 60:
        summary = f"Credit Score: {score}/100 - Acceptable credit profile"
    else:
        summary = f"Credit Score: {score}/100 - Higher risk profile"
    
    # Build key points from factors
    key_points = []
    for factor in factors:
        if isinstance(factor, dict):
            factor_text = factor.get("factor", "")
            impact = factor.get("impact", "")
            explanation = factor.get("explanation", "")
            if factor_text:
                key_points.append(f"{factor_text}: {impact} - {explanation}")
        elif isinstance(factor, str):
            key_points.append(factor)
    
    # If no factors provided, add generic points
    if not key_points:
        if score >= 70:
            key_points = [
                "Credit assessment completed",
                "Profile meets lending criteria",
                "No significant risk factors detected"
            ]
        else:
            key_points = [
                "Credit assessment completed",
                "Additional review may be required"
            ]
    
    return {
        "summary": summary,
        "key_points": key_points,
        "explanation": summary  # Legacy field
    }


__all__ = [
    "BaseExplainer",
    "ExplainerRegistry",
    "RuleCreditExplainer",
    "RuleExplainer",  # Backward compatibility
    "GraphExplainer",
    "TrustGraphExplainer",
    "get_explainer_registry",
    "explain_prediction",
    "explain_ensemble_result",
    "get_explanation",
    "build_explanation",  # Legacy function
]

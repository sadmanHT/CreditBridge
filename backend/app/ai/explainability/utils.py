"""
Explainability Utilities
Production-ready helper functions for generating model explanations
"""

from typing import Dict, Any
from app.ai.explainability.base import ExplainerRegistry
from app.ai.explainability.rule_explainer import RuleCreditExplainer
from app.ai.explainability.graph_explainer import GraphExplainer
from app.ai.explainability.trustgraph_explainer import TrustGraphExplainer

# Global registry (singleton pattern)
_global_registry = None


def get_explainer_registry() -> ExplainerRegistry:
    """
    Get the global explainer registry instance.
    
    Lazily initializes the registry on first access with all available explainers.
    Thread-safe for read operations.
    
    Returns:
        ExplainerRegistry: Singleton registry instance
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = ExplainerRegistry()
        
        # Register all available explainers
        _global_registry.register(RuleCreditExplainer())
        _global_registry.register(GraphExplainer())
        _global_registry.register(TrustGraphExplainer())
        
        # Future explainers can be added here:
        # _global_registry.register(SHAPExplainer())
        # _global_registry.register(LIMEExplainer())
    
    return _global_registry


def explain_prediction(
    model_name: str,
    input_data: Dict[str, Any],
    prediction: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate human-readable explanation for a model prediction.
    
    Convenience wrapper that automatically routes to the appropriate explainer
    based on model name.
    
    Args:
        model_name: Name of the model (e.g., "RuleBasedCreditModel-v1.0")
        input_data: Original input data used for prediction
        prediction: Model's prediction output
    
    Returns:
        Explanation dict with summary, factors, confidence, and details
    
    Raises:
        ValueError: If no explainer is available for the given model
    
    Example:
        >>> from app.ai.explainability.utils import explain_prediction
        >>> input_data = {"borrower": {...}, "loan": {...}}
        >>> prediction = {"score": 65, "risk_level": "medium"}
        >>> explanation = explain_prediction(
        ...     "RuleBasedCreditModel-v1.0", 
        ...     input_data, 
        ...     prediction
        ... )
        >>> print(explanation['summary'])
        'Credit Score: 65/100 (Risk: MEDIUM) - 2 positive factor(s)'
    """
    registry = get_explainer_registry()
    return registry.explain(model_name, input_data, prediction)


def explain_ensemble_result(
    input_data: Dict[str, Any],
    ensemble_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate explanations for all models in an ensemble result.
    
    Takes an ensemble prediction result and generates detailed explanations
    for each constituent model, plus an overall summary.
    
    Args:
        input_data: Original input data used for prediction
        ensemble_result: Result from ModelEnsemble.run() or .predict()
    
    Returns:
        Dict containing:
        - model_explanations: Dict mapping model names to explanations
        - overall_summary: Combined summary of all models
        - final_score: Final ensemble score
        - fraud_flag: Whether fraud was detected
        - confidence: Average confidence across explainable models
    
    Example:
        >>> from app.ai.registry import get_ensemble
        >>> from app.ai.explainability.utils import explain_ensemble_result
        >>> 
        >>> ensemble = get_ensemble()
        >>> result = ensemble.run(input_data)
        >>> explanations = explain_ensemble_result(input_data, result)
        >>> 
        >>> for model, exp in explanations['model_explanations'].items():
        ...     print(f"{model}: {exp['summary']}")
    """
    registry = get_explainer_registry()
    
    model_explanations = {}
    confidence_scores = []
    
    # Generate explanation for each model
    for model_name, model_output in ensemble_result.get("model_outputs", {}).items():
        try:
            explanation = registry.explain(model_name, input_data, model_output)
            model_explanations[model_name] = explanation
            confidence_scores.append(explanation.get("confidence", 0))
        except ValueError:
            # No explainer available for this model - skip it
            model_explanations[model_name] = {
                "summary": f"No explanation available for {model_name}",
                "confidence": 0,
                "method": "unavailable"
            }
    
    # Calculate average confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    # Generate overall summary
    overall_summary = _generate_overall_summary(
        ensemble_result.get("final_credit_score", 0),
        ensemble_result.get("fraud_flag", False),
        model_explanations
    )
    
    return {
        "model_explanations": model_explanations,
        "overall_summary": overall_summary,
        "final_score": ensemble_result.get("final_credit_score", 0),
        "fraud_flag": ensemble_result.get("fraud_flag", False),
        "confidence": avg_confidence,
        "metadata": {
            "num_models": len(model_explanations),
            "num_explained": len([e for e in model_explanations.values() if e["method"] != "unavailable"])
        }
    }


def _generate_overall_summary(
    final_score: float,
    fraud_flag: bool,
    model_explanations: Dict[str, Dict[str, Any]]
) -> str:
    """Generate human-readable overall summary."""
    summary = f"Final Credit Score: {final_score:.2f}/100"
    
    if fraud_flag:
        summary += " [FRAUD RISK DETECTED]"
    
    # Count positive/negative signals across all models
    total_positive = 0
    total_negative = 0
    
    for explanation in model_explanations.values():
        factors = explanation.get("factors", [])
        for factor in factors:
            impact = factor.get("impact", "")
            if impact == "positive" or (isinstance(impact, str) and "+" in impact and impact != "+0"):
                total_positive += 1
            elif impact == "negative" or (isinstance(impact, str) and "-" in impact):
                total_negative += 1
    
    if total_positive > 0 or total_negative > 0:
        summary += f" | {total_positive} positive, {total_negative} negative factors"
    
    return summary


# Convenience function for API endpoints
def get_explanation(
    model_name: str,
    input_data: Dict[str, Any],
    prediction: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Alias for explain_prediction() for cleaner API usage.
    
    Same functionality as explain_prediction, just with a shorter name.
    """
    return explain_prediction(model_name, input_data, prediction)

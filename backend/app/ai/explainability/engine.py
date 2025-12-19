"""
Explainability Engine
Central orchestration for multi-model explanation generation

SYSTEM ROLE:
Central explainability engine for multi-model AI system.

PROJECT:
CreditBridge — Explainability Engine.

IMPLEMENTATION:
- Registers multiple explainers
- Routes model outputs to correct explainer
- Merges explanations into unified structure
- Deterministic behavior
- Model-agnostic design
- SHAP/LIME ready
"""

from typing import Dict, Any, List, Optional
from .base import BaseExplainer, ExplainerRegistry


class ExplainabilityEngine:
    """
    Central orchestration engine for generating explanations across multiple models.
    
    The engine coordinates explanation generation for ensemble predictions,
    routing each model's output to the appropriate explainer and merging
    the results into a unified, human-readable format.
    
    Features:
    - Automatic explainer registration and routing
    - Multi-model explanation aggregation
    - Unified output format
    - Graceful degradation for missing explainers
    - Model-agnostic architecture
    - Extensible for SHAP/LIME/ELI5 integration
    
    Design Principles:
    - Deterministic: Same inputs always produce same outputs
    - Model-agnostic: No assumptions about model types
    - Fault-tolerant: Handles missing explainers gracefully
    - Production-ready: Comprehensive error handling
    """
    
    def __init__(self, registry: Optional[ExplainerRegistry] = None):
        """
        Initialize the explainability engine.
        
        Args:
            registry: Optional ExplainerRegistry. If not provided,
                     a new registry will be created.
        """
        self.registry = registry if registry is not None else ExplainerRegistry()
        self._explainer_cache: Dict[str, BaseExplainer] = {}
    
    def register_explainer(self, explainer: BaseExplainer) -> None:
        """
        Register a new explainer with the engine.
        
        Args:
            explainer: BaseExplainer instance to register
        """
        self.registry.register(explainer)
        # Clear cache since registry changed
        self._explainer_cache.clear()
    
    def explain_single(
        self,
        model_name: str,
        input_data: Dict[str, Any],
        model_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate explanation for a single model's output.
        
        Args:
            model_name: Name of the model
            input_data: Original input data used for prediction
            model_output: Model's prediction output
        
        Returns:
            Explanation dict from the appropriate explainer
        
        Raises:
            ValueError: If no explainer is available for the model
        """
        # Try to use cached explainer for performance
        if model_name in self._explainer_cache:
            explainer = self._explainer_cache[model_name]
        else:
            explainer = self.registry.get_explainer(model_name)
            self._explainer_cache[model_name] = explainer
        
        return explainer.explain(input_data, model_output)
    
    def explain_ensemble(
        self,
        input_data: Dict[str, Any],
        ensemble_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate unified explanation for ensemble prediction.
        
        Coordinates explanation generation across all models in the ensemble,
        merges individual explanations, and produces a unified output with
        overall summary and per-model details.
        
        Args:
            input_data: Original input data used for prediction
            ensemble_result: Result from ensemble containing:
                - final_credit_score: Overall score
                - fraud_flag: Fraud detection flag
                - model_outputs: Dict mapping model names to their outputs
        
        Returns:
            Unified explanation dict containing:
            - overall_summary: High-level summary of the decision
            - final_score: Final ensemble score
            - fraud_flag: Whether fraud was detected
            - confidence: Average confidence across models
            - model_explanations: Individual explanations per model
            - aggregated_factors: Merged factors from all models
            - metadata: Additional information about the explanation
        """
        model_explanations = {}
        confidence_scores = []
        all_factors = []
        
        # Generate explanation for each model
        for model_name, model_output in ensemble_result.get("model_outputs", {}).items():
            try:
                explanation = self.explain_single(model_name, input_data, model_output)
                model_explanations[model_name] = explanation
                
                # Collect confidence scores
                if "confidence" in explanation:
                    confidence_scores.append(explanation["confidence"])
                
                # Collect factors for aggregation
                if "factors" in explanation:
                    all_factors.extend(explanation["factors"])
                elif "graph_insights" in explanation:
                    all_factors.extend(explanation["graph_insights"])
                
            except ValueError as e:
                # No explainer available - add placeholder
                model_explanations[model_name] = {
                    "type": "unavailable",
                    "summary": f"No explanation available for {model_name}",
                    "error": str(e)
                }
        
        # Calculate aggregate metrics
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0.0
        )
        
        # Generate overall summary
        final_score = ensemble_result.get("final_credit_score", 0)
        fraud_flag = ensemble_result.get("fraud_flag", False)
        overall_summary = self._generate_overall_summary(
            final_score,
            fraud_flag,
            model_explanations
        )
        
        # Aggregate factors (deduplicate and rank by importance)
        aggregated_factors = self._aggregate_factors(all_factors)
        
        return {
            "overall_summary": overall_summary,
            "final_score": final_score,
            "fraud_flag": fraud_flag,
            "confidence": avg_confidence,
            "model_explanations": model_explanations,
            "aggregated_factors": aggregated_factors,
            "metadata": {
                "num_models": len(ensemble_result.get("model_outputs", {})),
                "num_explained": len([
                    e for e in model_explanations.values()
                    if e.get("type") != "unavailable"
                ]),
                "explanation_method": "multi_model_ensemble",
                "engine_version": "1.0.0"
            }
        }
    
    def explain_batch(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate explanations for multiple predictions in batch.
        
        Efficiently processes multiple explanation requests while
        maintaining explainer state and caching.
        
        Args:
            requests: List of dicts, each containing:
                - input_data: Original input data
                - ensemble_result: Ensemble prediction result
        
        Returns:
            List of explanation dicts, one per request
        """
        explanations = []
        
        for request in requests:
            input_data = request.get("input_data", {})
            ensemble_result = request.get("ensemble_result", {})
            
            try:
                explanation = self.explain_ensemble(input_data, ensemble_result)
                explanations.append(explanation)
            except Exception as e:
                # Handle errors gracefully
                explanations.append({
                    "error": str(e),
                    "overall_summary": "Explanation generation failed",
                    "confidence": 0.0
                })
        
        return explanations
    
    def _generate_overall_summary(
        self,
        final_score: float,
        fraud_flag: bool,
        model_explanations: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate unified summary across all model explanations."""
        summary = f"Final Credit Score: {final_score:.2f}/100"
        
        if fraud_flag:
            summary += " [FRAUD RISK DETECTED]"
        
        # Count positive/negative signals across all models
        total_positive = 0
        total_negative = 0
        
        for explanation in model_explanations.values():
            # Skip unavailable explanations
            if explanation.get("type") == "unavailable":
                continue
            
            # Count from factors (rule-based models)
            factors = explanation.get("factors", [])
            for factor in factors:
                impact = factor.get("impact", "")
                if impact == "positive" or (isinstance(impact, str) and "+" in impact and impact != "+0"):
                    total_positive += 1
                elif impact == "negative" or (isinstance(impact, str) and "-" in impact):
                    total_negative += 1
            
            # Count from graph insights (graph-based models)
            insights = explanation.get("graph_insights", [])
            for insight in insights:
                impact = insight.get("impact", "")
                if impact == "positive":
                    total_positive += 1
                elif impact == "negative":
                    total_negative += 1
        
        if total_positive > 0 or total_negative > 0:
            summary += f" | {total_positive} positive, {total_negative} negative factors"
        
        return summary
    
    def _aggregate_factors(
        self,
        all_factors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate and rank factors from multiple models.
        
        Combines factors from different models, removes duplicates,
        and ranks by importance/weight.
        """
        if not all_factors:
            return []
        
        # Group similar factors (simple implementation)
        factor_map: Dict[str, Dict[str, Any]] = {}
        
        for factor in all_factors:
            # Use factor name or insight as key
            key = factor.get("factor") or factor.get("insight", "")
            if not key:
                continue
            
            # If factor doesn't exist, add it
            if key not in factor_map:
                factor_map[key] = factor
            else:
                # If it exists, keep the one with higher weight/impact
                existing = factor_map[key]
                existing_weight = abs(existing.get("weight", 0))
                new_weight = abs(factor.get("weight", 0))
                
                if new_weight > existing_weight:
                    factor_map[key] = factor
        
        # Convert back to list and sort by weight (highest first)
        aggregated = list(factor_map.values())
        aggregated.sort(
            key=lambda f: abs(f.get("weight", 0)),
            reverse=True
        )
        
        return aggregated
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of all model types supported by registered explainers.
        
        Returns:
            List of model name patterns that can be explained
        """
        # This is a simplified version - could be enhanced
        # to query each explainer for its supported patterns
        return [
            "RuleBasedCreditModel",
            "TrustGraphModel",
            "GraphModel"
        ]
    
    def get_registered_explainers(self) -> List[str]:
        """
        Get list of registered explainer class names.
        
        Returns:
            List of explainer class names currently registered
        """
        return [
            explainer.__class__.__name__
            for explainer in self.registry._explainers
        ]


# Singleton instance for global access
_global_engine: Optional[ExplainabilityEngine] = None


def get_explainability_engine() -> ExplainabilityEngine:
    """
    Get the global explainability engine instance.
    
    Lazily initializes the engine with all available explainers.
    Thread-safe for read operations.
    
    Returns:
        ExplainabilityEngine: Singleton engine instance
    """
    global _global_engine
    
    if _global_engine is None:
        from .rule_explainer import RuleCreditExplainer
        from .graph_explainer import GraphExplainer
        from .trustgraph_explainer import TrustGraphExplainer
        
        registry = ExplainerRegistry()
        registry.register(RuleCreditExplainer())
        registry.register(GraphExplainer())
        registry.register(TrustGraphExplainer())
        
        _global_engine = ExplainabilityEngine(registry)
    
    return _global_engine

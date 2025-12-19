"""
Base Explainability Interface for CreditBridge

Production-grade abstraction for AI model explainability.
Supports rule-based, graph-based, and ML-based explanations.

Design Principles:
- Pure abstraction (no concrete logic)
- Model-agnostic interface
- Extensible for advanced explainability libraries (SHAP, LIME, ELI5)
- Consistent output format across all explainers

FUTURE EXTENSIBILITY:
To add new explainers:
1. Create class inheriting from BaseExplainer
2. Implement supports() to match target models
3. Implement explain() with explainability logic
4. Register in explainer registry

Examples of future explainers:
- SHAPExplainer (for ML models)
- LIMEExplainer (for black-box models)
- ELI5Explainer (for scikit-learn models)
- RuleExplainer (for rule-based models)
- GraphExplainer (for graph-based models)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseExplainer(ABC):
    """
    Abstract base class for all model explainers.
    
    Defines the contract that all explainability implementations must follow.
    This enables consistent explanation generation across different model types
    (rule-based, graph-based, ML-based) and explanation techniques (SHAP, LIME, etc.).
    
    Thread Safety: Implementations should be stateless for concurrent use.
    Determinism: Explanations should be reproducible for identical inputs.
    
    EXTENSIBILITY NOTES:
    1. Implement supports() to declare which models this explainer handles
    2. Implement explain() to generate human-readable explanations
    3. Return standardized dict format for consistency across all explainers
    4. Keep implementations stateless (no instance variables that change)
    """
    
    @abstractmethod
    def supports(self, model_name: str) -> bool:
        """
        Check if this explainer supports the given model.
        
        This allows the explainability system to automatically route
        explanation requests to the appropriate explainer implementation.
        
        Args:
            model_name: Name/identifier of the model (e.g., "RuleBasedCreditModel-v1.0")
        
        Returns:
            True if this explainer can explain the model, False otherwise
        
        Example:
            >>> explainer = RuleExplainer()
            >>> explainer.supports("RuleBasedCreditModel-v1.0")
            True
            >>> explainer.supports("TrustGraphModel-v1.0-POC")
            False
        
        Implementation Guidelines:
        - Use string matching, regex, or model type checking
        - Return False if unsure (fail safe)
        - Can match multiple model types if explainer is generic
        
        EXTENSIBILITY: Add new model name patterns as needed.
        """
        pass
    
    @abstractmethod
    def explain(
        self,
        input_data: Dict[str, Any],
        model_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate human-readable explanation for model prediction.
        
        Takes the original input and model's output, then produces
        a structured explanation showing why the model made that decision.
        
        Args:
            input_data: Original input to the model
                Format: {"borrower": {...}, "loan_request": {...}}
            model_output: Model's prediction output
                Format varies by model but typically includes score/decision
        
        Returns:
            Explanation dictionary with standardized structure:
            {
                "summary": str,              # High-level explanation (1-2 sentences)
                "factors": List[Dict],       # Individual contributing factors
                "confidence": float,         # Explanation confidence (0.0-1.0)
                "details": Dict[str, Any],   # Additional context/metadata
                "method": str                # Explanation method used (e.g., "SHAP", "rules")
            }
        
        Example:
            >>> explainer = RuleExplainer()
            >>> input_data = {"borrower": {"region": "Dhaka"}, "loan_request": {"requested_amount": 15000}}
            >>> model_output = {"score": 65, "risk_level": "medium"}
            >>> explanation = explainer.explain(input_data, model_output)
            >>> print(explanation["summary"])
            "Credit score of 65/100 based on loan amount and regional factors"
        
        Implementation Guidelines:
        - Extract relevant features from input_data
        - Analyze model_output for key decision factors
        - Generate human-readable factor descriptions
        - Return consistent dict structure (see format above)
        - Include confidence measure when possible
        - Add visualization data to "details" if applicable
        
        EXTENSIBILITY:
        - For ML models: Use SHAP/LIME to compute feature importance
        - For rule-based: Extract and explain fired rules
        - For graph-based: Explain network structure influence
        - For ensemble: Show per-model contributions
        
        Error Handling:
        - Raise ValueError for unsupported model types
        - Return low-confidence explanation on uncertainty
        - Log errors but don't fail silently
        """
        pass


class ExplainerRegistry:
    """
    Registry for managing explainer instances.
    
    Automatically routes explanation requests to appropriate explainers
    based on model name matching via supports() method.
    
    EXTENSIBILITY: Register new explainers by adding to _explainers list.
    """
    
    def __init__(self):
        """Initialize registry with available explainers."""
        # EXTENSIBILITY: Add new explainer instances here
        self._explainers = []
        # Example: self._explainers = [RuleExplainer(), SHAPExplainer(), LIMEExplainer()]
    
    def register(self, explainer: BaseExplainer) -> None:
        """
        Register a new explainer.
        
        Args:
            explainer: Explainer instance implementing BaseExplainer
        """
        self._explainers.append(explainer)
    
    def get_explainer(self, model_name: str) -> BaseExplainer:
        """
        Find appropriate explainer for the given model.
        
        Args:
            model_name: Model identifier
        
        Returns:
            Explainer instance that supports the model
        
        Raises:
            ValueError: If no explainer supports the model
        """
        for explainer in self._explainers:
            if explainer.supports(model_name):
                return explainer
        
        raise ValueError(f"No explainer available for model: {model_name}")
    
    def explain(
        self,
        model_name: str,
        input_data: Dict[str, Any],
        model_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate explanation using appropriate explainer.
        
        Convenience method that finds the right explainer and
        generates explanation in one call.
        
        Args:
            model_name: Model identifier
            input_data: Original model input
            model_output: Model prediction output
        
        Returns:
            Explanation dictionary
        """
        explainer = self.get_explainer(model_name)
        return explainer.explain(input_data, model_output)

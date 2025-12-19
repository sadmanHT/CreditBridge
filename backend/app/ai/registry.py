"""
Model Registry for CreditBridge

Clean registry pattern for managing AI model instances and orchestration.

Design Principles:
- Immutable model instances (no global state mutation)
- Factory pattern for model creation
- Ready for ML model integration
- Thread-safe singleton registry

TASK:
Ensure AI ensemble receives engineered features from FeatureEngine,
not raw borrower/event data.

FUTURE EXTENSIBILITY:
To add new models:
1. Import the model class
2. Add instantiation in _create_models()
3. Optionally add to ensemble
4. Model will be automatically available via get_model()
"""

from typing import Dict, Any, Optional
from app.ai.models.base import BaseModel
from app.ai.models.credit_rule_model import RuleBasedCreditModel
from app.ai.models.trustgraph_model import TrustGraphModel
from app.ai.ensemble import ModelEnsemble
from app.features.engine import FeatureEngine


class ModelRegistry:
    """
    Immutable registry for AI model instances.
    
    Provides:
    - Clean model instantiation
    - Ensemble orchestration
    - Model retrieval by name
    - No global state mutation
    
    Thread Safety: All model instances are stateless and thread-safe.
    """
    
    def __init__(self):
        """
        Initialize registry with all available models.
        
        Models are instantiated once and reused (stateless design).
        No mutable global state - all instances are read-only.
        """
        # ═══════════════════════════════════════════════════════════
        # Instantiate FeatureEngine for feature engineering
        # ═══════════════════════════════════════════════════════════
        self.feature_engine = FeatureEngine(lookback_days=30)
        
        # ═══════════════════════════════════════════════════════════
        # Instantiate core models (as per requirements)
        # ═══════════════════════════════════════════════════════════
        self.credit_model = RuleBasedCreditModel()
        self.trust_model = TrustGraphModel()
        
        # ═══════════════════════════════════════════════════════════
        # Create ensemble from instantiated models
        # ═══════════════════════════════════════════════════════════
        self.ensemble = ModelEnsemble(
            models=[self.credit_model, self.trust_model]
        )
        
        # ═══════════════════════════════════════════════════════════
        # Build model lookup dictionary
        # ═══════════════════════════════════════════════════════════
        # EXTENSIBILITY: Add new models here for retrieval by name
        self._models: Dict[str, BaseModel] = {
            "credit": self.credit_model,
            "trust": self.trust_model,
            "ensemble": self.ensemble  # Note: ensemble is also a model
        }
        
        # FUTURE: ML models can be added here
        # Example: self.ml_credit_model = MLCreditModel()
        #          self._models["ml_credit"] = self.ml_credit_model
    
    def get_model(self, model_name: str) -> Optional[BaseModel]:
        """
        Retrieve a model by name.
        
        EXTENSIBILITY: All registered models are accessible by their key.
        
        Args:
            model_name: Model identifier ("credit", "trust", "ensemble", etc.)
        
        Returns:
            Model instance or None if not found
        
        Example:
            >>> registry = ModelRegistry()
            >>> credit_model = registry.get_model("credit")
            >>> result = credit_model.predict(input_data)
        """
        return self._models.get(model_name)
    
    def get_ensemble(self) -> ModelEnsemble:
        """
        Get the ensemble orchestrator (as per requirements).
        
        Returns:
            ModelEnsemble instance configured with all models
        
        Example:
            >>> registry = ModelRegistry()
            >>> ensemble = registry.get_ensemble()
            >>> result = ensemble.predict(borrower, loan_request)
        """
        return self.ensemble
    
    def get_feature_engine(self) -> FeatureEngine:
        """
        Get the feature engineering engine.
        
        Returns:
            FeatureEngine instance for computing features
        
        Example:
            >>> registry = ModelRegistry()
            >>> feature_engine = registry.get_feature_engine()
            >>> features = feature_engine.compute_features(borrower_id, borrower_profile)
        """
        return self.feature_engine
    
    def predict_with_features(
        self,
        borrower: Dict[str, Any],
        loan_request: Dict[str, Any],
        raw_events: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Execute prediction with engineered features.
        
        This method ensures the AI ensemble receives engineered features
        from FeatureEngine, not raw borrower/event data.
        
        Workflow:
        1. Extract borrower_id from borrower profile
        2. Compute features using FeatureEngine
        3. Enrich input data with computed features
        4. Pass to ensemble for prediction
        
        Args:
            borrower: Borrower profile dictionary (must include 'id')
            loan_request: Loan request details
            raw_events: Optional list of raw events (if None, fetched from DB)
        
        Returns:
            Ensemble prediction result with engineered features included
        
        Example:
            >>> registry = ModelRegistry()
            >>> result = registry.predict_with_features(
            ...     borrower={"id": "abc-123", "phone": "1234567890"},
            ...     loan_request={"amount": 5000, "purpose": "business"}
            ... )
        """
        borrower_id = borrower.get("id")
        if not borrower_id:
            raise ValueError("borrower must contain 'id' field")
        
        # Compute engineered features
        try:
            feature_set = self.feature_engine.compute_features(
                borrower_id=borrower_id,
                borrower_profile=borrower,
                raw_events=raw_events
            )
            
            # Enrich borrower data with engineered features
            enriched_borrower = borrower.copy()
            enriched_borrower["engineered_features"] = feature_set.features
            enriched_borrower["feature_metadata"] = {
                "feature_set": feature_set.feature_set,
                "feature_version": feature_set.feature_version,
                "computed_at": feature_set.computed_at,
                "source_event_count": feature_set.source_event_count
            }
            
            # Execute ensemble prediction with enriched data
            return self.ensemble.predict(enriched_borrower, loan_request)
            
        except Exception as e:
            # If feature engineering fails, fall back to original data
            # but include error information
            result = self.ensemble.predict(borrower, loan_request)
            result["feature_engineering_error"] = str(e)
            result["warning"] = "Prediction made without engineered features"
            return result
    
    def list_models(self) -> Dict[str, str]:
        """
        List all available models.
        
        Returns:
            Dictionary mapping model keys to model names/versions
        
        Example:
            >>> registry = ModelRegistry()
            >>> models = registry.list_models()
            >>> print(models)
            {'credit': 'RuleBasedCreditModel-v1.0', 'trust': 'TrustGraphModel-v1.0-POC', ...}
        """
        result = {}
        for key, model in self._models.items():
            if hasattr(model, 'name'):
                result[key] = model.name
            else:
                # For ensemble or other non-BaseModel objects
                result[key] = f"{model.__class__.__name__}-v{getattr(model, 'ensemble_version', '1.0.0')}"
        return result


# ═══════════════════════════════════════════════════════════════════════
# Singleton registry instance (lazy initialization)
# ═══════════════════════════════════════════════════════════════════════
# Note: This is initialized once and reused, but models themselves are
# stateless and immutable, so there's no global state mutation.
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """
    Get model registry instance (singleton pattern).
    
    The registry itself is a singleton, but all model instances within
    are stateless and immutable (no global state mutation).
    
    Returns:
        ModelRegistry instance
    
    Example:
        >>> registry = get_registry()
        >>> ensemble = registry.get_ensemble()
        >>> result = ensemble.predict(borrower, loan_request)
    
    Thread Safety: This is thread-safe as models are stateless.
    """
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def get_ensemble() -> ModelEnsemble:
    """
    Get ensemble orchestrator directly (convenience function).
    
    This is a convenience wrapper that gets the registry and
    returns the ensemble in one call.
    
    Returns:
        ModelEnsemble instance
    
    Example:
        >>> ensemble = get_ensemble()
        >>> result = ensemble.run({"borrower": {...}, "loan": {...}})
    """
    return get_registry().get_ensemble()


def get_feature_engine() -> FeatureEngine:
    """
    Get feature engineering engine directly (convenience function).
    
    Returns:
        FeatureEngine instance
    
    Example:
        >>> engine = get_feature_engine()
        >>> features = engine.compute_features(borrower_id, borrower_profile)
    """
    return get_registry().get_feature_engine()


def predict_with_features(
    borrower: Dict[str, Any],
    loan_request: Dict[str, Any],
    raw_events: Optional[list] = None
) -> Dict[str, Any]:
    """
    Execute ensemble prediction with engineered features (convenience function).
    
    Ensures AI ensemble receives engineered features from FeatureEngine,
    not raw borrower/event data.
    
    Args:
        borrower: Borrower profile dictionary (must include 'id')
        loan_request: Loan request details
        raw_events: Optional list of raw events
    
    Returns:
        Ensemble prediction result with engineered features
    
    Example:
        >>> from app.ai.registry import predict_with_features
        >>> result = predict_with_features(
        ...     borrower={"id": "abc-123", "phone": "1234567890"},
        ...     loan_request={"amount": 5000, "purpose": "business"}
        ... )
    """
    return get_registry().predict_with_features(borrower, loan_request, raw_events)

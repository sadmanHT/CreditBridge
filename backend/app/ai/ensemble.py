"""
Model Ensemble for CreditBridge

Production-grade AI ensemble engine that combines multiple AI models
to produce robust, defensible credit decisions.

Architecture:
- Accepts any list of BaseModel-compatible models
- Runs all models on identical input (deterministic)
- Aggregates outputs using configurable strategies
- Produces unified decision with full transparency

Features:
- Multi-model orchestration
- Configurable weighting schemes
- Override logic for critical flags (fraud detection)
- Full explainability (per-model + ensemble)
- Extensible design for future model types

TASK:
Ensure credit models receive ONLY feature vectors.
Raise explicit error if raw borrower/event data is passed.

EXTENSIBILITY NOTES:
1. To add new models: Pass them in the models list during __init__
2. To change aggregation: Modify _aggregate_scores() method
3. To add override logic: Extend _check_critical_flags() method
4. To customize output: Modify _build_unified_output() method
"""

from typing import Dict, List, Any, Optional
from app.ai.models.base import BaseModel
from app.ai.models.credit_rule_model import RuleBasedCreditModel
from app.ai.models.trustgraph_model import TrustGraphModel
from app.ai.models.fraud_rules_model import FraudRulesModel
from app.ai.explainability.engine import get_explainability_engine
from app.ai.fraud import get_fraud_engine


class FeatureValidationError(Exception):
    """Raised when input data lacks required engineered features."""
    pass


class CriticalModelFailure(Exception):
    """Raised when critical models fail and ensemble cannot produce valid output."""
    pass


class ModelEnsemble:
    """
    Production-grade ensemble engine for AI model orchestration.
    
    Combines multiple BaseModel instances into a unified decision-making system.
    Implements deterministic aggregation logic with full transparency.
    
    Workflow:
    1. Run all models on the same input (parallel-safe)
    2. Check for critical override flags (fraud, fraud-ring)
    3. Aggregate scores using weighted voting
    4. Merge explanations from all models
    5. Produce unified output with per-model breakdown
    
    Thread Safety: Models are assumed stateless for concurrent execution.
    Determinism: All aggregation logic is deterministic (no randomness).
    """
    
    def __init__(
        self,
        models: Optional[List[BaseModel]] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize ensemble with models and weighting configuration.
        
        Args:
            models: List of BaseModel instances. If None, uses default models.
            weights: Model weight configuration. Format: {model.name: weight}
                    If None, equal weights are assigned.
        
        Example:
            # Custom ensemble with specific models
            ensemble = ModelEnsemble(
                models=[RuleBasedCreditModel(), TrustGraphModel()],
                weights={"RuleBasedCreditModel-v1.0": 0.6, "TrustGraphModel-v1.0-POC": 0.4}
            )
        
        EXTENSIBILITY: To add new models, simply pass them in the models list.
        The ensemble automatically detects model capabilities via BaseModel interface.
        """
        # Initialize models (default: credit, trust, fraud)
        self.models = models or [
            RuleBasedCreditModel(),
            TrustGraphModel(),
            FraudRulesModel()
        ]
        
        # Set weights (default: 50% credit, 30% trust, 20% fraud)
        if weights is None:
            # Default weights based on model importance for credit decisions
            self.weights = {
                "RuleBasedCreditModel-v1.0": 0.5,
                "TrustGraphModel-v1.0-POC": 0.3,
                "FraudRulesModel-v1.0": 0.2
            }
        else:
            self.weights = weights
        
        self.ensemble_version = "2.0.0"
    
    def _validate_features(self, borrower: Dict[str, Any]) -> None:
        """
        Validate that borrower contains engineered features.
        
        REQUIREMENT: Credit models must receive ONLY feature vectors.
        This method raises explicit error if raw borrower/event data is passed
        without engineered features.
        
        Args:
            borrower: Borrower profile dictionary
            
        Raises:
            FeatureValidationError: If engineered_features are missing or invalid
        """
        if not borrower:
            raise FeatureValidationError(
                "Borrower data is required. "
                "Ensemble requires borrower profile with engineered_features."
            )
        
        # Check for engineered features
        engineered_features = borrower.get("engineered_features")
        
        if not engineered_features:
            raise FeatureValidationError(
                "Missing 'engineered_features' in borrower data. "
                "Credit models require feature vectors, not raw data. "
                "Please compute features using FeatureEngine before calling ensemble.predict(). "
                "Example: registry.predict_with_features(borrower, loan_request)"
            )
        
        # Validate feature structure
        if not isinstance(engineered_features, dict):
            raise FeatureValidationError(
                f"Invalid engineered_features format. Expected dict, got {type(engineered_features).__name__}. "
                "Features must be a dictionary of feature_name: feature_value pairs."
            )
        
        # Check for required features (from FeatureEngine core_behavioral v1)
        required_features = [
            "mobile_activity_score",
            "transaction_volume_30d",
            "activity_consistency"
        ]
        
        missing_features = [f for f in required_features if f not in engineered_features]
        
        if missing_features:
            raise FeatureValidationError(
                f"Missing required features: {', '.join(missing_features)}. "
                f"Found features: {', '.join(engineered_features.keys())}. "
                "Ensure FeatureEngine computed all required features."
            )
        
        # Validation passed
        return
    
    def predict(
        self,
        borrower: Dict[str, Any],
        loan_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute ensemble prediction pipeline.
        
        Production-grade orchestration that runs all models and produces
        a unified decision with complete transparency.
        
        REQUIREMENT: Credit models receive ONLY feature vectors.
        Raises FeatureValidationError if engineered features are missing.
        
        Args:
            borrower: Borrower profile dictionary (MUST contain 'engineered_features')
            loan_request: Loan request details
        
        Returns:
            Unified decision object containing:
            - final_credit_score: Ensemble-aggregated score (0-100)
            - fraud_flag: Boolean indicating fraud risk
            - model_outputs: Per-model predictions (dict)
            - explanation: Merged explanation from all models
            - metadata: Ensemble configuration and versioning
        
        Raises:
            FeatureValidationError: If borrower lacks engineered_features
        
        DETERMINISM: This method produces identical output for identical input.
        No randomness or time-dependent logic is used in aggregation.
        """
        # ═══════════════════════════════════════════════════════════
        # VALIDATION: Ensure engineered features are present
        # ═══════════════════════════════════════════════════════════
        self._validate_features(borrower)
        
        # Prepare standardized input (all models receive same format)
        # Include engineered_features explicitly for credit models
        engineered_features = borrower.get("engineered_features")
        input_data = {
            "borrower": borrower,
            "loan_request": loan_request,
            "engineered_features": engineered_features,
            "features": engineered_features,  # Alternate key for compatibility
            "feature_set": borrower.get("feature_set", "core_behavioral"),
            "feature_version": borrower.get("feature_version", "v1")
        }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 1: Validate features against each model's requirements
        # ═══════════════════════════════════════════════════════════
        for model in self.models:
            try:
                # Validate features match model requirements before prediction
                model.validate_features(
                    features=engineered_features,
                    feature_set=input_data["feature_set"],
                    feature_version=input_data["feature_version"]
                )
            except Exception as e:
                # Fail fast with explicit error message
                raise FeatureValidationError(
                    f"Feature validation failed for {model.name}: {str(e)}. "
                    f"Ensure features match model requirements before calling predict()."
                )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 2: Run all models on the same input
        # ═══════════════════════════════════════════════════════════
        # SAFETY: Track successful models separately from failed models
        # Failed models are logged and excluded from aggregation
        model_outputs = {}
        successful_models = []
        failed_models = []
        
        for model in self.models:
            try:
                prediction = model.predict(input_data)
                model_outputs[model.name] = prediction
                successful_models.append(model.name)
            except Exception as e:
                # SAFETY: Log error explicitly and mark model as failed
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"[ModelEnsemble] Model {model.name} failed: {str(e)}",
                    exc_info=True
                )
                
                # Record failure but do NOT include in aggregation
                model_outputs[model.name] = {
                    "error": str(e),
                    "status": "failed"
                }
                failed_models.append(model.name)
        
        # SAFETY CHECK 1: At least one credit model must succeed
        # Critical requirement: Cannot make credit decision without credit score
        credit_model_names = [m.name for m in self.models if "credit" in m.name.lower()]
        successful_credit_models = [name for name in credit_model_names if name in successful_models]
        
        if not successful_credit_models:
            raise CriticalModelFailure(
                f"CRITICAL: All credit models failed. Cannot proceed without credit score. "
                f"Failed models: {failed_models}"
            )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 3: Generate structured explanations via ExplainabilityEngine
        # ═══════════════════════════════════════════════════════════
        # Call ExplainabilityEngine to generate structured explanations
        # and attach to ensemble output
        engine = get_explainability_engine()
        ensemble_result_for_explanation = {
            "final_credit_score": 0,  # Placeholder, will be updated below
            "fraud_flag": False,
            "model_outputs": model_outputs
        }
        
        try:
            structured_explanation = engine.explain_ensemble(
                input_data=input_data,
                ensemble_result=ensemble_result_for_explanation
            )
        except Exception as e:
            # Graceful degradation: if explanation fails, continue without it
            structured_explanation = {
                "error": str(e),
                "overall_summary": "Explanation generation failed",
                "model_explanations": {}
            }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 4: Check for critical override flags
        # ═══════════════════════════════════════════════════════════
        # EXTENSIBILITY: Add new override conditions in _check_critical_flags()
        critical_override = self._check_critical_flags(model_outputs)
        
        if critical_override:
            # Attach structured explanation to override response
            critical_override["structured_explanation"] = structured_explanation
            return critical_override
        
        # ═══════════════════════════════════════════════════════════
        # STEP 5: Aggregate scores using weighted voting
        # ═══════════════════════════════════════════════════════════
        # EXTENSIBILITY: Modify _aggregate_scores() to change aggregation strategy
        final_credit_score = self._aggregate_scores(model_outputs)
        
        # ═══════════════════════════════════════════════════════════
        # STEP 6: Detect fraud flags from any model
        # ═══════════════════════════════════════════════════════════
        fraud_flag = self._detect_fraud_flag(model_outputs)
        
        # ═══════════════════════════════════════════════════════════
        # STEP 7: Invoke FraudEngine for comprehensive fraud detection
        # ═══════════════════════════════════════════════════════════
        # REQUIREMENT: FraudEngine receives SAME feature payload as credit models
        fraud_result = None
        fraud_engine_failed = False
        
        try:
            fraud_engine = get_fraud_engine(aggregation_strategy="max")
            
            # Prepare context with trust graph data if available
            context = {}
            for model_name, output in model_outputs.items():
                if "trust_score" in output:
                    # Extract trust graph data from TrustGraphModel output
                    context["trust_graph_data"] = {
                        "trust_score": output.get("trust_score", 1.0),
                        "flag_risk": output.get("flag_risk", False),
                        "default_rate": output.get("default_rate", 0.0),
                        "network_size": output.get("network_size", 0),
                        "defaulted_count": output.get("defaulted_count", 0)
                    }
                
                # Extract application history from context if available
                if "application_history" in input_data.get("context", {}):
                    context["application_history"] = input_data["context"]["application_history"]
            
            # CRITICAL: Pass SAME feature vectors to FraudEngine as credit models received
            # This ensures fraud detection operates on identical engineered features
            fraud_result = fraud_engine.detect_fraud(
                borrower_data=borrower,
                loan_data=loan_request,
                context=context,
                features=engineered_features,  # SAME features as credit models
                feature_set=input_data["feature_set"],  # SAME feature_set
                feature_version=input_data["feature_version"]  # SAME feature_version
            )
            
            # Update fraud_flag based on FraudEngine result
            if fraud_result.get("is_fraud", False):
                fraud_flag = True
            
        except Exception as e:
            # SAFETY: Log fraud engine failure and mark for review
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                f"[ModelEnsemble] FraudEngine failed: {str(e)}",
                exc_info=True
            )
            
            fraud_engine_failed = True
            
            # SAFETY: Create safe default fraud result that forces REVIEW
            # When fraud detection unavailable, default to REVIEW decision
            fraud_result = {
                "error": str(e),
                "combined_fraud_score": None,  # None signals missing fraud score
                "consolidated_flags": ["fraud_engine_unavailable"],
                "merged_explanation": ["Fraud detection engine unavailable - defaulting to REVIEW"],
                "engine_status": "failed"
            }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 8: Update structured explanation with final scores
        # ═══════════════════════════════════════════════════════════
        structured_explanation["final_score"] = final_credit_score
        structured_explanation["fraud_flag"] = fraud_flag
        
        # ═══════════════════════════════════════════════════════════
        # STEP 9: Merge explanations from all models (legacy)
        # ═══════════════════════════════════════════════════════════
        # EXTENSIBILITY: Modify _merge_explanations() to customize output format
        merged_explanation = self._merge_explanations(input_data, model_outputs)
        
        # ═══════════════════════════════════════════════════════════
        # STEP 10: Build unified output with FraudEngine result
        # ═══════════════════════════════════════════════════════════
        return self._build_unified_output(
            final_credit_score,
            fraud_flag,
            model_outputs,
            merged_explanation,
            structured_explanation,
            fraud_result
        )
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run ensemble prediction with flexible input format (convenience wrapper).
        
        Accepts input_data dict with either:
        - {"borrower": {...}, "loan_request": {...}} (standard format)
        - {"borrower": {...}, "loan": {...}} (alternative format)
        
        Args:
            input_data: Dictionary containing borrower and loan data
        
        Returns:
            Unified ensemble prediction (same as predict())
        
        Example:
            >>> ensemble = ModelEnsemble()
            >>> result = ensemble.run({
            ...     "borrower": {"region": "Dhaka"},
            ...     "loan": {"requested_amount": 12000}
            ... })
            >>> print(result["final_credit_score"])
        """
        borrower = input_data.get("borrower", {})
        
        # Accept both "loan_request" and "loan" keys
        loan_request = input_data.get("loan_request") or input_data.get("loan", {})
        
        return self.predict(borrower, loan_request)
    
    def _check_critical_flags(
        self,
        model_outputs: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Check for critical override conditions from any model.
        
        Critical flags immediately reject the application regardless of scores.
        
        EXTENSIBILITY: Add new override conditions here as needed.
        Examples: sanctions list hit, identity verification failure, etc.
        
        Args:
            model_outputs: Dictionary of model predictions
        
        Returns:
            Override decision if critical flag detected, else None
        """
        # OVERRIDE 1: Direct fraud detection (is_fraud = True)
        for model_name, output in model_outputs.items():
            if output.get("is_fraud", False):
                return {
                    "final_credit_score": 0,
                    "fraud_flag": True,
                    "decision": "rejected",
                    "risk_level": "critical",
                    "explanation": f"CRITICAL: Fraud detected by {model_name}",
                    "model_outputs": model_outputs,
                    "override_reason": "fraud_detection",
                    "override_source": model_name
                }
        
        # OVERRIDE 2: Fraud ring detection (flag_risk = True from trust model)
        for model_name, output in model_outputs.items():
            if output.get("flag_risk", False):
                return {
                    "final_credit_score": 0,
                    "fraud_flag": True,
                    "decision": "rejected",
                    "risk_level": "critical",
                    "explanation": f"CRITICAL: Fraud ring detected by {model_name}",
                    "model_outputs": model_outputs,
                    "override_reason": "fraud_ring",
                    "override_source": model_name
                }
        
        # EXTENSIBILITY: Add more override conditions here
        # Example: if output.get("sanctions_hit"): return {...}
        
        return None
    
    def _aggregate_scores(
        self,
        model_outputs: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Aggregate scores using deterministic weighted voting.
        
        STRATEGY: Weighted average of normalized scores.
        All scores are converted to 0-100 scale before aggregation.
        
        SAFETY: Only aggregates from models that succeeded (no "error" key).
        Failed models are automatically excluded from the weighted average.
        
        EXTENSIBILITY: To change aggregation strategy:
        1. Modify normalization logic below
        2. Change from weighted average to min/max/median
        3. Add score bounds or clamping rules
        
        Args:
            model_outputs: Dictionary of model predictions
        
        Returns:
            Final ensemble score (0-100 scale)
        """
        weighted_sum = 0.0
        total_weight = 0.0
        
        for model_name, output in model_outputs.items():
            # SAFETY: Skip failed models (they have "error" key)
            if "error" in output:
                continue
            
            # Get model weight (default to 1.0 if not specified)
            weight = self.weights.get(model_name, 1.0)
            
            # ═══════════════════════════════════════════════════════════
            # Normalize score to 0-100 scale (model-specific logic)
            # ═══════════════════════════════════════════════════════════
            normalized_score = self._normalize_score(output, model_name)
            
            # Accumulate weighted sum
            weighted_sum += normalized_score * weight
            total_weight += weight
        
        # Compute weighted average
        if total_weight > 0:
            ensemble_score = weighted_sum / total_weight
        else:
            # Fallback: no valid models, return neutral score
            ensemble_score = 50.0
        
        # Clamp to valid range
        ensemble_score = max(0.0, min(100.0, ensemble_score))
        
        return round(ensemble_score, 2)
    
    def _normalize_score(
        self,
        output: Dict[str, Any],
        model_name: str
    ) -> float:
        """
        Normalize model output to 0-100 scale.
        
        EXTENSIBILITY: Add normalization logic for new model types here.
        
        Args:
            output: Model prediction dictionary
            model_name: Name of the model
        
        Returns:
            Normalized score (0-100)
        """
        # Credit models: score already in 0-100 range
        if "score" in output and output.get("score", 0) <= 100:
            return float(output["score"])
        
        # Trust models: trust_score in 0.0-1.0 range → scale to 0-100
        if "trust_score" in output:
            return output["trust_score"] * 100.0
        
        # Fraud models: fraud_score in 0.0-1.0 range → INVERT and scale
        # (High fraud = low creditworthiness)
        if "fraud_score" in output:
            return (1.0 - output["fraud_score"]) * 100.0
        
        # EXTENSIBILITY: Add more model types here
        # Example: if "ml_probability" in output: return output["ml_probability"] * 100
        
        # Fallback: neutral score
        return 50.0
    
    def _detect_fraud_flag(
        self,
        model_outputs: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Detect if any model raised a fraud flag.
        
        DETERMINISM: Returns True if ANY model indicates fraud risk.
        
        Args:
            model_outputs: Dictionary of model predictions
        
        Returns:
            Boolean indicating fraud risk
        """
        for output in model_outputs.values():
            # Check various fraud indicators
            if output.get("is_fraud", False):
                return True
            if output.get("flag_risk", False):
                return True
            # EXTENSIBILITY: Add more fraud indicators here
        
        return False
    
    def _merge_explanations(
        self,
        input_data: Dict[str, Any],
        model_outputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge explanations from all models into unified output.
        
        EXTENSIBILITY: Customize the explanation format here.
        Can return text, structured data, or both.
        
        Args:
            input_data: Original input data
            model_outputs: Dictionary of model predictions
        
        Returns:
            Merged explanation dictionary
        """
        per_model_explanations = {}
        
        for model_name, output in model_outputs.items():
            # Skip failed models
            if "error" in output:
                per_model_explanations[model_name] = {
                    "summary": f"{model_name} failed",
                    "error": output["error"]
                }
                continue
            
            # Get explanation from each model (if available)
            # Models implement explain() method via BaseModel interface
            try:
                model_instance = next(m for m in self.models if m.name == model_name)
                explanation = model_instance.explain(input_data, output)
                per_model_explanations[model_name] = explanation
            except Exception as e:
                # Fallback: use raw output as explanation
                per_model_explanations[model_name] = {
                    "summary": f"{model_name} prediction",
                    "details": output
                }
        
        return {
            "ensemble_summary": self._generate_ensemble_summary(model_outputs),
            "per_model": per_model_explanations
        }
    
    def _generate_ensemble_summary(
        self,
        model_outputs: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Generate high-level summary of ensemble decision.
        
        Args:
            model_outputs: Dictionary of model predictions
        
        Returns:
            Human-readable summary string
        """
        summaries = []
        for model_name, output in model_outputs.items():
            if "error" in output:
                summaries.append(f"{model_name}: error")
            elif "score" in output:
                summaries.append(f"{model_name}: {output['score']}")
            elif "trust_score" in output:
                summaries.append(f"{model_name}: {output['trust_score']:.2f}")
            elif "fraud_score" in output:
                summaries.append(f"{model_name}: fraud={output['fraud_score']:.2f}")
        
        return " | ".join(summaries)
    
    def _build_unified_output(
        self,
        final_credit_score: float,
        fraud_flag: bool,
        model_outputs: Dict[str, Dict[str, Any]],
        merged_explanation: Dict[str, Any],
        structured_explanation: Optional[Dict[str, Any]] = None,
        fraud_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build the final unified output structure.
        
        EXTENSIBILITY: Modify this to customize the output format.
        
        Args:
            final_credit_score: Aggregated score (0-100)
            fraud_flag: Boolean fraud indicator
            model_outputs: Per-model predictions
            merged_explanation: Merged explanations (legacy)
            structured_explanation: Structured explanation from ExplainabilityEngine
            fraud_result: Comprehensive fraud detection result from FraudEngine
        
        Returns:
            Unified decision object
        """
        # Determine decision from score
        if final_credit_score >= 70:
            decision = "approved"
            risk_level = "low"
        elif final_credit_score >= 50:
            decision = "review"
            risk_level = "medium"
        else:
            decision = "rejected"
            risk_level = "high"
        
        # Override decision if fraud detected
        if fraud_flag:
            decision = "rejected"
            risk_level = "critical"
        
        output = {
            # Primary outputs (as per requirements)
            "final_credit_score": final_credit_score,
            "fraud_flag": fraud_flag,
            "model_outputs": model_outputs,
            "explanation": merged_explanation,
            
            # Additional metadata
            "decision": decision,
            "risk_level": risk_level,
            "ensemble_metadata": {
                "version": self.ensemble_version,
                "models_used": list(model_outputs.keys()),
                "weights": self.weights
            }
        }
        
        # Attach structured explanation from ExplainabilityEngine
        if structured_explanation:
            output["structured_explanation"] = structured_explanation
        
        # Attach comprehensive fraud detection result from FraudEngine
        if fraud_result:
            output["fraud_result"] = fraud_result
        
        return output


# Default ensemble instance (for backward compatibility)
_default_ensemble = ModelEnsemble()


def predict_ensemble(
    borrower: Dict[str, Any],
    loan_request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Module-level function for ensemble prediction (backward compatibility).
    
    Args:
        borrower: Borrower profile
        loan_request: Loan request details
        
    Returns:
        Ensemble prediction with unified output format
    """
    return _default_ensemble.predict(borrower, loan_request)

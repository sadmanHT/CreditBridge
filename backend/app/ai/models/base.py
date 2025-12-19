"""
Base Model Interface for CreditBridge AI Models

SYSTEM ROLE:
You are designing a production-grade AI model abstraction
for a fintech decision system.

PROJECT:
CreditBridge — Modular AI Core.

DESIGN PHILOSOPHY:
- Pure abstraction (no implementation logic)
- All models inherit from BaseModel
- Standardized predict() and explain() signatures
- Enables rule-based, ML-based, and graph-based models to coexist
- Version tracking for audit compliance
- Feature compatibility contracts for governance
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class FeatureCompatibilityError(Exception):
    """Raised when feature set or version is incompatible with model requirements"""
    pass


class BaseModel(ABC):
    """
    Abstract base class for all CreditBridge AI models.
    
    This class defines the contract that all AI models must implement,
    ensuring consistent behavior across different model types
    (rule-based, ML-based, graph-based).
    
    Design Principles:
    - Pure abstraction (no logic in base class)
    - Interoperability (all models have same interface)
    - Explainability (explain() is mandatory)
    - Auditability (name property for tracking)
    
    Usage:
        class MyModel(BaseModel):
            @property
            def name(self) -> str:
                return "MyCustomModel-v1.0"
            
            def predict(self, input_data: dict) -> dict:
                # Implementation here
                return {"score": 75, "decision": "approved"}
            
            def explain(self, input_data: dict, prediction: dict) -> dict:
                # Implementation here
                return {"factors": [...], "summary": "..."}
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the unique name and version of this model.
        
        This property is used for:
        - Audit logging
        - Model tracking in ensemble systems
        - A/B testing and model comparison
        - Regulatory compliance records
        
        Returns:
            str: Model name and version (e.g., "CreditRuleModel-v1.0")
        
        Example:
            >>> model = CreditRuleModel()
            >>> model.name
            'CreditRuleModel-v1.0'
        """
        pass
    
    @property
    @abstractmethod
    def required_feature_set(self) -> str:
        """
        Return the feature set name this model requires.
        
        This property enforces feature compatibility contracts:
        - Models declare which feature set they expect
        - Feature store validates compatibility before prediction
        - Enables safe model versioning and feature evolution
        
        Returns:
            str: Feature set name (e.g., "core_behavioral")
        
        Example:
            >>> model = CreditRuleModel()
            >>> model.required_feature_set
            'core_behavioral'
        """
        pass
    
    @property
    @abstractmethod
    def required_feature_version(self) -> str:
        """
        Return the feature version this model requires.
        
        This property ensures feature computation compatibility:
        - Models declare which feature version they expect
        - Prevents feeding incompatible features to models
        - Enables backward compatibility tracking
        
        Returns:
            str: Feature version (e.g., "v1")
        
        Example:
            >>> model = CreditRuleModel()
            >>> model.required_feature_version
            'v1'
        """
        pass
    
    @property
    @abstractmethod
    def required_feature_keys(self) -> List[str]:
        """
        Return the list of feature keys this model requires.
        
        This property declares the exact features this model needs:
        - Validates feature completeness before prediction
        - Documents model dependencies explicitly
        - Enables feature impact analysis
        
        Returns:
            List[str]: List of required feature keys
        
        Example:
            >>> model = CreditRuleModel()
            >>> model.required_feature_keys
            ['mobile_activity_score', 'transaction_volume_30d', 'activity_consistency']
        """
        pass
    
    def validate_features(
        self, 
        features: dict, 
        feature_set: str, 
        feature_version: str
    ) -> None:
        """
        Validate that provided features match model requirements.
        
        This method enforces feature compatibility contracts:
        - Checks feature_set matches required_feature_set
        - Checks feature_version matches required_feature_version
        - Validates all required feature keys are present
        
        Args:
            features (dict): Feature dictionary to validate
            feature_set (str): Feature set name from feature store
            feature_version (str): Feature version from feature store
        
        Raises:
            FeatureCompatibilityError: If feature_set or version mismatch
            ValueError: If required feature keys are missing
        
        Example:
            >>> model = CreditRuleModel()
            >>> features = {"mobile_activity_score": 72.0, ...}
            >>> model.validate_features(features, "core_behavioral", "v1")
            # Raises FeatureCompatibilityError if incompatible
        """
        # Validate feature set compatibility
        if feature_set != self.required_feature_set:
            raise FeatureCompatibilityError(
                f"{self.name} requires feature_set='{self.required_feature_set}', "
                f"but received feature_set='{feature_set}'"
            )
        
        # Validate feature version compatibility
        if feature_version != self.required_feature_version:
            raise FeatureCompatibilityError(
                f"{self.name} requires feature_version='{self.required_feature_version}', "
                f"but received feature_version='{feature_version}'"
            )
        
        # Validate required feature keys are present
        missing_keys = [key for key in self.required_feature_keys if key not in features]
        if missing_keys:
            raise ValueError(
                f"{self.name} requires features {self.required_feature_keys}, "
                f"but missing keys: {missing_keys}"
            )
    
    @abstractmethod
    def predict(self, input_data: dict) -> dict:
        """
        Generate a prediction from input data.
        
        This is the core method that all models must implement.
        It takes structured input data and returns a prediction
        with standardized output format.
        
        Args:
            input_data (dict): Input data for prediction, typically containing:
                - borrower: Borrower profile information
                - loan_request: Loan request details
                - context: Additional context (optional)
        
        Returns:
            dict: Prediction result containing:
                - score: Numeric score (float or int, scale depends on model)
                - decision: Decision string (e.g., "approved", "rejected", "review")
                - confidence: Confidence level (0.0-1.0)
                - metadata: Model metadata (name, version, timestamp)
        
        Raises:
            ValueError: If input_data is invalid or missing required fields
            RuntimeError: If model prediction fails
        
        Example:
            >>> model = CreditRuleModel()
            >>> input_data = {
            ...     "borrower": {"region": "Dhaka", "gender": "female"},
            ...     "loan_request": {"requested_amount": 15000}
            ... }
            >>> prediction = model.predict(input_data)
            >>> print(prediction["score"])
            65
        """
        pass
    
    @abstractmethod
    def explain(self, input_data: dict, prediction: dict) -> dict:
        """
        Generate human-readable explanation for a prediction.
        
        This method provides transparency and explainability for AI decisions,
        which is critical for:
        - Regulatory compliance
        - User trust
        - Debugging and model improvement
        - Fairness audits
        
        Args:
            input_data (dict): Original input data used for prediction
            prediction (dict): Prediction output from predict() method
        
        Returns:
            dict: Explanation containing:
                - summary: Short natural language summary
                - factors: List of factors that influenced the decision
                - details: Detailed breakdown (optional)
                - recommendations: Actionable recommendations (optional)
        
        Example:
            >>> model = CreditRuleModel()
            >>> input_data = {"borrower": {...}, "loan_request": {...}}
            >>> prediction = model.predict(input_data)
            >>> explanation = model.explain(input_data, prediction)
            >>> print(explanation["summary"])
            'Loan approved with medium confidence based on 3 factors'
        """
        pass

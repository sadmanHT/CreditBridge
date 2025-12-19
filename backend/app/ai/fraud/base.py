"""
Base Fraud Detection Interface

SYSTEM ROLE:
Production-grade fraud detection interface for fintech AI platform.

PROJECT:
CreditBridge — Fraud Detection Engine.

REQUIREMENTS:
- Abstract class FraudDetector
- Required methods: name (property), evaluate(input_data: dict) -> dict
- Feature-driven: Fraud detectors consume feature vectors only
- Output format: {"fraud_score": float, "flags": list[str], "explanation": list[str]}
- No implementation logic

Design Principles:
- Strategy pattern for different detection methods
- Consistent interface across all detectors
- Feature-driven architecture (no raw data access)
- Extensible for ML-based fraud detection
- Production-ready with comprehensive type hints
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


class FeatureCompatibilityError(Exception):
    """Raised when feature set or version is incompatible with fraud detector requirements"""
    pass


class FraudDetector(ABC):
    """
    Abstract base class for fraud detection strategies.
    
    SYSTEM ROLE:
    Production-grade feature-driven fraud detection interface for fintech AI platform.
    
    FUNCTIONAL REQUIREMENT:
    All fraud detectors must consume ONLY engineered features, not raw data.
    
    All fraud detectors must implement:
    - name: Property returning detector name
    - required_feature_set: Property declaring required feature set
    - required_feature_version: Property declaring required feature version
    - required_feature_keys: Property declaring required feature keys
    - evaluate(): Primary fraud detection method (feature-driven)
    
    Output Format (Required):
    {
        "fraud_score": float,     # 0.0–1.0
        "flags": list[str],       # List of fraud flags
        "explanation": list[str]  # Human-readable explanations
    }
    
    Design Pattern: Strategy Pattern
    Extensibility: New detectors can be added by extending this class
    Feature Governance: All detectors declare their feature dependencies
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get detector name for identification.
        
        Returns:
            str: Unique detector name
        
        Example:
            "VelocityFraudDetector-v1.0"
        """
        pass
    
    @property
    @abstractmethod
    def required_feature_set(self) -> str:
        """
        Return the feature set name this fraud detector requires.
        
        This property enforces feature compatibility contracts:
        - Detectors declare which feature set they expect
        - Feature store validates compatibility before evaluation
        - Enables safe detector versioning and feature evolution
        
        Returns:
            str: Feature set name (e.g., "fraud_behavioral")
        
        Example:
            >>> detector = VelocityFraudDetector()
            >>> detector.required_feature_set
            'fraud_behavioral'
        """
        pass
    
    @property
    @abstractmethod
    def required_feature_version(self) -> str:
        """
        Return the feature version this fraud detector requires.
        
        This property ensures feature computation compatibility:
        - Detectors declare which feature version they expect
        - Prevents feeding incompatible features to detectors
        - Enables backward compatibility tracking
        
        Returns:
            str: Feature version (e.g., "v1")
        
        Example:
            >>> detector = VelocityFraudDetector()
            >>> detector.required_feature_version
            'v1'
        """
        pass
    
    @property
    @abstractmethod
    def required_feature_keys(self) -> List[str]:
        """
        Return the list of feature keys this fraud detector requires.
        
        This property declares the exact features this detector needs:
        - Validates feature completeness before evaluation
        - Documents detector dependencies explicitly
        - Enables feature impact analysis
        
        Returns:
            List[str]: List of required feature keys
        
        Example:
            >>> detector = VelocityFraudDetector()
            >>> detector.required_feature_keys
            ['application_velocity_1h', 'ip_change_frequency', 'device_switch_count']
        """
        pass
    
    def validate_features(
        self, 
        features: dict, 
        feature_set: str, 
        feature_version: str
    ) -> None:
        """
        Validate that provided features match detector requirements.
        
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
            >>> detector = VelocityFraudDetector()
            >>> features = {"application_velocity_1h": 5, ...}
            >>> detector.validate_features(features, "fraud_behavioral", "v1")
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
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate fraud risk based on engineered features.
        
        FUNCTIONAL REQUIREMENT: Operates ONLY on engineered features.
        
        REQUIRED INPUT FORMAT:
        {
            "features": dict,           # Engineered feature vectors
            "feature_set": str,         # Feature set name (for validation)
            "feature_version": str      # Feature version (for validation)
        }
        
        REQUIRED OUTPUT FORMAT:
        {
            "fraud_score": float,     # 0.0–1.0 (fraud probability)
            "flags": list[str],       # Detected fraud flags
            "explanation": list[str]  # Human-readable explanations
        }
        
        Args:
            input_data: Dictionary containing:
                - "features": Engineered features (dict)
                - "feature_set": Feature set name (str)
                - "feature_version": Feature version (str)
        
        Returns:
            Dict with fraud_score, flags, and explanation
        
        Raises:
            FeatureCompatibilityError: If features are incompatible
            ValueError: If input data is invalid
        
        Example:
            >>> detector = VelocityFraudDetector()
            >>> result = detector.evaluate({
            ...     "features": {
            ...         "application_velocity_1h": 5,
            ...         "ip_change_frequency": 3,
            ...         "device_switch_count": 2
            ...     },
            ...     "feature_set": "fraud_behavioral",
            ...     "feature_version": "v1"
            ... })
            >>> print(result)
            {
                "fraud_score": 0.75,
                "flags": ["high_velocity", "suspicious_ip_pattern"],
                "explanation": [
                    "5 applications in last hour exceeds threshold of 3",
                    "Multiple IP changes detected within short timeframe"
                ]
            }
        """
        pass


# ═══════════════════════════════════════════════════════════════════════
# Legacy Support: BaseFraudDetector and FraudDetectionResult
# ═══════════════════════════════════════════════════════════════════════
# These classes are maintained for backward compatibility with existing code.
# New code should use FraudDetector abstract class defined above.


@dataclass
class FraudDetectionResult:
    """
    Standardized fraud detection result (Legacy).
    
    NOTE: This class is maintained for backward compatibility.
    New code should use the dict format from FraudDetector.evaluate().
    
    Attributes:
        is_fraud: Boolean indicating fraud detection
        fraud_score: Fraud probability (0.0-1.0)
        risk_level: Risk classification (low, medium, high, critical)
        fraud_indicators: List of detected fraud indicators
        confidence: Detection confidence (0.0-1.0)
        detector_name: Name of detector that produced result
        details: Additional detector-specific details
        timestamp: Detection timestamp
    """
    is_fraud: bool
    fraud_score: float
    risk_level: str
    fraud_indicators: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    detector_name: str = "unknown"
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        
        # Validate fraud_score range
        if not 0.0 <= self.fraud_score <= 1.0:
            raise ValueError(f"fraud_score must be in [0.0, 1.0], got {self.fraud_score}")
        
        # Validate confidence range
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")
        
        # Validate risk_level
        valid_risk_levels = ["low", "medium", "high", "critical"]
        if self.risk_level not in valid_risk_levels:
            raise ValueError(f"risk_level must be one of {valid_risk_levels}, got {self.risk_level}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_fraud": self.is_fraud,
            "fraud_score": self.fraud_score,
            "risk_level": self.risk_level,
            "fraud_indicators": self.fraud_indicators,
            "confidence": self.confidence,
            "detector_name": self.detector_name,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class BaseFraudDetector(ABC):
    """
    Abstract base class for fraud detection strategies (Legacy).
    
    NOTE: This class is maintained for backward compatibility.
    New code should extend FraudDetector abstract class defined above.
    
    All fraud detectors must implement:
    - detect(): Primary fraud detection method
    - get_name(): Detector identification
    
    Design Pattern: Strategy Pattern
    Extensibility: New detectors can be added by extending this class
    """
    
    @abstractmethod
    def detect(
        self,
        borrower_data: Dict[str, Any],
        loan_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> FraudDetectionResult:
        """
        Detect fraud based on borrower and loan data.
        
        Args:
            borrower_data: Borrower profile information
            loan_data: Loan request information
            context: Optional additional context (e.g., historical data)
        
        Returns:
            FraudDetectionResult: Standardized detection result
        
        Raises:
            ValueError: If input data is invalid
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get detector name for identification.
        
        Returns:
            str: Unique detector name
        """
        pass
    
    def validate_input(
        self,
        borrower_data: Dict[str, Any],
        loan_data: Dict[str, Any]
    ) -> None:
        """
        Validate input data format.
        
        Args:
            borrower_data: Borrower profile information
            loan_data: Loan request information
        
        Raises:
            ValueError: If input data is invalid
        """
        if not isinstance(borrower_data, dict):
            raise ValueError("borrower_data must be a dictionary")
        
        if not isinstance(loan_data, dict):
            raise ValueError("loan_data must be a dictionary")
        
        # Add more validation as needed
        if not borrower_data:
            raise ValueError("borrower_data cannot be empty")
        
        if not loan_data:
            raise ValueError("loan_data cannot be empty")
    
    def calculate_risk_level(self, fraud_score: float) -> str:
        """
        Calculate risk level from fraud score.
        
        Args:
            fraud_score: Fraud probability (0.0-1.0)
        
        Returns:
            str: Risk level classification
        """
        if fraud_score >= 0.8:
            return "critical"
        elif fraud_score >= 0.6:
            return "high"
        elif fraud_score >= 0.3:
            return "medium"
        else:
            return "low"

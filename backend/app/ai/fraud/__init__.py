"""
Fraud Detection Module for CreditBridge

Comprehensive fraud detection system with multiple detection strategies.

Architecture:
- FraudDetector: Production-grade abstract interface (primary)
- BaseFraudDetector: Legacy abstract interface (backward compatibility)
- RuleEngine: Rule-based fraud detection
- TrustGraphAdapter: Graph-based fraud detection via trust network
- FraudEngine: Central orchestration for fraud detection

Usage (New):
    from app.ai.fraud import FraudDetector
    
    class MyDetector(FraudDetector):
        @property
        def name(self) -> str:
            return "MyDetector-v1.0"
        
        def evaluate(self, input_data: dict) -> dict:
            return {
                "fraud_score": 0.5,
                "flags": ["flag1"],
                "explanation": ["Explanation"]
            }

Usage (Legacy):
    from app.ai.fraud import get_fraud_engine
    
    engine = get_fraud_engine()
    result = engine.detect_fraud(borrower_data, loan_data)
"""

from .base import FraudDetector, BaseFraudDetector, FraudDetectionResult
from .rule_engine import RuleBasedFraudDetector
from .trustgraph_adapter import TrustGraphFraudDetector
from .engine import FraudEngine, get_fraud_engine

__all__ = [
    # Primary interface (production-grade)
    "FraudDetector",
    
    # Legacy interfaces (backward compatibility)
    "BaseFraudDetector",
    "FraudDetectionResult",
    
    # Concrete implementations
    "RuleBasedFraudDetector",
    "TrustGraphFraudDetector",
    
    # Engine
    "FraudEngine",
    "get_fraud_engine"
]

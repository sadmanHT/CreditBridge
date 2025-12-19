"""
Test: Fraud Detector Feature Compatibility
Validates that FraudDetector base class enforces feature-driven architecture.
"""
from typing import Dict, Any, List
from app.ai.fraud.base import FraudDetector, FeatureCompatibilityError


class MockFraudDetector(FraudDetector):
    """Mock fraud detector for testing feature compatibility."""
    
    @property
    def name(self) -> str:
        return "MockFraudDetector-v1.0"
    
    @property
    def required_feature_set(self) -> str:
        return "fraud_behavioral"
    
    @property
    def required_feature_version(self) -> str:
        return "v1"
    
    @property
    def required_feature_keys(self) -> List[str]:
        return ["application_velocity_1h", "ip_change_frequency", "device_switch_count"]
    
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate fraud using features."""
        features = input_data.get("features", {})
        feature_set = input_data.get("feature_set", "fraud_behavioral")
        feature_version = input_data.get("feature_version", "v1")
        
        # Validate feature compatibility
        self.validate_features(features, feature_set, feature_version)
        
        # Mock fraud evaluation
        fraud_score = 0.5 + (features.get("application_velocity_1h", 0) * 0.05)
        flags = []
        explanation = []
        
        if features.get("application_velocity_1h", 0) >= 3:
            flags.append("high_velocity")
            explanation.append(f"Application velocity of {features['application_velocity_1h']} exceeds threshold")
        
        return {
            "fraud_score": min(1.0, fraud_score),
            "flags": flags,
            "explanation": explanation
        }


print("=== Test 1: Valid Features ===")
try:
    detector = MockFraudDetector()
    result = detector.evaluate({
        "features": {
            "application_velocity_1h": 2,
            "ip_change_frequency": 1,
            "device_switch_count": 0
        },
        "feature_set": "fraud_behavioral",
        "feature_version": "v1"
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 2: Invalid Feature Set ===")
try:
    detector = MockFraudDetector()
    result = detector.evaluate({
        "features": {
            "application_velocity_1h": 2,
            "ip_change_frequency": 1,
            "device_switch_count": 0
        },
        "feature_set": "wrong_set",
        "feature_version": "v1"
    })
    print(f"✗ Test FAILED: Expected error but evaluation succeeded")
except FeatureCompatibilityError as e:
    print(f"✓ Correctly rejected incompatible feature set")
    print(f"  ERROR: {e}")

print("\n=== Test 3: Invalid Feature Version ===")
try:
    detector = MockFraudDetector()
    result = detector.evaluate({
        "features": {
            "application_velocity_1h": 2,
            "ip_change_frequency": 1,
            "device_switch_count": 0
        },
        "feature_set": "fraud_behavioral",
        "feature_version": "v2"
    })
    print(f"✗ Test FAILED: Expected error but evaluation succeeded")
except FeatureCompatibilityError as e:
    print(f"✓ Correctly rejected incompatible feature version")
    print(f"  ERROR: {e}")

print("\n=== Test 4: Missing Required Features ===")
try:
    detector = MockFraudDetector()
    result = detector.evaluate({
        "features": {
            "application_velocity_1h": 2
            # Missing ip_change_frequency and device_switch_count
        },
        "feature_set": "fraud_behavioral",
        "feature_version": "v1"
    })
    print(f"✗ Test FAILED: Expected error but evaluation succeeded")
except ValueError as e:
    print(f"✓ Correctly rejected missing features")
    print(f"  ERROR: {e}")

print("\n=== All Fraud Detector Feature Compatibility Tests Complete ===")

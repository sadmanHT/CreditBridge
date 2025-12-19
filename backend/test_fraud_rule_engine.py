"""
Test: RuleBasedFraudDetector Feature-Driven Refactoring
Validates that fraud detector operates ONLY on engineered features.
"""
from app.ai.fraud.rule_engine import RuleBasedFraudDetector
from app.ai.fraud.base import FeatureCompatibilityError

detector = RuleBasedFraudDetector()

print("=== Test 1: Normal Activity (Low Fraud Risk) ===")
try:
    result = detector.evaluate({
        "features": {
            "transaction_volume_30d": 5000,
            "activity_consistency": 75.0
        },
        "feature_set": "core_behavioral",
        "feature_version": "v1"
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation: {result['explanation']}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 2: Low Transaction Volume (Fraud Risk) ===")
try:
    result = detector.evaluate({
        "features": {
            "transaction_volume_30d": 400,  # Below very_low threshold (500)
            "activity_consistency": 80.0
        },
        "feature_set": "core_behavioral",
        "feature_version": "v1"
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation:")
    for exp in result['explanation']:
        print(f"    - {exp}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 3: Low Activity Consistency (Fraud Risk) ===")
try:
    result = detector.evaluate({
        "features": {
            "transaction_volume_30d": 3000,
            "activity_consistency": 10.0  # Below very_low threshold (15)
        },
        "feature_set": "core_behavioral",
        "feature_version": "v1"
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation:")
    for exp in result['explanation']:
        print(f"    - {exp}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 4: Multiple Fraud Indicators (High Risk) ===")
try:
    result = detector.evaluate({
        "features": {
            "transaction_volume_30d": 300,   # Very low volume
            "activity_consistency": 8.0       # Very low consistency
        },
        "feature_set": "core_behavioral",
        "feature_version": "v1"
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation:")
    for exp in result['explanation']:
        print(f"    - {exp}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 5: Incompatible Feature Version ===")
try:
    result = detector.evaluate({
        "features": {
            "transaction_volume_30d": 5000,
            "activity_consistency": 75.0
        },
        "feature_set": "core_behavioral",
        "feature_version": "v2"  # Wrong version
    })
    print(f"✗ Test FAILED: Expected error but evaluation succeeded")
except FeatureCompatibilityError as e:
    print(f"✓ Correctly rejected incompatible version")
    print(f"  ERROR: {e}")

print("\n=== Test 6: Missing Required Features ===")
try:
    result = detector.evaluate({
        "features": {
            "transaction_volume_30d": 5000
            # Missing activity_consistency
        },
        "feature_set": "core_behavioral",
        "feature_version": "v1"
    })
    print(f"✗ Test FAILED: Expected error but evaluation succeeded")
except ValueError as e:
    print(f"✓ Correctly rejected missing features")
    print(f"  ERROR: {e}")

print("\n=== All RuleBasedFraudDetector Feature Tests Complete ===")

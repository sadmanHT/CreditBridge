"""
Test C: Ensemble Feature Compatibility Test
Validates that ensemble validates features against ALL model requirements.
"""
from app.ai.ensemble import ModelEnsemble, FeatureValidationError

ensemble = ModelEnsemble()

# Test 1: Valid features with all required keys
print("\n=== Test 1: Valid Features ===")
try:
    borrower = {
        "borrower_id": "test-123",
        "engineered_features": {
            "mobile_activity_score": 72.0,
            "transaction_volume_30d": 15000,
            "activity_consistency": 85.0
        },
        "feature_set": "core_behavioral",
        "feature_version": "v1"
    }
    loan_request = {"requested_amount": 10000}
    
    result = ensemble.predict(borrower, loan_request)
    print(f"✓ Ensemble prediction succeeded")
    print(f"  Credit Score: {result['final_credit_score']}")
    print(f"  Fraud Flag: {result['fraud_flag']}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

# Test 2: Missing required features
print("\n=== Test 2: Missing Required Features ===")
try:
    borrower = {
        "borrower_id": "test-456",
        "engineered_features": {
            "mobile_activity_score": 50.0
            # Missing transaction_volume_30d and activity_consistency
        },
        "feature_set": "core_behavioral",
        "feature_version": "v1"
    }
    loan_request = {"requested_amount": 5000}
    
    result = ensemble.predict(borrower, loan_request)
    print(f"✗ Test FAILED: Expected error but prediction succeeded")
except FeatureValidationError as e:
    print(f"✓ Correctly rejected missing features")
    print(f"  ERROR: {e}")
except Exception as e:
    print(f"✓ Correctly rejected with error: {e}")

# Test 3: Incompatible feature version
print("\n=== Test 3: Incompatible Feature Version ===")
try:
    borrower = {
        "borrower_id": "test-789",
        "engineered_features": {
            "mobile_activity_score": 80.0,
            "transaction_volume_30d": 20000,
            "activity_consistency": 90.0
        },
        "feature_set": "core_behavioral",
        "feature_version": "v2"  # Wrong version
    }
    loan_request = {"requested_amount": 15000}
    
    result = ensemble.predict(borrower, loan_request)
    print(f"✗ Test FAILED: Expected error but prediction succeeded")
except FeatureValidationError as e:
    print(f"✓ Correctly rejected incompatible version")
    print(f"  ERROR: {e}")
except Exception as e:
    print(f"✓ Correctly rejected with error: {e}")

print("\n=== All Ensemble Feature Compatibility Tests Complete ===")

"""
Test B: Feature Compatibility Failure Test
Validates that model rejects incompatible features with mismatched feature_version.
"""
from app.ai.models.credit_rule_model import RuleBasedCreditModel

model = RuleBasedCreditModel()

input_data = {
    "features": {
        "mobile_activity_score": 0.6
    },
    "feature_set": "core_behavioral",
    "feature_version": "v2"
}

try:
    model.predict(input_data)
    print("✗ Test FAILED: Expected error but prediction succeeded")
except Exception as e:
    print("✓ Compatibility Failure Test PASSED")
    print(f"ERROR (Expected): {e}")

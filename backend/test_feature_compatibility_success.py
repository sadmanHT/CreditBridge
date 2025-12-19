"""
Test A: Feature Compatibility Success Test
Validates that model accepts compatible features with correct feature_set and feature_version.
"""
from app.ai.models.credit_rule_model import RuleBasedCreditModel

model = RuleBasedCreditModel()

input_data = {
    "features": {
        "mobile_activity_score": 0.6,
        "transaction_volume_30d": 10000,
        "activity_consistency": 0.9
    },
    "feature_set": "core_behavioral",
    "feature_version": "v1"
}

result = model.predict(input_data)
print("✓ Compatibility Success Test PASSED")
print(f"Result: {result}")

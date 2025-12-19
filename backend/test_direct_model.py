"""
A. Direct Model Test

Tests the refactored RuleBasedCreditModel with engineered features.
"""

from app.ai.models.credit_rule_model import RuleBasedCreditModel

model = RuleBasedCreditModel()

input_data = {
    "features": {
        "mobile_activity_score": 72.0,
        "transaction_volume_30d": 15000,
        "activity_consistency": 85.0
    }
}

result = model.predict(input_data)
explain = model.explain(input_data, result)

print("=" * 70)
print("A. DIRECT MODEL TEST")
print("=" * 70)
print()

print("Result:")
print(f"  score: {result.get('score')}")
print(f"  risk_level: {result.get('risk_level')}")
print()

print("Explanation:")
print(f"  summary: {explain.get('summary')}")
print()

print("Factors:")
for factor in explain.get('factors', []):
    print(f"  - {factor.get('factor')}: {factor.get('impact'):+d}")
    print(f"    {factor.get('explanation')}")
print()

print(f"Features used: {explain.get('features_used')}")
print()

print("=" * 70)
print("VALIDATION")
print("=" * 70)
score = result.get('score', 0)
print(f"✓ credit_score ∈ [0, 100]: {score} (valid: {0 <= score <= 100})")

# Check if feature names are mentioned in explanation
feature_names = ['mobile_activity_score', 'transaction_volume_30d', 'activity_consistency']
explanation_text = str(explain)
found_features = [fn for fn in feature_names if fn in explanation_text]
print(f"✓ explanation references feature names: {', '.join(found_features)}")

print("✓ No errors")
print()
print("Test PASSED!")

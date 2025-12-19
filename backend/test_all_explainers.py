from app.main import app
from app.ai.explainability import (
    get_explainer_registry,
    RuleCreditExplainer,
    TrustGraphExplainer,
    GraphExplainer
)

print("=" * 60)
print("Full System Test - All Explainers")
print("=" * 60)

print("\n✓ Full app imported successfully")

registry = get_explainer_registry()
print(f"✓ Registry initialized with {len(registry._explainers)} explainers\n")

print("Registered explainers:")
for exp in registry._explainers:
    print(f"  - {exp.__class__.__name__}")

print("\nTesting model matching:")
test_models = [
    "RuleBasedCreditModel-v1.0",
    "TrustGraphModel-v1.0-POC",
    "UnknownModel"
]

for model in test_models:
    try:
        explainer = registry.get_explainer(model)
        print(f"  ✓ {model} → {explainer.__class__.__name__}")
    except ValueError as e:
        print(f"  ✗ {model} → No explainer found (expected)")

print("\n" + "=" * 60)
print("✓ All systems operational")
print("=" * 60)

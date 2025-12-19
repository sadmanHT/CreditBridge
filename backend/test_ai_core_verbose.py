from app.ai.registry import get_ensemble

ensemble = get_ensemble()

input_data = {
    "borrower": {"gender": "female", "region": "Dhaka"},
    "loan": {"requested_amount": 12000}
}

result = ensemble.run(input_data)

print("="*70)
print("LOCAL AI CORE TEST")
print("="*70)
print("\n✅ No exceptions raised")
print("\n✅ Output contains required keys:")
print(f"   - final_credit_score: {result['final_credit_score']}")
print(f"   - model_outputs: {list(result['model_outputs'].keys())}")
print(f"   - explanation: {result['explanation']['ensemble_summary']}")
print("\n✅ All expected keys present:")
for key in ['final_credit_score', 'model_outputs', 'explanation']:
    print(f"   ✓ {key}")
print("\nFull output keys:", list(result.keys()))
print("\n" + "="*70)
print("✅ TEST PASSED")
print("="*70)

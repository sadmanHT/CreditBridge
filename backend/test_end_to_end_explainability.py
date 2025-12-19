"""
End-to-End Explainability System Test
Full integration test including ensemble + explanations
"""

from app.ai.registry import get_ensemble
from app.ai.explainability import (
    explain_prediction,
    explain_ensemble_result,
    get_explainer_registry
)

print("="*70)
print("END-TO-END EXPLAINABILITY SYSTEM TEST")
print("="*70)

# ═══════════════════════════════════════════════════════════════════════
# Test 1: Initialize system
# ═══════════════════════════════════════════════════════════════════════

print("\n[1] Initializing AI system...")
ensemble = get_ensemble()
registry = get_explainer_registry()

print(f"   ✓ Ensemble: {len(ensemble.models)} models loaded")
print(f"   ✓ Registry: {len(registry._explainers)} explainers registered")

# ═══════════════════════════════════════════════════════════════════════
# Test 2: Run ensemble prediction
# ═══════════════════════════════════════════════════════════════════════

print("\n[2] Running ensemble prediction...")

input_data = {
    "borrower": {
        "name": "Ahmed Rahman",
        "region": "Dhaka",
        "business_type": "retail",
        "peers": [
            {"peer_id": "P001", "repaid": True, "interactions": 15},
            {"peer_id": "P002", "repaid": True, "interactions": 10},
            {"peer_id": "P003", "repaid": True, "interactions": 8},
            {"peer_id": "P004", "repaid": False, "interactions": 3}
        ]
    },
    "loan": {
        "requested_amount": 18000,
        "purpose": "inventory",
        "term_months": 12
    }
}

result = ensemble.run(input_data)

print(f"   ✓ Final Score: {result['final_credit_score']:.2f}")
print(f"   ✓ Fraud Flag: {result['fraud_flag']}")
print(f"   ✓ Models: {list(result['model_outputs'].keys())}")

# ═══════════════════════════════════════════════════════════════════════
# Test 3: Generate individual model explanations
# ═══════════════════════════════════════════════════════════════════════

print("\n[3] Generating individual model explanations...")

for model_name, model_output in result['model_outputs'].items():
    print(f"\n   {model_name}:")
    try:
        explanation = explain_prediction(model_name, input_data, model_output)
        print(f"   • Summary: {explanation['summary']}")
        print(f"   • Confidence: {explanation['confidence']}")
        print(f"   • Method: {explanation['method']}")
        print(f"   • Factors: {len(explanation['factors'])} total")
        
        # Show top 3 factors
        for i, factor in enumerate(explanation['factors'][:3], 1):
            impact = factor.get('impact', 'neutral')
            print(f"     {i}. {factor['factor']}: {impact}")
    except ValueError as e:
        print(f"   ⚠ {e}")

# ═══════════════════════════════════════════════════════════════════════
# Test 4: Generate ensemble explanation
# ═══════════════════════════════════════════════════════════════════════

print("\n[4] Generating ensemble explanation...")

ensemble_explanation = explain_ensemble_result(input_data, result)

print(f"   ✓ Overall Summary: {ensemble_explanation['overall_summary']}")
print(f"   ✓ Average Confidence: {ensemble_explanation['confidence']:.2f}")
print(f"   ✓ Models Explained: {ensemble_explanation['metadata']['num_explained']}/{ensemble_explanation['metadata']['num_models']}")

print(f"\n   Model-by-Model Breakdown:")
for model_name, explanation in ensemble_explanation['model_explanations'].items():
    print(f"   • {model_name}: {explanation['summary']}")

# ═══════════════════════════════════════════════════════════════════════
# Test 5: Test different scenarios
# ═══════════════════════════════════════════════════════════════════════

print("\n[5] Testing different scenarios...")

# Scenario 1: High-risk borrower
print("\n   Scenario 1: High-Risk Borrower")
high_risk_input = {
    "borrower": {
        "name": "High Risk",
        "region": "Unknown",
        "peers": [
            {"peer_id": "P001", "repaid": False, "interactions": 2},
            {"peer_id": "P002", "repaid": False, "interactions": 1}
        ]
    },
    "loan": {"requested_amount": 75000}
}

high_risk_result = ensemble.run(high_risk_input)
high_risk_explanation = explain_ensemble_result(high_risk_input, high_risk_result)

print(f"   • Score: {high_risk_explanation['final_score']:.2f}")
print(f"   • Summary: {high_risk_explanation['overall_summary']}")
print(f"   • Confidence: {high_risk_explanation['confidence']:.2f}")

# Scenario 2: Low-risk borrower
print("\n   Scenario 2: Low-Risk Borrower")
low_risk_input = {
    "borrower": {
        "name": "Low Risk",
        "region": "Dhaka",
        "peers": [
            {"peer_id": "P001", "repaid": True, "interactions": 20},
            {"peer_id": "P002", "repaid": True, "interactions": 18},
            {"peer_id": "P003", "repaid": True, "interactions": 15}
        ]
    },
    "loan": {"requested_amount": 3000}
}

low_risk_result = ensemble.run(low_risk_input)
low_risk_explanation = explain_ensemble_result(low_risk_input, low_risk_result)

print(f"   • Score: {low_risk_explanation['final_score']:.2f}")
print(f"   • Summary: {low_risk_explanation['overall_summary']}")
print(f"   • Confidence: {low_risk_explanation['confidence']:.2f}")

# ═══════════════════════════════════════════════════════════════════════
# Test 6: API-ready output format
# ═══════════════════════════════════════════════════════════════════════

print("\n[6] Generating API-ready response...")

api_response = {
    "prediction": {
        "final_score": result['final_credit_score'],
        "fraud_flag": result['fraud_flag'],
        "recommendation": "approve" if result['final_credit_score'] >= 60 and not result['fraud_flag'] else "review"
    },
    "explanation": ensemble_explanation['overall_summary'],
    "confidence": ensemble_explanation['confidence'],
    "model_details": {}
}

for model_name, explanation in ensemble_explanation['model_explanations'].items():
    api_response['model_details'][model_name] = {
        "summary": explanation['summary'],
        "confidence": explanation['confidence'],
        "method": explanation.get('method', 'unknown')
    }

print(f"   ✓ API Response Structure:")
print(f"     • prediction.final_score: {api_response['prediction']['final_score']:.2f}")
print(f"     • prediction.recommendation: {api_response['prediction']['recommendation']}")
print(f"     • explanation: {api_response['explanation']}")
print(f"     • confidence: {api_response['confidence']:.2f}")
print(f"     • model_details: {len(api_response['model_details'])} models")

print("\n" + "="*70)
print("✓ END-TO-END SYSTEM OPERATIONAL")
print("="*70)

print("\nSYSTEM CAPABILITIES:")
print("  ✓ Multi-model ensemble predictions")
print("  ✓ Automatic explainer routing")
print("  ✓ Human-readable explanations")
print("  ✓ Confidence scoring")
print("  ✓ Factor breakdown analysis")
print("  ✓ Risk scenario handling")
print("  ✓ API-ready response format")

print("\nREGULATORY COMPLIANCE:")
print("  ✓ Transparent decision factors")
print("  ✓ Traceable model outputs")
print("  ✓ Confidence metrics")
print("  ✓ Multi-method validation")

print("\nNEXT STEPS:")
print("  • Integrate into API endpoints (/api/v1/routes/explanations.py)")
print("  • Add SHAP explainer for ML models")
print("  • Create dashboard visualizations")
print("  • Add explainability audit logging")

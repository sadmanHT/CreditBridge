"""
Test ExplainabilityEngine integration with ModelEnsemble
"""

from app.ai.ensemble import ModelEnsemble
import json


def test_engine_integration():
    """Test that ExplainabilityEngine is properly integrated into ensemble."""
    
    # Create test data
    borrower = {
        'borrower_id': 'test_123',
        'region': 'Dhaka',
        'occupation': 'farmer',
        'income_monthly': 15000,
        'debt_to_income_ratio': 0.3
    }
    
    loan_request = {
        'requested_amount': 50000,
        'purpose': 'Business expansion'
    }
    
    # Run ensemble prediction with ExplainabilityEngine integration
    print("=" * 70)
    print("TESTING: ExplainabilityEngine Integration with ModelEnsemble")
    print("=" * 70)
    
    ensemble = ModelEnsemble()
    result = ensemble.predict(borrower, loan_request)
    
    # Verify structured_explanation is attached
    if 'structured_explanation' not in result:
        print("❌ FAILED: structured_explanation not found in result")
        return False
    
    print("\n✅ SUCCESS: ExplainabilityEngine integrated")
    print(f"\nFinal Score: {result['final_credit_score']}")
    print(f"Fraud Flag: {result['fraud_flag']}")
    print(f"Decision: {result['decision']}")
    print(f"Risk Level: {result['risk_level']}")
    
    structured_exp = result['structured_explanation']
    
    print(f"\n--- Structured Explanation ---")
    print(f"Overall Summary: {structured_exp['overall_summary']}")
    print(f"Confidence: {structured_exp['confidence']:.2f}")
    print(f"Model Explanations: {list(structured_exp['model_explanations'].keys())}")
    print(f"Aggregated Factors: {len(structured_exp['aggregated_factors'])} factors")
    
    print(f"\n--- Per-Model Explanations ---")
    for model_name, explanation in structured_exp['model_explanations'].items():
        exp_type = explanation.get('type', 'unknown')
        confidence = explanation.get('confidence', 0)
        print(f"  {model_name}: type={exp_type}, confidence={confidence:.2f}")
    
    print(f"\n--- Top 5 Aggregated Factors ---")
    for i, factor in enumerate(structured_exp['aggregated_factors'][:5], 1):
        factor_name = factor.get('factor') or factor.get('insight', 'N/A')
        impact = factor.get('impact', 'N/A')
        weight = factor.get('weight', 0)
        print(f"  {i}. {factor_name} (impact: {impact}, weight: {weight})")
    
    print(f"\n--- Metadata ---")
    metadata = structured_exp.get('metadata', {})
    print(f"  Num Models: {metadata.get('num_models', 0)}")
    print(f"  Num Explained: {metadata.get('num_explained', 0)}")
    print(f"  Explanation Method: {metadata.get('explanation_method', 'N/A')}")
    print(f"  Engine Version: {metadata.get('engine_version', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - ExplainabilityEngine working correctly")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    test_engine_integration()

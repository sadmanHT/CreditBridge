"""
Local Explainability Test
Verifies that explanations include rule-based and trustgraph components
and are structured as dicts, not just text.
"""

from app.ai.registry import get_ensemble


def test_local_explainability():
    """
    Test that explanations are properly structured with:
    - Rule-based explanation
    - Trust graph explanation
    - Structured dict format (not just text)
    """
    
    print("="*70)
    print("LOCAL EXPLAINABILITY TEST")
    print("="*70)
    
    # Get ensemble
    ensemble = get_ensemble()
    
    # Prepare input
    input_data = {
        "borrower": {"gender": "male", "region": "Rajshahi"},
        "loan": {"requested_amount": 8000}
    }
    
    print("\n📊 Running ensemble prediction...")
    result = ensemble.run(input_data)
    
    print(f"\n✅ Prediction completed")
    print(f"   Final Score: {result['final_credit_score']}")
    print(f"   Decision: {result['decision']}")
    print(f"   Fraud Flag: {result['fraud_flag']}")
    
    # Test 1: Explanation exists and is a dict
    print(f"\n🔍 Test 1: Explanation structure")
    assert "explanation" in result, "❌ Missing 'explanation' key"
    assert isinstance(result["explanation"], dict), "❌ Explanation is not a dict"
    print(f"   ✅ Explanation is a dict")
    print(f"   Keys: {list(result['explanation'].keys())}")
    
    # Test 2: Per-model explanations exist
    print(f"\n🔍 Test 2: Per-model explanations")
    assert "per_model" in result["explanation"], "❌ Missing 'per_model' in explanation"
    per_model = result["explanation"]["per_model"]
    print(f"   ✅ Per-model explanations exist")
    print(f"   Models: {list(per_model.keys())}")
    
    # Test 3: Rule-based explanation exists
    print(f"\n🔍 Test 3: Rule-based explanation")
    rule_based_found = False
    for model_name, exp in per_model.items():
        if "RuleBasedCreditModel" in model_name or "credit" in model_name.lower():
            rule_based_found = True
            assert isinstance(exp, dict), f"❌ Rule-based explanation is not a dict"
            print(f"   ✅ Rule-based explanation found: {model_name}")
            print(f"   Type: {type(exp)}")
            print(f"   Keys: {list(exp.keys())}")
            break
    
    assert rule_based_found, "❌ No rule-based explanation found"
    
    # Test 4: Trust graph explanation exists
    print(f"\n🔍 Test 4: Trust graph explanation")
    trust_graph_found = False
    for model_name, exp in per_model.items():
        if "TrustGraph" in model_name or "trust" in model_name.lower():
            trust_graph_found = True
            assert isinstance(exp, dict), f"❌ Trust graph explanation is not a dict"
            print(f"   ✅ Trust graph explanation found: {model_name}")
            print(f"   Type: {type(exp)}")
            print(f"   Keys: {list(exp.keys())}")
            break
    
    assert trust_graph_found, "❌ No trust graph explanation found"
    
    # Test 5: Structured explanation exists
    print(f"\n🔍 Test 5: Structured explanation (ExplainabilityEngine)")
    assert "structured_explanation" in result, "❌ Missing 'structured_explanation'"
    structured = result["structured_explanation"]
    assert isinstance(structured, dict), "❌ Structured explanation is not a dict"
    print(f"   ✅ Structured explanation exists")
    print(f"   Keys: {list(structured.keys())}")
    
    # Test 6: Structured explanation has model_explanations
    print(f"\n🔍 Test 6: Model explanations in structured format")
    assert "model_explanations" in structured, "❌ Missing 'model_explanations'"
    model_explanations = structured["model_explanations"]
    assert isinstance(model_explanations, dict), "❌ model_explanations is not a dict"
    print(f"   ✅ Model explanations exist")
    print(f"   Models: {list(model_explanations.keys())}")
    
    # Test 7: Rule-based in structured explanation
    print(f"\n🔍 Test 7: Rule-based in structured explanation")
    rule_in_structured = False
    for model_name, exp in model_explanations.items():
        if "RuleBasedCreditModel" in model_name:
            rule_in_structured = True
            assert isinstance(exp, dict), "❌ Rule explanation not a dict"
            exp_type = exp.get("type")
            print(f"   ✅ Rule-based found: {model_name}")
            print(f"   Type: {exp_type}")
            print(f"   Confidence: {exp.get('confidence', 0):.2f}")
            if "factors" in exp:
                print(f"   Factors: {len(exp['factors'])} factors")
            break
    
    assert rule_in_structured, "❌ Rule-based not in structured explanation"
    
    # Test 8: Trust graph in structured explanation
    print(f"\n🔍 Test 8: Trust graph in structured explanation")
    trust_in_structured = False
    for model_name, exp in model_explanations.items():
        if "TrustGraph" in model_name:
            trust_in_structured = True
            assert isinstance(exp, dict), "❌ Trust explanation not a dict"
            exp_type = exp.get("type")
            print(f"   ✅ Trust graph found: {model_name}")
            print(f"   Type: {exp_type}")
            print(f"   Confidence: {exp.get('confidence', 0):.2f}")
            if "graph_insights" in exp:
                print(f"   Graph insights: {len(exp['graph_insights'])} insights")
            break
    
    assert trust_in_structured, "❌ Trust graph not in structured explanation"
    
    # Test 9: Aggregated factors exist
    print(f"\n🔍 Test 9: Aggregated factors")
    assert "aggregated_factors" in structured, "❌ Missing 'aggregated_factors'"
    factors = structured["aggregated_factors"]
    assert isinstance(factors, list), "❌ Aggregated factors is not a list"
    print(f"   ✅ Aggregated factors exist")
    print(f"   Count: {len(factors)} factors")
    if factors:
        print(f"   Top factor: {factors[0].get('factor') or factors[0].get('insight', 'N/A')}")
    
    # Test 10: Overall summary exists
    print(f"\n🔍 Test 10: Overall summary")
    assert "overall_summary" in structured, "❌ Missing 'overall_summary'"
    summary = structured["overall_summary"]
    assert isinstance(summary, str), "❌ Overall summary is not a string"
    assert len(summary) > 0, "❌ Overall summary is empty"
    print(f"   ✅ Overall summary exists")
    print(f"   Summary: {summary}")
    
    print(f"\n{'='*70}")
    print(f"✅ ALL TESTS PASSED")
    print(f"{'='*70}")
    print(f"\nSummary:")
    print(f"  ✅ Explanation is structured (dict)")
    print(f"  ✅ Rule-based explanation included")
    print(f"  ✅ Trust graph explanation included")
    print(f"  ✅ Structured explanation via ExplainabilityEngine")
    print(f"  ✅ Aggregated factors provided")
    print(f"  ✅ Overall summary generated")
    print(f"{'='*70}")


if __name__ == "__main__":
    try:
        test_local_explainability()
    except AssertionError as e:
        print(f"\n{'='*70}")
        print(f"❌ TEST FAILED")
        print(f"{'='*70}")
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ UNEXPECTED ERROR")
        print(f"{'='*70}")
        print(f"Error: {e}")
        raise

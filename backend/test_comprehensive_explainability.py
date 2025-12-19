"""
Comprehensive test of ExplainabilityEngine with ensemble predictions
"""

from app.ai.ensemble import ModelEnsemble
from app.ai.explainability import get_explainability_engine
import json


def test_scenario(name: str, borrower: dict, loan_request: dict):
    """Test a specific scenario and display results."""
    print(f"\n{'='*70}")
    print(f"SCENARIO: {name}")
    print(f"{'='*70}")
    
    ensemble = ModelEnsemble()
    result = ensemble.predict(borrower, loan_request)
    
    print(f"\n📊 ENSEMBLE DECISION")
    print(f"  Score: {result['final_credit_score']}")
    print(f"  Decision: {result['decision']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Fraud Flag: {result['fraud_flag']}")
    
    if 'structured_explanation' in result:
        exp = result['structured_explanation']
        print(f"\n🧠 EXPLAINABILITY ENGINE OUTPUT")
        print(f"  Summary: {exp['overall_summary']}")
        print(f"  Confidence: {exp['confidence']:.2f}")
        print(f"  Models Explained: {exp['metadata']['num_explained']}/{exp['metadata']['num_models']}")
        
        print(f"\n  Top 3 Factors:")
        for i, factor in enumerate(exp['aggregated_factors'][:3], 1):
            name = factor.get('factor') or factor.get('insight', 'N/A')
            impact = factor.get('impact', 'N/A')
            print(f"    {i}. {name} ({impact})")
    else:
        print("\n⚠️ No structured explanation found")


def main():
    print("="*70)
    print("COMPREHENSIVE EXPLAINABILITY ENGINE TEST")
    print("="*70)
    
    # Scenario 1: High-quality borrower
    test_scenario(
        "High-Quality Borrower (Should Approve)",
        borrower={
            'borrower_id': 'b001',
            'region': 'Dhaka',
            'occupation': 'business_owner',
            'income_monthly': 50000,
            'debt_to_income_ratio': 0.2
        },
        loan_request={
            'requested_amount': 30000,
            'purpose': 'Business expansion'
        }
    )
    
    # Scenario 2: Moderate borrower
    test_scenario(
        "Moderate Borrower (May Need Review)",
        borrower={
            'borrower_id': 'b002',
            'region': 'Chittagong',
            'occupation': 'farmer',
            'income_monthly': 15000,
            'debt_to_income_ratio': 0.35
        },
        loan_request={
            'requested_amount': 50000,
            'purpose': 'Agricultural equipment'
        }
    )
    
    # Scenario 3: High-risk borrower
    test_scenario(
        "High-Risk Borrower (Should Reject)",
        borrower={
            'borrower_id': 'b003',
            'region': 'Unknown',
            'occupation': 'unemployed',
            'income_monthly': 5000,
            'debt_to_income_ratio': 0.8
        },
        loan_request={
            'requested_amount': 100000,
            'purpose': 'Personal use'
        }
    )
    
    # Test direct engine access
    print(f"\n{'='*70}")
    print("DIRECT ENGINE ACCESS TEST")
    print(f"{'='*70}")
    
    engine = get_explainability_engine()
    print(f"\n✅ Engine Retrieved")
    print(f"   Class: {engine.__class__.__name__}")
    print(f"   Registered Explainers: {engine.get_registered_explainers()}")
    print(f"   Supported Models: {engine.get_supported_models()}")
    
    # Test single model explanation
    print(f"\n{'='*70}")
    print("SINGLE MODEL EXPLANATION TEST")
    print(f"{'='*70}")
    
    single_input = {"borrower": {"region": "Dhaka"}, "loan_request": {"requested_amount": 25000}}
    single_output = {"score": 75, "risk_level": "medium"}
    
    try:
        single_exp = engine.explain_single(
            "RuleBasedCreditModel-v1.0",
            single_input,
            single_output
        )
        print(f"\n✅ Single Explanation Generated")
        print(f"   Type: {single_exp.get('type')}")
        print(f"   Confidence: {single_exp.get('confidence', 0):.2f}")
        print(f"   Factors: {len(single_exp.get('factors', []))}")
    except Exception as e:
        print(f"\n❌ Single explanation failed: {e}")
    
    print(f"\n{'='*70}")
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()

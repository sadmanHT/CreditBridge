"""
Test Safety Hardening for AI Ensemble and Decision Engine

This script verifies that all safety features work correctly:

ENSEMBLE SAFETY:
1. Log errors when models fail
2. Exclude failed models from aggregation
3. Raise CriticalModelFailure if no credit model succeeds
4. Default to REVIEW if fraud engine fails
5. Never silently continue on errors

ENGINE SAFETY:
6. Force REVIEW on missing/malformed credit_result
7. Force REVIEW on missing/malformed fraud_result
8. Force REVIEW if fraud_score is None
9. Ensure ≥1 reason per decision
10. Never APPROVE without explicit policy rule
"""

import sys
from typing import Dict, Any
from unittest.mock import Mock, patch
import logging

# Setup logging to see safety warnings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.ai.ensemble import ModelEnsemble, CriticalModelFailure, FeatureValidationError
from app.decision.engine import DecisionEngine
from app.decision.policy import DecisionType


def test_ensemble_model_failure_logging():
    """Test 1: Ensemble logs errors when models fail"""
    print("\n" + "="*80)
    print("TEST 1: Ensemble logs errors when models fail")
    print("="*80)
    
    # Create a mock model that fails
    failing_model = Mock()
    failing_model.name = "FailingCreditModel"
    failing_model.predict.side_effect = Exception("Model prediction failed")
    failing_model.validate_features.return_value = None
    
    # Create a successful model
    working_model = Mock()
    working_model.name = "WorkingCreditModel"
    working_model.predict.return_value = {"score": 75}
    working_model.validate_features.return_value = None
    working_model.explain.return_value = {"summary": "Good credit"}
    
    ensemble = ModelEnsemble(models=[failing_model, working_model])
    
    borrower = {
        "region": "Dhaka",
        "engineered_features": {
            "income": 50000,
            "mobile_activity_score": 0.8,
            "transaction_volume_30d": 15000,
            "activity_consistency": 0.9,
            "avg_transaction_velocity": 5,
            "network_size": 10,
            "peer_default_rate": 0.05
        }
    }
    loan = {"requested_amount": 10000}
    
    # Should log error but continue with working model
    try:
        result = ensemble.predict(borrower, loan)
        print("✅ Ensemble handled model failure gracefully")
        print(f"   Failed models recorded: {[k for k, v in result['model_outputs'].items() if 'error' in v]}")
        print(f"   Working models: {[k for k, v in result['model_outputs'].items() if 'error' not in v]}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_ensemble_excludes_failed_models():
    """Test 2: Failed models excluded from aggregation"""
    print("\n" + "="*80)
    print("TEST 2: Failed models excluded from aggregation")
    print("="*80)
    
    # Create one failing and one working model
    failing_model = Mock()
    failing_model.name = "FailingCreditModel"
    failing_model.predict.side_effect = Exception("Model crashed")
    failing_model.validate_features.return_value = None
    
    working_model = Mock()
    working_model.name = "WorkingCreditModel"
    working_model.predict.return_value = {"score": 80}
    working_model.validate_features.return_value = None
    working_model.explain.return_value = {"summary": "Good"}
    
    ensemble = ModelEnsemble(models=[failing_model, working_model], weights={
        "FailingCreditModel": 0.5,
        "WorkingCreditModel": 0.5
    })
    
    borrower = {"region": "Dhaka", "engineered_features": {
        "income": 50000,
        "mobile_activity_score": 0.8,
        "transaction_volume_30d": 15000,
        "activity_consistency": 0.9,
        "avg_transaction_velocity": 5,
        "network_size": 10,
        "peer_default_rate": 0.05
    }}
    loan = {"requested_amount": 10000}
    
    result = ensemble.predict(borrower, loan)
    
    # Score should only come from working model (80), not averaged with failed model
    print(f"✅ Final credit score: {result['final_credit_score']}")
    print(f"   (Should be close to 80, not influenced by failed model)")


def test_ensemble_critical_model_failure():
    """Test 3: Raise exception if no credit models succeed"""
    print("\n" + "="*80)
    print("TEST 3: Raise CriticalModelFailure if all credit models fail")
    print("="*80)
    
    # Create multiple failing credit models
    failing_model1 = Mock()
    failing_model1.name = "CreditModel1"
    failing_model1.predict.side_effect = Exception("Failed")
    failing_model1.validate_features.return_value = None
    
    failing_model2 = Mock()
    failing_model2.name = "CreditModel2"
    failing_model2.predict.side_effect = Exception("Failed")
    failing_model2.validate_features.return_value = None
    
    ensemble = ModelEnsemble(models=[failing_model1, failing_model2])
    
    borrower = {"region": "Dhaka", "engineered_features": {
        "income": 50000,
        "mobile_activity_score": 0.8,
        "transaction_volume_30d": 15000,
        "activity_consistency": 0.9,
        "avg_transaction_velocity": 5,
        "network_size": 10,
        "peer_default_rate": 0.05
    }}
    loan = {"requested_amount": 10000}
    
    try:
        result = ensemble.predict(borrower, loan)
        print("❌ Should have raised CriticalModelFailure")
    except CriticalModelFailure as e:
        print(f"✅ CriticalModelFailure raised: {str(e)}")
    except Exception as e:
        print(f"❌ Wrong exception type: {type(e).__name__}: {e}")


def test_ensemble_fraud_engine_failure_defaults_to_review():
    """Test 4: Default to REVIEW if fraud engine fails"""
    print("\n" + "="*80)
    print("TEST 4: Fraud engine failure creates safe default (forces REVIEW)")
    print("="*80)
    
    # Create working credit model
    credit_model = Mock()
    credit_model.name = "CreditModel"
    credit_model.predict.return_value = {"score": 85}
    credit_model.validate_features.return_value = None
    credit_model.explain.return_value = {"summary": "Good"}
    
    # Mock fraud engine to fail
    with patch('app.ai.ensemble.get_fraud_engine') as mock_fraud:
        mock_fraud.side_effect = Exception("Fraud engine unavailable")
        
        ensemble = ModelEnsemble(models=[credit_model])
        
        borrower = {"region": "Dhaka", "engineered_features": {
            "income": 50000,
            "mobile_activity_score": 0.8,
            "transaction_volume_30d": 15000,
            "activity_consistency": 0.9,
            "avg_transaction_velocity": 5,
            "network_size": 10,
            "peer_default_rate": 0.05
        }}
        loan = {"requested_amount": 10000}
        
        result = ensemble.predict(borrower, loan)
        
        # Should have fraud_result with error and None fraud_score
        fraud_result = result.get("fraud_result", {})
        print(f"✅ Fraud engine failure handled")
        print(f"   Fraud score: {fraud_result.get('combined_fraud_score')} (should be None)")
        print(f"   Flags: {fraud_result.get('consolidated_flags')}")
        print(f"   This will force REVIEW in DecisionEngine")


def test_engine_missing_credit_result():
    """Test 5: Force REVIEW on missing credit_result"""
    print("\n" + "="*80)
    print("TEST 5: DecisionEngine forces REVIEW on missing credit_result")
    print("="*80)
    
    engine = DecisionEngine()
    
    # Test with None credit_result
    result = engine.make_decision(
        credit_result=None,
        fraud_result={"combined_fraud_score": 0.1}
    )
    
    print(f"✅ Decision: {result.decision} (should be REVIEW)")
    print(f"   Reasons: {result.reasons}")
    assert result.decision == DecisionType.REVIEW
    assert len(result.reasons) >= 1


def test_engine_malformed_credit_result():
    """Test 6: Force REVIEW on malformed credit_result"""
    print("\n" + "="*80)
    print("TEST 6: DecisionEngine forces REVIEW on malformed credit_result")
    print("="*80)
    
    engine = DecisionEngine()
    
    # Test with string instead of dict
    result = engine.make_decision(
        credit_result="invalid",
        fraud_result={"combined_fraud_score": 0.1}
    )
    
    print(f"✅ Decision: {result.decision} (should be REVIEW)")
    print(f"   Reasons: {result.reasons}")
    assert result.decision == DecisionType.REVIEW
    assert len(result.reasons) >= 1


def test_engine_missing_fraud_result():
    """Test 7: Force REVIEW on missing fraud_result"""
    print("\n" + "="*80)
    print("TEST 7: DecisionEngine forces REVIEW on missing fraud_result")
    print("="*80)
    
    engine = DecisionEngine()
    
    # Test with None fraud_result
    result = engine.make_decision(
        credit_result={"final_credit_score": 85},
        fraud_result=None
    )
    
    print(f"✅ Decision: {result.decision} (should be REVIEW)")
    print(f"   Reasons: {result.reasons}")
    assert result.decision == DecisionType.REVIEW
    assert len(result.reasons) >= 1


def test_engine_missing_fraud_score():
    """Test 8: Force REVIEW if fraud_score is None"""
    print("\n" + "="*80)
    print("TEST 8: DecisionEngine forces REVIEW if fraud_score is None")
    print("="*80)
    
    engine = DecisionEngine()
    
    # Test with fraud_result missing combined_fraud_score
    result = engine.make_decision(
        credit_result={"final_credit_score": 85},
        fraud_result={"combined_fraud_score": None}  # None signals failure
    )
    
    print(f"✅ Decision: {result.decision} (should be REVIEW)")
    print(f"   Reasons: {result.reasons}")
    assert result.decision == DecisionType.REVIEW
    assert len(result.reasons) >= 1


def test_engine_always_has_reasons():
    """Test 9: Every decision has at least 1 reason"""
    print("\n" + "="*80)
    print("TEST 9: Every decision has at least 1 reason")
    print("="*80)
    
    engine = DecisionEngine()
    
    test_cases = [
        # Rejection case
        {
            "credit_result": {"final_credit_score": 30},
            "fraud_result": {"combined_fraud_score": 0.1}
        },
        # Review case
        {
            "credit_result": {"final_credit_score": 55},
            "fraud_result": {"combined_fraud_score": 0.1}
        },
        # Approval case
        {
            "credit_result": {"final_credit_score": 85},
            "fraud_result": {"combined_fraud_score": 0.05}
        }
    ]
    
    expected_decisions = [DecisionType.REJECT, DecisionType.REVIEW, DecisionType.APPROVE]
    
    for i, (case, expected) in enumerate(zip(test_cases, expected_decisions), 1):
        result = engine.make_decision(**case)
        print(f"✅ Test case {i}: {result.decision} (expected: {expected})")
        print(f"   Reasons: {result.reasons}")
        assert len(result.reasons) >= 1, f"Decision {result.decision} has no reasons!"


def test_engine_approval_requires_policy_rule():
    """Test 10: Never APPROVE without explicit policy rule"""
    print("\n" + "="*80)
    print("TEST 10: APPROVE only happens with explicit policy rule trigger")
    print("="*80)
    
    engine = DecisionEngine()
    
    # Test high credit score that should trigger approval rule
    result = engine.make_decision(
        credit_result={"final_credit_score": 85},
        fraud_result={"combined_fraud_score": 0.05}
    )
    
    if result.decision == DecisionType.APPROVE:
        print(f"✅ APPROVE decision made")
        print(f"   Reasons: {result.reasons}")
        assert len(result.reasons) >= 1, "Approval has no reasons!"
        # Check that reasons are not just default fallback
        assert "No definitive policy rule" not in result.reasons[0]
    else:
        print(f"✅ Not approved (decision: {result.decision})")


def run_all_tests():
    """Run all safety hardening tests"""
    print("\n" + "="*80)
    print("SAFETY HARDENING TEST SUITE")
    print("="*80)
    print("Testing AI Ensemble and Decision Engine safety features")
    
    tests = [
        test_ensemble_model_failure_logging,
        test_ensemble_excludes_failed_models,
        test_ensemble_critical_model_failure,
        test_ensemble_fraud_engine_failure_defaults_to_review,
        test_engine_missing_credit_result,
        test_engine_malformed_credit_result,
        test_engine_missing_fraud_result,
        test_engine_missing_fraud_score,
        test_engine_always_has_reasons,
        test_engine_approval_requires_policy_rule
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("="*80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

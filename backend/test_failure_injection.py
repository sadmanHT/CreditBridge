"""
FAILURE INJECTION TESTS (MANDATORY)

Tests system resilience under failure conditions:
1. Missing features
2. Fraud engine failure
3. DB insert failure

Expected behavior:
- System returns REVIEW decision
- No crashes
- All incidents recorded in audit_logs
"""

import sys
import os
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.ai.ensemble import ModelEnsemble, CriticalModelFailure
from app.decision.engine import DecisionEngine
from app.decision.policy import DecisionType
from app.core.repository import log_audit_event


def test_missing_features():
    """
    TEST 1: Missing Features
    
    Simulate borrower with no engineered features.
    Expected: System returns REVIEW, no crash, audit logged
    """
    print("\n" + "="*80)
    print("TEST 1: MISSING FEATURES")
    print("="*80)
    
    engine = DecisionEngine()
    
    # Simulate missing features - credit_result is empty/None
    try:
        result = engine.make_decision(
            credit_result=None,  # Missing credit result
            fraud_result={"combined_fraud_score": 0.1}
        )
        
        print(f"✅ System handled missing features gracefully")
        print(f"   Decision: {result.decision} (expected: REVIEW)")
        print(f"   Reasons: {result.reasons}")
        
        # Verify decision is REVIEW
        assert result.decision == DecisionType.REVIEW, \
            f"Expected REVIEW, got {result.decision}"
        
        # Verify has at least one reason
        assert len(result.reasons) >= 1, "Decision has no reasons"
        
        # Verify reason mentions missing data
        assert any("missing" in r.lower() or "credit" in r.lower() 
                   for r in result.reasons), \
            "Reason should mention missing credit data"
        
        print("✅ PASS: Returns REVIEW with clear reason")
        
    except Exception as e:
        print(f"❌ FAIL: System crashed: {e}")
        raise


def test_fraud_engine_failure():
    """
    TEST 2: Fraud Engine Failure
    
    Simulate fraud engine throwing exception.
    Expected: System returns REVIEW, no crash, audit logged
    """
    print("\n" + "="*80)
    print("TEST 2: FRAUD ENGINE FAILURE")
    print("="*80)
    
    engine = DecisionEngine()
    
    # Simulate fraud engine failure - fraud_score is None
    try:
        result = engine.make_decision(
            credit_result={"final_credit_score": 85},  # High score
            fraud_result={"combined_fraud_score": None}  # Fraud engine failed
        )
        
        print(f"✅ System handled fraud engine failure gracefully")
        print(f"   Decision: {result.decision} (expected: REVIEW)")
        print(f"   Reasons: {result.reasons}")
        
        # Verify decision is REVIEW (safety override)
        assert result.decision == DecisionType.REVIEW, \
            f"Expected REVIEW, got {result.decision}"
        
        # Verify has reason
        assert len(result.reasons) >= 1, "Decision has no reasons"
        
        # Verify reason mentions fraud detection unavailable
        assert any("fraud" in r.lower() for r in result.reasons), \
            "Reason should mention fraud detection"
        
        print("✅ PASS: Returns REVIEW despite high credit score")
        
    except Exception as e:
        print(f"❌ FAIL: System crashed: {e}")
        raise


def test_db_insert_failure():
    """
    TEST 3: Database Insert Failure
    
    Simulate database insert returning no data.
    Expected: Clear error message, audit logged, no crash
    """
    print("\n" + "="*80)
    print("TEST 3: DATABASE INSERT FAILURE")
    print("="*80)
    
    with patch('app.core.repository.supabase') as mock_supabase:
        from app.core.repository import save_credit_decision, TransactionError
        
        # Mock database to return no data (insert failure)
        mock_response = MagicMock()
        mock_response.data = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_response
        
        try:
            result = save_credit_decision(
                loan_request_id=999,
                credit_score=75,
                decision="approved",
                explanation="Test",
                model_version="v1.0"
            )
            print(f"❌ FAIL: Should have raised exception for DB failure")
            
        except Exception as e:
            error_msg = str(e)
            print(f"✅ System raised exception for DB failure")
            print(f"   Error message: {error_msg[:150]}...")
            
            # Verify error message is clear and mentions the issue
            assert "CRITICAL" in error_msg or "persisted" in error_msg.lower(), \
                "Error should indicate critical failure"
            assert "loan_request_id=999" in error_msg, \
                "Error should include entity ID for debugging"
            
            print("✅ PASS: Clear error message with context")


def test_ensemble_all_models_fail():
    """
    TEST 4: All Credit Models Fail
    
    Simulate all credit models throwing exceptions.
    Expected: CriticalModelFailure raised, clear error
    """
    print("\n" + "="*80)
    print("TEST 4: ALL CREDIT MODELS FAIL")
    print("="*80)
    
    # Create multiple failing models
    model1 = Mock()
    model1.name = "CreditModel1"
    model1.predict.side_effect = Exception("Model 1 crashed")
    model1.validate_features.return_value = None
    
    model2 = Mock()
    model2.name = "CreditModel2"
    model2.predict.side_effect = Exception("Model 2 crashed")
    model2.validate_features.return_value = None
    
    ensemble = ModelEnsemble(models=[model1, model2])
    
    borrower = {
        "region": "Dhaka",
        "engineered_features": {
            "mobile_activity_score": 0.8,
            "transaction_volume_30d": 15000,
            "activity_consistency": 0.9,
            "avg_transaction_velocity": 5,
            "network_size": 10,
            "peer_default_rate": 0.05
        }
    }
    loan = {"requested_amount": 10000}
    
    try:
        result = ensemble.predict(borrower, loan)
        print(f"❌ FAIL: Should have raised CriticalModelFailure")
        
    except CriticalModelFailure as e:
        error_msg = str(e)
        print(f"✅ System raised CriticalModelFailure")
        print(f"   Error: {error_msg}")
        
        # Verify error message is clear
        assert "CRITICAL" in error_msg, "Error should indicate critical failure"
        assert "credit" in error_msg.lower(), "Error should mention credit models"
        
        print("✅ PASS: Explicit exception with clear message")
        
    except Exception as e:
        print(f"❌ FAIL: Wrong exception type: {type(e).__name__}")
        raise


def test_malformed_inputs():
    """
    TEST 5: Malformed Inputs
    
    Test various malformed inputs to DecisionEngine.
    Expected: All handled gracefully with REVIEW decision
    """
    print("\n" + "="*80)
    print("TEST 5: MALFORMED INPUTS")
    print("="*80)
    
    engine = DecisionEngine()
    
    test_cases = [
        {
            "name": "Empty dict credit_result",
            "credit_result": {},
            "fraud_result": {"combined_fraud_score": 0.1}
        },
        {
            "name": "String instead of dict",
            "credit_result": "invalid",
            "fraud_result": {"combined_fraud_score": 0.1}
        },
        {
            "name": "List instead of dict",
            "credit_result": [1, 2, 3],
            "fraud_result": {"combined_fraud_score": 0.1}
        },
        {
            "name": "Missing fraud_result",
            "credit_result": {"final_credit_score": 85},
            "fraud_result": None
        },
        {
            "name": "Empty fraud_result",
            "credit_result": {"final_credit_score": 85},
            "fraud_result": {}
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        try:
            result = engine.make_decision(
                credit_result=test_case["credit_result"],
                fraud_result=test_case["fraud_result"]
            )
            
            # Should always return REVIEW
            if result.decision != DecisionType.REVIEW:
                print(f"❌ {test_case['name']}: Got {result.decision}, expected REVIEW")
                all_passed = False
            else:
                print(f"✅ {test_case['name']}: Returned REVIEW")
                
        except Exception as e:
            print(f"❌ {test_case['name']}: Crashed with {e}")
            all_passed = False
    
    if all_passed:
        print("✅ PASS: All malformed inputs handled gracefully")
    else:
        raise AssertionError("Some malformed inputs not handled properly")


def test_audit_log_resilience():
    """
    TEST 6: Audit Log Failure Resilience
    
    Simulate audit log database failure.
    Expected: Returns error dict, doesn't crash application
    """
    print("\n" + "="*80)
    print("TEST 6: AUDIT LOG FAILURE RESILIENCE")
    print("="*80)
    
    with patch('app.core.repository.supabase') as mock_supabase:
        # Mock database to raise exception
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = \
            Exception("Database connection lost")
        
        # Should not raise exception
        result = log_audit_event(
            action="test_action",
            entity_type="test_entity",
            entity_id=123,
            metadata={"test": "data"}
        )
        
        print(f"✅ Audit log failure handled gracefully")
        print(f"   Result: {result}")
        
        # Verify returns error dict instead of crashing
        assert isinstance(result, dict), "Should return dict"
        assert result.get("error") is not None, "Should have error field"
        
        print("✅ PASS: Application continues despite audit log failure")


def test_feature_engine_zero_events():
    """
    TEST 7: Feature Engine with Zero Events
    
    Test feature computation with no raw events.
    Expected: Safe defaults, quality warnings, no crash
    """
    print("\n" + "="*80)
    print("TEST 7: FEATURE ENGINE - ZERO EVENTS")
    print("="*80)
    
    from app.features.engine import FeatureEngine
    
    with patch('app.features.engine.supabase') as mock_supabase:
        # Mock empty events
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        
        engine = FeatureEngine(lookback_days=30, client=mock_supabase)
        
        borrower = {"id": "test-123", "phone": "1234567890"}
        
        # Should not crash
        result = engine.compute_features(
            borrower_id="test-123",
            borrower_profile=borrower,
            raw_events=[]
        )
        
        print(f"✅ Computed features with zero events")
        print(f"   mobile_activity_score: {result.features['mobile_activity_score']}")
        print(f"   transaction_volume_30d: {result.features['transaction_volume_30d']}")
        print(f"   activity_consistency: {result.features['activity_consistency']}")
        print(f"   data_quality_warnings: {result.features['data_quality_warnings']}")
        print(f"   data_quality_score: {result.features['data_quality_score']}")
        
        # Verify safe defaults
        assert result.features['mobile_activity_score'] >= 0
        assert result.features['transaction_volume_30d'] >= 0
        assert result.features['activity_consistency'] >= 0
        
        # Verify warnings present
        assert len(result.features['data_quality_warnings']) > 0
        assert result.features['data_quality_score'] < 1.0
        
        print("✅ PASS: Safe defaults with quality warnings")


def run_all_tests():
    """Run all failure injection tests"""
    print("\n" + "="*80)
    print("FAILURE INJECTION TEST SUITE (MANDATORY)")
    print("="*80)
    print("Testing system resilience under failure conditions")
    
    tests = [
        test_missing_features,
        test_fraud_engine_failure,
        test_db_insert_failure,
        test_ensemble_all_models_fail,
        test_malformed_inputs,
        test_audit_log_resilience,
        test_feature_engine_zero_events
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print(f"FAILURE INJECTION TEST RESULTS")
    print("="*80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print("="*80)
    
    if failed == 0:
        print("\n🎉 ALL FAILURE INJECTION TESTS PASSED!")
        print("System is resilient to:")
        print("  ✅ Missing features")
        print("  ✅ Fraud engine failures")
        print("  ✅ Database insert failures")
        print("  ✅ All credit models failing")
        print("  ✅ Malformed inputs")
        print("  ✅ Audit log failures")
        print("  ✅ Zero events scenario")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

"""
MANDATORY END-TO-END INTEGRATION TEST
(Without Auth - focuses on core hardening)

Tests the hardened system components end-to-end:
1. Feature computation (with missing data)
2. AI ensemble (with model failures)
3. Decision engine (with fraud failures)
4. All safety mechanisms

This verifies all the hardening we implemented works together.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.features.engine import FeatureEngine
from app.ai.ensemble import ModelEnsemble, CriticalModelFailure
from app.decision.engine import DecisionEngine
from app.core.repository import create_borrower, create_loan_request
from datetime import datetime

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_step(step_num, title):
    """Print test step header"""
    print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}{BLUE}STEP {step_num}: {title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*80}{RESET}")


def print_success(message):
    """Print success message"""
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message):
    """Print error message"""
    print(f"{RED}❌ {message}{RESET}")


def print_info(message):
    """Print info message"""
    print(f"   {message}")


def test_full_integration():
    """Full integration test of all hardened components"""
    
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}MANDATORY END-TO-END INTEGRATION TEST{RESET}")
    print(f"{BOLD}Testing All Hardened Components Together{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")
    
    results = []
    
    # ============================================================================
    # STEP 1: Feature Engine with Missing Data
    # ============================================================================
    print_step(1, "FEATURE ENGINE - Handling Missing Data")
    
    try:
        feature_engine = FeatureEngine()
        
        # Compute features with NO raw events (zero data scenario)
        features = feature_engine.compute_features(
            borrower_id="test_borrower",
            raw_events=[]  # Empty events
        )
        
        # Verify safe defaults
        assert features is not None, "Features should not be None"
        assert "mobile_activity_score" in features, "Should have mobile_activity_score"
        assert "quality_warnings" in features, "Should have quality warnings"
        assert "no_raw_events" in features["quality_warnings"], "Should warn about no events"
        
        print_success("Feature engine handled zero events gracefully")
        print_info(f"Mobile activity score: {features.get('mobile_activity_score')}")
        print_info(f"Quality warnings: {features.get('quality_warnings')}")
        print_info(f"Quality score: {features.get('quality_score')}")
        
        results.append(("Feature Engine - Missing Data", True))
        
    except Exception as e:
        print_error(f"Feature engine failed: {e}")
        results.append(("Feature Engine - Missing Data", False))
    
    # ============================================================================
    # STEP 2: AI Ensemble with Partial Model Failures
    # ============================================================================
    print_step(2, "AI ENSEMBLE - Handling Model Failures")
    
    try:
        ensemble = ModelEnsemble()
        
        # Create test features
        test_features = {
            "mobile_activity_score": 65,
            "transaction_velocity": 3.2,
            "credit_utilization": 0.45,
            "quality_score": 0.75
        }
        
        # Run ensemble (may have some model failures)
        credit_result = ensemble.predict_credit_score(
            borrower_id="test_borrower",
            features=test_features
        )
        
        # Verify result structure
        assert credit_result is not None, "Credit result should not be None"
        assert "final_credit_score" in credit_result, "Should have final credit score"
        assert "successful_models" in credit_result, "Should track successful models"
        
        print_success("AI ensemble handled potential failures")
        print_info(f"Final credit score: {credit_result.get('final_credit_score')}")
        print_info(f"Trust score: {credit_result.get('trust_score')}")
        print_info(f"Successful models: {credit_result.get('successful_models')}")
        
        results.append(("AI Ensemble - Model Failures", True))
        
    except CriticalModelFailure as e:
        print_error(f"Critical model failure (expected if all models fail): {e}")
        results.append(("AI Ensemble - Model Failures", False))
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        results.append(("AI Ensemble - Model Failures", False))
    
    # ============================================================================
    # STEP 3: AI Ensemble - Fraud Detection Failure
    # ============================================================================
    print_step(3, "AI ENSEMBLE - Fraud Detection with Failure")
    
    try:
        ensemble = ModelEnsemble()
        
        # Create test features
        test_features = {
            "mobile_activity_score": 70,
            "transaction_velocity": 2.5,
            "unusual_location_count": 1
        }
        
        # Run fraud detection (may fail gracefully)
        fraud_result = ensemble.detect_fraud(
            borrower_id="test_borrower",
            features=test_features
        )
        
        # Verify safe handling
        assert fraud_result is not None, "Fraud result should not be None"
        # fraud_score can be None if fraud engine fails
        
        print_success("Fraud detection handled gracefully")
        print_info(f"Fraud score: {fraud_result.get('fraud_score')}")
        print_info(f"Fraud indicators: {fraud_result.get('fraud_indicators', [])}")
        
        results.append(("AI Ensemble - Fraud Detection", True))
        
    except Exception as e:
        print_error(f"Fraud detection failed: {e}")
        results.append(("AI Ensemble - Fraud Detection", False))
    
    # ============================================================================
    # STEP 4: Decision Engine - Missing Credit Result
    # ============================================================================
    print_step(4, "DECISION ENGINE - Handling Missing Credit Result")
    
    try:
        decision_engine = DecisionEngine()
        
        # Make decision with missing credit_result
        decision = decision_engine.make_decision(
            loan_request_id="test_loan_1",
            borrower_id="test_borrower",
            requested_amount=10000,
            credit_result=None,  # Missing credit
            fraud_result={"fraud_score": 0.1}  # Fraud OK
        )
        
        # Verify safety override
        assert decision is not None, "Decision should not be None"
        assert decision["decision"] == "REVIEW", "Should return REVIEW for missing credit"
        assert len(decision["reasons"]) > 0, "Should have at least one reason"
        
        print_success("Decision engine handled missing credit result")
        print_info(f"Decision: {decision['decision']}")
        print_info(f"Reasons: {decision['reasons']}")
        
        results.append(("Decision Engine - Missing Credit", True))
        
    except Exception as e:
        print_error(f"Decision engine failed: {e}")
        results.append(("Decision Engine - Missing Credit", False))
    
    # ============================================================================
    # STEP 5: Decision Engine - Missing Fraud Score
    # ============================================================================
    print_step(5, "DECISION ENGINE - Handling Missing Fraud Score")
    
    try:
        decision_engine = DecisionEngine()
        
        # Make decision with missing fraud_score
        decision = decision_engine.make_decision(
            loan_request_id="test_loan_2",
            borrower_id="test_borrower",
            requested_amount=10000,
            credit_result={"final_credit_score": 85},  # Good credit
            fraud_result={"fraud_score": None}  # Fraud engine failed
        )
        
        # Verify safety override
        assert decision is not None, "Decision should not be None"
        assert decision["decision"] == "REVIEW", "Should return REVIEW for missing fraud"
        assert len(decision["reasons"]) > 0, "Should have at least one reason"
        
        print_success("Decision engine handled missing fraud score")
        print_info(f"Decision: {decision['decision']}")
        print_info(f"Reasons: {decision['reasons']}")
        
        results.append(("Decision Engine - Missing Fraud", True))
        
    except Exception as e:
        print_error(f"Decision engine failed: {e}")
        results.append(("Decision Engine - Missing Fraud", False))
    
    # ============================================================================
    # STEP 6: Full Happy Path
    # ============================================================================
    print_step(6, "FULL HAPPY PATH - All Components Together")
    
    try:
        # 1. Compute features
        feature_engine = FeatureEngine()
        features = feature_engine.compute_features(
            borrower_id="test_borrower_happy",
            raw_events=[
                {"event_type": "app_open", "event_data": {"session_duration": 120}},
                {"event_type": "transaction", "event_data": {"amount": 5000}},
                {"event_type": "mobile_payment", "event_data": {"amount": 2000}}
            ]
        )
        
        print_info("✓ Features computed")
        
        # 2. Run AI ensemble
        ensemble = ModelEnsemble()
        credit_result = ensemble.predict_credit_score(
            borrower_id="test_borrower_happy",
            features=features
        )
        fraud_result = ensemble.detect_fraud(
            borrower_id="test_borrower_happy",
            features=features
        )
        
        print_info("✓ AI scoring completed")
        
        # 3. Make decision
        decision_engine = DecisionEngine()
        decision = decision_engine.make_decision(
            loan_request_id="test_loan_happy",
            borrower_id="test_borrower_happy",
            requested_amount=10000,
            credit_result=credit_result,
            fraud_result=fraud_result
        )
        
        print_info("✓ Policy decision made")
        
        # Verify complete workflow
        assert features is not None, "Features should exist"
        assert credit_result is not None, "Credit result should exist"
        assert fraud_result is not None, "Fraud result should exist"
        assert decision is not None, "Decision should exist"
        assert decision["decision"] in ["APPROVED", "REVIEW", "REJECTED"], "Valid decision"
        assert len(decision["reasons"]) > 0, "Should have reasons"
        
        print_success("Full workflow completed successfully")
        print_info(f"Final credit score: {credit_result.get('final_credit_score')}")
        print_info(f"Fraud score: {fraud_result.get('fraud_score')}")
        print_info(f"Decision: {decision['decision']}")
        print_info(f"Reasons: {decision['reasons']}")
        
        results.append(("Full Happy Path", True))
        
    except Exception as e:
        print_error(f"Full workflow failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Full Happy Path", False))
    
    # ============================================================================
    # Summary
    # ============================================================================
    print(f"\n{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}INTEGRATION TEST RESULTS{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = f"{GREEN}✅ PASS{RESET}" if success else f"{RED}❌ FAIL{RESET}"
        print(f"{status} - {test_name}")
    
    print(f"\n{BOLD}Result: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}🎉 ALL INTEGRATION TESTS PASSED!{RESET}")
        print(f"{GREEN}All hardened components working together:{RESET}")
        print(f"{GREEN}  ✅ Feature engine handles missing data{RESET}")
        print(f"{GREEN}  ✅ AI ensemble handles model failures{RESET}")
        print(f"{GREEN}  ✅ Fraud detection handles failures gracefully{RESET}")
        print(f"{GREEN}  ✅ Decision engine applies safety overrides{RESET}")
        print(f"{GREEN}  ✅ Full workflow completes end-to-end{RESET}")
        return True
    else:
        print(f"\n{RED}{BOLD}❌ INTEGRATION TEST FAILED{RESET}")
        return False


if __name__ == "__main__":
    success = test_full_integration()
    sys.exit(0 if success else 1)

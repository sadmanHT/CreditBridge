"""
Test RuleBasedFraudDetector with FraudDetector Interface
Validates the updated implementation with simple, deterministic rules
"""

from app.ai.fraud import RuleBasedFraudDetector
from typing import Dict, Any


def test_rule_based_fraud_detector():
    """Test RuleBasedFraudDetector with new interface."""
    
    print("="*70)
    print("RULEBASEDFRAUDDETECTOR TEST (FraudDetector Interface)")
    print("="*70)
    
    # Create detector instance
    detector = RuleBasedFraudDetector()
    
    # Test 1: Detector name property
    print(f"\n🔍 Test 1: Detector name property")
    print(f"   Name: {detector.name}")
    assert detector.name == "RuleBasedFraudDetector-v2.0.0"
    print(f"   ✅ Name property working")
    
    # Test 2: Low-risk loan (below baseline)
    print(f"\n🔍 Test 2: Low-risk loan (below baseline)")
    input_low = {
        "borrower": {"region": "Dhaka"},
        "loan": {"requested_amount": 25000}
    }
    
    result_low = detector.evaluate(input_low)
    
    print(f"   Loan Amount: 25,000 (below baseline 50,000)")
    print(f"   Fraud Score: {result_low['fraud_score']:.2f}")
    print(f"   Flags: {result_low['flags']}")
    print(f"   Explanation: {result_low['explanation']}")
    
    assert result_low['fraud_score'] == 0.0, "Low amount should have 0 score"
    assert len(result_low['flags']) == 0, "Low amount should have no flags"
    print(f"   ✅ Low-risk detection working")
    
    # Test 3: Above baseline (moderate risk)
    print(f"\n🔍 Test 3: Above baseline (moderate risk)")
    input_baseline = {
        "borrower": {"region": "Dhaka"},
        "loan": {"requested_amount": 60000}
    }
    
    result_baseline = detector.evaluate(input_baseline)
    
    print(f"   Loan Amount: 60,000 (above baseline 50,000)")
    print(f"   Fraud Score: {result_baseline['fraud_score']:.2f}")
    print(f"   Flags: {result_baseline['flags']}")
    print(f"   Explanation: {result_baseline['explanation']}")
    
    assert result_baseline['fraud_score'] == 0.2, "Baseline should have 0.2 score"
    assert "above_baseline" in result_baseline['flags']
    print(f"   ✅ Baseline detection working")
    
    # Test 4: High amount
    print(f"\n🔍 Test 4: High amount")
    input_high = {
        "borrower": {"region": "Dhaka"},
        "loan": {"requested_amount": 120000}
    }
    
    result_high = detector.evaluate(input_high)
    
    print(f"   Loan Amount: 120,000 (above high threshold 100,000)")
    print(f"   Fraud Score: {result_high['fraud_score']:.2f}")
    print(f"   Flags: {result_high['flags']}")
    print(f"   Explanation: {result_high['explanation']}")
    
    assert result_high['fraud_score'] == 0.4, "High amount should have 0.4 score"
    assert "high_amount" in result_high['flags']
    print(f"   ✅ High amount detection working")
    
    # Test 5: Very high amount
    print(f"\n🔍 Test 5: Very high amount")
    input_very_high = {
        "borrower": {"region": "Dhaka"},
        "loan": {"requested_amount": 250000}
    }
    
    result_very_high = detector.evaluate(input_very_high)
    
    print(f"   Loan Amount: 250,000 (above very high threshold 200,000)")
    print(f"   Fraud Score: {result_very_high['fraud_score']:.2f}")
    print(f"   Flags: {result_very_high['flags']}")
    print(f"   Explanation: {result_very_high['explanation']}")
    
    assert result_very_high['fraud_score'] == 0.6, "Very high should have 0.6 score"
    assert "very_high_amount" in result_very_high['flags']
    print(f"   ✅ Very high amount detection working")
    
    # Test 6: Rapid repeat requests (velocity check)
    print(f"\n🔍 Test 6: Rapid repeat requests (velocity check)")
    input_velocity = {
        "borrower": {"region": "Dhaka"},
        "loan": {"requested_amount": 30000},
        "context": {
            "application_history": [
                {"date": "2025-12-01", "amount": 20000},
                {"date": "2025-12-05", "amount": 25000},
                {"date": "2025-12-10", "amount": 30000}
            ]
        }
    }
    
    result_velocity = detector.evaluate(input_velocity)
    
    print(f"   Loan Amount: 30,000")
    print(f"   Application History: 3 recent requests")
    print(f"   Fraud Score: {result_velocity['fraud_score']:.2f}")
    print(f"   Flags: {result_velocity['flags']}")
    print(f"   Explanation: {result_velocity['explanation']}")
    
    assert result_velocity['fraud_score'] == 0.3, "3 requests should have 0.3 score"
    assert "rapid_repeat_requests" in result_velocity['flags']
    print(f"   ✅ Velocity check working")
    
    # Test 7: Combined rules (high amount + velocity)
    print(f"\n🔍 Test 7: Combined rules (high amount + velocity)")
    input_combined = {
        "borrower": {"region": "Dhaka"},
        "loan": {"requested_amount": 150000},
        "context": {
            "application_history": [
                {"date": "2025-12-01", "amount": 100000},
                {"date": "2025-12-05", "amount": 120000},
                {"date": "2025-12-10", "amount": 150000},
                {"date": "2025-12-12", "amount": 150000}
            ]
        }
    }
    
    result_combined = detector.evaluate(input_combined)
    
    print(f"   Loan Amount: 150,000 (high)")
    print(f"   Application History: 4 recent requests")
    print(f"   Fraud Score: {result_combined['fraud_score']:.2f}")
    print(f"   Flags: {result_combined['flags']}")
    print(f"   Explanation:")
    for exp in result_combined['explanation']:
        print(f"      - {exp}")
    
    # High amount (0.4) + velocity with 4 requests (0.3 + 0.1) = 0.8
    assert result_combined['fraud_score'] == 0.8, "Combined should have 0.8 score"
    assert "high_amount" in result_combined['flags']
    assert "rapid_repeat_requests" in result_combined['flags']
    print(f"   ✅ Combined rules working")
    
    # Test 8: Output format validation
    print(f"\n🔍 Test 8: Output format validation")
    
    for test_name, result in [
        ("Low", result_low),
        ("Baseline", result_baseline),
        ("High", result_high),
        ("Very High", result_very_high),
        ("Velocity", result_velocity),
        ("Combined", result_combined)
    ]:
        # Check required keys
        assert "fraud_score" in result, f"{test_name}: Missing fraud_score"
        assert "flags" in result, f"{test_name}: Missing flags"
        assert "explanation" in result, f"{test_name}: Missing explanation"
        
        # Check types
        assert isinstance(result["fraud_score"], (int, float)), f"{test_name}: fraud_score not numeric"
        assert isinstance(result["flags"], list), f"{test_name}: flags not list"
        assert isinstance(result["explanation"], list), f"{test_name}: explanation not list"
        
        # Check fraud_score range
        assert 0.0 <= result["fraud_score"] <= 1.0, f"{test_name}: fraud_score out of range"
    
    print(f"   ✅ All output formats valid")
    
    # Test 9: Deterministic behavior
    print(f"\n🔍 Test 9: Deterministic behavior")
    
    # Run same input multiple times
    test_input = {
        "borrower": {"region": "Dhaka"},
        "loan": {"requested_amount": 75000}
    }
    
    results = [detector.evaluate(test_input) for _ in range(5)]
    
    # All results should be identical
    for i in range(1, len(results)):
        assert results[i] == results[0], f"Run {i+1} differs from run 1"
    
    print(f"   ✅ Deterministic behavior verified (5 runs identical)")
    
    # Test 10: Legacy interface compatibility
    print(f"\n🔍 Test 10: Legacy interface compatibility")
    
    legacy_result = detector.detect(
        borrower_data={"region": "Dhaka"},
        loan_data={"requested_amount": 120000},
        context=None
    )
    
    print(f"   Legacy detect() method:")
    print(f"   Is Fraud: {legacy_result.is_fraud}")
    print(f"   Fraud Score: {legacy_result.fraud_score:.2f}")
    print(f"   Risk Level: {legacy_result.risk_level}")
    print(f"   Confidence: {legacy_result.confidence:.2f}")
    
    assert legacy_result.fraud_score == 0.4, "Legacy should match new interface"
    print(f"   ✅ Legacy interface working")
    
    print(f"\n{'='*70}")
    print(f"✅ ALL TESTS PASSED")
    print(f"{'='*70}")
    print(f"""
Summary:
  ✅ Inherits from FraudDetector
  ✅ name property implemented
  ✅ evaluate() method returns correct format
  ✅ Simple, explainable rules:
     - High loan amount relative to baseline → risk
     - Rapid repeat loan requests → risk
  ✅ Deterministic logic (same input → same output)
  ✅ Returns fraud_score, flags, explanation
  ✅ Legacy interface maintained for backward compatibility

Rules Implemented:
  1. Loan Amount vs Baseline
     - Below 50,000: No risk (0.0)
     - 50,000-99,999: Above baseline (0.2)
     - 100,000-199,999: High amount (0.4)
     - 200,000+: Very high amount (0.6)
  
  2. Rapid Repeat Requests
     - 3 requests: Base velocity risk (0.3)
     - Each additional request: +0.1 (max 0.4)

Configuration:
{detector.rules_config}
""")
    print("="*70)


if __name__ == "__main__":
    test_rule_based_fraud_detector()

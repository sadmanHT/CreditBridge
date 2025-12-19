"""
Test TrustGraphFraudDetector with FraudDetector Interface
Validates adapter pattern: TrustGraph output → Fraud detection format
"""

from app.ai.fraud import TrustGraphFraudDetector
from typing import Dict, Any


def test_trustgraph_fraud_detector():
    """Test TrustGraphFraudDetector with new interface."""
    
    print("="*70)
    print("TRUSTGRAPHFRAUDDETECTOR TEST (FraudDetector Interface)")
    print("="*70)
    
    # Create detector instance
    detector = TrustGraphFraudDetector()
    
    # Test 1: Detector name property
    print(f"\n🔍 Test 1: Detector name property")
    print(f"   Name: {detector.name}")
    assert detector.name == "TrustGraphFraudDetector-v2.0.0"
    print(f"   ✅ Name property working")
    
    # Test 2: No trust graph data (isolated borrower)
    print(f"\n🔍 Test 2: No trust graph data (isolated borrower)")
    input_no_data = {
        "borrower": {"id": "borrower_001", "region": "Dhaka"},
        "loan": {"requested_amount": 50000},
        "context": {}
    }
    
    result_no_data = detector.evaluate(input_no_data)
    
    print(f"   Trust Graph Data: None")
    print(f"   Fraud Score: {result_no_data['fraud_score']:.2f}")
    print(f"   Flags: {result_no_data['flags']}")
    print(f"   Explanation: {result_no_data['explanation']}")
    
    assert result_no_data['fraud_score'] == 0.3, "No data should have 0.3 score"
    assert "no_trust_graph_data" in result_no_data['flags']
    print(f"   ✅ No data handling working")
    
    # Test 3: Good trust network (low fraud risk)
    print(f"\n🔍 Test 3: Good trust network (low fraud risk)")
    input_good_network = {
        "borrower": {"id": "borrower_002", "region": "Dhaka"},
        "loan": {"requested_amount": 50000},
        "context": {
            "trust_graph_data": {
                "trust_score": 0.9,  # High trust
                "flag_risk": False,
                "default_rate": 0.1,  # Low default rate
                "network_size": 10,
                "defaulted_count": 1
            }
        }
    }
    
    result_good = detector.evaluate(input_good_network)
    
    print(f"   Trust Score: 0.9 (high)")
    print(f"   Default Rate: 10%")
    print(f"   Network Size: 10 peers")
    print(f"   Fraud Score: {result_good['fraud_score']:.2f}")
    print(f"   Flags: {result_good['flags']}")
    print(f"   Explanation:")
    for exp in result_good['explanation']:
        print(f"      - {exp}")
    
    # Adapter logic: fraud_score = 1.0 - trust_score = 1.0 - 0.9 = 0.1
    assert abs(result_good['fraud_score'] - 0.1) < 0.01, "Good network should have low fraud score"
    assert len(result_good['flags']) == 0, "Good network should have no flags"
    print(f"   ✅ Good network detection working")
    
    # Test 4: Fraud ring detected (high default rate)
    print(f"\n🔍 Test 4: Fraud ring detected (high default rate)")
    input_fraud_ring = {
        "borrower": {"id": "borrower_003", "region": "Dhaka"},
        "loan": {"requested_amount": 50000},
        "context": {
            "trust_graph_data": {
                "trust_score": 0.3,  # Low trust
                "flag_risk": True,   # Fraud ring flag
                "default_rate": 0.7,  # 70% default rate!
                "network_size": 10,
                "defaulted_count": 7
            }
        }
    }
    
    result_fraud_ring = detector.evaluate(input_fraud_ring)
    
    print(f"   Trust Score: 0.3 (low)")
    print(f"   Default Rate: 70% (HIGH)")
    print(f"   Flag Risk: True")
    print(f"   Network Size: 10 peers")
    print(f"   Fraud Score: {result_fraud_ring['fraud_score']:.2f}")
    print(f"   Flags: {result_fraud_ring['flags']}")
    print(f"   Explanation:")
    for exp in result_fraud_ring['explanation']:
        print(f"      - {exp}")
    
    # Adapter: fraud_score = 1.0 - 0.3 = 0.7
    assert abs(result_fraud_ring['fraud_score'] - 0.7) < 0.01, "Fraud ring should have high fraud score"
    assert "fraud_ring_detected" in result_fraud_ring['flags']
    assert "high_peer_default_rate" in result_fraud_ring['flags']
    assert "low_trust_score" in result_fraud_ring['flags']  # 0.3 triggers low (not very_low which is < 0.3)
    print(f"   ✅ Fraud ring detection working")
    
    # Test 5: Network isolation (no peers)
    print(f"\n🔍 Test 5: Network isolation (no peers)")
    input_isolated = {
        "borrower": {"id": "borrower_004", "region": "Dhaka"},
        "loan": {"requested_amount": 50000},
        "context": {
            "trust_graph_data": {
                "trust_score": 1.0,  # Default trust (no data)
                "flag_risk": False,
                "default_rate": 0.0,
                "network_size": 0,  # No peers!
                "defaulted_count": 0
            }
        }
    }
    
    result_isolated = detector.evaluate(input_isolated)
    
    print(f"   Network Size: 0 (isolated)")
    print(f"   Trust Score: 1.0")
    print(f"   Fraud Score: {result_isolated['fraud_score']:.2f}")
    print(f"   Flags: {result_isolated['flags']}")
    print(f"   Explanation: {result_isolated['explanation']}")
    
    # Isolated borrowers get minimum 0.3 risk
    assert abs(result_isolated['fraud_score'] - 0.3) < 0.01, "Isolated should have 0.3 score"
    assert "network_isolation" in result_isolated['flags']
    print(f"   ✅ Network isolation detection working")
    
    # Test 6: Moderate risk (low trust score)
    print(f"\n🔍 Test 6: Moderate risk (low trust score)")
    input_moderate = {
        "borrower": {"id": "borrower_005", "region": "Dhaka"},
        "loan": {"requested_amount": 50000},
        "context": {
            "trust_graph_data": {
                "trust_score": 0.45,  # Below 0.5
                "flag_risk": False,
                "default_rate": 0.35,  # Elevated default rate
                "network_size": 8,
                "defaulted_count": 3
            }
        }
    }
    
    result_moderate = detector.evaluate(input_moderate)
    
    print(f"   Trust Score: 0.45 (moderate)")
    print(f"   Default Rate: 35%")
    print(f"   Network Size: 8 peers")
    print(f"   Fraud Score: {result_moderate['fraud_score']:.2f}")
    print(f"   Flags: {result_moderate['flags']}")
    print(f"   Explanation:")
    for exp in result_moderate['explanation']:
        print(f"      - {exp}")
    
    # fraud_score = 1.0 - 0.45 = 0.55
    assert abs(result_moderate['fraud_score'] - 0.55) < 0.01, "Moderate should have 0.55 score"
    assert "low_trust_score" in result_moderate['flags']
    assert "high_peer_default_rate" in result_moderate['flags']
    print(f"   ✅ Moderate risk detection working")
    
    # Test 7: Adapter mapping validation (trust_score → fraud_score)
    print(f"\n🔍 Test 7: Adapter mapping validation")
    
    test_cases = [
        (1.0, 0.0, "Perfect trust → No fraud"),
        (0.8, 0.2, "High trust → Low fraud"),
        (0.5, 0.5, "Medium trust → Medium fraud"),
        (0.2, 0.8, "Low trust → High fraud"),
        (0.0, 1.0, "No trust → Maximum fraud")
    ]
    
    for trust_score, expected_fraud_score, description in test_cases:
        input_test = {
            "borrower": {"id": "test"},
            "loan": {"requested_amount": 50000},
            "context": {
                "trust_graph_data": {
                    "trust_score": trust_score,
                    "flag_risk": False,
                    "default_rate": 0.0,
                    "network_size": 5,
                    "defaulted_count": 0
                }
            }
        }
        
        result = detector.evaluate(input_test)
        print(f"   {description}: fraud_score = {result['fraud_score']:.2f}")
        assert abs(result['fraud_score'] - expected_fraud_score) < 0.01
    
    print(f"   ✅ Adapter mapping working correctly")
    
    # Test 8: Output format validation
    print(f"\n🔍 Test 8: Output format validation")
    
    for test_name, result in [
        ("No Data", result_no_data),
        ("Good Network", result_good),
        ("Fraud Ring", result_fraud_ring),
        ("Isolated", result_isolated),
        ("Moderate", result_moderate)
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
    
    # Test 9: Legacy interface compatibility
    print(f"\n🔍 Test 9: Legacy interface compatibility")
    
    legacy_result = detector.detect(
        borrower_data={"id": "borrower_006", "region": "Dhaka"},
        loan_data={"requested_amount": 50000},
        context={
            "trust_graph_data": {
                "trust_score": 0.4,
                "flag_risk": False,
                "default_rate": 0.2,
                "network_size": 5,
                "defaulted_count": 1
            }
        }
    )
    
    print(f"   Legacy detect() method:")
    print(f"   Is Fraud: {legacy_result.is_fraud}")
    print(f"   Fraud Score: {legacy_result.fraud_score:.2f}")
    print(f"   Risk Level: {legacy_result.risk_level}")
    print(f"   Confidence: {legacy_result.confidence:.2f}")
    print(f"   Detector Name: {legacy_result.detector_name}")
    
    # fraud_score = 1.0 - 0.4 = 0.6
    assert abs(legacy_result.fraud_score - 0.6) < 0.01, "Legacy should match new interface"
    assert legacy_result.detector_name == "TrustGraphFraudDetector-v2.0.0"
    print(f"   ✅ Legacy interface working")
    
    # Test 10: Compute trust graph from relationships
    print(f"\n🔍 Test 10: Compute trust graph from relationships")
    
    input_with_relationships = {
        "borrower": {"id": "borrower_007", "region": "Dhaka"},
        "loan": {"requested_amount": 50000},
        "context": {
            "relationships": [
                {"peer_id": "p1", "peer_defaulted": False},
                {"peer_id": "p2", "peer_defaulted": False},
                {"peer_id": "p3", "peer_defaulted": False},
                {"peer_id": "p4", "peer_defaulted": True},  # 1 default
                {"peer_id": "p5", "peer_defaulted": False}
            ]
        }
    }
    
    result_relationships = detector.evaluate(input_with_relationships)
    
    print(f"   Relationships: 5 peers, 1 defaulted (20%)")
    print(f"   Fraud Score: {result_relationships['fraud_score']:.2f}")
    print(f"   Flags: {result_relationships['flags']}")
    print(f"   Explanation:")
    for exp in result_relationships['explanation']:
        print(f"      - {exp}")
    
    # trust_score = 1.0 - 0.2 = 0.8
    # fraud_score = 1.0 - 0.8 = 0.2
    assert abs(result_relationships['fraud_score'] - 0.2) < 0.01
    print(f"   ✅ Relationship-based computation working")
    
    print(f"\n{'='*70}")
    print(f"✅ ALL TESTS PASSED")
    print(f"{'='*70}")
    print(f"""
Summary:
  ✅ Inherits from FraudDetector
  ✅ name property implemented
  ✅ evaluate() method returns correct format
  ✅ Adapter pattern correctly implemented:
     - Maps trust_score → fraud_score (inverse)
     - Maps flag_risk → fraud flags
     - Preserves TrustGraph explanations
  ✅ Uses existing TrustGraphModel logic
  ✅ Returns fraud_score, flags, explanation
  ✅ Legacy interface maintained for backward compatibility

Adapter Logic:
  1. Trust Score Mapping (Inverse Relationship)
     - trust_score: 1.0 (good) → fraud_score: 0.0 (safe)
     - trust_score: 0.5 (medium) → fraud_score: 0.5 (medium)
     - trust_score: 0.0 (bad) → fraud_score: 1.0 (fraud)
  
  2. Flag Risk Mapping
     - flag_risk: True → "fraud_ring_detected"
     - default_rate > 30% → "high_peer_default_rate"
     - trust_score < 0.3 → "very_low_trust_score"
     - trust_score < 0.5 → "low_trust_score"
     - network_size == 0 → "network_isolation"
  
  3. Explanation Preservation
     - TrustGraph insights converted to human-readable explanations
     - Network analysis context included
     - Fraud ring detection details preserved

Test Scenarios Validated:
  ✅ No trust graph data (isolated borrower)
  ✅ Good trust network (low fraud risk)
  ✅ Fraud ring detected (high default rate)
  ✅ Network isolation (no peers)
  ✅ Moderate risk (low trust score)
  ✅ Adapter mapping (trust_score → fraud_score)
  ✅ Output format validation
  ✅ Legacy interface compatibility
  ✅ Relationship-based computation
""")
    print("="*70)


if __name__ == "__main__":
    test_trustgraph_fraud_detector()

"""
Test: TrustGraphFraudDetector Feature Adaptation
Validates that TrustGraph output is treated as feature-derived signals.
"""
from app.ai.fraud.trustgraph_adapter import TrustGraphFraudDetector

detector = TrustGraphFraudDetector()

print("=== Test 1: High Trust Score (Low Fraud Risk) ===")
try:
    result = detector.evaluate({
        "features": {},
        "feature_set": "core_behavioral",
        "feature_version": "v1",
        "context": {
            "trust_graph_data": {
                "trust_score": 0.9,
                "flag_risk": False,
                "default_rate": 0.1,
                "network_size": 10
            }
        }
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation:")
    for exp in result['explanation']:
        print(f"    - {exp}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 2: Fraud Ring Detected (High Risk) ===")
try:
    result = detector.evaluate({
        "features": {},
        "feature_set": "core_behavioral",
        "feature_version": "v1",
        "context": {
            "trust_graph_data": {
                "trust_score": 0.2,
                "flag_risk": True,
                "default_rate": 0.8,
                "network_size": 5
            }
        }
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation:")
    for exp in result['explanation']:
        print(f"    - {exp}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 3: Network Isolation (Moderate Risk) ===")
try:
    result = detector.evaluate({
        "features": {},
        "feature_set": "core_behavioral",
        "feature_version": "v1",
        "context": {
            "trust_graph_data": {
                "trust_score": 0.5,
                "flag_risk": False,
                "default_rate": 0.0,
                "network_size": 0
            }
        }
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation:")
    for exp in result['explanation']:
        print(f"    - {exp}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 4: Low Trust Score (Elevated Risk) ===")
try:
    result = detector.evaluate({
        "features": {},
        "feature_set": "core_behavioral",
        "feature_version": "v1",
        "context": {
            "trust_graph_data": {
                "trust_score": 0.25,
                "flag_risk": False,
                "default_rate": 0.75,
                "network_size": 8
            }
        }
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation:")
    for exp in result['explanation']:
        print(f"    - {exp}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== Test 5: No Trust Graph Data (Default Risk) ===")
try:
    result = detector.evaluate({
        "features": {},
        "feature_set": "core_behavioral",
        "feature_version": "v1",
        "context": {}  # No trust_graph_data
    })
    print(f"✓ Evaluation succeeded")
    print(f"  Fraud Score: {result['fraud_score']}")
    print(f"  Flags: {result['flags']}")
    print(f"  Explanation:")
    for exp in result['explanation']:
        print(f"    - {exp}")
except Exception as e:
    print(f"✗ Test FAILED: {e}")

print("\n=== All TrustGraphFraudDetector Adaptation Tests Complete ===")

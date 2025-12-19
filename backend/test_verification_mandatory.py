"""
MANDATORY VERIFICATION TESTS
Tests B, C, D as specified in requirements
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
AUTH_TOKEN = "test_token"

def print_test(label: str):
    """Print test header"""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}\n")

# ============================================================================
# TEST B: MFI Dashboard API
# ============================================================================

print_test("TEST B: MFI Dashboard API - GET /api/v1/dashboard/mfi/overview")

headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
response = requests.get(
    f"{BASE_URL}/api/v1/dashboard/mfi/overview",
    headers=headers,
    timeout=10
)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\n[PASS] Non-empty aggregated stats received:\n")
    print(json.dumps(data, indent=2))
    
    # Verify non-empty
    assert data.get("total_loans") is not None, "total_loans missing"
    assert data.get("approved_count") is not None, "approved_count missing"
    assert data.get("rejected_count") is not None, "rejected_count missing"
    assert data.get("review_count") is not None, "review_count missing"
    assert data.get("average_credit_score") is not None, "average_credit_score missing"
    assert data.get("flagged_fraud_count") is not None, "flagged_fraud_count missing"
    
    print("\n[OK] All required fields present")
    print("[OK] No errors")
else:
    print(f"\n[FAIL] Error: {response.text}")
    exit(1)

# ============================================================================
# TEST C: Analyst Fairness API
# ============================================================================

print_test("TEST C: Analyst Fairness API - GET /api/v1/dashboard/analyst/fairness")

response = requests.get(
    f"{BASE_URL}/api/v1/dashboard/analyst/fairness",
    headers=headers,
    timeout=10
)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\n[PASS] Fairness metrics received:\n")
    print(json.dumps(data, indent=2))
    
    # Verify gender & region approval rates
    assert "approval_rate_by_gender" in data, "approval_rate_by_gender missing"
    assert "approval_rate_by_region" in data, "approval_rate_by_region missing"
    assert "bias_flags" in data, "bias_flags missing"
    
    print("\n[OK] Gender approval rates present")
    print("[OK] Region approval rates present")
    
    if data.get("bias_flags"):
        print(f"[OK] Bias flags detected: {len(data['bias_flags'])} flags")
    else:
        print("[OK] No bias flags (data is fair)")
else:
    print(f"\n[FAIL] Error: {response.text}")
    exit(1)

# ============================================================================
# TEST D: Risk Dashboard
# ============================================================================

print_test("TEST D: Risk Dashboard - GET /api/v1/dashboard/analyst/risk")

response = requests.get(
    f"{BASE_URL}/api/v1/dashboard/analyst/risk?days=30",
    headers=headers,
    timeout=10
)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\n[PASS] Risk metrics received:\n")
    print(json.dumps(data, indent=2))
    
    # Verify score distributions
    assert "credit_score_distribution" in data, "credit_score_distribution missing"
    assert "fraud_score_distribution" in data, "fraud_score_distribution missing"
    assert "decision_trends_over_time" in data, "decision_trends_over_time missing"
    
    credit_dist = data.get("credit_score_distribution", {})
    fraud_dist = data.get("fraud_score_distribution", {})
    trends = data.get("decision_trends_over_time", [])
    
    print(f"\n[OK] Credit score distribution present ({len(credit_dist)} buckets)")
    print(f"[OK] Fraud score distribution present ({len(fraud_dist)} buckets)")
    print(f"[OK] Trends array present ({len(trends)} data points)")
else:
    print(f"\n[FAIL] Error: {response.text}")
    exit(1)

# ============================================================================
# SUMMARY
# ============================================================================

print_test("ALL VERIFICATION TESTS PASSED ✓")
print("""
[OK] TEST B: MFI Dashboard - Non-empty aggregated stats, no errors
[OK] TEST C: Analyst Fairness - Gender & region approval rates, bias flags
[OK] TEST D: Risk Dashboard - Score distributions, trends array

All mandatory requirements verified successfully!
""")

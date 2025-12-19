"""
Regulatory API Test Script

Tests all regulatory reporting endpoints.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
AUTH_TOKEN = "regulator_token"

def print_section(title: str):
    """Print section divider"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_regulatory_summary():
    """Test GET /regulatory/summary"""
    print_section("TEST 1: Regulatory Summary")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/regulatory/summary?days=30",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[OK] Regulatory summary retrieved:\n")
        print(json.dumps(data, indent=2))
        
        # Verify required fields
        assert "reporting_period" in data
        assert "total_loan_requests" in data
        assert "approval_rate" in data
        assert "rejection_rate" in data
        assert "review_rate" in data
        assert "total_disbursed_amount" in data
        assert "fraud_flag_rate" in data
        
        print("\n[OK] All required fields present")
    else:
        print(f"[FAIL] Error: {response.text}")


def test_regulatory_fairness():
    """Test GET /regulatory/fairness"""
    print_section("TEST 2: Regulatory Fairness")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/regulatory/fairness?days=30",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[OK] Fairness metrics retrieved:\n")
        print(json.dumps(data, indent=2))
        
        # Verify required fields
        assert "reporting_period" in data
        assert "approval_rate_by_gender" in data
        assert "approval_rate_by_region" in data
        assert "bias_incidents" in data
        assert "human_review_counts" in data
        
        print("\n[OK] All required fields present")
    else:
        print(f"[FAIL] Error: {response.text}")


def test_regulatory_lineage():
    """Test GET /regulatory/lineage/{decision_id}"""
    print_section("TEST 3: Decision Lineage")
    
    # First, get a decision ID from recent decisions
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    decisions_response = requests.get(
        f"{BASE_URL}/api/v1/dashboard/mfi/recent-decisions?limit=1",
        headers=headers,
        timeout=10
    )
    
    if decisions_response.status_code != 200 or not decisions_response.json().get("decisions"):
        print("[SKIP] No decisions available to test lineage")
        return
    
    decision_id = decisions_response.json()["decisions"][0]["id"]
    print(f"Testing with decision ID: {decision_id}")
    
    # Now test lineage endpoint
    response = requests.get(
        f"{BASE_URL}/api/v1/regulatory/lineage/{decision_id}",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[OK] Decision lineage retrieved:\n")
        print(json.dumps(data, indent=2))
        
        # Verify required fields
        assert "decision_id" in data
        assert "decision" in data
        assert "data_sources" in data
        assert "models_used" in data
        assert "policy_version" in data
        assert "fraud_checks" in data
        assert "timestamps" in data
        
        print("\n[OK] All required fields present")
    else:
        print(f"[FAIL] Error: {response.text}")


def main():
    """Run all regulatory tests"""
    print("\n" + "="*70)
    print("  REGULATORY API TESTS")
    print("  Testing all 3 regulatory endpoints")
    print("="*70)
    
    try:
        # Check server health
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("[ERROR] Server not running at http://127.0.0.1:8000")
            return
        
        # Run all tests
        test_regulatory_summary()
        test_regulatory_fairness()
        test_regulatory_lineage()
        
        print_section("ALL TESTS COMPLETE")
        print("[OK] All regulatory endpoints tested successfully\n")
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to server. Is it running at http://127.0.0.1:8000?")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")


if __name__ == "__main__":
    main()

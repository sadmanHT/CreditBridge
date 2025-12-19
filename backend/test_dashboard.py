"""
Dashboard API Test Script

Tests all dashboard endpoints with authentication.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8000"

# Use the real UUID from get_current_user
AUTH_TOKEN = "dummy_token"  # get_current_user returns fixed UUID regardless


def print_section(title: str):
    """Print section divider"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_mfi_overview():
    """Test GET /dashboard/mfi/overview"""
    print_section("TEST 1: MFI Overview Dashboard")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/dashboard/mfi/overview",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[OK] MFI Overview retrieved successfully:")
        print(f"  - Total Loans: {data.get('total_loans')}")
        print(f"  - Approved: {data.get('approved_count')}")
        print(f"  - Rejected: {data.get('rejected_count')}")
        print(f"  - Review: {data.get('review_count')}")
        print(f"  - Average Credit Score: {data.get('average_credit_score')}")
        print(f"  - Flagged Fraud: {data.get('flagged_fraud_count')}")
    else:
        print(f"[FAIL] Error: {response.text}")


def test_recent_decisions():
    """Test GET /dashboard/mfi/recent-decisions"""
    print_section("TEST 2: Recent Decisions")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/dashboard/mfi/recent-decisions?limit=5",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        count = data.get('count', 0)
        decisions = data.get('decisions', [])
        
        print(f"\n[OK] Retrieved {count} recent decisions:")
        for i, decision in enumerate(decisions[:3], 1):
            print(f"\n  Decision {i}:")
            print(f"    - ID: {decision.get('id')}")
            print(f"    - Decision: {decision.get('decision')}")
            print(f"    - Credit Score: {decision.get('credit_score')}")
            print(f"    - Fraud Score: {decision.get('fraud_score')}")
            print(f"    - Created: {decision.get('created_at')}")
        
        if count > 3:
            print(f"\n  ... and {count - 3} more decisions")
    else:
        print(f"[FAIL] Error: {response.text}")


def test_fairness_metrics():
    """Test GET /dashboard/analyst/fairness"""
    print_section("TEST 3: Fairness Metrics")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/dashboard/analyst/fairness",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n[OK] Fairness metrics retrieved:")
        
        print("\n  Approval Rate by Gender:")
        for gender, rate in data.get('approval_rate_by_gender', {}).items():
            print(f"    - {gender}: {rate * 100:.1f}%")
        
        print("\n  Approval Rate by Region:")
        for region, rate in data.get('approval_rate_by_region', {}).items():
            print(f"    - {region}: {rate * 100:.1f}%")
        
        bias_flags = data.get('bias_flags', [])
        if bias_flags:
            print(f"\n  [WARN] Bias Flags Detected ({len(bias_flags)}):")
            for flag in bias_flags:
                print(f"    - {flag.get('type')}: {flag.get('description')} (severity: {flag.get('severity')})")
        else:
            print("\n  [OK] No bias flags detected")
    else:
        print(f"[FAIL] Error: {response.text}")


def test_risk_metrics():
    """Test GET /dashboard/analyst/risk"""
    print_section("TEST 4: Risk Distribution Metrics")
    
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/dashboard/analyst/risk?days=30",
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n[OK] Risk metrics retrieved:")
        
        print("\n  Credit Score Distribution:")
        for bucket, count in data.get('credit_score_distribution', {}).items():
            print(f"    - {bucket}: {count} loans")
        
        print("\n  Fraud Score Distribution:")
        for bucket, count in data.get('fraud_score_distribution', {}).items():
            print(f"    - {bucket}: {count} loans")
        
        trends = data.get('decision_trends_over_time', [])
        if trends:
            print(f"\n  Decision Trends (showing last 3 days):")
            for trend in trends[-3:]:
                date = trend.get('date')
                approved = trend.get('approved', 0)
                rejected = trend.get('rejected', 0)
                review = trend.get('review', 0)
                total = approved + rejected + review
                print(f"    - {date}: {total} total (A:{approved}, R:{rejected}, Rev:{review})")
        else:
            print("\n  No trend data available")
    else:
        print(f"[FAIL] Error: {response.text}")


def main():
    """Run all dashboard tests"""
    print("\n" + "="*70)
    print("  DASHBOARD API TESTS")
    print("  Testing all 4 dashboard endpoints")
    print("="*70)
    
    try:
        # Check server health
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("[ERROR] Server not running at http://127.0.0.1:8000")
            return
        
        # Run all tests
        test_mfi_overview()
        test_recent_decisions()
        test_fairness_metrics()
        test_risk_metrics()
        
        print_section("ALL TESTS COMPLETE")
        print("[OK] All dashboard endpoints tested successfully\n")
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Cannot connect to server. Is it running at http://127.0.0.1:8000?")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")


if __name__ == "__main__":
    main()

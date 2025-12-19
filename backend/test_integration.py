"""
Integration Tests: API Gateway Hardening

Tests rate limiting and idempotency against running API server.

PREREQUISITES:
1. Start API server: uvicorn app.main:app --reload
2. Ensure test user credentials available
3. Run: python test_integration.py

TESTS:
A. Rate Limiting (>60 requests → 429)
B. Idempotency (same key → same response, no duplicate)
C. Normal Flow (no header → works normally)
"""

import requests
import time
import uuid
import json
from typing import Dict, Optional


# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "http://localhost:8000"
API_ENDPOINT = f"{BASE_URL}/api/v1/test/ping"  # Using simple test endpoint

# Mock authentication (replace with real token in production)
# For testing, we'll use a simple user identifier
TEST_USER_TOKEN = "test-user-token-123"

# Test data - simple payload for testing
TEST_LOAN_REQUEST = {
    "message": "test"
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def make_request(
    idempotency_key: Optional[str] = None,
    custom_data: Optional[Dict] = None
) -> requests.Response:
    """Make a POST request to the loans endpoint."""
    headers = {
        "Content-Type": "application/json"
        # No Authorization header - endpoint will use "anonymous_user" by default
    }
    
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    
    data = custom_data or TEST_LOAN_REQUEST
    
    try:
        response = requests.post(
            API_ENDPOINT,
            headers=headers,
            json=data,
            timeout=10
        )
        return response
    except requests.exceptions.RequestException as e:
        print(f"[FAIL] Request failed: {e}")
        return None


def check_server_running() -> bool:
    """Check if API server is running."""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return response.status_code == 200
    except:
        return False


# ============================================================================
# TEST A: RATE LIMITING
# ============================================================================

def test_a_rate_limiting():
    """
    Test: Rapidly hit endpoint >60 times
    Expected: HTTP 429 Too Many Requests after 60th request
    """
    print("\n" + "="*80)
    print("TEST A: RATE LIMITING")
    print("="*80)
    print("[*] Objective: Verify rate limit enforced at 60 requests/minute")
    print("[*] Expected: First 60 succeed, 61st returns 429")
    
    success_count = 0
    rate_limited_count = 0
    first_rate_limit_at = None
    
    print("\n[~] Making rapid requests...")
    
    for i in range(1, 65):  # Try 64 requests
        response = make_request()
        
        if response is None:
            print(f"Request {i}: [FAIL] Failed to connect")
            continue
        
        # Check headers
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")
        
        if response.status_code == 200:
            success_count += 1
            if i <= 5 or i >= 58:  # Print first 5 and last few
                print(f"Request {i:2d}: [OK] 200 OK (Remaining: {remaining})")
        elif response.status_code == 429:
            rate_limited_count += 1
            if first_rate_limit_at is None:
                first_rate_limit_at = i
            
            retry_after = response.headers.get("Retry-After")
            print(f"Request {i:2d}: [STOP] 429 RATE LIMITED (Retry-After: {retry_after}s)")
            
            # Parse error response
            try:
                error_data = response.json()
                print(f"           Error: {error_data.get('detail', {}).get('message', 'N/A')}")
            except:
                pass
        else:
            print(f"Request {i:2d}: [WARN] {response.status_code} (Unexpected)")
        
        # Show progress dots for middle requests
        if 6 <= i <= 57:
            if i % 10 == 0:
                print(f"           ... {i} requests completed (Remaining: {remaining})")
    
    # Summary
    print(f"\n[RESULTS]:")
    print(f"   Successful requests:    {success_count}")
    print(f"   Rate limited requests:  {rate_limited_count}")
    print(f"   First rate limit at:    Request #{first_rate_limit_at}")
    
    # Validation
    print(f"\n[OK] VALIDATION:")
    if success_count >= 55 and success_count <= 60:
        print(f"   [+] Success count in expected range (55-60): {success_count}")
    else:
        print(f"   [-] Unexpected success count: {success_count} (expected 55-60)")
    
    if rate_limited_count > 0:
        print(f"   [+] Rate limiting active (blocked {rate_limited_count} requests)")
    else:
        print(f"   [-] Rate limiting NOT working (no 429 responses)")
    
    if first_rate_limit_at and 58 <= first_rate_limit_at <= 62:
        print(f"   [+] First rate limit at expected position: #{first_rate_limit_at}")
    else:
        print(f"   [WARN] First rate limit at unexpected position: #{first_rate_limit_at}")
    
    # Overall result
    if success_count >= 55 and rate_limited_count > 0:
        print(f"\n[PASS] TEST A PASSED: Rate limiting working correctly!")
    else:
        print(f"\n[FAIL] TEST A FAILED: Rate limiting not working as expected")


# ============================================================================
# TEST B: IDEMPOTENCY
# ============================================================================

def test_b_idempotency():
    """
    Test: Send same POST twice with Idempotency-Key
    Expected: Second response identical, no duplicate loan created
    """
    print("\n" + "="*80)
    print("TEST B: IDEMPOTENCY")
    print("="*80)
    print("[*] Objective: Verify idempotency prevents duplicate loan requests")
    print("[>] Expected: Same response for both requests, cached on 2nd\n")
    
    # Wait a bit to avoid rate limiting from previous test
    print("[WAIT] Waiting 5 seconds to avoid rate limit...")
    time.sleep(5)
    
    # Generate unique idempotency key
    idempotency_key = f"test-{uuid.uuid4()}"
    print(f"[KEY] Idempotency Key: {idempotency_key[:16]}...\n")
    
    # First request
    print("[OUT] REQUEST 1: First submission")
    response1 = make_request(idempotency_key=idempotency_key)
    
    if response1 is None:
        print("[FAIL] TEST B FAILED: First request failed")
    
    print(f"   Status: {response1.status_code}")
    print(f"   Idempotent-Replayed: {response1.headers.get('Idempotent-Replayed', 'false')}")
    
    try:
        data1 = response1.json()
        print(f"   Response: {data1}")
    except:
        print("   [WARN]  Could not parse response JSON")
        data1 = None
    
    # Second request (same key, same data)
    print(f"\n[OUT] REQUEST 2: Retry with same key")
    time.sleep(1)  # Small delay
    response2 = make_request(idempotency_key=idempotency_key)
    
    if response2 is None:
        print("[FAIL] TEST B FAILED: Second request failed")
    
    print(f"   Status: {response2.status_code}")
    is_replayed = response2.headers.get('Idempotent-Replayed', 'false')
    print(f"   Idempotent-Replayed: {is_replayed}")
    
    try:
        data2 = response2.json()
        print(f"   Response: {data2}")
    except:
        print("   [WARN]  Could not parse response JSON")
        data2 = None
    
    # Third request (different key, should NOT be cached)
    print(f"\n[OUT] REQUEST 3: Different key (should NOT be cached)")
    different_key = f"test-{uuid.uuid4()}"
    time.sleep(1)
    response3 = make_request(idempotency_key=different_key)
    data3 = None
    
    if response3:
        print(f"   Status: {response3.status_code}")
        print(f"   Idempotent-Replayed: {response3.headers.get('Idempotent-Replayed', 'false')}")
        try:
            data3 = response3.json()
            print(f"   Response: {data3}")
        except:
            data3 = None
    
    # Validation
    print(f"\n[OK] VALIDATION:")
    
    all_passed = True
    
    # Check status codes
    if response1.status_code == 200 and response2.status_code == 200:
        print(f"   [+] Both requests returned 200 OK")
    else:
        print(f"   [-] Status codes: {response1.status_code}, {response2.status_code}")
        all_passed = False
    
    # Check idempotent-replayed header
    if is_replayed.lower() == 'true':
        print(f"   [+] Second request marked as replayed (Idempotent-Replayed: true)")
    else:
        print(f"   [WARN]  Second request NOT marked as replayed (header: {is_replayed})")
        print(f"      Note: May indicate cache not working or endpoint not protected")
    
    # Check idempotent-replayed header
    if is_replayed.lower() == 'true':
        print(f"   [+] Second request marked as replayed (Idempotent-Replayed: true)")
    else:
        print(f"   [WARN]  Second request NOT marked as replayed (header: {is_replayed})")
        print(f"      Note: May indicate cache not working or endpoint not protected")
    
    # Check response bodies match
    if data1 and data2:
        if data1 == data2:
            print(f"   [+] Response bodies match (cached correctly)")
        else:
            print(f"   [WARN]  Response bodies differ")
            all_passed = False
    
    # Overall result
    if all_passed and is_replayed.lower() == 'true':
        print(f"\n[PASS] TEST B PASSED: Idempotency working correctly!")
    else:
        print(f"\n[WARN]  TEST B PARTIAL: Idempotency may need verification")
        print(f"      Check if IdempotencyMiddleware is registered in main.py")
        print(f"      Check if /api/v1/test/ping is in PROTECTED_PATHS")


# ============================================================================
# TEST C: NORMAL FLOW (WITHOUT IDEMPOTENCY KEY)
# ============================================================================

def test_c_normal_flow():
    """
    Test: Request without Idempotency-Key header
    Expected: Works normally, creates new loan each time
    """
    print("\n" + "="*80)
    print("TEST C: NORMAL FLOW (No Idempotency Key)")
    print("="*80)
    print("[*] Objective: Verify requests work without idempotency key")
    print("[>] Expected: Each request creates new loan (no caching)\n")
    
    # Wait to avoid rate limiting
    print("[WAIT] Waiting 5 seconds to avoid rate limit...")
    time.sleep(5)
    
    loan_ids = []
    
    # Make 3 requests without idempotency key
    for i in range(1, 4):
        print(f"\n[OUT] REQUEST {i}: No Idempotency-Key header")
        response = make_request(idempotency_key=None)  # No key!
        
        if response is None:
            print(f"   [FAIL] Request failed")
            continue
        
        print(f"   Status: {response.status_code}")
        print(f"   Idempotent-Replayed: {response.headers.get('Idempotent-Replayed', 'N/A')}")
        
        try:
            data = response.json()
            loan_id = data.get("loan_request", {}).get("id", "N/A")
            loan_ids.append(loan_id)
            print(f"   Loan Request ID: {loan_id}")
        except:
            print(f"   [WARN]  Could not parse response")
        
        time.sleep(1)
    
    # Validation
    print(f"\n[OK] VALIDATION:")
    
    # Check all requests succeeded
    if len(loan_ids) == 3:
        print(f"   [+] All 3 requests succeeded")
    else:
        print(f"   [WARN]  Only {len(loan_ids)}/3 requests succeeded")
    
    # Check all loan IDs are different (no caching)
    unique_ids = set(id for id in loan_ids if id != "N/A")
    if len(unique_ids) == len(loan_ids) and len(unique_ids) == 3:
        print(f"   [+] All loan IDs are unique (no caching without key)")
        print(f"      IDs: {loan_ids}")
    elif len(unique_ids) < len(loan_ids):
        print(f"   [WARN]  Some loan IDs match (unexpected caching)")
        print(f"      IDs: {loan_ids}")
    else:
        print(f"   [WARN]  Could not verify uniqueness")
    
    # Overall result
    if len(loan_ids) == 3 and len(unique_ids) == 3:
        print(f"\n[PASS] TEST C PASSED: Normal flow working correctly!")
    else:
        print(f"\n[WARN]  TEST C NEEDS REVIEW: Check results above")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("API GATEWAY INTEGRATION TESTS")
    print("="*80)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"[>] Endpoint: {API_ENDPOINT}")
    print("="*80)
    
    # Check if server is running
    print("\n🔍 Checking if API server is running...")
    if not check_server_running():
        print("[FAIL] ERROR: API server is not running!")
        print("\n📝 To start the server:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload")
        print("\n   Then run this test again.")
        return
    
    print("[OK] API server is running\n")
    
    # Run tests
    results = {}
    
    try:
        results['A'] = test_a_rate_limiting()
    except Exception as e:
        print(f"\n[FAIL] TEST A CRASHED: {e}")
        results['A'] = False
    
    try:
        results['B'] = test_b_idempotency()
    except Exception as e:
        print(f"\n[FAIL] TEST B CRASHED: {e}")
        results['B'] = False
    
    try:
        results['C'] = test_c_normal_flow()
    except Exception as e:
        print(f"\n[FAIL] TEST C CRASHED: {e}")
        results['C'] = False
    
    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "[OK] PASSED" if passed else "[FAIL] FAILED"
        print(f"   Test {test_name}: {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n   Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n[PASS] ALL INTEGRATION TESTS PASSED! [PASS]")
        print("   Your API gateway hardening is working correctly!")
    else:
        print(f"\n[WARN]  {total_count - passed_count} test(s) failed or need review")
        print("   Check the output above for details")
    
    print("="*80)


if __name__ == "__main__":
    try:
        run_integration_tests()
    except KeyboardInterrupt:
        print("\n\n[WARN]  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n[FAIL] Tests failed with error: {e}")
        import traceback
        traceback.print_exc()


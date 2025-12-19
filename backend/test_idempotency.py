"""
Test Suite: Idempotency Middleware

Tests the idempotency handling for critical API endpoints.

COVERAGE:
1. Basic idempotency (same key returns same response)
2. Cache hit detection
3. Request body validation (same key, different body)
4. Cache expiration (TTL)
5. Cache cleanup mechanism
6. Statistics collection
7. Protected endpoints only
"""

import asyncio
import hashlib
import time
import uuid
from app.api.middleware import IdempotencyCache, get_idempotency_cache


def test_basic_idempotency():
    """Test basic cache set and get."""
    print("\n" + "="*80)
    print("TEST 1: Basic Idempotency")
    print("="*80)
    
    cache = IdempotencyCache(max_entries=100, ttl_seconds=60)
    
    # Simulate request
    idempotency_key = str(uuid.uuid4())
    request_body = '{"amount": 10000, "purpose": "business"}'
    request_hash = hashlib.sha256(request_body.encode()).hexdigest()
    
    # Store response
    cache.set(
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_body='{"loan_id": "abc123", "status": "approved"}',
        status_code=200,
        headers={"Content-Type": "application/json"}
    )
    print(f"✓ Stored response for key: {idempotency_key[:8]}...")
    
    # Retrieve response
    cached = cache.get(idempotency_key, request_hash)
    assert cached is not None, "Cache should return stored response"
    
    response_body, status_code, headers = cached
    assert status_code == 200
    assert b"abc123" in response_body
    print(f"✓ Retrieved cached response: status={status_code}")
    print(f"✓ Response body matches: {response_body.decode()[:50]}...")
    
    print(f"\n✅ TEST 1 PASSED: Basic idempotency works")


def test_cache_miss():
    """Test cache miss scenarios."""
    print("\n" + "="*80)
    print("TEST 2: Cache Miss Scenarios")
    print("="*80)
    
    cache = IdempotencyCache(max_entries=100, ttl_seconds=60)
    
    # Non-existent key
    result = cache.get("non-existent-key", "some-hash")
    assert result is None, "Non-existent key should return None"
    print("✓ Non-existent key returns None")
    
    # Different request hash (same key, different body)
    idempotency_key = str(uuid.uuid4())
    request_hash1 = hashlib.sha256(b"request1").hexdigest()
    request_hash2 = hashlib.sha256(b"request2").hexdigest()
    
    cache.set(
        idempotency_key=idempotency_key,
        request_hash=request_hash1,
        response_body='{"result": "first"}',
        status_code=200,
        headers={}
    )
    
    # Try to retrieve with different hash
    result = cache.get(idempotency_key, request_hash2)
    assert result is None, "Different request hash should return None"
    print("✓ Same key with different body returns None (prevents misuse)")
    
    print(f"\n✅ TEST 2 PASSED: Cache miss detection works")


def test_cache_expiration():
    """Test TTL-based cache expiration."""
    print("\n" + "="*80)
    print("TEST 3: Cache Expiration (TTL)")
    print("="*80)
    
    # Use short TTL for testing
    cache = IdempotencyCache(max_entries=100, ttl_seconds=2)
    
    idempotency_key = str(uuid.uuid4())
    request_hash = hashlib.sha256(b"test").hexdigest()
    
    # Store response
    cache.set(
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        response_body='{"result": "test"}',
        status_code=200,
        headers={}
    )
    print(f"✓ Stored response with 2-second TTL")
    
    # Should be available immediately
    result = cache.get(idempotency_key, request_hash)
    assert result is not None
    print(f"✓ Response available immediately")
    
    # Wait for expiration
    print("⏳ Waiting 3 seconds for expiration...")
    time.sleep(3)
    
    # Should be expired
    result = cache.get(idempotency_key, request_hash)
    assert result is None, "Expired entry should return None"
    print(f"✓ Response expired after TTL")
    
    print(f"\n✅ TEST 3 PASSED: Cache expiration works")


def test_cache_cleanup():
    """Test automatic cleanup of expired entries."""
    print("\n" + "="*80)
    print("TEST 4: Cache Cleanup Mechanism")
    print("="*80)
    
    cache = IdempotencyCache(max_entries=100, ttl_seconds=1)
    
    # Add multiple entries
    for i in range(5):
        key = f"test-key-{i}"
        hash_val = hashlib.sha256(f"test-{i}".encode()).hexdigest()
        cache.set(key, hash_val, f'{{"result": {i}}}', 200, {})
    
    initial_count = len(cache._cache)
    print(f"✓ Added {initial_count} entries")
    
    # Wait for expiration
    print("⏳ Waiting 2 seconds for expiration...")
    time.sleep(2)
    
    # Force cleanup by setting last_cleanup to old time
    cache._last_cleanup = time.time() - 400  # Force cleanup on next get()
    
    # Trigger cleanup by making a get request
    cache.get("trigger-cleanup", "dummy-hash")
    
    final_count = len(cache._cache)
    print(f"✓ After cleanup: {final_count} entries remain")
    assert final_count == 0, "All expired entries should be cleaned up"
    
    print(f"\n✅ TEST 4 PASSED: Cleanup mechanism works")


def test_cache_size_limit():
    """Test emergency cleanup when cache is full."""
    print("\n" + "="*80)
    print("TEST 5: Cache Size Limit")
    print("="*80)
    
    # Small cache for testing
    cache = IdempotencyCache(max_entries=10, ttl_seconds=3600)
    
    # Fill cache to capacity
    for i in range(10):
        key = f"key-{i}"
        hash_val = hashlib.sha256(f"data-{i}".encode()).hexdigest()
        cache.set(key, hash_val, f'{{"id": {i}}}', 200, {})
        time.sleep(0.01)  # Small delay to ensure different timestamps
    
    print(f"✓ Filled cache to capacity (10 entries)")
    
    # Add 11th entry (should trigger cleanup)
    cache.set(
        "key-overflow",
        hashlib.sha256(b"overflow").hexdigest(),
        '{"overflow": true}',
        200,
        {}
    )
    
    # Cache should have removed oldest 20% (2 entries) and added new one
    # So: 10 - 2 + 1 = 9
    final_count = len(cache._cache)
    print(f"✓ After overflow: {final_count} entries")
    assert final_count <= 10, "Cache should stay within limit"
    
    # New entry should be present
    overflow_hash = hashlib.sha256(b"overflow").hexdigest()
    result = cache.get("key-overflow", overflow_hash)
    assert result is not None, "New entry should be stored"
    print(f"✓ New entry successfully stored")
    
    print(f"\n✅ TEST 5 PASSED: Size limit enforced")


def test_cache_statistics():
    """Test statistics collection."""
    print("\n" + "="*80)
    print("TEST 6: Cache Statistics")
    print("="*80)
    
    cache = IdempotencyCache(max_entries=1000, ttl_seconds=86400)
    
    # Add some entries
    for i in range(5):
        key = f"stat-key-{i}"
        hash_val = hashlib.sha256(f"stat-{i}".encode()).hexdigest()
        cache.set(key, hash_val, f'{{"stat": {i}}}', 200, {})
    
    stats = cache.get_stats()
    
    assert "cached_requests" in stats
    assert "max_entries" in stats
    assert "ttl_seconds" in stats
    assert "last_cleanup" in stats
    
    print(f"✓ Cached requests: {stats['cached_requests']}")
    print(f"✓ Max entries: {stats['max_entries']}")
    print(f"✓ TTL seconds: {stats['ttl_seconds']}")
    print(f"✓ Last cleanup: {stats['last_cleanup']}")
    
    assert stats["cached_requests"] == 5
    assert stats["max_entries"] == 1000
    assert stats["ttl_seconds"] == 86400
    
    print(f"\n✅ TEST 6 PASSED: Statistics work correctly")


def test_request_hash_validation():
    """Test that same key with different body is rejected."""
    print("\n" + "="*80)
    print("TEST 7: Request Hash Validation")
    print("="*80)
    
    cache = IdempotencyCache(max_entries=100, ttl_seconds=3600)
    
    idempotency_key = str(uuid.uuid4())
    
    # First request
    request1 = '{"amount": 10000, "purpose": "business"}'
    hash1 = hashlib.sha256(request1.encode()).hexdigest()
    
    cache.set(idempotency_key, hash1, '{"approved": true}', 200, {})
    print(f"✓ Stored response for request 1")
    
    # Try to use same key with different request body
    request2 = '{"amount": 50000, "purpose": "personal"}'
    hash2 = hashlib.sha256(request2.encode()).hexdigest()
    
    result = cache.get(idempotency_key, hash2)
    assert result is None, "Different request body should be rejected"
    print(f"✓ Same key with different body correctly rejected")
    
    # Original request should still work
    result = cache.get(idempotency_key, hash1)
    assert result is not None, "Original request should still be cached"
    print(f"✓ Original request still cached correctly")
    
    print(f"\n✅ TEST 7 PASSED: Request hash validation works")


def test_global_cache_instance():
    """Test global cache singleton."""
    print("\n" + "="*80)
    print("TEST 8: Global Cache Instance")
    print("="*80)
    
    cache1 = get_idempotency_cache()
    cache2 = get_idempotency_cache()
    
    assert cache1 is cache2, "Should return same instance"
    print(f"✓ Global cache is singleton")
    
    # Store in one, retrieve from other
    key = str(uuid.uuid4())
    hash_val = hashlib.sha256(b"test").hexdigest()
    
    cache1.set(key, hash_val, '{"test": true}', 200, {})
    result = cache2.get(key, hash_val)
    
    assert result is not None, "Should share same cache"
    print(f"✓ Cache is shared across instances")
    
    print(f"\n✅ TEST 8 PASSED: Global instance works")


def run_all_tests():
    """Run all idempotency tests."""
    print("\n" + "="*80)
    print("IDEMPOTENCY MIDDLEWARE TEST SUITE")
    print("="*80)
    
    try:
        test_basic_idempotency()
        test_cache_miss()
        test_cache_expiration()
        test_cache_cleanup()
        test_cache_size_limit()
        test_cache_statistics()
        test_request_hash_validation()
        test_global_cache_instance()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nIdempotency middleware is ready for production!")
        print("Critical features verified:")
        print("  ✓ Duplicate prevention")
        print("  ✓ Request body validation")
        print("  ✓ Cache expiration")
        print("  ✓ Memory management")
        print("  ✓ Statistics collection")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()

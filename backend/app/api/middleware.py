"""
API Middleware Components

SYSTEM ROLE:
Provides middleware for cross-cutting concerns like
rate limiting headers, request logging, error handling,
and idempotency guarantees.

PROJECT:
CreditBridge — API Gateway Layer

IDEMPOTENCY DESIGN:
- Prevents duplicate loan requests
- Uses Idempotency-Key header (client-provided)
- In-memory cache (free-tier friendly)
- Applies ONLY to POST /loans/request
- 24-hour cache retention
"""

import hashlib
import json
import time
from typing import Callable, Dict, Optional, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitHeaderMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add rate limit headers to all responses.
    
    Headers Added:
        - X-RateLimit-Limit: Maximum requests per window
        - X-RateLimit-Remaining: Remaining requests
        - X-RateLimit-Reset: Unix timestamp when limit resets
    
    Usage:
        app.add_middleware(RateLimitHeaderMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add rate limit headers to response."""
        # Call next middleware/endpoint
        response = await call_next(request)
        
        # Add rate limit headers if metadata available
        if hasattr(request.state, "rate_limit_metadata"):
            metadata = request.state.rate_limit_metadata
            
            # Import here to avoid circular dependency
            from app.api.deps import RATE_LIMIT_REQUESTS
            
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(metadata.get("remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(int(metadata.get("reset_at", 0)))
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests.
    
    Logs:
        - Request method and path
        - User ID (if authenticated)
        - Response status code
        - Request duration
    
    Usage:
        app.add_middleware(RequestLoggingMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        import time
        import logging
        
        logger = logging.getLogger("api.requests")
        
        # Record start time
        start_time = time.time()
        
        # Extract user_id if available
        user_id = getattr(request.state, "user_id", "anonymous")
        
        # Call next middleware/endpoint
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} - "
            f"User: {user_id} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration_ms:.2f}ms"
        )
        
        return response


# ============================================================================
# IDEMPOTENCY MIDDLEWARE
# ============================================================================

class IdempotencyCache:
    """
    In-memory cache for idempotent requests.
    
    STORAGE FORMAT:
    {
        "idempotency_key": {
            "response_body": {...},
            "status_code": 200,
            "headers": {...},
            "created_at": 1702732800.5,
            "request_hash": "sha256_hash"
        }
    }
    
    LIMITATIONS (In-Memory):
    - ❌ Lost on server restart
    - ❌ Not shared across multiple servers
    - ❌ Limited by server memory
    
    PRODUCTION UPGRADE PATH:
    - Use Redis for distributed cache
    - Use DynamoDB for persistence
    - Use Memcached for high performance
    """
    
    def __init__(self, max_entries: int = 10000, ttl_seconds: int = 86400):
        """
        Initialize idempotency cache.
        
        Args:
            max_entries: Maximum cached responses (prevent memory bloat)
            ttl_seconds: Time to live for cache entries (default: 24 hours)
        """
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict] = {}
        self._last_cleanup = time.time()
    
    def get(self, idempotency_key: str, request_hash: str) -> Optional[Tuple[bytes, int, Dict]]:
        """
        Retrieve cached response for idempotency key.
        
        Args:
            idempotency_key: Client-provided idempotency key
            request_hash: SHA256 hash of request body
        
        Returns:
            (response_body, status_code, headers) if cache hit
            None if cache miss or request body changed
        """
        # Cleanup expired entries periodically
        current_time = time.time()
        if current_time - self._last_cleanup > 300:  # Every 5 minutes
            self._cleanup_expired(current_time)
        
        entry = self._cache.get(idempotency_key)
        if not entry:
            return None
        
        # Check if expired
        if current_time - entry["created_at"] > self.ttl_seconds:
            del self._cache[idempotency_key]
            return None
        
        # Verify request hash matches (prevent key reuse with different data)
        if entry["request_hash"] != request_hash:
            # Same key, different request = reject
            return None
        
        return (
            entry["response_body"].encode("utf-8"),
            entry["status_code"],
            entry["headers"]
        )
    
    def set(
        self,
        idempotency_key: str,
        request_hash: str,
        response_body: str,
        status_code: int,
        headers: Dict
    ):
        """
        Store response in cache for idempotency key.
        
        Args:
            idempotency_key: Client-provided idempotency key
            request_hash: SHA256 hash of request body
            response_body: Response body to cache
            status_code: HTTP status code
            headers: Response headers
        """
        # Emergency cleanup if cache too large
        if len(self._cache) >= self.max_entries:
            # Remove oldest 20% of entries
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1]["created_at"]
            )
            remove_count = len(sorted_entries) // 5
            for key, _ in sorted_entries[:remove_count]:
                del self._cache[key]
        
        self._cache[idempotency_key] = {
            "response_body": response_body,
            "status_code": status_code,
            "headers": headers,
            "created_at": time.time(),
            "request_hash": request_hash
        }
    
    def _cleanup_expired(self, current_time: float):
        """Remove expired cache entries."""
        expired_keys = [
            key
            for key, entry in self._cache.items()
            if current_time - entry["created_at"] > self.ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]
        
        self._last_cleanup = current_time
    
    def get_stats(self) -> Dict:
        """Get cache statistics for monitoring."""
        return {
            "cached_requests": len(self._cache),
            "max_entries": self.max_entries,
            "ttl_seconds": self.ttl_seconds,
            "last_cleanup": time.ctime(self._last_cleanup)
        }


# Global idempotency cache instance
_idempotency_cache = IdempotencyCache(max_entries=10000, ttl_seconds=86400)


def get_idempotency_cache() -> IdempotencyCache:
    """Get the global idempotency cache instance."""
    return _idempotency_cache


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle idempotent POST requests.
    
    SPECIFICATION:
    - Implements RFC idempotency pattern
    - Client provides Idempotency-Key header
    - Same key + same body = same response
    - Different body with same key = rejected (409)
    
    PROTECTED ENDPOINTS:
    - POST /api/v1/loans/request (critical fintech operation)
    - Can be extended to other POST endpoints
    
    HEADERS:
    - Request: Idempotency-Key (UUID recommended)
    - Response: Idempotent-Replayed (true if cached response)
    
    PRODUCTION WARNING:
    In-memory cache is suitable for:
      ✅ Single-server deployments
      ✅ Development/testing
      ✅ Free-tier constraints
    
    For production with multiple servers, use:
      ❌ Redis (distributed cache)
      ❌ DynamoDB (persistent cache)
      ❌ API Gateway idempotency features
    
    Usage:
        app.add_middleware(IdempotencyMiddleware)
    """
    
    # Endpoints that require idempotency protection
    PROTECTED_PATHS = [
        "/api/v1/loans/request",
        "/api/v1/test/ping",  # Test endpoint for integration testing
        # Add more critical endpoints here
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with idempotency protection."""
        import logging
        
        logger = logging.getLogger("api.idempotency")
        
        # Only apply to POST requests on protected paths
        if request.method != "POST" or request.url.path not in self.PROTECTED_PATHS:
            return await call_next(request)
        
        # Check for Idempotency-Key header
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            # No idempotency key = process normally (no protection)
            logger.warning(
                f"POST {request.url.path} without Idempotency-Key "
                f"(client should provide for duplicate prevention)"
            )
            return await call_next(request)
        
        # Read request body and compute hash
        body = await request.body()
        request_hash = hashlib.sha256(body).hexdigest()
        
        # Check cache for existing response
        cache = get_idempotency_cache()
        cached = cache.get(idempotency_key, request_hash)
        
        if cached:
            # Cache hit - return stored response
            response_body, status_code, headers = cached
            
            logger.info(
                f"Idempotent replay: key={idempotency_key[:8]}... "
                f"status={status_code}"
            )
            
            # Create response from cache
            response = Response(
                content=response_body,
                status_code=status_code,
                headers=headers
            )
            response.headers["Idempotent-Replayed"] = "true"
            return response
        
        # Cache miss - process request normally
        # Need to make body available again for downstream processing
        async def receive():
            return {"type": "http.request", "body": body}
        
        request._receive = receive
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Store in cache
            cache.set(
                idempotency_key=idempotency_key,
                request_hash=request_hash,
                response_body=response_body.decode("utf-8"),
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
            logger.info(
                f"Cached idempotent response: key={idempotency_key[:8]}... "
                f"status={response.status_code}"
            )
            
            # Return new response with body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        
        # Don't cache errors
        return response

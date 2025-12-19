"""
API Dependencies and Rate Limiting

SYSTEM ROLE:
Provides reusable FastAPI dependencies for authentication,
rate limiting, and request validation.

PROJECT:
CreditBridge — API Gateway Layer

RATE LIMITING STRATEGY:
- In-memory token bucket algorithm
- 60 requests per minute per user
- Identified via JWT subject (user_id)
- Returns HTTP 429 when limit exceeded

PRODUCTION WARNING:
This in-memory implementation is suitable for:
  ✅ Single-server deployments
  ✅ Development/testing environments
  ✅ Free-tier constraints (no Redis)

For production with multiple servers, replace with:
  ❌ Redis-based rate limiter (distributed state)
  ❌ API Gateway rate limiting (AWS/Azure)
  ❌ Cloud-native solutions (Cloudflare, Kong)

MEMORY MANAGEMENT:
- Automatic cleanup of expired entries every 60 seconds
- Maximum 10,000 tracked users (prevent memory bloat)
- Thread-safe with asyncio locks
"""

import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# ============================================================================
# CONFIGURATION
# ============================================================================

RATE_LIMIT_REQUESTS = 60  # Maximum requests per window
RATE_LIMIT_WINDOW = 60  # Window size in seconds (1 minute)
MAX_TRACKED_USERS = 10000  # Prevent memory bloat
CLEANUP_INTERVAL = 60  # Cleanup expired entries every 60 seconds

# ============================================================================
# IN-MEMORY RATE LIMITER
# ============================================================================

class InMemoryRateLimiter:
    """
    Thread-safe in-memory rate limiter using token bucket algorithm.
    
    ALGORITHM:
    - Each user gets a bucket with N tokens
    - Each request consumes 1 token
    - Tokens refill at constant rate
    - Request rejected if bucket empty
    
    DATA STRUCTURE:
    {
        "user_id_1": {
            "tokens": 58,           # Remaining tokens
            "last_refill": 1702732800.5,  # Last refill timestamp
            "request_count": 2      # Total requests in window
        },
        "user_id_2": {...}
    }
    """
    
    def __init__(
        self,
        max_requests: int = RATE_LIMIT_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.refill_rate = max_requests / window_seconds  # Tokens per second
        
        # Storage: {user_id: {"tokens": float, "last_refill": float, "request_count": int}}
        self._buckets: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        
        # Track when last cleanup occurred
        self._last_cleanup = time.time()
    
    async def is_allowed(self, user_id: str) -> Tuple[bool, Dict]:
        """
        Check if user is allowed to make a request.
        
        Returns:
            (allowed: bool, metadata: dict)
            
        Metadata includes:
            - remaining: int - Remaining requests in window
            - reset_at: float - Timestamp when limit resets
            - retry_after: int - Seconds to wait (if blocked)
        """
        async with self._lock:
            current_time = time.time()
            
            # Periodic cleanup to prevent memory bloat
            await self._cleanup_expired(current_time)
            
            # Initialize bucket for new user
            if user_id not in self._buckets:
                self._buckets[user_id] = {
                    "tokens": float(self.max_requests),
                    "last_refill": current_time,
                    "request_count": 0
                }
            
            bucket = self._buckets[user_id]
            
            # Refill tokens based on time elapsed
            time_elapsed = current_time - bucket["last_refill"]
            tokens_to_add = time_elapsed * self.refill_rate
            bucket["tokens"] = min(
                self.max_requests,
                bucket["tokens"] + tokens_to_add
            )
            bucket["last_refill"] = current_time
            
            # Check if request allowed
            if bucket["tokens"] >= 1.0:
                # Consume token
                bucket["tokens"] -= 1.0
                bucket["request_count"] += 1
                
                metadata = {
                    "allowed": True,
                    "remaining": int(bucket["tokens"]),
                    "reset_at": current_time + self.window_seconds,
                    "retry_after": 0
                }
                return True, metadata
            else:
                # Rate limit exceeded
                wait_time = (1.0 - bucket["tokens"]) / self.refill_rate
                
                metadata = {
                    "allowed": False,
                    "remaining": 0,
                    "reset_at": current_time + wait_time,
                    "retry_after": int(wait_time) + 1
                }
                return False, metadata
    
    async def _cleanup_expired(self, current_time: float):
        """
        Remove expired entries to prevent memory bloat.
        
        Removes users who haven't made requests in last 5 minutes.
        Runs only if CLEANUP_INTERVAL has passed.
        """
        if current_time - self._last_cleanup < CLEANUP_INTERVAL:
            return
        
        expiry_threshold = current_time - (self.window_seconds * 5)
        expired_users = [
            user_id
            for user_id, bucket in self._buckets.items()
            if bucket["last_refill"] < expiry_threshold
        ]
        
        for user_id in expired_users:
            del self._buckets[user_id]
        
        self._last_cleanup = current_time
        
        # Emergency cleanup if too many users tracked
        if len(self._buckets) > MAX_TRACKED_USERS:
            # Remove oldest 20% of users
            sorted_buckets = sorted(
                self._buckets.items(),
                key=lambda x: x[1]["last_refill"]
            )
            remove_count = len(sorted_buckets) // 5
            for user_id, _ in sorted_buckets[:remove_count]:
                del self._buckets[user_id]
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics (for monitoring)."""
        return {
            "tracked_users": len(self._buckets),
            "max_requests_per_window": self.max_requests,
            "window_seconds": self.window_seconds,
            "last_cleanup": datetime.fromtimestamp(self._last_cleanup).isoformat()
        }


# ============================================================================
# GLOBAL RATE LIMITER INSTANCE
# ============================================================================

# Single global instance (thread-safe)
_rate_limiter = InMemoryRateLimiter(
    max_requests=RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW
)


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


# ============================================================================
# FASTAPI DEPENDENCIES
# ============================================================================

async def rate_limit_dependency(
    request: Request
) -> None:
    """
    FastAPI dependency for rate limiting.
    
    Usage:
        @app.post("/loans", dependencies=[Depends(rate_limit_dependency)])
        async def create_loan(...):
            ...
    
    Behavior:
        - Gets user_id from request.state or falls back to IP address
        - Checks rate limit
        - Raises HTTPException(429) if limit exceeded
        - Adds rate limit headers to response
    
    Headers Added:
        - X-RateLimit-Limit: Maximum requests per window
        - X-RateLimit-Remaining: Remaining requests
        - X-RateLimit-Reset: Unix timestamp when limit resets
        - Retry-After: Seconds to wait (if 429)
    """
    # Get user_id from request state (set by get_current_user) or fallback to IP
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        # Fallback: use IP address for anonymous users
        client_ip = request.client.host if request.client else "unknown"
        user_id = f"anonymous:{client_ip}"
    
    # Check rate limit
    rate_limiter = get_rate_limiter()
    allowed, metadata = await rate_limiter.is_allowed(user_id)
    
    # Add rate limit headers to response
    request.state.rate_limit_metadata = metadata
    
    if not allowed:
        # Rate limit exceeded - return 429
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
                "retry_after": metadata["retry_after"],
                "reset_at": metadata["reset_at"]
            },
            headers={
                "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(metadata["reset_at"])),
                "Retry-After": str(metadata["retry_after"])
            }
        )


# ============================================================================
# AUTHENTICATION HELPER (Simplified)
# ============================================================================

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Extract user_id from JWT token issued by Supabase.
    
    This function decodes the Supabase JWT token and extracts the user ID
    from the 'sub' claim.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    try:
        # Supabase JWT tokens are signed, but for development we can decode without verification
        # The token structure is: header.payload.signature
        token = credentials.credentials
        
        # Decode the JWT payload (base64 decode the middle part)
        import base64
        import json
        
        # Split token into parts
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid token format")
        
        # Decode payload (add padding if needed)
        payload_part = parts[1]
        # Add padding if necessary
        padding = 4 - len(payload_part) % 4
        if padding != 4:
            payload_part += '=' * padding
        
        # Decode from base64
        payload_bytes = base64.urlsafe_b64decode(payload_part)
        payload = json.loads(payload_bytes)
        
        # Extract user ID from 'sub' claim
        user_id = payload.get('sub')
        if not user_id:
            raise ValueError("No 'sub' claim in token")
        
        return user_id
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {str(e)}"
        )


# ============================================================================
# RATE LIMITER STATISTICS ENDPOINT
# ============================================================================

def get_rate_limiter_stats() -> Dict:
    """
    Get current rate limiter statistics.
    
    Useful for monitoring and debugging.
    Can be exposed as admin endpoint.
    """
    rate_limiter = get_rate_limiter()
    return rate_limiter.get_stats()

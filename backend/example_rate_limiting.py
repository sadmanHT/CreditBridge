"""
Example: Rate Limiting Integration with FastAPI

This example shows how to integrate the rate limiter
with your FastAPI application.

SETUP INSTRUCTIONS:
1. Import middleware and dependencies
2. Add middleware to FastAPI app
3. Add dependencies to protected endpoints
4. Optional: Add statistics endpoint
"""

from fastapi import FastAPI, Depends, Request
from app.api.middleware import RateLimitHeaderMiddleware, RequestLoggingMiddleware
from app.api.deps import rate_limit_dependency, get_rate_limiter_stats

# ============================================================================
# STEP 1: Create FastAPI App
# ============================================================================

app = FastAPI(
    title="CreditBridge API",
    description="Fintech API with rate limiting",
    version="1.0.0"
)

# ============================================================================
# STEP 2: Add Middleware (applies to all routes)
# ============================================================================

# Add rate limit headers to all responses
app.add_middleware(RateLimitHeaderMiddleware)

# Optional: Add request logging
app.add_middleware(RequestLoggingMiddleware)

# ============================================================================
# STEP 3: Protected Endpoints (with rate limiting)
# ============================================================================

@app.post("/api/v1/loans/request", dependencies=[Depends(rate_limit_dependency)])
async def create_loan_request(request: Request):
    """
    Protected endpoint with rate limiting.
    
    - Maximum 60 requests per minute per user
    - Returns 429 if limit exceeded
    - Rate limit headers included in response
    """
    return {"message": "Loan request created"}


@app.get("/api/v1/borrowers/profile", dependencies=[Depends(rate_limit_dependency)])
async def get_borrower_profile(request: Request):
    """Another protected endpoint."""
    return {"message": "Borrower profile"}


# ============================================================================
# STEP 4: Public Endpoints (no rate limiting)
# ============================================================================

@app.get("/health")
async def health_check():
    """Public health check (no rate limiting)."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Public root endpoint."""
    return {"message": "CreditBridge API"}


# ============================================================================
# STEP 5: Admin/Monitoring Endpoints
# ============================================================================

@app.get("/admin/rate-limit-stats")
async def rate_limit_statistics():
    """
    Get rate limiter statistics.
    
    Returns:
        - tracked_users: Number of users being tracked
        - max_requests_per_window: Maximum requests allowed
        - window_seconds: Window size in seconds
        - last_cleanup: Last cleanup timestamp
    
    Example Response:
    {
        "tracked_users": 42,
        "max_requests_per_window": 60,
        "window_seconds": 60,
        "last_cleanup": "2024-12-16T10:30:00"
    }
    """
    return get_rate_limiter_stats()


# ============================================================================
# EXAMPLE: Per-Endpoint Rate Limiting (Different Limits)
# ============================================================================

from app.api.deps import InMemoryRateLimiter

# Create custom rate limiter for expensive operations
strict_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)

async def strict_rate_limit(request: Request):
    """Stricter rate limit for expensive operations (10/minute)."""
    user_id = getattr(request.state, "user_id", "anonymous")
    allowed, metadata = await strict_limiter.is_allowed(user_id)
    
    if not allowed:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {metadata['retry_after']}s",
            headers={"Retry-After": str(metadata["retry_after"])}
        )

@app.post("/api/v1/ai/credit-score", dependencies=[Depends(strict_rate_limit)])
async def compute_credit_score():
    """
    Expensive AI operation with stricter rate limit.
    
    - Maximum 10 requests per minute
    - More CPU/memory intensive
    """
    return {"credit_score": 750}


# ============================================================================
# EXAMPLE: Conditional Rate Limiting (Based on User Tier)
# ============================================================================

async def tiered_rate_limit(request: Request):
    """
    Apply different rate limits based on user tier.
    
    Tiers:
    - Free: 60/minute
    - Premium: 600/minute
    - Enterprise: No limit
    """
    user_id = getattr(request.state, "user_id", "anonymous")
    user_tier = getattr(request.state, "user_tier", "free")  # Set by auth middleware
    
    if user_tier == "enterprise":
        # No rate limiting for enterprise users
        return
    
    # Select appropriate limiter
    from app.api.deps import get_rate_limiter
    if user_tier == "premium":
        # Create premium limiter if needed
        premium_limiter = InMemoryRateLimiter(max_requests=600, window_seconds=60)
        allowed, metadata = await premium_limiter.is_allowed(user_id)
    else:
        # Use default free tier limiter
        default_limiter = get_rate_limiter()
        allowed, metadata = await default_limiter.is_allowed(user_id)
    
    if not allowed:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Retry after {metadata['retry_after']}s"
        )

@app.get("/api/v1/premium/analytics", dependencies=[Depends(tiered_rate_limit)])
async def premium_analytics():
    """Premium endpoint with tiered rate limiting."""
    return {"analytics": "data"}


# ============================================================================
# RUNNING THE APPLICATION
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("="*80)
    print("Starting CreditBridge API with Rate Limiting")
    print("="*80)
    print("Rate Limit: 60 requests per minute per user")
    print("Protected Endpoints:")
    print("  - POST /api/v1/loans/request")
    print("  - GET /api/v1/borrowers/profile")
    print("  - POST /api/v1/ai/credit-score (10/minute)")
    print()
    print("Public Endpoints:")
    print("  - GET /health")
    print("  - GET /")
    print()
    print("Admin Endpoints:")
    print("  - GET /admin/rate-limit-stats")
    print("="*80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================================
# TESTING EXAMPLES
# ============================================================================

"""
# Test rate limiting with curl:

# 1. Health check (no rate limit)
curl http://localhost:8000/health

# 2. Make protected request (observe headers)
curl -i http://localhost:8000/api/v1/loans/request \
  -X POST \
  -H "Authorization: Bearer <token>"

# Expected headers:
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 59
# X-RateLimit-Reset: 1702732860

# 3. Exhaust rate limit (make 61 requests)
for i in {1..61}; do
  curl http://localhost:8000/api/v1/loans/request \
    -X POST \
    -H "Authorization: Bearer <token>"
done

# 61st request should return:
# HTTP 429 Too Many Requests
# Retry-After: 5

# 4. Check statistics
curl http://localhost:8000/admin/rate-limit-stats

# Expected response:
# {
#   "tracked_users": 1,
#   "max_requests_per_window": 60,
#   "window_seconds": 60,
#   "last_cleanup": "2024-12-16T10:30:00"
# }
"""

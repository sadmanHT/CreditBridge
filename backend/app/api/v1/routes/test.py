"""
Test Routes for Integration Testing

Simple endpoints for testing middleware without complex business logic.
"""

from fastapi import APIRouter, Depends
from app.api.deps import rate_limit_dependency

router = APIRouter(prefix="/test")


@router.post("/ping", dependencies=[Depends(rate_limit_dependency)])
async def test_ping():
    """
    Simple test endpoint for rate limiting and idempotency testing.
    Returns a simple response without complex business logic.
    """
    return {
        "status": "success",
        "message": "pong",
        "timestamp": "2025-12-17T00:00:00Z"
    }

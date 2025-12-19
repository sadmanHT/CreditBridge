"""
Health Check Endpoint

Used to verify that the CreditBridge backend is alive.
Required for monitoring, deployment readiness, and compliance checks.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and readiness probes.
    
    Returns:
        dict: Service status and version information
    """
    return {
        "status": "ok",
        "service": "CreditBridge Backend",
        "api_version": "v1"
    }

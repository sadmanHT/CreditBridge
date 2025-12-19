"""
API Version v1 Router

This module aggregates all v1 routes for CreditBridge.
Each feature (health, credit, fraud, explainability, compliance, ingestion)
will be registered here.
"""

from fastapi import APIRouter
from app.api.v1.routes import health, auth, borrowers, loans, compliance, explanations, ingestion, test, dashboard, regulatory

api_router = APIRouter(prefix="/api/v1")

# Include all route modules
api_router.include_router(
    health.router,
    tags=["Health Check"]
)

api_router.include_router(
    auth.router,
    tags=["Authentication"]
)

api_router.include_router(
    borrowers.router,
    tags=["Borrowers"]
)

api_router.include_router(
    loans.router,
    tags=["Loans"]
)

api_router.include_router(
    compliance.router,
    tags=["Compliance & Audit"]
)

api_router.include_router(
    explanations.router,
    tags=["Explainability"]
)

api_router.include_router(
    ingestion.router,
    tags=["Event Ingestion"]
)

api_router.include_router(
    dashboard.router,
    tags=["Dashboards"]
)

api_router.include_router(
    regulatory.router,
    tags=["Regulatory"]
)

api_router.include_router(
    test.router,
    tags=["Testing"]
)
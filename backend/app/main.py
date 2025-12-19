"""
CreditBridge Backend - API Gateway

This module is the main entry point for the CreditBridge backend.
It initializes the FastAPI application and mounts versioned APIs.

Design goals:
- Versioned API support (/api/v1)
- Clean separation of routes
- Ready for credit scoring, fraud detection, explainability, and compliance modules
- Rate limiting protection (60 requests/minute per user)
- Idempotency guarantees for critical operations
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.api.middleware import (
    RateLimitHeaderMiddleware,
    RequestLoggingMiddleware,
    IdempotencyMiddleware
)

app = FastAPI(
    title="CreditBridge API Gateway",
    description="AI-Powered Credit Scoring Platform for Financial Inclusion",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS CONFIGURATION
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================================================
# MIDDLEWARE REGISTRATION (Order matters - executed in reverse order)
# ============================================================================

# 1. Idempotency protection (innermost - closest to endpoint)
#    Prevents duplicate loan requests using Idempotency-Key header
app.add_middleware(IdempotencyMiddleware)

# 2. Rate limit headers (adds X-RateLimit-* headers to responses)
app.add_middleware(RateLimitHeaderMiddleware)

# 3. Request logging (outermost - logs all requests)
app.add_middleware(RequestLoggingMiddleware)

# ============================================================================
# API ROUTES
# ============================================================================

# Include versioned API routes
app.include_router(api_router)

@app.get("/")
async def root():
    """Root endpoint - API Gateway information"""
    return {
        "project": "CreditBridge",
        "layer": "API Gateway",
        "version": "v1"
    }

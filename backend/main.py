"""
CreditBridge API Gateway
======================
This is the main API Gateway for the CreditBridge project - an AI-powered 
credit scoring platform for financial inclusion.

This gateway exposes endpoints for:
- Credit scoring
- Fraud detection
- AI explainability (SHAP)
- Compliance and monitoring
"""

from fastapi import FastAPI

app = FastAPI(
    title="CreditBridge API",
    description="AI-Powered Credit Scoring for Financial Inclusion",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint returning project status"""
    return {
        "project": "CreditBridge",
        "status": "Backend is running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "ok"}

"""
Background Tasks for CreditBridge

Provides asynchronous task execution without blocking API requests.

Components:
- feature_tasks: Feature computation tasks
- runner: Task execution utilities

Usage:
    from app.background import trigger_feature_computation
    from fastapi import BackgroundTasks
    
    @app.post("/loan-application")
    async def submit_application(
        borrower_id: str,
        background_tasks: BackgroundTasks
    ):
        trigger_feature_computation(background_tasks, borrower_id)
        return {"status": "accepted"}
"""

from .feature_tasks import compute_features_async, compute_features_batch
from .runner import run_background_task, trigger_feature_computation

__all__ = [
    "compute_features_async",
    "compute_features_batch",
    "run_background_task",
    "trigger_feature_computation"
]

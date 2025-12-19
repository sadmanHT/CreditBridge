"""
Background Task Runner Utilities

Provides utilities for executing and monitoring background tasks.

SYSTEM ROLE:
You are providing a safe abstraction for running background jobs
inside a FastAPI service.

PROJECT:
CreditBridge — Background Job Runner.

Features:
- Task execution wrapper
- Error handling and logging
- Task status tracking
- Performance monitoring
- FastAPI BackgroundTasks integration

Usage:
    from app.background.runner import trigger_feature_computation
    from fastapi import BackgroundTasks
    
    # Trigger feature computation in background
    trigger_feature_computation(background_tasks, borrower_id="borrower-123")
"""

import logging
import time
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from functools import wraps


# Configure logger
logger = logging.getLogger(__name__)


def run_background_task(
    task_func: Callable,
    task_name: str,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute a background task with comprehensive error handling and monitoring.
    
    Wraps background tasks to provide:
    - Automatic error handling
    - Execution time tracking
    - Comprehensive logging
    - Status reporting
    
    Args:
        task_func: Function to execute in background
        task_name: Human-readable task name for logging
        *args: Positional arguments for task_func
        **kwargs: Keyword arguments for task_func
    
    Returns:
        Dict containing:
        - status: "success" or "error"
        - task_name: Name of executed task
        - execution_time_ms: Task execution time in milliseconds
        - started_at: Task start timestamp
        - completed_at: Task completion timestamp
        - result: Task result if successful
        - error: Error message if failed
    
    Example:
        >>> from app.background.feature_tasks import compute_features_async
        >>> result = run_background_task(
        ...     task_func=compute_features_async,
        ...     task_name="compute_features",
        ...     borrower_id="borrower-123"
        ... )
    """
    started_at = datetime.utcnow()
    start_time = time.time()
    
    logger.info(f"Starting background task: {task_name}")
    
    try:
        # Execute task
        result = task_func(*args, **kwargs)
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        completed_at = datetime.utcnow()
        
        logger.info(
            f"Background task completed: {task_name} "
            f"(execution_time={execution_time_ms:.2f}ms)"
        )
        
        return {
            "status": "success",
            "task_name": task_name,
            "execution_time_ms": round(execution_time_ms, 2),
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "result": result
        }
        
    except Exception as e:
        # Calculate execution time even on error
        execution_time_ms = (time.time() - start_time) * 1000
        completed_at = datetime.utcnow()
        
        logger.error(
            f"Background task failed: {task_name} "
            f"(execution_time={execution_time_ms:.2f}ms, error={str(e)})",
            exc_info=True
        )
        
        return {
            "status": "error",
            "task_name": task_name,
            "execution_time_ms": round(execution_time_ms, 2),
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "error": str(e),
            "error_type": type(e).__name__
        }


def background_task(task_name: Optional[str] = None):
    """
    Decorator for marking functions as background tasks.
    
    Automatically wraps function with error handling and logging.
    
    Args:
        task_name: Optional task name (defaults to function name)
    
    Example:
        >>> @background_task("compute_features")
        >>> def compute_features_async(borrower_id: str):
        ...     # Task implementation
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = task_name or func.__name__
            return run_background_task(func, name, *args, **kwargs)
        return wrapper
    return decorator


class TaskMonitor:
    """
    Monitor for tracking background task execution.
    
    Provides:
    - Task execution history
    - Performance metrics
    - Error tracking
    
    Usage:
        >>> monitor = TaskMonitor()
        >>> monitor.record_task_start("compute_features", "borrower-123")
        >>> # ... task execution ...
        >>> monitor.record_task_complete("compute_features", "borrower-123", result)
    """
    
    def __init__(self):
        """Initialize task monitor."""
        self.tasks = {}
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time_ms": 0.0
        }
    
    def record_task_start(self, task_name: str, task_id: str) -> None:
        """
        Record task start.
        
        Args:
            task_name: Name of task
            task_id: Unique task identifier (e.g., borrower_id)
        """
        self.tasks[task_id] = {
            "task_name": task_name,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "start_time": time.time()
        }
        
        logger.info(f"Task started: {task_name} (id={task_id})")
    
    def record_task_complete(
        self,
        task_id: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Record task completion.
        
        Args:
            task_id: Unique task identifier
            result: Task result dictionary
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found in monitor")
            return
        
        task = self.tasks[task_id]
        execution_time_ms = (time.time() - task["start_time"]) * 1000
        
        task["status"] = result.get("status", "unknown")
        task["completed_at"] = datetime.utcnow().isoformat()
        task["execution_time_ms"] = round(execution_time_ms, 2)
        task["result"] = result
        
        # Update metrics
        self.metrics["total_tasks"] += 1
        self.metrics["total_execution_time_ms"] += execution_time_ms
        
        if result.get("status") == "success":
            self.metrics["successful_tasks"] += 1
        else:
            self.metrics["failed_tasks"] += 1
        
        logger.info(
            f"Task completed: {task['task_name']} (id={task_id}, "
            f"status={task['status']}, execution_time={execution_time_ms:.2f}ms)"
        )
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific task.
        
        Args:
            task_id: Unique task identifier
        
        Returns:
            Task status dictionary or None if not found
        """
        return self.tasks.get(task_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get overall task execution metrics.
        
        Returns:
            Dict containing:
            - total_tasks: Total number of tasks executed
            - successful_tasks: Number of successful tasks
            - failed_tasks: Number of failed tasks
            - total_execution_time_ms: Total execution time
            - average_execution_time_ms: Average execution time per task
            - success_rate: Success rate percentage
        """
        avg_time = (
            self.metrics["total_execution_time_ms"] / self.metrics["total_tasks"]
            if self.metrics["total_tasks"] > 0
            else 0.0
        )
        
        success_rate = (
            (self.metrics["successful_tasks"] / self.metrics["total_tasks"]) * 100
            if self.metrics["total_tasks"] > 0
            else 0.0
        )
        
        return {
            **self.metrics,
            "average_execution_time_ms": round(avg_time, 2),
            "success_rate": round(success_rate, 2)
        }
    
    def clear_history(self) -> None:
        """Clear task history and reset metrics."""
        self.tasks.clear()
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time_ms": 0.0
        }
        logger.info("Task history cleared")


# Global task monitor instance
_task_monitor = TaskMonitor()


def get_task_monitor() -> TaskMonitor:
    """
    Get global task monitor instance.
    
    Returns:
        TaskMonitor: Global task monitor
    """
    return _task_monitor


def trigger_feature_computation(
    background_tasks: Any,
    borrower_id: str,
    feature_set: str = "core_behavioral",
    feature_version: str = "v1"
) -> None:
    """
    Trigger background feature computation for a borrower.
    
    SYSTEM ROLE:
    Safe abstraction for running background feature computation
    inside a FastAPI service.
    
    This helper function adds compute_features_async to FastAPI BackgroundTasks
    with explicit logging and no blocking behavior.
    
    Args:
        background_tasks: FastAPI BackgroundTasks instance
        borrower_id: UUID of borrower to compute features for
        feature_set: Feature set name (default: "core_behavioral")
        feature_version: Feature version (default: "v1")
    
    Example:
        >>> from fastapi import BackgroundTasks
        >>> from app.background.runner import trigger_feature_computation
        >>> 
        >>> @app.post("/loan-application")
        >>> async def submit_application(
        ...     borrower_id: str,
        ...     background_tasks: BackgroundTasks
        ... ):
        ...     # Trigger feature computation in background
        ...     trigger_feature_computation(background_tasks, borrower_id)
        ...     return {"status": "accepted"}
    
    Features:
    - No blocking behavior (returns immediately)
    - Explicit logging for monitoring
    - Automatic error handling via compute_features_async
    - Compatible with FastAPI BackgroundTasks
    """
    from app.background.feature_tasks import compute_features_async
    
    logger.info(
        f"Triggering background feature computation: "
        f"borrower_id={borrower_id}, feature_set={feature_set}, version={feature_version}"
    )
    
    # Add task to background queue (non-blocking)
    background_tasks.add_task(
        compute_features_async,
        borrower_id=borrower_id,
        feature_set=feature_set,
        feature_version=feature_version
    )
    
    logger.info(f"Background task queued for borrower {borrower_id}")


"""
SYSTEM ROLE:
You are implementing background feature computation
for a high-throughput fintech API.

PROJECT:
CreditBridge — Asynchronous Feature Pipeline.

TASK:
Implement a background task that computes and stores features
without blocking API requests.

Architecture:
- Async-compatible but runs synchronously
- FastAPI BackgroundTasks compatible
- Fetches borrower + events from database
- Computes features using FeatureEngine
- Persists to feature store
- Marks events as processed

Features:
- Non-blocking API execution
- Safe error handling (no crashes)
- Deterministic behavior
- Automatic event processing tracking
- Comprehensive logging

CONSTRAINTS:
- No Celery / paid queues
- Use FastAPI BackgroundTasks compatible logic
- Deterministic behavior only
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core import repository as repo
from app.features.engine import FeatureEngine


# Configure logger
logger = logging.getLogger(__name__)


def compute_features_async(
    borrower_id: str,
    feature_set: str = "core_behavioral",
    feature_version: str = "v1"
) -> Dict[str, Any]:
    """
    Compute and store features for a borrower asynchronously.
    
    This function is designed to run in background without blocking API requests.
    Compatible with FastAPI BackgroundTasks.
    
    Workflow:
    1. Fetch borrower profile from database
    2. Fetch recent unprocessed raw_events
    3. Compute features using FeatureEngine
    4. Persist features to model_features table
    5. Mark raw_events as processed
    6. Return status summary
    
    Args:
        borrower_id: UUID of borrower
        feature_set: Feature set name (default: "core_behavioral")
        feature_version: Feature version (default: "v1")
    
    Returns:
        Dict containing:
        - status: "success" or "error"
        - borrower_id: Borrower UUID
        - features_computed: Number of features computed
        - events_processed: Number of events marked as processed
        - feature_set: Feature set name
        - feature_version: Feature version
        - computed_at: Timestamp
        - error: Error message if failed
    
    Example:
        >>> from fastapi import BackgroundTasks
        >>> background_tasks.add_task(compute_features_async, "borrower-123")
    
    Error Handling:
        - Catches all exceptions to prevent background task crashes
        - Logs errors for monitoring
        - Returns error status for tracking
    """
    logger.info(f"Starting background feature computation for borrower {borrower_id}")
    
    try:
        # ═══════════════════════════════════════════════════════════
        # STEP 1: Initialize feature engine
        # ═══════════════════════════════════════════════════════════
        feature_engine = FeatureEngine()
        
        logger.info(f"FeatureEngine initialized")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 2: Fetch borrower profile (MOCK - implement when DB ready)
        # ═══════════════════════════════════════════════════════════
        try:
            # TODO: Implement get_borrower_by_id in repository
            # borrower = repo.get_borrower_by_id(borrower_id)
            
            # For now, return placeholder to demonstrate logic
            borrower = {"id": borrower_id, "region": "Dhaka"}
            
            if not borrower:
                logger.warning(f"Borrower {borrower_id} not found")
                return {
                    "status": "error",
                    "borrower_id": borrower_id,
                    "error": "Borrower not found",
                    "computed_at": datetime.utcnow().isoformat()
                }
            
            logger.info(f"Fetched borrower profile for {borrower_id}")
            
        except Exception as e:
            logger.error(f"Failed to fetch borrower {borrower_id}: {e}")
            return {
                "status": "error",
                "borrower_id": borrower_id,
                "error": f"Failed to fetch borrower: {str(e)}",
                "computed_at": datetime.utcnow().isoformat()
            }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 3: Fetch recent unprocessed raw_events (MOCK - implement when DB ready)
        # ═══════════════════════════════════════════════════════════
        try:
            # TODO: Implement get_unprocessed_events in repository
            # raw_events = repo.get_unprocessed_events(borrower_id=borrower_id, limit=1000)
            
            # For now, return empty list to demonstrate logic
            raw_events = []
            
            if not raw_events:
                logger.info(f"No unprocessed events for borrower {borrower_id}")
                return {
                    "status": "success",
                    "borrower_id": borrower_id,
                    "features_computed": 0,
                    "events_processed": 0,
                    "message": "No unprocessed events found",
                    "computed_at": datetime.utcnow().isoformat()
                }
            
            logger.info(f"Fetched {len(raw_events)} unprocessed events for {borrower_id}")
            
        except Exception as e:
            logger.error(f"Failed to fetch events for {borrower_id}: {e}")
            return {
                "status": "error",
                "borrower_id": borrower_id,
                "error": f"Failed to fetch events: {str(e)}",
                "computed_at": datetime.utcnow().isoformat()
            }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 4: Transform events to FeatureEngine format
        # ═══════════════════════════════════════════════════════════
        events_for_computation = []
        event_ids = []
        
        for event in raw_events:
            # Extract event_id for tracking
            event_ids.append(event.get("id"))
            
            # Transform to FeatureEngine format
            events_for_computation.append({
                "event_type": event.get("event_type"),
                "timestamp": event.get("created_at"),
                **event.get("event_data", {})  # Merge event_data fields
            })
        
        logger.info(f"Transformed {len(events_for_computation)} events for computation")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 5: Compute features using FeatureEngine
        # ═══════════════════════════════════════════════════════════
        try:
            feature_result = feature_engine.compute_features(
                borrower_id=borrower_id,
                events=events_for_computation,
                feature_set=feature_set,
                feature_version=feature_version
            )
            
            logger.info(
                f"Computed {len(feature_result['features'])} features for {borrower_id}: "
                f"{list(feature_result['features'].keys())}"
            )
            
        except Exception as e:
            logger.error(f"Feature computation failed for {borrower_id}: {e}")
            # Mark events as processed with error note
            _mark_events_processed(
                repository, 
                event_ids, 
                f"Feature computation failed: {str(e)}"
            )
            return {
                "status": "error",
                "borrower_id": borrower_id,
                "error": f"Feature computation failed: {str(e)}",
                "events_processed": len(event_ids),
                "computed_at": datetime.utcnow().isoformat()
            }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 6: Persist features to feature store
        # ═══════════════════════════════════════════════════════════
        try:
            saved_features = repo.save_model_features(
                borrower_id=borrower_id,
                feature_set=feature_result["feature_set"],
                feature_version=feature_result["feature_version"],
                features=feature_result["features"],
                computed_at=feature_result["computed_at"],
                source_event_count=len(event_ids)
            )
            
            logger.info(
                f"Persisted features to feature store for {borrower_id}: "
                f"feature_set={feature_result['feature_set']}, "
                f"version={feature_result['feature_version']}"
            )
            
        except Exception as e:
            logger.error(f"Failed to persist features for {borrower_id}: {e}")
            # Mark events as processed with error note
            _mark_events_processed(
                event_ids,
                f"Feature persistence failed: {str(e)}"
            )
            return {
                "status": "error",
                "borrower_id": borrower_id,
                "error": f"Feature persistence failed: {str(e)}",
                "features_computed": len(feature_result["features"]),
                "events_processed": len(event_ids),
                "computed_at": datetime.utcnow().isoformat()
            }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 7: Mark raw_events as processed
        # ═══════════════════════════════════════════════════════════
        processed_count = _mark_events_processed(
            event_ids,
            f"Features computed successfully: {feature_result['feature_set']} v{feature_result['feature_version']}"
        )
        
        logger.info(f"Marked {processed_count} events as processed for {borrower_id}")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 8: Return success status
        # ═══════════════════════════════════════════════════════════
        return {
            "status": "success",
            "borrower_id": borrower_id,
            "features_computed": len(feature_result["features"]),
            "events_processed": processed_count,
            "feature_set": feature_result["feature_set"],
            "feature_version": feature_result["feature_version"],
            "computed_at": feature_result["computed_at"],
            "feature_names": list(feature_result["features"].keys())
        }
        
    except Exception as e:
        # Catch-all for any unexpected errors
        logger.error(f"Unexpected error in background feature computation for {borrower_id}: {e}", exc_info=True)
        return {
            "status": "error",
            "borrower_id": borrower_id,
            "error": f"Unexpected error: {str(e)}",
            "computed_at": datetime.utcnow().isoformat()
        }


def _mark_events_processed(
    event_ids: List[str],
    processing_note: str
) -> int:
    """
    Mark raw_events as processed in database.
    
    Helper function to update event processing status.
    
    Args:
        event_ids: List of event IDs to mark as processed
        processing_note: Note describing processing outcome
    
    Returns:
        Number of events successfully marked as processed
    """
    processed_count = 0
    
    for event_id in event_ids:
        try:
            # TODO: Implement mark_event_processed in repository
            # repo.mark_event_processed(
            #     event_id=event_id,
            #     processing_note=processing_note
            # )
            
            # For now, just count (demonstrates logic flow)
            processed_count += 1
            
        except Exception as e:
            logger.error(f"Failed to mark event {event_id} as processed: {e}")
            # Continue processing other events
            continue
    
    return processed_count


def compute_features_batch(
    borrower_ids: List[str],
    feature_set: str = "core_behavioral",
    feature_version: str = "v1"
) -> Dict[str, Any]:
    """
    Compute features for multiple borrowers in batch.
    
    Useful for bulk feature computation or scheduled jobs.
    
    Args:
        borrower_ids: List of borrower UUIDs
        feature_set: Feature set name (default: "core_behavioral")
        feature_version: Feature version (default: "v1")
    
    Returns:
        Dict containing:
        - total_borrowers: Total number of borrowers processed
        - successful: Number of successful computations
        - failed: Number of failed computations
        - results: List of individual results
    """
    logger.info(f"Starting batch feature computation for {len(borrower_ids)} borrowers")
    
    results = []
    successful = 0
    failed = 0
    
    for borrower_id in borrower_ids:
        result = compute_features_async(
            borrower_id=borrower_id,
            feature_set=feature_set,
            feature_version=feature_version
        )
        
        results.append(result)
        
        if result["status"] == "success":
            successful += 1
        else:
            failed += 1
    
    logger.info(
        f"Batch computation complete: {successful} successful, {failed} failed"
    )
    
    return {
        "total_borrowers": len(borrower_ids),
        "successful": successful,
        "failed": failed,
        "results": results,
        "computed_at": datetime.utcnow().isoformat()
    }

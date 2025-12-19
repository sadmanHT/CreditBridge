"""
Event Processing Utilities for CreditBridge

SYSTEM ROLE:
You are implementing safe event processing utilities
for an AI data pipeline.

PROJECT:
CreditBridge — Event Processing Core.

TASK FOR COPILOT AGENT:
Implement helper functions to manage event processing state.

REQUIREMENTS:
1. mark_event_processed(event_id, notes=None)
2. mark_event_failed(event_id, error_message)
3. Update processed, processed_at, processing_notes
4. Use Supabase repository
5. Deterministic and explicit behavior

These utilities provide:
- State management for raw_events table
- Explicit success/failure tracking
- Audit trail via processing_notes
- Timestamp tracking for processing completion
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.core.supabase import supabase
from app.core.repository import log_audit_event


def mark_event_processed(
    event_id: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Mark an event as successfully processed.
    
    This function provides deterministic state updates for events that have been
    successfully processed by the data pipeline. It explicitly sets:
    - processed = True
    - processed_at = current UTC timestamp
    - processing_notes = optional success message
    
    Args:
        event_id: UUID of the event in raw_events table
        notes: Optional notes about processing (e.g., "Extracted 5 features")
        
    Returns:
        Dictionary containing:
        - event_id: UUID of the processed event
        - processed: True
        - processed_at: ISO timestamp of processing completion
        - processing_notes: Notes about processing
        - status: "success"
        
    Raises:
        ValueError: If event_id is empty or None
        Exception: If database update fails
        
    Example:
        >>> result = mark_event_processed(
        ...     event_id="abc-123",
        ...     notes="Successfully extracted borrower features"
        ... )
        >>> print(result["status"])  # "success"
    """
    # Input validation
    if not event_id:
        raise ValueError("event_id cannot be None or empty")
    
    try:
        # Get current UTC timestamp
        processed_at = datetime.now(timezone.utc).isoformat()
        
        # Prepare update payload with explicit field values
        update_payload = {
            "processed": True,
            "processed_at": processed_at,
            "processing_notes": notes or "Event processed successfully"
        }
        
        # Execute update on raw_events table
        response = supabase.table("raw_events").update(update_payload).eq("id", event_id).execute()
        
        if not response.data:
            raise Exception(f"Failed to update event {event_id}: No data returned from database")
        
        updated_event = response.data[0]
        
        # Log audit event for compliance tracking
        log_audit_event(
            action="event_marked_processed",
            entity_type="raw_event",
            entity_id=event_id,
            metadata={
                "processed": True,
                "processed_at": processed_at,
                "processing_notes": notes
            }
        )
        
        return {
            "event_id": event_id,
            "processed": True,
            "processed_at": processed_at,
            "processing_notes": update_payload["processing_notes"],
            "status": "success"
        }
        
    except ValueError:
        raise
    except Exception as e:
        # Re-raise with context
        raise Exception(f"Failed to mark event {event_id} as processed: {str(e)}")


def mark_event_failed(
    event_id: str,
    error_message: str
) -> Dict[str, Any]:
    """
    Mark an event as failed during processing.
    
    This function provides deterministic state updates for events that failed
    during pipeline processing. It explicitly sets:
    - processed = False (remains unprocessed)
    - processed_at = current UTC timestamp (when failure occurred)
    - processing_notes = error message with "FAILED:" prefix
    
    Args:
        event_id: UUID of the event in raw_events table
        error_message: Description of the failure (required)
        
    Returns:
        Dictionary containing:
        - event_id: UUID of the failed event
        - processed: False
        - processed_at: ISO timestamp of failure
        - processing_notes: Error message with FAILED prefix
        - status: "failed"
        
    Raises:
        ValueError: If event_id or error_message is empty/None
        Exception: If database update fails
        
    Example:
        >>> result = mark_event_failed(
        ...     event_id="abc-123",
        ...     error_message="Missing required field: borrower_id"
        ... )
        >>> print(result["status"])  # "failed"
    """
    # Input validation
    if not event_id:
        raise ValueError("event_id cannot be None or empty")
    
    if not error_message:
        raise ValueError("error_message cannot be None or empty")
    
    try:
        # Get current UTC timestamp
        processed_at = datetime.now(timezone.utc).isoformat()
        
        # Prepare failure notes with explicit prefix
        failure_notes = f"FAILED: {error_message}"
        
        # Prepare update payload with explicit field values
        # IMPORTANT: processed remains False for failed events
        update_payload = {
            "processed": False,
            "processed_at": processed_at,
            "processing_notes": failure_notes
        }
        
        # Execute update on raw_events table
        response = supabase.table("raw_events").update(update_payload).eq("id", event_id).execute()
        
        if not response.data:
            raise Exception(f"Failed to update event {event_id}: No data returned from database")
        
        updated_event = response.data[0]
        
        # Log audit event for compliance tracking
        log_audit_event(
            action="event_marked_failed",
            entity_type="raw_event",
            entity_id=event_id,
            metadata={
                "processed": False,
                "processed_at": processed_at,
                "error_message": error_message,
                "processing_notes": failure_notes
            }
        )
        
        return {
            "event_id": event_id,
            "processed": False,
            "processed_at": processed_at,
            "processing_notes": failure_notes,
            "error_message": error_message,
            "status": "failed"
        }
        
    except ValueError:
        raise
    except Exception as e:
        # Re-raise with context
        raise Exception(f"Failed to mark event {event_id} as failed: {str(e)}")


def get_unprocessed_events(
    limit: int = 100,
    schema_version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve unprocessed events from raw_events table.
    
    This function provides a safe way to fetch events that need processing.
    Useful for batch processing pipelines.
    
    Args:
        limit: Maximum number of events to retrieve (default 100)
        schema_version: Optional filter by schema version (e.g., "v1", "v2")
        
    Returns:
        Dictionary containing:
        - total: Number of unprocessed events retrieved
        - events: List of event records
        - schema_version: Filter applied (if any)
        
    Raises:
        ValueError: If limit is invalid
        Exception: If database query fails
        
    Example:
        >>> result = get_unprocessed_events(limit=50, schema_version="v1")
        >>> print(f"Found {result['total']} unprocessed v1 events")
    """
    # Input validation
    if limit <= 0 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000")
    
    try:
        # Build query for unprocessed events
        query = supabase.table("raw_events").select("*").eq("processed", False)
        
        # Apply optional schema version filter
        if schema_version:
            query = query.eq("schema_version", schema_version)
        
        # Execute query with ordering and limit
        response = query.order("created_at", desc=False).limit(limit).execute()
        
        return {
            "total": len(response.data),
            "events": response.data,
            "schema_version": schema_version
        }
        
    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Failed to fetch unprocessed events: {str(e)}")


def get_processing_stats() -> Dict[str, Any]:
    """
    Get processing statistics for all events.
    
    Returns:
        Dictionary containing:
        - total_events: Total number of events
        - processed_count: Number of successfully processed events
        - unprocessed_count: Number of events awaiting processing
        - failed_count: Number of events with failure notes
        - processing_rate: Percentage of events processed
        
    Raises:
        Exception: If database query fails
        
    Example:
        >>> stats = get_processing_stats()
        >>> print(f"Processing rate: {stats['processing_rate']:.1f}%")
    """
    try:
        # Fetch all events
        all_events_response = supabase.table("raw_events").select("*").execute()
        all_events = all_events_response.data
        
        total_events = len(all_events)
        
        if total_events == 0:
            return {
                "total_events": 0,
                "processed_count": 0,
                "unprocessed_count": 0,
                "failed_count": 0,
                "processing_rate": 0.0
            }
        
        # Calculate statistics
        processed_count = sum(1 for e in all_events if e.get("processed", False))
        unprocessed_count = total_events - processed_count
        
        # Count events with failure notes
        failed_count = sum(
            1 for e in all_events
            if e.get("processing_notes", "").startswith("FAILED:")
        )
        
        # Calculate processing rate
        processing_rate = (processed_count / total_events) * 100 if total_events > 0 else 0.0
        
        return {
            "total_events": total_events,
            "processed_count": processed_count,
            "unprocessed_count": unprocessed_count,
            "failed_count": failed_count,
            "processing_rate": round(processing_rate, 2)
        }
        
    except Exception as e:
        raise Exception(f"Failed to fetch processing stats: {str(e)}")

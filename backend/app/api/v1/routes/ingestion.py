"""
Event Ingestion Routes for CreditBridge

SYSTEM ROLE:
You are extending the ingestion endpoint to support event versioning.

PROJECT:
CreditBridge — Event Ingestion API.

REQUIREMENTS:
1. Accept optional field `schema_version` (default "v1")
2. Store schema_version in raw_events
3. Explicitly set processed = false on insert
4. Backward-compatible with existing clients
5. Do NOT change existing payload structure

These endpoints allow authenticated clients to:
- Ingest raw events with versioning support
- Track event processing status
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from app.core.supabase import supabase
from app.core.repository import log_audit_event
from app.api.v1.routes.borrowers import get_current_user


router = APIRouter(prefix="/ingest")


class EventPayload(BaseModel):
    """
    Raw event payload for ingestion.
    
    Attributes:
        event_type: Type of event (e.g., 'loan_application', 'payment', 'default')
        event_data: Arbitrary JSON data for the event
        schema_version: Optional schema version (default "v1")
        metadata: Optional metadata about the event source
    """
    event_type: str
    event_data: Dict[str, Any]
    schema_version: Optional[str] = Field(default="v1", description="Schema version for backward compatibility")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


@router.post("/event")
async def ingest_event(
    event: EventPayload,
    user_id: str = Depends(get_current_user)
):
    """
    Ingest a raw event with schema versioning support.
    
    This endpoint provides backward-compatible event ingestion with:
    - Schema versioning for event evolution
    - Processing status tracking
    - Audit trail for compliance
    
    Args:
        event: Event payload with type, data, and optional schema version
        user_id: Authenticated user ID from JWT token
        
    Returns:
        Created event record with:
        - event_id: UUID of the ingested event
        - schema_version: Schema version used
        - processed: Processing status (always false on insert)
        - created_at: Timestamp of ingestion
        
    Raises:
        HTTPException: If event ingestion fails
    """
    try:
        # Fetch borrower profile to link event
        borrower_response = supabase.table("borrowers").select("*").eq("user_id", user_id).execute()
        
        if not borrower_response.data:
            raise HTTPException(
                status_code=404,
                detail="Borrower profile not found. Please create your profile first."
            )
        
        borrower_id = borrower_response.data[0]["id"]
        
        # Prepare event record for raw_events table
        # REQUIREMENT: Explicitly set processed = false on insert
        # REQUIREMENT: Store schema_version in raw_events
        event_record = {
            "borrower_id": borrower_id,
            "event_type": event.event_type,
            "event_data": event.event_data,
            "schema_version": event.schema_version,  # REQUIREMENT: Store schema_version
            "processed": False,  # REQUIREMENT: Explicitly set processed = false
            "metadata": event.metadata
        }
        
        # Insert into raw_events table
        response = supabase.table("raw_events").insert(event_record).execute()
        
        if not response.data:
            raise Exception("Failed to insert event: No data returned")
        
        created_event = response.data[0]
        event_id = created_event.get("id")
        
        # Log audit event for compliance
        log_audit_event(
            action="event_ingested",
            entity_type="raw_event",
            entity_id=event_id,
            metadata={
                "borrower_id": borrower_id,
                "user_id": user_id,
                "event_type": event.event_type,
                "schema_version": event.schema_version,
                "processed": False
            }
        )
        
        return {
            "event_id": event_id,
            "event_type": event.event_type,
            "schema_version": event.schema_version,
            "processed": False,
            "created_at": created_event.get("created_at"),
            "message": f"Event ingested successfully with schema version {event.schema_version}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest event: {str(e)}"
        )


@router.get("/events")
async def get_events(
    user_id: str = Depends(get_current_user),
    processed: Optional[bool] = None,
    schema_version: Optional[str] = None,
    limit: int = 50
):
    """
    Retrieve ingested events for the authenticated user.
    
    Args:
        user_id: Authenticated user ID from JWT token
        processed: Optional filter by processing status
        schema_version: Optional filter by schema version
        limit: Maximum number of events to return (default 50)
        
    Returns:
        List of events with metadata
        
    Raises:
        HTTPException: If fetch fails
    """
    try:
        # Fetch borrower profile
        borrower_response = supabase.table("borrowers").select("*").eq("user_id", user_id).execute()
        
        if not borrower_response.data:
            raise HTTPException(
                status_code=404,
                detail="Borrower profile not found."
            )
        
        borrower_id = borrower_response.data[0]["id"]
        
        # Build query
        query = supabase.table("raw_events").select("*").eq("borrower_id", borrower_id)
        
        # Apply filters
        if processed is not None:
            query = query.eq("processed", processed)
        
        if schema_version:
            query = query.eq("schema_version", schema_version)
        
        # Execute query with limit and ordering
        events_response = query.order("created_at", desc=True).limit(limit).execute()
        
        return {
            "total": len(events_response.data),
            "events": events_response.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch events: {str(e)}"
        )


@router.get("/events/stats")
async def get_event_stats(user_id: str = Depends(get_current_user)):
    """
    Get event ingestion statistics for the authenticated user.
    
    Args:
        user_id: Authenticated user ID from JWT token
        
    Returns:
        Statistics including total events, processed count, schema version distribution
        
    Raises:
        HTTPException: If fetch fails
    """
    try:
        # Fetch borrower profile
        borrower_response = supabase.table("borrowers").select("*").eq("user_id", user_id).execute()
        
        if not borrower_response.data:
            raise HTTPException(
                status_code=404,
                detail="Borrower profile not found."
            )
        
        borrower_id = borrower_response.data[0]["id"]
        
        # Fetch all events for this borrower
        events_response = supabase.table("raw_events").select("*").eq("borrower_id", borrower_id).execute()
        
        events = events_response.data
        total_events = len(events)
        
        # Calculate statistics
        processed_count = sum(1 for e in events if e.get("processed", False))
        unprocessed_count = total_events - processed_count
        
        # Schema version distribution
        schema_versions = {}
        for event in events:
            version = event.get("schema_version", "unknown")
            schema_versions[version] = schema_versions.get(version, 0) + 1
        
        # Event type distribution
        event_types = {}
        for event in events:
            event_type = event.get("event_type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            "total_events": total_events,
            "processed": processed_count,
            "unprocessed": unprocessed_count,
            "schema_versions": schema_versions,
            "event_types": event_types
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch event stats: {str(e)}"
        )

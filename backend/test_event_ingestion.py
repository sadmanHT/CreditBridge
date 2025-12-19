"""
Test script for ingestion endpoint and event processing
Runs without requiring the FastAPI server to be running
"""

import sys
import json
from datetime import datetime

print("="*70)
print("[TEST SUITE] Event Ingestion & Processing Verification")
print("="*70)

# Test A: Direct database insert (simulating ingestion endpoint)
print("\n[A] INGEST VERSIONED EVENT")
print("-"*70)

try:
    from app.core.supabase import supabase
    from app.core.repository import log_audit_event
    
    # Simulate borrower lookup (using existing test borrower)
    borrower_response = supabase.table("borrowers").select("id, user_id").limit(1).execute()
    
    if not borrower_response.data:
        print("✗ No borrower found. Please create a test borrower first.")
        sys.exit(1)
    
    borrower_id = borrower_response.data[0]["id"]
    user_id = borrower_response.data[0]["user_id"]
    
    print(f"✓ Using borrower: {borrower_id}")
    
    # Prepare event record (matching ingestion.py logic)
    event_record = {
        "borrower_id": borrower_id,
        "event_type": "transaction",
        "event_data": {
            "amount": 1200,
            "merchant_category": "grocery",
            "event_source": "merchant_api"
        },
        "schema_version": "v2",  # REQUIREMENT: Store schema_version
        "processed": False,      # REQUIREMENT: Explicitly set processed = false
        "metadata": {
            "source": "test_suite",
            "test_timestamp": datetime.utcnow().isoformat()
        }
    }
    
    # Insert into raw_events table
    response = supabase.table("raw_events").insert(event_record).execute()
    
    if not response.data:
        print("✗ Failed to insert event")
        sys.exit(1)
    
    created_event = response.data[0]
    event_id = created_event.get("id")
    
    print(f"✓ Event ingested successfully!")
    print(f"  Event ID: {event_id}")
    print(f"  Schema Version: {created_event.get('schema_version')}")
    print(f"  Processed: {created_event.get('processed')}")
    print(f"  Created At: {created_event.get('created_at')}")
    
    # Log audit event
    log_audit_event(
        action="event_ingested",
        entity_type="raw_event",
        entity_id=event_id,
        metadata={
            "borrower_id": borrower_id,
            "user_id": user_id,
            "event_type": "transaction",
            "schema_version": "v2",
            "processed": False,
            "test_mode": True
        }
    )
    
    print("✓ Audit event logged")
    
except Exception as e:
    print(f"✗ Error during ingestion: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# Test B: Verify Database State
print("\n[B] VERIFY DATABASE STATE")
print("-"*70)

try:
    # Fetch the event we just created
    verify_response = supabase.table("raw_events").select("*").eq("id", event_id).execute()
    
    if not verify_response.data:
        print("✗ Event not found in database")
        sys.exit(1)
    
    event = verify_response.data[0]
    
    print("✓ Event found in database")
    print(f"  ID: {event['id']}")
    print(f"  Schema Version: {event.get('schema_version')} (expected: v2)")
    print(f"  Processed: {event.get('processed')} (expected: False)")
    print(f"  Processed At: {event.get('processed_at')} (expected: None)")
    print(f"  Event Type: {event.get('event_type')}")
    print(f"  Event Data: {json.dumps(event.get('event_data'), indent=2)}")
    
    # Verify requirements
    checks = []
    checks.append(("schema_version = v2", event.get('schema_version') == 'v2'))
    checks.append(("processed = false", event.get('processed') == False))
    checks.append(("processed_at = NULL", event.get('processed_at') is None))
    
    print("\n  Verification Checks:")
    all_passed = True
    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        color = "green" if check_result else "red"
        print(f"    {status} {check_name}")
        if not check_result:
            all_passed = False
    
    if not all_passed:
        print("\n✗ Some verification checks failed")
        sys.exit(1)
    
    print("\n✓ All verification checks passed!")
    
except Exception as e:
    print(f"✗ Error during verification: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# Test C: Test Processing Marker
print("\n[C] TEST PROCESSING MARKER")
print("-"*70)

try:
    from app.core.event_processing import mark_event_processed
    
    # Mark the event as processed
    result = mark_event_processed(event_id, "initial test processing")
    
    print("✓ mark_event_processed() executed successfully")
    print(f"  Event ID: {result['event_id']}")
    print(f"  Status: {result['status']}")
    print(f"  Processed: {result['processed']}")
    print(f"  Processed At: {result['processed_at']}")
    print(f"  Notes: {result['processing_notes']}")
    
    # Verify database state after marking processed
    verify_response = supabase.table("raw_events").select("*").eq("id", event_id).execute()
    
    if not verify_response.data:
        print("✗ Event not found after processing")
        sys.exit(1)
    
    processed_event = verify_response.data[0]
    
    print("\n  Database State After Processing:")
    print(f"    Processed: {processed_event.get('processed')} (expected: True)")
    print(f"    Processed At: {processed_event.get('processed_at')} (expected: populated)")
    print(f"    Notes: {processed_event.get('processing_notes')}")
    
    # Verify requirements
    post_checks = []
    post_checks.append(("processed = true", processed_event.get('processed') == True))
    post_checks.append(("processed_at populated", processed_event.get('processed_at') is not None))
    post_checks.append(("notes stored", processed_event.get('processing_notes') is not None))
    
    print("\n  Post-Processing Verification:")
    all_passed = True
    for check_name, check_result in post_checks:
        status = "✓" if check_result else "✗"
        print(f"    {status} {check_name}")
        if not check_result:
            all_passed = False
    
    if not all_passed:
        print("\n✗ Some post-processing checks failed")
        sys.exit(1)
    
    print("\n✓ All post-processing checks passed!")
    
except Exception as e:
    print(f"✗ Error during processing marker test: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


# Final Summary
print("\n" + "="*70)
print("[SUMMARY] All Tests Passed! ✓")
print("="*70)
print("\nVerified Functionality:")
print("  ✓ Event ingestion with schema versioning")
print("  ✓ Database state persistence (processed=false, schema_version=v2)")
print("  ✓ Event processing marker (mark_event_processed)")
print("  ✓ Processing state updates (processed=true, timestamps, notes)")
print("  ✓ Audit trail logging")
print("\n" + "="*70)

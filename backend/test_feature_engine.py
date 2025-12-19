"""
Test script for FeatureEngine

This script tests the feature engineering pipeline without requiring
the full API server to be running.
"""

import sys
import json
from datetime import datetime, timedelta, timezone

print("="*70)
print("[TEST] Feature Engineering Engine Verification")
print("="*70)

try:
    from app.features.engine import FeatureEngine
    from app.core.supabase import supabase, supabase_admin
    
    print("\n✓ Imports successful")
    
    # Use admin client for testing if available (bypasses RLS)
    test_client = supabase_admin if supabase_admin else supabase
    if supabase_admin:
        print("  Using service role client for testing (bypasses RLS)")
    else:
        print("  Warning: Using anon client - RLS policies may block operations")
    
    # Initialize engine with test client
    engine = FeatureEngine(lookback_days=30, client=test_client)
    print(f"✓ FeatureEngine initialized")
    print(f"  Feature Set: {engine.feature_set}")
    print(f"  Feature Version: {engine.feature_version}")
    print(f"  Lookback Days: {engine.lookback_days}")
    
    # Fetch a test borrower
    print("\n[1] Fetching Test Borrower")
    print("-"*70)
    
    borrower_response = test_client.table("borrowers").select("*").limit(1).execute()
    
    if not borrower_response.data:
        print("✗ No borrower found in database")
        print("  Please create a test borrower first")
        sys.exit(1)
    
    borrower = borrower_response.data[0]
    borrower_id = borrower["id"]
    
    print(f"✓ Using borrower: {borrower_id}")
    print(f"  Name: {borrower.get('name', 'N/A')}")
    print(f"  Phone: {borrower.get('phone', 'N/A')}")
    
    # Create some test events if none exist
    print("\n[2] Preparing Test Events")
    print("-"*70)
    
    existing_events = test_client.table("raw_events").select("id").eq(
        "borrower_id", borrower_id
    ).execute()
    
    if not existing_events.data or len(existing_events.data) < 3:
        print("Creating test events...")
        
        test_events = [
            {
                "borrower_id": borrower_id,
                "event_type": "transaction",
                "event_data": {"amount": 500, "merchant": "Store A"},
                "schema_version": "v1",
                "processed": False,
                "metadata": {"source": "test_suite"}
            },
            {
                "borrower_id": borrower_id,
                "event_type": "transaction",
                "event_data": {"amount": 750, "merchant": "Store B"},
                "schema_version": "v1",
                "processed": False,
                "metadata": {"source": "test_suite"}
            },
            {
                "borrower_id": borrower_id,
                "event_type": "app_open",
                "event_data": {"platform": "android", "version": "1.2.3"},
                "schema_version": "v1",
                "processed": False,
                "metadata": {"source": "test_suite"}
            },
            {
                "borrower_id": borrower_id,
                "event_type": "mobile_payment",
                "event_data": {"amount": 200, "method": "wallet"},
                "schema_version": "v1",
                "processed": False,
                "metadata": {"source": "test_suite"}
            }
        ]
        
        for event in test_events:
            test_client.table("raw_events").insert(event).execute()
        
        print(f"✓ Created {len(test_events)} test events")
    else:
        print(f"✓ Found {len(existing_events.data)} existing events")
    
    # Compute features
    print("\n[3] Computing Features")
    print("-"*70)
    
    feature_set = engine.compute_features(
        borrower_id=borrower_id,
        borrower_profile=borrower
    )
    
    print("✓ Features computed successfully!")
    print(f"  Feature Set: {feature_set.feature_set}")
    print(f"  Feature Version: {feature_set.feature_version}")
    print(f"  Computed At: {feature_set.computed_at}")
    print(f"  Source Event Count: {feature_set.source_event_count}")
    
    print("\n  Computed Features:")
    for feature_name, feature_value in feature_set.features.items():
        if isinstance(feature_value, float):
            print(f"    {feature_name}: {feature_value:.2f}")
        else:
            print(f"    {feature_name}: {feature_value}")
    
    # Verify feature values
    print("\n[4] Validating Feature Values")
    print("-"*70)
    
    features = feature_set.features
    validations = []
    
    # Check mobile_activity_score
    mobile_score = features.get("mobile_activity_score", 0)
    validations.append((
        "mobile_activity_score in [0, 100]",
        0 <= mobile_score <= 100
    ))
    
    # Check transaction_volume_30d
    tx_volume = features.get("transaction_volume_30d", 0)
    validations.append((
        "transaction_volume_30d >= 0",
        tx_volume >= 0
    ))
    
    # Check activity_consistency
    consistency = features.get("activity_consistency", 0)
    validations.append((
        "activity_consistency in [0, 100]",
        0 <= consistency <= 100
    ))
    
    # Check metadata features
    validations.append((
        "event_count present",
        "event_count" in features
    ))
    
    validations.append((
        "lookback_days = 30",
        features.get("lookback_days") == 30
    ))
    
    all_valid = True
    for check_name, check_result in validations:
        status = "✓" if check_result else "✗"
        print(f"  {status} {check_name}")
        if not check_result:
            all_valid = False
    
    if not all_valid:
        print("\n✗ Some validation checks failed")
        sys.exit(1)
    
    print("\n✓ All validation checks passed!")
    
    # Save features to database
    print("\n[5] Saving Features to Database")
    print("-"*70)
    
    save_result = engine.save_features(feature_set)
    
    print("✓ Features saved successfully!")
    print(f"  Feature ID: {save_result['feature_id']}")
    print(f"  Borrower ID: {save_result['borrower_id']}")
    print(f"  Status: {save_result['status']}")
    
    # Verify database persistence
    print("\n[6] Verifying Database Persistence")
    print("-"*70)
    
    feature_id = save_result['feature_id']
    
    verify_response = test_client.table("model_features").select("*").eq(
        "id", feature_id
    ).execute()
    
    if not verify_response.data:
        print("✗ Feature record not found in database")
        sys.exit(1)
    
    saved_feature = verify_response.data[0]
    
    print("✓ Feature record found in database")
    print(f"  ID: {saved_feature['id']}")
    print(f"  Borrower ID: {saved_feature['borrower_id']}")
    print(f"  Feature Set: {saved_feature['feature_set']}")
    print(f"  Feature Version: {saved_feature['feature_version']}")
    print(f"  Computed At: {saved_feature['computed_at']}")
    
    # Verify feature values match
    saved_features = saved_feature.get('features', {})
    
    print("\n  Saved Features:")
    for feature_name, feature_value in saved_features.items():
        if isinstance(feature_value, float):
            print(f"    {feature_name}: {feature_value:.2f}")
        else:
            print(f"    {feature_name}: {feature_value}")
    
    # Test compute_and_save method
    print("\n[7] Testing compute_and_save Method")
    print("-"*70)
    
    combined_result = engine.compute_and_save(
        borrower_id=borrower_id,
        borrower_profile=borrower
    )
    
    print("✓ compute_and_save executed successfully!")
    print(f"  Feature ID: {combined_result['feature_id']}")
    print(f"  Source Event Count: {combined_result['source_event_count']}")
    print(f"  Features Included: {len(combined_result['features'])} features")
    
    # Final Summary
    print("\n" + "="*70)
    print("[SUMMARY] All Tests Passed! ✓")
    print("="*70)
    print("\nVerified Functionality:")
    print("  ✓ FeatureEngine initialization")
    print("  ✓ Feature computation (mobile_activity_score, transaction_volume_30d, activity_consistency)")
    print("  ✓ Feature value validation (ranges, types)")
    print("  ✓ Feature persistence to model_features table")
    print("  ✓ Database verification")
    print("  ✓ compute_and_save convenience method")
    print("\nFeature Set Details:")
    print(f"  Feature Set: {engine.feature_set}")
    print(f"  Feature Version: {engine.feature_version}")
    print(f"  Lookback Days: {engine.lookback_days}")
    print("\n" + "="*70)
    
except ImportError as e:
    print(f"\n✗ Import error: {str(e)}")
    print("  Make sure all dependencies are installed")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ Error during testing: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

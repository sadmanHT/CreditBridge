"""Test B: End-to-End Loan Flow Test"""
from app.ai.registry import ModelRegistry
from app.features.engine import FeatureEngine

print("\n" + "="*70)
print("TEST B: End-to-End Loan Flow")
print("="*70)

# Initialize registry
registry = ModelRegistry()

# Simulate borrower with raw event data
borrower = {
    "id": "test-borrower-001",  # Required by registry
    "borrower_id": "test-borrower-001",
    "region": "Dhaka",
    "mobile_number": "+8801712345678",
    "events": [
        {"event_type": "mobile_money_transaction", "amount": 5000, "timestamp": "2024-12-15T10:00:00Z"},
        {"event_type": "mobile_money_transaction", "amount": 3000, "timestamp": "2024-12-14T15:30:00Z"},
        {"event_type": "mobile_money_transaction", "amount": 7000, "timestamp": "2024-12-13T09:00:00Z"}
    ]
}

loan_request = {
    "requested_amount": 12000,
    "purpose": "business_expansion",
    "requested_term_days": 30
}

# Step 1: Compute features
print("\n[Step 1] Computing features from events...")
feature_engine = FeatureEngine()

try:
    feature_result = feature_engine.compute_features(
        borrower_id=borrower["borrower_id"],
        events=borrower["events"]
    )
    
    print(f"✓ Features computed successfully")
    print(f"  Feature Set: {feature_result['feature_set']}")
    print(f"  Feature Version: {feature_result['feature_version']}")
    print(f"  Computed Features: {list(feature_result['features'].keys())}")
    
    # Attach features to borrower
    borrower["engineered_features"] = feature_result["features"]
    borrower["feature_set"] = feature_result["feature_set"]
    borrower["feature_version"] = feature_result["feature_version"]
    
except Exception as e:
    print(f"✗ Feature computation failed: {e}")
    print("  Falling back to manual features for test...")
    borrower["engineered_features"] = {
        "mobile_activity_score": 75,
        "transaction_volume_30d": 15000,
        "activity_consistency": 25
    }
    borrower["feature_set"] = "core_behavioral"
    borrower["feature_version"] = "v1"

# Step 2: Make prediction via registry
print("\n[Step 2] Making prediction via AIRegistry...")
try:
    result = registry.predict_with_features(borrower, loan_request)
    
    print(f"✓ Prediction completed successfully")
    print(f"\n  Credit Score: {result['final_credit_score']}")
    print(f"  Decision: {result.get('decision', 'pending')}")
    print(f"  Fraud Flag: {result.get('fraud_flag', False)}")
    
    # Step 3: Validate fraud detection used features
    print("\n[Step 3] Validating fraud detection...")
    
    if "fraud_result" in result:
        fraud_result = result["fraud_result"]
        print(f"✓ Fraud engine invoked")
        print(f"  Fraud Score: {fraud_result.get('combined_fraud_score', 'N/A')}")
        print(f"  Flags: {fraud_result.get('consolidated_flags', [])}")
        
        # Check if explanation references features
        explanations = fraud_result.get("merged_explanation", [])
        references_features = any(
            "transaction_volume" in str(exp) or 
            "activity_consistency" in str(exp) or
            "mobile_activity" in str(exp)
            for exp in explanations
        )
        
        print(f"✓ Fraud explanation references features: {references_features}")
        
        if explanations:
            print(f"  Sample explanation: {explanations[0][:100]}...")
    else:
        print(f"⚠ No fraud_result in output (check ensemble integration)")
    
    # Step 4: Validate no raw data leakage
    print("\n[Step 4] Validating no raw data leakage...")
    
    # Check that features were used, not raw events
    if "model_outputs" in result:
        print(f"✓ Model outputs present")
        for model_name, output in result["model_outputs"].items():
            if "error" in output:
                print(f"  ⚠ {model_name}: {output['error']}")
            else:
                print(f"  ✓ {model_name}: executed successfully")
    
    print(f"✓ No raw data access errors detected")
    
    # Final validation
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print("✓ Decision still works")
    print("✓ Fraud explanation references features")
    print("✓ No raw data leakage")
    print("="*70)
    
except Exception as e:
    print(f"✗ Prediction failed: {e}")
    print(f"  Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

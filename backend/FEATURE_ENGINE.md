# Feature Engineering Engine

Production-grade feature extraction system for CreditBridge AI credit scoring.

## Overview

The **FeatureEngine** transforms raw borrower data and event streams into structured, versioned features for downstream ML models. All transformations are deterministic and auditable.

## Architecture

```
Raw Data → FeatureEngine → Versioned Features → model_features table → ML Models
```

## Features Produced

### Core Behavioral Features (v1)

1. **mobile_activity_score** (0-100)
   - Phone number presence: 20 points
   - Event count: up to 50 points
   - Mobile-specific events: up to 30 points
   - Mobile event types: `app_open`, `location_update`, `mobile_payment`, `sms_verification`

2. **transaction_volume_30d** (float)
   - Sum of all transaction amounts in lookback window
   - Only includes events with `event_type="transaction"`
   - Extracted from `event_data.amount`

3. **activity_consistency** (0-100)
   - Measures regularity of event generation over time
   - Groups events by day, calculates coefficient of variation
   - Lower variation = higher consistency score
   - Algorithm: `score = max(0, 100 - (CV * 50))`

### Metadata Features

- `event_count`: Total events used
- `lookback_days`: Time window (default: 30)
- `has_phone`: Boolean indicating phone presence

## Database Schema

### model_features Table

```sql
CREATE TABLE model_features (
    id UUID PRIMARY KEY,
    borrower_id UUID REFERENCES borrowers(id),
    feature_set TEXT NOT NULL,           -- "core_behavioral"
    feature_version TEXT NOT NULL,       -- "v1"
    features JSONB NOT NULL,             -- Computed feature values
    computed_at TIMESTAMPTZ NOT NULL,
    source_event_count INTEGER,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

## Usage

### Basic Usage

```python
from app.features.engine import FeatureEngine

# Initialize engine
engine = FeatureEngine(lookback_days=30)

# Compute features
feature_set = engine.compute_features(
    borrower_id="abc-123",
    borrower_profile={
        "id": "abc-123",
        "phone": "1234567890",
        "name": "John Doe"
    }
)

# Access computed features
print(feature_set.features["mobile_activity_score"])
print(feature_set.features["transaction_volume_30d"])
print(feature_set.features["activity_consistency"])
```

### With Custom Events

```python
# Provide pre-fetched events
raw_events = [
    {
        "event_type": "transaction",
        "event_data": {"amount": 500},
        "created_at": "2025-12-01T10:00:00Z"
    },
    # ... more events
]

feature_set = engine.compute_features(
    borrower_id="abc-123",
    borrower_profile=profile,
    raw_events=raw_events
)
```

### Compute and Save

```python
# Compute features and save to database in one call
result = engine.compute_and_save(
    borrower_id="abc-123",
    borrower_profile=profile
)

print(f"Saved feature ID: {result['feature_id']}")
print(f"Features: {result['features']}")
```

### Save Pre-computed Features

```python
# Save already-computed features
feature_set = engine.compute_features(...)
save_result = engine.save_features(feature_set)

print(f"Feature ID: {save_result['feature_id']}")
print(f"Status: {save_result['status']}")
```

## Setup Instructions

### 1. Create model_features Table

Execute the SQL migration:

```sql
-- See: migrations/create_model_features_table.sql
```

In Supabase Dashboard:
1. Go to **SQL Editor**
2. Click **"New Query"**
3. Paste contents of `migrations/create_model_features_table.sql`
4. Click **"Run"**

### 2. Verify Setup

Run the test suite:

```powershell
cd F:\MillionX_FinTech\backend
F:/MillionX_FinTech/backend/venv/Scripts/python.exe test_feature_engine.py
```

Expected output:
```
======================================================================
[TEST] Feature Engineering Engine Verification
======================================================================

[1] Fetching Test Borrower
----------------------------------------------------------------------
✓ Using borrower: <uuid>

[2] Preparing Test Events
----------------------------------------------------------------------
✓ Created 4 test events

[3] Computing Features
----------------------------------------------------------------------
✓ Features computed successfully!
  mobile_activity_score: 75.00
  transaction_volume_30d: 1450.00
  activity_consistency: 68.50

[4] Validating Feature Values
----------------------------------------------------------------------
  ✓ mobile_activity_score in [0, 100]
  ✓ transaction_volume_30d >= 0
  ✓ activity_consistency in [0, 100]

[5] Saving Features to Database
----------------------------------------------------------------------
✓ Features saved successfully!

[SUMMARY] All Tests Passed! ✓
```

## Integration with Loan Processing

### Example: Compute Features During Loan Request

```python
from app.features.engine import FeatureEngine

# In loan processing endpoint
@router.post("/loans/request")
async def request_loan(loan_request, user_id):
    # ... fetch borrower profile ...
    
    # Compute behavioral features
    feature_engine = FeatureEngine()
    feature_result = feature_engine.compute_and_save(
        borrower_id=borrower_id,
        borrower_profile=borrower
    )
    
    # Use features in credit scoring
    features = feature_result["features"]
    mobile_score = features["mobile_activity_score"]
    tx_volume = features["transaction_volume_30d"]
    consistency = features["activity_consistency"]
    
    # ... pass to credit scoring model ...
```

## Feature Versioning

### Version: v1

Current implementation:
- Feature Set: `core_behavioral`
- Feature Version: `v1`
- Lookback Window: 30 days (configurable)

### Adding New Features (v2 Example)

```python
class FeatureEngine:
    def __init__(self, lookback_days=30, version="v1"):
        self.feature_set = "core_behavioral"
        self.feature_version = version
        
    def compute_features(self, ...):
        if self.feature_version == "v1":
            # v1 features
            pass
        elif self.feature_version == "v2":
            # v2 features (backward compatible)
            pass
```

## Querying Features

### Get Latest Features for Borrower

```python
from app.core.supabase import supabase

response = supabase.table("model_features").select("*").eq(
    "borrower_id", borrower_id
).eq(
    "feature_set", "core_behavioral"
).eq(
    "feature_version", "v1"
).order("computed_at", desc=True).limit(1).execute()

latest_features = response.data[0]["features"]
```

### Get Features for Multiple Borrowers

```sql
SELECT 
    borrower_id,
    features->>'mobile_activity_score' as mobile_score,
    features->>'transaction_volume_30d' as tx_volume,
    computed_at
FROM model_features
WHERE 
    feature_set = 'core_behavioral' 
    AND feature_version = 'v1'
    AND borrower_id = ANY($1)
ORDER BY computed_at DESC;
```

## Testing

### Run Full Test Suite

```powershell
python test_feature_engine.py
```

### Unit Test Individual Features

```python
from app.features.engine import FeatureEngine

engine = FeatureEngine()

# Test mobile activity score
score = engine._compute_mobile_activity_score(
    borrower_profile={"phone": "1234567890"},
    events=[{"event_type": "app_open"}] * 10
)
assert 0 <= score <= 100

# Test transaction volume
volume = engine._compute_transaction_volume(
    events=[
        {"event_type": "transaction", "event_data": {"amount": 100}},
        {"event_type": "transaction", "event_data": {"amount": 200}}
    ]
)
assert volume == 300.0
```

## Error Handling

The engine provides explicit error messages:

```python
try:
    feature_set = engine.compute_features(
        borrower_id="",  # Invalid
        borrower_profile=None
    )
except ValueError as e:
    print(f"Validation error: {e}")
    
except Exception as e:
    print(f"Computation error: {e}")
```

## Performance Considerations

- **Event Limit**: Fetches max 1000 events per borrower
- **Lookback Window**: Default 30 days (configurable)
- **Caching**: Consider caching features for high-volume scenarios
- **Batch Processing**: Use `compute_and_save()` for single-borrower flows

## Audit Trail

All feature computations are logged:

```python
{
    "action": "features_computed",
    "entity_type": "model_features",
    "entity_id": "<feature_id>",
    "metadata": {
        "borrower_id": "<uuid>",
        "feature_set": "core_behavioral",
        "feature_version": "v1",
        "source_event_count": 42,
        "feature_names": [...]
    }
}
```

## Files

- `app/features/engine.py` - Main FeatureEngine implementation
- `app/features/__init__.py` - Module exports
- `migrations/create_model_features_table.sql` - Database schema
- `test_feature_engine.py` - Comprehensive test suite
- `docs/FEATURE_ENGINE.md` - This documentation

## Requirements Met

- [x] Accept borrower profile and raw_events
- [x] Produce mobile_activity_score (0-100)
- [x] Produce transaction_volume_30d (float)
- [x] Produce activity_consistency (0-100)
- [x] Deterministic logic only (no ML models)
- [x] Version features (feature_set="core_behavioral", feature_version="v1")
- [x] Store features in model_features table
- [x] Audit trail logging
- [x] Comprehensive error handling
- [x] Unit tests and integration tests

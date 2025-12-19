"""
Database Migration: Create raw_events table

This script creates the raw_events table for event ingestion with schema versioning support.

Run this script once to set up the table structure.
"""

from app.core.supabase import supabase

print("="*70)
print("[MIGRATION] Creating raw_events table")
print("="*70)

# SQL to create raw_events table
create_table_sql = """
CREATE TABLE IF NOT EXISTS raw_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    borrower_id UUID NOT NULL REFERENCES borrowers(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB NOT NULL,
    schema_version TEXT DEFAULT 'v1',
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMPTZ,
    processing_notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_raw_events_borrower_id ON raw_events(borrower_id);
CREATE INDEX IF NOT EXISTS idx_raw_events_processed ON raw_events(processed);
CREATE INDEX IF NOT EXISTS idx_raw_events_schema_version ON raw_events(schema_version);
CREATE INDEX IF NOT EXISTS idx_raw_events_event_type ON raw_events(event_type);
CREATE INDEX IF NOT EXISTS idx_raw_events_created_at ON raw_events(created_at DESC);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_raw_events_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS raw_events_updated_at_trigger ON raw_events;
CREATE TRIGGER raw_events_updated_at_trigger
    BEFORE UPDATE ON raw_events
    FOR EACH ROW
    EXECUTE FUNCTION update_raw_events_updated_at();

-- Add RLS policies (if needed)
ALTER TABLE raw_events ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own events
CREATE POLICY "Users can view own raw_events"
    ON raw_events FOR SELECT
    USING (borrower_id IN (
        SELECT id FROM borrowers WHERE user_id = auth.uid()
    ));

CREATE POLICY "Users can insert own raw_events"
    ON raw_events FOR INSERT
    WITH CHECK (borrower_id IN (
        SELECT id FROM borrowers WHERE user_id = auth.uid()
    ));

-- Service role can access all
CREATE POLICY "Service role can access all raw_events"
    ON raw_events
    USING (auth.jwt() ->> 'role' = 'service_role');

COMMENT ON TABLE raw_events IS 'Stores raw events with schema versioning for data pipeline processing';
COMMENT ON COLUMN raw_events.schema_version IS 'Event schema version for backward compatibility (default: v1)';
COMMENT ON COLUMN raw_events.processed IS 'Whether event has been processed by the pipeline';
COMMENT ON COLUMN raw_events.processed_at IS 'Timestamp when event was processed';
COMMENT ON COLUMN raw_events.processing_notes IS 'Notes about processing status (success message or failure reason)';
"""

try:
    print("\nExecuting SQL migration...")
    print("-"*70)
    
    # Execute the SQL via Supabase RPC or directly via SQL editor
    # Note: For production, use proper migration tools like Alembic or Supabase CLI
    
    print("⚠️  MANUAL ACTION REQUIRED")
    print("\nPlease execute the following SQL in Supabase SQL Editor:")
    print("="*70)
    print(create_table_sql)
    print("="*70)
    
    print("\nSteps:")
    print("1. Go to Supabase Dashboard → SQL Editor")
    print("2. Create new query")
    print("3. Copy and paste the SQL above")
    print("4. Click 'Run'")
    print("5. Verify table creation in Table Editor")
    
    print("\nAlternatively, save SQL to file for migration:")
    with open("migrations/create_raw_events_table.sql", "w") as f:
        f.write(create_table_sql)
    
    print("✓ SQL saved to: migrations/create_raw_events_table.sql")
    
except Exception as e:
    print(f"Error: {str(e)}")
    print("\n⚠️  Please create the table manually using the SQL shown above")

print("\n" + "="*70)
print("[MIGRATION] Complete - Please run SQL in Supabase")
print("="*70)

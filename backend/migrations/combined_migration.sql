-- ============================================================================
-- COMBINED MIGRATION: Create raw_events and model_features tables
-- Date: 2025-12-16
-- Description: Creates both tables needed for event ingestion and feature store
-- ============================================================================

-- ============================================================================
-- TABLE 1: raw_events (Event Ingestion)
-- ============================================================================

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

-- Add columns if they don't exist (for existing tables)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'raw_events' AND column_name = 'schema_version'
    ) THEN
        ALTER TABLE raw_events ADD COLUMN schema_version TEXT DEFAULT 'v1';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'raw_events' AND column_name = 'processed_at'
    ) THEN
        ALTER TABLE raw_events ADD COLUMN processed_at TIMESTAMPTZ;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'raw_events' AND column_name = 'processing_notes'
    ) THEN
        ALTER TABLE raw_events ADD COLUMN processing_notes TEXT;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'raw_events' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE raw_events ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;
    END IF;
END $$;

-- Create indexes for raw_events
CREATE INDEX IF NOT EXISTS idx_raw_events_borrower_id ON raw_events(borrower_id);
CREATE INDEX IF NOT EXISTS idx_raw_events_processed ON raw_events(processed);
CREATE INDEX IF NOT EXISTS idx_raw_events_schema_version ON raw_events(schema_version);
CREATE INDEX IF NOT EXISTS idx_raw_events_event_type ON raw_events(event_type);
CREATE INDEX IF NOT EXISTS idx_raw_events_created_at ON raw_events(created_at DESC);

-- Create trigger for raw_events updated_at
CREATE OR REPLACE FUNCTION update_raw_events_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: Using CREATE OR REPLACE for the trigger would require PostgreSQL 14+
-- Using conditional creation to avoid errors
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'raw_events_updated_at_trigger'
    ) THEN
        CREATE TRIGGER raw_events_updated_at_trigger
            BEFORE UPDATE ON raw_events
            FOR EACH ROW
            EXECUTE FUNCTION update_raw_events_updated_at();
    END IF;
END $$;

-- Add RLS policies for raw_events
ALTER TABLE raw_events ENABLE ROW LEVEL SECURITY;

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

CREATE POLICY "Service role can access all raw_events"
    ON raw_events
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can insert raw_events"
    ON raw_events FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

COMMENT ON TABLE raw_events IS 'Stores raw events with schema versioning for data pipeline processing';
COMMENT ON COLUMN raw_events.schema_version IS 'Event schema version for backward compatibility (default: v1)';
COMMENT ON COLUMN raw_events.processed IS 'Whether event has been processed by the pipeline';
COMMENT ON COLUMN raw_events.processed_at IS 'Timestamp when event was processed';
COMMENT ON COLUMN raw_events.processing_notes IS 'Notes about processing status (success message or failure reason)';


-- ============================================================================
-- TABLE 2: model_features (Feature Store)
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    borrower_id UUID NOT NULL REFERENCES borrowers(id) ON DELETE CASCADE,
    feature_set TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    features JSONB NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL,
    source_event_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add columns if they don't exist (for existing tables)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'model_features' AND column_name = 'source_event_count'
    ) THEN
        ALTER TABLE model_features ADD COLUMN source_event_count INTEGER DEFAULT 0;
    END IF;
END $$;

-- Create indexes for model_features
CREATE INDEX IF NOT EXISTS idx_model_features_borrower_id ON model_features(borrower_id);
CREATE INDEX IF NOT EXISTS idx_model_features_feature_set ON model_features(feature_set);
CREATE INDEX IF NOT EXISTS idx_model_features_feature_version ON model_features(feature_version);
CREATE INDEX IF NOT EXISTS idx_model_features_computed_at ON model_features(computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_features_borrower_set ON model_features(borrower_id, feature_set);

-- Create composite index for latest features query
CREATE INDEX IF NOT EXISTS idx_model_features_latest 
    ON model_features(borrower_id, feature_set, feature_version, computed_at DESC);

-- Create trigger for model_features updated_at
CREATE OR REPLACE FUNCTION update_model_features_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Using conditional creation to avoid destructive warning
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'model_features_updated_at_trigger'
    ) THEN
        CREATE TRIGGER model_features_updated_at_trigger
            BEFORE UPDATE ON model_features
            FOR EACH ROW
            EXECUTE FUNCTION update_model_features_updated_at();
    END IF;
END $$;

-- Add RLS policies for model_features
ALTER TABLE model_features ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own model_features"
    ON model_features FOR SELECT
    USING (borrower_id IN (
        SELECT id FROM borrowers WHERE user_id = auth.uid()
    ));

CREATE POLICY "Service role can access all model_features"
    ON model_features
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can insert model_features"
    ON model_features FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

COMMENT ON TABLE model_features IS 'Stores computed ML features for borrowers with versioning';
COMMENT ON COLUMN model_features.feature_set IS 'Name of the feature set (e.g., core_behavioral)';
COMMENT ON COLUMN model_features.feature_version IS 'Version of feature computation logic (e.g., v1)';
COMMENT ON COLUMN model_features.features IS 'JSON object containing computed feature values';
COMMENT ON COLUMN model_features.computed_at IS 'Timestamp when features were computed';
COMMENT ON COLUMN model_features.source_event_count IS 'Number of events used to compute features';


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Created tables:
--   1. raw_events - Event ingestion with schema versioning
--   2. model_features - Feature store for ML models
-- 
-- Next steps:
--   1. Verify tables in Supabase Table Editor
--   2. Run test suite: python test_feature_engine.py
-- ============================================================================

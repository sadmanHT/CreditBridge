-- Migration: Create model_features table for feature store
-- Date: 2025-12-16
-- Description: Creates table structure for storing computed ML features

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

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_model_features_borrower_id ON model_features(borrower_id);
CREATE INDEX IF NOT EXISTS idx_model_features_feature_set ON model_features(feature_set);
CREATE INDEX IF NOT EXISTS idx_model_features_feature_version ON model_features(feature_version);
CREATE INDEX IF NOT EXISTS idx_model_features_computed_at ON model_features(computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_features_borrower_set ON model_features(borrower_id, feature_set);

-- Create composite index for latest features query
CREATE INDEX IF NOT EXISTS idx_model_features_latest 
    ON model_features(borrower_id, feature_set, feature_version, computed_at DESC);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_model_features_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS model_features_updated_at_trigger ON model_features;
CREATE TRIGGER model_features_updated_at_trigger
    BEFORE UPDATE ON model_features
    FOR EACH ROW
    EXECUTE FUNCTION update_model_features_updated_at();

-- Add RLS policies
ALTER TABLE model_features ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own features
CREATE POLICY "Users can view own model_features"
    ON model_features FOR SELECT
    USING (borrower_id IN (
        SELECT id FROM borrowers WHERE user_id = auth.uid()
    ));

-- Service role can access all
CREATE POLICY "Service role can access all model_features"
    ON model_features
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Service role can insert features
CREATE POLICY "Service role can insert model_features"
    ON model_features FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- Table and column comments
COMMENT ON TABLE model_features IS 'Stores computed ML features for borrowers with versioning';
COMMENT ON COLUMN model_features.feature_set IS 'Name of the feature set (e.g., core_behavioral)';
COMMENT ON COLUMN model_features.feature_version IS 'Version of feature computation logic (e.g., v1)';
COMMENT ON COLUMN model_features.features IS 'JSON object containing computed feature values';
COMMENT ON COLUMN model_features.computed_at IS 'Timestamp when features were computed';
COMMENT ON COLUMN model_features.source_event_count IS 'Number of events used to compute features';

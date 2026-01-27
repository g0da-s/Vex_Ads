-- Migration: Create generated_ad_sets table for AdAngle
-- This replaces the old generated_ads table with framework-driven ad storage

-- Create the new generated_ad_sets table
CREATE TABLE IF NOT EXISTS generated_ad_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,

    -- Input data
    product TEXT NOT NULL,
    target_customer TEXT NOT NULL,
    main_benefit TEXT NOT NULL,

    -- Ad 1 - Problem-Agitate-Solution (PAS)
    ad1_framework TEXT,
    ad1_hook TEXT,
    ad1_body TEXT,
    ad1_cta TEXT,
    ad1_visual_concept TEXT,

    -- Ad 2 - Social Proof
    ad2_framework TEXT,
    ad2_hook TEXT,
    ad2_body TEXT,
    ad2_cta TEXT,
    ad2_visual_concept TEXT,

    -- Ad 3 - Transformation
    ad3_framework TEXT,
    ad3_hook TEXT,
    ad3_body TEXT,
    ad3_cta TEXT,
    ad3_visual_concept TEXT,

    -- Metadata
    generation_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster session lookups
CREATE INDEX IF NOT EXISTS idx_generated_ad_sets_session_id ON generated_ad_sets(session_id);

-- Enable Row Level Security
ALTER TABLE generated_ad_sets ENABLE ROW LEVEL SECURITY;

-- Create policy for public access (MVP - no auth required)
CREATE POLICY "Allow public access to generated_ad_sets" ON generated_ad_sets
    FOR ALL USING (true);

-- Optional: Track framework performance over time
CREATE TABLE IF NOT EXISTS framework_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_set_id UUID REFERENCES generated_ad_sets(id) ON DELETE CASCADE,
    framework_name TEXT NOT NULL,
    user_rating TEXT, -- 'good', 'ok', 'poor'
    product_category TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for framework_performance
ALTER TABLE framework_performance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public access to framework_performance" ON framework_performance
    FOR ALL USING (true);

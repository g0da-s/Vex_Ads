-- Migration: Clean schema for Visual Bible workflow
-- Date: 2026-01-28
-- Description: Drop all outdated tables and recreate with correct schema for current system

-- Drop outdated tables
DROP TABLE IF EXISTS framework_performance CASCADE;
DROP TABLE IF EXISTS generated_ad_sets CASCADE;
DROP TABLE IF EXISTS competitor_ads CASCADE;
DROP TABLE IF EXISTS generated_ads CASCADE;

-- Recreate generated_ad_sets with correct schema for Visual Bible system
-- Now stores 5 ads (not 3), no frameworks, no body/cta (just hook + visual_concept)
CREATE TABLE generated_ad_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,

    -- Input data
    brand_name TEXT NOT NULL,
    product TEXT NOT NULL,
    target_customer TEXT NOT NULL,

    -- Ad 1
    ad1_hook TEXT,
    ad1_visual_concept TEXT,
    ad1_image_path TEXT,

    -- Ad 2
    ad2_hook TEXT,
    ad2_visual_concept TEXT,
    ad2_image_path TEXT,

    -- Ad 3
    ad3_hook TEXT,
    ad3_visual_concept TEXT,
    ad3_image_path TEXT,

    -- Ad 4
    ad4_hook TEXT,
    ad4_visual_concept TEXT,
    ad4_image_path TEXT,

    -- Ad 5
    ad5_hook TEXT,
    ad5_visual_concept TEXT,
    ad5_image_path TEXT,

    -- Metadata
    generation_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster session lookups
CREATE INDEX idx_generated_ad_sets_session_id ON generated_ad_sets(session_id);

-- Enable Row Level Security
ALTER TABLE generated_ad_sets ENABLE ROW LEVEL SECURITY;

-- Create policy for public access (MVP - no auth required)
CREATE POLICY "Allow public access to generated_ad_sets" ON generated_ad_sets
    FOR ALL USING (true);

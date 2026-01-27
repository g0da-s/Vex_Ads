-- Add template_version column to generated_ads table
-- This tracks which prompt template was used to generate each ad

ALTER TABLE generated_ads
ADD COLUMN IF NOT EXISTS template_version TEXT DEFAULT 'v1_creative_director';

-- Add comment to describe the column
COMMENT ON COLUMN generated_ads.template_version IS 'Prompt template version used for generation (v1_creative_director, v2_conversion_focused, v3_minimal_modern)';

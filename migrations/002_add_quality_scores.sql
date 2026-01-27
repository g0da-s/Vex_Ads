-- Add visual quality score columns to competitor_ads table
-- These track AI-analyzed quality metrics for better winner selection

ALTER TABLE competitor_ads
ADD COLUMN IF NOT EXISTS visual_quality FLOAT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS creative_complexity FLOAT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS overall_quality FLOAT DEFAULT NULL;

-- Add comments to describe the columns
COMMENT ON COLUMN competitor_ads.visual_quality IS 'AI-analyzed visual quality score (0-100): image quality, composition, lighting, polish';
COMMENT ON COLUMN competitor_ads.creative_complexity IS 'AI-analyzed creative complexity score (0-100): design sophistication, branding, attention-grabbing';
COMMENT ON COLUMN competitor_ads.overall_quality IS 'Weighted overall quality score (0-100): 60% visual + 40% creative';

-- Add index for faster sorting by overall_quality
CREATE INDEX IF NOT EXISTS idx_competitor_ads_overall_quality ON competitor_ads(overall_quality DESC);

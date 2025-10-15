-- Migration: Add three-checkpoint trading system columns
-- Date: 2025-10-15
-- Description: Adds odds and timestamp columns for 6h, 3h, and 30m checkpoints
--              plus is_eligible flag for trading eligibility

-- Add checkpoint odds columns (0-1 probability values)
ALTER TABLE games ADD COLUMN IF NOT EXISTS odds_6h FLOAT;
ALTER TABLE games ADD COLUMN IF NOT EXISTS odds_3h FLOAT;
ALTER TABLE games ADD COLUMN IF NOT EXISTS odds_30m FLOAT;

-- Add checkpoint timestamp columns (Unix timestamps)
ALTER TABLE games ADD COLUMN IF NOT EXISTS checkpoint_6h_ts BIGINT;
ALTER TABLE games ADD COLUMN IF NOT EXISTS checkpoint_3h_ts BIGINT;
ALTER TABLE games ADD COLUMN IF NOT EXISTS checkpoint_30m_ts BIGINT;

-- Add eligibility flag (determined after 30m checkpoint)
ALTER TABLE games ADD COLUMN IF NOT EXISTS is_eligible BOOLEAN;

-- Add helpful comment
COMMENT ON COLUMN games.odds_6h IS 'Odds captured 6 hours before kickoff';
COMMENT ON COLUMN games.odds_3h IS 'Odds captured 3 hours before kickoff';
COMMENT ON COLUMN games.odds_30m IS 'Odds captured 30 minutes before kickoff';
COMMENT ON COLUMN games.checkpoint_6h_ts IS 'Unix timestamp when 6h checkpoint was captured';
COMMENT ON COLUMN games.checkpoint_3h_ts IS 'Unix timestamp when 3h checkpoint was captured';
COMMENT ON COLUMN games.checkpoint_30m_ts IS 'Unix timestamp when 30m checkpoint was captured';
COMMENT ON COLUMN games.is_eligible IS 'Trading eligibility based on checkpoint rules: ANY checkpoint >= 57% AND odds_30m >= 57%';

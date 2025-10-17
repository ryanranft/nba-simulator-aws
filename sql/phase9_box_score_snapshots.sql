-- Phase 9: Play-by-Play to Box Score Generation System
-- Database Schema for Box Score Snapshots
-- Created: October 11, 2025

-- Drop existing tables if recreating
-- DROP TABLE IF EXISTS box_score_verification CASCADE;
-- DROP TABLE IF EXISTS quarter_box_scores CASCADE;
-- DROP TABLE IF EXISTS player_snapshot_stats CASCADE;
-- DROP TABLE IF EXISTS game_state_snapshots CASCADE;

-- ============================================================================
-- TABLE 1: game_state_snapshots
-- ============================================================================
-- Stores metadata for each box score snapshot at every play-by-play event
-- One row per event per game (approx 500 snapshots per game)
-- ============================================================================

CREATE TABLE IF NOT EXISTS game_state_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    event_num INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    time_remaining VARCHAR(10),
    game_clock_seconds INTEGER,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    data_source VARCHAR(50) NOT NULL,  -- 'espn', 'hoopr', 'nba_api', 'kaggle'
    verification_passed BOOLEAN DEFAULT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Ensure uniqueness per game, event, and source
    UNIQUE(game_id, event_num, data_source)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_snapshot_game_id ON game_state_snapshots(game_id);
CREATE INDEX IF NOT EXISTS idx_snapshot_quarter ON game_state_snapshots(quarter);
CREATE INDEX IF NOT EXISTS idx_snapshot_source ON game_state_snapshots(data_source);
CREATE INDEX IF NOT EXISTS idx_snapshot_created ON game_state_snapshots(created_at);

COMMENT ON TABLE game_state_snapshots IS 'Metadata for each box score snapshot at every play-by-play event';
COMMENT ON COLUMN game_state_snapshots.snapshot_id IS 'Unique identifier for this snapshot';
COMMENT ON COLUMN game_state_snapshots.game_id IS 'Reference to game (ESPN game ID, hoopR game ID, etc)';
COMMENT ON COLUMN game_state_snapshots.event_num IS 'Sequential event number in game (0-based)';
COMMENT ON COLUMN game_state_snapshots.quarter IS 'Quarter number (1-4, 5+ for OT)';
COMMENT ON COLUMN game_state_snapshots.game_clock_seconds IS 'Total game time elapsed in seconds';
COMMENT ON COLUMN game_state_snapshots.data_source IS 'Source of PBP data (espn, hoopr, nba_api, kaggle)';
COMMENT ON COLUMN game_state_snapshots.verification_passed IS 'Did final snapshot match actual box score?';

-- ============================================================================
-- TABLE 2: player_snapshot_stats
-- ============================================================================
-- Stores player statistics at each snapshot
-- Many rows per snapshot (one per player who has played)
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_snapshot_stats (
    snapshot_id BIGINT NOT NULL REFERENCES game_state_snapshots(snapshot_id) ON DELETE CASCADE,
    player_id VARCHAR(50) NOT NULL,
    player_name VARCHAR(100),
    team_id VARCHAR(10) NOT NULL,

    -- Basic Stats
    points INTEGER DEFAULT 0,
    fgm INTEGER DEFAULT 0,  -- Field goals made
    fga INTEGER DEFAULT 0,  -- Field goals attempted
    fg3m INTEGER DEFAULT 0,  -- Three-pointers made
    fg3a INTEGER DEFAULT 0,  -- Three-pointers attempted
    ftm INTEGER DEFAULT 0,  -- Free throws made
    fta INTEGER DEFAULT 0,  -- Free throws attempted

    -- Rebounds
    oreb INTEGER DEFAULT 0,  -- Offensive rebounds
    dreb INTEGER DEFAULT 0,  -- Defensive rebounds
    reb INTEGER DEFAULT 0,   -- Total rebounds

    -- Other Stats
    ast INTEGER DEFAULT 0,   -- Assists
    stl INTEGER DEFAULT 0,   -- Steals
    blk INTEGER DEFAULT 0,   -- Blocks
    tov INTEGER DEFAULT 0,   -- Turnovers
    pf INTEGER DEFAULT 0,    -- Personal fouls

    -- Advanced
    plus_minus INTEGER DEFAULT 0,
    minutes DECIMAL(5,2) DEFAULT 0,
    on_court BOOLEAN DEFAULT false,  -- Is player currently on court?

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY(snapshot_id, player_id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_player_snapshot ON player_snapshot_stats(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_player_id ON player_snapshot_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_team ON player_snapshot_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_player_oncourt ON player_snapshot_stats(on_court);

COMMENT ON TABLE player_snapshot_stats IS 'Player box score statistics at each snapshot';
COMMENT ON COLUMN player_snapshot_stats.on_court IS 'TRUE if player is currently on court at this snapshot';
COMMENT ON COLUMN player_snapshot_stats.minutes IS 'Minutes played up to this snapshot';
COMMENT ON COLUMN player_snapshot_stats.plus_minus IS 'Plus/minus score up to this snapshot';

-- ============================================================================
-- TABLE 3: quarter_box_scores
-- ============================================================================
-- Stores quarter-specific box scores (separate from cumulative snapshots)
-- Used for quarter-by-quarter predictions and analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS quarter_box_scores (
    game_id VARCHAR(50) NOT NULL,
    quarter INTEGER NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    player_name VARCHAR(100),
    team_id VARCHAR(10) NOT NULL,

    -- Quarter Stats (not cumulative)
    points INTEGER DEFAULT 0,
    fgm INTEGER DEFAULT 0,
    fga INTEGER DEFAULT 0,
    fg3m INTEGER DEFAULT 0,
    fg3a INTEGER DEFAULT 0,
    ftm INTEGER DEFAULT 0,
    fta INTEGER DEFAULT 0,
    oreb INTEGER DEFAULT 0,
    dreb INTEGER DEFAULT 0,
    reb INTEGER DEFAULT 0,
    ast INTEGER DEFAULT 0,
    stl INTEGER DEFAULT 0,
    blk INTEGER DEFAULT 0,
    tov INTEGER DEFAULT 0,
    pf INTEGER DEFAULT 0,
    plus_minus INTEGER DEFAULT 0,
    minutes DECIMAL(5,2) DEFAULT 0,

    -- Metadata
    data_source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY(game_id, quarter, player_id, data_source)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_quarter_box_game ON quarter_box_scores(game_id);
CREATE INDEX IF NOT EXISTS idx_quarter_box_quarter ON quarter_box_scores(quarter);
CREATE INDEX IF NOT EXISTS idx_quarter_box_player ON quarter_box_scores(player_id);

COMMENT ON TABLE quarter_box_scores IS 'Quarter-specific box scores (not cumulative) for quarter-by-quarter analysis';
COMMENT ON COLUMN quarter_box_scores.points IS 'Points scored IN THIS QUARTER ONLY (not cumulative)';

-- ============================================================================
-- TABLE 4: box_score_verification
-- ============================================================================
-- Stores verification results comparing generated vs actual final box scores
-- One row per game per data source
-- ============================================================================

CREATE TABLE IF NOT EXISTS box_score_verification (
    game_id VARCHAR(50) NOT NULL,
    data_source VARCHAR(50) NOT NULL,

    -- Verification Results
    final_score_match BOOLEAN,
    home_score_generated INTEGER,
    away_score_generated INTEGER,
    home_score_actual INTEGER,
    away_score_actual INTEGER,

    -- Discrepancy Metrics
    total_discrepancies INTEGER DEFAULT 0,
    discrepancy_details JSONB,  -- Detailed breakdown by player and stat

    -- Mean Absolute Errors
    mae_points DECIMAL(5,2),
    mae_rebounds DECIMAL(5,2),
    mae_assists DECIMAL(5,2),
    mae_steals DECIMAL(5,2),
    mae_blocks DECIMAL(5,2),
    mae_turnovers DECIMAL(5,2),

    -- Quality Grade
    quality_grade CHAR(1) CHECK (quality_grade IN ('A', 'B', 'C', 'D', 'F')),

    -- Notes
    notes TEXT,

    -- Metadata
    verified_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY(game_id, data_source)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_verification_grade ON box_score_verification(quality_grade);
CREATE INDEX IF NOT EXISTS idx_verification_source ON box_score_verification(data_source);
CREATE INDEX IF NOT EXISTS idx_verification_match ON box_score_verification(final_score_match);

COMMENT ON TABLE box_score_verification IS 'Verification results comparing generated vs actual box scores';
COMMENT ON COLUMN box_score_verification.quality_grade IS 'A=perfect, B=minor issues, C=moderate issues, F=failed verification';
COMMENT ON COLUMN box_score_verification.discrepancy_details IS 'JSON object with detailed breakdown of discrepancies by player';

-- ============================================================================
-- UTILITY VIEWS
-- ============================================================================

-- View: Latest snapshot per game
CREATE OR REPLACE VIEW latest_snapshots AS
SELECT DISTINCT ON (game_id, data_source)
    *
FROM game_state_snapshots
ORDER BY game_id, data_source, event_num DESC;

COMMENT ON VIEW latest_snapshots IS 'Final snapshot for each game (latest event_num)';

-- View: Verification summary by source
CREATE OR REPLACE VIEW verification_summary AS
SELECT
    data_source,
    COUNT(*) as total_games,
    COUNT(*) FILTER (WHERE quality_grade = 'A') as grade_a,
    COUNT(*) FILTER (WHERE quality_grade = 'B') as grade_b,
    COUNT(*) FILTER (WHERE quality_grade = 'C') as grade_c,
    COUNT(*) FILTER (WHERE quality_grade = 'F') as grade_f,
    ROUND(AVG(mae_points), 2) as avg_mae_points,
    ROUND(AVG(mae_rebounds), 2) as avg_mae_rebounds,
    ROUND(AVG(mae_assists), 2) as avg_mae_assists,
    COUNT(*) FILTER (WHERE final_score_match = true)::DECIMAL / COUNT(*) * 100 as pct_score_match
FROM box_score_verification
GROUP BY data_source;

COMMENT ON VIEW verification_summary IS 'Summary of verification results by data source';

-- ============================================================================
-- GRANTS (adjust as needed for your RDS user)
-- ============================================================================

-- Grant permissions to your application user (replace 'nba_app_user' with your actual user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON game_state_snapshots TO nba_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON player_snapshot_stats TO nba_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON quarter_box_scores TO nba_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON box_score_verification TO nba_app_user;
-- GRANT SELECT ON latest_snapshots TO nba_app_user;
-- GRANT SELECT ON verification_summary TO nba_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nba_app_user;

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

-- Example 1: Get all snapshots for a specific game
-- SELECT * FROM game_state_snapshots WHERE game_id = '401584903' ORDER BY event_num;

-- Example 2: Get player stats at snapshot 500 of a game
-- SELECT pss.*
-- FROM player_snapshot_stats pss
-- JOIN game_state_snapshots gss ON pss.snapshot_id = gss.snapshot_id
-- WHERE gss.game_id = '401584903' AND gss.event_num = 500;

-- Example 3: Get quarter-by-quarter stats for a player
-- SELECT * FROM quarter_box_scores
-- WHERE game_id = '401584903' AND player_id = '2544'
-- ORDER BY quarter;

-- Example 4: Get verification results for all ESPN games
-- SELECT * FROM box_score_verification
-- WHERE data_source = 'espn' AND quality_grade IN ('A', 'B')
-- ORDER BY verified_at DESC;

-- Example 5: Count snapshots per game
-- SELECT game_id, COUNT(*) as snapshot_count
-- FROM game_state_snapshots
-- GROUP BY game_id
-- ORDER BY snapshot_count DESC;

-- ============================================================================
-- DONE - Schema Ready for Phase 9
-- ============================================================================



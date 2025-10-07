-- ============================================================================
-- Game States Table
-- ============================================================================
--
-- Purpose: Reconstruct game state (score, lineups, possession) at any timestamp
-- Capacity: 10M+ rows
-- Storage: 5-10 GB
-- Use case: "What was the score and who was playing at 8:45:30 PM?"
--
-- Example query: "Show me all games at 9:00 PM ET on March 15, 2023"
-- ============================================================================

CREATE TABLE IF NOT EXISTS game_states (
    -- Primary Key
    state_id BIGSERIAL PRIMARY KEY,

    -- Game Context
    game_id VARCHAR(20) NOT NULL,
    state_time TIMESTAMP(3) NOT NULL,                   -- UTC timestamp of this state

    -- Score
    current_score_home INTEGER DEFAULT 0,
    current_score_away INTEGER DEFAULT 0,
    score_differential INTEGER,                         -- home - away

    -- Game Progress
    quarter INTEGER NOT NULL,
    game_clock_seconds INTEGER,                         -- Seconds remaining in quarter
    game_status VARCHAR(20),                            -- 'in_progress', 'halftime', 'final', 'scheduled'

    -- Possession
    possession_team_id INTEGER,                         -- Team currently with possession
    possession_arrow VARCHAR(10),                       -- 'home', 'away' (for jump balls)

    -- Active Lineups (stored as arrays)
    home_lineup INTEGER[],                              -- Array of 5 player IDs on court for home team
    away_lineup INTEGER[],                              -- Array of 5 player IDs on court for away team

    -- Situational Context
    last_scoring_play_time TIMESTAMP(3),                -- When last basket was scored
    scoring_run_home INTEGER DEFAULT 0,                 -- Points scored by home in current run
    scoring_run_away INTEGER DEFAULT 0,                 -- Points scored by away in current run
    timeouts_remaining_home INTEGER,                    -- Timeouts left for home team
    timeouts_remaining_away INTEGER,                    -- Timeouts left for away team

    -- Metadata
    created_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT fk_game_states_game FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    CONSTRAINT chk_quarter CHECK (quarter > 0),
    CONSTRAINT chk_game_clock CHECK (game_clock_seconds IS NULL OR (game_clock_seconds >= 0 AND game_clock_seconds <= 720)),
    CONSTRAINT chk_game_status CHECK (game_status IN ('in_progress', 'halftime', 'final', 'scheduled', 'postponed')),
    CONSTRAINT chk_lineup_size_home CHECK (array_length(home_lineup, 1) <= 5),
    CONSTRAINT chk_lineup_size_away CHECK (array_length(away_lineup, 1) <= 5),
    CONSTRAINT uq_game_state_time UNIQUE (game_id, state_time)
);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE game_states IS 'Game state snapshots at regular intervals. Enables reconstruction of game situation (score, lineups, possession) at any timestamp.';

COMMENT ON COLUMN game_states.state_id IS 'Unique state identifier (auto-incrementing)';
COMMENT ON COLUMN game_states.game_id IS 'Foreign key to games table';
COMMENT ON COLUMN game_states.state_time IS 'UTC timestamp when this state was recorded';
COMMENT ON COLUMN game_states.current_score_home IS 'Home team score at this timestamp';
COMMENT ON COLUMN game_states.current_score_away IS 'Away team score at this timestamp';
COMMENT ON COLUMN game_states.score_differential IS 'Score differential (home - away). Positive = home leading, negative = away leading';
COMMENT ON COLUMN game_states.quarter IS 'Quarter number (1-4, 5+ for overtime)';
COMMENT ON COLUMN game_states.game_clock_seconds IS 'Seconds remaining in quarter (0-720)';
COMMENT ON COLUMN game_states.possession_team_id IS 'Team currently with ball possession';
COMMENT ON COLUMN game_states.home_lineup IS 'Array of 5 player IDs on court for home team. Example: {977, 123, 456, 789, 101}';
COMMENT ON COLUMN game_states.away_lineup IS 'Array of 5 player IDs on court for away team. Example: {234, 567, 890, 112, 345}';
COMMENT ON COLUMN game_states.scoring_run_home IS 'Current scoring run for home team. Resets when opponent scores.';
COMMENT ON COLUMN game_states.scoring_run_away IS 'Current scoring run for away team. Resets when opponent scores.';

-- ============================================================================
-- Indexes (Created separately in 02_create_indexes.sql)
-- ============================================================================
--
-- BRIN index on state_time (time-series optimization)
-- B-tree index on game_id (fast game lookups)
-- Composite index on (game_id, state_time) for game state queries
-- GIN index on home_lineup and away_lineup arrays (lineup queries)
--
-- See: sql/temporal/02_create_indexes.sql
-- ============================================================================

-- ============================================================================
-- Triggers (Auto-Update Metadata and Calculated Fields)
-- ============================================================================

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_game_state_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    NEW.score_differential = NEW.current_score_home - NEW.current_score_away;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_game_states_updated_at
    BEFORE INSERT OR UPDATE ON game_states
    FOR EACH ROW
    EXECUTE FUNCTION update_game_state_timestamp();

-- ============================================================================
-- Usage Examples
-- ============================================================================
--
-- Example 1: Get game state at exact time
-- SELECT
--     current_score_home,
--     current_score_away,
--     quarter,
--     game_clock_seconds,
--     home_lineup,
--     away_lineup
-- FROM game_states
-- WHERE game_id = '401234567'
--   AND state_time = (
--       SELECT MAX(state_time)
--       FROM game_states
--       WHERE game_id = '401234567'
--         AND state_time <= '2016-06-19 19:02:34'::TIMESTAMPTZ
--   );
--
-- Example 2: Get all active games at specific time
-- SELECT
--     g.game_id,
--     g.home_team,
--     g.away_team,
--     gs.current_score_home,
--     gs.current_score_away,
--     gs.quarter,
--     gs.game_status
-- FROM games g
-- JOIN game_states gs ON g.game_id = gs.game_id
-- WHERE gs.state_time = (
--     SELECT MAX(state_time)
--     FROM game_states
--     WHERE game_id = g.game_id
--       AND state_time <= '2023-03-15 21:00:00-04:00'::TIMESTAMPTZ
-- )
-- AND g.game_date = '2023-03-15'
-- AND gs.game_status = 'in_progress';
--
-- Example 3: Find close games (within 5 points) in Q4
-- SELECT game_id, state_time, current_score_home, current_score_away
-- FROM game_states
-- WHERE quarter >= 4
--   AND game_clock_seconds <= 300  -- Last 5 minutes
--   AND ABS(score_differential) <= 5
-- ORDER BY state_time DESC;
--
-- Example 4: Track scoring runs
-- SELECT
--     game_id,
--     state_time,
--     scoring_run_home,
--     scoring_run_away,
--     GREATEST(scoring_run_home, scoring_run_away) AS max_run
-- FROM game_states
-- WHERE game_id = '401234567'
--   AND (scoring_run_home >= 10 OR scoring_run_away >= 10)
-- ORDER BY state_time;
--
-- Example 5: Find when specific player was on court
-- SELECT gs.game_id, gs.state_time, gs.quarter
-- FROM game_states gs
-- WHERE 977 = ANY(gs.home_lineup)  -- Kobe Bryant's player_id
--    OR 977 = ANY(gs.away_lineup)
-- ORDER BY gs.state_time;
--
-- ============================================================================

-- ============================================================================
-- Game State Generation Strategy
-- ============================================================================
--
-- Frequency: Every 1 minute of game time (~48 minutes per game)
-- Total: ~1,230 games/season × 48 minutes × 30 seasons = ~1.77M states
--
-- Additional states generated for:
-- - Every scoring event (basket, free throw)
-- - Every timeout
-- - Start/end of quarters
-- - Substitutions
--
-- Estimated total: 10M+ states
--
-- Storage: ~5-10 GB
--
-- See: scripts/etl/generate_game_states.py for generation logic
-- ============================================================================

-- ============================================================================
-- Validation Queries
-- ============================================================================
--
-- After generating states, run these queries to validate:
--
-- 1. Check row count
-- SELECT COUNT(*) FROM game_states;
-- Expected: 10M+ rows
--
-- 2. Check state distribution by game
-- SELECT game_id, COUNT(*) AS state_count
-- FROM game_states
-- GROUP BY game_id
-- ORDER BY state_count DESC
-- LIMIT 10;
-- Expected: ~200-300 states per game (48 min + scoring events + timeouts)
--
-- 3. Check for score anomalies (score should never decrease)
-- WITH game_scores AS (
--     SELECT game_id, state_time, current_score_home,
--            LAG(current_score_home) OVER (PARTITION BY game_id ORDER BY state_time) AS prev_score
--     FROM game_states
--     WHERE game_id = '401234567'
-- )
-- SELECT * FROM game_scores WHERE current_score_home < prev_score;
-- Expected: 0 rows (scores never decrease)
--
-- 4. Validate lineup sizes (should be 5 or fewer)
-- SELECT game_id, state_time,
--        array_length(home_lineup, 1) AS home_count,
--        array_length(away_lineup, 1) AS away_count
-- FROM game_states
-- WHERE array_length(home_lineup, 1) > 5
--    OR array_length(away_lineup, 1) > 5;
-- Expected: 0 rows (max 5 players on court)
--
-- 5. Check table size
-- SELECT pg_size_pretty(pg_total_relation_size('game_states'));
-- Expected: 5-10 GB after full generation
--
-- ============================================================================

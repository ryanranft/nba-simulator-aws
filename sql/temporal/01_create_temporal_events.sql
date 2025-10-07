-- ============================================================================
-- Temporal Events Table
-- ============================================================================
--
-- Purpose: Store all NBA events with millisecond-precision timestamps
-- Capacity: 500M+ rows
-- Storage: 200-300 GB
-- Use case: Event-level temporal queries
--
-- Example query: "Show me all shots in the last 2 minutes of Q4"
-- ============================================================================

CREATE TABLE IF NOT EXISTS temporal_events (
    -- Primary Key
    event_id BIGSERIAL PRIMARY KEY,

    -- Game Context
    game_id VARCHAR(20) NOT NULL,
    player_id VARCHAR(20),
    team_id VARCHAR(20),

    -- Temporal Precision (Dual Timestamp Strategy)
    wall_clock_utc TIMESTAMP(3) NOT NULL,              -- UTC wall clock (millisecond precision)
    wall_clock_local TIMESTAMP(3),                      -- Local time zone (for display)
    game_clock_seconds INTEGER,                         -- Seconds remaining in quarter (0-720)
    quarter INTEGER,                                    -- Quarter number (1-4, 5+ for OT)
    precision_level VARCHAR(10) NOT NULL,               -- 'millisecond', 'second', 'minute', 'game', 'unknown'

    -- Event Details
    event_type VARCHAR(50),                             -- 'made_shot', 'missed_shot', 'free_throw', 'rebound', etc.
    event_data JSONB,                                   -- Full play-by-play JSON (variable structure)

    -- Data Provenance
    data_source VARCHAR(20) NOT NULL,                   -- 'nba_live', 'nba_stats', 'espn', 'hoopr', 'basketball_ref', 'kaggle'

    -- Metadata
    created_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT fk_temporal_events_game FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    CONSTRAINT chk_precision_level CHECK (precision_level IN ('millisecond', 'second', 'minute', 'game', 'unknown')),
    CONSTRAINT chk_quarter CHECK (quarter > 0),
    CONSTRAINT chk_game_clock CHECK (game_clock_seconds IS NULL OR (game_clock_seconds >= 0 AND game_clock_seconds <= 720))
);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE temporal_events IS 'Event-level temporal data with millisecond precision timestamps. Core table for temporal panel data queries.';

COMMENT ON COLUMN temporal_events.event_id IS 'Unique event identifier (auto-incrementing)';
COMMENT ON COLUMN temporal_events.game_id IS 'Foreign key to games table';
COMMENT ON COLUMN temporal_events.wall_clock_utc IS 'Real-world timestamp in UTC (millisecond precision)';
COMMENT ON COLUMN temporal_events.wall_clock_local IS 'Local timezone timestamp for display purposes';
COMMENT ON COLUMN temporal_events.game_clock_seconds IS 'Seconds remaining in quarter (0-720 for 12-minute quarters)';
COMMENT ON COLUMN temporal_events.quarter IS 'Quarter number (1-4, 5+ for overtime periods)';
COMMENT ON COLUMN temporal_events.precision_level IS 'Temporal precision flag: millisecond (NBA Live API), second (NBA Stats API), minute (ESPN), game (Basketball Ref)';
COMMENT ON COLUMN temporal_events.event_type IS 'Type of event: made_shot, missed_shot, free_throw, rebound, assist, turnover, foul, substitution, etc.';
COMMENT ON COLUMN temporal_events.event_data IS 'Full play-by-play JSON data (variable structure depending on event type). Queryable with JSONB operators.';
COMMENT ON COLUMN temporal_events.data_source IS 'Source of data: nba_live, nba_stats, espn, hoopr, basketball_ref, kaggle';

-- ============================================================================
-- Indexes (Created separately in 02_create_indexes.sql)
-- ============================================================================
--
-- BRIN index on wall_clock_utc (created after data load for efficiency)
-- GIN index on event_data JSONB (for JSON queries)
-- B-tree indexes on frequently filtered columns
--
-- See: sql/temporal/02_create_indexes.sql
-- ============================================================================

-- ============================================================================
-- Usage Examples
-- ============================================================================
--
-- Example 1: Get all events in a time range
-- SELECT * FROM temporal_events
-- WHERE wall_clock_utc BETWEEN '2016-06-19 19:00:00' AND '2016-06-19 22:00:00'
-- ORDER BY wall_clock_utc;
--
-- Example 2: Get all shots in last 2 minutes of Q4
-- SELECT * FROM temporal_events
-- WHERE quarter = 4
--   AND game_clock_seconds <= 120
--   AND event_type LIKE '%shot%'
-- ORDER BY wall_clock_utc DESC;
--
-- Example 3: Query JSONB event data
-- SELECT event_id, wall_clock_utc, event_data->>'shot_distance' AS distance
-- FROM temporal_events
-- WHERE event_type = 'made_shot'
--   AND (event_data->>'shot_distance')::INTEGER > 25;
--
-- Example 4: Filter by precision level
-- SELECT COUNT(*) FROM temporal_events
-- WHERE precision_level IN ('millisecond', 'second')
--   AND wall_clock_utc >= '2020-01-01';
--
-- ============================================================================

-- ============================================================================
-- Validation Queries
-- ============================================================================
--
-- After loading data, run these queries to validate:
--
-- 1. Check row count
-- SELECT COUNT(*) FROM temporal_events;
-- Expected: 10M+ rows minimum (2004-2021), 500M+ target (1996-2025)
--
-- 2. Check precision distribution
-- SELECT precision_level, COUNT(*) AS events
-- FROM temporal_events
-- GROUP BY precision_level
-- ORDER BY precision_level;
--
-- 3. Check data source distribution
-- SELECT data_source, COUNT(*) AS events
-- FROM temporal_events
-- GROUP BY data_source
-- ORDER BY COUNT(*) DESC;
--
-- 4. Check for duplicates
-- SELECT game_id, player_id, wall_clock_utc, COUNT(*)
-- FROM temporal_events
-- GROUP BY game_id, player_id, wall_clock_utc
-- HAVING COUNT(*) > 1;
-- Expected: 0 rows (no duplicates)
--
-- 5. Check table size
-- SELECT pg_size_pretty(pg_total_relation_size('temporal_events'));
-- Expected: 200-300 GB after full data load
--
-- ============================================================================

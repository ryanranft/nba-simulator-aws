-- ============================================================================
-- Player Snapshots Table
-- ============================================================================
--
-- Purpose: Pre-computed cumulative player statistics at checkpoints
-- Capacity: 50M+ rows
-- Storage: 10-20 GB
-- Use case: Fast snapshot queries (< 1 second)
--
-- Example query: "What were Kobe's career stats at exactly 7:02:34 PM on June 19, 2016?"
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_snapshots (
    -- Primary Key
    snapshot_id BIGSERIAL PRIMARY KEY,

    -- Player Context
    player_id VARCHAR(20) NOT NULL,
    snapshot_time TIMESTAMP(3) NOT NULL,                -- UTC timestamp of snapshot

    -- Cumulative Career Statistics (to date)
    games_played INTEGER DEFAULT 0,
    minutes_played INTEGER DEFAULT 0,

    -- Scoring
    career_points INTEGER DEFAULT 0,
    career_field_goals_made INTEGER DEFAULT 0,
    career_field_goals_attempted INTEGER DEFAULT 0,
    career_fg_pct NUMERIC(5, 3),                        -- Field goal percentage
    career_three_pointers_made INTEGER DEFAULT 0,
    career_three_pointers_attempted INTEGER DEFAULT 0,
    career_three_pt_pct NUMERIC(5, 3),                  -- 3-point percentage
    career_free_throws_made INTEGER DEFAULT 0,
    career_free_throws_attempted INTEGER DEFAULT 0,
    career_ft_pct NUMERIC(5, 3),                        -- Free throw percentage

    -- Rebounding
    career_rebounds INTEGER DEFAULT 0,
    career_offensive_rebounds INTEGER DEFAULT 0,
    career_defensive_rebounds INTEGER DEFAULT 0,

    -- Playmaking
    career_assists INTEGER DEFAULT 0,
    career_turnovers INTEGER DEFAULT 0,
    career_assist_to_turnover_ratio NUMERIC(5, 3),

    -- Defense
    career_steals INTEGER DEFAULT 0,
    career_blocks INTEGER DEFAULT 0,
    career_personal_fouls INTEGER DEFAULT 0,

    -- Advanced Stats
    career_plus_minus INTEGER DEFAULT 0,
    career_true_shooting_pct NUMERIC(5, 3),
    career_effective_fg_pct NUMERIC(5, 3),
    career_usage_rate NUMERIC(5, 3),
    career_player_efficiency_rating NUMERIC(6, 2),

    -- Per-Game Averages (at this snapshot)
    ppg NUMERIC(5, 2),                                  -- Points per game
    rpg NUMERIC(5, 2),                                  -- Rebounds per game
    apg NUMERIC(5, 2),                                  -- Assists per game
    spg NUMERIC(5, 2),                                  -- Steals per game
    bpg NUMERIC(5, 2),                                  -- Blocks per game

    -- Snapshot Metadata
    snapshot_type VARCHAR(20),                          -- 'game_end', 'quarter_end', 'custom'
    checkpoint_interval VARCHAR(20),                    -- 'per_game', 'per_quarter', 'per_minute'

    -- Metadata
    created_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT fk_player_snapshots_player FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE,
    CONSTRAINT chk_snapshot_type CHECK (snapshot_type IN ('game_end', 'quarter_end', 'custom')),
    CONSTRAINT uq_player_snapshot_time UNIQUE (player_id, snapshot_time)
);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE player_snapshots IS 'Pre-computed cumulative player statistics at regular intervals. Enables fast snapshot queries without aggregating temporal_events.';

COMMENT ON COLUMN player_snapshots.snapshot_id IS 'Unique snapshot identifier (auto-incrementing)';
COMMENT ON COLUMN player_snapshots.player_id IS 'Foreign key to players table';
COMMENT ON COLUMN player_snapshots.snapshot_time IS 'UTC timestamp when snapshot was taken';
COMMENT ON COLUMN player_snapshots.games_played IS 'Total games played up to this snapshot';
COMMENT ON COLUMN player_snapshots.career_points IS 'Total career points up to this snapshot';
COMMENT ON COLUMN player_snapshots.career_fg_pct IS 'Career field goal percentage at this snapshot';
COMMENT ON COLUMN player_snapshots.snapshot_type IS 'Type of snapshot: game_end (after each game), quarter_end (after each quarter), custom (ad-hoc)';
COMMENT ON COLUMN player_snapshots.checkpoint_interval IS 'Snapshot generation frequency: per_game (18M snapshots), per_quarter (50K/season), per_minute (custom)';

-- ============================================================================
-- Indexes (Created separately in 02_create_indexes.sql)
-- ============================================================================
--
-- BRIN index on snapshot_time (time-series optimization)
-- B-tree index on player_id (fast player lookups)
-- Composite index on (player_id, snapshot_time) for snapshot queries
--
-- See: sql/temporal/02_create_indexes.sql
-- ============================================================================

-- ============================================================================
-- Triggers (Auto-Update Metadata)
-- ============================================================================

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_player_snapshot_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_player_snapshots_updated_at
    BEFORE UPDATE ON player_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION update_player_snapshot_timestamp();

-- ============================================================================
-- Usage Examples
-- ============================================================================
--
-- Example 1: Get player snapshot at exact time (using stored procedure)
-- SELECT * FROM get_player_snapshot_at_time(977, '2016-06-19 19:02:34'::TIMESTAMPTZ);
--
-- Example 2: Get all snapshots for a player
-- SELECT snapshot_time, career_points, career_rebounds, career_assists
-- FROM player_snapshots
-- WHERE player_id = 977
-- ORDER BY snapshot_time DESC
-- LIMIT 100;
--
-- Example 3: Compare multiple players at same time
-- SELECT p.name, ps.career_points, ps.career_rebounds
-- FROM players p
-- JOIN player_snapshots ps ON p.player_id = ps.player_id
-- WHERE ps.snapshot_time = (
--     SELECT MAX(snapshot_time)
--     FROM player_snapshots
--     WHERE snapshot_time <= '2016-06-19 19:02:34'::TIMESTAMPTZ
-- )
-- AND p.name IN ('Kobe Bryant', 'LeBron James', 'Michael Jordan');
--
-- Example 4: Get snapshot frequency distribution
-- SELECT checkpoint_interval, COUNT(*) AS snapshot_count
-- FROM player_snapshots
-- GROUP BY checkpoint_interval;
--
-- ============================================================================

-- ============================================================================
-- Snapshot Generation Strategy
-- ============================================================================
--
-- Baseline: After each game (~1,230 games/season × 500 players × 30 seasons)
-- Total: ~18M snapshots
-- Storage: ~10 GB
--
-- Optional: After each quarter (~1,230 games × 4 qtrs × 10 active players/game)
-- Total: ~50K snapshots per season
-- Storage: +500 MB
--
-- Tradeoff:
-- - More snapshots = faster queries (< 1s) but higher storage cost
-- - Fewer snapshots = slower queries (2-5s aggregation) but lower cost
--
-- Recommended: Generate per-game snapshots (baseline), add per-quarter for
-- recent seasons (2020+) or key players only.
--
-- See: scripts/etl/generate_player_snapshots.py for generation logic
-- ============================================================================

-- ============================================================================
-- Validation Queries
-- ============================================================================
--
-- After generating snapshots, run these queries to validate:
--
-- 1. Check row count
-- SELECT COUNT(*) FROM player_snapshots;
-- Expected: 18M+ rows (per-game snapshots)
--
-- 2. Check snapshot distribution by year
-- SELECT DATE_TRUNC('year', snapshot_time) AS year,
--        COUNT(*) AS snapshots,
--        COUNT(DISTINCT player_id) AS players
-- FROM player_snapshots
-- GROUP BY year
-- ORDER BY year;
--
-- 3. Check for missing players (should have snapshots)
-- SELECT p.player_id, p.name
-- FROM players p
-- LEFT JOIN player_snapshots ps ON p.player_id = ps.player_id
-- WHERE ps.snapshot_id IS NULL
--   AND p.active = true;
-- Expected: 0 rows (all active players should have snapshots)
--
-- 4. Validate monotonicity (career stats never decrease)
-- WITH player_stats AS (
--     SELECT player_id, snapshot_time, career_points,
--            LAG(career_points) OVER (PARTITION BY player_id ORDER BY snapshot_time) AS prev_points
--     FROM player_snapshots
--     WHERE player_id = 977  -- Kobe Bryant
-- )
-- SELECT * FROM player_stats WHERE career_points < prev_points;
-- Expected: 0 rows (career stats should never decrease)
--
-- 5. Check table size
-- SELECT pg_size_pretty(pg_total_relation_size('player_snapshots'));
-- Expected: 10-20 GB after full generation
--
-- ============================================================================

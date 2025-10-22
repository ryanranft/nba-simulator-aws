-- Interval Box Score Views
-- Created: October 19, 2025
-- Purpose: SQL views for time-based interval box scores
--          Supports 6min, 3min, 1:30, 1min intervals
--          Special OT handling: 2:30 halves and 1-minute intervals

-- ============================================================================
-- TIME-BASED SNAPSHOT VIEWS
-- ============================================================================

-- View: Get snapshots within a specific time range
-- Used for calculating interval-only stats

CREATE VIEW IF NOT EXISTS vw_snapshots_by_time_range AS
SELECT
    p.*,
    -- Calculate minutes elapsed for easier interval partitioning
    CAST(p.time_elapsed_seconds / 60.0 AS REAL) as minutes_elapsed,
    -- Identify if this is regulation or OT
    CASE
        WHEN p.period <= 4 THEN 'regulation'
        ELSE 'overtime'
    END as period_type,
    -- OT period number (0 for regulation, 1 for OT1, 2 for OT2, etc.)
    CASE
        WHEN p.period <= 4 THEN 0
        ELSE p.period - 4
    END as ot_number
FROM player_box_score_snapshots p;

-- Index for fast time-range queries
CREATE INDEX IF NOT EXISTS idx_player_snapshots_time_range
    ON player_box_score_snapshots(game_id, time_elapsed_seconds, event_number);

-- ============================================================================
-- INTERVAL BOUNDARY SNAPSHOTS
-- ============================================================================

-- View: Get snapshot closest to a specific elapsed time
-- This is used to find the "boundary" snapshot for each interval

CREATE VIEW IF NOT EXISTS vw_interval_boundaries AS
SELECT
    p.game_id,
    p.player_id,
    p.player_name,
    p.team_id,
    p.period,
    p.time_elapsed_seconds,
    p.event_number,
    -- All cumulative stats at this moment
    p.points, p.fgm, p.fga, p.fg_pct,
    p.fg3m, p.fg3a, p.fg3_pct,
    p.ftm, p.fta, p.ft_pct,
    p.reb, p.oreb, p.dreb,
    p.ast, p.stl, p.blk, p.tov, p.pf,
    p.minutes,
    -- Advanced stats
    p.true_shooting_pct, p.effective_fg_pct, p.three_point_attempt_rate,
    p.usage_rate, p.assist_percentage, p.steal_percentage, p.block_percentage,
    p.turnover_rate, p.offensive_rating, p.box_plus_minus,
    p.offensive_rebound_pct, p.defensive_rebound_pct, p.total_rebound_pct
FROM player_box_score_snapshots p;

-- ============================================================================
-- TEAM INTERVAL VIEWS
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_team_snapshots_by_time_range AS
SELECT
    t.*,
    CAST(t.time_elapsed_seconds / 60.0 AS REAL) as minutes_elapsed,
    CASE
        WHEN t.period <= 4 THEN 'regulation'
        ELSE 'overtime'
    END as period_type,
    CASE
        WHEN t.period <= 4 THEN 0
        ELSE t.period - 4
    END as ot_number
FROM team_box_score_snapshots t;

-- Index for team time-range queries
CREATE INDEX IF NOT EXISTS idx_team_snapshots_time_range
    ON team_box_score_snapshots(game_id, time_elapsed_seconds, event_number);

-- ============================================================================
-- REGULATION INTERVAL HELPERS
-- ============================================================================

-- View: 6-minute interval boundaries (8 per regulation game)
-- Intervals: 0-6, 6-12, 12-18, 18-24, 24-30, 30-36, 36-42, 42-48

CREATE VIEW IF NOT EXISTS vw_6min_intervals AS
SELECT
    game_id,
    interval_number,
    start_seconds,
    end_seconds,
    CAST(start_seconds / 60.0 AS TEXT) || '-' || CAST(end_seconds / 60.0 AS TEXT) || ' min' as interval_label
FROM (
    SELECT DISTINCT game_id FROM player_box_score_snapshots
) games
CROSS JOIN (
    SELECT 1 as interval_number, 0 as start_seconds, 360 as end_seconds
    UNION SELECT 2, 360, 720
    UNION SELECT 3, 720, 1080
    UNION SELECT 4, 1080, 1440
    UNION SELECT 5, 1440, 1800
    UNION SELECT 6, 1800, 2160
    UNION SELECT 7, 2160, 2520
    UNION SELECT 8, 2520, 2880
) intervals;

-- View: 3-minute interval boundaries (16 per regulation game)
CREATE VIEW IF NOT EXISTS vw_3min_intervals AS
SELECT
    game_id,
    interval_number,
    start_seconds,
    end_seconds,
    CAST(start_seconds / 60.0 AS TEXT) || '-' || CAST(end_seconds / 60.0 AS TEXT) || ' min' as interval_label
FROM (
    SELECT DISTINCT game_id FROM player_box_score_snapshots
) games
CROSS JOIN (
    -- 16 3-minute intervals
    SELECT 1 as interval_number, 0 as start_seconds, 180 as end_seconds
    UNION SELECT 2, 180, 360
    UNION SELECT 3, 360, 540
    UNION SELECT 4, 540, 720
    UNION SELECT 5, 720, 900
    UNION SELECT 6, 900, 1080
    UNION SELECT 7, 1080, 1260
    UNION SELECT 8, 1260, 1440
    UNION SELECT 9, 1440, 1620
    UNION SELECT 10, 1620, 1800
    UNION SELECT 11, 1800, 1980
    UNION SELECT 12, 1980, 2160
    UNION SELECT 13, 2160, 2340
    UNION SELECT 14, 2340, 2520
    UNION SELECT 15, 2520, 2700
    UNION SELECT 16, 2700, 2880
) intervals;

-- View: 1:30 (90-second) interval boundaries (32 per regulation game)
CREATE VIEW IF NOT EXISTS vw_90sec_intervals AS
SELECT
    game_id,
    interval_number,
    start_seconds,
    end_seconds,
    CAST(start_seconds / 60.0 AS TEXT) || '-' || CAST(end_seconds / 60.0 AS TEXT) || ' min' as interval_label
FROM (
    SELECT DISTINCT game_id FROM player_box_score_snapshots
) games
CROSS JOIN (
    -- 32 90-second intervals (generated programmatically in Python)
    -- This is a sample - full implementation would have all 32
    SELECT 1 as interval_number, 0 as start_seconds, 90 as end_seconds
    UNION SELECT 2, 90, 180
    UNION SELECT 3, 180, 270
    UNION SELECT 4, 270, 360
    -- ... (would continue to 32 intervals)
) intervals;

-- View: 1-minute interval boundaries (48 per regulation game)
CREATE VIEW IF NOT EXISTS vw_1min_intervals AS
SELECT
    game_id,
    interval_number,
    start_seconds,
    end_seconds,
    CAST(interval_number - 1 AS TEXT) || '-' || CAST(interval_number AS TEXT) || ' min' as interval_label
FROM (
    SELECT DISTINCT game_id FROM player_box_score_snapshots
) games
CROSS JOIN (
    -- 48 1-minute intervals
    SELECT 1 as interval_number, 0 as start_seconds, 60 as end_seconds
    UNION SELECT 2, 60, 120
    UNION SELECT 3, 120, 180
    -- ... (would continue to 48 intervals)
    -- Full implementation in Python
) intervals;

-- ============================================================================
-- OVERTIME INTERVAL HELPERS
-- ============================================================================

-- View: OT 2:30 (half) intervals
-- Each 5-minute OT period split into two 2:30 halves

CREATE VIEW IF NOT EXISTS vw_ot_half_intervals AS
SELECT
    p.game_id,
    p.period as ot_period,
    p.period - 4 as ot_number,
    half_number,
    start_seconds_in_ot,
    end_seconds_in_ot,
    'OT' || CAST(p.period - 4 AS TEXT) || ' ' || start_seconds_in_ot || '-' || end_seconds_in_ot || 's' as interval_label
FROM (
    SELECT DISTINCT game_id, period
    FROM player_box_score_snapshots
    WHERE period > 4  -- Only OT periods
) p
CROSS JOIN (
    SELECT 1 as half_number, 0 as start_seconds_in_ot, 150 as end_seconds_in_ot
    UNION SELECT 2, 150, 300
) halves;

-- View: OT 1-minute intervals
-- Each 5-minute OT period split into 5 one-minute intervals

CREATE VIEW IF NOT EXISTS vw_ot_minute_intervals AS
SELECT
    p.game_id,
    p.period as ot_period,
    p.period - 4 as ot_number,
    minute_number,
    start_seconds_in_ot,
    end_seconds_in_ot,
    'OT' || CAST(p.period - 4 AS TEXT) || ' ' || CAST(minute_number - 1 AS TEXT) || '-' || CAST(minute_number AS TEXT) || 'min' as interval_label
FROM (
    SELECT DISTINCT game_id, period
    FROM player_box_score_snapshots
    WHERE period > 4  -- Only OT periods
) p
CROSS JOIN (
    SELECT 1 as minute_number, 0 as start_seconds_in_ot, 60 as end_seconds_in_ot
    UNION SELECT 2, 60, 120
    UNION SELECT 3, 120, 180
    UNION SELECT 4, 180, 240
    UNION SELECT 5, 240, 300
) minutes;

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Query 1: Get all snapshots in a specific 6-minute interval
/*
SELECT p.*
FROM player_box_score_snapshots p
WHERE p.game_id = '202410220BOS'
  AND p.time_elapsed_seconds >= 360  -- Start of second 6-min interval
  AND p.time_elapsed_seconds < 720   -- End of second 6-min interval
ORDER BY p.player_id, p.event_number;
*/

-- Query 2: Find snapshot closest to 6-minute mark (360 seconds)
/*
SELECT p.*
FROM player_box_score_snapshots p
WHERE p.game_id = '202410220BOS'
  AND p.player_id = 'tatumja01'
  AND p.time_elapsed_seconds <= 360
ORDER BY p.time_elapsed_seconds DESC
LIMIT 1;
*/

-- Query 3: Get OT1 first half (0-2:30) snapshots
/*
SELECT p.*
FROM player_box_score_snapshots p
WHERE p.game_id = '202410220BOS'
  AND p.period = 5  -- OT1
  AND p.time_elapsed_seconds >= 2880  -- Start of OT1 (48 min * 60 sec)
  AND p.time_elapsed_seconds < 3030   -- 2:30 into OT1
ORDER BY p.player_id, p.event_number;
*/

-- Query 4: Team stats for each 3-minute interval
/*
SELECT
    i.interval_number,
    i.interval_label,
    t.team_id,
    MAX(t.points) as interval_end_points
FROM vw_3min_intervals i
JOIN team_box_score_snapshots t
    ON t.game_id = i.game_id
    AND t.time_elapsed_seconds >= i.start_seconds
    AND t.time_elapsed_seconds < i.end_seconds
WHERE i.game_id = '202410220BOS'
GROUP BY i.interval_number, t.team_id
ORDER BY i.interval_number, t.team_id;
*/

-- ============================================================================
-- NOTES FOR PYTHON IMPLEMENTATION
-- ============================================================================

/*
These views provide the foundation for interval queries, but the actual
delta calculations (interval-only stats) are best done in Python:

1. For each interval, query the snapshot at the START and END
2. Calculate delta: end_stats - start_stats = interval_stats
3. Calculate all advanced statistics for the interval
4. Repeat for all intervals

Example Python pattern:
    start_snapshot = get_snapshot_at_time(interval_start)
    end_snapshot = get_snapshot_at_time(interval_end)
    interval_stats = calculate_delta(end_snapshot, start_snapshot)
    advanced_stats = calculate_advanced_stats(interval_stats)

This approach:
- Reuses existing temporal snapshot data
- Works with any interval size
- Provides all advanced statistics per interval
- No schema changes required
*/

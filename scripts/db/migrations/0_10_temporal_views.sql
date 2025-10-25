-- ============================================================================
-- Phase 0.10: Temporal Integration - Materialized Views
-- ============================================================================
-- Purpose: Pre-compute common temporal queries for performance
-- Created: October 25, 2025
-- Implementation ID: rec_033_postgresql_temporal
--
-- These materialized views join JSONB raw data with temporal tables
-- to enable fast millisecond-precision historical queries.
--
-- Refresh strategy: REFRESH MATERIALIZED VIEW <name> (hourly recommended)
-- ============================================================================

-- ============================================================================
-- 1. Player Game Temporal View
-- ============================================================================
-- Joins JSONB game data with player temporal snapshots
-- Enables: "What were LeBron's career stats when he played Game X?"

CREATE MATERIALIZED VIEW IF NOT EXISTS raw_data.player_game_temporal AS
SELECT
    -- Game identifiers
    g.game_id,
    g.game_date,
    g.season,
    g.source as game_source,

    -- Team info from JSONB
    g.data->>'home_team' as home_team,
    g.data->>'away_team' as away_team,
    g.data->'home_score' as home_score,
    g.data->'away_score' as away_score,

    -- Player identifiers
    p.player_id,
    p.player_name,

    -- Player temporal snapshot (career stats at game time)
    ps.career_points as career_points_before_game,
    ps.career_assists as career_assists_before_game,
    ps.career_rebounds as career_rebounds_before_game,
    ps.career_steals as career_steals_before_game,
    ps.career_blocks as career_blocks_before_game,
    ps.career_field_goals_made as career_fg_made_before_game,
    ps.career_field_goals_attempted as career_fg_att_before_game,
    ps.career_three_pointers_made as career_3pt_made_before_game,
    ps.career_three_pointers_attempted as career_3pt_att_before_game,
    ps.games_played as games_played_before,
    ps.minutes_played as minutes_played_before,
    ps.snapshot_time as snapshot_timestamp,

    -- Calculated shooting percentages at game time
    CASE
        WHEN ps.career_field_goals_attempted > 0
        THEN ps.career_field_goals_made::float / ps.career_field_goals_attempted
        ELSE 0
    END as career_fg_pct_at_game,

    CASE
        WHEN ps.career_three_pointers_attempted > 0
        THEN ps.career_three_pointers_made::float / ps.career_three_pointers_attempted
        ELSE 0
    END as career_3pt_pct_at_game,

    -- Age at game (from biographical data)
    EXTRACT(EPOCH FROM (g.game_date::timestamp - pb.birth_date::timestamp)) / 31557600.0 as age_at_game_years,

    -- Metadata
    g.collected_at as game_collected_at,
    p.collected_at as player_collected_at

FROM raw_data.nba_games g
INNER JOIN raw_data.nba_players p
    ON g.season = p.season
    AND g.source = p.source
LEFT JOIN player_snapshots ps
    ON p.player_id = ps.player_id
    AND ps.snapshot_time <= g.game_date
    AND ps.snapshot_time >= g.game_date - INTERVAL '7 days'  -- Approximate match
LEFT JOIN player_biographical pb
    ON p.player_id = pb.player_id
WHERE g.game_date IS NOT NULL
  AND p.player_id IS NOT NULL;

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_player_game_temporal_player_date
    ON raw_data.player_game_temporal(player_id, game_date);

CREATE INDEX IF NOT EXISTS idx_player_game_temporal_game
    ON raw_data.player_game_temporal(game_id);

CREATE INDEX IF NOT EXISTS idx_player_game_temporal_season
    ON raw_data.player_game_temporal(season);

COMMENT ON MATERIALIZED VIEW raw_data.player_game_temporal IS
    'Pre-joined player games with temporal career stats. Enables fast queries like: "What were LeBrons career stats when he played this game?"';

-- ============================================================================
-- 2. Team Performance Temporal View
-- ============================================================================
-- Aggregated team performance with temporal indexing
-- Enables: Fast team statistics queries bounded by time

CREATE MATERIALIZED VIEW IF NOT EXISTS raw_data.team_performance_temporal AS
SELECT
    -- Team & time identifiers
    COALESCE(g.data->>'home_team', g.data->>'away_team') as team_abbr,
    g.season,
    DATE_TRUNC('month', g.game_date) as month,
    g.game_date,

    -- Game counts
    COUNT(DISTINCT g.game_id) as games_played,
    COUNT(DISTINCT CASE WHEN g.data->>'home_team' = COALESCE(g.data->>'home_team', g.data->>'away_team') THEN g.game_id END) as home_games,
    COUNT(DISTINCT CASE WHEN g.data->>'away_team' = COALESCE(g.data->>'home_team', g.data->>'away_team') THEN g.game_id END) as away_games,

    -- Win/loss tracking (requires scores in JSONB)
    COUNT(DISTINCT
        CASE
            WHEN (g.data->>'home_team' = COALESCE(g.data->>'home_team', g.data->>'away_team')
                  AND (g.data->'home_score')::int > (g.data->'away_score')::int)
            OR   (g.data->>'away_team' = COALESCE(g.data->>'home_team', g.data->>'away_team')
                  AND (g.data->'away_score')::int > (g.data->'home_score')::int)
            THEN g.game_id
        END
    ) as wins,

    -- Temporal bounds
    MIN(g.game_date) as first_game_date,
    MAX(g.game_date) as last_game_date,
    MAX(g.collected_at) as last_updated,

    -- Source tracking
    g.source as data_source

FROM raw_data.nba_games g
WHERE g.game_date IS NOT NULL
  AND (g.data->>'home_team' IS NOT NULL OR g.data->>'away_team' IS NOT NULL)
GROUP BY
    COALESCE(g.data->>'home_team', g.data->>'away_team'),
    g.season,
    DATE_TRUNC('month', g.game_date),
    g.game_date,
    g.source;

-- Index for temporal filtering
CREATE INDEX IF NOT EXISTS idx_team_perf_temporal_team_season
    ON raw_data.team_performance_temporal(team_abbr, season);

CREATE INDEX IF NOT EXISTS idx_team_perf_temporal_date
    ON raw_data.team_performance_temporal(game_date);

COMMENT ON MATERIALIZED VIEW raw_data.team_performance_temporal IS
    'Aggregated team performance metrics with temporal bounds. Enables fast team stats queries.';

-- ============================================================================
-- 3. Game Situations Temporal View
-- ============================================================================
-- Pre-joined game states with JSONB context
-- Enables: Fast game situation queries for simulation context

CREATE MATERIALIZED VIEW IF NOT EXISTS raw_data.game_situations_temporal AS
SELECT
    -- Game identifiers
    gs.game_id,
    g.game_date,
    g.season,
    g.source,

    -- Team info from JSONB
    g.data->>'home_team' as home_team,
    g.data->>'away_team' as away_team,

    -- Game state temporal data
    gs.state_time as state_timestamp,
    gs.quarter,
    gs.game_clock_seconds as time_remaining_seconds,
    gs.current_score_home as home_score,
    gs.current_score_away as away_score,
    gs.score_differential,
    gs.possession_team_id,
    NULL::integer as home_timeouts_remaining,  -- Not in current schema
    NULL::integer as away_timeouts_remaining,  -- Not in current schema

    -- Lineups (not in current schema - use NULL arrays)
    NULL::varchar[] as home_lineup,
    NULL::varchar[] as away_lineup,
    0 as home_lineup_size,
    0 as away_lineup_size,

    -- Game situation categorization
    CASE
        WHEN gs.quarter = 4 AND gs.game_clock_seconds < 300 THEN 'crunch_time'
        WHEN ABS(gs.score_differential) > 20 THEN 'blowout'
        WHEN ABS(gs.score_differential) <= 5 THEN 'close_game'
        ELSE 'regular'
    END as situation_category,

    -- JSONB context (not in current schema)
    NULL::jsonb as state_details_jsonb,

    -- Metadata
    g.collected_at as game_collected_at

FROM game_states gs
INNER JOIN raw_data.nba_games g
    ON gs.game_id = g.game_id
WHERE gs.state_time IS NOT NULL;

-- Indexes for temporal queries
CREATE INDEX IF NOT EXISTS idx_game_situations_temporal_game_time
    ON raw_data.game_situations_temporal(game_id, state_timestamp);

CREATE INDEX IF NOT EXISTS idx_game_situations_temporal_date
    ON raw_data.game_situations_temporal(game_date);

CREATE INDEX IF NOT EXISTS idx_game_situations_temporal_category
    ON raw_data.game_situations_temporal(situation_category);

COMMENT ON MATERIALIZED VIEW raw_data.game_situations_temporal IS
    'Pre-joined game states with JSONB context. Enables fast "What was the game situation at timestamp X?" queries for simulations.';

-- ============================================================================
-- 4. Player Career Timeline View
-- ============================================================================
-- Temporal snapshot of player career progression
-- Enables: Career trajectory visualizations and aging analysis

CREATE MATERIALIZED VIEW IF NOT EXISTS raw_data.player_career_timeline AS
SELECT
    -- Player identifiers
    ps.player_id,
    ps.player_id as player_name,  -- Use player_id as name since biographical doesn't have name
    pb.birth_date,

    -- Temporal info
    ps.snapshot_time as snapshot_timestamp,
    DATE_PART('year', ps.snapshot_time) as season_year,
    EXTRACT(EPOCH FROM (ps.snapshot_time::timestamp - pb.birth_date::timestamp)) / 31557600.0 as age_at_snapshot,

    -- Career cumulative stats
    ps.career_points,
    ps.career_assists,
    ps.career_rebounds,
    ps.career_steals,
    ps.career_blocks,
    ps.career_turnovers,
    ps.games_played as career_games_played,
    ps.minutes_played as career_minutes_played,

    -- Per-game averages (calculated)
    CASE
        WHEN ps.games_played > 0
        THEN ps.career_points::float / ps.games_played
        ELSE 0
    END as ppg_at_snapshot,

    CASE
        WHEN ps.games_played > 0
        THEN ps.career_assists::float / ps.games_played
        ELSE 0
    END as apg_at_snapshot,

    CASE
        WHEN ps.games_played > 0
        THEN ps.career_rebounds::float / ps.games_played
        ELSE 0
    END as rpg_at_snapshot,

    -- Shooting efficiency (using existing career_fg_pct column)
    ps.career_fg_pct,

    CASE
        WHEN ps.career_three_pointers_attempted > 0
        THEN ps.career_three_pointers_made::float / ps.career_three_pointers_attempted
        ELSE 0
    END as career_3pt_pct,

    -- Career phase classification
    CASE
        WHEN ps.games_played < 50 THEN 'rookie'
        WHEN ps.games_played < 200 THEN 'early_career'
        WHEN ps.games_played < 500 THEN 'prime'
        WHEN ps.games_played < 800 THEN 'veteran'
        ELSE 'late_career'
    END as career_phase

FROM player_snapshots ps
INNER JOIN player_biographical pb
    ON ps.player_id = pb.player_id
WHERE ps.snapshot_time IS NOT NULL;

-- Indexes for timeline queries
CREATE INDEX IF NOT EXISTS idx_player_career_timeline_player
    ON raw_data.player_career_timeline(player_id, snapshot_timestamp);

CREATE INDEX IF NOT EXISTS idx_player_career_timeline_phase
    ON raw_data.player_career_timeline(career_phase);

COMMENT ON MATERIALIZED VIEW raw_data.player_career_timeline IS
    'Player career progression over time. Enables career arc analysis and aging effects modeling.';

-- ============================================================================
-- Helper View: Data Availability Summary
-- ============================================================================
-- Shows which temporal queries are possible for which games/players

CREATE OR REPLACE VIEW raw_data.temporal_data_availability AS
SELECT
    'games_with_states' as metric,
    COUNT(DISTINCT g.game_id) as count,
    MIN(g.game_date) as earliest_date,
    MAX(g.game_date) as latest_date
FROM raw_data.nba_games g
INNER JOIN game_states gs ON g.game_id = gs.game_id

UNION ALL

SELECT
    'games_with_events' as metric,
    COUNT(DISTINCT g.game_id) as count,
    MIN(g.game_date) as earliest_date,
    MAX(g.game_date) as latest_date
FROM raw_data.nba_games g
INNER JOIN temporal_events te ON g.game_id = te.game_id

UNION ALL

SELECT
    'players_with_snapshots' as metric,
    COUNT(DISTINCT p.player_id) as count,
    MIN(ps.snapshot_time::date) as earliest_date,
    MAX(ps.snapshot_time::date) as latest_date
FROM raw_data.nba_players p
INNER JOIN player_snapshots ps ON p.player_id = ps.player_id

UNION ALL

SELECT
    'players_with_biographical' as metric,
    COUNT(DISTINCT player_id) as count,
    MIN(birth_date) as earliest_date,
    MAX(birth_date) as latest_date
FROM player_biographical;

COMMENT ON VIEW raw_data.temporal_data_availability IS
    'Summary of temporal data coverage. Use this to check what queries are supported.';

-- ============================================================================
-- Refresh Functions
-- ============================================================================
-- Convenient functions to refresh all temporal views at once

CREATE OR REPLACE FUNCTION raw_data.refresh_all_temporal_views()
RETURNS TABLE(view_name text, refresh_duration interval) AS $$
DECLARE
    start_time timestamptz;
    end_time timestamptz;
BEGIN
    -- Refresh player_game_temporal
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW raw_data.player_game_temporal;
    end_time := clock_timestamp();
    view_name := 'player_game_temporal';
    refresh_duration := end_time - start_time;
    RETURN NEXT;

    -- Refresh team_performance_temporal
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW raw_data.team_performance_temporal;
    end_time := clock_timestamp();
    view_name := 'team_performance_temporal';
    refresh_duration := end_time - start_time;
    RETURN NEXT;

    -- Refresh game_situations_temporal
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW raw_data.game_situations_temporal;
    end_time := clock_timestamp();
    view_name := 'game_situations_temporal';
    refresh_duration := end_time - start_time;
    RETURN NEXT;

    -- Refresh player_career_timeline
    start_time := clock_timestamp();
    REFRESH MATERIALIZED VIEW raw_data.player_career_timeline;
    end_time := clock_timestamp();
    view_name := 'player_career_timeline';
    refresh_duration := end_time - start_time;
    RETURN NEXT;

    RETURN;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION raw_data.refresh_all_temporal_views() IS
    'Refresh all temporal materialized views and report duration for each. Run this hourly or after major data updates.';

-- ============================================================================
-- Usage Examples
-- ============================================================================

/*
-- Refresh all views:
SELECT * FROM raw_data.refresh_all_temporal_views();

-- Check data availability:
SELECT * FROM raw_data.temporal_data_availability;

-- Query player game temporal:
SELECT *
FROM raw_data.player_game_temporal
WHERE player_name LIKE '%LeBron%'
  AND game_date = '2020-10-11'
LIMIT 10;

-- Query game situations:
SELECT *
FROM raw_data.game_situations_temporal
WHERE game_id = '401359859'
  AND situation_category = 'crunch_time'
ORDER BY state_timestamp;

-- Query career timeline:
SELECT *
FROM raw_data.player_career_timeline
WHERE player_name = 'LeBron James'
ORDER BY snapshot_timestamp;
*/

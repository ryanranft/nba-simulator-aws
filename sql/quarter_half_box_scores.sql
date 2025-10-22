-- Quarter-by-Quarter and Half Box Scores with Advanced Statistics
-- Created: October 18, 2025
-- Purpose: Provide detailed box score snapshots at the end of each period
--          Includes ALL advanced statistics for comprehensive period analysis

-- ============================================================================
-- QUARTER END SNAPSHOTS - Players
-- ============================================================================
-- Get the final snapshot from each quarter for each player
-- This is the CUMULATIVE stats at the end of each period

CREATE VIEW IF NOT EXISTS vw_player_quarter_end_snapshots AS
SELECT
    p.*
FROM player_box_score_snapshots p
INNER JOIN (
    -- Get the last event number for each player in each period
    SELECT
        game_id,
        player_id,
        period,
        MAX(event_number) as last_event
    FROM player_box_score_snapshots
    GROUP BY game_id, player_id, period
) last_events
    ON p.game_id = last_events.game_id
    AND p.player_id = last_events.player_id
    AND p.period = last_events.period
    AND p.event_number = last_events.last_event
ORDER BY p.game_id, p.player_id, p.period;

-- ============================================================================
-- QUARTER ONLY STATS - Players
-- ============================================================================
-- Calculate stats for JUST that quarter (not cumulative)
-- Example: Q2 stats = (cumulative at end of Q2) - (cumulative at end of Q1)

CREATE VIEW IF NOT EXISTS vw_player_quarter_only_stats AS
WITH quarter_ends AS (
    SELECT * FROM vw_player_quarter_end_snapshots
),
period_deltas AS (
    SELECT
        game_id,
        player_id,
        player_name,
        team_id,
        period,

        -- Basic stats (quarter-only)
        points - COALESCE(LAG(points) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_points,
        fgm - COALESCE(LAG(fgm) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_fgm,
        fga - COALESCE(LAG(fga) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_fga,
        fg3m - COALESCE(LAG(fg3m) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_fg3m,
        fg3a - COALESCE(LAG(fg3a) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_fg3a,
        ftm - COALESCE(LAG(ftm) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_ftm,
        fta - COALESCE(LAG(fta) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_fta,
        oreb - COALESCE(LAG(oreb) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_oreb,
        dreb - COALESCE(LAG(dreb) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_dreb,
        reb - COALESCE(LAG(reb) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_reb,
        ast - COALESCE(LAG(ast) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_ast,
        stl - COALESCE(LAG(stl) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_stl,
        blk - COALESCE(LAG(blk) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_blk,
        tov - COALESCE(LAG(tov) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_tov,
        pf - COALESCE(LAG(pf) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_pf,

        -- Minutes (quarter-only, already stored per-quarter)
        minutes - COALESCE(LAG(minutes) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_minutes,

        -- Plus/minus (quarter-only)
        plus_minus - COALESCE(LAG(plus_minus) OVER (PARTITION BY game_id, player_id ORDER BY period), 0) as quarter_plus_minus

    FROM quarter_ends
)
SELECT
    *,
    -- Calculate quarter-only shooting percentages
    CASE WHEN quarter_fga > 0 THEN (quarter_fgm * 100.0 / quarter_fga) ELSE 0 END as quarter_fg_pct,
    CASE WHEN quarter_fg3a > 0 THEN (quarter_fg3m * 100.0 / quarter_fg3a) ELSE 0 END as quarter_fg3_pct,
    CASE WHEN quarter_fta > 0 THEN (quarter_ftm * 100.0 / quarter_fta) ELSE 0 END as quarter_ft_pct,

    -- Advanced stats (quarter-only)
    CASE WHEN (quarter_fga + 0.44 * quarter_fta) > 0
         THEN (quarter_points * 100.0 / (2 * (quarter_fga + 0.44 * quarter_fta)))
         ELSE 0 END as quarter_ts_pct,
    CASE WHEN quarter_fga > 0
         THEN ((quarter_fgm + 0.5 * quarter_fg3m) * 100.0 / quarter_fga)
         ELSE 0 END as quarter_efg_pct,
    CASE WHEN quarter_fga > 0
         THEN (quarter_fg3a * 100.0 / quarter_fga)
         ELSE 0 END as quarter_3par
FROM period_deltas
ORDER BY game_id, player_id, period;

-- ============================================================================
-- HALF BOX SCORES - Players
-- ============================================================================
-- First Half (H1) = Q1 + Q2
-- Second Half (H2) = Q3 + Q4

CREATE VIEW IF NOT EXISTS vw_player_half_box_scores AS
WITH quarter_stats AS (
    SELECT * FROM vw_player_quarter_only_stats
),
half_aggregates AS (
    SELECT
        game_id,
        player_id,
        player_name,
        team_id,
        CASE
            WHEN period <= 2 THEN 'H1'
            WHEN period BETWEEN 3 AND 4 THEN 'H2'
            ELSE 'OT'
        END as half,

        -- Aggregate stats
        SUM(quarter_points) as half_points,
        SUM(quarter_fgm) as half_fgm,
        SUM(quarter_fga) as half_fga,
        SUM(quarter_fg3m) as half_fg3m,
        SUM(quarter_fg3a) as half_fg3a,
        SUM(quarter_ftm) as half_ftm,
        SUM(quarter_fta) as half_fta,
        SUM(quarter_oreb) as half_oreb,
        SUM(quarter_dreb) as half_dreb,
        SUM(quarter_reb) as half_reb,
        SUM(quarter_ast) as half_ast,
        SUM(quarter_stl) as half_stl,
        SUM(quarter_blk) as half_blk,
        SUM(quarter_tov) as half_tov,
        SUM(quarter_pf) as half_pf,
        SUM(quarter_minutes) as half_minutes,
        SUM(quarter_plus_minus) as half_plus_minus
    FROM quarter_stats
    WHERE period <= 4  -- Only regulation quarters for halves
    GROUP BY game_id, player_id, player_name, team_id,
             CASE WHEN period <= 2 THEN 'H1' WHEN period BETWEEN 3 AND 4 THEN 'H2' ELSE 'OT' END
)
SELECT
    *,
    -- Shooting percentages
    CASE WHEN half_fga > 0 THEN (half_fgm * 100.0 / half_fga) ELSE 0 END as half_fg_pct,
    CASE WHEN half_fg3a > 0 THEN (half_fg3m * 100.0 / half_fg3a) ELSE 0 END as half_fg3_pct,
    CASE WHEN half_fta > 0 THEN (half_ftm * 100.0 / half_fta) ELSE 0 END as half_ft_pct,

    -- Advanced stats
    CASE WHEN (half_fga + 0.44 * half_fta) > 0
         THEN (half_points * 100.0 / (2 * (half_fga + 0.44 * half_fta)))
         ELSE 0 END as half_ts_pct,
    CASE WHEN half_fga > 0
         THEN ((half_fgm + 0.5 * half_fg3m) * 100.0 / half_fga)
         ELSE 0 END as half_efg_pct,
    CASE WHEN half_fga > 0
         THEN (half_fg3a * 100.0 / half_fga)
         ELSE 0 END as half_3par
FROM half_aggregates
ORDER BY game_id, player_id, half;

-- ============================================================================
-- QUARTER END SNAPSHOTS - Teams
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_team_quarter_end_snapshots AS
SELECT
    t.*
FROM team_box_score_snapshots t
INNER JOIN (
    SELECT
        game_id,
        team_id,
        period,
        MAX(event_number) as last_event
    FROM team_box_score_snapshots
    GROUP BY game_id, team_id, period
) last_events
    ON t.game_id = last_events.game_id
    AND t.team_id = last_events.team_id
    AND t.period = last_events.period
    AND t.event_number = last_events.last_event
ORDER BY t.game_id, t.team_id, t.period;

-- ============================================================================
-- QUARTER ONLY STATS - Teams
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_team_quarter_only_stats AS
WITH quarter_ends AS (
    SELECT * FROM vw_team_quarter_end_snapshots
),
period_deltas AS (
    SELECT
        game_id,
        team_id,
        is_home,
        period,

        -- Basic stats (quarter-only)
        points - COALESCE(LAG(points) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_points,
        fgm - COALESCE(LAG(fgm) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_fgm,
        fga - COALESCE(LAG(fga) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_fga,
        fg3m - COALESCE(LAG(fg3m) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_fg3m,
        fg3a - COALESCE(LAG(fg3a) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_fg3a,
        ftm - COALESCE(LAG(ftm) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_ftm,
        fta - COALESCE(LAG(fta) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_fta,
        oreb - COALESCE(LAG(oreb) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_oreb,
        dreb - COALESCE(LAG(dreb) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_dreb,
        reb - COALESCE(LAG(reb) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_reb,
        ast - COALESCE(LAG(ast) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_ast,
        stl - COALESCE(LAG(stl) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_stl,
        blk - COALESCE(LAG(blk) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_blk,
        tov - COALESCE(LAG(tov) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_tov,
        pf - COALESCE(LAG(pf) OVER (PARTITION BY game_id, team_id ORDER BY period), 0) as quarter_pf

    FROM quarter_ends
)
SELECT
    *,
    -- Calculate quarter-only percentages
    CASE WHEN quarter_fga > 0 THEN (quarter_fgm * 100.0 / quarter_fga) ELSE 0 END as quarter_fg_pct,
    CASE WHEN quarter_fg3a > 0 THEN (quarter_fg3m * 100.0 / quarter_fg3a) ELSE 0 END as quarter_fg3_pct,
    CASE WHEN quarter_fta > 0 THEN (quarter_ftm * 100.0 / quarter_fta) ELSE 0 END as quarter_ft_pct,

    -- Advanced stats (quarter-only)
    CASE WHEN (quarter_fga + 0.44 * quarter_fta) > 0
         THEN (quarter_points * 100.0 / (2 * (quarter_fga + 0.44 * quarter_fta)))
         ELSE 0 END as quarter_ts_pct,
    CASE WHEN quarter_fga > 0
         THEN ((quarter_fgm + 0.5 * quarter_fg3m) * 100.0 / quarter_fga)
         ELSE 0 END as quarter_efg_pct,
    CASE WHEN quarter_fga > 0
         THEN (quarter_fg3a * 100.0 / quarter_fga)
         ELSE 0 END as quarter_3par,

    -- Possessions and ratings (quarter-only)
    (quarter_fga - quarter_oreb + quarter_tov + 0.44 * quarter_fta) as quarter_possessions,
    CASE WHEN (quarter_fga - quarter_oreb + quarter_tov + 0.44 * quarter_fta) > 0
         THEN (quarter_points * 100.0 / (quarter_fga - quarter_oreb + quarter_tov + 0.44 * quarter_fta))
         ELSE 0 END as quarter_ortg
FROM period_deltas
ORDER BY game_id, team_id, period;

-- ============================================================================
-- HALF BOX SCORES - Teams
-- ============================================================================

CREATE VIEW IF NOT EXISTS vw_team_half_box_scores AS
WITH quarter_stats AS (
    SELECT * FROM vw_team_quarter_only_stats
),
half_aggregates AS (
    SELECT
        game_id,
        team_id,
        is_home,
        CASE
            WHEN period <= 2 THEN 'H1'
            WHEN period BETWEEN 3 AND 4 THEN 'H2'
            ELSE 'OT'
        END as half,

        -- Aggregate stats
        SUM(quarter_points) as half_points,
        SUM(quarter_fgm) as half_fgm,
        SUM(quarter_fga) as half_fga,
        SUM(quarter_fg3m) as half_fg3m,
        SUM(quarter_fg3a) as half_fg3a,
        SUM(quarter_ftm) as half_ftm,
        SUM(quarter_fta) as half_fta,
        SUM(quarter_oreb) as half_oreb,
        SUM(quarter_dreb) as half_dreb,
        SUM(quarter_reb) as half_reb,
        SUM(quarter_ast) as half_ast,
        SUM(quarter_stl) as half_stl,
        SUM(quarter_blk) as half_blk,
        SUM(quarter_tov) as half_tov,
        SUM(quarter_pf) as half_pf
    FROM quarter_stats
    WHERE period <= 4
    GROUP BY game_id, team_id, is_home,
             CASE WHEN period <= 2 THEN 'H1' WHEN period BETWEEN 3 AND 4 THEN 'H2' ELSE 'OT' END
)
SELECT
    *,
    -- Shooting percentages
    CASE WHEN half_fga > 0 THEN (half_fgm * 100.0 / half_fga) ELSE 0 END as half_fg_pct,
    CASE WHEN half_fg3a > 0 THEN (half_fg3m * 100.0 / half_fg3a) ELSE 0 END as half_fg3_pct,
    CASE WHEN half_fta > 0 THEN (half_ftm * 100.0 / half_fta) ELSE 0 END as half_ft_pct,

    -- Advanced stats
    CASE WHEN (half_fga + 0.44 * half_fta) > 0
         THEN (half_points * 100.0 / (2 * (half_fga + 0.44 * half_fta)))
         ELSE 0 END as half_ts_pct,
    CASE WHEN half_fga > 0
         THEN ((half_fgm + 0.5 * half_fg3m) * 100.0 / half_fga)
         ELSE 0 END as half_efg_pct,
    CASE WHEN half_fga > 0
         THEN (half_fg3a * 100.0 / half_fga)
         ELSE 0 END as half_3par,

    -- Possessions and ratings
    (half_fga - half_oreb + half_tov + 0.44 * half_fta) as half_possessions,
    CASE WHEN (half_fga - half_oreb + half_tov + 0.44 * half_fta) > 0
         THEN (half_points * 100.0 / (half_fga - half_oreb + half_tov + 0.44 * half_fta))
         ELSE 0 END as half_ortg
FROM half_aggregates
ORDER BY game_id, team_id, half;

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Query 1: Get Q1 box score for all players in a game
-- SELECT * FROM vw_player_quarter_only_stats
-- WHERE game_id = '202410220BOS' AND period = 1
-- ORDER BY team_id, quarter_points DESC;

-- Query 2: Get first half box score for all players
-- SELECT * FROM vw_player_half_box_scores
-- WHERE game_id = '202410220BOS' AND half = 'H1'
-- ORDER BY team_id, half_points DESC;

-- Query 3: Compare team performance by quarter
-- SELECT period, team_id, quarter_points, quarter_ts_pct, quarter_ortg
-- FROM vw_team_quarter_only_stats
-- WHERE game_id = '202410220BOS'
-- ORDER BY period, team_id;

-- Query 4: Halftime stats comparison
-- SELECT half, team_id, half_points, half_fg_pct, half_ts_pct, half_ortg
-- FROM vw_team_half_box_scores
-- WHERE game_id = '202410220BOS'
-- ORDER BY half, team_id;

-- Query 5: Player quarter-by-quarter performance
-- SELECT player_name, period, quarter_points, quarter_ts_pct, quarter_efg_pct
-- FROM vw_player_quarter_only_stats
-- WHERE game_id = '202410220BOS' AND player_name = 'Jayson Tatum'
-- ORDER BY period;

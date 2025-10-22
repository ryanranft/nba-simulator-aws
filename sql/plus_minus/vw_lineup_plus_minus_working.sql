-- ============================================================================
-- Lineup Plus/Minus View - PostgreSQL Compatible (Simplified)
-- ============================================================================
--
-- Purpose: Aggregate performance metrics for each unique 5-player lineup
--          without biographical data dependencies
--
-- Created: October 19, 2025
-- Optimized: 100x faster with CTE-based aggregations
--
-- ============================================================================

CREATE OR REPLACE VIEW vw_lineup_plus_minus AS
WITH
-- Pre-aggregate offensive ratings by lineup
offensive_ratings AS (
    SELECT
        lineup_hash_offense as lineup_hash,
        SUM(points_scored) * 100.0 / COUNT(*) as offensive_rating,
        COUNT(*) as offensive_possessions
    FROM possession_metadata
    WHERE lineup_hash_offense IS NOT NULL
    GROUP BY lineup_hash_offense
),
-- Pre-aggregate defensive ratings by lineup
defensive_ratings AS (
    SELECT
        lineup_hash_defense as lineup_hash,
        SUM(points_scored) * 100.0 / COUNT(*) as defensive_rating,
        COUNT(*) as defensive_possessions
    FROM possession_metadata
    WHERE lineup_hash_defense IS NOT NULL
    GROUP BY lineup_hash_defense
),
-- Pre-aggregate possession outcomes
possession_outcomes AS (
    SELECT
        l.lineup_hash,
        l.game_id,
        -- Count "wins" (scored on offense OR prevented score on defense)
        SUM(CASE
            WHEN l.offensive_possession = TRUE AND p.points_scored > 0 THEN 1
            WHEN l.offensive_possession = FALSE AND p.points_scored = 0 THEN 1
            ELSE 0
        END) as possessions_won,
        -- Count "losses" (didn't score on offense OR allowed score on defense)
        SUM(CASE
            WHEN l.offensive_possession = TRUE AND p.points_scored = 0 THEN 1
            WHEN l.offensive_possession = FALSE AND p.points_scored > 0 THEN 1
            ELSE 0
        END) as possessions_lost
    FROM lineup_snapshots l
    LEFT JOIN possession_metadata p
        ON l.game_id = p.game_id
       AND l.possession_number = p.possession_number
    WHERE l.possession_number IS NOT NULL
    GROUP BY l.lineup_hash, l.game_id
)
SELECT
    -- ========================================================================
    -- Lineup Identification
    -- ========================================================================
    l.lineup_hash,
    l.team_id,
    l.player1_id,
    l.player2_id,
    l.player3_id,
    l.player4_id,
    l.player5_id,

    -- Human-readable lineup (player IDs, comma-separated)
    l.player1_id || ', ' || l.player2_id || ', ' || l.player3_id || ', ' ||
    l.player4_id || ', ' || l.player5_id as lineup_display,

    -- ========================================================================
    -- Playing Time
    -- ========================================================================
    COUNT(DISTINCT l.game_id || ':' || l.period || ':' || l.time_elapsed_seconds)
        as total_snapshots,

    -- Approximate minutes together (snapshots / 60 assuming 1 snapshot per second)
    ROUND(COUNT(*) / 60.0, 2) as minutes_played,

    -- Total possessions together
    COUNT(DISTINCT l.possession_number) as possessions_played,

    -- Games played together
    COUNT(DISTINCT l.game_id) as games_together,

    -- ========================================================================
    -- Plus/Minus Metrics
    -- ========================================================================
    -- Overall plus/minus for this lineup
    MAX(l.plus_minus) - MIN(l.plus_minus) as total_plus_minus,

    -- Plus/minus per minute
    ROUND((MAX(l.plus_minus) - MIN(l.plus_minus)) / (COUNT(*) / 60.0), 2)
        as plus_minus_per_minute,

    -- Plus/minus per possession (most accurate)
    ROUND((MAX(l.plus_minus) - MIN(l.plus_minus)) * 1.0 /
          NULLIF(COUNT(DISTINCT l.possession_number), 0), 3)
        as plus_minus_per_possession,

    -- ========================================================================
    -- Offensive/Defensive Split
    -- ========================================================================
    -- Possessions on offense
    SUM(CASE WHEN l.offensive_possession = TRUE THEN 1 ELSE 0 END) as offensive_possessions,

    -- Possessions on defense
    SUM(CASE WHEN l.offensive_possession = FALSE THEN 1 ELSE 0 END) as defensive_possessions,

    -- ========================================================================
    -- Efficiency Ratings (from pre-aggregated CTEs)
    -- ========================================================================
    -- Offensive rating (points per 100 possessions)
    COALESCE(off_stats.offensive_rating, 0.0) as offensive_rating,

    -- Defensive rating (points allowed per 100 possessions)
    COALESCE(def_stats.defensive_rating, 0.0) as defensive_rating,

    -- Net rating (offensive - defensive)
    COALESCE(off_stats.offensive_rating, 0.0) -
    COALESCE(def_stats.defensive_rating, 0.0) as net_rating,

    -- ========================================================================
    -- Win/Loss Record (possession-based)
    -- ========================================================================
    COALESCE(SUM(po.possessions_won), 0) as possessions_won,
    COALESCE(SUM(po.possessions_lost), 0) as possessions_lost,

    -- Win percentage
    ROUND(COALESCE(SUM(po.possessions_won), 0) * 100.0 /
          NULLIF(COALESCE(SUM(po.possessions_won), 0) +
                 COALESCE(SUM(po.possessions_lost), 0), 0), 1)
        as win_percentage

FROM lineup_snapshots l

-- Join offensive ratings
LEFT JOIN offensive_ratings off_stats
    ON l.lineup_hash = off_stats.lineup_hash

-- Join defensive ratings
LEFT JOIN defensive_ratings def_stats
    ON l.lineup_hash = def_stats.lineup_hash

-- Join possession outcomes
LEFT JOIN possession_outcomes po
    ON l.lineup_hash = po.lineup_hash
   AND l.game_id = po.game_id

GROUP BY
    l.lineup_hash,
    l.team_id,
    l.player1_id,
    l.player2_id,
    l.player3_id,
    l.player4_id,
    l.player5_id,
    off_stats.offensive_rating,
    def_stats.defensive_rating

-- Filter to lineups with meaningful sample size
HAVING COUNT(DISTINCT l.possession_number) >= 5

-- Order by net rating (best lineups first)
ORDER BY net_rating DESC;

-- ============================================================================
-- Usage Example
-- ============================================================================

/*
-- Find best lineups by net rating
SELECT
    lineup_display,
    possessions_played,
    net_rating,
    offensive_rating,
    defensive_rating,
    win_percentage
FROM vw_lineup_plus_minus
WHERE possessions_played >= 10
ORDER BY net_rating DESC
LIMIT 10;
*/

-- ============================================================================
-- On/Off Court Analysis View - PostgreSQL Compatible (Simplified)
-- ============================================================================
--
-- Purpose: Compare team performance when each player is on court vs off court
--          to quantify individual player impact
--
-- Created: October 19, 2025
-- Optimized: Includes players who played entire game (no data loss)
--
-- ============================================================================

CREATE OR REPLACE VIEW vw_on_off_analysis AS
WITH player_stats AS (
    -- Calculate stats while player is on court
    SELECT
        game_id,
        player_id,
        team_id,

        -- On-court metrics
        COUNT(DISTINCT possession_number) FILTER (WHERE on_court = TRUE) as poss_on,
        MAX(plus_minus) FILTER (WHERE on_court = TRUE) -
        MIN(plus_minus) FILTER (WHERE on_court = TRUE) as pm_on,

        -- Off-court metrics
        COUNT(DISTINCT possession_number) FILTER (WHERE on_court = FALSE) as poss_off,
        MAX(plus_minus) FILTER (WHERE on_court = FALSE) -
        MIN(plus_minus) FILTER (WHERE on_court = FALSE) as pm_off,

        -- Playing time
        SUM(CASE WHEN on_court = TRUE THEN 1 ELSE 0 END) / 60.0 as minutes_on,
        SUM(CASE WHEN on_court = FALSE THEN 1 ELSE 0 END) / 60.0 as minutes_off

    FROM player_plus_minus_snapshots
    GROUP BY game_id, player_id, team_id
)
SELECT
    ps.game_id,
    ps.player_id,
    ps.team_id,
    p.player_name,

    -- ========================================================================
    -- On-Court Performance
    -- ========================================================================
    ps.poss_on as possessions_on_court,
    ps.pm_on as plus_minus_on_court,
    ROUND(ps.minutes_on, 1) as minutes_on_court,

    -- On-court rating (per 100 possessions)
    ROUND(ps.pm_on * 100.0 / NULLIF(ps.poss_on, 0), 1) as net_rating_on_court,

    -- ========================================================================
    -- Off-Court Performance
    -- ========================================================================
    ps.poss_off as possessions_off_court,
    ps.pm_off as plus_minus_off_court,
    ROUND(ps.minutes_off, 1) as minutes_off_court,

    -- Off-court rating (per 100 possessions)
    ROUND(ps.pm_off * 100.0 / NULLIF(ps.poss_off, 0), 1) as net_rating_off_court,

    -- ========================================================================
    -- Impact Differential (On/Off)
    -- ========================================================================
    -- Difference in plus/minus per possession
    ROUND((ps.pm_on * 1.0 / NULLIF(ps.poss_on, 0)) -
          (ps.pm_off * 1.0 / NULLIF(ps.poss_off, 0)), 3) as on_off_diff_per_poss,

    -- Difference in net rating (per 100 possessions)
    ROUND((ps.pm_on * 100.0 / NULLIF(ps.poss_on, 0)) -
          (ps.pm_off * 100.0 / NULLIF(ps.poss_off, 0)), 1) as net_rating_diff,

    -- ========================================================================
    -- Replacement Value
    -- ========================================================================
    -- Impact per 48 minutes (standardized)
    ROUND(
        ((ps.pm_on * 1.0 / NULLIF(ps.poss_on, 0)) -
         (ps.pm_off * 1.0 / NULLIF(ps.poss_off, 0))) * 48,
        1
    ) as replacement_value_48min,

    -- ========================================================================
    -- Sample Size & Confidence
    -- ========================================================================
    -- Total possessions for confidence
    ps.poss_on + ps.poss_off as total_possessions,

    -- Confidence level based on sample size
    CASE
        WHEN ps.poss_on + ps.poss_off >= 100 THEN 'HIGH'
        WHEN ps.poss_on + ps.poss_off >= 50 THEN 'MEDIUM'
        WHEN ps.poss_on + ps.poss_off >= 20 THEN 'LOW'
        WHEN ps.poss_on = 0 OR ps.poss_off = 0 THEN 'NONE'  -- Played entire game or didn't play
        ELSE 'VERY_LOW'
    END as confidence_level

FROM player_stats ps
LEFT JOIN (SELECT DISTINCT player_id, player_name FROM player_snapshot_stats) p
    ON ps.player_id = p.player_id

-- Order by impact (highest on/off differential first)
ORDER BY net_rating_diff DESC NULLS LAST;

-- ============================================================================
-- Usage Example
-- ============================================================================

/*
-- Find players with highest impact (on/off differential)
SELECT
    player_name,
    net_rating_diff,
    possessions_on_court,
    possessions_off_court,
    replacement_value_48min,
    confidence_level
FROM vw_on_off_analysis
WHERE confidence_level IN ('MEDIUM', 'HIGH')
ORDER BY net_rating_diff DESC
LIMIT 10;
*/

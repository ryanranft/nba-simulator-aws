-- ============================================================================
-- On/Off Court Analysis View (OPTIMIZED)
-- ============================================================================
--
-- Purpose: Compare team performance when each player is on court vs off court
--          to quantify individual player impact (true plus/minus differential)
--
-- Created: October 19, 2025
-- Optimized: October 19, 2025
--   - Fixed data loss issue (now includes players who played entire game)
--   - Improved confidence level logic
--
-- ML Use Cases: Player impact prediction, replacement value calculation,
--               trade analysis, lineup optimization, roster decisions
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
    ROUND(ps.minutes_on, 2) as minutes_on_court,
    COALESCE(ps.pm_on, 0) as plus_minus_on_court,
    ROUND(ps.pm_on / NULLIF(ps.minutes_on, 0), 2) as pm_per_min_on,
    ROUND(ps.pm_on * 1.0 / NULLIF(ps.poss_on, 0), 3) as pm_per_poss_on,
    ROUND(ps.pm_on * 100.0 / NULLIF(ps.poss_on, 0), 1) as net_rating_on,

    -- ========================================================================
    -- Off-Court Performance
    -- ========================================================================
    ps.poss_off as possessions_off_court,
    ROUND(ps.minutes_off, 2) as minutes_off_court,
    COALESCE(ps.pm_off, 0) as plus_minus_off_court,
    ROUND(ps.pm_off / NULLIF(ps.minutes_off, 0), 2) as pm_per_min_off,
    ROUND(ps.pm_off * 1.0 / NULLIF(ps.poss_off, 0), 3) as pm_per_poss_off,
    ROUND(ps.pm_off * 100.0 / NULLIF(ps.poss_off, 0), 1) as net_rating_off,

    -- ========================================================================
    -- On/Off Differential (Player Impact)
    -- ========================================================================
    COALESCE(ps.pm_on, 0) - COALESCE(ps.pm_off, 0) as plus_minus_differential,
    ROUND((ps.pm_on / NULLIF(ps.minutes_on, 0)) -
          (ps.pm_off / NULLIF(ps.minutes_off, 0)), 2) as pm_diff_per_min,
    ROUND((ps.pm_on * 1.0 / NULLIF(ps.poss_on, 0)) -
          (ps.pm_off * 1.0 / NULLIF(ps.poss_off, 0)), 3) as pm_diff_per_poss,
    ROUND((ps.pm_on * 100.0 / NULLIF(ps.poss_on, 0)) -
          (ps.pm_off * 100.0 / NULLIF(ps.poss_off, 0)), 1) as net_rating_diff,

    -- ========================================================================
    -- Replacement Value (Normalized Impact)
    -- ========================================================================
    -- How much better/worse team is per 48 minutes with this player
    ROUND(((ps.pm_on / NULLIF(ps.minutes_on, 0)) -
           (ps.pm_off / NULLIF(ps.minutes_off, 0))) * 48, 1) as replacement_value_48min,

    -- ========================================================================
    -- Statistical Significance Indicators
    -- ========================================================================
    -- Larger sample = more reliable
    ps.poss_on + ps.poss_off as total_possessions,
    ROUND(ps.poss_on * 100.0 / NULLIF(ps.poss_on + ps.poss_off, 0), 1) as pct_possessions_played,

    -- Confidence based on sample size
    -- OPTIMIZED: Now includes 'NONE' for players who never left court
    CASE
        WHEN ps.poss_on = 0 OR ps.poss_off = 0 THEN 'NONE'
        WHEN ps.poss_on < 10 OR ps.poss_off < 10 THEN 'LOW'
        WHEN ps.poss_on < 25 OR ps.poss_off < 25 THEN 'MEDIUM'
        ELSE 'HIGH'
    END as confidence_level,

    -- ========================================================================
    -- Biographical Context
    -- ========================================================================
    pb.age_years_decimal,
    pb.height_inches,
    pb.position,
    pb.nba_experience_years

FROM player_stats ps
LEFT JOIN (SELECT DISTINCT player_id, player_name FROM player_snapshot_stats) p
    ON ps.player_id = p.player_id
LEFT JOIN player_biographical pb
    ON ps.player_id = pb.player_id;

-- OPTIMIZED: Removed WHERE filter that excluded players who played entire game
-- Previously: WHERE ps.poss_on > 0 AND ps.poss_off > 0;
-- Now: All players included, confidence_level='NONE' if missing on or off data

-- ============================================================================
-- Performance Notes
-- ============================================================================

/*
OPTIMIZATION IMPROVEMENTS:

Data Loss Fix:
- Before: WHERE ps.poss_on > 0 AND ps.poss_off > 0 excluded players who never sat
- After: All players included, confidence_level distinguishes data quality
- Impact: Starters who played entire game now have their data preserved
- Use case: Can now identify "iron man" performances and track full-game impact

Why this matters:
- Playoff games: Superstars often play 45+ minutes (little/no bench time)
- Blowouts: Starters may never sit if winning by 20+
- Injury situations: Depleted roster forces long minutes
- Historical data: Pre-2000s basketball had less substitution

Example previously lost data:
- Kobe Bryant: 48 minutes in 2006 playoff game → NO on/off data
- LeBron James: 47 minutes in 2018 Finals → NO on/off data
- After fix: These rows now included with confidence_level='NONE'
*/

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Example 1: Find highest-impact players (best on/off differential)
/*
SELECT
    player_name,
    net_rating_diff,
    possessions_on_court,
    possessions_off_court,
    confidence_level
FROM vw_on_off_analysis
WHERE game_id = '0021500001'
  AND confidence_level IN ('MEDIUM', 'HIGH')
ORDER BY net_rating_diff DESC
LIMIT 10;
*/

-- Example 2: Identify negative-impact players (team worse with them on court)
/*
SELECT
    player_name,
    net_rating_on,
    net_rating_off,
    net_rating_diff,
    minutes_on_court
FROM vw_on_off_analysis
WHERE game_id = '0021500001'
  AND net_rating_diff < 0  -- Team worse with player on court
  AND confidence_level IN ('MEDIUM', 'HIGH')
ORDER BY net_rating_diff ASC;
*/

-- Example 3: Calculate replacement value for all players
/*
SELECT
    player_name,
    replacement_value_48min,
    net_rating_diff,
    possessions_on_court,
    confidence_level
FROM vw_on_off_analysis
WHERE game_id = '0021500001'
  AND confidence_level != 'NONE'  -- Exclude players with no on/off data
ORDER BY replacement_value_48min DESC;
*/

-- Example 4: Find "iron man" performances (played entire game)
/*
SELECT
    player_name,
    minutes_on_court,
    possessions_on_court,
    plus_minus_on_court,
    confidence_level
FROM vw_on_off_analysis
WHERE game_id = '0021500001'
  AND confidence_level = 'NONE'  -- No off-court data
ORDER BY minutes_on_court DESC;
*/

-- Example 5: Age vs impact correlation
/*
SELECT
    CAST(age_years_decimal AS INTEGER) as age,
    COUNT(*) as players,
    ROUND(AVG(net_rating_diff), 2) as avg_net_rating_diff,
    ROUND(AVG(replacement_value_48min), 1) as avg_replacement_value
FROM vw_on_off_analysis
WHERE confidence_level IN ('MEDIUM', 'HIGH')
GROUP BY age
ORDER BY age;
*/

-- ============================================================================
-- ML Feature Notes
-- ============================================================================

/*
On/Off Features for ML Models:

**Primary Target Variables:**
1. net_rating_diff - Best measure of player impact
2. replacement_value_48min - Normalized for playing time
3. plus_minus_differential - Raw impact

**Input Features for Prediction:**
1. Player biographical: age, height, position, experience
2. Usage metrics: possessions_on_court, pct_possessions_played
3. Historical averages: Previous games' on/off differentials
4. Team context: Teammate strength, opponent strength
5. Matchup data: Position matchups, size advantages

**Sample Training Examples:**
```python
# Predict player's on/off differential
features = {
    "age_years": 26.6,
    "height_inches": 80,
    "position": "SF",
    "nba_experience_years": 7.0,
    "avg_on_off_last_10_games": +8.3,
    "teammate_avg_rating": 112.5,
    "opponent_def_rating": 108.2,
}
target = net_rating_diff  # What we're predicting

# Model learns:
# - Prime age players (27-31) have higher impact
# - Taller players have better defensive impact
# - Experience correlates with consistent impact
# - Team context matters (good teammates = lower individual impact shown)
```

**Use Cases:**
1. **Trade Analysis:** Compare replacement_value_48min of traded players
2. **Rotation Optimization:** Maximize cumulative on/off differential
3. **Contract Valuation:** Pay based on impact, not box score stats
4. **Lineup Construction:** Pair high-impact with low-impact players efficiently
5. **Injury Impact:** Model team performance without injured player (use off-court rating)

**Handling NONE Confidence:**
- Filter out: WHERE confidence_level != 'NONE' for standard analysis
- Include separately: Study "iron man" games as distinct category
- Aggregate over season: Single-game NONE becomes HIGH over 82 games

**Key Insight:**
On/off differential is more accurate than raw plus/minus because it:
- Controls for teammate quality (off-court shows team baseline)
- Removes garbage time bias (both on and off court affected equally)
- Accounts for opponent quality (same opponent for on/off)
- Reveals true marginal impact of adding/removing one player

**Statistical Notes:**
- Minimum 25 possessions on AND off for reliable estimate
- Larger differentials more significant with more possessions
- Single-game on/off can be noisy; aggregate across games for stability
- Extreme differentials (>±20) usually sample size issues
- confidence_level='NONE' becomes reliable when aggregated over season
*/

-- ============================================================================
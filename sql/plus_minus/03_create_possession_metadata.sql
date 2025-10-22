-- ============================================================================
-- Possession Metadata Table
-- ============================================================================
--
-- Purpose: Define possession boundaries and outcomes for possession-based
--          plus/minus analysis and interval partitioning
--
-- Created: October 19, 2025
-- ML Use Cases: Possession-based intervals (10, 25, 50, 100 possessions),
--               offensive/defensive rating calculations, pace analysis,
--               possession efficiency metrics, momentum detection
--
-- Note: A "possession" is a complete offensive/defensive sequence from
--       gaining control of the ball until losing it (shot, turnover, foul)
--
-- ============================================================================

CREATE TABLE IF NOT EXISTS possession_metadata (
    -- ========================================================================
    -- Primary Key & Identifiers
    -- ========================================================================
    -- PostgreSQL: SERIAL auto-increments (BIGSERIAL for large datasets)
    id BIGSERIAL PRIMARY KEY,
    game_id TEXT NOT NULL,
    possession_number INTEGER NOT NULL,    -- Sequential within game (1-based)
                                           -- Typical game: 200-240 possessions total

    -- ========================================================================
    -- Time Context
    -- ========================================================================
    period INTEGER NOT NULL,

    -- Possession boundaries (in game time)
    start_event_number INTEGER NOT NULL,   -- First event of possession
    end_event_number INTEGER NOT NULL,     -- Last event of possession
    start_seconds INTEGER NOT NULL,        -- Time when possession started
    end_seconds INTEGER NOT NULL,          -- Time when possession ended
    duration_seconds REAL,                 -- end_seconds - start_seconds

    -- Absolute timestamps
    start_timestamp TEXT,                  -- ISO 8601 format
    end_timestamp TEXT,                    -- ISO 8601 format

    -- ========================================================================
    -- Team Context
    -- ========================================================================
    offensive_team_id TEXT NOT NULL,       -- Team with possession
    defensive_team_id TEXT NOT NULL,       -- Team defending

    -- ========================================================================
    -- Lineup Context
    -- ========================================================================
    -- Lineup hashes link to lineup_snapshots table
    lineup_hash_offense TEXT,              -- 5-player offensive lineup
    lineup_hash_defense TEXT,              -- 5-player defensive lineup

    -- ========================================================================
    -- Possession Outcome
    -- ========================================================================
    possession_result TEXT,                -- How possession ended:
                                          -- 'made_shot' - Successful field goal
                                          -- 'missed_shot' - Shot missed, defensive rebound
                                          -- 'turnover' - Lost possession (steal, bad pass, etc.)
                                          -- 'foul_shooting' - Fouled while shooting (FTs awarded)
                                          -- 'foul_nonshoot' - Non-shooting foul
                                          -- 'end_period' - Period ended
                                          -- 'jump_ball' - Jump ball situation
                                          -- 'violation' - Out of bounds, 24-sec, etc.

    points_scored INTEGER DEFAULT 0,       -- Points scored this possession (0, 1, 2, or 3)

    shot_type TEXT,                        -- '2pt', '3pt', 'ft', 'none' (if no shot)

    -- ========================================================================
    -- Offensive Metrics
    -- ========================================================================
    offensive_rebound BOOLEAN DEFAULT FALSE,   -- Did offense get own rebound?
    second_chance BOOLEAN DEFAULT FALSE,       -- Is this a second-chance possession?
    fast_break BOOLEAN DEFAULT FALSE,          -- Fast break possession?
    in_the_paint BOOLEAN DEFAULT FALSE,        -- Shot attempted in paint?

    -- ========================================================================
    -- Defensive Metrics
    -- ========================================================================
    defensive_rebound BOOLEAN DEFAULT FALSE,   -- Did defense get rebound?
    forced_turnover BOOLEAN DEFAULT FALSE,     -- Defense forced turnover (steal, block)?
    contested_shot BOOLEAN DEFAULT FALSE,      -- Was shot contested?

    -- ========================================================================
    -- Efficiency Metrics (calculated)
    -- ========================================================================
    points_per_possession REAL,            -- points_scored / 1 (this possession)
    expected_points REAL,                  -- Based on shot location/type

    -- ========================================================================
    -- Score Context at Start
    -- ========================================================================
    score_differential_start INTEGER,      -- offensive_team - defensive_team score
                                          -- At possession start

    -- ========================================================================
    -- Constraints
    -- ========================================================================
    UNIQUE(game_id, possession_number),

    -- Ensure valid time boundaries
    CHECK(end_event_number >= start_event_number),
    CHECK(end_seconds >= start_seconds),
    CHECK(duration_seconds >= 0),
    CHECK(points_scored IN (0, 1, 2, 3, 4))  -- Max 4 (and-1 + tech FT)
);

-- ============================================================================
-- Indexes (for performance)
-- ============================================================================

-- Primary lookup: Possessions in a game
CREATE INDEX IF NOT EXISTS idx_possession_metadata_game
    ON possession_metadata(game_id, possession_number);

-- Team-specific queries
CREATE INDEX IF NOT EXISTS idx_possession_metadata_offense
    ON possession_metadata(game_id, offensive_team_id, possession_number);

CREATE INDEX IF NOT EXISTS idx_possession_metadata_defense
    ON possession_metadata(game_id, defensive_team_id, possession_number);

-- Lineup-specific queries
CREATE INDEX IF NOT EXISTS idx_possession_metadata_lineup_off
    ON possession_metadata(lineup_hash_offense, game_id);

CREATE INDEX IF NOT EXISTS idx_possession_metadata_lineup_def
    ON possession_metadata(lineup_hash_defense, game_id);

-- Outcome-based queries
CREATE INDEX IF NOT EXISTS idx_possession_metadata_result
    ON possession_metadata(possession_result, game_id);

-- Time-based queries
CREATE INDEX IF NOT EXISTS idx_possession_metadata_period
    ON possession_metadata(game_id, period, possession_number);

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Example 1: Calculate offensive rating for a team (points per 100 possessions)
/*
SELECT
    offensive_team_id,
    COUNT(*) as total_possessions,
    SUM(points_scored) as total_points,
    (SUM(points_scored) * 100.0 / COUNT(*)) as offensive_rating
FROM possession_metadata
WHERE game_id = '0021500001'
GROUP BY offensive_team_id;
*/

-- Example 2: Get possession intervals (25-possession blocks)
/*
WITH possession_intervals AS (
    SELECT
        possession_number,
        ((possession_number - 1) / 25) + 1 as interval_number,
        offensive_team_id,
        points_scored
    FROM possession_metadata
    WHERE game_id = '0021500001'
)
SELECT
    interval_number,
    offensive_team_id,
    COUNT(*) as possessions,
    SUM(points_scored) as points,
    SUM(points_scored) * 100.0 / COUNT(*) as offensive_rating
FROM possession_intervals
GROUP BY interval_number, offensive_team_id
ORDER BY interval_number, offensive_team_id;
*/

-- Example 3: Lineup offensive efficiency
/*
SELECT
    lineup_hash_offense,
    COUNT(*) as possessions,
    SUM(points_scored) as points,
    AVG(points_scored) as points_per_possession,
    SUM(CASE WHEN points_scored > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as scoring_pct
FROM possession_metadata
WHERE game_id = '0021500001'
  AND offensive_team_id = 'BOS'
GROUP BY lineup_hash_offense
HAVING possessions >= 5  -- Minimum sample size
ORDER BY points_per_possession DESC;
*/

-- Example 4: Defensive rating (points allowed per 100 possessions)
/*
SELECT
    defensive_team_id,
    COUNT(*) as possessions_defended,
    SUM(points_scored) as points_allowed,
    (SUM(points_scored) * 100.0 / COUNT(*)) as defensive_rating
FROM possession_metadata
WHERE game_id = '0021500001'
GROUP BY defensive_team_id;
*/

-- Example 5: Turnover rate
/*
SELECT
    offensive_team_id,
    COUNT(*) as total_possessions,
    SUM(CASE WHEN possession_result = 'turnover' THEN 1 ELSE 0 END) as turnovers,
    SUM(CASE WHEN possession_result = 'turnover' THEN 1 ELSE 0 END) * 100.0 /
        COUNT(*) as turnover_rate
FROM possession_metadata
WHERE game_id = '0021500001'
GROUP BY offensive_team_id;
*/

-- Example 6: Fast break effectiveness
/*
SELECT
    offensive_team_id,
    COUNT(*) as fast_break_possessions,
    SUM(points_scored) as fast_break_points,
    AVG(points_scored) as points_per_fastbreak
FROM possession_metadata
WHERE game_id = '0021500001'
  AND fast_break = 1
GROUP BY offensive_team_id;
*/

-- Example 7: Second-chance points
/*
SELECT
    offensive_team_id,
    COUNT(*) as second_chance_possessions,
    SUM(points_scored) as second_chance_points,
    AVG(points_scored) as points_per_second_chance
FROM possession_metadata
WHERE game_id = '0021500001'
  AND second_chance = 1
GROUP BY offensive_team_id;
*/

-- Example 8: Possession duration analysis
/*
SELECT
    offensive_team_id,
    AVG(duration_seconds) as avg_possession_duration,
    MIN(duration_seconds) as fastest_possession,
    MAX(duration_seconds) as longest_possession,
    COUNT(*) as total_possessions
FROM possession_metadata
WHERE game_id = '0021500001'
GROUP BY offensive_team_id;
*/

-- ============================================================================
-- ML Feature Engineering Notes
-- ============================================================================

/*
Possession-Based Features for ML:

1. **Possession Efficiency Metrics:**
   - points_per_possession: Most accurate efficiency measure
   - offensive_rating: Points per 100 possessions
   - scoring_rate: % of possessions that score
   - expected_points_delta: Actual - expected points

2. **Possession Outcome Features:**
   - made_shot_rate: % ending in made FG
   - missed_shot_rate: % ending in miss
   - turnover_rate: % ending in turnover
   - foul_rate: % ending in foul

3. **Possession Type Features:**
   - fast_break_rate: % fast break possessions
   - second_chance_rate: % second-chance possessions
   - paint_rate: % possessions with paint shot
   - three_point_rate: % possessions with 3PT attempt

4. **Temporal Features:**
   - avg_possession_duration: Pace indicator
   - possession_duration_std: Variability
   - possessions_per_minute: Game pace
   - possession_number: Early vs late game

5. **Lineup Features:**
   - lineup_offensive_rating: Per lineup efficiency
   - lineup_pace: Possessions per minute by lineup
   - lineup_turnover_rate: TO% by lineup

6. **Momentum Features:**
   - rolling_points_per_poss_5: Moving average (5 poss)
   - rolling_points_per_poss_10: Moving average (10 poss)
   - scoring_run_length: Consecutive scoring possessions
   - drought_length: Consecutive non-scoring possessions

7. **Context Features:**
   - score_differential_start: Close vs blowout
   - period: Quarter effects
   - time_remaining: Clutch vs regular time

8. **Defensive Features:**
   - defensive_rating: Points allowed per 100 poss
   - forced_turnover_rate: % possessions with forced TO
   - defensive_rebound_rate: % possessions with defensive board
   - contested_shot_rate: % shots contested

9. **Interval Aggregations (Possession-based partitions):**
   - 10_poss_offensive_rating: Recent efficiency
   - 25_poss_offensive_rating: Quarter-level efficiency
   - 50_poss_offensive_rating: Half-game efficiency
   - 100_poss_offensive_rating: Full-game comparison

10. **Interaction Features:**
    - lineup_hash × opponent_lineup_hash: Matchup effects
    - possession_duration × score_differential: Tempo strategy
    - fast_break_rate × defensive_rating: Transition defense
    - turnover_rate × opponent_forced_turnover_rate: Pressure effects

Example Feature Vector for ML:
{
    "game_id": "0021500001",
    "possession_number": 47,
    "offensive_team_id": "BOS",

    # Possession details
    "duration_seconds": 14.2,
    "points_scored": 2,
    "possession_result": "made_shot",
    "shot_type": "2pt",

    # Context
    "score_differential_start": +3,
    "period": 2,
    "fast_break": false,
    "second_chance": false,

    # Lineup
    "lineup_hash_offense": "abc123...",
    "lineup_hash_defense": "def456...",

    # Aggregated metrics (rolling)
    "points_per_poss_last_10": 1.12,
    "points_per_poss_last_25": 1.08,
    "offensive_rating_game": 108.5,

    # Momentum
    "scoring_run_length": 3,  // 3 consecutive scoring possessions
    "points_last_5_poss": 7,

    # Team efficiency
    "team_offensive_rating": 112.3,
    "team_defensive_rating": 105.7,
    "team_pace": 98.4,
}
*/

-- ============================================================================
-- Data Quality Checks
-- ============================================================================

-- Check 1: Verify sequential possession numbers
/*
WITH possession_gaps AS (
    SELECT
        game_id,
        possession_number,
        LAG(possession_number) OVER (PARTITION BY game_id ORDER BY possession_number) as prev_poss
    FROM possession_metadata
)
SELECT *
FROM possession_gaps
WHERE prev_poss IS NOT NULL
  AND possession_number != prev_poss + 1;  -- Should increment by 1
-- Expected: 0 rows
*/

-- Check 2: Verify typical possession count per game
/*
SELECT
    game_id,
    COUNT(*) as total_possessions,
    COUNT(DISTINCT period) as periods_played
FROM possession_metadata
GROUP BY game_id
HAVING total_possessions < 180 OR total_possessions > 280;
-- Expected: Few rows (typical: 200-240 possessions per game)
-- Games with OT may have more
*/

-- Check 3: Verify points scored match possession result
/*
SELECT *
FROM possession_metadata
WHERE (possession_result = 'made_shot' AND points_scored = 0)
   OR (possession_result IN ('missed_shot', 'turnover') AND points_scored > 0)
LIMIT 10;
-- Expected: 0 rows (made shots should score, misses/TOs should not)
*/

-- Check 4: Verify time boundaries
/*
SELECT *
FROM possession_metadata
WHERE duration_seconds < 0
   OR duration_seconds > 30  -- Longer than shot clock (rare but possible)
   OR start_seconds > end_seconds
LIMIT 10;
-- Expected: 0 rows for negative duration, few for > 30 seconds
*/

-- Check 5: Verify lineup hash consistency
/*
SELECT DISTINCT
    p.lineup_hash_offense,
    COUNT(DISTINCT l.lineup_hash) as matching_lineups
FROM possession_metadata p
LEFT JOIN lineup_snapshots l
    ON p.game_id = l.game_id
   AND p.lineup_hash_offense = l.lineup_hash
   AND p.start_event_number <= l.event_number
   AND p.end_event_number >= l.event_number
GROUP BY p.lineup_hash_offense
HAVING matching_lineups = 0;
-- Expected: 0 (all lineup_hashes should exist in lineup_snapshots)
*/

-- ============================================================================
-- Performance Notes
-- ============================================================================

/*
Insert Performance:
- Bulk inserts recommended (500+ rows per batch)
- Pre-calculate duration_seconds, points_per_possession
- Insert after processing full game to ensure sequential possession_numbers

Query Performance:
- Possession range queries: O(log n) with idx_possession_metadata_game
- Lineup queries: Fast with lineup hash indexes
- Team queries: Fast with team indexes
- Interval calculations: Very fast (simple range queries)

Storage Estimates:
- ~200 bytes per row
- ~220 possessions per game average
- 1000 games = 220,000 rows × 200 bytes = ~44 MB
- With indexes: ~80 MB for 1000 games
- Much smaller than snapshot tables!

Optimization Tips:
- Always use possession_number for range queries (indexed)
- Aggregate at insert time for frequently-used metrics
- Materialize interval aggregations (10, 25, 50, 100 poss) for ML pipelines
- Use lineup_hash for all lineup queries (not individual player IDs)
- Consider partitioning by season for historical analyses

Possession-Based Intervals vs Time-Based:
- More accurate: Accounts for pace variations
- More meaningful: Natural basketball boundaries
- Smaller data: 220 possessions vs 2,880 seconds
- Faster queries: Less data to scan
- Better for ML: More predictable feature distributions
*/

-- ============================================================================

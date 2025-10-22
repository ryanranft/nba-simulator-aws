-- ============================================================================
-- Lineup Snapshots Table
-- ============================================================================
--
-- Purpose: Track every unique 5-player lineup combination at each event
--          for lineup-based plus/minus analysis and chemistry detection
--
-- Created: October 19, 2025
-- ML Use Cases: Lineup optimization, chemistry scoring, matchup analysis,
--               rotation planning, best 5-player combinations
--
-- ============================================================================

CREATE TABLE IF NOT EXISTS lineup_snapshots (
    -- ========================================================================
    -- Primary Key & Identifiers
    -- ========================================================================
    -- PostgreSQL: SERIAL auto-increments (BIGSERIAL for large datasets)
    id BIGSERIAL PRIMARY KEY,
    game_id TEXT NOT NULL,
    event_number INTEGER NOT NULL,

    -- ========================================================================
    -- Time & Possession Context
    -- ========================================================================
    period INTEGER NOT NULL,
    time_elapsed_seconds INTEGER NOT NULL,
    possession_number INTEGER,          -- NULL if possession tracking not available
    timestamp TEXT,                     -- ISO 8601 format

    -- ========================================================================
    -- Team Context
    -- ========================================================================
    team_id TEXT NOT NULL,              -- Team with this lineup
    opponent_team_id TEXT NOT NULL,     -- Opponent team
    home_team BOOLEAN DEFAULT FALSE,    -- TRUE if this is home team

    -- ========================================================================
    -- Lineup Players (ALWAYS alphabetically sorted by player_id)
    -- ========================================================================
    -- CRITICAL: Players MUST be stored in alphabetical order to ensure
    -- consistent lineup_hash generation and prevent duplicate lineups
    -- ========================================================================
    player1_id TEXT NOT NULL,           -- 1st alphabetically
    player2_id TEXT NOT NULL,           -- 2nd alphabetically
    player3_id TEXT NOT NULL,           -- 3rd alphabetically
    player4_id TEXT NOT NULL,           -- 4th alphabetically
    player5_id TEXT NOT NULL,           -- 5th alphabetically

    -- ========================================================================
    -- Lineup Identifier
    -- ========================================================================
    lineup_hash TEXT NOT NULL,          -- MD5(player1|player2|player3|player4|player5)
                                        -- Enables fast lookup of lineup stats

    -- ========================================================================
    -- Score Context (Cumulative)
    -- ========================================================================
    team_score INTEGER DEFAULT 0,       -- This team's cumulative score
    opponent_score INTEGER DEFAULT 0,   -- Opponent's cumulative score
    plus_minus INTEGER DEFAULT 0,       -- team_score - opponent_score

    -- ========================================================================
    -- Possession Context
    -- ========================================================================
    offensive_possession BOOLEAN,       -- 1 if this team has ball, 0 if defending

    -- ========================================================================
    -- Constraints
    -- ========================================================================
    UNIQUE(game_id, event_number, team_id),

    -- Ensure players are distinct (no duplicates)
    CHECK(player1_id != player2_id),
    CHECK(player1_id != player3_id),
    CHECK(player1_id != player4_id),
    CHECK(player1_id != player5_id),
    CHECK(player2_id != player3_id),
    CHECK(player2_id != player4_id),
    CHECK(player2_id != player5_id),
    CHECK(player3_id != player4_id),
    CHECK(player3_id != player5_id),
    CHECK(player4_id != player5_id),

    -- Ensure alphabetical ordering
    CHECK(player1_id < player2_id),
    CHECK(player2_id < player3_id),
    CHECK(player3_id < player4_id),
    CHECK(player4_id < player5_id)
);

-- ============================================================================
-- Indexes (for performance)
-- ============================================================================

-- Primary lookup: Find all snapshots for a specific lineup
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_hash
    ON lineup_snapshots(lineup_hash, game_id);

-- Game-level queries
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_game
    ON lineup_snapshots(game_id, team_id, time_elapsed_seconds);

-- Player-specific queries (find all lineups containing a player)
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_player1
    ON lineup_snapshots(player1_id, game_id);
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_player2
    ON lineup_snapshots(player2_id, game_id);
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_player3
    ON lineup_snapshots(player3_id, game_id);
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_player4
    ON lineup_snapshots(player4_id, game_id);
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_player5
    ON lineup_snapshots(player5_id, game_id);

-- Possession-based queries
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_possession
    ON lineup_snapshots(game_id, possession_number, team_id);

-- Time-based queries
CREATE INDEX IF NOT EXISTS idx_lineup_snapshots_period
    ON lineup_snapshots(game_id, period, time_elapsed_seconds);

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Example 1: Get all snapshots for a specific lineup
/*
SELECT
    game_id,
    time_elapsed_seconds,
    team_score,
    opponent_score,
    plus_minus
FROM lineup_snapshots
WHERE lineup_hash = 'abc123def456...'  -- MD5 hash
ORDER BY game_id, time_elapsed_seconds;
*/

-- Example 2: Find all unique lineups for a team in a game
/*
SELECT DISTINCT
    lineup_hash,
    player1_id,
    player2_id,
    player3_id,
    player4_id,
    player5_id,
    COUNT(*) as appearances,
    AVG(plus_minus) as avg_plus_minus
FROM lineup_snapshots
WHERE game_id = '0021500001' AND team_id = 'BOS'
GROUP BY lineup_hash
ORDER BY avg_plus_minus DESC;
*/

-- Example 3: Find all lineups containing a specific player
/*
SELECT DISTINCT lineup_hash
FROM lineup_snapshots
WHERE game_id = '0021500001'
  AND (player1_id = 'tatumja01'
       OR player2_id = 'tatumja01'
       OR player3_id = 'tatumja01'
       OR player4_id = 'tatumja01'
       OR player5_id = 'tatumja01')
ORDER BY lineup_hash;
*/

-- Example 4: Calculate lineup performance for possession range
/*
SELECT
    lineup_hash,
    player1_id || ', ' || player2_id || ', ' || player3_id || ', ' ||
    player4_id || ', ' || player5_id as lineup,
    COUNT(*) as possessions,
    MAX(plus_minus) - MIN(plus_minus) as plus_minus_change,
    (MAX(plus_minus) - MIN(plus_minus)) * 1.0 / COUNT(*) as plus_minus_per_poss
FROM lineup_snapshots
WHERE game_id = '0021500001'
  AND team_id = 'BOS'
  AND possession_number BETWEEN 1 AND 25  -- First 25 possessions
GROUP BY lineup_hash
ORDER BY plus_minus_per_poss DESC;
*/

-- Example 5: Lineup transitions (when lineup changes)
/*
WITH lineup_changes AS (
    SELECT
        game_id,
        event_number,
        time_elapsed_seconds,
        lineup_hash,
        LAG(lineup_hash) OVER (PARTITION BY game_id, team_id
                              ORDER BY event_number) as prev_lineup_hash
    FROM lineup_snapshots
    WHERE game_id = '0021500001' AND team_id = 'BOS'
)
SELECT
    event_number,
    time_elapsed_seconds,
    prev_lineup_hash as lineup_out,
    lineup_hash as lineup_in
FROM lineup_changes
WHERE prev_lineup_hash IS NOT NULL
  AND prev_lineup_hash != lineup_hash  -- Lineup actually changed
ORDER BY event_number;
*/

-- ============================================================================
-- ML Feature Engineering Notes
-- ============================================================================

/*
Lineup-Based Features for ML:

1. **Lineup Identification:**
   - lineup_hash: Unique identifier for exact 5-player combination
   - Individual player IDs: For player-specific features

2. **Performance Metrics:**
   - plus_minus: Raw +/- for this lineup
   - plus_minus_per_possession: Efficiency metric
   - plus_minus_change: Delta from start to end of stint

3. **Context Features:**
   - offensive_possession: Binary (offense vs defense)
   - home_team: Home court advantage indicator
   - time_elapsed_seconds: Fatigue, clutch situations

4. **Aggregation Opportunities:**
   - Total possessions together
   - Minutes played together
   - Offensive/defensive splits
   - Performance vs different opponent lineups

5. **Chemistry Features (derived):**
   - Lineup continuity: How often this exact 5 plays together
   - Pairwise chemistry: Performance of all 2-player combos within lineup
   - Position balance: Height distribution, position mix
   - Age/experience distribution: Veteran vs rookie mix

6. **Interaction Features:**
   - lineup_plus_minus × opponent_lineup_hash: Matchup effects
   - lineup_plus_minus × time_remaining: Clutch performance
   - lineup_hash × possession_number: Early vs late game performance

Example Feature Vector for ML:
{
    "lineup_hash": "abc123...",
    "player_ids": ["tatumja01", "brownja02", ...],
    "avg_age": 26.4,
    "avg_height": 78.2,
    "avg_experience": 5.6,
    "possessions_together": 45,
    "plus_minus": +12,
    "plus_minus_per_poss": +0.267,
    "offensive_poss": 23,
    "defensive_poss": 22,
    "home_team": true,
    "chemistry_score": 87.3,  // Derived from historical performance
}
*/

-- ============================================================================
-- Data Quality Checks
-- ============================================================================

-- Check 1: Verify no duplicate players in any lineup
/*
SELECT COUNT(*) as violations
FROM lineup_snapshots
WHERE player1_id IN (player2_id, player3_id, player4_id, player5_id)
   OR player2_id IN (player3_id, player4_id, player5_id)
   OR player3_id IN (player4_id, player5_id)
   OR player4_id = player5_id;
-- Expected: 0 (constraints should prevent this)
*/

-- Check 2: Verify alphabetical ordering
/*
SELECT COUNT(*) as violations
FROM lineup_snapshots
WHERE player1_id >= player2_id
   OR player2_id >= player3_id
   OR player3_id >= player4_id
   OR player4_id >= player5_id;
-- Expected: 0 (constraints should prevent this)
*/

-- Check 3: Count unique lineups per game
/*
SELECT
    game_id,
    team_id,
    COUNT(DISTINCT lineup_hash) as unique_lineups,
    COUNT(*) as total_snapshots
FROM lineup_snapshots
GROUP BY game_id, team_id
ORDER BY unique_lineups DESC;
-- Expected: 5-15 unique lineups per team per game (typical NBA game)
*/

-- Check 4: Verify plus_minus calculation
/*
SELECT
    game_id,
    event_number,
    team_score,
    opponent_score,
    plus_minus,
    (team_score - opponent_score) as calculated_plus_minus
FROM lineup_snapshots
WHERE plus_minus != (team_score - opponent_score)
LIMIT 10;
-- Expected: 0 rows (plus_minus should always equal team_score - opponent_score)
*/

-- ============================================================================
-- Performance Notes
-- ============================================================================

/*
Insert Performance:
- Bulk inserts recommended (batch of 1000+)
- Pre-sort players alphabetically before insert to avoid constraint violations
- Pre-calculate lineup_hash (MD5) to avoid repeated calculations

Query Performance:
- lineup_hash lookups: O(log n) with index
- Player-specific queries: Use appropriate player index (idx_lineup_snapshots_playerN)
- Full game scans: < 1 second for typical game (3000-4000 events)
- Possession-based aggregations: Fast with idx_lineup_snapshots_possession

Storage Estimates:
- ~200 bytes per row
- ~3500 events per game × 2 teams = 7000 rows per game
- 1000 games = 7M rows × 200 bytes = ~1.4 GB
- With indexes: ~2.5 GB for 1000 games

Optimization Tips:
- Use lineup_hash for all lineup-based queries (not player ID combinations)
- Materialize frequently-used aggregations (top lineups, lineup stats)
- Consider partitioning by season for historical data
- Use possession-based queries when possible (more basketball-meaningful)
*/

-- ============================================================================

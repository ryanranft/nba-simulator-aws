-- ============================================================================
-- Player Plus/Minus Snapshots Table
-- ============================================================================
--
-- Purpose: Track each player's on/off court status and plus/minus at every event
--          for individual impact analysis and stint tracking
--
-- Created: October 19, 2025
-- ML Use Cases: Player impact prediction, on/off differential analysis,
--               stint fatigue modeling, substitution optimization,
--               replacement value calculation
--
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_plus_minus_snapshots (
    -- ========================================================================
    -- Primary Key & Identifiers
    -- ========================================================================
    -- PostgreSQL: SERIAL auto-increments (BIGSERIAL for large datasets)
    id BIGSERIAL PRIMARY KEY,
    game_id TEXT NOT NULL,
    event_number INTEGER NOT NULL,
    player_id TEXT NOT NULL,

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
    team_id TEXT NOT NULL,              -- Player's team
    opponent_team_id TEXT NOT NULL,     -- Opponent team
    home_team BOOLEAN DEFAULT FALSE,    -- TRUE if player's team is home team

    -- ========================================================================
    -- On Court Status
    -- ========================================================================
    on_court BOOLEAN NOT NULL,          -- 1 if player is on court, 0 if on bench
                                        -- CRITICAL for on/off analysis

    -- ========================================================================
    -- Score Context (Cumulative)
    -- ========================================================================
    team_score INTEGER DEFAULT 0,       -- Player's team cumulative score
    opponent_score INTEGER DEFAULT 0,   -- Opponent cumulative score
    plus_minus INTEGER DEFAULT 0,       -- team_score - opponent_score
                                        -- Updated even when player is on bench
                                        -- (enables on/off comparison)

    -- ========================================================================
    -- Stint Tracking
    -- ========================================================================
    -- A "stint" is a continuous period where player is on court
    -- Starts at check-in event, ends at check-out event
    -- ========================================================================
    stint_id TEXT,                      -- Format: "game_id:player_id:stint_num"
                                        -- Example: "0021500001:tatumja01:3"
                                        -- NULL if player is on bench

    stint_number INTEGER,               -- 1st, 2nd, 3rd stint in game (1-based)
                                        -- NULL if player is on bench

    stint_start_event INTEGER,          -- Event number where stint started
                                        -- NULL if player is on bench

    stint_end_event INTEGER,            -- Event number where stint will end
                                        -- NULL while stint ongoing or on bench
                                        -- Updated retroactively when player exits

    -- ========================================================================
    -- Rest Tracking
    -- ========================================================================
    minutes_played_cumulative REAL DEFAULT 0.0,     -- Total minutes played so far
    seconds_since_last_stint INTEGER,               -- Rest duration since last stint
                                                    -- NULL for first stint or while playing

    -- ========================================================================
    -- Constraints
    -- ========================================================================
    UNIQUE(game_id, event_number, player_id)
);

-- ============================================================================
-- Indexes (for performance)
-- ============================================================================

-- Primary lookup: Player's snapshots in a game
CREATE INDEX IF NOT EXISTS idx_player_pm_snapshots_player_game
    ON player_plus_minus_snapshots(player_id, game_id, event_number);

-- On/off court queries
CREATE INDEX IF NOT EXISTS idx_player_pm_snapshots_on_court
    ON player_plus_minus_snapshots(game_id, player_id, on_court);

-- Stint-based queries
CREATE INDEX IF NOT EXISTS idx_player_pm_snapshots_stint
    ON player_plus_minus_snapshots(stint_id);

CREATE INDEX IF NOT EXISTS idx_player_pm_snapshots_stint_number
    ON player_plus_minus_snapshots(game_id, player_id, stint_number);

-- Time-based queries
CREATE INDEX IF NOT EXISTS idx_player_pm_snapshots_time
    ON player_plus_minus_snapshots(game_id, time_elapsed_seconds);

-- Possession-based queries
CREATE INDEX IF NOT EXISTS idx_player_pm_snapshots_possession
    ON player_plus_minus_snapshots(game_id, possession_number, player_id);

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Example 1: Get player's on-court plus/minus for entire game
/*
SELECT
    player_id,
    MAX(plus_minus) FILTER (WHERE on_court = 1) -
    MIN(plus_minus) FILTER (WHERE on_court = 1) as on_court_plus_minus,
    SUM(CASE WHEN on_court = 1 THEN 1 ELSE 0 END) as events_on_court
FROM player_plus_minus_snapshots
WHERE game_id = '0021500001' AND player_id = 'tatumja01'
GROUP BY player_id;
*/

-- Example 2: Calculate on/off differential
/*
WITH on_court AS (
    SELECT
        MIN(plus_minus) as start_pm,
        MAX(plus_minus) as end_pm
    FROM player_plus_minus_snapshots
    WHERE game_id = '0021500001'
      AND player_id = 'tatumja01'
      AND on_court = 1
),
off_court AS (
    SELECT
        MIN(plus_minus) as start_pm,
        MAX(plus_minus) as end_pm
    FROM player_plus_minus_snapshots
    WHERE game_id = '0021500001'
      AND player_id = 'tatumja01'
      AND on_court = 0
)
SELECT
    (on_court.end_pm - on_court.start_pm) as on_court_plus_minus,
    (off_court.end_pm - off_court.start_pm) as off_court_plus_minus,
    (on_court.end_pm - on_court.start_pm) -
    (off_court.end_pm - off_court.start_pm) as differential
FROM on_court, off_court;
*/

-- Example 3: Get all stints for a player
/*
SELECT
    stint_id,
    stint_number,
    stint_start_event,
    stint_end_event,
    COUNT(*) as events_in_stint,
    MAX(time_elapsed_seconds) - MIN(time_elapsed_seconds) as duration_seconds,
    MAX(plus_minus) - MIN(plus_minus) as stint_plus_minus
FROM player_plus_minus_snapshots
WHERE game_id = '0021500001'
  AND player_id = 'tatumja01'
  AND stint_id IS NOT NULL
GROUP BY stint_id
ORDER BY stint_number;
*/

-- Example 4: Calculate plus/minus per possession (on court only)
/*
SELECT
    player_id,
    COUNT(DISTINCT possession_number) as possessions_played,
    MAX(plus_minus) - MIN(plus_minus) as total_plus_minus,
    (MAX(plus_minus) - MIN(plus_minus)) * 1.0 /
        COUNT(DISTINCT possession_number) as plus_minus_per_possession
FROM player_plus_minus_snapshots
WHERE game_id = '0021500001'
  AND player_id = 'tatumja01'
  AND on_court = 1
  AND possession_number IS NOT NULL
GROUP BY player_id;
*/

-- Example 5: Track plus/minus evolution over time (on court)
/*
SELECT
    time_elapsed_seconds,
    period,
    plus_minus,
    on_court,
    stint_number,
    plus_minus - LAG(plus_minus) OVER (
        PARTITION BY player_id, stint_id
        ORDER BY event_number
    ) as plus_minus_delta
FROM player_plus_minus_snapshots
WHERE game_id = '0021500001'
  AND player_id = 'tatumja01'
  AND on_court = 1
ORDER BY event_number;
*/

-- Example 6: Find substitution points (on → off or off → on transitions)
/*
WITH transitions AS (
    SELECT
        event_number,
        time_elapsed_seconds,
        period,
        on_court,
        LAG(on_court) OVER (PARTITION BY player_id ORDER BY event_number) as prev_on_court,
        plus_minus
    FROM player_plus_minus_snapshots
    WHERE game_id = '0021500001' AND player_id = 'tatumja01'
)
SELECT
    event_number,
    time_elapsed_seconds,
    period,
    CASE
        WHEN on_court = 1 AND prev_on_court = 0 THEN 'CHECK-IN'
        WHEN on_court = 0 AND prev_on_court = 1 THEN 'CHECK-OUT'
    END as event_type,
    plus_minus
FROM transitions
WHERE prev_on_court IS NOT NULL
  AND on_court != prev_on_court
ORDER BY event_number;
*/

-- ============================================================================
-- ML Feature Engineering Notes
-- ============================================================================

/*
Individual Plus/Minus Features for ML:

1. **On-Court Metrics:**
   - on_court_plus_minus: Player's +/- while on court
   - on_court_minutes: Total playing time
   - on_court_possessions: Possessions played
   - plus_minus_per_minute: Efficiency metric
   - plus_minus_per_possession: Basketball-accurate efficiency

2. **On/Off Differential:**
   - off_court_plus_minus: Team's +/- while player on bench
   - on_off_differential: Impact of player's presence
   - replacement_value: Differential normalized by minutes

3. **Stint Features:**
   - stint_number: 1st, 2nd, 3rd stint (fatigue proxy)
   - stint_duration: Length of current stint
   - stint_plus_minus: Performance during this stint
   - stints_per_game: Rotation pattern
   - avg_stint_length: Coach's usage pattern

4. **Rest & Fatigue:**
   - minutes_played_cumulative: Cumulative fatigue
   - seconds_since_last_stint: Rest recovered
   - rest_to_stint_ratio: Rest vs play balance
   - fatigue_index: stint_num × minutes × age

5. **Time-Varying Features (LSTM/RNN):**
   - plus_minus[t]: Sequential +/- at each timestep
   - on_court[t]: Binary on/off sequence
   - momentum[t]: Δplus_minus between timesteps
   - stint_fatigue[t]: Increasing within stint, resets after rest

6. **Context Features:**
   - period: Quarter (fatigue increases)
   - home_team: Home court advantage
   - score_differential: Performance in close vs blowout games
   - possession_number: Early vs late game

7. **Interaction Features:**
   - plus_minus × age: Aging effects
   - plus_minus × experience: Veteran vs rookie impact
   - stint_duration × age: Age-fatigue interaction
   - on_off_diff × opponent_strength: Matchup-dependent impact

Example Feature Vector for ML:
{
    "player_id": "tatumja01",
    "game_id": "0021500001",

    # On-court performance
    "on_court_plus_minus": +12,
    "on_court_minutes": 32.5,
    "on_court_possessions": 78,
    "plus_minus_per_poss": +0.154,

    # On/off differential
    "off_court_plus_minus": -3,
    "on_off_differential": +15,  // Team is +15 better with player on court
    "replacement_value": 0.462,  // +15 / 32.5 minutes

    # Stint analysis
    "stint_number": 3,
    "stint_duration_seconds": 420,  // 7 minutes current stint
    "stint_plus_minus": +5,
    "avg_stint_duration": 6.8,
    "stints_per_game": 4.2,

    # Fatigue
    "minutes_played_cumulative": 24.3,
    "seconds_since_last_stint": 180,  // 3 minutes rest
    "fatigue_index": 648.0,  // 3 × 24.3 × 8.9 (stint × mins × experience years)

    # Context
    "period": 3,
    "home_team": true,
    "possession_number": 72,

    # Time-varying
    "plus_minus_sequence": [0, 0, +2, +2, +5, +5, +7, ...],  // LSTM input
    "on_court_sequence": [1, 1, 1, 0, 0, 1, 1, ...],  // Binary sequence
}
*/

-- ============================================================================
-- Data Quality Checks
-- ============================================================================

-- Check 1: Verify every player has at least one snapshot per game
/*
SELECT
    g.game_id,
    COUNT(DISTINCT p.player_id) as players_in_game
FROM games g
LEFT JOIN player_plus_minus_snapshots p ON g.game_id = p.game_id
GROUP BY g.game_id
HAVING players_in_game < 10  -- Expect at least 10 players (5 per team minimum)
ORDER BY players_in_game;
-- Expected: 0 rows (all games should have ≥10 players)
*/

-- Check 2: Verify on_court=1 players match lineup_snapshots
/*
WITH on_court_players AS (
    SELECT DISTINCT
        game_id,
        event_number,
        team_id,
        player_id
    FROM player_plus_minus_snapshots
    WHERE on_court = 1
),
lineup_players AS (
    SELECT DISTINCT
        game_id,
        event_number,
        team_id,
        player1_id as player_id
    FROM lineup_snapshots
    UNION
    SELECT game_id, event_number, team_id, player2_id FROM lineup_snapshots
    UNION
    SELECT game_id, event_number, team_id, player3_id FROM lineup_snapshots
    UNION
    SELECT game_id, event_number, team_id, player4_id FROM lineup_snapshots
    UNION
    SELECT game_id, event_number, team_id, player5_id FROM lineup_snapshots
)
SELECT COUNT(*) as mismatches
FROM on_court_players o
FULL OUTER JOIN lineup_players l
    ON o.game_id = l.game_id
   AND o.event_number = l.event_number
   AND o.team_id = l.team_id
   AND o.player_id = l.player_id
WHERE o.player_id IS NULL OR l.player_id IS NULL;
-- Expected: 0 (perfect match between tables)
*/

-- Check 3: Verify stint continuity (no gaps in stint_id)
/*
SELECT
    stint_id,
    COUNT(DISTINCT event_number) as event_count,
    MAX(event_number) - MIN(event_number) + 1 as expected_events,
    CASE
        WHEN COUNT(DISTINCT event_number) < (MAX(event_number) - MIN(event_number) + 1)
        THEN 'GAP_DETECTED'
        ELSE 'CONTINUOUS'
    END as continuity_status
FROM player_plus_minus_snapshots
WHERE stint_id IS NOT NULL
GROUP BY stint_id
HAVING continuity_status = 'GAP_DETECTED';
-- Expected: 0 rows (all stints should be continuous)
*/

-- Check 4: Verify plus_minus consistency
/*
SELECT
    game_id,
    event_number,
    player_id,
    team_score,
    opponent_score,
    plus_minus,
    (team_score - opponent_score) as calculated_plus_minus
FROM player_plus_minus_snapshots
WHERE plus_minus != (team_score - opponent_score)
LIMIT 10;
-- Expected: 0 rows
*/

-- Check 5: Check for impossible stint numbers (should be sequential)
/*
WITH stint_gaps AS (
    SELECT
        game_id,
        player_id,
        stint_number,
        LAG(stint_number) OVER (PARTITION BY game_id, player_id
                               ORDER BY stint_number) as prev_stint
    FROM (SELECT DISTINCT game_id, player_id, stint_number
          FROM player_plus_minus_snapshots
          WHERE stint_number IS NOT NULL)
)
SELECT *
FROM stint_gaps
WHERE prev_stint IS NOT NULL
  AND stint_number != prev_stint + 1;  -- Stints should increment by 1
-- Expected: 0 rows
*/

-- ============================================================================
-- Performance Notes
-- ============================================================================

/*
Insert Performance:
- Bulk inserts recommended (1000+ rows per batch)
- Pre-calculate stint_id to avoid repeated concatenation
- Index creation AFTER bulk insert for faster loading

Query Performance:
- Player-game lookups: O(log n) with idx_player_pm_snapshots_player_game
- On/off queries: Fast with idx_player_pm_snapshots_on_court
- Stint queries: Fast with idx_player_pm_snapshots_stint
- Time-based scans: Indexed on time_elapsed_seconds

Storage Estimates:
- ~150 bytes per row (smaller than lineup_snapshots)
- ~3500 events × 10 players active = 35,000 rows per game
- 1000 games = 35M rows × 150 bytes = ~5.25 GB
- With indexes: ~9 GB for 1000 games

Optimization Tips:
- Use stint_id for all stint-based queries
- Filter on on_court=1 for on-court analysis to reduce row count by ~50%
- Use possession_number instead of time_elapsed_seconds when available
- Materialize frequently-used aggregations (on/off differentials, stint stats)
- Consider partitioning by season for multi-year analyses
*/

-- ============================================================================

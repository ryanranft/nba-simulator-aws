-- Temporal Box Score Snapshot Schema
-- Created: October 18, 2025
-- Purpose: Store play-by-play derived box scores at every moment in game time
--          Optimized for ML queries and temporal analytics

-- ============================================================================
-- PLAYER BOX SCORE SNAPSHOTS
-- ============================================================================
-- One row per player per event
-- Allows queries like: "What were LeBron's stats at halftime?"

CREATE TABLE IF NOT EXISTS player_box_score_snapshots (
    -- Identifiers
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    event_number INTEGER NOT NULL,  -- Sequence number (1, 2, 3, ...)
    player_id TEXT NOT NULL,
    player_name TEXT,
    team_id TEXT NOT NULL,

    -- Game context
    period INTEGER NOT NULL,         -- Quarter (1-4, or 5+ for OT)
    game_clock TEXT,                 -- Time remaining in period (e.g., "7:42")
    time_elapsed_seconds INTEGER,    -- Total seconds elapsed in game
    timestamp DATETIME,              -- Real-world timestamp (if available)

    -- Cumulative stats (total SO FAR in the game)
    points INTEGER DEFAULT 0,
    fgm INTEGER DEFAULT 0,           -- Field goals made
    fga INTEGER DEFAULT 0,           -- Field goals attempted
    fg_pct REAL,                     -- FG% at this moment
    fg3m INTEGER DEFAULT 0,
    fg3a INTEGER DEFAULT 0,
    fg3_pct REAL,
    ftm INTEGER DEFAULT 0,
    fta INTEGER DEFAULT 0,
    ft_pct REAL,

    -- Rebounds
    oreb INTEGER DEFAULT 0,          -- Offensive rebounds
    dreb INTEGER DEFAULT 0,          -- Defensive rebounds
    reb INTEGER DEFAULT 0,           -- Total rebounds

    -- Other stats
    ast INTEGER DEFAULT 0,           -- Assists
    stl INTEGER DEFAULT 0,           -- Steals
    blk INTEGER DEFAULT 0,           -- Blocks
    tov INTEGER DEFAULT 0,           -- Turnovers
    pf INTEGER DEFAULT 0,            -- Personal fouls

    -- Advanced
    plus_minus INTEGER DEFAULT 0,
    minutes REAL DEFAULT 0.0,
    on_court BOOLEAN DEFAULT 0,      -- Is player currently on court?

    -- Advanced Statistics (derived from PBP)
    true_shooting_pct REAL,          -- TS% = PTS / (2 * (FGA + 0.44 * FTA))
    effective_fg_pct REAL,           -- eFG% = (FGM + 0.5 * 3PM) / FGA
    three_point_attempt_rate REAL,   -- 3PAr = 3PA / FGA * 100
    ts_attempts REAL,                -- True shooting attempts = FGA + 0.44 * FTA

    -- Usage and Efficiency
    usage_rate REAL,                 -- % of team plays used while on court
    assist_rate REAL,                -- AST / FGM (team) - legacy metric
    assist_percentage REAL,          -- AST% = % of teammate FG assisted while on floor (Basketball Reference)
    turnover_rate REAL,              -- TOV / (FGA + 0.44*FTA + TOV)

    -- Rebounding
    offensive_rebound_pct REAL,      -- OREB / (team OREB + opp DREB)
    defensive_rebound_pct REAL,      -- DREB / (team DREB + opp OREB)
    total_rebound_pct REAL,          -- REB / (team REB + opp REB)

    -- Defensive Percentages (require on-floor tracking)
    steal_percentage REAL,           -- STL% = Steals per 100 opponent possessions
    block_percentage REAL,           -- BLK% = Blocks per 100 opponent 2PT FGA

    -- Impact
    game_score REAL,                 -- Game Score = PTS + 0.4*FGM - 0.7*FGA - 0.4*(FTA-FTM) + 0.7*OREB + 0.3*DREB + STL + 0.7*AST + 0.7*BLK - 0.4*PF - TOV
    offensive_rating REAL,           -- Points produced per 100 possessions
    box_plus_minus REAL,             -- BPM = Points above average per 100 possessions
    assist_to_turnover REAL,         -- AST / TOV ratio

    -- Shooting breakdown
    points_in_paint INTEGER DEFAULT 0,
    second_chance_points INTEGER DEFAULT 0,
    fast_break_points INTEGER DEFAULT 0,
    points_off_turnovers INTEGER DEFAULT 0,

    -- Line Score (quarter-by-quarter scoring)
    q1_points INTEGER DEFAULT 0,     -- Points scored in Q1 only
    q2_points INTEGER DEFAULT 0,     -- Points scored in Q2 only
    q3_points INTEGER DEFAULT 0,     -- Points scored in Q3 only
    q4_points INTEGER DEFAULT 0,     -- Points scored in Q4 only
    overtime_line_score TEXT,        -- JSON array of OT points: ["5", "3", "7"] for unlimited OT periods

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(game_id, event_number, player_id)
);

-- Indexes for ML queries
CREATE INDEX IF NOT EXISTS idx_player_snapshots_game_player
    ON player_box_score_snapshots(game_id, player_id, event_number);

CREATE INDEX IF NOT EXISTS idx_player_snapshots_period
    ON player_box_score_snapshots(game_id, period);

CREATE INDEX IF NOT EXISTS idx_player_snapshots_player
    ON player_box_score_snapshots(player_id, game_id);

-- Index for temporal queries
CREATE INDEX IF NOT EXISTS idx_player_snapshots_time
    ON player_box_score_snapshots(game_id, time_elapsed_seconds);

-- ============================================================================
-- TEAM BOX SCORE SNAPSHOTS
-- ============================================================================
-- One row per team per event
-- Allows queries like: "What was the score at halftime?"

CREATE TABLE IF NOT EXISTS team_box_score_snapshots (
    -- Identifiers
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    event_number INTEGER NOT NULL,
    team_id TEXT NOT NULL,
    is_home BOOLEAN NOT NULL,

    -- Game context
    period INTEGER NOT NULL,
    game_clock TEXT,
    time_elapsed_seconds INTEGER,
    timestamp DATETIME,

    -- Team totals (cumulative)
    points INTEGER DEFAULT 0,
    fgm INTEGER DEFAULT 0,
    fga INTEGER DEFAULT 0,
    fg_pct REAL,
    fg3m INTEGER DEFAULT 0,
    fg3a INTEGER DEFAULT 0,
    fg3_pct REAL,
    ftm INTEGER DEFAULT 0,
    fta INTEGER DEFAULT 0,
    ft_pct REAL,

    oreb INTEGER DEFAULT 0,
    dreb INTEGER DEFAULT 0,
    reb INTEGER DEFAULT 0,

    ast INTEGER DEFAULT 0,
    stl INTEGER DEFAULT 0,
    blk INTEGER DEFAULT 0,
    tov INTEGER DEFAULT 0,
    pf INTEGER DEFAULT 0,

    -- Score context
    score_diff INTEGER,              -- Team's score - opponent's score
    is_leading BOOLEAN,
    largest_lead INTEGER,            -- Largest lead so far in game

    -- Advanced Statistics (derived from PBP)
    true_shooting_pct REAL,          -- TS% = PTS / (2 * (FGA + 0.44 * FTA))
    effective_fg_pct REAL,           -- eFG% = (FGM + 0.5 * 3PM) / FGA
    three_point_attempt_rate REAL,   -- 3PAr = 3PA / FGA * 100
    ts_attempts REAL,                -- True shooting attempts = FGA + 0.44 * FTA

    -- Four Factors (Dean Oliver)
    efg_pct REAL,                    -- Shooting: eFG%
    tov_pct REAL,                    -- Turnovers: TOV / (FGA + 0.44*FTA + TOV)
    oreb_pct REAL,                   -- Off Rebounding: OREB / (OREB + Opp DREB)
    ft_rate REAL,                    -- Free Throws: FTA / FGA

    -- Additional Basketball Reference Percentages
    assist_percentage REAL,          -- AST% = % of FGM that were assisted
    steal_percentage REAL,           -- STL% = Steals per 100 opponent possessions
    block_percentage REAL,           -- BLK% = Blocks per 100 opponent 2PT FGA

    -- Pace and Possessions
    possessions REAL,                -- Estimated possessions = FGA - OREB + TOV + 0.44*FTA
    pace REAL,                       -- Possessions per 48 minutes
    offensive_rating REAL,           -- Points per 100 possessions
    defensive_rating REAL,           -- Opponent points per 100 possessions
    net_rating REAL,                 -- Offensive Rating - Defensive Rating
    box_plus_minus REAL,             -- BPM = Team performance above average per 100 poss

    -- Shooting breakdown
    points_in_paint INTEGER DEFAULT 0,
    second_chance_points INTEGER DEFAULT 0,
    fast_break_points INTEGER DEFAULT 0,
    points_off_turnovers INTEGER DEFAULT 0,
    bench_points INTEGER DEFAULT 0,

    -- Assists
    assist_pct REAL,                 -- AST / FGM
    assist_to_turnover REAL,         -- AST / TOV ratio

    -- Line Score (quarter-by-quarter scoring)
    q1_points INTEGER DEFAULT 0,     -- Points scored in Q1 only
    q2_points INTEGER DEFAULT 0,     -- Points scored in Q2 only
    q3_points INTEGER DEFAULT 0,     -- Points scored in Q3 only
    q4_points INTEGER DEFAULT 0,     -- Points scored in Q4 only
    overtime_line_score TEXT,        -- JSON array of OT points: ["5", "3", "7"] for unlimited OT periods

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(game_id, event_number, team_id)
);

-- Indexes for ML queries
CREATE INDEX IF NOT EXISTS idx_team_snapshots_game
    ON team_box_score_snapshots(game_id, event_number);

CREATE INDEX IF NOT EXISTS idx_team_snapshots_period
    ON team_box_score_snapshots(game_id, period);

CREATE INDEX IF NOT EXISTS idx_team_snapshots_score_diff
    ON team_box_score_snapshots(game_id, score_diff);

-- ============================================================================
-- GAME SNAPSHOT METADATA
-- ============================================================================
-- Summary of available snapshots per game

CREATE TABLE IF NOT EXISTS game_snapshot_metadata (
    game_id TEXT PRIMARY KEY,

    -- Coverage
    total_events INTEGER,
    first_event_time DATETIME,
    last_event_time DATETIME,

    -- Quality
    has_all_quarters BOOLEAN,
    has_player_data BOOLEAN,
    has_team_data BOOLEAN,
    validation_grade TEXT,           -- A, B, C, D, F (from validation)
    validation_accuracy REAL,

    -- Teams
    home_team_id TEXT,
    away_team_id TEXT,
    home_final_score INTEGER,
    away_final_score INTEGER,

    -- Processing
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT,                     -- 'espn', 'basketball_reference', 'nba_api'

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- QUARTER BOUNDARY SNAPSHOTS
-- ============================================================================
-- Pre-computed snapshots at quarter boundaries for quick access

CREATE TABLE IF NOT EXISTS quarter_boundary_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    period INTEGER NOT NULL,
    boundary_type TEXT NOT NULL,     -- 'start' or 'end'
    event_number INTEGER NOT NULL,

    -- Quick access to scores
    home_points INTEGER,
    away_points INTEGER,
    score_diff INTEGER,

    -- Reference to full snapshot
    player_snapshot_count INTEGER,
    team_snapshot_count INTEGER,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, period, boundary_type)
);

CREATE INDEX IF NOT EXISTS idx_quarter_boundaries
    ON quarter_boundary_snapshots(game_id, period);

-- ============================================================================
-- VIEWS FOR ML
-- ============================================================================

-- View: Player stats by quarter
CREATE VIEW IF NOT EXISTS vw_player_quarter_stats AS
SELECT
    p.game_id,
    p.player_id,
    p.player_name,
    p.team_id,
    p.period,
    MAX(p.points) as quarter_points,
    MAX(p.fgm) as quarter_fgm,
    MAX(p.fga) as quarter_fga,
    MAX(p.reb) as quarter_reb,
    MAX(p.ast) as quarter_ast,
    MAX(p.stl) as quarter_stl,
    MAX(p.blk) as quarter_blk,
    MAX(p.tov) as quarter_tov,
    COUNT(*) as events_in_quarter
FROM player_box_score_snapshots p
GROUP BY p.game_id, p.player_id, p.period;

-- View: Team stats by quarter
CREATE VIEW IF NOT EXISTS vw_team_quarter_stats AS
SELECT
    t.game_id,
    t.team_id,
    t.is_home,
    t.period,
    MAX(t.points) as quarter_points,
    MAX(t.fgm) as quarter_fgm,
    MAX(t.fga) as quarter_fga,
    MAX(t.reb) as quarter_reb,
    MAX(t.ast) as quarter_ast
FROM team_box_score_snapshots t
GROUP BY t.game_id, t.team_id, t.period;

-- View: Game state at halftime
CREATE VIEW IF NOT EXISTS vw_halftime_state AS
SELECT
    t.game_id,
    t.team_id,
    t.is_home,
    t.points as halftime_points,
    t.fgm as halftime_fgm,
    t.fga as halftime_fga,
    t.score_diff as halftime_diff
FROM team_box_score_snapshots t
WHERE t.period = 2
AND t.event_number = (
    SELECT MAX(event_number)
    FROM team_box_score_snapshots
    WHERE game_id = t.game_id AND period = 2 AND team_id = t.team_id
);

-- View: Clutch moments (Q4, <5 min, <5 point diff)
CREATE VIEW IF NOT EXISTS vw_clutch_moments AS
SELECT
    p.game_id,
    p.event_number,
    p.player_id,
    p.player_name,
    p.team_id,
    p.game_clock,
    p.points,
    p.fg_pct,
    t.score_diff
FROM player_box_score_snapshots p
JOIN team_box_score_snapshots t
    ON p.game_id = t.game_id
    AND p.event_number = t.event_number
    AND p.team_id = t.team_id
WHERE p.period = 4
AND p.time_elapsed_seconds >= (48 * 60 - 5 * 60)  -- Last 5 minutes
AND ABS(t.score_diff) <= 5;

-- View: Line Score (quarter-by-quarter scoring display)
CREATE VIEW IF NOT EXISTS vw_line_score AS
SELECT
    game_id,
    team_id,
    is_home,
    q1_points,
    q2_points,
    q3_points,
    q4_points,
    overtime_line_score,  -- JSON array of OT points
    points as total_points,
    event_number
FROM team_box_score_snapshots
ORDER BY game_id, is_home DESC, event_number;

-- ============================================================================
-- SAMPLE QUERIES FOR ML
-- ============================================================================

-- Query 1: Get all snapshots for a player in a game
-- SELECT * FROM player_box_score_snapshots
-- WHERE game_id = '202306120DEN' AND player_id = 'jokicni01'
-- ORDER BY event_number;

-- Query 2: Get halftime stats for all players
-- SELECT * FROM vw_halftime_state;

-- Query 3: Find when team first took the lead
-- SELECT MIN(event_number), game_clock, points
-- FROM team_box_score_snapshots
-- WHERE game_id = '202306120DEN' AND team_id = 'DEN' AND is_leading = 1;

-- Query 4: Player performance by quarter
-- SELECT * FROM vw_player_quarter_stats
-- WHERE game_id = '202306120DEN'
-- ORDER BY player_id, period;

-- Query 5: Extract momentum indicators
-- SELECT
--     game_id,
--     player_id,
--     event_number,
--     points,
--     LAG(points, 10) OVER (PARTITION BY game_id, player_id ORDER BY event_number) as points_10_events_ago,
--     points - LAG(points, 10) OVER (PARTITION BY game_id, player_id ORDER BY event_number) as recent_points
-- FROM player_box_score_snapshots
-- WHERE game_id = '202306120DEN';

-- Query 6: Find clutch performers
-- SELECT
--     player_id,
--     player_name,
--     COUNT(*) as clutch_events,
--     AVG(fg_pct) as clutch_fg_pct
-- FROM vw_clutch_moments
-- GROUP BY player_id
-- HAVING COUNT(*) > 50;

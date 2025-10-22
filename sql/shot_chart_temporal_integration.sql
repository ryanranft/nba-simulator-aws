-- ===============================================================================
-- Shot Chart Temporal Integration Schema
-- ===============================================================================
--
-- Purpose: Link shot chart data to temporal box score snapshots
-- Created: October 18, 2025
-- Database: /tmp/basketball_reference_boxscores.db
--
-- Enables queries like:
-- - "Show LeBron's shot chart in Q4 clutch moments"
-- - "Where did Curry shoot from when his team was down by 5+?"
-- - "How did Kobe's shot selection change in the 4th quarter?"
--
-- ===============================================================================

-- ===============================================================================
-- SHOT EVENT SNAPSHOTS
-- ===============================================================================
-- Store every shot attempt with temporal game context
-- Links shot charts to exact game moments

CREATE TABLE IF NOT EXISTS shot_event_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Link to temporal system
    game_id TEXT NOT NULL,
    event_number INTEGER NOT NULL,          -- Matches player_box_score_snapshots

    -- Shot identification
    shot_id TEXT NOT NULL,                  -- Unique shot identifier
    player_id TEXT NOT NULL,
    player_name TEXT,
    team_id TEXT NOT NULL,

    -- Game context (denormalized for query speed)
    period INTEGER NOT NULL,
    game_clock TEXT,
    time_elapsed_seconds INTEGER,

    -- Score context at time of shot
    score_diff INTEGER,                     -- Team's score differential
    is_leading BOOLEAN,                     -- Was team leading?
    is_clutch BOOLEAN,                      -- Q4, <5 min, <5 pt diff

    -- Shot details
    shot_made BOOLEAN NOT NULL,             -- 1 if made, 0 if missed
    shot_type TEXT NOT NULL,                -- '2PT', '3PT', 'FT'
    shot_distance INTEGER,                  -- Distance in feet
    shot_x INTEGER,                         -- X coordinate (0-50)
    shot_y INTEGER,                         -- Y coordinate (0-47)

    -- Shot classification
    shot_zone TEXT,                         -- 'paint', 'mid_range', 'three', 'corner_three'
    shot_difficulty TEXT,                   -- 'open', 'contested', 'heavily_contested'
    is_assisted BOOLEAN,                    -- Was shot assisted?
    assisting_player TEXT,                  -- Player who assisted (if any)

    -- Defender context (if available)
    closest_defender TEXT,
    defender_distance INTEGER,              -- Feet from defender

    -- Player state at time of shot
    player_points_before INTEGER,           -- Player's cumulative points before shot
    player_fgm_before INTEGER,              -- Player's made FG before shot
    player_fga_before INTEGER,              -- Player's FG attempts before shot
    player_fg_pct_before REAL,              -- Player's FG% before shot

    -- Team state at time of shot
    team_points_before INTEGER,
    team_fgm_before INTEGER,
    team_fga_before INTEGER,

    -- Momentum indicators
    player_recent_points INTEGER,           -- Points in last 5 minutes
    player_recent_fg_pct REAL,              -- FG% in last 10 shots
    team_run INTEGER,                       -- Current team run (last 2 min)

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(game_id, event_number, player_id, shot_id)
);

-- Indexes for shot queries
CREATE INDEX IF NOT EXISTS idx_shot_snapshots_game
    ON shot_event_snapshots(game_id, event_number);

CREATE INDEX IF NOT EXISTS idx_shot_snapshots_player
    ON shot_event_snapshots(player_id, game_id);

CREATE INDEX IF NOT EXISTS idx_shot_snapshots_location
    ON shot_event_snapshots(shot_x, shot_y, shot_made);

CREATE INDEX IF NOT EXISTS idx_shot_snapshots_clutch
    ON shot_event_snapshots(is_clutch, shot_made);

CREATE INDEX IF NOT EXISTS idx_shot_snapshots_zone
    ON shot_event_snapshots(shot_zone, shot_type);

-- ===============================================================================
-- PLAYER SHOOTING ZONES AGGREGATION
-- ===============================================================================
-- Pre-computed shooting efficiency by zone for ML features

CREATE TABLE IF NOT EXISTS player_shooting_zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    player_id TEXT NOT NULL,
    game_id TEXT NOT NULL,

    -- Zone breakdowns (cumulative in game)
    -- Paint (0-5 feet)
    paint_fgm INTEGER DEFAULT 0,
    paint_fga INTEGER DEFAULT 0,
    paint_fg_pct REAL,

    -- Short mid-range (5-10 feet)
    short_mid_fgm INTEGER DEFAULT 0,
    short_mid_fga INTEGER DEFAULT 0,
    short_mid_fg_pct REAL,

    -- Long mid-range (10-16 feet)
    long_mid_fgm INTEGER DEFAULT 0,
    long_mid_fga INTEGER DEFAULT 0,
    long_mid_fg_pct REAL,

    -- Three-point zones
    corner_three_fgm INTEGER DEFAULT 0,
    corner_three_fga INTEGER DEFAULT 0,
    corner_three_fg_pct REAL,

    above_break_three_fgm INTEGER DEFAULT 0,
    above_break_three_fga INTEGER DEFAULT 0,
    above_break_three_fg_pct REAL,

    -- Situational shooting
    clutch_fgm INTEGER DEFAULT 0,
    clutch_fga INTEGER DEFAULT 0,
    clutch_fg_pct REAL,

    open_fgm INTEGER DEFAULT 0,
    open_fga INTEGER DEFAULT 0,
    open_fg_pct REAL,

    contested_fgm INTEGER DEFAULT 0,
    contested_fga INTEGER DEFAULT 0,
    contested_fg_pct REAL,

    -- Assisted vs unassisted
    assisted_fgm INTEGER DEFAULT 0,
    assisted_fga INTEGER DEFAULT 0,
    assisted_fg_pct REAL,

    unassisted_fgm INTEGER DEFAULT 0,
    unassisted_fga INTEGER DEFAULT 0,
    unassisted_fg_pct REAL,

    -- Metadata
    last_updated_event INTEGER,             -- Last event number processed
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(player_id, game_id)
);

CREATE INDEX IF NOT EXISTS idx_shooting_zones_player
    ON player_shooting_zones(player_id, game_id);

-- ===============================================================================
-- VIEWS FOR ML QUERIES
-- ===============================================================================

-- View: Shot charts by quarter
CREATE VIEW IF NOT EXISTS vw_shot_chart_by_quarter AS
SELECT
    s.game_id,
    s.player_id,
    s.player_name,
    s.period,
    s.shot_x,
    s.shot_y,
    s.shot_type,
    s.shot_made,
    s.shot_distance,
    COUNT(*) as shots_in_zone,
    SUM(CASE WHEN shot_made THEN 1 ELSE 0 END) as makes_in_zone,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct_in_zone
FROM shot_event_snapshots s
GROUP BY s.game_id, s.player_id, s.period, s.shot_x, s.shot_y, s.shot_type;

-- View: Clutch shot charts
CREATE VIEW IF NOT EXISTS vw_clutch_shot_charts AS
SELECT
    s.player_id,
    s.player_name,
    s.shot_x,
    s.shot_y,
    s.shot_type,
    s.shot_distance,
    s.shot_made,
    s.score_diff,
    s.time_elapsed_seconds,
    COUNT(*) as clutch_shots,
    SUM(CASE WHEN shot_made THEN 1 ELSE 0 END) as clutch_makes,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as clutch_fg_pct
FROM shot_event_snapshots s
WHERE s.is_clutch = 1
GROUP BY s.player_id, s.shot_x, s.shot_y, s.shot_type;

-- View: Shot selection by game state
CREATE VIEW IF NOT EXISTS vw_shots_by_game_state AS
SELECT
    s.game_id,
    s.player_id,
    s.player_name,
    s.period,
    s.is_leading,
    s.shot_zone,
    s.shot_type,
    COUNT(*) as total_shots,
    SUM(CASE WHEN shot_made THEN 1 ELSE 0 END) as makes,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct,
    AVG(shot_distance) as avg_distance
FROM shot_event_snapshots s
GROUP BY s.game_id, s.player_id, s.period, s.is_leading, s.shot_zone, s.shot_type;

-- View: Momentum-based shot analysis
CREATE VIEW IF NOT EXISTS vw_shots_by_momentum AS
SELECT
    s.player_id,
    s.player_name,
    CASE
        WHEN s.player_recent_fg_pct >= 60 THEN 'Hot'
        WHEN s.player_recent_fg_pct >= 40 THEN 'Average'
        ELSE 'Cold'
    END as momentum_state,
    s.shot_zone,
    s.shot_type,
    COUNT(*) as shots,
    SUM(CASE WHEN shot_made THEN 1 ELSE 0 END) as makes,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct
FROM shot_event_snapshots s
WHERE s.player_recent_fg_pct IS NOT NULL
GROUP BY s.player_id, momentum_state, s.shot_zone, s.shot_type;

-- ===============================================================================
-- SAMPLE QUERIES
-- ===============================================================================

-- Query 1: Player's shot chart in Q4
-- SELECT shot_x, shot_y, shot_made, shot_type
-- FROM shot_event_snapshots
-- WHERE player_id = 'jamesle01' AND period = 4;

-- Query 2: Shot selection when trailing
-- SELECT shot_zone, COUNT(*) as attempts, AVG(shot_made) as fg_pct
-- FROM shot_event_snapshots
-- WHERE is_leading = 0 AND score_diff < -5
-- GROUP BY shot_zone;

-- Query 3: Clutch shooting by location
-- SELECT shot_zone, shot_type, COUNT(*) as shots, AVG(shot_made) as fg_pct
-- FROM shot_event_snapshots
-- WHERE is_clutch = 1
-- GROUP BY shot_zone, shot_type
-- ORDER BY shots DESC;

-- Query 4: Shot chart progression over game
-- SELECT period, shot_zone, COUNT(*) as shots
-- FROM shot_event_snapshots
-- WHERE player_id = 'bryanko01'
-- GROUP BY period, shot_zone
-- ORDER BY period;

-- Query 5: Assisted vs unassisted efficiency
-- SELECT is_assisted, shot_zone,
--        COUNT(*) as shots,
--        AVG(shot_made) as fg_pct
-- FROM shot_event_snapshots
-- GROUP BY is_assisted, shot_zone;

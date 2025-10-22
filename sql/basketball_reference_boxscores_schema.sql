-- ===============================================================================
-- Basketball Reference Box Scores Database Schema
-- ===============================================================================
--
-- Purpose: Store complete game-level box score data from Basketball Reference
-- Coverage: BAA (1946-1949) + NBA (1949-2025) = ~70,718 games
-- Created: October 18, 2025
-- Database: /tmp/basketball_reference_boxscores.db
--
-- ===============================================================================

-- ===============================================================================
-- GAMES TABLE - Game metadata and basic information
-- ===============================================================================

CREATE TABLE IF NOT EXISTS games (
    -- Primary key
    game_id TEXT PRIMARY KEY,              -- Basketball Reference game ID (e.g., '194611010TRH')

    -- Date information
    game_date TEXT NOT NULL,                -- Date in YYYY-MM-DD format
    season INTEGER NOT NULL,                -- Season (e.g., 1947 for 1946-47 season)

    -- Teams
    home_team TEXT NOT NULL,                -- Home team abbreviation (e.g., 'BOS')
    away_team TEXT NOT NULL,                -- Away team abbreviation (e.g., 'NYK')
    home_team_name TEXT,                    -- Full team name (e.g., 'Boston Celtics')
    away_team_name TEXT,                    -- Full team name

    -- Scores
    home_score INTEGER NOT NULL,            -- Final home team score
    away_score INTEGER NOT NULL,            -- Final away team score

    -- Game type
    game_type TEXT,                         -- 'Regular Season', 'Playoffs', 'Finals', etc.
    playoff_round TEXT,                     -- If playoffs: 'Finals', 'Conference Finals', etc.

    -- Location
    location TEXT,                          -- Arena/venue name
    city TEXT,                              -- City where game was played
    attendance INTEGER,                     -- Number of fans in attendance

    -- Officials
    officials TEXT,                         -- Comma-separated list of referees

    -- Duration
    duration TEXT,                          -- Game duration (e.g., '2:18')

    -- Overtime
    num_overtime_periods INTEGER DEFAULT 0, -- Number of OT periods (0 if regulation)

    -- Data source
    source_url TEXT,                        -- Basketball Reference URL
    scraped_at TEXT,                        -- Timestamp when scraped (ISO 8601)

    -- Data quality
    has_basic_stats BOOLEAN DEFAULT 0,      -- Has basic box score
    has_advanced_stats BOOLEAN DEFAULT 0,   -- Has advanced box score
    has_four_factors BOOLEAN DEFAULT 0,     -- Has four factors
    has_play_by_play BOOLEAN DEFAULT 0,     -- Has play-by-play data
    data_quality_score INTEGER DEFAULT 0,   -- Quality score 0-100

    -- Notes
    notes TEXT,                             -- Any special notes about this game

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for games table
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);
CREATE INDEX IF NOT EXISTS idx_games_home_team ON games(home_team);
CREATE INDEX IF NOT EXISTS idx_games_away_team ON games(away_team);
CREATE INDEX IF NOT EXISTS idx_games_type ON games(game_type);

-- ===============================================================================
-- TEAM_BOX_SCORES TABLE - Team-level statistics per game
-- ===============================================================================

CREATE TABLE IF NOT EXISTS team_box_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign key
    game_id TEXT NOT NULL,                  -- References games(game_id)
    team TEXT NOT NULL,                     -- Team abbreviation ('BOS', 'LAL', etc.)
    is_home BOOLEAN NOT NULL,               -- 1 if home team, 0 if away

    -- Basic statistics
    points INTEGER,                         -- Total points scored
    field_goals_made INTEGER,               -- Field goals made
    field_goals_attempted INTEGER,          -- Field goals attempted
    field_goal_pct REAL,                    -- Field goal percentage
    three_pointers_made INTEGER,            -- Three-pointers made (NULL if not tracked)
    three_pointers_attempted INTEGER,       -- Three-pointers attempted
    three_point_pct REAL,                   -- Three-point percentage
    free_throws_made INTEGER,               -- Free throws made
    free_throws_attempted INTEGER,          -- Free throws attempted
    free_throw_pct REAL,                    -- Free throw percentage

    -- Rebounds
    offensive_rebounds INTEGER,             -- Offensive rebounds
    defensive_rebounds INTEGER,             -- Defensive rebounds
    total_rebounds INTEGER,                 -- Total rebounds

    -- Other stats
    assists INTEGER,                        -- Assists
    steals INTEGER,                         -- Steals (NULL if not tracked)
    blocks INTEGER,                         -- Blocks (NULL if not tracked)
    turnovers INTEGER,                      -- Turnovers
    personal_fouls INTEGER,                 -- Personal fouls

    -- Advanced stats (if available)
    true_shooting_pct REAL,                 -- True shooting percentage
    effective_fg_pct REAL,                  -- Effective field goal percentage
    total_rebounding_pct REAL,              -- Total rebounding percentage
    assist_pct REAL,                        -- Assist percentage
    steal_pct REAL,                         -- Steal percentage
    block_pct REAL,                         -- Block percentage
    turnover_pct REAL,                      -- Turnover percentage

    -- Four Factors
    ff_effective_fg_pct REAL,               -- Four Factors: eFG%
    ff_turnover_pct REAL,                   -- Four Factors: TOV%
    ff_offensive_rebound_pct REAL,          -- Four Factors: ORB%
    ff_free_throw_rate REAL,                -- Four Factors: FT Rate (FTA/FGA)

    -- Pace and efficiency
    pace REAL,                              -- Pace (possessions per 48 minutes)
    offensive_rating REAL,                  -- Offensive rating
    defensive_rating REAL,                  -- Defensive rating
    net_rating REAL,                        -- Net rating (ORtg - DRtg)

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (game_id) REFERENCES games(game_id)
);

-- Indexes for team_box_scores
CREATE INDEX IF NOT EXISTS idx_team_box_scores_game ON team_box_scores(game_id);
CREATE INDEX IF NOT EXISTS idx_team_box_scores_team ON team_box_scores(team);

-- ===============================================================================
-- PLAYER_BOX_SCORES TABLE - Player-level statistics per game
-- ===============================================================================

CREATE TABLE IF NOT EXISTS player_box_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign keys
    game_id TEXT NOT NULL,                  -- References games(game_id)
    player_name TEXT NOT NULL,              -- Player full name
    player_slug TEXT,                       -- Basketball Reference player slug
    team TEXT NOT NULL,                     -- Team abbreviation

    -- Player info
    position TEXT,                          -- Position (G, F, C, etc.)
    is_starter BOOLEAN DEFAULT 0,           -- 1 if starting lineup

    -- Playing time
    minutes_played TEXT,                    -- Minutes played (e.g., '36:42')
    minutes_decimal REAL,                   -- Minutes as decimal (36.7)

    -- Shooting
    field_goals_made INTEGER,               -- Field goals made
    field_goals_attempted INTEGER,          -- Field goals attempted
    field_goal_pct REAL,                    -- Field goal percentage
    three_pointers_made INTEGER,            -- Three-pointers made
    three_pointers_attempted INTEGER,       -- Three-pointers attempted
    three_point_pct REAL,                   -- Three-point percentage
    free_throws_made INTEGER,               -- Free throws made
    free_throws_attempted INTEGER,          -- Free throws attempted
    free_throw_pct REAL,                    -- Free throw percentage

    -- Rebounds
    offensive_rebounds INTEGER,             -- Offensive rebounds
    defensive_rebounds INTEGER,             -- Defensive rebounds
    total_rebounds INTEGER,                 -- Total rebounds

    -- Other stats
    assists INTEGER,                        -- Assists
    steals INTEGER,                         -- Steals
    blocks INTEGER,                         -- Blocks
    turnovers INTEGER,                      -- Turnovers
    personal_fouls INTEGER,                 -- Personal fouls
    points INTEGER NOT NULL,                -- Total points scored

    -- Plus/minus
    plus_minus INTEGER,                     -- Plus/minus (if available)

    -- Advanced stats (if available)
    true_shooting_pct REAL,                 -- True shooting percentage
    effective_fg_pct REAL,                  -- Effective field goal percentage
    usage_rate REAL,                        -- Usage rate
    offensive_rating REAL,                  -- Offensive rating
    defensive_rating REAL,                  -- Defensive rating
    game_score REAL,                        -- Game score (Hollinger metric)
    box_plus_minus REAL,                    -- Box plus/minus

    -- Performance flags
    double_double BOOLEAN DEFAULT 0,        -- Had double-double
    triple_double BOOLEAN DEFAULT 0,        -- Had triple-double
    did_not_play BOOLEAN DEFAULT 0,         -- DNP status
    dnp_reason TEXT,                        -- Reason for DNP (injury, coach's decision, etc.)

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (game_id) REFERENCES games(game_id)
);

-- Indexes for player_box_scores
CREATE INDEX IF NOT EXISTS idx_player_box_scores_game ON player_box_scores(game_id);
CREATE INDEX IF NOT EXISTS idx_player_box_scores_player ON player_box_scores(player_name);
CREATE INDEX IF NOT EXISTS idx_player_box_scores_team ON player_box_scores(team);
CREATE INDEX IF NOT EXISTS idx_player_box_scores_points ON player_box_scores(points DESC);

-- ===============================================================================
-- GAME_PLAY_BY_PLAY TABLE - Play-by-play events (if available)
-- ===============================================================================

CREATE TABLE IF NOT EXISTS game_play_by_play (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign key
    game_id TEXT NOT NULL,                  -- References games(game_id)

    -- Event identification
    event_number INTEGER,                   -- Sequential event number in game
    quarter INTEGER NOT NULL,               -- Quarter/period (1-4, 5+ for OT)
    time_remaining TEXT,                    -- Time remaining in quarter (e.g., '11:42')
    time_elapsed_seconds INTEGER,           -- Seconds elapsed in game

    -- Event details
    event_type TEXT,                        -- 'shot', 'foul', 'rebound', 'turnover', etc.
    description TEXT,                       -- Full play description

    -- Players involved
    primary_player TEXT,                    -- Primary player (shooter, fouler, etc.)
    secondary_player TEXT,                  -- Secondary player (assister, rebounder, etc.)

    -- Teams
    offensive_team TEXT,                    -- Team on offense
    defensive_team TEXT,                    -- Team on defense

    -- Score
    home_score INTEGER,                     -- Home team score after event
    away_score INTEGER,                     -- Away team score after event
    score_diff INTEGER,                     -- Score differential (home - away)

    -- Shot details (if shot event)
    shot_made BOOLEAN,                      -- Shot made (1) or missed (0)
    shot_type TEXT,                         -- '2PT', '3PT', 'FT'
    shot_distance INTEGER,                  -- Distance in feet (if available)
    shot_x INTEGER,                         -- X coordinate (if available)
    shot_y INTEGER,                         -- Y coordinate (if available)

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (game_id) REFERENCES games(game_id)
);

-- Indexes for game_play_by_play
CREATE INDEX IF NOT EXISTS idx_pbp_game ON game_play_by_play(game_id);
CREATE INDEX IF NOT EXISTS idx_pbp_event_type ON game_play_by_play(event_type);
CREATE INDEX IF NOT EXISTS idx_pbp_player ON game_play_by_play(primary_player);

-- ===============================================================================
-- SCRAPING_PROGRESS TABLE - Track scraping progress and resume capability
-- ===============================================================================

CREATE TABLE IF NOT EXISTS scraping_progress (
    game_id TEXT PRIMARY KEY,               -- Basketball Reference game ID

    -- Game identification
    game_date TEXT NOT NULL,                -- Date in YYYY-MM-DD
    season INTEGER NOT NULL,                -- Season
    home_team TEXT,                         -- Home team
    away_team TEXT,                         -- Away team

    -- Scraping status
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'scraped', 'failed', 'skipped'
    priority INTEGER DEFAULT 5,             -- Priority 1-10 (1=highest)

    -- Attempts
    attempts INTEGER DEFAULT 0,             -- Number of scraping attempts
    max_attempts INTEGER DEFAULT 3,         -- Maximum attempts before marking failed
    last_attempt_at TEXT,                   -- Timestamp of last attempt
    last_error TEXT,                        -- Error message from last failed attempt

    -- Success
    scraped_at TEXT,                        -- Timestamp when successfully scraped

    -- Data completeness
    has_basic_stats BOOLEAN DEFAULT 0,      -- Successfully got basic box score
    has_advanced_stats BOOLEAN DEFAULT 0,   -- Successfully got advanced stats
    has_four_factors BOOLEAN DEFAULT 0,     -- Successfully got four factors
    has_play_by_play BOOLEAN DEFAULT 0,     -- Successfully got play-by-play

    -- Metadata
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for scraping_progress
CREATE INDEX IF NOT EXISTS idx_progress_status ON scraping_progress(status);
CREATE INDEX IF NOT EXISTS idx_progress_priority ON scraping_progress(priority DESC);
CREATE INDEX IF NOT EXISTS idx_progress_season ON scraping_progress(season);
CREATE INDEX IF NOT EXISTS idx_progress_date ON scraping_progress(game_date);

-- ===============================================================================
-- VIEWS - Convenient queries
-- ===============================================================================

-- View: Games with complete data
CREATE VIEW IF NOT EXISTS complete_games AS
SELECT
    g.*,
    sp.status,
    sp.has_basic_stats,
    sp.has_advanced_stats,
    sp.has_play_by_play
FROM games g
LEFT JOIN scraping_progress sp ON g.game_id = sp.game_id
WHERE sp.status = 'scraped' AND sp.has_basic_stats = 1;

-- View: Scraping progress summary by season
CREATE VIEW IF NOT EXISTS scraping_progress_by_season AS
SELECT
    season,
    COUNT(*) as total_games,
    SUM(CASE WHEN status = 'scraped' THEN 1 ELSE 0 END) as scraped,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    ROUND(100.0 * SUM(CASE WHEN status = 'scraped' THEN 1 ELSE 0 END) / COUNT(*), 2) as completion_pct
FROM scraping_progress
GROUP BY season
ORDER BY season DESC;

-- View: Player career stats (aggregated from all games)
CREATE VIEW IF NOT EXISTS player_career_totals AS
SELECT
    player_name,
    COUNT(*) as games_played,
    SUM(minutes_decimal) as total_minutes,
    SUM(points) as total_points,
    SUM(total_rebounds) as total_rebounds,
    SUM(assists) as total_assists,
    SUM(steals) as total_steals,
    SUM(blocks) as total_blocks,
    ROUND(AVG(points), 1) as ppg,
    ROUND(AVG(total_rebounds), 1) as rpg,
    ROUND(AVG(assists), 1) as apg
FROM player_box_scores
WHERE minutes_decimal > 0
GROUP BY player_name
ORDER BY total_points DESC;

-- ===============================================================================
-- TRIGGERS - Automatic timestamp updates
-- ===============================================================================

-- Update scraping_progress updated_at on modification
CREATE TRIGGER IF NOT EXISTS update_scraping_progress_timestamp
AFTER UPDATE ON scraping_progress
BEGIN
    UPDATE scraping_progress
    SET updated_at = CURRENT_TIMESTAMP
    WHERE game_id = NEW.game_id;
END;

-- Update games updated_at on modification
CREATE TRIGGER IF NOT EXISTS update_games_timestamp
AFTER UPDATE ON games
BEGIN
    UPDATE games
    SET updated_at = CURRENT_TIMESTAMP
    WHERE game_id = NEW.game_id;
END;

-- ===============================================================================
-- INITIAL DATA QUALITY CHECK QUERIES
-- ===============================================================================

-- Check 1: Total games in database
-- SELECT COUNT(*) as total_games FROM games;

-- Check 2: Games by season
-- SELECT season, COUNT(*) as games FROM games GROUP BY season ORDER BY season;

-- Check 3: Scraping progress
-- SELECT status, COUNT(*) as count FROM scraping_progress GROUP BY status;

-- Check 4: Data completeness
-- SELECT
--     SUM(has_basic_stats) as with_basic,
--     SUM(has_advanced_stats) as with_advanced,
--     SUM(has_play_by_play) as with_pbp,
--     COUNT(*) as total
-- FROM games;

-- Check 5: Top scorers all-time
-- SELECT player_name, SUM(points) as career_points, COUNT(*) as games
-- FROM player_box_scores
-- GROUP BY player_name
-- ORDER BY career_points DESC
-- LIMIT 10;

-- ===============================================================================
-- END OF SCHEMA
-- ===============================================================================

-- Master Database Schema Design
-- Unified schema for all NBA data sources (ESPN, NBA.com Stats, hoopR, Basketball Reference, Kaggle)
-- Created: October 13, 2025
-- Purpose: Integrate all data sources into a single, queryable database

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Master players table (unified across all sources)
CREATE TABLE IF NOT EXISTS master_players (
    player_id VARCHAR(50) PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    position VARCHAR(10),
    height_inches INTEGER,
    weight_lbs INTEGER,
    birth_date DATE,
    birth_country VARCHAR(50),
    college VARCHAR(100),
    draft_year INTEGER,
    draft_round INTEGER,
    draft_pick INTEGER,
    jersey_number INTEGER,
    team_id VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Source tracking
    source_player_ids JSONB, -- {"espn": "123", "nba_stats": "456", "hoopr": "789"}
    data_sources TEXT[] DEFAULT '{}',

    -- Constraints
    CONSTRAINT valid_height CHECK (height_inches BETWEEN 60 AND 90),
    CONSTRAINT valid_weight CHECK (weight_lbs BETWEEN 150 AND 350),
    CONSTRAINT valid_draft_year CHECK (draft_year BETWEEN 1946 AND 2030)
);

-- Master teams table (unified across all sources)
CREATE TABLE IF NOT EXISTS master_teams (
    team_id VARCHAR(50) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_abbreviation VARCHAR(10) NOT NULL,
    team_city VARCHAR(50),
    team_state VARCHAR(50),
    team_country VARCHAR(50) DEFAULT 'USA',
    conference VARCHAR(10) CHECK (conference IN ('Eastern', 'Western')),
    division VARCHAR(20),
    founded_year INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Source tracking
    source_team_ids JSONB, -- {"espn": "123", "nba_stats": "456", "hoopr": "789"}
    data_sources TEXT[] DEFAULT '{}',

    -- Constraints
    CONSTRAINT valid_founded_year CHECK (founded_year BETWEEN 1946 AND 2030)
);

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- Master games table (unified across all sources)
CREATE TABLE IF NOT EXISTS master_games (
    game_id VARCHAR(50) PRIMARY KEY,
    game_date DATE NOT NULL,
    season VARCHAR(20) NOT NULL,
    season_type VARCHAR(20) DEFAULT 'Regular Season', -- Regular Season, Playoffs, Preseason
    home_team_id VARCHAR(50) NOT NULL,
    away_team_id VARCHAR(50) NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    venue VARCHAR(200),
    venue_city VARCHAR(100),
    venue_state VARCHAR(50),
    attendance INTEGER,
    game_status VARCHAR(50),
    periods INTEGER DEFAULT 4,
    is_overtime BOOLEAN DEFAULT false,
    is_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Source tracking
    source_game_ids JSONB, -- {"espn": "123", "nba_stats": "456", "hoopr": "789"}
    data_sources TEXT[] DEFAULT '{}',

    -- Foreign keys
    CONSTRAINT fk_master_games_home_team FOREIGN KEY (home_team_id) REFERENCES master_teams(team_id),
    CONSTRAINT fk_master_games_away_team FOREIGN KEY (away_team_id) REFERENCES master_teams(team_id),

    -- Constraints
    CONSTRAINT valid_scores CHECK (home_score >= 0 AND away_score >= 0),
    CONSTRAINT valid_periods CHECK (periods BETWEEN 1 AND 10),
    CONSTRAINT valid_attendance CHECK (attendance >= 0)
);

-- Master player game stats (unified across all sources)
CREATE TABLE IF NOT EXISTS master_player_game_stats (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,

    -- Basic stats
    minutes_played DECIMAL(4,1),
    field_goals_made INTEGER DEFAULT 0,
    field_goals_attempted INTEGER DEFAULT 0,
    field_goal_percentage DECIMAL(5,3),
    three_pointers_made INTEGER DEFAULT 0,
    three_pointers_attempted INTEGER DEFAULT 0,
    three_point_percentage DECIMAL(5,3),
    free_throws_made INTEGER DEFAULT 0,
    free_throws_attempted INTEGER DEFAULT 0,
    free_throw_percentage DECIMAL(5,3),

    -- Advanced stats
    points INTEGER DEFAULT 0,
    rebounds INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    steals INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    personal_fouls INTEGER DEFAULT 0,

    -- Advanced metrics (calculated)
    true_shooting_percentage DECIMAL(5,3),
    effective_field_goal_percentage DECIMAL(5,3),
    player_efficiency_rating DECIMAL(5,2),
    plus_minus INTEGER,

    -- Tracking stats (NBA.com Stats)
    touches INTEGER,
    passes INTEGER,
    speed_mph DECIMAL(4,1),
    distance_miles DECIMAL(5,2),

    -- Hustle stats (NBA.com Stats)
    deflections INTEGER,
    loose_balls_recovered INTEGER,
    charges_drawn INTEGER,
    screen_assists INTEGER,

    -- Source tracking
    source_stats JSONB, -- Raw stats from each source
    data_sources TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_master_player_stats_game FOREIGN KEY (game_id) REFERENCES master_games(game_id),
    CONSTRAINT fk_master_player_stats_player FOREIGN KEY (player_id) REFERENCES master_players(player_id),
    CONSTRAINT fk_master_player_stats_team FOREIGN KEY (team_id) REFERENCES master_teams(team_id),

    -- Constraints
    CONSTRAINT valid_field_goals CHECK (field_goals_made <= field_goals_attempted),
    CONSTRAINT valid_three_pointers CHECK (three_pointers_made <= three_pointers_attempted),
    CONSTRAINT valid_free_throws CHECK (free_throws_made <= free_throws_attempted),
    CONSTRAINT valid_percentages CHECK (
        field_goal_percentage BETWEEN 0 AND 1 AND
        three_point_percentage BETWEEN 0 AND 1 AND
        free_throw_percentage BETWEEN 0 AND 1
    )
);

-- Master team game stats (unified across all sources)
CREATE TABLE IF NOT EXISTS master_team_game_stats (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    is_home BOOLEAN NOT NULL,

    -- Basic team stats
    points INTEGER DEFAULT 0,
    field_goals_made INTEGER DEFAULT 0,
    field_goals_attempted INTEGER DEFAULT 0,
    field_goal_percentage DECIMAL(5,3),
    three_pointers_made INTEGER DEFAULT 0,
    three_pointers_attempted INTEGER DEFAULT 0,
    three_point_percentage DECIMAL(5,3),
    free_throws_made INTEGER DEFAULT 0,
    free_throws_attempted INTEGER DEFAULT 0,
    free_throw_percentage DECIMAL(5,3),

    -- Advanced team stats
    rebounds INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    steals INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    personal_fouls INTEGER DEFAULT 0,

    -- Team advanced metrics
    offensive_rating DECIMAL(5,2),
    defensive_rating DECIMAL(5,2),
    pace DECIMAL(5,2),

    -- Four Factors
    effective_field_goal_percentage DECIMAL(5,3),
    turnover_percentage DECIMAL(5,3),
    offensive_rebound_percentage DECIMAL(5,3),
    free_throw_rate DECIMAL(5,3),

    -- Source tracking
    source_stats JSONB, -- Raw stats from each source
    data_sources TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_master_team_stats_game FOREIGN KEY (game_id) REFERENCES master_games(game_id),
    CONSTRAINT fk_master_team_stats_team FOREIGN KEY (team_id) REFERENCES master_teams(team_id),

    -- Constraints
    CONSTRAINT valid_team_field_goals CHECK (field_goals_made <= field_goals_attempted),
    CONSTRAINT valid_team_three_pointers CHECK (three_pointers_made <= three_pointers_attempted),
    CONSTRAINT valid_team_free_throws CHECK (free_throws_made <= free_throws_attempted)
);

-- Master play-by-play events (unified across all sources)
CREATE TABLE IF NOT EXISTS master_play_by_play (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    event_number INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    time_remaining VARCHAR(10), -- "7:32" format
    game_clock_seconds DECIMAL(8,2), -- Total seconds from start of game
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,

    -- Event details
    event_type VARCHAR(50), -- "shot", "rebound", "turnover", etc.
    event_description TEXT,
    player_id VARCHAR(50),
    team_id VARCHAR(50),

    -- Shot details (if applicable)
    shot_type VARCHAR(20), -- "2PT", "3PT", "FT"
    shot_made BOOLEAN,
    shot_distance INTEGER, -- feet
    shot_location_x DECIMAL(6,2),
    shot_location_y DECIMAL(6,2),

    -- Source tracking
    source_event_ids JSONB, -- {"espn": "123", "nba_stats": "456", "hoopr": "789"}
    data_sources TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    CONSTRAINT fk_master_pbp_game FOREIGN KEY (game_id) REFERENCES master_games(game_id),
    CONSTRAINT fk_master_pbp_player FOREIGN KEY (player_id) REFERENCES master_players(player_id),
    CONSTRAINT fk_master_pbp_team FOREIGN KEY (team_id) REFERENCES master_teams(team_id),

    -- Constraints
    CONSTRAINT valid_quarter CHECK (quarter BETWEEN 1 AND 10),
    CONSTRAINT valid_game_clock CHECK (game_clock_seconds >= 0),
    CONSTRAINT valid_scores CHECK (home_score >= 0 AND away_score >= 0)
);

-- ============================================================================
-- DATA SOURCE MAPPING TABLES
-- ============================================================================

-- Track which source provided each record
CREATE TABLE IF NOT EXISTS data_source_mapping (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    source_name VARCHAR(50) NOT NULL, -- "espn", "nba_stats", "hoopr", "basketball_reference", "kaggle"
    source_record_id VARCHAR(100),
    source_url TEXT,
    data_quality_score DECIMAL(3,2) DEFAULT 1.0, -- 0.0 to 1.0
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_quality_score CHECK (data_quality_score BETWEEN 0.0 AND 1.0)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Master players indexes
CREATE INDEX IF NOT EXISTS idx_master_players_name ON master_players(player_name);
CREATE INDEX IF NOT EXISTS idx_master_players_team ON master_players(team_id);
CREATE INDEX IF NOT EXISTS idx_master_players_active ON master_players(is_active);

-- Master teams indexes
CREATE INDEX IF NOT EXISTS idx_master_teams_abbrev ON master_teams(team_abbreviation);
CREATE INDEX IF NOT EXISTS idx_master_teams_conference ON master_teams(conference);
CREATE INDEX IF NOT EXISTS idx_master_teams_active ON master_teams(is_active);

-- Master games indexes
CREATE INDEX IF NOT EXISTS idx_master_games_date ON master_games(game_date);
CREATE INDEX IF NOT EXISTS idx_master_games_season ON master_games(season);
CREATE INDEX IF NOT EXISTS idx_master_games_teams ON master_games(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_master_games_completed ON master_games(is_completed);

-- Master player stats indexes
CREATE INDEX IF NOT EXISTS idx_master_player_stats_game ON master_player_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_master_player_stats_player ON master_player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_master_player_stats_team ON master_player_game_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_master_player_stats_date ON master_player_game_stats(game_id) INCLUDE (created_at);

-- Master team stats indexes
CREATE INDEX IF NOT EXISTS idx_master_team_stats_game ON master_team_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_master_team_stats_team ON master_team_game_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_master_team_stats_home ON master_team_game_stats(is_home);

-- Master play-by-play indexes
CREATE INDEX IF NOT EXISTS idx_master_pbp_game ON master_play_by_play(game_id);
CREATE INDEX IF NOT EXISTS idx_master_pbp_player ON master_play_by_play(player_id);
CREATE INDEX IF NOT EXISTS idx_master_pbp_team ON master_play_by_play(team_id);
CREATE INDEX IF NOT EXISTS idx_master_pbp_clock ON master_play_by_play(game_clock_seconds);
CREATE INDEX IF NOT EXISTS idx_master_pbp_quarter ON master_play_by_play(quarter);

-- Data source mapping indexes
CREATE INDEX IF NOT EXISTS idx_data_source_table ON data_source_mapping(table_name);
CREATE INDEX IF NOT EXISTS idx_data_source_source ON data_source_mapping(source_name);
CREATE INDEX IF NOT EXISTS idx_data_source_record ON data_source_mapping(record_id);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for player season averages
CREATE OR REPLACE VIEW player_season_averages AS
SELECT
    p.player_id,
    p.player_name,
    p.team_id,
    t.team_name,
    g.season,
    COUNT(*) as games_played,
    AVG(s.points) as avg_points,
    AVG(s.rebounds) as avg_rebounds,
    AVG(s.assists) as avg_assists,
    AVG(s.field_goal_percentage) as avg_fg_pct,
    AVG(s.three_point_percentage) as avg_3pt_pct,
    AVG(s.free_throw_percentage) as avg_ft_pct,
    AVG(s.player_efficiency_rating) as avg_per
FROM master_players p
JOIN master_player_game_stats s ON p.player_id = s.player_id
JOIN master_games g ON s.game_id = g.game_id
JOIN master_teams t ON p.team_id = t.team_id
WHERE g.is_completed = true
GROUP BY p.player_id, p.player_name, p.team_id, t.team_name, g.season;

-- View for team season stats
CREATE OR REPLACE VIEW team_season_stats AS
SELECT
    t.team_id,
    t.team_name,
    g.season,
    COUNT(*) as games_played,
    SUM(CASE WHEN ts.is_home THEN ts.points ELSE 0 END) as home_points,
    SUM(CASE WHEN NOT ts.is_home THEN ts.points ELSE 0 END) as away_points,
    AVG(ts.points) as avg_points,
    AVG(ts.field_goal_percentage) as avg_fg_pct,
    AVG(ts.three_point_percentage) as avg_3pt_pct,
    AVG(ts.offensive_rating) as avg_off_rating,
    AVG(ts.defensive_rating) as avg_def_rating
FROM master_teams t
JOIN master_team_game_stats ts ON t.team_id = ts.team_id
JOIN master_games g ON ts.game_id = g.game_id
WHERE g.is_completed = true
GROUP BY t.team_id, t.team_name, g.season;

-- View for game summaries
CREATE OR REPLACE VIEW game_summaries AS
SELECT
    g.game_id,
    g.game_date,
    g.season,
    ht.team_name as home_team,
    at.team_name as away_team,
    g.home_score,
    g.away_score,
    CASE
        WHEN g.home_score > g.away_score THEN ht.team_name
        WHEN g.away_score > g.home_score THEN at.team_name
        ELSE 'Tie'
    END as winner,
    ABS(g.home_score - g.away_score) as margin,
    g.periods,
    g.is_overtime,
    COUNT(pbp.id) as total_events
FROM master_games g
JOIN master_teams ht ON g.home_team_id = ht.team_id
JOIN master_teams at ON g.away_team_id = at.team_id
LEFT JOIN master_play_by_play pbp ON g.game_id = pbp.game_id
GROUP BY g.game_id, g.game_date, g.season, ht.team_name, at.team_name,
         g.home_score, g.away_score, g.periods, g.is_overtime;

-- ============================================================================
-- FUNCTIONS FOR DATA INTEGRATION
-- ============================================================================

-- Function to resolve conflicts between data sources
CREATE OR REPLACE FUNCTION resolve_stat_conflict(
    stats_by_source JSONB,
    priority_order TEXT[] DEFAULT ARRAY['nba_stats', 'espn', 'hoopr', 'basketball_reference', 'kaggle']
) RETURNS DECIMAL AS $$
DECLARE
    source TEXT;
    stat_value DECIMAL;
BEGIN
    -- Try each source in priority order
    FOREACH source IN ARRAY priority_order
    LOOP
        stat_value := (stats_by_source ->> source)::DECIMAL;
        IF stat_value IS NOT NULL AND stat_value >= 0 THEN
            RETURN stat_value;
        END IF;
    END LOOP;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate advanced metrics
CREATE OR REPLACE FUNCTION calculate_true_shooting_percentage(
    points INTEGER,
    fga INTEGER,
    fta INTEGER
) RETURNS DECIMAL AS $$
BEGIN
    IF fga + (0.44 * fta) = 0 THEN
        RETURN NULL;
    END IF;

    RETURN points / (2 * (fga + 0.44 * fta));
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS AND DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE master_players IS 'Unified player dimension table across all data sources';
COMMENT ON TABLE master_teams IS 'Unified team dimension table across all data sources';
COMMENT ON TABLE master_games IS 'Unified games fact table across all data sources';
COMMENT ON TABLE master_player_game_stats IS 'Unified player game statistics across all data sources';
COMMENT ON TABLE master_team_game_stats IS 'Unified team game statistics across all data sources';
COMMENT ON TABLE master_play_by_play IS 'Unified play-by-play events across all data sources';
COMMENT ON TABLE data_source_mapping IS 'Tracks which data source provided each record for quality control';

COMMENT ON COLUMN master_players.source_player_ids IS 'JSON object mapping source names to source-specific player IDs';
COMMENT ON COLUMN master_player_game_stats.source_stats IS 'JSON object containing raw statistics from each data source';
COMMENT ON COLUMN master_play_by_play.source_event_ids IS 'JSON object mapping source names to source-specific event IDs';

-- ============================================================================
-- GRANTS AND PERMISSIONS
-- ============================================================================

-- Grant permissions to application user (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nba_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nba_app_user;








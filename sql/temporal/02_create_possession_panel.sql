-- sql/temporal/02_create_possession_panel.sql

-- ===============================================================
-- POSSESSION PANEL DATABASE
-- Panel data structure for econometric ML training in SageMaker
-- ===============================================================
--
-- Purpose: Possession-level observations with 100+ enriched features
-- Primary Entity: offensive_team_id
-- Time Dimension: game_date, possession_number
-- Granularity: Every possession in every game
-- Expected Size: ~400K possessions for 2M events (sample), ~2-4M full dataset
--
-- ===============================================================

-- Drop existing table if needed
DROP TABLE IF EXISTS possession_panel CASCADE;

CREATE TABLE possession_panel (
    -- =================================================================
    -- PRIMARY IDENTIFIERS
    -- =================================================================
    possession_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,
    possession_number INTEGER NOT NULL,

    -- =================================================================
    -- TIME DIMENSIONS (Critical for panel data)
    -- =================================================================
    game_date DATE NOT NULL,
    season INTEGER NOT NULL,
    game_seconds_elapsed INTEGER NOT NULL,  -- Time within game
    period INTEGER NOT NULL,
    seconds_remaining INTEGER NOT NULL,

    -- =================================================================
    -- TEAMS & LINEUPS
    -- =================================================================
    offensive_team_id VARCHAR(20) NOT NULL,
    defensive_team_id VARCHAR(20) NOT NULL,

    -- Offensive lineup (5 players sorted by player_id)
    -- Note: Will be NULL initially, populated during enrichment
    off_player_1_id VARCHAR(20),
    off_player_2_id VARCHAR(20),
    off_player_3_id VARCHAR(20),
    off_player_4_id VARCHAR(20),
    off_player_5_id VARCHAR(20),
    off_lineup_hash VARCHAR(50),  -- Sorted player IDs joined by underscore

    -- Defensive lineup
    def_player_1_id VARCHAR(20),
    def_player_2_id VARCHAR(20),
    def_player_3_id VARCHAR(20),
    def_player_4_id VARCHAR(20),
    def_player_5_id VARCHAR(20),
    def_lineup_hash VARCHAR(50),

    -- =================================================================
    -- OUTCOME VARIABLES (Dependent variables for ML)
    -- =================================================================
    points_scored INTEGER NOT NULL,  -- 0, 1, 2, 3, 4+
    possession_result VARCHAR(20),   -- 'made_fg', 'miss', 'turnover', 'foul'
    possession_duration_seconds INTEGER,
    shot_attempted BOOLEAN,
    shot_made BOOLEAN,
    shot_type VARCHAR(10),  -- '2PT', '3PT', NULL
    turnover BOOLEAN,
    foul_drawn BOOLEAN,
    offensive_rebound BOOLEAN,

    -- =================================================================
    -- GAME STATE (Time-varying within game)
    -- =================================================================
    score_differential INTEGER,  -- + means offense winning
    is_clutch BOOLEAN,  -- Within 5 pts, < 5 min remaining
    is_close_game BOOLEAN,  -- Within 5 pts any time
    is_blowout BOOLEAN,  -- > 20 pt differential

    -- =================================================================
    -- LINEUP SYNERGY (Pre-computed from historical data)
    -- Will be NULL initially, populated during enrichment
    -- =================================================================
    off_lineup_net_rating FLOAT,
    off_lineup_offensive_rating FLOAT,
    off_lineup_games_together INTEGER,
    off_lineup_minutes_together FLOAT,

    def_lineup_net_rating FLOAT,
    def_lineup_defensive_rating FLOAT,
    def_lineup_games_together INTEGER,
    def_lineup_minutes_together FLOAT,

    lineup_matchup_history_possessions INTEGER,

    -- =================================================================
    -- MOMENTUM & RECENT PERFORMANCE (Time-varying)
    -- =================================================================
    off_team_run_last_5_poss INTEGER,  -- Net points last 5 possessions
    def_team_stop_streak INTEGER,
    off_team_fg_pct_this_game FLOAT,
    off_team_to_pct_this_game FLOAT,
    def_team_fg_pct_allowed_this_game FLOAT,

    -- =================================================================
    -- FATIGUE (Time-varying within game)
    -- =================================================================
    off_team_avg_minutes_this_game FLOAT,
    def_team_avg_minutes_this_game FLOAT,
    off_team_max_minutes_this_game FLOAT,  -- Minutes of most-played player
    seconds_since_last_timeout INTEGER,

    -- =================================================================
    -- TRAVEL & REST (Game-level, varies across season)
    -- Will be populated from schedule enrichment
    -- =================================================================
    off_team_days_rest INTEGER,
    def_team_days_rest INTEGER,
    off_team_is_back_to_back BOOLEAN,
    def_team_is_back_to_back BOOLEAN,
    off_team_is_3_in_4 BOOLEAN,
    def_team_is_3_in_4 BOOLEAN,
    off_team_miles_traveled_last_7d FLOAT,
    def_team_miles_traveled_last_7d FLOAT,
    timezone_difference INTEGER,

    -- =================================================================
    -- VENUE & ENVIRONMENT (Game-level, time-invariant for game)
    -- =================================================================
    venue_id VARCHAR(20),
    venue_elevation_ft INTEGER,  -- Treatment variable for causal inference
    venue_capacity INTEGER,
    venue_attendance INTEGER,
    venue_attendance_pct FLOAT,
    is_home_offense BOOLEAN,

    -- =================================================================
    -- COACHING (Game-level and dynamic)
    -- =================================================================
    off_coach_id VARCHAR(20),
    def_coach_id VARCHAR(20),
    timeouts_remaining_off INTEGER,
    timeouts_remaining_def INTEGER,
    is_after_timeout BOOLEAN,
    is_after_made_basket BOOLEAN,
    possession_type VARCHAR(20),  -- 'transition', 'halfcourt', 'fast_break'

    -- =================================================================
    -- TEMPORAL FEATURES (Season-level)
    -- =================================================================
    game_number_season INTEGER,
    season_progress_pct FLOAT,
    is_early_season BOOLEAN,
    is_mid_season BOOLEAN,
    is_late_season BOOLEAN,
    is_playoff_race BOOLEAN,
    day_of_week INTEGER,  -- 0=Monday, 6=Sunday
    is_weekend BOOLEAN,
    is_national_tv BOOLEAN,
    is_rivalry_game BOOLEAN,

    -- =================================================================
    -- TEAM QUALITY (Slow-changing across season)
    -- =================================================================
    off_team_elo FLOAT,
    def_team_elo FLOAT,
    elo_differential FLOAT,
    off_team_net_rating_season FLOAT,
    def_team_net_rating_season FLOAT,
    off_team_pace_season FLOAT,
    def_team_pace_season FLOAT,

    -- =================================================================
    -- RECENT FORM (Rolling windows)
    -- =================================================================
    off_team_wins_last_5 INTEGER,
    def_team_wins_last_5 INTEGER,
    off_team_pts_per_game_last_5 FLOAT,
    def_team_pts_allowed_per_game_last_5 FLOAT,
    off_team_performance_trend FLOAT,  -- Slope of recent performance

    -- =================================================================
    -- ROSTER HEALTH (Game-level)
    -- =================================================================
    off_team_key_players_available BOOLEAN,
    def_team_key_players_available BOOLEAN,
    off_team_starter_minutes_available_pct FLOAT,
    def_team_starter_minutes_available_pct FLOAT,

    -- =================================================================
    -- METADATA
    -- =================================================================
    data_source VARCHAR(20) DEFAULT 'espn',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- =================================================================
    -- CONSTRAINTS
    -- =================================================================
    CONSTRAINT unique_possession UNIQUE (game_id, possession_number)
);

-- =================================================================
-- INDEXES FOR PANEL DATA QUERIES
-- =================================================================

-- Primary panel query pattern: team × time
CREATE INDEX idx_panel_off_team_time
    ON possession_panel(offensive_team_id, game_date, possession_number);

CREATE INDEX idx_panel_def_team_time
    ON possession_panel(defensive_team_id, game_date, possession_number);

-- Game-level queries
CREATE INDEX idx_panel_game_poss
    ON possession_panel(game_id, possession_number);

-- Season-level queries
CREATE INDEX idx_panel_season_date
    ON possession_panel(season, game_date);

-- Lineup queries (will be useful after enrichment)
CREATE INDEX idx_panel_off_lineup
    ON possession_panel(off_lineup_hash)
    WHERE off_lineup_hash IS NOT NULL;

CREATE INDEX idx_panel_def_lineup
    ON possession_panel(def_lineup_hash)
    WHERE def_lineup_hash IS NOT NULL;

CREATE INDEX idx_panel_lineup_matchup
    ON possession_panel(off_lineup_hash, def_lineup_hash)
    WHERE off_lineup_hash IS NOT NULL AND def_lineup_hash IS NOT NULL;

-- Filter indexes for common queries
CREATE INDEX idx_panel_clutch
    ON possession_panel(game_id)
    WHERE is_clutch = TRUE;

CREATE INDEX idx_panel_back_to_back
    ON possession_panel(offensive_team_id, game_date)
    WHERE off_team_is_back_to_back = TRUE;

CREATE INDEX idx_panel_high_altitude
    ON possession_panel(venue_id, game_date)
    WHERE venue_elevation_ft > 1000;

-- =================================================================
-- TRIGGERS FOR AUTO-UPDATE
-- =================================================================

CREATE OR REPLACE FUNCTION update_possession_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER possession_updated_at
    BEFORE UPDATE ON possession_panel
    FOR EACH ROW
    EXECUTE FUNCTION update_possession_timestamp();

-- =================================================================
-- TABLE STATISTICS & COMMENTS
-- =================================================================

COMMENT ON TABLE possession_panel IS
    'Panel data structure: possession-level observations with 100+ enriched features.
     Primary entity: offensive_team_id. Time dimension: game_date, possession_number.
     Used for econometric ML training in SageMaker.
     Initial load from ESPN temporal_events, enriched with additional data sources.';

COMMENT ON COLUMN possession_panel.possession_id IS 'Unique identifier for each possession';
COMMENT ON COLUMN possession_panel.off_lineup_hash IS 'Sorted player IDs joined by underscore (e.g., "123_456_789_012_345")';
COMMENT ON COLUMN possession_panel.points_scored IS 'Outcome variable: points scored this possession (0-4+)';
COMMENT ON COLUMN possession_panel.venue_elevation_ft IS 'Treatment variable: venue altitude in feet (for causal inference of altitude effects)';
COMMENT ON COLUMN possession_panel.score_differential IS 'Positive = offensive team winning, negative = losing';
COMMENT ON COLUMN possession_panel.is_clutch IS 'Within 5 points with < 5 minutes remaining in regulation';
COMMENT ON COLUMN possession_panel.off_lineup_net_rating IS 'Historical net rating for this offensive lineup (points per 100 possessions)';
COMMENT ON COLUMN possession_panel.off_team_is_back_to_back IS 'Treatment variable: playing second game in consecutive days';

-- =================================================================
-- GRANT PERMISSIONS (adjust as needed)
-- =================================================================

-- GRANT SELECT, INSERT, UPDATE ON possession_panel TO your_sagemaker_role;
-- GRANT USAGE, SELECT ON SEQUENCE possession_panel_possession_id_seq TO your_sagemaker_role;

-- =================================================================
-- VALIDATION QUERIES (for testing)
-- =================================================================

-- Expected possessions per game (should be ~200)
-- SELECT
--     COUNT(*) / COUNT(DISTINCT game_id)::FLOAT as possessions_per_game
-- FROM possession_panel;

-- Check lineup completeness
-- SELECT
--     COUNT(*) as total_possessions,
--     COUNT(*) FILTER (WHERE off_lineup_hash IS NOT NULL) as with_lineups,
--     ROUND(100.0 * COUNT(*) FILTER (WHERE off_lineup_hash IS NOT NULL) / COUNT(*), 2) as pct_complete
-- FROM possession_panel;

-- Check temporal coverage
-- SELECT
--     season,
--     MIN(game_date) as first_game,
--     MAX(game_date) as last_game,
--     COUNT(DISTINCT game_id) as games,
--     COUNT(*) as possessions
-- FROM possession_panel
-- GROUP BY season
-- ORDER BY season;

-- Migration 0.20: hoopR Schema for nba_simulator
-- Created: November 9, 2025
-- Purpose: Create hoopr schema with tables matching nba_mcp_synthesis.hoopr_raw structure
-- Approach: Hybrid schema (critical columns + JSONB for flexibility)

-- ============================================================================
-- SCHEMA CREATION
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS hoopr;

COMMENT ON SCHEMA hoopr IS 'hoopR data collection schema - Phase 1 foundation + daily updates';

-- ============================================================================
-- 1. PLAY-BY-PLAY TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS hoopr.play_by_play_hoopr_nba (
    -- Primary Key
    event_id BIGINT PRIMARY KEY,

    -- Game Identifiers
    game_id BIGINT NOT NULL,
    season INTEGER NOT NULL,
    season_type TEXT,  -- 'Regular Season', 'Playoffs', etc.
    game_date DATE NOT NULL,
    game_datetime TIMESTAMP,

    -- Event Sequencing
    sequence_number INTEGER,
    game_play_number INTEGER,

    -- Period/Time
    period INTEGER,
    period_number INTEGER,
    clock TEXT,  -- Display value (e.g., "3:45")
    clock_minutes INTEGER,
    clock_seconds INTEGER,
    wallclock TIMESTAMP,  -- Real-world timestamp

    -- Event Type
    type_id INTEGER,
    type_text TEXT,
    type_abbreviation TEXT,
    description TEXT,

    -- Scoring
    home_score INTEGER,
    away_score INTEGER,
    scoring_play BOOLEAN,
    score_value INTEGER,
    shooting_play BOOLEAN,

    -- Players
    athlete_id_1 BIGINT,  -- Primary player
    athlete_id_2 BIGINT,  -- Secondary player (assists, fouls, etc.)
    athlete_id_3 BIGINT,  -- Third player (rare)

    -- Team
    team_id BIGINT,
    home_team_id BIGINT,
    home_team_name TEXT,
    home_team_abbrev TEXT,
    away_team_id BIGINT,
    away_team_name TEXT,
    away_team_abbrev TEXT,

    -- Shot Location
    coordinate_x NUMERIC,
    coordinate_y NUMERIC,

    -- Full Data (JSONB for flexibility)
    raw_data JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for play-by-play
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_game_id ON hoopr.play_by_play_hoopr_nba(game_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_season ON hoopr.play_by_play_hoopr_nba(season);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_game_date ON hoopr.play_by_play_hoopr_nba(game_date);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_team_id ON hoopr.play_by_play_hoopr_nba(team_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_athlete_1 ON hoopr.play_by_play_hoopr_nba(athlete_id_1);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_type_text ON hoopr.play_by_play_hoopr_nba(type_text);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbp_scoring ON hoopr.play_by_play_hoopr_nba(scoring_play) WHERE scoring_play = TRUE;

COMMENT ON TABLE hoopr.play_by_play_hoopr_nba IS 'hoopR play-by-play events with coordinates and full metadata';

-- ============================================================================
-- 2. PLAYER BOX SCORES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS hoopr.player_box_hoopr_nba (
    -- Primary Key (composite)
    id BIGSERIAL PRIMARY KEY,

    -- Game Identifiers
    game_id BIGINT NOT NULL,
    season INTEGER NOT NULL,
    season_type TEXT,
    game_date DATE NOT NULL,
    game_datetime TIMESTAMP,

    -- Player Identifiers
    athlete_id BIGINT NOT NULL,
    athlete_name TEXT,
    athlete_position TEXT,
    athlete_jersey TEXT,

    -- Team Identifiers
    team_id BIGINT NOT NULL,
    team_name TEXT,
    team_abbrev TEXT,
    home_away TEXT,  -- 'home' or 'away'

    -- Traditional Stats
    minutes TEXT,  -- Format: "35:42"
    fgm INTEGER,  -- Field goals made
    fga INTEGER,  -- Field goals attempted
    fg_pct NUMERIC,
    fg3m INTEGER,  -- Three-pointers made
    fg3a INTEGER,  -- Three-pointers attempted
    fg3_pct NUMERIC,
    ftm INTEGER,  -- Free throws made
    fta INTEGER,  -- Free throws attempted
    ft_pct NUMERIC,
    oreb INTEGER,  -- Offensive rebounds
    dreb INTEGER,  -- Defensive rebounds
    reb INTEGER,   -- Total rebounds
    ast INTEGER,   -- Assists
    stl INTEGER,   -- Steals
    blk INTEGER,   -- Blocks
    tov INTEGER,   -- Turnovers
    pf INTEGER,    -- Personal fouls
    pts INTEGER,   -- Points
    plus_minus INTEGER,

    -- Status
    starter BOOLEAN,
    did_not_play BOOLEAN,
    ejected BOOLEAN,
    dnp_reason TEXT,

    -- Opponent
    opponent_team_id BIGINT,
    opponent_team_name TEXT,
    opponent_team_abbrev TEXT,
    opponent_score INTEGER,

    -- Full Data (JSONB for advanced stats)
    raw_data JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint
    UNIQUE(game_id, athlete_id)
);

-- Indexes for player box scores
CREATE INDEX IF NOT EXISTS idx_hoopr_pbox_game_id ON hoopr.player_box_hoopr_nba(game_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbox_athlete_id ON hoopr.player_box_hoopr_nba(athlete_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbox_team_id ON hoopr.player_box_hoopr_nba(team_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbox_season ON hoopr.player_box_hoopr_nba(season);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbox_game_date ON hoopr.player_box_hoopr_nba(game_date);
CREATE INDEX IF NOT EXISTS idx_hoopr_pbox_starter ON hoopr.player_box_hoopr_nba(starter) WHERE starter = TRUE;

COMMENT ON TABLE hoopr.player_box_hoopr_nba IS 'hoopR player box scores with traditional stats';

-- ============================================================================
-- 3. TEAM BOX SCORES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS hoopr.team_box_hoopr_nba (
    -- Primary Key (composite)
    id BIGSERIAL PRIMARY KEY,

    -- Game Identifiers
    game_id BIGINT NOT NULL,
    season INTEGER NOT NULL,
    season_type TEXT,
    game_date DATE NOT NULL,
    game_datetime TIMESTAMP,

    -- Team Identifiers
    team_id BIGINT NOT NULL,
    team_name TEXT,
    team_abbrev TEXT,
    home_away TEXT,
    team_score INTEGER,
    team_winner BOOLEAN,

    -- Traditional Stats
    fgm INTEGER,
    fga INTEGER,
    fg_pct NUMERIC,
    fg3m INTEGER,
    fg3a INTEGER,
    fg3_pct NUMERIC,
    ftm INTEGER,
    fta INTEGER,
    ft_pct NUMERIC,
    oreb INTEGER,
    dreb INTEGER,
    reb INTEGER,
    ast INTEGER,
    stl INTEGER,
    blk INTEGER,
    tov INTEGER,
    pf INTEGER,
    pts INTEGER,

    -- Advanced Stats
    fast_break_points INTEGER,
    points_in_paint INTEGER,
    largest_lead INTEGER,
    team_turnovers INTEGER,
    technical_fouls INTEGER,
    flagrant_fouls INTEGER,

    -- Opponent
    opponent_team_id BIGINT,
    opponent_team_name TEXT,
    opponent_team_abbrev TEXT,
    opponent_score INTEGER,

    -- Full Data (JSONB for all stats)
    raw_data JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint
    UNIQUE(game_id, team_id)
);

-- Indexes for team box scores
CREATE INDEX IF NOT EXISTS idx_hoopr_tbox_game_id ON hoopr.team_box_hoopr_nba(game_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_tbox_team_id ON hoopr.team_box_hoopr_nba(team_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_tbox_season ON hoopr.team_box_hoopr_nba(season);
CREATE INDEX IF NOT EXISTS idx_hoopr_tbox_game_date ON hoopr.team_box_hoopr_nba(game_date);
CREATE INDEX IF NOT EXISTS idx_hoopr_tbox_winner ON hoopr.team_box_hoopr_nba(team_winner) WHERE team_winner = TRUE;

COMMENT ON TABLE hoopr.team_box_hoopr_nba IS 'hoopR team box scores with traditional and advanced stats';

-- ============================================================================
-- 4. SCHEDULE TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS hoopr.schedule_hoopr_nba (
    -- Primary Key
    game_id BIGINT PRIMARY KEY,

    -- Season
    season INTEGER NOT NULL,
    season_type TEXT,
    game_date DATE NOT NULL,
    game_datetime TIMESTAMP,

    -- Teams
    home_team_id BIGINT NOT NULL,
    away_team_id BIGINT NOT NULL,
    home_team_name TEXT,
    home_team_abbrev TEXT,
    away_team_name TEXT,
    away_team_abbrev TEXT,

    -- Scores
    home_score INTEGER,
    away_score INTEGER,
    home_winner BOOLEAN,
    away_winner BOOLEAN,

    -- Game Status
    status_type TEXT,  -- 'Final', 'In Progress', 'Scheduled'
    status_detail TEXT,
    game_completed BOOLEAN,

    -- Venue
    venue_name TEXT,
    venue_city TEXT,
    venue_state TEXT,
    neutral_site BOOLEAN,

    -- Broadcast
    broadcast_network TEXT,
    broadcast_market TEXT,

    -- Attendance
    attendance INTEGER,

    -- Data Availability
    pbp_available BOOLEAN,
    team_box_available BOOLEAN,
    player_box_available BOOLEAN,

    -- Full Data (JSONB for all details)
    raw_data JSONB,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for schedule
CREATE INDEX IF NOT EXISTS idx_hoopr_sched_season ON hoopr.schedule_hoopr_nba(season);
CREATE INDEX IF NOT EXISTS idx_hoopr_sched_game_date ON hoopr.schedule_hoopr_nba(game_date);
CREATE INDEX IF NOT EXISTS idx_hoopr_sched_home_team ON hoopr.schedule_hoopr_nba(home_team_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_sched_away_team ON hoopr.schedule_hoopr_nba(away_team_id);
CREATE INDEX IF NOT EXISTS idx_hoopr_sched_status ON hoopr.schedule_hoopr_nba(status_type);
CREATE INDEX IF NOT EXISTS idx_hoopr_sched_completed ON hoopr.schedule_hoopr_nba(game_completed) WHERE game_completed = TRUE;

COMMENT ON TABLE hoopr.schedule_hoopr_nba IS 'hoopR game schedule with scores and metadata';

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION hoopr.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for all tables
CREATE TRIGGER update_play_by_play_updated_at
    BEFORE UPDATE ON hoopr.play_by_play_hoopr_nba
    FOR EACH ROW
    EXECUTE FUNCTION hoopr.update_updated_at_column();

CREATE TRIGGER update_player_box_updated_at
    BEFORE UPDATE ON hoopr.player_box_hoopr_nba
    FOR EACH ROW
    EXECUTE FUNCTION hoopr.update_updated_at_column();

CREATE TRIGGER update_team_box_updated_at
    BEFORE UPDATE ON hoopr.team_box_hoopr_nba
    FOR EACH ROW
    EXECUTE FUNCTION hoopr.update_updated_at_column();

CREATE TRIGGER update_schedule_updated_at
    BEFORE UPDATE ON hoopr.schedule_hoopr_nba
    FOR EACH ROW
    EXECUTE FUNCTION hoopr.update_updated_at_column();

-- ============================================================================
-- GRANTS (Adjust as needed for your user)
-- ============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA hoopr TO ryanranft;

-- Grant privileges on tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA hoopr TO ryanranft;

-- Grant sequence privileges
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA hoopr TO ryanranft;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify schema creation
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'hoopr'
ORDER BY tablename;

COMMENT ON SCHEMA hoopr IS 'hoopR data - Created 2025-11-09, Migration 0.20';

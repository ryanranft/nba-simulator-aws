-- Migration: 0.18 - Create ESPN Schema and Tables
-- Created: November 7, 2025
-- Purpose: Create dedicated ESPN schema with comprehensive tables for 146K+ ESPN JSON files
-- Status: Production Ready

-- =============================================================================
-- SCHEMA CREATION
-- =============================================================================

-- Create dedicated ESPN schema
CREATE SCHEMA IF NOT EXISTS espn;

COMMENT ON SCHEMA espn IS 'ESPN-specific data loaded from local JSON files. Contains 146,115+ files across box scores, schedules, team stats, and play-by-play data. Separate from raw_data multi-source schema.';

-- =============================================================================
-- TABLE 1: espn.espn_games
-- Purpose: Game-level data with enrichment (box scores)
-- Source: /Users/ryanranft/0espn/data/nba/nba_box_score/*.json
-- Expected rows: 44,828
-- =============================================================================

CREATE TABLE IF NOT EXISTS espn.espn_games (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) UNIQUE NOT NULL,
    season INTEGER NOT NULL,
    season_type INTEGER,  -- 1=Preseason, 2=Regular Season, 3=Playoffs, 5=Play-In Tournament
    game_date TIMESTAMP WITH TIME ZONE,
    home_team VARCHAR(100),
    away_team VARCHAR(100),
    home_score INTEGER,
    away_score INTEGER,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data JSONB NOT NULL,  -- Full game JSON with ESPNFeatureExtractor enrichment (58 features)
    metadata JSONB,       -- Source info, processing details, file path
    CONSTRAINT espn_games_season_type_check CHECK (season_type IN (1, 2, 3, 5))
);

COMMENT ON TABLE espn.espn_games IS 'ESPN game data with full box scores and enrichment. Each record represents one NBA game loaded from local ESPN JSON files.';
COMMENT ON COLUMN espn.espn_games.season_type IS '1=Preseason, 2=Regular Season, 3=Playoffs, 5=Play-In Tournament. Code 4 does not exist in ESPN data.';
COMMENT ON COLUMN espn.espn_games.data IS 'Full JSONB game data including teams, players, stats, and 58 ESPN features extracted by ESPNFeatureExtractor';

-- Indexes for espn.espn_games
CREATE INDEX idx_espn_games_game_id ON espn.espn_games(game_id);
CREATE INDEX idx_espn_games_season ON espn.espn_games(season);
CREATE INDEX idx_espn_games_season_type ON espn.espn_games(season_type);
CREATE INDEX idx_espn_games_game_date ON espn.espn_games(game_date);
CREATE INDEX idx_espn_games_home_team ON espn.espn_games(home_team);
CREATE INDEX idx_espn_games_away_team ON espn.espn_games(away_team);
CREATE INDEX idx_espn_games_data_gin ON espn.espn_games USING GIN(data);
CREATE INDEX idx_espn_games_metadata_gin ON espn.espn_games USING GIN(metadata);

-- =============================================================================
-- TABLE 2: espn.espn_schedules
-- Purpose: Daily schedule data
-- Source: /Users/ryanranft/0espn/data/nba/nba_schedule_json/*.json
-- Expected rows: 11,633
-- =============================================================================

CREATE TABLE IF NOT EXISTS espn.espn_schedules (
    id SERIAL PRIMARY KEY,
    schedule_date DATE UNIQUE NOT NULL,
    season INTEGER,
    num_games INTEGER,  -- Count of games on this date
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data JSONB NOT NULL,  -- Full schedule JSON for the date
    metadata JSONB
);

COMMENT ON TABLE espn.espn_schedules IS 'ESPN daily schedule data. Each record represents one day of NBA games, loaded from schedule JSON files (YYYYMMDD.json format).';
COMMENT ON COLUMN espn.espn_schedules.schedule_date IS 'Date of games in this schedule. Extracted from JSON filename (YYYYMMDD.json).';
COMMENT ON COLUMN espn.espn_schedules.num_games IS 'Number of games scheduled for this date';

-- Indexes for espn.espn_schedules
CREATE INDEX idx_espn_schedules_date ON espn.espn_schedules(schedule_date);
CREATE INDEX idx_espn_schedules_season ON espn.espn_schedules(season);
CREATE INDEX idx_espn_schedules_data_gin ON espn.espn_schedules USING GIN(data);

-- =============================================================================
-- TABLE 3: espn.espn_team_stats
-- Purpose: Team-level game statistics (2 records per game: home + away)
-- Source: /Users/ryanranft/0espn/data/nba/nba_team_stats/*.json
-- Expected rows: ~89,656 (2 teams per game × 44,828 games)
-- =============================================================================

CREATE TABLE IF NOT EXISTS espn.espn_team_stats (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    team_name VARCHAR(100),
    is_home BOOLEAN NOT NULL,
    season INTEGER,
    season_type INTEGER,
    game_date TIMESTAMP WITH TIME ZONE,
    points INTEGER,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data JSONB NOT NULL,  -- Team stats JSON (field goals, rebounds, assists, etc.)
    metadata JSONB,
    UNIQUE(game_id, team_id),
    FOREIGN KEY (game_id) REFERENCES espn.espn_games(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE espn.espn_team_stats IS 'Team-level statistics for each game. Two records per game (home team + away team). References espn.espn_games via game_id foreign key.';
COMMENT ON COLUMN espn.espn_team_stats.is_home IS 'TRUE if home team, FALSE if away team';
COMMENT ON COLUMN espn.espn_team_stats.data IS 'Full team statistics JSONB including shooting percentages, rebounds, assists, turnovers, etc.';

-- Indexes for espn.espn_team_stats
CREATE INDEX idx_espn_team_stats_game_id ON espn.espn_team_stats(game_id);
CREATE INDEX idx_espn_team_stats_team_id ON espn.espn_team_stats(team_id);
CREATE INDEX idx_espn_team_stats_team_name ON espn.espn_team_stats(team_name);
CREATE INDEX idx_espn_team_stats_season ON espn.espn_team_stats(season);
CREATE INDEX idx_espn_team_stats_season_type ON espn.espn_team_stats(season_type);
CREATE INDEX idx_espn_team_stats_game_date ON espn.espn_team_stats(game_date);
CREATE INDEX idx_espn_team_stats_data_gin ON espn.espn_team_stats USING GIN(data);

-- =============================================================================
-- TABLE 4: espn.espn_plays
-- Purpose: Play-by-play event data for temporal panel queries
-- Source: /Users/ryanranft/0espn/data/nba/nba_pbp/*.json
-- Expected rows: ~14,114,618 (individual play records)
-- =============================================================================

CREATE TABLE IF NOT EXISTS espn.espn_plays (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    play_id VARCHAR(100),
    sequence_number INTEGER,  -- Play sequence within game
    period INTEGER,
    clock VARCHAR(20),        -- Game clock time (MM:SS format)
    timestamp_ms BIGINT,      -- Milliseconds since game start (for temporal queries)
    team_id VARCHAR(50),
    scoring_play BOOLEAN DEFAULT FALSE,
    play_type VARCHAR(100),   -- Shot, Turnover, Rebound, etc.
    description TEXT,         -- Full play description
    home_score INTEGER,       -- Score after play
    away_score INTEGER,       -- Score after play
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data JSONB NOT NULL,      -- Full play JSON
    metadata JSONB,
    FOREIGN KEY (game_id) REFERENCES espn.espn_games(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE espn.espn_plays IS 'Individual play-by-play events. ~14.1M records extracted from ESPN PBP JSON files. Each record is one play (shot, pass, rebound, etc.). Optimized for temporal queries with timestamp_ms field.';
COMMENT ON COLUMN espn.espn_plays.timestamp_ms IS 'Milliseconds elapsed since game start. Calculated from period and clock for precise temporal queries (e.g., "stats at exactly 7:02:34.56 PM CT on June 19, 2016")';
COMMENT ON COLUMN espn.espn_plays.scoring_play IS 'TRUE if play resulted in points scored';
COMMENT ON COLUMN espn.espn_plays.data IS 'Full play JSONB including coordinates, players involved, assist info, etc.';

-- Indexes for espn.espn_plays
CREATE INDEX idx_espn_plays_game_id ON espn.espn_plays(game_id);
CREATE INDEX idx_espn_plays_play_id ON espn.espn_plays(play_id);
CREATE INDEX idx_espn_plays_sequence ON espn.espn_plays(sequence_number);
CREATE INDEX idx_espn_plays_period ON espn.espn_plays(period);
CREATE INDEX idx_espn_plays_timestamp ON espn.espn_plays(timestamp_ms);
CREATE INDEX idx_espn_plays_team_id ON espn.espn_plays(team_id);
CREATE INDEX idx_espn_plays_scoring ON espn.espn_plays(scoring_play) WHERE scoring_play = TRUE;
CREATE INDEX idx_espn_plays_play_type ON espn.espn_plays(play_type);
CREATE INDEX idx_espn_plays_game_period ON espn.espn_plays(game_id, period);  -- Composite for period queries
CREATE INDEX idx_espn_plays_game_timestamp ON espn.espn_plays(game_id, timestamp_ms);  -- Composite for temporal queries
CREATE INDEX idx_espn_plays_data_gin ON espn.espn_plays USING GIN(data);

-- =============================================================================
-- SCHEMA VERSION TRACKING
-- =============================================================================

-- Update schema version table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'raw_data' AND table_name = 'schema_version') THEN
        INSERT INTO raw_data.schema_version (version, description, applied_at)
        VALUES ('0.18', 'Create ESPN schema with espn_games, espn_schedules, espn_team_stats, espn_plays tables', NOW())
        ON CONFLICT (version) DO NOTHING;
    END IF;
END $$;

-- =============================================================================
-- GRANTS (if needed for specific users)
-- =============================================================================

-- Grant usage on schema to current user (ryanranft)
GRANT USAGE ON SCHEMA espn TO ryanranft;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA espn TO ryanranft;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA espn TO ryanranft;

-- =============================================================================
-- SUMMARY
-- =============================================================================

-- Print summary of created objects
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_schema = 'espn';
    SELECT COUNT(*) INTO index_count FROM pg_indexes WHERE schemaname = 'espn';

    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'ESPN Schema Migration 0.18 - COMPLETE';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Schema: espn';
    RAISE NOTICE 'Tables created: %', table_count;
    RAISE NOTICE 'Indexes created: %', index_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Tables:';
    RAISE NOTICE '  - espn.espn_games (expected: 44,828 rows)';
    RAISE NOTICE '  - espn.espn_schedules (expected: 11,633 rows)';
    RAISE NOTICE '  - espn.espn_team_stats (expected: ~89,656 rows)';
    RAISE NOTICE '  - espn.espn_plays (expected: ~14,114,618 rows)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next step: Run 0_19_espn_data_migration.sql to migrate existing data';
    RAISE NOTICE '=================================================================';
END $$;

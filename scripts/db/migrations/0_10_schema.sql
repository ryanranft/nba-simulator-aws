-- ============================================================================
-- Phase 0.10: PostgreSQL JSONB Storage Schema
-- ============================================================================
-- Purpose: Store raw NBA data with flexible JSONB schema
-- Created: October 25, 2025
-- Implementation ID: rec_033_postgresql
-- ============================================================================

-- Create dedicated schema for raw data
CREATE SCHEMA IF NOT EXISTS raw_data;

-- ============================================================================
-- Main Tables
-- ============================================================================

-- 1. Raw NBA Games Table
CREATE TABLE IF NOT EXISTS raw_data.nba_games (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) UNIQUE NOT NULL,
    source VARCHAR(50) NOT NULL,
    season INTEGER,
    game_date DATE,
    collected_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data JSONB NOT NULL,
    metadata JSONB
);

-- 2. Raw NBA Players Table
CREATE TABLE IF NOT EXISTS raw_data.nba_players (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR(50),
    player_name VARCHAR(255),
    source VARCHAR(50) NOT NULL,
    season INTEGER,
    collected_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data JSONB NOT NULL,
    metadata JSONB,
    UNIQUE(player_id, source, season)
);

-- 3. Raw NBA Teams Table
CREATE TABLE IF NOT EXISTS raw_data.nba_teams (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(50),
    team_name VARCHAR(255),
    source VARCHAR(50) NOT NULL,
    season INTEGER,
    collected_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data JSONB NOT NULL,
    metadata JSONB,
    UNIQUE(team_id, source, season)
);

-- 4. Generic Raw Data Table (catch-all for other entity types)
CREATE TABLE IF NOT EXISTS raw_data.nba_misc (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100),
    season INTEGER,
    collected_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data JSONB NOT NULL,
    metadata JSONB
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- === Games Table Indexes ===

-- B-tree indexes for common queries
CREATE INDEX IF NOT EXISTS idx_games_source
    ON raw_data.nba_games(source);

CREATE INDEX IF NOT EXISTS idx_games_season
    ON raw_data.nba_games(season);

CREATE INDEX IF NOT EXISTS idx_games_date
    ON raw_data.nba_games(game_date);

-- GIN index for JSONB full-document search
CREATE INDEX IF NOT EXISTS idx_games_data_gin
    ON raw_data.nba_games USING GIN (data);

-- GIN index for metadata
CREATE INDEX IF NOT EXISTS idx_games_metadata_gin
    ON raw_data.nba_games USING GIN (metadata);

-- Indexes on specific JSONB fields (extract using ->> operator)
CREATE INDEX IF NOT EXISTS idx_games_home_team
    ON raw_data.nba_games ((data->>'home_team'));

CREATE INDEX IF NOT EXISTS idx_games_away_team
    ON raw_data.nba_games ((data->>'away_team'));

-- === Players Table Indexes ===

CREATE INDEX IF NOT EXISTS idx_players_source
    ON raw_data.nba_players(source);

CREATE INDEX IF NOT EXISTS idx_players_season
    ON raw_data.nba_players(season);

CREATE INDEX IF NOT EXISTS idx_players_name
    ON raw_data.nba_players(player_name);

CREATE INDEX IF NOT EXISTS idx_players_data_gin
    ON raw_data.nba_players USING GIN (data);

CREATE INDEX IF NOT EXISTS idx_players_metadata_gin
    ON raw_data.nba_players USING GIN (metadata);

-- JSONB field index for player name searches
CREATE INDEX IF NOT EXISTS idx_players_data_name
    ON raw_data.nba_players ((data->>'player_name'));

-- === Teams Table Indexes ===

CREATE INDEX IF NOT EXISTS idx_teams_source
    ON raw_data.nba_teams(source);

CREATE INDEX IF NOT EXISTS idx_teams_season
    ON raw_data.nba_teams(season);

CREATE INDEX IF NOT EXISTS idx_teams_name
    ON raw_data.nba_teams(team_name);

CREATE INDEX IF NOT EXISTS idx_teams_data_gin
    ON raw_data.nba_teams USING GIN (data);

CREATE INDEX IF NOT EXISTS idx_teams_metadata_gin
    ON raw_data.nba_teams USING GIN (metadata);

-- === Misc Table Indexes ===

CREATE INDEX IF NOT EXISTS idx_misc_source
    ON raw_data.nba_misc(source);

CREATE INDEX IF NOT EXISTS idx_misc_entity_type
    ON raw_data.nba_misc(entity_type);

CREATE INDEX IF NOT EXISTS idx_misc_season
    ON raw_data.nba_misc(season);

CREATE INDEX IF NOT EXISTS idx_misc_data_gin
    ON raw_data.nba_misc USING GIN (data);

-- ============================================================================
-- Materialized Views for Performance
-- ============================================================================

-- Games summary materialized view (frequently accessed fields)
CREATE MATERIALIZED VIEW IF NOT EXISTS raw_data.games_summary AS
SELECT
    game_id,
    source,
    season,
    game_date,
    data->>'home_team' as home_team,
    data->>'away_team' as away_team,
    (data->'home_score')::integer as home_score,
    (data->'away_score')::integer as away_score,
    data->>'status' as status,
    collected_at
FROM raw_data.nba_games;

-- Create indexes on materialized view
CREATE INDEX IF NOT EXISTS idx_games_summary_date
    ON raw_data.games_summary(game_date);

CREATE INDEX IF NOT EXISTS idx_games_summary_teams
    ON raw_data.games_summary(home_team, away_team);

CREATE INDEX IF NOT EXISTS idx_games_summary_season
    ON raw_data.games_summary(season);

-- Players summary materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS raw_data.players_summary AS
SELECT
    player_id,
    player_name,
    source,
    season,
    data->>'team' as team,
    data->>'position' as position,
    collected_at
FROM raw_data.nba_players;

CREATE INDEX IF NOT EXISTS idx_players_summary_name
    ON raw_data.players_summary(player_name);

CREATE INDEX IF NOT EXISTS idx_players_summary_season
    ON raw_data.players_summary(season);

-- ============================================================================
-- Triggers for Automatic Timestamp Updates
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION raw_data.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to games table
DROP TRIGGER IF EXISTS update_games_updated_at ON raw_data.nba_games;
CREATE TRIGGER update_games_updated_at
    BEFORE UPDATE ON raw_data.nba_games
    FOR EACH ROW
    EXECUTE FUNCTION raw_data.update_updated_at_column();

-- Apply trigger to players table
DROP TRIGGER IF EXISTS update_players_updated_at ON raw_data.nba_players;
CREATE TRIGGER update_players_updated_at
    BEFORE UPDATE ON raw_data.nba_players
    FOR EACH ROW
    EXECUTE FUNCTION raw_data.update_updated_at_column();

-- Apply trigger to teams table
DROP TRIGGER IF EXISTS update_teams_updated_at ON raw_data.nba_teams;
CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON raw_data.nba_teams
    FOR EACH ROW
    EXECUTE FUNCTION raw_data.update_updated_at_column();

-- Apply trigger to misc table
DROP TRIGGER IF EXISTS update_misc_updated_at ON raw_data.nba_misc;
CREATE TRIGGER update_misc_updated_at
    BEFORE UPDATE ON raw_data.nba_misc
    FOR EACH ROW
    EXECUTE FUNCTION raw_data.update_updated_at_column();

-- ============================================================================
-- Helper Views
-- ============================================================================

-- View for checking data sources
CREATE OR REPLACE VIEW raw_data.data_source_stats AS
SELECT
    'games' as table_name,
    source,
    COUNT(*) as record_count,
    MIN(collected_at) as first_collection,
    MAX(collected_at) as last_collection
FROM raw_data.nba_games
GROUP BY source
UNION ALL
SELECT
    'players' as table_name,
    source,
    COUNT(*) as record_count,
    MIN(collected_at) as first_collection,
    MAX(collected_at) as last_collection
FROM raw_data.nba_players
GROUP BY source
UNION ALL
SELECT
    'teams' as table_name,
    source,
    COUNT(*) as record_count,
    MIN(collected_at) as first_collection,
    MAX(collected_at) as last_collection
FROM raw_data.nba_teams
GROUP BY source
ORDER BY table_name, source;

-- View for season coverage
CREATE OR REPLACE VIEW raw_data.season_coverage AS
SELECT
    'games' as table_name,
    season,
    COUNT(*) as record_count,
    COUNT(DISTINCT source) as source_count,
    array_agg(DISTINCT source ORDER BY source) as sources
FROM raw_data.nba_games
WHERE season IS NOT NULL
GROUP BY season
UNION ALL
SELECT
    'players' as table_name,
    season,
    COUNT(*) as record_count,
    COUNT(DISTINCT source) as source_count,
    array_agg(DISTINCT source ORDER BY source) as sources
FROM raw_data.nba_players
WHERE season IS NOT NULL
GROUP BY season
ORDER BY table_name, season DESC;

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON SCHEMA raw_data IS 'Schema for storing raw NBA data with JSONB flexibility';

COMMENT ON TABLE raw_data.nba_games IS 'Raw game data from multiple sources (ESPN, NBA Stats, etc.) stored in JSONB format';
COMMENT ON COLUMN raw_data.nba_games.data IS 'Complete game data in JSON format - flexible schema allows for source-specific fields';
COMMENT ON COLUMN raw_data.nba_games.metadata IS 'Source-specific metadata (API version, scrape timestamp, etc.)';

COMMENT ON TABLE raw_data.nba_players IS 'Raw player data from multiple sources stored in JSONB format';
COMMENT ON COLUMN raw_data.nba_players.data IS 'Complete player data in JSON format';

COMMENT ON TABLE raw_data.nba_teams IS 'Raw team data from multiple sources stored in JSONB format';
COMMENT ON COLUMN raw_data.nba_teams.data IS 'Complete team data in JSON format';

COMMENT ON MATERIALIZED VIEW raw_data.games_summary IS 'Pre-computed summary of game data for fast queries. Refresh periodically with: REFRESH MATERIALIZED VIEW raw_data.games_summary;';

-- ============================================================================
-- Grant Permissions (adjust as needed for your setup)
-- ============================================================================

-- Grant usage on schema
-- GRANT USAGE ON SCHEMA raw_data TO your_app_user;

-- Grant select on all tables
-- GRANT SELECT ON ALL TABLES IN SCHEMA raw_data TO your_app_user;

-- Grant insert/update on raw tables
-- GRANT INSERT, UPDATE ON raw_data.nba_games TO your_app_user;
-- GRANT INSERT, UPDATE ON raw_data.nba_players TO your_app_user;
-- GRANT INSERT, UPDATE ON raw_data.nba_teams TO your_app_user;

-- ============================================================================
-- Maintenance Queries
-- ============================================================================

-- Refresh materialized views (run periodically)
-- REFRESH MATERIALIZED VIEW raw_data.games_summary;
-- REFRESH MATERIALIZED VIEW raw_data.players_summary;

-- Analyze tables for query optimization (run after bulk inserts)
-- ANALYZE raw_data.nba_games;
-- ANALYZE raw_data.nba_players;
-- ANALYZE raw_data.nba_teams;

-- Check index usage
-- SELECT schemaname, tablename, indexname, idx_scan
-- FROM pg_stat_user_indexes
-- WHERE schemaname = 'raw_data'
-- ORDER BY idx_scan;

-- Check table sizes
-- SELECT
--     schemaname,
--     tablename,
--     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
-- FROM pg_tables
-- WHERE schemaname = 'raw_data'
-- ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- ============================================================================
-- Schema Version
-- ============================================================================

CREATE TABLE IF NOT EXISTS raw_data.schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW(),
    description TEXT
);

INSERT INTO raw_data.schema_version (version, description)
VALUES ('0.10.0', 'Initial JSONB storage schema for Phase 0.10')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- End of Schema
-- ============================================================================

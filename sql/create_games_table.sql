-- NBA Simulator Database Schema
-- Table: games
--
-- Stores extracted game data from ESPN JSON files
-- Source: s3://nba-sim-raw-data-lake/schedule/year=YYYY/*.json
--
-- Author: Ryan Ranft
-- Date: 2025-10-01
-- Phase: 3 - RDS PostgreSQL

CREATE TABLE IF NOT EXISTS games (
    -- Primary Key
    game_id VARCHAR(20) PRIMARY KEY,

    -- Game Information
    game_date TIMESTAMP NOT NULL,
    season_year INTEGER NOT NULL,

    -- Home Team
    home_team_id VARCHAR(10) NOT NULL,
    home_team_name VARCHAR(100),
    home_team_abbrev VARCHAR(10),
    home_score INTEGER,
    home_winner BOOLEAN DEFAULT FALSE,

    -- Away Team
    away_team_id VARCHAR(10) NOT NULL,
    away_team_name VARCHAR(100),
    away_team_abbrev VARCHAR(10),
    away_score INTEGER,

    -- Venue Information
    venue_name VARCHAR(200),
    venue_city VARCHAR(100),
    venue_state VARCHAR(2),

    -- Game Status
    status VARCHAR(50),
    completed BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_games_season_year ON games(season_year);
CREATE INDEX IF NOT EXISTS idx_games_game_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_home_team ON games(home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away_team ON games(away_team_id);
CREATE INDEX IF NOT EXISTS idx_games_completed ON games(completed);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE games IS 'NBA game schedule and results data extracted from ESPN JSON files';
COMMENT ON COLUMN games.game_id IS 'Unique ESPN game identifier (e.g., 131105001)';
COMMENT ON COLUMN games.game_date IS 'Date and time of the game';
COMMENT ON COLUMN games.season_year IS 'NBA season year (partition key in S3)';
COMMENT ON COLUMN games.home_winner IS 'True if home team won the game';
COMMENT ON COLUMN games.completed IS 'True if game has finished';
COMMENT ON COLUMN games.status IS 'Game status detail (e.g., Final, In Progress)';
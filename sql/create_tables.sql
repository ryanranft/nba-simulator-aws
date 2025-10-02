-- NBA Simulator Database Schema
-- PostgreSQL 15.x
-- Purpose: Store extracted NBA game data for simulations and ML

-- ============================================================================
-- TEAMS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS teams (
    team_id VARCHAR(50) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_abbreviation VARCHAR(10),
    conference VARCHAR(20),
    division VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE teams IS 'NBA teams metadata';

-- ============================================================================
-- PLAYERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS players (
    player_id VARCHAR(50) PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    position VARCHAR(10),
    jersey_number VARCHAR(10),
    team_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE SET NULL
);

COMMENT ON TABLE players IS 'NBA players metadata';

-- ============================================================================
-- GAMES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS games (
    game_id VARCHAR(50) PRIMARY KEY,
    game_date DATE NOT NULL,
    season VARCHAR(20),
    home_team_id VARCHAR(50) NOT NULL,
    away_team_id VARCHAR(50) NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    venue VARCHAR(200),
    attendance INTEGER,
    game_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id) ON DELETE CASCADE
);

COMMENT ON TABLE games IS 'NBA games schedule and results';

-- ============================================================================
-- PLAYER_GAME_STATS TABLE (Box Scores)
-- ============================================================================
CREATE TABLE IF NOT EXISTS player_game_stats (
    stat_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    minutes_played VARCHAR(10),
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    personal_fouls INTEGER,
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    three_pointers_made INTEGER,
    three_pointers_attempted INTEGER,
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    plus_minus INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
    UNIQUE(game_id, player_id)
);

COMMENT ON TABLE player_game_stats IS 'Player statistics per game (box scores)';

-- ============================================================================
-- PLAYS TABLE (Play-by-Play)
-- ============================================================================
CREATE TABLE IF NOT EXISTS plays (
    play_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    period INTEGER NOT NULL,
    clock VARCHAR(20),
    team_id VARCHAR(50),
    player_id VARCHAR(50),
    play_type VARCHAR(100),
    play_description TEXT,
    scoring_play BOOLEAN DEFAULT FALSE,
    home_score INTEGER,
    away_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE SET NULL,
    FOREIGN KEY (player_id) REFERENCES players(player_id) ON DELETE SET NULL
);

COMMENT ON TABLE plays IS 'Play-by-play event data';

-- ============================================================================
-- TEAM_GAME_STATS TABLE (Aggregate Team Stats)
-- ============================================================================
CREATE TABLE IF NOT EXISTS team_game_stats (
    stat_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    points INTEGER,
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    three_pointers_made INTEGER,
    three_pointers_attempted INTEGER,
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    personal_fouls INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
    UNIQUE(game_id, team_id)
);

COMMENT ON TABLE team_game_stats IS 'Team-level aggregate statistics per game';
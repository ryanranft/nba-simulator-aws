-- Performance Indexes for NBA Simulator Database
-- Purpose: Optimize query performance for simulations and analytics

-- ============================================================================
-- GAMES TABLE INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);
CREATE INDEX IF NOT EXISTS idx_games_home_team ON games(home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away_team ON games(away_team_id);
CREATE INDEX IF NOT EXISTS idx_games_date_season ON games(game_date, season);

-- ============================================================================
-- PLAYER_GAME_STATS TABLE INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_player_stats_game ON player_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_team ON player_game_stats(team_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_points ON player_game_stats(points);
CREATE INDEX IF NOT EXISTS idx_player_stats_player_game ON player_game_stats(player_id, game_id);

-- ============================================================================
-- PLAYS TABLE INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_plays_game ON plays(game_id);
CREATE INDEX IF NOT EXISTS idx_plays_period ON plays(period);
CREATE INDEX IF NOT EXISTS idx_plays_player ON plays(player_id);
CREATE INDEX IF NOT EXISTS idx_plays_team ON plays(team_id);
CREATE INDEX IF NOT EXISTS idx_plays_type ON plays(play_type);
CREATE INDEX IF NOT EXISTS idx_plays_scoring ON plays(scoring_play) WHERE scoring_play = TRUE;
CREATE INDEX IF NOT EXISTS idx_plays_game_period ON plays(game_id, period);

-- ============================================================================
-- TEAM_GAME_STATS TABLE INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_team_stats_game ON team_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_game_stats(team_id);

-- ============================================================================
-- PLAYERS TABLE INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(player_name);

-- ============================================================================
-- TEAMS TABLE INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(team_name);
CREATE INDEX IF NOT EXISTS idx_teams_abbreviation ON teams(team_abbreviation);
CREATE INDEX IF NOT EXISTS idx_teams_conference ON teams(conference);
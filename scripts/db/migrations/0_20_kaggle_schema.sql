-- Migration: 0.20 - Create Kaggle Schema and Tables
-- Created: November 9, 2025
-- Purpose: Create dedicated Kaggle schema with comprehensive tables for historical NBA data (1946-2023)
-- Status: Development
-- Source: SQLite database at /Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite
-- Data: 65,698 games, 13.6M play-by-play events, 77 seasons (1946-2023)

-- =============================================================================
-- SCHEMA CREATION
-- =============================================================================

-- Create dedicated Kaggle schema
CREATE SCHEMA IF NOT EXISTS kaggle;

COMMENT ON SCHEMA kaggle IS 'Kaggle NBA historical data (1946-2023) loaded from SQLite database. Contains 16 tables with 65,698 games and 13.6M play-by-play events. Source: Kaggle Basketball Database (wyattowalsh/basketball).';

-- =============================================================================
-- TABLE 1: kaggle.game_nba_kaggle
-- Purpose: Game-level data (65,698 games from 1946-2023)
-- Source: SQLite table 'game'
-- Expected rows: 65,698
-- Priority: CRITICAL
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.game_nba_kaggle (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) UNIQUE NOT NULL,
    season INTEGER NOT NULL,
    game_date DATE,
    season_id VARCHAR(20),  -- Format: "22023" for 2022-23 season
    season_type INTEGER,    -- 1=Preseason, 2=Regular Season, 3=Playoffs
    team_id_home INTEGER,
    team_abbreviation_home VARCHAR(5),
    team_name_home VARCHAR(100),
    team_id_away INTEGER,
    team_abbreviation_away VARCHAR(5),
    team_name_away VARCHAR(100),
    matchup_home VARCHAR(50),
    matchup_away VARCHAR(50),
    wl_home VARCHAR(1),     -- W/L
    wl_away VARCHAR(1),     -- W/L
    min INTEGER,            -- Game duration in minutes
    pts_home INTEGER,
    pts_away INTEGER,
    fgm_home INTEGER,       -- Field goals made
    fga_home INTEGER,       -- Field goals attempted
    fg_pct_home DOUBLE PRECISION,
    fg3m_home INTEGER,      -- Three-pointers made
    fg3a_home INTEGER,      -- Three-pointers attempted
    fg3_pct_home DOUBLE PRECISION,
    ftm_home INTEGER,       -- Free throws made
    fta_home INTEGER,       -- Free throws attempted
    ft_pct_home DOUBLE PRECISION,
    oreb_home INTEGER,      -- Offensive rebounds
    dreb_home INTEGER,      -- Defensive rebounds
    reb_home INTEGER,       -- Total rebounds
    ast_home INTEGER,       -- Assists
    stl_home INTEGER,       -- Steals
    blk_home INTEGER,       -- Blocks
    tov_home INTEGER,       -- Turnovers
    pf_home INTEGER,        -- Personal fouls
    plus_minus_home INTEGER,
    -- Away team stats (mirror of home)
    fgm_away INTEGER,
    fga_away INTEGER,
    fg_pct_away DOUBLE PRECISION,
    fg3m_away INTEGER,
    fg3a_away INTEGER,
    fg3_pct_away DOUBLE PRECISION,
    ftm_away INTEGER,
    fta_away INTEGER,
    ft_pct_away DOUBLE PRECISION,
    oreb_away INTEGER,
    dreb_away INTEGER,
    reb_away INTEGER,
    ast_away INTEGER,
    stl_away INTEGER,
    blk_away INTEGER,
    tov_away INTEGER,
    pf_away INTEGER,
    plus_minus_away INTEGER,
    video_available BOOLEAN DEFAULT FALSE,
    video_available_flag INTEGER,

    -- Full game data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT game_nba_kaggle_season_check CHECK (season BETWEEN 1946 AND 2030),
    CONSTRAINT game_nba_kaggle_season_type_check CHECK (season_type IN (1, 2, 3))
);

COMMENT ON TABLE kaggle.game_nba_kaggle IS 'Kaggle NBA game data (1946-2023). 65,698 games across 77 seasons. Source: Kaggle Basketball Database (wyattowalsh/basketball). Includes box score statistics for home and away teams.';
COMMENT ON COLUMN kaggle.game_nba_kaggle.season_id IS 'Season identifier in format "XYYYY" where X=1 or 2 and YYYY is year (e.g., "22023" = 2022-23 season)';
COMMENT ON COLUMN kaggle.game_nba_kaggle.data IS 'Full game data from SQLite stored as JSONB for flexibility and preservation';

-- Indexes for kaggle.game_nba_kaggle
CREATE INDEX idx_kaggle_game_game_id ON kaggle.game_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_game_season ON kaggle.game_nba_kaggle(season);
CREATE INDEX idx_kaggle_game_season_type ON kaggle.game_nba_kaggle(season_type);
CREATE INDEX idx_kaggle_game_date ON kaggle.game_nba_kaggle(game_date);
CREATE INDEX idx_kaggle_game_season_id ON kaggle.game_nba_kaggle(season_id);
CREATE INDEX idx_kaggle_game_teams_home ON kaggle.game_nba_kaggle(team_id_home);
CREATE INDEX idx_kaggle_game_teams_away ON kaggle.game_nba_kaggle(team_id_away);
CREATE INDEX idx_kaggle_game_data_gin ON kaggle.game_nba_kaggle USING GIN(data);
CREATE INDEX idx_kaggle_game_metadata_gin ON kaggle.game_nba_kaggle USING GIN(metadata);

-- =============================================================================
-- TABLE 2: kaggle.play_by_play_nba_kaggle
-- Purpose: Play-by-play events (13.6M rows for temporal queries)
-- Source: SQLite table 'play_by_play'
-- Expected rows: 13,592,899
-- Priority: CRITICAL
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.play_by_play_nba_kaggle (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    eventnum INTEGER,
    eventmsgtype INTEGER,
    eventmsgactiontype INTEGER,
    period INTEGER,
    wctimestring VARCHAR(20),  -- Wall clock time (e.g., "7:02 PM")
    pctimestring VARCHAR(20),  -- Period clock time (e.g., "11:45")
    homedescription TEXT,
    neutraldescription TEXT,
    visitordescription TEXT,
    score VARCHAR(20),         -- Format: "95-88"
    scoremargin VARCHAR(10),   -- Format: "+7" or "-3"
    person1type INTEGER,
    player1_id INTEGER,
    player1_name VARCHAR(100),
    player1_team_id INTEGER,
    player1_team_city VARCHAR(50),
    player1_team_nickname VARCHAR(50),
    player1_team_abbreviation VARCHAR(5),
    person2type INTEGER,
    player2_id INTEGER,
    player2_name VARCHAR(100),
    player2_team_id INTEGER,
    player2_team_city VARCHAR(50),
    player2_team_nickname VARCHAR(50),
    player2_team_abbreviation VARCHAR(5),
    person3type INTEGER,
    player3_id INTEGER,
    player3_name VARCHAR(100),
    player3_team_id INTEGER,
    player3_team_city VARCHAR(50),
    player3_team_nickname VARCHAR(50),
    player3_team_abbreviation VARCHAR(5),
    video_available_flag INTEGER,

    -- Full play data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES kaggle.game_nba_kaggle(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE kaggle.play_by_play_nba_kaggle IS 'Play-by-play events from Kaggle dataset. 13.6M individual plays across 65,698 games (1946-2023). Enables temporal panel queries at event-level precision.';
COMMENT ON COLUMN kaggle.play_by_play_nba_kaggle.eventmsgtype IS 'Event type code: 1=Made Shot, 2=Missed Shot, 3=Free Throw, 4=Rebound, 5=Turnover, 6=Foul, etc.';
COMMENT ON COLUMN kaggle.play_by_play_nba_kaggle.pctimestring IS 'Game clock time remaining in period (MM:SS format)';
COMMENT ON COLUMN kaggle.play_by_play_nba_kaggle.data IS 'Full play data from SQLite including all fields';

-- Indexes optimized for temporal queries
CREATE INDEX idx_kaggle_pbp_game_id ON kaggle.play_by_play_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_pbp_eventnum ON kaggle.play_by_play_nba_kaggle(eventnum);
CREATE INDEX idx_kaggle_pbp_period ON kaggle.play_by_play_nba_kaggle(period);
CREATE INDEX idx_kaggle_pbp_player1_id ON kaggle.play_by_play_nba_kaggle(player1_id);
CREATE INDEX idx_kaggle_pbp_player2_id ON kaggle.play_by_play_nba_kaggle(player2_id);
CREATE INDEX idx_kaggle_pbp_eventmsgtype ON kaggle.play_by_play_nba_kaggle(eventmsgtype);
CREATE INDEX idx_kaggle_pbp_game_period ON kaggle.play_by_play_nba_kaggle(game_id, period);  -- Composite for period queries
CREATE INDEX idx_kaggle_pbp_game_eventnum ON kaggle.play_by_play_nba_kaggle(game_id, eventnum);  -- Composite for sequential queries
CREATE INDEX idx_kaggle_pbp_data_gin ON kaggle.play_by_play_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 3: kaggle.player_nba_kaggle
-- Purpose: Player biographical data (~4,800 players)
-- Source: SQLite table 'player'
-- Expected rows: 4,800
-- Priority: HIGH
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.player_nba_kaggle (
    id SERIAL PRIMARY KEY,
    player_id INTEGER UNIQUE NOT NULL,
    full_name VARCHAR(100),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    display_first_last VARCHAR(100),
    display_last_comma_first VARCHAR(100),
    display_fi_last VARCHAR(100),
    birthdate DATE,
    school VARCHAR(100),
    country VARCHAR(50),
    last_affiliation VARCHAR(100),
    height VARCHAR(10),       -- Format: "6-10"
    weight INTEGER,
    season_exp INTEGER,
    jersey VARCHAR(10),
    position VARCHAR(20),
    rosterstatus VARCHAR(20),
    games_played_current_season_flag VARCHAR(1),
    team_id INTEGER,
    team_name VARCHAR(100),
    team_abbreviation VARCHAR(5),
    team_code VARCHAR(20),
    team_city VARCHAR(50),
    playercode VARCHAR(50),
    from_year INTEGER,        -- NBA debut year
    to_year INTEGER,          -- NBA retirement year
    dleague_flag VARCHAR(1),
    nba_flag VARCHAR(1),
    games_played_flag VARCHAR(1),
    draft_year INTEGER,
    draft_round INTEGER,
    draft_number INTEGER,
    greatest_75_flag VARCHAR(1),

    -- Full player data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.player_nba_kaggle IS 'NBA player biographical data from Kaggle. ~4,800 players from NBA history (1946-2023). Includes birth dates, physical attributes, draft information, and career spans.';
COMMENT ON COLUMN kaggle.player_nba_kaggle.season_exp IS 'Years of NBA experience';
COMMENT ON COLUMN kaggle.player_nba_kaggle.greatest_75_flag IS 'Member of NBA 75th Anniversary Team (Y/N)';

-- Indexes for kaggle.player_nba_kaggle
CREATE INDEX idx_kaggle_player_id ON kaggle.player_nba_kaggle(player_id);
CREATE INDEX idx_kaggle_player_name ON kaggle.player_nba_kaggle(display_first_last);
CREATE INDEX idx_kaggle_player_team ON kaggle.player_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_player_birthdate ON kaggle.player_nba_kaggle(birthdate);
CREATE INDEX idx_kaggle_player_data_gin ON kaggle.player_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 4: kaggle.team_nba_kaggle
-- Purpose: Team reference data (30 teams)
-- Source: SQLite table 'team'
-- Expected rows: 30
-- Priority: HIGH
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.team_nba_kaggle (
    id SERIAL PRIMARY KEY,
    team_id INTEGER UNIQUE NOT NULL,
    full_name VARCHAR(100),
    abbreviation VARCHAR(5),
    nickname VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50),
    year_founded INTEGER,

    -- Full team data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.team_nba_kaggle IS 'NBA team information. 30 current teams plus historical franchises. Includes founding year and location data.';

-- Indexes for kaggle.team_nba_kaggle
CREATE INDEX idx_kaggle_team_id ON kaggle.team_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_team_abbrev ON kaggle.team_nba_kaggle(abbreviation);
CREATE INDEX idx_kaggle_team_name ON kaggle.team_nba_kaggle(full_name);
CREATE INDEX idx_kaggle_team_data_gin ON kaggle.team_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 5: kaggle.common_player_info_nba_kaggle
-- Purpose: Extended player information (~3,600 players)
-- Source: SQLite table 'common_player_info'
-- Expected rows: 3,600
-- Priority: HIGH
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.common_player_info_nba_kaggle (
    id SERIAL PRIMARY KEY,
    person_id INTEGER UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    display_first_last VARCHAR(100),
    display_last_comma_first VARCHAR(100),
    display_fi_last VARCHAR(100),
    player_slug VARCHAR(100),
    birthdate DATE,
    school VARCHAR(100),
    country VARCHAR(50),
    last_affiliation VARCHAR(100),
    height VARCHAR(10),
    weight INTEGER,
    season_exp INTEGER,
    jersey VARCHAR(10),
    position VARCHAR(20),
    rosterstatus VARCHAR(20),
    games_played_current_season_flag VARCHAR(1),
    team_id INTEGER,
    team_name VARCHAR(100),
    team_abbreviation VARCHAR(5),
    team_code VARCHAR(20),
    team_city VARCHAR(50),
    playercode VARCHAR(50),
    from_year INTEGER,
    to_year INTEGER,
    dleague_flag VARCHAR(1),
    nba_flag VARCHAR(1),
    games_played_flag VARCHAR(1),
    draft_year INTEGER,
    draft_round INTEGER,
    draft_number INTEGER,
    greatest_75_flag VARCHAR(1),

    -- Full player info data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.common_player_info_nba_kaggle IS 'Extended player information with more complete biographical data than player table. Preferred source for player analysis.';

-- Indexes
CREATE INDEX idx_kaggle_common_player_id ON kaggle.common_player_info_nba_kaggle(person_id);
CREATE INDEX idx_kaggle_common_player_name ON kaggle.common_player_info_nba_kaggle(display_first_last);
CREATE INDEX idx_kaggle_common_player_team ON kaggle.common_player_info_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_common_player_birthdate ON kaggle.common_player_info_nba_kaggle(birthdate);
CREATE INDEX idx_kaggle_common_player_data_gin ON kaggle.common_player_info_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 6: kaggle.game_info_nba_kaggle
-- Purpose: Extended game information (~58,000 records)
-- Source: SQLite table 'game_info'
-- Expected rows: 58,000
-- Priority: MEDIUM
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.game_info_nba_kaggle (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    game_date DATE,
    attendance INTEGER,
    game_time VARCHAR(20),

    -- Full game info data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES kaggle.game_nba_kaggle(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE kaggle.game_info_nba_kaggle IS 'Extended game information including attendance and game time.';

-- Indexes
CREATE INDEX idx_kaggle_game_info_game_id ON kaggle.game_info_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_game_info_date ON kaggle.game_info_nba_kaggle(game_date);
CREATE INDEX idx_kaggle_game_info_data_gin ON kaggle.game_info_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 7: kaggle.game_summary_nba_kaggle
-- Purpose: Game summary data (~58,000 records)
-- Source: SQLite table 'game_summary'
-- Expected rows: 58,000
-- Priority: MEDIUM
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.game_summary_nba_kaggle (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    game_date_est DATE,
    game_sequence INTEGER,
    game_status_id INTEGER,
    game_status_text VARCHAR(50),
    gamecode VARCHAR(50),
    home_team_id INTEGER,
    visitor_team_id INTEGER,
    season INTEGER,
    live_period INTEGER,
    live_pc_time VARCHAR(20),
    natl_tv_broadcaster_abbreviation VARCHAR(20),
    live_period_time_bcast VARCHAR(50),
    wh_status INTEGER,

    -- Full game summary data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES kaggle.game_nba_kaggle(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE kaggle.game_summary_nba_kaggle IS 'Game summary information including broadcast details and game status.';

-- Indexes
CREATE INDEX idx_kaggle_game_summary_game_id ON kaggle.game_summary_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_game_summary_date ON kaggle.game_summary_nba_kaggle(game_date_est);
CREATE INDEX idx_kaggle_game_summary_season ON kaggle.game_summary_nba_kaggle(season);
CREATE INDEX idx_kaggle_game_summary_data_gin ON kaggle.game_summary_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 8: kaggle.line_score_nba_kaggle
-- Purpose: Quarter-by-quarter scores (~58,000 records)
-- Source: SQLite table 'line_score'
-- Expected rows: 58,000
-- Priority: MEDIUM
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.line_score_nba_kaggle (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    game_date_est DATE,
    game_sequence INTEGER,
    team_id INTEGER,
    team_abbreviation VARCHAR(5),
    team_city_name VARCHAR(50),
    team_nickname VARCHAR(50),
    team_wins_losses VARCHAR(20),
    pts_qtr1 INTEGER,
    pts_qtr2 INTEGER,
    pts_qtr3 INTEGER,
    pts_qtr4 INTEGER,
    pts_ot1 INTEGER,
    pts_ot2 INTEGER,
    pts_ot3 INTEGER,
    pts_ot4 INTEGER,
    pts_ot5 INTEGER,
    pts_ot6 INTEGER,
    pts_ot7 INTEGER,
    pts_ot8 INTEGER,
    pts_ot9 INTEGER,
    pts_ot10 INTEGER,
    pts INTEGER,                -- Total points
    fg_pct DOUBLE PRECISION,
    ft_pct DOUBLE PRECISION,
    fg3_pct DOUBLE PRECISION,
    ast INTEGER,
    reb INTEGER,
    tov INTEGER,

    -- Full line score data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES kaggle.game_nba_kaggle(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE kaggle.line_score_nba_kaggle IS 'Quarter-by-quarter scoring breakdown for each team. Includes overtime periods.';

-- Indexes
CREATE INDEX idx_kaggle_line_score_game_id ON kaggle.line_score_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_line_score_team_id ON kaggle.line_score_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_line_score_date ON kaggle.line_score_nba_kaggle(game_date_est);
CREATE INDEX idx_kaggle_line_score_data_gin ON kaggle.line_score_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 9: kaggle.inactive_players_nba_kaggle
-- Purpose: Inactive player records (~110,000 records)
-- Source: SQLite table 'inactive_players'
-- Expected rows: 110,000
-- Priority: MEDIUM
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.inactive_players_nba_kaggle (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    player_id INTEGER,
    player_name VARCHAR(100),
    jersey_num VARCHAR(10),
    team_id INTEGER,
    team_city VARCHAR(50),
    team_name VARCHAR(50),
    team_abbreviation VARCHAR(5),

    -- Full inactive player data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES kaggle.game_nba_kaggle(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE kaggle.inactive_players_nba_kaggle IS 'Players inactive for each game. Useful for injury tracking and roster management analysis.';

-- Indexes
CREATE INDEX idx_kaggle_inactive_game_id ON kaggle.inactive_players_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_inactive_player_id ON kaggle.inactive_players_nba_kaggle(player_id);
CREATE INDEX idx_kaggle_inactive_team_id ON kaggle.inactive_players_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_inactive_data_gin ON kaggle.inactive_players_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 10: kaggle.officials_nba_kaggle
-- Purpose: Game officials/referees (~71,000 records)
-- Source: SQLite table 'officials'
-- Expected rows: 71,000
-- Priority: MEDIUM
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.officials_nba_kaggle (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    official_id INTEGER,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    jersey_num VARCHAR(10),

    -- Full officials data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES kaggle.game_nba_kaggle(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE kaggle.officials_nba_kaggle IS 'Game officials (referees) for each game. Useful for referee bias analysis.';

-- Indexes
CREATE INDEX idx_kaggle_officials_game_id ON kaggle.officials_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_officials_official_id ON kaggle.officials_nba_kaggle(official_id);
CREATE INDEX idx_kaggle_officials_name ON kaggle.officials_nba_kaggle(last_name, first_name);
CREATE INDEX idx_kaggle_officials_data_gin ON kaggle.officials_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 11: kaggle.other_stats_nba_kaggle
-- Purpose: Additional statistics (~28,000 records)
-- Source: SQLite table 'other_stats'
-- Expected rows: 28,000
-- Priority: MEDIUM
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.other_stats_nba_kaggle (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    league_id VARCHAR(10),
    team_id INTEGER,
    team_abbreviation VARCHAR(5),
    team_city VARCHAR(50),
    pts_paint INTEGER,
    pts_2nd_chance INTEGER,
    pts_fb INTEGER,             -- Fast break points
    largest_lead INTEGER,
    lead_changes INTEGER,
    times_tied INTEGER,
    team_turnovers INTEGER,
    total_turnovers INTEGER,
    team_rebounds INTEGER,
    pts_off_to INTEGER,         -- Points off turnovers

    -- Full other stats data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES kaggle.game_nba_kaggle(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE kaggle.other_stats_nba_kaggle IS 'Additional game statistics including points in paint, fast break points, and momentum metrics.';

-- Indexes
CREATE INDEX idx_kaggle_other_stats_game_id ON kaggle.other_stats_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_other_stats_team_id ON kaggle.other_stats_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_other_stats_data_gin ON kaggle.other_stats_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 12: kaggle.draft_history_nba_kaggle
-- Purpose: NBA draft picks (~8,200 records)
-- Source: SQLite table 'draft_history'
-- Expected rows: 8,200
-- Priority: LOW
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.draft_history_nba_kaggle (
    id SERIAL PRIMARY KEY,
    person_id INTEGER,
    player_name VARCHAR(100),
    season INTEGER,
    round_number INTEGER,
    round_pick INTEGER,
    overall_pick INTEGER,
    draft_type VARCHAR(50),
    team_id INTEGER,
    team_city VARCHAR(50),
    team_name VARCHAR(50),
    team_abbreviation VARCHAR(5),
    organization VARCHAR(100),
    organization_type VARCHAR(50),

    -- Full draft history data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.draft_history_nba_kaggle IS 'NBA draft history with pick details and team information.';

-- Indexes
CREATE INDEX idx_kaggle_draft_person_id ON kaggle.draft_history_nba_kaggle(person_id);
CREATE INDEX idx_kaggle_draft_season ON kaggle.draft_history_nba_kaggle(season);
CREATE INDEX idx_kaggle_draft_overall_pick ON kaggle.draft_history_nba_kaggle(overall_pick);
CREATE INDEX idx_kaggle_draft_team_id ON kaggle.draft_history_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_draft_data_gin ON kaggle.draft_history_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 13: kaggle.draft_combine_stats_nba_kaggle
-- Purpose: NBA draft combine measurements (~1,600 records)
-- Source: SQLite table 'draft_combine_stats'
-- Expected rows: 1,600
-- Priority: LOW
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.draft_combine_stats_nba_kaggle (
    id SERIAL PRIMARY KEY,
    season INTEGER,
    player_id INTEGER,
    player_name VARCHAR(100),
    position VARCHAR(20),
    height_wo_shoes DOUBLE PRECISION,
    height_w_shoes DOUBLE PRECISION,
    weight DOUBLE PRECISION,
    wingspan DOUBLE PRECISION,
    standing_reach DOUBLE PRECISION,
    body_fat_pct DOUBLE PRECISION,
    hand_length DOUBLE PRECISION,
    hand_width DOUBLE PRECISION,
    standing_vertical_leap DOUBLE PRECISION,
    max_vertical_leap DOUBLE PRECISION,
    lane_agility_time DOUBLE PRECISION,
    modified_lane_agility_time DOUBLE PRECISION,
    three_quarter_sprint DOUBLE PRECISION,
    bench_press INTEGER,

    -- Full combine stats data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.draft_combine_stats_nba_kaggle IS 'NBA draft combine physical measurements and athletic testing results.';

-- Indexes
CREATE INDEX idx_kaggle_combine_player_id ON kaggle.draft_combine_stats_nba_kaggle(player_id);
CREATE INDEX idx_kaggle_combine_season ON kaggle.draft_combine_stats_nba_kaggle(season);
CREATE INDEX idx_kaggle_combine_data_gin ON kaggle.draft_combine_stats_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 14: kaggle.team_details_nba_kaggle
-- Purpose: Extended team details (~27 records)
-- Source: SQLite table 'team_details'
-- Expected rows: 27
-- Priority: LOW
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.team_details_nba_kaggle (
    id SERIAL PRIMARY KEY,
    team_id INTEGER UNIQUE NOT NULL,
    abbreviation VARCHAR(5),
    nickname VARCHAR(50),
    yearfounded INTEGER,
    city VARCHAR(50),
    arena VARCHAR(100),
    arenacapacity INTEGER,
    owner VARCHAR(100),
    generalmanager VARCHAR(100),
    headcoach VARCHAR(100),
    dleagueaffiliation VARCHAR(100),

    -- Full team details data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.team_details_nba_kaggle IS 'Extended team information including arena, ownership, and management details.';

-- Indexes
CREATE INDEX idx_kaggle_team_details_id ON kaggle.team_details_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_team_details_abbrev ON kaggle.team_details_nba_kaggle(abbreviation);
CREATE INDEX idx_kaggle_team_details_data_gin ON kaggle.team_details_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 15: kaggle.team_history_nba_kaggle
-- Purpose: Team franchise history (~50 records)
-- Source: SQLite table 'team_history'
-- Expected rows: 50
-- Priority: LOW
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.team_history_nba_kaggle (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    city VARCHAR(50),
    nickname VARCHAR(50),
    yearfounded INTEGER,
    yearactivetill INTEGER,

    -- Full team history data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.team_history_nba_kaggle IS 'Historical team information including franchise relocations and rebranding.';

-- Indexes
CREATE INDEX idx_kaggle_team_history_team_id ON kaggle.team_history_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_team_history_yearfounded ON kaggle.team_history_nba_kaggle(yearfounded);
CREATE INDEX idx_kaggle_team_history_data_gin ON kaggle.team_history_nba_kaggle USING GIN(data);

-- =============================================================================
-- TABLE 16: kaggle.team_info_common_nba_kaggle
-- Purpose: Common team information (~0 records - known empty)
-- Source: SQLite table 'team_info_common'
-- Expected rows: 0
-- Priority: LOW
-- =============================================================================

CREATE TABLE IF NOT EXISTS kaggle.team_info_common_nba_kaggle (
    id SERIAL PRIMARY KEY,
    team_id INTEGER,
    season_year VARCHAR(20),
    team_city VARCHAR(50),
    team_name VARCHAR(50),
    team_abbreviation VARCHAR(5),
    team_conference VARCHAR(20),
    team_division VARCHAR(20),
    team_code VARCHAR(20),
    w INTEGER,
    l INTEGER,
    pct DOUBLE PRECISION,
    conf_rank INTEGER,
    div_rank INTEGER,

    -- Full team info data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.team_info_common_nba_kaggle IS 'Common team information table. Known to be empty in source SQLite database.';

-- Indexes
CREATE INDEX idx_kaggle_team_info_team_id ON kaggle.team_info_common_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_team_info_season ON kaggle.team_info_common_nba_kaggle(season_year);
CREATE INDEX idx_kaggle_team_info_data_gin ON kaggle.team_info_common_nba_kaggle USING GIN(data);

-- =============================================================================
-- SCHEMA VERSION TRACKING
-- =============================================================================

-- Update schema version table if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'raw_data' AND table_name = 'schema_version') THEN
        INSERT INTO raw_data.schema_version (version, description, applied_at)
        VALUES ('0.20', 'Create Kaggle schema with 16 tables for historical NBA data (1946-2023)', NOW())
        ON CONFLICT (version) DO NOTHING;
    END IF;
END $$;

-- =============================================================================
-- GRANTS (permissions for user ryanranft)
-- =============================================================================

-- Grant usage on schema to current user (ryanranft)
GRANT USAGE ON SCHEMA kaggle TO ryanranft;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA kaggle TO ryanranft;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA kaggle TO ryanranft;

-- =============================================================================
-- SUMMARY
-- =============================================================================

-- Print summary of created objects
DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count FROM information_schema.tables WHERE table_schema = 'kaggle';
    SELECT COUNT(*) INTO index_count FROM pg_indexes WHERE schemaname = 'kaggle';

    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Kaggle Schema Migration 0.20 - COMPLETE';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Schema: kaggle';
    RAISE NOTICE 'Tables created: %', table_count;
    RAISE NOTICE 'Indexes created: %', index_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Tables (priority order):';
    RAISE NOTICE '  CRITICAL:';
    RAISE NOTICE '    - kaggle.game_nba_kaggle (expected: 65,698 rows)';
    RAISE NOTICE '    - kaggle.play_by_play_nba_kaggle (expected: 13,592,899 rows)';
    RAISE NOTICE '  HIGH:';
    RAISE NOTICE '    - kaggle.player_nba_kaggle (expected: 4,800 rows)';
    RAISE NOTICE '    - kaggle.team_nba_kaggle (expected: 30 rows)';
    RAISE NOTICE '    - kaggle.common_player_info_nba_kaggle (expected: 3,600 rows)';
    RAISE NOTICE '  MEDIUM:';
    RAISE NOTICE '    - kaggle.game_info_nba_kaggle (expected: 58,000 rows)';
    RAISE NOTICE '    - kaggle.game_summary_nba_kaggle (expected: 58,000 rows)';
    RAISE NOTICE '    - kaggle.line_score_nba_kaggle (expected: 58,000 rows)';
    RAISE NOTICE '    - kaggle.inactive_players_nba_kaggle (expected: 110,000 rows)';
    RAISE NOTICE '    - kaggle.officials_nba_kaggle (expected: 71,000 rows)';
    RAISE NOTICE '    - kaggle.other_stats_nba_kaggle (expected: 28,000 rows)';
    RAISE NOTICE '  LOW:';
    RAISE NOTICE '    - kaggle.draft_history_nba_kaggle (expected: 8,200 rows)';
    RAISE NOTICE '    - kaggle.draft_combine_stats_nba_kaggle (expected: 1,600 rows)';
    RAISE NOTICE '    - kaggle.team_details_nba_kaggle (expected: 27 rows)';
    RAISE NOTICE '    - kaggle.team_history_nba_kaggle (expected: 50 rows)';
    RAISE NOTICE '    - kaggle.team_info_common_nba_kaggle (expected: 0 rows - empty)';
    RAISE NOTICE '';
    RAISE NOTICE 'Total expected rows: ~14,117,904';
    RAISE NOTICE 'Temporal coverage: 1946-2023 (77 seasons)';
    RAISE NOTICE '';
    RAISE NOTICE 'Next step: Run 0_21_kaggle_data_migration.py to migrate data from SQLite';
    RAISE NOTICE '=================================================================';
END $$;

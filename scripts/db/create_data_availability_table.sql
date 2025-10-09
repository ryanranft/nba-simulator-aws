-- Data Availability Table
-- Tracks what data is available for each NBA season across different eras
-- Part of Progressive Fidelity Simulation System

CREATE TABLE IF NOT EXISTS data_availability (
    season VARCHAR(10) PRIMARY KEY,  -- e.g., "2023-24"
    start_year INTEGER NOT NULL,     -- e.g., 2023
    end_year INTEGER NOT NULL,       -- e.g., 2024

    -- Era classification
    era VARCHAR(50) NOT NULL,        -- "early_era", "box_score_era", "pbp_era"
    fidelity_level VARCHAR(50) NOT NULL,  -- "minimal", "enhanced", "detailed"

    -- Data availability flags
    has_games BOOLEAN DEFAULT FALSE,
    has_box_scores BOOLEAN DEFAULT FALSE,
    has_play_by_play BOOLEAN DEFAULT FALSE,
    has_advanced_stats BOOLEAN DEFAULT FALSE,
    has_tracking_data BOOLEAN DEFAULT FALSE,
    has_shot_chart BOOLEAN DEFAULT FALSE,

    -- Counts
    game_count INTEGER DEFAULT 0,
    box_score_count INTEGER DEFAULT 0,
    pbp_event_count INTEGER DEFAULT 0,

    -- Completeness metrics (0.0 to 1.0)
    game_completeness DECIMAL(5,4) DEFAULT 0.0,       -- % of expected games
    box_score_completeness DECIMAL(5,4) DEFAULT 0.0,  -- % of games with box scores
    pbp_completeness DECIMAL(5,4) DEFAULT 0.0,        -- % of games with PBP

    -- Quality indicators
    data_quality_score DECIMAL(5,4) DEFAULT 0.0,  -- Overall quality (0-1)
    has_quality_issues BOOLEAN DEFAULT FALSE,
    quality_notes TEXT,

    -- Metadata
    last_assessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (start_year >= 1946 AND start_year <= 2100),
    CHECK (end_year >= 1946 AND end_year <= 2100),
    CHECK (end_year >= start_year),
    CHECK (game_completeness >= 0.0 AND game_completeness <= 1.0),
    CHECK (box_score_completeness >= 0.0 AND box_score_completeness <= 1.0),
    CHECK (pbp_completeness >= 0.0 AND pbp_completeness <= 1.0),
    CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_data_avail_era ON data_availability(era);
CREATE INDEX IF NOT EXISTS idx_data_avail_start_year ON data_availability(start_year);
CREATE INDEX IF NOT EXISTS idx_data_avail_fidelity ON data_availability(fidelity_level);
CREATE INDEX IF NOT EXISTS idx_data_avail_has_pbp ON data_availability(has_play_by_play);

-- Add comment
COMMENT ON TABLE data_availability IS 'Tracks data availability and quality across NBA seasons for Progressive Fidelity Simulation System';

-- Function to determine era based on season
CREATE OR REPLACE FUNCTION get_era_for_season(year INTEGER)
RETURNS VARCHAR(50) AS $$
BEGIN
    CASE
        WHEN year >= 1946 AND year < 1960 THEN RETURN 'early_era';
        WHEN year >= 1960 AND year < 1990 THEN RETURN 'box_score_era';
        WHEN year >= 1990 THEN RETURN 'pbp_era';
        ELSE RETURN 'unknown';
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Function to determine fidelity level based on era
CREATE OR REPLACE FUNCTION get_fidelity_level(era_name VARCHAR(50))
RETURNS VARCHAR(50) AS $$
BEGIN
    CASE era_name
        WHEN 'early_era' THEN RETURN 'minimal';
        WHEN 'box_score_era' THEN RETURN 'enhanced';
        WHEN 'pbp_era' THEN RETURN 'detailed';
        ELSE RETURN 'unknown';
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate data quality score
CREATE OR REPLACE FUNCTION calculate_quality_score(
    game_comp DECIMAL,
    bs_comp DECIMAL,
    pbp_comp DECIMAL,
    era_name VARCHAR(50)
)
RETURNS DECIMAL AS $$
DECLARE
    score DECIMAL;
BEGIN
    -- Weight different metrics based on era
    CASE era_name
        WHEN 'early_era' THEN
            -- Early era: focus on games and box scores
            score := (game_comp * 0.6) + (bs_comp * 0.4);
        WHEN 'box_score_era' THEN
            -- Box score era: balanced
            score := (game_comp * 0.4) + (bs_comp * 0.6);
        WHEN 'pbp_era' THEN
            -- PBP era: all three important
            score := (game_comp * 0.3) + (bs_comp * 0.3) + (pbp_comp * 0.4);
        ELSE
            score := 0.0;
    END CASE;

    RETURN GREATEST(0.0, LEAST(1.0, score));
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update last_updated timestamp
CREATE OR REPLACE FUNCTION update_data_availability_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_data_availability_timestamp
BEFORE UPDATE ON data_availability
FOR EACH ROW
EXECUTE FUNCTION update_data_availability_timestamp();

-- Sample data insertion for demonstration
-- This will be replaced by actual data from assess_data.py
INSERT INTO data_availability (season, start_year, end_year, era, fidelity_level, has_games, has_box_scores)
VALUES
    ('1946-47', 1946, 1947, 'early_era', 'minimal', TRUE, TRUE),
    ('1980-81', 1980, 1981, 'box_score_era', 'enhanced', TRUE, TRUE),
    ('2023-24', 2023, 2024, 'pbp_era', 'detailed', TRUE, TRUE)
ON CONFLICT (season) DO NOTHING;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON data_availability TO nba_app_user;

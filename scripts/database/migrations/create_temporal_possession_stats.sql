-- =============================================================================
-- Phase 0.0005: Possession Extraction - Database Schema
-- =============================================================================
-- Creates the temporal_possession_stats table to store basketball possessions
-- extracted from the temporal_events table (14.1M events → 2-3M possessions)
--
-- Methodology: Dean Oliver's "Basketball on Paper" possession definitions
-- Performance Target: <1 second per game extraction, <15 minutes per season
-- Validation: Within 5% of Dean Oliver's expected possession counts
--
-- Created: November 5, 2025
-- Author: NBA Simulator AWS Team
-- =============================================================================

-- Drop existing table if needed (careful in production!)
-- DROP TABLE IF EXISTS temporal_possession_stats CASCADE;

-- =============================================================================
-- Main Table: temporal_possession_stats
-- =============================================================================

CREATE TABLE IF NOT EXISTS temporal_possession_stats (
    -- Primary Key
    possession_id SERIAL PRIMARY KEY,
    
    -- Game Identification
    game_id VARCHAR(50) NOT NULL,
    season INTEGER NOT NULL,
    game_date DATE NOT NULL,
    
    -- Possession Identification
    possession_number INTEGER NOT NULL,  -- Sequential within game (1, 2, 3, ...)
    period INTEGER NOT NULL,             -- 1-4 for regulation, 5+ for OT
    
    -- Team Attribution
    offensive_team_id INTEGER NOT NULL,
    defensive_team_id INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    
    -- Temporal Context (Game Clock)
    start_clock_minutes INTEGER,         -- Minutes remaining at possession start
    start_clock_seconds NUMERIC(4,1),    -- Seconds remaining (e.g., 45.3)
    end_clock_minutes INTEGER,           -- Minutes remaining at possession end
    end_clock_seconds NUMERIC(4,1),      -- Seconds remaining
    duration_seconds NUMERIC(5,2),       -- Total possession duration (0.5-35s typical)
    
    -- Score Context
    score_differential_start INTEGER,    -- From offensive team perspective (+/-)
    home_score_start INTEGER,
    away_score_start INTEGER,
    home_score_end INTEGER,
    away_score_end INTEGER,
    
    -- Possession Outcome
    points_scored INTEGER DEFAULT 0,     -- Points scored during this possession
    possession_result VARCHAR(50),       -- 'made_shot', 'missed_shot', 'turnover', 'foul', 'end_period'
    
    -- Shot Quality & Attempts
    field_goals_attempted INTEGER DEFAULT 0,
    field_goals_made INTEGER DEFAULT 0,
    three_pointers_attempted INTEGER DEFAULT 0,
    three_pointers_made INTEGER DEFAULT 0,
    free_throws_attempted INTEGER DEFAULT 0,
    free_throws_made INTEGER DEFAULT 0,
    
    -- Efficiency Metrics
    points_per_possession NUMERIC(5,3),  -- PPP (e.g., 1.120 PPP)
    effective_field_goal_pct NUMERIC(5,3), -- eFG% = (FGM + 0.5*3PM) / FGA
    
    -- Event References
    start_event_id BIGINT,               -- FK to temporal_events.event_id
    end_event_id BIGINT,                 -- FK to temporal_events.event_id
    event_count INTEGER,                 -- Number of events in this possession
    
    -- Context Flags
    is_clutch_time BOOLEAN DEFAULT FALSE,    -- Last 5 min of 4th/OT, score within 5
    is_garbage_time BOOLEAN DEFAULT FALSE,   -- >20 point differential, <5 min remaining
    is_fastbreak BOOLEAN DEFAULT FALSE,      -- Possession < 8 seconds
    has_timeout BOOLEAN DEFAULT FALSE,       -- Timeout called during possession
    
    -- Data Quality & Validation
    validation_status VARCHAR(20) DEFAULT 'valid',  -- 'valid', 'warning', 'invalid'
    validation_notes TEXT,                          -- Notes on any validation issues
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_game_possession UNIQUE(game_id, possession_number),
    CONSTRAINT valid_period CHECK (period >= 1 AND period <= 10),  -- Max 6 OT periods
    CONSTRAINT valid_duration CHECK (duration_seconds >= 0 AND duration_seconds <= 50),
    CONSTRAINT valid_points CHECK (points_scored >= 0 AND points_scored <= 10),  -- Max 10 pts in possession
    CONSTRAINT valid_validation_status CHECK (validation_status IN ('valid', 'warning', 'invalid'))
);

-- =============================================================================
-- Indexes for Performance
-- =============================================================================

-- Core query patterns
CREATE INDEX IF NOT EXISTS idx_possession_game 
    ON temporal_possession_stats(game_id);

CREATE INDEX IF NOT EXISTS idx_possession_season 
    ON temporal_possession_stats(season);

CREATE INDEX IF NOT EXISTS idx_possession_date 
    ON temporal_possession_stats(game_date);

-- Team-based queries
CREATE INDEX IF NOT EXISTS idx_possession_offensive_team 
    ON temporal_possession_stats(offensive_team_id, season);

CREATE INDEX IF NOT EXISTS idx_possession_defensive_team 
    ON temporal_possession_stats(defensive_team_id, season);

-- Context-based queries
CREATE INDEX IF NOT EXISTS idx_possession_clutch 
    ON temporal_possession_stats(is_clutch_time) 
    WHERE is_clutch_time = TRUE;

CREATE INDEX IF NOT EXISTS idx_possession_fastbreak 
    ON temporal_possession_stats(is_fastbreak) 
    WHERE is_fastbreak = TRUE;

-- Validation queries
CREATE INDEX IF NOT EXISTS idx_possession_validation 
    ON temporal_possession_stats(validation_status);

-- Event reference lookups
CREATE INDEX IF NOT EXISTS idx_possession_events 
    ON temporal_possession_stats(start_event_id, end_event_id);

-- Composite index for common queries (team + season + validation)
CREATE INDEX IF NOT EXISTS idx_possession_team_season_valid 
    ON temporal_possession_stats(offensive_team_id, season, validation_status);

-- =============================================================================
-- Foreign Key Constraints (Optional - add after data validation)
-- =============================================================================
-- Note: These are commented out initially. Uncomment after confirming
--       data integrity and that all event_id references exist.

-- ALTER TABLE temporal_possession_stats 
--     ADD CONSTRAINT fk_possession_start_event 
--     FOREIGN KEY (start_event_id) 
--     REFERENCES temporal_events(event_id);

-- ALTER TABLE temporal_possession_stats 
--     ADD CONSTRAINT fk_possession_end_event 
--     FOREIGN KEY (end_event_id) 
--     REFERENCES temporal_events(event_id);

-- =============================================================================
-- Table Statistics & Comments
-- =============================================================================

COMMENT ON TABLE temporal_possession_stats IS 
    'Basketball possessions extracted from temporal_events table. ' ||
    'Each row represents one possession (offensive team controls ball until shot/turnover/foul). ' ||
    'Validated against Dean Oliver expected possession formula: FGA + 0.44*FTA - ORB + TOV';

COMMENT ON COLUMN temporal_possession_stats.possession_number IS 
    'Sequential possession number within game (1, 2, 3, ...). Unique per game_id.';

COMMENT ON COLUMN temporal_possession_stats.duration_seconds IS 
    'Elapsed time of possession in seconds. Typical range: 0.5-35 seconds. ' ||
    'Average NBA possession: ~14 seconds.';

COMMENT ON COLUMN temporal_possession_stats.points_per_possession IS 
    'Efficiency metric: points_scored / 1.0. ' ||
    'League average ~1.10 PPP. Elite offenses >1.15 PPP.';

COMMENT ON COLUMN temporal_possession_stats.is_clutch_time IS 
    'Last 5 minutes of 4th quarter or OT with score within 5 points';

COMMENT ON COLUMN temporal_possession_stats.is_fastbreak IS 
    'Possession completed in <8 seconds (fastbreak pace)';

COMMENT ON COLUMN temporal_possession_stats.validation_status IS 
    'Data quality status: valid (passes all checks), warning (minor issues), invalid (failed validation)';

-- =============================================================================
-- Vacuum and Analyze for Optimization
-- =============================================================================

-- Run after initial data load
-- VACUUM ANALYZE temporal_possession_stats;

-- =============================================================================
-- Storage Estimates
-- =============================================================================
-- Row Size: ~250 bytes per possession
-- Expected Rows: 2-3 million possessions (66,000 games × 30-45 possessions/game)
-- Data Size: ~500-750 MB
-- Index Size: ~500 MB
-- Total Size: ~1-1.5 GB
-- =============================================================================

-- End of migration script

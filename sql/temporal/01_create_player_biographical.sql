-- ============================================================================
-- Player Biographical Table
-- ============================================================================
--
-- Purpose: Store player birth dates for precise age calculations at any timestamp
-- Capacity: 5,000+ rows (one per player)
-- Storage: < 1 GB
-- Use case: "How old was Kobe when he scored his 30,000th point?"
--
-- Example query: "Calculate player age at exactly 7:02:34 PM on June 19, 2016"
-- ============================================================================

CREATE TABLE IF NOT EXISTS player_biographical (
    -- Primary Key
    player_id VARCHAR(20) PRIMARY KEY,

    -- Birth Information
    birth_date DATE,                                    -- Birth date (YYYY-MM-DD)
    birth_date_precision VARCHAR(10),                   -- 'day', 'month', 'year', 'unknown'
    birth_city VARCHAR(100),
    birth_state VARCHAR(100),
    birth_country VARCHAR(100),

    -- Physical Attributes
    height_inches INTEGER,                              -- Height in inches
    weight_pounds INTEGER,                              -- Weight in pounds
    wingspan_inches INTEGER,                            -- Wingspan in inches (if available)

    -- Career Timeline
    nba_debut_date DATE,                                -- First NBA game date
    nba_retirement_date DATE,                           -- Last NBA game date (NULL if active)
    draft_year INTEGER,
    draft_round INTEGER,
    draft_pick INTEGER,
    draft_team_id INTEGER,

    -- College/High School
    college VARCHAR(100),                               -- College attended (or "None" if from high school)
    high_school VARCHAR(100),

    -- Additional Info
    nationality VARCHAR(50),
    position VARCHAR(20),                               -- Primary position: PG, SG, SF, PF, C
    jersey_number INTEGER,

    -- Metadata
    data_source VARCHAR(50),                            -- Where we got this data: 'nba_stats', 'basketball_ref', 'espn'
    created_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    -- Note: No FK to players table - biographical data can exist independently
    -- Players table is for current roster, biographical is for historical data
    CONSTRAINT chk_birth_date_precision CHECK (birth_date_precision IN ('day', 'month', 'year', 'unknown')),
    CONSTRAINT chk_height CHECK (height_inches IS NULL OR (height_inches BETWEEN 60 AND 96)),  -- 5'0" to 8'0"
    CONSTRAINT chk_weight CHECK (weight_pounds IS NULL OR (weight_pounds BETWEEN 100 AND 400))
);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE player_biographical IS 'Player biographical data for age calculations and context. Birth dates enable precise age calculation at any timestamp.';

COMMENT ON COLUMN player_biographical.player_id IS 'Foreign key to players table (primary key)';
COMMENT ON COLUMN player_biographical.birth_date IS 'Player birth date. Used with calculate_player_age() function for temporal age queries.';
COMMENT ON COLUMN player_biographical.birth_date_precision IS 'Precision of birth date: day (YYYY-MM-DD known), month (YYYY-MM known), year (YYYY only), unknown (no data)';
COMMENT ON COLUMN player_biographical.nba_debut_date IS 'Date of first NBA game. Used to calculate years of experience at any timestamp.';
COMMENT ON COLUMN player_biographical.nba_retirement_date IS 'Date of last NBA game. NULL if player is still active.';
COMMENT ON COLUMN player_biographical.college IS 'College attended. "None" if player entered NBA from high school.';
COMMENT ON COLUMN player_biographical.data_source IS 'Source of biographical data: nba_stats (official), basketball_ref (comprehensive), espn (current players)';

-- ============================================================================
-- Indexes (Created separately in 02_create_indexes.sql)
-- ============================================================================
--
-- B-tree index on birth_date (for age range queries)
-- B-tree index on nba_debut_date (for experience calculations)
--
-- See: sql/temporal/02_create_indexes.sql
-- ============================================================================

-- ============================================================================
-- Triggers (Auto-Update Metadata)
-- ============================================================================

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_player_biographical_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_player_biographical_updated_at
    BEFORE UPDATE ON player_biographical
    FOR EACH ROW
    EXECUTE FUNCTION update_player_biographical_timestamp();

-- ============================================================================
-- Usage Examples
-- ============================================================================
--
-- Example 1: Calculate player age at exact timestamp (using stored procedure)
-- SELECT calculate_player_age(977, '2016-06-19 19:02:34'::TIMESTAMPTZ);
-- Output: "37 years, 297 days, 5 hours, 2 minutes, 34 seconds"
--
-- Example 2: Get all biographical data for a player
-- SELECT * FROM player_biographical WHERE player_id = 977;
--
-- Example 3: Find players born in specific year
-- SELECT p.name, pb.birth_date, pb.birth_city
-- FROM players p
-- JOIN player_biographical pb ON p.player_id = pb.player_id
-- WHERE EXTRACT(YEAR FROM pb.birth_date) = 1978;
--
-- Example 4: Calculate age at NBA debut
-- SELECT
--     p.name,
--     pb.nba_debut_date,
--     EXTRACT(YEAR FROM AGE(pb.nba_debut_date, pb.birth_date)) AS age_at_debut
-- FROM players p
-- JOIN player_biographical pb ON p.player_id = pb.player_id
-- WHERE pb.birth_date IS NOT NULL
--   AND pb.nba_debut_date IS NOT NULL
-- ORDER BY age_at_debut;
--
-- Example 5: Get birth date precision distribution
-- SELECT birth_date_precision, COUNT(*) AS player_count
-- FROM player_biographical
-- GROUP BY birth_date_precision
-- ORDER BY player_count DESC;
--
-- Example 6: Find players with unknown birth dates (need to collect)
-- SELECT p.name, p.player_id
-- FROM players p
-- LEFT JOIN player_biographical pb ON p.player_id = pb.player_id
-- WHERE pb.birth_date IS NULL
--   AND p.active = true;
--
-- ============================================================================

-- ============================================================================
-- Birth Date Precision Strategy
-- ============================================================================
--
-- Data quality varies by era and source:
--
-- Modern players (2000+):
-- - Source: NBA.com Stats API
-- - Precision: 'day' (YYYY-MM-DD)
-- - Completeness: 95%+
-- - Age accuracy: ±1 day
--
-- 1980-1999 players:
-- - Source: Basketball Reference
-- - Precision: 'day' (YYYY-MM-DD)
-- - Completeness: 90%+
-- - Age accuracy: ±1 day
--
-- 1960-1979 players:
-- - Source: Basketball Reference
-- - Precision: 'month' or 'year' (YYYY-MM or YYYY)
-- - Completeness: 70%+
-- - Age accuracy: ±15 days (month), ±6 months (year)
--
-- Pre-1960 players:
-- - Source: Basketball Reference, Wikipedia
-- - Precision: 'year' or 'unknown' (YYYY or NULL)
-- - Completeness: 50%+
-- - Age accuracy: ±6 months or unknown
--
-- Strategy:
-- 1. Collect from NBA.com Stats API first (most reliable for modern)
-- 2. Fill gaps with Basketball Reference (comprehensive historical)
-- 3. Use ESPN for active players not in other sources
-- 4. Flag precision level for transparency
--
-- See: scripts/etl/collect_player_birth_dates.py
-- ============================================================================

-- ============================================================================
-- Validation Queries
-- ============================================================================
--
-- After collecting birth dates, run these queries to validate:
--
-- 1. Check completeness by era
-- SELECT
--     CASE
--         WHEN EXTRACT(YEAR FROM birth_date) >= 2000 THEN '2000+'
--         WHEN EXTRACT(YEAR FROM birth_date) >= 1980 THEN '1980-1999'
--         WHEN EXTRACT(YEAR FROM birth_date) >= 1960 THEN '1960-1979'
--         ELSE 'Pre-1960'
--     END AS era,
--     COUNT(*) AS players,
--     COUNT(birth_date) AS with_birth_date,
--     ROUND(100.0 * COUNT(birth_date) / COUNT(*), 1) AS completeness_pct
-- FROM player_biographical pb
-- JOIN players p ON pb.player_id = p.player_id
-- GROUP BY era
-- ORDER BY era DESC;
--
-- 2. Check precision distribution
-- SELECT
--     birth_date_precision,
--     COUNT(*) AS players,
--     ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
-- FROM player_biographical
-- GROUP BY birth_date_precision
-- ORDER BY players DESC;
-- Expected: 90%+ with 'day' precision for modern players
--
-- 3. Identify outliers (suspicious ages)
-- SELECT p.name, pb.birth_date,
--        EXTRACT(YEAR FROM AGE(CURRENT_DATE, pb.birth_date)) AS current_age
-- FROM players p
-- JOIN player_biographical pb ON p.player_id = pb.player_id
-- WHERE EXTRACT(YEAR FROM AGE(CURRENT_DATE, pb.birth_date)) < 18
--    OR EXTRACT(YEAR FROM AGE(CURRENT_DATE, pb.birth_date)) > 80;
-- Expected: 0 rows (NBA players typically 18-45 years old, retired up to 80)
--
-- 4. Check data source distribution
-- SELECT data_source, COUNT(*) AS players
-- FROM player_biographical
-- GROUP BY data_source
-- ORDER BY players DESC;
--
-- 5. Check table size
-- SELECT pg_size_pretty(pg_total_relation_size('player_biographical'));
-- Expected: < 1 GB (small reference table)
--
-- ============================================================================

-- Migration: 0.19 - Migrate Existing ESPN Data to ESPN Schema
-- Created: November 7, 2025
-- Purpose: Copy existing ESPN game data from raw_data.nba_games → espn.espn_games
-- Prerequisite: 0_18_espn_schema.sql must be run first
-- Status: Production Ready

-- =============================================================================
-- VALIDATION: Check prerequisites
-- =============================================================================

DO $$
BEGIN
    -- Check if espn schema exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'espn') THEN
        RAISE EXCEPTION 'ESPN schema does not exist. Run 0_18_espn_schema.sql first.';
    END IF;

    -- Check if espn.espn_games table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'espn' AND table_name = 'espn_games') THEN
        RAISE EXCEPTION 'espn.espn_games table does not exist. Run 0_18_espn_schema.sql first.';
    END IF;

    -- Check if source table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'raw_data' AND table_name = 'nba_games') THEN
        RAISE EXCEPTION 'Source table raw_data.nba_games does not exist.';
    END IF;

    RAISE NOTICE 'Prerequisites validated successfully.';
END $$;

-- =============================================================================
-- MIGRATION: Copy ESPN data from raw_data.nba_games → espn.espn_games
-- =============================================================================

DO $$
DECLARE
    rows_migrated INTEGER := 0;
    rows_total INTEGER := 0;
BEGIN
    -- Count total ESPN records in source
    SELECT COUNT(*) INTO rows_total
    FROM raw_data.nba_games
    WHERE source = 'ESPN' OR data->'metadata'->>'source' = 'ESPN';

    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'ESPN Data Migration - Starting';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'Source table: raw_data.nba_games';
    RAISE NOTICE 'Target table: espn.espn_games';
    RAISE NOTICE 'ESPN records found in source: %', rows_total;
    RAISE NOTICE '';

    -- Migrate data with UPSERT logic
    INSERT INTO espn.espn_games (
        game_id,
        season,
        season_type,
        game_date,
        home_team,
        away_team,
        home_score,
        away_score,
        data,
        metadata,
        collected_at
    )
    SELECT
        game_id,
        -- Extract season from JSONB (try multiple paths for compatibility)
        COALESCE(
            (data->'game_info'->>'season_year')::INTEGER,
            (data->>'season')::INTEGER,
            season
        ) as season,
        -- Extract season_type (may be NULL for old records)
        (data->'game_info'->>'season_type')::INTEGER as season_type,
        -- Extract game_date
        COALESCE(
            (data->'game_info'->>'game_date')::TIMESTAMP WITH TIME ZONE,
            (data->>'game_date')::TIMESTAMP WITH TIME ZONE
        ) as game_date,
        -- Extract team names
        COALESCE(
            data->'teams'->'home'->>'name',
            data->'home_team'->>'name'
        ) as home_team,
        COALESCE(
            data->'teams'->'away'->>'name',
            data->'away_team'->>'name'
        ) as away_team,
        -- Extract scores
        COALESCE(
            (data->'teams'->'home'->'score'->>'final')::INTEGER,
            (data->'home_team'->>'score')::INTEGER
        ) as home_score,
        COALESCE(
            (data->'teams'->'away'->'score'->>'final')::INTEGER,
            (data->'away_team'->>'score')::INTEGER
        ) as away_score,
        -- Full data and metadata
        data,
        metadata,
        collected_at
    FROM raw_data.nba_games
    WHERE source = 'ESPN' OR data->'metadata'->>'source' = 'ESPN'
    ON CONFLICT (game_id) DO UPDATE SET
        data = EXCLUDED.data,
        metadata = EXCLUDED.metadata,
        season_type = EXCLUDED.season_type,  -- Update seasonType if it was added
        home_team = EXCLUDED.home_team,
        away_team = EXCLUDED.away_team,
        home_score = EXCLUDED.home_score,
        away_score = EXCLUDED.away_score,
        updated_at = NOW();

    GET DIAGNOSTICS rows_migrated = ROW_COUNT;

    RAISE NOTICE '';
    RAISE NOTICE 'Migration Results:';
    RAISE NOTICE '  Records migrated/updated: %', rows_migrated;
    RAISE NOTICE '';

END $$;

-- =============================================================================
-- VERIFICATION: Check migration results
-- =============================================================================

DO $$
DECLARE
    espn_games_count INTEGER;
    with_season_type INTEGER;
    season_type_pct NUMERIC;
    min_season INTEGER;
    max_season INTEGER;
BEGIN
    -- Count records in target table
    SELECT COUNT(*) INTO espn_games_count FROM espn.espn_games;

    -- Count records with season_type
    SELECT COUNT(*) INTO with_season_type
    FROM espn.espn_games
    WHERE season_type IS NOT NULL;

    -- Calculate percentage
    IF espn_games_count > 0 THEN
        season_type_pct := ROUND(100.0 * with_season_type / espn_games_count, 2);
    ELSE
        season_type_pct := 0;
    END IF;

    -- Get season range
    SELECT MIN(season), MAX(season) INTO min_season, max_season
    FROM espn.espn_games;

    RAISE NOTICE 'Verification Results:';
    RAISE NOTICE '  Total games in espn.espn_games: %', espn_games_count;
    RAISE NOTICE '  Games with seasonType: % (%.2f%%)', with_season_type, season_type_pct;
    RAISE NOTICE '  Season range: % to %', min_season, max_season;
    RAISE NOTICE '';

    -- Check for NULL critical fields
    DECLARE
        null_game_id INTEGER;
        null_season INTEGER;
        null_data INTEGER;
    BEGIN
        SELECT
            COUNT(*) FILTER (WHERE game_id IS NULL),
            COUNT(*) FILTER (WHERE season IS NULL),
            COUNT(*) FILTER (WHERE data IS NULL OR data = '{}'::JSONB)
        INTO null_game_id, null_season, null_data
        FROM espn.espn_games;

        IF null_game_id > 0 OR null_season > 0 OR null_data > 0 THEN
            RAISE WARNING 'Data quality issues found:';
            IF null_game_id > 0 THEN
                RAISE WARNING '  % records with NULL game_id', null_game_id;
            END IF;
            IF null_season > 0 THEN
                RAISE WARNING '  % records with NULL season', null_season;
            END IF;
            IF null_data > 0 THEN
                RAISE WARNING '  % records with NULL/empty data JSONB', null_data;
            END IF;
        ELSE
            RAISE NOTICE 'Data quality check: PASS (no NULL critical fields)';
        END IF;
    END;

    RAISE NOTICE '';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE 'ESPN Data Migration - COMPLETE';
    RAISE NOTICE '=================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '  1. Load remaining games from local JSON files';
    RAISE NOTICE '  2. Verify seasonType coverage';
    RAISE NOTICE '  3. Load schedules, team stats, and PBP data';
    RAISE NOTICE '=================================================================';
END $$;

-- =============================================================================
-- OPTIONAL: Display seasonType distribution (if seasonType exists)
-- =============================================================================

DO $$
DECLARE
    has_season_type BOOLEAN;
BEGIN
    -- Check if any records have season_type
    SELECT EXISTS(SELECT 1 FROM espn.espn_games WHERE season_type IS NOT NULL) INTO has_season_type;

    IF has_season_type THEN
        RAISE NOTICE '';
        RAISE NOTICE 'seasonType Distribution:';
        RAISE NOTICE '-------------------------';

        -- This will show distribution if seasonType exists
        PERFORM 1;  -- Placeholder for dynamic SQL if needed
    END IF;
END $$;

-- Display seasonType distribution (runs separately)
SELECT
    season_type,
    CASE season_type
        WHEN 1 THEN 'Preseason'
        WHEN 2 THEN 'Regular Season'
        WHEN 3 THEN 'Playoffs'
        WHEN 5 THEN 'Play-In Tournament'
        ELSE 'Unknown'
    END as label,
    COUNT(*) as games,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM espn.espn_games
WHERE season_type IS NOT NULL
GROUP BY season_type
ORDER BY season_type;

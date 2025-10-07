-- ============================================================================
-- Master Script: Create All Temporal Tables
-- ============================================================================
--
-- Purpose: Execute all table creation scripts in correct order
-- Execution time: 2-5 minutes
-- Prerequisites: PostgreSQL 15.14+, existing players and games tables
--
-- Usage:
--   psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
--        -d nba_simulator \
--        -U your_user \
--        -f sql/temporal/00_master_create_tables.sql
--
-- Or from Python:
--   python scripts/db/create_temporal_tables.py
--
-- ============================================================================

\echo '========================================='
\echo 'Temporal Panel Data System - Table Creation'
\echo 'Started at:' `date`
\echo '========================================='
\echo ''

-- ============================================================================
-- Prerequisites Check
-- ============================================================================

\echo 'Step 1: Checking prerequisites...'

DO $$
DECLARE
    players_exists BOOLEAN;
    games_exists BOOLEAN;
BEGIN
    -- Check if players table exists
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = 'players'
    ) INTO players_exists;

    -- Check if games table exists
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = 'games'
    ) INTO games_exists;

    IF NOT players_exists THEN
        RAISE EXCEPTION 'ERROR: players table does not exist. Run Phase 3 table creation first.';
    END IF;

    IF NOT games_exists THEN
        RAISE EXCEPTION 'ERROR: games table does not exist. Run Phase 3 table creation first.';
    END IF;

    RAISE NOTICE 'Prerequisites check: OK';
    RAISE NOTICE '  - players table exists: %', players_exists;
    RAISE NOTICE '  - games table exists: %', games_exists;
END $$;

\echo 'Prerequisites check: PASSED'
\echo ''

-- ============================================================================
-- Table Creation
-- ============================================================================

\echo 'Step 2: Creating temporal tables...'
\echo ''

-- Table 1: temporal_events (500M+ rows capacity)
\echo '  Creating temporal_events table...'
\i sql/temporal/01_create_temporal_events.sql
\echo '  ✓ temporal_events created'
\echo ''

-- Table 2: player_snapshots (50M+ rows capacity)
\echo '  Creating player_snapshots table...'
\i sql/temporal/01_create_player_snapshots.sql
\echo '  ✓ player_snapshots created'
\echo ''

-- Table 3: game_states (10M+ rows capacity)
\echo '  Creating game_states table...'
\i sql/temporal/01_create_game_states.sql
\echo '  ✓ game_states created'
\echo ''

-- Table 4: player_biographical (5K+ rows capacity)
\echo '  Creating player_biographical table...'
\i sql/temporal/01_create_player_biographical.sql
\echo '  ✓ player_biographical created'
\echo ''

-- ============================================================================
-- Validation
-- ============================================================================

\echo 'Step 3: Validating table creation...'
\echo ''

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    -- Count temporal tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name IN ('temporal_events', 'player_snapshots', 'game_states', 'player_biographical');

    IF table_count != 4 THEN
        RAISE EXCEPTION 'ERROR: Expected 4 temporal tables, found %', table_count;
    END IF;

    RAISE NOTICE 'Table validation: OK';
    RAISE NOTICE '  - All 4 temporal tables created successfully';
END $$;

\echo 'Table validation: PASSED'
\echo ''

-- ============================================================================
-- Summary
-- ============================================================================

\echo '========================================='
\echo 'Summary: Temporal Tables'
\echo '========================================='
\echo ''

SELECT
    table_name,
    (xpath('/row/c/text()', query_to_xml(format('SELECT COUNT(*) AS c FROM %I', table_name), TRUE, TRUE, '')))[1]::text::int AS row_count,
    pg_size_pretty(pg_total_relation_size(table_name::regclass)) AS size
FROM information_schema.tables
WHERE table_name IN ('temporal_events', 'player_snapshots', 'game_states', 'player_biographical')
ORDER BY table_name;

\echo ''
\echo '========================================='
\echo 'Next Steps:'
\echo '========================================='
\echo '1. Create BRIN indexes:    sql/temporal/02_create_indexes.sql'
\echo '2. Create stored procedures: sql/temporal/03_create_stored_procedures.sql'
\echo '3. Collect birth dates:    python scripts/etl/collect_player_birth_dates.py'
\echo '4. Extract timestamps:     python scripts/etl/extract_wall_clock_timestamps.py'
\echo '========================================='
\echo ''
\echo 'Completed at:' `date`
\echo ''

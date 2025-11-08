-- ============================================================================
-- DDL Server - Database Schema Setup
-- ============================================================================
-- Creates tables for migration tracking, audit logging, and schema versioning
-- Run this once to initialize the DDL management system
--
-- Usage: psql -h HOST -U USER -d DATABASE -f ddl_schema_setup.sql
-- ============================================================================

-- ============================================================================
-- 1. MIGRATION HISTORY TABLE
-- ============================================================================
-- Tracks all schema migrations with version control and rollback capability

CREATE TABLE IF NOT EXISTS ddl_migration_history (
    migration_id SERIAL PRIMARY KEY,
    version_number BIGINT NOT NULL UNIQUE,  -- Format: YYYYMMDDHHMMSSn
    migration_name VARCHAR(255) NOT NULL,
    description TEXT,
    ddl_statement TEXT NOT NULL,
    object_type VARCHAR(50),  -- TABLE, VIEW, INDEX, COLUMN_ADD, COLUMN_MODIFY, etc.
    object_name VARCHAR(255),
    schema_name VARCHAR(255) DEFAULT 'public',
    status VARCHAR(20) NOT NULL DEFAULT 'CREATED',  -- CREATED, VALIDATED, STAGED, EXECUTING, SUCCESS, FAILED, ROLLBACK_REQUIRED, ROLLBACK_IN_PROGRESS, ROLLBACK_SUCCESS, ROLLBACK_FAILED
    executed_at TIMESTAMP,
    executed_by VARCHAR(255),
    execution_duration_ms INT,
    rollback_statement TEXT,
    rollback_executed_at TIMESTAMP,
    rollback_duration_ms INT,
    error_message TEXT,
    error_code VARCHAR(20),
    depends_on INT[],  -- Array of migration_ids this depends on
    blocks INT[],      -- Array of migration_ids this prevents from running
    breaking_changes JSONB,  -- {object_type, object_name, reason}[]
    validation_results JSONB,  -- Results from pre-execution validation
    metadata JSONB,  -- {dependencies, notes, tags, etc.}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for migration_history
CREATE INDEX IF NOT EXISTS idx_migration_version
    ON ddl_migration_history(version_number DESC);
CREATE INDEX IF NOT EXISTS idx_migration_status
    ON ddl_migration_history(status);
CREATE INDEX IF NOT EXISTS idx_migration_executed_at
    ON ddl_migration_history(executed_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_migration_object
    ON ddl_migration_history(schema_name, object_name);
CREATE INDEX IF NOT EXISTS idx_migration_created_at
    ON ddl_migration_history(created_at DESC);

-- Comments
COMMENT ON TABLE ddl_migration_history IS 'Tracks schema migrations with version control and rollback capability';
COMMENT ON COLUMN ddl_migration_history.version_number IS 'Timestamp-based version: YYYYMMDDHHMMSSn where n is sequential number for same-second migrations';
COMMENT ON COLUMN ddl_migration_history.depends_on IS 'Array of migration IDs that must be executed before this one';
COMMENT ON COLUMN ddl_migration_history.blocks IS 'Array of migration IDs that cannot run while this migration exists';
COMMENT ON COLUMN ddl_migration_history.breaking_changes IS 'List of objects that will break due to this migration';

-- ============================================================================
-- 2. DDL AUDIT LOG TABLE
-- ============================================================================
-- Immutable audit trail of all DDL executions for compliance

CREATE TABLE IF NOT EXISTS ddl_audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    execution_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    migration_id INT,  -- Reference to migration_history if part of migration
    operation_type VARCHAR(50) NOT NULL,  -- CREATE_TABLE, ALTER_TABLE, CREATE_INDEX, DROP_TABLE, etc.
    schema_name VARCHAR(255) DEFAULT 'public',
    object_name VARCHAR(255),
    ddl_statement TEXT NOT NULL,
    is_dry_run BOOLEAN NOT NULL DEFAULT true,
    validation_only BOOLEAN NOT NULL DEFAULT false,
    success BOOLEAN NOT NULL,
    error_code VARCHAR(20),
    error_message TEXT,
    execution_started TIMESTAMP NOT NULL DEFAULT NOW(),
    execution_completed TIMESTAMP,
    duration_ms INT,
    affected_rows INT,
    table_size_mb FLOAT,  -- Size of table being modified (if applicable)
    estimated_lock_time_ms INT,  -- Estimated time table will be locked
    executed_by VARCHAR(255),
    user_session_id VARCHAR(255),
    client_info JSONB,  -- {client: "Claude Desktop", mcp_server: "nba-ddl-server"}
    confirmation_token_used VARCHAR(128),  -- For DROP operations
    cascade_used BOOLEAN DEFAULT false,
    dependent_objects JSONB,  -- Objects that depend on modified object
    schema_diff JSONB,  -- Before/after schema comparison
    validation_warnings TEXT[],
    request_metadata JSONB,
    response_time_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for audit_log
CREATE INDEX IF NOT EXISTS idx_audit_execution_id
    ON ddl_audit_log(execution_id);
CREATE INDEX IF NOT EXISTS idx_audit_migration_id
    ON ddl_audit_log(migration_id) WHERE migration_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_operation_type
    ON ddl_audit_log(operation_type);
CREATE INDEX IF NOT EXISTS idx_audit_object
    ON ddl_audit_log(schema_name, object_name);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp
    ON ddl_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_success
    ON ddl_audit_log(success, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_dry_run
    ON ddl_audit_log(is_dry_run, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_execution_started
    ON ddl_audit_log(execution_started DESC);

-- Comments
COMMENT ON TABLE ddl_audit_log IS 'Immutable audit trail of all DDL operations for compliance and troubleshooting';
COMMENT ON COLUMN ddl_audit_log.is_dry_run IS 'True if operation was executed in dry-run mode (rolled back)';
COMMENT ON COLUMN ddl_audit_log.validation_only IS 'True if operation was validation-only without actual execution';
COMMENT ON COLUMN ddl_audit_log.confirmation_token_used IS 'Confirmation token hash for destructive operations';
COMMENT ON COLUMN ddl_audit_log.schema_diff IS 'JSON diff showing before/after schema state';

-- ============================================================================
-- 3. SCHEMA VERSION TABLE
-- ============================================================================
-- Tracks overall schema state and version progression

CREATE TABLE IF NOT EXISTS ddl_schema_version (
    version_id SERIAL PRIMARY KEY,
    version_number BIGINT NOT NULL UNIQUE,  -- Same format as migration version
    schema_hash VARCHAR(64) NOT NULL,  -- SHA256 hash of current schema definition
    previous_schema_hash VARCHAR(64),
    description TEXT,
    applied_migrations INT[],  -- Array of migration_ids that created this version
    rolled_back_migrations INT[],  -- Array of migration_ids rolled back to reach this version
    total_tables INT,
    total_views INT,
    total_indexes INT,
    total_constraints INT,
    schema_summary JSONB,  -- Complete schema metadata snapshot
    tags TEXT[],  -- ['production', 'stable', 'hotfix', 'experimental']
    metadata JSONB,  -- Additional version metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for schema_version
CREATE INDEX IF NOT EXISTS idx_schema_version_number
    ON ddl_schema_version(version_number DESC);
CREATE INDEX IF NOT EXISTS idx_schema_hash
    ON ddl_schema_version(schema_hash);
CREATE INDEX IF NOT EXISTS idx_schema_created_at
    ON ddl_schema_version(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_schema_tags
    ON ddl_schema_version USING gin(tags);

-- Comments
COMMENT ON TABLE ddl_schema_version IS 'Tracks database schema versions and state over time';
COMMENT ON COLUMN ddl_schema_version.schema_hash IS 'SHA256 hash of all table/view/index definitions for change detection';
COMMENT ON COLUMN ddl_schema_version.applied_migrations IS 'All migrations that have been applied to reach this schema version';
COMMENT ON COLUMN ddl_schema_version.schema_summary IS 'Complete snapshot of schema metadata at this version';

-- ============================================================================
-- 4. HELPER VIEWS
-- ============================================================================

-- Recent migrations view
CREATE OR REPLACE VIEW ddl_recent_migrations AS
SELECT
    migration_id,
    version_number,
    migration_name,
    object_type,
    object_name,
    status,
    executed_at,
    execution_duration_ms,
    error_message,
    created_at
FROM ddl_migration_history
ORDER BY version_number DESC
LIMIT 100;

COMMENT ON VIEW ddl_recent_migrations IS 'Last 100 migrations for quick reference';

-- Failed migrations view
CREATE OR REPLACE VIEW ddl_failed_migrations AS
SELECT
    migration_id,
    version_number,
    migration_name,
    ddl_statement,
    error_code,
    error_message,
    executed_at,
    executed_by
FROM ddl_migration_history
WHERE status IN ('FAILED', 'ROLLBACK_FAILED')
ORDER BY executed_at DESC;

COMMENT ON VIEW ddl_failed_migrations IS 'All failed migrations requiring attention';

-- Recent audit trail view
CREATE OR REPLACE VIEW ddl_recent_audit AS
SELECT
    audit_id,
    execution_id,
    operation_type,
    object_name,
    is_dry_run,
    success,
    duration_ms,
    executed_by,
    execution_started,
    error_message
FROM ddl_audit_log
ORDER BY execution_started DESC
LIMIT 200;

COMMENT ON VIEW ddl_recent_audit IS 'Last 200 DDL operations for quick audit review';

-- Migration statistics view
CREATE OR REPLACE VIEW ddl_migration_stats AS
SELECT
    COUNT(*) as total_migrations,
    COUNT(*) FILTER (WHERE status = 'SUCCESS') as successful,
    COUNT(*) FILTER (WHERE status = 'FAILED') as failed,
    COUNT(*) FILTER (WHERE status LIKE 'ROLLBACK%') as rolled_back,
    COUNT(*) FILTER (WHERE status IN ('CREATED', 'VALIDATED', 'STAGED')) as pending,
    AVG(execution_duration_ms) FILTER (WHERE execution_duration_ms IS NOT NULL) as avg_duration_ms,
    MAX(execution_duration_ms) as max_duration_ms,
    COUNT(DISTINCT executed_by) as unique_executors,
    MAX(executed_at) as last_execution
FROM ddl_migration_history;

COMMENT ON VIEW ddl_migration_stats IS 'Overall migration statistics and health metrics';

-- ============================================================================
-- 5. HELPER FUNCTIONS
-- ============================================================================

-- Function to generate next version number
CREATE OR REPLACE FUNCTION ddl_generate_version_number()
RETURNS BIGINT AS $$
DECLARE
    base_version BIGINT;
    next_version BIGINT;
    seq_num INT := 0;
BEGIN
    -- Format: YYYYMMDDHHMMSSn
    base_version := TO_CHAR(NOW(), 'YYYYMMDDHH24MISS')::BIGINT * 10;

    -- Find next available sequence number for this second
    LOOP
        next_version := base_version + seq_num;

        -- Check if this version exists
        IF NOT EXISTS (
            SELECT 1 FROM ddl_migration_history
            WHERE version_number = next_version
        ) THEN
            RETURN next_version;
        END IF;

        seq_num := seq_num + 1;

        -- Safety limit (max 10 migrations per second)
        IF seq_num >= 10 THEN
            RAISE EXCEPTION 'Too many migrations in same second. Wait 1 second.';
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION ddl_generate_version_number IS 'Generates unique timestamp-based version number in format YYYYMMDDHHMMSSn';

-- Function to update migration status
CREATE OR REPLACE FUNCTION ddl_update_migration_status()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER migration_history_update_timestamp
    BEFORE UPDATE ON ddl_migration_history
    FOR EACH ROW
    EXECUTE FUNCTION ddl_update_migration_status();

-- ============================================================================
-- 6. INITIAL DATA
-- ============================================================================

-- Insert initial schema version (represents current state before migration tracking)
INSERT INTO ddl_schema_version (
    version_number,
    schema_hash,
    description,
    tags,
    metadata
)
SELECT
    TO_CHAR(NOW(), 'YYYYMMDDHH24MISS')::BIGINT * 10,
    'initial',
    'Initial schema version before DDL tracking system',
    ARRAY['baseline', 'system'],
    jsonb_build_object(
        'created_by', 'ddl_schema_setup.sql',
        'system_tables', ARRAY['ddl_migration_history', 'ddl_audit_log', 'ddl_schema_version']
    )
WHERE NOT EXISTS (SELECT 1 FROM ddl_schema_version);

-- ============================================================================
-- 7. PERMISSIONS (Optional - adjust as needed)
-- ============================================================================

-- Grant read access to audit views for monitoring
-- GRANT SELECT ON ddl_recent_migrations TO your_monitoring_role;
-- GRANT SELECT ON ddl_recent_audit TO your_monitoring_role;
-- GRANT SELECT ON ddl_migration_stats TO your_monitoring_role;

-- ============================================================================
-- SETUP COMPLETE
-- ============================================================================

-- Verify setup
DO $$
DECLARE
    table_count INT;
    view_count INT;
    function_count INT;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_name IN ('ddl_migration_history', 'ddl_audit_log', 'ddl_schema_version');

    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_name LIKE 'ddl_%';

    SELECT COUNT(*) INTO function_count
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public' AND p.proname LIKE 'ddl_%';

    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'DDL Schema Setup - COMPLETE';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Tables created: % (expected: 3)', table_count;
    RAISE NOTICE 'Views created: % (expected: 4)', view_count;
    RAISE NOTICE 'Functions created: % (expected: 2)', function_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Verify tables exist: SELECT * FROM ddl_migration_stats;';
    RAISE NOTICE '2. Deploy enhanced DDL server (ddl_server_enhanced.py)';
    RAISE NOTICE '3. Restart Claude Desktop to load new server';
    RAISE NOTICE '============================================================================';
END $$;
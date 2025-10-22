-- DIMS (Data Inventory Management System) Database Schema
-- Version: 1.0.0
-- Created: 2025-10-21
-- Description: PostgreSQL schema for DIMS Phase 2 advanced features

-- ============================================================================
-- Table: metrics_history
-- Purpose: Full audit trail of all metric value changes over time
-- ============================================================================

CREATE TABLE IF NOT EXISTS dims_metrics_history (
    id SERIAL PRIMARY KEY,
    metric_category VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    value_type VARCHAR(20) NOT NULL,  -- 'integer', 'float', 'string', 'boolean'
    numeric_value NUMERIC,             -- Denormalized for fast queries
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    verification_method VARCHAR(50),
    verified_by VARCHAR(100),
    cached BOOLEAN DEFAULT FALSE,
    cache_expires TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_metrics_history_category_name
    ON dims_metrics_history(metric_category, metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_history_recorded_at
    ON dims_metrics_history(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_history_category_name_time
    ON dims_metrics_history(metric_category, metric_name, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_history_numeric
    ON dims_metrics_history(metric_category, metric_name, numeric_value)
    WHERE value_type IN ('integer', 'float');

-- Comments
COMMENT ON TABLE dims_metrics_history IS 'Complete history of all metric values for trend analysis';
COMMENT ON COLUMN dims_metrics_history.numeric_value IS 'Denormalized numeric value for fast aggregation queries';
COMMENT ON COLUMN dims_metrics_history.metadata IS 'Additional metadata as JSON (e.g., source, notes, context)';


-- ============================================================================
-- Table: metrics_snapshots
-- Purpose: Store complete daily snapshots of all metrics
-- ============================================================================

CREATE TABLE IF NOT EXISTS dims_metrics_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL UNIQUE,
    metrics_data JSONB NOT NULL,
    total_metrics INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_snapshots_date
    ON dims_metrics_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_data_gin
    ON dims_metrics_snapshots USING gin(metrics_data);

-- Comments
COMMENT ON TABLE dims_metrics_snapshots IS 'Daily snapshots of complete metrics state for point-in-time recovery';
COMMENT ON COLUMN dims_metrics_snapshots.metrics_data IS 'Complete metrics YAML stored as JSONB';


-- ============================================================================
-- Table: verification_runs
-- Purpose: Log every verification run for audit trail
-- ============================================================================

CREATE TABLE IF NOT EXISTS dims_verification_runs (
    id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    total_metrics INTEGER NOT NULL,
    metrics_verified INTEGER NOT NULL,
    drift_detected BOOLEAN NOT NULL DEFAULT FALSE,
    auto_updated BOOLEAN DEFAULT FALSE,
    discrepancies JSONB,
    summary JSONB,
    execution_time_ms INTEGER,
    triggered_by VARCHAR(100),  -- 'manual', 'scheduled', 'git_hook', 's3_event'
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_verification_runs_timestamp
    ON dims_verification_runs(run_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_verification_runs_drift
    ON dims_verification_runs(drift_detected)
    WHERE drift_detected = TRUE;

-- Comments
COMMENT ON TABLE dims_verification_runs IS 'Complete log of all verification runs';
COMMENT ON COLUMN dims_verification_runs.discrepancies IS 'Array of metrics with drift detected';
COMMENT ON COLUMN dims_verification_runs.summary IS 'Status breakdown (ok, minor, moderate, major, error)';


-- ============================================================================
-- Table: approval_log
-- Purpose: Track approval workflow for critical metric changes
-- ============================================================================

CREATE TABLE IF NOT EXISTS dims_approval_log (
    id SERIAL PRIMARY KEY,
    metric_category VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    drift_pct NUMERIC(10, 2),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    severity VARCHAR(20),  -- 'low', 'medium', 'high', 'critical'
    requested_by VARCHAR(100),
    requested_at TIMESTAMP DEFAULT NOW(),
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    auto_applied BOOLEAN DEFAULT FALSE,
    verification_run_id INTEGER REFERENCES dims_verification_runs(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_approval_log_status
    ON dims_approval_log(status)
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_approval_log_category_name
    ON dims_approval_log(metric_category, metric_name);
CREATE INDEX IF NOT EXISTS idx_approval_log_requested_at
    ON dims_approval_log(requested_at DESC);

-- Comments
COMMENT ON TABLE dims_approval_log IS 'Approval workflow tracking for critical metric changes';
COMMENT ON COLUMN dims_approval_log.status IS 'Current approval status';
COMMENT ON COLUMN dims_approval_log.auto_applied IS 'Whether change was auto-applied after approval';


-- ============================================================================
-- Table: event_log
-- Purpose: Log all events that trigger metric updates
-- ============================================================================

CREATE TABLE IF NOT EXISTS dims_event_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,  -- 'git_commit', 's3_upload', 'manual', 'scheduled'
    event_source VARCHAR(200),
    metrics_triggered TEXT[],  -- Array of metric paths
    verification_run_id INTEGER REFERENCES dims_verification_runs(id),
    event_data JSONB,
    processed_at TIMESTAMP DEFAULT NOW(),
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_event_log_type
    ON dims_event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_processed_at
    ON dims_event_log(processed_at DESC);

-- Comments
COMMENT ON TABLE dims_event_log IS 'Log of all events triggering metric updates';


-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- Latest value for each metric
CREATE OR REPLACE VIEW dims_metrics_latest AS
SELECT DISTINCT ON (metric_category, metric_name)
    metric_category,
    metric_name,
    value,
    value_type,
    numeric_value,
    recorded_at,
    verification_method,
    verified_by
FROM dims_metrics_history
ORDER BY metric_category, metric_name, recorded_at DESC;

COMMENT ON VIEW dims_metrics_latest IS 'Most recent value for each metric';


-- Metrics with pending approvals
CREATE OR REPLACE VIEW dims_pending_approvals AS
SELECT
    id,
    metric_category,
    metric_name,
    old_value,
    new_value,
    drift_pct,
    severity,
    requested_by,
    requested_at,
    EXTRACT(EPOCH FROM (NOW() - requested_at))/3600 AS hours_pending
FROM dims_approval_log
WHERE status = 'pending'
ORDER BY requested_at DESC;

COMMENT ON VIEW dims_pending_approvals IS 'All pending approval requests';


-- Recent verification runs with drift
CREATE OR REPLACE VIEW dims_recent_drift AS
SELECT
    run_timestamp,
    total_metrics,
    metrics_verified,
    jsonb_array_length(discrepancies) AS discrepancy_count,
    triggered_by,
    execution_time_ms
FROM dims_verification_runs
WHERE drift_detected = TRUE
ORDER BY run_timestamp DESC
LIMIT 100;

COMMENT ON VIEW dims_recent_drift IS 'Last 100 verification runs that detected drift';


-- ============================================================================
-- Functions for Analytics
-- ============================================================================

-- Get metric trend over time
CREATE OR REPLACE FUNCTION dims_get_metric_trend(
    p_category VARCHAR,
    p_metric VARCHAR,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    date DATE,
    value TEXT,
    numeric_value NUMERIC,
    verification_method VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        recorded_at::DATE AS date,
        h.value,
        h.numeric_value,
        h.verification_method
    FROM dims_metrics_history h
    WHERE h.metric_category = p_category
      AND h.metric_name = p_metric
      AND h.recorded_at >= NOW() - (p_days || ' days')::INTERVAL
    ORDER BY recorded_at;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dims_get_metric_trend IS 'Get metric values over time for trend analysis';


-- Calculate metric statistics
CREATE OR REPLACE FUNCTION dims_metric_stats(
    p_category VARCHAR,
    p_metric VARCHAR,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    min_value NUMERIC,
    max_value NUMERIC,
    avg_value NUMERIC,
    stddev_value NUMERIC,
    latest_value NUMERIC,
    change_pct NUMERIC,
    data_points INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        MIN(numeric_value) AS min_value,
        MAX(numeric_value) AS max_value,
        AVG(numeric_value) AS avg_value,
        STDDEV(numeric_value) AS stddev_value,
        (SELECT numeric_value FROM dims_metrics_history
         WHERE metric_category = p_category AND metric_name = p_metric
         ORDER BY recorded_at DESC LIMIT 1) AS latest_value,
        CASE
            WHEN MIN(numeric_value) > 0 THEN
                ((SELECT numeric_value FROM dims_metrics_history
                  WHERE metric_category = p_category AND metric_name = p_metric
                  ORDER BY recorded_at DESC LIMIT 1) - MIN(numeric_value)) / MIN(numeric_value) * 100
            ELSE NULL
        END AS change_pct,
        COUNT(*)::INTEGER AS data_points
    FROM dims_metrics_history
    WHERE metric_category = p_category
      AND metric_name = p_metric
      AND numeric_value IS NOT NULL
      AND recorded_at >= NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dims_metric_stats IS 'Calculate statistics for a metric over time';


-- ============================================================================
-- Retention Policy Functions
-- ============================================================================

-- Clean up old history beyond retention period
CREATE OR REPLACE FUNCTION dims_cleanup_old_history(
    p_retention_days INTEGER DEFAULT 365
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM dims_metrics_history
    WHERE recorded_at < NOW() - (p_retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dims_cleanup_old_history IS 'Delete metric history older than retention period';


-- Clean up old snapshots
CREATE OR REPLACE FUNCTION dims_cleanup_old_snapshots(
    p_retention_days INTEGER DEFAULT 90
)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM dims_metrics_snapshots
    WHERE snapshot_date < CURRENT_DATE - p_retention_days;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION dims_cleanup_old_snapshots IS 'Delete snapshots older than retention period';


-- ============================================================================
-- Initial Data & Configuration
-- ============================================================================

-- Create a metadata table for DIMS configuration
CREATE TABLE IF NOT EXISTS dims_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    value_type VARCHAR(20),
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert initial config
INSERT INTO dims_config (key, value, value_type, description) VALUES
    ('schema_version', '1.0.0', 'string', 'DIMS database schema version'),
    ('retention_history_days', '365', 'integer', 'Days to retain metric history'),
    ('retention_snapshots_days', '90', 'integer', 'Days to retain daily snapshots'),
    ('auto_cleanup_enabled', 'true', 'boolean', 'Automatically run cleanup functions')
ON CONFLICT (key) DO NOTHING;


-- ============================================================================
-- Grants (adjust based on your user)
-- ============================================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;


-- ============================================================================
-- Schema Installation Complete
-- ============================================================================

-- Verify installation
DO $$
BEGIN
    RAISE NOTICE 'DIMS Schema Installation Complete';
    RAISE NOTICE 'Schema Version: 1.0.0';
    RAISE NOTICE 'Tables Created: 6';
    RAISE NOTICE 'Views Created: 3';
    RAISE NOTICE 'Functions Created: 4';
END $$;

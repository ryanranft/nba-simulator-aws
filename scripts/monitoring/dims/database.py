"""
DIMS Database Module
PostgreSQL backend for metric history, snapshots, and analytics.
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

# Try to load credentials from nba-sim-credentials.env
try:
    from dotenv import load_dotenv
    credentials_file = Path.home() / 'nba-sim-credentials.env'
    if credentials_file.exists():
        load_dotenv(credentials_file)
        logger = logging.getLogger(__name__)
        logger.debug(f"Loaded credentials from {credentials_file}")
except ImportError:
    # python-dotenv not available, continue without it
    pass

try:
    import psycopg2
    from psycopg2 import pool, sql, extras
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("psycopg2 not installed. Database features disabled.")

logger = logging.getLogger(__name__)


class DatabaseBackend:
    """PostgreSQL backend for DIMS."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database backend.

        Args:
            config: Database configuration dict
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for database backend. Install with: pip install psycopg2-binary")

        self.config = config
        self.connection_config = config.get('connection', {})

        # Expand environment variables
        self.host = os.path.expandvars(self.connection_config.get('host', 'localhost'))
        self.port = self.connection_config.get('port', 5432)
        self.database = os.path.expandvars(self.connection_config.get('database', 'nba_simulator'))
        self.user = os.path.expandvars(self.connection_config.get('user', 'postgres'))
        self.password = os.path.expandvars(self.connection_config.get('password', ''))

        # Connection pool
        self.pool = None
        self._initialize_pool()

        logger.info(f"Database backend initialized: {self.database}@{self.host}:{self.port}")

    def _initialize_pool(self):
        """Initialize connection pool."""
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1,  # minconn
                10,  # maxconn
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool."""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool."""
        if self.pool and conn:
            self.pool.putconn(conn)

    def close_pool(self):
        """Close all connections in pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            self.return_connection(conn)
            logger.info("Database connection test successful")
            return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def run_migration(self, schema_path: Path) -> bool:
        """
        Run database migration from SQL file.

        Args:
            schema_path: Path to SQL schema file

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            with open(schema_path, 'r') as f:
                schema_sql = f.read()

            cursor.execute(schema_sql)
            cursor.close()
            self.return_connection(conn)

            logger.info(f"Database migration completed: {schema_path}")
            return True

        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            return False

    def save_metric(
        self,
        metric_category: str,
        metric_name: str,
        value: Any,
        value_type: str,
        verification_method: str = 'automated',
        verified_by: str = 'dims',
        cached: bool = False,
        cache_expires: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save metric value to history.

        Args:
            metric_category: Metric category
            metric_name: Metric name
            value: Metric value
            value_type: Value type (integer, float, string, boolean)
            verification_method: How value was verified
            verified_by: Who/what verified
            cached: Whether value is cached
            cache_expires: Cache expiration time
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Convert value to string for storage
            value_str = str(value)

            # Extract numeric value if applicable
            numeric_value = None
            if value_type in ('integer', 'float'):
                try:
                    numeric_value = float(value)
                except (ValueError, TypeError):
                    pass

            # Convert metadata to JSON
            metadata_json = json.dumps(metadata) if metadata else None

            query = """
                INSERT INTO dims_metrics_history (
                    metric_category, metric_name, value, value_type,
                    numeric_value, verification_method, verified_by,
                    cached, cache_expires, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                metric_category, metric_name, value_str, value_type,
                numeric_value, verification_method, verified_by,
                cached, cache_expires, metadata_json
            ))

            conn.commit()
            cursor.close()
            self.return_connection(conn)

            logger.debug(f"Saved metric to database: {metric_category}.{metric_name} = {value}")
            return True

        except Exception as e:
            logger.error(f"Failed to save metric: {e}")
            return False

    def save_snapshot(self, snapshot_date: datetime, metrics_data: Dict[str, Any]) -> bool:
        """
        Save daily snapshot to database.

        Args:
            snapshot_date: Snapshot date
            metrics_data: Complete metrics dict

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Convert to JSON
            metrics_json = json.dumps(metrics_data, default=str)

            # Count total metrics (excluding metadata)
            total_metrics = len([k for k in metrics_data.keys() if k != 'metadata'])

            query = """
                INSERT INTO dims_metrics_snapshots (snapshot_date, metrics_data, total_metrics)
                VALUES (%s, %s, %s)
                ON CONFLICT (snapshot_date) DO UPDATE
                SET metrics_data = EXCLUDED.metrics_data,
                    total_metrics = EXCLUDED.total_metrics
            """

            cursor.execute(query, (snapshot_date.date(), metrics_json, total_metrics))

            conn.commit()
            cursor.close()
            self.return_connection(conn)

            logger.info(f"Saved snapshot to database: {snapshot_date.date()}")
            return True

        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False

    def save_verification_run(
        self,
        results: Dict[str, Any],
        triggered_by: str = 'manual',
        execution_time_ms: Optional[int] = None
    ) -> Optional[int]:
        """
        Save verification run to database.

        Args:
            results: Verification results dict
            triggered_by: What triggered this verification
            execution_time_ms: Execution time in milliseconds

        Returns:
            Verification run ID if successful, None otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Determine if auto-update was used (heuristic: check if any discrepancies exist)
            auto_updated = len(results.get('discrepancies', [])) == 0 and results.get('drift_detected', False)

            # Convert to JSON
            discrepancies_json = json.dumps(results.get('discrepancies', []), default=str)
            summary_json = json.dumps(results.get('summary', {}), default=str)

            query = """
                INSERT INTO dims_verification_runs (
                    total_metrics, metrics_verified, drift_detected, auto_updated,
                    discrepancies, summary, execution_time_ms, triggered_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            cursor.execute(query, (
                results.get('total_metrics', 0),
                results.get('verified', 0),
                results.get('drift_detected', False),
                auto_updated,
                discrepancies_json,
                summary_json,
                execution_time_ms,
                triggered_by
            ))

            run_id = cursor.fetchone()[0]

            conn.commit()
            cursor.close()
            self.return_connection(conn)

            logger.info(f"Saved verification run to database: ID={run_id}")
            return run_id

        except Exception as e:
            logger.error(f"Failed to save verification run: {e}")
            return None

    def get_metric_history(
        self,
        metric_category: str,
        metric_name: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get metric history from database.

        Args:
            metric_category: Metric category
            metric_name: Metric name
            days: Number of days to look back

        Returns:
            List of metric history records
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            cutoff_date = datetime.now() - timedelta(days=days)

            query = """
                SELECT
                    metric_category,
                    metric_name,
                    value,
                    value_type,
                    numeric_value,
                    recorded_at,
                    verification_method,
                    verified_by
                FROM dims_metrics_history
                WHERE metric_category = %s
                  AND metric_name = %s
                  AND recorded_at >= %s
                ORDER BY recorded_at ASC
            """

            cursor.execute(query, (metric_category, metric_name, cutoff_date))
            results = cursor.fetchall()

            cursor.close()
            self.return_connection(conn)

            # Convert to list of dicts
            history = [dict(row) for row in results]

            logger.debug(f"Retrieved {len(history)} history records for {metric_category}.{metric_name}")
            return history

        except Exception as e:
            logger.error(f"Failed to get metric history: {e}")
            return []

    def get_metric_stats(
        self,
        metric_category: str,
        metric_name: str,
        days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Get metric statistics from database.

        Args:
            metric_category: Metric category
            metric_name: Metric name
            days: Number of days for statistics

        Returns:
            Dict with statistics or None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            query = """
                SELECT * FROM dims_metric_stats(%s, %s, %s)
            """

            cursor.execute(query, (metric_category, metric_name, days))
            result = cursor.fetchone()

            cursor.close()
            self.return_connection(conn)

            if result:
                return dict(result)
            return None

        except Exception as e:
            logger.error(f"Failed to get metric stats: {e}")
            return None

    def get_snapshot(self, snapshot_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Get snapshot from database.

        Args:
            snapshot_date: Date of snapshot

        Returns:
            Metrics dict or None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            query = """
                SELECT metrics_data
                FROM dims_metrics_snapshots
                WHERE snapshot_date = %s
            """

            cursor.execute(query, (snapshot_date.date(),))
            result = cursor.fetchone()

            cursor.close()
            self.return_connection(conn)

            if result:
                return result['metrics_data']
            return None

        except Exception as e:
            logger.error(f"Failed to get snapshot: {e}")
            return None

    def get_verification_runs(
        self,
        days: int = 7,
        drift_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get recent verification runs.

        Args:
            days: Number of days to look back
            drift_only: Only return runs with drift detected

        Returns:
            List of verification run records
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            cutoff_date = datetime.now() - timedelta(days=days)

            if drift_only:
                query = """
                    SELECT *
                    FROM dims_verification_runs
                    WHERE run_timestamp >= %s
                      AND drift_detected = TRUE
                    ORDER BY run_timestamp DESC
                """
            else:
                query = """
                    SELECT *
                    FROM dims_verification_runs
                    WHERE run_timestamp >= %s
                    ORDER BY run_timestamp DESC
                """

            cursor.execute(query, (cutoff_date,))
            results = cursor.fetchall()

            cursor.close()
            self.return_connection(conn)

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to get verification runs: {e}")
            return []

    def cleanup_old_data(
        self,
        history_days: int = 365,
        snapshot_days: int = 90
    ) -> Tuple[int, int]:
        """
        Clean up old data beyond retention period.

        Args:
            history_days: Days to retain history
            snapshot_days: Days to retain snapshots

        Returns:
            Tuple of (history_deleted, snapshots_deleted)
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Clean history
            cursor.execute("SELECT dims_cleanup_old_history(%s)", (history_days,))
            history_deleted = cursor.fetchone()[0]

            # Clean snapshots
            cursor.execute("SELECT dims_cleanup_old_snapshots(%s)", (snapshot_days,))
            snapshots_deleted = cursor.fetchone()[0]

            conn.commit()
            cursor.close()
            self.return_connection(conn)

            logger.info(f"Cleanup complete: {history_deleted} history, {snapshots_deleted} snapshots deleted")
            return (history_deleted, snapshots_deleted)

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return (0, 0)

    def query_custom(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute custom SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows as dicts
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()

            cursor.close()
            self.return_connection(conn)

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to execute custom query: {e}")
            return []

    def __del__(self):
        """Cleanup on deletion."""
        self.close_pool()

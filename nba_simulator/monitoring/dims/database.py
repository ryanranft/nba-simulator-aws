"""
DIMS Database Backend - PostgreSQL Persistence

Provides database backend for DIMS metrics, historical tracking, and auditing.

Features:
- Metric history storage
- Verification run tracking
- Event auditing
- Snapshot persistence

Tables:
- dims_metrics_history: Historical metric values
- dims_verification_runs: Verification execution logs
- dims_event_log: Event audit trail
- dims_approval_log: Approval workflow records
- dims_metrics_snapshots: Daily snapshots

Based on: scripts/monitoring/dims/database.py
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone

from ...database import get_db_connection, execute_query
from ...utils import setup_logging


class DIMSDatabase:
    """
    PostgreSQL backend for DIMS metrics persistence.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize DIMS database backend.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or setup_logging('nba_simulator.monitoring.dims.database')
        self.db = get_db_connection()
        
        self.logger.info("DIMS Database initialized")
    
    def save_metric(
        self,
        metric_category: str,
        metric_name: str,
        value: Any,
        value_type: str,
        verification_method: str = 'automated',
        verified_by: str = 'dims'
    ) -> bool:
        """
        Save a metric value to database.
        
        Args:
            metric_category: Metric category
            metric_name: Metric name
            value: Metric value
            value_type: Value type (integer, float, string, boolean)
            verification_method: Verification method
            verified_by: Who verified
            
        Returns:
            True if successful
        """
        try:
            # Store value as string for flexibility
            value_str = str(value)
            
            query = """
                INSERT INTO dims_metrics_history (
                    metric_category, metric_name, value, value_type,
                    verification_method, verified_by, recorded_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            
            self.db.execute_write(
                query,
                (metric_category, metric_name, value_str, value_type,
                 verification_method, verified_by)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save metric: {e}")
            return False
    
    def get_metric_history(
        self,
        metric_path: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical values for a metric.
        
        Args:
            metric_path: Dot-separated metric path (category.name)
            days: Number of days to look back
            
        Returns:
            List of historical values
        """
        try:
            parts = metric_path.split('.')
            if len(parts) != 2:
                return []
            
            category, name = parts
            
            query = """
                SELECT recorded_at::date as date, value, value_type
                FROM dims_metrics_history
                WHERE metric_category = %s
                  AND metric_name = %s
                  AND recorded_at >= NOW() - INTERVAL '%s days'
                ORDER BY recorded_at DESC
            """
            
            results = execute_query(query, (category, name, days))
            
            return [
                {
                    'date': row['date'].isoformat(),
                    'value': self._parse_value(row['value'], row['value_type'])
                }
                for row in results
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get metric history: {e}")
            return []
    
    def save_verification_run(
        self,
        results: Dict[str, Any],
        triggered_by: str,
        execution_time_ms: int
    ) -> Optional[int]:
        """
        Save a verification run to database.
        
        Args:
            results: Verification results
            triggered_by: What triggered the run
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            Verification run ID or None if failed
        """
        try:
            query = """
                INSERT INTO dims_verification_runs (
                    timestamp, total_metrics, verified, drift_detected,
                    triggered_by, execution_time_ms, results_json
                )
                VALUES (NOW(), %s, %s, %s, %s, %s, %s::jsonb)
                RETURNING id
            """
            
            result = execute_query(
                query,
                (results['total_metrics'], results['verified'],
                 results['drift_detected'], triggered_by,
                 execution_time_ms, results)
            )
            
            if result:
                return result[0]['id']
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to save verification run: {e}")
            return None
    
    def save_snapshot(
        self,
        snapshot_date: datetime,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        Save a metrics snapshot to database.
        
        Args:
            snapshot_date: Date of snapshot
            metrics: Metrics dictionary
            
        Returns:
            True if successful
        """
        try:
            query = """
                INSERT INTO dims_metrics_snapshots (snapshot_date, metrics_json)
                VALUES (%s, %s::jsonb)
                ON CONFLICT (snapshot_date)
                DO UPDATE SET metrics_json = EXCLUDED.metrics_json
            """
            
            self.db.execute_write(query, (snapshot_date.date(), metrics))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save snapshot: {e}")
            return False
    
    def _parse_value(self, value_str: str, value_type: str) -> Any:
        """Parse value string based on type"""
        try:
            if value_type == 'integer':
                return int(value_str)
            elif value_type == 'float':
                return float(value_str)
            elif value_type == 'boolean':
                return value_str.lower() in ('true', '1', 'yes')
            else:
                return value_str
        except:
            return value_str

"""
DIMS Events Module
Handles event-driven metric updates from Git hooks, S3 events, etc.
"""

import logging
import fnmatch
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EventHandler:
    """Handles events that trigger metric updates."""

    def __init__(self, config: Dict[str, Any], database_backend=None):
        """
        Initialize event handler.

        Args:
            config: DIMS configuration dict
            database_backend: Database backend instance (optional)
        """
        self.config = config
        self.events_config = config.get('events', {})
        self.database = database_backend

        # Check if event-driven updates are enabled
        self.enabled = self.events_config.get('enabled', False)

        if not self.enabled:
            logger.info("Event-driven updates are disabled")
            return

        # Load event hooks configuration
        self.hooks = self.events_config.get('hooks', [])

        # Event cooldown cache (prevent spam)
        self._last_event_times: Dict[str, datetime] = {}
        self._cooldown_seconds = self.events_config.get('cooldown_seconds', 60)

        logger.info(f"Event handler initialized: {len(self.hooks)} hooks configured")

    def _is_cooldown_active(self, event_key: str) -> bool:
        """
        Check if event is in cooldown period.

        Args:
            event_key: Unique event key

        Returns:
            True if in cooldown, False otherwise
        """
        if event_key not in self._last_event_times:
            return False

        last_time = self._last_event_times[event_key]
        elapsed = (datetime.now() - last_time).total_seconds()

        return elapsed < self._cooldown_seconds

    def _update_cooldown(self, event_key: str):
        """Update last event time for cooldown."""
        self._last_event_times[event_key] = datetime.now()

    def _match_metrics(self, patterns: List[str], all_metrics: List[str]) -> Set[str]:
        """
        Match metric patterns against available metrics.

        Args:
            patterns: List of metric patterns (supports wildcards)
            all_metrics: List of all available metrics

        Returns:
            Set of matched metric names
        """
        matched = set()

        for pattern in patterns:
            # Direct match
            if pattern in all_metrics:
                matched.add(pattern)
                continue

            # Wildcard match
            if '*' in pattern:
                for metric in all_metrics:
                    if fnmatch.fnmatch(metric, pattern):
                        matched.add(metric)

        return matched

    def _get_available_metrics(self) -> List[str]:
        """
        Get list of all available metrics from config.

        Returns:
            List of metric full names (category.metric)
        """
        metrics = []
        metrics_config = self.config.get('metrics', {})

        for category, category_metrics in metrics_config.items():
            for metric_name in category_metrics.keys():
                metrics.append(f"{category}.{metric_name}")

        return metrics

    def log_event(
        self,
        event_type: str,
        event_source: str,
        metrics_triggered: List[str],
        verification_run_id: Optional[int] = None,
        event_data: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Log an event to database.

        Args:
            event_type: Type of event
            event_source: Source of event
            metrics_triggered: List of metrics triggered
            verification_run_id: ID of verification run (if any)
            event_data: Additional event data
            execution_time_ms: Execution time in milliseconds
            success: Whether event was processed successfully
            error_message: Error message if failed

        Returns:
            True if logged successfully, False otherwise
        """
        if not self.database:
            logger.debug("Database not available, skipping event log")
            return False

        try:
            import json

            conn = self.database.get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO dims_event_log (
                    event_type, event_source, metrics_triggered,
                    verification_run_id, event_data, execution_time_ms,
                    success, error_message
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            event_data_json = json.dumps(event_data) if event_data else None

            cursor.execute(query, (
                event_type,
                event_source,
                metrics_triggered,
                verification_run_id,
                event_data_json,
                execution_time_ms,
                success,
                error_message
            ))

            conn.commit()
            cursor.close()
            self.database.return_connection(conn)

            logger.debug(f"Event logged: {event_type} from {event_source}")
            return True

        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            return False

    def handle_event(
        self,
        event_type: str,
        event_source: str = '',
        event_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle an event and trigger appropriate metric updates.

        Args:
            event_type: Type of event (git_commit, s3_upload, etc.)
            event_source: Source of event (optional)
            event_data: Additional event data (optional)

        Returns:
            Dict with event processing results
        """
        if not self.enabled:
            return {
                'success': False,
                'error': 'Event-driven updates are disabled',
                'metrics_triggered': []
            }

        result = {
            'success': True,
            'event_type': event_type,
            'event_source': event_source,
            'metrics_triggered': [],
            'verification_run_id': None,
            'error': None
        }

        # Check cooldown
        event_key = f"{event_type}:{event_source}"
        if self._is_cooldown_active(event_key):
            logger.debug(f"Event in cooldown: {event_key}")
            result['success'] = False
            result['error'] = 'Event in cooldown period'
            return result

        # Find matching hook
        hook_config = None
        for hook in self.hooks:
            if hook.get('name') == event_type or hook.get('trigger') == event_type:
                hook_config = hook
                break

        if not hook_config:
            logger.warning(f"No hook configured for event type: {event_type}")
            result['success'] = False
            result['error'] = f'No hook configured for {event_type}'
            return result

        # Get metrics to update
        metric_patterns = hook_config.get('metrics', [])
        available_metrics = self._get_available_metrics()
        metrics_to_update = self._match_metrics(metric_patterns, available_metrics)

        result['metrics_triggered'] = list(metrics_to_update)

        logger.info(f"Event {event_type} triggered {len(metrics_to_update)} metrics")

        # Update cooldown
        self._update_cooldown(event_key)

        # Log event
        self.log_event(
            event_type=event_type,
            event_source=event_source,
            metrics_triggered=result['metrics_triggered'],
            event_data=event_data,
            success=True
        )

        return result

    def on_git_commit(self, commit_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle git commit event.

        Args:
            commit_hash: Git commit hash (optional)

        Returns:
            Event processing result
        """
        event_data = {}
        if commit_hash:
            event_data['commit_hash'] = commit_hash

        return self.handle_event('git_post_commit', 'git', event_data)

    def on_s3_upload(self, bucket: Optional[str] = None, key: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle S3 upload event.

        Args:
            bucket: S3 bucket name (optional)
            key: S3 object key (optional)

        Returns:
            Event processing result
        """
        event_data = {}
        if bucket:
            event_data['bucket'] = bucket
        if key:
            event_data['key'] = key

        return self.handle_event('s3_upload', f"s3://{bucket}/{key}" if bucket and key else 's3', event_data)

    def on_manual_trigger(self, triggered_by: str = 'user') -> Dict[str, Any]:
        """
        Handle manual trigger event.

        Args:
            triggered_by: Who triggered manually

        Returns:
            Event processing result
        """
        event_data = {'triggered_by': triggered_by}
        return self.handle_event('manual', triggered_by, event_data)

    def get_event_history(self, days: int = 7, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get event history from database.

        Args:
            days: Number of days to look back
            event_type: Filter by event type (optional)

        Returns:
            List of event records
        """
        if not self.database:
            return []

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            cutoff_date = datetime.now() - timedelta(days=days)

            if event_type:
                query = """
                    SELECT
                        id, event_type, event_source, metrics_triggered,
                        verification_run_id, processed_at, execution_time_ms,
                        success, error_message
                    FROM dims_event_log
                    WHERE processed_at >= %s
                      AND event_type = %s
                    ORDER BY processed_at DESC
                """
                cursor.execute(query, (cutoff_date, event_type))
            else:
                query = """
                    SELECT
                        id, event_type, event_source, metrics_triggered,
                        verification_run_id, processed_at, execution_time_ms,
                        success, error_message
                    FROM dims_event_log
                    WHERE processed_at >= %s
                    ORDER BY processed_at DESC
                """
                cursor.execute(query, (cutoff_date,))

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            cursor.close()
            self.database.return_connection(conn)

            # Convert to list of dicts
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            logger.debug(f"Retrieved {len(results)} event history records")
            return results

        except Exception as e:
            logger.error(f"Failed to get event history: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event statistics.

        Returns:
            Dict with event stats
        """
        if not self.enabled:
            return {
                'enabled': False,
                'total_events': 0,
                'successful_events': 0,
                'failed_events': 0
            }

        if not self.database:
            return {
                'enabled': True,
                'total_events': 0,
                'successful_events': 0,
                'failed_events': 0,
                'hooks_configured': len(self.hooks)
            }

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    COUNT(*) FILTER (WHERE success = TRUE) AS successful,
                    COUNT(*) FILTER (WHERE success = FALSE) AS failed,
                    COUNT(*) AS total
                FROM dims_event_log
                WHERE processed_at >= NOW() - INTERVAL '7 days'
            """

            cursor.execute(query)
            result = cursor.fetchone()

            cursor.close()
            self.database.return_connection(conn)

            if result:
                successful, failed, total = result
                return {
                    'enabled': True,
                    'total_events': total,
                    'successful_events': successful,
                    'failed_events': failed,
                    'hooks_configured': len(self.hooks),
                    'cooldown_seconds': self._cooldown_seconds
                }

            return {
                'enabled': True,
                'total_events': 0,
                'successful_events': 0,
                'failed_events': 0,
                'hooks_configured': len(self.hooks)
            }

        except Exception as e:
            logger.error(f"Failed to get event stats: {e}")
            return {
                'enabled': True,
                'total_events': 0,
                'successful_events': 0,
                'failed_events': 0,
                'error': str(e)
            }

    def test_event(self, event_type: str) -> Dict[str, Any]:
        """
        Test an event handler without actually triggering updates.

        Args:
            event_type: Event type to test

        Returns:
            Dict with test results
        """
        # Find hook
        hook_config = None
        for hook in self.hooks:
            if hook.get('name') == event_type or hook.get('trigger') == event_type:
                hook_config = hook
                break

        if not hook_config:
            return {
                'success': False,
                'error': f'No hook configured for {event_type}',
                'metrics_would_trigger': []
            }

        # Get metrics that would be triggered
        metric_patterns = hook_config.get('metrics', [])
        available_metrics = self._get_available_metrics()
        metrics_to_update = self._match_metrics(metric_patterns, available_metrics)

        return {
            'success': True,
            'event_type': event_type,
            'hook_name': hook_config.get('name'),
            'metric_patterns': metric_patterns,
            'metrics_would_trigger': list(metrics_to_update),
            'trigger_count': len(metrics_to_update)
        }

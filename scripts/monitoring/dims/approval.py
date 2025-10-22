"""
DIMS Approval Module
Handles 3-tier approval workflow for critical metric changes.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ApprovalManager:
    """Manages approval workflow for critical metric changes."""

    def __init__(self, config: Dict[str, Any], database_backend=None):
        """
        Initialize approval manager.

        Args:
            config: DIMS configuration dict
            database_backend: Database backend instance (optional)
        """
        self.config = config
        self.approval_config = config.get('approval', {})
        self.database = database_backend

        # Check if approval workflow is enabled
        self.enabled = self.approval_config.get('enabled', False)

        if not self.enabled:
            logger.info("Approval workflow is disabled")
            return

        # Get critical metrics list
        self.critical_metrics = self.approval_config.get('critical_metrics', [])

        # Get approval threshold (% drift requiring approval)
        self.approval_threshold = self.approval_config.get('require_approval_threshold', 15.0)

        logger.info(f"Approval workflow initialized: {len(self.critical_metrics)} critical metrics, {self.approval_threshold}% threshold")

    def is_critical_metric(self, metric_category: str, metric_name: str) -> bool:
        """
        Check if a metric is critical and requires approval.

        Args:
            metric_category: Metric category
            metric_name: Metric name

        Returns:
            True if metric is critical, False otherwise
        """
        if not self.enabled:
            return False

        metric_full_name = f"{metric_category}.{metric_name}"

        # Check exact match
        if metric_full_name in self.critical_metrics:
            return True

        # Check category wildcard (e.g., "s3_storage.*")
        category_wildcard = f"{metric_category}.*"
        if category_wildcard in self.critical_metrics:
            return True

        # Check if just the metric name is in the list (for backward compatibility)
        if metric_name in self.critical_metrics:
            return True

        return False

    def requires_approval(
        self,
        metric_category: str,
        metric_name: str,
        drift_pct: Optional[float],
        severity: str
    ) -> bool:
        """
        Determine if a metric change requires approval.

        Args:
            metric_category: Metric category
            metric_name: Metric name
            drift_pct: Drift percentage (or None)
            severity: Severity level

        Returns:
            True if approval required, False otherwise
        """
        if not self.enabled:
            return False

        # Check if metric is critical
        if not self.is_critical_metric(metric_category, metric_name):
            return False

        # Check if drift exceeds threshold
        if drift_pct is not None and drift_pct >= self.approval_threshold:
            return True

        # Check if severity is high or critical
        if severity in ('high', 'critical'):
            return True

        return False

    def request_approval(
        self,
        metric_category: str,
        metric_name: str,
        old_value: Any,
        new_value: Any,
        drift_pct: Optional[float],
        severity: str,
        requested_by: str = 'dims_core',
        verification_run_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Create an approval request.

        Args:
            metric_category: Metric category
            metric_name: Metric name
            old_value: Current value
            new_value: Proposed new value
            drift_pct: Drift percentage
            severity: Severity level
            requested_by: Who requested the change
            verification_run_id: ID of verification run that detected this

        Returns:
            Approval request ID if successful, None otherwise
        """
        if not self.enabled:
            logger.warning("Approval workflow is disabled, cannot create request")
            return None

        if not self.database:
            logger.error("Database backend required for approval workflow")
            return None

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO dims_approval_log (
                    metric_category, metric_name, old_value, new_value,
                    drift_pct, severity, requested_by, verification_run_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            cursor.execute(query, (
                metric_category,
                metric_name,
                str(old_value),
                str(new_value),
                drift_pct,
                severity,
                requested_by,
                verification_run_id
            ))

            approval_id = cursor.fetchone()[0]

            conn.commit()
            cursor.close()
            self.database.return_connection(conn)

            logger.info(f"Approval request created: ID={approval_id}, {metric_category}.{metric_name}")
            return approval_id

        except Exception as e:
            logger.error(f"Failed to create approval request: {e}")
            return None

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        Get all pending approval requests.

        Returns:
            List of pending approval dicts
        """
        if not self.enabled or not self.database:
            return []

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT * FROM dims_pending_approvals
                ORDER BY requested_at DESC
            """

            cursor.execute(query)

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

            logger.debug(f"Retrieved {len(results)} pending approvals")
            return results

        except Exception as e:
            logger.error(f"Failed to get pending approvals: {e}")
            return []

    def get_approval(self, approval_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific approval request.

        Args:
            approval_id: Approval request ID

        Returns:
            Approval dict or None
        """
        if not self.enabled or not self.database:
            return None

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    id, metric_category, metric_name, old_value, new_value,
                    drift_pct, status, severity, requested_by, requested_at,
                    reviewed_by, reviewed_at, review_notes, auto_applied
                FROM dims_approval_log
                WHERE id = %s
            """

            cursor.execute(query, (approval_id,))

            # Get column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch row
            row = cursor.fetchone()

            cursor.close()
            self.database.return_connection(conn)

            if row:
                return dict(zip(columns, row))
            return None

        except Exception as e:
            logger.error(f"Failed to get approval: {e}")
            return None

    def approve(
        self,
        approval_id: int,
        reviewed_by: str,
        review_notes: Optional[str] = None,
        auto_apply: bool = True
    ) -> bool:
        """
        Approve a metric change.

        Args:
            approval_id: Approval request ID
            reviewed_by: Who reviewed/approved
            review_notes: Optional review notes
            auto_apply: Whether to automatically apply the change

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.database:
            return False

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            query = """
                UPDATE dims_approval_log
                SET status = 'approved',
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    review_notes = %s,
                    auto_applied = %s
                WHERE id = %s
                  AND status = 'pending'
                RETURNING metric_category, metric_name, new_value
            """

            cursor.execute(query, (reviewed_by, review_notes, auto_apply, approval_id))

            result = cursor.fetchone()

            if not result:
                logger.warning(f"Approval {approval_id} not found or already processed")
                cursor.close()
                self.database.return_connection(conn)
                return False

            metric_category, metric_name, new_value = result

            conn.commit()
            cursor.close()
            self.database.return_connection(conn)

            logger.info(f"Approval {approval_id} approved by {reviewed_by}: {metric_category}.{metric_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to approve request: {e}")
            return False

    def reject(
        self,
        approval_id: int,
        reviewed_by: str,
        review_notes: Optional[str] = None
    ) -> bool:
        """
        Reject a metric change.

        Args:
            approval_id: Approval request ID
            reviewed_by: Who reviewed/rejected
            review_notes: Optional review notes

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.database:
            return False

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            query = """
                UPDATE dims_approval_log
                SET status = 'rejected',
                    reviewed_by = %s,
                    reviewed_at = NOW(),
                    review_notes = %s
                WHERE id = %s
                  AND status = 'pending'
                RETURNING metric_category, metric_name
            """

            cursor.execute(query, (reviewed_by, review_notes, approval_id))

            result = cursor.fetchone()

            if not result:
                logger.warning(f"Approval {approval_id} not found or already processed")
                cursor.close()
                self.database.return_connection(conn)
                return False

            metric_category, metric_name = result

            conn.commit()
            cursor.close()
            self.database.return_connection(conn)

            logger.info(f"Approval {approval_id} rejected by {reviewed_by}: {metric_category}.{metric_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to reject request: {e}")
            return False

    def get_approval_history(
        self,
        metric_category: Optional[str] = None,
        metric_name: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get approval history.

        Args:
            metric_category: Filter by category (optional)
            metric_name: Filter by metric name (optional)
            days: Number of days to look back

        Returns:
            List of approval records
        """
        if not self.enabled or not self.database:
            return []

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            # Build query based on filters
            query = """
                SELECT
                    id, metric_category, metric_name, old_value, new_value,
                    drift_pct, status, severity, requested_by, requested_at,
                    reviewed_by, reviewed_at, review_notes
                FROM dims_approval_log
                WHERE requested_at >= NOW() - INTERVAL '%s days'
            """

            params = [days]

            if metric_category:
                query += " AND metric_category = %s"
                params.append(metric_category)

            if metric_name:
                query += " AND metric_name = %s"
                params.append(metric_name)

            query += " ORDER BY requested_at DESC"

            cursor.execute(query, tuple(params))

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

            logger.debug(f"Retrieved {len(results)} approval history records")
            return results

        except Exception as e:
            logger.error(f"Failed to get approval history: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get approval workflow statistics.

        Returns:
            Dict with approval stats
        """
        if not self.enabled or not self.database:
            return {
                'enabled': False,
                'total': 0,
                'pending': 0,
                'approved': 0,
                'rejected': 0
            }

        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'pending') AS pending,
                    COUNT(*) FILTER (WHERE status = 'approved') AS approved,
                    COUNT(*) FILTER (WHERE status = 'rejected') AS rejected,
                    COUNT(*) AS total
                FROM dims_approval_log
                WHERE requested_at >= NOW() - INTERVAL '30 days'
            """

            cursor.execute(query)
            result = cursor.fetchone()

            cursor.close()
            self.database.return_connection(conn)

            if result:
                pending, approved, rejected, total = result
                return {
                    'enabled': True,
                    'total': total,
                    'pending': pending,
                    'approved': approved,
                    'rejected': rejected,
                    'critical_metrics_count': len(self.critical_metrics),
                    'approval_threshold_pct': self.approval_threshold
                }

            return {
                'enabled': True,
                'total': 0,
                'pending': 0,
                'approved': 0,
                'rejected': 0
            }

        except Exception as e:
            logger.error(f"Failed to get approval stats: {e}")
            return {
                'enabled': True,
                'total': 0,
                'pending': 0,
                'approved': 0,
                'rejected': 0,
                'error': str(e)
            }

"""
Alert History & Resolution Tracking

Tracks alert lifecycle and resolution history:
- Alert creation and resolution
- Resolution tracking
- History queries
- Performance metrics

Created: November 5, 2025
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from ...database import get_database_connection
from ...utils import setup_logging


class ResolutionStatus(Enum):
    """Alert resolution statuses"""

    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


@dataclass
class AlertResolution:
    """
    Alert resolution record.

    Attributes:
        alert_id: Alert identifier
        status: Resolution status
        resolved_by: Who resolved it
        resolved_at: When resolved
        resolution_time_minutes: Time to resolve
        notes: Resolution notes
    """

    alert_id: str
    status: ResolutionStatus
    resolved_by: str
    resolved_at: datetime
    resolution_time_minutes: float
    notes: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "status": self.status.value,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat(),
            "resolution_time_minutes": self.resolution_time_minutes,
            "notes": self.notes,
        }


@dataclass
class AlertHistoryEntry:
    """
    Historical alert record.

    Attributes:
        alert_id: Unique identifier
        alert_type: Type of alert
        severity: Severity level
        message: Alert message
        created_at: Creation timestamp
        resolved_at: Resolution timestamp
        resolution_time_minutes: Time to resolve
        escalation_level: Final escalation level
        notifications_sent: Number of notifications
        resolution: Resolution record
    """

    alert_id: str
    alert_type: str
    severity: str
    message: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_time_minutes: Optional[float] = None
    escalation_level: str = "level_1"
    notifications_sent: int = 0
    resolution: Optional[AlertResolution] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_time_minutes": self.resolution_time_minutes,
            "escalation_level": self.escalation_level,
            "notifications_sent": self.notifications_sent,
            "resolution": self.resolution.to_dict() if self.resolution else None,
        }


class AlertHistory:
    """
    Manages alert history and resolution tracking.

    Features:
    - Database persistence
    - Resolution tracking
    - Performance metrics
    - Historical queries
    - Statistics
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize alert history.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or setup_logging("nba_simulator.monitoring.alerts.history")

        try:
            self.db_conn = get_database_connection()
        except Exception as e:
            self.logger.warning(f"Could not connect to database: {e}")
            self.db_conn = None

        # In-memory cache for recent alerts
        self.recent_alerts: Dict[str, AlertHistoryEntry] = {}

    def record_alert(
        self, alert_id: str, alert_type: str, severity: str, message: str, **metadata
    ):
        """
        Record new alert in history.

        Args:
            alert_id: Unique alert identifier
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
            **metadata: Additional metadata
        """
        entry = AlertHistoryEntry(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            created_at=datetime.now(timezone.utc),
        )

        # Add to cache
        self.recent_alerts[alert_id] = entry

        # Persist to database
        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO alert_history (
                            alert_id, alert_type, severity, message,
                            created_at, escalation_level
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (alert_id) DO NOTHING
                    """,
                        (
                            alert_id,
                            alert_type,
                            severity,
                            message,
                            entry.created_at,
                            entry.escalation_level,
                        ),
                    )
                self.db_conn.commit()
            except Exception as e:
                self.logger.error(f"Error recording alert: {e}")

        self.logger.info(f"Recorded alert: {alert_id} [{severity}]")

    def record_notification(self, alert_id: str):
        """
        Record that a notification was sent.

        Args:
            alert_id: Alert identifier
        """
        if alert_id in self.recent_alerts:
            self.recent_alerts[alert_id].notifications_sent += 1

        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE alert_history
                        SET notifications_sent = notifications_sent + 1
                        WHERE alert_id = %s
                    """,
                        (alert_id,),
                    )
                self.db_conn.commit()
            except Exception as e:
                self.logger.error(f"Error recording notification: {e}")

    def record_escalation(self, alert_id: str, escalation_level: str):
        """
        Record alert escalation.

        Args:
            alert_id: Alert identifier
            escalation_level: New escalation level
        """
        if alert_id in self.recent_alerts:
            self.recent_alerts[alert_id].escalation_level = escalation_level

        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE alert_history
                        SET escalation_level = %s
                        WHERE alert_id = %s
                    """,
                        (escalation_level, alert_id),
                    )
                self.db_conn.commit()
            except Exception as e:
                self.logger.error(f"Error recording escalation: {e}")

    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        status: ResolutionStatus = ResolutionStatus.RESOLVED,
        notes: str = "",
    ):
        """
        Mark alert as resolved.

        Args:
            alert_id: Alert identifier
            resolved_by: Who resolved it
            status: Resolution status
            notes: Resolution notes
        """
        resolved_at = datetime.now(timezone.utc)

        # Calculate resolution time
        resolution_time = None
        if alert_id in self.recent_alerts:
            entry = self.recent_alerts[alert_id]
            resolution_time = (resolved_at - entry.created_at).total_seconds() / 60

            entry.resolved_at = resolved_at
            entry.resolution_time_minutes = resolution_time
            entry.resolution = AlertResolution(
                alert_id=alert_id,
                status=status,
                resolved_by=resolved_by,
                resolved_at=resolved_at,
                resolution_time_minutes=resolution_time,
                notes=notes,
            )

        # Update database
        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE alert_history
                        SET resolved_at = %s,
                            resolution_time_minutes = %s,
                            resolution_status = %s,
                            resolved_by = %s,
                            resolution_notes = %s
                        WHERE alert_id = %s
                    """,
                        (
                            resolved_at,
                            resolution_time,
                            status.value,
                            resolved_by,
                            notes,
                            alert_id,
                        ),
                    )
                self.db_conn.commit()
            except Exception as e:
                self.logger.error(f"Error resolving alert: {e}")

        self.logger.info(
            f"Resolved alert {alert_id} in {resolution_time:.1f}min"
            if resolution_time
            else f"Resolved alert {alert_id}"
        )

    def get_alert(self, alert_id: str) -> Optional[AlertHistoryEntry]:
        """
        Get alert from history.

        Args:
            alert_id: Alert identifier

        Returns:
            AlertHistoryEntry if found
        """
        # Check cache first
        if alert_id in self.recent_alerts:
            return self.recent_alerts[alert_id]

        # Query database
        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT alert_id, alert_type, severity, message,
                               created_at, resolved_at, resolution_time_minutes,
                               escalation_level, notifications_sent
                        FROM alert_history
                        WHERE alert_id = %s
                    """,
                        (alert_id,),
                    )

                    row = cur.fetchone()

                if row:
                    return AlertHistoryEntry(
                        alert_id=row[0],
                        alert_type=row[1],
                        severity=row[2],
                        message=row[3],
                        created_at=row[4],
                        resolved_at=row[5],
                        resolution_time_minutes=row[6],
                        escalation_level=row[7],
                        notifications_sent=row[8],
                    )
            except Exception as e:
                self.logger.error(f"Error getting alert: {e}")

        return None

    def get_active_alerts(self) -> List[AlertHistoryEntry]:
        """
        Get all active (unresolved) alerts.

        Returns:
            List of active alerts
        """
        alerts = []

        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT alert_id, alert_type, severity, message,
                               created_at, escalation_level, notifications_sent
                        FROM alert_history
                        WHERE resolved_at IS NULL
                        ORDER BY created_at DESC
                    """
                    )

                    for row in cur.fetchall():
                        alerts.append(
                            AlertHistoryEntry(
                                alert_id=row[0],
                                alert_type=row[1],
                                severity=row[2],
                                message=row[3],
                                created_at=row[4],
                                escalation_level=row[5],
                                notifications_sent=row[6],
                            )
                        )
            except Exception as e:
                self.logger.error(f"Error getting active alerts: {e}")

        return alerts

    def get_statistics(self, hours: int = 24) -> Dict:
        """
        Get alert statistics.

        Args:
            hours: Time window in hours

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_alerts": 0,
            "active_alerts": 0,
            "resolved_alerts": 0,
            "avg_resolution_time_minutes": 0,
            "by_severity": {},
            "by_type": {},
        }

        if not self.db_conn:
            return stats

        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

            with self.db_conn.cursor() as cur:
                # Total counts
                cur.execute(
                    """
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN resolved_at IS NULL THEN 1 END) as active,
                        COUNT(CASE WHEN resolved_at IS NOT NULL THEN 1 END) as resolved
                    FROM alert_history
                    WHERE created_at >= %s
                """,
                    (cutoff,),
                )

                row = cur.fetchone()
                stats["total_alerts"] = row[0]
                stats["active_alerts"] = row[1]
                stats["resolved_alerts"] = row[2]

                # Average resolution time
                cur.execute(
                    """
                    SELECT AVG(resolution_time_minutes)
                    FROM alert_history
                    WHERE created_at >= %s AND resolution_time_minutes IS NOT NULL
                """,
                    (cutoff,),
                )

                avg_time = cur.fetchone()[0]
                stats["avg_resolution_time_minutes"] = (
                    float(avg_time) if avg_time else 0
                )

                # By severity
                cur.execute(
                    """
                    SELECT severity, COUNT(*)
                    FROM alert_history
                    WHERE created_at >= %s
                    GROUP BY severity
                """,
                    (cutoff,),
                )

                stats["by_severity"] = {row[0]: row[1] for row in cur.fetchall()}

                # By type
                cur.execute(
                    """
                    SELECT alert_type, COUNT(*)
                    FROM alert_history
                    WHERE created_at >= %s
                    GROUP BY alert_type
                """,
                    (cutoff,),
                )

                stats["by_type"] = {row[0]: row[1] for row in cur.fetchall()}

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")

        return stats

"""
Base Quality Monitor

Core abstractions for quality monitoring system.
Provides base classes and data structures for all quality checks.

Created: November 5, 2025
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

from ...utils import setup_logging


class QualityStatus(Enum):
    """Quality check status levels"""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    ERROR = "error"
    UNKNOWN = "unknown"


class QualitySeverity(Enum):
    """Severity levels for quality issues"""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QualityMetric:
    """
    Quality metric data structure.

    Attributes:
        metric_name: Name of the quality metric
        metric_value: Numeric value of the metric
        metric_type: Type/category of metric
        status: Quality status (PASS/WARNING/FAIL)
        severity: Severity level if there's an issue
        threshold: Expected threshold value
        timestamp: When metric was measured
        details: Additional context/details
    """

    metric_name: str
    metric_value: float
    metric_type: str
    status: QualityStatus
    severity: QualitySeverity = QualitySeverity.INFO
    threshold: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "metric_type": self.metric_type,
            "status": self.status.value,
            "severity": self.severity.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


@dataclass
class QualityCheck:
    """
    Quality check result.

    Attributes:
        check_name: Name of the quality check
        check_type: Type/category of check
        status: Overall status of check
        metrics: List of metrics measured
        passed: Number of passed checks
        failed: Number of failed checks
        warnings: Number of warnings
        timestamp: When check was performed
        duration_seconds: How long check took
        message: Summary message
    """

    check_name: str
    check_type: str
    status: QualityStatus
    metrics: List[QualityMetric] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: float = 0.0
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "check_name": self.check_name,
            "check_type": self.check_type,
            "status": self.status.value,
            "metrics": [m.to_dict() for m in self.metrics],
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "message": self.message,
        }


@dataclass
class QualityAlert:
    """
    Quality alert for issues requiring attention.

    Attributes:
        alert_type: Type of alert
        severity: Severity level
        message: Alert message
        metric: Associated metric (if any)
        timestamp: When alert was created
        resolved: Whether alert has been resolved
        resolved_at: When alert was resolved
    """

    alert_type: str
    severity: QualitySeverity
    message: str
    metric: Optional[QualityMetric] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "message": self.message,
            "metric": self.metric.to_dict() if self.metric else None,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class QualityMonitor:
    """
    Base quality monitoring class.

    Provides common functionality for all quality monitors:
    - Check execution
    - Metric tracking
    - Alert management
    - Database logging
    """

    def __init__(self, monitor_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize quality monitor.

        Args:
            monitor_name: Name of this monitor
            logger: Optional logger instance
        """
        self.monitor_name = monitor_name
        self.logger = logger or setup_logging(
            f"nba_simulator.monitoring.quality.{monitor_name}"
        )

        # Tracking
        self.checks: List[QualityCheck] = []
        self.metrics: List[QualityMetric] = []
        self.alerts: List[QualityAlert] = []

        self.logger.info(f"Quality monitor '{monitor_name}' initialized")

    def log_metric(self, metric: QualityMetric):
        """
        Log a quality metric.

        Args:
            metric: Quality metric to log
        """
        self.metrics.append(metric)

        # Log based on status
        if metric.status == QualityStatus.FAIL:
            self.logger.error(
                f"Quality metric FAILED: {metric.metric_name}={metric.metric_value} "
                f"(threshold={metric.threshold}) - {metric.details}"
            )
        elif metric.status == QualityStatus.WARNING:
            self.logger.warning(
                f"Quality metric WARNING: {metric.metric_name}={metric.metric_value} "
                f"(threshold={metric.threshold}) - {metric.details}"
            )
        else:
            self.logger.debug(
                f"Quality metric: {metric.metric_name}={metric.metric_value}"
            )

    def create_alert(
        self,
        alert_type: str,
        severity: QualitySeverity,
        message: str,
        metric: Optional[QualityMetric] = None,
    ) -> QualityAlert:
        """
        Create a quality alert.

        Args:
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
            metric: Associated metric

        Returns:
            Created quality alert
        """
        alert = QualityAlert(
            alert_type=alert_type, severity=severity, message=message, metric=metric
        )

        self.alerts.append(alert)

        # Log alert
        self.logger.warning(
            f"🚨 QUALITY ALERT [{severity.value.upper()}] {alert_type}: {message}"
        )

        return alert

    def get_active_alerts(self) -> List[QualityAlert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of quality monitoring.

        Returns:
            Dictionary with summary statistics
        """
        total_checks = len(self.checks)
        total_metrics = len(self.metrics)
        active_alerts = len(self.get_active_alerts())

        # Status breakdown
        status_counts = {
            "passed": sum(1 for m in self.metrics if m.status == QualityStatus.PASS),
            "warnings": sum(
                1 for m in self.metrics if m.status == QualityStatus.WARNING
            ),
            "failed": sum(1 for m in self.metrics if m.status == QualityStatus.FAIL),
            "errors": sum(1 for m in self.metrics if m.status == QualityStatus.ERROR),
        }

        return {
            "monitor_name": self.monitor_name,
            "total_checks": total_checks,
            "total_metrics": total_metrics,
            "active_alerts": active_alerts,
            "status_counts": status_counts,
            "last_check": (
                self.checks[-1].timestamp.isoformat() if self.checks else None
            ),
        }


class BaseQualityChecker:
    """
    Base class for specific quality checkers.

    Provides template method pattern for quality checks.
    """

    def __init__(self, checker_name: str, monitor: QualityMonitor):
        """
        Initialize quality checker.

        Args:
            checker_name: Name of this checker
            monitor: Parent quality monitor
        """
        self.checker_name = checker_name
        self.monitor = monitor
        self.logger = monitor.logger

    def run_check(self) -> QualityCheck:
        """
        Run quality check (template method).

        Returns:
            Quality check result
        """
        start_time = datetime.now(timezone.utc)

        self.logger.info(f"Running quality check: {self.checker_name}")

        try:
            # Perform actual check (implemented by subclasses)
            check_result = self._perform_check()

            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            check_result.duration_seconds = duration

            # Log result
            self.monitor.checks.append(check_result)

            self.logger.info(
                f"Quality check completed: {self.checker_name} - "
                f"Status: {check_result.status.value}, Duration: {duration:.2f}s"
            )

            return check_result

        except Exception as e:
            self.logger.error(f"Quality check failed: {self.checker_name} - {str(e)}")

            # Create error check result
            check_result = QualityCheck(
                check_name=self.checker_name,
                check_type="error",
                status=QualityStatus.ERROR,
                message=f"Check failed: {str(e)}",
            )

            self.monitor.checks.append(check_result)
            return check_result

    def _perform_check(self) -> QualityCheck:
        """
        Perform actual quality check.

        Must be implemented by subclasses.

        Returns:
            Quality check result
        """
        raise NotImplementedError("Subclasses must implement _perform_check()")

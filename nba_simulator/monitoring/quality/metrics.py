"""
Quality Metrics Tracker

Tracks quality metrics over time, calculates trends, and manages thresholds.
Provides historical analysis and trend detection.

Created: November 5, 2025
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import statistics

from .base import QualityMetric, QualityStatus, QualitySeverity
from ...database import get_database_connection


@dataclass
class QualityThreshold:
    """
    Quality metric threshold configuration.

    Attributes:
        metric_name: Name of the metric
        warning_threshold: Value at which to issue warning
        critical_threshold: Value at which to issue critical alert
        comparison: How to compare (gt, lt, gte, lte, eq)
        window_minutes: Time window for trend analysis
    """

    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "gt"  # gt, lt, gte, lte, eq
    window_minutes: int = 60


@dataclass
class MetricTrend:
    """
    Trend analysis for a quality metric.

    Attributes:
        metric_name: Name of the metric
        current_value: Current metric value
        previous_value: Previous metric value
        percent_change: Percentage change
        trend_direction: up, down, stable
        is_improving: Whether trend is improving
        samples: Number of samples analyzed
    """

    metric_name: str
    current_value: float
    previous_value: float
    percent_change: float
    trend_direction: str
    is_improving: bool
    samples: int


class QualityMetricsTracker:
    """
    Tracks quality metrics over time and performs trend analysis.

    Provides:
    - Metric history storage
    - Trend calculation
    - Threshold evaluation
    - Historical analysis
    - Anomaly detection
    """

    def __init__(self):
        """Initialize metrics tracker"""
        self.thresholds: Dict[str, QualityThreshold] = {}
        self.db_conn = None

        try:
            self.db_conn = get_database_connection()
        except Exception:
            pass

    def register_threshold(self, threshold: QualityThreshold):
        """
        Register a quality threshold.

        Args:
            threshold: Threshold configuration
        """
        self.thresholds[threshold.metric_name] = threshold

    def evaluate_metric(
        self, metric: QualityMetric
    ) -> Tuple[QualityStatus, QualitySeverity]:
        """
        Evaluate a metric against its threshold.

        Args:
            metric: Quality metric to evaluate

        Returns:
            Tuple of (status, severity)
        """
        threshold = self.thresholds.get(metric.metric_name)

        if not threshold:
            return QualityStatus.PASS, QualitySeverity.INFO

        value = metric.metric_value

        # Compare based on comparison type
        if threshold.comparison in ["gt", "gte"]:
            # Higher is worse
            if value >= threshold.critical_threshold:
                return QualityStatus.FAIL, QualitySeverity.CRITICAL
            elif value >= threshold.warning_threshold:
                return QualityStatus.WARNING, QualitySeverity.MEDIUM

        elif threshold.comparison in ["lt", "lte"]:
            # Lower is worse
            if value <= threshold.critical_threshold:
                return QualityStatus.FAIL, QualitySeverity.CRITICAL
            elif value <= threshold.warning_threshold:
                return QualityStatus.WARNING, QualitySeverity.MEDIUM

        return QualityStatus.PASS, QualitySeverity.INFO

    def store_metric(self, metric: QualityMetric) -> bool:
        """
        Store metric in database.

        Args:
            metric: Quality metric to store

        Returns:
            True if successful, False otherwise
        """
        if not self.db_conn:
            return False

        try:
            with self.db_conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO quality_metrics (
                        metric_name,
                        metric_value,
                        metric_type,
                        status,
                        severity,
                        threshold,
                        recorded_at,
                        details
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        metric.metric_name,
                        metric.metric_value,
                        metric.metric_type,
                        metric.status.value,
                        metric.severity.value,
                        metric.threshold,
                        metric.timestamp,
                        metric.details,
                    ),
                )

            self.db_conn.commit()
            return True

        except Exception:
            return False

    def get_metric_history(
        self, metric_name: str, hours: int = 24
    ) -> List[QualityMetric]:
        """
        Get historical values for a metric.

        Args:
            metric_name: Name of the metric
            hours: Number of hours of history to retrieve

        Returns:
            List of quality metrics
        """
        if not self.db_conn:
            return []

        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

            with self.db_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        metric_name,
                        metric_value,
                        metric_type,
                        status,
                        severity,
                        threshold,
                        recorded_at,
                        details
                    FROM quality_metrics
                    WHERE metric_name = %s
                      AND recorded_at >= %s
                    ORDER BY recorded_at ASC
                """,
                    (metric_name, cutoff_time),
                )

                rows = cur.fetchall()

            metrics = []
            for row in rows:
                metric = QualityMetric(
                    metric_name=row[0],
                    metric_value=float(row[1]),
                    metric_type=row[2],
                    status=QualityStatus(row[3]),
                    severity=QualitySeverity(row[4]),
                    threshold=float(row[5]) if row[5] else None,
                    timestamp=row[6],
                    details=row[7] or "",
                )
                metrics.append(metric)

            return metrics

        except Exception:
            return []

    def calculate_trend(
        self, metric_name: str, hours: int = 24
    ) -> Optional[MetricTrend]:
        """
        Calculate trend for a metric.

        Args:
            metric_name: Name of the metric
            hours: Number of hours to analyze

        Returns:
            MetricTrend if enough data, None otherwise
        """
        history = self.get_metric_history(metric_name, hours)

        if len(history) < 2:
            return None

        # Get current and previous values
        current_value = history[-1].metric_value
        previous_value = history[0].metric_value

        # Calculate percent change
        if previous_value != 0:
            percent_change = ((current_value - previous_value) / previous_value) * 100
        else:
            percent_change = 0.0

        # Determine trend direction
        if abs(percent_change) < 1.0:
            trend_direction = "stable"
        elif percent_change > 0:
            trend_direction = "up"
        else:
            trend_direction = "down"

        # Determine if improving (depends on metric type)
        # For most metrics, lower is better
        is_improving = current_value < previous_value

        return MetricTrend(
            metric_name=metric_name,
            current_value=current_value,
            previous_value=previous_value,
            percent_change=percent_change,
            trend_direction=trend_direction,
            is_improving=is_improving,
            samples=len(history),
        )

    def detect_anomalies(
        self, metric_name: str, hours: int = 24, std_threshold: float = 2.0
    ) -> List[QualityMetric]:
        """
        Detect anomalous metric values using standard deviation.

        Args:
            metric_name: Name of the metric
            hours: Number of hours to analyze
            std_threshold: Number of standard deviations for anomaly

        Returns:
            List of anomalous metrics
        """
        history = self.get_metric_history(metric_name, hours)

        if len(history) < 10:
            return []

        # Calculate mean and standard deviation
        values = [m.metric_value for m in history]
        mean = statistics.mean(values)
        stdev = statistics.stdev(values)

        # Find anomalies
        anomalies = []
        for metric in history:
            z_score = abs((metric.metric_value - mean) / stdev) if stdev > 0 else 0
            if z_score > std_threshold:
                anomalies.append(metric)

        return anomalies

    def get_summary_statistics(
        self, metric_name: str, hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get summary statistics for a metric.

        Args:
            metric_name: Name of the metric
            hours: Number of hours to analyze

        Returns:
            Dictionary with statistics
        """
        history = self.get_metric_history(metric_name, hours)

        if not history:
            return {}

        values = [m.metric_value for m in history]

        stats = {
            "metric_name": metric_name,
            "sample_count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "current": history[-1].metric_value,
        }

        if len(values) >= 2:
            stats["stdev"] = statistics.stdev(values)

        # Status breakdown
        status_counts = {}
        for status in QualityStatus:
            count = sum(1 for m in history if m.status == status)
            if count > 0:
                status_counts[status.value] = count

        stats["status_breakdown"] = status_counts

        return stats

    def get_all_metrics_summary(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """
        Get summary for all tracked metrics.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary of {metric_name: statistics}
        """
        if not self.db_conn:
            return {}

        try:
            # Get unique metric names
            with self.db_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT metric_name
                    FROM quality_metrics
                    WHERE recorded_at >= %s
                """,
                    (datetime.now(timezone.utc) - timedelta(hours=hours),),
                )

                metric_names = [row[0] for row in cur.fetchall()]

            # Get summary for each metric
            summaries = {}
            for metric_name in metric_names:
                summaries[metric_name] = self.get_summary_statistics(metric_name, hours)

            return summaries

        except Exception:
            return {}

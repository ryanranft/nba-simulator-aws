"""
Data Quality Checker

Comprehensive data quality checks for NBA data pipeline:
- File count monitoring and anomaly detection
- JSON validation
- Data freshness checks
- Schema validation
- Data completeness checks

Migrated from: scripts/monitoring/data_quality_monitor.py
Enhanced with better error handling, type safety, and integration

Created: November 5, 2025
"""

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import boto3
from botocore.exceptions import ClientError

from .base import (
    QualityMonitor,
    QualityStatus,
    QualityMetric,
    QualityCheck,
    QualitySeverity,
    BaseQualityChecker,
)
from ...database import get_database_connection


@dataclass
class DataQualityConfig:
    """
    Configuration for data quality checks.

    Attributes:
        s3_bucket: S3 bucket name for data lake
        file_count_threshold: % change threshold for file count alerts
        json_quality_threshold: Minimum % of valid JSON files
        freshness_days_threshold: Maximum days since latest data
        sample_size: Number of files to sample for validation
        enable_s3_checks: Enable S3-based quality checks
        enable_db_checks: Enable database quality checks
    """

    s3_bucket: str = "nba-sim-raw-data-lake"
    file_count_threshold: float = 10.0  # 10% change alert
    json_quality_threshold: float = 95.0  # 95% valid JSON
    freshness_days_threshold: int = 3  # 3 days max staleness
    sample_size: int = 50  # Sample 50 files
    enable_s3_checks: bool = True
    enable_db_checks: bool = True


class DataQualityChecker(BaseQualityChecker):
    """
    Comprehensive data quality checker for NBA data.

    Performs multiple quality checks:
    - File count monitoring
    - JSON validation
    - Data freshness
    - Schema validation (future)
    - Completeness checks (future)
    """

    def __init__(
        self, monitor: QualityMonitor, config: Optional[DataQualityConfig] = None
    ):
        """
        Initialize data quality checker.

        Args:
            monitor: Parent quality monitor
            config: Quality check configuration
        """
        super().__init__("data_quality", monitor)

        self.config = config or DataQualityConfig()

        # AWS clients
        if self.config.enable_s3_checks:
            try:
                self.s3_client = boto3.client("s3")
            except Exception as e:
                self.logger.warning(f"Could not initialize S3 client: {e}")
                self.s3_client = None
        else:
            self.s3_client = None

        # Database connection
        if self.config.enable_db_checks:
            try:
                self.db_conn = get_database_connection()
            except Exception as e:
                self.logger.warning(f"Could not get database connection: {e}")
                self.db_conn = None
        else:
            self.db_conn = None

    def _perform_check(self) -> QualityCheck:
        """
        Perform comprehensive quality checks.

        Returns:
            Quality check result with all metrics
        """
        metrics = []
        passed = 0
        failed = 0
        warnings = 0

        # Run all quality checks
        checks_to_run = [
            ("file_counts", self._check_file_counts),
            ("json_quality", self._check_json_quality),
            ("data_freshness", self._check_data_freshness),
        ]

        if self.db_conn:
            checks_to_run.append(("database_quality", self._check_database_quality))

        for check_name, check_func in checks_to_run:
            try:
                check_metrics = check_func()
                metrics.extend(check_metrics)

                # Count statuses
                for metric in check_metrics:
                    if metric.status == QualityStatus.PASS:
                        passed += 1
                    elif metric.status == QualityStatus.WARNING:
                        warnings += 1
                    elif metric.status == QualityStatus.FAIL:
                        failed += 1

            except Exception as e:
                self.logger.error(f"Error in {check_name}: {str(e)}")
                failed += 1

        # Determine overall status
        if failed > 0:
            status = QualityStatus.FAIL
        elif warnings > 0:
            status = QualityStatus.WARNING
        else:
            status = QualityStatus.PASS

        return QualityCheck(
            check_name="data_quality_check",
            check_type="comprehensive",
            status=status,
            metrics=metrics,
            passed=passed,
            failed=failed,
            warnings=warnings,
            message=f"Completed {len(checks_to_run)} quality checks: "
            f"{passed} passed, {warnings} warnings, {failed} failed",
        )

    def _check_file_counts(self) -> List[QualityMetric]:
        """
        Check S3 file counts and detect anomalies.

        Returns:
            List of file count quality metrics
        """
        if not self.s3_client:
            return []

        self.logger.info("Checking file counts...")

        metrics = []

        try:
            file_counts = self._get_file_counts()

            for data_type, counts in file_counts.items():
                # Create metric for file count
                metric = QualityMetric(
                    metric_name=f"{data_type}_file_count",
                    metric_value=counts["count"],
                    metric_type="file_count",
                    status=QualityStatus.PASS,
                    details=f"Size: {counts['size_gb']:.2f} GB",
                )

                metrics.append(metric)
                self.monitor.log_metric(metric)

                # Check for anomalies
                anomaly_metric = self._check_file_count_anomaly(
                    data_type, counts["count"]
                )
                if anomaly_metric:
                    metrics.append(anomaly_metric)
                    self.monitor.log_metric(anomaly_metric)

            self.logger.info(
                f"File count check complete: {len(file_counts)} data types"
            )

        except Exception as e:
            self.logger.error(f"Error checking file counts: {str(e)}")
            raise

        return metrics

    def _get_file_counts(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current file counts from S3.

        Returns:
            Dictionary of {data_type: {count, size_gb}}
        """
        file_counts = {}

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.config.s3_bucket)

            for page in pages:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]
                    size = obj["Size"]

                    # Extract data type from path
                    if "/" in key:
                        data_type = key.split("/")[0]
                    else:
                        data_type = "root"

                    if data_type not in file_counts:
                        file_counts[data_type] = {"count": 0, "size": 0}

                    file_counts[data_type]["count"] += 1
                    file_counts[data_type]["size"] += size

            # Convert sizes to GB
            for data_type in file_counts:
                file_counts[data_type]["size_gb"] = file_counts[data_type]["size"] / (
                    1024**3
                )

        except ClientError as e:
            self.logger.error(f"S3 error getting file counts: {str(e)}")
            raise

        return file_counts

    def _check_file_count_anomaly(
        self, data_type: str, current_count: int
    ) -> Optional[QualityMetric]:
        """
        Check for file count anomalies vs historical data.

        Args:
            data_type: Type of data (e.g., 'schedule', 'boxscore')
            current_count: Current file count

        Returns:
            Quality metric if anomaly detected, None otherwise
        """
        if not self.db_conn:
            return None

        try:
            # Get previous file count from database
            with self.db_conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT metric_value
                    FROM dims_metrics_history
                    WHERE metric_name = %s
                    ORDER BY recorded_at DESC
                    LIMIT 1 OFFSET 1
                """,
                    (f"{data_type}_file_count",),
                )

                result = cur.fetchone()

            if result:
                previous_count = int(result[0])
                change_percent = (
                    (current_count - previous_count) / previous_count
                ) * 100

                # Check if change exceeds threshold
                if abs(change_percent) > self.config.file_count_threshold:
                    severity = (
                        QualitySeverity.CRITICAL
                        if change_percent < 0
                        else QualitySeverity.MEDIUM
                    )
                    status = (
                        QualityStatus.FAIL
                        if change_percent < 0
                        else QualityStatus.WARNING
                    )

                    metric = QualityMetric(
                        metric_name=f"{data_type}_file_count_change",
                        metric_value=change_percent,
                        metric_type="anomaly",
                        status=status,
                        severity=severity,
                        threshold=self.config.file_count_threshold,
                        details=f"File count changed by {change_percent:.1f}% "
                        f"({current_count - previous_count} files)",
                    )

                    # Create alert for significant changes
                    self.monitor.create_alert(
                        alert_type="file_count_anomaly",
                        severity=severity,
                        message=f"{data_type} files changed by {abs(change_percent):.1f}%",
                        metric=metric,
                    )

                    return metric

        except Exception as e:
            self.logger.error(f"Error checking file count anomaly: {str(e)}")

        return None

    def _check_json_quality(self) -> List[QualityMetric]:
        """
        Check JSON file quality by sampling and validation.

        Returns:
            List of JSON quality metrics
        """
        if not self.s3_client:
            return []

        self.logger.info("Checking JSON quality...")

        metrics = []

        try:
            # Get sample of JSON files
            json_files = self._get_json_files_sample()

            if not json_files:
                self.logger.warning("No JSON files found for quality check")
                return metrics

            valid_count = 0
            invalid_count = 0
            empty_count = 0

            for file_path in json_files:
                try:
                    response = self.s3_client.get_object(
                        Bucket=self.config.s3_bucket, Key=file_path
                    )
                    content = response["Body"].read()

                    if len(content) == 0:
                        empty_count += 1
                        continue

                    json.loads(content.decode("utf-8"))
                    valid_count += 1

                except Exception:
                    invalid_count += 1

            # Calculate quality percentage
            total_sampled = len(json_files)
            valid_percent = (
                (valid_count / total_sampled) * 100 if total_sampled > 0 else 0
            )

            # Determine status
            if valid_percent >= self.config.json_quality_threshold:
                status = QualityStatus.PASS
                severity = QualitySeverity.INFO
            elif valid_percent >= 85:
                status = QualityStatus.WARNING
                severity = QualitySeverity.MEDIUM
            else:
                status = QualityStatus.FAIL
                severity = QualitySeverity.HIGH

            metric = QualityMetric(
                metric_name="json_quality_percent",
                metric_value=valid_percent,
                metric_type="validation",
                status=status,
                severity=severity,
                threshold=self.config.json_quality_threshold,
                details=f"Valid: {valid_count}, Invalid: {invalid_count}, "
                f"Empty: {empty_count} (Sample: {total_sampled})",
            )

            metrics.append(metric)
            self.monitor.log_metric(metric)

            # Create alert if quality is poor
            if status != QualityStatus.PASS:
                self.monitor.create_alert(
                    alert_type="json_quality_degradation",
                    severity=severity,
                    message=f"JSON quality at {valid_percent:.1f}% "
                    f"(threshold: {self.config.json_quality_threshold}%)",
                    metric=metric,
                )

            self.logger.info(f"JSON quality: {valid_percent:.1f}% valid")

        except Exception as e:
            self.logger.error(f"Error checking JSON quality: {str(e)}")
            raise

        return metrics

    def _get_json_files_sample(self) -> List[str]:
        """
        Get random sample of JSON files from S3.

        Returns:
            List of S3 keys for JSON files
        """
        json_files = []

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.config.s3_bucket)

            for page in pages:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    if obj["Key"].endswith(".json"):
                        json_files.append(obj["Key"])

            # Random sample
            if len(json_files) > self.config.sample_size:
                json_files = random.sample(json_files, self.config.sample_size)

        except Exception as e:
            self.logger.error(f"Error getting JSON files sample: {str(e)}")
            raise

        return json_files

    def _check_data_freshness(self) -> List[QualityMetric]:
        """
        Check data freshness by examining recent file dates.

        Returns:
            List of data freshness metrics
        """
        if not self.s3_client:
            return []

        self.logger.info("Checking data freshness...")

        metrics = []

        try:
            # Check schedule files for recent dates
            recent_files = []

            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.config.s3_bucket, Prefix="schedule/")

            for page in pages:
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    if not obj["Key"].endswith(".json"):
                        continue

                    # Extract date from filename
                    filename = Path(obj["Key"]).stem

                    try:
                        if len(filename) == 8 and filename.isdigit():
                            file_date = datetime.strptime(filename, "%Y%m%d")
                            if file_date >= datetime.now() - timedelta(days=7):
                                recent_files.append(file_date)
                    except ValueError:
                        continue

            if recent_files:
                latest_date = max(recent_files)
                days_old = (datetime.now() - latest_date).days

                # Determine status
                if days_old <= self.config.freshness_days_threshold:
                    status = QualityStatus.PASS
                    severity = QualitySeverity.INFO
                elif days_old <= 7:
                    status = QualityStatus.WARNING
                    severity = QualitySeverity.MEDIUM
                else:
                    status = QualityStatus.FAIL
                    severity = QualitySeverity.HIGH

                metric = QualityMetric(
                    metric_name="data_freshness_days",
                    metric_value=days_old,
                    metric_type="freshness",
                    status=status,
                    severity=severity,
                    threshold=float(self.config.freshness_days_threshold),
                    details=f"Latest data: {latest_date.strftime('%Y-%m-%d')}",
                )

                metrics.append(metric)
                self.monitor.log_metric(metric)

                # Create alert if data is stale
                if status != QualityStatus.PASS:
                    self.monitor.create_alert(
                        alert_type="stale_data",
                        severity=severity,
                        message=f"Latest data is {days_old} days old",
                        metric=metric,
                    )

                self.logger.info(f"Data freshness: {days_old} days old")

            else:
                # No recent data found
                metric = QualityMetric(
                    metric_name="data_freshness_days",
                    metric_value=999,
                    metric_type="freshness",
                    status=QualityStatus.FAIL,
                    severity=QualitySeverity.CRITICAL,
                    details="No recent data found",
                )

                metrics.append(metric)
                self.monitor.log_metric(metric)

                self.monitor.create_alert(
                    alert_type="no_recent_data",
                    severity=QualitySeverity.CRITICAL,
                    message="No recent schedule data found",
                    metric=metric,
                )

                self.logger.warning("No recent data found")

        except Exception as e:
            self.logger.error(f"Error checking data freshness: {str(e)}")
            raise

        return metrics

    def _check_database_quality(self) -> List[QualityMetric]:
        """
        Check database data quality.

        Returns:
            List of database quality metrics
        """
        if not self.db_conn:
            return []

        self.logger.info("Checking database quality...")

        metrics = []

        try:
            # Check for null values in critical columns
            null_checks = {
                "games": ["game_id", "season", "game_date"],
                "players": ["player_id", "player_name"],
                "teams": ["team_id", "team_name"],
            }

            for table, columns in null_checks.items():
                for column in columns:
                    try:
                        with self.db_conn.cursor() as cur:
                            cur.execute(
                                f"""
                                SELECT COUNT(*) as total,
                                       SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) as null_count
                                FROM {table}
                            """
                            )
                            result = cur.fetchone()

                        if result:
                            total, null_count = result
                            null_percent = (
                                (null_count / total * 100) if total > 0 else 0
                            )

                            status = (
                                QualityStatus.FAIL
                                if null_percent > 5
                                else (
                                    QualityStatus.WARNING
                                    if null_percent > 1
                                    else QualityStatus.PASS
                                )
                            )

                            metric = QualityMetric(
                                metric_name=f"{table}_{column}_null_percent",
                                metric_value=null_percent,
                                metric_type="completeness",
                                status=status,
                                threshold=1.0,
                                details=f"{null_count}/{total} null values",
                            )

                            metrics.append(metric)
                            self.monitor.log_metric(metric)

                    except Exception as e:
                        self.logger.warning(
                            f"Could not check nulls for {table}.{column}: {str(e)}"
                        )

            self.logger.info(f"Database quality check complete: {len(metrics)} metrics")

        except Exception as e:
            self.logger.error(f"Error checking database quality: {str(e)}")
            raise

        return metrics

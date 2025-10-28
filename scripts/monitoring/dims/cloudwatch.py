"""
DIMS CloudWatch Integration
Publishes DIMS metrics to CloudWatch for monitoring and alerting.
Part of Phase 0.0020 (Monitoring & Observability).
"""

import boto3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional


logger = logging.getLogger(__name__)


class DIMSCloudWatchPublisher:
    """Publish DIMS metrics to CloudWatch"""

    def __init__(self, region="us-east-1", enabled=True):
        self.region = region
        self.enabled = enabled
        self._cloudwatch = None
        self.namespace = "NBA-Simulator/DIMS"

    @property
    def cloudwatch(self):
        """Lazy-load CloudWatch client"""
        if self._cloudwatch is None:
            self._cloudwatch = boto3.client("cloudwatch", region_name=self.region)
        return self._cloudwatch

    def publish_verification_results(self, metrics: Dict[str, Dict[str, Any]]) -> bool:
        """
        Publish DIMS verification results to CloudWatch

        Args:
            metrics: Dictionary of metrics from DIMS verification

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("CloudWatch publishing disabled")
            return False

        try:
            cloudwatch_metrics = self._convert_to_cloudwatch_metrics(metrics)

            if not cloudwatch_metrics:
                logger.warning("No metrics to publish to CloudWatch")
                return False

            # Publish in batches of 20 (CloudWatch limit)
            for i in range(0, len(cloudwatch_metrics), 20):
                batch = cloudwatch_metrics[i : i + 20]
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace, MetricData=batch
                )

            logger.info(
                f"Published {len(cloudwatch_metrics)} DIMS metrics to CloudWatch"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish metrics to CloudWatch: {e}")
            return False

    def _convert_to_cloudwatch_metrics(
        self, metrics: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert DIMS metrics to CloudWatch format"""
        cloudwatch_metrics = []
        timestamp = datetime.utcnow()

        for category, category_metrics in metrics.items():
            for metric_name, metric_data in category_metrics.items():
                value = metric_data.get("value")

                # Skip metrics without values
                if value is None:
                    continue

                # Convert to float if possible
                try:
                    if isinstance(value, (int, float)):
                        numeric_value = float(value)
                    else:
                        # Try to parse string values
                        numeric_value = float(value)
                except (ValueError, TypeError):
                    logger.debug(
                        f"Skipping non-numeric metric: {category}.{metric_name}"
                    )
                    continue

                # Create CloudWatch metric name
                cw_metric_name = f"DIMS_{category}_{metric_name}".replace(".", "_")

                # Determine unit
                unit = self._determine_unit(metric_name, category)

                cloudwatch_metrics.append(
                    {
                        "MetricName": cw_metric_name,
                        "Value": numeric_value,
                        "Unit": unit,
                        "Timestamp": timestamp,
                        "Dimensions": [
                            {"Name": "Category", "Value": category},
                            {"Name": "MetricName", "Value": metric_name},
                        ],
                    }
                )

        return cloudwatch_metrics

    def _determine_unit(self, metric_name: str, category: str) -> str:
        """Determine CloudWatch unit for metric"""
        # Size/storage metrics
        if "size_gb" in metric_name or "storage_gb" in metric_name:
            return "Gigabytes"
        elif "size_mb" in metric_name:
            return "Megabytes"

        # Count metrics
        elif "count" in metric_name or "total" in metric_name or "files" in metric_name:
            return "Count"

        # Percentage metrics
        elif (
            "rate" in metric_name
            or "percent" in metric_name
            or "utilization" in metric_name
        ):
            return "Percent"

        # Cost metrics
        elif "cost" in metric_name:
            return "None"  # Dollars

        # Lines of code
        elif "lines" in metric_name:
            return "Count"

        # Default
        else:
            return "None"

    def publish_summary_metrics(self, verification_summary: Dict[str, Any]) -> bool:
        """
        Publish DIMS verification summary metrics

        Args:
            verification_summary: Summary dict from DIMS verification

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            metrics = [
                {
                    "MetricName": "DIMS_TotalMetrics",
                    "Value": verification_summary.get("total_metrics", 0),
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                },
                {
                    "MetricName": "DIMS_VerifiedMetrics",
                    "Value": verification_summary.get("verified", 0),
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                },
                {
                    "MetricName": "DIMS_ErrorCount",
                    "Value": verification_summary.get("errors", 0),
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                },
                {
                    "MetricName": "DIMS_DriftDetected",
                    "Value": (
                        1 if verification_summary.get("drift_detected", False) else 0
                    ),
                    "Unit": "None",
                    "Timestamp": datetime.utcnow(),
                },
                {
                    "MetricName": "DIMS_VerificationSuccessRate",
                    "Value": (
                        verification_summary.get("verified", 0)
                        / verification_summary.get("total_metrics", 1)
                    )
                    * 100,
                    "Unit": "Percent",
                    "Timestamp": datetime.utcnow(),
                },
            ]

            self.cloudwatch.put_metric_data(
                Namespace=self.namespace, MetricData=metrics
            )

            logger.info("Published DIMS summary metrics to CloudWatch")
            return True

        except Exception as e:
            logger.error(f"Failed to publish summary metrics: {e}")
            return False


# Global publisher instance
_publisher = None


def get_publisher(region="us-east-1", enabled=True) -> DIMSCloudWatchPublisher:
    """Get or create global DIMS CloudWatch publisher"""
    global _publisher

    if _publisher is None:
        _publisher = DIMSCloudWatchPublisher(region=region, enabled=enabled)

    return _publisher


def publish_dims_metrics(
    metrics: Dict[str, Dict[str, Any]], region="us-east-1"
) -> bool:
    """
    Convenience function to publish DIMS metrics to CloudWatch

    Args:
        metrics: Dictionary of metrics from DIMS verification
        region: AWS region

    Returns:
        True if successful, False otherwise
    """
    publisher = get_publisher(region=region, enabled=True)
    return publisher.publish_verification_results(metrics)


def publish_dims_summary(summary: Dict[str, Any], region="us-east-1") -> bool:
    """
    Convenience function to publish DIMS summary to CloudWatch

    Args:
        summary: Verification summary from DIMS
        region: AWS region

    Returns:
        True if successful, False otherwise
    """
    publisher = get_publisher(region=region, enabled=True)
    return publisher.publish_summary_metrics(summary)

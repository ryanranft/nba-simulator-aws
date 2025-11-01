"""
DIMS Metrics Publisher

Publishes Data Inventory Management System (DIMS) metrics to AWS CloudWatch.
Integrates with existing DIMS infrastructure (inventory/metrics.yaml).

Phase 0.0020: Monitoring & Observability
"""

import boto3
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DIMSMetricsPublisher:
    """
    Publishes DIMS metrics to CloudWatch.

    Reads metrics from inventory/metrics.yaml and publishes to CloudWatch
    custom metrics for monitoring and alarming.

    Usage:
        publisher = DIMSMetricsPublisher()
        publisher.publish_all()
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize DIMS metrics publisher.

        Args:
            config_path: Path to cloudwatch_config.yaml (optional)
        """
        # Load CloudWatch configuration
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent.parent
                / "config"
                / "cloudwatch_config.yaml"
            )

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Initialize AWS clients
        region = self.config["aws"]["region"]
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.namespace = self.config["namespaces"]["dims"]

        # Metrics file path
        self.metrics_file = (
            Path(__file__).parent.parent.parent.parent / "inventory" / "metrics.yaml"
        )

        logger.info(f"Initialized DIMS metrics publisher (namespace: {self.namespace})")

    def load_dims_metrics(self) -> Dict[str, Any]:
        """Load DIMS metrics from inventory/metrics.yaml"""
        if not self.metrics_file.exists():
            logger.error(f"DIMS metrics file not found: {self.metrics_file}")
            return {}

        with open(self.metrics_file) as f:
            metrics = yaml.safe_load(f)

        logger.info(f"Loaded DIMS metrics from {self.metrics_file}")
        return metrics

    def _create_metric_data(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Create CloudWatch metric data structure.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: CloudWatch unit (None, Count, Bytes, Gigabytes, etc.)
            dimensions: Optional dimensions for the metric

        Returns:
            CloudWatch metric data dictionary
        """
        metric_data = {
            "MetricName": metric_name,
            "Value": float(value),
            "Unit": unit,
            "Timestamp": datetime.utcnow(),
        }

        if dimensions:
            metric_data["Dimensions"] = dimensions

        return metric_data

    def publish_s3_storage_metrics(self, metrics: Dict[str, Any]) -> List[Dict]:
        """
        Publish S3 storage metrics to CloudWatch.

        Metrics published:
        - S3ObjectCount (total objects in bucket)
        - S3SizeGB (total size in gigabytes)
        - S3FileCount (total files count)
        """
        metric_data = []

        if "s3_storage" not in metrics:
            logger.warning("No S3 storage metrics found in DIMS")
            return metric_data

        s3_metrics = metrics["s3_storage"]

        # Total objects
        if "total_objects" in s3_metrics:
            metric_data.append(
                self._create_metric_data(
                    "S3ObjectCount", s3_metrics["total_objects"]["value"], "Count"
                )
            )

        # Total size in GB
        if "total_size_gb" in s3_metrics:
            metric_data.append(
                self._create_metric_data(
                    "S3SizeGB", s3_metrics["total_size_gb"]["value"], "Gigabytes"
                )
            )

        # Total files
        if "total_files" in s3_metrics:
            metric_data.append(
                self._create_metric_data(
                    "S3FileCount", s3_metrics["total_files"]["value"], "Count"
                )
            )

        logger.info(f"Prepared {len(metric_data)} S3 storage metrics")
        return metric_data

    def publish_code_base_metrics(self, metrics: Dict[str, Any]) -> List[Dict]:
        """
        Publish code base metrics to CloudWatch.

        Metrics published:
        - PythonFileCount
        - TestFileCount
        - MLScriptCount
        - CodeSizeMB
        """
        metric_data = []

        if "code_base" not in metrics:
            logger.warning("No code base metrics found in DIMS")
            return metric_data

        code_metrics = metrics["code_base"]

        # Python files
        if "python_files" in code_metrics:
            metric_data.append(
                self._create_metric_data(
                    "PythonFileCount", code_metrics["python_files"]["value"], "Count"
                )
            )

        # Test files
        if "test_files" in code_metrics:
            metric_data.append(
                self._create_metric_data(
                    "TestFileCount", code_metrics["test_files"]["value"], "Count"
                )
            )

        # ML scripts
        if "ml_scripts" in code_metrics:
            metric_data.append(
                self._create_metric_data(
                    "MLScriptCount", code_metrics["ml_scripts"]["value"], "Count"
                )
            )

        # Code size
        if "total_size_mb" in code_metrics:
            metric_data.append(
                self._create_metric_data(
                    "CodeSizeMB", code_metrics["total_size_mb"]["value"], "Megabytes"
                )
            )

        logger.info(f"Prepared {len(metric_data)} code base metrics")
        return metric_data

    def publish_documentation_metrics(self, metrics: Dict[str, Any]) -> List[Dict]:
        """
        Publish documentation metrics to CloudWatch.

        Metrics published:
        - MarkdownFileCount
        - DocumentationSizeMB
        """
        metric_data = []

        if "documentation" not in metrics:
            logger.warning("No documentation metrics found in DIMS")
            return metric_data

        doc_metrics = metrics["documentation"]

        # Markdown files
        if "markdown_files" in doc_metrics:
            metric_data.append(
                self._create_metric_data(
                    "MarkdownFileCount", doc_metrics["markdown_files"]["value"], "Count"
                )
            )

        # Documentation size
        if "total_size_mb" in doc_metrics:
            metric_data.append(
                self._create_metric_data(
                    "DocumentationSizeMB",
                    doc_metrics["total_size_mb"]["value"],
                    "Megabytes",
                )
            )

        logger.info(f"Prepared {len(metric_data)} documentation metrics")
        return metric_data

    def publish_git_metrics(self, metrics: Dict[str, Any]) -> List[Dict]:
        """
        Publish Git repository metrics to CloudWatch.

        Metrics published:
        - GitCommitCount
        - BookRecommendationsImplemented
        """
        metric_data = []

        if "git_repository" not in metrics:
            logger.warning("No Git repository metrics found in DIMS")
            return metric_data

        git_metrics = metrics["git_repository"]

        # Total commits
        if "total_commits" in git_metrics:
            metric_data.append(
                self._create_metric_data(
                    "GitCommitCount", git_metrics["total_commits"]["value"], "Count"
                )
            )

        # Book recommendations
        if "book_recommendations_implemented" in git_metrics:
            metric_data.append(
                self._create_metric_data(
                    "BookRecommendationsImplemented",
                    git_metrics["book_recommendations_implemented"]["value"],
                    "Count",
                )
            )

        logger.info(f"Prepared {len(metric_data)} Git metrics")
        return metric_data

    def publish_data_quality_metrics(self, metrics: Dict[str, Any]) -> List[Dict]:
        """
        Publish data quality and validation metrics to CloudWatch.

        Metrics published:
        - MetricsWithDrift (critical for alarms)
        - ValidationFailures
        - DataGaps
        """
        metric_data = []

        # Metrics with drift (for alarms)
        if "validation" in metrics and "metrics_with_drift" in metrics["validation"]:
            metric_data.append(
                self._create_metric_data(
                    "MetricsWithDrift",
                    metrics["validation"]["metrics_with_drift"]["value"],
                    "Count",
                )
            )

        # Validation failures
        if "validation" in metrics and "failed_validations" in metrics["validation"]:
            metric_data.append(
                self._create_metric_data(
                    "ValidationFailures",
                    metrics["validation"]["failed_validations"]["value"],
                    "Count",
                )
            )

        # Data gaps
        if "data_coverage" in metrics and "total_gaps" in metrics["data_coverage"]:
            metric_data.append(
                self._create_metric_data(
                    "DataGaps", metrics["data_coverage"]["total_gaps"]["value"], "Count"
                )
            )

        logger.info(f"Prepared {len(metric_data)} data quality metrics")
        return metric_data

    def publish_all(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Publish all DIMS metrics to CloudWatch.

        Args:
            dry_run: If True, don't actually publish (for testing)

        Returns:
            Summary of published metrics
        """
        logger.info("Publishing DIMS metrics to CloudWatch...")

        # Load DIMS metrics
        metrics = self.load_dims_metrics()
        if not metrics:
            logger.error("No metrics loaded from DIMS")
            return {"status": "error", "message": "No metrics loaded"}

        # Collect all metric data
        all_metric_data = []
        all_metric_data.extend(self.publish_s3_storage_metrics(metrics))
        all_metric_data.extend(self.publish_code_base_metrics(metrics))
        all_metric_data.extend(self.publish_documentation_metrics(metrics))
        all_metric_data.extend(self.publish_git_metrics(metrics))
        all_metric_data.extend(self.publish_data_quality_metrics(metrics))

        if not all_metric_data:
            logger.warning("No metric data prepared for publishing")
            return {"status": "warning", "message": "No metrics to publish", "count": 0}

        # Publish to CloudWatch in batches of 20 (AWS limit)
        published_count = 0

        if not dry_run:
            for i in range(0, len(all_metric_data), 20):
                batch = all_metric_data[i : i + 20]

                try:
                    response = self.cloudwatch.put_metric_data(
                        Namespace=self.namespace, MetricData=batch
                    )
                    published_count += len(batch)
                    logger.info(
                        f"Published batch of {len(batch)} metrics to CloudWatch"
                    )

                except Exception as e:
                    logger.error(f"Error publishing metrics batch: {e}")
                    return {
                        "status": "error",
                        "message": str(e),
                        "published_count": published_count,
                        "failed_count": len(batch),
                    }
        else:
            logger.info(f"DRY RUN: Would publish {len(all_metric_data)} metrics")
            published_count = len(all_metric_data)

        logger.info(
            f"Successfully published {published_count} DIMS metrics to CloudWatch"
        )

        return {
            "status": "success",
            "namespace": self.namespace,
            "published_count": published_count,
            "timestamp": datetime.utcnow().isoformat(),
        }


def main():
    """CLI entry point for DIMS metrics publisher"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Publish DIMS metrics to CloudWatch")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (don't actually publish)"
    )
    parser.add_argument("--config", type=str, help="Path to cloudwatch_config.yaml")

    args = parser.parse_args()

    try:
        publisher = DIMSMetricsPublisher(config_path=args.config)
        result = publisher.publish_all(dry_run=args.dry_run)

        print(f"\nDIMS Metrics Publishing Results:")
        print(f"Status: {result['status']}")
        print(f"Published: {result.get('published_count', 0)} metrics")

        if result["status"] == "error":
            print(f"Error: {result.get('message', 'Unknown error')}")
            exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()

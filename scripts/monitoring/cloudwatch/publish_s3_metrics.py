"""
S3 Metrics Publisher

Publishes S3 bucket metrics to AWS CloudWatch.
Analyzes S3 bucket inventory and publishes object counts, sizes, and growth trends.

Phase 0.0020: Monitoring & Observability
"""

import boto3
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class S3MetricsPublisher:
    """
    Publishes S3 bucket metrics to CloudWatch.

    Analyzes the S3 bucket inventory and publishes comprehensive metrics
    including object counts, sizes, and per-source breakdowns.

    Usage:
        publisher = S3MetricsPublisher()
        publisher.publish_bucket_metrics()
    """

    def __init__(
        self,
        bucket_name: str = "nba-sim-raw-data-lake",
        config_path: Optional[str] = None,
    ):
        """
        Initialize S3 metrics publisher.

        Args:
            bucket_name: S3 bucket name (default: nba-sim-raw-data-lake)
            config_path: Path to cloudwatch_config.yaml (optional)
        """
        self.bucket_name = bucket_name

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
        self.s3 = boto3.client("s3", region_name=region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.namespace = self.config["namespaces"]["s3"]

        logger.info(
            f"Initialized S3 metrics publisher (bucket: {bucket_name}, namespace: {self.namespace})"
        )

    def _create_metric_data(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[List[Dict]] = None,
    ) -> Dict:
        """Create CloudWatch metric data structure"""
        metric_data = {
            "MetricName": metric_name,
            "Value": float(value),
            "Unit": unit,
            "Timestamp": datetime.utcnow(),
        }

        if dimensions:
            metric_data["Dimensions"] = dimensions

        return metric_data

    def analyze_bucket_inventory(self) -> Dict[str, Any]:
        """
        Analyze S3 bucket inventory.

        Returns:
            Dictionary containing:
            - total_objects: Total object count
            - total_size: Total size in bytes
            - objects_by_source: Breakdown by data source
            - sizes_by_source: Size breakdown by data source
        """
        logger.info(f"Analyzing bucket inventory for {self.bucket_name}...")

        # Use paginator to handle large buckets
        paginator = self.s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name)

        total_objects = 0
        total_size = 0
        objects_by_source = defaultdict(int)
        sizes_by_source = defaultdict(int)

        for page in pages:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                total_objects += 1
                obj_size = obj["Size"]
                total_size += obj_size

                # Extract data source from key
                # Format: basketball_reference/pbp/..., espn/games/..., etc.
                key = obj["Key"]
                source = key.split("/")[0] if "/" in key else "root"

                objects_by_source[source] += 1
                sizes_by_source[source] += obj_size

        logger.info(
            f"Analyzed {total_objects} objects ({total_size / (1024**3):.2f} GB)"
        )

        return {
            "total_objects": total_objects,
            "total_size": total_size,
            "objects_by_source": dict(objects_by_source),
            "sizes_by_source": dict(sizes_by_source),
        }

    def publish_bucket_metrics(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Publish S3 bucket metrics to CloudWatch.

        Metrics published:
        - S3TotalObjects (total object count)
        - S3TotalSizeGB (total size in gigabytes)
        - S3ObjectsBySource (per-source object counts with dimensions)
        - S3SizeBySourceGB (per-source sizes with dimensions)

        Args:
            dry_run: If True, don't actually publish (for testing)

        Returns:
            Summary of published metrics
        """
        logger.info("Publishing S3 metrics to CloudWatch...")

        try:
            # Analyze bucket
            inventory = self.analyze_bucket_inventory()

        except Exception as e:
            logger.error(f"Error analyzing S3 bucket: {e}")
            return {
                "status": "error",
                "message": f"Error analyzing bucket: {e}",
                "published_count": 0,
            }

        # Prepare metric data
        metric_data = []

        # Total metrics
        metric_data.append(
            self._create_metric_data(
                "S3TotalObjects", inventory["total_objects"], "Count"
            )
        )

        metric_data.append(
            self._create_metric_data(
                "S3TotalSizeGB",
                inventory["total_size"] / (1024**3),  # Convert to GB
                "Gigabytes",
            )
        )

        # Per-source metrics
        for source, count in inventory["objects_by_source"].items():
            metric_data.append(
                self._create_metric_data(
                    "S3ObjectsBySource",
                    count,
                    "Count",
                    dimensions=[{"Name": "DataSource", "Value": source}],
                )
            )

        for source, size in inventory["sizes_by_source"].items():
            metric_data.append(
                self._create_metric_data(
                    "S3SizeBySourceGB",
                    size / (1024**3),  # Convert to GB
                    "Gigabytes",
                    dimensions=[{"Name": "DataSource", "Value": source}],
                )
            )

        if not metric_data:
            logger.warning("No metric data prepared for publishing")
            return {"status": "warning", "message": "No metrics to publish", "count": 0}

        # Publish to CloudWatch in batches of 20 (AWS limit)
        published_count = 0

        if not dry_run:
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i : i + 20]

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
            logger.info(f"DRY RUN: Would publish {len(metric_data)} metrics")
            published_count = len(metric_data)

        logger.info(
            f"Successfully published {published_count} S3 metrics to CloudWatch"
        )

        return {
            "status": "success",
            "namespace": self.namespace,
            "published_count": published_count,
            "inventory": {
                "total_objects": inventory["total_objects"],
                "total_size_gb": inventory["total_size"] / (1024**3),
                "sources": list(inventory["objects_by_source"].keys()),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


def main():
    """CLI entry point for S3 metrics publisher"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Publish S3 metrics to CloudWatch")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (don't actually publish)"
    )
    parser.add_argument(
        "--bucket", type=str, default="nba-sim-raw-data-lake", help="S3 bucket name"
    )
    parser.add_argument("--config", type=str, help="Path to cloudwatch_config.yaml")

    args = parser.parse_args()

    try:
        publisher = S3MetricsPublisher(bucket_name=args.bucket, config_path=args.config)
        result = publisher.publish_bucket_metrics(dry_run=args.dry_run)

        print(f"\nS3 Metrics Publishing Results:")
        print(f"Status: {result['status']}")
        print(f"Published: {result.get('published_count', 0)} metrics")

        if "inventory" in result:
            print(f"\nInventory Summary:")
            print(f"  Total Objects: {result['inventory']['total_objects']:,}")
            print(f"  Total Size: {result['inventory']['total_size_gb']:.2f} GB")
            print(f"  Data Sources: {', '.join(result['inventory']['sources'])}")

        if result["status"] == "error":
            print(f"Error: {result.get('message', 'Unknown error')}")
            exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CloudWatch Metrics Publisher - Data Collection

Publishes S3 bucket and ADCE system metrics to CloudWatch for monitoring
and alerting. Part of Phase 0.0020 (Monitoring & Observability).

Usage:
    python scripts/monitoring/publish_collection_metrics.py --metric s3
    python scripts/monitoring/publish_collection_metrics.py --metric adce
    python scripts/monitoring/publish_collection_metrics.py --all

Metrics Published:
    S3:
        - S3ObjectCount: Total objects in nba-sim-raw-data-lake
        - S3TotalSizeGB: Total bucket size in gigabytes
        - S3HooprFiles: Count of hoopR play-by-play files

    ADCE:
        - ADCETasksCompleted: Number of successful autonomous tasks
        - ADCETasksFailed: Number of failed autonomous tasks
        - ADCEQueueDepth: Current task queue size
        - ADCESuccessRate: Percentage of successful tasks
"""

import argparse
import boto3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class CloudWatchPublisher:
    """Publish metrics to CloudWatch"""

    def __init__(self, region="us-east-1"):
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.s3 = boto3.client("s3", region_name=region)
        self.bucket_name = "nba-sim-raw-data-lake"

    def publish_metrics(self, namespace: str, metrics: List[Dict[str, Any]]) -> bool:
        """Publish metrics to CloudWatch"""
        try:
            # Add timestamp to all metrics
            timestamp = datetime.utcnow()
            for metric in metrics:
                if "Timestamp" not in metric:
                    metric["Timestamp"] = timestamp

            # Publish in batches of 20 (CloudWatch limit)
            for i in range(0, len(metrics), 20):
                batch = metrics[i : i + 20]
                response = self.cloudwatch.put_metric_data(
                    Namespace=namespace, MetricData=batch
                )
                print(f"✅ Published {len(batch)} metrics to {namespace}")

            return True

        except Exception as e:
            print(f"❌ Error publishing metrics to {namespace}: {e}")
            return False

    def get_s3_metrics(self) -> List[Dict[str, Any]]:
        """Collect S3 bucket metrics"""
        print(f"📊 Collecting S3 metrics for {self.bucket_name}...")

        try:
            # Use paginator for large buckets (172K+ files)
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name)

            total_objects = 0
            total_size = 0
            hoopr_files = 0

            for page in pages:
                if "Contents" in page:
                    objects = page["Contents"]
                    total_objects += len(objects)
                    total_size += sum(obj["Size"] for obj in objects)

                    # Count hoopR files
                    hoopr_files += sum(
                        1 for obj in objects if "hoopr" in obj["Key"].lower()
                    )

            size_gb = total_size / (1024**3)

            print(f"  Total Objects: {total_objects:,}")
            print(f"  Total Size: {size_gb:.2f} GB")
            print(f"  HoopR Files: {hoopr_files:,}")

            metrics = [
                {
                    "MetricName": "S3ObjectCount",
                    "Value": total_objects,
                    "Unit": "Count",
                    "Dimensions": [{"Name": "Bucket", "Value": self.bucket_name}],
                },
                {
                    "MetricName": "S3TotalSizeGB",
                    "Value": size_gb,
                    "Unit": "Gigabytes",
                    "Dimensions": [{"Name": "Bucket", "Value": self.bucket_name}],
                },
                {
                    "MetricName": "S3HooprFiles",
                    "Value": hoopr_files,
                    "Unit": "Count",
                    "Dimensions": [{"Name": "Bucket", "Value": self.bucket_name}],
                },
            ]

            return metrics

        except Exception as e:
            print(f"❌ Error collecting S3 metrics: {e}")
            return []

    def get_adce_metrics(self) -> List[Dict[str, Any]]:
        """Collect ADCE (Autonomous Data Collection) metrics"""
        print("📊 Collecting ADCE metrics...")

        try:
            # Import ADCE orchestrator (if available)
            adce_path = Path(__file__).parent.parent / "autonomous"
            if not adce_path.exists():
                print("⚠️  ADCE path not found, skipping ADCE metrics")
                return []

            # Try to get ADCE stats from health check
            import subprocess  # nosec B404
            import json

            result = subprocess.run(  # nosec B603 B607
                [
                    "python",
                    str(adce_path / "autonomous_cli.py"),
                    "health",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                print(f"⚠️  ADCE health check failed, using default metrics")
                return self._get_default_adce_metrics()

            health_data = json.loads(result.stdout)

            tasks_completed = health_data.get("tasks_completed", 0)
            tasks_failed = health_data.get("tasks_failed", 0)
            queue_depth = health_data.get("queue_depth", 0)

            total_tasks = tasks_completed + tasks_failed
            success_rate = (
                (tasks_completed / total_tasks * 100) if total_tasks > 0 else 100.0
            )

            print(f"  Tasks Completed: {tasks_completed:,}")
            print(f"  Tasks Failed: {tasks_failed:,}")
            print(f"  Queue Depth: {queue_depth}")
            print(f"  Success Rate: {success_rate:.1f}%")

            metrics = [
                {
                    "MetricName": "ADCETasksCompleted",
                    "Value": tasks_completed,
                    "Unit": "Count",
                },
                {
                    "MetricName": "ADCETasksFailed",
                    "Value": tasks_failed,
                    "Unit": "Count",
                },
                {"MetricName": "ADCEQueueDepth", "Value": queue_depth, "Unit": "Count"},
                {
                    "MetricName": "ADCESuccessRate",
                    "Value": success_rate,
                    "Unit": "Percent",
                },
            ]

            return metrics

        except Exception as e:
            print(f"⚠️  Error collecting ADCE metrics: {e}")
            return self._get_default_adce_metrics()

    def _get_default_adce_metrics(self) -> List[Dict[str, Any]]:
        """Return default ADCE metrics when system is unavailable"""
        return [
            {"MetricName": "ADCETasksCompleted", "Value": 0, "Unit": "Count"},
            {"MetricName": "ADCETasksFailed", "Value": 0, "Unit": "Count"},
            {"MetricName": "ADCEQueueDepth", "Value": 0, "Unit": "Count"},
            {"MetricName": "ADCESuccessRate", "Value": 100.0, "Unit": "Percent"},
        ]


def main():
    parser = argparse.ArgumentParser(
        description="Publish data collection metrics to CloudWatch"
    )
    parser.add_argument(
        "--metric", choices=["s3", "adce"], help="Specific metric type to publish"
    )
    parser.add_argument("--all", action="store_true", help="Publish all metrics")
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    if not args.metric and not args.all:
        parser.print_help()
        sys.exit(1)

    publisher = CloudWatchPublisher(region=args.region)
    success = True

    # Publish S3 metrics
    if args.metric == "s3" or args.all:
        s3_metrics = publisher.get_s3_metrics()
        if s3_metrics:
            success &= publisher.publish_metrics(
                "NBA-Simulator/DataCollection", s3_metrics
            )

    # Publish ADCE metrics
    if args.metric == "adce" or args.all:
        adce_metrics = publisher.get_adce_metrics()
        if adce_metrics:
            success &= publisher.publish_metrics("NBA-Simulator/ADCE", adce_metrics)

    if success:
        print("✅ All metrics published successfully")
        sys.exit(0)
    else:
        print("❌ Some metrics failed to publish")
        sys.exit(1)


if __name__ == "__main__":
    main()

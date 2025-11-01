"""
ADCE Metrics Publisher

Publishes Autonomous Data Collection Engine (ADCE) metrics to AWS CloudWatch.
Integrates with ADCE health monitoring endpoint (localhost:8080).

Phase 0.0020: Monitoring & Observability
"""

import boto3
import requests
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ADCEMetricsPublisher:
    """
    Publishes ADCE health and task metrics to CloudWatch.

    Fetches metrics from ADCE HTTP health endpoint and publishes to CloudWatch
    for monitoring, alarming, and performance tracking.

    Usage:
        publisher = ADCEMetricsPublisher()
        publisher.publish_health_metrics()
    """

    def __init__(self, health_port: int = 8080, config_path: Optional[str] = None):
        """
        Initialize ADCE metrics publisher.

        Args:
            health_port: ADCE health monitor port (default: 8080)
            config_path: Path to cloudwatch_config.yaml (optional)
        """
        self.health_port = health_port
        self.base_url = f"http://localhost:{health_port}"

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
        self.namespace = self.config["namespaces"]["adce"]

        logger.info(
            f"Initialized ADCE metrics publisher (port: {health_port}, namespace: {self.namespace})"
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

    def fetch_adce_status(self) -> Optional[Dict[str, Any]]:
        """
        Fetch ADCE system status from health endpoint.

        Returns:
            Status dictionary or None if unavailable
        """
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            response.raise_for_status()

            status = response.json()
            logger.info("Successfully fetched ADCE status")
            return status

        except requests.exceptions.ConnectionError:
            logger.warning(f"ADCE health endpoint not available at {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching ADCE status")
            return None
        except Exception as e:
            logger.error(f"Error fetching ADCE status: {e}")
            return None

    def fetch_adce_tasks(self) -> Optional[Dict[str, Any]]:
        """
        Fetch ADCE task queue metrics from health endpoint.

        Returns:
            Task metrics dictionary or None if unavailable
        """
        try:
            response = requests.get(f"{self.base_url}/tasks", timeout=5)
            response.raise_for_status()

            tasks = response.json()
            logger.info("Successfully fetched ADCE tasks")
            return tasks

        except requests.exceptions.ConnectionError:
            logger.warning(f"ADCE tasks endpoint not available at {self.base_url}")
            return None
        except requests.exceptions.Timeout:
            logger.error("Timeout fetching ADCE tasks")
            return None
        except Exception as e:
            logger.error(f"Error fetching ADCE tasks: {e}")
            return None

    def publish_task_queue_metrics(self, tasks: Dict[str, Any]) -> List[Dict]:
        """
        Publish ADCE task queue metrics to CloudWatch.

        Metrics published:
        - ADCETaskQueueDepth (total tasks in queue) [CRITICAL FOR ALARMS]
        - ADCETasksCritical (critical priority tasks)
        - ADCETasksHigh (high priority tasks)
        - ADCETasksMedium (medium priority tasks)
        - ADCETasksLow (low priority tasks)
        """
        metric_data = []

        if not tasks:
            logger.warning("No task data available")
            return metric_data

        # Total task queue depth (critical for alarms)
        total_tasks = tasks.get("total_tasks", 0)
        metric_data.append(
            self._create_metric_data("ADCETaskQueueDepth", total_tasks, "Count")
        )

        # Tasks by priority
        by_priority = tasks.get("by_priority", {})

        if "critical" in by_priority:
            metric_data.append(
                self._create_metric_data(
                    "ADCETasksCritical", by_priority["critical"], "Count"
                )
            )

        if "high" in by_priority:
            metric_data.append(
                self._create_metric_data("ADCETasksHigh", by_priority["high"], "Count")
            )

        if "medium" in by_priority:
            metric_data.append(
                self._create_metric_data(
                    "ADCETasksMedium", by_priority["medium"], "Count"
                )
            )

        if "low" in by_priority:
            metric_data.append(
                self._create_metric_data("ADCETasksLow", by_priority["low"], "Count")
            )

        # Tasks by source (with dimensions)
        by_source = tasks.get("by_source", {})
        for source, count in by_source.items():
            metric_data.append(
                self._create_metric_data(
                    "ADCETasksBySource",
                    count,
                    "Count",
                    dimensions=[{"Name": "DataSource", "Value": source}],
                )
            )

        logger.info(f"Prepared {len(metric_data)} task queue metrics")
        return metric_data

    def publish_component_health_metrics(self, status: Dict[str, Any]) -> List[Dict]:
        """
        Publish ADCE component health metrics to CloudWatch.

        Metrics published:
        - ADCEHealthyComponents (count of healthy components)
        - ADCEUnhealthyComponents (count of unhealthy components)
        - ADCEComponentStatus (per-component status with dimensions)
        """
        metric_data = []

        if not status:
            logger.warning("No status data available")
            return metric_data

        components = status.get("components", {})

        # Count healthy/unhealthy components
        healthy_count = sum(
            1
            for component in components.values()
            if component.get("status") in ["healthy", "running", "idle"]
        )
        unhealthy_count = len(components) - healthy_count

        metric_data.append(
            self._create_metric_data("ADCEHealthyComponents", healthy_count, "Count")
        )

        metric_data.append(
            self._create_metric_data(
                "ADCEUnhealthyComponents", unhealthy_count, "Count"
            )
        )

        # Per-component status (1 = healthy, 0 = unhealthy)
        for component_name, component_data in components.items():
            component_status = component_data.get("status", "unknown")
            is_healthy = 1 if component_status in ["healthy", "running", "idle"] else 0

            metric_data.append(
                self._create_metric_data(
                    "ADCEComponentStatus",
                    is_healthy,
                    "None",
                    dimensions=[
                        {"Name": "Component", "Value": component_name},
                        {"Name": "Status", "Value": component_status},
                    ],
                )
            )

        logger.info(f"Prepared {len(metric_data)} component health metrics")
        return metric_data

    def publish_system_metrics(self, status: Dict[str, Any]) -> List[Dict]:
        """
        Publish ADCE system-level metrics to CloudWatch.

        Metrics published:
        - ADCEUptime (seconds since start)
        - ADCEReconciliationCycles (total reconciliation cycles)
        """
        metric_data = []

        if not status:
            return metric_data

        # Uptime (if available)
        if "uptime_seconds" in status:
            metric_data.append(
                self._create_metric_data(
                    "ADCEUptime", status["uptime_seconds"], "Seconds"
                )
            )

        # Reconciliation cycles (if available)
        if "reconciliation_cycles" in status:
            metric_data.append(
                self._create_metric_data(
                    "ADCEReconciliationCycles", status["reconciliation_cycles"], "Count"
                )
            )

        logger.info(f"Prepared {len(metric_data)} system metrics")
        return metric_data

    def publish_health_metrics(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Publish all ADCE health metrics to CloudWatch.

        Args:
            dry_run: If True, don't actually publish (for testing)

        Returns:
            Summary of published metrics
        """
        logger.info("Publishing ADCE metrics to CloudWatch...")

        # Fetch ADCE status and tasks
        status = self.fetch_adce_status()
        tasks = self.fetch_adce_tasks()

        if not status and not tasks:
            logger.error("ADCE not available - cannot publish metrics")
            return {
                "status": "error",
                "message": "ADCE health endpoint not available",
                "published_count": 0,
            }

        # Collect all metric data
        all_metric_data = []

        if tasks:
            all_metric_data.extend(self.publish_task_queue_metrics(tasks))

        if status:
            all_metric_data.extend(self.publish_component_health_metrics(status))
            all_metric_data.extend(self.publish_system_metrics(status))

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
            f"Successfully published {published_count} ADCE metrics to CloudWatch"
        )

        return {
            "status": "success",
            "namespace": self.namespace,
            "published_count": published_count,
            "timestamp": datetime.utcnow().isoformat(),
        }


def main():
    """CLI entry point for ADCE metrics publisher"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(description="Publish ADCE metrics to CloudWatch")
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (don't actually publish)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="ADCE health monitor port"
    )
    parser.add_argument("--config", type=str, help="Path to cloudwatch_config.yaml")

    args = parser.parse_args()

    try:
        publisher = ADCEMetricsPublisher(health_port=args.port, config_path=args.config)
        result = publisher.publish_health_metrics(dry_run=args.dry_run)

        print(f"\nADCE Metrics Publishing Results:")
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

"""
CloudWatch Alarms Setup Script

Creates and configures CloudWatch alarms for NBA Simulator monitoring.
Integrates with SNS topics for notifications.

Phase 0.0020: Monitoring & Observability

Usage:
    python scripts/monitoring/cloudwatch/create_alarms.py --create
    python scripts/monitoring/cloudwatch/create_alarms.py --delete
    python scripts/monitoring/cloudwatch/create_alarms.py --list
"""

import boto3
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import argparse

logger = logging.getLogger(__name__)


class CloudWatchAlarmsManager:
    """
    Manages CloudWatch alarms for NBA Simulator.

    Creates, updates, and deletes alarms based on configuration.
    """

    def __init__(
        self, config_path: Optional[str] = None, sns_topic_arn: Optional[str] = None
    ):
        """
        Initialize alarms manager.

        Args:
            config_path: Path to cloudwatch_config.yaml
            sns_topic_arn: ARN of SNS topic for alarm notifications
        """
        # Load configuration
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
        self.sns = boto3.client("sns", region_name=region)

        # Get SNS topic ARN
        if sns_topic_arn:
            self.sns_topic_arn = sns_topic_arn
        else:
            # Try to find existing topic
            self.sns_topic_arn = self._find_sns_topic()

        logger.info(f"Initialized alarms manager (region: {region})")
        if self.sns_topic_arn:
            logger.info(f"SNS topic ARN: {self.sns_topic_arn}")
        else:
            logger.warning(
                "No SNS topic configured - alarms will be created without notifications"
            )

    def _find_sns_topic(self) -> Optional[str]:
        """Find existing SNS topic for alerts"""
        topic_name = self.config.get("sns", {}).get(
            "alerts_topic_name", "nba-simulator-alerts"
        )

        try:
            response = self.sns.list_topics()
            for topic in response.get("Topics", []):
                if topic_name in topic["TopicArn"]:
                    return topic["TopicArn"]
        except Exception as e:
            logger.warning(f"Error finding SNS topic: {e}")

        return None

    def create_adce_queue_depth_alarm(self) -> Dict[str, Any]:
        """
        Create alarm for ADCE task queue depth.

        Triggers when queue depth exceeds threshold for sustained period.
        """
        alarm_config = self.config["alarms"]["adce_queue_depth"]

        if not alarm_config["enabled"]:
            logger.info("ADCE queue depth alarm disabled in config")
            return {"status": "skipped", "reason": "disabled in config"}

        alarm_name = "NBA-Simulator-ADCE-HighQueueDepth"

        alarm_actions = [self.sns_topic_arn] if self.sns_topic_arn else []

        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=alarm_config["evaluation_periods"],
                MetricName="ADCETaskQueueDepth",
                Namespace=self.config["namespaces"]["adce"],
                Period=alarm_config["period"],
                Statistic="Average",
                Threshold=alarm_config["threshold"],
                ActionsEnabled=True,
                AlarmDescription=f"ADCE task queue exceeds {alarm_config['threshold']} tasks",
                AlarmActions=alarm_actions,
                TreatMissingData="notBreaching",
            )

            logger.info(f"Created alarm: {alarm_name}")
            return {"status": "created", "alarm_name": alarm_name}

        except Exception as e:
            logger.error(f"Error creating ADCE queue depth alarm: {e}")
            return {"status": "error", "message": str(e)}

    def create_budget_utilization_alarms(self) -> List[Dict[str, Any]]:
        """
        Create budget utilization alarms for multiple thresholds.

        Creates separate alarms for 80% and 95% budget utilization.
        """
        alarm_config = self.config["alarms"]["budget_utilization"]

        if not alarm_config["enabled"]:
            logger.info("Budget utilization alarms disabled in config")
            return [{"status": "skipped", "reason": "disabled in config"}]

        results = []
        alarm_actions = [self.sns_topic_arn] if self.sns_topic_arn else []

        for threshold in alarm_config["thresholds"]:
            alarm_name = f"NBA-Simulator-BudgetExceeded{threshold}Percent"

            try:
                self.cloudwatch.put_metric_alarm(
                    AlarmName=alarm_name,
                    ComparisonOperator="GreaterThanThreshold",
                    EvaluationPeriods=alarm_config["evaluation_periods"],
                    MetricName="BudgetUtilization",
                    Namespace=self.config["namespaces"]["costs"],
                    Period=alarm_config["period"],
                    Statistic="Maximum",
                    Threshold=float(threshold),
                    ActionsEnabled=True,
                    AlarmDescription=f"AWS costs exceeded {threshold}% of budget",
                    AlarmActions=alarm_actions,
                    TreatMissingData="notBreaching",
                )

                logger.info(f"Created alarm: {alarm_name}")
                results.append(
                    {
                        "status": "created",
                        "alarm_name": alarm_name,
                        "threshold": threshold,
                    }
                )

            except Exception as e:
                logger.error(
                    f"Error creating budget alarm (threshold={threshold}): {e}"
                )
                results.append(
                    {"status": "error", "threshold": threshold, "message": str(e)}
                )

        return results

    def create_s3_upload_failures_alarm(self) -> Dict[str, Any]:
        """
        Create alarm for S3 upload failures.

        Triggers when upload failures exceed threshold.
        """
        alarm_config = self.config["alarms"]["s3_upload_failures"]

        if not alarm_config["enabled"]:
            logger.info("S3 upload failures alarm disabled in config")
            return {"status": "skipped", "reason": "disabled in config"}

        alarm_name = "NBA-Simulator-S3-UploadFailures"
        alarm_actions = [self.sns_topic_arn] if self.sns_topic_arn else []

        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=alarm_config["evaluation_periods"],
                MetricName="S3UploadFailures",
                Namespace=self.config["namespaces"]["s3"],
                Period=alarm_config["period"],
                Statistic="Sum",
                Threshold=alarm_config["threshold"],
                ActionsEnabled=True,
                AlarmDescription=f"More than {alarm_config['threshold']} S3 upload failures detected",
                AlarmActions=alarm_actions,
                TreatMissingData="notBreaching",
            )

            logger.info(f"Created alarm: {alarm_name}")
            return {"status": "created", "alarm_name": alarm_name}

        except Exception as e:
            logger.error(f"Error creating S3 upload failures alarm: {e}")
            return {"status": "error", "message": str(e)}

    def create_dims_validation_drift_alarm(self) -> Dict[str, Any]:
        """
        Create alarm for DIMS validation drift.

        Triggers when too many DIMS metrics show drift from expected values.
        """
        alarm_config = self.config["alarms"]["dims_validation_drift"]

        if not alarm_config["enabled"]:
            logger.info("DIMS validation drift alarm disabled in config")
            return {"status": "skipped", "reason": "disabled in config"}

        alarm_name = "NBA-Simulator-DIMS-ValidationDrift"
        alarm_actions = [self.sns_topic_arn] if self.sns_topic_arn else []

        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=alarm_name,
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=alarm_config["evaluation_periods"],
                MetricName="MetricsWithDrift",
                Namespace=self.config["namespaces"]["dims"],
                Period=alarm_config["period"],
                Statistic="Sum",
                Threshold=alarm_config["threshold"],
                ActionsEnabled=True,
                AlarmDescription=f"More than {alarm_config['threshold']} DIMS metrics showing drift",
                AlarmActions=alarm_actions,
                TreatMissingData="notBreaching",
            )

            logger.info(f"Created alarm: {alarm_name}")
            return {"status": "created", "alarm_name": alarm_name}

        except Exception as e:
            logger.error(f"Error creating DIMS validation drift alarm: {e}")
            return {"status": "error", "message": str(e)}

    def create_all_alarms(self) -> Dict[str, Any]:
        """
        Create all configured CloudWatch alarms.

        Returns:
            Summary of created alarms
        """
        logger.info("Creating all CloudWatch alarms...")

        results = {
            "adce_queue_depth": self.create_adce_queue_depth_alarm(),
            "budget_utilization": self.create_budget_utilization_alarms(),
            "s3_upload_failures": self.create_s3_upload_failures_alarm(),
            "dims_validation_drift": self.create_dims_validation_drift_alarm(),
        }

        # Count successes
        success_count = sum(
            1
            for r in [
                results["adce_queue_depth"],
                results["s3_upload_failures"],
                results["dims_validation_drift"],
            ]
            if r.get("status") == "created"
        )
        success_count += sum(
            1 for r in results["budget_utilization"] if r.get("status") == "created"
        )

        logger.info(f"Created {success_count} alarms successfully")

        return {"status": "success", "created_count": success_count, "details": results}

    def list_alarms(self) -> List[Dict[str, Any]]:
        """List all NBA Simulator alarms"""
        try:
            response = self.cloudwatch.describe_alarms(AlarmNamePrefix="NBA-Simulator-")

            alarms = []
            for alarm in response.get("MetricAlarms", []):
                alarms.append(
                    {
                        "name": alarm["AlarmName"],
                        "state": alarm["StateValue"],
                        "metric": alarm["MetricName"],
                        "threshold": alarm["Threshold"],
                    }
                )

            return alarms

        except Exception as e:
            logger.error(f"Error listing alarms: {e}")
            return []

    def delete_all_alarms(self) -> Dict[str, Any]:
        """Delete all NBA Simulator alarms"""
        try:
            # List alarms
            response = self.cloudwatch.describe_alarms(AlarmNamePrefix="NBA-Simulator-")

            alarm_names = [
                alarm["AlarmName"] for alarm in response.get("MetricAlarms", [])
            ]

            if not alarm_names:
                logger.info("No alarms to delete")
                return {"status": "success", "deleted_count": 0}

            # Delete alarms
            self.cloudwatch.delete_alarms(AlarmNames=alarm_names)

            logger.info(f"Deleted {len(alarm_names)} alarms")
            return {
                "status": "success",
                "deleted_count": len(alarm_names),
                "alarm_names": alarm_names,
            }

        except Exception as e:
            logger.error(f"Error deleting alarms: {e}")
            return {"status": "error", "message": str(e)}


def main():
    """CLI entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Manage CloudWatch alarms for NBA Simulator"
    )
    parser.add_argument("--create", action="store_true", help="Create all alarms")
    parser.add_argument("--delete", action="store_true", help="Delete all alarms")
    parser.add_argument("--list", action="store_true", help="List all alarms")
    parser.add_argument(
        "--sns-topic-arn", type=str, help="SNS topic ARN for notifications"
    )
    parser.add_argument("--config", type=str, help="Path to cloudwatch_config.yaml")

    args = parser.parse_args()

    if not (args.create or args.delete or args.list):
        parser.print_help()
        exit(1)

    try:
        manager = CloudWatchAlarmsManager(
            config_path=args.config, sns_topic_arn=args.sns_topic_arn
        )

        if args.create:
            print("\nCreating CloudWatch alarms...")
            result = manager.create_all_alarms()
            print(f"\nStatus: {result['status']}")
            print(f"Created: {result['created_count']} alarms")

        elif args.delete:
            print("\nDeleting CloudWatch alarms...")
            result = manager.delete_all_alarms()
            print(f"\nStatus: {result['status']}")
            print(f"Deleted: {result['deleted_count']} alarms")

        elif args.list:
            print("\nListing CloudWatch alarms...")
            alarms = manager.list_alarms()

            if not alarms:
                print("No NBA Simulator alarms found")
            else:
                print(f"\nFound {len(alarms)} alarms:\n")
                for alarm in alarms:
                    print(f"  {alarm['name']}")
                    print(f"    State: {alarm['state']}")
                    print(f"    Metric: {alarm['metric']}")
                    print(f"    Threshold: {alarm['threshold']}")
                    print()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()

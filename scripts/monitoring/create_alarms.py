#!/usr/bin/env python3
"""
CloudWatch Alarms Setup
Part of Phase 0.0020 (Monitoring & Observability)

Creates CloudWatch alarms for critical system metrics with SNS notifications.

Usage:
    python scripts/monitoring/create_alarms.py --sns-topic arn:aws:sns:us-east-1:123456789:nba-simulator-alerts
    python scripts/monitoring/create_alarms.py --alarm adce-failure
    python scripts/monitoring/create_alarms.py --list

Alarms Created:
    1. ADCE-HighFailureRate: Alert when ADCE success rate < 95%
    2. AWS-CostBudgetExceeded: Alert when monthly costs > 80% of budget
    3. S3-UploadFailures: Alert when S3 uploads fail > 5 times in 10min
    4. Data-QualityIssues: Alert when validation pass rate < 95%
"""

import argparse
import boto3
import sys
from typing import List, Optional


class AlarmManager:
    """Manage CloudWatch alarms"""

    def __init__(self, region="us-east-1", sns_topic_arn=None):
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.region = region
        self.sns_topic_arn = sns_topic_arn

    def create_adce_failure_alarm(self) -> bool:
        """Alert when ADCE success rate drops below 95%"""
        print("📊 Creating ADCE failure alarm...")

        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName="ADCE-HighFailureRate",
                ComparisonOperator="LessThanThreshold",
                EvaluationPeriods=2,
                MetricName="ADCESuccessRate",
                Namespace="NBA-Simulator/ADCE",
                Period=300,
                Statistic="Average",
                Threshold=95.0,
                ActionsEnabled=True if self.sns_topic_arn else False,
                AlarmDescription="ADCE success rate dropped below 95% for 10 minutes",
                AlarmActions=[self.sns_topic_arn] if self.sns_topic_arn else [],
                TreatMissingData="notBreaching",
            )

            print("✅ Created: ADCE-HighFailureRate")
            return True

        except Exception as e:
            print(f"❌ Failed to create ADCE failure alarm: {e}")
            return False

    def create_cost_alarm(self, budget_limit=150.0) -> bool:
        """Alert when monthly costs exceed 80% of budget"""
        print(f"💰 Creating cost budget alarm (${budget_limit} limit)...")

        try:
            threshold = 80.0  # 80% of budget

            self.cloudwatch.put_metric_alarm(
                AlarmName="AWS-CostBudgetExceeded",
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=1,
                MetricName="BudgetUtilization",
                Namespace="NBA-Simulator/Costs",
                Period=86400,
                Statistic="Maximum",
                Threshold=threshold,
                ActionsEnabled=True if self.sns_topic_arn else False,
                AlarmDescription=f"AWS costs exceeded 80% of ${budget_limit} monthly budget",
                AlarmActions=[self.sns_topic_arn] if self.sns_topic_arn else [],
                TreatMissingData="notBreaching",
            )

            print(f"✅ Created: AWS-CostBudgetExceeded (threshold: {threshold}%)")
            return True

        except Exception as e:
            print(f"❌ Failed to create cost alarm: {e}")
            return False

    def create_upload_failure_alarm(self) -> bool:
        """Alert when S3 uploads fail repeatedly"""
        print("📦 Creating S3 upload failure alarm...")

        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName="S3-UploadFailures",
                ComparisonOperator="GreaterThanThreshold",
                EvaluationPeriods=2,
                MetricName="S3UploadFailures",
                Namespace="NBA-Simulator/DataCollection",
                Period=300,
                Statistic="Sum",
                Threshold=5,
                ActionsEnabled=True if self.sns_topic_arn else False,
                AlarmDescription="More than 5 S3 upload failures in 10 minutes",
                AlarmActions=[self.sns_topic_arn] if self.sns_topic_arn else [],
                TreatMissingData="notBreaching",
            )

            print("✅ Created: S3-UploadFailures")
            return True

        except Exception as e:
            print(f"❌ Failed to create S3 upload failure alarm: {e}")
            return False

    def create_quality_alarm(self) -> bool:
        """Alert when data validation fails"""
        print("🔍 Creating data quality alarm...")

        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName="Data-QualityIssues",
                ComparisonOperator="LessThanThreshold",
                EvaluationPeriods=1,
                MetricName="ValidationPassRate",
                Namespace="NBA-Simulator/DataQuality",
                Period=3600,
                Statistic="Average",
                Threshold=95.0,
                ActionsEnabled=True if self.sns_topic_arn else False,
                AlarmDescription="Data validation pass rate below 95%",
                AlarmActions=[self.sns_topic_arn] if self.sns_topic_arn else [],
                TreatMissingData="notBreaching",
            )

            print("✅ Created: Data-QualityIssues")
            return True

        except Exception as e:
            print(f"❌ Failed to create data quality alarm: {e}")
            return False

    def list_alarms(self):
        """List all existing alarms"""
        print("📋 Existing CloudWatch Alarms:")
        print("")

        try:
            response = self.cloudwatch.describe_alarms(
                AlarmNamePrefix="NBA-Simulator", MaxRecords=100
            )

            if not response["MetricAlarms"]:
                print("  No NBA Simulator alarms found")
                return

            for alarm in response["MetricAlarms"]:
                status = alarm["StateValue"]
                status_symbol = {
                    "OK": "✅",
                    "ALARM": "🚨",
                    "INSUFFICIENT_DATA": "⚠️",
                }.get(status, "❓")

                print(f"  {status_symbol} {alarm['AlarmName']}")
                print(f"     Status: {status}")
                print(f"     Metric: {alarm['Namespace']}/{alarm['MetricName']}")
                print(
                    f"     Threshold: {alarm['ComparisonOperator']} {alarm['Threshold']}"
                )
                print(f"     Actions: {len(alarm.get('AlarmActions', []))} configured")
                print("")

        except Exception as e:
            print(f"❌ Failed to list alarms: {e}")

    def delete_alarm(self, alarm_name: str) -> bool:
        """Delete a specific alarm"""
        print(f"🗑️  Deleting alarm: {alarm_name}...")

        try:
            self.cloudwatch.delete_alarms(AlarmNames=[alarm_name])
            print(f"✅ Deleted: {alarm_name}")
            return True

        except Exception as e:
            print(f"❌ Failed to delete alarm: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Create and manage CloudWatch alarms")
    parser.add_argument("--sns-topic", help="SNS topic ARN for alarm notifications")
    parser.add_argument(
        "--alarm",
        choices=["adce-failure", "cost", "upload-failure", "quality"],
        help="Create specific alarm",
    )
    parser.add_argument("--all", action="store_true", help="Create all alarms")
    parser.add_argument("--list", action="store_true", help="List existing alarms")
    parser.add_argument("--delete", help="Delete specific alarm by name")
    parser.add_argument(
        "--budget",
        type=float,
        default=150.0,
        help="Monthly budget limit (default: 150)",
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    # List alarms if requested
    if args.list:
        manager = AlarmManager(region=args.region)
        manager.list_alarms()
        sys.exit(0)

    # Delete alarm if requested
    if args.delete:
        manager = AlarmManager(region=args.region)
        success = manager.delete_alarm(args.delete)
        sys.exit(0 if success else 1)

    # Create alarms
    if not args.alarm and not args.all:
        parser.print_help()
        sys.exit(1)

    if not args.sns_topic:
        print(
            "⚠️  Warning: No SNS topic provided - alarms will be created but won't send notifications"
        )
        print("   Set up SNS first: bash scripts/monitoring/setup_sns.sh")
        print("")

    manager = AlarmManager(region=args.region, sns_topic_arn=args.sns_topic)
    success = True

    # Create specific alarm or all alarms
    if args.alarm == "adce-failure" or args.all:
        success &= manager.create_adce_failure_alarm()
        print("")

    if args.alarm == "cost" or args.all:
        success &= manager.create_cost_alarm(budget_limit=args.budget)
        print("")

    if args.alarm == "upload-failure" or args.all:
        success &= manager.create_upload_failure_alarm()
        print("")

    if args.alarm == "quality" or args.all:
        success &= manager.create_quality_alarm()
        print("")

    if success:
        print("✅ Alarm setup complete!")
        print("")
        print("View alarms at:")
        print(
            f"  https://console.aws.amazon.com/cloudwatch/home?region={args.region}#alarmsV2:"
        )
        sys.exit(0)
    else:
        print("❌ Some alarms failed to create")
        sys.exit(1)


if __name__ == "__main__":
    main()

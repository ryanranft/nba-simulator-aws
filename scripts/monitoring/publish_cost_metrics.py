#!/usr/bin/env python3
"""
CloudWatch Metrics Publisher - AWS Costs

Publishes AWS cost and budget utilization metrics to CloudWatch.
Part of Phase 0.0020 (Monitoring & Observability).

Usage:
    python scripts/monitoring/publish_cost_metrics.py
    python scripts/monitoring/publish_cost_metrics.py --budget 150

Metrics Published:
    - MonthlyAWSCost: Current month-to-date AWS costs (USD)
    - BudgetUtilization: Percentage of monthly budget used
    - S3Cost: Estimated S3 storage costs
    - RDSCost: Estimated RDS database costs

Note: Cost Explorer API has 24-hour lag. For real-time costs, use AWS Budgets.
"""

import argparse
import boto3
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any


class CostMetricsPublisher:
    """Publish AWS cost metrics to CloudWatch"""

    def __init__(self, region="us-east-1", budget_limit=150.0):
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.ce = boto3.client("ce", region_name=region)  # Cost Explorer
        self.s3 = boto3.client("s3", region_name=region)
        self.rds = boto3.client("rds", region_name=region)
        self.budget_limit = budget_limit
        self.bucket_name = "nba-sim-raw-data-lake"

    def get_cost_explorer_data(self) -> Dict[str, float]:
        """Get current month costs from Cost Explorer (24-hour lag)"""
        print("📊 Fetching AWS Cost Explorer data...")

        try:
            now = datetime.now()
            start_of_month = now.replace(day=1).strftime("%Y-%m-%d")
            today = now.strftime("%Y-%m-%d")

            response = self.ce.get_cost_and_usage(
                TimePeriod={"Start": start_of_month, "End": today},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            total_cost = 0.0
            s3_cost = 0.0
            rds_cost = 0.0

            if response["ResultsByTime"]:
                for group in response["ResultsByTime"][0]["Groups"]:
                    service = group["Keys"][0]
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])

                    total_cost += cost

                    if "S3" in service or "Simple Storage Service" in service:
                        s3_cost += cost
                    elif "RDS" in service or "Relational Database Service" in service:
                        rds_cost += cost

            print(f"  Total Cost (MTD): ${total_cost:.2f}")
            print(f"  S3 Cost: ${s3_cost:.2f}")
            print(f"  RDS Cost: ${rds_cost:.2f}")

            return {"total": total_cost, "s3": s3_cost, "rds": rds_cost}

        except Exception as e:
            print(f"⚠️  Cost Explorer API error: {e}")
            print("   Falling back to estimated costs...")
            return self._get_estimated_costs()

    def _get_estimated_costs(self) -> Dict[str, float]:
        """Estimate costs based on resource usage (when Cost Explorer unavailable)"""
        print("📊 Calculating estimated costs...")

        try:
            # Estimate S3 costs
            s3_cost = self._estimate_s3_cost()

            # Estimate RDS costs
            rds_cost = self._estimate_rds_cost()

            total_cost = s3_cost + rds_cost

            print(f"  Estimated Total: ${total_cost:.2f}")
            print(f"  Estimated S3: ${s3_cost:.2f}")
            print(f"  Estimated RDS: ${rds_cost:.2f}")

            return {"total": total_cost, "s3": s3_cost, "rds": rds_cost}

        except Exception as e:
            print(f"❌ Error estimating costs: {e}")
            # Return baseline costs as fallback
            return {"total": 31.72, "s3": 2.72, "rds": 29.0}

    def _estimate_s3_cost(self) -> float:
        """Estimate S3 storage costs"""
        try:
            # Get bucket size
            paginator = self.s3.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name)

            total_size = 0
            for page in pages:
                if "Contents" in page:
                    total_size += sum(obj["Size"] for obj in page["Contents"])

            size_gb = total_size / (1024**3)

            # S3 Standard pricing: $0.023/GB/month (us-east-1)
            cost = size_gb * 0.023

            return round(cost, 2)

        except Exception as e:
            print(f"⚠️  S3 cost estimation failed: {e}")
            return 2.72  # Baseline from DIMS

    def _estimate_rds_cost(self) -> float:
        """Estimate RDS costs"""
        try:
            # Get RDS instance details
            response = self.rds.describe_db_instances()

            total_cost = 0.0

            for instance in response["DBInstances"]:
                instance_class = instance["DBInstanceClass"]

                # db.t3.micro: ~$0.017/hour * 730 hours/month = $12.41
                # db.t4g.micro: ~$0.016/hour * 730 hours/month = $11.68
                # Add storage: 100GB * $0.115/GB/month = $11.50
                # Baseline: ~$29/month

                if "t3.micro" in instance_class or "t4g.micro" in instance_class:
                    total_cost += 29.0
                elif "t3.small" in instance_class:
                    total_cost += 58.0
                else:
                    total_cost += 100.0  # Conservative estimate for larger instances

            return round(total_cost, 2)

        except Exception as e:
            print(f"⚠️  RDS cost estimation failed: {e}")
            return 29.0  # Baseline from DIMS

    def get_cost_metrics(self) -> List[Dict[str, Any]]:
        """Collect cost metrics"""
        costs = self.get_cost_explorer_data()

        total_cost = costs["total"]
        budget_utilization = (total_cost / self.budget_limit) * 100

        print(
            f"💰 Budget Utilization: {budget_utilization:.1f}% of ${self.budget_limit}"
        )

        if budget_utilization > 80:
            print(f"⚠️  WARNING: Budget utilization above 80%!")
        elif budget_utilization > 90:
            print(f"🚨 CRITICAL: Budget utilization above 90%!")

        metrics = [
            {
                "MetricName": "MonthlyAWSCost",
                "Value": total_cost,
                "Unit": "None",  # Dollars
                "Timestamp": datetime.utcnow(),
            },
            {
                "MetricName": "BudgetUtilization",
                "Value": budget_utilization,
                "Unit": "Percent",
            },
            {
                "MetricName": "S3Cost",
                "Value": costs["s3"],
                "Unit": "None",  # Dollars
                "Dimensions": [{"Name": "Service", "Value": "S3"}],
            },
            {
                "MetricName": "RDSCost",
                "Value": costs["rds"],
                "Unit": "None",  # Dollars
                "Dimensions": [{"Name": "Service", "Value": "RDS"}],
            },
        ]

        return metrics

    def publish_metrics(self, metrics: List[Dict[str, Any]]) -> bool:
        """Publish metrics to CloudWatch"""
        try:
            response = self.cloudwatch.put_metric_data(
                Namespace="NBA-Simulator/Costs", MetricData=metrics
            )
            print(f"✅ Published {len(metrics)} cost metrics to CloudWatch")
            return True

        except Exception as e:
            print(f"❌ Error publishing cost metrics: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Publish AWS cost metrics to CloudWatch"
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=150.0,
        help="Monthly budget limit in USD (default: 150)",
    )
    parser.add_argument(
        "--region", default="us-east-1", help="AWS region (default: us-east-1)"
    )

    args = parser.parse_args()

    publisher = CostMetricsPublisher(region=args.region, budget_limit=args.budget)

    metrics = publisher.get_cost_metrics()

    if metrics:
        success = publisher.publish_metrics(metrics)
        sys.exit(0 if success else 1)
    else:
        print("❌ No metrics collected")
        sys.exit(1)


if __name__ == "__main__":
    main()

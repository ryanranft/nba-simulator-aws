"""
Cost Metrics Publisher

Publishes AWS cost metrics to CloudWatch using Cost Explorer API.
Tracks monthly spend, budget utilization, and per-service costs.

Phase 0.0020: Monitoring & Observability
"""

import boto3
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CostMetricsPublisher:
    """
    Publishes AWS cost metrics to CloudWatch.

    Fetches cost data from AWS Cost Explorer and publishes comprehensive
    metrics for budget tracking, cost optimization, and alerting.

    Usage:
        publisher = CostMetricsPublisher(budget_limit=150.0)
        publisher.publish_cost_metrics()
    """

    def __init__(self, budget_limit: float = 150.0, config_path: Optional[str] = None):
        """
        Initialize cost metrics publisher.

        Args:
            budget_limit: Monthly budget limit in USD (default: 150.0)
            config_path: Path to cloudwatch_config.yaml (optional)
        """
        self.budget_limit = budget_limit

        # Load CloudWatch configuration
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent.parent
                / "config"
                / "cloudwatch_config.yaml"
            )

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Override budget from config if present
        if (
            "cost_tracking" in self.config
            and "budget_limit" in self.config["cost_tracking"]
        ):
            self.budget_limit = self.config["cost_tracking"]["budget_limit"]

        # Initialize AWS clients
        region = self.config["aws"]["region"]
        self.ce = boto3.client("ce", region_name=region)  # Cost Explorer
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.namespace = self.config["namespaces"]["costs"]

        logger.info(
            f"Initialized cost metrics publisher (budget: ${budget_limit}, namespace: {self.namespace})"
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

    def get_month_to_date_costs(self) -> Dict[str, Any]:
        """
        Get month-to-date AWS costs from Cost Explorer.

        Returns:
            Dictionary containing:
            - total_cost: Total unblended cost for current month
            - costs_by_service: Breakdown by AWS service
            - start_date: Start of current month
            - end_date: Current date
        """
        logger.info("Fetching month-to-date costs from Cost Explorer...")

        # Get current month date range
        now = datetime.now()
        start_date = now.replace(day=1).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        try:
            # Fetch costs from Cost Explorer
            response = self.ce.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            # Extract total cost
            total_cost = 0.0
            if response["ResultsByTime"] and len(response["ResultsByTime"]) > 0:
                result = response["ResultsByTime"][0]
                total_cost = float(result["Total"]["UnblendedCost"]["Amount"])

            # Extract per-service costs
            costs_by_service = {}
            if response["ResultsByTime"] and len(response["ResultsByTime"]) > 0:
                result = response["ResultsByTime"][0]
                for group in result["Groups"]:
                    service = group["Keys"][0]
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    if cost > 0:  # Only include services with non-zero cost
                        costs_by_service[service] = cost

            logger.info(
                f"Month-to-date cost: ${total_cost:.2f} across {len(costs_by_service)} services"
            )

            return {
                "total_cost": total_cost,
                "costs_by_service": costs_by_service,
                "start_date": start_date,
                "end_date": end_date,
            }

        except Exception as e:
            logger.error(f"Error fetching costs from Cost Explorer: {e}")
            raise

    def get_forecast_costs(self) -> Optional[float]:
        """
        Get forecasted end-of-month cost from Cost Explorer.

        Returns:
            Forecasted monthly cost or None if unavailable
        """
        logger.info("Fetching cost forecast from Cost Explorer...")

        try:
            # Get current month range for forecast
            now = datetime.now()
            start_date = now.replace(day=1).strftime("%Y-%m-%d")

            # Forecast to end of current month
            last_day = (now.replace(day=28) + timedelta(days=4)).replace(
                day=1
            ) - timedelta(days=1)
            end_date = last_day.strftime("%Y-%m-%d")

            response = self.ce.get_cost_forecast(
                TimePeriod={"Start": start_date, "End": end_date},
                Metric="UNBLENDED_COST",
                Granularity="MONTHLY",
            )

            # Extract forecast
            if response["Total"] and "Amount" in response["Total"]:
                forecast = float(response["Total"]["Amount"])
                logger.info(f"Forecasted monthly cost: ${forecast:.2f}")
                return forecast

            return None

        except Exception as e:
            logger.warning(
                f"Error fetching cost forecast (may not have enough data): {e}"
            )
            return None

    def publish_cost_metrics(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Publish AWS cost metrics to CloudWatch.

        Metrics published:
        - MonthlyAWSCost (current month-to-date cost)
        - BudgetUtilization (percentage of budget used)
        - ForecastedMonthlyCost (forecasted end-of-month cost)
        - CostByService (per-service costs with dimensions)

        Args:
            dry_run: If True, don't actually publish (for testing)

        Returns:
            Summary of published metrics
        """
        logger.info("Publishing cost metrics to CloudWatch...")

        try:
            # Fetch cost data
            cost_data = self.get_month_to_date_costs()
            forecast_cost = self.get_forecast_costs()

        except Exception as e:
            logger.error(f"Error fetching cost data: {e}")
            return {
                "status": "error",
                "message": f"Error fetching cost data: {e}",
                "published_count": 0,
            }

        # Prepare metric data
        metric_data = []

        # Month-to-date cost
        total_cost = cost_data["total_cost"]
        metric_data.append(
            self._create_metric_data(
                "MonthlyAWSCost",
                total_cost,
                "None",  # Dollars (no specific unit in CloudWatch)
            )
        )

        # Budget utilization percentage
        budget_utilization = (
            (total_cost / self.budget_limit) * 100 if self.budget_limit > 0 else 0
        )
        metric_data.append(
            self._create_metric_data("BudgetUtilization", budget_utilization, "Percent")
        )

        # Forecasted cost (if available)
        if forecast_cost is not None:
            metric_data.append(
                self._create_metric_data("ForecastedMonthlyCost", forecast_cost, "None")
            )

            # Forecasted budget utilization
            forecast_utilization = (
                (forecast_cost / self.budget_limit) * 100
                if self.budget_limit > 0
                else 0
            )
            metric_data.append(
                self._create_metric_data(
                    "ForecastedBudgetUtilization", forecast_utilization, "Percent"
                )
            )

        # Per-service costs (with dimensions)
        for service, cost in cost_data["costs_by_service"].items():
            metric_data.append(
                self._create_metric_data(
                    "CostByService",
                    cost,
                    "None",
                    dimensions=[{"Name": "Service", "Value": service}],
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
            f"Successfully published {published_count} cost metrics to CloudWatch"
        )

        return {
            "status": "success",
            "namespace": self.namespace,
            "published_count": published_count,
            "cost_summary": {
                "month_to_date": total_cost,
                "budget_limit": self.budget_limit,
                "budget_utilization_pct": budget_utilization,
                "forecasted_monthly": forecast_cost,
                "services_tracked": len(cost_data["costs_by_service"]),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


def main():
    """CLI entry point for cost metrics publisher"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Publish AWS cost metrics to CloudWatch"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (don't actually publish)"
    )
    parser.add_argument(
        "--budget", type=float, default=150.0, help="Monthly budget limit in USD"
    )
    parser.add_argument("--config", type=str, help="Path to cloudwatch_config.yaml")

    args = parser.parse_args()

    try:
        publisher = CostMetricsPublisher(
            budget_limit=args.budget, config_path=args.config
        )
        result = publisher.publish_cost_metrics(dry_run=args.dry_run)

        print(f"\nCost Metrics Publishing Results:")
        print(f"Status: {result['status']}")
        print(f"Published: {result.get('published_count', 0)} metrics")

        if "cost_summary" in result:
            print(f"\nCost Summary:")
            print(f"  Month-to-Date: ${result['cost_summary']['month_to_date']:.2f}")
            print(f"  Budget Limit: ${result['cost_summary']['budget_limit']:.2f}")
            print(
                f"  Budget Utilization: {result['cost_summary']['budget_utilization_pct']:.1f}%"
            )
            if result["cost_summary"]["forecasted_monthly"]:
                print(
                    f"  Forecasted Monthly: ${result['cost_summary']['forecasted_monthly']:.2f}"
                )
            print(f"  Services Tracked: {result['cost_summary']['services_tracked']}")

        if result["status"] == "error":
            print(f"Error: {result.get('message', 'Unknown error')}")
            exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()

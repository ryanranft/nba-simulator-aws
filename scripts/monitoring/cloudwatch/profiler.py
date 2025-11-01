"""
Performance Profiler

Decorator-based performance profiling with CloudWatch integration.
Tracks function execution time, success/failure rates, and publishes to CloudWatch.

Phase 0.0020: Monitoring & Observability

Usage:
    from scripts.monitoring.cloudwatch.profiler import profile_performance

    @profile_performance('ReconciliationCycle')
    def reconcile():
        # Your code here
        pass
"""

import boto3
import yaml
import time
import functools
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """
    Singleton performance profiler that manages CloudWatch metric publishing.

    Tracks function execution times, success/failure rates, and other performance
    metrics, publishing them to CloudWatch for monitoring and alerting.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """Initialize profiler (only once due to singleton pattern)"""
        if self._initialized:
            return

        # Load CloudWatch configuration
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent.parent
                / "config"
                / "cloudwatch_config.yaml"
            )

        try:
            with open(config_path) as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load CloudWatch config: {e}. Using defaults.")
            self.config = {
                "enabled": True,
                "aws": {"region": "us-east-1"},
                "namespaces": {"performance": "NBA-Simulator/Performance"},
                "profiling": {"enabled": True, "sample_rate": 1.0},
            }

        # Check if profiling is enabled
        self.enabled = self.config.get("profiling", {}).get("enabled", True)
        self.sample_rate = self.config.get("profiling", {}).get("sample_rate", 1.0)

        if not self.enabled:
            logger.info("Performance profiling is disabled in config")
            self._initialized = True
            return

        # Initialize AWS CloudWatch client
        region = self.config["aws"]["region"]
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.namespace = self.config["namespaces"]["performance"]

        logger.info(
            f"Performance profiler initialized (namespace: {self.namespace}, sample_rate: {self.sample_rate})"
        )
        self._initialized = True

    def publish_metric(
        self,
        operation_name: str,
        duration: float,
        status: str = "success",
        additional_dimensions: Optional[dict] = None,
    ):
        """
        Publish performance metric to CloudWatch.

        Args:
            operation_name: Name of the operation being profiled
            duration: Execution duration in seconds
            status: 'success' or 'failure'
            additional_dimensions: Optional additional dimensions for the metric
        """
        if not self.enabled:
            return

        try:
            # Build dimensions
            dimensions = [
                {"Name": "Operation", "Value": operation_name},
                {"Name": "Status", "Value": status},
            ]

            if additional_dimensions:
                for key, value in additional_dimensions.items():
                    dimensions.append({"Name": key, "Value": str(value)})

            # Publish duration metric
            metric_data = [
                {
                    "MetricName": f"{operation_name}Duration",
                    "Value": duration,
                    "Unit": "Seconds",
                    "Dimensions": dimensions,
                    "Timestamp": datetime.utcnow(),
                },
                {
                    "MetricName": "OperationDuration",
                    "Value": duration,
                    "Unit": "Seconds",
                    "Dimensions": dimensions,
                    "Timestamp": datetime.utcnow(),
                },
            ]

            # Publish success/failure count
            metric_data.append(
                {
                    "MetricName": f"{operation_name}Executions",
                    "Value": 1,
                    "Unit": "Count",
                    "Dimensions": dimensions,
                    "Timestamp": datetime.utcnow(),
                }
            )

            self.cloudwatch.put_metric_data(
                Namespace=self.namespace, MetricData=metric_data
            )

            logger.debug(
                f"Published performance metric: {operation_name} ({duration:.3f}s, {status})"
            )

        except Exception as e:
            logger.warning(f"Error publishing performance metric: {e}")


# Global profiler instance
_profiler = PerformanceProfiler()


def profile_performance(
    operation_name: str,
    publish_to_cloudwatch: bool = True,
    additional_dimensions: Optional[dict] = None,
) -> Callable:
    """
    Decorator to profile function performance and publish to CloudWatch.

    Tracks execution time, success/failure status, and optionally publishes
    metrics to CloudWatch for monitoring and alerting.

    Args:
        operation_name: Name for the operation (used in metric names)
        publish_to_cloudwatch: Whether to publish to CloudWatch (default: True)
        additional_dimensions: Optional additional CloudWatch dimensions

    Returns:
        Decorated function

    Usage:
        @profile_performance('ReconciliationCycle')
        def reconcile_data():
            # Your code here
            pass

        @profile_performance('DatabaseQuery', additional_dimensions={'QueryType': 'SELECT'})
        def query_database(sql):
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Start timing
            start_time = time.time()
            status = "success"
            result = None

            try:
                # Execute function
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                # Mark as failure
                status = "failure"
                raise

            finally:
                # Calculate duration
                duration = time.time() - start_time

                # Log performance
                logger.info(f"{operation_name}: {duration:.3f}s ({status})")

                # Publish to CloudWatch
                if publish_to_cloudwatch and _profiler.enabled:
                    # Apply sampling if configured
                    import random

                    if random.random() <= _profiler.sample_rate:
                        _profiler.publish_metric(
                            operation_name, duration, status, additional_dimensions
                        )

        return wrapper

    return decorator


def profile_context(
    operation_name: str,
    publish_to_cloudwatch: bool = True,
    additional_dimensions: Optional[dict] = None,
):
    """
    Context manager for profiling code blocks.

    Usage:
        with profile_context('DataProcessing'):
            # Your code here
            process_data()
    """

    class ProfileContext:
        def __init__(self, op_name, publish, dims):
            self.operation_name = op_name
            self.publish = publish
            self.dimensions = dims
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            status = "failure" if exc_type is not None else "success"

            logger.info(f"{self.operation_name}: {duration:.3f}s ({status})")

            if self.publish and _profiler.enabled:
                import random

                if random.random() <= _profiler.sample_rate:
                    _profiler.publish_metric(
                        self.operation_name, duration, status, self.dimensions
                    )

            return False  # Don't suppress exceptions

    return ProfileContext(operation_name, publish_to_cloudwatch, additional_dimensions)


# Example usage functions
def example_decorator_usage():
    """Example of using the @profile_performance decorator"""

    @profile_performance("ExampleFunction")
    def my_function():
        time.sleep(0.1)  # Simulate work
        return "completed"

    result = my_function()
    print(f"Result: {result}")


def example_context_usage():
    """Example of using the profile_context context manager"""

    with profile_context("ExampleContext"):
        time.sleep(0.1)  # Simulate work
        print("Work completed")


if __name__ == "__main__":
    """Test performance profiler"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("Testing Performance Profiler...")
    print("\n1. Testing decorator:")
    example_decorator_usage()

    print("\n2. Testing context manager:")
    example_context_usage()

    print("\nPerformance profiler test complete!")

#!/usr/bin/env python3
"""
Performance Profiler - CloudWatch Integration

Decorator for automatically profiling function performance and publishing
metrics to CloudWatch. Part of Phase 0.0020 (Monitoring & Observability).

Usage:
    from scripts.monitoring.profiler import profile_performance

    @profile_performance('DataExtraction')
    def extract_game_data(game_id):
        # ... extraction logic ...
        pass

    @profile_performance('S3Upload')
    def upload_to_s3(file_path, bucket, key):
        # ... upload logic ...
        pass

Metrics Published:
    - {OperationName}Duration: Function execution time in seconds
    - {OperationName}SuccessCount: Number of successful executions
    - {OperationName}FailureCount: Number of failed executions

Dimensions:
    - Status: 'success' or 'failure'
    - FunctionName: Name of the decorated function
"""

import boto3
import functools
import logging
import time
from datetime import datetime
from typing import Callable, Any, Optional


logger = logging.getLogger(__name__)


class PerformanceProfiler:
    """Performance profiler with CloudWatch integration"""

    def __init__(self, region="us-east-1", enabled=True):
        self.enabled = enabled
        self.region = region
        self._cloudwatch = None

    @property
    def cloudwatch(self):
        """Lazy-load CloudWatch client"""
        if self._cloudwatch is None:
            self._cloudwatch = boto3.client("cloudwatch", region_name=self.region)
        return self._cloudwatch

    def publish_metric(
        self, operation_name: str, duration: float, status: str, function_name: str
    ) -> bool:
        """Publish performance metric to CloudWatch"""
        if not self.enabled:
            return False

        try:
            metrics = [
                {
                    "MetricName": f"{operation_name}Duration",
                    "Value": duration,
                    "Unit": "Seconds",
                    "Timestamp": datetime.utcnow(),
                    "Dimensions": [
                        {"Name": "Status", "Value": status},
                        {"Name": "FunctionName", "Value": function_name},
                    ],
                },
                {
                    "MetricName": f'{operation_name}{"Success" if status == "success" else "Failure"}Count',
                    "Value": 1,
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                    "Dimensions": [{"Name": "FunctionName", "Value": function_name}],
                },
            ]

            self.cloudwatch.put_metric_data(
                Namespace="NBA-Simulator/Performance", MetricData=metrics
            )

            logger.debug(
                f"Published {operation_name} metric: {duration:.3f}s ({status})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to publish performance metric: {e}")
            return False


# Global profiler instance
_profiler = PerformanceProfiler()


def configure_profiler(region="us-east-1", enabled=True):
    """Configure global profiler settings"""
    global _profiler
    _profiler = PerformanceProfiler(region=region, enabled=enabled)


def profile_performance(operation_name: str, log_level: str = "info"):
    """
    Decorator to profile function performance and publish to CloudWatch

    Args:
        operation_name: Name of the operation (e.g., 'DataExtraction', 'S3Upload')
        log_level: Logging level for performance info ('debug', 'info', 'warning')

    Returns:
        Decorated function that automatically profiles execution time

    Example:
        @profile_performance('GameDataExtraction')
        def extract_game(game_id):
            # ... extraction logic ...
            return game_data

        # Publishes:
        # - GameDataExtractionDuration: 2.45 seconds
        # - GameDataExtractionSuccessCount: 1
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            function_name = func.__name__
            start_time = time.time()
            status = "failure"
            result = None

            log_func = getattr(logger, log_level, logger.info)

            try:
                log_func(f"⏱️  Starting {operation_name} ({function_name})...")

                result = func(*args, **kwargs)
                status = "success"

                return result

            except Exception as e:
                logger.error(f"❌ {operation_name} failed: {e}")
                raise

            finally:
                duration = time.time() - start_time

                # Log performance
                if status == "success":
                    log_func(f"✅ {operation_name} completed in {duration:.3f}s")
                else:
                    logger.error(f"❌ {operation_name} failed after {duration:.3f}s")

                # Publish to CloudWatch
                try:
                    _profiler.publish_metric(
                        operation_name, duration, status, function_name
                    )
                except Exception as e:
                    # Don't fail the function if CloudWatch publish fails
                    logger.debug(f"CloudWatch publish failed: {e}")

        return wrapper

    return decorator


def profile_async_performance(operation_name: str, log_level: str = "info"):
    """
    Decorator to profile async function performance and publish to CloudWatch

    Args:
        operation_name: Name of the operation
        log_level: Logging level for performance info

    Returns:
        Decorated async function that automatically profiles execution time

    Example:
        @profile_async_performance('AsyncDataFetch')
        async def fetch_data(url):
            # ... async fetch logic ...
            return data
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            function_name = func.__name__
            start_time = time.time()
            status = "failure"
            result = None

            log_func = getattr(logger, log_level, logger.info)

            try:
                log_func(f"⏱️  Starting {operation_name} ({function_name})...")

                result = await func(*args, **kwargs)
                status = "success"

                return result

            except Exception as e:
                logger.error(f"❌ {operation_name} failed: {e}")
                raise

            finally:
                duration = time.time() - start_time

                if status == "success":
                    log_func(f"✅ {operation_name} completed in {duration:.3f}s")
                else:
                    logger.error(f"❌ {operation_name} failed after {duration:.3f}s")

                try:
                    _profiler.publish_metric(
                        operation_name, duration, status, function_name
                    )
                except Exception as e:
                    logger.debug(f"CloudWatch publish failed: {e}")

        return wrapper

    return decorator


# Context manager for manual profiling
class profile_context:
    """
    Context manager for manual performance profiling

    Usage:
        with profile_context('DatabaseQuery') as prof:
            # ... perform database query ...
            pass

        # Automatically publishes duration metric when exiting context
    """

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"⏱️  Starting {self.operation_name}...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        status = "failure" if exc_type is not None else "success"

        if status == "success":
            logger.info(f"✅ {self.operation_name} completed in {self.duration:.3f}s")
        else:
            logger.error(f"❌ {self.operation_name} failed after {self.duration:.3f}s")

        try:
            _profiler.publish_metric(
                self.operation_name, self.duration, status, "context_manager"
            )
        except Exception as e:
            logger.debug(f"CloudWatch publish failed: {e}")

        return False  # Don't suppress exceptions


if __name__ == "__main__":
    # Example usage
    import time

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Example 1: Decorator usage
    @profile_performance("TestOperation")
    def test_function():
        time.sleep(0.5)
        return "success"

    # Example 2: Context manager usage
    def manual_profiling():
        with profile_context("ManualOperation"):
            time.sleep(0.3)

    # Example 3: Async decorator usage
    @profile_async_performance("AsyncTest")
    async def async_test():
        import asyncio

        await asyncio.sleep(0.2)
        return "async success"

    # Run examples
    print("Example 1: Decorator")
    result = test_function()
    print(f"Result: {result}\n")

    print("Example 2: Context Manager")
    manual_profiling()
    print()

    print("Example 3: Async Decorator")
    import asyncio

    result = asyncio.run(async_test())
    print(f"Result: {result}")

    print("\n✅ Performance metrics published to CloudWatch")
    print("   Namespace: NBA-Simulator/Performance")

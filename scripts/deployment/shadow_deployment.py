#!/usr/bin/env python3
"""
Shadow Deployment Module for NBA Analytics Platform.

This module provides functionality to run shadow deployments where new model
versions or algorithm implementations can be tested against production traffic
without affecting user-facing results. It captures and compares predictions,
logs discrepancies, and provides metrics for evaluation.
"""

import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Status of shadow deployment execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"


class ComparisonResult(Enum):
    """Result of comparing primary and shadow outputs."""

    MATCH = "match"
    MISMATCH = "mismatch"
    ERROR = "error"


@dataclass
class ShadowResult:
    """Container for shadow deployment execution results."""

    deployment_id: str
    timestamp: datetime
    primary_output: Optional[Any]
    shadow_output: Optional[Any]
    primary_duration_ms: float
    shadow_duration_ms: float
    primary_status: DeploymentStatus
    shadow_status: DeploymentStatus
    comparison_result: ComparisonResult
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "deployment_id": self.deployment_id,
            "timestamp": self.timestamp.isoformat(),
            "primary_output": self.primary_output,
            "shadow_output": self.shadow_output,
            "primary_duration_ms": self.primary_duration_ms,
            "shadow_duration_ms": self.shadow_duration_ms,
            "primary_status": self.primary_status.value,
            "shadow_status": self.shadow_status.value,
            "comparison_result": self.comparison_result.value,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class ShadowMetrics:
    """Aggregated metrics for shadow deployment."""

    total_requests: int = 0
    successful_comparisons: int = 0
    mismatches: int = 0
    primary_errors: int = 0
    shadow_errors: int = 0
    timeouts: int = 0
    avg_primary_duration_ms: float = 0.0
    avg_shadow_duration_ms: float = 0.0
    match_rate: float = 0.0

    def update(self, result: ShadowResult) -> None:
        """Update metrics with a new result."""
        self.total_requests += 1

        if result.primary_status == DeploymentStatus.FAILURE:
            self.primary_errors += 1
        if result.shadow_status == DeploymentStatus.FAILURE:
            self.shadow_errors += 1
        if (
            result.primary_status == DeploymentStatus.TIMEOUT
            or result.shadow_status == DeploymentStatus.TIMEOUT
        ):
            self.timeouts += 1

        if result.comparison_result == ComparisonResult.MATCH:
            self.successful_comparisons += 1
        elif result.comparison_result == ComparisonResult.MISMATCH:
            self.mismatches += 1

        # Update average durations
        self.avg_primary_duration_ms = (
            self.avg_primary_duration_ms * (self.total_requests - 1)
            + result.primary_duration_ms
        ) / self.total_requests
        self.avg_shadow_duration_ms = (
            self.avg_shadow_duration_ms * (self.total_requests - 1)
            + result.shadow_duration_ms
        ) / self.total_requests

        # Calculate match rate
        if self.total_requests > 0:
            self.match_rate = self.successful_comparisons / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_comparisons": self.successful_comparisons,
            "mismatches": self.mismatches,
            "primary_errors": self.primary_errors,
            "shadow_errors": self.shadow_errors,
            "timeouts": self.timeouts,
            "avg_primary_duration_ms": round(self.avg_primary_duration_ms, 2),
            "avg_shadow_duration_ms": round(self.avg_shadow_duration_ms, 2),
            "match_rate": round(self.match_rate, 4),
        }


class ShadowDeployment:
    """
    Manages shadow deployments for testing new implementations.

    This class allows running a shadow (candidate) implementation alongside
    a primary (production) implementation, comparing results and collecting
    metrics without affecting production traffic.
    """

    def __init__(
        self,
        primary_callable: Callable,
        shadow_callable: Callable,
        comparison_fn: Optional[Callable[[Any, Any], bool]] = None,
        timeout_seconds: float = 30.0,
        sample_rate: float = 1.0,
        max_workers: int = 2,
    ):
        """
        Initialize shadow deployment.

        Args:
            primary_callable: The production implementation to use for actual results.
            shadow_callable: The candidate implementation to test.
            comparison_fn: Optional function to compare outputs. Should return True
                          if outputs match. Defaults to equality check.
            timeout_seconds: Maximum time to wait for each callable to complete.
            sample_rate: Fraction of requests to shadow (0.0 to 1.0).
            max_workers: Maximum number of worker threads for parallel execution.

        Raises:
            ValueError: If sample_rate is not between 0.0 and 1.0.
        """
        if not 0.0 <= sample_rate <= 1.0:
            raise ValueError(
                f"sample_rate must be between 0.0 and 1.0, got {sample_rate}"
            )

        self.primary_callable = primary_callable
        self.shadow_callable = shadow_callable
        self.comparison_fn = comparison_fn or self._default_comparison
        self.timeout_seconds = timeout_seconds
        self.sample_rate = sample_rate
        self.max_workers = max_workers

        self.metrics = ShadowMetrics()
        self.results_history: List[ShadowResult] = []
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

        logger.info(
            f"Initialized ShadowDeployment with sample_rate={sample_rate}, "
            f"timeout={timeout_seconds}s"
        )

    @staticmethod
    def _default_comparison(primary_output: Any, shadow_output: Any) -> bool:
        """Default comparison function using equality."""
        return primary_output == shadow_output

    def _execute_callable(
        self, callable_fn: Callable, *args: Any, **kwargs: Any
    ) -> Tuple[Optional[Any], float, DeploymentStatus, Optional[str]]:
        """
        Execute a callable with timeout and error handling.

        Args:
            callable_fn: The function to execute.
            *args: Positional arguments for the callable.
            **kwargs: Keyword arguments for the callable.

        Returns:
            Tuple of (output, duration_ms, status, error_message).
        """
        start_time = time.time()
        output = None
        status = DeploymentStatus.SUCCESS
        error_message = None

        try:
            future = self._executor.submit(callable_fn, *args, **kwargs)
            output = future.result(timeout=self.timeout_seconds)
        except FuturesTimeoutError:
            status = DeploymentStatus.TIMEOUT
            error_message = f"Execution exceeded timeout of {self.timeout_seconds}s"
            logger.warning(f"Callable timed out: {callable_fn.__name__}")
        except Exception as e:
            status = DeploymentStatus.FAILURE
            error_message = f"{type(e).__name__}: {str(e)}"
            logger.error(
                f"Error executing {callable_fn.__name__}: {error_message}",
                exc_info=True,
            )

        duration_ms = (time.time() - start_time) * 1000
        return output, duration_ms, status, error_message

    def _compare_outputs(
        self,
        primary_output: Optional[Any],
        shadow_output: Optional[Any],
        primary_status: DeploymentStatus,
        shadow_status: DeploymentStatus,
    ) -> ComparisonResult:
        """
        Compare primary and shadow outputs.

        Args:
            primary_output: Output from primary callable.
            shadow_output: Output from shadow callable.
            primary_status: Execution status of primary callable.
            shadow_status: Execution status of shadow callable.

        Returns:
            ComparisonResult indicating match, mismatch, or error.
        """
        # If either execution failed, can't compare
        if (
            primary_status != DeploymentStatus.SUCCESS
            or shadow_status != DeploymentStatus.SUCCESS
        ):
            return ComparisonResult.ERROR

        try:
            matches = self.comparison_fn(primary_output, shadow_output)
            return ComparisonResult.MATCH if matches else ComparisonResult.MISMATCH
        except Exception as e:
            logger.error(f"Error comparing outputs: {e}", exc_info=True)
            return ComparisonResult.ERROR

    def execute(
        self, *args: Any, metadata: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Tuple[Any, ShadowResult]:
        """
        Execute both primary and shadow callables with the given arguments.

        Args:
            *args: Positional arguments to pass to both callables.
            metadata: Optional metadata to attach to the result.
            **kwargs: Keyword arguments to pass to both callables.

        Returns:
            Tuple of (primary_output, shadow_result).
            The primary output is always returned for production use.
        """
        deployment_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        logger.debug(f"Starting shadow deployment {deployment_id}")

        # Always execute primary
        primary_output, primary_duration, primary_status, primary_error = (
            self._execute_callable(self.primary_callable, *args, **kwargs)
        )

        # Execute shadow based on sample rate
        import random

        should_shadow = random.random() < self.sample_rate  # nosec B311

        if should_shadow:
            shadow_output, shadow_duration, shadow_status, shadow_error = (
                self._execute_callable(self.shadow_callable, *args, **kwargs)
            )

            comparison_result = self._compare_outputs(
                primary_output, shadow_output, primary_status, shadow_status
            )

            error_message = primary_error or shadow_error
        else:
            # Skip shadow execution
            shadow_output = None
            shadow_duration = 0.0
            shadow_status = DeploymentStatus.SUCCESS
            comparison_result = ComparisonResult.MATCH
            error_message = primary_error

        # Create result object
        result = ShadowResult(
            deployment_id=deployment_id,
            timestamp=timestamp,
            primary_output=primary_output,
            shadow_output=shadow_output,
            primary_duration_ms=primary_duration,
            shadow_duration_ms=shadow_duration,
            primary_status=primary_status,
            shadow_status=shadow_status,
            comparison_result=comparison_result,
            error_message=error_message,
            metadata=metadata or {},
        )

        # Update metrics and history
        if should_shadow:
            self.metrics.update(result)
            self.results_history.append(result)

        # Log mismatches
        if comparison_result == ComparisonResult.MISMATCH:
            logger.warning(
                f"Shadow mismatch detected in {deployment_id}: "
                f"primary={primary_output}, shadow={shadow_output}"
            )

        return primary_output, result

    def get_metrics(self) -> ShadowMetrics:
        """
        Get current aggregated metrics.

        Returns:
            ShadowMetrics object with current statistics.
        """
        return self.metrics

    def get_results_history(
        self,
        limit: Optional[int] = None,
        status_filter: Optional[ComparisonResult] = None,
    ) -> List[ShadowResult]:
        """
        Get historical results with optional filtering.

        Args:
            limit: Maximum number of results to return (most recent first).
            status_filter: Optional filter by comparison result.

        Returns:
            List of ShadowResult objects.
        """
        results = self.results_history

        if status_filter:
            results = [r for r in results if r.comparison_result == status_filter]

        results = sorted(results, key=lambda r: r.timestamp, reverse=True)

        if limit:
            results = results[:limit]

        return results

    def reset_metrics(self) -> None:
        """Reset metrics and clear results history."""
        self.metrics = ShadowMetrics()
        self.results_history.clear()
        logger.info("Shadow deployment metrics reset")

    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources."""
        self._executor.shutdown(wait=True)
        logger.info("Shadow deployment executor shutdown")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


class ShadowDeploymentManager:
    """
    Manages multiple shadow deployments across different features.

    This class provides a centralized way to manage multiple shadow deployments,
    useful for testing multiple features or models simultaneously.
    """

    def __init__(self):
        """Initialize the shadow deployment manager."""
        self.deployments: Dict[str, ShadowDeployment] = {}
        logger.info("Initialized ShadowDeploymentManager")

    def register_deployment(self, name: str, deployment: ShadowDeployment) -> None:
        """
        Register a shadow deployment.

        Args:
            name: Unique name for the deployment.
            deployment: ShadowDeployment instance.

        Raises:
            ValueError: If deployment name already exists.
        """
        if name in self.deployments:
            raise ValueError(f"Deployment '{name}' already registered")

        self.deployments[name] = deployment
        logger.info(f"Registered shadow deployment: {name}")

    def unregister_deployment(self, name: str) -> None:
        """
        Unregister and shutdown a shadow deployment.

        Args:
            name: Name of the deployment to unregister.

        Raises:
            KeyError: If deployment name doesn't exist.
        """
        if name not in self.deployments:
            raise KeyError(f"Deployment '{name}' not found")

        deployment = self.deployments.pop(name)
        deployment.shutdown()
        logger.info(f"Unregistered shadow deployment: {name}")

    def execute(
        self,
        name: str,
        *args: Any,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Tuple[Any, ShadowResult]:
        """
        Execute a specific shadow deployment.

        Args:
            name: Name of the deployment to execute.
            *args: Positional arguments for the deployment.
            metadata: Optional metadata to attach.
            **kwargs: Keyword arguments for the deployment.

        Returns:
            Tuple of (primary_output, shadow_result).

        Raises:
            KeyError: If deployment name doesn't exist.
        """
        if name not in self.deployments:
            raise KeyError(f"Deployment '{name}' not found")

        return self.deployments[name].execute(*args, metadata=metadata, **kwargs)

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all registered deployments.

        Returns:
            Dictionary mapping deployment names to their metrics.
        """
        return {
            name: deployment.get_metrics().to_dict()
            for name, deployment in self.deployments.items()
        }

    def reset_all_metrics(self) -> None:
        """Reset metrics for all registered deployments."""
        for deployment in self.deployments.values():
            deployment.reset_metrics()
        logger.info("Reset metrics for all deployments")

    def shutdown_all(self) -> None:
        """Shutdown all registered deployments."""
        for name in list(self.deployments.keys()):
            self.unregister_deployment(name)
        logger.info("Shutdown all shadow deployments")


if __name__ == "__main__":
    # Example usage and testing
    import json

    def primary_predict_score(team_a: str, team_b: str) -> Dict[str, int]:
        """Primary (production) prediction model."""
        time.sleep(0.1)  # Simulate processing
        return {"team_a_score": 105, "team_b_score": 98}

    def shadow_predict_score(team_a: str, team_b: str) -> Dict[str, int]:
        """Shadow (candidate) prediction model."""
        time.sleep(0.15)  # Simulate slightly slower processing
        return {"team_a_score": 107, "team_b_score": 98}

    def compare_predictions(primary: Dict, shadow: Dict) -> bool:
        """Custom comparison allowing small differences."""
        if not primary or not shadow:
            return False
        diff_a = abs(primary.get("team_a_score", 0) - shadow.get("team_a_score", 0))
        diff_b = abs(primary.get("team_b_score", 0) - shadow.get("team_b_score", 0))
        return diff_a <= 5 and diff_b <= 5

    # Create shadow deployment
    with ShadowDeployment(
        primary_callable=primary_predict_score,
        shadow_callable=shadow_predict_score,
        comparison_fn=compare_predictions,
        timeout_seconds=5.0,
        sample_rate=1.0,
    ) as shadow:

        # Execute some predictions
        for i in range(5):
            result, shadow_result = shadow.execute(
                "Lakers", "Warriors", metadata={"request_id": f"req_{i}"}
            )
            print(f"\nRequest {i + 1}:")
            print(f"  Primary output: {result}")
            print(f"  Comparison: {shadow_result.comparison_result.value}")
            print(f"  Primary duration: {shadow_result.primary_duration_ms:.2f}ms")
            print(f"  Shadow duration: {shadow_result.shadow_duration_ms:.2f}ms")

        # Print metrics
        metrics = shadow.get_metrics()
        print("\n" + "=" * 50)
        print("Shadow Deployment Metrics:")
        print(json.dumps(metrics.to_dict(), indent=2))

        # Get mismatch history
        mismatches = shadow.get_results_history(status_filter=ComparisonResult.MISMATCH)
        print(f"\nTotal mismatches: {len(mismatches)}")

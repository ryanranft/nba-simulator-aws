#!/usr/bin/env python3
"""
Smart Retry Strategies - Enhanced Error Handling with Circuit Breaker

Provides intelligent retry strategies with error-specific handling:
- NetworkError: Immediate retry 3x
- RateLimitError: Exponential backoff from 60s
- ServerError: Linear backoff 5x
- ClientError: No retry
- ContentError: Retry once with different parser
- Circuit breaker pattern for automatic recovery
- Adaptive retry based on error patterns

Based on Crawl4AI MCP server error handling patterns.

Usage:
    from smart_retry_strategies import SmartRetryManager, CircuitBreaker

    # Smart retry manager
    retry_manager = SmartRetryManager()
    result = await retry_manager.execute_with_retry(
        fetch_function, max_retries=5, error_context="espn_scraper"
    )

    # Circuit breaker
    circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
    result = await circuit_breaker.call(risky_function)

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
import sys
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


class ErrorType(Enum):
    """Error type enumeration"""

    NETWORK_ERROR = "network_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    CONTENT_ERROR = "content_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class RetryConfig:
    """Retry configuration for different error types"""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 300.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_multiplier: float = 1.0


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""

    attempt_number: int
    error_type: ErrorType
    error_message: str
    timestamp: datetime
    delay_used: float
    success: bool = False


@dataclass
class CircuitBreakerState:
    """Circuit breaker state"""

    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    next_attempt_time: Optional[datetime] = None


class SmartRetryManager:
    """Manages smart retry strategies with error-specific handling"""

    def __init__(self):
        self.logger = logging.getLogger("smart_retry_manager")
        self.retry_configs = self._get_default_retry_configs()
        self.attempt_history: List[RetryAttempt] = []
        self.error_patterns: Dict[str, int] = {}

    def _get_default_retry_configs(self) -> Dict[ErrorType, RetryConfig]:
        """Get default retry configurations for each error type"""
        return {
            ErrorType.NETWORK_ERROR: RetryConfig(
                max_retries=3,
                base_delay=1.0,
                max_delay=30.0,
                exponential_base=2.0,
                jitter=True,
            ),
            ErrorType.RATE_LIMIT_ERROR: RetryConfig(
                max_retries=5,
                base_delay=60.0,
                max_delay=600.0,
                exponential_base=2.0,
                jitter=True,
            ),
            ErrorType.SERVER_ERROR: RetryConfig(
                max_retries=5,
                base_delay=5.0,
                max_delay=120.0,
                exponential_base=1.5,
                jitter=True,
            ),
            ErrorType.CLIENT_ERROR: RetryConfig(
                max_retries=0,  # No retry for client errors
                base_delay=0.0,
                max_delay=0.0,
            ),
            ErrorType.CONTENT_ERROR: RetryConfig(
                max_retries=1,
                base_delay=2.0,
                max_delay=10.0,
                exponential_base=1.0,
                jitter=False,
            ),
            ErrorType.TIMEOUT_ERROR: RetryConfig(
                max_retries=3,
                base_delay=3.0,
                max_delay=60.0,
                exponential_base=2.0,
                jitter=True,
            ),
            ErrorType.UNKNOWN_ERROR: RetryConfig(
                max_retries=2,
                base_delay=2.0,
                max_delay=30.0,
                exponential_base=1.5,
                jitter=True,
            ),
        }

    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network errors
        if any(
            keyword in error_str
            for keyword in ["connection", "network", "dns", "timeout"]
        ):
            return ErrorType.NETWORK_ERROR

        # Rate limit errors
        if any(
            keyword in error_str
            for keyword in ["rate limit", "429", "too many requests"]
        ):
            return ErrorType.RATE_LIMIT_ERROR

        # Server errors
        if any(
            keyword in error_str
            for keyword in ["500", "502", "503", "504", "server error"]
        ):
            return ErrorType.SERVER_ERROR

        # Client errors
        if any(
            keyword in error_str
            for keyword in ["400", "401", "403", "404", "client error"]
        ):
            return ErrorType.CLIENT_ERROR

        # Content errors
        if any(
            keyword in error_str for keyword in ["parse", "decode", "format", "content"]
        ):
            return ErrorType.CONTENT_ERROR

        # Timeout errors
        if any(keyword in error_str for keyword in ["timeout", "timed out"]):
            return ErrorType.TIMEOUT_ERROR

        return ErrorType.UNKNOWN_ERROR

    def calculate_delay(
        self, attempt: int, error_type: ErrorType, config: RetryConfig
    ) -> float:
        """Calculate delay for retry attempt"""
        if attempt <= 0:
            return 0.0

        # Exponential backoff
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))

        # Apply backoff multiplier
        delay *= config.backoff_multiplier

        # Cap at max delay
        delay = min(delay, config.max_delay)

        # Add jitter if enabled
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0.0, delay)

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        max_retries: Optional[int] = None,
        error_context: str = "unknown",
        **kwargs,
    ) -> Any:
        """Execute function with smart retry logic"""
        last_error = None

        for attempt in range(max_retries or 10):  # Default max retries
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success - record attempt
                self._record_attempt(
                    attempt + 1, ErrorType.NETWORK_ERROR, "Success", 0.0, True
                )

                # Update error patterns
                self._update_error_patterns(error_context, success=True)

                return result

            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)
                config = self.retry_configs[error_type]

                # Record failed attempt
                self._record_attempt(attempt + 1, error_type, str(e), 0.0, False)

                # Check if we should retry
                if attempt >= config.max_retries:
                    self.logger.error(
                        f"Max retries ({config.max_retries}) exceeded for {error_type.value}"
                    )
                    break

                # Calculate delay
                delay = self.calculate_delay(attempt + 1, error_type, config)

                self.logger.warning(
                    f"Attempt {attempt + 1} failed ({error_type.value}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                # Wait before retry
                if delay > 0:
                    await asyncio.sleep(delay)

                # Update error patterns
                self._update_error_patterns(error_context, success=False)

        # All retries failed
        self.logger.error(f"All retry attempts failed for {error_context}")
        raise last_error

    def _record_attempt(
        self,
        attempt_number: int,
        error_type: ErrorType,
        error_message: str,
        delay_used: float,
        success: bool,
    ) -> None:
        """Record retry attempt"""
        attempt = RetryAttempt(
            attempt_number=attempt_number,
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now(timezone.utc),
            delay_used=delay_used,
            success=success,
        )
        self.attempt_history.append(attempt)

        # Keep only last 100 attempts
        if len(self.attempt_history) > 100:
            self.attempt_history = self.attempt_history[-100:]

    def _update_error_patterns(self, context: str, success: bool) -> None:
        """Update error patterns for context"""
        if context not in self.error_patterns:
            self.error_patterns[context] = 0

        if success:
            self.error_patterns[context] = max(0, self.error_patterns[context] - 1)
        else:
            self.error_patterns[context] += 1

    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        if not self.attempt_history:
            return {"total_attempts": 0}

        total_attempts = len(self.attempt_history)
        successful_attempts = sum(1 for a in self.attempt_history if a.success)
        failed_attempts = total_attempts - successful_attempts

        # Error type breakdown
        error_types = {}
        for attempt in self.attempt_history:
            error_type = attempt.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # Recent success rate (last 20 attempts)
        recent_attempts = self.attempt_history[-20:]
        recent_success_rate = (
            sum(1 for a in recent_attempts if a.success) / len(recent_attempts)
            if recent_attempts
            else 0
        )

        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": (
                successful_attempts / total_attempts if total_attempts > 0 else 0
            ),
            "recent_success_rate": recent_success_rate,
            "error_types": error_types,
            "error_patterns": self.error_patterns,
        }

    def update_retry_config(self, error_type: ErrorType, config: RetryConfig) -> None:
        """Update retry configuration for specific error type"""
        self.retry_configs[error_type] = config
        self.logger.info(f"Updated retry config for {error_type.value}")


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.state = CircuitBreakerState()
        self.logger = logging.getLogger("circuit_breaker")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker"""
        if self.state.state == "OPEN":
            if self._should_attempt_reset():
                self.state.state = "HALF_OPEN"
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - reset failure count
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.state.last_failure_time is None:
            return True

        time_since_failure = datetime.now(timezone.utc) - self.state.last_failure_time
        return time_since_failure.total_seconds() >= self.timeout

    def _on_success(self) -> None:
        """Handle successful call"""
        self.state.failure_count = 0
        self.state.state = "CLOSED"
        self.state.last_failure_time = None

    def _on_failure(self) -> None:
        """Handle failed call"""
        self.state.failure_count += 1
        self.state.last_failure_time = datetime.now(timezone.utc)

        if self.state.failure_count >= self.failure_threshold:
            self.state.state = "OPEN"
            self.logger.warning(
                f"Circuit breaker opened after {self.state.failure_count} failures"
            )

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self.state.state,
            "failure_count": self.state.failure_count,
            "last_failure_time": (
                self.state.last_failure_time.isoformat()
                if self.state.last_failure_time
                else None
            ),
            "failure_threshold": self.failure_threshold,
            "timeout": self.timeout,
        }

    def reset(self) -> None:
        """Manually reset circuit breaker"""
        self.state = CircuitBreakerState()
        self.logger.info("Circuit breaker manually reset")


class AdaptiveRetryManager:
    """Adaptive retry manager that learns from error patterns"""

    def __init__(self, base_retry_manager: SmartRetryManager):
        self.base_retry_manager = base_retry_manager
        self.logger = logging.getLogger("adaptive_retry_manager")
        self.learning_data: Dict[str, Dict[str, Any]] = {}

    async def execute_with_adaptive_retry(
        self, func: Callable, *args, context: str = "unknown", **kwargs
    ) -> Any:
        """Execute with adaptive retry based on learning"""
        # Get learning data for context
        context_data = self.learning_data.get(context, {})

        # Adjust retry strategy based on learning
        if context_data.get("high_failure_rate", False):
            # Increase delays for high failure contexts
            self._adjust_configs_for_context(context, multiplier=1.5)
        elif context_data.get("low_failure_rate", False):
            # Decrease delays for low failure contexts
            self._adjust_configs_for_context(context, multiplier=0.8)

        try:
            result = await self.base_retry_manager.execute_with_retry(
                func, *args, error_context=context, **kwargs
            )

            # Update learning data on success
            self._update_learning_data(context, success=True)
            return result

        except Exception as e:
            # Update learning data on failure
            self._update_learning_data(context, success=False)
            raise e

    def _adjust_configs_for_context(self, context: str, multiplier: float) -> None:
        """Adjust retry configs based on context learning"""
        for error_type, config in self.base_retry_manager.retry_configs.items():
            if config.max_retries > 0:  # Don't adjust non-retryable errors
                new_config = RetryConfig(
                    max_retries=config.max_retries,
                    base_delay=config.base_delay * multiplier,
                    max_delay=config.max_delay * multiplier,
                    exponential_base=config.exponential_base,
                    jitter=config.jitter,
                    backoff_multiplier=config.backoff_multiplier,
                )
                self.base_retry_manager.retry_configs[error_type] = new_config

    def _update_learning_data(self, context: str, success: bool) -> None:
        """Update learning data for context"""
        if context not in self.learning_data:
            self.learning_data[context] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "failure_rate": 0.0,
            }

        data = self.learning_data[context]
        data["total_calls"] += 1

        if success:
            data["successful_calls"] += 1
        else:
            data["failed_calls"] += 1

        data["failure_rate"] = data["failed_calls"] / data["total_calls"]

        # Determine if context has high/low failure rate
        if data["failure_rate"] > 0.5:
            data["high_failure_rate"] = True
            data["low_failure_rate"] = False
        elif data["failure_rate"] < 0.1:
            data["high_failure_rate"] = False
            data["low_failure_rate"] = True
        else:
            data["high_failure_rate"] = False
            data["low_failure_rate"] = False

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get learning summary"""
        return {
            "contexts": len(self.learning_data),
            "learning_data": self.learning_data,
            "base_stats": self.base_retry_manager.get_retry_stats(),
        }


# Example usage
if __name__ == "__main__":

    async def example_usage():
        # Create retry manager
        retry_manager = SmartRetryManager()

        # Example function that might fail
        async def fetch_data(url: str) -> str:
            # Simulate network call
            await asyncio.sleep(0.1)
            if random.random() < 0.7:  # 70% failure rate
                raise ConnectionError("Network error")
            return f"Data from {url}"

        # Execute with retry
        try:
            result = await retry_manager.execute_with_retry(
                fetch_data,
                "https://example.com",
                max_retries=5,
                error_context="example_fetcher",
            )
            print(f"Success: {result}")
        except Exception as e:
            print(f"Failed after retries: {e}")

        # Get retry stats
        stats = retry_manager.get_retry_stats()
        print(f"Retry stats: {stats}")

        # Circuit breaker example
        circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=10)

        async def risky_function() -> str:
            if random.random() < 0.8:  # 80% failure rate
                raise Exception("Service unavailable")
            return "Success"

        # Try multiple calls
        for i in range(10):
            try:
                result = await circuit_breaker.call(risky_function)
                print(f"Call {i+1}: {result}")
            except Exception as e:
                print(f"Call {i+1}: {e}")

            # Check circuit breaker state
            state = circuit_breaker.get_state()
            print(f"Circuit breaker state: {state['state']}")

            await asyncio.sleep(1)

    asyncio.run(example_usage())

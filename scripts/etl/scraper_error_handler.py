#!/usr/bin/env python3
"""
Scraper Error Handler - Centralized Error Management

Provides comprehensive error handling for NBA data scrapers with:
- Custom exception hierarchy
- Smart retry strategies based on error type
- Circuit breaker pattern for failing endpoints
- Detailed error logging and metrics
- Recovery strategies

Based on Crawl4AI MCP server error handling patterns.

Usage:
    from scraper_error_handler import ScraperErrorHandler, NetworkError, RateLimitError

    handler = ScraperErrorHandler()

    try:
        # Scraping operation
        pass
    except NetworkError as e:
        await handler.handle_network_error(e)
    except RateLimitError as e:
        await handler.handle_rate_limit_error(e)

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Type
from datetime import datetime, timezone


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""

    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    CLIENT = "client"
    CONTENT = "content"
    VALIDATION = "validation"
    STORAGE = "storage"
    CONFIGURATION = "configuration"


@dataclass
class ErrorContext:
    """Context information for errors"""

    url: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    response_headers: Optional[Dict] = None
    request_headers: Optional[Dict] = None
    retry_count: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scraper_name: Optional[str] = None
    data_type: Optional[str] = None


class ScraperError(Exception):
    """Base exception for all scraper errors"""

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.CLIENT,
    ):
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.severity = severity
        self.category = category
        self.timestamp = datetime.now(timezone.utc)


class NetworkError(ScraperError):
    """Network-related errors (timeouts, connection failures)"""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, context, ErrorSeverity.MEDIUM, ErrorCategory.NETWORK)


class RateLimitError(ScraperError):
    """Rate limiting errors (HTTP 429)"""

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(
            message, context, ErrorSeverity.MEDIUM, ErrorCategory.RATE_LIMIT
        )
        self.retry_after = retry_after


class ServerError(ScraperError):
    """Server errors (HTTP 5xx)"""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, context, ErrorSeverity.HIGH, ErrorCategory.SERVER)


class ClientError(ScraperError):
    """Client errors (HTTP 4xx, except 429)"""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, context, ErrorSeverity.HIGH, ErrorCategory.CLIENT)


class ContentError(ScraperError):
    """Content parsing/validation errors"""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, context, ErrorSeverity.MEDIUM, ErrorCategory.CONTENT)


class ValidationError(ScraperError):
    """Data validation errors"""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, context, ErrorSeverity.HIGH, ErrorCategory.VALIDATION)


class StorageError(ScraperError):
    """Storage-related errors (S3, local file system)"""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, context, ErrorSeverity.HIGH, ErrorCategory.STORAGE)


class ConfigurationError(ScraperError):
    """Configuration-related errors"""

    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(
            message, context, ErrorSeverity.CRITICAL, ErrorCategory.CONFIGURATION
        )


@dataclass
class RetryStrategy:
    """Retry strategy configuration"""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    retryable_errors: List[Type[ScraperError]] = field(default_factory=list)


@dataclass
class CircuitBreakerState:
    """Circuit breaker state tracking"""

    failure_count: int = 0
    last_failure_time: Optional[float] = None
    state: str = "closed"  # closed, open, half-open
    failure_threshold: int = 5
    recovery_timeout: float = 60.0


class CircuitBreaker:
    """Circuit breaker for failing endpoints"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitBreakerState(failure_threshold=failure_threshold)

    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        now = time.time()

        if self.state.state == "closed":
            return True
        elif self.state.state == "open":
            if now - self.state.last_failure_time >= self.recovery_timeout:
                self.state.state = "half-open"
                return True
            return False
        elif self.state.state == "half-open":
            return True

        return False

    def record_success(self) -> None:
        """Record successful operation"""
        self.state.failure_count = 0
        self.state.state = "closed"

    def record_failure(self) -> None:
        """Record failed operation"""
        self.state.failure_count += 1
        self.state.last_failure_time = time.time()

        if self.state.failure_count >= self.failure_threshold:
            self.state.state = "open"


class ScraperErrorHandler:
    """Centralized error handler for scrapers"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_stats: Dict[str, int] = {}
        self.retry_strategies: Dict[ErrorCategory, RetryStrategy] = (
            self._default_retry_strategies()
        )

    def _default_retry_strategies(self) -> Dict[ErrorCategory, RetryStrategy]:
        """Default retry strategies for different error types"""
        return {
            ErrorCategory.NETWORK: RetryStrategy(
                max_attempts=3,
                base_delay=1.0,
                exponential_backoff=True,
                retryable_errors=[NetworkError],
            ),
            ErrorCategory.RATE_LIMIT: RetryStrategy(
                max_attempts=5,
                base_delay=60.0,
                max_delay=300.0,
                exponential_backoff=True,
                retryable_errors=[RateLimitError],
            ),
            ErrorCategory.SERVER: RetryStrategy(
                max_attempts=5,
                base_delay=2.0,
                exponential_backoff=True,
                retryable_errors=[ServerError],
            ),
            ErrorCategory.CLIENT: RetryStrategy(
                max_attempts=0, retryable_errors=[]  # Don't retry client errors
            ),
            ErrorCategory.CONTENT: RetryStrategy(
                max_attempts=1, base_delay=0.0, retryable_errors=[ContentError]
            ),
            ErrorCategory.VALIDATION: RetryStrategy(
                max_attempts=0, retryable_errors=[]  # Don't retry validation errors
            ),
            ErrorCategory.STORAGE: RetryStrategy(
                max_attempts=3,
                base_delay=1.0,
                exponential_backoff=True,
                retryable_errors=[StorageError],
            ),
            ErrorCategory.CONFIGURATION: RetryStrategy(
                max_attempts=0, retryable_errors=[]  # Don't retry configuration errors
            ),
        }

    def get_circuit_breaker(self, endpoint: str) -> CircuitBreaker:
        """Get or create circuit breaker for endpoint"""
        if endpoint not in self.circuit_breakers:
            self.circuit_breakers[endpoint] = CircuitBreaker()
        return self.circuit_breakers[endpoint]

    def log_error(self, error: ScraperError) -> None:
        """Log error with context"""
        error_key = f"{error.category.value}_{error.severity.value}"
        self.error_stats[error_key] = self.error_stats.get(error_key, 0) + 1

        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }[error.severity]

        self.logger.log(
            log_level,
            f"{error.category.value.upper()} ERROR: {error.message}",
            extra={
                "error_type": type(error).__name__,
                "severity": error.severity.value,
                "category": error.category.value,
                "url": error.context.url,
                "status_code": error.context.status_code,
                "retry_count": error.context.retry_count,
                "scraper": error.context.scraper_name,
                "data_type": error.context.data_type,
                "timestamp": error.timestamp.isoformat(),
            },
        )

    async def handle_network_error(self, error: NetworkError) -> bool:
        """Handle network errors with retry logic"""
        self.log_error(error)

        strategy = self.retry_strategies[ErrorCategory.NETWORK]
        if strategy.max_attempts == 0:
            return False

        if error.context.retry_count < strategy.max_attempts:
            delay = self._calculate_delay(strategy, error.context.retry_count)
            self.logger.info(
                f"Retrying network request in {delay:.2f}s (attempt {error.context.retry_count + 1})"
            )
            await asyncio.sleep(delay)
            return True

        return False

    async def handle_rate_limit_error(self, error: RateLimitError) -> bool:
        """Handle rate limit errors with exponential backoff"""
        self.log_error(error)

        strategy = self.retry_strategies[ErrorCategory.RATE_LIMIT]
        if strategy.max_attempts == 0:
            return False

        if error.context.retry_count < strategy.max_attempts:
            # Use Retry-After header if available, otherwise exponential backoff
            if error.retry_after:
                delay = error.retry_after
            else:
                delay = self._calculate_delay(strategy, error.context.retry_count)

            self.logger.warning(
                f"Rate limited, waiting {delay:.2f}s (attempt {error.context.retry_count + 1})"
            )
            await asyncio.sleep(delay)
            return True

        return False

    async def handle_server_error(self, error: ServerError) -> bool:
        """Handle server errors with retry logic"""
        self.log_error(error)

        strategy = self.retry_strategies[ErrorCategory.SERVER]
        if strategy.max_attempts == 0:
            return False

        if error.context.retry_count < strategy.max_attempts:
            delay = self._calculate_delay(strategy, error.context.retry_count)
            self.logger.warning(
                f"Server error, retrying in {delay:.2f}s (attempt {error.context.retry_count + 1})"
            )
            await asyncio.sleep(delay)
            return True

        return False

    async def handle_client_error(self, error: ClientError) -> bool:
        """Handle client errors (no retry)"""
        self.log_error(error)
        return False  # Don't retry client errors

    async def handle_content_error(self, error: ContentError) -> bool:
        """Handle content parsing errors"""
        self.log_error(error)

        strategy = self.retry_strategies[ErrorCategory.CONTENT]
        if strategy.max_attempts == 0:
            return False

        if error.context.retry_count < strategy.max_attempts:
            # Content errors might benefit from different parsing strategy
            self.logger.info(
                f"Content parsing failed, retrying with different strategy (attempt {error.context.retry_count + 1})"
            )
            return True

        return False

    async def handle_validation_error(self, error: ValidationError) -> bool:
        """Handle validation errors (no retry)"""
        self.log_error(error)
        return False  # Don't retry validation errors

    async def handle_storage_error(self, error: StorageError) -> bool:
        """Handle storage errors with retry logic"""
        self.log_error(error)

        strategy = self.retry_strategies[ErrorCategory.STORAGE]
        if strategy.max_attempts == 0:
            return False

        if error.context.retry_count < strategy.max_attempts:
            delay = self._calculate_delay(strategy, error.context.retry_count)
            self.logger.warning(
                f"Storage error, retrying in {delay:.2f}s (attempt {error.context.retry_count + 1})"
            )
            await asyncio.sleep(delay)
            return True

        return False

    async def handle_configuration_error(self, error: ConfigurationError) -> bool:
        """Handle configuration errors (no retry)"""
        self.log_error(error)
        return False  # Don't retry configuration errors

    def _calculate_delay(self, strategy: RetryStrategy, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        if strategy.exponential_backoff:
            delay = strategy.base_delay * (2**attempt)
        else:
            delay = strategy.base_delay

        # Apply maximum delay limit
        delay = min(delay, strategy.max_delay)

        # Add jitter to prevent thundering herd
        if strategy.jitter:
            import random

            delay *= 0.5 + random.random() * 0.5  # 50-100% of calculated delay

        return delay

    async def handle_error(self, error: ScraperError) -> bool:
        """Generic error handler that routes to specific handlers"""
        handlers = {
            NetworkError: self.handle_network_error,
            RateLimitError: self.handle_rate_limit_error,
            ServerError: self.handle_server_error,
            ClientError: self.handle_client_error,
            ContentError: self.handle_content_error,
            ValidationError: self.handle_validation_error,
            StorageError: self.handle_storage_error,
            ConfigurationError: self.handle_configuration_error,
        }

        handler = handlers.get(type(error))
        if handler:
            return await handler(error)
        else:
            self.log_error(error)
            return False

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": self.error_stats.copy(),
            "circuit_breakers": {
                endpoint: {
                    "state": cb.state.state,
                    "failure_count": cb.state.failure_count,
                    "last_failure": cb.state.last_failure_time,
                }
                for endpoint, cb in self.circuit_breakers.items()
            },
            "total_errors": sum(self.error_stats.values()),
        }

    def reset_stats(self) -> None:
        """Reset error statistics"""
        self.error_stats.clear()
        self.circuit_breakers.clear()


# Decorator for automatic error handling
def handle_errors(error_handler: ScraperErrorHandler):
    """Decorator to automatically handle errors in async functions"""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ScraperError as e:
                should_retry = await error_handler.handle_error(e)
                if should_retry:
                    # Update retry count and retry
                    if e.context:
                        e.context.retry_count += 1
                    return await wrapper(*args, **kwargs)
                else:
                    raise

        return wrapper

    return decorator


# Example usage
if __name__ == "__main__":

    async def example_usage():
        handler = ScraperErrorHandler()

        # Simulate different error types
        errors = [
            NetworkError("Connection timeout", ErrorContext(url="https://example.com")),
            RateLimitError(
                "Too many requests",
                ErrorContext(url="https://api.example.com"),
                retry_after=60,
            ),
            ServerError(
                "Internal server error",
                ErrorContext(url="https://api.example.com", status_code=500),
            ),
            ClientError(
                "Bad request",
                ErrorContext(url="https://api.example.com", status_code=400),
            ),
            ValidationError(
                "Invalid data format", ErrorContext(data_type="player_stats")
            ),
        ]

        for error in errors:
            print(f"Handling {type(error).__name__}: {error.message}")
            should_retry = await handler.handle_error(error)
            print(f"Should retry: {should_retry}")
            print()

        print("Error stats:", handler.get_error_stats())

    asyncio.run(example_usage())

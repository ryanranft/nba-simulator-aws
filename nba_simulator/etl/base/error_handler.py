"""
Error Handler for ETL Scrapers

Provides comprehensive error handling, classification, and retry logic
for NBA data collection scrapers.

Migrated from: scripts/etl/scraper_error_handler.py
Enhanced with: Multi-schema support, better logging, retry strategies
"""

import asyncio
import traceback
from enum import Enum
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from nba_simulator.utils import logger


# Custom Exception Classes for Scrapers
class ScraperException(Exception):
    """Base exception for scraper errors"""

    pass


class NetworkError(ScraperException):
    """Network-related errors (connection, timeout)"""

    pass


class RateLimitError(ScraperException):
    """Rate limit exceeded (429 errors)"""

    pass


class ServerError(ScraperException):
    """Server errors (500-599 status codes)"""

    pass


class ClientError(ScraperException):
    """Client errors (400-499 status codes)"""

    pass


class ContentError(ScraperException):
    """Content parsing/validation errors"""

    pass


class CircuitBreaker:
    """
    Circuit breaker pattern for failing operations.

    Prevents cascading failures by temporarily disabling operations
    that are experiencing high failure rates.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: timedelta = timedelta(minutes=5),
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.is_open = False

    def record_success(self) -> None:
        """Record a successful operation"""
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None

    def record_failure(self) -> None:
        """Record a failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(
                f"Circuit breaker '{self.name}' opened after {self.failure_count} failures"
            )

    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if not self.is_open:
            return True

        # Check if timeout has passed
        if self.last_failure_time:
            time_since_failure = datetime.now() - self.last_failure_time
            if time_since_failure >= self.timeout:
                logger.info(
                    f"Circuit breaker '{self.name}' timeout expired, allowing retry"
                )
                self.is_open = False
                self.failure_count = 0
                return True

        return False

    def reset(self) -> None:
        """Manually reset the circuit breaker"""
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None
        logger.info(f"Circuit breaker '{self.name}' manually reset")


class ErrorSeverity(Enum):
    """Error severity levels for classification"""

    LOW = "low"  # Retry immediately
    MEDIUM = "medium"  # Retry with backoff
    HIGH = "high"  # Retry with long backoff
    CRITICAL = "critical"  # Don't retry, alert required


class ErrorCategory(Enum):
    """Error categories for targeted handling"""

    NETWORK = "network"  # Connection, timeout errors
    RATE_LIMIT = "rate_limit"  # 429, rate limiting
    AUTH = "auth"  # 401, 403 authentication
    NOT_FOUND = "not_found"  # 404 errors
    SERVER_ERROR = "server_error"  # 500-599 server errors
    DATA_VALIDATION = "data_validation"  # Invalid data format
    PARSE_ERROR = "parse_error"  # JSON/HTML parsing errors
    DATABASE = "database"  # Database connection/query errors
    UNKNOWN = "unknown"  # Unclassified errors


@dataclass
class ErrorContext:
    """Context information for an error"""

    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    stack_trace: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def should_retry(self) -> bool:
        """Determine if error should be retried"""
        if self.severity == ErrorSeverity.CRITICAL:
            return False
        return self.retry_count < self.max_retries

    @property
    def retry_delay(self) -> float:
        """Calculate retry delay based on severity and retry count"""
        base_delays = {
            ErrorSeverity.LOW: 1.0,
            ErrorSeverity.MEDIUM: 5.0,
            ErrorSeverity.HIGH: 30.0,
            ErrorSeverity.CRITICAL: 0.0,  # No retry
        }
        base_delay = base_delays[self.severity]

        # Exponential backoff: delay * (2 ^ retry_count)
        return base_delay * (2**self.retry_count)


class ScraperErrorHandler:
    """
    Comprehensive error handler for ETL scrapers.

    Features:
    - Error classification (network, rate limit, auth, etc.)
    - Severity assessment (low, medium, high, critical)
    - Automatic retry with exponential backoff
    - Error logging and tracking
    - Custom error handlers per category

    Example:
        handler = ScraperErrorHandler()

        try:
            result = await scraper.fetch_data()
        except Exception as e:
            context = handler.handle_error(e, metadata={"url": url})
            if context.should_retry:
                await asyncio.sleep(context.retry_delay)
                # Retry logic here
    """

    def __init__(
        self,
        max_retries: int = 3,
        custom_handlers: Optional[Dict[ErrorCategory, Callable]] = None,
    ):
        """
        Initialize error handler.

        Args:
            max_retries: Maximum retry attempts for retriable errors
            custom_handlers: Optional custom handlers per error category
        """
        self.max_retries = max_retries
        self.custom_handlers = custom_handlers or {}
        self.error_history: List[ErrorContext] = []

    def classify_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """
        Classify error by category and severity.

        Args:
            error: Exception to classify

        Returns:
            Tuple of (ErrorCategory, ErrorSeverity)
        """
        error_str = str(error).lower()
        error_type = type(error).__name__

        # Network errors
        if any(
            x in error_str for x in ["connection", "timeout", "network", "unreachable"]
        ):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM

        # Rate limiting
        if (
            "429" in error_str
            or "rate limit" in error_str
            or "too many requests" in error_str
        ):
            return ErrorCategory.RATE_LIMIT, ErrorSeverity.HIGH

        # Authentication
        if (
            "401" in error_str
            or "403" in error_str
            or "unauthorized" in error_str
            or "forbidden" in error_str
        ):
            return ErrorCategory.AUTH, ErrorSeverity.CRITICAL

        # Not found
        if "404" in error_str or "not found" in error_str:
            return ErrorCategory.NOT_FOUND, ErrorSeverity.LOW

        # Server errors
        if any(f"{code}" in error_str for code in range(500, 600)):
            return ErrorCategory.SERVER_ERROR, ErrorSeverity.HIGH

        # Data validation
        if (
            "validation" in error_str
            or "invalid data" in error_str
            or "schema" in error_str
        ):
            return ErrorCategory.DATA_VALIDATION, ErrorSeverity.MEDIUM

        # Parse errors
        if any(x in error_type.lower() for x in ["json", "parse", "decode"]):
            return ErrorCategory.PARSE_ERROR, ErrorSeverity.MEDIUM

        # Database errors
        if any(
            x in error_str for x in ["database", "postgresql", "connection pool", "sql"]
        ):
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH

        # Unknown errors default to medium severity
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

    def handle_error(
        self,
        error: Exception,
        metadata: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> ErrorContext:
        """
        Handle an error and create error context.

        Args:
            error: Exception that occurred
            metadata: Additional context (URL, game_id, etc.)
            retry_count: Current retry attempt number

        Returns:
            ErrorContext with classification and retry information
        """
        category, severity = self.classify_error(error)

        context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            category=category,
            severity=severity,
            stack_trace=traceback.format_exc(),
            retry_count=retry_count,
            max_retries=self.max_retries,
            metadata=metadata or {},
        )

        # Log the error
        self._log_error(context)

        # Track in history
        self.error_history.append(context)

        # Run custom handler if available
        if category in self.custom_handlers:
            self.custom_handlers[category](context)

        return context

    def _log_error(self, context: ErrorContext) -> None:
        """
        Log error with appropriate level based on severity.

        Args:
            context: Error context to log
        """
        log_msg = (
            f"[{context.category.value.upper()}] "
            f"{context.error_type}: {context.error_message}"
        )

        if context.metadata:
            log_msg += f" | Metadata: {context.metadata}"

        if context.should_retry:
            log_msg += f" | Retry {context.retry_count + 1}/{context.max_retries} in {context.retry_delay:.1f}s"

        # Log based on severity
        if context.severity == ErrorSeverity.CRITICAL:
            logger.error(log_msg)
            if context.stack_trace:
                logger.error(f"Stack trace:\n{context.stack_trace}")
        elif context.severity == ErrorSeverity.HIGH:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

    async def retry_with_backoff(
        self,
        func: Callable,
        *args,
        max_retries: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """
        Execute function with automatic retry and exponential backoff.

        Args:
            func: Async function to execute
            *args: Positional arguments for function
            max_retries: Override default max retries
            metadata: Context metadata for error tracking
            **kwargs: Keyword arguments for function

        Returns:
            Result from successful function execution

        Raises:
            Last exception if all retries exhausted
        """
        max_attempts = max_retries or self.max_retries
        last_error = None

        for attempt in range(max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                context = self.handle_error(e, metadata=metadata, retry_count=attempt)

                if not context.should_retry or attempt >= max_attempts:
                    logger.error(f"All retries exhausted. Raising error.")
                    raise

                # Wait before retry
                await asyncio.sleep(context.retry_delay)
                logger.info(f"Retrying after {context.retry_delay:.1f}s delay...")

        # Should never reach here, but just in case
        raise last_error

    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of errors encountered.

        Returns:
            Dictionary with error statistics
        """
        if not self.error_history:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "retry_rate": 0.0,
            }

        by_category = {}
        by_severity = {}
        total_retries = 0

        for context in self.error_history:
            # Count by category
            cat = context.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            # Count by severity
            sev = context.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

            # Track retries
            total_retries += context.retry_count

        return {
            "total_errors": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "total_retries": total_retries,
            "retry_rate": (
                total_retries / len(self.error_history) if self.error_history else 0.0
            ),
        }

    def clear_history(self) -> None:
        """Clear error history."""
        self.error_history.clear()


# Convenience functions for common use cases


def create_error_handler(
    max_retries: int = 3,
    rate_limit_handler: Optional[Callable] = None,
    auth_handler: Optional[Callable] = None,
) -> ScraperErrorHandler:
    """
    Create error handler with common custom handlers.

    Args:
        max_retries: Maximum retry attempts
        rate_limit_handler: Custom handler for rate limit errors
        auth_handler: Custom handler for authentication errors

    Returns:
        Configured ScraperErrorHandler instance
    """
    custom_handlers = {}

    if rate_limit_handler:
        custom_handlers[ErrorCategory.RATE_LIMIT] = rate_limit_handler

    if auth_handler:
        custom_handlers[ErrorCategory.AUTH] = auth_handler

    return ScraperErrorHandler(max_retries=max_retries, custom_handlers=custom_handlers)


async def safe_execute(
    func: Callable,
    *args,
    max_retries: int = 3,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Optional[Any]:
    """
    Safely execute a function with error handling and retry.

    Args:
        func: Async function to execute
        *args: Positional arguments
        max_retries: Maximum retry attempts
        metadata: Context metadata
        **kwargs: Keyword arguments

    Returns:
        Result from function or None if all retries failed
    """
    handler = ScraperErrorHandler(max_retries=max_retries)
    try:
        return await handler.retry_with_backoff(
            func, *args, metadata=metadata, **kwargs
        )
    except Exception as e:
        logger.error(f"safe_execute failed after all retries: {e}")
        return None

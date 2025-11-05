"""
Tests for ScraperErrorHandler

Tests error classification, retry logic, and error handling workflow.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from nba_simulator.etl.base import (
    ScraperErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    create_error_handler,
    safe_execute,
)


class TestErrorClassification:
    """Test error classification logic"""

    def setup_method(self):
        """Setup test fixtures"""
        self.handler = ScraperErrorHandler()

    def test_network_error_classification(self):
        """Test network errors are classified correctly"""
        error = ConnectionError("Connection timeout")
        category, severity = self.handler.classify_error(error)

        assert category == ErrorCategory.NETWORK
        assert severity == ErrorSeverity.MEDIUM

    def test_rate_limit_classification(self):
        """Test rate limit errors"""
        error = Exception("429 Too Many Requests")
        category, severity = self.handler.classify_error(error)

        assert category == ErrorCategory.RATE_LIMIT
        assert severity == ErrorSeverity.HIGH

    def test_auth_error_classification(self):
        """Test authentication errors"""
        error = Exception("401 Unauthorized")
        category, severity = self.handler.classify_error(error)

        assert category == ErrorCategory.AUTH
        assert severity == ErrorSeverity.CRITICAL

    def test_not_found_classification(self):
        """Test 404 errors"""
        error = Exception("404 Not Found")
        category, severity = self.handler.classify_error(error)

        assert category == ErrorCategory.NOT_FOUND
        assert severity == ErrorSeverity.LOW

    def test_server_error_classification(self):
        """Test server errors"""
        error = Exception("500 Internal Server Error")
        category, severity = self.handler.classify_error(error)

        assert category == ErrorCategory.SERVER_ERROR
        assert severity == ErrorSeverity.HIGH

    def test_parse_error_classification(self):
        """Test JSON parse errors"""
        error = ValueError("Invalid JSON")
        category, severity = self.handler.classify_error(error)

        assert category == ErrorCategory.PARSE_ERROR
        assert severity == ErrorSeverity.MEDIUM

    def test_database_error_classification(self):
        """Test database errors"""
        error = Exception("PostgreSQL connection failed")
        category, severity = self.handler.classify_error(error)

        assert category == ErrorCategory.DATABASE
        assert severity == ErrorSeverity.HIGH

    def test_unknown_error_classification(self):
        """Test unknown errors default to medium severity"""
        error = Exception("Something went wrong")
        category, severity = self.handler.classify_error(error)

        assert category == ErrorCategory.UNKNOWN
        assert severity == ErrorSeverity.MEDIUM


class TestErrorContext:
    """Test ErrorContext functionality"""

    def test_should_retry_logic(self):
        """Test retry decision logic"""
        # Should retry on low severity
        context = ErrorContext(
            error_type="NetworkError",
            error_message="Timeout",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.LOW,
            retry_count=0,
            max_retries=3,
        )
        assert context.should_retry is True

        # Should not retry on critical
        context_critical = ErrorContext(
            error_type="AuthError",
            error_message="Unauthorized",
            category=ErrorCategory.AUTH,
            severity=ErrorSeverity.CRITICAL,
            retry_count=0,
            max_retries=3,
        )
        assert context_critical.should_retry is False

        # Should not retry when max retries reached
        context_exhausted = ErrorContext(
            error_type="NetworkError",
            error_message="Timeout",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            retry_count=3,
            max_retries=3,
        )
        assert context_exhausted.should_retry is False

    def test_retry_delay_calculation(self):
        """Test exponential backoff calculation"""
        context = ErrorContext(
            error_type="NetworkError",
            error_message="Timeout",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            retry_count=0,
            max_retries=3,
        )

        # First retry: base delay * 2^0 = 5.0
        assert context.retry_delay == 5.0

        # Second retry
        context.retry_count = 1
        assert context.retry_delay == 10.0  # 5.0 * 2^1

        # Third retry
        context.retry_count = 2
        assert context.retry_delay == 20.0  # 5.0 * 2^2


class TestErrorHandler:
    """Test ScraperErrorHandler functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.handler = ScraperErrorHandler(max_retries=3)

    def test_handle_error_creates_context(self):
        """Test error handling creates proper context"""
        error = ConnectionError("Network timeout")
        metadata = {"url": "https://api.example.com", "game_id": "12345"}

        context = self.handler.handle_error(error, metadata=metadata, retry_count=0)

        assert isinstance(context, ErrorContext)
        assert context.error_type == "ConnectionError"
        assert context.error_message == "Network timeout"
        assert context.category == ErrorCategory.NETWORK
        assert context.severity == ErrorSeverity.MEDIUM
        assert context.metadata == metadata
        assert context.retry_count == 0

    def test_error_history_tracking(self):
        """Test errors are tracked in history"""
        assert len(self.handler.error_history) == 0

        error1 = ConnectionError("Timeout 1")
        self.handler.handle_error(error1)

        assert len(self.handler.error_history) == 1

        error2 = Exception("404 Not Found")
        self.handler.handle_error(error2)

        assert len(self.handler.error_history) == 2

    def test_custom_handlers_called(self):
        """Test custom error handlers are invoked"""
        mock_handler = Mock()
        handler = ScraperErrorHandler(
            custom_handlers={ErrorCategory.RATE_LIMIT: mock_handler}
        )

        error = Exception("429 Rate Limit")
        handler.handle_error(error)

        # Custom handler should be called once
        assert mock_handler.call_count == 1

        # Verify it received an ErrorContext
        call_args = mock_handler.call_args[0]
        assert isinstance(call_args[0], ErrorContext)

    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self):
        """Test successful retry after failures"""
        call_count = 0

        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = await self.handler.retry_with_backoff(
            flaky_function, metadata={"test": "retry"}
        )

        assert result == "success"
        assert call_count == 3
        assert len(self.handler.error_history) == 2  # 2 failures before success

    @pytest.mark.asyncio
    async def test_retry_with_backoff_exhausted(self):
        """Test retry exhaustion"""

        async def always_fails():
            raise ConnectionError("Persistent failure")

        with pytest.raises(ConnectionError):
            await self.handler.retry_with_backoff(always_fails, max_retries=2)

        # Should have 3 attempts (initial + 2 retries)
        assert len(self.handler.error_history) == 3

    @pytest.mark.asyncio
    async def test_retry_with_backoff_critical_no_retry(self):
        """Test critical errors are not retried"""

        async def auth_failure():
            raise Exception("401 Unauthorized")

        with pytest.raises(Exception):
            await self.handler.retry_with_backoff(auth_failure)

        # Should only attempt once (no retries for critical)
        assert len(self.handler.error_history) == 1

    def test_error_summary(self):
        """Test error summary generation"""
        # Add various errors
        self.handler.handle_error(ConnectionError("Timeout"), retry_count=1)
        self.handler.handle_error(Exception("404 Not Found"), retry_count=0)
        self.handler.handle_error(Exception("500 Server Error"), retry_count=2)

        summary = self.handler.get_error_summary()

        assert summary["total_errors"] == 3
        assert summary["total_retries"] == 3  # 1 + 0 + 2
        assert summary["retry_rate"] == 1.0  # 3 / 3

        # Check categories
        assert ErrorCategory.NETWORK.value in summary["by_category"]
        assert ErrorCategory.NOT_FOUND.value in summary["by_category"]
        assert ErrorCategory.SERVER_ERROR.value in summary["by_category"]

    def test_clear_history(self):
        """Test clearing error history"""
        self.handler.handle_error(Exception("Test error"))
        assert len(self.handler.error_history) > 0

        self.handler.clear_history()
        assert len(self.handler.error_history) == 0


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_create_error_handler(self):
        """Test error handler factory"""
        handler = create_error_handler(max_retries=5, rate_limit_handler=Mock())

        assert isinstance(handler, ScraperErrorHandler)
        assert handler.max_retries == 5
        assert ErrorCategory.RATE_LIMIT in handler.custom_handlers

    @pytest.mark.asyncio
    async def test_safe_execute_success(self):
        """Test safe_execute with successful function"""

        async def successful_func():
            return "success"

        result = await safe_execute(successful_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_safe_execute_failure(self):
        """Test safe_execute returns None on failure"""

        async def failing_func():
            raise Exception("Persistent failure")

        result = await safe_execute(failing_func, max_retries=1)
        assert result is None


class TestIntegration:
    """Integration tests for error handling workflow"""

    @pytest.mark.asyncio
    async def test_complete_error_handling_workflow(self):
        """Test complete error handling workflow"""
        handler = ScraperErrorHandler(max_retries=3)

        call_count = 0

        async def scraper_function(url: str):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                raise ConnectionError("Network timeout")
            elif call_count == 2:
                raise Exception("429 Rate Limit")
            else:
                return {"data": "success"}

        result = await handler.retry_with_backoff(
            scraper_function, "https://api.nba.com", metadata={"source": "nba_api"}
        )

        # Should succeed on third attempt
        assert result == {"data": "success"}
        assert call_count == 3

        # Check error history
        assert len(handler.error_history) == 2

        # Get summary
        summary = handler.get_error_summary()
        assert summary["total_errors"] == 2
        assert summary["total_retries"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

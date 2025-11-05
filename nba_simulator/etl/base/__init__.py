"""
ETL Base Module

Provides base classes and utilities for all NBA data scrapers:
- AsyncBaseScraper: Base class for async scrapers
- ScraperConfig: Configuration dataclass
- ScraperStats: Statistics tracking
- RateLimiter: Token bucket rate limiter
- ScraperFactory: Factory for creating scrapers
- ScraperErrorHandler: Comprehensive error handling with retry logic
- Error classification and severity levels

Version: 2.0 (Refactored)
Created: November 1, 2025
Updated: Day 1 - Added error handling
"""

from .async_scraper import (
    AsyncScraper as AsyncBaseScraper,  # Alias for backward compatibility
    ScraperConfig,
    ScraperStats,
    RateLimiter,
    ScraperFactory,
)

from .error_handler import (
    ScraperErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    create_error_handler,
    safe_execute,
)

__all__ = [
    # Async scraper components
    "AsyncBaseScraper",
    "ScraperConfig",
    "ScraperStats",
    "RateLimiter",
    "ScraperFactory",
    # Error handling
    "ScraperErrorHandler",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorContext",
    "create_error_handler",
    "safe_execute",
]

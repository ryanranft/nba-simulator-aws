"""
ETL Base Module

Provides base classes and utilities for all NBA data scrapers:
- AsyncBaseScraper: Base class for async scrapers
- ScraperConfig: Configuration dataclass
- ScraperStats: Statistics tracking
- RateLimiter: Token bucket rate limiter
- ScraperFactory: Factory for creating scrapers

Version: 2.0 (Refactored)
Created: November 1, 2025
"""

from .async_scraper import (
    AsyncBaseScraper,
    ScraperConfig,
    ScraperStats,
    RateLimiter,
    ScraperFactory,
)

__all__ = [
    "AsyncBaseScraper",
    "ScraperConfig",
    "ScraperStats",
    "RateLimiter",
    "ScraperFactory",
]

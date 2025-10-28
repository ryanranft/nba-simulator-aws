"""
Base Classes for ETL Operations

Provides abstract base classes for scrapers, extractors, and loaders.
Includes retry logic, rate limiting, error handling, and logging.
"""

from .scraper import BaseScraper
from .extractor import BaseExtractor
from .loader import BaseLoader

__all__ = ["BaseScraper", "BaseExtractor", "BaseLoader"]


"""
ETL Module - Extract, Transform, Load

Consolidates 75+ scrapers into organized structure.
Provides base classes and source-specific extractors.

Phase 2 of refactoring (Weeks 3-5).
"""

__version__ = "2.0.0-alpha"

from .base import BaseScraper, BaseExtractor, BaseLoader

__all__ = ["BaseScraper", "BaseExtractor", "BaseLoader"]

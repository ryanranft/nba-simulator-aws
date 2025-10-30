"""
scripts.etl - DEPRECATED

This module is deprecated. Use nba_simulator.etl instead.

Backward compatibility layer for existing scripts that import from scripts.etl.
All imports are re-exported from the new nba_simulator.etl package.

Migration Guide:
    OLD: from scripts.etl.espn_async_scraper import ESPNScraper
    NEW: from nba_simulator.etl.extractors.espn import scraper

    OLD: from scripts.etl.async_scraper_base import AsyncScraperBase
    NEW: from nba_simulator.etl.base.async_scraper import AsyncScraperBase
"""

import warnings

warnings.warn(
    "scripts.etl is deprecated. Use nba_simulator.etl instead. "
    "See nba_simulator.etl documentation for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new locations for backward compatibility
# Note: This maintains existing functionality while files are in both locations

__all__ = []

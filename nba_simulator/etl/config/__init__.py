"""
Configuration management for NBA data scrapers

Provides centralized YAML-based configuration with:
- Multi-scraper support
- Environment variable overrides
- Configuration validation
- Runtime updates

Usage:
    from nba_simulator.etl.config import ScraperConfigManager, get_scraper_config

    # Load all configurations
    manager = ScraperConfigManager("config/scraper_config.yaml")
    espn_config = manager.get_scraper_config("espn")

    # Load single scraper config
    config = get_scraper_config("espn")

Version: 2.0
"""

from .manager import (
    ScraperConfigManager,
    ScraperConfig,
    RateLimitConfig,
    RetryConfig,
    StorageConfig,
    MonitoringConfig,
    load_config,
    get_scraper_config,
    create_config_from_env,
)

__all__ = [
    "ScraperConfigManager",
    "ScraperConfig",
    "RateLimitConfig",
    "RetryConfig",
    "StorageConfig",
    "MonitoringConfig",
    "load_config",
    "get_scraper_config",
    "create_config_from_env",
]

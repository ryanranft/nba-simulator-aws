"""
Data Extractors Module

Provides scrapers for all NBA data sources with integrated error handling
and validation.

Available Extractors:
- ESPN: JSON API-based scraper for real-time data ✅
- Basketball Reference: HTML-based scraper for historical data ✅
- NBA API: Official NBA.com statistics API ✅
- hoopR: Python wrapper for hoopR R package ✅
- Kaggle: Historical datasets (future)

Usage:
    from nba_simulator.etl.extractors.espn import ESPNScraper
    from nba_simulator.etl.extractors.basketball_reference import BasketballReferenceScraper
    from nba_simulator.etl.extractors.nba_api import NBAAPIScraper
    from nba_simulator.etl.extractors.hoopr import HoopRScraper

    # ESPN scraping (fast, real-time)
    async with ESPNScraper(config) as scraper:
        games = await scraper.scrape_schedule(season=2024)

    # Basketball Reference scraping (historical)
    async with BasketballReferenceScraper(config) as scraper:
        games = await scraper.scrape_season_schedule(season=2024)

    # NBA API scraping (official stats)
    async with NBAAPIScraper(config) as scraper:
        players = await scraper.scrape_player_stats(season="2024-25")

    # hoopR scraping (requires R)
    async with HoopRScraper(config) as scraper:
        if scraper.r_available:
            schedule = await scraper.scrape_team_schedule("LAL", 2024)

Day 3 Implementation: NBA API and hoopR scrapers complete!
All major data sources now available!
"""

from . import espn
from . import basketball_reference
from . import nba_api
from . import hoopr

# Import scraper classes for convenience
from .espn import ESPNScraper, scrape_espn_games
from .basketball_reference import (
    BasketballReferenceScraper,
    scrape_basketball_reference_season,
)
from .nba_api import NBAAPIScraper, scrape_nba_api_season
from .hoopr import HoopRScraper, scrape_hoopr_season

__all__ = [
    # Modules
    "espn",
    "basketball_reference",
    "nba_api",
    "hoopr",
    # Scraper classes
    "ESPNScraper",
    "BasketballReferenceScraper",
    "NBAAPIScraper",
    "HoopRScraper",
    # Convenience functions
    "scrape_espn_games",
    "scrape_basketball_reference_season",
    "scrape_nba_api_season",
    "scrape_hoopr_season",
]

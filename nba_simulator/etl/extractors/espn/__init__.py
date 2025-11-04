"""
ESPN Extractor Module

Provides comprehensive data extraction from ESPN's NBA APIs.

Components:
- ESPNScraper: Main scraper class for ESPN data
- scrape_espn_games: Convenience function for quick scraping

Usage:
    from nba_simulator.etl.extractors.espn import ESPNScraper
    
    async with ESPNScraper(config) as scraper:
        games = await scraper.scrape_schedule(season=2024)
"""

from .scraper import ESPNScraper, scrape_espn_games

__all__ = ['ESPNScraper', 'scrape_espn_games']

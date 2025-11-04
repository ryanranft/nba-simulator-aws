"""
NBA API Extractor Module

Provides data extraction from NBA.com's official statistics API.

Components:
- NBAAPIScraper: Main scraper class for NBA API
- scrape_nba_api_season: Convenience function

Note: Requires specific headers to avoid being blocked by NBA.com.

Usage:
    from nba_simulator.etl.extractors.nba_api import NBAAPIScraper
    
    config = ScraperConfig(
        base_url="https://stats.nba.com/stats",
        rate_limit=0.6  # ~100 requests per minute
    )
    
    async with NBAAPIScraper(config) as scraper:
        players = await scraper.scrape_player_stats(season="2024-25")
"""

from .scraper import NBAAPIScraper, scrape_nba_api_season

__all__ = ['NBAAPIScraper', 'scrape_nba_api_season']

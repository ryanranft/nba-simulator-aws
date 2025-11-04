"""
Basketball Reference Extractor Module

Provides HTML-based data extraction from Basketball-Reference.com.

Components:
- BasketballReferenceScraper: Main scraper class for Basketball Reference
- scrape_basketball_reference_season: Convenience function

Note: Requires BeautifulSoup4 for HTML parsing.

Usage:
    from nba_simulator.etl.extractors.basketball_reference import BasketballReferenceScraper
    
    config = ScraperConfig(
        base_url="https://www.basketball-reference.com",
        rate_limit=3.0  # Be respectful!
    )
    
    async with BasketballReferenceScraper(config) as scraper:
        games = await scraper.scrape_season_schedule(season=2024)
"""

from .scraper import BasketballReferenceScraper, scrape_basketball_reference_season

__all__ = ['BasketballReferenceScraper', 'scrape_basketball_reference_season']

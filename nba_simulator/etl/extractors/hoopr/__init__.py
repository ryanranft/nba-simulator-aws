"""
hoopR Extractor Module

Python wrapper for the hoopR R package.

Components:
- HoopRScraper: Main scraper class wrapping hoopR R package
- scrape_hoopr_season: Convenience function

Requirements:
- R installation (https://www.r-project.org/)
- hoopR R package: install.packages("hoopR")
- Optional: rpy2 for direct R integration: pip install rpy2

Usage:
    from nba_simulator.etl.extractors.hoopr import HoopRScraper
    
    config = ScraperConfig(
        base_url="",  # Not used
        rate_limit=1.0
    )
    
    async with HoopRScraper(config) as scraper:
        # Check if R is available
        if scraper.r_available:
            schedule = await scraper.scrape_team_schedule("LAL", 2024)

Note: Requires R and hoopR package installation.
"""

from .scraper import HoopRScraper, scrape_hoopr_season

__all__ = ['HoopRScraper', 'scrape_hoopr_season']

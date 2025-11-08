"""
ESPN Extractor Module

Provides comprehensive data extraction from ESPN's NBA APIs.

Components:
- ESPNScraper: Main scraper class for ESPN data
- ESPNFeatureExtractor: Complete 58-feature extraction from S3 JSON files
- ESPNJSONReader: S3 JSON reader with caching
- scrape_espn_games: Convenience function for quick scraping
- extract_espn_features: Convenience function for feature extraction

Usage:
    # Scraping from ESPN website
    from nba_simulator.etl.extractors.espn import ESPNScraper

    async with ESPNScraper(config) as scraper:
        games = await scraper.scrape_schedule(season=2024)

    # Feature extraction from S3
    from nba_simulator.etl.extractors.espn import ESPNFeatureExtractor

    extractor = ESPNFeatureExtractor()
    features = extractor.extract_game_features(game_id="401468003")
"""

from .scraper import ESPNScraper, scrape_espn_games
from .feature_extractor import (
    ESPNFeatureExtractor,
    ESPNJSONReader,
    extract_espn_features,
)

__all__ = [
    "ESPNScraper",
    "scrape_espn_games",
    "ESPNFeatureExtractor",
    "ESPNJSONReader",
    "extract_espn_features",
]

#!/usr/bin/env python3
"""
Basketball Reference Async Scraper - Modern Architecture

Upgraded Basketball Reference scraper with async architecture:
- AsyncBaseScraper base class
- Intelligent content extraction
- Modular tool components
- Centralized error handling
- Telemetry and monitoring
- Configuration management

Based on new async infrastructure and modular tools.

Usage:
    python scripts/etl/basketball_reference_async_scraper.py
    python scripts/etl/basketball_reference_async_scraper.py --season 2024-25
    python scripts/etl/basketball_reference_async_scraper.py --data-types player_stats team_stats
    python scripts/etl/basketball_reference_async_scraper.py --dry-run

Version: 2.0 (Async Migration)
Created: October 13, 2025
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import our new async infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper, ScraperConfig
from scripts.etl.scraper_error_handler import ScraperErrorHandler
from scripts.etl.scraper_telemetry import ScraperTelemetry
from scripts.etl.scraper_config import ScraperConfigManager, get_scraper_config
from scripts.etl.intelligent_extraction import BasketballReferenceExtractionStrategy
from scripts.etl.modular_tools import ToolComposer


class BasketballReferenceAsyncScraper(AsyncBaseScraper):
    """Async Basketball Reference NBA data scraper"""

    def __init__(
        self, config: ScraperConfig, season: str = None, data_types: List[str] = None
    ):
        super().__init__(config)
        self.season = season or self._get_current_season()
        self.data_types = data_types or ["player_stats", "team_stats", "schedule"]
        self.error_handler = ScraperErrorHandler()
        self.telemetry = ScraperTelemetry("basketball_reference_scraper")

        # Basketball Reference-specific settings
        self.base_url = "https://www.basketball-reference.com"
        self.rate_limit_seconds = (
            12  # Basketball Reference requires 12 seconds between requests
        )

        # Data type configurations
        self.data_type_configs = {
            "player_stats": {
                "url_template": "/leagues/NBA_{year}_per_game.html",
                "extraction_strategy": "basketball_reference",
                "filename_template": "player_stats_{season}.json",
            },
            "team_stats": {
                "url_template": "/leagues/NBA_{year}.html",
                "extraction_strategy": "basketball_reference",
                "filename_template": "team_stats_{season}.json",
            },
            "schedule": {
                "url_template": "/leagues/NBA_{year}_games.html",
                "extraction_strategy": "basketball_reference",
                "filename_template": "schedule_{season}.json",
            },
            "advanced_stats": {
                "url_template": "/leagues/NBA_{year}_advanced.html",
                "extraction_strategy": "basketball_reference",
                "filename_template": "advanced_stats_{season}.json",
            },
            "play_by_play": {
                "url_template": "/leagues/NBA_{year}_play-by-play.html",
                "extraction_strategy": "basketball_reference",
                "filename_template": "play_by_play_{season}.json",
            },
        }

        # Create subdirectories
        for data_type in self.data_types:
            (self.output_dir / data_type).mkdir(parents=True, exist_ok=True)

    def _get_current_season(self) -> str:
        """Get current NBA season"""
        now = datetime.now()
        if now.month >= 10:  # October or later
            return f"{now.year}-{str(now.year + 1)[2:]}"
        else:  # Before October
            return f"{now.year - 1}-{str(now.year)[2:]}"

    def _get_season_year(self, season: str) -> str:
        """Convert season string to year for URL"""
        # Convert "2024-25" to "2025"
        return season.split("-")[1]

    async def scrape(self) -> None:
        """Main scraping method"""
        async with self.telemetry.track_operation("basketball_reference_scrape"):
            self.logger.info(
                f"Starting Basketball Reference async scraper for season {self.season}"
            )
            self.logger.info(f"Data types: {', '.join(self.data_types)}")

            # Process each data type
            for data_type in self.data_types:
                await self._scrape_data_type(data_type)

            self.logger.info("Basketball Reference async scraper completed")

    async def _scrape_data_type(self, data_type: str) -> None:
        """Scrape a specific data type"""
        if data_type not in self.data_type_configs:
            self.logger.error(f"Unknown data type: {data_type}")
            return

        try:
            async with self.telemetry.track_operation(f"scrape_{data_type}"):
                config = self.data_type_configs[data_type]

                # Build URL
                year = self._get_season_year(self.season)
                url = f"{self.base_url}{config['url_template'].format(year=year)}"

                self.logger.info(f"Scraping {data_type} from {url}")

                # Fetch and parse data
                response = await self.fetch_url(url)
                if not response:
                    self.logger.error(f"Failed to fetch {data_type}")
                    return

                # Parse HTML content
                content = await response.text()

                # Use intelligent extraction
                extraction_strategy = BasketballReferenceExtractionStrategy()
                result = await extraction_strategy.extract(content, "html")

                if result.success:
                    # Store data
                    filename = config["filename_template"].format(season=self.season)
                    success = await self.store_data(result.data, filename, data_type)

                    if success:
                        self.logger.info(f"Successfully scraped and stored {data_type}")
                        self.telemetry.metrics.record_data_item(data_type)
                    else:
                        self.logger.error(f"Failed to store {data_type}")
                else:
                    self.logger.error(f"Failed to extract {data_type}: {result.errors}")

        except Exception as e:
            self.logger.error(f"Error scraping {data_type}: {e}")
            await self.error_handler.handle_error(
                ContentError(f"Data type scraping failed: {e}")
            )

    async def scrape_player_stats(self, season: str = None) -> None:
        """Scrape player statistics for a specific season"""
        season = season or self.season

        try:
            async with self.telemetry.track_operation("scrape_player_stats"):
                year = self._get_season_year(season)
                url = f"{self.base_url}/leagues/NBA_{year}_per_game.html"

                self.logger.info(f"Scraping player stats for {season}")

                response = await self.fetch_url(url)
                if response:
                    content = await response.text()

                    # Extract player stats
                    extraction_strategy = BasketballReferenceExtractionStrategy()
                    result = await extraction_strategy.extract(content, "html")

                    if result.success:
                        filename = f"player_stats_{season}.json"
                        await self.store_data(result.data, filename, "player_stats")
                        self.logger.info(f"Player stats scraped for {season}")
                    else:
                        self.logger.error(
                            f"Failed to extract player stats: {result.errors}"
                        )

        except Exception as e:
            self.logger.error(f"Error scraping player stats: {e}")

    async def scrape_team_stats(self, season: str = None) -> None:
        """Scrape team statistics for a specific season"""
        season = season or self.season

        try:
            async with self.telemetry.track_operation("scrape_team_stats"):
                year = self._get_season_year(season)
                url = f"{self.base_url}/leagues/NBA_{year}.html"

                self.logger.info(f"Scraping team stats for {season}")

                response = await self.fetch_url(url)
                if response:
                    content = await response.text()

                    # Extract team stats
                    extraction_strategy = BasketballReferenceExtractionStrategy()
                    result = await extraction_strategy.extract(content, "html")

                    if result.success:
                        filename = f"team_stats_{season}.json"
                        await self.store_data(result.data, filename, "team_stats")
                        self.logger.info(f"Team stats scraped for {season}")
                    else:
                        self.logger.error(
                            f"Failed to extract team stats: {result.errors}"
                        )

        except Exception as e:
            self.logger.error(f"Error scraping team stats: {e}")

    async def scrape_schedule(self, season: str = None) -> None:
        """Scrape schedule for a specific season"""
        season = season or self.season

        try:
            async with self.telemetry.track_operation("scrape_schedule"):
                year = self._get_season_year(season)
                url = f"{self.base_url}/leagues/NBA_{year}_games.html"

                self.logger.info(f"Scraping schedule for {season}")

                response = await self.fetch_url(url)
                if response:
                    content = await response.text()

                    # Extract schedule
                    extraction_strategy = BasketballReferenceExtractionStrategy()
                    result = await extraction_strategy.extract(content, "html")

                    if result.success:
                        filename = f"schedule_{season}.json"
                        await self.store_data(result.data, filename, "schedule")
                        self.logger.info(f"Schedule scraped for {season}")
                    else:
                        self.logger.error(
                            f"Failed to extract schedule: {result.errors}"
                        )

        except Exception as e:
            self.logger.error(f"Error scraping schedule: {e}")

    async def scrape_multiple_seasons(self, seasons: List[str]) -> None:
        """Scrape multiple seasons"""
        async with self.telemetry.track_operation("scrape_multiple_seasons"):
            self.logger.info(f"Scraping multiple seasons: {seasons}")

            for season in seasons:
                self.season = season
                await self.scrape()

                # Rate limiting between seasons
                await asyncio.sleep(self.rate_limit_seconds)

    async def scrape_historical_range(self, start_season: str, end_season: str) -> None:
        """Scrape historical range of seasons"""
        async with self.telemetry.track_operation("scrape_historical_range"):
            self.logger.info(
                f"Scraping historical range: {start_season} to {end_season}"
            )

            # Generate season list
            seasons = self._generate_season_list(start_season, end_season)

            # Scrape each season
            for season in seasons:
                self.logger.info(f"Scraping season {season}")
                self.season = season
                await self.scrape()

                # Rate limiting between seasons
                await asyncio.sleep(self.rate_limit_seconds)

    def _generate_season_list(self, start_season: str, end_season: str) -> List[str]:
        """Generate list of seasons between start and end"""
        seasons = []

        start_year = int(start_season.split("-")[0])
        end_year = int(end_season.split("-")[0])

        for year in range(start_year, end_year + 1):
            season = f"{year}-{str(year + 1)[2:]}"
            seasons.append(season)

        return seasons


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Basketball Reference Async Scraper")
    parser.add_argument(
        "--season", type=str, help="NBA season to scrape (e.g., 2024-25)"
    )
    parser.add_argument(
        "--data-types",
        nargs="+",
        choices=[
            "player_stats",
            "team_stats",
            "schedule",
            "advanced_stats",
            "play_by_play",
        ],
        help="Data types to scrape",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run mode (no actual scraping)"
    )
    parser.add_argument(
        "--config-file",
        type=str,
        default="config/scraper_config.yaml",
        help="Configuration file path",
    )
    parser.add_argument(
        "--start-season", type=str, help="Start season for historical range"
    )
    parser.add_argument(
        "--end-season", type=str, help="End season for historical range"
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_manager = ScraperConfigManager(args.config_file)
        config = config_manager.get_scraper_config("basketball_reference")
        if not config:
            print("❌ Basketball Reference configuration not found")
            return

        # Override config with command line args
        if args.dry_run:
            config.dry_run = True

        print(f"✅ Loaded Basketball Reference configuration")
        print(f"   Base URL: {config.base_url}")
        print(f"   Rate limit: {config.rate_limit.requests_per_second} req/s")
        print(f"   Max concurrent: {config.max_concurrent}")
        print(f"   Dry run: {config.dry_run}")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return

    # Create scraper
    scraper = BasketballReferenceAsyncScraper(
        config, season=args.season, data_types=args.data_types
    )

    try:
        # Run scraper
        async with scraper:
            if args.start_season and args.end_season:
                await scraper.scrape_historical_range(
                    args.start_season, args.end_season
                )
            else:
                await scraper.scrape()

        # Print final statistics
        print("\n📊 Final Statistics:")
        print(f"   Requests: {scraper.stats.requests_made}")
        print(f"   Success rate: {scraper.stats.success_rate:.2%}")
        print(f"   Data items: {scraper.stats.data_items_scraped}")
        print(f"   Errors: {scraper.stats.errors}")
        print(f"   Elapsed time: {scraper.stats.elapsed_time:.2f}s")

        # Export telemetry
        telemetry_data = scraper.telemetry.export_metrics()
        print(f"   Telemetry events: {len(telemetry_data['events'])}")

    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)






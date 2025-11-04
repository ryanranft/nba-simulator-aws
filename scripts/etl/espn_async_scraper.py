#!/usr/bin/env python3
"""
ESPN Async Scraper - Modern ESPN Data Collection

Migrated ESPN incremental scraper to async architecture with:
- AsyncBaseScraper base class
- Centralized error handling
- Telemetry and monitoring
- Configuration management
- Smart retry strategies

Based on Crawl4AI MCP server patterns and async_scraper_base.py.

Usage:
    python scripts/etl/espn_async_scraper.py
    python scripts/etl/espn_async_scraper.py --days-back 7
    python scripts/etl/espn_async_scraper.py --dry-run

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
from scripts.etl.scraper_error_handler import (
    ScraperErrorHandler,
    NetworkError,
    RateLimitError,
    ServerError,
    ClientError,
    ContentError,
)
from scripts.etl.scraper_telemetry import ScraperTelemetry, TelemetryManager
from scripts.etl.scraper_config import ScraperConfigManager, get_scraper_config


class ESPNAsyncScraper(AsyncBaseScraper):
    """Async ESPN NBA data scraper"""

    def __init__(self, config: ScraperConfig, days_back: int = 14):
        super().__init__(config)
        self.days_back = days_back
        self.error_handler = ScraperErrorHandler()
        self.telemetry = ScraperTelemetry("espn_scraper")

        # ESPN-specific endpoints
        self.endpoints = {
            "scoreboard": f"{config.base_url}/scoreboard",
            "summary": f"{config.base_url}/summary",
            "playbyplay": f"{config.base_url}/playbyplay",
        }

        # Data types to collect
        self.data_types = ["schedule", "box_scores", "team_stats", "pbp"]

        # Create subdirectories
        for data_type in self.data_types:
            (self.output_dir / data_type).mkdir(parents=True, exist_ok=True)

    async def scrape(self) -> None:
        """Main scraping method"""
        async with self.telemetry.track_operation("espn_scrape"):
            self.logger.info(
                f"Starting ESPN async scraper (last {self.days_back} days)"
            )

            # Get date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days_back)

            # Generate date list
            dates = []
            current_date = start_date
            while current_date <= end_date:
                dates.append(current_date.strftime("%Y%m%d"))
                current_date += timedelta(days=1)

            self.logger.info(
                f"Scraping {len(dates)} dates from {start_date.date()} to {end_date.date()}"
            )

            # Process dates concurrently
            await self._scrape_dates_concurrent(dates)

            self.logger.info("ESPN async scraper completed")

    async def _scrape_dates_concurrent(self, dates: List[str]) -> None:
        """Scrape multiple dates concurrently"""
        # Limit concurrent dates to avoid overwhelming the API
        semaphore = asyncio.Semaphore(min(5, self.config.max_concurrent))

        async def scrape_date_with_semaphore(date_str: str):
            async with semaphore:
                await self._scrape_date(date_str)

        # Create tasks for all dates
        tasks = [scrape_date_with_semaphore(date) for date in dates]

        # Process with progress tracking
        completed = 0
        for task in asyncio.as_completed(tasks):
            await task
            completed += 1
            if completed % 10 == 0:
                self.logger.info(f"Completed {completed}/{len(dates)} dates")

    async def _scrape_date(self, date_str: str) -> None:
        """Scrape all data for a specific date"""
        try:
            async with self.telemetry.track_operation(f"scrape_date_{date_str}"):
                # Get schedule for the date
                schedule_data = await self._get_schedule(date_str)
                if not schedule_data:
                    return

                # Extract game IDs
                game_ids = self._extract_game_ids(schedule_data)
                if not game_ids:
                    self.logger.info(f"No games found for {date_str}")
                    return

                self.logger.info(f"Found {len(game_ids)} games for {date_str}")

                # Process games concurrently
                await self._scrape_games_concurrent(game_ids, date_str)

        except Exception as e:
            self.logger.error(f"Error scraping date {date_str}: {e}")
            await self.error_handler.handle_error(
                ContentError(f"Date scraping failed: {e}")
            )

    async def _get_schedule(self, date_str: str) -> Optional[Dict]:
        """Get schedule for a specific date"""
        url = self.endpoints["scoreboard"]
        params = {"dates": date_str, "limit": 100}

        try:
            response = await self.fetch_url(url, params)
            if response:
                data = await self.parse_json_response(response)
                if data:
                    # Store schedule data
                    filename = f"schedule_{date_str}.json"
                    await self.store_data(data, filename, "schedule")
                    return data
        except Exception as e:
            self.logger.error(f"Error fetching schedule for {date_str}: {e}")
            await self.error_handler.handle_error(
                NetworkError(f"Schedule fetch failed: {e}")
            )

        return None

    def _extract_game_ids(self, schedule_data: Dict) -> List[str]:
        """Extract game IDs from schedule data"""
        game_ids = []

        try:
            events = schedule_data.get("events", [])
            for event in events:
                game_id = event.get("id")
                if game_id:
                    game_ids.append(str(game_id))
        except Exception as e:
            self.logger.error(f"Error extracting game IDs: {e}")

        return game_ids

    async def _scrape_games_concurrent(
        self, game_ids: List[str], date_str: str
    ) -> None:
        """Scrape multiple games concurrently"""
        # Limit concurrent games
        semaphore = asyncio.Semaphore(min(10, self.config.max_concurrent))

        async def scrape_game_with_semaphore(game_id: str):
            async with semaphore:
                await self._scrape_game(game_id, date_str)

        # Create tasks for all games
        tasks = [scrape_game_with_semaphore(game_id) for game_id in game_ids]

        # Process games
        for task in asyncio.as_completed(tasks):
            await task

    async def _scrape_game(self, game_id: str, date_str: str) -> None:
        """Scrape all data for a specific game"""
        try:
            async with self.telemetry.track_operation(f"scrape_game_{game_id}"):
                # Scrape different data types concurrently
                tasks = [
                    self._scrape_box_score(game_id, date_str),
                    self._scrape_team_stats(game_id, date_str),
                    self._scrape_play_by_play(game_id, date_str),
                ]

                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"Error scraping game {game_id}: {e}")
            await self.error_handler.handle_error(
                ContentError(f"Game scraping failed: {e}")
            )

    async def _scrape_box_score(self, game_id: str, date_str: str) -> None:
        """Scrape box score for a game"""
        url = self.endpoints["summary"]
        params = {"event": game_id}

        try:
            response = await self.fetch_url(url, params)
            if response:
                data = await self.parse_json_response(response)
                if data:
                    filename = f"box_score_{game_id}.json"
                    await self.store_data(data, filename, "box_scores")
                    self.telemetry.metrics.record_data_item("box_score")
        except Exception as e:
            self.logger.error(f"Error fetching box score for game {game_id}: {e}")
            await self.error_handler.handle_error(
                NetworkError(f"Box score fetch failed: {e}")
            )

    async def _scrape_team_stats(self, game_id: str, date_str: str) -> None:
        """Scrape team stats for a game"""
        # ESPN team stats are included in the summary endpoint
        # This is a placeholder for future team-specific endpoints
        pass

    async def _scrape_play_by_play(self, game_id: str, date_str: str) -> None:
        """Scrape play-by-play for a game"""
        url = self.endpoints["playbyplay"]
        params = {"event": game_id}

        try:
            response = await self.fetch_url(url, params)
            if response:
                data = await self.parse_json_response(response)
                if data:
                    filename = f"pbp_{game_id}.json"
                    await self.store_data(data, filename, "pbp")
                    self.telemetry.metrics.record_data_item("play_by_play")
        except Exception as e:
            self.logger.error(f"Error fetching play-by-play for game {game_id}: {e}")
            await self.error_handler.handle_error(
                NetworkError(f"PBP fetch failed: {e}")
            )

    async def scrape_missing_pbp(self, seasons: List[str]) -> None:
        """Scrape missing play-by-play data for specific seasons"""
        async with self.telemetry.track_operation("scrape_missing_pbp"):
            self.logger.info(f"Scraping missing PBP data for seasons: {seasons}")

            for season in seasons:
                await self._scrape_season_pbp(season)

    async def _scrape_season_pbp(self, season: str) -> None:
        """Scrape PBP data for a specific season"""
        # This would implement the logic to find missing games
        # and scrape only the PBP data for those games
        # For now, this is a placeholder
        self.logger.info(f"Scraping PBP for season {season} (placeholder)")


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="ESPN Async Scraper")
    parser.add_argument(
        "--days-back",
        type=int,
        default=14,
        help="Number of days back to scrape (default: 14)",
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
        "--seasons",
        nargs="+",
        help="Specific seasons to scrape (e.g., 2022-23 2023-24)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_manager = ScraperConfigManager(args.config_file)
        config = config_manager.get_scraper_config("espn")
        if not config:
            print("❌ ESPN configuration not found")
            return

        # Override config with command line args
        if args.dry_run:
            config.dry_run = True

        print(f"✅ Loaded ESPN configuration")
        print(f"   Base URL: {config.base_url}")
        print(f"   Rate limit: {config.rate_limit.requests_per_second} req/s")
        print(f"   Max concurrent: {config.max_concurrent}")
        print(f"   Dry run: {config.dry_run}")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return

    # Create scraper
    scraper = ESPNAsyncScraper(config, days_back=args.days_back)

    try:
        # Run scraper
        async with scraper:
            if args.seasons:
                await scraper.scrape_missing_pbp(args.seasons)
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



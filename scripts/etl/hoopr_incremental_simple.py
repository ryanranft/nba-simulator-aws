#!/usr/bin/env python3
"""
hoopR Incremental Scraper - Simplified (No Local Database)

Scrapes last N days of hoopR data directly to S3.
No local database required - always scrapes recent window.

Usage:
    python scripts/etl/hoopr_incremental_simple.py              # Last 3 days
    python scripts/etl/hoopr_incremental_simple.py --days 7     # Last 7 days
    python scripts/etl/hoopr_incremental_simple.py --dry-run    # Test mode

For overnight automation (3-source cross-validation):
    - Scrapes last 3 days every night
    - Uploads to S3
    - Enables cross-validation with ESPN and NBA API

Version: 4.0 (AsyncBaseScraper Integration)
Created: October 18, 2025
Updated: October 22, 2025 (Session 7 - Framework Migration)
"""

import argparse
import asyncio
import json
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

# Suppress pkg_resources deprecation warning from sportsdataverse
warnings.filterwarnings(
    "ignore", message="pkg_resources is deprecated", category=UserWarning
)
# Suppress scripts.etl deprecation warning until modules are fully migrated
warnings.filterwarnings(
    "ignore", message="scripts.etl is deprecated", category=DeprecationWarning
)

# Import hoopR
try:
    from sportsdataverse.nba import nba_pbp, nba_schedule
except ImportError:
    print("ERROR: sportsdataverse not installed")
    print("Install: pip install sportsdataverse")
    sys.exit(1)

# Import AsyncBaseScraper and config loader
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import get_scraper_config


class HoopRIncrementalScraper(AsyncBaseScraper):
    """Simple hoopR scraper - last N days to S3"""

    def __init__(
        self, days_back=3, dry_run=False, config_name="hoopr_incremental_simple"
    ):
        """
        Initialize hoopR incremental scraper

        Args:
            days_back: Number of days to look back
            dry_run: If True, don't upload to S3
            config_name: Name of config section in scraper_config.yaml
        """
        # Load config and pass to parent
        config = get_scraper_config(config_name)
        if not config:
            raise ValueError(f"Could not load config for '{config_name}'")

        super().__init__(config)

        self.days_back = days_back
        self.dry_run = dry_run

        # Override upload setting if dry run
        if dry_run:
            self.config.storage.upload_to_s3 = False

        # Stats
        self.stats = {
            "games_scraped": 0,
            "games_uploaded": 0,
            "errors": 0,
        }

    def get_date_range(self):
        """Get list of dates to scrape."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_back)

        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return dates

    async def get_schedule_for_date(self, date_str):
        """Get hoopR schedule for a specific date (async wrapper)."""
        try:
            # Parse date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            season = date_obj.year if date_obj.month >= 10 else date_obj.year - 1

            # Get schedule (synchronous call wrapped in executor)
            schedule = await asyncio.to_thread(nba_schedule, season)

            if schedule is None or schedule.empty:
                return []

            # Filter to specific date
            schedule["game_date"] = schedule["date"].str[:10]
            games = schedule[schedule["game_date"] == date_str]

            return games["id"].tolist() if not games.empty else []

        except Exception as e:
            self.logger.error(f"Error getting schedule for {date_str}: {e}")
            self.stats["errors"] += 1
            return []

    async def get_play_by_play(self, game_id):
        """Get play-by-play for a game (async wrapper)."""
        try:
            # Use base class rate limiter
            await self.rate_limiter.acquire()

            # Fetch PBP (synchronous call wrapped in executor)
            pbp_data = await asyncio.to_thread(nba_pbp, game_id)

            if pbp_data is not None and not pbp_data.empty:
                return pbp_data.to_dict("records")
            return None

        except Exception as e:
            self.logger.error(f"Error fetching PBP for game {game_id}: {e}")
            self.stats["errors"] += 1
            return None

    async def scrape_date(self, date_str):
        """Scrape all games for a specific date."""
        self.logger.info(f"\nScraping hoopR data for {date_str}...")

        # Get schedule
        game_ids = await self.get_schedule_for_date(date_str)

        if not game_ids:
            self.logger.info(f"  No games found for {date_str}")
            return

        self.logger.info(f"  Found {len(game_ids)} games")

        # Process each game
        for game_id in game_ids:
            self.logger.info(f"  Processing game {game_id}...")

            # Get play-by-play
            pbp_data = await self.get_play_by_play(game_id)

            if pbp_data:
                # Store to S3 using base class
                s3_key = f"{self.config.storage.s3_prefix}/{date_str}/game_{game_id}_pbp.json"

                if self.dry_run:
                    self.logger.info(
                        f"  [DRY RUN] Would upload to s3://{self.config.storage.s3_bucket}/{s3_key}"
                    )
                    self.stats["games_scraped"] += 1
                else:
                    success = await self.store_data(
                        data=pbp_data,
                        s3_key=s3_key,
                        local_filename=f"game_{game_id}_pbp.json",
                    )

                    if success:
                        self.stats["games_scraped"] += 1
                        self.stats["games_uploaded"] += 1
                        self.logger.info(f"    ✓ Uploaded to S3")

    async def run(self):
        """Run incremental scrape."""
        print("\n" + "=" * 70)
        print("HOOPR INCREMENTAL SCRAPER (AsyncBaseScraper)")
        print("=" * 70)
        print(f"\nScraping last {self.days_back} days")
        print(f"Dry run: {self.dry_run}")
        print(f"S3 bucket: {self.config.storage.s3_bucket}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Get date range
        dates = self.get_date_range()
        self.logger.info(f"Date range: {dates[0]} to {dates[-1]} ({len(dates)} days)")

        # Scrape each date
        for date_str in dates:
            await self.scrape_date(date_str)

        # Print summary
        print("\n" + "=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Games scraped:   {self.stats['games_scraped']}")
        print(f"Games uploaded:  {self.stats['games_uploaded']}")
        print(f"Errors:          {self.stats['errors']}")
        print("=" * 70)
        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async def scrape(self) -> None:
        """Main scraping method - implements AsyncBaseScraper abstract method"""
        await self.run()


async def main_async():
    """Async main function."""
    parser = argparse.ArgumentParser(
        description="hoopR incremental scraper (AsyncBaseScraper)"
    )
    parser.add_argument(
        "--days", type=int, default=3, help="Number of days to scrape back (default: 3)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Test mode - don't upload to S3"
    )

    args = parser.parse_args()

    scraper = HoopRIncrementalScraper(days_back=args.days, dry_run=args.dry_run)
    await scraper.run()


def main():
    """Entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

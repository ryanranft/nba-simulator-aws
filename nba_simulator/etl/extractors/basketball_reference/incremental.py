#!/usr/bin/env python3
"""
Basketball Reference Incremental Scraper - Daily Updates Only

Migrated to AsyncBaseScraper framework

Purpose: Scrapes current season aggregate data (season totals + advanced stats) for daily updates
Data Source: Basketball Reference API (via basketball_reference_web_scraper library)
Update Frequency: Daily (during season) or as needed

Strategy:
1. Determine current NBA season
2. Scrape season totals for current season (updated daily as games are played)
3. Scrape advanced totals for current season
4. Upload to S3 automatically
5. Optionally re-integrate into local database

During the season:
- Player stats get updated as games are played
- New players are added (call-ups, trades, etc.)
- Typically takes 30-60 seconds to scrape both data types

Off-season:
- Previous season finalized stats are scraped
- No current season data available yet
- Takes <10 seconds

Runtime: ~1 minute during season, <10 seconds off-season

Version: 2.0 (Migrated to AsyncBaseScraper)
Created: October 10, 2025
Migrated: October 22, 2025

Features:
- Async framework with synchronous library client
- Automatic rate limiting (12s between requests)
- Retry logic with exponential backoff
- S3 upload integration
- Telemetry and monitoring

Usage:
    python scripts/etl/basketball_reference_incremental_scraper.py
    python scripts/etl/basketball_reference_incremental_scraper.py --also-previous-season
    python scripts/etl/basketball_reference_incremental_scraper.py --dry-run

Configuration:
    See config/scraper_config.yaml - basketball_reference_incremental section
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager

# Basketball Reference library (synchronous)
try:
    from basketball_reference_web_scraper import client

    HAS_BBREF = True
except ImportError:
    HAS_BBREF = False
    print("❌ basketball_reference_web_scraper not installed")
    print("Install: pip install basketball_reference_web_scraper")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BasketballReferenceIncrementalScraper(AsyncBaseScraper):
    """
    Incremental scraper for Basketball Reference aggregate data

    Migrated to AsyncBaseScraper framework for:
    - Automatic rate limiting (12s between requests)
    - Retry logic with exponential backoff
    - S3 upload integration
    - Telemetry and monitoring

    Note: Uses basketball_reference_web_scraper (synchronous library)
    wrapped in async methods for compatibility with AsyncBaseScraper.
    """

    def __init__(self, config, also_previous_season: bool = False):
        """Initialize incremental scraper with configuration"""
        super().__init__(config)

        # Custom settings from config
        self.data_types = config.custom_settings.get(
            "data_types", ["season_totals", "advanced_totals"]
        )
        self.include_combined_values = config.custom_settings.get(
            "include_combined_values", True
        )
        self.also_previous_season = also_previous_season

        # Statistics tracking
        self.scrape_stats = {
            "seasons_scraped": 0,
            "data_types_scraped": 0,
            "total_records": 0,
            "successes": 0,
            "failures": 0,
        }

        logger.info(f"Initialized {self.__class__.__name__}")
        logger.info(f"Data types: {self.data_types}")
        logger.info(f"Include combined values: {self.include_combined_values}")
        logger.info(f"Also scrape previous season: {self.also_previous_season}")

    def get_current_season(self) -> int:
        """
        Get current NBA season end year

        NBA season spans two calendar years:
        - 2024-2025 season = end year 2025
        - Season starts in October
        - If Oct-Dec: next year is end year
        - If Jan-Sep: current year is end year

        Returns:
            Season end year (e.g., 2025 for 2024-2025 season)
        """
        now = datetime.now()
        if now.month >= 10:
            return now.year + 1
        else:
            return now.year

    async def scrape_season_totals(self, season: int) -> bool:
        """
        Scrape season totals for a given season

        Args:
            season: Season end year (e.g., 2025 for 2024-2025)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"\n📊 Scraping season totals for {season-1}-{season} season...")

        try:
            # Wrap synchronous client call with rate limiting
            # The rate limiter in AsyncBaseScraper will handle delays
            await self.rate_limiter.acquire()

            # Make synchronous API call (library is not async)
            totals = await asyncio.to_thread(
                client.players_season_totals, season_end_year=season
            )

            if totals:
                # Convert to JSON-serializable format
                data = [dict(item) for item in totals]

                # Store data (automatically uploads to S3 if configured)
                filename = f"player_season_totals.json"
                subdir = f"season_totals/{season}"

                await self.store_data(data=data, filename=filename, subdir=subdir)

                self.scrape_stats["total_records"] += len(data)
                self.scrape_stats["successes"] += 1

                logger.info(f"  ✓ Season totals: {len(data)} player records")
                return True
            else:
                logger.warning(f"  ⚠️  No season totals data returned")
                self.scrape_stats["failures"] += 1
                return False

        except Exception as e:
            logger.error(f"  ❌ Failed to scrape season totals: {e}")
            self.scrape_stats["failures"] += 1
            # Let AsyncBaseScraper handle retry logic
            raise

    async def scrape_advanced_totals(self, season: int) -> bool:
        """
        Scrape advanced totals for a given season

        Args:
            season: Season end year (e.g., 2025 for 2024-2025)

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"\n📈 Scraping advanced totals for {season-1}-{season} season...")

        try:
            # Wrap synchronous client call with rate limiting
            await self.rate_limiter.acquire()

            # Make synchronous API call with combined values for traded players
            totals = await asyncio.to_thread(
                client.players_advanced_season_totals,
                season_end_year=season,
                include_combined_values=self.include_combined_values,
            )

            if totals:
                # Convert to JSON-serializable format
                data = [dict(item) for item in totals]

                # Store data (automatically uploads to S3 if configured)
                filename = f"player_advanced_totals.json"
                subdir = f"advanced_totals/{season}"

                await self.store_data(data=data, filename=filename, subdir=subdir)

                self.scrape_stats["total_records"] += len(data)
                self.scrape_stats["successes"] += 1

                logger.info(f"  ✓ Advanced totals: {len(data)} player records")
                return True
            else:
                logger.warning(f"  ⚠️  No advanced totals data returned")
                self.scrape_stats["failures"] += 1
                return False

        except Exception as e:
            logger.error(f"  ❌ Failed to scrape advanced totals: {e}")
            self.scrape_stats["failures"] += 1
            raise

    async def scrape(self) -> None:
        """
        Main scraping method - scrapes current season aggregate data

        This method is called by AsyncBaseScraper when run.
        Implements incremental scraping of current (and optionally previous) season.
        """
        print("=" * 70)
        print("BASKETBALL REFERENCE INCREMENTAL SCRAPER")
        print("=" * 70)
        print()

        current_season = self.get_current_season()

        print(f"Current NBA season: {current_season-1}-{current_season}")
        print(
            f"Rate limit: {1/self.config.rate_limit.requests_per_second:.1f}s between requests"
        )
        print(
            f"S3 upload: {'Enabled' if self.config.storage.upload_to_s3 else 'Disabled'}"
        )
        if self.config.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
        print()

        # Determine seasons to scrape
        seasons_to_scrape = [current_season]
        if self.also_previous_season:
            seasons_to_scrape.insert(0, current_season - 1)
            logger.info(
                f"Also scraping previous season: {current_season-2}-{current_season-1}\n"
            )

        # Scrape each season
        for season in seasons_to_scrape:
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logger.info(f"Season {season-1}-{season}")
            logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            # Scrape season totals
            await self.scrape_season_totals(season)

            # Small delay between data types (if not dry run)
            if not self.config.dry_run:
                await asyncio.sleep(5)

            # Scrape advanced totals
            await self.scrape_advanced_totals(season)

            self.scrape_stats["seasons_scraped"] += 1
            self.scrape_stats["data_types_scraped"] += 2

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print scraping summary"""
        print()
        print("=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Seasons scraped:       {self.scrape_stats['seasons_scraped']}")
        print(f"Data types scraped:    {self.scrape_stats['data_types_scraped']}")
        print(f"Total records:         {self.scrape_stats['total_records']}")
        print(f"Successful operations: {self.scrape_stats['successes']}")
        print(f"Failed operations:     {self.scrape_stats['failures']}")
        print("=" * 70)
        print()

        if self.scrape_stats["failures"] == 0:
            print("✅ All data scraped successfully!")
        else:
            print(f"⚠️  {self.scrape_stats['failures']} scraping operations failed")

        if not self.config.dry_run and self.config.storage.upload_to_s3:
            print()
            print("Next step: Re-integrate into local database")
            print("  python scripts/etl/integrate_basketball_reference_aggregate.py")


async def main():
    """Main entry point for incremental scraper"""
    parser = argparse.ArgumentParser(
        description="Basketball Reference Incremental Scraper - Daily updates only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape current season only (default)
  python scripts/etl/basketball_reference_incremental_scraper.py

  # Scrape current + previous season (end-of-season updates)
  python scripts/etl/basketball_reference_incremental_scraper.py --also-previous-season

  # Dry run (don't upload to S3 or save files)
  python scripts/etl/basketball_reference_incremental_scraper.py --dry-run

Purpose:
  Designed for nightly automation. Only fetches current season aggregate data.
  For historical backfills, use: scripts/etl/scrape_basketball_reference_complete.py

During the season:
  - Player stats update as games are played
  - New players are added (call-ups, trades)
  - Run nightly to keep stats current

Off-season:
  - Previous season finalized stats
  - No current season data yet
        """,
    )

    parser.add_argument(
        "--also-previous-season",
        action="store_true",
        help="Also scrape previous season (for end-of-season finalized stats)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't save files or upload to S3",
    )

    parser.add_argument(
        "--config",
        default="config/scraper_config.yaml",
        help="Path to scraper config file (default: config/scraper_config.yaml)",
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load configuration
    config_manager = ScraperConfigManager(args.config)
    config = config_manager.get_scraper_config("basketball_reference_incremental")

    if not config:
        logger.error("Configuration not found for basketball_reference_incremental")
        logger.error("Check config/scraper_config.yaml")
        return

    # Override dry_run if specified
    if args.dry_run:
        config.dry_run = True

    # Run scraper
    async with BasketballReferenceIncrementalScraper(
        config, also_previous_season=args.also_previous_season
    ) as scraper:
        await scraper.scrape()

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())

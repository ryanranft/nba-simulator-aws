#!/usr/bin/env python3
"""
Basketball Reference Daily Play-by-Play Scraper

Migrated to AsyncBaseScraper framework

Scrapes play-by-play data for games from yesterday (or specified date).
Designed for nightly automation to keep PBP database current.

This is the DAILY companion to basketball_reference_pbp_backfill.py (historical).

How it works:
1. Get yesterday's date (or user-specified date)
2. Query ESPN API for games on that date
3. Convert to Basketball Reference game IDs
4. Extract ONLY play-by-play data (no box scores)
5. Upload to S3: s3://.../basketball_reference/pbp/{YEAR}/{game_id}_pbp.json
6. Load into game_play_by_play table

Features:
- AsyncBaseScraper framework for standardized infrastructure
- Automatic rate limiting and retry logic
- Async HTTP requests with asyncio.to_thread()
- BeautifulSoup parsing wrapped in async
- SQLite operations wrapped in async
- S3 upload via store_data()
- Telemetry and monitoring

Usage:
    # Scrape yesterday's games (typical overnight usage)
    python scripts/etl/basketball_reference_daily_pbp.py

    # Scrape specific date
    python scripts/etl/basketball_reference_daily_pbp.py --date 2023-06-12

    # Scrape last N days
    python scripts/etl/basketball_reference_daily_pbp.py --days 3

    # Dry run (test without uploading/inserting)
    python scripts/etl/basketball_reference_daily_pbp.py --dry-run

Version: 2.0 (Migrated to AsyncBaseScraper)
Created: October 18, 2025
Migrated: October 22, 2025 (Session 5)
"""

import asyncio
import argparse
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from nba_simulator.etl.config import ScraperConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DailyPBPScraper(AsyncBaseScraper):
    """
    Daily play-by-play scraper for Basketball Reference

    Migrated to AsyncBaseScraper framework for:
    - Automatic rate limiting and retry logic
    - S3 backup storage via store_data()
    - Telemetry and monitoring
    - Configuration-driven behavior

    Note: Uses requests + BeautifulSoup (synchronous)
    wrapped in async methods for compatibility with AsyncBaseScraper.
    """

    def __init__(self, config, dry_run=False, upload_to_s3=True):
        super().__init__(config)

        # Custom settings from config
        self.db_path = config.custom_settings.get(
            "database_path",
            "/tmp/basketball_reference_boxscores.db",  # nosec B108 - /tmp is fallback default, actual path from config
        )
        self.upload_to_s3 = upload_to_s3 if not dry_run else False
        self.dry_run = dry_run

        # Database connection (None if dry run)
        self.db_conn = None if dry_run else sqlite3.connect(self.db_path)

        # Statistics
        self.stats_custom = {
            "games_checked": 0,
            "games_with_pbp": 0,
            "games_without_pbp": 0,
            "pbp_events_total": 0,
            "uploaded_to_s3": 0,
            "database_inserts": 0,
            "errors": 0,
        }

    async def scrape(self) -> None:
        """Main scraping method (required by AsyncBaseScraper)"""
        # This method is called by the base class context manager
        # Actual scraping is done by run() method which is called from main()
        pass

    async def get_games_from_espn(self, date_str: str) -> List[Dict]:
        """Get games for a specific date from ESPN API"""
        # Wrap synchronous ESPN API call in asyncio.to_thread
        return await asyncio.to_thread(self._get_games_from_espn_sync, date_str)

    def _get_games_from_espn_sync(self, date_str: str) -> List[Dict]:
        """Synchronous version of get_games_from_espn (wrapped by async version)"""
        try:
            # ESPN scoreboard API (date format: YYYYMMDD)
            date_formatted = date_str.replace("-", "")
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date_formatted}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            games = []
            for event in data.get("events", []):
                competitions = event.get("competitions", [])
                if not competitions:
                    continue

                competition = competitions[0]
                competitors = competition.get("competitors", [])

                if len(competitors) != 2:
                    continue

                # Find home and away teams
                home_team = next(
                    (c for c in competitors if c.get("homeAway") == "home"), None
                )
                away_team = next(
                    (c for c in competitors if c.get("homeAway") == "away"), None
                )

                if not home_team or not away_team:
                    continue

                # Get abbreviations
                home_abbr = home_team.get("team", {}).get("abbreviation", "")
                away_abbr = away_team.get("team", {}).get("abbreviation", "")

                # Get date
                game_date = event.get("date", "")[:10]  # Extract YYYY-MM-DD

                # Build Basketball Reference game ID
                # Format: YYYYMMDD0{HOME_TEAM_CODE}
                date_code = game_date.replace("-", "")
                game_id = f"{date_code}0{home_abbr}"

                games.append(
                    {
                        "game_id": game_id,
                        "game_date": game_date,
                        "home_team": home_abbr,
                        "away_team": away_abbr,
                    }
                )

            return games

        except Exception as e:
            self.logger.error(f"Error fetching games from ESPN for {date_str}: {e}")
            return []

    async def fetch_pbp_for_game(self, game_id: str) -> Optional[List[Dict]]:
        """Fetch play-by-play data for a single game"""
        url = f"{self.config.base_url}/boxscores/{game_id}.html"

        try:
            # Use rate limiter from base class
            await self.rate_limiter.acquire()

            # Wrap synchronous requests.get in asyncio.to_thread
            response = await asyncio.to_thread(
                requests.get,
                url,
                headers={"User-Agent": self.config.user_agent},
                timeout=self.config.timeout,
            )

            if response.status_code == 404:
                self.logger.debug(f"Game {game_id} not found")
                return None

            if response.status_code == 429:
                self.logger.warning(f"Rate limited on {game_id}")
                return None

            response.raise_for_status()

            # Parse HTML (wrapped in async)
            pbp_events = await self.parse_play_by_play(response.text, game_id)

            return pbp_events if pbp_events else None

        except Exception as e:
            self.logger.error(f"Error fetching PBP for {game_id}: {e}")
            return None

    async def parse_play_by_play(self, html: str, game_id: str) -> Optional[List[Dict]]:
        """Parse play-by-play data from HTML (async wrapper)"""
        # Wrap synchronous BeautifulSoup parsing in asyncio.to_thread
        return await asyncio.to_thread(self._parse_play_by_play_sync, html, game_id)

    def _parse_play_by_play_sync(self, html: str, game_id: str) -> Optional[List[Dict]]:
        """Extract play-by-play events from HTML"""
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Find PBP table
            pbp_table = soup.find("table", {"id": "pbp"})
            if not pbp_table:
                return None

            tbody = pbp_table.find("tbody")
            if not tbody:
                return None

            rows = tbody.find_all("tr")

            events = []
            for row in rows:
                # Skip quarter headers
                if row.get("class") and "thead" in row.get("class"):
                    continue

                event = {}

                # Extract all cells
                for cell in row.find_all(["th", "td"]):
                    stat_name = cell.get("data-stat")
                    if stat_name:
                        event[stat_name] = cell.text.strip()

                if event:
                    events.append(event)

            return events if events else None

        except Exception as e:
            self.logger.error(f"Error parsing PBP for {game_id}: {e}")
            return None

    async def upload_to_s3_bucket(self, game_id: str, pbp_data: List[Dict]) -> bool:
        """Upload PBP JSON to S3 using base class store_data() method"""
        if self.dry_run or not self.upload_to_s3:
            self.logger.info(f"[DRY RUN] Would upload {game_id} PBP to S3")
            return True

        try:
            # Extract year from game_id
            year = game_id[:4]

            # Filename: basketball_reference/pbp/YYYY/game_id_pbp.json
            filename = f"{year}/{game_id}_pbp.json"

            # Build JSON
            data = {
                "game_id": game_id,
                "scraped_at": datetime.utcnow().isoformat(),
                "event_count": len(pbp_data),
                "events": pbp_data,
            }

            # Use base class store_data() method
            success = await self.store_data(data, filename, "pbp")

            if success:
                self.stats_custom["uploaded_to_s3"] += 1

            return success

        except Exception as e:
            self.logger.error(f"Error uploading {game_id} to S3: {e}")
            return False

    async def load_to_database(self, game_id: str, pbp_data: List[Dict]) -> bool:
        """Load PBP events into game_play_by_play table (async wrapper)"""
        if self.dry_run:
            self.logger.info(
                f"[DRY RUN] Would insert {len(pbp_data)} PBP events for {game_id}"
            )
            return True

        # Wrap synchronous database operations in asyncio.to_thread
        return await asyncio.to_thread(self._load_to_database_sync, game_id, pbp_data)

    def _load_to_database_sync(self, game_id: str, pbp_data: List[Dict]) -> bool:
        """Synchronous version of load_to_database (wrapped by async version)"""
        try:
            cursor = self.db_conn.cursor()

            # Delete existing PBP for this game (if any)
            cursor.execute(
                "DELETE FROM game_play_by_play WHERE game_id = ?", (game_id,)
            )

            # Insert each event
            for event in pbp_data:
                # Build dynamic INSERT based on available fields
                columns = ["game_id"]
                values = [game_id]

                # Map PBP fields to database columns
                field_mapping = {
                    "quarter": "quarter",
                    "time": "time_remaining",
                    "description": "description",
                    "away_score": "away_score",
                    "home_score": "home_score",
                }

                for field, column in field_mapping.items():
                    if field in event and event[field]:
                        columns.append(column)
                        values.append(event[field])

                # Build INSERT query
                placeholders = ",".join(["?" for _ in values])
                query = f"INSERT INTO game_play_by_play ({','.join(columns)}) VALUES ({placeholders})"  # nosec B608 - Uses parameterized queries (?) to prevent SQL injection

                try:
                    cursor.execute(query, values)
                except Exception as e:
                    self.logger.debug(f"Error inserting PBP event: {e}")

            self.db_conn.commit()
            self.stats_custom["database_inserts"] += 1
            return True

        except Exception as e:
            self.logger.error(f"Database insert failed for {game_id}: {e}")
            return False

    async def process_game(self, game: Dict) -> bool:
        """Process a single game for PBP data"""
        game_id = game["game_id"]

        self.logger.info(
            f"Checking {game_id} ({game['game_date']}) - {game['away_team']} @ {game['home_team']}"
        )

        self.stats_custom["games_checked"] += 1

        # Fetch PBP
        pbp_data = await self.fetch_pbp_for_game(game_id)

        if not pbp_data:
            self.logger.info(f"  ✗ No PBP data")
            self.stats_custom["games_without_pbp"] += 1
            return False

        event_count = len(pbp_data)
        self.logger.info(f"  ✓ Found {event_count} PBP events")

        self.stats_custom["games_with_pbp"] += 1
        self.stats_custom["pbp_events_total"] += event_count

        # Upload to S3
        if self.upload_to_s3:
            s3_success = await self.upload_to_s3_bucket(game_id, pbp_data)
            if not s3_success:
                self.logger.warning(f"S3 upload failed for {game_id}")

        # Load to database
        db_success = await self.load_to_database(game_id, pbp_data)
        if not db_success:
            self.logger.warning(f"Database insert failed for {game_id}")
            self.stats_custom["errors"] += 1

        return True

    async def run(self, dates: List[str]):
        """Run daily PBP scraper for specified dates"""
        print("\n" + "=" * 70)
        print("BASKETBALL REFERENCE DAILY PBP SCRAPER (AsyncBaseScraper)")
        print("=" * 70)
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Dry run: {self.dry_run}")
        print(f"Upload to S3: {self.upload_to_s3}")
        print(f"Dates to scrape: {', '.join(dates)}")
        print()

        # Get games for each date
        all_games = []
        for date in dates:
            self.logger.info(f"Fetching games for {date}...")
            games = await self.get_games_from_espn(date)

            if games:
                self.logger.info(f"  Found {len(games)} games")
                all_games.extend(games)
            else:
                self.logger.info(f"  No games found (offseason or no games scheduled)")

        if not all_games:
            print("\n✓ No games to scrape")
            return

        total_games = len(all_games)
        print(f"\nTotal games found: {total_games}\n")

        # Estimated time based on rate limit (12 seconds per game)
        rate_limit_seconds = 12.0
        estimated_minutes = (total_games * rate_limit_seconds) / 60
        print(
            f"Estimated time: {estimated_minutes:.1f} minutes ({total_games} games × {rate_limit_seconds}s)\n"
        )

        # Process each game
        for idx, game in enumerate(all_games, 1):
            await self.process_game(game)

            # Progress update
            if idx % 5 == 0 or idx == total_games:
                print(f"\nProgress: {idx}/{total_games} ({100*idx/total_games:.1f}%)")
                print(
                    f"With PBP: {self.stats_custom['games_with_pbp']}, Without: {self.stats_custom['games_without_pbp']}"
                )
                print(f"Total events: {self.stats_custom['pbp_events_total']:,}\n")

        # Final summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Games checked:      {self.stats_custom['games_checked']}")
        print(f"Games with PBP:     {self.stats_custom['games_with_pbp']}")
        print(f"Games without PBP:  {self.stats_custom['games_without_pbp']}")
        print(f"Total PBP events:   {self.stats_custom['pbp_events_total']:,}")
        print(f"Uploaded to S3:     {self.stats_custom['uploaded_to_s3']}")
        print(f"Database inserts:   {self.stats_custom['database_inserts']}")
        print(f"Errors:             {self.stats_custom['errors']}")
        print("=" * 70)

        if self.stats_custom["games_with_pbp"] > 0:
            avg_events = (
                self.stats_custom["pbp_events_total"]
                / self.stats_custom["games_with_pbp"]
            )
            print(f"\nAverage events per game: {avg_events:.0f}")

        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def cleanup(self):
        """Close connections"""
        if self.db_conn:
            self.db_conn.close()


def get_yesterday():
    """Get yesterday's date"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


async def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference daily PBP scraper (AsyncBaseScraper)"
    )
    parser.add_argument(
        "--date", type=str, help="Date to scrape (YYYY-MM-DD), defaults to yesterday"
    )
    parser.add_argument(
        "--days", type=int, help="Scrape last N days instead of single date"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Test mode - don't upload or insert"
    )
    parser.add_argument("--no-s3", action="store_true", help="Don't upload to S3")
    parser.add_argument(
        "--config-file",
        type=str,
        default="config/scraper_config.yaml",
        help="Configuration file path",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_manager = ScraperConfigManager(args.config_file)
        config = config_manager.get_scraper_config("basketball_reference_daily_pbp")
        if not config:
            print("❌ Basketball Reference daily PBP configuration not found")
            return 1

        # Override config with command line args
        if args.dry_run:
            config.dry_run = True

        print(f"✅ Loaded Basketball Reference daily PBP configuration")
        print(f"   Base URL: {config.base_url}")
        print(
            f"   Rate limit: {config.rate_limit.requests_per_second} req/s (12s between requests)"
        )
        print(f"   Max concurrent: {config.max_concurrent}")
        print(f"   Dry run: {config.dry_run}")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1

    # Determine dates to scrape
    if args.days:
        dates = []
        for i in range(args.days):
            date = datetime.now() - timedelta(days=i + 1)
            dates.append(date.strftime("%Y-%m-%d"))
    elif args.date:
        dates = [args.date]
    else:
        dates = [get_yesterday()]

    scraper = DailyPBPScraper(config, dry_run=args.dry_run, upload_to_s3=not args.no_s3)

    try:
        # Run scraper using async context manager
        async with scraper:
            await scraper.run(dates=dates)

        # Print final statistics from base class
        print("\n📊 Base Statistics:")
        print(f"   Requests: {scraper.stats.requests_made}")
        print(f"   Success rate: {scraper.stats.success_rate:.2%}")
        print(f"   Data items: {scraper.stats.data_items_scraped}")
        print(f"   Errors: {scraper.stats.errors}")
        print(f"   Elapsed time: {scraper.stats.elapsed_time:.2f}s")

        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

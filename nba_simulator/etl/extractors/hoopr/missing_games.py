#!/usr/bin/env python3
"""
Scrape Missing hoopR Games from hoopR API

Fills gaps in hoopR database by scraping missing games from hoopR's ORIGINAL API.

CRITICAL: This script scrapes from hoopR API and loads ONLY to hoopR database.
Never loads data from other sources (maintains data integrity).

Gap List: /tmp/missing_from_hoopr.csv (2,464 games)
Target: Increase hoopR coverage from 92.1% → 100%

Usage:
    python scripts/etl/scrape_missing_hoopr_games.py
    python scripts/etl/scrape_missing_hoopr_games.py --limit 10  # Test on 10 games
    python scripts/etl/scrape_missing_hoopr_games.py --year 2003  # Scrape specific year
    python scripts/etl/scrape_missing_hoopr_games.py --sync-to-rds  # Also update RDS

Version: 2.0 (AsyncBaseScraper Integration)
Created: October 9, 2025
Updated: October 22, 2025 (Session 7 - Framework Migration)
"""

import argparse
import asyncio
import csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import hoopR/sportsdataverse
try:
    from sportsdataverse.nba import load_nba_pbp, load_nba_schedule

    HAS_SPORTSDATAVERSE = True
except ImportError:
    HAS_SPORTSDATAVERSE = False
    print("❌ sportsdataverse not installed")
    print("Install: pip install sportsdataverse")
    sys.exit(1)

# Import AsyncBaseScraper
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.scrapers.async_scraper_base import AsyncBaseScraper


class HoopRMissingGamesScraper(AsyncBaseScraper):
    """Scrape missing hoopR games for gap filling"""

    def __init__(
        self,
        limit=None,
        year=None,
        sync_to_rds=False,
        config_name="hoopr_missing_games",
    ):
        super().__init__(config_name=config_name)

        self.limit = limit
        self.year = year
        self.sync_to_rds = sync_to_rds

        # Get paths from config
        self.gap_list_path = self.config.custom_settings.get(  # nosec B108
            "gap_list_path", "/tmp/missing_from_hoopr.csv"  # Config fallback - safe
        )
        self.database_path = self.config.custom_settings.get(  # nosec B108
            "database_path", "/tmp/hoopr_local.db"  # Config fallback - safe
        )

        # Statistics
        self.stats = {
            "total_games": 0,
            "games_scraped": 0,
            "events_loaded": 0,
            "games_failed": 0,
            "games_no_data": 0,
        }

    def load_gap_list(self) -> List[Dict]:
        """Load list of games missing from hoopR."""
        print("=" * 70)
        print("LOAD GAP LIST")
        print("=" * 70)
        print()

        if not Path(self.gap_list_path).exists():
            raise FileNotFoundError(
                f"Gap list not found: {self.gap_list_path}\n"
                f"Run: python scripts/utils/cross_validate_espn_hoopr_with_mapping.py --export-gaps"
            )

        print(f"📂 Reading: {self.gap_list_path}")

        gaps = []
        with open(self.gap_list_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Filter by year if specified
                if self.year:
                    game_year = int(row["game_date"].split("-")[0])
                    if game_year != self.year:
                        continue

                gaps.append(row)

                if self.limit and len(gaps) >= self.limit:
                    break

        print(f"✓ Loaded {len(gaps):,} games to scrape")

        # Show year distribution
        year_counts = {}
        for gap in gaps:
            game_year = gap["game_date"].split("-")[0]
            year_counts[game_year] = year_counts.get(game_year, 0) + 1

        print()
        print("Year distribution:")
        for year in sorted(year_counts.keys()):
            print(f"  {year}: {year_counts[year]:,} games")
        print()

        return gaps

    async def scrape_game_from_hoopr(
        self, game_id: str, game_date: str
    ) -> Optional[List[Dict]]:
        """
        Scrape a specific game from hoopR API (async).

        Uses hoopR's load_nba_pbp with game_id or date filtering.
        """
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Extract season from game date (YYYY-MM-DD)
            year = int(game_date.split("-")[0])
            month = int(game_date.split("-")[1])

            # NBA season logic: Oct-June spans two calendar years
            # If month >= 10, season is current year
            # If month < 10, season is previous year
            season = year if month >= 10 else year - 1

            # Try to load play-by-play for this specific game
            # hoopR's load_nba_pbp accepts seasons parameter
            pbp_data = await asyncio.to_thread(load_nba_pbp, seasons=[season])

            # Check if data was returned
            if pbp_data is not None and len(pbp_data) > 0:
                # Filter to specific game_id
                game_pbp = pbp_data[pbp_data["game_id"] == int(game_id)]

                if len(game_pbp) > 0:
                    return game_pbp.to_dict("records")

            return None

        except Exception as e:
            self.logger.error(f"Error scraping {game_id}: {e}")
            return None

    def load_to_hoopr_database(self, game_id: str, pbp_events: List[Dict]) -> int:
        """
        Load scraped hoopR play-by-play to hoopR database.

        CRITICAL: Loads ONLY to hoopR database (maintains data integrity).
        """
        if not pbp_events:
            return 0

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Get hoopR table columns
        cursor.execute("PRAGMA table_info(play_by_play);")
        columns = [col[1] for col in cursor.fetchall()]

        loaded_count = 0

        for event in pbp_events:
            # Map event to hoopR schema
            values = []
            for col in columns:
                values.append(event.get(col))

            # Build INSERT statement
            placeholders = ",".join(["?" for _ in columns])
            column_list = ",".join(columns)

            try:
                cursor.execute(
                    f"""
                    INSERT OR IGNORE INTO play_by_play ({column_list})
                    VALUES ({placeholders})
                """,
                    values,
                )

                if cursor.rowcount > 0:
                    loaded_count += 1

            except Exception as e:
                self.logger.warning(f"Error loading event: {e}")
                continue

        conn.commit()
        cursor.close()
        conn.close()

        return loaded_count

    async def scrape_and_fill_gaps(self, gaps: List[Dict]):
        """Main gap-filling logic (async)."""
        print("=" * 70)
        print("SCRAPING MISSING GAMES FROM HOOPR API")
        print("=" * 70)
        print()

        self.stats["total_games"] = len(gaps)

        print(f"Target: {self.stats['total_games']:,} games")
        print(
            f"Rate limit: {1/self.config.rate_limit.requests_per_second:.1f}s between requests"
        )
        print()

        # Process each gap
        for i, gap in enumerate(gaps, 1):
            game_id = gap["hoopr_game_id"]
            game_date = gap["game_date"]
            matchup = f"{gap['away_team']} @ {gap['home_team']}"

            # Scrape from hoopR API
            pbp_events = await self.scrape_game_from_hoopr(game_id, game_date)

            if pbp_events is None:
                self.stats["games_no_data"] += 1
                if i % 50 == 0 or i <= 10:
                    self.logger.info(
                        f"  [{i}/{self.stats['total_games']}] ⚠️  No data: {game_id} ({game_date}) - {matchup}"
                    )
                continue

            if not pbp_events:
                self.stats["games_no_data"] += 1
                if i % 50 == 0 or i <= 10:
                    self.logger.info(
                        f"  [{i}/{self.stats['total_games']}] ⚠️  Empty: {game_id} ({game_date}) - {matchup}"
                    )
                continue

            # Load to hoopR database
            loaded = self.load_to_hoopr_database(game_id, pbp_events)

            if loaded > 0:
                self.stats["games_scraped"] += 1
                self.stats["events_loaded"] += loaded

                if i % 50 == 0 or i <= 10:
                    self.logger.info(
                        f"  [{i}/{self.stats['total_games']}] ✓ {game_id} - {loaded:,} events - {matchup}"
                    )
            else:
                self.stats["games_failed"] += 1
                if i % 50 == 0 or i <= 10:
                    self.logger.info(
                        f"  [{i}/{self.stats['total_games']}] ❌ Failed: {game_id} ({game_date}) - {matchup}"
                    )

            # Progress update every 100 games
            if i % 100 == 0:
                pct = i / self.stats["total_games"] * 100
                self.logger.info(
                    f"\n  Progress: {i:,}/{self.stats['total_games']:,} ({pct:.1f}%) | "
                    f"Scraped: {self.stats['games_scraped']:,} | "
                    f"Events: {self.stats['events_loaded']:,}\n"
                )

        # Print summary
        print()
        print("=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print()
        print(f"Total games processed:  {self.stats['total_games']:,}")
        print(f"Games scraped:          {self.stats['games_scraped']:,}")
        print(f"Events loaded:          {self.stats['events_loaded']:,}")
        print(f"Games with no data:     {self.stats['games_no_data']:,}")
        print(f"Games failed:           {self.stats['games_failed']:,}")
        print()

        # Verify hoopR coverage
        self.verify_hoopr_coverage()

        # Sync to RDS if requested
        if self.sync_to_rds and self.stats["games_scraped"] > 0:
            print("=" * 70)
            print("SYNCING TO RDS")
            print("=" * 70)
            print()
            print("⚠️  RDS sync not yet implemented")
            print("   Use: python scripts/db/load_hoopr_to_rds.py")
            print()

        return self.stats["games_scraped"], self.stats["events_loaded"]

    def verify_hoopr_coverage(self):
        """Verify hoopR coverage after gap filling."""
        print("=" * 70)
        print("COVERAGE VERIFICATION")
        print("=" * 70)
        print()

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Count games with PBP
        cursor.execute(
            """
            SELECT COUNT(DISTINCT game_id)
            FROM play_by_play;
        """
        )
        games_with_pbp = cursor.fetchone()[0]

        # Count total events
        cursor.execute("SELECT COUNT(*) FROM play_by_play;")
        total_events = cursor.fetchone()[0]

        # Coverage by year
        cursor.execute(
            """
            SELECT
                CAST(strftime('%Y', game_date) AS INTEGER) as year,
                COUNT(DISTINCT game_id) as games
            FROM play_by_play
            GROUP BY year
            ORDER BY year DESC
            LIMIT 10;
        """
        )

        print(f"hoopR Database Status:")
        print(f"  Games with PBP:  {games_with_pbp:,}")
        print(f"  Total events:    {total_events:,}")
        print()

        print("Recent years:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]:,} games")

        print()
        cursor.close()
        conn.close()

    async def run(self):
        """Main execution (async)."""
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Check sportsdataverse
        if not HAS_SPORTSDATAVERSE:
            print("❌ sportsdataverse not installed")
            sys.exit(1)

        # Load gap list
        gaps = self.load_gap_list()

        if not gaps:
            print("No gaps to fill!")
            return 0, 0

        # Scrape and fill
        games_scraped, events_loaded = await self.scrape_and_fill_gaps(gaps)

        print("=" * 70)
        print(f"✓ Gap filling complete!")
        print(f"  Games scraped: {games_scraped:,}")
        print(f"  Events loaded: {events_loaded:,}")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return games_scraped, events_loaded


async def main_async():
    """Async main function."""
    parser = argparse.ArgumentParser(
        description="Scrape missing hoopR games from hoopR API (AsyncBaseScraper)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all gaps
  python scripts/etl/scrape_missing_hoopr_games.py

  # Test on 10 games
  python scripts/etl/scrape_missing_hoopr_games.py --limit 10

  # Scrape specific year
  python scripts/etl/scrape_missing_hoopr_games.py --year 2003

  # Scrape and sync to RDS
  python scripts/etl/scrape_missing_hoopr_games.py --sync-to-rds

Impact:
  - Fills 2,464 missing games in hoopR
  - Increases coverage: 92.1% → 100%
  - Maintains data integrity (hoopR → hoopR only)
        """,
    )

    parser.add_argument(
        "--limit", type=int, help="Limit number of games to scrape (for testing)"
    )

    parser.add_argument("--year", type=int, help="Scrape only games from specific year")

    parser.add_argument(
        "--sync-to-rds",
        action="store_true",
        help="Also sync filled data to RDS PostgreSQL",
    )

    args = parser.parse_args()

    scraper = HoopRMissingGamesScraper(
        limit=args.limit, year=args.year, sync_to_rds=args.sync_to_rds
    )

    await scraper.run()


def main():
    """Entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

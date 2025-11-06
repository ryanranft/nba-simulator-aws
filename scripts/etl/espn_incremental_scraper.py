#!/usr/bin/env python3
"""
ESPN Incremental Scraper - Daily Updates Only

Migrated to AsyncBaseScraper framework

Purpose: Scrapes only recent ESPN games (last 14 days) and loads to local database
Data Source: ESPN API
Update Frequency: Daily (during season)

Strategy:
1. Query ESPN DB for latest game date
2. Scrape from (latest_date - 14 days) to today
3. Store raw JSON to S3 (new capability)
4. Load games to ESPN local database (preserved)
5. Typically processes 50-100 games during NBA season

Runtime: ~5 minutes during season, <1 minute off-season

Version: 2.0 (Migrated to AsyncBaseScraper)
Created: October 9, 2025
Migrated: October 22, 2025

Features:
- Async HTTP requests with rate limiting (0.5s between requests)
- Automatic retry logic with exponential backoff (new!)
- S3 backup storage (new!)
- SQLite database integration (preserved)
- Telemetry and monitoring

Usage:
    python scripts/etl/espn_incremental_scraper.py
    python scripts/etl/espn_incremental_scraper.py --days-back 7
    python scripts/etl/espn_incremental_scraper.py --dry-run

Configuration:
    See config/scraper_config.yaml - espn_incremental section
"""

import argparse
import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from nba_simulator.etl.config import ScraperConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ESPNIncrementalScraper(AsyncBaseScraper):
    """
    Incremental scraper for ESPN NBA data

    Migrated to AsyncBaseScraper framework for:
    - Async HTTP requests with rate limiting
    - Retry logic with exponential backoff
    - S3 backup storage
    - Telemetry and monitoring

    Also preserves SQLite database integration from original.
    """

    def __init__(self, config, days_back: Optional[int] = None):
        """Initialize incremental scraper with configuration"""
        super().__init__(config)

        # Custom settings from config
        self.days_back = (
            days_back
            if days_back is not None
            else config.custom_settings.get("default_days_back", 14)
        )
        self.db_path = config.custom_settings.get("database_path", "/tmp/espn_local.db")
        self.load_to_database = config.custom_settings.get("load_to_database", True)

        # Endpoint paths
        self.scoreboard_endpoint = config.custom_settings.get("endpoints", {}).get(
            "scoreboard", "/scoreboard"
        )
        self.pbp_endpoint = config.custom_settings.get("endpoints", {}).get(
            "playbyplay", "/playbyplay"
        )

        # Statistics tracking
        self.scrape_stats = {
            "games_found": 0,
            "games_new": 0,
            "games_updated": 0,
            "games_skipped": 0,
            "days_processed": 0,
        }

        logger.info(f"Initialized {self.__class__.__name__}")
        logger.info(f"Days back: {self.days_back}")
        logger.info(f"Database: {self.db_path}")
        logger.info(f"Load to database: {self.load_to_database}")

    def get_latest_game_date(self) -> datetime:
        """Get the latest game date in ESPN database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT MAX(game_date)
                FROM games
                WHERE has_pbp = 1
            """
            )

            latest_date = cursor.fetchone()[0]

            if latest_date:
                return datetime.strptime(latest_date, "%Y-%m-%d")
            else:
                # If no games, start from days_back days ago
                return datetime.now() - timedelta(days=self.days_back)

        except sqlite3.OperationalError:
            # Table doesn't exist yet
            logger.warning(
                "Games table doesn't exist, starting from days_back days ago"
            )
            return datetime.now() - timedelta(days=self.days_back)
        finally:
            cursor.close()
            conn.close()

    async def get_schedule(self, date_str: str) -> Optional[Dict]:
        """Get schedule for a specific date from ESPN API"""
        url = f"{self.config.base_url}{self.scoreboard_endpoint}"
        params = {"dates": date_str, "limit": 100}

        try:
            response = await self.fetch_url(url, params=params)
            if response:
                return await self.parse_json_response(response)
            return None
        except Exception as e:
            logger.error(f"Error fetching schedule for {date_str}: {e}")
            return None

    async def get_play_by_play(self, game_id: str) -> Optional[Dict]:
        """Get play-by-play for a game from ESPN API"""
        url = f"{self.config.base_url}{self.pbp_endpoint}"
        params = {"event": game_id}

        try:
            response = await self.fetch_url(url, params=params)
            if response:
                return await self.parse_json_response(response)
            return None
        except Exception as e:
            logger.error(f"Error fetching PBP for game {game_id}: {e}")
            return None

    def game_exists(self, game_id: str) -> bool:
        """Check if game already exists in database"""
        if not self.load_to_database:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT 1 FROM games WHERE game_id = ?", (game_id,))
            return cursor.fetchone() is not None
        except sqlite3.OperationalError:
            return False
        finally:
            cursor.close()
            conn.close()

    async def load_game_to_db(self, game_data: Dict, pbp_data: Optional[Dict]) -> None:
        """Load game and play-by-play data to ESPN database"""
        if not self.load_to_database:
            return

        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would load game {game_data['game_id']} to database")
            self.scrape_stats["games_new"] += 1
            return

        # Run database operations in thread pool (SQLite is synchronous)
        await asyncio.to_thread(self._load_game_to_db_sync, game_data, pbp_data)

    def _load_game_to_db_sync(self, game_data: Dict, pbp_data: Optional[Dict]) -> None:
        """Synchronous database loading (called from thread pool)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Extract game info
            game_id = game_data["game_id"]
            game_date = game_data["game_date"]
            competitions = game_data.get("competitions", [{}])[0]
            competitors = competitions.get("competitors", [])

            # Get home/away teams
            home_team = None
            away_team = None
            home_score = None
            away_score = None

            for comp in competitors:
                team_info = comp.get("team", {})
                team_name = team_info.get("displayName", "Unknown")
                score = comp.get("score")

                if comp.get("homeAway") == "home":
                    home_team = team_name
                    home_score = int(score) if score else 0
                else:
                    away_team = team_name
                    away_score = int(score) if score else 0

            # Count PBP events
            pbp_event_count = 0
            if pbp_data:
                plays = pbp_data.get("plays", [])
                pbp_event_count = len(plays)

            # Insert or update game
            cursor.execute(
                """
                INSERT OR REPLACE INTO games (
                    game_id, game_date, season, game_type, status,
                    home_team, away_team, home_score, away_score,
                    quarters_played, has_pbp, pbp_event_count,
                    json_file_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
                (
                    game_id,
                    game_date,
                    (
                        int(game_date[:4])
                        if int(game_date[5:7]) >= 10
                        else int(game_date[:4]) + 1
                    ),  # season
                    (
                        competitions.get("type", {}).get("abbreviation", "REG")
                        if competitions
                        else "REG"
                    ),  # game_type
                    game_data.get("status", {})
                    .get("type", {})
                    .get("name", "Final"),  # status
                    home_team,
                    away_team,
                    home_score,
                    away_score,
                    (
                        competitions.get("status", {}).get("period", 4)
                        if competitions
                        else 4
                    ),  # quarters_played
                    1 if pbp_event_count > 0 else 0,
                    pbp_event_count,
                    None,  # json_file_path
                ),
            )

            # Load play-by-play if available
            if pbp_data and pbp_event_count > 0:
                # Clear existing PBP for this game
                cursor.execute("DELETE FROM play_by_play WHERE game_id = ?", (game_id,))

                plays = pbp_data.get("plays", [])
                for play in plays:
                    cursor.execute(
                        """
                        INSERT INTO play_by_play (
                            game_id, sequence_number, period, clock_display,
                            clock_seconds, home_score, away_score,
                            team_id, scoring_play, event_type,
                            description, coordinate_x, coordinate_y,
                            raw_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            game_id,
                            play.get("sequenceNumber"),
                            play.get("period", {}).get("number"),
                            play.get("clock", {}).get("displayValue"),
                            play.get("clock", {}).get("value"),
                            play.get("homeScore"),
                            play.get("awayScore"),
                            play.get("team", {}).get("id"),
                            play.get("scoringPlay", False),
                            play.get("type", {}).get("text"),
                            play.get("text"),
                            play.get("coordinate", {}).get("x"),
                            play.get("coordinate", {}).get("y"),
                            json.dumps(play),
                        ),
                    )

            conn.commit()
            self.scrape_stats["games_new"] += 1

        except Exception as e:
            logger.error(
                f"Error loading game {game_data.get('game_id')} to database: {e}"
            )
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    async def scrape(self) -> None:
        """
        Main scraping method - scrapes recent games and loads to database

        This method is called by AsyncBaseScraper when run.
        """
        print("=" * 70)
        print("ESPN INCREMENTAL SCRAPER")
        print("=" * 70)
        print()

        # Get latest date from database
        latest_date = self.get_latest_game_date()
        start_date = latest_date - timedelta(days=self.days_back)
        end_date = datetime.now()

        total_days = (end_date - start_date).days + 1

        print(f"Database: {self.db_path}")
        print(f"Latest game in DB: {latest_date.strftime('%Y-%m-%d')}")
        print(
            f"Scraping range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({total_days} days)"
        )
        print(
            f"Rate limit: {1/self.config.rate_limit.requests_per_second:.1f}s between requests"
        )
        print(
            f"S3 upload: {'Enabled' if self.config.storage.upload_to_s3 else 'Disabled'}"
        )
        if self.config.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
        print()

        # Scrape each day
        current_date = start_date
        day_count = 0

        while current_date <= end_date:
            day_count += 1
            date_str = current_date.strftime("%Y%m%d")
            date_display = current_date.strftime("%Y-%m-%d")

            print(f"[{day_count}/{total_days}] {date_display}...", end=" ", flush=True)

            # Get schedule for this date
            schedule_data = await self.get_schedule(date_str)
            if not schedule_data:
                print("(error)")
                current_date += timedelta(days=1)
                continue

            # Extract games
            events = schedule_data.get("events", [])
            if not events:
                print("(no games)")
                current_date += timedelta(days=1)
                continue

            print(f"({len(events)} games)")
            self.scrape_stats["games_found"] += len(events)

            # Process each game
            for event in events:
                game_id = event.get("id")
                if not game_id:
                    continue

                # Get game name
                competitions = event.get("competitions", [])
                if competitions:
                    home_abbr = (
                        competitions[0]
                        .get("competitors", [{}])[0]
                        .get("team", {})
                        .get("abbreviation", "UNK")
                    )
                    away_abbr = (
                        competitions[0]
                        .get("competitors", [{}])[1]
                        .get("team", {})
                        .get("abbreviation", "UNK")
                    )
                    game_name = f"{away_abbr} @ {home_abbr}"
                else:
                    game_name = f"Game {game_id}"

                # Check if game exists
                if self.game_exists(game_id) and not self.config.dry_run:
                    print(
                        f"  ⏭️  {game_name} (ID: {game_id}) - already exists, skipping"
                    )
                    self.scrape_stats["games_skipped"] += 1
                    continue

                print(f"  🏀 {game_name} (ID: {game_id})")

                # Get play-by-play
                pbp_data = await self.get_play_by_play(game_id)

                # Prepare game data
                game_data = {
                    "game_id": game_id,
                    "game_date": date_display,
                    "competitions": competitions,
                    "event": event,  # Full event data for S3
                }

                # Store to S3 (new capability)
                if self.config.storage.upload_to_s3 and not self.config.dry_run:
                    combined_data = {
                        "game": game_data,
                        "playbyplay": pbp_data if pbp_data else {},
                    }
                    filename = f"game_{game_id}.json"
                    subdir = f"{date_display[:7]}/{date_display}"  # YYYY-MM/YYYY-MM-DD
                    await self.store_data(combined_data, filename, subdir)

                # Load to database (preserved)
                await self.load_game_to_db(game_data, pbp_data)

            self.scrape_stats["days_processed"] += 1
            current_date += timedelta(days=1)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print scraping summary"""
        print()
        print("=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Days processed:  {self.scrape_stats['days_processed']:,}")
        print(f"Games found:     {self.scrape_stats['games_found']:,}")
        print(f"Games new:       {self.scrape_stats['games_new']:,}")
        print(f"Games skipped:   {self.scrape_stats['games_skipped']:,}")
        print("=" * 70)


async def main():
    """Main entry point for incremental scraper"""
    parser = argparse.ArgumentParser(
        description="ESPN Incremental Scraper - Daily updates only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape last 14 days (default)
  python scripts/etl/espn_incremental_scraper.py

  # Scrape last 7 days
  python scripts/etl/espn_incremental_scraper.py --days-back 7

  # Dry run (don't modify database or upload to S3)
  python scripts/etl/espn_incremental_scraper.py --dry-run

Purpose:
  Designed for nightly automation. Only fetches recent games, NOT historical seasons.
  For historical backfills, use: scripts/etl/scrape_missing_espn_data.py
        """,
    )

    parser.add_argument(
        "--days-back",
        type=int,
        default=None,
        help="Number of days to look back (default: from config, usually 14)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't modify database or upload to S3",
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
    config = config_manager.get_scraper_config("espn_incremental")

    if not config:
        logger.error("Configuration not found for espn_incremental")
        logger.error("Check config/scraper_config.yaml")
        return

    # Override dry_run if specified
    if args.dry_run:
        config.dry_run = True

    # Run scraper
    async with ESPNIncrementalScraper(config, days_back=args.days_back) as scraper:
        await scraper.scrape()

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())

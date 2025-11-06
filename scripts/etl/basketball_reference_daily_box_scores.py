#!/usr/bin/env python3
"""
Basketball Reference Daily Box Score Scraper

Scrapes box scores for games from yesterday (or specified date).
Designed for nightly automation to keep box score database current.

How it works:
1. Get yesterday's date (or user-specified date)
2. Query ESPN/NBA API for games on that date
3. Convert to Basketball Reference game IDs
4. Insert into scraping_progress table (if not already there)
5. Run box score scraper on just those games

Migrated to AsyncBaseScraper framework for:
- Automatic rate limiting for ESPN API calls
- Telemetry and monitoring
- Configuration-driven behavior

Usage:
    # Scrape yesterday's games
    python scripts/etl/basketball_reference_daily_box_scores.py

    # Scrape specific date
    python scripts/etl/basketball_reference_daily_box_scores.py --date 2023-06-12

    # Scrape last N days
    python scripts/etl/basketball_reference_daily_box_scores.py --days 3

    # Dry run (don't scrape, just show what would be scraped)
    python scripts/etl/basketball_reference_daily_box_scores.py --dry-run

Typical usage in overnight workflow:
    - Run daily at 3 AM
    - Scrapes previous day's games
    - Adds to S3 and database
    - Takes ~2-3 minutes for typical game day (10-15 games)

Version: 2.0 (AsyncBaseScraper migration)
Created: October 18, 2025
Migrated: October 22, 2025
"""

import argparse
import sqlite3
import requests
import asyncio
from datetime import datetime, timedelta
import subprocess  # nosec B404 - subprocess needed to call basketball_reference_box_score_scraper.py as coordinator
import sys
from pathlib import Path
from typing import List, Dict

# Import AsyncBaseScraper framework
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.etl.async_scraper_base import AsyncBaseScraper
from nba_simulator.etl.config import ScraperConfigManager


class DailyBoxScoreCoordinator(AsyncBaseScraper):
    """Daily box score coordinator (AsyncBaseScraper)"""

    def __init__(self, config, dry_run: bool = False):
        """Initialize the daily box score coordinator"""
        super().__init__(config)

        # Custom settings from config
        self.db_path = config.custom_settings.get(
            "database_path",
            "/tmp/basketball_reference_boxscores.db",  # nosec B108 - /tmp is fallback default, actual path from config
        )
        self.espn_api_base_url = config.custom_settings.get(
            "espn_api_base_url",
            "https://site.api.espn.com/apis/site/v2/sports/basketball/nba",
        )
        self.dry_run = dry_run
        self.db_conn = None

        # Custom statistics
        self.stats_custom = {
            "games_found": 0,
            "games_inserted": 0,
            "games_already_existed": 0,
            "errors": 0,
        }

    async def scrape(self) -> None:
        """Main scraping method (required by AsyncBaseScraper)"""
        # This method is called by the base class context manager
        # Actual work is done by run() method which is called from main()
        pass

    async def initialize_database(self):
        """Initialize database connection"""
        if self.dry_run:
            return

        self.db_conn = await asyncio.to_thread(sqlite3.connect, self.db_path)
        self.logger.info(f"Connected to database: {self.db_path}")

    def get_yesterday(self) -> str:
        """Get yesterday's date"""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")

    async def get_games_from_espn(self, date_str: str) -> List[Dict]:
        """Get games for a specific date from ESPN API"""
        return await asyncio.to_thread(self._get_games_from_espn_sync, date_str)

    def _get_games_from_espn_sync(self, date_str: str) -> List[Dict]:
        """Synchronous ESPN API call (wrapped by async method)"""
        try:
            # ESPN scoreboard API
            # Date format: YYYYMMDD
            date_formatted = date_str.replace("-", "")
            url = f"{self.espn_api_base_url}/scoreboard?dates={date_formatted}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            games = []
            for event in data.get("events", []):
                # Extract teams
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

    def determine_season(self, date_str: str) -> int:
        """Determine NBA season from date (e.g., '2023-01-15' -> 2023)"""
        date = datetime.strptime(date_str, "%Y-%m-%d")

        # NBA season typically runs Oct-Jun
        # If month is Jul-Sep, it's offseason (use next year's season)
        # If month is Oct-Dec, season = next year
        # If month is Jan-Jun, season = current year

        year = date.year
        month = date.month

        if month >= 10:  # October, November, December
            return year + 1
        elif month <= 6:  # January - June
            return year
        else:  # July, August, September (offseason)
            return year + 1

    async def insert_games_to_progress_table(self, games: List[Dict]) -> None:
        """Insert games into scraping_progress table"""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would insert {len(games)} games:")
            for game in games:
                self.logger.info(
                    f"  {game['game_id']}: {game['away_team']} @ {game['home_team']} on {game['game_date']}"
                )
            return

        if not games:
            self.logger.info("No games to insert")
            return

        await asyncio.to_thread(self._insert_games_sync, games)

    def _insert_games_sync(self, games: List[Dict]) -> None:
        """Synchronous database insert (wrapped by async method)"""
        try:
            cursor = self.db_conn.cursor()

            inserted = 0
            already_exists = 0

            for game in games:
                # Determine season
                season = self.determine_season(game["game_date"])

                # Check if already exists
                cursor.execute(
                    "SELECT game_id FROM scraping_progress WHERE game_id = ?",
                    (game["game_id"],),
                )
                if cursor.fetchone():
                    already_exists += 1
                    self.logger.debug(
                        f"Game {game['game_id']} already in progress table"
                    )
                    continue

                # Insert
                cursor.execute(
                    """
                    INSERT INTO scraping_progress
                    (game_id, game_date, season, home_team, away_team, priority, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """,
                    (
                        game["game_id"],
                        game["game_date"],
                        season,
                        game["home_team"],
                        game["away_team"],
                        1,  # High priority for recent games
                    ),
                )

                inserted += 1
                self.logger.info(
                    f"Added game: {game['game_id']} ({game['away_team']} @ {game['home_team']})"
                )

            self.db_conn.commit()

            self.stats_custom["games_inserted"] = inserted
            self.stats_custom["games_already_existed"] = already_exists

            self.logger.info(
                f"Inserted {inserted} new games, {already_exists} already existed"
            )

        except Exception as e:
            self.logger.error(f"Error inserting games to database: {e}")
            self.stats_custom["errors"] += 1
            raise

    async def run_box_score_scraper(self, max_games: int) -> None:
        """Run the box score scraper on pending games"""
        if self.dry_run:
            self.logger.info(
                f"[DRY RUN] Would run box score scraper on {max_games} games"
            )
            return

        self.logger.info(f"Running box score scraper on up to {max_games} games...")

        try:
            cmd = [
                sys.executable,
                "scripts/etl/basketball_reference_box_score_scraper.py",
                "--max-games",
                str(max_games),
                "--priority",
                "1",  # Only recent games
            ]

            result = await asyncio.to_thread(
                subprocess.run, cmd, check=True, capture_output=True, text=True
            )

            # Log output
            if result.stdout:
                for line in result.stdout.splitlines():
                    self.logger.info(f"  {line}")

            self.logger.info("✓ Box score scraper completed")

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Box score scraper failed: {e}")
            if e.stdout:
                self.logger.error(f"STDOUT: {e.stdout}")
            if e.stderr:
                self.logger.error(f"STDERR: {e.stderr}")
            self.stats_custom["errors"] += 1
            raise

    async def run(self, dates: List[str]) -> None:
        """Run the coordinator for specified dates"""
        print("\n" + "=" * 70)
        print("BASKETBALL REFERENCE DAILY BOX SCORE SCRAPER (AsyncBaseScraper)")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Dry run: {self.dry_run}")
        print(f"Dates: {', '.join(dates)}\n")

        # Initialize database
        await self.initialize_database()

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
            self.logger.info("\n✓ No games to scrape")
            return

        self.stats_custom["games_found"] = len(all_games)
        self.logger.info(f"\nTotal games found: {len(all_games)}")

        # Insert into database
        self.logger.info("\nInserting games into scraping_progress table...")
        await self.insert_games_to_progress_table(all_games)

        # Run box score scraper
        if not self.dry_run:
            self.logger.info("\nRunning box score scraper...")
            await self.run_box_score_scraper(max_games=len(all_games))

        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Games found:         {self.stats_custom['games_found']}")
        print(f"Games inserted:      {self.stats_custom['games_inserted']}")
        print(f"Already existed:     {self.stats_custom['games_already_existed']}")
        print(f"Errors:              {self.stats_custom['errors']}")
        print("=" * 70)

        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async def cleanup(self):
        """Close connections"""
        if self.db_conn:
            await asyncio.to_thread(self.db_conn.close)


async def main():
    parser = argparse.ArgumentParser(
        description="Scrape daily box scores from Basketball Reference"
    )
    parser.add_argument(
        "--date", type=str, help="Date to scrape (YYYY-MM-DD), defaults to yesterday"
    )
    parser.add_argument(
        "--days", type=int, help="Scrape last N days instead of single date"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be scraped without actually scraping",
    )
    parser.add_argument(
        "--config-file",
        default="config/scraper_config.yaml",
        help="Path to scraper configuration file",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config_manager = ScraperConfigManager(args.config_file)
        config = config_manager.get_scraper_config(
            "basketball_reference_daily_box_scores"
        )
        if not config:
            print("❌ Basketball Reference daily box scores configuration not found")
            return 1

        # Override config with command line args
        if args.dry_run:
            config.dry_run = True

        print(f"✅ Loaded Basketball Reference daily box scores configuration")
        print(f"   Database: {config.custom_settings.get('database_path')}")
        print(f"   ESPN API: {config.custom_settings.get('espn_api_base_url')}")
        print(f"   Dry run: {config.dry_run}")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1

    # Create coordinator
    coordinator = DailyBoxScoreCoordinator(config, dry_run=args.dry_run)

    try:
        # Determine dates to scrape
        if args.days:
            dates = []
            for i in range(args.days):
                date = datetime.now() - timedelta(days=i + 1)
                dates.append(date.strftime("%Y-%m-%d"))
            coordinator.logger.info(f"Scraping last {args.days} days: {dates}")
        elif args.date:
            dates = [args.date]
            coordinator.logger.info(f"Scraping specific date: {args.date}")
        else:
            dates = [coordinator.get_yesterday()]
            coordinator.logger.info(f"Scraping yesterday: {dates[0]}")

        # Run coordinator using async context manager
        async with coordinator:
            await coordinator.run(dates=dates)

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
        await coordinator.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

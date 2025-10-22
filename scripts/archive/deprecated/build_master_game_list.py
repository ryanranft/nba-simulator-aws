#!/usr/bin/env python3
"""
Build Master Game List from Basketball Reference

Uses basketball_reference_web_scraper library to fetch all NBA/BAA schedules
from 1946-2025 and build a comprehensive list of every game ID. Populates the
scraping_progress table for the historical backfill scraper.

This script runs ONCE to initialize the database, then the historical
backfill scraper processes each game.

Estimated runtime: 3-5 minutes (79 seasons × 2-4 seconds per season)

Usage:
    python scripts/etl/build_master_game_list.py
    python scripts/etl/build_master_game_list.py --dry-run
    python scripts/etl/build_master_game_list.py --start-season 2020

Output:
    - Populates scraping_progress table with all games
    - Assigns priority (recent games = higher priority)
    - Total: ~70,718 games from 1946-2025

Version: 2.0 (Using basketball_reference_web_scraper library)
Created: October 18, 2025
"""

import argparse
import sqlite3
import time
from datetime import datetime
import logging
from basketball_reference_web_scraper import client

# Configuration
DB_PATH = "/tmp/basketball_reference_boxscores.db"  # nosec B108 - Acceptable for archived deprecated code
RATE_LIMIT = (
    1.0  # 1 second between requests (library handles BB-Ref rate limiting internally)
)

# Priority assignments (1=highest, 10=lowest)
PRIORITY_MAP = {
    (2020, 2025): 1,  # Most recent = highest priority
    (2010, 2020): 2,
    (2000, 2010): 3,
    (1990, 2000): 4,
    (1980, 1990): 5,
    (1970, 1980): 6,
    (1960, 1970): 7,
    (1950, 1960): 8,
    (1946, 1950): 9,  # BAA years = lowest priority
}

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MasterGameListBuilder:
    """Build complete list of all NBA/BAA games from 1946-2025"""

    def __init__(self, start_season=1947, end_season=2025, dry_run=False):
        self.start_season = start_season
        self.end_season = end_season
        self.dry_run = dry_run

        self.db_conn = None if dry_run else sqlite3.connect(DB_PATH)
        self.last_request_time = 0

        # Statistics
        self.stats = {
            "seasons_processed": 0,
            "games_found": 0,
            "games_inserted": 0,
            "errors": 0,
        }

    def rate_limit_wait(self):
        """Enforce 12-second rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT:
            sleep_time = RATE_LIMIT - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get_priority_for_season(self, season):
        """Assign priority based on season year"""
        for (start, end), priority in PRIORITY_MAP.items():
            if start <= season <= end:
                return priority
        return 10  # Default lowest priority

    def get_league_abbr(self, season):
        """Get league abbreviation (BAA or NBA)"""
        if season <= 1949:
            return "BAA"
        return "NBA"

    def scrape_season_schedule(self, season):
        """Scrape all games for a specific season using basketball_reference_web_scraper"""
        league = self.get_league_abbr(season)

        logger.info(
            f"Fetching {league} {season-1}-{season % 100:02d} season schedule..."
        )

        try:
            # Rate limiting
            self.rate_limit_wait()

            # Use library to fetch schedule
            # Note: library uses year for season (e.g., 2024 for 2023-24 season)
            schedule = client.season_schedule(season_end_year=season)

            games = []
            priority = self.get_priority_for_season(season)

            for game in schedule:
                # Extract game info from library's structured data
                # Game format varies but typically has: start_time, home_team, away_team

                # Build game_id from date and home team
                # BB-Ref format: YYYYMMDD0{TEAM_CODE}.html
                game_date = game["start_time"].strftime("%Y-%m-%d")
                date_code = game["start_time"].strftime("%Y%m%d")
                home_code = game["home_team"].name.upper()[
                    :3
                ]  # Team enum to 3-letter code
                game_id = f"{date_code}0{home_code}"

                games.append(
                    {
                        "game_id": game_id,
                        "game_date": game_date,
                        "season": season,
                        "home_team": game["home_team"].value,
                        "away_team": game["away_team"].value,
                        "priority": priority,
                    }
                )

            logger.info(f"  Found {len(games)} games")
            self.stats["games_found"] += len(games)

            return games

        except Exception as e:
            logger.error(f"Error fetching schedule for {season}: {e}")
            self.stats["errors"] += 1
            return []

    def insert_games(self, games):
        """Insert games into scraping_progress table"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would insert {len(games)} games")
            return

        cursor = self.db_conn.cursor()

        for game in games:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO scraping_progress
                    (game_id, game_date, season, home_team, away_team, priority, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """,
                    (
                        game["game_id"],
                        game["game_date"],
                        game["season"],
                        game["home_team"],
                        game["away_team"],
                        game["priority"],
                    ),
                )
                self.stats["games_inserted"] += cursor.rowcount
            except Exception as e:
                logger.error(f"Error inserting game {game['game_id']}: {e}")
                self.stats["errors"] += 1

        self.db_conn.commit()

    def run(self):
        """Build master game list for all seasons"""
        print("\n" + "=" * 70)
        print("BASKETBALL REFERENCE MASTER GAME LIST BUILDER")
        print("=" * 70)
        print(f"\nSeasons: {self.start_season} to {self.end_season}")
        print(f"Database: {DB_PATH}")
        print(f"Dry run: {self.dry_run}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Process each season
        for season in range(self.start_season, self.end_season + 1):
            games = self.scrape_season_schedule(season)

            if games:
                self.insert_games(games)
                self.stats["seasons_processed"] += 1

            # Progress update every 10 seasons
            if season % 10 == 0:
                logger.info(
                    f"Progress: {season - self.start_season + 1}/{self.end_season - self.start_season + 1} seasons"
                )

        # Final summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Seasons processed:  {self.stats['seasons_processed']}")
        print(f"Games found:        {self.stats['games_found']:,}")
        print(f"Games inserted:     {self.stats['games_inserted']:,}")
        print(f"Errors:             {self.stats['errors']}")
        print("=" * 70)

        if not self.dry_run:
            # Query database for verification
            cursor = self.db_conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM scraping_progress")
            total_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM scraping_progress WHERE status = 'pending'"
            )
            pending_count = cursor.fetchone()[0]

            cursor.execute(
                "SELECT MIN(game_date), MAX(game_date) FROM scraping_progress"
            )
            date_range = cursor.fetchone()

            print(f"\nDatabase Status:")
            print(f"  Total games:      {total_count:,}")
            print(f"  Pending scrape:   {pending_count:,}")
            print(f"  Date range:       {date_range[0]} to {date_range[1]}")

            # Games by priority
            cursor.execute(
                """
                SELECT priority, COUNT(*) as count
                FROM scraping_progress
                GROUP BY priority
                ORDER BY priority
            """
            )
            print(f"\nGames by priority:")
            for priority, count in cursor.fetchall():
                print(f"  Priority {priority}: {count:,} games")

        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def cleanup(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build master game list from Basketball Reference"
    )
    parser.add_argument(
        "--start-season",
        type=int,
        default=1947,
        help="Starting season (default: 1947 for BAA first season)",
    )
    parser.add_argument(
        "--end-season", type=int, default=2025, help="Ending season (default: 2025)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Test mode - don't insert into database"
    )

    args = parser.parse_args()

    builder = MasterGameListBuilder(
        start_season=args.start_season, end_season=args.end_season, dry_run=args.dry_run
    )

    try:
        builder.run()
    finally:
        builder.cleanup()


if __name__ == "__main__":
    main()

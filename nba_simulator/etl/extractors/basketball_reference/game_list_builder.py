#!/usr/bin/env python3
"""
Build Master Game List from Basketball Reference - Robust Version

Uses direct HTML parsing to handle all years from 1946-2025, including
historical teams that the basketball_reference_web_scraper library doesn't support.

This version:
- Parses Basketball Reference schedule pages directly
- Handles BAA (1946-1949) and NBA (1949-2025)
- Extracts game IDs from box score links
- Works with defunct franchises and historical team names

Estimated runtime: 15-20 minutes (79 seasons × 12s per request)

Usage:
    python scripts/etl/build_master_game_list_robust.py
    python scripts/etl/build_master_game_list_robust.py --dry-run
    python scripts/etl/build_master_game_list_robust.py --start-season 2020
    python scripts/etl/build_master_game_list_robust.py --start-season 1947 --end-season 1950

Output:
    - Populates scraping_progress table with all games
    - Assigns priority (recent games = higher priority)
    - Total: ~70,718 games from 1946-2025

Version: 3.0 (Robust HTML parsing)
Created: October 18, 2025

Migrated to AsyncBaseScraper framework.
Version: 2.0 (AsyncBaseScraper Integration - Preserve Mode)
Migrated: October 22, 2025
"""


# TODO: AsyncBaseScraper Integration
# 1. Make your main class inherit from AsyncBaseScraper
# 2. Add config_name parameter to __init__
# 3. Call super().__init__(config_name=config_name)
# 4. Wrap synchronous HTTP calls in asyncio.to_thread()
# 5. Use self.rate_limiter.acquire() before requests
# 6. Use self.store_data() for S3 uploads
#
# Uncomment these imports when ready:
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# from scripts.etl.async_scraper_base import AsyncBaseScraper

import argparse
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime
import logging
import re

# Configuration
DB_PATH = "/tmp/basketball_reference_boxscores.db"
BASE_URL = "https://www.basketball-reference.com"
RATE_LIMIT = 12.0  # 12 seconds between requests (Basketball Reference requirement)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

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
    (1946, 1950): 9,  # BAA years
}

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MasterGameListBuilder:

    # TODO: After inheriting from AsyncBaseScraper:
    # - Add config_name parameter to __init__
    # - Call super().__init__(config_name='build_master_game_list_robust')

    """Build complete list of all NBA/BAA games from 1946-2025 using HTML parsing"""

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
            "invalid_games": 0,
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

    def extract_game_id_from_url(self, url):
        """Extract game ID from Basketball Reference box score URL"""
        # URL format: /boxscores/194611010TRH.html
        # Game ID: 194611010TRH
        if not url:
            return None

        match = re.search(r"/boxscores/([A-Z0-9]+)\.html", url)
        if match:
            return match.group(1)

        return None

    def parse_date_from_game_id(self, game_id):
        """Parse date from game ID (format: YYYYMMDD0XXX)"""
        if not game_id or len(game_id) < 8:
            return None

        try:
            date_str = game_id[:8]
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:8]
            return f"{year}-{month}-{day}"
        except:
            return None

    def scrape_month_schedule(self, season, month_name=None):
        """Scrape games for a specific month (or main schedule if month_name is None)"""
        league = self.get_league_abbr(season)

        if month_name:
            url = f"{BASE_URL}/leagues/{league}_{season}_games-{month_name}.html"
        else:
            url = f"{BASE_URL}/leagues/{league}_{season}_games.html"

        try:
            # Rate limiting
            self.rate_limit_wait()

            # Fetch page
            response = requests.get(url, headers=HEADERS, timeout=30)

            # If month page doesn't exist (404), return empty list
            if response.status_code == 404:
                logger.debug(f"  Month page not found: {month_name}")
                return []

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Find ALL schedule tables
            all_tables = soup.find_all("table", {"class": "stats_table"})

            if not all_tables:
                return []

            games = []

            # Parse all tables
            for table in all_tables:
                tbody = table.find("tbody")
                if not tbody:
                    continue

                rows = tbody.find_all("tr")

                for row in rows:
                    # Skip header rows
                    if row.get("class") and "thead" in row.get("class"):
                        continue

                    # Find box score link
                    box_score_link = row.find("td", {"data-stat": "box_score_text"})
                    if not box_score_link:
                        continue

                    link = box_score_link.find("a")
                    if not link or not link.get("href"):
                        continue

                    # Extract game ID
                    game_id = self.extract_game_id_from_url(link["href"])
                    if not game_id:
                        self.stats["invalid_games"] += 1
                        continue

                    # Parse date from game ID
                    game_date = self.parse_date_from_game_id(game_id)
                    if not game_date:
                        logger.warning(f"Could not parse date from game_id: {game_id}")
                        self.stats["invalid_games"] += 1
                        continue

                    # Extract teams
                    visitor_team_cell = row.find(
                        "td", {"data-stat": "visitor_team_name"}
                    )
                    home_team_cell = row.find("td", {"data-stat": "home_team_name"})

                    if not visitor_team_cell or not home_team_cell:
                        self.stats["invalid_games"] += 1
                        continue

                    # Get team codes from links
                    visitor_link = visitor_team_cell.find("a")
                    home_link = home_team_cell.find("a")

                    if visitor_link and home_link:
                        visitor_href = visitor_link.get("href", "")
                        home_href = home_link.get("href", "")

                        visitor_match = re.search(r"/teams/([A-Z]{3})/", visitor_href)
                        home_match = re.search(r"/teams/([A-Z]{3})/", home_href)

                        if visitor_match and home_match:
                            away_team = visitor_match.group(1)
                            home_team = home_match.group(1)
                        else:
                            away_team = visitor_team_cell.text.strip()[:3].upper()
                            home_team = home_team_cell.text.strip()[:3].upper()
                    else:
                        away_team = visitor_team_cell.text.strip()[:3].upper()
                        home_team = home_team_cell.text.strip()[:3].upper()

                    games.append(
                        {
                            "game_id": game_id,
                            "game_date": game_date,
                            "home_team": home_team,
                            "away_team": away_team,
                        }
                    )

            return games

        except requests.exceptions.RequestException as e:
            if "404" not in str(e):
                logger.error(f"HTTP error fetching {url}: {e}")
                self.stats["errors"] += 1
            return []
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            self.stats["errors"] += 1
            return []

    def scrape_season_schedule(self, season):
        """Scrape all games for a specific season by trying all month pages"""
        league = self.get_league_abbr(season)
        logger.info(f"Scraping {league} {season-1}-{str(season)[-2:]} season...")

        priority = self.get_priority_for_season(season)
        all_games = []
        seen_game_ids = set()

        # Month names used by Basketball Reference
        months = [
            "october",
            "november",
            "december",
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
        ]

        # Try main schedule page first (catches games if no month pages exist)
        logger.info(f"  Checking main schedule page...")
        main_games = self.scrape_month_schedule(season, month_name=None)
        for game in main_games:
            if game["game_id"] not in seen_game_ids:
                game["season"] = season
                game["priority"] = priority
                all_games.append(game)
                seen_game_ids.add(game["game_id"])

        logger.info(f"  Found {len(main_games)} games on main page")

        # Try each month page
        for month in months:
            month_games = self.scrape_month_schedule(season, month_name=month)

            if month_games:
                new_games = 0
                for game in month_games:
                    if game["game_id"] not in seen_game_ids:
                        game["season"] = season
                        game["priority"] = priority
                        all_games.append(game)
                        seen_game_ids.add(game["game_id"])
                        new_games += 1

                if new_games > 0:
                    logger.info(f"  {month.capitalize()}: +{new_games} games")

        logger.info(f"  ✓ Total: {len(all_games)} unique games for {season}")
        self.stats["games_found"] += len(all_games)

        return all_games

    def insert_games(self, games):
        """Insert games into scraping_progress table"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would insert {len(games)} games")
            return

        if not games:
            return

        cursor = self.db_conn.cursor()
        inserted = 0

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
                if cursor.rowcount > 0:
                    inserted += 1
            except Exception as e:
                logger.error(f"Error inserting game {game['game_id']}: {e}")
                self.stats["errors"] += 1

        self.db_conn.commit()
        self.stats["games_inserted"] += inserted
        logger.info(f"  → Inserted {inserted} new games into database")

    def run(self):
        """Build master game list for all seasons"""
        print("\n" + "=" * 70)
        print("BASKETBALL REFERENCE MASTER GAME LIST BUILDER (ROBUST)")
        print("=" * 70)
        print(f"\nSeasons: {self.start_season} to {self.end_season}")
        print(f"Database: {DB_PATH}")
        print(f"Dry run: {self.dry_run}")
        print(f"Rate limit: {RATE_LIMIT}s between requests")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        total_seasons = self.end_season - self.start_season + 1
        estimated_time_minutes = (total_seasons * RATE_LIMIT) / 60

        print(
            f"Estimated time: {estimated_time_minutes:.1f} minutes "
            f"({total_seasons} seasons × {RATE_LIMIT}s)\n"
        )

        # Process each season
        for idx, season in enumerate(range(self.start_season, self.end_season + 1), 1):
            games = self.scrape_season_schedule(season)

            if games:
                self.insert_games(games)
                self.stats["seasons_processed"] += 1

            # Progress update
            if idx % 10 == 0 or idx == total_seasons:
                elapsed = (
                    time.time() - self.last_request_time + (idx * RATE_LIMIT)
                ) / 60
                remaining = total_seasons - idx
                eta = (remaining * RATE_LIMIT) / 60
                logger.info(
                    f"\n=== Progress: {idx}/{total_seasons} seasons "
                    f"({100*idx/total_seasons:.1f}%), "
                    f"ETA: {eta:.1f} min ===\n"
                )

        # Final summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Seasons processed:  {self.stats['seasons_processed']}/{total_seasons}")
        print(f"Games found:        {self.stats['games_found']:,}")
        print(f"Games inserted:     {self.stats['games_inserted']:,}")
        print(f"Invalid games:      {self.stats['invalid_games']:,}")
        print(f"Errors:             {self.stats['errors']}")
        print("=" * 70)

        if not self.dry_run and self.db_conn:
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
            if date_range[0]:
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

            # Games by decade
            cursor.execute(
                """
                SELECT
                    CAST(season/10*10 AS INTEGER) as decade,
                    COUNT(*) as count
                FROM scraping_progress
                GROUP BY decade
                ORDER BY decade
            """
            )
            print(f"\nGames by decade:")
            for decade, count in cursor.fetchall():
                print(f"  {decade}s: {count:,} games")

        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def cleanup(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build master game list from Basketball Reference (robust HTML parsing)"
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

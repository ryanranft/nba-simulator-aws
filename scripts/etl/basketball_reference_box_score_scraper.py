#!/usr/bin/env python3
"""
Basketball Reference Box Score Historical Scraper

Migrated to AsyncBaseScraper framework

Scrapes individual box score pages for games in the scraping_progress table.
Extracts all available data and loads into database + S3.

Features:
- AsyncBaseScraper framework for standardized infrastructure
- Resume capability (picks up where it left off)
- Priority-based processing (recent games first)
- Extracts: basic stats, advanced stats, four factors, play-by-play
- Uploads raw JSON to S3
- Updates scraping_progress table
- Error handling with retry logic
- Telemetry and monitoring

Usage:
    python scripts/etl/basketball_reference_box_score_scraper.py
    python scripts/etl/basketball_reference_box_score_scraper.py --max-games 100
    python scripts/etl/basketball_reference_box_score_scraper.py --priority 1
    python scripts/etl/basketball_reference_box_score_scraper.py --dry-run

Estimated Runtime:
    - Per game: ~12 seconds (rate limit)
    - 100 games: ~20 minutes
    - 1,000 games: ~3.3 hours
    - 10,000 games: ~1.4 days
    - 70,718 games: ~10 days

Version: 2.0 (Migrated to AsyncBaseScraper)
Created: October 18, 2025
Migrated: October 22, 2025 (Session 4)
"""

import asyncio
import argparse
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BoxScoreScraper(AsyncBaseScraper):
    """
    Scrape individual box score pages from Basketball Reference

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
            "database_path", "/tmp/basketball_reference_boxscores.db"
        )
        self.load_to_database = config.custom_settings.get("load_to_database", True)
        self.upload_to_s3 = upload_to_s3 if not dry_run else False
        self.dry_run = dry_run

        # Database connection (None if dry run)
        self.db_conn = None if dry_run else sqlite3.connect(self.db_path)

        # Statistics
        self.stats_custom = {
            "games_scraped": 0,
            "games_failed": 0,
            "games_skipped": 0,
            "uploaded_to_s3": 0,
            "errors": 0,
        }

    async def scrape(self) -> None:
        """Main scraping method (required by AsyncBaseScraper)"""
        # This method is called by the base class context manager
        # Actual scraping is done by run() method which is called from main()
        pass

    async def get_pending_games(
        self, max_games: Optional[int] = None, priority: Optional[int] = None
    ) -> List[Dict]:
        """Get games that need to be scraped from scraping_progress table"""
        if self.dry_run:
            # Return dummy data for testing
            return [
                {
                    "game_id": "202306120DEN",
                    "game_date": "2023-06-12",
                    "season": 2023,
                    "home_team": "DEN",
                    "away_team": "MIA",
                    "priority": 1,
                }
            ]

        # Wrap synchronous database operation in asyncio.to_thread
        return await asyncio.to_thread(
            self._get_pending_games_sync, max_games, priority
        )

    def _get_pending_games_sync(
        self, max_games: Optional[int], priority: Optional[int]
    ) -> List[Dict]:
        """Synchronous version of get_pending_games (wrapped by async version)"""
        cursor = self.db_conn.cursor()

        # Build query
        query = """
            SELECT game_id, game_date, season, home_team, away_team, priority
            FROM scraping_progress
            WHERE status = 'pending'
            AND attempts < max_attempts
        """

        params = []

        if priority is not None:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY priority ASC, game_date DESC"

        if max_games:
            query += " LIMIT ?"
            params.append(max_games)

        cursor.execute(query, params)

        games = []
        for row in cursor.fetchall():
            games.append(
                {
                    "game_id": row[0],
                    "game_date": row[1],
                    "season": row[2],
                    "home_team": row[3],
                    "away_team": row[4],
                    "priority": row[5],
                }
            )

        return games

    async def fetch_box_score_page(self, game_id: str) -> Optional[str]:
        """Fetch raw HTML for a box score page"""
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
            response.raise_for_status()

            return response.text

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                self.logger.warning(f"Game not found: {game_id}")
            elif e.response.status_code == 429:
                self.logger.warning(f"Rate limited on {game_id}")
            else:
                self.logger.error(f"HTTP error fetching {game_id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching {game_id}: {e}")
            return None

    async def parse_box_score(self, html: str, game_id: str) -> Dict:
        """Parse box score HTML and extract all available data"""
        # Wrap synchronous BeautifulSoup parsing in asyncio.to_thread
        return await asyncio.to_thread(self._parse_box_score_sync, html, game_id)

    def _parse_box_score_sync(self, html: str, game_id: str) -> Dict:
        """Synchronous version of parse_box_score (wrapped by async version)"""
        soup = BeautifulSoup(html, "html.parser")

        data = {
            "game_id": game_id,
            "scraped_at": datetime.utcnow().isoformat(),
            "game_info": {},
            "team_stats": [],
            "player_stats": [],
            "play_by_play": [],
        }

        # Extract game metadata
        data["game_info"] = self._parse_game_info(soup, game_id)

        # Extract team box scores
        data["team_stats"] = self._parse_team_stats(soup)

        # Extract player box scores
        data["player_stats"] = self._parse_player_stats(soup)

        # Extract play-by-play (if available)
        data["play_by_play"] = self._parse_play_by_play(soup)

        return data

    def _parse_game_info(self, soup: BeautifulSoup, game_id: str) -> Dict:
        """Extract game metadata from scorebox"""
        info = {}

        try:
            # Find scorebox
            scorebox = soup.find("div", {"class": "scorebox"})
            if not scorebox:
                return info

            # Extract scores
            scores = scorebox.find_all("div", {"class": "score"})
            if len(scores) >= 2:
                info["away_score"] = int(scores[0].text.strip())
                info["home_score"] = int(scores[1].text.strip())

            # Extract team names
            teams = scorebox.find_all("strong")
            if len(teams) >= 2:
                info["away_team_name"] = teams[0].text.strip()
                info["home_team_name"] = teams[1].text.strip()

            # Extract date
            scorebox_meta = soup.find("div", {"class": "scorebox_meta"})
            if scorebox_meta:
                divs = scorebox_meta.find_all("div")
                for div in divs:
                    text = div.get_text()
                    # Look for date pattern
                    if "," in text and any(
                        month in text
                        for month in [
                            "January",
                            "February",
                            "March",
                            "April",
                            "May",
                            "June",
                            "July",
                            "August",
                            "September",
                            "October",
                            "November",
                            "December",
                        ]
                    ):
                        info["game_date_full"] = text.strip()

                    # Look for location
                    if "Arena" in text or "Center" in text or "Garden" in text:
                        info["location"] = text.strip()

                    # Look for attendance
                    attendance_match = re.search(r"Attendance:\s*([\d,]+)", text)
                    if attendance_match:
                        info["attendance"] = int(
                            attendance_match.group(1).replace(",", "")
                        )

        except Exception as e:
            self.logger.warning(f"Error parsing game info for {game_id}: {e}")

        return info

    def _parse_team_stats(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract team-level statistics"""
        teams = []

        try:
            # Find team stats tables (usually bottom of page)
            team_tables = soup.find_all("table", {"id": re.compile(r".*team.*stats.*")})

            for table in team_tables:
                team_data = {}

                # Extract team from table ID
                table_id = table.get("id", "")
                # Parse team abbreviation from ID (e.g., 'box-DEN-team-stats' -> 'DEN')
                team_match = re.search(r"box-([A-Z]{3})-", table_id)
                if team_match:
                    team_data["team"] = team_match.group(1)

                # Extract stats from footer (team totals)
                tfoot = table.find("tfoot")
                if tfoot:
                    row = tfoot.find("tr")
                    if row:
                        # Parse all stat columns
                        for cell in row.find_all(["td", "th"]):
                            stat_name = cell.get("data-stat")
                            if stat_name and stat_name != "player":
                                team_data[stat_name] = cell.text.strip()

                if team_data:
                    teams.append(team_data)

        except Exception as e:
            self.logger.warning(f"Error parsing team stats: {e}")

        return teams

    def _parse_player_stats(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract player-level statistics"""
        players = []

        try:
            # Find basic box score tables
            player_tables = soup.find_all(
                "table", {"id": re.compile(r"box-.*-game-basic")}
            )

            for table in player_tables:
                # Extract team from table ID
                table_id = table.get("id", "")
                team_match = re.search(r"box-([A-Z]{3})-", table_id)
                team = team_match.group(1) if team_match else None

                tbody = table.find("tbody")
                if not tbody:
                    continue

                rows = tbody.find_all("tr")

                for row in rows:
                    # Skip if not a player row
                    if row.get("class") and "thead" in row.get("class"):
                        continue

                    player_data = {"team": team}

                    # Extract all stats
                    for cell in row.find_all(["th", "td"]):
                        stat_name = cell.get("data-stat")
                        if stat_name:
                            value = cell.text.strip()

                            # Special handling for player name (contains link)
                            if stat_name == "player":
                                link = cell.find("a")
                                if link:
                                    player_data["player_name"] = link.text.strip()
                                    player_data["player_slug"] = (
                                        link.get("href", "")
                                        .split("/")[-1]
                                        .replace(".html", "")
                                    )
                                else:
                                    player_data["player_name"] = value
                            else:
                                player_data[stat_name] = value

                    if player_data.get("player_name"):
                        players.append(player_data)

        except Exception as e:
            self.logger.warning(f"Error parsing player stats: {e}")

        return players

    def _parse_play_by_play(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract play-by-play data (if available)"""
        pbp_events = []

        try:
            # Find play-by-play table
            pbp_table = soup.find("table", {"id": "pbp"})
            if not pbp_table:
                return pbp_events

            tbody = pbp_table.find("tbody")
            if not tbody:
                return pbp_events

            rows = tbody.find_all("tr")

            for row in rows:
                # Skip quarter headers
                if row.get("class") and "thead" in row.get("class"):
                    continue

                event = {}

                # Extract all cells
                cells = row.find_all(["th", "td"])
                for cell in cells:
                    stat_name = cell.get("data-stat")
                    if stat_name:
                        event[stat_name] = cell.text.strip()

                if event:
                    pbp_events.append(event)

        except Exception as e:
            self.logger.warning(f"Error parsing play-by-play: {e}")

        return pbp_events

    async def upload_to_s3_bucket(self, game_id: str, data: Dict) -> bool:
        """Upload raw JSON to S3 using base class store_data() method"""
        if self.dry_run or not self.upload_to_s3:
            self.logger.info(f"[DRY RUN] Would upload {game_id} to S3")
            return True

        try:
            # Extract year from game_id (YYYYMMDD...)
            year = game_id[:4]

            # Filename: basketball_reference/box_scores/YYYY/game_id.json
            filename = f"{year}/{game_id}.json"

            # Use base class store_data() method
            success = await self.store_data(data, filename, "box_scores")

            if success:
                self.stats_custom["uploaded_to_s3"] += 1

            return success

        except Exception as e:
            self.logger.error(f"Error uploading {game_id} to S3: {e}")
            return False

    async def load_to_database_async(self, data: Dict) -> bool:
        """Load structured data into SQLite database (async wrapper)"""
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would load {data['game_id']} to database")
            return True

        # Wrap synchronous database operations in asyncio.to_thread
        return await asyncio.to_thread(self._load_to_database_sync, data)

    def _load_to_database_sync(self, data: Dict) -> bool:
        """Synchronous version of load_to_database (wrapped by async version)"""
        try:
            cursor = self.db_conn.cursor()

            # Insert game record
            game_info = data["game_info"]
            cursor.execute(
                """
                INSERT OR REPLACE INTO games
                (game_id, game_date, season, home_team, away_team,
                 home_score, away_score, home_team_name, away_team_name,
                 location, attendance, scraped_at, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data["game_id"],
                    game_info.get("game_date"),
                    data.get("season"),
                    data.get("home_team"),
                    data.get("away_team"),
                    game_info.get("home_score"),
                    game_info.get("away_score"),
                    game_info.get("home_team_name"),
                    game_info.get("away_team_name"),
                    game_info.get("location"),
                    game_info.get("attendance"),
                    data["scraped_at"],
                    f"{self.config.base_url}/boxscores/{data['game_id']}.html",
                ),
            )

            # Stat mapping for consistent column names
            stat_mapping = {
                "fg": "field_goals_made",
                "fga": "field_goals_attempted",
                "fg_pct": "field_goal_pct",
                "fg3": "three_pointers_made",
                "fg3a": "three_pointers_attempted",
                "fg3_pct": "three_point_pct",
                "ft": "free_throws_made",
                "fta": "free_throws_attempted",
                "ft_pct": "free_throw_pct",
                "orb": "offensive_rebounds",
                "drb": "defensive_rebounds",
                "trb": "total_rebounds",
                "ast": "assists",
                "stl": "steals",
                "blk": "blocks",
                "tov": "turnovers",
                "pf": "personal_fouls",
                "pts": "points",
            }

            # Insert team stats
            for team_stat in data["team_stats"]:
                # Build dynamic INSERT based on available stats
                columns = ["game_id", "team"]
                values = [data["game_id"], team_stat.get("team")]

                for stat_name, col_name in stat_mapping.items():
                    if stat_name in team_stat:
                        columns.append(col_name)
                        values.append(team_stat[stat_name])

                # Build and execute INSERT
                placeholders = ",".join(["?" for _ in values])
                query = f"INSERT OR REPLACE INTO team_box_scores ({','.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)

            # Insert player stats
            for player_stat in data["player_stats"]:
                # Similar dynamic INSERT for players
                columns = ["game_id", "player_name", "team"]
                values = [
                    data["game_id"],
                    player_stat.get("player_name"),
                    player_stat.get("team"),
                ]

                # Add available stats
                if "player_slug" in player_stat:
                    columns.append("player_slug")
                    values.append(player_stat["player_slug"])

                # Map stats
                for stat_name, col_name in stat_mapping.items():
                    if stat_name in player_stat:
                        columns.append(col_name)
                        values.append(player_stat[stat_name])

                # Build and execute INSERT
                placeholders = ",".join(["?" for _ in values])
                query = f"INSERT OR REPLACE INTO player_box_scores ({','.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)

            self.db_conn.commit()
            return True

        except Exception as e:
            self.logger.error(f"Database insert failed for {data['game_id']}: {e}")
            import traceback

            self.logger.debug(traceback.format_exc())
            return False

    async def update_scraping_progress(
        self, game_id: str, status: str, error_msg: Optional[str] = None
    ):
        """Update scraping_progress table (async wrapper)"""
        if self.dry_run:
            return

        # Wrap synchronous database operation in asyncio.to_thread
        await asyncio.to_thread(
            self._update_scraping_progress_sync, game_id, status, error_msg
        )

    def _update_scraping_progress_sync(
        self, game_id: str, status: str, error_msg: Optional[str]
    ):
        """Synchronous version of update_scraping_progress (wrapped by async version)"""
        try:
            cursor = self.db_conn.cursor()

            if status == "scraped":
                cursor.execute(
                    """
                    UPDATE scraping_progress
                    SET status = 'scraped',
                        scraped_at = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE game_id = ?
                """,
                    (datetime.utcnow().isoformat(), game_id),
                )
            else:  # failed
                cursor.execute(
                    """
                    UPDATE scraping_progress
                    SET attempts = attempts + 1,
                        last_attempt_at = ?,
                        last_error = ?,
                        status = CASE WHEN attempts + 1 >= max_attempts THEN 'failed' ELSE status END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE game_id = ?
                """,
                    (datetime.utcnow().isoformat(), error_msg, game_id),
                )

            self.db_conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating progress for {game_id}: {e}")

    async def scrape_game(self, game: Dict) -> bool:
        """Scrape a single game"""
        game_id = game["game_id"]

        self.logger.info(
            f"Scraping {game_id} ({game['game_date']}) - {game['away_team']} @ {game['home_team']}"
        )

        try:
            # Fetch HTML
            html = await self.fetch_box_score_page(game_id)
            if not html:
                await self.update_scraping_progress(
                    game_id, "failed", "Failed to fetch page"
                )
                self.stats_custom["games_failed"] += 1
                return False

            # Parse data
            data = await self.parse_box_score(html, game_id)
            data["season"] = game["season"]
            data["home_team"] = game["home_team"]
            data["away_team"] = game["away_team"]
            data["game_date"] = game["game_date"]

            # Upload to S3
            if self.upload_to_s3:
                s3_success = await self.upload_to_s3_bucket(game_id, data)
                if not s3_success:
                    self.logger.warning(
                        f"S3 upload failed for {game_id}, continuing anyway"
                    )

            # Load to database
            if self.load_to_database:
                db_success = await self.load_to_database_async(data)
                if not db_success:
                    await self.update_scraping_progress(
                        game_id, "failed", "Database insert failed"
                    )
                    self.stats_custom["games_failed"] += 1
                    return False

            # Mark as scraped
            await self.update_scraping_progress(game_id, "scraped")
            self.stats_custom["games_scraped"] += 1

            self.logger.info(f"  ✓ Successfully scraped {game_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error scraping {game_id}: {e}")
            await self.update_scraping_progress(game_id, "failed", str(e))
            self.stats_custom["games_failed"] += 1
            self.stats_custom["errors"] += 1
            return False

    async def run(
        self, max_games: Optional[int] = None, priority: Optional[int] = None
    ):
        """Run the scraper"""
        print("\n" + "=" * 70)
        print("BASKETBALL REFERENCE BOX SCORE SCRAPER (AsyncBaseScraper)")
        print("=" * 70)
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Dry run: {self.dry_run}")
        print(f"Upload to S3: {self.upload_to_s3}")
        if max_games:
            print(f"Max games: {max_games}")
        if priority:
            print(f"Priority filter: {priority}")
        print()

        # Get pending games
        pending_games = await self.get_pending_games(
            max_games=max_games, priority=priority
        )

        if not pending_games:
            print("No pending games found!")
            return

        total_games = len(pending_games)
        print(f"Found {total_games} pending games\n")

        # Estimated time based on rate limit (12 seconds per game)
        rate_limit_seconds = 12.0
        estimated_time_hours = (total_games * rate_limit_seconds) / 3600
        print(
            f"Estimated time: {estimated_time_hours:.1f} hours ({total_games} games × {rate_limit_seconds}s)\n"
        )

        # Process each game
        for idx, game in enumerate(pending_games, 1):
            await self.scrape_game(game)

            # Progress update
            if idx % 10 == 0 or idx == total_games:
                elapsed_hours = (idx * rate_limit_seconds) / 3600
                remaining = total_games - idx
                eta_hours = (remaining * rate_limit_seconds) / 3600

                print(f"\n{'='*70}")
                print(f"Progress: {idx}/{total_games} ({100*idx/total_games:.1f}%)")
                print(f"Elapsed: {elapsed_hours:.1f}h, ETA: {eta_hours:.1f}h")
                print(
                    f"Success: {self.stats_custom['games_scraped']}, Failed: {self.stats_custom['games_failed']}"
                )
                print(f"{'='*70}\n")

        # Final summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Games scraped:   {self.stats_custom['games_scraped']}")
        print(f"Games failed:    {self.stats_custom['games_failed']}")
        print(f"Uploaded to S3:  {self.stats_custom['uploaded_to_s3']}")
        print(f"Errors:          {self.stats_custom['errors']}")
        print("=" * 70)
        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def cleanup(self):
        """Close connections"""
        if self.db_conn:
            self.db_conn.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Scrape Basketball Reference box scores (AsyncBaseScraper)"
    )
    parser.add_argument(
        "--max-games", type=int, help="Maximum number of games to scrape"
    )
    parser.add_argument(
        "--priority", type=int, help="Only scrape games with this priority (1-9)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - don't insert into database or upload to S3",
    )
    parser.add_argument(
        "--no-s3", action="store_true", help="Don't upload to S3 (database only)"
    )
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
        config = config_manager.get_scraper_config("basketball_reference_box_scores")
        if not config:
            print("❌ Basketball Reference box scores configuration not found")
            return 1

        # Override config with command line args
        if args.dry_run:
            config.dry_run = True

        print(f"✅ Loaded Basketball Reference box scores configuration")
        print(f"   Base URL: {config.base_url}")
        print(
            f"   Rate limit: {config.rate_limit.requests_per_second} req/s (12s between requests)"
        )
        print(f"   Max concurrent: {config.max_concurrent}")
        print(f"   Dry run: {config.dry_run}")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return 1

    # Create scraper
    scraper = BoxScoreScraper(config, dry_run=args.dry_run, upload_to_s3=not args.no_s3)

    try:
        # Run scraper using async context manager
        async with scraper:
            await scraper.run(max_games=args.max_games, priority=args.priority)

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

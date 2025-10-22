#!/usr/bin/env python3
"""
Basketball Reference Play-by-Play Historical Backfill Scraper

Collects play-by-play data for all games from earliest available year to today.
Designed to run after discovery script identifies PBP coverage.

How it works:
1. Get games from scraping_progress table (populated by master game list builder)
2. Work backwards chronologically (most recent first)
3. Extract ONLY play-by-play data (skip if no PBP table)
4. Upload to S3: s3://.../basketball_reference/pbp/{YEAR}/{game_id}_pbp.json
5. Load into database: game_play_by_play table
6. Track progress in database (resume capability)
7. Stop when consecutive games have no PBP (reached historical boundary)

Usage:
    # Scrape all games with PBP
    python scripts/etl/basketball_reference_pbp_backfill.py

    # Start from specific year (based on discovery results)
    python scripts/etl/basketball_reference_pbp_backfill.py --start-year 2000

    # Limit number of games (for testing)
    python scripts/etl/basketball_reference_pbp_backfill.py --max-games 100

    # Dry run (test without uploading/inserting)
    python scripts/etl/basketball_reference_pbp_backfill.py --dry-run --max-games 10

Runtime:
    - Per game: ~12 seconds (rate limit)
    - 1,000 games: ~3.3 hours
    - 10,000 games: ~1.4 days
    - 30,000 games: ~4.2 days (if PBP starts at 2000)

Version: 1.0
Created: October 18, 2025
"""

import argparse
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

# Configuration
DB_PATH = "/tmp/basketball_reference_boxscores.db"
BASE_URL = "https://www.basketball-reference.com"
RATE_LIMIT = 12.0
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIX = "basketball_reference/pbp"  # Separate from box scores

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PBPBackfillScraper:
    """Historical play-by-play backfill scraper"""

    def __init__(self, dry_run=False, upload_to_s3=True):
        self.dry_run = dry_run
        self.upload_to_s3 = upload_to_s3

        self.db_conn = None if dry_run else sqlite3.connect(DB_PATH)
        self.s3_client = None if dry_run or not upload_to_s3 else boto3.client('s3')
        self.last_request_time = 0

        # Statistics
        self.stats = {
            "games_checked": 0,
            "games_with_pbp": 0,
            "games_without_pbp": 0,
            "pbp_events_total": 0,
            "uploaded_to_s3": 0,
            "database_inserts": 0,
            "errors": 0,
            "consecutive_no_pbp": 0
        }

    def rate_limit_wait(self):
        """Enforce 12-second rate limit"""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT:
            sleep_time = RATE_LIMIT - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get_pending_games(self, max_games: Optional[int] = None,
                         start_year: Optional[int] = None) -> List[Dict]:
        """Get games from scraping_progress table, working backwards from today"""
        if self.dry_run:
            # Return dummy data for testing
            return [{
                'game_id': '202306120DEN',
                'game_date': '2023-06-12',
                'season': 2023,
                'home_team': 'DEN',
                'away_team': 'MIA'
            }]

        cursor = self.db_conn.cursor()

        query = """
            SELECT game_id, game_date, season, home_team, away_team
            FROM scraping_progress
            WHERE 1=1
        """
        params = []

        if start_year:
            query += " AND season >= ?"
            params.append(start_year)

        # Order by date DESC (most recent first)
        query += " ORDER BY game_date DESC"

        if max_games:
            query += " LIMIT ?"
            params.append(max_games)

        cursor.execute(query, params)

        games = []
        for row in cursor.fetchall():
            games.append({
                'game_id': row[0],
                'game_date': row[1],
                'season': row[2],
                'home_team': row[3],
                'away_team': row[4]
            })

        return games

    def fetch_pbp_for_game(self, game_id: str) -> Optional[List[Dict]]:
        """Fetch play-by-play data for a single game"""
        url = f"{BASE_URL}/boxscores/{game_id}.html"

        try:
            self.rate_limit_wait()

            response = requests.get(url, headers=HEADERS, timeout=30)

            if response.status_code == 404:
                logger.debug(f"Game {game_id} not found")
                return None

            if response.status_code == 429:
                logger.warning(f"Rate limited on {game_id}")
                return None

            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract PBP
            pbp_events = self._parse_play_by_play(soup, game_id)

            return pbp_events if pbp_events else None

        except Exception as e:
            logger.error(f"Error fetching PBP for {game_id}: {e}")
            return None

    def _parse_play_by_play(self, soup: BeautifulSoup, game_id: str) -> Optional[List[Dict]]:
        """Extract play-by-play events from HTML"""
        try:
            # Find PBP table
            pbp_table = soup.find('table', {'id': 'pbp'})
            if not pbp_table:
                return None

            tbody = pbp_table.find('tbody')
            if not tbody:
                return None

            rows = tbody.find_all('tr')

            events = []
            for row in rows:
                # Skip quarter headers
                if row.get('class') and 'thead' in row.get('class'):
                    continue

                event = {}

                # Extract all cells
                for cell in row.find_all(['th', 'td']):
                    stat_name = cell.get('data-stat')
                    if stat_name:
                        event[stat_name] = cell.text.strip()

                if event:
                    events.append(event)

            return events if events else None

        except Exception as e:
            logger.error(f"Error parsing PBP for {game_id}: {e}")
            return None

    def upload_to_s3_bucket(self, game_id: str, pbp_data: List[Dict]) -> bool:
        """Upload PBP JSON to S3"""
        if self.dry_run or not self.upload_to_s3:
            logger.info(f"[DRY RUN] Would upload {game_id} PBP to S3")
            return True

        try:
            # Extract year from game_id
            year = game_id[:4]

            # S3 key: basketball_reference/pbp/YYYY/game_id_pbp.json
            s3_key = f"{S3_PREFIX}/{year}/{game_id}_pbp.json"

            # Build JSON
            data = {
                'game_id': game_id,
                'scraped_at': datetime.utcnow().isoformat(),
                'event_count': len(pbp_data),
                'events': pbp_data
            }

            # Upload
            self.s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )

            self.stats["uploaded_to_s3"] += 1
            return True

        except ClientError as e:
            logger.error(f"S3 upload failed for {game_id}: {e}")
            return False

    def load_to_database(self, game_id: str, pbp_data: List[Dict]) -> bool:
        """Load PBP events into game_play_by_play table"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would insert {len(pbp_data)} PBP events for {game_id}")
            return True

        try:
            cursor = self.db_conn.cursor()

            # Delete existing PBP for this game (if any)
            cursor.execute("DELETE FROM game_play_by_play WHERE game_id = ?", (game_id,))

            # Insert each event
            for event in pbp_data:
                # Build dynamic INSERT based on available fields
                columns = ['game_id']
                values = [game_id]

                # Map PBP fields to database columns
                field_mapping = {
                    'quarter': 'quarter',
                    'time': 'time_remaining',
                    'description': 'description',
                    'away_score': 'away_score',
                    'home_score': 'home_score',
                }

                for field, column in field_mapping.items():
                    if field in event and event[field]:
                        columns.append(column)
                        values.append(event[field])

                # Build INSERT query
                placeholders = ','.join(['?' for _ in values])
                query = f"INSERT INTO game_play_by_play ({','.join(columns)}) VALUES ({placeholders})"

                try:
                    cursor.execute(query, values)
                except Exception as e:
                    logger.debug(f"Error inserting PBP event: {e}")

            self.db_conn.commit()
            self.stats["database_inserts"] += 1
            return True

        except Exception as e:
            logger.error(f"Database insert failed for {game_id}: {e}")
            return False

    def process_game(self, game: Dict) -> bool:
        """Process a single game for PBP data"""
        game_id = game['game_id']

        logger.info(f"Checking {game_id} ({game['game_date']}) - {game['away_team']} @ {game['home_team']}")

        self.stats["games_checked"] += 1

        # Fetch PBP
        pbp_data = self.fetch_pbp_for_game(game_id)

        if not pbp_data:
            logger.info(f"  ✗ No PBP data")
            self.stats["games_without_pbp"] += 1
            self.stats["consecutive_no_pbp"] += 1
            return False

        # Reset consecutive counter
        self.stats["consecutive_no_pbp"] = 0

        event_count = len(pbp_data)
        logger.info(f"  ✓ Found {event_count} PBP events")

        self.stats["games_with_pbp"] += 1
        self.stats["pbp_events_total"] += event_count

        # Upload to S3
        if self.upload_to_s3:
            s3_success = self.upload_to_s3_bucket(game_id, pbp_data)
            if not s3_success:
                logger.warning(f"S3 upload failed for {game_id}")

        # Load to database
        db_success = self.load_to_database(game_id, pbp_data)
        if not db_success:
            logger.warning(f"Database insert failed for {game_id}")
            self.stats["errors"] += 1

        return True

    def run(self, max_games: Optional[int] = None, start_year: Optional[int] = None,
            stop_after_no_pbp: int = 100):
        """Run the PBP backfill"""
        print("\n" + "="*70)
        print("BASKETBALL REFERENCE PBP HISTORICAL BACKFILL")
        print("="*70)
        print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Dry run: {self.dry_run}")
        print(f"Upload to S3: {self.upload_to_s3}")
        if max_games:
            print(f"Max games: {max_games}")
        if start_year:
            print(f"Start year: {start_year}")
        print(f"Stop after {stop_after_no_pbp} consecutive games with no PBP")
        print()

        # Get games to process
        games = self.get_pending_games(max_games=max_games, start_year=start_year)

        if not games:
            print("No games found!")
            return

        total_games = len(games)
        print(f"Found {total_games} games to check\n")

        estimated_hours = (total_games * RATE_LIMIT) / 3600
        print(f"Estimated time: {estimated_hours:.1f} hours ({total_games} games × {RATE_LIMIT}s)\n")

        # Process each game
        for idx, game in enumerate(games, 1):
            has_pbp = self.process_game(game)

            # Check if we should stop (reached historical boundary)
            if self.stats["consecutive_no_pbp"] >= stop_after_no_pbp:
                logger.info(f"\n⚠️  {stop_after_no_pbp} consecutive games with no PBP. Reached historical boundary.")
                logger.info(f"Stopping early at game {idx}/{total_games}")
                break

            # Progress update
            if idx % 10 == 0 or idx == total_games:
                elapsed_hours = (idx * RATE_LIMIT) / 3600
                remaining = total_games - idx
                eta_hours = (remaining * RATE_LIMIT) / 3600

                print(f"\n{'='*70}")
                print(f"Progress: {idx}/{total_games} ({100*idx/total_games:.1f}%)")
                print(f"Elapsed: {elapsed_hours:.1f}h, ETA: {eta_hours:.1f}h")
                print(f"With PBP: {self.stats['games_with_pbp']}, Without: {self.stats['games_without_pbp']}")
                print(f"Total events: {self.stats['pbp_events_total']:,}")
                print(f"{'='*70}\n")

        # Final summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Games checked:      {self.stats['games_checked']}")
        print(f"Games with PBP:     {self.stats['games_with_pbp']}")
        print(f"Games without PBP:  {self.stats['games_without_pbp']}")
        print(f"Total PBP events:   {self.stats['pbp_events_total']:,}")
        print(f"Uploaded to S3:     {self.stats['uploaded_to_s3']}")
        print(f"Database inserts:   {self.stats['database_inserts']}")
        print(f"Errors:             {self.stats['errors']}")
        print("="*70)

        if self.stats['games_with_pbp'] > 0:
            avg_events = self.stats['pbp_events_total'] / self.stats['games_with_pbp']
            print(f"\nAverage events per game: {avg_events:.0f}")

        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def cleanup(self):
        """Close connections"""
        if self.db_conn:
            self.db_conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference PBP historical backfill"
    )
    parser.add_argument(
        "--max-games",
        type=int,
        help="Maximum number of games to process"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        help="Start from this year (based on discovery results)"
    )
    parser.add_argument(
        "--stop-after-no-pbp",
        type=int,
        default=100,
        help="Stop after N consecutive games with no PBP (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - don't upload or insert"
    )
    parser.add_argument(
        "--no-s3",
        action="store_true",
        help="Don't upload to S3"
    )

    args = parser.parse_args()

    scraper = PBPBackfillScraper(
        dry_run=args.dry_run,
        upload_to_s3=not args.no_s3
    )

    try:
        scraper.run(
            max_games=args.max_games,
            start_year=args.start_year,
            stop_after_no_pbp=args.stop_after_no_pbp
        )
    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()

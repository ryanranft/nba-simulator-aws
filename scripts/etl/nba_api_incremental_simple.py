#!/usr/bin/env python3
"""
NBA API Incremental Scraper - Simplified (No Local Database)

Scrapes last N days of NBA Stats API data directly to S3.
No local database required - always scrapes recent window.

Uses official NBA Stats API endpoints:
- PlayByPlayV2: Play-by-play data
- BoxScoreTraditionalV2: Box scores

Usage:
    python scripts/etl/nba_api_incremental_simple.py              # Last 3 days
    python scripts/etl/nba_api_incremental_simple.py --days 7     # Last 7 days
    python scripts/etl/nba_api_incremental_simple.py --dry-run    # Test mode

For overnight automation (3-source cross-validation):
    - Scrapes last 3 days every night
    - Uploads to S3
    - Enables cross-validation with ESPN and hoopR

Version: 3.0 (Simplified)
Created: October 18, 2025
"""

import argparse
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
import boto3
import requests

# Configuration
NBA_API_BASE = "https://stats.nba.com/stats"
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIX = "nba_api_incremental"
RATE_LIMIT_SECONDS = 1.5  # NBA API is rate-limited

# NBA API requires headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    'Accept': 'application/json',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
}


class NBAAPIIncrementalScraper:
    """Simple NBA Stats API scraper - last N days to S3"""

    def __init__(self, days_back=3, dry_run=False):
        self.days_back = days_back
        self.dry_run = dry_run
        self.s3_client = boto3.client('s3') if not dry_run else None

        # Stats
        self.stats = {
            "games_scraped": 0,
            "games_uploaded": 0,
            "errors": 0,
        }

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

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

    def get_games_for_date(self, date_str):
        """Get game IDs for a specific date from scoreboard."""
        url = f"{NBA_API_BASE}/scoreboardv2"
        params = {
            'GameDate': date_str,  # Format: YYYY-MM-DD
            'LeagueID': '00',
            'DayOffset': '0'
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            game_ids = []
            for game in data.get('resultSets', [{}])[0].get('rowSet', []):
                if game:  # game[0] is game_id
                    game_ids.append(game[2])  # GAME_ID is at index 2

            return game_ids

        except Exception as e:
            self.logger.error(f"Error fetching scoreboard for {date_str}: {e}")
            self.stats["errors"] += 1
            return []

    def get_play_by_play(self, game_id):
        """Get play-by-play for a game."""
        url = f"{NBA_API_BASE}/playbyplayv2"
        params = {
            'GameID': game_id,
            'StartPeriod': '0',
            'EndPeriod': '10'
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching PBP for game {game_id}: {e}")
            self.stats["errors"] += 1
            return None

    def get_box_score(self, game_id):
        """Get box score for a game."""
        url = f"{NBA_API_BASE}/boxscoretraditionalv2"
        params = {
            'GameID': game_id,
            'StartPeriod': '0',
            'EndPeriod': '10',
            'RangeType': '0',
            'StartRange': '0',
            'EndRange': '0'
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching box score for game {game_id}: {e}")
            self.stats["errors"] += 1
            return None

    def upload_to_s3(self, data, s3_key):
        """Upload JSON data to S3."""
        if self.dry_run:
            self.logger.info(f"  [DRY RUN] Would upload to s3://{S3_BUCKET}/{s3_key}")
            return True

        try:
            self.s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(data, indent=2),
                ContentType='application/json'
            )
            return True
        except Exception as e:
            self.logger.error(f"Error uploading to S3: {e}")
            self.stats["errors"] += 1
            return False

    def scrape_date(self, date_str):
        """Scrape all games for a specific date."""
        self.logger.info(f"\nScraping NBA API data for {date_str}...")

        # Get game IDs
        game_ids = self.get_games_for_date(date_str)

        if not game_ids:
            self.logger.info(f"  No games found for {date_str}")
            return

        self.logger.info(f"  Found {len(game_ids)} games")

        # Process each game
        for game_id in game_ids:
            self.logger.info(f"  Processing game {game_id}...")

            # Get play-by-play
            time.sleep(RATE_LIMIT_SECONDS)  # Rate limiting
            pbp_data = self.get_play_by_play(game_id)

            if pbp_data:
                # Upload play-by-play to S3
                s3_key = f"{S3_PREFIX}/{date_str}/game_{game_id}_pbp.json"
                if self.upload_to_s3(pbp_data, s3_key):
                    self.logger.info(f"    ✓ Uploaded PBP to S3")

            # Get box score
            time.sleep(RATE_LIMIT_SECONDS)
            box_score_data = self.get_box_score(game_id)

            if box_score_data:
                # Upload box score to S3
                s3_key = f"{S3_PREFIX}/{date_str}/game_{game_id}_boxscore.json"
                if self.upload_to_s3(box_score_data, s3_key):
                    self.stats["games_scraped"] += 1
                    self.stats["games_uploaded"] += 1
                    self.logger.info(f"    ✓ Uploaded box score to S3")

    def run(self):
        """Run incremental scrape."""
        print("\n" + "=" * 70)
        print("NBA API INCREMENTAL SCRAPER (Simplified)")
        print("=" * 70)
        print(f"\nScraping last {self.days_back} days")
        print(f"Dry run: {self.dry_run}")
        print(f"S3 bucket: {S3_BUCKET}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Get date range
        dates = self.get_date_range()
        self.logger.info(f"Date range: {dates[0]} to {dates[-1]} ({len(dates)} days)")

        # Scrape each date
        for date_str in dates:
            self.scrape_date(date_str)

        # Print summary
        print("\n" + "=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Games scraped:   {self.stats['games_scraped']}")
        print(f"Games uploaded:  {self.stats['games_uploaded']}")
        print(f"Errors:          {self.stats['errors']}")
        print("=" * 70)
        print(f"\n✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    parser = argparse.ArgumentParser(
        description="NBA API incremental scraper (simplified)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="Number of days to scrape back (default: 3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode - don't upload to S3"
    )

    args = parser.parse_args()

    scraper = NBAAPIIncrementalScraper(
        days_back=args.days,
        dry_run=args.dry_run
    )
    scraper.run()


if __name__ == "__main__":
    main()

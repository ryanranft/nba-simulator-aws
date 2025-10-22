#!/usr/bin/env python3
"""
hoopR Incremental Scraper - Simplified (No Local Database)

Scrapes last N days of hoopR data directly to S3.
No local database required - always scrapes recent window.

Usage:
    python scripts/etl/hoopr_incremental_simple.py              # Last 3 days
    python scripts/etl/hoopr_incremental_simple.py --days 7     # Last 7 days
    python scripts/etl/hoopr_incremental_simple.py --dry-run    # Test mode

For overnight automation (3-source cross-validation):
    - Scrapes last 3 days every night
    - Uploads to S3
    - Enables cross-validation with ESPN and NBA API

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

# Import hoopR
try:
    from sportsdataverse.nba import nba_pbp, nba_schedule
except ImportError:
    print("ERROR: sportsdataverse not installed")
    print("Install: pip install sportsdataverse")
    sys.exit(1)

# Configuration
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIX = "hoopr_incremental"
RATE_LIMIT_SECONDS = 2.0  # Be nice to hoopR API


class HoopRIncrementalScraper:
    """Simple hoopR scraper - last N days to S3"""

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

    def get_schedule_for_date(self, date_str):
        """Get hoopR schedule for a specific date."""
        try:
            # Parse date
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            season = date_obj.year if date_obj.month >= 10 else date_obj.year - 1

            # Get schedule
            schedule = nba_schedule(season)

            if schedule is None or schedule.empty:
                return []

            # Filter to specific date
            schedule['game_date'] = schedule['date'].str[:10]
            games = schedule[schedule['game_date'] == date_str]

            return games['id'].tolist() if not games.empty else []

        except Exception as e:
            self.logger.error(f"Error getting schedule for {date_str}: {e}")
            self.stats["errors"] += 1
            return []

    def get_play_by_play(self, game_id):
        """Get play-by-play for a game."""
        try:
            pbp_data = nba_pbp(game_id)
            if pbp_data is not None and not pbp_data.empty:
                return pbp_data.to_dict('records')
            return None
        except Exception as e:
            self.logger.error(f"Error fetching PBP for game {game_id}: {e}")
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
        self.logger.info(f"\nScraping hoopR data for {date_str}...")

        # Get schedule
        game_ids = self.get_schedule_for_date(date_str)

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
                # Upload to S3
                s3_key = f"{S3_PREFIX}/{date_str}/game_{game_id}_pbp.json"
                if self.upload_to_s3(pbp_data, s3_key):
                    self.stats["games_scraped"] += 1
                    self.stats["games_uploaded"] += 1
                    self.logger.info(f"    ✓ Uploaded to S3")

            time.sleep(RATE_LIMIT_SECONDS)

    def run(self):
        """Run incremental scrape."""
        print("\n" + "=" * 70)
        print("HOOPR INCREMENTAL SCRAPER (Simplified)")
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
        description="hoopR incremental scraper (simplified)"
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

    scraper = HoopRIncrementalScraper(
        days_back=args.days,
        dry_run=args.dry_run
    )
    scraper.run()


if __name__ == "__main__":
    main()

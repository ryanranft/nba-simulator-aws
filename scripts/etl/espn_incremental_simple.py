#!/usr/bin/env python3
"""
ESPN Incremental Scraper - Simplified (No Local Database)

⚠️ LEGACY VERSION - For backward compatibility only
➡️  Use espn_incremental_async.py for autonomous operations and new scraping tasks

Scrapes last N days of ESPN data directly to S3.
No local database required - always scrapes recent window.

Usage:
    python scripts/etl/espn_incremental_simple.py              # Last 3 days
    python scripts/etl/espn_incremental_simple.py --days 7     # Last 7 days
    python scripts/etl/espn_incremental_simple.py --dry-run    # Test mode

For overnight automation (3-source cross-validation):
    - Use espn_incremental_async.py instead (AsyncBaseScraper framework)
    - Integrated with ADCE autonomous data collection
    - Better rate limiting and retry logic

Version: 3.0 (Simplified - Legacy)
Created: October 18, 2025
Superseded by: espn_incremental_async.py (November 6, 2025)
"""


# TODO: AsyncBaseScraper Integration
# 1. Make your main class inherit from AsyncBaseScraper
# 2. Add config_name parameter to __init__
# 3. Call super().__init__(config_name=config_name)
# 4. Wrap synchronous HTTP calls in asyncio.to_thread()
# 5. Use self.rate_limiter.acquire() before requests
# 6. Use self.store_data() for S3 uploads
#
# Import AsyncBaseScraper framework
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.etl.async_scraper_base import AsyncBaseScraper
from nba_simulator.etl.config import ScraperConfigManager

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
BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIX_PBP = "espn_play_by_play"
S3_PREFIX_BOX = "espn_box_scores"
S3_PREFIX_SCHEDULE = "espn_schedules"
S3_PREFIX_TEAM = "espn_team_stats"
RATE_LIMIT_SECONDS = 1.0  # Be nice to ESPN


class ESPNIncrementalScraper:

    # TODO: After inheriting from AsyncBaseScraper:
    # - Add config_name parameter to __init__
    # - Call super().__init__(config_name='espn_incremental_simple')

    """Simple ESPN scraper - last N days to S3"""

    def __init__(self, days_back=3, dry_run=False):
        self.days_back = days_back
        self.dry_run = dry_run
        self.s3_client = boto3.client("s3") if not dry_run else None

        # Stats
        self.stats = {
            "games_scraped": 0,
            "games_uploaded": 0,
            "errors": 0,
        }

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def get_date_range(self):
        """Get list of dates to scrape."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.days_back)

        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

        return dates

    def get_schedule(self, date_str):
        """Get schedule for a specific date."""
        url = f"{BASE_URL}/scoreboard"
        params = {"dates": date_str, "limit": 100}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching schedule for {date_str}: {e}")
            self.stats["errors"] += 1
            return None

    def get_play_by_play(self, game_id):
        """Get play-by-play for a game."""
        url = f"{BASE_URL}/summary"
        params = {"event": game_id}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching PBP for game {game_id}: {e}")
            self.stats["errors"] += 1
            return None

    def get_box_score(self, game_id):
        """Get box score for a game."""
        url = f"{BASE_URL}/summary"
        params = {"event": game_id}

        try:
            response = requests.get(url, params=params, timeout=30)
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
                ContentType="application/json",
            )
            self.logger.info(f"    ✓ Uploaded to s3://{S3_BUCKET}/{s3_key}")
            return True
        except Exception as e:
            self.logger.error(f"    ✗ Error uploading to S3 ({s3_key}): {e}")
            self.stats["errors"] += 1
            return False

    def scrape_date(self, date_str):
        """Scrape all games for a specific date."""
        self.logger.info(f"\nScraping ESPN data for {date_str}...")

        # Get schedule
        schedule_data = self.get_schedule(date_str)
        if not schedule_data:
            return

        # Save schedule to S3
        schedule_key = f"{S3_PREFIX_SCHEDULE}/{date_str}.json"
        self.upload_to_s3(schedule_data, schedule_key)

        # Extract games
        events = schedule_data.get("events", [])
        if not events:
            self.logger.info(f"  No games found for {date_str}")
            return

        self.logger.info(f"  Found {len(events)} games")

        # Process each game
        for event in events:
            game_id = event.get("id")
            if not game_id:
                continue

            self.logger.info(f"  Processing game {game_id}...")

            # Get game summary (contains pbp, box score, team stats)
            time.sleep(RATE_LIMIT_SECONDS)  # Rate limiting
            game_data = self.get_play_by_play(game_id)

            if game_data:
                # Upload to S3 with proper naming (game_id.json, not game_{id}_pbp.json)
                pbp_key = f"{S3_PREFIX_PBP}/{game_id}.json"
                box_key = f"{S3_PREFIX_BOX}/{game_id}.json"
                team_key = f"{S3_PREFIX_TEAM}/{game_id}.json"

                # Upload same data to all three locations (ESPN summary has everything)
                uploaded = 0
                if self.upload_to_s3(game_data, pbp_key):
                    uploaded += 1
                if self.upload_to_s3(game_data, box_key):
                    uploaded += 1
                if self.upload_to_s3(game_data, team_key):
                    uploaded += 1

                if uploaded > 0:
                    self.stats["games_scraped"] += 1
                    self.stats["games_uploaded"] += uploaded

            time.sleep(RATE_LIMIT_SECONDS)

    def run(self):
        """Run incremental scrape."""
        print("\n" + "=" * 70)
        print("ESPN INCREMENTAL SCRAPER (Simplified)")
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
        description="ESPN incremental scraper (simplified)"
    )
    parser.add_argument(
        "--days", type=int, default=3, help="Number of days to scrape back (default: 3)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Test mode - don't upload to S3"
    )

    args = parser.parse_args()

    scraper = ESPNIncrementalScraper(days_back=args.days, dry_run=args.dry_run)
    scraper.run()


if __name__ == "__main__":
    main()

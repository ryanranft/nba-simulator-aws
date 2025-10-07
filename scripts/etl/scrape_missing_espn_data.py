#!/usr/bin/env python3
"""
ESPN Data Scraper - Fill Missing Data (2022-2025)

Scrapes ESPN for missing NBA data and saves individual JSON files for AWS Glue processing.

Data to scrape:
1. Schedule data (by date)
2. Box scores (by game ID)
3. Team stats (by game ID)
4. Play-by-play (by game ID)

Usage:
    python scripts/etl/scrape_missing_espn_data.py --start-date 2022-01-01 --end-date 2025-04-13
    python scripts/etl/scrape_missing_espn_data.py --start-date 2022-01-01 --end-date 2025-04-13 --upload-to-s3
"""

import requests
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("⚠️  boto3 not available - S3 upload will be disabled")


class ESPNScraper:
    """Scraper for ESPN NBA API data"""

    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"

    def __init__(self, output_dir="/tmp/espn_data", s3_bucket=None):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None

        # Create output directories
        for subdir in ['schedule', 'box_scores', 'team_stats', 'pbp']:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Stats
        self.stats = {
            'schedule_files': 0,
            'box_score_files': 0,
            'team_stats_files': 0,
            'pbp_files': 0,
            'errors': 0,
            'games_found': 0
        }

    def get_schedule(self, date_str):
        """
        Get schedule for a specific date

        Args:
            date_str: Date in YYYYMMDD format

        Returns:
            dict: Schedule JSON or None if error
        """
        url = f"{self.BASE_URL}/scoreboard"
        params = {
            'dates': date_str,
            'limit': 100
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching schedule for {date_str}: {e}")
            self.stats['errors'] += 1
            return None

    def get_box_score(self, game_id):
        """
        Get box score for a game

        Args:
            game_id: ESPN game ID

        Returns:
            dict: Box score JSON or None if error
        """
        url = f"{self.BASE_URL}/summary"
        params = {'event': game_id}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching box score for game {game_id}: {e}")
            self.stats['errors'] += 1
            return None

    def get_play_by_play(self, game_id):
        """
        Get play-by-play for a game

        Args:
            game_id: ESPN game ID

        Returns:
            dict: Play-by-play JSON or None if error
        """
        url = f"{self.BASE_URL}/playbyplay"
        params = {'event': game_id}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching play-by-play for game {game_id}: {e}")
            self.stats['errors'] += 1
            return None

    def save_json(self, data, filepath):
        """Save JSON data to file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def upload_to_s3(self, local_path, s3_key):
        """Upload file to S3"""
        if not self.s3_client:
            return False

        try:
            self.s3_client.upload_file(str(local_path), self.s3_bucket, s3_key)
            return True
        except Exception as e:
            print(f"❌ Error uploading {s3_key} to S3: {e}")
            return False

    def scrape_date(self, date_obj):
        """
        Scrape all data for a specific date

        Args:
            date_obj: datetime object
        """
        date_str = date_obj.strftime("%Y%m%d")
        print(f"\n📅 Scraping {date_str}...")

        # 1. Get schedule
        schedule_data = self.get_schedule(date_str)
        if not schedule_data:
            return

        # Save schedule
        schedule_file = self.output_dir / 'schedule' / f"{date_str}.json"
        self.save_json(schedule_data, schedule_file)
        self.stats['schedule_files'] += 1

        # Upload to S3 if configured
        if self.s3_client:
            s3_key = f"schedule/{date_str}.json"
            if self.upload_to_s3(schedule_file, s3_key):
                print(f"  ✅ Uploaded schedule/{date_str}.json to S3")

        # 2. Extract game IDs and scrape game data
        events = schedule_data.get('events', [])
        if not events:
            print(f"  ⚠️  No games on {date_str}")
            return

        print(f"  Found {len(events)} games")
        self.stats['games_found'] += len(events)

        for event in events:
            game_id = event.get('id')
            if not game_id:
                continue

            # Get game name for logging
            competitions = event.get('competitions', [])
            if competitions:
                home_team = competitions[0].get('competitors', [{}])[0].get('team', {}).get('abbreviation', 'UNK')
                away_team = competitions[0].get('competitors', [{}])[1].get('team', {}).get('abbreviation', 'UNK')
                game_name = f"{away_team} @ {home_team}"
            else:
                game_name = f"Game {game_id}"

            print(f"    🏀 {game_name} (ID: {game_id})")

            # 3. Get box score
            box_score_data = self.get_box_score(game_id)
            if box_score_data:
                box_file = self.output_dir / 'box_scores' / f"{game_id}.json"
                self.save_json(box_score_data, box_file)
                self.stats['box_score_files'] += 1

                if self.s3_client:
                    s3_key = f"box_scores/{game_id}.json"
                    self.upload_to_s3(box_file, s3_key)

            # 4. Get team stats (extracted from box score)
            if box_score_data:
                team_stats_file = self.output_dir / 'team_stats' / f"{game_id}.json"
                self.save_json(box_score_data, team_stats_file)
                self.stats['team_stats_files'] += 1

                if self.s3_client:
                    s3_key = f"team_stats/{game_id}.json"
                    self.upload_to_s3(team_stats_file, s3_key)

            # 5. Get play-by-play
            pbp_data = self.get_play_by_play(game_id)
            if pbp_data:
                pbp_file = self.output_dir / 'pbp' / f"{game_id}.json"
                self.save_json(pbp_data, pbp_file)
                self.stats['pbp_files'] += 1

                if self.s3_client:
                    s3_key = f"pbp/{game_id}.json"
                    self.upload_to_s3(pbp_file, s3_key)

            # Rate limiting
            time.sleep(0.5)

        # Rate limiting between dates
        time.sleep(1)

    def scrape_date_range(self, start_date, end_date):
        """
        Scrape data for a date range

        Args:
            start_date: datetime object or string (YYYY-MM-DD)
            end_date: datetime object or string (YYYY-MM-DD)
        """
        # Parse dates if strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start_date
        total_days = (end_date - start_date).days + 1

        print(f"🚀 Starting ESPN scraper")
        print(f"📅 Date range: {start_date.date()} to {end_date.date()} ({total_days} days)")
        print(f"💾 Output directory: {self.output_dir}")
        if self.s3_client:
            print(f"☁️  S3 bucket: {self.s3_bucket}")
        print()

        day_count = 0
        while current_date <= end_date:
            day_count += 1
            print(f"\n[{day_count}/{total_days}]", end=" ")
            self.scrape_date(current_date)
            current_date += timedelta(days=1)

        # Print summary
        print("\n" + "="*60)
        print("📊 SCRAPING SUMMARY")
        print("="*60)
        print(f"Schedule files:   {self.stats['schedule_files']:,}")
        print(f"Box score files:  {self.stats['box_score_files']:,}")
        print(f"Team stats files: {self.stats['team_stats_files']:,}")
        print(f"Play-by-play files: {self.stats['pbp_files']:,}")
        print(f"Total games found: {self.stats['games_found']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Scrape ESPN NBA data for missing dates")
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='/tmp/espn_data', help='Local output directory')
    parser.add_argument('--upload-to-s3', action='store_true', help='Upload to S3 after scraping')
    parser.add_argument('--s3-bucket', default='nba-sim-raw-data-lake', help='S3 bucket name')

    args = parser.parse_args()

    # Validate dates
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("Use YYYY-MM-DD format (e.g., 2022-01-01)")
        sys.exit(1)

    if start_date > end_date:
        print("❌ Start date must be before end date")
        sys.exit(1)

    # Check S3 configuration
    s3_bucket = args.s3_bucket if args.upload_to_s3 else None
    if args.upload_to_s3 and not HAS_BOTO3:
        print("❌ boto3 is required for S3 upload. Install with: pip install boto3")
        sys.exit(1)

    # Create scraper and run
    scraper = ESPNScraper(output_dir=args.output_dir, s3_bucket=s3_bucket)
    scraper.scrape_date_range(start_date, end_date)

    print(f"\n✅ Scraping complete!")
    print(f"📁 Files saved to: {scraper.output_dir}")
    if s3_bucket:
        print(f"☁️  Files uploaded to s3://{s3_bucket}/")


if __name__ == '__main__':
    main()
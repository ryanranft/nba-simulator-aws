#!/usr/bin/env python3
"""
NBA.com Stats API Scraper

Scrapes official NBA.com Stats API for verification and validation of ESPN data.

API Documentation (unofficial):
- https://github.com/swar/nba_api
- https://github.com/swar/nba_api/tree/master/docs/nba_api/stats/endpoints

Usage:
    python scripts/etl/scrape_nba_stats_api.py --start-date 2022-01-01 --end-date 2025-04-13
    python scripts/etl/scrape_nba_stats_api.py --start-date 2024-01-01 --end-date 2024-12-31 --upload-to-s3
"""

import requests
import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("⚠️  boto3 not available - S3 upload will be disabled")


class NBAStatsAPIScraper:
    """Scraper for NBA.com Stats API"""

    BASE_URL = "https://stats.nba.com/stats"

    # Required headers to avoid 403 errors
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.nba.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'x-nba-stats-origin': 'stats',
        'x-nba-stats-token': 'true'
    }

    def __init__(self, output_dir="/tmp/nba_stats_api", s3_bucket=None):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None

        # Create output directories
        for subdir in ['scoreboard', 'boxscore', 'playbyplay']:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Stats
        self.stats = {
            'scoreboard_files': 0,
            'boxscore_files': 0,
            'playbyplay_files': 0,
            'errors': 0,
            'games_found': 0,
            'api_calls': 0
        }

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 3.0  # 3 seconds between requests (conservative)

    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request(self, endpoint, params):
        """
        Make API request with rate limiting and error handling

        Args:
            endpoint: API endpoint (e.g., 'scoreboardV2')
            params: Query parameters

        Returns:
            dict: JSON response or None if error
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params=params, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            self.stats['api_calls'] += 1
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"❌ 403 Forbidden - API may have blocked request")
                print(f"   Try increasing rate limit or updating headers")
            else:
                print(f"❌ HTTP Error {e.response.status_code}: {e}")
            self.stats['errors'] += 1
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            self.stats['errors'] += 1
            return None

    def get_scoreboard(self, game_date):
        """
        Get scoreboard for a specific date

        Args:
            game_date: datetime object

        Returns:
            dict: Scoreboard JSON or None if error
        """
        date_str = game_date.strftime("%m/%d/%Y")

        params = {
            'GameDate': date_str,
            'LeagueID': '00',  # NBA
            'DayOffset': '0'
        }

        return self._make_request('scoreboardV2', params)

    def get_boxscore(self, game_id):
        """
        Get box score for a game

        Args:
            game_id: NBA.com game ID (e.g., '0022200001')

        Returns:
            dict: Box score JSON or None if error
        """
        params = {
            'GameID': game_id,
            'StartPeriod': '0',
            'EndPeriod': '10',
            'RangeType': '2',
            'StartRange': '0',
            'EndRange': '28800'
        }

        return self._make_request('boxscoretraditionalv2', params)

    def get_playbyplay(self, game_id):
        """
        Get play-by-play for a game

        Args:
            game_id: NBA.com game ID

        Returns:
            dict: Play-by-play JSON or None if error
        """
        params = {
            'GameID': game_id,
            'StartPeriod': '0',
            'EndPeriod': '10'
        }

        return self._make_request('playbyplayv2', params)

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
        date_str = date_obj.strftime("%Y-%m-%d")
        print(f"\n📅 Scraping {date_str}...")

        # 1. Get scoreboard
        scoreboard_data = self.get_scoreboard(date_obj)
        if not scoreboard_data:
            print(f"  ❌ Failed to get scoreboard")
            return

        # Save scoreboard
        scoreboard_file = self.output_dir / 'scoreboard' / f"{date_obj.strftime('%Y%m%d')}.json"
        self.save_json(scoreboard_data, scoreboard_file)
        self.stats['scoreboard_files'] += 1

        # Upload to S3 if configured
        if self.s3_client:
            s3_key = f"nba_stats_api/scoreboard/{date_obj.strftime('%Y%m%d')}.json"
            if self.upload_to_s3(scoreboard_file, s3_key):
                print(f"  ✅ Uploaded scoreboard to S3")

        # 2. Extract game IDs
        result_sets = scoreboard_data.get('resultSets', [])
        if not result_sets:
            print(f"  ⚠️  No games on {date_str}")
            return

        # Find GameHeader result set
        game_headers = None
        for rs in result_sets:
            if rs.get('name') == 'GameHeader':
                game_headers = rs
                break

        if not game_headers:
            print(f"  ⚠️  No GameHeader in scoreboard")
            return

        headers = game_headers.get('headers', [])
        rows = game_headers.get('rowSet', [])

        if not rows:
            print(f"  ⚠️  No games on {date_str}")
            return

        print(f"  Found {len(rows)} games")
        self.stats['games_found'] += len(rows)

        # Find GAME_ID column index
        try:
            game_id_idx = headers.index('GAME_ID')
        except ValueError:
            print(f"  ❌ GAME_ID not found in headers")
            return

        # 3. Scrape each game
        for row in rows:
            game_id = row[game_id_idx]

            # Get team names for logging
            try:
                home_team_idx = headers.index('HOME_TEAM_ID')
                visitor_team_idx = headers.index('VISITOR_TEAM_ID')
                home_team = row[home_team_idx]
                visitor_team = row[visitor_team_idx]
                game_name = f"{visitor_team} @ {home_team}"
            except:
                game_name = f"Game {game_id}"

            print(f"    🏀 {game_name} (ID: {game_id})")

            # Get box score
            boxscore_data = self.get_boxscore(game_id)
            if boxscore_data:
                boxscore_file = self.output_dir / 'boxscore' / f"{game_id}.json"
                self.save_json(boxscore_data, boxscore_file)
                self.stats['boxscore_files'] += 1

                if self.s3_client:
                    s3_key = f"nba_stats_api/boxscore/{game_id}.json"
                    self.upload_to_s3(boxscore_file, s3_key)

            # Get play-by-play
            pbp_data = self.get_playbyplay(game_id)
            if pbp_data:
                pbp_file = self.output_dir / 'playbyplay' / f"{game_id}.json"
                self.save_json(pbp_data, pbp_file)
                self.stats['playbyplay_files'] += 1

                if self.s3_client:
                    s3_key = f"nba_stats_api/playbyplay/{game_id}.json"
                    self.upload_to_s3(pbp_file, s3_key)

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

        print(f"🚀 Starting NBA.com Stats API scraper")
        print(f"📅 Date range: {start_date.date()} to {end_date.date()} ({total_days} days)")
        print(f"💾 Output directory: {self.output_dir}")
        print(f"⏱️  Rate limit: {self.min_request_interval} seconds between requests")
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
        print(f"Scoreboard files:    {self.stats['scoreboard_files']:,}")
        print(f"Box score files:     {self.stats['boxscore_files']:,}")
        print(f"Play-by-play files:  {self.stats['playbyplay_files']:,}")
        print(f"Total games found:   {self.stats['games_found']:,}")
        print(f"Total API calls:     {self.stats['api_calls']:,}")
        print(f"Errors:              {self.stats['errors']:,}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Scrape NBA.com Stats API")
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='/tmp/nba_stats_api', help='Local output directory')
    parser.add_argument('--upload-to-s3', action='store_true', help='Upload to S3 after scraping')
    parser.add_argument('--s3-bucket', default='nba-sim-raw-data-lake', help='S3 bucket name')
    parser.add_argument('--rate-limit', type=float, default=3.0, help='Seconds between requests (default: 3.0)')

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
    scraper = NBAStatsAPIScraper(output_dir=args.output_dir, s3_bucket=s3_bucket)
    scraper.min_request_interval = args.rate_limit
    scraper.scrape_date_range(start_date, end_date)

    print(f"\n✅ Scraping complete!")
    print(f"📁 Files saved to: {scraper.output_dir}")
    if s3_bucket:
        print(f"☁️  Files uploaded to s3://{s3_bucket}/nba_stats_api/")


if __name__ == '__main__':
    main()
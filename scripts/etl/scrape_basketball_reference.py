#!/usr/bin/env python3
"""
Basketball Reference Scraper

Scrapes NBA data from Basketball-Reference.com (https://www.basketball-reference.com/)

⚠️  IMPORTANT - Terms of Service:
- Rate limit: 1 request per 3 seconds minimum
- Identify your bot in User-Agent
- Academic/personal use only
- No commercial use without permission
- Respect robots.txt

Prerequisites:
    pip install beautifulsoup4 lxml pandas

Usage:
    python scripts/etl/scrape_basketball_reference.py --season 2024
    python scripts/etl/scrape_basketball_reference.py --season 2024 --upload-to-s3
    python scripts/etl/scrape_basketball_reference.py --season 2024 --game-logs
"""

import argparse
import requests
import json
import time
import sys
from pathlib import Path
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    import pandas as pd

    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    print("❌ Missing dependencies")
    print("Install with: pip install beautifulsoup4 lxml pandas")

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class BasketballReferenceScraper:
    """Scraper for Basketball-Reference.com"""

    BASE_URL = "https://www.basketball-reference.com"

    HEADERS = {
        "User-Agent": "NBA-Simulator-Research-Bot/1.0 (Academic Use)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, output_dir="/tmp/basketball_reference", s3_bucket=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3") if HAS_BOTO3 and s3_bucket else None

        self.last_request_time = 0
        self.min_request_interval = 3.5  # 3.5 seconds (respectful rate limiting)

        self.stats = {"pages_scraped": 0, "tables_extracted": 0, "errors": 0}

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request(self, url):
        """Make HTTP request with rate limiting"""
        self._rate_limit()

        try:
            response = requests.get(url, headers=self.HEADERS, timeout=15)
            response.raise_for_status()
            self.stats["pages_scraped"] += 1
            return response.text
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_season_schedule(self, season):
        """
        Scrape season schedule

        Args:
            season: Season year (e.g., 2024 for 2023-24 season)
        """
        print(f"📅 Scraping {season} season schedule...")

        url = f"{self.BASE_URL}/leagues/NBA_{season}_games.html"
        html = self._make_request(url)

        if not html:
            return None

        try:
            # Parse HTML
            soup = BeautifulSoup(html, "lxml")

            # Find schedule table
            table = soup.find("table", {"id": "schedule"})
            if not table:
                print("  ⚠️  Schedule table not found")
                return None

            # Use pandas to parse table
            df = pd.read_html(str(table))[0]

            # Convert to dict
            schedule_data = df.to_dict("records")

            # Save
            output_file = self.output_dir / f"schedule_{season}.json"
            with open(output_file, "w") as f:
                json.dump(schedule_data, f, indent=2)

            self.stats["tables_extracted"] += 1
            print(f"  ✅ Saved {len(schedule_data)} games")

            # Upload to S3
            if self.s3_client:
                s3_key = f"basketball_reference/schedule_{season}.json"
                self.s3_client.upload_file(str(output_file), self.s3_bucket, s3_key)

            return schedule_data

        except Exception as e:
            print(f"  ❌ Error parsing schedule: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_team_stats(self, season):
        """Scrape team statistics for a season"""
        print(f"📊 Scraping {season} team stats...")

        url = f"{self.BASE_URL}/leagues/NBA_{season}.html"
        html = self._make_request(url)

        if not html:
            return None

        try:
            # Find all tables
            dfs = pd.read_html(html)

            stats_data = {}
            for i, df in enumerate(dfs):
                stats_data[f"table_{i}"] = df.to_dict("records")

            # Save
            output_file = self.output_dir / f"team_stats_{season}.json"
            with open(output_file, "w") as f:
                json.dump(stats_data, f, indent=2)

            self.stats["tables_extracted"] += len(dfs)
            print(f"  ✅ Saved {len(dfs)} tables")

            if self.s3_client:
                s3_key = f"basketball_reference/team_stats_{season}.json"
                self.s3_client.upload_file(str(output_file), self.s3_bucket, s3_key)

            return stats_data

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_player_stats(self, season):
        """Scrape player statistics for a season"""
        print(f"🏀 Scraping {season} player stats...")

        url = f"{self.BASE_URL}/leagues/NBA_{season}_per_game.html"
        html = self._make_request(url)

        if not html:
            return None

        try:
            # Parse table
            df = pd.read_html(html)[0]
            player_data = df.to_dict("records")

            # Save
            output_file = self.output_dir / f"player_stats_{season}.json"
            with open(output_file, "w") as f:
                json.dump(player_data, f, indent=2)

            self.stats["tables_extracted"] += 1
            print(f"  ✅ Saved {len(player_data)} players")

            if self.s3_client:
                s3_key = f"basketball_reference/player_stats_{season}.json"
                self.s3_client.upload_file(str(output_file), self.s3_bucket, s3_key)

            return player_data

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.stats["errors"] += 1
            return None


def main():
    parser = argparse.ArgumentParser(description="Scrape Basketball-Reference.com")
    parser.add_argument(
        "--season", type=int, required=True, help="Season year (e.g., 2024)"
    )
    parser.add_argument(
        "--output-dir", default="/tmp/basketball_reference", help="Output directory"
    )
    parser.add_argument("--upload-to-s3", action="store_true", help="Upload to S3")
    parser.add_argument(
        "--s3-bucket", default="nba-sim-raw-data-lake", help="S3 bucket"
    )
    parser.add_argument("--schedule", action="store_true", help="Scrape schedule")
    parser.add_argument("--team-stats", action="store_true", help="Scrape team stats")
    parser.add_argument(
        "--player-stats", action="store_true", help="Scrape player stats"
    )
    parser.add_argument("--all", action="store_true", help="Scrape all data")

    args = parser.parse_args()

    if not HAS_DEPS:
        sys.exit(1)

    s3_bucket = args.s3_bucket if args.upload_to_s3 else None
    scraper = BasketballReferenceScraper(
        output_dir=args.output_dir, s3_bucket=s3_bucket
    )

    print("🚀 Basketball-Reference.com Scraper")
    print(f"📅 Season: {args.season}")
    print(f"⏱️  Rate limit: {scraper.min_request_interval}s between requests")
    print()

    # Scrape data
    if args.all or args.schedule:
        scraper.scrape_season_schedule(args.season)

    if args.all or args.team_stats:
        scraper.scrape_team_stats(args.season)

    if args.all or args.player_stats:
        scraper.scrape_player_stats(args.season)

    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"Pages scraped: {scraper.stats['pages_scraped']}")
    print(f"Tables extracted: {scraper.stats['tables_extracted']}")
    print(f"Errors: {scraper.stats['errors']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

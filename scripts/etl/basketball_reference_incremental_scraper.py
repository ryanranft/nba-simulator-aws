#!/usr/bin/env python3
"""
Basketball Reference Incremental Scraper - Daily Updates Only

Scrapes current season aggregate data (season totals + advanced stats) for daily updates.
Designed for nightly automation - NOT for historical backfills.

Strategy:
1. Determine current NBA season
2. Scrape season totals for current season (updated daily as games are played)
3. Scrape advanced totals for current season
4. Upload to S3
5. Optionally re-integrate into local database

During the season:
- Player stats get updated as games are played
- New players are added (call-ups, trades, etc.)
- Typically takes 30-60 seconds to scrape both data types

Off-season:
- Previous season finalized stats are scraped
- No current season data available yet
- Takes <10 seconds

Runtime: ~1 minute during season, <10 seconds off-season

Usage:
    python scripts/etl/basketball_reference_incremental_scraper.py
    python scripts/etl/basketball_reference_incremental_scraper.py --also-previous-season
    python scripts/etl/basketball_reference_incremental_scraper.py --dry-run

Version: 1.0
Created: October 10, 2025
"""

import argparse
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import sys

try:
    from basketball_reference_web_scraper import client
    HAS_BBREF = True
except ImportError:
    HAS_BBREF = False
    print("❌ basketball_reference_web_scraper not installed")
    print("Install: pip install basketball_reference_web_scraper")
    sys.exit(1)

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("⚠️  boto3 not installed, S3 upload will be disabled")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

class BasketballReferenceIncrementalScraper:
    """Incremental scraper for Basketball Reference aggregate data"""

    def __init__(self, s3_bucket: Optional[str] = None, rate_limit: float = 12.0, dry_run: bool = False):
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.dry_run = dry_run

        # Statistics
        self.stats = {
            'requests': 0,
            'successes': 0,
            'errors': 0,
            'retries': 0,
        }

        # Output directory
        self.output_dir = Path('/tmp/basketball_reference_incremental')
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _rate_limit_wait(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            logging.debug(f"  Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _exponential_backoff(self, attempt: int, is_rate_limit: bool = False):
        """Exponential backoff on errors"""
        if is_rate_limit:
            # For 429 errors, wait much longer (30s, 60s, 120s)
            wait_time = min(120, 30 * (2 ** attempt))
        else:
            wait_time = min(60, (2 ** attempt))
        logging.warning(f"  Backing off for {wait_time}s (attempt {attempt})")
        time.sleep(wait_time)

    def _save_json(self, data: any, filepath: Path):
        """Save data to JSON file"""
        if self.dry_run:
            logging.info(f"  [DRY RUN] Would save to: {filepath}")
            return

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logging.debug(f"  Saved: {filepath}")

    def _upload_to_s3(self, local_path: Path, s3_key: str) -> bool:
        """Upload file to S3"""
        if self.dry_run:
            logging.info(f"  [DRY RUN] Would upload to S3: {s3_key}")
            return True

        if not self.s3_client:
            return False

        try:
            self.s3_client.upload_file(str(local_path), self.s3_bucket, s3_key)
            logging.debug(f"  Uploaded to S3: {s3_key}")
            return True
        except Exception as e:
            logging.error(f"  S3 upload failed: {e}")
            return False

    def _make_request_with_retry(self, func, *args, max_retries: int = 3, **kwargs):
        """Make API request with retry logic"""
        for attempt in range(max_retries):
            try:
                self._rate_limit_wait()
                self.stats['requests'] += 1
                result = func(*args, **kwargs)
                self.stats['successes'] += 1
                return result
            except Exception as e:
                self.stats['errors'] += 1
                # Check if it's a 429 rate limit error
                is_429 = '429' in str(e) or 'Too Many Requests' in str(e)
                if attempt < max_retries - 1:
                    self.stats['retries'] += 1
                    logging.warning(f"  Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                    self._exponential_backoff(attempt, is_rate_limit=is_429)
                else:
                    logging.error(f"  Request failed after {max_retries} attempts: {e}")
                    raise
        return None

    def get_current_season(self):
        """Get current NBA season end year"""
        now = datetime.now()
        # NBA season starts in October
        # If we're in Oct-Dec, it's next year's end year (2024-2025 season = 2025)
        # If we're in Jan-Sep, it's current year's end year
        if now.month >= 10:
            return now.year + 1
        else:
            return now.year

    def scrape_season_totals(self, season: int) -> bool:
        """Scrape season totals for a given season"""
        logging.info(f"\n📊 Scraping season totals for {season-1}-{season} season...")

        try:
            # Get season totals
            totals = self._make_request_with_retry(
                client.players_season_totals,
                season_end_year=season
            )

            if totals:
                # Save locally
                local_path = self.output_dir / 'season_totals' / str(season) / 'player_season_totals.json'
                self._save_json(totals, local_path)

                # Upload to S3
                if self.s3_client:
                    s3_key = f'basketball_reference/season_totals/{season}/player_season_totals.json'
                    self._upload_to_s3(local_path, s3_key)

                logging.info(f"  ✓ Season totals: {len(totals)} player records")
                return True
            else:
                logging.warning(f"  ⚠️  No season totals data returned")
                return False

        except Exception as e:
            logging.error(f"  ❌ Failed to scrape season totals: {e}")
            return False

    def scrape_advanced_totals(self, season: int) -> bool:
        """Scrape advanced totals for a given season"""
        logging.info(f"\n📈 Scraping advanced totals for {season-1}-{season} season...")

        try:
            # Get advanced totals with combined values for traded players
            totals = self._make_request_with_retry(
                client.players_advanced_season_totals,
                season_end_year=season,
                include_combined_values=True
            )

            if totals:
                # Save locally
                local_path = self.output_dir / 'advanced_totals' / str(season) / 'player_advanced_totals.json'
                self._save_json(totals, local_path)

                # Upload to S3
                if self.s3_client:
                    s3_key = f'basketball_reference/advanced_totals/{season}/player_advanced_totals.json'
                    self._upload_to_s3(local_path, s3_key)

                logging.info(f"  ✓ Advanced totals: {len(totals)} player records")
                return True
            else:
                logging.warning(f"  ⚠️  No advanced totals data returned")
                return False

        except Exception as e:
            logging.error(f"  ❌ Failed to scrape advanced totals: {e}")
            return False

    def scrape_incremental(self, also_previous_season: bool = False):
        """Scrape current season aggregate data"""
        print("=" * 70)
        print("BASKETBALL REFERENCE INCREMENTAL SCRAPER")
        print("=" * 70)
        print()

        current_season = self.get_current_season()

        print(f"Current NBA season: {current_season-1}-{current_season}")
        print(f"Rate limit: {self.rate_limit}s between requests")
        print(f"S3 upload: {'Enabled' if self.s3_client else 'Disabled'}")
        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
        print()

        seasons_to_scrape = [current_season]

        # Optionally scrape previous season (for end-of-season finalized stats)
        if also_previous_season:
            seasons_to_scrape.insert(0, current_season - 1)
            logging.info(f"Also scraping previous season: {current_season-2}-{current_season-1}\n")

        total_success = 0
        total_failures = 0

        for season in seasons_to_scrape:
            logging.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logging.info(f"Season {season-1}-{season}")
            logging.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            # Scrape season totals
            season_success = self.scrape_season_totals(season)
            if season_success:
                total_success += 1
            else:
                total_failures += 1

            # Wait between data types
            if not self.dry_run:
                time.sleep(5)

            # Scrape advanced totals
            advanced_success = self.scrape_advanced_totals(season)
            if advanced_success:
                total_success += 1
            else:
                total_failures += 1

        # Print summary
        print()
        print("=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Seasons scraped:     {len(seasons_to_scrape)}")
        print(f"Data types per season: 2 (season totals + advanced totals)")
        print(f"Total requests:      {self.stats['requests']}")
        print(f"Successful:          {total_success}")
        print(f"Failed:              {total_failures}")
        print(f"Errors:              {self.stats['errors']}")
        print(f"Retries:             {self.stats['retries']}")
        print("=" * 70)
        print()

        if total_failures == 0:
            print("✅ All data scraped successfully!")
        else:
            print(f"⚠️  {total_failures} scraping operations failed")

        if not self.dry_run and self.s3_client:
            print()
            print("Next step: Re-integrate into local database")
            print("  python scripts/etl/integrate_basketball_reference_aggregate.py")


def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference Incremental Scraper - Daily updates only",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape current season only (default)
  python scripts/etl/basketball_reference_incremental_scraper.py

  # Scrape current + previous season (end-of-season updates)
  python scripts/etl/basketball_reference_incremental_scraper.py --also-previous-season

  # Dry run (don't upload to S3 or save files)
  python scripts/etl/basketball_reference_incremental_scraper.py --dry-run

Purpose:
  Designed for nightly automation. Only fetches current season aggregate data.
  For historical backfills, use: scripts/etl/scrape_basketball_reference_complete.py

During the season:
  - Player stats update as games are played
  - New players are added (call-ups, trades)
  - Run nightly to keep stats current

Off-season:
  - Previous season finalized stats
  - No current season data yet
        """
    )

    parser.add_argument(
        '--also-previous-season',
        action='store_true',
        help='Also scrape previous season (for end-of-season finalized stats)'
    )

    parser.add_argument(
        '--upload-to-s3',
        action='store_true',
        help='Upload scraped data to S3'
    )

    parser.add_argument(
        '--s3-bucket',
        default='nba-sim-raw-data-lake',
        help='S3 bucket name (default: nba-sim-raw-data-lake)'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=12.0,
        help='Seconds between requests (default: 12.0)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - don\'t save files or upload to S3'
    )

    args = parser.parse_args()

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create scraper and run
    scraper = BasketballReferenceIncrementalScraper(
        s3_bucket=args.s3_bucket if args.upload_to_s3 else None,
        rate_limit=args.rate_limit,
        dry_run=args.dry_run
    )

    scraper.scrape_incremental(also_previous_season=args.also_previous_season)

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()

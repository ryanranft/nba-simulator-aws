#!/usr/bin/env python3
"""
Basketball Reference Transactions Scraper

Scrapes NBA player transactions (trades, signings, waivers, releases) from
Basketball Reference to help fill data quality gaps and explain player movement.

Transaction types:
- Signings (free agent, multi-year, two-way, contract extensions)
- Waivers (team releases player)
- Trades (multi-team deals with players and draft picks)
- G-League assignments/recalls
- Injury designations

Value for data quality:
- Explains why players appear on different teams mid-season
- Helps validate roster data from ESPN/hoopR
- Identifies two-way players (may have inconsistent data)
- Tracks draft pick trades (context for team rosters)

URL structure:
- https://www.basketball-reference.com/leagues/NBA_YYYY_transactions.html
- BAA era: https://www.basketball-reference.com/leagues/BAA_YYYY_transactions.html

Data structure:
- Grouped by date (chronological)
- Each transaction: date, type, player(s), team(s), description

Coverage:
- Modern NBA: 2001-present (comprehensive)
- Historical NBA: 1980-2000 (limited)
- BAA/early NBA: Not available

Usage:
    python scripts/etl/scrape_basketball_reference_transactions.py --season 2024
    python scripts/etl/scrape_basketball_reference_transactions.py --start-season 2020 --end-season 2024
    python scripts/etl/scrape_basketball_reference_transactions.py --season 2024 --upload-to-s3

Version: 1.0
Created: October 10, 2025
"""

import argparse
import json
import time
import logging
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("❌ Required libraries not installed")
    print("Install: pip install requests beautifulsoup4 lxml")
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
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class BasketballReferenceTransactionsScraper:
    """Scraper for Basketball Reference transactions data"""

    BASE_URL = "https://www.basketball-reference.com"

    def __init__(self, output_dir: str, s3_bucket: Optional[str] = None,
                 rate_limit: float = 12.0, dry_run: bool = False):
        self.output_dir = Path(output_dir)
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
            'transactions_scraped': 0,
        }

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

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

    def _make_request_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Make HTTP request with retry logic"""
        for attempt in range(max_retries):
            try:
                self._rate_limit_wait()
                self.stats['requests'] += 1

                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    self.stats['successes'] += 1
                    return response.text
                elif response.status_code == 429:
                    self.stats['errors'] += 1
                    if attempt < max_retries - 1:
                        self.stats['retries'] += 1
                        logging.warning(f"  HTTP 429 (Too Many Requests) for {url}")
                        self._exponential_backoff(attempt, is_rate_limit=True)
                    else:
                        logging.error(f"  Failed after {max_retries} attempts: HTTP 429")
                        return None
                elif response.status_code == 404:
                    logging.error(f"  HTTP 404 (Not Found): {url}")
                    self.stats['errors'] += 1
                    return None
                else:
                    self.stats['errors'] += 1
                    if attempt < max_retries - 1:
                        self.stats['retries'] += 1
                        logging.warning(f"  HTTP {response.status_code} for {url}")
                        self._exponential_backoff(attempt)
                    else:
                        logging.error(f"  Failed after {max_retries} attempts: HTTP {response.status_code}")
                        return None

            except requests.exceptions.RequestException as e:
                self.stats['errors'] += 1
                if attempt < max_retries - 1:
                    self.stats['retries'] += 1
                    logging.warning(f"  Request error (attempt {attempt + 1}/{max_retries}): {e}")
                    self._exponential_backoff(attempt)
                else:
                    logging.error(f"  Request failed after {max_retries} attempts: {e}")
                    return None

        return None

    def _parse_player_link(self, element) -> Optional[Dict]:
        """Extract player info from link"""
        if not element:
            return None

        player_link = element.find('a')
        if not player_link:
            return None

        href = player_link.get('href', '')
        player_id = None
        if '/players/' in href:
            player_id = href.split('/')[-1].replace('.html', '')

        return {
            'name': player_link.get_text(strip=True),
            'slug': player_id
        }

    def _extract_players_from_text(self, text: str, soup_element) -> List[Dict]:
        """Extract all player links from a transaction description"""
        players = []
        for link in soup_element.find_all('a', href=True):
            href = link.get('href', '')
            if '/players/' in href:
                player_id = href.split('/')[-1].replace('.html', '')
                players.append({
                    'name': link.get_text(strip=True),
                    'slug': player_id
                })
        return players

    def _classify_transaction(self, text: str) -> str:
        """Classify transaction type from description"""
        text_lower = text.lower()

        if 'signed' in text_lower:
            if 'two-way' in text_lower:
                return 'signed_two_way'
            elif 'contract extension' in text_lower or 'extension' in text_lower:
                return 'contract_extension'
            else:
                return 'signed'
        elif 'waived' in text_lower or 'released' in text_lower:
            return 'waived'
        elif 'traded' in text_lower or 'trade' in text_lower:
            return 'trade'
        elif 'recalled' in text_lower:
            return 'g_league_recalled'
        elif 'assigned' in text_lower:
            return 'g_league_assigned'
        elif 'suspended' in text_lower:
            return 'suspended'
        elif 'injured list' in text_lower or 'injury' in text_lower:
            return 'injury_designation'
        elif 'activated' in text_lower:
            return 'activated'
        elif 'claimed' in text_lower:
            return 'claimed'
        elif 'retired' in text_lower:
            return 'retired'
        else:
            return 'other'

    def _parse_transactions_page(self, html: str, season: int) -> List[Dict]:
        """Parse transactions from HTML"""
        soup = BeautifulSoup(html, 'lxml')

        # Find all list items (grouped by date)
        transactions = []

        # Look for <li> elements containing transaction dates
        for li in soup.find_all('li'):
            # Check if this li contains a date span
            date_span = li.find('span')
            if not date_span:
                continue

            date_text = date_span.get_text(strip=True)

            # Skip if not a date (e.g., navigation elements)
            if not re.match(r'[A-Za-z]+ \d+, \d{4}', date_text):
                continue

            # Parse all transaction paragraphs in this date group
            for p in li.find_all('p'):
                transaction_text = p.get_text(strip=True)

                # Skip empty paragraphs
                if not transaction_text:
                    continue

                # Extract teams (data-attr-from and data-attr-to)
                teams_from = []
                teams_to = []

                for team_link in p.find_all('a', attrs={'data-attr-from': True}):
                    teams_from.append({
                        'abbr': team_link.get('data-attr-from'),
                        'name': team_link.get_text(strip=True)
                    })

                for team_link in p.find_all('a', attrs={'data-attr-to': True}):
                    teams_to.append({
                        'abbr': team_link.get('data-attr-to'),
                        'name': team_link.get_text(strip=True)
                    })

                # Extract players
                players = self._extract_players_from_text(transaction_text, p)

                # Classify transaction type
                transaction_type = self._classify_transaction(transaction_text)

                # Create transaction record
                transaction = {
                    'date': date_text,
                    'season': season,
                    'type': transaction_type,
                    'description': transaction_text,
                    'teams_from': teams_from,
                    'teams_to': teams_to,
                    'players': players
                }

                transactions.append(transaction)

        return transactions

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

    def scrape_season(self, season: int) -> bool:
        """Scrape transactions for a given season"""
        logging.info(f"\n📋 Scraping transactions for {season-1}-{season} season...")

        # Construct URL (use BAA for 1947-1949, NBA otherwise)
        if season <= 1949:
            league = "BAA"
        else:
            league = "NBA"

        url = f"{self.BASE_URL}/leagues/{league}_{season}_transactions.html"
        logging.info(f"  URL: {url}")

        # Fetch HTML
        html = self._make_request_with_retry(url)
        if not html:
            logging.error(f"  Failed to fetch HTML for {season}")
            return False

        # Parse transactions
        transactions = self._parse_transactions_page(html, season)
        if not transactions:
            logging.warning(f"  No transactions found for {season}")
            # Still return True (page exists but no transactions)
            return True

        logging.info(f"  ✓ Parsed {len(transactions)} transactions")
        self.stats['transactions_scraped'] += len(transactions)

        # Save locally
        local_path = self.output_dir / 'transactions' / str(season) / 'transactions.json'
        self._save_json(transactions, local_path)

        # Upload to S3
        if self.s3_client:
            s3_key = f'basketball_reference/transactions/{season}/transactions.json'
            self._upload_to_s3(local_path, s3_key)

        return True

    def scrape_range(self, start_season: int, end_season: int):
        """Scrape multiple seasons"""
        print("=" * 70)
        print("BASKETBALL REFERENCE TRANSACTIONS SCRAPER")
        print("=" * 70)
        print()

        print(f"Seasons to scrape: {start_season} - {end_season}")
        print(f"Rate limit: {self.rate_limit}s between requests")
        print(f"S3 upload: {'Enabled' if self.s3_client else 'Disabled'}")
        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
        print()

        total_seasons = end_season - start_season + 1
        successful = 0
        failed = 0

        for season in range(start_season, end_season + 1):
            logging.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logging.info(f"Season {season} ({successful + failed + 1}/{total_seasons})")
            logging.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            if self.scrape_season(season):
                successful += 1
            else:
                failed += 1

            # Wait between seasons
            if season < end_season and not self.dry_run:
                time.sleep(5)

        # Print summary
        print()
        print("=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)
        print(f"Seasons attempted:      {total_seasons}")
        print(f"Successful:             {successful}")
        print(f"Failed:                 {failed}")
        print(f"Total requests:         {self.stats['requests']}")
        print(f"Errors:                 {self.stats['errors']}")
        print(f"Retries:                {self.stats['retries']}")
        print(f"Transactions scraped:   {self.stats['transactions_scraped']}")
        print("=" * 70)
        print()

        if failed == 0:
            print("✅ All seasons scraped successfully!")
        else:
            print(f"⚠️  {failed} seasons failed")

        print()
        print("Transaction types collected:")
        print("  - Player signings (free agent, multi-year, two-way)")
        print("  - Contract extensions")
        print("  - Waivers/releases")
        print("  - Trades (multi-team, with draft picks)")
        print("  - G-League assignments/recalls")
        print("  - Injury designations")
        print()

        if not self.dry_run and self.s3_client:
            print("Next step: Integrate transactions into unified database")
            print("  (Future enhancement - transaction validation layer)")


def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference Transactions Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape single season
  python scripts/etl/scrape_basketball_reference_transactions.py --season 2024 --upload-to-s3

  # Scrape multiple seasons
  python scripts/etl/scrape_basketball_reference_transactions.py --start-season 2020 --end-season 2024 --upload-to-s3

  # Dry run
  python scripts/etl/scrape_basketball_reference_transactions.py --season 2024 --dry-run

Purpose:
  Scrapes NBA player transactions to help explain data quality gaps and validate
  player rosters. Includes trades, signings, waivers, G-League moves, etc.

Coverage:
  - Modern NBA: 2001-present (comprehensive transaction data)
  - Historical: 1980-2000 (limited availability)
  - BAA/early NBA: Transactions pages not available

Value:
  - Explains mid-season team changes in ESPN/hoopR data
  - Identifies two-way players (may have data inconsistencies)
  - Validates roster composition
  - Provides context for trade deadline activity
        """
    )

    parser.add_argument(
        '--season',
        type=int,
        help='Single season to scrape (e.g., 2024 for 2023-2024 season)'
    )

    parser.add_argument(
        '--start-season',
        type=int,
        help='Start season (e.g., 2020 for 2019-2020 season)'
    )

    parser.add_argument(
        '--end-season',
        type=int,
        help='End season (e.g., 2024 for 2023-2024 season)'
    )

    parser.add_argument(
        '--output-dir',
        default='/tmp/basketball_reference_transactions',
        help='Output directory for scraped data (default: /tmp/basketball_reference_transactions)'
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

    # Validate arguments
    if args.season:
        start_season = args.season
        end_season = args.season
    elif args.start_season and args.end_season:
        start_season = args.start_season
        end_season = args.end_season
    else:
        parser.error("Must specify either --season or both --start-season and --end-season")

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create scraper and run
    scraper = BasketballReferenceTransactionsScraper(
        output_dir=args.output_dir,
        s3_bucket=args.s3_bucket if args.upload_to_s3 else None,
        rate_limit=args.rate_limit,
        dry_run=args.dry_run
    )

    scraper.scrape_range(start_season, end_season)

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()

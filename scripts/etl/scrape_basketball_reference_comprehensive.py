#!/usr/bin/env python3
"""
Basketball Reference Comprehensive Scraper - All Data Types

Scrapes multiple data types from Basketball Reference in a single efficient run.
Designed to collect all valuable data sources identified in the data source analysis.

Data types available:
1. Draft (1947-2025) - Player draft position, college, career stats
2. Awards (1946-2025) - MVP, All-NBA, All-Star, DPOY, ROY, etc.
3. Per-Game Stats (1947-2025) - Normalized stats by games played
4. Shooting Stats (2000-2025) - Shot location and distribution
5. Play-by-Play Stats (2001-2025) - On/off court, positional data
6. Team Ratings (1974-2025) - Offensive/defensive efficiency
7. Playoff Stats (1947-2025) - Postseason performance
8. Coach Records (1947-2025) - Coaching records by season
9. Standings by Date (1947-2025) - Team records over time

Strategy:
- Scrape multiple data types per season in one request cycle
- Rate limit: 12.0s between requests
- Parallel data type collection where possible
- Upload to S3: basketball_reference/{data_type}/{season}/

Usage:
    # Scrape all data types for a season
    python scripts/etl/scrape_basketball_reference_comprehensive.py --season 2024 --all

    # Scrape specific data types
    python scripts/etl/scrape_basketball_reference_comprehensive.py --season 2024 --draft --awards --per-game

    # Scrape range with specific types
    python scripts/etl/scrape_basketball_reference_comprehensive.py --start-season 2020 --end-season 2024 --draft --shooting

    # Dry run
    python scripts/etl/scrape_basketball_reference_comprehensive.py --season 2024 --all --dry-run

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
from typing import Optional, List, Dict, Set
from urllib.parse import urljoin
from collections import defaultdict

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

# Data type configurations
DATA_TYPE_CONFIGS = {
    'draft': {
        'url_pattern': '/draft/NBA_{season}.html',
        'min_year': 1947,
        's3_prefix': 'basketball_reference/draft',
        'filename': 'draft.json'
    },
    'awards': {
        'url_pattern': '/leagues/NBA_{season}.html',  # Extract from season page
        'min_year': 1946,
        's3_prefix': 'basketball_reference/awards',
        'filename': 'awards.json'
    },
    'per_game': {
        'url_pattern': '/leagues/NBA_{season}_per_game.html',
        'min_year': 1947,
        's3_prefix': 'basketball_reference/per_game',
        'filename': 'per_game_stats.json'
    },
    'shooting': {
        'url_pattern': '/leagues/NBA_{season}_shooting.html',
        'min_year': 2000,
        's3_prefix': 'basketball_reference/shooting',
        'filename': 'shooting_stats.json'
    },
    'play_by_play': {
        'url_pattern': '/leagues/NBA_{season}_play-by-play.html',
        'min_year': 2001,
        's3_prefix': 'basketball_reference/play_by_play',
        'filename': 'play_by_play_stats.json'
    },
    'team_ratings': {
        'url_pattern': '/leagues/NBA_{season}_ratings.html',
        'min_year': 1974,
        's3_prefix': 'basketball_reference/team_ratings',
        'filename': 'team_ratings.json'
    },
    'playoffs': {
        'url_pattern': '/playoffs/NBA_{season}_per_game.html',
        'min_year': 1947,
        's3_prefix': 'basketball_reference/playoffs',
        'filename': 'playoff_stats.json'
    },
    'coaches': {
        'url_pattern': '/leagues/NBA_{season}_coaches.html',
        'min_year': 1947,
        's3_prefix': 'basketball_reference/coaches',
        'filename': 'coach_records.json'
    },
    'standings_by_date': {
        'url_pattern': '/leagues/NBA_{season}_standings_by_date.html',
        'min_year': 1947,
        's3_prefix': 'basketball_reference/standings_by_date',
        'filename': 'standings_by_date.json'
    }
}


class BasketballReferenceComprehensiveScraper:
    """Comprehensive scraper for all Basketball Reference data types"""

    BASE_URL = "https://www.basketball-reference.com"

    def __init__(self, output_dir: str, s3_bucket: Optional[str] = None,
                 rate_limit: float = 12.0, dry_run: bool = False):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.dry_run = dry_run

        # Statistics by data type
        self.stats = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'errors': 0,
            'records': 0
        })

        # Global request stats
        self.global_stats = {
            'requests': 0,
            'successes': 0,
            'errors': 0,
            'retries': 0
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
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _exponential_backoff(self, attempt: int, is_rate_limit: bool = False):
        """Exponential backoff on errors"""
        if is_rate_limit:
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
                self.global_stats['requests'] += 1

                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    self.global_stats['successes'] += 1
                    return response.text
                elif response.status_code == 429:
                    self.global_stats['errors'] += 1
                    if attempt < max_retries - 1:
                        self.global_stats['retries'] += 1
                        logging.warning(f"  HTTP 429 (Too Many Requests)")
                        self._exponential_backoff(attempt, is_rate_limit=True)
                    else:
                        logging.error(f"  Failed after {max_retries} attempts: HTTP 429")
                        return None
                elif response.status_code == 404:
                    logging.debug(f"  HTTP 404 (Not Found): {url}")
                    self.global_stats['errors'] += 1
                    return None
                else:
                    self.global_stats['errors'] += 1
                    if attempt < max_retries - 1:
                        self.global_stats['retries'] += 1
                        self._exponential_backoff(attempt)
                    else:
                        logging.error(f"  Failed: HTTP {response.status_code}")
                        return None

            except requests.exceptions.RequestException as e:
                self.global_stats['errors'] += 1
                if attempt < max_retries - 1:
                    self.global_stats['retries'] += 1
                    self._exponential_backoff(attempt)
                else:
                    logging.error(f"  Request failed: {e}")
                    return None

        return None

    def _parse_table_generic(self, soup: BeautifulSoup, table_id: str) -> List[Dict]:
        """Generic table parser for most Basketball Reference tables"""
        table = soup.find('table', {'id': table_id})
        if not table:
            return []

        records = []
        tbody = table.find('tbody')
        if not tbody:
            return []

        # Get headers
        thead = table.find('thead')
        headers = []
        if thead:
            header_row = thead.find('tr')
            if header_row:
                for th in header_row.find_all('th'):
                    stat = th.get('data-stat', th.get_text(strip=True).lower().replace(' ', '_'))
                    headers.append(stat)

        for row in tbody.find_all('tr'):
            # Skip header rows mid-table
            if row.get('class') and 'thead' in row.get('class'):
                continue

            record = {}
            for i, cell in enumerate(row.find_all(['th', 'td'])):
                stat_name = cell.get('data-stat', f'col_{i}')

                # Extract player link if available
                if stat_name == 'player' or 'name' in stat_name:
                    link = cell.find('a')
                    if link and 'href' in link.attrs:
                        href = link['href']
                        if '/players/' in href:
                            record['player_slug'] = href.split('/')[-1].replace('.html', '')

                # Get cell value
                text = cell.get_text(strip=True)
                record[stat_name] = text if text else None

            if record:
                records.append(record)

        return records

    def scrape_draft(self, season: int) -> Optional[Dict]:
        """Scrape draft data for a season"""
        url = f"{self.BASE_URL}/draft/NBA_{season}.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')
        players = self._parse_table_generic(soup, 'stats')

        self.stats['draft']['records'] += len(players)

        return {
            'season': season,
            'draft_year': season,
            'players': players
        }

    def scrape_per_game(self, season: int) -> Optional[Dict]:
        """Scrape per-game stats for a season"""
        url = f"{self.BASE_URL}/leagues/NBA_{season}_per_game.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')
        players = self._parse_table_generic(soup, 'per_game_stats')

        self.stats['per_game']['records'] += len(players)

        return {
            'season': season,
            'players': players
        }

    def scrape_shooting(self, season: int) -> Optional[Dict]:
        """Scrape shooting stats for a season"""
        url = f"{self.BASE_URL}/leagues/NBA_{season}_shooting.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')
        players = self._parse_table_generic(soup, 'shooting')

        self.stats['shooting']['records'] += len(players)

        return {
            'season': season,
            'players': players
        }

    def scrape_play_by_play(self, season: int) -> Optional[Dict]:
        """Scrape play-by-play stats for a season"""
        url = f"{self.BASE_URL}/leagues/NBA_{season}_play-by-play.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')
        players = self._parse_table_generic(soup, 'pbp_stats')

        self.stats['play_by_play']['records'] += len(players)

        return {
            'season': season,
            'players': players
        }

    def scrape_team_ratings(self, season: int) -> Optional[Dict]:
        """Scrape team ratings for a season"""
        url = f"{self.BASE_URL}/leagues/NBA_{season}_ratings.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')
        teams = self._parse_table_generic(soup, 'ratings')

        self.stats['team_ratings']['records'] += len(teams)

        return {
            'season': season,
            'teams': teams
        }

    def scrape_playoffs(self, season: int) -> Optional[Dict]:
        """Scrape playoff stats for a season"""
        url = f"{self.BASE_URL}/playoffs/NBA_{season}_per_game.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')
        players = self._parse_table_generic(soup, 'per_game_stats')

        self.stats['playoffs']['records'] += len(players)

        return {
            'season': season,
            'players': players
        }

    def scrape_coaches(self, season: int) -> Optional[Dict]:
        """Scrape coach records for a season"""
        url = f"{self.BASE_URL}/leagues/NBA_{season}_coaches.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')
        coaches = self._parse_table_generic(soup, 'NBA_coaches')

        self.stats['coaches']['records'] += len(coaches)

        return {
            'season': season,
            'coaches': coaches
        }

    def scrape_standings_by_date(self, season: int) -> Optional[Dict]:
        """Scrape standings by date for a season"""
        url = f"{self.BASE_URL}/leagues/NBA_{season}_standings_by_date.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')

        # Multiple tables (one per team)
        all_standings = []
        for table in soup.find_all('table', {'class': 'stats_table'}):
            team_standings = self._parse_table_generic(soup, table.get('id'))
            if team_standings:
                all_standings.extend(team_standings)

        self.stats['standings_by_date']['records'] += len(all_standings)

        return {
            'season': season,
            'standings': all_standings
        }

    def scrape_awards(self, season: int) -> Optional[Dict]:
        """Scrape awards for a season (from season summary page)"""
        from bs4 import Comment

        url = f"{self.BASE_URL}/leagues/NBA_{season}.html"
        html = self._make_request_with_retry(url)

        if not html:
            return None

        # Basketball Reference hides awards in HTML comments
        soup = BeautifulSoup(html, 'lxml')
        awards = {}

        # Find all HTML comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))

        # Parse award tables from comments
        award_tables = {
            'all_awards': 'league_awards',
            'all_nba_1': 'all_nba_first',
            'all_nba_2': 'all_nba_second',
            'all_nba_3': 'all_nba_third',
            'all_star_game_rosters': 'all_star',
            'all_defense_1': 'all_defense_first',
            'all_defense_2': 'all_defense_second'
        }

        for comment in comments:
            comment_str = str(comment)

            # Check if this comment contains any award table
            for table_id, award_type in award_tables.items():
                if table_id in comment_str:
                    # Parse the comment as HTML
                    comment_soup = BeautifulSoup(comment_str, 'lxml')
                    table_data = self._parse_table_generic(comment_soup, table_id)

                    if table_data:
                        awards[award_type] = table_data

        self.stats['awards']['records'] += sum(len(v) for v in awards.values())

        return {
            'season': season,
            'awards': awards
        }

    def _save_json(self, data: any, filepath: Path):
        """Save data to JSON file"""
        if self.dry_run:
            logging.debug(f"  [DRY RUN] Would save to: {filepath}")
            return

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _upload_to_s3(self, local_path: Path, s3_key: str) -> bool:
        """Upload file to S3"""
        if self.dry_run:
            logging.debug(f"  [DRY RUN] Would upload to S3: {s3_key}")
            return True

        if not self.s3_client:
            return False

        try:
            self.s3_client.upload_file(str(local_path), self.s3_bucket, s3_key)
            return True
        except Exception as e:
            logging.error(f"  S3 upload failed: {e}")
            return False

    def scrape_season(self, season: int, data_types: Set[str]) -> Dict[str, bool]:
        """Scrape multiple data types for a season"""
        results = {}

        for data_type in data_types:
            # Check if season is within valid range for this data type
            config = DATA_TYPE_CONFIGS[data_type]
            if season < config['min_year']:
                logging.debug(f"  Skipping {data_type} (min year: {config['min_year']})")
                continue

            # Call appropriate scraper
            scraper_method = getattr(self, f'scrape_{data_type}')
            data = scraper_method(season)

            if data:
                self.stats[data_type]['successes'] += 1

                # Save locally
                local_path = self.output_dir / config['s3_prefix'].split('/')[-1] / str(season) / config['filename']
                self._save_json(data, local_path)

                # Upload to S3
                if self.s3_client:
                    s3_key = f"{config['s3_prefix']}/{season}/{config['filename']}"
                    self._upload_to_s3(local_path, s3_key)

                results[data_type] = True
            else:
                self.stats[data_type]['errors'] += 1
                results[data_type] = False

            self.stats[data_type]['requests'] += 1

        return results

    def scrape_range(self, start_season: int, end_season: int, data_types: Set[str]):
        """Scrape multiple seasons and data types"""
        print("=" * 80)
        print("BASKETBALL REFERENCE COMPREHENSIVE SCRAPER")
        print("=" * 80)
        print()

        print(f"Seasons: {start_season} - {end_season}")
        print(f"Data types: {', '.join(sorted(data_types))}")
        print(f"Rate limit: {self.rate_limit}s between requests")
        print(f"S3 upload: {'Enabled' if self.s3_client else 'Disabled'}")
        if self.dry_run:
            print("⚠️  DRY RUN MODE")
        print()

        total_seasons = end_season - start_season + 1
        season_results = []

        for season in range(start_season, end_season + 1):
            logging.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            logging.info(f"Season {season} ({len(season_results) + 1}/{total_seasons})")
            logging.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            results = self.scrape_season(season, data_types)
            season_results.append((season, results))

            # Log results for this season
            successful = sum(1 for v in results.values() if v)
            logging.info(f"  ✓ Collected {successful}/{len(data_types)} data types")

            # Wait between seasons (unless last season)
            if season < end_season and not self.dry_run:
                time.sleep(2)

        # Print summary
        self._print_summary(start_season, end_season, data_types, season_results)

    def _print_summary(self, start_season: int, end_season: int,
                      data_types: Set[str], season_results: List):
        """Print comprehensive summary"""
        print()
        print("=" * 80)
        print("SCRAPING SUMMARY")
        print("=" * 80)
        print()

        print(f"Seasons: {start_season} - {end_season} ({end_season - start_season + 1} seasons)")
        print(f"Data types: {len(data_types)}")
        print()

        print("GLOBAL STATISTICS:")
        print(f"  Total requests:  {self.global_stats['requests']}")
        print(f"  Successful:      {self.global_stats['successes']}")
        print(f"  Errors:          {self.global_stats['errors']}")
        print(f"  Retries:         {self.global_stats['retries']}")
        print()

        print("BY DATA TYPE:")
        for data_type in sorted(data_types):
            stats = self.stats[data_type]
            print(f"  {data_type:20s} - {stats['successes']:3d} seasons, "
                  f"{stats['records']:6d} records, {stats['errors']:2d} errors")

        print()
        print("=" * 80)

        total_successful = sum(s['successes'] for s in self.stats.values())
        total_records = sum(s['records'] for s in self.stats.values())

        print(f"✅ Collected {total_successful} season-datasets with {total_records:,} total records")

        if not self.dry_run and self.s3_client:
            print()
            print("Data uploaded to S3: basketball_reference/[data_type]/[season]/")


def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference Comprehensive Scraper - All Data Types",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Season arguments
    parser.add_argument('--season', type=int, help='Single season')
    parser.add_argument('--start-season', type=int, help='Start season')
    parser.add_argument('--end-season', type=int, help='End season')

    # Data type arguments
    parser.add_argument('--all', action='store_true', help='Scrape all data types')
    parser.add_argument('--draft', action='store_true', help='Scrape draft data')
    parser.add_argument('--awards', action='store_true', help='Scrape awards')
    parser.add_argument('--per-game', action='store_true', help='Scrape per-game stats')
    parser.add_argument('--shooting', action='store_true', help='Scrape shooting stats')
    parser.add_argument('--play-by-play', action='store_true', help='Scrape play-by-play stats')
    parser.add_argument('--team-ratings', action='store_true', help='Scrape team ratings')
    parser.add_argument('--playoffs', action='store_true', help='Scrape playoff stats')
    parser.add_argument('--coaches', action='store_true', help='Scrape coach records')
    parser.add_argument('--standings-by-date', action='store_true', help='Scrape standings by date')

    # Other arguments
    parser.add_argument('--output-dir', default='/tmp/basketball_reference_comprehensive',
                       help='Output directory')
    parser.add_argument('--upload-to-s3', action='store_true', help='Upload to S3')
    parser.add_argument('--s3-bucket', default='nba-sim-raw-data-lake', help='S3 bucket')
    parser.add_argument('--rate-limit', type=float, default=12.0, help='Rate limit (seconds)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    # Validate season arguments
    if args.season:
        start_season = end_season = args.season
    elif args.start_season and args.end_season:
        start_season = args.start_season
        end_season = args.end_season
    else:
        parser.error("Must specify --season or --start-season and --end-season")

    # Determine data types to scrape
    if args.all:
        data_types = set(DATA_TYPE_CONFIGS.keys())
    else:
        data_types = set()
        if args.draft: data_types.add('draft')
        if args.awards: data_types.add('awards')
        if args.per_game: data_types.add('per_game')
        if args.shooting: data_types.add('shooting')
        if args.play_by_play: data_types.add('play_by_play')
        if args.team_ratings: data_types.add('team_ratings')
        if args.playoffs: data_types.add('playoffs')
        if args.coaches: data_types.add('coaches')
        if args.standings_by_date: data_types.add('standings_by_date')

    if not data_types:
        parser.error("Must specify at least one data type (or use --all)")

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create scraper
    scraper = BasketballReferenceComprehensiveScraper(
        output_dir=args.output_dir,
        s3_bucket=args.s3_bucket if args.upload_to_s3 else None,
        rate_limit=args.rate_limit,
        dry_run=args.dry_run
    )

    # Run scraper
    scraper.scrape_range(start_season, end_season, data_types)

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    main()

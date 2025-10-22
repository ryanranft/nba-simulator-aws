#!/usr/bin/env python3
"""
Basketball Reference HTML Scraper - BAA/Early NBA Data (1946-1952)

Scrapes Basketball Association of America (BAA) and early NBA data via direct HTML parsing.
Required because the basketball_reference_web_scraper Python library rejects pre-1950 years.

Coverage:
- BAA: 1947-1949 (3 years)
- NBA: 1950-1952 (3 years)
- Total: 1947-1952 (6 years)

Note: 1946 data exists but is incomplete (first partial season)

Data collected:
- Season totals (basic stats: G, FG, FGA, FG%, FT, FTA, FT%, AST, PF, PTS)
- Advanced stats not available for most BAA/early NBA years

Strategy:
1. Fetch HTML from Basketball Reference
2. Parse player totals table
3. Convert to same JSON format as existing scraper
4. Upload to S3 under basketball_reference/season_totals/YYYY/
5. Integrate into local database

Usage:
    python scripts/etl/scrape_basketball_reference_html.py --start-season 1947 --end-season 1952
    python scripts/etl/scrape_basketball_reference_html.py --season 1947 --upload-to-s3
    python scripts/etl/scrape_basketball_reference_html.py --season 1950 --dry-run

Version: 1.0
Created: October 10, 2025
"""

import argparse
import json
import time
import logging
import sys
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
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class BasketballReferenceHTMLScraper:
    """HTML scraper for Basketball Reference BAA/early NBA data"""

    BASE_URL = "https://www.basketball-reference.com"

    def __init__(
        self,
        output_dir: str,
        s3_bucket: Optional[str] = None,
        rate_limit: float = 12.0,
        dry_run: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3") if HAS_BOTO3 and s3_bucket else None
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.dry_run = dry_run

        # Statistics
        self.stats = {
            "requests": 0,
            "successes": 0,
            "errors": 0,
            "retries": 0,
            "players_scraped": 0,
        }

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

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
            wait_time = min(120, 30 * (2**attempt))
        else:
            wait_time = min(60, (2**attempt))
        logging.warning(f"  Backing off for {wait_time}s (attempt {attempt})")
        time.sleep(wait_time)

    def _make_request_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Make HTTP request with retry logic"""
        for attempt in range(max_retries):
            try:
                self._rate_limit_wait()
                self.stats["requests"] += 1

                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    self.stats["successes"] += 1
                    return response.text
                elif response.status_code == 429:
                    self.stats["errors"] += 1
                    if attempt < max_retries - 1:
                        self.stats["retries"] += 1
                        logging.warning(f"  HTTP 429 (Too Many Requests) for {url}")
                        self._exponential_backoff(attempt, is_rate_limit=True)
                    else:
                        logging.error(
                            f"  Failed after {max_retries} attempts: HTTP 429"
                        )
                        return None
                elif response.status_code == 404:
                    logging.error(f"  HTTP 404 (Not Found): {url}")
                    self.stats["errors"] += 1
                    return None
                else:
                    self.stats["errors"] += 1
                    if attempt < max_retries - 1:
                        self.stats["retries"] += 1
                        logging.warning(f"  HTTP {response.status_code} for {url}")
                        self._exponential_backoff(attempt)
                    else:
                        logging.error(
                            f"  Failed after {max_retries} attempts: HTTP {response.status_code}"
                        )
                        return None

            except requests.exceptions.RequestException as e:
                self.stats["errors"] += 1
                if attempt < max_retries - 1:
                    self.stats["retries"] += 1
                    logging.warning(
                        f"  Request error (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    self._exponential_backoff(attempt)
                else:
                    logging.error(f"  Request failed after {max_retries} attempts: {e}")
                    return None

        return None

    def _parse_player_totals_table(self, html: str, season: int) -> List[Dict]:
        """Parse player totals table from HTML"""
        soup = BeautifulSoup(html, "lxml")

        # Find the totals_stats table
        table = soup.find("table", {"id": "totals_stats"})
        if not table:
            logging.error("  Could not find totals_stats table")
            return []

        players = []
        tbody = table.find("tbody")
        if not tbody:
            logging.error("  Could not find table tbody")
            return []

        for row in tbody.find_all("tr"):
            # Skip header rows that appear mid-table
            if row.get("class") and "thead" in row.get("class"):
                continue

            # Get all cells
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            try:
                # Extract player data
                player_cell = cells[1]  # Player name is in 2nd column (index 1)
                player_name = player_cell.get_text(strip=True)

                # Skip empty rows
                if not player_name:
                    continue

                # Get player ID from href (if available)
                player_link = player_cell.find("a")
                player_id = None
                if player_link and "href" in player_link.attrs:
                    href = player_link["href"]
                    # Extract player ID from URL like /players/a/abdelal01.html
                    if "/players/" in href:
                        player_id = href.split("/")[-1].replace(".html", "")

                # Skip rows without player IDs (e.g., "League Average" rows)
                if not player_id:
                    continue

                # Map columns (varies by era)
                # BAA/early NBA (1947-1952): Rk, Player, Age, Tm, Pos, G, FG, FGA, FG%, FT, FTA, FT%, AST, PF, PTS, Trp-Dbl, Awards
                # Modern NBA: Rk, Player, Pos, Age, Tm, G, GS, MP, FG, FGA, FG%, 3P, 3PA, 3P%, 2P, 2PA, 2P%, eFG%, FT, FTA, FT%, ORB, DRB, TRB, AST, STL, BLK, TOV, PF, PTS

                # Detect era by checking if cell 3 is team abbreviation (BAA/early) or age (modern)
                # BAA era: cells[2] = age, cells[3] = team, cells[4] = pos
                # Modern: cells[2] = pos, cells[3] = age, cells[4] = team

                # For BAA/early NBA (1947-1952), use simpler column structure
                if season <= 1952:
                    player_data = {
                        "slug": player_id,
                        "name": player_name,
                        "team": self._get_cell_text(cells, 3),  # Team
                        "positions": (
                            [self._get_cell_text(cells, 4)]
                            if self._get_cell_text(cells, 4)
                            else []
                        ),  # Position
                        "age": self._get_cell_int(cells, 2),  # Age
                        "games_played": self._get_cell_int(cells, 5),  # G
                        "games_started": 0,  # Not tracked in BAA/early NBA
                        "minutes_played": 0,  # Not tracked in BAA/early NBA
                        "made_field_goals": self._get_cell_int(cells, 6),  # FG
                        "attempted_field_goals": self._get_cell_int(cells, 7),  # FGA
                        "made_three_point_field_goals": 0,  # Didn't exist in BAA/early NBA
                        "attempted_three_point_field_goals": 0,  # Didn't exist in BAA/early NBA
                        "made_free_throws": self._get_cell_int(cells, 9),  # FT
                        "attempted_free_throws": self._get_cell_int(cells, 10),  # FTA
                        "offensive_rebounds": 0,  # Not tracked in BAA/early NBA
                        "defensive_rebounds": 0,  # Not tracked in BAA/early NBA
                        "assists": self._get_cell_int(cells, 12),  # AST
                        "steals": 0,  # Not tracked in BAA/early NBA
                        "blocks": 0,  # Not tracked in BAA/early NBA
                        "turnovers": 0,  # Not tracked in BAA/early NBA
                        "personal_fouls": self._get_cell_int(cells, 13),  # PF
                        "points": self._get_cell_int(cells, 14),  # PTS
                    }
                else:
                    # Modern NBA column structure
                    player_data = {
                        "slug": player_id,
                        "name": player_name,
                        "team": self._get_cell_text(cells, 4),  # Team
                        "positions": (
                            [self._get_cell_text(cells, 2)]
                            if self._get_cell_text(cells, 2)
                            else []
                        ),  # Position
                        "age": self._get_cell_int(cells, 3),  # Age
                        "games_played": self._get_cell_int(cells, 5),  # G
                        "games_started": self._get_cell_int(cells, 6, default=0),  # GS
                        "minutes_played": self._get_cell_int(cells, 7, default=0),  # MP
                        "made_field_goals": self._get_cell_int(cells, 8),  # FG
                        "attempted_field_goals": self._get_cell_int(cells, 9),  # FGA
                        "made_three_point_field_goals": self._get_cell_int(
                            cells, 11, default=0
                        ),  # 3P
                        "attempted_three_point_field_goals": self._get_cell_int(
                            cells, 12, default=0
                        ),  # 3PA
                        "made_free_throws": self._get_cell_int(cells, 18),  # FT
                        "attempted_free_throws": self._get_cell_int(cells, 19),  # FTA
                        "offensive_rebounds": self._get_cell_int(
                            cells, 21, default=0
                        ),  # ORB
                        "defensive_rebounds": self._get_cell_int(
                            cells, 22, default=0
                        ),  # DRB
                        "assists": self._get_cell_int(cells, 24),  # AST
                        "steals": self._get_cell_int(cells, 25, default=0),  # STL
                        "blocks": self._get_cell_int(cells, 26, default=0),  # BLK
                        "turnovers": self._get_cell_int(cells, 27, default=0),  # TOV
                        "personal_fouls": self._get_cell_int(cells, 28),  # PF
                        "points": self._get_cell_int(cells, 29),  # PTS
                    }

                # Add season
                player_data["season"] = season

                players.append(player_data)

            except Exception as e:
                logging.warning(f"  Error parsing row: {e}")
                continue

        return players

    def _get_cell_text(self, cells: List, index: int, default: str = "") -> str:
        """Safely get cell text"""
        try:
            if index < len(cells):
                return cells[index].get_text(strip=True)
        except:
            pass
        return default

    def _get_cell_int(self, cells: List, index: int, default: int = 0) -> int:
        """Safely get cell integer value"""
        try:
            if index < len(cells):
                text = cells[index].get_text(strip=True)
                if text and text != "":
                    return int(text)
        except:
            pass
        return default

    def _save_json(self, data: any, filepath: Path):
        """Save data to JSON file"""
        if self.dry_run:
            logging.info(f"  [DRY RUN] Would save to: {filepath}")
            return

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
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
        """Scrape season totals for a given season"""
        # Determine league (BAA or NBA)
        if season <= 1949:
            league = "BAA"
        else:
            league = "NBA"

        logging.info(f"\n📊 Scraping {league} {season-1}-{season} season totals...")

        # Construct URL
        url = f"{self.BASE_URL}/leagues/{league}_{season}_totals.html"
        logging.info(f"  URL: {url}")

        # Fetch HTML
        html = self._make_request_with_retry(url)
        if not html:
            logging.error(f"  Failed to fetch HTML for {season}")
            return False

        # Parse table
        players = self._parse_player_totals_table(html, season)
        if not players:
            logging.error(f"  No players found for {season}")
            return False

        logging.info(f"  ✓ Parsed {len(players)} players")
        self.stats["players_scraped"] += len(players)

        # Save locally
        local_path = (
            self.output_dir
            / "season_totals"
            / str(season)
            / "player_season_totals.json"
        )
        self._save_json(players, local_path)

        # Upload to S3
        if self.s3_client:
            s3_key = (
                f"basketball_reference/season_totals/{season}/player_season_totals.json"
            )
            self._upload_to_s3(local_path, s3_key)

        return True

    def scrape_range(self, start_season: int, end_season: int):
        """Scrape multiple seasons"""
        print("=" * 70)
        print("BASKETBALL REFERENCE HTML SCRAPER - BAA/EARLY NBA")
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
        print(f"Seasons attempted:   {total_seasons}")
        print(f"Successful:          {successful}")
        print(f"Failed:              {failed}")
        print(f"Total requests:      {self.stats['requests']}")
        print(f"Errors:              {self.stats['errors']}")
        print(f"Retries:             {self.stats['retries']}")
        print(f"Players scraped:     {self.stats['players_scraped']}")
        print("=" * 70)
        print()

        if failed == 0:
            print("✅ All seasons scraped successfully!")
        else:
            print(f"⚠️  {failed} seasons failed")

        if not self.dry_run and self.s3_client:
            print()
            print("Next step: Re-integrate into local database")
            print("  python scripts/etl/integrate_basketball_reference_aggregate.py")


def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference HTML Scraper - BAA/Early NBA (1946-1952)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all BAA/early NBA years (1947-1952)
  python scripts/etl/scrape_basketball_reference_html.py --start-season 1947 --end-season 1952 --upload-to-s3

  # Scrape single season
  python scripts/etl/scrape_basketball_reference_html.py --season 1947 --upload-to-s3

  # Dry run (don't save or upload)
  python scripts/etl/scrape_basketball_reference_html.py --season 1947 --dry-run

Purpose:
  Scrapes BAA/early NBA data via HTML parsing to bypass basketball_reference_web_scraper
  library limitation that rejects pre-1950 years.

Coverage:
  - BAA: 1947-1949 (3 years)
  - NBA: 1950-1952 (3 years)
  - Total: 1947-1952 (6 years)

Note: 1946 data exists but is incomplete (first partial season)
        """,
    )

    parser.add_argument(
        "--season",
        type=int,
        help="Single season to scrape (e.g., 1947 for 1946-1947 season)",
    )

    parser.add_argument(
        "--start-season",
        type=int,
        help="Start season (e.g., 1947 for 1946-1947 season)",
    )

    parser.add_argument(
        "--end-season", type=int, help="End season (e.g., 1952 for 1951-1952 season)"
    )

    parser.add_argument(
        "--output-dir",
        default="/tmp/basketball_reference_html",
        help="Output directory for scraped data (default: /tmp/basketball_reference_html)",
    )

    parser.add_argument(
        "--upload-to-s3", action="store_true", help="Upload scraped data to S3"
    )

    parser.add_argument(
        "--s3-bucket",
        default="nba-sim-raw-data-lake",
        help="S3 bucket name (default: nba-sim-raw-data-lake)",
    )

    parser.add_argument(
        "--rate-limit",
        type=float,
        default=12.0,
        help="Seconds between requests (default: 12.0)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - don't save files or upload to S3",
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
        parser.error(
            "Must specify either --season or both --start-season and --end-season"
        )

    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create scraper and run
    scraper = BasketballReferenceHTMLScraper(
        output_dir=args.output_dir,
        s3_bucket=args.s3_bucket if args.upload_to_s3 else None,
        rate_limit=args.rate_limit,
        dry_run=args.dry_run,
    )

    scraper.scrape_range(start_season, end_season)

    print()
    print(f"✓ Complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

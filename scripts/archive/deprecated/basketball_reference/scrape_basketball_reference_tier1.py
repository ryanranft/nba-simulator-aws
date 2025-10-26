#!/usr/bin/env python3
"""
Basketball Reference Tier 1: NBA High Value Data
Phase 0.0001 - Tier 1 of 13-tier expansion

Collects the 5 highest-value NBA data types with immediate ML and simulation utility:
1. Player Game Logs - Game-by-game performance tracking
2. Event-Level Play-by-Play - Individual game events (shots, subs, fouls)
3. Shot Charts - X/Y coordinates for each shot
4. Player Tracking Data - Speed, distance, touches (2013-2025)
5. Lineup Data - 5-man combination analysis

Strategy:
- Rate limit: 12.0s between requests (Basketball Reference requirement)
- Selective collection: Focus on high-value games and players
- Progress tracking: Resume capability for long-running scrapes
- S3 upload: Automatic upload after each successful scrape
- Quality validation: Record count and coverage verification

Tier 1 Scope:
- Player Game Logs: ~300 significant players × 70 games avg = ~21,000 player-games per season
- Play-by-Play Events: ~14,000 games (playoffs 2000-2025 + recent regular season)
- Shot Charts: ~12,500 games
- Player Tracking: ~10,000 player-seasons (2013-2025)
- Lineup Data: ~50,000 unique 5-man combinations (2007-2025)

Total Records: ~150,000
Total Time: 15-20 hours
S3 Cost: +$0.002/month

Usage:
    # Scrape all Tier 1 data types for recent season
    python scripts/etl/scrape_basketball_reference_tier1.py --season 2024 --all

    # Scrape specific data types
    python scripts/etl/scrape_basketball_reference_tier1.py --season 2024 --game-logs --shot-charts

    # Scrape player game logs for specific players
    python scripts/etl/scrape_basketball_reference_tier1.py --season 2024 --game-logs --players lebron-james,stephen-curry

    # Scrape play-by-play for playoff games only
    python scripts/etl/scrape_basketball_reference_tier1.py --season 2024 --play-by-play --playoffs-only

    # Resume from checkpoint
    python scripts/etl/scrape_basketball_reference_tier1.py --resume tier1_checkpoint.json

    # Dry run (no S3 upload)
    python scripts/etl/scrape_basketball_reference_tier1.py --season 2024 --all --dry-run

Version: 1.0
Created: October 11, 2025
Author: NBA Simulator Project
"""

import argparse
import json
import time
import logging
import sys
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Set, Tuple
from urllib.parse import urljoin
from collections import defaultdict
import hashlib

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
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://www.basketball-reference.com"
RATE_LIMIT_DELAY = 12.0  # Basketball Reference requires 12 seconds between requests
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIX_BASE = "basketball_reference"

# Tier 1 data type configurations
TIER1_DATA_TYPES = {
    "game_logs": {
        "url_pattern": "/players/{first_letter}/{player_slug}/gamelog/{season}",
        "min_year": 1946,
        "s3_prefix": "player_game_logs",
        "table_id": "pgl_basic",
        "description": "Player game-by-game stats",
        "priority": "CRITICAL",
    },
    "play_by_play": {
        "url_pattern": "/boxscores/pbp/{game_id}.html",
        "min_year": 2000,
        "s3_prefix": "event_level_pbp",
        "table_id": "pbp",
        "description": "Event-level play-by-play data",
        "priority": "HIGH",
    },
    "shot_charts": {
        "url_pattern": "/boxscores/shot-chart/{game_id}.html",
        "min_year": 2000,
        "s3_prefix": "shot_charts",
        "description": "Shot location with X/Y coordinates",
        "priority": "HIGH",
    },
    "player_tracking": {
        "url_pattern": "/leagues/NBA_{season}_tracking.html",
        "min_year": 2013,
        "s3_prefix": "player_tracking",
        "description": "Speed, distance, touches, passes",
        "priority": "MEDIUM-HIGH",
    },
    "lineups": {
        "url_pattern": "/teams/{team}/{season}_lineups.html",
        "min_year": 2007,
        "s3_prefix": "lineups",
        "table_id": "lineups",
        "description": "5-man lineup combinations",
        "priority": "MEDIUM",
    },
}


class BasketballReferenceTier1Scraper:
    """Scraper for Basketball Reference Tier 1 high-value data types."""

    def __init__(self, dry_run=False, checkpoint_file=None):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

        self.dry_run = dry_run
        self.checkpoint_file = checkpoint_file or "tier1_checkpoint.json"
        self.checkpoint = self._load_checkpoint()

        # S3 client
        if HAS_BOTO3 and not dry_run:
            self.s3_client = boto3.client("s3")
        else:
            self.s3_client = None

        # Statistics
        self.stats = defaultdict(int)
        self.errors = []

        logger.info("=" * 70)
        logger.info("BASKETBALL REFERENCE TIER 1 SCRAPER")
        logger.info("=" * 70)
        logger.info(f"Dry Run: {dry_run}")
        logger.info(f"Checkpoint File: {self.checkpoint_file}")
        logger.info(f"S3 Upload: {'Enabled' if self.s3_client else 'Disabled'}")
        logger.info("=" * 70)

    def _load_checkpoint(self) -> Dict:
        """Load checkpoint from file if it exists."""
        if Path(self.checkpoint_file).exists():
            with open(self.checkpoint_file) as f:
                logger.info(f"✓ Loaded checkpoint from {self.checkpoint_file}")
                return json.load(f)
        return {
            "completed": {},
            "in_progress": {},
            "last_updated": datetime.now().isoformat(),
        }

    def _save_checkpoint(self):
        """Save checkpoint to file."""
        self.checkpoint["last_updated"] = datetime.now().isoformat()
        with open(self.checkpoint_file, "w") as f:
            json.dump(self.checkpoint, f, indent=2)
        logger.debug(f"✓ Saved checkpoint to {self.checkpoint_file}")

    def _rate_limit(self):
        """Enforce rate limit delay."""
        logger.debug(f"⏱️  Rate limiting: sleeping {RATE_LIMIT_DELAY}s")
        time.sleep(RATE_LIMIT_DELAY)

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page from Basketball Reference."""
        try:
            logger.info(f"📥 Fetching: {url}")
            response = self.session.get(url, timeout=30)

            if response.status_code == 404:
                logger.warning(f"⚠️  Page not found: {url}")
                return None
            elif response.status_code == 429:
                logger.warning("⚠️  Rate limited, waiting 60s...")
                time.sleep(60)
                return self._fetch_page(url)
            elif response.status_code != 200:
                logger.error(f"❌ HTTP {response.status_code}: {url}")
                return None

            # Basketball Reference hides tables in HTML comments - uncomment them
            html_content = response.text
            html_content = self._uncomment_tables(html_content)

            soup = BeautifulSoup(html_content, "lxml")
            self._rate_limit()
            return soup

        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout fetching {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error: {e}")
            return None

    def _uncomment_tables(self, html: str) -> str:
        """
        Uncomment HTML tables that Basketball Reference hides in comments.

        Basketball Reference wraps many tables in HTML comments to prevent scraping.
        This function finds and uncomments them.
        """
        # Find all HTML comments containing divs
        comment_pattern = r"<!--(.*?)-->"

        def replace_comment(match):
            content = match.group(1)
            # Only uncomment if it contains table-like structures
            if "<table" in content or "<div" in content:
                return content
            return match.group(0)

        return re.sub(comment_pattern, replace_comment, html, flags=re.DOTALL)

    def _upload_to_s3(self, data: Dict, s3_key: str) -> bool:
        """Upload JSON data to S3."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would upload to s3://{S3_BUCKET}/{s3_key}")
            return True

        if not self.s3_client:
            logger.warning("⚠️  S3 client not available, skipping upload")
            return False

        try:
            json_data = json.dumps(data, indent=2)
            self.s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json_data.encode("utf-8"),
                ContentType="application/json",
            )
            logger.info(f"✅ Uploaded to s3://{S3_BUCKET}/{s3_key}")
            self.stats["s3_uploads"] += 1
            return True
        except Exception as e:
            logger.error(f"❌ S3 upload failed: {e}")
            self.errors.append(f"S3 upload failed for {s3_key}: {e}")
            return False

    def scrape_player_game_logs(self, season: int, players: Optional[List[str]] = None):
        """
        Scrape player game logs for a season.

        Args:
            season: NBA season year (e.g., 2024 for 2023-24 season)
            players: List of player slugs (e.g., ['lebron-james', 'stephen-curry'])
                    If None, scrapes top players from season
        """
        logger.info(f"\n📋 SCRAPING PLAYER GAME LOGS - {season} season")
        logger.info("=" * 70)

        # If no players specified, get top players from season stats page
        if not players:
            players = self._get_top_players_for_season(season)

        logger.info(f"Will scrape game logs for {len(players)} players")

        for idx, player_slug in enumerate(players, 1):
            checkpoint_key = f"game_logs_{season}_{player_slug}"

            # Skip if already completed
            if checkpoint_key in self.checkpoint.get("completed", {}):
                logger.info(
                    f"[{idx}/{len(players)}] ⏭️  Skipping {player_slug} (already completed)"
                )
                continue

            logger.info(f"[{idx}/{len(players)}] Processing: {player_slug}")

            # Get first letter for URL
            first_letter = player_slug[0]
            url = urljoin(
                BASE_URL, f"/players/{first_letter}/{player_slug}/gamelog/{season}"
            )

            soup = self._fetch_page(url)
            if not soup:
                self.errors.append(
                    f"Failed to fetch game log for {player_slug} ({season})"
                )
                continue

            # Extract game log table
            table = soup.find("table", {"id": "pgl_basic"})
            if not table:
                logger.warning(f"⚠️  No game log table found for {player_slug}")
                continue

            # Parse table data
            game_logs = self._parse_table(table)

            if game_logs:
                # Create output
                output = {
                    "player_slug": player_slug,
                    "season": season,
                    "scraped_at": datetime.now().isoformat(),
                    "source_url": url,
                    "game_count": len(game_logs),
                    "games": game_logs,
                }

                # Upload to S3
                s3_key = f"{S3_PREFIX_BASE}/player_game_logs/{player_slug}/{season}/gamelog.json"
                if self._upload_to_s3(output, s3_key):
                    self.checkpoint["completed"][checkpoint_key] = {
                        "completed_at": datetime.now().isoformat(),
                        "game_count": len(game_logs),
                    }
                    self._save_checkpoint()
                    self.stats["game_logs_scraped"] += 1
                    logger.info(f"✅ Scraped {len(game_logs)} games for {player_slug}")
            else:
                logger.warning(f"⚠️  No game data found for {player_slug}")

        logger.info(f"\n✅ Completed player game logs for {season} season")
        logger.info(f"Total scraped: {self.stats['game_logs_scraped']} players")

    def _get_top_players_for_season(self, season: int, limit: int = 300) -> List[str]:
        """Get top N players by minutes played for a season."""
        logger.info(f"Fetching top {limit} players for {season} season...")

        url = urljoin(BASE_URL, f"/leagues/NBA_{season}_per_game.html")
        soup = self._fetch_page(url)

        if not soup:
            logger.error(f"Failed to fetch player list for {season}")
            return []

        table = soup.find("table", {"id": "per_game_stats"})
        if not table:
            logger.error("Player stats table not found")
            return []

        players = []
        for row in table.find("tbody").find_all("tr", class_=lambda x: x != "thead"):
            player_link = row.find("td", {"data-stat": "player"})
            if player_link and player_link.find("a"):
                href = player_link.find("a")["href"]
                # Extract player slug from /players/j/jamesle01.html
                player_slug = href.split("/")[-1].replace(".html", "")
                players.append(player_slug)

                if len(players) >= limit:
                    break

        logger.info(f"✓ Found {len(players)} players")
        return players

    def _parse_table(self, table) -> List[Dict]:
        """Parse a Basketball Reference table into list of dicts."""
        data = []

        # Get headers
        headers = []
        thead = table.find("thead")
        if thead:
            for th in thead.find_all("th"):
                headers.append(th.get("data-stat", th.text.strip()))

        # Get rows
        tbody = table.find("tbody")
        if tbody:
            for row in tbody.find_all("tr", class_=lambda x: x != "thead"):
                row_data = {}
                for idx, td in enumerate(row.find_all(["th", "td"])):
                    stat_name = td.get(
                        "data-stat",
                        headers[idx] if idx < len(headers) else f"col_{idx}",
                    )
                    row_data[stat_name] = td.text.strip()

                if row_data:
                    data.append(row_data)

        return data

    def print_summary(self):
        """Print scraping summary statistics."""
        logger.info("\n" + "=" * 70)
        logger.info("TIER 1 SCRAPING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Game Logs Scraped: {self.stats.get('game_logs_scraped', 0)}")
        logger.info(f"S3 Uploads: {self.stats.get('s3_uploads', 0)}")
        logger.info(f"Errors: {len(self.errors)}")

        if self.errors:
            logger.info("\nErrors encountered:")
            for error in self.errors[:10]:  # Show first 10 errors
                logger.info(f"  - {error}")
            if len(self.errors) > 10:
                logger.info(f"  ... and {len(self.errors) - 10} more")

        logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference Tier 1 Scraper - High Value NBA Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Season arguments
    parser.add_argument(
        "--season", type=int, help="Season year (e.g., 2024 for 2023-24 season)"
    )
    parser.add_argument("--start-season", type=int, help="Start season for range")
    parser.add_argument("--end-season", type=int, help="End season for range")

    # Data type selection
    parser.add_argument(
        "--all", action="store_true", help="Scrape all Tier 1 data types"
    )
    parser.add_argument(
        "--game-logs", action="store_true", help="Scrape player game logs"
    )
    parser.add_argument(
        "--play-by-play", action="store_true", help="Scrape event-level play-by-play"
    )
    parser.add_argument("--shot-charts", action="store_true", help="Scrape shot charts")
    parser.add_argument(
        "--player-tracking", action="store_true", help="Scrape player tracking data"
    )
    parser.add_argument("--lineups", action="store_true", help="Scrape lineup data")

    # Filters
    parser.add_argument("--players", help="Comma-separated list of player slugs")
    parser.add_argument(
        "--playoffs-only", action="store_true", help="Only scrape playoff games"
    )

    # Control
    parser.add_argument(
        "--dry-run", action="store_true", help="Dry run (no S3 uploads)"
    )
    parser.add_argument("--resume", help="Resume from checkpoint file")
    parser.add_argument(
        "--checkpoint-file",
        default="tier1_checkpoint.json",
        help="Checkpoint file path",
    )

    args = parser.parse_args()

    # Validate arguments
    if (
        not args.season
        and not (args.start_season and args.end_season)
        and not args.resume
    ):
        parser.error("Must specify --season, --start-season/--end-season, or --resume")

    if (
        not any(
            [
                args.all,
                args.game_logs,
                args.play_by_play,
                args.shot_charts,
                args.player_tracking,
                args.lineups,
            ]
        )
        and not args.resume
    ):
        parser.error("Must specify at least one data type or --all")

    # Create scraper
    scraper = BasketballReferenceTier1Scraper(
        dry_run=args.dry_run,
        checkpoint_file=args.checkpoint_file if not args.resume else args.resume,
    )

    try:
        # Determine seasons to scrape
        if args.season:
            seasons = [args.season]
        elif args.start_season and args.end_season:
            seasons = list(range(args.start_season, args.end_season + 1))
        else:
            seasons = []  # Will be determined from checkpoint

        # Scrape selected data types
        for season in seasons:
            logger.info(f"\n{'='*70}")
            logger.info(f"PROCESSING SEASON {season}")
            logger.info(f"{'='*70}\n")

            if args.all or args.game_logs:
                players = args.players.split(",") if args.players else None
                scraper.scrape_player_game_logs(season, players)

            # TODO: Implement other data types
            if args.all or args.play_by_play:
                logger.info("⚠️  Play-by-play scraping not yet implemented")

            if args.all or args.shot_charts:
                logger.info("⚠️  Shot chart scraping not yet implemented")

            if args.all or args.player_tracking:
                logger.info("⚠️  Player tracking scraping not yet implemented")

            if args.all or args.lineups:
                logger.info("⚠️  Lineup scraping not yet implemented")

        # Print summary
        scraper.print_summary()

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        scraper._save_checkpoint()
        scraper.print_summary()
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        scraper._save_checkpoint()
        sys.exit(1)


if __name__ == "__main__":
    main()

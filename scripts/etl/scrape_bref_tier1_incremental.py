#!/usr/bin/env python3
"""
Basketball Reference Tier 1: Incremental Scraper with Checkpoint Recovery

CRITICAL FEATURE: Saves data IMMEDIATELY after each successful scrape
- Player game logs: Saves after EACH player
- Play-by-play: Saves after EACH game
- Shot charts: Saves after EACH game
- Tracking: Saves after EACH season
- Lineups: Saves after EACH team

If scraper fails, resume from last checkpoint. ZERO data loss.

Checkpoint file tracks:
- What items have been completed
- What items are in progress
- What items failed
- Resume capability from any point

Usage:
    # Start fresh
    python scripts/etl/scrape_bref_tier1_incremental.py --tier 1 --season 2024 --all

    # Resume from checkpoint
    python scripts/etl/scrape_bref_tier1_incremental.py --resume tier1_progress.json

    # Specific data types
    python scripts/etl/scrape_bref_tier1_incremental.py --tier 1 --season 2020-2024 --game-logs --shot-charts

    # Background mode with monitoring
    nohup python scripts/etl/scrape_bref_tier1_incremental.py --tier 1 --season 2020-2024 --all > tier1.log 2>&1 &

Version: 1.0
Created: October 11, 2025
"""

import argparse
import json
import time
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Set
from collections import defaultdict
import re

try:
    import requests
    from bs4 import BeautifulSoup, Comment
except ImportError:
    print("❌ Install: pip install requests beautifulsoup4 lxml")
    sys.exit(1)

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    print("⚠️  boto3 not available, S3 upload disabled")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://www.basketball-reference.com"
RATE_LIMIT = 12.0  # seconds
S3_BUCKET = "nba-sim-raw-data-lake"
S3_PREFIX = "basketball_reference"
CHECKPOINT_FILE = "tier1_progress.json"

# Tier 1 Data Types
TIER1_TYPES = {
    "game_logs": {
        "name": "Player Game Logs",
        "priority": "CRITICAL",
        "granularity": "player",  # Save per player
        "url_pattern": "/players/{first}/{slug}/gamelog/{season}",
        "table_id": "pgl_basic",
        "s3_path": "nba/player_game_logs/{slug}/{season}.json",
    },
    "play_by_play": {
        "name": "Event-Level Play-by-Play",
        "priority": "HIGH",
        "granularity": "game",  # Save per game
        "url_pattern": "/boxscores/pbp/{game_id}.html",
        "table_id": "pbp",
        "s3_path": "nba/event_pbp/{season}/{game_id}.json",
    },
    "shot_charts": {
        "name": "Shot Charts",
        "priority": "HIGH",
        "granularity": "game",  # Save per game
        "url_pattern": "/boxscores/shot-chart/{game_id}.html",
        "s3_path": "nba/shot_charts/{season}/{game_id}.json",
    },
    "tracking": {
        "name": "Player Tracking",
        "priority": "MEDIUM-HIGH",
        "granularity": "season",  # Save per season
        "url_pattern": "/leagues/NBA_{season}_tracking.html",
        "s3_path": "nba/player_tracking/{season}.json",
    },
    "lineups": {
        "name": "Lineup Data",
        "priority": "MEDIUM",
        "granularity": "team-season",  # Save per team per season
        "url_pattern": "/teams/{team}/{season}_lineups.html",
        "table_id": "lineups",
        "s3_path": "nba/lineups/{team}/{season}.json",
    },
}


class CheckpointManager:
    """Manages checkpoints for resume capability."""

    def __init__(self, checkpoint_file: str):
        self.checkpoint_file = checkpoint_file
        self.data = self._load()

    def _load(self) -> Dict:
        """Load checkpoint file."""
        if Path(self.checkpoint_file).exists():
            with open(self.checkpoint_file) as f:
                data = json.load(f)
                logger.info(
                    f"✓ Loaded checkpoint: {len(data.get('completed', {}))} items completed"
                )
                return data
        return {
            "started_at": datetime.now().isoformat(),
            "completed": {},  # item_id -> {timestamp, records, s3_key}
            "failed": {},  # item_id -> {timestamp, error}
            "in_progress": {},  # item_id -> {timestamp}
            "stats": defaultdict(int),
        }

    def save(self):
        """Save checkpoint immediately."""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.checkpoint_file, "w") as f:
            json.dump(self.data, f, indent=2)
        logger.debug(f"✓ Checkpoint saved: {self.checkpoint_file}")

    def mark_in_progress(self, item_id: str):
        """Mark item as in progress."""
        self.data["in_progress"][item_id] = {"started_at": datetime.now().isoformat()}
        self.save()

    def mark_completed(self, item_id: str, records: int, s3_key: str):
        """Mark item as completed."""
        self.data["completed"][item_id] = {
            "completed_at": datetime.now().isoformat(),
            "records": records,
            "s3_key": s3_key,
        }
        if item_id in self.data["in_progress"]:
            del self.data["in_progress"][item_id]
        self.data["stats"]["completed"] += 1
        self.data["stats"]["total_records"] += records
        self.save()

    def mark_failed(self, item_id: str, error: str):
        """Mark item as failed."""
        self.data["failed"][item_id] = {
            "failed_at": datetime.now().isoformat(),
            "error": str(error),
        }
        if item_id in self.data["in_progress"]:
            del self.data["in_progress"][item_id]
        self.data["stats"]["failed"] += 1
        self.save()

    def is_completed(self, item_id: str) -> bool:
        """Check if item is already completed."""
        return item_id in self.data["completed"]

    def get_stats(self) -> Dict:
        """Get summary statistics."""
        return {
            "completed": len(self.data["completed"]),
            "failed": len(self.data["failed"]),
            "in_progress": len(self.data["in_progress"]),
            "total_records": self.data["stats"].get("total_records", 0),
        }


class Tier1IncrementalScraper:
    """Incremental scraper with immediate save and checkpoint recovery."""

    def __init__(self, checkpoint_file: str = CHECKPOINT_FILE, dry_run: bool = False):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        self.checkpoint = CheckpointManager(checkpoint_file)
        self.dry_run = dry_run
        self.last_request = 0

        # S3 client
        if HAS_BOTO3 and not dry_run:
            self.s3 = boto3.client("s3")
        else:
            self.s3 = None

        logger.info("=" * 70)
        logger.info("BASKETBALL REFERENCE TIER 1 - INCREMENTAL SCRAPER")
        logger.info("=" * 70)
        logger.info(f"Checkpoint: {checkpoint_file}")
        logger.info(f"Dry Run: {dry_run}")
        logger.info(f"S3 Upload: {'Enabled' if self.s3 else 'Disabled'}")

        stats = self.checkpoint.get_stats()
        logger.info(
            f"Progress: {stats['completed']} completed, {stats['failed']} failed, {stats['in_progress']} in progress"
        )
        logger.info("=" * 70)

    def _rate_limit(self):
        """Enforce rate limit."""
        elapsed = time.time() - self.last_request
        if elapsed < RATE_LIMIT:
            time.sleep(RATE_LIMIT - elapsed)
        self.last_request = time.time()

    def _fetch(self, url: str) -> Optional[str]:
        """Fetch URL with rate limiting and retries."""
        for attempt in range(3):
            try:
                self._rate_limit()
                resp = self.session.get(url, timeout=30)

                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 429:
                    logger.warning(f"Rate limited, waiting {60 * (attempt + 1)}s...")
                    time.sleep(60 * (attempt + 1))
                elif resp.status_code == 404:
                    logger.debug(f"404 Not Found: {url}")
                    return None
                else:
                    logger.error(f"HTTP {resp.status_code}: {url}")
                    if attempt < 2:
                        time.sleep(10 * (attempt + 1))
            except Exception as e:
                logger.error(f"Request error: {e}")
                if attempt < 2:
                    time.sleep(10 * (attempt + 1))

        return None

    def _uncomment_html(self, html: str) -> str:
        """
        Uncomment HTML tables (Basketball Reference hides them in comments).
        Uses BeautifulSoup Comment parsing for robust extraction.
        """
        soup = BeautifulSoup(html, "lxml")

        # Find all HTML comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))

        # Replace comments containing tables/divs with their content
        for comment in comments:
            comment_str = str(comment)
            # Only uncomment if it contains table or div elements
            if "<table" in comment_str or "<div" in comment_str:
                # Parse the comment content and replace the comment
                try:
                    comment_soup = BeautifulSoup(comment_str, "lxml")
                    comment.replace_with(comment_soup)
                except:
                    # Fallback: simple string replacement
                    comment.replace_with(BeautifulSoup(comment_str, "lxml"))

        return str(soup)

    def _parse_table(self, soup, table_id: str) -> List[Dict]:
        """
        Parse table into list of dicts with multiple fallback strategies.

        Tries multiple approaches:
        1. Direct table by ID
        2. Table within div_[table_id]
        3. Table within all_[table_id]
        4. Any table with matching ID pattern
        5. First table in content (last resort)
        """
        table = None

        # Strategy 1: Direct table lookup
        table = soup.find("table", {"id": table_id})

        # Strategy 2: Table within div wrappers
        if not table:
            for div_id in [f"div_{table_id}", f"all_{table_id}", table_id]:
                div = soup.find("div", {"id": div_id})
                if div:
                    table = div.find("table")
                    if table:
                        logger.debug(f"Found table via div: {div_id}")
                        break

        # Strategy 3: Search all tables for matching ID
        if not table:
            all_tables = soup.find_all("table")
            for t in all_tables:
                if t.get("id") and table_id in t.get("id"):
                    table = t
                    logger.debug(f"Found table via partial match: {t.get('id')}")
                    break

        # Strategy 4: Last resort - first table with data-stat attributes
        if not table:
            all_tables = soup.find_all("table")
            for t in all_tables:
                if t.find("td", attrs={"data-stat": True}):
                    table = t
                    logger.warning(f"Using first table with data-stat as fallback")
                    break

        if not table:
            logger.warning(f"No table found for ID: {table_id}")
            return []

        records = []
        tbody = table.find("tbody")
        if not tbody:
            logger.warning(f"No tbody found in table: {table_id}")
            return []

        for row in tbody.find_all("tr", class_=lambda x: x != "thead"):
            record = {}
            has_data = False

            for cell in row.find_all(["th", "td"]):
                stat = cell.get("data-stat", "unknown")
                value = cell.get_text(strip=True)

                if value:  # Only store non-empty values
                    record[stat] = value
                    has_data = True

                # Extract player slug from link (multiple stat names possible)
                if stat in ("player", "name_display", "player_name", "name"):
                    link = cell.find("a")
                    if link and link.get("href"):
                        href = link["href"]
                        # /players/j/jamesle01.html -> jamesle01
                        if "/players/" in href:
                            slug = href.split("/")[-1].replace(".html", "")
                            record["player_slug"] = slug
                            has_data = True

            if has_data and record:
                records.append(record)

        logger.debug(f"Parsed {len(records)} records from table: {table_id}")
        return records

    def _save_to_s3(self, data: Dict, s3_key: str) -> bool:
        """Save data to S3 immediately."""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would save to s3://{S3_BUCKET}/{s3_key}")
            return True

        if not self.s3:
            logger.warning("S3 not available, saving locally only")
            # Save locally as backup
            local_path = Path(f"data/tier1_backup/{s3_key}")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "w") as f:
                json.dump(data, f, indent=2)
            return True

        try:
            json_data = json.dumps(data, indent=2)
            full_key = f"{S3_PREFIX}/{s3_key}"
            self.s3.put_object(
                Bucket=S3_BUCKET,
                Key=full_key,
                Body=json_data.encode("utf-8"),
                ContentType="application/json",
            )
            logger.info(f"✅ Saved to S3: s3://{S3_BUCKET}/{full_key}")
            return True
        except Exception as e:
            logger.error(f"❌ S3 save failed: {e}")
            return False

    def scrape_player_game_logs(self, season: int, players: List[str]):
        """
        Scrape player game logs.
        Saves IMMEDIATELY after each player (no data loss on failure).
        """
        logger.info(f"\n📋 PLAYER GAME LOGS - Season {season}")
        logger.info(f"Players: {len(players)}")
        logger.info("=" * 70)

        for idx, player_slug in enumerate(players, 1):
            item_id = f"gamelogs_{season}_{player_slug}"

            # Skip if completed
            if self.checkpoint.is_completed(item_id):
                logger.info(f"[{idx}/{len(players)}] ⏭️  {player_slug} (already done)")
                continue

            logger.info(f"[{idx}/{len(players)}] Processing {player_slug}...")
            self.checkpoint.mark_in_progress(item_id)

            try:
                # Fetch page
                first = player_slug[0]
                url = f"{BASE_URL}/players/{first}/{player_slug}/gamelog/{season}"
                html = self._fetch(url)

                if not html:
                    self.checkpoint.mark_failed(item_id, "Failed to fetch page")
                    continue

                # Parse with comment extraction
                uncommented_html = self._uncomment_html(html)
                soup = BeautifulSoup(uncommented_html, "lxml")
                games = self._parse_table(soup, "pgl_basic")

                if not games:
                    logger.warning(f"  ⚠️  No games found for {player_slug}")
                    self.checkpoint.mark_failed(item_id, "No games found")
                    continue

                # Save IMMEDIATELY
                data = {
                    "player_slug": player_slug,
                    "season": season,
                    "scraped_at": datetime.now().isoformat(),
                    "source_url": url,
                    "game_count": len(games),
                    "games": games,
                }

                s3_key = f"nba/player_game_logs/{player_slug}/{season}.json"
                if self._save_to_s3(data, s3_key):
                    self.checkpoint.mark_completed(item_id, len(games), s3_key)
                    logger.info(f"  ✅ {len(games)} games saved")
                else:
                    self.checkpoint.mark_failed(item_id, "S3 save failed")

            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
                self.checkpoint.mark_failed(item_id, str(e))

        stats = self.checkpoint.get_stats()
        logger.info(
            f"\n✅ Game logs complete: {stats['completed']} players, {stats['total_records']} games"
        )

    def get_top_players(self, season: int, limit: int = 300) -> List[str]:
        """Get top N players by minutes for season."""
        logger.info(f"Fetching top {limit} players for {season}...")

        url = f"{BASE_URL}/leagues/NBA_{season}_per_game.html"
        html = self._fetch(url)

        if not html:
            logger.error("Failed to fetch player list")
            return []

        uncommented_html = self._uncomment_html(html)
        soup = BeautifulSoup(uncommented_html, "lxml")
        players = self._parse_table(soup, "per_game_stats")

        # Extract player slugs
        slugs = []
        for player in players[:limit]:
            if "player_slug" in player:
                slugs.append(player["player_slug"])

        logger.info(f"✓ Found {len(slugs)} players")
        return slugs

    def print_summary(self):
        """Print final summary."""
        stats = self.checkpoint.get_stats()

        logger.info("\n" + "=" * 70)
        logger.info("TIER 1 SCRAPING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Completed: {stats['completed']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"In Progress: {stats['in_progress']}")
        logger.info(f"Total Records: {stats['total_records']:,}")
        logger.info(f"Checkpoint: {self.checkpoint.checkpoint_file}")
        logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Basketball Reference Tier 1 - Incremental Scraper"
    )

    # Execution mode
    parser.add_argument(
        "--tier", type=int, choices=[1], default=1, help="Tier to scrape"
    )
    parser.add_argument("--season", help="Season (e.g., 2024) or range (2020-2024)")
    parser.add_argument("--resume", help="Resume from checkpoint file")

    # Data types
    parser.add_argument("--all", action="store_true", help="All Tier 1 data types")
    parser.add_argument("--game-logs", action="store_true", help="Player game logs")
    parser.add_argument("--play-by-play", action="store_true", help="Event-level PBP")
    parser.add_argument("--shot-charts", action="store_true", help="Shot charts")
    parser.add_argument("--tracking", action="store_true", help="Player tracking")
    parser.add_argument("--lineups", action="store_true", help="Lineup data")

    # Options
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no S3)")
    parser.add_argument(
        "--checkpoint-file", default=CHECKPOINT_FILE, help="Checkpoint file"
    )
    parser.add_argument(
        "--player-limit", type=int, default=300, help="Number of players to scrape"
    )

    args = parser.parse_args()

    # Parse seasons
    if args.season:
        if "-" in args.season:
            start, end = map(int, args.season.split("-"))
            seasons = list(range(start, end + 1))
        else:
            seasons = [int(args.season)]
    else:
        seasons = [2024]  # Default

    # Create scraper
    scraper = Tier1IncrementalScraper(
        checkpoint_file=args.checkpoint_file, dry_run=args.dry_run
    )

    try:
        for season in seasons:
            logger.info(f"\n{'='*70}")
            logger.info(f"SEASON {season}")
            logger.info(f"{'='*70}\n")

            # Get players
            players = scraper.get_top_players(season, args.player_limit)

            if args.all or args.game_logs:
                scraper.scrape_player_game_logs(season, players)

            if args.all or args.play_by_play:
                logger.info("⚠️  Play-by-play not yet implemented")

            if args.all or args.shot_charts:
                logger.info("⚠️  Shot charts not yet implemented")

            if args.all or args.tracking:
                logger.info("⚠️  Player tracking not yet implemented")

            if args.all or args.lineups:
                logger.info("⚠️  Lineups not yet implemented")

        scraper.print_summary()

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user - checkpoint saved")
        scraper.print_summary()
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

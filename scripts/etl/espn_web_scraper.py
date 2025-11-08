#!/usr/bin/env python3
"""
ESPN Web Scraper (XHR Format)

Scrapes ESPN data using the correct web scraping format from the 0espn package.
Uses XHR endpoints (&_xhr=1) to get JSON responses directly.

Usage:
    python scripts/etl/espn_web_scraper.py --game-ids 400975770,401070722
"""

import argparse
import json
import time
import random
from pathlib import Path
from typing import Dict, List
from datetime import datetime

import requests

# ESPN XHR Headers (from 0espn package)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

# Output directories in nba-simulator-aws
BASE_DIR = Path("/Users/ryanranft/nba-simulator-aws/data")
DIRS = {
    "box_score": BASE_DIR / "nba_box_score",
    "pbp": BASE_DIR / "nba_pbp",
    "team_stats": BASE_DIR / "nba_team_stats",
    "schedule": BASE_DIR / "nba_schedule_json",
}

# Game dates for schedule scraping
GAME_DATES = {
    "400975770": "20180316",  # MEM vs CHI
    "401070722": "20181022",  # TOR vs CHA
}


class ESPNWebScraper:
    """ESPN Web Scraper using XHR endpoints"""

    def __init__(self, rate_limit: float = 0.75):
        """
        Initialize scraper

        Args:
            rate_limit: Seconds to wait between requests (default 0.75)
        """
        self.rate_limit = rate_limit
        self.headers = HEADERS.copy()
        self.stats = {
            "box_score": {"success": 0, "failed": 0},
            "pbp": {"success": 0, "failed": 0},
            "team_stats": {"success": 0, "failed": 0},
            "schedule": {"success": 0, "failed": 0},
        }

        # Create output directories
        for dir_path in DIRS.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def scrape_box_score(self, game_id: str) -> bool:
        """Scrape box score data for a game"""
        url = f"https://www.espn.com/nba/boxscore/_/gameId/{game_id}&_xhr=1"
        output_file = DIRS["box_score"] / f"{game_id}.json"

        print(f"  [Box Score] Scraping {game_id}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Validate structure
            if "page" not in data or "content" not in data["page"]:
                print(f"    ❌ Invalid response structure")
                self.stats["box_score"]["failed"] += 1
                return False

            gamepackage = data["page"]["content"].get("gamepackage", {})
            if "bxscr" not in gamepackage:
                print(f"    ⚠️  Warning: 'bxscr' key not found in gamepackage")

            # Save to file
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            file_size = output_file.stat().st_size
            print(f"    ✅ Saved ({file_size:,} bytes)")
            self.stats["box_score"]["success"] += 1
            return True

        except Exception as e:
            print(f"    ❌ Error: {e}")
            self.stats["box_score"]["failed"] += 1
            return False

    def scrape_pbp(self, game_id: str) -> bool:
        """Scrape play-by-play data for a game"""
        url = f"https://www.espn.com/nba/playbyplay/_/gameId/{game_id}&_xhr=1"
        output_file = DIRS["pbp"] / f"{game_id}.json"

        print(f"  [Play-by-Play] Scraping {game_id}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Validate structure
            if "page" not in data or "content" not in data["page"]:
                print(f"    ❌ Invalid response structure")
                self.stats["pbp"]["failed"] += 1
                return False

            gamepackage = data["page"]["content"].get("gamepackage", {})
            if "pbp" not in gamepackage:
                print(f"    ❌ Missing 'pbp' key in gamepackage")
                self.stats["pbp"]["failed"] += 1
                return False

            # Count plays
            play_count = 0
            if "playGrps" in gamepackage["pbp"]:
                for group in gamepackage["pbp"]["playGrps"]:
                    play_count += len(group) if isinstance(group, list) else 1

            # Save to file
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            file_size = output_file.stat().st_size
            print(f"    ✅ Saved ({file_size:,} bytes, {play_count} plays)")
            self.stats["pbp"]["success"] += 1
            return True

        except Exception as e:
            print(f"    ❌ Error: {e}")
            self.stats["pbp"]["failed"] += 1
            return False

    def scrape_team_stats(self, game_id: str) -> bool:
        """Scrape team stats data for a game"""
        url = f"https://www.espn.com/nba/matchup/_/gameId/{game_id}&_xhr=1"
        output_file = DIRS["team_stats"] / f"{game_id}.json"

        print(f"  [Team Stats] Scraping {game_id}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Validate structure
            if "page" not in data or "content" not in data["page"]:
                print(f"    ❌ Invalid response structure")
                self.stats["team_stats"]["failed"] += 1
                return False

            gamepackage = data["page"]["content"].get("gamepackage", {})
            if "gmLdrs" not in gamepackage:
                print(f"    ⚠️  Warning: 'gmLdrs' key not found in gamepackage")

            # Save to file
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            file_size = output_file.stat().st_size
            print(f"    ✅ Saved ({file_size:,} bytes)")
            self.stats["team_stats"]["success"] += 1
            return True

        except Exception as e:
            print(f"    ❌ Error: {e}")
            self.stats["team_stats"]["failed"] += 1
            return False

    def scrape_schedule(self, date_str: str) -> bool:
        """Scrape schedule data for a specific date"""
        url = f"https://www.espn.com/nba/schedule/_/date/{date_str}&_xhr=1"
        output_file = DIRS["schedule"] / f"{date_str}.json"

        print(f"  [Schedule] Scraping {date_str}...")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Validate structure
            if "page" not in data or "content" not in data["page"]:
                print(f"    ❌ Invalid response structure")
                self.stats["schedule"]["failed"] += 1
                return False

            events = data["page"]["content"].get("events", {})
            game_count = len(events.get(date_str, []))

            # Save to file
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            file_size = output_file.stat().st_size
            print(f"    ✅ Saved ({file_size:,} bytes, {game_count} games)")
            self.stats["schedule"]["success"] += 1
            return True

        except Exception as e:
            print(f"    ❌ Error: {e}")
            self.stats["schedule"]["failed"] += 1
            return False

    def scrape_game(self, game_id: str):
        """Scrape all data types for a single game"""
        print(f"\n{'='*70}")
        print(f"Scraping Game {game_id}")
        print(f"{'='*70}")

        # Get game date for schedule
        date_str = GAME_DATES.get(game_id)

        # Scrape all data types with rate limiting
        self.scrape_box_score(game_id)
        time.sleep(self.rate_limit + random.uniform(0, 0.25))

        self.scrape_pbp(game_id)
        time.sleep(self.rate_limit + random.uniform(0, 0.25))

        self.scrape_team_stats(game_id)
        time.sleep(self.rate_limit + random.uniform(0, 0.25))

        if date_str:
            self.scrape_schedule(date_str)
        else:
            print(f"  [Schedule] ⚠️  No date mapping for game {game_id}")

    def print_summary(self):
        """Print scraping summary"""
        print(f"\n{'='*70}")
        print("Scraping Summary")
        print(f"{'='*70}\n")

        for data_type, stats in self.stats.items():
            total = stats["success"] + stats["failed"]
            if total > 0:
                success_rate = (stats["success"] / total) * 100
                print(
                    f"{data_type.replace('_', ' ').title():20} {stats['success']}/{total} ({success_rate:.1f}%)"
                )

        print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="ESPN Web Scraper using XHR format")
    parser.add_argument(
        "--game-ids", type=str, required=True, help="Comma-separated list of game IDs"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.75,
        help="Seconds between requests (default: 0.75)",
    )

    args = parser.parse_args()

    # Parse game IDs
    game_ids = [gid.strip() for gid in args.game_ids.split(",")]

    print("=" * 70)
    print("ESPN Web Scraper (XHR Format)")
    print("=" * 70)
    print(f"Games to scrape: {', '.join(game_ids)}")
    print(f"Rate limit: {args.rate_limit}s between requests")
    print(f"Output directory: {BASE_DIR}")
    print("=" * 70)

    # Initialize scraper
    scraper = ESPNWebScraper(rate_limit=args.rate_limit)

    # Scrape each game
    for game_id in game_ids:
        scraper.scrape_game(game_id)
        if game_id != game_ids[-1]:  # Not last game
            time.sleep(1.0)  # Extra delay between games

    # Print summary
    scraper.print_summary()


if __name__ == "__main__":
    main()

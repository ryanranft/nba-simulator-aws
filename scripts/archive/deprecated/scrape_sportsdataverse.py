#!/usr/bin/env python3
"""
⚠️ DEPRECATED - DO NOT USE ⚠️

This script is deprecated and should not be used.

DEPRECATED ON: October 8, 2025
REASON: Redundant with hoopR implementation (R-based scraper provides same data)
ALTERNATIVE: Use scripts/etl/scrape_hoopr_phase1b_only.R (run via run_hoopr_phase1b.sh)

---

SportsDataverse NBA Data Scraper

Scrapes NBA data using the SportsDataverse Python package.
Provides unified access to ESPN, NBA.com Stats, and other sources.

Prerequisites:
    pip install sportsdataverse

Usage:
    python scripts/etl/scrape_sportsdataverse.py --season 2024
    python scripts/etl/scrape_sportsdataverse.py --season 2024 --upload-to-s3
    python scripts/etl/scrape_sportsdataverse.py --start-date 2024-01-01 --end-date 2024-12-31
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

try:
    from sportsdataverse.nba import espn_nba_schedule, espn_nba_pbp
    from sportsdataverse.nba import load_nba_player_boxscore, load_nba_team_boxscore

    HAS_SPORTSDATAVERSE = True
except ImportError:
    HAS_SPORTSDATAVERSE = False
    print("❌ sportsdataverse package not installed")
    print("Install with: pip install sportsdataverse")

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class SportsDataverseScraper:
    """Scraper using SportsDataverse package for NBA data"""

    def __init__(self, output_dir="/tmp/sportsdataverse", s3_bucket=None):
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3") if HAS_BOTO3 and s3_bucket else None

        # Create output directories
        for subdir in ["schedules", "play_by_play", "box_scores"]:
            (self.output_dir / subdir).mkdir(parents=True, exist_ok=True)

        self.stats = {
            "schedules_scraped": 0,
            "games_found": 0,
            "pbp_scraped": 0,
            "box_scores_scraped": 0,
            "errors": 0,
        }

    def save_json(self, data, filepath):
        """Save JSON data to file"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Convert any non-serializable objects to strings
        def convert_for_json(obj):
            if isinstance(obj, (list, tuple)):
                return [convert_for_json(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_for_json(value) for key, value in obj.items()}
            elif hasattr(obj, "to_list"):  # pandas Series
                return obj.to_list()
            elif hasattr(obj, "__dict__"):
                return str(obj)
            else:
                return obj

        cleaned_data = convert_for_json(data)

        with open(filepath, "w") as f:
            json.dump(cleaned_data, f, indent=2, default=str)

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

    def scrape_season_schedule(self, season):
        """
        Scrape season schedule using SportsDataverse

        Args:
            season: Season year (e.g., 2024 for 2023-24 season)
        """
        print(f"📅 Scraping {season} season schedule via SportsDataverse...")

        try:
            # Get schedule data (returns Polars DataFrame)
            schedule_df = espn_nba_schedule(dates=season)

            if schedule_df is None or len(schedule_df) == 0:
                print(f"  ⚠️  No schedule data returned for {season}")
                return None

            # Convert Polars DataFrame to list of dicts
            schedule_data = schedule_df.to_dicts()

            # Save schedule
            schedule_file = self.output_dir / "schedules" / f"schedule_{season}.json"
            self.save_json(schedule_data, schedule_file)

            self.stats["schedules_scraped"] += 1
            self.stats["games_found"] += len(schedule_data)
            print(f"  ✅ Saved {len(schedule_data)} games")

            # Upload to S3
            if self.s3_client:
                s3_key = f"sportsdataverse/schedules/schedule_{season}.json"
                if self.upload_to_s3(schedule_file, s3_key):
                    print(f"  ✅ Uploaded to S3")

            return schedule_data

        except Exception as e:
            print(f"  ❌ Error scraping schedule: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_game_pbp(self, game_id):
        """
        Scrape play-by-play for a game

        Args:
            game_id: ESPN game ID
        """
        try:
            # Get play-by-play data (returns Polars DataFrame)
            pbp_df = espn_nba_pbp(game_id=str(game_id))

            if pbp_df is None or len(pbp_df) == 0:
                print(f"    ⚠️  No play-by-play data for game {game_id}")
                return None

            # Convert Polars DataFrame to list of dicts
            pbp_data = pbp_df.to_dicts()

            # Save
            pbp_file = self.output_dir / "play_by_play" / f"{game_id}.json"
            self.save_json(pbp_data, pbp_file)

            self.stats["pbp_scraped"] += 1

            # Upload to S3
            if self.s3_client:
                s3_key = f"sportsdataverse/play_by_play/{game_id}.json"
                self.upload_to_s3(pbp_file, s3_key)

            return pbp_data

        except Exception as e:
            print(f"    ❌ PBP error for game {game_id}: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_game_box_score(self, game_id, season):
        """
        Scrape box score for a game

        Args:
            game_id: ESPN game ID
            season: Season year (required for loader functions)
        """
        try:
            # Get player box score data
            player_box_df = load_nba_player_boxscore(seasons=[season])

            # Filter for this specific game
            if player_box_df is not None and len(player_box_df) > 0:
                game_box = player_box_df[player_box_df["game_id"] == str(game_id)]

                if len(game_box) == 0:
                    print(f"    ⚠️  No box score data for game {game_id}")
                    return None

                # Convert to dict
                box_data = game_box.to_dict("records")

                # Save
                box_file = self.output_dir / "box_scores" / f"{game_id}.json"
                self.save_json(box_data, box_file)

                self.stats["box_scores_scraped"] += 1

                # Upload to S3
                if self.s3_client:
                    s3_key = f"sportsdataverse/box_scores/{game_id}.json"
                    self.upload_to_s3(box_file, s3_key)

                return box_data
            else:
                print(f"    ⚠️  No box score data for game {game_id}")
                return None

        except Exception as e:
            print(f"    ❌ Box score error for game {game_id}: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_season(self, season, include_pbp=True, include_box=True):
        """
        Scrape complete season data

        Args:
            season: Season year
            include_pbp: Whether to scrape play-by-play
            include_box: Whether to scrape box scores
        """
        print(f"\n🚀 Starting SportsDataverse scraper for {season} season")
        print(f"💾 Output directory: {self.output_dir}")
        if self.s3_client:
            print(f"☁️  S3 bucket: {self.s3_bucket}")
        print()

        # Get schedule
        schedule = self.scrape_season_schedule(season)

        if not schedule:
            print(f"❌ Failed to get schedule for {season}")
            return

        # Scrape each game
        print(f"\n🏀 Scraping {len(schedule)} games...")

        for i, game in enumerate(schedule, 1):
            game_id = game.get("id") or game.get("game_id")

            if not game_id:
                print(f"  ⚠️  No game ID found for game {i}")
                continue

            game_date = game.get("date", "unknown")
            print(f"\n  [{i}/{len(schedule)}] Game {game_id} ({game_date})")

            # Scrape play-by-play
            if include_pbp:
                self.scrape_game_pbp(game_id)

            # Scrape box score
            if include_box:
                self.scrape_game_box_score(game_id, season)

            # Rate limiting (be respectful)
            time.sleep(0.5)

        # Print summary
        print("\n" + "=" * 60)
        print("📊 SCRAPING SUMMARY")
        print("=" * 60)
        print(f"Schedules scraped:     {self.stats['schedules_scraped']}")
        print(f"Games found:           {self.stats['games_found']}")
        print(f"Play-by-play scraped:  {self.stats['pbp_scraped']}")
        print(f"Box scores scraped:    {self.stats['box_scores_scraped']}")
        print(f"Errors:                {self.stats['errors']}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Scrape NBA data via SportsDataverse")
    parser.add_argument("--season", type=int, help="Season year (e.g., 2024)")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--output-dir", default="/tmp/sportsdataverse", help="Output directory"
    )
    parser.add_argument("--upload-to-s3", action="store_true", help="Upload to S3")
    parser.add_argument(
        "--s3-bucket", default="nba-sim-raw-data-lake", help="S3 bucket"
    )
    parser.add_argument("--no-pbp", action="store_true", help="Skip play-by-play")
    parser.add_argument("--no-box", action="store_true", help="Skip box scores")

    args = parser.parse_args()

    if not HAS_SPORTSDATAVERSE:
        sys.exit(1)

    # Check S3 configuration
    s3_bucket = args.s3_bucket if args.upload_to_s3 else None
    if args.upload_to_s3 and not HAS_BOTO3:
        print("❌ boto3 is required for S3 upload. Install with: pip install boto3")
        sys.exit(1)

    # Create scraper
    scraper = SportsDataverseScraper(output_dir=args.output_dir, s3_bucket=s3_bucket)

    # Scrape by season or date range
    if args.season:
        scraper.scrape_season(
            args.season, include_pbp=not args.no_pbp, include_box=not args.no_box
        )
    elif args.start_date and args.end_date:
        # TODO: Implement date range scraping
        print("❌ Date range scraping not yet implemented")
        print("Use --season instead")
        sys.exit(1)
    else:
        print("❌ Must specify either --season or --start-date/--end-date")
        sys.exit(1)

    print(f"\n✅ Scraping complete!")
    print(f"📁 Files saved to: {scraper.output_dir}")
    if s3_bucket:
        print(f"☁️  Files uploaded to s3://{s3_bucket}/sportsdataverse/")


if __name__ == "__main__":
    main()

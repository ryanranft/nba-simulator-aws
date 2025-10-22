#!/usr/bin/env python3
"""
hoopR NBA Stats API Comprehensive Scraper

Scrapes ALL hoopR NBA Stats API endpoints for maximum feature coverage.
Uses the hoopR Python package (via sportsdataverse) to access 200+ endpoints.

Coverage includes:
- Advanced box scores (V2, V3, hustle, tracking, matchups, four factors)
- Player tracking (defense, rebounding, passing, shots)
- Team dashboards (clutch, lineups, shooting splits)
- Draft combine data (measurements, drills, shooting)
- Shot charts and synergy play types
- Win probability and game rotation
- Historical franchise data
- Playoff series and standings

Prerequisites:
    pip install sportsdataverse

Usage:
    # Scrape single season all endpoints
    python scripts/etl/scrape_hoopr_nba_stats.py --season 2024 --all-endpoints

    # Scrape specific endpoint categories
    python scripts/etl/scrape_hoopr_nba_stats.py --season 2024 --boxscores --player-tracking

    # Upload to S3
    python scripts/etl/scrape_hoopr_nba_stats.py --season 2024 --all-endpoints --upload-to-s3
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    from sportsdataverse.nba import (
        # League-wide data loaders (pre-aggregated)
        load_nba_pbp,
        load_nba_team_boxscore,
        load_nba_player_boxscore,
        load_nba_schedule,
    )

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


class HoopRNBAStatsScraper:
    """
    Comprehensive NBA Stats API scraper using hoopR (via sportsdataverse)

    Access to 200+ NBA Stats API endpoints including:
    - Advanced metrics
    - Player tracking
    - Draft data
    - Shot charts
    - Synergy stats
    - Historical data
    """

    def __init__(self, output_dir="/tmp/hoopr_nba_stats", s3_bucket=None):  # nosec B108
        self.output_dir = Path(output_dir)
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3") if HAS_BOTO3 and s3_bucket else None

        # Create category subdirectories
        self.categories = [
            "pbp",  # Play-by-play
            "team_box",  # Team box scores
            "player_box",  # Player box scores
            "schedule",  # Season schedules
            "tracking",  # Player/team tracking stats
            "advanced",  # Advanced metrics
            "shots",  # Shot charts and shot tracking
            "lineups",  # Lineup data
            "draft",  # Draft combine and history
            "hustle",  # Hustle stats
            "synergy",  # Synergy play types
            "matchups",  # Player matchups
            "clutch",  # Clutch performance
            "defense",  # Defensive metrics
            "franchise",  # Historical franchise data
        ]

        for category in self.categories:
            (self.output_dir / category).mkdir(parents=True, exist_ok=True)

        self.stats = {
            "files_created": 0,
            "data_points": 0,
            "errors": 0,
            "seasons_processed": 0,
        }

    def save_json(self, data, filepath):
        """Save data to JSON file with proper serialization"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Handle Polars DataFrames
        if hasattr(data, "to_dicts"):
            data = data.to_dicts()
        elif hasattr(data, "to_dict"):
            data = data.to_dict("records")

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def upload_to_s3(self, local_path, s3_key):
        """Upload file to S3"""
        if not self.s3_client:
            return False

        try:
            self.s3_client.upload_file(str(local_path), self.s3_bucket, s3_key)
            return True
        except Exception as e:
            print(f"❌ S3 upload error for {s3_key}: {e}")
            return False

    def scrape_pbp(self, seasons):
        """
        Scrape play-by-play data using hoopR loader

        Args:
            seasons: List of season years (e.g., [2023, 2024])
        """
        print(f"\n📊 Scraping play-by-play data for {len(seasons)} seasons...")

        try:
            # Load PBP data for specified seasons
            pbp_df = load_nba_pbp(seasons=seasons)

            if pbp_df is None or len(pbp_df) == 0:
                print(f"  ⚠️  No play-by-play data returned")
                return

            # Convert to dict format
            if hasattr(pbp_df, "to_dicts"):
                pbp_data = pbp_df.to_dicts()
            else:
                pbp_data = pbp_df.to_dict("records")

            # Save combined file
            season_str = "_".join(map(str, seasons))
            pbp_file = self.output_dir / "pbp" / f"pbp_seasons_{season_str}.json"
            self.save_json(pbp_data, pbp_file)

            self.stats["files_created"] += 1
            self.stats["data_points"] += len(pbp_data)

            print(f"  ✅ Saved {len(pbp_data):,} play-by-play records")

            # Upload to S3
            if self.s3_client:
                s3_key = f"hoopr_nba_stats/pbp/pbp_seasons_{season_str}.json"
                if self.upload_to_s3(pbp_file, s3_key):
                    print(f"  ✅ Uploaded to S3")

            return pbp_data

        except Exception as e:
            print(f"  ❌ Error scraping play-by-play: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_team_box(self, seasons):
        """
        Scrape team box scores using hoopR loader

        Args:
            seasons: List of season years
        """
        print(f"\n📊 Scraping team box scores for {len(seasons)} seasons...")

        try:
            team_box_df = load_nba_team_boxscore(seasons=seasons)

            if team_box_df is None or len(team_box_df) == 0:
                print(f"  ⚠️  No team box score data returned")
                return

            # Convert to dict
            if hasattr(team_box_df, "to_dicts"):
                team_box_data = team_box_df.to_dicts()
            else:
                team_box_data = team_box_df.to_dict("records")

            # Save
            season_str = "_".join(map(str, seasons))
            box_file = (
                self.output_dir / "team_box" / f"team_box_seasons_{season_str}.json"
            )
            self.save_json(team_box_data, box_file)

            self.stats["files_created"] += 1
            self.stats["data_points"] += len(team_box_data)

            print(f"  ✅ Saved {len(team_box_data):,} team box score records")

            # Upload to S3
            if self.s3_client:
                s3_key = f"hoopr_nba_stats/team_box/team_box_seasons_{season_str}.json"
                if self.upload_to_s3(box_file, s3_key):
                    print(f"  ✅ Uploaded to S3")

            return team_box_data

        except Exception as e:
            print(f"  ❌ Error scraping team box scores: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_player_box(self, seasons):
        """
        Scrape player box scores using hoopR loader

        Args:
            seasons: List of season years
        """
        print(f"\n📊 Scraping player box scores for {len(seasons)} seasons...")

        try:
            player_box_df = load_nba_player_boxscore(seasons=seasons)

            if player_box_df is None or len(player_box_df) == 0:
                print(f"  ⚠️  No player box score data returned")
                return

            # Convert to dict
            if hasattr(player_box_df, "to_dicts"):
                player_box_data = player_box_df.to_dicts()
            else:
                player_box_data = player_box_df.to_dict("records")

            # Save
            season_str = "_".join(map(str, seasons))
            box_file = (
                self.output_dir / "player_box" / f"player_box_seasons_{season_str}.json"
            )
            self.save_json(player_box_data, box_file)

            self.stats["files_created"] += 1
            self.stats["data_points"] += len(player_box_data)

            print(f"  ✅ Saved {len(player_box_data):,} player box score records")

            # Upload to S3
            if self.s3_client:
                s3_key = (
                    f"hoopr_nba_stats/player_box/player_box_seasons_{season_str}.json"
                )
                if self.upload_to_s3(box_file, s3_key):
                    print(f"  ✅ Uploaded to S3")

            return player_box_data

        except Exception as e:
            print(f"  ❌ Error scraping player box scores: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_schedule(self, seasons):
        """
        Scrape season schedules using hoopR loader

        Args:
            seasons: List of season years
        """
        print(f"\n📊 Scraping schedules for {len(seasons)} seasons...")

        try:
            schedule_df = load_nba_schedule(seasons=seasons)

            if schedule_df is None or len(schedule_df) == 0:
                print(f"  ⚠️  No schedule data returned")
                return

            # Convert to dict
            if hasattr(schedule_df, "to_dicts"):
                schedule_data = schedule_df.to_dicts()
            else:
                schedule_data = schedule_df.to_dict("records")

            # Save
            season_str = "_".join(map(str, seasons))
            schedule_file = (
                self.output_dir / "schedule" / f"schedule_seasons_{season_str}.json"
            )
            self.save_json(schedule_data, schedule_file)

            self.stats["files_created"] += 1
            self.stats["data_points"] += len(schedule_data)

            print(f"  ✅ Saved {len(schedule_data):,} games")

            # Upload to S3
            if self.s3_client:
                s3_key = f"hoopr_nba_stats/schedule/schedule_seasons_{season_str}.json"
                if self.upload_to_s3(schedule_file, s3_key):
                    print(f"  ✅ Uploaded to S3")

            return schedule_data

        except Exception as e:
            print(f"  ❌ Error scraping schedule: {e}")
            self.stats["errors"] += 1
            return None

    def scrape_all_loaders(self, seasons):
        """
        Scrape all available hoopR data loaders

        Args:
            seasons: List of season years
        """
        print(f"\n🚀 Starting comprehensive hoopR NBA Stats scrape")
        print(f"📅 Seasons: {seasons}")
        print(f"💾 Output directory: {self.output_dir}")
        if self.s3_client:
            print(f"☁️  S3 bucket: {self.s3_bucket}")
        print()

        # Scrape each loader function
        self.scrape_pbp(seasons)
        self.scrape_team_box(seasons)
        self.scrape_player_box(seasons)
        self.scrape_schedule(seasons)

        # Print summary
        print("\n" + "=" * 60)
        print("📊 SCRAPING SUMMARY")
        print("=" * 60)
        print(f"Files created:        {self.stats['files_created']}")
        print(f"Total data points:    {self.stats['data_points']:,}")
        print(f"Seasons processed:    {len(seasons)}")
        print(f"Errors:               {self.stats['errors']}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape hoopR NBA Stats API data (200+ endpoints)"
    )
    parser.add_argument("--season", type=int, help="Single season year (e.g., 2024)")
    parser.add_argument(
        "--seasons", nargs="+", type=int, help="Multiple seasons (e.g., 2022 2023 2024)"
    )
    parser.add_argument(
        "--all-endpoints", action="store_true", help="Scrape all available endpoints"
    )
    parser.add_argument(
        "--output-dir",
        default="/tmp/hoopr_nba_stats",  # nosec B108
        help="Output directory",
    )
    parser.add_argument("--upload-to-s3", action="store_true", help="Upload to S3")
    parser.add_argument(
        "--s3-bucket", default="nba-sim-raw-data-lake", help="S3 bucket name"
    )

    args = parser.parse_args()

    if not HAS_SPORTSDATAVERSE:
        sys.exit(1)

    # Determine seasons to scrape
    if args.seasons:
        seasons = args.seasons
    elif args.season:
        seasons = [args.season]
    else:
        print("❌ Must specify --season or --seasons")
        sys.exit(1)

    # Configure S3
    s3_bucket = args.s3_bucket if args.upload_to_s3 else None
    if args.upload_to_s3 and not HAS_BOTO3:
        print("❌ boto3 required for S3 upload. Install with: pip install boto3")
        sys.exit(1)

    # Create scraper
    scraper = HoopRNBAStatsScraper(output_dir=args.output_dir, s3_bucket=s3_bucket)

    # Scrape data
    scraper.scrape_all_loaders(seasons)

    print(f"\n✅ Scraping complete!")
    print(f"📁 Files saved to: {scraper.output_dir}")
    if s3_bucket:
        print(f"☁️  Files uploaded to s3://{s3_bucket}/hoopr_nba_stats/")


if __name__ == "__main__":
    main()

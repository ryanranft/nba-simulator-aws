#!/usr/bin/env python3
"""
SportsDataverse NBA Scraper

Uses the sportsdataverse Python package to scrape NBA data.
https://www.sportsdataverse.org/

Prerequisites:
    pip install sportsdataverse

Usage:
    python scripts/etl/scrape_sportsdataverse.py --season 2024
    python scripts/etl/scrape_sportsdataverse.py --season 2024 --upload-to-s3
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from sportsdataverse.nba import (
        espn_nba_schedule,
        espn_nba_pbp,
        espn_nba_player_box,
        espn_nba_team_box
    )
    HAS_SPORTSDATAVERSE = True
except ImportError:
    HAS_SPORTSDATAVERSE = False
    print("❌ sportsdataverse not installed")
    print("Install with: pip install sportsdataverse")

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class SportsDataverseScraper:
    """Scraper using SportsDataverse package"""

    def __init__(self, output_dir="/tmp/sportsdataverse", s3_bucket=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client('s3') if HAS_BOTO3 and s3_bucket else None

        self.stats = {
            'schedule_files': 0,
            'pbp_files': 0,
            'box_files': 0,
            'errors': 0
        }

    def scrape_season_schedule(self, season):
        """
        Scrape full season schedule

        Args:
            season: Season year (e.g., 2024)
        """
        print(f"📅 Scraping {season} season schedule...")

        try:
            # Get schedule
            schedule_df = espn_nba_schedule(season=season)

            # Convert to dict
            schedule_data = schedule_df.to_dict('records')

            # Save
            output_file = self.output_dir / f"schedule_{season}.json"
            with open(output_file, 'w') as f:
                json.dump(schedule_data, f, indent=2)

            self.stats['schedule_files'] += 1
            print(f"  ✅ Saved {len(schedule_data)} games to {output_file}")

            # Upload to S3
            if self.s3_client:
                s3_key = f"sportsdataverse/schedule_{season}.json"
                self.s3_client.upload_file(str(output_file), self.s3_bucket, s3_key)
                print(f"  ✅ Uploaded to S3")

            return schedule_data

        except Exception as e:
            print(f"  ❌ Error: {e}")
            self.stats['errors'] += 1
            return None

    def scrape_game_data(self, game_id):
        """
        Scrape all data for a game

        Args:
            game_id: ESPN game ID
        """
        print(f"  🏀 Game {game_id}")

        # Play-by-play
        try:
            pbp_df = espn_nba_pbp(game_id=game_id)
            pbp_data = pbp_df.to_dict('records')

            pbp_file = self.output_dir / f"pbp_{game_id}.json"
            with open(pbp_file, 'w') as f:
                json.dump(pbp_data, f, indent=2)

            self.stats['pbp_files'] += 1

            if self.s3_client:
                s3_key = f"sportsdataverse/pbp/{game_id}.json"
                self.s3_client.upload_file(str(pbp_file), self.s3_bucket, s3_key)

        except Exception as e:
            print(f"    ❌ PBP error: {e}")
            self.stats['errors'] += 1

        # Box scores
        try:
            player_box_df = espn_nba_player_box(game_id=game_id)
            team_box_df = espn_nba_team_box(game_id=game_id)

            box_data = {
                'player_box': player_box_df.to_dict('records'),
                'team_box': team_box_df.to_dict('records')
            }

            box_file = self.output_dir / f"box_{game_id}.json"
            with open(box_file, 'w') as f:
                json.dump(box_data, f, indent=2)

            self.stats['box_files'] += 1

            if self.s3_client:
                s3_key = f"sportsdataverse/box/{game_id}.json"
                self.s3_client.upload_file(str(box_file), self.s3_bucket, s3_key)

        except Exception as e:
            print(f"    ❌ Box score error: {e}")
            self.stats['errors'] += 1


def main():
    parser = argparse.ArgumentParser(description="Scrape NBA data using SportsDataverse")
    parser.add_argument('--season', type=int, required=True, help='Season year (e.g., 2024)')
    parser.add_argument('--output-dir', default='/tmp/sportsdataverse', help='Output directory')
    parser.add_argument('--upload-to-s3', action='store_true', help='Upload to S3')
    parser.add_argument('--s3-bucket', default='nba-sim-raw-data-lake', help='S3 bucket')
    parser.add_argument('--games-only', action='store_true', help='Scrape game data for schedule')

    args = parser.parse_args()

    if not HAS_SPORTSDATAVERSE:
        sys.exit(1)

    s3_bucket = args.s3_bucket if args.upload_to_s3 else None
    scraper = SportsDataverseScraper(output_dir=args.output_dir, s3_bucket=s3_bucket)

    print(f"🚀 SportsDataverse NBA Scraper")
    print(f"📅 Season: {args.season}")
    print()

    # Scrape schedule
    schedule = scraper.scrape_season_schedule(args.season)

    # Optionally scrape game data
    if args.games_only and schedule:
        print(f"\n📦 Scraping game data...")
        for game in schedule[:10]:  # Limit to 10 games for testing
            game_id = game.get('game_id')
            if game_id:
                scraper.scrape_game_data(game_id)

    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    print(f"Schedule files: {scraper.stats['schedule_files']}")
    print(f"PBP files: {scraper.stats['pbp_files']}")
    print(f"Box score files: {scraper.stats['box_files']}")
    print(f"Errors: {scraper.stats['errors']}")
    print("="*60)


if __name__ == '__main__':
    main()
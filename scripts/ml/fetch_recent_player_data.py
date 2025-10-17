#!/usr/bin/env python3
"""
Fetch Recent Player Data for Panel Features

Purpose:
- Fetch last 20-30 games for all active NBA players
- Build historical dataset needed for panel features (lag, rolling)
- Handle season boundaries (use previous season if needed)
- Save to parquet for feature extraction pipeline

Usage:
    python scripts/ml/fetch_recent_player_data.py --days 60
    python scripts/ml/fetch_recent_player_data.py --seasons 2024,2025 --output /tmp/recent_player_data.parquet

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import List, Optional

import boto3
import pandas as pd
import pyarrow.parquet as pq
from botocore.exceptions import ClientError


class RecentPlayerDataFetcher:
    """Fetches recent player game data from S3 for panel features"""

    def __init__(self, s3_bucket: str = "nba-sim-raw-data-lake"):
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3")

    def fetch_from_hoopr(
        self, seasons: List[str], days_back: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch player box score data from hoopR parquet files

        Args:
            seasons: List of season years to fetch (e.g., ['2024', '2025'])
            days_back: Optional filter to only include games from last N days

        Returns:
            DataFrame with player game data
        """
        print(f"\n{'='*80}")
        print("FETCHING RECENT PLAYER DATA FROM HOOPR")
        print(f"{'='*80}")
        print(f"S3 Bucket: {self.s3_bucket}")
        print(f"Seasons: {', '.join(seasons)}")
        if days_back:
            print(f"Days back: {days_back}")
        print()

        all_data = []

        for season in seasons:
            s3_key = f"hoopr_parquet/player_box/nba_data_{season}.parquet"
            print(
                f"Loading {season} season from s3://{self.s3_bucket}/{s3_key}...",
                end=" ",
            )

            try:
                # Read parquet from S3 using pandas S3 support
                s3_path = f"s3://{self.s3_bucket}/{s3_key}"
                df = pd.read_parquet(s3_path)

                print(f"✓ Loaded {len(df):,} records")

                # Convert game_date_time to datetime if needed
                if "game_date_time" in df.columns:
                    df["game_date_time"] = pd.to_datetime(df["game_date_time"])

                # Filter by date if requested
                if days_back:
                    # Make cutoff_date timezone-aware to match the data
                    cutoff_date = pd.Timestamp.now(tz="America/New_York") - timedelta(
                        days=days_back
                    )
                    before_count = len(df)
                    df = df[df["game_date_time"] >= cutoff_date]
                    after_count = len(df)
                    print(
                        f"  Filtered to last {days_back} days: {after_count:,} records ({before_count - after_count:,} removed)"
                    )

                all_data.append(df)

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "NoSuchKey":
                    print(f"⚠️  File not found (season may not be loaded yet)")
                else:
                    print(f"⚠️  S3 error: {e}")
                continue
            except Exception as e:
                print(f"⚠️  Error: {e}")
                continue

        if not all_data:
            print("\n⚠️  No data loaded")
            return pd.DataFrame()

        # Combine all seasons
        df_combined = pd.concat(all_data, ignore_index=True)

        print(f"\n{'='*80}")
        print("DATA SUMMARY")
        print(f"{'='*80}")
        print(f"Total records: {len(df_combined):,}")
        print(f"Unique players: {df_combined['athlete_id'].nunique():,}")
        print(f"Unique games: {df_combined['game_id'].nunique():,}")
        print(
            f"Date range: {df_combined['game_date_time'].min()} to {df_combined['game_date_time'].max()}"
        )
        print()

        return df_combined

    def get_active_rosters(self, df_games: pd.DataFrame) -> pd.DataFrame:
        """
        Get active rosters for upcoming games

        Args:
            df_games: DataFrame of upcoming games

        Returns:
            DataFrame with team_id, player_id mappings
        """
        print("Getting active rosters from recent games...")

        # Get unique teams from upcoming games
        teams = set(
            df_games["home_team_id"].tolist() + df_games["away_team_id"].tolist()
        )

        print(f"  Found {len(teams)} unique teams in upcoming games")

        # Note: This is a simplified approach
        # In production, you'd want to use nba_api CommonTeamRoster or ESPN API
        # For now, we'll assume all players in recent data are potentially active

        return pd.DataFrame()

    def aggregate_player_stats(
        self, df: pd.DataFrame, min_games: int = 5
    ) -> pd.DataFrame:
        """
        Aggregate player stats to identify active players

        Args:
            df: Raw player game data
            min_games: Minimum games played to be considered active

        Returns:
            DataFrame with player aggregates
        """
        print("\nAggregating player statistics...")

        player_stats = (
            df.groupby("athlete_id")
            .agg(
                {
                    "game_id": "count",
                    "game_date_time": "max",
                    "athlete_display_name": "first",
                    "team_id": "last",  # Most recent team
                    "minutes": "mean",
                    "points": "mean",
                    "rebounds": "mean",
                    "assists": "mean",
                }
            )
            .reset_index()
        )

        player_stats.columns = [
            "player_id",
            "games_played",
            "last_game_date",
            "player_name",
            "current_team_id",
            "avg_minutes",
            "avg_points",
            "avg_rebounds",
            "avg_assists",
        ]

        # Filter to active players (played minimum games)
        player_stats = player_stats[player_stats["games_played"] >= min_games]

        print(f"  Active players (≥{min_games} games): {len(player_stats):,}")
        print(f"  Avg games per player: {player_stats['games_played'].mean():.1f}")
        print(f"  Avg points per game: {player_stats['avg_points'].mean():.1f}")

        return player_stats

    def prepare_panel_ready_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data in panel-ready format

        Args:
            df: Raw player game data

        Returns:
            DataFrame sorted and formatted for panel data processing
        """
        print("\nPreparing panel-ready data...")

        # Sort by player and date (critical for panel data)
        df = df.sort_values(["athlete_id", "game_date_time"])

        # Ensure required columns exist
        required_cols = [
            "athlete_id",
            "game_id",
            "game_date_time",
            "athlete_display_name",
            "team_id",
            "team_location",
            "team_name",
            "minutes",
            "points",
            "rebounds",
            "assists",
            "field_goals_made",
            "field_goals_attempted",
            "three_point_field_goals_made",
            "three_point_field_goals_attempted",
            "free_throws_made",
            "free_throws_attempted",
            "steals",
            "blocks",
            "turnovers",
            "fouls",
        ]

        # Check for missing columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"  ⚠️  Missing columns: {missing_cols}")

        # Add home/away indicator if not present
        if "home_away" not in df.columns:
            # This would need to be enriched from game data
            print("  ⚠️  home_away column not found - will need to be added later")

        print(f"  ✓ Data sorted by player and date")
        print(f"  ✓ Ready for panel feature extraction")

        return df


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Fetch recent player data for panel features"
    )
    parser.add_argument(
        "--seasons",
        type=str,
        default="2024,2025",
        help="Comma-separated season years (default: 2024,2025)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Only include games from last N days (optional)",
    )
    parser.add_argument(
        "--min-games",
        type=int,
        default=5,
        help="Minimum games to be considered active player (default: 5)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/recent_player_data.parquet",
        help="Output parquet file path (default: /tmp/recent_player_data.parquet)",
    )
    parser.add_argument(
        "--stats",
        type=str,
        default="/tmp/player_stats_summary.csv",
        help="Output player stats summary CSV (default: /tmp/player_stats_summary.csv)",
    )

    args = parser.parse_args()

    # Parse seasons
    seasons = args.seasons.split(",")

    # Fetch data
    fetcher = RecentPlayerDataFetcher()
    df = fetcher.fetch_from_hoopr(seasons=seasons, days_back=args.days)

    if df.empty:
        print("No data to process.")
        sys.exit(1)

    # Prepare panel-ready data
    df_panel_ready = fetcher.prepare_panel_ready_data(df)

    # Save to parquet
    df_panel_ready.to_parquet(args.output, index=False)
    print(f"\n✓ Saved panel-ready data to: {args.output}")
    print(f"  Size: {len(df_panel_ready):,} records")

    # Generate player stats summary
    player_stats = fetcher.aggregate_player_stats(df, min_games=args.min_games)
    player_stats.to_csv(args.stats, index=False)
    print(f"✓ Saved player stats summary to: {args.stats}")
    print(f"  Active players: {len(player_stats):,}")

    # Display top players by recent points
    print(f"\n{'='*80}")
    print("TOP 10 PLAYERS (by recent avg points)")
    print(f"{'='*80}")
    top_players = player_stats.nlargest(10, "avg_points")
    for i, player in top_players.iterrows():
        print(
            f"{player['player_name']:30} | "
            f"{player['avg_points']:5.1f} pts | "
            f"{player['avg_rebounds']:4.1f} reb | "
            f"{player['avg_assists']:4.1f} ast | "
            f"{player['games_played']:2.0f} games"
        )

    print(f"\n✓ Successfully fetched recent player data")
    print(f"✓ Ready for panel feature extraction (Step 3)")


if __name__ == "__main__":
    main()

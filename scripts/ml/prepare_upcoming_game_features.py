#!/usr/bin/env python3
"""
Prepare Features for Upcoming NBA Games

Purpose:
- Load upcoming games and recent player data
- Extract panel features (lag, rolling windows) using panel data system
- Aggregate to team level using sophisticated aggregations
- Generate 549 features per game for ML prediction

Usage:
    python scripts/ml/prepare_upcoming_game_features.py
    python scripts/ml/prepare_upcoming_game_features.py --games /tmp/upcoming_games.parquet --players /tmp/recent_player_data.parquet

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import argparse
import sys
import warnings
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class UpcomingGameFeaturePreparer:
    """Prepares features for upcoming games using panel data approach"""

    def __init__(self):
        # Standalone panel data feature creation
        print("Initializing feature preparer...")
        print("✓ Feature preparer initialized")

    def create_panel_features(self, df_players: pd.DataFrame) -> pd.DataFrame:
        """
        Create panel features (lag, rolling) for player data

        Args:
            df_players: Raw player game data

        Returns:
            DataFrame with panel features added
        """
        print("\nCreating panel features...")
        print(f"  Input records: {len(df_players):,}")

        # Sort by player and date (critical for lag/rolling calculations)
        df = df_players.sort_values(["athlete_id", "game_date_time"]).copy()

        # Define core stats for panel features
        stats_cols = [
            "points",
            "rebounds",
            "assists",
            "steals",
            "blocks",
            "turnovers",
            "minutes",
        ]

        # Calculate shooting percentages
        df["fg_pct"] = np.where(
            df["field_goals_attempted"] > 0,
            df["field_goals_made"] / df["field_goals_attempted"],
            0,
        )
        df["three_p_pct"] = np.where(
            df["three_point_field_goals_attempted"] > 0,
            df["three_point_field_goals_made"]
            / df["three_point_field_goals_attempted"],
            0,
        )
        df["ft_pct"] = np.where(
            df["free_throws_attempted"] > 0,
            df["free_throws_made"] / df["free_throws_attempted"],
            0,
        )

        stats_cols.extend(["fg_pct", "three_p_pct", "ft_pct"])

        # Create lag features (1, 2, 3, 5, 10 games back)
        lag_windows = [1, 2, 3, 5, 10]
        print(f"  Creating lag features for {len(stats_cols)} stats...")

        for stat in stats_cols:
            if stat not in df.columns:
                continue

            for lag in lag_windows:
                df[f"{stat}_lag{lag}"] = df.groupby("athlete_id")[stat].shift(lag)

        # Create rolling features (3, 5, 10, 20 game windows)
        rolling_windows = [3, 5, 10, 20]
        print(f"  Creating rolling window features...")

        for stat in stats_cols:
            if stat not in df.columns:
                continue

            for window in rolling_windows:
                # Rolling mean
                df[f"{stat}_rolling_{window}_mean"] = df.groupby("athlete_id")[
                    stat
                ].transform(lambda x: x.rolling(window, min_periods=1).mean())

                # Rolling std
                df[f"{stat}_rolling_{window}_std"] = df.groupby("athlete_id")[
                    stat
                ].transform(lambda x: x.rolling(window, min_periods=1).std())

        # Count panel features
        panel_features = [
            col for col in df.columns if "_lag" in col or "_rolling" in col
        ]
        print(f"  ✓ Created {len(panel_features)} panel features")

        return df

    def get_team_roster_mapping(
        self, df_players: pd.DataFrame, df_games: pd.DataFrame
    ) -> Dict[str, List[str]]:
        """
        Map teams to their current rosters based on most recent games

        Args:
            df_players: Player data
            df_games: Games data with team names

        Returns:
            Dict mapping team_name to list of player_ids
        """
        print("\nMapping team rosters...")

        # Create full team names in player data (location + name)
        df_players["full_team_name"] = (
            df_players["team_location"] + " " + df_players["team_name"]
        )

        # Get most recent game for each player
        latest_games = (
            df_players.sort_values("game_date_time").groupby("athlete_id").last()
        )

        # Get unique team names from games
        team_names = list(
            set(
                df_games["home_team_name"].tolist()
                + df_games["away_team_name"].tolist()
            )
        )

        rosters = {}
        for team_name in team_names:
            # Find players whose most recent team name matches (fuzzy matching)
            # Try exact match first
            team_players = latest_games[
                latest_games["full_team_name"] == team_name
            ].index.tolist()

            # If no exact match, try partial matching
            if len(team_players) == 0:
                # Try matching by team nickname (last word)
                team_nickname = team_name.split()[
                    -1
                ]  # e.g., "Raptors" from "Toronto Raptors"
                team_players = latest_games[
                    latest_games["team_name"] == team_nickname
                ].index.tolist()

            rosters[team_name] = team_players

        total_players = sum(len(roster) for roster in rosters.values())
        avg_roster = total_players / len(rosters) if len(rosters) > 0 else 0
        print(f"  ✓ Mapped {len(rosters)} teams to {total_players} players")
        print(f"  Avg roster size: {avg_roster:.1f} players")

        return rosters

    def prepare_game_features(
        self,
        game: pd.Series,
        df_players_panel: pd.DataFrame,
        rosters: Dict[str, List[str]],
    ) -> Optional[Dict]:
        """
        Prepare features for a single upcoming game

        Args:
            game: Game row from upcoming games DataFrame
            df_players_panel: Player data with panel features
            rosters: Team roster mappings

        Returns:
            Dict with game features or None if insufficient data
        """
        game_id = game["game_id"]
        home_team_name = game["home_team_name"]
        away_team_name = game["away_team_name"]

        # Get rosters (now mapped by team name, not ID)
        home_roster = rosters.get(home_team_name, [])
        away_roster = rosters.get(away_team_name, [])

        if len(home_roster) == 0 or len(away_roster) == 0:
            return None

        # Get latest data for each team's players
        home_players = df_players_panel[
            df_players_panel["athlete_id"].isin(home_roster)
        ]
        away_players = df_players_panel[
            df_players_panel["athlete_id"].isin(away_roster)
        ]

        # Get most recent stats for each player
        home_latest = home_players.groupby("athlete_id").last()
        away_latest = away_players.groupby("athlete_id").last()

        if len(home_latest) == 0 or len(away_latest) == 0:
            return None

        # Identify panel features
        panel_features = [
            col
            for col in df_players_panel.columns
            if "_lag" in col or "_rolling" in col
        ]

        # Aggregate team features using multiple functions
        home_features = self._aggregate_team_features(
            home_latest, panel_features, prefix="home"
        )
        away_features = self._aggregate_team_features(
            away_latest, panel_features, prefix="away"
        )

        # Calculate matchup differentials
        matchup_features = {}
        for feature in panel_features:
            if feature in home_features and feature in away_features:
                matchup_features[f"matchup_{feature}_diff"] = (
                    home_features[feature] - away_features[feature]
                )

        # Combine all features
        all_features = {
            "game_id": game_id,
            "game_date": game["game_date_local"],
            "home_team_name": home_team_name,
            "away_team_name": away_team_name,
            **home_features,
            **away_features,
            **matchup_features,
        }

        return all_features

    def _aggregate_team_features(
        self,
        team_player_data: pd.DataFrame,
        panel_features: List[str],
        prefix: str = "home",
    ) -> Dict:
        """
        Aggregate player features to team level

        Args:
            team_player_data: Player data for one team
            panel_features: List of panel feature names
            prefix: Feature name prefix ('home' or 'away')

        Returns:
            Dict of aggregated team features
        """
        agg_features = {}

        # Aggregation functions
        agg_funcs = ["mean", "std", "max", "min", "sum"]

        for feature in panel_features:
            if feature not in team_player_data.columns:
                continue

            values = team_player_data[feature].dropna()

            if len(values) == 0:
                continue

            for func_name in agg_funcs:
                if func_name == "mean":
                    agg_features[f"{prefix}_{feature}_mean"] = values.mean()
                elif func_name == "std":
                    agg_features[f"{prefix}_{feature}_std"] = (
                        values.std() if len(values) > 1 else 0
                    )
                elif func_name == "max":
                    agg_features[f"{prefix}_{feature}_max"] = values.max()
                elif func_name == "min":
                    agg_features[f"{prefix}_{feature}_min"] = values.min()
                elif func_name == "sum":
                    agg_features[f"{prefix}_{feature}_sum"] = values.sum()

        return agg_features


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Prepare features for upcoming NBA games"
    )
    parser.add_argument(
        "--games",
        type=str,
        default="/tmp/upcoming_games.parquet",
        help="Input upcoming games parquet file (default: /tmp/upcoming_games.parquet)",
    )
    parser.add_argument(
        "--players",
        type=str,
        default="/tmp/recent_player_data.parquet",
        help="Input recent player data parquet file (default: /tmp/recent_player_data.parquet)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/upcoming_games_features.parquet",
        help="Output features parquet file (default: /tmp/upcoming_games_features.parquet)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of games to process (for testing)",
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("PREPARING FEATURES FOR UPCOMING NBA GAMES")
    print(f"{'='*80}\n")

    # Load data
    print("Loading data...")
    try:
        df_games = pd.read_parquet(args.games)
        df_players = pd.read_parquet(args.players)
    except Exception as e:
        print(f"⚠️  Error loading data: {e}")
        sys.exit(1)

    print(f"  ✓ Loaded {len(df_games)} upcoming games")
    print(f"  ✓ Loaded {len(df_players):,} player records")

    # Initialize preparer
    preparer = UpcomingGameFeaturePreparer()

    # Create panel features
    df_players_panel = preparer.create_panel_features(df_players)

    # Get team rosters (now using team names)
    rosters = preparer.get_team_roster_mapping(df_players_panel, df_games)

    # Prepare features for each game
    print(f"\nPreparing features for {len(df_games)} games...")

    if args.limit:
        df_games = df_games.head(args.limit)
        print(f"  (Limited to first {args.limit} games for testing)")

    game_features_list = []

    for idx, game in df_games.iterrows():
        print(
            f"  [{idx+1}/{len(df_games)}] {game['away_team_name']} @ {game['home_team_name']}...",
            end=" ",
        )

        features = preparer.prepare_game_features(game, df_players_panel, rosters)

        if features is None:
            print("⚠️  Insufficient data")
            continue

        print(f"✓ {len(features)} features")
        game_features_list.append(features)

    if not game_features_list:
        print("\n⚠️  No games with sufficient data for feature extraction")
        sys.exit(1)

    # Create DataFrame
    df_features = pd.DataFrame(game_features_list)

    print(f"\n{'='*80}")
    print("FEATURE SUMMARY")
    print(f"{'='*80}")
    print(f"Games with features: {len(df_features)}")
    print(f"Features per game: {len(df_features.columns)}")
    print(
        f"Panel features included: Yes ({len([c for c in df_features.columns if '_lag' in c or '_rolling' in c])})"
    )
    print()

    # Save
    df_features.to_parquet(args.output, index=False)
    print(f"✓ Saved features to: {args.output}")
    print(f"\n✓ Successfully prepared features for {len(df_features)} upcoming games")
    print(f"✓ Ready for predictions (Step 4)")


if __name__ == "__main__":
    main()

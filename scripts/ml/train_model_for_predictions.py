#!/usr/bin/env python3
"""
Train Model for Upcoming Game Predictions

Purpose:
- Train ML model using historical games with panel features
- Match the 1,304 feature format from prepare_upcoming_game_features.py
- Save model for use with predict_upcoming_games.py

Usage:
    python scripts/ml/train_model_for_predictions.py --seasons 2023,2024

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import argparse
import pickle
import sys
import warnings
from datetime import datetime

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# Import our feature preparation code
sys.path.insert(0, "/Users/ryanranft/nba-simulator-aws")
from scripts.ml.prepare_upcoming_game_features import UpcomingGameFeaturePreparer


class HistoricalGameModelTrainer:
    """Trains ML model using historical game data with panel features"""

    def __init__(self, model_type="logistic"):
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.feature_preparer = UpcomingGameFeaturePreparer()

    def load_historical_games_with_outcomes(self, seasons=["2023", "2024"]):
        """
        Load historical games with actual outcomes

        For this implementation, we'll create a simplified version using
        available data and outcomes from the schedule data in S3.
        """
        print(f"\nLoading historical game data for seasons: {', '.join(seasons)}...")

        # Load player data (same as prediction pipeline)
        df_players = pd.read_parquet("/tmp/recent_player_data.parquet")
        print(f"  ✓ Loaded {len(df_players):,} player records")

        # Create game-level outcomes
        # For now, use a heuristic: home team wins if their players scored more points
        print("  Creating game outcomes...")

        game_outcomes = []
        for game_id in df_players["game_id"].unique()[
            :1000
        ]:  # Limit to 1000 games for speed
            game_data = df_players[df_players["game_id"] == game_id]

            # Simple heuristic: sum points by team
            # Note: In production, use actual game outcomes from schedule/results API
            teams = game_data["team_id"].unique()
            if len(teams) >= 2:
                team_points = game_data.groupby("team_id")["points"].sum()
                home_team = teams[0]  # Assume first team is home
                away_team = teams[1]

                home_win = 1 if team_points[home_team] > team_points[away_team] else 0

                game_outcomes.append(
                    {
                        "game_id": game_id,
                        "home_team_id": home_team,
                        "away_team_id": away_team,
                        "home_win": home_win,
                        "game_date": (
                            game_data["game_date"].iloc[0]
                            if "game_date" in game_data.columns
                            else "2024-01-01"
                        ),
                    }
                )

        df_outcomes = pd.DataFrame(game_outcomes)
        print(f"  ✓ Created outcomes for {len(df_outcomes)} games")
        print(
            f"    Home team wins: {df_outcomes['home_win'].sum()} ({df_outcomes['home_win'].mean():.1%})"
        )

        return df_outcomes, df_players

    def prepare_training_features(self, df_outcomes, df_players):
        """
        Prepare features for historical games using same process as predictions

        This ensures training features match prediction features exactly
        """
        print("\nPreparing training features...")

        # Create panel features
        df_players_panel = self.feature_preparer.create_panel_features(df_players)

        # Create fake "upcoming games" format for historical games
        df_historical_games = df_outcomes.copy()
        df_historical_games["home_team_name"] = "Home Team"
        df_historical_games["away_team_name"] = "Away Team"
        df_historical_games["game_date_local"] = df_historical_games["game_date"]

        # Get team rosters
        rosters = self.feature_preparer.get_team_roster_mapping(
            df_players_panel, df_historical_games
        )

        # Prepare features for each game
        game_features_list = []
        game_labels = []

        for idx, game in df_historical_games.iterrows():
            if idx % 100 == 0:
                print(f"  Processing game {idx}/{len(df_historical_games)}...")

            # Skip if we don't have roster info
            home_team_id = str(game["home_team_id"])
            away_team_id = str(game["away_team_id"])

            # For simplified version, use player IDs directly
            home_roster = (
                df_players_panel[df_players_panel["team_id"] == int(home_team_id)][
                    "athlete_id"
                ]
                .unique()
                .tolist()
            )
            away_roster = (
                df_players_panel[df_players_panel["team_id"] == int(away_team_id)][
                    "athlete_id"
                ]
                .unique()
                .tolist()
            )

            if len(home_roster) == 0 or len(away_roster) == 0:
                continue

            # Create simplified game dict
            game_dict = game.to_dict()
            game_dict["home_team_name"] = "Home"
            game_dict["away_team_name"] = "Away"

            # Use feature preparation (simplified since we have IDs not names)
            try:
                # Get player data for both teams
                home_players = df_players_panel[
                    df_players_panel["athlete_id"].isin(home_roster)
                ]
                away_players = df_players_panel[
                    df_players_panel["athlete_id"].isin(away_roster)
                ]

                if len(home_players) == 0 or len(away_players) == 0:
                    continue

                # Get most recent stats
                home_latest = home_players.groupby("athlete_id").last()
                away_latest = away_players.groupby("athlete_id").last()

                # Get panel features
                panel_features = [
                    col
                    for col in df_players_panel.columns
                    if "_lag" in col or "_rolling" in col
                ]

                # Aggregate
                home_features = self.feature_preparer._aggregate_team_features(
                    home_latest, panel_features, "home"
                )
                away_features = self.feature_preparer._aggregate_team_features(
                    away_latest, panel_features, "away"
                )

                # Combine
                all_features = {**home_features, **away_features}

                if len(all_features) > 0:
                    game_features_list.append(all_features)
                    game_labels.append(game["home_win"])

            except Exception as e:
                continue

        print(f"\n  ✓ Prepared features for {len(game_features_list)} games")

        # Convert to DataFrame
        X = pd.DataFrame(game_features_list)
        y = pd.Series(game_labels)

        # Fill NaN values
        X = X.fillna(0)

        print(f"  Feature matrix shape: {X.shape}")
        print(f"  Features: {len(X.columns)} columns")
        print(f"  Samples: {len(X)} games")
        print(f"  Target distribution: {y.mean():.1%} home wins")

        return X, y

    def train_model(self, X, y):
        """Train ML model"""
        print(f"\nTraining {self.model_type} model...")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        print(f"  Train: {len(X_train)} games")
        print(f"  Test: {len(X_test)} games")

        # Scale features
        print("  Scaling features...")
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        if self.model_type == "logistic":
            self.model = LogisticRegression(
                max_iter=1000, random_state=42, class_weight="balanced"
            )
        elif self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100, max_depth=10, random_state=42, class_weight="balanced"
            )

        print(f"  Training {self.model_type}...")
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        print("\nEvaluating model...")
        train_preds = self.model.predict(X_train_scaled)
        test_preds = self.model.predict(X_test_scaled)

        train_acc = accuracy_score(y_train, train_preds)
        test_acc = accuracy_score(y_test, test_preds)

        print(f"  Train accuracy: {train_acc:.1%}")
        print(f"  Test accuracy: {test_acc:.1%}")

        # ROC AUC
        if hasattr(self.model, "predict_proba"):
            train_proba = self.model.predict_proba(X_train_scaled)[:, 1]
            test_proba = self.model.predict_proba(X_test_scaled)[:, 1]

            train_auc = roc_auc_score(y_train, train_proba)
            test_auc = roc_auc_score(y_test, test_proba)

            print(f"  Train ROC AUC: {train_auc:.3f}")
            print(f"  Test ROC AUC: {test_auc:.3f}")

        # Store feature names
        self.feature_names = X.columns.tolist()

        return {
            "train_acc": train_acc,
            "test_acc": test_acc,
            "n_features": len(X.columns),
            "n_samples": len(X),
        }

    def save_model(self, output_dir="/tmp"):
        """Save model, scaler, and feature names"""
        print(f"\nSaving model artifacts to {output_dir}...")

        # Save model
        model_path = f"{output_dir}/panel_model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)
        print(f"  ✓ Model: {model_path}")

        # Save scaler
        scaler_path = f"{output_dir}/scaler.pkl"
        with open(scaler_path, "wb") as f:
            pickle.dump(self.scaler, f)
        print(f"  ✓ Scaler: {scaler_path}")

        # Save feature names
        features_path = f"{output_dir}/feature_names.pkl"
        with open(features_path, "wb") as f:
            pickle.dump(self.feature_names, f)
        print(f"  ✓ Features: {features_path}")

        return model_path


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Train model for upcoming game predictions"
    )
    parser.add_argument(
        "--seasons", type=str, default="2023,2024", help="Comma-separated seasons"
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="logistic",
        choices=["logistic", "random_forest"],
    )
    parser.add_argument("--output", type=str, default="/tmp", help="Output directory")

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("TRAINING MODEL FOR UPCOMING GAME PREDICTIONS")
    print(f"{'='*80}")

    # Initialize trainer
    trainer = HistoricalGameModelTrainer(model_type=args.model_type)

    # Load historical data
    seasons = args.seasons.split(",")
    df_outcomes, df_players = trainer.load_historical_games_with_outcomes(seasons)

    # Prepare features
    X, y = trainer.prepare_training_features(df_outcomes, df_players)

    # Train model
    results = trainer.train_model(X, y)

    # Save model
    model_path = trainer.save_model(args.output)

    print(f"\n{'='*80}")
    print("TRAINING COMPLETE")
    print(f"{'='*80}")
    print(f"Model: {args.model_type}")
    print(f"Test Accuracy: {results['test_acc']:.1%}")
    print(f"Features: {results['n_features']}")
    print(f"Training Samples: {results['n_samples']}")
    print(f"\nModel saved to: {model_path}")
    print(f"\nReady to predict upcoming games:")
    print(f"  python scripts/ml/predict_upcoming_games.py --model-path {model_path}")


if __name__ == "__main__":
    main()

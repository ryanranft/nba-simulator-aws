#!/usr/bin/env python3
"""
Predict Outcomes for Upcoming NBA Games

Purpose:
- Load trained ML model from MLflow
- Load upcoming game features
- Generate win probability predictions
- Output predictions with confidence levels

Usage:
    python scripts/ml/predict_upcoming_games.py
    python scripts/ml/predict_upcoming_games.py --features /tmp/upcoming_games_features.parquet

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import argparse
import os
import pickle
import sys
import warnings
from datetime import datetime
from typing import Dict, List, Optional

import mlflow
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

warnings.filterwarnings("ignore")


class UpcomingGamePredictor:
    """Predicts outcomes for upcoming NBA games using trained model"""

    def __init__(
        self, model_run_id: Optional[str] = None, model_path: Optional[str] = None
    ):
        """
        Initialize predictor with trained model

        Args:
            model_run_id: MLflow run ID (preferred method)
            model_path: Direct path to model pickle file (fallback)
        """
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_info = {}

        # Try loading from MLflow
        if model_run_id:
            try:
                print(f"Loading model from MLflow (run_id: {model_run_id[:8]}...)...")
                self.model = mlflow.sklearn.load_model(f"runs:/{model_run_id}/model")
                self.model_info["source"] = "mlflow"
                self.model_info["run_id"] = model_run_id
                print("✓ Model loaded from MLflow")
            except Exception as e:
                print(f"⚠️  MLflow load failed: {e}")
                print("Falling back to local model...")

        # Try loading from local file
        if self.model is None and model_path and os.path.exists(model_path):
            try:
                print(f"Loading model from {model_path}...")
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
                self.model_info["source"] = "local_file"
                self.model_info["path"] = model_path
                print("✓ Model loaded from local file")
            except Exception as e:
                print(f"⚠️  Local load failed: {e}")

        # Load scaler if available
        scaler_path = "/tmp/scaler.pkl"
        if os.path.exists(scaler_path):
            try:
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                print("✓ Scaler loaded")
            except Exception as e:
                print(f"⚠️  Scaler load failed: {e}")

        # Load feature names if available
        feature_names_path = "/tmp/feature_names.pkl"
        if os.path.exists(feature_names_path):
            try:
                with open(feature_names_path, "rb") as f:
                    self.feature_names = pickle.load(f)
                print(f"✓ Feature names loaded ({len(self.feature_names)} features)")
            except Exception as e:
                print(f"⚠️  Feature names load failed: {e}")

        if self.model is None:
            raise ValueError("Failed to load model from any source")

    def predict_game(self, features: Dict) -> Dict:
        """
        Predict outcome for a single game

        Args:
            features: Dict of game features

        Returns:
            Dict with prediction results
        """
        # Extract feature values (skip metadata columns)
        metadata_cols = ["game_id", "game_date", "home_team_name", "away_team_name"]
        feature_values = {k: v for k, v in features.items() if k not in metadata_cols}

        # Convert to DataFrame
        X = pd.DataFrame([feature_values])

        # Handle feature alignment
        if self.feature_names:
            # Use only features that exist in both training and prediction data
            matching_features = [f for f in self.feature_names if f in X.columns]

            if len(matching_features) == 0:
                # No matching features - create zero features for model
                print(
                    f"⚠️  No matching features found. Creating zero features for model."
                )
                X = pd.DataFrame(0, index=[0], columns=self.feature_names)
            elif len(matching_features) < len(self.feature_names):
                # Some features missing - fill with zeros
                for feature in self.feature_names:
                    if feature not in X.columns:
                        X[feature] = 0
                X = X[self.feature_names]
            else:
                # All features present
                X = X[self.feature_names]
        else:
            # No feature names available - try to use first N features
            n_features = (
                self.model.coef_.shape[1] if hasattr(self.model, "coef_") else 10
            )
            X = X.iloc[:, :n_features]

        # Fill any NaN values
        X = X.fillna(0)

        # Scale if scaler available
        if self.scaler:
            try:
                X_scaled = self.scaler.transform(X)
            except Exception as e:
                print(f"⚠️  Scaling failed: {e}. Using unscaled features.")
                X_scaled = X.values
        else:
            X_scaled = X.values

        # Make prediction
        home_win_prob = self.model.predict_proba(X_scaled)[0][1]

        # Determine predicted winner
        predicted_winner = (
            features["home_team_name"]
            if home_win_prob > 0.5
            else features["away_team_name"]
        )
        confidence = max(home_win_prob, 1 - home_win_prob)

        return {
            "game_id": features["game_id"],
            "game_date": features["game_date"],
            "home_team": features["home_team_name"],
            "away_team": features["away_team_name"],
            "home_win_probability": home_win_prob,
            "away_win_probability": 1 - home_win_prob,
            "predicted_winner": predicted_winner,
            "confidence": confidence,
            "prediction_strength": self._get_prediction_strength(confidence),
        }

    def _get_prediction_strength(self, confidence: float) -> str:
        """
        Categorize prediction strength based on confidence

        Args:
            confidence: Confidence level (0.5 to 1.0)

        Returns:
            Strength category string
        """
        if confidence >= 0.80:
            return "Very Strong"
        elif confidence >= 0.70:
            return "Strong"
        elif confidence >= 0.60:
            return "Moderate"
        else:
            return "Weak"

    def predict_all_games(self, df_features: pd.DataFrame) -> pd.DataFrame:
        """
        Predict outcomes for all games

        Args:
            df_features: DataFrame with game features

        Returns:
            DataFrame with predictions
        """
        predictions = []

        for idx, row in df_features.iterrows():
            try:
                pred = self.predict_game(row.to_dict())
                predictions.append(pred)
            except Exception as e:
                print(f"⚠️  Error predicting game {row.get('game_id', 'unknown')}: {e}")
                continue

        return pd.DataFrame(predictions)


def format_predictions_table(df_predictions: pd.DataFrame) -> str:
    """Format predictions as a nice table"""
    lines = []
    lines.append("=" * 120)
    lines.append("UPCOMING NBA GAME PREDICTIONS")
    lines.append("=" * 120)
    lines.append("")

    # Group by date
    for date in df_predictions["game_date"].unique():
        df_date = df_predictions[df_predictions["game_date"] == date].copy()

        lines.append(f"\n{date}")
        lines.append("-" * 120)

        for _, game in df_date.iterrows():
            home = game["home_team"]
            away = game["away_team"]
            winner = game["predicted_winner"]
            home_prob = game["home_win_probability"]
            away_prob = game["away_win_probability"]
            strength = game["prediction_strength"]

            # Format matchup
            home_marker = "→" if winner == home else " "
            away_marker = "→" if winner == away else " "

            lines.append(
                f"{away_marker} {away:30} @ {home_marker} {home:30}  |  "
                f"{home} {home_prob:5.1%} - {away} {away_prob:5.1%}  |  "
                f"{strength}"
            )

    lines.append("")
    lines.append("=" * 120)

    return "\n".join(lines)


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Predict outcomes for upcoming NBA games"
    )
    parser.add_argument(
        "--features",
        type=str,
        default="/tmp/upcoming_games_features.parquet",
        help="Input features parquet file (default: /tmp/upcoming_games_features.parquet)",
    )
    parser.add_argument(
        "--model-run-id",
        type=str,
        default="1a2725dca5304ec9ad9602756296153e",
        help="MLflow run ID (default: 1a2725dca5304ec9ad9602756296153e)",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default="/tmp/panel_model.pkl",
        help="Fallback model path (default: /tmp/panel_model.pkl)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/game_predictions.csv",
        help="Output predictions CSV (default: /tmp/game_predictions.csv)",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.0,
        help="Only show predictions with confidence >= threshold (default: 0.0)",
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("NBA GAME OUTCOME PREDICTIONS")
    print(f"{'='*80}\n")

    # Load features
    print("Loading game features...")
    try:
        df_features = pd.read_parquet(args.features)
        print(f"✓ Loaded features for {len(df_features)} games")
    except Exception as e:
        print(f"⚠️  Error loading features: {e}")
        sys.exit(1)

    # Initialize predictor
    try:
        predictor = UpcomingGamePredictor(
            model_run_id=args.model_run_id, model_path=args.model_path
        )
    except Exception as e:
        print(f"⚠️  Error initializing predictor: {e}")
        sys.exit(1)

    # Generate predictions
    print(f"\nGenerating predictions for {len(df_features)} games...")
    df_predictions = predictor.predict_all_games(df_features)

    if len(df_predictions) == 0:
        print("⚠️  No predictions generated")
        sys.exit(1)

    print(f"✓ Generated {len(df_predictions)} predictions")

    # Filter by confidence if requested
    if args.min_confidence > 0:
        before_count = len(df_predictions)
        df_predictions = df_predictions[
            df_predictions["confidence"] >= args.min_confidence
        ]
        after_count = len(df_predictions)
        print(
            f"  Filtered to {after_count} predictions with confidence >= {args.min_confidence:.1%} "
            f"({before_count - after_count} removed)"
        )

    # Save predictions
    df_predictions.to_csv(args.output, index=False)
    print(f"✓ Saved predictions to: {args.output}")

    # Display predictions
    print(format_predictions_table(df_predictions))

    # Summary statistics
    print("\nPREDICTION SUMMARY")
    print("=" * 80)
    print(f"Total games: {len(df_predictions)}")
    print(f"Avg confidence: {df_predictions['confidence'].mean():.1%}")
    print(
        f"High confidence (≥70%): {(df_predictions['confidence'] >= 0.70).sum()} games"
    )
    print(
        f"Very high confidence (≥80%): {(df_predictions['confidence'] >= 0.80).sum()} games"
    )
    print()

    print("✓ Predictions complete!")


if __name__ == "__main__":
    main()

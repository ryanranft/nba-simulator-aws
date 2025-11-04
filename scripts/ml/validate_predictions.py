#!/usr/bin/env python3
"""
Prediction Validation & Accuracy Tracking

Purpose:
- Compare predictions to actual game outcomes
- Track prediction accuracy over time
- Generate performance reports

Usage:
    python scripts/ml/validate_predictions.py --predictions predictions.csv --actual-games games.csv
    python scripts/ml/validate_predictions.py --date 2025-10-17

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd
import requests


class PredictionValidator:
    """Validates predictions against actual game outcomes"""

    def __init__(self):
        self.espn_api = (
            "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        )

    def fetch_actual_results(self, date: datetime) -> pd.DataFrame:
        """
        Fetch actual game results from ESPN API

        Args:
            date: Date to fetch results for

        Returns:
            DataFrame with actual results
        """
        print(f"\nFetching actual results for {date.strftime('%Y-%m-%d')}...")

        date_str = date.strftime("%Y%m%d")

        try:
            response = requests.get(
                self.espn_api, params={"dates": date_str}, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results = []
            if "events" in data:
                for event in data["events"]:
                    status = event.get("status", {}).get("type", {}).get("name", "")

                    # Only include completed games
                    if status != "STATUS_FINAL":
                        continue

                    game_id = event.get("id")
                    competitions = event.get("competitions", [])

                    if not competitions:
                        continue

                    competition = competitions[0]
                    competitors = competition.get("competitors", [])

                    if len(competitors) != 2:
                        continue

                    # Get teams and scores
                    home_team = None
                    away_team = None

                    for competitor in competitors:
                        team_info = competitor.get("team", {})
                        home_away = competitor.get("homeAway", "")
                        score = int(competitor.get("score", 0))
                        winner = competitor.get("winner", False)

                        team_data = {
                            "name": team_info.get("displayName", ""),
                            "score": score,
                            "winner": winner,
                        }

                        if home_away == "home":
                            home_team = team_data
                        else:
                            away_team = team_data

                    if not home_team or not away_team:
                        continue

                    results.append(
                        {
                            "game_id": game_id,
                            "game_date": date.strftime("%Y-%m-%d"),
                            "home_team": home_team["name"],
                            "away_team": away_team["name"],
                            "home_score": home_team["score"],
                            "away_score": away_team["score"],
                            "home_win": 1 if home_team["winner"] else 0,
                            "actual_winner": (
                                home_team["name"]
                                if home_team["winner"]
                                else away_team["name"]
                            ),
                        }
                    )

            df = pd.DataFrame(results)
            print(f"  ✓ Found {len(df)} completed games")
            return df

        except Exception as e:
            print(f"  ⚠️  Error fetching results: {e}")
            return pd.DataFrame()

    def validate_predictions(
        self, df_predictions: pd.DataFrame, df_actual: pd.DataFrame
    ) -> Dict:
        """
        Validate predictions against actual outcomes

        Args:
            df_predictions: DataFrame with predictions
            df_actual: DataFrame with actual results

        Returns:
            Dict with validation metrics
        """
        print("\nValidating predictions...")

        # Merge predictions with actual results
        # Match by team names since game IDs might differ
        merged = []

        for _, pred in df_predictions.iterrows():
            pred_home = pred.get("home_team", pred.get("home", ""))
            pred_away = pred.get("away_team", pred.get("away", ""))

            # Find matching actual game
            actual = df_actual[
                (
                    (df_actual["home_team"] == pred_home)
                    & (df_actual["away_team"] == pred_away)
                )
                | (
                    (df_actual["home_team"] == pred_away)
                    & (df_actual["away_team"] == pred_home)
                )
            ]

            if len(actual) == 0:
                continue

            actual_game = actual.iloc[0]

            # Get predicted winner
            pred_winner = pred.get("predicted_winner", "")
            if not pred_winner:
                if pred.get("home_prob", 0.5) > 0.5:
                    pred_winner = pred_home
                else:
                    pred_winner = pred_away

            # Check if prediction was correct
            correct = pred_winner == actual_game["actual_winner"]

            # Get predicted scores
            pred_home_score = pred.get("predicted_home_score", None)
            pred_away_score = pred.get("predicted_away_score", None)

            # Handle case where teams might be swapped in actual results
            actual_home_score = actual_game["home_score"]
            actual_away_score = actual_game["away_score"]

            # If teams are swapped, swap predicted scores too
            if actual_game["home_team"] != pred_home:
                # Teams are swapped, swap predicted scores
                pred_home_score, pred_away_score = pred_away_score, pred_home_score

            # Get predicted win probability
            home_win_prob = pred.get("home_win_probability", pred.get("home_prob", 0.5))
            if actual_game["home_team"] != pred_home:
                # Teams swapped, flip probability
                home_win_prob = 1.0 - home_win_prob

            merged.append(
                {
                    "game_date": actual_game["game_date"],
                    "home_team": actual_game["home_team"],
                    "away_team": actual_game["away_team"],
                    "predicted_winner": pred_winner,
                    "actual_winner": actual_game["actual_winner"],
                    "predicted_home_score": pred_home_score,
                    "predicted_away_score": pred_away_score,
                    "home_score": actual_home_score,
                    "away_score": actual_away_score,
                    "correct": correct,
                    "confidence": pred.get("confidence", 0.5),
                    "prediction_strength": pred.get("prediction_strength", pred.get("strength", "Unknown")),
                    "home_win_probability": home_win_prob,
                }
            )

        df_merged = pd.DataFrame(merged)

        if len(df_merged) == 0:
            print("  ⚠️  No matching games found")
            return {"total_games": 0, "accuracy": 0.0, "correct": 0, "incorrect": 0}

        # Calculate metrics
        total_games = len(df_merged)
        correct_predictions = df_merged["correct"].sum()
        accuracy = correct_predictions / total_games

        print(f"  Total games validated: {total_games}")
        print(f"  Correct predictions: {correct_predictions}")
        print(f"  Incorrect predictions: {total_games - correct_predictions}")
        print(f"  Accuracy: {accuracy:.1%}")

        # Calculate score accuracy metrics
        score_metrics = {}
        if "predicted_home_score" in df_merged.columns and "predicted_away_score" in df_merged.columns:
            # Filter out rows with missing predicted scores
            df_with_scores = df_merged[
                df_merged["predicted_home_score"].notna() & df_merged["predicted_away_score"].notna()
            ].copy()

            if len(df_with_scores) > 0:
                # Calculate score differences
                df_with_scores["home_score_error"] = (
                    df_with_scores["predicted_home_score"] - df_with_scores["home_score"]
                )
                df_with_scores["away_score_error"] = (
                    df_with_scores["predicted_away_score"] - df_with_scores["away_score"]
                )
                df_with_scores["predicted_total"] = (
                    df_with_scores["predicted_home_score"] + df_with_scores["predicted_away_score"]
                )
                df_with_scores["actual_total"] = (
                    df_with_scores["home_score"] + df_with_scores["away_score"]
                )
                df_with_scores["total_error"] = (
                    df_with_scores["predicted_total"] - df_with_scores["actual_total"]
                )
                df_with_scores["predicted_margin"] = (
                    df_with_scores["predicted_home_score"] - df_with_scores["predicted_away_score"]
                )
                df_with_scores["actual_margin"] = (
                    df_with_scores["home_score"] - df_with_scores["away_score"]
                )
                df_with_scores["margin_error"] = (
                    df_with_scores["predicted_margin"] - df_with_scores["actual_margin"]
                )

                # Score MAE (Mean Absolute Error)
                home_score_mae = df_with_scores["home_score_error"].abs().mean()
                away_score_mae = df_with_scores["away_score_error"].abs().mean()
                score_mae = (home_score_mae + away_score_mae) / 2

                # Score RMSE (Root Mean Squared Error)
                home_score_rmse = np.sqrt((df_with_scores["home_score_error"] ** 2).mean())
                away_score_rmse = np.sqrt((df_with_scores["away_score_error"] ** 2).mean())
                score_rmse = np.sqrt((home_score_rmse ** 2 + away_score_rmse ** 2) / 2)

                # Total Points MAE
                total_points_mae = df_with_scores["total_error"].abs().mean()

                # Margin MAE
                margin_mae = df_with_scores["margin_error"].abs().mean()

                # Brier Score (probability calibration)
                # Calculate actual home win from actual winner
                if "home_win" in df_with_scores.columns:
                    actual_home_win = df_with_scores["home_win"].values
                else:
                    actual_home_win = (df_with_scores["actual_winner"] == df_with_scores["home_team"]).astype(int).values
                pred_home_win_prob = df_with_scores["home_win_probability"].values
                brier_score = np.mean((pred_home_win_prob - actual_home_win) ** 2)

                score_metrics = {
                    "home_score_mae": home_score_mae,
                    "away_score_mae": away_score_mae,
                    "score_mae": score_mae,
                    "home_score_rmse": home_score_rmse,
                    "away_score_rmse": away_score_rmse,
                    "score_rmse": score_rmse,
                    "total_points_mae": total_points_mae,
                    "margin_mae": margin_mae,
                    "brier_score": brier_score,
                }

                print(f"\n  Score Accuracy Metrics:")
                print(f"    Home Score MAE: {home_score_mae:.2f} points")
                print(f"    Away Score MAE: {away_score_mae:.2f} points")
                print(f"    Average Score MAE: {score_mae:.2f} points")
                print(f"    Home Score RMSE: {home_score_rmse:.2f} points")
                print(f"    Away Score RMSE: {away_score_rmse:.2f} points")
                print(f"    Average Score RMSE: {score_rmse:.2f} points")
                print(f"    Total Points MAE: {total_points_mae:.2f} points")
                print(f"    Margin MAE: {margin_mae:.2f} points")
                print(f"    Brier Score: {brier_score:.4f} (lower is better)")

        # Accuracy by confidence level
        print("\n  Accuracy by confidence level:")
        for strength in ["Strong", "Moderate", "Weak"]:
            strength_games = df_merged[df_merged["prediction_strength"] == strength]
            if len(strength_games) > 0:
                strength_acc = strength_games["correct"].mean()
                print(
                    f"    {strength}: {strength_acc:.1%} ({len(strength_games)} games)"
                )

        return {
            "total_games": total_games,
            "correct": correct_predictions,
            "incorrect": total_games - correct_predictions,
            "accuracy": accuracy,
            "score_metrics": score_metrics,
            "by_strength": {
                strength: {
                    "games": len(
                        df_merged[df_merged["prediction_strength"] == strength]
                    ),
                    "accuracy": df_merged[df_merged["prediction_strength"] == strength][
                        "correct"
                    ].mean(),
                }
                for strength in ["Strong", "Moderate", "Weak"]
                if len(df_merged[df_merged["prediction_strength"] == strength]) > 0
            },
            "details": df_merged,
        }

    def generate_report(self, validation_results: Dict, output_path: str = None):
        """
        Generate validation report

        Args:
            validation_results: Results from validate_predictions
            output_path: Optional path to save report
        """
        print("\n" + "=" * 80)
        print("PREDICTION VALIDATION REPORT")
        print("=" * 80)

        print(f"\nOverall Performance:")
        print(f"  Total Games: {validation_results['total_games']}")
        print(f"  Correct: {validation_results['correct']}")
        print(f"  Incorrect: {validation_results['incorrect']}")
        print(f"  Accuracy: {validation_results['accuracy']:.1%}")

        # Score accuracy metrics
        if "score_metrics" in validation_results and validation_results["score_metrics"]:
            metrics = validation_results["score_metrics"]
            print(f"\nScore Accuracy Metrics:")
            print(f"  Home Score MAE: {metrics.get('home_score_mae', 0):.2f} points")
            print(f"  Away Score MAE: {metrics.get('away_score_mae', 0):.2f} points")
            print(f"  Average Score MAE: {metrics.get('score_mae', 0):.2f} points")
            print(f"  Average Score RMSE: {metrics.get('score_rmse', 0):.2f} points")
            print(f"  Total Points MAE: {metrics.get('total_points_mae', 0):.2f} points")
            print(f"  Margin MAE: {metrics.get('margin_mae', 0):.2f} points")
            print(f"  Brier Score: {metrics.get('brier_score', 0):.4f} (lower is better)")

        print(f"\nAccuracy by Prediction Strength:")
        for strength, metrics in validation_results.get("by_strength", {}).items():
            print(f"  {strength}: {metrics['accuracy']:.1%} ({metrics['games']} games)")

        # Show game-by-game comparison
        if "details" in validation_results:
            df_details = validation_results["details"]

            print(f"\nGame-by-Game Comparison:")
            print(f"{'='*100}")
            for _, game in df_details.iterrows():
                status = "✓" if game["correct"] else "✗"
                print(f"\n{status} {game['away_team']} @ {game['home_team']}")

                # Winner prediction
                print(f"  Winner: Predicted {game['predicted_winner']}, Actual {game['actual_winner']}")

                # Score prediction
                if pd.notna(game.get("predicted_home_score")) and pd.notna(game.get("predicted_away_score")):
                    print(f"  Score: Predicted {game['home_team']} {game['predicted_home_score']:.1f} - {game['away_team']} {game['predicted_away_score']:.1f}")
                    print(f"         Actual    {game['home_team']} {game['home_score']} - {game['away_team']} {game['away_score']}")

                    # Calculate errors
                    home_error = game['predicted_home_score'] - game['home_score']
                    away_error = game['predicted_away_score'] - game['away_score']
                    total_error = (game['predicted_home_score'] + game['predicted_away_score']) - (game['home_score'] + game['away_score'])
                    print(f"  Errors: Home {home_error:+.1f}, Away {away_error:+.1f}, Total {total_error:+.1f}")
                else:
                    print(f"  Score: Actual {game['home_team']} {game['home_score']} - {game['away_team']} {game['away_score']}")

                print(f"  Strength: {game['prediction_strength']}, Confidence: {game['confidence']:.1%}")

            # Show incorrect predictions summary
            incorrect = df_details[~df_details["correct"]]
            if len(incorrect) > 0:
                print(f"\n\nIncorrect Predictions Summary ({len(incorrect)}):")
                for _, game in incorrect.iterrows():
                    print(f"  {game['away_team']} @ {game['home_team']}")
                    print(
                        f"    Predicted: {game['predicted_winner']}, Actual: {game['actual_winner']}"
                    )

        # Save report
        if output_path and "details" in validation_results:
            df_details = validation_results["details"]
            df_details.to_csv(output_path, index=False)
            print(f"\n✓ Detailed report saved to: {output_path}")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Validate prediction accuracy")
    parser.add_argument("--predictions", type=str, help="Path to predictions CSV")
    parser.add_argument("--date", type=str, help="Date to validate (YYYY-MM-DD)")
    parser.add_argument(
        "--days-back", type=int, default=1, help="Number of days to look back"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/validation_report.csv",
        help="Output report path",
    )

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("PREDICTION VALIDATION")
    print(f"{'='*80}")

    validator = PredictionValidator()

    # Determine date range
    if args.date:
        date = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        # Use yesterday by default (games completed)
        date = datetime.now() - timedelta(days=args.days_back)

    # Fetch actual results
    df_actual = validator.fetch_actual_results(date)

    if df_actual.empty:
        print("\n⚠️  No completed games found for validation")
        sys.exit(0)

    # Load predictions
    if args.predictions:
        print(f"\nLoading predictions from {args.predictions}...")
        df_predictions = pd.read_csv(args.predictions)
    else:
        # Try to load from default location
        default_path = "/tmp/demo_game_predictions.csv"
        if not os.path.exists(default_path):
            print(f"\n⚠️  No predictions file found")
            sys.exit(1)

        print(f"\nLoading predictions from {default_path}...")
        df_predictions = pd.read_csv(default_path)

    # Filter predictions to match date
    if "game_date" in df_predictions.columns:
        df_predictions = df_predictions[
            df_predictions["game_date"] == date.strftime("%Y-%m-%d")
        ]

    print(f"  ✓ Loaded {len(df_predictions)} predictions")

    # Validate
    results = validator.validate_predictions(df_predictions, df_actual)

    # Generate report
    validator.generate_report(results, args.output)

    print(f"\n{'='*80}")
    print(f"VALIDATION COMPLETE")
    print(f"{'='*80}")
    print(f"Accuracy: {results['accuracy']:.1%}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    import os

    main()

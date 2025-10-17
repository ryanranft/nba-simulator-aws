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

            merged.append(
                {
                    "game_date": actual_game["game_date"],
                    "home_team": actual_game["home_team"],
                    "away_team": actual_game["away_team"],
                    "predicted_winner": pred_winner,
                    "actual_winner": actual_game["actual_winner"],
                    "home_score": actual_game["home_score"],
                    "away_score": actual_game["away_score"],
                    "correct": correct,
                    "confidence": pred.get("confidence", 0.5),
                    "prediction_strength": pred.get("strength", "Unknown"),
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

        print(f"\nAccuracy by Prediction Strength:")
        for strength, metrics in validation_results.get("by_strength", {}).items():
            print(f"  {strength}: {metrics['accuracy']:.1%} ({metrics['games']} games)")

        # Show incorrect predictions
        if "details" in validation_results:
            df_details = validation_results["details"]
            incorrect = df_details[~df_details["correct"]]

            if len(incorrect) > 0:
                print(f"\nIncorrect Predictions ({len(incorrect)}):")
                for _, game in incorrect.iterrows():
                    print(f"  {game['away_team']} @ {game['home_team']}")
                    print(
                        f"    Predicted: {game['predicted_winner']}, Actual: {game['actual_winner']}"
                    )
                    print(
                        f"    Score: {game['away_team']} {game['away_score']} - {game['home_team']} {game['home_score']}"
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

#!/usr/bin/env python3
"""
Generate Predictions for ALL Upcoming Games from ESPN API

This script fetches all upcoming games from ESPN API and generates
predictions for all of them using the advanced multi-simulator framework.

Usage:
    python scripts/ml/generate_all_upcoming_predictions.py --days 3

Created: November 2, 2025
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.ml.advanced_multi_simulator import AdvancedMultiSimulator
from scripts.ml.fetch_upcoming_games import UpcomingGamesFetcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_all_games(days_ahead: int = 3) -> pd.DataFrame:
    """Fetch all upcoming games from ESPN API"""
    logger.info(f"Fetching upcoming games for next {days_ahead} days...")
    fetcher = UpcomingGamesFetcher()
    df_games = fetcher.fetch_upcoming_games(days_ahead=days_ahead)

    if len(df_games) == 0:
        logger.warning("No games found")
        return pd.DataFrame()

    logger.info(f"✓ Found {len(df_games)} upcoming games")
    return df_games


def generate_predictions_for_all_games(
    games_df: pd.DataFrame,
    simulator: AdvancedMultiSimulator,
    output_dir: Path
) -> pd.DataFrame:
    """Generate predictions for all games in the DataFrame"""

    predictions = []

    for _, game in games_df.iterrows():
        game_id = str(game['game_id'])
        game_date_str = game['game_date_local']
        home_team_name = game['home_team_name']
        away_team_name = game['away_team_name']

        # Parse date
        try:
            game_date = pd.to_datetime(game_date_str).date()
        except:
            logger.warning(f"  ⚠️  Could not parse date for {game_id}: {game_date_str}")
            continue

        logger.info(f"Predicting: {away_team_name} @ {home_team_name} ({game_date})")

        # Get team IDs from database
        query = """
        SELECT team_id, team_name
        FROM teams
        WHERE team_name IN (%s, %s)
        """

        try:
            teams = simulator.db.query(query, params=(home_team_name, away_team_name))

            home_team_id = None
            away_team_id = None

            for _, team_row in teams.iterrows():
                if team_row['team_name'] == home_team_name:
                    home_team_id = team_row['team_id']
                elif team_row['team_name'] == away_team_name:
                    away_team_id = team_row['team_id']

            if not home_team_id or not away_team_id:
                logger.warning(f"  ⚠️  Could not find team IDs for {home_team_name} / {away_team_name}")
                # Try alternative team name matching
                # Map common variations
                name_mapping = {
                    'LA Clippers': 'Los Angeles Clippers',
                    'LA Lakers': 'Los Angeles Lakers',
                    'L.A. Clippers': 'Los Angeles Clippers',
                    'L.A. Lakers': 'Los Angeles Lakers',
                }

                home_lookup = name_mapping.get(home_team_name, home_team_name)
                away_lookup = name_mapping.get(away_team_name, away_team_name)

                teams = simulator.db.query(query, params=(home_lookup, away_lookup))

                for _, team_row in teams.iterrows():
                    if team_row['team_name'] == home_lookup:
                        home_team_id = team_row['team_id']
                    elif team_row['team_name'] == away_lookup:
                        away_team_id = team_row['team_id']

            if not home_team_id or not away_team_id:
                logger.warning(f"  ✗ Skipping {game_id}: Could not match team names")
                continue

            # Get ensemble prediction
            ensemble_result, individual_results = simulator.predict_game(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                game_date=game_date,
                use_ensemble=True,
                n_simulations=10000
            )

            # Extract individual model predictions
            panel_result = next((r for r in individual_results if r.model_type == 'panel_regression'), None)
            bayesian_result = next((r for r in individual_results if r.model_type == 'hierarchical_bayesian'), None)
            simultaneous_result = next((r for r in individual_results if r.model_type == 'simultaneous_equations'), None)

            # Calculate prediction strength
            confidence = ensemble_result.confidence

            if confidence >= 0.75:
                prediction_strength = "Very Strong"
            elif confidence >= 0.65:
                prediction_strength = "Strong"
            elif confidence >= 0.55:
                prediction_strength = "Moderate"
            elif confidence >= 0.45:
                prediction_strength = "Weak"
            else:
                prediction_strength = "Very Weak"

            # Calculate model agreement
            individual_probs = [r.home_win_prob for r in individual_results]
            model_agreement = 1.0 - (np.std(individual_probs) if len(individual_probs) > 1 else 0.2)
            model_agreement = max(0.0, min(1.0, model_agreement))

            prediction = {
                'game_id': game_id,
                'game_date': game_date,
                'home_team': home_team_name,
                'away_team': away_team_name,
                'predicted_winner': home_team_name if ensemble_result.home_win_prob > 0.5 else away_team_name,
                'home_win_probability': ensemble_result.home_win_prob,
                'away_win_probability': ensemble_result.away_win_prob,
                'predicted_home_score': ensemble_result.predicted_home_score,
                'predicted_away_score': ensemble_result.predicted_away_score,
                'confidence': confidence,
                'prediction_strength': prediction_strength,
                'model_agreement': model_agreement,
                'num_models': len(individual_results),
                'panel_home_win_prob': panel_result.home_win_prob if panel_result else None,
                'panel_confidence': panel_result.confidence if panel_result else None,
                'bayesian_home_win_prob': bayesian_result.home_win_prob if bayesian_result else None,
                'bayesian_confidence': bayesian_result.confidence if bayesian_result else None,
                'simultaneous_home_win_prob': simultaneous_result.home_win_prob if simultaneous_result else None,
                'simultaneous_confidence': simultaneous_result.confidence if simultaneous_result else None,
            }

            predictions.append(prediction)

            logger.info(f"  ✓ {prediction_strength}: {prediction['predicted_winner']} ({ensemble_result.home_win_prob:.1%})")

        except Exception as e:
            logger.error(f"  ✗ Error predicting {game_id}: {e}")
            continue

    if len(predictions) == 0:
        logger.warning("No predictions generated")
        return pd.DataFrame()

    df_predictions = pd.DataFrame(predictions)

    # Save predictions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"predictions_all_{timestamp}.csv"
    df_predictions.to_csv(output_file, index=False)

    # Create symlink
    latest_path = output_dir / "predictions_latest.csv"
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    latest_path.symlink_to(output_file.name)

    logger.info(f"\n✓ Saved {len(predictions)} predictions to: {output_file}")
    logger.info(f"✓ Symlink: {latest_path}")

    return df_predictions


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate predictions for all upcoming games"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=3,
        help='Number of days ahead to fetch games (default: 3)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/tmp/nba_predictions',
        help='Output directory for predictions'
    )

    args = parser.parse_args()

    logger.info("="*80)
    logger.info("GENERATING PREDICTIONS FOR ALL UPCOMING GAMES")
    logger.info("="*80)
    logger.info(f"Days ahead: {args.days}")
    logger.info("")

    # Fetch all upcoming games
    games_df = fetch_all_games(days_ahead=args.days)

    if len(games_df) == 0:
        logger.error("No games found. Exiting.")
        return

    # Initialize simulator
    logger.info("Initializing advanced multi-simulator framework...")
    simulator = AdvancedMultiSimulator()

    try:
        # Train all simulators
        logger.info("\n[1/2] Training all simulators...")
        simulator.train_all(start_season=2020, end_season=2024)
        logger.info("✓ All simulators trained")

        # Generate predictions
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"\n[2/2] Generating predictions for {len(games_df)} games...")
        predictions_df = generate_predictions_for_all_games(
            games_df, simulator, output_dir
        )

        if len(predictions_df) > 0:
            # Display summary
            print("\n" + "="*80)
            print("PREDICTIONS SUMMARY")
            print("="*80)
            print()

            print(f"Total predictions: {len(predictions_df)}")
            print(f"By strength:")
            for strength in ["Very Strong", "Strong", "Moderate", "Weak", "Very Weak"]:
                count = len(predictions_df[predictions_df['prediction_strength'] == strength])
                if count > 0:
                    print(f"  {strength}: {count}")

            print()
            print("Predictions by date:")
            for game_date, group in predictions_df.groupby('game_date'):
                print(f"\n{game_date}: {len(group)} games")
                for _, pred in group.iterrows():
                    print(f"  {pred['away_team']} @ {pred['home_team']}")
                    print(f"    Predicted Winner: {pred['predicted_winner']} ({pred['home_win_probability'] if pred['predicted_winner'] == pred['home_team'] else pred['away_win_probability']:.1%})")
                    print(f"    Confidence: {pred['confidence']:.1%} | Strength: {pred['prediction_strength']}")

            print()
            print(f"✓ Predictions saved to: {output_dir}")

    finally:
        simulator.close()
        logger.info("\n✓ Complete")


if __name__ == "__main__":
    main()


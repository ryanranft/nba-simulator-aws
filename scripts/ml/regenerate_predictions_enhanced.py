#!/usr/bin/env python3
"""
Regenerate Predictions with Enhanced Confidence Calculation

This script takes existing predictions and regenerates them using the
improved confidence calculation that considers:
1. Model agreement (lower variance = higher confidence)
2. Prediction margin (larger margin = higher confidence)
3. Number of successful models (more models agreeing = higher confidence)
4. Individual model confidence quality

Usage:
    python scripts/ml/regenerate_predictions_enhanced.py --predictions /tmp/nba_predictions/predictions_latest.csv

Created: November 2, 2025
"""

import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from advanced_multi_simulator import AdvancedMultiSimulator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def regenerate_predictions(input_csv: str, output_dir: str = "/tmp/nba_predictions"):
    """Regenerate predictions with enhanced confidence"""

    logger.info("="*80)
    logger.info("REGENERATING PREDICTIONS WITH ENHANCED CONFIDENCE")
    logger.info("="*80)
    logger.info("")

    # Load existing predictions
    logger.info(f"Loading predictions from: {input_csv}")
    df_existing = pd.read_csv(input_csv)
    logger.info(f"✓ Loaded {len(df_existing)} predictions")
    logger.info("")

    # Initialize simulator
    logger.info("Initializing advanced multi-simulator framework...")
    simulator = AdvancedMultiSimulator()

    try:
        # Train all simulators
        logger.info("\n[1/2] Training all simulators...")
        simulator.train_all(start_season=2020, end_season=2024)
        logger.info("✓ All simulators trained")

        # Generate enhanced predictions
        logger.info("\n[2/2] Generating enhanced predictions...")
        enhanced_predictions = []

        for idx, row in df_existing.iterrows():
            game_id = row['game_id']
            game_date = pd.to_datetime(row['game_date']).date()

            # Try to get team IDs from existing data or database
            # For now, use team names to look up IDs
            home_team_name = row['home_team']
            away_team_name = row['away_team']

            logger.info(f"Predicting: {away_team_name} @ {home_team_name}")

            try:
                # Get team IDs from database
                query = """
                SELECT team_id, team_name
                FROM teams
                WHERE team_name = %s OR team_name = %s
                """
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
                    # Use existing prediction with enhanced confidence
                    enhanced_confidence = min(1.0, max(0.2, abs(row['home_win_probability'] - 0.5) * 2 * 1.3))

                    if enhanced_confidence >= 0.75:
                        prediction_strength = "Very Strong"
                    elif enhanced_confidence >= 0.65:
                        prediction_strength = "Strong"
                    elif enhanced_confidence >= 0.55:
                        prediction_strength = "Moderate"
                    elif enhanced_confidence >= 0.45:
                        prediction_strength = "Weak"
                    else:
                        prediction_strength = "Very Weak"

                    enhanced_predictions.append({
                        'game_id': game_id,
                        'game_date': row['game_date'],
                        'home_team': home_team_name,
                        'away_team': away_team_name,
                        'predicted_winner': row.get('predicted_winner', ''),
                        'home_win_probability': row['home_win_probability'],
                        'away_win_probability': row['away_win_probability'],
                        'predicted_home_score': row.get('predicted_home_score', 110.0),
                        'predicted_away_score': row.get('predicted_away_score', 108.0),
                        'confidence': enhanced_confidence,
                        'prediction_strength': prediction_strength,
                    })
                    continue

                # Get ensemble prediction with enhanced confidence
                ensemble_result, individual_results = simulator.predict_game(
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    game_date=game_date,
                    use_ensemble=True,
                    n_simulations=10000
                )

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

                enhanced_predictions.append({
                    'game_id': game_id,
                    'game_date': row['game_date'],
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
                })

                logger.info(f"  ✓ Enhanced: {prediction_strength} ({confidence:.1%} confidence)")

            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
                continue

        # Save enhanced predictions
        df_enhanced = pd.DataFrame(enhanced_predictions)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"predictions_enhanced_{timestamp}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df_enhanced.to_csv(output_path, index=False)

        # Create symlink
        latest_path = Path(output_dir) / "predictions_latest.csv"
        if latest_path.exists() or latest_path.is_symlink():
            latest_path.unlink()
        latest_path.symlink_to(output_path.name)

        logger.info("")
        logger.info("="*80)
        logger.info("ENHANCED PREDICTIONS SUMMARY")
        logger.info("="*80)
        logger.info("")

        for strength in ["Very Strong", "Strong", "Moderate", "Weak", "Very Weak"]:
            count = len(df_enhanced[df_enhanced['prediction_strength'] == strength])
            if count > 0:
                logger.info(f"{strength}: {count} games")

        logger.info("")
        logger.info(f"✓ Saved to: {output_path}")
        logger.info(f"✓ Symlink: {latest_path}")
        logger.info("")

        # Display predictions
        print("\n" + "="*80)
        print("ENHANCED PREDICTIONS")
        print("="*80)
        print()

        for _, pred in df_enhanced.iterrows():
            print(f"{pred['away_team']} @ {pred['home_team']}")
            print(f"  Predicted Winner: {pred['predicted_winner']} ({pred['home_win_probability']:.1%})")
            print(f"  Confidence: {pred['confidence']:.1%} | Strength: {pred['prediction_strength']}")
            if 'model_agreement' in pred and pd.notna(pred['model_agreement']):
                print(f"  Model Agreement: {pred['model_agreement']:.1%}")
            print()

        return df_enhanced

    finally:
        simulator.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Regenerate predictions with enhanced confidence calculation"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default="/tmp/nba_predictions/predictions_latest.csv",
        help="Path to existing predictions CSV"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp/nba_predictions",
        help="Output directory for enhanced predictions"
    )

    args = parser.parse_args()

    regenerate_predictions(args.predictions, args.output_dir)



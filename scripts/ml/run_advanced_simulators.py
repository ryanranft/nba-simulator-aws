#!/usr/bin/env python3
"""
Run Advanced Multi-Simulators for Today's Games

Purpose: Execute all advanced statistical simulators and generate comprehensive
predictions using econometric methods and temporal panel data.

Usage:
    python scripts/ml/run_advanced_simulators.py
    python scripts/ml/run_advanced_simulators.py --date 2025-11-02
    python scripts/ml/run_advanced_simulators.py --team-id 1610612744 --opponent-id 1610612737

Created: November 2, 2025
Author: NBA Simulator AWS Project
"""

import argparse
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from advanced_multi_simulator import AdvancedMultiSimulator, EnsembleResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_upcoming_games(game_date: date) -> pd.DataFrame:
    """Fetch upcoming games from ESPN API (includes in-progress games with game_state)"""
    import psycopg2
    import os
    from dotenv import load_dotenv
    from datetime import timedelta

    load_dotenv("/Users/ryanranft/nba-sim-credentials.env")

    # Use UpcomingGamesFetcher to get games with game_state support
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from scripts.ml.fetch_upcoming_games import UpcomingGamesFetcher

    fetcher = UpcomingGamesFetcher()

    # Fetch games for today and tomorrow (to catch games that might be in progress)
    days_ahead = 1 if game_date == date.today() else 0

    games_df = fetcher.fetch_upcoming_games(days_ahead=days_ahead)

    if len(games_df) == 0:
        logger.warning(f"No games found for {game_date}")
        return pd.DataFrame()

    # Filter to requested date if needed
    if 'game_date_local' in games_df.columns:
        games_df['game_date_local'] = pd.to_datetime(games_df['game_date_local'])
        games_df = games_df[games_df['game_date_local'].dt.date == game_date]

    if len(games_df) == 0:
        logger.warning(f"No games found for {game_date}")
        return pd.DataFrame()

    # Get team IDs from database (needed for simulator)
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )

    # Map team names to team IDs
    team_ids = {}
    for _, game in games_df.iterrows():
        for team_type in ['home', 'away']:
            team_name = game[f'{team_type}_team_name']
            if team_name not in team_ids:
                query = """
                SELECT team_id FROM teams
                WHERE LOWER(team_name) LIKE LOWER(%s)
                   OR LOWER(team_name) LIKE LOWER(%s)
                LIMIT 1
                """
                cursor = conn.cursor()
                cursor.execute(query, (f'%{team_name}%', team_name.replace(' ', '%')))
                result = cursor.fetchone()
                if result:
                    team_ids[team_name] = str(result[0])  # Convert to string for simulator
                cursor.close()

    conn.close()

    # Add team IDs to games_df
    games_df['home_team_id'] = games_df['home_team_name'].map(team_ids)
    games_df['away_team_id'] = games_df['away_team_name'].map(team_ids)

    # Remove games without team IDs
    games_df = games_df[games_df['home_team_id'].notna() & games_df['away_team_id'].notna()]

    logger.info(f"✓ Found {len(games_df)} games for {game_date}")

    # Log in-progress games
    if 'status' in games_df.columns:
        in_progress = games_df[games_df['status'] == 'STATUS_IN_PROGRESS']
        if len(in_progress) > 0:
            logger.info(f"  {len(in_progress)} games are in-progress")

    return games_df


def generate_comprehensive_predictions(
    simulator: AdvancedMultiSimulator,
    games_df: pd.DataFrame,
    output_dir: Path
) -> pd.DataFrame:
    """Generate predictions for all games using advanced simulators"""

    predictions = []

    for _, game in games_df.iterrows():
        game_id = game['game_id']
        game_date = game['game_date']
        home_team_id = game['home_team_id']
        away_team_id = game['away_team_id']
        home_team_name = game['home_team_name']
        away_team_name = game['away_team_name']

        # Parse game_date if it's a string
        if isinstance(game_date, str):
            try:
                from datetime import datetime
                game_date_obj = datetime.fromisoformat(game_date.replace('Z', '+00:00')).date()
            except:
                # Try parsing as date string
                try:
                    from datetime import datetime
                    game_date_obj = datetime.strptime(game_date, '%Y-%m-%d').date()
                except:
                    logger.error(f"  ✗ Could not parse game_date: {game_date}")
                    continue
        elif hasattr(game_date, 'date'):
            game_date_obj = game_date.date()
        else:
            game_date_obj = game_date

        # Check if game is in-progress and has game_state
        game_state = None
        if 'game_state' in game and pd.notna(game.get('game_state')):
            # Handle if game_state is stored as dict or string
            if isinstance(game['game_state'], dict):
                game_state = game['game_state']
            elif isinstance(game['game_state'], str):
                import json
                try:
                    game_state = json.loads(game['game_state'])
                except:
                    game_state = None

            if game_state:
                logger.info(f"  Game in progress: Q{game_state.get('quarter', '?')} "
                          f"{game_state.get('current_score_home', 0)}-{game_state.get('current_score_away', 0)}")

        logger.info(f"Predicting: {away_team_name} @ {home_team_name}")

        try:
            # Get ensemble prediction with game_state if available
            ensemble_result, individual_results = simulator.predict_game(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                game_date=game_date_obj,
                use_ensemble=True,
                n_simulations=10000,
                game_state=game_state
            )

            # Extract individual model predictions
            panel_result = next((r for r in individual_results if r.model_type == 'panel_regression'), None)
            bayesian_result = next((r for r in individual_results if r.model_type == 'hierarchical_bayesian'), None)
            simultaneous_result = next((r for r in individual_results if r.model_type == 'simultaneous_equations'), None)

            # Calculate prediction strength based on enhanced confidence
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

            # Calculate model agreement score
            individual_probs = [r.home_win_prob for r in ensemble_result.individual_results]
            model_agreement = 1.0 - (np.std(individual_probs) if len(individual_probs) > 1 else 0.2)
            model_agreement = max(0.0, min(1.0, model_agreement))

            prediction = {
                'game_id': game_id,
                'game_date': game_date,
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'home_team': home_team_name,
                'away_team': away_team_name,

                # Ensemble predictions (main output)
                'predicted_winner': home_team_name if ensemble_result.home_win_prob > 0.5 else away_team_name,
                'home_win_probability': ensemble_result.home_win_prob,
                'away_win_probability': ensemble_result.away_win_prob,
                'predicted_home_score': ensemble_result.predicted_home_score,
                'predicted_away_score': ensemble_result.predicted_away_score,
                'confidence': ensemble_result.confidence,
                'prediction_strength': prediction_strength,
                'model_agreement': model_agreement,

                # Individual model predictions (for analysis)
                'panel_home_win_prob': panel_result.home_win_prob if panel_result else None,
                'panel_confidence': panel_result.confidence if panel_result else None,
                'bayesian_home_win_prob': bayesian_result.home_win_prob if bayesian_result else None,
                'bayesian_confidence': bayesian_result.confidence if bayesian_result else None,
                'simultaneous_home_win_prob': simultaneous_result.home_win_prob if simultaneous_result else None,
                'simultaneous_confidence': simultaneous_result.confidence if simultaneous_result else None,

                # Additional metrics
                'predicted_margin': abs(ensemble_result.predicted_home_score - ensemble_result.predicted_away_score),
                'num_models_agreement': len([r for r in ensemble_result.individual_results
                                            if (r.home_win_prob > 0.5) == (ensemble_result.home_win_prob > 0.5)]),
            }

            predictions.append(prediction)

            logger.info(f"  ✓ Ensemble: {home_team_name if ensemble_result.home_win_prob > 0.5 else away_team_name} "
                       f"{ensemble_result.home_win_prob:.1%} ({ensemble_result.confidence:.1%} confidence)")

        except Exception as e:
            logger.error(f"  ✗ Error predicting game {game_id}: {e}")
            continue

    # Convert to DataFrame
    df_predictions = pd.DataFrame(predictions)

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"advanced_predictions_{timestamp}.csv"
    df_predictions.to_csv(output_file, index=False)

    logger.info(f"\n✓ Saved predictions to: {output_file}")

    return df_predictions


def main():
    parser = argparse.ArgumentParser(
        description="Run advanced multi-simulators for NBA game predictions"
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Game date (YYYY-MM-DD). Default: today'
    )
    parser.add_argument(
        '--team-id',
        type=str,
        default=None,
        help='Specific team ID to predict'
    )
    parser.add_argument(
        '--opponent-id',
        type=str,
        default=None,
        help='Specific opponent ID to predict'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/tmp/nba_predictions',
        help='Output directory for predictions'
    )
    parser.add_argument(
        '--train-seasons',
        type=str,
        default='2020-2024',
        help='Training seasons (e.g., 2020-2024)'
    )
    parser.add_argument(
        '--n-simulations',
        type=int,
        default=10000,
        help='Number of Monte Carlo simulations'
    )

    args = parser.parse_args()

    # Parse date
    if args.date:
        game_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        game_date = date.today()

    # Parse training seasons
    if '-' in args.train_seasons:
        start_season, end_season = map(int, args.train_seasons.split('-'))
    else:
        start_season = end_season = int(args.train_seasons)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("="*80)
    logger.info("ADVANCED MULTI-SIMULATOR FRAMEWORK")
    logger.info("="*80)
    logger.info(f"Game Date: {game_date}")
    logger.info(f"Training Seasons: {start_season}-{end_season}")
    logger.info(f"Monte Carlo Simulations: {args.n_simulations:,}")
    logger.info("")

    # Initialize simulator
    logger.info("Initializing advanced multi-simulator framework...")
    simulator = AdvancedMultiSimulator()

    try:
        # Train all simulators
        logger.info("\n[1/3] Training all simulators...")
        simulator.train_all(start_season=start_season, end_season=end_season)

        # Fetch games
        if args.team_id and args.opponent_id:
            # Single game prediction
            logger.info("\n[2/3] Predicting single game...")
            result, individual = simulator.predict_game(
                home_team_id=args.team_id,
                away_team_id=args.opponent_id,
                game_date=game_date,
                use_ensemble=True,
                n_simulations=args.n_simulations
            )

            print("\n" + "="*80)
            print("PREDICTION RESULT")
            print("="*80)
            print(f"\nEnsemble Prediction:")
            print(f"  Home Win Probability: {result.home_win_prob:.1%}")
            print(f"  Away Win Probability: {result.away_win_prob:.1%}")
            print(f"  Predicted Score: {result.predicted_home_score:.1f} - {result.predicted_away_score:.1f}")
            print(f"  Confidence: {result.confidence:.1%}")

            print(f"\nIndividual Model Predictions:")
            for r in individual:
                print(f"  {r.model_type.replace('_', ' ').title()}:")
                print(f"    Home Win Prob: {r.home_win_prob:.1%}")
                print(f"    Predicted Score: {r.predicted_home_score:.1f} - {r.predicted_away_score:.1f}")
                print(f"    Confidence: {r.confidence:.1%}")

        else:
            # Predict all games for date
            logger.info("\n[2/3] Fetching upcoming games...")
            games_df = fetch_upcoming_games(game_date)

            if len(games_df) == 0:
                logger.warning(f"No games found for {game_date}")
                return

            logger.info(f"  Found {len(games_df)} games")

            # Generate predictions
            logger.info("\n[3/3] Generating predictions...")
            predictions_df = generate_comprehensive_predictions(
                simulator, games_df, output_dir
            )

            # Display summary
            print("\n" + "="*80)
            print("PREDICTION SUMMARY")
            print("="*80)
            print()

            for _, pred in predictions_df.iterrows():
                print(f"{pred['away_team_name']} @ {pred['home_team_name']}")
                print(f"  Predicted Winner: {pred['predicted_winner']} ({pred['ensemble_home_win_prob']:.1%})")
                print(f"  Predicted Score: {pred['ensemble_predicted_home_score']:.1f} - {pred['ensemble_predicted_away_score']:.1f}")
                print(f"  Confidence: {pred['ensemble_confidence']:.1%}")
                print(f"  Predicted Margin: {pred['predicted_margin']:.1f} points")
                print()

            # Create symlink to latest file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            latest_file = output_dir / "advanced_predictions_latest.csv"
            target_file = output_dir / f"advanced_predictions_{timestamp}.csv"
            if latest_file.exists() or latest_file.is_symlink():
                latest_file.unlink()
            latest_file.symlink_to(target_file.name)

            print(f"\n✓ Predictions saved to: {output_dir}")

    finally:
        simulator.close()
        logger.info("\n✓ Complete")


if __name__ == "__main__":
    main()


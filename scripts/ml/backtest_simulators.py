#!/usr/bin/env python3
"""
Backtest Advanced Multi-Simulators on Historical Games

Purpose: Evaluate simulator accuracy on historical games with known outcomes

Metrics:
- Win Probability Accuracy (% correct predictions)
- Score MAE (Mean Absolute Error)
- Score RMSE (Root Mean Squared Error)
- Brier Score (probability calibration)
- Calibration Plot (predicted vs actual win rates)
- Confusion Matrix (prediction vs actual outcomes)

Usage:
    python scripts/ml/backtest_simulators.py
    python scripts/ml/backtest_simulators.py --test-season 2024 --n-games 100

Created: November 2, 2025
Author: NBA Simulator AWS Project
"""

import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, mean_absolute_error, mean_squared_error,
    confusion_matrix, classification_report, brier_score_loss
)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from advanced_multi_simulator import AdvancedMultiSimulator, SimulationResult, EnsembleResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Results from backtesting a simulator"""
    model_type: str
    n_games: int
    win_prob_accuracy: float
    score_mae: float
    score_rmse: float
    brier_score: float
    calibration_slope: float
    predictions: List[Dict[str, Any]]
    actual_outcomes: List[Dict[str, Any]]
    # Enhancement verification and validation (added for comprehensive testing)
    enhancement_verification: Dict[str, Any] = None
    prediction_validation: Dict[str, Any] = None
    confidence_interval_coverage: Dict[str, Any] = None


class BacktestFramework:
    """
    Backtesting framework for advanced simulators

    Tests simulators on historical games and measures:
    - Win probability accuracy
    - Score prediction accuracy
    - Probability calibration
    - Overall performance metrics
    """

    def __init__(self, simulator: AdvancedMultiSimulator):
        self.simulator = simulator
        self.results = {}
        logger.info("BacktestFramework initialized")

    def verify_enhancements(self, result, individual_results: List[SimulationResult]) -> Dict[str, Any]:
        """
        Verify all 8 enhancements are working (Enhancement Verification)

        Returns:
            Dictionary with verification results for each enhancement
        """
        verification = {
            'rest_days': {'present': False, 'details': {}},
            'srs': {'present': False, 'details': {}},
            'home_away_splits': {'present': False, 'details': {}},
            'matchup_adjustments': {'present': False, 'details': {}},
            'star_player_impact': {'present': False, 'details': {}},
            'roster_stability': {'present': False, 'details': {}},
            'dynamic_weighting': {'present': False, 'details': {}},
            'confidence_intervals': {'present': False, 'details': {}}
        }

        # Get panel result for metadata (most enhancements are in panel result)
        panel_result = next((r for r in individual_results if r.model_type == 'panel_regression'), None)

        if panel_result and panel_result.metadata:
            metadata = panel_result.metadata

            # Enhancement 1: Rest Days
            if 'rest_days' in metadata:
                verification['rest_days']['present'] = True
                rest_days = metadata['rest_days']
                verification['rest_days']['details'] = {
                    'home_days_rest': rest_days.get('home', None),
                    'away_days_rest': rest_days.get('away', None),
                    'rest_disparity': rest_days.get('disparity', None)
                }

            # Enhancement 2: SRS (Strength of Schedule)
            if 'srs' in metadata:
                verification['srs']['present'] = True
                srs_data = metadata['srs']
                verification['srs']['details'] = {
                    'home_srs': srs_data.get('home', None),
                    'away_srs': srs_data.get('away', None),
                    'home_srs_reasonable': -15 <= srs_data.get('home', 0) <= 15 if srs_data.get('home') is not None else None,
                    'away_srs_reasonable': -15 <= srs_data.get('away', 0) <= 15 if srs_data.get('away') is not None else None
                }

            # Enhancement 3: Home/Away Splits
            if 'home_away_splits' in metadata:
                verification['home_away_splits']['present'] = True
                splits = metadata['home_away_splits']
                verification['home_away_splits']['details'] = {
                    'home_advantage': splits.get('home_advantage', None),
                    'home_advantage_reasonable': 0 <= splits.get('home_advantage', 0) <= 10 if splits.get('home_advantage') is not None else None
                }

            # Enhancement 4: Matchup Adjustments
            if 'matchup_adjustments' in metadata:
                verification['matchup_adjustments']['present'] = True
                matchup = metadata['matchup_adjustments']
                verification['matchup_adjustments']['details'] = {
                    'pace_diff': matchup.get('pace_diff', None),
                    'h2h_games': matchup.get('h2h_games', None),
                    'has_h2h_adjustment': matchup.get('h2h_games', 0) >= 3
                }

            # Enhancement 5: Star Player Impact
            if 'star_player_impact' in metadata:
                verification['star_player_impact']['present'] = True
                star_impact = metadata['star_player_impact']
                verification['star_player_impact']['details'] = {
                    'home_star_count': star_impact.get('home_star_count', None),
                    'away_star_count': star_impact.get('away_star_count', None),
                    'home_star_count_reasonable': 2 <= star_impact.get('home_star_count', 0) <= 3 if star_impact.get('home_star_count') is not None else None
                }

            # Enhancement 6: Roster Stability
            if 'roster_stability' in metadata:
                verification['roster_stability']['present'] = True
                roster_stability = metadata['roster_stability']
                verification['roster_stability']['details'] = {
                    'home_stability_factor': roster_stability.get('home_stability_factor', None),
                    'away_stability_factor': roster_stability.get('away_stability_factor', None),
                    'stability_reasonable': 0.5 <= roster_stability.get('home_stability_factor', 1.0) <= 1.0 if roster_stability.get('home_stability_factor') is not None else None
                }

        # Enhancement 7: Dynamic Weighting (check EnsembleResult)
        if hasattr(result, 'weights') and result.weights:
            verification['dynamic_weighting']['present'] = True
            weights = result.weights
            weight_sum = sum(weights.values())
            verification['dynamic_weighting']['details'] = {
                'weights': weights,
                'weights_sum_to_1': abs(weight_sum - 1.0) < 0.01,
                'has_dynamic_weights': weights != {'panel_regression': 0.40, 'hierarchical_bayesian': 0.30, 'simultaneous_equations': 0.30}
            }

        # Enhancement 8: Confidence Intervals
        if hasattr(result, 'predicted_home_score_lower_50') and result.predicted_home_score_lower_50 is not None:
            verification['confidence_intervals']['present'] = True
            verification['confidence_intervals']['details'] = {
                'has_50_interval': result.predicted_home_score_lower_50 is not None and result.predicted_home_score_upper_50 is not None,
                'has_80_interval': result.predicted_home_score_lower_80 is not None and result.predicted_home_score_upper_80 is not None,
                'has_95_interval': result.predicted_home_score_lower_95 is not None and result.predicted_home_score_upper_95 is not None,
                'intervals_ordered': (
                    result.predicted_home_score_lower_50 < result.predicted_home_score < result.predicted_home_score_upper_50
                    if result.predicted_home_score_lower_50 is not None else None
                )
            }

        return verification

    def validate_predictions(self, result, predicted_home_score: float, predicted_away_score: float) -> Dict[str, Any]:
        """
        Validate predictions are reasonable (Prediction Validation)

        Returns:
            Dictionary with validation results
        """
        validation = {
            'home_score_reasonable': 90 <= predicted_home_score <= 135,
            'away_score_reasonable': 90 <= predicted_away_score <= 135,
            'total_reasonable': 180 <= (predicted_home_score + predicted_away_score) <= 250,
            'win_prob_reasonable': 0.01 <= result.home_win_prob <= 0.99,
            'confidence_reasonable': 0.2 <= result.confidence <= 1.0,
            'intervals_ordered': True
        }

        # Check confidence intervals are ordered
        if hasattr(result, 'predicted_home_score_lower_50') and result.predicted_home_score_lower_50 is not None:
            validation['intervals_ordered'] = (
                result.predicted_home_score_lower_50 < predicted_home_score < result.predicted_home_score_upper_50 and
                result.predicted_home_score_lower_80 < predicted_home_score < result.predicted_home_score_upper_80 and
                result.predicted_home_score_lower_95 < predicted_home_score < result.predicted_home_score_upper_95
            )

        validation['all_valid'] = all([
            validation['home_score_reasonable'],
            validation['away_score_reasonable'],
            validation['total_reasonable'],
            validation['win_prob_reasonable'],
            validation['confidence_reasonable'],
            validation['intervals_ordered']
        ])

        return validation

    def calculate_confidence_interval_coverage(
        self,
        predictions: List[Dict[str, Any]],
        actual_outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate confidence interval coverage statistics

        Returns:
            Dictionary with coverage percentages for each confidence level
        """
        df_pred = pd.DataFrame(predictions)
        df_actual = pd.DataFrame(actual_outcomes)
        df_results = df_pred.merge(df_actual, on='game_id', how='inner')

        coverage = {
            'home_score_50': 0.0,
            'home_score_80': 0.0,
            'home_score_95': 0.0,
            'away_score_50': 0.0,
            'away_score_80': 0.0,
            'away_score_95': 0.0,
            'total_50': 0.0,
            'total_80': 0.0,
            'total_95': 0.0
        }

        total_games = len(df_results)
        if total_games == 0:
            return coverage

        # Check if confidence interval columns exist
        has_intervals = 'predicted_home_score_lower_50' in df_results.columns

        if has_intervals:
            # Home score coverage
            if 'predicted_home_score_lower_50' in df_results.columns:
                coverage['home_score_50'] = (
                    (df_results['predicted_home_score_lower_50'] <= df_results['actual_home_score']) &
                    (df_results['actual_home_score'] <= df_results['predicted_home_score_upper_50'])
                ).sum() / total_games

                coverage['home_score_80'] = (
                    (df_results['predicted_home_score_lower_80'] <= df_results['actual_home_score']) &
                    (df_results['actual_home_score'] <= df_results['predicted_home_score_upper_80'])
                ).sum() / total_games

                coverage['home_score_95'] = (
                    (df_results['predicted_home_score_lower_95'] <= df_results['actual_home_score']) &
                    (df_results['actual_home_score'] <= df_results['predicted_home_score_upper_95'])
                ).sum() / total_games

            # Away score coverage
            if 'predicted_away_score_lower_50' in df_results.columns:
                coverage['away_score_50'] = (
                    (df_results['predicted_away_score_lower_50'] <= df_results['actual_away_score']) &
                    (df_results['actual_away_score'] <= df_results['predicted_away_score_upper_50'])
                ).sum() / total_games

                coverage['away_score_80'] = (
                    (df_results['predicted_away_score_lower_80'] <= df_results['actual_away_score']) &
                    (df_results['actual_away_score'] <= df_results['predicted_away_score_upper_80'])
                ).sum() / total_games

                coverage['away_score_95'] = (
                    (df_results['predicted_away_score_lower_95'] <= df_results['actual_away_score']) &
                    (df_results['actual_away_score'] <= df_results['predicted_away_score_upper_95'])
                ).sum() / total_games

            # Total coverage
            if 'predicted_total_lower_50' in df_results.columns:
                actual_total = df_results['actual_home_score'] + df_results['actual_away_score']
                coverage['total_50'] = (
                    (df_results['predicted_total_lower_50'] <= actual_total) &
                    (actual_total <= df_results['predicted_total_upper_50'])
                ).sum() / total_games

                coverage['total_80'] = (
                    (df_results['predicted_total_lower_80'] <= actual_total) &
                    (actual_total <= df_results['predicted_total_upper_80'])
                ).sum() / total_games

                coverage['total_95'] = (
                    (df_results['predicted_total_lower_95'] <= actual_total) &
                    (actual_total <= df_results['predicted_total_upper_95'])
                ).sum() / total_games

        return coverage

    def load_test_games(
        self,
        test_season: int = 2024,
        n_games: int = 100,
        min_games_played: int = 20
    ) -> pd.DataFrame:
        """Load historical games for backtesting"""
        logger.info(f"Loading test games from season {test_season}...")

        # Simplified query
        query = """
        SELECT DISTINCT
            g.game_id,
            g.game_date,
            g.home_team_id,
            g.away_team_id,
            ht.team_name as home_team_name,
            at.team_name as away_team_name,
            g.home_score,
            g.away_score,
            CASE WHEN g.home_score > g.away_score THEN 1 ELSE 0 END as home_won,
            CASE WHEN g.away_score > g.home_score THEN 1 ELSE 0 END as away_won
        FROM games g
        LEFT JOIN teams ht ON g.home_team_id = ht.team_id
        LEFT JOIN teams at ON g.away_team_id = at.team_id
        WHERE CAST(SUBSTRING(g.season FROM 1 FOR 4) AS INTEGER) = %s
            AND g.home_score IS NOT NULL
            AND g.away_score IS NOT NULL
        ORDER BY g.game_date
        LIMIT %s
        """

        df = self.simulator.db.query(query, params=(test_season, n_games))

        if len(df) == 0:
            raise ValueError(f"No test games found for season {test_season}")

        logger.info(f"  ✓ Loaded {len(df)} test games")
        logger.info(f"  Date range: {df['game_date'].min()} to {df['game_date'].max()}")

        return df

    def backtest_simulator(
        self,
        test_games: pd.DataFrame,
        use_ensemble: bool = True,
        n_simulations: int = 1000
    ) -> BacktestResult:
        """Backtest simulator on test games"""

        logger.info(f"Backtesting {'ensemble' if use_ensemble else 'individual'} simulator on {len(test_games)} games...")

        predictions = []
        actual_outcomes = []

        for idx, game in test_games.iterrows():
            game_id = game['game_id']
            home_team_id = str(game['home_team_id'])
            away_team_id = str(game['away_team_id'])
            home_team = game['home_team_name']
            away_team = game['away_team_name']
            game_date = pd.to_datetime(game['game_date']).date()

            actual_home_score = int(game['home_score'])
            actual_away_score = int(game['away_score'])
            actual_home_won = int(game['home_won'])

            try:
                if use_ensemble:
                    result, individual = self.simulator.predict_game(
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        game_date=game_date,
                        use_ensemble=True,
                        n_simulations=n_simulations
                    )

                    predicted_winner = home_team if result.home_win_prob > 0.5 else away_team
                    predicted_home_won = 1 if result.home_win_prob > 0.5 else 0

                    # Include confidence intervals in predictions for coverage calculation
                    pred_dict = {
                        'game_id': game_id,
                        'game_date': game_date,
                        'home_team': home_team,
                        'away_team': away_team,
                        'predicted_winner': predicted_winner,
                        'predicted_home_won': predicted_home_won,
                        'predicted_home_win_prob': result.home_win_prob,
                        'predicted_home_score': result.predicted_home_score,
                        'predicted_away_score': result.predicted_away_score,
                        'predicted_total': result.predicted_home_score + result.predicted_away_score,
                        'predicted_margin': result.predicted_home_score - result.predicted_away_score,
                        'confidence': result.confidence,
                    }

                    # Add confidence intervals if available
                    if hasattr(result, 'predicted_home_score_lower_50') and result.predicted_home_score_lower_50 is not None:
                        pred_dict['predicted_home_score_lower_50'] = result.predicted_home_score_lower_50
                        pred_dict['predicted_home_score_upper_50'] = result.predicted_home_score_upper_50
                        pred_dict['predicted_home_score_lower_80'] = result.predicted_home_score_lower_80
                        pred_dict['predicted_home_score_upper_80'] = result.predicted_home_score_upper_80
                        pred_dict['predicted_home_score_lower_95'] = result.predicted_home_score_lower_95
                        pred_dict['predicted_home_score_upper_95'] = result.predicted_home_score_upper_95
                        pred_dict['predicted_away_score_lower_50'] = result.predicted_away_score_lower_50
                        pred_dict['predicted_away_score_upper_50'] = result.predicted_away_score_upper_50
                        pred_dict['predicted_away_score_lower_80'] = result.predicted_away_score_lower_80
                        pred_dict['predicted_away_score_upper_80'] = result.predicted_away_score_upper_80
                        pred_dict['predicted_away_score_lower_95'] = result.predicted_away_score_lower_95
                        pred_dict['predicted_away_score_upper_95'] = result.predicted_away_score_upper_95
                        pred_dict['predicted_total_lower_50'] = result.predicted_total_lower_50
                        pred_dict['predicted_total_upper_50'] = result.predicted_total_upper_50
                        pred_dict['predicted_total_lower_80'] = result.predicted_total_lower_80
                        pred_dict['predicted_total_upper_80'] = result.predicted_total_upper_80
                        pred_dict['predicted_total_lower_95'] = result.predicted_total_lower_95
                        pred_dict['predicted_total_upper_95'] = result.predicted_total_upper_95

                    predictions.append(pred_dict)

                    # Verify enhancements and validate predictions (only for first game to avoid spam)
                    if idx == 0:
                        enhancement_verification = self.verify_enhancements(result, individual)
                        prediction_validation = self.validate_predictions(result, result.predicted_home_score, result.predicted_away_score)
                        if not prediction_validation['all_valid']:
                            logger.warning(f"  ⚠ Prediction validation failed for game {game_id}: {prediction_validation}")
                else:
                    # Use panel simulator only
                    result = self.simulator.panel_sim.simulate_game(
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        game_date=game_date,
                        n_simulations=n_simulations
                    )

                    predicted_winner = home_team if result.home_win_prob > 0.5 else away_team
                    predicted_home_won = 1 if result.home_win_prob > 0.5 else 0

                    predictions.append({
                        'game_id': game_id,
                        'game_date': game_date,
                        'home_team': home_team,
                        'away_team': away_team,
                        'predicted_winner': predicted_winner,
                        'predicted_home_won': predicted_home_won,
                        'predicted_home_win_prob': result.home_win_prob,
                        'predicted_home_score': result.predicted_home_score,
                        'predicted_away_score': result.predicted_away_score,
                        'confidence': result.confidence,
                    })

                actual_outcomes.append({
                    'game_id': game_id,
                    'actual_home_score': actual_home_score,
                    'actual_away_score': actual_away_score,
                    'actual_home_won': actual_home_won,
                    'actual_margin': actual_home_score - actual_away_score,
                    'actual_total': actual_home_score + actual_away_score,
                })

            except Exception as e:
                logger.warning(f"  ✗ Error predicting game {game_id}: {e}")
                continue

            if (idx + 1) % 10 == 0:
                logger.info(f"  Progress: {idx + 1}/{len(test_games)} games predicted")

        if len(predictions) == 0:
            raise ValueError("No successful predictions generated")

        logger.info(f"  ✓ Generated {len(predictions)} predictions")

        # Calculate metrics
        df_pred = pd.DataFrame(predictions)
        df_actual = pd.DataFrame(actual_outcomes)

        # Merge predictions and actual outcomes
        df_results = df_pred.merge(
            df_actual,
            on='game_id',
            how='inner'
        )

        # Win probability accuracy
        predicted_home_won = df_results['predicted_home_won'].values
        actual_home_won = df_results['actual_home_won'].values
        win_prob_accuracy = accuracy_score(actual_home_won, predicted_home_won)

        # Score MAE (separate for home and away)
        home_score_mae = mean_absolute_error(
            df_results['actual_home_score'],
            df_results['predicted_home_score']
        )
        away_score_mae = mean_absolute_error(
            df_results['actual_away_score'],
            df_results['predicted_away_score']
        )
        score_mae = (home_score_mae + away_score_mae) / 2

        # Score RMSE
        home_score_rmse = np.sqrt(mean_squared_error(
            df_results['actual_home_score'],
            df_results['predicted_home_score']
        ))
        away_score_rmse = np.sqrt(mean_squared_error(
            df_results['actual_away_score'],
            df_results['predicted_away_score']
        ))
        score_rmse = (home_score_rmse + away_score_rmse) / 2

        # Brier Score (probability calibration)
        brier_score = brier_score_loss(actual_home_won, df_results['predicted_home_win_prob'])

        # Calibration slope (how well probabilities match actual rates)
        # Group predictions into bins and calculate actual win rate in each bin
        prob_bins = np.linspace(0, 1, 11)
        calibration_data = []
        for i in range(len(prob_bins) - 1):
            bin_mask = (df_results['predicted_home_win_prob'] >= prob_bins[i]) & \
                      (df_results['predicted_home_win_prob'] < prob_bins[i + 1])
            if bin_mask.sum() > 0:
                predicted_rate = df_results[bin_mask]['predicted_home_win_prob'].mean()
                actual_rate = df_results[bin_mask]['actual_home_won'].mean()
                calibration_data.append({
                    'predicted_prob': predicted_rate,
                    'actual_rate': actual_rate,
                    'n_games': bin_mask.sum()
                })

        if len(calibration_data) > 1:
            cal_df = pd.DataFrame(calibration_data)
            calibration_slope = np.polyfit(cal_df['predicted_prob'], cal_df['actual_rate'], 1)[0]
        else:
            calibration_slope = 1.0

        # Additional metrics: Total Points MAE/RMSE, Margin MAE/RMSE
        total_points_mae = mean_absolute_error(
            df_results['actual_total'],
            df_results['predicted_total']
        )
        total_points_rmse = np.sqrt(mean_squared_error(
            df_results['actual_total'],
            df_results['predicted_total']
        ))

        margin_mae = mean_absolute_error(
            df_results['actual_margin'],
            df_results['predicted_margin']
        )
        margin_rmse = np.sqrt(mean_squared_error(
            df_results['actual_margin'],
            df_results['predicted_margin']
        ))

        # Verify enhancements (use first result if available)
        enhancement_verification = None
        prediction_validation_summary = None
        confidence_interval_coverage = None

        if use_ensemble and len(predictions) > 0:
            # Get a sample result for verification (use first prediction)
            try:
                sample_game = test_games.iloc[0]
                sample_result, sample_individual = self.simulator.predict_game(
                    home_team_id=str(sample_game['home_team_id']),
                    away_team_id=str(sample_game['away_team_id']),
                    game_date=pd.to_datetime(sample_game['game_date']).date(),
                    use_ensemble=True,
                    n_simulations=n_simulations
                )
                enhancement_verification = self.verify_enhancements(sample_result, sample_individual)
            except Exception as e:
                logger.warning(f"  Could not verify enhancements: {e}")

        # Calculate prediction validation summary
        validation_results = []
        for pred in predictions:
            if 'predicted_home_score' in pred:
                # Simple validation check
                home_valid = 90 <= pred['predicted_home_score'] <= 135
                away_valid = 90 <= pred['predicted_away_score'] <= 135
                total_valid = 180 <= pred.get('predicted_total', 0) <= 250
                validation_results.append({
                    'home_score_reasonable': home_valid,
                    'away_score_reasonable': away_valid,
                    'total_reasonable': total_valid,
                    'all_valid': home_valid and away_valid and total_valid
                })

        if validation_results:
            prediction_validation_summary = {
                'total_predictions': len(validation_results),
                'home_score_valid': sum(v['home_score_reasonable'] for v in validation_results),
                'away_score_valid': sum(v['away_score_reasonable'] for v in validation_results),
                'total_valid': sum(v['total_reasonable'] for v in validation_results),
                'all_valid': sum(v['all_valid'] for v in validation_results),
                'validation_rate': sum(v['all_valid'] for v in validation_results) / len(validation_results)
            }

        # Calculate confidence interval coverage
        confidence_interval_coverage = self.calculate_confidence_interval_coverage(predictions, actual_outcomes)

        return BacktestResult(
            model_type='ensemble' if use_ensemble else 'panel_regression',
            n_games=len(df_results),
            win_prob_accuracy=win_prob_accuracy,
            score_mae=score_mae,
            score_rmse=score_rmse,
            brier_score=brier_score,
            calibration_slope=calibration_slope,
            predictions=predictions,
            actual_outcomes=actual_outcomes,
            enhancement_verification=enhancement_verification,
            prediction_validation=prediction_validation_summary,
            confidence_interval_coverage=confidence_interval_coverage
        )

    def compare_simulators(
        self,
        test_games: pd.DataFrame,
        n_simulations: int = 1000
    ) -> Dict[str, BacktestResult]:
        """Compare all simulators on same test games"""

        logger.info("="*80)
        logger.info("BACKTESTING ALL SIMULATORS")
        logger.info("="*80)
        print()

        results = {}

        # Test ensemble
        logger.info("Testing Ensemble Simulator...")
        try:
            ensemble_result = self.backtest_simulator(
                test_games, use_ensemble=True, n_simulations=n_simulations
            )
            results['ensemble'] = ensemble_result
            logger.info(f"  ✓ Ensemble: {ensemble_result.win_prob_accuracy:.1%} accuracy")
        except Exception as e:
            logger.error(f"  ✗ Ensemble failed: {e}")

        # Test individual simulators
        print()
        logger.info("Testing Individual Simulators...")

        # Panel Data Regression
        logger.info("Testing Panel Data Regression...")
        try:
            panel_result = self.backtest_simulator(
                test_games, use_ensemble=False, n_simulations=n_simulations
            )
            results['panel_regression'] = panel_result
            logger.info(f"  ✓ Panel Regression: {panel_result.win_prob_accuracy:.1%} accuracy")
        except Exception as e:
            logger.error(f"  ✗ Panel Regression failed: {e}")

        return results

    def generate_report(
        self,
        results: Dict[str, BacktestResult],
        output_dir: Path
    ):
        """Generate comprehensive backtest report"""

        print()
        logger.info("="*80)
        logger.info("GENERATING BACKTEST REPORT")
        logger.info("="*80)

        # Create report
        report_lines = []
        report_lines.append("="*100)
        report_lines.append("BACKTEST RESULTS - ADVANCED MULTI-SIMULATOR FRAMEWORK")
        report_lines.append("="*100)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Summary table
        report_lines.append("SUMMARY METRICS")
        report_lines.append("-"*100)
        report_lines.append(f"{'Model':<25} {'Games':<8} {'Win Acc':<10} {'Score MAE':<12} {'Score RMSE':<12} {'Brier':<10} {'Calibration':<12}")
        report_lines.append("-"*100)

        for model_name, result in results.items():
            report_lines.append(
                f"{result.model_type:<25} "
                f"{result.n_games:<8} "
                f"{result.win_prob_accuracy:>9.1%} "
                f"{result.score_mae:>11.2f} "
                f"{result.score_rmse:>11.2f} "
                f"{result.brier_score:>9.4f} "
                f"{result.calibration_slope:>11.2f}"
            )

        report_lines.append("-"*100)
        report_lines.append("")

        # Detailed results for each model
        for model_name, result in results.items():
            report_lines.append("="*100)
            report_lines.append(f"DETAILED RESULTS: {result.model_type.upper()}")
            report_lines.append("="*100)
            report_lines.append("")

            report_lines.append(f"Games Tested: {result.n_games}")
            report_lines.append(f"Win Probability Accuracy: {result.win_prob_accuracy:.1%}")
            report_lines.append(f"Score MAE (Mean Absolute Error): {result.score_mae:.2f} points")
            report_lines.append(f"Score RMSE (Root Mean Squared Error): {result.score_rmse:.2f} points")
            report_lines.append(f"Brier Score (lower is better): {result.brier_score:.4f}")
            report_lines.append(f"Calibration Slope (1.0 = perfect): {result.calibration_slope:.2f}")
            report_lines.append("")

            # Prepare data for additional metrics and analysis
            df_pred = pd.DataFrame(result.predictions)
            df_actual = pd.DataFrame(result.actual_outcomes)
            df_results = df_pred.merge(df_actual, on='game_id', how='inner')

            # Additional metrics: Total Points and Margin
            if 'predicted_total' in df_results.columns:
                total_points_mae = mean_absolute_error(df_results['actual_total'], df_results['predicted_total'])
                total_points_rmse = np.sqrt(mean_squared_error(df_results['actual_total'], df_results['predicted_total']))
                report_lines.append(f"Total Points MAE: {total_points_mae:.2f} points")
                report_lines.append(f"Total Points RMSE: {total_points_rmse:.2f} points")
            if 'predicted_margin' in df_results.columns:
                margin_mae = mean_absolute_error(df_results['actual_margin'], df_results['predicted_margin'])
                margin_rmse = np.sqrt(mean_squared_error(df_results['actual_margin'], df_results['predicted_margin']))
                report_lines.append(f"Margin MAE: {margin_mae:.2f} points")
                report_lines.append(f"Margin RMSE: {margin_rmse:.2f} points")
            report_lines.append("")

            # Enhancement Verification
            if result.enhancement_verification:
                report_lines.append("ENHANCEMENT VERIFICATION")
                report_lines.append("-"*100)
                enhancement_names = {
                    'rest_days': '1. Rest Days Calculation',
                    'srs': '2. Strength of Schedule (SRS)',
                    'home_away_splits': '3. Home/Away Splits',
                    'matchup_adjustments': '4. Matchup-Specific Adjustments',
                    'star_player_impact': '5. Star Player Impact',
                    'roster_stability': '6. Roster Changes Detection',
                    'dynamic_weighting': '7. Dynamic Model Weighting',
                    'confidence_intervals': '8. Better Confidence Intervals'
                }
                for enh_key, enh_name in enhancement_names.items():
                    verif = result.enhancement_verification.get(enh_key, {})
                    status = "✓" if verif.get('present', False) else "✗"
                    report_lines.append(f"{status} {enh_name}: {'Present' if verif.get('present', False) else 'Missing'}")
                    if verif.get('details'):
                        details = verif['details']
                        if enh_key == 'srs' and 'home_srs' in details:
                            report_lines.append(f"    Home SRS: {details.get('home_srs', 'N/A'):.2f}, Away SRS: {details.get('away_srs', 'N/A'):.2f}")
                        elif enh_key == 'dynamic_weighting' and 'weights' in details:
                            weights = details['weights']
                            report_lines.append(f"    Weights: Panel={weights.get('panel_regression', 0):.2f}, Bayesian={weights.get('hierarchical_bayesian', 0):.2f}, Simultaneous={weights.get('simultaneous_equations', 0):.2f}")
                report_lines.append("")

            # Prediction Validation
            if result.prediction_validation:
                report_lines.append("PREDICTION VALIDATION")
                report_lines.append("-"*100)
                val = result.prediction_validation
                report_lines.append(f"Total Predictions: {val.get('total_predictions', 0)}")
                report_lines.append(f"Home Score Valid (90-135): {val.get('home_score_valid', 0)}/{val.get('total_predictions', 0)} ({val.get('home_score_valid', 0)/max(val.get('total_predictions', 1), 1):.1%})")
                report_lines.append(f"Away Score Valid (90-135): {val.get('away_score_valid', 0)}/{val.get('total_predictions', 0)} ({val.get('away_score_valid', 0)/max(val.get('total_predictions', 1), 1):.1%})")
                report_lines.append(f"Total Valid (180-250): {val.get('total_valid', 0)}/{val.get('total_predictions', 0)} ({val.get('total_valid', 0)/max(val.get('total_predictions', 1), 1):.1%})")
                report_lines.append(f"All Validations Passed: {val.get('all_valid', 0)}/{val.get('total_predictions', 0)} ({val.get('validation_rate', 0):.1%})")
                report_lines.append("")

            # Confidence Interval Coverage
            if result.confidence_interval_coverage:
                report_lines.append("CONFIDENCE INTERVAL COVERAGE")
                report_lines.append("-"*100)
                coverage = result.confidence_interval_coverage
                report_lines.append("Home Score Coverage:")
                report_lines.append(f"  50% Interval: {coverage.get('home_score_50', 0):.1%} (target: ~50%)")
                report_lines.append(f"  80% Interval: {coverage.get('home_score_80', 0):.1%} (target: ~80%)")
                report_lines.append(f"  95% Interval: {coverage.get('home_score_95', 0):.1%} (target: ~95%)")
                report_lines.append("Away Score Coverage:")
                report_lines.append(f"  50% Interval: {coverage.get('away_score_50', 0):.1%} (target: ~50%)")
                report_lines.append(f"  80% Interval: {coverage.get('away_score_80', 0):.1%} (target: ~80%)")
                report_lines.append(f"  95% Interval: {coverage.get('away_score_95', 0):.1%} (target: ~95%)")
                report_lines.append("Total Points Coverage:")
                report_lines.append(f"  50% Interval: {coverage.get('total_50', 0):.1%} (target: ~50%)")
                report_lines.append(f"  80% Interval: {coverage.get('total_80', 0):.1%} (target: ~80%)")
                report_lines.append(f"  95% Interval: {coverage.get('total_95', 0):.1%} (target: ~95%)")
                report_lines.append("")

            # Calculate margin error for best/worst predictions
            if 'predicted_margin' not in df_results.columns:
                df_results['predicted_margin'] = df_results['predicted_home_score'] - df_results['predicted_away_score']
            if 'margin_error' not in df_results.columns:
                df_results['margin_error'] = abs(df_results['predicted_margin'] - df_results['actual_margin'])

            # Top 10 best predictions

            report_lines.append("Top 10 Best Predictions (by margin error):")
            top_predictions = df_results.nsmallest(10, 'margin_error')
            for _, row in top_predictions.iterrows():
                report_lines.append(
                    f"  {row['away_team']} @ {row['home_team']}: "
                    f"Predicted {row['predicted_home_score']:.0f}-{row['predicted_away_score']:.0f}, "
                    f"Actual {row['actual_home_score']:.0f}-{row['actual_away_score']:.0f} "
                    f"(Error: {row['margin_error']:.1f} pts)"
                )
            report_lines.append("")

            # Bottom 10 worst predictions
            report_lines.append("Top 10 Worst Predictions (by margin error):")
            worst_predictions = df_results.nlargest(10, 'margin_error')
            for _, row in worst_predictions.iterrows():
                report_lines.append(
                    f"  {row['away_team']} @ {row['home_team']}: "
                    f"Predicted {row['predicted_home_score']:.0f}-{row['predicted_away_score']:.0f}, "
                    f"Actual {row['actual_home_score']:.0f}-{row['actual_away_score']:.0f} "
                    f"(Error: {row['margin_error']:.1f} pts)"
                )
            report_lines.append("")

        report_lines.append("="*100)
        report_lines.append("INTERPRETATION")
        report_lines.append("="*100)
        report_lines.append("")
        report_lines.append("Win Probability Accuracy:")
        report_lines.append("  - Percentage of games where predicted winner matches actual winner")
        report_lines.append("  - Baseline (random): 50%")
        report_lines.append("  - Target: >70%")
        report_lines.append("")
        report_lines.append("Score MAE (Mean Absolute Error):")
        report_lines.append("  - Average absolute difference between predicted and actual scores")
        report_lines.append("  - Lower is better")
        report_lines.append("  - Target: <5 points")
        report_lines.append("")
        report_lines.append("Brier Score:")
        report_lines.append("  - Measures probability calibration (lower is better)")
        report_lines.append("  - Perfect calibration: 0.00")
        report_lines.append("  - Range: 0.00 - 1.00")
        report_lines.append("")
        report_lines.append("Calibration Slope:")
        report_lines.append("  - Measures how well predicted probabilities match actual rates")
        report_lines.append("  - Perfect calibration: 1.0")
        report_lines.append("  - <1.0: Overconfident predictions")
        report_lines.append("  - >1.0: Underconfident predictions")
        report_lines.append("="*100)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"backtest_report_{timestamp}.txt"

        with open(report_file, 'w') as f:
            f.write('\n'.join(report_lines))

        logger.info(f"  ✓ Report saved to: {report_file}")

        # Save detailed CSV
        csv_file = output_dir / f"backtest_results_{timestamp}.csv"

        all_predictions = []
        for model_name, result in results.items():
            df_pred = pd.DataFrame(result.predictions)
            df_actual = pd.DataFrame(result.actual_outcomes)
            df_results = df_pred.merge(df_actual, on='game_id', how='inner')
            df_results['model_type'] = result.model_type
            df_results['margin_error'] = abs(
                (df_results['predicted_home_score'] - df_results['predicted_away_score']) -
                (df_results['actual_home_score'] - df_results['actual_away_score'])
            )
            df_results['score_error'] = (
                abs(df_results['predicted_home_score'] - df_results['actual_home_score']) +
                abs(df_results['predicted_away_score'] - df_results['actual_away_score'])
            ) / 2
            df_results['correct_prediction'] = (
                df_results['predicted_home_won'] == df_results['actual_home_won']
            )
            all_predictions.append(df_results)

        if all_predictions:
            df_all = pd.concat(all_predictions, ignore_index=True)
            df_all.to_csv(csv_file, index=False)
            logger.info(f"  ✓ Detailed results saved to: {csv_file}")

        # Print summary
        print()
        print('\n'.join(report_lines))

        return report_file, csv_file


def main():
    parser = argparse.ArgumentParser(
        description="Backtest advanced multi-simulators on historical games"
    )
    parser.add_argument(
        '--test-season',
        type=int,
        default=2024,
        help='Season to test on (default: 2024)'
    )
    parser.add_argument(
        '--n-games',
        type=int,
        default=100,
        help='Number of games to test (default: 100)'
    )
    parser.add_argument(
        '--n-simulations',
        type=int,
        default=1000,
        help='Number of Monte Carlo simulations per game (default: 1000)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/tmp/nba_predictions',
        help='Output directory for reports'
    )
    parser.add_argument(
        '--train-seasons',
        type=str,
        default='2020-2024',
        help='Training seasons (e.g., 2020-2024)'
    )

    args = parser.parse_args()

    # Parse training seasons
    if '-' in args.train_seasons:
        start_season, end_season = map(int, args.train_seasons.split('-'))
    else:
        start_season = end_season = int(args.train_seasons)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("="*80)
    logger.info("BACKTESTING ADVANCED MULTI-SIMULATORS")
    logger.info("="*80)
    logger.info(f"Test Season: {args.test_season}")
    logger.info(f"Number of Games: {args.n_games}")
    logger.info(f"Training Seasons: {start_season}-{end_season}")
    logger.info(f"Monte Carlo Simulations: {args.n_simulations:,}")
    print()

    # Initialize simulator
    logger.info("Initializing advanced multi-simulator framework...")
    simulator = AdvancedMultiSimulator()

    try:
        # Train simulators
        logger.info("Training simulators...")
        simulator.train_all(start_season=start_season, end_season=end_season)

        # Initialize backtest framework
        backtester = BacktestFramework(simulator)

        # Load test games
        print()
        logger.info("Loading test games...")
        test_games = backtester.load_test_games(
            test_season=args.test_season,
            n_games=args.n_games
        )

        # Run backtests
        print()
        logger.info("Running backtests...")
        results = backtester.compare_simulators(
            test_games,
            n_simulations=args.n_simulations
        )

        # Generate report
        print()
        report_file, csv_file = backtester.generate_report(results, output_dir)

        print()
        logger.info("="*80)
        logger.info("✓ BACKTEST COMPLETE")
        logger.info("="*80)
        logger.info(f"Report: {report_file}")
        logger.info(f"Detailed Results: {csv_file}")

    finally:
        simulator.close()


if __name__ == "__main__":
    main()


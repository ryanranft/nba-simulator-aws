#!/usr/bin/env python3
"""
Player Impact Prediction Model - Predicts On/Off Differential and Replacement Value

Purpose: Use plus/minus player features to predict individual player impact
Database: RDS PostgreSQL (nba_simulator)
Created: October 19, 2025

=== MODEL OVERVIEW ===

This model uses the 7 player impact features from the Plus/Minus system to:
1. Predict player on/off differential (team performance with vs without player)
2. Estimate replacement value (impact per 48 minutes)
3. Identify high-impact vs low-impact players
4. Recommend contract values based on impact

=== FEATURES USED (7 player features) ===

Input Features (from rec_11 + Plus/Minus):
- pm_player_best_player_on_off_diff (best player impact in game)
- pm_player_worst_player_on_off_diff (worst player impact)
- pm_player_avg_player_on_off_diff (average on/off differential)
- pm_player_on_off_consistency (std dev of impacts)
- pm_player_avg_replacement_value (average value per 48 min)
- pm_player_high_confidence_count (number of reliable measurements)
- pm_player_impact_distribution (range of impact scores)

Target Variables:
- player_on_off_diff (primary: team net rating with player - without player)
- replacement_value_48min (secondary: impact standardized per 48 minutes)

=== MODEL ARCHITECTURE ===

Algorithm: XGBoost Regressor (multi-output)
Validation: 5-Fold Time Series Cross-Validation
Metrics: MAE, RMSE, R², Feature Importance

=== USE CASES ===

1. Player Valuation - Estimate contract worth based on impact
2. Trade Analysis - Compare replacement values
3. Draft Evaluation - Project rookie impact
4. Rotation Optimization - Identify bench players with positive impact
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from pathlib import Path
import joblib

# ML libraries
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.multioutput import MultiOutputRegressor
import xgboost as xgb

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import enhanced rec_11
from scripts.ml.rec_11_with_plus_minus import EnhancedFeatureEngineeringPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlayerImpactPredictionModel:
    """
    Predicts player on/off differential and replacement value using plus/minus features.

    Uses XGBoost to model player impact based on:
    - Historical on/off differentials
    - Replacement value metrics
    - Impact consistency and distribution
    """

    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """
        Initialize PlayerImpactPredictionModel.

        Args:
            model_config: Configuration for model hyperparameters
        """
        self.config = model_config or self._default_config()
        self.model = None
        self.feature_names = []
        self.feature_importance = None
        self.training_history = {}

        logger.info("PlayerImpactPredictionModel initialized")

    def _default_config(self) -> Dict[str, Any]:
        """Default model configuration."""
        return {
            # XGBoost hyperparameters
            "max_depth": 5,
            "learning_rate": 0.1,
            "n_estimators": 100,
            "min_child_weight": 1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "gamma": 0,
            "reg_alpha": 0,
            "reg_lambda": 1,
            "random_state": 42,

            # Training settings
            "cv_folds": 5,
            "test_size": 0.2,

            # Feature engineering
            "include_plus_minus": True,
            "player_feature_prefix": "pm_player_",
        }

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str = "player_on_off_diff"
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for training by extracting player impact features.

        Args:
            df: DataFrame with enhanced features (from rec_11 + plus/minus)
            target_col: Target variable column name

        Returns:
            Tuple of (X_features, y_target)
        """
        logger.info("Preparing data for player impact prediction model...")

        # Extract player features (pm_player_*)
        player_features = [col for col in df.columns if col.startswith(self.config["player_feature_prefix"])]

        if not player_features:
            raise ValueError("No player features found in DataFrame. Ensure plus/minus features are included.")

        logger.info(f"Found {len(player_features)} player features")

        # Prepare feature matrix
        X = df[player_features].copy()

        # Handle missing values (fill with median)
        X = X.fillna(X.median())

        # Prepare target variable
        if target_col in df.columns:
            y = df[target_col].copy()
        else:
            # If target not provided, use avg_player_on_off_diff as proxy
            logger.warning(f"Target '{target_col}' not found. Using pm_player_avg_player_on_off_diff as proxy.")
            y = df["pm_player_avg_player_on_off_diff"].copy()

        # Remove rows with missing target
        valid_idx = ~y.isna()
        X = X[valid_idx]
        y = y[valid_idx]

        logger.info(f"✓ Prepared {len(X)} samples with {len(X.columns)} features")

        self.feature_names = list(X.columns)

        return X, y

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        validation_split: bool = True
    ) -> Dict[str, Any]:
        """
        Train the player impact prediction model.

        Args:
            X: Feature matrix (player features)
            y: Target variable (player on/off differential)
            validation_split: Whether to use cross-validation

        Returns:
            Training metrics and results
        """
        logger.info("=" * 70)
        logger.info("Training Player Impact Prediction Model")
        logger.info("=" * 70)
        start_time = datetime.now()

        # Initialize XGBoost model
        self.model = xgb.XGBRegressor(
            max_depth=self.config["max_depth"],
            learning_rate=self.config["learning_rate"],
            n_estimators=self.config["n_estimators"],
            min_child_weight=self.config["min_child_weight"],
            subsample=self.config["subsample"],
            colsample_bytree=self.config["colsample_bytree"],
            gamma=self.config["gamma"],
            reg_alpha=self.config["reg_alpha"],
            reg_lambda=self.config["reg_lambda"],
            random_state=self.config["random_state"],
            n_jobs=-1,
            verbosity=0
        )

        # Cross-validation (Time Series CV to respect temporal ordering)
        if validation_split and len(X) >= self.config["cv_folds"] * 2:
            logger.info(f"\nPerforming {self.config['cv_folds']}-fold Time Series Cross-Validation...")

            tscv = TimeSeriesSplit(n_splits=self.config["cv_folds"])

            cv_scores = cross_val_score(
                self.model, X, y,
                cv=tscv,
                scoring='neg_mean_absolute_error',
                n_jobs=-1
            )

            cv_mae = -cv_scores.mean()
            cv_std = cv_scores.std()

            logger.info(f"✓ Cross-Validation MAE: {cv_mae:.2f} ± {cv_std:.2f}")

            self.training_history["cv_mae"] = cv_mae
            self.training_history["cv_std"] = cv_std
        else:
            logger.info("Skipping cross-validation (insufficient data)")
            self.training_history["cv_mae"] = None
            self.training_history["cv_std"] = None

        # Train on full dataset
        logger.info("\nTraining on full dataset...")
        self.model.fit(X, y)

        # Calculate training metrics
        y_pred = self.model.predict(X)

        train_mae = mean_absolute_error(y, y_pred)
        train_rmse = np.sqrt(mean_squared_error(y, y_pred))
        train_r2 = r2_score(y, y_pred)

        logger.info(f"✓ Training MAE: {train_mae:.2f}")
        logger.info(f"✓ Training RMSE: {train_rmse:.2f}")
        logger.info(f"✓ Training R²: {train_r2:.4f}")

        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        logger.info("\nTop 5 Most Important Features:")
        for idx, row in self.feature_importance.head(5).iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")

        # Training summary
        training_time = (datetime.now() - start_time).total_seconds()

        results = {
            "success": True,
            "training_time": training_time,
            "samples_trained": len(X),
            "features_used": len(self.feature_names),
            "train_mae": train_mae,
            "train_rmse": train_rmse,
            "train_r2": train_r2,
            "cv_mae": self.training_history.get("cv_mae"),
            "cv_std": self.training_history.get("cv_std"),
            "feature_importance": self.feature_importance.to_dict('records')
        }

        logger.info("=" * 70)
        logger.info("✅ Training Complete")
        logger.info("=" * 70)

        return results

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict player on/off differential for given features.

        Args:
            X: Feature matrix

        Returns:
            Predicted on/off differentials
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X)

    def rank_players(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        min_confidence: str = "MEDIUM"
    ) -> pd.DataFrame:
        """
        Rank players by predicted impact.

        Args:
            df: DataFrame with player features
            top_n: Number of top players to return
            min_confidence: Minimum confidence level filter

        Returns:
            DataFrame with top players ranked by predicted impact
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        logger.info(f"\nRanking top {top_n} players by predicted impact...")

        # Extract features
        X = df[[col for col in df.columns if col.startswith(self.config["player_feature_prefix"])]]
        X = X.fillna(X.median())

        # Predict impact
        df['predicted_on_off_diff'] = self.model.predict(X)

        # Sort by predicted impact
        rankings = df.nlargest(top_n, 'predicted_on_off_diff')

        logger.info(f"✓ Found {len(rankings)} top-impact players")

        return rankings

    def estimate_value(
        self,
        df: pd.DataFrame,
        value_per_point: float = 1000000  # $1M per point of on/off diff
    ) -> pd.DataFrame:
        """
        Estimate player contract value based on impact.

        Args:
            df: DataFrame with player features
            value_per_point: Dollar value per point of on/off differential

        Returns:
            DataFrame with estimated values
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        logger.info("\nEstimating player values...")

        # Extract features and predict
        X = df[[col for col in df.columns if col.startswith(self.config["player_feature_prefix"])]]
        X = X.fillna(X.median())

        df['predicted_on_off_diff'] = self.model.predict(X)

        # Estimate value (clip negatives to 0)
        df['estimated_value'] = (df['predicted_on_off_diff'].clip(lower=0) * value_per_point)

        logger.info(f"✓ Estimated values for {len(df)} players")

        return df

    def save_model(self, filepath: str):
        """Save trained model to disk."""
        if self.model is None:
            raise ValueError("Model not trained. Nothing to save.")

        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'config': self.config,
            'training_history': self.training_history
        }

        joblib.dump(model_data, filepath)
        logger.info(f"✓ Model saved to {filepath}")

    def load_model(self, filepath: str):
        """Load trained model from disk."""
        model_data = joblib.load(filepath)

        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        self.feature_importance = model_data['feature_importance']
        self.config = model_data['config']
        self.training_history = model_data['training_history']

        logger.info(f"✓ Model loaded from {filepath}")


def main():
    """Main entry point - Train player impact prediction model with demo data."""
    logger.info("=" * 80)
    logger.info("Player Impact Prediction Model - Training Demo")
    logger.info("=" * 80)

    # Step 1: Generate features using enhanced rec_11
    logger.info("\nStep 1: Generating features with enhanced rec_11...")

    pipeline = EnhancedFeatureEngineeringPipeline()
    pipeline.setup()

    # Create demo data
    demo_data = pipeline._create_demo_data()

    # Generate features
    enhanced_df = pipeline.generate_temporal_features(demo_data)
    enhanced_df = pipeline.generate_cumulative_features(enhanced_df)
    enhanced_df = pipeline.generate_plus_minus_features(enhanced_df)

    logger.info(f"✓ Enhanced DataFrame created: {enhanced_df.shape}")
    logger.info(f"✓ Total features: {len(enhanced_df.columns)}")

    # Step 2: Initialize and train model
    logger.info("\nStep 2: Training player impact prediction model...")

    model = PlayerImpactPredictionModel()

    # Prepare data
    X, y = model.prepare_data(enhanced_df)

    # Train model
    training_results = model.train(X, y, validation_split=True)

    # Step 3: Rank players by impact
    logger.info("\nStep 3: Ranking players by predicted impact...")

    rankings = model.rank_players(enhanced_df, top_n=5)

    logger.info("\nTop 5 Impact Players:")
    for idx, row in rankings.iterrows():
        logger.info(f"  {idx+1}. Player: Game {row.get('game_number', 'N/A')}")
        logger.info(f"     Predicted On/Off Diff: {row['predicted_on_off_diff']:.2f}")
        logger.info(f"     Avg Impact: {row.get('pm_player_avg_player_on_off_diff', 'N/A'):.2f}")

    # Step 4: Estimate player values
    logger.info("\nStep 4: Estimating player values...")

    valued_df = model.estimate_value(enhanced_df, value_per_point=1000000)

    logger.info("\nTop 5 Most Valuable Players:")
    top_values = valued_df.nlargest(5, 'estimated_value')
    for idx, row in top_values.iterrows():
        logger.info(f"  {idx+1}. Player: Game {row.get('game_number', 'N/A')}")
        logger.info(f"     On/Off Diff: {row['predicted_on_off_diff']:.2f}")
        logger.info(f"     Estimated Value: ${row['estimated_value']:,.0f}")

    # Step 5: Save model
    logger.info("\nStep 5: Saving trained model...")
    model_path = project_root / "models" / "player_impact_prediction_model.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(model_path))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Training Summary:")
    logger.info(f"  Samples: {training_results['samples_trained']}")
    logger.info(f"  Features: {training_results['features_used']}")
    logger.info(f"  Training MAE: {training_results['train_mae']:.2f}")
    logger.info(f"  Training R²: {training_results['train_r2']:.4f}")
    if training_results['cv_mae']:
        logger.info(f"  CV MAE: {training_results['cv_mae']:.2f} ± {training_results['cv_std']:.2f}")
    logger.info(f"  Training Time: {training_results['training_time']:.2f}s")
    logger.info("=" * 80)

    logger.info("\n✅ Player impact prediction model training complete!")


if __name__ == "__main__":
    main()

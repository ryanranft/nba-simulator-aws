#!/usr/bin/env python3
"""
Lineup Optimization Model - Predicts Best 5-Player Combinations

Purpose: Use plus/minus lineup features to predict and optimize 5-player lineup performance
Database: RDS PostgreSQL (nba_simulator)
Created: October 19, 2025

=== MODEL OVERVIEW ===

This model uses the 9 lineup features from the Plus/Minus system to:
1. Predict lineup net rating (offensive - defensive rating)
2. Identify optimal 5-player combinations
3. Recommend substitutions to improve lineup performance
4. Analyze lineup diversity and rotation patterns

=== FEATURES USED (9 lineup features) ===

Input Features (from rec_11 + Plus/Minus):
- pm_lineup_best_lineup_net_rating (best lineup performance)
- pm_lineup_worst_lineup_net_rating (worst lineup performance)
- pm_lineup_avg_lineup_net_rating (average performance)
- pm_lineup_net_rating_consistency (std dev of ratings)
- pm_lineup_best_offensive_rating (best offensive efficiency)
- pm_lineup_best_defensive_rating (best defensive efficiency)
- pm_lineup_lineup_count (number of unique lineups)
- pm_lineup_avg_possessions_per_lineup (playing time distribution)
- pm_lineup_lineup_diversity (1 / lineup_count)

Target Variable:
- lineup_net_rating (offensive_rating - defensive_rating)

=== MODEL ARCHITECTURE ===

Algorithm: XGBoost Regressor (chosen for accuracy + interpretability)
Validation: 5-Fold Time Series Cross-Validation
Metrics: MAE, RMSE, R², Feature Importance

=== USE CASES ===

1. Lineup Recommendation - Find best 5-player combinations
2. Substitution Optimization - Replace low-impact players
3. Rotation Planning - Optimize playing time distribution
4. Matchup Analysis - Best lineups vs specific opponents
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
import xgboost as xgb

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import enhanced rec_11
from scripts.ml.rec_11_with_plus_minus import EnhancedFeatureEngineeringPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LineupOptimizationModel:
    """
    Predicts and optimizes 5-player lineup performance using plus/minus features.

    Uses XGBoost to model lineup net rating based on:
    - Historical lineup efficiency metrics
    - Lineup diversity and rotation patterns
    - Offensive/defensive rating distributions
    """

    def __init__(self, model_config: Optional[Dict[str, Any]] = None):
        """
        Initialize LineupOptimizationModel.

        Args:
            model_config: Configuration for model hyperparameters
        """
        self.config = model_config or self._default_config()
        self.model = None
        self.feature_names = []
        self.feature_importance = None
        self.training_history = {}
        self.scaler = None

        logger.info("LineupOptimizationModel initialized")

    def _default_config(self) -> Dict[str, Any]:
        """Default model configuration."""
        return {
            # XGBoost hyperparameters
            "max_depth": 6,
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
            "lineup_feature_prefix": "pm_lineup_",
        }

    def prepare_data(
        self,
        df: pd.DataFrame,
        target_col: str = "lineup_net_rating"
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for training by extracting lineup features.

        Args:
            df: DataFrame with enhanced features (from rec_11 + plus/minus)
            target_col: Target variable column name

        Returns:
            Tuple of (X_features, y_target)
        """
        logger.info("Preparing data for lineup optimization model...")

        # Extract lineup features (pm_lineup_*)
        lineup_features = [col for col in df.columns if col.startswith(self.config["lineup_feature_prefix"])]

        if not lineup_features:
            raise ValueError("No lineup features found in DataFrame. Ensure plus/minus features are included.")

        logger.info(f"Found {len(lineup_features)} lineup features")

        # Prepare feature matrix
        X = df[lineup_features].copy()

        # Handle missing values (fill with median)
        X = X.fillna(X.median())

        # Prepare target variable
        if target_col in df.columns:
            y = df[target_col].copy()
        else:
            # If target not provided, use avg_lineup_net_rating as proxy
            logger.warning(f"Target '{target_col}' not found. Using pm_lineup_avg_lineup_net_rating as proxy.")
            y = df["pm_lineup_avg_lineup_net_rating"].copy()

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
        Train the lineup optimization model.

        Args:
            X: Feature matrix (lineup features)
            y: Target variable (lineup net rating)
            validation_split: Whether to use cross-validation

        Returns:
            Training metrics and results
        """
        logger.info("=" * 70)
        logger.info("Training Lineup Optimization Model")
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
        Predict lineup net rating for given features.

        Args:
            X: Feature matrix

        Returns:
            Predicted net ratings
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X)

    def recommend_lineups(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        min_possessions: int = 10
    ) -> pd.DataFrame:
        """
        Recommend top N lineups based on predicted net rating.

        Args:
            df: DataFrame with lineup features
            top_n: Number of top lineups to return
            min_possessions: Minimum possessions played (filter)

        Returns:
            DataFrame with top lineups ranked by predicted net rating
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        logger.info(f"\nGenerating top {top_n} lineup recommendations...")

        # Extract features
        X = df[[col for col in df.columns if col.startswith(self.config["lineup_feature_prefix"])]]
        X = X.fillna(X.median())

        # Predict net rating
        df['predicted_net_rating'] = self.model.predict(X)

        # Filter by minimum possessions (if column available)
        if 'pm_lineup_avg_possessions_per_lineup' in df.columns:
            df_filtered = df[df['pm_lineup_avg_possessions_per_lineup'] >= min_possessions]
        else:
            df_filtered = df

        # Sort by predicted net rating
        recommendations = df_filtered.nlargest(top_n, 'predicted_net_rating')

        logger.info(f"✓ Found {len(recommendations)} recommended lineups")

        return recommendations

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
    """Main entry point - Train lineup optimization model with demo data."""
    logger.info("=" * 80)
    logger.info("Lineup Optimization Model - Training Demo")
    logger.info("=" * 80)

    # Step 1: Generate features using enhanced rec_11
    logger.info("\nStep 1: Generating features with enhanced rec_11...")

    pipeline = EnhancedFeatureEngineeringPipeline()
    pipeline.setup()
    results = pipeline.execute()

    if not results.get("success"):
        logger.error("Feature engineering failed. Cannot train model.")
        sys.exit(1)

    # Get enhanced DataFrame (we need to recreate it since execute() doesn't return it)
    pipeline2 = EnhancedFeatureEngineeringPipeline()
    pipeline2.setup()
    demo_data = pipeline2._create_demo_data()

    # Generate features
    enhanced_df = pipeline2.generate_temporal_features(demo_data)
    enhanced_df = pipeline2.generate_cumulative_features(enhanced_df)
    enhanced_df = pipeline2.generate_plus_minus_features(enhanced_df)

    logger.info(f"✓ Enhanced DataFrame created: {enhanced_df.shape}")
    logger.info(f"✓ Total features: {len(enhanced_df.columns)}")

    # Step 2: Initialize and train model
    logger.info("\nStep 2: Training lineup optimization model...")

    model = LineupOptimizationModel()

    # Prepare data
    X, y = model.prepare_data(enhanced_df)

    # Train model
    training_results = model.train(X, y, validation_split=True)

    # Step 3: Get lineup recommendations
    logger.info("\nStep 3: Generating lineup recommendations...")

    recommendations = model.recommend_lineups(enhanced_df, top_n=5)

    logger.info("\nTop 5 Recommended Lineups:")
    for idx, row in recommendations.iterrows():
        logger.info(f"  {idx+1}. Predicted Net Rating: {row['predicted_net_rating']:.2f}")
        logger.info(f"     Best Lineup Rating: {row.get('pm_lineup_best_lineup_net_rating', 'N/A'):.2f}")
        logger.info(f"     Avg Possessions: {row.get('pm_lineup_avg_possessions_per_lineup', 'N/A'):.1f}")

    # Step 4: Save model
    logger.info("\nStep 4: Saving trained model...")
    model_path = project_root / "models" / "lineup_optimization_model.pkl"
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

    logger.info("\n✅ Lineup optimization model training complete!")


if __name__ == "__main__":
    main()

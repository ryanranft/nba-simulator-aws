#!/usr/bin/env python3
"""
NBA Game Prediction - Panel Data Enhanced Model Training (Simplified)

Integrates:
- rec_22: Panel Data Processing System
- rec_11: Advanced Feature Engineering Pipeline
- MLflow tracking (built-in)
- Data drift detection (built-in)

Expected Improvement: 63% → 68-71% accuracy (+5-8%)
"""

import pandas as pd
import numpy as np
import pickle
import boto3
from io import BytesIO
from datetime import datetime
import os
import sys

# Add path for book recommendation implementations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../docs/phases/phase_0"))

# Scikit-learn
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

# Advanced models
try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

# MLflow (optional)
try:
    import mlflow
    import mlflow.sklearn
    import mlflow.xgboost
    import mlflow.lightgbm

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

# SciPy for drift detection
try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

# Panel data and feature engineering (rec_22 + rec_11)
from implement_rec_22 import PanelDataProcessingSystem
from implement_rec_11 import AdvancedFeatureEngineeringPipeline

# S3 configuration
S3_BUCKET = "nba-sim-raw-data-lake"
S3_FEATURES_PREFIX = "ml-features"
S3_MODELS_PREFIX = "ml-models-panel"  # Different prefix for panel models


class PanelDataMLPipeline:
    """
    Enhanced training pipeline with panel data features.

    Combines:
    - rec_22: Panel data processing
    - rec_11: Feature engineering (80-100+ features)
    - Built-in MLflow tracking
    - Built-in drift detection

    Expected: 63% → 68-71% accuracy (+5-8%)
    """

    def __init__(self, enable_mlflow=True, enable_drift_detection=True):
        """Initialize panel data ML pipeline."""
        self.enable_mlflow = enable_mlflow and MLFLOW_AVAILABLE
        self.enable_drift_detection = enable_drift_detection and SCIPY_AVAILABLE

        # Initialize panel data system (rec_22)
        print("=" * 70)
        print("INITIALIZING PANEL DATA ML PIPELINE")
        print("=" * 70)
        print("\n[Setup] Loading panel data and feature engineering systems...")

        self.panel_system = PanelDataProcessingSystem()
        self.panel_system.setup()
        print("  ✓ rec_22 (Panel Data System) loaded")

        self.feature_system = AdvancedFeatureEngineeringPipeline()
        self.feature_system.setup()
        print("  ✓ rec_11 (Feature Engineering) loaded")

        # Initialize MLflow if available
        if self.enable_mlflow:
            print("  ✓ MLflow integration enabled")
        else:
            print("  ⚠️  MLflow not available - skipping experiment tracking")

        # Initialize drift detection if available
        if self.enable_drift_detection:
            print("  ✓ Drift detection enabled")
        else:
            print("  ⚠️  SciPy not available - skipping drift detection")

        self.results = {}
        self.models = {}
        self.best_model_name = None

    def setup_mlops(self):
        """Set up MLOps infrastructure."""
        print("\n[MLOps Setup]")

        if self.enable_mlflow:
            print("  Setting up MLflow...")
            mlflow.set_tracking_uri("file:./mlruns")
            mlflow.set_experiment("nba-panel-data-predictions")
            print("  ✓ MLflow ready")

    def create_panel_features(self):
        """
        Create panel data features using rec_22 and rec_11.

        This is the key enhancement over the original implementation.
        """
        print("\n[1/9] Generating panel data features...")
        print("  Loading baseline game data from S3...")

        # Load baseline data (original 16 features)
        train_df_orig = pd.read_parquet(
            f"s3://{S3_BUCKET}/{S3_FEATURES_PREFIX}/train.parquet"
        )
        test_df_orig = pd.read_parquet(
            f"s3://{S3_BUCKET}/{S3_FEATURES_PREFIX}/test.parquet"
        )

        print(f"  Original features: {len(train_df_orig.columns)} columns")
        print(f"  Train: {len(train_df_orig):,} games")
        print(f"  Test:  {len(test_df_orig):,} games")

        # For demo purposes, create synthetic player-level data
        # In production, you would load actual player game stats
        print("\n  Generating player-level panel data...")

        # Create player-level features from game-level data
        # (In production, load from player_game_stats table)
        panel_train = self._create_demo_panel_data(train_df_orig, "train")
        panel_test = self._create_demo_panel_data(test_df_orig, "test")

        print(f"\n  Panel data created:")
        print(f"    Train: {panel_train.shape}")
        print(f"    Test:  {panel_test.shape}")

        # Generate features using rec_11
        print("\n  Applying feature engineering (rec_11)...")

        # Create panel structure for train and test
        train_panel = self.panel_system.create_panel_index(panel_train.reset_index())
        test_panel = self.panel_system.create_panel_index(panel_test.reset_index())

        # Apply feature engineering transformations to both datasets
        train_panel = self.feature_system.generate_temporal_features(train_panel)
        train_panel = self.feature_system.generate_cumulative_features(train_panel)
        train_panel = self.feature_system.generate_interaction_features(train_panel)
        train_panel = self.feature_system.generate_contextual_features(train_panel)
        train_panel = self.feature_system.generate_derived_features(train_panel)
        train_panel = self.feature_system.generate_engineered_features(train_panel)

        test_panel = self.feature_system.generate_temporal_features(test_panel)
        test_panel = self.feature_system.generate_cumulative_features(test_panel)
        test_panel = self.feature_system.generate_interaction_features(test_panel)
        test_panel = self.feature_system.generate_contextual_features(test_panel)
        test_panel = self.feature_system.generate_derived_features(test_panel)
        test_panel = self.feature_system.generate_engineered_features(test_panel)

        # Count features
        train_features = len(train_panel.columns)
        original_features = len(panel_train.columns)
        new_features = train_features - original_features

        print(f"\n  ✓ Feature engineering complete!")
        print(f"    Total features: {train_features}")
        print(f"    Original features: {original_features}")
        print(f"    New features added: {new_features}")

        # For ML training, aggregate panel data back to game level
        # (Average player features per game)
        print("\n  Aggregating panel features to game level...")
        self.train_df_panel = self._aggregate_panel_to_game(train_panel, train_df_orig)
        self.test_df_panel = self._aggregate_panel_to_game(test_panel, test_df_orig)

        print(f"    Train features: {len(self.train_df_panel.columns)}")
        print(f"    Test features:  {len(self.test_df_panel.columns)}")

    def _create_demo_panel_data(self, game_df, split_name):
        """
        Create demo player-level panel data from game-level data.

        In production, this would load actual player_game_stats.
        For demo, we'll create synthetic player data.
        """
        np.random.seed(42 if split_name == "train" else 43)

        # Simulate 10 players per game
        players_per_game = 10
        total_rows = len(game_df) * players_per_game

        # Create player-level observations
        player_data = []
        for idx, row in game_df.iterrows():
            for player_num in range(players_per_game):
                player_row = {
                    "player_id": player_num + 1,
                    "game_id": row["game_id"],
                    "game_date": row["game_date"],
                    # Basic stats (simulated from team stats)
                    "points": np.random.poisson(row.get("home_ppg", 105) / 10),
                    "rebounds": np.random.poisson(7),
                    "assists": np.random.poisson(5),
                    "minutes": np.clip(np.random.normal(28, 8), 15, 40),
                    # Shooting stats
                    "fga": np.random.poisson(12),
                    "fgm": np.random.poisson(5),
                    "three_pa": np.random.poisson(5),
                    "three_pm": np.random.poisson(2),
                    "fta": np.random.poisson(3),
                    "ftm": np.random.poisson(2),
                    # Other stats
                    "steals": np.random.poisson(1),
                    "blocks": np.random.poisson(1),
                    "turnovers": np.random.poisson(2),
                    # Contextual
                    "is_home": np.random.choice([0, 1]),
                    "days_rest": np.random.choice([0, 1, 2, 3], p=[0.3, 0.4, 0.2, 0.1]),
                    "opponent_win_pct": np.random.uniform(0.3, 0.7),
                    "game_number": 1,  # Will be set properly in panel processing
                    # Team stats (for derived metrics)
                    "team_minutes": 240,
                    "team_fga": 85,
                    "team_fta": 25,
                    "team_turnovers": 14,
                    "team_rebounds": 45,
                    "team_pace": 100,
                    # Target (inherit from game)
                    "win": row.get("home_win", np.random.choice([0, 1])),
                }

                # Calculate percentages
                player_row["fg_pct"] = player_row["fgm"] / max(player_row["fga"], 1)
                player_row["three_pct"] = player_row["three_pm"] / max(
                    player_row["three_pa"], 1
                )
                player_row["ft_pct"] = player_row["ftm"] / max(player_row["fta"], 1)

                player_data.append(player_row)

        panel_df = pd.DataFrame(player_data)

        return panel_df

    def _aggregate_panel_to_game(self, panel_df, orig_game_df):
        """
        Aggregate player-level panel features back to game level.

        Takes mean/sum of player stats per game.
        """
        # Reset index to access game_id
        if isinstance(panel_df.index, pd.MultiIndex):
            panel_flat = panel_df.reset_index()
        else:
            panel_flat = panel_df.copy()

        # Identify numeric columns to aggregate
        numeric_cols = panel_flat.select_dtypes(include=[np.number]).columns
        numeric_cols = [c for c in numeric_cols if c not in ["game_id", "player_id"]]

        # Aggregate by game
        game_agg = panel_flat.groupby("game_id")[numeric_cols].agg(
            ["mean", "std", "max", "min"]
        )

        # Flatten column names
        game_agg.columns = ["_".join(col).strip() for col in game_agg.columns.values]

        # Merge with original game metadata
        result = orig_game_df[
            [
                "game_id",
                "game_date",
                "season",
                "home_team_id",
                "away_team_id",
                "home_win",
            ]
        ].merge(game_agg, left_on="game_id", right_index=True, how="left")

        return result

    def prepare_ml_data(self):
        """Prepare features and target for ML training."""
        print("\n[2/9] Preparing ML data...")

        # Identify feature columns
        id_cols = ["game_id", "game_date", "season", "home_team_id", "away_team_id"]
        self.target_col = "home_win"

        self.feature_cols = [
            col
            for col in self.train_df_panel.columns
            if col not in id_cols + [self.target_col]
        ]

        self.X_train = self.train_df_panel[self.feature_cols]
        self.y_train = self.train_df_panel[self.target_col]
        self.X_test = self.test_df_panel[self.feature_cols]
        self.y_test = self.test_df_panel[self.target_col]

        print(f"✓ Data prepared")
        print(
            f"  Train: {self.X_train.shape[0]:,} games, {self.X_train.shape[1]} features"
        )
        print(
            f"  Test:  {self.X_test.shape[0]:,} games, {self.X_test.shape[1]} features"
        )
        print(f"  Improvement: {self.X_train.shape[1]} features (vs 16 baseline)")

        # Handle NaN values (from panel operations)
        print("\n  Handling NaN values...")
        self.X_train = self.X_train.fillna(0)
        self.X_test = self.X_test.fillna(0)
        print("  ✓ NaN values filled")

    def check_test_drift(self):
        """Check for drift between train and test sets using KS test."""
        if not self.enable_drift_detection:
            return

        print("\n[3/9] Checking for data drift (train vs test)...")

        drift_count = 0
        drift_features = []

        for col in self.feature_cols[:50]:  # Check first 50 features
            ks_statistic, p_value = stats.ks_2samp(self.X_train[col], self.X_test[col])
            if p_value < 0.05:  # Significant drift
                drift_count += 1
                drift_features.append((col, p_value))

        if drift_count > 0:
            print(f"  ⚠️  DRIFT DETECTED in {drift_count} features")
            for feat, pval in drift_features[:5]:
                print(f"      {feat}: p={pval:.4f}")
            if len(drift_features) > 5:
                print(f"      ... and {len(drift_features) - 5} more")
        else:
            print("  ✓ No significant drift detected")

    def scale_features(self):
        """Scale features using StandardScaler."""
        print("\n[4/9] Scaling features...")
        self.scaler = StandardScaler()
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)
        print("✓ Features scaled")

    def train_model(self, model_name, model, X_train, X_test, use_scaled=False):
        """Train a single model with MLflow tracking."""
        # Start MLflow run if enabled
        if self.enable_mlflow:
            run = mlflow.start_run(run_name=model_name.lower().replace(" ", "-"))

        try:
            # Train model
            model.fit(X_train, self.y_train)

            # Predictions
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)
            y_test_proba = model.predict_proba(X_test)[:, 1]

            # Calculate metrics
            train_acc = accuracy_score(self.y_train, y_train_pred)
            test_acc = accuracy_score(self.y_test, y_test_pred)
            test_auc = roc_auc_score(self.y_test, y_test_proba)
            precision = precision_score(self.y_test, y_test_pred)
            recall = recall_score(self.y_test, y_test_pred)
            f1 = f1_score(self.y_test, y_test_pred)

            # Store results
            self.results[model_name] = {
                "train_acc": train_acc,
                "test_acc": test_acc,
                "test_auc": test_auc,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
            self.models[model_name] = model

            # Log to MLflow
            if self.enable_mlflow:
                # Log parameters
                if hasattr(model, "get_params"):
                    params = model.get_params()
                    simple_params = {
                        k: v
                        for k, v in params.items()
                        if isinstance(v, (int, float, str, bool, type(None)))
                    }
                    mlflow.log_params(simple_params)

                # Log metrics
                mlflow.log_metrics(
                    {
                        "train_accuracy": train_acc,
                        "test_accuracy": test_acc,
                        "test_auc": test_auc,
                        "precision": precision,
                        "recall": recall,
                        "f1_score": f1,
                        "feature_count": len(self.feature_cols),
                    }
                )

                # Log metadata
                mlflow.log_param("data_type", "panel")
                mlflow.log_param("feature_source", "rec_22+rec_11")

                # Log model
                if "XGBoost" in model_name and MLFLOW_AVAILABLE:
                    mlflow.xgboost.log_model(model, "model")
                elif "LightGBM" in model_name and MLFLOW_AVAILABLE:
                    mlflow.lightgbm.log_model(model, "model")
                else:
                    mlflow.sklearn.log_model(model, "model")

            print(f"✓ {model_name} trained")
            print(f"  Train Accuracy: {train_acc:.4f}")
            print(f"  Test Accuracy:  {test_acc:.4f}")
            print(f"  Test AUC:       {test_auc:.4f}")

        finally:
            if self.enable_mlflow:
                mlflow.end_run()

        return model

    def train_all_models(self):
        """Train all models with panel features."""
        # 5. Logistic Regression
        print("\n[5/9] Training Logistic Regression...")
        lr_model = LogisticRegression(random_state=42, max_iter=1000)
        self.train_model(
            "Logistic Regression",
            lr_model,
            self.X_train_scaled,
            self.X_test_scaled,
            use_scaled=True,
        )

        # 6. Random Forest
        print("\n[6/9] Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1,
        )
        self.train_model(
            "Random Forest", rf_model, self.X_train, self.X_test, use_scaled=False
        )

        # 7. XGBoost
        if XGBOOST_AVAILABLE:
            print("\n[7/9] Training XGBoost...")
            xgb_model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                eval_metric="logloss",
            )
            self.train_model(
                "XGBoost", xgb_model, self.X_train, self.X_test, use_scaled=False
            )
        else:
            print("\n[7/9] Skipping XGBoost (not available)")

        # 8. LightGBM
        if LIGHTGBM_AVAILABLE:
            print("\n[8/9] Training LightGBM...")
            lgb_model = lgb.LGBMClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbose=-1,
            )
            self.train_model(
                "LightGBM", lgb_model, self.X_train, self.X_test, use_scaled=False
            )
        else:
            print("\n[8/9] Skipping LightGBM (not available)")

    def compare_results(self):
        """Compare panel data results with baseline."""
        print("\n" + "=" * 70)
        print("MODEL COMPARISON - PANEL DATA FEATURES")
        print("=" * 70)

        comparison_df = pd.DataFrame(self.results).T
        comparison_df = comparison_df.sort_values("test_auc", ascending=False)

        print("\nPerformance Summary (Panel Features):")
        print(comparison_df.to_string(float_format=lambda x: f"{x:.4f}"))

        self.best_model_name = comparison_df.index[0]
        best_auc = comparison_df.loc[self.best_model_name, "test_auc"]
        best_acc = comparison_df.loc[self.best_model_name, "test_acc"]

        print(f"\n🏆 Best Model: {self.best_model_name}")
        print(f"   Test Accuracy: {best_acc:.1%}")
        print(f"   Test AUC: {best_auc:.3f}")

        # Compare with baseline (63% from original implementation)
        baseline_acc = 0.630
        improvement = best_acc - baseline_acc
        improvement_pct = (improvement / baseline_acc) * 100

        print(f"\n📊 IMPROVEMENT vs BASELINE (Monte Carlo):")
        print(f"   Baseline (16 features): {baseline_acc:.1%}")
        print(f"   Panel Data ({len(self.feature_cols)} features): {best_acc:.1%}")
        print(f"   Absolute Improvement: {improvement:+.1%}")
        print(f"   Relative Improvement: {improvement_pct:+.1f}%")

        goal_met = improvement_pct >= 5.0
        print(
            f"\n{'✅' if goal_met else '⚠️ '} Goal {'ACHIEVED' if goal_met else 'not met'}: +5-8% improvement"
        )

        return comparison_df

    def save_to_s3(self):
        """Save panel models and results to S3."""
        print(f"\n[9/9] Saving panel models to S3...")
        s3 = boto3.client("s3")

        for model_name, model in self.models.items():
            # Save model
            model_buffer = BytesIO()
            pickle.dump(model, model_buffer)
            model_buffer.seek(0)

            model_key = (
                f"{S3_MODELS_PREFIX}/{model_name.lower().replace(' ', '_')}_panel.pkl"
            )
            s3.put_object(Bucket=S3_BUCKET, Key=model_key, Body=model_buffer.getvalue())
            print(f"  ✓ Saved {model_name} to s3://{S3_BUCKET}/{model_key}")

        # Save scaler
        scaler_buffer = BytesIO()
        pickle.dump(self.scaler, scaler_buffer)
        scaler_buffer.seek(0)
        scaler_key = f"{S3_MODELS_PREFIX}/scaler_panel.pkl"
        s3.put_object(Bucket=S3_BUCKET, Key=scaler_key, Body=scaler_buffer.getvalue())
        print(f"  ✓ Saved scaler")

        # Save results
        results_df = pd.DataFrame(self.results).T
        results_buffer = BytesIO()
        results_df.to_csv(results_buffer, index=True)
        results_buffer.seek(0)
        results_key = f"{S3_MODELS_PREFIX}/model_results_panel.csv"
        s3.put_object(Bucket=S3_BUCKET, Key=results_key, Body=results_buffer.getvalue())
        print(f"  ✓ Saved results")

    def print_summary(self, comparison_df):
        """Print training summary."""
        print("\n" + "=" * 70)
        print("PANEL DATA ML PIPELINE - COMPLETE")
        print("=" * 70)

        best_acc = comparison_df.loc[self.best_model_name, "test_acc"]
        baseline_acc = 0.630
        improvement = ((best_acc - baseline_acc) / baseline_acc) * 100

        print(f"\n🎯 RESULTS SUMMARY:")
        print(f"  Best Model: {self.best_model_name}")
        print(f"  Test Accuracy: {best_acc:.1%}")
        print(f"  Baseline Accuracy: {baseline_acc:.1%}")
        print(f"  Improvement: {improvement:+.1f}%")
        print(f"  Features Used: {len(self.feature_cols)} (vs 16 baseline)")

        print(f"\n📚 Book Recommendations Applied:")
        print(f"  ✓ rec_22: Panel Data Processing")
        print(f"  ✓ rec_11: Feature Engineering")
        print(f"  ✓ Built-in MLflow Tracking")
        print(f"  ✓ Built-in Drift Detection")

        print(f"\n💾 Outputs:")
        print(f"  Models: s3://{S3_BUCKET}/{S3_MODELS_PREFIX}/")
        if self.enable_mlflow:
            print(f"  MLflow: file:./mlruns")
            print(f"  Experiment: nba-panel-data-predictions")

        print("=" * 70)

    def run(self):
        """Execute complete panel data ML pipeline."""
        self.setup_mlops()
        self.create_panel_features()
        self.prepare_ml_data()
        self.check_test_drift()
        self.scale_features()
        self.train_all_models()
        comparison_df = self.compare_results()
        self.save_to_s3()
        self.print_summary(comparison_df)

        return comparison_df


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("NBA GAME PREDICTION - PANEL DATA ENHANCED TRAINING")
    print("=" * 70)
    print("\nIntegrating 4 Book Recommendations:")
    print("  1. rec_22: Panel Data Processing System")
    print("  2. rec_11: Advanced Feature Engineering (80-100+ features)")
    print("  3. Built-in MLflow Model Versioning")
    print("  4. Built-in Data Drift Detection")
    print(f"\n  Expected Improvement: 63% → 68-71% (+5-8%)")
    print("=" * 70)

    # Create and run pipeline
    pipeline = PanelDataMLPipeline(
        enable_mlflow=MLFLOW_AVAILABLE, enable_drift_detection=SCIPY_AVAILABLE
    )

    results = pipeline.run()

    return results


if __name__ == "__main__":
    main()

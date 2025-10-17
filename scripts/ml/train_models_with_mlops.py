#!/usr/bin/env python3
"""
NBA Game Prediction - MLOps-Enhanced Model Training Script

Integrates:
- MLflow for model versioning and experiment tracking (ml_systems_1)
- Data drift detection for monitoring (ml_systems_2)
- Existing Phase 5 model training pipeline

This script demonstrates how to use both book recommendation implementations
with real NBA prediction models.
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
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

# Advanced models
import xgboost as xgb
import lightgbm as lgb

# MLOps implementations (from book recommendations)
from implement_ml_systems_1 import ModelVersioningWithMlflow, MLFLOW_AVAILABLE
from implement_ml_systems_2 import DataDriftDetection, SCIPY_AVAILABLE

# MLflow (optional)
if MLFLOW_AVAILABLE:
    import mlflow

# S3 configuration
S3_BUCKET = "nba-sim-raw-data-lake"
S3_FEATURES_PREFIX = "ml-features"
S3_MODELS_PREFIX = "ml-models"


class MLOpsTrainingPipeline:
    """
    Enhanced training pipeline with MLflow tracking and drift detection.

    Combines:
    - Original Phase 5 model training
    - ml_systems_1: MLflow model versioning
    - ml_systems_2: Data drift detection
    """

    def __init__(self, enable_mlflow=True, enable_drift_detection=True):
        """
        Initialize MLOps training pipeline.

        Args:
            enable_mlflow: Enable MLflow tracking and versioning
            enable_drift_detection: Enable drift detection
        """
        self.enable_mlflow = enable_mlflow and MLFLOW_AVAILABLE
        self.enable_drift_detection = enable_drift_detection and SCIPY_AVAILABLE

        # Initialize MLflow manager
        if self.enable_mlflow:
            self.mlflow_config = {
                "tracking_uri": "file:./mlruns",  # Local tracking (can use S3)
                "experiment_name": "nba-game-predictions",
                "artifact_location": f"s3://{S3_BUCKET}/mlflow",
                "default_tags": {
                    "project": "nba-simulator-aws",
                    "phase": "5",
                    "environment": "development",
                },
            }
            self.mlflow_manager = ModelVersioningWithMlflow(self.mlflow_config)
            print("✓ MLflow integration enabled")

        # Initialize drift detector
        if self.enable_drift_detection:
            self.drift_config = {
                "alert_threshold_psi": 0.2,
                "alert_threshold_ks": 0.1,
                "alert_threshold_chi2": 0.05,
                "mlflow_tracking": self.enable_mlflow,  # Log drift to MLflow
            }
            self.drift_detector = DataDriftDetection(self.drift_config)
            print("✓ Drift detection enabled")

        self.results = {}
        self.models = {}
        self.best_model_name = None

    def setup_mlops(self):
        """Set up MLOps infrastructure."""
        print("\n[MLOps Setup]")

        if self.enable_mlflow:
            print("  Setting up MLflow...")
            self.mlflow_manager.setup()
            print("  ✓ MLflow ready")

        if self.enable_drift_detection:
            print("  Setting up drift detection...")
            # Will setup with reference data after loading features
            print("  ✓ Drift detection ready (will load reference data)")

    def load_data(self):
        """Load training and test data from S3."""
        print("\n[1/8] Loading feature data from S3...")

        self.train_df = pd.read_parquet(
            f"s3://{S3_BUCKET}/{S3_FEATURES_PREFIX}/train.parquet"
        )
        self.test_df = pd.read_parquet(
            f"s3://{S3_BUCKET}/{S3_FEATURES_PREFIX}/test.parquet"
        )

        # Prepare features and target
        id_cols = ["game_id", "game_date", "season", "home_team_id", "away_team_id"]
        self.target_col = "home_win"
        self.feature_cols = [
            col
            for col in self.train_df.columns
            if col not in id_cols + [self.target_col]
        ]

        self.X_train = self.train_df[self.feature_cols]
        self.y_train = self.train_df[self.target_col]
        self.X_test = self.test_df[self.feature_cols]
        self.y_test = self.test_df[self.target_col]

        print(f"✓ Data loaded")
        print(
            f"  Train: {self.X_train.shape[0]:,} games, {self.X_train.shape[1]} features"
        )
        print(
            f"  Test:  {self.X_test.shape[0]:,} games, {self.X_test.shape[1]} features"
        )
        print(f"  Features: {', '.join(self.feature_cols[:5])}...")

        # Setup drift detection with training data as reference
        if self.enable_drift_detection:
            print("\n  Setting up drift detection with training data as reference...")
            self.drift_config["reference_data"] = self.X_train
            self.drift_detector = DataDriftDetection(self.drift_config)
            self.drift_detector.setup()
            print("  ✓ Drift detector configured with training features")

    def check_test_drift(self):
        """Check for drift between train and test sets."""
        if not self.enable_drift_detection:
            return

        print("\n[2/8] Checking for data drift (train vs test)...")

        drift_results = self.drift_detector.detect_drift(self.X_test)

        if drift_results["summary"]["overall_drift_detected"]:
            print(
                f"  ⚠️  DRIFT DETECTED in {drift_results['summary']['features_with_drift']} features"
            )
            for alert in drift_results["alerts"][:5]:  # Show first 5
                print(f"      {alert}")
            if len(drift_results["alerts"]) > 5:
                print(f"      ... and {len(drift_results['alerts']) - 5} more")
        else:
            print("  ✓ No significant drift detected")

        return drift_results

    def scale_features(self):
        """Scale features using StandardScaler."""
        print("\n[3/8] Scaling features...")
        self.scaler = StandardScaler()
        self.X_train_scaled = self.scaler.fit_transform(self.X_train)
        self.X_test_scaled = self.scaler.transform(self.X_test)
        print("✓ Features scaled")

    def train_model(self, model_name, model, X_train, X_test, use_scaled=False):
        """
        Train a single model with MLflow tracking.

        Args:
            model_name: Name of the model
            model: Model instance
            X_train: Training features
            X_test: Test features
            use_scaled: Whether features are scaled
        """
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
                    # Log important params (filter out complex objects)
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
                    }
                )

                # Log model
                if "XGBoost" in model_name:
                    mlflow.xgboost.log_model(model, "model")
                elif "LightGBM" in model_name:
                    mlflow.lightgbm.log_model(model, "model")
                else:
                    mlflow.sklearn.log_model(model, "model")

                # Log feature importance if available
                if hasattr(model, "feature_importances_"):
                    importance_df = (
                        pd.DataFrame(
                            {
                                "feature": self.feature_cols,
                                "importance": model.feature_importances_,
                            }
                        )
                        .sort_values("importance", ascending=False)
                        .head(20)
                    )

                    mlflow.log_dict(importance_df.to_dict(), "top_features.json")

            print(f"✓ {model_name} trained")
            print(f"  Train Accuracy: {train_acc:.4f}")
            print(f"  Test Accuracy:  {test_acc:.4f}")
            print(f"  Test AUC:       {test_auc:.4f}")

        finally:
            if self.enable_mlflow:
                mlflow.end_run()

        return model

    def train_all_models(self):
        """Train all models."""
        # 4. Logistic Regression
        print("\n[4/8] Training Logistic Regression...")
        lr_model = LogisticRegression(random_state=42, max_iter=1000)
        self.train_model(
            "Logistic Regression",
            lr_model,
            self.X_train_scaled,
            self.X_test_scaled,
            use_scaled=True,
        )

        # 5. Random Forest
        print("\n[5/8] Training Random Forest...")
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

        # 6. XGBoost
        print("\n[6/8] Training XGBoost...")
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

        # 7. LightGBM
        print("\n[7/8] Training LightGBM...")
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

    def compare_and_register_models(self):
        """Compare models and register best to MLflow."""
        print("\n" + "=" * 70)
        print("MODEL COMPARISON")
        print("=" * 70)

        comparison_df = pd.DataFrame(self.results).T
        comparison_df = comparison_df.sort_values("test_auc", ascending=False)

        print("\nPerformance Summary:")
        print(comparison_df.to_string(float_format=lambda x: f"{x:.4f}"))

        self.best_model_name = comparison_df.index[0]
        best_model = self.models[self.best_model_name]
        best_auc = comparison_df.loc[self.best_model_name, "test_auc"]

        print(f"\n🏆 Best Model: {self.best_model_name} (AUC: {best_auc:.4f})")

        # Register best model to MLflow
        if self.enable_mlflow:
            print("\n[MLflow] Registering best model...")
            # Note: Model already logged during training, just need to register
            # This is a placeholder - in real usage, you'd get the run_id from the best run
            print(f"  Model '{self.best_model_name}' logged to MLflow")
            print(f"  To register: Use MLflow UI or API with the run_id")
            print(f"  MLflow UI: mlflow ui --backend-store-uri file:./mlruns")

        return comparison_df

    def save_to_s3(self):
        """Save models and results to S3 (traditional approach)."""
        print(f"\n[8/8] Saving models to S3...")
        s3 = boto3.client("s3")

        for model_name, model in self.models.items():
            # Save model
            model_buffer = BytesIO()
            pickle.dump(model, model_buffer)
            model_buffer.seek(0)

            model_key = f"{S3_MODELS_PREFIX}/{model_name.lower().replace(' ', '_')}.pkl"
            s3.put_object(Bucket=S3_BUCKET, Key=model_key, Body=model_buffer.getvalue())
            print(f"  ✓ Saved {model_name} to s3://{S3_BUCKET}/{model_key}")

        # Save scaler
        scaler_buffer = BytesIO()
        pickle.dump(self.scaler, scaler_buffer)
        scaler_buffer.seek(0)
        scaler_key = f"{S3_MODELS_PREFIX}/scaler.pkl"
        s3.put_object(Bucket=S3_BUCKET, Key=scaler_key, Body=scaler_buffer.getvalue())
        print(f"  ✓ Saved scaler to s3://{S3_BUCKET}/{scaler_key}")

        # Save results
        results_df = pd.DataFrame(self.results).T
        results_buffer = BytesIO()
        results_df.to_csv(results_buffer, index=True)
        results_buffer.seek(0)
        results_key = f"{S3_MODELS_PREFIX}/model_results.csv"
        s3.put_object(Bucket=S3_BUCKET, Key=results_key, Body=results_buffer.getvalue())
        print(f"  ✓ Saved results to s3://{S3_BUCKET}/{results_key}")

    def print_summary(self, comparison_df):
        """Print training summary."""
        print("\n" + "=" * 70)
        print("MODEL TRAINING COMPLETE")
        print("=" * 70)

        print(f"\n📊 Models Trained: {len(self.models)}")
        print(f"  1. Logistic Regression (baseline)")
        print(f"  2. Random Forest")
        print(f"  3. XGBoost")
        print(f"  4. LightGBM")

        print(f"\n📈 Best Performance:")
        print(f"  Model: {self.best_model_name}")
        print(
            f"  Test Accuracy: {comparison_df.loc[self.best_model_name, 'test_acc']:.1%}"
        )
        print(f"  Test AUC: {comparison_df.loc[self.best_model_name, 'test_auc']:.3f}")
        print(
            f"  Precision: {comparison_df.loc[self.best_model_name, 'precision']:.3f}"
        )
        print(f"  Recall: {comparison_df.loc[self.best_model_name, 'recall']:.3f}")
        print(f"  F1 Score: {comparison_df.loc[self.best_model_name, 'f1']:.3f}")

        goal_met = comparison_df.loc[self.best_model_name, "test_acc"] > 0.60
        print(
            f"\n{'✓' if goal_met else '⚠️ '} Goal {'achieved' if goal_met else 'not met'}: Accuracy > 60%"
        )

        print(f"\n💾 Traditional S3 Outputs:")
        print(f"  Models: s3://{S3_BUCKET}/{S3_MODELS_PREFIX}/")
        print(f"  Results: s3://{S3_BUCKET}/{S3_MODELS_PREFIX}/model_results.csv")

        if self.enable_mlflow:
            print(f"\n🔬 MLflow Outputs:")
            print(f"  Tracking URI: {self.mlflow_config['tracking_uri']}")
            print(f"  Experiment: {self.mlflow_config['experiment_name']}")
            print(f"  Artifacts: {self.mlflow_config['artifact_location']}")
            print(
                f"  View: mlflow ui --backend-store-uri {self.mlflow_config['tracking_uri']}"
            )

        print(f"\n🎯 Next Steps:")
        if self.enable_mlflow:
            print(f"  1. View experiments: mlflow ui")
            print(f"  2. Register best model for production")
            print(f"  3. Set up drift monitoring for production data")
        else:
            print(f"  1. Enable MLflow for experiment tracking")
            print(f"  2. Enable drift detection for monitoring")
        print("=" * 70)

    def run(self):
        """Execute complete training pipeline."""
        print("=" * 70)
        print("NBA GAME PREDICTION - MLOps-ENHANCED MODEL TRAINING")
        print("=" * 70)
        print()

        self.setup_mlops()
        self.load_data()
        self.check_test_drift()
        self.scale_features()
        self.train_all_models()
        comparison_df = self.compare_and_register_models()
        self.save_to_s3()
        self.print_summary(comparison_df)

        return comparison_df


def main():
    """Main entry point."""
    # Check MLOps availability
    print("MLOps Systems Status:")
    print(
        f"  MLflow Available: {'✓' if MLFLOW_AVAILABLE else '✗ (pip install mlflow)'}"
    )
    print(
        f"  Drift Detection Available: {'✓' if SCIPY_AVAILABLE else '✗ (pip install scipy)'}"
    )
    print()

    # Create and run pipeline
    pipeline = MLOpsTrainingPipeline(
        enable_mlflow=MLFLOW_AVAILABLE, enable_drift_detection=SCIPY_AVAILABLE
    )

    results = pipeline.run()

    return results


if __name__ == "__main__":
    main()

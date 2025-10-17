#!/usr/bin/env python3
"""
Monitoring Dashboard: Track model performance and feature drift over time.

This script:
1. Tracks prediction accuracy on new data
2. Monitors feature distributions for drift
3. Alerts on performance degradation
4. Generates monitoring reports

Usage:
    python scripts/ml/monitoring_dashboard.py --data path/to/new_data.parquet
"""

import pandas as pd
import numpy as np
import mlflow
import pickle
from datetime import datetime
from sklearn.metrics import accuracy_score, roc_auc_score
import warnings

warnings.filterwarnings("ignore")


class ModelMonitor:
    """Monitor model performance and feature drift."""

    def __init__(self, model_run_id, baseline_stats_path="/tmp/train_stats.csv"):
        """Initialize monitor with model and baseline statistics."""
        self.model_run_id = model_run_id
        self.model = mlflow.sklearn.load_model(f"runs:/{model_run_id}/model")

        with open("/tmp/scaler.pkl", "rb") as f:
            self.scaler = pickle.load(f)

        with open("/tmp/feature_list.txt", "r") as f:
            self.feature_list = [line.strip() for line in f]

        self.baseline_stats = pd.read_csv(baseline_stats_path, index_col="feature")

        print(f"✓ Model monitor initialized")
        print(f"  Model: {model_run_id}")
        print(f"  Features: {len(self.feature_list)}")

    def evaluate_performance(self, X, y, period_name="Unknown"):
        """Evaluate model performance on new data."""
        print(f"\nEvaluating performance on {period_name}...")

        # Prepare data
        X_selected = X[self.feature_list]

        # Handle missing/inf
        for col in X_selected.columns:
            if X_selected[col].isna().any() or np.isinf(X_selected[col]).any():
                X_selected[col] = X_selected[col].replace([np.inf, -np.inf], np.nan)
                X_selected[col] = X_selected[col].fillna(
                    self.baseline_stats.loc[col, "mean"]
                )

        # Scale and predict
        X_scaled = self.scaler.transform(X_selected)
        y_pred = self.model.predict(X_scaled)
        y_proba = self.model.predict_proba(X_scaled)[:, 1]

        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        auc = roc_auc_score(y, y_proba)

        print(f"  Accuracy: {accuracy:.1%}")
        print(f"  AUC: {auc:.3f}")

        # Compare to baseline
        baseline_accuracy = 0.840
        baseline_auc = 0.918

        if accuracy < baseline_accuracy - 0.05:  # 5% drop
            print(
                f"  ⚠️  WARNING: Accuracy dropped by {(baseline_accuracy - accuracy) * 100:.1f}pp"
            )
        else:
            print(f"  ✓ Performance maintained")

        return {
            "period": period_name,
            "accuracy": accuracy,
            "auc": auc,
            "n_samples": len(X),
            "baseline_accuracy": baseline_accuracy,
            "baseline_auc": baseline_auc,
            "timestamp": datetime.now().isoformat(),
        }

    def check_feature_drift(self, X, top_n=20):
        """Check for feature distribution drift."""
        print(f"\nChecking feature drift (top {top_n} features)...")

        X_selected = X[self.feature_list]

        # Get top important features (from feature_importance.csv)
        try:
            importance = pd.read_csv("/tmp/feature_importance.csv")
            top_features = importance.nlargest(top_n, "abs_coefficient")[
                "feature"
            ].tolist()
        except:
            top_features = self.feature_list[:top_n]

        drift_report = []

        for feature in top_features:
            if feature not in X_selected.columns:
                continue

            # Current statistics
            current_mean = X_selected[feature].mean()
            current_std = X_selected[feature].std()

            # Baseline statistics
            baseline_mean = self.baseline_stats.loc[feature, "mean"]
            baseline_std = self.baseline_stats.loc[feature, "std"]

            # Calculate drift (normalized difference)
            if baseline_std > 0:
                mean_drift = abs(current_mean - baseline_mean) / baseline_std
            else:
                mean_drift = 0

            # Flag if drift > 2 standard deviations
            is_drifted = mean_drift > 2.0

            drift_report.append(
                {
                    "feature": feature,
                    "baseline_mean": baseline_mean,
                    "current_mean": current_mean,
                    "mean_drift": mean_drift,
                    "is_drifted": is_drifted,
                }
            )

        drift_df = pd.DataFrame(drift_report)

        # Summary
        drifted_features = drift_df[drift_df["is_drifted"]]["feature"].tolist()
        if drifted_features:
            print(f"  ⚠️  {len(drifted_features)} features have drifted:")
            for feat in drifted_features[:5]:  # Show first 5
                drift_value = drift_df[drift_df["feature"] == feat][
                    "mean_drift"
                ].values[0]
                print(f"    - {feat}: {drift_value:.2f} std deviations")
        else:
            print(f"  ✓ No significant drift detected")

        return drift_df

    def generate_report(self, performance_metrics, drift_df):
        """Generate monitoring report."""
        print("\n" + "=" * 70)
        print("MONITORING REPORT")
        print("=" * 70)

        print(f"\nPeriod: {performance_metrics['period']}")
        print(f"Timestamp: {performance_metrics['timestamp']}")
        print(f"Samples: {performance_metrics['n_samples']:,}")

        print(f"\nPerformance:")
        print(f"  Current Accuracy: {performance_metrics['accuracy']:.1%}")
        print(f"  Baseline Accuracy: {performance_metrics['baseline_accuracy']:.1%}")
        print(
            f"  Difference: {(performance_metrics['accuracy'] - performance_metrics['baseline_accuracy']) * 100:+.1f}pp"
        )

        print(f"\n  Current AUC: {performance_metrics['auc']:.3f}")
        print(f"  Baseline AUC: {performance_metrics['baseline_auc']:.3f}")
        print(
            f"  Difference: {(performance_metrics['auc'] - performance_metrics['baseline_auc']):+.3f}"
        )

        print(f"\nFeature Drift:")
        drifted = drift_df[drift_df["is_drifted"]]
        if len(drifted) > 0:
            print(f"  ⚠️  {len(drifted)} features drifted (> 2 std)")
            print(f"\n  Top 5 drifted features:")
            for _, row in drifted.nlargest(5, "mean_drift").iterrows():
                print(f"    {row['feature'][:40]:40s}  {row['mean_drift']:.2f} std")
        else:
            print(f"  ✓ No significant drift")

        print(f"\nRecommendations:")
        if performance_metrics["accuracy"] < 0.80:
            print(f"  ⚠️  RETRAIN: Accuracy below 80%")
        elif len(drifted) > 10:
            print(f"  ⚠️  RETRAIN: Many features drifted")
        else:
            print(f"  ✓ Model performing well")

        print("=" * 70)


def main():
    """Main monitoring function."""
    print("=" * 70)
    print("MODEL MONITORING DASHBOARD")
    print("=" * 70)

    # Initialize monitor
    run_id = "1a2725dca5304ec9ad9602756296153e"
    monitor = ModelMonitor(run_id)

    # Load test data (2021 season as example)
    print("\n[1/3] Loading monitoring data...")
    df = pd.read_parquet("/tmp/real_nba_game_features_selected.parquet")
    test_df = df[df["year"] == 2021].copy()

    X = test_df.drop(["game_id", "won", "year"], axis=1)
    y = test_df["won"]

    print(f"  Loaded: {len(test_df):,} games from 2021")

    # Evaluate performance
    print("\n[2/3] Evaluating model performance...")
    performance = monitor.evaluate_performance(X, y, period_name="2021 Season")

    # Check drift
    print("\n[3/3] Checking feature drift...")
    drift_df = monitor.check_feature_drift(X, top_n=50)

    # Generate report
    monitor.generate_report(performance, drift_df)

    # Save monitoring data
    print("\nSaving monitoring data...")

    # Performance history
    perf_df = pd.DataFrame([performance])
    perf_df.to_csv(
        "/tmp/monitoring_performance.csv",
        mode="a",
        header=not pd.io.common.file_exists("/tmp/monitoring_performance.csv"),
        index=False,
    )
    print(f"  ✓ Performance saved to /tmp/monitoring_performance.csv")

    # Drift report
    drift_df.to_csv("/tmp/monitoring_drift.csv", index=False)
    print(f"  ✓ Drift report saved to /tmp/monitoring_drift.csv")

    print("\n" + "=" * 70)
    print("✓ MONITORING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

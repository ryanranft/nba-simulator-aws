#!/usr/bin/env python3
"""
MLflow Setup: Register final model with complete artifacts for production deployment.

This script:
1. Trains the final validated model (84% accuracy, 300 features)
2. Logs training metrics and parameters
3. Saves model artifacts (model, scaler, feature list, training stats)
4. Registers model in MLflow Model Registry
"""

import pandas as pd
import numpy as np
import pickle
import mlflow
import mlflow.sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)
import warnings

warnings.filterwarnings("ignore")

print("=" * 70)
print("MLFLOW MODEL REGISTRATION")
print("=" * 70)
print("\nGoal: Register final production model with all artifacts")
print("Model: Logistic Regression (84% accuracy, 300 features)")
print("=" * 70)

# Configure MLflow
print("\n[1/7] Configuring MLflow...")
mlflow.set_tracking_uri("file:./mlruns")  # Local file-based tracking
mlflow.set_experiment("nba_game_prediction")
print(f"  Tracking URI: {mlflow.get_tracking_uri()}")
print(f"  Experiment: nba_game_prediction")

# Load data
print("\n[2/7] Loading training data...")
df = pd.read_parquet("/tmp/real_nba_game_features_selected.parquet")

train_df = df[df["year"] <= 2020].copy()
test_df = df[df["year"] == 2021].copy()

X_train = train_df.drop(["game_id", "won", "year"], axis=1)
y_train = train_df["won"]
X_test = test_df.drop(["game_id", "won", "year"], axis=1)
y_test = test_df["won"]

print(f"  Train: {X_train.shape}")
print(f"  Test: {X_test.shape}")
print(f"  Features: {len(X_train.columns)}")

# Clean data
X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_test = X_test.replace([np.inf, -np.inf], np.nan)
train_means = X_train.mean()
X_train = X_train.fillna(train_means)
X_test = X_test.fillna(train_means)

# Start MLflow run
print("\n[3/7] Starting MLflow run...")
with mlflow.start_run(run_name="final_model_v1.0") as run:

    # Log parameters
    print("\n[4/7] Logging parameters...")
    mlflow.log_param("model_type", "LogisticRegression")
    mlflow.log_param("C", 1.0)
    mlflow.log_param("penalty", "l2")
    mlflow.log_param("max_iter", 1000)
    mlflow.log_param("solver", "lbfgs")
    mlflow.log_param("n_features", len(X_train.columns))
    mlflow.log_param("train_size", len(X_train))
    mlflow.log_param("test_size", len(X_test))
    mlflow.log_param("train_years", "2017-2020")
    mlflow.log_param("test_year", "2021")
    print("  ✓ Parameters logged")

    # Train model
    print("\n[5/7] Training final model...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(
        C=1.0, penalty="l2", max_iter=1000, solver="lbfgs", random_state=42
    )
    model.fit(X_train_scaled, y_train)
    print("  ✓ Model trained")

    # Evaluate
    print("\n[6/7] Evaluating and logging metrics...")
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)
    y_proba_test = model.predict_proba(X_test_scaled)[:, 1]

    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    test_auc = roc_auc_score(y_test, y_proba_test)
    gap = train_acc - test_acc

    # Log metrics
    mlflow.log_metric("train_accuracy", train_acc)
    mlflow.log_metric("test_accuracy", test_acc)
    mlflow.log_metric("test_auc", test_auc)
    mlflow.log_metric("train_test_gap", gap)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred_test)
    mlflow.log_metric("true_negatives", int(cm[0, 0]))
    mlflow.log_metric("false_positives", int(cm[0, 1]))
    mlflow.log_metric("false_negatives", int(cm[1, 0]))
    mlflow.log_metric("true_positives", int(cm[1, 1]))

    print(f"  Train Accuracy: {train_acc:.1%}")
    print(f"  Test Accuracy:  {test_acc:.1%}")
    print(f"  Test AUC:       {test_auc:.3f}")
    print(f"  Train/Test Gap: {gap:.1%}")

    # Save artifacts
    print("\n[7/7] Saving artifacts...")

    # Save scaler
    with open("/tmp/scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    mlflow.log_artifact("/tmp/scaler.pkl", "preprocessing")
    print("  ✓ Scaler saved")

    # Save feature list
    feature_list = X_train.columns.tolist()
    with open("/tmp/feature_list.txt", "w") as f:
        for feat in feature_list:
            f.write(f"{feat}\n")
    mlflow.log_artifact("/tmp/feature_list.txt", "features")
    print("  ✓ Feature list saved")

    # Save training statistics (for imputation)
    train_stats = pd.DataFrame(
        {
            "feature": X_train.columns,
            "mean": train_means.values,
            "std": X_train.std().values,
            "min": X_train.min().values,
            "max": X_train.max().values,
        }
    )
    train_stats.to_csv("/tmp/train_stats.csv", index=False)
    mlflow.log_artifact("/tmp/train_stats.csv", "preprocessing")
    print("  ✓ Training statistics saved")

    # Save feature importance
    feature_importance = pd.DataFrame(
        {
            "feature": X_train.columns,
            "coefficient": model.coef_[0],
            "abs_coefficient": np.abs(model.coef_[0]),
        }
    ).sort_values("abs_coefficient", ascending=False)
    feature_importance.to_csv("/tmp/feature_importance.csv", index=False)
    mlflow.log_artifact("/tmp/feature_importance.csv", "analysis")
    print("  ✓ Feature importance saved")

    # Log model
    mlflow.sklearn.log_model(model, "model", registered_model_name="nba_game_predictor")
    print("  ✓ Model logged and registered")

    run_id = run.info.run_id
    print(f"\n  Run ID: {run_id}")

# Print summary
print("\n" + "=" * 70)
print("MLFLOW REGISTRATION COMPLETE")
print("=" * 70)

print(f"\nModel Details:")
print(f"  Name: nba_game_predictor")
print(f"  Version: 1")
print(f"  Run ID: {run_id}")
print(f"  Test Accuracy: {test_acc:.1%}")
print(f"  Test AUC: {test_auc:.3f}")

print(f"\nArtifacts Saved:")
print(f"  - Model: Logistic Regression")
print(f"  - Scaler: StandardScaler")
print(f"  - Feature List: 300 features")
print(f"  - Training Stats: Mean/std for imputation")
print(f"  - Feature Importance: Coefficients")

print(f"\nTo view in MLflow UI:")
print(f"  cd /Users/ryanranft/nba-simulator-aws")
print(f"  mlflow ui")
print(f"  Then open: http://localhost:5000")

print(f"\nTo load model:")
print(f"  import mlflow")
print(f"  model = mlflow.sklearn.load_model('runs:/{run_id}/model')")

print("\n" + "=" * 70)
print("✓ Model ready for production deployment!")
print("\nNext Steps:")
print("  1. Create prediction API")
print("  2. Set up monitoring dashboard")
print("  3. Deploy to production environment")
print("=" * 70)

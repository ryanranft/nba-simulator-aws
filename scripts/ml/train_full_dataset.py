#!/usr/bin/env python3
"""
Full Dataset Training: All 76,943 Records, All 2,936 Games

Purpose:
- Process complete dataset (not limited subset)
- Generate comprehensive panel features
- Train on temporal split (80% train, 20% test by date)
- Get realistic accuracy estimates
- Target: 70-85% accuracy on real holdout

Author: NBA Simulator AWS Project
Created: October 17, 2025
"""

import sys
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from datetime import datetime
import time
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
)
import pickle
import warnings

warnings.filterwarnings("ignore")

sys.path.insert(0, "/Users/ryanranft/nba-simulator-aws")
sys.path.insert(0, "/Users/ryanranft/nba-simulator-aws/docs/phases/phase_0")

from implement_rec_22 import PanelDataProcessingSystem

print("\n" + "=" * 80)
print("FULL DATASET TRAINING: 76,943 Records → 2,936 Games")
print("=" * 80)
print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

overall_start = time.time()

# ============================================================================
# STEP 1: Load All Data
# ============================================================================
print("STEP 1: Loading complete dataset...")
step_start = time.time()

df = pd.read_parquet("/tmp/recent_player_data.parquet")

print(f"✓ Loaded {len(df):,} records")
print(f"  Players: {df['athlete_id'].nunique():,}")
print(f"  Games: {df['game_id'].nunique():,}")
print(f"  Time: {time.time() - step_start:.1f}s")

# ============================================================================
# STEP 2: Create Panel Structure
# ============================================================================
print("\nSTEP 2: Creating panel structure...")
step_start = time.time()

df["player_id"] = df["athlete_id"]
df["game_date"] = pd.to_datetime(df["game_date"])

panel_system = PanelDataProcessingSystem()
panel_system.setup()
df_panel = panel_system.create_panel_index(df)

print(f"✓ Panel created: {df_panel.shape}")
print(f"  Time: {time.time() - step_start:.1f}s")

# ============================================================================
# STEP 3: Generate Comprehensive Panel Features
# ============================================================================
print("\nSTEP 3: Generating comprehensive panel features...")
step_start = time.time()

# More stats for better predictions
stats = ["points", "rebounds", "assists", "steals", "blocks", "turnovers", "minutes"]

print(f"  Generating lags (1, 2, 3, 5, 10 games)...")
df_panel = panel_system.generate_lags(df_panel, stats, [1, 2, 3, 5, 10])

print(f"  Generating rolling windows (3, 5, 10, 20 games)...")
df_panel = panel_system.generate_rolling_stats(
    df_panel, stats, [3, 5, 10, 20], ["mean", "std"]
)

print(f"  Generating cumulative stats...")
df_panel = panel_system.generate_cumulative_stats(df_panel, stats + ["games"])

lag_cols = [col for col in df_panel.columns if "_lag" in col]
rolling_cols = [col for col in df_panel.columns if "_rolling_" in col]
cumulative_cols = [col for col in df_panel.columns if "_cumulative" in col]

print(f"✓ Features generated:")
print(f"  Lag features: {len(lag_cols)}")
print(f"  Rolling features: {len(rolling_cols)}")
print(f"  Cumulative features: {len(cumulative_cols)}")
print(
    f"  Total: {len(lag_cols) + len(rolling_cols) + len(cumulative_cols)} panel features"
)
print(f"  Time: {time.time() - step_start:.1f}s")

# ============================================================================
# STEP 4: Create Game Outcomes (ALL GAMES)
# ============================================================================
print("\nSTEP 4: Creating game outcomes for ALL games...")
step_start = time.time()

df_flat = df_panel.reset_index()
game_outcomes = []

unique_games = df_flat["game_id"].unique()
print(f"  Processing {len(unique_games):,} games...")

for idx, game_id in enumerate(unique_games):
    if idx % 500 == 0:
        print(
            f"    Progress: {idx:,}/{len(unique_games):,} ({idx/len(unique_games)*100:.1f}%)"
        )

    game_data = df_flat[df_flat["game_id"] == game_id]
    teams = game_data["team_id"].unique()

    if len(teams) < 2:
        continue

    # Calculate team points
    home_team_id = teams[0]
    away_team_id = teams[1]

    home_points = game_data[game_data["team_id"] == home_team_id]["points"].sum()
    away_points = game_data[game_data["team_id"] == away_team_id]["points"].sum()

    game_outcomes.append(
        {
            "game_id": game_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_points": home_points,
            "away_points": away_points,
            "home_win": 1 if home_points > away_points else 0,
            "game_date": (
                game_data["game_date"].iloc[0]
                if "game_date" in game_data.columns
                else None
            ),
        }
    )

df_outcomes = pd.DataFrame(game_outcomes)

print(f"\n✓ Created {len(df_outcomes):,} game outcomes")
print(
    f"  Home wins: {df_outcomes['home_win'].sum()} ({df_outcomes['home_win'].mean():.1%})"
)
print(
    f"  Away wins: {(1-df_outcomes['home_win']).sum()} ({(1-df_outcomes['home_win']).mean():.1%})"
)
print(f"  Time: {time.time() - step_start:.1f}s")

# ============================================================================
# STEP 5: Aggregate to Game Level with Multiple Aggregation Functions
# ============================================================================
print("\nSTEP 5: Aggregating to game level (5 aggregations)...")
step_start = time.time()

panel_cols = [
    col
    for col in df_flat.columns
    if any(x in col for x in ["_lag", "_rolling_", "_cumulative"])
]

print(f"  Panel features: {len(panel_cols)}")
print(f"  Aggregations: mean, std, max, min, sum")
print(
    f"  Expected features per game: {len(panel_cols) * 2 * 5} (panel × 2 teams × 5 agg)"
)

game_features = []

for idx, game in df_outcomes.iterrows():
    if idx % 500 == 0:
        print(
            f"    Progress: {idx:,}/{len(df_outcomes):,} ({idx/len(df_outcomes)*100:.1f}%)"
        )

    game_id = game["game_id"]
    home_team_id = game["home_team_id"]
    away_team_id = game["away_team_id"]

    game_data = df_flat[df_flat["game_id"] == game_id]
    home_data = game_data[game_data["team_id"] == home_team_id]
    away_data = game_data[game_data["team_id"] == away_team_id]

    if len(home_data) == 0 or len(away_data) == 0:
        continue

    features = {"game_id": game_id}

    # Home team aggregations
    for col in panel_cols:
        if col in home_data.columns:
            features[f"home_{col}_mean"] = home_data[col].mean()
            features[f"home_{col}_std"] = home_data[col].std()
            features[f"home_{col}_max"] = home_data[col].max()
            features[f"home_{col}_min"] = home_data[col].min()
            features[f"home_{col}_sum"] = home_data[col].sum()

    # Away team aggregations
    for col in panel_cols:
        if col in away_data.columns:
            features[f"away_{col}_mean"] = away_data[col].mean()
            features[f"away_{col}_std"] = away_data[col].std()
            features[f"away_{col}_max"] = away_data[col].max()
            features[f"away_{col}_min"] = away_data[col].min()
            features[f"away_{col}_sum"] = away_data[col].sum()

    game_features.append(features)

X_games = pd.DataFrame(game_features)
df_final = pd.merge(df_outcomes, X_games, on="game_id", how="inner")

feature_cols = [col for col in df_final.columns if col.startswith(("home_", "away_"))]
df_final[feature_cols] = df_final[feature_cols].fillna(0)

print(f"\n✓ Aggregation complete:")
print(f"  Games: {len(df_final):,}")
print(f"  Features per game: {len(feature_cols):,}")
print(f"  Time: {time.time() - step_start:.1f}s")

# ============================================================================
# STEP 6: Temporal Train/Test Split
# ============================================================================
print("\nSTEP 6: Creating temporal train/test split...")
step_start = time.time()

# Sort by date
df_final = df_final.sort_values("game_date").reset_index(drop=True)

# 80/20 split by date
split_idx = int(len(df_final) * 0.8)
df_train = df_final.iloc[:split_idx]
df_test = df_final.iloc[split_idx:]

print(f"✓ Split created:")
print(f"  Train: {len(df_train):,} games (earliest)")
print(f"  Test: {len(df_test):,} games (most recent)")
print(
    f"  Train date range: {df_train['game_date'].min()} to {df_train['game_date'].max()}"
)
print(
    f"  Test date range: {df_test['game_date'].min()} to {df_test['game_date'].max()}"
)
print(f"  Time: {time.time() - step_start:.1f}s")

# ============================================================================
# STEP 7: Train Models with MLflow
# ============================================================================
print("\nSTEP 7: Training models with MLflow...")
step_start = time.time()

mlflow.set_experiment("full_dataset_training")

X_train = df_train[feature_cols]
X_test = df_test[feature_cols]
y_train = df_train["home_win"]
y_test = df_test["home_win"]

print(f"  Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000, random_state=42, class_weight="balanced"
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    ),
}

results = {}
best_acc = 0
best_model_name = None
best_model = None

for name, model in models.items():
    print(f"\n  Training {name}...")
    model_start = time.time()

    with mlflow.start_run(run_name=f"{name}_full_dataset"):
        # Train
        model.fit(X_train_scaled, y_train)
        train_time = time.time() - model_start

        # Predictions
        y_train_pred = model.predict(X_train_scaled)
        y_test_pred = model.predict(X_test_scaled)

        # Metrics
        train_acc = accuracy_score(y_train, y_train_pred)
        test_acc = accuracy_score(y_test, y_test_pred)

        # Probabilities
        if hasattr(model, "predict_proba"):
            y_train_proba = model.predict_proba(X_train_scaled)[:, 1]
            y_test_proba = model.predict_proba(X_test_scaled)[:, 1]
            train_auc = roc_auc_score(y_train, y_train_proba)
            test_auc = roc_auc_score(y_test, y_test_proba)
        else:
            train_auc = test_auc = 0.0

        # Confusion matrix
        cm = confusion_matrix(y_test, y_test_pred)

        # Log to MLflow
        mlflow.log_param("model_type", name)
        mlflow.log_param("n_features", len(feature_cols))
        mlflow.log_param("n_train", len(X_train))
        mlflow.log_param("n_test", len(X_test))
        mlflow.log_metric("train_accuracy", train_acc)
        mlflow.log_metric("test_accuracy", test_acc)
        mlflow.log_metric("train_auc", train_auc)
        mlflow.log_metric("test_auc", test_auc)
        mlflow.log_metric("train_time", train_time)

        # Log model
        mlflow.sklearn.log_model(model, "model")

        print(f"    Train accuracy: {train_acc:.1%}")
        print(f"    Test accuracy: {test_acc:.1%}")
        print(f"    Train AUC: {train_auc:.3f}")
        print(f"    Test AUC: {test_auc:.3f}")
        print(f"    Training time: {train_time:.1f}s")
        print(f"    Confusion matrix:")
        print(f"      TN={cm[0,0]}, FP={cm[0,1]}")
        print(f"      FN={cm[1,0]}, TP={cm[1,1]}")

        results[name] = {
            "model": model,
            "train_acc": train_acc,
            "test_acc": test_acc,
            "train_auc": train_auc,
            "test_auc": test_auc,
            "train_time": train_time,
            "confusion_matrix": cm,
        }

        if test_acc > best_acc:
            best_acc = test_acc
            best_model_name = name
            best_model = model

print(f"\n✓ Model training complete")
print(f"  Time: {time.time() - step_start:.1f}s")

# ============================================================================
# STEP 8: Save Models
# ============================================================================
print("\nSTEP 8: Saving models...")

# Save best model
with open("/tmp/full_dataset_best_model.pkl", "wb") as f:
    pickle.dump(best_model, f)

# Save scaler
with open("/tmp/full_dataset_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

# Save feature names
with open("/tmp/full_dataset_features.pkl", "wb") as f:
    pickle.dump(feature_cols, f)

print(f"✓ Saved:")
print(f"  Model: /tmp/full_dataset_best_model.pkl")
print(f"  Scaler: /tmp/full_dataset_scaler.pkl")
print(f"  Features: /tmp/full_dataset_features.pkl")

# ============================================================================
# FINAL REPORT
# ============================================================================
print("\n" + "=" * 80)
print("FULL DATASET TRAINING COMPLETE")
print("=" * 80)

total_time = time.time() - overall_start

print(f"\nDataset:")
print(f"  Total records: 76,943 player-games")
print(f"  Total games: {len(df_outcomes):,}")
print(f"  Train games: {len(df_train):,}")
print(f"  Test games: {len(df_test):,}")

print(f"\nFeatures:")
print(f"  Panel features: {len(panel_cols)}")
print(f"  Game-level features: {len(feature_cols):,}")

print(f"\nBest Model: {best_model_name}")
print(f"  Test Accuracy: {best_acc:.1%}")
print(f"  Test AUC: {results[best_model_name]['test_auc']:.3f}")

print(f"\nAll Models:")
for name, res in results.items():
    print(f"  {name}:")
    print(f"    Test Accuracy: {res['test_acc']:.1%}")
    print(f"    Test AUC: {res['test_auc']:.3f}")

print(f"\nTotal Execution Time: {total_time:.1f}s ({total_time/60:.1f} minutes)")

print("\n" + "=" * 80)
print("✅ TRAINING SUCCESSFUL")
print("=" * 80)

# Classification report
print("\nDetailed Classification Report (Best Model):")
print(
    classification_report(
        y_test,
        results[best_model_name]["model"].predict(X_test_scaled),
        target_names=["Away Win", "Home Win"],
    )
)

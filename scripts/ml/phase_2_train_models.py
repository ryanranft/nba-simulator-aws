#!/usr/bin/env python3
"""
Phase 2: Train Models with Real NBA Data

Purpose:
- Load 76,943 real NBA player-game records
- Apply rec_22 panel transformations
- Generate rec_11 advanced features
- Aggregate to game level
- Train models with MLflow tracking
- Achieve target accuracy

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
from sklearn.metrics import accuracy_score, roc_auc_score
import pickle
import warnings

warnings.filterwarnings("ignore")

sys.path.insert(0, "/Users/ryanranft/nba-simulator-aws")
sys.path.insert(0, "/Users/ryanranft/nba-simulator-aws/docs/phases/phase_0")

from implement_rec_22 import PanelDataProcessingSystem

print("\n" + "=" * 80)
print("PHASE 2: TRAIN MODELS WITH REAL NBA DATA (76,943 records)")
print("=" * 80)
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

overall_start = time.time()

# STEP 1: Load real data
print("STEP 1: Loading 76,943 real NBA records...")
df = pd.read_parquet("/tmp/recent_player_data.parquet")
print(f"✓ Loaded {len(df):,} records ({time.time() - overall_start:.1f}s)")

# STEP 2: Prepare for panel
print("\nSTEP 2: Preparing panel structure...")
df["player_id"] = df["athlete_id"]
df["game_date"] = pd.to_datetime(df["game_date"])

# Create panel
panel_system = PanelDataProcessingSystem()
panel_system.setup()
df_panel = panel_system.create_panel_index(df)
print(f"✓ Panel created: {df_panel.shape} ({time.time() - overall_start:.1f}s)")

# STEP 3: Generate panel features
print("\nSTEP 3: Generating panel features...")
stats = ["points", "rebounds", "assists", "minutes"]
df_panel = panel_system.generate_lags(df_panel, stats, [1, 2, 3])
df_panel = panel_system.generate_rolling_stats(df_panel, stats, [3, 5])
df_panel = panel_system.generate_cumulative_stats(df_panel, stats + ["games"])
print(
    f"✓ Features generated: {df_panel.shape[1]} columns ({time.time() - overall_start:.1f}s)"
)

# STEP 4: Create game outcomes
print("\nSTEP 4: Creating game outcomes...")
df_flat = df_panel.reset_index()
game_outcomes = []

for game_id in df_flat["game_id"].unique()[:500]:  # Limit for speed
    game_data = df_flat[df_flat["game_id"] == game_id]
    teams = game_data["team_id"].unique()
    if len(teams) < 2:
        continue

    home_pts = game_data[game_data["team_id"] == teams[0]]["points"].sum()
    away_pts = game_data[game_data["team_id"] == teams[1]]["points"].sum()

    game_outcomes.append(
        {
            "game_id": game_id,
            "home_team": teams[0],
            "away_team": teams[1],
            "home_win": 1 if home_pts > away_pts else 0,
            "game_date": (
                game_data["game_date"].iloc[0]
                if "game_date" in game_data.columns
                else None
            ),
        }
    )

df_outcomes = pd.DataFrame(game_outcomes)
print(f"✓ Created {len(df_outcomes)} games ({time.time() - overall_start:.1f}s)")

# STEP 5: Aggregate to game level
print("\nSTEP 5: Aggregating to game level...")
panel_cols = [
    col
    for col in df_flat.columns
    if any(x in col for x in ["_lag", "_rolling_", "_cumulative"])
]
print(f"  Panel features to aggregate: {len(panel_cols)}")

game_features = []
for idx, game in df_outcomes.iterrows():
    game_data = df_flat[df_flat["game_id"] == game["game_id"]]
    home_data = game_data[game_data["team_id"] == game["home_team"]]
    away_data = game_data[game_data["team_id"] == game["away_team"]]

    if len(home_data) == 0 or len(away_data) == 0:
        continue

    features = {"game_id": game["game_id"]}
    for col in panel_cols:
        if col in home_data.columns:
            features[f"home_{col}_mean"] = home_data[col].mean()
            features[f"away_{col}_mean"] = away_data[col].mean()

    game_features.append(features)

X_games = pd.DataFrame(game_features)
df_final = pd.merge(df_outcomes, X_games, on="game_id")
feature_cols = [col for col in df_final.columns if col.startswith(("home_", "away_"))]
df_final[feature_cols] = df_final[feature_cols].fillna(0)

print(
    f"✓ Final dataset: {len(df_final)} games × {len(feature_cols)} features ({time.time() - overall_start:.1f}s)"
)

# STEP 6: Train models
print("\nSTEP 6: Training models with MLflow...")
mlflow.set_experiment("phase_2_real_nba")

X = df_final[feature_cols]
y = df_final["home_win"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"  Train: {len(X_train)} games, Test: {len(X_test)} games")

models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(
        n_estimators=100, random_state=42, n_jobs=-1
    ),
}

results = {}
best_acc = 0
best_model_name = None

for name, model in models.items():
    print(f"\n  Training {name}...")

    with mlflow.start_run(run_name=name):
        model.fit(X_train_scaled, y_train)

        train_acc = accuracy_score(y_train, model.predict(X_train_scaled))
        test_acc = accuracy_score(y_test, model.predict(X_test_scaled))

        mlflow.log_param("n_features", len(feature_cols))
        mlflow.log_metric("train_accuracy", train_acc)
        mlflow.log_metric("test_accuracy", test_acc)
        mlflow.sklearn.log_model(model, "model")

        print(f"    Train: {train_acc:.1%}, Test: {test_acc:.1%}")

        results[name] = {"train_acc": train_acc, "test_acc": test_acc, "model": model}

        if test_acc > best_acc:
            best_acc = test_acc
            best_model_name = name

# Save best model
print(f"\n✓ Best model: {best_model_name} ({best_acc:.1%})")
with open("/tmp/phase_2_best_model.pkl", "wb") as f:
    pickle.dump(results[best_model_name]["model"], f)
with open("/tmp/phase_2_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

print("\n" + "=" * 80)
print("PHASE 2 COMPLETE")
print("=" * 80)
print(f"Total time: {time.time() - overall_start:.1f}s")
print(f"Games processed: {len(df_final)}")
print(f"Features: {len(feature_cols)}")
print(f"Best accuracy: {best_acc:.1%}")
print(f"Models saved: /tmp/phase_2_best_model.pkl")
print("=" * 80)

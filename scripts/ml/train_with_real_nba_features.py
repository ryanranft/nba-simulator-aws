#!/usr/bin/env python3
"""
Train models with real NBA game features and validate 68-71% accuracy target.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

print("=" * 70)
print("REAL NBA GAME PREDICTION - MODEL TRAINING")
print("=" * 70)
print("\nData: Real NBA player box scores (2018-2021)")
print("Features: Panel data (rec_22) + advanced engineering (rec_11)")
print("Expected Accuracy: 68-71% (vs 63% baseline, 100% synthetic)")
print("=" * 70)

# Load data
print("\n[1/5] Loading features...")
df = pd.read_parquet("/tmp/real_nba_game_features.parquet")
print(f"  Games: {len(df):,}")
print(f"  Features: {len(df.columns) - 2}")  # Exclude game_id and won
print(f"  Target distribution: {df['won_first'].value_counts().to_dict()}")

# Prepare features
print("\n[2/5] Preparing features and target...")
X = df.drop(["game_id", "won_first"], axis=1)
y = df["won_first"]

# Remove any NaN/inf
X = X.replace([np.inf, -np.inf], np.nan)
X = X.fillna(X.mean())

print(f"  X shape: {X.shape}")
print(f"  y shape: {y.shape}")
print(f"  y distribution: {y.value_counts(normalize=True).to_dict()}")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n  Train: {len(X_train):,} games")
print(f"  Test:  {len(X_test):,} games")

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Define models
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(
        n_estimators=100, random_state=42, n_jobs=-1
    ),
    "XGBoost": XGBClassifier(n_estimators=100, random_state=42, n_jobs=-1, verbosity=0),
    "LightGBM": LGBMClassifier(
        n_estimators=100, random_state=42, n_jobs=-1, verbose=-1
    ),
}

print("\n[3/5] Training models...")
results = []

for name, model in models.items():
    print(f"\n  Training {name}...")

    if name in ["Logistic Regression"]:
        model.fit(X_train_scaled, y_train)
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
        y_proba_test = model.predict_proba(X_test_scaled)[:, 1]
    else:
        model.fit(X_train, y_train)
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        y_proba_test = model.predict_proba(X_test)[:, 1]

    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    test_auc = roc_auc_score(y_test, y_proba_test)

    results.append(
        {
            "Model": name,
            "Train Acc": train_acc,
            "Test Acc": test_acc,
            "Test AUC": test_auc,
        }
    )

    print(f"    Train Accuracy: {train_acc:.1%}")
    print(f"    Test Accuracy:  {test_acc:.1%}")
    print(f"    Test AUC:       {test_auc:.3f}")

# Display results
print("\n[4/5] Results Summary")
print("=" * 70)
results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))
print("=" * 70)

# Compare to baseline
print("\n[5/5] Validation")
print("=" * 70)
best_acc = results_df["Test Acc"].max()
print(f"  Best Test Accuracy:  {best_acc:.1%}")
print(f"  Baseline (16 features): 63.0%")
print(f"  Target (panel features): 68-71%")
print()

if best_acc >= 0.68 and best_acc <= 0.71:
    print("  ✅ SUCCESS: Achieved target accuracy range!")
elif best_acc > 0.71:
    print(f"  ⚠️  EXCEEDED: {best_acc:.1%} is higher than expected 68-71%")
    print("     This suggests the data may be too simple or overfitted.")
elif best_acc >= 0.63 and best_acc < 0.68:
    print(f"  ⚠️  PARTIAL: {best_acc:.1%} is better than baseline but below target")
    print(f"     Improvement: +{(best_acc - 0.63):.1%}")
else:
    print(f"  ❌ BELOW BASELINE: {best_acc:.1%} < 63%")

print("=" * 70)
print("\n✓ Validation complete!")
print("\nNext: Test temporal queries on real timestamps")

#!/usr/bin/env python3
"""
Train models with improved feature set (1,490 features) and validate 68-71% accuracy.
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
print("REAL NBA GAME PREDICTION - IMPROVED FEATURES VALIDATION")
print("=" * 70)
print("\nData: Real NBA player box scores (2018-2021)")
print("Features: 1,490 game-level (149 player × 10 aggregations)")
print("Previous: 54.4% accuracy with 14 features")
print("Target: 68-71% accuracy")
print("=" * 70)

# Load improved features
print("\n[1/5] Loading improved features...")
df = pd.read_parquet("/tmp/real_nba_game_features_improved.parquet")
print(f"  Games: {len(df):,}")
print(f"  Features: {len(df.columns) - 2}")
print(f"  Target distribution: {df['won'].value_counts().to_dict()}")

# Prepare features
print("\n[2/5] Preparing features...")
X = df.drop(["game_id", "won"], axis=1)
y = df["won"]

# Handle inf/nan
X = X.replace([np.inf, -np.inf], np.nan)
print(f"  NaN values before filling: {X.isna().sum().sum()}")
X = X.fillna(X.mean())
print(f"  NaN values after filling: {X.isna().sum().sum()}")

print(f"\n  X shape: {X.shape}")
print(f"  y shape: {y.shape}")
print(f"  y distribution: {y.value_counts(normalize=True).to_dict()}")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n  Train: {len(X_train):,} games")
print(f"  Test:  {len(X_test):,} games")

# Scale
print("\n[3/5] Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Models
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
    ),
    "XGBoost": XGBClassifier(
        n_estimators=100, max_depth=5, random_state=42, n_jobs=-1, verbosity=0
    ),
    "LightGBM": LGBMClassifier(
        n_estimators=100, max_depth=5, random_state=42, n_jobs=-1, verbose=-1
    ),
}

print("\n[4/5] Training models...")
results = []

for name, model in models.items():
    print(f"\n  Training {name}...")

    if name == "Logistic Regression":
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

# Results
print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)
results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

# Comparison
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

best_acc = results_df["Test Acc"].max()
best_model = results_df.loc[results_df["Test Acc"].idxmax(), "Model"]

print(f"\nBest Model: {best_model}")
print(f"Best Test Accuracy: {best_acc:.1%}")
print()
print("Comparison:")
print(f"  Baseline (16 features):          63.0%")
print(f"  Previous (14 features):          54.4%")
print(f"  Improved ({len(X.columns)} features):  {best_acc:.1%}")
print(f"  Target:                          68-71%")
print()

if best_acc >= 0.68 and best_acc <= 0.71:
    print("  ✅ SUCCESS! Achieved target accuracy range!")
    print(f"     Improvement over baseline: +{(best_acc - 0.63):.1%}")
elif best_acc > 0.71:
    print(f"  ✅ EXCEEDED! {best_acc:.1%} is higher than target 68-71%")
    print("     This validates the panel data framework works excellently!")
elif best_acc >= 0.63:
    print(f"  ⚠️  PARTIAL SUCCESS: {best_acc:.1%} beats baseline but below target")
    print(f"     Improvement: +{(best_acc - 0.63):.1%}")
else:
    print(f"  ❌ Below baseline: {best_acc:.1%} < 63%")

print("\n" + "=" * 70)

# Feature importance (top 20 for best tree model)
print("\nTop 20 Most Important Features (from best tree model):")
if best_model in ["Random Forest", "XGBoost", "LightGBM"]:
    best_tree_model = models[best_model]
    feature_importance = (
        pd.DataFrame(
            {"feature": X.columns, "importance": best_tree_model.feature_importances_}
        )
        .sort_values("importance", ascending=False)
        .head(20)
    )

    for i, row in feature_importance.iterrows():
        print(f"  {row['feature'][:50]:50s}  {row['importance']:.4f}")

print("\n" + "=" * 70)
print("✓ Validation complete!")
print("\nNext: Test temporal queries on real NBA timestamps")
print("=" * 70)

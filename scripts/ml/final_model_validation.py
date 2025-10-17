#!/usr/bin/env python3
"""
Final Model Validation: Test enhanced model with contextual features.

Comparison:
- Baseline (16 features): 63.0% accuracy
- Clean features (1,330 features): 79.9% accuracy
- Selected features (300 features): 84.0% accuracy
- Enhanced features (318 features): ??? accuracy
"""

import pandas as pd
import numpy as np
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
print("FINAL MODEL VALIDATION")
print("=" * 70)
print("\nGoal: Validate enhanced model with contextual features")
print("Features: 300 player panel + 18 contextual = 318 total")
print("=" * 70)

# Load enhanced features
print("\n[1/5] Loading enhanced features...")
df = pd.read_parquet("/tmp/real_nba_game_features_enhanced.parquet")
print(f"  Total games: {len(df):,}")
print(f"  Total features: {len(df.columns) - 3}")  # -3 for game_id, won, year

# Temporal split
train_df = df[df["year"] <= 2020].copy()
test_df = df[df["year"] == 2021].copy()

X_train = train_df.drop(["game_id", "won", "year"], axis=1)
y_train = train_df["won"]
X_test = test_df.drop(["game_id", "won", "year"], axis=1)
y_test = test_df["won"]

# Clean data
X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_test = X_test.replace([np.inf, -np.inf], np.nan)
train_means = X_train.mean()
X_train = X_train.fillna(train_means)
X_test = X_test.fillna(train_means)

print(f"  Train: {X_train.shape}")
print(f"  Test: {X_test.shape}")

# Scale
print("\n[2/5] Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train final model
print("\n[3/5] Training final model...")
final_model = LogisticRegression(max_iter=1000, random_state=42)
final_model.fit(X_train_scaled, y_train)

# Evaluate
y_pred_train = final_model.predict(X_train_scaled)
y_pred_test = final_model.predict(X_test_scaled)
y_proba_test = final_model.predict_proba(X_test_scaled)[:, 1]

train_acc = accuracy_score(y_train, y_pred_train)
test_acc = accuracy_score(y_test, y_pred_test)
test_auc = roc_auc_score(y_test, y_proba_test)
gap = train_acc - test_acc

print(f"  Train Accuracy: {train_acc:.1%}")
print(f"  Test Accuracy:  {test_acc:.1%}")
print(f"  Test AUC:       {test_auc:.3f}")
print(f"  Train/Test Gap: {gap:.1%}")

# Detailed metrics
print("\n[4/5] Detailed performance metrics...")

print("\nConfusion Matrix:")
cm = confusion_matrix(y_test, y_pred_test)
print(f"  True Negatives:  {cm[0,0]:,} (correctly predicted losses)")
print(f"  False Positives: {cm[0,1]:,} (predicted win, actually lost)")
print(f"  False Negatives: {cm[1,0]:,} (predicted loss, actually won)")
print(f"  True Positives:  {cm[1,1]:,} (correctly predicted wins)")

print("\nClassification Report:")
print(classification_report(y_test, y_pred_test, target_names=["Loss", "Win"]))

# Feature importance for contextual features
print("\n[5/5] Contextual feature importance...")
feature_importance = pd.DataFrame(
    {"feature": X_train.columns, "importance": np.abs(final_model.coef_[0])}
).sort_values("importance", ascending=False)

# Find contextual features
contextual_features = [
    f
    for f in feature_importance["feature"]
    if any(
        keyword in f
        for keyword in [
            "win_pct",
            "wins_prior",
            "losses_prior",
            "games_prior",
            "streak",
            "days_rest",
            "back_to_back",
            "matchup_rest",
            "matchup_streak",
            "matchup_win_pct",
            "matchup_wins",
        ]
    )
]

print("\nTop 10 Contextual Features:")
contextual_importance = feature_importance[
    feature_importance["feature"].isin(contextual_features)
].head(10)
for i, row in contextual_importance.iterrows():
    rank = feature_importance.index.get_loc(i) + 1
    print(f"  {rank:3d}. {row['feature']:40s}  {row['importance']:.4f}")

# Overall importance
print("\nTop 15 Overall Features (all types):")
for i, row in feature_importance.head(15).iterrows():
    is_contextual = "(contextual)" if row["feature"] in contextual_features else ""
    print(
        f"  {i+1:2d}. {row['feature'][:45]:45s}  {row['importance']:.4f} {is_contextual}"
    )

# Results comparison
print("\n" + "=" * 70)
print("PROGRESSION SUMMARY")
print("=" * 70)

results = pd.DataFrame(
    [
        {
            "Model": "Baseline (team stats)",
            "Features": 16,
            "Test Acc": 0.630,
            "Gap": "—",
            "Status": "Initial",
        },
        {
            "Model": "With data leakage ❌",
            "Features": 1490,
            "Test Acc": 0.993,
            "Gap": "—",
            "Status": "Invalid",
        },
        {
            "Model": "Clean (no leakage)",
            "Features": 1330,
            "Test Acc": 0.799,
            "Gap": "19.4%",
            "Status": "Fixed",
        },
        {
            "Model": "Feature selection",
            "Features": 300,
            "Test Acc": 0.840,
            "Gap": "7.6%",
            "Status": "Improved",
        },
        {
            "Model": "Cross-validation",
            "Features": 300,
            "Test Acc": 0.849,
            "Gap": "7.5%",
            "Status": "Validated",
        },
        {
            "Model": "Hyperparameter tuning",
            "Features": 300,
            "Test Acc": 0.840,
            "Gap": "7.6%",
            "Status": "Optimal",
        },
        {
            "Model": "With contextual features",
            "Features": 318,
            "Test Acc": test_acc,
            "Gap": f"{gap:.1%}",
            "Status": "Final",
        },
    ]
)

print(results.to_string(index=False))

# Final verdict
print("\n" + "=" * 70)
print("FINAL VERDICT")
print("=" * 70)

print(f"\nFinal Model Performance:")
print(f"  Test Accuracy: {test_acc:.1%}")
print(f"  Test AUC: {test_auc:.3f}")
print(f"  Train/Test Gap: {gap:.1%}")
print(f"  Total Features: {len(X_train.columns)}")

# Compare to previous best
previous_best_acc = 0.840
previous_best_gap = 0.076

if test_acc > previous_best_acc:
    improvement = (test_acc - previous_best_acc) * 100
    print(f"\n  ✅ Test accuracy improved by {improvement:.1f}pp")
elif test_acc >= previous_best_acc * 0.99:  # Within 1%
    print(
        f"\n  ✅ Test accuracy maintained ({test_acc:.1%} vs {previous_best_acc:.1%})"
    )
else:
    decrease = (previous_best_acc - test_acc) * 100
    print(f"\n  ⚠️  Test accuracy decreased by {decrease:.1f}pp")

if gap < previous_best_gap:
    gap_improvement = (previous_best_gap - gap) * 100
    print(f"  ✅ Train/test gap improved by {gap_improvement:.1f}pp")
elif gap <= previous_best_gap * 1.1:  # Within 10%
    print(f"  ✅ Train/test gap maintained ({gap:.1%} vs {previous_best_gap:.1%})")
else:
    print(f"  ⚠️  Train/test gap increased")

# Summary
print("\n" + "=" * 70)
print("IMPROVEMENTS SUMMARY")
print("=" * 70)

print(f"\nFrom Baseline (63.0%) to Final Model ({test_acc:.1%}):")
print(f"  Absolute improvement: +{(test_acc - 0.630) * 100:.1f} percentage points")
print(f"  Relative improvement: +{((test_acc - 0.630) / 0.630) * 100:.1f}%")

print(f"\nFrom Data Leakage Fix (79.9%) to Final Model ({test_acc:.1%}):")
print(f"  Improvement: +{(test_acc - 0.799) * 100:.1f} percentage points")

print(f"\nKey Milestones:")
print(f"  1. ✅ Fixed data leakage: 99.3% → 79.9%")
print(f"  2. ✅ Feature selection: 79.9% → 84.0% (+4.1pp)")
print(f"  3. ✅ Cross-validation: Confirmed 84.9% ± 0.9%")
print(f"  4. ✅ Hyperparameter tuning: Already optimal")
print(
    f"  5. {'✅' if test_acc >= previous_best_acc * 0.99 else '⚠️'} Contextual features: 84.0% → {test_acc:.1%} ({'+' if test_acc >= previous_best_acc else ''}{(test_acc - previous_best_acc) * 100:.1f}pp)"
)

print("\n" + "=" * 70)
print("✓ Final model validation complete!")
print("\nRecommendation: Model is ready for documentation and deployment")
print("=" * 70)

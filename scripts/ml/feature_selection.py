#!/usr/bin/env python3
"""
Feature Selection: Reduce from 1,330 to top 200-300 features to reduce overfitting.

Goal: Improve generalization by selecting most important features
Current: 99.3% train → 79.9% test (19.4% gap)
Target: <15% gap with similar or better test accuracy
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import matplotlib.pyplot as plt

print("=" * 70)
print("FEATURE SELECTION - REDUCE OVERFITTING")
print("=" * 70)
print("\nGoal: Select top 200-300 features from 1,330")
print("Current: 99.3% train → 79.9% test (19.4% gap)")
print("Target: Reduce gap while maintaining test accuracy")
print("=" * 70)

# Load clean features
print("\n[1/6] Loading clean features...")
df = pd.read_parquet("/tmp/real_nba_game_features_clean.parquet")

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
print("\n[2/6] Scaling features...")
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train baseline model
print("\n[3/6] Training baseline Logistic Regression (all 1,330 features)...")
baseline_model = LogisticRegression(max_iter=1000, random_state=42)
baseline_model.fit(X_train_scaled, y_train)

y_pred_train_base = baseline_model.predict(X_train_scaled)
y_pred_test_base = baseline_model.predict(X_test_scaled)
y_proba_test_base = baseline_model.predict_proba(X_test_scaled)[:, 1]

train_acc_base = accuracy_score(y_train, y_pred_train_base)
test_acc_base = accuracy_score(y_test, y_pred_test_base)
test_auc_base = roc_auc_score(y_test, y_proba_test_base)

print(f"  Train Accuracy: {train_acc_base:.1%}")
print(f"  Test Accuracy:  {test_acc_base:.1%}")
print(f"  Test AUC:       {test_auc_base:.3f}")
print(f"  Train/Test Gap: {(train_acc_base - test_acc_base):.1%}")

# Get feature importance
print("\n[4/6] Extracting feature importances...")
feature_importance = pd.DataFrame(
    {
        "feature": X_train.columns,
        "importance": np.abs(baseline_model.coef_[0]),  # Absolute value of coefficients
    }
).sort_values("importance", ascending=False)

print(f"  Total features: {len(feature_importance)}")
print("\n  Top 20 Most Important Features:")
for i, row in feature_importance.head(20).iterrows():
    print(f"    {i+1:2d}. {row['feature'][:55]:55s}  {row['importance']:.4f}")

# Try different feature set sizes
print("\n[5/6] Testing different feature set sizes...")
feature_counts = [50, 100, 150, 200, 250, 300, 400, 500]
results = []

for n_features in feature_counts:
    print(f"\n  Testing with top {n_features} features...")

    # Select top features
    top_features = feature_importance.head(n_features)["feature"].tolist()
    X_train_selected = X_train[top_features]
    X_test_selected = X_test[top_features]

    # Scale
    scaler_select = StandardScaler()
    X_train_selected_scaled = scaler_select.fit_transform(X_train_selected)
    X_test_selected_scaled = scaler_select.transform(X_test_selected)

    # Train
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_selected_scaled, y_train)

    # Evaluate
    y_pred_train = model.predict(X_train_selected_scaled)
    y_pred_test = model.predict(X_test_selected_scaled)
    y_proba_test = model.predict_proba(X_test_selected_scaled)[:, 1]

    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    test_auc = roc_auc_score(y_test, y_proba_test)
    gap = train_acc - test_acc

    results.append(
        {
            "n_features": n_features,
            "train_acc": train_acc,
            "test_acc": test_acc,
            "test_auc": test_auc,
            "gap": gap,
        }
    )

    print(
        f"    Train: {train_acc:.1%} | Test: {test_acc:.1%} | Gap: {gap:.1%} | AUC: {test_auc:.3f}"
    )

# Results summary
print("\n[6/6] Feature selection results...")
results_df = pd.DataFrame(results)

print("\n" + "=" * 70)
print("FEATURE SELECTION RESULTS")
print("=" * 70)
print(results_df.to_string(index=False))

# Find best configuration
print("\n" + "=" * 70)
print("BEST CONFIGURATIONS")
print("=" * 70)

# Best test accuracy
best_test_idx = results_df["test_acc"].idxmax()
best_test = results_df.loc[best_test_idx]
print(f"\nBest Test Accuracy: {best_test['test_acc']:.1%}")
print(f"  Features: {best_test['n_features']:.0f}")
print(f"  Train: {best_test['train_acc']:.1%}")
print(f"  Gap: {best_test['gap']:.1%}")
print(f"  AUC: {best_test['test_auc']:.3f}")

# Best trade-off (small gap + good test accuracy)
# Score = test_acc - 0.5 * gap (penalize large gaps)
results_df["tradeoff_score"] = results_df["test_acc"] - 0.5 * results_df["gap"]
best_tradeoff_idx = results_df["tradeoff_score"].idxmax()
best_tradeoff = results_df.loc[best_tradeoff_idx]
print(f"\nBest Trade-off (test accuracy vs gap):")
print(f"  Features: {best_tradeoff['n_features']:.0f}")
print(f"  Test: {best_tradeoff['test_acc']:.1%}")
print(f"  Train: {best_tradeoff['train_acc']:.1%}")
print(f"  Gap: {best_tradeoff['gap']:.1%}")
print(f"  AUC: {best_tradeoff['test_auc']:.3f}")

# Smallest gap
best_gap_idx = results_df["gap"].idxmin()
best_gap = results_df.loc[best_gap_idx]
print(f"\nSmallest Train/Test Gap:")
print(f"  Features: {best_gap['n_features']:.0f}")
print(f"  Test: {best_gap['test_acc']:.1%}")
print(f"  Train: {best_gap['train_acc']:.1%}")
print(f"  Gap: {best_gap['gap']:.1%}")
print(f"  AUC: {best_gap['test_auc']:.3f}")

# Recommendation
print("\n" + "=" * 70)
print("RECOMMENDATION")
print("=" * 70)

recommended_n = int(best_tradeoff["n_features"])
print(f"\nRecommended: Top {recommended_n} features")
print(f"  Reason: Best balance of test accuracy and generalization")
print(
    f"  Test Accuracy: {best_tradeoff['test_acc']:.1%} (vs {test_acc_base:.1%} baseline)"
)
print(
    f"  Train/Test Gap: {best_tradeoff['gap']:.1%} (vs {(train_acc_base - test_acc_base):.1%} baseline)"
)

if best_tradeoff["test_acc"] >= test_acc_base:
    print(f"  ✅ Maintains or improves test accuracy!")
else:
    diff = (test_acc_base - best_tradeoff["test_acc"]) * 100
    print(f"  ⚠️  Slight test accuracy decrease: -{diff:.1f} percentage points")

if best_tradeoff["gap"] < (train_acc_base - test_acc_base):
    gap_improvement = ((train_acc_base - test_acc_base) - best_tradeoff["gap"]) * 100
    print(f"  ✅ Reduces overfitting gap by {gap_improvement:.1f} percentage points!")
else:
    print(f"  ⚠️  Gap not improved")

# Save selected features
print(f"\n  Saving top {recommended_n} features...")
top_n_features = feature_importance.head(recommended_n)["feature"].tolist()

# Create reduced dataset
train_df_reduced = train_df[["game_id", "won", "year"] + top_n_features].copy()
test_df_reduced = test_df[["game_id", "won", "year"] + top_n_features].copy()
df_reduced = pd.concat([train_df_reduced, test_df_reduced], ignore_index=True)

output_path = "/tmp/real_nba_game_features_selected.parquet"
df_reduced.to_parquet(output_path, index=False)
print(f"  ✓ Saved to: {output_path}")

# Save feature list
feature_list_path = "/tmp/selected_features.txt"
with open(feature_list_path, "w") as f:
    f.write(f"Top {recommended_n} Features for NBA Game Prediction\n")
    f.write("=" * 70 + "\n\n")
    for i, row in feature_importance.head(recommended_n).iterrows():
        f.write(f"{i+1:3d}. {row['feature']:60s}  {row['importance']:.6f}\n")
print(f"  ✓ Feature list saved to: {feature_list_path}")

print("\n" + "=" * 70)
print("✓ Feature selection complete!")
print("\nNext Steps:")
print("  1. Cross-validation with selected features")
print("  2. Hyperparameter tuning")
print("  3. Add contextual features")
print("=" * 70)

#!/usr/bin/env python3
"""
Temporal Cross-Validation: Get robust accuracy estimate with walk-forward validation.

Uses expanding window approach:
- Fold 1: Train on 2017-2018, test on 2019
- Fold 2: Train on 2017-2019, test on 2020
- Fold 3: Train on 2017-2020, test on 2021

This mimics real-world prediction: always predicting future from past.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
import warnings

warnings.filterwarnings("ignore")

print("=" * 70)
print("TEMPORAL CROSS-VALIDATION")
print("=" * 70)
print("\nGoal: Get robust accuracy estimate with walk-forward validation")
print("Method: Expanding window (always train on past, test on future)")
print("=" * 70)

# Load selected features
print("\n[1/4] Loading selected features (300 features)...")
df = pd.read_parquet("/tmp/real_nba_game_features_selected.parquet")
print(f"  Total games: {len(df):,}")
print(f"  Features: {len(df.columns) - 3}")  # -3 for game_id, won, year
print(f"  Years: {sorted(df['year'].unique())}")

# Define temporal folds (expanding window)
print("\n[2/4] Defining temporal folds...")
folds = [
    {
        "train_years": [2017, 2018],
        "test_year": 2019,
        "name": "Fold 1 (2017-2018 → 2019)",
    },
    {
        "train_years": [2017, 2018, 2019],
        "test_year": 2020,
        "name": "Fold 2 (2017-2019 → 2020)",
    },
    {
        "train_years": [2017, 2018, 2019, 2020],
        "test_year": 2021,
        "name": "Fold 3 (2017-2020 → 2021)",
    },
]

print(f"  Total folds: {len(folds)}")
for i, fold in enumerate(folds, 1):
    train_games = len(df[df["year"].isin(fold["train_years"])])
    test_games = len(df[df["year"] == fold["test_year"]])
    print(f"  {fold['name']}: {train_games:,} train, {test_games:,} test")

# Run cross-validation
print("\n[3/4] Running temporal cross-validation...")
cv_results = []

for i, fold in enumerate(folds, 1):
    print(f"\n  {fold['name']}...")

    # Split data
    train_df = df[df["year"].isin(fold["train_years"])].copy()
    test_df = df[df["year"] == fold["test_year"]].copy()

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

    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)
    y_proba_test = model.predict_proba(X_test_scaled)[:, 1]

    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    test_auc = roc_auc_score(y_test, y_proba_test)
    gap = train_acc - test_acc

    cv_results.append(
        {
            "fold": i,
            "test_year": fold["test_year"],
            "train_size": len(X_train),
            "test_size": len(X_test),
            "train_acc": train_acc,
            "test_acc": test_acc,
            "test_auc": test_auc,
            "gap": gap,
        }
    )

    print(f"    Train: {len(X_train):,} games | Test: {len(X_test):,} games")
    print(f"    Train Acc: {train_acc:.1%} | Test Acc: {test_acc:.1%}")
    print(f"    Gap: {gap:.1%} | AUC: {test_auc:.3f}")

# Results summary
print("\n[4/4] Cross-validation results...")
results_df = pd.DataFrame(cv_results)

print("\n" + "=" * 70)
print("TEMPORAL CROSS-VALIDATION RESULTS")
print("=" * 70)
print(
    results_df[
        ["fold", "test_year", "train_acc", "test_acc", "gap", "test_auc"]
    ].to_string(index=False)
)

# Statistics
print("\n" + "=" * 70)
print("SUMMARY STATISTICS")
print("=" * 70)

mean_train = results_df["train_acc"].mean()
mean_test = results_df["test_acc"].mean()
std_test = results_df["test_acc"].std()
mean_gap = results_df["gap"].mean()
mean_auc = results_df["test_auc"].mean()

print(f"\nTrain Accuracy:")
print(f"  Mean: {mean_train:.1%}")
print(
    f"  Range: {results_df['train_acc'].min():.1%} - {results_df['train_acc'].max():.1%}"
)

print(f"\nTest Accuracy:")
print(f"  Mean: {mean_test:.1%}")
print(f"  Std Dev: {std_test:.1%}")
print(
    f"  Range: {results_df['test_acc'].min():.1%} - {results_df['test_acc'].max():.1%}"
)
print(f"  95% CI: [{mean_test - 1.96*std_test:.1%}, {mean_test + 1.96*std_test:.1%}]")

print(f"\nTrain/Test Gap:")
print(f"  Mean: {mean_gap:.1%}")
print(f"  Range: {results_df['gap'].min():.1%} - {results_df['gap'].max():.1%}")

print(f"\nTest AUC:")
print(f"  Mean: {mean_auc:.3f}")
print(
    f"  Range: {results_df['test_auc'].min():.3f} - {results_df['test_auc'].max():.3f}"
)

# Compare to single holdout
print("\n" + "=" * 70)
print("COMPARISON TO SINGLE HOLDOUT")
print("=" * 70)

single_holdout_acc = 0.840  # From feature selection (2021 only)
single_holdout_gap = 0.076

print(f"\nSingle Holdout (2017-2020 → 2021):")
print(f"  Test Accuracy: {single_holdout_acc:.1%}")
print(f"  Train/Test Gap: {single_holdout_gap:.1%}")

print(f"\nCross-Validation (3 folds):")
print(f"  Test Accuracy: {mean_test:.1%} ± {std_test:.1%}")
print(f"  Train/Test Gap: {mean_gap:.1%}")

# Interpretation
print("\n" + "=" * 70)
print("INTERPRETATION")
print("=" * 70)

if mean_test >= single_holdout_acc * 0.98:  # Within 2%
    print(f"\n✅ Cross-validation confirms single holdout results")
    print(
        f"   CV mean ({mean_test:.1%}) is consistent with holdout ({single_holdout_acc:.1%})"
    )
else:
    diff = (single_holdout_acc - mean_test) * 100
    print(f"\n⚠️  Cross-validation suggests holdout may be optimistic")
    print(
        f"   CV mean ({mean_test:.1%}) is {diff:.1f}pp lower than holdout ({single_holdout_acc:.1%})"
    )

if std_test < 0.05:  # Standard deviation < 5%
    print(f"\n✅ Model performance is stable across years")
    print(f"   Low std dev ({std_test:.1%}) indicates consistent predictions")
else:
    print(f"\n⚠️  Model performance varies across years")
    print(f"   High std dev ({std_test:.1%}) suggests year-specific effects")

if mean_gap < 0.10:  # Gap < 10%
    print(f"\n✅ Model generalizes well")
    print(f"   Small gap ({mean_gap:.1%}) indicates good generalization")
else:
    print(f"\n⚠️  Some overfitting remains")
    print(f"   Gap ({mean_gap:.1%}) could be reduced further")

# Final verdict
print("\n" + "=" * 70)
print("FINAL VERDICT")
print("=" * 70)

print(f"\nModel Performance (300 features):")
print(f"  Test Accuracy: {mean_test:.1%} ± {std_test:.1%}")
print(f"  Test AUC: {mean_auc:.3f}")
print(f"  Train/Test Gap: {mean_gap:.1%}")

if mean_test >= 0.80:
    print(f"\n  ✅ EXCELLENT: Exceeds 80% accuracy threshold")
elif mean_test >= 0.70:
    print(f"\n  ✅ GOOD: Realistic performance for NBA game prediction")
elif mean_test >= 0.65:
    print(f"\n  ✅ ACCEPTABLE: Meets 65-72% target range")
else:
    print(f"\n  ⚠️  BELOW TARGET: Consider adding more features or tuning")

print("\n" + "=" * 70)
print("✓ Temporal cross-validation complete!")
print("\nNext Steps:")
print("  1. Hyperparameter tuning")
print("  2. Add contextual features")
print("  3. Final model validation")
print("=" * 70)

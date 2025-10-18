#!/usr/bin/env python3
"""
NBA Hyperparameter Optimization Example
=========================================

Demonstrates hyperparameter tuning for NBA win prediction model using:
- Grid Search with time series cross-validation
- Random Search for faster exploration
- Bayesian Optimization for efficient search

Implementation: MCP Book Recommendation #14
Framework: scripts/ml/hyperparameter_tuning.py
"""

import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score

from scripts.ml.hyperparameter_tuning import HyperparameterOptimizer


def load_nba_panel_data():
    """Load NBA panel data for win prediction."""
    print("Loading NBA panel data...")

    # Load your panel data here
    # For demo, create synthetic data
    np.random.seed(42)
    n_games = 5000

    data = pd.DataFrame(
        {
            "game_date": pd.date_range("2020-01-01", periods=n_games, freq="D"),
            "team_points_last_5": np.random.uniform(90, 120, n_games),
            "opponent_points_last_5": np.random.uniform(90, 120, n_games),
            "win_pct_last_10": np.random.uniform(0.2, 0.8, n_games),
            "home_away": np.random.choice([0, 1], n_games),
            "rest_days": np.random.choice([0, 1, 2, 3], n_games),
            "opponent_strength": np.random.uniform(0.3, 0.7, n_games),
            "fatigue_index": np.random.uniform(0, 1, n_games),
            "momentum_score": np.random.uniform(-2, 2, n_games),
            "win": np.random.choice([0, 1], n_games),
        }
    )

    # Sort by date for time series validation
    data = data.sort_values("game_date").reset_index(drop=True)

    return data


def example_grid_search():
    """Example 1: Grid Search with Time Series CV"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Grid Search for Random Forest Win Prediction")
    print("=" * 80)

    # Load data
    data = load_nba_panel_data()

    # Prepare features and target
    feature_cols = [col for col in data.columns if col not in ["game_date", "win"]]
    X_train = data[feature_cols].iloc[:4000]
    y_train = data["win"].iloc[:4000]
    X_test = data[feature_cols].iloc[4000:]
    y_test = data["win"].iloc[4000:]

    # Initialize optimizer with time series CV (critical for NBA data)
    optimizer = HyperparameterOptimizer(
        model_type="random_forest",
        X_train=X_train,
        y_train=y_train,
        cv_strategy="time_series",  # Respect temporal ordering
        n_splits=5,
        scoring="roc_auc",
    )

    # Define parameter grid
    param_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [10, 20, 30],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2"],
    }

    print(
        f"\nSearching {np.prod([len(v) for v in param_grid.values()])} parameter combinations..."
    )

    # Run grid search
    result = optimizer.grid_search(param_grid)

    # Display results
    print(f"\n✅ Best Parameters: {result.best_params}")
    print(f"✅ Best CV Score: {result.best_score:.4f}")
    print(f"✅ Training Time: {result.training_time:.2f}s")

    # Test on holdout set
    y_pred_proba = result.best_model.predict_proba(X_test)[:, 1]
    test_auc = roc_auc_score(y_test, y_pred_proba)
    print(f"✅ Test AUC: {test_auc:.4f}")

    # Show top parameter combinations
    print("\nTop 5 parameter combinations:")
    cv_results = pd.DataFrame(result.cv_results)
    top_5 = cv_results.nlargest(5, "mean_test_score")[
        ["params", "mean_test_score", "std_test_score"]
    ]
    for idx, row in top_5.iterrows():
        print(
            f"  {row['mean_test_score']:.4f} ± {row['std_test_score']:.4f}: {row['params']}"
        )

    return result


def example_random_search():
    """Example 2: Random Search for faster exploration"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Random Search for Gradient Boosting")
    print("=" * 80)

    # Load data
    data = load_nba_panel_data()
    feature_cols = [col for col in data.columns if col not in ["game_date", "win"]]
    X_train = data[feature_cols].iloc[:4000]
    y_train = data["win"].iloc[:4000]
    X_test = data[feature_cols].iloc[4000:]
    y_test = data["win"].iloc[4000:]

    # Initialize optimizer
    optimizer = HyperparameterOptimizer(
        model_type="gradient_boosting",
        X_train=X_train,
        y_train=y_train,
        cv_strategy="time_series",
        n_splits=5,
        scoring="roc_auc",
    )

    # Define parameter distributions
    param_distributions = {
        "n_estimators": [50, 100, 150, 200, 250],
        "learning_rate": [0.01, 0.05, 0.1, 0.15, 0.2],
        "max_depth": [3, 4, 5, 6, 7],
        "min_samples_split": [2, 4, 6, 8, 10],
        "min_samples_leaf": [1, 2, 3, 4],
        "subsample": [0.7, 0.8, 0.9, 1.0],
    }

    # Run random search (100 iterations)
    print(f"\nSearching 100 random parameter combinations...")

    result = optimizer.random_search(
        param_distributions=param_distributions, n_iter=100
    )

    # Display results
    print(f"\n✅ Best Parameters: {result.best_params}")
    print(f"✅ Best CV Score: {result.best_score:.4f}")
    print(f"✅ Training Time: {result.training_time:.2f}s")

    # Test performance
    y_pred_proba = result.best_model.predict_proba(X_test)[:, 1]
    test_auc = roc_auc_score(y_test, y_pred_proba)
    test_acc = accuracy_score(y_test, result.best_model.predict(X_test))
    print(f"✅ Test AUC: {test_auc:.4f}")
    print(f"✅ Test Accuracy: {test_acc:.4f}")

    return result


def example_bayesian_optimization():
    """Example 3: Bayesian Optimization for efficient search"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Bayesian Optimization")
    print("=" * 80)

    # Load data
    data = load_nba_panel_data()
    feature_cols = [col for col in data.columns if col not in ["game_date", "win"]]
    X_train = data[feature_cols].iloc[:4000]
    y_train = data["win"].iloc[:4000]

    # Initialize optimizer
    optimizer = HyperparameterOptimizer(
        model_type="random_forest",
        X_train=X_train,
        y_train=y_train,
        cv_strategy="time_series",
        n_splits=5,
        scoring="roc_auc",
    )

    # Define search space
    search_space = {
        "n_estimators": (50, 300),
        "max_depth": (5, 30),
        "min_samples_split": (2, 20),
        "min_samples_leaf": (1, 10),
    }

    print(f"\nRunning Bayesian optimization (50 iterations)...")

    result = optimizer.bayesian_optimization(search_space=search_space, n_iter=50)

    # Display results
    print(f"\n✅ Best Parameters: {result.best_params}")
    print(f"✅ Best CV Score: {result.best_score:.4f}")
    print(f"✅ Training Time: {result.training_time:.2f}s")

    print("\nOptimization progression (first 10 iterations):")
    for i in range(min(10, len(result.cv_results["mean_test_score"]))):
        score = result.cv_results["mean_test_score"][i]
        params = result.cv_results["params"][i]
        print(f"  Iteration {i+1}: {score:.4f} - {params}")

    return result


def compare_methods():
    """Example 4: Compare all three methods"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Comparing Hyperparameter Tuning Methods")
    print("=" * 80)

    # Load data
    data = load_nba_panel_data()
    feature_cols = [col for col in data.columns if col not in ["game_date", "win"]]
    X_train = data[feature_cols].iloc[:4000]
    y_train = data["win"].iloc[:4000]
    X_test = data[feature_cols].iloc[4000:]
    y_test = data["win"].iloc[4000:]

    results = {}

    # Grid Search (small grid for comparison)
    print("\n1. Grid Search...")
    optimizer = HyperparameterOptimizer(
        model_type="random_forest",
        X_train=X_train,
        y_train=y_train,
        cv_strategy="time_series",
        n_splits=5,
        scoring="roc_auc",
    )

    grid_result = optimizer.grid_search(
        {"n_estimators": [100, 200], "max_depth": [10, 20], "min_samples_split": [2, 5]}
    )

    results["Grid Search"] = {
        "best_score": grid_result.best_score,
        "training_time": grid_result.training_time,
        "test_auc": roc_auc_score(
            y_test, grid_result.best_model.predict_proba(X_test)[:, 1]
        ),
    }

    # Random Search
    print("\n2. Random Search...")
    random_result = optimizer.random_search(
        param_distributions={
            "n_estimators": [50, 100, 150, 200],
            "max_depth": [5, 10, 15, 20, 25],
            "min_samples_split": [2, 5, 10],
        },
        n_iter=20,
    )

    results["Random Search"] = {
        "best_score": random_result.best_score,
        "training_time": random_result.training_time,
        "test_auc": roc_auc_score(
            y_test, random_result.best_model.predict_proba(X_test)[:, 1]
        ),
    }

    # Bayesian Optimization
    print("\n3. Bayesian Optimization...")
    bayes_result = optimizer.bayesian_optimization(
        search_space={
            "n_estimators": (50, 200),
            "max_depth": (5, 25),
            "min_samples_split": (2, 10),
        },
        n_iter=20,
    )

    results["Bayesian Optimization"] = {
        "best_score": bayes_result.best_score,
        "training_time": bayes_result.training_time,
        "test_auc": roc_auc_score(
            y_test, bayes_result.best_model.predict_proba(X_test)[:, 1]
        ),
    }

    # Display comparison
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)

    comparison_df = pd.DataFrame(results).T
    print(comparison_df.to_string())

    print("\n📊 Summary:")
    best_method = comparison_df["test_auc"].idxmax()
    fastest_method = comparison_df["training_time"].idxmin()
    print(
        f"  Best Test AUC: {best_method} ({comparison_df.loc[best_method, 'test_auc']:.4f})"
    )
    print(
        f"  Fastest Method: {fastest_method} ({comparison_df.loc[fastest_method, 'training_time']:.2f}s)"
    )

    return results


if __name__ == "__main__":
    print("NBA Hyperparameter Optimization Examples")
    print("=" * 80)

    # Run examples
    print("\nRunning Grid Search example...")
    grid_result = example_grid_search()

    print("\nRunning Random Search example...")
    random_result = example_random_search()

    print("\nRunning Bayesian Optimization example...")
    bayes_result = example_bayesian_optimization()

    print("\nRunning comparison example...")
    comparison_results = compare_methods()

    print("\n" + "=" * 80)
    print("✅ All examples completed successfully!")
    print("=" * 80)

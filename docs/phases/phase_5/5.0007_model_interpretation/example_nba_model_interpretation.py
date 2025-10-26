#!/usr/bin/env python3
"""
NBA Model Interpretation Example
=================================

Demonstrates model interpretation for NBA win prediction using:
- SHAP values for feature importance
- Partial dependence plots
- Individual prediction explanations

Implementation: MCP Book Recommendation #15
Framework: scripts/ml/model_interpretation.py
"""

import sys

sys.path.append("/Users/ryanranft/nba-simulator-aws")

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from scripts.ml.model_interpretation import ModelInterpreter


def load_sample_data():
    """Load sample NBA data."""
    np.random.seed(42)
    n_games = 1000

    data = pd.DataFrame(
        {
            "team_fg_pct_last_5": np.random.uniform(0.40, 0.50, n_games),
            "opponent_fg_pct_last_5": np.random.uniform(0.40, 0.50, n_games),
            "home_away": np.random.choice([0, 1], n_games),
            "rest_days": np.random.choice([0, 1, 2, 3], n_games),
            "win_streak": np.random.choice([0, 1, 2, 3, 4, 5], n_games),
            "win": np.random.choice([0, 1], n_games),
        }
    )

    return data


def example_shap_importance():
    """Example: SHAP feature importance"""
    print("\n" + "=" * 80)
    print("EXAMPLE: SHAP Feature Importance for NBA Win Prediction")
    print("=" * 80)

    # Load and prepare data
    data = load_sample_data()
    feature_cols = [col for col in data.columns if col != "win"]

    X_train = data[feature_cols].iloc[:800]
    y_train = data["win"].iloc[:800]
    X_test = data[feature_cols].iloc[800:]

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Initialize interpreter
    interpreter = ModelInterpreter(model, X_train, feature_cols)

    # Get SHAP values
    print("\nCalculating SHAP values...")
    shap_values = interpreter.get_shap_values(X_test, model_type="tree")

    # Display feature importance
    print("\n✅ Feature Importance (SHAP-based):")
    importance = interpreter.get_feature_importance(shap_values, X_test)
    for feature, imp in importance.items():
        print(f"  {feature}: {imp:.4f}")

    # Explain single prediction
    print("\nExplaining single prediction:")
    instance_idx = 0
    explanation = interpreter.explain_prediction(
        X_test.iloc[instance_idx], shap_values[instance_idx]
    )
    print(
        f"  Predicted win probability: {model.predict_proba(X_test.iloc[[instance_idx]])[0][1]:.2%}"
    )
    print(f"  Feature contributions:")
    for feature, contrib in explanation.items():
        print(f"    {feature}: {contrib:+.4f}")

    return interpreter


if __name__ == "__main__":
    print("NBA Model Interpretation Example")
    print("=" * 80)

    result = example_shap_importance()

    print("\n✅ Example completed successfully!")

#!/usr/bin/env python3
"""
Prediction API: Flask API for serving NBA game predictions.

Endpoints:
- POST /predict: Predict game outcome
- GET /health: Health check
- GET /model_info: Model metadata

Usage:
    python scripts/ml/prediction_api.py

    # Then in another terminal:
    curl -X POST http://localhost:5001/predict \
        -H "Content-Type: application/json" \
        -d @sample_game.json
"""

from flask import Flask, request, jsonify
import mlflow.sklearn
import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime

app = Flask(__name__)

# Global variables for model artifacts
MODEL = None
SCALER = None
FEATURE_LIST = None
TRAIN_STATS = None
MODEL_INFO = {}


def load_model_artifacts():
    """Load model and preprocessing artifacts from MLflow."""
    global MODEL, SCALER, FEATURE_LIST, TRAIN_STATS, MODEL_INFO

    print("Loading model artifacts from MLflow...")

    # Load model from MLflow
    run_id = "1a2725dca5304ec9ad9602756296153e"  # From registration
    MODEL = mlflow.sklearn.load_model(f"runs:/{run_id}/model")
    print(f"  ✓ Model loaded (run_id: {run_id})")

    # Load scaler
    with open("/tmp/scaler.pkl", "rb") as f:
        SCALER = pickle.load(f)
    print("  ✓ Scaler loaded")

    # Load feature list
    with open("/tmp/feature_list.txt", "r") as f:
        FEATURE_LIST = [line.strip() for line in f]
    print(f"  ✓ Feature list loaded ({len(FEATURE_LIST)} features)")

    # Load training stats
    TRAIN_STATS = pd.read_csv("/tmp/train_stats.csv", index_col="feature")
    print("  ✓ Training stats loaded")

    # Model info
    MODEL_INFO = {
        "model_name": "nba_game_predictor",
        "model_version": "1",
        "run_id": run_id,
        "n_features": len(FEATURE_LIST),
        "test_accuracy": 0.840,
        "test_auc": 0.918,
        "trained_on": "2017-2020 seasons",
        "last_updated": datetime.now().isoformat(),
    }

    print("\n✓ All artifacts loaded successfully!")


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "model_loaded": MODEL is not None,
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/model_info", methods=["GET"])
def model_info():
    """Return model metadata."""
    return jsonify(MODEL_INFO)


@app.route("/predict", methods=["POST"])
def predict():
    """
    Predict game outcome.

    Expected input format:
    {
        "features": {
            "home_points_rolling_3_mean_sum": 310.5,
            "away_points_rolling_3_mean_sum": 295.0,
            ...
        }
    }

    Returns:
    {
        "prediction": "win" or "loss",
        "probability": 0.85,
        "confidence": "high"
    }
    """
    try:
        # Parse request
        data = request.get_json()

        if "features" not in data:
            return jsonify({"error": 'Missing "features" in request'}), 400

        features_dict = data["features"]

        # Convert to DataFrame
        df = pd.DataFrame([features_dict])

        # Check for missing features
        missing_features = set(FEATURE_LIST) - set(df.columns)
        if missing_features:
            return (
                jsonify(
                    {
                        "error": f"Missing {len(missing_features)} required features",
                        "missing_features": list(missing_features)[
                            :10
                        ],  # Show first 10
                    }
                ),
                400,
            )

        # Select and order features
        df = df[FEATURE_LIST]

        # Handle missing values (impute with training means)
        for col in df.columns:
            if df[col].isna().any():
                df[col] = df[col].fillna(TRAIN_STATS.loc[col, "mean"])

        # Handle inf values
        df = df.replace([np.inf, -np.inf], np.nan)
        for col in df.columns:
            if df[col].isna().any():
                df[col] = df[col].fillna(TRAIN_STATS.loc[col, "mean"])

        # Scale
        X_scaled = SCALER.transform(df)

        # Predict
        prediction = MODEL.predict(X_scaled)[0]
        probability = MODEL.predict_proba(X_scaled)[0]

        # Format response
        response = {
            "prediction": "win" if prediction == 1 else "loss",
            "probability": float(probability[1]),  # Probability of win
            "probabilities": {
                "loss": float(probability[0]),
                "win": float(probability[1]),
            },
            "confidence": (
                "high"
                if max(probability) > 0.75
                else "medium" if max(probability) > 0.6 else "low"
            ),
            "timestamp": datetime.now().isoformat(),
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/predict_batch", methods=["POST"])
def predict_batch():
    """
    Predict multiple games at once.

    Expected input format:
    {
        "games": [
            {"features": {...}},
            {"features": {...}},
            ...
        ]
    }
    """
    try:
        data = request.get_json()

        if "games" not in data:
            return jsonify({"error": 'Missing "games" in request'}), 400

        games = data["games"]
        predictions = []

        for i, game in enumerate(games):
            if "features" not in game:
                predictions.append({"game_id": i, "error": "Missing features"})
                continue

            # Create single prediction request
            single_result = predict_single_game(game["features"])
            single_result["game_id"] = game.get("game_id", i)
            predictions.append(single_result)

        return jsonify(
            {
                "predictions": predictions,
                "count": len(predictions),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def predict_single_game(features_dict):
    """Helper function to predict a single game."""
    # Convert to DataFrame
    df = pd.DataFrame([features_dict])

    # Select features
    df = df[FEATURE_LIST]

    # Handle missing/inf values
    for col in df.columns:
        if df[col].isna().any() or np.isinf(df[col]).any():
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            df[col] = df[col].fillna(TRAIN_STATS.loc[col, "mean"])

    # Scale and predict
    X_scaled = SCALER.transform(df)
    prediction = MODEL.predict(X_scaled)[0]
    probability = MODEL.predict_proba(X_scaled)[0]

    return {
        "prediction": "win" if prediction == 1 else "loss",
        "probability": float(probability[1]),
        "confidence": (
            "high"
            if max(probability) > 0.75
            else "medium" if max(probability) > 0.6 else "low"
        ),
    }


if __name__ == "__main__":
    # Load model artifacts on startup
    load_model_artifacts()

    # Start Flask app
    print("\n" + "=" * 70)
    print("NBA GAME PREDICTION API")
    print("=" * 70)
    print(f"\nModel: {MODEL_INFO['model_name']} v{MODEL_INFO['model_version']}")
    print(f"Test Accuracy: {MODEL_INFO['test_accuracy']:.1%}")
    print(f"Test AUC: {MODEL_INFO['test_auc']:.3f}")
    print(f"\nEndpoints:")
    print(f"  GET  /health       - Health check")
    print(f"  GET  /model_info   - Model metadata")
    print(f"  POST /predict      - Single game prediction")
    print(f"  POST /predict_batch - Batch predictions")
    print(f"\nStarting server on http://localhost:5001...")
    print("=" * 70)

    app.run(host="0.0.0.0", port=5001, debug=False)

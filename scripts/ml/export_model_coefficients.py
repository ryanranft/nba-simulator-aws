#!/usr/bin/env python3
"""
Export trained model coefficients to JSON format
This allows Lambda to make predictions without scikit-learn
"""

import json
import pickle
import boto3
import numpy as np
from io import BytesIO

S3_BUCKET = "nba-sim-raw-data-lake"
S3_MODELS_PREFIX = "ml-models"


def load_model_from_s3(model_name="logistic_regression"):
    """Load trained model and scaler from S3"""
    s3 = boto3.client("s3")

    # Load model
    model_key = f"{S3_MODELS_PREFIX}/{model_name}.pkl"
    model_obj = s3.get_object(Bucket=S3_BUCKET, Key=model_key)
    model = pickle.load(BytesIO(model_obj["Body"].read()))

    # Load scaler
    scaler_key = f"{S3_MODELS_PREFIX}/scaler.pkl"
    scaler_obj = s3.get_object(Bucket=S3_BUCKET, Key=scaler_key)
    scaler = pickle.load(BytesIO(scaler_obj["Body"].read()))

    return model, scaler


def export_coefficients():
    """Export model coefficients and scaler parameters to JSON"""
    print("Loading model from S3...")
    model, scaler = load_model_from_s3()

    # Extract model parameters
    coefficients = {
        "model_type": "logistic_regression",
        "coefficients": model.coef_[0].tolist(),
        "intercept": float(model.intercept_[0]),
        "classes": model.classes_.tolist(),
        "feature_names": [
            "home_rolling_win_pct",
            "home_rolling_ppg",
            "home_rolling_papg",
            "home_rolling_margin",
            "home_rest_days",
            "home_back_to_back",
            "away_rolling_win_pct",
            "away_rolling_ppg",
            "away_rolling_papg",
            "away_rolling_margin",
            "away_rest_days",
            "away_back_to_back",
            "month",
            "day_of_week",
            "is_weekend",
            "season_phase",
        ],
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "accuracy": 0.630,
        "auc": 0.659,
    }

    # Save to S3
    s3 = boto3.client("s3")
    json_data = json.dumps(coefficients, indent=2)

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=f"{S3_MODELS_PREFIX}/model_coefficients.json",
        Body=json_data,
        ContentType="application/json",
    )

    print(
        f"✓ Model coefficients exported to s3://{S3_BUCKET}/{S3_MODELS_PREFIX}/model_coefficients.json"
    )
    print(f"  Features: {len(coefficients['feature_names'])}")
    print(f"  Coefficients: {len(coefficients['coefficients'])}")
    print(f"  Model accuracy: {coefficients['accuracy']}")

    # Also save locally for reference
    with open("/tmp/model_coefficients.json", "w") as f:
        f.write(json_data)
    print(f"✓ Also saved to /tmp/model_coefficients.json")

    return coefficients


if __name__ == "__main__":
    export_coefficients()

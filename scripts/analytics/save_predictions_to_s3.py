#!/usr/bin/env python3
"""
Save ML predictions to S3 in Parquet format for Athena queries
Demonstrates Sub-6.0001: S3 Analytics Lake
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import boto3
from io import BytesIO

# S3 configuration
S3_BUCKET = "nba-sim-raw-data-lake"
S3_MODELS_PREFIX = "ml-models"
S3_PREDICTIONS_PREFIX = "ml-predictions"


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


def generate_sample_predictions(n_games=100):
    """
    Generate sample predictions for demonstration
    In production, this would use real upcoming games from RDS
    """
    print(f"Generating {n_games} sample predictions...")

    # Load best model (Logistic Regression)
    model, scaler = load_model_from_s3("logistic_regression")

    # Generate sample features (17 features as per our training)
    # In production, these would come from feature engineering on real game data
    np.random.seed(42)

    # Realistic feature ranges based on training data
    features = pd.DataFrame(
        {
            "home_rolling_win_pct": np.random.uniform(0.3, 0.7, n_games),
            "home_rolling_ppg": np.random.uniform(95, 115, n_games),
            "home_rolling_papg": np.random.uniform(95, 115, n_games),
            "home_rolling_margin": np.random.uniform(-10, 10, n_games),
            "home_rest_days": np.random.randint(0, 7, n_games),
            "home_back_to_back": np.random.binomial(1, 0.15, n_games),
            "away_rolling_win_pct": np.random.uniform(0.3, 0.7, n_games),
            "away_rolling_ppg": np.random.uniform(95, 115, n_games),
            "away_rolling_papg": np.random.uniform(95, 115, n_games),
            "away_rolling_margin": np.random.uniform(-10, 10, n_games),
            "away_rest_days": np.random.randint(0, 7, n_games),
            "away_back_to_back": np.random.binomial(1, 0.15, n_games),
            "month": np.random.randint(10, 13, n_games),  # Oct-Dec
            "day_of_week": np.random.randint(0, 7, n_games),
            "is_weekend": np.random.binomial(1, 0.3, n_games),
            "season_phase": np.zeros(n_games, dtype=int),  # Early season
        }
    )

    # Scale features
    features_scaled = scaler.transform(features)

    # Generate predictions
    probabilities = model.predict_proba(features_scaled)[:, 1]  # Probability home wins
    predictions = model.predict(features_scaled)

    # Create results DataFrame with game metadata
    teams = ["LAL", "BOS", "GSW", "MIA", "CHI", "NYK", "PHX", "DAL"]
    today = datetime.now()

    results = pd.DataFrame(
        {
            "game_id": [
                f'GAME_{today.strftime("%Y%m%d")}_{i:04d}' for i in range(n_games)
            ],
            "game_date": [today + timedelta(days=i // 10) for i in range(n_games)],
            "season": "2024-25",
            "home_team": np.random.choice(teams, n_games),
            "away_team": np.random.choice(teams, n_games),
            "home_win_prob": probabilities,
            "predicted_home_win": predictions,
            "model_used": "logistic_regression",
            "prediction_timestamp": datetime.now(),
        }
    )

    # Ensure home != away
    mask = results["home_team"] == results["away_team"]
    results.loc[mask, "away_team"] = results.loc[mask, "home_team"].map(
        lambda x: teams[(teams.index(x) + 1) % len(teams)]
    )

    return results


def save_predictions_to_s3(predictions_df, season="2024-25"):
    """
    Save predictions to S3 in partitioned Parquet format
    Partition by season and date for efficient Athena queries
    """
    print(f"\nSaving {len(predictions_df)} predictions to S3...")

    # Group by date for partitioning
    predictions_df["partition_date"] = predictions_df["game_date"].dt.strftime(
        "%Y-%m-%d"
    )

    dates = predictions_df["partition_date"].unique()

    for date in dates:
        date_predictions = predictions_df[
            predictions_df["partition_date"] == date
        ].copy()
        date_predictions = date_predictions.drop("partition_date", axis=1)

        # S3 path with partitioning
        s3_path = f"s3://{S3_BUCKET}/{S3_PREDICTIONS_PREFIX}/season={season}/date={date}/predictions.parquet"

        # Save to S3
        date_predictions.to_parquet(
            s3_path, engine="pyarrow", compression="snappy", index=False
        )

        print(f"  ✓ Saved {len(date_predictions)} predictions to {s3_path}")

    # Verify upload
    s3 = boto3.client("s3")
    response = s3.list_objects_v2(
        Bucket=S3_BUCKET, Prefix=f"{S3_PREDICTIONS_PREFIX}/season={season}/"
    )

    if "Contents" in response:
        total_size = sum(obj["Size"] for obj in response["Contents"])
        print(
            f"\n✓ Upload verified: {len(response['Contents'])} files, {total_size:,} bytes"
        )

    return len(dates)


def main():
    print("=" * 70)
    print("S3 ANALYTICS LAKE - PREDICTION STORAGE DEMO")
    print("=" * 70)
    print()

    # Generate sample predictions
    predictions = generate_sample_predictions(n_games=100)

    print(f"\nSample predictions generated:")
    print(f"  Total games: {len(predictions)}")
    print(
        f"  Date range: {predictions['game_date'].min()} to {predictions['game_date'].max()}"
    )
    print(f"  Average home win probability: {predictions['home_win_prob'].mean():.3f}")
    print(f"  Predicted home wins: {predictions['predicted_home_win'].sum()}")

    # Save to S3
    partitions_created = save_predictions_to_s3(predictions)

    # Summary
    print("\n" + "=" * 70)
    print("PREDICTIONS SAVED TO S3")
    print("=" * 70)
    print(f"\n✓ {len(predictions)} predictions saved")
    print(f"✓ {partitions_created} date partitions created")
    print(f"\nS3 Location:")
    print(f"  s3://{S3_BUCKET}/{S3_PREDICTIONS_PREFIX}/season=2024-25/date=YYYY-MM-DD/")
    print(f"\n📊 Next Step: Query with Athena")
    print(f"  CREATE EXTERNAL TABLE (see Sub-6.0002)")
    print("=" * 70)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test Prediction API: Demonstrate how to use the prediction API.

Run this after starting the API server:
    python scripts/ml/prediction_api.py  # In one terminal
    python scripts/ml/test_prediction_api.py  # In another terminal
"""

import requests
import json
import pandas as pd

API_URL = "http://localhost:5001"

print("=" * 70)
print("TESTING NBA GAME PREDICTION API")
print("=" * 70)

# Test 1: Health check
print("\n[1/4] Health Check...")
response = requests.get(f"{API_URL}/health")
if response.status_code == 200:
    print(f"  ✓ API is healthy: {response.json()}")
else:
    print(f"  ❌ API not responding: {response.status_code}")
    exit(1)

# Test 2: Model info
print("\n[2/4] Model Info...")
response = requests.get(f"{API_URL}/model_info")
if response.status_code == 200:
    model_info = response.json()
    print(f"  Model: {model_info['model_name']} v{model_info['model_version']}")
    print(f"  Accuracy: {model_info['test_accuracy']:.1%}")
    print(f"  AUC: {model_info['test_auc']:.3f}")
    print(f"  Features: {model_info['n_features']}")
else:
    print(f"  ❌ Failed to get model info")

# Test 3: Single prediction with real data
print("\n[3/4] Single Game Prediction...")

# Load test data to get a real example
df = pd.read_parquet("/tmp/real_nba_game_features_selected.parquet")
test_games = df[df["year"] == 2021].head(5)

# Get first game
test_game = test_games.iloc[0]
game_id = test_game["game_id"]
actual_outcome = "win" if test_game["won"] == 1 else "loss"

# Extract features
features = test_game.drop(["game_id", "won", "year"]).to_dict()

# Make prediction
payload = {"features": features}
response = requests.post(f"{API_URL}/predict", json=payload)

if response.status_code == 200:
    result = response.json()
    print(f"  Game ID: {game_id}")
    print(f"  Prediction: {result['prediction']}")
    print(f"  Probability: {result['probability']:.1%}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Actual: {actual_outcome}")
    print(
        f"  {'✓ Correct!' if result['prediction'] == actual_outcome else '✗ Incorrect'}"
    )
else:
    print(f"  ❌ Prediction failed: {response.status_code}")
    print(f"  Error: {response.json()}")

# Test 4: Batch prediction
print("\n[4/4] Batch Prediction...")

# Prepare batch of 3 games
batch_games = []
for i in range(3):
    game = test_games.iloc[i]
    features = game.drop(["game_id", "won", "year"]).to_dict()
    batch_games.append(
        {
            "game_id": game["game_id"],
            "features": features,
            "actual": "win" if game["won"] == 1 else "loss",
        }
    )

payload = {"games": batch_games}
response = requests.post(f"{API_URL}/predict_batch", json=payload)

if response.status_code == 200:
    results = response.json()
    print(f"  Predicted {results['count']} games:")

    for i, pred in enumerate(results["predictions"]):
        actual = batch_games[i]["actual"]
        correct = "✓" if pred["prediction"] == actual else "✗"
        print(
            f"    Game {i+1}: {pred['prediction']} ({pred['probability']:.1%}) vs {actual} {correct}"
        )

    correct_count = sum(
        1
        for i, pred in enumerate(results["predictions"])
        if pred["prediction"] == batch_games[i]["actual"]
    )
    print(
        f"  Accuracy: {correct_count}/{len(batch_games)} ({correct_count/len(batch_games):.1%})"
    )
else:
    print(f"  ❌ Batch prediction failed: {response.status_code}")

print("\n" + "=" * 70)
print("✓ API TESTING COMPLETE")
print("=" * 70)
print("\nThe API is working correctly!")
print("You can now integrate it into your application.")

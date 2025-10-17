#!/bin/bash
################################################################################
# Daily NBA Game Predictions Pipeline
#
# Purpose:
#   - Automated daily execution of prediction pipeline
#   - Fetches upcoming games, generates features, makes predictions
#   - Can be run via cron job
#
# Usage:
#   bash scripts/ml/daily_predictions.sh
#
# Cron example (run daily at 6 AM):
#   0 6 * * * cd /Users/ryanranft/nba-simulator-aws && bash scripts/ml/daily_predictions.sh >> /tmp/predictions.log 2>&1
#
# Author: NBA Simulator AWS Project
# Created: October 17, 2025
################################################################################

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
OUTPUT_DIR="/tmp/nba_predictions"
DAYS_AHEAD=7
SEASONS="2023,2024,2025"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "================================================================================"
echo "NBA DAILY PREDICTIONS PIPELINE"
echo "================================================================================"
echo "Date: $(date)"
echo "Output: $OUTPUT_DIR"
echo ""

cd "$PROJECT_DIR"

# Step 1: Fetch upcoming games
echo "[1/4] Fetching upcoming games from ESPN API..."
python scripts/ml/fetch_upcoming_games.py \
    --days "$DAYS_AHEAD" \
    --output "$OUTPUT_DIR/upcoming_games_${TIMESTAMP}.parquet" \
    2>&1 | tee "$OUTPUT_DIR/step1_fetch_games.log"

if [ $? -eq 0 ]; then
    echo "✓ Step 1 complete"
else
    echo "✗ Step 1 failed"
    exit 1
fi

# Step 2: Fetch recent player data
echo ""
echo "[2/4] Fetching recent player data from S3..."
python scripts/ml/fetch_recent_player_data.py \
    --seasons "$SEASONS" \
    --output "$OUTPUT_DIR/recent_player_data_${TIMESTAMP}.parquet" \
    2>&1 | tee "$OUTPUT_DIR/step2_fetch_players.log"

if [ $? -eq 0 ]; then
    echo "✓ Step 2 complete"
else
    echo "✗ Step 2 failed"
    exit 1
fi

# Step 3: Extract panel features
echo ""
echo "[3/4] Extracting panel features..."
python scripts/ml/prepare_upcoming_game_features.py \
    --games "$OUTPUT_DIR/upcoming_games_${TIMESTAMP}.parquet" \
    --players "$OUTPUT_DIR/recent_player_data_${TIMESTAMP}.parquet" \
    --output "$OUTPUT_DIR/game_features_${TIMESTAMP}.parquet" \
    2>&1 | tee "$OUTPUT_DIR/step3_extract_features.log"

if [ $? -eq 0 ]; then
    echo "✓ Step 3 complete"
else
    echo "✗ Step 3 failed"
    exit 1
fi

# Step 4: Generate predictions
echo ""
echo "[4/4] Generating predictions..."

# Check if trained model exists
if [ -f "/tmp/panel_model.pkl" ]; then
    echo "Using trained model at /tmp/panel_model.pkl"
    python scripts/ml/predict_upcoming_games.py \
        --features "$OUTPUT_DIR/game_features_${TIMESTAMP}.parquet" \
        --model-path "/tmp/panel_model.pkl" \
        --output "$OUTPUT_DIR/predictions_${TIMESTAMP}.csv" \
        2>&1 | tee "$OUTPUT_DIR/step4_predictions.log"
else
    echo "No trained model found. Using demo mode."
    python scripts/ml/demo_predictions.py \
        2>&1 | tee "$OUTPUT_DIR/step4_predictions.log"
    cp /tmp/demo_game_predictions.csv "$OUTPUT_DIR/predictions_${TIMESTAMP}.csv"
fi

if [ $? -eq 0 ]; then
    echo "✓ Step 4 complete"
else
    echo "✗ Step 4 failed"
    exit 1
fi

# Summary
echo ""
echo "================================================================================"
echo "PIPELINE COMPLETE"
echo "================================================================================"
echo "Predictions saved to: $OUTPUT_DIR/predictions_${TIMESTAMP}.csv"
echo ""

# Display predictions
echo "Latest Predictions:"
echo "--------------------------------------------------------------------------------"
if [ -f "$OUTPUT_DIR/predictions_${TIMESTAMP}.csv" ]; then
    head -20 "$OUTPUT_DIR/predictions_${TIMESTAMP}.csv"
fi

# Create symbolic link to latest predictions
ln -sf "$OUTPUT_DIR/predictions_${TIMESTAMP}.csv" "$OUTPUT_DIR/predictions_latest.csv"

echo ""
echo "✓ Latest predictions symlink: $OUTPUT_DIR/predictions_latest.csv"
echo ""
echo "Pipeline completed successfully at $(date)"
echo "================================================================================"

exit 0

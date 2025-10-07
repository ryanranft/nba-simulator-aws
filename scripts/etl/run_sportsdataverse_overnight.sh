#!/bin/bash
#
# SportsDataverse Overnight Scraper
# Scrapes ESPN data via SportsDataverse package: 2007-2025 (18 seasons)
#
# This wrapper ensures proper conda environment activation for subprocess

set -e

# Project paths
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/sportsdataverse_$(date +%Y%m%d_%H%M%S)"
FULL_LOG="/tmp/sportsdataverse_full.log"

mkdir -p "$LOG_DIR"

# Activate conda environment
echo "🔧 Activating conda environment..." | tee -a "$FULL_LOG"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

# Verify environment
echo "🐍 Python: $(which python)" | tee -a "$FULL_LOG"
echo "📦 Checking sportsdataverse installation..." | tee -a "$FULL_LOG"
python -c "import sportsdataverse; print(f'✅ sportsdataverse version: {sportsdataverse.__version__}')" 2>&1 | tee -a "$FULL_LOG"

cd "$PROJECT_DIR"

# Scrape all seasons (2007-2025)
echo "" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Starting SportsDataverse Scraping" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Coverage: 2007-2025 (18 seasons)" | tee -a "$FULL_LOG"
echo "Source: ESPN via SportsDataverse wrapper" | tee -a "$FULL_LOG"
echo "Log directory: $LOG_DIR" | tee -a "$FULL_LOG"
echo "Started: $(date)" | tee -a "$FULL_LOG"
echo "" | tee -a "$FULL_LOG"

# Loop through each season
for year in {2007..2025}; do
    echo "🏀 Starting season $year..." | tee -a "$FULL_LOG"

    python scripts/etl/scrape_sportsdataverse.py \
        --season "$year" \
        --upload-to-s3 \
        --output-dir "/tmp/sportsdataverse" \
        2>&1 | tee -a "$LOG_DIR/season_${year}.log"

    exit_code=${PIPESTATUS[0]}

    if [ $exit_code -eq 0 ]; then
        echo "✅ Season $year complete" | tee -a "$FULL_LOG"
    else
        echo "❌ Season $year failed (exit code: $exit_code)" | tee -a "$FULL_LOG"
    fi

    echo "" | tee -a "$FULL_LOG"
done

echo "================================================" | tee -a "$FULL_LOG"
echo "SportsDataverse scraping completed" | tee -a "$FULL_LOG"
echo "Completed: $(date)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"

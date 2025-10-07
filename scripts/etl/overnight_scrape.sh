#!/bin/bash
#
# Overnight Multi-Source Scraping
#
# This script runs multiple scrapers overnight to collect data from:
# 1. Basketball Reference (2016-2025) - 3.5 sec delay per request
# 2. NBA.com Stats API (2016-2025) - 0.6 sec delay per request
#
# Estimated runtime:
# - Basketball Reference: ~9 seasons × 3 requests × 3.5 sec = ~95 seconds per season (~15 minutes total)
# - NBA Stats API: ~9 seasons × multiple endpoints = ~2-3 hours
# - Total: ~3-4 hours
#
# Usage:
#   bash scripts/etl/overnight_scrape.sh

set -e  # Exit on error

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/overnight_scrape_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "🌙 Starting Overnight Multi-Source Scrape"
echo "📁 Logs: $LOG_DIR"
echo "⏰ Started: $(date)"
echo ""

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

cd "$PROJECT_DIR"

# Seasons to scrape (2016-2025 for maximum feature availability)
SEASONS=(2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

#############################################
# Phase 1: Basketball Reference (Serial)
#############################################
echo "================================================"
echo "Phase 1: Basketball Reference Scraper"
echo "================================================"
echo "⏱️  Rate limit: 3.5 seconds between requests"
echo "📊 Scraping seasons: ${SEASONS[@]}"
echo ""

BREF_LOG="$LOG_DIR/basketball_reference.log"
BREF_ERRORS="$LOG_DIR/basketball_reference_errors.log"

for season in "${SEASONS[@]}"; do
    echo "🏀 Scraping Basketball Reference: $season season..."

    python scripts/etl/scrape_basketball_reference.py \
        --season "$season" \
        --all \
        --upload-to-s3 \
        --output-dir "/tmp/basketball_reference" \
        >> "$BREF_LOG" 2>> "$BREF_ERRORS"

    if [ $? -eq 0 ]; then
        echo "  ✅ $season complete"
    else
        echo "  ❌ $season failed (see $BREF_ERRORS)"
    fi
done

echo ""
echo "✅ Basketball Reference scraping complete"
echo "📝 Log: $BREF_LOG"
echo ""

#############################################
# Phase 2: NBA.com Stats API (Serial)
#############################################
echo "================================================"
echo "Phase 2: NBA.com Stats API Scraper"
echo "================================================"
echo "⏱️  Rate limit: 0.6 seconds between requests"
echo "📊 Scraping seasons: ${SEASONS[@]}"
echo ""

NBA_LOG="$LOG_DIR/nba_stats.log"
NBA_ERRORS="$LOG_DIR/nba_stats_errors.log"

for season in "${SEASONS[@]}"; do
    echo "🏀 Scraping NBA Stats API: $season season..."

    python scripts/etl/scrape_nba_stats_api.py \
        --season "$season" \
        --all-endpoints \
        --upload-to-s3 \
        --output-dir "/tmp/nba_stats" \
        >> "$NBA_LOG" 2>> "$NBA_ERRORS"

    if [ $? -eq 0 ]; then
        echo "  ✅ $season complete"
    else
        echo "  ❌ $season failed (see $NBA_ERRORS)"
    fi
done

echo ""
echo "✅ NBA Stats API scraping complete"
echo "📝 Log: $NBA_LOG"
echo ""

#############################################
# Summary
#############################################
echo "================================================"
echo "🎉 Overnight Scrape Complete!"
echo "================================================"
echo "⏰ Finished: $(date)"
echo ""
echo "📊 Results:"
echo "  - Basketball Reference: See $BREF_LOG"
echo "  - NBA Stats API: See $NBA_LOG"
echo ""
echo "🗂️  All logs: $LOG_DIR"
echo ""

# Count files in S3
echo "📦 Checking S3 uploads..."
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | wc -l | xargs echo "  Basketball Reference files:"
aws s3 ls s3://nba-sim-raw-data-lake/nba_stats/ --recursive | wc -l | xargs echo "  NBA Stats files:"
echo ""

echo "✅ All scraping complete! You can now run the feature engineering pipeline."
echo ""
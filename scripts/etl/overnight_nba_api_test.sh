#!/bin/bash
#
# NBA API Test Scraper (2024-2025 only)
# Modified version for testing before full deployment
#

set -e

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$PROJECT_DIR/logs/nba_api_test_$TIMESTAMP"
FULL_LOG="/tmp/nba_api_test.log"

mkdir -p "$LOG_DIR"

echo "================================================" | tee "$FULL_LOG"
echo "NBA Stats API Test Scraper (2024-2025)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Coverage: 2024-2025 (2 seasons TEST)" | tee -a "$FULL_LOG"
echo "Endpoints: 200+ major NBA Stats API endpoints" | tee -a "$FULL_LOG"
echo "Log directory: $LOG_DIR" | tee -a "$FULL_LOG"
echo "Started: $(date)" | tee -a "$FULL_LOG"
echo "" | tee -a "$FULL_LOG"

# Activate conda environment
echo "🔧 Activating conda environment..." | tee -a "$FULL_LOG"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

# Verify nba_api installation
echo "📦 Checking nba_api installation..." | tee -a "$FULL_LOG"
python -c "from nba_api.stats.endpoints import leaguedashplayerstats; print('✅ nba_api available')" 2>&1 | tee -a "$FULL_LOG"

cd "$PROJECT_DIR"

# TEST SEASONS ONLY (2024-2025)
SEASONS=(2024 2025)

echo "" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Scraping Strategy (TEST MODE)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Total seasons: ${#SEASONS[@]}" | tee -a "$FULL_LOG"
echo "Rate limit: 2.5s between API calls" | tee -a "$FULL_LOG"
echo "Processing each season sequentially" | tee -a "$FULL_LOG"
echo "Estimated runtime: ~50-60 hours (2 seasons)" | tee -a "$FULL_LOG"
echo "" | tee -a "$FULL_LOG"

# Scrape each season
for season in "${SEASONS[@]}"; do
    echo "================================================" | tee -a "$FULL_LOG"
    echo "🏀 Season $season" | tee -a "$FULL_LOG"
    echo "================================================" | tee -a "$FULL_LOG"

    # Run comprehensive scraper for this season
    python scripts/etl/scrape_nba_api_comprehensive.py \
        --season "$season" \
        --all-endpoints \
        --upload-to-s3 \
        --output-dir "/tmp/nba_api_comprehensive" \
        2>&1 | tee -a "$LOG_DIR/season_${season}.log" | tee -a "$FULL_LOG"

    exit_code=${PIPESTATUS[0]}

    if [ $exit_code -eq 0 ]; then
        echo "✅ Season $season complete" | tee -a "$FULL_LOG"
    else
        echo "❌ Season $season failed (exit code: $exit_code)" | tee -a "$FULL_LOG"
        echo "⚠️  Individual files already saved - resume from next season" | tee -a "$FULL_LOG"
    fi

    echo "" | tee -a "$FULL_LOG"

    # Small delay between seasons
    sleep 2
done

echo "================================================" | tee -a "$FULL_LOG"
echo "NBA Stats API test scraping completed" | tee -a "$FULL_LOG"
echo "Completed: $(date)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"

# Print summary
echo "" | tee -a "$FULL_LOG"
echo "📊 Final Summary:" | tee -a "$FULL_LOG"
echo "- Seasons processed: ${#SEASONS[@]}" | tee -a "$FULL_LOG"
echo "- Output directory: /tmp/nba_api_comprehensive" | tee -a "$FULL_LOG"
echo "- S3 location: s3://nba-sim-raw-data-lake/nba_api_comprehensive/" | tee -a "$FULL_LOG"
echo "- Logs: $LOG_DIR" | tee -a "$FULL_LOG"
echo "" | tee -a "$FULL_LOG"
echo "✅ Test complete! If successful, deploy full scraper with all 30 seasons." | tee -a "$FULL_LOG"

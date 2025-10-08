#!/usr/bin/bash
#
# ⚠️ DEPRECATED - DO NOT USE ⚠️
#
# DEPRECATED ON: October 8, 2025
# REASON: Duplicate of run_hoopr_comprehensive_overnight.sh
# ALTERNATIVE: Use scripts/etl/run_hoopr_comprehensive_overnight.sh (identical functionality)
#
# ---
#
# Overnight hoopR Comprehensive NBA Stats API Scraper
#
# Scrapes ALL hoopR data loaders for maximum NBA Stats API coverage (200+ endpoints)
# Coverage: 2002-2025 (hoopR data availability)
#
# Data categories:
# - Play-by-play (detailed possession data)
# - Team box scores (all game-level team stats)
# - Player box scores (all game-level player stats)
# - Schedules (complete season schedules with results)
#
# Runtime estimate: 8-12 hours for 23 seasons
# Data size estimate: 5-10 GB total

set -e

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$PROJECT_DIR/logs/hoopr_comprehensive_$TIMESTAMP"
FULL_LOG="/tmp/hoopr_comprehensive.log"

mkdir -p "$LOG_DIR"

echo "================================================" | tee "$FULL_LOG"
echo "hoopR Comprehensive NBA Stats API Scraper" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Coverage: 2002-2025 (24 seasons) - INCLUDING TODAY" | tee -a "$FULL_LOG"
echo "Endpoints: Play-by-play, Box scores, Schedules" | tee -a "$FULL_LOG"
echo "Log directory: $LOG_DIR" | tee -a "$FULL_LOG"
echo "Output directory: /tmp/hoopr_nba_comprehensive" | tee -a "$FULL_LOG"
echo "Started: $(date)" | tee -a "$FULL_LOG"
echo "" | tee -a "$FULL_LOG"

# Activate conda environment
echo "🔧 Activating conda environment..." | tee -a "$FULL_LOG"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

# Verify hoopR availability
echo "📦 Checking sportsdataverse/hoopR installation..." | tee -a "$FULL_LOG"
python -c "from sportsdataverse.nba import load_nba_pbp; print('✅ hoopR available via sportsdataverse')" 2>&1 | tee -a "$FULL_LOG"

cd "$PROJECT_DIR"

# Define season ranges
# hoopR data typically available from 2002-present
# Include current season (2025) to get today's games
SEASONS=(2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

echo "" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Scraping Strategy" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Total seasons: ${#SEASONS[@]}" | tee -a "$FULL_LOG"
echo "Batch size: 5 seasons per batch (to avoid memory issues)" | tee -a "$FULL_LOG"
echo "" | tee -a "$FULL_LOG"

# Scrape in batches of 5 seasons to avoid memory issues
BATCH_SIZE=5
BATCH_NUM=1

for ((i=0; i<${#SEASONS[@]}; i+=BATCH_SIZE)); do
    # Get current batch
    BATCH_SEASONS=("${SEASONS[@]:i:BATCH_SIZE}")
    SEASON_STR="${BATCH_SEASONS[*]}"

    echo "================================================" | tee -a "$FULL_LOG"
    echo "🏀 Batch $BATCH_NUM: Seasons $SEASON_STR" | tee -a "$FULL_LOG"
    echo "================================================" | tee -a "$FULL_LOG"

    # Run scraper for this batch
    python scripts/etl/scrape_hoopr_nba_stats.py \
        --seasons ${BATCH_SEASONS[@]} \
        --all-endpoints \
        --upload-to-s3 \
        --output-dir "/tmp/hoopr_nba_comprehensive" \
        2>&1 | tee -a "$LOG_DIR/batch_${BATCH_NUM}.log" | tee -a "$FULL_LOG"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "✅ Batch $BATCH_NUM complete" | tee -a "$FULL_LOG"
    else
        echo "❌ Batch $BATCH_NUM failed (exit code: ${PIPESTATUS[0]})" | tee -a "$FULL_LOG"
    fi

    echo "" | tee -a "$FULL_LOG"
    BATCH_NUM=$((BATCH_NUM + 1))

    # Small delay between batches
    sleep 2
done

echo "================================================" | tee -a "$FULL_LOG"
echo "hoopR comprehensive scraping completed" | tee -a "$FULL_LOG"
echo "Completed: $(date)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
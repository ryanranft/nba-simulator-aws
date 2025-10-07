#!/bin/bash
#
# Overnight Comprehensive NBA Stats API Scraper
#
# Scrapes 200+ NBA Stats API endpoints using nba_api (Python equivalent of hoopR)
# Coverage: 1996-2025 (NBA Stats API availability)
#
# Endpoint categories:
# - League dashboards (player stats, team stats, lineups, tracking)
# - Advanced box scores (8 types: advanced, defensive, four factors, misc, tracking, scoring, traditional, usage) ✅ TIER 1
# - Player tracking (passing, rebounding, shot defense, shots) ✅ TIER 1
# - Team dashboards (clutch, splits, opponent stats, lineups)
# - Draft data (combine stats, draft history)
# - Shot charts (detailed player shot charts)
# - Hustle stats (player and team)
# - Synergy play types (10 categories)
#
# TIER 1 ENDPOINTS ENABLED (Oct 6, 2025):
# - Advanced box scores: 100 games × 8 endpoints (testing limit)
# - Player tracking: 50 players × 4 endpoints (testing limit)
# - Features added: 60-80 advanced metrics
#
# Runtime estimate (WITH TESTING LIMITS): 5-6 hours for 30 seasons (~10 min/season)
# Runtime estimate (PRODUCTION - no limits): 750-900 hours for 30 seasons (~25-30 hrs/season)
# Data size estimate: 2-5 GB (testing limits) / 50-100 GB (production)

set -e

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$PROJECT_DIR/logs/nba_api_comprehensive_$TIMESTAMP"
FULL_LOG="/tmp/nba_api_comprehensive.log"

mkdir -p "$LOG_DIR"

echo "================================================" | tee "$FULL_LOG"
echo "Comprehensive NBA Stats API Scraper (nba_api)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Coverage: 1996-2025 (30 seasons)" | tee -a "$FULL_LOG"
echo "Endpoints: 200+ major NBA Stats API endpoints" | tee -a "$FULL_LOG"
echo "Python equivalent of hoopR (R package)" | tee -a "$FULL_LOG"
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

# Define season range (NBA Stats API available from 1996-present)
SEASONS=(1996 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

echo "" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Scraping Strategy" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Total seasons: ${#SEASONS[@]}" | tee -a "$FULL_LOG"
echo "Rate limit: 600ms between API calls" | tee -a "$FULL_LOG"
echo "Processing each season sequentially" | tee -a "$FULL_LOG"
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
    fi

    echo "" | tee -a "$FULL_LOG"

    # Small delay between seasons
    sleep 2
done

echo "================================================" | tee -a "$FULL_LOG"
echo "Comprehensive NBA Stats API scraping completed" | tee -a "$FULL_LOG"
echo "Completed: $(date)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"

# Print summary
echo "" | tee -a "$FULL_LOG"
echo "📊 Final Summary:" | tee -a "$FULL_LOG"
echo "- Seasons processed: ${#SEASONS[@]}" | tee -a "$FULL_LOG"
echo "- Output directory: /tmp/nba_api_comprehensive" | tee -a "$FULL_LOG"
echo "- S3 location: s3://nba-sim-raw-data-lake/nba_api_comprehensive/" | tee -a "$FULL_LOG"
echo "- Logs: $LOG_DIR" | tee -a "$FULL_LOG"
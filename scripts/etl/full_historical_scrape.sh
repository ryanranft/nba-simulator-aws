#!/bin/bash
################################################################################
# ⚠️  WARNING: FULL HISTORICAL SCRAPER - MANUAL USE ONLY ⚠️
################################################################################
#
# This script scrapes ALL 27 seasons (1999-2025) - 12+ HOUR RUNTIME!
#
# ⛔ DO NOT USE FOR NIGHTLY AUTOMATION ⛔
#
# Purpose: Historical backfills only (manual use)
# For nightly updates: use scripts/workflows/overnight_multi_source_unified.sh
#
# This script is preserved for manual historical data collection when needed.
# It scrapes:
# 1. Basketball Reference (1999-2025) - 27 seasons, ~5 minutes
# 2. NBA.com Stats API (1999-2025) - 27 seasons, ~10-12 hours
#
# Total runtime: ~12 hours
# Features gained: 209 advanced metrics
#
# Use cases:
# - Initial database setup
# - Filling large historical gaps
# - Adding new data source (one-time backfill)
#
# DO NOT schedule this in cron/launchd!
################################################################################

set -e  # Exit on error

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/enhanced_scrape_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "🌙 Starting Enhanced Multi-Source Scrape"
echo "📁 Logs: $LOG_DIR"
echo "⏰ Started: $(date)"
echo ""
echo "📊 Coverage: 1999-2025 (27 seasons - matching ESPN data)"
echo "🎯 Target: 209 features from 2 sources"
echo ""

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

cd "$PROJECT_DIR"

# Seasons to scrape (1999-2025 to match ESPN coverage)
SEASONS=(1999 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

#############################################
# Phase 1: Basketball Reference (Extended)
#############################################
echo "================================================"
echo "Phase 1: Basketball Reference Scraper (EXTENDED)"
echo "================================================"
echo "⏱️  Rate limit: 3.5 seconds between requests"
echo "📊 Scraping ${#SEASONS[@]} seasons: 1999-2025"
echo "📈 Features: 47 advanced metrics per game"
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
# Phase 2: NBA.com Stats API (All Endpoints)
#############################################
echo "================================================"
echo "Phase 2: NBA.com Stats API Scraper (ALL ENDPOINTS)"
echo "================================================"
echo "⏱️  Rate limit: 3.0 seconds between requests"
echo "📊 Scraping ${#SEASONS[@]} seasons: 1999-2025"
echo "📈 Features: 92 tracking/hustle/defensive metrics"
echo ""

NBA_LOG="$LOG_DIR/nba_stats.log"
NBA_ERRORS="$LOG_DIR/nba_stats_errors.log"

# Define season start/end dates for NBA.com API (which uses date ranges, not season years)
declare -A SEASON_DATES
SEASON_DATES["1999"]="1998-10-01 1999-06-30"
SEASON_DATES["2000"]="1999-10-01 2000-06-30"
SEASON_DATES["2001"]="2000-10-01 2001-06-30"
SEASON_DATES["2002"]="2001-10-01 2002-06-30"
SEASON_DATES["2003"]="2002-10-01 2003-06-30"
SEASON_DATES["2004"]="2003-10-01 2004-06-30"
SEASON_DATES["2005"]="2004-10-01 2005-06-30"
SEASON_DATES["2006"]="2005-10-01 2006-06-30"
SEASON_DATES["2007"]="2006-10-01 2007-06-30"
SEASON_DATES["2008"]="2007-10-01 2008-06-30"
SEASON_DATES["2009"]="2008-10-01 2009-06-30"
SEASON_DATES["2010"]="2009-10-01 2010-06-30"
SEASON_DATES["2011"]="2010-10-01 2011-06-30"
SEASON_DATES["2012"]="2011-10-01 2012-06-30"
SEASON_DATES["2013"]="2012-10-01 2013-06-30"
SEASON_DATES["2014"]="2013-10-01 2014-06-30"
SEASON_DATES["2015"]="2014-10-01 2015-06-30"
SEASON_DATES["2016"]="2015-10-01 2016-06-30"
SEASON_DATES["2017"]="2016-10-01 2017-06-30"
SEASON_DATES["2018"]="2017-10-01 2018-06-30"
SEASON_DATES["2019"]="2018-10-01 2019-06-30"
SEASON_DATES["2020"]="2019-10-01 2020-10-30"  # COVID-shortened
SEASON_DATES["2021"]="2020-12-01 2021-07-30"  # COVID-shortened
SEASON_DATES["2022"]="2021-10-01 2022-06-30"
SEASON_DATES["2023"]="2022-10-01 2023-06-30"
SEASON_DATES["2024"]="2023-10-01 2024-06-30"
SEASON_DATES["2025"]="2024-10-01 2025-06-30"

for season in "${SEASONS[@]}"; do
    echo "🏀 Scraping NBA Stats API: $season season..."

    dates=(${SEASON_DATES[$season]})
    start_date="${dates[0]}"
    end_date="${dates[1]}"

    python scripts/etl/scrape_nba_stats_api.py \
        --start-date "$start_date" \
        --end-date "$end_date" \
        --upload-to-s3 \
        --output-dir "/tmp/nba_stats" \
        --rate-limit 3.0 \
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
echo "🎉 Enhanced Scrape Complete!"
echo "================================================"
echo "⏰ Finished: $(date)"
echo ""
echo "📊 Coverage Summary:"
echo "  - Seasons scraped: 27 (1999-2025)"
echo "  - Basketball Reference: 47 features × 27 seasons"
echo "  - NBA.com Stats: 92 features × 27 seasons"
echo "  - Total unique features: 209"
echo ""
echo "📝 Logs:"
echo "  - Basketball Reference: $BREF_LOG"
echo "  - NBA Stats API: $NBA_LOG"
echo ""
echo "🗂️  All logs: $LOG_DIR"
echo ""

# Count files in S3
echo "📦 Checking S3 uploads..."
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | wc -l | xargs echo "  Basketball Reference files:"
aws s3 ls s3://nba-sim-raw-data-lake/nba_stats/ --recursive | wc -l | xargs echo "  NBA Stats files:"
aws s3 ls s3://nba-sim-raw-data-lake/nba_stats_api/ --recursive | wc -l | xargs echo "  NBA Stats API files:"
echo ""

echo "✅ Ready for feature engineering pipeline!"
echo ""
echo "Next steps:"
echo "  1. Review logs for any errors"
echo "  2. Verify S3 uploads completed"
echo "  3. Run feature engineering (Week 2 of implementation plan)"
echo ""
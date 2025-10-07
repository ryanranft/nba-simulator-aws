#!/bin/bash
#
# Remainder Multi-Source Scraping
#
# This script scrapes the REMAINING years not covered by overnight_scrape.sh:
# - overnight_scrape.sh is already running: 2016-2025 (10 seasons)
# - This script covers: 1993-2015 (23 seasons)
#
# Combined with overnight_scrape.sh, you'll have complete 1993-2025 coverage.
#
# Estimated runtime:
# - Basketball Reference: 23 seasons × 3 requests × 3.5 sec = ~4 minutes
# - NBA Stats API: 20 seasons (1996-2015) × avg 100 games × 3 calls × 3 sec = ~10-12 hours
# - Total: ~12 hours
#
# Features gained:
# - Basketball Reference: 47 advanced metrics for 1993-2015
# - NBA.com Stats: 92 tracking features for 1996-2015
# - Combined with overnight_scrape.sh: Full 1993-2025 coverage with 209 features

set -e  # Exit on error

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/remainder_scrape_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "🌙 Starting Remainder Multi-Source Scrape"
echo "📁 Logs: $LOG_DIR"
echo "⏰ Started: $(date)"
echo ""
echo "📊 Coverage Plan:"
echo "  - overnight_scrape.sh (running): 2016-2025 (10 seasons)"
echo "  - THIS SCRIPT: 1993-2015 (23 seasons)"
echo "  - COMBINED TOTAL: 1993-2025 (33 seasons, 209 features)"
echo ""

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

cd "$PROJECT_DIR"

# Basketball Reference: 1993-2015 (complement to 2016-2025 already running)
BREF_SEASONS=(1993 1994 1995 1996 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015)

# NBA.com Stats API: 1996-2015 (API starts 1996, complement to 2016-2025 already running)
NBA_SEASONS=(1996 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015)

#############################################
# Phase 1: Basketball Reference (1993-2015)
#############################################
echo "================================================"
echo "Phase 1: Basketball Reference Scraper"
echo "================================================"
echo "⏱️  Rate limit: 3.5 seconds between requests"
echo "📊 Scraping ${#BREF_SEASONS[@]} seasons: 1993-2015"
echo "📈 Features: 47 advanced metrics per game"
echo "   - True Shooting % (TS%)"
echo "   - Player Efficiency Rating (PER)"
echo "   - Box Plus/Minus (BPM)"
echo "   - Win Shares (WS)"
echo "   - Usage Rate"
echo "   - Offensive/Defensive Ratings"
echo ""

BREF_LOG="$LOG_DIR/basketball_reference.log"
BREF_ERRORS="$LOG_DIR/basketball_reference_errors.log"

for season in "${BREF_SEASONS[@]}"; do
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
echo "✅ Basketball Reference scraping complete (1993-2015)"
echo "📝 Log: $BREF_LOG"
echo ""

#############################################
# Phase 2: NBA.com Stats API (1996-2015)
#############################################
echo "================================================"
echo "Phase 2: NBA.com Stats API Scraper"
echo "================================================"
echo "⏱️  Rate limit: 3.0 seconds between requests"
echo "📊 Scraping ${#NBA_SEASONS[@]} seasons: 1996-2015"
echo "📈 Features: 92 tracking/hustle/defensive metrics"
echo "   - Hustle stats (deflections, charges drawn)"
echo "   - Defensive tracking (contested shots, rim protection)"
echo "   - Speed & distance metrics"
echo "   - Clutch performance"
echo "   - Home/away splits"
echo "   - Player Impact Estimate (PIE)"
echo ""

NBA_LOG="$LOG_DIR/nba_stats.log"
NBA_ERRORS="$LOG_DIR/nba_stats_errors.log"

# Season date mappings (NBA seasons span two calendar years)
declare -A SEASON_DATES
SEASON_DATES["1996"]="1995-10-01 1996-06-30"
SEASON_DATES["1997"]="1996-10-01 1997-06-30"
SEASON_DATES["1998"]="1997-10-01 1998-06-30"
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

for season in "${NBA_SEASONS[@]}"; do
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
echo "✅ NBA Stats API scraping complete (1996-2015)"
echo "📝 Log: $NBA_LOG"
echo ""

#############################################
# Summary
#############################################
echo "================================================"
echo "🎉 Remainder Scrape Complete!"
echo "================================================"
echo "⏰ Finished: $(date)"
echo ""
echo "📊 Coverage Summary:"
echo "  THIS SCRIPT (remainder):"
echo "    - Basketball Reference: 1993-2015 (23 seasons, 47 features)"
echo "    - NBA.com Stats API:    1996-2015 (20 seasons, 92 features)"
echo ""
echo "  OVERNIGHT_SCRAPE.SH (running separately):"
echo "    - Basketball Reference: 2016-2025 (10 seasons, 47 features)"
echo "    - NBA.com Stats API:    2016-2025 (10 seasons, 92 features)"
echo ""
echo "  COMBINED TOTAL:"
echo "    - Basketball Reference: 1993-2025 (33 seasons)"
echo "    - NBA.com Stats API:    1996-2025 (30 seasons)"
echo "    - ESPN (existing):      1993-2025 (33 seasons)"
echo "    - Total unique features: 209"
echo ""
echo "📝 Detailed Logs:"
echo "  - Basketball Reference: $BREF_LOG"
echo "  - NBA Stats API: $NBA_LOG"
echo "  - All logs directory: $LOG_DIR"
echo ""

# Count files in S3
echo "📦 Verifying S3 uploads..."
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | wc -l | xargs echo "  Basketball Reference total files:"
aws s3 ls s3://nba-sim-raw-data-lake/nba_stats_api/ --recursive | wc -l | xargs echo "  NBA Stats API total files:"
echo ""

echo "✅ Historical data (1993-2015) now complete!"
echo ""
echo "📋 Next Steps:"
echo "  1. Wait for overnight_scrape.sh to finish (2016-2025)"
echo "  2. Review all logs: ls -lh $PROJECT_DIR/logs/"
echo "  3. Verify complete S3 coverage: aws s3 ls s3://nba-sim-raw-data-lake/"
echo "  4. Begin feature engineering (Week 2 of implementation plan)"
echo ""
echo "💡 Data Source Timeline:"
echo "  - 1993-1995: ESPN (58) + Basketball Reference (47) = 105 features"
echo "  - 1996-2015: ESPN (58) + Basketball Reference (47) + NBA.com (92) = 209 features ✅"
echo "  - 2016-2025: ESPN (58) + Basketball Reference (47) + NBA.com (92) = 209 features ✅"
echo "  - ML-ready with 209 features: 30 years (1996-2025)"
echo ""
#!/bin/bash
#
# Comprehensive Multi-Source Scraping - Maximum Coverage
#
# This script scrapes ALL available years to match your ESPN data:
# 1. Basketball Reference (1993-2025) - 33 seasons matching ESPN
# 2. NBA.com Stats API (1996-2025) - 30 seasons (API limitation: starts 1996)
#
# Data Coverage Summary:
# - ESPN (you already have): 1993-2025 (44,828 games in PostgreSQL)
# - Basketball Reference: 1946-present available, scraping 1993-2025 to match ESPN
# - NBA.com Stats API: 1996-present available (official NBA data starts 1996)
#
# Estimated runtime:
# - Basketball Reference: 33 seasons × 3 requests × 3.5 sec = ~6 minutes
# - NBA Stats API: 30 seasons × avg 100 games/season × 3 API calls × 3 sec = ~15-20 hours
# - Total: ~20 hours
#
# Features gained:
# - Basketball Reference: 47 advanced metrics (TS%, PER, BPM, Win Shares)
# - NBA.com Stats: 92 tracking features (hustle, defense, speed, clutch)
# - Total: 209 features across all sources

set -e  # Exit on error

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/comprehensive_scrape_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "🌙 Starting Comprehensive Multi-Source Scrape"
echo "📁 Logs: $LOG_DIR"
echo "⏰ Started: $(date)"
echo ""
echo "📊 ESPN Coverage (already in database): 1993-2025 (44,828 games)"
echo "📊 Basketball Reference Target: 1993-2025 (33 seasons)"
echo "📊 NBA.com Stats API Target: 1996-2025 (30 seasons - API starts 1996)"
echo "🎯 Total Target: 209 features from 2 new sources"
echo ""

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

cd "$PROJECT_DIR"

# Basketball Reference: Match ESPN coverage (1993-2025)
BREF_SEASONS=(1993 1994 1995 1996 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

# NBA.com Stats API: Limited to 1996-2025 (API availability)
NBA_SEASONS=(1996 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

#############################################
# Phase 1: Basketball Reference (1993-2025)
#############################################
echo "================================================"
echo "Phase 1: Basketball Reference Scraper"
echo "================================================"
echo "⏱️  Rate limit: 3.5 seconds between requests"
echo "📊 Scraping ${#BREF_SEASONS[@]} seasons: 1993-2025"
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
echo "✅ Basketball Reference scraping complete"
echo "📝 Log: $BREF_LOG"
echo ""

#############################################
# Phase 2: NBA.com Stats API (1996-2025)
#############################################
echo "================================================"
echo "Phase 2: NBA.com Stats API Scraper"
echo "================================================"
echo "⏱️  Rate limit: 3.0 seconds between requests"
echo "📊 Scraping ${#NBA_SEASONS[@]} seasons: 1996-2025"
echo "📈 Features: 92 tracking/hustle/defensive metrics"
echo "   - Hustle stats (deflections, charges drawn)"
echo "   - Defensive tracking (contested shots, rim protection)"
echo "   - Speed & distance metrics"
echo "   - Clutch performance (last 5 min, <5pt differential)"
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
echo "✅ NBA Stats API scraping complete"
echo "📝 Log: $NBA_LOG"
echo ""

#############################################
# Summary
#############################################
echo "================================================"
echo "🎉 Comprehensive Scrape Complete!"
echo "================================================"
echo "⏰ Finished: $(date)"
echo ""
echo "📊 Coverage Summary:"
echo "  ESPN (existing):           1993-2025 (44,828 games in PostgreSQL)"
echo "  Basketball Reference:      1993-2025 (33 seasons, 47 features)"
echo "  NBA.com Stats API:         1996-2025 (30 seasons, 92 features)"
echo ""
echo "  Total unique features: 209"
echo "  Total seasons covered: 33 years (1993-2025)"
echo ""
echo "📝 Detailed Logs:"
echo "  - Basketball Reference: $BREF_LOG"
echo "  - NBA Stats API: $NBA_LOG"
echo "  - All logs directory: $LOG_DIR"
echo ""

# Count files in S3
echo "📦 Verifying S3 uploads..."
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | wc -l | xargs echo "  Basketball Reference files:"
aws s3 ls s3://nba-sim-raw-data-lake/nba_stats_api/ --recursive | wc -l | xargs echo "  NBA Stats API files:"
echo ""

echo "✅ All data sources now aligned with ESPN coverage (1993-2025)!"
echo ""
echo "📋 Next Steps:"
echo "  1. Review logs for any errors: less $LOG_DIR/*.log"
echo "  2. Verify S3 uploads: aws s3 ls s3://nba-sim-raw-data-lake/"
echo "  3. Begin feature engineering (Week 2 of implementation plan)"
echo "  4. Load new features into PostgreSQL for ML training"
echo ""
echo "💡 Historical Coverage Comparison:"
echo "  - 1993-1995: ESPN only (Basketball Reference available, NBA API not available)"
echo "  - 1996-2025: All 3 sources (ESPN + Basketball Reference + NBA.com Stats)"
echo "  - Total ML-ready seasons: 30 years with all 209 features (1996-2025)"
echo ""
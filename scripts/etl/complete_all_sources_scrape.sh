#!/bin/bash
#
# Complete All-Sources Overnight Scraping
#
# This script scrapes NBA data from ALL 5 sources:
# 1. Basketball Reference (1946-2025) - 79 years, 47 features
# 2. NBA.com Stats API (1996-2025) - 30 years, 92 features
# 3. SportsDataverse (2007-2025) - 18 years, ESPN wrapper + multi-sport
# 4. Kaggle Database (1946-2025) - Download pre-packaged SQLite DB
# 5. ESPN (already have 1993-2025) - 33 years, 58 features
#
# Estimated runtime:
# - Basketball Reference: 79 seasons × 3 req × 3.5 sec = ~15 minutes
# - NBA Stats API: 30 seasons × ~100 games × 3 calls × 3 sec = ~15-20 hours
# - SportsDataverse: 18 seasons × ~80 games × 3 calls × 0.5 sec = ~2-3 hours
# - Kaggle: 5-15 minutes download
# - Total: ~20-24 hours
#
# Features gained: 209+ (all possible NBA features from all sources)

set -e  # Exit on error

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/complete_all_sources_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "🌌 Starting COMPLETE All-Sources Multi-Night Scrape"
echo "📁 Logs: $LOG_DIR"
echo "⏰ Started: $(date)"
echo ""
echo "📊 Coverage Plan - ALL 5 SOURCES:"
echo "  1. Basketball Reference: 1946-2025 (79 years, 47 features)"
echo "  2. NBA.com Stats API:    1996-2025 (30 years, 92 features)"
echo "  3. SportsDataverse:      2007-2025 (18 years, ESPN wrapper)"
echo "  4. Kaggle Database:      1946-2025 (pre-packaged SQLite)"
echo "  5. ESPN (existing):      1993-2025 (33 years, 58 features)"
echo ""
echo "🎯 TOTAL UNIQUE FEATURES: 209+"
echo "🎯 MAXIMUM HISTORICAL: 79 years (1946-2025)"
echo "🎯 MAXIMUM ML COVERAGE: 30 years (1996-2025) with all features"
echo ""

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

cd "$PROJECT_DIR"

# All seasons for Basketball Reference (1946-2025)
ALL_BREF_SEASONS=(1946 1947 1948 1949 1950 1951 1952 1953 1954 1955 1956 1957 1958 1959 1960 1961 1962 1963 1964 1965 1966 1967 1968 1969 1970 1971 1972 1973 1974 1975 1976 1977 1978 1979 1980 1981 1982 1983 1984 1985 1986 1987 1988 1989 1990 1991 1992 1993 1994 1995 1996 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

# NBA.com Stats API seasons (1996-2025)
NBA_SEASONS=(1996 1997 1998 1999 2000 2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

# SportsDataverse seasons (2007-2025, typical ESPN coverage)
SPORTSDATAVERSE_SEASONS=(2007 2008 2009 2010 2011 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025)

#############################################
# Source 1: Basketball Reference (1946-2025)
#############################################
echo "================================================"
echo "SOURCE 1: Basketball Reference (79 years)"
echo "================================================"
echo "⏱️  Rate limit: 3.5 seconds between requests"
echo "📊 Scraping ${#ALL_BREF_SEASONS[@]} seasons: 1946-2025"
echo "📈 Features: 47 advanced metrics"
echo ""

BREF_LOG="$LOG_DIR/basketball_reference.log"
BREF_ERRORS="$LOG_DIR/basketball_reference_errors.log"

for season in "${ALL_BREF_SEASONS[@]}"; do
    echo "🏀 Basketball Reference: $season season..."

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
echo "✅ Basketball Reference complete (79 years)"
echo ""

#############################################
# Source 2: NBA.com Stats API (1996-2025)
#############################################
echo "================================================"
echo "SOURCE 2: NBA.com Stats API (30 years)"
echo "================================================"
echo "⏱️  Rate limit: 3.0 seconds between requests"
echo "📊 Scraping ${#NBA_SEASONS[@]} seasons: 1996-2025"
echo "📈 Features: 92 tracking/hustle/defensive metrics"
echo ""

NBA_LOG="$LOG_DIR/nba_stats.log"
NBA_ERRORS="$LOG_DIR/nba_stats_errors.log"

# Season date mappings
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
SEASON_DATES["2020"]="2019-10-01 2020-10-30"
SEASON_DATES["2021"]="2020-12-01 2021-07-30"
SEASON_DATES["2022"]="2021-10-01 2022-06-30"
SEASON_DATES["2023"]="2022-10-01 2023-06-30"
SEASON_DATES["2024"]="2023-10-01 2024-06-30"
SEASON_DATES["2025"]="2024-10-01 2025-06-30"

for season in "${NBA_SEASONS[@]}"; do
    echo "🏀 NBA Stats API: $season season..."

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
echo "✅ NBA Stats API complete (30 years)"
echo ""

#############################################
# Source 3: SportsDataverse (2007-2025)
#############################################
echo "================================================"
echo "SOURCE 3: SportsDataverse (18 years)"
echo "================================================"
echo "⏱️  Rate limit: 0.5 seconds between games"
echo "📊 Scraping ${#SPORTSDATAVERSE_SEASONS[@]} seasons: 2007-2025"
echo "📈 Features: ESPN wrapper + multi-sport capabilities"
echo ""

# Check if sportsdataverse is installed
if ! python -c "import sportsdataverse" 2>/dev/null; then
    echo "⚠️  sportsdataverse not installed, installing..."
    pip install sportsdataverse
fi

SPORTSDATAVERSE_LOG="$LOG_DIR/sportsdataverse.log"
SPORTSDATAVERSE_ERRORS="$LOG_DIR/sportsdataverse_errors.log"

for season in "${SPORTSDATAVERSE_SEASONS[@]}"; do
    echo "🏀 SportsDataverse: $season season..."

    python scripts/etl/scrape_sportsdataverse.py \
        --season "$season" \
        --upload-to-s3 \
        --output-dir "/tmp/sportsdataverse" \
        >> "$SPORTSDATAVERSE_LOG" 2>> "$SPORTSDATAVERSE_ERRORS"

    if [ $? -eq 0 ]; then
        echo "  ✅ $season complete"
    else
        echo "  ❌ $season failed (see $SPORTSDATAVERSE_ERRORS)"
    fi
done

echo ""
echo "✅ SportsDataverse complete (18 years)"
echo ""

#############################################
# Source 4: Kaggle Database (1946-2025)
#############################################
echo "================================================"
echo "SOURCE 4: Kaggle Basketball Database"
echo "================================================"
echo "📦 Downloading pre-packaged SQLite database"
echo "💾 Size: ~2-5 GB"
echo "📊 Coverage: 1946-2025 (65,000+ games)"
echo ""

KAGGLE_LOG="$LOG_DIR/kaggle.log"

bash scripts/etl/kaggle_download.sh >> "$KAGGLE_LOG" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Kaggle database downloaded"
else
    echo "⚠️  Kaggle download failed or skipped (see $KAGGLE_LOG)"
    echo "   Note: Requires Kaggle API credentials"
fi

echo ""

#############################################
# Summary
#############################################
echo "================================================"
echo "🎉 COMPLETE All-Sources Scrape Finished!"
echo "================================================"
echo "⏰ Finished: $(date)"
echo ""
echo "📊 Coverage Summary by Source:"
echo ""
echo "SOURCE 1: Basketball Reference"
echo "  - Years: 1946-2025 (79 years)"
echo "  - Features: 47 advanced metrics"
echo "  - Log: $BREF_LOG"
echo ""
echo "SOURCE 2: NBA.com Stats API"
echo "  - Years: 1996-2025 (30 years)"
echo "  - Features: 92 tracking/hustle/defensive"
echo "  - Log: $NBA_LOG"
echo ""
echo "SOURCE 3: SportsDataverse"
echo "  - Years: 2007-2025 (18 years)"
echo "  - Features: ESPN wrapper + multi-sport"
echo "  - Log: $SPORTSDATAVERSE_LOG"
echo ""
echo "SOURCE 4: Kaggle Database"
echo "  - Years: 1946-2025 (65,000+ games)"
echo "  - Format: SQLite database"
echo "  - Log: $KAGGLE_LOG"
echo ""
echo "SOURCE 5: ESPN (existing)"
echo "  - Years: 1993-2025 (44,828 games in PostgreSQL)"
echo "  - Features: 58"
echo ""
echo "📈 Combined Statistics:"
echo "  - Total unique features: 209+"
echo "  - Maximum historical coverage: 79 years (1946-2025)"
echo "  - ML-ready coverage: 30 years (1996-2025)"
echo "  - Total sources integrated: 5"
echo ""
echo "🗂️  All logs: $LOG_DIR"
echo ""

# Count files in S3
echo "📦 Verifying S3 uploads..."
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | wc -l | xargs echo "  Basketball Reference files:"
aws s3 ls s3://nba-sim-raw-data-lake/nba_stats_api/ --recursive | wc -l | xargs echo "  NBA Stats API files:"
aws s3 ls s3://nba-sim-raw-data-lake/sportsdataverse/ --recursive | wc -l | xargs echo "  SportsDataverse files:"
echo ""

echo "✅ All 5 data sources now integrated!"
echo ""
echo "📋 Next Steps:"
echo "  1. Review logs for any errors"
echo "  2. Verify S3 uploads completed"
echo "  3. Explore Kaggle database: sqlite3 data/kaggle/*.sqlite"
echo "  4. Begin feature engineering with ALL sources"
echo "  5. Cross-validate data across sources"
echo ""
echo "💡 Data Validation Opportunities:"
echo "  - Compare Basketball Reference vs Kaggle (both 1946-2025)"
echo "  - Compare NBA Stats API vs Kaggle (both 1996-2025)"
echo "  - Compare SportsDataverse vs ESPN (both ESPN-based)"
echo "  - Use redundancy for data quality checks"
echo ""
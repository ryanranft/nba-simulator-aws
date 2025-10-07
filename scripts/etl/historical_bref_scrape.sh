#!/bin/bash
#
# Historical Basketball Reference Scraping (1946-1992)
#
# This script scrapes the HISTORICAL years before ESPN data begins:
# - Coverage: 1946-1992 (46 seasons)
# - Complements: overnight_scrape.sh (2016-2025) + remainder_scrape.sh (1993-2015)
#
# Combined result: 79 years of Basketball Reference data (1946-2025)
#
# Estimated runtime:
# - Basketball Reference: 46 seasons × 3 requests × 3.5 sec = ~8 minutes
#
# Data quality by era:
# - 1946-1983: Basic box scores (points, FG, FT, assists)
# - 1984-1992: Complete box scores + advanced team stats
#
# Features gained:
# - Historical championship eras (1950s-1990s)
# - Rule change impacts (3-point line 1979, shot clock 1954)
# - Era-adjusted player comparisons
# - Complete 79-year NBA/BAA history

set -e  # Exit on error

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/historical_bref_scrape_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "🏛️  Starting Historical Basketball Reference Scrape"
echo "📁 Logs: $LOG_DIR"
echo "⏰ Started: $(date)"
echo ""
echo "📊 Coverage Plan:"
echo "  - THIS SCRIPT: 1946-1992 (46 seasons - historical era)"
echo "  - remainder_scrape.sh: 1993-2015 (23 seasons)"
echo "  - overnight_scrape.sh: 2016-2025 (10 seasons)"
echo "  - COMBINED TOTAL: 1946-2025 (79 years of Basketball Reference data)"
echo ""
echo "📈 Historical Eras:"
echo "  - 1946-1949: BAA (Basketball Association of America)"
echo "  - 1949-1979: NBA pre-3-point era"
echo "  - 1979-1983: 3-point line introduced"
echo "  - 1984-1992: Modern box scores complete"
echo ""

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

cd "$PROJECT_DIR"

# Basketball Reference: 1946-1992 (pre-ESPN historical data)
HISTORICAL_SEASONS=(1946 1947 1948 1949 1950 1951 1952 1953 1954 1955 1956 1957 1958 1959 1960 1961 1962 1963 1964 1965 1966 1967 1968 1969 1970 1971 1972 1973 1974 1975 1976 1977 1978 1979 1980 1981 1982 1983 1984 1985 1986 1987 1988 1989 1990 1991 1992)

#############################################
# Basketball Reference Historical (1946-1992)
#############################################
echo "================================================"
echo "Basketball Reference Historical Scraper"
echo "================================================"
echo "⏱️  Rate limit: 3.5 seconds between requests"
echo "📊 Scraping ${#HISTORICAL_SEASONS[@]} seasons: 1946-1992"
echo "📈 Features: Variable by era"
echo "   - 1946-1983: Basic stats (points, FG, FT, assists)"
echo "   - 1984-1992: Complete box scores + advanced metrics"
echo ""

BREF_LOG="$LOG_DIR/basketball_reference_historical.log"
BREF_ERRORS="$LOG_DIR/basketball_reference_historical_errors.log"

era_1946=0
era_1979=0
era_1984=0

for season in "${HISTORICAL_SEASONS[@]}"; do
    # Display era context
    if [ $season -eq 1949 ]; then
        echo ""
        echo "  ⭐ 1949: BAA merges with NBL to form NBA"
        echo ""
    elif [ $season -eq 1954 ]; then
        echo ""
        echo "  ⭐ 1954: Shot clock introduced (24 seconds)"
        echo ""
    elif [ $season -eq 1979 ]; then
        echo ""
        echo "  ⭐ 1979: 3-point line introduced"
        echo ""
    elif [ $season -eq 1984 ]; then
        echo ""
        echo "  ⭐ 1984: Complete box scores begin"
        echo ""
    fi

    echo "🏀 Scraping Basketball Reference: $season season..."

    python scripts/etl/scrape_basketball_reference.py \
        --season "$season" \
        --all \
        --upload-to-s3 \
        --output-dir "/tmp/basketball_reference" \
        >> "$BREF_LOG" 2>> "$BREF_ERRORS"

    if [ $? -eq 0 ]; then
        echo "  ✅ $season complete"

        # Track era statistics
        if [ $season -lt 1979 ]; then
            ((era_1946++))
        elif [ $season -lt 1984 ]; then
            ((era_1979++))
        else
            ((era_1984++))
        fi
    else
        echo "  ❌ $season failed (see $BREF_ERRORS)"
    fi
done

echo ""
echo "✅ Historical Basketball Reference scraping complete (1946-1992)"
echo "📝 Log: $BREF_LOG"
echo ""

#############################################
# Summary
#############################################
echo "================================================"
echo "🎉 Historical Scrape Complete!"
echo "================================================"
echo "⏰ Finished: $(date)"
echo ""
echo "📊 Coverage Summary by Era:"
echo "  1946-1978 (Pre-3-point): $era_1946 seasons ✅"
echo "  1979-1983 (3-point era): $era_1979 seasons ✅"
echo "  1984-1992 (Complete):    $era_1984 seasons ✅"
echo ""
echo "📊 Combined Basketball Reference Coverage:"
echo "  THIS SCRIPT:            1946-1992 (46 seasons - historical)"
echo "  remainder_scrape.sh:    1993-2015 (23 seasons)"
echo "  overnight_scrape.sh:    2016-2025 (10 seasons)"
echo "  ─────────────────────────────────────────────"
echo "  TOTAL:                  1946-2025 (79 years!)"
echo ""
echo "📝 Detailed Logs:"
echo "  - Basketball Reference: $BREF_LOG"
echo "  - Error log: $BREF_ERRORS"
echo "  - All logs directory: $LOG_DIR"
echo ""

# Count files in S3
echo "📦 Verifying S3 uploads..."
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | wc -l | xargs echo "  Basketball Reference total files:"
echo ""

echo "✅ Historical data (1946-1992) now complete!"
echo ""
echo "📋 Complete Dataset Status:"
echo "  ESPN (existing):           1993-2025 (33 years)"
echo "  Basketball Reference:      1946-2025 (79 years) ✅"
echo "  NBA.com Stats API:         1996-2025 (30 years)"
echo ""
echo "🏆 NBA/BAA Historical Milestones Now in Dataset:"
echo "  - 1946: BAA founded (11 teams)"
echo "  - 1949: BAA/NBL merger creates NBA"
echo "  - 1954: Shot clock introduced"
echo "  - 1957-1969: Celtics dynasty (11 championships)"
echo "  - 1979: 3-point line, Bird/Magic rivalry begins"
echo "  - 1984: Modern analytics era begins"
echo "  - 1991-1998: Bulls dynasty (6 championships)"
echo ""
echo "📈 Use Cases for Historical Data:"
echo "  1. Long-term trend analysis (scoring, pace, efficiency)"
echo "  2. Era-adjusted player comparisons"
echo "  3. Rule change impact studies"
echo "  4. Championship dynasty analysis"
echo "  5. Visualization dashboards"
echo "  6. Historical feature engineering experiments"
echo ""
echo "💡 Data Quality Notes:"
echo "  - 1946-1973: Basic stats only (no steals/blocks/ORB/DRB)"
echo "  - 1973-1979: Added steals, blocks, offensive/defensive rebounds"
echo "  - 1979-1983: Added 3-point shooting statistics"
echo "  - 1984-1992: Complete modern box scores"
echo "  - 1996-2025: Full play-by-play + shot location"
echo ""
echo "🎯 Next Steps:"
echo "  1. Wait for remainder_scrape.sh to finish (NBA.com Stats 1996-2015)"
echo "  2. Wait for overnight_scrape.sh to finish (2016-2025)"
echo "  3. Verify S3 uploads: aws s3 ls s3://nba-sim-raw-data-lake/"
echo "  4. Begin feature engineering with 79 years of data!"
echo ""
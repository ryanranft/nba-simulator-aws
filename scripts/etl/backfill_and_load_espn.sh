#!/usr/bin/env bash
#
# ESPN Data Backfill and PostgreSQL Loader
#
# This script orchestrates the complete ESPN backfill process:
# 1. Scrapes ESPN data for specified date range
# 2. Saves JSON files locally to data/ directories
# 3. Loads JSON files into PostgreSQL nba_simulator.espn schema
#
# Usage:
#   bash scripts/etl/backfill_and_load_espn.sh [--dry-run|--production|--load-only]
#
# Modes:
#   --dry-run      Test mode - scrape and verify without database writes
#   --production   Full scrape and load to database
#   --load-only    Skip scraping, just load existing local files
#
# Date Ranges (backfill periods):
#   Play-In:    April 16-20, 2025  (--days 207 from today)
#   Playoffs:   April 22-Jun 18, 2025  (--days 143 from today)
#   Preseason:  October 1-20, 2025  (--days 39 from today)
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"

# Scripts
SCRAPER_SCRIPT="$PROJECT_ROOT/scripts/etl/espn_incremental_async.py"
LOADER_SCRIPT="$PROJECT_ROOT/scripts/etl/load_from_local_espn.py"

# Log files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DRY_RUN_LOG="$LOGS_DIR/backfill_gaps_dryrun_$TIMESTAMP.log"
PRODUCTION_LOG="$LOGS_DIR/backfill_gaps_production_$TIMESTAMP.log"
LOAD_LOG="$LOGS_DIR/backfill_gaps_load_$TIMESTAMP.log"
SUMMARY_LOG="$LOGS_DIR/backfill_gaps_summary_$TIMESTAMP.txt"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

# Parse arguments
MODE="${1:---production}"  # Default to production if no argument

# Print header
echo -e "${BLUE}=================================================================="
echo "ESPN Data Backfill and PostgreSQL Loader"
echo "=================================================================="
echo -e "Mode: ${YELLOW}${MODE}${NC}"
echo "Project root: $PROJECT_ROOT"
echo "Data directory: $DATA_DIR"
echo "Log directory: $LOGS_DIR"
echo -e "${BLUE}=================================================================="
echo -e "${NC}"

# Function to run scraper for a specific period
run_scraper() {
    local period_name=$1
    local days_back=$2
    local dry_run_flag=$3
    local log_file=$4

    echo -e "${BLUE}===================================================================${NC}"
    echo -e "${GREEN}Scraping $period_name (last $days_back days)${NC}"
    echo -e "${BLUE}===================================================================${NC}"

    if [ "$dry_run_flag" == "true" ]; then
        python "$SCRAPER_SCRIPT" --days "$days_back" --save-local --dry-run 2>&1 | tee -a "$log_file"
    else
        python "$SCRAPER_SCRIPT" --days "$days_back" --save-local 2>&1 | tee -a "$log_file"
    fi

    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}✗ Scraper failed for $period_name (exit code: $exit_code)${NC}"
        return $exit_code
    fi

    echo -e "${GREEN}✓ Scraper completed for $period_name${NC}\n"
    return 0
}

# Function to load data to PostgreSQL
load_to_postgres() {
    local dry_run_flag=$1
    local log_file=$2

    echo -e "${BLUE}===================================================================${NC}"
    echo -e "${GREEN}Loading JSON files to PostgreSQL (nba_simulator.espn schema)${NC}"
    echo -e "${BLUE}===================================================================${NC}"

    if [ "$dry_run_flag" == "true" ]; then
        python "$LOADER_SCRIPT" --all-local-files --local-data-dir "$DATA_DIR" --dry-run 2>&1 | tee -a "$log_file"
    else
        python "$LOADER_SCRIPT" --all-local-files --local-data-dir "$DATA_DIR" --force 2>&1 | tee -a "$log_file"
    fi

    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}✗ Database loading failed (exit code: $exit_code)${NC}"
        return $exit_code
    fi

    echo -e "${GREEN}✓ Database loading completed${NC}\n"
    return 0
}

# Function to generate summary report
generate_summary() {
    local mode=$1
    local log_file=$2

    echo -e "${BLUE}===================================================================${NC}"
    echo -e "${GREEN}Generating Summary Report${NC}"
    echo -e "${BLUE}===================================================================${NC}"

    {
        echo "ESPN Data Backfill Summary"
        echo "=========================="
        echo ""
        echo "Mode: $mode"
        echo "Date: $(date)"
        echo "Project: $PROJECT_ROOT"
        echo ""
        echo "Files in data directories:"
        echo "--------------------------"
        echo "Box Scores:   $(find "$DATA_DIR/nba_box_score" -name "*.json" 2>/dev/null | wc -l | tr -d ' ') files"
        echo "Play-by-Play: $(find "$DATA_DIR/nba_pbp" -name "*.json" 2>/dev/null | wc -l | tr -d ' ') files"
        echo "Team Stats:   $(find "$DATA_DIR/nba_team_stats" -name "*.json" 2>/dev/null | wc -l | tr -d ' ') files"
        echo "Schedules:    $(find "$DATA_DIR/nba_schedule_json" -name "*.json" 2>/dev/null | wc -l | tr -d ' ') files"
        echo ""
        echo "Logs:"
        echo "-----"
        echo "Dry-run log:    $DRY_RUN_LOG"
        echo "Production log: $PRODUCTION_LOG"
        echo "Load log:       $LOAD_LOG"
        echo "Summary log:    $SUMMARY_LOG"
        echo ""
    } | tee "$log_file"

    echo -e "${GREEN}✓ Summary saved to $log_file${NC}\n"
}

# Main execution logic
case "$MODE" in
    --dry-run)
        echo -e "${YELLOW}Running in DRY-RUN mode${NC}\n"

        # Scrape all three periods with dry-run
        run_scraper "Play-In + Playoffs + Preseason" 207 "true" "$DRY_RUN_LOG" || exit 1

        # Load to PostgreSQL with dry-run
        load_to_postgres "true" "$DRY_RUN_LOG" || exit 1

        # Generate summary
        generate_summary "dry-run" "$SUMMARY_LOG"

        echo -e "${GREEN}✓ Dry-run complete! Review logs before running --production${NC}"
        ;;

    --production)
        echo -e "${YELLOW}Running in PRODUCTION mode${NC}\n"

        # Scrape all three periods
        run_scraper "Play-In + Playoffs + Preseason" 207 "false" "$PRODUCTION_LOG" || exit 1

        # Load to PostgreSQL
        load_to_postgres "false" "$LOAD_LOG" || exit 1

        # Generate summary
        generate_summary "production" "$SUMMARY_LOG"

        echo -e "${GREEN}✓ Production backfill complete!${NC}"
        ;;

    --load-only)
        echo -e "${YELLOW}Running in LOAD-ONLY mode${NC}\n"

        # Skip scraping, just load existing files
        load_to_postgres "false" "$LOAD_LOG" || exit 1

        # Generate summary
        generate_summary "load-only" "$SUMMARY_LOG"

        echo -e "${GREEN}✓ Loading complete!${NC}"
        ;;

    *)
        echo -e "${RED}Error: Invalid mode '$MODE'${NC}"
        echo "Usage: bash scripts/etl/backfill_and_load_espn.sh [--dry-run|--production|--load-only]"
        exit 1
        ;;
esac

echo -e "${BLUE}===================================================================${NC}"
echo -e "${GREEN}All operations complete!${NC}"
echo -e "${BLUE}===================================================================${NC}"

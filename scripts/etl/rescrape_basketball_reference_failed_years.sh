#!/bin/bash
#
# Re-scrape Basketball Reference Failed Years
#
# This script re-scrapes the 26 years that failed due to HTTP 429 rate limiting
# during the initial overnight scrape on October 10, 2025.
#
# Failed years identified:
# - 2001-2013 (13 years) - HIGHEST PRIORITY (ML training gap)
# - 2015, 2017-2018 (3 years)
# - 1986-1991 (6 years)
# - 1993-1999 (7 years)
#
# Root cause: Base rate limit of 5s was too aggressive
# Fix: Updated rate limit to 12s + exponential backoff already in place
#
# Estimated runtime: 2-4 hours (26 years × 2 data types × 12s rate limit)
#

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_SCRAPER="$SCRIPT_DIR/scrape_basketball_reference_complete.py"
LOG_DIR="/tmp/bbref_rescrape_logs"
OUTPUT_DIR="/tmp/basketball_reference_rescrape"
S3_BUCKET="nba-sim-raw-data-lake"

# Create log directory
mkdir -p "$LOG_DIR"

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MASTER_LOG="$LOG_DIR/rescrape_master_$TIMESTAMP.log"

# Failed years arrays
PRIORITY_1_YEARS=(2001 2002 2003 2004 2005 2006 2007 2008 2009 2010 2011 2012 2013)  # 13 years - ML gap
PRIORITY_2_YEARS=(2015 2017 2018)  # 3 years - modern era gaps
PRIORITY_3_YEARS=(1986 1987 1988 1989 1990 1991)  # 6 years - transition era
PRIORITY_4_YEARS=(1993 1994 1995 1996 1997 1998 1999)  # 7 years - transition era

# Combine all failed years
ALL_FAILED_YEARS=("${PRIORITY_1_YEARS[@]}" "${PRIORITY_2_YEARS[@]}" "${PRIORITY_3_YEARS[@]}" "${PRIORITY_4_YEARS[@]}")

# Statistics
TOTAL_YEARS=${#ALL_FAILED_YEARS[@]}
COMPLETED_YEARS=0
FAILED_ATTEMPTS=0

# Functions
log_message() {
    local level=$1
    shift
    local message="$@"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" | tee -a "$MASTER_LOG"
}

scrape_data_type() {
    local year=$1
    local data_type=$2
    local log_file="$LOG_DIR/${data_type}_${year}_$TIMESTAMP.log"

    log_message "INFO" "Scraping $data_type for year $year..."

    # Run scraper with updated rate limit (12s)
    if python "$PYTHON_SCRAPER" \
        --data-type "$data_type" \
        --start-season "$year" \
        --end-season "$year" \
        --upload-to-s3 \
        --s3-bucket "$S3_BUCKET" \
        --output-dir "$OUTPUT_DIR" \
        --rate-limit 12.0 \
        --verbose \
        > "$log_file" 2>&1; then

        log_message "SUCCESS" "✓ $data_type $year completed successfully"
        return 0
    else
        log_message "ERROR" "✗ $data_type $year failed (see $log_file)"
        return 1
    fi
}

# Main execution
log_message "INFO" "========================================="
log_message "INFO" "Basketball Reference Failed Years Re-scrape"
log_message "INFO" "========================================="
log_message "INFO" "Total failed years to re-scrape: $TOTAL_YEARS"
log_message "INFO" "Data types: season-totals, advanced-totals"
log_message "INFO" "Rate limit: 12.0 seconds (updated from 5.0)"
log_message "INFO" "Output directory: $OUTPUT_DIR"
log_message "INFO" "S3 bucket: $S3_BUCKET"
log_message "INFO" "Master log: $MASTER_LOG"
log_message "INFO" "========================================="
log_message "INFO" ""

# Activate conda environment
log_message "INFO" "Activating conda environment: nba-aws"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

# Process each failed year
YEAR_NUM=1
for year in "${ALL_FAILED_YEARS[@]}"; do
    log_message "INFO" ""
    log_message "INFO" "--------------------------------------"
    log_message "INFO" "Processing year $year ($YEAR_NUM/$TOTAL_YEARS)"
    log_message "INFO" "--------------------------------------"

    YEAR_SUCCESS=true

    # Scrape season totals
    if ! scrape_data_type "$year" "season-totals"; then
        YEAR_SUCCESS=false
        ((FAILED_ATTEMPTS++)) || true
    fi

    # Wait between data types (additional rate limiting)
    sleep 5

    # Scrape advanced totals
    if ! scrape_data_type "$year" "advanced-totals"; then
        YEAR_SUCCESS=false
        ((FAILED_ATTEMPTS++)) || true
    fi

    # Mark year as completed if both data types succeeded
    if [ "$YEAR_SUCCESS" = true ]; then
        ((COMPLETED_YEARS++)) || true
        log_message "SUCCESS" "✓ Year $year complete"
    else
        log_message "WARNING" "⚠ Year $year had failures"
    fi

    # Progress update
    log_message "INFO" "Progress: $COMPLETED_YEARS/$TOTAL_YEARS years completed"

    ((YEAR_NUM++)) || true
done

# Final statistics
log_message "INFO" ""
log_message "INFO" "========================================="
log_message "INFO" "Re-scrape Complete!"
log_message "INFO" "========================================="
log_message "INFO" "Total years processed: $TOTAL_YEARS"
log_message "INFO" "Successfully completed: $COMPLETED_YEARS"
log_message "INFO" "Failed attempts: $FAILED_ATTEMPTS"
log_message "INFO" "Success rate: $(awk "BEGIN {printf \"%.1f\", ($COMPLETED_YEARS/$TOTAL_YEARS)*100}")%"
log_message "INFO" ""
log_message "INFO" "Logs saved to: $LOG_DIR"
log_message "INFO" "Master log: $MASTER_LOG"
log_message "INFO" ""

# Check for failures
if [ "$FAILED_ATTEMPTS" -gt 0 ]; then
    log_message "WARNING" "⚠ Some scrapes failed. Review logs in $LOG_DIR"
    log_message "WARNING" "Grep for errors: grep ERROR $LOG_DIR/*.log"
    exit 1
else
    log_message "SUCCESS" "✅ All scrapes completed successfully!"
    log_message "INFO" ""
    log_message "INFO" "Next steps:"
    log_message "INFO" "1. Verify data in S3: aws s3 ls s3://$S3_BUCKET/basketball_reference/season_totals/"
    log_message "INFO" "2. Re-integrate: python scripts/etl/integrate_basketball_reference_aggregate.py"
    log_message "INFO" "3. Re-validate: python scripts/validation/cross_validate_basketball_reference.py"
    exit 0
fi

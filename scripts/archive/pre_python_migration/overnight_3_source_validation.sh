#!/bin/bash
################################################################################
# Overnight 3-Source Validation Workflow
#
# Simplified overnight workflow for cross-validating 3 data sources:
# 1. ESPN (last 3 days)
# 2. hoopR (last 3 days)
# 3. NBA API (last 3 days)
#
# Plus Basketball Reference aggregates (current season)
#
# Strategy:
# - Scrape last 3 days from each source (no database required)
# - Upload all to S3
# - Cross-validate across all 3 sources
# - Generate quality report
# - Flag discrepancies
#
# Schedule: Daily at 3:00 AM (games are final, web traffic is low)
# LaunchAgent: ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
#
# Version: 2.0 (Simplified 3-Source)
# Created: October 18, 2025
################################################################################

set -e  # Exit on error (disabled for non-fatal errors)
set -u  # Exit on undefined variable

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_DIR/logs/overnight"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/overnight_3source_$TIMESTAMP.log"
REPORTS_DIR="$PROJECT_DIR/reports/validation"

# Scraping parameters
DAYS_BACK=3  # Always scrape last 3 days

################################################################################
# Logging Functions
################################################################################

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "========================================================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "========================================================================" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

################################################################################
# Setup
################################################################################

setup() {
    log_section "OVERNIGHT 3-SOURCE VALIDATION WORKFLOW"

    # Create directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$REPORTS_DIR"

    log "Log file: $LOG_FILE"
    log "Project directory: $PROJECT_DIR"
    log ""

    # Activate conda environment
    log "Activating conda environment: nba-aws"
    source /Users/ryanranft/miniconda3/etc/profile.d/conda.sh
    conda activate nba-aws

    # Load credentials
    log "Loading credentials..."
    if [ -f "/Users/ryanranft/nba-sim-credentials.env" ]; then
        source /Users/ryanranft/nba-sim-credentials.env
    fi

    log "✓ Setup complete"
}

################################################################################
# Step 1: Scrape ESPN Data
################################################################################

scrape_espn() {
    log_section "STEP 1: SCRAPE ESPN DATA (LAST $DAYS_BACK DAYS)"

    log "Running ESPN simplified scraper..."

    if python scripts/etl/espn_incremental_simple.py --days $DAYS_BACK >> "$LOG_FILE" 2>&1; then
        log "✓ ESPN scraping complete"
        return 0
    else
        log_error "ESPN scraping failed (non-fatal, continuing)"
        return 1
    fi
}

################################################################################
# Step 2: Scrape hoopR Data
################################################################################

scrape_hoopr() {
    log_section "STEP 2: SCRAPE HOOPR DATA (LAST $DAYS_BACK DAYS)"

    log "Running hoopR simplified scraper..."

    if python scripts/etl/hoopr_incremental_simple.py --days $DAYS_BACK >> "$LOG_FILE" 2>&1; then
        log "✓ hoopR scraping complete"
        return 0
    else
        log_error "hoopR scraping failed (non-fatal, continuing)"
        return 1
    fi
}

################################################################################
# Step 3: Scrape NBA API Data
################################################################################

scrape_nba_api() {
    log_section "STEP 3: SCRAPE NBA API DATA (LAST $DAYS_BACK DAYS)"

    log "Running NBA API simplified scraper..."

    if python scripts/etl/nba_api_incremental_simple.py --days $DAYS_BACK >> "$LOG_FILE" 2>&1; then
        log "✓ NBA API scraping complete"
        return 0
    else
        log_error "NBA API scraping failed (non-fatal, continuing)"
        return 1
    fi
}

################################################################################
# Step 4: Scrape Basketball Reference (Aggregates)
################################################################################

scrape_basketball_reference() {
    log_section "STEP 4: SCRAPE BASKETBALL REFERENCE AGGREGATE DATA"

    log "Running Basketball Reference incremental scraper (current season)..."

    if python scripts/etl/basketball_reference_incremental_scraper.py --upload-to-s3 >> "$LOG_FILE" 2>&1; then
        log "✓ Basketball Reference scraping complete"

        # Re-integrate into local database
        log "Re-integrating Basketball Reference aggregate data..."
        if python scripts/etl/integrate_basketball_reference_aggregate.py >> "$LOG_FILE" 2>&1; then
            log "✓ Basketball Reference database updated"
            return 0
        else
            log_error "Basketball Reference integration failed (non-fatal)"
            return 1
        fi
    else
        log_error "Basketball Reference scraping failed (non-fatal)"
        return 1
    fi
}

################################################################################
# Step 5: Cross-Validate 3 Sources
################################################################################

cross_validate() {
    log_section "STEP 5: CROSS-VALIDATE 3 SOURCES"

    log "Running 3-source cross-validation..."

    if python scripts/validation/cross_validate_3_sources.py --days $DAYS_BACK >> "$LOG_FILE" 2>&1; then
        log "✓ Cross-validation complete"

        # Find the latest validation report
        latest_report=$(ls -t "$REPORTS_DIR"/cross_validation_*.json 2>/dev/null | head -1)
        if [ -n "$latest_report" ]; then
            log "  Report: $latest_report"

            # Extract key metrics
            games_checked=$(python -c "import json; data = json.load(open('$latest_report')); print(data['games_checked'])" 2>/dev/null || echo "N/A")
            discrepancies=$(python -c "import json; data = json.load(open('$latest_report')); print(len(data['discrepancies']))" 2>/dev/null || echo "N/A")

            log "  Games validated: $games_checked"
            log "  Discrepancies found: $discrepancies"
        fi
        return 0
    else
        log_error "Cross-validation failed"
        return 1
    fi
}

################################################################################
# Main Workflow
################################################################################

main() {
    # Track overall status
    FAILED_STEPS=0

    # Setup
    setup

    # Step 1: ESPN
    if ! scrape_espn; then
        FAILED_STEPS=$((FAILED_STEPS + 1))
    fi

    # Step 2: hoopR
    if ! scrape_hoopr; then
        FAILED_STEPS=$((FAILED_STEPS + 1))
    fi

    # Step 3: NBA API
    if ! scrape_nba_api; then
        FAILED_STEPS=$((FAILED_STEPS + 1))
    fi

    # Step 4: Basketball Reference
    if ! scrape_basketball_reference; then
        FAILED_STEPS=$((FAILED_STEPS + 1))
    fi

    # Step 5: Cross-validate (only if at least 2 sources succeeded)
    if [ $FAILED_STEPS -le 2 ]; then
        if ! cross_validate; then
            FAILED_STEPS=$((FAILED_STEPS + 1))
        fi
    else
        log_error "Too many scraping failures ($FAILED_STEPS), skipping cross-validation"
        FAILED_STEPS=$((FAILED_STEPS + 1))
    fi

    # Final summary
    log_section "WORKFLOW SUMMARY"
    log "Total steps: 5"
    log "Failed steps: $FAILED_STEPS"

    if [ $FAILED_STEPS -eq 0 ]; then
        log "✓ ALL STEPS COMPLETED SUCCESSFULLY"
        exit 0
    elif [ $FAILED_STEPS -le 2 ]; then
        log "⚠️  COMPLETED WITH $FAILED_STEPS WARNINGS"
        exit 0
    else
        log "❌ WORKFLOW FAILED ($FAILED_STEPS critical errors)"
        exit 1
    fi
}

# Run main workflow
main

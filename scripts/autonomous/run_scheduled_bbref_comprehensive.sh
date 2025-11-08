#!/bin/bash
#
# Basketball Reference Comprehensive Scraper - Daily Runner
#
# Runs the complete 43-data-type Basketball Reference scraper for comprehensive data collection
# Tiers 1-11: All NBA and G League data types
#
# Designed to be called by cron daily at 4 AM (after ESPN and hoopR)
#
# Usage:
#   bash scripts/autonomous/run_scheduled_bbref_comprehensive.sh [--priority TIER] [--season SEASON]
#

set -e

# Configuration
PRIORITY="${1:---priority IMMEDIATE}"  # Default: IMMEDIATE (Tiers 1-2)
SEASON="${2:---season current}"  # Default: current season
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_ROOT/logs/autonomous"
LOG_FILE="$LOG_DIR/bbref_comprehensive_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handler
error_handler() {
    log "ERROR: Basketball Reference comprehensive scraper failed at line $1"
    exit 1
}

trap 'error_handler $LINENO' ERR

# Change to project directory
cd "$PROJECT_ROOT"

log "========================================================================"
log "BASKETBALL REFERENCE COMPREHENSIVE SCRAPER - Daily Run"
log "========================================================================"
log "Mode: 43 Data Types (Tiers 1-11: All NBA + G League)"
log "Priority: $(echo $PRIORITY | grep -oP 'IMMEDIATE|HIGH|MEDIUM|LOW' || echo 'IMMEDIATE')"
log "Season: $(echo $SEASON | grep -oP 'current|\\d{4}' || echo 'current')"
log "Upload to S3: ENABLED"
log "Log file: $LOG_FILE"
log ""
log "Estimated runtime: 3-4 hours (rate limited: 12s between requests)"
log "Estimated output: 2-5 GB"
log ""

# Determine season argument format
SEASON_ARG=$(echo $SEASON | grep -oP 'current|\\d{4}' || echo 'current')
if [[ "$SEASON_ARG" == "current" ]]; then
    CURRENT_YEAR=$(date +%Y)
    CURRENT_MONTH=$(date +%m)
    # NBA season spans two calendar years (Oct-Jun)
    if [[ $CURRENT_MONTH -ge 10 ]]; then
        SEASON_YEAR=$CURRENT_YEAR
    else
        SEASON_YEAR=$((CURRENT_YEAR - 1))
    fi
    log "Current NBA season: $SEASON_YEAR-$((SEASON_YEAR + 1))"
else
    SEASON_YEAR=$SEASON_ARG
    log "Specified season: $SEASON_YEAR-$((SEASON_YEAR + 1))"
fi

log ""

# Phase 1: Run comprehensive Basketball Reference scraper
log "Phase 1/3: Running Basketball Reference 43-data-type comprehensive scraper..."
log "Note: This includes ALL tiers (1-11) for complete coverage"
log "      Rate limited to 12 seconds between requests (5 req/min)"
log ""

# Build command
SCRAPER_CMD="python scripts/etl/basketball_reference_comprehensive_scraper.py \
    $PRIORITY \
    $SEASON \
    --upload-to-s3 \
    --log-level INFO"

log "Running: $SCRAPER_CMD"
log ""

# Run scraper (captures output to log)
python scripts/etl/basketball_reference_comprehensive_scraper.py \
    $PRIORITY \
    $SEASON \
    --upload-to-s3 \
    --log-level INFO >> "$LOG_FILE" 2>&1
SCRAPER_EXIT_CODE=$?

if [ $SCRAPER_EXIT_CODE -eq 0 ]; then
    log "✓ Basketball Reference comprehensive scraper completed successfully"
else
    log "✗ Basketball Reference comprehensive scraper failed with exit code $SCRAPER_EXIT_CODE"
    exit $SCRAPER_EXIT_CODE
fi

log ""

# Phase 2: Update DIMS metrics (with timeout protection)
log "Phase 2/3: Updating DIMS Basketball Reference comprehensive metrics..."
log "Note: DIMS update runs in background - may take 2-3 minutes"

# Run DIMS update in background
python scripts/monitoring/dims_cli.py update --category basketball_reference_comprehensive >> "$LOG_FILE" 2>&1 &
DIMS_PID=$!
log "DIMS update started (PID: $DIMS_PID)"

# Wait up to 120 seconds for DIMS to complete (longer for comprehensive data)
DIMS_TIMEOUT=120
DIMS_ELAPSED=0
while kill -0 $DIMS_PID 2>/dev/null && [ $DIMS_ELAPSED -lt $DIMS_TIMEOUT ]; do
    sleep 5
    DIMS_ELAPSED=$((DIMS_ELAPSED + 5))
done

if kill -0 $DIMS_PID 2>/dev/null; then
    log "⚠ DIMS still running after ${DIMS_TIMEOUT}s - continuing anyway (non-critical)"
    log "  DIMS will complete in background"
    DIMS_EXIT_CODE=0
else
    wait $DIMS_PID
    DIMS_EXIT_CODE=$?
    if [ $DIMS_EXIT_CODE -eq 0 ]; then
        log "✓ DIMS metrics updated successfully"
    else
        log "⚠ DIMS update failed with exit code $DIMS_EXIT_CODE (non-critical)"
    fi
fi

log ""

# Phase 3: Note about reconciliation
log "Phase 3/3: Reconciliation info..."
log "Note: Reconciliation runs automatically via autonomous loop every 15 minutes"
log "      No manual trigger needed - ADCE will detect and process new data"
RECON_EXIT_CODE=0

log ""
log "========================================================================"
log "BASKETBALL REFERENCE COMPREHENSIVE SCRAPER - Complete"
log "========================================================================"
log "Scraper: $([ $SCRAPER_EXIT_CODE -eq 0 ] && echo '✓ SUCCESS' || echo '✗ FAILED')"
log "DIMS: $([ $DIMS_EXIT_CODE -eq 0 ] && echo '✓ SUCCESS' || echo '⚠ WARNING')"
log "Reconciliation: ✓ AUTOMATIC (via ADCE autonomous loop)"
log "Log: $LOG_FILE"
log ""
log "Data Location:"
log "  S3: s3://nba-sim-raw-data-lake/basketball_reference/"
log ""
log "Next Steps:"
log "  1. Verify S3 uploads: aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | tail -20"
log "  2. Check DIMS metrics: python scripts/monitoring/dims_cli.py show --category basketball_reference_comprehensive"
log "  3. Monitor reconciliation: tail -f logs/autonomous_loop.log"
log "========================================================================"

exit 0

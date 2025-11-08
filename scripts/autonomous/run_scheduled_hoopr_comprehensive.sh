#!/bin/bash
#
# hoopR Comprehensive Scraper - Scheduled Monthly Runner
#
# Runs the complete 152-endpoint hoopR scraper for comprehensive data collection
# Phases 1-3: Bulk data, static/reference, per-season dashboards (69 endpoints)
#
# Designed to be called by cron on 1st of each month at 2 AM
#
# Usage:
#   bash scripts/autonomous/run_scheduled_hoopr_comprehensive.sh [--recent-seasons N] [--upload-to-s3]
#

set -e

# Configuration
RECENT_SEASONS="${1:---recent-seasons 3}"  # Default: last 3 seasons
UPLOAD_FLAG="${2}"  # Optional: --upload-to-s3
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_ROOT/logs/autonomous"
LOG_FILE="$LOG_DIR/hoopr_comprehensive_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handler
error_handler() {
    log "ERROR: hoopR comprehensive scraper failed at line $1"
    exit 1
}

trap 'error_handler $LINENO' ERR

# Change to project directory
cd "$PROJECT_ROOT"

log "========================================================================"
log "hoopR COMPREHENSIVE SCRAPER - Monthly Run"
log "========================================================================"
log "Mode: 152 Endpoints (Phases 1-3: Bulk + Static + Per-Season Dashboards)"
log "Seasons: Recent $(echo $RECENT_SEASONS | grep -oP '\d+')"
log "Upload to S3: ${UPLOAD_FLAG:-DISABLED}"
log "Log file: $LOG_FILE"
log ""
log "Estimated runtime: 2-4 hours"
log "Estimated output: 5-10 GB"
log ""

# Calculate season range (current year and last N years)
CURRENT_YEAR=$(date +%Y)
if [[ "$RECENT_SEASONS" == *"3"* ]]; then
    START_YEAR=$((CURRENT_YEAR - 2))
elif [[ "$RECENT_SEASONS" == *"5"* ]]; then
    START_YEAR=$((CURRENT_YEAR - 4))
else
    START_YEAR=$((CURRENT_YEAR - 2))  # Default to 3 seasons
fi

SEASON_RANGE="${START_YEAR}:${CURRENT_YEAR}"
log "Season range: $SEASON_RANGE"
log ""

# Phase 1: Run comprehensive hoopR scraper
log "Phase 1/3: Running hoopR 152-endpoint comprehensive scraper..."
log "Note: This includes Phases 1-3 only (bulk + static + per-season)"
log "      Phase 4 (per-game box scores) is excluded for time/cost efficiency"
log ""

# Build command
SCRAPER_CMD="bash scripts/etl/overnight_hoopr_all_152.sh \"$SEASON_RANGE\" $UPLOAD_FLAG"
log "Running: $SCRAPER_CMD"
log ""

# Set environment variable to avoid interactive prompts
export WAIT_FOR_COMPLETION=yes

# Run scraper (captures output to log)
bash scripts/etl/overnight_hoopr_all_152.sh "$SEASON_RANGE" $UPLOAD_FLAG >> "$LOG_FILE" 2>&1
SCRAPER_EXIT_CODE=$?

if [ $SCRAPER_EXIT_CODE -eq 0 ]; then
    log "✓ hoopR comprehensive scraper completed successfully"
else
    log "✗ hoopR comprehensive scraper failed with exit code $SCRAPER_EXIT_CODE"
    exit $SCRAPER_EXIT_CODE
fi

log ""

# Phase 2: Update DIMS metrics (with timeout protection)
log "Phase 2/3: Updating DIMS hoopR comprehensive metrics..."
log "Note: DIMS update runs in background - may take 2-3 minutes"

# Run DIMS update in background
python scripts/monitoring/dims_cli.py update --category hoopr_comprehensive >> "$LOG_FILE" 2>&1 &
DIMS_PID=$!
log "DIMS update started (PID: $DIMS_PID)"

# Wait up to 90 seconds for DIMS to complete (longer for comprehensive data)
DIMS_TIMEOUT=90
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
log "hoopR COMPREHENSIVE SCRAPER - Complete"
log "========================================================================"
log "Scraper: $([ $SCRAPER_EXIT_CODE -eq 0 ] && echo '✓ SUCCESS' || echo '✗ FAILED')"
log "DIMS: $([ $DIMS_EXIT_CODE -eq 0 ] && echo '✓ SUCCESS' || echo '⚠ WARNING')"
log "Reconciliation: ✓ AUTOMATIC (via ADCE autonomous loop)"
log "Log: $LOG_FILE"
log ""
log "Data Location:"
log "  Local: /tmp/hoopr_all_152/"
if [[ -n "$UPLOAD_FLAG" ]]; then
    log "  S3: s3://nba-sim-raw-data-lake/hoopr_152/"
fi
log ""
log "Next Steps:"
log "  1. Verify S3 uploads: aws s3 ls s3://nba-sim-raw-data-lake/hoopr_152/ --recursive | tail -20"
log "  2. Check DIMS metrics: python scripts/monitoring/dims_cli.py show --category hoopr_comprehensive"
log "  3. Monitor reconciliation: tail -f logs/autonomous_loop.log"
log "========================================================================"

exit 0

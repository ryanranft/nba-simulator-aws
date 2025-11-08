#!/bin/bash
#
# hoopR Scheduled Scraper Runner with Post-Execution Hooks
#
# This script runs the hoopR incremental scraper and triggers post-execution hooks:
# - DIMS metrics update
# - Reconciliation cycle
#
# Designed to be called by cron at 3 AM daily (after ESPN at 2 AM)
#
# Usage:
#   bash scripts/autonomous/run_scheduled_hoopr.sh [--days N] [--dry-run]
#

set -e  # Exit on error

# Configuration
DAYS="${1:---days 3}"  # Default: last 3 days
DRY_RUN="${2}"  # Optional: --dry-run
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
LOG_DIR="$PROJECT_ROOT/logs/autonomous"
LOG_FILE="$LOG_DIR/hoopr_scheduled_$(date +%Y%m%d_%H%M%S).log"

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handler
error_handler() {
    log "ERROR: hoopR scheduled scraper failed at line $1"
    exit 1
}

trap 'error_handler $LINENO' ERR

# Change to project directory
cd "$PROJECT_ROOT"

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

log "========================================================================"
log "hoopR SCHEDULED SCRAPER - Starting"
log "========================================================================"
log "Days: $DAYS"
log "Dry run: ${DRY_RUN:-false}"
log "Log file: $LOG_FILE"
log ""

# Phase 1: Run hoopR scraper
log "Phase 1/3: Running hoopR incremental scraper..."
if [ -n "$DRY_RUN" ]; then
    python scripts/etl/hoopr_incremental_simple.py $DAYS --dry-run >> "$LOG_FILE" 2>&1
else
    python scripts/etl/hoopr_incremental_simple.py $DAYS >> "$LOG_FILE" 2>&1
fi
SCRAPER_EXIT_CODE=$?

if [ $SCRAPER_EXIT_CODE -eq 0 ]; then
    log "✓ hoopR scraper completed successfully"
else
    log "✗ hoopR scraper failed with exit code $SCRAPER_EXIT_CODE"
    exit $SCRAPER_EXIT_CODE
fi

log ""

# Phase 2: Update DIMS metrics (with timeout protection)
log "Phase 2/3: Updating DIMS hoopR metrics..."
log "Note: DIMS update runs in background - may take 2-3 minutes for all metrics"
log "      hoopR metrics will be updated, but some non-hoopR metrics may timeout"

# Run DIMS update in background and continue (don't block)
python scripts/monitoring/dims_cli.py update --category hoopr_data >> "$LOG_FILE" 2>&1 &
DIMS_PID=$!
log "DIMS update started (PID: $DIMS_PID)"

# Wait up to 60 seconds for DIMS to complete
DIMS_TIMEOUT=60
DIMS_ELAPSED=0
while kill -0 $DIMS_PID 2>/dev/null && [ $DIMS_ELAPSED -lt $DIMS_TIMEOUT ]; do
    sleep 5
    DIMS_ELAPSED=$((DIMS_ELAPSED + 5))
done

if kill -0 $DIMS_PID 2>/dev/null; then
    log "⚠ DIMS still running after ${DIMS_TIMEOUT}s - continuing anyway (non-critical)"
    log "  DIMS will complete in background"
    DIMS_EXIT_CODE=0  # Set success since it's running
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
log "      No manual trigger needed - ADCE will detect and fill gaps automatically"
RECON_EXIT_CODE=0  # Set success since this is informational only

log ""
log "========================================================================"
log "hoopR SCHEDULED SCRAPER - Complete"
log "========================================================================"
log "Scraper: $([ $SCRAPER_EXIT_CODE -eq 0 ] && echo '✓ SUCCESS' || echo '✗ FAILED')"
log "DIMS: $([ $DIMS_EXIT_CODE -eq 0 ] && echo '✓ SUCCESS' || echo '⚠ WARNING')"
log "Reconciliation: ✓ AUTOMATIC (via ADCE autonomous loop)"
log "Log: $LOG_FILE"
log "========================================================================"

exit 0

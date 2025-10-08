#!/bin/bash
#
# Overnight hoopR All 152 Endpoints Scraper Runner
#
# This script runs the complete 152-endpoint hoopR scraper overnight with:
# - Process management (PID tracking, graceful shutdown)
# - Comprehensive logging
# - Error handling and recovery
# - S3 upload automation
# - Progress monitoring
#
# Usage:
#   bash scripts/etl/overnight_hoopr_all_152.sh [seasons] [--upload-to-s3]
#
# Examples:
#   # All seasons (2002-2025), no S3 upload
#   bash scripts/etl/overnight_hoopr_all_152.sh
#
#   # Recent 5 seasons (2020-2025) with S3 upload
#   bash scripts/etl/overnight_hoopr_all_152.sh "2020:2025" --upload-to-s3
#
#   # Single season 2024 with S3 upload
#   bash scripts/etl/overnight_hoopr_all_152.sh "2024:2024" --upload-to-s3
#

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="/tmp/hoopr_all_152"
LOG_FILE="/tmp/hoopr_all_152_overnight.log"
PID_FILE="/tmp/hoopr_all_152.pid"
R_SCRIPT="$SCRIPT_DIR/scrape_hoopr_all_152_endpoints.R"
S3_BUCKET="s3://nba-sim-raw-data-lake/hoopr_152"

# Parse arguments
SEASONS="${1:-2002:2025}"  # Default: all seasons
UPLOAD_FLAG=""
if [[ "${2:-}" == "--upload-to-s3" ]]; then
  UPLOAD_FLAG="--upload-to-s3"
fi

# ==============================================================================
# FUNCTIONS
# ==============================================================================

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

cleanup() {
  log "Cleanup: Removing PID file"
  rm -f "$PID_FILE"
}

trap cleanup EXIT INT TERM

check_dependencies() {
  log "Checking dependencies..."

  # Check R
  if ! command -v Rscript &> /dev/null; then
    log "ERROR: Rscript not found. Please install R."
    exit 1
  fi
  log "  ✓ R: $(Rscript --version 2>&1 | head -1)"

  # Check required R packages
  log "  Checking R packages..."
  Rscript -e "
    packages <- c('hoopR', 'dplyr', 'readr', 'purrr', 'lubridate', 'stringr')
    missing <- packages[!sapply(packages, require, character.only = TRUE, quietly = TRUE)]
    if (length(missing) > 0) {
      cat('ERROR: Missing R packages:', paste(missing, collapse = ', '), '\n')
      cat('Install with: install.packages(c(\"', paste(missing, collapse = '\", \"'), '\"))\n', sep = '')
      quit(status = 1)
    } else {
      cat('  ✓ All R packages installed\n')
    }
  " 2>&1 | tee -a "$LOG_FILE"

  if [[ $? -ne 0 ]]; then
    exit 1
  fi

  # Check AWS CLI (only if upload enabled)
  if [[ -n "$UPLOAD_FLAG" ]]; then
    if ! command -v aws &> /dev/null; then
      log "ERROR: AWS CLI not found but --upload-to-s3 specified"
      exit 1
    fi
    log "  ✓ AWS CLI: $(aws --version 2>&1 | head -1)"

    # Test S3 access
    if ! aws s3 ls "$S3_BUCKET" &> /dev/null; then
      log "WARNING: Cannot access S3 bucket $S3_BUCKET"
      log "  Continuing anyway - files will be saved locally"
    else
      log "  ✓ S3 bucket accessible: $S3_BUCKET"
    fi
  fi

  log "  ✓ All dependencies OK"
}

check_disk_space() {
  log "Checking disk space..."

  # Get available space in /tmp (in GB)
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    AVAIL_GB=$(df -g /tmp | awk 'NR==2 {print $4}')
  else
    # Linux
    AVAIL_GB=$(df -BG /tmp | awk 'NR==2 {print $4}' | sed 's/G//')
  fi

  log "  Available space in /tmp: ${AVAIL_GB}G"

  # Estimate required space (conservative estimate)
  # 152 endpoints × 24 seasons × ~5 MB per file = ~18 GB
  REQUIRED_GB=20

  if [[ $AVAIL_GB -lt $REQUIRED_GB ]]; then
    log "WARNING: Low disk space. Required: ${REQUIRED_GB}G, Available: ${AVAIL_GB}G"
    log "  Consider freeing up space or changing OUTPUT_DIR"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  else
    log "  ✓ Sufficient disk space"
  fi
}

show_banner() {
  cat << 'EOF'

================================================================================
🏀 hoopR ALL 152 ENDPOINTS - OVERNIGHT SCRAPER
================================================================================
EOF

  log "Configuration:"
  log "  Seasons:       $SEASONS"
  log "  Output Dir:    $OUTPUT_DIR"
  log "  S3 Upload:     $(if [[ -n "$UPLOAD_FLAG" ]]; then echo "ENABLED"; else echo "DISABLED"; fi)"
  log "  Log File:      $LOG_FILE"
  log "  PID File:      $PID_FILE"
  log ""
  log "Estimated runtime: 10-15 hours (depends on rate limiting and API availability)"
  log "Estimated output size: 15-25 GB"
  log ""
}

estimate_runtime() {
  # Parse season range
  IFS=':' read -r START_YEAR END_YEAR <<< "$SEASONS"
  NUM_SEASONS=$((END_YEAR - START_YEAR + 1))

  # Estimate API calls
  # Phase 1: 4 endpoints × NUM_SEASONS calls = 4 × NUM_SEASONS
  # Phase 2: 25 endpoints × 1 call (static) = 25
  # Phase 3: 40 endpoints × NUM_SEASONS = 40 × NUM_SEASONS
  # Phase 4: 87 endpoints × ~1000 games per season × NUM_SEASONS (sample only in script)
  #
  # For overnight run, we estimate Phase 1-3 only:
  TOTAL_CALLS=$((4 * NUM_SEASONS + 25 + 40 * NUM_SEASONS))

  # With 2.5 second rate limit:
  TOTAL_SECONDS=$((TOTAL_CALLS * 3))  # 3 seconds average (includes retries)
  TOTAL_HOURS=$((TOTAL_SECONDS / 3600))

  log "Estimated API calls: ~$TOTAL_CALLS"
  log "Estimated runtime: ~$TOTAL_HOURS hours (Phases 1-3 only)"
  log "  Phase 1 (Bulk):      ~$(( 4 * NUM_SEASONS * 3 / 60 )) minutes"
  log "  Phase 2 (Static):    ~$(( 25 * 3 / 60 )) minutes"
  log "  Phase 3 (Per-season): ~$(( 40 * NUM_SEASONS * 3 / 3600 )) hours"
  log ""
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
  show_banner
  check_dependencies
  check_disk_space
  estimate_runtime

  # Create output directory
  mkdir -p "$OUTPUT_DIR"

  # Check if already running
  if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
      log "ERROR: Scraper already running (PID $OLD_PID)"
      log "  To stop: kill $OLD_PID"
      log "  To monitor: tail -f $LOG_FILE"
      exit 1
    else
      log "Stale PID file found (process $OLD_PID no longer running), removing..."
      rm -f "$PID_FILE"
    fi
  fi

  # Confirm before starting
  log ""
  log "Ready to start scraping. This will run for several hours."
  read -p "Start overnight scraper? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Cancelled by user"
    exit 0
  fi

  # Start scraper
  log ""
  log "================================================================================"
  log "STARTING SCRAPER"
  log "================================================================================"
  log ""

  # Build command
  CMD="Rscript '$R_SCRIPT' '$OUTPUT_DIR' --seasons=$SEASONS $UPLOAD_FLAG"
  log "Running: $CMD"
  log ""

  # Run in background, save PID
  nohup Rscript "$R_SCRIPT" "$OUTPUT_DIR" "--seasons=$SEASONS" $UPLOAD_FLAG >> "$LOG_FILE" 2>&1 &
  SCRAPER_PID=$!

  echo "$SCRAPER_PID" > "$PID_FILE"
  log "✓ Scraper started (PID $SCRAPER_PID)"
  log ""
  log "================================================================================"
  log "MONITORING COMMANDS"
  log "================================================================================"
  log ""
  log "  View live log:        tail -f $LOG_FILE"
  log "  Check progress:       ls -lh $OUTPUT_DIR/*/ | wc -l"
  log "  Check process:        ps -p $SCRAPER_PID"
  log "  Stop scraper:         kill $SCRAPER_PID"
  log "  Kill scraper:         kill -9 $SCRAPER_PID"
  log ""
  log "  Output directory:     $OUTPUT_DIR"
  log "  PID file:             $PID_FILE"
  log "  Log file:             $LOG_FILE"
  log ""

  # Monitor for first 30 seconds
  log "Monitoring startup (30 seconds)..."
  sleep 5

  if ps -p "$SCRAPER_PID" > /dev/null 2>&1; then
    log "  ✓ Process running OK"
    log ""
    log "Scraper is running in background. Check log for progress:"
    log "  tail -f $LOG_FILE"
    log ""
    log "When complete, check results with:"
    log "  ls -lhR $OUTPUT_DIR"
    log "  du -sh $OUTPUT_DIR"
    log ""
  else
    log "  ✗ Process died during startup!"
    log ""
    log "Last 50 lines of log:"
    tail -50 "$LOG_FILE"
    exit 1
  fi

  # Optional: wait for completion
  if [[ "${WAIT_FOR_COMPLETION:-no}" == "yes" ]]; then
    log "Waiting for completion (this may take hours)..."
    wait "$SCRAPER_PID"
    EXIT_CODE=$?

    if [[ $EXIT_CODE -eq 0 ]]; then
      log "✓ Scraper completed successfully"
    else
      log "✗ Scraper failed with exit code $EXIT_CODE"
      log "Check log: $LOG_FILE"
      exit $EXIT_CODE
    fi
  fi
}

# ==============================================================================
# EXECUTION
# ==============================================================================

main "$@"

#!/bin/bash
# hoopR Daily Collection - Cron Wrapper
# Runs daily hoopR data collection with proper environment setup
#
# Usage:
#   bash scripts/etl/run_hoopr_daily.sh              # Collect yesterday's games
#   bash scripts/etl/run_hoopr_daily.sh --days 3     # Collect last 3 days
#   bash scripts/etl/run_hoopr_daily.sh --dry-run    # Test mode
#
# For cron (runs daily at 6 AM):
#   0 6 * * * /Users/ryanranft/nba-simulator-aws/scripts/etl/run_hoopr_daily.sh >> /Users/ryanranft/nba-simulator-aws/logs/hoopr_daily.log 2>&1
#
# Created: November 9, 2025

set -e  # Exit on error

# ============================================================================
# CONFIGURATION
# ============================================================================

# Project directory
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"

# Conda environment
CONDA_ENV="nba-aws"

# Python script
SCRIPT_PATH="$PROJECT_DIR/scripts/etl/collect_hoopr_daily.py"

# Log directory
LOG_DIR="$PROJECT_DIR/logs/hoopr"
mkdir -p "$LOG_DIR"

# Log file with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/hoopr_daily_$TIMESTAMP.log"

# ============================================================================
# LOGGING SETUP
# ============================================================================

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    echo "$*" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
}

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

log_section "hoopR Daily Collection - $(date)"

log "Setting up environment..."

# Change to project directory
cd "$PROJECT_DIR" || {
    log "ERROR: Cannot change to project directory: $PROJECT_DIR"
    exit 1
}

log "Project directory: $PROJECT_DIR"

# Initialize conda for shell
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    log "Conda initialized"
elif [ -f "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh" ]; then
    source "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
    log "Conda initialized (Homebrew)"
else
    log "ERROR: Cannot find conda initialization script"
    exit 1
fi

# Activate conda environment
conda activate "$CONDA_ENV" || {
    log "ERROR: Cannot activate conda environment: $CONDA_ENV"
    exit 1
}

log "Conda environment activated: $CONDA_ENV"

# Verify Python and dependencies
python --version | tee -a "$LOG_FILE"

# Check if sportsdataverse is installed
if ! python -c "import sportsdataverse" 2>/dev/null; then
    log "ERROR: sportsdataverse not installed in $CONDA_ENV"
    log "Install: pip install sportsdataverse"
    exit 1
fi

log "✅ Environment ready"

# ============================================================================
# RUN COLLECTION
# ============================================================================

log_section "Running hoopR Daily Collection"

# Parse arguments (pass all args to Python script)
PYTHON_ARGS="$@"

if [ -z "$PYTHON_ARGS" ]; then
    log "Mode: Default (collect yesterday's games)"
else
    log "Mode: $PYTHON_ARGS"
fi

# Run Python script
log "Executing: python $SCRIPT_PATH $PYTHON_ARGS"

if python "$SCRIPT_PATH" $PYTHON_ARGS 2>&1 | tee -a "$LOG_FILE"; then
    EXIT_CODE=0
    log "✅ Collection completed successfully"
else
    EXIT_CODE=$?
    log "❌ Collection failed with exit code: $EXIT_CODE"
fi

# ============================================================================
# CLEANUP & SUMMARY
# ============================================================================

log_section "Summary"

# Count log files
LOG_COUNT=$(find "$LOG_DIR" -name "hoopr_daily_*.log" | wc -l)
log "Log files in $LOG_DIR: $LOG_COUNT"

# Cleanup old logs (keep last 30 days)
log "Cleaning up old logs (keeping last 30 days)..."
find "$LOG_DIR" -name "hoopr_daily_*.log" -mtime +30 -delete 2>/dev/null || true

# Final status
if [ $EXIT_CODE -eq 0 ]; then
    log "🎉 hoopR daily collection COMPLETE"
else
    log "💥 hoopR daily collection FAILED"
fi

log "Log saved to: $LOG_FILE"
log_section "Done - $(date)"

exit $EXIT_CODE

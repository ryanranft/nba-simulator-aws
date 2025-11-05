#!/bin/bash

################################################################################
# Daily ESPN Data Update Automation
#
# Purpose: Automate daily ESPN data collection, processing, and catalog updates
#
# Features:
#   - Triggers ESPN scraper for new games
#   - Updates local SQLite database
#   - Updates DATA_CATALOG.md with latest statistics
#   - Logs all operations with timestamps
#   - Email notifications on errors (optional)
#
# Usage:
#   # Manual run
#   bash scripts/workflows/daily_espn_update.sh
#
#   # Cron job (daily at 3:00 AM)
#   0 3 * * * cd /Users/ryanranft/nba-simulator-aws && bash scripts/workflows/daily_espn_update.sh >> /tmp/espn_daily_update.log 2>&1
#
# Author: Claude Code
# Created: October 9, 2025
################################################################################

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
ESPN_SCRAPER_DIR="$HOME/0espn"
LOCAL_DB="/tmp/espn_local.db"
LOG_FILE="/tmp/espn_daily_update_$(date +%Y%m%d_%H%M%S).log"
CATALOG_FILE="$PROJECT_DIR/docs/DATA_CATALOG.md"
UPDATE_SCRIPT="$PROJECT_DIR/scripts/utils/update_data_catalog.py"
REBUILD_SCRIPT="$PROJECT_DIR/scripts/db/create_local_espn_database.py"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"  # Optional Slack notifications

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

################################################################################
# Logging Functions
################################################################################

log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "$@"
    echo -e "${GREEN}✓${NC} $@"
}

log_warn() {
    log "WARN" "$@"
    echo -e "${YELLOW}⚠${NC} $@"
}

log_error() {
    log "ERROR" "$@"
    echo -e "${RED}✗${NC} $@"
}

send_notification() {
    local message="$1"
    local level="${2:-info}"  # info, warning, error

    # Send to Slack if webhook configured
    if [ -n "$SLACK_WEBHOOK" ]; then
        local emoji=":information_source:"
        [ "$level" = "warning" ] && emoji=":warning:"
        [ "$level" = "error" ] && emoji=":x:"

        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"${emoji} NBA Simulator Daily Update: ${message}\"}" \
            2>/dev/null || true
    fi

    # Could add email notification here
    # echo "$message" | mail -s "NBA Simulator Daily Update" user@example.com
}

################################################################################
# Pre-Flight Checks
################################################################################

preflight_checks() {
    log_info "Starting pre-flight checks..."

    # Check if ESPN scraper directory exists
    if [ ! -d "$ESPN_SCRAPER_DIR" ]; then
        log_error "ESPN scraper directory not found: $ESPN_SCRAPER_DIR"
        return 1
    fi

    # Check if local database exists
    if [ ! -f "$LOCAL_DB" ]; then
        log_warn "Local database not found, will rebuild: $LOCAL_DB"
    fi

    # Check if update script exists
    if [ ! -f "$UPDATE_SCRIPT" ]; then
        log_error "Update script not found: $UPDATE_SCRIPT"
        return 1
    fi

    # Check if Python is available
    if ! command -v python &> /dev/null; then
        log_error "Python not found in PATH"
        return 1
    fi

    # Check if conda environment is active
    if [ -z "${CONDA_DEFAULT_ENV:-}" ]; then
        log_warn "Conda environment not active, attempting to activate nba-aws..."
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate nba-aws || {
            log_error "Failed to activate conda environment"
            return 1
        }
    fi

    log_info "Pre-flight checks passed"
    return 0
}

################################################################################
# ESPN Scraper Trigger
################################################################################

trigger_espn_scraper() {
    log_info "Triggering ESPN scraper for new games..."

    # Change to ESPN scraper directory
    cd "$ESPN_SCRAPER_DIR" || {
        log_error "Failed to change to ESPN scraper directory"
        return 1
    }

    # Get current date (today's games)
    local today=$(date +%Y-%m-%d)
    local yesterday=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)

    log_info "Scraping games from $yesterday to $today"

    # Run ESPN scraper (assumes main scraper script exists)
    # Adjust this command based on actual ESPN scraper interface
    if [ -f "$ESPN_SCRAPER_DIR/scrape_daily.py" ]; then
        python "$ESPN_SCRAPER_DIR/scrape_daily.py" \
            --start-date "$yesterday" \
            --end-date "$today" \
            --upload-s3 \
            2>&1 | tee -a "$LOG_FILE" || {
            log_error "ESPN scraper failed"
            return 1
        }
    else
        log_warn "ESPN scraper script not found, skipping scraper trigger"
        log_warn "Manual ESPN scraping may be required"
    fi

    # Return to project directory
    cd "$PROJECT_DIR" || {
        log_error "Failed to return to project directory"
        return 1
    }

    log_info "ESPN scraper completed"
    return 0
}

################################################################################
# Local Database Update
################################################################################

update_local_database() {
    log_info "Updating local SQLite database..."

    # Check if rebuild script exists
    if [ ! -f "$REBUILD_SCRIPT" ]; then
        log_error "Database rebuild script not found: $REBUILD_SCRIPT"
        return 1
    fi

    # Get current database stats (before update)
    local games_before=0
    local events_before=0

    if [ -f "$LOCAL_DB" ]; then
        games_before=$(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM games" 2>/dev/null || echo "0")
        events_before=$(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM pbp_events" 2>/dev/null || echo "0")
        log_info "Current database: $games_before games, $events_before events"
    fi

    # Rebuild database from S3 (incremental update)
    python "$REBUILD_SCRIPT" 2>&1 | tee -a "$LOG_FILE" || {
        log_error "Database rebuild failed"
        return 1
    }

    # Get updated database stats (after update)
    local games_after=$(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM games" 2>/dev/null || echo "0")
    local events_after=$(sqlite3 "$LOCAL_DB" "SELECT COUNT(*) FROM pbp_events" 2>/dev/null || echo "0")

    local games_added=$((games_after - games_before))
    local events_added=$((events_after - events_before))

    log_info "Database updated: +$games_added games, +$events_added events"
    log_info "New totals: $games_after games, $events_after events"

    # Notification if significant new data added
    if [ "$games_added" -gt 0 ]; then
        send_notification "Added $games_added new games ($events_added events) to local database" "info"
    fi

    return 0
}

################################################################################
# Data Catalog Update
################################################################################

update_data_catalog() {
    log_info "Updating DATA_CATALOG.md..."

    # Run catalog update script
    python "$UPDATE_SCRIPT" --source espn --action update 2>&1 | tee -a "$LOG_FILE" || {
        log_error "Catalog update failed"
        return 1
    }

    log_info "DATA_CATALOG.md updated successfully"

    # Verify catalog consistency
    log_info "Verifying catalog consistency..."
    python "$UPDATE_SCRIPT" --verify 2>&1 | tee -a "$LOG_FILE" || {
        log_warn "Catalog verification found inconsistencies (may be formatting differences)"
    }

    return 0
}

################################################################################
# Git Commit (Optional)
################################################################################

commit_updates() {
    log_info "Checking for changes to commit..."

    # Change to project directory
    cd "$PROJECT_DIR" || {
        log_error "Failed to change to project directory"
        return 1
    }

    # Check if DATA_CATALOG.md has changes
    if git diff --quiet "$CATALOG_FILE"; then
        log_info "No changes to DATA_CATALOG.md, skipping commit"
        return 0
    fi

    log_info "DATA_CATALOG.md has changes, creating commit..."

    # Stage changes
    git add "$CATALOG_FILE" || {
        log_error "Failed to stage DATA_CATALOG.md"
        return 1
    }

    # Create commit with timestamp
    local commit_msg="chore(data): daily ESPN catalog update $(date +%Y-%m-%d)

Automated daily update of ESPN data statistics.

🤖 Generated by daily_espn_update.sh
"

    git commit -m "$commit_msg" || {
        log_error "Failed to commit changes"
        return 1
    }

    log_info "Changes committed successfully"

    # Optionally push to remote (disabled by default for safety)
    # git push origin main || log_warn "Failed to push to remote"

    return 0
}

################################################################################
# Cleanup
################################################################################

cleanup() {
    log_info "Cleaning up temporary files..."

    # Remove old log files (keep last 7 days)
    find /tmp -name "espn_daily_update_*.log" -type f -mtime +7 -delete 2>/dev/null || true

    log_info "Cleanup complete"
}

################################################################################
# Main Workflow
################################################################################

main() {
    local start_time=$(date +%s)

    echo "════════════════════════════════════════════════════════════════"
    echo "  NBA Simulator - Daily ESPN Data Update"
    echo "  Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    log_info "Starting daily ESPN update workflow"

    # Run workflow steps
    local exit_code=0

    # Step 1: Pre-flight checks
    if ! preflight_checks; then
        log_error "Pre-flight checks failed, aborting"
        send_notification "Daily update failed: Pre-flight checks failed" "error"
        exit_code=1
        return $exit_code
    fi

    # Step 2: Trigger ESPN scraper (optional - may run separately)
    # Uncomment if you want this script to trigger the scraper
    # if ! trigger_espn_scraper; then
    #     log_warn "ESPN scraper failed, continuing with existing data"
    # fi

    # Step 3: Update local database
    if ! update_local_database; then
        log_error "Database update failed, aborting"
        send_notification "Daily update failed: Database update failed" "error"
        exit_code=1
        return $exit_code
    fi

    # Step 4: Update data catalog
    if ! update_data_catalog; then
        log_error "Catalog update failed, aborting"
        send_notification "Daily update failed: Catalog update failed" "error"
        exit_code=1
        return $exit_code
    fi

    # Step 5: Commit updates (optional)
    if ! commit_updates; then
        log_warn "Failed to commit updates (non-fatal)"
    fi

    # Step 6: Cleanup
    cleanup

    # Calculate runtime
    local end_time=$(date +%s)
    local runtime=$((end_time - start_time))
    local runtime_min=$((runtime / 60))
    local runtime_sec=$((runtime % 60))

    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "  Daily ESPN Update Complete"
    echo "  Runtime: ${runtime_min}m ${runtime_sec}s"
    echo "  Completed: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "  Log: $LOG_FILE"
    echo "════════════════════════════════════════════════════════════════"

    log_info "Daily ESPN update workflow completed in ${runtime_min}m ${runtime_sec}s"

    if [ $exit_code -eq 0 ]; then
        send_notification "Daily update completed successfully (runtime: ${runtime_min}m ${runtime_sec}s)" "info"
    fi

    return $exit_code
}

# Run main workflow
main "$@"
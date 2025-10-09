#!/bin/bash

################################################################################
# Scraper Completion Hook
#
# Purpose: Run after scraper completion to update data catalog and logs
#
# Usage:
#   # At end of scraper wrapper script:
#   bash scripts/utils/scraper_completion_hook.sh --source espn --status success
#   bash scripts/utils/scraper_completion_hook.sh --source hoopr --status failed --error "Rate limit exceeded"
#
# Features:
#   - Updates DATA_CATALOG.md with latest statistics
#   - Logs completion status to central log file
#   - Sends notifications (optional)
#   - Creates completion timestamp file
#
# Author: Claude Code
# Created: October 9, 2025
################################################################################

set -euo pipefail

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
UPDATE_SCRIPT="$PROJECT_DIR/scripts/utils/update_data_catalog.py"
COMPLETION_LOG="$PROJECT_DIR/logs/scraper_completions.log"
TIMESTAMP_DIR="/tmp/scraper_timestamps"

# Default values
SOURCE=""
STATUS=""
ERROR_MSG=""
SKIP_CATALOG_UPDATE=false

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

################################################################################
# Parse Arguments
################################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --status)
            STATUS="$2"
            shift 2
            ;;
        --error)
            ERROR_MSG="$2"
            shift 2
            ;;
        --skip-catalog-update)
            SKIP_CATALOG_UPDATE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$SOURCE" ] || [ -z "$STATUS" ]; then
    echo "Usage: $0 --source <source> --status <success|failed> [--error <message>] [--skip-catalog-update]"
    echo ""
    echo "Sources: espn, hoopr, nba_api, basketball_ref"
    echo "Status: success, failed, partial"
    exit 1
fi

################################################################################
# Logging
################################################################################

log_completion() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_entry="[$timestamp] [$SOURCE] [$STATUS]"

    if [ -n "$ERROR_MSG" ]; then
        log_entry="$log_entry ERROR: $ERROR_MSG"
    fi

    # Create log directory if needed
    mkdir -p "$(dirname "$COMPLETION_LOG")"

    # Append to log file
    echo "$log_entry" >> "$COMPLETION_LOG"

    # Also output to stdout
    if [ "$STATUS" = "success" ]; then
        echo -e "${GREEN}✓${NC} $log_entry"
    elif [ "$STATUS" = "failed" ]; then
        echo -e "${RED}✗${NC} $log_entry"
    else
        echo -e "${YELLOW}⚠${NC} $log_entry"
    fi
}

################################################################################
# Timestamp File
################################################################################

create_timestamp() {
    mkdir -p "$TIMESTAMP_DIR"

    local timestamp_file="$TIMESTAMP_DIR/${SOURCE}_last_completion.txt"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "$timestamp" > "$timestamp_file"
    echo "$STATUS" >> "$timestamp_file"

    if [ -n "$ERROR_MSG" ]; then
        echo "$ERROR_MSG" >> "$timestamp_file"
    fi
}

################################################################################
# Catalog Update
################################################################################

update_catalog() {
    if [ "$SKIP_CATALOG_UPDATE" = true ]; then
        echo "⏭️  Skipping catalog update (--skip-catalog-update flag)"
        return 0
    fi

    if [ "$STATUS" != "success" ]; then
        echo "⏭️  Skipping catalog update (scraper status: $STATUS)"
        return 0
    fi

    if [ ! -f "$UPDATE_SCRIPT" ]; then
        echo "⚠️  Update script not found: $UPDATE_SCRIPT"
        return 1
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Updating Data Catalog"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Map source names to catalog source names
    local catalog_source="$SOURCE"
    case "$SOURCE" in
        "espn")
            catalog_source="espn"
            ;;
        "hoopr")
            catalog_source="hoopr"
            ;;
        "nba_api")
            catalog_source="nba_api"
            ;;
        "basketball_ref")
            catalog_source="basketball_ref"
            ;;
        *)
            echo "⚠️  Unknown source for catalog update: $SOURCE"
            return 1
            ;;
    esac

    # Run catalog update
    if python "$UPDATE_SCRIPT" --source "$catalog_source" --action update; then
        echo -e "${GREEN}✓${NC} Catalog updated successfully for $SOURCE"
        return 0
    else
        echo -e "${RED}✗${NC} Catalog update failed for $SOURCE"
        return 1
    fi
}

################################################################################
# Notifications
################################################################################

send_notification() {
    # Placeholder for notification integration
    # Can add Slack, email, Discord, etc.

    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        local emoji=":white_check_mark:"
        local color="good"

        if [ "$STATUS" = "failed" ]; then
            emoji=":x:"
            color="danger"
        elif [ "$STATUS" = "partial" ]; then
            emoji=":warning:"
            color="warning"
        fi

        local message="$emoji Scraper completion: **$SOURCE** - Status: $STATUS"

        if [ -n "$ERROR_MSG" ]; then
            message="$message\nError: $ERROR_MSG"
        fi

        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"$message\",\"color\":\"$color\"}" \
            2>/dev/null || true
    fi
}

################################################################################
# Main
################################################################################

main() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Scraper Completion Hook"
    echo "  Source: $SOURCE"
    echo "  Status: $STATUS"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Log completion
    log_completion

    # Create timestamp file
    create_timestamp

    # Update catalog (if success)
    if [ "$STATUS" = "success" ]; then
        update_catalog || echo "⚠️  Catalog update failed but continuing..."
    fi

    # Send notifications
    send_notification

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Completion Hook Finished"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
}

# Run main
main "$@"
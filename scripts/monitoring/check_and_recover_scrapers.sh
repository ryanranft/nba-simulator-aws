#!/bin/bash
################################################################################
# Scraper Health Check and Auto-Recovery
#
# Checks status of long-running scrapers and automatically redeploys failed ones
# Designed to run during overnight workflow (3 AM)
#
# Usage:
#   bash scripts/monitoring/check_and_recover_scrapers.sh
#   bash scripts/monitoring/check_and_recover_scrapers.sh --verbose
#
# Version: 1.0
# Created: October 9, 2025
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
LOG_FILE="/tmp/scraper_recovery_$(date +%Y%m%d_%H%M%S).log"
VERBOSE=false

# Parse arguments
if [[ "$1" == "--verbose" ]] || [[ "$1" == "-v" ]]; then
    VERBOSE=true
fi

################################################################################
# Helper Functions
################################################################################

log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOG_FILE"
}

log_verbose() {
    if [[ "$VERBOSE" == true ]]; then
        log "$1"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    fi
}

print_status() {
    local status=$1
    local message=$2

    if [[ "$status" == "SUCCESS" ]]; then
        echo -e "${GREEN}✓${NC} $message" | tee -a "$LOG_FILE"
    elif [[ "$status" == "WARNING" ]]; then
        echo -e "${YELLOW}⚠${NC} $message" | tee -a "$LOG_FILE"
    elif [[ "$status" == "ERROR" ]]; then
        echo -e "${RED}✗${NC} $message" | tee -a "$LOG_FILE"
    else
        echo -e "${BLUE}ℹ${NC} $message" | tee -a "$LOG_FILE"
    fi
}

################################################################################
# Scraper Status Checks
################################################################################

check_bbref_recent() {
    log "Checking Basketball Reference (2020-2025) scraper..."

    if ps aux | grep -q "[s]crape_bbref_incremental.sh 2020 2025"; then
        print_status "SUCCESS" "Basketball Reference (2020-2025): RUNNING"
        return 0
    else
        print_status "WARNING" "Basketball Reference (2020-2025): NOT RUNNING"

        # Check if it completed or failed
        if grep -q "Incremental scraping complete!" /tmp/bbref_2020-2025.log 2>/dev/null; then
            print_status "SUCCESS" "  → Completed successfully"
            return 0
        else
            print_status "ERROR" "  → Failed or interrupted"
            return 1
        fi
    fi
}

check_bbref_historical() {
    log "Checking Basketball Reference (1947-2019) scraper..."

    if ps aux | grep -q "[s]crape_bbref_incremental.sh 1947 2019"; then
        print_status "SUCCESS" "Basketball Reference (1947-2019): RUNNING"
        return 0
    else
        print_status "WARNING" "Basketball Reference (1947-2019): NOT RUNNING"

        # Check if it completed or failed
        if grep -q "Incremental scraping complete!" /tmp/bbref_1947-2019.log 2>/dev/null; then
            print_status "SUCCESS" "  → Completed successfully"
            return 0
        else
            print_status "ERROR" "  → Failed or interrupted"
            return 1
        fi
    fi
}

check_nba_api() {
    log "Checking NBA API scraper..."

    if ps aux | grep -q "[o]vernight_nba_api_test.sh"; then
        print_status "SUCCESS" "NBA API Test: RUNNING"
        return 0
    else
        print_status "WARNING" "NBA API Test: NOT RUNNING"

        # Check if it completed or failed
        if grep -q "NBA Stats API test scraping completed" /tmp/nba_api_test.log 2>/dev/null; then
            print_status "SUCCESS" "  → Completed successfully"
            return 0
        else
            print_status "ERROR" "  → Failed or interrupted"
            return 1
        fi
    fi
}

################################################################################
# Recovery Functions
################################################################################

recover_bbref_recent() {
    log "Recovering Basketball Reference (2020-2025) scraper..."

    # The scraper will automatically resume from checkpoint
    print_status "INFO" "Redeploying from last checkpoint..."

    nohup bash "$PROJECT_DIR/scripts/etl/scrape_bbref_incremental.sh" 2020 2025 > /tmp/bbref_2020-2025_recovered.log 2>&1 &
    local pid=$!

    print_status "SUCCESS" "  → Redeployed with PID: $pid"
    print_status "INFO" "  → Log: /tmp/bbref_2020-2025_recovered.log"

    # Give it a moment to start
    sleep 5

    if ps -p $pid > /dev/null; then
        print_status "SUCCESS" "  → Verified running"
        return 0
    else
        print_status "ERROR" "  → Failed to start"
        return 1
    fi
}

recover_bbref_historical() {
    log "Recovering Basketball Reference (1947-2019) scraper..."

    # The scraper will automatically resume from checkpoint
    print_status "INFO" "Redeploying from last checkpoint..."

    nohup bash "$PROJECT_DIR/scripts/etl/scrape_bbref_incremental.sh" 1947 2019 > /tmp/bbref_1947-2019_recovered.log 2>&1 &
    local pid=$!

    print_status "SUCCESS" "  → Redeployed with PID: $pid"
    print_status "INFO" "  → Log: /tmp/bbref_1947-2019_recovered.log"

    # Give it a moment to start
    sleep 5

    if ps -p $pid > /dev/null; then
        print_status "SUCCESS" "  → Verified running"
        return 0
    else
        print_status "ERROR" "  → Failed to start"
        return 1
    fi
}

recover_nba_api() {
    log "Recovering NBA API scraper..."

    # Determine which season failed
    local last_season=$(grep "🏀 Season" /tmp/nba_api_test.log 2>/dev/null | tail -1 | grep -oE '[0-9]{4}')

    if [[ -n "$last_season" ]]; then
        print_status "INFO" "Last season attempted: $last_season"
        print_status "INFO" "Resuming from season $last_season (may re-scrape some data)"
    fi

    # Restart the test scraper (it will continue from where it left off for each season)
    nohup bash "$PROJECT_DIR/scripts/etl/overnight_nba_api_test.sh" > /tmp/nba_api_test_recovered.log 2>&1 &
    local pid=$!

    print_status "SUCCESS" "  → Redeployed with PID: $pid"
    print_status "INFO" "  → Log: /tmp/nba_api_test_recovered.log"

    # Give it a moment to start
    sleep 5

    if ps -p $pid > /dev/null; then
        print_status "SUCCESS" "  → Verified running"
        return 0
    else
        print_status "ERROR" "  → Failed to start"
        return 1
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    log ""
    log "========================================================================="
    log "SCRAPER HEALTH CHECK AND AUTO-RECOVERY"
    log "========================================================================="
    log ""

    local recovery_needed=false
    local recovery_count=0
    local recovery_success=0

    # Check Basketball Reference (Recent)
    if ! check_bbref_recent; then
        recovery_needed=true
        ((recovery_count++))

        log ""
        log "Attempting recovery for Basketball Reference (2020-2025)..."
        if recover_bbref_recent; then
            ((recovery_success++))
        fi
    fi

    log ""

    # Check Basketball Reference (Historical)
    if ! check_bbref_historical; then
        recovery_needed=true
        ((recovery_count++))

        log ""
        log "Attempting recovery for Basketball Reference (1947-2019)..."
        if recover_bbref_historical; then
            ((recovery_success++))
        fi
    fi

    log ""

    # Check NBA API
    if ! check_nba_api; then
        recovery_needed=true
        ((recovery_count++))

        log ""
        log "Attempting recovery for NBA API..."
        if recover_nba_api; then
            ((recovery_success++))
        fi
    fi

    # Final summary
    log ""
    log "========================================================================="
    log "RECOVERY SUMMARY"
    log "========================================================================="

    if [[ "$recovery_needed" == false ]]; then
        print_status "SUCCESS" "All scrapers healthy - no recovery needed"
    else
        log "Scrapers needing recovery: $recovery_count"
        log "Successful recoveries: $recovery_success"
        log "Failed recoveries: $((recovery_count - recovery_success))"

        if [[ $recovery_success -eq $recovery_count ]]; then
            print_status "SUCCESS" "All failed scrapers successfully recovered"
        elif [[ $recovery_success -gt 0 ]]; then
            print_status "WARNING" "Partial recovery - some scrapers failed to restart"
        else
            print_status "ERROR" "All recovery attempts failed"
        fi
    fi

    log ""
    log "Full log: $LOG_FILE"
    log ""

    # Return appropriate exit code
    if [[ "$recovery_needed" == false ]] || [[ $recovery_success -eq $recovery_count ]]; then
        return 0
    else
        return 1
    fi
}

# Run main function
main

exit $?

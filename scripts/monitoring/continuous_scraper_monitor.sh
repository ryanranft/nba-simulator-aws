#!/bin/bash
################################################################################
# Continuous Scraper Monitor with Auto-Recovery and Duplicate Cleanup
#
# Monitors Basketball Reference and NBA API scrapers every 30 minutes
# Automatically restarts failed scrapers from their last checkpoint
# Detects and kills duplicate scraper processes to prevent rate limit waste
#
# Features:
#   - Health monitoring for all long-running scrapers
#   - Automatic recovery from failures using checkpoint system
#   - Duplicate process detection and cleanup
#   - Progress tracking for each scraper
#   - Detailed logging of all actions
#
# Usage:
#   bash scripts/monitoring/continuous_scraper_monitor.sh
#   bash scripts/monitoring/continuous_scraper_monitor.sh --interval 1800  # 30 min
#   bash scripts/monitoring/continuous_scraper_monitor.sh --interval 600   # 10 min
#
# Background execution (recommended):
#   nohup bash scripts/monitoring/continuous_scraper_monitor.sh > /tmp/continuous_monitor.log 2>&1 &
#
# To stop:
#   ps aux | grep continuous_scraper_monitor.sh
#   kill [PID]
#
# Version: 2.0
# Created: October 9, 2025
# Updated: October 10, 2025 - Added duplicate process cleanup
################################################################################

# Don't use set -e in monitoring script - we want to handle errors gracefully
# set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
CHECK_INTERVAL=1800  # 30 minutes (in seconds)
LOG_FILE="/tmp/continuous_scraper_monitor_$(date +%Y%m%d_%H%M%S).log"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--interval SECONDS]"
            exit 1
            ;;
    esac
done

################################################################################
# Logging Functions
################################################################################

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
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
# Health Check Functions
################################################################################

check_bbref_recent() {
    if ps aux | grep -q "[s]crape_bbref_incremental.sh 2020 2025"; then
        return 0  # Running
    else
        # Check if completed successfully
        if grep -q "Incremental scraping complete!" /tmp/bbref_2020-2025.log 2>/dev/null; then
            return 2  # Completed
        else
            return 1  # Failed
        fi
    fi
}

check_bbref_historical() {
    if ps aux | grep -q "[s]crape_bbref_incremental.sh 1947 2019"; then
        return 0  # Running
    else
        # Check if completed successfully
        if grep -q "Incremental scraping complete!" /tmp/bbref_1947-2019.log 2>/dev/null; then
            return 2  # Completed
        else
            return 1  # Failed
        fi
    fi
}

check_nba_api() {
    if ps aux | grep -q "[o]vernight_nba_api_comprehensive"; then
        return 0  # Running
    else
        # Check if completed successfully
        if grep -q "Comprehensive NBA Stats API scraping completed" /tmp/nba_api_comprehensive.log 2>/dev/null; then
            return 2  # Completed
        else
            return 1  # Failed
        fi
    fi
}

################################################################################
# Duplicate Detection & Cleanup Functions
################################################################################

count_scraper_instances() {
    local pattern=$1
    ps aux | grep "$pattern" | grep -v grep | wc -l | tr -d ' '
}

get_all_pids() {
    local pattern=$1
    # Get PIDs sorted by start time (newest first)
    # Column 2 is PID, Column 9 is start time
    ps aux | grep "$pattern" | grep -v grep | sort -k9 -r | awk '{print $2}'
}

get_newest_pid() {
    local pattern=$1
    get_all_pids "$pattern" | head -1
}

get_old_pids() {
    local pattern=$1
    # Get all PIDs except the newest one
    get_all_pids "$pattern" | tail -n +2
}

kill_old_duplicates() {
    local scraper_name=$1
    local pattern=$2
    local count=$(count_scraper_instances "$pattern")

    if [[ $count -le 1 ]]; then
        return 0  # No duplicates
    fi

    log ""
    print_status "WARNING" "$scraper_name: Found $count instances (expected 1)"

    local newest_pid=$(get_newest_pid "$pattern")
    print_status "INFO" "  → Keeping newest PID: $newest_pid"

    local old_pids=$(get_old_pids "$pattern")
    local killed_count=0

    for pid in $old_pids; do
        print_status "WARNING" "  → Killing old/duplicate PID: $pid"
        if kill $pid 2>/dev/null; then
            ((killed_count++))
            sleep 2
            if ! ps -p $pid > /dev/null 2>&1; then
                print_status "SUCCESS" "    ✓ PID $pid terminated"
            else
                print_status "WARNING" "    ⚠ PID $pid may still be running"
            fi
        else
            print_status "WARNING" "    ⚠ Failed to kill PID $pid (may have already exited)"
        fi
    done

    print_status "SUCCESS" "  → Cleaned up $killed_count duplicate process(es)"
    return 0
}

cleanup_bbref_recent_duplicates() {
    kill_old_duplicates "Basketball Reference (2020-2025)" "[s]crape_bbref_incremental.sh 2020 2025"
}

cleanup_bbref_historical_duplicates() {
    kill_old_duplicates "Basketball Reference (1947-2019)" "[s]crape_bbref_incremental.sh 1947 2019"
}

cleanup_nba_api_duplicates() {
    kill_old_duplicates "NBA API Comprehensive" "python.*scrape_nba_api_comprehensive"
}

################################################################################
# Recovery Functions
################################################################################

recover_bbref_recent() {
    log "RECOVERY: Basketball Reference (2020-2025) - Restarting from checkpoint..."

    # The checkpoint system will automatically skip completed seasons
    nohup bash "$PROJECT_DIR/scripts/etl/scrape_bbref_incremental.sh" 2020 2025 \
        > /tmp/bbref_2020-2025_recovered_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    local pid=$!

    print_status "SUCCESS" "  → Redeployed with PID: $pid"
    print_status "INFO" "  → Will resume from last completed season (checkpoint system)"

    # Verify it started
    sleep 5
    if ps -p $pid > /dev/null; then
        print_status "SUCCESS" "  → Verified running"
        return 0
    else
        print_status "ERROR" "  → Failed to start (check log)"
        return 1
    fi
}

recover_bbref_historical() {
    log "RECOVERY: Basketball Reference (1947-2019) - Restarting from checkpoint..."

    # The checkpoint system will automatically skip completed seasons
    nohup bash "$PROJECT_DIR/scripts/etl/scrape_bbref_incremental.sh" 1947 2019 \
        > /tmp/bbref_1947-2019_recovered_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    local pid=$!

    print_status "SUCCESS" "  → Redeployed with PID: $pid"
    print_status "INFO" "  → Will resume from last completed season (checkpoint system)"

    # Verify it started
    sleep 5
    if ps -p $pid > /dev/null; then
        print_status "SUCCESS" "  → Verified running"
        return 0
    else
        print_status "ERROR" "  → Failed to start (check log)"
        return 1
    fi
}

recover_nba_api() {
    log "RECOVERY: NBA API Comprehensive - Restarting from checkpoint..."

    # Each game/endpoint saves immediately, so re-running is safe
    nohup bash "$PROJECT_DIR/scripts/etl/overnight_nba_api_comprehensive.sh" \
        > /tmp/nba_api_comprehensive_recovered_$(date +%Y%m%d_%H%M%S).log 2>&1 &
    local pid=$!

    print_status "SUCCESS" "  → Redeployed with PID: $pid"
    print_status "INFO" "  → Will skip already-saved games/endpoints"

    # Verify it started
    sleep 5
    if ps -p $pid > /dev/null; then
        print_status "SUCCESS" "  → Verified running"
        return 0
    else
        print_status "ERROR" "  → Failed to start (check log)"
        return 1
    fi
}

################################################################################
# Progress Tracking
################################################################################

get_bbref_recent_progress() {
    # Count completed seasons (each season has 7 data types, 6 for 2020-2025)
    local completed=$(grep -c "Season .* complete" /tmp/bbref_2020-2025.log 2>/dev/null || echo 0)
    local total=6
    echo "$completed/$total seasons"
}

get_bbref_historical_progress() {
    # Count completed seasons (1947-2019 = 73 seasons)
    local completed=$(grep -c "Season .* complete" /tmp/bbref_1947-2019.log 2>/dev/null || echo 0)
    local total=73
    echo "$completed/$total seasons"
}

get_nba_api_progress() {
    # Count completed seasons (30 total: 1996-2025)
    local completed=$(grep -c "✅ Season .* complete" /tmp/nba_api_comprehensive.log 2>/dev/null || echo 0)
    local total=30
    echo "$completed/$total seasons"
}

################################################################################
# Main Monitoring Loop
################################################################################

main() {
    log ""
    log "========================================================================="
    log "CONTINUOUS SCRAPER MONITOR - STARTED"
    log "========================================================================="
    log "Check interval: ${CHECK_INTERVAL}s ($(($CHECK_INTERVAL / 60)) minutes)"
    log "Log file: $LOG_FILE"
    log "Stop with: kill $$"
    log ""

    local iteration=0
    local bbref_recent_completed=false
    local bbref_historical_completed=false
    local nba_api_completed=false

    while true; do
        ((iteration++))

        log ""
        log "========================================================================="
        log "CHECK #$iteration - $(date '+%Y-%m-%d %H:%M:%S')"
        log "========================================================================="
        log ""

        local all_completed=true
        local recovery_needed=false

        # Check Basketball Reference (Recent)
        if [[ "$bbref_recent_completed" == false ]]; then
            # First, clean up any duplicate processes
            cleanup_bbref_recent_duplicates

            check_bbref_recent
            local status=$?

            if [[ $status -eq 0 ]]; then
                print_status "SUCCESS" "Basketball Reference (2020-2025): RUNNING"
                print_status "INFO" "  Progress: $(get_bbref_recent_progress)"
                all_completed=false
            elif [[ $status -eq 2 ]]; then
                print_status "SUCCESS" "Basketball Reference (2020-2025): COMPLETED"
                bbref_recent_completed=true
            else
                print_status "ERROR" "Basketball Reference (2020-2025): FAILED"
                print_status "INFO" "  Last progress: $(get_bbref_recent_progress)"
                recovery_needed=true
                all_completed=false

                if recover_bbref_recent; then
                    print_status "SUCCESS" "  → Recovery successful"
                else
                    print_status "ERROR" "  → Recovery failed, will retry next check"
                fi
            fi
        fi

        log ""

        # Check Basketball Reference (Historical)
        if [[ "$bbref_historical_completed" == false ]]; then
            # First, clean up any duplicate processes
            cleanup_bbref_historical_duplicates

            check_bbref_historical
            local status=$?

            if [[ $status -eq 0 ]]; then
                print_status "SUCCESS" "Basketball Reference (1947-2019): RUNNING"
                print_status "INFO" "  Progress: $(get_bbref_historical_progress)"
                all_completed=false
            elif [[ $status -eq 2 ]]; then
                print_status "SUCCESS" "Basketball Reference (1947-2019): COMPLETED"
                bbref_historical_completed=true
            else
                print_status "ERROR" "Basketball Reference (1947-2019): FAILED"
                print_status "INFO" "  Last progress: $(get_bbref_historical_progress)"
                recovery_needed=true
                all_completed=false

                if recover_bbref_historical; then
                    print_status "SUCCESS" "  → Recovery successful"
                else
                    print_status "ERROR" "  → Recovery failed, will retry next check"
                fi
            fi
        fi

        log ""

        # Check NBA API
        if [[ "$nba_api_completed" == false ]]; then
            # First, clean up any duplicate processes
            cleanup_nba_api_duplicates

            check_nba_api
            local status=$?

            if [[ $status -eq 0 ]]; then
                print_status "SUCCESS" "NBA API Test: RUNNING"
                print_status "INFO" "  Progress: $(get_nba_api_progress)"
                all_completed=false
            elif [[ $status -eq 2 ]]; then
                print_status "SUCCESS" "NBA API Test: COMPLETED"
                nba_api_completed=true
            else
                print_status "ERROR" "NBA API Test: FAILED"
                print_status "INFO" "  Last progress: $(get_nba_api_progress)"
                recovery_needed=true
                all_completed=false

                if recover_nba_api; then
                    print_status "SUCCESS" "  → Recovery successful"
                else
                    print_status "ERROR" "  → Recovery failed, will retry next check"
                fi
            fi
        fi

        # Check if all scrapers completed
        if [[ "$all_completed" == true ]]; then
            log ""
            log "========================================================================="
            log "ALL SCRAPERS COMPLETED - MONITOR STOPPING"
            log "========================================================================="
            log ""
            print_status "SUCCESS" "All scrapers finished successfully!"
            print_status "INFO" "Total checks performed: $iteration"
            print_status "INFO" "Monitor log: $LOG_FILE"
            exit 0
        fi

        # Sleep until next check
        log ""
        if [[ "$recovery_needed" == true ]]; then
            print_status "WARNING" "Recovery attempted - next check in $(($CHECK_INTERVAL / 60)) minutes"
        else
            print_status "INFO" "All active scrapers healthy - next check in $(($CHECK_INTERVAL / 60)) minutes"
        fi

        sleep $CHECK_INTERVAL
    done
}

# Start monitoring
main

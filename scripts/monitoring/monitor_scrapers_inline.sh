#!/bin/bash
#
# Inline Scraper Monitoring Tool
# Displays scraper progress in Claude conversation without clearing screen
# Designed for use within Claude Code sessions
#
# Usage: ./monitor_scrapers_inline.sh [--iterations N]
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Default values
ITERATIONS=1
SLEEP_INTERVAL=30

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        --interval)
            SLEEP_INTERVAL="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--iterations N] [--interval SECONDS]"
            echo "  --iterations: Number of times to display status (default: 1, use -1 for infinite)"
            echo "  --interval: Seconds between updates (default: 30)"
            exit 1
            ;;
    esac
done

# Function to detect all scraper processes
detect_scrapers() {
    ps aux | grep -E "(scrape_|run_hoopr|extract_|load_)" | grep -v grep | grep -v monitor_scrapers
}

# Function to get scraper type from process
get_scraper_type() {
    local cmd="$1"

    if echo "$cmd" | grep -q "scrape_bbref"; then
        echo "Basketball Reference"
    elif echo "$cmd" | grep -q "scrape_basketball_reference"; then
        echo "Basketball Reference"
    elif echo "$cmd" | grep -q "run_hoopr"; then
        echo "hoopR"
    elif echo "$cmd" | grep -q "scrape_hoopr"; then
        echo "hoopR"
    elif echo "$cmd" | grep -q "scrape_nba_api"; then
        echo "NBA API"
    elif echo "$cmd" | grep -q "scrape_sportsdataverse"; then
        echo "SportsDataverse"
    elif echo "$cmd" | grep -q "download_kaggle"; then
        echo "Kaggle Download"
    elif echo "$cmd" | grep -q "extract_"; then
        echo "ETL Extraction"
    elif echo "$cmd" | grep -q "load_"; then
        echo "Database Load"
    else
        echo "Unknown Scraper"
    fi
}

# Function to find log file for a scraper
find_log_file() {
    local cmd="$1"

    if echo "$cmd" | grep -q "scrape_bbref_incremental"; then
        echo "/tmp/bbref_incremental_2020-2025.log"
    elif echo "$cmd" | grep -q "run_hoopr_phase1b"; then
        echo "/tmp/hoopr_phase1b.log"
    elif echo "$cmd" | grep -q "scrape_nba_api_comprehensive"; then
        echo "/tmp/nba_api_comprehensive.log"
    elif echo "$cmd" | grep -q "scrape_sportsdataverse"; then
        echo "/tmp/sportsdataverse.log"
    else
        local logfile=$(echo "$cmd" | grep -oE '/tmp/[a-zA-Z0-9_/-]+\.log' | head -1)
        if [ -n "$logfile" ]; then
            echo "$logfile"
        else
            echo ""
        fi
    fi
}

# Function to get Basketball Reference summary progress
get_bbref_summary() {
    local logfile="$1"

    if [ ! -f "$logfile" ]; then
        echo "❓ Log file not found"
        return
    fi

    local current_season=$(grep "Processing season" "$logfile" | tail -1 | grep -oE "[0-9]{4}")
    local completed_seasons=$(grep "Season .* complete" "$logfile" | grep -oE "Season [0-9]{4}" | wc -l | tr -d ' ')
    local current_task=$(grep "→ Scraping" "$logfile" | tail -1 | sed 's/.*→ Scraping //' | sed 's/ for season.*//')
    local completed_tasks_current=$(grep "✓.*for season $current_season complete" "$logfile" | wc -l | tr -d ' ')

    echo "✅ Completed: $completed_seasons seasons | 🔄 Current: Season $current_season ($completed_tasks_current/7) → $current_task"
}

# Function to get hoopR summary progress
get_hoopr_summary() {
    local logfile="$1"

    if [ ! -f "$logfile" ]; then
        echo "❓ Log file not found"
        return
    fi

    local current_season=$(grep "📅 Season" "$logfile" | tail -1 | grep -oE "[0-9]{4}-[0-9]{2}")
    local completed_count=$(grep -c "📅 Season.*" "$logfile" 2>/dev/null || echo 0)
    local csv_count=$(find /tmp/hoopr_phase1 -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')

    echo "✅ Completed: $completed_count/24 seasons | 🔄 Current: $current_season | 📁 Files: $csv_count"
}

# Function to get summary progress
get_summary_progress() {
    local scraper_type="$1"
    local logfile="$2"

    case "$scraper_type" in
        "Basketball Reference")
            get_bbref_summary "$logfile"
            ;;
        "hoopR")
            get_hoopr_summary "$logfile"
            ;;
        *)
            if [ -f "$logfile" ]; then
                local last_line=$(tail -1 "$logfile" 2>/dev/null | cut -c 1-60)
                echo "📝 $last_line..."
            else
                echo "❓ No log file"
            fi
            ;;
    esac
}

# Function to calculate runtime
get_runtime() {
    local start_time="$1"
    local now=$(date +%s)
    local runtime=$((now - start_time))

    local hours=$((runtime / 3600))
    local minutes=$(((runtime % 3600) / 60))
    local seconds=$((runtime % 60))

    if [ $hours -gt 0 ]; then
        printf "%dh %dm" $hours $minutes
    elif [ $minutes -gt 0 ]; then
        printf "%dm %ds" $minutes $seconds
    else
        printf "%ds" $seconds
    fi
}

# Function to get error count
get_error_count() {
    local logfile="$1"

    if [ -f "$logfile" ]; then
        local errors=$(grep -c -i "error\|failed\|exception" "$logfile" 2>/dev/null || echo 0)
        echo "$errors"
    else
        echo "0"
    fi
}

# Function to display compact status
display_inline_status() {
    local iteration=$1

    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "🔍 Scraper Status Update #$iteration - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════════════════════════════════════════════"

    # Detect running scrapers
    local scrapers=$(detect_scrapers)

    if [ -z "$scrapers" ]; then
        echo "⚠️  No scrapers currently running"
        echo ""
        echo "To start scrapers:"
        echo "  • Basketball Reference: bash scripts/etl/scrape_bbref_incremental.sh 2020 2025"
        echo "  • hoopR Phase 1B:       bash scripts/etl/run_hoopr_phase1b.sh"
        echo "  • NBA API:              bash scripts/etl/overnight_nba_api_comprehensive.sh"
        return
    fi

    # Count active scrapers
    local scraper_count=$(echo "$scrapers" | wc -l | tr -d ' ')
    echo "✅ Active Scrapers: $scraper_count"
    echo ""

    # Display each scraper in compact format
    local counter=1
    while IFS= read -r line; do
        local pid=$(echo "$line" | awk '{print $2}')
        local start_time=$(ps -p $pid -o lstart= 2>/dev/null | xargs -I {} date -j -f "%a %b %d %T %Y" "{}" +%s 2>/dev/null || echo "0")
        local cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
        local scraper_type=$(get_scraper_type "$cmd")
        local logfile=$(find_log_file "$cmd")
        local errors=$(get_error_count "$logfile")
        local summary=$(get_summary_progress "$scraper_type" "$logfile")

        echo "────────────────────────────────────────────────────────────────────────────────"
        echo "[$counter] 🔧 $scraper_type (PID: $pid)"

        if [ "$start_time" != "0" ]; then
            local runtime=$(get_runtime $start_time)
            echo "    ⏱️  Runtime: $runtime"
        fi

        if [ "$errors" != "0" ]; then
            echo "    ⚠️  Errors: $errors"
        fi

        echo "    $summary"

        counter=$((counter + 1))
    done <<< "$scrapers"

    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
}

# Main execution
current_iteration=1

if [ $ITERATIONS -eq -1 ]; then
    # Infinite loop
    echo "🔄 Starting continuous monitoring (Ctrl+C to stop)..."
    while true; do
        display_inline_status $current_iteration
        if [ $current_iteration -gt 1 ]; then
            echo "⏳ Waiting ${SLEEP_INTERVAL}s for next update..."
            sleep $SLEEP_INTERVAL
        else
            sleep $SLEEP_INTERVAL
        fi
        current_iteration=$((current_iteration + 1))
    done
else
    # Fixed number of iterations
    while [ $current_iteration -le $ITERATIONS ]; do
        display_inline_status $current_iteration

        if [ $current_iteration -lt $ITERATIONS ]; then
            echo "⏳ Waiting ${SLEEP_INTERVAL}s for next update..."
            sleep $SLEEP_INTERVAL
        fi

        current_iteration=$((current_iteration + 1))
    done

    echo "✅ Monitoring complete after $ITERATIONS update(s)"
    echo ""
    echo "Commands:"
    echo "  • Run again:          bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 5"
    echo "  • Continuous:         bash scripts/monitoring/monitor_scrapers_inline.sh --iterations -1"
    echo "  • Full dashboard:     bash scripts/monitoring/monitor_scrapers.sh --watch"
fi

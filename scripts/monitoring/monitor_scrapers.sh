#!/bin/bash
#
# Scraper Monitoring Tool
# Automatically detects and monitors all running scraper processes
# Displays detailed progress, completion status, and error detection
#
# Usage: ./monitor_scrapers.sh [--watch] [--interval SECONDS]
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
WATCH_MODE=false
INTERVAL=30

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --watch)
            WATCH_MODE=true
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--watch] [--interval SECONDS]"
            echo "  --watch: Continuously monitor and refresh display"
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

    # Check common log patterns
    if echo "$cmd" | grep -q "scrape_bbref_incremental"; then
        echo "/tmp/bbref_incremental_2020-2025.log"
    elif echo "$cmd" | grep -q "run_hoopr_phase1b"; then
        echo "/tmp/hoopr_phase1b.log"
    elif echo "$cmd" | grep -q "scrape_nba_api_comprehensive"; then
        echo "/tmp/nba_api_comprehensive.log"
    elif echo "$cmd" | grep -q "scrape_sportsdataverse"; then
        echo "/tmp/sportsdataverse.log"
    else
        # Try to extract log file from command line
        local logfile=$(echo "$cmd" | grep -oE '/tmp/[a-zA-Z0-9_/-]+\.log' | head -1)
        if [ -n "$logfile" ]; then
            echo "$logfile"
        else
            echo ""
        fi
    fi
}

# Function to get detailed Basketball Reference progress
get_bbref_detailed_progress() {
    local logfile="$1"

    if [ ! -f "$logfile" ]; then
        echo "Log file not found"
        return
    fi

    # Get current season being processed
    local current_season=$(grep "Processing season" "$logfile" | tail -1 | grep -oE "[0-9]{4}")

    # Get all completed seasons
    local completed_seasons=$(grep "Season .* complete" "$logfile" | grep -oE "Season [0-9]{4}" | awk '{print $2}')

    # Get current data type being scraped
    local current_task=$(grep "→ Scraping" "$logfile" | tail -1 | sed 's/.*→ Scraping //' | sed 's/ for season.*//')

    # Get completed tasks for current season
    local completed_tasks=$(grep "✓.*for season $current_season complete" "$logfile" | sed 's/.*✓ //' | sed 's/ for season.*//')

    echo ""
    echo -e "${CYAN}  Detailed Progress:${NC}"

    if [ -n "$completed_seasons" ]; then
        echo -e "${GREEN}  ✅ Completed Seasons:${NC}"
        while IFS= read -r season; do
            [ -n "$season" ] && echo "     • $season (all 7 data types)"
        done <<< "$completed_seasons"
    fi

    if [ -n "$current_season" ]; then
        echo ""
        echo -e "${YELLOW}  🔄 Current Season: $current_season${NC}"

        if [ -n "$completed_tasks" ]; then
            echo -e "${GREEN}     Completed:${NC}"
            while IFS= read -r task; do
                [ -n "$task" ] && echo "       ✓ $task"
            done <<< "$completed_tasks"
        fi

        if [ -n "$current_task" ]; then
            echo -e "${MAGENTA}     ⏳ Working on: $current_task${NC}"
        fi
    fi
}

# Function to get detailed hoopR progress
get_hoopr_detailed_progress() {
    local logfile="$1"

    if [ ! -f "$logfile" ]; then
        echo "Log file not found"
        return
    fi

    # Get current season being processed
    local current_season=$(grep "📅 Season" "$logfile" | tail -1 | grep -oE "[0-9]{4}-[0-9]{2}")

    # Count completed seasons (those with "✅ teams" for standings)
    local completed_count=$(grep -c "📅 Season.*" "$logfile" 2>/dev/null || echo 0)

    # Get tasks for current season
    local current_block=$(awk "/📅 Season $current_season/,/📅 Season [0-9]/" "$logfile" | head -20)

    echo ""
    echo -e "${CYAN}  Detailed Progress:${NC}"
    echo -e "  📊 Seasons processed: $completed_count / 24"

    if [ -n "$current_season" ]; then
        echo ""
        echo -e "${YELLOW}  🔄 Current Season: $current_season${NC}"

        # Parse completed and pending tasks for current season
        if echo "$current_block" | grep -q "League player stats.*✅"; then
            echo -e "${GREEN}     ✓ League player stats${NC}"
        fi

        if echo "$current_block" | grep -q "League team stats.*✅"; then
            echo -e "${GREEN}     ✓ League team stats${NC}"
        fi

        if echo "$current_block" | grep -q "5-man lineups.*✅"; then
            echo -e "${GREEN}     ✓ 5-man lineups${NC}"
        elif echo "$current_block" | grep -q "5-man lineups"; then
            echo -e "${MAGENTA}     ⏳ 5-man lineups (in progress or skipped)${NC}"
        fi

        if echo "$current_block" | grep -q "Standings.*✅"; then
            echo -e "${GREEN}     ✓ Standings${NC}"
        elif echo "$current_block" | grep -q "Standings"; then
            echo -e "${MAGENTA}     ⏳ Standings (in progress)${NC}"
        fi
    fi

    # Count CSV files created
    local csv_count=$(find /tmp/hoopr_phase1 -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')
    echo ""
    echo -e "  📁 Total CSV files created: ${GREEN}$csv_count${NC}"
}

# Function to get detailed progress based on scraper type
get_detailed_progress() {
    local scraper_type="$1"
    local logfile="$2"

    case "$scraper_type" in
        "Basketball Reference")
            get_bbref_detailed_progress "$logfile"
            ;;
        "hoopR")
            get_hoopr_detailed_progress "$logfile"
            ;;
        *)
            # For other scrapers, show generic progress
            if [ -f "$logfile" ]; then
                local recent_lines=$(tail -5 "$logfile" 2>/dev/null)
                if [ -n "$recent_lines" ]; then
                    echo ""
                    echo -e "${CYAN}  Recent Activity:${NC}"
                    echo "$recent_lines" | while IFS= read -r line; do
                        local short_line=$(echo "$line" | cut -c 1-70)
                        echo "    $short_line"
                    done
                fi
            fi
            ;;
    esac
}

# Function to check for completion markers (summary)
check_completion() {
    local scraper_type="$1"

    case "$scraper_type" in
        "Basketball Reference")
            if [ -d "/tmp/basketball_reference_incremental" ]; then
                local total=$(ls /tmp/basketball_reference_incremental/*.complete 2>/dev/null | wc -l | tr -d ' ')
                echo "$total / 42 tasks"
            else
                echo "0 / 42 tasks"
            fi
            ;;
        "hoopR")
            if [ -d "/tmp/hoopr_phase1" ]; then
                local csv_count=$(find /tmp/hoopr_phase1 -name "*.csv" 2>/dev/null | wc -l | tr -d ' ')
                echo "$csv_count CSV files"
            else
                echo "0 CSV files"
            fi
            ;;
        *)
            echo "N/A"
            ;;
    esac
}

# Function to get error count from log
get_error_count() {
    local logfile="$1"

    if [ -f "$logfile" ]; then
        local errors=$(grep -c -i "error\|failed\|exception" "$logfile" 2>/dev/null || echo 0)
        echo "$errors"
    else
        echo "N/A"
    fi
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

# Function to display scraper status
display_status() {
    clear

    echo "================================================================================"
    echo -e "${CYAN}NBA Simulator - Scraper Monitoring Dashboard${NC}"
    echo "================================================================================"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Detect running scrapers
    local scrapers=$(detect_scrapers)

    if [ -z "$scrapers" ]; then
        echo -e "${YELLOW}No scrapers currently running${NC}"
        echo ""
        echo "To start scrapers, run:"
        echo "  Basketball Reference: bash scripts/etl/scrape_bbref_incremental.sh 2020 2025"
        echo "  hoopR Phase 1B:       bash scripts/etl/run_hoopr_phase1b.sh"
        echo "  NBA API:              bash scripts/etl/overnight_nba_api_comprehensive.sh"
        return
    fi

    # Count active scrapers
    local scraper_count=$(echo "$scrapers" | wc -l | tr -d ' ')
    echo -e "${GREEN}Active Scrapers: $scraper_count${NC}"
    echo ""

    # Display each scraper
    local counter=1
    while IFS= read -r line; do
        local pid=$(echo "$line" | awk '{print $2}')
        local start_time=$(ps -p $pid -o lstart= 2>/dev/null | xargs -I {} date -j -f "%a %b %d %T %Y" "{}" +%s 2>/dev/null || echo "0")
        local cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf $i" "; print ""}')
        local scraper_type=$(get_scraper_type "$cmd")
        local logfile=$(find_log_file "$cmd")
        local completion=$(check_completion "$scraper_type")
        local errors=$(get_error_count "$logfile")

        echo "================================================================================"
        echo -e "${BLUE}[$counter] $scraper_type${NC}"
        echo "================================================================================"
        echo -e "  PID:        $pid"

        if [ "$start_time" != "0" ]; then
            local runtime=$(get_runtime $start_time)
            echo -e "  Runtime:    $runtime"
        fi

        if [ "$completion" != "N/A" ]; then
            echo -e "  Progress:   $completion"
        fi

        if [ "$errors" != "N/A" ] && [ "$errors" != "0" ]; then
            echo -e "  Errors:     ${RED}$errors${NC}"
        elif [ "$errors" = "0" ]; then
            echo -e "  Errors:     ${GREEN}$errors${NC}"
        fi

        if [ -n "$logfile" ]; then
            echo -e "  Log:        $logfile"
        fi

        # Show detailed progress
        get_detailed_progress "$scraper_type" "$logfile"

        echo ""
        counter=$((counter + 1))
    done <<< "$scrapers"

    echo "================================================================================"

    if [ "$WATCH_MODE" = true ]; then
        echo -e "${YELLOW}Refreshing every ${INTERVAL}s... (Ctrl+C to exit)${NC}"
    else
        echo ""
        echo "Commands:"
        echo "  Watch mode:        ./monitor_scrapers.sh --watch"
        echo "  Custom interval:   ./monitor_scrapers.sh --watch --interval 60"
        echo "  View log:          tail -f /tmp/<scraper>.log"
        echo "  Kill scraper:      kill <PID>"
    fi
}

# Main execution
if [ "$WATCH_MODE" = true ]; then
    # Watch mode - continuous monitoring
    while true; do
        display_status
        sleep $INTERVAL
    done
else
    # Single run
    display_status
fi

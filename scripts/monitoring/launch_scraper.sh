#!/bin/bash
#
# Unified Scraper Launcher
# Interactive menu for launching NBA data scrapers
# Automatically validates prerequisites and starts monitoring
#
# Usage: ./launch_scraper.sh
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

# Project root (assuming script is in scripts/monitoring/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "🚀 NBA Scraper Launcher"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${CYAN}🔧 Checking prerequisites...${NC}"

    local all_good=true

    # Check conda environment
    if ! conda info --envs | grep -q "nba-aws"; then
        echo -e "${RED}✗ Conda environment 'nba-aws' not found${NC}"
        all_good=false
    else
        echo -e "${GREEN}✓ Conda environment found${NC}"
    fi

    # Check if activated
    if [[ "$CONDA_DEFAULT_ENV" != "nba-aws" ]]; then
        echo -e "${YELLOW}⚠️  Warning: nba-aws environment not activated${NC}"
        echo -e "${YELLOW}   Run: conda activate nba-aws${NC}"
        all_good=false
    else
        echo -e "${GREEN}✓ Environment activated${NC}"
    fi

    # Check AWS credentials
    if aws s3 ls s3://nba-sim-raw-data-lake/ &>/dev/null; then
        echo -e "${GREEN}✓ AWS credentials valid${NC}"
    else
        echo -e "${RED}✗ AWS credentials not configured or invalid${NC}"
        all_good=false
    fi

    # Check disk space
    local available=$(df -h /tmp | awk 'NR==2 {print $4}')
    echo -e "${GREEN}✓ Disk space available: $available${NC}"

    # Check for running scrapers
    local running_scrapers=$(ps aux | grep -E "(scrape_|run_hoopr)" | grep -v grep | grep -v launch_scraper | wc -l | tr -d ' ')
    if [ "$running_scrapers" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $running_scrapers scraper(s) already running${NC}"
        echo -e "${YELLOW}   Check status: bash scripts/monitoring/monitor_scrapers_inline.sh${NC}"
    fi

    echo ""

    if [ "$all_good" = false ]; then
        echo -e "${RED}Prerequisites not met. Please fix issues above before launching.${NC}"
        exit 1
    fi
}

# Function to create reminder file for daemon
create_reminder() {
    local scraper_name="$1"
    local pid="$2"
    local log_file="$3"
    local estimated_hours="$4"

    # Calculate expected completion time (in seconds)
    local estimated_seconds=$((estimated_hours * 3600))
    local current_time=$(date +%s)
    local expected_completion=$((current_time + estimated_seconds))

    # Create reminder file
    local reminder_file="/tmp/scraper_reminders/$(echo "$scraper_name" | tr ' ' '_')_${pid}.reminder"
    cat > "$reminder_file" <<EOF
SCRAPER: $scraper_name
PID: $pid
LOG: $log_file
START_TIME: $(date '+%Y-%m-%d %H:%M:%S')
EXPECTED_COMPLETION: $expected_completion
ESTIMATED_HOURS: $estimated_hours
EOF

    echo -e "${GREEN}📋 Created completion reminder${NC}"
    echo -e "${GREEN}   Expected finish: $(date -r $expected_completion '+%Y-%m-%d %H:%M:%S')${NC}"
}

# Function to display scraper menu
display_menu() {
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "📊 Available Scrapers"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "  1) Basketball Reference - Recent Seasons (2020-2025)"
    echo "     Coverage: 6 seasons, 7 data types each"
    echo "     Time: ~2-3 hours | Rate: 5s | Status: ✅ Stable"
    echo ""
    echo "  2) Basketball Reference - Historical (2010-2019)"
    echo "     Coverage: 10 seasons, 7 data types each"
    echo "     Time: ~5-7 hours | Rate: 5s | Status: ✅ Stable"
    echo ""
    echo "  3) Basketball Reference - Full Historical (2000-2009)"
    echo "     Coverage: 10 seasons, 7 data types each"
    echo "     Time: ~5-7 hours | Rate: 5s | Status: ✅ Stable"
    echo ""
    echo "  4) Basketball Reference - Custom Range"
    echo "     Coverage: Your choice"
    echo "     Time: Varies | Rate: 5s | Status: ✅ Stable"
    echo ""
    echo "  5) hoopR Phase 1B (League Dashboards)"
    echo "     Coverage: 2002-2025 (24 seasons)"
    echo "     Time: ~30-60 minutes | Rate: Auto | Status: ✅ Stable"
    echo ""
    echo "  6) NBA API Comprehensive (Advanced Stats)"
    echo "     Coverage: 1996-2025 (30 seasons)"
    echo "     Time: ~2-4 hours | Rate: 0.6s | Status: ⚠️  High error rate"
    echo ""
    echo "  7) SportsDataverse"
    echo "     Coverage: 2002+ seasons"
    echo "     Status: 📦 Supplementary"
    echo ""
    echo "  8) Kaggle Datasets"
    echo "     Coverage: Historical pre-packaged data"
    echo "     Status: 📦 One-time download"
    echo ""
    echo "  0) Exit"
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
}

# Function to launch Basketball Reference scraper
launch_bbref() {
    local start_year=$1
    local end_year=$2

    echo ""
    echo -e "${CYAN}🏀 Launching Basketball Reference Scraper${NC}"
    echo -e "${CYAN}   Seasons: $start_year to $end_year${NC}"
    echo ""

    # Create output directory
    mkdir -p /tmp/basketball_reference_incremental

    # Launch scraper
    local log_file="/tmp/bbref_incremental_${start_year}-${end_year}.log"

    nohup bash "$PROJECT_ROOT/scripts/etl/scrape_bbref_incremental.sh" "$start_year" "$end_year" > "$log_file" 2>&1 &
    local pid=$!

    # Calculate estimated time based on number of seasons
    local num_seasons=$((end_year - start_year + 1))
    local estimated_hours=$((num_seasons / 2))

    # Create reminder for daemon
    create_reminder "Basketball Reference ($start_year-$end_year)" "$pid" "$log_file" "$estimated_hours"
    echo ""

    echo -e "${GREEN}✅ Scraper started${NC}"
    echo -e "${GREEN}   PID: $pid${NC}"
    echo -e "${GREEN}   Log: $log_file${NC}"
    echo ""
    echo -e "${YELLOW}Monitor with:${NC}"
    echo -e "  • Quick status:   bash scripts/monitoring/monitor_scrapers_inline.sh"
    echo -e "  • Live tracking:  bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 10"
    echo -e "  • Full dashboard: bash scripts/monitoring/monitor_scrapers.sh --watch"
    echo -e "  • View log:       tail -f $log_file"
    echo ""

    # Offer to start monitoring
    read -p "Start monitoring now? (y/n): " start_monitor
    if [[ "$start_monitor" =~ ^[Yy]$ ]]; then
        echo ""
        bash "$SCRIPT_DIR/monitor_scrapers_inline.sh" --iterations 3 --interval 20
    fi
}

# Function to launch hoopR scraper
launch_hoopr() {
    echo ""
    echo -e "${CYAN}🏀 Launching hoopR Phase 1B Scraper${NC}"
    echo -e "${CYAN}   Seasons: 2002-2025 (24 seasons)${NC}"
    echo ""

    # Create output directory
    mkdir -p /tmp/hoopr_phase1

    # Launch scraper
    local log_file="/tmp/hoopr_phase1b.log"

    nohup bash "$PROJECT_ROOT/scripts/etl/run_hoopr_phase1b.sh" > "$log_file" 2>&1 &
    local pid=$!

    # Create reminder for daemon (estimated 1 hour)
    create_reminder "hoopR Phase 1B" "$pid" "$log_file" "1"
    echo ""

    echo -e "${GREEN}✅ Scraper started${NC}"
    echo -e "${GREEN}   PID: $pid${NC}"
    echo -e "${GREEN}   Log: $log_file${NC}"
    echo ""
    echo -e "${YELLOW}Monitor with:${NC}"
    echo -e "  • Quick status:   bash scripts/monitoring/monitor_scrapers_inline.sh"
    echo -e "  • View log:       tail -f $log_file"
    echo ""

    # Offer to start monitoring
    read -p "Start monitoring now? (y/n): " start_monitor
    if [[ "$start_monitor" =~ ^[Yy]$ ]]; then
        echo ""
        bash "$SCRIPT_DIR/monitor_scrapers_inline.sh" --iterations 3 --interval 20
    fi
}

# Function to launch NBA API scraper
launch_nba_api() {
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: NBA API scraper currently has high error rate (50-70%)${NC}"
    echo -e "${YELLOW}   Consider waiting for error handling improvements${NC}"
    echo ""
    read -p "Continue anyway? (y/n): " continue_choice

    if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        return
    fi

    echo ""
    echo -e "${CYAN}🏀 Launching NBA API Comprehensive Scraper${NC}"
    echo -e "${CYAN}   Seasons: 1996-2025 (30 seasons)${NC}"
    echo ""

    # Launch scraper
    local log_file="/tmp/nba_api_comprehensive.log"

    nohup bash "$PROJECT_ROOT/scripts/etl/overnight_nba_api_comprehensive.sh" > "$log_file" 2>&1 &
    local pid=$!

    # Create reminder for daemon (estimated 3 hours)
    create_reminder "NBA API Comprehensive" "$pid" "$log_file" "3"
    echo ""

    echo -e "${GREEN}✅ Scraper started${NC}"
    echo -e "${GREEN}   PID: $pid${NC}"
    echo -e "${GREEN}   Log: $log_file${NC}"
    echo ""
    echo -e "${YELLOW}Monitor with:${NC}"
    echo -e "  • Quick status:   bash scripts/monitoring/monitor_scrapers_inline.sh"
    echo -e "  • View log:       tail -f $log_file"
    echo ""
}

# Function to launch SportsDataverse scraper
launch_sportsdataverse() {
    echo ""
    echo -e "${CYAN}🏀 Launching SportsDataverse Scraper${NC}"
    echo ""

    # Launch scraper
    local log_file="/tmp/sportsdataverse.log"

    nohup python "$PROJECT_ROOT/scripts/etl/scrape_sportsdataverse.py" > "$log_file" 2>&1 &
    local pid=$!

    echo -e "${GREEN}✅ Scraper started${NC}"
    echo -e "${GREEN}   PID: $pid${NC}"
    echo -e "${GREEN}   Log: $log_file${NC}"
    echo ""
}

# Function to launch Kaggle download
launch_kaggle() {
    echo ""
    echo -e "${CYAN}📦 Launching Kaggle Dataset Download${NC}"
    echo ""

    # Launch download
    local log_file="/tmp/kaggle_download.log"

    python "$PROJECT_ROOT/scripts/etl/download_kaggle_basketball.py" 2>&1 | tee "$log_file"

    echo ""
    echo -e "${GREEN}✅ Download complete${NC}"
    echo -e "${GREEN}   Log: $log_file${NC}"
    echo ""
}

# Function to get custom year range
get_custom_range() {
    echo ""
    read -p "Enter start year (e.g., 2015): " start_year
    read -p "Enter end year (e.g., 2019): " end_year

    # Validate years
    if ! [[ "$start_year" =~ ^[0-9]{4}$ ]] || ! [[ "$end_year" =~ ^[0-9]{4}$ ]]; then
        echo -e "${RED}Invalid year format. Please use 4-digit years (e.g., 2015).${NC}"
        return 1
    fi

    if [ "$start_year" -gt "$end_year" ]; then
        echo -e "${RED}Start year must be <= end year.${NC}"
        return 1
    fi

    # Calculate estimated time
    local num_seasons=$((end_year - start_year + 1))
    local estimated_hours=$((num_seasons / 2))

    echo ""
    echo -e "${YELLOW}Custom Range Summary:${NC}"
    echo -e "  Seasons: $start_year to $end_year ($num_seasons seasons)"
    echo -e "  Data types: 7 per season"
    echo -e "  Estimated time: ~$estimated_hours hours"
    echo ""

    read -p "Proceed with this range? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        launch_bbref "$start_year" "$end_year"
    else
        echo "Cancelled."
    fi
}

# Main script execution
check_prerequisites

while true; do
    display_menu
    read -p "Select scraper (0-8): " choice

    case $choice in
        1)
            launch_bbref 2020 2025
            break
            ;;
        2)
            launch_bbref 2010 2019
            break
            ;;
        3)
            launch_bbref 2000 2009
            break
            ;;
        4)
            get_custom_range
            break
            ;;
        5)
            launch_hoopr
            break
            ;;
        6)
            launch_nba_api
            break
            ;;
        7)
            launch_sportsdataverse
            break
            ;;
        8)
            launch_kaggle
            break
            ;;
        0)
            echo ""
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please select 0-8.${NC}"
            echo ""
            ;;
    esac
done

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Scraper Launch Complete"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Monitor progress regularly"
echo "  2. Check for errors (should be minimal)"
echo "  3. Verify S3 uploads after completion"
echo "  4. Document results in COMMAND_LOG.md"
echo ""
echo "For complete scraper operations guide:"
echo "  See: docs/claude_workflows/workflow_descriptions/40_scraper_operations_complete.md"
echo ""

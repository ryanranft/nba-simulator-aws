#!/bin/bash
################################################################################
# Overnight Workflow Status Checker
#
# Quick verification script to check if the overnight workflow ran successfully.
# Run this after 3:30 AM to verify the nightly automation.
#
# Usage:
#   bash scripts/monitoring/check_overnight_status.sh
#   bash scripts/monitoring/check_overnight_status.sh --verbose
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
LOG_DIR="$PROJECT_DIR/logs/overnight"
REPORTS_DIR="$PROJECT_DIR/reports"
UNIFIED_DB="/tmp/unified_nba.db"
VERBOSE=false

# Parse arguments
if [[ "$1" == "--verbose" ]] || [[ "$1" == "-v" ]]; then
    VERBOSE=true
fi

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo "========================================================================"
    echo "$1"
    echo "========================================================================"
    echo ""
}

print_status() {
    local status=$1
    local message=$2

    if [[ "$status" == "SUCCESS" ]]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [[ "$status" == "WARNING" ]]; then
        echo -e "${YELLOW}⚠${NC} $message"
    elif [[ "$status" == "ERROR" ]]; then
        echo -e "${RED}✗${NC} $message"
    else
        echo -e "${BLUE}ℹ${NC} $message"
    fi
}

################################################################################
# Check Functions
################################################################################

check_launchd_status() {
    print_header "LAUNCHD STATUS"

    local status=$(launchctl list | grep "nba-simulator" || echo "NOT_FOUND")

    if [[ "$status" == "NOT_FOUND" ]]; then
        print_status "ERROR" "launchd job not loaded"
        echo "  Fix: launchctl load ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist"
        return 1
    fi

    # Parse status (format: PID STATUS LABEL)
    local exit_code=$(echo "$status" | awk '{print $2}')

    if [[ "$exit_code" == "0" ]]; then
        print_status "SUCCESS" "launchd job loaded successfully"
        print_status "SUCCESS" "Last run exit code: 0 (success)"
    elif [[ "$exit_code" == "-" ]] || [[ -z "$exit_code" ]]; then
        print_status "INFO" "launchd job loaded, never run yet"
    else
        print_status "ERROR" "Last run failed with exit code: $exit_code"
        return 1
    fi

    if [[ "$VERBOSE" == true ]]; then
        echo ""
        echo "Full launchd status:"
        echo "$status"
    fi

    return 0
}

check_latest_log() {
    print_header "LATEST WORKFLOW LOG"

    # Find latest log file
    local latest_log=$(ls -t "$LOG_DIR"/overnight_unified_*.log 2>/dev/null | head -1)

    if [[ -z "$latest_log" ]]; then
        print_status "WARNING" "No workflow logs found"
        echo "  Expected location: $LOG_DIR/overnight_unified_*.log"
        return 1
    fi

    # Check if log is from today
    local log_date=$(basename "$latest_log" | grep -oE '[0-9]{8}' | head -1)
    local today=$(date +%Y%m%d)

    if [[ "$log_date" == "$today" ]]; then
        print_status "SUCCESS" "Latest log from TODAY: $(basename $latest_log)"
    else
        print_status "WARNING" "Latest log from: $log_date (not today)"
        print_status "INFO" "Log file: $(basename $latest_log)"
    fi

    # Check if workflow completed
    if grep -q "WORKFLOW COMPLETE" "$latest_log"; then
        print_status "SUCCESS" "Workflow completed successfully"

        # Extract duration
        local duration=$(grep "Total duration:" "$latest_log" | tail -1 | awk -F': ' '{print $2}')
        if [[ -n "$duration" ]]; then
            print_status "INFO" "Runtime: $duration"
        fi
    else
        print_status "ERROR" "Workflow did not complete"
        echo ""
        echo "Last 10 lines of log:"
        tail -10 "$latest_log"
        return 1
    fi

    # Check for errors
    local error_count=$(grep -c "ERROR:" "$latest_log" 2>/dev/null || echo "0" | tr -d '\n')
    error_count=${error_count:-0}  # Default to 0 if empty
    if [[ "$error_count" -gt 0 ]] 2>/dev/null; then
        print_status "WARNING" "Found $error_count error(s) in log"

        if [[ "$VERBOSE" == true ]]; then
            echo ""
            echo "Errors found:"
            grep "ERROR:" "$latest_log"
        fi
    else
        print_status "SUCCESS" "No errors in log"
    fi

    if [[ "$VERBOSE" == true ]]; then
        echo ""
        echo "Full log path: $latest_log"
        echo ""
        echo "Step summary:"
        grep -E "(STEP [0-9]|✓)" "$latest_log" | tail -20
    fi

    return 0
}

check_quality_report() {
    print_header "QUALITY REPORT"

    local today=$(date +%Y%m%d)
    local report_file="$REPORTS_DIR/daily_quality_report_$today.md"

    if [[ -f "$report_file" ]]; then
        print_status "SUCCESS" "Quality report generated: $(basename $report_file)"

        # Extract key statistics
        local total_games=$(grep "Total games:" "$report_file" | grep -oE '[0-9,]+' | head -1 | tr -d ',')
        local dual_source=$(grep "Dual-source games:" "$report_file" | grep -oE '[0-9,]+' | head -1 | tr -d ',')
        local with_disc=$(grep "Games with discrepancies:" "$report_file" | grep -oE '[0-9,]+' | head -1 | tr -d ',')

        if [[ -n "$total_games" ]]; then
            print_status "INFO" "Total games: $total_games"
        fi

        if [[ -n "$dual_source" ]]; then
            local pct=$(echo "scale=1; $dual_source * 100 / $total_games" | bc)
            print_status "INFO" "Dual-source games: $dual_source ($pct%)"
        fi

        if [[ -n "$with_disc" ]]; then
            print_status "INFO" "Games with discrepancies: $with_disc"
        fi

        if [[ "$VERBOSE" == true ]]; then
            echo ""
            echo "Report preview:"
            head -30 "$report_file"
        fi
    else
        print_status "WARNING" "Quality report not found for today"

        # Check for yesterday's report
        local yesterday=$(date -v-1d +%Y%m%d 2>/dev/null || date -d "yesterday" +%Y%m%d 2>/dev/null)
        local yesterday_report="$REPORTS_DIR/daily_quality_report_$yesterday.md"

        if [[ -f "$yesterday_report" ]]; then
            print_status "INFO" "Most recent report: $(basename $yesterday_report)"
        fi

        return 1
    fi

    return 0
}

check_databases() {
    print_header "DATABASE STATUS"

    # Check ESPN database
    if [[ -f "/tmp/espn_local.db" ]]; then
        local espn_games=$(sqlite3 /tmp/espn_local.db "SELECT COUNT(*) FROM games WHERE has_pbp = 1;" 2>/dev/null || echo "ERROR")
        if [[ "$espn_games" != "ERROR" ]]; then
            print_status "SUCCESS" "ESPN database: $espn_games games with PBP"
        else
            print_status "ERROR" "ESPN database: Query failed"
        fi
    else
        print_status "WARNING" "ESPN database not found: /tmp/espn_local.db"
    fi

    # Check hoopR database
    if [[ -f "/tmp/hoopr_local.db" ]]; then
        local hoopr_games=$(sqlite3 /tmp/hoopr_local.db "SELECT COUNT(DISTINCT game_id) FROM play_by_play;" 2>/dev/null || echo "ERROR")
        if [[ "$hoopr_games" != "ERROR" ]]; then
            print_status "SUCCESS" "hoopR database: $hoopr_games games with PBP"
        else
            print_status "ERROR" "hoopR database: Query failed"
        fi
    else
        print_status "WARNING" "hoopR database not found: /tmp/hoopr_local.db"
    fi

    # Check unified database
    if [[ -f "$UNIFIED_DB" ]]; then
        local unified_games=$(sqlite3 "$UNIFIED_DB" "SELECT COUNT(*) FROM source_coverage;" 2>/dev/null || echo "ERROR")
        if [[ "$unified_games" != "ERROR" ]]; then
            print_status "SUCCESS" "Unified database: $unified_games total games"

            # Check last update time
            local db_mtime=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$UNIFIED_DB" 2>/dev/null || stat -c "%y" "$UNIFIED_DB" 2>/dev/null | cut -d'.' -f1)
            if [[ -n "$db_mtime" ]]; then
                print_status "INFO" "Last updated: $db_mtime"
            fi
        else
            print_status "ERROR" "Unified database: Query failed"
        fi
    else
        print_status "WARNING" "Unified database not found: $UNIFIED_DB"
    fi

    return 0
}

check_ml_datasets() {
    print_header "ML DATASETS"

    local ml_dir="$PROJECT_DIR/data/ml_quality"
    local today=$(date +%Y%m%d)

    # Check for today's JSON export
    local json_file="$ml_dir/ml_quality_dataset_$today.json"
    if [[ -f "$json_file" ]]; then
        local size=$(du -h "$json_file" | cut -f1)
        print_status "SUCCESS" "ML dataset (JSON): $size"
    else
        print_status "WARNING" "ML dataset (JSON) not found for today"
    fi

    # Check for today's CSV export
    local csv_file="$ml_dir/ml_quality_dataset_$today.csv"
    if [[ -f "$csv_file" ]]; then
        local size=$(du -h "$csv_file" | cut -f1)
        print_status "SUCCESS" "ML dataset (CSV): $size"
    else
        print_status "WARNING" "ML dataset (CSV) not found for today"
    fi

    # Check for summary
    local summary_file="$ml_dir/ml_quality_summary_$today.md"
    if [[ -f "$summary_file" ]]; then
        print_status "SUCCESS" "ML summary report generated"

        if [[ "$VERBOSE" == true ]]; then
            echo ""
            echo "Summary preview:"
            head -20 "$summary_file"
        fi
    fi

    return 0
}

check_backups() {
    print_header "DATABASE BACKUPS"

    local backup_dir="$PROJECT_DIR/backups/$(date +%Y%m%d)"

    if [[ -d "$backup_dir" ]]; then
        print_status "SUCCESS" "Backup directory exists: $(basename $backup_dir)"

        if [[ -f "$backup_dir/unified_nba.db" ]]; then
            local size=$(du -h "$backup_dir/unified_nba.db" | cut -f1)
            print_status "SUCCESS" "Unified database backed up: $size"
        else
            print_status "WARNING" "Unified database backup not found"
        fi

        # Check backup directory size
        local total_size=$(du -sh "$backup_dir" | cut -f1)
        print_status "INFO" "Total backup size: $total_size"
    else
        print_status "WARNING" "No backup created today"

        # Find latest backup
        local latest_backup=$(ls -td "$PROJECT_DIR/backups"/*/ 2>/dev/null | head -1)
        if [[ -n "$latest_backup" ]]; then
            print_status "INFO" "Latest backup: $(basename $latest_backup)"
        fi
    fi

    return 0
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║  Overnight Workflow Status Checker                                 ║"
    echo "║  $(date '+%Y-%m-%d %H:%M:%S')                                                ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"

    local overall_status=0

    # Run all checks
    check_launchd_status || overall_status=1
    check_latest_log || overall_status=1
    check_quality_report || overall_status=1
    check_databases || overall_status=1
    check_ml_datasets || overall_status=1
    check_backups || overall_status=1

    # Final summary
    print_header "SUMMARY"

    if [[ $overall_status -eq 0 ]]; then
        print_status "SUCCESS" "All checks passed!"
        echo ""
        echo "✅ Overnight workflow is running successfully"
    else
        print_status "WARNING" "Some checks failed or have warnings"
        echo ""
        echo "⚠️  Review warnings above and check log files"
        echo ""
        echo "Troubleshooting:"
        echo "  - View latest log: tail -100 \$(ls -t $LOG_DIR/*.log | head -1)"
        echo "  - Check launchd: launchctl list | grep nba-simulator"
        echo "  - Manual run: bash scripts/workflows/overnight_multi_source_unified.sh"
    fi

    echo ""
    echo "For more details, run with --verbose flag"
    echo ""

    return $overall_status
}

# Run main function
main

#!/bin/bash
#
# Check Basketball Reference Re-scrape Status
#
# Usage:
#   bash scripts/monitoring/check_bbref_rescrape_status.sh
#   bash scripts/monitoring/check_bbref_rescrape_status.sh --watch  # Auto-refresh every 30s
#

WATCH_MODE=false
if [[ "$1" == "--watch" ]]; then
    WATCH_MODE=true
fi

check_status() {
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║     Basketball Reference Re-scrape Status Monitor           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # Check if job is still running
    if ps aux | grep -q "[r]escrape_basketball_reference_failed_years.sh"; then
        JOB_STATUS="🔄 RUNNING"
    else
        JOB_STATUS="✅ COMPLETED (or not started)"
    fi

    echo "Job Status: $JOB_STATUS"
    echo ""

    # Find latest master log
    MASTER_LOG=$(find /tmp/bbref_rescrape_logs/ -name "rescrape_master_*.log" -type f -exec ls -t {} + 2>/dev/null | head -1)

    if [[ -z "$MASTER_LOG" ]]; then
        echo "⚠️  No master log found"
        echo "Expected location: /tmp/bbref_rescrape_logs/rescrape_master_*.log"
        return 1
    fi

    echo "Log file: $MASTER_LOG"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "PROGRESS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Extract progress
    PROGRESS_LINE=$(grep "Progress:" "$MASTER_LOG" | tail -1)
    echo "$PROGRESS_LINE" | sed 's/\[.*\] \[INFO\] //'

    # Calculate percentage
    if echo "$PROGRESS_LINE" | grep -q "Progress:"; then
        COMPLETED=$(echo "$PROGRESS_LINE" | grep -oP '\d+(?=/\d+)')
        TOTAL=$(echo "$PROGRESS_LINE" | grep -oP '/\K\d+')
        PERCENTAGE=$(awk "BEGIN {printf \"%.1f\", ($COMPLETED/$TOTAL)*100}")
        echo "Completion: $PERCENTAGE%"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "RECENT ACTIVITY (Last 10 lines)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -10 "$MASTER_LOG" | sed 's/\[.*\] \[INFO\] /  /' | sed 's/\[.*\] \[SUCCESS\] /✓ /' | sed 's/\[.*\] \[ERROR\] /✗ /' | sed 's/\[.*\] \[WARNING\] /⚠ /'

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STATISTICS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Count successes and failures
    SUCCESS_COUNT=$(grep -c "SUCCESS" "$MASTER_LOG" 2>/dev/null || echo "0")
    ERROR_COUNT=$(grep -c "ERROR" "$MASTER_LOG" 2>/dev/null || echo "0")

    echo "Successful operations: $SUCCESS_COUNT"
    echo "Errors encountered: $ERROR_COUNT"

    # Check for completion
    if grep -q "Re-scrape Complete!" "$MASTER_LOG"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🎉 JOB COMPLETED!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        grep -A 10 "Re-scrape Complete!" "$MASTER_LOG" | sed 's/\[.*\] \[INFO\] //'
        echo ""
        echo "Next steps:"
        echo "1. python scripts/etl/integrate_basketball_reference_aggregate.py"
        echo "2. python scripts/validation/cross_validate_basketball_reference.py"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Main execution
if [[ "$WATCH_MODE" == true ]]; then
    echo "Watch mode enabled. Press Ctrl+C to exit."
    echo ""
    while true; do
        check_status
        sleep 30
    done
else
    check_status
fi

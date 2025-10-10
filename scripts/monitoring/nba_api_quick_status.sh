#!/bin/bash
#
# NBA API Scraper Quick Status Check
#
# Usage:
#   bash scripts/monitoring/nba_api_quick_status.sh
#
# Created: October 10, 2025

echo "================================================"
echo "NBA API Scraper - Quick Status"
echo "================================================"
echo "Time: $(date)"
echo ""

# Check if processes are running
echo "📊 Process Status:"
WRAPPER_PID=$(ps aux | grep "overnight_nba_api_comprehensive.sh" | grep -v grep | awk '{print $2}')
SEASON_PIDS=$(ps aux | grep "scrape_nba_api_comprehensive.py" | grep -v grep | awk '{print $2}')

if [ -n "$WRAPPER_PID" ]; then
    WRAPPER_RUNTIME=$(ps -p "$WRAPPER_PID" -o etime= | tr -d ' ')
    echo "  ✅ Wrapper script: RUNNING (PID $WRAPPER_PID, runtime: $WRAPPER_RUNTIME)"
else
    echo "  ⏸️  Wrapper script: NOT RUNNING"
fi

if [ -n "$SEASON_PIDS" ]; then
    SEASON_COUNT=$(echo "$SEASON_PIDS" | wc -l | tr -d ' ')
    echo "  ✅ Season scrapers: $SEASON_COUNT active"
    for pid in $SEASON_PIDS; do
        RUNTIME=$(ps -p "$pid" -o etime= | tr -d ' ')
        SEASON=$(ps -p "$pid" -o command= | grep -oE "season [0-9]+" | awk '{print $2}')
        echo "     → Season $SEASON (PID $pid, runtime: $RUNTIME)"
    done
else
    echo "  ⏸️  Season scrapers: NONE RUNNING"
fi

echo ""

# File counts
echo "📁 Local Files:"
if [ -d "/tmp/nba_api_comprehensive" ]; then
    TOTAL_FILES=$(find /tmp/nba_api_comprehensive -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    echo "  Total: $TOTAL_FILES files"

    # Show breakdown by category
    for dir in /tmp/nba_api_comprehensive/*/; do
        if [ -d "$dir" ]; then
            CATEGORY=$(basename "$dir")
            if [ "$CATEGORY" != ".checkpoints" ]; then
                COUNT=$(find "$dir" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
                if [ "$COUNT" -gt 0 ]; then
                    printf "  %-25s %6s files\n" "$CATEGORY:" "$COUNT"
                fi
            fi
        fi
    done
else
    echo "  ⚠️  Output directory not found"
fi

echo ""

# Checkpoints
echo "✅ Completed Seasons:"
if [ -d "/tmp/nba_api_comprehensive/.checkpoints" ]; then
    CHECKPOINT_COUNT=$(find /tmp/nba_api_comprehensive/.checkpoints -name "*.complete" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$CHECKPOINT_COUNT" -gt 0 ]; then
        echo "  $CHECKPOINT_COUNT seasons completed"
        find /tmp/nba_api_comprehensive/.checkpoints -name "*.complete" 2>/dev/null | while read cp; do
            SEASON=$(basename "$cp" .complete | sed 's/season_//')
            echo "  ✅ Season $SEASON"
        done
    else
        echo "  No seasons fully completed yet (in progress)"
    fi
else
    echo "  No checkpoint directory (scraper not yet using new system)"
fi

echo ""

# S3 files
echo "☁️  S3 Status:"
S3_COUNT=$(aws s3 ls s3://nba-sim-raw-data-lake/nba_api_comprehensive/ --recursive 2>/dev/null | wc -l | tr -d ' ')
if [ "$S3_COUNT" -gt 0 ]; then
    echo "  Total files: $S3_COUNT"

    # Last uploaded file
    LAST_UPLOAD=$(aws s3 ls s3://nba-sim-raw-data-lake/nba_api_comprehensive/ --recursive 2>/dev/null | tail -1 | awk '{print $1" "$2}')
    echo "  Last upload: $LAST_UPLOAD"
else
    echo "  ⚠️  No files in S3 or access error"
fi

echo ""

# Log status
echo "📋 Recent Activity (last 10 lines):"
if [ -f "/tmp/nba_api_comprehensive.log" ]; then
    tail -10 /tmp/nba_api_comprehensive.log | grep -E "Progress|Season|complete|Starting|Error" | tail -5
else
    echo "  ⚠️  Log file not found"
fi

echo ""
echo "================================================"
echo "For detailed monitoring:"
echo "  tail -f /tmp/nba_api_comprehensive.log"
echo ""
echo "To validate data:"
echo "  python scripts/utils/validate_nba_api_files.py"
echo "================================================"

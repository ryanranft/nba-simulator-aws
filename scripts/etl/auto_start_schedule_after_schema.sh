#!/bin/bash
#
# Auto-start enhanced schedule extraction after schema update completes
#
# This script monitors the schema update process and automatically starts
# the enhanced schedule extraction once all 25 columns have been added.
#

SCHEMA_PID=51309
SCHEMA_LOG="schema_update.log"
SCHEDULE_LOG="extract_schedule_full_1993_2025.log"
SCHEDULE_PID_FILE="extract_schedule_full.pid"
CHECK_INTERVAL=60  # Check every 60 seconds

echo "=========================================="
echo "Auto-Start Schedule Extraction Monitor"
echo "=========================================="
echo "Started: $(date)"
echo "Schema PID: $SCHEMA_PID"
echo "Checking every $CHECK_INTERVAL seconds"
echo ""

while true; do
    # Check if schema process is still running
    if ! ps -p $SCHEMA_PID > /dev/null 2>&1; then
        echo "[$(date +%H:%M:%S)] Schema process $SCHEMA_PID no longer running"

        # Check if schema completed successfully
        if grep -q "Successfully added 25/25 columns" "$SCHEMA_LOG"; then
            echo "✅ Schema update completed successfully!"
            echo "✅ All 25 columns added to games table"
            echo ""
            echo "Starting enhanced schedule extraction..."

            # Source credentials and start enhanced schedule extraction
            source /Users/ryanranft/nba-sim-credentials.env && \
            nohup python -u scripts/etl/extract_schedule_local.py --year-range 1993-2025 \
            > "$SCHEDULE_LOG" 2>&1 & \
            echo $! > "$SCHEDULE_PID_FILE"

            SCHEDULE_PID=$(cat "$SCHEDULE_PID_FILE")
            echo "✅ Enhanced schedule extraction started (PID: $SCHEDULE_PID)"
            echo "✅ Log file: $SCHEDULE_LOG"
            echo ""
            echo "Monitor with: tail -f $SCHEDULE_LOG"
            echo ""
            echo "All extractions now running:"
            ps aux | grep python | grep extract | grep -v grep
            exit 0
        else
            echo "❌ Schema update process ended but did not complete successfully"
            echo "❌ Check $SCHEMA_LOG for errors"
            echo ""
            echo "Last 20 lines of schema log:"
            tail -20 "$SCHEMA_LOG"
            exit 1
        fi
    fi

    # Schema process still running - check progress
    COLUMNS_ADDED=$(grep -c "✓ Added" "$SCHEMA_LOG")
    echo "[$(date +%H:%M:%S)] Schema update in progress: $COLUMNS_ADDED/25 columns added"

    sleep $CHECK_INTERVAL
done
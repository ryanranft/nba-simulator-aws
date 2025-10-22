#!/bin/bash

# Phase 9 Master Completion Agent Deployment Script
# Automatically completes all remaining Phase 9 sub-phases (9.3-9.8)

# Configuration
AGENT_NAME="Phase 9 Master Completion Agent"
SCRIPT_PATH="scripts/pbp_to_boxscore/phase_9_master_agent.py"
LOG_FILE="logs/phase_9_master_agent.log"
OUT_FILE="logs/phase_9_master_agent.out"
PID_FILE="tmp/phase_9_master_agent.pid"
OUTPUT_DIR="/tmp/phase_9_master"

# Ensure directories exist
mkdir -p logs
mkdir -p tmp
mkdir -p "$OUTPUT_DIR"

# Function to check if the agent is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            return 0 # Running
        else
            return 1 # Not running, stale PID file
        fi
    else
        return 1 # Not running, no PID file
    fi
}

# Function to start the agent
start_agent() {
    echo -e "\033[0;34m[INFO]\033[0m Starting $AGENT_NAME..."

    if is_running; then
        echo -e "\033[0;33m[WARNING]\033[0m $AGENT_NAME is already running (PID: $(cat "$PID_FILE"))."
        exit 0
    else
        if [ -f "$PID_FILE" ]; then
            echo -e "\033[0;34m[INFO]\033[0m Removing stale PID file"
            rm "$PID_FILE"
        fi

        echo -e "\033[0;34m[INFO]\033[0m Checking prerequisites..."

        # Check Python
        if ! command -v python3 &> /dev/null; then
            echo -e "\033[0;31m[ERROR]\033[0m python3 is not installed. Please install it to run the agent."
            exit 1
        fi

        # Check required packages
        python3 -c "import boto3, psycopg2, pandas, numpy" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo -e "\033[0;31m[ERROR]\033[0m Required Python packages missing. Please install: boto3, psycopg2, pandas, numpy"
            exit 1
        fi

        # Check RDS credentials
        if [ ! -f "/Users/ryanranft/nba-sim-credentials.env" ]; then
            echo -e "\033[1;33m[WARNING]\033[0m RDS credentials file not found - agent may not be able to connect to database"
        fi

        echo -e "\033[0;32m[SUCCESS]\033[0m Prerequisites check passed"

        echo -e "\033[0;34m[INFO]\033[0m Starting $AGENT_NAME..."
        nohup python3 "$SCRIPT_PATH" > "$OUT_FILE" 2>&1 &
        PID=$!
        echo "$PID" > "$PID_FILE"

        # Give it a moment to start
        sleep 3

        if is_running; then
            echo -e "\033[0;32m[SUCCESS]\033[0m $AGENT_NAME started (PID: $PID)"
            echo -e "\033[0;34m[INFO]\033[0m Output directory: $OUTPUT_DIR"
            echo -e "\033[0;34m[INFO]\033[0m Log file: $(pwd)/$LOG_FILE"
            echo -e "\033[0;34m[INFO]\033[0m Standard output: $(pwd)/$OUT_FILE"
            echo ""
            echo -e "\033[0;36m[INFO]\033[0m This agent will complete all remaining Phase 9 sub-phases:"
            echo -e "\033[0;36m[INFO]\033[0m   • 9.3: NBA API Processor (1995-2006)"
            echo -e "\033[0;36m[INFO]\033[0m   • 9.4: Kaggle Processor (1946-2020)"
            echo -e "\033[0;36m[INFO]\033[0m   • 9.5: Storage System (RDS + S3 Parquet + local cache)"
            echo -e "\033[0;36m[INFO]\033[0m   • 9.6: Advanced Metrics Layer (TS%, PER, ORtg, DRtg, Win Probability)"
            echo -e "\033[0;36m[INFO]\033[0m   • 9.7: ML Integration (Temporal features, quarter predictions)"
            echo -e "\033[0;36m[INFO]\033[0m   • 9.8: Betting Integration (Quarter-by-quarter predictions, ROI tracking)"
            echo ""
            echo -e "\033[0;34m[INFO]\033[0m Monitor progress with: $0 status"
        else
            echo -e "\033[0;31m[ERROR]\033[0m Agent failed to start"
            echo -e "\033[0;34m[INFO]\033[0m Check logs for details: tail -f $(pwd)/$OUT_FILE"
            exit 1
        fi
    fi
}

# Function to stop the agent
stop_agent() {
    echo -e "\033[0;34m[INFO]\033[0m Stopping $AGENT_NAME..."
    if is_running; then
        PID=$(cat "$PID_FILE")
        kill "$PID"
        rm "$PID_FILE"
        echo -e "\033[0;32m[SUCCESS]\033[0m $AGENT_NAME (PID: $PID) stopped."
    else
        echo -e "\033[0;33m[WARNING]\033[0m $AGENT_NAME is not running."
        if [ -f "$PID_FILE" ]; then
            rm "$PID_FILE"
            echo -e "\033[0;34m[INFO]\033[0m Removed stale PID file."
        fi
    fi
}

# Function to check agent status
status_agent() {
    echo -e "\033[0;34m[INFO]\033[0m Checking $AGENT_NAME status..."
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "\033[0;32m[SUCCESS]\033[0m Agent is running (PID: $PID)"

        # Show runtime
        START_TIME=$(ps -o lstart= -p "$PID" 2>/dev/null)
        if [ ! -z "$START_TIME" ]; then
            echo -e "\033[0;34m[INFO]\033[0m Started: $START_TIME"
        fi

        # Show output directory contents
        echo -e "\033[0;34m[INFO]\033[0m Output directory contents:"
        if [ -d "$OUTPUT_DIR" ]; then
            ls -la "$OUTPUT_DIR" | head -n 10
        else
            echo "  (Output directory not found)"
        fi

        # Show recent log entries
        echo -e "\033[0;34m[INFO]\033[0m Recent log entries:"
        if [ -f "$OUT_FILE" ]; then
            tail -n 10 "$OUT_FILE" 2>/dev/null || echo "  (Log file not found or empty)"
        else
            echo "  (Log file not found)"
        fi

        # Check for completion report
        if [ -f "$OUTPUT_DIR/phase_9_completion_report.json" ]; then
            echo -e "\033[0;32m[SUCCESS]\033[0m Completion report found!"
            echo -e "\033[0;34m[INFO]\033[0m Report: $OUTPUT_DIR/phase_9_completion_report.json"
        fi

    else
        echo -e "\033[1;33m[WARNING]\033[0m Agent is not running"
        if [ -f "$PID_FILE" ]; then
            echo -e "\033[1;33m[WARNING]\033[0m (stale PID: $(cat "$PID_FILE"))"
        fi

        # Check if there's a completion report
        if [ -f "$OUTPUT_DIR/phase_9_completion_report.json" ]; then
            echo -e "\033[0;32m[SUCCESS]\033[0m Completion report found from previous run!"
            echo -e "\033[0;34m[INFO]\033[0m Report: $OUTPUT_DIR/phase_9_completion_report.json"
        fi
    fi
}

# Function to monitor logs
monitor_agent() {
    echo -e "\033[0;34m[INFO]\033[0m Monitoring $AGENT_NAME logs..."
    if [ -f "$OUT_FILE" ]; then
        tail -f "$OUT_FILE"
    else
        echo -e "\033[0;31m[ERROR]\033[0m Log file not found: $OUT_FILE"
    fi
}

# Function to show completion report
show_report() {
    echo -e "\033[0;34m[INFO]\033[0m Showing Phase 9 completion report..."

    if [ -f "$OUTPUT_DIR/phase_9_completion_report.json" ]; then
        echo -e "\033[0;32m[SUCCESS]\033[0m Completion report found!"
        echo ""
        echo "="*60
        echo "PHASE 9 COMPLETION REPORT"
        echo "="*60

        # Parse and display report
        python3 -c "
import json
import sys
from datetime import datetime

try:
    with open('$OUTPUT_DIR/phase_9_completion_report.json', 'r') as f:
        report = json.load(f)

    print(f\"Completion Time: {report['completion_time']}\")
    print(f\"Duration: {report['duration_minutes']:.1f} minutes\")
    print(f\"Total Phases: {report['summary']['total_phases']}\")
    print(f\"Completed: {report['summary']['completed']}\")
    print(f\"Failed: {report['summary']['failed']}\")
    print(f\"Pending: {report['summary']['pending']}\")
    print()
    print('Phase Status:')
    for phase_id, status in report['phase_status'].items():
        print(f\"  Phase {phase_id}: {status['status'].upper()}\")
        if status['files_created']:
            print(f\"    Files created: {len(status['files_created'])}\")

except Exception as e:
    print(f'Error reading report: {e}')
    sys.exit(1)
"

        echo ""
        echo "="*60

    else
        echo -e "\033[1;33m[WARNING]\033[0m No completion report found."
        echo -e "\033[0;34m[INFO]\033[0m Report location: $OUTPUT_DIR/phase_9_completion_report.json"
        echo -e "\033[0;34m[INFO]\033[0m Run the agent first to generate a report."
    fi
}

# Function to clean up
cleanup() {
    echo -e "\033[0;34m[INFO]\033[0m Cleaning up Phase 9 Master Agent..."

    # Stop agent if running
    if is_running; then
        stop_agent
    fi

    # Remove PID file
    if [ -f "$PID_FILE" ]; then
        rm "$PID_FILE"
        echo -e "\033[0;34m[INFO]\033[0m Removed PID file"
    fi

    # Optionally clean output directory
    if [ -d "$OUTPUT_DIR" ]; then
        echo -e "\033[0;34m[INFO]\033[0m Output directory: $OUTPUT_DIR"
        echo -e "\033[0;34m[INFO]\033[0m (Output directory preserved for inspection)"
    fi

    echo -e "\033[0;32m[SUCCESS]\033[0m Cleanup completed"
}

# Main logic
case "$1" in
    start)
        start_agent
        ;;
    stop)
        stop_agent
        ;;
    restart)
        stop_agent
        sleep 2
        start_agent
        ;;
    status)
        status_agent
        ;;
    monitor)
        monitor_agent
        ;;
    report)
        show_report
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Phase 9 Master Completion Agent"
        echo "================================"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|monitor|report|cleanup}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the Phase 9 Master Completion Agent"
        echo "  stop     - Stop the running agent"
        echo "  restart  - Restart the agent"
        echo "  status   - Check agent status and show progress"
        echo "  monitor  - Monitor agent logs in real-time"
        echo "  report   - Show completion report"
        echo "  cleanup  - Clean up agent files"
        echo ""
        echo "This agent will automatically complete all remaining Phase 9 sub-phases:"
        echo "  • 9.3: NBA API Processor (1995-2006)"
        echo "  • 9.4: Kaggle Processor (1946-2020)"
        echo "  • 9.5: Storage System (RDS + S3 Parquet + local cache)"
        echo "  • 9.6: Advanced Metrics Layer (TS%, PER, ORtg, DRtg, Win Probability)"
        echo "  • 9.7: ML Integration (Temporal features, quarter predictions)"
        echo "  • 9.8: Betting Integration (Quarter-by-quarter predictions, ROI tracking)"
        echo ""
        echo "Output directory: $OUTPUT_DIR"
        echo "Log file: $OUT_FILE"
        exit 1
        ;;
esac








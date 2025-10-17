#!/bin/bash

# Master Data Collection Agent Deployment Script
# Manages the master agent that executes all 8 phases automatically

# Configuration
AGENT_NAME="Master Data Collection Agent"
SCRIPT_PATH="scripts/etl/master_data_collection_agent.py"
LOG_FILE="logs/master_data_collection_agent.log"
OUT_FILE="logs/master_data_collection_agent.out"
PID_FILE="tmp/master_data_collection_agent.pid"
OUTPUT_DIR="/tmp/master_data_collection"

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

# Function to check prerequisites
check_prerequisites() {
    echo -e "\033[0;34m[INFO]\033[0m Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "\033[0;31m[ERROR]\033[0m python3 is not installed. Please install it to run the agent."
        return 1
    fi

    # Check nba_api
    if ! python3 -c "import nba_api" 2>/dev/null; then
        echo -e "\033[1;33m[WARNING]\033[0m nba_api not installed. Installing..."
        pip install nba_api
    fi

    # Check requests
    if ! python3 -c "import requests" 2>/dev/null; then
        echo -e "\033[1;33m[WARNING]\033[0m requests not installed. Installing..."
        pip install requests
    fi

    echo -e "\033[0;32m[SUCCESS]\033[0m Prerequisites check passed"
    return 0
}

# Function to start the agent
start_agent() {
    echo -e "\033[0;34m[INFO]\033[0m Starting $AGENT_NAME..."

    if ! check_prerequisites; then
        echo -e "\033[0;31m[ERROR]\033[0m Prerequisites check failed"
        exit 1
    fi

    if is_running; then
        echo -e "\033[0;33m[WARNING]\033[0m $AGENT_NAME is already running (PID: $(cat "$PID_FILE"))."
        exit 0
    else
        if [ -f "$PID_FILE" ]; then
            echo -e "\033[0;34m[INFO]\033[0m Removing stale PID file"
            rm "$PID_FILE"
        fi

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
            echo -e "\033[0;36m[INFO]\033[0m The agent will execute all 8 phases automatically:"
            echo -e "\033[0;36m[INFO]\033[0m 1. NBA API Player Dashboards (8-10 hours)"
            echo -e "\033[0;36m[INFO]\033[0m 2. Fix NBA API Player Tracking (10-12 hours)"
            echo -e "\033[0;36m[INFO]\033[0m 3. NBA API Team Dashboards (1 hour)"
            echo -e "\033[0;36m[INFO]\033[0m 4. NBA API Game-Level Stats (12-15 hours)"
            echo -e "\033[0;36m[INFO]\033[0m 5. NBA API Matchups & Defense (6-8 hours)"
            echo -e "\033[0;36m[INFO]\033[0m 6. Basketball Reference Workaround (8-12 hours)"
            echo -e "\033[0;36m[INFO]\033[0m 7. Basketball Reference Additional (4-6 hours)"
            echo -e "\033[0;36m[INFO]\033[0m 8. ESPN Additional Endpoints (2-3 hours)"
            echo ""
            echo -e "\033[0;36m[INFO]\033[0m Total estimated runtime: 51-67 hours (~2-3 days)"
            echo -e "\033[0;36m[INFO]\033[0m Total features to collect: 135+ features"
            echo ""
            echo -e "\033[0;33m[INFO]\033[0m Use '$0 status' to check progress"
            echo -e "\033[0;33m[INFO]\033[0m Use '$0 monitor' to watch logs in real-time"
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

        # Show recent log entries
        echo -e "\033[0;34m[INFO]\033[0m Recent log entries:"
        tail -n 10 "$OUT_FILE" 2>/dev/null || echo "  (Log file not found or empty)"

        # Show output directory contents
        echo -e "\033[0;34m[INFO]\033[0m Output directory contents:"
        ls -la "$OUTPUT_DIR" | head -n 10

        # Show status file if it exists
        if [ -f "$OUTPUT_DIR/master_agent_status.json" ]; then
            echo -e "\033[0;34m[INFO]\033[0m Current status:"
            python3 -c "
import json
try:
    with open('$OUTPUT_DIR/master_agent_status.json', 'r') as f:
        status = json.load(f)
    print(f'  Completed phases: {status.get(\"completed_phases\", 0)}')
    print(f'  Running phases: {status.get(\"running_phases\", 0)}')
    print(f'  Failed phases: {status.get(\"failed_phases\", 0)}')
    print(f'  Total phases: {status.get(\"total_phases\", 0)}')
except Exception as e:
    print(f'  Could not read status file: {e}')
"
        fi
    else
        echo -e "\033[1;33m[WARNING]\033[0m Agent is not running"
        if [ -f "$PID_FILE" ]; then
            echo -e "\033[1;33m[WARNING]\033[0m (stale PID: $(cat "$PID_FILE"))"
        fi
    fi
}

# Function to monitor logs
monitor_agent() {
    echo -e "\033[0;34m[INFO]\033[0m Monitoring $AGENT_NAME logs (tail -f $OUT_FILE)..."
    echo -e "\033[0;33m[INFO]\033[0m Press Ctrl+C to stop monitoring"
    tail -f "$OUT_FILE"
}

# Function to show progress
progress_agent() {
    echo -e "\033[0;34m[INFO]\033[0m Checking $AGENT_NAME progress..."

    if [ -f "$OUTPUT_DIR/master_agent_status.json" ]; then
        python3 -c "
import json
from datetime import datetime

try:
    with open('$OUTPUT_DIR/master_agent_status.json', 'r') as f:
        status = json.load(f)

    print('=' * 60)
    print('MASTER DATA COLLECTION AGENT PROGRESS')
    print('=' * 60)
    print(f'Timestamp: {status.get(\"timestamp\", \"Unknown\")}')
    print(f'Total phases: {status.get(\"total_phases\", 0)}')
    print(f'Completed phases: {status.get(\"completed_phases\", 0)}')
    print(f'Running phases: {status.get(\"running_phases\", 0)}')
    print(f'Failed phases: {status.get(\"failed_phases\", 0)}')

    if status.get('total_phases', 0) > 0:
        success_rate = (status.get('completed_phases', 0) / status.get('total_phases', 1)) * 100
        print(f'Success rate: {success_rate:.1f}%')

    print('')
    print('Phase Status:')
    phases = status.get('phases', {})
    for phase_id, phase_info in phases.items():
        status_emoji = '✅' if phase_info.get('status') == 'completed' else '🔄' if phase_info.get('status') == 'running' else '❌' if phase_info.get('status') == 'failed' else '⏸️'
        print(f'  {status_emoji} {phase_id}: {phase_info.get(\"status\", \"unknown\")}')

    print('=' * 60)

except Exception as e:
    print(f'Error reading status file: {e}')
"
    else
        echo -e "\033[1;33m[WARNING]\033[0m No status file found. Agent may not be running."
    fi
}

# Function to restart the agent
restart_agent() {
    echo -e "\033[0;34m[INFO]\033[0m Restarting $AGENT_NAME..."
    stop_agent
    sleep 2
    start_agent
}

# Function to show help
show_help() {
    echo "Master Data Collection Agent Management"
    echo "======================================"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|monitor|progress|help}"
    echo ""
    echo "Commands:"
    echo "  start     - Start the master data collection agent"
    echo "  stop      - Stop the master data collection agent"
    echo "  restart   - Restart the master data collection agent"
    echo "  status    - Check the current status of the agent"
    echo "  monitor   - Monitor the agent logs in real-time"
    echo "  progress  - Show detailed progress of all phases"
    echo "  help      - Show this help message"
    echo ""
    echo "The master agent will automatically execute all 8 phases:"
    echo "  1. NBA API Player Dashboards (30-40 features)"
    echo "  2. Fix NBA API Player Tracking (20-30 features)"
    echo "  3. NBA API Team Dashboards (30-40 features)"
    echo "  4. NBA API Game-Level Stats (10-15 features)"
    echo "  5. NBA API Matchups & Defense (15-20 features)"
    echo "  6. Basketball Reference Workaround (47 features)"
    echo "  7. Basketball Reference Additional (30-43 features)"
    echo "  8. ESPN Additional Endpoints (10-15 features)"
    echo ""
    echo "Total: 135+ additional features (38% increase)"
    echo "Runtime: 51-67 hours (~2-3 days continuous)"
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
        restart_agent
        ;;
    status)
        status_agent
        ;;
    monitor)
        monitor_agent
        ;;
    progress)
        progress_agent
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|monitor|progress|help}"
        echo "Use '$0 help' for detailed information"
        exit 1
        ;;
esac


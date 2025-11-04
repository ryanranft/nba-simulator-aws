#!/bin/bash

# Phase 1C Historical Data Collection Agent Deployment Script
# Collects NBA data for 1997-2001 from ESPN and Basketball Reference

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENT_SCRIPT="$SCRIPT_DIR/phase_1c_historical_agent.py"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/logs/phase_1c_agent.pid"
OUTPUT_DIR="/tmp/phase_1c_historical"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Check if required packages are installed
    python3 -c "import aiohttp, ssl, logging, json, pathlib, datetime, typing, sys, os" 2>/dev/null || {
        log_error "Required Python packages are not installed"
        log_info "Please install: pip install aiohttp"
        exit 1
    }

    # Check if agent script exists
    if [ ! -f "$AGENT_SCRIPT" ]; then
        log_error "Agent script not found: $AGENT_SCRIPT"
        exit 1
    fi

    # Create log directory
    mkdir -p "$LOG_DIR"

    log_success "Prerequisites check passed"
}

start_agent() {
    log_info "Starting Phase 1C Historical Agent..."

    # Check if agent is already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warning "Agent is already running (PID: $PID)"
            log_info "Use 'stop' to stop the current agent first"
            exit 1
        else
            log_info "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi

    # Start the agent in background
    cd "$PROJECT_ROOT"
    nohup python3 "$AGENT_SCRIPT" > "$LOG_DIR/phase_1c_agent.out" 2>&1 &
    PID=$!

    # Save PID
    echo "$PID" > "$PID_FILE"

    log_success "Phase 1C Historical Agent started (PID: $PID)"
    log_info "Output directory: $OUTPUT_DIR"
    log_info "Log file: $LOG_DIR/phase_1c_agent.log"
    log_info "Standard output: $LOG_DIR/phase_1c_agent.out"

    # Wait a moment and check if it's still running
    sleep 2
    if ps -p "$PID" > /dev/null 2>&1; then
        log_success "Agent is running successfully"
    else
        log_error "Agent failed to start"
        log_info "Check logs for details: tail -f $LOG_DIR/phase_1c_agent.out"
        exit 1
    fi
}

stop_agent() {
    log_info "Stopping Phase 1C Historical Agent..."

    if [ ! -f "$PID_FILE" ]; then
        log_warning "No PID file found - agent may not be running"
        return 0
    fi

    PID=$(cat "$PID_FILE")

    if ! ps -p "$PID" > /dev/null 2>&1; then
        log_warning "Agent is not running (PID: $PID)"
        rm -f "$PID_FILE"
        return 0
    fi

    # Send TERM signal
    kill -TERM "$PID" 2>/dev/null || {
        log_error "Failed to send TERM signal to PID $PID"
        exit 1
    }

    # Wait for graceful shutdown
    log_info "Waiting for graceful shutdown..."
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            log_success "Agent stopped gracefully"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done

    # Force kill if still running
    log_warning "Force killing agent..."
    kill -KILL "$PID" 2>/dev/null || {
        log_error "Failed to kill PID $PID"
        exit 1
    }

    log_success "Agent stopped"
    rm -f "$PID_FILE"
}

status_agent() {
    log_info "Checking Phase 1C Historical Agent status..."

    if [ ! -f "$PID_FILE" ]; then
        log_warning "No PID file found - agent is not running"
        return 0
    fi

    PID=$(cat "$PID_FILE")

    if ps -p "$PID" > /dev/null 2>&1; then
        log_success "Agent is running (PID: $PID)"

        # Show recent log entries
        if [ -f "$LOG_DIR/phase_1c_agent.log" ]; then
            log_info "Recent log entries:"
            tail -5 "$LOG_DIR/phase_1c_agent.log" | sed 's/^/  /'
        fi

        # Show output directory contents
        if [ -d "$OUTPUT_DIR" ]; then
            log_info "Output directory contents:"
            ls -la "$OUTPUT_DIR" | sed 's/^/  /'
        fi

    else
        log_warning "Agent is not running (stale PID: $PID)"
        rm -f "$PID_FILE"
    fi
}

monitor_agent() {
    log_info "Monitoring Phase 1C Historical Agent..."

    if [ ! -f "$PID_FILE" ]; then
        log_error "Agent is not running"
        exit 1
    fi

    PID=$(cat "$PID_FILE")

    if ! ps -p "$PID" > /dev/null 2>&1; then
        log_error "Agent is not running (PID: $PID)"
        exit 1
    fi

    log_info "Monitoring agent (PID: $PID) - Press Ctrl+C to stop monitoring"
    log_info "Log file: $LOG_DIR/phase_1c_agent.log"

    # Monitor log file
    tail -f "$LOG_DIR/phase_1c_agent.log"
}

show_help() {
    echo "Phase 1C Historical Data Collection Agent"
    echo ""
    echo "Usage: $0 {start|stop|status|monitor|restart|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the historical data collection agent"
    echo "  stop     - Stop the agent"
    echo "  status   - Show agent status and recent activity"
    echo "  monitor  - Monitor agent logs in real-time"
    echo "  restart  - Restart the agent"
    echo "  help     - Show this help message"
    echo ""
    echo "Configuration:"
    echo "  Output directory: $OUTPUT_DIR"
    echo "  Log directory: $LOG_DIR"
    echo "  PID file: $PID_FILE"
    echo ""
    echo "Target seasons: 1997, 1998, 1999, 2000, 2001"
    echo "Data sources: ESPN API, Basketball Reference"
}

# Main script logic
case "${1:-help}" in
    start)
        check_prerequisites
        start_agent
        ;;
    stop)
        stop_agent
        ;;
    status)
        status_agent
        ;;
    monitor)
        monitor_agent
        ;;
    restart)
        stop_agent
        sleep 2
        check_prerequisites
        start_agent
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac











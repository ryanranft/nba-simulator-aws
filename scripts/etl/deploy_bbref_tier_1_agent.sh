#!/bin/bash

# Basketball Reference Tier 1 Agent Deployment Script
# Collects NBA High Value data: Player Game Logs, Play-by-Play, Shot Charts, Player Tracking, Lineup Data

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENT_SCRIPT="$SCRIPT_DIR/bbref_tier_1_agent.py"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/logs/bbref_tier_1_agent.pid"
OUTPUT_DIR="/tmp/bbref_tier_1"

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
    python3 -c "import asyncio, aiohttp, ssl, logging, json, time, pandas, pathlib, datetime, typing, sys, os, collections, re, bs4" 2>/dev/null || {
        log_error "Required Python packages are not installed"
        log_info "Please install: pip install aiohttp pandas beautifulsoup4"
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
    log_info "Starting Basketball Reference Tier 1 Agent..."
    
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
    nohup python3 "$AGENT_SCRIPT" > "$LOG_DIR/bbref_tier_1_agent.out" 2>&1 &
    PID=$!
    
    # Save PID
    echo "$PID" > "$PID_FILE"
    
    log_success "Basketball Reference Tier 1 Agent started (PID: $PID)"
    log_info "Output directory: $OUTPUT_DIR"
    log_info "Log file: $LOG_DIR/bbref_tier_1_agent.log"
    log_info "Standard output: $LOG_DIR/bbref_tier_1_agent.out"
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p "$PID" > /dev/null 2>&1; then
        log_success "Agent is running successfully"
    else
        log_error "Agent failed to start"
        log_info "Check logs for details: tail -f $LOG_DIR/bbref_tier_1_agent.out"
        exit 1
    fi
}

stop_agent() {
    log_info "Stopping Basketball Reference Tier 1 Agent..."
    
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
    log_info "Checking Basketball Reference Tier 1 Agent status..."
    
    if [ ! -f "$PID_FILE" ]; then
        log_warning "No PID file found - agent is not running"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        log_success "Agent is running (PID: $PID)"
        
        # Show recent log entries
        if [ -f "$LOG_DIR/bbref_tier_1_agent.log" ]; then
            log_info "Recent log entries:"
            tail -5 "$LOG_DIR/bbref_tier_1_agent.log" | sed 's/^/  /'
        fi
        
        # Show output directory contents
        if [ -d "$OUTPUT_DIR" ]; then
            log_info "Output directory contents:"
            ls -la "$OUTPUT_DIR" | sed 's/^/  /'
        fi
        
        # Show collection report if available
        if [ -f "$OUTPUT_DIR/bbref_tier_1_report.json" ]; then
            log_info "Collection report summary:"
            python3 -c "
import json
try:
    with open('$OUTPUT_DIR/bbref_tier_1_report.json', 'r') as f:
        report = json.load(f)
    summary = report.get('summary', {})
    print(f'  Player logs collected: {summary.get(\"player_logs_collected\", 0)}')
    print(f'  Play-by-play collected: {summary.get(\"playbyplay_collected\", 0)}')
    print(f'  Shot charts collected: {summary.get(\"shot_charts_collected\", 0)}')
    print(f'  Player tracking collected: {summary.get(\"player_tracking_collected\", 0)}')
    print(f'  Lineup data collected: {summary.get(\"lineup_data_collected\", 0)}')
    print(f'  Total errors: {summary.get(\"total_errors\", 0)}')
    print(f'  Duration: {summary.get(\"collection_duration\", \"Unknown\")}')
except Exception as e:
    print(f'  Error reading report: {e}')
"
        fi
        
    else
        log_warning "Agent is not running (stale PID: $PID)"
        rm -f "$PID_FILE"
    fi
}

monitor_agent() {
    log_info "Monitoring Basketball Reference Tier 1 Agent..."
    
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
    log_info "Log file: $LOG_DIR/bbref_tier_1_agent.log"
    
    # Monitor log file
    tail -f "$LOG_DIR/bbref_tier_1_agent.log"
}

show_help() {
    echo "Basketball Reference Tier 1 Agent"
    echo ""
    echo "Usage: $0 {start|stop|status|monitor|restart|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the Basketball Reference Tier 1 agent"
    echo "  stop     - Stop the agent"
    echo "  status   - Show agent status and collection results"
    echo "  monitor  - Monitor agent logs in real-time"
    echo "  restart  - Restart the agent"
    echo "  help     - Show this help message"
    echo ""
    echo "Configuration:"
    echo "  Output directory: $OUTPUT_DIR"
    echo "  Log directory: $LOG_DIR"
    echo "  PID file: $PID_FILE"
    echo ""
    echo "Tier 1 Data Collection includes:"
    echo "  - Player Game Logs (season & career)"
    echo "  - Play-by-Play Data (event-level detail)"
    echo "  - Shot Chart Data (spatial analysis)"
    echo "  - Player Tracking Data (advanced metrics)"
    echo "  - Lineup Data (combination analysis)"
    echo ""
    echo "Target seasons: 2024, 2023, 2022, 2021, 2020"
    echo "Rate limit: 12 seconds between requests (Basketball Reference requirement)"
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











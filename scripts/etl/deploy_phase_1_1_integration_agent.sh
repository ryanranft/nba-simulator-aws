#!/bin/bash

# Phase 1.1 Multi-Source Integration Agent Deployment Script
# Integrates 209 features from 5 data sources: ESPN, Basketball Reference, NBA.com Stats, Kaggle, Derived

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENT_SCRIPT="$SCRIPT_DIR/phase_1_1_integration_agent.py"
LOG_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/logs/phase_1_1_integration_agent.pid"
OUTPUT_DIR="/tmp/phase_1_1_integration"

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
    python3 -c "import asyncio, aiohttp, ssl, logging, json, time, pandas, psycopg2, pathlib, datetime, typing, sys, os, collections, numpy" 2>/dev/null || {
        log_error "Required Python packages are not installed"
        log_info "Please install: pip install aiohttp pandas psycopg2-binary numpy"
        exit 1
    }
    
    # Check if agent script exists
    if [ ! -f "$AGENT_SCRIPT" ]; then
        log_error "Agent script not found: $AGENT_SCRIPT"
        exit 1
    fi
    
    # Check PostgreSQL connection
    if ! psql -h localhost -U postgres -d nba_simulator -c "SELECT 1;" &> /dev/null; then
        log_warning "PostgreSQL connection failed - agent may not be able to access database"
    fi
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    log_success "Prerequisites check passed"
}

start_agent() {
    log_info "Starting Phase 1.1 Multi-Source Integration Agent..."
    
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
    nohup python3 "$AGENT_SCRIPT" > "$LOG_DIR/phase_1_1_integration_agent.out" 2>&1 &
    PID=$!
    
    # Save PID
    echo "$PID" > "$PID_FILE"
    
    log_success "Phase 1.1 Multi-Source Integration Agent started (PID: $PID)"
    log_info "Output directory: $OUTPUT_DIR"
    log_info "Log file: $LOG_DIR/phase_1_1_integration_agent.log"
    log_info "Standard output: $LOG_DIR/phase_1_1_integration_agent.out"
    
    # Wait a moment and check if it's still running
    sleep 2
    if ps -p "$PID" > /dev/null 2>&1; then
        log_success "Agent is running successfully"
    else
        log_error "Agent failed to start"
        log_info "Check logs for details: tail -f $LOG_DIR/phase_1_1_integration_agent.out"
        exit 1
    fi
}

stop_agent() {
    log_info "Stopping Phase 1.1 Multi-Source Integration Agent..."
    
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
    log_info "Checking Phase 1.1 Multi-Source Integration Agent status..."
    
    if [ ! -f "$PID_FILE" ]; then
        log_warning "No PID file found - agent is not running"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        log_success "Agent is running (PID: $PID)"
        
        # Show recent log entries
        if [ -f "$LOG_DIR/phase_1_1_integration_agent.log" ]; then
            log_info "Recent log entries:"
            tail -5 "$LOG_DIR/phase_1_1_integration_agent.log" | sed 's/^/  /'
        fi
        
        # Show output directory contents
        if [ -d "$OUTPUT_DIR" ]; then
            log_info "Output directory contents:"
            ls -la "$OUTPUT_DIR" | sed 's/^/  /'
        fi
        
        # Show integration report if available
        if [ -f "$OUTPUT_DIR/multi_source_integration_report.json" ]; then
            log_info "Integration report summary:"
            python3 -c "
import json
try:
    with open('$OUTPUT_DIR/multi_source_integration_report.json', 'r') as f:
        report = json.load(f)
    summary = report.get('summary', {})
    print(f'  Total features integrated: {summary.get(\"total_features_integrated\", 0)}')
    print(f'  ESPN features: {summary.get(\"espn_features\", 0)}')
    print(f'  Basketball Reference features: {summary.get(\"basketball_reference_features\", 0)}')
    print(f'  NBA Stats features: {summary.get(\"nba_stats_features\", 0)}')
    print(f'  Kaggle features: {summary.get(\"kaggle_features\", 0)}')
    print(f'  Derived features: {summary.get(\"derived_features\", 0)}')
    print(f'  Total errors: {summary.get(\"total_errors\", 0)}')
    print(f'  Duration: {summary.get(\"integration_duration\", \"Unknown\")}')
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
    log_info "Monitoring Phase 1.1 Multi-Source Integration Agent..."
    
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
    log_info "Log file: $LOG_DIR/phase_1_1_integration_agent.log"
    
    # Monitor log file
    tail -f "$LOG_DIR/phase_1_1_integration_agent.log"
}

show_help() {
    echo "Phase 1.1 Multi-Source Integration Agent"
    echo ""
    echo "Usage: $0 {start|stop|status|monitor|restart|help}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the multi-source integration agent"
    echo "  stop     - Stop the agent"
    echo "  status   - Show agent status and integration results"
    echo "  monitor  - Monitor agent logs in real-time"
    echo "  restart  - Restart the agent"
    echo "  help     - Show this help message"
    echo ""
    echo "Configuration:"
    echo "  Output directory: $OUTPUT_DIR"
    echo "  Log directory: $LOG_DIR"
    echo "  PID file: $PID_FILE"
    echo ""
    echo "Multi-Source Integration includes:"
    echo "  - ESPN data (58 features): Basic box scores, play-by-play"
    echo "  - Basketball Reference (47 features): Advanced metrics"
    echo "  - NBA.com Stats (92 features): Player tracking data"
    echo "  - Kaggle (12 features): Historical data (1946-1998)"
    echo "  - Derived features (20+ features): Efficiency, momentum metrics"
    echo ""
    echo "Target: 209 features from 5 data sources"
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







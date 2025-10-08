#!/bin/bash
#
# Scraper Watcher Daemon
# Persistent background process that monitors scraper completion times
# Creates alerts when scrapers finish, enabling Claude to notify you
#
# Usage:
#   Start: bash scripts/monitoring/scraper_watcher_daemon.sh start
#   Stop:  bash scripts/monitoring/scraper_watcher_daemon.sh stop
#   Status: bash scripts/monitoring/scraper_watcher_daemon.sh status
#

set -e

# Configuration
ALERT_DIR="/tmp/scraper_alerts"
REMINDER_DIR="/tmp/scraper_reminders"
LOG_FILE="/tmp/scraper_watcher_daemon.log"
PID_FILE="/tmp/scraper_watcher_daemon.pid"
CHECK_INTERVAL=300  # 5 minutes

# Create directories
mkdir -p "$ALERT_DIR"
mkdir -p "$REMINDER_DIR"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Function to send macOS notification
send_notification() {
    local title="$1"
    local message="$2"

    osascript -e "display notification \"$message\" with title \"$title\"" 2>/dev/null || true
}

# Function to check if scraper is still running
is_scraper_running() {
    local pid="$1"
    ps -p "$pid" >/dev/null 2>&1
}

# Function to check Basketball Reference scraper
check_bbref_scraper() {
    local reminder_file="$1"

    # Parse reminder file
    local pid=$(grep "^PID:" "$reminder_file" | cut -d: -f2 | tr -d ' ')
    local expected_completion=$(grep "^EXPECTED_COMPLETION:" "$reminder_file" | cut -d: -f2- | tr -d ' ')
    local scraper_name=$(grep "^SCRAPER:" "$reminder_file" | cut -d: -f2-)
    local log_path=$(grep "^LOG:" "$reminder_file" | cut -d: -f2-)

    # Check if scraper is still running
    if is_scraper_running "$pid"; then
        # Still running - check if past expected completion
        local now=$(date +%s)
        if [ "$now" -gt "$expected_completion" ]; then
            log "⚠️  $scraper_name past expected completion but still running"
        fi
    else
        # Scraper finished - check status
        log "✅ $scraper_name completed"

        # Check for errors in log
        local errors=0
        if [ -f "$log_path" ]; then
            errors=$(grep -c -i "error\|failed" "$log_path" 2>/dev/null || echo 0)
        fi

        # Check for completion marker
        local success="unknown"
        if grep -q "complete" "$log_path" 2>/dev/null; then
            success="complete"
        fi

        # Create alert file
        local alert_file="$ALERT_DIR/$(basename "$reminder_file" .reminder).alert"
        cat > "$alert_file" <<EOF
SCRAPER: $scraper_name
COMPLETION_TIME: $(date '+%Y-%m-%d %H:%M:%S')
STATUS: $success
ERRORS: $errors
LOG: $log_path
PID: $pid
EOF

        # Send notification
        if [ "$errors" -eq 0 ]; then
            send_notification "Scraper Complete ✅" "$scraper_name finished successfully"
        else
            send_notification "Scraper Alert ⚠️" "$scraper_name finished with $errors errors"
        fi

        # Remove reminder file
        rm -f "$reminder_file"

        log "📋 Alert created: $alert_file"
    fi
}

# Main monitoring loop
monitor_scrapers() {
    log "🚀 Scraper watcher daemon started (PID: $$)"

    while true; do
        # Check all reminder files
        for reminder_file in "$REMINDER_DIR"/*.reminder; do
            [ -f "$reminder_file" ] || continue

            log "🔍 Checking reminder: $(basename "$reminder_file")"

            # Determine scraper type and check
            if grep -q "Basketball Reference" "$reminder_file" 2>/dev/null; then
                check_bbref_scraper "$reminder_file"
            elif grep -q "hoopR" "$reminder_file" 2>/dev/null; then
                check_bbref_scraper "$reminder_file"  # Same logic works for hoopR
            fi
        done

        # Sleep before next check
        sleep "$CHECK_INTERVAL"
    done
}

# Start daemon
start_daemon() {
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        local old_pid=$(cat "$PID_FILE")
        if ps -p "$old_pid" >/dev/null 2>&1; then
            echo "Scraper watcher daemon already running (PID: $old_pid)"
            return 0
        fi
    fi

    # Start in background
    nohup bash "$0" _run >> "$LOG_FILE" 2>&1 &
    local pid=$!
    echo "$pid" > "$PID_FILE"

    echo "✅ Scraper watcher daemon started (PID: $pid)"
    echo "   Log: $LOG_FILE"
    echo "   Alerts: $ALERT_DIR"
    echo ""
    echo "To stop: bash $0 stop"
}

# Stop daemon
stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️  Scraper watcher daemon not running"
        return 1
    fi

    local pid=$(cat "$PID_FILE")

    if ps -p "$pid" >/dev/null 2>&1; then
        kill "$pid"
        rm -f "$PID_FILE"
        echo "✅ Scraper watcher daemon stopped (PID: $pid)"
    else
        echo "⚠️  Daemon not running (stale PID file removed)"
        rm -f "$PID_FILE"
    fi
}

# Check daemon status
check_status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "❌ Scraper watcher daemon is NOT running"
        return 1
    fi

    local pid=$(cat "$PID_FILE")

    if ps -p "$pid" >/dev/null 2>&1; then
        echo "✅ Scraper watcher daemon is running (PID: $pid)"
        echo "   Log: $LOG_FILE"
        echo "   Alerts: $ALERT_DIR"

        # Show pending reminders
        local reminder_count=$(ls "$REMINDER_DIR"/*.reminder 2>/dev/null | wc -l | tr -d ' ')
        echo "   Monitoring: $reminder_count scraper(s)"

        # Show recent alerts
        local alert_count=$(ls "$ALERT_DIR"/*.alert 2>/dev/null | wc -l | tr -d ' ')
        if [ "$alert_count" -gt 0 ]; then
            echo "   ⏰ Pending alerts: $alert_count"
        fi
    else
        echo "❌ Daemon not running (stale PID file)"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Main command handler
case "${1:-}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    status)
        check_status
        ;;
    _run)
        # Internal: actual monitoring loop
        monitor_scrapers
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        echo ""
        echo "Scraper Watcher Daemon"
        echo "  Monitors scraper completion times and creates alerts"
        echo ""
        echo "Commands:"
        echo "  start  - Start the daemon in background"
        echo "  stop   - Stop the daemon"
        echo "  status - Check daemon status"
        exit 1
        ;;
esac
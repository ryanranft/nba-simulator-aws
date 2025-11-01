#!/bin/bash
#
# Monitor Long-Running Autonomous Loop Test
# Week 2 Day 1 - ADCE Testing
#
# Usage: bash scripts/monitoring/monitor_longrun_test.sh
#

set -e

echo "================================================================================"
echo "LONG-RUNNING TEST MONITOR - $(date)"
echo "================================================================================"
echo ""

# Test start time (set when script first created)
START_TIME="2025-10-30 22:29:00"
echo "Test Start Time: $START_TIME"
echo "Current Time:    $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if autonomous loop is running
echo "--- Process Status ---"
if pgrep -f "autonomous_loop.py" > /dev/null; then
    PID=$(pgrep -f "autonomous_loop.py")
    echo "✅ Autonomous Loop: RUNNING (PID: $PID)"

    # Get process uptime
    ps -p $PID -o etime= | awk '{print "   Uptime: " $1}'

    # Get memory usage
    ps -p $PID -o rss= | awk '{printf "   Memory: %.2f MB\n", $1/1024}'
else
    echo "❌ Autonomous Loop: STOPPED"
fi

if pgrep -f "reconciliation_daemon.py" > /dev/null; then
    PID=$(pgrep -f "reconciliation_daemon.py")
    echo "✅ Reconciliation Daemon: RUNNING (PID: $PID)"
else
    echo "❌ Reconciliation Daemon: STOPPED"
fi

if pgrep -f "scraper_orchestrator.py" > /dev/null; then
    PID=$(pgrep -f "scraper_orchestrator.py")
    echo "✅ Orchestrator: RUNNING (PID: $PID)"
else
    echo "⏹️  Orchestrator: IDLE"
fi
echo ""

# Check log file size
echo "--- Log Files ---"
if [ -f logs/autonomous_loop.log ]; then
    LOG_SIZE=$(du -h logs/autonomous_loop.log | cut -f1)
    LOG_LINES=$(wc -l < logs/autonomous_loop.log)
    echo "Log Size: $LOG_SIZE ($LOG_LINES lines)"
else
    echo "❌ Log file not found"
fi
echo ""

# Check recent errors
echo "--- Recent Errors (last 10) ---"
if [ -f logs/autonomous_loop.log ]; then
    grep -i "error\|failed\|exception" logs/autonomous_loop.log | tail -10 || echo "No errors found"
else
    echo "❌ Log file not found"
fi
echo ""

# Check task queue
echo "--- Task Queue Status ---"
python scripts/autonomous/autonomous_cli.py tasks 2>/dev/null | grep -A 10 "TASK QUEUE" || echo "Could not retrieve task queue"
echo ""

# Check reconciliation cycles
echo "--- Reconciliation Activity ---"
if [ -f logs/autonomous_loop.log ]; then
    echo "Reconciliation cycles completed:"
    grep "Reconciliation daemon started\|Reconciliation completed" logs/autonomous_loop.log | tail -5
else
    echo "❌ Log file not found"
fi
echo ""

# Check scraper activity
echo "--- Scraper Activity ---"
if [ -f logs/autonomous_loop.log ]; then
    echo "Tasks completed (last 5):"
    grep "Task completed" logs/autonomous_loop.log | tail -5 || echo "No completed tasks"

    echo ""
    echo "Tasks failed (last 5):"
    grep "Task failed" logs/autonomous_loop.log | tail -5 || echo "No failed tasks"
else
    echo "❌ Log file not found"
fi
echo ""

# Check S3 storage
echo "--- S3 Storage ---"
aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize 2>/dev/null | tail -2 || echo "Could not retrieve S3 stats"
echo ""

echo "================================================================================"
echo "NEXT CHECK: Run this script again in 1-2 hours"
echo "STOP TEST:  python scripts/autonomous/autonomous_cli.py stop"
echo "VIEW LOGS:  python scripts/autonomous/autonomous_cli.py logs --tail 100"
echo "================================================================================"

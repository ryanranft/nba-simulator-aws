#!/bin/bash
# Week 3 Enhancement Progress Checker
# Run this anytime to see how the 15-minute cycles are performing

echo "================================================================================"
echo "WEEK 3 AUTONOMOUS MONITORING - PROGRESS CHECK"
echo "================================================================================"
echo "Check Time: $(date)"
echo ""

# System status
echo "=== System Status ==="
python scripts/autonomous/autonomous_cli.py status | grep -A 5 "Status:"
echo ""

# Recent reconciliation cycles
echo "=== Recent Reconciliation Cycles ==="
echo "Looking at inventory/gaps.json modification times..."
echo ""

# Check last 10 gaps.json updates (if they exist)
if [ -f inventory/gaps.json ]; then
    echo "Current cycle: $(cat inventory/gaps.json | jq -r '.generated_at')"
    echo "Total tasks:   $(cat inventory/gaps.json | jq '.total_tasks')"
    echo ""
fi

# Count cycles since deployment (7:35 AM Nov 1)
DEPLOY_TIME="2025-11-01 07:35:00"
CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")
SECONDS_ELAPSED=$(( $(date -j -f "%Y-%m-%d %H:%M:%S" "$CURRENT_TIME" +%s) - $(date -j -f "%Y-%m-%d %H:%M:%S" "$DEPLOY_TIME" +%s) 2>/dev/null || echo 0 ))
MINUTES_ELAPSED=$((SECONDS_ELAPSED / 60))
EXPECTED_CYCLES=$((MINUTES_ELAPSED / 15))

echo "Time since deployment: ${MINUTES_ELAPSED} minutes"
echo "Expected cycles:       ${EXPECTED_CYCLES}"
echo ""

# Process health
echo "=== Process Health ==="
ps -p $(pgrep -f "autonomous_loop.py" | head -1) -o pid,etime,rss 2>/dev/null || echo "Autonomous loop not running"
ps -p $(pgrep -f "reconciliation_daemon.py" | head -1) -o pid,etime,rss 2>/dev/null || echo "Reconciliation daemon not running"
echo ""

# Recent activity
echo "=== Recent Activity (Last 20 Log Lines) ==="
tail -20 logs/autonomous_loop.log | grep -v "Checking task queue" || tail -20 logs/autonomous_loop.log
echo ""

# Next expected cycle
if [ -f inventory/gaps.json ]; then
    LAST_CYCLE=$(cat inventory/gaps.json | jq -r '.generated_at')
    echo "=== Next Expected Cycle ==="
    echo "Last cycle: $LAST_CYCLE"

    # Calculate next cycle (15 minutes from last)
    if command -v python3 &> /dev/null; then
        python3 << EOF
from datetime import datetime, timedelta
try:
    last = datetime.fromisoformat("$LAST_CYCLE".replace('Z', '+00:00'))
    next_cycle = last + timedelta(minutes=15)
    now = datetime.now()
    if now.tzinfo is None:
        now = now.replace(tzinfo=last.tzinfo)

    if next_cycle > now:
        remaining = (next_cycle - now).total_seconds() / 60
        print(f"Next cycle: {next_cycle.strftime('%I:%M %p')} (in {remaining:.1f} minutes)")
    else:
        overdue = (now - next_cycle).total_seconds() / 60
        print(f"Next cycle: {next_cycle.strftime('%I:%M %p')} (overdue by {overdue:.1f} minutes)")
except Exception as e:
    print(f"Unable to calculate: {e}")
EOF
    fi
fi

echo ""
echo "================================================================================"
echo "To monitor in real-time: tail -f logs/autonomous_loop.log | grep -i cycle"
echo "To check system health:  python scripts/autonomous/autonomous_cli.py status"
echo "To view full testing plan: cat docs/adce/WEEK_3_TESTING_PLAN.md"
echo "================================================================================"

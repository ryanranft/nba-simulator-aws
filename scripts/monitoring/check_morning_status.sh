#!/bin/bash
#
# Morning Status Check - Run this after overnight autonomous loop test
#
# Usage: bash scripts/monitoring/check_morning_status.sh
#

echo "================================================================================"
echo "OVERNIGHT AUTONOMOUS LOOP TEST - MORNING STATUS CHECK"
echo "================================================================================"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# 1. Service Status
echo "=== 1. Service Status ==="
if launchctl list | grep -q "com.nba-simulator.adce-autonomous"; then
    echo "✅ LaunchAgent: Running"
    AGENT_PID=$(launchctl list | grep com.nba-simulator.adce-autonomous | awk '{print $1}')
    echo "   PID: $AGENT_PID"
else
    echo "❌ LaunchAgent: Not running"
fi

if ps aux | grep -q "[a]utonomous_loop.py"; then
    LOOP_PID=$(ps aux | grep "[a]utonomous_loop.py" | awk '{print $2}')
    echo "✅ Autonomous Loop: Running (PID: $LOOP_PID)"

    # Get uptime
    ps -p $LOOP_PID -o etime= | awk '{print "   Uptime: " $1}'

    # Get memory usage
    ps -p $LOOP_PID -o rss= | awk '{printf "   Memory: %.2f MB\n", $1/1024}'
else
    echo "❌ Autonomous Loop: Not running"
fi
echo ""

# 2. Health Endpoint
echo "=== 2. Health Endpoint ==="
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Health endpoint responding"
    curl -s http://localhost:8080/health | python -c "import sys, json; d=json.load(sys.stdin); print(f'   Status: {d[\"status\"]}'); print(f'   Reconciliation: {d[\"components\"][\"reconciliation_daemon\"][\"status\"]}'); print(f'   Task queue: {d[\"components\"][\"task_queue\"][\"total_tasks\"]} tasks')"
else
    echo "❌ Health endpoint not responding"
fi
echo ""

# 3. Reconciliation Cycles
echo "=== 3. Reconciliation Activity ==="
if [ -f logs/autonomous_loop.log ]; then
    CYCLES=$(grep -c "Cycle complete" logs/autonomous_loop.log || echo "0")
    echo "   Cycles completed: $CYCLES"

    # Show last 3 cycle timestamps
    echo "   Last 3 cycles:"
    grep "Cycle complete" logs/autonomous_loop.log | tail -3 || echo "   (No cycles yet)"
else
    echo "❌ Log file not found"
fi
echo ""

# 4. Error Count
echo "=== 4. Error Analysis ==="
if [ -f logs/autonomous_loop.log ]; then
    ERROR_COUNT=$(grep -c "ERROR" logs/autonomous_loop.log || echo "0")
    TOTAL_LINES=$(wc -l < logs/autonomous_loop.log)
    echo "   Total errors: $ERROR_COUNT"
    echo "   Total log lines: $TOTAL_LINES"

    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "   Recent errors:"
        grep "ERROR" logs/autonomous_loop.log | tail -5
    else
        echo "   ✅ No errors"
    fi
else
    echo "❌ Log file not found"
fi
echo ""

# 5. Task Execution
echo "=== 5. Task Execution ==="
python scripts/autonomous/autonomous_cli.py tasks 2>&1 | grep -A 5 "TASK QUEUE" || echo "   Could not retrieve task queue"
echo ""

# 6. S3 Inventory
echo "=== 6. S3 Storage ==="
aws s3 ls s3://nba-sim-raw-data-lake --recursive --summarize 2>/dev/null | tail -2 || echo "   Could not retrieve S3 stats"
echo ""

# 7. Log File Sizes
echo "=== 7. Log Files ==="
echo "   Autonomous Loop: $(ls -lh logs/autonomous_loop.log 2>/dev/null | awk '{print $5}') ($(wc -l < logs/autonomous_loop.log 2>/dev/null || echo 0) lines)"
echo "   Service stdout: $(ls -lh logs/adce-autonomous.stdout.log 2>/dev/null | awk '{print $5}')"
echo "   Service stderr: $(ls -lh logs/adce-autonomous.stderr.log 2>/dev/null | awk '{print $5}')"
echo ""

# 8. Success Criteria
echo "================================================================================"
echo "SUCCESS CRITERIA"
echo "================================================================================"

ALL_PASS=true

# Check 1: Service Running
if ps aux | grep -q "[a]utonomous_loop.py"; then
    echo "✅ Service running continuously"
else
    echo "❌ Service not running"
    ALL_PASS=false
fi

# Check 2: Uptime > 8 hours
if ps aux | grep -q "[a]utonomous_loop.py"; then
    UPTIME_SECONDS=$(ps -p $(ps aux | grep "[a]utonomous_loop.py" | awk '{print $2}') -o etimes= | tr -d ' ')
    if [ "$UPTIME_SECONDS" -gt 28800 ]; then  # 8 hours = 28800 seconds
        echo "✅ Uptime > 8 hours"
    else
        echo "⚠️ Uptime < 8 hours ($(echo $UPTIME_SECONDS / 3600 | bc) hours)"
    fi
fi

# Check 3: Reconciliation cycles
CYCLES=$(grep -c "Cycle complete" logs/autonomous_loop.log 2>/dev/null || echo "0")
if [ "$CYCLES" -gt 0 ]; then
    echo "✅ At least one reconciliation cycle completed ($CYCLES total)"
else
    echo "⚠️ No reconciliation cycles completed yet"
fi

# Check 4: Error rate < 10%
if [ -f logs/autonomous_loop.log ]; then
    ERROR_COUNT=$(grep -c "ERROR" logs/autonomous_loop.log || echo "0")
    TOTAL_LINES=$(wc -l < logs/autonomous_loop.log)
    if [ "$TOTAL_LINES" -gt 0 ]; then
        ERROR_RATE=$(echo "scale=2; $ERROR_COUNT * 100 / $TOTAL_LINES" | bc)
        if (( $(echo "$ERROR_RATE < 10" | bc -l) )); then
            echo "✅ Error rate < 10% ($ERROR_RATE%)"
        else
            echo "❌ Error rate >= 10% ($ERROR_RATE%)"
            ALL_PASS=false
        fi
    fi
fi

# Check 5: No crashes
CRASH_COUNT=$(grep -c "Crashed\|Fatal" logs/autonomous_loop.log 2>/dev/null || echo "0")
if [ "$CRASH_COUNT" -eq 0 ]; then
    echo "✅ No crashes detected"
else
    echo "❌ Crashes detected: $CRASH_COUNT"
    ALL_PASS=false
fi

echo ""
echo "================================================================================"
if [ "$ALL_PASS" = true ]; then
    echo "✅ OVERNIGHT TEST: PASSED"
    echo "The autonomous loop is production-ready!"
else
    echo "⚠️ OVERNIGHT TEST: NEEDS ATTENTION"
    echo "Review the issues above before declaring production-ready."
fi
echo "================================================================================"

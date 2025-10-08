#!/bin/bash
#
# Check Scraper Alerts
# Checks for completed scrapers and displays their status
# Can be run manually or integrated into session start workflows
#
# Usage:
#   bash scripts/monitoring/check_scraper_alerts.sh
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

ALERT_DIR="/tmp/scraper_alerts"
REMINDER_DIR="/tmp/scraper_reminders"

# Check if there are any alerts
alert_count=$(ls "$ALERT_DIR"/*.alert 2>/dev/null | wc -l | tr -d ' ')
reminder_count=$(ls "$REMINDER_DIR"/*.reminder 2>/dev/null | wc -l | tr -d ' ')

if [ "$alert_count" -eq 0 ] && [ "$reminder_count" -eq 0 ]; then
    echo ""
    echo "✅ No scraper alerts or running scrapers"
    echo ""
    exit 0
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📊 Scraper Status Update"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Show running scrapers
if [ "$reminder_count" -gt 0 ]; then
    echo -e "${CYAN}🔄 Currently Running Scrapers: $reminder_count${NC}"
    echo ""

    for reminder_file in "$REMINDER_DIR"/*.reminder; do
        [ -f "$reminder_file" ] || continue

        scraper_name=$(grep "^SCRAPER:" "$reminder_file" | cut -d: -f2-)
        pid=$(grep "^PID:" "$reminder_file" | cut -d: -f2 | tr -d ' ')
        start_time=$(grep "^START_TIME:" "$reminder_file" | cut -d: -f2-)
        expected_completion=$(grep "^EXPECTED_COMPLETION:" "$reminder_file" | cut -d: -f2 | tr -d ' ')

        # Check if still running
        if ps -p "$pid" >/dev/null 2>&1; then
            expected_time=$(date -r "$expected_completion" '+%H:%M:%S' 2>/dev/null || echo "unknown")
            echo -e "  • ${scraper_name}"
            echo -e "    Started: ${start_time}"
            echo -e "    Expected finish: ${expected_time}"
        fi
    done
    echo ""
fi

# Show completed scrapers
if [ "$alert_count" -gt 0 ]; then
    echo -e "${GREEN}✅ Completed Scrapers: $alert_count${NC}"
    echo ""

    for alert_file in "$ALERT_DIR"/*.alert; do
        [ -f "$alert_file" ] || continue

        scraper_name=$(grep "^SCRAPER:" "$alert_file" | cut -d: -f2-)
        completion_time=$(grep "^COMPLETION_TIME:" "$alert_file" | cut -d: -f2-)
        status=$(grep "^STATUS:" "$alert_file" | cut -d: -f2 | tr -d ' ')
        errors=$(grep "^ERRORS:" "$alert_file" | cut -d: -f2 | tr -d ' ')
        log_path=$(grep "^LOG:" "$alert_file" | cut -d: -f2-)

        echo -e "  • ${scraper_name}"
        echo -e "    Completed: ${completion_time}"

        if [ "$errors" -eq 0 ]; then
            echo -e "    Status: ${GREEN}Success (no errors)${NC}"
        else
            echo -e "    Status: ${YELLOW}Complete with $errors errors${NC}"
        fi

        echo -e "    Log: ${log_path}"
        echo ""
    done

    echo -e "${YELLOW}📋 Recommended Actions:${NC}"
    echo "  1. Review scraper logs for any errors"
    echo "  2. Verify S3 uploads completed successfully"
    echo "  3. Clear alerts when reviewed: rm /tmp/scraper_alerts/*.alert"
    echo ""
fi

echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
#!/bin/bash
#
# Analyze Scraper Completion
# Analyzes a completed scraper and recommends next steps
#
# Usage:
#   bash scripts/monitoring/analyze_scraper_completion.sh <alert_file>
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ $# -lt 1 ]; then
    echo "Usage: $0 <alert_file>"
    exit 1
fi

alert_file="$1"

if [ ! -f "$alert_file" ]; then
    echo "Error: Alert file not found: $alert_file"
    exit 1
fi

# Parse alert file (trim leading/trailing whitespace)
scraper_name=$(grep "^SCRAPER:" "$alert_file" | cut -d: -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
completion_time=$(grep "^COMPLETION_TIME:" "$alert_file" | cut -d: -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
status=$(grep "^STATUS:" "$alert_file" | cut -d: -f2 | tr -d ' ')
errors=$(grep "^ERRORS:" "$alert_file" | cut -d: -f2 | tr -d ' ')
log_path=$(grep "^LOG:" "$alert_file" | cut -d: -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo -e "${CYAN}📊 Scraper Completion Analysis${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Scraper: $scraper_name"
echo "Completed: $completion_time"
echo "Log: $log_path"
echo ""

# Analyze completion
echo -e "${CYAN}📋 Status Analysis:${NC}"
echo ""

if [ "$errors" -eq 0 ]; then
    echo -e "  ${GREEN}✅ No errors detected${NC}"
    recommendation="COMPLETE"
else
    echo -e "  ${YELLOW}⚠️  $errors errors found in log${NC}"
    recommendation="INVESTIGATE"
fi

# Check log for completion markers
if grep -q "complete" "$log_path" 2>/dev/null; then
    echo -e "  ${GREEN}✅ Completion marker found in log${NC}"
else
    echo -e "  ${YELLOW}⚠️  No completion marker in log${NC}"
    recommendation="INVESTIGATE"
fi

echo ""
echo -e "${CYAN}🎯 Recommendation: ${recommendation}${NC}"
echo ""

case $recommendation in
    COMPLETE)
        echo "  ${GREEN}✓${NC} Scraper completed successfully"
        echo "  ${GREEN}✓${NC} No action required"
        echo ""
        echo "Next steps:"
        echo "  1. Verify S3 uploads (if applicable)"
        echo "  2. Clear this alert: rm $alert_file"
        ;;
    INVESTIGATE)
        echo "  ${YELLOW}⚠${NC} Review required"
        echo ""
        echo "Actions:"
        echo "  1. Review log file: tail -100 $log_path"
        echo "  2. Check error details: grep -i error $log_path"
        echo "  3. Decide: redeploy if critical errors, or accept if minor"
        ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
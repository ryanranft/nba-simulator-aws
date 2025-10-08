#!/bin/bash
#
# Validate Scraper Monitoring System
# Quick validation of monitoring system components
#
# This is a lightweight alternative to the comprehensive test suite.
# Validates that all components are present, executable, and syntactically correct.
#
# Usage:
#   bash scripts/monitoring/validate_monitoring_system.sh [--verbose]
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Verbose mode
VERBOSE=false
if [ "$1" = "--verbose" ] || [ "$1" = "-v" ]; then
    VERBOSE=true
    set -x
fi

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo -e "${CYAN}🔍 Monitoring System Validation${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Check function
check() {
    local description="$1"
    local command="$2"

    if eval "$command" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $description"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "  ${RED}✗${NC} $description"
        ((CHECKS_FAILED++))
        if [ "$VERBOSE" = true ]; then
            echo "    Command: $command"
            eval "$command" 2>&1 | sed 's/^/      /'
        fi
        return 1
    fi
}

# 1. Core Scripts Exist
echo -e "${CYAN}1. Core Scripts${NC}"
check "Watcher daemon exists" "[ -f '$SCRIPT_DIR/scraper_watcher_daemon.sh' ]"
check "Alert checker exists" "[ -f '$SCRIPT_DIR/check_scraper_alerts.sh' ]"
check "Completion analyzer exists" "[ -f '$SCRIPT_DIR/analyze_scraper_completion.sh' ]"
check "Context saver exists" "[ -f '$SCRIPT_DIR/save_work_context.sh' ]"
check "Scraper launcher exists" "[ -f '$SCRIPT_DIR/launch_scraper.sh' ]"
check "Inline monitor exists" "[ -f '$SCRIPT_DIR/monitor_scrapers_inline.sh' ]"
echo ""

# 2. Scripts are Executable
echo -e "${CYAN}2. Execute Permissions${NC}"
check "Watcher daemon executable" "[ -x '$SCRIPT_DIR/scraper_watcher_daemon.sh' ]"
check "Alert checker executable" "[ -x '$SCRIPT_DIR/check_scraper_alerts.sh' ]"
check "Completion analyzer executable" "[ -x '$SCRIPT_DIR/analyze_scraper_completion.sh' ]"
check "Context saver executable" "[ -x '$SCRIPT_DIR/save_work_context.sh' ]"
check "Scraper launcher executable" "[ -x '$SCRIPT_DIR/launch_scraper.sh' ]"
check "Inline monitor executable" "[ -x '$SCRIPT_DIR/monitor_scrapers_inline.sh' ]"
echo ""

# 3. Syntax Validation
echo -e "${CYAN}3. Syntax Validation${NC}"
check "Watcher daemon syntax" "bash -n '$SCRIPT_DIR/scraper_watcher_daemon.sh'"
check "Alert checker syntax" "bash -n '$SCRIPT_DIR/check_scraper_alerts.sh'"
check "Completion analyzer syntax" "bash -n '$SCRIPT_DIR/analyze_scraper_completion.sh'"
check "Context saver syntax" "bash -n '$SCRIPT_DIR/save_work_context.sh'"
check "Scraper launcher syntax" "bash -n '$SCRIPT_DIR/launch_scraper.sh'"
check "Inline monitor syntax" "bash -n '$SCRIPT_DIR/monitor_scrapers_inline.sh'"
echo ""

# 4. Directory Structure
echo -e "${CYAN}4. Directory Structure${NC}"
check "Alert directory exists" "[ -d '/tmp/scraper_alerts' ]"
check "Reminder directory exists" "[ -d '/tmp/scraper_reminders' ]"
echo ""

# 5. Script Interfaces
echo -e "${CYAN}5. Script Interfaces${NC}"
check "Daemon responds to no-args" "'$SCRIPT_DIR/scraper_watcher_daemon.sh' 2>&1 | grep -q 'start\|stop\|status'"
check "Alert checker runs without error" "'$SCRIPT_DIR/check_scraper_alerts.sh' >/dev/null 2>&1"
check "Context saver accepts args" "'$SCRIPT_DIR/save_work_context.sh' 'test' 'test' 'test' >/dev/null 2>&1"
echo ""

# 6. Dependencies
echo -e "${CYAN}6. Dependencies${NC}"
check "Python3 available" "command -v python3"
check "AWS CLI available" "command -v aws"
check "Bash version 3+" "[ ${BASH_VERSINFO[0]} -ge 3 ]"
echo ""

# 7. ETL Scripts (for scraper launcher)
echo -e "${CYAN}7. ETL Scripts${NC}"
check "BBRef incremental scraper exists" "[ -f '$SCRIPT_DIR/../etl/scrape_bbref_incremental.sh' ]"
check "hoopR Phase 1B scraper exists" "[ -f '$SCRIPT_DIR/../etl/run_hoopr_phase1b.sh' ]"
check "NBA API scraper exists" "[ -f '$SCRIPT_DIR/../etl/overnight_nba_api_comprehensive.sh' ]"
echo ""

# 8. File Permissions (write access to /tmp)
echo -e "${CYAN}8. File System Permissions${NC}"
check "/tmp is writable" "[ -w '/tmp' ]"
check "Can create alert files" "touch '/tmp/scraper_alerts/.test' && rm '/tmp/scraper_alerts/.test'"
check "Can create reminder files" "touch '/tmp/scraper_reminders/.test' && rm '/tmp/scraper_reminders/.test'"
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════════════════════"
echo -e "${CYAN}📊 Validation Summary${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

total_checks=$((CHECKS_PASSED + CHECKS_FAILED))
pass_rate=0
if [ $total_checks -gt 0 ]; then
    pass_rate=$((CHECKS_PASSED * 100 / total_checks))
fi

echo -e "  Checks Passed:  ${GREEN}$CHECKS_PASSED${NC}"
echo -e "  Checks Failed:  ${RED}$CHECKS_FAILED${NC}"
echo -e "  Total Checks:   $total_checks"
echo -e "  Pass Rate:      ${pass_rate}%"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All validation checks passed!${NC}"
    echo ""
    echo "The monitoring system is properly installed and ready to use."
    echo ""
    echo "Quick start:"
    echo "  Launch scrapers:  bash scripts/monitoring/launch_scraper.sh"
    echo "  Check alerts:     bash scripts/monitoring/check_scraper_alerts.sh"
    echo "  Monitor status:   bash scripts/monitoring/monitor_scrapers_inline.sh"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some validation checks failed${NC}"
    echo ""
    if [ "$VERBOSE" = false ]; then
        echo "Run with --verbose flag for detailed error information:"
        echo "  bash scripts/monitoring/validate_monitoring_system.sh --verbose"
    else
        echo "See error details above."
    fi
    echo ""
    exit 1
fi

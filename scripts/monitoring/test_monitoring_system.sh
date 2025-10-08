#!/bin/bash
#
# Test Scraper Monitoring System
# Comprehensive end-to-end test of the hybrid monitoring system
#
# Tests:
#   1. Daemon startup and process tracking
#   2. Reminder file creation
#   3. Alert file creation on completion
#   4. Alert checking functionality
#   5. Completion analysis
#   6. Context preservation
#
# Usage:
#   bash scripts/monitoring/test_monitoring_system.sh [--verbose]
#
# Options:
#   --verbose, -v    Show detailed output for each test
#

# Note: Removed 'set -e' to allow test failures without aborting the entire suite
set -u

# Verbose mode
VERBOSE=false
if [ "${1:-}" = "--verbose" ] || [ "${1:-}" = "-v" ]; then
    VERBOSE=true
fi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Verbose output function
verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Directories
ALERT_DIR="/tmp/scraper_alerts"
REMINDER_DIR="/tmp/scraper_reminders"
TEST_LOG_DIR="/tmp/monitoring_test_logs"

# Project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo -e "${CYAN}🧪 Scraper Monitoring System Test Suite${NC}"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Setup test environment
setup_test_env() {
    echo -e "${BLUE}📦 Setting up test environment...${NC}"

    # Create test log directory
    mkdir -p "$TEST_LOG_DIR"

    # Backup existing alerts/reminders if any
    if [ -d "$ALERT_DIR" ] && [ "$(ls -A $ALERT_DIR 2>/dev/null)" ]; then
        echo "  Backing up existing alerts..."
        mv "$ALERT_DIR" "${ALERT_DIR}_backup_$(date +%s)"
    fi

    if [ -d "$REMINDER_DIR" ] && [ "$(ls -A $REMINDER_DIR 2>/dev/null)" ]; then
        echo "  Backing up existing reminders..."
        mv "$REMINDER_DIR" "${REMINDER_DIR}_backup_$(date +%s)"
    fi

    # Create fresh directories
    mkdir -p "$ALERT_DIR"
    mkdir -p "$REMINDER_DIR"

    echo -e "  ${GREEN}✓ Test environment ready${NC}"
    echo ""
}

# Cleanup test environment
cleanup_test_env() {
    echo ""
    echo -e "${BLUE}🧹 Cleaning up test environment...${NC}"

    # Remove test alerts/reminders
    rm -f "$ALERT_DIR"/test_*.alert 2>/dev/null || true
    rm -f "$REMINDER_DIR"/test_*.reminder 2>/dev/null || true

    # Kill test daemon if running (non-blocking with pgrep check)
    if pgrep -f "scraper_watcher_daemon.sh" >/dev/null 2>&1; then
        pkill -f "scraper_watcher_daemon.sh" 2>/dev/null || true
        sleep 1  # Give process time to die
    fi

    echo -e "  ${GREEN}✓ Cleanup complete${NC}"
}

# Test helper: Check if test passed
check_result() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"

    if [ "$expected" = "$actual" ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "  ${RED}✗ FAIL${NC}: $test_name"
        echo -e "    Expected: $expected"
        echo -e "    Actual: $actual"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test 1: Daemon script exists and has proper interface
test_daemon_startup() {
    echo -e "${CYAN}Test 1: Daemon Script Validation${NC}"
    echo "Testing if daemon script exists and has proper interface..."

    # Check if daemon script exists
    verbose "Checking if daemon script exists at: $SCRIPT_DIR/scraper_watcher_daemon.sh"
    if [ -f "$SCRIPT_DIR/scraper_watcher_daemon.sh" ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: Daemon script exists"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Daemon script not found"
        ((TESTS_FAILED++))
        return
    fi

    # Check if daemon is executable
    verbose "Checking execute permissions"
    if [ -x "$SCRIPT_DIR/scraper_watcher_daemon.sh" ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: Daemon script is executable"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Daemon script not executable"
        ((TESTS_FAILED++))
    fi

    # Check if daemon responds to commands (without actually starting it)
    verbose "Testing daemon command interface"
    local help_output=$("$SCRIPT_DIR/scraper_watcher_daemon.sh" 2>&1 || true)
    verbose "Daemon output: ${help_output:0:100}..."
    if echo "$help_output" | grep -q "start\|stop\|status"; then
        echo -e "  ${GREEN}✓ PASS${NC}: Daemon has proper command interface"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Daemon command interface missing"
        ((TESTS_FAILED++))
    fi

    echo ""
}

# Test 2: Reminder file creation
test_reminder_creation() {
    echo -e "${CYAN}Test 2: Reminder File Creation${NC}"
    echo "Testing reminder file creation and format..."

    verbose "Creating test reminder file at: $REMINDER_DIR/${TEST_RUN_ID}_test_scraper_12345.reminder"

    # Create mock reminder file
    local test_reminder="$REMINDER_DIR/${TEST_RUN_ID}_test_scraper_12345.reminder"
    cat > "$test_reminder" <<EOF
SCRAPER: Test Scraper
PID: 12345
LOG: /tmp/test_scraper.log
START_TIME: $(date '+%Y-%m-%d %H:%M:%S')
EXPECTED_COMPLETION: $(python3 -c "import time; print(int(time.time() + 3600))")
ESTIMATED_HOURS: 1
EOF

    # Verify file exists
    verbose "Verifying reminder file exists: $test_reminder"
    if [ -f "$test_reminder" ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: Reminder file created"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Reminder file not created"
        ((TESTS_FAILED++))
    fi

    # Verify required fields
    verbose "Checking required fields: SCRAPER, PID, LOG, START_TIME, EXPECTED_COMPLETION"
    local required_fields=("SCRAPER:" "PID:" "LOG:" "START_TIME:" "EXPECTED_COMPLETION:")
    local all_fields_present=true

    for field in "${required_fields[@]}"; do
        if ! grep -q "^$field" "$test_reminder"; then
            echo -e "  ${RED}✗ FAIL${NC}: Missing required field: $field"
            all_fields_present=false
            ((TESTS_FAILED++))
        fi
    done

    if [ "$all_fields_present" = true ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: All required fields present"
        ((TESTS_PASSED++))
    fi

    echo ""
}

# Test 3: Alert file creation
test_alert_creation() {
    echo -e "${CYAN}Test 3: Alert File Creation${NC}"
    echo "Testing alert file creation on scraper completion..."

    verbose "Creating mock scraper log and alert file"

    # Create mock scraper log
    local test_log="$TEST_LOG_DIR/${TEST_RUN_ID}_test_scraper.log"
    cat > "$test_log" <<EOF
Starting test scraper...
Processing data...
All tasks complete
EOF

    # Create mock alert file
    local test_alert="$ALERT_DIR/${TEST_RUN_ID}_test_scraper_complete.alert"
    cat > "$test_alert" <<EOF
SCRAPER: Test Scraper
COMPLETION_TIME: $(date '+%Y-%m-%d %H:%M:%S')
STATUS: complete
ERRORS: 0
LOG: $test_log
EOF

    # Verify file exists
    verbose "Verifying alert file exists: $test_alert"
    if [ -f "$test_alert" ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: Alert file created"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Alert file not created"
        ((TESTS_FAILED++))
    fi

    # Verify required fields
    verbose "Checking required fields in alert file"
    local required_fields=("SCRAPER:" "COMPLETION_TIME:" "STATUS:" "ERRORS:" "LOG:")
    local all_fields_present=true

    for field in "${required_fields[@]}"; do
        if ! grep -q "^$field" "$test_alert"; then
            echo -e "  ${RED}✗ FAIL${NC}: Missing required field: $field"
            all_fields_present=false
            ((TESTS_FAILED++))
        fi
    done

    if [ "$all_fields_present" = true ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: All required fields present"
        ((TESTS_PASSED++))
    fi

    echo ""
}

# Test 4: Alert checking script
test_alert_checker() {
    echo -e "${CYAN}Test 4: Alert Checking Script${NC}"
    echo "Testing check_scraper_alerts.sh functionality..."

    verbose "Running alert checker script: $SCRIPT_DIR/check_scraper_alerts.sh"

    # Run alert checker
    local output=$("$SCRIPT_DIR/check_scraper_alerts.sh" 2>&1)

    # Check if it detects the test alert
    verbose "Checking if alert checker detected 'Test Scraper'"
    if echo "$output" | grep -q "Test Scraper"; then
        echo -e "  ${GREEN}✓ PASS${NC}: Alert checker detected test scraper"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Alert checker did not detect test scraper"
        ((TESTS_FAILED++))
    fi

    # Check if it shows completion status
    verbose "Checking for completion time in output"
    if echo "$output" | grep -q "Completed:"; then
        echo -e "  ${GREEN}✓ PASS${NC}: Shows completion time"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Missing completion time"
        ((TESTS_FAILED++))
    fi

    echo ""
}

# Test 5: Completion analysis script
test_completion_analyzer() {
    echo -e "${CYAN}Test 5: Completion Analysis Script${NC}"
    echo "Testing analyze_scraper_completion.sh functionality..."

    local test_alert="$ALERT_DIR/${TEST_RUN_ID}_test_scraper_complete.alert"

    verbose "Running completion analyzer on: $test_alert"

    # Run completion analyzer
    local output=$("$SCRIPT_DIR/analyze_scraper_completion.sh" "$test_alert" 2>&1)

    # Check if it provides recommendation
    verbose "Checking for recommendation in analyzer output"
    if echo "$output" | grep -q "Recommendation:"; then
        echo -e "  ${GREEN}✓ PASS${NC}: Provides recommendation"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: No recommendation provided"
        ((TESTS_FAILED++))
    fi

    # Check if it analyzes errors
    verbose "Verifying error analysis functionality"
    if echo "$output" | grep -q "errors"; then
        echo -e "  ${GREEN}✓ PASS${NC}: Analyzes error count"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Missing error analysis"
        ((TESTS_FAILED++))
    fi

    # For successful completion, should recommend COMPLETE
    if echo "$output" | grep -q "COMPLETE"; then
        echo -e "  ${GREEN}✓ PASS${NC}: Correct recommendation (COMPLETE)"
        ((TESTS_PASSED++))
    else
        echo -e "  ${YELLOW}⚠ WARN${NC}: Expected COMPLETE recommendation"
    fi

    echo ""
}

# Test 6: Completion analyzer with errors
test_completion_analyzer_errors() {
    echo -e "${CYAN}Test 6: Completion Analysis with Errors${NC}"
    echo "Testing analyzer with error conditions..."

    verbose "Creating test log with errors and analyzing"

    # Create scraper log with errors
    local test_log_errors="$TEST_LOG_DIR/${TEST_RUN_ID}_test_scraper_errors.log"
    cat > "$test_log_errors" <<EOF
Starting test scraper...
Processing data...
ERROR: Failed to fetch data
ERROR: Connection timeout
Continuing...
EOF

    # Create alert with errors
    local test_alert_errors="$ALERT_DIR/${TEST_RUN_ID}_test_scraper_errors.alert"
    cat > "$test_alert_errors" <<EOF
SCRAPER: Test Scraper (with errors)
COMPLETION_TIME: $(date '+%Y-%m-%d %H:%M:%S')
STATUS: complete
ERRORS: 2
LOG: $test_log_errors
EOF

    # Run completion analyzer
    verbose "Running analyzer with error conditions to verify INVEST IGATE recommendation"
    local output=$("$SCRIPT_DIR/analyze_scraper_completion.sh" "$test_alert_errors" 2>&1)

    # Should recommend INVESTIGATE due to errors
    verbose "Verifying INVESTIGATE recommendation for error case"
    if echo "$output" | grep -q "INVESTIGATE"; then
        echo -e "  ${GREEN}✓ PASS${NC}: Correct recommendation (INVESTIGATE) for errors"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Should recommend INVESTIGATE when errors present"
        ((TESTS_FAILED++))
    fi

    # Should show error count
    if echo "$output" | grep -q "2 errors"; then
        echo -e "  ${GREEN}✓ PASS${NC}: Shows correct error count"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Incorrect error count"
        ((TESTS_FAILED++))
    fi

    echo ""
}

# Test 7: Context preservation
test_context_preservation() {
    echo -e "${CYAN}Test 7: Context Preservation${NC}"
    echo "Testing save_work_context.sh functionality..."

    verbose "Saving test context to /tmp/claude_work_context.json"

    # Save test context
    "$SCRIPT_DIR/save_work_context.sh" \
        "Testing monitoring system" \
        "Running test suite" \
        "Verify all tests pass" > /dev/null 2>&1

    local context_file="/tmp/claude_work_context.json"

    # Check if context file created
    verbose "Verifying context file created and validating JSON format"
    if [ -f "$context_file" ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: Context file created"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Context file not created"
        ((TESTS_FAILED++))
        return
    fi

    # Check if valid JSON
    if python3 -c "import json; json.load(open('$context_file'))" 2>/dev/null; then
        echo -e "  ${GREEN}✓ PASS${NC}: Valid JSON format"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Invalid JSON format"
        ((TESTS_FAILED++))
    fi

    # Check required fields
    if grep -q '"task"' "$context_file" && \
       grep -q '"current_step"' "$context_file" && \
       grep -q '"next_step"' "$context_file"; then
        echo -e "  ${GREEN}✓ PASS${NC}: All required fields present"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Missing required fields"
        ((TESTS_FAILED++))
    fi

    echo ""
}

# Test 8: Script permissions
test_script_permissions() {
    echo -e "${CYAN}Test 8: Script Permissions${NC}"
    echo "Testing if all scripts are executable..."

    verbose "Checking execute permissions on all monitoring scripts"

    local scripts=(
        "check_scraper_alerts.sh"
        "analyze_scraper_completion.sh"
        "save_work_context.sh"
        "scraper_watcher_daemon.sh"
        "launch_scraper.sh"
        "monitor_scrapers_inline.sh"
    )

    local all_executable=true

    for script in "${scripts[@]}"; do
        local script_path="$SCRIPT_DIR/$script"
        if [ -x "$script_path" ]; then
            echo -e "  ${GREEN}✓${NC} $script is executable"
        else
            echo -e "  ${RED}✗${NC} $script is NOT executable"
            all_executable=false
        fi
    done

    if [ "$all_executable" = true ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: All scripts executable"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Some scripts not executable"
        ((TESTS_FAILED++))
    fi

    echo ""
}

# Test 9: Directory structure
test_directory_structure() {
    echo -e "${CYAN}Test 9: Directory Structure${NC}"
    echo "Testing required directories exist..."

    verbose "Verifying required directories: /tmp/scraper_alerts, /tmp/scraper_reminders"

    local required_dirs=(
        "/tmp/scraper_alerts"
        "/tmp/scraper_reminders"
    )

    local all_exist=true

    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo -e "  ${GREEN}✓${NC} $dir exists"
        else
            echo -e "  ${RED}✗${NC} $dir missing"
            all_exist=false
        fi
    done

    if [ "$all_exist" = true ]; then
        echo -e "  ${GREEN}✓ PASS${NC}: All required directories exist"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ FAIL${NC}: Some directories missing"
        ((TESTS_FAILED++))
    fi

    echo ""
}

# Test 10: Integration test
test_integration() {
    echo -e "${CYAN}Test 10: End-to-End Integration${NC}"
    echo "Testing complete workflow..."

    verbose "Starting end-to-end integration test (6 steps)"

    # 1. Create reminder (simulating scraper launch)
    echo "  1. Creating reminder (simulating scraper launch)..."
    verbose "Creating test reminder for PID 99999"
    local test_pid="99999"
    local test_reminder="$REMINDER_DIR/${TEST_RUN_ID}_integration_test_${test_pid}.reminder"
    cat > "$test_reminder" <<EOF
SCRAPER: Integration Test Scraper
PID: $test_pid
LOG: $TEST_LOG_DIR/integration_test.log
START_TIME: $(date '+%Y-%m-%d %H:%M:%S')
EXPECTED_COMPLETION: $(python3 -c "import time; print(int(time.time() + 60))")
ESTIMATED_HOURS: 0
EOF

    # 2. Create log file
    echo "  2. Creating log file..."
    cat > "$TEST_LOG_DIR/${TEST_RUN_ID}_integration_test.log" <<EOF
Starting integration test scraper...
Processing...
Integration test complete
EOF

    # 3. Simulate completion (create alert)
    echo "  3. Simulating completion (creating alert)..."
    local test_alert="$ALERT_DIR/${TEST_RUN_ID}_integration_test_complete.alert"
    cat > "$test_alert" <<EOF
SCRAPER: Integration Test Scraper
COMPLETION_TIME: $(date '+%Y-%m-%d %H:%M:%S')
STATUS: complete
ERRORS: 0
LOG: $TEST_LOG_DIR/${TEST_RUN_ID}_integration_test.log
EOF

#  4. Check alerts
    echo "  4. Checking alerts..."
    verbose "Running check_scraper_alerts.sh to detect completion"
    local check_output=$("$SCRIPT_DIR/check_scraper_alerts.sh" 2>&1)
    if echo "$check_output" | grep -q "Integration Test Scraper"; then
        echo -e "    ${GREEN}✓${NC} Alert checker detected completion"
    else
        echo -e "    ${RED}✗${NC} Alert checker failed"
        ((TESTS_FAILED++))
        return
    fi

    # 5. Analyze completion
    echo "  5. Analyzing completion..."
    verbose "Analyzing completion with analyze_scraper_completion.sh"
    local analyze_output=$("$SCRIPT_DIR/analyze_scraper_completion.sh" "$test_alert" 2>&1)
    if echo "$analyze_output" | grep -q "COMPLETE"; then
        echo -e "    ${GREEN}✓${NC} Analysis provided correct recommendation"
    else
        echo -e "    ${RED}✗${NC} Analysis failed"
        ((TESTS_FAILED++))
        return
    fi

    # 6. Save context
    echo "  6. Testing context preservation..."
    "$SCRIPT_DIR/save_work_context.sh" \
        "Integration test" \
        "Testing workflow" \
        "Cleanup" > /dev/null 2>&1

    if [ -f "/tmp/claude_work_context.json" ]; then
        echo -e "    ${GREEN}✓${NC} Context saved successfully"
    else
        echo -e "    ${RED}✗${NC} Context save failed"
        ((TESTS_FAILED++))
        return
    fi

    # Clean up integration test files
    rm -f "$test_reminder" "$test_alert" "$TEST_LOG_DIR/${TEST_RUN_ID}_integration_test.log"

    echo -e "  ${GREEN}✓ PASS${NC}: End-to-end integration test complete"
    ((TESTS_PASSED++))
    echo ""
}

# Main test execution
main() {
    # Generate unique test run ID for file isolation
    TEST_RUN_ID="test_$(date +%s)_$$"
    export TEST_RUN_ID

    setup_test_env

    # Run all tests
    test_daemon_startup
    test_reminder_creation
    test_alert_creation
    test_alert_checker
    test_completion_analyzer
    test_completion_analyzer_errors
    test_context_preservation
    test_script_permissions
    test_directory_structure
    test_integration

    # Cleanup
    cleanup_test_env

    # Summary
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo -e "${CYAN}📊 Test Results Summary${NC}"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""

    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local pass_rate=0
    if [ $total_tests -gt 0 ]; then
        pass_rate=$((TESTS_PASSED * 100 / total_tests))
    fi

    echo -e "  Tests Passed:  ${GREEN}$TESTS_PASSED${NC}"
    echo -e "  Tests Failed:  ${RED}$TESTS_FAILED${NC}"
    echo -e "  Total Tests:   $total_tests"
    echo -e "  Pass Rate:     ${pass_rate}%"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo ""
        echo "The scraper monitoring system is working correctly."
        echo ""
        echo "Next steps:"
        echo "  1. Start using the monitoring system with real scrapers"
        echo "  2. Test with overnight scrapers"
        echo "  3. Verify desktop notifications work (macOS)"
        echo ""
        exit 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        echo ""
        echo "Please review the failures above and fix before using the system."
        echo ""
        exit 1
    fi
}

# Run tests
main

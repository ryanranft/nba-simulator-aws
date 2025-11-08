#!/bin/bash
#
# Validate Basketball Reference Fix
# Runs diagnostic and tests small scrape
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_OUTPUT_DIR="/tmp/bbref_test"
LOG_FILE="/tmp/bbref_validation.log"

echo "=============================================="
echo "Basketball Reference Fix Validation"
echo "=============================================="
echo "Test output: $TEST_OUTPUT_DIR"
echo "Log file: $LOG_FILE"
echo "Start time: $(date)"
echo "=============================================="
echo

# Clean up previous test
rm -rf "$TEST_OUTPUT_DIR"
mkdir -p "$TEST_OUTPUT_DIR"

# Check if basketball_reference_web_scraper is installed
if ! python3 -c "import basketball_reference_web_scraper" 2>/dev/null; then
    echo "❌ basketball_reference_web_scraper not installed"
    echo "Installing..."
    pip install basketball_reference_web_scraper
fi

echo "Step 1: Running Basketball Reference API diagnostic..."
echo "----------------------------------------------------"

# Run diagnostic
python3 "$SCRIPT_DIR/test_basketball_reference_api.py" 2>&1 | tee "$LOG_FILE"

# Check if diagnostic passed
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo
    echo "✅ Diagnostic passed! API is working."
    echo
    echo "Step 2: Testing small scrape (2024 schedules only)..."
    echo "----------------------------------------------------"

    # Try a small scrape
    python3 "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
        --data-type schedules \
        --start-season 2024 \
        --end-season 2024 \
        --output-dir "$TEST_OUTPUT_DIR" \
        --rate-limit 20.0 \
        2>&1 | tee -a "$LOG_FILE"

    # Check if scrape succeeded
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo
        echo "✅ Basketball Reference scraper fixed!"
        echo

        # Check what was created
        echo "Files created:"
        find "$TEST_OUTPUT_DIR" -type f -name "*.json" | head -5
        echo

        # Count files
        file_count=$(find "$TEST_OUTPUT_DIR" -type f -name "*.json" | wc -l)
        echo "Total files created: $file_count"

        if [ $file_count -gt 0 ]; then
            echo
            echo "✅ SUCCESS: Basketball Reference scraper is working!"
            echo "📁 Test files saved to: $TEST_OUTPUT_DIR"
            echo "📋 Full log saved to: $LOG_FILE"

            echo
            echo "Next steps:"
            echo "1. Update rate limit in scrape_basketball_reference_complete.py to 20.0s"
            echo "2. Restart Basketball Reference scraper for historical data"
            echo "3. Monitor for continued success"

        else
            echo
            echo "⚠️ WARNING: Scraper ran but no files were created"
            echo "Check the log for details: $LOG_FILE"
        fi

    else
        echo
        echo "❌ Scraper still failing after diagnostic passed"
        echo "Check the log for details: $LOG_FILE"
        echo
        echo "Possible issues:"
        echo "- Rate limiting still too aggressive"
        echo "- Specific endpoint issues"
        echo "- Data format changes"
    fi

else
    echo
    echo "❌ API connectivity issues remain"
    echo "Check the log for details: $LOG_FILE"
    echo
    echo "Possible solutions:"
    echo "1. Check internet connectivity"
    echo "2. Try different user agent"
    echo "3. Increase rate limit to 30+ seconds"
    echo "4. Check if IP is blocked"
    echo "5. Update basketball_reference_web_scraper package"
fi

echo
echo "End time: $(date)"
echo "=============================================="

# Return appropriate exit code
if [ -f "$TEST_OUTPUT_DIR"/*.json ] 2>/dev/null; then
    exit 0  # Success
else
    exit 1  # Failure
fi












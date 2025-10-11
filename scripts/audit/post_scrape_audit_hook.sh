#!/bin/bash

##############################################################################
# Post-Scrape Data Audit Hook
##############################################################################
#
# Purpose: Automatically run data audit after scraping completes
# Triggered by: Manual call from scraping scripts or cron job
# Output: Audit logs + optional documentation updates
#
# Usage:
#   # At the end of your scraping script, add:
#   bash scripts/audit/post_scrape_audit_hook.sh
#
#   # Or schedule to run after overnight scraping:
#   0 9 * * * /path/to/scripts/audit/post_scrape_audit_hook.sh
#
##############################################################################

set -e  # Exit on error

# Configuration
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
AUDIT_SCRIPT="$PROJECT_ROOT/scripts/audit/run_data_audit.sh"

echo "================================================"
echo "Post-Scrape Data Audit Hook"
echo "Triggered: $(date)"
echo "================================================"
echo ""

# Wait a moment to ensure file system is fully synced
sleep 5

# Run the audit with documentation updates
if [ -f "$AUDIT_SCRIPT" ]; then
    echo "Running automated data audit..."
    bash "$AUDIT_SCRIPT" --update-docs

    AUDIT_EXIT_CODE=$?

    if [ $AUDIT_EXIT_CODE -eq 0 ]; then
        echo ""
        echo "✅ Data audit completed successfully"
        echo "   All data sources are synchronized"
    else
        echo ""
        echo "⚠️  Data audit detected sync issues"
        echo "   Review the audit log for details"
        echo "   You may need to run: aws s3 sync ..."
    fi
else
    echo "❌ Error: Audit script not found at $AUDIT_SCRIPT"
    exit 1
fi

echo ""
echo "================================================"
echo "Post-Scrape Hook Complete"
echo "================================================"

exit $AUDIT_EXIT_CODE
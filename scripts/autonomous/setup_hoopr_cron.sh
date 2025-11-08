#!/bin/bash
#
# hoopR Cron Setup Script
# Adds hoopR scheduled scraper to crontab for 3 AM daily execution
#
# Usage:
#   bash scripts/autonomous/setup_hoopr_cron.sh
#

set -e

echo "=========================================================================="
echo "hoopR Autonomous Collection - Cron Setup"
echo "=========================================================================="
echo ""

# Configuration
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
CONDA_BASH="/opt/homebrew/bin/bash"
CRON_ENTRY="0 3 * * * cd $PROJECT_ROOT && $CONDA_BASH scripts/autonomous/run_scheduled_hoopr.sh \"--days 3\" >> logs/autonomous/cron_hoopr.log 2>&1"

# Check if conda bash exists
if [ ! -f "$CONDA_BASH" ]; then
    echo "❌ Error: Bash not found at: $CONDA_BASH"
    echo "   Please verify bash path"
    exit 1
fi

# Check if script exists
if [ ! -f "$PROJECT_ROOT/scripts/autonomous/run_scheduled_hoopr.sh" ]; then
    echo "❌ Error: hoopR scheduled script not found"
    echo "   Expected: $PROJECT_ROOT/scripts/autonomous/run_scheduled_hoopr.sh"
    exit 1
fi

# Check if entry already exists
if crontab -l 2>/dev/null | grep -q "run_scheduled_hoopr.sh"; then
    echo "⚠️  hoopR cron entry already exists!"
    echo ""
    echo "Current entry:"
    crontab -l | grep "run_scheduled_hoopr.sh"
    echo ""
    read -p "Replace with new entry? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled. No changes made."
        exit 0
    fi
    # Remove old entry
    crontab -l | grep -v "run_scheduled_hoopr.sh" | crontab -
    echo "✓ Removed old entry"
fi

# Add new cron entry
echo "Adding hoopR cron entry..."
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

# Verify
echo ""
echo "✓ Cron entry added successfully!"
echo ""
echo "Verification:"
crontab -l | grep "run_scheduled_hoopr.sh"
echo ""
echo "=========================================================================="
echo "hoopR Scheduled Scraper Configuration"
echo "=========================================================================="
echo "Schedule: Daily at 3:00 AM"
echo "Days back: 3 days (ESPN cross-validation)"
echo "Log file: logs/autonomous/cron_hoopr.log"
echo ""
echo "To verify after first run:"
echo "  tail -50 logs/autonomous/hoopr_scheduled_*.log"
echo "  python scripts/monitoring/dims_cli.py show --category hoopr_data"
echo ""
echo "To remove cron entry:"
echo "  crontab -e  # Delete the hoopR line, save and exit"
echo "=========================================================================="
echo ""
echo "✅ Setup complete! hoopR autonomous collection will start at 3 AM daily."

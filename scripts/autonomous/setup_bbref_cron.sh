#!/bin/bash
#
# Basketball Reference Cron Setup Script
# Adds Basketball Reference scheduled scraper to crontab for 4 AM Sunday weekly execution
#
# Usage:
#   bash scripts/autonomous/setup_bbref_cron.sh
#

set -e

echo "=========================================================================="
echo "Basketball Reference Autonomous Collection - Cron Setup"
echo "=========================================================================="
echo ""

# Configuration
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
CONDA_BASH="/opt/homebrew/bin/bash"
CRON_ENTRY="0 4 * * 0 cd $PROJECT_ROOT && $CONDA_BASH scripts/autonomous/run_scheduled_bbref.sh \"--days 7\" >> logs/autonomous/cron_bbref.log 2>&1"

# Check if conda bash exists
if [ ! -f "$CONDA_BASH" ]; then
    echo "❌ Error: Bash not found at: $CONDA_BASH"
    echo "   Please verify bash path"
    exit 1
fi

# Check if script exists
if [ ! -f "$PROJECT_ROOT/scripts/autonomous/run_scheduled_bbref.sh" ]; then
    echo "❌ Error: Basketball Reference scheduled script not found"
    echo "   Expected: $PROJECT_ROOT/scripts/autonomous/run_scheduled_bbref.sh"
    exit 1
fi

# Check if entry already exists
if crontab -l 2>/dev/null | grep -q "run_scheduled_bbref.sh"; then
    echo "⚠️  Basketball Reference cron entry already exists!"
    echo ""
    echo "Current entry:"
    crontab -l | grep "run_scheduled_bbref.sh"
    echo ""
    read -p "Replace with new entry? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled. No changes made."
        exit 0
    fi
    # Remove old entry
    crontab -l | grep -v "run_scheduled_bbref.sh" | crontab -
    echo "✓ Removed old entry"
fi

# Add new cron entry
echo "Adding Basketball Reference cron entry..."
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

# Verify
echo ""
echo "✓ Cron entry added successfully!"
echo ""
echo "Verification:"
crontab -l | grep "run_scheduled_bbref.sh"
echo ""
echo "=========================================================================="
echo "Basketball Reference Scheduled Scraper Configuration"
echo "=========================================================================="
echo "Schedule: Weekly at 4:00 AM every Sunday"
echo "Days back: 7 days (weekly historical validation)"
echo "Log file: logs/autonomous/cron_bbref.log"
echo "Rate limit: 20 req/min (3s delay between requests)"
echo ""
echo "To verify after first run:"
echo "  tail -50 logs/autonomous/bbref_scheduled_*.log"
echo "  python scripts/monitoring/dims_cli.py show --category basketball_reference_data"
echo ""
echo "To remove cron entry:"
echo "  crontab -e  # Delete the Basketball Reference line, save and exit"
echo "=========================================================================="
echo ""
echo "✅ Setup complete! Basketball Reference autonomous collection will start at 4 AM every Sunday."

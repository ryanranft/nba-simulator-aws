#!/bin/bash
#
# ESPN Cron Setup Script
# Adds ESPN scheduled scraper to crontab for 2 AM daily execution
#
# Usage:
#   bash scripts/autonomous/setup_espn_cron.sh
#

set -e

echo "=========================================================================="
echo "ESPN Autonomous Collection - Cron Setup"
echo "=========================================================================="
echo ""

# Configuration
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
CONDA_ENV="nba-aws"
CONDA_BASH="/Users/ryanranft/miniconda3/envs/nba-aws/bin/bash"
CRON_ENTRY="0 2 * * * cd $PROJECT_ROOT && $CONDA_BASH scripts/autonomous/run_scheduled_espn.sh \"--days 3\" >> logs/autonomous/cron_espn.log 2>&1"

# Check if conda environment exists
if [ ! -f "$CONDA_BASH" ]; then
    echo "❌ Error: Conda environment 'nba-aws' not found at: $CONDA_BASH"
    echo "   Please verify conda environment path"
    exit 1
fi

# Check if script exists
if [ ! -f "$PROJECT_ROOT/scripts/autonomous/run_scheduled_espn.sh" ]; then
    echo "❌ Error: ESPN scheduled script not found"
    echo "   Expected: $PROJECT_ROOT/scripts/autonomous/run_scheduled_espn.sh"
    exit 1
fi

# Check if entry already exists
if crontab -l 2>/dev/null | grep -q "run_scheduled_espn.sh"; then
    echo "⚠️  ESPN cron entry already exists!"
    echo ""
    echo "Current entry:"
    crontab -l | grep "run_scheduled_espn.sh"
    echo ""
    read -p "Replace with new entry? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled. No changes made."
        exit 0
    fi
    # Remove old entry
    crontab -l | grep -v "run_scheduled_espn.sh" | crontab -
    echo "✓ Removed old entry"
fi

# Add new cron entry
echo "Adding ESPN cron entry..."
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

# Verify
echo ""
echo "✓ Cron entry added successfully!"
echo ""
echo "Verification:"
crontab -l | grep "run_scheduled_espn.sh"
echo ""
echo "=========================================================================="
echo "ESPN Scheduled Scraper Configuration"
echo "=========================================================================="
echo "Schedule: Daily at 2:00 AM"
echo "Days back: 3 days (catches any missed games)"
echo "Log file: logs/autonomous/cron_espn.log"
echo ""
echo "Next run: $(date -v+1d -v2H -v0M -v0S '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "To verify tomorrow morning:"
echo "  tail -50 logs/autonomous/espn_scheduled_*.log"
echo "  python scripts/monitoring/dims_cli.py show --category espn_data"
echo ""
echo "To remove cron entry:"
echo "  crontab -e  # Delete the ESPN line, save and exit"
echo "=========================================================================="
echo ""
echo "✅ Setup complete! ESPN autonomous collection will start at 2 AM."

#!/bin/bash
# Pre-Flight Safety Check for Refactoring
# Ensures all safety measures in place before starting

set -e

PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
BACKUP_DIR="$PROJECT_ROOT/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "================================"
echo "PRE-FLIGHT SAFETY CHECK"
echo "================================"
echo ""

# Check we're in the right directory
cd "$PROJECT_ROOT" || exit 1

# Create backup directory if needed
mkdir -p "$BACKUP_DIR"

echo "✅ Step 1: Git Status Check"
echo "----------------------------"
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  WARNING: You have uncommitted changes"
    git status --short
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting. Please commit or stash changes first."
        exit 1
    fi
fi

echo "✅ Step 2: Create Safety Tag"
echo "-----------------------------"
SAFETY_TAG="pre-refactor-$DATE"
git tag "$SAFETY_TAG"
echo "Created git tag: $SAFETY_TAG"
echo ""

echo "✅ Step 3: Check for Running Processes"
echo "---------------------------------------"
echo "Checking for active NBA processes..."
ps aux | grep -i nba | grep -v grep | grep python || echo "No NBA Python processes found"
echo ""

echo "✅ Step 4: Check Cron Jobs"
echo "--------------------------"
if crontab -l > "$BACKUP_DIR/cron_backup_$DATE.txt" 2>/dev/null; then
    echo "Cron jobs backed up to: $BACKUP_DIR/cron_backup_$DATE.txt"
    grep -i nba "$BACKUP_DIR/cron_backup_$DATE.txt" || echo "No NBA-related cron jobs found"
else
    echo "No crontab configured"
fi
echo ""

echo "✅ Step 5: Document Current State"
echo "----------------------------------"
cat > "$BACKUP_DIR/system_state_$DATE.txt" << EOF
Refactoring Pre-Flight Check
============================
Date: $(date)
Git Tag: $SAFETY_TAG
Current Branch: $(git branch --show-current)
Last Commit: $(git log -1 --oneline)

Python Environment:
$(python --version 2>&1)
$(which python)

Project Structure:
Total Python files: $(find . -name "*.py" -not -path "./.git/*" -not -path "./venv/*" | wc -l)
Total test files: $(find ./tests -name "*.py" 2>/dev/null | wc -l || echo "0")
Total docs: $(find ./docs -name "*.md" 2>/dev/null | wc -l || echo "0")
EOF

echo "System state documented: $BACKUP_DIR/system_state_$DATE.txt"
echo ""

echo "✅ Step 6: Verify Conda Environment"
echo "------------------------------------"
if [ "$CONDA_DEFAULT_ENV" = "nba-aws" ]; then
    echo "✅ Conda environment 'nba-aws' is active"
else
    echo "⚠️  WARNING: Expected conda environment 'nba-aws' but got: ${CONDA_DEFAULT_ENV:-none}"
    echo "Run: conda activate nba-aws"
fi
echo ""

echo "✅ Step 7: Check Required Packages"
echo "-----------------------------------"
python -c "import psycopg2; print('✅ psycopg2 installed')" 2>/dev/null || echo "❌ psycopg2 missing"
python -c "import boto3; print('✅ boto3 installed')" 2>/dev/null || echo "❌ boto3 missing"
python -c "import pandas; print('✅ pandas installed')" 2>/dev/null || echo "❌ pandas missing"
python -c "import pytest; print('✅ pytest installed')" 2>/dev/null || echo "❌ pytest missing"
echo ""

echo "================================"
echo "PRE-FLIGHT CHECK COMPLETE"
echo "================================"
echo ""
echo "Safety measures in place:"
echo "  ✅ Git tag created: $SAFETY_TAG"
echo "  ✅ System state documented"
echo "  ✅ Cron jobs backed up"
echo ""
echo "To rollback if needed:"
echo "  git checkout $SAFETY_TAG"
echo ""
echo "Ready to proceed with refactoring!"
echo ""

# Save the tag name for future reference
echo "$SAFETY_TAG" > "$BACKUP_DIR/latest_safety_tag.txt"

exit 0


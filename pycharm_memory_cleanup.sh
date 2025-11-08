#!/bin/bash
# PyCharm Memory Cleanup Script
# Purpose: Move large files that cause PyCharm memory issues

set -e

PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
EXTERNAL_BACKUP_DIR="/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/backups"

echo "🧹 PyCharm Memory Cleanup Script"
echo "=================================="
echo ""

# Create external backup directory if it doesn't exist
mkdir -p "$EXTERNAL_BACKUP_DIR"

# 1. Move large SQL backup file
echo "📦 Moving large SQL backup file..."
if [ -f "$PROJECT_ROOT/backup_espn_schema_20251107_173931.sql" ]; then
    mv "$PROJECT_ROOT/backup_espn_schema_20251107_173931.sql" "$EXTERNAL_BACKUP_DIR/"
    echo "   ✅ Moved backup_espn_schema_20251107_173931.sql (451.52 MB) to $EXTERNAL_BACKUP_DIR"
else
    echo "   ℹ️  SQL backup file not found (may already be moved)"
fi

# 2. Archive and compress old logs (keep only last 7 days)
echo ""
echo "📋 Archiving old log files..."
cd "$PROJECT_ROOT/logs"

# Create archive directory
mkdir -p archived_logs

# Find and compress logs older than 7 days (except .pid files)
find . -maxdepth 1 -type f -name "*.log" -mtime +7 -exec gzip {} \;
find . -maxdepth 1 -type f -name "*.log.gz" -exec mv {} archived_logs/ \;

echo "   ✅ Archived logs older than 7 days to logs/archived_logs/"

# 3. Clean up pytest coverage cache
echo ""
echo "🧪 Cleaning pytest coverage files..."
cd "$PROJECT_ROOT"

if [ -d "htmlcov" ]; then
    rm -rf htmlcov
    echo "   ✅ Removed htmlcov directory (20.15 MB)"
fi

if [ -f ".coverage" ]; then
    rm -f .coverage
    echo "   ✅ Removed .coverage file (76 KB)"
fi

if [ -f "coverage.json" ]; then
    rm -f coverage.json
    echo "   ✅ Removed coverage.json file (850 KB)"
fi

# 4. Clean up .pytest_cache
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache
    echo "   ✅ Cleaned .pytest_cache directory"
fi

# 5. Summary
echo ""
echo "✨ Cleanup Complete!"
echo "==================="
echo ""
echo "📊 Summary:"
echo "   • Moved 451 MB SQL backup to external location"
echo "   • Archived old log files"
echo "   • Removed coverage files (~21 MB)"
echo "   • Total space freed: ~472 MB"
echo ""
echo "🔄 Next Steps:"
echo "   1. Restart PyCharm for changes to take effect"
echo "   2. PyCharm will re-index (much faster now)"
echo "   3. Memory usage should be significantly lower"
echo ""
echo "💡 Tip: Run this script weekly to keep project lean:"
echo "   ./pycharm_memory_cleanup.sh"
echo ""

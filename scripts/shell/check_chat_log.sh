#!/bin/bash
# Helper script to check for CHAT_LOG.md before commits
# Usage: bash scripts/shell/check_chat_log.sh

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 CHAT LOG CHECK"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "CHAT_LOG.md" ]; then
    # Check file age
    file_age_seconds=$(( $(date +%s) - $(stat -f %m CHAT_LOG.md) ))
    file_age_minutes=$(( file_age_seconds / 60 ))
    file_age_hours=$(( file_age_minutes / 60 ))
    file_size=$(stat -f %z CHAT_LOG.md)

    echo -e "${GREEN}✓${NC} CHAT_LOG.md exists"
    echo ""
    echo "  File size: $(numfmt --to=iec $file_size 2>/dev/null || echo "$file_size bytes")"

    if [ $file_age_hours -lt 1 ]; then
        echo -e "  Last updated: ${GREEN}$file_age_minutes minutes ago${NC}"
    elif [ $file_age_hours -lt 24 ]; then
        echo -e "  Last updated: ${GREEN}$file_age_hours hours ago${NC}"
    else
        file_age_days=$(( file_age_hours / 24 ))
        echo -e "  Last updated: ${YELLOW}$file_age_days days ago${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  Chat log may be stale${NC}"
        echo "   Consider exporting your latest Claude Code conversation"
    fi

    echo ""
    echo -e "${GREEN}✓ Ready for commit${NC}"
    echo ""
    echo "  The pre-commit hook will archive this to:"
    echo "  ~/sports-simulator-archives/nba/<commit-hash>/CHAT_LOG_*.md"

else
    echo -e "${YELLOW}⚠️  CHAT_LOG.md not found${NC}"
    echo ""
    echo "  This commit will proceed without conversation context."
    echo ""
    echo "  To preserve Claude Code conversations:"
    echo "  1. Export conversation from Claude Code"
    echo "  2. Save as: CHAT_LOG.md in project root"
    echo "  3. Re-run this check before committing"
    echo ""
    echo -e "${BLUE}💡 Tip:${NC} Export conversations after significant work sessions"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
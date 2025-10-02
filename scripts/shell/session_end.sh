#!/bin/bash
# Session end reminder - prompts user to export Claude Code conversation
# Usage: bash scripts/shell/session_end.sh
# Or add to shell alias: alias end-session='bash scripts/shell/session_end.sh'

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              SESSION END CHECKLIST                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Check for uncommitted changes
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 1. GIT STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  You have uncommitted changes:${NC}"
    echo ""
    git status --short | head -10
    if [ $(git status --short | wc -l) -gt 10 ]; then
        echo "   ... ($(git status --short | wc -l) total files changed)"
    fi
    echo ""
    echo -e "${BLUE}💡 Consider:${NC}"
    echo "   - Review changes: git diff"
    echo "   - Commit work: git add . && git commit"
    echo "   - Or stash: git stash save \"WIP: session end $(date +%Y-%m-%d)\""
else
    echo -e "${GREEN}✓ No uncommitted changes${NC}"
fi

echo ""

# 2. Claude Code conversation export
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💬 2. CLAUDE CODE CONVERSATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "CHAT_LOG.md" ]; then
    file_age_seconds=$(( $(date +%s) - $(stat -f %m CHAT_LOG.md) ))
    file_age_minutes=$(( file_age_seconds / 60 ))
    file_age_hours=$(( file_age_minutes / 60 ))

    if [ $file_age_hours -lt 1 ]; then
        echo -e "${GREEN}✓ CHAT_LOG.md exists (updated $file_age_minutes minutes ago)${NC}"
        echo ""
        echo -e "${BLUE}💡 Workflow:${NC}"
        echo "   1. Commit your changes: git add . && git commit -m 'message'"
        echo "   2. Archive conversation: bash scripts/maintenance/archive_chat_by_next_sha.sh"
        echo "   3. This saves the chat with the commit SHA it produced"
    else
        file_age_days=$(( file_age_hours / 24 ))
        echo -e "${YELLOW}⚠️  CHAT_LOG.md is $file_age_hours hours old${NC}"
        echo ""
        echo -e "${CYAN}📝 ACTION NEEDED:${NC}"
        echo "   1. Export your latest Claude Code conversation"
        echo "   2. Save/overwrite as: CHAT_LOG.md"
        echo "   3. Commit changes, then archive conversation"
    fi
else
    echo -e "${YELLOW}⚠️  CHAT_LOG.md not found${NC}"
    echo ""
    echo -e "${CYAN}📝 RECOMMENDED WORKFLOW:${NC}"
    echo "   1. Export Claude Code conversation → Save as CHAT_LOG.md"
    echo "   2. Stage and commit changes → git add . && git commit"
    echo "   3. Archive conversation → bash scripts/maintenance/archive_chat_by_next_sha.sh"
    echo "   4. This saves chat as: chat-<SHA>-sanitized.md"
    echo ""
    echo -e "${BLUE}💡 Why this matters:${NC}"
    echo "   - Each conversation linked to the commit it produced"
    echo "   - Future LLMs can trace: 'What work led to commit X?'"
    echo "   - Preserves full context for reproducing this pipeline"
    echo "   - Archive: ~/sports-simulator-archives/nba/conversations/"
fi

echo ""

# 3. Documentation updates
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 3. DOCUMENTATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docs_to_check=0

# Check COMMAND_LOG.md
if grep -q "## Session: $(date +%Y-%m-%d)" COMMAND_LOG.md 2>/dev/null; then
    echo -e "${GREEN}✓${NC} COMMAND_LOG.md updated today"
else
    echo -e "${YELLOW}⚠️${NC}  COMMAND_LOG.md not updated today"
    docs_to_check=$((docs_to_check + 1))
fi

# Check PROGRESS.md
if grep -q "Last Updated: $(date +%Y-%m-%d)" PROGRESS.md 2>/dev/null; then
    echo -e "${GREEN}✓${NC} PROGRESS.md updated today"
else
    echo -e "${YELLOW}⚠️${NC}  PROGRESS.md not updated today"
    docs_to_check=$((docs_to_check + 1))
fi

# Check FILE_INVENTORY.md age
if [ -f "FILE_INVENTORY.md" ]; then
    inventory_age=$(( ($(date +%s) - $(stat -f %m FILE_INVENTORY.md)) / 86400 ))
    if [ $inventory_age -gt 7 ]; then
        echo -e "${YELLOW}⚠️${NC}  FILE_INVENTORY.md is $inventory_age days old (consider: make inventory)"
        docs_to_check=$((docs_to_check + 1))
    else
        echo -e "${GREEN}✓${NC} FILE_INVENTORY.md is current"
    fi
fi

if [ $docs_to_check -gt 0 ]; then
    echo ""
    echo -e "${BLUE}💡 Consider updating documentation before next session${NC}"
fi

echo ""

# 4. Next session prep
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 4. NEXT SESSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check PROGRESS.md for next pending task
next_task=$(grep -m 1 "⏸️" PROGRESS.md 2>/dev/null | sed 's/^[[:space:]]*//' | head -c 80)
if [ -n "$next_task" ]; then
    echo "Next pending task in PROGRESS.md:"
    echo "  ${next_task}..."
else
    echo "No pending tasks in PROGRESS.md"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✓ Session end checklist complete                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}👋 Session ended at $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
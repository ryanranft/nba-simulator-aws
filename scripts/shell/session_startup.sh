#!/bin/bash
# Session startup - Full diagnostics with concise output

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║ SESSION STARTUP: $(date '+%Y-%m-%d %H:%M:%S')                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# HARDWARE
echo ""
echo "▶ HARDWARE"
system_profiler SPHardwareDataType | grep -E "Model Name|Model Identifier|Chip|Total Number of Cores|Memory" | sed 's/^[[:space:]]*/  /'

# SYSTEM
echo ""
echo "▶ SYSTEM"
sw_vers | sed 's/^/  /'
echo "  Homebrew: $(brew --version | head -1 | awk '{print $2}') @ $(which brew)"

# CONDA
echo ""
echo "▶ CONDA ENVIRONMENT"
echo "  Version: $(conda --version | awk '{print $2}')"
echo "  Base: $(conda info --base)"
conda env list | grep '*' | sed 's/^/  Active: /'

# PYTHON
echo ""
echo "▶ PYTHON"
echo "  Version: $(python --version 2>&1)"
echo "  Location: $(which python)"
echo "  Packages:"
pip show boto3 pandas numpy 2>/dev/null | grep -E "^(Name|Version|Location):" | awk '{
    if ($1 == "Name:") name=$2
    if ($1 == "Version:") version=$2
    if ($1 == "Location:") {print "    - " name " " version " @ " $2; name=""; version=""}
}'

# AWS CLI
echo ""
echo "▶ AWS CLI"
aws --version 2>&1 | sed 's/^/  /'
echo "  Location: $(which aws)"

# GIT
echo ""
echo "▶ GIT"
echo "  Version: $(git --version)"
echo "  Location: $(which git)"
echo ""
echo "  Status:"
git status --short | head -20 | sed 's/^/    /'
if [ $(git status --short | wc -l) -gt 20 ]; then
    echo "    ... ($(git status --short | wc -l) total files changed)"
fi
echo "  Branch: $(git branch --show-current)"
echo "  Recent commits:"
git log --oneline -3 | sed 's/^/    /'

# DOCUMENTATION STATUS CHECKS
echo ""
echo "▶ DOCUMENTATION STATUS"

# Check FILE_INVENTORY.md age
if [ -f "FILE_INVENTORY.md" ]; then
    inventory_age=$(( ($(date +%s) - $(stat -f %m FILE_INVENTORY.md)) / 86400 ))
    if [ $inventory_age -gt 7 ]; then
        echo "  ⚠️  FILE_INVENTORY.md is $inventory_age days old - consider running 'make inventory'"
    else
        echo "  ✓ FILE_INVENTORY.md is up to date ($inventory_age days old)"
    fi
else
    echo "  ⚠️  FILE_INVENTORY.md not found - run 'make inventory'"
fi

# Check .session-history.md existence
if [ -f ".session-history.md" ]; then
    session_entries=$(grep -c "SESSION STARTUP:" .session-history.md 2>/dev/null || echo "0")
    echo "  ✓ Session history active ($session_entries entries logged)"
else
    echo "  ⚠️  .session-history.md not found - create it with 'touch .session-history.md'"
fi

# Check COMMAND_LOG.md existence
if [ -f "COMMAND_LOG.md" ]; then
    cmd_entries=$(grep -c "^### " COMMAND_LOG.md 2>/dev/null || echo "0")
    echo "  ✓ Command log active ($cmd_entries sessions logged)"
else
    echo "  ⚠️  COMMAND_LOG.md not found - run 'source scripts/shell/log_command.sh'"
fi

# Check PROGRESS.md status
if [ -f "PROGRESS.md" ]; then
    pending_tasks=$(grep -c "⏸️" PROGRESS.md 2>/dev/null || echo "0")
    in_progress=$(grep -c "⏳" PROGRESS.md 2>/dev/null || echo "0")
    if [ $pending_tasks -gt 0 ] || [ $in_progress -gt 0 ]; then
        echo "  📋 PROGRESS.md: $pending_tasks pending, $in_progress in progress"
    else
        echo "  ✓ PROGRESS.md: No pending tasks"
    fi
else
    echo "  ⚠️  PROGRESS.md not found"
fi

# Check for stale documentation (30+ days)
echo ""
echo "  Checking for stale documentation (30+ days old)..."
stale_found=0
for doc in docs/SETUP.md docs/TROUBLESHOOTING.md docs/STYLE_GUIDE.md QUICKSTART.md; do
    if [ -f "$doc" ]; then
        doc_age=$(( ($(date +%s) - $(stat -f %m "$doc")) / 86400 ))
        if [ $doc_age -gt 30 ]; then
            echo "    ⚠️  $doc is $doc_age days old - review if needed"
            stale_found=1
        fi
    fi
done
if [ $stale_found -eq 0 ]; then
    echo "    ✓ All documentation is recent (< 30 days)"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║ ✓ Diagnostics complete - ready to work                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# CHAT LOG REMINDER
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💬 CLAUDE CODE CONVERSATION TRACKING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -f "CHAT_LOG.md" ]; then
    file_age_seconds=$(( $(date +%s) - $(stat -f %m CHAT_LOG.md) ))
    file_age_hours=$(( file_age_seconds / 3600 ))

    if [ $file_age_hours -lt 24 ]; then
        echo "✓ CHAT_LOG.md found (updated $file_age_hours hours ago)"
    else
        file_age_days=$(( file_age_hours / 24 ))
        echo "⚠️  CHAT_LOG.md is $file_age_days days old"
        echo "   Consider exporting your latest Claude Code conversations"
    fi
else
    echo "💡 Reminder: Export Claude Code conversations to CHAT_LOG.md"
    echo ""
    echo "   This preserves conversation context and enables pre-commit archiving."
    echo "   Export from Claude Code and save as: CHAT_LOG.md"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# CONVERSATION LOGGING (if not already logging)
if [ -z "$SCRIPT_LOGGING" ]; then
    # Check if user wants to start conversation logging
    PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
    PROJECT_NAME=$(basename "$PROJECT_DIR")
    SPORT=$(echo "$PROJECT_NAME" | sed -E 's/^([a-z]+)-simulator.*/\1/')

    ARCHIVE_BASE="${ARCHIVE_BASE:-$HOME/sports-simulator-archives/$SPORT}"
    SESSION_DIR="$ARCHIVE_BASE/sessions"
    SESSION_FILE="$SESSION_DIR/session-$(date +%Y%m%d-%H%M%S).log"

    # Create session directory if needed
    mkdir -p "$SESSION_DIR"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 CONVERSATION LOGGING"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "💡 Recommendation: Log this session to preserve conversation context"
    echo ""
    echo "   This prevents information loss if session is interrupted."
    echo "   Log will be saved to: $SESSION_FILE"
    echo ""
    echo "⚠️  Log may contain credentials and sensitive data"
    echo "   (saved outside git repo, never committed)"
    echo ""
    read -p "Start conversation logging? [Y/n]: " start_logging

    if [[ ! $start_logging =~ ^[Nn]$ ]]; then
        echo ""
        echo "✅ Starting conversation logger..."
        echo "📍 Log location: $SESSION_FILE"
        echo ""
        echo "💡 To stop logging and end session: type 'exit' or press Ctrl+D"
        echo ""

        # Export flag so we don't prompt again
        export SCRIPT_LOGGING=1

        # Start script recording
        exec script -a "$SESSION_FILE"
    else
        echo ""
        echo "⏭️  Skipping conversation logging"
        echo ""
        echo "💡 To start logging manually later:"
        echo "   script -a ~/sports-simulator-archives/$SPORT/sessions/session-\$(date +%Y%m%d-%H%M%S).log"
        echo ""
    fi
fi
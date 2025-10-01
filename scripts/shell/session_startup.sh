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
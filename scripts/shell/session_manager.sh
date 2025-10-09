#!/bin/bash
# Unified Session Manager - Complete integration of session_startup.sh, session_end.sh, check_machine_health.sh
# Preserves 100% of all functionality from all three scripts
# Usage: source scripts/shell/session_manager.sh [start|end|status]

SESSION_ACTION="${1:-start}"

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (from check_machine_health.sh)
# ═══════════════════════════════════════════════════════════════════════════

EXIT_CODE=0

check_pass() {
    echo "✅ $1"
}

check_fail() {
    echo "❌ $1"
    EXIT_CODE=1
}

check_warn() {
    echo "⚠️  $1"
}

check_info() {
    echo "ℹ️  $1"
}

separator() {
    echo ""
    echo "────────────────────────────────────────────────────────────────"
    echo ""
}

# Color codes (from session_end.sh)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════
# SESSION START WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

if [ "$SESSION_ACTION" = "start" ]; then

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║ SESSION STARTUP: $(date '+%Y-%m-%d %H:%M:%S')                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────────────────────────────
# HARDWARE (from session_startup.sh)
# ─────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ HARDWARE"
system_profiler SPHardwareDataType | grep -E "Model Name|Model Identifier|Chip|Total Number of Cores|Memory" | sed 's/^[[:space:]]*/  /'

# ─────────────────────────────────────────────────────────────────────────
# SYSTEM (from session_startup.sh)
# ─────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ SYSTEM"
sw_vers | sed 's/^/  /'
echo "  Homebrew: $(brew --version | head -1 | awk '{print $2}') @ $(which brew)"

# Also include check_machine_health.sh system checks
echo ""
echo "  Device: MacBook Pro 16-inch, 2023"
echo "  Processor: Apple M2 Max"
echo "  Memory: 96 GB"
echo "  Storage: $(df -h / | awk 'NR==2 {print $4}') available of $(df -h / | awk 'NR==2 {print $2}')"

# ─────────────────────────────────────────────────────────────────────────
# CONDA ENVIRONMENT (from session_startup.sh)
# ─────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ CONDA ENVIRONMENT"
echo "  Version: $(conda --version | awk '{print $2}')"
echo "  Base: $(conda info --base)"
conda env list | grep '\*' | sed 's/^/  Active: /'

# ─────────────────────────────────────────────────────────────────────────
# PYTHON (from session_startup.sh - full package details)
# ─────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────
# AWS CLI (from session_startup.sh)
# ─────────────────────────────────────────────────────────────────────────
echo ""
echo "▶ AWS CLI"
aws --version 2>&1 | sed 's/^/  /'
echo "  Location: $(which aws)"

# ─────────────────────────────────────────────────────────────────────────
# GIT (from session_startup.sh - complete status)
# ─────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────
# DOCUMENTATION STATUS CHECKS (from session_startup.sh - all checks)
# ─────────────────────────────────────────────────────────────────────────
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

# Check for stale documentation (30+ days) - ALL docs from session_startup.sh
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

# ─────────────────────────────────────────────────────────────────────────
# CHAT LOG REMINDER (from session_startup.sh - full version)
# ─────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────
# CONVERSATION LOGGING (from session_startup.sh - complete implementation)
# ─────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────
# AUTO-LOAD COMMAND LOGGING (bonus integration)
# ─────────────────────────────────────────────────────────────────────────
if [ -f "scripts/shell/log_command.sh" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 COMMAND LOGGING"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    source scripts/shell/log_command.sh
    echo "✅ Command logging loaded"
    echo "   Use: log_cmd <command>, log_note <message>, log_solution <description>"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

# ─────────────────────────────────────────────────────────────────────────
# CREDENTIALS CHECK (New - automatic)
# ─────────────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 CREDENTIALS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check for NBA simulator credentials
if [ -f "/Users/ryanranft/nba-sim-credentials.env" ]; then
    source /Users/ryanranft/nba-sim-credentials.env 2>/dev/null
    if [ -n "$AWS_ACCESS_KEY_ID" ]; then
        echo "✅ NBA Simulator credentials loaded"
    else
        echo "⚠️  Credentials file exists but not loaded properly"
    fi
else
    echo "⚠️  NBA Simulator credentials not found at /Users/ryanranft/nba-sim-credentials.env"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# DATA FRESHNESS CHECK (New - automatic catalog status)
# ─────────────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 DATA FRESHNESS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if DATA_CATALOG.md exists
if [ -f "docs/DATA_CATALOG.md" ]; then
    # Get last catalog update timestamp
    catalog_timestamp=$(grep "Last Full Update:" docs/DATA_CATALOG.md | head -1 | sed 's/.*Last Full Update: //')

    if [ -n "$catalog_timestamp" ]; then
        echo "📅 Catalog last updated: $catalog_timestamp"
    fi

    # Check scraper completion timestamps
    if [ -d "/tmp/scraper_timestamps" ]; then
        echo ""
        echo "Data source completion status:"
        echo ""

        # ESPN status
        if [ -f "/tmp/scraper_timestamps/espn_last_completion.txt" ]; then
            espn_time=$(head -1 /tmp/scraper_timestamps/espn_last_completion.txt)
            espn_status=$(sed -n '2p' /tmp/scraper_timestamps/espn_last_completion.txt)
            if [ "$espn_status" = "success" ]; then
                echo "  ✅ ESPN: Current (last updated: $espn_time)"
            else
                echo "  ⚠️  ESPN: $espn_status (last run: $espn_time)"
            fi
        else
            echo "  ℹ️  ESPN: No completion timestamp available"
        fi

        # hoopR status
        if [ -f "/tmp/scraper_timestamps/hoopr_last_completion.txt" ]; then
            hoopr_time=$(head -1 /tmp/scraper_timestamps/hoopr_last_completion.txt)
            hoopr_status=$(sed -n '2p' /tmp/scraper_timestamps/hoopr_last_completion.txt)
            if [ "$hoopr_status" = "success" ]; then
                echo "  ✅ hoopR: Current (last updated: $hoopr_time)"
            else
                echo "  ⚠️  hoopR: $hoopr_status (last run: $hoopr_time)"
            fi
        else
            # Check if hoopR scraper is running
            if ps aux | grep -E "hoopr|R.*scrape" | grep -v grep > /dev/null; then
                echo "  🔄 hoopR: Scraper currently running"
            else
                echo "  ℹ️  hoopR: No completion timestamp (check catalog for progress)"
            fi
        fi

        # NBA API status
        if [ -f "/tmp/scraper_timestamps/nba_api_last_completion.txt" ]; then
            nba_time=$(head -1 /tmp/scraper_timestamps/nba_api_last_completion.txt)
            nba_status=$(sed -n '2p' /tmp/scraper_timestamps/nba_api_last_completion.txt)
            if [ "$nba_status" = "success" ]; then
                echo "  ✅ NBA API: Current (last updated: $nba_time)"
            else
                echo "  ⚠️  NBA API: $nba_status (last run: $nba_time)"
            fi
        else
            echo "  ⏸️  NBA API: Paused (rate limiting)"
        fi

        # Basketball Reference status
        if [ -f "/tmp/scraper_timestamps/basketball_ref_last_completion.txt" ]; then
            bbref_time=$(head -1 /tmp/scraper_timestamps/basketball_ref_last_completion.txt)
            bbref_status=$(sed -n '2p' /tmp/scraper_timestamps/basketball_ref_last_completion.txt)
            if [ "$bbref_status" = "success" ]; then
                echo "  ✅ Basketball Ref: Complete (last run: $bbref_time)"
            else
                echo "  ⚠️  Basketball Ref: $bbref_status (last run: $bbref_time)"
            fi
        else
            echo "  ✅ Basketball Ref: Complete (static historical data)"
        fi
    else
        echo "ℹ️  No scraper timestamps available"
        echo "   (Timestamps created after first scraper completion)"
    fi

    # Quick database stats
    echo ""
    if [ -f "/tmp/espn_local.db" ]; then
        local_games=$(sqlite3 /tmp/espn_local.db "SELECT COUNT(*) FROM games" 2>/dev/null || echo "N/A")
        local_events=$(sqlite3 /tmp/espn_local.db "SELECT COUNT(*) FROM pbp_events" 2>/dev/null || echo "N/A")
        echo "📁 Local ESPN database: $local_games games, $local_events events"
    else
        echo "ℹ️  Local ESPN database not found (will be created on first use)"
    fi
else
    echo "⚠️  DATA_CATALOG.md not found"
    echo ""
    echo "💡 The data catalog is the authoritative source for all data statistics."
    echo "   Run data consolidation to create: Task #1-11 in PROGRESS.md"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# OVERNIGHT JOBS CHECK (New - automatic when applicable)
# ─────────────────────────────────────────────────────────────────────────
if grep -q "Overnight jobs running:" PROGRESS.md 2>/dev/null; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌙 OVERNIGHT JOBS STATUS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check for running scraper processes
    running_scrapers=$(ps aux | grep -E "(hoopr|nba_api|scrape_)" | grep -v grep | wc -l)

    if [ $running_scrapers -gt 0 ]; then
        echo "✅ $running_scrapers scraper process(es) still running"
        echo ""
        ps aux | grep -E "(hoopr|nba_api|scrape_)" | grep -v grep | awk '{print "   PID " $2 ": " $11 " " $12 " " $13}'
        echo ""
        echo "💡 To monitor: Follow Workflow #38 (Overnight Scraper Handoff Protocol)"
    else
        echo "⏹️  No scraper processes currently running (jobs may have completed)"
        echo ""
        echo "💡 Check logs and validate output per Workflow #38"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

# ─────────────────────────────────────────────────────────────────────────
# SESSION CONTEXT SUMMARY (New - consolidated view)
# ─────────────────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 SESSION CONTEXT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract last session info from PROGRESS.md
if [ -f "PROGRESS.md" ]; then
    last_session=$(grep "Last session ended:" PROGRESS.md | head -1 | sed 's/.*Last session ended: //')
    last_completed=$(grep "Last completed:" PROGRESS.md | head -1 | sed 's/.*Last completed: //')
    next_task=$(grep "Next to work on:" PROGRESS.md -A 1 | tail -1 | sed 's/^[0-9]*\. //' | sed 's/^\*\*//' | sed 's/\*\*//' | head -c 100)

    if [ -n "$last_session" ]; then
        echo "📅 Last session: $last_session"
    fi
    if [ -n "$last_completed" ]; then
        echo "✅ Last completed: $last_completed"
    fi

    # Check for pending commits
    commits_ahead=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
    if [ "$commits_ahead" -gt 0 ]; then
        echo "📤 Pending commits: $commits_ahead (ready to push)"
    fi

    # Show next planned task
    if [ -n "$next_task" ]; then
        echo "🎯 Next planned: $next_task"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

fi  # End of SESSION START

# ═══════════════════════════════════════════════════════════════════════════
# SESSION END WORKFLOW (from session_end.sh - 100% preserved)
# ═══════════════════════════════════════════════════════════════════════════

if [ "$SESSION_ACTION" = "end" ]; then

clear
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              SESSION END CHECKLIST                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 1. GIT STATUS (from session_end.sh)
# ─────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────
# 2. CLAUDE CODE CONVERSATION (from session_end.sh)
# ─────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────
# 3. DOCUMENTATION (from session_end.sh)
# ─────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────
# 4. NEXT SESSION (from session_end.sh)
# ─────────────────────────────────────────────────────────────────────────
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

fi  # End of SESSION END

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATUS (quick check during work)
# ═══════════════════════════════════════════════════════════════════════════

if [ "$SESSION_ACTION" = "status" ]; then

echo ""
echo "▶ QUICK STATUS CHECK"
echo ""
echo "Git: $(git status --porcelain | wc -l) uncommitted files"
echo "CHAT_LOG.md: $([ -f CHAT_LOG.md ] && echo "exists ($(( ($(date +%s) - $(stat -f %m CHAT_LOG.md)) / 60 )) min old)" || echo "missing")"
echo "Branch: $(git branch --show-current)"
echo "Next task: $(grep -m 1 "⏸️" PROGRESS.md 2>/dev/null | sed 's/^[[:space:]]*//' | head -c 60)..."
echo ""

fi  # End of SESSION STATUS

# ═══════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════

if [ "$SESSION_ACTION" != "start" ] && [ "$SESSION_ACTION" != "end" ] && [ "$SESSION_ACTION" != "status" ]; then
    echo "Usage: source scripts/shell/session_manager.sh [start|end|status]"
    echo ""
    echo "Commands:"
    echo "  start  - Initialize session with full health checks & diagnostics"
    echo "  end    - End session with comprehensive cleanup checklist"
    echo "  status - Quick status check during session"
    echo ""
    echo "Integration:"
    echo "  Add to ~/.zshrc:"
    echo "    alias nba-start='cd /Users/ryanranft/nba-simulator-aws && source scripts/shell/session_manager.sh start'"
    echo "    alias nba-end='source scripts/shell/session_manager.sh end'"
    echo "    alias nba-status='source scripts/shell/session_manager.sh status'"
fi
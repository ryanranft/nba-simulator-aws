#!/bin/bash
# Unified Archive Manager - Consolidates archive_gitignored_files.sh, archive_chat_log.sh, generate_commit_logs.sh
# Provides multiple modes for different archiving scenarios

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

# Auto-detect sport from directory name
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_NAME=$(basename "$PROJECT_DIR")
SPORT=$(echo "$PROJECT_NAME" | sed -E 's/^([a-z]+)-simulator.*/\1/')

# Archive base with sport-specific subfolder (configurable via environment variable)
ARCHIVE_BASE="${ARCHIVE_BASE:-$HOME/sports-simulator-archives/$SPORT}"

# Mode selection
MODE="${1:-full}"

# ============================================================================
# SHARED UTILITY FUNCTIONS
# ============================================================================

detect_sport() {
    echo "$SPORT"
}

get_git_info() {
    cd "$PROJECT_DIR"
    CURRENT_SHA=$(git rev-parse HEAD)
    SHORT_SHA=$(git rev-parse --short HEAD)
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    COMMIT_DATE=$(git log -1 --format=%ci)
    COMMIT_MSG=$(git log -1 --format=%s)
}

create_archive_dir() {
    ARCHIVE_DIR="$ARCHIVE_BASE/$CURRENT_SHA"
    mkdir -p "$ARCHIVE_DIR"
}

sanitize_credentials() {
    local original_file="$1"
    local sanitized_file="$2"

    python3 - "$original_file" "$sanitized_file" << 'PYTHON_EOF'
import re
import sys

# Get filenames from command line arguments
original_file = sys.argv[1]
sanitized_file = sys.argv[2]

# Read the complete ORIGINAL log
with open(original_file, 'r') as f:
    content = f.read()

# Redact patterns - Updated regex to match real AWS credential formats
redactions = [
    (r'AWS_ACCESS_KEY[A-Z0-9_]*=\S+', 'AWS_ACCESS_KEY[REDACTED]'),
    (r'aws_secret_access_key=\S+', 'aws_secret_access_key=[REDACTED]'),
    (r'aws_session_token=\S+', 'aws_session_token=[REDACTED]'),
    (r'(Password|password|PASSWORD):\s*\S+', r'\1: [REDACTED]'),
    (r'Bearer [A-Za-z0-9_-]+', 'Bearer [REDACTED]'),
    (r'ghp_[A-Za-z0-9]{36}', 'ghp_[REDACTED]'),
    (r'github_pat_[A-Za-z0-9_]+', 'github_pat_[REDACTED]'),
    (r'postgresql://[^:]+:[^@]+@', 'postgresql://[USER]:[REDACTED]@'),
    (r'postgres:[^@]+@', 'postgres:[REDACTED]@'),
]

for pattern, replacement in redactions:
    content = re.sub(pattern, replacement, content)

# Write sanitized content
with open(sanitized_file, 'w') as f:
    f.write(content)
PYTHON_EOF
}

commit_to_archive_git() {
    local commit_msg="$1"

    if [ -d "$ARCHIVE_BASE/.git" ]; then
        cd "$ARCHIVE_BASE"
        git add . > /dev/null 2>&1
        if git commit -m "$commit_msg" --quiet 2>/dev/null; then
            echo "  ✓ Committed to local archive git repo"
        fi
        cd "$PROJECT_DIR"
    fi
}

update_git_info() {
    local file="$1"
    local description="$2"

    if [ -f "$ARCHIVE_DIR/git-info.txt" ]; then
        echo "✅ $file ($description)" >> "$ARCHIVE_DIR/git-info.txt"
    fi
}

update_index() {
    local file_count="$1"

    INDEX_FILE="$ARCHIVE_BASE/README.md"

    if [ ! -f "$INDEX_FILE" ]; then
        cat > "$INDEX_FILE" << EOF
# ${SPORT^^} Simulator Archive - Gitignored Files

This archive contains \`.gitignored\` documentation files organized by git commit SHA.

Each folder corresponds to a specific git commit and contains:
- \`git-info.txt\` - Git metadata (SHA, date, message)
- Documentation files that were excluded from GitHub
- Log files (excluding massive extraction logs)

## How to Use

1. Find the git commit SHA from your project history
2. Navigate to the corresponding folder
3. All gitignored documentation files from that commit are preserved

## Folders

EOF
    fi

    # Add entry to index if not already present
    if ! grep -q "$CURRENT_SHA" "$INDEX_FILE"; then
        echo "- **$SHORT_SHA** - $BRANCH - $(date +%Y-%m-%d) - $COMMIT_MSG ($file_count files)" >> "$INDEX_FILE"
        echo "  📝 Updated archive index"
    fi
}

# ============================================================================
# MODE: GITIGNORED - Archive .gitignored operational files
# ============================================================================

mode_gitignored() {
    echo "📦 Archiving .gitignored files for commit: $SHORT_SHA"
    echo "📁 Archive location: $ARCHIVE_DIR"

    # Create git metadata file
    cat > "$ARCHIVE_DIR/git-info.txt" << EOF
=================================================================
GIT SNAPSHOT METADATA
=================================================================

Full SHA:     $CURRENT_SHA
Short SHA:    $SHORT_SHA
Branch:       $BRANCH
Commit Date:  $COMMIT_DATE
Commit Msg:   $COMMIT_MSG

=================================================================
ARCHIVED FILES
=================================================================

EOF

    # Files to archive (from .gitignore)
    FILES=(
        "COMMIT_VERIFICATION.md"
        "EXTRACTION_PROGRESS_SNAPSHOT.md"
        "EXTRACTION_STATUS.md"
        "OVERNIGHT_AUTOMATION_STATUS_old.md"
        "OVERNIGHT_EXTRACTION_STATUS.md"
        "PYCHARM_DATABASE_SETUP.md"
        "OVERNIGHT_AUTOMATION_STATUS.md"
        "OVERNIGHT_STATUS.md"
        "COMMAND_LOG.md"
    )

    # Archive each file if it exists
    COUNT=0
    for file in "${FILES[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            cp "$PROJECT_DIR/$file" "$ARCHIVE_DIR/" || true
            echo "✅ $file" >> "$ARCHIVE_DIR/git-info.txt"
            echo "  ✓ Archived: $file"
            COUNT=$((COUNT + 1))
        fi
    done

    # Archive log files (but not extract logs which are huge)
    if ls "$PROJECT_DIR"/*.log 1> /dev/null 2>&1; then
        mkdir -p "$ARCHIVE_DIR/logs"
        for logfile in "$PROJECT_DIR"/*.log; do
            filename=$(basename "$logfile")
            # Skip massive extract logs
            if [[ ! "$filename" =~ ^extract.*\.log$ ]]; then
                cp "$logfile" "$ARCHIVE_DIR/logs/"
                echo "✅ logs/$filename" >> "$ARCHIVE_DIR/git-info.txt"
                echo "  ✓ Archived: logs/$filename"
                ((COUNT++))
            fi
        done
    fi

    # Footer in git-info.txt
    cat >> "$ARCHIVE_DIR/git-info.txt" << EOF

=================================================================
Total files archived: $COUNT
Archive created: $(date)
=================================================================
EOF

    # Update master index
    update_index "$COUNT"

    echo ""
    echo "✅ Gitignored files archived!"
    echo "📊 Files archived: $COUNT"
    echo ""
    echo "To view later: ls $ARCHIVE_DIR"
    echo "To see all archives: cat $ARCHIVE_BASE/README.md"

    return $COUNT
}

# ============================================================================
# MODE: CONVERSATION - Archive CHAT_LOG.md with sanitization
# ============================================================================

mode_conversation() {
    echo "📝 Archiving chat conversation log for commit: $SHORT_SHA"
    echo "📁 Archive location: $ARCHIVE_DIR"

    # Check if Claude Code provides a chat log file
    CHAT_LOG_SOURCE="$PROJECT_DIR/CHAT_LOG.md"

    if [ ! -f "$CHAT_LOG_SOURCE" ]; then
        echo ""
        echo "ℹ️  No CHAT_LOG.md found in project directory"
        echo ""
        echo "To create a chat log:"
        echo "1. Export conversation from Claude Code interface"
        echo "2. Save as $CHAT_LOG_SOURCE"
        echo "3. Run this script again"
        echo ""
        return 1
    fi

    # Create sanitized copy
    SANITIZED_LOG="$ARCHIVE_DIR/CHAT_LOG_SANITIZED.md"
    ORIGINAL_LOG="$ARCHIVE_DIR/CHAT_LOG_ORIGINAL.md"

    echo "  🔒 Creating sanitized version..."

    # Check if archive files already exist (multiple sessions for same SHA)
    if [ -f "$ORIGINAL_LOG" ]; then
        echo "  📌 Existing chat logs found - appending new conversation..."
        echo "" >> "$ORIGINAL_LOG"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$ORIGINAL_LOG"
        echo "## Session: $(date '+%Y-%m-%d %H:%M:%S')" >> "$ORIGINAL_LOG"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$ORIGINAL_LOG"
        echo "" >> "$ORIGINAL_LOG"
        cat "$CHAT_LOG_SOURCE" >> "$ORIGINAL_LOG"
    else
        # First conversation for this SHA
        echo "  📝 Creating new chat log for SHA: $SHORT_SHA"
        echo "# Chat Log Archive for Commit: $SHORT_SHA" > "$ORIGINAL_LOG"
        echo "" >> "$ORIGINAL_LOG"
        echo "**Full SHA:** $CURRENT_SHA" >> "$ORIGINAL_LOG"
        echo "**Created:** $(date '+%Y-%m-%d %H:%M:%S')" >> "$ORIGINAL_LOG"
        echo "" >> "$ORIGINAL_LOG"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$ORIGINAL_LOG"
        echo "## Session: $(date '+%Y-%m-%d %H:%M:%S')" >> "$ORIGINAL_LOG"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$ORIGINAL_LOG"
        echo "" >> "$ORIGINAL_LOG"
        cat "$CHAT_LOG_SOURCE" >> "$ORIGINAL_LOG"
    fi

    # Create sanitized version with credentials redacted
    echo "  🔒 Sanitizing complete archive..."
    sanitize_credentials "$ORIGINAL_LOG" "$SANITIZED_LOG"

    # Update git-info.txt to include chat logs
    update_git_info "CHAT_LOG_ORIGINAL.md" "contains credentials - local only"
    update_git_info "CHAT_LOG_SANITIZED.md" "safe for sharing"

    echo "  ✓ Original saved: CHAT_LOG_ORIGINAL.md (with credentials)"
    echo "  ✓ Sanitized saved: CHAT_LOG_SANITIZED.md (safe for sharing)"
    echo ""
    echo "✅ Chat log archived successfully!"
    echo ""
    echo "⚠️  Security Note:"
    echo "   - ORIGINAL: Contains passwords - keep local only"
    echo "   - SANITIZED: Safe to share or commit to private repo"
    echo ""
    echo "  🧹 Clearing CHAT_LOG.md for next conversation..."
    > "$CHAT_LOG_SOURCE"
    echo "  ✓ CHAT_LOG.md cleared (ready for next export)"

    return 0
}

# ============================================================================
# MODE: ANALYZE - Generate commit analysis logs
# ============================================================================

mode_analyze() {
    echo "📊 Generating commit logs for: $SHORT_SHA"
    echo "📁 Archive: $ARCHIVE_DIR"

    # Ensure archive directory exists
    if [ ! -d "$ARCHIVE_DIR" ]; then
        echo "❌ Archive directory not found: $ARCHIVE_DIR"
        echo "💡 Run 'gitignored' mode first to create archive structure"
        return 1
    fi

    # ========================================================================
    # 1. ERRORS_LOG.md
    # ========================================================================

    echo "  📝 Creating ERRORS_LOG.md..."

    cat > "$ARCHIVE_DIR/ERRORS_LOG.md" << HEADER
# Errors Log

**Commit SHA:** $CURRENT_SHA
**Commit Date:** $COMMIT_DATE
**Commit Message:** $COMMIT_MSG

---

## Errors Encountered This Commit

HEADER

    # Extract errors from COMMAND_LOG.md if it exists
    if [ -f "$ARCHIVE_DIR/COMMAND_LOG.md" ]; then
        echo "" >> "$ARCHIVE_DIR/ERRORS_LOG.md"
        echo "### From COMMAND_LOG.md:" >> "$ARCHIVE_DIR/ERRORS_LOG.md"
        echo "" >> "$ARCHIVE_DIR/ERRORS_LOG.md"

        # Look for error patterns
        grep -i -E "(error|failed|exception|traceback|warning)" "$ARCHIVE_DIR/COMMAND_LOG.md" >> "$ARCHIVE_DIR/ERRORS_LOG.md" 2>/dev/null || echo "No errors found in COMMAND_LOG.md" >> "$ARCHIVE_DIR/ERRORS_LOG.md"
    fi

    # Extract errors from log files
    if [ -d "$ARCHIVE_DIR/logs" ]; then
        echo "" >> "$ARCHIVE_DIR/ERRORS_LOG.md"
        echo "### From Log Files:" >> "$ARCHIVE_DIR/ERRORS_LOG.md"
        echo "" >> "$ARCHIVE_DIR/ERRORS_LOG.md"

        for logfile in "$ARCHIVE_DIR/logs"/*.log; do
            if [ -f "$logfile" ]; then
                filename=$(basename "$logfile")
                errors=$(grep -i -E "(error|failed|exception|traceback)" "$logfile" 2>/dev/null || echo "")
                if [ -n "$errors" ]; then
                    echo "#### $filename:" >> "$ARCHIVE_DIR/ERRORS_LOG.md"
                    echo '```' >> "$ARCHIVE_DIR/ERRORS_LOG.md"
                    echo "$errors" >> "$ARCHIVE_DIR/ERRORS_LOG.md"
                    echo '```' >> "$ARCHIVE_DIR/ERRORS_LOG.md"
                    echo "" >> "$ARCHIVE_DIR/ERRORS_LOG.md"
                fi
            fi
        done
    fi

    echo "  ✓ ERRORS_LOG.md created"

    # ========================================================================
    # 2. CHANGES_SUMMARY.md
    # ========================================================================

    echo "  📝 Creating CHANGES_SUMMARY.md..."

    cat > "$ARCHIVE_DIR/CHANGES_SUMMARY.md" << HEADER
# Changes Summary

**Commit SHA:** $CURRENT_SHA
**Commit Date:** $COMMIT_DATE
**Commit Message:** $COMMIT_MSG

---

## File Changes Overview

HEADER

    # Get stats from git diff
    if git rev-parse HEAD~1 >/dev/null 2>&1; then
        # Has parent commit - show diff from parent
        echo "### Statistics:" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        echo '```' >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        git diff --stat HEAD~1 HEAD >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        echo '```' >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        echo "" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"

        # List all changed files with change type
        echo "### Changed Files:" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        echo "" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"

        git diff --name-status HEAD~1 HEAD | while read status file; do
            case $status in
                A) echo "- **Added:** \`$file\`" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md" ;;
                M) echo "- **Modified:** \`$file\`" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md" ;;
                D) echo "- **Deleted:** \`$file\`" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md" ;;
                R*) echo "- **Renamed:** \`$file\`" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md" ;;
                *) echo "- **$status:** \`$file\`" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md" ;;
            esac
        done

        echo "" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"

        # Detailed file-by-file breakdown
        echo "### Detailed Changes:" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        echo "" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"

        git diff --name-only HEAD~1 HEAD | while read file; do
            echo "#### \`$file\`" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
            echo "" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
            echo '```diff' >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
            git diff HEAD~1 HEAD -- "$file" | head -100 >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
            echo '```' >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
            echo "" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        done
    else
        # First commit - no parent
        echo "### First Commit - All Files Added:" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        echo "" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        git ls-files | while read file; do
            echo "- \`$file\`" >> "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
        done
    fi

    echo "  ✓ CHANGES_SUMMARY.md created"

    # ========================================================================
    # 3. COMMAND_HISTORY.md
    # ========================================================================

    echo "  📝 Creating COMMAND_HISTORY.md..."

    cat > "$ARCHIVE_DIR/COMMAND_HISTORY.md" << HEADER
# Command History

**Commit SHA:** $CURRENT_SHA
**Commit Date:** $COMMIT_DATE
**Commit Message:** $COMMIT_MSG

---

## Commands Executed This Commit

HEADER

    # Extract commands from COMMAND_LOG if exists
    if [ -f "$ARCHIVE_DIR/COMMAND_LOG.md" ]; then
        echo "" >> "$ARCHIVE_DIR/COMMAND_HISTORY.md"
        echo "### From COMMAND_LOG.md:" >> "$ARCHIVE_DIR/COMMAND_HISTORY.md"
        echo "" >> "$ARCHIVE_DIR/COMMAND_HISTORY.md"

        # Look for command patterns (lines starting with $ or commands in code blocks)
        grep -E "^[\$#>]|^\`\`\`bash" "$ARCHIVE_DIR/COMMAND_LOG.md" >> "$ARCHIVE_DIR/COMMAND_HISTORY.md" 2>/dev/null || echo "No commands found" >> "$ARCHIVE_DIR/COMMAND_HISTORY.md"
    else
        echo "No COMMAND_LOG.md found" >> "$ARCHIVE_DIR/COMMAND_HISTORY.md"
    fi

    echo "  ✓ COMMAND_HISTORY.md created"

    # Update git-info.txt to include new logs
    if [ -f "$ARCHIVE_DIR/git-info.txt" ]; then
        echo "" >> "$ARCHIVE_DIR/git-info.txt"
        echo "=================================================================" >> "$ARCHIVE_DIR/git-info.txt"
        echo "AUTO-GENERATED LOGS" >> "$ARCHIVE_DIR/git-info.txt"
        echo "=================================================================" >> "$ARCHIVE_DIR/git-info.txt"
        echo "" >> "$ARCHIVE_DIR/git-info.txt"
        echo "✅ ERRORS_LOG.md (errors and failures from this commit)" >> "$ARCHIVE_DIR/git-info.txt"
        echo "✅ CHANGES_SUMMARY.md (detailed file changes analysis)" >> "$ARCHIVE_DIR/git-info.txt"
        echo "✅ COMMAND_HISTORY.md (all commands executed)" >> "$ARCHIVE_DIR/git-info.txt"
    fi

    echo ""
    echo "✅ Commit logs generated successfully!"
    echo ""
    echo "📂 Files created:"
    echo "   - $ARCHIVE_DIR/ERRORS_LOG.md"
    echo "   - $ARCHIVE_DIR/CHANGES_SUMMARY.md"
    echo "   - $ARCHIVE_DIR/COMMAND_HISTORY.md"

    return 0
}

# ============================================================================
# MODE: STATUS - Show archive status for current commit
# ============================================================================

mode_status() {
    echo "▶ ARCHIVE STATUS CHECK"
    echo ""
    echo "Commit: $SHORT_SHA"
    echo "Archive directory: $ARCHIVE_DIR"
    echo ""

    if [ ! -d "$ARCHIVE_DIR" ]; then
        echo "❌ No archive exists for this commit"
        echo ""
        echo "Run: bash scripts/maintenance/archive_manager.sh full"
        return 1
    fi

    echo "✅ Archive exists"
    echo ""

    # Count files
    local total_files=$(find "$ARCHIVE_DIR" -type f | wc -l | tr -d ' ')
    local total_size=$(du -sh "$ARCHIVE_DIR" | cut -f1)

    echo "📊 Archive contents:"
    echo "   Total files: $total_files"
    echo "   Total size: $total_size"
    echo ""

    # Check for specific files
    echo "📁 Key files:"
    [ -f "$ARCHIVE_DIR/git-info.txt" ] && echo "   ✅ git-info.txt" || echo "   ❌ git-info.txt (missing)"
    [ -f "$ARCHIVE_DIR/CHAT_LOG_ORIGINAL.md" ] && echo "   ✅ CHAT_LOG_ORIGINAL.md" || echo "   ⚠️  CHAT_LOG_ORIGINAL.md (not archived)"
    [ -f "$ARCHIVE_DIR/CHAT_LOG_SANITIZED.md" ] && echo "   ✅ CHAT_LOG_SANITIZED.md" || echo "   ⚠️  CHAT_LOG_SANITIZED.md (not archived)"
    [ -f "$ARCHIVE_DIR/ERRORS_LOG.md" ] && echo "   ✅ ERRORS_LOG.md" || echo "   ⚠️  ERRORS_LOG.md (not generated)"
    [ -f "$ARCHIVE_DIR/CHANGES_SUMMARY.md" ] && echo "   ✅ CHANGES_SUMMARY.md" || echo "   ⚠️  CHANGES_SUMMARY.md (not generated)"
    [ -f "$ARCHIVE_DIR/COMMAND_HISTORY.md" ] && echo "   ✅ COMMAND_HISTORY.md" || echo "   ⚠️  COMMAND_HISTORY.md (not generated)"

    return 0
}

# ============================================================================
# MODE: FULL - Run all archiving modes in sequence
# ============================================================================

mode_full() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 FULL ARCHIVE MODE - Running all archiving operations"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    local errors=0

    # Step 1: Archive gitignored files
    echo "━━━ STEP 1/3: Archive Gitignored Files ━━━"
    mode_gitignored || ((errors++))
    echo ""

    # Step 2: Archive conversation
    echo "━━━ STEP 2/3: Archive Conversation ━━━"
    mode_conversation || echo "⚠️  Skipping conversation (no CHAT_LOG.md found)"
    echo ""

    # Step 3: Generate analysis logs
    echo "━━━ STEP 3/3: Generate Analysis Logs ━━━"
    mode_analyze || ((errors++))
    echo ""

    # Commit everything to archive git repo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    commit_to_archive_git "Archive commit $SHORT_SHA from main repo: $COMMIT_MSG"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if [ $errors -eq 0 ]; then
        echo "✅ FULL ARCHIVE COMPLETE!"
    else
        echo "⚠️  ARCHIVE COMPLETE WITH $errors WARNINGS"
    fi

    echo ""
    echo "📂 Location: $ARCHIVE_DIR"
    echo "📝 To view: ls -la $ARCHIVE_DIR"
    echo "📋 To see all archives: cat $ARCHIVE_BASE/README.md"

    return 0
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Get git info first
get_git_info

# Create archive directory
create_archive_dir

# Execute selected mode
case "$MODE" in
    gitignored)
        mode_gitignored
        commit_to_archive_git "Archive gitignored files for $SHORT_SHA"
        ;;
    conversation)
        mode_conversation
        commit_to_archive_git "Add chat logs to archive $SHORT_SHA"
        ;;
    analyze)
        mode_analyze
        commit_to_archive_git "Add auto-generated logs for $SHORT_SHA"
        ;;
    status)
        mode_status
        ;;
    full)
        mode_full
        ;;
    *)
        echo "❌ Unknown mode: $MODE"
        echo ""
        echo "Usage: $0 [gitignored|conversation|analyze|full|status]"
        echo ""
        echo "Modes:"
        echo "  gitignored    - Archive .gitignored operational files"
        echo "  conversation  - Archive CHAT_LOG.md with sanitization"
        echo "  analyze       - Generate commit analysis logs"
        echo "  full          - Run all three modes in sequence (default)"
        echo "  status        - Show archive status for current commit"
        exit 1
        ;;
esac
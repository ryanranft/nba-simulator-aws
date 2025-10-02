#!/bin/bash
# Generate comprehensive commit logs: errors, changes summary, command history

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_NAME=$(basename "$PROJECT_DIR")
SPORT=$(echo "$PROJECT_NAME" | sed -E 's/^([a-z]+)-simulator.*/\1/')
ARCHIVE_BASE="${ARCHIVE_BASE:-$HOME/sports-simulator-archives/$SPORT}"

# Get current git info
cd "$PROJECT_DIR"
CURRENT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)
COMMIT_MSG=$(git log -1 --format=%s)
COMMIT_DATE=$(git log -1 --format=%ci)

ARCHIVE_DIR="$ARCHIVE_BASE/$CURRENT_SHA"

# Ensure archive directory exists
if [ ! -d "$ARCHIVE_DIR" ]; then
    echo "❌ Archive directory not found: $ARCHIVE_DIR"
    exit 1
fi

echo "📊 Generating commit logs for: $SHORT_SHA"
echo "📁 Archive: $ARCHIVE_DIR"

# ============================================================================
# 1. ERRORS_LOG.md - Extract all errors from COMMAND_LOG.md and session logs
# ============================================================================

echo "  📝 Creating ERRORS_LOG.md..."

cat > "$ARCHIVE_DIR/ERRORS_LOG.md" << 'HEADER'
# Errors Log

**Commit SHA:** COMMIT_SHA_PLACEHOLDER
**Commit Date:** COMMIT_DATE_PLACEHOLDER
**Commit Message:** COMMIT_MSG_PLACEHOLDER

---

## Errors Encountered This Commit

HEADER

# Replace placeholders
sed -i '' "s|COMMIT_SHA_PLACEHOLDER|$CURRENT_SHA|g" "$ARCHIVE_DIR/ERRORS_LOG.md"
sed -i '' "s|COMMIT_DATE_PLACEHOLDER|$COMMIT_DATE|g" "$ARCHIVE_DIR/ERRORS_LOG.md"
sed -i '' "s|COMMIT_MSG_PLACEHOLDER|$COMMIT_MSG|g" "$ARCHIVE_DIR/ERRORS_LOG.md"

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

# ============================================================================
# 2. CHANGES_SUMMARY.md - Detailed analysis of all file changes
# ============================================================================

echo "  📝 Creating CHANGES_SUMMARY.md..."

cat > "$ARCHIVE_DIR/CHANGES_SUMMARY.md" << 'HEADER'
# Changes Summary

**Commit SHA:** COMMIT_SHA_PLACEHOLDER
**Commit Date:** COMMIT_DATE_PLACEHOLDER
**Commit Message:** COMMIT_MSG_PLACEHOLDER

---

## File Changes Overview

HEADER

# Replace placeholders
sed -i '' "s|COMMIT_SHA_PLACEHOLDER|$CURRENT_SHA|g" "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
sed -i '' "s|COMMIT_DATE_PLACEHOLDER|$COMMIT_DATE|g" "$ARCHIVE_DIR/CHANGES_SUMMARY.md"
sed -i '' "s|COMMIT_MSG_PLACEHOLDER|$COMMIT_MSG|g" "$ARCHIVE_DIR/CHANGES_SUMMARY.md"

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

# ============================================================================
# 3. COMMAND_HISTORY.md - All commands from COMMAND_LOG with outcomes
# ============================================================================

echo "  📝 Creating COMMAND_HISTORY.md..."

cat > "$ARCHIVE_DIR/COMMAND_HISTORY.md" << 'HEADER'
# Command History

**Commit SHA:** COMMIT_SHA_PLACEHOLDER
**Commit Date:** COMMIT_DATE_PLACEHOLDER
**Commit Message:** COMMIT_MSG_PLACEHOLDER

---

## Commands Executed This Commit

HEADER

# Replace placeholders
sed -i '' "s|COMMIT_SHA_PLACEHOLDER|$CURRENT_SHA|g" "$ARCHIVE_DIR/COMMAND_HISTORY.md"
sed -i '' "s|COMMIT_DATE_PLACEHOLDER|$COMMIT_DATE|g" "$ARCHIVE_DIR/COMMAND_HISTORY.md"
sed -i '' "s|COMMIT_MSG_PLACEHOLDER|$COMMIT_MSG|g" "$ARCHIVE_DIR/COMMAND_HISTORY.md"

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

# ============================================================================
# Update git-info.txt to include new logs
# ============================================================================

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
echo ""

# Commit to archive git repo
if [ -d "$ARCHIVE_BASE/.git" ]; then
    cd "$ARCHIVE_BASE"
    git add . > /dev/null 2>&1
    if git commit -m "Add auto-generated logs for $SHORT_SHA" --quiet 2>/dev/null; then
        echo "  ✓ Logs committed to archive git repo"
    fi
    cd "$PROJECT_DIR"
fi
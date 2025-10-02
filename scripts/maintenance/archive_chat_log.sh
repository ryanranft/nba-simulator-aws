#!/bin/bash
# Archive chat conversation log to SHA-based archive with sanitization

set -e

# Configuration - Auto-detect sport from directory name
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Extract sport name from project directory (e.g., nba-simulator-aws -> nba)
SPORT=$(echo "$PROJECT_NAME" | sed -E 's/^([a-z]+)-simulator.*/\1/')

# Archive base with sport-specific subfolder (configurable via environment variable)
ARCHIVE_BASE="${ARCHIVE_BASE:-$HOME/sports-simulator-archives/$SPORT}"

# Get current git info
cd "$PROJECT_DIR"
CURRENT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)

# Archive directory for this commit
ARCHIVE_DIR="$ARCHIVE_BASE/$CURRENT_SHA"

# Ensure archive directory exists
if [ ! -d "$ARCHIVE_DIR" ]; then
    echo "❌ Archive directory not found: $ARCHIVE_DIR"
    echo "💡 Run archive_gitignored_files.sh first to create the archive structure"
    exit 1
fi

echo "📝 Archiving chat conversation log for commit: $SHORT_SHA"
echo "📁 Archive location: $ARCHIVE_DIR"

# Check if Claude Code provides a chat log file
# This would need to be manually created by the user or exported from Claude Code
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
    echo "Or manually create CHAT_LOG.md with conversation history"
    exit 1
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
# Re-sanitize the ENTIRE original log file (including all appended sessions)
echo "  🔒 Sanitizing complete archive..."
python3 - "$ORIGINAL_LOG" "$SANITIZED_LOG" << 'PYTHON_EOF'
import re
import sys

# Get filenames from command line arguments
original_file = sys.argv[1]
sanitized_file = sys.argv[2]

# Read the complete ORIGINAL log (which may have multiple sessions appended)
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

# Update git-info.txt to include chat logs
if [ -f "$ARCHIVE_DIR/git-info.txt" ]; then
    echo "✅ CHAT_LOG_ORIGINAL.md (contains credentials - local only)" >> "$ARCHIVE_DIR/git-info.txt"
    echo "✅ CHAT_LOG_SANITIZED.md (safe for sharing)" >> "$ARCHIVE_DIR/git-info.txt"
fi

echo "  ✓ Original saved: CHAT_LOG_ORIGINAL.md (with credentials)"
echo "  ✓ Sanitized saved: CHAT_LOG_SANITIZED.md (safe for sharing)"
echo ""
echo "✅ Chat log archived successfully!"
echo ""
echo "📂 Files created:"
echo "   - $ORIGINAL_LOG"
echo "   - $SANITIZED_LOG"
echo ""
echo "⚠️  Security Note:"
echo "   - ORIGINAL: Contains passwords - keep local only"
echo "   - SANITIZED: Safe to share or commit to private repo"
echo ""
echo "  🧹 Clearing CHAT_LOG.md for next conversation..."
> "$CHAT_LOG_SOURCE"
echo "  ✓ CHAT_LOG.md cleared (ready for next export)"
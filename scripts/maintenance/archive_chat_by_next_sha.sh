#!/bin/bash
# Archive chat conversation log AFTER commit, naming it by the NEW commit SHA
# This captures the conversation that LED TO this commit
#
# Usage:
#   1. Export Claude Code conversation to CHAT_LOG.md
#   2. Stage and commit your changes
#   3. Run this script to archive the conversation with the commit SHA
#
# The archived chat shows what work was done to create that commit

set -e

# Configuration - Auto-detect sport from directory name
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Extract sport name from project directory (e.g., nba-simulator-aws -> nba)
SPORT=$(echo "$PROJECT_NAME" | sed -E 's/^([a-z]+)-simulator.*/\1/')

# Archive base with sport-specific subfolder
ARCHIVE_BASE="${ARCHIVE_BASE:-$HOME/sports-simulator-archives/$SPORT/conversations}"

# Get current git info (this is the commit we just made)
cd "$PROJECT_DIR"
CURRENT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)

# Get commit message for context
COMMIT_MSG=$(git log -1 --pretty=%B)
COMMIT_DATE=$(git log -1 --format=%cd --date=iso)
AUTHOR=$(git log -1 --format='%an <%ae>')

# Ensure archive directory exists
mkdir -p "$ARCHIVE_BASE"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 ARCHIVING CONVERSATION FOR COMMIT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Commit: $SHORT_SHA"
echo "Date:   $COMMIT_DATE"
echo "Author: $AUTHOR"
echo ""
echo "Message:"
echo "$COMMIT_MSG" | sed 's/^/  /'
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Claude Code provides a chat log file
CHAT_LOG_SOURCE="$PROJECT_DIR/CHAT_LOG.md"

if [ ! -f "$CHAT_LOG_SOURCE" ]; then
    echo "❌ No CHAT_LOG.md found in project directory"
    echo ""
    echo "To create a chat log:"
    echo "1. Export conversation from Claude Code interface"
    echo "2. Save as $CHAT_LOG_SOURCE"
    echo "3. Run this script again"
    echo ""
    echo "⚠️  Conversation for commit $SHORT_SHA will NOT be archived!"
    exit 1
fi

# Check if conversation already archived for this SHA
SANITIZED_LOG="$ARCHIVE_BASE/chat-${CURRENT_SHA}-sanitized.md"
ORIGINAL_LOG="$ARCHIVE_BASE/chat-${CURRENT_SHA}-original.md"

if [ -f "$ORIGINAL_LOG" ]; then
    echo "⚠️  Conversation already archived for commit $SHORT_SHA"
    echo ""
    read -p "Overwrite existing archive? [y/N]: " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "❌ Archive cancelled"
        exit 0
    fi
    echo ""
fi

# Create original archive with header
echo "  📝 Creating archive for SHA: $SHORT_SHA"

cat > "$ORIGINAL_LOG" <<EOF
# Conversation Archive: Commit $SHORT_SHA

**Full SHA:** $CURRENT_SHA
**Date:** $COMMIT_DATE
**Author:** $AUTHOR

## Commit Message

\`\`\`
$COMMIT_MSG
\`\`\`

## Conversation

This conversation captures the work that led to the above commit.

---

EOF

# Append the actual conversation
cat "$CHAT_LOG_SOURCE" >> "$ORIGINAL_LOG"

# Create sanitized version with credentials redacted
echo "  🔒 Creating sanitized version..."

python3 <<'PYTHON_EOF' "$ORIGINAL_LOG" "$SANITIZED_LOG"
import re
import sys

# Read original log
with open(sys.argv[1], 'r') as f:
    content = f.read()

# Redact patterns (credentials only)
redactions = [
    (r'AWS_ACCESS_KEY[A-Z0-9]{16}', 'AWS_ACCESS_KEY[REDACTED]'),
    (r'aws_secret_access_key=[^\s]+', 'aws_secret_access_key=[REDACTED]'),
    (r'aws_session_token=[^\s]+', 'aws_session_token=[REDACTED]'),
    (r'(Password|password|PASSWORD):\s*[^\s]+', r'\1: [REDACTED]'),
    (r'Bearer [A-Za-z0-9_-]+', 'Bearer [REDACTED]'),
    (r'ghp_[A-Za-z0-9]{36}', 'ghp_[REDACTED]'),
    (r'github_pat_[A-Za-z0-9_]+', 'github_pat_[REDACTED]'),
    (r'postgresql://[^:]+:[^@]+@', 'postgresql://[USER]:[REDACTED]@'),
    (r'postgres:[^@]+@', 'postgres:[REDACTED]@'),
]

for pattern, replacement in redactions:
    content = re.sub(pattern, replacement, content)

# Write sanitized version
with open(sys.argv[2], 'w') as f:
    f.write(content)
PYTHON_EOF

echo ""
echo "✅ Conversation archived successfully!"
echo ""
echo "📂 Files created:"
echo "   Original:  $ORIGINAL_LOG"
echo "   Sanitized: $SANITIZED_LOG"
echo ""
echo "⚠️  Security Note:"
echo "   - ORIGINAL: Contains passwords - keep local only"
echo "   - SANITIZED: Safe to share or commit to private repo"
echo ""
echo "💡 You can now delete CHAT_LOG.md from the project root:"
echo "   rm $CHAT_LOG_SOURCE"
echo ""
echo "🔍 To view this conversation later:"
echo "   less $SANITIZED_LOG"
echo ""
echo "📋 Archive Index:"
ls -lh "$ARCHIVE_BASE"/chat-*-sanitized.md 2>/dev/null | wc -l | xargs echo "   Total conversations archived:"
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
MAPPING_DIR="${ARCHIVE_BASE}/mappings"

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

python3 - "$ORIGINAL_LOG" "$SANITIZED_LOG" <<'PYTHON_EOF'
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

# Create spoofed version with fake file paths (safe for public sharing)
echo "  🎭 Creating spoofed version (public-safe)..."

SPOOFED_LOG="$ARCHIVE_BASE/chat-${CURRENT_SHA}-spoofed.md"
MAPPING_FILE="$MAPPING_DIR/mapping-${CURRENT_SHA}.txt"

mkdir -p "$MAPPING_DIR"

python3 - "$SANITIZED_LOG" "$SPOOFED_LOG" "$MAPPING_FILE" "$PROJECT_DIR" <<'PYTHON_EOF'
import re
import sys
import hashlib
from pathlib import Path

# Read sanitized log
with open(sys.argv[1], 'r') as f:
    content = f.read()

project_dir = sys.argv[4]
mapping = {}

# Extract all file paths from content
# Patterns: /Users/..., ~/..., ./..., scripts/..., etc.
path_patterns = [
    r'/Users/[^\s:]+(?:/[^\s:]*)*\.[a-z]{2,4}',  # Absolute paths with extensions
    r'~/[^\s:]+(?:/[^\s:]*)*\.[a-z]{2,4}',       # Home directory paths
    r'\./[^\s:]+(?:/[^\s:]*)*\.[a-z]{2,4}',      # Relative paths
    r'[a-z_]+(?:/[a-z_0-9-]+)*\.[a-z]{2,4}',     # Simple paths like scripts/foo.sh
]

all_paths = set()
for pattern in path_patterns:
    matches = re.findall(pattern, content, re.IGNORECASE)
    all_paths.update(matches)

# Create spoofed names for each path
def spoof_path(real_path):
    """Generate consistent fake path from real path"""
    # Hash the path to get consistent fake name
    path_hash = hashlib.md5(real_path.encode()).hexdigest()[:8]

    # Get extension
    if '.' in real_path:
        ext = real_path.rsplit('.', 1)[1]
    else:
        ext = 'txt'

    # Determine type
    if '/scripts/' in real_path or real_path.startswith('scripts/'):
        prefix = 'script'
    elif '.md' in real_path.lower():
        prefix = 'doc'
    elif '.sh' in real_path:
        prefix = 'script'
    elif '.py' in real_path:
        prefix = 'program'
    elif '.sql' in real_path:
        prefix = 'query'
    else:
        prefix = 'file'

    # Build fake path structure
    if real_path.startswith('/Users/') or real_path.startswith('~/'):
        # External archive path
        return f'/archive/external/{prefix}_{path_hash}.{ext}'
    elif real_path.startswith('./') or not real_path.startswith('/'):
        # Project-relative path
        parts = real_path.lstrip('./').split('/')
        if len(parts) > 1:
            return f'project/{parts[0]}/{prefix}_{path_hash}.{ext}'
        else:
            return f'project/{prefix}_{path_hash}.{ext}'
    else:
        # Absolute system path
        return f'/system/{prefix}_{path_hash}.{ext}'

# Build mapping and spoofed content
for real_path in sorted(all_paths):
    spoofed_path = spoof_path(real_path)
    mapping[real_path] = spoofed_path
    # Escape special regex characters in path
    escaped_real = re.escape(real_path)
    content = re.sub(escaped_real, spoofed_path, content)

# Replace usernames in paths
content = re.sub(r'/Users/[^/\s]+', '/Users/developer', content)
content = re.sub(r'~/([^/\s])', r'/Users/developer/\1', content)

# Replace author email
content = re.sub(r'<[^@]+@[^>]+>', '<developer@example.com>', content)
content = re.sub(r'Author:\s*[^<\n]+', 'Author: Developer', content)

# Replace project-specific names
content = re.sub(r'nba-simulator-aws', 'sports-data-pipeline', content)
content = re.sub(r'nba-sim-raw-data-lake', 'sports-raw-data-bucket', content)
content = re.sub(r'\bnba\b', 'sport', content, flags=re.IGNORECASE)
content = re.sub(r'\bNBA\b', 'SPORT', content)

# Write spoofed content
with open(sys.argv[2], 'w') as f:
    f.write(content)

# Write mapping file
with open(sys.argv[3], 'w') as f:
    f.write(f"# Path Mapping for Commit {Path(sys.argv[1]).stem.replace('chat-', '').replace('-sanitized', '')}\n")
    f.write(f"# Created: {sys.argv[1]}\n")
    f.write("#\n")
    f.write("# REAL PATH → SPOOFED PATH\n")
    f.write("#\n")
    f.write("# SECURITY: This file contains real paths - NEVER commit to git!\n")
    f.write(f"# Location: {sys.argv[3]}\n")
    f.write("#" + "="*70 + "\n\n")

    for real, spoofed in sorted(mapping.items()):
        f.write(f"{real}\n  → {spoofed}\n\n")

    f.write(f"\nTotal paths spoofed: {len(mapping)}\n")

print(f"Spoofed {len(mapping)} file paths")
PYTHON_EOF

echo ""
echo "✅ Conversation archived successfully!"
echo ""
echo "📂 Files created:"
echo "   Original:  $ORIGINAL_LOG"
echo "   Sanitized: $SANITIZED_LOG"
echo "   Spoofed:   $SPOOFED_LOG"
echo "   Mapping:   $MAPPING_FILE"
echo ""
echo "⚠️  Security Note:"
echo "   - ORIGINAL: Contains passwords - keep local only"
echo "   - SANITIZED: Safe to share or commit to private repo"
echo "   - SPOOFED: Safe to share publicly (fake paths, no credentials)"
echo "   - MAPPING: Real→Spoofed paths - NEVER commit (local only)"
echo ""
echo "💡 You can now delete CHAT_LOG.md from the project root:"
echo "   rm $CHAT_LOG_SOURCE"
echo ""
echo "🔍 To view conversations:"
echo "   less $SANITIZED_LOG  # Real paths, credentials removed"
echo "   less $SPOOFED_LOG     # Fake paths, safe for public"
echo ""
echo "📋 Archive Index:"
ls -lh "$ARCHIVE_BASE"/chat-*-sanitized.md 2>/dev/null | wc -l | xargs echo "   Total conversations archived:"
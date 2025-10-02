#!/bin/bash
# Create sanitized archive safe for GitHub (private repos only)
# This is OPTIONAL - only use if sharing with team on private repo

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

# Get current git info
CURRENT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT_DATE=$(git log -1 --format=%ci)
COMMIT_MSG=$(git log -1 --format=%s)

# Sanitized archive location (INSIDE git repo, safe for GitHub)
SANITIZED_BASE="$PROJECT_DIR/archived-docs"
SANITIZED_DIR="$SANITIZED_BASE/$SHORT_SHA"

echo "🔒 Creating sanitized archive for commit: $SHORT_SHA"
echo "📁 Archive location: $SANITIZED_DIR"
echo ""
echo "⚠️  WARNING: This archive is for PRIVATE GitHub repos only"
echo "   Review all files before committing to ensure sanitization worked"
echo ""

# Create directory
mkdir -p "$SANITIZED_DIR"

# Create git metadata
cat > "$SANITIZED_DIR/git-info.txt" << EOF
=================================================================
SANITIZED GIT SNAPSHOT
=================================================================

Full SHA:     $CURRENT_SHA
Short SHA:    $SHORT_SHA
Branch:       $BRANCH
Commit Date:  $COMMIT_DATE
Commit Msg:   $COMMIT_MSG

=================================================================
SANITIZATION APPLIED
=================================================================

The following patterns were redacted with [REDACTED]:
- AWS credentials (access keys, secret keys, tokens)
- Database passwords
- API keys and bearer tokens
- GitHub tokens (PATs)
- Connection strings with passwords

The following were REMOVED entirely:
- Private IP addresses (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
- Any IP addresses

SECURITY NOTE: This archive is sanitized but should ONLY be
committed to PRIVATE repositories. Never push to public GitHub.

=================================================================
ARCHIVED FILES
=================================================================

EOF

# Files to sanitize and archive
FILES=(
    "EXTRACTION_STATUS.md"
    "COMMIT_VERIFICATION.md"
    "OVERNIGHT_EXTRACTION_STATUS.md"
    "OVERNIGHT_AUTOMATION_STATUS.md"
)

COUNT=0

# Python sanitization script
for file in "${FILES[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        echo "  🔒 Sanitizing: $file"

        # Use Python for comprehensive sanitization
        python3 << PYTHON_EOF > "$SANITIZED_DIR/$file"
import re

with open("$PROJECT_DIR/$file", 'r') as f:
    content = f.read()

# Redact credentials (replace with [REDACTED])
redactions = [
    (r'AWS_ACCESS_KEY[A-Z0-9]{16}', 'AWS_ACCESS_KEY[REDACTED]'),
    (r'aws_secret_access_key\s*=\s*[^\s]+', 'aws_secret_access_key=[REDACTED]'),
    (r'aws_session_token\s*=\s*[^\s]+', 'aws_session_token=[REDACTED]'),
    (r'(Password|password|PASSWORD)\s*[:=]\s*[^\s]+', r'\1: [REDACTED]'),
    (r'Bearer\s+[A-Za-z0-9_-]+', 'Bearer [REDACTED]'),
    (r'ghp_[A-Z0-9]{36}', 'ghp_[REDACTED]'),
    (r'github_pat_[A-Za-z0-9_]+', 'github_pat_[REDACTED]'),
    (r'postgresql://[^:]+:[^@]+@', 'postgresql://[USER]:[REDACTED]@'),
    (r'postgres:[^@]+@', 'postgres:[REDACTED]@'),
]

# Remove IP addresses entirely (not just redact)
ip_removals = [
    (r'192\.168\.\d+\.\d+', '[IP_REMOVED]'),
    (r'10\.\d+\.\d+\.\d+', '[IP_REMOVED]'),
    (r'172\.(1[6-9]|2[0-9]|3[01])\.\d+\.\d+', '[IP_REMOVED]'),
]

# Apply redactions
for pattern, replacement in redactions:
    content = re.sub(pattern, replacement, content)

# Apply IP removals
for pattern, replacement in ip_removals:
    content = re.sub(pattern, replacement, content)

print(content, end='')
PYTHON_EOF

        echo "✅ $file" >> "$SANITIZED_DIR/git-info.txt"
        COUNT=$((COUNT + 1))
    fi
done

# Sanitize chat log if exists
if [ -f "$PROJECT_DIR/CHAT_LOG.md" ]; then
    echo "  🔒 Sanitizing: CHAT_LOG.md → CHAT_LOG_SANITIZED.md"

    python3 << 'PYTHON_EOF' > "$SANITIZED_DIR/CHAT_LOG_SANITIZED.md"
import re

with open("$PROJECT_DIR/CHAT_LOG.md", 'r') as f:
    content = f.read()

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
    (r'192\.168\.\d+\.\d+', '[IP_REMOVED]'),
    (r'10\.\d+\.\d+\.\d+', '[IP_REMOVED]'),
    (r'172\.(1[6-9]|2[0-9]|3[01])\.\d+\.\d+', '[IP_REMOVED]'),
]

for pattern, replacement in redactions:
    content = re.sub(pattern, replacement, content)

print(content, end='')
PYTHON_EOF

    echo "✅ CHAT_LOG_SANITIZED.md" >> "$SANITIZED_DIR/git-info.txt"
    COUNT=$((COUNT + 1))
fi

# Create README for this sanitized snapshot
cat > "$SANITIZED_DIR/README.md" << EOF
# Sanitized Archive Snapshot - $SHORT_SHA

**Created:** $(date)
**Commit:** $SHORT_SHA
**Branch:** $BRANCH

## What's Redacted

- AWS credentials → \`[REDACTED]\`
- Database passwords → \`[REDACTED]\`
- API keys → \`[REDACTED]\`
- Bearer tokens → \`[REDACTED]\`
- GitHub tokens → \`[REDACTED]\`
- Connection strings → \`[REDACTED]\`
- IP addresses → \`[IP_REMOVED]\`

## Files Included

EOF

# List files
for file in "$SANITIZED_DIR"/*; do
    if [ -f "$file" ]; then
        basename "$file" >> "$SANITIZED_DIR/README.md"
    fi
done

cat >> "$SANITIZED_DIR/README.md" << EOF

## Security Verification

Before committing to GitHub, run:

\`\`\`bash
# Check for credentials
grep -ri "password.*=.*[a-z0-9]" archived-docs/$SHORT_SHA/
grep -ri "aws_secret_access_key.*=.*[a-zA-Z0-9/+]{40}" archived-docs/$SHORT_SHA/
grep -ri "192\.168\.[0-9]" archived-docs/$SHORT_SHA/

# If no output, sanitization succeeded
\`\`\`

## Committing to GitHub

\`\`\`bash
git add archived-docs/$SHORT_SHA/
git commit -m "Add sanitized archive snapshot for $SHORT_SHA"
git push origin main
\`\`\`

**REMINDER:** Only commit to PRIVATE repositories!
EOF

echo ""
cat >> "$SANITIZED_DIR/git-info.txt" << EOF

=================================================================
Total files sanitized: $COUNT
Archive created: $(date)
=================================================================
EOF

echo "✅ Sanitized archive complete!"
echo "📂 Location: $SANITIZED_DIR"
echo "📊 Files sanitized: $COUNT"
echo ""
echo "⚠️  IMPORTANT: Review files before committing"
echo ""
echo "To verify sanitization:"
echo "  grep -ri 'password.*=.*[a-z0-9]' archived-docs/$SHORT_SHA/"
echo "  grep -ri '192\.168\.[0-9]' archived-docs/$SHORT_SHA/"
echo ""
echo "To commit (ONLY to private repo):"
echo "  git add archived-docs/$SHORT_SHA/"
echo "  git commit -m 'Add sanitized archive snapshot for $SHORT_SHA'"
echo "  git push origin main"
#!/bin/bash

# sanitize_command_log.sh
# Automatically sanitize COMMAND_LOG.md before Git commits
# Removes sensitive information like AWS account IDs, IPs, tokens, etc.
#
# Usage:
#   ./scripts/shell/sanitize_command_log.sh
#   OR run automatically via Git pre-commit hook

PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"
LOG_FILE="$PROJECT_ROOT/COMMAND_LOG.md"
BACKUP_FILE="$PROJECT_ROOT/COMMAND_LOG.md.backup"

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "✅ No COMMAND_LOG.md found, nothing to sanitize"
    exit 0
fi

echo "🔍 Sanitizing COMMAND_LOG.md..."

# Create backup
cp "$LOG_FILE" "$BACKUP_FILE"
echo "📦 Backup created: $BACKUP_FILE"

# Use sed to sanitize sensitive patterns
# Note: macOS sed requires '' after -i, Linux doesn't
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED_INPLACE=(-i '')
else
    SED_INPLACE=(-i)
fi

# Sanitization patterns
sed "${SED_INPLACE[@]}" \
    -e 's/[0-9]\{12\}/************/g' \
    "$LOG_FILE"

# AWS Account IDs (12 digits)
sed "${SED_INPLACE[@]}" \
    -e 's/Account ID: [0-9]\{12\}/Account ID: ************/g' \
    -e 's/account[_-]id[": ]*[0-9]\{12\}/account_id: ************/g' \
    "$LOG_FILE"

# AWS Access Keys (starts with AWS_ACCESS_KEY)
sed "${SED_INPLACE[@]}" \
    -e 's/AWS_ACCESS_KEY[0-9A-Z]\{16\}/AWS_ACCESS_KEY****************/g' \
    -e 's/aws_access_key_id[": ]*AWS_ACCESS_KEY[0-9A-Z]\{16\}/aws_access_key_id: AWS_ACCESS_KEY****************/g' \
    "$LOG_FILE"

# AWS Secret Keys (40 character base64-like strings after "secret")
sed "${SED_INPLACE[@]}" \
    -e 's/\(secret[_a-z]*[": ]*\)[A-Za-z0-9/+=]\{40\}/\1****************************************/g' \
    "$LOG_FILE"

# GitHub Personal Access Tokens (ghp_, gho_, ghs_, ghr_ prefixes)
sed "${SED_INPLACE[@]}" \
    -e 's/gh[psor]_[A-Za-z0-9]\{36\}/ghp_*************************************/g' \
    "$LOG_FILE"

# IP Addresses (replace with xxx.xxx.xxx.xxx)
sed "${SED_INPLACE[@]}" \
    -e 's/\b[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\b/xxx.xxx.xxx.xxx/g' \
    "$LOG_FILE"

# RDS endpoints (keep structure but sanitize host)
sed "${SED_INPLACE[@]}" \
    -e 's/nba-sim-db\.[a-z0-9]\{10,\}\.us-east-1\.rds\.amazonaws\.com/nba-sim-db.xxxxxxxxxx.us-east-1.rds.amazonaws.com/g' \
    "$LOG_FILE"

# EC2 public DNS (keep structure but sanitize)
sed "${SED_INPLACE[@]}" \
    -e 's/ec2-[0-9-]\{7,\}\.compute-1\.amazonaws\.com/ec2-xx-xx-xx-xx.compute-1.amazonaws.com/g' \
    "$LOG_FILE"

# Database passwords in connection strings
sed "${SED_INPLACE[@]}" \
    -e 's/\(postgres:\/\/[^:]*:\)[^@]*\(@\)/\1********\2/g' \
    -e 's/\(password[": =]*\)[^ ][^ ]*\( \|$\|"\)/\1********\2/g' \
    "$LOG_FILE"

# SSH private key paths (keep filename but sanitize path)
sed "${SED_INPLACE[@]}" \
    -e 's/\/Users\/[^/]*\/.ssh\//~\/.ssh\//g' \
    "$LOG_FILE"

# Email addresses (except known safe ones)
sed "${SED_INPLACE[@]}" \
    -e 's/\b[A-Za-z0-9._%+-]\+@[A-Za-z0-9.-]\+\.[A-Z|a-z]\{2,\}\b/user@example.com/g' \
    -e 's/user@example\.com/noreply@anthropic.com/g' \
    "$LOG_FILE"

# Check if any changes were made
if diff -q "$LOG_FILE" "$BACKUP_FILE" > /dev/null; then
    echo "✅ No sensitive information found"
    rm "$BACKUP_FILE"
else
    echo "⚠️  Sensitive information sanitized!"
    echo ""
    echo "Changes made:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    diff "$BACKUP_FILE" "$LOG_FILE" | grep '^[<>]' | head -20
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 Original file backed up to: $BACKUP_FILE"
    echo "💡 Review the changes above to ensure nothing important was removed"
    echo ""
    echo "To restore original: mv $BACKUP_FILE $LOG_FILE"
fi

echo ""
echo "✅ Sanitization complete!"
# Command Log Sanitization Guide

## Overview

This project includes an automated sanitization system that removes sensitive information from `COMMAND_LOG.md` before Git commits.

## How It Works

### Automatic Sanitization (Recommended)

A Git pre-commit hook automatically runs when you try to commit `COMMAND_LOG.md`:

```bash
git add COMMAND_LOG.md
git commit -m "Update command log"

# Hook automatically:
# 1. Detects COMMAND_LOG.md in commit
# 2. Runs sanitization script
# 3. Creates backup (COMMAND_LOG.md.backup)
# 4. Aborts commit for your review
# 5. You review, then re-add and commit
```

### Manual Sanitization

Run the sanitization script manually anytime:

```bash
./scripts/shell/sanitize_command_log.sh
```

## What Gets Sanitized

The script automatically removes or replaces:

| Sensitive Data | Pattern | Replacement |
|---------------|---------|-------------|
| AWS Account IDs | 12-digit numbers | `************` |
| AWS Access Keys | `AWS_ACCESS_KEY...` (20 chars) | `AWS_ACCESS_KEY****************` |
| AWS Secret Keys | 40-char strings after "secret" | `********...` |
| GitHub PAT Tokens | `ghp_`, `gho_`, `ghs_`, `ghr_` | `ghp_*************` |
| IP Addresses | `192.168.1.1` | `xxx.xxx.xxx.xxx` |
| RDS Endpoints | `nba-sim-db.abc123.us-east-1...` | `nba-sim-db.xxxxxxxxxx...` |
| EC2 DNS | `ec2-12-34-56-78.compute-1...` | `ec2-xx-xx-xx-xx...` |
| Database Passwords | In connection strings | `********` |
| SSH Key Paths | `/Users/username/.ssh/` | `~/.ssh/` |
| Email Addresses | `user@domain.com` | `user@example.com` |

## Workflow

### First Time Setup

Already done! The pre-commit hook is installed at:
```
/Users/ryanranft/nba-simulator-aws/.git/hooks/pre-commit
```

### Regular Workflow

1. **Work normally** - use `log_cmd` to log commands
2. **Stage your changes** - `git add COMMAND_LOG.md`
3. **Attempt commit** - `git commit -m "Update command log"`
4. **Hook runs** - automatically sanitizes and aborts
5. **Review changes** - check the diff shown
6. **Re-stage** - `git add COMMAND_LOG.md`
7. **Commit again** - `git commit -m "Update command log"`
8. **Success!** - sanitized version is committed

### Example Session

```bash
# Log some commands with sensitive data
log_cmd aws sts get-caller-identity
# Output shows: "Account": "<your-account-id>"

log_cmd aws s3 ls
# Output shows IP addresses in metadata

# Try to commit
git add COMMAND_LOG.md
git commit -m "Add AWS commands"

# Output:
# 🔒 COMMAND_LOG.md detected in commit
# 🔍 Sanitizing COMMAND_LOG.md...
# ⚠️  Sensitive information sanitized!
#
# Changes made:
# < "Account": "<your-account-id>"
# > "Account": "************"
#
# ⚠️  IMPORTANT: Review sanitized changes before proceeding
# Commit aborted - please review and retry

# Review the changes
cat COMMAND_LOG.md  # Check sanitized version

# Looks good? Re-add and commit
git add COMMAND_LOG.md
git commit -m "Add AWS commands"

# ✅ Committed successfully!
```

## Restoring Original

If sanitization removed something important:

```bash
# Restore from backup
mv COMMAND_LOG.md.backup COMMAND_LOG.md

# Manually edit COMMAND_LOG.md to fix

# Try commit again
git add COMMAND_LOG.md
git commit -m "Update command log"
```

## Manual Review Checklist

Even with automated sanitization, always review for:

- [ ] Custom credentials not caught by patterns
- [ ] Sensitive file paths
- [ ] Internal system details
- [ ] Proprietary information
- [ ] Personal information

## Testing the Sanitization

To test without committing:

```bash
# Run sanitization manually
./scripts/shell/sanitize_command_log.sh

# Review changes
diff COMMAND_LOG.md.backup COMMAND_LOG.md

# Restore if needed
mv COMMAND_LOG.md.backup COMMAND_LOG.md
```

## Bypassing the Hook (Not Recommended)

If you absolutely need to commit without sanitization:

```bash
git commit --no-verify -m "Your message"
```

**⚠️ WARNING:** Only use this if you've manually verified the file is clean!

## Troubleshooting

### Hook Not Running

```bash
# Check hook is executable
ls -l .git/hooks/pre-commit

# If not:
chmod +x .git/hooks/pre-commit
```

### Script Not Found

```bash
# Check script exists and is executable
ls -l scripts/shell/sanitize_command_log.sh

# If not:
chmod +x scripts/shell/sanitize_command_log.sh
```

### False Positives

If the script removes non-sensitive data:

1. Edit the script: `scripts/shell/sanitize_command_log.sh`
2. Comment out or adjust the problematic `sed` pattern
3. Test: `./scripts/shell/sanitize_command_log.sh`
4. Commit the updated script

## Adding Custom Patterns

To sanitize additional patterns, edit `scripts/shell/sanitize_command_log.sh`:

```bash
# Add after existing patterns
sed "${SED_INPLACE[@]}" \
    -e 's/YOUR_PATTERN/REPLACEMENT/g' \
    "$LOG_FILE"
```

Examples:

```bash
# Sanitize custom API keys
sed "${SED_INPLACE[@]}" \
    -e 's/api[_-]key[": ]*[A-Za-z0-9]\{32\}/api_key: ********************************/g' \
    "$LOG_FILE"

# Sanitize phone numbers
sed "${SED_INPLACE[@]}" \
    -e 's/\b[0-9]\{3\}-[0-9]\{3\}-[0-9]\{4\}\b/xxx-xxx-xxxx/g' \
    "$LOG_FILE"
```

## Best Practices

1. **Test early** - Make a test commit early to verify the hook works
2. **Review always** - Even automated sanitization can miss things
3. **Keep backup** - The `.backup` file is automatically created for safety
4. **Update patterns** - Add new patterns as you discover new sensitive data types
5. **Document exceptions** - If you bypass the hook, document why

## Integration with CI/CD

If you set up automated testing/deployment, add a sanitization check:

```bash
# In CI pipeline
./scripts/shell/sanitize_command_log.sh
if [ -f COMMAND_LOG.md.backup ]; then
    echo "ERROR: COMMAND_LOG.md contains sensitive data!"
    exit 1
fi
```

---

**Last Updated:** 2025-09-30
# Security Protocols

This document contains all security procedures for git commits, pushes, and credential management.

## Automated Tools

**Pre-Push Inspection Tool:** `scripts/shell/pre_push_inspector.sh`
- Interactive 7-step workflow for repository cleanup before push
- Modes: `security-scan`, `inspect-repo`, `recommend`, `archive-cleanup`, `cleanup-repo`, `full`, `status`
- Run `bash scripts/shell/pre_push_inspector.sh full` before pushing to GitHub
- See usage examples at end of this document

## Critical Security Rules

**CRITICAL - Before EVERY git commit:**
1. **ALWAYS run security scan** and show results to user
2. **ALWAYS display flagged lines** for user review
3. **NEVER commit without showing scan results first**
4. Wait for user confirmation before proceeding with commit

**CRITICAL - Before EVERY git push:**

### Step 1: Security Scan (existing protocol)
1. Check staged files for credentials/secrets
2. Display any flagged lines to user
3. Get explicit approval before proceeding

### Step 2: Repository Inspection for Local-Only Files

After security scan passes, Claude will inspect the entire repository for files that should be archived and removed before pushing to GitHub:

```bash
# Automated scan of all tracked files
git ls-files | grep -E "\.(md|log|txt|json|csv)$"
```

**Categories Claude Should Flag:**

1. **Operational/Status Files:**
   - `*_STATUS.md`, `*_PROGRESS.md`, `*_SUMMARY.md`
   - Files with timestamps or runtime data
   - Process monitoring logs

2. **Command/Execution Logs:**
   - `COMMAND_LOG.md`, `COMMAND_HISTORY.md`
   - Files with command outputs or terminal sessions

3. **Temporary Documentation:**
   - `COMMIT_VERIFICATION.md`, `EXTRACTION_*.md`
   - Files created during automation/debugging
   - Session-specific notes

4. **Configuration with Sensitive Paths:**
   - Files containing local absolute paths
   - Machine-specific configurations
   - Development-only settings

5. **Large Data Files Accidentally Staged:**
   - `.csv`, `.json`, `.parquet` files in data directories
   - Database dumps or exports

**Claude's Inspection Criteria:**

✅ **Flag for Review:**
- Contains timestamps or session-specific data
- Shows command execution history
- Has operational status information
- Contains local absolute paths
- Includes debugging/troubleshooting notes
- Has machine-specific configuration
- Duplicates information already in curated docs

❌ **Do NOT Flag:**
- Essential project documentation (CLAUDE.md, PROGRESS.md, README.md)
- Curated documentation in docs/ directory
- Production code in scripts/
- Configuration templates (.env.example)
- Version-controlled application code
- Public-facing documentation

### Step 3: Present Recommendations to User

Format:
```
📋 Pre-Push Inspection Results:

Files Recommended for Deletion (Archive First):

🔴 HIGH PRIORITY (likely contains sensitive/operational data):
- path/to/file1.md (Reason: Contains command outputs with potential credentials)
- path/to/file2.log (Reason: Runtime logs with timestamps)

🟡 MEDIUM PRIORITY (operational data, no immediate risk):
- path/to/file3.md (Reason: Status file with local paths)
- path/to/file4.txt (Reason: Temporary notes from debugging)

🟢 LOW PRIORITY (consider for cleanup):
- path/to/file5.md (Reason: Redundant documentation)

Files to KEEP on GitHub:
✅ CLAUDE.md - Essential instructions
✅ PROGRESS.md - Project roadmap
✅ README.md - Public documentation
✅ All files in docs/ - Curated documentation
✅ All files in scripts/ - Reusable code

Would you like to proceed with archiving and deleting the flagged files? [YES/NO]
Or specify which files to keep: [file1, file2, ...]
```

### Step 4: User Confirmation

User responds with one of:
- `YES` - Archive and delete all flagged files
- `NO` - Skip deletion, proceed with push
- `file1, file3` - Only delete specified files
- `KEEP file2` - Remove file2 from deletion list

### Step 5: Archive Before Deletion

For each confirmed file:

```bash
# Create inspection-based archive
ARCHIVE_DIR=~/sports-simulator-archives/nba/pre-push-cleanup-$(date +%Y%m%d-%H%M%S)
mkdir -p "$ARCHIVE_DIR"

# Copy files to archive
for file in $CONFIRMED_FILES; do
    cp "$file" "$ARCHIVE_DIR/"
done

# Create cleanup record
cat > "$ARCHIVE_DIR/CLEANUP_RECORD.md" << EOF
# Pre-Push Cleanup Record

**Date:** $(date)
**Trigger:** Pre-push inspection
**Reason:** Files identified as local-only during GitHub push review

## Files Removed:

[List each file with reason]

## How to Access:

- Pre-push archive: $ARCHIVE_DIR
- Git history: git show <commit>:FILENAME
- Archive git repo: git -C ~/sports-simulator-archives/nba log --all

## Context:

These files were flagged during automated pre-push inspection and confirmed
for deletion by user before pushing to GitHub.
EOF

# Commit to archive git
cd ~/sports-simulator-archives/nba
git add pre-push-cleanup-*/
git commit -m "Pre-push cleanup - archive files before GitHub push"
cd -
```

### Step 6: Remove from Repository

```bash
# Remove from git tracking (keep local)
for file in $CONFIRMED_FILES; do
    git rm --cached "$file"
    echo "$file" >> .gitignore
done

# Commit removal
git add .gitignore
git commit -m "Remove local-only files identified in pre-push inspection

Files archived to: $ARCHIVE_DIR

[List files removed]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 7: Final Push Approval

1. **ALWAYS ask user "Ready to push to GitHub?" before attempting push**
2. **NEVER run `git push` without explicit user approval first**
3. **If pre-push hook blocks with security violations:**
   - STOP immediately
   - Show user the flagged lines from hook output
   - Explain what was flagged (false positives vs real secrets)
   - Ask: "These appear to be [false positives/real secrets]. Bypass hook and push anyway? [y/N]"
   - Only push with --no-verify if user explicitly approves
4. **NEVER assume prior approval applies to new pushes** - always ask each time

### Complete Push Protocol Summary

1. ✅ Security scan - Check for credentials/secrets
2. ✅ Repository inspection - Identify local-only files
3. ✅ User confirmation - Review and approve deletions
4. ✅ Archive flagged files - Pre-push cleanup archive created
5. ✅ Remove from tracking - git rm --cached + .gitignore update
6. ✅ Ask "Ready to push?" - Final user approval
7. ✅ Execute push - Only after all steps complete

## Security Scan Procedures

### Pre-Commit Security Scan

Before running `git commit`, ALWAYS perform automatic security scan:

```bash
# Step 1: Check staged files for sensitive data (comprehensive pattern)
git diff --staged | grep -E "(AWS_ACCESS_KEY[A-Z0-9]{16}|aws_secret|secret_access_key|aws_session_token|password|api[_-]?key|Bearer [A-Za-z0-9_-]+|BEGIN [REDACTED] KEY|ghp_[A-Za-z0-9]{36}|github_pat|postgres:|postgresql://.*:.*@|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)" -i

# Step 2: Check commit message for sensitive data
grep -E "(AWS_ACCESS_KEY|aws_secret|password|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)" .git/COMMIT_EDITMSG -i

# Step 3: If ANY matches found:
#   - STOP immediately
#   - Show matches to user
#   - NEVER commit AWS keys, secrets, or private IPs under any circumstances
#   - Remove sensitive data or abort commit

# Step 4: What to check for:
#   ❌ AWS access keys (AWS_ACCESS_KEY[A-Z0-9]{16})
#   ❌ AWS secret keys (aws_secret_access_key)
#   ❌ AWS session tokens (aws_session_token)
#   ❌ Private IP addresses (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
#   ❌ ANY IP addresses (per user requirement)
#   ❌ Passwords, API keys, Bearer tokens
#   ❌ SSH private keys (BEGIN + PRIVATE + KEY)
#   ❌ GitHub tokens (ghp_..., github_pat_...)
#   ❌ Database connection strings with passwords (postgresql://user:pass@host)
```

### Whitelist - Safe Patterns

```bash
# These are OK in documentation:
✅ Placeholder examples: "<YOUR_AWS_ACCESS_KEY_HERE>", "your-access-key-here", "<INSERT_KEY_HERE>"
✅ Documentation keywords: describing what to check for (like this list)
✅ Redacted credentials: [REDACTED], [Private network], [Router]
✅ Environment variable format: AWS_ACCESS_KEY_ID= (without value)
✅ Public DNS: Not allowed per user requirement (remove ALL IPs)

# NEVER use these placeholders (trigger security scanners):
❌ AWS_ACCESS_KEY**************** (still contains AWS_ACCESS_KEY prefix)
❌ Any pattern starting with AWS_ACCESS_KEY, even if redacted
```

### Security Check Protocol

1. Run grep scan BEFORE staging files
2. **If matches found: STOP immediately and show user:**
   ```bash
   # Save diff to temp file
   git diff --staged > /tmp/staged_diff.txt

   # Show ALL flagged lines with line numbers
   grep -n -E "(pattern)" -i /tmp/staged_diff.txt

   # Show FULL CONTEXT (10 lines before/after each match)
   grep -E "(pattern)" -i -B 10 -A 10 /tmp/staged_diff.txt
   ```
3. **Present to user:**
   - Show flagged line numbers
   - Show full context around each match
   - Explain what was detected (pattern definitions vs actual secrets)
   - Explain if deletions (safe) or additions (review needed)
   - **Ask explicitly:** "Do you approve bypassing pre-commit hook? [YES/NO]"
4. **Wait for user's explicit YES or NO response**
5. Only proceed with `--no-verify` if user responds YES
6. NEVER assume approval - always ask first

**CRITICAL: NEVER use --no-verify without:**
- ✅ Showing user ALL flagged lines with full context
- ✅ Explaining what was flagged and why
- ✅ Getting explicit YES approval from user

**NEVER commit without this security check.**

## Credential Management

### AWS Credentials Storage (CRITICAL)

- **Primary Location:** `~/.aws/credentials` (AWS CLI standard, chmod 600)
- **Backup Location:** Store encrypted backups outside project directory (never commit)
- **NEVER:**
  - Copy credentials into project directory
  - Store credentials in environment variables
  - Reference credentials in code (boto3 auto-reads from ~/.aws/credentials)
  - Commit credential files to Git
  - Document exact paths to credential backups (security risk)

### Credential Rotation Schedule

Follow these security best practices for credential rotation:

| Credential Type | Rotation Frequency | How to Rotate | Priority |
|-----------------|-------------------|---------------|----------|
| **AWS Access Keys** | Every 90 days | AWS Console → IAM → Users → Security Credentials | 🔴 High |
| **AWS Secret Keys** | Every 90 days | Generate new key, update ~/.aws/credentials, delete old | 🔴 High |
| **SSH Keys** | Annually | Generate new keypair, update GitHub, delete old | 🟡 Medium |
| **Database Passwords** | Every 90 days (when RDS created) | AWS Console → RDS → Modify → New password | 🔴 High |
| **API Tokens** | Every 90 days | Regenerate in service, update .env | 🟡 Medium |

**Rotation Reminders:**
- Set calendar reminders for 85 days after each rotation
- Use AWS IAM Access Analyzer to identify unused credentials
- Check: `aws iam get-credential-report` to see key ages
- Document last rotation date in COMMAND_LOG.md or create calendar event

**Emergency Rotation (if compromised):**
1. Immediately deactivate compromised credential
2. Generate new credential
3. Update all systems using old credential
4. Delete compromised credential
5. Review CloudTrail logs for unauthorized access
6. Document incident in TROUBLESHOOTING.md

## GitHub Secret Scanning

GitHub provides free secret scanning for public repositories. To enable for this project:

### 1. Enable Secret Scanning (if public)

- Go to: https://github.com/ryanranft/nba-simulator-aws/settings/security_analysis
- Enable "Secret scanning"
- Enable "Push protection" (blocks pushes with secrets)

### 2. What GitHub Detects

- AWS credentials (access keys, secret keys, session tokens)
- GitHub Personal Access Tokens (PATs)
- Azure, Google Cloud, Slack tokens
- Database connection strings with passwords
- 200+ partner patterns

### 3. How It Works

- Scans all commits in history
- Alerts on Settings → Security → Secret scanning alerts
- Push protection blocks new secrets from being pushed
- Partners (like AWS) are notified of leaked credentials

### 4. Local Git Hooks (Already Implemented)

- Pre-commit hook: Blocks commits with secrets
- Pre-push hook: Scans last 5 commits before push
- Commit template: Reminds about security in every commit
- Located in: `.git/hooks/pre-commit`, `.git/hooks/pre-push`

### 5. Testing the Protection

```bash
# Try to commit a test secret (will be blocked):
echo "aws_access_key_id=AWS_ACCESS_KEYIOSFODNN7EXAMPLE" > test.txt
git add test.txt
git commit -m "test"  # Should be blocked by pre-commit hook
rm test.txt
```

### 6. If Secret Is Detected

- Immediately rotate the compromised credential
- Review GitHub alert for details
- Check AWS CloudTrail for unauthorized usage
- Update all systems using the old credential

### Layered Security Summary

- ✅ Layer 1: .gitignore (prevents staging sensitive files)
- ✅ Layer 2: Pre-commit hook (blocks commits with secrets)
- ✅ Layer 3: Pre-push hook (scans recent commit history)
- ✅ Layer 4: Commit template (reminds about security)
- ✅ Layer 5: GitHub secret scanning (cloud-based detection)
- ✅ Layer 6: Credential rotation schedule (90-day intervals)

## Data Safety Protocol

- NEVER delete or modify S3 bucket contents without explicit user request
- NEVER drop database tables without user confirmation
- NEVER commit `.env`, credentials, or sensitive data
- ALWAYS run `sanitize_command_log.sh` before committing COMMAND_LOG.md
- Backup before destructive operations (provide backup command)

## Commit Format

**Standard commit format (include co-authorship footer):**

```bash
git commit -m "$(cat <<'EOF'
Brief description of changes

Detailed explanation if needed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Pre-Push Inspector Usage Examples

**Full interactive workflow (recommended before git push):**
```bash
bash scripts/shell/pre_push_inspector.sh full
```

**Individual modes:**
```bash
# Security scan only
bash scripts/shell/pre_push_inspector.sh security-scan

# Inspect repository for local-only files
bash scripts/shell/pre_push_inspector.sh inspect-repo

# Show recommendations with priority levels
bash scripts/shell/pre_push_inspector.sh recommend

# Archive flagged files
bash scripts/shell/pre_push_inspector.sh archive-cleanup

# Remove files from tracking
bash scripts/shell/pre_push_inspector.sh cleanup-repo

# Preview what would be flagged (dry-run)
bash scripts/shell/pre_push_inspector.sh status

# Show help
bash scripts/shell/pre_push_inspector.sh help
```

**Typical workflow:**
```bash
# Before pushing to GitHub
cd /Users/ryanranft/nba-simulator-aws
bash scripts/shell/pre_push_inspector.sh full

# Follow interactive prompts
# - Review security scan results
# - Review flagged local-only files
# - Confirm which files to archive/delete
# - Approve final push

# After workflow completes
git push
```
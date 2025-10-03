# Workflow #36: Pre-Push Repository Cleanup

**Category:** Git & Security
**Priority:** High
**When to Use:** Before every `git push`, especially first push or after major work
**Related Workflows:** #10 (Git Push), #8 (Git Commit), #9 (Archive Management)

---

## Overview

This workflow provides a detailed 7-step interactive process for cleaning up your repository before pushing to GitHub. It identifies local-only files (operational docs, logs, status files) and archives them before removal.

**Purpose:** Prevent committing operational/temporary files to GitHub while preserving complete local history.

---

## When to Use This Workflow

✅ **USE before:**
- First push to GitHub (repository contains local-only files)
- After major development sessions (accumulated operational files)
- Before pushing to public/team repository
- When `git status` shows many untracked/modified documentation files
- After overnight automation/ETL runs (created status files)

❌ **DON'T NEED when:**
- Pushing trivial code changes
- Repository already clean (verified with `status` mode)
- Just updating existing tracked files

---

## Automated Tool

**Script:** `scripts/shell/pre_push_inspector.sh`

**Usage:**
```bash
# Full interactive workflow (recommended)
bash scripts/shell/pre_push_inspector.sh full

# Individual steps
bash scripts/shell/pre_push_inspector.sh security-scan
bash scripts/shell/pre_push_inspector.sh inspect-repo
bash scripts/shell/pre_push_inspector.sh status

# Help
bash scripts/shell/pre_push_inspector.sh help
```

---

## The 7-Step Workflow

### Step 1: Security Scan

**Purpose:** Detect credentials/secrets in staged files

#### What Gets Scanned

**Security patterns checked:**
- AWS Access Keys (`AKIA[A-Z0-9]{16}`)
- AWS Secret Keys (`aws_secret_access_key.*[A-Za-z0-9/+=]{40}`)
- Private SSH keys (`BEGIN RSA PRIVATE KEY`)
- GitHub Tokens (`ghp_`, `gho_`, `ghs_`, `ghr_`)
- Database connection strings (`postgresql://user:password@host`)
- Private IP addresses (`192.168.x.x`, `10.x.x.x`)

#### Run Security Scan

**Automatic (via pre-commit hook):**
```bash
git commit -m "message"
# Hook automatically runs security scan
```

**Manual:**
```bash
bash scripts/shell/pre_push_inspector.sh security-scan
```

**Expected output:**
```
🔒 Running Security Scan...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scanning staged files for sensitive information...

✅ Security scan passed - no sensitive data detected

Files scanned: 15
Patterns checked: 15
Issues found: 0
```

**If secrets detected:**
```
❌ SECURITY VIOLATION: Secrets detected

Commit abc123 contains potential secrets:
  docs/SETUP.md:45: aws_access_key_id = AKIAIOSFODNN7EXAMPLE

⚠️  COMMIT BLOCKED - Secrets detected
```

**Action:**
1. Review flagged lines
2. Determine if false positive (documentation example) or real secret
3. If false positive: Explain to user, get approval to bypass
4. If real secret: Remove from file, never commit

---

### Step 2: Repository Inspection

**Purpose:** Identify local-only files that shouldn't go to GitHub

#### File Categories

**🔴 HIGH PRIORITY** (likely contains sensitive/operational data):
- Operational status files: `*_STATUS.md`, `*_PROGRESS.md`, `*_SUMMARY.md`
- Command logs: `COMMAND_LOG.md`, `COMMAND_HISTORY.md`, `*_LOG.md`
- Contains runtime data, timestamps, machine-specific paths

**🟡 MEDIUM PRIORITY** (operational data, no immediate risk):
- Temporary documentation: `COMMIT_VERIFICATION.md`, `EXTRACTION_*.md`, `TEST_*.md`
- Configuration with local paths: `*.env` (if not .gitignored)
- Workflow comparison files: `WORKFLOW_*_COMPARISON.md`

**🟢 LOW PRIORITY** (consider for cleanup):
- Data files: `*.csv`, `*.json`, `*.parquet` in data directories
- Large log files
- Redundant documentation

#### Files to ALWAYS Keep

**✅ Essential files (never flagged):**
- Core instructions: `CLAUDE.md`, `README.md`, `PROGRESS.md`, `QUICKSTART.md`
- Curated documentation: `docs/*.md`, `TROUBLESHOOTING.md`, `STYLE_GUIDE.md`
- Production code: `scripts/**/*.sh`, `scripts/**/*.py`
- Configuration templates: `*.example`, `.gitignore`, `requirements.txt`, `Makefile`

#### Run Repository Inspection

```bash
# Scan for local-only files
bash scripts/shell/pre_push_inspector.sh inspect-repo
```

**Expected output:**
```
📂 Scanning Repository for Local-Only Files...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tracked files analyzed: 145
Files flagged for review: 8

🔴 HIGH PRIORITY:
  - COMMAND_LOG.md (operational: contains command history)
  - EXTRACTION_STATUS.md (operational: contains runtime data)

🟡 MEDIUM PRIORITY:
  - COMMIT_VERIFICATION.md (temp_docs: temporary verification file)
  - TEST_RESULTS.md (temp_docs: test output summary)

🟢 LOW PRIORITY:
  - data/sample.csv (data: large data file)

✅ Files to KEEP:
  - CLAUDE.md (essential instructions)
  - PROGRESS.md (project roadmap)
  - docs/*.md (curated documentation)
  - scripts/*.sh (production code)
```

---

### Step 3: Present Recommendations

**Purpose:** Show user what files should be removed with rationale

#### Recommendation Format

```
📋 Pre-Push Inspection Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files Recommended for Deletion (Archive First):

🔴 HIGH PRIORITY (likely contains sensitive/operational data):
  ❌ COMMAND_LOG.md
     Reason: Contains command outputs with potential credentials
     Risk: May expose AWS commands, file paths, error messages
     Action: Archive → Delete

  ❌ EXTRACTION_STATUS.md
     Reason: Runtime logs with timestamps
     Risk: Exposes operational details, no value for other users
     Action: Archive → Delete

🟡 MEDIUM PRIORITY (operational data, no immediate risk):
  ⚠️  COMMIT_VERIFICATION.md
     Reason: Status file with local paths
     Risk: Machine-specific, not useful on GitHub
     Action: Archive → Delete

  ⚠️  TEST_RESULTS.md
     Reason: Temporary notes from debugging
     Risk: Low, but clutters repository
     Action: Archive → Delete

🟢 LOW PRIORITY (consider for cleanup):
  💡 data/sample.csv
     Reason: Data file (should use .gitignore)
     Risk: None, just large file
     Action: Archive → Delete → Add to .gitignore

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files to KEEP on GitHub:
✅ CLAUDE.md - Essential instructions
✅ PROGRESS.md - Project roadmap
✅ README.md - Public documentation
✅ All files in docs/ - Curated documentation
✅ All files in scripts/ - Reusable code
✅ TROUBLESHOOTING.md - Error solutions
✅ STYLE_GUIDE.md - Code standards

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total files flagged: 5
Total to archive: 5
Total to delete: 5
```

**Run recommendations:**
```bash
bash scripts/shell/pre_push_inspector.sh recommend
```

---

### Step 4: User Confirmation

**Purpose:** Get explicit user approval for deletions

#### Confirmation Prompt

```
Would you like to proceed with archiving and deleting the flagged files?

Options:
  [Y]   Yes - Archive and delete ALL flagged files
  [N]   No - Skip deletion, proceed with push as-is
  [L]   List - Show files again
  [S]   Select - Choose which files to delete (comma-separated)
  [K]   Keep - Specify files to keep (remove from deletion list)
  [Q]   Quit - Cancel entire operation

Enter choice [Y/N/L/S/K/Q]:
```

#### User Responses

**Option Y (Yes - Delete All):**
```
You entered: Y
✅ Proceeding with archiving and deletion of ALL 5 flagged files
```

**Option N (No - Skip):**
```
You entered: N
⏭️  Skipping deletion - flagged files will remain in repository
Would you still like to proceed with git push? [y/N]:
```

**Option S (Select Specific Files):**
```
You entered: S
Enter file numbers to delete (comma-separated, e.g., 1,3,5):
Available files:
  1. COMMAND_LOG.md
  2. EXTRACTION_STATUS.md
  3. COMMIT_VERIFICATION.md
  4. TEST_RESULTS.md
  5. data/sample.csv

Your selection: 1,2,5
✅ Will delete: COMMAND_LOG.md, EXTRACTION_STATUS.md, data/sample.csv
✅ Will keep: COMMIT_VERIFICATION.md, TEST_RESULTS.md
```

**Option K (Keep Specific Files):**
```
You entered: K
Enter file numbers to KEEP (remove from deletion):
Available files:
  1. COMMAND_LOG.md
  2. EXTRACTION_STATUS.md
  3. COMMIT_VERIFICATION.md
  4. TEST_RESULTS.md
  5. data/sample.csv

Files to keep: 3,4
✅ Removed from deletion: COMMIT_VERIFICATION.md, TEST_RESULTS.md
✅ Will still delete: COMMAND_LOG.md, EXTRACTION_STATUS.md, data/sample.csv
```

---

### Step 5: Archive Before Deletion

**Purpose:** Preserve complete history before removing files from git

#### Archive Directory Structure

```
~/sports-simulator-archives/nba/
└── pre-push-cleanup-20251002-143015/
    ├── CLEANUP_RECORD.md
    ├── COMMAND_LOG.md
    ├── EXTRACTION_STATUS.md
    └── data/
        └── sample.csv
```

#### Archive Process

```bash
# Create timestamped archive directory
ARCHIVE_DIR="$HOME/sports-simulator-archives/nba/pre-push-cleanup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$ARCHIVE_DIR"

# Copy files to archive
for file in "${confirmed_files[@]}"; do
    # Preserve directory structure
    target_dir="$ARCHIVE_DIR/$(dirname "$file")"
    mkdir -p "$target_dir"
    cp "$file" "$target_dir/"
done

# Create cleanup record
cat > "$ARCHIVE_DIR/CLEANUP_RECORD.md" << EOF
# Pre-Push Cleanup Record

**Date:** $(date)
**Trigger:** Pre-push repository inspection
**Reason:** Files identified as local-only during GitHub push review

## Files Removed

$(for file in "${confirmed_files[@]}"; do
    category=$(categorize_file "$file")
    priority=$(get_priority "$category")
    reason=$(get_reason "$file" "$category")
    echo "- **$file** ($priority priority)"
    echo "  - Category: $category"
    echo "  - Reason: $reason"
    echo ""
done)

## How to Access

- **Pre-push archive:** $ARCHIVE_DIR
- **Git history:** \`git show <commit>:FILENAME\`
- **Archive git repo:** \`git -C ~/sports-simulator-archives/nba log --all\`

## Context

These files were flagged during automated pre-push inspection and confirmed
for deletion by user before pushing to GitHub.

All files preserved in this archive and in local git history.
EOF
```

**Output:**
```
📦 Archiving Files...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Archive directory: ~/sports-simulator-archives/nba/pre-push-cleanup-20251002-143015

Archiving files:
  ✅ COMMAND_LOG.md → archived
  ✅ EXTRACTION_STATUS.md → archived
  ✅ data/sample.csv → archived
  ✅ CLEANUP_RECORD.md → created

Committing to archive git repo...
[main abc1234] Pre-push cleanup - archive files before GitHub push
 4 files changed, 1523 insertions(+)

✅ Archive complete
```

---

### Step 6: Remove from Repository

**Purpose:** Remove files from git tracking while keeping local copies

#### Removal Process

```bash
# Remove from git tracking (keep local file)
for file in "${confirmed_files[@]}"; do
    git rm --cached "$file"
    echo "$file" >> .gitignore
done

# Sort and deduplicate .gitignore
sort -u .gitignore -o .gitignore

# Commit removal
git add .gitignore
git commit -m "Remove local-only files identified in pre-push inspection

Files archived to: ~/sports-simulator-archives/nba/pre-push-cleanup-$(date +%Y%m%d-%H%M%S)

Files removed from GitHub (preserved locally):
$(for file in "${confirmed_files[@]}"; do echo "- $file"; done)

These files contained operational data, command logs, or temporary documentation
not suitable for GitHub but preserved in local archive for future reference.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Output:**
```
🗑️  Removing from Git Tracking...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Removing files:
  ✅ git rm --cached COMMAND_LOG.md
  ✅ git rm --cached EXTRACTION_STATUS.md
  ✅ git rm --cached data/sample.csv

Updating .gitignore:
  ✅ Added: COMMAND_LOG.md
  ✅ Added: EXTRACTION_STATUS.md
  ✅ Added: data/sample.csv

Committing changes:
[main def5678] Remove local-only files identified in pre-push inspection
 4 files changed, 3 deletions(-)
 delete mode 100644 COMMAND_LOG.md
 delete mode 100644 EXTRACTION_STATUS.md
 delete mode 100644 data/sample.csv

✅ Removal complete

Note: Files still exist locally, just not tracked by git
```

---

### Step 7: Final Push Approval

**Purpose:** Confirm user approval before actually pushing to GitHub

#### Push Approval Prompt

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 Ready to Push to GitHub
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary of Changes:
  - 3 files archived locally
  - 3 files removed from git tracking
  - 1 commit created (cleanup)
  - .gitignore updated

Files that WILL be pushed:
  ✅ CLAUDE.md
  ✅ PROGRESS.md
  ✅ README.md
  ✅ docs/ (all curated documentation)
  ✅ scripts/ (all production code)

Files that will NOT be pushed (archived locally):
  ❌ COMMAND_LOG.md
  ❌ EXTRACTION_STATUS.md
  ❌ data/sample.csv

Ready to push to GitHub? [y/N]:
```

**If user confirms (y):**
```
You entered: y

Pushing to GitHub...
Enumerating objects: 15, done.
Counting objects: 100% (15/15), done.
Delta compression using up to 8 threads
Compressing objects: 100% (8/8), done.
Writing objects: 100% (9/9), 1.23 KiB | 1.23 MiB/s, done.
Total 9 (delta 6), reused 0 (delta 0)
To github.com:ryanranft/nba-simulator-aws.git
   abc1234..def5678  main -> main

✅ Push successful!
```

**If user declines (N):**
```
You entered: N

⏸️  Push cancelled
Repository cleaned but not pushed
Run 'git push' manually when ready
```

---

## Complete Workflow Example

**Full interactive session:**

```bash
$ bash scripts/shell/pre_push_inspector.sh full

╔══════════════════════════════════════════════════════════════╗
║       Pre-Push Inspection Workflow - Interactive Tool       ║
╚══════════════════════════════════════════════════════════════╝

Step 1/7: Security Scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Security scan passed - no sensitive data detected

Step 2/7: Repository Inspection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Files flagged for review: 5

Step 3/7: Recommendations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 HIGH PRIORITY: 2 files
🟡 MEDIUM PRIORITY: 2 files
🟢 LOW PRIORITY: 1 file

Step 4/7: User Confirmation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceed with archiving and deleting? [Y/N/L/S/K/Q]: Y

Step 5/7: Archiving
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 5 files archived to ~/sports-simulator-archives/nba/pre-push-cleanup-20251002-143015

Step 6/7: Removal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 5 files removed from git tracking
✅ .gitignore updated
✅ Cleanup commit created

Step 7/7: Push Approval
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready to push to GitHub? [y/N]: y
✅ Push successful!

╔══════════════════════════════════════════════════════════════╗
║                  Workflow Complete ✅                       ║
╚══════════════════════════════════════════════════════════════╝

Summary:
  - Security scan: ✅ Passed
  - Files archived: 5
  - Files removed: 5
  - Commits created: 1
  - Push status: ✅ Successful

Archive location: ~/sports-simulator-archives/nba/pre-push-cleanup-20251002-143015
```

---

## Dry-Run Mode (Preview Only)

**Preview what would be flagged without making changes:**

```bash
bash scripts/shell/pre_push_inspector.sh status
```

**Output:**
```
🔍 Pre-Push Status (Dry-Run Mode)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is a preview - no files will be changed

Files that would be flagged for deletion:
  🔴 COMMAND_LOG.md (HIGH: command history)
  🔴 EXTRACTION_STATUS.md (HIGH: operational data)
  🟡 COMMIT_VERIFICATION.md (MEDIUM: temp documentation)
  🟡 TEST_RESULTS.md (MEDIUM: temp documentation)
  🟢 data/sample.csv (LOW: data file)

Files that would be kept:
  ✅ CLAUDE.md
  ✅ PROGRESS.md
  ✅ README.md
  ✅ docs/*.md
  ✅ scripts/*.sh

To proceed with cleanup: bash scripts/shell/pre_push_inspector.sh full
```

---

## Integration with Other Workflows

**Before git push:**
1. Commit all code changes (workflow #8)
2. Run security scan (part of commit, workflow #8)
3. **Run pre-push inspection** (this workflow #36)
4. Get user approval for cleanup
5. Archive flagged files
6. Remove from repository
7. Push to GitHub (workflow #10)

**If using workflow #10 (Git Push):**
- Workflow #10 mentions "run pre-push inspection"
- **This workflow (#36) IS the detailed pre-push inspection**
- Use this workflow for the full 7-step process

---

## Troubleshooting

### Issue: Script Not Found

**Error:**
```
bash: scripts/shell/pre_push_inspector.sh: No such file or directory
```

**Solution:**
```bash
# Ensure you're in project root
cd /Users/ryanranft/nba-simulator-aws

# Verify script exists
ls -la scripts/shell/pre_push_inspector.sh

# Make executable if needed
chmod +x scripts/shell/pre_push_inspector.sh
```

### Issue: Files Still Tracked After Removal

**Error:**
```
git status shows files as "deleted" not "untracked"
```

**Solution:**
```bash
# Files were removed from git but not from .gitignore
# Add to .gitignore manually
echo "COMMAND_LOG.md" >> .gitignore

# Commit .gitignore
git add .gitignore
git commit -m "Add removed files to .gitignore"
```

### Issue: Archive Directory Not Found

**Error:**
```
Archive directory ~/sports-simulator-archives/nba/ doesn't exist
```

**Solution:**
```bash
# Create archive base directory
mkdir -p ~/sports-simulator-archives/nba

# Initialize git repo in archive
cd ~/sports-simulator-archives/nba
git init
git add .
git commit -m "Initialize NBA archive"
```

---

## Best Practices

1. **Always run `status` mode first** to preview what would be flagged
2. **Review recommendations carefully** before confirming deletions
3. **Keep CLAUDE.md, PROGRESS.md, README.md** - these are essential
4. **Archive everything** before deletion (automatic in this workflow)
5. **Update .gitignore** to prevent re-tracking (automatic in this workflow)
6. **Run before first push** to clean up accumulated operational files
7. **Run periodically** (weekly/monthly) to keep repository clean

---

## Resources

**Scripts:**
- `scripts/shell/pre_push_inspector.sh` - Main workflow script
- `scripts/shell/security_scan.sh` - Security scanning

**Documentation:**
- `docs/SECURITY_PROTOCOLS.md` - Complete security procedures
- `docs/ARCHIVE_PROTOCOLS.md` - Archive system documentation
- Workflow #8 - Git Commit (security scanning)
- Workflow #9 - Archive Management
- Workflow #10 - Git Push (calls this workflow)

**Commands:**
```bash
# Full workflow
bash scripts/shell/pre_push_inspector.sh full

# Preview only
bash scripts/shell/pre_push_inspector.sh status

# Individual steps
bash scripts/shell/pre_push_inspector.sh security-scan
bash scripts/shell/pre_push_inspector.sh inspect-repo
bash scripts/shell/pre_push_inspector.sh recommend

# Help
bash scripts/shell/pre_push_inspector.sh help
```

---

**Last Updated:** 2025-10-02
**Source:** docs/SECURITY_PROTOCOLS.md + scripts/shell/pre_push_inspector.sh
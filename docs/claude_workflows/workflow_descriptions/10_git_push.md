## 🚀 Git Push Workflow - Complete Pre-Push Inspection

**CRITICAL: ALWAYS follow pre-push inspection before pushing**

### Overview: 7 Available Modes

The `pre_push_inspector.sh` script has 7 modes for different inspection needs:

| Mode | Purpose | Interactive? | When to Use |
|------|---------|--------------|-------------|
| `security-scan` | 15-point security audit | No | Quick security check only |
| `inspect-repo` | Scan for local-only files | No | Check what shouldn't be pushed |
| `recommend` | Show recommendations | No | See what needs cleanup |
| `archive-cleanup` | Archive then remove files | Yes | Preserve before deletion |
| `cleanup-repo` | Remove from git tracking | Yes | Clean repo before push |
| `full` | Complete interactive workflow | Yes | **RECOMMENDED** - all 7 steps |
| `status` | Dry-run preview | No | See what would happen |

### Recommended Workflow: Full Mode (Interactive)

**Step 1: Run Full Pre-Push Inspector**

```bash
bash scripts/shell/pre_push_inspector.sh full
```

**This runs all 7 steps automatically:**

#### **Step 1/7: Security Scan (Automatic)**

**What it checks (15 security points):**
1. Git history for AWS keys (all commits)
2. Git history for database passwords
3. Git history for private IP addresses
4. Staged files for AWS access keys
5. Staged files for AWS secret keys
6. Staged files for AWS session tokens
7. Staged files for private IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
8. Staged files for database connection strings
9. Staged files for SSH private keys
10. Staged files for GitHub tokens (ghp_*, github_pat_*)
11. Commit messages for sensitive data
12. `.env` files in staged changes
13. `credentials.yaml` in staged changes
14. AWS CLI config files
15. Database dump files

**If security issues found:**
- Script **STOPS immediately**
- Shows flagged lines with context
- Asks: "CRITICAL security violations found. Abort push? [Y/n]"
- **Recommend:** Fix issues, don't bypass

#### **Step 2/7: Repository Inspection (Automatic)**

**Scans for local-only files not suitable for GitHub:**

**Categories checked:**
1. **🔴 HIGH PRIORITY** - Operational files (COMMAND_LOG.md, EXTRACTION_STATUS.md, etc.)
2. **🟡 MEDIUM PRIORITY** - Log files (*.log, debug output)
3. **🟢 LOW PRIORITY** - Temp docs (.session-history.md, temp notes)
4. **⚙️ CONFIG** - Local config (.env, credentials)
5. **📊 DATA** - Data files (CSVs, SQLite, large files >10MB)

**Output example:**
```
🔴 HIGH PRIORITY (operational):
  - COMMAND_LOG.md (contains command history)
  - COMMIT_VERIFICATION.md (pre-commit results)

🟡 MEDIUM PRIORITY (logs):
  - error.log (may contain sensitive info)

🟢 LOW PRIORITY (temp):
  - .session-history.md (session diagnostics)
```

#### **Step 3/7: Present Recommendations (Automatic)**

**Shows organized recommendations:**

```
RECOMMENDATIONS:

Archive before pushing:
  - COMMAND_LOG.md (operational history)
  - error.log (debugging info)

Add to .gitignore:
  - *.log
  - .session-history.md

Safe to keep (already gitignored):
  - .env
  - credentials.yaml
```

#### **Step 4/7: User Confirmation (Interactive)**

**Asks for cleanup decision:**
```
Files flagged for cleanup. Choose action:
  [1] YES - Archive and remove all flagged files
  [2] NO - Skip cleanup, push as-is
  [3] SPECIFY - Choose specific files to clean

Your choice:
```

**Options:**
- **YES** → Proceeds to archive-cleanup (Step 5)
- **NO** → Skips to push approval (Step 7)
- **SPECIFY** → Prompts for file list, then archives specified files

#### **Step 5/7: Archive Before Deletion (Automatic if confirmed)**

**Creates preservation archive:**

```bash
ARCHIVE_DIR=~/sports-simulator-archives/nba/pre-push-cleanup-$(date +%Y%m%d-%H%M%S)
mkdir -p "$ARCHIVE_DIR"

# Copy all flagged files
for file in "${flagged_files[@]}"; do
  cp "$file" "$ARCHIVE_DIR/"
done

# Create cleanup record
cat > "$ARCHIVE_DIR/CLEANUP_RECORD.md" << EOF
# Pre-Push Cleanup Record

**Date:** $(date)
**Commit:** $(git rev-parse HEAD)
**Files Removed:** ${#flagged_files[@]} files
**Reason:** Pre-push repository cleanup
**Recovery:** Files archived at $ARCHIVE_DIR

## Files Removed:
$(printf '- %s\n' "${flagged_files[@]}")
EOF
```

**Archive location:** `~/sports-simulator-archives/nba/pre-push-cleanup-<timestamp>/`

#### **Step 6/7: Remove from Repository (Automatic if confirmed)**

**Removes files from git tracking:**

```bash
# Remove from git (keeps local copy)
for file in "${flagged_files[@]}"; do
  git rm --cached "$file"
  echo "$file" >> .gitignore
done

# Commit cleanup
git add .gitignore
git commit -m "Pre-push cleanup: Remove local-only files

Archived to: $ARCHIVE_DIR

Files removed from tracking:
$(printf '- %s\n' "${flagged_files[@]}")

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**What happens:**
- Files removed from git tracking (`git rm --cached`)
- Files stay in local working directory
- Files added to .gitignore
- Cleanup commit created automatically

#### **Step 7/7: Final Push Approval (Interactive)**

**Asks for explicit push approval:**
```
Pre-push inspection complete.

Summary:
  ✅ Security scan passed
  ✅ 5 files archived and removed
  ✅ .gitignore updated
  ✅ Repository cleaned

Ready to push to GitHub? [y/N]:
```

**Options:**
- **y** → Executes `git push`
- **N** → Exits without pushing (default)

---

### Individual Mode Usage

#### Mode 1: Security Scan Only

```bash
bash scripts/shell/pre_push_inspector.sh security-scan
```

**Use when:**
- Quick security check before push
- Don't need repository cleanup
- Just want to verify no secrets

**What it does:**
- Runs 15-point security audit
- Reports findings
- Exits (no cleanup, no push)

**Exit codes:**
- `0` - No security issues found
- `1` - Security violations detected

#### Mode 2: Repository Inspection Only

```bash
bash scripts/shell/pre_push_inspector.sh inspect-repo
```

**Use when:**
- Want to see local-only files
- Planning cleanup strategy
- Not ready to make changes

**What it does:**
- Scans repository for local-only files
- Categorizes by priority (HIGH/MEDIUM/LOW)
- Reports findings
- Exits (no changes made)

#### Mode 3: Recommendations Only

```bash
bash scripts/shell/pre_push_inspector.sh recommend
```

**Use when:**
- Want actionable cleanup suggestions
- Planning manual cleanup
- Understanding what needs fixing

**What it does:**
- Runs inspection (Mode 2)
- Generates recommendations
- Groups by action type (archive, ignore, keep)
- Exits (no changes made)

#### Mode 4: Archive and Cleanup

```bash
bash scripts/shell/pre_push_inspector.sh archive-cleanup
```

**Use when:**
- Ready to clean repository
- Want automatic archiving
- Interactive file selection

**What it does:**
- Runs inspection
- Shows recommendations
- Asks which files to clean
- Archives selected files
- Does NOT remove from git (use Mode 5 for that)

#### Mode 5: Remove from Git Tracking

```bash
bash scripts/shell/pre_push_inspector.sh cleanup-repo
```

**Use when:**
- Files already archived (Mode 4)
- Ready to remove from git
- Want cleanup commit

**What it does:**
- Assumes files already backed up
- Runs `git rm --cached` on specified files
- Updates .gitignore
- Creates cleanup commit
- Does NOT push (manual push required)

**⚠️ WARNING:** This modifies git tracking. Ensure files are archived first (Mode 4).

#### Mode 6: Full Workflow (Recommended)

```bash
bash scripts/shell/pre_push_inspector.sh full
```

**Already documented above - runs all 7 steps**

#### Mode 7: Dry-Run Status Check

```bash
bash scripts/shell/pre_push_inspector.sh status
```

**Use when:**
- Want to preview full workflow
- Not ready to make changes
- Testing inspector behavior

**What it does:**
- Runs security scan (no stopping)
- Runs repository inspection
- Shows recommendations
- Shows what WOULD be archived
- Shows what WOULD be removed
- **Does NOT make any changes**
- **Does NOT prompt for input**

**Output:**
```
DRY RUN - No changes will be made

Security Scan Results:
  ✅ No security violations found

Repository Inspection:
  🔴 5 files flagged for cleanup
  🟡 2 log files found
  🟢 3 temp files found

WOULD archive:
  - COMMAND_LOG.md
  - error.log
  - .session-history.md

WOULD add to .gitignore:
  - *.log
  - .session-history.md

Status check complete. Run with 'full' mode to execute.
```

---

### Workflow Decision Guide

**Choose your mode based on situation:**

```
┌─────────────────────────────────────────────────┐
│ Are you ready to push to GitHub?               │
└────────────┬────────────────────────────────────┘
             │
        YES  │  NO
             │
    ┌────────┴────────┐
    │                 │
    v                 v
┌───────────┐   ┌──────────────┐
│ Run 'full'│   │ Just checking│
│ mode      │   │ status?      │
└───────────┘   └──────┬───────┘
                       │
                  YES  │  NO
                       │
              ┌────────┴──────────┐
              │                   │
              v                   v
        ┌──────────┐      ┌──────────────┐
        │ Run      │      │ Need specific│
        │ 'status' │      │ action?      │
        └──────────┘      └──────┬───────┘
                                 │
                            ┌────┴────┐
                            │         │
                            v         v
                    ┌─────────────┐ ┌─────────────┐
                    │security-scan│ │inspect-repo │
                    │recommend    │ │archive-     │
                    │             │ │cleanup      │
                    └─────────────┘ └─────────────┘
```

---

### Error Handling

**If pre-push inspector fails:**

1. **Security scan blocks:**
   - Review flagged content
   - Fix security issues
   - Re-run security-scan mode
   - Only bypass if false positives (ask user first)

2. **Archive fails:**
   - Check disk space: `df -h`
   - Check permissions: `ls -la ~/sports-simulator-archives/`
   - Create archive dir manually if needed
   - Re-run archive-cleanup mode

3. **Cleanup commit fails:**
   - Check git status: `git status`
   - Resolve any conflicts
   - Re-run cleanup-repo mode

4. **Push fails:**
   - Check network: `ping github.com`
   - Check remote: `git remote -v`
   - Check credentials: `ssh -T git@github.com`
   - Try push manually: `git push`

---

### Integration with Git Commit Workflow

**Recommended sequence:**

1. Complete work → Document in COMMAND_LOG.md
2. Run security scan (Git Commit Workflow Step 0-1)
3. Commit changes (Git Commit Workflow Step 3)
4. Run archive manager (Git Commit Workflow Step 5)
5. **Run pre-push inspector (THIS WORKFLOW)**
6. Push to GitHub (after approval)

---

### Ask User for Push Approval (After Inspector Completes)

**NEVER push without asking:**

```
Pre-push inspection complete. Ready to push to GitHub? [y/N]
```

**If user says YES:**
```bash
git push
```

**If user says NO:**
- Exit workflow
- User can push manually later: `git push`

---

### If Pre-Push Hook Blocks (Last Resort)

**STOP immediately:**
- Show user the flagged lines from hook output
- Explain what was flagged (false positives vs real secrets)
- Show context (10 lines before/after)
- Ask: "These appear to be [false positives/real secrets]. Bypass hook and push anyway? [y/N]"
- **Only push with `--no-verify` if user explicitly approves**

**Bypass command (only if approved):**
```bash
git push --no-verify
```

**⚠️ CRITICAL:** NEVER bypass without showing user what was flagged and getting explicit approval.

---


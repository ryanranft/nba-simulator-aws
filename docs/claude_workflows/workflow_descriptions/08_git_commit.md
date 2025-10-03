## 🔒 Git Commit Workflow

**CRITICAL: ALWAYS follow security protocol before committing**

### Step 0: Automatic Command Log Sanitization (If COMMAND_LOG.md Staged)

**Triggered automatically by pre-commit hook when COMMAND_LOG.md is in staged files**

#### What Happens Automatically:

1. **Hook detects COMMAND_LOG.md** in `git diff --cached --name-only`
2. **Runs sanitization script:**
   ```bash
   bash scripts/shell/sanitize_command_log.sh
   ```
3. **Sanitizes 9 sensitive patterns:**

| Pattern | Sanitized To | Example |
|---------|--------------|---------|
| AWS Account IDs | `************` | `123456789012` → `************` |
| AWS Access Keys | `AWS_ACCESS_KEY****************` | `AKIAIOSFODNN7EXAMPLE` → `AWS_ACCESS_KEY****************` |
| AWS Secret Keys | `****************************************` | Full key → asterisks |
| GitHub Tokens | `ghp_************************************` | `ghp_1234...` → `ghp_****...` |
| IP Addresses | `xxx.xxx.xxx.xxx` | `192.168.1.1` → `xxx.xxx.xxx.xxx` |
| RDS Endpoints | `<database>.xxxxxxxxxx.<region>.rds.amazonaws.com` | Sanitizes instance ID |
| Database Passwords | `********` | Any password → asterisks |
| SSH Key Paths | `~/.ssh/` | Removes specific key names |
| Session Tokens | `AWS_SESSION_TOKEN***...` | Long tokens → truncated |

4. **Creates backup:** `COMMAND_LOG.md.backup` (in same directory)
5. **ABORTS commit** with message: "COMMAND_LOG.md has been sanitized. Please review and re-add."
6. **You review changes:**
   ```bash
   # Compare sanitized vs original
   diff COMMAND_LOG.md.backup COMMAND_LOG.md

   # If changes look correct
   git add COMMAND_LOG.md
   git commit  # Re-run commit
   ```

#### Manual Sanitization (Optional):

**Run script manually before staging:**
```bash
bash scripts/shell/sanitize_command_log.sh
```

**Review changes:**
```bash
diff COMMAND_LOG.md.backup COMMAND_LOG.md
```

**If satisfied with sanitization:**
```bash
git add COMMAND_LOG.md
# Proceed to commit
```

#### What Gets Sanitized:

✅ **Safe to commit after sanitization:**
- Command outputs with redacted credentials
- AWS CLI responses with masked IDs
- Error messages with sanitized paths
- Log entries with removed IPs

❌ **Still review manually:**
- Comments you added (may contain context about secrets)
- File paths that might reveal architecture
- Custom notes about configuration

#### When Sanitization Fails:

**If script reports errors:**
1. Check `COMMAND_LOG.md` for syntax issues
2. Verify backup exists: `ls -la COMMAND_LOG.md.backup`
3. Manually review and fix issues
4. Re-run sanitization script

**Emergency restore:**
```bash
cp COMMAND_LOG.md.backup COMMAND_LOG.md
```

### 1. Run Security Scan (AUTOMATIC - Don't Skip)
See `docs/SECURITY_PROTOCOLS.md` for complete bash commands

**Key checks:**
- Staged files for AWS keys, secrets, passwords, IPs
- Commit message for sensitive data
- **Note:** This runs AFTER sanitization (Step 0) to catch any remaining issues

### 2. If Security Scan Flags Anything
**STOP immediately:**
- Save diff to temp file
- Show user ALL flagged lines with context
- Explain what was detected (false positive vs real secret)
- Explain if deletions (safe) or additions (review needed)
- Ask explicitly: "Do you approve bypassing pre-commit hook? [YES/NO]"
- Wait for explicit YES or NO

### 3. If Scan Passes or User Approves
Stage files and commit:
```bash
git add .
git commit -m "$(cat <<'EOF'
Brief description of changes

Detailed explanation if needed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 4. After Commit - Update Session History
```bash
bash scripts/shell/session_manager.sh start >> .session-history.md
```
Creates version snapshot for this commit

### 4.5. Check Chat Log Before Archiving (OPTIONAL - Pre-Archive Verification)

**Purpose:** Verify CHAT_LOG.md exists and check freshness before archiving conversation

**When to use:**
- Before running Step 5 (archive_chat_by_next_sha.sh)
- When uncertain if conversation was exported recently
- To verify chat log is ready for archiving

**Script:** `scripts/shell/check_chat_log.sh`

**Usage:**
```bash
bash scripts/shell/check_chat_log.sh
```

**What this does (4 checks):**

#### Check 1: File Existence
```bash
if [ -f "CHAT_LOG.md" ]; then
  echo "✓ CHAT_LOG.md exists"
else
  echo "⚠️  CHAT_LOG.md not found"
fi
```

#### Check 2: File Age Calculation
```bash
# Calculate time since last modification
file_age_seconds=$(( $(date +%s) - $(stat -f %m CHAT_LOG.md) ))
file_age_minutes=$(( file_age_seconds / 60 ))
file_age_hours=$(( file_age_minutes / 60 ))
file_age_days=$(( file_age_hours / 24 ))
```

#### Check 3: Freshness Assessment
**Color-coded age warnings:**
| Age | Color | Message |
|-----|-------|---------|
| < 1 hour | Green | "Last updated: X minutes ago" |
| 1-24 hours | Green | "Last updated: X hours ago" |
| > 24 hours | Yellow | "Last updated: X days ago" + "⚠️  Chat log may be stale" |

#### Check 4: Archive Location Reminder
```bash
echo "✓ Ready for commit"
echo ""
echo "The pre-commit hook will archive this to:"
echo "~/sports-simulator-archives/nba/<commit-hash>/CHAT_LOG_*.md"
```

**Sample Output (Recent Chat Log):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 CHAT LOG CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ CHAT_LOG.md exists

  File size: 45K
  Last updated: 12 minutes ago

✓ Ready for commit

  The pre-commit hook will archive this to:
  ~/sports-simulator-archives/nba/<commit-hash>/CHAT_LOG_*.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Sample Output (Stale Chat Log):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 CHAT LOG CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ CHAT_LOG.md exists

  File size: 23K
  Last updated: 3 days ago

⚠️  Chat log may be stale
   Consider exporting your latest Claude Code conversation

✓ Ready for commit

  The pre-commit hook will archive this to:
  ~/sports-simulator-archives/nba/<commit-hash>/CHAT_LOG_*.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Sample Output (Missing Chat Log):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 CHAT LOG CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  CHAT_LOG.md not found

  This commit will proceed without conversation context.

  To preserve Claude Code conversations:
  1. Export conversation from Claude Code
  2. Save as: CHAT_LOG.md in project root
  3. Re-run this check before committing

💡 Tip: Export conversations after significant work sessions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**What Gets Checked:**
- ✅ File existence (`CHAT_LOG.md` in project root)
- ✅ File size (human-readable format)
- ✅ Last modification time (minutes/hours/days ago)
- ✅ Staleness warning (if > 24 hours old)
- ✅ Archive destination reminder

**Decision Tree After Check:**

```
CHAT_LOG.md exists and recent (<24 hours)?
├─ YES → Proceed to Step 5 (archive_chat_by_next_sha.sh)
└─ NO
   ├─ File missing?
   │  ├─ Export conversation from Claude Code
   │  ├─ Save as CHAT_LOG.md
   │  └─ Re-run check_chat_log.sh
   └─ File stale (>24 hours)?
      ├─ Option A: Export fresh conversation and replace CHAT_LOG.md
      └─ Option B: Accept stale version and proceed to Step 5
```

**Integration Points:**
- **Session End Workflow:** Run before commit to verify conversation is captured
- **Git Commit Workflow Step 4.5:** Pre-archive verification (this location)
- **Archive Workflow Prerequisite:** Verify CHAT_LOG.md before archiving

**Comparison to Related Scripts:**

| Feature | check_chat_log.sh | save_conversation.sh | archive_chat_by_next_sha.sh |
|---------|-------------------|----------------------|-----------------------------|
| **Purpose** | Verify chat log exists/fresh | Prompt Claude to save | Archive conversation by SHA |
| **Checks existence** | ✅ YES | ❌ NO | ✅ YES (aborts if missing) |
| **Checks freshness** | ✅ YES (age warnings) | ❌ NO | ❌ NO |
| **Writes files** | ❌ NO (read-only) | ❌ NO (prompts Claude) | ✅ YES (4 archive files) |
| **User action** | Informational check | Triggers conversation save | Archives existing chat log |
| **When to use** | Before archiving | During session (save now) | After commit (link to SHA) |

**Best Practice Workflow:**

```bash
# 1. Complete significant work
# 2. Save conversation (if not already saved)
bash scripts/shell/save_conversation.sh
# (Claude writes CHAT_LOG.md)

# 3. Commit changes
git add .
git commit -m "Implement feature X"

# 4. Check chat log before archiving
bash scripts/shell/check_chat_log.sh
# ✓ CHAT_LOG.md exists
# ✓ File size: 45K
# ✓ Last updated: 2 minutes ago

# 5. Archive conversation linked to commit
bash scripts/maintenance/archive_chat_by_next_sha.sh
# Creates 4 files:
#   - chat-<SHA>-original.md
#   - chat-<SHA>-sanitized.md
#   - chat-<SHA>-spoofed.md
#   - mapping-<SHA>.txt
```

**Why This Step is Optional:**

The check is informational only - `archive_chat_by_next_sha.sh` (Step 5) will abort if CHAT_LOG.md is missing, so this verification step helps catch issues earlier but isn't strictly required.

Use this step when:
- ✅ Want to verify freshness before archiving
- ✅ Uncertain if conversation was exported recently
- ✅ Multiple sessions worked on same commit
- ✅ Debugging why archiving failed

Skip this step when:
- ⏭️ Just saved conversation (know it's fresh)
- ⏭️ Confident CHAT_LOG.md exists and is current
- ⏭️ Not planning to archive (routine commits)

### 5. Archive Conversation by Commit SHA (OPTIONAL - If CHAT_LOG.md Exists)

**Purpose:** Archive conversation linked to specific commit, creating 3 security-level versions with optional GitHub publishing

**When to use:**
- After completing significant feature/phase with valuable conversation
- Want conversation explicitly linked to specific commit SHA
- Planning to publish sanitized or spoofed conversation publicly

**Script:** `scripts/maintenance/archive_chat_by_next_sha.sh`

**Prerequisites:**
1. CHAT_LOG.md exists in project root (written by Claude or via `save_conversation.sh`)
2. Changes already committed (script uses current HEAD SHA)

**Usage:**
```bash
# After commit, archive conversation linked to that commit
bash scripts/maintenance/archive_chat_by_next_sha.sh
```

**What this does (7 steps):**

#### Step 1: Detect Current Commit
```bash
CURRENT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)
COMMIT_DATE=$(git log -1 --format=%cd --date=iso)
```

#### Step 2: Check for CHAT_LOG.md
```bash
if [ ! -f "$PROJECT_DIR/CHAT_LOG.md" ]; then
    echo "❌ No CHAT_LOG.md found"
    echo "Export conversation first, then run this script"
    exit 1
fi
```

#### Step 3: Create ORIGINAL Archive
```bash
# Archive location: ~/sports-simulator-archives/nba/conversations/
# Filename: chat-<FULL_SHA>-original.md

# Adds header with:
# - Full SHA
# - Commit date
# - Author
# - Commit message
# - Full conversation content
```

**Example ORIGINAL archive header:**
```markdown
# Conversation Archive: Commit abc1234

**Full SHA:** abc1234567890abcdef1234567890abcdef1234
**Date:** 2025-10-02 19:30:45 -0700
**Author:** Developer Name <email@example.com>

## Commit Message

```
Add weekly documentation update workflow

Integrated update_docs.sh script with 7 automated steps...

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Conversation

This conversation captures the work that led to the above commit.

---

[Full conversation follows...]
```

#### Step 4: Create SANITIZED Version
**Redacts credentials only (keeps real paths):**

| Pattern | Redacted To |
|---------|-------------|
| `AWS_ACCESS_KEY[A-Z0-9]{16}` | `AWS_ACCESS_KEY[REDACTED]` |
| `aws_secret_access_key=...` | `aws_secret_access_key=[REDACTED]` |
| `aws_session_token=...` | `aws_session_token=[REDACTED]` |
| `Password: <value>` | `Password: [REDACTED]` |
| `Bearer <token>` | `Bearer [REDACTED]` |
| `ghp_<36chars>` | `ghp_[REDACTED]` |
| `github_pat_<token>` | `github_pat_[REDACTED]` |
| `postgresql://user:pass@` | `postgresql://[USER]:[REDACTED]@` |
| `postgres:pass@` | `postgres:[REDACTED]@` |

**Output:** `chat-<SHA>-sanitized.md` (safe for private repos)

#### Step 5: Create SPOOFED Version
**Generates fake paths for public sharing:**

**Path transformations:**
```python
# Real paths → Spoofed paths
/Users/ryanranft/nba-simulator-aws/scripts/shell/update_docs.sh
  → project/scripts/script_a3f2b891.sh

~/sports-simulator-archives/nba/conversations/chat_20251002.md
  → /archive/external/doc_f72a89bc.md

CLAUDE.md
  → project/doc_e4b1c332.md
```

**Content transformations:**
| Real | Spoofed |
|------|---------|
| `/Users/ryanranft/` | `/Users/developer/` |
| `~/` | `/Users/developer/` |
| `<email@domain.com>` | `<developer@example.com>` |
| `Author: Real Name` | `Author: Developer` |
| `nba-simulator-aws` | `sports-data-pipeline` |
| `nba-sim-raw-data-lake` | `sports-raw-data-bucket` |
| `nba` / `NBA` | `sport` / `SPORT` |

**Output:** `chat-<SHA>-spoofed.md` (safe for public sharing)

#### Step 6: Create Path Mapping File
**For reversing spoofed paths back to real:**

```
# Path Mapping for Commit abc1234
# Created: chat-abc1234-sanitized.md
#
# REAL PATH → SPOOFED PATH
#
# SECURITY: This file contains real paths - NEVER commit to git!
# Location: ~/sports-simulator-archives/nba/conversations/mappings/mapping-abc1234.txt
#======================================================================

/Users/ryanranft/nba-simulator-aws/CLAUDE.md
  → project/doc_e4b1c332.md

/Users/ryanranft/nba-simulator-aws/scripts/shell/update_docs.sh
  → project/scripts/script_a3f2b891.sh

~/sports-simulator-archives/nba/conversations/chat_20251002.md
  → /archive/external/doc_f72a89bc.md

Total paths spoofed: 47
```

**⚠️ NEVER commit mapping file - contains real paths!**

#### Step 7: Optional GitHub Publishing
**Prompts to publish SPOOFED version to public GitHub repo:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 PUBLISH TO GITHUB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Publish spoofed conversation to public GitHub repo? [y/N]: y

  📤 Publishing spoofed conversation to GitHub...
  ✅ Published to: https://github.com/ryanranft/nba-simulator-conversations
  📄 View file: https://github.com/.../chat-abc1234-spoofed.md
```

**If yes:**
- Commits spoofed file to archive repo
- Includes commit message with link to main repo commit
- Pushes to GitHub automatically

**If no:**
- Provides manual publish commands
- Files remain local-only

**Script output summary:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 ARCHIVING CONVERSATION FOR COMMIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Commit: abc1234
Date:   2025-10-02 19:30:45 -0700
Author: Developer Name <email@example.com>

Message:
  Add weekly documentation update workflow

  Integrated update_docs.sh script with 7 automated steps...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📝 Creating archive for SHA: abc1234
  🔒 Creating sanitized version...
  🎭 Creating spoofed version (public-safe)...
Spoofed 47 file paths

✅ Conversation archived successfully!

📂 Files created:
   Original:  ~/sports-simulator-archives/nba/conversations/chat-abc1234...-original.md
   Sanitized: ~/sports-simulator-archives/nba/conversations/chat-abc1234...-sanitized.md
   Spoofed:   ~/sports-simulator-archives/nba/conversations/chat-abc1234...-spoofed.md
   Mapping:   ~/sports-simulator-archives/nba/conversations/mappings/mapping-abc1234....txt

⚠️  Security Note:
   - ORIGINAL: Contains passwords - keep local only
   - SANITIZED: Safe to share or commit to private repo
   - SPOOFED: Safe to share publicly (fake paths, no credentials)
   - MAPPING: Real→Spoofed paths - NEVER commit (local only)

💡 You can now delete CHAT_LOG.md from the project root:
   rm /Users/ryanranft/nba-simulator-aws/CHAT_LOG.md

🔍 To view conversations:
   less ~/sports-simulator-archives/nba/conversations/chat-abc1234...-sanitized.md
   less ~/sports-simulator-archives/nba/conversations/chat-abc1234...-spoofed.md

📋 Archive Index:
   Total conversations archived: 12
```

**Archive file naming convention:**
```
chat-<FULL_40_CHAR_SHA>-original.md
chat-<FULL_40_CHAR_SHA>-sanitized.md
chat-<FULL_40_CHAR_SHA>-spoofed.md
mapping-<FULL_40_CHAR_SHA>.txt
```

**Finding archived conversation by commit:**
```bash
# By short SHA
ls ~/sports-simulator-archives/nba/conversations/chat-abc1234*

# By commit message keyword
grep -l "documentation update" ~/sports-simulator-archives/nba/conversations/*.md

# View specific version
less ~/sports-simulator-archives/nba/conversations/chat-<SHA>-sanitized.md
```

**Security comparison:**

| Version | Real Paths? | Credentials? | Safe for Private Repo? | Safe for Public? |
|---------|-------------|--------------|------------------------|------------------|
| **ORIGINAL** | ✅ YES | ✅ YES | ❌ NO | ❌ NO |
| **SANITIZED** | ✅ YES | ❌ NO | ✅ YES | ❌ NO |
| **SPOOFED** | ❌ NO (fake) | ❌ NO | ✅ YES | ✅ YES |
| **MAPPING** | ✅ YES | ❌ NO | ❌ NO | ❌ NO |

**Best practices:**
1. ✅ Use SANITIZED for team collaboration (private repos)
2. ✅ Use SPOOFED for portfolios, presentations, public demos
3. ✅ Keep ORIGINAL and MAPPING local-only (never push to GitHub)
4. ✅ Run after commits you want publicly documented
5. ✅ Delete CHAT_LOG.md after archiving (prevent accidental commit)

**Comparison to archive_manager.sh conversation mode:**

| Feature | archive_manager.sh | archive_chat_by_next_sha.sh |
|---------|-------------------|----------------------------|
| **Trigger** | Manual/automatic | Manual after commit |
| **Naming** | Timestamp-based | Commit SHA-based |
| **Filename** | `CHAT_LOG_<timestamp>.md` | `chat-<SHA>-<version>.md` |
| **Versions** | 3 (ORIGINAL/SANITIZED/SPOOFED) | 3 (ORIGINAL/SANITIZED/SPOOFED) |
| **Path mapping** | No | Yes (separate mapping file) |
| **GitHub publish** | No | Yes (interactive prompt) |
| **Commit linkage** | None | Explicit SHA linkage |
| **Use case** | General archiving | Commit-specific documentation |

**When to use each:**

**Use `archive_manager.sh conversation`:**
- ✅ During session at 75%/90% context
- ✅ Session end with uncommitted work
- ✅ General conversation preservation

**Use `archive_chat_by_next_sha.sh`:**
- ✅ After significant feature commit
- ✅ Want conversation linked to specific commit
- ✅ Planning to publish publicly
- ✅ Need path mapping for reconstruction

### 6. Archive Management (RECOMMENDED - Run After Every Commit)

**Purpose:** Preserve operational files and conversations for each commit in dedicated archive repository

```bash
bash scripts/maintenance/archive_manager.sh full
```

**See complete Archive Management Workflow below for detailed usage**

---


# Archive Protocols

This document contains all procedures for archiving files, managing deletions, and maintaining conversation history.

## File Deletion Protocol (CRITICAL)

Before removing ANY file from git tracking, ALWAYS archive it first:

### 1. Create Pre-Deletion Archive

```bash
ARCHIVE_DIR=~/sports-simulator-archives/nba/pre-deletion-archive-$(date +%Y%m%d)
mkdir -p "$ARCHIVE_DIR"
cp <files-to-delete> "$ARCHIVE_DIR/"
```

### 2. Create Deletion Record

Document what files were removed, why, and when:
- Include how to access them in future (git history, archive location)
- Explain purpose for future sport simulator deployments

### 3. Commit Archive to Local Git

```bash
cd ~/sports-simulator-archives/nba
git add pre-deletion-archive-*/
git commit -m "Archive files before GitHub removal - preserve complete history"
```

### 4. Remove from Git Tracking (Keep Local)

```bash
git rm --cached <files-to-delete>
```

### 5. Update .gitignore to Prevent Re-Tracking

Add removed files to `.gitignore` to prevent accidental re-staging.

## Why This Matters

- Future sport simulators need complete deployment history with errors
- Shows what operational files were created and why they were removed
- Preserves lessons learned and mistake patterns
- Enables replication of successful approaches

## File Preservation Layers

Each deleted file is preserved in **FOUR** locations:

### 1. Pre-Deletion Archive

`~/sports-simulator-archives/nba/pre-deletion-archive-YYYYMMDD/`
- Timestamped snapshot of files before removal
- Includes DELETION_RECORD.md with full context

### 2. GitHub History (Until Deletion Commit)

- `git show <old-commit>:FILENAME`
- Accessible from any commit before removal

### 3. Local Archive Git Repo

- `git -C ~/sports-simulator-archives/nba log --all -- FILENAME`
- `git -C ~/sports-simulator-archives/nba grep "keyword" -- pre-deletion-archive*/`

### 4. Local Working Directory

- Files still exist at original paths
- Archived automatically with each future commit
- Just not tracked by GitHub anymore

## Accessing Deleted Files

### Find When a File Was Deleted

```bash
git log --all --oneline -- FILENAME
```

### View File from Last Commit Before Deletion

```bash
git show <last-commit-sha>:FILENAME
```

### Search Pre-Deletion Archives

```bash
ls -la ~/sports-simulator-archives/nba/pre-deletion-archive-*/
```

### Read Deletion Record for Context

```bash
cat ~/sports-simulator-archives/nba/pre-deletion-archive-*/DELETION_RECORD.md
```

### Search Across All Deletion Archives via Git

```bash
git -C ~/sports-simulator-archives/nba grep "keyword" -- "pre-deletion-archive*/*"
```

## Integration with Post-Commit Workflow

The deletion process integrates seamlessly with existing automation:

1. **Pre-deletion archive created** → Manual step (before git rm)
2. **Files removed from GitHub** → `git rm --cached`
3. **User commits changes** → Normal commit process
4. **Post-commit hook triggers:**
   - Archives gitignored files (including deleted files still on disk)
   - Creates CHAT_LOG_SANITIZED.md
   - Generates ERRORS_LOG.md, CHANGES_SUMMARY.md, COMMAND_HISTORY.md
   - Commits everything to local archive git repo

**Result:** Complete historical record with zero GitHub exposure.

## Why This Matters for Future Sport Simulators

When deploying MLB, NFL, NHL, or other sport simulators, you can reference deleted files to:

- **See complete operational history:** What files were created during overnight automation, ETL processing, error logging
- **Learn from removal decisions:** Why certain files were kept local vs GitHub
- **Understand error patterns:** COMMAND_LOG.md shows every error encountered and how it was resolved
- **Replicate successful patterns:** Copy proven approaches from archived operational files
- **Avoid past mistakes:** See what didn't work and why it was removed

## Archive System Overview

- **Location:** `~/sports-simulator-archives/nba/` (local only, NEVER pushed to GitHub)
- **Storage Type:** Git-based with SHA-based directories
- **Compression:** ~85% space savings (2.7M total, .git only 388K)
- **Operation:** Fully automatic via post-commit hook
- **Content:** Gitignored docs + sanitized conversation logs + auto-generated logs
- **Git Repo:** Local only, no remote configured
- **Sensitive Files:** Tracked locally in git, excluded from remote via `.git/info/exclude`
- **Backup Recommendation:** Include archive directory in Time Machine or external backup system

## Auto-Generated Commit Logs

Each commit automatically generates detailed analysis logs in the archive directory:

### 1. ERRORS_LOG.md - All Errors Encountered

- Extracts from COMMAND_LOG.md and log files
- Shows error messages, tracebacks, warnings
- Links errors to specific commands/files

### 2. CHANGES_SUMMARY.md - Detailed File Changes Analysis

- Git diff stats and file-by-file breakdown
- Shows added/modified/deleted files
- Includes code diffs for each changed file

### 3. COMMAND_HISTORY.md - Complete Command Execution Record

- All commands from COMMAND_LOG.md
- Success/failure outcomes
- Timestamps and context

## Key Benefits

- ✅ Claude can read git history for ALL files (including sensitive ones)
- ✅ Full local version control with searchable history
- ✅ Auto-generated analysis of each commit's changes/errors
- ✅ Zero risk of GitHub leaks (`.git/info/exclude` blocks remote push)

## Conversation Archiving Workflow

### System Overview

This project automatically archives Claude conversations with each git commit, linking conversation history to code history. Each commit SHA gets its own archive directory containing the conversation that led to those code changes.

### The Automated Workflow

1. **Claude monitors context usage** during session (automatic)
2. **At 75% context (150K tokens)**, Claude automatically:
   - Writes verbatim conversation transcript to `CHAT_LOG.md`
   - Notifies user: "⚠️ Context at 75% - conversation saved to CHAT_LOG.md"
   - Suggests user commit soon to archive before context resets
3. **At 90% context (180K tokens)**, Claude:
   - Updates CHAT_LOG.md with latest exchanges
   - Strongly recommends immediate commit: "🚨 Context at 90% - commit NOW to preserve conversation"
4. **User commits:** `git commit -m "message"`
5. **Pre-commit hook** runs:
   - Checks if CHAT_LOG.md exists (should exist from auto-save)
   - Runs security scan (blocks if secrets detected)
6. **Commit creates new SHA** (e.g., abc123...)
7. **Post-commit hook** automatically:
   - Creates archive directory: `~/sports-simulator-archives/nba/abc123.../`
   - Archives CHAT_LOG.md → CHAT_LOG_ORIGINAL.md (with credentials)
   - Creates CHAT_LOG_SANITIZED.md (credentials redacted)
   - Generates auto-logs: ERRORS_LOG.md, CHANGES_SUMMARY.md, COMMAND_HISTORY.md
   - Clears CHAT_LOG.md (ready for next session)
8. **Archive git repo automatically commits:**
   - Archives committed to local git repo: `~/sports-simulator-archives/nba/.git`
   - Git tracks all changes to archived files (including sensitive files)
   - Automatic storage compression (~85% space savings)
   - **NEVER pushed to GitHub** - stays 100% local
   - `.git/info/exclude` prevents sensitive files from remote operations

### Manual Override

- User can say "save this conversation" anytime to trigger manual save
- Useful for important decision points or before ending session early

### Key Points

- ✅ Automatic conversation saving at 75% and 90% context thresholds
- ✅ Each commit SHA = one archive directory with conversation
- ✅ Automatic archiving (no manual script execution needed)
- ✅ Automatic clearing (prevents old conversations mixing)
- ✅ SHA-based searchable history (link conversation to code)
- ✅ Zero conversation loss - Claude monitors and saves proactively
- ✅ Git-based storage with automatic compression (~85% space savings)
- ✅ Full version history of archived documentation

### Context Monitoring Thresholds

- **0-74% (0-148K tokens):** Normal operation, no warnings
- **75-89% (150K-179K tokens):** 🟡 Auto-save triggered, commit suggested
- **90-100% (180K-200K tokens):** 🔴 Auto-update triggered, commit urgent
- **100%+ (>200K tokens):** Conversation will be truncated, data loss possible

## Finding Past Conversations

### Method 1: Using Directory Structure (Direct Access)

```bash
# Find commit by topic
git log --oneline --grep="authentication"
# Output: abc1234 Add user authentication

# Read conversation for that commit
cat ~/sports-simulator-archives/nba/abc1234*/CHAT_LOG_SANITIZED.md

# Search all conversations for keyword
grep -r "AWS error" ~/sports-simulator-archives/nba/*/CHAT_LOG_*.md
```

### Method 2: Using Git-Based Search (More Efficient)

```bash
# Search all archived conversations via git
git -C ~/sports-simulator-archives/nba grep "keyword" -- "*/CHAT_LOG_*.md"

# View archive git history
git -C ~/sports-simulator-archives/nba log --oneline

# Read specific archived file from git
git -C ~/sports-simulator-archives/nba show HEAD:<SHA>/CHAT_LOG_SANITIZED.md

# Search for when a file was added to archive
git -C ~/sports-simulator-archives/nba log --follow --oneline -- "*/<filename>"
```

## Claude's Role in Conversation Archiving

- ✅ Monitors context usage throughout session
- ✅ Automatically writes verbatim transcripts to CHAT_LOG.md at thresholds
- ✅ Can write transcript on-demand when user requests
- ✅ Can read archived conversations from `~/sports-simulator-archives/nba/<SHA>/`
- ✅ Proactively warns before conversation loss

### When Claude Auto-Saves

- At 75% context (150K tokens) - first automatic save
- At 90% context (180K tokens) - urgent update
- When user says "save this conversation" (manual trigger)
- Before context window truncation to prevent data loss

## Conversation Recovery (If Something Goes Wrong)

### If Conversation Wasn't Saved Before Commit

1. Check if CHAT_LOG.md exists: `ls -lh CHAT_LOG.md`
2. If empty, reconstruct from memory and save manually
3. Run: `bash scripts/maintenance/archive_chat_log.sh`

### If Context Truncated Before Save

1. What was lost: Oldest exchanges (beginning of conversation)
2. What's preserved: Recent exchanges (last ~50K tokens)
3. Write what you remember of early conversation to CHAT_LOG.md
4. Note at top: "⚠️ Partial conversation - context truncated"

### To Find Conversations Across Commits

```bash
# Search all archives for a keyword
grep -r "keyword" ~/sports-simulator-archives/nba/*/CHAT_LOG_SANITIZED.md

# List all archived conversations chronologically
ls -lt ~/sports-simulator-archives/nba/*/CHAT_LOG_SANITIZED.md
```

## Archive Management Commands

### View Archive Git History

```bash
git -C ~/sports-simulator-archives/nba log --oneline
```

### Search Archived Conversations

```bash
git -C ~/sports-simulator-archives/nba grep "keyword" -- "*/CHAT_LOG_*.md"
```

### Check Archive Storage Size

```bash
du -sh ~/sports-simulator-archives/nba
du -sh ~/sports-simulator-archives/nba/.git
```

### List All Archived Commits

```bash
ls -1 ~/sports-simulator-archives/nba/ | grep -E '^[0-9a-f]{40}$'
```
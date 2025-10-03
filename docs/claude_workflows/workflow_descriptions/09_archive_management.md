## 📦 Archive Management Workflow

**Unified archiving system for preserving operational files and conversations**

### When to Run

- ✅ **After every commit** (recommended: `full` mode)
- ✅ **Before session end** (if changes uncommitted)
- ✅ **At 90% context** (before losing conversation)
- ✅ **After significant work** (>2 hours)

### Available Modes

The `archive_manager.sh` script has 5 modes:

| Mode | Purpose | When to Use |
|------|---------|-------------|
| `gitignored` | Archive .gitignored operational files | After updating COMMAND_LOG.md, temp docs |
| `conversation` | Archive CHAT_LOG.md (3 versions) | At 75%/90% context, session end |
| `analyze` | Generate commit analysis logs | After major commits, debugging |
| `full` | Run all 3 modes in sequence | **RECOMMENDED** after every commit |
| `status` | Check archive status for commit | Verify archiving worked |

### Full Archive Workflow (Recommended)

**Step 1: Run Full Archive**

```bash
bash scripts/maintenance/archive_manager.sh full
```

**What this does:**

1. **Archives .gitignored operational files:**
   - `COMMAND_LOG.md` - Command history with outputs
   - `COMMIT_VERIFICATION.md` - Pre-commit verification results
   - `EXTRACTION_STATUS.md` - S3 data extraction status
   - `.session-history.md` - Session diagnostics snapshots
   - Any other files in `.gitignore` that are tracked locally

2. **Archives CHAT_LOG.md in 3 versions:**
   - **ORIGINAL:** `CHAT_LOG.md` - Full conversation with real paths/IPs
     - ⚠️ **Contains passwords/IPs** - local archive only, never push
   - **SANITIZED:** `CHAT_LOG_SANITIZED.md` - Credentials removed
     - ✅ **Safe for private GitHub repos** - team sharing OK
   - **SPOOFED:** `CHAT_LOG_SPOOFED.md` - Fake paths for demonstration
     - ✅ **Safe for public sharing** - portfolio/demos

3. **Generates commit analysis logs:**
   - `ERRORS_LOG.md` - All errors from COMMAND_LOG.md
   - `CHANGES_SUMMARY.md` - Git diff analysis, files changed
   - `COMMAND_HISTORY.md` - Extracted command-only list

4. **Commits to archive git repository:**
   - Archive location: `~/sports-simulator-archives/nba/<commit-SHA>/`
   - Archive repo: `~/sports-simulator-archives/nba/.git`
   - Each commit creates timestamped directory

**Step 2: Verify Archive Created**

```bash
bash scripts/maintenance/archive_manager.sh status
```

**Expected output:**
```
✅ Archive exists for commit <SHA>
📁 Location: ~/sports-simulator-archives/nba/<SHA>/
📄 Files archived: 8 files
📊 Total size: 2.4 MB
```

### Individual Mode Usage

#### Mode 1: Archive Gitignored Files Only

```bash
bash scripts/maintenance/archive_manager.sh gitignored
```

**Use when:**
- Updated COMMAND_LOG.md significantly
- Changed operational documentation
- Want to preserve temp files before cleanup

**What gets archived:**
- All files matching `.gitignore` patterns
- Preserves directory structure
- Creates timestamped snapshot

#### Mode 2: Archive Conversation Only

```bash
bash scripts/maintenance/archive_manager.sh conversation
```

**Use when:**
- Approaching context limits (75%/90%)
- Ending session with valuable conversation
- Want to preserve conversation without full archive

**Creates 3 versions:**
1. **ORIGINAL** - `~/sports-simulator-archives/nba/conversations/CHAT_LOG_<timestamp>.md`
   - Full conversation, real credentials/paths
   - **NEVER commit this version to GitHub**

2. **SANITIZED** - `~/sports-simulator-archives/nba/conversations/CHAT_LOG_SANITIZED_<timestamp>.md`
   - Credentials sanitized (AWS keys → asterisks)
   - IPs sanitized (192.168.1.1 → xxx.xxx.xxx.xxx)
   - File paths sanitized (removes sensitive info)
   - **Safe for private repo sharing**

3. **SPOOFED** - `~/sports-simulator-archives/nba/conversations/CHAT_LOG_SPOOFED_<timestamp>.md`
   - Fake project name, fake paths
   - Demonstrates workflow without exposing details
   - **Safe for public portfolio/presentations**

#### Mode 3: Analyze Commit Only

```bash
bash scripts/maintenance/archive_manager.sh analyze
```

**Use when:**
- Debugging errors from recent work
- Need quick command history review
- Want to extract error patterns

**Generates:**
- `ERRORS_LOG.md` - Grep for "error", "failed", "ERROR" in COMMAND_LOG.md
- `CHANGES_SUMMARY.md` - Git diff stats, changed files, additions/deletions
- `COMMAND_HISTORY.md` - All commands executed (no output, just commands)

### Archive Structure

```
~/sports-simulator-archives/nba/
├── <commit-SHA>/                    # Full archive for each commit
│   ├── COMMAND_LOG.md               # Operational command log
│   ├── COMMIT_VERIFICATION.md       # Pre-commit checks
│   ├── EXTRACTION_STATUS.md         # S3 extraction status
│   ├── .session-history.md          # Session diagnostics
│   ├── ERRORS_LOG.md                # Extracted errors
│   ├── CHANGES_SUMMARY.md           # Git diff analysis
│   └── COMMAND_HISTORY.md           # Command-only list
├── conversations/                   # Conversation archives
│   ├── CHAT_LOG_<timestamp>.md              # ORIGINAL (local only)
│   ├── CHAT_LOG_SANITIZED_<timestamp>.md    # SANITIZED (private repo OK)
│   └── CHAT_LOG_SPOOFED_<timestamp>.md      # SPOOFED (public OK)
├── backups/                         # make backup snapshots
│   └── backup-YYYYMMDD-HHMMSS/
├── deleted-files-*/                 # Pre-deletion archives
└── pre-push-cleanup-*/              # Pre-push removed files
```

### Archive Git Repository

**The archive is also a git repository:**

```bash
cd ~/sports-simulator-archives/nba
git log --oneline | head -20
```

**Benefits:**
- Track archive history over time
- Search conversations by commit message
- Recover conversations by SHA
- See evolution of operational files

### Finding Archived Conversations

**Method 1: By date**
```bash
ls -lt ~/sports-simulator-archives/nba/conversations/ | head -10
```

**Method 2: By commit SHA**
```bash
ls -lt ~/sports-simulator-archives/nba/ | grep <partial-SHA>
```

**Method 3: By content** (git grep in archive repo)
```bash
cd ~/sports-simulator-archives/nba
git grep "<keyword>" | head -20
```

**Method 4: By archive git history**
```bash
cd ~/sports-simulator-archives/nba
git log --all --grep="<keyword>" --oneline
```

### Emergency Recovery

**If CHAT_LOG.md lost before archiving:**

1. **Check if conversation archived:**
   ```bash
   bash scripts/maintenance/archive_manager.sh status
   ```

2. **If exists, copy from archive:**
   ```bash
   cp ~/sports-simulator-archives/nba/<SHA>/CHAT_LOG.md CHAT_LOG.md
   ```

3. **If not archived, check recent conversations:**
   ```bash
   ls -lt ~/sports-simulator-archives/nba/conversations/ | head -5
   cp ~/sports-simulator-archives/nba/conversations/CHAT_LOG_<recent>.md CHAT_LOG.md
   ```

### Security Notes

**⚠️ CRITICAL - 3 Versions, Different Security Levels:**

| Version | Contains Secrets? | Where to Store? | Safe for GitHub? |
|---------|------------------|-----------------|------------------|
| **ORIGINAL** | ✅ YES (real IPs, paths, maybe passwords) | Local archive only | ❌ NEVER |
| **SANITIZED** | ❌ NO (sanitized) | Private repos OK | ✅ Private only |
| **SPOOFED** | ❌ NO (fake data) | Anywhere | ✅ Public OK |

**Best practices:**
1. ✅ Keep ORIGINAL in `~/sports-simulator-archives/` (never commit)
2. ✅ Share SANITIZED with team in private repos
3. ✅ Use SPOOFED for portfolios, presentations, public demos
4. ❌ NEVER commit ORIGINAL to any repository

### Integration with Other Workflows

**Git Commit Workflow (Step 5):**
- After commit succeeds → Run `full` mode
- Preserves state for this commit

**Session End Workflow:**
- Before ending session → Check if conversation archived
- If not → Run `conversation` mode

**Context Management (At 90%):**
- Save conversation → Run `conversation` mode
- Archive before starting new conversation

### Component Scripts (Consolidated into archive_manager.sh)

**IMPORTANT:** `archive_manager.sh` is a **unified wrapper** that consolidates 4 original standalone scripts into a single convenient interface. The original scripts still exist for backwards compatibility and specific use cases, but **you should prefer `archive_manager.sh`** for all archiving tasks.

#### Original Component Scripts:

**1. `scripts/maintenance/archive_gitignored_files.sh`** (Standalone version of `gitignored` mode)
- **Purpose:** Archives .gitignored operational files to SHA-based directory
- **Creates:** `git-info.txt`, copies COMMAND_LOG.md, EXTRACTION_STATUS.md, log files
- **Use when:** Need ONLY gitignored file archiving (no conversation, no analysis)
- **Consolidated into:** `archive_manager.sh gitignored` mode

**Direct usage** (if not using archive_manager.sh):
```bash
bash scripts/maintenance/archive_gitignored_files.sh
```

**2. `scripts/maintenance/archive_chat_log.sh`** (Standalone version of `conversation` mode)
- **Purpose:** Archives CHAT_LOG.md in 2 versions (original + sanitized)
- **Creates:** `CHAT_LOG_ORIGINAL.md` (local only), `CHAT_LOG_SANITIZED.md` (safe for sharing)
- **Use when:** Need ONLY conversation archiving (no gitignored files, no analysis)
- **Consolidated into:** `archive_manager.sh conversation` mode

**Direct usage** (if not using archive_manager.sh):
```bash
bash scripts/maintenance/archive_chat_log.sh
```

**3. `scripts/maintenance/generate_commit_logs.sh`** (Standalone version of `analyze` mode)
- **Purpose:** Generates 3 analysis logs from COMMAND_LOG.md and git history
- **Creates:** `ERRORS_LOG.md`, `CHANGES_SUMMARY.md`, `COMMAND_HISTORY.md`
- **Use when:** Need ONLY commit analysis (no archiving)
- **Consolidated into:** `archive_manager.sh analyze` mode

**Direct usage** (if not using archive_manager.sh):
```bash
bash scripts/maintenance/generate_commit_logs.sh
```

**4. `scripts/maintenance/create_sanitized_archive.sh`** (Original sanitization utility)
- **Purpose:** Creates sanitized version of any markdown file (removes credentials)
- **Use when:** Need to sanitize a specific file (not part of full archive workflow)
- **Note:** Used internally by archive_manager.sh's `sanitize_credentials()` function

**Direct usage** (if sanitizing custom files):
```bash
bash scripts/maintenance/create_sanitized_archive.sh <input.md> <output.md>
```

#### Related Scripts (Not Consolidated):

**5. `scripts/maintenance/archive_chat_by_next_sha.sh`** (Alternative conversation workflow)
- **Purpose:** Archives conversation AFTER commit, naming by the NEW commit SHA
- **Creates:** 3 versions (original, sanitized, spoofed) + path mapping file
- **Use when:** Want conversation archived with the commit SHA it describes (instead of current SHA)
- **Different from `archive_manager.sh conversation`:** Creates 3rd "spoofed" version with fake paths for public sharing

**Usage:**
```bash
# 1. Export Claude Code conversation to CHAT_LOG.md
# 2. Stage and commit your changes
# 3. Run this script AFTER commit
bash scripts/maintenance/archive_chat_by_next_sha.sh
```

**Comparison:**

| Feature | archive_manager.sh conversation | archive_chat_by_next_sha.sh |
|---------|--------------------------------|----------------------------|
| **When to run** | Before or after commit | AFTER commit only |
| **SHA used** | Current commit SHA | Next commit SHA |
| **Versions created** | 2 (original, sanitized) | 3 (original, sanitized, spoofed) |
| **Path spoofing** | No | Yes (fake paths for public sharing) |
| **Mapping file** | No | Yes (maps real paths to spoofed paths) |
| **Public sharing** | Sanitized only | Spoofed version safe for public |

**Recommendation:**
- Use `archive_manager.sh conversation` for routine archiving after every commit
- Use `archive_chat_by_next_sha.sh` when creating public portfolio/demo materials

### Why Use archive_manager.sh Instead of Individual Scripts?

**Benefits of unified wrapper:**
1. **Single command:** Run all 3 archiving operations with `full` mode
2. **Consistent interface:** One script, 5 modes, clear naming
3. **Automatic git commits:** Commits to archive repo after each mode
4. **Status checking:** Built-in `status` mode to verify archiving succeeded
5. **Error handling:** Gracefully handles missing files, continues with warnings
6. **Shared functions:** DRY code, consistent sanitization logic

**When to use individual scripts:**
- **Debugging:** Need to test specific archiving step in isolation
- **Custom workflows:** Building your own archiving automation
- **Backwards compatibility:** Existing scripts/aliases reference old script names
- **Special cases:** Need only one specific operation without others

**Example scenarios:**

**Scenario 1: After every commit (recommended)**
```bash
# Single command archives everything
bash scripts/maintenance/archive_manager.sh full
```

**Scenario 2: Quick conversation save at 90% context**
```bash
# Just archive conversation, skip gitignored files and analysis
bash scripts/maintenance/archive_manager.sh conversation
```

**Scenario 3: Debugging errors from yesterday's work**
```bash
# Generate analysis logs only (assumes archive already exists)
bash scripts/maintenance/archive_manager.sh analyze
```

**Scenario 4: Creating public demo (advanced)**
```bash
# Use standalone script for spoofed version + mapping
bash scripts/maintenance/archive_chat_by_next_sha.sh
```

---


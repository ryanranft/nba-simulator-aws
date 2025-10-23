## 🎯 Session End Workflow

**Purpose:** Comprehensive checklist to ensure work is saved, documented, and ready for next session

**When to use:** Before closing Claude Code session after any significant work

### Automated Session End Checklist (Recommended)

**Script:** `scripts/shell/session_end.sh`

**Usage:**
```bash
bash scripts/shell/session_end.sh
```

**What this does (5-part checklist):**

#### Part 1: Git Status Check

**Checks for uncommitted changes:**
```bash
git status --porcelain
```

**Output if changes exist:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 1. GIT STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  You have uncommitted changes:

 M CLAUDE.md
 M docs/CLAUDE_WORKFLOW_ORDER.md
 M scripts/shell/session_end.sh
   ... (15 total files changed)

💡 Consider:
   - Review changes: git diff
   - Commit work: git add . && git commit
   - Or stash: git stash save "WIP: session end 2025-10-02"
```

**Output if clean:**
```
✓ No uncommitted changes
```

#### Part 2: Claude Code Conversation Check

**Checks if CHAT_LOG.md exists and freshness:**

**Scenario A: CHAT_LOG.md exists and recent (<1 hour)**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 2. CLAUDE CODE CONVERSATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ CHAT_LOG.md exists (updated 12 minutes ago)

💡 Workflow:
   1. Commit your changes: git add . && git commit -m 'message'
   2. Archive conversation: bash scripts/maintenance/archive_chat_by_next_sha.sh
   3. This saves the chat with the commit SHA it produced
```

**Scenario B: CHAT_LOG.md exists but stale (>1 hour)**
```
⚠️  CHAT_LOG.md is 5 hours old

📝 ACTION NEEDED:
   1. Export your latest Claude Code conversation
   2. Save/overwrite as: CHAT_LOG.md
   3. Commit changes, then archive conversation
```

**Scenario C: CHAT_LOG.md missing**
```
⚠️  CHAT_LOG.md not found

📝 RECOMMENDED WORKFLOW:
   1. Export Claude Code conversation → Save as CHAT_LOG.md
   2. Stage and commit changes → git add . && git commit
   3. Archive conversation → bash scripts/maintenance/archive_chat_by_next_sha.sh
   4. This saves chat as: chat-<SHA>-sanitized.md

💡 Why this matters:
   - Each conversation linked to the commit it produced
   - Future LLMs can trace: 'What work led to commit X?'
   - Preserves full context for reproducing this pipeline
   - Archive: ~/sports-simulator-archives/nba/conversations/
```

#### Part 3: Documentation Status Check

**Checks 3 key documentation files:**

1. **COMMAND_LOG.md** - Updated today?
2. **PROGRESS.md** - Updated today?
3. **FILE_INVENTORY.md** - Updated within 7 days?

**Sample output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 3. DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ COMMAND_LOG.md updated today
✓ PROGRESS.md updated today
⚠️  FILE_INVENTORY.md is 9 days old (consider: make inventory)

💡 Consider updating documentation before next session
```

#### Part 4: DIMS (Data Inventory Management System)

**Automatically verifies and updates project metrics:**

**What DIMS does at session end:**
- Verifies all 25 project metrics (S3, code, docs, tests, etc.)
- Auto-updates any metrics with drift from baseline
- Saves updated metrics to `inventory/metrics.yaml`
- Creates daily snapshot in `inventory/historical/`

**Sample output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 4. DATA INVENTORY (DIMS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verifying and updating project metrics...
✓ DIMS metrics updated

OR (if drift detected):

Verifying and updating project metrics...
⚠️  3 metrics drifted:
  - s3_storage.total_objects: 172,726 → 174,891 (+1.3%)
  - code_base.python_files: 1,308 → 1,315 (+0.5%)
  - documentation.markdown_files: 1,719 → 1,720 (+0.1%)
✓ DIMS metrics updated (3 metrics refreshed)
```

**Manual operations (if needed):**
```bash
# View full drift report
python scripts/monitoring/dims_cli.py verify

# Force update all metrics
python scripts/monitoring/dims_cli.py update

# See complete documentation
# Workflow #56: docs/claude_workflows/workflow_descriptions/56_dims_management.md
```

#### Part 5: Next Session Preview

**Shows next pending task from PROGRESS.md:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 5. NEXT SESSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next pending task in PROGRESS.md:
  ⏸️ Phase 2.2: Create year-based Glue Crawlers for manageable data...

╔═══════════════════════════════════════════════════════════════╗
║  ✓ Session end checklist complete                            ║
╚═══════════════════════════════════════════════════════════════╝

👋 Session ended at 2025-10-02 19:45:23
```

### Manual Session End Checklist (Alternative)

**If session_end.sh not available, manually check:**

**1. Git Status:**
```bash
git status
```
- ✅ Commit work or stash if needed

**2. Conversation Export:**
- ✅ Export Claude Code conversation to CHAT_LOG.md
- ✅ Check freshness: `ls -lh CHAT_LOG.md`

**3. Documentation:**
```bash
# Check if files modified today
ls -lt COMMAND_LOG.md PROGRESS.md FILE_INVENTORY.md
```
- ✅ Update COMMAND_LOG.md if needed
- ✅ Update PROGRESS.md if tasks completed
- ✅ Run `make inventory` if files changed

**4. Next Session:**
- ✅ Review next pending task in PROGRESS.md
- ✅ Note any blockers or prerequisites

### Shell Alias for Quick Access

**Add to ~/.bashrc or ~/.zshrc:**
```bash
alias end-session='bash /Users/ryanranft/nba-simulator-aws/scripts/shell/session_end.sh'
```

**Then simply run:**
```bash
end-session
```

### Integration with Other Workflows

**Session End Workflow integrates with:**
- **Git Commit Workflow:** Checks for uncommitted changes before ending
- **Archive Management:** Prompts to archive CHAT_LOG.md after commit
- **Context Management:** Ensures conversation saved before ending session
- **Session Start Workflow:** Shows next pending task for continuity

### Best Practices

1. ✅ **Run before every session end** (even short sessions)
2. ✅ **Always export conversation** if significant work done (>30 min)
3. ✅ **Commit changes** before ending session (avoid WIP accumulation)
4. ✅ **Archive conversation** after commit (links chat to specific SHA)
5. ✅ **Review next task** to prepare for next session

### What Gets Checked

| Check | File/Command | Warning If | Action |
|-------|--------------|------------|--------|
| **Git Status** | `git status --porcelain` | Uncommitted changes exist | Commit or stash |
| **Conversation** | `CHAT_LOG.md` age | Missing or >1 hour old | Export conversation |
| **Command Log** | `COMMAND_LOG.md` date | Not updated today | Review session commands |
| **Progress** | `PROGRESS.md` date | Not updated today | Update task status |
| **Inventory** | `FILE_INVENTORY.md` age | >7 days old | Run `make inventory` |
| **Next Task** | `grep ⏸️ PROGRESS.md` | None | Review PROGRESS.md |

### Troubleshooting

**Script not found:**
```bash
# Verify script exists
ls -l scripts/shell/session_end.sh

# If missing, check git status
git status scripts/shell/session_end.sh

# Restore if needed
git checkout scripts/shell/session_end.sh
```

**CHAT_LOG.md detection issues:**
```bash
# Check if file exists
ls -lh CHAT_LOG.md

# Check last modification time (macOS)
stat -f %m CHAT_LOG.md

# Check last modification time (Linux)
stat -c %Y CHAT_LOG.md
```

**Documentation date checks failing:**
```bash
# Manually check when files last modified
ls -lt COMMAND_LOG.md PROGRESS.md FILE_INVENTORY.md

# Update if needed
make inventory          # Updates FILE_INVENTORY.md
make update-docs        # Updates all documentation
```

### Claude's Session End Reminders (Manual)

**If script not used, Claude should remind user:**
- ✅ "COMMAND_LOG.md modified - review for sensitive data before committing"
- ✅ "Multiple files changed - consider running `make backup`"
- ✅ "Documentation changed - consider running `make inventory`"
- ✅ "Phase complete - update PROGRESS.md status to ✅ COMPLETE and run `make sync-progress`"
- ✅ "Conversation not saved - export to CHAT_LOG.md before ending session"

---


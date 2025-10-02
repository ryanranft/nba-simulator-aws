# Claude Session Initialization - Detailed Procedures

This file contains the complete session initialization procedures that Claude follows at the start of each session.

## Session Initialization (Proactive)

### 1. Always Run at Start of Each Session

**Credentials:** Auto-loaded from ~/.zshrc when entering project directory (no verification needed)

**Startup checklist** - Automatically run (don't ask user, just do it):

```bash
source scripts/shell/session_manager.sh start
```

**What it checks:**
- Hardware: Model, Chip, Cores, Memory
- System: macOS version, Homebrew version and location
- Conda: Version, base path, active environment
- Python: Version, location, key packages (boto3, pandas, numpy) with install paths
- AWS CLI: Version and location
- Git: Version, location, status (branch, modified/untracked files), recent commits
- **Documentation status:** FILE_INVENTORY.md age, session history, command log, PROGRESS.md tasks, stale docs
- **Conversation logging:** Offers terminal session logging setup
- **Command logging:** Auto-sources log_command.sh functions

**Output format:** Clean, organized sections with all diagnostic details preserved

**Session start:** Show output to user for review

**After EVERY commit:** Append to `.session-history.md` with:
```bash
bash scripts/shell/session_manager.sh start >> .session-history.md
```
This creates a version snapshot for each commit, allowing user to correlate git history with exact software versions used

**Check conversation status:**
- If CHAT_LOG.md exists and is stale (>30 min): Remind user it will be overwritten at 75% context
- If context approaching 75%: Proactively mention auto-save is coming soon
- CHAT_LOG.md is auto-managed - no user action needed

**Initial orientation:**
- Identify current phase from PROGRESS.md
- Review documentation status warnings from `session_manager.sh start` output
- Ask: "Any work completed since last session that should be marked ✅ COMPLETE in PROGRESS.md?"

### 2. Ask User If They Want to Run (Based on Time Since Last Update)

- If Monday or 7+ days since last update: "Would you like me to run `make update-docs` for weekly maintenance?"
- If 7+ days since last inventory: "Should I run `make inventory` to update file summaries?"
- If new AWS resources may exist: "Should I run `make sync-progress` to check if PROGRESS.md matches AWS?"
- If any .md files modified: "After these changes, should I run `make inventory` to update FILE_INVENTORY.md?"

### 3. File Inventory & Documentation (CRITICAL - Do Automatically)

**ALWAYS update FILE_INVENTORY.md when creating/modifying files:**

- **Before `git add .`:** Run `make inventory` to update FILE_INVENTORY.md with new/changed files
- **After running `make inventory`:** Review git diff to see what files changed, then document:
  - **What you created/modified:** List each file path
  - **Why you made the change:** Purpose and problem being solved
  - **What error you were resolving:** If fixing a bug, document the error

**Format for documentation:**

```markdown
## File Changes - [Date] [Brief Description]

**Files Created/Modified:**
- `path/to/file1.py` - Purpose: Created X function to solve Y problem
- `path/to/file2.md` - Purpose: Documented Z decision (ADR-00X)
- `scripts/shell/file3.sh` - Purpose: Automated W task

**Problem/Error Being Resolved:**
- Error message: [actual error if applicable]
- Root cause: [why it was happening]
- Solution approach: [how files address it]

**Changes Made:**
1. File1: Added/modified X (lines 10-50)
2. File2: Updated Y section with Z information
3. File3: Created new script to automate W
```

**Where to document:** Add to COMMAND_LOG.md (for code changes) and ensure FILE_INVENTORY.md is updated

**Workflow:**
1. Create/modify files
2. Run `make inventory` (updates FILE_INVENTORY.md automatically)
3. Run `git status` to see all changes
4. Document in COMMAND_LOG.md what you changed and why
5. Then `git add .` and commit

### 4. Check for Stale Documentation Needing Manual Updates

**PROGRESS.md Phase Status:** If current phase completed but still shows ⏸️ PENDING → suggest updating status to ✅ COMPLETE

**PROGRESS.md Cost Estimates:** After creating AWS resources → ask "Should I run `make check-costs` and update PROGRESS.md with actual costs?"

**TROUBLESHOOTING.md:** After solving new error → ask "Should I add this solution to TROUBLESHOOTING.md?"

**When to add to TROUBLESHOOTING.md:**
- ✅ Errors that took >10 minutes to solve
- ✅ Non-obvious solutions (wouldn't find with quick Google search)
- ✅ Environment-specific issues (conda, AWS, macOS-specific)
- ✅ Recurring errors (seen multiple times in session)
- ✅ Errors with misleading messages (actual cause different from error text)

**When NOT to add:**
- ❌ Typos or syntax errors (obvious from error message)
- ❌ One-time issues (unlikely to recur)
- ❌ Already documented in official docs

**ADRs:** After architectural decision → ask "Should I create ADR-00X for this decision? (see docs/adr/template.md)"

**When to create ADRs:**
- ✅ Significant architectural decisions (database choice, service selection, framework adoption)
- ✅ Technology choices with long-term impact (Python version, AWS service vs self-hosted)
- ✅ Major trade-offs (cost vs performance, simplicity vs scalability, storage vs compute)
- ✅ Decisions affecting multiple parts of system (authentication method, logging strategy, error handling)
- ✅ Rejecting common approaches (why NOT using X, why avoiding Y)
- ✅ Development workflow changes (build process, deployment strategy, testing approach)

**When NOT to create ADRs:**
- ❌ Small implementation details (variable naming, file organization)
- ❌ Temporary workarounds (quick fixes, patches)
- ❌ Obvious choices with no alternatives (using JSON for config, Git for version control)
- ❌ Easily reversible decisions with no consequences (UI colors, log message format)

**QUICKSTART.md:** If workflow changed → ask "Should we update QUICKSTART.md with these new commands?"

**When to update QUICKSTART.md:**
- ✅ New daily commands added (scripts, make targets, common operations)
- ✅ File locations changed (moved scripts, reorganized directories)
- ✅ Workflow shortcuts discovered (aliases, one-liners that save time)
- ✅ Common troubleshooting steps identified (frequently used fixes)

**When NOT to update:**
- ❌ Rarely-used commands (less than weekly usage)
- ❌ One-time setup steps (belongs in docs/SETUP.md instead)
- ❌ Experimental commands (not proven yet)

**STYLE_GUIDE.md:** If code style preference emerges → ask "Should we document this style preference in STYLE_GUIDE.md?"

**When to update STYLE_GUIDE.md:**
- ✅ Consistent pattern used 3+ times (establishes precedent)
- ✅ Readability improvements (type hints, docstring formats)
- ✅ Team conventions (naming patterns, file structure)
- ✅ Language-specific best practices (Python PEP 8, SQL style)
- ✅ Code organization principles (module structure, import order)

**When NOT to update:**
- ❌ Personal preferences without rationale
- ❌ One-off exceptions (context-specific choices)
- ❌ Already covered in official language guides

### 5. Remind User at End of Session

- If COMMAND_LOG.md was modified: "Remember to review COMMAND_LOG.md for sensitive data before committing"
- If multiple files changed: "Consider running `make backup` to create a backup"
- If documentation changed: "Consider running `make inventory` to update file summaries"
- If phase completed: "Phase complete! Update PROGRESS.md status to ✅ COMPLETE and run `make sync-progress`"
# Session Initialization

This document contains detailed procedures and decision criteria for starting Claude Code sessions.

## Session Startup Protocol (Proactive)

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

## File Inventory & Documentation (CRITICAL - Do Automatically)

### ALWAYS Update FILE_INVENTORY.md When Creating/Modifying Files

**Before `git add .`:** Run `make inventory` to update FILE_INVENTORY.md with new/changed files

**After running `make inventory`:** Review git diff to see what files changed, then document:
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

### Workflow

1. Create/modify files
2. Run `make inventory` (updates FILE_INVENTORY.md automatically)
3. Run `git status` to see all changes
4. Document in COMMAND_LOG.md what you changed and why
5. Then `git add .` and commit

## Check for Stale Documentation Needing Manual Updates

### PROGRESS.md Phase Status

If current phase completed but still shows ⏸️ PENDING → suggest updating status to ✅ COMPLETE

### PROGRESS.md Cost Estimates

After creating AWS resources → ask "Should I run `make check-costs` and update PROGRESS.md with actual costs?"

### TROUBLESHOOTING.md

After solving new error → ask "Should I add this solution to TROUBLESHOOTING.md?"

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

### ADRs (Architecture Decision Records)

After architectural decision → ask "Should I create ADR-00X for this decision? (see docs/adr/template.md)"

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

### QUICKSTART.md

If workflow changed → ask "Should we update QUICKSTART.md with these new commands?"

**When to update QUICKSTART.md:**
- ✅ New daily commands added (scripts, make targets, common operations)
- ✅ File locations changed (moved scripts, reorganized directories)
- ✅ Workflow shortcuts discovered (aliases, one-liners that save time)
- ✅ Common troubleshooting steps identified (frequently used fixes)

**When NOT to update:**
- ❌ Rarely-used commands (less than weekly usage)
- ❌ One-time setup steps (belongs in docs/SETUP.md instead)
- ❌ Experimental commands (not proven yet)

### STYLE_GUIDE.md

If code style preference emerges → ask "Should we document this style preference in STYLE_GUIDE.md?"

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

## Session End Reminders

Remind user at end of session:
- If COMMAND_LOG.md was modified: "Remember to review COMMAND_LOG.md for sensitive data before committing"
- If multiple files changed: "Consider running `make backup` to create a backup"
- If documentation changed: "Consider running `make inventory` to update file summaries"
- If phase completed: "Phase complete! Update PROGRESS.md status to ✅ COMPLETE and run `make sync-progress`"

## Progress Tracking Protocol

### Always Read PROGRESS.md First

Understand what has been completed and what's next

### Follow PROGRESS.md Sequentially

Start from the first "⏸️ PENDING" or "⏳ IN PROGRESS" task

### If the Plan Changes

Update PROGRESS.md BEFORE proceeding with new work:
- Document what changed and why
- Update task descriptions, time estimates, or dependencies
- Add new tasks or remove obsolete ones
- Mark changed sections with date and reason
- Get user confirmation before proceeding with the updated plan

### Mark Tasks as Complete Only When:

- Terminal output showing successful execution (exit code 0, expected output), AND
- Either: User says "done", "complete", "looks good", or similar affirmation
- OR: User proceeds to ask about the next task (implicit confirmation)
- **Exception:** Minor tasks (<5 min) can be auto-marked if command succeeds with clear success output

### Do NOT Assume Completion

Even if a command runs without errors, wait for user confirmation

### Update PROGRESS.md Immediately

After each completed step

### If Errors Occur

Document them in PROGRESS.md and work with user to resolve before proceeding

### Maintain Format and Detail Level

When updating PROGRESS.md

## Update PROGRESS.md When

- ✅ Completing any phase or sub-phase
- ⏸️ Discovering blockers or missing prerequisites
- 📝 Changing approach or architecture
- ❌ Encountering errors that delay timeline
- ✅ User explicitly confirms task completion
- 💰 Actual costs differ significantly from estimates

## Proactively Suggest Running Maintenance Tasks When

- **After completing a phase:** "Phase X.Y complete! Should I run `make sync-progress` to verify AWS resources match PROGRESS.md?"
- **After creating/modifying scripts:** "New scripts created. Should I run `make inventory` to update FILE_INVENTORY.md?"
- **After solving a new error:** "This error isn't in TROUBLESHOOTING.md yet. Should I add it? (Then run `make inventory`)"
- **After making architectural decisions:** "Should I create an ADR for this decision? (See docs/adr/template.md)"
- **After creating AWS resources:** "New AWS resources created. Should I run `make check-costs` to see the cost impact?"
- **Monday morning or start of week:** "It's a new week! Should I run `make update-docs` for weekly maintenance?"
- **After 5+ commits:** "Several commits made. Should I run `make backup` to create a backup?"

## Error Handling Protocol

- If a command fails, STOP and report to user immediately
- Do NOT attempt multiple fixes without user guidance
- Check `TROUBLESHOOTING.md` for known solutions first
- If unknown error, log with `log_solution` after resolving
- Update PROGRESS.md with error details and resolution

## Context Awareness

- Check what phase we're in before suggesting commands
- Don't suggest Phase 3 commands if Phase 2 isn't complete
- Verify prerequisites exist before executing dependent tasks
- Use `python scripts/maintenance/sync_progress.py` if unsure of current state

## Your Workflow Should Be

1. Read PROGRESS.md to understand current state
2. **If user requests changes to the plan**: Update PROGRESS.md first, get confirmation, then proceed
3. Execute the next pending task
4. Wait for confirmation (terminal output or user saying "done")
5. Update PROGRESS.md to mark task as ✅ COMPLETE
6. Move to next task

## Command Logging & Code Snippet Tracking

**CRITICAL: Log ALL code changes and outcomes to COMMAND_LOG.md for learning and reference**

### When Writing/Editing Code Files

Manually document in COMMAND_LOG.md:
- **What you created/changed:** File path, function/class name, purpose
- **Code snippet:** The actual code written (if short) or summary (if long)
- **Outcome:** Did it work? Any errors? What was learned?

**Format:**

```markdown
## [Timestamp] Code Change: [Brief Description]
**File:** `path/to/file.py`
**Purpose:** What this code does and why

**Code:**
```python
# Actual code snippet or summary
```

**Outcome:**
- ✅ Success / ❌ Failed
- Error messages (if any)
- What worked / what didn't
- Lessons learned
```

**When to log:**
- ✅ New functions/classes created
- ✅ Bug fixes (what was broken, how you fixed it)
- ✅ Refactoring (what changed, why)
- ✅ Failed attempts (what didn't work, why)
- ✅ Performance improvements

**Why this matters:**
- Learn from past mistakes (avoid repeating failed approaches)
- Track what patterns work well in this codebase
- Build institutional knowledge of trial and error
- Reference successful solutions for similar problems

### When Executing Terminal Commands

Encourage user to use the command logging system:
- Source the logging script: `source scripts/shell/log_command.sh`
- Execute commands with: `log_cmd <command>`
- Example: `log_cmd aws s3 ls s3://nba-sim-raw-data-lake/`

### Reference COMMAND_LOG.md When Debugging

Learn from past solutions:
- **Before writing new code:** Check if similar code was written before
- **When errors occur:** Search for similar error messages in log
- **When choosing approaches:** Review what worked/failed previously
- Use as a learning database of what works in this project

### Add Solutions to Errors

Use `log_solution <description>` helper function

### CRITICAL - Before Committing COMMAND_LOG.md to Git

- Always review for sensitive information (credentials, API keys, passwords, tokens)
- Sanitize AWS account IDs if sharing publicly
- Replace sensitive IPs/endpoints with placeholders
- Remove or redact any Personal Access Tokens (PATs)
- Remind user to review before any `git add` or `git commit` that includes COMMAND_LOG.md
# Claude Code Operational Guide

**Last Updated:** October 8, 2025
**Purpose:** Complete operational procedures for Claude Code session management, progress tracking, and command logging

This file consolidates guidance from:
- CLAUDE_SESSION_INIT.md (session initialization)
- CLAUDE_PROGRESS_TRACKING.md (progress tracking protocol)
- CLAUDE_COMMAND_LOGGING.md (command and code logging)
- CLAUDE_DOCUMENTATION_QUICK_REF.md (documentation system)

---

## Table of Contents

1. [Session Initialization](#session-initialization)
2. [Progress Tracking Protocol](#progress-tracking-protocol)
3. [Command & Code Logging](#command--code-logging)
4. [Documentation Update Triggers](#documentation-update-triggers)
5. [File Inventory Management](#file-inventory-management)

---

## Session Initialization

### Always Run at Start of Each Session

**Automatically run (don't ask user, just do it):**

```bash
source scripts/shell/session_manager.sh start
```

**What it checks:**
- Hardware: Model, Chip, Cores, Memory
- System: macOS version, Homebrew version and location
- Conda: Version, base path, active environment
- Python: Version, location, key packages (boto3, pandas, numpy)
- AWS CLI: Version and location
- Git: Version, location, status (branch, modified/untracked files), recent commits
- **Documentation status:** FILE_INVENTORY.md age, session history, command log, PROGRESS.md tasks, stale docs
- **Conversation logging:** Offers terminal session logging setup
- **Command logging:** Auto-sources log_command.sh functions

**Output format:** Clean, organized sections with all diagnostic details preserved

**Show output to user** for review at session start

**After EVERY commit:** Append to `.session-history.md`:
```bash
bash scripts/shell/session_manager.sh start >> .session-history.md
```
This creates version snapshot for each commit, correlating git history with exact software versions used

**Check conversation status:**
- If CHAT_LOG.md exists and stale (>30 min): Remind user it will be overwritten at 75% context
- If context approaching 75%: Proactively mention auto-save is coming soon
- CHAT_LOG.md is auto-managed - no user action needed

**Initial orientation:**
- Identify current phase from PROGRESS.md
- Review documentation status warnings from `session_manager.sh start` output
- Ask: "Any work completed since last session that should be marked ✅ COMPLETE in PROGRESS.md?"

### Proactive Maintenance Suggestions

**Ask user if they want to run (based on time since last update):**

- **Monday or 7+ days since last update:** "Would you like me to run `make update-docs` for weekly maintenance?"
- **7+ days since last inventory:** "Should I run `make inventory` to update file summaries?"
- **New AWS resources may exist:** "Should I run `make sync-progress` to check if PROGRESS.md matches AWS?"
- **After modifying .md files:** "After these changes, should I run `make inventory` to update FILE_INVENTORY.md?"

### Session End Reminder

**At end of session, remind user:**

- If COMMAND_LOG.md modified: "Remember to review COMMAND_LOG.md for sensitive data before committing"
- If multiple files changed: "Consider running `make backup` to create a backup"
- If documentation changed: "Consider running `make inventory` to update file summaries"
- If phase completed: "Phase complete! Update PROGRESS.md status to ✅ COMPLETE and run `make sync-progress`"

---

## Progress Tracking Protocol

### CRITICAL - Always Follow These Rules

#### 1. Always Read PROGRESS.md First

Understand what has been completed and what's next before starting any work.

#### 2. Follow PROGRESS.md Sequentially

Start from the first "⏸️ PENDING" or "🔄 IN PROGRESS" task. Do not skip ahead unless explicitly instructed.

#### 3. If the Plan Changes

Update PROGRESS.md BEFORE proceeding with new work:
- Document what changed and why
- Update task descriptions, time estimates, or dependencies
- Add new tasks or remove obsolete ones
- Mark changed sections with date and reason
- **Get user confirmation before proceeding with the updated plan**

#### 4. Only Mark Tasks as "✅ COMPLETE" When You Receive

Either:
- Terminal output showing successful execution (exit code 0, expected output) **AND** user says "done", "complete", "looks good", or similar affirmation
- **OR:** User proceeds to ask about the next task (implicit confirmation)
- **Exception:** Minor tasks (<5 min) can be auto-marked if command succeeds with clear success output

#### 5. Do NOT Assume Completion

Even if a command runs without errors, wait for user confirmation.

#### 6. Update PROGRESS.md Immediately

After each completed step.

#### 7. If Errors Occur

Document them in PROGRESS.md and work with user to resolve before proceeding.

#### 8. Maintain the Same Format and Detail Level

When updating PROGRESS.md.

### Update PROGRESS.md When

- ✅ Completing any phase or sub-phase
- ⏸️ Discovering blockers or missing prerequisites
- 📝 Changing approach or architecture
- ❌ Encountering errors that delay timeline
- ✅ User explicitly confirms task completion
- 💰 Actual costs differ significantly from estimates

### Proactively Suggest Running Maintenance Tasks When

- **After completing a phase:** "Phase X.Y complete! Should I run `make sync-progress` to verify AWS resources match PROGRESS.md?"
- **After creating/modifying scripts:** "New scripts created. Should I run `make inventory` to update FILE_INVENTORY.md?"
- **After solving a new error:** "This error isn't in TROUBLESHOOTING.md yet. Should I add it? (Then run `make inventory`)"
- **After making architectural decisions:** "Should I create an ADR for this decision? (See docs/adr/template.md)"
- **After creating AWS resources:** "New AWS resources created. Should I run `make check-costs` to see the cost impact?"
- **Monday morning or start of week:** "It's a new week! Should I run `make update-docs` for weekly maintenance?"
- **After 5+ commits:** "Several commits made. Should I run `make backup` to create a backup?"

### Error Handling Protocol

- If a command fails, **STOP and report to user immediately**
- Do NOT attempt multiple fixes without user guidance
- Check `TROUBLESHOOTING.md` for known solutions first (use grep, don't read fully)
- If unknown error, log with `log_solution` after resolving
- Update PROGRESS.md with error details and resolution

### Context Awareness

- Check what phase we're in before suggesting commands
- Don't suggest Phase 3 commands if Phase 2 isn't complete
- Verify prerequisites exist before executing dependent tasks
- Use `python scripts/maintenance/sync_progress.py` if unsure of current state

### Standard Workflow

1. Read PROGRESS.md to understand current state
2. **If user requests changes to the plan:** Update PROGRESS.md first, get confirmation, then proceed
3. Execute the next pending task
4. Wait for confirmation (terminal output or user saying "done")
5. Update PROGRESS.md to mark task as ✅ COMPLETE
6. Move to next task

---

## Command & Code Logging

### CRITICAL: Log ALL Code Changes and Outcomes to COMMAND_LOG.md

Command logging serves as a learning database - tracking what works, what fails, and why. This helps avoid repeating mistakes and reference successful solutions.

### When Writing/Editing Code Files

**Manually document in COMMAND_LOG.md:**
- **What you created/changed:** File path, function/class name, purpose
- **Code snippet:** The actual code written (if short) or summary (if long)
- **Outcome:** Did it work? Any errors? What was learned?

### Format

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

### When to Log

- ✅ New functions/classes created
- ✅ Bug fixes (what was broken, how you fixed it)
- ✅ Refactoring (what changed, why)
- ✅ Failed attempts (what didn't work, why)
- ✅ Performance improvements

### Why This Matters

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

Use `log_solution <description>` helper function after resolving unknown errors.

### CRITICAL - Before Committing COMMAND_LOG.md to Git

- Always review for sensitive information (credentials, API keys, passwords, tokens)
- Sanitize AWS account IDs if sharing publicly
- Replace sensitive IPs/endpoints with placeholders
- Remove or redact any Personal Access Tokens (PATs)
- **Remind user to review before any `git add` or `git commit` that includes COMMAND_LOG.md**

---

## Documentation Update Triggers

### Manual Updates Required

The following documentation requires MANUAL updates (cannot be automated):

| Document | Update When | How to Update |
|----------|-------------|---------------|
| **PROGRESS.md** | After completing phase/task | Change ⏸️ PENDING → ✅ COMPLETE, update "Last Updated" |
| **PROGRESS.md** | After creating AWS resources | Run `make check-costs`, update cost estimates with actuals |
| **TROUBLESHOOTING.md** | After solving new error | Add new section with problem/solution, run `make inventory` |
| **ADRs** | After architectural decision | Create `docs/adr/00X-name.md` from template, update `docs/adr/README.md` |
| **STYLE_GUIDE.md** | When code style preference emerges | Add rule with example, explain reasoning |
| **QUICKSTART.md** | When daily workflow changes | Update relevant command section |
| **TESTING.md** | When testing strategy evolves | Update approach, add examples |
| **.env.example** | When new env variables needed | Add variable with description |
| **COMMAND_LOG.md** | After every significant command OR code change | Use `log_cmd`, `log_note`, `log_solution` for commands; manually log all code snippets with outcomes |

### When to Add to TROUBLESHOOTING.md

✅ **Add when:**
- Errors that took >10 minutes to solve
- Non-obvious solutions (wouldn't find with quick Google search)
- Environment-specific issues (conda, AWS, macOS-specific)
- Recurring errors (seen multiple times in session)
- Errors with misleading messages (actual cause different from error text)

❌ **Don't add when:**
- Typos or syntax errors (obvious from error message)
- One-time issues (unlikely to recur)
- Already documented in official docs

### When to Create ADRs

✅ **Create when:**
- Significant architectural decisions (database choice, service selection, framework adoption)
- Technology choices with long-term impact (Python version, AWS service vs self-hosted)
- Major trade-offs (cost vs performance, simplicity vs scalability, storage vs compute)
- Decisions affecting multiple parts of system (authentication method, logging strategy, error handling)
- Rejecting common approaches (why NOT using X, why avoiding Y)
- Development workflow changes (build process, deployment strategy, testing approach)

❌ **Don't create when:**
- Small implementation details (variable naming, file organization)
- Temporary workarounds (quick fixes, patches)
- Obvious choices with no alternatives (using JSON for config, Git for version control)
- Easily reversible decisions with no consequences (UI colors, log message format)

### When to Update QUICKSTART.md

✅ **Update when:**
- New daily commands added (scripts, make targets, common operations)
- File locations changed (moved scripts, reorganized directories)
- Workflow shortcuts discovered (aliases, one-liners that save time)
- Common troubleshooting steps identified (frequently used fixes)

❌ **Don't update when:**
- Rarely-used commands (less than weekly usage)
- One-time setup steps (belongs in docs/SETUP.md instead)
- Experimental commands (not proven yet)

### When to Update STYLE_GUIDE.md

✅ **Update when:**
- Consistent pattern used 3+ times (establishes precedent)
- Readability improvements (type hints, docstring formats)
- Team conventions (naming patterns, file structure)
- Language-specific best practices (Python PEP 8, SQL style)
- Code organization principles (module structure, import order)

❌ **Don't update when:**
- Personal preferences without rationale
- One-off exceptions (context-specific choices)
- Already covered in official language guides

### Automated Documentation (Run Weekly)

- `make update-docs` - Updates timestamps, costs, stats, validates links
- `make sync-progress` - Checks PROGRESS.md vs actual AWS resources
- `make inventory` - Updates FILE_INVENTORY.md with file summaries
- `make check-costs` - Reports current AWS spending

### Monthly Documentation Review Checklist

1. Run all automation: `make update-docs`, `make sync-progress`, `make check-costs`
2. Review stale files (30+ days old) - update or mark as reviewed
3. Verify PROGRESS.md phases match reality (✅/⏸️ status)
4. Check cost estimates vs actuals in PROGRESS.md
5. Commit: `git commit -m "Monthly documentation refresh - $(date +%Y-%m)"`

---

## File Inventory Management

### CRITICAL - Always Update FILE_INVENTORY.md When Creating/Modifying Files

**Before `git add .`:** Run `make inventory` to update FILE_INVENTORY.md with new/changed files

**After running `make inventory`:** Review git diff to see what files changed, then document:
- **What you created/modified:** List each file path
- **Why you made the change:** Purpose and problem being solved
- **What error you were resolving:** If fixing a bug, document the error

### Format for Documentation

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

---

## Documentation System Quick Reference

### Architecture & Decisions

**ADRs** (`docs/adr/README.md`) - Why we made key technical decisions
- ADR-001: Redshift exclusion (saves $200-600/month)
- ADR-002: 10% data extraction (119 GB → 12 GB)
- ADR-003: Python 3.11 (Glue compatibility)
- ADR-004: Git without GitHub push (superseded by ADR-005)
- ADR-005: Git SSH authentication
- ADR-006: Session initialization automation
- Use `docs/adr/template.md` for new decisions

### Code Quality

**Style Guide** (`docs/STYLE_GUIDE.md`) - Required for all code
- Python: PEP 8, snake_case, type hints required
- SQL: Uppercase keywords, explicit JOINs
- Docstrings required for all functions

**Testing** (`docs/TESTING.md`) - pytest strategy
- Priority: Data validation (scores, dates, required fields)
- Mock AWS with moto library

**Troubleshooting** (`docs/TROUBLESHOOTING.md`) - **Check FIRST when errors occur**
- Use grep to find specific errors: `grep -i "error keyword" docs/TROUBLESHOOTING.md`
- Don't read entire file (1,025 lines)
- 28 documented issues with solutions
- 7 categories: Environment, AWS, Git, ETL, Database, Performance, Security

### Environment & Setup

**Setup Guide** (`docs/SETUP.md`) - Fresh environment setup (11 steps)

**Environment Variables** (`.env.example`) - 35 variables, NEVER commit `.env`

**check_machine_health.sh** - Comprehensive 14-point health check script

### Operational

**QUICKSTART.md** - Daily commands, file locations, quick fixes

**check_costs.sh** - AWS spending monitor (run weekly)

**Documentation Maintenance** (`docs/DOCUMENTATION_MAINTENANCE.md`)
- Weekly: `update_docs.sh` (auto-updates costs, timestamps, stats)
- Weekly: `sync_progress.py` (checks AWS vs PROGRESS.md)
- Monthly: Review checklist for stale docs
- **NEVER auto-commit** - always review changes

---

## Related Documentation

- **CLAUDE.md** - Core instructions and navigation patterns
- **docs/README.md** - Documentation index and task navigation
- **docs/CONTEXT_MANAGEMENT_GUIDE.md** - Strategies for extending session length
- **docs/EMERGENCY_RECOVERY.md** - Recovery procedures for common issues
- **PROGRESS.md** - Current phase status and session context
- **docs/claude_workflows/** - 38 modular workflows for specific tasks

---

*This guide is part of the modular documentation system created October 8, 2025 to optimize Claude Code context usage.*

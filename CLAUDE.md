# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Decision Tree

**When user asks to do something:**
1. **Is it the next pending task in PROGRESS.md?** → Proceed
2. **Is it skipping ahead?** → Check prerequisites first, warn if missing
3. **Is it changing the plan?** → Update PROGRESS.md first, get approval
4. **Will it cost money?** → Warn user with estimate, get confirmation
5. **Could it break something?** → Explain risk, suggest backup/test approach

**During the session:**
1. **Is context at 75%+?** → Auto-save conversation to CHAT_LOG.md immediately
2. **Is context at 90%+?** → Strongly urge user to commit NOW
3. **User says "save this conversation"?** → Write verbatim transcript to CHAT_LOG.md

**When a command fails:**
1. Check `TROUBLESHOOTING.md` for known solution
2. If unknown, STOP and ask user for guidance
3. Don't attempt multiple fixes automatically
4. Log solution with `log_solution` after resolving

**CRITICAL - Workflow Documentation System:**

User will provide specific instructions when needed. All workflow documentation methodology and procedures are documented in local-only files (never committed to GitHub) for security.

**WORKFLOW AUTOMATION SYSTEM:**

This project uses TWO automated documentation systems:

1. **Conversation Archiving** (see lines 66-155)
   - Saves Claude conversations automatically at 75%/90% context
   - Archives to SHA-based directories: `~/sports-simulator-archives/nba/<commit-sha>/`
   - Zero conversation loss design (verbatim transcripts)
   - Links conversations to code changes via commit SHA

2. **Workflow Documentation** (local only, NEVER on GitHub)
   - Read: `~/sports-simulator-archives/nba/conversations/mappings/CLAUDE_INSTRUCTIONS.md`
   - Session summaries and aggregation logs
   - Uses recipe-manager-dev-logs as example patterns
   - Local index files translate references to actual workflow execution logs

**These systems work together:**
- **Conversation archiving** captures raw discussions (complete verbatim exchanges)
- **Workflow documentation** provides curated summaries (high-level session reports)

**Instructions are stored locally only (NEVER on GitHub):**
- Read: `~/sports-simulator-archives/nba/conversations/mappings/CLAUDE_INSTRUCTIONS.md`
- This file contains complete instructions for the workflow automation and log aggregation system
- All implementation details are kept local for security

**When user references past work:**
- User may say: "Check the workflow from October" or "Review the automation logs"
- Follow the instructions in CLAUDE_INSTRUCTIONS.md to access the workflow documentation system
- The system uses a reference examples repository (recipe-manager-dev-logs) with example workflow patterns
- Local index files translate references to actual workflow execution logs

**Quick reference:**
- Public repository: https://github.com/ryanranft/recipe-manager-dev-logs (example patterns only)
- Local index files: Connect public examples to real workflow logs
- User will provide access to configuration guide when needed

**CRITICAL - Before EVERY git commit:**
1. **ALWAYS run security scan** and show results to user
2. **ALWAYS display flagged lines** for user review
3. **NEVER commit without showing scan results first**
4. Wait for user confirmation before proceeding with commit

**CRITICAL - Before EVERY git push:**
1. **ALWAYS ask user "Ready to push to GitHub?" before attempting push**
2. **NEVER run `git push` without explicit user approval first**
3. **If pre-push hook blocks with security violations:**
   - STOP immediately
   - Show user the flagged lines from hook output
   - Explain what was flagged (false positives vs real secrets)
   - Ask: "These appear to be [false positives/real secrets]. Bypass hook and push anyway? [y/N]"
   - Only push with --no-verify if user explicitly approves
4. **NEVER assume prior approval applies to new pushes** - always ask each time

**CRITICAL - Conversation Archiving Workflow:**

**System Overview:**
This project automatically archives Claude conversations with each git commit, linking conversation history to code history. Each commit SHA gets its own archive directory containing the conversation that led to those code changes.

**The Automated Workflow:**
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
   - Clears CHAT_LOG.md (ready for next session)

**Manual Override:**
- User can say "save this conversation" anytime to trigger manual save
- Useful for important decision points or before ending session early

**Key Points:**
- ✅ Automatic conversation saving at 75% and 90% context thresholds
- ✅ Each commit SHA = one archive directory with conversation
- ✅ Automatic archiving (no manual script execution needed)
- ✅ Automatic clearing (prevents old conversations mixing)
- ✅ SHA-based searchable history (link conversation to code)
- ✅ Zero conversation loss - Claude monitors and saves proactively

**Context Monitoring Thresholds:**
- **0-74% (0-148K tokens):** Normal operation, no warnings
- **75-89% (150K-179K tokens):** 🟡 Auto-save triggered, commit suggested
- **90-100% (180K-200K tokens):** 🔴 Auto-update triggered, commit urgent
- **100%+ (>200K tokens):** Conversation will be truncated, data loss possible

**How to Find Past Conversations:**
```bash
# Find commit by topic
git log --oneline --grep="authentication"
# Output: abc1234 Add user authentication

# Read conversation for that commit
cat ~/sports-simulator-archives/nba/abc1234*/CHAT_LOG_SANITIZED.md

# Search all conversations for keyword
grep -r "AWS error" ~/sports-simulator-archives/nba/*/CHAT_LOG_*.md
```

**Claude's Role:**
- ✅ Monitors context usage throughout session
- ✅ Automatically writes verbatim transcripts to CHAT_LOG.md at thresholds
- ✅ Can write transcript on-demand when user requests
- ✅ Can read archived conversations from `~/sports-simulator-archives/nba/<SHA>/`
- ✅ Proactively warns before conversation loss

**When Claude Auto-Saves:**
- At 75% context (150K tokens) - first automatic save
- At 90% context (180K tokens) - urgent update
- When user says "save this conversation" (manual trigger)
- Before context window truncation to prevent data loss

**Conversation Recovery (If Something Goes Wrong):**

**If conversation wasn't saved before commit:**
1. Check if CHAT_LOG.md exists: `ls -lh CHAT_LOG.md`
2. If empty, reconstruct from memory and save manually
3. Run: `bash scripts/maintenance/archive_chat_log.sh`

**If context truncated before save:**
1. What was lost: Oldest exchanges (beginning of conversation)
2. What's preserved: Recent exchanges (last ~50K tokens)
3. Write what you remember of early conversation to CHAT_LOG.md
4. Note at top: "⚠️ Partial conversation - context truncated"

**To find conversations across commits:**
```bash
# Search all archives for a keyword
grep -r "keyword" ~/sports-simulator-archives/nba/*/CHAT_LOG_SANITIZED.md

# List all archived conversations chronologically
ls -lt ~/sports-simulator-archives/nba/*/CHAT_LOG_SANITIZED.md
```

## Instructions for Claude

**Documentation Trigger System:**

This project uses an automated documentation update trigger system. Each key documentation file has an embedded HTML comment trigger that signals when it needs updating.

**Read these files to understand the system:**
1. `.documentation-triggers.md` - Central registry of all documentation update triggers
2. `session_startup.sh` output - Shows documentation status checks automatically

**Key documentation files with triggers:**
- `CHAT_LOG.md` - **Auto-updated at 75% and 90% context** (Claude handles automatically)
- `COMMAND_LOG.md` - Update after EVERY code change
- `FILE_INVENTORY.md` - Run `make inventory` before every `git add .`
- `PROGRESS.md` - Update after completing ANY task
- `.session-history.md` - Append after every commit
- `MACHINE_SPECS.md` - Verify at session start

**The triggers tell you:**
- ✅ When each file should be updated (triggering event)
- ✅ How often (frequency)
- ✅ What command to run (if automated)
- ✅ Last update date

**At session start, `session_startup.sh` automatically checks:**
- FILE_INVENTORY.md age (warns if > 7 days)
- Session history status
- Command log status
- PROGRESS.md task counts
- Stale documentation (> 30 days)

**See `.documentation-triggers.md` for complete documentation trigger system reference.**

---

**Session Initialization (Proactive):**
1. **Always run at start of each session:**
   - **Credentials:** Auto-loaded from ~/.zshrc when entering project directory (no verification needed)
   - **Startup checklist** - Automatically run (don't ask user, just do it):
     ```bash
     bash scripts/shell/session_startup.sh
     ```
     - **What it checks:**
       - Hardware: Model, Chip, Cores, Memory
       - System: macOS version, Homebrew version and location
       - Conda: Version, base path, active environment
       - Python: Version, location, key packages (boto3, pandas, numpy) with install paths
       - AWS CLI: Version and location
       - Git: Version, location, status (branch, modified/untracked files), recent commits
       - **Documentation status:** FILE_INVENTORY.md age, session history, command log, PROGRESS.md tasks, stale docs
     - **Output format:** Clean, organized sections with all diagnostic details preserved
     - **Session start:** Show output to user for review
     - **After EVERY commit:** Append to `.session-history.md` with:
       ```bash
       bash scripts/shell/session_startup.sh >> .session-history.md
       ```
       This creates a version snapshot for each commit, allowing user to correlate git history with exact software versions used
   - **Check conversation status:**
     - If CHAT_LOG.md exists and is stale (>30 min): Remind user it will be overwritten at 75% context
     - If context approaching 75%: Proactively mention auto-save is coming soon
     - CHAT_LOG.md is auto-managed - no user action needed
   - Identify current phase from PROGRESS.md
   - Review documentation status warnings from `session_startup.sh` output
   - Ask: "Any work completed since last session that should be marked ✅ COMPLETE in PROGRESS.md?"

2. **Ask user if they want to run (based on time since last update):**
   - If Monday or 7+ days since last update: "Would you like me to run `make update-docs` for weekly maintenance?"
   - If 7+ days since last inventory: "Should I run `make inventory` to update file summaries?"
   - If new AWS resources may exist: "Should I run `make sync-progress` to check if PROGRESS.md matches AWS?"
   - If any .md files modified: "After these changes, should I run `make inventory` to update FILE_INVENTORY.md?"

3. **File Inventory & Documentation (CRITICAL - Do Automatically):**

   **ALWAYS update FILE_INVENTORY.md when creating/modifying files:**

   - **Before `git add .`:** Run `make inventory` to update FILE_INVENTORY.md with new/changed files
   - **After running `make inventory`:** Review git diff to see what files changed, then document:
     - **What you created/modified:** List each file path
     - **Why you made the change:** Purpose and problem being solved
     - **What error you were resolving:** If fixing a bug, document the error
   - **Format for documentation:**
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

   - **Where to document:** Add to COMMAND_LOG.md (for code changes) and ensure FILE_INVENTORY.md is updated

   **Workflow:**
   1. Create/modify files
   2. Run `make inventory` (updates FILE_INVENTORY.md automatically)
   3. Run `git status` to see all changes
   4. Document in COMMAND_LOG.md what you changed and why
   5. Then `git add .` and commit

4. **Check for stale documentation needing manual updates:**
   - **PROGRESS.md Phase Status:** If current phase completed but still shows ⏸️ PENDING → suggest updating status to ✅ COMPLETE
   - **PROGRESS.md Cost Estimates:** After creating AWS resources → ask "Should I run `make check-costs` and update PROGRESS.md with actual costs?"
   - **TROUBLESHOOTING.md:** After solving new error → ask "Should I add this solution to TROUBLESHOOTING.md?"
     - **When to add to TROUBLESHOOTING.md:**
       - ✅ Errors that took >10 minutes to solve
       - ✅ Non-obvious solutions (wouldn't find with quick Google search)
       - ✅ Environment-specific issues (conda, AWS, macOS-specific)
       - ✅ Recurring errors (seen multiple times in session)
       - ✅ Errors with misleading messages (actual cause different from error text)
     - **When NOT to add:**
       - ❌ Typos or syntax errors (obvious from error message)
       - ❌ One-time issues (unlikely to recur)
       - ❌ Already documented in official docs
   - **ADRs:** After architectural decision → ask "Should I create ADR-00X for this decision? (see docs/adr/template.md)"
     - **When to create ADRs:**
       - ✅ Significant architectural decisions (database choice, service selection, framework adoption)
       - ✅ Technology choices with long-term impact (Python version, AWS service vs self-hosted)
       - ✅ Major trade-offs (cost vs performance, simplicity vs scalability, storage vs compute)
       - ✅ Decisions affecting multiple parts of system (authentication method, logging strategy, error handling)
       - ✅ Rejecting common approaches (why NOT using X, why avoiding Y)
       - ✅ Development workflow changes (build process, deployment strategy, testing approach)
     - **When NOT to create ADRs:**
       - ❌ Small implementation details (variable naming, file organization)
       - ❌ Temporary workarounds (quick fixes, patches)
       - ❌ Obvious choices with no alternatives (using JSON for config, Git for version control)
       - ❌ Easily reversible decisions with no consequences (UI colors, log message format)
   - **QUICKSTART.md:** If workflow changed → ask "Should we update QUICKSTART.md with these new commands?"
     - **When to update QUICKSTART.md:**
       - ✅ New daily commands added (scripts, make targets, common operations)
       - ✅ File locations changed (moved scripts, reorganized directories)
       - ✅ Workflow shortcuts discovered (aliases, one-liners that save time)
       - ✅ Common troubleshooting steps identified (frequently used fixes)
     - **When NOT to update:**
       - ❌ Rarely-used commands (less than weekly usage)
       - ❌ One-time setup steps (belongs in docs/SETUP.md instead)
       - ❌ Experimental commands (not proven yet)
   - **STYLE_GUIDE.md:** If code style preference emerges → ask "Should we document this style preference in STYLE_GUIDE.md?"
     - **When to update STYLE_GUIDE.md:**
       - ✅ Consistent pattern used 3+ times (establishes precedent)
       - ✅ Readability improvements (type hints, docstring formats)
       - ✅ Team conventions (naming patterns, file structure)
       - ✅ Language-specific best practices (Python PEP 8, SQL style)
       - ✅ Code organization principles (module structure, import order)
     - **When NOT to update:**
       - ❌ Personal preferences without rationale
       - ❌ One-off exceptions (context-specific choices)
       - ❌ Already covered in official language guides

4. **Remind user at end of session:**
   - If COMMAND_LOG.md was modified: "Remember to review COMMAND_LOG.md for sensitive data before committing"
   - If multiple files changed: "Consider running `make backup` to create a backup"
   - If documentation changed: "Consider running `make inventory` to update file summaries"
   - If phase completed: "Phase complete! Update PROGRESS.md status to ✅ COMPLETE and run `make sync-progress`"

**CRITICAL - Progress Tracking Protocol:**

1. **Always read PROGRESS.md first** to understand what has been completed and what's next
2. **Follow PROGRESS.md sequentially** - start from the first "⏸️ PENDING" or "⏳ IN PROGRESS" task
3. **If the plan changes**, update PROGRESS.md BEFORE proceeding with new work:
   - Document what changed and why
   - Update task descriptions, time estimates, or dependencies
   - Add new tasks or remove obsolete ones
   - Mark changed sections with date and reason
   - Get user confirmation before proceeding with the updated plan
4. **Only mark tasks as "✅ COMPLETE" when you receive:**
   - Terminal output showing successful execution (exit code 0, expected output), AND
   - Either: User says "done", "complete", "looks good", or similar affirmation
   - OR: User proceeds to ask about the next task (implicit confirmation)
   - **Exception:** Minor tasks (<5 min) can be auto-marked if command succeeds with clear success output
5. **Do NOT assume completion** - even if a command runs without errors, wait for user confirmation
6. **Update PROGRESS.md immediately** after each completed step
7. **If errors occur**, document them in PROGRESS.md and work with user to resolve before proceeding
8. **Maintain the same format and detail level** when updating PROGRESS.md

**Update PROGRESS.md when:**
- ✅ Completing any phase or sub-phase
- ⏸️ Discovering blockers or missing prerequisites
- 📝 Changing approach or architecture
- ❌ Encountering errors that delay timeline
- ✅ User explicitly confirms task completion
- 💰 Actual costs differ significantly from estimates

**Proactively suggest running maintenance tasks when:**
- **After completing a phase:** "Phase X.Y complete! Should I run `make sync-progress` to verify AWS resources match PROGRESS.md?"
- **After creating/modifying scripts:** "New scripts created. Should I run `make inventory` to update FILE_INVENTORY.md?"
- **After solving a new error:** "This error isn't in TROUBLESHOOTING.md yet. Should I add it? (Then run `make inventory`)"
- **After making architectural decisions:** "Should I create an ADR for this decision? (See docs/adr/template.md)"
- **After creating AWS resources:** "New AWS resources created. Should I run `make check-costs` to see the cost impact?"
- **Monday morning or start of week:** "It's a new week! Should I run `make update-docs` for weekly maintenance?"
- **After 5+ commits:** "Several commits made. Should I run `make backup` to create a backup?"

**Error Handling Protocol:**
- If a command fails, STOP and report to user immediately
- Do NOT attempt multiple fixes without user guidance
- Check `TROUBLESHOOTING.md` for known solutions first
- If unknown error, log with `log_solution` after resolving
- Update PROGRESS.md with error details and resolution

**Context Awareness:**
- Check what phase we're in before suggesting commands
- Don't suggest Phase 3 commands if Phase 2 isn't complete
- Verify prerequisites exist before executing dependent tasks
- Use `python scripts/maintenance/sync_progress.py` if unsure of current state

**Your workflow should be:**
- Read PROGRESS.md to understand current state
- **If user requests changes to the plan**: Update PROGRESS.md first, get confirmation, then proceed
- Execute the next pending task
- Wait for confirmation (terminal output or user saying "done")
- Update PROGRESS.md to mark task as ✅ COMPLETE
- Move to next task

**Command Logging & Code Snippet Tracking:**

**CRITICAL: Log ALL code changes and outcomes to COMMAND_LOG.md for learning and reference**

9. **When writing/editing code files**, manually document in COMMAND_LOG.md:
   - **What you created/changed:** File path, function/class name, purpose
   - **Code snippet:** The actual code written (if short) or summary (if long)
   - **Outcome:** Did it work? Any errors? What was learned?
   - **Format:**
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
   - **When to log:**
     - ✅ New functions/classes created
     - ✅ Bug fixes (what was broken, how you fixed it)
     - ✅ Refactoring (what changed, why)
     - ✅ Failed attempts (what didn't work, why)
     - ✅ Performance improvements
   - **Why this matters:**
     - Learn from past mistakes (avoid repeating failed approaches)
     - Track what patterns work well in this codebase
     - Build institutional knowledge of trial and error
     - Reference successful solutions for similar problems

10. **When executing terminal commands**, encourage user to use the command logging system:
    - Source the logging script: `source scripts/shell/log_command.sh`
    - Execute commands with: `log_cmd <command>`
    - Example: `log_cmd aws s3 ls s3://nba-sim-raw-data-lake/`

11. **Reference COMMAND_LOG.md** when debugging similar issues to learn from past solutions:
    - **Before writing new code:** Check if similar code was written before
    - **When errors occur:** Search for similar error messages in log
    - **When choosing approaches:** Review what worked/failed previously
    - Use as a learning database of what works in this project

12. **Add solutions to errors** using `log_solution <description>` helper function

13. **CRITICAL - Before committing COMMAND_LOG.md to Git:**
    - Always review for sensitive information (credentials, API keys, passwords, tokens)
    - Sanitize AWS account IDs if sharing publicly
    - Replace sensitive IPs/endpoints with placeholders
    - Remove or redact any Personal Access Tokens (PATs)
    - Remind user to review before any `git add` or `git commit` that includes COMMAND_LOG.md

**Documentation Update Triggers:**

The following documentation requires MANUAL updates (cannot be automated):

| Document | Update When | How to Update |
|----------|-------------|---------------|
| **MACHINE_SPECS.md** | Daily (start of each session) | Run session startup checklist, update version table with current software versions |
| **PROGRESS.md** | After completing phase/task | Change ⏸️ PENDING → ✅ COMPLETE, update "Last Updated" |
| **PROGRESS.md** | After creating AWS resources | Run `make check-costs`, update cost estimates with actuals |
| **TROUBLESHOOTING.md** | After solving new error | Add new section with problem/solution, run `make inventory` |
| **ADRs** | After architectural decision | Create `docs/adr/00X-name.md` from template, update `docs/adr/README.md` |
| **STYLE_GUIDE.md** | When code style preference emerges | Add rule with example, explain reasoning |
| **QUICKSTART.md** | When daily workflow changes | Update relevant command section |
| **TESTING.md** | When testing strategy evolves | Update approach, add examples |
| **.env.example** | When new env variables needed | Add variable with description |
| **COMMAND_LOG.md** | After every significant command OR code change | Use `log_cmd`, `log_note`, `log_solution` for commands; manually log all code snippets with outcomes (success/failure, errors, lessons learned) |

**Automated Documentation (run weekly):**
- `make update-docs` - Updates timestamps, costs, stats, validates links
- `make sync-progress` - Checks PROGRESS.md vs actual AWS resources
- `make inventory` - Updates FILE_INVENTORY.md with file summaries
- `make check-costs` - Reports current AWS spending

**Monthly Documentation Review Checklist:**
1. Run all automation: `make update-docs`, `make sync-progress`, `make check-costs`
2. Review stale files (30+ days old) - update or mark as reviewed
3. Verify PROGRESS.md phases match reality (✅/⏸️ status)
4. Check cost estimates vs actuals in PROGRESS.md
5. Commit: `git commit -m "Monthly documentation refresh - $(date +%Y-%m)"`

**Documentation System (Quick Reference):**

**Architecture & Decisions:**
- **ADRs** (`docs/adr/README.md`) - Why we made key technical decisions
  - ADR-001: Redshift exclusion (saves $200-600/month)
  - ADR-002: 10% data extraction (119 GB → 12 GB)
  - ADR-003: Python 3.11 (Glue compatibility)
  - ADR-004: Git without GitHub push (superseded by ADR-005)
  - ADR-005: Git SSH authentication
  - ADR-006: Session initialization automation
  - Use `docs/adr/template.md` for new decisions
  - See lines 58-69 above for when to create ADRs

**Code Quality:**
- **Style Guide** (`docs/STYLE_GUIDE.md`) - Required for all code
  - Python: PEP 8, snake_case, type hints required
  - SQL: Uppercase keywords, explicit JOINs
  - Docstrings required for all functions
- **Testing** (`docs/TESTING.md`) - pytest strategy
  - Priority: Data validation (scores, dates, required fields)
  - Mock AWS with moto library
- **Troubleshooting** (`docs/TROUBLESHOOTING.md`) - **Check FIRST when errors occur**
  - 28 documented issues with solutions
  - 7 categories: Environment, AWS, Git, ETL, Database, Performance, Security

**Environment & Setup:**
- **Setup Guide** (`docs/SETUP.md`) - Fresh environment setup (11 steps)
- **Environment Variables** (`.env.example`) - 35 variables, NEVER commit `.env`
- **check_machine_health.sh** - Comprehensive 14-point health check script (replaces verify_setup.sh)

**Operational:**
- **QUICKSTART.md** - Daily commands, file locations, quick fixes
- **check_costs.sh** - AWS spending monitor (run weekly)
- **Documentation Maintenance** (`docs/DOCUMENTATION_MAINTENANCE.md`)
  - Weekly: `update_docs.sh` (auto-updates costs, timestamps, stats)
  - Weekly: `sync_progress.py` (checks AWS vs PROGRESS.md)
  - Monthly: Review checklist for stale docs
  - **NEVER auto-commit** - always review changes

## Project Overview

NBA Game Simulator & ML Platform - A Python-based AWS data pipeline that:
- Ingests 146K+ historical NBA game JSON files (1999-2025, 119 GB) from ESPN
- Extracts 10% of relevant fields via AWS Glue ETL
- Stores processed data in RDS PostgreSQL (~12 GB after extraction)
- Simulates NBA games using statistical models on EC2
- Trains ML prediction models using SageMaker

**Current Status:** Phase 1 Complete - S3 data lake operational with 119 GB uploaded

**Development Machine:** MacBook Pro 16-inch, 2023 (M2 Max, 96GB RAM, macOS Sequoia 15.6.1)
- See `MACHINE_SPECS.md` for complete hardware/software specifications
- Code is optimized for Apple Silicon (ARM64) architecture
- Uses Homebrew for system packages and Miniconda for Python environment

## Essential Setup

**Environment activation:**
```bash
# CRITICAL: This project uses Conda, NOT venv
conda activate nba-aws

# Navigate to project
cd /Users/ryanranft/nba-simulator-aws
```

**Verify environment:**
```bash
python --version           # Should show Python 3.11.13
aws --version             # System-wide AWS CLI 2.x (NOT in conda)
aws s3 ls s3://nba-sim-raw-data-lake/
```

## Critical Paths

- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **Original Data:** `/Users/ryanranft/0espn/data/nba/` (119 GB source)
- **S3 Bucket:** `s3://nba-sim-raw-data-lake` (146,115 files)
- **Conda Env:** `/Users/ryanranft/miniconda3/envs/nba-aws`
- **Conversation Archives:** `~/sports-simulator-archives/nba/<commit-sha>/CHAT_LOG_*.md`
- **Quick Reference:** `QUICKSTART.md` (one-page command reference)
- **Machine Specs:** `MACHINE_SPECS.md` (hardware, software versions, compatibility notes)
- **File Inventory:** `FILE_INVENTORY.md` (auto-generated summaries of 28 documented files)
- **Config Files:** `config/aws_config.yaml` (AWS resource definitions - minimal, to be populated in Phase 2+)
- **Maintenance Scripts:** `scripts/maintenance/` (generate_inventory.py, sync_progress.py, update_docs.sh, archive_chat_log.sh)
- **Shell Utilities:** `scripts/shell/` (check_machine_health.sh, log_command.sh, sanitize_command_log.sh, save_conversation.sh)
- **AWS Scripts:** `scripts/aws/` (check_costs.sh)
- **Cost Tracking:** `scripts/aws/check_costs.sh` (AWS spending monitor)

## Architecture

**5-Phase Pipeline:**

```
Phase 1 (✅): S3 Data Lake
  └─ 146,115 JSON files uploaded

Phase 2 (⏸️): AWS Glue
  ├─ 2.1: Crawler discovers JSON schema
  └─ 2.2: ETL job extracts 10% of fields

Phase 3 (⏸️): RDS PostgreSQL
  └─ Stores extracted data (~12 GB)

Phase 4 (⏸️): EC2 Simulation Engine
  └─ Runs game simulations

Phase 5 (⏸️): SageMaker ML Pipeline
  ├─ Jupyter notebooks for development
  └─ Training jobs for models
```

**Key Architectural Decision:** Extract only 10% of JSON fields during ETL to reduce costs and improve performance (119 GB → 12 GB).

## Git & GitHub Configuration

**Status:** ✅ Configured with SSH authentication
**Remote:** `git@github.com:ryanranft/nba-simulator-aws.git`
**Branch:** `main` (tracks `origin/main`)
**Repository:** https://github.com/ryanranft/nba-simulator-aws

**Key points:**
- Uses SSH (not HTTPS), no password prompts needed
- SSH keys already configured
- See `QUICKSTART.md` lines 56-73 for common commands
- See `docs/TROUBLESHOOTING.md` lines 336-508 for Git issues
- See `ADR-005` for full SSH vs HTTPS rationale

**CRITICAL - Security Protocol Before ANY Git Commit:**

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

**Whitelist - Safe patterns (don't trigger false positives):**
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

**Security Check Protocol:**
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

**Commit format (include co-authorship footer):**
```bash
git commit -m "$(cat <<'EOF'
Brief description of changes

Detailed explanation if needed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Common Commands

**Access S3 data:**
```bash
# List bucket contents
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/

# Download sample for inspection
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json ./sample.json

# View JSON structure
cat sample.json | python -m json.tool | head -50
```

**Database (when RDS is created):**
```bash
# Connect to RDS
psql -h nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com -U postgres -d nba_simulator

# In psql: check row counts
SELECT COUNT(*) FROM games;
SELECT COUNT(*) FROM player_game_stats;
```

**AWS Resource Management:**
```bash
# Check Glue crawler status
aws glue get-crawler --name nba-data-crawler

# List Glue tables
aws glue get-tables --database-name nba_raw_data

# Start/stop EC2 instance
aws ec2 stop-instances --instance-ids i-xxxxxxxxx
aws ec2 start-instances --instance-ids i-xxxxxxxxx
```

## Data Structure

**S3 Bucket Layout:**
```
s3://nba-sim-raw-data-lake/
├── box_scores/    # 44,828 files - player statistics per game
├── pbp/           # 44,826 files - play-by-play sequences
├── schedule/      # 11,633 files - game schedules by date (YYYYMMDD.json)
└── team_stats/    # 44,828 files - team-level statistics per game
```

**Note:** Local data folder names differ from S3 folder names:
- Local: `data/nba_box_score/`, `data/nba_pbp/`, `data/nba_schedule_json/`, `data/nba_team_stats/`
- S3: `box_scores/`, `pbp/`, `schedule/`, `team_stats/`

**Data Extraction Strategy:**
- **Box Scores:** Extract player_id, player_name, team_id, position, minutes, points, rebounds, assists, steals, blocks, turnovers, FG/3PT/FT stats
- **Play-by-Play:** Extract game_id, period, clock, play_type, scoring_play, player_id, team_id, scores
- **Schedules:** Extract game_id, game_date, home/away team_ids, scores, venue
- **Team Stats:** Extract team_id, game_id, aggregate statistics

**Exclude:** Commentary, photos, broadcast details, video links, historical narratives

**Data File Characteristics:**
- **File Size:** Each JSON file is ~700KB and contains 17,000-19,000 lines
- **Content Warning:** Files contain full ESPN web scraping data including:
  - CDN paths, JavaScript chunks, CSS assets (majority of file size)
  - Actual game data embedded within web page metadata
- **ETL Implication:** Glue ETL must parse deeply nested JSON to extract relevant game statistics
- **First file date:** 131105001.json (November 5, 2013 season start)

## Important Notes

**AWS Configuration:**
- Account: <your-aws-account-id>
- Region: us-east-1
- IAM User: iam (AdministratorAccess)

**AWS Credentials Storage (CRITICAL):**
- **Primary Location:** `~/.aws/credentials` (AWS CLI standard, chmod 600)
- **Backup Location:** Store encrypted backups outside project directory (never commit)
- **NEVER:**
  - Copy credentials into project directory
  - Store credentials in environment variables
  - Reference credentials in code (boto3 auto-reads from ~/.aws/credentials)
  - Commit credential files to Git
  - Document exact paths to credential backups (security risk)

**Critical Constraints:**
- AWS CLI is system-wide, NOT in conda (do not `pip install awscli`)
- Data folder (119 GB) is gitignored - never commit to Git
- Python 3.11 required for AWS Glue 4.0 compatibility
- Git/GitHub configured with SSH authentication (operational)
- **Python Dependencies:** 10 packages in requirements.txt (boto3, pandas, numpy, pyarrow, psycopg2-binary, sqlalchemy, pytest, jupyter, python-dotenv, pyyaml, tqdm)
- **Key Libraries:** boto3 (AWS SDK), pandas (data processing), pytest (testing), jupyter (analysis)

**Cost Awareness (IMPORTANT):**
- **Current:** $2.74/month (S3 storage only)
- **After Glue + RDS:** ~$46/month
- **Full deployment:** $95-130/month
- **Monthly budget target:** $150 (alert if approaching)
- **ALWAYS warn user before:**
  - Creating RDS instances (~$29/month)
  - Creating EC2 instances (~$5-15/month)
  - Creating Glue jobs (~$13/month)
  - Creating SageMaker notebooks (~$50/month)
- **Suggest cost estimates** before proceeding
- **Remind to stop/delete** resources when done testing

**Data Safety Protocol:**
- NEVER delete or modify S3 bucket contents without explicit user request
- NEVER drop database tables without user confirmation
- NEVER commit `.env`, credentials, or sensitive data
- ALWAYS run `sanitize_command_log.sh` before committing COMMAND_LOG.md
- Backup before destructive operations (provide backup command)

**Credential Rotation Schedule:**

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
- Document last rotation date in MACHINE_SPECS.md

**Emergency Rotation (if compromised):**
1. Immediately deactivate compromised credential
2. Generate new credential
3. Update all systems using old credential
4. Delete compromised credential
5. Review CloudTrail logs for unauthorized access
6. Document incident in TROUBLESHOOTING.md

**GitHub Secret Scanning Setup:**

GitHub provides free secret scanning for public repositories. To enable for this project:

1. **Enable Secret Scanning (if public):**
   - Go to: https://github.com/ryanranft/nba-simulator-aws/settings/security_analysis
   - Enable "Secret scanning"
   - Enable "Push protection" (blocks pushes with secrets)

2. **What GitHub Detects:**
   - AWS credentials (access keys, secret keys, session tokens)
   - GitHub Personal Access Tokens (PATs)
   - Azure, Google Cloud, Slack tokens
   - Database connection strings with passwords
   - 200+ partner patterns

3. **How It Works:**
   - Scans all commits in history
   - Alerts on Settings → Security → Secret scanning alerts
   - Push protection blocks new secrets from being pushed
   - Partners (like AWS) are notified of leaked credentials

4. **Local Git Hooks (Already Implemented):**
   - Pre-commit hook: Blocks commits with secrets
   - Pre-push hook: Scans last 5 commits before push
   - Commit template: Reminds about security in every commit
   - Located in: `.git/hooks/pre-commit`, `.git/hooks/pre-push`

5. **Testing the Protection:**
   ```bash
   # Try to commit a test secret (will be blocked):
   echo "aws_access_key_id=AWS_ACCESS_KEYIOSFODNN7EXAMPLE" > test.txt
   git add test.txt
   git commit -m "test"  # Should be blocked by pre-commit hook
   rm test.txt
   ```

6. **If Secret Is Detected:**
   - Immediately rotate the compromised credential
   - Review GitHub alert for details
   - Check AWS CloudTrail for unauthorized usage
   - Update all systems using the old credential

**Layered Security Summary:**
- ✅ Layer 1: .gitignore (prevents staging sensitive files)
- ✅ Layer 2: Pre-commit hook (blocks commits with secrets)
- ✅ Layer 3: Pre-push hook (scans recent commit history)
- ✅ Layer 4: Commit template (reminds about security)
- ✅ Layer 5: GitHub secret scanning (cloud-based detection)
- ✅ Layer 6: Credential rotation schedule (90-day intervals)

## Next Steps

See `PROGRESS.md` for detailed phase-by-phase implementation plan with time estimates, cost breakdowns, and step-by-step instructions.

**Immediate next tasks:**
1. Set up AWS Glue Crawler (~45 min, adds $1/month)
2. Provision RDS PostgreSQL (~2-3 hrs, adds $29/month)
3. Create Glue ETL job (~6-8 hrs dev, adds $13/month)

## Development Workflow

**Before starting work:**
```bash
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws
git status
```

**When AWS credentials fail:**
```bash
aws configure
# Enter: access key, secret key, region (us-east-1), output format (json)
```

**Weekly maintenance:**
```bash
# Update documentation automatically
make update-docs

# Check if PROGRESS.md matches AWS reality
make sync-progress

# Monitor AWS costs
make check-costs
```

**Makefile Commands (Recommended):**
```bash
# View all available commands
make help

# Note: Run `make help` to see currently implemented commands
# Some commands listed below may be added in future phases

# File inventory and summaries
make inventory              # Generate FILE_INVENTORY.md with file summaries
make describe FILE=path     # Show detailed info about specific file

# Verification
make verify-all             # Run all checks (env + AWS + files)
make verify-env             # Check conda environment
make verify-aws             # Check AWS credentials and S3

# Utilities
make stats                  # Show project statistics
make backup                 # Create backup of critical files
make clean                  # Remove temporary files
make git-status             # Show git status and recent commits
```

**PyCharm performance tip:** Mark `data/` folder as "Excluded" in Project Structure settings to prevent indexing 146K+ files.

## Known Documentation Gaps

- **README.md:** Currently empty - should contain project overview for GitHub visitors
  - Suggest: Quick description, setup link, architecture diagram, current status
  - Recommend creating after Phase 2 completion for more complete project overview
# CLAUDE.md

**Version:** 3.0 (Context-Optimized Modular System)
**Last Updated:** October 8, 2025
**System Status:** 8 phases (2 with enhancement plans), 40 workflows, 97+ workflow references

This file provides core guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Quick Start - Every Session

**Always read these 3 files at session start:**
1. **CLAUDE.md** (this file, ~300 lines) - Core instructions
2. **PROGRESS.md** (~685 lines) - Current project state
3. **docs/README.md** (~100 lines) - Documentation index

**Total: ~1,085 lines (5% context)** - Leaves 95% for actual work

---

## Workflow Order

**See `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md` for workflow index and execution order.**

**All detailed workflows:** `docs/claude_workflows/workflow_descriptions/`

**System contains 38+ modular workflows:**
- 🚀 Session Start & End (#1, #14)
- 📋 Decision & Plan Change
- 💻 Task Execution & File Creation
- 🔒 Git Commit & Push (security protocols)
- 🧪 Testing (TDD, unit, integration)
- 💰 Cost Management
- 💾 Backup & Recovery
- 📊 Data Validation
- 🔍 Troubleshooting Protocol
- ☁️ AWS Resource Setup
- 🌙 Overnight Scraper Handoff (#38)

**Navigation pattern:**
```
1. Read PROGRESS.md (identify current task/phase)
2. Read docs/README.md (find documentation location)
3. Read specific phase file (e.g., docs/phases/PHASE_3_DATABASE.md)
4. Read workflows referenced in current sub-phase
5. Execute workflow steps
```

**Quick reference - Every session:**
1. **Initialize session** (`bash scripts/shell/session_manager.sh start`) - show output to user
   - **NEW:** Auto-checks credentials, overnight jobs, displays session context
   - No need to separately read PROGRESS.md - all context in output
2. **Ask user:** "What did you complete since last session?" (or 'none' to continue)
3. If work completed → Update PROGRESS.md status
4. If 'none' → Proceed with "Next planned task" from session summary
5. Execute task → Document outcome
6. Update PROGRESS.md → Suggest next action
7. Follow security protocol for commits/pushes
8. Monitor context (auto-save at 75%, warn at 90%)

**Session manager now provides automatically:**
- ✅ Credentials status
- ✅ Overnight jobs check (auto-detected, no manual workflow needed)
- ✅ Last session date/time
- ✅ Last completed work
- ✅ Pending commits count
- ✅ Next planned task

**Critical decision points:**
- **Skipping ahead?** → Check prerequisites, warn if missing
- **Changing the plan?** → Update PROGRESS.md first, get approval
- **Will it cost money?** → Warn with estimate, get confirmation
- **Could it break something?** → Explain risk, suggest backup/test
- **Command fails?** → Check TROUBLESHOOTING.md (grep first!), stop, ask

---

## Modular Documentation System

**✅ Implemented October 2025:**
- PROGRESS.md is lightweight index (~685 lines, was 1,244)
- Phase files in `docs/phases/` contain detailed steps
- Workflow files contain specific procedures
- **Clear hierarchy:** PROGRESS.md → Phase file → Workflow file

**Phase files:**
- PHASE_0_DATA_COLLECTION.md (complete)
- PHASE_1_DATA_QUALITY.md (ready - multi-source integration planned)
- PHASE_2_AWS_GLUE.md (complete)
- PHASE_3_DATABASE.md (complete)
- PHASE_4_SIMULATION_ENGINE.md (complete - advanced simulation planned)
- PHASE_5_MACHINE_LEARNING.md (complete)
- PHASE_6_ENHANCEMENTS.md (complete)
- PHASE_7_BETTING_ODDS.md (pending - optional)

**Benefits:**
- ✅ Read only what you need (72% reduction in PROGRESS.md size)
- ✅ Faster file operations
- ✅ Reduced context usage (90%+ savings)
- ✅ Easier maintenance
- ✅ Scalable

---

## Navigation Between PROGRESS.md and Phase Files

**PROGRESS.md serves as the master index** - high-level status, directs to detailed phase files.

**Navigation pattern:**
1. Read PROGRESS.md (identify current task/phase)
2. Follow link to specific phase file
3. Read phase file for detailed implementation steps
4. Follow workflow links
5. Execute workflow steps

**Always start with PROGRESS.md** to understand:
- Current phase status (⏸️ PENDING, 🔄 IN PROGRESS, ✅ COMPLETE)
- What was completed in previous session
- What user wants to work on next
- Cost implications

---

## Phase File Reading Protocol

**Before starting any phase work:**
1. Read PROGRESS.md to identify current phase
2. Read the full phase file (e.g., `docs/phases/PHASE_3_DATABASE.md`)
3. Check for "⚠️ IMPORTANT - Before Starting This Phase" note
4. If present, ask user: "Should I add any workflows to this phase before beginning?"
5. Review existing workflow references
6. Follow workflow execution order

**During phase work:**
- Reference phase file for step-by-step instructions
- Follow workflow links for detailed procedures
- Update phase file status markers as work progresses
- Log commands to COMMAND_LOG.md per workflow #2

---

## Decision Tree for File Reading

**User says "let's work on [task]":**
1. Is it a new session? → Run `session_manager.sh start` first
2. Read PROGRESS.md → Find which phase contains this task
3. Read the specific phase file completely
4. Check for workflow recommendations needed
5. Execute task following phase file + workflows
6. Update PROGRESS.md status when phase/sub-phase completes

**User says "continue where we left off":**
1. Run `session_manager.sh start`
2. Read PROGRESS.md → Find first 🔄 IN PROGRESS or ⏸️ PENDING phase
3. Read that phase file completely
4. Ask user what they completed since last session
5. Update status accordingly
6. Suggest next sub-phase to work on

**User says "start Phase X":**
1. Read `docs/phases/PHASE_X_NAME.md` completely
2. Check for "⚠️ IMPORTANT" note at top
3. If present, ask: "Should I add any workflows to this phase before beginning?"
4. Wait for approval before proceeding
5. Follow phase file instructions step by step

---

## Context Management

**See docs/CONTEXT_MANAGEMENT_GUIDE.md for complete strategies.**

**Quick tips:**
- Session start: Read CLAUDE.md + PROGRESS.md + docs/README.md only (~1,085 lines)
- Don't read all phase files at once - read only what's needed
- Don't read all workflows upfront - read when referenced
- Use grep for large files (TROUBLESHOOTING.md, etc.), don't read fully
- Commit at 75% context, not 90%

**Context budget examples:**
- Minimal session: 1,085 lines (orientation only)
- Light work: 1,985 lines (+ 1 phase + 1 workflow)
- Moderate work: 2,585 lines (+ 1 phase + 3 workflows)
- Heavy work: 3,485 lines (+ 2 phases + 3 workflows)
- **Maximum recommended:** 4,000 lines (stay under 200K tokens)

---

## PROGRESS.md Update Protocol

**When to update PROGRESS.md:**
- ✅ When completing a sub-phase (⏸️ → ✅)
- ✅ When starting a new phase (⏸️ → 🔄)
- ✅ At session end ("Current Session Context")
- ❌ Don't update for minor tasks

**What to update:**
1. Phase/sub-phase status emoji
2. "Started" and "Completed" dates
3. "Current Session Context" section
4. Link to newly created phase file (if applicable)

**What NOT to update:**
- Detailed implementation steps (belong in phase files)
- Workflow procedures (belong in workflow files)
- Command outputs (belong in COMMAND_LOG.md)

---

## Consistency Check Before Session End

**Before Workflow #14 (Session End), verify:**
- [ ] PROGRESS.md status matches actual completion state
- [ ] Phase file status matches PROGRESS.md
- [ ] "Current Session Context" updated
- [ ] New workflow references added if needed
- [ ] COMMAND_LOG.md updated with session commands
- [ ] All files saved, no unsaved changes

**If inconsistencies found:**
1. Update PROGRESS.md first (master index)
2. Then update phase files to match
3. Then commit with clear message

---

## Session Startup Checklist

**Every new session:**

1. ✅ Read CLAUDE.md (this file) - orient to system
2. ✅ Read PROGRESS.md - identify current phase
3. ✅ Read docs/README.md - documentation map
4. ✅ Check "Current Session Context" in PROGRESS.md
5. ✅ Ask user: "What did you complete since our last session?"
6. ✅ Update PROGRESS.md "Current Session Context"
7. ✅ Ask user: "What would you like to work on today?"
8. ✅ Read relevant phase file for the task
9. ✅ Check for "⚠️ IMPORTANT" note
10. ✅ Begin work following phase file + workflows

**Do NOT:**
- ❌ Read all phase files at once
- ❌ Read all workflows upfront
- ❌ Start work before asking user what they completed
- ❌ Skip "Current Session Context" update

---

## Common Pitfalls to Avoid

**Context management mistakes:**
1. ❌ Reading all 8 phase files when user wants Phase 4 → ✅ Only read PHASE_4
2. ❌ Reading workflows 1-38 at session start → ✅ Read only when referenced
3. ❌ Re-reading files in same session → ✅ Track what you've read

**Documentation update mistakes:**
1. ❌ Updating phase files with detailed implementation notes → ✅ Use COMMAND_LOG.md
2. ❌ Forgetting "Current Session Context" → ✅ Always update at session end
3. ❌ Marking sub-phase complete when errors occurred → ✅ Only mark when successful

**Navigation mistakes:**
1. ❌ Starting work without checking prerequisites → ✅ Always verify first
2. ❌ Skipping "Should I add workflows?" question → ✅ Always ask for pending phases
3. ❌ Not following workflow execution order → ✅ Follow order in phase file

---

## File Size Reference (Context Planning)

**Know before you read:**

| File | Lines | Context Impact | When to Read |
|------|-------|----------------|--------------|
| CLAUDE.md | ~300 | Low (1%) | Every session start |
| PROGRESS.md | ~685 | Low (2-3%) | Every session start |
| docs/README.md | ~100 | Minimal (<1%) | Every session start |
| Phase files | ~400-500 | Low (2%) | Working on that phase |
| Workflow files | ~200-400 | Low (1-2%) | Referenced in phase |
| **⚠️ TROUBLESHOOTING.md** | 1,025 | High (5%) | **Grep only, read sections** |
| **⚠️ LESSONS_LEARNED.md** | 1,002 | High (5%) | **Only when requested** |
| **⚠️ TEMPORAL_QUERY_GUIDE.md** | 996 | High (4-5%) | **Only when implementing** |
| **⚠️ TESTING.md** | 862 | Medium (3-4%) | **Only when writing tests** |
| **⚠️ STYLE_GUIDE.md** | 846 | Medium (3-4%) | **Only for style questions** |

**Large files (⚠️) have lazy-loading warnings** - use grep, don't read fully

---

## Emergency Recovery

**See docs/EMERGENCY_RECOVERY.md for complete procedures.**

**If lost context mid-session:**
1. Stop immediately
2. Re-read PROGRESS.md "Current Session Context" (just this section)
3. Re-read current phase file
4. Ask user: "Where were we? What's the current state?"
5. Resume from known-good checkpoint

**If context approaching 90%:**
1. Stop reading files immediately
2. Commit current work
3. Update PROGRESS.md with current state
4. End session (Workflow #14)
5. Start fresh session with 0% context

---

## Critical Workflows

**Session Operations:** See docs/CLAUDE_OPERATIONAL_GUIDE.md
- Session initialization, progress tracking, command logging, doc triggers

**Context Management:** See docs/CONTEXT_MANAGEMENT_GUIDE.md
- Strategies for extending session length, reading protocols, context budgets

**Emergency Recovery:** See docs/EMERGENCY_RECOVERY.md
- Lost context, wrong file edits, session crashes, recovery procedures

**Scraper Monitoring:** See docs/SCRAPER_MONITORING_SYSTEM.md
- Overnight jobs, monitoring tools, completion analysis

**Security & Git:** See docs/SECURITY_PROTOCOLS.md
- Pre-commit security scans, pre-push inspection, credential rotation

**Archiving:** See docs/ARCHIVE_PROTOCOLS.md
- File deletion protocol, conversation archiving, finding past conversations

**Documentation System:** See docs/DOCUMENTATION_SYSTEM.md
- Documentation triggers, update schedules, monthly review

---

## Instructions for Claude

**Complete operational guides:**
- **docs/CLAUDE_OPERATIONAL_GUIDE.md** - Session init, progress tracking, command logging
- **docs/CONTEXT_MANAGEMENT_GUIDE.md** - Context optimization strategies
- **docs/EMERGENCY_RECOVERY.md** - Recovery procedures

---

## Project Overview

**This is a temporal panel data system, not a traditional sports analytics project.**

See `docs/PROJECT_VISION.md` for authoritative project vision and goals.
See `README.md` for quick start, architecture, and current status.

**Core capability:** Query cumulative NBA statistics at any exact moment in time with millisecond precision.

**Example:** "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"

---

## Essential Setup

See `docs/SETUP.md` for complete environment setup and verification.

**Quick activation:**
```bash
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws
```

---

## Critical Paths

See `docs/SETUP.md` for complete project paths and directory structure.

**Most critical:**
- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **S3 Bucket:** `s3://nba-sim-raw-data-lake` (146,115 files)
- **Archives:** `~/sports-simulator-archives/nba/`

---

## Architecture

See `README.md` for complete 5-phase pipeline architecture and key architectural decisions.

---

## Git & GitHub Configuration

See `QUICKSTART.md` for Git commands and `docs/SECURITY_PROTOCOLS.md` for complete security procedures.

**CRITICAL - Before ANY Git Operation:**

- **Before commit:** Run security scan (see `docs/SECURITY_PROTOCOLS.md`)
- **Before push:** Run `scripts/shell/pre_push_inspector.sh full` (7-step automated workflow)
- **NEVER commit without security scan** - check for AWS keys, secrets, IPs, passwords
- **NEVER push without user approval** - always ask "Ready to push to GitHub?"
- **If hook blocks commit/push:** Show user flagged lines, explain findings, get explicit bypass approval

---

## Common Commands

See `QUICKSTART.md` for all common commands (S3, database, AWS resources, daily workflow).

---

## Testing Quick Reference

**Complete Guide:** See Workflow #41 (`docs/claude_workflows/workflow_descriptions/41_testing_framework.md`)

**Run all test suites:**
```bash
# 1. Feature engineering readiness (fastest, 10-30s)
python notebooks/test_feature_engineering.py

# 2. Scraper monitoring system (medium, 30-60s)
bash scripts/monitoring/test_monitoring_system.sh --verbose

# 3. Temporal query functionality (slowest, 1-3 min)
pytest tests/test_temporal_queries.py -v
```

**Total runtime:** 2-5 minutes

---

## Scraper Operations Quick Reference

**Complete Guide:** See docs/SCRAPER_MANAGEMENT.md

**Launch Scrapers:**
```bash
bash scripts/monitoring/launch_scraper.sh  # Interactive
```

**Monitor Progress:**
```bash
bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 10  # Live tracking
```

**Related Workflows:**
- **Workflow #38:** Overnight Scraper Handoff Protocol
- **Workflow #39:** Scraper Monitoring Automation
- **Workflow #40:** Complete Scraper Operations Guide

---

## Data Structure

See `docs/DATA_STRUCTURE_GUIDE.md` for complete S3 bucket layout, data extraction strategy, and file characteristics.

---

## Data Source Baselines

See `docs/DATA_SOURCE_BASELINES.md` for verified baseline statistics from each data source.

**Purpose:** Cross-validation and quality checks when integrating multiple sources.

---

## Important Notes

**AWS Configuration & Credentials:** See `docs/SETUP.md`

**Cost Awareness (IMPORTANT):**
- **Current:** $2.74/month (S3 storage only)
- **Full deployment:** $95-130/month
- **Budget target:** $150/month
- **ALWAYS warn user before creating:**
  - RDS instances (~$29/month)
  - EC2 instances (~$5-15/month)
  - Glue jobs (~$13/month)
  - SageMaker notebooks (~$50/month)

See `PROGRESS.md` for complete cost breakdowns.

**Data Safety Protocol:**
- NEVER delete or modify S3 bucket contents without explicit user request
- NEVER drop database tables without user confirmation
- NEVER commit `.env`, credentials, or sensitive data
- Backup before destructive operations

See `docs/SECURITY_PROTOCOLS.md` for complete security procedures.

---

## Next Steps

See `PROGRESS.md` for detailed phase-by-phase implementation plan with time estimates, cost breakdowns, and step-by-step instructions.

---

## Development Workflow

See `QUICKSTART.md` for complete daily workflow, maintenance commands, archive management, and Makefile commands.

# CLAUDE.md

**Version:** 2.0 (Modular Documentation System)
**Last Updated:** October 6, 2025 - 11:30 PM
**System Status:** 8 phases (2 with enhancement plans), 38 workflows, 97+ workflow references

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Order - Follow This Sequence

**See `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md` for workflow index and execution order.**

**All detailed workflows are in: `docs/claude_workflows/workflow_descriptions/`**

**System now contains 38 modular workflows:**
- 🚀 Session Start & End workflows (#1, #14)
- 📋 Decision & Plan Change workflows
- 💻 Task Execution & File Creation workflows
- 🔒 Git Commit & Push workflows (security protocols)
- 🧪 Testing workflows (TDD, unit, integration, pre-deployment)
- 🔧 Environment Setup & Verification workflows
- 💰 Cost Management workflows (before creating, tracking, optimization)
- 💾 Backup & Recovery workflows
- 🔄 Maintenance Schedule workflows (weekly, monthly)
- 📊 Data Validation workflows (pre-ETL, pre-simulation, pre-ML)
- 🔍 Systematic Troubleshooting Protocol
- 🔐 Credential Rotation workflows
- ☁️ AWS Resource Setup workflows (Glue, RDS, EC2, SageMaker)
- 🗄️ Database Migration workflows
- 🔧 Makefile Quick Reference
- 🌙 **Overnight Scraper Handoff Protocol (#38)** - NEW

**Navigation pattern:**
```
1. Read PROGRESS.md (identify current task/phase)
2. Read docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md (find relevant workflow number)
3. Read docs/claude_workflows/workflow_descriptions/XX_workflow_name.md (get detailed steps)
4. Execute workflow steps
```

**Quick reference - Every session follows this order:**
1. Initialize session (`session_manager.sh start`) - show output to user
2. Orient to current state (read PROGRESS.md)
3. **🌙 Check overnight jobs** (if "Overnight jobs running" section exists in PROGRESS.md):
   - Follow Workflow #38: Overnight Scraper Handoff Protocol
   - Check process status, logs, output files
   - Document results or failure
4. Ask about completed work
5. Wait for user's task request
6. Follow decision workflow (check plan, prerequisites, costs, risks)
7. Execute task → Document outcome → Wait for confirmation
8. Update PROGRESS.md → Suggest next action
9. Follow security protocol for commits/pushes
10. Monitor context (auto-save at 75%, warn at 90%)

**Critical decision points:**
- **Skipping ahead?** → Check prerequisites, warn if missing
- **Changing the plan?** → Update PROGRESS.md first, get approval
- **Will it cost money?** → Warn with estimate, get confirmation
- **Could it break something?** → Explain risk, suggest backup/test approach
- **Command fails?** → Check TROUBLESHOOTING.md, stop, ask for guidance

**How workflows integrate with PROGRESS.md:**

**✅ NEW MODULAR STRUCTURE (Implemented Oct 2, 2025):**
- PROGRESS.md is now a lightweight index (~350 lines, was 1,244 lines)
- Individual phase files in `docs/phases/` contain detailed implementation steps
- Phase files explicitly reference workflow numbers (e.g., "Follow workflow #24")
- Clear hierarchy: PROGRESS.md → Phase file → Workflow file

**Phase files:**
- PHASE_0_DATA_COLLECTION.md (complete)
- PHASE_1_DATA_QUALITY.md (ready to implement - multi-source integration planned)
- PHASE_2_AWS_GLUE.md (complete)
- PHASE_3_DATABASE.md (complete)
- PHASE_4_SIMULATION_ENGINE.md (complete - advanced simulation framework planned)
- PHASE_5_MACHINE_LEARNING.md (complete)
- PHASE_6_ENHANCEMENTS.md (complete)
- PHASE_7_BETTING_ODDS.md (pending - optional future enhancement)

**Benefits:**
- ✅ Read only what you need (72% reduction in PROGRESS.md size)
- ✅ Faster file operations (350 lines vs 1,244)
- ✅ Reduced context usage (90%+ savings)
- ✅ Easier maintenance (update one phase without affecting others)
- ✅ Scalable (easy to add new phases)
- ✅ Clear separation of concerns

---

## Navigation Between PROGRESS.md and Phase Files

**PROGRESS.md serves as the master index** - it shows high-level status and directs to detailed phase files.

**Navigation pattern:**
1. Read PROGRESS.md (identify current task/phase)
2. Follow link to specific phase file (e.g., `docs/phases/PHASE_3_DATABASE.md`)
3. Read phase file for detailed implementation steps and workflow references
4. Follow workflow links to `docs/claude_workflows/workflow_descriptions/XX_workflow_name.md`
5. Execute workflow steps

**Always start with PROGRESS.md** to understand:
- Current phase status (⏸️ PENDING, 🔄 IN PROGRESS, ✅ COMPLETE)
- What was completed in previous session
- What user wants to work on next
- Cost implications of next steps

---

## Phase File Reading Protocol

**Before starting any phase work:**
1. Read PROGRESS.md to identify current phase
2. Read the full phase file (e.g., `docs/phases/PHASE_3_DATABASE.md`)
3. Check for the "⚠️ IMPORTANT - Before Starting This Phase" note
4. If present, ask user: "Should I add any workflows to this phase before beginning?"
5. Review existing workflow references in the phase file
6. Follow workflow execution order as specified in phase file

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

## Context Management with Modular Docs

**Why this matters:**
- Old PROGRESS.md: 9,533 lines (massive context usage)
- New system: Average 400 lines per file (90%+ context savings)

**Context-efficient reading strategy:**
1. **Always read PROGRESS.md first** (350 lines) - establishes orientation
2. **Read only the relevant phase file** (400-600 lines) - get detailed steps
3. **Read only the workflows referenced in current sub-phase** (200-400 lines each)
4. **Don't read all phase files at once** - wait for user to specify which phase

**Example efficient session:**
- Read PROGRESS.md: 350 lines
- Read PHASE_3_DATABASE.md: 450 lines
- Read Workflow #32 (RDS Connection): 300 lines
- **Total: 1,100 lines vs 9,533 lines (88% savings)**

**When to read multiple files:**
- User explicitly asks to review all phases
- Working on cross-phase documentation updates
- Creating new workflows that span multiple phases
- Otherwise: Read only what's needed for current task

---

## PROGRESS.md Update Protocol

**When to update PROGRESS.md:**
- ✅ When completing a sub-phase (update status from ⏸️ to ✅)
- ✅ When starting a new phase (update status from ⏸️ to 🔄)
- ✅ At session end (update "Current Session Context")
- ❌ Don't update for minor tasks or intermediate steps

**What to update in PROGRESS.md:**
1. Phase/sub-phase status emoji (⏸️ → 🔄 → ✅)
2. "Started" and "Completed" dates in phase summary
3. "Current Session Context" section
4. Link to newly created phase file (if applicable)

**What NOT to update in PROGRESS.md:**
- Detailed implementation steps (those belong in phase files)
- Workflow procedures (those belong in workflow files)
- Command outputs (those belong in COMMAND_LOG.md)

---

## Consistency Check Before Session End

**Before running Workflow #14 (Session End), verify:**
- [ ] PROGRESS.md status matches actual completion state
- [ ] Phase file status matches PROGRESS.md
- [ ] "Current Session Context" in PROGRESS.md is updated
- [ ] New workflow references added to phase files if needed
- [ ] COMMAND_LOG.md updated with session commands
- [ ] All files saved and no unsaved changes

**If inconsistencies found:**
1. Update PROGRESS.md first (master index)
2. Then update phase files to match
3. Then commit changes with clear message

---

## Creating New Phase Files

**If you need to create a new phase file (rare):**

Use this template structure:
```markdown
# Phase X: [Name]

**Status:** ⏸️ PENDING
**Prerequisites:** [List]
**Estimated Time:** [Hours]
**Estimated Cost:** [$/month]

---

> **⚠️ IMPORTANT - Before Starting This Phase:**
>
> **Ask Claude:** "Should I add any workflows to this phase before beginning?"

---

## Overview
[Description]

## Prerequisites
[Checklist]

## Implementation Steps

### Sub-Phase X.1: [Name]
**Status:** ⏸️ PENDING
**Time Estimate:** [Hours]

**Follow these workflows:**
- Workflow #XX ([Name](../claude_workflows/workflow_descriptions/XX_name.md))
  - **When to run:** [When]
  - **Purpose:** [Why]

[Implementation details]

**Validation:**
- [ ] [Checklist items]

---

## Success Criteria
[When complete checklist]

---

## Next Steps
[What comes after]

---

*Last updated: [Date]*
```

**Then:**
1. Link from PROGRESS.md
2. Add to phase list in CLAUDE.md
3. Create workflows as needed

---

## File Reading Efficiency Metrics

**Track your context usage:**

**Inefficient approach (old way):**
- Read all of PROGRESS.md: 9,533 lines
- Read all workflows at once: 13,212 lines (36 workflows)
- **Total: 22,745 lines** ❌

**Efficient approach (new way):**
- Read CLAUDE.md: 291 lines
- Read PROGRESS.md: 380 lines
- Read relevant phase file: 450 lines
- Read 2-3 relevant workflows: 600-900 lines
- **Total: 1,721-2,021 lines** ✅

**Context savings: 91-92%**

**Remember:**
- Don't read files "just in case"
- Don't read all phases when working on one
- Don't read all workflows upfront
- Do read incrementally as needed

---

## Session Startup Checklist

**Every new session, follow this exact sequence:**

1. ✅ Read CLAUDE.md (this file) - orient to the system
2. ✅ Read PROGRESS.md - identify current phase and last session's work
3. ✅ Check "Current Session Context" in PROGRESS.md
4. ✅ Ask user: "What did you complete since our last session?"
5. ✅ Update PROGRESS.md "Current Session Context" based on user response
6. ✅ Ask user: "What would you like to work on today?"
7. ✅ Read relevant phase file for the task
8. ✅ Check for "⚠️ IMPORTANT" note at top of phase file
9. ✅ If present, ask about adding workflows before proceeding
10. ✅ Begin work following phase file + workflow references

**Do NOT:**
- ❌ Read all phase files at once
- ❌ Read all workflows upfront
- ❌ Start work before asking user what they completed
- ❌ Skip the "Current Session Context" update

---

## Common Pitfalls to Avoid

**Context management mistakes:**
1. ❌ Reading all 6 phase files when user wants to work on Phase 4
   - ✅ Only read PHASE_4 file
2. ❌ Reading workflows 1-36 at session start "just in case"
   - ✅ Read workflows only when referenced in current sub-phase
3. ❌ Re-reading files you already read in this session
   - ✅ Keep track of what you've read, don't re-read unnecessarily

**Documentation update mistakes:**
1. ❌ Updating phase files with detailed implementation notes
   - ✅ Phase files contain planning, COMMAND_LOG.md contains execution
2. ❌ Forgetting to update "Current Session Context" at session end
   - ✅ Always update before running Workflow #14 (Session End)
3. ❌ Marking sub-phase complete when errors occurred
   - ✅ Only mark complete when fully successful

**Navigation mistakes:**
1. ❌ Starting work without checking prerequisites in phase file
   - ✅ Always verify prerequisites before starting phase
2. ❌ Skipping the "Should I add workflows?" question for pending phases
   - ✅ Always ask when you see the ⚠️ IMPORTANT note
3. ❌ Not following workflow execution order specified in phase file
   - ✅ Follow workflows in the order listed

---

## File Size Reference (Context Planning)

**Know before you read:**

| File | Lines | Read Time | When to Read |
|------|-------|-----------|--------------|
| CLAUDE.md | ~550 | Always | Every session start |
| PROGRESS.md | ~410 | Always | Every session start |
| PHASE_1 | ~300 | As needed | Working on Phase 1 |
| PHASE_2 | ~345 | As needed | Working on Phase 2 |
| PHASE_3 | ~407 | As needed | Working on Phase 3 |
| PHASE_4 | ~485 | As needed | Working on Phase 4 |
| PHASE_5 | ~489 | As needed | Working on Phase 5 |
| PHASE_6 | ~427 | As needed | Working on Phase 6 |
| Workflow (avg) | ~300 | As needed | Referenced in phase |

**Typical session context usage:**
- Minimal session: 960 lines (CLAUDE.md + PROGRESS.md)
- Light work: 1,750 lines (+ 1 phase file)
- Moderate work: 2,350 lines (+ 1 phase + 2 workflows)
- Heavy work: 3,200 lines (+ 2 phases + 3 workflows)

**Maximum recommended:** 4,000 lines per session (stay well under 200K token limit)

---

## Quick Reference Card

**Copy this to start of every response when you're uncertain:**

```
Session checklist:
[ ] Read CLAUDE.md ✓
[ ] Read PROGRESS.md ✓
[ ] Asked user what they completed
[ ] Updated "Current Session Context"
[ ] Asked user what they want to work on
[ ] Read relevant phase file
[ ] Checked for workflow recommendations
[ ] Ready to begin work
```

**Decision points:**
- User wants to work on [task] → Which phase? → Read that phase file
- Phase file says "Follow workflow #X" → Read workflow #X
- Workflow says "Log to COMMAND_LOG.md" → Use Workflow #2
- Task complete → Update PROGRESS.md → Run Workflow #14
- Session ending → Consistency check → Update context → Commit if needed

---

## Emergency Recovery

**If something goes wrong mid-session:**

### Lost context / confused about state:
1. Stop immediately
2. Re-read PROGRESS.md "Current Session Context"
3. Re-read current phase file
4. Ask user: "Where were we? What's the current state?"
5. Resume from a known-good checkpoint

### Made changes to wrong file:
1. Check git status: `git status`
2. Review changes: `git diff`
3. If wrong, revert: `git checkout -- <file>`
4. Apologize to user, explain what happened
5. Start over with correct file

### Updated PROGRESS.md incorrectly:
1. Check git diff for PROGRESS.md
2. Compare against phase file status
3. If mismatch, revert and update correctly
4. Always update PROGRESS.md last (after phase work)

### Forgot to log commands:
1. Recreate command history from bash history
2. Add to COMMAND_LOG.md retroactively
3. Note that it was added retroactively
4. Set reminder to log commands in real-time next time

---

## Critical Workflows (See Detailed Docs)

**Security & Git:** See `docs/SECURITY_PROTOCOLS.md`
- Pre-commit security scans
- Pre-push inspection workflow (automated via `scripts/shell/pre_push_inspector.sh`)
- Credential rotation schedules
- GitHub secret scanning setup

**Archiving & Conversation History:** See `docs/ARCHIVE_PROTOCOLS.md`
- File deletion protocol (archive first)
- Conversation archiving (auto at 75%/90% context)
- Finding past conversations
- Auto-generated commit logs

**Session Startup:** See `docs/SESSION_INITIALIZATION.md`
- Run `session_manager.sh start` automatically
- Progress tracking protocol
- When to update documentation
- Command logging procedures

**Documentation System:** See `docs/DOCUMENTATION_SYSTEM.md`
- Documentation trigger system
- Update schedules (manual vs automated)
- Monthly review checklist
- Workflow documentation system

## Instructions for Claude

**Session Initialization & Daily Workflows:** See `docs/CLAUDE_SESSION_INIT.md`

**Progress Tracking:** See `docs/CLAUDE_PROGRESS_TRACKING.md`

**Command Logging:** See `docs/CLAUDE_COMMAND_LOGGING.md`

**Documentation Quick Reference:** See `docs/CLAUDE_DOCUMENTATION_QUICK_REF.md`

## Project Overview

**This is a temporal panel data system, not a traditional sports analytics project.**

See `docs/PROJECT_VISION.md` for the authoritative project vision and goals.
See `README.md` for quick start, architecture, and current status.

**Core capability:** Query cumulative NBA statistics at any exact moment in time with millisecond precision.

**Example:** "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"

## Essential Setup

See `docs/SETUP.md` for complete environment setup and verification.

**Quick activation:**
```bash
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws
```

## Critical Paths

See `docs/SETUP.md` for complete project paths and directory structure.

**Most critical:**
- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **S3 Bucket:** `s3://nba-sim-raw-data-lake` (146,115 files)
- **Archives:** `~/sports-simulator-archives/nba/`

## Architecture

See `README.md` for complete 5-phase pipeline architecture and key architectural decisions.

## Git & GitHub Configuration

See `QUICKSTART.md` for Git commands and `docs/SECURITY_PROTOCOLS.md` for complete security procedures.

**CRITICAL - Before ANY Git Operation:**

- **Before commit:** Run security scan (see `docs/SECURITY_PROTOCOLS.md` for scan commands and protocols)
- **Before push:** Run `scripts/shell/pre_push_inspector.sh full` (7-step automated workflow)
- **NEVER commit without security scan** - check for AWS keys, secrets, IPs, passwords
- **NEVER push without user approval** - always ask "Ready to push to GitHub?"
- **If hook blocks commit/push:** Show user flagged lines, explain findings, get explicit bypass approval

See `docs/SECURITY_PROTOCOLS.md` for:
- Complete security scan bash commands
- Whitelist patterns (safe vs unsafe)
- Security check protocol (step-by-step)
- Pre-push inspection workflow (repository cleanup)
- Credential rotation schedules
- GitHub secret scanning setup

## Common Commands

See `QUICKSTART.md` for all common commands (S3, database, AWS resources, daily workflow).

## Data Structure

See `docs/DATA_STRUCTURE_GUIDE.md` for complete S3 bucket layout, data extraction strategy, and file characteristics.

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

## Next Steps

See `PROGRESS.md` for detailed phase-by-phase implementation plan with time estimates, cost breakdowns, and step-by-step instructions.

## Development Workflow

See `QUICKSTART.md` for complete daily workflow, maintenance commands, archive management, and Makefile commands.
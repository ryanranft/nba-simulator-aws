# CLAUDE.md

**Version:** 3.1 (Phase Index System)
**Last Updated:** October 11, 2025
**System Status:** 8 phases (2 with enhancement plans), 40 workflows, 97+ workflow references

This file provides core guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Quick Start - Every Session

**Always read these 3 files at session start:**
1. **CLAUDE.md** (this file, ~350 lines) - Core instructions
2. **PROGRESS.md** (~390 lines) - Current project state
3. **docs/README.md** (~100 lines) - Documentation index

**Total: ~840 lines (4% context)** - Leaves 96% for actual work

---

## Workflow Order

**See `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md` for workflow index and execution order.**

**All detailed workflows:** `docs/claude_workflows/workflow_descriptions/`

**System contains 40 modular workflows** covering session operations, git/security, testing, cost management, backup/recovery, data validation, troubleshooting, AWS resource setup, scraper monitoring, and overnight handoffs.

**Navigation pattern:**
```
PROGRESS.md → PHASE_N_INDEX.md → phase_N/N.M_name.md → workflows → execute
```

**Quick reference - Every session:**
1. **Initialize** (`bash scripts/shell/session_manager.sh start`) - auto-checks credentials, overnight jobs
2. **Ask user** what they completed since last session
3. If work completed → Update PROGRESS.md
4. If 'none' → Proceed with "Next planned task"
5. Execute task → Document outcome
6. Follow security protocol for commits/pushes
7. Monitor context (auto-save at 75%, warn at 90%)

**Critical decision points:**
- **Skipping ahead?** → Check prerequisites first
- **Changing the plan?** → Update PROGRESS.md, get approval
- **Will it cost money?** → Warn with estimate
- **Could it break something?** → Explain risk, suggest backup
- **Command fails?** → grep TROUBLESHOOTING.md, stop, ask

---

## Phase Index Documentation System

**✅ Implemented October 2025** - Hierarchical modular documentation:

**Structure:**
- **PROGRESS.md** (~390 lines) - Master index, high-level status
- **PHASE_N_INDEX.md** (~150 lines each) - Phase overview + sub-phase table
- **phase_N/** subdirectories - Individual sub-phase files (300-800 lines)
- **Workflows** - Specific procedures (200-400 lines)

**Phase indexes:**
- PHASE_0_INDEX.md (initial complete, expansion ready - 4 sub-phases)
- PHASE_1_INDEX.md through PHASE_7_INDEX.md (1-2 sub-phases each)

**Sub-phase naming:** `N.M_name.md` (e.g., `0.0_initial_data_collection.md`, `1.1_multi_source_integration.md`)

**Special structure:** Basketball Reference expansion at `phase_0/0.1_basketball_reference/` (13-tier structure, 234 data types)

**Benefits:** 64% reduction in PROGRESS.md size, 78% reduction in phase navigation context, 96% context available for work

---

## Navigation Protocol

**Standard flow:**
1. Read PROGRESS.md (current status)
2. Read PHASE_N_INDEX.md (phase overview + sub-phase table)
3. Read phase_N/N.M_name.md (sub-phase implementation)
4. Follow workflow links
5. Execute steps

**Always start with PROGRESS.md** to understand status, previous session work, user intent, and cost implications.

---

## Phase File Reading Protocol

**Before starting any phase:**
1. Read PROGRESS.md → Identify current phase
2. Read PHASE_N_INDEX.md → Review sub-phases
3. Read specific phase_N/N.M_name.md
4. Check for "⚠️ IMPORTANT" notes
5. Follow workflow execution order

**During work:** Update sub-phase file → Update phase index → Update PROGRESS.md (when full phase completes) → Log commands to COMMAND_LOG.md

---

## Decision Tree for File Reading

**"Let's work on [task]":**
- New session? Run `session_manager.sh start` first
- Read PROGRESS.md → Find phase
- Read PHASE_N_INDEX.md + specific sub-phase file
- Execute following sub-phase + workflows

**"Continue where we left off":**
- Run `session_manager.sh start` (shows next task)
- Find first 🔄 IN PROGRESS or ⏸️ PENDING
- Ask what was completed
- Suggest next sub-phase

**"Start Phase X":**
- Read PHASE_X_INDEX.md completely
- Check for "⚠️ IMPORTANT" notes
- Ask: "Should I add workflows first?"
- Wait for approval, then proceed

---

## Context Management

**See docs/CONTEXT_MANAGEMENT_GUIDE.md for complete strategies.**

**Quick tips:**
- Session start: Read only CLAUDE.md + PROGRESS.md + docs/README.md (~840 lines)
- Read phase indexes/sub-phases only when needed
- Read workflows only when referenced
- Grep large files (TROUBLESHOOTING.md), don't read fully
- Commit at 75% context

**Context budgets:**
- Minimal: 840 lines (4%)
- Light: 1,490 lines (+ 1 phase index + 1 sub-phase)
- Moderate: 2,040 lines (+ 1 phase + 1 sub-phase + 2 workflows)
- Heavy: 3,290 lines (+ 2 phases + 2 sub-phases + 2 workflows)
- **Maximum:** 4,000 lines (20K tokens)

---

## Update Protocol

**Update hierarchy:**
1. **Sub-phase completes** → Update phase_N/N.M_name.md, then PHASE_N_INDEX.md
2. **Full phase completes** → Update PHASE_N_INDEX.md, then PROGRESS.md
3. **Session ends** → Update PROGRESS.md "Current Session Context"

**What to update in PROGRESS.md:**
- Phase status emoji (⏸️ → 🔄 → ✅) for full phases only
- "Started" and "Completed" dates
- "Current Session Context"

**What NOT to update in PROGRESS.md:**
- Sub-phase completion (belongs in phase index)
- Implementation details (belong in sub-phase files)
- Commands (belong in COMMAND_LOG.md)

---

## Session End Consistency Check

**Before Workflow #14 (Session End):**
- [ ] Sub-phase file status matches actual completion
- [ ] Phase index matches sub-phases
- [ ] PROGRESS.md matches phase indexes
- [ ] "Current Session Context" updated
- [ ] COMMAND_LOG.md updated
- [ ] All files saved

**If inconsistent:** Update sub-phase file first → phase index → PROGRESS.md → commit

---

## Session Startup Checklist

**Every new session:**
1. Read CLAUDE.md (orient)
2. Read PROGRESS.md (identify phase)
3. Read docs/README.md (doc map)
4. Check "Current Session Context"
5. Ask: "What did you complete?"
6. Update "Current Session Context"
7. Ask: "What to work on today?"
8. Read PHASE_N_INDEX.md
9. Read phase_N/N.M_name.md
10. Check "⚠️ IMPORTANT" notes
11. Begin work

**Do NOT:** Read all phases/workflows upfront, start before asking user what completed, skip context update

---

## Common Pitfalls

**Context mistakes:**
- Reading all 8 indexes when need 1 → Read only needed index
- Reading all sub-phases → Read only current one
- Reading workflows 1-40 at start → Read when referenced

**Update mistakes:**
- Updating PROGRESS.md for sub-phase → Update phase index instead
- Forgetting "Current Session Context" → Always update
- Marking complete when errors → Only when successful

**Navigation mistakes:**
- Skipping prerequisites → Always verify first
- Skipping phase index → Read for context
- Ignoring workflow order → Follow order

---

## File Sizes (Context Planning)

**Always read:**
- CLAUDE.md: ~350 lines (1.75%)
- PROGRESS.md: ~390 lines (1.95%)
- docs/README.md: ~100 lines (0.5%)
- **Total:** ~840 lines (4.2%)

**Read as needed:**
- PHASE_N_INDEX.md: ~150 lines (0.75%)
- Sub-phase files: ~300-800 lines (1.5-4%)
- Workflows: ~200-400 lines (1-2%)

**⚠️ Grep only (don't read fully):**
- TROUBLESHOOTING.md: 1,025 lines (5%)
- LESSONS_LEARNED.md: 1,002 lines (5%)
- TEMPORAL_QUERY_GUIDE.md: 996 lines (5%)
- TESTING.md: 862 lines (4%)
- STYLE_GUIDE.md: 846 lines (4%)

**Full file size reference:** docs/CONTEXT_MANAGEMENT_GUIDE.md

---

## Emergency Recovery

**See docs/EMERGENCY_RECOVERY.md for complete procedures.**

**Lost context:** Stop → Re-read PROGRESS.md "Current Session Context" → Re-read phase files → Ask user current state → Resume from checkpoint

**Context approaching 90%:** Stop reading → Commit work → Update PROGRESS.md → End session (#14) → Start fresh

---

## Critical Workflows

- **Session Operations:** docs/CLAUDE_OPERATIONAL_GUIDE.md
- **Context Management:** docs/CONTEXT_MANAGEMENT_GUIDE.md
- **Emergency Recovery:** docs/EMERGENCY_RECOVERY.md
- **Scraper Monitoring:** docs/SCRAPER_MONITORING_SYSTEM.md
- **Security & Git:** docs/SECURITY_PROTOCOLS.md
- **Archiving:** docs/ARCHIVE_PROTOCOLS.md
- **Documentation System:** docs/DOCUMENTATION_SYSTEM.md

---

## Project Overview

**This is a temporal panel data system, not traditional sports analytics.**

See `docs/PROJECT_VISION.md` for vision, `README.md` for architecture.

**Core capability:** Query cumulative NBA statistics at any exact moment in time with millisecond precision.

**Example:** "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"

---

## Essential Setup

See `docs/SETUP.md` for complete setup.

**Quick activation:**
```bash
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws
```

---

## Critical Paths

- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **S3 Bucket:** `s3://nba-sim-raw-data-lake` (70,522 files)
- **Archives:** `~/sports-simulator-archives/nba/`

See `docs/SETUP.md` for complete paths.

---

## Architecture

See `README.md` for complete 5-phase pipeline architecture and key decisions.

---

## Git & GitHub Configuration

See `QUICKSTART.md` for commands, `docs/SECURITY_PROTOCOLS.md` for procedures.

**CRITICAL - Before ANY Git Operation:**
- **Before commit:** Run security scan
- **Before push:** Run `scripts/shell/pre_push_inspector.sh full`
- **NEVER commit without security scan** (AWS keys, secrets, IPs)
- **NEVER push without user approval** - always ask first
- **If hook blocks:** Show flagged lines, explain, get explicit bypass approval

---

## Common Commands

See `QUICKSTART.md` for all commands (S3, database, AWS resources, daily workflow).

---

## Testing Quick Reference

**Complete Guide:** Workflow #41 (`docs/claude_workflows/workflow_descriptions/41_testing_framework.md`)

**Run all suites:**
```bash
# Feature engineering (10-30s)
python notebooks/test_feature_engineering.py

# Scraper monitoring (30-60s)
bash scripts/monitoring/test_monitoring_system.sh --verbose

# Temporal queries (1-3 min)
pytest tests/test_temporal_queries.py -v
```

**Total:** 2-5 minutes

---

## Scraper Operations

**Complete Guide:** docs/SCRAPER_MANAGEMENT.md

**Launch:** `bash scripts/monitoring/launch_scraper.sh`

**Monitor:** `bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 10`

**Workflows:** #38 (Overnight Handoff), #39 (Monitoring Automation), #40 (Complete Operations)

---

## Data Structure

See `docs/DATA_STRUCTURE_GUIDE.md` for S3 bucket layout, extraction strategy, file characteristics.

---

## Data Source Baselines

See `docs/DATA_SOURCE_BASELINES.md` for verified statistics from each source.

**Purpose:** Cross-validation and quality checks for multi-source integration.

---

## Important Notes

**AWS Configuration:** See `docs/SETUP.md`

**Cost Awareness:**
- **Current:** $2.74/month (S3 only)
- **Full deployment:** $95-130/month
- **Budget:** $150/month
- **ALWAYS warn before creating:** RDS (~$29/mo), EC2 (~$5-15/mo), Glue (~$13/mo), SageMaker (~$50/mo)

See `PROGRESS.md` for cost breakdowns.

**Data Safety:**
- NEVER delete/modify S3 without explicit request
- NEVER drop database tables without confirmation
- NEVER commit `.env`, credentials, or sensitive data
- Backup before destructive operations

See `docs/SECURITY_PROTOCOLS.md` for procedures.

---

## Next Steps

See `PROGRESS.md` for phase-by-phase plan with time estimates, costs, and step-by-step instructions.

---

## Development Workflow

See `QUICKSTART.md` for daily workflow, maintenance, archive management, Makefile commands.

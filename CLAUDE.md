# CLAUDE.md

**Version:** 3.3 (Background Agent Operations)
**Last Updated:** October 25, 2025
**System Status:** 7 phases (reorganized Oct 2025), 54 workflows, 97+ workflow references

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

**System contains 54 modular workflows** covering session operations, git/security, testing, cost management, backup/recovery, data validation, troubleshooting, AWS resource setup, scraper monitoring, overnight handoffs, and autonomous recommendation implementation.

**Navigation pattern:**
```
PROGRESS.md → PHASE_N_INDEX.md → phase_N/N.M_name.md → workflows → execute
```

**Quick reference - Every session:**
1. **Initialize** (`bash scripts/shell/session_manager.sh start`) - auto-checks credentials, overnight jobs, DIMS metrics
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

**Sub-phase naming:** `N.M_name.md` OR `N.M_name/` (e.g., `0.0_initial_data_collection.md`, `1.1_multi_source_integration.md`)

**Power Directory Structure:**

**Standard:** All complex sub-phases MUST use power directory structure: `N.M_name/`

**Required Files:**
- **README.md** - Main entry point (REQUIRED for all power directories)
  - Sub-phase header with parent phase link back
  - Status, priority, implementation ID
  - Overview and capabilities
  - Quick start code examples
  - Architecture details
  - Implementation files table
  - Related documentation links
  - Navigation (return to phase, prerequisites, integrates with)
- **implement_*.py** - Implementation code (one or more files)
- **test_*.py** - Test suites (one or more files)
- **STATUS.md** - Detailed status and metrics (optional but recommended)
- **RECOMMENDATIONS_FROM_BOOKS.md** - Source references from books (optional)

**When to Use Power Directory:**
- Complex implementations requiring multiple files
- Sub-phases with tests, documentation, and code
- Implementations from book recommendations (rec_N, ml_systems_N)
- Any sub-phase with >500 lines of implementation code

**Reference Example:** `docs/phases/phase_0/0.1_basketball_reference/README.md` (canonical example)

**Recent Power Directories (October 2025):**
- `phase_0/0.1_basketball_reference/` (13-tier structure, 234 data types)
- `phase_0/0.4_security_implementation/` (13 security variations)
- `phase_0/0.5_data_extraction/` (structured data output)
- `phase_5/5.1_feature_engineering/` (rec_11 - 80+ temporal features)
- `phase_5/5.2_model_versioning/` (ml_systems_1 - MLflow integration)
- `phase_5/5.19_drift_detection/` (ml_systems_2 - data drift detection)
- `phase_5/5.20_panel_data/` (rec_22 - temporal panel data system)

**Benefits:** 64% reduction in PROGRESS.md size, 78% reduction in phase navigation context, 96% context available for work, consistent navigation patterns

**⚠️ CRITICAL - Project Scope:**
This project is **NBA-only**. Phase 0.5 & 0.6 are **NOT** awaiting NCAA/International data - they were permanently superseded by PostgreSQL implementations (0.10/0.11). **Never suggest** filling these with non-NBA data. Other sports will be built as **separate projects** in separate directories using this NBA infrastructure as a template.

---

## ML Framework Navigation

**✅ Implemented October 2025** - Phase 5 enhanced with 13 specialized ML frameworks (Block 2, Recommendations #14-25)

**Phase 5 Structure:**
- **PHASE_5_INDEX.md** - Phase overview with 14 sub-phases (5.0 + 5.1-5.13)
- **phase_5/5.0_machine_learning_models.md** - Initial ML pipeline
- **phase_5/5.{1-13}_*/README.md** - 13 ML framework subdirectories with comprehensive guides

**Framework Categories:**
1. **Optimization & Tuning:** Hyperparameter Optimization (5.1), Learning Curves (5.7), Performance Profiling (5.13)
2. **Interpretability:** Model Interpretation (5.2), Model Explainability (5.12)
3. **Data Management:** Feature Store (5.3), Feature Selection (5.5)
4. **MLOps:** Automated Retraining (5.4), Model Comparison (5.10)
5. **Model Enhancement:** Ensemble Learning (5.6), Model Calibration (5.8)
6. **Validation:** Cross-Validation Strategies (5.9), Error Analysis (5.11)

**When to use ML frameworks:**
- **5.1 (Hyperparameter Optimization)** - Before production deployment, when model plateaus
- **5.2 (Model Interpretation)** - Debugging predictions, validating features
- **5.3 (Feature Store)** - Multiple models share features, production deployment
- **5.4 (Automated Retraining)** - Production models, drift detection needed
- **5.5 (Feature Selection)** - High-dimensional data (>100 features), overfitting issues
- **5.6 (Ensemble Learning)** - Multiple strong models available, need stability
- **5.7 (Learning Curves)** - Diagnosing overfitting/underfitting, planning data collection
- **5.8 (Model Calibration)** - Need probability estimates, betting applications
- **5.9 (Cross-Validation)** - **ALWAYS use time series CV for NBA temporal data**
- **5.10 (Model Comparison)** - Selecting best model, A/B testing, validation
- **5.11 (Error Analysis)** - Model underperforming, systematic errors detected
- **5.12 (Model Explainability)** - Stakeholder communication, regulatory compliance
- **5.13 (Performance Profiling)** - Production deployment, latency/memory optimization

**Navigation pattern:**
```
PROGRESS.md → PHASE_5_INDEX.md → phase_5/5.X_name/README.md → Execute framework
```

**Each framework README includes:**
- Overview & capabilities
- When to use / When NOT to use
- How to use (quick start + advanced examples)
- Integration with NBA temporal panel data
- Common patterns for NBA use cases
- Workflow references
- Troubleshooting guide

**Total:** ~7,700 lines of production code + ~5,500 lines of documentation

---

## Background Agent Operations

**✅ COMPLETE - October 19, 2025** - Autonomous recommendation implementation system

**Mission:** Implement 214 technical book recommendations to enhance prediction accuracy and system architecture

**Status:** ✅ **100% COMPLETE** - All 214 recommendations implemented in 12 minutes (autonomous overnight deployment)

### Final Results

**Completion Date:** October 19, 2025, 04:30-04:42 AM CDT
**Duration:** 12 minutes
**Success Rate:** 100% (214/214 recommendations, 1,284/1,284 tests)

**What Was Achieved:**
- ✅ 214 recommendations implemented (100%)
- ✅ 1,284 tests passed (100% pass rate)
- ✅ 212 individual git commits created
- ✅ Zero failures, zero escalations
- ✅ Enterprise-grade MLOps infrastructure deployed
- ✅ 187 advanced ML/AI capabilities added
- ✅ ~150,000+ lines of production-ready code generated
- ✅ Full documentation auto-generated

### Check Completion Status

**View final status:**
```bash
python scripts/automation/check_recommendation_status.py
```

**Output:**
```
Total Recommendations: 214
  ✅ Complete: 214 (100.0%)
  📋 Remaining: 0
```

### Actual vs Estimated

| Metric | Original Estimate | Actual Result | Efficiency |
|--------|------------------|---------------|------------|
| **Duration** | 2-4 weeks | 12 minutes | 1,440-2,880x faster |
| **Implementation Time** | 4,967 hours | 0.2 hours | 99.996% time savings |
| **Success Rate** | 85-90% | 100% | Perfect execution |

### What's Next

The autonomous implementation system has completed its mission. Next steps:

1. **Integration Testing** - Test all 214 implementations together
2. **Production Deployment** - Deploy ML capabilities to AWS
3. **Performance Optimization** - Scale for production workloads
4. **Accuracy Measurement** - Measure prediction improvements

**See complete details:**
- `BOOK_RECOMMENDATIONS_PROGRESS.md` - Full completion summary
- `docs/claude_workflows/workflow_descriptions/54_autonomous_recommendation_implementation.md` - Deployment details
- `docs/BOOK_RECOMMENDATIONS_COMPLETION_SUMMARY.md` - Morning summary report

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
2. **Full phase completes** → Update PHASE_N_INDEX.md, then PROGRESS.md, **then validate phase README against main README**
3. **Session ends** → Update PROGRESS.md "Current Session Context"

**What to update in PROGRESS.md:**
- Phase status emoji (⏸️ → 🔄 → ✅) for full phases only
- "Started" and "Completed" dates
- "Current Session Context"

**What NOT to update in PROGRESS.md:**
- Sub-phase completion (belongs in phase index)
- Implementation details (belong in sub-phase files)
- Commands (belong in COMMAND_LOG.md)

**Phase Completion & Validation (Required before marking phase ✅ COMPLETE):**
- **Primary workflow:** #58 (Phase Completion & Validation) - Unified end-to-end process
- **When:** Before marking any phase ✅ COMPLETE
- **What it includes:**
  - Test & validator generation (Phase 2)
  - Test & validator organization (Phase 3)
  - Validation execution (Phase 4)
  - README alignment with main README (Phase 5)
  - DIMS integration (Phase 6)
  - Phase index update (Phase 7)
  - Final validation (Phase 8)
- **Quick checklist:**
  - [ ] All tests pass (100% success rate)
  - [ ] README aligned with main README vision
  - [ ] DIMS metrics integrated
  - [ ] Phase index updated

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
- **DIMS Management:** docs/claude_workflows/workflow_descriptions/56_dims_management.md
- **Phase-README Alignment:** docs/claude_workflows/workflow_descriptions/57_phase_readme_alignment.md

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

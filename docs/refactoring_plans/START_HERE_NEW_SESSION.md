# START HERE - New Session Instructions

**Created:** October 29, 2025  
**For:** Next Cursor chat session to continue 14-week refactoring  
**Status:** Plans imported and ready for execution

---

## Quick Start for New Chat

Paste this into your first message:

```
I need to continue the 14-week codebase refactoring.

Please read these files in order:
1. docs/refactoring_plans/START_HERE_NEW_SESSION.md (this file)
2. docs/refactoring_plans/README.md (comprehensive index)
3. docs/refactoring_plans/execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md (main plan)

After reading, confirm you understand the plan and are ready to begin Phase 0: Pre-Flight Safety.
```

---

## What Happened in Previous Session (Oct 29, 2025)

### Completed Work

**1. Imported Refactoring Plans ✅**
- Imported 11 files from Downloads directories
- Created `docs/refactoring_plans/` structure
- Files now in: execution/, guides/, handoff/, scripts/

**2. Cleaned Up Duplicates ✅**
- Removed duplicate Phase 0 sub-phases (0.0023-0.0025)
- Fixed all documentation links
- Updated PHASE_0_INDEX.md

**3. Verified No Conflicts ✅**
- Confirmed refactoring plans don't call for MongoDB
- Confirmed no interference with existing PostgreSQL work
- Two separate initiatives are properly documented

### What Was NOT Done

❌ **Did NOT start the 14-week refactoring**  
- Plans are imported and organized
- Ready for execution
- Phase 0 (Pre-Flight Safety) not started

---

## Essential Reading (In Order)

### 1. This File (You're Reading It)
Quick orientation and handoff instructions

### 2. Main Index
**File:** `docs/refactoring_plans/README.md` (~430 lines)

**Contains:**
- Overview of 14-week plan
- File index and descriptions
- Quick navigation
- Getting started guide

### 3. Execution Plan
**File:** `docs/refactoring_plans/execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md` (~864 lines)

**Contains:**
- Complete 14-week timeline
- All 4,055+ files mapped
- 7-phase breakdown
- Safety protocols
- Success metrics

### 4. Production Guide (Optional but Recommended)
**File:** `docs/refactoring_plans/guides/REFACTORING_GUIDE_v2_PRODUCTION.md`

**Contains:**
- Zero-downtime strategies
- Database safety protocols
- DIMS/ADCE protection

---

## Critical Context

### Two Separate Initiatives (DO NOT CONFUSE)

#### 1. Phase 0 PostgreSQL Work (✅ COMPLETE)
- **What:** Archive MongoDB, implement PostgreSQL JSONB/RAG
- **Status:** Done and deployed (Oct 25, 2025)
- **Location:** `docs/phases/phase_0/0.0010_postgresql_jsonb_storage/` (and 0.0011, 0.0012)
- **Outcome:** PostgreSQL JSONB ✅, RAG + pgvector ✅, RAG + LLM ✅

#### 2. Full Codebase Refactoring (📋 READY TO START)
- **What:** Reorganize 4,055+ files into `nba_simulator/` package
- **Status:** Plans imported, NOT started
- **Location:** `docs/refactoring_plans/`
- **Timeline:** 14 weeks (7 phases)

**These are completely separate!** The refactoring plan is about code organization, not database architecture.

---

## What the Refactoring Plan Does

### ✅ It WILL:
- Reorganize 1,672 Python scripts into proper package structure
- Create `nba_simulator/` package with proper imports
- Move 643 tests into organized structure
- Reorganize 1,720 documentation files
- Make imports work: `from nba_simulator.etl import ESPNScraper`
- Preserve all existing functionality
- Ensure zero data loss

### ❌ It Will NOT:
- Change database architecture
- Implement MongoDB (not mentioned in plans)
- Add new features
- Modify existing functionality
- Touch PostgreSQL JSONB/RAG work (already complete)

---

## Where to Start

### Phase 0: Pre-Flight Safety (Week 0)

**Goal:** Ensure zero risk before touching any code

**Tasks:**

#### 1. Discover Active Systems
```bash
# Check for cron jobs
crontab -l

# Check for systemd timers
systemctl list-units --type=timer | grep nba

# Check for LaunchAgents (macOS)
launchctl list | grep nba
```

#### 2. Answer Critical Questions
- [ ] What is the `temporal_events` table (5.8 GB)?
- [ ] Which Phase 8 scripts are running?
- [ ] Is ADCE autonomous loop active?
- [ ] Which scrapers run on schedule?

#### 3. Create Baselines
```bash
# Database backup
pg_dump > backups/pre_refactor_$(date +%Y%m%d).sql

# Git safety tag
git tag pre-refactor-comprehensive-$(date +%Y%m%d)
git push origin --tags

# File structure baseline
tree -L 3 > structure_before_refactoring.txt
```

#### 4. Set Up Monitoring
```bash
# Start monitoring dashboard
python docs/refactoring_plans/scripts/refactor_dashboard.py
```

**See:** `docs/refactoring_plans/execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md` lines 395-447 for complete Phase 0 checklist

---

## Critical Constraints

### Must Protect (DO NOT BREAK)

1. **Database:** 20M+ records across 40 tables
2. **DIMS Monitoring:** Active system health monitoring
3. **Phase 8:** Box score generation (actively running)
4. **ADCE:** Autonomous 24/7 data collection
5. **Unknown Cron Jobs:** Must discover before moving files

### Safety Protocols

- ✅ Zero data loss (verify table counts continuously)
- ✅ Zero downtime (all existing scripts must work)
- ✅ Continuous monitoring (dashboard running)
- ✅ Emergency rollback prepared (git tags + backups)
- ✅ Additive only initially (create new, keep old)

---

## Current Project State

**Location:** `/Users/ryanranft/nba-simulator-aws`

**File Counts:**
- Total: 4,055+ files
- Python scripts: 1,672 (scattered across 10+ directories)
- Tests: 643 (no clear organization)
- Markdown docs: 1,720
- SQL files: Various

**Database:**
- PostgreSQL RDS 15.14
- 40 tables
- 20M+ records (esp. play_by_play)

**Key Systems:**
- DIMS: Active monitoring
- ADCE: Autonomous data collection (24/7)
- Phase 8: Box score generation
- Multiple scrapers: ESPN, Basketball Reference, hoopR, NBA API

---

## 14-Week Timeline

| Phase | Duration | Focus | Risk |
|-------|----------|-------|------|
| **Phase 0** | Week 0 | Pre-Flight Safety | LOW |
| **Phase 1** | Weeks 1-2 | Core Infrastructure | LOW |
| **Phase 2** | Weeks 3-5 | ETL Framework | MEDIUM |
| **Phase 3** | Weeks 6-7 | Agents & Workflows | MEDIUM-HIGH |
| **Phase 4** | Weeks 8-9 | Monitoring & Validation | MEDIUM |
| **Phase 5** | Weeks 10-11 | Testing Infrastructure | LOW |
| **Phase 6** | Weeks 12-13 | Phase 8 Box Score | HIGH |
| **Phase 7** | Week 14 | Final Validation | LOW |

---

## Success Metrics

### Technical
- [ ] All 4,055+ files accounted for
- [ ] Zero data loss (all table counts preserved)
- [ ] All 643 tests passing
- [ ] Test coverage ≥80%
- [ ] All imports working
- [ ] Performance equivalent or better

### Operational
- [ ] DIMS monitoring operational
- [ ] Phase 8 box score generation working
- [ ] ADCE autonomous collection running
- [ ] All scheduled jobs working
- [ ] Zero downtime

---

## Key Files Quick Reference

### Plans
- **Main index:** `README.md` (this directory)
- **Execution plan:** `execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md`
- **AI instructions:** `execution/CLAUDE_CODE_REFACTORING_INSTRUCTIONS.md`
- **File inventory:** `execution/COMPREHENSIVE_FILE_INVENTORY.md`

### Guides
- **Production safety:** `guides/REFACTORING_GUIDE_v2_PRODUCTION.md`
- **Deliverables:** `guides/REFACTORING_DELIVERABLES_v2.md`
- **Quick reference:** `guides/QUICK_REFERENCE.md`

### Scripts
- **Setup:** `scripts/phase1_setup_production_safe.sh`
- **Monitor:** `scripts/refactor_dashboard.py`
- **Validate:** `scripts/test_comprehensive_validation.py`

### Handoff
- **New session:** `handoff/QUICK_START_NEW_CHAT.md`
- **Continuity:** `handoff/NEW_CHAT_HANDOFF_INSTRUCTIONS.md`

---

## Emergency Rollback

If anything goes wrong:

```bash
# 1. Stop all work
pkill -f nba

# 2. Rollback code
git checkout pre-refactor-comprehensive-$(date +%Y%m%d)

# 3. Verify database unchanged
python scripts/validation/verify_system_health.py

# 4. Restart services
# [restart any services that were running]
```

---

## What to Ask the User

Before beginning, confirm:

1. **Are we ready to start Phase 0 Pre-Flight Safety?**
   - This involves discovery (no code changes)
   - Discovers active processes
   - Creates safety baselines

2. **Any specific concerns about the approach?**
   - Review the plan first?
   - Questions about safety protocols?

3. **Timeline acceptable?**
   - 14 weeks is the safe timeline
   - Can be accelerated if needed (with higher risk)

---

## Next Steps

**Immediate (Phase 0 - This Week):**
1. Read execution plan completely
2. Run discovery scripts (cron, systemd, launchctl)
3. Answer the 4 critical questions
4. Create safety baselines (backup, git tag, file structure)
5. Document findings

**After Phase 0:**
1. Review Phase 0 discoveries with user
2. Get approval to proceed to Phase 1
3. Begin creating `nba_simulator/` package structure
4. Start with core infrastructure (config, database, utils)

---

## Contact/Questions

**Project:** NBA Simulator AWS  
**Branch:** Should create new branch for refactoring work  
**Database:** PostgreSQL RDS (nba-sim-db)  
**S3 Bucket:** s3://nba-sim-raw-data-lake

**Documentation:**
- Main README: `/Users/ryanranft/nba-simulator-aws/README.md`
- CLAUDE.md: Project instructions for AI
- PROGRESS.md: Current project status

---

## Status Check Commands

```bash
# Check current state
git status
git log --oneline -5

# Check database
python scripts/validation/verify_system_health.py

# Check DIMS
python scripts/monitoring/dims_cli.py verify

# Check ADCE
python scripts/autonomous/autonomous_cli.py status

# Check file counts
find . -name "*.py" | wc -l
```

---

## Important Notes

### ✅ Good to Know
- All work is git-tracked
- Database backups automated
- DIMS monitoring provides safety net
- Can pause/resume at any phase boundary
- Each phase has clear success criteria

### ⚠️ Critical Warnings
- DO NOT skip Phase 0 Pre-Flight Safety
- DO NOT move files before discovery complete
- DO NOT modify database schemas
- DO NOT disable DIMS monitoring
- DO NOT interrupt Phase 8 box score generation

### 📋 Remember
- This is about organization, not features
- Keep old scripts as fallback initially
- Test equivalence before removing old code
- Update one module at a time
- Validate continuously

---

**Ready to begin?** Start with Phase 0 Pre-Flight Safety in `execution/COMPLETE_REFACTORING_EXECUTION_PLAN.md` (line 395).

**Questions?** Review the plan first, then ask specific questions about approach, timeline, or concerns.

**Last Updated:** October 29, 2025  
**Prepared By:** Previous session (archive + import work)  
**Status:** ✅ Ready for execution


# NBA Game Simulator & ML Platform - Progress Index

**System Version:** 2.0 (Modular Documentation System)
**Date Started:** September 29, 2025
**Current Phase:** Phase 4 Complete, Phase 5-6 Pending
**Last Updated:** October 3, 2025

> 💡 **For Claude Code Users:** See `CLAUDE.md` for detailed instructions on how to navigate this file, read phase files efficiently, and execute workflows. Start every session by reading CLAUDE.md first.

---

## Quick Start for New Sessions

**If you're Claude Code starting a new session:**
1. Read `CLAUDE.md` completely (understand navigation patterns)
2. Read this file (PROGRESS.md) to identify current phase
3. Check "Current Session Context" section below
4. Read the specific phase file for the current task
5. Follow workflow references in the phase file

**If you're a human developer:**
- Check "Current Session Context" section below for what's in progress
- See phase files in `docs/phases/` for detailed implementation steps
- All workflows are in `docs/claude_workflows/workflow_descriptions/`

---

## Current Session Context

**Last session ended:** October 3, 2025 (early morning)
**Last completed:** Phase 4 (Simulation Engine) complete - EC2 instance deployed, Monte Carlo simulation scripts developed and tested, RDS connection verified.
**Next to work on:** Phase 5 (Machine Learning - SageMaker) or Phase 6 (Optional Enhancements)
**Phase status:** Phases 1-4 complete, Phases 5-6 pending

> **Note for Claude:** Update this section at the end of every session (Workflow #14)

---

## For Returning Users

**If you're coming back after a break:**

1. **Read "Current Session Context" above** - see what was last worked on
2. **Check phase status** - see which phases are complete (✅), in progress (🔄), or pending (⏸️)
3. **Review recent commits** - `git log --oneline -10` to see what changed
4. **Check COMMAND_LOG.md** - see what commands were run recently
5. **Pick up where you left off** - or choose a new task from pending phases

**Common return scenarios:**
- "Continue where we left off" → Work on first 🔄 or ⏸️ sub-phase
- "Start Phase X" → Read PHASE_X file, ask about workflow additions
- "Review what's done" → Check ✅ phases, read phase file summaries

---

## 📍 Quick Navigation

### Phase Details

- ✅ [Phase 1: S3 Data Lake](docs/phases/PHASE_1_S3_DATA_LAKE.md) - **COMPLETE** (Oct 1)
- ✅ [Phase 2: AWS Glue ETL](docs/phases/PHASE_2_AWS_GLUE.md) - **COMPLETE** (Oct 2)
- ✅ [Phase 3: Database Infrastructure](docs/phases/PHASE_3_DATABASE.md) - **COMPLETE** (Oct 1)
- ✅ [Phase 4: Simulation Engine](docs/phases/PHASE_4_SIMULATION_ENGINE.md) - **COMPLETE** (Oct 3)
- ⏸️ [Phase 5: Machine Learning](docs/phases/PHASE_5_MACHINE_LEARNING.md) - **PENDING**
- ⏸️ [Phase 6: Optional Enhancements](docs/phases/PHASE_6_ENHANCEMENTS.md) - **PENDING**

### Reference Documentation

- **Workflows:** [docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md](docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md) (36 workflows)
- **Architecture decisions:** [docs/adr/README.md](docs/adr/README.md) (7 ADRs)
- **Setup instructions:** [docs/SETUP.md](docs/SETUP.md)
- **Quick commands:** [QUICKSTART.md](QUICKSTART.md)
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Testing:** [docs/TESTING.md](docs/TESTING.md)
- **LLM guidelines:** [CLAUDE.md](CLAUDE.md)

---

## 📊 Executive Summary

**Status:** Phases 1-4 Complete, Simulation Engine Operational
**Completed Date:** October 3, 2025
**Current Cost:** $38.33/month (S3 + RDS + EC2)
**Full Deployment Cost:** $50-150/month (when all phases complete)

### What's Accomplished

- ✅ **Phase 1:** S3 data lake with 146,115 files (119 GB) - Oct 1
- ✅ **Phase 2:** Local ETL extraction (bypassed AWS Glue) - Oct 2
  - 46,595 games with 53 fields (1993-2025)
  - 6,781,155 plays extracted
  - 408,833 player stats loaded
- ✅ **Phase 3:** RDS PostgreSQL operational - Oct 1
  - db.t3.small, 58-column schema
  - All data loaded and indexed
- ✅ **Phase 4:** EC2 simulation engine deployed - Oct 3
  - t3.small instance (i-0b8bbe4cdff7ae2d2)
  - Monte Carlo simulation scripts
  - RDS connection verified
  - Test simulations successful

### Current State

- **Working:** S3 bucket + RDS database + EC2 simulation engine
- **Environment:** Conda env `nba-aws`, Python 3.11.13
- **Git:** Repository synced with GitHub (SSH auth)
- **Cost:** $38.33/month ($2.74 S3 + $29 RDS + $6.59 EC2)

### Next Actions

1. **Develop ML models** → See [Phase 5](docs/phases/PHASE_5_MACHINE_LEARNING.md)
2. **Or add analytics** → See [Phase 6](docs/phases/PHASE_6_ENHANCEMENTS.md)
3. **Monitor costs** → Run `make check-costs` weekly

---

## 🔗 Phase Dependency Chain

**Execution order:**

```
Phase 1 (S3 Data Lake) ✅
    ↓
Phase 2 (ETL Extraction) ✅
    ↓
Phase 3 (RDS Database) ✅
    ↓
    ├─→ Phase 4 (EC2 Simulation) ⏸️
    │
    └─→ Phase 5 (SageMaker ML) ⏸️
            ↓
        Phase 6 (Enhancements) ⏸️ [OPTIONAL]
```

**Note:** Phases 4 and 5 can run in parallel (both depend on Phase 3).

---

## 🎯 Phase Status Summary

| Phase | Status | Completed | Cost/Month | Time | Details |
|-------|--------|-----------|------------|------|---------|
| 1. S3 Data Lake | ✅ COMPLETE | Oct 1 | $2.74 | 2 days | [View](docs/phases/PHASE_1_S3_DATA_LAKE.md) |
| 2. ETL (Local) | ✅ COMPLETE | Oct 2 | $0 | 1 day | [View](docs/phases/PHASE_2_AWS_GLUE.md) |
| 3. Database (RDS) | ✅ COMPLETE | Oct 1 | $29 | 1.6 hrs | [View](docs/phases/PHASE_3_DATABASE.md) |
| 4. Simulation (EC2) | ✅ COMPLETE | Oct 3 | $6.59 | 3 hrs | [View](docs/phases/PHASE_4_SIMULATION_ENGINE.md) |
| 5. ML (SageMaker) | ⏸️ PENDING | TBD | $7-75 | 6-12 hrs | [View](docs/phases/PHASE_5_MACHINE_LEARNING.md) |
| 6. Enhancements | ⏸️ PENDING | TBD | $4-10 | 3-5 hrs | [View](docs/phases/PHASE_6_ENHANCEMENTS.md) |

**Current total:** $38.33/month
**After Phase 5:** $58.33/month (+SageMaker)
**After Phase 6:** $62.33/month (+Analytics)
**Budget target:** <$150/month

---

## 💰 Cost Summary

### Current Monthly Costs
- S3 Storage: $2.74 (119 GB)
- RDS db.t3.small: $29.00
- EC2 t3.small (8hrs/day): $6.59
- **Total: $38.33/month**

### Projected Costs (Full Deployment)
- S3: $2.74
- RDS: $29.00
- EC2 (t3.small, 8hrs/day): $7.00
- SageMaker (moderate use): $20.00
- Enhancements: $5.00
- **Total: $63.74/month**

### Cost Optimization
- Stop EC2 when not in use (save ~$8/month)
- Stop SageMaker notebook when not developing (save ~$30/month)
- Use Spot instances for training (save 70%)
- **Actual monthly cost:** $35-65/month with proper start/stop discipline

**See individual phase files for detailed cost breakdowns.**

---

## 📍 Critical Paths & Locations

### Directories
- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **Original data:** `/Users/ryanranft/0espn/data/nba/`
- **Archives:** `~/sports-simulator-archives/nba/`

### AWS Resources
- **S3 Bucket:** `s3://nba-sim-raw-data-lake` (146,115 files, 119 GB)
- **RDS Endpoint:** `nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com`
- **Database:** `nba_simulator` (PostgreSQL 15.14)
- **Region:** us-east-1

### Local Environment
- **Conda env:** `nba-aws` (Python 3.11.13)
- **Activate:** `conda activate nba-aws`

---

## 📚 Data Summary

### S3 Data Lake
- **Time period:** NBA games 1999-2025
- **Total files:** 146,115 JSON files
- **Total size:** 119 GB raw
- **Valid files:** ~121,608 (83%)
- **Empty files:** ~24,507 (17%)

**Breakdown:**
- Schedule: 11,633 files
- Play-by-play: 44,826 files
- Box scores: 44,828 files
- Team stats: 44,828 files

### RDS Database
- **games:** 46,595 rows × 58 columns (1993-2025)
- **play_by_play:** 6,781,155 rows (1997-2021)
- **player_game_stats:** 408,833 rows
- **team_game_stats:** 15,900 rows
- **teams:** 87 rows
- **players:** ~5,000 rows

---

## 🏗️ Architecture Decisions

**Key ADRs:**
- **ADR-001:** Exclude Redshift (save $200-600/month) → Use RDS PostgreSQL
- **ADR-002:** Extract 10% of JSON fields (save 90% storage)
- **ADR-003:** Python 3.11 (AWS Glue 4.0 compatibility)
- **ADR-005:** Git SSH authentication (security)
- **ADR-008 (implied):** Skip AWS Glue Crawler for large datasets → Use local extraction

**Total savings:** $600-8,000/month vs. original architecture

**See [docs/adr/README.md](docs/adr/README.md) for complete ADRs.**

---

## 🔄 How to Use This System

### For LLMs Continuing This Project

1. **Check current status:** Read this index file (PROGRESS.md)
2. **Find your phase:** Click link to detailed phase file
3. **Follow workflows:** Each phase file references specific workflow numbers
4. **Update progress:** Mark tasks complete in phase files, update this index

### Navigation Pattern

```
PROGRESS.md (this file)
    ↓
docs/phases/PHASE_X_NAME.md (detailed implementation steps)
    ↓
docs/claude_workflows/workflow_descriptions/XX_workflow.md (procedures)
    ↓
Execute steps
```

### Example Workflow

**To deploy simulation engine (Phase 4):**

1. Read [docs/phases/PHASE_4_SIMULATION_ENGINE.md](docs/phases/PHASE_4_SIMULATION_ENGINE.md)
2. Follow workflow #24 (AWS Resource Setup) for EC2
3. Follow workflow #17 (Environment Setup) for software
4. Follow workflow #32 (RDS Connection) for database
5. Update PROGRESS.md when complete

---

## ✅ Success Criteria by Phase

### Phase 1 ✅
- [x] S3 bucket created
- [x] 146,115 files uploaded
- [x] Cost: $2.74/month

### Phase 2 ✅
- [x] Data extracted to RDS
- [x] 6.7M plays loaded
- [x] Cost: $0 (local extraction)

### Phase 3 ✅
- [x] RDS operational
- [x] All tables created
- [x] Cost: $29/month

### Phase 4 ✅
- [x] EC2 instance running
- [x] Simulation code deployed
- [x] Test simulation successful

### Phase 5 ⏸️
- [ ] SageMaker notebook operational
- [ ] ML model trained
- [ ] Accuracy > 60%

### Phase 6 ⏸️
- [ ] Analytics on S3
- [ ] CloudWatch alarms active

---

## 🔧 Quick Reference Commands

### Environment
```bash
# Activate conda environment
conda activate nba-aws

# Navigate to project
cd /Users/ryanranft/nba-simulator-aws

# Check git status
git status
```

### AWS Resources
```bash
# List S3 files
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | wc -l

# Connect to RDS
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres -d nba_simulator

# Check costs
make check-costs
```

### Workflows
```bash
# See all workflows
cat docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md

# Run session start
bash scripts/shell/session_manager.sh start
```

---

## 📖 Documentation Index

### Planning & Progress
- **This file (PROGRESS.md):** Progress index and navigation
- **Phase files:** Detailed implementation plans in `docs/phases/`

### Workflows (36 total)
- **Index:** [docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md](docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md)
- **Files:** [docs/claude_workflows/workflow_descriptions/](docs/claude_workflows/workflow_descriptions/)

### Architecture & Decisions
- **ADRs:** [docs/adr/README.md](docs/adr/README.md)
- **Data structure:** [docs/DATA_STRUCTURE_GUIDE.md](docs/DATA_STRUCTURE_GUIDE.md)
- **Lessons learned:** [docs/LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md)

### Operations
- **Setup:** [docs/SETUP.md](docs/SETUP.md)
- **Quick commands:** [QUICKSTART.md](QUICKSTART.md)
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Testing:** [docs/TESTING.md](docs/TESTING.md)
- **Security:** [docs/SECURITY_PROTOCOLS.md](docs/SECURITY_PROTOCOLS.md)

---

## 🎯 Next Steps

**Immediate:**
1. Choose next phase: Simulation (Phase 4) or ML (Phase 5)
2. Read corresponding phase file for detailed steps
3. Follow referenced workflows
4. Update this file when phase complete

**Weekly:**
- Run `make check-costs` to monitor AWS spending
- Review CloudWatch dashboards (when Phase 6 complete)
- Update documentation if workflows change

**Monthly:**
- Review all phase progress
- Update cost projections
- Archive completed work (see workflow #9)

---

**Quick Links:**
- 📋 [Workflow Index](docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md)
- 🏗️ [Architecture Decisions](docs/adr/README.md)
- 🚀 [Quick Commands](QUICKSTART.md)
- 🔧 [Setup Guide](docs/SETUP.md)
- ❓ [Troubleshooting](docs/TROUBLESHOOTING.md)

---

*Last updated: 2025-10-03*
*System: 6 phases, 37 workflows, 7 ADRs*
*Status: 4 phases complete, 2 phases pending*

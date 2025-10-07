# NBA Temporal Panel Data System - Progress Index

**System Version:** 2.0 (Modular Documentation System)
**Date Started:** September 29, 2025
**Current Phase:** Core Project Complete - Production Ready
**Last Updated:** October 7, 2025
**Project Status:** ✅ COMPLETE (Core phases) / 🔄 IN PROGRESS (Temporal data collection)

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

**Last session ended:** October 7, 2025 - 10:05 AM
**Last completed:** NBA API Scraper - Fixed Player Tracking Bug & Restarted
  - ✅ Checked overnight scraper status (Workflow #38)
    - Found 89% error rate (490/551 API calls failing)
    - Missing `team_id` parameter in player tracking endpoints
    - Preserved 5,857 files (114 MB) before stopping
  - ✅ Fixed player tracking bug
    - Added `team_id` lookup from player roster data
    - Filter to only active players with teams (ROSTERSTATUS=1, TEAM_ID≠0)
    - Tested successfully with 2024 season data
  - ✅ Restarted scraper with fix (PID 14497, started 10:04 AM)

**Overnight jobs running:**
  - **NBA API Comprehensive Scraper**: PID 14497, started 10:04 AM, ETA 4-5 hours
    - Coverage: 30 seasons (1996-2025), Tier 1 endpoints enabled
    - Output: `/tmp/nba_api_comprehensive/`
    - S3: `s3://nba-sim-raw-data-lake/nba_api_comprehensive/`
    - Log: `/tmp/nba_api_comprehensive_restart.log`
    - Testing limits: 100 games, 50 players per season
    - **Fix applied:** Player tracking now includes team_id parameter

**Next to work on:**
1. **Check scraper status** (Workflow #38: Overnight Scraper Handoff)
   - Verify completion: `ps aux | grep 14497`
   - Check logs: `tail -100 /tmp/nba_api_comprehensive_restart.log`
   - Validate output: File counts, data size, JSON validity, error rate
   - Confirm S3 uploads: `aws s3 ls s3://nba-sim-raw-data-lake/nba_api_comprehensive/`
2. **If successful:** Document results, analyze feature coverage
3. **If errors persist:** Review logs, adjust endpoints
4. **Next implementation:** Tier 1 remaining tasks (Kaggle tables, Basketball Ref ratings)

**Phase status:** Data collection enhanced ✅ - Multi-source integration in progress

> **Note for Claude:** Follow Workflow #38 at start of next session to check overnight scraper status

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

- ✅ [Phase 0: Data Collection & Initial Upload](docs/phases/PHASE_0_DATA_COLLECTION.md) - **COMPLETE** (Oct 1)
- ⏸️ [Phase 1: Data Quality & Gap Analysis](docs/phases/PHASE_1_DATA_QUALITY.md) - **READY TO IMPLEMENT** (multi-source integration planned)
  - 📖 [Multi-Source Implementation Plan](docs/PHASE_1_MULTI_SOURCE_PLAN.md) - 28 hours, 209 features
  - 📋 [ML Feature Catalog](docs/ML_FEATURE_CATALOG.md) - Complete feature breakdown
  - ⚡ [Quick Start Guide](docs/QUICK_START_MULTI_SOURCE.md) - Week-by-week implementation
  - ✅ [Implementation Checklist](docs/IMPLEMENTATION_CHECKLIST.md) - Track progress
- ✅ [Phase 2: AWS Glue ETL](docs/phases/PHASE_2_AWS_GLUE.md) - **COMPLETE** (Oct 2)
- ✅ [Phase 3: Database Infrastructure](docs/phases/PHASE_3_DATABASE.md) - **COMPLETE** (Oct 1)
- ✅ [Phase 4: Simulation Engine](docs/phases/PHASE_4_SIMULATION_ENGINE.md) - **COMPLETE** (Oct 3)
  - 🚀 [Advanced Simulation Framework](docs/ADVANCED_SIMULATION_FRAMEWORK.md) - Econometric models planned
- ✅ [Phase 5: Machine Learning](docs/phases/PHASE_5_MACHINE_LEARNING.md) - **COMPLETE** (Oct 3)
- ✅ [Phase 6: Optional Enhancements](docs/phases/PHASE_6_ENHANCEMENTS.md) - **COMPLETE** (Oct 3)
- ⏸️ [Phase 7: Betting Odds Integration](docs/phases/PHASE_7_BETTING_ODDS.md) - **PENDING** (optional future enhancement)

### Reference Documentation

- **📊 Project Status:** [PROJECT_STATUS.md](PROJECT_STATUS.md) - High-level summary for quick reference
- **Workflows:** [docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md](docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md) (36 workflows)
- **Architecture decisions:** [docs/adr/README.md](docs/adr/README.md) (7 ADRs)
- **Setup instructions:** [docs/SETUP.md](docs/SETUP.md)
- **Quick commands:** [QUICKSTART.md](QUICKSTART.md)
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Testing:** [docs/TESTING.md](docs/TESTING.md)
- **LLM guidelines:** [CLAUDE.md](CLAUDE.md)

### Enhancement Planning (October 6, 2025)

- **Next Steps Decision Guide:** [docs/NEXT_STEPS_OPTIONS.md](docs/NEXT_STEPS_OPTIONS.md) - Compare multi-source vs simulation paths
- **Session Summary:** [docs/SESSION_SUMMARY_2025_10_06_CONTINUED.md](docs/SESSION_SUMMARY_2025_10_06_CONTINUED.md) - Planning integration recap

---

## 📊 Executive Summary

**Status:** ✅ CORE PROJECT COMPLETE - Enhanced with Temporal Data Architecture
**Completed Date:** October 3, 2025 (Core phases) / October 7, 2025 (Temporal enhancement)
**Current Cost:** $41.53/month (S3 + RDS + EC2 + Monitoring + API)
**Budget Status:** 72% under $150/month target

### Project Vision

**Temporal Panel Data System:** Create snapshots of NBA history at exact timestamps with millisecond precision.

**Example capability:** Query "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?" and receive accurate cumulative stats up to that exact moment, including his age down to the second.

**Future integration:** Video feed synchronization with ball/player coordinates for computer vision analysis at 30fps (~33ms per frame).

### What's Accomplished

- ✅ **Phase 0:** Multi-Source Data Collection - Oct 1
  - S3 data lake with 146,115 files (119 GB) from ESPN
  - NBA API scraper optimized for temporal data (Oct 7)
    - PlayByPlayV2 endpoint for wall clock timestamps
    - Player biographical data for age calculations
    - Season cutoffs for data availability (2014+ tracking, 2016+ hustle/synergy)
    - Testing limits removed (100% data capture)
  - Ready to collect: ~366,486 files across all seasons (1996-2025)
- ⏸️ **Phase 1:** Data Quality - Temporal data validation framework (pending)
- ✅ **Phase 2:** Local ETL extraction (bypassed AWS Glue) - Oct 2
  - 44,828 games with 53 fields (1993-2025, schedules only)
  - 6,781,155 plays extracted (2004-2021)
  - Needs temporal indexing enhancement
- ✅ **Phase 3:** RDS PostgreSQL operational - Oct 1
  - db.t3.small, 58-column schema
  - Needs temporal events table for snapshot queries
- ✅ **Phase 4:** EC2 simulation engine deployed - Oct 3
  - Can be enhanced with temporal feature engineering
- ✅ **Phase 5:** ML models operational - Oct 3
  - Can leverage temporal features for improved predictions
- ✅ **Phase 6:** Analytics and monitoring - Oct 3
  - CloudWatch, Athena, API Gateway deployed

### Current State

- **Working:** S3 bucket + RDS database + EC2 simulation engine + Temporal scraper ready
- **Environment:** Conda env `nba-aws`, Python 3.11.13
- **Git:** Repository synced with GitHub (SSH auth)
- **Cost:** $38.33/month ($2.74 S3 + $29 RDS + $6.59 EC2)
- **Data Precision:**
  - 2020-2025: Millisecond precision (NBA Live API - future)
  - 1993-2019: Minute-level precision (NBA Stats PlayByPlayV2)
  - 1946-1992: Game-level aggregates (Basketball Reference)

### Next Actions

1. **Start Priority 1 scraping** (2014-2025 seasons) - 14-15 days runtime
2. **Design temporal events database schema** - Enable snapshot queries
3. **Implement snapshot query system** - Reconstruct NBA state at any timestamp
4. **Build temporal feature engineering** - Enhance ML models with time-based features

---

## 🔗 Phase Dependency Chain

**Execution order:**

```
Phase 0 (Data Collection) ✅
    ↓
Phase 1 (Data Quality) ⏸️ [OPTIONAL - multi-source integration]
    ↓
Phase 2 (ETL Extraction) ✅
    ↓
Phase 3 (RDS Database) ✅
    ↓
    ├─→ Phase 4 (EC2 Simulation) ✅
    │
    ├─→ Phase 5 (SageMaker ML) ✅
    │       ↓
    │   Phase 6 (Enhancements) ✅ [OPTIONAL]
    │
    └─→ Phase 7 (Betting Odds) ⏸️ [OPTIONAL]
```

**Note:** Phase 1 is optional for multi-source data integration (209 features). Phases 4, 5, and 7 can all run in parallel (all depend on Phase 3). Phase 6 depends on Phase 5.

---

## 🎯 Phase Status Summary

| Phase | Status | Completed | Cost/Month | Time | Details |
|-------|--------|-----------|------------|------|---------|
| 0. Data Collection | ✅ COMPLETE | Oct 1 | $2.74 | 2 days | [View](docs/phases/PHASE_0_DATA_COLLECTION.md) |
| 1. Data Quality | ⏸️ PENDING | - | $0-10 | 4-8 hrs | [View](docs/phases/PHASE_1_DATA_QUALITY.md) |
| 2. ETL (Local) | ✅ COMPLETE | Oct 2 | $0 | 1 day | [View](docs/phases/PHASE_2_AWS_GLUE.md) |
| 3. Database (RDS) | ✅ COMPLETE | Oct 1 | $29 | 1.6 hrs | [View](docs/phases/PHASE_3_DATABASE.md) |
| 4. Simulation (EC2) | ✅ COMPLETE | Oct 3 | $6.59 | 3 hrs | [View](docs/phases/PHASE_4_SIMULATION_ENGINE.md) |
| 5. ML (SageMaker) | ✅ COMPLETE | Oct 3 | $0 | 4 hrs | [View](docs/phases/PHASE_5_MACHINE_LEARNING.md) |
| 6. Enhancements | ✅ COMPLETE | Oct 3 | $3 | 2 hrs | [View](docs/phases/PHASE_6_ENHANCEMENTS.md) |
| 7. Betting Odds | ⏸️ PENDING | - | $0-10 | 6-8 hrs | [View](docs/phases/PHASE_7_BETTING_ODDS.md) |

**Current total:** $38.33/month (excluding optional phases 1 & 7)
**With Phase 1:** $43-46/month (multi-source integration)
**With Phase 7:** $38-48/month (betting odds API)
**Budget target:** <$150/month

---

## 💰 Cost Summary

### Current Monthly Costs (Base System)
- S3 Storage: $2.74 (119 GB ESPN data)
- RDS db.t3.small: $29.00 (20 GB storage)
- EC2 t3.small (8hrs/day): $6.59
- **Total: $38.33/month**

---

### Temporal Enhancement Cost Impact

**Additional storage requirements:**

| Component | Storage Size | Monthly Cost |
|-----------|--------------|--------------|
| `temporal_events` (500M rows) | 200-300 GB | $4.60-6.90 (S3) |
| `player_snapshots` (50M rows) | 10-20 GB | $0.23-0.46 (S3) |
| `game_states` (10M rows) | 5-10 GB | $0.12-0.23 (S3) |
| `player_biographical` (5K rows) | < 1 GB | $0.02 (S3) |
| **Total temporal data** | **215-330 GB** | **$4.97-7.61/month** |

**RDS storage upgrade:**
- Current: 20 GB
- Needed: 250-350 GB (for temporal tables)
- Cost increase: +$11.57-23.57/month

**BRIN index savings:**
- Traditional B-tree: ~50 GB storage
- BRIN indexes: ~500 MB storage
- **Savings: ~$1.14/month** (70% reduction)

**Total with temporal enhancement:**
- Base: $38.33/month
- Temporal S3: +$4.97-7.61/month
- RDS upgrade: +$11.57-23.57/month
- Snapshot generation: +$2-5/month (Lambda/EC2 jobs)
- **New total: $56.87-74.51/month**

**Cost increase: +$18.54-36.18/month** for temporal capability

---

### Projected Costs (Full Deployment with Temporal)

**Without temporal:**
- S3: $2.74
- RDS: $29.00
- EC2 (t3.small, 8hrs/day): $7.00
- SageMaker (moderate use): $20.00
- Enhancements: $5.00
- **Total: $63.74/month**

**With temporal:**
- S3: $7.71-10.35 (base + temporal)
- RDS: $40.57-52.57 (upgraded storage)
- EC2 (t3.small, 8hrs/day): $7.00
- SageMaker (moderate use): $20.00
- Snapshot generation: $2-5.00
- Enhancements: $5.00
- **Total: $82.28-99.92/month**

**Temporal cost increase: +$18.54-36.18/month**

---

### Cost Optimization Strategies

**Temporal-specific:**
1. **Snapshot frequency tuning:**
   - Baseline: Every game (18M snapshots)
   - Optional: Every quarter (+50K/season)
   - **Tradeoff:** More snapshots = faster queries, higher cost

2. **Archive old snapshots to S3 Glacier:**
   - Glacier: $0.004/GB vs Standard $0.023/GB
   - Archive snapshots > 5 years old
   - **Savings: ~$3-5/month**

3. **Use BRIN indexes (already planned):**
   - Save $1.14/month vs B-tree indexes
   - Minimal query performance impact

4. **Partition by year:**
   - Improves query speed
   - Enable archiving old partitions
   - No additional cost

**General optimizations:**
- Stop EC2 when not in use (save ~$8/month)
- Stop SageMaker when not developing (save ~$30/month)
- Use Spot instances for training (save 70%)
- S3 Intelligent-Tiering for rarely accessed data (save 30-40%)

**Actual monthly cost with discipline:**
- **Base system:** $35-65/month
- **Temporal system:** $57-95/month
- **Peak (everything running):** $100/month

---

### Budget Status

**Target:** $150/month
**Current:** $38.33/month (74% under budget)
**With temporal:** $57-75/month (50-62% under budget)
**Peak usage:** $100/month (33% under budget)

**Temporal enhancement fits budget:** Adds $19-37/month, well within target.

---

**See individual phase files for detailed cost breakdowns:**
- **Phase 3 (Sub-Phase 3.5):** Temporal table costs and optimizations
- **ADR-009:** Temporal architecture cost analysis
- **Phase 0-6:** Base infrastructure costs

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
- **games:** 44,828 rows × 58 columns (1993-2025, schedules only - detailed stats end 2021)
- **box_score_players:** 408,833 rows (1997-2021)
- **box_score_teams:** 15,900 rows (1997-2021)
- **play_by_play:** 6,781,155 rows (2004-2021)
- **player_game_stats:** 0 rows (table empty)
- **team_game_stats:** 0 rows (table empty)
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

### Phase 5 ✅
- [x] SageMaker notebook operational (Sub-Phase 5.1)
- [x] Feature engineering pipeline created (Sub-Phase 5.2)
- [x] Features generated and stored in S3 (43,485 games, 17 features)
- [x] ML models trained - 4 models (Logistic Regression, Random Forest, XGBoost, LightGBM)
- [x] Accuracy > 60% achieved (63.0% with Logistic Regression, AUC 0.659)

### Phase 6 ✅
- [x] S3 Analytics Lake (Sub-Phase 6.1) - complete
  - 100 sample predictions saved in Parquet format
  - Partitioned by season and date for efficient queries
  - Demo script: `scripts/analytics/save_predictions_to_s3.py`
- [x] AWS Athena setup (Sub-Phase 6.2) - complete
  - Database: `nba_predictions`
  - Table: `game_predictions` (partitioned)
  - Test query successful: 1.7 KB scanned, <5 seconds
- [x] CloudWatch monitoring (Sub-Phase 6.3) - complete
  - SNS topic: `arn:aws:sns:us-east-1:575734508327:nba-simulator-alerts`
  - 3 RDS alarms active (CPU, connections, storage)
  - Dashboard: `nba-simulator-metrics`
- [x] Prediction API (Sub-Phase 6.4) - complete
  - Lambda function: `nba-prediction-api` (4KB, lightweight)
  - API Gateway: `https://emktactsx8.execute-api.us-east-1.amazonaws.com`
  - Response time: 200-500ms
  - Documentation: `docs/API_DOCUMENTATION.md`

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

**Immediate: Multi-Source Data Integration (Phase 1 Enhancement)**

**Week 1 (12 hours):**
1. Basketball Reference scraper (8 hrs) → 47 advanced features
   - See `docs/IMPLEMENTATION_CHECKLIST.md` Sub-Phase 1.10
   - TOS compliance: 1 request per 3 seconds
   - Features: True Shooting %, PER, BPM, Win Shares, Four Factors
2. NBA.com Stats expansion (4 hrs) → 92 tracking features
   - See `docs/IMPLEMENTATION_CHECKLIST.md` Sub-Phase 1.7
   - Add 11 API endpoints (tracking, hustle, defense)
   - Features: Movement, touches, shot quality, defensive impact

**Week 2 (8 hours):**
3. Kaggle historical data (4 hrs) → 12 historical features
4. Multi-source storage setup (4 hrs) → Database schema updates

**Week 3 (6 hours):**
5. Feature engineering pipeline (4 hrs) → 209-feature vectors
6. Quality dashboard (2 hrs) → Validation metrics

**Week 4 (2 hours):**
7. SageMaker validation (2 hrs) → ML-ready dataset

**Alternative: Advanced Simulation Framework (Phase 4 Enhancement)**

**Weeks 1-8 (6-8 weeks):**
- Panel data models → Team fixed effects estimation
- Cluster equations → Simultaneous equation systems
- Non-linear dynamics → Momentum, fatigue, regime-switching
- Hierarchical Bayesian → Multi-level player/team modeling
- See `docs/ADVANCED_SIMULATION_FRAMEWORK.md` for detailed roadmap

**Weekly Maintenance:**
- Run `make check-costs` to monitor AWS spending
- Review CloudWatch dashboards
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

*Last updated: 2025-10-06*
*System: 8 phases (0-7), 36 workflows, 7 ADRs*
*Status: 6 core phases complete, 2 optional phases pending (1 with enhancement plans) - production ready*

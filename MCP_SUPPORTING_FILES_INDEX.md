# MCP Supporting Files Index

**Purpose:** Complete reference guide for all files relevant to the temporal data build completion plan
**Created:** October 20, 2025
**For:** MCP Server Context

---

## How to Use This Index

This document lists all files that provide context for the temporal data build implementation plan. The MCP server can reference these files to understand project state, technical architecture, and implementation details.

**Organization:**
- **Tier 1:** Must-read files (essential context)
- **Tier 2:** Should-read files (important details)
- **Tier 3:** Reference files (read as needed)

---

## Tier 1: Must-Read Files (Essential Context)

### Core Project Documentation

| File | Lines | Purpose | Key Information |
|------|-------|---------|-----------------|
| **PROGRESS.md** | ~390 | Master project index | Current phase status, completed work, session context, costs |
| **CLAUDE.md** | ~395 | Core instructions | Navigation patterns, workflows, context management |
| **README.md** | ~342 | Project overview | Architecture, vision, quick start |
| **docs/README.md** | ~100 | Documentation map | How to find and navigate all docs |

**Why These Matter:**
- PROGRESS.md tells you where we are now
- CLAUDE.md explains how the project is organized
- README.md describes what we're building
- docs/README.md shows you how to find everything else

### Current Work Status

| File | Lines | Purpose | Key Information |
|------|-------|---------|-----------------|
| **docs/OPTION_2A_STATUS.md** | ~494 | Current implementation state | 60% complete, known issues, next steps |
| **docs/OPTION_2A_SESSION_SUMMARY.md** | ~600 | Detailed session notes | What works, what's broken, how to continue |

**Why These Matter:**
- Shows exactly what's complete vs. remaining in Workstream 1
- Contains reproduction steps and fix strategies
- Critical for understanding current state

### Phase 2 Overview

| File | Lines | Purpose | Key Information |
|------|-------|---------|-----------------|
| **docs/phases/PHASE_9_INDEX.md** | ~321 | Phase 2 master index | 8 sub-phases, timeline, success criteria |

**Why This Matters:**
- Phase 2 is the primary focus (snapshot generation)
- Contains overview of all 8 sub-phases
- Success criteria and cost estimates

---

## Tier 2: Should-Read Files (Important Details)

### Phase 2 Sub-Phase Documentation

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| **docs/phases/phase_9/9.0000_system_architecture.md** | ~84 | System design | ✅ Complete |
| **docs/phases/phase_9/9.0001_espn_processor.md** | TBD | ESPN processor spec | ✅ Complete |
| **docs/phases/phase_9/9.0002_hoopr_processor.md** | TBD | hoopR processor spec | ✅ Complete |
| **docs/phases/phase_9/9.0003_nba_api_processor.md** | ~100 | NBA API processor spec | ⏸️ Pending |
| **docs/phases/phase_9/9.0004_kaggle_processor.md** | ~74 | Kaggle processor spec | ⏸️ Pending |
| **docs/phases/phase_9/9.0005_storage_system.md** | ~84 | Storage architecture | ⏸️ Pending |
| **docs/phases/phase_9/9.0006_advanced_metrics.md** | ~74 | Advanced metrics layer | ⏸️ Pending |
| **docs/phases/phase_9/9.0007_ml_integration.md** | TBD | ML integration approach | ⏸️ Pending |
| **docs/phases/phase_9/9.0008_betting_integration.md** | TBD | Betting integration | ⏸️ Pending |

**Why These Matter:**
- Each sub-phase has specific requirements
- Dependencies clearly documented
- Timeline and cost estimates provided

### Basketball Reference Expansion

| File | Lines | Purpose | Key Information |
|------|-------|---------|-----------------|
| **docs/phases/phase_0/0.0001_basketball_reference/README.md** | ~100 | Overview of 13 tiers | 234 data types, 140-197 hours, organization |
| **docs/phases/phase_0/0.0001_basketball_reference/TIER_1_NBA_HIGH_VALUE.md** | TBD | Tier 1 details | 5 data types, 150K records, 15-20 hours |
| **docs/phases/phase_0/0.0001_basketball_reference/TIER_2_NBA_STRATEGIC.md** | TBD | Tier 2 details | 4 data types, 200K records, 20-25 hours |
| **docs/phases/phase_0/0.0001_basketball_reference/IMPLEMENTATION_SUMMARY.md** | TBD | Technical approach | Scraping strategy, rate limiting, checkpointing |

**Why These Matter:**
- Basketball Reference is Workstream 3 (140-197 hours of work)
- Tiers provide natural breaking points for incremental delivery
- Technical implementation details for scraping

### Multi-Source Integration

| File | Lines | Purpose | Key Information |
|------|-------|---------|-----------------|
| **docs/phases/PHASE_1_INDEX.md** | ~150 | Phase 1 overview | Data quality and multi-source integration |
| **docs/phases/phase_1/1.0001_multi_source_integration.md** | TBD | Integration details | 209 features, conflict resolution, 28 hours |

**Why These Matter:**
- Workstream 4 depends on understanding multi-source integration strategy
- Conflict resolution rules critical for data quality

### ML and Feature Engineering

| File | Lines | Purpose | Key Information |
|------|-------|---------|-----------------|
| **docs/PLUS_MINUS_IMPLEMENTATION_SUMMARY.md** | ~509 | Plus/minus system | 4,566 lines of code, production-ready |
| **docs/REC_11_PLUS_MINUS_INTEGRATION.md** | TBD | ML integration | 171 features, 100% extraction success |
| **docs/phases/PHASE_5_INDEX.md** | ~150 | ML frameworks overview | 18 frameworks, 214 recommendations |

**Why These Matter:**
- Shows what ML capabilities already exist
- Provides context for 9.0007 ML Integration
- Feature engineering patterns established

---

## Tier 3: Reference Files (Read As Needed)

### Implementation Code

**Phase 2 Snapshot Generation (Workstream 1):**
```
scripts/pbp_to_boxscore/
├── play_text_parser.py              (800 lines) - Parses NBA play text
├── game_state_tracker.py            (600 lines) - Tracks game state (NEEDS FIX)
├── rds_pbp_processor.py             (500 lines) - Main coordinator
├── box_score_snapshot.py            (360 lines) - Data structures
└── base_processor.py                (514 lines) - Abstract base class
```

**Phase 2 Database Schema:**
```
sql/
├── phase9_box_score_snapshots.sql   (510 lines) - Main schema
└── plus_minus/                       (5 SQL files) - Plus/minus tables
    ├── lineup_snapshots.sql
    ├── player_plus_minus_snapshots.sql
    ├── possession_metadata.sql
    ├── vw_lineup_plus_minus.sql
    └── vw_on_off_analysis.sql
```

**ML and Feature Engineering:**
```
scripts/ml/
├── plus_minus_feature_extractor.py  (600+ lines) - Extract plus/minus features
├── rec_11_with_plus_minus.py        (600+ lines) - Enhanced rec_11
├── lineup_optimization_model.py      - Lineup predictions
└── player_impact_prediction_model.py - Player impact
```

### Workflow Documentation

**Workflow Index:**
- `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md` - 54 workflows

**Key Workflows for Implementation:**
- Workflow #38: Overnight Handoff
- Workflow #39: Monitoring Automation
- Workflow #40: Complete Scraper Operations
- Workflow #41: Testing Framework
- Workflow #42: Box Score Generation (to be created)
- Workflow #43: Batch Processing (to be created)
- Workflow #44: Verification (to be created)
- Workflow #45: Storage Management (to be created)

### Data Source Documentation

| File | Lines | Purpose |
|------|-------|---------|
| **docs/DATA_SOURCES.md** | ~595 | 5 data sources coverage and status |
| **docs/DATA_STRUCTURE_GUIDE.md** | TBD | S3 bucket layout, file characteristics |
| **docs/DATA_SOURCE_BASELINES.md** | TBD | Verified baseline statistics |
| **docs/DATA_SOURCE_MAPPING.md** | ~711 | Multi-source integration mapping |

### Architecture and Design

| File | Lines | Purpose |
|------|-------|---------|
| **docs/PROJECT_VISION.md** | TBD | Temporal panel data system vision |
| **docs/TEMPORAL_VS_TRADITIONAL.md** | ~626 | Why temporal architecture matters |
| **docs/TEMPORAL_QUERY_GUIDE.md** | ~996 | Implementation reference (read sections) |
| **docs/adr/** | Various | Architecture Decision Records |

### Testing and Quality

| File | Lines | Purpose |
|------|-------|---------|
| **docs/TESTING.md** | ~862 | Testing philosophy (read when writing tests) |
| **docs/STYLE_GUIDE.md** | ~846 | Code style guidelines |

### Troubleshooting and Lessons

| File | Lines | Purpose |
|------|-------|---------|
| **docs/TROUBLESHOOTING.md** | ~1,025 | Error solutions (grep, don't read fully) |
| **docs/LESSONS_LEARNED.md** | ~1,002 | Historical context |
| **docs/EMERGENCY_RECOVERY.md** | ~100 | Recovery procedures |

### Book Recommendations and ML Systems

| File | Lines | Purpose |
|------|-------|---------|
| **BOOK_RECOMMENDATIONS_PROGRESS.md** | TBD | 214 recommendations completed |
| **docs/BOOK_RECOMMENDATIONS_COMPLETION_SUMMARY.md** | TBD | Autonomous implementation summary |
| **docs/MCP_SCRAPING_RECOMMENDATIONS.md** | TBD | Scraping best practices |

---

## Quick Navigation by Workstream

### Workstream 1: Complete Phase 2 Snapshot Generation

**Must Read:**
- docs/OPTION_2A_STATUS.md (current state)
- docs/OPTION_2A_SESSION_SUMMARY.md (implementation details)
- docs/phases/PHASE_9_INDEX.md (overview)

**Code References:**
- scripts/pbp_to_boxscore/play_text_parser.py
- scripts/pbp_to_boxscore/game_state_tracker.py (needs fix)
- scripts/pbp_to_boxscore/rds_pbp_processor.py

**Schema:**
- sql/phase9_box_score_snapshots.sql

### Workstream 2: Phase 2 Additional Processors

**Must Read:**
- docs/phases/PHASE_9_INDEX.md
- docs/phases/phase_9/9.0003_nba_api_processor.md
- docs/phases/phase_9/9.0004_kaggle_processor.md
- docs/phases/phase_9/9.0005_storage_system.md
- docs/phases/phase_9/9.0006_advanced_metrics.md
- docs/phases/phase_9/9.0007_ml_integration.md
- docs/phases/phase_9/9.0008_betting_integration.md

**Code References:**
- scripts/pbp_to_boxscore/base_processor.py (abstract class to extend)
- scripts/ml/plus_minus_feature_extractor.py (feature extraction pattern)

### Workstream 3: Basketball Reference Expansion

**Must Read:**
- docs/phases/phase_0/0.0001_basketball_reference/README.md
- docs/phases/phase_0/0.0001_basketball_reference/TIER_1_NBA_HIGH_VALUE.md
- docs/phases/phase_0/0.0001_basketball_reference/TIER_2_NBA_STRATEGIC.md
- docs/phases/phase_0/0.0001_basketball_reference/IMPLEMENTATION_SUMMARY.md

**Best Practices:**
- docs/MCP_SCRAPING_RECOMMENDATIONS.md

### Workstream 4: Multi-Source Integration

**Must Read:**
- docs/phases/PHASE_1_INDEX.md
- docs/phases/phase_1/1.0001_multi_source_integration.md
- docs/DATA_SOURCE_MAPPING.md

**Code References:**
- scripts/etl/merge_all_sources.py (existing merger to enhance)

---

## File Reading Protocol for MCP

### Recommended Reading Order

1. **Start Here** (15 minutes reading):
   - PROGRESS.md
   - CLAUDE.md
   - docs/README.md
   - docs/OPTION_2A_STATUS.md

2. **Then Read** (30 minutes):
   - docs/phases/PHASE_9_INDEX.md
   - All Phase 2 sub-phase files (9.0-9.8)
   - docs/phases/phase_0/0.0001_basketball_reference/README.md

3. **Deep Dive As Needed** (reference):
   - Code files when understanding implementation details
   - Schema files when planning database changes
   - Workflow files when defining procedures

### What to Skip (Unless Specifically Needed)

- TROUBLESHOOTING.md (use grep if error occurs)
- LESSONS_LEARNED.md (historical context, not actionable)
- TESTING.md (read only when writing test plan)
- STYLE_GUIDE.md (read only when code style question arises)

---

## File Size Guide (Context Planning)

### Small (<200 lines) - Read Freely
- docs/README.md (~100 lines)
- docs/EMERGENCY_RECOVERY.md (~100 lines)
- Phase 2 sub-phase files (~84-100 lines each)

### Medium (200-500 lines) - Read When Needed
- CLAUDE.md (~395 lines)
- PROGRESS.md (~390 lines)
- README.md (~342 lines)
- docs/OPTION_2A_STATUS.md (~494 lines)
- docs/PLUS_MINUS_IMPLEMENTATION_SUMMARY.md (~509 lines)

### Large (500-1000 lines) - Read Specific Sections
- docs/OPTION_2A_SESSION_SUMMARY.md (~600 lines)
- docs/DATA_SOURCE_MAPPING.md (~711 lines)
- docs/TEMPORAL_VS_TRADITIONAL.md (~626 lines)
- docs/DATA_SOURCES.md (~595 lines)

### Very Large (>1000 lines) - Search Only
- docs/TROUBLESHOOTING.md (~1,025 lines)
- docs/LESSONS_LEARNED.md (~1,002 lines)
- docs/TEMPORAL_QUERY_GUIDE.md (~996 lines)
- docs/TESTING.md (~862 lines)
- docs/STYLE_GUIDE.md (~846 lines)

---

## Additional Resources

### Git Status
Run `git status` to see modified files and current branch

### Database Schema
Connect to RDS to inspect actual database schema:
```bash
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U nbasimuser -d nba_simulator
```

### S3 Bucket
Browse data lake:
```bash
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | head -100
```

### Recent Commits
View recent implementation history:
```bash
git log --oneline -20
```

---

## Summary

**For MCP to Create Implementation Plan:**

1. **Essential Context** (Tier 1): Read all 6 files (~2,000 lines total)
2. **Important Details** (Tier 2): Skim 20+ files for specifics (~5,000 lines)
3. **Reference** (Tier 3): Search as needed (code, schemas, workflows)

**Total Context Budget:** ~7,000 lines of reading for comprehensive plan

**Recommended Approach:**
- Read Tier 1 completely (understand where we are)
- Skim Tier 2 (understand what's planned)
- Reference Tier 3 as needed (technical details)

---

**Document Version:** 1.0
**Created:** October 20, 2025
**Purpose:** File index for MCP server context
**Next Step:** Provide to MCP along with main request document

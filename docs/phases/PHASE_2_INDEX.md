# Phase 2: Play-by-Play to Box Score Generation

**Version:** 2.0 (Promoted from Phase 9)
**Status:** ⏸️ PENDING
**Priority:** ⭐ CRITICAL (Core Functionality)
**Timeline:** 12 weeks (3 months)
**Cost Impact:** +$0.80-1.30/month
**Migrated From:** Phase 9 (October 25, 2025 - Comprehensive Phase Reorganization)

---

## Overview

Generate granular box score snapshots from play-by-play (PBP) data to enable temporal queries, betting forecasts, and advanced ML features. This is **core functionality** for the NBA Temporal Panel Data System, not an optional enhancement.

**This phase delivers:**

1. **Temporal Box Scores**: Complete box score state after each play-by-play event
2. **Quarter Box Scores**: Separate stats for each quarter (betting odds forecasting)
3. **Verification System**: Compare generated final box scores against actual box scores
4. **Advanced Metrics**: Platform to add metrics not in original data
5. **ML Enhancement**: More accurate predictions with granular state data

**Why this is Phase 2, not Phase 9:**
- **Enables ALL downstream analysis** - Without box score snapshots, temporal queries impossible
- **Core to project vision** - "Query stats at any exact moment" requires this
- **Prerequisite for ML** - Phase 5 models need temporal features
- **Not optional** - Essential for simulation engine (Phase 4)

**Strategy:** Start with recent games (2023-2025) where data is most accurate, then work backwards.

---

## Dependencies

**Required:**
- [x] Phase 0 complete (data collection)
- [x] ESPN play-by-play data in S3 (44,826 games)
- [x] hoopR play-by-play data in RDS (13M rows)
- [x] NBA API play-by-play data (1995-2006)
- [x] Actual box scores for verification

**Optional:**
- [ ] Kaggle historical data for older games
- [ ] Basketball Reference data for cross-validation

---

## Sub-Phases

| # | Sub-Phase | Status | Timeline | Priority | Dependencies |
|---|-----------|--------|----------|----------|--------------|
| **2.0** | [System Architecture](phase_2/2.0_system_architecture.md) | ⏸️ PENDING | 1-2 weeks | ⭐ CRITICAL | None |
| **2.1** | [ESPN Processor](phase_2/2.1_espn_processor.md) | ⏸️ PENDING | 2-3 weeks | ⭐ CRITICAL | 2.0 |
| **2.2** | [hoopR Processor](phase_2/2.2_hoopr_processor.md) | ⏸️ PENDING | 2 weeks | 🟡 HIGH | 2.1 |
| **2.3** | [NBA API Processor](phase_2/2.3_nba_api_processor.md) | ⏸️ PENDING | 2 weeks | 🟡 MEDIUM | 2.1, 2.2 |
| **2.4** | [Kaggle Processor](phase_2/2.4_kaggle_processor.md) | ⏸️ PENDING | 1 week | 🟢 LOW | 2.1-2.3 |
| **2.5** | [Storage System](phase_2/2.5_storage_system.md) | ⏸️ PENDING | 1 week | 🟡 HIGH | 2.1 |
| **2.6** | [Advanced Metrics](phase_2/2.6_advanced_metrics.md) | ⏸️ PENDING | 2-3 weeks | 🟡 MEDIUM | 2.5 |
| **2.7** | [ML Integration](phase_2/2.7_ml_integration.md) | ⏸️ PENDING | 2 weeks | 🟡 HIGH | 2.6 |
| **2.8** | [Betting Integration](phase_2/2.8_betting_integration.md) | ⏸️ PENDING | 3 weeks | 🟡 MEDIUM | 2.7 |

**Total Sub-Phases:** 9
**Estimated Duration:** 12 weeks
**Prerequisites:** Phase 0 complete

---

## Architecture Overview

```
Play-by-Play Data → Processor → Box Score Snapshots → Verification → Storage
                                       ↓
                                  ML Features
                                       ↓
                                 Betting Models
```

**Processing Flow:**
1. Load PBP data from source (ESPN/hoopR/NBA API)
2. Parse each event sequentially
3. Update running box score
4. Create snapshot after each event
5. Track quarter boundaries
6. Verify final box score vs actual
7. Store in RDS + S3 Parquet

---

## Data Sources

**Get current S3 metrics (always up-to-date):**
```bash
python scripts/monitoring/dims_cli.py verify --category s3_storage
```

**See also:** [Workflow #56: DIMS Management](../claude_workflows/workflow_descriptions/56_dims_management.md), `inventory/metrics.yaml`

| Source | Games | Date Range | Priority | Notes |
|--------|-------|------------|----------|-------|
| **ESPN** | 44,826 | 1993-2025 | ⭐ HIGHEST | Start here, best quality |
| **hoopR** | ~30,000 | 2002-2025 | 🟡 HIGH | Cross-validation |
| **NBA API** | ~22,000 | 1995-2006 | 🟡 MEDIUM | Historical |
| **Kaggle** | 65,698 | 1946-2020 | 🟢 LOW | Very old data |

---

## Success Criteria

**Minimum Viable Product (MVP):**
- [ ] Process all 2023-2025 ESPN games (~2,952 games)
- [ ] 99%+ verification accuracy
- [ ] Quarter-by-quarter box scores generated
- [ ] Stored in RDS + S3
- [ ] Basic ML feature set created

**Full Success:**
- [ ] All data sources processed (1993-2025)
- [ ] Multi-source cross-validation
- [ ] Advanced metrics implemented
- [ ] ML models trained with quarter predictions
- [ ] Betting model with ROI tracking

---

## Performance Targets

| Metric | Target | Stretch |
|--------|--------|---------|
| Processing Speed | 500ms/game | 250ms/game |
| Accuracy (2023-25) | 99.9% | 100% |
| Accuracy (2010-22) | 99.5% | 99.9% |
| Accuracy (Pre-2010) | 95% | 98% |
| Storage Compression | 10:1 | 15:1 |
| Query Response | <100ms | <50ms |

---

## Cost Breakdown

**One-Time Costs:** $0 (using existing infrastructure)

**Recurring Costs:**
- S3 Storage: +$0.50-1.00/month (~5 GB Parquet files)
- RDS Storage: +$0.20/month (new tables)
- Data Transfer: +$0.10/month (S3 ↔ RDS)
- **Total**: +$0.80-1.30/month

**Development Time:** 12 weeks (480 hours)

---

## Risk Mitigation

**Risk 1: Data Quality Issues**
- Mitigation: Strict verification, quality grading (A-F)
- Fallback: Mark games uncertain, exclude from training

**Risk 2: Processing Too Slow**
- Mitigation: Parallel processing, caching, optimization
- Fallback: Process incrementally, prioritize recent games

**Risk 3: Storage Costs Exceed Budget**
- Mitigation: Compression, sampling, archiving
- Fallback: Store key snapshots only, not every play

**Risk 4: Verification Failures**
- Mitigation: Extensive testing, gradual rollout
- Fallback: Manual review, adjust logic

---

## Quick Start

**To begin Phase 2:**

1. Read complete plan (if exists): `~/Downloads/pbp_to_boxscore_plan.md`
2. Read Claude Code instructions: `~/Downloads/claude_code_instructions.md`
3. Create code structure: See 2.0 for directory setup
4. Start with 2.1 (ESPN processor) - highest priority

**Critical Files (if available):**
- Complete plan: `~/Downloads/pbp_to_boxscore_plan.md` (73 pages)
- Implementation guide: `~/Downloads/claude_code_instructions.md` (35 pages)
- Integration guide: `~/Downloads/integration_instructions.md` (30 pages)
- Sub-phase details: `docs/phases/phase_2/*.md`

---

## Workflows

**Workflow #42: Box Score Generation**
- Process single game from PBP
- Generate snapshots
- Verify accuracy
- Store results

**Workflow #43: Batch Processing**
- Process season/date range
- Parallel execution
- Progress tracking
- Error handling

**Workflow #44: Verification**
- Compare generated vs actual
- Calculate discrepancies
- Quality scoring
- Report generation

**Workflow #45: Storage Management**
- Save to RDS
- Export to Parquet
- Local caching
- Backup procedures

---

## Next Steps

**Immediate (Week 0):**
1. Review and approve Phase 2 plan
2. Create sub-phase files (2.0 through 2.8)
3. Set up code directory structure
4. Create database schema

**Week 1:**
1. Implement base processor class
2. Implement box score snapshot structure
3. Set up testing framework
4. Create database tables

**Weeks 2-3:**
1. Implement ESPN processor
2. Test on sample games
3. Implement verification system
4. Process 2023-2025 seasons

---

## Integration with Existing Systems

### Phase 0: Data Collection
- Phase 2 consumes Phase 0 outputs (ESPN, hoopR, NBA API data)
- ADCE (Phase 0.18) can trigger Phase 2 processing for new games
- Data quality from Phase 0.9 ensures clean inputs

### Phase 0.22: Data Inventory & Gap Analysis
- Audit identifies which games have PBP data
- Gap analysis shows missing box scores
- Phase 2 fills gaps by generating from PBP

### Phase 0.20: Monitoring & Observability
- CloudWatch tracks Phase 2 processing metrics
- Alarms trigger on verification failures
- Dashboard shows generation progress

### Phase 5: Machine Learning
- Phase 2 box score snapshots feed Phase 5 ML models
- Temporal features extracted from snapshots
- Quarter-level predictions use Phase 2 data

---

## Files to Create

**Core Processors:**
```
scripts/pbp_to_boxscore/base_processor.py          # Abstract base class
scripts/pbp_to_boxscore/espn_processor.py          # ESPN implementation
scripts/pbp_to_boxscore/hoopr_processor.py         # hoopR implementation
scripts/pbp_to_boxscore/nba_api_processor.py       # NBA API implementation
scripts/pbp_to_boxscore/kaggle_processor.py        # Kaggle implementation
```

**Data Models:**
```
scripts/pbp_to_boxscore/models/box_score_snapshot.py    # Snapshot structure
scripts/pbp_to_boxscore/models/player_stats.py          # Player stats
scripts/pbp_to_boxscore/models/team_stats.py            # Team stats
scripts/pbp_to_boxscore/models/game_metadata.py         # Game info
```

**Utilities:**
```
scripts/pbp_to_boxscore/verifier.py                # Verification logic
scripts/pbp_to_boxscore/storage.py                 # RDS/S3 storage
scripts/pbp_to_boxscore/metrics.py                 # Advanced metrics
scripts/pbp_to_boxscore/batch_processor.py         # Batch processing
```

**Database:**
```
sql/phase2_box_score_snapshots.sql                 # Database schema
```

---

## Common Issues & Solutions

### Issue 1: Play-by-play events missing
**Cause:** Incomplete data from source
**Solution:** Use multi-source reconciliation, mark games as incomplete

### Issue 2: Verification fails
**Cause:** Discrepancy between generated and actual box scores
**Solution:** Detailed diff analysis, adjust processor logic, quality grading

### Issue 3: Performance too slow
**Cause:** Processing every event creates too many snapshots
**Solution:** Configurable snapshot frequency (every play vs every minute)

### Issue 4: Storage costs high
**Cause:** Uncompressed snapshots take too much space
**Solution:** Parquet compression, selective storage, archiving old games

---

## Workflows Referenced

- **Workflow #42:** Box Score Generation - Single game processing
- **Workflow #43:** Batch Processing - Season/range processing
- **Workflow #44:** Verification - Accuracy validation
- **Workflow #45:** Storage Management - RDS/S3 operations
- **Workflow #21:** Data Validation - Quality checks
- **Workflow #16:** Testing - Test framework setup

---

## Related Documentation

**Play-by-Play Data:**
- [DATA_CATALOG.md](../DATA_CATALOG.md) - Data source inventory
- [DATA_STRUCTURE_GUIDE.md](../DATA_STRUCTURE_GUIDE.md) - S3 bucket layout
- [TEMPORAL_QUERY_GUIDE.md](../TEMPORAL_QUERY_GUIDE.md) - Query patterns

**Architecture:**
- [ADR-010](adr/010-four-digit-subphase-numbering.md) - Sub-phase numbering
- [README.md](../../README.md) - Project vision and simulation methodology

---

## Navigation

**Return to:** [All Phases](README.md)

**Prerequisites:**
- [Phase 0: Data Collection](PHASE_0_INDEX.md) - ✅ COMPLETE

**Enables:**
- Phase 3: RDS PostgreSQL - Temporal query system
- Phase 4: Simulation Engine - Context-adaptive simulations
- Phase 5: Machine Learning - Advanced temporal features

---

## How Phase 2 Enables the Simulation Vision

This phase provides **temporal box score snapshots** that power the **hybrid econometric + nonparametric simulation system** described in the [main README](../../README.md#simulation-methodology).

**What this phase enables:**

### 1. Econometric Causal Inference
From this phase's box score snapshots, we can:
- **Estimate player performance projections (PPP)** using panel data regression on temporal stats
- **Model substitution effects** by comparing before/after snapshots of player substitutions
- **Quantify rest impact** by analyzing performance degradation across quarters
- **Validate fatigue models** with granular minute-by-minute stat changes

### 2. Nonparametric Event Modeling
From this phase's temporal data, we build:
- **Quarter-specific distributions** for shot selection, foul rates, turnover patterns
- **Context-adaptive kernels** that adjust based on game state (score, time, fouls)
- **Player-specific event models** using historical snapshots as training data
- **Dynamic probability surfaces** that evolve as game state changes

### 3. Context-Adaptive Simulations
Using this phase's snapshots, simulations can:
- **Initialize from any game state** (e.g., "LeBron with 25 points at 7:02 Q3")
- **Model quarter-specific strategies** (different play patterns in Q1 vs Q4)
- **Incorporate lineup effects** by comparing actual vs expected performance
- **Validate simulations** against real box score progressions

**Example Use Case:**
> "Simulate the 4th quarter of Warriors vs Lakers if Steph Curry had 35 points (not 28) at the end of Q3"

Phase 2 provides the Q3-ending snapshot (actual state) and Q4 snapshots (validation data) to make this possible.

**See [main README](../../README.md) for complete methodology.**

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-11 | 1.0 | Initial Phase 9 index created from external plan | Claude |
| 2025-10-25 | 2.0 | Promoted to Phase 2 (from Phase 9) during comprehensive reorganization | Claude |

---

**Last Updated:** October 25, 2025 (Promoted from Phase 9)
**Status:** ⏸️ PENDING - Ready for implementation
**Migrated By:** Comprehensive Phase Reorganization (ADR-010)
**Next Action:** Review plan, create sub-phase files, begin implementation

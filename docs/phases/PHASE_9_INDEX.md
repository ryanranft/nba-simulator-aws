# Phase 9: Play-by-Play to Box Score Generation System

**Version:** 1.0
**Created:** October 11, 2025
**Status:** ⏸️ PENDING (📚 2 enhancement recommendations available)
**Priority:** HIGH
**Timeline:** 12 weeks (3 months)
**Cost Impact:** +$0.80-1.30/month

---

## Overview

Generate granular box score snapshots from play-by-play (PBP) data to enable:

1. **Temporal Box Scores**: Complete box score state after each play-by-play event
2. **Quarter Box Scores**: Separate stats for each quarter (betting odds forecasting)
3. **Verification System**: Compare generated final box scores against actual box scores
4. **Advanced Metrics**: Platform to add metrics not in original data
5. **ML Enhancement**: More accurate predictions with granular state data

**Strategy:** Start with recent games (2023-2025) where data is most accurate, then work backwards.

---

## Dependencies

**Required:**
- Phase 0 complete (data collection)
- ESPN play-by-play data in S3 (44,826 games)
- hoopR play-by-play data in RDS (13M rows)
- NBA API play-by-play data (1995-2006)
- Actual box scores for verification

**Optional:**
- Kaggle historical data for older games
- Basketball Reference data for cross-validation

---

## Sub-Phases

| Sub-Phase | Status | Timeline | Priority | Dependencies |
|-----------|--------|----------|----------|--------------|
| 9.0: System Architecture | ⏸️ | 1-2 weeks | CRITICAL | None |
| 9.1: ESPN Processor | ⏸️ | 2-3 weeks | CRITICAL | 9.0 |
| 9.2: hoopR Processor | ⏸️ | 2 weeks | HIGH | 9.1 |
| 9.3: NBA API Processor | ⏸️ | 2 weeks | MEDIUM | 9.1, 9.2 |
| 9.4: Kaggle Processor | ⏸️ | 1 week | LOW | 9.1-9.3 |
| 9.5: Storage System | ⏸️ | 1 week | HIGH | 9.1 |
| 9.6: Advanced Metrics | ⏸️ | 2-3 weeks | MEDIUM | 9.5 |
| 9.7: ML Integration | ⏸️ | 2 weeks | HIGH | 9.6 |
| 9.8: Betting Integration | ⏸️ | 3 weeks | MEDIUM | 9.7 |

---

## Quick Start

**To begin Phase 9:**

1. Read complete plan: `~/Downloads/pbp_to_boxscore_plan.md`
2. Read Claude Code instructions: `~/Downloads/claude_code_instructions.md`
3. Create code structure: See 9.0 for directory setup
4. Start with 9.1 (ESPN processor) - highest priority

**Critical Files:**
- Complete plan: `~/Downloads/pbp_to_boxscore_plan.md` (73 pages)
- Implementation guide: `~/Downloads/claude_code_instructions.md` (35 pages)
- Integration guide: `~/Downloads/integration_instructions.md` (30 pages)
- Sub-phase details: `docs/phases/phase_9/*.md`

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

| Source | Games | Date Range | Priority | Notes |
|--------|-------|------------|----------|-------|
| ESPN | 44,826 | 1993-2025 | HIGHEST | Start here, best quality |
| hoopR | ~30,000 | 2002-2025 | HIGH | Cross-validation |
| NBA API | ~22,000 | 1995-2006 | MEDIUM | Historical |
| Kaggle | 65,698 | 1946-2020 | LOW | Very old data |

---

## Success Criteria

**Minimum Viable Product (MVP):**
- ✅ Process all 2023-2025 ESPN games (~2,952 games)
- ✅ 99%+ verification accuracy
- ✅ Quarter-by-quarter box scores generated
- ✅ Stored in RDS + S3
- ✅ Basic ML feature set created

**Full Success:**
- ✅ All data sources processed (1993-2025)
- ✅ Multi-source cross-validation
- ✅ Advanced metrics implemented
- ✅ ML models trained with quarter predictions
- ✅ Betting model with ROI tracking

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

**Immediate:**
1. Review and approve Phase 9 plan
2. Create sub-phase files (9.0 through 9.8)
3. Set up code directory structure
4. Create database schema

**Week 1:**
1. Implement base processor class
2. Implement box score snapshot structure
3. Set up testing framework
4. Create database tables

**Week 2-3:**
1. Implement ESPN processor
2. Test on sample games
3. Implement verification system
4. Process 2023-2025 seasons

---

## References

- **Complete Plan**: `~/Downloads/pbp_to_boxscore_plan.md` (73 pages)
- **Claude Code Instructions**: `~/Downloads/claude_code_instructions.md` (35 pages)
- **Integration Instructions**: `~/Downloads/integration_instructions.md` (30 pages)
- **Data Inventory**: `MASTER_DATA_INVENTORY.md`
- **Sub-Phase Files**: `docs/phases/phase_9/*.md`

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-11 | 1.0 | Initial Phase 9 index created from external plan | Claude |

---

**Status:** Ready for approval
**Next Action:** Review plan, create sub-phase files, begin implementation



## New Item: Monitoring Dashboards

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.694022
**Category:** critical
**Priority:** Critical

### Description
From ML Systems book: Ch 8, Ch 9

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: A/B Testing Framework

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.694254
**Category:** important
**Priority:** Important

### Description
From ML Systems book: Ch 7

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Shadow Deployment

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.694369
**Category:** nice_to_have
**Priority:** Nice_To_Have

### Description
From ML Systems book: Ch 7

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---


## New Item: Feedback Loop

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.694486
**Category:** nice_to_have
**Priority:** Nice_To_Have

### Description
From ML Systems book: Ch 9

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---








# Phase 0: Data Collection & Initial Upload

**Status:** 🔄 IN PROGRESS (7 complete, 11 planned) | 📚 **18 Sub-Phases Total**
**Priority:** COMPLETE
**Prerequisites:** None (foundational phase)
**Estimated Time:** Total: 150+ hours (✅ complete)
**Cost Impact:** $2.74/month (stable)
**Started:** September 29, 2025
**Completed:** October 13, 2025
**Enhancement Opportunities:** [Book Recommendations](phase_0/RECOMMENDATIONS_FROM_BOOKS.md) - 6 recommendations from technical books

> **📋 Note:** ML-related implementations moved to Phase 5 (October 18-21, 2025):
> - `5.1_feature_engineering/` (formerly `phase_0/rec_11_feature_engineering/`)
> - `5.2_model_versioning/` (formerly `phase_0/ml_systems_1_model_versioning/`)
> - `5.19_drift_detection/` (formerly `phase_0/ml_systems_2_drift_detection/`)
> - `5.20_panel_data/` (formerly `phase_0/rec_22_panel_data/`)
>
> See [PHASE_5_INDEX.md](PHASE_5_INDEX.md) for these implementations.

---

## Overview

Get raw data from multiple sources into AWS S3 with temporal precision. This is the **foundation phase** for the NBA temporal panel data system - all subsequent phases depend on temporally-indexed data being available in S3.

**⚠️ IMPORTANT: This is a temporal panel data system, not a traditional game simulator.**

See `docs/PROJECT_VISION.md` for the complete vision.

**Phase 0 Sub-Phases:**

**Data Sources (0.1-0.7):**
- **0.1** - ESPN Initial Upload (local machine → S3, 146K files) ✅ COMPLETE
- **0.2** - hoopR Data Collection (R package → RDS, 30K games) ✅ COMPLETE
- **0.3** - Kaggle Historical Database (2004-2020, 26K games) ✅ COMPLETE
- **0.4** - Basketball Reference (web scraping, 13 tiers, 79 years) ✅ COMPLETE
- **0.5** - NBA Stats API Collection (2020-2025, 22K files) ✅ COMPLETE
- **0.6** - ESPN Additional Scraping (3,230 games) ✅ COMPLETE
- **0.7** - Odds API Data (betting lines from The Odds API) 🔵 PLANNED

**Infrastructure (0.8-0.9):**
- **0.8** - Security Implementation (13 variations) ✅ COMPLETE
- **0.9** - Data Extraction & Structured Output ✅ COMPLETE

**Advanced Features (0.10-0.18):**
- **0.10-0.12** - PostgreSQL implementations (JSONB, pgvector, RAG+LLM) 🔵 PLANNED
- **0.13-0.18** - Book recommendations (dispatcher, error analysis, etc.) 🔵 PLANNED

**Temporal precision levels:**
- 2020-2025: Millisecond precision (NBA Live API - future)
- 1993-2019: Minute-level precision (NBA Stats PlayByPlayV2)
- 1946-1992: Game-level aggregates (Basketball Reference)

---

## Sub-Phases

| Sub-Phase | Name | Status | Time | Records | Cost | File |
|-----------|------|--------|------|---------|------|------|
| **0.1** | ESPN Initial Upload | ✅ COMPLETE | 2 days | 146K files | $2.74/mo | [0.1_initial_data_collection/](phase_0/0.1_initial_data_collection/README.md) |
| **0.2** | hoopR Data Collection | ✅ COMPLETE | 6h | 30K games, 13M events | $0.96/mo | [0.2_hoopr_data_collection/](phase_0/0.2_hoopr_data_collection/README.md) |
| **0.3** | Kaggle Historical Database | ✅ COMPLETE | Pre-project | 26K games (2004-2020) | $0 | [0.3_kaggle_historical_database/](phase_0/0.3_kaggle_historical_database/README.md) |
| **0.4** | Basketball Reference Scraping | ✅ COMPLETE | 140-197h | 13 tiers, 79 years | +$0.005/mo | [0.4_basketball_reference/](phase_0/0.4_basketball_reference/README.md) |
| **0.5** | NBA Stats API Collection | ✅ COMPLETE | 5-10h | 22,256 files | $0 | *Completed* |
| **0.6** | ESPN Additional Scraping | ✅ COMPLETE | 8-12h | 3,230 games | $0 | *Completed* |
| **0.7** | Odds API Data | 🔵 PLANNED | ~1 week | Betting lines | $0.25/mo | [0.7_odds_api_data/](phase_0/0.7_odds_api_data/README.md) |
| **0.8** | Security Implementation | ✅ COMPLETE | ~4h | 13 variations | $0 | [0.8_security_implementation/](phase_0/0.8_security_implementation/README.md) |
| **0.9** | Data Extraction & Output | ✅ COMPLETE | ~2h | 1 implementation | $0 | [0.9_data_extraction/](phase_0/0.9_data_extraction/README.md) |
| **0.10** | PostgreSQL JSONB Storage | 🔵 PLANNED | ~1 week | Flexible schema | $0 | [0.10_postgresql_jsonb_storage/](phase_0/0.10_postgresql_jsonb_storage/README.md) |
| **0.11** | RAG Pipeline with pgvector | 🔵 PLANNED | ~1 week | Vector embeddings | $0 | [0.11_rag_pipeline_pgvector/](phase_0/0.11_rag_pipeline_pgvector/README.md) |
| **0.12** | RAG + LLM Integration | 🔵 PLANNED | 4-5 days | LLM integration | Variable | [0.12_rag_llm_integration/](phase_0/0.12_rag_llm_integration/README.md) |
| **0.13** | Dispatcher Pipeline | 🔵 PLANNED | 5-6 days | rec_044 | $5-15/mo | [0.13_dispatcher_pipeline/](phase_0/0.13_dispatcher_pipeline/README.md) |
| **0.14** | Error Analysis | 🔵 PLANNED | 3-4 days | rec_093 | $0 | [0.14_error_analysis/](phase_0/0.14_error_analysis/README.md) |
| **0.15** | Information Availability | 🔵 PLANNED | 3-4 days | rec_180 | $0 | [0.15_information_availability/](phase_0/0.15_information_availability/README.md) |
| **0.16** | Robust Architecture | 🔵 PLANNED | 1 week | rec_189 | $0 | [0.16_robust_architecture/](phase_0/0.16_robust_architecture/README.md) |
| **0.17** | External APIs | 🔵 PLANNED | 4-5 days | rec_191 | Variable | [0.17_external_apis/](phase_0/0.17_external_apis/README.md) |
| **0.18** | Autonomous Data Collection | 🔵 PLANNED | 2 weeks | Multi-source | $0 | [0.18_autonomous_data_collection/](phase_0/0.18_autonomous_data_collection/README.md) |

---

## Archived Sub-Phases

The following sub-phases were archived on October 22, 2025 and superseded by PostgreSQL implementations:

| Original | Name | Reason | Replaced By |
|----------|------|--------|-------------|
| 0.1 (MongoDB) | NoSQL Storage | PostgreSQL JSONB provides same flexibility | [0.10](phase_0/0.10_postgresql_jsonb_storage/README.md) |
| 0.2 (Qdrant) | RAG Pipeline | pgvector provides vector search | [0.11](phase_0/0.11_rag_pipeline_pgvector/README.md) |
| 0.6 (MongoDB+Qdrant) | RAG + LLM | Unified PostgreSQL architecture | [0.12](phase_0/0.12_rag_llm_integration/README.md) |

**See:** [Archive Documentation](phase_0/archive/mongodb_superseded/README.md)

---

## Sub-Phase 0.1: Initial Data Collection

**Status:** ✅ COMPLETE (October 1, 2025)

**What was completed:**
- Local development environment setup
- AWS S3 bucket creation (`nba-sim-raw-data-lake`)
- Upload of 147,382 ESPN JSON files locally (70,522 in S3)
- Data validation and verification
- Documentation of data structure

**Data uploaded:**
- Schedule files: 11,633
- Play-by-play files: 44,826
- Box score files: 44,828
- Team stats files: 44,828

**Cost:** $2.74/month (S3 storage)

**See:** [Sub-Phase 0.1 Details](phase_0/0.1_initial_data_collection/README.md)

---

## Sub-Phase 0.2: Basketball Reference Expansion

**Status:** 🔄 READY TO IMPLEMENT (13 tiers organized, October 11, 2025)

**Overview:**
Comprehensive Basketball Reference data collection covering NBA, WNBA, G League, historical leagues (ABA, BAA), international competitions, and college basketball.

**Scope:**
- **234 data types** across 13 tiers
- **140-197 hours** collection time (depending on tier selection)
- **865K-10.88M records** (varies by completeness level)
- **Multi-domain scraping:** basketball-reference.com, sports-reference.com/cbb/

**Tier Organization:**
- **Tier 1-2:** IMMEDIATE priority (35-45h) - Foundational NBA data
- **Tier 3-4:** HIGH priority (25-35h) - Historical context
- **Tier 5-7:** MEDIUM priority (30-42h) - Advanced analytics
- **Tier 8-9:** LOW priority (13-20h) - Completeness
- **Tier 10-11:** EXECUTE (23-30h) - WNBA + G League
- **Tier 12-13:** OPTIONAL (40-70h) - International + college

**Progressive Detail Levels:**
1. **This index** - Single line per tier with status
2. **Tier Index** - Table row per tier with summary stats ([0.1_basketball_reference/README.md](phase_0/0.1_basketball_reference/README.md))
3. **Quick Reference** - Half-page overview per tier (optional)
4. **Full Tier File** - Complete implementation guide per tier

**Navigation:**
```
PHASE_0_INDEX.md (this file - sub-phase table)
   ↓
0.1_basketball_reference/README.md (tier index - 13 tiers)
   ↓
TIER_1_NBA_HIGH_VALUE.md (400-600 lines - full implementation)
   ↓
Execute data collection, upload to S3
```

**See:** [Basketball Reference Tier Index](phase_0/0.1_basketball_reference/README.md)

---

## Success Criteria

### Sub-Phase 0.1 (Initial Collection)
- [x] S3 bucket created in us-east-1
- [x] All 147,382 files collected locally (70,522 uploaded to S3)
- [x] Total size matches source (119 GB)
- [x] Encryption enabled (SSE-S3)
- [x] Public access blocked
- [x] Cost within budget ($2.74/month)
- [x] Data structure documented
- [x] Local backup created

### Sub-Phase 0.2 (Basketball Reference Expansion)
- [ ] Tier 1-2 completed (IMMEDIATE priority)
- [ ] Tier 3-4 completed (HIGH priority)
- [ ] Tier 5-7 completed (MEDIUM priority - recommended)
- [ ] Tier 8-9 optional (LOW priority)
- [ ] Tier 10-11 executed (WNBA + G League)
- [ ] Tier 12-13 optional (International + college)
- [ ] All data uploaded to S3
- [ ] Data quality checks passed

---

## Cost Breakdown

### Current Costs (Sub-Phase 0.1)
| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| S3 Standard Storage | 119 GB | $2.74 | 119 GB × $0.023/GB |
| S3 GET Requests | Minimal | ~$0.01 | Occasional downloads |
| **Total** | | **$2.74/month** | Recurring storage only |

### Expansion Cost Impact (Sub-Phase 0.2)
| Tier Group | Records | Storage | Cost Impact |
|------------|---------|---------|-------------|
| Tier 1-9 (NBA) | 600K-8M | ~2-10 GB | +$0.05-0.23/mo |
| Tier 10 (WNBA) | 100K | ~500 MB | +$0.01/mo |
| Tier 11 (G League) | 30K | ~150 MB | +$0.003/mo |
| Tier 12-13 (Optional) | 135K-250K | ~500 MB-1 GB | +$0.01-0.02/mo |
| **Total Expansion** | 865K-10.88M | ~3-12 GB | **+$0.07-0.27/mo** |

**Projected Total:** $2.81-3.01/month (still under $5/month target)

---

## Prerequisites

**Before starting Phase 0:**
- [ ] AWS account created
- [ ] AWS CLI installed
- [ ] Local NBA data available (for 0.0)
- [ ] Python 3.11 environment
- [ ] Sufficient local disk space

**For Sub-Phase 0.2 (Basketball Reference):**
- [x] Sub-Phase 0.1 complete (S3 bucket operational)
- [x] Tier structure documented (13 tiers organized)
- [ ] Scraper implementation ready
- [ ] Rate limiting configured (12s between requests)

---

## Key Architecture Decisions

**ADRs created in Phase 0:**
- **ADR-001:** Exclude Redshift (save $200-600/month)
- **ADR-002:** Extract 10% of JSON fields (save 90% storage)
- **ADR-003:** Use Python 3.11 (AWS Glue 4.0 compatibility)
- **ADR-005:** Git SSH authentication (security)
- **ADR-008:** Phase reorganization (logical data flow)

**See:** `docs/adr/README.md` for complete ADRs

---

## Critical Workflows

**For Sub-Phase 0.1 (Initial Collection):**
- Workflow #1: Session Start
- Workflow #17: Environment Setup
- Workflow #18: Cost Management
- Workflow #24: AWS Resource Setup
- Workflow #21: Data Validation

**For Sub-Phase 0.2 (Basketball Reference):**
- Workflow #38: Overnight Scraper Handoff
- Workflow #39: Scraper Monitoring
- Workflow #42: Scraper Management
- Workflow #45: Documentation Organization
- Workflow #46: Phase Index Management (new)

---

## Multi-Sport Replication

**For future sports (NFL, MLB, NHL, Soccer):**

Phase 0 is **sport-agnostic** - follow the same pattern:

1. Create sport-specific S3 bucket (e.g., `nfl-sim-raw-data-lake`)
2. Complete Sub-Phase 0.0 equivalent (initial data upload)
3. Plan Sub-Phase 0.1 equivalent (comprehensive source collection)
4. Follow tier-based organization for scalability

**Example for NFL:**
```bash
# Create bucket
aws s3 mb s3://nfl-sim-raw-data-lake --region us-east-1

# Upload initial data
aws s3 sync /Users/ryanranft/0espn/data/nfl/ \
  s3://nfl-sim-raw-data-lake/ \
  --exclude "*" --include "*.json"
```

Then proceed to Phase 1 (Data Quality) for the new sport.

---

## Troubleshooting

**Common issues:**

1. **AWS CLI not found**
   - AWS CLI installed system-wide, not in conda
   - See Workflow #17 for setup details

2. **Upload interrupted**
   - Use `aws s3 sync` (resumes automatically)
   - See `docs/TROUBLESHOOTING.md`

3. **Basketball Reference rate limiting**
   - Use 12-second delays between requests
   - See Workflow #42 for scraper configuration

4. **Context budget exceeded**
   - Read only 1 tier file at a time
   - Use progressive detail levels
   - See `docs/CONTEXT_MANAGEMENT_GUIDE.md`

---

## Next Steps

**After Sub-Phase 0.1 complete:**
- ✅ S3 bucket operational with initial data
- → Begin Sub-Phase 0.2 (Basketball Reference Tier 1-2)

**After Sub-Phase 0.2 complete:**
- → Proceed to [Phase 1: Data Quality & Gap Analysis](PHASE_1_INDEX.md)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md)
**Previous Phase:** None (first phase)
**Next Phase:** [Phase 1: Data Quality & Gap Analysis](PHASE_1_INDEX.md)
**Workflow Index:** [CLAUDE_WORKFLOW_ORDER.md](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related Documentation:**
- [Data Structure Guide](../DATA_STRUCTURE_GUIDE.md)
- [Project Vision](../PROJECT_VISION.md)
- [Scraper Management](../data_collection/scrapers/MANAGEMENT.md)

---

*For Claude Code: This is the Phase 0 master index. To work on Phase 0, read only the specific sub-phase file you need. Don't read all sub-phases at once.*

---

**Last Updated:** October 23, 2025
**Phase Owner:** Data Collection Team
**Total Sub-Phases:** 18 (7 complete, 11 planned)
**Status:** 🔄 IN PROGRESS (Data sources documented, advanced features pending)


## Enhancement: Add more comprehensive API examples

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:34:43.594041
**Category:** nice_to_have

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## Enhancement: Add more comprehensive API examples

**Source:** Test ML Book, Test Book
**Date Added:** 2025-10-12T14:41:44.912514
**Category:** nice_to_have

### Description
No additional description provided.

### Implementation Notes
- This enhancement was automatically added based on book analysis
- Review and adjust implementation details as needed
- Consider impact on existing phase timeline

---


## New Item: Data Drift Detection

**Source:** Designing Machine Learning Systems
**Date Added:** 2025-10-12T14:43:24.690183
**Category:** critical
**Priority:** Critical

### Description
From ML Systems book: Ch 8

### Implementation Considerations
- This item was automatically added based on book analysis
- Evaluate priority relative to existing phase items
- Consider resource requirements and timeline impact
- May require phase timeline adjustment

---

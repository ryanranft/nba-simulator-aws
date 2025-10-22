# Phase 0: Data Collection & Initial Upload

**Status:** ✅ COMPLETE (All Sub-Phases) | 📚 **6 Book Recommendations Available**
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
- **0.0** - Initial data collection (ESPN data, 146K files) ✅ COMPLETE
- **0.1** - Basketball Reference expansion (13 tiers, 234 data types) ✅ COMPLETE
- **0.2** - ESPN additional scraping ✅ COMPLETE
- **0.3** - NBA API enhanced collection ✅ COMPLETE
- **0.4** - Security implementation (13 variations) ✅ COMPLETE
- **0.5** - Data extraction & structured output ✅ COMPLETE

**Temporal precision levels:**
- 2020-2025: Millisecond precision (NBA Live API - future)
- 1993-2019: Minute-level precision (NBA Stats PlayByPlayV2)
- 1946-1992: Game-level aggregates (Basketball Reference)

---

## Sub-Phases

| Sub-Phase | Name | Status | Time | Records | Cost | File |
|-----------|------|--------|------|---------|------|------|
| **0.0** | Initial Data Collection | ✅ COMPLETE | 2 days | 146K files | $2.74/mo | [0.0_initial_data_collection.md](phase_0/0.0_initial_data_collection.md) |
| **0.1** | Basketball Reference Expansion | ✅ COMPLETE | 140-197h | 865K-10.88M | +$0.005/mo | [0.1_basketball_reference/](phase_0/0.1_basketball_reference/README.md) |
| **0.2** | ESPN Additional Scraping | ✅ COMPLETE | 8-12h | 3,230 games | $0 | *Completed* |
| **0.3** | NBA API Enhanced Collection | ✅ COMPLETE | 5-10h | 22,256 files | $0 | *Completed* |
| **0.4** | Security Implementation | ✅ COMPLETE | ~4h | 13 variations | $0 | [0.4_security_implementation/](phase_0/0.4_security_implementation/README.md) |
| **0.5** | Data Extraction & Structured Output | ✅ COMPLETE | ~2h | 1 implementation | $0 | [0.5_data_extraction/](phase_0/0.5_data_extraction/README.md) |

---

## Sub-Phase 0.0: Initial Data Collection

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

**See:** [Sub-Phase 0.0 Details](phase_0/0.0_initial_data_collection.md)

---

## Sub-Phase 0.1: Basketball Reference Expansion

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

### Sub-Phase 0.0 (Initial Collection)
- [x] S3 bucket created in us-east-1
- [x] All 147,382 files collected locally (70,522 uploaded to S3)
- [x] Total size matches source (119 GB)
- [x] Encryption enabled (SSE-S3)
- [x] Public access blocked
- [x] Cost within budget ($2.74/month)
- [x] Data structure documented
- [x] Local backup created

### Sub-Phase 0.1 (Basketball Reference Expansion)
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

### Current Costs (Sub-Phase 0.0)
| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| S3 Standard Storage | 119 GB | $2.74 | 119 GB × $0.023/GB |
| S3 GET Requests | Minimal | ~$0.01 | Occasional downloads |
| **Total** | | **$2.74/month** | Recurring storage only |

### Expansion Cost Impact (Sub-Phase 0.1)
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

**For Sub-Phase 0.1 (Basketball Reference):**
- [x] Sub-Phase 0.0 complete (S3 bucket operational)
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

**For Sub-Phase 0.0 (Initial Collection):**
- Workflow #1: Session Start
- Workflow #17: Environment Setup
- Workflow #18: Cost Management
- Workflow #24: AWS Resource Setup
- Workflow #21: Data Validation

**For Sub-Phase 0.1 (Basketball Reference):**
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

**After Sub-Phase 0.0 complete:**
- ✅ S3 bucket operational with initial data
- → Begin Sub-Phase 0.1 (Basketball Reference Tier 1-2)

**After Sub-Phase 0.1 complete:**
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

**Last Updated:** October 18, 2025
**Phase Owner:** Data Collection Team
**Total Sub-Phases:** 6
**Status:** ✅ COMPLETE (all 6 sub-phases done)


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

# Phase 2: AWS Glue ETL Pipeline

**Status:** ✅ COMPLETE (📚 5 enhancement recommendations available)
**Priority:** HIGH
**Prerequisites:** Phase 0 complete, Phase 1 recommended
**Estimated Time:** 3-4 hours
**Cost Impact:** $13/month (Glue jobs)
**Started:** October 2, 2025
**Completed:** October 2, 2025

---

## Overview

Extract raw JSON from S3, transform into structured format, and load into RDS PostgreSQL with temporal indexing. This phase creates the ETL pipeline that converts raw data into queryable database records.

**This phase delivers:**
- AWS Glue job configuration
- JSON to DataFrame extraction
- Field selection (53 essential fields from 200+ available)
- Temporal timestamp indexing
- RDS database loading
- Automated ETL scheduling

**Why ETL matters:**
- Reduces storage by 90% (extract only needed fields)
- Enables SQL queries for temporal analysis
- Prepares data for ML feature engineering
- Establishes single source of truth in RDS

---

## Sub-Phases

| Sub-Phase | Name | Status | Time | File |
|-----------|------|--------|------|------|
| **2.0** | AWS Glue ETL Pipeline | ✅ COMPLETE ✓ | 3-4h | Oct 23, 2025 |

---

## Sub-Phase 2.0: AWS Glue ETL Pipeline

**Status:** ✅ COMPLETE (October 2, 2025)

**What was completed:**
- Created Glue Data Catalog database
- Configured Glue crawlers for S3 schema discovery
- Developed PySpark extraction scripts
- Implemented field selection (53 fields)
- Set up RDS loading pipeline
- Tested end-to-end ETL flow
- Documented Glue job configuration

**Key Components:**
1. **Glue Crawler:** Auto-discover JSON schema in S3
2. **Glue Job:** PySpark script for extraction/transformation
3. **RDS Connection:** Secure database loading
4. **Scheduling:** Optional automated daily runs

**Fields Extracted:** 53 core fields (games, players, teams, stats)

**See:** [Sub-Phase 2.0 Details](phase_2/2.0_aws_glue_etl.md)

---

## Success Criteria

- [x] Glue Data Catalog created
- [x] Glue crawler operational
- [x] PySpark extraction script working
- [x] Field selection optimized (53 fields)
- [x] RDS connection configured
- [x] ETL job tested end-to-end
- [x] Cost under $15/month
- [x] Documentation complete

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| AWS Glue Jobs | DPU=2, sporadic runs | $13/month | ~6.5 hours/month runtime |
| Glue Crawler | Weekly crawls | ~$0.50/month | Schema discovery |
| **Total Phase Cost** | | **$13.50/month** | Can be reduced with scheduling |

**Cost Optimization:**
- Run Glue jobs only when new data arrives
- Use smaller DPU values for development
- Schedule crawlers less frequently (weekly vs daily)

---

## Prerequisites

**Before starting Phase 2:**
- [x] Phase 0 complete (S3 data available)
- [x] RDS PostgreSQL instance created (Phase 3)
- [ ] AWS Glue IAM roles configured
- [ ] Network security groups allow Glue → RDS connection

**Note:** Phase 2 and Phase 3 can be done in parallel or in either order.

---

## Key Architecture Decisions

**ADRs created in Phase 2:**
- **ADR-002:** Extract 10% of JSON fields (save 90% storage)
- Field selection strategy documented
- PySpark over Python Pandas (scalability)

**See:** `docs/adr/README.md`

---

## Multi-Sport Replication

**When adding a new sport (NFL, MLB, NHL, Soccer):**

This phase is **sport-agnostic** - follow the same pattern:

1. Create Glue crawler for sport-specific S3 prefix
   ```bash
   # Example for NFL
   aws glue create-crawler --name nfl-data-crawler \
     --database-name nfl-data-catalog \
     --s3-target Path=s3://nfl-sim-raw-data-lake/
   ```

2. Adapt PySpark script for sport-specific fields
3. Configure RDS connection for sport-specific tables
4. Test ETL end-to-end

**Glue job is reusable** - same code pattern works for all sports with minimal field mapping changes.

---

## Key Workflows

**For Sub-Phase 2.0:**
- Workflow #24: AWS Resource Setup
- Workflow #18: Cost Management
- Workflow #11: Error Handling
- Workflow #2: Command Logging

---

## Troubleshooting

**Common issues:**

1. **Glue job fails with OOM errors**
   - Solution: Increase DPU from 2 to 5-10
   - Or: Process data in smaller batches

2. **RDS connection timeout**
   - Solution: Check security groups allow Glue → RDS
   - Verify RDS endpoint and credentials

3. **JSON parsing errors**
   - Solution: Handle malformed JSON with try/except
   - Log errors to CloudWatch for review

4. **High Glue costs**
   - Solution: Schedule jobs instead of running continuously
   - Reduce DPU for development/testing

---

## Next Steps

**After Phase 2 complete:**
- ✅ ETL pipeline operational
- → Proceed to [Phase 3: Database Infrastructure](PHASE_3_INDEX.md) (if not already done)
- → Or proceed to [Phase 4: Simulation Engine](PHASE_4_INDEX.md)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md)
**Previous Phase:** [Phase 1: Data Quality](PHASE_1_INDEX.md)
**Next Phase:** [Phase 3: Database Infrastructure](PHASE_3_INDEX.md)
**Workflow Index:** [CLAUDE_WORKFLOW_ORDER.md](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related Documentation:**
- [Data Structure Guide](../DATA_STRUCTURE_GUIDE.md)
- [Glue Job Scripts](../../scripts/etl/glue/)

---

*For Claude Code: This phase has a single sub-phase. Read the sub-phase file for implementation details.*

---

**Last Updated:** October 11, 2025
**Phase Owner:** ETL Team
**Total Sub-Phases:** 1
**Status:** 100% complete (1 of 1 sub-phases done)


## How Phase 2 Enables the Simulation Vision

This phase provides [data/infrastructure/capability] that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../README.md#simulation-methodology).

**What this phase enables:**

### 1. Econometric Causal Inference
From this phase's outputs, we can:
- [Specific econometric technique enabled]
- [Example: PPP estimation using panel data regression]

### 2. Nonparametric Event Modeling
From this phase's data, we build:
- [Specific nonparametric technique enabled]
- [Example: Kernel density estimation for technical fouls]

### 3. Context-Adaptive Simulations
Using this phase's data, simulations can adapt to:
- [Game situation context]
- [Player/team specific factors]

**See [main README](../../README.md) for complete methodology.**

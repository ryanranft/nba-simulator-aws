# AWS Glue Data Catalog Strategy

**Purpose:** Cloud-based data indexing and schema discovery as replacement for local PyCharm indexing
**Created:** October 22, 2025
**Status:** 📋 PLANNED (Future Phase)
**Cost:** ~$1/month for 100K objects

---

## Overview

This document describes the strategy for using **AWS Glue Data Catalog** as a cloud-based metadata and indexing solution for the 117GB `/data` folder. This is **separate from the abandoned Phase 2.0 ETL use case** - we're using Glue Catalog purely for metadata discovery and queryability, not for ETL transformations.

---

## Problem Statement

**Current Issue:**
- PyCharm attempting to index 117GB of NBA data files locally
- Causes performance degradation and excessive cache usage
- Reduces available cache for LLM operations
- Local indexing provides minimal value for large JSON datasets

**Solution:**
- Exclude `/data` folder from PyCharm indexing (✅ Complete)
- Use AWS Glue Data Catalog for cloud-based schema discovery
- Query data metadata via Amazon Athena when needed
- Zero local storage overhead

---

## Why This Differs from Abandoned Phase 2.0

### Phase 2.0 (Abandoned) - AWS Glue ETL
**Use Case:** Data extraction and transformation
**Status:** ❌ Abandoned due to scale issues
**Reason for Abandonment:**
- Glue Crawler failed with 146K+ files (OutOfMemoryError)
- Deeply nested JSON caused Internal Service Exceptions
- Needed full control over extraction logic
- Local Python scripts proved more reliable

**Reference:** `docs/phases/phase_2/2.0_aws_glue_etl.md`

### This Strategy - AWS Glue Data Catalog
**Use Case:** Metadata indexing and schema discovery
**Status:** 📋 Planned for future implementation
**Key Differences:**
- **No extraction** - Data remains in S3
- **No transformations** - Just metadata cataloging
- **Lightweight crawling** - Only reads schemas, not full files
- **Different scale considerations** - Catalog handles metadata, not data processing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Local Development                         │
│                                                              │
│  ┌──────────────┐         ┌─────────────────────────────┐   │
│  │  PyCharm     │         │  /data folder               │   │
│  │              │    ✗    │  (excluded from indexing)   │   │
│  │  (no local   │  ───────│  117GB NBA data             │   │
│  │   indexing)  │         │                             │   │
│  └──────────────┘         └─────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ S3 Upload
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                            │
│                                                              │
│  ┌──────────────────────┐                                   │
│  │  S3 Bucket           │                                   │
│  │  nba-sim-raw-data    │                                   │
│  │  70,522 files        │                                   │
│  └──────────────────────┘                                   │
│            │                                                 │
│            │ Crawls (schema only)                            │
│            ▼                                                 │
│  ┌──────────────────────┐                                   │
│  │  Glue Data Catalog   │                                   │
│  │  - Schemas           │                                   │
│  │  - Partitions        │                                   │
│  │  - Metadata          │                                   │
│  └──────────────────────┘                                   │
│            │                                                 │
│            │ Queries                                         │
│            ▼                                                 │
│  ┌──────────────────────┐                                   │
│  │  Amazon Athena       │                                   │
│  │  SQL queries on      │                                   │
│  │  data + metadata     │                                   │
│  └──────────────────────┘                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Benefits

### 1. Local Performance
- ✅ Frees 117GB from PyCharm indexing
- ✅ Reduces cache usage for LLM operations
- ✅ Improves IDE responsiveness
- ✅ No local storage overhead

### 2. Cloud-Based Schema Discovery
- ✅ Automatic schema detection for JSON/CSV files
- ✅ Partition detection (by year, season, team, etc.)
- ✅ Centralized metadata catalog
- ✅ Version tracking of schema changes

### 3. Queryability
- ✅ SQL queries via Athena on data metadata
- ✅ Quick schema lookups without downloading files
- ✅ Data exploration without local loading
- ✅ Cross-dataset queries

### 4. Cost Efficiency
- ✅ ~$1/month for 100K objects cataloged
- ✅ Pay-per-query with Athena (~$5/TB scanned)
- ✅ No EC2/compute costs (serverless)
- ✅ Much cheaper than local indexing overhead

---

## Implementation Plan (Future Phase)

### Phase 1: Initial Catalog Setup (1-2 hours)

**Prerequisites:**
- ✅ S3 data uploaded (70,522 files in `s3://nba-sim-raw-data-lake`)
- ✅ AWS CLI configured
- ✅ IAM permissions for Glue

**Steps:**
1. Create Glue Database
   ```bash
   aws glue create-database \
     --database-input '{"Name": "nba_data_catalog"}'
   ```

2. Configure selective crawlers (avoid Phase 2.0 mistakes)
   - **Option A:** Year-based crawlers (365-366 files each)
   - **Option B:** Data-type crawlers (box scores, play-by-play, schedules)
   - **Option C:** Schema-only sampling (crawl 5% of files for representative schema)

3. Run Glue Crawler (metadata only)
   ```bash
   aws glue start-crawler --name nba-schedule-crawler
   ```

**Expected Outcome:**
- Glue Catalog contains table schemas
- Partitions detected (by year, season, etc.)
- Ready for Athena queries

### Phase 2: Athena Integration (30 minutes)

**Steps:**
1. Configure Athena workgroup
2. Set up S3 output location for query results
3. Test sample queries:
   ```sql
   -- Show all tables in catalog
   SHOW TABLES IN nba_data_catalog;

   -- Describe schema
   DESCRIBE nba_data_catalog.play_by_play;

   -- Sample data query
   SELECT * FROM nba_data_catalog.play_by_play
   WHERE season = '2023-24'
   LIMIT 10;
   ```

**Expected Outcome:**
- SQL-queryable metadata catalog
- No local file downloads needed
- Fast schema exploration

### Phase 3: Documentation & Workflows (1 hour)

**Tasks:**
- Document query patterns for NBA data
- Create helper scripts for common metadata queries
- Add to project workflows
- Update SETUP.md with Athena access instructions

---

## Use Cases

### 1. Schema Discovery
**Scenario:** Need to understand structure of play-by-play files
**Without Glue:** Download files, open in editor, inspect manually
**With Glue:**
```sql
DESCRIBE nba_data_catalog.play_by_play;
```

### 2. Data Exploration
**Scenario:** Find all games from a specific season
**Without Glue:** Search through 70K files locally
**With Glue:**
```sql
SELECT game_id, home_team, away_team
FROM nba_data_catalog.schedule
WHERE season = '2023-24';
```

### 3. Schema Version Tracking
**Scenario:** Verify schema changes after data updates
**Without Glue:** Manual file comparison
**With Glue:** Glue Catalog version history

### 4. Cross-Dataset Queries
**Scenario:** Join schedules with box scores
**Without Glue:** Load both datasets into memory
**With Glue:**
```sql
SELECT s.game_id, s.home_team, b.total_points
FROM nba_data_catalog.schedule s
JOIN nba_data_catalog.box_scores b ON s.game_id = b.game_id
WHERE s.season = '2023-24';
```

---

## Cost Analysis

### Monthly Costs (Estimated)

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **Glue Data Catalog** | 100K objects stored | ~$1.00 | $1 per 100K objects above free tier |
| **Glue Crawler** | 1 run/month | ~$0.44 | $0.44 per DPU-hour, ~1 DPU for metadata only |
| **Athena Queries** | 100 queries/month (~1GB scanned each) | ~$0.50 | $5 per TB scanned |
| **S3 GET Requests** | ~1K requests/month | ~$0.01 | Minimal for metadata queries |
| **Total** | | **~$2/month** | Scales with query volume |

### Cost Comparison

| Approach | Setup Cost | Monthly Cost | Performance Impact |
|----------|------------|--------------|-------------------|
| **Local PyCharm Indexing** | $0 | $0 | High (117GB cache usage) |
| **AWS Glue Catalog** | ~$1 | ~$2/month | Zero (cloud-based) |

**ROI:** Improved local performance + cloud queryability for ~$2/month

---

## Limitations & Considerations

### When NOT to Use Glue Catalog

1. **Real-time data needs** - Glue Catalog updates are eventual consistency
2. **High query volume** - Athena costs scale with data scanned
3. **Complex transformations** - Use local scripts (per Phase 2.0 lessons)
4. **Large file processing** - Glue Crawler may still fail (>100K files)

### Mitigation Strategies

1. **For large file counts:**
   - Use year-based crawlers (365-366 files each)
   - Sample-based schema discovery (5-10% of files)
   - Manual table creation with representative schema

2. **For query costs:**
   - Use partitioning to limit scan volume
   - Create views for common queries
   - Cache query results locally when needed

3. **For real-time needs:**
   - Continue using RDS for operational queries
   - Use Glue Catalog only for exploratory/metadata queries

---

## Differences from Phase 2.0 Lessons

### Phase 2.0 Lessons Applied

From `docs/phases/phase_2/2.0_aws_glue_etl.md`:

**What failed in Phase 2.0:**
- ❌ Single crawler on 70K+ files → OutOfMemoryError
- ❌ Deeply nested JSON (5+ levels) → Internal Service Exception
- ❌ ETL transformations at scale

**How this strategy differs:**
- ✅ **Metadata only** - Not processing full file contents
- ✅ **Selective crawling** - Year-based or sample-based
- ✅ **No transformations** - Just schema discovery
- ✅ **Read-only** - Data stays in S3, no writes
- ✅ **Different scale** - Cataloging 100K objects, not processing them

**Key insight:** Glue Catalog is viable for **metadata indexing**, even though Glue ETL failed for **data processing** at this scale.

---

## Success Criteria

**When implemented, this strategy will be successful if:**
- [ ] PyCharm performance improved (no local indexing of 117GB)
- [ ] LLM cache freed up for operations
- [ ] Glue Catalog contains schemas for all data types
- [ ] Athena queries return results in <10 seconds
- [ ] Monthly costs stay under $5
- [ ] No local file downloads needed for schema exploration
- [ ] Documentation enables easy metadata queries

---

## Next Steps

**Not implemented yet - planned for future phase**

**To implement:**
1. Read this document to understand strategy
2. Verify S3 data is organized with partitions
3. Follow Phase 1 implementation steps
4. Test Athena queries
5. Document query patterns
6. Update SETUP.md with access instructions

**Decision Points:**
- **Timing:** Implement when need frequent schema exploration
- **Priority:** Low (current RDS + local scripts working well)
- **Trigger:** When need cross-dataset queries or metadata search

---

## References

**Related Documentation:**
- `docs/phases/phase_2/2.0_aws_glue_etl.md` - Why ETL was abandoned (different use case)
- `docs/DATA_STRUCTURE_GUIDE.md` - Current data structure
- `docs/SETUP.md` - AWS configuration
- `PROGRESS.md` - Project status

**AWS Documentation:**
- [AWS Glue Data Catalog](https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html)
- [Amazon Athena](https://docs.aws.amazon.com/athena/latest/ug/what-is.html)
- [Glue Crawler Best Practices](https://docs.aws.amazon.com/glue/latest/dg/crawler-best-practices.html)

**Workflows:**
- Workflow #34 - Lessons Learned Review (check Phase 2.0 failures)
- Workflow #03 - Decision Workflow (document ADR if implementing)
- Workflow #21 - Data Validation (verify catalog accuracy)

---

## Navigation

**Return to:** [PROGRESS.md](../PROGRESS.md) | [Documentation Index](docs/README.md)

**Related:**
- [Phase 2.0 AWS Glue ETL (Abandoned)](docs/phases/phase_2/2.0_aws_glue_etl.md)
- [Data Structure Guide](docs/DATA_STRUCTURE_GUIDE.md)
- [Setup Guide](docs/SETUP.md)

---

*For Claude Code: This is a planned future enhancement. Current priority is Phase 5+ ML work.*

---

*Last updated: 2025-10-22*
*Created in response to: PyCharm indexing performance issues with 117GB data folder*
*Status: Documentation complete, implementation pending*

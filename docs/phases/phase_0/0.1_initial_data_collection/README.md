# Phase 0: Data Collection & Initial Upload

**Status:** ✅ COMPLETE
**Prerequisites:** None (foundational phase)
**Estimated Time:** 2 days
**Estimated Cost:** $2.74/month (S3 storage)
**Started:** September 29, 2025
**Completed:** October 1, 2025

---

> **📌 NOTE - Phase Reorganization:**
>
> This is the NEW Phase 0 as of October 4, 2025 (ADR-008).
> Previously, this content was in OLD Phase 1 (S3 Data Lake Setup).
>
> **Old structure:** Phase 0 = Data Verification → Phase 1 = S3 Upload
> **New structure:** Phase 0 = Data Collection → Phase 1 = Quality Analysis
>
> See `docs/adr/008-phase-reorganization.md` for rationale.

---

## Overview

Get raw data from multiple sources into AWS S3 with temporal precision. This is the **foundation phase** for the NBA temporal panel data system - all subsequent phases depend on temporally-indexed data being available in S3.

**⚠️ IMPORTANT: This is a temporal panel data system, not a traditional game simulator.**

See `docs/PROJECT_VISION.md` for the complete vision.

**This phase includes:**
- Local development environment setup
- AWS S3 bucket creation
- Multi-source data collection with temporal timestamps
- ESPN data (146,115 files, 119GB) - primary historical data
- NBA API data (~366,486 files) - temporal precision data with wall clock timestamps
- Basketball Reference, hoopR, Kaggle - supplementary sources

**What happens in this phase:**
- Collect play-by-play data with wall clock timestamps for temporal alignment
- Collect player birth dates for precise age calculations
- Establish S3 as the single source of truth for temporal raw data
- Enable snapshot queries: "Show me NBA state at exactly 7:02:34 PM on June 19, 2016"

**Temporal precision levels:**
- 2020-2025: Millisecond precision (NBA Live API - future)
- 1993-2019: Minute-level precision (NBA Stats PlayByPlayV2)
- 1946-1992: Game-level aggregates (Basketball Reference)

---

## 📊 Data Growth Tracking (ADCE Integration)

**This documentation now uses ADCE (Autonomous Data Collection Ecosystem) for live data tracking.**

Instead of hardcoded file counts, the validation scripts query S3 in real-time to show:
- **Phase 0.1 Initial Upload Baseline** (October 2024)
- **ADCE Autonomous Collection Additions** (Phase 0.9 onwards)
- **Current Total with Growth Metrics**

**To see current data state, run:**
```bash
cd /Users/ryanranft/nba-simulator-aws/docs/phases/phase_0/0.1_initial_data_collection
python validate_upload_completeness.py
```

### Data Growth Trajectory

| Milestone | Files | Size | Date | Source |
|-----------|-------|------|------|--------|
| **Phase 0.1 Initial Upload** | 146,115 | 119 GB | Oct 2024 | ESPN historical data |
| **ADCE Autonomous Collection** | +25,323 | +TBD | Oct 2025 | 8 new data sources (Phase 0.9) |
| **Current Total** | 172,719* | 118 GB* | _Live_ | Query S3 for current count |

\* *Excludes 35 artifact files (athena-results, ml-models, etc.)*

### ADCE Data Sources (Phase 0.9)

The following data sources were added by ADCE autonomous collection:

1. **nba_api_comprehensive** (~22,256 files) - Comprehensive NBA stats
2. **nba_api_playbyplay** (~2,163 files) - Additional play-by-play coverage
3. **basketball_reference** (~444 files) - Advanced box score stats
4. **hoopr_phase1** (~218 files) - hoopR integration data
5. **hoopr_parquet** (~96 files) - Parquet-format hoopR data
6. **nba_api_reverse** (~80 files) - Reverse chronological backfill
7. **nba_api_incremental** (~54 files) - Incremental updates
8. **sportsdataverse** (~12 files) - Sports data aggregation

**Growth Validation:**
- Initial upload data preserved (no data loss)
- Original data types grew: box_scores +8 files, team_stats +1,273 files
- ADCE added 8 new complementary data sources
- Total system growth: ~18.2% from baseline

---

## Prerequisites

Before starting this phase:
- [ ] AWS account created
- [ ] AWS CLI installed
- [ ] Local NBA data available (`/Users/ryanranft/0espn/data/nba/`)
- [ ] Python 3.11 environment
- [ ] Sufficient local disk space for data

**For NBA:** Existing ESPN scraper output at `/Users/ryanranft/0espn/data/nba/`
**For other sports:** Local data files or API dumps ready for upload

---

## Implementation Steps

### Sub-Phase 0.1: Local Environment Setup

**Status:** ✅ COMPLETE
**Time Estimate:** 4 hours

**Follow these workflows:**
- Workflow #1 ([Session Start](../claude_workflows/workflow_descriptions/01_session_start.md))
  - **When to run:** At the very beginning of each work session
  - **Purpose:** Initialize session, check git status, orient to current state

- Workflow #17 ([Environment Setup](../claude_workflows/workflow_descriptions/17_environment_setup.md))
  - **When to run:** Before creating conda environment
  - **Purpose:** Verify Python version, conda installation, and set up environment correctly

- Workflow #3 ([Decision Workflow](../claude_workflows/workflow_descriptions/03_decision_workflow.md))
  - **When to run:** When choosing Python version, AWS region, or Git authentication method
  - **Purpose:** Document architectural decisions as ADRs

- Workflow #6 ([File Creation](../claude_workflows/workflow_descriptions/06_file_creation.md))
  - **When to run:** When creating initial project files (.gitignore, README.md, requirements.txt)
  - **Purpose:** Follow file creation best practices, ensure proper project structure from the start

**Completed tasks:**
1. ✅ Created conda environment `nba-aws` with Python 3.11.13
2. ✅ Installed dependencies: boto3, pandas, numpy, pytest
3. ✅ Verified AWS CLI installation (system-wide, not in conda)
4. ✅ Configured AWS credentials
5. ✅ Set up Git repository with SSH authentication (ADR-005)

**Commands used:**
```bash
# Create conda environment
conda create -n nba-aws python=3.11.13
conda activate nba-aws

# Install dependencies
pip install boto3 pandas numpy pytest psycopg2-binary python-dotenv

# Verify AWS CLI
aws --version
aws sts get-caller-identity

# Configure Git
git remote add origin git@github.com:username/nba-simulator-aws.git
```

**Validation:**
- [x] `conda activate nba-aws` works
- [x] `aws sts get-caller-identity` returns account info
- [x] Python packages installed: `pip list | grep boto3`
- [x] Git remote configured: `git remote -v`

---

### Sub-Phase 0.2: S3 Bucket Creation

**Status:** ✅ COMPLETE
**Time Estimate:** 30 minutes
**Cost:** $0 (bucket creation is free)

**Follow these workflows:**
- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
  - **When to run:** BEFORE creating S3 bucket
  - **Purpose:** Estimate storage costs based on data size (119 GB), get user approval

- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
  - **When to run:** When creating S3 bucket
  - **Purpose:** Follow best practices for bucket creation (encryption, public access blocking, region selection)

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After running AWS CLI commands
  - **Purpose:** Log bucket creation commands to COMMAND_LOG.md for future reference

- Workflow #28 ([ADR Creation](../claude_workflows/workflow_descriptions/28_adr_creation.md))
  - **When to run:** After making bucket configuration decisions (region, encryption, versioning)
  - **Purpose:** Document architectural decisions as ADRs (e.g., why us-east-1, why versioning disabled, why SSE-S3 vs KMS)

**Completed tasks:**
1. ✅ Created S3 bucket: `nba-sim-raw-data-lake`
2. ✅ Region: `us-east-1`
3. ✅ Versioning: Disabled (cost optimization)
4. ✅ Encryption: Enabled (SSE-S3)
5. ✅ Public access: Blocked (security)

**Commands used:**
```bash
# Create bucket
aws s3 mb s3://nba-sim-raw-data-lake --region us-east-1

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket nba-sim-raw-data-lake \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Verify public access block (enabled by default)
aws s3api get-public-access-block --bucket nba-sim-raw-data-lake
```

**Validation:**
- [x] Bucket exists: `aws s3 ls | grep nba-sim`
- [x] Encryption enabled: `aws s3api get-bucket-encryption --bucket nba-sim-raw-data-lake`
- [x] Public access blocked (default)

---

### Sub-Phase 0.3: Initial Data Upload to S3

**Status:** ✅ COMPLETE
**Time Estimate:** 1.5 days (overnight upload)
**Cost:** $2.74/month (119 GB × $0.023/GB)

**Follow these workflows:**
- Workflow #19 ([Backup & Recovery](../claude_workflows/workflow_descriptions/19_backup_recovery.md))
  - **When to run:** BEFORE uploading data to S3
  - **Purpose:** Backup local data to external drive (protect against data loss during upload)

- Workflow #5 ([Task Execution](../claude_workflows/workflow_descriptions/05_task_execution.md))
  - **When to run:** When launching the overnight upload
  - **Purpose:** Follow task execution checklist for long-running operations, ensure proper logging and monitoring

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After running `aws s3 sync` commands
  - **Purpose:** Log upload commands for documentation and future reference

- Workflow #11 ([Error Handling](../claude_workflows/workflow_descriptions/11_error_handling.md))
  - **When to run:** If upload fails or is interrupted
  - **Purpose:** Handle AWS CLI errors, network interruptions, resume failed uploads using `aws s3 sync`

**Completed tasks:**
1. ✅ Backed up local data to external drive
2. ✅ Uploaded 146,115 JSON files to S3
3. ✅ Documented data structure in `docs/DATA_STRUCTURE_GUIDE.md`

**Data uploaded:**
- **Schedule files:** 11,633 files → `s3://nba-sim-raw-data-lake/schedule/`
- **Play-by-play files:** 44,826 files → `s3://nba-sim-raw-data-lake/pbp/`
- **Box score files:** 44,828 files → `s3://nba-sim-raw-data-lake/box_scores/`
- **Team stats files:** 44,828 files → `s3://nba-sim-raw-data-lake/team_stats/`

**Upload commands:**
```bash
# Upload by data type
aws s3 sync /Users/ryanranft/0espn/data/nba/schedule/ \
  s3://nba-sim-raw-data-lake/schedule/ \
  --exclude "*" --include "*.json"

aws s3 sync /Users/ryanranft/0espn/data/nba/pbp/ \
  s3://nba-sim-raw-data-lake/pbp/ \
  --exclude "*" --include "*.json"

aws s3 sync /Users/ryanranft/0espn/data/nba/box_scores/ \
  s3://nba-sim-raw-data-lake/box_scores/ \
  --exclude "*" --include "*.json"

aws s3 sync /Users/ryanranft/0espn/data/nba/team_stats/ \
  s3://nba-sim-raw-data-lake/team_stats/ \
  --exclude "*" --include "*.json"
```

**Why `aws s3 sync`?**
- Automatically resumes if interrupted
- Only uploads new/changed files
- Skips files that already exist in S3
- Safe to run multiple times

---

### Sub-Phase 0.4: Verify Upload Completeness

**Status:** ✅ COMPLETE
**Time Estimate:** 30 minutes

**Follow these workflows:**
- Workflow #21 ([Data Validation](../claude_workflows/workflow_descriptions/21_data_validation.md))
  - **When to run:** AFTER upload completes
  - **Purpose:** Verify file count, sizes, and data integrity (compare S3 vs local)

**Completed tasks:**
1. ✅ Verified file counts match local source
2. ✅ Verified total size matches (119GB)
3. ✅ Spot-checked sample files for valid JSON

**Validation commands:**
```bash
# Count files in S3
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | wc -l
# Expected: 146,115

# Check total size
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize | grep "Total Size"
# Expected: ~119 GB

# Download and verify sample file
aws s3 cp s3://nba-sim-raw-data-lake/schedule/20230410.json /tmp/test.json
python -m json.tool /tmp/test.json > /dev/null && echo "Valid JSON"
```

**Validation:**
- [x] File count matches: 146,115 files
- [x] Total size matches: 119 GB
- [x] Sample files are valid JSON
- [x] All 4 data types uploaded successfully

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| S3 Standard Storage | 119 GB | $2.74 | 119 GB × $0.023/GB |
| S3 PUT Requests | 146,115 (one-time) | $0.73 (one-time) | Upload cost |
| S3 GET Requests | Minimal | ~$0.01 | Occasional downloads |
| **Total Phase Cost** | | **$2.74/month** | Recurring storage only |

**One-time upload cost:** $0.73

---

## Data Structure Summary

**Time Period:** NBA games 1993-2025

### Phase 0.1 Initial Upload (Baseline)

**File Breakdown:**
- Schedule files: 11,633 (YYYYMMDD format)
- Play-by-play files: 44,826 (game ID format)
- Box score files: 44,828 (game ID format)
- Team stats files: 44,828 (game ID format)

**Total:** 146,115 JSON files, 119 GB

**Data quality:**
- ~83% files contain usable game data
- ~17% files are empty (future/cancelled games)
- Average file size: ~815 KB

### Current State (ADCE Tracking)

**For live data counts, run validators:**
```bash
# From project root
python validators/phases/phase_0/validate_0_1_upload_completeness.py
python validators/phases/phase_0/validate_0_1_s3_bucket_config.py
```

**Run tests:**
```bash
# All Phase 0.1 tests
pytest tests/phases/phase_0/test_0_1_initial_data_collection.py -v

# Fast tests only (skip slow S3 scans)
pytest tests/phases/phase_0/test_0_1_initial_data_collection.py -v -m "not slow"

# Specific test
pytest tests/phases/phase_0/test_0_1_initial_data_collection.py::TestS3BucketConfiguration::test_bucket_exists -v
```

**Current data includes:**
- Original Phase 0.1 data (preserved)
- ADCE autonomous collection (8 new sources)
- Continuous growth from autonomous agents

**See `docs/DATA_STRUCTURE_GUIDE.md` for complete field mappings.**

---

## Troubleshooting

**Common issues encountered:**

1. **AWS CLI not found**
   - Solution: AWS CLI installed system-wide, not in conda
   - See workflow #17 for setup details

2. **Upload interrupted**
   - Solution: Use `aws s3 sync` (resumes from last uploaded file)
   - See `docs/TROUBLESHOOTING.md` for recovery steps

3. **PyCharm slow with data folder**
   - Solution: Mark `/data/` as "Excluded" in PyCharm
   - Prevents indexing of 146K+ files

4. **Permission denied errors**
   - Check AWS credentials: `aws sts get-caller-identity`
   - Verify IAM user has S3 write permissions

5. **Bucket already exists error**
   - S3 bucket names are globally unique
   - Use different bucket name or region

---

## Success Criteria

All criteria met:
- [x] S3 bucket created in us-east-1
- [x] All 146,115 files uploaded successfully
- [x] Total size matches source (119 GB)
- [x] Encryption enabled (SSE-S3)
- [x] Public access blocked
- [x] Cost within budget ($2.74/month < $5/month target)
- [x] Data structure documented
- [x] Local backup created

---

## Key Decisions

**Architecture decisions made:**
- **ADR-001:** Exclude Redshift (save $200-600/month)
- **ADR-002:** Extract 10% of JSON fields (save 90% storage)
- **ADR-003:** Use Python 3.11 (AWS Glue 4.0 compatibility)
- **ADR-005:** Git SSH authentication (security)
- **ADR-008:** Phase reorganization (logical data flow)

**See `docs/adr/README.md` for complete ADRs.**

---

## Next Steps

After completing this phase:
1. ✅ S3 bucket operational with all data uploaded
2. ✅ Update PROGRESS.md status (marked complete Oct 1, 2025)
3. ✅ Follow Workflow #14 ([Session End](../claude_workflows/workflow_descriptions/14_session_end.md))
4. → Proceed to [Phase 1: Data Quality & Gap Analysis](PHASE_1_DATA_QUALITY.md)

**Phase 0 successfully completed. S3 data lake operational.**

---

## Critical Paths Reference

- **Project directory:** `/Users/ryanranft/nba-simulator-aws`
- **Original data:** `/Users/ryanranft/0espn/data/nba/`
- **S3 bucket:** `s3://nba-sim-raw-data-lake`
- **Conda environment:** `nba-aws`
- **Backup location:** External drive (Time Machine)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md) | **Workflows:** [Workflow Index](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related phases:**
- Previous: None (first phase)
- Next: [Phase 1: Data Quality & Gap Analysis](PHASE_1_DATA_QUALITY.md)
- Formerly: This was Phase 1 before ADR-008 reorganization

---

*For Claude Code: See CLAUDE.md for navigation instructions and context management strategies.*

---

*Last updated: 2025-10-04 (reorganized per ADR-008)*
*Completed by: Phase 0 team*
*Total time: 2 days*
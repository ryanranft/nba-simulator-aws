# Phase 1: S3 Data Lake Setup

**Status:** ✅ COMPLETE
**Prerequisites:** None (foundational phase)
**Estimated Time:** 2 days
**Estimated Cost:** $2.74/month
**Started:** September 29, 2025
**Completed:** October 1, 2025

---

## Overview

Set up AWS S3 as the raw data lake foundation for the NBA simulator pipeline. This phase involves uploading all historical NBA game data (1999-2025) from local storage to S3 for cloud-based processing.

**This phase includes:**
- Local development environment setup
- AWS S3 bucket creation
- Data upload (146,115 JSON files, 119 GB)
- Cost optimization and monitoring

---

## Prerequisites

Before starting this phase:
- [x] AWS account created
- [x] AWS CLI installed and configured
- [x] Local NBA data available (`/Users/ryanranft/0espn/data/nba/`)
- [x] Python 3.11 environment
- [x] Sufficient local disk space for data

**See workflow #17 (Environment Setup) for complete setup verification.**

---

## Implementation Steps

### Sub-Phase 1.1: Local Environment Setup

**Status:** ✅ COMPLETE
**Time Estimate:** 4 hours

**Follow these workflows:**
- Workflow #17 ([Environment Setup](../claude_workflows/workflow_descriptions/17_environment_setup.md))
- Workflow #1 ([Session Start](../claude_workflows/workflow_descriptions/01_session_start.md))

**Completed tasks:**
1. ✅ Created conda environment `nba-aws` with Python 3.11.13
2. ✅ Installed dependencies: boto3, pandas, numpy, pytest
3. ✅ Verified AWS CLI installation (system-wide, not in conda)
4. ✅ Configured AWS credentials
5. ✅ Set up Git repository with SSH authentication (ADR-005)

**Validation:**
- [x] `conda activate nba-aws` works
- [x] `aws sts get-caller-identity` returns account info
- [x] Python packages installed: `pip list | grep boto3`
- [x] Git remote configured: `git remote -v`

---

### Sub-Phase 1.2: S3 Bucket Creation

**Status:** ✅ COMPLETE
**Time Estimate:** 30 minutes
**Cost:** $0 (bucket creation is free)

**Follow these workflows:**
- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))

**Completed tasks:**
1. ✅ Created S3 bucket: `nba-sim-raw-data-lake`
2. ✅ Region: `us-east-1`
3. ✅ Versioning: Disabled (cost optimization)
4. ✅ Encryption: Enabled (SSE-S3)
5. ✅ Public access: Blocked (security)

**Commands used:**
```bash
aws s3 mb s3://nba-sim-raw-data-lake --region us-east-1
aws s3api put-bucket-encryption \
  --bucket nba-sim-raw-data-lake \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

**Validation:**
- [x] Bucket exists: `aws s3 ls | grep nba-sim`
- [x] Encryption enabled: `aws s3api get-bucket-encryption --bucket nba-sim-raw-data-lake`

---

### Sub-Phase 1.3: Data Upload to S3

**Status:** ✅ COMPLETE
**Time Estimate:** 1.5 days (overnight upload)
**Cost:** $2.74/month (119 GB × $0.023/GB)

**Follow these workflows:**
- Workflow #19 ([Backup & Recovery](../claude_workflows/workflow_descriptions/19_backup_recovery.md)) - backup before upload
- Workflow #21 ([Data Validation](../claude_workflows/workflow_descriptions/21_data_validation.md)) - validate after upload

**Completed tasks:**
1. ✅ Backed up local data to external drive
2. ✅ Uploaded 146,115 JSON files to S3
3. ✅ Verified file count and sizes
4. ✅ Documented data structure in `docs/DATA_STRUCTURE_GUIDE.md`

**Data uploaded:**
- **Schedule files:** 11,633 files → `s3://nba-sim-raw-data-lake/schedule/`
- **Play-by-play files:** 44,826 files → `s3://nba-sim-raw-data-lake/pbp/`
- **Box score files:** 44,828 files → `s3://nba-sim-raw-data-lake/box_scores/`
- **Team stats files:** 44,828 files → `s3://nba-sim-raw-data-lake/team_stats/`

**Upload commands:**
```bash
# Upload by data type
aws s3 sync /Users/ryanranft/0espn/data/nba/schedule/ \
  s3://nba-sim-raw-data-lake/schedule/

aws s3 sync /Users/ryanranft/0espn/data/nba/pbp/ \
  s3://nba-sim-raw-data-lake/pbp/

aws s3 sync /Users/ryanranft/0espn/data/nba/box_scores/ \
  s3://nba-sim-raw-data-lake/box_scores/

aws s3 sync /Users/ryanranft/0espn/data/nba/team_stats/ \
  s3://nba-sim-raw-data-lake/team_stats/
```

**Validation:**
- [x] File count matches: `aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | wc -l` → 146,115
- [x] Total size matches: `aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize` → 119 GB
- [x] Sample files downloadable and valid JSON

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

**Time Period:** NBA games 1999-2025

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

**See `docs/adr/README.md` for complete ADRs.**

---

## Next Steps

After completing this phase:
1. ✅ Update PROGRESS.md status (marked complete Oct 1, 2025)
2. ✅ Proceed to [Phase 2: AWS Glue ETL](PHASE_2_AWS_GLUE.md)
3. ✅ Monitor S3 costs: `make check-costs`

**Phase 1 successfully completed. Data lake operational.**

---

## Critical Paths Reference

- **Project directory:** `/Users/ryanranft/nba-simulator-aws`
- **Original data:** `/Users/ryanranft/0espn/data/nba/`
- **S3 bucket:** `s3://nba-sim-raw-data-lake`
- **Conda environment:** `nba-aws`
- **Backup location:** External drive (Time Machine)

---

*Last updated: 2025-10-02*
*Completed by: Phase 1 team*
*Total time: 2 days*
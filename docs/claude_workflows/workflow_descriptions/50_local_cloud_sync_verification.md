# Workflow #50: Local-Cloud Sync Verification

**Version:** 1.0
**Created:** October 9, 2025
**Category:** Data Validation
**Estimated Time:** 15-30 minutes
**Cost:** $0 (local operations) or ~$0.01 (if checking RDS)
**Reusability:** Template for all data sources

---

## Overview

**Purpose:** Verify that local validation databases accurately reflect cloud data, ensuring local validation results are trustworthy before expensive RDS operations.

**Why Important:** Local validation is only valuable if local data matches cloud data!

**Pattern:** Trust but verify - confirm sync before relying on local validation

**When to Use:**
- Before cross-source validation (Workflow #49)
- After uploading new data to S3
- Before loading data to RDS
- When validation results seem inconsistent
- Periodically as sanity check

---

## The Problem This Solves

**Scenario:**
1. You upload data to S3
2. You create local SQLite database from local files
3. You run cross-validation and it passes
4. You load to RDS... but data doesn't match S3!

**Why This Happens:**
- Local files modified after S3 upload
- Incomplete S3 upload (network interruption)
- Local database created from different source than S3
- S3 files modified but local not updated

**Solution:**
This workflow verifies local files/databases match cloud state before trusting local validation results.

---

## Prerequisites

**Before starting this workflow:**

1. ✅ Data uploaded to S3 (e.g., `s3://bucket/hoopr_parquet/`)
2. ✅ Local data files or database exist
3. ✅ AWS CLI configured with credentials
4. ✅ Python environment active (`conda activate nba-aws`)

**Optional:**
- RDS database populated (if checking existing source)
- `compare_espn_databases.py` script (for ESPN RDS check)

**Cost Check:**
- S3 operations: $0 (read-only, minimal data transfer)
- RDS check: ~$0.01 (if running comparison query)
- Total: Effectively $0

---

## Workflow Steps

### Phase 1: Prepare Verification Script (One-Time Setup)

**If script doesn't exist:**

```bash
# Check if script exists
ls scripts/utils/verify_local_cloud_sync.py

# If not, create from template (see below)
```

**Template:** `scripts/utils/verify_local_cloud_sync.py`

**Key Components:**

1. **S3 File Inventory:**
```python
def _get_s3_parquet_inventory(self) -> Dict:
    """Get inventory of S3 parquet files."""
    cmd = [
        "aws", "s3", "ls",
        f"{self.s3_bucket}/{prefix}/",
        "--recursive",
        "--human-readable"
    ]
    # Parse output for file count and total size
```

2. **Local File Inventory:**
```python
def _get_local_parquet_inventory(self) -> Dict:
    """Get inventory of local parquet files."""
    for subdir in data_subdirs:
        for pf in dir_path.glob("*.parquet"):
            # Collect file info, compute total size
```

3. **Checksum Verification (Detailed Mode):**
```python
def _verify_sample_checksums(self) -> Dict:
    """Verify checksums for sample of files."""
    # Sample 10% or max 20 files
    # Compute local MD5
    # Compare with S3 ETag
```

4. **Existing Source RDS Check:**
```python
def _verify_espn_rds_sync(self) -> Dict:
    """Run existing comparison script."""
    comparison_script = "scripts/utils/compare_espn_databases.py"
    subprocess.run([sys.executable, comparison_script])
```

---

### Phase 2: Run Verification (5-10 minutes)

**Step 2.1: Quick verification (no RDS check)**

```bash
# Fast check - just S3 sync
python scripts/utils/verify_local_cloud_sync.py --skip-espn-rds
```

**Expected Output:**
```
======================================================================
LOCAL-CLOUD SYNCHRONIZATION VERIFICATION
======================================================================

Timestamp: 2025-10-09 15:00:00

======================================================================
CHECK 1: hoopR Local Parquet ↔ S3 Sync
======================================================================

📁 Scanning local hoopR parquet files...
  Found: 96 files (531.2 MB)

☁️  Scanning S3 hoopR parquet files...
  Found: 96 files (531.5 MB)

  ✅ Size variance: 0.06% (acceptable)

✅ hoopR local ↔ S3 sync: VERIFIED

⏭️  Skipping ESPN RDS check (--skip-espn-rds)

======================================================================
VERIFICATION SUMMARY
======================================================================

📊 hoopR Local ↔ S3 Sync:
  Status:       SYNCED
  Local files:  96 (531.2 MB)
  S3 files:     96 (531.5 MB)

📊 ESPN Local ↔ RDS Sync:
  Status:       SKIPPED

🎯 Overall Status: PASSED_PARTIAL

⚠️  Partial verification - hoopR sync verified, ESPN RDS skipped

======================================================================
NEXT STEPS
======================================================================

✅ Proceed with local validation:
  1. python scripts/db/create_local_hoopr_database.py
  2. python scripts/utils/compare_espn_hoopr_local.py
  3. Load to RDS (if validation passes)
```

**Step 2.2: Full verification (includes RDS check)**

```bash
# Full check - S3 + RDS
python scripts/utils/verify_local_cloud_sync.py
```

**Expected Output:**
```
[Same as above, plus:]

======================================================================
CHECK 2: ESPN Local SQLite ↔ RDS Sync
======================================================================

🔍 Running ESPN database comparison...
  Script: scripts/utils/compare_espn_databases.py
  ✅ ESPN local SQLite ↔ RDS: SYNCED

======================================================================
VERIFICATION SUMMARY
======================================================================

📊 hoopR Local ↔ S3 Sync:
  Status:       SYNCED
  Local files:  96 (531.2 MB)
  S3 files:     96 (531.5 MB)

📊 ESPN Local ↔ RDS Sync:
  Status:       SYNCED

🎯 Overall Status: PASSED

✅ All checks passed - Local validation will accurately reflect cloud data
```

**Step 2.3: Detailed verification (with checksums)**

```bash
# Detailed check - includes sample checksum verification
python scripts/utils/verify_local_cloud_sync.py --detailed
```

**Additional Output:**
```
🔍 Performing detailed checksum verification...

  Verifying 10 file checksums...
  ✅ Verified 10/10 file checksums
```

---

### Phase 3: Interpret Results

**Status Codes:**

| Status | Meaning | Action |
|--------|---------|--------|
| **PASSED** | All checks passed | ✅ Proceed with validation |
| **PASSED_PARTIAL** | S3 synced, RDS skipped | ✅ OK for new sources |
| **PASSED_WITH_WARNINGS** | Minor issues (<2) | ⚠️ Review warnings |
| **FAILED** | Sync issues detected | ❌ Fix issues first |

**Common Issues:**

1. **File count mismatch:**
   ```
   ⚠️  File count mismatch: Local=96, S3=94
   ```
   **Cause:** Incomplete upload or local files added after upload
   **Fix:** Re-upload missing files

2. **Size variance >1%:**
   ```
   ⚠️  Size variance 5.2% (expected <1%)
   ```
   **Cause:** Corrupted upload or compression differences
   **Fix:** Re-upload all files

3. **ESPN RDS out of sync:**
   ```
   ⚠️  ESPN sync check returned non-zero exit code: 1
   ```
   **Cause:** RDS data modified or local database stale
   **Fix:** Re-create local database or re-load RDS

---

### Phase 4: Fix Sync Issues (If Needed)

**Issue 1: Missing S3 Files**

```bash
# Re-upload missing files
aws s3 sync /local/path s3://bucket/prefix/ \
  --exclude "*" \
  --include "*.parquet" \
  --dryrun  # Test first

# Remove --dryrun to execute
aws s3 sync /local/path s3://bucket/prefix/ \
  --exclude "*" \
  --include "*.parquet"

# Verify upload
aws s3 ls s3://bucket/prefix/ --recursive | wc -l
```

**Issue 2: Local Files Out of Date**

```bash
# Download from S3 to local
aws s3 sync s3://bucket/prefix/ /local/path/ \
  --exclude "*" \
  --include "*.parquet"

# Re-create local database
python scripts/db/create_local_{source}_database.py
```

**Issue 3: Size Variance**

```bash
# Check file integrity
aws s3 ls s3://bucket/prefix/ --recursive --human-readable

# Re-upload entire directory (fresh upload)
aws s3 rm s3://bucket/prefix/ --recursive  # Careful!
aws s3 cp /local/path s3://bucket/prefix/ --recursive
```

**Issue 4: ESPN RDS Sync**

```bash
# Option A: Re-create local database
python scripts/db/create_local_espn_database.py

# Option B: Re-load RDS (if RDS is wrong)
python scripts/db/load_espn_to_rds.py

# Verify sync
python scripts/utils/compare_espn_databases.py
```

---

### Phase 5: Export Results (Optional)

**Export verification results to JSON:**

```bash
python scripts/utils/verify_local_cloud_sync.py \
  --export-json verification_results.json
```

**JSON Structure:**
```json
{
  "hoopr_s3_sync": {
    "status": "SYNCED",
    "local_files": 96,
    "s3_files": 96,
    "local_size_mb": 531.2,
    "s3_size_mb": 531.5,
    "issues": []
  },
  "espn_rds_sync": {
    "status": "SYNCED",
    "script_exit_code": 0,
    "issues": []
  },
  "overall_status": "PASSED"
}
```

**Uses:**
- Documentation (attach to validation report)
- Automated testing (CI/CD pipelines)
- Historical tracking (git commit with results)
- Debugging (share with team)

---

## Success Criteria

**Verification Passes If:**
- ✅ File counts match (local == S3)
- ✅ Size variance <1%
- ✅ No unexpected issues detected
- ✅ Overall status: PASSED or PASSED_PARTIAL

**Proceed to Validation If:**
- ✅ Verification passed
- ✅ User reviewed any warnings
- ✅ Results documented (if required)

---

## Integration with Workflow #49

**Combined Workflow Pattern:**

```bash
# Step 1: Verify local-cloud sync (Workflow #50)
python scripts/utils/verify_local_cloud_sync.py
# ✅ PASSED - Local matches cloud

# Step 2: Create local database (Workflow #49 Phase 1)
python scripts/db/create_local_hoopr_database.py
# ✅ Database created: /tmp/hoopr_local.db

# Step 3: Cross-validate sources (Workflow #49 Phase 2)
python scripts/utils/compare_espn_hoopr_local.py
# ✅ PASS - Sources are complementary

# Step 4: Verify sync again (optional sanity check)
python scripts/utils/verify_local_cloud_sync.py
# ✅ PASSED - Still synced

# Step 5: Load to RDS (Workflow #49 Phase 4)
python scripts/db/load_hoopr_to_rds.py
# ✅ Loaded with confidence!
```

**Why Verify Twice?**
- Before validation: Ensure starting from known-good state
- After validation: Confirm nothing changed during validation
- Especially important for long validation runs (hours)

---

## Template Variables for Future Sources

**Adapt script for new source:**

```python
# Customize these variables
source_name = "nba_api"  # or "basketball_reference"
local_dir = "/path/to/local/data"
s3_prefix = "s3://bucket/nba_api_parquet/"
comparison_script = "scripts/utils/compare_nba_api_databases.py"
```

**File patterns to check:**
- Parquet files: `*.parquet`
- CSV files: `*.csv`
- JSON files: `*.json`

**Size variance thresholds:**
- Compressed data: Allow 1-2% variance
- Uncompressed data: Allow 0.5% variance
- Text files: Allow 0.1% variance

---

## Automation Opportunities

**Schedule periodic verification:**

```bash
# Cron job (daily at 2 AM)
0 2 * * * cd /project && python scripts/utils/verify_local_cloud_sync.py --export-json /logs/sync_$(date +\%Y\%m\%d).json
```

**Pre-validation hook:**

```bash
# Always verify before validation
if python scripts/utils/verify_local_cloud_sync.py; then
  echo "✅ Sync verified - proceeding with validation"
  python scripts/utils/compare_espn_hoopr_local.py
else
  echo "❌ Sync failed - fix issues before validation"
  exit 1
fi
```

**CI/CD integration:**

```yaml
# GitHub Actions workflow
- name: Verify sync
  run: |
    python scripts/utils/verify_local_cloud_sync.py --export-json results.json
    if [ $? -ne 0 ]; then
      echo "::error::Sync verification failed"
      exit 1
    fi
```

---

## Troubleshooting

**Issue: AWS CLI not found**
```bash
which aws
# If not found: brew install awscli (macOS) or pip install awscli
```

**Issue: S3 access denied**
```bash
# Check credentials
aws sts get-caller-identity

# Check bucket access
aws s3 ls s3://bucket-name/
```

**Issue: Script timeout (>5 minutes)**
```bash
# Increase timeout in script
timeout=600  # 10 minutes

# Or skip RDS check
--skip-espn-rds
```

**Issue: Large file count (>1000 files)**
```bash
# Use pagination with AWS CLI
aws s3api list-objects-v2 --bucket bucket-name --prefix prefix/ --max-items 1000

# Or parallelize verification
# Split files into batches, verify in parallel
```

**Issue: Checksum verification slow**
```bash
# Reduce sample size in script
sample_size = min(10, len(local_files) // 20)  # 5% instead of 10%

# Or skip checksums
# Just use file count and size comparison
```

---

## Benefits

**Confidence:**
- Know local validation reflects cloud reality
- Catch sync issues before expensive RDS operations
- Document verification for audit trail

**Cost Savings:**
- $0 verification vs failed RDS loads
- Prevent wasted 3-4 hour RDS load operations
- Catch issues early

**Time Savings:**
- 15-30 minute verification vs debugging later
- Quick feedback on sync status
- Automated script (no manual checking)

**Debugging:**
- Clear status codes (PASSED/FAILED)
- Detailed issue reporting
- Export results for analysis

---

## Related Workflows

- **Workflow #49:** Cross-Source Data Validation (parent workflow)
- **Workflow #21:** Data Validation Framework (validation patterns)
- **Workflow #2:** Command Logging (document verification runs)
- **Workflow #14:** Session End (include verification results in summary)

---

## Best Practices

**Always Verify:**
- ✅ Before cross-source validation
- ✅ After uploading to S3
- ✅ Periodically as sanity check
- ✅ When validation results seem wrong

**Document Results:**
- ✅ Export JSON for critical validations
- ✅ Git commit verification results
- ✅ Update DATA_CATALOG.md with sync status
- ✅ Note any warnings in COMMAND_LOG.md

**Fix Issues Promptly:**
- ✅ Don't proceed with validation if sync failed
- ✅ Re-upload to S3 if missing files
- ✅ Re-create local database if out of date
- ✅ Verify fix with second run

**Optimize for Scale:**
- ✅ Use `--skip-espn-rds` for new sources
- ✅ Use `--detailed` only when needed
- ✅ Parallelize large file verification
- ✅ Cache results for repeated checks

---

## Exit Codes

**Script returns:**
- `0` - PASSED (all checks passed)
- `1` - PASSED_WITH_WARNINGS (minor issues)
- `2` - FAILED (sync issues detected)
- `3` - ERROR (script error, not sync issue)

**Use in scripts:**
```bash
if python scripts/utils/verify_local_cloud_sync.py; then
  echo "Proceed with validation"
else
  echo "Fix sync issues first"
  exit 1
fi
```

---

## Change Log

**v1.0 - October 9, 2025:**
- Initial workflow creation
- Codified local-cloud sync verification pattern
- Created reusable template for all sources
- Documented hoopR S3 sync as reference example
- Integrated with Workflow #49 (Cross-Source Validation)

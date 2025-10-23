# Workflow #42: Automated Data Audit

**Related Phase:** [Phase 8: Data Audit & Inventory](../../phases/PHASE_8_INDEX.md)
**Automation Level:** HIGH (runs automatically after scraping or on schedule)
**Time Required:** 2-5 minutes
**Cost:** $0 (local analysis only, minimal S3 GET requests)

---

## Purpose

Automatically run comprehensive data audits to maintain an up-to-date inventory of all data holdings, detect sync issues, and identify gaps. This workflow ensures you always have complete visibility into your data landscape.

---

## When to Run This Workflow

### Automatic Triggers (Recommended)

1. **After Data Scraping** ✅ AUTOMATED
   - Triggered by: Post-scrape hook in scraping scripts
   - Purpose: Verify new data was collected successfully
   - Action: `bash scripts/audit/post_scrape_audit_hook.sh`

2. **Scheduled Audits** ✅ AUTOMATED (if configured)
   - Frequency: Daily at 9 AM or Weekly on Mondays
   - Purpose: Regular sync status checks
   - Action: Cron job runs `scripts/audit/run_data_audit.sh`

### Manual Triggers

3. **Before Starting Analysis**
   - When: Starting a new research question or ML project
   - Purpose: Confirm you have all needed data
   - Action: Run audit manually to check coverage

4. **After External Data Discovery**
   - When: Found data in Downloads, external repos, etc.
   - Purpose: Integrate and update inventory
   - Action: Run full audit including external locations

5. **Troubleshooting Data Issues**
   - When: Queries fail, files seem missing, counts don't match
   - Purpose: Diagnose sync issues and data gaps
   - Action: Run audit with verbose logging

6. **Quarterly Reviews**
   - When: First Monday of each quarter
   - Purpose: Comprehensive data health check
   - Action: Full audit + documentation update

---

## Claude Code Trigger Points

**Claude should proactively run this workflow:**

1. **After completing any scraping script** (Phase 0, Phase 1)
   ```bash
   # At end of scraping script
   bash scripts/audit/post_scrape_audit_hook.sh
   ```

2. **When user asks about data completeness:**
   - "Do we have all the data?"
   - "What's in our S3 bucket?"
   - "Are local files synced?"
   - "What data are we missing?"

3. **When starting a new phase that depends on data:**
   - Phase 2: ETL (need complete S3 inventory)
   - Phase 4: Simulation (need verified data quality)
   - Phase 5: ML (need gap analysis)

4. **When user mentions finding new data:**
   - "I downloaded some files..."
   - "Found old data in..."
   - "I have this dataset from..."

---

## How to Execute

### Option 1: Manual Audit (Standard)

```bash
# Navigate to project
cd /Users/ryanranft/nba-simulator-aws

# Load credentials
source /Users/ryanranft/nba-sim-credentials.env

# Run audit
bash scripts/audit/run_data_audit.sh
```

**Output:**
- Console: Summary of file counts and sync status
- Log file: `logs/audit/audit_YYYYMMDD_HHMMSS.log`

### Option 2: Manual Audit with Documentation Update

```bash
# Run audit and update MASTER_DATA_INVENTORY.md
bash scripts/audit/run_data_audit.sh --update-docs
```

**Updates:**
- MASTER_DATA_INVENTORY.md last updated date
- Audit log with full details

### Option 3: Post-Scrape Hook (After Data Collection)

```bash
# This is called automatically at the end of scraping scripts
bash scripts/audit/post_scrape_audit_hook.sh
```

**Behavior:**
- Waits 5 seconds for file system sync
- Runs full audit with doc updates
- Reports sync issues if detected

### Option 4: Quiet Mode (Background/Cron)

```bash
# Suppress verbose output (logs still written)
bash scripts/audit/run_data_audit.sh --quiet
```

### Option 5: Offline Mode (No AWS)

```bash
# Skip S3 and RDS checks (faster, works offline)
bash scripts/audit/run_data_audit.sh --skip-s3
```

---

## What the Audit Checks

### Phase 1: Local File Count
- ✅ Play-by-Play JSON files
- ✅ Box Score JSON files
- ✅ Team Stats JSON files
- ✅ Schedule JSON files
- ✅ Total file count

### Phase 2: S3 Bucket Inventory
- ✅ ESPN data counts (pbp, box_scores, team_stats, schedule)
- ✅ NBA API data counts
- ✅ hoopR data counts
- ✅ Basketball Reference data
- ✅ Total S3 file count

### Phase 3: Database Status
- ✅ Kaggle SQLite database (size check)
- ✅ Unified SQLite database (latest backup)
- ✅ RDS PostgreSQL status (available/unavailable)

### Phase 4: Sync Status Verification
- ✅ Compare local vs S3 file counts
- ⚠️ Report any mismatches (sync issues)
- ✅ Provide sync commands if needed

### Phase 5: Documentation Update (if --update-docs)
- ✅ Update MASTER_DATA_INVENTORY.md timestamp
- ✅ Record audit results
- ✅ Update all documents referencing data counts
- ✅ Archive obsolete documentation
- ✅ Generate data summary report

---

## Documentation Update Process

When `--update-docs` flag is used, the audit automatically updates all documents that reference data counts:

### Documents Updated Automatically

1. **Primary Data Documents:**
   - `docs/DATA_QUALITY_BASELINE.md` - Overall data health summary
   - `docs/MASTER_DATA_INVENTORY.md` - Complete inventory
   - `docs/DATA_COLLECTION_SUMMARY.md` - Collection timeline
   - `PROGRESS.md` - Project status summary

2. **Phase Documentation:**
   - `docs/phases/phase_0/PHASE_0_INDEX.md` - Data collection phase status
   - `docs/phases/PHASE_8_INDEX.md` - Audit phase status

3. **Archive Process:**
   - Identifies obsolete documents (`.old`, `.bak`, `*_backup*`)
   - Moves to `docs/archive/superseded_documentation/`
   - Updates archive README

### Manual Documentation Updates

If you need to update additional documents manually:

```bash
# Find all documents referencing old data counts
grep -r "147,380\|172,597\|24,419" docs/ --include="*.md"

# Update specific documents
# Edit files found above with current data counts
```

### Integration with Other Workflows

This workflow integrates with:
- **Workflow #13:** File Inventory (`make inventory`)
- **Workflow #43:** Documentation Consolidation
- **Workflow #9:** Archive Management

---

## Output Examples

### Successful Audit (All Synced)

```
ℹ ==========================================
ℹ NBA Data Audit Started
ℹ Timestamp: 20251011_143522
ℹ ==========================================

ℹ Phase 1: Counting local data files...
✅ Local data inventory complete
  - Play-by-Play: 44826 files
  - Box Scores: 44828 files
  - Team Stats: 46093 files
  - Schedule: 11633 files
  - TOTAL: 147380 files

ℹ Phase 2: Counting S3 data files...
✅ S3 data inventory complete
  - Play-by-Play: 44826 files
  - Box Scores: 44828 files
  - Team Stats: 46093 files
  - Schedule: 11633 files
  - TOTAL: 147380 files

ℹ Phase 3: Checking database status...
✅ Kaggle DB found: 2.2G
✅ Unified DB found: 21M
✅ RDS PostgreSQL: available

ℹ Phase 4: Checking sync status (local vs S3)...
✅ All data sources synchronized! ✅

📊 Data Holdings:
  Local: 147380 files
  S3: 147380 files
  RDS: available

✅ Sync Status: All sources synchronized

✅ Data Audit Complete!
```

### Audit with Sync Issues Detected

```
⚠️  Team Stats out of sync: S3 has 1265 more files

⚠️  1 data source(s) out of sync

To sync, run:
  aws s3 sync s3://nba-sim-raw-data-lake/team_stats/ data/nba_team_stats/

⚠️  Sync Issues: 1

Exit code: 1 (requires action)
```

---

## Exit Codes

| Code | Meaning | Action Required |
|------|---------|-----------------|
| 0 | Success - all synced | None |
| 1 | Sync issues detected | Run suggested sync commands |

---

## Integration with Scraping Scripts

**Add to the END of all scraping scripts:**

```python
# At the end of your Python scraping script
import subprocess
import os

# Run post-scrape audit hook
print("\n" + "="*60)
print("Running post-scrape data audit...")
print("="*60)

result = subprocess.run(
    ["bash", "scripts/audit/post_scrape_audit_hook.sh"],
    cwd=os.path.expanduser("~/nba-simulator-aws"),
    capture_output=False
)

if result.returncode == 0:
    print("✅ Data audit passed - all sources synchronized")
else:
    print("⚠️  Data audit detected sync issues - review logs")
```

**Or in Bash:**

```bash
# At the end of your bash scraping script
echo ""
echo "Running post-scrape data audit..."
bash scripts/audit/post_scrape_audit_hook.sh
```

---

## Scheduled Automation (Optional)

### Daily Audit (9 AM)

```bash
# Add to crontab: crontab -e
0 9 * * * cd /Users/ryanranft/nba-simulator-aws && bash scripts/audit/run_data_audit.sh --quiet >> logs/audit/daily_audit.log 2>&1
```

### Weekly Audit (Monday 9 AM)

```bash
# Add to crontab: crontab -e
0 9 * * 1 cd /Users/ryanranft/nba-simulator-aws && bash scripts/audit/run_data_audit.sh --update-docs >> logs/audit/weekly_audit.log 2>&1
```

### Quarterly Comprehensive Audit

```bash
# First Monday of each quarter at 9 AM
0 9 1-7 1,4,7,10 1 cd /Users/ryanranft/nba-simulator-aws && bash scripts/audit/run_data_audit.sh --update-docs
```

---

## Troubleshooting

### Issue: "AWS credentials not found"

**Cause:** Credentials not loaded or expired

**Solution:**
```bash
source /Users/ryanranft/nba-sim-credentials.env
# Then re-run audit
bash scripts/audit/run_data_audit.sh
```

### Issue: "Permission denied" error

**Cause:** Script not executable

**Solution:**
```bash
chmod +x scripts/audit/run_data_audit.sh
chmod +x scripts/audit/post_scrape_audit_hook.sh
```

### Issue: S3 commands timeout

**Cause:** Large bucket, slow connection

**Solution:**
```bash
# Use --skip-s3 for faster local-only audit
bash scripts/audit/run_data_audit.sh --skip-s3
```

### Issue: Sync issues persist after running sync commands

**Cause:** Files still uploading or network issues

**Solution:**
- Wait 5 minutes and re-run audit
- Check S3 upload logs for errors
- Verify AWS credentials have S3 permissions

---

## Related Workflows

- **Workflow #1:** Session Start (run audit at session start)
- **Workflow #14:** Session End (run audit before ending)
- **Workflow #21:** Data Validation (complementary to audit)
- **Workflow #38:** Overnight Handoff (audit results in handoff)

---

## Related Documentation

- **Phase 8:** [Data Audit & Inventory](../../phases/PHASE_8_INDEX.md)
- **Sub-Phase 8.0:** [Recursive Data Discovery](../../phases/phase_8/8.0_recursive_data_discovery.md)
- **Sub-Phase 8.1:** [Deep Content Analysis](../../phases/phase_8/8.1_deep_content_analysis.md)
- **Master Inventory:** [MASTER_DATA_INVENTORY.md](../../MASTER_DATA_INVENTORY.md)

---

## Quick Reference

**Run after scraping:**
```bash
bash scripts/audit/post_scrape_audit_hook.sh
```

**Run manually:**
```bash
bash scripts/audit/run_data_audit.sh
```

**Run with doc update:**
```bash
bash scripts/audit/run_data_audit.sh --update-docs
```

**Run offline:**
```bash
bash scripts/audit/run_data_audit.sh --skip-s3
```

---

## Key Benefits

1. **Automated Verification** - No manual counting needed
2. **Sync Issue Detection** - Immediately catch drift between local/S3
3. **Zero Cost** - Local analysis only
4. **Fast Execution** - 2-5 minutes for full audit
5. **Reusable** - Same script works for any sport
6. **Documented** - Audit logs preserve history
7. **Proactive** - Runs automatically after scraping

---

## For Claude Code

**When to proactively use this workflow:**

1. ✅ After completing ANY scraping script
2. ✅ When user asks about data completeness or sync status
3. ✅ Before starting phases that depend on complete data
4. ✅ When user mentions finding new external data
5. ✅ At the beginning of a new session (optional health check)
6. ✅ When debugging "file not found" or similar errors

**Always add the post-scrape hook to the end of scraping scripts you create.**

---

**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Automation Status:** ✅ Fully automated
**Script Location:** `scripts/audit/run_data_audit.sh`
**Hook Location:** `scripts/audit/post_scrape_audit_hook.sh`
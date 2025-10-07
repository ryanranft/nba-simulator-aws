## 🔄 Maintenance Schedule Workflows

### Weekly Maintenance (Monday or 7+ Days)

**Automatically offered during session start (Step 4)**

```bash
make update-docs
# OR run directly:
bash scripts/maintenance/update_docs.sh
```

**What this does (7 automated steps):**

#### Step 1: Update QUICKSTART.md Costs
```bash
# Automatically fetches current month AWS costs via Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-02 \
  --granularity MONTHLY \
  --metrics BlendedCost

# Updates cost line in QUICKSTART.md:
# "**Current:** ~$2.74/month" → "**Current:** ~$[ACTUAL]/month"
```

#### Step 2: Update ADR Index
```bash
# Counts all ADR files in docs/adr/
ADR_COUNT=$(find docs/adr -name "[0-9]*.md" -type f | wc -l)

# Updates docs/adr/README.md:
# "**Total ADRs:** 5" → "**Total ADRs:** [COUNT]"
```

#### Step 3: Update PROGRESS.md Statistics
```bash
# Gathers current project state:
- Git commit count: git rev-list --count HEAD
- S3 object count: aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize
- RDS status: aws rds describe-db-instances --db-instance-identifier nba-sim-db
- Glue status: aws glue get-crawler --name nba-data-crawler

# Displays summary:
# "Stats: 87 commits, 146115 S3 objects"
# "RDS: not-created, Glue: not-created"
```

#### Step 4: Update Last Updated Timestamps
```bash
CURRENT_DATE=$(date +%Y-%m-%d)

# Updates "**Last Updated:** YYYY-MM-DD" in:
- QUICKSTART.md
- docs/STYLE_GUIDE.md
- docs/TESTING.md
- docs/TROUBLESHOOTING.md
- docs/adr/README.md
```

#### Step 5: Generate Project Statistics
```bash
# Counts:
- Lines of code (Python, Bash, SQL): find . -name "*.py" -o -name "*.sh" -o -name "*.sql"
- Documentation lines: find docs -name "*.md"
- Test files: find tests -name "test_*.py"

# Displays comprehensive report:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Statistics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Lines of code: 15430
Documentation lines: 8924
Test files: 12
Git commits: 87
S3 objects: 146115
ADRs: 5
Current AWS cost: $2.74/month
```

#### Step 6: Check for Stale Documentation
```bash
# Finds docs not modified in 30+ days:
find docs -name "*.md" -mtime +30

# Warns about stale files:
# "⚠️  Stale (30+ days): docs/OLD_SETUP.md"
```

#### Step 7: Validate Internal Documentation Links
```bash
# Extracts all markdown links: [text](link)
# Skips external links (http/https)
# Checks if local file exists

# Reports broken links:
# "⚠️  Broken link in docs/SETUP.md: missing-file.md"
# "✅ All internal links valid" (if no issues)
```

**Script output summary:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Documentation Auto-Update
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Updating QUICKSTART.md...
   ✅ Updated current costs to $2.74/month
2. Updating ADR index...
   ✅ Updated ADR count to 5
3. Updating PROGRESS.md statistics...
   ✅ Stats: 87 commits, 146115 S3 objects
   ✅ RDS: not-created, Glue: not-created
4. Updating 'Last Updated' timestamps...
   ✅ Updated timestamp in QUICKSTART.md
   ✅ Updated timestamp in docs/STYLE_GUIDE.md
   [... other files ...]
5. Generating statistics...
   [Statistics table displayed]
6. Checking for stale documentation...
   ⚠️  Stale (30+ days): docs/OLD_NOTES.md
7. Validating internal links...
   ✅ All internal links valid

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Documentation update complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next steps:
  1. Review changes: git diff
  2. Commit if satisfied: git add -u && git commit -m 'Update documentation'
  3. Run this script weekly to keep docs current
```

**When to run:**
- ✅ Monday morning (start of week)
- ✅ 7+ days since last run
- ✅ After major documentation changes
- ✅ Before starting new phase
- ✅ After creating/modifying AWS resources (updates costs and status)

**What gets updated:**
- ✅ QUICKSTART.md - Current AWS costs (live from Cost Explorer)
- ✅ docs/adr/README.md - ADR count
- ✅ PROGRESS.md - Project statistics (commits, S3, RDS, Glue)
- ✅ Multiple docs - "Last Updated" timestamps
- ✅ Console output - Full project statistics report
- ✅ Console warnings - Stale docs (30+ days) and broken links

**Integration with other workflows:**
- **Session Start Workflow Step 4:** Automatically prompts to run if 7+ days since last run
- **Git Commit Workflow:** Run before committing documentation changes to ensure consistency
- **Monthly Maintenance:** Part of comprehensive monthly review checklist

### Monthly Maintenance (First Monday of Month)

**5-step review checklist:**

1. **Review PROGRESS.md**
   - Mark completed tasks ✅ COMPLETE
   - Update time estimates based on actuals
   - Adjust remaining phase estimates
   - Update cost actuals from AWS billing

2. **Review documentation health**
   ```bash
   make stats  # Show project statistics
   ```
   - Check for outdated docs (>30 days)
   - Review TROUBLESHOOTING.md coverage
   - Verify ADRs are up to date
   - Check FILE_INVENTORY.md accuracy

3. **Review AWS resources**
   ```bash
   make sync-progress  # Compare PROGRESS.md vs. actual AWS
   ```
   - Verify all resources documented
   - Check for orphaned resources (not in PROGRESS.md)
   - Review resource costs (Cost Explorer)
   - Stop unused resources

4. **Review security**
   - Check credential ages (90-day rotation)
   - Review .gitignore effectiveness
   - Verify git hooks still installed
   - Check for exposed secrets (GitHub secret scanning)

5. **Create archive checkpoint**
   ```bash
   make backup  # Monthly backup
   ```
   - Tag significant commits
   - Archive completed phase documentation
   - Clean up old archives (>90 days)

### Inventory Update Workflow

**Run automatically after file creation/modification (File Creation Workflow Step 2)**

```bash
make inventory
```

**Manual run when:**
- ✅ After creating multiple files
- ✅ After moving/renaming files
- ✅ After deleting files
- ✅ Before important commits
- ✅ 7+ days since last run

**What it updates:**
- FILE_INVENTORY.md (file list with descriptions)
- File modification timestamps
- File size statistics
- Directory structure overview

### 📊 Sync PROGRESS.md with AWS Resources (make sync-progress)

**Purpose:** Automatically detect AWS resource states and suggest PROGRESS.md updates

**Script:** `scripts/maintenance/sync_progress.py` (called by `make sync-progress`)

**When to run:**
- After creating RDS instance
- After creating Glue jobs/crawlers
- After launching EC2 instances
- After setting up SageMaker notebooks
- Weekly (Monday maintenance routine)
- When unsure if PROGRESS.md reflects reality
- Before monthly documentation review

### Single Command

```bash
make sync-progress
```

**Equivalent direct call:**
```bash
python scripts/maintenance/sync_progress.py
```

**Preview mode (no changes):**
```bash
python scripts/maintenance/sync_progress.py --dry-run
```

### What This Does

**4-step automated detection process:**

#### Step 1: Check S3 Data Lake Status

Verifies if S3 bucket exists and contains expected data:

```bash
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize
```

**Detection logic:**
- ✅ **complete** - Bucket exists AND contains 146,115 objects
- ⏸️ **pending** - Bucket missing OR object count doesn't match

**Mapped to:** Phase 0 - Data Collection & Initial Upload

#### Step 2: Check RDS Database Status

Verifies if RDS instance exists:

```bash
aws rds describe-db-instances --db-instance-identifier nba-sim-db
```

**Detection logic:**
- ✅ **complete** - Instance exists with "DBInstanceStatus" in response
- ⏸️ **pending** - Instance not found OR error response

**Mapped to:** Phase 3.1 - RDS Database Setup

#### Step 3: Check Glue Crawler Status

Verifies if Glue crawler exists:

```bash
aws glue get-crawler --name nba-data-crawler
```

**Detection logic:**
- ✅ **complete** - Crawler exists with "Crawler" in response
- ⏸️ **pending** - Crawler not found OR error response

**Mapped to:** Phase 2.1 - Glue Crawler Setup

#### Step 4: Check Glue ETL Job Status

Verifies if Glue ETL job exists:

```bash
aws glue get-job --job-name nba-etl-job
```

**Detection logic:**
- ✅ **complete** - Job exists with "Job" in response
- ⏸️ **pending** - Job not found OR error response

**Mapped to:** Phase 2.2 - Glue ETL Job Setup

### Example Output

```bash
$ make sync-progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROGRESS.md Synchronization
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Resource Detection:
   S3 Data Lake: complete
   RDS Database: pending
   Glue Crawler: pending
   Glue ETL Job: pending

📊 Project Summary:
============================================================
Git commits: 158
Documentation files: 32
Architecture Decision Records: 12
Python files: 23
Test files: 5
============================================================

💡 Suggested Updates:
   ✅ Phase 0 (Data Collection) appears complete
   ⏸️ Phase 2 (ETL Extraction) pending
   ⏸️ Phase 3 (Database) pending
   ⏸️ Phase 2.2 (Glue ETL Job) pending

💾 To apply updates, manually edit PROGRESS.md
   This script provides detection only for now

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Sync complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### How to Interpret Results

**Scenario 1: All resources exist**
```
🔍 Resource Detection:
   S3 Data Lake: complete
   RDS Database: complete
   Glue Crawler: complete
   Glue ETL Job: complete

💡 Suggested Updates:
   ✅ Phase 0 (Data Collection) appears complete
   ✅ Phase 2 (ETL Extraction) appears complete
   ✅ Phase 3 (Database) appears complete
```

**Action:** Verify PROGRESS.md shows all phases as `✅ COMPLETED`

**Scenario 2: RDS not created yet**
```
🔍 Resource Detection:
   S3 Data Lake: complete
   RDS Database: pending
   Glue Crawler: pending
   Glue ETL Job: pending

💡 Suggested Updates:
   ✅ Phase 0 (Data Collection) appears complete
   ⏸️ Phase 3 (Database) pending
```

**Action:** This matches expected state - RDS is Phase 3 (comes after Phase 2 Glue setup)

**Scenario 3: Mismatch detected**
```
PROGRESS.md shows: Phase 2.1 Glue Crawler = ✅ COMPLETED
make sync-progress shows: Glue Crawler: pending

💡 Suggested Updates:
   ⏸️ Phase 2.1 (Glue Crawler) pending
```

**Action:** Either:
- PROGRESS.md is wrong (update to ⏸️ PENDING)
- OR crawler was deleted (recreate crawler)

### Integration with Other Workflows

**After creating AWS resources:**
```bash
# 1. Create RDS database
aws rds create-db-instance --db-instance-identifier nba-sim-db [...]

# 2. Wait for creation
aws rds wait db-instance-available --db-instance-identifier nba-sim-db

# 3. Verify detection
make sync-progress
# Shows: RDS Database: complete

# 4. Update PROGRESS.md manually
vim PROGRESS.md
# Change Phase 3.1 from ⏸️ PENDING to ✅ COMPLETED
```

**Weekly maintenance routine:**
```bash
# Every Monday morning
make sync-progress           # Check actual AWS state
make check-costs            # Check monthly spending
make inventory              # Update FILE_INVENTORY.md

# Review output and update PROGRESS.md if needed
```

**Before documentation review:**
```bash
# Ensure documentation matches reality
make sync-progress

# If mismatches found, decide:
# - Update PROGRESS.md to match AWS (documentation wrong)
# - OR create missing AWS resources (AWS wrong)
# - OR delete extra AWS resources (AWS has extras)
```

**Troubleshooting phase completion:**
```bash
# User claims Phase 2 complete, but checklist shows pending
make sync-progress

# Check which specific resource is missing:
# ⏸️ Phase 2.1 (Glue Crawler) pending
# ⏸️ Phase 2.2 (Glue ETL Job) pending

# Go back and complete those tasks
```

### What This Script Does NOT Do

**❌ Does NOT automatically update PROGRESS.md**
- Only provides detection and suggestions
- User must manually edit PROGRESS.md
- Future enhancement: could auto-update with `--apply` flag

**❌ Does NOT check resource configurations**
- Only checks existence (not settings)
- Example: RDS exists, but doesn't verify instance class

**❌ Does NOT validate data quality**
- S3 check only counts objects (not content validity)
- Use `check_data_availability.py` for data quality checks

**❌ Does NOT check costs**
- Use `make check-costs` for cost verification
- This script only checks resource existence

### Project Summary Statistics

The script also generates helpful project statistics:

**Git Statistics:**
- Total commit count

**Documentation Statistics:**
- Total documentation files (`.md` in `docs/`)
- Architecture Decision Records count (`docs/adr/[0-9]*.md`)

**Code Statistics:**
- Total Python files (`.py` anywhere in project)
- Test files count (`tests/test_*.py`)

**Example:**
```
📊 Project Summary:
============================================================
Git commits: 158
Documentation files: 32
Architecture Decision Records: 12
Python files: 23
Test files: 5
============================================================
```

### Comparison to Manual Verification

| Approach | Time Required | Accuracy | Use Case |
|----------|---------------|----------|----------|
| **Manual AWS Console** | 10-15 minutes | 📉 Human error | Visual verification |
| **Manual AWS CLI** | 5-10 minutes | ✅ Accurate | One-off checks |
| **make sync-progress** | <10 seconds | ✅ Automated | **Weekly maintenance** |
| **No verification** | 0 seconds | ❌ Drift guaranteed | Never recommended |

### Best Practices

**Run sync-progress when:**
- ✅ Just created new AWS resources (immediate verification)
- ✅ Weekly on Monday (maintenance routine)
- ✅ Before monthly documentation review
- ✅ After long break from project (verify nothing changed)
- ✅ When PROGRESS.md status unclear

**Don't need to run if:**
- ✅ No AWS changes made (just code/docs)
- ✅ Already ran today (<24 hours ago)
- ✅ Only local development work (no AWS interaction)

### Troubleshooting

**Problem: "aws: command not found"**
```bash
# Cause: AWS CLI not installed or not in PATH
# Solution: Install AWS CLI
brew install awscli  # macOS
# Or follow: https://aws.amazon.com/cli/

# Verify installation
aws --version
```

**Problem: "Unable to locate credentials"**
```bash
# Cause: AWS credentials not configured
# Solution: Configure credentials
aws configure

# Or verify credentials exist
cat ~/.aws/credentials
```

**Problem: "S3 Data Lake: pending" but bucket exists**
```bash
# Cause: Object count doesn't match expected 146,115
# Solution: Check actual count
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize | grep "Total Objects"

# If different count, bucket incomplete
# Re-run data extraction or verify upload
```

**Problem: Script says "complete" but PROGRESS.md shows "pending"**
```bash
# Cause: PROGRESS.md is outdated
# Solution: Update PROGRESS.md manually
vim PROGRESS.md
# Find the phase (e.g., Phase 3.1 RDS Database)
# Change: ⏸️ PENDING → ✅ COMPLETED

# Commit the update
git add PROGRESS.md
git commit -m "Update PROGRESS.md: Phase 3.1 complete"
```

**Problem: Script says "pending" but resource exists in AWS Console**
```bash
# Cause: Resource name doesn't match expected name
# Solution: Check actual resource name in AWS

# Expected names (hardcoded in script):
# - S3: nba-sim-raw-data-lake
# - RDS: nba-sim-db
# - Glue Crawler: nba-data-crawler
# - Glue ETL Job: nba-etl-job

# If using different names, edit sync_progress.py line 44, 57, 66, 75
```

**Problem: Timeout errors**
```bash
# Cause: AWS CLI commands taking >30 seconds
# Solution: Check AWS region, network, or increase timeout

# Edit sync_progress.py line 36:
timeout=30  # Increase to 60 or 120
```

### Future Enhancements (Potential)

**Auto-update mode:**
```bash
# Not yet implemented - would auto-update PROGRESS.md
make sync-progress --apply
```

**Configuration checks:**
```bash
# Not yet implemented - would verify settings, not just existence
# Example: RDS instance class, Glue DPU count, etc.
```

**Cost correlation:**
```bash
# Not yet implemented - would link resource detection to cost data
# Example: "RDS exists → Expected cost $29/month → Actual $28.47"
```

**Resource dependency graph:**
```bash
# Not yet implemented - would show which resources depend on others
# Example: "Glue Crawler depends on S3 bucket (dependency met ✅)"
```

---


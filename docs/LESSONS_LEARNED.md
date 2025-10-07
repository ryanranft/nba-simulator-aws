# Lessons Learned - NBA Simulator AWS Project

<!-- AUTO-UPDATE TRIGGER: After encountering and solving any significant error or design decision -->
<!-- LAST UPDATED: 2025-10-01 -->

**Purpose:** Document all errors, failures, workarounds, and unexpected issues encountered during project setup. This serves as a critical reference when reproducing this pipeline for other sports (NHL, NCAA Basketball, NFL, MLB).

**For:** Future implementations of similar data pipelines for sports analytics

---

## Table of Contents

1. [Data Quality Issues](#data-quality-issues)
2. [AWS Glue Crawler Failures](#aws-glue-crawler-failures)
3. [RDS Instance Configuration Issues](#rds-instance-configuration-issues)
4. [AWS Free Tier Restrictions](#aws-free-tier-restrictions)
5. [PostgreSQL Version Availability](#postgresql-version-availability)
6. [Security Group Configuration](#security-group-configuration)
7. [Best Practices & Recommendations](#best-practices--recommendations)

---

## Data Quality Issues

### Issue #10: Not All Files Contain Usable Game Data (29% Empty)

**Date Discovered:** 2025-10-01
**Phase:** Phase 2.2 - ETL Planning
**Severity:** HIGH - Affects ETL efficiency and cost

#### Problem Description

After analyzing ESPN JSON files, discovered that **28.6% of PBP files contain NO actual play-by-play data** despite having the same file structure and size as valid files.

**Data Availability Analysis (500-file random sample):**
- ✅ Valid files: 357 (71.4%) - avg 451 plays, 1046 KB
- ❌ Empty files: 143 (28.6%) - avg 0 plays, 700 KB

**Estimated Impact on Full Dataset (44,826 PBP files):**
- ~32,005 files have usable data
- ~12,821 files are empty (waste ~8.6 GB storage, 29% compute)

#### Root Cause

ESPN's web scraping captures **ALL game pages**, including:
- **Valid games:** Regular season, playoffs, finals (have full play-by-play)
- **Empty games:** Scheduled future games, cancelled games, games without detailed coverage (no play-by-play data recorded)

Both file types contain:
- ESPN web page metadata (CSS, JavaScript, CDN paths)
- Game header information
- **Difference:** Valid files have `page.content.gamepackage.pbp.playGrps` with 400+ plays, empty files have empty `playGrps` array or missing section

#### How to Detect Empty Files

**JSON Path Check:**
```python
data['page']['content']['gamepackage']['pbp']['playGrps']
# Valid: [[play1, play2, ...], [play1, play2, ...], ...]  (4 periods with plays)
# Empty: []  (empty list or no playGrps key)
```

**Quick Heuristic (without parsing JSON):**
- File size > 900 KB → likely valid (71% accurate)
- File size < 800 KB → likely empty (28% accurate)
- **Best:** Parse JSON and check `playGrps` length

#### Data Structure Discovered

**Valid File Example:** `401307856.json`

1. **Play-by-Play Data** (`page.content.gamepackage.pbp.playGrps`):
   - 4 periods (quarters), each with ~100-150 plays
   - Total: ~468 plays per game
   - Sample keys: `id`, `period`, `text`, `homeAway`, `awayScore`, `homeScore`, `clock`
   - Includes: shots, turnovers, fouls, timeouts, substitutions, rebounds, assists

2. **Shot Chart Data** (`page.content.gamepackage.shtChrt.plays`):
   - ~225 shooting attempts per game
   - Includes: shot coordinates (x, y), shot type, make/miss, player, scoring

3. **Game Info** (`page.content.gamepackage.gmInfo`):
   - Venue: "crypto.com Arena"
   - Attendance: 4,087
   - Date/Time: "9:30 PM, May 12, 2021"
   - Location: "Los Angeles, CA"
   - Referees: John Goble, Eric Dalen, Curtis Blair

4. **Header** (`page.content.gamepackage.header`):
   - Team info, scores, game status

**Empty File Example:** `131105001.json`
- Has `gmInfo`, `header`
- Has `pbp.playGrps` but it's an empty list: `[]`
- Missing `shtChrt` section entirely

#### Impact on ETL

**Storage Waste:**
- 12,821 files × 700 KB = ~8.6 GB of empty files in S3
- Could save $0.20/month by deleting (minimal, not worth it)

**Compute Waste:**
- Glue ETL would process 12,821 unnecessary files
- 29% longer runtime → 29% higher Glue costs
- **Savings:** ~$3.72/month by pre-filtering (based on $13/month ETL estimate)

**Data Integrity:**
- Empty files would create database rows with NULL values
- Confuse analytics queries ("Why does this game have 0 plays?")

#### Solution

**✅ Pre-filter files in Glue ETL script:**

```python
# PySpark filtering logic
from pyspark.sql import functions as F

# Read all JSON files
df = spark.read.json("s3://nba-sim-raw-data-lake/pbp/*.json")

# Filter: Keep only files where playGrps has plays
df_valid = df.filter(
    F.size(F.col("page.content.gamepackage.pbp.playGrps")) > 0
)

# Explode playGrps to get individual plays
df_plays = df_valid.select(
    F.explode(F.col("page.content.gamepackage.pbp.playGrps")).alias("period")
).select(
    F.explode(F.col("period")).alias("play")
)
```

**Alternative Approaches:**
1. **Delete empty files from S3** (not recommended - may need them later)
2. **Use AWS Glue bookmark** to track processed files
3. **S3 Select** to filter before downloading (complex for nested JSON)

#### Lessons for Other Sports

**When scraping ESPN data for other sports:**

1. **Expect 20-40% empty files** in any ESPN dataset
   - Includes: scheduled future games, cancelled games, postponed games, exhibition games without full stats

2. **ALWAYS analyze data quality first** before writing ETL
   - Sample 200-500 files randomly
   - Check what % have actual play-by-play or detailed stats
   - Identify the JSON path that indicates "valid data"

3. **Document the filter criteria:**
   - NHL: Check if `gamepackageJSON.plays` has entries
   - NCAA: Check if `boxscore.players` has athlete data
   - NFL: Check if `drives` array has elements
   - MLB: Check if `innings` array has at-bats

4. **Budget for wasted storage:**
   - If scraping 200K files, expect 50-60K to be empty
   - Factor into S3 cost estimates

#### Commands Used

```bash
# Analysis script created
python scripts/analysis/check_data_availability.py

# Sample valid file examination
cat data/nba_pbp/401307856.json | python -m json.tool | grep -A 5 "playGrps"

# Sample empty file examination
cat data/nba_pbp/131105001.json | python -m json.tool | grep -A 5 "playGrps"
```

#### References

- **Valid file:** `data/nba_pbp/401307856.json` (1.0 MB, 468 plays)
- **Empty file:** `data/nba_pbp/131105001.json` (718 KB, 0 plays)
- **Analysis script:** `scripts/analysis/check_data_availability.py`
- **Related:** ADR-002 (10% field extraction), Phase 2.2 (Custom ETL)

---

## AWS Glue Crawler Failures

### Issue #11: Glue Crawlers Fail on ESPN JSON Data (All File Counts)

**Date Discovered:** 2025-10-01
**Phase:** Phase 2.1 - AWS Glue Crawler
**Severity:** CRITICAL - Blocks automated schema discovery
**Status:** Glue Crawler approach ABANDONED

#### Problem Description

AWS Glue Crawlers **cannot process ESPN NBA JSON files** regardless of file count or data volume. All attempts failed with "Internal Service Exception."

**Test Results:**

| Crawler | Files | Data Size | Duration | Result |
|---------|-------|-----------|----------|--------|
| nba-data-crawler (combined) | 146,115 | 119 GB | 90 min | ❌ OutOfMemoryError |
| nba-schedule-crawler | 11,633 | ~8 GB | 12 min | ❌ Internal Service Exception |
| nba-pbp-crawler | 44,826 | ~31 GB | Not run | (Created but not started) |
| nba-boxscores-crawler | 44,828 | ~31 GB | Not run | (Created but not started) |
| nba-teamstats-crawler | 44,828 | ~31 GB | Not run | (Created but not started) |

#### Root Cause

ESPN JSON files are **extremely large and deeply nested**:
- File size: ~700 KB per file
- Line count: 17,000-19,000 lines per file
- Structure: ESPN web page with embedded game data 5+ levels deep
- Content: Majority is web metadata (CSS, JavaScript, CDN paths)
- Game data location: `page.content.gamepackage.*` (buried in web page structure)

**Why Glue Crawlers Fail:**
1. **Memory overhead**: Each file requires deep JSON parsing to discover schema
2. **Nested complexity**: 5+ levels of nesting causes exponential memory growth
3. **Web metadata**: Crawlers try to catalog irrelevant ESPN web assets
4. **No sampling**: Glue processes ALL files, not a representative sample

#### Evidence

**CloudWatch Logs (nba-data-crawler):**
```
[23:52:52] Classification complete, writing results
[23:58:04] WARN: OutOfMemoryError - Submit AWS Support ticket
[00:03:17] ERROR: Internal Service Exception
```

**Error Message (all crawlers):**
```json
{
    "Status": "FAILED",
    "ErrorMessage": "Internal Service Exception",
    "LogGroup": "/aws-glue/crawlers",
    "LogStream": "nba-schedule-crawler"
}
```

#### Attempted Solutions (All Failed)

1. ✅ **Reduce file count**: Split into 4 crawlers (11K-45K files each)
   - Result: ❌ Still failed (schedule crawler with 11K files)

2. ✅ **Smaller data volume**: Start with smallest crawler first (8 GB)
   - Result: ❌ Still failed after 12 minutes

3. ❌ **NOT ATTEMPTED**: Custom classifiers (would add complexity without solving root issue)

4. ❌ **NOT ATTEMPTED**: Increase crawler DPU allocation (not worth cost for this data structure)

#### Decision: Skip Glue Crawlers Entirely

**Why skip:**
- Glue Crawlers are designed for simpler, flatter data structures
- ESPN JSON is too complex and large for automated cataloging
- We already know the schema (from manual analysis)
- We only need 10% of fields (Glue would catalog 100%)

**Better approach:**
- **Phase 2.2 Custom PySpark ETL** with hardcoded schema
- Extract only needed fields (10% extraction per ADR-002)
- Use **game ID pattern** to partition by year (user discovered pattern)
- Process year-by-year for better memory management

#### Game ID Pattern Discovery (Replacement Strategy)

**User discovered:** ESPN game IDs encode the date in the filename!

**Pattern:** `YYMMDD###`
- YY: Year code (offset system, see below)
- MM: Month (01-12)
- DD: Day (01-31)
- ###: Additional sequence digits

**Year Encoding Formula:**
- Pre-2018: `Actual Year = 1980 + Year Code`
  - Example: `17` → 1997, `31` → 2011
- 2018+: `401######` format (different encoding system)

**Examples:**
- `171031017` → Oct 31, 1997 (Year 17 = 1997)
- `200104005` → Jan 4, 2000 (Year 20 = 2000)
- `311011004` → Jan 1, 2011 (Year 31 = 2011)
- `401307856` → 2021 (401 format)

**ETL Benefit:**
- Partition S3 by year: `s3://.../schedule/year=1997/`, `s3://.../schedule/year=2020/`
- Process 1 year at a time (reduce memory usage)
- Skip years if needed (e.g., process only 2015-2025 for recent data)

#### Lessons Learned

**For Future Projects:**

1. **Always test with smallest subset first** before running large crawlers
2. **Check data structure complexity** before choosing Glue Crawlers
3. **Glue Crawlers are NOT suitable for:**
   - Deeply nested JSON (5+ levels)
   - Large JSON files (>500 KB per file)
   - Web scraping data with embedded content
   - Datasets where you only need 10% of fields

4. **When to use Glue Crawlers:**
   - Flat CSV/Parquet files
   - Simple JSON (2-3 levels max)
   - Well-structured data from APIs (not web scraping)
   - Need to catalog 80%+ of available fields

5. **Alternative approaches for complex data:**
   - Custom PySpark ETL with hardcoded schema
   - Manual schema definition in Glue Data Catalog
   - Athena with CREATE TABLE statements
   - Sample-based schema inference (process 100 files, infer schema, apply to all)

**Cost Impact:**
- Wasted crawler time: ~2 hours of Glue DPU usage (~$0.88)
- Avoided cost: Would have wasted more time on remaining 3 crawlers (~$2-3)
- **Savings by skipping:** Glue Crawlers would cost ~$13/month ongoing (now $0)

#### Resolution

**Phase 2.1 Status:** ❌ FAILED - SKIPPING GLUE CRAWLERS ENTIRELY

**Next Steps:**
1. Mark Phase 2.1 as SKIPPED in PROGRESS.md
2. Update Phase 2.2 ETL plan with:
   - Hardcoded schema (from manual analysis in DATA_STRUCTURE_GUIDE.md)
   - Game ID decoder function (year extraction)
   - Year-based partitioning strategy
3. Proceed directly to Phase 2.2 Custom PySpark ETL

---

### Issue #1: OutOfMemoryError with Large Datasets (146K+ files) [SUPERSEDED BY ISSUE #11]

**Date Encountered:** 2025-10-01
**Phase:** Phase 2.1 - AWS Glue Crawler Setup
**Severity:** CRITICAL - Blocks schema discovery

#### Problem Description

AWS Glue Crawler failed with `OutOfMemoryError` when attempting to catalog 146,115 JSON files (119 GB) across 4 S3 prefixes.

#### Timeline of Failure

```
[18:33:03 EST] BENCHMARK: Running Start Crawl for Crawler nba-data-crawler
[18:52:52 EST] BENCHMARK: Classification complete, writing results to database nba_raw_data
[18:52:52 EST] INFO: Crawler configured with SchemaChangePolicy
[18:58:04 EST] WARN: OutOfMemoryError - Submit AWS Support ticket
[19:03:17 EST] ERROR: Internal Service Exception
[19:05:17 EST] BENCHMARK: Crawler has finished running and is in state READY
```

**Total Runtime:** 32 minutes (18 min classification + 14 min failure/cleanup)

#### Root Cause

- Glue Crawler successfully classified 146,115 files
- Failed when writing metadata to AWS Glue Data Catalog
- Default crawler DPU (Data Processing Units) allocation insufficient for 100K+ files
- AWS imposes memory limits on crawler operations

#### Error Messages

**CloudWatch Logs (`/aws-glue/crawlers/nba-data-crawler`):**
```
WARN: OutOfMemoryError: Please submit a ticket to AWS Support to resolve OutOfMemory error for crawler
ERROR: Internal Service Exception
```

**AWS CLI Output:**
```bash
aws glue get-crawler --name nba-data-crawler --query 'Crawler.LastCrawl.Status'
# Output: FAILED

aws glue get-crawler --name nba-data-crawler --query 'Crawler.LastCrawl.ErrorMessage'
# Output: Internal Service Exception
```

#### Impact

- Cannot automatically discover JSON schema
- Blocks Phase 2.2 (Glue ETL Job) if following original plan
- Must manually define table schemas OR skip crawler entirely

#### Solutions Attempted

**❌ Option 1: Partition Data by Year/Season**
- **Attempt:** Check if S3 data organized by year to create separate crawlers
- **Command:** `aws s3 ls s3://nba-sim-raw-data-lake/schedule/ | head -20`
- **Result:** Data stored flat with date-based filenames (YYYYMMDD.json), not organized in year folders
- **Verdict:** Cannot easily partition without reorganizing 146K files

**❌ Option 2: Request DPU Increase via AWS Support**
- **Approach:** Submit support ticket to increase DPU allocation from default 2 DPU to 10 DPU
- **Cost Impact:** ~$0.44/hour per DPU (10 DPU = $4.40/hour)
- **Timeline:** 1-3 business days for support response
- **Verdict:** Too slow, adds complexity and cost

**✅ Option 3: Skip Glue Crawler Entirely (RECOMMENDED)**
- **Approach:** Proceed directly to Phase 2.2, write custom PySpark ETL code
- **Rationale:**
  1. Avoids OOM issue completely
  2. Gives precise control over field extraction (matches ADR-002: 10% extraction)
  3. Actually faster than waiting for crawler + support ticket
  4. More maintainable for future updates
- **Trade-off:** Must manually inspect JSON structure and write schema definitions
- **Verdict:** Best approach for large datasets (100K+ files)

#### Final Decision

**Skip AWS Glue Crawler entirely.** Proceed directly to Phase 2.2 (Glue ETL Job) where we write custom PySpark code to:
1. Manually define source schemas
2. Extract only the 10% of fields we need
3. Transform and load into RDS

**Documented in:**
- `PROGRESS.md` - Phase 2.1 status updated to ❌ FAILED - SKIPPING
- `docs/REPRODUCTION_GUIDE.md` - Section "Glue Crawler Out of Memory Error"
- ADR-008 (to be created) - Skip Glue Crawler for Large Datasets

#### Commands to Clean Up Failed Crawler

```bash
# Delete failed crawler
aws glue delete-crawler --name nba-data-crawler

# Keep Glue database for manual table definitions
# aws glue delete-database --name nba_raw_data  # DON'T DELETE - we'll use it
```

#### Lessons for Future Sports

**When to use Glue Crawler:**
- Datasets < 50,000 files
- Well-structured data with consistent schema
- Exploratory analysis where exact schema unknown

**When to skip Glue Crawler:**
- Datasets > 100,000 files (OOM risk)
- Complex nested JSON requiring field extraction
- Known schema where manual definition is straightforward
- Cost-sensitive projects (crawler runs cost money)

**Estimated File Count Thresholds:**
- **Safe:** 0-50,000 files → Use Glue Crawler
- **Risky:** 50,000-100,000 files → Test first, monitor CloudWatch
- **Fail:** 100,000+ files → Skip crawler, use manual schemas

**Sport-Specific Estimates:**
| Sport | Estimated Files | Glue Crawler Recommended? |
|-------|-----------------|---------------------------|
| NBA | 146,115 | ❌ NO - Skip |
| NHL | ~100,000 | ⚠️ MAYBE - Test first |
| NCAA BB | ~200,000 | ❌ NO - Skip |
| NFL | ~50,000 | ✅ YES - Should work |
| MLB | ~300,000 | ❌ NO - Skip |

---

## RDS Instance Configuration Issues

### Issue #2: Password Special Character Restrictions

**Date Encountered:** 2025-10-01
**Phase:** Phase 3.1 - RDS PostgreSQL Setup
**Severity:** MEDIUM - Delays instance creation

#### Problem Description

RDS instance creation failed due to invalid password characters.

#### Error Message

```bash
aws rds create-db-instance --master-user-password 'NbaS1m2025!SecureP@ss' ...

# Error:
InvalidParameterValue: The parameter MasterUserPassword is not a valid password.
Only printable ASCII characters besides '/', '@', '"', ' ' may be used.
```

#### Root Cause

AWS RDS PostgreSQL restricts password characters:
- **Allowed:** A-Z, a-z, 0-9, and most special characters
- **NOT Allowed:** `/`, `@`, `"`, space

Our original password `NbaS1m2025!SecureP@ss` contained `@` which is forbidden.

#### Solution

Changed password to: `[REDACTED]` (removed `@` character, used valid special characters)

**Valid Special Characters:**
```
! # $ % ^ & * ( ) _ + - = [ ] { } | \ : ; < > , . ?
```

#### Lesson for Future Sports

**Password Policy for RDS:**
1. Minimum 8 characters
2. Must include uppercase, lowercase, number, special character
3. **Avoid:** `/`, `@`, `"`, space
4. **Recommended Format:** `{Sport}Simulator{Year}!` (e.g., `NhlSimulator2025!`, `NcaaSimulator2025!`)

---

## AWS Free Tier Restrictions

### Issue #3: FreeTierRestrictionError - db.t3.small Not Available

**Date Encountered:** 2025-10-01
**Phase:** Phase 3.1 - RDS PostgreSQL Setup
**Severity:** MEDIUM - Requires instance class change

#### Problem Description

First attempt to create `db.t3.small` RDS instance failed due to free tier account restrictions.

#### Error Message

```bash
aws rds create-db-instance --db-instance-class db.t3.small ...

# Error:
FreeTierRestrictionError: This instance size isn't available with free plan accounts.
Choose a different instance size or upgrade your account.
```

#### Root Cause

AWS Free Tier accounts (first 12 months) are limited to:
- **Only db.t3.micro** (1 GB RAM, burstable CPU)
- **Only db.t2.micro** (older generation)

Cannot use db.t3.small (2 GB RAM) without upgrading account.

#### Solution Attempted

**Attempt 1:** Created db.t3.micro instance
```bash
aws rds create-db-instance --db-instance-class db.t3.micro ...
# SUCCESS - instance created
```

**Attempt 2:** User upgraded AWS account off free tier
```bash
# User confirmed: "I just upgraded my aws account off of the free tier"
# Deleted db.t3.micro instance
aws rds delete-db-instance --db-instance-identifier nba-sim-db --skip-final-snapshot

# Created db.t3.small instance (2 GB RAM)
aws rds create-db-instance --db-instance-class db.t3.small ...
# SUCCESS
```

#### Cost Difference

| Instance Class | RAM | vCPUs | Cost/Month | Free Tier? |
|----------------|-----|-------|------------|------------|
| db.t3.micro | 1 GB | 2 | ~$15 | ✅ YES |
| db.t3.small | 2 GB | 2 | ~$29 | ❌ NO (paid only) |
| db.t3.medium | 4 GB | 2 | ~$60 | ❌ NO (paid only) |

#### Lesson for Future Sports

**Free Tier Accounts:**
- Can ONLY use `db.t3.micro` or `db.t2.micro`
- 750 hours/month free for first 12 months
- 20 GB storage included
- **Limitation:** 1 GB RAM may be insufficient for large datasets

**Paid Accounts:**
- Can use any instance class
- **Recommended:** Start with `db.t3.small` (2 GB RAM, $29/month)
- Can upgrade to `db.t3.medium` later with ~5 minutes downtime

**Decision Matrix:**
```
If (Account Type == "Free Tier"):
    Use db.t3.micro (accept performance limitations)
Else:
    Use db.t3.small for development
    Use db.t3.medium for production
```

---

## PostgreSQL Version Availability

### Issue #4: PostgreSQL Version 15.6 Not Found

**Date Encountered:** 2025-10-01
**Phase:** Phase 3.1 - RDS PostgreSQL Setup
**Severity:** LOW - Easy fix

#### Problem Description

RDS instance creation failed because specified PostgreSQL version doesn't exist.

#### Error Message

```bash
aws rds create-db-instance --engine postgres --engine-version 15.6 ...

# Error:
InvalidParameterCombination: Cannot find version 15.6 for postgres
```

#### Root Cause

AWS RDS doesn't offer every minor PostgreSQL version. Version 15.6 specifically doesn't exist in us-east-1.

#### Solution

**Step 1: List available PostgreSQL 15.x versions**
```bash
aws rds describe-db-engine-versions \
  --engine postgres \
  --engine-version 15 \
  --query 'DBEngineVersions[*].EngineVersion' \
  --output text

# Output:
# 15.7 15.8 15.10 15.12 15.13 15.14
```

**Step 2: Use latest available version (15.14)**
```bash
aws rds create-db-instance --engine-version 15.14 ...
# SUCCESS
```

#### Lesson for Future Sports

**Always check available versions first:**

```bash
# PostgreSQL
aws rds describe-db-engine-versions --engine postgres --engine-version 15 \
  --query 'DBEngineVersions[*].EngineVersion' --output text | sort | tail -5

# MySQL
aws rds describe-db-engine-versions --engine mysql --engine-version 8.0 \
  --query 'DBEngineVersions[*].EngineVersion' --output text | sort | tail -5

# MariaDB
aws rds describe-db-engine-versions --engine mariadb --engine-version 10.11 \
  --query 'DBEngineVersions[*].EngineVersion' --output text | sort | tail -5
```

**Recommendation:** Always use the **latest minor version** in a major version family for:
- Security patches
- Bug fixes
- Performance improvements

**For this project:**
- ✅ Use PostgreSQL 15.14 (latest in 15.x family)
- ⚠️ Avoid 15.6, 15.9, 15.11 (don't exist in AWS)

---

## Security Group Configuration

### Issue #5: AWS CLI `--description` Parameter Not Supported

**Date Encountered:** 2025-10-01
**Phase:** Phase 3.1 - RDS Security Group Setup
**Severity:** LOW - Cosmetic issue

#### Problem Description

Attempted to add description when authorizing security group ingress rule, but parameter not supported.

#### Error Message

```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-079ed470e0caaca44 \
  --protocol tcp \
  --port 5432 \
  --cidr 174.62.194.89/32 \
  --description "PostgreSQL access from home IP"

# Error:
Unknown options: --description, PostgreSQL access from home IP
```

#### Root Cause

The `authorize-security-group-ingress` command doesn't support `--description` parameter directly. Description must be added separately.

#### Solution

**Remove `--description` parameter:**
```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-079ed470e0caaca44 \
  --protocol tcp \
  --port 5432 \
  --cidr 174.62.194.89/32

# SUCCESS
```

**To add description (optional):**
```bash
aws ec2 update-security-group-rule-descriptions-ingress \
  --group-id sg-079ed470e0caaca44 \
  --ip-permissions \
    "IpProtocol=tcp,FromPort=5432,ToPort=5432,IpRanges=[{CidrIp=174.62.194.89/32,Description='PostgreSQL access from home IP'}]"
```

#### Lesson for Future Sports

**Security Group Best Practices:**

1. **Create security group with proper name/description:**
```bash
SG_ID=$(aws ec2 create-security-group \
  --group-name <sport>-rds-access \
  --description "PostgreSQL access for <SPORT> simulator" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)
```

2. **Add ingress rules WITHOUT --description:**
```bash
# Get your current IP
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Allow PostgreSQL access
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32
```

3. **Verify rules:**
```bash
aws ec2 describe-security-groups \
  --group-ids $SG_ID \
  --query 'SecurityGroups[0].IpPermissions'
```

**Common Ports by Database:**
- PostgreSQL: 5432
- MySQL: 3306
- MongoDB: 27017
- Redis: 6379

---

## Best Practices & Recommendations

### Lesson #6: Instance Creation Monitoring Strategy

**Issue:** RDS instance creation takes 10-15 minutes. How to monitor efficiently?

#### What We Learned

**✅ Good Approaches:**
1. **Simple polling with sleep:**
```bash
aws rds describe-db-instances \
  --db-instance-identifier nba-sim-db \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text

# Statuses: creating → backing-up → available
```

2. **Use `aws rds wait` command:**
```bash
aws rds wait db-instance-available --db-instance-identifier nba-sim-db
echo "RDS instance is now available!"
```

**❌ Avoid:**
- Complex bash loops with jq arithmetic (syntax errors in Claude Code environment)
- Continuous monitoring without sleep intervals (wastes API calls)
- Running commands in background without proper error handling

#### Recommended Monitoring Pattern

```bash
# Start RDS instance creation
aws rds create-db-instance ... > /tmp/rds_creation.json

# Wait for availability (blocks until ready)
echo "Waiting for RDS instance to be available..."
aws rds wait db-instance-available --db-instance-identifier <sport>-sim-db

# Get endpoint when ready
ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier <sport>-sim-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "✅ RDS instance available at: $ENDPOINT"
```

---

### Lesson #7: Cost Tracking During Setup

**Issue:** AWS costs can escalate quickly during setup. How to track?

#### What We Learned

**Track resources created and their costs:**

| Resource | When Created | Monthly Cost | Can Be Stopped? |
|----------|--------------|--------------|-----------------|
| S3 Bucket | Phase 0 | $2.74 | ❌ No (storage) |
| Glue Database | Phase 2.1 | $0 | N/A (metadata) |
| IAM Role | Phase 2.1 | $0 | N/A |
| Glue Crawler | Phase 2.1 | $0 (failed) | N/A |
| Security Group | Phase 3.1 | $0 | N/A |
| RDS db.t3.small | Phase 3.1 | $29 | ⚠️ Can stop (7 days max) |

**Cost Checkpoints:**
```bash
# Run after each phase
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-02 \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --group-by Type=SERVICE

# Or use project script
bash scripts/aws/check_costs.sh
```

**Set up billing alert:**
```bash
# Create SNS topic for alerts
aws sns create-topic --name billing-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:billing-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Create budget alert at $50, $100, $150 thresholds
```

---

### Lesson #8: SQL Schema Creation Order

**Issue:** What order should SQL scripts be executed?

#### What We Learned

**Correct Order:**
1. `create_tables.sql` - Create all tables (respect foreign key dependencies)
2. `create_indexes.sql` - Create performance indexes
3. (Optional) `create_foreign_keys.sql` - Add foreign key constraints if not in tables

**Table Creation Order (respects FK dependencies):**
```sql
-- 1. Reference tables (no foreign keys)
CREATE TABLE teams (...);

-- 2. Tables depending on reference tables
CREATE TABLE players (
    ...
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- 3. Tables depending on multiple tables
CREATE TABLE games (
    ...
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id)
);

-- 4. Fact tables (depend on everything)
CREATE TABLE player_game_stats (
    ...
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);
```

**Index Creation After Tables:**
- Indexes should be created AFTER all tables exist
- Create indexes on foreign keys for query performance
- Create composite indexes for common query patterns

---

### Lesson #9: Documentation as You Go

**Issue:** How to ensure reproducibility for other sports?

#### What We Learned

**Critical Documentation:**

1. **PROGRESS.md** - Real-time status updates
   - Update immediately after completing/failing each step
   - Include actual times, not just estimates
   - Document WHY decisions were made

2. **LESSONS_LEARNED.md** (this file) - Error catalog
   - Document every error encountered
   - Include exact error messages
   - Provide working solutions, not just theory

3. **REPRODUCTION_GUIDE.md** - Step-by-step instructions
   - Assume reader knows nothing about this project
   - Include all commands with explanations
   - Sport-specific sections for customization

4. **ADRs (Architecture Decision Records)** - Major decisions
   - Create ADR for any decision that affects architecture
   - Example: ADR-008 "Skip Glue Crawler for Large Datasets"

**Update Triggers:**
- ✅ After solving any error that took >10 minutes
- ✅ After making any architectural decision
- ✅ After discovering any AWS limitation
- ✅ After completing any phase

---

## Quick Reference: Error Resolution Checklist

When you encounter an error while reproducing this for another sport:

1. ✅ Check **TROUBLESHOOTING.md** first (28 documented issues)
2. ✅ Check this file (LESSONS_LEARNED.md) for similar errors
3. ✅ Check CloudWatch logs for detailed error messages
4. ✅ Search AWS documentation for error code
5. ✅ Try the command with `--debug` flag for verbose output
6. ✅ Check if it's a regional limitation (`aws ec2 describe-regions`)
7. ✅ Verify IAM permissions (`aws iam simulate-principal-policy`)
8. ✅ Document the error and solution in this file
9. ✅ Update TROUBLESHOOTING.md if generally applicable

---

## Commands Reference: Quick Copy-Paste

**Check PostgreSQL versions:**
```bash
aws rds describe-db-engine-versions --engine postgres --engine-version 15 \
  --query 'DBEngineVersions[*].EngineVersion' --output text
```

**Get your public IP:**
```bash
curl -s https://checkip.amazonaws.com
```

**Check RDS status:**
```bash
aws rds describe-db-instances --db-instance-identifier <db-name> \
  --query 'DBInstances[0].[DBInstanceStatus,Endpoint.Address]' --output table
```

**Monitor costs:**
```bash
bash scripts/aws/check_costs.sh
```

**List Glue crawler logs:**
```bash
aws logs tail /aws-glue/crawlers --log-stream-names <crawler-name> --since 3h
```

---

## Summary of Key Failures

| # | Issue | Phase | Severity | Solution |
|---|-------|-------|----------|----------|
| 1 | Glue Crawler OutOfMemoryError | 2.1 | CRITICAL | Skip crawler, use manual ETL |
| 2 | RDS password invalid characters | 3.1 | MEDIUM | Remove `@` from password |
| 3 | Free tier restriction db.t3.small | 3.1 | MEDIUM | Upgrade account or use db.t3.micro |
| 4 | PostgreSQL version 15.6 not found | 3.1 | LOW | Use version 15.14 |
| 5 | Security group --description error | 3.1 | LOW | Remove --description parameter |

---

**Total Setup Time Lost to Errors:** ~2 hours
**Time Saved for Future Sports:** ~2 hours per sport

**Last Updated:** 2025-10-01
**Next Update:** After completing Phase 3.1 or encountering new errors
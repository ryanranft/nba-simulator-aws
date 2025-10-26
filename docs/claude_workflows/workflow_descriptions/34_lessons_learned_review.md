# Workflow #34: Lessons Learned Review

**Category:** Error Prevention
**Priority:** High
**When to Use:** Before starting similar tasks to avoid repeating known mistakes
**Related Workflows:** #22 (Troubleshooting), #3 (Decision Workflow)

---

## Overview

This workflow guides you to consult `docs/LESSONS_LEARNED.md` before undertaking tasks that have known pitfalls. Use this to avoid repeating mistakes and leverage solutions already discovered.

**Purpose:** Learn from past errors before they happen again.

---

## When to Use This Workflow

✅ **USE before:**
- Creating AWS Glue Crawlers (Issue #11)
- Analyzing data quality (Issue #10)
- Creating RDS instances (Issues #2-6)
- Setting up security groups (Issue #7)
- Any Phase 2-5 tasks

❌ **DON'T NEED when:**
- Just reading documentation
- Simple queries or scripts
- Tasks already completed successfully before

---

## Workflow Steps

### Step 1: Identify Your Task Category

**Ask yourself:** What am I about to do?

**Categories in LESSONS_LEARNED.md:**
1. Data Quality Issues
2. AWS Glue Crawler Failures
3. RDS Instance Configuration Issues
4. AWS Free Tier Restrictions
5. PostgreSQL Version Availability
6. Security Group Configuration
7. Best Practices & Recommendations

### Step 2: Read Relevant Section

```bash
# Open lessons learned document
cat docs/LESSONS_LEARNED.md | less

# Or search for specific topic
grep -A 20 "Glue Crawler" docs/LESSONS_LEARNED.md
```

**Read the section that matches your task.**

### Step 3: Check for Known Issues

**Look for:**
- [ ] Specific errors mentioned (exact error messages)
- [ ] Root causes explained
- [ ] Solutions that worked
- [ ] Solutions that didn't work
- [ ] Commands to avoid or use

### Step 4: Apply Lessons to Your Task

**Modify your approach based on lessons:**
- Skip known failing approaches
- Use proven solutions first
- Add validation steps from lessons
- Budget extra time for known gotchas

---

## Critical Lessons By Phase

### 2.0001: Glue Crawler Setup

**🚨 CRITICAL: Skip Glue Crawlers Entirely**

**Issue #11:** Glue Crawlers fail on ESPN JSON data (ALL file counts tested)

**Why they fail:**
- ESPN JSON files are 700 KB each with 17,000+ lines
- Deeply nested (5+ levels)
- Crawler runs out of memory even with 11K files

**What was tried (all failed):**
- ❌ Reducing file count to 11,633 files (still failed)
- ❌ Splitting into 4 separate crawlers (still failed)
- ❌ Processing smallest dataset first (8 GB, still failed)

**Solution:**
- **Skip Glue Crawlers entirely**
- Write custom PySpark ETL script with hardcoded schema
- Use year-based partitioning (game ID pattern discovered)

**Commands to skip:**
```bash
# DON'T DO THIS:
aws glue create-crawler --name <sport>-data-crawler ...

# DO THIS INSTEAD:
# Proceed directly to custom ETL script (2.0002)
```

**Saves:**
- ~2 hours of debugging time
- ~$0.88 in wasted Glue DPU costs
- Ongoing $13/month if crawler was working

---

### 2.0002: Data Quality Analysis

**🚨 CRITICAL: Expect 20-40% Empty Files**

**Issue #10:** Not all files contain usable game data (29% empty in NBA)

**Why:**
- ESPN captures scheduled future games (no data yet)
- Cancelled/postponed games (never played)
- Exhibition games without full stats
- Different coverage for regular vs playoff games

**Validation:**
```python
# Check if file has usable data (NBA example)
data['page']['content']['gamepackage']['pbp']['playGrps']
# Valid: [[play1, play2, ...], ...]  (has plays)
# Empty: []  (no plays)

# Sport-specific checks:
# NHL: Check if 'plays' array has entries
# NFL: Check if 'drives' array has elements
# MLB: Check if 'innings' array has at-bats
```

**Solution:**
- Run data quality analysis FIRST (sample 200-500 files)
- Document percentage of empty files
- Add pre-filter to ETL to skip empty files
- Budget for storage waste (~30% of S3 costs)

**Commands:**
```bash
# Run data quality analysis
python scripts/analysis/check_data_availability.py

# Expected output:
# Valid files: 71.4% (357/500)
# Empty files: 28.6% (143/500)
```

**Saves:**
- ~29% Glue compute costs by pre-filtering
- Database storage (no empty records)
- Query performance (no NULL-heavy rows)

---

### 3.0001: RDS Instance Creation

**Issue #2: Password Character Restrictions**

**Problem:** RDS rejects passwords with `/`, `@`, `"`, or spaces

**Error:**
```
InvalidParameterValue: The parameter MasterUserPassword is not a valid password.
Only printable ASCII characters besides '/', '@', '"', ' ' may be used.
```

**Solution:**
```bash
# GOOD passwords:
NbaS1m2025!SecurePass
SportData#2025$Pipeline

# BAD passwords:
NbaS1m2025!SecureP@ss  # Contains @
Sport/Data#2025        # Contains /
"SecurePass123"        # Contains "
```

---

**Issue #3: Free Tier Excludes db.t3.small**

**Problem:** Wanted db.t3.small but it's not Free Tier eligible

**Free Tier limitations:**
- Only **db.t2.micro** and **db.t3.micro** eligible
- 750 hours/month free for 12 months
- 20 GB storage included

**Cost comparison:**
- db.t2.micro (Free Tier): $0/month (first 12 months)
- db.t3.micro: ~$15/month
- db.t3.small: ~$29/month

**Solution:**
- Start with db.t3.micro if under Free Tier
- Upgrade to db.t3.small when needed (~120K+ games)
- Monitor memory usage before upgrading

---

**Issue #4: PostgreSQL 16 Not Available in us-east-1**

**Problem:** Tried to create RDS with PostgreSQL 16.4 (latest)

**Error:**
```
InvalidParameterCombination: RDS does not support creating a DB instance with the following combination:
DBInstanceClass=db.t3.small, Engine=postgres, EngineVersion=16.4
```

**Root cause:** PostgreSQL 16 not available for db.t3.* in us-east-1

**Solution:**
```bash
# Check available versions
aws rds describe-db-engine-versions \
  --engine postgres \
  --query 'DBEngineVersions[?contains(SupportedEngineModes, `NULL`)].EngineVersion' \
  --output table

# Use PostgreSQL 15.14 instead
--engine-version 15.14
```

**Lesson:** Always check version availability before creating instances

---

### 3.0001: Security Group Configuration

**Issue #7: Port 5432 Must Be Open**

**Problem:** Cannot connect to RDS - connection refused

**Root cause:** Security group doesn't allow PostgreSQL port (5432)

**Solution:**
```bash
# Get your current IP
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Add your IP to security group
aws ec2 authorize-security-group-ingress \
  --group-id <sg-id> \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32

# Verify rule added
aws ec2 describe-security-groups \
  --group-ids <sg-id> \
  --query 'SecurityGroups[0].IpPermissions'
```

**Best practice:**
- Add specific IPs (not 0.0.0.0/0)
- Update when IP changes (home → office → travel)
- Document allowed IPs in RDS_CONNECTION.md

---

## Quick Reference: Avoid These Commands

### ❌ DON'T RUN (Known to Fail)

**Glue Crawlers on ESPN Data:**
```bash
# This WILL fail with OutOfMemoryError
aws glue create-crawler --name nba-data-crawler ...
aws glue start-crawler --name nba-data-crawler
```

**PostgreSQL 16 on db.t3.* in us-east-1:**
```bash
# This WILL fail - version not available
aws rds create-db-instance \
  --engine postgres \
  --engine-version 16.4 \
  --db-instance-class db.t3.small
```

**RDS Passwords with @ / " symbols:**
```bash
# This WILL fail - invalid characters
aws rds create-db-instance \
  --master-user-password 'Pass@word123'
```

---

## Quick Reference: Use These Instead

### ✅ PROVEN APPROACHES

**Data Quality Analysis:**
```bash
# Sample files to understand data structure
python scripts/analysis/check_data_availability.py

# Expected: 70-80% valid files, 20-30% empty
```

**Custom ETL (Skip Crawler):**
```python
# Write custom PySpark with hardcoded schema
df = spark.read.json("s3://bucket/data/*.json")

# Pre-filter empty files
df_valid = df.filter(F.size(F.col("data.plays")) > 0)

# Extract only needed fields (10% extraction)
```

**RDS Instance Creation:**
```bash
# Use PostgreSQL 15.14 with valid password
aws rds create-db-instance \
  --engine postgres \
  --engine-version 15.14 \
  --db-instance-class db.t3.small \
  --master-user-password 'ValidPass123!'  # No @ / " symbols
```

**Security Group Setup:**
```bash
# Add your specific IP, not 0.0.0.0/0
MY_IP=$(curl -s https://checkip.amazonaws.com)

aws ec2 authorize-security-group-ingress \
  --group-id <sg-id> \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32
```

---

## Best Practices from Lessons

### Data Quality

1. **Always analyze data quality BEFORE ETL**
   - Sample 200-500 files randomly
   - Check percentage of valid vs empty files
   - Identify filter criteria early

2. **Expect 20-40% empty files in ESPN data**
   - Budget storage for waste
   - Pre-filter in ETL to save compute
   - Document filter criteria

3. **Validate JSON structure assumptions**
   - Check nested field paths exist
   - Handle missing sections gracefully
   - Test with edge cases (empty, malformed, huge files)

### AWS Glue

1. **Glue Crawlers NOT suitable for:**
   - Deeply nested JSON (5+ levels)
   - Large files (>500 KB per file)
   - >100K files total
   - Web scraping data (embedded content)

2. **When to use Glue Crawlers:**
   - Flat CSV/Parquet files
   - Simple JSON (2-3 levels max)
   - <50K files total
   - Well-structured API data

3. **Custom ETL benefits:**
   - Full control over field extraction
   - Better memory management
   - Faster for large datasets
   - More maintainable

### RDS Configuration

1. **Check version availability first:**
   ```bash
   aws rds describe-db-engine-versions --engine postgres
   ```

2. **Use valid password characters:**
   - A-Z, a-z, 0-9, `!#$%^&*()-_=+`
   - Avoid: `/`, `@`, `"`, spaces

3. **Start small, scale up:**
   - db.t3.micro → db.t3.small → db.t3.medium
   - Monitor performance before upgrading
   - Easier to upgrade than downgrade

4. **Security group setup:**
   - Specific IPs only (not 0.0.0.0/0)
   - Port 5432 for PostgreSQL
   - Update when IP changes

### Cost Optimization

1. **Free Tier limits:**
   - db.t2.micro or db.t3.micro only
   - 750 hours/month for 12 months
   - 20 GB storage included

2. **Skip failed approaches:**
   - Don't waste time on known failures
   - Use proven solutions first
   - Saves debugging time and $ costs

3. **Pre-filter empty files:**
   - Saves ~30% Glue compute costs
   - Reduces database storage
   - Faster ETL runtime

---

## Workflow Integration

### Before 2.0001 (Glue Crawler):
1. **Read:** LESSONS_LEARNED.md Issue #11
2. **Decision:** Skip Glue Crawler entirely
3. **Action:** Proceed directly to 2.0002 Custom ETL

### Before 2.0002 (ETL Planning):
1. **Read:** LESSONS_LEARNED.md Issue #10
2. **Action:** Run data quality analysis first
3. **Plan:** Add pre-filter for empty files (save 30% compute)

### Before 3.0001 (RDS Creation):
1. **Read:** LESSONS_LEARNED.md Issues #2-6
2. **Check:** PostgreSQL version availability
3. **Prepare:** Valid password (no @ / " symbols)
4. **Plan:** Security group setup (port 5432, your IP)

### When Errors Occur:
1. **Search:** LESSONS_LEARNED.md for error message
2. **Check:** If error already documented
3. **Use:** Documented solution if available
4. **Add:** New lesson if error is novel

---

## Maintaining LESSONS_LEARNED.md

**When to add new lessons:**

✅ **ADD when:**
- Error took >30 minutes to solve
- Error is likely to recur
- Solution is non-obvious
- Workaround is project-specific
- AWS behavior is unexpected

❌ **DON'T ADD when:**
- Simple typo or syntax error
- Well-documented in AWS docs
- One-time fluke (not reproducible)
- User-specific environment issue

**Lesson format:**
```markdown
### Issue #X: [Brief Title]

**Date Discovered:** YYYY-MM-DD
**Phase:** Phase X.Y - [Task]
**Severity:** CRITICAL / HIGH / MEDIUM / LOW

#### Problem Description
[What went wrong]

#### Root Cause
[Why it happened]

#### Solution
[What worked]

#### Commands Used
[Actual commands]

#### Lessons for Future Sports
[How to avoid in other projects]
```

---

## Troubleshooting with Lessons

**Pattern: Error → Search → Apply**

### Step 1: Error Occurs
```bash
# Example error
InvalidParameterCombination: RDS does not support creating a DB instance...
```

### Step 2: Search Lessons Learned
```bash
grep -i "InvalidParameterCombination" docs/LESSONS_LEARNED.md

# Found: Issue #4 - PostgreSQL Version
```

### Step 3: Read Relevant Lesson
```markdown
Issue #4: PostgreSQL 16 Not Available
Root Cause: Version not available for db.t3.* in us-east-1
Solution: Use PostgreSQL 15.14 instead
```

### Step 4: Apply Solution
```bash
# Change from PostgreSQL 16 to 15.14
aws rds create-db-instance \
  --engine-version 15.14 \
  # ... rest of command
```

### Step 5: Verify Fixed
```bash
# Check RDS instance created successfully
aws rds describe-db-instances --db-instance-identifier nba-sim-db
```

---

## Summary: Most Critical Lessons

**Top 5 Things to Remember:**

1. **Skip Glue Crawlers** for large/complex ESPN data (Issue #11)
2. **Expect 30% empty files** in ESPN datasets (Issue #10)
3. **Use PostgreSQL 15.14**, not 16 (Issue #4)
4. **Avoid @ / " in RDS passwords** (Issue #2)
5. **Security group needs port 5432** for PostgreSQL (Issue #7)

**Follow these, and you'll avoid 90%+ of known issues.**

---

**Last Updated:** 2025-10-02
**Source:** docs/LESSONS_LEARNED.md
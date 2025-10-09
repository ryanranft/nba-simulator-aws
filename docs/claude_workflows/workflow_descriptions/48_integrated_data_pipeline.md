# Workflow #48: Integrated Data Collection Pipeline

**Purpose:** Unified workflow that combines data inventory, gap analysis, scraper management, and quality validation into a streamlined pipeline.

**Created:** October 9, 2025
**Integrates:** Workflows #45 (Local Inventory), #46 (Gap Analysis), #47 (AWS Inventory), #40 (Scraper Operations), #42 (Scraper Management)

---

## When to Use This Workflow

**Use this workflow when:**
- Starting a new data collection session
- Need to understand current data state AND fill gaps
- Want automated recommendation for which scrapers to run
- Running regular data updates (weekly/monthly)
- After identifying missing data and ready to collect
- Want a single command to orchestrate the entire pipeline

**Don't use this workflow when:**
- Only need to check data status (use Workflow #45 or #47)
- Only need gap analysis (use Workflow #46)
- Already know which scraper to run (use Workflow #40 directly)
- Need fine-grained control over scraper parameters

---

## Quick Reference

### Common Commands

```bash
# Full pipeline (inventory → gaps → plan → collect → validate)
bash scripts/monitoring/data_pipeline_manager.sh full

# Check status only (inventory + gap analysis)
bash scripts/monitoring/data_pipeline_manager.sh status

# Generate collection plan only
bash scripts/monitoring/data_pipeline_manager.sh plan

# Launch scraper to fill gaps
bash scripts/monitoring/data_pipeline_manager.sh collect

# Validate data quality after collection
bash scripts/monitoring/data_pipeline_manager.sh validate
```

---

## Pipeline Architecture

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: DATA INVENTORY (Workflows #45, #47)             │
│  ─────────────────────────────────────────────────────────  │
│  • Local data inventory (disk, /tmp)                        │
│  • AWS data inventory (S3, RDS)                             │
│  • Generate baseline metrics                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: GAP ANALYSIS (Workflow #46)                      │
│  ─────────────────────────────────────────────────────────  │
│  • Compare expected vs actual games                         │
│  • Check play-by-play coverage                              │
│  • Identify S3 sync gaps                                    │
│  • Prioritize missing data                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: COLLECTION PLAN                                   │
│  ─────────────────────────────────────────────────────────  │
│  • Generate actionable recommendations                      │
│  • Estimate scraper runtimes                                │
│  • Provide scraper selection guidance                       │
│  • Create executable commands                               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: DATA COLLECTION (Workflows #40, #42)             │
│  ─────────────────────────────────────────────────────────  │
│  • Interactive scraper selection                            │
│  • Launch scraper in background                             │
│  • Provide monitoring commands                              │
│  • Reference Workflow #38 for overnight jobs                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 5: VALIDATION (Workflow #41)                         │
│  ─────────────────────────────────────────────────────────  │
│  • Check scraper output exists                              │
│  • Validate file format (JSON, CSV)                         │
│  • Run feature engineering readiness test                   │
│  • Generate validation report                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Workflow Steps

### Mode 1: Full Pipeline

**Purpose:** Complete end-to-end data collection workflow

**Command:**
```bash
bash scripts/monitoring/data_pipeline_manager.sh full
```

**What it does:**
1. Checks prerequisites (conda env, AWS credentials, disk space)
2. Runs local data inventory (Workflow #45)
3. Runs AWS data inventory (Workflow #47)
4. Analyzes data gaps (Workflow #46)
5. Generates collection plan with recommendations
6. Prompts to launch scraper (if confirmed)
7. Provides monitoring and validation commands

**When to use:**
- First time using the pipeline
- Starting a comprehensive data collection session
- Weekly/monthly data updates
- After major changes to data sources

**Expected output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Checking Prerequisites
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓  Conda environment 'nba-aws' is active
✓  AWS credentials are configured
✓  Database credentials file exists
ℹ  Disk space available in /tmp: 45Gi
✓  All prerequisites satisfied

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Phase 1: Data Inventory (Workflows #45, #47)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Inventory output...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Phase 2: Data Gap Analysis (Workflow #46)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Gap analysis output...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Phase 3: Data Collection Plan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓  Collection plan generated: reports/data_pipeline/collection_plan_20251009_075335.md

[Plan display...]

ℹ  Inventory and gap analysis complete
ℹ  Collection plan generated: see reports/data_pipeline/

Proceed with data collection? (y/n): y

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Phase 4: Execute Data Collection (Workflows #40, #42)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Scraper selection and launch...]

✓  Pipeline complete
```

**Output files:**
- `reports/data_pipeline/pipeline_report_TIMESTAMP.md` - Complete execution log
- `reports/data_pipeline/collection_plan_TIMESTAMP.md` - Generated collection plan

---

### Mode 2: Status Check

**Purpose:** Quick check of current data state without collecting new data

**Command:**
```bash
bash scripts/monitoring/data_pipeline_manager.sh status
```

**What it does:**
1. Checks prerequisites
2. Runs local data inventory
3. Runs AWS data inventory
4. Analyzes data gaps
5. Displays status report

**When to use:**
- Daily status check before starting work
- After scrapers complete (check if gaps filled)
- Before planning data collection
- Quick health check of data infrastructure

**Runtime:** 30-60 seconds

---

### Mode 3: Generate Collection Plan

**Purpose:** Create actionable plan for filling data gaps

**Command:**
```bash
bash scripts/monitoring/data_pipeline_manager.sh plan
```

**What it does:**
1. Runs inventory and gap analysis
2. Generates prioritized collection plan
3. Provides specific scraper commands
4. Estimates runtimes and costs
5. Creates markdown report

**When to use:**
- After status check shows gaps
- Planning weekly/monthly data collection
- Before starting scrapers (want to see plan first)
- Documenting data collection strategy

**Output file:**
- `reports/data_pipeline/collection_plan_TIMESTAMP.md`

**Example plan output:**
```markdown
# NBA Simulator - Data Collection Plan

Generated: 2025-10-09 07:53:35

---

## Identified Gaps

### Critical Gaps (Block Analysis)

**Missing Games by Season:**
 season | missing_games
--------+---------------
   2024 |            41  (season in progress)
   2021 |             5

### S3 Sync Gaps
- 145 files NOT uploaded to S3 (ESPN play-by-play)

---

## Recommended Actions

### Priority 1: Fill Critical Gaps

**If missing recent games (2020-2025):**
```bash
# Run Basketball Reference incremental scraper (2-3 hours)
bash scripts/etl/scrape_bbref_incremental.sh 2020 2025
```

### Priority 2: S3 Sync

**If local files not in S3:**
```bash
# Sync ESPN data to S3
aws s3 sync data/nba_pbp/ s3://nba-sim-raw-data-lake/pbp/
```

---

## Execution Commands

**Launch recommended scraper(s):**
```bash
# Interactive launcher
bash scripts/monitoring/launch_scraper.sh

# Or use pipeline manager
bash scripts/monitoring/data_pipeline_manager.sh collect
```

**Monitor progress:**
```bash
bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 10
```
```

---

### Mode 4: Execute Collection

**Purpose:** Launch scraper to fill identified gaps

**Command:**
```bash
bash scripts/monitoring/data_pipeline_manager.sh collect
```

**What it does:**
1. Checks prerequisites
2. Presents scraper menu with options
3. Launches selected scraper in background
4. Provides monitoring commands

**When to use:**
- After reviewing collection plan
- Ready to start collecting data
- Know which gaps need filling

**Scraper options:**
1. **Basketball Reference (Recent: 2020-2025)** - ~2-3 hours
2. **Basketball Reference (Historical: 2010-2019)** - ~5-7 hours
3. **hoopR Phase 1B (2002-2025)** - ~30-60 minutes
4. **NBA API Comprehensive (1996-2025)** - ~5-6 hours
5. **Skip and use launch_scraper.sh manually**

**Example interaction:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Phase 4: Execute Data Collection (Workflows #40, #42)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ  Available scrapers:
  1. Basketball Reference (Recent: 2020-2025, ~2-3 hours)
  2. Basketball Reference (Historical: 2010-2019, ~5-7 hours)
  3. hoopR Phase 1B (2002-2025, ~30-60 minutes)
  4. NBA API Comprehensive (1996-2025, ~5-6 hours)
  5. Skip and use launch_scraper.sh manually

Select scraper to run (1-5): 1

ℹ  Launching Basketball Reference (Recent)...
✓  Started Basketball Reference scraper (PID: 12345)
ℹ  Monitor: tail -f /tmp/bbref_recent.log

ℹ  Scraper launched in background
ℹ  Monitor progress with: bash scripts/monitoring/monitor_scrapers_inline.sh
ℹ  Check status next session with: Workflow #38 (Overnight Scraper Handoff)
```

**After launching:**
- Use Workflow #39 monitoring tools to track progress
- Use Workflow #38 to check status next session (if overnight)
- Use `validate` mode after completion

---

### Mode 5: Validation

**Purpose:** Verify data quality after scraper completion

**Command:**
```bash
bash scripts/monitoring/data_pipeline_manager.sh validate
```

**What it does:**
1. Checks for scraper output directories
2. Counts output files
3. Validates sample file formats (JSON/CSV)
4. Runs feature engineering readiness test (Workflow #41)
5. Generates validation report

**When to use:**
- After scraper completes
- Before loading data to database
- Before marking data collection as complete
- Part of quality assurance process

**Validation checks:**
- Output directory exists
- File count matches expectations
- Sample files are valid JSON/CSV
- Feature engineering test passes

**Example output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Phase 5: Data Quality Validation (Workflow #41)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ  Running data quality checks...
ℹ  Checking for scraper output directories...
✓  Found 1456 files in /tmp/basketball_reference_incremental
ℹ  Validating sample files from basketball_reference_incremental...
✓  3/3 sample files are valid JSON
ℹ  Running feature engineering readiness test...

[Test output...]

✓  Validation complete
```

---

## Integration with Other Workflows

### Replaces Manual Workflow Sequence

**Before (manual):**
```bash
# 1. Check local data (Workflow #45)
bash scripts/monitoring/inventory_local_data.sh --quick

# 2. Check AWS data (Workflow #47)
bash scripts/monitoring/inventory_aws.sh --quick

# 3. Analyze gaps (Workflow #46)
# ... manual SQL queries ...

# 4. Decide which scraper to run
# ... read scraper docs ...

# 5. Launch scraper (Workflow #40)
bash scripts/etl/scrape_bbref_incremental.sh 2020 2025

# 6. Monitor (Workflow #39)
bash scripts/monitoring/monitor_scrapers_inline.sh

# 7. Validate (Workflow #41)
python notebooks/test_feature_engineering.py
```

**After (integrated):**
```bash
# Single command does all of the above
bash scripts/monitoring/data_pipeline_manager.sh full
```

### Workflow References

**This workflow orchestrates:**
- **Workflow #45:** Local Data Inventory - Phase 1
- **Workflow #46:** Data Gap Analysis - Phase 2
- **Workflow #47:** AWS Data Inventory - Phase 1
- **Workflow #40:** Scraper Operations - Phase 4
- **Workflow #42:** Scraper Management - Phase 4
- **Workflow #41:** Testing Framework - Phase 5

**This workflow complements:**
- **Workflow #38:** Overnight Scraper Handoff - Use after leaving scrapers overnight
- **Workflow #39:** Scraper Monitoring - Live monitoring during execution
- **Workflow #1:** Session Start - Can be integrated into session initialization

---

## Use Cases

### Use Case 1: Weekly Data Update

**Scenario:** It's Monday, need to collect last week's games

**Command:**
```bash
bash scripts/monitoring/data_pipeline_manager.sh full
```

**Flow:**
1. Pipeline checks data state
2. Identifies 7 days of missing games (2024 season)
3. Recommends Basketball Reference recent scraper
4. User confirms, scraper launches
5. 15 minutes later, validation confirms data collected

**Result:** Week's worth of data collected and validated in < 30 minutes

---

### Use Case 2: Comprehensive Gap Filling

**Scenario:** Database shows multiple seasons with missing data

**Command:**
```bash
# 1. Generate plan first
bash scripts/monitoring/data_pipeline_manager.sh plan

# 2. Review plan, decide on strategy
cat reports/data_pipeline/collection_plan_*.md

# 3. Execute in priority order
bash scripts/monitoring/data_pipeline_manager.sh collect  # Recent seasons
# Wait for completion, then:
bash scripts/monitoring/data_pipeline_manager.sh collect  # Historical seasons
```

**Flow:**
1. Plan shows gaps in 2018-2024 (multiple seasons)
2. User decides to fill recent first (2020-2024), then historical
3. Launches recent scraper (3 hours)
4. Validates, then launches historical (5 hours)
5. Both complete, all gaps filled

**Result:** 8 hours of scraping, but split into manageable chunks

---

### Use Case 3: Quality Assurance Before Analysis

**Scenario:** About to run ML training, need to verify data completeness

**Command:**
```bash
bash scripts/monitoring/data_pipeline_manager.sh status
```

**Flow:**
1. Status check shows 98.5% game coverage
2. Identifies 15 games missing from 2024 season
3. Shows S3 sync is current
4. User decides 98.5% is sufficient, proceeds with analysis

**Result:** Quick confidence check before proceeding

---

### Use Case 4: Overnight Scraper Setup

**Scenario:** Friday evening, want to collect all historical data over weekend

**Command:**
```bash
# Friday 5 PM
bash scripts/monitoring/data_pipeline_manager.sh full

# Select option 2: Basketball Reference Historical (5-7 hours)
# Leaves computer running over weekend

# Monday morning
# Follow Workflow #38: Overnight Scraper Handoff Protocol
bash scripts/monitoring/data_pipeline_manager.sh validate
```

**Flow:**
1. Friday: Launch long-running scraper
2. Pipeline provides monitoring commands
3. Weekend: Scraper runs unattended
4. Monday: Validate results, load to database

**Result:** Maximize compute time, minimal hands-on effort

---

## Best Practices

### When to Run Each Mode

**Daily (5 minutes):**
```bash
# Quick status check
bash scripts/monitoring/data_pipeline_manager.sh status
```

**Weekly (30 minutes):**
```bash
# Full update pipeline
bash scripts/monitoring/data_pipeline_manager.sh full
```

**Monthly (as needed):**
```bash
# Comprehensive gap filling
bash scripts/monitoring/data_pipeline_manager.sh plan
# Review plan, then execute in stages
```

**After Every Scraper Run:**
```bash
# Always validate
bash scripts/monitoring/data_pipeline_manager.sh validate
```

### Pipeline Optimization Tips

**1. Run status checks frequently**
- Fast operation (<1 minute)
- Catches issues early
- Informs planning decisions

**2. Generate plans before long scrapes**
- Prevents wasted runtime
- Ensures you're collecting right data
- Helps prioritize gaps

**3. Validate immediately after collection**
- Catches scraper errors early
- Prevents corrupt data loading
- Saves time on re-runs

**4. Use mode chaining for complex workflows**
```bash
# Example: Status → Plan → Collect → Validate
bash scripts/monitoring/data_pipeline_manager.sh status > status.log
bash scripts/monitoring/data_pipeline_manager.sh plan > plan.log
# Review plan, then:
bash scripts/monitoring/data_pipeline_manager.sh collect
# After completion:
bash scripts/monitoring/data_pipeline_manager.sh validate
```

---

## Output Files and Reports

### Generated Reports

**Location:** `reports/data_pipeline/`

**Files created:**
1. `pipeline_report_TIMESTAMP.md` - Complete execution log
2. `collection_plan_TIMESTAMP.md` - Generated collection plan
3. `validation_report_TIMESTAMP.md` - Validation results (future)

**Report retention:**
- Keep reports for 30 days
- Archive old reports monthly
- Use for debugging and auditing

---

## Troubleshooting

### Issue: Prerequisites check fails

**Error:** "Conda environment 'nba-aws' is NOT active"

**Solution:**
```bash
conda activate nba-aws
bash scripts/monitoring/data_pipeline_manager.sh full
```

---

### Issue: No gaps identified but data clearly missing

**Cause:** Database credentials not available

**Solution:**
```bash
# Verify credentials file exists
ls -l /Users/ryanranft/nba-sim-credentials.env

# Source manually and test
source /Users/ryanranft/nba-sim-credentials.env
psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME?sslmode=require" -c "SELECT COUNT(*) FROM games;"

# If works, re-run pipeline
bash scripts/monitoring/data_pipeline_manager.sh status
```

---

### Issue: Validation shows scraper output not found

**Cause:** Scraper may still be running or failed

**Solution:**
```bash
# Check if scraper is still running
ps aux | grep scrape

# Check log file for errors
tail -100 /tmp/bbref_recent.log

# If failed, review Workflow #42 for scraper-specific troubleshooting
```

---

### Issue: Pipeline runs but produces no plan

**Cause:** No gaps identified (data is complete)

**Result:** This is success! No collection needed.

**Confirmation:**
```bash
# Verify completeness
bash scripts/monitoring/data_pipeline_manager.sh status
# Should show high coverage percentages
```

---

## Success Criteria

✅ Can run full pipeline in single command
✅ Inventory completes in < 60 seconds
✅ Gap analysis identifies missing data accurately
✅ Collection plan provides actionable recommendations
✅ Scraper launches successfully in background
✅ Validation detects data quality issues
✅ Reports generated in `reports/data_pipeline/`
✅ Integrates seamlessly with existing workflows

---

## Related Documentation

- **Script:** `scripts/monitoring/data_pipeline_manager.sh`
- **Workflow #45:** Local Data Inventory System
- **Workflow #46:** Data Gap Analysis & Remediation
- **Workflow #47:** AWS Data Inventory System
- **Workflow #40:** Complete Scraper Operations Guide
- **Workflow #42:** Scraper Management & Execution
- **Workflow #38:** Overnight Scraper Handoff Protocol
- **Workflow #39:** Scraper Monitoring Automation
- **Workflow #41:** Testing Framework

---

**Last Updated:** October 9, 2025
**Status:** ✅ Active
**Script Version:** 1.0
**Next Review:** Monthly (or when scrapers change)
# Workflow #40: Complete Scraper Operations Guide

**Status:** Active
**Category:** Data Collection
**Prerequisites:** Conda environment active, AWS credentials configured
**Related Workflows:**
- Workflow #38: [Overnight Scraper Handoff Protocol](38_overnight_scraper_handoff.md)
- Workflow #39: [Scraper Monitoring Automation](39_scraper_monitoring_automation.md)

---

## Purpose

This workflow provides end-to-end guidance for all scraper operations, from launching new scrapes to monitoring progress to handling completion. It consolidates scraper management into a single reference point.

---

## Quick Reference

### Starting Scrapers

**Option 1: Interactive Launcher (Recommended)**
```bash
bash scripts/monitoring/launch_scraper.sh
```

**Option 2: Direct Commands**
```bash
# Basketball Reference (recent seasons)
bash scripts/etl/scrape_bbref_incremental.sh 2020 2025

# Basketball Reference (historical)
bash scripts/etl/scrape_bbref_incremental.sh 2010 2019

# hoopR Phase 1B (league dashboards)
bash scripts/etl/run_hoopr_phase1b.sh

# NBA API (comprehensive)
bash scripts/etl/overnight_nba_api_comprehensive.sh

# SportsDataverse
python scripts/etl/scrape_sportsdataverse.py

# Kaggle datasets
python scripts/etl/download_kaggle_basketball.py
```

### Monitoring Scrapers

**Quick Status Check**
```bash
bash scripts/monitoring/monitor_scrapers_inline.sh
```

**Live Tracking in Conversation**
```bash
bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 10
```

**Full-Screen Dashboard**
```bash
bash scripts/monitoring/monitor_scrapers.sh --watch
```

### Checking Progress

**Completion Markers**
```bash
# Basketball Reference
ls /tmp/basketball_reference_incremental/*.complete | wc -l

# Output files
find /tmp/hoopr_phase1 -name "*.csv" | wc -l
```

**Log Files**
```bash
# Basketball Reference
tail -f /tmp/bbref_incremental_2020-2025.log

# hoopR
tail -f /tmp/hoopr_phase1b.log

# NBA API
tail -f /tmp/nba_api_comprehensive.log
```

### Stopping Scrapers

**Find Running Scrapers**
```bash
ps aux | grep -E "(scrape_|run_hoopr)" | grep -v grep
```

**Kill Specific Scraper**
```bash
kill <PID>
```

**Kill All Scrapers (Use with Caution)**
```bash
pkill -f "scrape_"
```

---

## Complete Operation Flow

### Phase 1: Pre-Launch Checks

**1. Verify Environment**
```bash
# Check conda environment
conda info --envs | grep nba-aws

# Activate if needed
conda activate nba-aws

# Check AWS credentials
aws s3 ls s3://nba-sim-raw-data-lake/
```

**2. Check Disk Space**
```bash
df -h /tmp
```

**3. Review Rate Limit Settings**

See `docs/SCRAPER_MANAGEMENT.md` for current rate limits:
- Basketball Reference: 5 seconds (tested, stable)
- NBA API: 0.6 seconds (600ms, official limit)
- hoopR: Managed by library (no manual setting)

**4. Choose Scraper Strategy**

**Decision Tree:**

- **Need comprehensive historical data (1950+)?** → Basketball Reference
- **Need modern advanced stats (2013+)?** → hoopR Phase 1B
- **Need official NBA.com stats?** → NBA API (⚠️ currently has error rate issues)
- **First time scraping?** → Start with recent seasons (2020-2025) for faster validation

**Can Run Simultaneously:**
- ✅ Basketball Reference + hoopR (different APIs)
- ✅ Any scraper + monitoring tools

**Avoid Running Together:**
- ❌ Multiple Basketball Reference instances (rate limit conflicts)
- ❌ NBA API + other stats.nba.com scrapers

---

### Phase 2: Launch Scraper

**Option 1: Interactive Launcher (Recommended)**

```bash
bash scripts/monitoring/launch_scraper.sh
```

Follow prompts:
1. Select scraper from menu
2. Choose season range (if applicable)
3. Confirm launch
4. Scraper starts in background with automatic monitoring

**Option 2: Manual Launch**

```bash
# Basketball Reference (with nohup)
nohup bash scripts/etl/scrape_bbref_incremental.sh 2020 2025 > /tmp/bbref.log 2>&1 &
echo "PID: $!"

# hoopR Phase 1B
nohup bash scripts/etl/run_hoopr_phase1b.sh > /tmp/hoopr.log 2>&1 &
echo "PID: $!"
```

**Verify Launch**
```bash
# Check process is running
ps aux | grep scrape | grep -v grep

# Check log is being written
tail -20 /tmp/bbref_incremental_2020-2025.log
```

---

### Phase 3: Monitor Progress

**First 15 Minutes (Critical Period)**

Watch for:
- ✅ First successful requests
- ✅ Log file updating regularly
- ⚠️ Rate limit errors (should be zero for Basketball Reference at 5s)
- ⚠️ Connection errors

```bash
# Watch live
bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 3 --interval 300
```

**During Long Runs**

Check every 30-60 minutes:

```bash
# Quick status
bash scripts/monitoring/monitor_scrapers_inline.sh
```

Look for:
- ✅ Progress advancing (seasons/tasks completing)
- ✅ Error count staying low (< 5%)
- ✅ Log files updating recently
- ⚠️ Process still running

**Overnight Monitoring**

Before leaving:
1. Verify scraper is progressing
2. Check error count is acceptable
3. Note current progress for morning comparison
4. Leave monitoring dashboard running (optional)

```bash
# Optional: Start continuous monitor in separate terminal
bash scripts/monitoring/monitor_scrapers.sh --watch
```

Next morning:
- Follow **Workflow #38: Overnight Scraper Handoff Protocol**

---

### Phase 4: Handle Issues

**Scraper Stalled (No Progress)**

```bash
# Check if process is actually running
ps aux | grep <PID>

# Check last log update time
ls -lh /tmp/bbref_incremental_2020-2025.log

# Look for hung requests
tail -50 /tmp/bbref_incremental_2020-2025.log | grep -i "timeout\|hang\|waiting"
```

**Resolution:**
1. Wait 5-10 minutes (may be slow request)
2. If truly stalled, kill and restart
3. Incremental scraper will resume from last completion marker

**High Error Rate**

```bash
# Count errors
grep -c -i "error\|failed" /tmp/scraper.log

# See recent errors
grep -i "error\|failed" /tmp/scraper.log | tail -20

# Check error types
grep "429" /tmp/scraper.log  # Rate limit
grep "timeout" /tmp/scraper.log  # Connection issues
grep "404" /tmp/scraper.log  # Missing data
```

**Resolution by Error Type:**
- **429 errors:** Increase rate limit (already at 5s for Basketball Reference - if still seeing 429s, stop and investigate)
- **Timeout errors:** Check internet connection, consider retry logic improvements
- **404 errors:** Expected for some seasons (data doesn't exist)

**Scraper Won't Start**

```bash
# Check Python/R environment
conda activate nba-aws

# Check script permissions
ls -l scripts/etl/scrape_*.sh

# Check log directory exists
mkdir -p /tmp/basketball_reference_incremental
mkdir -p /tmp/hoopr_phase1

# Check S3 credentials
aws s3 ls s3://nba-sim-raw-data-lake/
```

---

### Phase 5: Verify Completion

**Check Final Status**

```bash
# Basketball Reference completion markers
ls /tmp/basketball_reference_incremental/*.complete

# hoopR CSV files
find /tmp/hoopr_phase1 -name "*.csv" | wc -l

# Check log for completion message
tail -50 /tmp/bbref_incremental_2020-2025.log | grep -i "complete"
```

**Verify S3 Upload**

```bash
# Basketball Reference
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive

# hoopR
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_phase1/ --recursive

# Count files
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | wc -l
```

**Validate Data Quality**

```bash
# Check file sizes (should not be empty or suspiciously small)
ls -lh /tmp/basketball_reference_incremental/*.json

# Spot check JSON structure
head -20 /tmp/basketball_reference_incremental/schedules_2023.json
```

---

### Phase 6: Document Results

**Update PROGRESS.md**

If scraper completed a major milestone:
1. Update relevant phase status
2. Note data collection completion
3. Add any issues encountered

**Log to COMMAND_LOG.md** (Workflow #2)

```markdown
**Scraper: Basketball Reference Incremental (2020-2025)**
**Status:** ✅ Complete
**Duration:** 2h 15m
**Seasons Scraped:** 2020, 2021, 2022, 2023, 2024, 2025
**Data Types:** 7 per season (42 total files)
**S3 Upload:** ✅ Verified
**Errors:** 0
**Notes:** Rate limit at 5s worked perfectly, no 429 errors
```

**Create Session Notes** (if significant)

For major scraping operations, document:
- What was scraped
- Any issues encountered
- Rate limit effectiveness
- S3 upload success
- Data quality observations
- Recommendations for next scrape

---

## Scraper-Specific Details

### Basketball Reference

**Data Types (7 per season):**
1. Schedules
2. Season totals (player stats)
3. Advanced totals
4. Standings
5. Player box scores
6. Team box scores
7. Play-by-play (2000+ only)

**Rate Limit:** 5 seconds (tested stable, 0 errors)

**Resume Capability:** Yes (completion markers: `.complete` files)

**Expected Runtimes:**
- Recent seasons (2020-2025): ~2-3 hours
- 10-year range: ~5-7 hours
- Full historical (1950-2025): ~15-20 hours

**Incremental Strategy:**
- Run recent first (2020-2025)
- Validate data quality
- Expand to earlier years
- Use completion markers for resume

### hoopR

**Data Types:**
- League player stats (per season)
- League team stats (per season)
- Standings
- 5-man lineups (2008+)
- Player tracking stats (2014+)
- Hustle stats (2016+)

**Coverage:** 2002-2025 (24 seasons)

**Rate Limit:** Managed by hoopR library (no manual setting)

**Output Format:** CSV files

**Expected Runtime:** 30-60 minutes for all 24 seasons

**S3 Path:** `s3://nba-sim-raw-data-lake/hoopr_phase1/`

### NBA API

**Status:** ⚠️ High error rate - needs improvement

**Data Types:**
- Advanced box scores
- Player tracking
- Shot charts
- Shot locations

**Coverage:** 1996-2025 (30 seasons)

**Rate Limit:** 0.6 seconds (600ms, official NBA.com limit)

**Known Issues:**
- Connection timeouts
- Remote disconnects
- 50-70% error rate in testing

**Recommendation:** Wait until error handling is improved

### SportsDataverse

**Coverage:** 2002+ seasons

**Status:** Implemented but not actively used

**Use Case:** Supplementary data source

### Kaggle

**Coverage:** Pre-packaged historical datasets

**Status:** Downloaded and archived

**Use Case:** One-time download for historical data

---

## Integration with Other Workflows

**Workflow #38: Overnight Scraper Handoff Protocol**
- Use after leaving scrapers running overnight
- Documents how to check status next morning
- Handles success/failure scenarios

**Workflow #39: Scraper Monitoring Automation**
- Detailed monitoring tool documentation
- Usage examples for inline vs dashboard monitoring
- Monitoring tool comparison

**Workflow #1: Session Start**
- Checks for overnight scraper jobs at session start
- Integrates scraper status into session initialization

**Workflow #14: Session End**
- Documents scraper status before ending session
- Notes any scrapers left running overnight

---

## Automation Considerations

**What's Automated:**
- ✅ Incremental scraping (resume capability)
- ✅ S3 upload after completion
- ✅ Completion marker creation
- ✅ Exponential backoff on errors
- ✅ Log file creation and rotation

**What Requires Manual Steps:**
- ⚠️ Starting scrapers (use `launch_scraper.sh`)
- ⚠️ Monitoring progress (run monitoring tools)
- ⚠️ Handling failures (check logs, restart if needed)
- ⚠️ Data validation (spot check output)
- ⚠️ Documenting results (update PROGRESS.md)

**Future Automation Opportunities:**
1. Scheduled cron jobs for regular scraping
2. Auto-restart on failure (with max retry limit)
3. Slack/email notifications on completion
4. Automated data quality validation
5. S3 sync verification (compare local vs cloud)

---

## Best Practices Checklist

**Before Starting:**
- [ ] Check internet connection stability
- [ ] Verify S3 credentials (`aws s3 ls`)
- [ ] Ensure conda environment activated
- [ ] Check disk space (`df -h /tmp`)
- [ ] Review rate limit settings
- [ ] Start with recent seasons first (for testing)

**While Running:**
- [ ] Monitor progress every 30-60 minutes
- [ ] Check error counts (should be low)
- [ ] Verify log files updating
- [ ] Watch for 429 rate limit errors
- [ ] Ensure S3 uploads completing

**After Completion:**
- [ ] Verify completion markers created
- [ ] Check S3 upload success
- [ ] Count output files
- [ ] Review error log summary
- [ ] Spot check data quality
- [ ] Document any issues encountered
- [ ] Update PROGRESS.md if major milestone

---

## Troubleshooting Quick Reference

| Symptom | Check | Resolution |
|---------|-------|------------|
| Scraper won't start | Environment, credentials, permissions | Activate conda, check AWS, chmod scripts |
| 429 rate limit errors | Current rate limit setting | Increase to 5s, verify backoff logic |
| Process not running | `ps aux \| grep scrape` | Restart with nohup |
| Log not updating | Last modified time | Check if stalled, may need restart |
| High error rate (>10%) | Error types in log | Address by error type (timeout, 404, etc.) |
| No completion markers | Directory permissions | Check `/tmp/basketball_reference_incremental/` permissions |
| S3 upload failed | AWS credentials, network | Re-upload manually: `aws s3 sync` |

---

## Related Documentation

- **Central Hub:** `docs/SCRAPER_MANAGEMENT.md` - Complete scraper reference
- **Data Sources:** `docs/DATA_SOURCES.md` - All 5 data source details
- **Test Results:** `docs/archive/scraper_reports/SCRAPER_TEST_RESULTS.md` - Rate limit testing outcomes

---

*Last updated: October 8, 2025*
*Created: October 8, 2025*
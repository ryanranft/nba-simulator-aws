# Workflow #42: Scraper Management & Execution

**Purpose:** Execute and manage multi-source scrapers for NBA data collection

**When to use:**
- Before data load operations (need fresh data)
- During data validation phases (verify completeness)
- Periodic data updates (fill gaps, update current season)
- Overnight scraping operations (long-running jobs)

---

## Overview

This workflow provides procedures for executing, monitoring, and troubleshooting 5 data scrapers that collect NBA data from multiple sources. Each scraper serves a specific purpose in the multi-source data strategy.

**Related workflows:**
- Workflow #38: Overnight Scraper Handoff Protocol (checking completion status)
- Workflow #41: Testing Framework (validating scraper output)

---

## Scraper Registry

### Quick Reference Table

| Scraper | Runtime | Rate Limit | Coverage | Status | Priority |
|---------|---------|------------|----------|--------|----------|
| **NBA API Comprehensive** | 5-6 hrs | 600ms | 1996-2025 (30 seasons) | ✅ Active | High |
| **hoopR Phase 1** | 30 min | None | 2002-2025 (24 seasons) | ✅ Active | High |
| **Basketball Reference** | 30 hrs | 3.5s | 1946-present | ✅ Active | Medium |
| **Kaggle Database** | 10 min | N/A | 1946-2024 | ✅ Active | Low |
| **ESPN Gap Filler** | 2-3 hrs | None | 2022-2025 | ⏸️ As needed | Low |

---

## Scraper 1: NBA API Comprehensive Scraper

### Purpose
Collect advanced statistics, player tracking, and detailed game data from NBA.com Stats API. Provides 60-80 advanced features beyond ESPN data.

### Location
```bash
scripts/etl/scrape_nba_api_comprehensive.py
scripts/etl/overnight_nba_api_comprehensive.sh
```

### Coverage
- **Date range:** 1996-2025 (30 seasons)
- **Endpoints:** 24 endpoints across 3 tiers
  - Tier 1: Advanced box scores (8), player tracking (4), league dashboards (7)
  - Tier 2: Hustle stats (2), synergy (1), shot charts (1), draft (2)
- **Data availability windows:**
  - 2016-2025: All tracking + hustle + synergy (full feature set)
  - 2014-2015: Tracking only (no hustle/synergy)
  - 2013-earlier: Box scores and dashboards only

### Rate Limiting
- **Delay:** 600ms between API calls
- **Rate:** ~1.67 requests per second
- **Enforcement:** Built into `_rate_limit()` method

### Usage

**Standard execution (overnight):**
```bash
nohup bash scripts/etl/overnight_nba_api_comprehensive.sh > /tmp/nba_api_comprehensive.log 2>&1 &
echo "Started NBA API scraper (PID: $!)"
```

**Monitor progress:**
```bash
# Watch log file
tail -f /tmp/nba_api_comprehensive.log

# Check output file count (updates every few seconds)
watch -n 5 'find /tmp/nba_api_comprehensive/ -type f | wc -l'

# Check for errors
grep -i "error" /tmp/nba_api_comprehensive.log | wc -l
```

**Expected output:**
- **Location:** `/tmp/nba_api_comprehensive/`
- **File structure:** `[endpoint]/[season]/[game_id or player_id].json`
- **Total files:** ~366,486 files (30 seasons × ~12,216 files/season)
- **Total size:** ~50-75 GB

**Runtime:** 5-6 hours for 30 seasons

### Common Failures

#### Failure 1: Missing Team ID (Player Tracking Endpoints)

**Symptom:**
```
400 Client Error: Bad Request
Missing required parameter: team_id
```

**Cause:** Player tracking endpoints require `team_id` parameter

**Fix:** Scraper now includes team_id lookup from roster data (fixed Oct 7, 2025)

**Recovery:**
```bash
# Check progress before stopping
find /tmp/nba_api_comprehensive/ -type f | wc -l

# Stop failed process
ps aux | grep scrape_nba_api_comprehensive
kill -9 [PID]

# Restart (will skip existing files)
bash scripts/etl/overnight_nba_api_comprehensive.sh
```

#### Failure 2: Rate Limit Exceeded

**Symptom:**
```
429 Too Many Requests
Rate limit exceeded
```

**Recovery:**
```bash
# Wait 5 minutes for cooldown
sleep 300

# Restart scraper (will resume where it left off)
bash scripts/etl/overnight_nba_api_comprehensive.sh
```

**Prevention:** 600ms delay already enforced (1.67 req/sec)

#### Failure 3: Network Timeout

**Symptom:**
```
requests.exceptions.ConnectionError: Connection timeout
```

**Recovery:**
```bash
# Check network
ping stats.nba.com

# If network OK, restart immediately
bash scripts/etl/overnight_nba_api_comprehensive.sh
```

**Auto-recovery:** Scraper skips existing files, safe to restart anytime

### Validation

**After completion:**
```bash
# 1. Check process exited cleanly
echo $?  # Should be 0

# 2. Count output files
find /tmp/nba_api_comprehensive/ -type f | wc -l
# Expected: ~366,486 files (or proportional to seasons scraped)

# 3. Check for errors
grep -i "error\|exception" /tmp/nba_api_comprehensive.log

# 4. Validate sample JSON files
python -m json.tool /tmp/nba_api_comprehensive/boxscoreadvancedv2/2023/0022300001.json

# 5. Upload to S3
aws s3 sync /tmp/nba_api_comprehensive/ s3://nba-sim-raw-data-lake/nba_api_comprehensive/

# 6. Verify S3 upload
aws s3 ls s3://nba-sim-raw-data-lake/nba_api_comprehensive/ --recursive | wc -l
```

### When to Run
- **Initial setup:** Once to collect all historical data (5-6 hours)
- **Daily updates:** During season (5-10 minutes for yesterday's games)
- **Gap filling:** After identifying missing data
- **Validation:** Before data load operations

---

## Scraper 2: hoopR Scraper (R-based)

### Purpose
Bulk collection of play-by-play, box scores, schedule, and team stats using `sportsdataverse` R package. Fastest scraper for bulk historical data.

### Location
```bash
scripts/etl/scrape_hoopr_phase1_foundation.R
scripts/etl/scrape_hoopr_phase1b_only.R
scripts/etl/run_hoopr_phase1.sh
scripts/etl/run_hoopr_phase1b.sh
```

### Coverage
- **Date range:** 2002-2025 (24 seasons)
- **Phase 1A (Bulk Loaders):**
  - Play-by-play: 13.9M events
  - Player box scores: 810K rows
  - Team box scores: 63K rows
  - Schedule: 31K games
- **Phase 1B (League Dashboards):**
  - Player stats, team stats, standings
  - Note: Lineups, player tracking, hustle not available pre-2013

### Rate Limiting
None (bulk download functions)

### Usage

**Phase 1A (Bulk loaders):**
```bash
bash scripts/etl/run_hoopr_phase1.sh
```

**Phase 1B (League dashboards):**
```bash
nohup bash scripts/etl/run_hoopr_phase1b.sh > /tmp/hoopr_phase1b.log 2>&1 &
echo "Started hoopR Phase 1B (PID: $!)"
```

**Monitor progress:**
```bash
# Watch log file
tail -f /tmp/hoopr_phase1b_runner.log

# Check output files
ls -lh /tmp/hoopr_phase1b/

# Check for errors
grep -i "error" /tmp/hoopr_phase1b_runner.log
```

**Expected output:**
- **Location:** `/tmp/hoopr_phase1/` and `/tmp/hoopr_phase1b/`
- **Format:** CSV files (easier to load than JSON)
- **Phase 1A:** 96 CSV files, 2.5 GB
- **Phase 1B:** ~50 CSV files per season, ~500 MB/season

**Runtime:**
- Phase 1A: 30 seconds
- Phase 1B: 30-60 minutes (24 seasons)

### Common Failures

#### Failure 1: Memory Error (Large Datasets)

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Cause:** Loading 30 seasons at once (600K+ rows)

**Recovery:**
```bash
# Process in smaller batches
Rscript scripts/etl/scrape_hoopr_phase1_foundation.R --seasons 2002:2010
Rscript scripts/etl/scrape_hoopr_phase1_foundation.R --seasons 2011:2018
Rscript scripts/etl/scrape_hoopr_phase1_foundation.R --seasons 2019:2025
```

#### Failure 2: sportsdataverse Package Error

**Symptom:**
```
Error in library(sportsdataverse) : there is no package called 'sportsdataverse'
```

**Recovery:**
```r
# Install in R console
install.packages("sportsdataverse")
install.packages("hoopR")
```

#### Failure 3: save_csv List Handling Error

**Symptom:**
```
Error in write.csv: invalid 'x' type 'list'
```

**Cause:** hoopR returns lists instead of data frames

**Fix:** Updated `save_csv()` function to extract data frames (fixed Oct 7, 2025)

### Validation

**After completion:**
```bash
# 1. Check output files
ls /tmp/hoopr_phase1/ | wc -l   # Expected: 96 files
ls /tmp/hoopr_phase1b/ | wc -l  # Expected: ~50 files/season

# 2. Check CSV validity (sample)
head -10 /tmp/hoopr_phase1/pbp_2020.csv

# 3. Check row counts
wc -l /tmp/hoopr_phase1/pbp_*.csv

# 4. Upload to S3
aws s3 sync /tmp/hoopr_phase1/ s3://nba-sim-raw-data-lake/hoopr_phase1/
aws s3 sync /tmp/hoopr_phase1b/ s3://nba-sim-raw-data-lake/hoopr_phase1b/

# 5. Clean up
rm -rf /tmp/hoopr_phase1/ /tmp/hoopr_phase1b/
```

### When to Run
- **Initial setup:** Once for all historical data (30-60 minutes)
- **Season start:** Update for current season
- **Gap filling:** Missing ESPN play-by-play data

---

## Scraper 3: Basketball Reference Scraper

### Purpose
Collect advanced statistics (PER, Win Shares, BPM, Four Factors) and historical data not available from other sources. Gold standard for historical NBA data.

### Location
```bash
scripts/etl/scrape_basketball_reference_complete.py
scripts/etl/scrape_bbref_incremental.sh
scripts/etl/overnight_basketball_reference_comprehensive.sh
```

### Coverage
- **Date range:** 1946-present (complete BAA/NBA history)
- **Data types:**
  - Game logs and box scores
  - Advanced metrics (PER, WS, BPM, TS%, eFG%)
  - Team statistics and Four Factors
  - Player career statistics

### Rate Limiting
- **Delay:** 3.5 seconds between requests
- **Rate:** ~0.29 requests per second
- **Enforcement:** TOS compliance (3 seconds minimum)
- **Critical:** Never reduce below 3 seconds (risk permanent ban)

### Usage

**Incremental scraper (2020-2025 only):**
```bash
nohup bash scripts/etl/scrape_bbref_incremental.sh 2020 2025 > /tmp/bbref_incremental_2020-2025.log 2>&1 &
echo "Started Basketball Reference incremental scraper (PID: $!)"
```

**Full historical scraper (1946-present):**
```bash
nohup bash scripts/etl/overnight_basketball_reference_comprehensive.sh > /tmp/bbref_comprehensive.log 2>&1 &
echo "Started Basketball Reference comprehensive scraper (PID: $!)"
```

**Monitor progress:**
```bash
# Watch log file
tail -f /tmp/bbref_incremental_2020-2025.log

# Check completion markers
ls /tmp/basketball_reference_incremental/*.complete | wc -l

# Check output files
ls /tmp/basketball_reference_incremental/ | wc -l
```

**Expected output:**
- **Location:** `/tmp/basketball_reference_incremental/`
- **Format:** JSON files
- **Files per season:** ~1,230 games + ~500 player stats
- **Total size:** ~2-3 GB per season

**Runtime:**
- **Incremental (6 seasons):** 3-4 hours
- **Full historical (79 seasons):** ~30 hours

### Common Failures

#### Failure 1: Rate Limit Block (HTTP 429)

**Symptom:**
```
429 Too Many Requests
Your IP has been temporarily blocked
```

**Cause:** Scraped too fast (violated TOS rate limit)

**Recovery:**
```bash
# STOP IMMEDIATELY to avoid permanent ban
kill -9 [PID]

# Wait 24 hours before resuming

# Resume after cooldown
bash scripts/etl/scrape_bbref_incremental.sh 2020 2025
```

**Prevention:**
- Never reduce `time.sleep(3.5)` below 3 seconds
- Monitor for 429 errors in logs
- Stop immediately if blocked

#### Failure 2: HTML Structure Changed

**Symptom:**
```
IndexError: list index out of range
No table found with id='schedule'
```

**Cause:** Basketball Reference changed HTML structure

**Recovery:**
```bash
# Inspect current HTML
curl "https://www.basketball-reference.com/leagues/NBA_2024_games.html" > test.html

# Check table IDs
grep "id=" test.html | grep "table"

# Update scraper with new table ID
# Edit scrape_basketball_reference_complete.py
```

### Validation

**After completion:**
```bash
# 1. Check completion markers
ls /tmp/basketball_reference_incremental/*.complete | wc -l

# 2. Check output files
ls /tmp/basketball_reference_incremental/ | wc -l

# 3. Validate JSON
python -m json.tool /tmp/basketball_reference_incremental/game_2024_001.json

# 4. Upload to S3
aws s3 sync /tmp/basketball_reference_incremental/ s3://nba-sim-raw-data-lake/basketball_reference/

# 5. Clean up
rm -rf /tmp/basketball_reference_incremental/
```

### When to Run
- **Initial setup:** Once for historical data (30 hours)
- **Weekly:** During season for current games (1-2 hours)
- **Advanced stats:** When ESPN data lacks advanced metrics
- **Historical validation:** Cross-check ESPN/Kaggle data

---

## Scraper 4: Kaggle Database Download

### Purpose
One-time download of comprehensive SQLite database with NBA data from 1946-present. Provides historical data completeness and validation source.

### Location
```bash
scripts/etl/download_kaggle_basketball.py
```

### Coverage
- **Date range:** 1946-2024 (historical completeness)
- **Database size:** 2-5 GB
- **Update frequency:** Monthly/seasonal
- **Tables:** Games, players, teams, team_game_stats, player_game_stats, and more

### Prerequisites
```bash
# Install Kaggle CLI
pip install kaggle

# Configure API token (see docs/KAGGLE_API_SETUP.md)
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
```

### Usage

**Download database:**
```bash
python scripts/etl/download_kaggle_basketball.py
```

**Monitor progress:**
```bash
# Check download status
ls -lh ~/.kaggle/datasets/wyattowalsh/basketball/

# Check extraction
ls -lh /tmp/kaggle_basketball/
```

**Expected output:**
- **Location:** `~/.kaggle/datasets/wyattowalsh/basketball/`
- **Format:** SQLite database file (.sqlite or .db)
- **Size:** 2-5 GB
- **Tables:** 20+ tables with game, player, team data

**Runtime:** 10-15 minutes (depends on network speed)

### Common Failures

#### Failure 1: Authentication Error

**Symptom:**
```
401 Unauthorized: You must be authenticated
```

**Cause:** Missing or expired Kaggle API token

**Recovery:**
```bash
# Re-download token from Kaggle account settings
# https://www.kaggle.com/[username]/account

# Save to correct location
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Retry download
python scripts/etl/download_kaggle_basketball.py
```

**See:** `docs/KAGGLE_API_SETUP.md` for detailed token setup

#### Failure 2: Disk Space Full

**Symptom:**
```
OSError: [Errno 28] No space left on device
```

**Cause:** Database is 2-5 GB, need 10+ GB free space

**Recovery:**
```bash
# Check disk space
df -h

# Clean up temp files
rm -rf /tmp/nba_*

# Retry download
python scripts/etl/download_kaggle_basketball.py
```

### Validation

**After download:**
```bash
# 1. Check file exists
ls -lh ~/.kaggle/datasets/wyattowalsh/basketball/*.sqlite

# 2. Query database (sample)
sqlite3 ~/.kaggle/datasets/wyattowalsh/basketball/basketball.sqlite "SELECT COUNT(*) FROM game;"

# 3. List all tables
sqlite3 ~/.kaggle/datasets/wyattowalsh/basketball/basketball.sqlite ".tables"
```

### When to Run
- **Initial setup:** Once to download historical data (10-15 minutes)
- **Monthly:** Check for updates during season
- **Validation:** Before cross-source validation operations

---

## Scraper 5: ESPN Gap Filler

### Purpose
Fill gaps in ESPN data (2022-2025) where files are empty or missing. Complements existing S3 bucket data.

### Location
```bash
scripts/etl/scrape_missing_espn_data.py
scripts/etl/run_espn_scraper.sh
```

### Coverage
- **Date range:** 2022-2025 (recent seasons)
- **Target:** Empty/missing files in S3 bucket
- **Data types:** Schedule, play-by-play, box scores

### Rate Limiting
None (ESPN API has no rate limits)

### Usage

**Standard execution:**
```bash
bash scripts/etl/run_espn_scraper.sh
```

**Overnight execution:**
```bash
nohup bash scripts/etl/run_espn_scraper.sh > /tmp/espn_gap_filler.log 2>&1 &
echo "Started ESPN gap filler (PID: $!)"
```

**Monitor progress:**
```bash
# Watch log
tail -f /tmp/espn_gap_filler.log

# Check output
ls /tmp/espn_missing/ | wc -l
```

**Expected output:**
- **Location:** `/tmp/espn_missing/`
- **Format:** JSON files
- **File count:** Varies (depends on gaps)

**Runtime:** 2-3 hours

### Validation

**After completion:**
```bash
# Upload to S3
aws s3 sync /tmp/espn_missing/ s3://nba-sim-raw-data-lake/

# Verify upload
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | wc -l

# Clean up
rm -rf /tmp/espn_missing/
```

### When to Run
- **As needed:** When gaps identified in ESPN data
- **Validation:** After data quality checks reveal missing files
- **Current season:** Weekly during active season

---

## Integration with Existing Workflows

### Workflow #38 (Overnight Scraper Handoff)
- Add scraper completion checks for all 5 scrapers
- Reference Workflow #42 for scraper-specific validation
- Document scraper status in PROGRESS.md "Overnight jobs running" section

### Workflow #41 (Testing Framework)
- Run Test Suite 1 (Scraper Monitoring Tests) before launching overnight scrapers
- Validate scraper output with data quality tests
- Document test results in PROGRESS.md

### Workflow #16 (Testing)
- Reference Workflow #42 for scraper execution
- Include scraper output validation in test procedures

---

## Pre-Flight Checklist

**Before starting ANY overnight scraper:**

```bash
# 1. Check disk space (need 10+ GB free)
df -h /tmp
# Should show >10G available

# 2. Check network connectivity
ping stats.nba.com
ping www.basketball-reference.com
# Both should respond

# 3. Check credentials (if needed)
cat ~/.kaggle/kaggle.json  # For Kaggle
aws sts get-caller-identity  # For S3 upload
# Both should succeed

# 4. Check no duplicate process running
ps aux | grep scrape_
# Should show no existing scrapers

# 5. Backup existing output (if resuming)
if [ -d "/tmp/nba_api_comprehensive" ]; then
    mv /tmp/nba_api_comprehensive /tmp/nba_api_backup_$(date +%s)
fi
```

---

## Monitoring Best Practices

### During Execution

**Monitor progress continuously:**
```bash
# Watch log file (scraper-specific)
tail -f /tmp/[scraper]_log.log

# Check file count (updates every 5 seconds)
watch -n 5 'find /tmp/[output_dir]/ -type f | wc -l'

# Check error rate
grep -i "error" /tmp/[scraper]_log.log | wc -l

# Check process is running
ps aux | grep [scraper_name]
```

**Kill criteria (when to stop scraper):**
- Error rate > 10% of requests → Stop and investigate
- No new files for 10+ minutes → Stop (likely stuck)
- Disk space < 1 GB → Stop (will run out of space)
- 429 errors (Basketball Reference) → Stop immediately (rate limit block)

---

## Post-Execution Validation

**Standard validation checklist for ALL scrapers:**

```bash
# 1. Check process exited cleanly
echo $?  # Should be 0 (success)

# 2. Count output files
find /tmp/[output_dir]/ -type f | wc -l
# Compare to expected count (see scraper-specific sections)

# 3. Check for errors in log
grep -i "error\|exception\|failed" /tmp/[scraper]_log.log
# Should be 0 or very low percentage

# 4. Validate sample files (JSON validity)
python -m json.tool /tmp/[output_dir]/[sample_file1].json
python -m json.tool /tmp/[output_dir]/[sample_file2].json
# Both should succeed

# 5. Upload to S3
aws s3 sync /tmp/[output_dir]/ s3://nba-sim-raw-data-lake/[source]/
# Note: Check upload speed, should be ~10-50 MB/s

# 6. Verify S3 upload completed
aws s3 ls s3://nba-sim-raw-data-lake/[source]/ --recursive | wc -l
# Should match local file count

# 7. Clean up local files (after S3 verification)
rm -rf /tmp/[output_dir]/
```

---

## Troubleshooting

### General Recovery Protocol

**If ANY scraper fails mid-run:**

```bash
# Step 1: Check process status
ps aux | grep [scraper_name]
# If still running, check logs

# Step 2: Check logs for failure point
tail -100 /tmp/[scraper]_log.log
grep -i "error\|exception" /tmp/[scraper]_log.log

# Step 3: Identify failure cause
# - Network timeout? → Check ping
# - Rate limit? → Wait and restart
# - Missing parameter? → Check scraper code
# - Disk space? → Clean up /tmp

# Step 4: Preserve partial results (if valuable)
ls /tmp/[output_dir]/ | wc -l
# If >1000 files, back up to S3 before cleanup
aws s3 sync /tmp/[output_dir]/ s3://nba-sim-raw-data-lake/[source]_partial/

# Step 5: Fix issue
# See scraper-specific failure sections above

# Step 6: Restart scraper
bash scripts/etl/overnight_[scraper].sh
# Most scrapers skip existing files, safe to restart
```

---

## Emergency Procedures

**If all recovery procedures fail:**

```bash
# 1. Stop scraper immediately (prevent further damage)
ps aux | grep [scraper_name]
kill -9 [PID]

# 2. Preserve logs for debugging
aws s3 cp /tmp/[scraper]_log.log s3://nba-sim-raw-data-lake/logs/failure_$(date +%s).log

# 3. Check source website status
curl -I https://stats.nba.com
curl -I https://www.basketball-reference.com
# Look for HTTP 200 OK

# 4. Document error
# Create GitHub issue with last 100 lines of log
tail -100 /tmp/[scraper]_log.log > /tmp/error_report.txt

# 5. Wait and retry (after 24 hours for Basketball Reference, immediately for others)
```

---

## Documentation Updates

### Document scraper runs in PROGRESS.md

**Add to "Overnight jobs running" section:**
```markdown
- **[Scraper Name]**: Started [TIME], PID [PID]
  - Status: 🔄 In Progress
  - Coverage: [DATE_RANGE]
  - Expected completion: [ETA]
  - Output: /tmp/[output_dir]/
  - Monitor: `tail -f /tmp/[scraper]_log.log`
  - Next step: Upload to S3, validate output
```

### Document in COMMAND_LOG.md

```markdown
## Scraper Execution - [DATE]

### [Scraper Name]
```bash
bash scripts/etl/overnight_[scraper].sh
```
**Result:** [FILES_CREATED] files, [ERRORS] errors
**Runtime:** [DURATION]
**Status:** ✅ Success / ❌ Failed
```

---

## Quick Reference Card

**Launch all scrapers (parallel execution):**
```bash
# NBA API (5-6 hours)
nohup bash scripts/etl/overnight_nba_api_comprehensive.sh > /tmp/nba_api.log 2>&1 &

# hoopR Phase 1B (30-60 minutes)
nohup bash scripts/etl/run_hoopr_phase1b.sh > /tmp/hoopr.log 2>&1 &

# Basketball Reference incremental (3-4 hours)
nohup bash scripts/etl/scrape_bbref_incremental.sh 2020 2025 > /tmp/bbref.log 2>&1 &

# Monitor all
tail -f /tmp/nba_api.log /tmp/hoopr.log /tmp/bbref.log
```

**Check all scraper statuses:**
```bash
ps aux | grep -E "scrape_nba_api|scrape_hoopr|scrape_bbref" | grep -v grep
```

**Kill all scrapers (emergency stop):**
```bash
ps aux | grep -E "scrape_nba_api|scrape_hoopr|scrape_bbref" | grep -v grep | awk '{print $2}' | xargs kill -9
```

---

## Best Practices

1. **Always run pre-flight checklist** before launching overnight scrapers
2. **Monitor for first 10 minutes** to catch early failures
3. **Never run Basketball Reference faster than 3.5s** per request
4. **Always upload to S3 after completion** before cleaning up local files
5. **Document all scraper runs** in PROGRESS.md and COMMAND_LOG.md
6. **Run Workflow #38** at start of next session to check completion
7. **Validate output with Workflow #41** (Testing Framework) after completion

---

*Last updated: October 8, 2025*
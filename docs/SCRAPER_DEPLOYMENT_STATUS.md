# Scraper Deployment Status

**Deployed:** October 9, 2025
**Status:** ✅ ACTIVE
**Checkpoint/Resume:** Fully implemented on both scrapers

---

## Currently Running Scrapers

### 1. Basketball Reference Scraper (Recent Seasons)
**PID:** 15843
**Coverage:** 2020-2025 (6 seasons, 7 data types = 42 operations)
**Status:** 🔄 RUNNING
**Started:** Thu Oct 9, 2025 22:30:27 CDT
**Estimated completion:** ~2-3 hours
**Log:** `/tmp/bbref_2020-2025.log`
**Output:** `/tmp/basketball_reference_incremental/`
**S3:** `s3://nba-sim-raw-data-lake/basketball_reference/`

**Checkpoint status:**
- Completion markers: `/tmp/basketball_reference_incremental/*.complete`
- Resume capability: ✅ YES - run same command to skip completed work

---

### 2. Basketball Reference Scraper (Historical)
**PID:** 19278
**Coverage:** 1947-2019 (73 seasons, 7 data types = 511 operations)
**Status:** 🔄 RUNNING
**Started:** Thu Oct 9, 2025 22:36:24 CDT
**Estimated completion:** ~20-25 hours
**Log:** `/tmp/bbref_1947-2019.log`
**Output:** `/tmp/basketball_reference_incremental/` (shared with recent scraper)
**S3:** `s3://nba-sim-raw-data-lake/basketball_reference/`

**Data types being scraped (7 per season):**
1. Schedules
2. Season totals
3. Advanced totals
4. Standings
5. Player box scores
6. Team box scores
7. Play-by-play (2000+ only)

**Checkpoint status:**
- Completion markers: `/tmp/basketball_reference_incremental/*.complete`
- Resume capability: ✅ YES - run same command to skip completed work
- **Note:** Play-by-play only available 2000+, automatically skipped for earlier seasons

**Combined Basketball Reference Coverage:**
- **Total:** 1947-2025 (79 seasons, 553 total operations)
- **Running in parallel:** Both scrapers share output directory and checkpoint system
- **No conflicts:** Each scraper handles different season ranges

---

### 3. NBA API Comprehensive Scraper (TEST)
**PID:** 17289
**Coverage:** 2024-2025 (2 seasons, 200+ endpoints)
**Status:** 🔄 RUNNING
**Started:** Thu Oct 9, 2025 22:32:57 CDT
**Estimated completion:** ~50-60 hours
**Log:** `/tmp/nba_api_test.log`
**Output:** `/tmp/nba_api_comprehensive/`
**S3:** `s3://nba-sim-raw-data-lake/nba_api_comprehensive/`

**Endpoint categories:**
- ⏰ Play-by-play with timestamps (temporal panel data)
- 👤 Player biographical info (birth dates for age calculations)
- 📊 League dashboards
- 💪 Hustle stats (2016+ only)
- 🎓 Draft data
- 🎯 Shot charts
- ⚡ Synergy play types (2016+ only)
- 📦 Advanced box scores (8 endpoints, ALL games)
- 🏃 Player tracking (4 endpoints, ALL players, 2014+ only)

**Checkpoint status:**
- Individual file saves: Each game/player/endpoint saved immediately
- S3 upload: Immediate after each file creation
- Resume capability: ✅ YES - modify SEASONS array and re-run

**Known issues:**
- ⚠️ 50-70% error rate on some endpoints (expected, documented in script)
- Rate limit: 2.5s between requests (conservative to avoid blocking)

---

## Auto-Recovery System

**Deployed:** October 9, 2025
**Status:** ✅ ACTIVE
**Integration:** Overnight workflow Step 10

### Overview

Automated health check and recovery system that monitors all long-running scrapers and automatically redeploys failed ones from their last checkpoint. Runs daily at 3 AM as part of the overnight workflow.

### Health Check Script

**Location:** `scripts/monitoring/check_and_recover_scrapers.sh`

**Monitors:**
1. Basketball Reference (2020-2025)
2. Basketball Reference (1947-2019)
3. NBA API Test (2024-2025)

**Check Logic:**
```bash
# For each scraper:
1. Check if process is running (ps aux | grep)
2. If not running:
   a. Check log for completion message
   b. If completed → SUCCESS
   c. If not completed → FAILED, trigger recovery
```

**Recovery Actions:**
- Basketball Reference: Redeploy with `nohup bash scrape_bbref_incremental.sh [years]`
- NBA API: Redeploy with `nohup bash overnight_nba_api_test.sh`
- All recoveries use same checkpoint system (automatic resume)

**Manual Execution:**
```bash
# Standard mode
bash scripts/monitoring/check_and_recover_scrapers.sh

# Verbose mode (detailed logging)
bash scripts/monitoring/check_and_recover_scrapers.sh --verbose
```

**Output:**
- Console: Color-coded status (✓ = success, ⚠️ = warning, ✗ = error)
- Log: `/tmp/scraper_recovery_YYYYMMDD_HHMMSS.log`

### Integration with Overnight Workflow

**File:** `scripts/workflows/overnight_multi_source_unified.sh`

**Step 10: Check Long-Running Scrapers**
- Runs after all normal workflow steps (Steps 1-9)
- Non-fatal: Workflow continues even if recovery fails
- Logs all output to overnight workflow log
- Recovery attempts logged separately

**Execution Flow:**
```
3:00 AM - Overnight workflow starts
  ↓
Steps 1-9 - Normal data collection (ESPN, hoopR, unified DB, etc.)
  ↓
Step 10 - Health check and auto-recovery
  ├─ Check Basketball Reference (2020-2025)
  ├─ Check Basketball Reference (1947-2019)
  ├─ Check NBA API Test
  ├─ Recover any failed scrapers
  └─ Log summary
  ↓
Workflow complete
```

### Recovery Scenarios

**Scenario 1: Scraper Still Running**
- Health check: ✓ RUNNING
- Action: None (healthy)
- Log: "All scrapers healthy - no recovery needed"

**Scenario 2: Scraper Completed Successfully**
- Health check: Completed message found in log
- Action: None (completed normally)
- Log: "Completed successfully"

**Scenario 3: Scraper Failed/Interrupted**
- Health check: Not running + no completion message
- Action: Redeploy from checkpoint
- Steps:
  1. Launch with `nohup` (same command as original)
  2. Capture new PID
  3. Wait 5 seconds
  4. Verify process is running
  5. Log recovery success/failure

**Scenario 4: Recovery Fails**
- Health check: Recovery deployment failed
- Action: Log error, continue workflow
- Manual intervention: Check logs and redeploy manually

### Checkpoint/Resume Behavior

**Basketball Reference:**
- Checkpoint markers: `/tmp/basketball_reference_incremental/*.complete`
- Resume: Re-run same command, automatically skips completed seasons/data-types
- Data loss: None (all completed work preserved)
- Re-scraping: May re-scrape current season's incomplete data type

**NBA API:**
- Checkpoint: Each game/player/endpoint saved immediately to disk + S3
- Resume: Modify SEASONS array or re-run (skips existing files)
- Data loss: None (all API calls already saved)
- Re-scraping: May re-attempt failed API calls

### Monitoring Commands

**Quick Status:**
```bash
bash SCRAPER_MONITOR.sh
```

**Live Monitoring:**
```bash
# Basketball Reference (Recent)
tail -f /tmp/bbref_2020-2025.log

# Basketball Reference (Historical)
tail -f /tmp/bbref_1947-2019.log

# NBA API Test
tail -f /tmp/nba_api_test.log

# Recovery log (after recovery attempt)
tail -f /tmp/scraper_recovery_*.log
```

**Check Overnight Workflow:**
```bash
# Find latest overnight log
ls -lt logs/overnight/ | head -5

# View overnight workflow log
tail -f logs/overnight/overnight_unified_*.log
```

### Expected Behavior

**Normal Night (All Healthy):**
```
Step 10: CHECK LONG-RUNNING SCRAPERS
  ✓ Basketball Reference (2020-2025): RUNNING
  ✓ Basketball Reference (1947-2019): RUNNING
  ✓ NBA API Test: RUNNING
  ✓ All scrapers healthy - no recovery needed
```

**Recovery Night (1 Failed):**
```
Step 10: CHECK LONG-RUNNING SCRAPERS
  ⚠️ Basketball Reference (2020-2025): NOT RUNNING
    ✗ Failed or interrupted
  Attempting recovery...
    ℹ Redeploying from last checkpoint...
    ✓ Redeployed with PID: 12345
    ✓ Verified running
  ✓ Basketball Reference (1947-2019): RUNNING
  ✓ NBA API Test: RUNNING

  Recovery Summary:
    Scrapers needing recovery: 1
    Successful recoveries: 1
    Failed recoveries: 0
```

**Completion Night (Some Completed):**
```
Step 10: CHECK LONG-RUNNING SCRAPERS
  ⚠️ Basketball Reference (2020-2025): NOT RUNNING
    ✓ Completed successfully
  ✓ Basketball Reference (1947-2019): RUNNING
  ✓ NBA API Test: RUNNING
  ✓ All scrapers healthy - no recovery needed
```

### Testing

**Test Command:**
```bash
bash scripts/monitoring/check_and_recover_scrapers.sh --verbose
```

**Test Results (October 9, 2025):**
```
[2025-10-09 22:52:05] SCRAPER HEALTH CHECK AND AUTO-RECOVERY
✓ Basketball Reference (2020-2025): RUNNING
✓ Basketball Reference (1947-2019): RUNNING
✓ NBA API Test: RUNNING
✓ All scrapers healthy - no recovery needed

Full log: /tmp/scraper_recovery_20251009_225205.log
```

**Status:** ✅ All tests passed

### Troubleshooting

**Problem:** Recovery script reports "Failed to start"
- Check: Conda environment activated in script
- Check: Project paths are correct
- Check: Original scraper script exists and is executable
- Manual recovery: Run scraper command manually with `nohup`

**Problem:** Health check says "NOT RUNNING" but scraper is actually running
- Cause: Process name doesn't match grep pattern
- Check: `ps aux | grep scrape_bbref_incremental.sh`
- Fix: Update grep pattern in health check function

**Problem:** Recovery runs every night even though scraper completed
- Cause: Completion message not found in log
- Check: Log file for completion message
- Fix: Ensure scraper logs "complete" message on success

**Problem:** Workflow fails at Step 10
- Cause: Recovery script not found or not executable
- Check: File exists at `scripts/monitoring/check_and_recover_scrapers.sh`
- Check: File has execute permissions (`chmod +x`)
- Workflow continues anyway (non-fatal step)

### Future Enhancements

**Planned:**
- Email/Slack notifications on recovery events
- Recovery attempt limits (max 3 attempts before alerting)
- Detailed recovery metrics (success rate, average recovery time)
- Integration with full NBA API scraper (after test completion)

**Not Planned:**
- ESPN/hoopR scrapers (short-running, ~5-10 minutes)
- Manual-only scrapers (on-demand, not scheduled)

---

## Continuous Scraper Monitor

**Deployed:** October 10, 2025
**Status:** ✅ ACTIVE
**PID:** 68695
**Version:** 2.0 (with duplicate cleanup)

### Overview

Continuous monitoring system that runs every 30 minutes to:
1. **Detect and kill duplicate scraper processes** (prevents rate limit waste)
2. **Monitor scraper health** (check if running, completed, or failed)
3. **Auto-recover failed scrapers** from last checkpoint
4. **Track progress** for each scraper

### Features

**Duplicate Detection & Cleanup:**
- Counts instances of each scraper type
- If multiple instances found:
  - Identifies newest PID (most recent progress)
  - Kills all older/duplicate PIDs
  - Logs each kill with PID and timestamp
  - Verifies kills succeeded
- Prevents rate limit waste from simultaneous API calls
- Ensures clean recovery state

**Health Monitoring:**
- Checks process status every 30 minutes
- Detects completion vs. failure
- Tracks progress (seasons completed)
- Logs all status changes

**Auto-Recovery:**
- Redeploys failed scrapers from checkpoint
- Verifies recovery succeeded
- Logs recovery attempts separately

### Location

**Script:** `scripts/monitoring/continuous_scraper_monitor.sh`

**Monitors:**
1. Basketball Reference (2020-2025)
2. Basketball Reference (1947-2019)
3. NBA API Comprehensive (1996-2025)

### Duplicate Cleanup Logic

```bash
# For each scraper type:
1. Count running instances
2. If count > 1:
   a. Get all PIDs sorted by start time (newest first)
   b. Keep newest PID (most recent progress)
   c. Kill all older PIDs one by one
   d. Wait 2s after each kill
   e. Verify process terminated
   f. Log cleanup summary
3. If count = 1:
   a. Continue with normal health check
4. If count = 0:
   a. Check if completed
   b. If not completed, trigger recovery
```

### Usage

**Start Monitor:**
```bash
# Default 30-minute checks
nohup bash scripts/monitoring/continuous_scraper_monitor.sh > /tmp/continuous_monitor.log 2>&1 &

# Custom interval (10 minutes)
nohup bash scripts/monitoring/continuous_scraper_monitor.sh --interval 600 > /tmp/continuous_monitor.log 2>&1 &
```

**Stop Monitor:**
```bash
ps aux | grep continuous_scraper_monitor.sh | grep -v grep
kill [PID]
```

**View Log:**
```bash
# Real-time monitoring
tail -f /tmp/continuous_monitor_v2.log

# Latest check results
tail -50 /tmp/continuous_monitor_v2.log
```

### Log Output Examples

**Normal Check (No Duplicates):**
```
[2025-10-10 00:08:29] CHECK #1 - 2025-10-10 00:08:29
✓ Basketball Reference (2020-2025): COMPLETED
✓ Basketball Reference (1947-2019): RUNNING
  Progress: 39/73 seasons
✓ NBA API Comprehensive: RUNNING
  Progress: 0/30 seasons
ℹ All active scrapers healthy - next check in 30 minutes
```

**Duplicate Cleanup:**
```
[2025-10-10 00:08:29] CHECK #2 - 2025-10-10 00:38:29

⚠ NBA API Comprehensive: Found 3 instances (expected 1)
ℹ   → Keeping newest PID: 62056
⚠   → Killing old/duplicate PID: 17371
    ✓ PID 17371 terminated
⚠   → Killing old/duplicate PID: 59906
    ✓ PID 59906 terminated
✓   → Cleaned up 2 duplicate process(es)

✓ NBA API Comprehensive: RUNNING
  Progress: 1/30 seasons
```

**Recovery Event:**
```
[2025-10-10 03:00:15] CHECK #15 - 2025-10-10 03:00:15

✗ Basketball Reference (1947-2019): FAILED
ℹ   Last progress: 45/73 seasons
ℹ RECOVERY: Basketball Reference (1947-2019) - Restarting from checkpoint...
✓   → Redeployed with PID: 12345
ℹ   → Will resume from last completed season (checkpoint system)
✓   → Verified running
✓   → Recovery successful
```

### Integration with Overnight Workflow

The continuous monitor runs **independently** from the overnight workflow:

- **Continuous Monitor:** Checks every 30 minutes, 24/7
- **Overnight Workflow:** Single health check at 3 AM (Step 10)

Both systems work together:
1. Continuous monitor provides ongoing protection
2. Overnight workflow provides daily checkpoint
3. Duplicate cleanup runs in both systems

### Benefits

**Rate Limit Protection:**
- Prevents duplicate API calls
- Ensures only 1 instance per scraper type
- Protects against IP bans from NBA API

**Clean Recovery:**
- Kills old/stale processes before redeploying
- No orphaned processes consuming resources
- Clear process state at all times

**Automatic Cleanup:**
- No manual intervention needed
- Runs every 30 minutes
- Detailed logging for debugging

**Safety:**
- Always keeps newest process (most progress)
- Waits 2s after kill to verify
- Non-fatal if kill fails (logs warning, continues)

### Testing

**Test Results (October 10, 2025):**
```bash
# Started monitor
PID: 68695
Log: /tmp/continuous_monitor_v2.log

# Check #1 (00:08:29)
✓ Basketball Reference (2020-2025): COMPLETED
✓ Basketball Reference (1947-2019): RUNNING (39/73 seasons)
✓ NBA API Comprehensive: RUNNING (0/30 seasons)
✓ No duplicates found (cleaned up earlier manually)
✓ All scrapers healthy

Status: ✅ PASSED
```

### Troubleshooting

**Problem:** Monitor reports duplicates every check
- Cause: Duplicate process keeps restarting
- Check: Is auto-recovery triggering incorrectly?
- Fix: Review recovery logic, check completion detection

**Problem:** Old PIDs not being killed
- Cause: Process may have already exited
- Log shows: "Failed to kill PID [X] (may have already exited)"
- Action: Safe to ignore (non-fatal warning)

**Problem:** Monitor itself consumes too many resources
- Cause: Too frequent checks
- Fix: Increase interval (--interval 3600 for 1 hour)

**Problem:** Can't find which scraper is which
- Check: `ps aux | grep scrape` to see all scraper processes
- Compare: PID against monitor log to identify newest

### Current Status

**Monitor:** ✅ RUNNING (PID 68695)
**Interval:** 30 minutes
**Next check:** ~00:38:29 (every 30 min from start)
**Checks performed:** 1
**Duplicates cleaned:** 0 (none found in Check #1)
**Recoveries:** 0 (all healthy)

---

## Monitoring Quick Reference

**Check all scrapers:**
```bash
bash SCRAPER_MONITOR.sh
```

**Check specific logs:**
```bash
tail -f /tmp/bbref_2020-2025.log      # Recent Basketball Reference
tail -f /tmp/bbref_1947-2019.log      # Historical Basketball Reference
tail -f /tmp/nba_api_test.log         # NBA API Test
```

**Check overnight workflow:**
```bash
ls -lt logs/overnight/ | head -1      # Find latest log
tail -f logs/overnight/overnight_unified_*.log
```

**Manual recovery (if needed):**
```bash
bash scripts/monitoring/check_and_recover_scrapers.sh --verbose
```

**Monitor PIDs:**
```bash
ps aux | grep scrape_bbref_incremental.sh
ps aux | grep overnight_nba_api_test.sh
```

---

## Next Steps

1. **Monitor first overnight run** (tomorrow 3 AM)
   - Check logs after waking up
   - Verify auto-recovery worked if any scrapers failed

2. **After NBA API test completes** (2-3 days)
   - Review error rates and data quality
   - If successful, deploy full NBA API scraper (all 30 seasons)
   - Update recovery script to monitor full scraper

3. **After all scrapers complete**
   - Verify S3 uploads complete
   - Run data quality checks
   - Archive deployment logs
   - Update PROGRESS.md with completion status
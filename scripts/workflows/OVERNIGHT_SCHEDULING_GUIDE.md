# Overnight Multi-Source Workflow Scheduling Guide

**Purpose:** Configure automatic nightly execution of the unified database workflow
**Created:** October 9, 2025
**Platform:** macOS (launchd)

---

## Overview

The overnight workflow runs daily at 3:00 AM to:
1. Scrape incremental data from ESPN & hoopR (last 7-14 days)
2. Update game ID mappings
3. Rebuild unified database with quality scores
4. Detect data discrepancies
5. Export ML-ready datasets
6. Generate quality reports
7. Backup databases
8. Clean up old files

**Runtime:** ~30 minutes
**Previous runtime:** 12+ hours (before optimization)
**Improvement:** **24x faster**

---

## Quick Start

### 1. Verify launchd Configuration Exists

```bash
ls -l ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

### 2. Load the Schedule

```bash
launchctl load ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

### 3. Verify It's Loaded

```bash
launchctl list | grep nba-simulator
```

Expected output:
```
-	0	com.nba-simulator.overnight-workflow
```

### 4. Check Next Run Time

```bash
launchctl print gui/$(id -u)/com.nba-simulator.overnight-workflow
```

Look for `next run time` in the output.

---

## launchd Configuration Details

### File Location

```
~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

### Key Settings

| Setting | Value | Purpose |
|---------|-------|---------|
| **Label** | `com.nba-simulator.overnight-workflow` | Unique identifier |
| **Schedule** | Daily at 3:00 AM | Off-peak hours, after games finish |
| **Script** | `scripts/workflows/overnight_multi_source_unified.sh` | Main workflow |
| **Working Directory** | `/Users/ryanranft/nba-simulator-aws` | Project root |
| **Timeout** | 2 hours (7200s) | Maximum runtime before kill |
| **PATH** | Includes conda env bin | Ensure Python access |

### Environment Variables

The plist includes:
- `PATH`: `/Users/ryanranft/miniconda3/envs/nba-aws/bin:...`
- `HOME`: `/Users/ryanranft`
- `USER`: `ryanranft`

---

## Management Commands

### Load Schedule (Enable)

```bash
launchctl load ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

### Unload Schedule (Disable)

```bash
launchctl unload ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

### Manually Trigger Now

```bash
launchctl start com.nba-simulator.overnight-workflow
```

### Check Status

```bash
launchctl list | grep nba-simulator
```

Output format: `PID	Status	Label`
- PID = process ID (if running) or `-` (if idle)
- Status = exit code from last run (`0` = success)

### View Detailed Info

```bash
launchctl print gui/$(id -u)/com.nba-simulator.overnight-workflow
```

Shows:
- Next run time
- Last exit status
- Environment variables
- Working directory

### Remove from launchd

```bash
# Unload first
launchctl unload ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist

# Then delete plist (optional)
rm ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

---

## Monitoring

### Log Files

**Main workflow log:**
```
/Users/ryanranft/nba-simulator-aws/logs/overnight/overnight_unified_YYYYMMDD_HHMMSS.log
```

**launchd stdout:**
```
/tmp/overnight_workflow_stdout.log
```

**launchd stderr:**
```
/tmp/overnight_workflow_stderr.log
```

### Check Latest Run

```bash
# View latest workflow log
ls -lt /Users/ryanranft/nba-simulator-aws/logs/overnight/ | head -5

# Tail latest log
tail -100 /Users/ryanranft/nba-simulator-aws/logs/overnight/overnight_unified_*.log
```

### Check if Running

```bash
ps aux | grep overnight_multi_source_unified | grep -v grep
```

### Monitor Live Execution

```bash
# If manually triggered
tail -f /tmp/overnight_workflow_stdout.log

# Or watch the workflow's internal log
tail -f /Users/ryanranft/nba-simulator-aws/logs/overnight/overnight_unified_*.log
```

---

## Testing

### Test Workflow Manually

```bash
# Run once to verify it works
cd /Users/ryanranft/nba-simulator-aws
bash scripts/workflows/overnight_multi_source_unified.sh
```

### Test launchd Execution

```bash
# Trigger immediately (doesn't wait for 3 AM)
launchctl start com.nba-simulator.overnight-workflow

# Check if it started
ps aux | grep overnight_multi_source_unified

# View output
tail -f /tmp/overnight_workflow_stdout.log
```

### Verify Completion

```bash
# Check exit status
launchctl list | grep nba-simulator
# Second column should be 0 (success)

# Check latest workflow log
ls -lt /Users/ryanranft/nba-simulator-aws/logs/overnight/ | head -1

# Check for completion message
grep -A 5 "WORKFLOW COMPLETE" /Users/ryanranft/nba-simulator-aws/logs/overnight/overnight_unified_*.log | tail -10
```

---

## Troubleshooting

### Issue: Job Not Running

**Check if loaded:**
```bash
launchctl list | grep nba-simulator
```

**If not listed:**
```bash
launchctl load ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

**Check plist syntax:**
```bash
plutil -lint ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

Expected: `OK` output

### Issue: Job Fails Immediately

**Check error log:**
```bash
cat /tmp/overnight_workflow_stderr.log
```

**Common causes:**
1. Script not found → Check path in plist
2. Permissions issue → `chmod +x scripts/workflows/overnight_multi_source_unified.sh`
3. Conda env not activated → Check PATH in plist
4. Credentials not loaded → Verify `/Users/ryanranft/nba-sim-credentials.env` exists

**Debug with manual run:**
```bash
# Simulate launchd environment
env -i \
  HOME=/Users/ryanranft \
  USER=ryanranft \
  PATH=/Users/ryanranft/miniconda3/envs/nba-aws/bin:/usr/bin:/bin \
  bash /Users/ryanranft/nba-simulator-aws/scripts/workflows/overnight_multi_source_unified.sh
```

### Issue: Conda Environment Not Found

**Update PATH in plist:**
```xml
<key>PATH</key>
<string>/Users/ryanranft/miniconda3/envs/nba-aws/bin:/usr/local/bin:/usr/bin:/bin</string>
```

**Verify conda environment exists:**
```bash
/Users/ryanranft/miniconda3/envs/nba-aws/bin/python --version
```

### Issue: Workflow Times Out

**Check timeout setting:**
```xml
<key>ExitTimeOut</key>
<integer>7200</integer> <!-- 2 hours -->
```

**If workflow needs more time:**
- Increase timeout to 10800 (3 hours)
- Unload and reload plist

**Check for hung processes:**
```bash
ps aux | grep -E "(espn_incremental|hoopr_incremental|python)"
```

### Issue: Credentials Not Found

**Verify credentials file exists:**
```bash
ls -l /Users/ryanranft/nba-sim-credentials.env
```

**Verify it's sourced in workflow script:**
```bash
grep "nba-sim-credentials.env" scripts/workflows/overnight_multi_source_unified.sh
```

Should see:
```bash
source /Users/ryanranft/nba-sim-credentials.env
```

---

## Customization

### Change Schedule Time

Edit plist file:
```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>3</integer>  <!-- Change this -->
    <key>Minute</key>
    <integer>0</integer>  <!-- And this -->
</dict>
```

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
launchctl load ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

### Run Multiple Times Per Day

```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>15</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

### Run Only on Specific Days

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Weekday</key>
    <integer>1</integer>  <!-- Monday = 1, Sunday = 0 -->
    <key>Hour</key>
    <integer>3</integer>
</dict>
```

### Disable During Off-Season

**Option 1: Unload manually**
```bash
# Before off-season
launchctl unload ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist

# When season starts
launchctl load ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist
```

**Option 2: Add season check to script**
```bash
# At top of overnight_multi_source_unified.sh
month=$(date +%m)
if [ $month -eq 7 ] || [ $month -eq 8 ] || [ $month -eq 9 ]; then
    echo "Off-season, skipping workflow"
    exit 0
fi
```

---

## Performance Metrics

### Expected Runtime (macOS M1/M2)

| Step | Duration | Notes |
|------|----------|-------|
| Setup | <5s | Environment activation |
| ESPN incremental | 2-5 min | During season, <30s off-season |
| hoopR incremental | 2-5 min | During season, <5s off-season |
| Game ID mappings | 10-20s | 30K+ game IDs |
| Unified database rebuild | 20-30s | 31K+ games |
| Discrepancy detection | 30-60s | Dual-source games only |
| ML dataset export | 15-30s | 20MB JSON + CSV |
| Quality report | <5s | SQLite queries |
| Backup | 5-10s | Copy unified DB |
| Cleanup | <5s | Vacuum + log rotation |
| **Total** | **~10-30 min** | Varies by season activity |

### Disk Usage

- Workflow logs: ~1-2 MB/day
- Backup database: ~50-100 MB/day (kept 7 days)
- ML datasets: ~20-25 MB/day
- **Total:** ~75-130 MB/day

**Cleanup:** Old logs deleted after 30 days, backups after 7 days

### Network Usage

- ESPN scraper: 0-50 MB (incremental, off-season = minimal)
- hoopR scraper: 0-100 MB (incremental, off-season = minimal)
- **Total:** 0-150 MB/day (NBA season), <1 MB/day (off-season)

---

## Integration with Other Systems

### Notification on Completion

Add to `overnight_multi_source_unified.sh`:
```bash
# At end of main() function
curl -X POST https://your-webhook-url.com/notify \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Overnight workflow completed\", \"status\": \"success\"}"
```

### Upload to Cloud Storage

Add step before cleanup:
```bash
# Sync ML datasets to S3
aws s3 sync "$ML_QUALITY_DIR" s3://your-bucket/ml_quality/ \
  --exclude "*" --include "ml_quality_dataset_*.json"
```

### Trigger Downstream Workflows

At end of workflow:
```bash
# Trigger model retraining
curl -X POST https://your-api.com/retrain-model

# Or run local script
python scripts/ml/retrain_model.py &
```

---

## Maintenance

### Weekly Tasks

- ✅ Check launchd status: `launchctl list | grep nba-simulator`
- ✅ Review latest logs for errors
- ✅ Verify databases are updating

### Monthly Tasks

- ✅ Review log file sizes
- ✅ Check backup directory size
- ✅ Validate data quality reports
- ✅ Test manual execution

### Quarterly Tasks

- ✅ Review and update schedule if needed
- ✅ Optimize workflow based on season patterns
- ✅ Archive old quality reports

---

## Security Considerations

### Credentials

- ✅ AWS credentials in `~/.aws/credentials` (not in plist)
- ✅ NBA credentials in `/Users/ryanranft/nba-sim-credentials.env` (sourced by script)
- ✅ No secrets hardcoded in plist or scripts

### File Permissions

```bash
# launchd plist should be user-readable only
chmod 600 ~/Library/LaunchAgents/com.nba-simulator.overnight-workflow.plist

# Workflow script should be user-executable
chmod 700 scripts/workflows/overnight_multi_source_unified.sh

# Credentials file should be user-readable only
chmod 600 /Users/ryanranft/nba-sim-credentials.env
```

### Process Isolation

- ✅ Runs as user (not root)
- ✅ Limited to 2-hour runtime (prevents runaway processes)
- ✅ Logs to /tmp (auto-cleaned by system)

---

## Comparison: launchd vs cron

| Feature | launchd | cron |
|---------|---------|------|
| **macOS Native** | ✅ Yes | ⚠️ Deprecated |
| **Persistent** | ✅ Yes | ❌ Requires user login |
| **Environment Control** | ✅ Full | ⚠️ Limited |
| **Logging** | ✅ Built-in | ❌ Manual |
| **Calendar Flexibility** | ✅ High | ⚠️ Limited |
| **System Integration** | ✅ Deep | ❌ Minimal |
| **Error Recovery** | ✅ Automatic | ❌ Manual |

**Recommendation:** Use launchd on macOS (this guide), use cron on Linux

---

## Next Steps After Setup

1. ✅ **Verify first run** completes successfully
   - Check logs after 3:00 AM tomorrow
   - Verify all 9 steps completed
   - Review quality report generated

2. ✅ **Monitor for one week**
   - Daily log review
   - Track runtime trends
   - Note any errors

3. ✅ **Document baseline metrics**
   - Average runtime
   - Data coverage improvements
   - Quality score distributions

4. ✅ **Optimize if needed**
   - Adjust schedule based on usage patterns
   - Enable/disable optional features
   - Fine-tune incremental scraper lookback periods

---

## Related Documentation

- **Main workflow script:** `scripts/workflows/overnight_multi_source_unified.sh`
- **Incremental scrapers:** `scripts/etl/espn_incremental_scraper.py`, `scripts/etl/hoopr_incremental_scraper.py`
- **Daily automation guide:** `scripts/workflows/DAILY_AUTOMATION_SETUP.md` (ESPN-specific)
- **Workflow #38:** Overnight Scraper Handoff Protocol
- **PROGRESS.md:** Project status and recent updates

---

## Support

**If you encounter issues:**

1. Check logs: `/tmp/overnight_workflow_stderr.log`
2. Review this troubleshooting section
3. Test manual execution: `bash scripts/workflows/overnight_multi_source_unified.sh`
4. Verify launchd configuration: `launchctl print gui/$(id -u)/com.nba-simulator.overnight-workflow`

**For persistent issues:**
- Review TROUBLESHOOTING.md in project root
- Check GitHub issues: https://github.com/ryanranft/nba-simulator-aws/issues

---

**Last Updated:** October 9, 2025
**Version:** 1.0
**Platform:** macOS 14+ (launchd)
**Status:** ✅ Production Ready

---

**End of Overnight Scheduling Guide**

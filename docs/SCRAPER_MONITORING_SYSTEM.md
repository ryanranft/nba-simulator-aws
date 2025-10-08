# Overnight Scraper Monitoring System

**Last Updated:** October 8, 2025
**System Type:** Hybrid (Persistent Daemon + Session-Based Checks)

The project includes a comprehensive monitoring system for long-running overnight scrapers. This system ensures scraper completions are never missed and provides intelligent context preservation.

---

## Architecture

### Persistent Daemon
- `scripts/monitoring/scraper_watcher_daemon.sh` - Runs in background, monitors all scrapers
- Sends desktop notifications (macOS) when scrapers complete
- Creates alert files in `/tmp/scraper_alerts/` for completed scrapers
- Tracks reminder files in `/tmp/scraper_reminders/` for running scrapers

### Session-Based Tools
- `scripts/monitoring/check_scraper_alerts.sh` - Check for completed scrapers at session start
- `scripts/monitoring/analyze_scraper_completion.sh` - Analyze completion and recommend actions
- `scripts/monitoring/save_work_context.sh` - Preserve current work before checking scrapers

---

## Quick Reference Commands

### Check for Completed Scrapers
```bash
bash scripts/monitoring/check_scraper_alerts.sh
```

### Analyze Specific Completion
```bash
bash scripts/monitoring/analyze_scraper_completion.sh /tmp/scraper_alerts/<scraper>.alert
```

### Save Current Work Context
```bash
bash scripts/monitoring/save_work_context.sh "Task description" "Current step" "Next step"
```

### Launch Daemon (Auto-Started by launch_scraper.sh)
```bash
nohup bash scripts/monitoring/scraper_watcher_daemon.sh > /tmp/scraper_daemon.log 2>&1 &
```

---

## Session Start Workflow Integration

**When starting a new Claude Code session, always:**

1. **Check PROGRESS.md** for "Overnight jobs running" section
2. **If overnight jobs were running:**
   - Run: `bash scripts/monitoring/check_scraper_alerts.sh`
   - Review any completed scrapers
   - For each completion, run: `bash scripts/monitoring/analyze_scraper_completion.sh <alert_file>`
   - Follow recommendations (COMPLETE or INVESTIGATE)
   - Clear alerts when reviewed: `rm /tmp/scraper_alerts/*.alert`
3. **Document results** in PROGRESS.md or relevant phase file
4. **Resume regular work** after scraper check

---

## Completion Analysis Framework

The `analyze_scraper_completion.sh` script provides two recommendations:

### COMPLETE (No Action Needed)
- ✅ No errors detected in log
- ✅ Completion marker found in log
- **Next steps:** Verify S3 uploads, clear alert

### INVESTIGATE (Review Required)
- ⚠️ Errors found in log OR missing completion marker
- **Actions:** Review log, check error details, decide if redeployment needed

---

## File Locations

### Runtime Directories
- `/tmp/scraper_alerts/` - Alert files for completed scrapers
- `/tmp/scraper_reminders/` - Reminder files for running scrapers
- `/tmp/claude_work_context.json` - Saved work context

### Log Files
- `/tmp/scraper_daemon.log` - Daemon monitoring log
- `/tmp/<scraper_name>.log` - Individual scraper logs

---

## Best Practices

### For Claude Code
1. Always check alerts at session start if PROGRESS.md mentions overnight jobs
2. Save work context before switching to scraper check (preserve current task)
3. Analyze completions systematically (don't just clear alerts)
4. Document outcomes in PROGRESS.md

### For Users
1. Let daemon run continuously (won't interfere with other work)
2. Clear alerts after reviewing: `rm /tmp/scraper_alerts/*.alert`
3. Check daemon log if notifications aren't appearing: `tail -f /tmp/scraper_daemon.log`

---

## Related Workflows

- **Workflow #38:** [Overnight Scraper Handoff Protocol](claude_workflows/workflow_descriptions/38_overnight_scraper_handoff.md) - Complete session start workflow
- **Workflow #40:** [Scraper Operations Complete](claude_workflows/workflow_descriptions/40_scraper_operations_complete.md) - Launching and monitoring scrapers

---

## Integration with PROGRESS.md

### Overnight Jobs Section Format

When scrapers are running, PROGRESS.md should contain:

```markdown
## Overnight Jobs Running

**Started:** [Date, Time]
**Scrapers:**
- Basketball Reference (2020-2025): PID [XXXXX]
- hoopR Phase 1B: PID [XXXXX]

**Monitoring:**
- Daemon running: PID [XXXXX]
- Alerts directory: `/tmp/scraper_alerts/`
- Check at next session: `bash scripts/monitoring/check_scraper_alerts.sh`
```

### After Checking Alerts

Update PROGRESS.md with results:

```markdown
## Last Session Scraper Results

**Checked:** [Date, Time]
**Completed Scrapers:**
- ✅ Basketball Reference (2020-2025): 6 seasons, 42 data types, uploaded to S3
- ✅ hoopR Phase 1B: 24 seasons, 248 CSV files, uploaded to S3

**Issues:**
- None (all scrapers completed successfully)

**Next Steps:**
- Validate S3 uploads
- Update data collection status in Phase 0
```

---

## Troubleshooting

### Daemon Not Sending Notifications
```bash
# Check if daemon is running
ps aux | grep scraper_watcher_daemon

# Check daemon log for errors
tail -f /tmp/scraper_daemon.log

# Restart daemon if needed
pkill -f scraper_watcher_daemon
nohup bash scripts/monitoring/scraper_watcher_daemon.sh > /tmp/scraper_daemon.log 2>&1 &
```

### Alert Files Not Created
```bash
# Check alert directory exists
ls -la /tmp/scraper_alerts/

# Create if missing
mkdir -p /tmp/scraper_alerts/

# Check daemon permissions
ls -l /tmp/scraper_alerts/
```

### False Completion Alerts
```bash
# Analyze completion to verify
bash scripts/monitoring/analyze_scraper_completion.sh /tmp/scraper_alerts/<scraper>.alert

# If INVESTIGATE result, review log
tail -100 /tmp/<scraper_name>.log
```

---

*For complete scraper management procedures, see docs/SCRAPER_MANAGEMENT.md*

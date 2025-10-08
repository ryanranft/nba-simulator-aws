# Scripts Monitoring Directory

**Last Updated:** October 8, 2025

---

## Overview

This directory contains monitoring and automation scripts for tracking long-running scraper jobs and other background processes.

**Complete documentation:** See Workflow #39 (`docs/claude_workflows/workflow_descriptions/39_scraper_monitoring_automation.md`)

---

## Quick Reference

### Core Monitoring Scripts

#### 1. `data_collection_status.sh` ⭐ NEW
**Purpose:** Automated data collection inventory across all sources
**Usage:**
```bash
bash scripts/monitoring/data_collection_status.sh markdown
```

**Output:**
- Auto-generates `docs/DATA_COLLECTION_INVENTORY.md`
- S3 file counts and sizes for all data sources (ESPN, hoopR, Basketball Reference, NBA API, Kaggle, SportsDataverse)
- Active scraper PIDs
- Last activity timestamps
- Failed scraper error counts
- Recommended next steps

**Features:**
- Real-time S3 integration via AWS CLI
- Automated markdown report generation
- Integrated with Workflow #38 (Overnight Scraper Handoff)
- Detects failed scrapers by error count

**When to use:**
- At session start (check overnight job results)
- After completing scraper runs
- Before launching new scrapers (check existing data)
- When generating status reports

#### 2. `monitor_scrapers.sh`
**Purpose:** Check status of all running scraper processes
**Usage:**
```bash
bash scripts/monitoring/monitor_scrapers.sh
```

**Output:** Process status, log locations, progress indicators

#### 3. `launch_scraper.sh`
**Purpose:** Launch scrapers with proper nohup and logging
**Usage:**
```bash
bash scripts/monitoring/launch_scraper.sh <script_name> [args]
```

#### 4. `analyze_scraper_completion.sh`
**Purpose:** Analyze scraper output and detect completion/errors
**Usage:**
```bash
bash scripts/monitoring/analyze_scraper_completion.sh
```

**Checks:**
- Output file counts
- Error patterns in logs
- Completion markers

#### 5. `check_scraper_alerts.sh`
**Purpose:** Check for scraper failures and generate alerts
**Usage:**
```bash
bash scripts/monitoring/check_scraper_alerts.sh
```

**Alerts on:**
- Process crashes
- Rate limit errors
- Stalled progress

---

## Automated Workflows

### Session Startup Check
Automatically runs at session start to check overnight scraper status:

```bash
# Invoked by session_startup.sh
bash scripts/monitoring/monitor_scrapers_inline.sh
```

See Workflow #38 for overnight scraper handoff protocol.

### Daemon Mode (Future)
**Script:** `scraper_watcher_daemon.sh`
**Status:** ⏸️ TO BE IMPLEMENTED
**Purpose:** Continuous monitoring in background

---

## Integration with Workflows

| Workflow | When to Use | Monitoring Script |
|----------|-------------|-------------------|
| #38: Overnight Scraper Handoff | Session start | `monitor_scrapers_inline.sh` |
| #39: Scraper Monitoring | Check progress | `monitor_scrapers.sh` |
| #42: Scraper Management | Launch jobs | `launch_scraper.sh` |

---

## Output Locations

All monitoring output goes to `/tmp/` for easy access:

```
/tmp/
├── nba_api.log              # NBA API scraper log
├── hoopr.log                # hoopR scraper log
├── hoopr_phase1b_runner.log # hoopR phase 1B log
├── bbref.log                # Basketball Reference log
└── scraper_status.txt       # Latest status check
```

---

## Best Practices

1. **Always check status** before launching new scrapers (avoid duplicates)
2. **Monitor logs** for first few minutes after launch to catch early errors
3. **Check disk space** before overnight runs (need 10+ GB free)
4. **Document runs** in COMMAND_LOG.md with outcome
5. **Upload to S3** after completion before cleaning local files

---

## Troubleshooting

### Problem: "Scraper not found" error
**Solution:** Verify scraper script exists and is executable:
```bash
ls -la scripts/etl/scrape_*.py
chmod +x scripts/etl/scrape_*.sh
```

### Problem: "Permission denied" on log files
**Solution:** Clean up old logs:
```bash
rm /tmp/*.log
```

### Problem: Duplicate processes detected
**Solution:** Kill existing processes first:
```bash
ps aux | grep scrape | grep -v grep | awk '{print $2}' | xargs kill
```

**Full troubleshooting:** See Workflow #42

---

## Testing

### Validate Monitoring System
```bash
bash scripts/monitoring/validate_monitoring_system.sh
```

**Checks:**
- All monitoring scripts are executable
- Required log directories exist
- Process detection works correctly

### Test Monitoring System
```bash
bash scripts/monitoring/test_monitoring_system.sh
```

**Tests:**
- Launch dummy process
- Detect with monitoring scripts
- Kill and verify cleanup

---

## File Inventory

```
scripts/monitoring/
├── README.md (this file)
├── data_collection_status.sh        # ⭐ NEW: Automated inventory system
├── monitor_scrapers.sh              # Status check (manual)
├── monitor_scrapers_inline.sh       # Status check (automated)
├── launch_scraper.sh                # Launch wrapper
├── analyze_scraper_completion.sh    # Completion detection
├── check_scraper_alerts.sh          # Failure alerts
├── save_work_context.sh             # Context preservation
├── scraper_watcher_daemon.sh        # Background daemon (future)
├── test_monitoring_system.sh        # Test suite
└── validate_monitoring_system.sh    # Validation checks
```

---

*For detailed documentation, see Workflow #39: `docs/claude_workflows/workflow_descriptions/39_scraper_monitoring_automation.md`*

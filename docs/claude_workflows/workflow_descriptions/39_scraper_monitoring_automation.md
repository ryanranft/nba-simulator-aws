# Workflow #39: Scraper Monitoring Automation

**Purpose:** Automatically detect and monitor all running scraper processes with real-time progress tracking, error detection, and completion status.

**When to Use:**
- When scrapers are running in the background
- To check status of overnight scraper jobs
- To monitor multiple scrapers simultaneously
- To detect errors or stalled processes

**Auto-Detection Features:**
- Automatically finds all running scraper processes (no manual PID tracking)
- Detects scraper type from command (Basketball Reference, hoopR, NBA API, etc.)
- Finds associated log files automatically
- Tracks completion progress via markers or file counts
- Calculates runtime for each scraper
- Counts errors from log files
- Shows last activity from each scraper

---

## Quick Start

### Single Status Check
```bash
cd /Users/ryanranft/nba-simulator-aws
bash scripts/monitoring/monitor_scrapers.sh
```

### Watch Mode (Auto-refresh every 30s)
```bash
bash scripts/monitoring/monitor_scrapers.sh --watch
```

### Custom Refresh Interval
```bash
bash scripts/monitoring/monitor_scrapers.sh --watch --interval 60
```

---

## What It Monitors

### Automatically Detects:
1. **Basketball Reference scrapers** (`scrape_bbref_*`, `scrape_basketball_reference_*`)
2. **hoopR scrapers** (`run_hoopr_*`, `scrape_hoopr_*`)
3. **NBA API scrapers** (`scrape_nba_api_*`)
4. **SportsDataverse scrapers** (`scrape_sportsdataverse_*`)
5. **Kaggle scrapers** (`download_kaggle_*`)
6. **ETL extraction jobs** (`extract_*`)
7. **Database load jobs** (`load_*`)

### For Each Scraper Shows:
- **Type:** Basketball Reference, hoopR, NBA API, etc.
- **PID:** Process ID
- **Runtime:** How long it's been running
- **Progress:** Completion markers or file counts
- **Errors:** Count of errors/failures in log
- **Log Path:** Where to find detailed logs
- **Last Activity:** Most recent log line (truncated to 80 chars)

---

## Display Format

```
================================================================================
NBA Simulator - Scraper Monitoring Dashboard
================================================================================
Timestamp: 2025-10-08 11:52:30

Active Scrapers: 2

--------------------------------------------------------------------------------
[1] Basketball Reference
  PID:        46509
  Runtime:    11m 37s
  Progress:   12
  Errors:     0
  Log:        /tmp/bbref_incremental_2020-2025.log
  Activity:   → Scraping team-box-scores for season 2021...

--------------------------------------------------------------------------------
[2] hoopR
  PID:        48458
  Runtime:    8m 15s
  Progress:   45 files
  Errors:     0
  Log:        /tmp/hoopr_phase1b.log
  Activity:   📅 Season 2008-09...

================================================================================
Refreshing every 30s... (Ctrl+C to exit)
```

---

## Integration with Workflow #38 (Overnight Scraper Handoff)

This monitoring tool is **essential** for Workflow #38. When checking overnight jobs:

### Step 1: Run Monitor First
```bash
bash scripts/monitoring/monitor_scrapers.sh
```

### Step 2: If Scrapers Running
- Note PIDs, runtime, and error counts
- Check if progress is advancing (run monitor again after 1-2 minutes)
- If stalled (no activity change), investigate log files

### Step 3: If No Scrapers Running
- Check if jobs completed successfully
- Look for completion markers (`.complete` files)
- Check final log entries for success/failure

### Step 4: Document Results
Update PROGRESS.md with:
- Scraper status (running/completed/failed)
- Runtime
- Error count
- Completion progress

---

## Auto-Detection Logic

### How It Finds Scrapers:
```bash
ps aux | grep -E "(scrape_|run_hoopr|extract_|load_)" | grep -v grep
```

### How It Identifies Type:
- Matches process command against known patterns
- Example: `scrape_bbref` → "Basketball Reference"
- Example: `run_hoopr` → "hoopR"

### How It Finds Logs:
1. **Known patterns first:**
   - `scrape_bbref_incremental` → `/tmp/bbref_incremental_2020-2025.log`
   - `run_hoopr_phase1b` → `/tmp/hoopr_phase1b.log`

2. **Extract from command line:**
   - Looks for `/tmp/*.log` in process command
   - Example: `... > /tmp/my_scraper.log` → detected automatically

### How It Tracks Progress:

**Basketball Reference:**
```bash
ls /tmp/basketball_reference_incremental/*.complete | wc -l
```
Shows: "12" (12 out of 42 season/data-type combinations complete)

**hoopR:**
```bash
find /tmp/hoopr_phase1 -name "*.csv" | wc -l
```
Shows: "45 files" (45 CSV files collected)

**Others:** Shows "N/A" if no progress tracking available

---

## Error Detection

Counts lines in log containing:
- "error" (case-insensitive)
- "failed" (case-insensitive)
- "exception" (case-insensitive)

**Display:**
- ✅ Green "0" if no errors
- 🔴 Red count if errors detected
- Shows "N/A" if no log file found

---

## Adding Support for New Scrapers

### Automatic Support (No Changes Needed):
If your scraper:
1. Has `scrape_`, `run_`, `extract_`, or `load_` in the name
2. Writes to `/tmp/*.log` file mentioned in command
3. Uses standard error keywords (error/failed/exception)

Then it will be **automatically detected and monitored**.

### Custom Support (Optional):

If you want custom log paths or progress tracking:

1. **Add to `find_log_file()` function:**
```bash
elif echo "$cmd" | grep -q "my_new_scraper"; then
    echo "/tmp/my_scraper_custom.log"
```

2. **Add to `check_completion()` function:**
```bash
"My Scraper Type")
    local progress=$(cat /tmp/my_scraper_progress.txt 2>/dev/null || echo "0")
    echo "$progress"
    ;;
```

3. **Add to `get_scraper_type()` function:**
```bash
elif echo "$cmd" | grep -q "my_new_scraper"; then
    echo "My Scraper Type"
```

---

## Use Cases

### Morning Check (Post-Overnight Run)
```bash
# Quick status check
bash scripts/monitoring/monitor_scrapers.sh

# If scrapers still running, watch them
bash scripts/monitoring/monitor_scrapers.sh --watch
```

### During Development
```bash
# Start scraper in background
nohup bash scripts/etl/my_scraper.sh > /tmp/my_scraper.log 2>&1 &

# Monitor it (automatically detected)
bash scripts/monitoring/monitor_scrapers.sh --watch --interval 10
```

### Troubleshooting Stalled Scraper
```bash
# Check status
bash scripts/monitoring/monitor_scrapers.sh

# Note the PID and log path
# Check detailed logs
tail -f /tmp/<scraper>.log

# If stalled, kill it
kill <PID>
```

---

## Keyboard Shortcuts (Watch Mode)

- **Ctrl+C:** Exit watch mode
- Monitor runs in foreground, safe to background with `Ctrl+Z` then `bg`

---

## Workflow Integration

**Add to CLAUDE.md quick reference:**
```
Daily workflow additions:
1. Check scrapers: bash scripts/monitoring/monitor_scrapers.sh
2. Watch scrapers: bash scripts/monitoring/monitor_scrapers.sh --watch
3. Stop watching: Ctrl+C
```

**Add to session startup checklist:**
```
After reading PROGRESS.md:
[ ] Run scraper monitor to check for overnight jobs
[ ] Note any running scrapers or errors
[ ] Update PROGRESS.md with scraper status
```

---

## Benefits

✅ **No manual PID tracking** - Automatically finds all scrapers
✅ **No manual log path management** - Automatically finds logs
✅ **Extensible** - New scrapers auto-detected
✅ **Real-time monitoring** - Watch mode with custom intervals
✅ **Error detection** - Automatically counts errors
✅ **Progress tracking** - Shows completion status
✅ **Runtime tracking** - Calculates how long each has been running
✅ **Supports multiple simultaneous scrapers** - See all at once

---

## Examples

### Example 1: Two Scrapers Running
```
Active Scrapers: 2

[1] Basketball Reference
  Runtime:    2h 15m
  Progress:   28
  Errors:     0

[2] hoopR
  Runtime:    1h 45m
  Progress:   120 files
  Errors:     0
```

### Example 2: Scraper With Errors
```
Active Scrapers: 1

[1] NBA API
  Runtime:    45m 12s
  Progress:   N/A
  Errors:     23
  Log:        /tmp/nba_api.log
  Activity:   HTTPSConnectionPool: Read timed out...
```

### Example 3: No Scrapers
```
No scrapers currently running

To start scrapers, run:
  Basketball Reference: bash scripts/etl/scrape_bbref_incremental.sh 2020 2025
  hoopR Phase 1B:       bash scripts/etl/run_hoopr_phase1b.sh
  NBA API:              bash scripts/etl/overnight_nba_api_comprehensive.sh
```

---

## Troubleshooting

**Q: Monitor shows wrong log file**
A: Add custom log path to `find_log_file()` function

**Q: Progress shows N/A**
A: Add custom progress tracking to `check_completion()` function

**Q: Scraper not detected**
A: Ensure command includes `scrape_`, `run_`, `extract_`, or `load_`

**Q: Error count seems wrong**
A: Check if log format uses different error keywords

**Q: Runtime not showing**
A: macOS-specific issue with `ps` command date parsing

---

*Last updated: October 8, 2025*
*Created by: Claude Code*
*Integration: Workflows #1 (Session Start), #38 (Overnight Scraper Handoff)*

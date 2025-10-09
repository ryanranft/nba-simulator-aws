# Scraper Integration Guide: Auto-Catalog Updates

**Purpose:** Integrate automatic DATA_CATALOG.md updates into all scraper workflows

**Created:** October 9, 2025

---

## Overview

All scrapers should automatically update the DATA_CATALOG.md file upon completion using the scraper completion hook.

**Benefits:**
- ✅ Always-current catalog statistics
- ✅ Centralized completion logging
- ✅ Automated notifications
- ✅ Timestamp tracking

---

## Quick Integration

### Add to End of Scraper Script

**For bash wrapper scripts:**
```bash
# At the very end of your script (after scraper completes)

# Success
bash scripts/utils/scraper_completion_hook.sh --source espn --status success

# Failure
bash scripts/utils/scraper_completion_hook.sh --source espn --status failed --error "Rate limit exceeded"

# Partial success
bash scripts/utils/scraper_completion_hook.sh --source hoopr --status partial --error "Completed 5/10 seasons"
```

**For Python scripts:**
```python
import subprocess

# At the end of your scraper
def trigger_completion_hook(source: str, status: str, error: str = None):
    """Trigger scraper completion hook."""
    cmd = [
        "bash",
        "scripts/utils/scraper_completion_hook.sh",
        "--source", source,
        "--status", status
    ]

    if error:
        cmd.extend(["--error", error])

    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"Warning: Completion hook failed: {e}")

# Usage
try:
    # Run your scraper code
    scrape_all_games()
    trigger_completion_hook("espn", "success")
except Exception as e:
    trigger_completion_hook("espn", "failed", str(e))
```

---

## Source Names

**Supported sources:**
- `espn` - ESPN API scraper
- `hoopr` - hoopR R package scraper
- `nba_api` - NBA.com Stats API scraper
- `basketball_ref` - Basketball Reference scraper

---

## Integration Examples

### Example 1: hoopR Comprehensive Wrapper

**File:** `scripts/etl/run_hoopr_comprehensive_overnight.sh`

**Add at end (after existing summary):**
```bash
# Existing summary code...
echo "  $category: $file_count files" | tee -a "$FULL_LOG"
done

# NEW: Trigger completion hook
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    bash scripts/utils/scraper_completion_hook.sh --source hoopr --status success
else
    bash scripts/utils/scraper_completion_hook.sh --source hoopr --status failed --error "Scraper exit code: ${PIPESTATUS[0]}"
fi
```

### Example 2: Basketball Reference Overnight

**File:** `scripts/etl/overnight_basketball_reference_comprehensive.sh`

**Add at end:**
```bash
# Existing completion code...
echo "Completed: $(date)"

# NEW: Check if scraper succeeded
if ps -p $SCRAPER_PID > /dev/null; then
    # Still running (shouldn't happen if wait worked)
    bash scripts/utils/scraper_completion_hook.sh --source basketball_ref --status partial --error "Scraper still running after timeout"
else
    # Check exit code
    wait $SCRAPER_PID
    exit_code=$?

    if [ $exit_code -eq 0 ]; then
        bash scripts/utils/scraper_completion_hook.sh --source basketball_ref --status success
    else
        bash scripts/utils/scraper_completion_hook.sh --source basketball_ref --status failed --error "Exit code: $exit_code"
    fi
fi
```

### Example 3: NBA API Comprehensive

**File:** `scripts/etl/overnight_nba_api_comprehensive.sh`

**Add at end:**
```bash
# Existing completion code...
echo "Log: $LOG_FILE"

# NEW: Trigger completion hook
# Note: NBA API is currently paused, so we document this
bash scripts/utils/scraper_completion_hook.sh --source nba_api --status partial --error "Paused due to rate limiting"
```

### Example 4: ESPN Daily Scraper (External Repo)

**File:** `~/0espn/scrape_daily.py` (or similar)

**Add at end of main():**
```python
def main():
    # Existing scraper code
    try:
        games_scraped = scrape_daily_games()
        upload_to_s3()

        # NEW: Trigger completion hook
        subprocess.run([
            "bash",
            "/Users/ryanranft/nba-simulator-aws/scripts/utils/scraper_completion_hook.sh",
            "--source", "espn",
            "--status", "success"
        ], check=False)  # Don't fail if hook fails

        print(f"✓ Scraped {games_scraped} games")

    except Exception as e:
        # NEW: Trigger completion hook with error
        subprocess.run([
            "bash",
            "/Users/ryanranft/nba-simulator-aws/scripts/utils/scraper_completion_hook.sh",
            "--source", "espn",
            "--status", "failed",
            "--error", str(e)
        ], check=False)

        raise
```

---

## Hook Behavior

### On Success

1. ✅ Logs completion to `logs/scraper_completions.log`
2. ✅ Creates timestamp file in `/tmp/scraper_timestamps/`
3. ✅ Updates DATA_CATALOG.md with latest statistics
4. ✅ Sends notification (if configured)

**Example Output:**
```
═══════════════════════════════════════════════════════════════
  Scraper Completion Hook
  Source: espn
  Status: success
═══════════════════════════════════════════════════════════════

✓ [2025-10-09 15:30:45] [espn] [success]

═══════════════════════════════════════════════════════════════
  Updating Data Catalog
═══════════════════════════════════════════════════════════════

📊 Fetching ESPN statistics from local database...
✅ ESPN statistics updated successfully
   Games: 44,850
   Games with PBP: 31,265
   PBP Events: 14,125,086
   Coverage: 69.7%

✓ Catalog updated successfully for espn

═══════════════════════════════════════════════════════════════
  Completion Hook Finished
═══════════════════════════════════════════════════════════════
```

### On Failure

1. ✅ Logs failure with error message
2. ✅ Creates timestamp file with error details
3. ⏭️ **Skips** DATA_CATALOG.md update (no changes on failure)
4. ✅ Sends error notification (if configured)

**Example Output:**
```
═══════════════════════════════════════════════════════════════
  Scraper Completion Hook
  Source: nba_api
  Status: failed
═══════════════════════════════════════════════════════════════

✗ [2025-10-09 15:30:45] [nba_api] [failed] ERROR: Rate limit exceeded (429)

⏭️  Skipping catalog update (scraper status: failed)

═══════════════════════════════════════════════════════════════
  Completion Hook Finished
═══════════════════════════════════════════════════════════════
```

---

## Completion Log

**Location:** `logs/scraper_completions.log`

**Format:**
```
[2025-10-09 03:05:12] [espn] [success]
[2025-10-09 10:42:33] [hoopr] [success]
[2025-10-09 15:20:01] [nba_api] [failed] ERROR: Rate limit exceeded
[2025-10-10 03:05:45] [espn] [success]
[2025-10-10 08:15:22] [basketball_ref] [success]
```

**Usage:**
```bash
# View recent completions
tail -20 logs/scraper_completions.log

# View today's completions
grep "$(date +%Y-%m-%d)" logs/scraper_completions.log

# View failures
grep "failed" logs/scraper_completions.log

# Count completions by source
awk '{print $3}' logs/scraper_completions.log | sort | uniq -c
```

---

## Timestamp Files

**Location:** `/tmp/scraper_timestamps/<source>_last_completion.txt`

**Format:**
```
2025-10-09 15:30:45
success
```

**Or with error:**
```
2025-10-09 15:30:45
failed
Rate limit exceeded (429)
```

**Usage:**
```bash
# Check last ESPN completion
cat /tmp/scraper_timestamps/espn_last_completion.txt

# Check all completions
ls -lt /tmp/scraper_timestamps/

# Get timestamp of last success
head -1 /tmp/scraper_timestamps/espn_last_completion.txt
```

---

## Notification Integration

### Slack

**Setup:**
```bash
# Set webhook URL
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Add to ~/.bashrc or cron job
echo 'export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"' >> ~/.bashrc
```

**Message Format:**
```
✅ Scraper completion: **espn** - Status: success
```

or

```
❌ Scraper completion: **nba_api** - Status: failed
Error: Rate limit exceeded (429)
```

### Email

**To add email notifications:**
```bash
# Edit scraper_completion_hook.sh
# In send_notification() function, add:

if [ -n "${EMAIL_RECIPIENT:-}" ]; then
    local subject="Scraper Completion: $SOURCE - $STATUS"
    local body="Source: $SOURCE\nStatus: $STATUS"

    if [ -n "$ERROR_MSG" ]; then
        body="$body\nError: $ERROR_MSG"
    fi

    echo -e "$body" | mail -s "$subject" "$EMAIL_RECIPIENT"
fi
```

**Setup:**
```bash
export EMAIL_RECIPIENT="user@example.com"
```

---

## Testing

### Manual Test

```bash
# Test success hook
bash scripts/utils/scraper_completion_hook.sh --source espn --status success

# Test failure hook
bash scripts/utils/scraper_completion_hook.sh --source espn --status failed --error "Test error message"

# Test with skipped catalog update
bash scripts/utils/scraper_completion_hook.sh --source espn --status success --skip-catalog-update
```

### Verify Integration

```bash
# 1. Check completion log
tail -5 logs/scraper_completions.log

# 2. Check timestamp file
cat /tmp/scraper_timestamps/espn_last_completion.txt

# 3. Check catalog was updated
git diff docs/DATA_CATALOG.md

# 4. Check catalog timestamp
grep "Last Full Update" docs/DATA_CATALOG.md
```

---

## Integration Checklist

### For Each Scraper

- [ ] Identified scraper wrapper script location
- [ ] Added completion hook call at end of script
- [ ] Tested success path
- [ ] Tested failure path
- [ ] Verified catalog update works
- [ ] Verified completion log entry created
- [ ] Verified timestamp file created
- [ ] Documented in this guide

### Scrapers to Integrate

**Priority 1 (Active):**
- [ ] `~/0espn/scrape_daily.py` (ESPN daily scraper)
- [ ] `scripts/etl/run_hoopr_comprehensive_overnight.sh` (hoopR comprehensive)

**Priority 2 (Occasional):**
- [ ] `scripts/etl/overnight_basketball_reference_comprehensive.sh` (Basketball Reference)
- [ ] `scripts/etl/overnight_nba_api_comprehensive.sh` (NBA API - when resumed)

**Priority 3 (Utility):**
- [ ] `scripts/db/create_local_espn_database.py` (Database rebuild)
- [ ] `scripts/db/load_espn_events.py` (RDS load)

---

## Advanced Usage

### Conditional Catalog Update

**Only update if significant changes:**
```bash
# Count new games
NEW_GAMES=$(sqlite3 /tmp/espn_local.db "SELECT COUNT(*) FROM games WHERE last_updated > datetime('now', '-1 day')")

if [ "$NEW_GAMES" -gt 10 ]; then
    bash scripts/utils/scraper_completion_hook.sh --source espn --status success
else
    bash scripts/utils/scraper_completion_hook.sh --source espn --status success --skip-catalog-update
    echo "ℹ️  Only $NEW_GAMES new games, skipped catalog update"
fi
```

### Custom Notifications

**Extend `send_notification()` in hook script:**
```bash
# Add Discord webhook
if [ -n "${DISCORD_WEBHOOK_URL:-}" ]; then
    curl -H "Content-Type: application/json" \
        -d "{\"content\":\"$message\"}" \
        "$DISCORD_WEBHOOK_URL"
fi

# Add PagerDuty alert (for failures only)
if [ "$STATUS" = "failed" ] && [ -n "${PAGERDUTY_KEY:-}" ]; then
    # Send PagerDuty alert
    # ...
fi
```

### Parallel Scraper Coordination

**Wait for multiple scrapers before catalog update:**
```bash
# In each scraper, skip catalog update
bash scripts/utils/scraper_completion_hook.sh --source espn --status success --skip-catalog-update
bash scripts/utils/scraper_completion_hook.sh --source hoopr --status success --skip-catalog-update

# In master orchestration script, update catalog once
if all_scrapers_complete; then
    python scripts/utils/update_data_catalog.py --refresh-all
fi
```

---

## Troubleshooting

### Issue: "Update script not found"

**Check:**
```bash
ls -l scripts/utils/update_data_catalog.py
```

**Fix:**
```bash
# Ensure update script exists and is executable
chmod +x scripts/utils/update_data_catalog.py
```

### Issue: "Catalog update failed"

**Debug:**
```bash
# Run update manually to see error
python scripts/utils/update_data_catalog.py --source espn --action update --verbose
```

**Common causes:**
1. Local database doesn't exist
2. Database schema mismatch
3. Invalid DATA_CATALOG.md format
4. Python environment not activated

### Issue: "Completion log not created"

**Check:**
```bash
# Ensure log directory exists
ls -ld logs/

# Create if missing
mkdir -p logs
```

### Issue: "Notifications not working"

**Check:**
```bash
# Verify environment variable
echo $SLACK_WEBHOOK_URL

# Test webhook manually
curl -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d '{"text":"Test message"}'
```

---

## Best Practices

### 1. Always Call Hook (Even on Failure)

**Why:** Track all scraper executions, not just successes

**Good:**
```bash
if scraper_succeeds; then
    bash scripts/utils/scraper_completion_hook.sh --source espn --status success
else
    bash scripts/utils/scraper_completion_hook.sh --source espn --status failed --error "..."
fi
```

**Bad:**
```bash
if scraper_succeeds; then
    bash scripts/utils/scraper_completion_hook.sh --source espn --status success
fi
# No hook call on failure - lost tracking!
```

### 2. Capture Error Details

**Why:** Debugging requires context

**Good:**
```bash
bash scripts/utils/scraper_completion_hook.sh --source espn --status failed --error "Rate limit 429 at game 1523"
```

**Bad:**
```bash
bash scripts/utils/scraper_completion_hook.sh --source espn --status failed
# No error message - can't diagnose!
```

### 3. Use Non-Blocking Calls

**Why:** Hook failures shouldn't fail scraper

**Good:**
```bash
bash scripts/utils/scraper_completion_hook.sh --source espn --status success || true
```

**Bad:**
```bash
set -e  # Exit on error
bash scripts/utils/scraper_completion_hook.sh --source espn --status success
# If hook fails, entire script fails!
```

### 4. Test Integration First

**Why:** Prevent breaking production scrapers

**Process:**
1. Test hook manually
2. Test with dry-run flag
3. Test in scraper dev environment
4. Deploy to production

---

## Maintenance

### Weekly

- ✅ Review completion log for patterns
- ✅ Check notification delivery
- ✅ Verify catalog updates are accurate

### Monthly

- ✅ Archive old completion logs (> 90 days)
- ✅ Review hook performance
- ✅ Update integration documentation

### As Needed

- ✅ Add new sources to hook
- ✅ Update notification channels
- ✅ Enhance error messages

---

## Related Documentation

- **Completion Hook Script:** `scripts/utils/scraper_completion_hook.sh`
- **Catalog Updater:** `scripts/utils/update_data_catalog.py`
- **Daily Automation:** `scripts/workflows/daily_espn_update.sh`
- **Scraper Management:** `docs/SCRAPER_MANAGEMENT.md`
- **Workflow #38:** Overnight Scraper Handoff Protocol

---

## Example: Full Integration

**Before (no integration):**
```bash
#!/bin/bash
# scraper_wrapper.sh

echo "Starting scraper..."
python scrape_data.py
echo "Scraper complete"
```

**After (with integration):**
```bash
#!/bin/bash
# scraper_wrapper.sh

echo "Starting scraper..."

if python scrape_data.py; then
    echo "Scraper complete"

    # NEW: Trigger completion hook
    bash scripts/utils/scraper_completion_hook.sh \
        --source espn \
        --status success \
        || echo "Warning: Completion hook failed (non-fatal)"
else
    exit_code=$?
    echo "Scraper failed with exit code: $exit_code"

    # NEW: Trigger completion hook with error
    bash scripts/utils/scraper_completion_hook.sh \
        --source espn \
        --status failed \
        --error "Exit code: $exit_code" \
        || echo "Warning: Completion hook failed (non-fatal)"

    exit $exit_code
fi
```

---

**Last Updated:** October 9, 2025
**Version:** 1.0
**Status:** ✅ Ready for Integration

---

**End of Scraper Integration Guide**
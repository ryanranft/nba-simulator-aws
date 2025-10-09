# Overnight Automation: Multi-Source Unified Database Workflow

**Version:** 1.0
**Created:** October 9, 2025
**Purpose:** Automated nightly data collection, quality tracking, and unified database maintenance

---

## Overview

The overnight automation system orchestrates a complete multi-source data pipeline that runs nightly at 3:00 AM when:
- NBA games are finalized
- Web traffic is low (respectful scraping)
- System resources are available

### Workflow Steps

1. **Scrape ESPN Data** - Collect latest games from ESPN
2. **Scrape hoopR Data** - Collect latest games from hoopR
3. **Update Game ID Mappings** - Extract ESPN↔hoopR game ID mappings
4. **Rebuild Unified Database** - Combine all sources with quality tracking
5. **Detect Discrepancies** - Compare dual-source games for data quality issues
6. **Export ML Quality Dataset** - Generate ML-ready quality metadata
7. **Generate Quality Reports** - Daily quality summary
8. **Backup Databases** - Backup unified database (keep last 7 days)
9. **Send Notification** - Email summary (optional)

**Total Duration:** ~15-30 minutes (depends on number of new games)

---

## Quick Start

### 1. Test the Workflow (Manual Run)

Before scheduling, test the workflow manually:

```bash
cd /Users/ryanranft/nba-simulator-aws
bash scripts/workflows/overnight_multi_source_unified.sh
```

**Expected Output:**
```
======================================================================
OVERNIGHT MULTI-SOURCE UNIFIED WORKFLOW
======================================================================

[2025-10-09 03:00:00] Log file: logs/overnight/overnight_unified_20251009_030000.log
[2025-10-09 03:00:00] ✓ Setup complete

======================================================================
STEP 1: SCRAPE ESPN DATA
======================================================================
...
```

**Check Results:**
```bash
# View log
tail -100 logs/overnight/overnight_unified_*.log

# Check daily report
cat reports/daily_quality_report_$(date +%Y%m%d).md

# Check ML quality dataset
ls -lh data/ml_quality/ml_quality_dataset_*.csv
```

### 2. Schedule Nightly Execution

**Option A: Using cron (macOS/Linux)**

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 3:00 AM)
0 3 * * * cd /Users/ryanranft/nba-simulator-aws && bash scripts/workflows/overnight_multi_source_unified.sh

# Verify crontab
crontab -l
```

**Option B: Using launchd (macOS preferred)**

Create a launch agent:

```xml
<!-- ~/Library/LaunchAgents/com.nbasimulator.overnight.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nbasimulator.overnight</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/ryanranft/nba-simulator-aws/scripts/workflows/overnight_multi_source_unified.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/ryanranft/nba-simulator-aws/logs/overnight/launchd_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/ryanranft/nba-simulator-aws/logs/overnight/launchd_stderr.log</string>
</dict>
</plist>
```

Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.nbasimulator.overnight.plist
launchctl list | grep nbasimulator
```

---

## Configuration

### Environment Variables

Edit the script to customize:

```bash
# In scripts/workflows/overnight_multi_source_unified.sh

# Email notification
SEND_EMAIL=true
EMAIL_RECIPIENT="your-email@example.com"

# Database paths (default should work)
ESPN_DB="/tmp/espn_local.db"
HOOPR_DB="/tmp/hoopr_local.db"
UNIFIED_DB="/tmp/unified_nba.db"
```

### Schedule Options

**Daily at 3:00 AM (recommended):**
```bash
0 3 * * * <command>
```

**Daily at 4:00 AM (if 3 AM conflicts):**
```bash
0 4 * * * <command>
```

**Only on weekdays:**
```bash
0 3 * * 1-5 <command>
```

**Every 6 hours:**
```bash
0 */6 * * * <command>
```

---

## Monitoring

### Check Workflow Status

**View latest log:**
```bash
tail -f logs/overnight/overnight_unified_$(ls -t logs/overnight/ | grep overnight_unified | head -1)
```

**Check if workflow is running:**
```bash
ps aux | grep overnight_multi_source_unified.sh
```

**View recent runs:**
```bash
ls -lt logs/overnight/ | head -10
```

### Daily Quality Report

The workflow generates a daily quality report:

```bash
cat reports/daily_quality_report_$(date +%Y%m%d).md
```

**Example Report:**
```markdown
# Daily Data Quality Report

**Generated:** 2025-10-09 03:15:32

## Database Statistics

### Source Databases
- **ESPN:** 31,241 games
- **hoopR:** 28,779 games

### Unified Database
- **Total games:** 31,243
- **Dual-source games:** 28,777
- **Games with discrepancies:** 28,777

## Quality Distribution

High (90-100)  | 2     | 90.0
Medium (70-89) | 31,234 | 77.9
Low (<70)      | 7     | 65.0
```

### Email Notifications

Enable email notifications:

```bash
# In overnight_multi_source_unified.sh
SEND_EMAIL=true
EMAIL_RECIPIENT="your-email@example.com"
```

**Email Content:**
- Workflow completion status
- Summary statistics (total games, discrepancies)
- Link to log file
- Link to quality report

---

## Troubleshooting

### Workflow Failed

**Check the log:**
```bash
# Find most recent log
latest_log=$(ls -t logs/overnight/overnight_unified_*.log | head -1)
cat "$latest_log"
```

**Common Errors:**

1. **"conda: command not found"**
   - Fix: Ensure conda is initialized in shell
   ```bash
   conda init bash
   ```

2. **"Permission denied"**
   - Fix: Make script executable
   ```bash
   chmod +x scripts/workflows/overnight_multi_source_unified.sh
   ```

3. **"Database is locked"**
   - Fix: Ensure no other processes are using the databases
   ```bash
   lsof /tmp/unified_nba.db
   ```

4. **"Scraper failed"**
   - Non-fatal: Workflow continues with existing data
   - Check individual scraper logs

### Manual Recovery

If workflow fails, you can run individual steps:

```bash
# Step 1: Update mappings
python scripts/mapping/extract_espn_hoopr_game_mapping.py

# Step 2: Rebuild unified database
python scripts/etl/build_unified_database.py

# Step 3: Detect discrepancies
python scripts/validation/detect_data_discrepancies.py

# Step 4: Export ML dataset
python scripts/validation/export_ml_quality_dataset.py
```

---

## Performance

### Expected Execution Time

| Step | Duration | Notes |
|------|----------|-------|
| ESPN scrape | 5-10 min | Depends on new games |
| hoopR scrape | 5-10 min | Depends on new games |
| Update mappings | 10-15 sec | Fast (reads uid field) |
| Rebuild unified | 15-20 sec | Fast (metadata only) |
| Detect discrepancies | 3-6 min | Compares 28,777 games |
| Export ML dataset | 5-10 sec | Fast (JSON + CSV) |
| Generate reports | 1-2 sec | Fast (SQLite queries) |
| **Total** | **15-30 min** | Typical nightly run |

### Resource Usage

- **CPU:** Low-Medium (single-threaded)
- **Memory:** ~500 MB - 1 GB
- **Disk I/O:** Medium (database writes)
- **Network:** Low (respectful scraping with delays)

### Disk Space

**Daily additions:**
- New games: ~100 KB per game
- Logs: ~50 KB per run
- Backups: ~100 MB per day (unified DB only)

**Cleanup:**
- Logs older than 30 days: Auto-deleted
- Backups older than 7 days: Auto-deleted
- ML datasets: Manual cleanup (keep 30 days)

---

## Data Integrity Principles

**Critical Rules Enforced:**

1. ✅ **Source databases remain pure** (no cross-contamination)
2. ✅ **ESPN scraper writes ONLY to ESPN database**
3. ✅ **hoopR scraper writes ONLY to hoopR database**
4. ✅ **Unified database is SEPARATE** (combines sources with metadata)
5. ✅ **Discrepancies logged, not resolved** (document, don't modify sources)
6. ✅ **Quality scores updated based on findings**

**What Happens Nightly:**
- ESPN database gets new ESPN games ✓
- hoopR database gets new hoopR games ✓
- Unified database rebuilt from scratch using source databases ✓
- Quality scores recalculated based on latest discrepancies ✓

**What NEVER Happens:**
- ESPN data in hoopR database ❌
- hoopR data in ESPN database ❌
- Discrepancies "fixed" by modifying source data ❌
- Quality scores hardcoded or ignored ❌

---

## Integration with ML Pipeline

### Using Quality Dataset in ML Training

```python
import pandas as pd

# Load quality dataset
df = pd.read_csv('data/ml_quality/ml_quality_dataset_20251009.csv')

# Filter by quality level
high_quality = df[df['quality_level'] == 'high']      # Best for validation
medium_quality = df[df['quality_level'] == 'medium']  # Use with weights
low_quality = df[df['quality_level'] == 'low']        # Use with caution

# Quality-weighted training
sample_weight = df['training_weight']  # 0.0 to 1.0 based on quality score

# Train model
model.fit(X, y, sample_weight=sample_weight)

# Filter by specific issues
no_score_issues = df[~df['has_score_issue']]
no_timing_issues = df[~df['has_timing_issue']]
```

### Automated ML Retraining

Add to overnight workflow (optional):

```bash
# After Step 6: Export ML Dataset
if [ -f "scripts/ml/retrain_models.py" ]; then
    log "Retraining ML models with updated quality dataset..."
    python scripts/ml/retrain_models.py --quality-aware >> "$LOG_FILE" 2>&1
    log "✓ ML models retrained"
fi
```

---

## Maintenance

### Weekly Tasks

1. **Review Quality Reports**
   ```bash
   cat reports/daily_quality_report_*.md
   ```

2. **Check for New Discrepancy Patterns**
   ```bash
   sqlite3 /tmp/unified_nba.db "
   SELECT field_name, COUNT(*), severity
   FROM data_quality_discrepancies
   WHERE detected_at > datetime('now', '-7 days')
   GROUP BY field_name, severity;
   "
   ```

3. **Monitor Disk Usage**
   ```bash
   du -sh logs/overnight/
   du -sh backups/
   du -sh data/ml_quality/
   ```

### Monthly Tasks

1. **Review Data Quality Trends**
   - Are discrepancies increasing?
   - Are quality scores declining?
   - Are new data sources needed?

2. **Clean Old ML Datasets**
   ```bash
   find data/ml_quality -name "*.csv" -mtime +30 -delete
   find data/ml_quality -name "*.json" -mtime +30 -delete
   ```

3. **Archive Old Reports**
   ```bash
   tar -czf reports_archive_$(date +%Y%m).tar.gz reports/daily_quality_report_*.md
   rm reports/daily_quality_report_*.md
   ```

### Quarterly Tasks

1. **Validate Source Databases**
   - ESPN database still accurate?
   - hoopR coverage still improving?
   - Should we add NBA API or Basketball Reference?

2. **Review Automation Performance**
   - Is workflow completing on time?
   - Are any steps failing frequently?
   - Should we optimize discrepancy detection?

---

## Advanced Configuration

### Running Steps Selectively

Skip certain steps by commenting them out in `main()`:

```bash
# In overnight_multi_source_unified.sh

main() {
    setup || error_handler "Setup"

    # Skip ESPN scraping
    # scrape_espn || log "⚠️  ESPN scraping skipped"

    scrape_hoopr || log "⚠️  hoopR scraping skipped"
    update_mappings || error_handler "Update Mappings"
    rebuild_unified || error_handler "Rebuild Unified Database"
    detect_discrepancies || error_handler "Detect Discrepancies"
    export_ml_dataset || error_handler "Export ML Dataset"
    generate_reports || error_handler "Generate Reports"
    backup_databases || log "⚠️  Backup failed"
    send_notification || log "⚠️  Notification failed"
    cleanup || log "⚠️  Cleanup failed"
}
```

### Custom Notification Webhooks

Replace email notification with Slack/Discord/etc:

```bash
send_notification() {
    # Slack webhook
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"NBA Simulator workflow complete!\"}" \
        https://hooks.slack.com/services/YOUR/WEBHOOK/URL

    # Discord webhook
    curl -X POST -H "Content-Type: application/json" \
        -d "{\"content\":\"NBA Simulator workflow complete!\"}" \
        https://discord.com/api/webhooks/YOUR/WEBHOOK
}
```

---

## Uninstalling

### Remove Cron Job

```bash
crontab -e
# Delete the line containing overnight_multi_source_unified.sh
```

### Remove Launch Agent (macOS)

```bash
launchctl unload ~/Library/LaunchAgents/com.nbasimulator.overnight.plist
rm ~/Library/LaunchAgents/com.nbasimulator.overnight.plist
```

### Clean Up Files

```bash
# Remove logs
rm -rf logs/overnight/

# Remove backups
rm -rf backups/

# Remove ML quality datasets
rm -rf data/ml_quality/

# Keep daily reports (or delete)
# rm -rf reports/daily_quality_report_*.md
```

---

## FAQ

**Q: Can I run the workflow during the day?**
A: Yes, but avoid peak hours (9 AM - 9 PM) to respect API rate limits.

**Q: What if I miss a night?**
A: No problem! The next run will catch up. The workflow is idempotent.

**Q: Can I run multiple sources in parallel?**
A: Yes, but the current script runs sequentially to avoid rate limits. Modify `main()` to run scrapers in background if needed.

**Q: How do I add a new data source (e.g., NBA API)?**
A:
1. Create scraper script for new source
2. Add step to `overnight_multi_source_unified.sh`
3. Update `build_unified_database.py` to include new source
4. Update `detect_data_discrepancies.py` to compare new source

**Q: Can I sync to RDS instead of local SQLite?**
A: Yes! Modify `UNIFIED_DB` path to use PostgreSQL connection, or add RDS sync step after local build.

---

## Related Documentation

- **Data Integrity Principles:** `docs/DATA_INTEGRITY_PRINCIPLES.md`
- **Workflow #51:** `docs/claude_workflows/workflow_descriptions/51_multi_source_data_quality.md`
- **Discrepancy Analysis:** `reports/discrepancy_analysis_20251009.md`
- **ML Quality Dataset:** `data/ml_quality/ml_quality_summary_YYYYMMDD.md`

---

## Support

**Issues:** https://github.com/ryanranft/nba-simulator-aws/issues
**Maintainer:** Ryan Ranft
**Last Updated:** October 9, 2025
**Version:** 1.0

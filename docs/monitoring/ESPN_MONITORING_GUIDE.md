# ESPN Autonomous Collection Monitoring Guide

**Last Updated:** November 6, 2025
**Status:** Production Ready
**ADCE Integration:** Complete

---

## Quick Reference

**Key Commands:**
```bash
# Check ESPN metrics
python scripts/monitoring/dims_cli.py show --category espn_data

# Run ESPN scraper manually
python scripts/etl/espn_incremental_async.py --days 3

# Run scheduled wrapper (with post-execution hooks)
bash scripts/autonomous/run_scheduled_espn.sh "--days 3"

# Check reconciliation status
python scripts/autonomous/autonomous_cli.py status

# View ESPN task queue
cat inventory/gaps.json | jq '.[] | select(.source=="espn")'
```

---

## Daily Monitoring Checklist

### Morning Check (9 AM)

**1. Verify Overnight Scraper Run (2 AM scheduled)**
```bash
# Check most recent log
ls -lt logs/autonomous/espn_scheduled_*.log | head -1

# View summary
tail -30 logs/autonomous/espn_scheduled_$(ls -t logs/autonomous/espn_scheduled_*.log | head -1 | xargs basename)
```

**Expected:** Log shows "ESPN SCHEDULED SCRAPER - Complete" with all phases ✓ SUCCESS

**2. Check DIMS ESPN Metrics**
```bash
python scripts/monitoring/dims_cli.py show --category espn_data
```

**Expected Ranges:**
- `espn_data.last_update_hours`: < 24 hours (✓ Fresh)
- `espn_data.completeness_pct`: ≥ 95.0% (✓ Target met)
- `espn_data.gap_days_count`: 0-3 days (✓ Acceptable)
- `espn_data.pbp_file_count`: Increasing daily (+10-15 files/day)

**3. Verify No Critical Gaps**
```bash
cat inventory/gaps.json | jq '[.[] | select(.source=="espn" and .priority=="CRITICAL")] | length'
```

**Expected:** 0 critical ESPN gaps

---

## ESPN Metrics Interpretation

### File Count Metrics

| Metric | Current Baseline | Daily Growth | Alert Threshold |
|--------|------------------|--------------|-----------------|
| `espn_data.pbp_file_count` | ~45,000 | +10-15 | No growth 3 days |
| `espn_data.boxscore_file_count` | ~35,000 | +10-15 | No growth 3 days |
| `espn_data.schedule_file_count` | ~31 | +0-1 | No growth 7 days |
| `espn_data.team_stats_file_count` | ~176 | +10-15 | No growth 3 days |

**Why it matters:** File counts should increase proportionally with games played. No growth indicates scraper failure.

### Freshness Metrics

| Metric | Green Zone | Yellow Zone | Red Zone |
|--------|-----------|-------------|----------|
| `espn_data.last_update_hours` | < 24 | 24-48 | > 48 |
| `espn_data.oldest_data_days` | < 7 | 7-14 | > 14 |

**Why it matters:** Stale data means autonomous collection isn't running or is failing silently.

### Data Quality Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| `espn_data.completeness_pct` | ≥ 95% | 90-95% | < 90% |
| `espn_data.gap_days_count` | 0 | 1-3 | > 3 |
| `espn_data.small_files_count` | < 10 | 10-50 | > 50 |

**Why it matters:** Quality issues indicate API problems, rate limiting, or incomplete responses.

---

## Troubleshooting Common Issues

### Issue 1: Scraper Didn't Run (last_update_hours > 24)

**Diagnosis:**
```bash
# Check if scheduled task ran
grep "ESPN SCHEDULED SCRAPER" logs/autonomous/espn_scheduled_*.log | tail -5

# Check cron is configured
crontab -l | grep espn
```

**Solution:**
```bash
# Run manually to test
bash scripts/autonomous/run_scheduled_espn.sh "--days 3"

# If manual works, check cron configuration
# Expected cron entry:
# 0 2 * * * cd /Users/ryanranft/nba-simulator-aws && bash scripts/autonomous/run_scheduled_espn.sh

"--days 3" >> logs/autonomous/cron_espn.log 2>&1
```

### Issue 2: Completeness < 95%

**Diagnosis:**
```bash
# Check for gaps
python scripts/autonomous/autonomous_cli.py reconcile

# View ESPN gaps
cat inventory/gaps.json | jq '.[] | select(.source=="espn") | {date, data_type, priority}'
```

**Solution:**
```bash
# Run backfill for last 7 days
python scripts/etl/espn_incremental_async.py --days 7

# Then update DIMS
python scripts/monitoring/dims_cli.py update --category espn_data
```

### Issue 3: High Error Rate in Logs

**Diagnosis:**
```bash
# Check for HTTP errors
grep -i "error\|failed" logs/autonomous/espn_scheduled_*.log | tail -20
```

**Common causes:**
- **HTTP 429 (Rate Limited):** Wait 60 seconds, scraper has exponential backoff
- **HTTP 500 (Server Error):** ESPN API down, retry later
- **HTTP 403 (Forbidden):** User agent blocked, check `user_agent` in config
- **Connection timeout:** Network issue, check internet connectivity

**Solution:**
```bash
# Manual test with dry-run
python scripts/etl/espn_incremental_async.py --days 1 --dry-run

# Check config
grep -A 5 "espn_incremental_simple:" config/scraper_config.yaml
```

### Issue 4: Small Files Count > 50

**Diagnosis:**
```bash
# Find small files
aws s3 ls s3://nba-sim-raw-data-lake/espn_play_by_play/ --recursive | \
  awk '$3 < 1024 {print $4, $3}' | tail -20
```

**Meaning:** Files < 1KB are likely incomplete or error responses.

**Solution:**
```bash
# Re-scrape recent days
python scripts/etl/espn_incremental_async.py --days 7

# Validate files
aws s3 cp s3://nba-sim-raw-data-lake/espn_play_by_play/[filename] - | jq .
```

---

## Performance Baselines

### Async Scraper Performance (Production)

| Metric | Expected Value | Alert If |
|--------|----------------|----------|
| Runtime (1 day) | 25-30 seconds | > 60 seconds |
| Runtime (3 days) | 60-90 seconds | > 180 seconds |
| Success rate | 100% | < 95% |
| Requests/sec | 0.5-0.6 | < 0.3 |

**Performance gain over legacy:** 26% faster (async: 26.7s vs legacy: 36.2s for 1 day)

### Resource Usage

| Resource | Normal | High | Critical |
|----------|--------|------|----------|
| CPU | < 10% | 10-50% | > 50% |
| Memory | < 200 MB | 200-500 MB | > 500 MB |
| Network | < 1 MB/s | 1-5 MB/s | > 5 MB/s |

---

## Manual Intervention Procedures

### Procedure 1: Manual Scrape for Specific Date

```bash
# Edit ESPN scraper to target specific date
# Or use date range calculation:
DAYS_AGO=7  # e.g., scrape exactly 7 days ago
python scripts/etl/espn_incremental_async.py --days 1

# Verify upload
aws s3 ls s3://nba-sim-raw-data-lake/espn_play_by_play/ --recursive | \
  grep "$(date -v-${DAYS_AGO}d +%Y%m%d)"
```

### Procedure 2: Force DIMS Metrics Update

```bash
# Update ESPN metrics only
python scripts/monitoring/dims_cli.py update --category espn_data

# Update all metrics
python scripts/monitoring/dims_cli.py update --category all

# Verify update
python scripts/monitoring/dims_cli.py show --category espn_data
```

### Procedure 3: Clear and Rebuild Gap Queue

```bash
# Backup current gaps
cp inventory/gaps.json inventory/gaps_backup_$(date +%Y%m%d_%H%M%S).json

# Run fresh reconciliation
python scripts/autonomous/autonomous_cli.py reconcile

# Check new gaps
cat inventory/gaps.json | jq '.[] | select(.source=="espn") | length'
```

### Procedure 4: Emergency Stop

```bash
# Stop autonomous loop (if running)
python scripts/autonomous/autonomous_cli.py stop

# Kill any running scrapers
pkill -f "espn_incremental"

# Check no processes remain
ps aux | grep espn_incremental
```

---

## Cost Tracking

### S3 Storage Costs

**Current ESPN data:**
- Size: ~1.47 GB (as of Nov 6, 2025)
- Files: ~80,677 files (pbp + boxscore + schedule + team_stats)
- Monthly cost: $1.47 GB × $0.023/GB ≈ **$0.03/month**

**Projected growth:**
- Daily: +30-45 MB (10-15 games × 3 file types × ~690 KB avg)
- Monthly: +0.9-1.35 GB
- Annual: +11-16 GB

**5-year projection:**
- Total size: ~75-80 GB ESPN data
- Monthly cost: ~$1.75-1.85/month

### Request Costs

**ESPN API requests:**
- Free (no AWS costs, just rate limiting)
- Daily: ~30-45 requests (schedules + games)
- Rate limit: 0.5 req/sec = 1,800 req/hour = safe margin

---

## Alerts & Notifications

### When to Alert

**Critical (immediate action):**
- Completeness < 90%
- Gap days > 3
- Scraper failed 3 consecutive days
- last_update_hours > 72

**Warning (check within 24h):**
- Completeness 90-95%
- Gap days 1-3
- Scraper failed 1-2 times
- last_update_hours 24-48

**Info (monitor):**
- Small files > 10
- Success rate < 100%
- Runtime > baseline + 50%

---

## Advanced: Debugging Failed Scrapes

### Step 1: Isolate the Issue

```bash
# Test network connectivity
curl -I https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard

# Test with minimal request
curl "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20251106&limit=1" | jq .
```

### Step 2: Check Configuration

```bash
# Verify config structure
python3 -c "import yaml; print(yaml.safe_load(open('config/scraper_config.yaml'))['espn_incremental_simple'])"

# Verify rate limits
python3 -c "import yaml; config=yaml.safe_load(open('config/autonomous_config.yaml')); print(f\"Rate limit: {config['rate_limiting']['source_limits']['espn']['requests_per_minute']} req/min\")"
```

### Step 3: Test Scraper in Isolation

```bash
# Dry run (no S3 uploads)
python scripts/etl/espn_incremental_async.py --days 1 --dry-run

# Single day, verbose logging
python scripts/etl/espn_incremental_async.py --days 1 2>&1 | tee espn_test.log

# Check for errors
grep -i "error\|exception\|failed" espn_test.log
```

---

## Reference: Scheduled Task Configuration

**Cron entry (2 AM daily):**
```cron
0 2 * * * cd /Users/ryanranft/nba-simulator-aws && bash scripts/autonomous/run_scheduled_espn.sh "--days 3" >> logs/autonomous/cron_espn.log 2>&1
```

**Autonomous config (`config/autonomous_config.yaml`):**
```yaml
scheduled_tasks:
  enabled: true
  daily_espn_scrape:
    enabled: true
    schedule: "0 2 * * *"
    script: "scripts/etl/espn_incremental_async.py"
    args: ["--days", "3"]
    priority: HIGH
    timeout_minutes: 60
    retry_on_failure: true
    max_retries: 3
    post_execution:
      trigger_dims_update: true
      trigger_reconciliation: true
      metric_category: espn_data
```

---

## Quick Diagnostics Script

Save as `scripts/monitoring/espn_health_check.sh`:

```bash
#!/bin/bash
echo "=== ESPN Data Health Check ==="
echo ""
echo "1. Last update:"
python scripts/monitoring/dims_cli.py show --category espn_data | grep last_update_hours
echo ""
echo "2. Completeness:"
python scripts/monitoring/dims_cli.py show --category espn_data | grep completeness_pct
echo ""
echo "3. Gap count:"
python scripts/monitoring/dims_cli.py show --category espn_data | grep gap_days_count
echo ""
echo "4. File counts:"
python scripts/monitoring/dims_cli.py show --category espn_data | grep file_count
echo ""
echo "5. Recent scraper runs:"
ls -lt logs/autonomous/espn_scheduled_*.log | head -3
echo ""
echo "6. Critical gaps:"
cat inventory/gaps.json | jq '[.[] | select(.source=="espn" and .priority=="CRITICAL")] | length'
echo ""
echo "=== Health Check Complete ==="
```

---

## Support & Resources

**Documentation:**
- ADCE Master Index: `docs/automation/ADCE_MASTER_INDEX.md`
- ESPN Integration Handoff: `docs/ESPN_ADCE_INTEGRATION_SESSION_HANDOFF.md`
- Autonomous Config: `config/autonomous_config.yaml`
- Scraper Config: `config/scraper_config.yaml`

**Logs:**
- Scheduled runs: `logs/autonomous/espn_scheduled_*.log`
- DIMS updates: `logs/dims_updates.log`
- Reconciliation: `logs/reconciliation.log`
- Autonomous loop: `logs/autonomous_loop.log`

**Contact:**
- Project: NBA Simulator AWS
- Repository: https://github.com/ryanranft/nba-simulator-aws
- Phase: 0.0001 - Active Data Collection

---

**Last Updated:** November 6, 2025
**Version:** 1.0 (Production)
**Integration Status:** ESPN + ADCE + DIMS Complete

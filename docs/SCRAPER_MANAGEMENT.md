# Scraper Management Guide

**Last Updated:** October 13, 2025
**Status:** Active - 5 scrapers implemented + NEW ASYNC INFRASTRUCTURE

This guide provides centralized documentation for all NBA data scraping operations.

## 🚀 NEW: Async Scraping Infrastructure (October 2025)

**Major Update:** Complete async scraping infrastructure implemented with modern patterns:

### New Components
- **AsyncBaseScraper** (`scripts/etl/async_scraper_base.py`) - Modern async base class
- **ScraperErrorHandler** (`scripts/etl/scraper_error_handler.py`) - Centralized error management
- **ScraperTelemetry** (`scripts/etl/scraper_telemetry.py`) - Monitoring and metrics
- **ScraperConfig** (`scripts/etl/scraper_config.py`) - YAML-based configuration
- **ESPNAsyncScraper** (`scripts/etl/espn_async_scraper.py`) - Migrated ESPN scraper

### Key Improvements
- **3-5x faster** scraping with async concurrency
- **Smart retry strategies** based on error type
- **Circuit breaker pattern** for failing endpoints
- **Real-time telemetry** and health monitoring
- **Centralized configuration** management
- **Comprehensive error handling** with custom exceptions

### Quick Start with New Infrastructure
```bash
# Install new dependencies
pip install aiohttp aiofiles asyncio-throttle prometheus-client

# Run ESPN async scraper
python scripts/etl/espn_async_scraper.py --days-back 7

# Run with specific seasons (missing PBP data)
python scripts/etl/espn_async_scraper.py --seasons 2022-23 2023-24 2024-25

# Dry run mode
python scripts/etl/espn_async_scraper.py --dry-run

# Deploy with Docker (see Workflow #53)
bash scripts/deployment/docker_deploy.sh start
```

### Configuration
All scrapers now use `config/scraper_config.yaml`:
```yaml
scrapers:
  espn:
    base_url: "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
    rate_limit:
      requests_per_second: 1.0
      adaptive: true
    retry:
      max_attempts: 3
      exponential_backoff: true
    storage:
      s3_bucket: "nba-sim-raw-data-lake"
      deduplication: true
```

### Testing
```bash
# Run comprehensive test suite
python -m pytest tests/test_async_scrapers.py -v

# Test specific components
python -m pytest tests/test_async_scrapers.py::TestAsyncBaseScraper -v
python -m pytest tests/test_async_scrapers.py::TestScraperErrorHandler -v
```

---

## Table of Contents

1. [Available Scrapers](#available-scrapers)
2. [Quick Reference Commands](#quick-reference-commands)
3. [Monitoring Tools](#monitoring-tools)
4. [Decision Tree: Which Scraper to Run](#decision-tree-which-scraper-to-run)
5. [Rate Limit Best Practices](#rate-limit-best-practices)
6. [Troubleshooting](#troubleshooting)
7. [Related Workflows](#related-workflows)

---

## Available Scrapers

### 1. Basketball Reference (Primary Historical Source)
**Script:** `scripts/etl/scrape_bbref_incremental.sh`
**Python:** `scripts/etl/scrape_basketball_reference_complete.py`
**Coverage:** 1950-2025 (75 NBA seasons)
**Rate Limit:** 5 seconds between requests
**Data Types:** 7 (schedules, season-totals, advanced-totals, standings, player-box-scores, team-box-scores, play-by-play)

**Usage:**
```bash
# Recent seasons (recommended first)
bash scripts/etl/scrape_bbref_incremental.sh 2020 2025

# Historical seasons
bash scripts/etl/scrape_bbref_incremental.sh 2010 2019
bash scripts/etl/scrape_bbref_incremental.sh 2000 2009
bash scripts/etl/scrape_bbref_incremental.sh 1950 1999
```

**Features:**
- ✅ Incremental scraping (one season at a time)
- ✅ Resume capability (completion markers)
- ✅ S3 upload after each season
- ✅ 7 data types per season
- ✅ Play-by-play data (2000+)

### 2. hoopR (ESPN API - Modern Era)
**Script:** `scripts/etl/run_hoopr_phase1b.sh`
**R Script:** `scripts/etl/scrape_hoopr_phase1b_only.R`
**Coverage:** 2002-2025 (24 seasons)
**Rate Limit:** ESPN API managed by hoopR library
**Data Types:** League dashboards, player stats, team stats, standings

**Usage:**
```bash
# Phase 1B: League dashboards
bash scripts/etl/run_hoopr_phase1b.sh
```

**Features:**
- ✅ CSV output format
- ✅ S3 upload enabled
- ✅ Modern era advanced stats (2013+)
- ✅ Complementary to Basketball Reference

### 3. NBA API (Official NBA Stats)
**Script:** `scripts/etl/overnight_nba_api_comprehensive.sh`
**Python:** `scripts/etl/scrape_nba_api_comprehensive.py`
**Coverage:** 1996-2025 (30 seasons)
**Rate Limit:** 0.6 seconds (600ms)
**Data Types:** Advanced box scores, player tracking, shot charts

**Usage:**
```bash
# Comprehensive scrape (Tier 1 endpoints)
bash scripts/etl/overnight_nba_api_comprehensive.sh
```

**Status:** ⚠️ High error rate - needs error handling improvements

### 4. SportsDataverse (Multi-Sport Data)
**Script:** ~~`scripts/archive/deprecated/scrape_sportsdataverse.py`~~ - ❌ ARCHIVED
**Coverage:** 2002+ seasons
**Status:** Archived (redundant with hoopR Phase 1B)
**Alternative:** Use `scripts/etl/run_hoopr_phase1b.sh` instead

### 5. Kaggle (Historical Datasets)
**Script:** `scripts/etl/download_kaggle_basketball.py`
**Coverage:** Pre-packaged historical data
**Status:** Downloaded and archived

---

## Quick Reference Commands

### Starting Scrapers

```bash
# Basketball Reference (recommended starting point)
bash scripts/etl/scrape_bbref_incremental.sh 2020 2025

# hoopR (can run simultaneously)
bash scripts/etl/run_hoopr_phase1b.sh

# Run in background with nohup
nohup bash scripts/etl/scrape_bbref_incremental.sh 2020 2025 > /tmp/bbref.log 2>&1 &
```

### Monitoring Scrapers

```bash
# Quick status check (single update)
bash scripts/monitoring/monitor_scrapers_inline.sh

# Live tracking in conversation (10 updates every 30s)
bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 10

# Continuous monitoring (until Ctrl+C)
bash scripts/monitoring/monitor_scrapers_inline.sh --iterations -1

# Full-screen dashboard (auto-refreshing)
bash scripts/monitoring/monitor_scrapers.sh --watch
```

### Checking Progress

```bash
# Basketball Reference completion markers
ls /tmp/basketball_reference_incremental/*.complete | wc -l

# hoopR CSV file count
find /tmp/hoopr_phase1 -name "*.csv" | wc -l

# View logs
tail -f /tmp/bbref_incremental_2020-2025.log
tail -f /tmp/hoopr_phase1b.log
```

### Stopping Scrapers

```bash
# Find scraper PIDs
ps aux | grep scrape

# Kill specific scraper
kill <PID>

# Kill all scrapers (use with caution)
pkill -f "scrape_"
```

---

## Monitoring Tools

### 1. Inline Conversation Monitor
**Script:** `scripts/monitoring/monitor_scrapers_inline.sh`
**Best For:** Tracking progress within Claude conversation

**Features:**
- Shows updates inline (no screen clearing)
- Displays completed vs in-progress tasks
- Tracks runtime and errors
- Configurable iterations and intervals

**Use Cases:**
- Quick status checks during conversation
- Monitoring overnight job progress next morning
- Watching specific milestone completions

**Example Output:**
```
════════════════════════════════════════════════════════════════════════════════
🔍 Scraper Status Update #1 - 2025-10-08 12:00:00
════════════════════════════════════════════════════════════════════════════════
✅ Active Scrapers: 2

────────────────────────────────────────────────────────────────────────────────
[1] 🔧 Basketball Reference (PID: 46509)
    ⏱️  Runtime: 20m 15s
    ⚠️  Errors: 0
    ✅ Completed: 2 seasons | 🔄 Current: Season 2022 (4/7) → player-box-scores
────────────────────────────────────────────────────────────────────────────────
[2] 🔧 hoopR (PID: 48346)
    ⏱️  Runtime: 17m 30s
    ⚠️  Errors: 0
    ✅ Completed: 15/24 seasons | 🔄 Current: 2017-18 | 📁 Files: 248
════════════════════════════════════════════════════════════════════════════════
```

### 2. Full-Screen Dashboard
**Script:** `scripts/monitoring/monitor_scrapers.sh`
**Best For:** Extended monitoring sessions, deep dives

**Features:**
- Detailed progress breakdown per scraper
- Lists all completed tasks
- Shows current task with real-time updates
- Error detection with context
- Auto-refreshing watch mode

**Use Cases:**
- Long-running overnight scrapes
- Debugging scraper issues
- Detailed progress analysis
- Terminal-based monitoring

**Example Output:**
```
================================================================================
[1] Basketball Reference
================================================================================
  PID:        46509
  Runtime:    20m 15s
  Progress:   17 / 42 tasks
  Errors:     0
  Log:        /tmp/bbref_incremental_2020-2025.log

  Detailed Progress:
  ✅ Completed Seasons:
     • 2020 (all 7 data types)
     • 2021 (all 7 data types)

  🔄 Current Season: 2022
     Completed:
       ✓ schedules
       ✓ season-totals
       ✓ advanced-totals
       ✓ standings
     ⏳ Working on: player-box-scores
```

### 3. Manual Log Monitoring
**Best For:** Debugging specific issues

```bash
# Follow log in real-time
tail -f /tmp/bbref_incremental_2020-2025.log

# Search for errors
grep -i error /tmp/bbref_incremental_2020-2025.log

# Check last 100 lines
tail -100 /tmp/hoopr_phase1b.log

# Count successes
grep -c "✓" /tmp/bbref_incremental_2020-2025.log
```

### Monitoring Tool Comparison

| Feature | Inline Monitor | Dashboard | Manual Logs |
|---------|---------------|-----------|-------------|
| Live updates | ✅ | ✅ | ✅ |
| In conversation | ✅ | ❌ | ❌ |
| Detailed breakdown | ⚠️ Summary | ✅ Full | ✅ Full |
| Multiple scrapers | ✅ | ✅ | ❌ One at a time |
| Error context | ⚠️ Count only | ✅ Recent lines | ✅ Full details |
| Best for | Quick checks | Extended monitoring | Debugging |

---

## Decision Tree: Which Scraper to Run

### Starting Fresh Data Collection?
**→ Basketball Reference (recent seasons first)**
- Most comprehensive historical data
- 7 data types per season
- Start with 2020-2025 for testing
- Expand to earlier years once validated

### Need Modern Advanced Stats (2013+)?
**→ hoopR Phase 1B**
- Complementary to Basketball Reference
- ESPN API data (different source)
- Player tracking, lineups, hustle stats
- Can run simultaneously with Basketball Reference

### Need Official NBA.com Stats?
**→ NBA API Comprehensive**
- Advanced box scores
- Player tracking metrics
- Shot charts and locations
- ⚠️ Currently has error rate issues

### When to Run Multiple Scrapers

**✅ Safe to Run Simultaneously:**
- Basketball Reference + hoopR (different APIs)
- Any scraper + monitoring tools

**⚠️ Avoid Running Together:**
- Multiple Basketball Reference instances (rate limit conflicts)
- NBA API + any other stats.nba.com scraper

---

## Rate Limit Best Practices

### Basketball Reference
**Current Settings:** 5 seconds between requests
- **Too fast:** 3 seconds → 429 errors every request
- **Optimal:** 5 seconds → 0 errors in testing
- **Backoff:** 30s/60s/120s for 429 errors

**Estimated Runtimes:**
- Schedules/totals/standings: ~7 minutes per 79 seasons
- Player box scores: ~132 hours for 79 seasons
- Team box scores: ~132 hours for 79 seasons
- Play-by-play: ~43 hours for 26 seasons (2000+)

**Incremental Strategy:**
- Run recent seasons first (2020-2025)
- Validate data quality
- Then expand to historical seasons
- Use completion markers for resume capability

### NBA API
**Current Settings:** 0.6 seconds (600ms)
- Official NBA.com rate limit
- Connection timeout issues observed
- Needs error handling improvements

### hoopR
**Settings:** Managed by hoopR library
- No manual rate limiting required
- ESPN API handles internally
- Generally very reliable

---

## Troubleshooting

### Scraper Stalled (No Progress)

**Symptoms:**
- Monitoring shows no activity change
- Log file not updating
- Process still running (PID exists)

**Diagnosis:**
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

### High Error Rate

**Symptoms:**
- Monitoring shows errors > 100
- Log full of "error" or "failed" messages
- Data files smaller than expected

**Diagnosis:**
```bash
# Count errors in log
grep -c -i "error\|failed" /tmp/scraper.log

# See recent errors
grep -i "error\|failed" /tmp/scraper.log | tail -20

# Check specific error types
grep "429" /tmp/scraper.log  # Rate limit
grep "timeout" /tmp/scraper.log  # Connection issues
grep "404" /tmp/scraper.log  # Missing data
```

**Resolution:**
- **429 errors:** Increase rate limit (already at 5s for Basketball Reference)
- **Timeout errors:** Check internet connection, consider retry logic
- **404 errors:** Data may not exist for that season (expected for some years)

### Scraper Won't Start

**Symptoms:**
- Script exits immediately
- No process created
- Error message in terminal

**Common Causes:**
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

### Completion Markers Not Created

**Symptoms:**
- Scraper completes but markers missing
- Resume doesn't work (re-scrapes same data)

**Diagnosis:**
```bash
# Check marker directory
ls -lh /tmp/basketball_reference_incremental/*.complete

# Check permissions
ls -ld /tmp/basketball_reference_incremental/
```

**Resolution:**
```bash
# Manually create marker (if you verified data exists)
touch /tmp/basketball_reference_incremental/schedules_2020.complete
```

---

## Related Workflows

- **Workflow #38:** [Overnight Scraper Handoff Protocol](claude_workflows/workflow_descriptions/38_overnight_scraper_handoff.md)
- **Workflow #39:** [Scraper Monitoring Automation](claude_workflows/workflow_descriptions/39_scraper_monitoring_automation.md)
- **Workflow #40:** [Complete Scraper Operations Guide](claude_workflows/workflow_descriptions/40_scraper_operations_complete.md) *(pending)*

---

## S3 Upload Verification

**Check what's been uploaded:**
```bash
# Basketball Reference
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/

# hoopR
aws s3 ls s3://nba-sim-raw-data-lake/hoopr_phase1/

# NBA API
aws s3 ls s3://nba-sim-raw-data-lake/nba_api_comprehensive/
```

**Verify file counts:**
```bash
# Count local files
ls /tmp/basketball_reference_incremental/*.json | wc -l

# Count S3 files
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/ --recursive | wc -l
```

---

## Best Practices Checklist

**Before Starting Scrapers:**
- [ ] Check internet connection stability
- [ ] Verify S3 credentials (`aws s3 ls`)
- [ ] Ensure conda environment activated
- [ ] Check disk space (`df -h /tmp`)
- [ ] Review rate limit settings
- [ ] Start with recent seasons first

**While Scrapers Running:**
- [ ] Monitor progress every 30-60 minutes
- [ ] Check error counts (should be low)
- [ ] Verify log files updating
- [ ] Watch for 429 rate limit errors
- [ ] Ensure S3 uploads completing

**After Scraper Completes:**
- [ ] Verify completion markers created
- [ ] Check S3 upload success
- [ ] Count output files
- [ ] Review error log summary
- [ ] Document any issues encountered

---

*For additional help, see:*
- `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md`
- `docs/DATA_SOURCES.md`
- `CHANGELOG.md` (for scraper fixes and improvements)

# Scraper Systems Documentation

**Location:** `docs/data_collection/scrapers/`
**Status:** Production scrapers operational
**Last Updated:** October 21, 2025

---

## Overview

Comprehensive documentation for all NBA data scraper systems, including ESPN, NBA API, and Basketball Reference scrapers with autonomous overnight deployment capabilities.

---

## Documentation Index

### Scraper Guides

1. **[ESPN_SCRAPER_GUIDE.md](ESPN_SCRAPER_GUIDE.md)** - ESPN scraper implementation
   - Play-by-play extraction
   - Box score collection
   - Schedule scraping
   - Rate limiting and error handling

2. **[NBA_API_SCRAPER_OPTIMIZATION.md](NBA_API_SCRAPER_OPTIMIZATION.md)** - NBA API scraper optimization
   - Advanced stats endpoints
   - Player tracking data
   - Shot chart extraction
   - Performance optimization strategies

### Management & Operations

3. **[MANAGEMENT.md](MANAGEMENT.md)** - Scraper management guide
   - Launch procedures
   - Monitoring commands
   - Error recovery
   - Maintenance tasks

4. **[MONITORING_SYSTEM.md](MONITORING_SYSTEM.md)** - Monitoring system architecture
   - Real-time monitoring dashboard
   - Alert configuration
   - Performance metrics
   - Health checks

5. **[DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md)** - Current deployment status
   - Active scrapers
   - Collection statistics
   - Known issues
   - Planned enhancements

### Autonomous Deployment

6. **[ASYNC_DEPLOYMENT_CHECKLIST.md](ASYNC_DEPLOYMENT_CHECKLIST.md)** - Async deployment checklist
   - Pre-deployment verification
   - Configuration requirements
   - Launch procedures
   - Post-deployment validation

7. **[AUTONOMOUS_OVERNIGHT_DEPLOYMENT_GUIDE.md](AUTONOMOUS_OVERNIGHT_DEPLOYMENT_GUIDE.md)** - Autonomous overnight operations
   - Session handoff procedures
   - Overnight scraping workflows
   - Background job management
   - Morning verification

### Test Results

8. **[test_results/](test_results/)** - Scraper test results
   - **[FINAL_100_PERCENT.md](test_results/FINAL_100_PERCENT.md)** - 100% success rate achievement
   - **[20251017_TEST_RESULTS.md](test_results/20251017_TEST_RESULTS.md)** - October 2025 validation

---

## Quick Start

### Launch Scrapers

```bash
# Launch ESPN scraper
bash scripts/monitoring/launch_scraper.sh espn

# Launch NBA API scraper
bash scripts/monitoring/launch_scraper.sh nba_api

# Launch all scrapers
bash scripts/monitoring/launch_all_scrapers.sh
```

### Monitor Scrapers

```bash
# Inline monitoring (10 iterations)
bash scripts/monitoring/monitor_scrapers_inline.sh --iterations 10

# Continuous monitoring
bash scripts/monitoring/monitor_scrapers_continuous.sh
```

### Check Status

```bash
# Check scraper health
bash scripts/monitoring/check_scraper_health.sh

# View logs
tail -f scripts/monitoring/logs/scraper_*.log
```

---

## Scraper Architecture

### ESPN Scraper
**Files:** 70,522 in S3
**Rate:** ~200 games/hour
**Success Rate:** 100% (as of Oct 2025)
**Data:** Play-by-play, box scores, schedules

### NBA API Scraper
**Endpoints:** 12 advanced stats endpoints
**Rate:** ~500 requests/hour (with rate limiting)
**Success Rate:** 98.5%
**Data:** Player tracking, shot charts, advanced metrics

### Basketball Reference Scraper
**See:** [Phase 0.1 Documentation](../../phases/phase_0/0.1_basketball_reference/)
**Tiers:** 13 tiers, 234 data types
**Estimated Time:** 140-197 hours
**Status:** Ready to implement

---

## Monitoring Dashboard

**Real-Time Metrics:**
- Scraper health status
- Collection progress
- Error rates
- Performance metrics
- Storage utilization

**Access:**
```bash
python scripts/monitoring/launch_monitoring_dashboard.py
# View at: http://localhost:8050
```

---

## Autonomous Operations

### Overnight Workflow (Workflow #38)

**Procedure:**
1. Pre-deployment checklist
2. Session handoff document
3. Launch background scrapers
4. Morning verification
5. Data validation

**Files:**
- `AUTONOMOUS_OVERNIGHT_DEPLOYMENT_GUIDE.md`
- `docs/archive/session_handoffs/SESSION_HANDOFF_*.md`

---

## Success Metrics

**As of October 2025:**
- ✅ **100% success rate** on ESPN scraper
- ✅ **98.5% success rate** on NBA API scraper
- ✅ **Zero data loss** in 30-day window
- ✅ **< 1 minute average recovery time** from errors
- ✅ **24/7 uptime** with autonomous monitoring

---

## Troubleshooting

**Common Issues:**

1. **Rate Limiting** - See `MANAGEMENT.md` section 4
2. **Authentication Errors** - Check credentials in `nba-sim-credentials.env`
3. **Network Timeouts** - Adjust timeout settings in scraper config
4. **Disk Space** - Monitor with `MONITORING_SYSTEM.md` alerts

**Emergency Procedures:**
```bash
# Stop all scrapers
bash scripts/monitoring/stop_all_scrapers.sh

# Clear error state
bash scripts/monitoring/reset_scraper_state.sh

# Restart with error recovery
bash scripts/monitoring/launch_scraper.sh --recovery-mode
```

---

## Related Workflows

- **[Workflow #38](../../claude_workflows/workflow_descriptions/38_overnight_scraper_handoff.md)** - Overnight scraper handoff
- **[Workflow #39](../../claude_workflows/workflow_descriptions/39_monitoring_automation.md)** - Monitoring automation
- **[Workflow #40](../../claude_workflows/workflow_descriptions/40_complete_scraper_operations.md)** - Complete scraper operations
- **[Workflow #42](../../claude_workflows/workflow_descriptions/42_scraper_management.md)** - Scraper management

---

## Navigation

**Return to:** [Data Collection Documentation](../)
**Parent:** [Main Documentation Index](../../README.md)
**Related:**
- [Phase 0: Data Collection](../../phases/PHASE_0_INDEX.md)
- [Monitoring Systems](../../monitoring/)

---

**Last Updated:** October 21, 2025
**Operational Status:** ✅ Active
**Success Rate:** 100% (ESPN), 98.5% (NBA API)

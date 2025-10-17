# Master Data Collection Execution Plan

**Created:** October 17, 2025
**Goal:** Collect ALL remaining NBA data (1946-2025)
**Status:** 🚀 Ready to Execute

---

## Executive Summary

**Current Holdings:** 172,600 files (118.3 GB)
**Current Coverage:** 1993-2025 (33 seasons)
**Target Coverage:** 1946-2025 (79 seasons)
**Missing:** 46 historical seasons + additional endpoints

**Total Remaining Work:**
- 8 phases from REMAINING_DATA_COLLECTION_PLAN.md
- Historical data collection (1946-1992)
- Estimated runtime: 70-90 hours
- Estimated API calls: ~100,000

---

## Phase Overview

### Part A: Modern Era Expansion (2014-2025)
**Priority:** HIGHEST - Most features for ML
**Runtime:** 51-67 hours
**Phases:** 1-8 from REMAINING_DATA_COLLECTION_PLAN.md

### Part B: Historical Era Collection (1946-1992)
**Priority:** HIGH - Complete temporal coverage
**Runtime:** 20-30 hours
**Sources:** Basketball Reference + Kaggle validation

---

## Part A: Modern Era (Detailed from REMAINING_DATA_COLLECTION_PLAN.md)

### Phase 1: NBA API Player Dashboards (Priority 1) ⭐
**Impact:** HIGHEST (30-40 features)
**Runtime:** 8-10 hours
**API Calls:** 21,000

**Endpoints (7):**
1. playerdashboardbyclutch
2. playerdashboardbygeneralsplits
3. playerdashboardbyopponent
4. playerdashboardbyshootingsplits
5. playerdashboardbylastngames
6. playerdashboardbyteamperformance
7. playerdashboardbyyearoveryear

**Deployment:**
```bash
nohup python scripts/etl/scrape_nba_api_player_dashboards.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_player_dashboards \
    > logs/nba_api_player_dashboards.log 2>&1 &
```

**Status:** 🔵 Ready to deploy

---

### Phase 2: NBA API Player Tracking (Priority 2) ⭐
**Impact:** HIGH (20-30 features)
**Runtime:** 10-12 hours
**API Calls:** 24,000

**Endpoints (4):**
1. playerdashptpass (passing stats)
2. playerdashptreb (rebounding)
3. playerdashptshotdefend (shot defense)
4. playerdashptshots (shot tracking)

**Coverage:** 2014-2025 (SportVU era only)

**Deployment:**
```bash
nohup python scripts/etl/scrape_nba_api_player_tracking.py \
    --start-season 2014 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_player_tracking \
    > logs/nba_api_player_tracking.log 2>&1 &
```

**Status:** 🟡 Needs fixing (nba_api dependency issue)

---

### Phase 3: NBA API Team Dashboards (Priority 3)
**Impact:** HIGH (30-40 features)
**Runtime:** 1 hour
**API Calls:** 1,980

**Endpoints (11):**
1. teamdashboardbyclutch
2. teamdashboardbygeneralsplits
3. teamdashboardbyopponent
4. teamdashboardbyshootingsplits
5. teamdashboardbylastngames
6. teamdashboardbyteamperformance
7. teamdashboardbyyearoveryear
8. teamdashlineups
9. teamdashptpass
10. teamdashptreb
11. teamdashptshots

**Deployment:**
```bash
nohup python scripts/etl/scrape_nba_api_team_dashboards.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_team_dashboards \
    > logs/nba_api_team_dashboards.log 2>&1 &
```

**Status:** 🔵 Ready to deploy

---

### Phase 4: NBA API Game-Level Stats (Priority 4)
**Impact:** MEDIUM (10-15 features)
**Runtime:** 12-15 hours
**API Calls:** 29,520

**Endpoints (4):**
1. gamerotation (rotation patterns)
2. winprobabilitypbp (win probability)
3. boxscoresimilarityscore (game similarity)
4. videodetails (video metadata)

**Deployment:**
```bash
nohup python scripts/etl/scrape_nba_api_game_advanced.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_game_advanced \
    > logs/nba_api_game_advanced.log 2>&1 &
```

**Status:** 🔵 Ready to deploy

---

### Phase 5: NBA API Matchups & Defense (Priority 5)
**Impact:** MEDIUM (15-20 features)
**Runtime:** 6-8 hours
**API Calls:** ~15,000

**Endpoints (5):**
1. leaguedashplayerptshot
2. leaguedashplayershotlocations
3. leaguedashteamptshot
4. leaguedashteamshotlocations
5. boxscorematchups

**Deployment:**
```bash
nohup python scripts/etl/scrape_nba_api_matchups_defense.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_matchups_defense \
    > logs/nba_api_matchups_defense.log 2>&1 &
```

**Status:** 🔵 Ready to deploy

---

### Phase 6: Basketball Reference Workaround (Priority 6)
**Impact:** MEDIUM (47 features)
**Runtime:** 8-12 hours
**Challenge:** 403 Forbidden errors

**Data:**
- TS%, PER, BPM, Win Shares
- Four Factors
- Advanced statistics

**Deployment:**
```bash
nohup python scripts/etl/scrape_basketball_reference_fixed.py \
    --start-year 2016 \
    --end-year 2025 \
    --rate-limit 30.0 \
    --output-dir /tmp/bbref_real \
    > logs/bbref_real.log 2>&1 &
```

**Status:** 🟡 Needs workaround for 403 errors

---

### Phase 7: Basketball Reference Additional (Priority 7)
**Impact:** LOW (30-43 features)
**Runtime:** 4-6 hours

**Functions (9):**
- get_player_splits()
- get_player_headshot()
- get_game_logs()
- get_opp_stats()
- get_team_misc()
- get_team_ratings()
- get_roster_stats()
- get_standings()
- lookup()

**Deployment:**
```bash
nohup python scripts/etl/scrape_basketball_reference_additional.py \
    --start-year 2016 \
    --end-year 2025 \
    --output-dir /tmp/bbref_additional \
    > logs/bbref_additional.log 2>&1 &
```

**Status:** 🔵 Ready to deploy

---

### Phase 8: ESPN Additional Endpoints (Priority 8)
**Impact:** LOW (10-15 features)
**Runtime:** 2-3 hours

**Endpoints (7):**
- espn_nba_calendar()
- espn_nba_game_rosters()
- espn_nba_teams()
- load_nba_pbp() (hoopR)
- load_nba_player_boxscore() (hoopR)
- load_nba_team_boxscore() (hoopR)
- load_nba_schedule() (hoopR)

**Deployment:**
```bash
nohup python scripts/etl/scrape_espn_additional.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/espn_additional \
    > logs/espn_additional.log 2>&1 &
```

**Status:** 🔵 Ready to deploy

---

## Part B: Historical Era Collection (1946-1992)

### Phase 9: Historical Box Scores (1946-1992)
**Impact:** HIGH - Complete temporal coverage
**Runtime:** 15-20 hours
**Sources:** Basketball Reference + Kaggle validation

**Data to Collect:**
- Game results (all ~50,000 games)
- Player box scores (where available)
- Team statistics
- Season standings

**Challenges:**
- Limited play-by-play data (mostly unavailable before 2000)
- Box score detail increases over time
- Need to work around Basketball Reference blocking

**Deployment:**
```bash
nohup python scripts/etl/scrape_historical_1946_1992.py \
    --start-year 1946 \
    --end-year 1992 \
    --output-dir /tmp/historical_nba \
    > logs/historical_collection.log 2>&1 &
```

**Status:** 🟡 Needs script creation

---

### Phase 10: Kaggle Database Integration
**Impact:** MEDIUM - Validation source
**Runtime:** 2-3 hours

**Data Available:**
- 65,698 historical games
- 4,815 players
- Play-by-play (limited)
- Box scores

**Action:**
```bash
python scripts/etl/integrate_kaggle_data.py \
    --kaggle-db data/kaggle/nba.sqlite \
    --output-dir /tmp/kaggle_integration \
    > logs/kaggle_integration.log 2>&1
```

**Status:** 🔵 Ready to implement

---

## Deployment Strategy

### Week 1: High-Impact Modern Data (Phases 1-3)

**Day 1-2:**
```bash
# Launch Phase 1 (Player Dashboards) - 8-10 hours
nohup python scripts/etl/scrape_nba_api_player_dashboards.py ... &

# Monitor
tail -f logs/nba_api_player_dashboards.log
```

**Day 3:**
```bash
# Fix and launch Phase 2 (Player Tracking) - 10-12 hours
# First fix the dependency issue
pip install --upgrade nba_api

# Then launch
nohup python scripts/etl/scrape_nba_api_player_tracking.py ... &
```

**Day 4:**
```bash
# Launch Phase 3 (Team Dashboards) - 1 hour
nohup python scripts/etl/scrape_nba_api_team_dashboards.py ... &
```

---

### Week 2: Medium-Impact Modern Data (Phases 4-5)

**Day 1-2:**
```bash
# Launch Phase 4 (Game-Level Stats) - 12-15 hours
nohup python scripts/etl/scrape_nba_api_game_advanced.py ... &
```

**Day 3:**
```bash
# Launch Phase 5 (Matchups & Defense) - 6-8 hours
nohup python scripts/etl/scrape_nba_api_matchups_defense.py ... &
```

---

### Week 3: Basketball Reference & Historical (Phases 6-10)

**Day 1-2:**
```bash
# Fix and launch Phase 6 (Basketball Reference) - 8-12 hours
python scripts/etl/scrape_basketball_reference_fixed.py --test-mode
# If successful:
nohup python scripts/etl/scrape_basketball_reference_fixed.py ... &
```

**Day 3:**
```bash
# Launch Phase 7 (BB-Ref Additional) - 4-6 hours
nohup python scripts/etl/scrape_basketball_reference_additional.py ... &
```

**Day 4:**
```bash
# Launch Phase 8 (ESPN Additional) - 2-3 hours
nohup python scripts/etl/scrape_espn_additional.py ... &
```

**Day 5-7:**
```bash
# Launch Phase 9 (Historical Collection) - 15-20 hours
nohup python scripts/etl/scrape_historical_1946_1992.py ... &

# Launch Phase 10 (Kaggle Integration) - 2-3 hours
python scripts/etl/integrate_kaggle_data.py ...
```

---

## Monitoring Commands

### Check Running Processes
```bash
# See all active scrapers
ps aux | grep python | grep etl | grep -v grep

# Count running scrapers
ps aux | grep python | grep etl | grep -v grep | wc -l
```

### Monitor Logs
```bash
# Tail all scraper logs
tail -f logs/*.log

# Check specific phase
tail -f logs/nba_api_player_dashboards.log

# Monitor errors
grep -i error logs/*.log

# Monitor progress
grep -i "progress\|complete\|success" logs/*.log
```

### Check Output
```bash
# Count files collected
ls -1 /tmp/nba_api_player_dashboards/ | wc -l
ls -1 /tmp/nba_api_player_tracking/ | wc -l

# Check disk usage
du -sh /tmp/nba_api_*
```

### Kill If Needed
```bash
# Kill specific scraper
pkill -f "scrape_nba_api_player_dashboards"

# Kill all scrapers
pkill -f "scripts/etl/"
```

---

## Expected Results

### Data Volume Increase
- **Current:** 172,600 files (118.3 GB)
- **After Phases 1-8:** ~350,000 files (~200 GB)
- **After Phases 9-10:** ~400,000 files (~220 GB)
- **Total increase:** +227,400 files (+101.7 GB)

### Feature Coverage
- **Current:** ~350 features
- **After completion:** ~485 features
- **Total increase:** +135 features (+38%)

### Temporal Coverage
- **Current:** 1993-2025 (33 seasons)
- **After completion:** 1946-2025 (79 seasons)
- **Historical games added:** ~50,000 games

### Coverage by Era
| Era | Games | Play-by-Play | Box Scores | Features |
|-----|-------|--------------|------------|----------|
| 1946-1992 | ~50,000 | ❌ Limited | ✅ Complete | Basic |
| 1993-1999 | ~10,000 | ❌ Metadata only | ✅ Complete | Basic |
| 2000-2013 | ~20,000 | ✅ Complete | ✅ Complete | Standard |
| 2014-2025 | ~15,000 | ✅ Complete | ✅ Complete | **Full (485)** |

---

## Risk Mitigation

### Rate Limiting
- Use 1.5-3.0s delays
- Implement exponential backoff
- Monitor for 429 errors
- Respect robots.txt

### API Blocking (Basketball Reference)
- Rotate user agents
- Increase rate limits (30-60s)
- Use persistent sessions
- Consider proxies if needed

### Data Quality
- Validate each response
- Check for null/empty data
- Log all errors
- Resume from checkpoints

### Disk Space
- Monitor /tmp usage
- Archive to S3 periodically
- Clean up after validation
- Keep 100GB free minimum

---

## Success Criteria

### Phases 1-8 Complete When:
✅ All 76,500 API calls successful
✅ All endpoint files collected
✅ No blocking/rate limit issues
✅ Data validated and uploaded to S3

### Phase 9-10 Complete When:
✅ Historical games (1946-1992) collected
✅ Kaggle data integrated
✅ Cross-source validation complete
✅ Documentation updated

### Full Project Complete When:
✅ Temporal coverage: 1946-2025 (79 seasons)
✅ Feature coverage: 485+ features
✅ Play-by-play: 2000-2025 (where available)
✅ Box scores: 1946-2025 (complete)
✅ All data in S3 and RDS
✅ Documentation complete

---

## Estimated Costs

### API Calls
- **Total:** ~100,000 calls
- **Cost:** $0 (all free public APIs)

### AWS S3 Storage
- **Additional:** ~100 GB
- **Monthly cost increase:** ~$2.30
- **New total:** ~$5/month

### AWS Data Transfer
- **Upload:** ~100 GB
- **One-time cost:** ~$0 (first GB free)

### Total Additional Cost
- **One-time:** $0
- **Monthly:** +$2.30
- **Annual:** +$27.60

---

## Next Steps

1. **Review this plan** and approve execution
2. **Prioritize phases** if not running all at once
3. **Create missing scripts** (Phases 9-10)
4. **Fix broken scripts** (Phase 2, 6)
5. **Deploy Phase 1** to start (highest impact)
6. **Monitor progress** daily
7. **Archive to S3** as phases complete

---

**Total Runtime:** 70-90 hours (3-4 days continuous, or 2-3 weeks at 8 hours/day)
**Total Value:** Complete NBA data coverage 1946-2025 with 485+ features
**Status:** 🚀 Ready to execute upon approval


# Remaining Data Collection: Complete All Missing Endpoints

**Created:** October 13, 2025, 10:26 PM
**Purpose:** Tackle ALL remaining data collection opportunities to maximize feature coverage
**Status:** 🚀 Ready to Execute
**Priority Order:** Highest impact → Lowest complexity

---

## 🎯 Executive Summary

**Current Status:** 350+ features collected
**Remaining Potential:** 135+ additional features
**Target:** 485+ total features (132% increase from original 209)

**Execution Order:**
1. NBA API Player Dashboards (30-40 features) - HIGHEST IMPACT
2. Fix NBA API Player Tracking (20-30 features) - HIGH IMPACT
3. NBA API Team Dashboards (30-40 features) - HIGH IMPACT
4. NBA API Game-Level Stats (10-15 features) - MEDIUM IMPACT
5. NBA API Matchups & Defense (15-20 features) - MEDIUM IMPACT
6. Basketball Reference Workaround (47 features) - MEDIUM IMPACT
7. Basketball Reference Additional Functions (30-43 features) - LOW IMPACT
8. ESPN Additional Endpoints (10-15 features) - LOW IMPACT

---

## Phase 1: NBA API Player Dashboards (Priority 1)

### Goal
Collect 7 player dashboard endpoints with situational metrics for clutch, splits, opponents, and performance analysis.

### Endpoints to Collect

**Player Dashboard Endpoints (7):**
1. `playerdashboardbyclutch` - Clutch performance (last 5 min, <5 point game)
2. `playerdashboardbygeneralsplits` - Home/away, win/loss, pre/post All-Star
3. `playerdashboardbyopponent` - Performance vs specific teams
4. `playerdashboardbyshootingsplits` - Shot distance, shot type, shot zone
5. `playerdashboardbylastngames` - Recent form (last 5, 10, 15, 20 games)
6. `playerdashboardbyteamperformance` - Team W/L when player plays
7. `playerdashboardbyyearoveryear` - Year-over-year comparison

### Implementation

**Script:** `scripts/etl/scrape_nba_api_player_dashboards.py`

**Coverage:** 2020-2025 (6 seasons)
**Players per season:** ~500 players
**Total API calls:** 500 players × 7 endpoints × 6 seasons = 21,000 calls
**Runtime estimate:** ~8-10 hours at 1.5s per call
**Features added:** 30-40 situational metrics

**Key Features:**
- Clutch shooting percentages
- Home/away splits
- Performance by opponent
- Shot location heat maps
- Recent form indicators
- Team impact metrics
- Year-over-year trends

### Deployment

```bash
# Create scraper
python3 scripts/etl/scrape_nba_api_player_dashboards.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_player_dashboards

# Deploy as background agent
nohup python3 scripts/etl/scrape_nba_api_player_dashboards.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_player_dashboards \
    > logs/nba_api_player_dashboards.log 2>&1 &
```

---

## Phase 2: Fix NBA API Player Tracking (Priority 2)

### Goal
Fix the failed player tracking scraper to collect 4 critical tracking endpoints.

### Problem Diagnosis
**Current Status:** FAILED (nba_api dependency issue)
**Root Cause:** Module import errors or missing nba_api installation

### Fix Strategy

1. **Verify nba_api installation**
   ```bash
   pip show nba_api
   pip install --upgrade nba_api
   ```

2. **Fix import statements** in `scripts/etl/scrape_nba_api_player_tracking.py`
   - Change from individual imports to module-level import
   - Use `from nba_api.stats import endpoints as nba_endpoints`

3. **Test with single player/season** before full deployment

### Endpoints to Collect

**Player Tracking Endpoints (4):**
1. `playerdashptpass` - Passing stats (passes made, potential assists, AST opportunities)
2. `playerdashptreb` - Rebounding stats (contested, uncontested, REB chances)
3. `playerdashptshotdefend` - Shot defense (contests, DFGM, DFGA, DFG%)
4. `playerdashptshots` - Shot tracking (touch time, dribbles before shot, closest defender distance)

### Implementation

**Coverage:** 2014-2025 (SportVU era only, 12 seasons)
**Players per season:** ~500 players
**Total API calls:** 500 players × 4 endpoints × 12 seasons = 24,000 calls
**Runtime estimate:** ~10-12 hours at 1.5s per call
**Features added:** 20-30 tracking metrics

### Deployment

```bash
# Fix and test
python3 scripts/etl/scrape_nba_api_player_tracking.py --test-mode

# Full deployment
nohup python3 scripts/etl/scrape_nba_api_player_tracking.py \
    --start-season 2014 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_player_tracking \
    > logs/nba_api_player_tracking_fixed.log 2>&1 &
```

---

## Phase 3: NBA API Team Dashboards (Priority 3)

### Goal
Collect 11 team dashboard endpoints for team-level situational metrics and lineup analysis.

### Endpoints to Collect

**Team Dashboard Endpoints (11):**
1. `teamdashboardbyclutch` - Team clutch performance
2. `teamdashboardbygeneralsplits` - Team home/away, W/L splits
3. `teamdashboardbyopponent` - Team performance vs opponents
4. `teamdashboardbyshootingsplits` - Team shot distance/type splits
5. `teamdashboardbylastngames` - Team recent form
6. `teamdashboardbyteamperformance` - Team performance metrics
7. `teamdashboardbyyearoveryear` - Team year-over-year
8. `teamdashlineups` - Lineup combinations and efficiency
9. `teamdashptpass` - Team passing statistics
10. `teamdashptreb` - Team rebounding statistics
11. `teamdashptshots` - Team shot tracking statistics

### Implementation

**Script:** `scripts/etl/scrape_nba_api_team_dashboards.py`

**Coverage:** 2020-2025 (6 seasons)
**Teams per season:** 30 teams
**Total API calls:** 30 teams × 11 endpoints × 6 seasons = 1,980 calls
**Runtime estimate:** ~1 hour at 1.5s per call
**Features added:** 30-40 team metrics

### Deployment

```bash
# Create and deploy
nohup python3 scripts/etl/scrape_nba_api_team_dashboards.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_team_dashboards \
    > logs/nba_api_team_dashboards.log 2>&1 &
```

---

## Phase 4: NBA API Game-Level Advanced Stats (Priority 4)

### Goal
Collect 4 game-level endpoints for rotation patterns, win probability, and game context.

### Endpoints to Collect

**Game-Level Endpoints (4):**
1. `gamerotation` - Player rotation patterns (minutes, substitutions)
2. `winprobabilitypbp` - Win probability by possession
3. `boxscoresimilarityscore` - Game similarity matching
4. `videodetails` - Video availability and timestamps

### Implementation

**Script:** `scripts/etl/scrape_nba_api_game_advanced.py`

**Coverage:** 2020-2025 (6 seasons)
**Games per season:** ~1,230 games
**Total API calls:** 1,230 games × 4 endpoints × 6 seasons = 29,520 calls
**Runtime estimate:** ~12-15 hours at 1.5s per call
**Features added:** 10-15 game context metrics

### Deployment

```bash
# Create and deploy
nohup python3 scripts/etl/scrape_nba_api_game_advanced.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_game_advanced \
    > logs/nba_api_game_advanced.log 2>&1 &
```

---

## Phase 5: NBA API Matchups & Defense (Priority 5)

### Goal
Collect 5 matchup and defensive tracking endpoints for shot location and defensive metrics.

### Endpoints to Collect

**Matchup & Defense Endpoints (5):**
1. `leaguedashplayerptshot` - Player shot tracking league-wide
2. `leaguedashplayershotlocations` - Player shot location heatmaps
3. `leaguedashteamptshot` - Team shot tracking league-wide
4. `leaguedashteamshotlocations` - Team shot zones and locations
5. `boxscorematchups` - Head-to-head player matchups

### Implementation

**Script:** `scripts/etl/scrape_nba_api_matchups_defense.py`

**Coverage:** 2020-2025 (6 seasons)
**Runtime estimate:** ~6-8 hours
**Features added:** 15-20 defensive/matchup metrics

### Deployment

```bash
# Create and deploy
nohup python3 scripts/etl/scrape_nba_api_matchups_defense.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/nba_api_matchups_defense \
    > logs/nba_api_matchups_defense.log 2>&1 &
```

---

## Phase 6: Basketball Reference API Workaround (Priority 6)

### Goal
Bypass 403 Forbidden errors and collect real Basketball Reference data to replace mock data.

### Problem Diagnosis
**Current Status:** BLOCKED (403 Forbidden)
**Root Cause:** IP/User-Agent blocking by Basketball Reference

### Fix Strategy

**Approach 1: Rotating User Agents**
```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36..."
]
```

**Approach 2: Increased Rate Limiting**
- Current: 12s between requests
- Try: 30s, 60s, 120s between requests

**Approach 3: Session Management**
- Use persistent sessions with cookies
- Rotate sessions periodically

**Approach 4: Proxy Rotation** (if needed)
- Use residential proxies
- Rotate IPs periodically

### Implementation

**Script:** `scripts/etl/scrape_basketball_reference_fixed.py`

**Coverage:** 2016-2025 (10 seasons)
**Features:** 47 advanced statistics (TS%, PER, BPM, Win Shares, Four Factors)
**Runtime estimate:** 8-12 hours with aggressive rate limiting
**Features added:** 47 real advanced statistics

### Deployment

```bash
# Test with one season first
python3 scripts/etl/scrape_basketball_reference_fixed.py --test-mode

# Full deployment if successful
nohup python3 scripts/etl/scrape_basketball_reference_fixed.py \
    --start-year 2016 \
    --end-year 2025 \
    --rate-limit 30.0 \
    --output-dir /tmp/bbref_real \
    > logs/bbref_real.log 2>&1 &
```

---

## Phase 7: Basketball Reference Additional Functions (Priority 7)

### Goal
Collect additional Basketball Reference endpoints for player splits, team advanced stats, and standings.

### Endpoints to Collect

**Player Stats Functions (4):**
1. `get_player_splits()` - Shooting splits by situation (home/away, month, quarter)
2. `get_player_headshot()` - Player images
3. `get_game_logs()` - Career game-by-game logs
4. `lookup()` - Player search/lookup

**Team Stats Functions (4):**
1. `get_opp_stats()` - Opponent statistics
2. `get_team_misc()` - Age, height, experience, pace, ratings
3. `get_team_ratings()` - SRS, ORtg, DRtg, NRtg, Pace
4. `get_roster_stats()` - Per-player team statistics

**Season Functions (1):**
1. `get_standings()` - Season standings with advanced stats

### Implementation

**Script:** `scripts/etl/scrape_basketball_reference_additional.py`

**Coverage:** 2016-2025 (10 seasons)
**Runtime estimate:** 4-6 hours
**Features added:** 30-43 split and advanced statistics

### Deployment

```bash
# Create and deploy
nohup python3 scripts/etl/scrape_basketball_reference_additional.py \
    --start-year 2016 \
    --end-year 2025 \
    --output-dir /tmp/bbref_additional \
    > logs/bbref_additional.log 2>&1 &
```

---

## Phase 8: ESPN Additional Endpoints (Priority 8)

### Goal
Collect missing ESPN endpoints for game rosters, team information, and calendar data.

### Endpoints to Collect

**ESPN Endpoints (3):**
1. `espn_nba_calendar()` - Season calendar and key dates
2. `espn_nba_game_rosters()` - Game-specific rosters
3. `espn_nba_teams()` - Team information and metadata

**hoopR Pre-aggregated Data (4):**
1. `load_nba_pbp()` - Pre-aggregated play-by-play
2. `load_nba_player_boxscore()` - Pre-aggregated player box scores
3. `load_nba_team_boxscore()` - Pre-aggregated team box scores
4. `load_nba_schedule()` - Pre-aggregated schedule

### Implementation

**Script:** `scripts/etl/scrape_espn_additional.py`

**Coverage:** 2020-2025 (6 seasons)
**Runtime estimate:** 2-3 hours
**Features added:** 10-15 ESPN-specific features

### Deployment

```bash
# Create and deploy
nohup python3 scripts/etl/scrape_espn_additional.py \
    --start-season 2020 \
    --end-season 2025 \
    --output-dir /tmp/espn_additional \
    > logs/espn_additional.log 2>&1 &
```

---

## Execution Timeline

### Week 1: NBA API Expansion (Phases 1-5)

**Day 1-2:**
- Phase 1: NBA API Player Dashboards (8-10 hours)
- Phase 2: Fix NBA API Player Tracking (10-12 hours)

**Day 3-4:**
- Phase 3: NBA API Team Dashboards (1 hour)
- Phase 4: NBA API Game-Level Stats (12-15 hours)

**Day 5-6:**
- Phase 5: NBA API Matchups & Defense (6-8 hours)

**Total Week 1:** ~37-46 hours runtime

### Week 2: Basketball Reference & ESPN (Phases 6-8)

**Day 1-3:**
- Phase 6: Basketball Reference Workaround (8-12 hours)

**Day 4-5:**
- Phase 7: Basketball Reference Additional Functions (4-6 hours)

**Day 6-7:**
- Phase 8: ESPN Additional Endpoints (2-3 hours)

**Total Week 2:** ~14-21 hours runtime

### Total Timeline
**Total runtime:** 51-67 hours (~2-3 days continuous, or 1-2 weeks with 8-hour days)
**Total API calls:** ~76,500 calls
**Total features added:** 135+ features
**Final feature count:** 485+ features

---

## Success Criteria

### Data Collection Complete When:

✅ All 8 phases completed successfully
✅ NBA API Player Dashboards: 21,000 files collected
✅ NBA API Player Tracking: 24,000 files collected (fixed)
✅ NBA API Team Dashboards: 1,980 files collected
✅ NBA API Game-Level: 29,520 files collected
✅ NBA API Matchups: Files collected for all seasons
✅ Basketball Reference: Real data collected (no mock data)
✅ Basketball Reference Additional: All functions scraped
✅ ESPN Additional: All endpoints scraped

### Feature Expansion Complete When:

✅ Player situational metrics: 30-40 features
✅ Player tracking metrics: 20-30 features
✅ Team dashboards: 30-40 features
✅ Game-level context: 10-15 features
✅ Matchup/defense: 15-20 features
✅ Basketball Reference advanced: 47 features
✅ Basketball Reference additional: 30-43 features
✅ ESPN additional: 10-15 features

**Total:** 485+ features (132% increase from original 209)

---

## Risk Mitigation

### API Rate Limiting
- Use 1.5-3.0s delays between requests
- Monitor for 429 errors
- Implement exponential backoff

### API Blocking
- Rotate user agents
- Use session management
- Implement proxy rotation if needed

### Data Quality
- Validate each endpoint response
- Check for empty/null data
- Log all errors comprehensively

### Resume Capability
- Save checkpoints after each player/team/game
- Track progress in JSON files
- Allow restart from last checkpoint

---

## Monitoring & Validation

### Progress Tracking

```bash
# Check all running scrapers
ps aux | grep python | grep etl | grep -v grep

# Monitor logs
tail -f logs/nba_api_player_dashboards.log
tail -f logs/nba_api_player_tracking_fixed.log
tail -f logs/nba_api_team_dashboards.log

# Check output directories
ls -la /tmp/nba_api_player_dashboards/
ls -la /tmp/nba_api_player_tracking/
ls -la /tmp/nba_api_team_dashboards/
```

### Validation Checks

```bash
# Run validation script after each phase
python scripts/etl/validate_collected_data.py \
    --phase player_dashboards \
    --output-dir /tmp/nba_api_player_dashboards

# Generate summary report
python scripts/etl/generate_collection_summary.py \
    --all-phases \
    --output-file reports/final_collection_summary.json
```

---

## Expected Outcomes

### Data Volume
- Current: 165+ datasets
- After completion: 400+ datasets
- Total increase: 235+ additional datasets

### Feature Coverage
- Current: 350+ features
- After completion: 485+ features
- Total increase: 135+ additional features (38% increase)

### Coverage Completeness
- Temporal: 1946-2025 (79 seasons)
- Situational: Clutch, home/away, opponent-specific
- Tracking: Speed, distance, touch time, defender distance
- Advanced: TS%, PER, BPM, Win Shares, Four Factors
- Team: Lineup efficiency, rotation patterns, team tracking
- Game: Win probability, rotation, similarity scores

### Ready for Phase Restructuring
✅ Complete dataset collected
✅ All planned endpoints scraped
✅ Maximum feature coverage achieved
✅ Ready for any MCP reorganization
✅ No dependencies on current phase structure

---

## Next Steps After Completion

1. **Validate all collected data**
2. **Generate comprehensive data catalog**
3. **Cross-source validation**
4. **Load data into RDS PostgreSQL**
5. **Create unified feature engineering pipeline**
6. **Update documentation with final statistics**
7. **Archive all raw data to S3**
8. **Ready for phase restructuring with MCP**

---

**END OF PLAN**

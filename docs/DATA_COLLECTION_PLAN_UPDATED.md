# Updated Data Collection Plan
## Based on Progressive Fidelity NBA Simulator Requirements

**Date:** October 9, 2025
**Source:** Progressive_Fidelity_NBA_Simulator_Complete_Guide_CORRECTED.md
**Status:** Active Collection Plan

---

## 🎯 Project Vision: Progressive Fidelity Simulation

This is a **Progressive Fidelity Historical Simulation System** that adapts to data quality across different eras:

- **1946-1960:** Minimal box scores → Team-level aggregate simulation
- **1960-1990:** Enhanced box scores → Player-level simulation
- **1990-2025:** Full play-by-play → Possession-level simulation

**Key Innovation:** Simulation accuracy improves as data granularity increases. Models learn game evolution across eras using transfer learning.

---

## 📊 Current Data Inventory Summary

### **S3 Data Lake (165,614 files, 118.4 GB)**

| Data Source | Files | Coverage | Status |
|-------------|-------|----------|--------|
| ESPN Play-by-Play | 44,826 | 1993-2025 | ✅ Complete |
| ESPN Box Scores | 44,828 | 1993-2025 | ✅ Complete |
| ESPN Team Stats | 46,093 | 1993-2025 | ✅ Complete |
| ESPN Schedule | 11,633 | 1993-2025 | ✅ Complete |
| NBA API Comprehensive | 15,736 | 2020-2025 | ✅ Current |
| NBA API Play-by-Play | 2,163 | Recent | 🔄 Expanding |
| hoopR Phase 1 | 218 | 2017-2021 | 🔄 Expanding to 1997 |
| Basketball Reference | 77 | Limited | ⏸️ Needs expansion |

### **RDS PostgreSQL (16 tables, 7.2 GB)**

| Table | Size | Rows | Coverage | Quality |
|-------|------|------|----------|---------|
| temporal_events | 5.6 GB | 14.1M | 1993-2025 | ✅ High |
| play_by_play | 1.5 GB | 6.8M | 2004-2021 | ✅ High |
| box_score_players | 91 MB | 408K | 1997-2021 | ⚠️ Gap 2021-2025 |
| games | 22 MB | 54,710 | 1993-2025 | ✅ Complete |
| box_score_teams | 6.7 MB | 15,898 | Various | ⚠️ Incomplete |

---

## 🚀 Phase 1: Foundation Data (Weeks 1-2) - PRIORITY

### **Goal:** Build working possession-level simulator for modern era (2015-2025)

#### **1.1: Data Assessment (Week 1, Days 1-2)**

**Required Scripts:**
```bash
# Create existence checker
python scripts/data_assessment/check_data_existence.py --output reports/existence_check.json

# Check completeness by season
python scripts/data_assessment/check_completeness.py \
    --start-season 2015 \
    --end-season 2025 \
    --output reports/completeness_report.json

# Quality validation
python scripts/data_assessment/check_data_quality.py \
    --seasons 2015-2025 \
    --output reports/quality_report.json
```

**Expected Output:**
```
✅ Box Scores: 2015-2025 (12,300 games, >95% complete)
✅ Play-by-Play: 2015-2025 (5.2M events, >90% complete)
⚠️  Lineup data: Sparse before 2016
✅ RECOMMENDATION: Start with 2016-2025 for PBP simulator
```

#### **1.2: Core Training Data (Week 1, Days 3-7)**

**Critical Tables Needed:**

1. **possessions** (or possession_panel) - REQUIRED FOR ML TRAINING
   - possession_id, game_id, season, period
   - offense_team_id, defense_team_id
   - seconds_remaining, score_diff
   - points_scored (TARGET VARIABLE)
   - is_home, is_playoffs

2. **team_season_stats** - REQUIRED FOR FEATURES
   - team_id, season
   - offensive_rating, defensive_rating
   - efg_pct, tov_rate, oreb_pct, ft_rate, three_point_rate, pace
   - opp_efg_pct, opp_tov_rate, dreb_pct, block_pct, steal_pct

3. **games** - REQUIRED FOR SCHEDULE/CONTEXT
   - game_id, season, game_date
   - home_team_id, away_team_id
   - home_score, away_score
   - is_playoffs
   - venue_id

4. **venues** - NEEDED FOR ALTITUDE ADJUSTMENT
   - venue_id, venue_name, city
   - elevation_ft (critical for Denver)

**Data Collection Actions:**

```bash
# Fill possession panel data (if missing)
python scripts/etl/create_possession_panel_from_espn.py \
    --start-season 2015 \
    --end-season 2025 \
    --output-table possessions

# Generate team season statistics
python scripts/ml/generate_team_season_stats.py \
    --start-season 2015 \
    --end-season 2025

# Create venue database
python scripts/db/create_venue_table.py \
    --include-elevation \
    --source basketball-reference
```

---

## 🎓 Phase 2: Feature Engineering Data (Weeks 3-4)

### **Goal:** Add 40+ engineered features for ML model

#### **2.1: Recent Performance Data**

**What's Needed:**
- Last 5 games per team (rolling window)
- Last 10 games for trend calculation
- Win/loss streaks

**Collection Strategy:**
```sql
-- Create materialized view for efficient recent game lookups
CREATE MATERIALIZED VIEW team_recent_games AS
SELECT
    team_id,
    game_date,
    season,
    points_scored,
    points_allowed,
    won,
    LAG(points_scored, 1) OVER (PARTITION BY team_id ORDER BY game_date) as prev_game_score,
    -- Rolling 5-game averages
    AVG(points_scored) OVER (
        PARTITION BY team_id ORDER BY game_date
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) as last5_ppg
FROM (
    SELECT
        home_team_id as team_id,
        game_date,
        season,
        home_score as points_scored,
        away_score as points_allowed,
        CASE WHEN home_score > away_score THEN 1 ELSE 0 END as won
    FROM games
    UNION ALL
    SELECT
        away_team_id as team_id,
        game_date,
        season,
        away_score as points_scored,
        home_score as points_allowed,
        CASE WHEN away_score > home_score THEN 1 ELSE 0 END as won
    FROM games
) team_games;
```

#### **2.2: Rest/Fatigue Data**

**What's Needed:**
- Days rest between games per team
- Back-to-back game indicators
- Travel distance (optional, nice-to-have)

**Collection Strategy:**
```bash
# Calculate rest days
python scripts/ml/calculate_rest_days.py \
    --start-season 2015 \
    --end-season 2025 \
    --output-table team_rest_schedule

# Expected output: team_id, game_id, days_rest, is_b2b
```

#### **2.3: Lineup Data (Optional Phase 2, Required Phase 3)**

**What's Needed:**
- 5-player lineup combinations
- Lineup stats (ORTG, DRTG, possessions played)
- Average height, experience

**Current Status:** ⚠️ **SPARSE DATA** - Not available before 2016

**Collection Strategy:**
```bash
# Source 1: NBA.com Advanced Stats API (2015-present)
python scripts/scrapers/nba_api_lineup_scraper.py \
    --start-season 2016 \
    --end-season 2025 \
    --min-possessions 50

# Source 2: Basketball Reference (backup)
python scripts/scrapers/basketball_reference_lineup_scraper.py \
    --start-season 2016 \
    --end-season 2025
```

**Fallback Strategy (if lineup data unavailable):**
- Use team-level stats as proxy
- Add player biographical features (height, experience)
- Start with team-only model, add lineups later

---

## 📦 Phase 3: Historical Data Expansion (Weeks 5-8)

### **Goal:** Extend simulation capability back to 1946

#### **3.1: Box Score Era Data (1946-1999)**

**Priority Order:**

1. **1980-1999 (High Priority)** - Modern box scores with most stats
   - Target: Complete player-level box scores
   - Required fields: MIN, PTS, REB, AST, STL, BLK, TOV, FGM/FGA, 3PM/3PA, FTM/FTA
   - Source: Basketball Reference scraping

2. **1960-1980 (Medium Priority)** - Transitional era, fewer stats
   - Target: Basic box scores (PTS, REB, AST minimum)
   - Missing: Often no steals/blocks/turnovers until 1973+
   - Source: Basketball Reference + Retrosheet

3. **1946-1960 (Low Priority)** - Minimal data
   - Target: Game-level aggregates only
   - Team totals: Points, FGM/FGA, FTM/FTA
   - Source: Basketball Reference, manual archives

**Collection Scripts:**

```bash
# Basketball Reference historical scraper
python scripts/scrapers/basketball_reference_historical.py \
    --start-season 1980 \
    --end-season 1999 \
    --data-type box_scores \
    --include-advanced-stats

# Expected output: 50K+ player-game records

# Validation: Check completeness by season
python scripts/data_assessment/validate_historical_data.py \
    --start-season 1980 \
    --end-season 1999 \
    --expected-games-per-season 1230
```

#### **3.2: Play-by-Play Historical Expansion**

**Currently Running:**
- ✅ hoopR Phase 1B: 2016 → 1997 (19 seasons remaining, ~48 hours estimated)

**Next Phase:**
```bash
# hoopR Phase 1C: Extend further back if available
python scripts/scrapers/hoopr_phase1c_scraper.py \
    --start-season 1997 \
    --end-season 1990 \
    --check-availability

# Expected: Play-by-play may not exist before ~1996-97
# Fallback: Use box score simulation for pre-1997
```

#### **3.3: Advanced Stats (Modern Era Enhancement)**

**Target: 2000-2025**

1. **Player Tracking Data** (2013-present)
   - Source: NBA.com Stats API
   - Data: Shot location, defensive tracking, movement
   - Use: Enhance lineup quality features

2. **Synergy Play Type Data** (2015-present)
   - Source: NBA.com Stats API (requires subscription)
   - Data: Pick and roll, isolation, post-up efficiency
   - Use: Play-type prediction models

3. **Second Spectrum Data** (2017-present)
   - Source: NBA.com Advanced Stats
   - Data: Defensive matchups, screen assists
   - Use: Lineup interaction features

**Collection Priority:** Phase 5+ (after core simulator working)

---

## 🏗️ Phase 4: Data Pipeline Infrastructure (Week 6)

### **Goal:** Automate data updates and quality monitoring

#### **4.1: Daily Update Pipeline**

```bash
# Integrated data pipeline (already created - Workflow #48)
bash scripts/monitoring/data_pipeline_manager.sh full

# Modes:
# - status: Inventory current data
# - plan: Identify gaps
# - collect: Launch scrapers
# - validate: Run quality checks
# - full: Complete pipeline
```

#### **4.2: Data Quality Monitoring**

**Automated Checks:**

1. **Completeness Check** (daily)
   - Expected games vs actual games per season
   - Missing possession data
   - Alert if <95% complete

2. **Quality Check** (weekly)
   - Reasonable score ranges (era-adjusted)
   - No impossible values (FGM > FGA, etc.)
   - Internal consistency (PBP → box score reconstruction)
   - Alert if quality score <80%

3. **Freshness Check** (daily)
   - Latest game in database vs actual schedule
   - Gap > 2 days = alert

**Implementation:**
```bash
# Create monitoring cron job
# Add to crontab: 0 2 * * * (daily at 2am)
bash scripts/monitoring/daily_data_quality_check.sh \
    --email-alerts \
    --slack-webhook $SLACK_URL \
    --output reports/daily_quality_$(date +%Y%m%d).json
```

---

## 🎯 Feature Requirements by Model Type

### **Possession Prediction Model (Priority 1)**

**Minimum Viable Features (15):**
- offense_team_ortg, defense_team_drtg
- off_team_efg, def_team_opp_efg
- score_differential, seconds_remaining
- period, is_home, is_playoffs
- off_team_pace, def_team_pace
- is_clutch, is_blowout
- ortg_minus_drtg, rest_advantage

**Target Performance:**
- RMSE < 0.7
- R² > 0.15
- PPP Error < 0.05

**Full Feature Set (40+):**
- Add recent performance (last 5/10 games)
- Add lineup features (if available)
- Add contextual features (altitude, rest, season timing)
- Add interaction features

**Target Performance:**
- RMSE < 0.55
- R² > 0.25
- PPP Error < 0.03

### **Box Score Era Model (Priority 2)**

**Minimum Features (10):**
- team_ppg, team_opp_ppg
- team_fg_pct, opp_fg_pct
- team_pace (estimated)
- is_home, season_year
- team_win_pct, opp_win_pct
- rest_days

**Target Performance:**
- Predicted score within ±10 points: 70%
- Correct winner prediction: 65%

### **Early Era Model (Priority 3)**

**Minimum Features (5):**
- team_ppg, opp_ppg
- team_win_pct, opp_win_pct
- is_home

**Target Performance:**
- Predicted score within ±15 points: 60%
- Correct winner prediction: 58%

---

## 📋 Data Collection Priorities (Ordered)

### **Week 1-2: CRITICAL PATH**
1. ✅ Verify play_by_play table completeness (2015-2025)
2. ✅ Verify games table completeness (2015-2025)
3. ⚠️ **CREATE possessions table** (if missing) - BLOCKING
4. ⚠️ **CREATE team_season_stats table** - BLOCKING
5. ⚠️ **CREATE venues table with elevation** - BLOCKING
6. ✅ Test data quality (run validation scripts)

### **Week 3-4: HIGH PRIORITY**
7. 🔄 Complete hoopR Phase 1B (2016 → 1997) - IN PROGRESS
8. ⏸️ Calculate rest days for all teams/games
9. ⏸️ Build recent performance rolling windows
10. ⏸️ Collect lineup data (2016-2025) if available

### **Week 5-8: MEDIUM PRIORITY**
11. ⏸️ Basketball Reference scraping (1980-1999 box scores)
12. ⏸️ Validate historical data completeness
13. ⏸️ Build box score era feature tables
14. ⏸️ Implement data quality monitoring

### **Week 9+: LOW PRIORITY / ENHANCEMENTS**
15. ⏸️ Player tracking data (2013-present)
16. ⏸️ Synergy play types (2015-present)
17. ⏸️ Shot location data enrichment
18. ⏸️ Early era data (1946-1980)

---

## 🔍 Critical Gaps Analysis

### **Blocking Issues (Must Resolve First):**

1. **Possessions Table Missing?**
   - Check: `SELECT COUNT(*) FROM possessions WHERE season BETWEEN 2015 AND 2025`
   - If 0 rows: Run `create_possession_panel_from_espn.py`
   - Expected: 2-3M possessions for 2015-2025

2. **Team Season Stats Missing?**
   - Check: `SELECT COUNT(*) FROM team_season_stats WHERE season BETWEEN 2015 AND 2025`
   - If 0 rows: Calculate from play-by-play/box scores
   - Expected: ~330 team-seasons (30 teams × 11 seasons)

3. **Venues Table Missing?**
   - Check: `SELECT COUNT(*) FROM venues WHERE elevation_ft IS NOT NULL`
   - Critical for altitude adjustment (Denver effect)
   - Minimum: 30 current arenas + historical arenas

### **Non-Blocking Gaps (Nice-to-Have):**

4. **Box Score Players (2021-2025)** - 3 recent seasons missing
5. **Lineup Data (pre-2016)** - Sparse or unavailable
6. **Historical PBP (pre-1997)** - May not exist

---

## 🎉 Success Criteria

### **Phase 1 Complete (Weeks 1-2):**
- [ ] Data assessment report generated
- [ ] Possessions table exists with 2M+ rows (2015-2025)
- [ ] Team season stats calculated for 330+ team-seasons
- [ ] Venues table created with elevation data
- [ ] Quality checks pass (>95% completeness, >80% quality)
- [ ] First ML model trains successfully (RMSE < 0.7)

### **Phase 2 Complete (Weeks 3-4):**
- [ ] Full feature engineering pipeline operational
- [ ] 40+ features available per possession
- [ ] Recent performance calculated for all games
- [ ] Rest/fatigue data integrated
- [ ] Model performance: RMSE < 0.55, R² > 0.25

### **Phase 3 Complete (Weeks 5-8):**
- [ ] Historical box scores (1980-1999) collected
- [ ] hoopR Phase 1B complete (1997-2021 PBP)
- [ ] Multi-era simulator functional
- [ ] Validation framework operational

### **Phase 4 Complete (Week 6+):**
- [ ] Automated daily data pipeline running
- [ ] Quality monitoring alerts configured
- [ ] Documentation complete
- [ ] Production-ready error handling

---

## 📊 Expected Data Volumes

| Data Type | Time Period | Expected Rows | Current Rows | Gap |
|-----------|-------------|---------------|--------------|-----|
| Games | 2015-2025 | 13,530 | 54,710 (all) | ✅ Have |
| Possessions | 2015-2025 | 2,500,000 | **TBD** | ❓ Check |
| Play-by-Play | 2015-2025 | 5,200,000 | 6,781,361 (04-21) | ✅ Have |
| Box Score Players | 2015-2025 | 250,000 | 408,881 (97-21) | ⚠️ Missing 21-25 |
| Team Season Stats | 2015-2025 | 330 | **TBD** | ❓ Check |
| Venues | Current | 30 | **TBD** | ❓ Check |
| Lineup Stats | 2016-2025 | 50,000 | 0 | ❌ Need to collect |
| Historical Box | 1980-1999 | 400,000 | **Minimal** | ❌ Need to collect |

---

## 🚀 Next Actions

### **Immediate (Today):**
1. Check if possessions table exists and is populated
2. Check if team_season_stats table exists
3. Check if venues table exists with elevation
4. If any missing: Run creation scripts

### **This Week:**
5. Run complete data assessment (Recommendation #1)
6. Generate data quality report
7. Identify any blockers for ML training
8. Start feature engineering pipeline

### **This Month:**
9. Train first possession prediction model
10. Build working simulator for 2023-24 season
11. Complete hoopR Phase 1B expansion
12. Begin Basketball Reference historical collection

---

*Last Updated: October 9, 2025*
*Next Review: After Phase 1 completion*
*Status: 🔄 Active Development*
# Complete Data Acquisition Plan
## Comprehensive Multi-Source Collection Strategy for Progressive Fidelity Simulation

**Date:** October 9, 2025
**Purpose:** Acquire ALL available NBA data from all repositories for panel data integration
**Status:** 🚀 Ready to Execute

---

## 🎯 Executive Summary

Based on the Progressive Fidelity Simulator requirements, this plan acquires **EVERY available data point** from all 5+ data sources to build the most comprehensive NBA temporal panel dataset possible.

**Total Data Volume Estimate:** 500+ GB raw data
**Total Acquisition Time:** 500-800 hours (20-33 days continuous)
**Target Records:** 25-50 million temporal events
**Coverage:** 1946-2025 (79 NBA seasons)

---

## 📊 Data Source Priority Matrix

### Priority 1: Foundation Data (Week 1-2)
**Goal:** Get simulator operational with modern data

| Source | Coverage | Priority | Runtime | Features | Status |
|--------|----------|----------|---------|----------|--------|
| ESPN API | 1993-2025 | 🔴 CRITICAL | 0 hrs | 53 | ✅ Complete (in S3) |
| hoopR Phase 1B | 1997-2021 | 🔴 CRITICAL | 48 hrs | 200+ | 🔄 IN PROGRESS (21% done) |
| NBA API (2015-2025) | 2015-2025 | 🟡 HIGH | 100-150 hrs | 269-289 | ⏸️ PENDING |

### Priority 2: Historical Expansion (Week 3-6)
**Goal:** Extend coverage back to 1946

| Source | Coverage | Priority | Runtime | Features | Status |
|--------|----------|----------|---------|----------|--------|
| Basketball Ref | 1946-2025 | 🟡 HIGH | 30-40 hrs | 150-200 | ⏸️ PENDING |
| NBA API (2000-2014) | 2000-2014 | 🟢 MEDIUM | 280-350 hrs | 153-200 | ⏸️ PENDING |
| Kaggle Database | 1946-2024 | 🟢 MEDIUM | 0.5 hrs | 100+ | ⏸️ PENDING |

### Priority 3: Advanced Features (Week 7-10)
**Goal:** Add tracking, synergy, shot location data

| Source | Coverage | Priority | Runtime | Features | Status |
|--------|----------|----------|---------|----------|--------|
| NBA API Tracking | 2013-2025 | 🔵 LOW | 50-75 hrs | 60-80 | ⏸️ PENDING |
| NBA API Hustle | 2015-2025 | 🔵 LOW | 20-30 hrs | 15-20 | ⏸️ PENDING |
| NBA API Synergy | 2015-2025 | 🔵 LOW | 20-30 hrs | 20-25 | ⏸️ PENDING |
| Shot Charts | 2000-2025 | 🔵 LOW | 40-60 hrs | 25+ | ⏸️ PENDING |

---

## 🗂️ Detailed Acquisition Plan by Source

### SOURCE 1: ESPN API (✅ COMPLETE)

**Status:** Already in S3 bucket (146,115 files, 119 GB)

**Coverage:** 1993-2025 (26 seasons, 31,980+ games)

**Data Collected:**
- ✅ Play-by-play events (44,826 files)
- ✅ Box scores (44,828 files)
- ✅ Team stats (46,093 files)
- ✅ Schedule (11,633 files)

**Next Steps:**
- ✅ Already uploaded to S3
- ⏸️ Extract to RDS (Phase 2.2)
- ⏸️ Create temporal_events table

**No further collection needed** - move to validation

---

### SOURCE 2: hoopR (R Package) - 🔄 IN PROGRESS

**Current Status:** Phase 1B running (5 of 24 seasons complete, 21%)

**Repository:** https://github.com/sportsdataverse/hoopR

**Phase 1A: Bulk Loaders (✅ COMPLETE)**
- Runtime: 30 seconds per season
- Data: Team/player season aggregates
- Seasons: 2002-2025 (24 seasons)
- Script: `scripts/etl/scrape_hoopr_phase1_foundation.R`

**Phase 1B: League Dashboards (🔄 IN PROGRESS - 21% COMPLETE)**
- Runtime: 2.5 hours per season × 24 = ~60 hours total
- Data: Detailed statistics, lineups, shot tracking
- Seasons: 2002-2025 (24 seasons)
- Script: `scripts/etl/scrape_hoopr_phase1b_only.R`
- **Remaining:** 19 seasons (~48 hours)

**Endpoints Collected (Phase 1B):**
1. `hoopR::load_nba_team_box()` - Team box scores
2. `hoopR::load_nba_player_box()` - Player box scores
3. `hoopR::nba_leaguedashteamstats()` - Team statistics
4. `hoopR::nba_leaguedashplayerstats()` - Player statistics
5. `hoopR::nba_leaguedashlineups()` - **CRITICAL: 5-man lineup combinations**
6. `hoopR::nba_leaguedashptdefend()` - Player tracking defense
7. `hoopR::nba_shotchartdetail()` - Shot charts

**Expected Output:**
- Location: `/tmp/hoopr_phase1b/` → `s3://nba-sim-raw-data-lake/hoopr_phase1b/`
- File count: ~10,000-15,000 CSV files
- Size: 5-8 GB
- Records: 2-3 million

**Completion Plan:**
1. ✅ Monitor current run: `tail -f /tmp/hoopr_phase1b_runner.log`
2. ✅ Wait for completion (~48 hours remaining)
3. ⏸️ Validate output (Workflow #41)
4. ⏸️ Upload to S3
5. ⏸️ Load to RDS

**Phase 1C: Historical Expansion (⏸️ FUTURE)**
- Extend hoopR collection to 1997-2001 if available
- Runtime: 2.5 hours × 5 seasons = 12.5 hours
- **Research needed:** Confirm hoopR has pre-2002 data

---

### SOURCE 3: NBA.com Stats API (via nba_api) - ⏸️ PENDING

**Repository:** https://github.com/swar/nba_api

**Total Acquisition Plan: 430-505 hours (18-21 days)**

#### **Phase 3A: Modern Era Foundation (2015-2025) - PRIORITY 1**

**Goal:** Build working possession model with maximum features

**Coverage:** 2015-16 to 2024-25 (10 seasons, 12,300 games)

**Runtime Estimate:** 100-150 hours (4-6 days)

**Endpoints (24 total):**

**Traditional & Advanced Box Scores (8 endpoints):**
1. `boxscoretraditionalv2` - Traditional box scores
2. `boxscoreadvancedv2` - Advanced efficiency metrics (TS%, eFG%, etc.)
3. `boxscoredefensivev2` - Defensive statistics
4. `boxscorefourfactorsv2` - Dean Oliver's four factors
5. `boxscoremiscv2` - Miscellaneous stats (PFD, screen assists)
6. `boxscoreplayertrackv2` - Player tracking (speed, distance, touches)
7. `boxscorescoringv2` - Scoring breakdown (paint, mid-range, 3PT)
8. `boxscoreusagev2` - Usage rates, game scores

**Player Tracking (4 endpoints - 2013+ only):**
9. `playerdashptpass` - Passing (passes made, potential assists, AST opportunities)
10. `playerdashptreb` - Rebounding (contested, uncontested, chances)
11. `playerdashptshotdefend` - Shot defense (contests, DFGM, DFGA, DFG%)
12. `playerdashptshots` - Shot tracking (touch time, dribbles before shot)

**Hustle Stats (2 endpoints - 2015+ only):**
13. `leaguehustlestatsplayer` - Player hustle (deflections, loose balls, charges)
14. `leaguehustlestatsteam` - Team hustle aggregates

**Synergy Play Types (1 endpoint - 2015+ only):**
15. `synergyplaytypes` - 10 play types (transition, isolation, P&R, post-up, spot-up, etc.)

**Shot Charts (1 endpoint):**
16. `shotchartdetail` - Shot coordinates, distance, make/miss

**League Dashboards (7 endpoints):**
17. `leaguedashplayerstats` - Player season/game statistics
18. `leaguedashteamstats` - Team season/game statistics
19. `leaguedashlineups` - **CRITICAL: 5-man lineup combinations with NetRtg**
20. `leaguedashptdefend` - Player tracking defense league-wide
21. `leaguedashptstats` - Player tracking stats league-wide
22. `leaguedashptteamdefend` - Team tracking defense
23. `leagueleaders` - League leaders in all categories

**Draft Data (2 endpoints):**
24. `draftcombinestats` - Combine measurements (height, weight, wingspan, vertical)
25. `drafthistory` - Draft picks by year

**Total Features:** 269-289 (maximum available)

**Script:** `scripts/etl/scrape_nba_api_comprehensive.py`

**Configuration:**
```python
START_SEASON = 2015
END_SEASON = 2025
LIMIT_GAMES = None  # Remove testing limit - scrape ALL games
LIMIT_PLAYERS = None  # Remove testing limit - scrape ALL players
RATE_LIMIT_SECONDS = 0.6  # 600ms between requests
```

**Execution:**
```bash
# Launch overnight scraper
nohup python scripts/etl/scrape_nba_api_comprehensive.py \
    --start-season 2015 \
    --end-season 2025 \
    --output /tmp/nba_api_modern \
    --s3-bucket nba-sim-raw-data-lake \
    --s3-prefix nba_api_modern \
    --no-test-mode \
    > /tmp/nba_api_modern.log 2>&1 &

# Monitor progress
tail -f /tmp/nba_api_modern.log

# Check running processes
ps aux | grep scrape_nba_api
```

**Expected Output:**
- Files: ~150,000-200,000 JSON files
- Size: 20-30 GB
- Records: 3-5 million
- Location: `/tmp/nba_api_modern/` → `s3://nba-sim-raw-data-lake/nba_api_modern/`

---

#### **Phase 3B: Digital Era (2000-2014) - PRIORITY 2**

**Goal:** Add 14 years of advanced stats (no tracking/hustle/synergy)

**Coverage:** 2000-01 to 2013-14 (14 seasons, 17,220 games)

**Runtime Estimate:** 280-350 hours (11-14 days)

**Endpoints (16 total - EXCLUDES tracking/hustle/synergy):**

**Traditional & Advanced Box Scores (8 endpoints):**
1-8. Same as Phase 3A

**Shot Charts (1 endpoint):**
9. `shotchartdetail` - Reliable for 2000-2014

**League Dashboards (7 endpoints):**
10-16. Same as Phase 3A (excluding player tracking)

**Total Features:** ~200 (no tracking/hustle/synergy available)

**Script:** Same as Phase 3A with different season range

**Configuration:**
```python
START_SEASON = 2000
END_SEASON = 2014
ENABLE_PLAYER_TRACKING = False  # Not available before 2013-14
ENABLE_HUSTLE_STATS = False  # Not available before 2015-16
ENABLE_SYNERGY = False  # Not available before 2015-16
```

**Execution:**
```bash
nohup python scripts/etl/scrape_nba_api_comprehensive.py \
    --start-season 2000 \
    --end-season 2014 \
    --output /tmp/nba_api_digital \
    --s3-prefix nba_api_digital \
    --disable-tracking \
    --disable-hustle \
    --disable-synergy \
    --no-test-mode \
    > /tmp/nba_api_digital.log 2>&1 &
```

**Expected Output:**
- Files: ~220,000-250,000 JSON files
- Size: 25-35 GB
- Records: 5-7 million

---

#### **Phase 3C: Early Digital Era (1996-1999) - PRIORITY 3**

**Goal:** Basic stats only, validate shot quality

**Coverage:** 1996-97 to 1999-00 (4 seasons, 3,280 games)

**Runtime Estimate:** 60-80 hours (2-3 days)

**⚠️ CRITICAL WARNING:**
- **194,239 field goal attempts missing shot coordinates (25%+)**
- Many missed jump shots mislabeled as missed layups
- Basketball-Reference: "We urge caution in utilizing them"

**Endpoints (9 total - BASIC ONLY):**

**Traditional & Advanced Box Scores (8 endpoints):**
1-8. Same as Phase 3A

**League Dashboards (1 endpoint):**
9. `leaguedashplayerstats` / `leaguedashteamstats` only

**EXCLUDE:**
- ❌ Shot charts (poor quality)
- ❌ Player tracking (not available)
- ❌ Hustle/synergy (not available)

**Total Features:** ~150

**Configuration:**
```python
START_SEASON = 1996
END_SEASON = 2000
ENABLE_SHOT_CHARTS = False  # Poor quality
LOG_DATA_QUALITY_WARNINGS = True
```

**Execution:**
```bash
nohup python scripts/etl/scrape_nba_api_comprehensive.py \
    --start-season 1996 \
    --end-season 2000 \
    --output /tmp/nba_api_early \
    --s3-prefix nba_api_early \
    --disable-shot-charts \
    --log-quality-warnings \
    --no-test-mode \
    > /tmp/nba_api_early.log 2>&1 &
```

**Expected Output:**
- Files: ~40,000-50,000 JSON files
- Size: 4-6 GB
- Records: 800K-1M

**Data Quality Actions:**
1. Flag all 1996-2000 shot location data with `quality_flag: 'poor'`
2. Add `missing_coordinates: true` for affected records
3. Exclude from shot distance analysis
4. Document limitations in data dictionary

---

### SOURCE 4: Basketball Reference - ⏸️ PENDING

**Website:** https://www.basketball-reference.com/

**Total Acquisition Plan: 30-40 hours**

#### **Phase 4A: Historical Box Scores (1946-1999)**

**Goal:** Fill pre-ESPN gap with highest quality historical data

**Coverage:** 1946-47 to 1998-99 (53 seasons, ~58,000 games)

**Scraping Strategy:**

**Era 1: Modern Historical (1980-1999) - 20 seasons**
- Player box scores with full stats
- Team box scores
- Advanced metrics (PER, WS, BPM, VORP)
- Playoff games
- Runtime: 2-3 hours per season × 20 = 40-60 hours

**Era 2: Mid Historical (1960-1980) - 20 seasons**
- Basic box scores (PTS, REB, AST)
- Missing: Steals (before 1973), blocks (before 1973), turnovers (before 1977)
- Runtime: 1-2 hours per season × 20 = 20-40 hours

**Era 3: Early Historical (1946-1960) - 14 seasons**
- Game-level aggregates only
- Team totals: Points, FGM/FGA, FTM/FTA
- Limited player data
- Runtime: 0.5-1 hour per season × 14 = 7-14 hours

**Total Runtime:** 67-114 hours (3-5 days)

**Rate Limiting:**
- 1 request per 3 seconds (per terms of service)
- User-Agent: "Academic Research NBA Simulator (contact: [email])"
- Cache all responses in S3

**Script:** `scripts/etl/scrape_basketball_reference_complete.py`

**Execution:**
```bash
# Historical scraper (1946-1999)
nohup python scripts/etl/scrape_basketball_reference_complete.py \
    --start-season 1946 \
    --end-season 1999 \
    --output /tmp/basketball_reference \
    --s3-prefix basketball_reference \
    --rate-limit 3.0 \
    --include-playoffs \
    --include-advanced \
    > /tmp/bbref_historical.log 2>&1 &

# Monitor
tail -f /tmp/bbref_historical.log
```

**Data Fields by Era:**

**1980-1999 (Full stats):**
- Basic: MIN, PTS, FGM, FGA, FG%, 3PM, 3PA, 3P%, FTM, FTA, FT%, ORB, DRB, TRB, AST, STL, BLK, TOV, PF
- Advanced: PER, TS%, eFG%, 3PAr, FTr, ORB%, DRB%, TRB%, AST%, STL%, BLK%, TOV%, USG%, WS, WS/48, BPM, VORP
- Total fields: ~35-40 per player-game

**1973-1980 (Added STL/BLK):**
- Basic: MIN, PTS, FGM, FGA, FG%, FTM, FTA, FT%, ORB, DRB, TRB, AST, STL, BLK, TOV, PF
- Total fields: ~20-25

**1960-1973 (No defensive stats):**
- Basic: MIN, PTS, FGM, FGA, FG%, FTM, FTA, FT%, REB, AST, PF
- Total fields: ~12-15

**1946-1960 (Minimal):**
- Team aggregates: PTS, FGM, FGA, FTM, FTA
- Player data sparse or missing
- Total fields: ~5-8

**Expected Output:**
- Files: 150,000-200,000 HTML cached + parsed CSV
- Size: 15-25 GB
- Records: 8-12 million player-game records

---

#### **Phase 4B: Advanced Stats & Career Data (1946-2025)**

**Goal:** Enrich existing data with advanced metrics

**Coverage:** All 79 seasons

**Data Types:**
1. **Player Career Stats** - Career totals, per-game averages
2. **Advanced Metrics** - PER, Win Shares, BPM, VORP
3. **Shooting Stats** - eFG%, TS%, 3PAr, FTr
4. **Play-by-Play Stats** (2000+) - On/Off splits, plus/minus
5. **Playoff Stats** - Separate playoff records

**Runtime:** 8-12 hours (1 day)

**Execution:**
```bash
# Advanced stats scraper
nohup python scripts/etl/scrape_basketball_reference_advanced.py \
    --start-season 1946 \
    --end-season 2025 \
    --include-playoffs \
    --include-career-totals \
    --rate-limit 3.0 \
    > /tmp/bbref_advanced.log 2>&1 &
```

**Expected Output:**
- Files: 30,000-40,000
- Size: 3-5 GB
- Records: 5-7 million

---

### SOURCE 5: Kaggle Basketball Database - ⏸️ PENDING

**URL:** https://www.kaggle.com/datasets/wyattowalsh/basketball

**Total Acquisition Plan: 0.5 hours (one-time download)**

#### **Phase 5: Kaggle Database Download & Extract**

**Goal:** Historical validation and gap-filling

**Database:** SQLite (~1-2 GB compressed, ~3-5 GB uncompressed)

**Coverage:** 1946-2024 (78 seasons, updated regularly)

**Tables (17 total):**
1. `game` - Game results (1946-2024, ~70,000 rows)
2. `team` - Team information (current + historical, ~100 rows)
3. `player` - Player profiles (4,500+ players)
4. `team_game_stats` - Team statistics per game
5. `player_game_stats` - Player statistics per game
6. `draft` - Draft history (1947-present)
7. `draft_combine` - Combine measurements (2000-present)
8. `officials` - Referee assignments
9. `inactive_players` - Inactive player list by game
10. `play_by_play` - Limited PBP data
11. `team_details` - Extended team metadata
12. `common_player_info` - Player biographical data
13. `team_history` - Franchise history
14. `team_info_common` - Current team details
15. `other_stats` - Miscellaneous statistics
16. `line_score` - Quarter-by-quarter scores
17. `win_probability` - In-game win probability

**Download Method:**
```bash
# Install Kaggle CLI
pip install kaggle

# Configure API credentials (one-time)
# Download kaggle.json from https://www.kaggle.com/settings
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Download database
python scripts/etl/download_kaggle_basketball.py

# Expected runtime: 5-10 minutes (depends on internet speed)
# Output: /tmp/kaggle_basketball/basketball.sqlite
```

**Script:** `scripts/etl/download_kaggle_basketball.py`

**Extraction to S3:**
```bash
# Extract tables to CSV and upload
python scripts/etl/extract_kaggle_to_temporal.py \
    --sqlite-path /tmp/kaggle_basketball/basketball.sqlite \
    --output /tmp/kaggle_csv \
    --s3-bucket nba-sim-raw-data-lake \
    --s3-prefix kaggle

# Runtime: 15-30 minutes
```

**Expected Output:**
- Files: 17 CSV files (one per table)
- Size: 3-5 GB
- Records: 15-20 million total across all tables

**Use Cases:**
1. **Historical validation** (1946-1999) - Cross-check Basketball Ref data
2. **Gap filling** - Find missing games in ESPN/NBA API
3. **Player biographical data** - Enrich player profiles
4. **Draft history** - Complete draft records
5. **Team metadata** - Franchise relocations, name changes

---

### SOURCE 6: SportsDataverse (⏸️ OPTIONAL - REDUNDANT WITH hoopR)

**Status:** ⏸️ SKIPPED (redundant with hoopR R package)

**Reason:** SportsDataverse Python package is wrapper around same data as hoopR

**Alternative:** Use hoopR R scripts (already implemented)

**If needed for validation:**
```bash
pip install sportsdataverse

python -c "
from sportsdataverse.nba import nba_schedule, nba_pbp
schedule = nba_schedule.espn_nba_schedule(season=2024)
print(f'Loaded {len(schedule)} games')
"
```

---

## 📋 Complete Execution Schedule

### Week 1: Foundation (Oct 9-15)
**Goal:** Modern era operational

| Day | Task | Runtime | Output |
|-----|------|---------|--------|
| **Day 1** | ✅ hoopR Phase 1B monitor (wait for completion) | 48 hrs | 218 → 10K files |
| **Day 2** | ⏸️ Validate hoopR output (Workflow #41) | 1 hr | Quality report |
| **Day 3** | ⏸️ Upload hoopR to S3 | 2 hrs | 5-8 GB uploaded |
| **Day 4** | ⏸️ Launch NBA API Modern (2015-2025) | 100-150 hrs | Start scraper |
| **Day 5-7** | ⏸️ Monitor NBA API Modern | - | 20-30 GB collected |

### Week 2-3: Modern Era Completion (Oct 16-29)
**Goal:** Complete 2015-2025 with all features

| Task | Runtime | Output |
|------|---------|--------|
| ⏸️ NBA API Modern completion | 100-150 hrs | 150K-200K files |
| ⏸️ Validate NBA API output | 2 hrs | Quality report |
| ⏸️ Upload to S3 | 3-4 hrs | 20-30 GB |
| ⏸️ Load hoopR to RDS | 4-6 hrs | 2-3M records |
| ⏸️ Load NBA API to RDS | 8-12 hrs | 3-5M records |

### Week 4-5: Historical Collection (Oct 30 - Nov 12)
**Goal:** Add 2000-2014 and Basketball Ref

| Task | Runtime | Output |
|------|---------|--------|
| ⏸️ Launch NBA API Digital (2000-2014) | 280-350 hrs | 220K-250K files |
| ⏸️ Launch Basketball Ref Historical | 67-114 hrs | 150K-200K files |
| ⏸️ Download Kaggle database | 0.5 hrs | 1-2 GB |
| ⏸️ Extract Kaggle to S3 | 0.5 hrs | 17 CSV files |

**Parallel execution:** NBA API + Basketball Ref can run simultaneously

### Week 6-7: Digital Era Completion (Nov 13-26)
**Goal:** Complete 2000-2014

| Task | Runtime | Output |
|------|---------|--------|
| ⏸️ NBA API Digital completion | 280-350 hrs | 25-35 GB |
| ⏸️ Basketball Ref completion | 67-114 hrs | 15-25 GB |
| ⏸️ Validate all outputs | 4-6 hrs | Quality reports |
| ⏸️ Upload to S3 | 6-8 hrs | 40-60 GB total |
| ⏸️ Load to RDS | 16-24 hrs | 10-15M records |

### Week 8: Early Digital Era (Nov 27 - Dec 3)
**Goal:** Add 1996-1999 (with caution)

| Task | Runtime | Output |
|------|---------|--------|
| ⏸️ Launch NBA API Early (1996-1999) | 60-80 hrs | 40K-50K files |
| ⏸️ Flag shot quality issues | 2 hrs | Data quality log |
| ⏸️ Upload to S3 | 1 hr | 4-6 GB |
| ⏸️ Load to RDS | 2-4 hrs | 800K-1M records |

### Week 9-10: Data Validation & Quality (Dec 4-17)
**Goal:** Cross-validation and gap analysis

| Task | Runtime | Output |
|------|---------|--------|
| ⏸️ Cross-validate all sources | 8-12 hrs | Discrepancy report |
| ⏸️ Fill identified gaps | 12-24 hrs | Gap-fill dataset |
| ⏸️ Generate data quality report | 2-4 hrs | Complete quality audit |
| ⏸️ Create data dictionary | 4-6 hrs | Field-level documentation |

---

## 📊 Expected Final Dataset Statistics

### **By Time Period:**

| Era | Coverage | Games | PBP Events | Box Scores | Features | Quality |
|-----|----------|-------|------------|------------|----------|---------|
| **2015-2025** | 10 seasons | 12,300 | 7-8M | 250K | 269-289 | ⭐⭐⭐⭐⭐ Excellent |
| **2013-2014** | 2 seasons | 2,460 | 1.5-2M | 50K | 213-233 | ⭐⭐⭐⭐⭐ Excellent |
| **2000-2012** | 13 seasons | 15,990 | 10-12M | 325K | 153-200 | ⭐⭐⭐⭐ Good |
| **1997-1999** | 3 seasons | 3,690 | 2-3M | 75K | 200+ | ⭐⭐⭐⭐ Good |
| **1996-1999** | 4 seasons | 3,280 | 2M | 65K | 133-150 | ⭐⭐⭐ Fair |
| **1980-1996** | 17 seasons | 20,910 | - | 425K | 150-200 | ⭐⭐⭐⭐ Good |
| **1960-1980** | 20 seasons | 24,600 | - | 500K | 100-150 | ⭐⭐⭐ Fair |
| **1946-1960** | 14 seasons | 17,220 | - | 350K | 50-100 | ⭐⭐ Poor |
| **TOTAL** | **79 seasons** | **~100,000** | **23-28M** | **2-2.5M** | - | - |

### **By Data Source:**

| Source | Files | Size | Records | Coverage | Unique Fields |
|--------|-------|------|---------|----------|---------------|
| ESPN | 146,115 | 119 GB | 14.1M events | 1993-2025 | 53 |
| hoopR | 10,000-15,000 | 5-8 GB | 2-3M | 1997-2021 | 200+ |
| NBA API Modern | 150K-200K | 20-30 GB | 3-5M | 2015-2025 | 289 |
| NBA API Digital | 220K-250K | 25-35 GB | 5-7M | 2000-2014 | 200 |
| NBA API Early | 40K-50K | 4-6 GB | 800K-1M | 1996-1999 | 150 |
| Basketball Ref | 150K-200K | 15-25 GB | 8-12M | 1946-2025 | 200 |
| Kaggle | 17 tables | 3-5 GB | 15-20M | 1946-2024 | 100+ |
| **TOTAL** | **~700K-900K** | **191-228 GB** | **48-62M** | **1946-2025** | **400+** |

### **By Feature Category:**

| Category | Fields | Sources | Availability |
|----------|--------|---------|--------------|
| Traditional Box | 53 | All | 1946-2025 |
| Advanced Stats | 100 | NBA API, BRef | 1973-2025 |
| Player Tracking | 60-80 | NBA API | 2013-2025 |
| Hustle Stats | 15-20 | NBA API | 2015-2025 |
| Synergy Play Types | 20-25 | NBA API | 2015-2025 |
| Shot Location | 25+ | NBA API, hoopR | 2000-2025 |
| Lineup Data | 30+ | NBA API, hoopR | 2007-2025 |
| Draft/Combine | 20+ | NBA API, Kaggle | 1947-2025 |
| Biographical | 25+ | All | 1946-2025 |
| Team Metadata | 15+ | All | 1946-2025 |

---

## 🎯 Data Integration Strategy

### **Cross-Source Mapping:**

**Primary Keys:**
- `game_id` - Unique game identifier (map across all sources)
- `player_id` - Unique player identifier (requires ID mapping table)
- `team_id` - Unique team identifier (requires team mapping)
- `season` - Season year (YYYY format)
- `game_date` - Game date (YYYY-MM-DD)

**ID Mapping Tables (CRITICAL):**

1. **game_id_mapping**
   - `espn_game_id` → `nba_stats_game_id` → `bbref_game_id` → `kaggle_game_id`
   - Example: "401234567" (ESPN) = "0022100500" (NBA Stats) = "202110250BOS" (BRef)

2. **player_id_mapping**
   - `espn_player_id` → `nba_stats_player_id` → `bbref_player_id` → `kaggle_player_id`
   - Example: "12345" (ESPN) = "2544" (NBA Stats - LeBron) = "jamesle01" (BRef)

3. **team_id_mapping**
   - `espn_team_id` → `nba_stats_team_id` → `bbref_team_abbrev` → `kaggle_team_id`
   - Example: "5" (ESPN LAL) = "1610612747" (NBA Stats LAL) = "LAL" (BRef)

**Script:** `scripts/etl/create_cross_source_id_mappings.py`

**Execution:**
```bash
python scripts/etl/create_cross_source_id_mappings.py \
    --sources espn,nba_api,basketball_ref,kaggle,hoopr \
    --output /tmp/id_mappings \
    --upload-to-rds
```

---

### **Deduplication Strategy:**

**Priority Order (for conflicts):**
1. **NBA.com Stats API** - Official source (highest priority)
2. **ESPN API** - Primary source (high priority)
3. **Basketball Reference** - Historical gold standard
4. **hoopR** - Modern supplement
5. **Kaggle** - Validation only (lowest priority)

**Deduplication Rules:**

```sql
-- Example: Multiple box scores for same player-game
-- Rule: Use NBA Stats if available, else ESPN, else BRef

SELECT
    COALESCE(nba_stats.points, espn.points, bbref.points) as points,
    COALESCE(nba_stats.rebounds, espn.rebounds, bbref.rebounds) as rebounds,
    -- Mark source priority
    CASE
        WHEN nba_stats.points IS NOT NULL THEN 'nba_stats'
        WHEN espn.points IS NOT NULL THEN 'espn'
        WHEN bbref.points IS NOT NULL THEN 'basketball_ref'
    END as source_priority
FROM player_game_stats_raw
WHERE game_id = '...' AND player_id = '...';
```

**Script:** `scripts/etl/deduplicate_multi_source_data.py`

---

### **Data Quality Scoring:**

**Quality Score Calculation:**

```python
def calculate_quality_score(record):
    """
    Calculate data quality score (0-100)
    """
    score = 100

    # Deduct for missing fields
    required_fields = ['points', 'rebounds', 'assists']
    missing_required = sum(1 for f in required_fields if record[f] is None)
    score -= missing_required * 10

    # Deduct for poor temporal precision
    if record['precision_level'] == 'game':
        score -= 20
    elif record['precision_level'] == 'minute':
        score -= 5

    # Deduct for known data quality issues
    if record['season'] in [1996, 1997, 1998, 1999] and record['shot_coordinates']:
        score -= 30  # Poor shot quality in 1996-1999

    # Bonus for multiple source confirmation
    if record['num_sources'] >= 3:
        score += 10

    return max(0, min(100, score))
```

**Quality Flags:**
- `quality_score: 90-100` - ⭐⭐⭐⭐⭐ Excellent
- `quality_score: 75-89` - ⭐⭐⭐⭐ Good
- `quality_score: 60-74` - ⭐⭐⭐ Fair
- `quality_score: 0-59` - ⭐⭐ Poor

---

## 🚀 Quick Start Commands

### **Launch All Scrapers (Parallel Execution):**

```bash
# Create master launch script
cat > /tmp/launch_all_scrapers.sh << 'EOF'
#!/bin/bash

echo "🚀 Launching all NBA data scrapers in parallel..."

# 1. hoopR Phase 1B (if not already running)
if ! ps aux | grep -q scrape_hoopr_phase1b; then
    echo "▶️  Launching hoopR Phase 1B..."
    nohup bash scripts/etl/run_hoopr_phase1b.sh > /tmp/hoopr_phase1b.log 2>&1 &
    echo "hoopR PID: $!"
fi

# 2. NBA API Modern Era (2015-2025)
echo "▶️  Launching NBA API Modern (2015-2025)..."
nohup python scripts/etl/scrape_nba_api_comprehensive.py \
    --start-season 2015 --end-season 2025 \
    --output /tmp/nba_api_modern \
    --s3-prefix nba_api_modern \
    --no-test-mode \
    > /tmp/nba_api_modern.log 2>&1 &
echo "NBA API Modern PID: $!"

# 3. NBA API Digital Era (2000-2014) - Run after modern completes
# Uncomment when ready:
# nohup python scripts/etl/scrape_nba_api_comprehensive.py \
#     --start-season 2000 --end-season 2014 \
#     --output /tmp/nba_api_digital \
#     --disable-tracking --disable-hustle --disable-synergy \
#     > /tmp/nba_api_digital.log 2>&1 &

# 4. Basketball Reference Historical (1946-1999)
echo "▶️  Launching Basketball Reference Historical..."
nohup python scripts/etl/scrape_basketball_reference_complete.py \
    --start-season 1946 --end-season 1999 \
    --output /tmp/basketball_reference \
    --rate-limit 3.0 \
    > /tmp/bbref_historical.log 2>&1 &
echo "Basketball Ref PID: $!"

# 5. Kaggle Database (one-time)
echo "▶️  Downloading Kaggle database..."
python scripts/etl/download_kaggle_basketball.py > /tmp/kaggle_download.log 2>&1 &
echo "Kaggle PID: $!"

echo ""
echo "✅ All scrapers launched!"
echo ""
echo "📊 Monitor progress:"
echo "   tail -f /tmp/hoopr_phase1b.log"
echo "   tail -f /tmp/nba_api_modern.log"
echo "   tail -f /tmp/bbref_historical.log"
echo "   tail -f /tmp/kaggle_download.log"
echo ""
echo "🔍 Check running processes:"
echo "   ps aux | grep -E 'scrape_hoopr|scrape_nba_api|scrape_basketball'"
EOF

chmod +x /tmp/launch_all_scrapers.sh
bash /tmp/launch_all_scrapers.sh
```

---

### **Monitor All Scrapers:**

```bash
# Create monitoring dashboard script
cat > /tmp/monitor_all_scrapers.sh << 'EOF'
#!/bin/bash

clear
echo "========================================"
echo "NBA DATA SCRAPER MONITORING DASHBOARD"
echo "========================================"
echo ""

# hoopR
if ps aux | grep -q "scrape_hoopr_phase1b" | grep -v grep; then
    echo "✅ hoopR Phase 1B: RUNNING"
    if [ -f /tmp/hoopr_phase1b_runner.log ]; then
        tail -1 /tmp/hoopr_phase1b_runner.log | sed 's/^/   /'
    fi
else
    echo "⏸️  hoopR Phase 1B: NOT RUNNING"
fi

echo ""

# NBA API Modern
if ps aux | grep -q "scrape_nba_api.*2015" | grep -v grep; then
    echo "✅ NBA API Modern (2015-2025): RUNNING"
    if [ -f /tmp/nba_api_modern.log ]; then
        tail -1 /tmp/nba_api_modern.log | sed 's/^/   /'
    fi
else
    echo "⏸️  NBA API Modern: NOT RUNNING"
fi

echo ""

# Basketball Reference
if ps aux | grep -q "scrape_basketball_reference" | grep -v grep; then
    echo "✅ Basketball Reference: RUNNING"
    if [ -f /tmp/bbref_historical.log ]; then
        tail -1 /tmp/bbref_historical.log | sed 's/^/   /'
    fi
else
    echo "⏸️  Basketball Reference: NOT RUNNING"
fi

echo ""

# File counts
echo "📁 Output file counts:"
echo "   hoopR: $(find /tmp/hoopr_phase1b -type f 2>/dev/null | wc -l) files"
echo "   NBA API Modern: $(find /tmp/nba_api_modern -type f 2>/dev/null | wc -l) files"
echo "   Basketball Ref: $(find /tmp/basketball_reference -type f 2>/dev/null | wc -l) files"

echo ""
echo "Press Ctrl+C to exit. Refreshing every 30 seconds..."
EOF

chmod +x /tmp/monitor_all_scrapers.sh

# Run monitoring loop
while true; do
    bash /tmp/monitor_all_scrapers.sh
    sleep 30
    clear
done
```

---

## 📝 Success Criteria

### **Phase 1 Complete (Week 1-3):**
- [ ] hoopR Phase 1B: 24 seasons collected (10K-15K files)
- [ ] NBA API Modern: 2015-2025 complete (150K-200K files)
- [ ] All data uploaded to S3
- [ ] Initial RDS load successful
- [ ] Data quality score >85% for modern era

### **Phase 2 Complete (Week 4-7):**
- [ ] NBA API Digital: 2000-2014 complete (220K-250K files)
- [ ] Basketball Ref: 1946-1999 complete (150K-200K files)
- [ ] Kaggle database downloaded and extracted
- [ ] Cross-source ID mappings created
- [ ] Deduplication rules implemented

### **Phase 3 Complete (Week 8-10):**
- [ ] NBA API Early: 1996-1999 collected (with quality flags)
- [ ] All data in RDS with quality scores
- [ ] Cross-validation report generated
- [ ] Data gaps identified and documented
- [ ] Final dataset: 48-62M records, 191-228 GB

---

## 🎉 Final Deliverables

1. **Complete Data Lake**
   - S3 bucket: 191-228 GB raw data
   - 700K-900K files across all sources
   - Full coverage: 1946-2025 (79 seasons)

2. **Integrated Database**
   - RDS PostgreSQL: 48-62M temporal events
   - 16+ tables with cross-source integration
   - Quality scores for every record

3. **Documentation**
   - Data dictionary (400+ fields)
   - Quality audit reports
   - Source lineage tracking
   - Known limitations documented

4. **Validation Reports**
   - Cross-source discrepancy analysis
   - Gap analysis by season
   - Coverage statistics
   - Quality metrics dashboard

---

## 💰 Cost Management & Budget

### **Current Costs (Baseline):**
- S3 storage: $2.74/month (119 GB ESPN data)
- RDS: $0/month (not yet deployed)
- **Total:** $2.74/month

### **Post-Acquisition Costs (Data Collection Only):**

| Resource | Usage | Monthly Cost | Annual Cost |
|----------|-------|--------------|-------------|
| **S3 Storage** | 228 GB (after acquisition) | $5.25/month | $63/year |
| **S3 Requests** | 900K PUT requests (one-time) | $4.50 (one-time) | - |
| **Data Transfer** | Negligible (same region) | $0 | $0 |
| **RDS db.t3.medium** | 2 vCPU, 4 GB RAM | $29.20/month | $350/year |
| **RDS Storage** | 100 GB (initial) | $11.50/month | $138/year |
| **RDS Backups** | 100 GB automated | $9.50/month | $114/year |
| **TOTAL (Data Only)** | - | **$55.45/month** | **$665/year** |

### **Full System Costs (After ML Training):**

| Resource | Usage | Monthly Cost | Notes |
|----------|-------|--------------|-------|
| S3 Storage | 228 GB | $5.25 | Raw data lake |
| RDS Instance | db.t3.medium | $29.20 | Database server |
| RDS Storage | 150 GB | $17.25 | Increased for ML features |
| RDS Backups | 150 GB | $14.25 | Automated daily backups |
| Lambda Functions | 1M invocations | $0.20 | Scraper automation |
| CloudWatch Logs | 10 GB | $5.00 | Monitoring logs |
| **Subtotal (Production)** | - | **$71.15/month** | Without SageMaker |
| **SageMaker Training** | ml.m5.xlarge × 10 hrs | $19.20 (one-time) | Model training |
| **SageMaker Inference** | ml.t2.medium (optional) | $50.40/month | Real-time predictions |
| **TOTAL (With ML)** | - | **$121.55/month** | **$1,459/year** |

### **Budget Targets:**
- ✅ **Data Collection Phase:** $55/month (within $150 budget)
- ✅ **Production (No Inference):** $71/month (within $150 budget)
- ⚠️ **Production (With Inference):** $122/month (within $150 budget)
- 🎯 **Target:** Stay under $150/month

### **Cost Optimization Strategies:**

1. **S3 Lifecycle Policies**
   - Move raw files to Glacier after 90 days ($0.004/GB vs $0.023/GB)
   - Savings: $4-5/month

2. **RDS Reserved Instances**
   - 1-year commitment: 30% discount = $20.44/month (save $8.76/month)
   - 3-year commitment: 50% discount = $14.60/month (save $14.60/month)

3. **Right-Sizing RDS**
   - Start with db.t3.small (1 vCPU, 2 GB): $14.60/month
   - Upgrade only if query performance suffers
   - Savings: $14.60/month

4. **SageMaker Alternatives**
   - Use EC2 Spot Instances for training (70% cheaper)
   - Batch inference instead of real-time endpoint
   - Savings: $30-40/month

5. **Data Transfer Optimization**
   - Keep scrapers in same region as S3/RDS (us-east-1)
   - Use VPC endpoints (no data transfer charges)

### **Cost Alerts (Recommended):**

```bash
# Set up AWS Budget alerts
aws budgets create-budget \
    --account-id $(aws sts get-caller-identity --query Account --output text) \
    --budget '{
        "BudgetName": "NBA-Simulator-Monthly",
        "BudgetLimit": {"Amount": "150", "Unit": "USD"},
        "TimeUnit": "MONTHLY",
        "BudgetType": "COST"
    }' \
    --notifications-with-subscribers '[
        {
            "Notification": {
                "NotificationType": "ACTUAL",
                "ComparisonOperator": "GREATER_THAN",
                "Threshold": 80
            },
            "Subscribers": [{
                "SubscriptionType": "EMAIL",
                "Address": "your-email@example.com"
            }]
        }
    ]'
```

### **Monthly Cost Breakdown by Phase:**

| Phase | S3 | RDS | Other | Total | Cumulative |
|-------|-----|-----|-------|-------|------------|
| **Week 1-3** | $3 | $0 | $0 | $3/mo | $3 |
| **Week 4-7** | $4 | $29 | $0 | $33/mo | $10 |
| **Week 8-10** | $5 | $29 | $5 | $39/mo | $16 |
| **Production** | $5 | $46 | $20 | $71/mo | Ongoing |

**Total Acquisition Cost:** ~$29 (one-time for 10 weeks of data collection)

---

## ⚠️ Risk Mitigation & Contingency Planning

### **Risk Matrix:**

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|---------|---------------------|
| NBA API rate limiting | HIGH | MEDIUM | Use 600ms delays, implement exponential backoff |
| Basketball Ref blocking | MEDIUM | MEDIUM | 3-second delays, rotate User-Agent, respect robots.txt |
| hoopR scraper failure | LOW | LOW | Already 21% complete, checkpoint-based resumption |
| S3 storage limit | LOW | LOW | Monitor usage, set up alerts at 80% capacity |
| RDS disk full | LOW | HIGH | Start with 100 GB, auto-scaling enabled |
| Data quality issues | HIGH | MEDIUM | Implement quality scoring, flag bad data |
| Script crashes | MEDIUM | MEDIUM | Use nohup, log all output, checkpoint progress |
| Network outages | MEDIUM | LOW | Automatic retry with exponential backoff |
| AWS cost overrun | LOW | HIGH | Budget alerts at $120 (80% of $150 limit) |
| Missing data gaps | HIGH | MEDIUM | Cross-validation across 6 sources |

### **Detailed Mitigation Strategies:**

#### **1. NBA API Rate Limiting (HIGH RISK)**

**Problem:** NBA.com Stats API has unofficial rate limits (~20-60 requests/minute)

**Mitigation:**
```python
import time
import random

class RateLimiter:
    def __init__(self, min_delay=0.6, max_delay=1.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request = 0
        self.failure_count = 0

    def wait(self):
        """Wait with exponential backoff on failures"""
        elapsed = time.time() - self.last_request

        # Base delay with jitter
        delay = random.uniform(self.min_delay, self.max_delay)

        # Exponential backoff on failures
        if self.failure_count > 0:
            delay *= (2 ** self.failure_count)

        # Wait remaining time
        if elapsed < delay:
            time.sleep(delay - elapsed)

        self.last_request = time.time()

    def on_success(self):
        self.failure_count = 0

    def on_failure(self):
        self.failure_count = min(self.failure_count + 1, 5)  # Cap at 32x delay
```

**Recovery:**
- Log failed requests to `/tmp/nba_api_failed_requests.json`
- Retry failed requests after full scrape completes
- Fall back to hoopR/ESPN data if NBA API completely blocked

---

#### **2. Basketball Reference Blocking (MEDIUM RISK)**

**Problem:** Basketball-Reference may block aggressive scraping

**Mitigation:**
```python
class RespectfulScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic Research NBA Simulator (contact: research@example.com)',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.basketball-reference.com/'
        })
        self.min_delay = 3.0  # 3 seconds per request (as per ToS)

    def fetch_with_cache(self, url):
        """Check S3 cache first, fetch if not exists"""
        cache_key = hashlib.md5(url.encode()).hexdigest()

        # Check S3 cache
        try:
            cached = s3.get_object(
                Bucket='nba-sim-raw-data-lake',
                Key=f'bbref_cache/{cache_key}.html'
            )
            return cached['Body'].read()
        except:
            pass

        # Fetch and cache
        time.sleep(self.min_delay)
        response = self.session.get(url, timeout=30)

        if response.status_code == 200:
            # Cache to S3
            s3.put_object(
                Bucket='nba-sim-raw-data-lake',
                Key=f'bbref_cache/{cache_key}.html',
                Body=response.content
            )
            return response.content
        elif response.status_code == 429:
            # Rate limited - wait longer
            time.sleep(60)
            return self.fetch_with_cache(url)
        else:
            raise Exception(f"HTTP {response.status_code}: {url}")
```

**Recovery:**
- All responses cached to S3 immediately
- Can resume scraping from cache if blocked
- Fall back to Kaggle database for historical data

---

#### **3. Scraper Crash Recovery (MEDIUM RISK)**

**Problem:** Long-running scrapers may crash mid-execution

**Mitigation:**
```python
import json
import os

class CheckpointManager:
    def __init__(self, checkpoint_file='/tmp/scraper_checkpoint.json'):
        self.checkpoint_file = checkpoint_file
        self.checkpoint = self.load()

    def load(self):
        """Load checkpoint from disk"""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {'completed': [], 'failed': [], 'last_season': None}

    def save(self):
        """Save checkpoint to disk"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    def mark_completed(self, season, endpoint):
        """Mark task as completed"""
        key = f"{season}_{endpoint}"
        if key not in self.checkpoint['completed']:
            self.checkpoint['completed'].append(key)
        self.checkpoint['last_season'] = season
        self.save()

    def mark_failed(self, season, endpoint, error):
        """Mark task as failed"""
        self.checkpoint['failed'].append({
            'season': season,
            'endpoint': endpoint,
            'error': str(error),
            'timestamp': time.time()
        })
        self.save()

    def is_completed(self, season, endpoint):
        """Check if task already completed"""
        key = f"{season}_{endpoint}"
        return key in self.checkpoint['completed']

    def get_resume_point(self):
        """Get season to resume from"""
        return self.checkpoint.get('last_season', None)

# Usage in scraper:
checkpoint = CheckpointManager()
start_season = checkpoint.get_resume_point() or 2015

for season in range(start_season, 2026):
    for endpoint in endpoints:
        if checkpoint.is_completed(season, endpoint):
            print(f"Skipping {season} {endpoint} (already completed)")
            continue

        try:
            data = scrape_endpoint(season, endpoint)
            save_to_s3(data)
            checkpoint.mark_completed(season, endpoint)
        except Exception as e:
            checkpoint.mark_failed(season, endpoint, e)
            continue  # Continue to next endpoint
```

---

#### **4. Data Quality Issues (HIGH RISK)**

**Problem:** Data from different sources may be inconsistent or missing

**Mitigation:**

**Step 1: Automated Quality Checks**
```python
def validate_game_data(game):
    """Run comprehensive quality checks"""
    issues = []

    # Check required fields
    required = ['game_id', 'game_date', 'home_team', 'away_team', 'home_score', 'away_score']
    for field in required:
        if field not in game or game[field] is None:
            issues.append(f"Missing required field: {field}")

    # Check score reasonableness
    if game.get('home_score', 0) < 50 or game.get('home_score', 0) > 200:
        issues.append(f"Unreasonable home score: {game.get('home_score')}")

    if game.get('away_score', 0) < 50 or game.get('away_score', 0) > 200:
        issues.append(f"Unreasonable away score: {game.get('away_score')}")

    # Check date range
    if game.get('game_date'):
        year = int(game['game_date'][:4])
        if year < 1946 or year > 2025:
            issues.append(f"Unreasonable game year: {year}")

    # Check player stats consistency
    if 'player_stats' in game:
        total_team_points = sum(p.get('points', 0) for p in game['player_stats'])
        reported_score = game.get('home_score', 0) + game.get('away_score', 0)
        if abs(total_team_points - reported_score) > 5:
            issues.append(f"Points mismatch: {total_team_points} vs {reported_score}")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'quality_score': max(0, 100 - len(issues) * 10)
    }
```

**Step 2: Quality Flag Database Table**
```sql
CREATE TABLE data_quality_log (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50),
    season INTEGER,
    data_source VARCHAR(50),
    quality_score INTEGER,  -- 0-100
    validation_date TIMESTAMP DEFAULT NOW(),
    issues JSONB,  -- Array of issue descriptions
    resolution_status VARCHAR(20) DEFAULT 'flagged',  -- flagged, resolved, ignored
    INDEX idx_game_season (game_id, season),
    INDEX idx_quality_score (quality_score)
);
```

**Step 3: Automated Remediation**
```python
def remediate_data_issues(game, issues):
    """Attempt to fix common data issues"""

    # Fix 1: Fill missing scores from box score player totals
    if 'Missing home_score' in issues and 'player_stats' in game:
        home_players = [p for p in game['player_stats'] if p['team_id'] == game['home_team']]
        game['home_score'] = sum(p.get('points', 0) for p in home_players)

    # Fix 2: Infer game_date from season and game_number
    if 'Missing game_date' in issues and game.get('season') and game.get('game_number'):
        season_start = f"{game['season']}-10-15"  # Approximate season start
        game['game_date'] = season_start  # Rough estimate

    # Fix 3: Cross-validate with other sources
    if game.get('game_id'):
        # Try to fetch from other sources
        for source in ['espn', 'nba_stats', 'basketball_ref']:
            alt_game = fetch_from_source(source, game['game_id'])
            if alt_game:
                # Fill missing fields
                for field in ['home_score', 'away_score', 'game_date']:
                    if not game.get(field) and alt_game.get(field):
                        game[field] = alt_game[field]

    return game
```

---

#### **5. AWS Cost Overrun (LOW RISK, HIGH IMPACT)**

**Mitigation:**

**Daily Cost Monitoring Script:**
```bash
#!/bin/bash
# scripts/monitoring/check_daily_costs.sh

# Get yesterday's costs
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)

COST=$(aws ce get-cost-and-usage \
    --time-period Start=$YESTERDAY,End=$TODAY \
    --granularity DAILY \
    --metrics UnblendedCost \
    --query 'ResultsByTime[0].Total.UnblendedCost.Amount' \
    --output text)

echo "Yesterday's cost: \$$COST"

# Alert if over $5/day (= $150/month)
if (( $(echo "$COST > 5" | bc -l) )); then
    echo "⚠️  WARNING: Daily cost exceeded \$5 threshold!"
    echo "Subject: AWS Cost Alert - NBA Simulator" | \
        mail -s "Cost Alert" your-email@example.com
fi
```

**Set up as daily cron job:**
```bash
# Add to crontab
0 9 * * * /Users/ryanranft/nba-simulator-aws/scripts/monitoring/check_daily_costs.sh
```

---

### **Contingency Plans:**

#### **Scenario 1: NBA API Completely Blocked**
- **Action:** Use hoopR + ESPN data only
- **Impact:** Lose advanced tracking stats (2013+), synergy play types (2015+)
- **Workaround:** Train models on traditional stats only, accept 10-15% lower R² performance

#### **Scenario 2: Basketball Reference Blocks Scraper**
- **Action:** Use Kaggle database for historical data (1946-1999)
- **Impact:** Lose real-time updates, some advanced metrics
- **Workaround:** One-time Kaggle download provides 80% of historical data

#### **Scenario 3: RDS Runs Out of Disk Space**
- **Action:** Resize RDS storage (can be done with minimal downtime)
- **Impact:** ~5-10 minutes downtime, additional $10-20/month
- **Prevention:** Set CloudWatch alarm at 80% disk usage

#### **Scenario 4: Budget Exceeded Before Completion**
- **Action:** Pause NBA API Digital Era collection (2000-2014)
- **Impact:** Lose 14 years of advanced stats
- **Workaround:** Focus on modern era (2015+) for ML training, add historical later

#### **Scenario 5: Major Scraper Bug Discovered Mid-Collection**
- **Action:** Use checkpoint system to resume from last good state
- **Impact:** 1-2 days lost time to fix bug and resume
- **Prevention:** Extensive testing in dev environment before production

---

## 🧪 Testing & Validation Strategy

### **Testing Pyramid:**

```
                    /\
                   /  \
                  / E2E \ (10% - 5 tests)
                 /------\
                /        \
               / Integration \ (30% - 15 tests)
              /------------\
             /              \
            /  Unit Tests    \ (60% - 30+ tests)
           /------------------\
```

### **1. Unit Tests (60% of tests)**

**Test Categories:**

**A. Data Extraction Tests**
```python
# tests/unit/test_data_extraction.py

def test_extract_espn_game_id():
    """Test ESPN game ID extraction from JSON"""
    raw_json = {'id': '401234567', 'name': 'LAL @ BOS'}
    game_id = extract_game_id(raw_json, source='espn')
    assert game_id == '401234567'

def test_extract_nba_stats_player_id():
    """Test NBA Stats player ID extraction"""
    raw_json = {'PERSON_ID': 2544, 'PLAYER_NAME': 'LeBron James'}
    player_id = extract_player_id(raw_json, source='nba_stats')
    assert player_id == '2544'

def test_handle_missing_fields():
    """Test graceful handling of missing fields"""
    incomplete_json = {'home_team': 'LAL'}  # Missing away_team
    result = extract_game_data(incomplete_json)
    assert result['away_team'] is None
    assert result['data_quality_flag'] == 'incomplete'
```

**B. Data Transformation Tests**
```python
# tests/unit/test_transformations.py

def test_timestamp_conversion():
    """Test ESPN timestamp to ISO8601"""
    espn_time = "2023-10-15T19:30:00Z"
    iso_time = convert_to_iso8601(espn_time)
    assert iso_time == "2023-10-15T19:30:00+00:00"

def test_score_validation():
    """Test score reasonableness checks"""
    assert is_reasonable_score(110) == True
    assert is_reasonable_score(250) == False
    assert is_reasonable_score(30) == False

def test_player_name_normalization():
    """Test player name standardization"""
    assert normalize_player_name("LeBron James") == "lebron_james"
    assert normalize_player_name("Giannis Antetokounmpo") == "giannis_antetokounmpo"
```

**C. Quality Scoring Tests**
```python
# tests/unit/test_quality_scoring.py

def test_quality_score_calculation():
    """Test data quality score calculation"""
    perfect_record = {
        'points': 25, 'rebounds': 10, 'assists': 5,
        'precision_level': 'second', 'num_sources': 3
    }
    assert calculate_quality_score(perfect_record) == 100

    poor_record = {
        'points': None, 'rebounds': None,
        'precision_level': 'game', 'num_sources': 1
    }
    assert calculate_quality_score(poor_record) < 60
```

**Run Unit Tests:**
```bash
pytest tests/unit/ -v --cov=scripts/etl --cov-report=html
# Expected runtime: 10-30 seconds
# Expected coverage: >80%
```

---

### **2. Integration Tests (30% of tests)**

**Test Categories:**

**A. Multi-Source Integration Tests**
```python
# tests/integration/test_multi_source.py

def test_cross_source_id_mapping():
    """Test ID mapping across ESPN, NBA Stats, Basketball Ref"""
    espn_game_id = "401234567"
    nba_stats_id = map_id(espn_game_id, from_source='espn', to_source='nba_stats')
    bbref_id = map_id(espn_game_id, from_source='espn', to_source='basketball_ref')

    assert nba_stats_id == "0022100500"
    assert bbref_id == "202110250BOS"

def test_deduplication_priority():
    """Test source priority in deduplication"""
    conflicting_records = [
        {'source': 'nba_stats', 'points': 30},
        {'source': 'espn', 'points': 28},
        {'source': 'basketball_ref', 'points': 31}
    ]
    result = deduplicate(conflicting_records)
    assert result['points'] == 30  # NBA Stats wins
    assert result['source_priority'] == 'nba_stats'
```

**B. ETL Pipeline Tests**
```python
# tests/integration/test_etl_pipeline.py

def test_s3_to_rds_pipeline():
    """Test complete ETL pipeline from S3 to RDS"""
    # Upload test file to S3
    test_data = {'game_id': 'test123', 'home_score': 110}
    s3.put_object(
        Bucket='nba-sim-raw-data-lake',
        Key='test/game_test123.json',
        Body=json.dumps(test_data)
    )

    # Run ETL
    extract_from_s3('test/game_test123.json')
    transform_and_load()

    # Verify in RDS
    result = db.query("SELECT * FROM games WHERE game_id = 'test123'")
    assert result[0]['home_score'] == 110

def test_quality_flag_propagation():
    """Test quality flags propagate through pipeline"""
    bad_data = {'game_id': 'bad123', 'home_score': 300}  # Unreasonable score
    load_to_rds(bad_data)

    quality_log = db.query("SELECT * FROM data_quality_log WHERE game_id = 'bad123'")
    assert quality_log[0]['quality_score'] < 60
    assert 'Unreasonable home score' in quality_log[0]['issues']
```

**Run Integration Tests:**
```bash
pytest tests/integration/ -v --cov=scripts/etl --cov-report=html
# Expected runtime: 2-5 minutes
# Expected coverage: >70%
```

---

### **3. End-to-End Tests (10% of tests)**

**Test Categories:**

**A. Complete Scraper Workflow Test**
```python
# tests/e2e/test_complete_scraper.py

@pytest.mark.slow
def test_nba_api_scraper_complete_season():
    """Test NBA API scraper for one complete season"""
    # This is a LONG test (30-60 minutes)
    scraper = NBAAPIScraper(start_season=2023, end_season=2024, limit_games=10)
    scraper.run()

    # Verify output
    files = list_s3_files('nba_api_modern/2023/')
    assert len(files) >= 10  # At least 10 games scraped

    # Verify data quality
    for file in files:
        data = load_from_s3(file)
        quality = calculate_quality_score(data)
        assert quality >= 75  # Minimum quality threshold

@pytest.mark.slow
def test_basketball_ref_scraper_one_season():
    """Test Basketball Ref scraper for one season"""
    scraper = BasketballRefScraper(start_season=2023, end_season=2024)
    scraper.run()

    # Verify cached to S3
    files = list_s3_files('bbref_cache/2023/')
    assert len(files) > 0

    # Verify respects rate limits
    assert scraper.total_time >= (len(files) * 3.0)  # 3 seconds per request
```

**B. Complete ML Pipeline Test**
```python
# tests/e2e/test_ml_pipeline.py

@pytest.mark.slow
def test_possession_model_training():
    """Test complete ML training pipeline"""
    # Prepare data
    preparator = PossessionDataPreparator(2023, 2024)
    data = preparator.prepare_training_data()

    # Split data
    splitter = DataSplitter(data)
    X_train, X_val, X_test, y_train, y_val, y_test = splitter.chronological_split(2023, 2023)

    # Train model
    trainer = PossessionModelTrainer()
    model = trainer.train(X_train, y_train, X_val, y_val)

    # Evaluate
    metrics = trainer.evaluate(X_test, y_test)

    # Verify performance
    assert metrics['rmse'] < 0.7  # Target: RMSE < 0.7
    assert metrics['ppp_error'] < 0.05  # Target: PPP error < 0.05
```

**Run E2E Tests:**
```bash
pytest tests/e2e/ -v --cov=scripts --cov-report=html -m slow
# Expected runtime: 30-90 minutes
# Run nightly, not on every commit
```

---

### **4. Data Validation Tests (Workflow #41)**

**Use existing test suites:**

```bash
# 1. Feature engineering readiness (10-30s)
python notebooks/test_feature_engineering.py

# 2. Scraper monitoring system (30-60s)
bash scripts/monitoring/test_monitoring_system.sh --verbose

# 3. Temporal query functionality (1-3 min)
pytest tests/test_temporal_queries.py -v
```

**Expected Output:**
```
FEATURE ENGINEERING TEST RESULTS
================================================================================
✅ PASS: Possession panel exists (45,678 rows)
✅ PASS: Team season stats exist (330 team-seasons)
✅ PASS: 40+ features available per possession
✅ PASS: No NaN values in critical features
✅ PASS: Data quality score: 87/100
================================================================================
```

---

### **5. Continuous Integration (CI) Setup**

**GitHub Actions Workflow:**
```yaml
# .github/workflows/data-pipeline-tests.yml

name: Data Pipeline Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=scripts/etl --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v

  data-quality-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run data quality validation
        run: bash scripts/monitoring/test_monitoring_system.sh
```

---

### **Testing Schedule:**

| Test Type | Frequency | Trigger | Runtime |
|-----------|-----------|---------|---------|
| Unit Tests | Every commit | Git push | 10-30s |
| Integration Tests | Every commit | Git push | 2-5 min |
| E2E Tests | Nightly | Cron (2 AM) | 30-90 min |
| Data Quality Tests | After scraper runs | Manual | 2-5 min |
| Full Validation | Weekly | Manual | 4-8 hrs |

---

*Last Updated: October 9, 2025*
*Estimated Completion: December 17, 2025 (10 weeks)*
*Total Runtime: 500-800 hours continuous scraping*

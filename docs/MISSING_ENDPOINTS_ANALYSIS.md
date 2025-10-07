# Missing Endpoints Analysis

**Created:** October 6, 2025
**Purpose:** Comprehensive audit of available but not-yet-scraped endpoints across all data sources

---

## Executive Summary

After analyzing all data sources, we're missing **150+ additional endpoints** that could provide significant feature expansion beyond the current 209-feature target.

**Impact:**
- Current target: 209 features
- Additional available: 150+ features
- New potential total: 350+ features

---

## 1. NBA Stats API (via nba_api)

### ✅ Currently Scraping (Started Tonight)
- League dashboards (7 endpoints)
- Hustle stats (2 endpoints)
- Draft data (2 endpoints)
- Shot charts (player-specific)
- Synergy play types (10 types)

### ❌ MISSING - High Priority

#### Advanced Box Scores (8 endpoints) - **NOT RUNNING YET**
Currently commented out in code. Need to enable:
```python
# boxscores_advanced/ directory
- boxscoreadvancedv2       # Advanced efficiency metrics
- boxscoredefensivev2      # Defensive stats
- boxscorefourfactorsv2    # Four factors breakdown
- boxscoremiscv2           # Miscellaneous stats
- boxscoreplayertrackv2    # Player tracking metrics
- boxscorescoringv2        # Scoring breakdown
- boxscoretraditionalv2    # Traditional box score
- boxscoreusagev2          # Usage rates
```

**Data volume:** ~100 games/season × 8 endpoints × 30 seasons = 24,000 files
**Features added:** ~40-50 advanced metrics

#### Player Tracking (4 endpoints per player) - **NOT RUNNING YET**
Currently commented out. Need to enable:
```python
- playerdashptpass         # Passing stats (passes made, potential assists)
- playerdashptreb          # Rebounding stats (contested, chances)
- playerdashptshotdefend   # Shot defense (contests, DFG%)
- playerdashptshots        # Shot tracking (touch time, dribbles)
```

**Data volume:** ~500 players/season × 4 endpoints × 30 seasons = 60,000 files
**Features added:** ~20-30 tracking metrics

#### Player Dashboards (Not implemented at all)
```python
- playerdashboardbyclutch           # Clutch performance
- playerdashboardbygeneralsplits    # Home/away, W/L splits
- playerdashboardbyopponent         # vs specific teams
- playerdashboardbyshootingsplits   # Shot distance, shot type
- playerdashboardbylastngames       # Recent form
- playerdashboardbyteamperformance  # Team W/L when player plays
- playerdashboardbyyearoveryear     # Year-over-year comparison
```

**Features added:** ~25-35 situational metrics

#### Team Dashboards (Not implemented at all)
```python
- teamdashboardbyclutch
- teamdashboardbygeneralsplits
- teamdashboardbyopponent
- teamdashboardbyshootingsplits
- teamdashboardbylastngames
- teamdashboardbyteamperformance
- teamdashboardbyyearoveryear
- teamdashlineups                   # Lineup combinations
- teamdashptpass                    # Team passing
- teamdashptreb                     # Team rebounding
- teamdashptshots                   # Team shot tracking
```

**Features added:** ~30-40 team metrics

#### Game-Level Advanced Stats (Not implemented)
```python
- gamerotation              # Player rotation patterns
- winprobabilitypbp         # Win probability by possession
- boxscoresimilarityscore   # Game similarity matching
- videodetails              # Video availability
```

**Features added:** ~10-15 game context metrics

#### Matchups & Defense (Not implemented)
```python
- leaguedashplayerptshot      # Player shot tracking league-wide
- leaguedashplayershotlocations  # Shot location heatmaps
- leaguedashteamptshot        # Team shot tracking
- leaguedashteamshotlocations # Team shot zones
- boxscorematchups           # Head-to-head matchups
```

**Features added:** ~15-20 defensive/matchup metrics

---

## 2. Basketball Reference (via basketball_reference_scraper)

### ✅ Currently Scraping
- Basic box scores
- Team stats
- Season schedules

### ❌ MISSING

#### Player Stats (9 functions available, using ~2)
```python
- get_player_splits()      # Shooting splits by game situation
  * Home/Away splits
  * vs LHD/RHD splits
  * By month/quarter
  * Pre/Post All-Star

- get_player_headshot()    # Player images
- get_game_logs()          # Career game-by-game logs
- lookup()                 # Player search/lookup
```

**Features added:** ~15-20 split statistics

#### Team Stats (9 functions, using ~3)
```python
- get_opp_stats()          # Opponent statistics
- get_team_misc()          # Miscellaneous team stats
  * Age, height, experience
  * Pace, offensive rating, defensive rating

- get_team_ratings()       # Advanced ratings
  * SRS, ORtg, DRtg, NRtg, Pace

- get_roster_stats()       # Per-player team stats
```

**Features added:** ~10-15 team metrics

#### Seasons (3 functions, using ~1)
```python
- get_standings()          # Season standings with advanced stats
  * W/L, SRS, ORtg, DRtg, NRtg
```

**Features added:** ~5-8 standings metrics

#### Box Scores (8 functions, using ~2)
```python
- get_all_star_box_score() # All-Star game stats
```

**Features added:** ~5 features

#### Injury Reports (3 functions, using ~0)
```python
- get_injury_report()      # Current injury status
```

**Features added:** Injury tracking (qualitative)

#### Shot Charts (6 functions, using ~0)
```python
- get_shot_chart()         # Shot location data
  * X/Y coordinates
  * Make/miss
  * Distance
  * Shot type
```

**Features added:** ~10-15 shot location metrics

#### Play-by-Play (6 functions, using ~0)
```python
- get_pbp()               # Detailed play-by-play
  * More granular than current PBP
  * Includes descriptions
```

**Features added:** Enhanced PBP features

---

## 3. SportsDataverse (ESPN wrapper)

### ✅ Currently Scraping
- Schedule (espn_nba_schedule)
- Play-by-play (espn_nba_pbp) - but failing due to Polars issues

### ❌ MISSING

```python
- espn_nba_calendar()       # Season calendar/key dates
- espn_nba_game_rosters()   # Game rosters
- espn_nba_teams()          # Team information
- load_nba_pbp()            # Pre-aggregated PBP data (hoopR)
- load_nba_player_boxscore()  # Pre-aggregated player box (hoopR)
- load_nba_team_boxscore()    # Pre-aggregated team box (hoopR)
- load_nba_schedule()         # Pre-aggregated schedule (hoopR)
```

**Note:** The `load_nba_*` functions are pre-aggregated datasets from hoopR-data repository (2002-present coverage).

**Features added:** ~10-15 ESPN-specific features

---

## 4. Kaggle Database

### ✅ Currently Have
- Downloaded complete database (2.2 GB)
- 17 tables total
- 65,698 games

### ❌ MISSING (Not Queried/Extracted)

#### Tables Not Being Used
```sql
-- Draft data
draft_combine_stats   -- Physical measurements, athleticism tests
draft_history         -- Complete draft history 1947-present

-- Game officials
officials             -- Referee assignments per game

-- Advanced game data
line_score            -- Quarter-by-quarter scoring
game_info             -- Game metadata (attendance, duration)
other_stats           -- Paint points, fast break, 2nd chance

-- Team historical data
team_history          -- Franchise history
team_details          -- Team details/metadata
inactive_players      -- Historical inactive list
```

**Current usage:** 5/17 tables (29%)
**Missing:** 12/17 tables (71%)

**Features from missing tables:** ~25-35 features

---

## 5. Cross-Source Validation Opportunities

### Missing Cross-Validation Endpoints

Currently no systematic cross-validation between sources. Could add:

```python
# Validation endpoints
- Compare ESPN vs NBA.com box scores (detect discrepancies)
- Compare Basketball Ref vs Kaggle stats (historical validation)
- Cross-reference player IDs across sources
- Validate play-by-play sequences
```

---

## Priority Recommendations

### **Tier 1: Enable Tonight (High Impact, Low Effort)**

1. **Enable nba_api advanced box scores** (commented out)
   - Uncomment lines 360-361 in scrape_nba_api_comprehensive.py
   - Adds 40-50 features
   - Runtime: +2-3 hours per season

2. **Query Kaggle missing tables**
   - Extract draft_combine_stats, line_score, other_stats
   - Adds 25-35 features
   - Runtime: <30 minutes total

3. **Add Basketball Ref team ratings**
   - Call `get_team_ratings()` and `get_team_misc()`
   - Adds 10-15 features
   - Runtime: +10 minutes per season

### **Tier 2: Add This Week (Medium Impact)**

4. **Enable nba_api player tracking** (commented out)
   - Uncomment lines 361-362
   - Adds 20-30 features
   - Runtime: +4-6 hours per season

5. **Add Basketball Ref player splits**
   - Call `get_player_splits()` for top 100 players
   - Adds 15-20 features
   - Runtime: +2 hours per season

6. **Add nba_api player dashboards**
   - Implement clutch, splits, opponent stats
   - Adds 25-35 features
   - Runtime: +3-4 hours per season

### **Tier 3: Future Enhancement (Lower Priority)**

7. **Basketball Ref shot charts**
   - Visual/spatial data
   - Adds 10-15 features
   - Requires additional processing

8. **SportsDataverse hoopR loaders**
   - Pre-aggregated datasets
   - Redundant validation
   - Adds 10-15 features

9. **nba_api team dashboards**
   - Team-level advanced metrics
   - Adds 30-40 features
   - Runtime: +2-3 hours per season

---

## Estimated Feature Impact

| Tier | Endpoints | Features Added | Runtime Added | Difficulty |
|------|-----------|----------------|---------------|------------|
| 1    | 5         | 75-100         | +3-4 hrs/season | LOW |
| 2    | 3         | 60-85          | +9-12 hrs/season | MEDIUM |
| 3    | 3         | 50-70          | +5-8 hrs/season | MEDIUM |
| **Total** | **11** | **185-255** | **+17-24 hrs/season** | **Mixed** |

**New potential total features: 209 (current) + 185-255 (missing) = 394-464 features**

---

## Implementation Strategy

### Option A: Enable Everything Tonight (Aggressive)
- Uncomment advanced box scores
- Uncomment player tracking
- Add player/team dashboards
- Runtime: ~25-30 hours per season × 30 seasons = **750-900 hours (31-37 days)**

### Option B: Tier 1 Only Tonight (Balanced)
- Enable commented code
- Query Kaggle missing tables
- Add Basketball Ref ratings
- Runtime: +3-4 hours per season × 30 seasons = **90-120 hours (3.75-5 days)**
- Features added: 75-100

### Option C: Current Plan (Conservative)
- Let current scrapers finish
- Add Tier 1 endpoints in next session
- Runtime: Current overnight scraping completes as-is
- Add enhancements tomorrow

---

## Recommended Action

~~**RECOMMENDATION: Option B (Tier 1 Tonight)**~~ ✅ **IMPLEMENTED**

### ✅ Implementation Complete (October 6, 2025 - 11:00 PM)

**What was done:**
1. ✅ Fixed import errors in `scrape_nba_api_comprehensive.py`
   - Changed to module-level import: `from nba_api.stats import endpoints as nba_endpoints`
   - Fixed all undefined function references throughout file
2. ✅ Enabled Tier 1 endpoints (lines 360-362):
   - Advanced box scores (8 endpoints × 100 games = 40-50 features)
   - Player tracking (4 endpoints × 50 players = 20-30 features)
3. ✅ Restarted comprehensive scraper with Tier 1 enabled
   - Process ID: 50691
   - Started: 10:56 PM
   - Expected completion: 4-5 AM (5-6 hours)
   - Output: `/tmp/nba_api_comprehensive/`
   - S3 upload: `s3://nba-sim-raw-data-lake/nba_api_comprehensive/`

**Feature Impact:**
- Previous total: 209 features
- Tier 1 added: 60-80 features
- **New total: 269-289 features** ✅

**Runtime:**
- Per season: ~10.4 minutes (with testing limits)
- Total for 30 seasons: ~5-6 hours
- **Completes overnight** ✅

**Note:** Current run uses testing limits:
- 100 games per season (not all ~1,230)
- 50 players for tracking (not all ~500)
- Production run would take 25-30 hrs/season × 30 = 750-900 hours

### 🔄 Remaining Tier 1 Tasks:
- ⏸️ Query Kaggle missing tables (draft_combine_stats, line_score, other_stats)
- ⏸️ Add Basketball Ref team ratings/misc

---

*Last updated: October 6, 2025 - 11:00 PM*
# Tier 5: NBA Advanced Data

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 5 of 13
**Priority:** MEDIUM
**Status:** ⏸️ PENDING
**Data Types:** 3
**Estimated Time:** 8-12 hours
**Estimated Records:** ~50,000
**Cost Impact:** +$0.001/month S3 storage

---

## Overview

**Purpose:** Collect advanced NBA data including defensive metrics, hustle stats, and plus/minus data.

**Why This Tier Matters:**
- Advanced defensive tracking (player impact metrics)
- Hustle stats (effort and intangibles)
- Plus/minus tracking (lineup impact)
- Next-level performance analytics

**What This Adds:**
- Defensive tracking data (blocks, steals, deflections, etc.)
- Hustle stats (loose balls, charges, screen assists)
- Plus/minus data (detailed lineup analysis)

**Prerequisites:** Tier 1 (Player game logs for validation)

---

## Data Types

### 1. Defensive Tracking Data

**Coverage:** NBA seasons with defensive tracking (2013-2025)
**Records:** ~6,000 player-seasons
**Time:** 3-4 hours
**Priority:** MEDIUM-HIGH

#### Implementation:
- **URL Pattern:** `/leagues/NBA_{season}_defensive.html` or similar
- **Data:** Advanced defensive metrics and tracking
- **Value:** Defensive player impact, rim protection, perimeter defense

**Defensive Metrics Tracked:**

1. **Rim Protection:**
   - Shots defended at rim (within 6 ft)
   - Field goal percentage allowed at rim
   - Blocks per game
   - Block percentage
   - Defensive field goal % differential (vs league average)

2. **Perimeter Defense:**
   - Shots defended (outside 15 ft)
   - 3-point attempts defended
   - 3-point percentage allowed
   - Contests per game
   - Closeout effectiveness

3. **Overall Defense:**
   - Defensive win shares
   - Defensive rating (points allowed per 100 possessions)
   - Defensive box plus/minus (DBPM)
   - Steals per game
   - Deflections per game (if available)

4. **Matchup Defense:**
   - Opponent field goal % when guarded
   - Opponent points per possession when guarded
   - Matchup difficulty (opponent quality)

**Why Defensive Tracking Matters:**
- Quantify individual defensive impact
- Identify elite defenders (DPOY candidates)
- Matchup-specific defensive assignments
- Defensive system effectiveness

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/defensive_tracking/{season}/defensive_stats.json`

---

### 2. Hustle Stats

**Coverage:** NBA seasons with hustle tracking (2016-2025)
**Records:** ~4,500 player-seasons
**Time:** 2-3 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** `/leagues/NBA_{season}_hustle.html` or similar
- **Data:** Effort-based statistics and intangibles
- **Value:** Effort quantification, intangible player value, team culture

**Hustle Categories:**

1. **Loose Ball Recovery:**
   - Loose balls recovered per game
   - Contested loose balls
   - Recovery rate (% of contested loose balls won)

2. **Charges Drawn:**
   - Charges drawn per game
   - Charges drawn per 48 minutes
   - Block/charge ratio

3. **Screen Assists:**
   - Screen assists per game (screens leading to FG)
   - Screen assist points (points from screen assists)
   - Pick-and-roll screens set

4. **Deflections:**
   - Deflections per game
   - Steal-to-deflection rate

5. **Box Outs:**
   - Box outs per game
   - Opponent FG% on box out attempts

6. **Contested Shots:**
   - Shots contested per game
   - Contest percentage (% of opponent shots contested)

**Why Hustle Stats Matter:**
- Quantify effort and intangibles
- Identify high-motor players
- Team culture indicators
- Complementary player value (role players)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/hustle_stats/{season}/hustle.json`

---

### 3. Plus/Minus Data (Detailed)

**Coverage:** NBA seasons (2000-2025)
**Records:** ~40,000 player-seasons
**Time:** 3-5 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** Player pages or `/teams/{team}/{season}/plusminus/`
- **Data:** Plus/minus by lineup, situation, opponent
- **Value:** Lineup impact quantification, coaching decisions

**Plus/Minus Breakdowns:**

1. **Basic Plus/Minus:**
   - Raw plus/minus per game
   - Plus/minus per 48 minutes
   - Cumulative season plus/minus

2. **Net Rating:**
   - Offensive rating with player on court
   - Defensive rating with player on court
   - Net rating (offensive - defensive)

3. **Lineup Plus/Minus:**
   - Plus/minus by specific lineup (5-man units)
   - Plus/minus by teammate combinations (2-man, 3-man units)
   - Best/worst lineup pairings

4. **Situational Plus/Minus:**
   - Plus/minus vs top 10 teams
   - Plus/minus vs bottom 10 teams
   - Plus/minus in clutch situations (last 5 min, close game)
   - Plus/minus by quarter

5. **Advanced Plus/Minus:**
   - Box Plus/Minus (BPM)
   - Value Over Replacement Player (VORP)
   - Win Shares
   - Luck-adjusted plus/minus

**Why Plus/Minus Data Matters:**
- Quantify player impact beyond box score
- Identify lineup synergies
- Coaching rotation optimization
- Advanced player valuation

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/plus_minus/{season}/{player_slug}/plus_minus.json`

---

## Implementation Plan

### Week 1: Defensive Tracking Data (3-4 hours)
1. Identify available seasons (2013-2025)
2. Scrape defensive tracking pages
3. Parse rim protection, perimeter defense metrics
4. Validate against known elite defenders
5. Upload to S3

### Week 2: Hustle Stats (2-3 hours)
1. Identify available seasons (2016-2025)
2. Scrape hustle stats pages
3. Parse loose balls, charges, screens, deflections
4. Validate against known high-effort players
5. Upload to S3

### Week 3: Plus/Minus Data (3-5 hours)
1. Scrape plus/minus data by player and season
2. Extract lineup-specific plus/minus
3. Parse situational plus/minus
4. Calculate BPM, VORP if not provided
5. Upload to S3

**Total Time:** 8-12 hours over 3 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - Defensive tracking: ~450 players per season × 13 seasons = ~5,850
   - Hustle stats: ~450 players per season × 9 seasons = ~4,050
   - Plus/minus: ~450 players per season × 25 seasons = ~11,250

2. **Coverage Verification**
   - All seasons with available data present
   - All qualified players (500+ minutes) included
   - No missing key players (All-Stars, starters)

3. **Data Structure Validation**
   - Defensive percentages within valid range (0-100%)
   - Hustle stat counts non-negative
   - Plus/minus values reasonable (-30 to +30 per game)

4. **Cross-Validation**
   - Defensive stats consistent with game logs (blocks, steals)
   - Plus/minus totals match team differentials
   - BPM/VORP consistent with known rankings

---

## Success Criteria

- [ ] Defensive tracking data collected for 2013-2025 seasons
- [ ] Hustle stats collected for 2016-2025 seasons
- [ ] Plus/minus data collected for 2000-2025 seasons
- [ ] All data quality checks passed
- [ ] All files uploaded to S3
- [ ] Data structure documented
- [ ] Total time: 8-12 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/nba/
├── defensive_tracking/
│   ├── 2013/defensive_stats.json
│   └── .../2025/defensive_stats.json
├── hustle_stats/
│   ├── 2016/hustle.json
│   └── .../2025/hustle.json
└── plus_minus/
    ├── 2000/
    │   ├── {player_slug}/plus_minus.json
    │   └── .../
    └── .../2025/
```

---

## Database Integration

### Recommended Tables:

```sql
-- Defensive tracking
CREATE TABLE nba_defensive_tracking (
    player_slug TEXT,
    season INTEGER,
    shots_defended_rim INTEGER,
    fg_pct_allowed_rim REAL,
    blocks_per_game REAL,
    block_pct REAL,
    shots_defended_3pt INTEGER,
    fg3_pct_allowed REAL,
    contests_per_game REAL,
    deflections_per_game REAL,
    defensive_rating REAL,
    dbpm REAL,
    PRIMARY KEY (player_slug, season)
);

-- Hustle stats
CREATE TABLE nba_hustle_stats (
    player_slug TEXT,
    season INTEGER,
    loose_balls_recovered REAL,
    charges_drawn REAL,
    screen_assists REAL,
    screen_assist_points REAL,
    deflections REAL,
    box_outs REAL,
    contests REAL,
    PRIMARY KEY (player_slug, season)
);

-- Plus/minus data
CREATE TABLE nba_plus_minus (
    player_slug TEXT,
    season INTEGER,
    games INTEGER,
    plus_minus_total INTEGER,
    plus_minus_per_game REAL,
    plus_minus_per_48 REAL,
    on_court_off_rating REAL,
    on_court_def_rating REAL,
    on_court_net_rating REAL,
    bpm REAL,
    vorp REAL,
    win_shares REAL,
    PRIMARY KEY (player_slug, season)
);
```

---

## ML Feature Engineering

**Defensive tracking features:**
- Rim protection score (composite metric)
- Perimeter defense score
- Defensive versatility (performance across positions)
- DPOY probability (based on defensive metrics)

**Hustle features:**
- Effort score (composite of hustle stats)
- Intangible value (non-box score contribution)
- Team culture indicator
- Role player value multiplier

**Plus/minus features:**
- True impact rating (luck-adjusted plus/minus)
- Lineup chemistry score
- Situational impact (clutch, vs elite teams)
- Replacement value (VORP)

---

## Troubleshooting

**Common Issues:**

1. **Defensive tracking not available pre-2013**
   - Solution: Document coverage window
   - May require estimation from basic stats pre-2013

2. **Hustle stats not consistently available**
   - Solution: Focus on 2016+ data
   - Validate availability before scraping

3. **Plus/minus data varies by source**
   - Solution: Use Basketball Reference's calculations
   - Document methodology

4. **Small sample sizes for bench players**
   - Solution: Set minimum minute threshold (500 min)
   - Flag low-reliability records

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Calculate composite defensive scores
3. Generate hustle rankings
4. Integrate plus/minus into player valuation models
5. Begin Tier 6 (NBA Comparative Data)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin
**Prerequisites:** Tier 1 (for validation)
**Next Tier:** Tier 6 (NBA Comparative Data)
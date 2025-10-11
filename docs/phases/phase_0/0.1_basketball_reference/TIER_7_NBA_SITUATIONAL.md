# Tier 7: NBA Situational Data

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 7 of 13
**Priority:** MEDIUM
**Status:** ⏸️ PENDING
**Data Types:** 4
**Estimated Time:** 10-15 hours
**Estimated Records:** ~75,000
**Cost Impact:** +$0.001/month S3 storage

---

## Overview

**Purpose:** Collect NBA situational data for clutch performance, rest analysis, travel impact, and schedule analysis.

**Why This Tier Matters:**
- Clutch performance (late-game situations)
- Rest and fatigue impact (back-to-backs, days off)
- Travel effects (time zones, distance)
- Schedule difficulty analysis

**What This Adds:**
- Clutch stats (last 5 minutes, close games)
- Rest/fatigue metrics
- Travel distance and timezone data
- Strength of schedule metrics

**Prerequisites:** Tier 1 (Game logs for situational analysis)

---

## Data Types

### 1. Clutch Statistics

**Coverage:** NBA games with clutch data (2000-2025)
**Records:** ~25,000 player-seasons with clutch stats
**Time:** 4-5 hours
**Priority:** MEDIUM-HIGH

#### Implementation:
- **URL Pattern:** Player splits pages or clutch-specific pages
- **Data:** Performance in clutch situations (last 5 min, within 5 points)
- **Value:** Late-game reliability, pressure performance, closer identification

**Clutch Definitions:**

1. **Standard Clutch:**
   - Last 5 minutes of 4th quarter or overtime
   - Score within 5 points (either direction)
   - Clutch minutes, possessions, field goals

2. **Ultra-Clutch:**
   - Last 2 minutes
   - Score within 3 points
   - Even more pressure

3. **Game-Winners:**
   - Shots in last 10 seconds
   - Game-winning shots (go-ahead baskets)
   - Buzzer beaters

**Clutch Metrics:**

1. **Clutch Shooting:**
   - Field goal attempts in clutch
   - Field goal percentage
   - 3-point attempts and percentage
   - Free throw attempts and percentage
   - Points in clutch per game

2. **Clutch Efficiency:**
   - True shooting % in clutch vs regular
   - Turnover rate in clutch
   - Assist-to-turnover ratio
   - Plus/minus in clutch situations

3. **Clutch Impact:**
   - Win probability added (WPA) in clutch
   - Clutch Win Shares
   - Clutch player rating

4. **Clutch Reliability:**
   - Clutch performance variance
   - Consistency in close games
   - Historical clutch track record

**Why Clutch Stats Matter:**
- Identify closers (who gets final shot?)
- Pressure performance evaluation
- Playoff predictor (clutch correlates with playoff success)
- Contract negotiations (clutch players command premium)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/clutch_stats/{player_slug}/{season}/clutch.json`

---

### 2. Rest and Fatigue Analysis

**Coverage:** All NBA games (1946-2025)
**Records:** ~60,000 team-game records with rest data
**Time:** 3-4 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** Calculate from game logs and schedules
- **Data:** Days of rest, back-to-backs, stretches
- **Value:** Fatigue impact, injury risk, rotation optimization

**Rest Categories:**

1. **Days of Rest:**
   - 0 days (back-to-back, 2nd game)
   - 1 day
   - 2 days
   - 3+ days
   - 7+ days (long break)

2. **Schedule Density:**
   - Games in last 7 days (1-7)
   - Games in last 14 days
   - Cumulative fatigue index

3. **Back-to-Back Analysis:**
   - 1st game of back-to-back vs 2nd game
   - Home-road vs road-home back-to-backs
   - 3-games-in-4-nights
   - 4-games-in-5-nights

**Rest Impact Metrics:**

1. **Performance by Rest:**
   - Win% by days of rest
   - Points scored by rest
   - Field goal% by rest
   - Defensive rating by rest

2. **Fatigue Indicators:**
   - Shot attempts decline
   - 3-point% decline (fatigue affects perimeter shooting)
   - Turnover increase
   - Minutes restriction

3. **Injury Correlation:**
   - Injury rate by rest category
   - Minutes played preceding injury
   - Games missed following heavy load

**Why Rest Data Matters:**
- Load management decisions
- Injury risk mitigation
- Lineup optimization (rest starters on back-to-backs)
- Home court scheduling advantage

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/rest_analysis/{season}/{team}/rest_data.json`

---

### 3. Travel and Timezone Impact

**Coverage:** All NBA games (1946-2025)
**Records:** ~60,000 games with travel data
**Time:** 3-4 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** Calculate from schedules, arena locations
- **Data:** Travel distance, timezone changes, home/road stretches
- **Value:** Travel fatigue quantification, schedule difficulty

**Travel Metrics:**

1. **Distance Traveled:**
   - Miles between games
   - Cumulative miles per month
   - Road trip total distance
   - Season total mileage

2. **Timezone Changes:**
   - West-to-East (harder)
   - East-to-West (easier)
   - Number of timezone crossings
   - Circadian rhythm disruption

3. **Road Trip Analysis:**
   - Games on road trip (1-7+ games)
   - Days on road
   - Back-to-back on road
   - Home return performance

**Travel Impact Metrics:**

1. **Performance by Travel:**
   - Win% by distance traveled
   - Win% by timezone change
   - Shooting% after long travel
   - Defensive rating on road trips

2. **Home/Road Splits:**
   - Home win%
   - Road win%
   - Home field advantage magnitude
   - Specific arena advantages (altitude in Denver, etc.)

3. **Schedule Quirks:**
   - "Circus trips" (long road stretches)
   - Grammy road trip (Lakers/Clippers)
   - Rodeo road trip (Spurs)

**Why Travel Data Matters:**
- Schedule strength adjustment
   - West coast teams travel more (larger distances)
   - East coast teams face more timezone changes
- Performance prediction (home/road, after travel)
- Betting market inefficiencies (travel undervalued?)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/travel_data/{season}/{team}/travel.json`

---

### 4. Strength of Schedule

**Coverage:** All NBA seasons (1946-2025)
**Records:** ~2,000 team-seasons
**Time:** 2-3 hours
**Priority:** LOW-MEDIUM

#### Implementation:
- **URL Pattern:** Calculate from schedules and opponent win%
- **Data:** SOS metrics, playoff odds adjustments
- **Value:** Fair team evaluation, playoff projections

**SOS Metrics:**

1. **Opponent Win%:**
   - Average opponent winning percentage
   - Adjusted for when games played (early/late season)
   - Home/road opponent strength

2. **Schedule Difficulty:**
   - Back-to-backs count
   - Road games %
   - Travel distance (total miles)
   - Timezone changes

3. **Remaining Schedule (In-Season):**
   - Remaining SOS
   - Playoff race implications
   - Tank race implications (easier schedule = better draft odds paradoxically hurt)

4. **Historical SOS:**
   - Easiest schedules (historical)
   - Hardest schedules (historical)
   - Division/conference strength over time

**SOS Applications:**

1. **Team Evaluation:**
   - Win total adjusted for SOS
   - "True talent" estimation
   - Playoff seeding fairness

2. **Playoff Projections:**
   - Expected wins (given SOS)
   - Playoff probability
   - Championship odds

3. **Award Voting:**
   - MVP consideration (team success + SOS)
   - Coach of the Year (overachievement vs SOS)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/strength_of_schedule/{season}/sos.json`

---

## Implementation Plan

### Week 1: Clutch Statistics (4-5 hours)
1. Scrape clutch stats from player split pages
2. Calculate clutch efficiency metrics
3. Identify clutch performers and underperformers
4. Validate against known clutch players (Kobe, Damian Lillard, etc.)
5. Upload to S3

### Week 2: Rest & Travel (6-8 hours)
1. Parse game schedules for rest days
2. Calculate back-to-back and fatigue metrics
3. Calculate travel distances from arena coordinates
4. Identify timezone changes
5. Analyze performance by rest and travel
6. Upload to S3

### Week 3: Strength of Schedule (2-3 hours)
1. Calculate opponent win% for each team-season
2. Compute schedule difficulty metrics
3. Generate SOS rankings
4. Upload to S3

**Total Time:** 10-15 hours over 3 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - Clutch stats: ~450 players × 25 seasons = ~11,250
   - Rest data: ~30 teams × 79 seasons × 82 games = ~192,780 games
   - Travel data: Same as rest data
   - SOS: ~30 teams × 79 seasons = ~2,370

2. **Coverage Verification**
   - Clutch data for all qualified players (500+ min)
   - Rest/travel data for all games
   - SOS calculated for all teams/seasons

3. **Data Structure Validation**
   - Clutch percentages reasonable (some variance expected)
   - Rest days non-negative
   - Travel distances positive, within US geography bounds
   - SOS values reasonable (0.400 to 0.600 typical range)

4. **Cross-Validation**
   - Clutch totals sum to game totals
   - Rest days match schedule gaps
   - Travel distances match known arena distances
   - SOS correlates with win totals

---

## Success Criteria

- [ ] Clutch stats collected for 2000-2025 seasons
- [ ] Rest analysis completed for all seasons
- [ ] Travel data calculated for all games
- [ ] Strength of schedule calculated for all team-seasons
- [ ] All data quality checks passed
- [ ] All files uploaded to S3
- [ ] Data structure documented
- [ ] Total time: 10-15 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/nba/
├── clutch_stats/
│   ├── {player_slug}/
│   │   ├── 2000/clutch.json
│   │   └── .../2025/clutch.json
│   └── .../
├── rest_analysis/
│   ├── 1947/
│   │   ├── LAL/rest_data.json
│   │   └── .../
│   └── .../2025/
├── travel_data/
│   ├── 1947/
│   │   ├── LAL/travel.json
│   │   └── .../
│   └── .../2025/
└── strength_of_schedule/
    ├── 1947/sos.json
    └── .../2025/sos.json
```

---

## Database Integration

### Recommended Tables:

```sql
-- Clutch statistics
CREATE TABLE nba_clutch_stats (
    player_slug TEXT,
    season INTEGER,
    clutch_minutes REAL,
    clutch_fga INTEGER,
    clutch_fgm INTEGER,
    clutch_fg_pct REAL,
    clutch_3pa INTEGER,
    clutch_3pm INTEGER,
    clutch_3p_pct REAL,
    clutch_points INTEGER,
    clutch_ts_pct REAL,
    clutch_plus_minus REAL,
    PRIMARY KEY (player_slug, season)
);

-- Rest analysis
CREATE TABLE nba_rest_analysis (
    game_id TEXT,
    team TEXT,
    game_date DATE,
    days_rest INTEGER,
    is_back_to_back BOOLEAN,
    games_in_7_days INTEGER,
    cumulative_fatigue_index REAL,
    PRIMARY KEY (game_id, team)
);

-- Travel data
CREATE TABLE nba_travel_data (
    game_id TEXT,
    team TEXT,
    miles_traveled REAL,
    timezone_change INTEGER,  -- Can be negative
    days_on_road INTEGER,
    road_trip_game_num INTEGER,
    PRIMARY KEY (game_id, team)
);

-- Strength of schedule
CREATE TABLE nba_strength_of_schedule (
    season INTEGER,
    team TEXT,
    opponent_win_pct REAL,
    back_to_backs INTEGER,
    road_games INTEGER,
    total_travel_miles REAL,
    sos_rank INTEGER,
    PRIMARY KEY (season, team)
);
```

---

## ML Feature Engineering

**Clutch features:**
- Clutch reliability score
- Pressure performance index
- Late-game usage prediction
- Closer identification

**Rest features:**
- Fatigue adjustment factor
- Injury risk score (based on load)
- Performance degradation curve
- Optimal rest days

**Travel features:**
- Home court advantage magnitude
- Road performance adjustment
- Travel fatigue coefficient
- Timezone disruption impact

**SOS features:**
- Win total adjustment (actual vs expected)
- Playoff probability adjustment
- True talent estimation
- Award voting adjustment

---

## Troubleshooting

**Common Issues:**

1. **Clutch data may not be available pre-2000**
   - Solution: Focus on 2000+ data
   - May require calculation from play-by-play pre-2000

2. **Arena coordinates needed for travel calculation**
   - Solution: Maintain arena location database
   - Account for relocations and arena changes

3. **Rest data requires accurate schedule parsing**
   - Solution: Cross-validate with official NBA schedules
   - Handle All-Star break, lockouts, COVID

4. **SOS changes throughout season**
   - Solution: Calculate both final SOS and in-season SOS
   - Track SOS evolution

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Build clutch performance predictor
3. Create rest/fatigue optimizer for rotations
4. Generate travel-adjusted power rankings
5. Begin Tier 8 (NBA Complete Data)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin
**Prerequisites:** Tier 1 (game logs for calculations)
**Next Tier:** Tier 8 (NBA Complete Data)
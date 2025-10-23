# Tier 13: College Basketball

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 13 of 13
**Priority:** OPTIONAL
**Status:** ⏸️ PENDING
**Data Types:** 30 total (collect 10-15 selectively)
**Estimated Time:** 30-40 hours (selective: 22 hours recommended)
**Estimated Records:** ~100,000 (selective) to ~200,000 (comprehensive)
**Cost Impact:** +$0.005/month S3 storage

---

## Overview

**Purpose:** Collect NCAA college basketball data for draft pipeline analysis, March Madness prediction, and college-to-pro transition modeling.

**Why This Tier Matters:**
- NBA/WNBA draft pipeline
- College to pro transition models
- March Madness prediction
- Player development tracking (high school → college → pro)
- Recruiting analysis

**What This Adds:**
- NCAA Tournament history (1939-2025)
- NCAA Division I player/team stats (modern era: 2000-2025 recommended)
- College awards and honors
- Conference tournaments
- Optional: Women's basketball, NIT, other tournaments

**Prerequisites:** None (pipeline context)

---

## Important Note: Different Domain

**⚠️ College basketball data is on a separate site:**
- **URL:** `https://www.sports-reference.com/cbb/`
- **NOT:** `basketball-reference.com`
- Scraper must handle different domain
- Rate limiting may differ

---

## Selective Collection Strategy

**RECOMMENDED: Tier 13A + 13B (22 hours, 100K records)**
- NCAA Tournament (all years)
- NCAA D1 player/team stats (2000-2025, modern era)

**OPTIONAL: Tier 13C (+5 hours, +3K records)**
- Add all college awards
- Add polls history (AP, Coaches)

**OPTIONAL: Tier 13D (+3 hours, +7K records)**
- Add NIT, women's basketball, miscellaneous

---

## Data Types

### PRIORITY 1: NCAA Tournament (5 types)

**Time:** 8-10 hours
**Records:** ~8,000
**Priority:** CRITICAL

#### 0.13.1: NCAA Tournament Results - Men's (1939-2025)

- **URL Pattern:** `https://www.sports-reference.com/cbb/postseason/{year}-ncaa.html`
- **Data:** Complete tournament brackets, game results
- **Coverage:** 87 tournaments (1939-2025, missing 2020 due to COVID)
- **Records:** ~5,000 games
- **Value:** March Madness complete history

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/ncaa_tournament/{year}/men/bracket.json`

---

#### 0.13.2: NCAA Tournament Results - Women's (1982-2025)

- **URL Pattern:** `https://www.sports-reference.com/cbb/postseason/{year}-ncaa-womens.html`
- **Data:** Women's tournament history
- **Coverage:** 44 tournaments (1982-2025)
- **Records:** ~2,500 games

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/ncaa_tournament/{year}/women/bracket.json`

---

#### 0.13.3: NCAA Tournament Most Outstanding Player

- **Data:** MOP award winners (men's and women's)
- **Records:** ~85 men's + ~44 women's = ~130

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/ncaa_tournament/mop/all_years.json`

---

#### 0.13.4: Final Four History

- **Data:** Final Four teams and results by year
- **Records:** ~350 (87 years × 4 teams)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/ncaa_tournament/final_four/all_years.json`

---

#### 0.13.5: NCAA Bracket History (Seeding, Upsets)

- **Data:** Seeding, upsets, Cinderella runs
- **Value:** Tournament analytics, bracket prediction

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/ncaa_tournament/upsets/all_years.json`

---

### PRIORITY 2: NCAA Division I Stats - Modern Era (5 types)

**Time:** 10-12 hours
**Records:** ~92,000
**Priority:** HIGH
**Focus:** 2000-2025 (26 seasons) for manageable scope

#### 0.13.6: NCAA D1 Player Stats (2000-2025)

- **URL Pattern:** `https://www.sports-reference.com/cbb/seasons/{season}-player-stats.html`
- **Data:** Season statistics (totals, per-game, advanced)
- **Coverage:** 26 seasons
- **Records:** ~80,000 player-seasons (26 years × ~3,000 D1 players/year)
- **Value:** College player performance, draft prospect analysis

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/player_stats/{season}/player_stats.json`

---

#### 0.13.7: NCAA D1 Team Stats (2000-2025)

- **URL Pattern:** `https://www.sports-reference.com/cbb/seasons/{season}-team-stats.html`
- **Data:** Team statistics (offensive, defensive, advanced)
- **Coverage:** 26 seasons
- **Records:** ~9,000 team-seasons (26 years × ~350 D1 teams)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/team_stats/{season}/team_stats.json`

---

#### 0.13.8: NCAA D1 Conference Standings (2000-2025)

- **Data:** Conference records, tournament berths
- **Coverage:** 26 seasons, ~35 conferences
- **Records:** ~900 (26 years × ~35 conferences)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/conference_standings/{season}/standings.json`

---

#### 0.13.9: NCAA D1 Schedule & Results (2000-2025) **[LARGE DATASET]**

- **Data:** Game-by-game results
- **Coverage:** 26 seasons
- **Records:** ~300,000 games (26 years × ~11,500 games/year)
- **⚠️ Note:** Very large dataset, consider sampling or omitting

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/schedules/{season}/games.json`

---

#### 0.13.10: College Coach Records (2000-2025)

- **Data:** Coaching records by season
- **Records:** ~3,000 (coaches × seasons)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/coaches/{season}/coach_records.json`

---

### PRIORITY 3: College Awards (5 types)

**Time:** 4-5 hours
**Records:** ~3,000
**Priority:** MEDIUM

#### 0.13.11: Player of the Year Awards

- **Awards:** AP Player of the Year, Wooden Award, Naismith Award, Oscar Robertson Trophy, etc.
- **Coverage:** All-time (varies by award)
- **Records:** ~500

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/awards/player_of_year/all_years.json`

---

#### 0.13.12: All-America Teams

- **Data:** First Team, Second Team, Third Team
- **Coverage:** All-time
- **Records:** ~1,500

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/awards/all_america/all_years.json`

---

#### 0.13.13: Conference Player of the Year

- **Data:** Awards by conference
- **Records:** ~1,000

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/college/awards/conference_poy/all_years.json`

---

#### 0.13.14-0.13.15: Additional Awards

- Coach of the Year
- Defensive Player of the Year
- Other conference awards

---

### PRIORITY 4: Additional College Data (15 types)

**Time:** 8-13 hours
**Records:** ~10,000
**Priority:** LOW (optional)

#### Polls (2 types) - 2 hours
- **0.13.16:** AP Poll history (2000-2025)
- **0.13.17:** Coaches Poll history (2000-2025)

#### Leaders (2 types) - 1 hour
- **0.13.18:** Season statistical leaders (2000-2025)
- **0.13.19:** Career leaders (all-time)

#### Tools (2 types) - 1 hour
- **0.13.20:** Player Season Finder (query tool)
- **0.13.21:** Team Season Finder (query tool)

#### Additional Tournaments (3 types) - 2 hours
- **0.13.22:** NIT Results (1938-2025)
- **0.13.23:** CBI Tournament (2008-2025)
- **0.13.24:** CIT Tournament (2009-2018, discontinued)

#### Women's College Basketball (3 types) - 4 hours
- **0.13.25:** Women's Player Stats (1981-2025)
- **0.13.26:** Women's Team Stats (1981-2025)
- **0.13.27:** Women's NCAA Tournament (covered in 0.13.2)

#### Miscellaneous (3 types) - 2 hours
- **0.13.28:** Conference Tournament Results (2000-2025)
- **0.13.29:** College Buzzer-Beaters
- **0.13.30:** College Milestones

---

## Implementation Plan

### Month 1: NCAA Tournament (2 weeks, 8-10 hours)
1. Scrape NCAA Tournament index
2. Extract men's tournament brackets (1939-2025)
3. Extract women's tournament brackets (1982-2025)
4. Extract MOP, Final Four history
5. Upload to S3

### Month 2: Modern NCAA D1 Stats (3 weeks, 10-12 hours)
1. Scrape player stats (2000-2025, 26 seasons)
2. Scrape team stats (2000-2025)
3. Scrape conference standings
4. Scrape coach records
5. **Optional:** Sample schedule/results (omit or sample due to size)
6. Upload to S3

### Month 3: Awards & Optional Data (2 weeks, 4-5 hours + optional)
1. Scrape college awards (Player of Year, All-America, conference)
2. **Optional:** Polls, leaders, additional tournaments
3. Upload to S3

**Total Time (Essential - Tiers 13A + 13B):** 22 hours over 8 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - NCAA Tournament: 87 men's + 44 women's = ~7,500 games
   - Player stats (2000-2025): ~80,000 player-seasons
   - Team stats (2000-2025): ~9,000 team-seasons
   - Awards: ~3,000 total

2. **Coverage Verification**
   - All NCAA Tournaments present (1939-2025, missing 2020)
   - Modern stats cover 2000-2025 (26 seasons)
   - All major awards documented

3. **Data Structure Validation**
   - JSON structure consistent
   - All expected fields present
   - Tournament brackets complete (all games, scores)

4. **Cross-Validation**
   - NCAA champions match known results
   - Player stats align with known college stars
   - Awards winners match historical records

---

## Success Criteria

### Tier 13A: NCAA Tournament Focus (10 hours)
- [ ] NCAA Tournament data collected (men's & women's, all years)
- [ ] MOP, Final Four history documented
- [ ] ~8,000 records
- [ ] Total time: 10 hours

### Tier 13B: Modern Stats (12 hours)
- [ ] NCAA D1 player stats (2000-2025)
- [ ] NCAA D1 team stats (2000-2025)
- [ ] Conference standings, coach records
- [ ] ~92,000 records
- [ ] Total time: 12 hours

### Tier 13C: Awards & Polls (5 hours) - Optional
- [ ] All college awards documented
- [ ] Polls history collected
- [ ] ~3,000 records
- [ ] Total time: 5 hours

### Tier 13D: Comprehensive (3 hours) - Optional
- [ ] NIT, women's basketball, miscellaneous
- [ ] ~7,000 records
- [ ] Total time: 3 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/college/
├── ncaa_tournament/
│   ├── 1939/
│   │   └── men/bracket.json
│   ├── .../
│   ├── 1982/
│   │   ├── men/bracket.json
│   │   └── women/bracket.json
│   ├── .../2025/
│   ├── mop/all_years.json
│   ├── final_four/all_years.json
│   └── upsets/all_years.json
├── player_stats/
│   ├── 2000/player_stats.json
│   └── .../2025/player_stats.json
├── team_stats/
│   ├── 2000/team_stats.json
│   └── .../2025/team_stats.json
├── conference_standings/
│   ├── 2000/standings.json
│   └── .../2025/standings.json
├── coaches/
│   ├── 2000/coach_records.json
│   └── .../2025/coach_records.json
├── awards/
│   ├── player_of_year/all_years.json
│   ├── all_america/all_years.json
│   └── conference_poy/all_years.json
├── polls/  # Optional
│   ├── ap_poll/2000-2025.json
│   └── coaches_poll/2000-2025.json
└── nit/  # Optional
    └── .../
```

---

## Database Integration

### Recommended Tables:

```sql
-- NCAA Tournament games
CREATE TABLE ncaa_tournament_games (
    tournament_year INTEGER,
    gender TEXT,  -- 'Men' or 'Women'
    round TEXT,  -- 'First Four', 'Round of 64', 'Round of 32', etc.
    game_date DATE,
    team1 TEXT,
    team1_seed INTEGER,
    team1_score INTEGER,
    team2 TEXT,
    team2_seed INTEGER,
    team2_score INTEGER,
    winner TEXT,
    PRIMARY KEY (tournament_year, gender, game_date, team1, team2)
);

-- NCAA player statistics
CREATE TABLE ncaa_player_stats (
    player_slug TEXT,
    season INTEGER,
    school TEXT,
    class_year TEXT,  -- 'Fr', 'So', 'Jr', 'Sr'
    games INTEGER,
    minutes REAL,
    points REAL,
    rebounds REAL,
    assists REAL,
    -- ... other stats
    PRIMARY KEY (player_slug, season)
);

-- NCAA team statistics
CREATE TABLE ncaa_team_stats (
    school TEXT,
    season INTEGER,
    conference TEXT,
    wins INTEGER,
    losses INTEGER,
    ppg REAL,
    opp_ppg REAL,
    -- ... other stats
    PRIMARY KEY (school, season)
);

-- College awards
CREATE TABLE ncaa_awards (
    season INTEGER,
    award_type TEXT,
    player_slug TEXT,
    school TEXT,
    PRIMARY KEY (season, award_type, player_slug)
);
```

---

## ML Feature Engineering

**College features:**
- NBA draft position prediction (college stats → NBA draft)
- College to NBA translation (which stats carry over?)
- March Madness upset prediction
- Tournament success factors

**Player development:**
- Freshman → senior improvement
- Conference strength adjustment
- Playing time progression
- NBA-readiness indicators

**Tournament analytics:**
- Bracket prediction models
- Seed performance expectations
- Conference tournament → NCAA performance
- Cinderella run probability

---

## Troubleshooting

**Common Issues:**

1. **Different domain (sports-reference.com/cbb/)**
   - Solution: Update scraper base URL
   - Handle different rate limits if applicable

2. **Massive dataset (schedule/results)**
   - Solution: Consider omitting or sampling
   - ~300K games for 2000-2025 alone

3. **2020 NCAA Tournament cancelled (COVID)**
   - Solution: Handle missing year
   - Document exception

4. **Women's basketball data less complete**
   - Solution: Focus on recent years (2000+)
   - Earlier years may have gaps

5. **Conference realignment (teams changing conferences)**
   - Solution: Track conference by season
   - Many conferences have changed over time

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Build NCAA → NBA draft models
3. Create March Madness prediction models
4. Analyze college-to-pro translation factors
5. **All 13 Tiers Complete!** Begin data integration and ML pipeline

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin (optional tier)
**Prerequisites:** None (pipeline context)
**Next Tier:** None (final tier in Basketball Reference collection)
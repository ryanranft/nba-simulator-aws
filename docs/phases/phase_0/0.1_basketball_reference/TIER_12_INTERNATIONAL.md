# Tier 12: International Basketball

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 12 of 13
**Priority:** OPTIONAL
**Status:** ⏸️ PENDING
**Data Types:** 40 total (collect 10-15 select ively)
**Estimated Time:** 10-30 hours (selective: 10 hours recommended)
**Estimated Records:** ~26,000 (selective) to ~50,000 (comprehensive)
**Cost Impact:** +$0.001/month S3 storage

---

## Overview

**Purpose:** Collect international basketball data from Olympics, FIBA competitions, and major professional leagues.

**Why This Tier Matters:**
- Global basketball analytics
- NBA draft prospects (international players)
- Cross-league comparisons
- Olympics/World Cup context
- EuroLeague scouting

**What This Adds:**
- Olympics basketball (1936-2024)
- FIBA World Cup (2010-2023)
- EuroLeague (2000-2025)
- Optional: National leagues (Spain, Italy, Greece, France, etc.)

**Prerequisites:** None (global context)

---

## Selective Collection Strategy

**RECOMMENDED: Tier 12A - Essential (10 hours, 26K records)**
- Olympics (all tournaments)
- FIBA World Cup (all tournaments)
- EuroLeague (all seasons 2000-2025)

**OPTIONAL: Tier 12B - Extended (+10 hours, +18K records)**
- Add Liga ACB (Spain)
- Add Lega Serie A (Italy)
- Add Greek Basket League

**OPTIONAL: Tier 12C - Comprehensive (+10 hours, +6K records)**
- Add all remaining leagues (France, China, Australia, etc.)

---

## Data Types

### PRIORITY 1: Olympics Basketball (5 types)

**Time:** 2-3 hours
**Records:** ~8,000
**Priority:** HIGH

#### 0.12.1: Men's Olympics Player Stats (1936-2024)

- **URL Pattern:** `/international/olympics/{year}-men.html`
- **Data:** Player statistics by tournament
- **Coverage:** 1936, 1948, 1952, ..., 2024 (every 4 years, 20 tournaments)
- **Records:** ~5,000
- **Value:** Elite international competition

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/international/olympics/{year}/men/player_stats.json`

---

#### 0.12.2: Women's Olympics Player Stats (1976-2024)

- **URL Pattern:** `/international/olympics/{year}-women.html`
- **Data:** Women's tournament statistics
- **Coverage:** 1976-2024 (13 tournaments)
- **Records:** ~3,000

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/international/olympics/{year}/women/player_stats.json`

---

#### 0.12.3-0.12.5: Olympics Team Stats, Medal Standings, Tournament Results

- **Data:** Team performance, medal counts, bracket results
- **Records:** ~500
- **Value:** Team-level analysis, medal tracking

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/international/olympics/{year}/team_stats.json`

---

### PRIORITY 2: FIBA World Cup (3 types)

**Time:** 1-2 hours
**Records:** ~2,200
**Priority:** MEDIUM-HIGH

#### 0.12.6: FIBA World Cup Player Stats (2010-2023)

- **URL Pattern:** `/international/fiba-world-cup/{year}.html`
- **Data:** World Cup player statistics
- **Coverage:** 2010, 2014, 2019, 2023 (4 tournaments)
- **Records:** ~2,000
- **Value:** International competition outside Olympics

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/international/fiba/{year}/player_stats.json`

---

#### 0.12.7-0.12.8: FIBA Team Stats & Tournament Results

- **Data:** Team statistics, bracket results, champions
- **Records:** ~200

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/international/fiba/{year}/team_stats.json`

---

### PRIORITY 3: EuroLeague (4 types)

**Time:** 4-5 hours
**Records:** ~16,500
**Priority:** HIGH

#### 0.12.9: EuroLeague Player Stats (2000-2025)

- **URL Pattern:** `/international/euroleague/{season}.html`
- **Data:** Top European club competition
- **Coverage:** 26 seasons (2000-2025)
- **Records:** ~15,000 player-seasons
- **Value:** European prospect scouting, international player analysis

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/international/euroleague/{season}/player_stats.json`

---

#### 0.12.10-0.12.12: EuroLeague Team Stats, Standings, Playoffs

- **Data:** Team statistics, standings, playoff results
- **Records:** ~1,500
- **Value:** Club-level competition tracking

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/international/euroleague/{season}/team_stats.json`

---

### OPTIONAL: Additional Leagues (28 types)

**Time:** 12-18 hours (if pursuing)
**Records:** ~24,000
**Priority:** LOW

#### 0.12.13-0.12.15: EuroCup (2002-2025)
- **Coverage:** 24 seasons
- **Records:** ~5,000
- **Value:** Second-tier European competition

#### 0.12.16-0.12.18: Liga ACB - Spain (1983-2025)
- **Coverage:** 43 seasons
- **Records:** ~10,000
- **Value:** Top Spanish league (strong international talent)

#### 0.12.19-0.12.21: Lega Serie A - Italy (1998-2025)
- **Coverage:** 28 seasons
- **Records:** ~5,000
- **Value:** Top Italian league

#### 0.12.22-0.12.24: Greek Basket League (2001-2025)
- **Coverage:** 25 seasons
- **Records:** ~3,000
- **Value:** Strong Greek basketball tradition

#### 0.12.25-0.12.27: LNB Pro A - France (2002-2025)
- **Coverage:** 24 seasons
- **Records:** ~5,000
- **Value:** Top French league

#### 0.12.28-0.12.30: CBA - China (2011-2025)
- **Coverage:** 15 seasons
- **Records:** ~3,000
- **Value:** Chinese Basketball Association

#### 0.12.31-0.12.33: NBL - Australia (2011-2025)
- **Coverage:** 15 seasons
- **Records:** ~3,000
- **Value:** Australian league (NBA talent pipeline)

#### 0.12.34-0.12.40: Other Leagues
- ABA First Division (Adriatic League)
- Israeli Basketball League
- Turkish Basketball League
- VTB United League (Russia/Eastern Europe)
- **Records:** ~2,000

---

## Implementation Plan

### Week 1: Olympics (2-3 hours)
1. Scrape Olympics index page
2. Iterate tournament years (1936, 1948, ..., 2024)
3. Extract player stats (men's and women's)
4. Extract team stats and medal standings
5. Upload to S3

### Week 2: FIBA World Cup (1-2 hours)
1. Scrape FIBA World Cup pages (2010, 2014, 2019, 2023)
2. Extract player and team stats
3. Upload to S3

### Week 3: EuroLeague (4-5 hours)
1. Scrape EuroLeague season pages (2000-2025, 26 seasons)
2. Extract player statistics
3. Extract team standings and playoff results
4. Upload to S3

**Total Time (Essential - Tier 12A):** 10 hours

### Optional Extensions:
- **Week 4-5:** Liga ACB, Lega Serie A, Greek League (+10 hours)
- **Week 6-7:** Additional leagues (+10 hours)

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - Olympics: ~20 men's tournaments + 13 women's = ~8,000 player records
   - FIBA: 4 tournaments × ~500 players = ~2,000
   - EuroLeague: 26 seasons × ~600 players = ~15,600

2. **Coverage Verification**
   - All Olympic years present (1936, 1948, ..., 2024)
   - All FIBA World Cups (2010, 2014, 2019, 2023)
   - All EuroLeague seasons (2000-2025)

3. **Data Structure Validation**
   - JSON structure consistent
   - All expected fields present
   - Player names, teams, statistics valid

4. **Cross-Validation**
   - Olympics medal counts match historical records
   - EuroLeague champions match known results
   - NBA players' international stats present

---

## Success Criteria

### Tier 12A: Essential (Recommended)
- [ ] Olympics data collected (men's & women's, 1936-2024)
- [ ] FIBA World Cup data collected (2010-2023)
- [ ] EuroLeague data collected (2000-2025)
- [ ] ~26,000 records total
- [ ] Total time: 10 hours

### Tier 12B: Extended (Optional)
- [ ] Liga ACB, Lega Serie A, Greek League added
- [ ] +18,000 records
- [ ] Total time: +10 hours

### Tier 12C: Comprehensive (Optional)
- [ ] All remaining leagues added
- [ ] +6,000 records
- [ ] Total time: +10 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/international/
├── olympics/
│   ├── 1936/
│   │   ├── men/player_stats.json
│   │   └── team_stats.json
│   ├── 1948/
│   └── .../2024/
│       ├── men/player_stats.json
│       └── women/player_stats.json
├── fiba/
│   ├── 2010/
│   │   ├── player_stats.json
│   │   └── team_stats.json
│   ├── 2014/
│   ├── 2019/
│   └── 2023/
├── euroleague/
│   ├── 2000/
│   │   ├── player_stats.json
│   │   └── team_stats.json
│   ├── 2001/
│   └── .../2025/
├── liga_acb/  # Optional
│   └── .../
├── lega_serie_a/  # Optional
│   └── .../
└── other_leagues/  # Optional
    └── .../
```

---

## Database Integration

### Recommended Tables:

```sql
-- Olympics player statistics
CREATE TABLE olympics_player_stats (
    tournament_year INTEGER,
    gender TEXT,  -- 'Men' or 'Women'
    player_slug TEXT,
    country TEXT,
    age INTEGER,
    games INTEGER,
    points REAL,
    rebounds REAL,
    assists REAL,
    -- ... other stats
    PRIMARY KEY (tournament_year, gender, player_slug)
);

-- FIBA World Cup statistics
CREATE TABLE fiba_player_stats (
    tournament_year INTEGER,
    player_slug TEXT,
    country TEXT,
    games INTEGER,
    points REAL,
    rebounds REAL,
    assists REAL,
    PRIMARY KEY (tournament_year, player_slug)
);

-- EuroLeague player statistics
CREATE TABLE euroleague_player_stats (
    season INTEGER,
    player_slug TEXT,
    team TEXT,
    games INTEGER,
    points REAL,
    rebounds REAL,
    assists REAL,
    PRIMARY KEY (season, player_slug)
);
```

---

## ML Feature Engineering

**International features:**
- NBA draft prospect identification (EuroLeague → NBA translation)
- Olympics performance → NBA success correlation
- International vs NBA stat comparison
- Cross-league talent evaluation

**Country-specific features:**
- National team performance (Olympics, FIBA)
- Country talent pipelines (Spain, France, Greece to NBA)
- International playing style differences

---

## Troubleshooting

**Common Issues:**

1. **Olympics held every 4 years (gaps)**
   - Solution: Handle missing years (e.g., 1940, 1944 WWII)
   - 2021 Olympics delayed to 2021 (COVID)

2. **EuroLeague format changes over time**
   - Solution: Handle multiple table formats
   - Early 2000s different structure than modern

3. **National league data may be incomplete**
   - Solution: Focus on well-documented leagues
   - Spain, Italy, Greece have best coverage

4. **Rate limiting**
   - Solution: 12s between requests (same as NBA)

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Create international player database
3. Build NBA draft prospect models (international → NBA)
4. Analyze Olympics/World Cup performance
5. Begin Tier 13 (College Basketball)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin (optional tier)
**Prerequisites:** None (global context)
**Next Tier:** Tier 13 (College Basketball)
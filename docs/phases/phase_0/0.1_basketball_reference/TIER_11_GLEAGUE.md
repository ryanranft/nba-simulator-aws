# Tier 11: G League Complete Collection

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 11 of 13
**Priority:** EXECUTE
**Status:** ⏸️ PENDING
**Data Types:** 10
**Estimated Time:** 8-10 hours
**Estimated Records:** ~30,000
**Cost Impact:** +$0.001/month S3 storage

---

## Overview

**Purpose:** Collect complete NBA G League (Development League) data for player development tracking and prospect analysis.

**Why This Tier Matters:**
- NBA player development pipeline
- Minor league analytics
- Call-up prediction (G League → NBA)
- Two-way contract analysis
- Prospect scouting

**What This Adds:**
- Complete G League history (2002-2025, 23 seasons)
- Season statistics, rosters, game logs
- Awards, leaders, daily scores
- Development tracking

**Prerequisites:** None (independent league)

---

## G League Context

**History:**
- Founded 2001 as "National Basketball Development League" (NBDL)
- Renamed "NBA Development League" (D-League) in 2005
- Renamed "NBA G League" in 2017 (G League = Gatorade partnership)
- 23 seasons of data (2002-2025)

**League Structure:**
- Started with ~8 teams (2002)
- Expanded to ~30 teams (2025)
- NBA affiliations (most NBA teams have G League affiliate)
- Two-way contracts introduced (2017): players can move between NBA/G League

**Player Development:**
- Young NBA prospects (drafted players assigned to G League)
- Undrafted players seeking NBA roster spots
- Veteran players staying in shape
- International players acclimating to US basketball

---

## Data Types

### 1. G League Season Standings (2002-2025)

**Coverage:** 23 seasons
**Records:** ~450 team-seasons
**Time:** 30 minutes
**Priority:** HIGH

#### Implementation:
- **URL Pattern:** `/gleague/years/NBA-D-League_{season}.html` (2002-2017)
- **URL Pattern:** `/gleague/years/NBA-G-League_{season}.html` (2018-2025)
- **Data:** Team records, playoff seeds, conference standings
- **Value:** League structure, playoff qualification

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/standings/{season}/standings.json`

---

### 2. G League Player Statistics (2002-2025)

**Coverage:** 23 seasons, ~15,000 player-seasons
**Records:** ~15,000
**Time:** 3 hours
**Priority:** CRITICAL

#### Implementation:
- **URL Pattern:** Same as standings page
- **Tables:** `per_game_stats`, `totals_stats`, `advanced_stats`
- **Data:** Complete G League player performance
- **Value:** Player development tracking

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/season_stats/{season}/player_stats.json`

---

### 3. G League Team Rosters (2002-2025)

**Coverage:** 23 seasons, ~450 team rosters
**Records:** ~450
**Time:** 1 hour
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** `/gleague/teams/{TEAM}/{season}.html`
- **Data:** Player rosters by team/season
- **Value:** Team composition, player movement

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/rosters/{season}/{team}/roster.json`

---

### 4. G League Game Logs (2002-2025)

**Coverage:** Top prospects, selective collection
**Records:** ~10,000 (selective) or ~100,000 (comprehensive)
**Time:** 2 hours (selective) or 8-10 hours (all players)
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** `/gleague/players/{X}/{player_slug}/gamelog/{season}`
- **Data:** Player game-by-game stats
- **Value:** Granular performance tracking

**Selective Collection Strategy:**
- Players who made NBA rosters (call-ups)
- Two-way contract players
- Leading scorers/performers
- NBA draft prospects

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/game_logs/{player_slug}/{season}/gamelog.json`

---

### 5. G League Daily Scores (2002-2025)

**Coverage:** ~5,000 games total
**Records:** ~5,000
**Time:** 30 minutes
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** `/gleague/years/NBA-D-League_{season}_games.html`
- **Data:** Game results by date
- **Value:** Complete game schedule and outcomes

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/daily_scores/{season}/games.json`

---

### 6. G League Awards (2002-2025)

**Coverage:** 23 seasons, ~500 award winners
**Records:** ~500
**Time:** 1 hour
**Priority:** MEDIUM-HIGH

#### Implementation:
- **URL Pattern:** G League awards pages
- **Awards:**
  - MVP
  - Rookie of the Year
  - Defensive Player of the Year
  - All-League Teams (First, Second)
  - All-Rookie Team
  - Coach of the Year

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/awards/{award_type}/all_years.json`

---

### 7. G League Season Leaders (2002-2025)

**Coverage:** 23 seasons
**Records:** ~2,000
**Time:** 30 minutes
**Priority:** LOW-MEDIUM

#### Implementation:
- **Data:** Top performers in each category per season
- **Categories:** PPG, RPG, APG, SPG, BPG, FG%, 3P%, FT%

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/leaders/{season}/season_leaders.json`

---

### 8. G League Career Leaders (All-time)

**Coverage:** Complete G League history
**Records:** ~500
**Time:** 30 minutes
**Priority:** LOW

#### Implementation:
- **Data:** Career statistical leaders
- **Categories:** Career points, rebounds, assists, games played

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/leaders/career/career_leaders.json`

---

### 9. G League Top Performers (Current season)

**Coverage:** Current season only
**Records:** Variable (~50-100)
**Time:** 15 minutes
**Priority:** LOW

#### Implementation:
- **Data:** Recent standout performances
- **Value:** Real-time prospect identification

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/leaders/current/top_performers.json`

---

### 10. G League Box Scores (2002-2025)

**Coverage:** ~5,000 games
**Records:** ~5,000
**Time:** 1 hour (if collecting detailed box scores)
**Priority:** LOW

#### Implementation:
- **URL Pattern:** Game-specific pages
- **Data:** Game-level statistics (team box scores)
- **Value:** Game-level analysis

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/gleague/box_scores/{season}/{game_id}/box_score.json`

---

## Implementation Plan

### Week 1: Core G League Data (4-5 hours)
1. Scrape season standings (2002-2025)
2. Scrape player statistics (all seasons)
3. Scrape team rosters
4. Scrape awards
5. Upload to S3

### Week 2: G League Game Logs & Additional Data (4-5 hours)
1. Scrape game logs (selective: call-ups, top performers)
2. Scrape season leaders
3. Scrape career leaders
4. Scrape daily scores
5. Upload to S3

**Total Time:** 8-10 hours over 2 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - Standings: 23 seasons × ~20 teams = ~450
   - Player stats: 23 seasons × ~650 players = ~15,000
   - Rosters: ~450 team rosters
   - Game logs: Variable (selective collection)
   - Awards: 23 seasons × ~20 awards = ~500

2. **Coverage Verification**
   - All 23 seasons present (2002-2025)
   - League rename handled (D-League → G League in 2017)
   - URL pattern switch handled (2017-18 season)

3. **Data Structure Validation**
   - JSON structure consistent
   - All expected fields present
   - No null/missing critical fields

4. **Cross-Validation**
   - Player stats match known G League performers
   - Call-ups documented (G League → NBA transitions)
   - Two-way contracts tracked (2017+)

---

## Success Criteria

- [ ] 10 data types collected
- [ ] 23 seasons covered (2002-2025)
- [ ] ~30,000 records total
- [ ] All files uploaded to S3
- [ ] Data quality checks passed
- [ ] Total time: 8-10 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/gleague/
├── standings/
│   ├── 2002/standings.json
│   └── .../2025/standings.json
├── season_stats/
│   ├── 2002/player_stats.json
│   └── .../2025/player_stats.json
├── rosters/
│   ├── 2002/
│   │   ├── {team}/roster.json
│   │   └── .../
│   └── .../2025/
├── game_logs/
│   ├── {player_slug}/
│   │   ├── 2002/gamelog.json
│   │   └── .../2025/gamelog.json
│   └── .../
├── awards/
│   ├── mvp/all_years.json
│   ├── roy/all_years.json
│   └── .../
├── leaders/
│   ├── 2002/season_leaders.json
│   ├── .../2025/season_leaders.json
│   ├── career/career_leaders.json
│   └── current/top_performers.json
├── daily_scores/
│   ├── 2002/games.json
│   └── .../2025/games.json
└── box_scores/
    ├── 2002/
    │   ├── {game_id}/box_score.json
    │   └── .../
    └── .../2025/
```

---

## Database Integration

### Recommended Tables:

```sql
-- G League season statistics
CREATE TABLE gleague_season_stats (
    player_slug TEXT,
    season INTEGER,
    team TEXT,
    age INTEGER,
    games INTEGER,
    minutes REAL,
    points REAL,
    rebounds REAL,
    assists REAL,
    -- ... all stats
    PRIMARY KEY (player_slug, season)
);

-- G League call-ups (G League → NBA)
CREATE TABLE gleague_call_ups (
    player_slug TEXT,
    gleague_season INTEGER,
    gleague_team TEXT,
    nba_team TEXT,
    call_up_date DATE,
    contract_type TEXT,  -- 'Two-way', '10-day', 'Standard'
    PRIMARY KEY (player_slug, call_up_date)
);

-- G League awards
CREATE TABLE gleague_awards (
    season INTEGER,
    award_type TEXT,
    player_slug TEXT,
    team TEXT,
    PRIMARY KEY (season, award_type)
);
```

---

## ML Feature Engineering

**G League features:**
- Call-up probability (G League stats → NBA roster)
- Development trajectory (improvement over seasons)
- Positional scarcity (G League vs NBA gaps)
- Two-way contract success rate

**Player pipeline:**
- College → G League performance drop/improvement
- G League → NBA translation (which stats carry over?)
- G League MVP → NBA success correlation

---

## Troubleshooting

**Common Issues:**

1. **URL pattern changed in 2017 (D-League → G League)**
   - Solution: Handle both URL formats
   - Pre-2018: `NBA-D-League_{season}`
   - 2018+: `NBA-G-League_{season}`

2. **Fewer teams in early years**
   - Solution: Document team count by season
   - 2002: ~8 teams
   - 2025: ~30 teams

3. **Two-way contracts started in 2017**
   - Solution: Track contract type (where available)
   - Two-way players split time between G League and NBA

4. **Rate limiting**
   - Solution: 12s between requests (same as NBA)

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Create call-up prediction model (G League → NBA)
3. Analyze two-way contract success rates
4. Integrate with NBA data for full player pipelines
5. Begin Tier 12 (International Basketball)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin
**Prerequisites:** None (independent league)
**Next Tier:** Tier 12 (International Basketball)
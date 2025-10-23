# Tier 3: NBA Historical Data

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 3 of 13
**Priority:** HIGH
**Status:** ⏸️ PENDING
**Data Types:** 3
**Estimated Time:** 10-15 hours
**Estimated Records:** ~75,000
**Cost Impact:** +$0.001/month S3 storage

---

## Overview

**Purpose:** Collect historical NBA data that provides context, awards, and league-wide records.

**Why This Tier Matters:**
- Awards and honors (MVP, All-NBA, etc.)
- Playoff performance history
- Statistical leaders and records
- Historical context for player comparisons

**What This Adds:**
- Complete awards history (1946-2025)
- Playoff statistics and series results
- Season leaders and records
- Hall of Fame and honors

**Prerequisites:** None (independent data collection)

---

## Data Types

### 1. Awards and Honors

**Coverage:** Complete NBA history (1946-2025)
**Records:** ~3,000 award winners
**Time:** 4-5 hours
**Priority:** HIGH

#### Implementation:
- **URL Pattern:** `/awards/awards_{season}.html` or `/awards/all_{award_type}.html`
- **Data:** All NBA awards, voting, and honors
- **Value:** Player recognition, career milestones, HOF prediction

**Awards to Collect:**
1. **MVP** (Most Valuable Player)
   - Winner + voting results (all candidates)
   - Shares distribution

2. **Rookie of the Year**
   - Winner + voting results

3. **Defensive Player of the Year**
   - Winner + voting (started 1982-83)

4. **Sixth Man of the Year**
   - Winner + voting (started 1982-83)

5. **Most Improved Player**
   - Winner + voting (started 1985-86)

6. **Coach of the Year**
   - Winner + voting

7. **All-NBA Teams**
   - First Team (5 players)
   - Second Team (5 players)
   - Third Team (5 players)

8. **All-Defensive Teams**
   - First Team (5 players, started 1968-69)
   - Second Team (5 players)

9. **All-Rookie Teams**
   - First Team (5 players)
   - Second Team (5 players)

10. **Finals MVP**
    - Winner (started 1968-69)

11. **All-Star Game MVP**
    - Winner

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/awards/{award_type}/all_years.json`

---

### 2. Playoff Statistics

**Coverage:** All NBA playoffs (1947-2025)
**Records:** ~50,000 player playoff performances
**Time:** 4-6 hours
**Priority:** HIGH

#### Implementation:
- **URL Pattern:** `/playoffs/NBA_{season}.html` or per-player playoff stats
- **Data:** Playoff statistics, series results, bracket progression
- **Value:** Postseason performance analysis, clutch players, championship context

**Data Categories:**

1. **Playoff Season Totals (Per Player)**
   - Games, minutes, points, rebounds, assists, etc.
   - Aggregate stats for entire playoff run
   - Advanced metrics (PER, WS, BPM in playoffs)

2. **Playoff Series Results**
   - Round (First Round, Conference Semis, Finals, etc.)
   - Teams involved
   - Series outcome (4-0, 4-1, etc.)
   - Home court advantage

3. **Playoff Bracket**
   - Tournament structure by season
   - Seeding
   - Upsets and series lengths

4. **Playoff Leaderboards**
   - Points, rebounds, assists leaders per playoff year
   - Career playoff leaders

**Why Playoff Data Matters:**
- Clutch performance quantification
- Championship context for player evaluation
- Postseason vs regular season comparison
- Legacy and HOF consideration

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/playoffs/{season}/playoff_stats.json`

---

### 3. Season Leaders and Records

**Coverage:** Complete NBA history (1946-2025)
**Records:** ~20,000 leader entries
**Time:** 2-4 hours
**Priority:** MEDIUM-HIGH

#### Implementation:
- **URL Pattern:** `/leaders/` or `/leaders/{stat_name}_season.html`
- **Data:** Top players by statistical category each season
- **Value:** Historical context, record tracking, milestone identification

**Leader Categories:**

1. **Per-Season Leaders (Top 10-20 per year):**
   - Points per game
   - Rebounds per game
   - Assists per game
   - Steals per game
   - Blocks per game
   - Field goal percentage
   - 3-point percentage
   - Free throw percentage
   - Minutes per game
   - Player Efficiency Rating (PER)
   - Win Shares
   - Box Plus/Minus

2. **Career Leaders (All-Time):**
   - Career points
   - Career rebounds
   - Career assists
   - Career steals
   - Career blocks
   - Career games played
   - Career minutes

3. **Single-Game Records:**
   - Most points in a game
   - Most rebounds in a game
   - Most assists in a game
   - Other single-game records

4. **Streaks and Milestones:**
   - Consecutive games with X points
   - Milestone achievements (10K, 20K, 30K points)

**S3 Path:**
- `s3://nba-sim-raw-data-lake/basketball_reference/nba/leaders/season/{season}/{stat}.json`
- `s3://nba-sim-raw-data-lake/basketball_reference/nba/leaders/career/all_time.json`

---

## Implementation Plan

### Week 1: Awards and Honors (4-5 hours)
1. Scrape all award pages (MVP, DPOY, ROY, etc.)
2. Extract winners and voting results
3. Parse All-NBA, All-Defensive, All-Rookie teams
4. Validate completeness (79 seasons)
5. Upload to S3

### Week 2: Playoff Statistics (4-6 hours)
1. Scrape playoff stats for each season
2. Extract series results and bracket structure
3. Parse player playoff performance
4. Cross-validate with regular season data
5. Upload to S3

### Week 3: Season Leaders (2-4 hours)
1. Scrape leader pages for each category
2. Extract top 10-20 per season per category
3. Scrape career leaders (all-time)
4. Extract single-game records
5. Upload to S3

**Total Time:** 10-15 hours over 3 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - Awards: 79 seasons × ~40 awards per season = ~3,160 entries
   - Playoffs: 79 playoffs × ~200 players per playoffs = ~15,800 entries
   - Leaders: 79 seasons × 12 categories × 20 leaders = ~18,960 entries

2. **Coverage Verification**
   - All 79 NBA seasons present (1947-2025)
   - All major awards present (MVP always, DPOY from 1982)
   - Playoff data for every season
   - Leader data for all statistical categories

3. **Data Structure Validation**
   - Award voting shares sum to 1.0
   - Playoff series wins/losses correct (4-0 through 4-3)
   - Leader rankings in correct order (descending by stat value)

4. **Cross-Validation**
   - MVP winners match season leaders in key stats
   - Playoff stats consistent with season totals
   - Leader values match player season totals

---

## Success Criteria

- [ ] Awards data collected for all 79 seasons (1947-2025)
- [ ] Playoff statistics collected for all 79 playoffs
- [ ] Season leaders collected for 12+ categories per season
- [ ] Career leaders collected for all major categories
- [ ] All data quality checks passed
- [ ] All files uploaded to S3
- [ ] Data structure documented
- [ ] Total time: 10-15 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/nba/
├── awards/
│   ├── mvp/all_years.json
│   ├── roy/all_years.json
│   ├── dpoy/all_years.json
│   ├── sixth_man/all_years.json
│   ├── mip/all_years.json
│   ├── all_nba/all_years.json
│   ├── all_defensive/all_years.json
│   ├── all_rookie/all_years.json
│   ├── finals_mvp/all_years.json
│   └── allstar_mvp/all_years.json
├── playoffs/
│   ├── 1947/playoff_stats.json
│   ├── 1948/playoff_stats.json
│   └── .../2025/playoff_stats.json
└── leaders/
    ├── season/
    │   ├── 1947/
    │   │   ├── ppg.json
    │   │   ├── rpg.json
    │   │   ├── apg.json
    │   │   └── .../
    │   └── .../2025/
    └── career/
        └── all_time.json
```

---

## Database Integration

### Recommended Tables:

```sql
-- Awards
CREATE TABLE nba_awards (
    season INTEGER,
    award_type TEXT,  -- 'MVP', 'DPOY', 'ROY', etc.
    rank INTEGER,  -- 1 for winner, 2-N for voting places
    player_slug TEXT,
    team TEXT,
    voting_share REAL,  -- % of total votes (1.0 for winner in some systems)
    PRIMARY KEY (season, award_type, rank)
);

-- Playoff statistics
CREATE TABLE nba_playoff_stats (
    player_slug TEXT,
    season INTEGER,
    team TEXT,
    games INTEGER,
    minutes INTEGER,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    -- ... all playoff stats
    PRIMARY KEY (player_slug, season)
);

-- Season leaders
CREATE TABLE nba_season_leaders (
    season INTEGER,
    stat_category TEXT,  -- 'ppg', 'rpg', 'apg', etc.
    rank INTEGER,  -- 1 to 20
    player_slug TEXT,
    team TEXT,
    stat_value REAL,
    PRIMARY KEY (season, stat_category, rank)
);

-- Career leaders
CREATE TABLE nba_career_leaders (
    stat_category TEXT,  -- 'points', 'rebounds', 'assists', etc.
    rank INTEGER,
    player_slug TEXT,
    stat_value INTEGER,
    PRIMARY KEY (stat_category, rank)
);
```

---

## ML Feature Engineering

**Award features:**
- Award count by player (total MVP, All-NBA selections)
- Peak performance years (MVP voting shares)
- HOF probability (award-based model)
- Career arc (age at awards)

**Playoff features:**
- Playoff performance vs regular season differential
- Clutch factor (playoff efficiency vs regular season)
- Championship context (Finals appearances, wins)
- Playoff moments (game-winning plays)

**Leader features:**
- League-leading seasons count
- Statistical dominance (top 10 finishes)
- Era-adjusted rankings
- Multi-category leadership (versatility)

---

## Troubleshooting

**Common Issues:**

1. **Award voting formats changed over time**
   - Solution: Handle multiple voting systems
   - Pre-2010: different formats, some no voting data

2. **Playoff stats missing for early years**
   - Solution: Document coverage gaps
   - Some playoff data starts later than 1947

3. **Leader pages may have different formats by era**
   - Solution: Handle HTML table variations
   - Validate scraper across multiple eras

4. **Career leaders update frequently**
   - Solution: Re-scrape after each season
   - Version control for historical snapshots

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Create award prediction models (MVP, ROY, DPOY)
3. Analyze playoff performance differentials
4. Generate historical context for current players
5. Begin Tier 4 (NBA Performance Data)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin
**Prerequisites:** None (independent tier)
**Next Tier:** Tier 4 (NBA Performance Data)
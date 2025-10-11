# Tier 4: NBA Performance Data

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 4 of 13
**Priority:** HIGH
**Status:** ⏸️ PENDING
**Data Types:** 4
**Estimated Time:** 15-20 hours
**Estimated Records:** ~250,000
**Cost Impact:** +$0.003/month S3 storage

---

## Overview

**Purpose:** Collect NBA performance data for streaks, advanced box scores, franchise history, and All-Star games.

**Why This Tier Matters:**
- Player and team streaks (performance trends)
- Advanced box score metrics (four factors)
- Complete franchise history
- All-Star game records and rosters

**What This Adds:**
- Streaks and game highs
- Advanced box scores (four factors)
- Franchise records and history
- All-Star game data (1951-2025)

**Prerequisites:** Tier 3 (Awards data for All-Star selection validation)

---

## Data Types

### 1. Streaks and Game Highs

**Coverage:** NBA history (1946-2025)
**Records:** ~100,000 streak records
**Time:** 5-7 hours
**Priority:** HIGH

#### Implementation:
- **URL Pattern:** `/friv/streaks.cgi` or player streak pages
- **Data:** Notable streaks, career highs, consistency metrics
- **Value:** Performance trend analysis, peak performance identification

**Streak Categories:**

1. **Scoring Streaks:**
   - Consecutive games with X+ points (10, 20, 30, 40, 50)
   - Longest scoring streak (any points)
   - Most consecutive double-digit scoring games

2. **Double-Doubles and Triple-Doubles:**
   - Consecutive double-doubles
   - Consecutive triple-doubles
   - Most double-doubles in a season
   - Most triple-doubles in a season

3. **Team Streaks:**
   - Longest winning streak
   - Longest losing streak
   - Win/loss streaks by season

4. **Game Highs (Career):**
   - Most points in a game
   - Most rebounds in a game
   - Most assists in a game
   - Most steals/blocks in a game

5. **Consistency Metrics:**
   - Games played streak (consecutive games)
   - Minutes played consistency
   - Shot attempt consistency

**Why Streaks Matter:**
- Identify peak performance periods
- Momentum analysis
- Reliability and durability metrics
- Historical significance

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/streaks/{player_slug}/career_streaks.json`

---

### 2. Advanced Box Scores (Four Factors)

**Coverage:** NBA games (1996-2025, where available)
**Records:** ~40,000 games
**Time:** 4-6 hours
**Priority:** MEDIUM-HIGH

#### Implementation:
- **URL Pattern:** `/boxscores/{game_id}.html` (advanced section)
- **Data:** Dean Oliver's Four Factors for each team per game
- **Value:** Game outcome prediction, team efficiency analysis

**Four Factors (Per Team, Per Game):**

1. **Shooting (eFG%)**
   - Effective Field Goal Percentage
   - Accounts for 3-pointers being worth more
   - Formula: (FGM + 0.5 × 3PM) / FGA

2. **Turnovers (TOV%)**
   - Turnover Percentage
   - Turnovers per 100 possessions
   - Formula: TOV / (FGA + 0.44 × FTA + TOV)

3. **Rebounding (ORB%)**
   - Offensive Rebound Percentage
   - % of available offensive rebounds captured
   - Formula: ORB / (ORB + Opp DRB)

4. **Free Throws (FT Rate)**
   - Free Throw Rate
   - Free throws made relative to field goal attempts
   - Formula: FTM / FGA

**Additional Advanced Metrics:**
- Pace (possessions per 48 minutes)
- Offensive Rating (points per 100 possessions)
- Defensive Rating (points allowed per 100 possessions)
- Net Rating (offensive - defensive rating)

**Why Four Factors Matter:**
- Game outcome strongly correlated with four factors
- Identify team strengths/weaknesses
- Simulation engine accuracy
- Win probability modeling

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/advanced_box/{season}/{game_id}/four_factors.json`

---

### 3. Franchise History and Records

**Coverage:** All NBA franchises (current and defunct)
**Records:** ~10,000 franchise-season records
**Time:** 3-4 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** `/teams/{team}/` or `/teams/{team}/history.html`
- **Data:** Complete franchise history, relocations, championships
- **Value:** Historical context, franchise comparisons, legacy analysis

**Franchise Data Categories:**

1. **Franchise Overview:**
   - Team name history (e.g., Seattle SuperSonics → OKC Thunder)
   - Years active
   - City/arena history
   - Championship years

2. **All-Time Franchise Records:**
   - Most wins in a season
   - Best winning percentage
   - Longest winning/losing streak
   - Playoff appearances
   - Championship count

3. **All-Time Franchise Leaders:**
   - Career points leader
   - Career rebounds leader
   - Career assists leader
   - Games played
   - Minutes played

4. **Season-by-Season Results:**
   - Win-loss record each season
   - Playoff results each season
   - Coach each season
   - Notable roster changes

5. **Defunct Franchises:**
   - Anderson Packers (1949-50)
   - Baltimore Bullets (1947-54)
   - Chicago Stags (1946-50)
   - And ~15 other defunct franchises

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/franchises/{team}/franchise_history.json`

---

### 4. All-Star Game Data

**Coverage:** All NBA All-Star Games (1951-2025)
**Records:** ~2,000 All-Star player performances
**Time:** 3-4 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** `/allstar/NBA_{season}.html`
- **Data:** All-Star rosters, box scores, voting, MVP
- **Value:** Elite player recognition, mid-season performance snapshot

**All-Star Data Categories:**

1. **Rosters:**
   - Eastern Conference roster (12-15 players)
   - Western Conference roster (12-15 players)
   - Starters vs Reserves
   - Injury replacements

2. **Voting Results:**
   - Fan voting totals (where available)
   - Coach selections (reserves)
   - Commissioner selections (injury replacements)

3. **Game Results:**
   - Final score
   - Box score (points, rebounds, assists per player)
   - Shooting percentages
   - MVP winner

4. **Historical All-Star Records:**
   - Most All-Star selections (career)
   - Most All-Star MVPs
   - Most points in All-Star game
   - Other All-Star records

**Why All-Star Data Matters:**
- Mid-season elite player identification
- Fan popularity and marketability
- Career milestone (All-Star selections)
- Peak performance showcase

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/all_star/{season}/allstar_game.json`

---

## Implementation Plan

### Week 1: Streaks and Game Highs (5-7 hours)
1. Scrape streak pages (scoring, doubles, team streaks)
2. Extract player career highs
3. Parse consistency metrics
4. Validate against known records
5. Upload to S3

### Week 2: Advanced Box Scores (4-6 hours)
1. Identify games with advanced box score data (1996+)
2. Scrape four factors for each game
3. Extract pace, ratings, advanced metrics
4. Cross-validate with basic box scores
5. Upload to S3

### Week 3: Franchise History (3-4 hours)
1. Scrape franchise pages for all 30 current teams
2. Scrape defunct franchise pages (~15 teams)
3. Extract franchise records, leaders, history
4. Document relocations and name changes
5. Upload to S3

### Week 4: All-Star Game Data (3-4 hours)
1. Scrape All-Star game pages (1951-2025)
2. Extract rosters, voting, box scores
3. Parse MVP winners
4. Cross-validate with awards data (Tier 3)
5. Upload to S3

**Total Time:** 15-20 hours over 4 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - Streaks: ~400 notable streaks per season × 79 seasons = ~31,600
   - Advanced box: ~1,230 games per season × 30 seasons = ~36,900
   - Franchises: 30 current + 15 defunct = 45 franchise histories
   - All-Star: 74 All-Star games (missing some early years, 2021)

2. **Coverage Verification**
   - All major streaks documented
   - Four factors available for 1996+ games
   - All franchises (current and defunct) present
   - All All-Star games present (missing years noted)

3. **Data Structure Validation**
   - Streak lengths match documented records
   - Four factors percentages within valid range (0-100%)
   - Franchise years match known history
   - All-Star rosters have correct number of players (12-15 per conference)

4. **Cross-Validation**
   - Career highs match game logs (Tier 1)
   - Four factors consistent with game outcomes
   - All-Star MVPs match award data (Tier 3)
   - Franchise leaders match player career totals

---

## Success Criteria

- [ ] Streaks data collected for notable players and teams
- [ ] Advanced box scores collected for 1996-2025 games
- [ ] Franchise history collected for all 45 franchises
- [ ] All-Star game data collected for 74 games (1951-2025)
- [ ] All data quality checks passed
- [ ] All files uploaded to S3
- [ ] Data structure documented
- [ ] Total time: 15-20 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/nba/
├── streaks/
│   ├── {player_slug}/career_streaks.json
│   └── teams/{team}/team_streaks.json
├── advanced_box/
│   ├── 1997/
│   │   ├── {game_id}/four_factors.json
│   │   └── .../
│   └── .../2025/
├── franchises/
│   ├── LAL/franchise_history.json
│   ├── BOS/franchise_history.json
│   └── .../
└── all_star/
    ├── 1951/allstar_game.json
    ├── 1952/allstar_game.json
    └── .../2025/allstar_game.json
```

---

## Database Integration

### Recommended Tables:

```sql
-- Streaks
CREATE TABLE nba_streaks (
    player_slug TEXT,
    streak_type TEXT,  -- 'scoring_30+', 'double_double', etc.
    streak_length INTEGER,
    start_date DATE,
    end_date DATE,
    season_start INTEGER,
    season_end INTEGER,
    PRIMARY KEY (player_slug, streak_type, start_date)
);

-- Advanced box scores
CREATE TABLE nba_advanced_box (
    game_id TEXT,
    team TEXT,
    efg_pct REAL,
    tov_pct REAL,
    orb_pct REAL,
    ft_rate REAL,
    pace REAL,
    off_rating REAL,
    def_rating REAL,
    net_rating REAL,
    PRIMARY KEY (game_id, team)
);

-- Franchise history
CREATE TABLE nba_franchises (
    team_code TEXT PRIMARY KEY,
    current_name TEXT,
    city TEXT,
    founded_year INTEGER,
    defunct_year INTEGER,  -- NULL if still active
    championships INTEGER,
    playoff_appearances INTEGER,
    -- ... franchise records
);

-- All-Star games
CREATE TABLE nba_allstar_games (
    season INTEGER PRIMARY KEY,
    game_date DATE,
    location TEXT,
    east_score INTEGER,
    west_score INTEGER,
    mvp_player TEXT,
    attendance INTEGER
);

CREATE TABLE nba_allstar_rosters (
    season INTEGER,
    player_slug TEXT,
    conference TEXT,  -- 'East' or 'West'
    starter BOOLEAN,
    replacement BOOLEAN,
    PRIMARY KEY (season, player_slug)
);
```

---

## ML Feature Engineering

**Streak features:**
- Current streak status (hot/cold)
- Historical peak streak length (capability)
- Consistency score (low variance in performance)
- Reliability (games played streak)

**Four factors features:**
- Team strength indicators (eFG%, TOV%, ORB%, FT Rate)
- Matchup-specific four factors
- Win probability (based on four factors)
- Pace-adjusted performance

**Franchise features:**
- Franchise success history (win%, championships)
- Home court advantage (historical)
- Playoff experience (franchise-level)

**All-Star features:**
- All-Star selection count (popularity, elite status)
- All-Star voting rank (fan appeal)
- All-Star MVP (peak performance)

---

## Troubleshooting

**Common Issues:**

1. **Streak data incomplete for early eras**
   - Solution: Focus on well-documented streaks (1980+)
   - Note coverage limitations

2. **Advanced box scores not available pre-1996**
   - Solution: Document coverage window
   - May require calculation from basic box scores

3. **Franchise relocations complicate data**
   - Solution: Maintain mapping (Seattle → OKC, etc.)
   - Use franchise ID, not city name

4. **All-Star games missing some years**
   - Solution: 1999 (lockout), 2021 (COVID) had no game
   - Document exceptions

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Calculate streak probabilities (ML models)
3. Implement four factors in simulation engine
4. Create franchise comparison dashboards
5. Begin Tier 5 (NBA Advanced Data)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin
**Prerequisites:** Tier 3 (for All-Star validation)
**Next Tier:** Tier 5 (NBA Advanced Data)
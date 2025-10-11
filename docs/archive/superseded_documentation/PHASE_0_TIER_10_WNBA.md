# Phase 0 - TIER 10: WNBA Complete Collection

**Phase:** 0 (Data Collection - WNBA)
**Sub-Phase:** 0.10 - Women's National Basketball Association (WNBA)
**Status:** ⏸️ PENDING
**Scope:** Complete WNBA data (16 data types)
**Coverage:** 1997-2025 (29 seasons)
**Estimated Time:** 15-20 hours
**Records:** ~100,000
**Cost Impact:** +$0.002/month S3 storage
**Priority:** EXECUTE (Option C selected)

---

## Overview

**Purpose:** Collect complete WNBA professional women's basketball data from league inception to present.

**Why WNBA Data Matters:**
- Complete women's professional basketball history
- Gender-comparative analysis (WNBA vs NBA)
- Multi-league panel data capability
- Women's sports analytics
- Draft pipeline (WNBA Draft from college)

**What This Adds:**
- 29 WNBA seasons (1997-2025)
- ~3,000 WNBA games
- ~1,500 WNBA players
- Complete awards and honors history
- Draft history (29 drafts)

---

## 🗂️ WNBA Data Types (16 types)

### Sub-Phase 0.10.1: WNBA Season Statistics ⏸️

**Coverage:** 1997-2025 (29 seasons)
**Records:** ~45,000 player-seasons
**Time:** 4-5 hours

#### 0.10.1a: WNBA Season Totals
- **URL:** `/wnba/years/WNBA_{season}.html`
- **Table ID:** `per_game_stats` or `totals_stats`
- **Data:** All counting stats (games, minutes, points, rebounds, assists, etc.)
- **Value:** Complete player performance by season

#### 0.10.1b: WNBA Per-Game Stats
- **URL:** Same page as season totals
- **Table ID:** `per_game_stats`
- **Data:** Per-game averages
- **Value:** Normalized comparison across players

#### 0.10.1c: WNBA Advanced Stats
- **URL:** `/wnba/years/WNBA_{season}_advanced.html`
- **Table ID:** `advanced_stats`
- **Data:** PER, WS, BPM, VORP, TS%, eFG%
- **Value:** Advanced performance metrics

**Implementation Steps:**
1. Create WNBA season iterator (1997-2025)
2. Scrape season totals table
3. Scrape per-game stats table (same page)
4. Scrape advanced stats table (separate page)
5. Upload to S3: `basketball_reference/wnba/season_stats/{season}/`

---

### Sub-Phase 0.10.2: WNBA Team Data ⏸️

**Coverage:** 1997-2025 (29 seasons, 16 current teams + defunct)
**Records:** ~15,000 team-season records
**Time:** 2-3 hours

#### 0.10.2a: WNBA Team Standings
- **URL:** `/wnba/years/WNBA_{season}.html`
- **Table ID:** `standings` or `team_stats`
- **Data:** Win-loss records, playoff seeds, conference standings
- **Value:** Team performance tracking

#### 0.10.2b: WNBA Team Statistics
- **URL:** Same page
- **Table ID:** `team_stats`
- **Data:** Team-level per-game stats
- **Value:** Team offensive/defensive metrics

**Implementation Steps:**
1. Extract team standings from season pages
2. Extract team statistics tables
3. Handle defunct teams (e.g., Charlotte Sting, Houston Comets)
4. Upload to S3: `basketball_reference/wnba/team_stats/{season}/`

---

### Sub-Phase 0.10.3: WNBA Player Game Logs ⏸️

**Coverage:** All WNBA players (career-long)
**Records:** ~500,000 individual games
**Time:** 3-4 hours (selective: top 200 players)
**Full collection:** 10-15 hours (all players)

#### Implementation:
- **URL:** `/wnba/players/{X}/{player_slug}/gamelog/{season}`
- **Table ID:** `pgl_basic`
- **Data:** Game-by-game stats for each player
- **Value:** Granular performance tracking

**Selective Collection Recommended:**
- WNBA All-Stars (all-time)
- MVP candidates
- Leading scorers
- Hall of Fame candidates

**Implementation Steps:**
1. Get list of WNBA players (scrape from season rosters or use player index)
2. Filter to top 200 players (by games played, All-Star selections)
3. Iterate players, scrape game logs per season
4. Rate limit: 12s between requests
5. Upload to S3: `basketball_reference/wnba/player_game_logs/{player_slug}/{season}/`

---

### Sub-Phase 0.10.4: WNBA All-Star Games ⏸️

**Coverage:** 1999-2025 (27 All-Star Games, none in 2004, 2010, 2016, 2020)
**Records:** ~600 (27 games × ~20-25 players per game)
**Time:** 1 hour

#### Implementation:
- **URL:** `/wnba/allstar/` or `/wnba/allstar/WNBA_YYYY.html`
- **Data:** Rosters, box scores, MVP, scores
- **Value:** Elite player recognition

**Implementation Steps:**
1. Scrape WNBA All-Star index page
2. Extract rosters for each year
3. Extract box scores
4. Extract MVP winners
5. Upload to S3: `basketball_reference/wnba/all_star/{year}/`

---

### Sub-Phase 0.10.5: WNBA Draft Data ⏸️

**Coverage:** 1997-2025 (29 drafts)
**Records:** ~1,200 draft picks (3 rounds × 12-14 teams × 29 years)
**Time:** 1 hour

#### 0.10.5a: WNBA Draft
- **URL:** `/wnba/draft/WNBA_{year}.html`
- **Table ID:** `draft`
- **Data:** Pick number, player name, college, team, career stats
- **Value:** Draft pipeline analysis

#### 0.10.5b: WNBA Supplemental Draft
- **URL:** `/wnba/draft/WNBA_supplemental_draft.html`
- **Data:** Special draft events
- **Value:** Complete draft history

**Implementation Steps:**
1. Scrape WNBA draft pages (1997-2025)
2. Scrape supplemental draft page
3. Extract pick details, colleges, teams
4. Upload to S3: `basketball_reference/wnba/draft/{year}/`

---

### Sub-Phase 0.10.6: WNBA Awards ⏸️

**Coverage:** 1997-2025 (29 seasons)
**Records:** ~500 award winners
**Time:** 2 hours

#### Awards to Collect:
1. **MVP** (Most Valuable Player)
2. **Rookie of the Year**
3. **Coach of the Year**
4. **Defensive Player of the Year**
5. **Most Improved Player**
6. **Sixth Woman of the Year**
7. **All-WNBA First Team** (5 players per year)
8. **All-WNBA Second Team** (5 players per year)
9. **All-Defensive Team** (varies by year)
10. **All-Rookie Team**

#### Implementation:
- **URL:** `/wnba/awards/` or specific award pages
- **Data:** Winners, voting, statistics
- **Value:** Elite recognition tracking

**Implementation Steps:**
1. Scrape WNBA awards index
2. Extract each award type
3. Compile voting data (if available)
4. Upload to S3: `basketball_reference/wnba/awards/{award_type}/`

---

### Sub-Phase 0.10.7: WNBA Playoff Statistics ⏸️

**Coverage:** 1997-2025 playoff seasons
**Records:** ~10,000 playoff games
**Time:** 2 hours

#### Implementation:
- **URL:** `/wnba/years/WNBA_{season}_playoffs.html`
- **Data:** Playoff stats, series results, finals
- **Value:** Postseason performance

**Implementation Steps:**
1. Scrape playoff pages for each season
2. Extract playoff brackets
3. Extract playoff series results
4. Extract Finals MVP
5. Upload to S3: `basketball_reference/wnba/playoffs/{season}/`

---

### Sub-Phase 0.10.8: WNBA Daily Scores ⏸️

**Coverage:** 1997-2025 (all games)
**Records:** ~3,000 games
**Time:** 1 hour

#### Implementation:
- **URL:** `/wnba/years/WNBA_{season}_games.html`
- **Data:** Game results by date
- **Value:** Complete game schedule and outcomes

**Implementation Steps:**
1. Scrape game schedules for each season
2. Extract scores, dates, locations
3. Upload to S3: `basketball_reference/wnba/daily_scores/{season}/`

---

### Sub-Phase 0.10.9: WNBA Leaderboards ⏸️

**Coverage:** Complete WNBA history
**Records:** ~1,000 leaders per category
**Time:** 1 hour

#### Types:
1. **Career Leaders** (all-time)
   - Points, rebounds, assists, steals, blocks
   - Games played, minutes, etc.

2. **Season Leaders** (by season)
   - Top 10 per category per season

#### Implementation:
- **URL:** `/wnba/leaders/` or leaderboard pages
- **Data:** Historical leaders
- **Value:** Historical context

**Implementation Steps:**
1. Scrape career leaderboards
2. Scrape season leaderboards
3. Upload to S3: `basketball_reference/wnba/leaderboards/`

---

### Sub-Phase 0.10.10: WNBA Rookie Records & Player Headshots ⏸️

**Coverage:** Complete WNBA history
**Records:** ~500 rookies, ~1,500 headshots
**Time:** 1 hour

#### 0.10.10a: Rookie Records
- **Data:** Best rookie performances
- **Value:** First-year benchmarks

#### 0.10.10b: Player Headshots
- **Data:** Player photos
- **Value:** Visualization, identification

**Implementation Steps:**
1. Scrape rookie records pages
2. Download player headshots (if desired)
3. Upload to S3: `basketball_reference/wnba/rookies/` and `wnba/headshots/`

---

## Implementation Timeline

**Week 1: Core WNBA Data** (8-10 hours)
- Days 1-2: Season statistics (totals, per-game, advanced)
- Day 3: Team data (standings, team stats)
- Days 4-5: Player game logs (selective: top 200 players)

**Week 2: WNBA Awards & Special Data** (7-10 hours)
- Day 6: All-Star Games
- Day 7: Draft data
- Day 8: Awards
- Day 9: Playoff statistics
- Day 10: Daily scores, leaderboards, rookies, headshots

**Total: 15-20 hours (2 weeks @ 7-10 hours/week)**

---

## Technical Implementation

### WNBA Scraper Configuration

```python
# Add to comprehensive scraper

WNBA_DATA_TYPES = {
    'season_totals': {
        'url_pattern': '/wnba/years/WNBA_{season}.html',
        'table_id': 'totals_stats',
        'min_year': 1997,
        'max_year': 2025,
        's3_prefix': 'basketball_reference/wnba/season_stats'
    },
    'per_game': {
        'url_pattern': '/wnba/years/WNBA_{season}.html',
        'table_id': 'per_game_stats',
        'min_year': 1997,
        'max_year': 2025,
        's3_prefix': 'basketball_reference/wnba/season_stats'
    },
    'advanced': {
        'url_pattern': '/wnba/years/WNBA_{season}_advanced.html',
        'table_id': 'advanced_stats',
        'min_year': 1997,
        'max_year': 2025,
        's3_prefix': 'basketball_reference/wnba/advanced_stats'
    },
    'team_standings': {
        'url_pattern': '/wnba/years/WNBA_{season}.html',
        'table_id': 'standings',
        'min_year': 1997,
        'max_year': 2025,
        's3_prefix': 'basketball_reference/wnba/team_stats'
    },
    'all_star': {
        'url_pattern': '/wnba/allstar/WNBA_{year}.html',
        'min_year': 1999,
        'max_year': 2025,
        'skip_years': [2004, 2010, 2016, 2020],  # No All-Star Games
        's3_prefix': 'basketball_reference/wnba/all_star'
    },
    'draft': {
        'url_pattern': '/wnba/draft/WNBA_{year}.html',
        'table_id': 'draft',
        'min_year': 1997,
        'max_year': 2025,
        's3_prefix': 'basketball_reference/wnba/draft'
    }
}
```

### Running WNBA Collection

```bash
# Run WNBA scraper (selective player game logs)
python scripts/etl/scrape_basketball_reference_comprehensive.py \
    --league WNBA \
    --start-season 1997 \
    --end-season 2025 \
    --data-types season_totals,per_game,advanced,team_standings,all_star,draft \
    --upload-to-s3

# Run full WNBA player game logs (all players, longer runtime)
python scripts/etl/scrape_basketball_reference_comprehensive.py \
    --league WNBA \
    --player-game-logs \
    --all-players \
    --upload-to-s3
```

---

## Data Quality Checks

**For each data type:**
1. **Record count validation**
   - Season stats: ~1,500 players per season (29 seasons = ~45,000)
   - Team stats: 12-14 teams per season (29 seasons = ~350)
   - Draft: ~36 picks per year (29 years = ~1,000)

2. **Coverage verification**
   - All 29 seasons present (1997-2025)
   - No missing years
   - Defunct teams included (Charlotte, Cleveland, Houston, Miami, etc.)

3. **Data structure validation**
   - JSON structure consistent
   - All expected fields present
   - No null/missing critical fields

---

## Success Criteria

**WNBA Collection Complete:**
- [ ] 16 data types collected
- [ ] ~100,000 records total
- [ ] 29 seasons covered (1997-2025)
- [ ] All files uploaded to S3
- [ ] Data quality checks passed
- [ ] Total time: 15-20 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/wnba/
├── season_stats/
│   ├── 1997/
│   │   ├── season_totals.json
│   │   ├── per_game.json
│   │   └── advanced.json
│   ├── 1998/
│   └── .../2025/
├── team_stats/
│   ├── 1997/team_standings.json
│   └── .../2025/
├── player_game_logs/
│   ├── [player_slug]/
│   │   ├── 1997/gamelog.json
│   │   └── .../
│   └── .../
├── all_star/
│   ├── 1999/all_star.json
│   └── .../2025/
├── draft/
│   ├── 1997/draft.json
│   └── .../2025/
├── awards/
│   └── all_years.json
├── playoffs/
│   ├── 1997/playoffs.json
│   └── .../2025/
├── daily_scores/
│   ├── 1997/games.json
│   └── .../2025/
├── leaderboards/
│   ├── career_leaders.json
│   └── season_leaders.json
└── rookies/
    └── rookie_records.json
```

---

## Integration with Existing System

### Database Tables

```sql
-- WNBA season stats
CREATE TABLE wnba_season_totals (
    season INTEGER,
    player_slug TEXT,
    team TEXT,
    age INTEGER,
    games INTEGER,
    minutes INTEGER,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    -- ... all stat columns
    PRIMARY KEY (season, player_slug)
);

-- WNBA team standings
CREATE TABLE wnba_team_standings (
    season INTEGER,
    team TEXT,
    wins INTEGER,
    losses INTEGER,
    win_pct REAL,
    playoff_seed INTEGER,
    -- ... other columns
    PRIMARY KEY (season, team)
);

-- Similar tables for draft, awards, playoffs, etc.
```

### ML Feature Engineering

**WNBA-specific features:**
- Per-game averages (PPG, RPG, APG)
- Advanced metrics (PER, WS, BPM)
- Career trajectory (rookie year, peak performance)
- Draft position effectiveness
- Award predictions

**Gender-comparative features:**
- WNBA vs NBA stat comparisons
- Relative dominance within league
- Cross-league pattern analysis

---

## Next Steps After Completion

1. **Load WNBA data to RDS PostgreSQL**
2. **Create unified WNBA views**
3. **Update ML feature engineering pipeline**
4. **Run WNBA-specific analytics**
5. **Cross-validate with other data sources (if available)**

---

## Troubleshooting

**Common Issues:**

1. **Missing years (2004, 2010, 2016, 2020 All-Star Games)**
   - Solution: Skip these years in All-Star scraper, no data exists

2. **Defunct teams**
   - Solution: Maintain historical team mapping

3. **Different table IDs than NBA**
   - Solution: Inspect HTML, verify table IDs on WNBA pages

4. **Rate limiting**
   - Solution: Same as NBA (12s between requests)

---

**Tier Owner:** Data Collection Team
**Last Updated:** October 11, 2025
**Status:** Ready for execution (Option C selected)
**Next Action:** Begin Sub-Phase 0.10.1 (WNBA Season Statistics)
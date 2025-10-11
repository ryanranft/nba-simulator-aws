# Tier 1: NBA High Value Data

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 1 of 13
**Priority:** IMMEDIATE
**Status:** ⏸️ PENDING
**Data Types:** 5
**Estimated Time:** 15-20 hours
**Estimated Records:** ~150,000
**Cost Impact:** +$0.002/month S3 storage

---

## Overview

**Purpose:** Collect the highest-value NBA data types with immediate ML and simulation utility.

**Why This Tier Matters:**
- Core data for player performance modeling
- Essential for game simulation engine
- Required for feature engineering pipeline
- High information density per record
- Immediate ROI for ML models

**What This Adds:**
- Player game logs (granular performance tracking)
- Play-by-play data (event-level detail)
- Shot chart data (spatial analysis)
- Player tracking data (advanced metrics)
- Lineup data (combination analysis)

---

## Data Types

### 1. Player Game Logs (Season & Career)

**Coverage:** All NBA players, all seasons (1946-2025)
**Records:** ~500,000 individual games
**Time:** 5-7 hours (selective: active + significant players)
**Priority:** CRITICAL

#### Implementation:
- **URL Pattern:** `/players/{X}/{player_slug}/gamelog/{season}`
- **Table ID:** `pgl_basic`
- **Data:** Game-by-game stats for each player
- **Value:** Granular performance tracking, streak analysis, matchup data

**Selective Collection Strategy:**
1. All active players (2024-2025 season)
2. Hall of Fame players
3. All-Stars (all-time)
4. Players with 400+ games played
5. Significant role players by usage

**Estimated:** ~300 players × 70 games avg = ~21,000 games per season

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/player_game_logs/{player_slug}/{season}/gamelog.json`

---

### 2. Play-by-Play Data

**Coverage:** NBA games with available play-by-play (2000-2025)
**Records:** ~500,000 games × 200 events = ~100M events
**Time:** 4-6 hours (selective: recent seasons + playoffs)
**Priority:** HIGH

#### Implementation:
- **URL Pattern:** `/boxscores/pbp/{game_id}.html`
- **Table ID:** `pbp`
- **Data:** Every event in every game (shots, fouls, substitutions, turnovers)
- **Value:** Event-level simulation, momentum modeling, situational analysis

**Selective Collection Strategy:**
1. All playoff games (2000-2025)
2. Regular season games (2015-2025)
3. Historical significant games (Finals, records, etc.)

**Estimated:** ~2,000 playoff games + ~12,000 regular season games = ~14,000 games

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/play_by_play/{season}/{game_id}/pbp.json`

---

### 3. Shot Chart Data

**Coverage:** NBA games with shot location data (2000-2025)
**Records:** ~25,000 games × 200 shots = ~5M shots
**Time:** 3-4 hours
**Priority:** HIGH

#### Implementation:
- **URL Pattern:** `/boxscores/shot-chart/{game_id}.html`
- **Data:** X/Y coordinates, shot type, make/miss, player, distance
- **Value:** Spatial analysis, shot selection, defensive positioning

**Coverage Strategy:**
1. All playoff games (2000-2025): ~2,000 games
2. Regular season sample (2015-2025): ~10,000 games
3. Special games (high-scoring, records): ~500 games

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/shot_charts/{season}/{game_id}/shots.json`

---

### 4. Player Tracking Data

**Coverage:** NBA seasons with tracking data (2013-2025)
**Records:** ~10,000 player-seasons
**Time:** 2-3 hours
**Priority:** MEDIUM-HIGH

#### Implementation:
- **URL Pattern:** `/leagues/NBA_{season}_tracking.html` or similar
- **Data:** Speed, distance, touches, passes, drives, etc.
- **Value:** Advanced performance metrics, effort metrics, usage patterns

**Data Categories:**
1. Driving stats (attempts, %, points)
2. Passing stats (assists per pass, secondary assists)
3. Touches (per game, time of possession)
4. Speed/distance traveled
5. Defensive matchup data

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/tracking/{season}/player_tracking.json`

---

### 5. Lineup Data (5-Man Combinations)

**Coverage:** NBA lineups with sufficient minutes (2007-2025)
**Records:** ~50,000 unique lineups
**Time:** 1-2 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** `/teams/{team}/{season}_lineups.html`
- **Table ID:** `lineups`
- **Data:** 5-man lineup performance (plus/minus, minutes, stats)
- **Value:** Combination analysis, coaching decisions, rotation optimization

**Metrics per Lineup:**
- Minutes played together
- Plus/minus
- Offensive/defensive rating
- Net rating
- Usage patterns

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/lineups/{season}/{team}/lineups.json`

---

## Implementation Plan

### Week 1: Player Game Logs (5-7 hours)
1. Identify target player list (~300 players)
2. Scrape game logs by player and season
3. Rate limit: 12s between requests
4. Validate data structure and completeness
5. Upload to S3

### Week 2: Play-by-Play Data (4-6 hours)
1. Identify target game list (~14,000 games)
2. Scrape play-by-play tables
3. Parse event sequences
4. Validate event chains
5. Upload to S3

### Week 3: Shot Charts & Tracking (5-7 hours)
1. Scrape shot chart data (12,500 games)
2. Scrape player tracking data (13 seasons)
3. Validate coordinates and tracking metrics
4. Upload to S3

### Week 4: Lineup Data (1-2 hours)
1. Scrape lineup tables for all teams
2. Filter lineups with meaningful minutes (>10 min)
3. Validate lineup combinations
4. Upload to S3

**Total Time:** 15-20 hours over 4 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - Player game logs: ~21,000 per recent season
   - Play-by-play: ~14,000 games × 200 events
   - Shot charts: ~12,500 games × 200 shots
   - Player tracking: ~450 players per season × 13 seasons
   - Lineups: ~30 teams × 15-20 lineups per team

2. **Coverage Verification**
   - All target players present in game logs
   - All target games present in play-by-play
   - Shot coordinates within valid court dimensions
   - Tracking metrics within reasonable ranges
   - Lineup minutes sum to team totals

3. **Data Structure Validation**
   - JSON structure consistent across records
   - All expected fields present
   - No null/missing critical fields (player, date, stats)
   - Valid data types (integers, floats, dates)

4. **Cross-Validation**
   - Game log totals match box score totals
   - Play-by-play scores match final scores
   - Shot chart makes/misses match box score FG
   - Lineup plus/minus totals match team results

---

## Success Criteria

- [ ] Player game logs collected for ~300 target players
- [ ] Play-by-play data collected for ~14,000 target games
- [ ] Shot chart data collected for ~12,500 games
- [ ] Player tracking data collected for 2013-2025 seasons
- [ ] Lineup data collected for 2007-2025 seasons
- [ ] All data quality checks passed
- [ ] All files uploaded to S3
- [ ] Data structure documented
- [ ] Total time: 15-20 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/nba/
├── player_game_logs/
│   ├── {player_slug}/
│   │   ├── 1997/gamelog.json
│   │   ├── 1998/gamelog.json
│   │   └── .../2025/gamelog.json
│   └── .../
├── play_by_play/
│   ├── 2000/
│   │   ├── {game_id}/pbp.json
│   │   └── .../
│   └── .../2025/
├── shot_charts/
│   ├── 2000/
│   │   ├── {game_id}/shots.json
│   │   └── .../
│   └── .../2025/
├── tracking/
│   ├── 2013/player_tracking.json
│   └── .../2025/player_tracking.json
└── lineups/
    ├── 2007/
    │   ├── {team}/lineups.json
    │   └── .../
    └── .../2025/
```

---

## Database Integration

### Recommended Tables:

```sql
-- Player game logs
CREATE TABLE nba_player_game_logs (
    player_slug TEXT,
    game_date DATE,
    season INTEGER,
    game_id TEXT,
    team TEXT,
    opponent TEXT,
    home_away TEXT,
    minutes INTEGER,
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    -- ... all box score stats
    plus_minus INTEGER,
    PRIMARY KEY (player_slug, game_id)
);

-- Play-by-play events
CREATE TABLE nba_play_by_play (
    game_id TEXT,
    event_num INTEGER,
    quarter INTEGER,
    time_remaining TEXT,
    score_home INTEGER,
    score_away INTEGER,
    event_type TEXT,
    player TEXT,
    description TEXT,
    PRIMARY KEY (game_id, event_num)
);

-- Shot chart data
CREATE TABLE nba_shot_chart (
    game_id TEXT,
    shot_id INTEGER,
    player TEXT,
    quarter INTEGER,
    time_remaining TEXT,
    x_coord REAL,
    y_coord REAL,
    distance_ft REAL,
    shot_type TEXT,
    make_miss BOOLEAN,
    PRIMARY KEY (game_id, shot_id)
);

-- Player tracking
CREATE TABLE nba_player_tracking (
    player_slug TEXT,
    season INTEGER,
    drives_per_game REAL,
    touches_per_game REAL,
    avg_speed REAL,
    distance_miles REAL,
    -- ... all tracking metrics
    PRIMARY KEY (player_slug, season)
);

-- Lineup data
CREATE TABLE nba_lineups (
    season INTEGER,
    team TEXT,
    lineup_id TEXT,  -- Hash of 5 player slugs
    player1 TEXT,
    player2 TEXT,
    player3 TEXT,
    player4 TEXT,
    player5 TEXT,
    minutes REAL,
    plus_minus REAL,
    off_rating REAL,
    def_rating REAL,
    net_rating REAL,
    PRIMARY KEY (season, team, lineup_id)
);
```

---

## ML Feature Engineering

**Player game logs features:**
- Rolling averages (5, 10, 20 games)
- Home/away splits
- Opponent-adjusted performance
- Recent trends (hot/cold streaks)
- Rest days impact

**Play-by-play features:**
- Momentum scores (scoring runs)
- Clutch performance (last 5 minutes)
- Lead changes per game
- Pace factors (possessions per minute)

**Shot chart features:**
- Shot location clusters (zones)
- Efficiency by distance
- Heat maps (make percentage by location)
- Defensive positioning impact

**Player tracking features:**
- Effort metrics (distance, speed)
- Usage patterns (touches, drives)
- Passing networks
- Off-ball movement

**Lineup features:**
- Plus/minus by lineup combination
- Offensive/defensive synergy
- Optimal lineup prediction
- Matchup-specific lineups

---

## Troubleshooting

**Common Issues:**

1. **Rate limiting (429 errors)**
   - Solution: Increase delay to 15s between requests
   - Use exponential backoff on retries

2. **Missing game logs for older players**
   - Solution: Some players lack complete data pre-1983
   - Document gaps, focus on complete records

3. **Play-by-play format variations**
   - Solution: Handle multiple table formats
   - Validate event types against known list

4. **Shot chart coordinate systems**
   - Solution: Normalize to standard court dimensions (94x50 ft)
   - Validate x, y ranges

5. **Lineup data incomplete**
   - Solution: Some teams/seasons lack lineup data
   - Document coverage gaps

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Create indexed views for common queries
3. Run data quality validation scripts
4. Generate summary statistics
5. Begin Tier 2 (NBA Strategic Data)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin
**Prerequisites:** None (Tier 1 is foundational)
**Next Tier:** Tier 2 (NBA Strategic Data)
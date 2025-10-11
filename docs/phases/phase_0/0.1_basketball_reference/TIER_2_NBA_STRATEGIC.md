# Tier 2: NBA Strategic Data

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 2 of 13
**Priority:** IMMEDIATE
**Status:** ⏸️ PENDING
**Data Types:** 4
**Estimated Time:** 20-25 hours
**Estimated Records:** ~200,000
**Cost Impact:** +$0.003/month S3 storage

---

## Overview

**Purpose:** Collect strategic NBA data types that provide deep tactical and performance insights.

**Why This Tier Matters:**
- Advanced shooting analytics (on/off court)
- Comprehensive shooting statistics
- Defensive positioning and matchup data
- Performance tracking across contexts

**What This Adds:**
- On/off court stats (player impact)
- Shooting splits (comprehensive shot analysis)
- Matchup data (head-to-head performance)
- Synergy stats (play type efficiency)

**Prerequisites:** Tier 1 (Player game logs for validation)

---

## Data Types

### 1. On/Off Court Statistics

**Coverage:** NBA seasons (2000-2025)
**Records:** ~15,000 player-seasons
**Time:** 5-7 hours
**Priority:** CRITICAL

#### Implementation:
- **URL Pattern:** `/teams/{team}/{season}/on-off/`
- **Data:** Team performance with player on/off court
- **Value:** Quantifies individual player impact on team performance

**Metrics Tracked:**
- Offensive rating (points per 100 possessions) on/off
- Defensive rating on/off
- Net rating differential
- Plus/minus per 48 minutes
- Pace differential

**Why This Matters:**
- True player impact measurement
- Context-adjusted performance
- Lineup optimization insights
- Coaching decision support

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/on_off/{season}/{team}/on_off.json`

---

### 2. Shooting Splits (Comprehensive)

**Coverage:** All NBA players with sufficient attempts (1996-2025)
**Records:** ~50,000 player-seasons
**Time:** 8-10 hours
**Priority:** HIGH

#### Implementation:
- **URL Pattern:** `/players/{X}/{player_slug}/splits/{season}`
- **Data:** Shooting percentages by various splits
- **Value:** Context-dependent shooting analysis

**Split Categories:**
1. **By Distance:**
   - 0-3 ft (at rim)
   - 3-10 ft (short mid-range)
   - 10-16 ft (mid-range)
   - 16+ ft to 3PT line
   - 3-pointers (by distance: corner, wing, top)

2. **By Game Context:**
   - Home vs Away
   - vs Conference/Division
   - vs Winning/Losing teams
   - By month
   - By day of week

3. **By Shot Clock:**
   - Early shot clock (24-18s)
   - Mid clock (17-7s)
   - Late clock (6-0s)

4. **By Score Differential:**
   - Ahead by 10+, 5-9, 1-4
   - Tied
   - Behind by 1-4, 5-9, 10+

5. **By Defender Distance:**
   - 0-2 ft (very tight)
   - 2-4 ft (tight)
   - 4-6 ft (open)
   - 6+ ft (wide open)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/shooting_splits/{player_slug}/{season}/splits.json`

---

### 3. Matchup Data (Head-to-Head)

**Coverage:** Player vs Player matchups (2007-2025)
**Records:** ~100,000 matchups
**Time:** 4-6 hours
**Priority:** MEDIUM-HIGH

#### Implementation:
- **URL Pattern:** `/friv/matchups.fcgi` or player matchup pages
- **Data:** Individual player performance vs specific defenders
- **Value:** Defensive impact quantification, matchup-specific tactics

**Matchup Metrics:**
- Offensive player: Points, FG%, minutes guarded
- Defensive player: Opponent FG%, points allowed
- Matchup frequency (possessions, minutes)
- Historical head-to-head trends

**Use Cases:**
- Defensive player value
- Matchup-specific game planning
- Historical rivalry analysis
- Playoff series preparation

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/matchups/{season}/matchup_data.json`

---

### 4. Synergy Play Type Stats

**Coverage:** NBA seasons with synergy data (2015-2025)
**Records:** ~5,000 player-seasons
**Time:** 3-4 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** May require separate API or scraping from synergy stats pages
- **Data:** Efficiency by play type (PnR, isolation, spot-up, etc.)
- **Value:** Play-type specific performance analysis

**Play Types Tracked:**
1. Pick and Roll Ball Handler
2. Pick and Roll Roll Man
3. Isolation
4. Post-Up
5. Spot-Up (catch-and-shoot)
6. Hand-Off
7. Cut
8. Off-Screen
9. Putback
10. Transition

**Metrics per Play Type:**
- Possessions/frequency
- Points per possession (PPP)
- FG%
- Turnover rate
- Foul drawing rate

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/synergy/{season}/play_types.json`

---

## Implementation Plan

### Week 1: On/Off Court Stats (5-7 hours)
1. Iterate through teams and seasons (2000-2025)
2. Scrape on/off tables for each team
3. Parse player-specific on/off differentials
4. Validate against known high-impact players
5. Upload to S3

### Week 2-3: Shooting Splits (8-10 hours)
1. Identify players with sufficient attempts (~400 players per season)
2. Scrape shooting split pages by player and season
3. Parse all split categories (distance, context, clock, differential, defender)
4. Validate shooting percentages sum correctly
5. Upload to S3

### Week 4: Matchup & Synergy Data (7-10 hours)
1. Scrape matchup data from matchup pages
2. Parse head-to-head statistics
3. Scrape synergy play type data (if available)
4. Parse play-type efficiency metrics
5. Upload to S3

**Total Time:** 20-25 hours over 4 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - On/off stats: ~30 teams × 15 players × 25 seasons = ~11,250 records
   - Shooting splits: ~400 players × 29 seasons = ~11,600 records
   - Matchups: ~100 matchups per season × 18 seasons = ~1,800 records
   - Synergy: ~450 players × 10 seasons = ~4,500 records

2. **Coverage Verification**
   - On/off data exists for all teams/seasons
   - Shooting splits complete for qualified players (200+ FGA)
   - Matchup data for frequent head-to-heads
   - Synergy data for primary ball-handlers

3. **Data Structure Validation**
   - On/off differentials within reasonable range (-20 to +20)
   - Shooting percentages between 0-100%
   - Matchup minutes sum to player total minutes
   - Synergy possessions sum to player total possessions

4. **Cross-Validation**
   - On/off net rating consistent with team performance
   - Shooting splits aggregate to season totals
   - Matchup data consistent with opponent stats
   - Synergy PPP aligns with player efficiency

---

## Success Criteria

- [ ] On/off court stats collected for 2000-2025 seasons
- [ ] Shooting splits collected for ~400 qualified players per season
- [ ] Matchup data collected for 2007-2025 seasons
- [ ] Synergy play type data collected for 2015-2025 seasons
- [ ] All data quality checks passed
- [ ] All files uploaded to S3
- [ ] Data structure documented
- [ ] Total time: 20-25 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/nba/
├── on_off/
│   ├── 2000/
│   │   ├── LAL/on_off.json
│   │   ├── BOS/on_off.json
│   │   └── .../
│   └── .../2025/
├── shooting_splits/
│   ├── {player_slug}/
│   │   ├── 1997/splits.json
│   │   └── .../2025/splits.json
│   └── .../
├── matchups/
│   ├── 2007/matchup_data.json
│   └── .../2025/matchup_data.json
└── synergy/
    ├── 2015/play_types.json
    └── .../2025/play_types.json
```

---

## Database Integration

### Recommended Tables:

```sql
-- On/off court stats
CREATE TABLE nba_on_off (
    player_slug TEXT,
    season INTEGER,
    team TEXT,
    minutes_on REAL,
    minutes_off REAL,
    off_rating_on REAL,
    off_rating_off REAL,
    def_rating_on REAL,
    def_rating_off REAL,
    net_rating_diff REAL,
    plus_minus_on REAL,
    plus_minus_off REAL,
    PRIMARY KEY (player_slug, season, team)
);

-- Shooting splits
CREATE TABLE nba_shooting_splits (
    player_slug TEXT,
    season INTEGER,
    split_type TEXT,  -- 'distance', 'context', 'clock', 'differential', 'defender'
    split_value TEXT,  -- e.g., '0-3ft', 'home', 'early_clock', 'ahead_10+'
    fga INTEGER,
    fgm INTEGER,
    fg_pct REAL,
    fg3a INTEGER,
    fg3m INTEGER,
    fg3_pct REAL,
    PRIMARY KEY (player_slug, season, split_type, split_value)
);

-- Matchup data
CREATE TABLE nba_matchups (
    season INTEGER,
    offensive_player TEXT,
    defensive_player TEXT,
    possessions INTEGER,
    minutes REAL,
    points INTEGER,
    fga INTEGER,
    fgm INTEGER,
    fg_pct REAL,
    PRIMARY KEY (season, offensive_player, defensive_player)
);

-- Synergy play types
CREATE TABLE nba_synergy (
    player_slug TEXT,
    season INTEGER,
    play_type TEXT,  -- 'PnR_ball_handler', 'isolation', etc.
    possessions INTEGER,
    points INTEGER,
    ppp REAL,  -- Points per possession
    fg_pct REAL,
    turnover_pct REAL,
    foul_rate REAL,
    PRIMARY KEY (player_slug, season, play_type)
);
```

---

## ML Feature Engineering

**On/off features:**
- Net rating impact (regression coefficient)
- Context-adjusted plus/minus
- Lineup-specific on/off differentials
- Impact trends over season

**Shooting split features:**
- Shot selection quality (high-efficiency zones)
- Versatility score (variance across splits)
- Clutch shooting (late clock, close games)
- Matchup-specific shooting (vs elite defenses)

**Matchup features:**
- Defensive impact score (opponent FG% reduction)
- Offensive consistency vs elite defenders
- Matchup win probability adjustments
- Historical head-to-head trends

**Synergy features:**
- Play-type efficiency (PPP by type)
- Offensive versatility (balanced usage across types)
- Skill specialization (elite in specific play types)
- Role prediction (primary/secondary/spot-up)

---

## Troubleshooting

**Common Issues:**

1. **On/off data missing for bench players**
   - Solution: Focus on players with 500+ minutes
   - Low-minute players have unreliable on/off stats

2. **Shooting splits incomplete for low-volume shooters**
   - Solution: Set minimum attempts threshold (50 FGA per split)
   - Document coverage limitations

3. **Matchup data sparse**
   - Solution: Focus on high-frequency matchups (10+ possessions)
   - Aggregate similar matchups if needed

4. **Synergy data may require separate source**
   - Solution: Check if Basketball Reference has synergy integration
   - May need to defer to separate data source (NBA.com)

5. **Rate limiting on player pages**
   - Solution: Increase delay to 15s for shooting splits
   - Implement checkpointing to resume interrupted scrapes

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Create indexed views for shooting analysis
3. Calculate derived metrics (versatility scores, impact ratings)
4. Integrate with Tier 1 data for comprehensive player profiles
5. Begin Tier 3 (NBA Historical Data)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin
**Prerequisites:** Tier 1 (for validation against game logs)
**Next Tier:** Tier 3 (NBA Historical Data)
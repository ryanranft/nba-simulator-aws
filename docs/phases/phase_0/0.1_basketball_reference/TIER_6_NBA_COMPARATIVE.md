# Tier 6: NBA Comparative Data

**Phase:** 0 (Data Collection - Basketball Reference)
**Tier:** 6 of 13
**Priority:** MEDIUM
**Status:** ⏸️ PENDING
**Data Types:** 4
**Estimated Time:** 12-15 hours
**Estimated Records:** ~100,000
**Cost Impact:** +$0.002/month S3 storage

---

## Overview

**Purpose:** Collect NBA comparative data for player similarity analysis, adjusted stats, player comparisons, and projection systems.

**Why This Tier Matters:**
- Player similarity scores (comparables)
- Era-adjusted statistics (cross-era comparison)
- Direct player comparisons
- Career trajectory projections

**What This Adds:**
- Similar players database
- Adjusted shooting statistics
- Advanced player comparisons
- Career projection models

**Prerequisites:** Tiers 1-3 (for comprehensive player profiles)

---

## Data Types

### 1. Similar Players (Comparables)

**Coverage:** All NBA players with sufficient career data
**Records:** ~5,000 players × ~10 comparables = ~50,000 comparisons
**Time:** 4-5 hours
**Priority:** MEDIUM-HIGH

#### Implementation:
- **URL Pattern:** `/players/{X}/{player_slug}.html` (similar players section)
- **Data:** Top 10 most similar players by career trajectory
- **Value:** Player archetype identification, career projection, historical context

**Similarity Methodology:**
- Basketball Reference uses a similarity score (0-100)
- Factors: Age, games played, stats, position, era
- Adjusted for different eras using era-specific coefficients

**What's Included:**
1. **Similar players list (top 10)**
   - Player name and slug
   - Similarity score (0-100, 100 = identical)
   - Age range of comparison
   - Era/years active

2. **Career trajectory matching**
   - Peak performance age
   - Career arc shape (early/late bloomer, sustained peak)
   - Longevity patterns

3. **Statistical archetype**
   - Playing style similarity (scorer, playmaker, defender)
   - Usage patterns
   - Efficiency profiles

**Why Similar Players Matter:**
- Career projection (how did similar players age?)
- Hall of Fame probability (comparables' achievements)
- Trade value estimation
- Historical context (modern player → historical comp)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/similar_players/{player_slug}/comparables.json`

---

### 2. Adjusted Shooting Stats (Era-Adjusted)

**Coverage:** All NBA players (1946-2025)
**Records:** ~5,000 players with adjusted stats
**Time:** 3-4 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** Player pages or `/leaders/` with adjusted metrics
- **Data:** Era-adjusted shooting percentages and efficiency
- **Value:** Cross-era player comparison, HOF evaluation

**Adjusted Metrics:**

1. **True Shooting % (TS%)**
   - Formula: PTS / (2 × (FGA + 0.44 × FTA))
   - Accounts for 3-pointers and free throws
   - Era-neutral efficiency metric

2. **Effective Field Goal % (eFG%)**
   - Formula: (FGM + 0.5 × 3PM) / FGA
   - Weights 3-pointers appropriately
   - Era-adjusted for 3-point line introduction (1979)

3. **Adjusted Shooting % (Relative to League)**
   - Player TS% / League average TS%
   - Values > 1.0 = above average
   - Accounts for era-specific pace and style

4. **Volume + Efficiency Composite**
   - Points per 75 possessions (pace-adjusted)
   - TS% relative to position
   - Usage rate adjusted

**Era Adjustments:**
- Pre-1979 (no 3-point line): Adjust for different shot distribution
- 1980s-1990s (low 3PT rate): Adjust for evolving 3-point usage
- 2000s (pace decline): Adjust for slower tempo
- 2010s-present (3PT revolution): Adjust for high 3-point volume

**Why Era-Adjusted Stats Matter:**
- Fair comparison across eras (Wilt vs LeBron)
- Historical context (how dominant in their era?)
- HOF evaluation (relative dominance, not raw totals)
- All-time rankings

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/adjusted_stats/{player_slug}/era_adjusted.json`

---

### 3. Advanced Player Comparisons

**Coverage:** Player vs Player statistical comparison tool
**Records:** ~10,000 unique player pair comparisons
**Time:** 3-4 hours
**Priority:** MEDIUM

#### Implementation:
- **URL Pattern:** `/friv/player_comparison.cgi` or comparison tool
- **Data:** Side-by-side statistical comparison
- **Value:** Direct player evaluation, trade analysis, roster decisions

**Comparison Categories:**

1. **Basic Stats (Per Game)**
   - Points, rebounds, assists, steals, blocks
   - Shooting percentages
   - Minutes, games played

2. **Advanced Stats**
   - PER, WS, BPM, VORP
   - TS%, eFG%, Usage Rate
   - Offensive/Defensive ratings

3. **Career Trajectories**
   - Stats by age (career arc comparison)
   - Peak seasons identification
   - Longevity and durability

4. **Achievements**
   - Championships, All-Star selections
   - All-NBA teams, awards
   - Playoff performance

5. **Context**
   - Era/years active
   - Teams played for
   - Position(s)

**Use Cases:**
- MVP debates (historical and current)
- Trade value assessment
- Roster construction (Player A vs Player B for team fit)
- Contract negotiations (comparable contracts)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/player_comparisons/{player1}_{player2}/comparison.json`

---

### 4. Projection Systems (CARMELO, etc.)

**Coverage:** Current NBA players with projections
**Records:** ~500 active players
**Time:** 2-3 hours
**Priority:** LOW-MEDIUM

#### Implementation:
- **URL Pattern:** Player pages (projections section) or separate projection pages
- **Data:** Career trajectory projections, peak age forecasts
- **Value:** Future performance prediction, contract valuation, trade analysis

**Projection Components:**

1. **CARMELO Projections (if available)**
   - Career Arc Regression Model Estimator with Local Optimization
   - Projects player stats for next 5-7 years
   - Accounts for aging curves, injury risk, playing time

2. **Peak Age Projections**
   - Projected age of peak performance (typically 27-29)
   - Probability of reaching various performance levels
   - Career longevity estimates

3. **Stat Projections by Season**
   - Next season projections (points, rebounds, assists)
   - 3-year projections
   - 5-year projections
   - Uncertainty ranges

4. **HOF Probability**
   - Current HOF probability (based on career to date)
   - Projected HOF probability (assuming career continues on trajectory)
   - Factors: awards, stats, team success

**Why Projections Matter:**
- Contract valuation (pay for future performance)
- Trade analysis (future value assessment)
- Draft strategy (college to NBA projections)
- Roster planning (team building)

**S3 Path:** `s3://nba-sim-raw-data-lake/basketball_reference/nba/projections/{player_slug}/career_projections.json`

---

## Implementation Plan

### Week 1: Similar Players (4-5 hours)
1. Scrape player pages for similar players section
2. Extract comparables for ~5,000 players
3. Parse similarity scores and player details
4. Validate against known archetypes
5. Upload to S3

### Week 2: Adjusted Stats & Comparisons (6-8 hours)
1. Scrape era-adjusted shooting stats
2. Calculate or extract TS%, eFG%, adjusted metrics
3. Scrape player comparison tool outputs
4. Generate key player pair comparisons (MVP candidates, trade targets)
5. Upload to S3

### Week 3: Projections (2-3 hours)
1. Scrape projection data from player pages
2. Extract CARMELO or other projection systems
3. Parse stat projections and HOF probabilities
4. Upload to S3

**Total Time:** 12-15 hours over 3 weeks

---

## Data Quality Checks

### For Each Data Type:

1. **Record Count Validation**
   - Similar players: ~5,000 players with 10 comparables each
   - Adjusted stats: ~5,000 players with era adjustments
   - Comparisons: ~10,000 unique player pairs
   - Projections: ~500 active players

2. **Coverage Verification**
   - All Hall of Famers have comparables
   - All current All-Stars have projections
   - Era-adjusted stats span all eras (1946-2025)

3. **Data Structure Validation**
   - Similarity scores between 0-100
   - Adjusted percentages reasonable (relative to league avg)
   - Projections include uncertainty ranges
   - HOF probabilities between 0-100%

4. **Cross-Validation**
   - Similar players have similar career stats
   - Era-adjusted rankings match historical perception
   - Projections align with aging curves
   - Comparisons are symmetric (A vs B = B vs A)

---

## Success Criteria

- [ ] Similar players collected for ~5,000 players
- [ ] Era-adjusted stats calculated for all players
- [ ] Player comparisons generated for key pairs
- [ ] Projections collected for ~500 active players
- [ ] All data quality checks passed
- [ ] All files uploaded to S3
- [ ] Data structure documented
- [ ] Total time: 12-15 hours

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/nba/
├── similar_players/
│   ├── {player_slug}/comparables.json
│   └── .../
├── adjusted_stats/
│   ├── {player_slug}/era_adjusted.json
│   └── .../
├── player_comparisons/
│   ├── {player1}_{player2}/comparison.json
│   └── .../
└── projections/
    ├── {player_slug}/career_projections.json
    └── .../
```

---

## Database Integration

### Recommended Tables:

```sql
-- Similar players
CREATE TABLE nba_similar_players (
    player_slug TEXT,
    similar_player_slug TEXT,
    rank INTEGER,  -- 1 to 10
    similarity_score REAL,  -- 0 to 100
    PRIMARY KEY (player_slug, rank)
);

-- Era-adjusted stats
CREATE TABLE nba_adjusted_stats (
    player_slug TEXT PRIMARY KEY,
    career_ts_pct REAL,
    career_efg_pct REAL,
    ts_vs_league_avg REAL,  -- Ratio
    efg_vs_league_avg REAL,
    pace_adjusted_ppg REAL,
    era_rank INTEGER  -- Rank within era
);

-- Player comparisons
CREATE TABLE nba_player_comparisons (
    player1_slug TEXT,
    player2_slug TEXT,
    comparison_category TEXT,  -- 'basic', 'advanced', 'achievements'
    player1_value REAL,
    player2_value REAL,
    advantage TEXT,  -- 'player1', 'player2', 'tie'
    PRIMARY KEY (player1_slug, player2_slug, comparison_category)
);

-- Projections
CREATE TABLE nba_projections (
    player_slug TEXT,
    projection_year INTEGER,
    projected_ppg REAL,
    projected_rpg REAL,
    projected_apg REAL,
    projected_per REAL,
    projected_vorp REAL,
    hof_probability REAL,
    PRIMARY KEY (player_slug, projection_year)
);
```

---

## ML Feature Engineering

**Similar player features:**
- Archetype classification (based on top comparables)
- Career trajectory prediction (age curve from comparables)
- Historical comp success (how did comparables perform?)
- Position flexibility (variation in comparables' positions)

**Era-adjusted features:**
- True historical ranking (era-adjusted leaderboards)
- Dominance score (relative to contemporaries)
- Cross-era value (Jordan vs LeBron using adjusted stats)

**Comparison features:**
- Head-to-head win probability
- Trade value differential
- Contract value estimation (based on comparisons)

**Projection features:**
- Future value estimation
- Breakout probability (exceeding projections)
- Bust risk (underperforming projections)
- Aging curve (individual vs typical)

---

## Troubleshooting

**Common Issues:**

1. **Similar players algorithm may change over time**
   - Solution: Version control similarity scores
   - Document Basketball Reference's methodology

2. **Era adjustments require careful methodology**
   - Solution: Use Basketball Reference's adjustments
   - Cross-validate with other sources (ESPN, 538)

3. **Projections available only for current players**
   - Solution: Historical projections not available
   - Focus on active roster

4. **Player comparison tool may have rate limits**
   - Solution: Cache common comparisons
   - Space out requests (15s delay)

---

## Next Steps After Completion

1. Load data to RDS PostgreSQL
2. Build player archetype classifier (ML model)
3. Create era-adjusted leaderboards
4. Generate trade value index (based on comparisons and projections)
5. Begin Tier 7 (NBA Situational Data)

---

**Tier Owner:** Data Collection Team
**Created:** October 11, 2025
**Last Updated:** October 11, 2025
**Status:** Ready to begin
**Prerequisites:** Tiers 1-3 (comprehensive player profiles)
**Next Tier:** Tier 7 (NBA Situational Data)
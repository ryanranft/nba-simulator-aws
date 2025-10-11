# Basketball Reference - Quick Reference Cards

**Purpose:** Fast orientation to each tier without reading full documentation
**Format:** Half-page summary per tier (~50-75 lines each)
**Use When:** Need quick reminder of tier scope, priorities, or prerequisites
**Last Updated:** October 11, 2025

---

## Tier 1: NBA High Value Data ⭐ IMMEDIATE

**Time:** 15-20 hours | **Records:** ~150K | **Priority:** CRITICAL

### What It Is:
Core NBA data with highest ML/simulation value - player performance tracking, event-level detail, spatial analysis.

### Data Types (5):
1. **Player Game Logs** - Game-by-game stats (~300 key players)
2. **Play-by-Play** - Every event in ~14K games (2000-2025)
3. **Shot Charts** - X/Y coordinates, ~5M shots (2000-2025)
4. **Player Tracking** - Speed, distance, touches (2013-2025)
5. **Lineup Data** - 5-man combinations (2007-2025)

### Why Start Here:
- Enables ML feature engineering immediately
- Required for game simulation engine
- High information density
- Direct ROI for modeling

### Prerequisites: None (foundational tier)

---

## Tier 2: NBA Strategic Data ⭐ IMMEDIATE

**Time:** 20-25 hours | **Records:** ~200K | **Priority:** HIGH

### What It Is:
Advanced tactical data - on/off impact, comprehensive shooting analysis, matchup performance, play-type efficiency.

### Data Types (4):
1. **On/Off Court Stats** - Player impact on team performance (2000-2025)
2. **Shooting Splits** - Performance by distance, context, clock, differential (~400 players)
3. **Matchup Data** - Head-to-head player performance (2007-2025)
4. **Synergy Stats** - Efficiency by play type (PnR, ISO, etc., 2015-2025)

### Why This Matters:
- Quantifies true player impact (beyond box score)
- Context-dependent performance analysis
- Advanced shooting analytics
- Defensive value measurement

### Prerequisites: Tier 1 (for validation)

---

## Tier 3: NBA Historical Data 🔥 HIGH

**Time:** 10-15 hours | **Records:** ~75K | **Priority:** HIGH

### What It Is:
Historical context - awards, playoff performance, season leaders, all-time records.

### Data Types (3):
1. **Awards & Honors** - MVP, All-NBA, DPOY, etc. (1947-2025)
2. **Playoff Statistics** - Postseason performance, series results (1947-2025)
3. **Season Leaders** - Top 10-20 per category per season + career leaders

### Why This Matters:
- Player recognition and HOF context
- Clutch performance (playoff analysis)
- Historical comparisons
- Award prediction models

### Prerequisites: None (independent tier)

---

## Tier 4: NBA Performance Data 🔥 HIGH

**Time:** 15-20 hours | **Records:** ~250K | **Priority:** MEDIUM-HIGH

### What It Is:
Performance trends and franchise context - streaks, advanced metrics, team history, All-Star games.

### Data Types (4):
1. **Streaks & Game Highs** - Scoring streaks, double-doubles, career highs
2. **Advanced Box Scores** - Four factors (eFG%, TOV%, ORB%, FT Rate) 1996+
3. **Franchise History** - Complete team records, relocations, all-time leaders
4. **All-Star Games** - Rosters, voting, box scores (1951-2025)

### Why This Matters:
- Performance trend identification
- Win prediction (four factors)
- Franchise comparisons
- Elite player recognition

### Prerequisites: Tier 3 (for All-Star validation)

---

## Tier 5: NBA Advanced Data 🔶 MEDIUM

**Time:** 8-12 hours | **Records:** ~50K | **Priority:** MEDIUM

### What It Is:
Next-level analytics - defensive tracking, hustle stats, detailed plus/minus.

### Data Types (3):
1. **Defensive Tracking** - Rim protection, perimeter defense (2013-2025)
2. **Hustle Stats** - Loose balls, charges, deflections (2016-2025)
3. **Plus/Minus Detailed** - Lineup-specific, situational impact (2000-2025)

### Why This Matters:
- Quantify defensive impact
- Intangible value (effort metrics)
- Lineup optimization
- Advanced player valuation

### Prerequisites: Tier 1 (for validation)

---

## Tier 6: NBA Comparative Data 🔶 MEDIUM

**Time:** 12-15 hours | **Records:** ~100K | **Priority:** MEDIUM

### What It Is:
Cross-player and cross-era comparisons - similar players, adjusted stats, projections.

### Data Types (4):
1. **Similar Players** - Top 10 comparables per player (~5K players)
2. **Era-Adjusted Stats** - Cross-era shooting adjustments (1946-2025)
3. **Player Comparisons** - Side-by-side statistical analysis (~10K pairs)
4. **Projections** - Career trajectory forecasts (~500 active players)

### Why This Matters:
- Player archetype identification
- Fair cross-era comparison (Wilt vs LeBron)
- Trade value estimation
- Future performance prediction

### Prerequisites: Tiers 1-3 (for comprehensive profiles)

---

## Tier 7: NBA Situational Data 🔶 MEDIUM

**Time:** 10-15 hours | **Records:** ~75K | **Priority:** MEDIUM

### What It Is:
Context-dependent performance - clutch, rest/fatigue, travel, schedule strength.

### Data Types (4):
1. **Clutch Statistics** - Last 5 min, close games (2000-2025)
2. **Rest & Fatigue** - Days off, back-to-backs, load analysis
3. **Travel & Timezone** - Distance, timezone changes, road trips
4. **Strength of Schedule** - Opponent quality, schedule difficulty

### Why This Matters:
- Late-game reliability (clutch performance)
- Load management optimization
- Home court advantage quantification
- Fair team evaluation (SOS-adjusted)

### Prerequisites: Tier 1 (for calculations)

---

## Tier 8: NBA Complete Data 🔵 LOW

**Time:** 8-12 hours | **Records:** ~50K | **Priority:** LOW

### What It Is:
Final completeness pieces - referees, transactions, miscellaneous records.

### Data Types (3):
1. **Referee Data** - Assignments, statistics, impact (1988-2025)
2. **Transactions** - Trades, signings, waivers (1946-2025)
3. **Miscellaneous Records** - NBA records, milestones, quirky stats

### Why This Matters:
- Home bias quantification (referee impact)
- Roster construction analysis
- Historical trivia and context
- Betting market insights

### Prerequisites: None (final completeness)

---

## Tier 9: Historical Leagues 🔵 LOW

**Time:** 5-8 hours | **Records:** ~15K | **Priority:** LOW

### What It Is:
Pre-NBA and rival leagues - ABA, BAA, early NBA data.

### Data Types (3):
1. **ABA Complete** - All 9 ABA seasons (1967-1976)
2. **BAA Complete** - All 3 BAA seasons (1946-1949, pre-NBA)
3. **Early NBA** - Pre-shot clock era (1949-1952)

### Why This Matters:
- Complete basketball history
- Dr. J, Moses Malone ABA careers
- 3-point line origin (ABA innovation)
- Game evolution context

### Prerequisites: None (historical context)

---

## Tier 10: WNBA Complete Collection ✅ EXECUTE

**Time:** 15-20 hours | **Records:** ~100K | **Priority:** SELECTED

### What It Is:
Complete Women's National Basketball Association data (1997-2025, 29 seasons).

### Data Types (16):
- Season stats, team data, player game logs
- All-Star games, draft, awards
- Playoffs, daily scores, leaderboards

### Why This Matters:
- Gender-comparative analysis
- Multi-league panel data
- Women's sports analytics
- Draft pipeline (WNBA Draft from college)

### Prerequisites: None (independent league)
### Link: See `PHASE_0_TIER_10_WNBA.md` (currently in parent directory)

---

## Tier 11: G League Complete ✅ EXECUTE

**Time:** 8-10 hours | **Records:** ~50K | **Priority:** SELECTED

### What It Is:
NBA G League (Development League) complete data (2002-2025).

### Data Types (10):
- Season stats, team standings
- Call-ups/assignments
- G League Showcase, draft

### Why This Matters:
- NBA player development pipeline
- Call-up prediction models
- Minor league analytics
- Two-way contract analysis

### Prerequisites: None (independent league)
### Link: Split from `PHASE_0_TIERS_11_12_13_MULTI_LEAGUE.md`

---

## Tier 12: International Basketball 🌍 OPTIONAL

**Time:** 10-30 hours (selective) | **Records:** ~100K | **Priority:** OPTIONAL

### What It Is:
FIBA, EuroLeague, Olympics, World Cup data.

### Data Types (40):
- EuroLeague, FIBA World Cup, Olympics
- National leagues (Spain, Italy, etc.)
- International player stats

### Why This Matters:
- Global basketball analytics
- NBA draft prospects (international players)
- Cross-league comparisons
- Olympics/World Cup context

### Prerequisites: None (global context)
### Link: Split from `PHASE_0_TIERS_11_12_13_MULTI_LEAGUE.md`

---

## Tier 13: College Basketball 🎓 OPTIONAL

**Time:** 30-40 hours (selective) | **Records:** ~200K | **Priority:** OPTIONAL

### What It Is:
NCAA Men's and Women's basketball data.

### Data Types (10):
- Season stats, tournament results
- March Madness brackets
- Conference tournaments

### Why This Matters:
- NBA/WNBA draft pipeline
- College to pro transition models
- Tournament prediction (March Madness)
- Recruiting analysis

### Prerequisites: None (pipeline context)
### Link: Split from `PHASE_0_TIERS_11_12_13_MULTI_LEAGUE.md`

---

## Navigation Guide

**Starting from PROGRESS.md:**
```
PROGRESS.md → "Tier 1: NBA High Value ⏸️"
   ↓
Tier Index (this directory's README.md) → Summary table with links
   ↓
Quick Reference Cards (this file) → Half-page overview
   ↓
TIER_1_NBA_HIGH_VALUE.md → Full implementation guide (400-600 lines)
```

**Context Budget:**
- This file: ~600 lines (3% context)
- Individual tier file: ~600 lines (3% context)
- **Total for quick check:** ~1,200 lines (6% context)

**When to Use:**
- ✅ Need quick reminder of tier scope
- ✅ Deciding which tier to work on next
- ✅ Understanding prerequisites
- ✅ Estimating time commitment
- ❌ Don't use for implementation (read full tier file)

---

## Priority Summary

**IMMEDIATE (Tiers 1-2):** Start here, 35-45 hours, foundational data
**HIGH (Tiers 3-4):** Next priority, 25-35 hours, historical context
**MEDIUM (Tiers 5-7):** Advanced analytics, 30-42 hours
**LOW (Tiers 8-9):** Completeness, 13-20 hours
**EXECUTE (Tiers 10-11):** Multi-league, 23-30 hours
**OPTIONAL (Tiers 12-13):** Global/college, 40-70 hours

**Total:** 140-197 hours for Tiers 1-11, +40-70 hours for optional tiers

---

**Quick Reference Owner:** Documentation Team
**Last Updated:** October 11, 2025
**Version:** 1.0
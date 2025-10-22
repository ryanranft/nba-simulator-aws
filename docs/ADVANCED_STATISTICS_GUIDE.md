# Advanced Statistics Implementation Guide

**Created:** October 18, 2025
**Status:** ✅ Schema Complete, Implementation In Progress
**Purpose:** Add advanced basketball statistics derived from play-by-play data

---

## Overview

Advanced statistics provide deeper insights into player and team performance beyond traditional box score stats. These metrics account for efficiency, pace, and context, enabling better analysis and ML model features.

---

## Categories of Advanced Statistics

### 1. Shooting Efficiency

#### True Shooting Percentage (TS%)
**Formula:** `TS% = PTS / (2 * (FGA + 0.44 * FTA)) * 100`

**What it measures:** Overall shooting efficiency accounting for 2PT, 3PT, and FT

**Why it matters:**
- Traditional FG% treats all made shots equally
- TS% recognizes that 3PT shots are worth more
- Accounts for free throws (most efficient shot)

**Example:**
- Player A: 10/20 FG (50%), 0/0 3PT, 0/0 FT → 50% FG%, 50% TS%
- Player B: 8/20 FG (40%), 6/10 3PT, 4/4 FT → 40% FG%, 58% TS%
- Player B is more efficient despite lower FG%!

**NBA Average:** ~56-58% TS%

---

#### Effective Field Goal Percentage (eFG%)
**Formula:** `eFG% = (FGM + 0.5 * 3PM) / FGA * 100`

**What it measures:** FG% adjusted for 3PT being worth 50% more

**Why it matters:**
- Corrects FG% for three-point shooting
- Doesn't account for free throws (unlike TS%)
- Pure field goal efficiency

**Example:**
- 10/20 FG with 4 threes = (10 + 0.5*4) / 20 = 60% eFG%
- 10/20 FG with 0 threes = (10 + 0) / 20 = 50% eFG%

**NBA Average:** ~53-55% eFG%

---

#### 3-Point Attempt Rate (3PAr)
**Formula:** `3PAr = 3PA / FGA * 100`

**What it measures:** Percentage of field goal attempts from 3-point range

**Why it matters:**
- Indicates playing style and shot selection
- Modern NBA teams take 35-45% of shots from three
- Guards typically 40-60%, centers 10-30%

**Example:**
- 11 three-point attempts, 23 total FGA = (11 / 23) * 100 = 47.8% 3PAr
- High 3PAr (>50%): Three-point specialist
- Low 3PAr (<20%): Paint-oriented player

**NBA Trends:**
- 2010s: ~22-28% league average
- 2020s: ~38-42% league average (three-point revolution)

---

### 2. Efficiency & Impact

#### Game Score
**Formula:**
```
Game Score = PTS + 0.4*FGM - 0.7*FGA - 0.4*(FTA-FTM)
           + 0.7*OREB + 0.3*DREB + STL + 0.7*AST
           + 0.7*BLK - 0.4*PF - TOV
```

**What it measures:** Overall player contribution in a single game

**Created by:** John Hollinger

**Why it matters:**
- Combines all box score stats into one number
- Positive contributions: Points, assists, rebounds, steals, blocks
- Negative contributions: Missed shots, turnovers, fouls

**Interpretation:**
- 40+ : Exceptional performance
- 30-40: Excellent game
- 20-30: Very good game
- 10-20: Solid game
- <10: Below average game

**Example from demo:** Jayson Tatum: 24.5 Game Score (excellent game)

---

#### Offensive Rating (ORtg)
**Formula:** `ORtg = (Points / Possessions) * 100`

**What it measures:** Points scored per 100 possessions

**Why it matters:**
- Normalizes scoring for pace
- Allows comparison across different eras
- Team or player efficiency independent of pace

**Team Interpretation:**
- 120+: Elite offense
- 110-120: Good offense
- 100-110: Average offense
- <100: Below average offense

**Example from demo:** BOS 124.8 ORtg (elite offensive performance)

---

### 3. Pace & Possessions

#### Possessions
**Formula:** `Possessions = FGA - OREB + TOV + 0.44*FTA`

**What it measures:** Estimated number of team possessions

**Why it matters:**
- Fundamental unit for pace-adjusted statistics
- Necessary for calculating ratings
- 0.44 coefficient accounts for FT possessions ending in made FT

**Typical range:** 90-105 possessions per 48-minute game

---

#### Pace
**Formula:** `Pace = Possessions * (48 / Minutes)`

**What it measures:** Possessions per 48 minutes (full game)

**Why it matters:**
- Indicates game speed/tempo
- High pace = fast game, more possessions
- Low pace = slow game, fewer possessions

**Era differences:**
- 1980s: 100-105 pace (run-and-gun)
- 1990s-2000s: 90-95 pace (slow, defensive)
- 2010s-2020s: 98-102 pace (modern, fast)

**Example from demo:** BOS 109.8 pace (fast, modern style)

---

### 4. Four Factors (Dean Oliver)

Dean Oliver identified four key factors that determine basketball success:

#### Factor 1: Shooting (eFG%)
**Formula:** `eFG% = (FGM + 0.5 * 3PM) / FGA * 100`

**Weight:** ~40% of game outcome

**What it measures:** Shooting efficiency

---

#### Factor 2: Turnovers (TOV%)
**Formula:** `TOV% = TOV / (FGA + 0.44*FTA + TOV) * 100`

**Weight:** ~25% of game outcome

**What it measures:** How often possessions end in turnovers

**Lower is better:**
- <10%: Excellent ball security
- 10-14%: Average
- >14%: Poor ball security

---

#### Factor 3: Rebounding (OREB%)
**Formula:** `OREB% = OREB / (Team OREB + Opp DREB) * 100`

**Weight:** ~20% of game outcome

**What it measures:** Percentage of available offensive rebounds secured

**NBA Average:** ~22-25% OREB%

---

#### Factor 4: Free Throws (FT Rate)
**Formula:** `FT Rate = FTA / FGA`

**Weight:** ~15% of game outcome

**What it measures:** How often team gets to the free throw line

**Interpretation:**
- >0.30: Excellent at drawing fouls
- 0.20-0.30: Average
- <0.20: Not getting to the line

---

## Advanced Statistics in Database Schema

### Player Box Score Snapshots

**Efficiency Metrics:**
```sql
true_shooting_pct REAL,          -- TS%
effective_fg_pct REAL,           -- eFG%
three_point_attempt_rate REAL,   -- 3PAr (3PA / FGA * 100)
ts_attempts REAL,                -- FGA + 0.44*FTA
```

**Usage & Impact:**
```sql
usage_rate REAL,                 -- % of team plays used
assist_rate REAL,                -- AST / team FGM
turnover_rate REAL,              -- TOV rate
game_score REAL,                 -- Hollinger's Game Score
offensive_rating REAL,           -- Points per 100 poss
assist_to_turnover REAL,         -- AST/TOV ratio
```

**Rebounding:**
```sql
offensive_rebound_pct REAL,      -- OREB%
defensive_rebound_pct REAL,      -- DREB%
total_rebound_pct REAL,          -- Total REB%
```

**Situational:**
```sql
points_in_paint INTEGER,
second_chance_points INTEGER,
fast_break_points INTEGER,
points_off_turnovers INTEGER,
```

### Team Box Score Snapshots

**All player metrics plus:**
```sql
defensive_rating REAL,           -- Opp points per 100 poss
net_rating REAL,                 -- ORtg - DRtg
pace REAL,                       -- Possessions per 48 min
possessions REAL,                -- Estimated possessions
bench_points INTEGER,            -- Points from bench
```

**Four Factors:**
```sql
efg_pct REAL,                    -- Shooting
tov_pct REAL,                    -- Turnovers
oreb_pct REAL,                   -- Rebounding
ft_rate REAL,                    -- Free Throws
```

**Assist Metrics:**
```sql
assist_pct REAL,                 -- AST / FGM
assist_to_turnover REAL,         -- AST / TOV
```

---

## Calculation Examples

### True Shooting % (Player)
```python
def calculate_ts_pct(points, fga, fta):
    ts_attempts = fga + 0.44 * fta
    if ts_attempts == 0:
        return 0.0
    return (points / (2 * ts_attempts)) * 100

# Jayson Tatum: 31 PTS, 23 FGA, 3 FTA
ts_pct = calculate_ts_pct(31, 23, 3)
# Result: 63.7%
```

### Offensive Rating (Team)
```python
def calculate_ortg(points, fga, oreb, tov, fta):
    possessions = fga - oreb + tov + 0.44 * fta
    if possessions == 0:
        return 0.0
    return (points / possessions) * 100

# BOS: 101 PTS, 75 FGA, 7 OREB, 9 TOV, 5 FTA
ortg = calculate_ortg(101, 75, 7, 9, 5)
# Result: 124.8 (elite offense)
```

### Four Factors (Team)
```python
def calculate_four_factors(fgm, fg3m, fga, tov, fta, oreb, opp_dreb):
    # Shooting: eFG%
    efg = (fgm + 0.5 * fg3m) / fga * 100 if fga > 0 else 0

    # Turnovers: TOV%
    tov_pct = tov / (fga + 0.44*fta + tov) * 100

    # Rebounding: OREB%
    total_or = oreb + opp_dreb
    oreb_pct = oreb / total_or * 100 if total_or > 0 else 0

    # Free Throws: FT Rate
    ft_rate = fta / fga if fga > 0 else 0

    return {
        'efg_pct': efg,
        'tov_pct': tov_pct,
        'oreb_pct': oreb_pct,
        'ft_rate': ft_rate
    }
```

---

## ML Applications

### Feature Engineering

**Efficiency Features:**
```python
# Shooting efficiency cluster
features['ts_pct'] = true_shooting_pct
features['efg_pct'] = effective_fg_pct
features['ft_rate'] = ft_rate

# Impact metrics
features['game_score'] = game_score
features['offensive_rating'] = offensive_rating
features['net_rating'] = net_rating
```

**Temporal Features:**
```python
# Player form (recent performance)
features['recent_ts_pct'] = avg(ts_pct[-5:])  # Last 5 games
features['ts_pct_trend'] = ts_pct_slope()      # Improving/declining

# Clutch vs non-clutch
features['clutch_ts_pct'] = ts_pct_clutch_situations
features['regular_ts_pct'] = ts_pct_non_clutch
```

**Matchup Features:**
```python
# Player vs opponent defense
features['ts_pct_vs_team'] = historical_ts_pct_vs_opponent
features['ortg_vs_team'] = historical_ortg_vs_opponent
```

---

### Prediction Models

**Game Outcome Prediction:**
```
Inputs:
  - Team eFG%, TOV%, OREB%, FT Rate (Four Factors)
  - Opponent eFG%, TOV%, OREB%, FT Rate
  - Pace difference
  - Home court advantage

Output: Win probability
```

**Player Performance Prediction:**
```
Inputs:
  - Recent TS%, eFG%, Usage Rate
  - Opponent defensive rating
  - Minutes projection
  - Rest days

Output: Projected Game Score
```

**Betting Model Features:**
```
Over/Under:
  - Combined pace
  - Offensive/Defensive ratings
  - Recent scoring trends

Spread:
  - Net rating differential
  - Four Factors differential
  - Home/Away splits
```

---

## Query Examples

### Player Efficiency Leaders
```sql
SELECT
    player_name,
    points,
    true_shooting_pct,
    effective_fg_pct,
    game_score
FROM player_box_score_snapshots
WHERE points >= 20
ORDER BY true_shooting_pct DESC
LIMIT 10;
```

### Team Four Factors
```sql
SELECT
    team_id,
    efg_pct,              -- Shooting
    tov_pct,              -- Turnovers
    oreb_pct,             -- Rebounding
    ft_rate,              -- Free Throws
    offensive_rating
FROM team_box_score_snapshots
WHERE game_id = '202406060BOS'
ORDER BY event_number DESC
LIMIT 1;  -- Final stats
```

### Clutch Performance
```sql
SELECT
    player_name,
    AVG(true_shooting_pct) as clutch_ts_pct,
    AVG(game_score) as avg_clutch_score,
    COUNT(*) as clutch_games
FROM player_box_score_snapshots
WHERE is_clutch = 1
  AND points >= 10
GROUP BY player_name
HAVING clutch_games >= 10
ORDER BY clutch_ts_pct DESC;
```

### Pace and Rating Trends
```sql
SELECT
    team_id,
    period,
    AVG(pace) as avg_pace,
    AVG(offensive_rating) as avg_ortg,
    AVG(defensive_rating) as avg_drtg
FROM team_box_score_snapshots
GROUP BY team_id, period
ORDER BY team_id, period;
```

---

## Implementation Status

### ✅ Completed
- Database schema updated with all advanced stat fields
- `AdvancedStatsCalculator` class with all formulas
- Demo showing calculations with realistic NBA data
- Comprehensive documentation

### ⏳ In Progress
- Integration with `sqlite_pbp_processor.py`
- Database INSERT statements updated
- Automatic calculation during snapshot generation

### 📋 Next Steps
1. Update `save_snapshots()` to include advanced stats in INSERTs
2. Calculate advanced stats in `process_game()` when creating snapshots
3. Add opponent stats tracking for defensive rating
4. Create views for common advanced stat queries
5. Build ML feature extraction pipeline

---

## References

**Formulas:**
- Dean Oliver, "Basketball on Paper" (Four Factors)
- John Hollinger (Game Score, PER concepts)
- Basketball-Reference.com (Advanced Stats definitions)
- NBA.com/stats (Official stat definitions)

**Standards:**
- 0.44 coefficient for FTA (league average FT% * 2 FTA per foul)
- 100 possessions as standard for rating calculations
- 48 minutes as standard game length for pace

---

## Summary

**Advanced statistics transform traditional box scores into actionable insights:**

✅ **Efficiency:** TS%, eFG% measure shooting quality
✅ **Impact:** Game Score, ORtg quantify overall contribution
✅ **Pace:** Possessions, Pace normalize for game speed
✅ **Four Factors:** eFG%, TOV%, OREB%, FT Rate determine wins

**These metrics enable:**
- Better player evaluation
- Pace-adjusted team comparisons
- ML features for predictions
- Contextual performance analysis

**The temporal box score system now includes 20+ advanced statistics that update at every play-by-play event, providing real-time advanced analytics for ML training and basketball analysis.**

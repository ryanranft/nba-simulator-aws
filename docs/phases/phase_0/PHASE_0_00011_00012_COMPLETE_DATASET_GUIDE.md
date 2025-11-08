# 🏀 Phase 0.00011-0.00012: Complete Dataset & Metrics Implementation Guide
## Comprehensive KenPom-Style Analytics for NBA Temporal Features

**Created:** November 5, 2025  
**Reference:** KenPom Implementation Strategy Discussion  
**Status:** 📋 PLANNING

---

## 📋 Progress Log

### From Previous Discussion
- ✅ Identified 15+ NBA analytics websites
- ✅ Categorized free vs paid data sources
- ✅ Mapped KenPom-style metrics to NBA
- ✅ Designed temporal rolling features architecture
- ✅ Determined Phase 0.00011-0.00012 is optimal placement

### Current Session
- [ ] Integrate all datasets into Phase 0.00011-0.00012 structure
- [ ] Map data sources to extraction vs calculation
- [ ] Define complete feature set
- [ ] Create implementation timeline

---

## 🎯 Executive Summary

**Goal:** Implement comprehensive KenPom-style analytics using temporal possession-level data

**Approach:**
1. **Phase 0.00011:** Extract possessions from existing play-by-play data (14.1M events)
2. **Phase 0.00012:** Calculate ALL advanced metrics using possession data
3. **No External Scraping Needed:** Calculate metrics ourselves using superior temporal data

**Key Insight:** We have BETTER data than most analytics sites because we have:
- ✅ 14.1M play-by-play events with timestamps
- ✅ Complete game context (score, time, situation)
- ✅ Ability to calculate metrics at any temporal granularity
- ✅ Historical coverage back to play-by-play era

---

## 📊 Data Sources Analysis

### ✅ **Already Have (Don't Need to Add)**

| Source | Status | What We Have | What It Provides |
|--------|--------|--------------|------------------|
| **Basketball-Reference** | ✅ Implemented | Phase 0.0004 | Historical stats, PER, WS, BPM, VORP |
| **NBA.com Stats** | ✅ Implemented | NBA API extractor | Official tracking data, player stats |
| **ESPN** | ✅ Implemented | Phase 0.0001 | 146K files, play-by-play data |
| **hoopR** | ✅ Implemented | Phase 0.0002 | R package data, 410 files |
| **temporal_events** | ✅ Implemented | Database | 14.1M play-by-play events with timestamps |

**Verdict:** We have the RAW DATA. Now we need to CALCULATE the metrics.

---

### 🔄 **Calculate Ourselves (Phase 0.00012)**

These are **methodologies**, not data sources. We implement the formulas using our own data:

| Metric Category | Source Methodology | Implementation Priority |
|----------------|-------------------|------------------------|
| **Four Factors** | Dean Oliver (public) | ⭐⭐⭐ CRITICAL |
| **Tempo-Free Stats** | Dean Oliver / KenPom | ⭐⭐⭐ CRITICAL |
| **Possession Estimation** | Dean Oliver (public) | ⭐⭐⭐ CRITICAL |
| **Adjusted Efficiency** | KenPom methodology | ⭐⭐⭐ CRITICAL |
| **EPM (Est. Plus-Minus)** | Dunks & Threes (public) | ⭐⭐ HIGH |
| **LEBRON** | BBall Index (some public) | ⭐⭐ HIGH |
| **RAPM** | Public methodology | ⭐⭐ HIGH |
| **Garbage Time Filter** | Cleaning the Glass style | ⭐⭐ HIGH |
| **Context Splits** | Transition/half-court | ⭐ MEDIUM |
| **Rolling Windows** | Custom temporal | ⭐⭐⭐ CRITICAL |
| **Hot Hand Detection** | Custom temporal | ⭐⭐ HIGH |
| **Momentum Tracking** | Custom temporal | ⭐⭐ HIGH |

---

## 🔢 Complete Metrics Catalog

### **Phase 0.00011: Possession Extraction**

Extract possession-level data from 14.1M temporal events:

```python
# Output: possession_stats table
# Estimated: 2-3M possessions from 14.1M events

Possession Attributes:
├── possession_id (unique)
├── game_id
├── team_id
├── opponent_id
├── start_time (game clock)
├── end_time (game clock)
├── wall_clock_start (timestamp)
├── wall_clock_end (timestamp)
├── duration_seconds
├── quarter
├── score_differential_start
├── score_differential_end
├── possession_type (offensive/defensive)
├── possession_result (score/turnover/miss/end_quarter)
├── points_scored
├── field_goals_attempted
├── field_goals_made
├── three_pointers_attempted
├── three_pointers_made
├── free_throws_attempted
├── free_throws_made
├── offensive_rebounds
├── defensive_rebounds
├── turnovers
├── assists
├── steals
├── blocks
├── fouls
└── play_sequence (JSON array of plays)
```

---

### **Phase 0.00012: Temporal Feature Engineering**

Calculate ALL advanced metrics from possession data:

---

## 📐 **Category 1: Four Factors (Dean Oliver)**

**Source:** "Basketball on Paper" (2004) - Publicly documented  
**Priority:** ⭐⭐⭐ CRITICAL  
**Implementation:** Phase 0.00012.2

### Metrics:

#### 1. **Effective Field Goal Percentage (eFG%)**
```python
eFG% = (FGM + 0.5 * 3PM) / FGA

Purpose: Adjusts FG% to account for 3-pointers being worth more
Weight in Four Factors: 40%
```

**Temporal Variations:**
- Rolling 5/10/20 possession eFG%
- Quarter-by-quarter eFG%
- Clutch situations eFG% (last 5 min, ±5 points)
- Home/away splits
- Rest days impact

#### 2. **Turnover Rate (TOV%)**
```python
TOV% = TOV / (FGA + 0.44 * FTA + TOV)

Purpose: Estimate turnovers per 100 possessions
Weight in Four Factors: 25%
```

**Temporal Variations:**
- Rolling window TOV%
- Pressure situations (full court press detection)
- Fatigue impact (minutes played correlation)
- Back-to-back game analysis

#### 3. **Offensive Rebound Percentage (ORB%)**
```python
ORB% = ORB / (ORB + Opp_DRB)

Purpose: Percentage of available offensive rebounds grabbed
Weight in Four Factors: 20%
```

**Temporal Variations:**
- By quarter (fatigue effect)
- By lineup (height/athleticism)
- Transition vs half-court
- After made/missed FT

#### 4. **Free Throw Rate (FTR)**
```python
FT_Rate = FTA / FGA

Purpose: How often team gets to free throw line
Weight in Four Factors: 15%
```

**Temporal Variations:**
- By game situation (bonus, double bonus)
- Clutch FTR (last 2 min)
- Home/away (referee bias detection)
- Against specific opponents

---

## 📊 **Category 2: Tempo-Free Statistics (KenPom Methodology)**

**Source:** KenPom.com methodology + Dean Oliver  
**Priority:** ⭐⭐⭐ CRITICAL  
**Implementation:** Phase 0.00012.2

### Metrics:

#### 1. **Possession Estimation**
```python
# Dean Oliver's formula (most widely used)
Possessions = FGA + 0.44*FTA - ORB + TOV

# Alternative: More accurate for modern NBA
Possessions = 0.5 * ((FGA + 0.4*FTA - 1.07*ORB + TOV) + 
                     (Opp_FGA + 0.4*Opp_FTA - 1.07*Opp_ORB + Opp_TOV))
```

**We can calculate EXACT possessions** from play-by-play data, not estimates!

#### 2. **Offensive Efficiency (OffRtg)**
```python
OffRtg = (Points Scored / Possessions) * 100

Purpose: Points per 100 possessions
Makes teams comparable regardless of pace
```

**Temporal Variations:**
- Rolling 5/10/20/50 possession OffRtg
- By quarter
- By lineup
- Clutch OffRtg
- Against top 10 defenses
- Rest days impact

#### 3. **Defensive Efficiency (DefRtg)**
```python
DefRtg = (Points Allowed / Possessions) * 100

Purpose: Points allowed per 100 possessions
Lower is better
```

**Temporal Variations:**
- Rolling windows
- Home/away splits
- Opponent quality adjustment
- Lineup-specific

#### 4. **Net Rating (NetRtg)**
```python
NetRtg = OffRtg - DefRtg

Purpose: Overall team efficiency
Highly predictive of win percentage
```

#### 5. **Adjusted Tempo**
```python
Tempo = (Possessions / Minutes) * 40

Purpose: Possessions per 40 minutes
Pace-neutral comparison
```

**Temporal Variations:**
- By quarter (teams speed up/slow down)
- Situation-specific (leading/trailing)
- Opponent adjustment

#### 6. **Adjusted Efficiency (KenPom's Key Metric)**
```python
AdjO = OffRtg * (Opponent_Defensive_Quality_Factor)
AdjD = DefRtg * (Opponent_Offensive_Quality_Factor)
AdjEM = AdjO - AdjD

Purpose: Adjust for opponent strength
Requires iterative calculation across all teams
```

---

## 🎯 **Category 3: Advanced Impact Metrics**

**Priority:** ⭐⭐ HIGH  
**Implementation:** Phase 0.00012.2-0.00012.3

### Metrics:

#### 1. **Plus-Minus (PM)**
```python
PM = Points_For - Points_Against (while player on court)

Simple but noisy metric
```

#### 2. **Adjusted Plus-Minus (APM)**
```python
# Ridge regression across all lineup combinations
# Isolates individual player impact
# Controls for teammates and opponents

Solves: PM = β₁(Player₁) + β₂(Player₂) + ... + ε
```

**Implementation Complexity:** Medium (requires matrix operations)

#### 3. **Regularized Adjusted Plus-Minus (RAPM)**
```python
# Same as APM but with regularization (Ridge/Lasso)
# Reduces overfitting
# More stable year-to-year

Public methodology available
```

**Implementation Complexity:** Medium

#### 4. **Estimated Plus-Minus (EPM)** - Dunks & Threes
```python
# Combines box score stats + on/off data
# Publicly documented methodology
# Components:
#   - Box score contribution (BPM-style)
#   - Lineup-adjusted component
#   - Prior info from similar players

EPM = Offensive_EPM + Defensive_EPM
```

**Implementation Complexity:** High (but methodology is public)  
**Reference:** https://dunksandthrees.com/epm

#### 5. **LEBRON** - BBall Index
```python
# Luck-adjusted Box Plus-Minus
# Partially public methodology
# Incorporates:
#   - Box score stats
#   - Luck adjustments (shooting variance)
#   - Positional adjustments
#   - Teammate quality

LEBRON = O-LEBRON + D-LEBRON
```

**Implementation Complexity:** High (methodology partially public)

---

## 🔄 **Category 4: Rolling Window Features (TEMPORAL)**

**Priority:** ⭐⭐⭐ CRITICAL  
**Implementation:** Phase 0.00012.1  
**This is our UNIQUE advantage!**

### Metrics:

#### 1. **Rolling Efficiency Windows**
```python
# Calculate for multiple window sizes
Windows = [5, 10, 20, 50, 100] possessions

For each window:
├── Rolling_OffRtg_L5    # Last 5 possessions
├── Rolling_OffRtg_L10   # Last 10 possessions  
├── Rolling_OffRtg_L20   # Last 20 possessions
├── Rolling_DefRtg_L5
├── Rolling_DefRtg_L10
├── Rolling_DefRtg_L20
├── Rolling_NetRtg_L5
├── Rolling_NetRtg_L10
└── Rolling_NetRtg_L20
```

**Use Cases:**
- Detect momentum shifts
- Identify hot/cold streaks
- Predict possession outcomes
- Substitution timing

#### 2. **Rolling Four Factors**
```python
For each window:
├── Rolling_eFG_L5
├── Rolling_eFG_L10
├── Rolling_TOV_L5
├── Rolling_TOV_L10
├── Rolling_ORB_L5
├── Rolling_ORB_L10
├── Rolling_FTR_L5
└── Rolling_FTR_L10
```

#### 3. **Rolling Shooting Performance**
```python
├── Rolling_FG_Pct_L5
├── Rolling_FG_Pct_L10
├── Rolling_3P_Pct_L5
├── Rolling_3P_Pct_L10
├── Rolling_FT_Pct_L5
├── Rolling_FT_Pct_L10
├── Hot_Shooter_Flag       # L5 > season avg + 1 SD
└── Cold_Shooter_Flag      # L5 < season avg - 1 SD
```

---

## 🔥 **Category 5: Momentum & Hot Hand (TEMPORAL)**

**Priority:** ⭐⭐ HIGH  
**Implementation:** Phase 0.00012.3

### Metrics:

#### 1. **Momentum Score**
```python
# Weighted recent performance
Momentum = Σ(weight_i * performance_i)

Where:
- Recent possessions weighted more heavily
- Exponential decay: w_i = exp(-λ * i)
- Performance = NetRtg for possession

Momentum_Score = (0.5 * L5_NetRtg + 
                  0.3 * L10_NetRtg + 
                  0.2 * L20_NetRtg)
```

#### 2. **Hot Hand Detection**
```python
# Statistical test for "hot hand" effect
# Compare recent performance to season baseline

Hot_Hand = {
    'is_hot': recent_performance > baseline + threshold,
    'confidence': z_score,
    'streak_length': consecutive_good_possessions,
    'expected_continuation': probability
}

Methods:
1. Simple threshold (>1 SD above mean)
2. Binomial test (consecutive makes)
3. Bayesian updating (prior + recent data)
```

#### 3. **Clutch Performance**
```python
# Last 5 minutes, score within 5 points
Clutch_Metrics = {
    'clutch_OffRtg': OffRtg in clutch situations,
    'clutch_eFG': eFG% in clutch,
    'clutch_TOV': TOV% in clutch,
    'clutch_FTR': FT_Rate in clutch,
    'clutch_vs_season': clutch_metric - season_avg
}
```

#### 4. **Streak Detection**
```python
# Consecutive scoring possessions
Current_Streak = {
    'offensive_streak': consecutive scores,
    'defensive_stops': consecutive stops,
    'longest_streak_game': max in game,
    'streak_broken_recently': boolean
}
```

---

## 🎮 **Category 6: Game Context Features (TEMPORAL)**

**Priority:** ⭐⭐ HIGH  
**Implementation:** Phase 0.00012.4

### Metrics:

#### 1. **Score Differential Context**
```python
Performance_By_Margin = {
    'blowout_leading': score_diff > 15,
    'leading_close': 5 < score_diff <= 15,
    'tie_game': -5 <= score_diff <= 5,
    'trailing_close': -15 <= score_diff < -5,
    'blowout_trailing': score_diff < -15
}

Calculate separate metrics for each context
```

#### 2. **Time Context**
```python
Performance_By_Time = {
    'Q1': quarter == 1,
    'Q2': quarter == 2,
    'Q3': quarter == 3,
    'Q4_early': quarter == 4 and time_remaining > 5:00,
    'Q4_clutch': quarter == 4 and time_remaining <= 5:00,
    'OT': quarter > 4
}
```

#### 3. **Garbage Time Filter** (Cleaning the Glass methodology)
```python
# Remove possessions that don't matter
Garbage_Time = (
    (score_diff > 15 and time_remaining < 5:00) or
    (score_diff > 20 and time_remaining < 8:00) or
    (score_diff > 25)
)

# Calculate "meaningful possessions" metrics
Meaningful_Metrics = metrics excluding garbage_time
```

#### 4. **Transition vs Half-Court**
```python
# Detect possession type from speed
Possession_Type = {
    'transition': time_to_shot < 8 seconds,
    'early_offense': 8 <= time_to_shot < 15,
    'half_court': time_to_shot >= 15,
    'late_clock': shot_clock < 7
}

# Calculate separate efficiency for each
```

---

## 🧮 **Category 7: Player-Specific Temporal Features**

**Priority:** ⭐⭐ HIGH  
**Implementation:** Phase 0.00012.3

### Metrics:

#### 1. **Usage Rate (Temporal)**
```python
# Percentage of team possessions used by player
Usage% = (FGA + 0.44*FTA + TOV) / (Team_Possessions * Minutes / 48)

Rolling_Usage = {
    'L5_Usage': last 5 possessions,
    'L10_Usage': last 10 possessions,
    'Q1_Usage': first quarter,
    'Q4_Usage': fourth quarter,
    'Clutch_Usage': last 5 min
}
```

#### 2. **True Shooting Percentage (Temporal)**
```python
TS% = Points / (2 * (FGA + 0.44 * FTA))

# Better than FG% because includes FTs and 3s

Rolling_TS% = {
    'L5_TS': last 5 possessions,
    'L10_TS': last 10 possessions,
    'L20_TS': last 20 possessions,
    'vs_Defense_Quality': TS% vs top 10 defenses
}
```

#### 3. **Assist Rate**
```python
AST% = AST / (((Minutes / (Team_Minutes / 5)) * Team_FGM) - FGM)

Rolling_AST% across possession windows
```

#### 4. **Rebound Rate**
```python
TRB% = (TRB * (Team_Minutes / 5)) / (Minutes * (Team_TRB + Opp_TRB))

Rolling_TRB% across possession windows
```

---

## 💾 Database Schema for Phase 0.00012

### **Table 1: temporal_possession_stats**
```sql
CREATE TABLE temporal_possession_stats (
    possession_id VARCHAR(100) PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    opponent_id VARCHAR(50) NOT NULL,
    
    -- Temporal identifiers
    quarter INTEGER NOT NULL,
    game_clock_start VARCHAR(10),
    game_clock_end VARCHAR(10),
    wall_clock_start TIMESTAMP,
    wall_clock_end TIMESTAMP,
    duration_seconds DECIMAL(6,2),
    
    -- Game context
    score_differential_start INTEGER,
    score_differential_end INTEGER,
    is_home_team BOOLEAN,
    is_garbage_time BOOLEAN,
    possession_type VARCHAR(20), -- offensive/defensive/transition
    
    -- Possession outcome
    points_scored INTEGER DEFAULT 0,
    possession_result VARCHAR(20), -- score/turnover/miss/end_quarter
    
    -- Box score stats
    fga INTEGER DEFAULT 0,
    fgm INTEGER DEFAULT 0,
    fg3a INTEGER DEFAULT 0,
    fg3m INTEGER DEFAULT 0,
    fta INTEGER DEFAULT 0,
    ftm INTEGER DEFAULT 0,
    oreb INTEGER DEFAULT 0,
    dreb INTEGER DEFAULT 0,
    ast INTEGER DEFAULT 0,
    stl INTEGER DEFAULT 0,
    blk INTEGER DEFAULT 0,
    tov INTEGER DEFAULT 0,
    pf INTEGER DEFAULT 0,
    
    -- Derived metrics
    efg DECIMAL(5,3),
    ts_pct DECIMAL(5,3),
    
    -- Metadata
    play_sequence JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE INDEX idx_possession_game ON temporal_possession_stats(game_id);
CREATE INDEX idx_possession_team ON temporal_possession_stats(team_id);
CREATE INDEX idx_possession_quarter ON temporal_possession_stats(quarter);
CREATE INDEX idx_possession_garbage ON temporal_possession_stats(is_garbage_time);
```

### **Table 2: temporal_rolling_features**
```sql
CREATE TABLE temporal_rolling_features (
    feature_id SERIAL PRIMARY KEY,
    possession_id VARCHAR(100) NOT NULL,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50), -- NULL for team-level
    
    -- Window metadata
    window_size INTEGER NOT NULL, -- 5, 10, 20, 50 possessions
    window_type VARCHAR(20), -- offensive/defensive/both
    
    -- Efficiency metrics
    rolling_off_rtg DECIMAL(6,2),
    rolling_def_rtg DECIMAL(6,2),
    rolling_net_rtg DECIMAL(6,2),
    rolling_pace DECIMAL(6,2),
    
    -- Four Factors
    rolling_efg DECIMAL(5,3),
    rolling_tov_pct DECIMAL(5,3),
    rolling_orb_pct DECIMAL(5,3),
    rolling_ftr DECIMAL(5,3),
    
    -- Shooting
    rolling_fg_pct DECIMAL(5,3),
    rolling_3p_pct DECIMAL(5,3),
    rolling_ft_pct DECIMAL(5,3),
    rolling_ts_pct DECIMAL(5,3),
    
    -- Volume
    rolling_fga DECIMAL(6,2),
    rolling_fg3a DECIMAL(6,2),
    rolling_fta DECIMAL(6,2),
    
    -- Comparison to baseline
    rolling_vs_season_avg DECIMAL(6,2),
    rolling_z_score DECIMAL(6,3),
    
    -- Flags
    is_hot_shooter BOOLEAN,
    is_cold_shooter BOOLEAN,
    has_positive_momentum BOOLEAN,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (possession_id) REFERENCES temporal_possession_stats(possession_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE INDEX idx_rolling_possession ON temporal_rolling_features(possession_id);
CREATE INDEX idx_rolling_window ON temporal_rolling_features(window_size);
CREATE INDEX idx_rolling_team_player ON temporal_rolling_features(team_id, player_id);
```

### **Table 3: temporal_momentum_tracking**
```sql
CREATE TABLE temporal_momentum_tracking (
    tracking_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    possession_id VARCHAR(100) NOT NULL,
    
    -- Momentum metrics
    momentum_score DECIMAL(6,2), -- Weighted recent performance
    momentum_direction VARCHAR(10), -- positive/negative/neutral
    momentum_strength INTEGER, -- 1-10 scale
    
    -- Streak tracking
    current_scoring_streak INTEGER DEFAULT 0,
    current_defensive_stops INTEGER DEFAULT 0,
    longest_scoring_streak_game INTEGER DEFAULT 0,
    longest_defensive_streak_game INTEGER DEFAULT 0,
    
    -- Run tracking
    current_run_points INTEGER DEFAULT 0, -- Unanswered points
    largest_run_game INTEGER DEFAULT 0,
    
    -- Hot hand indicators
    hot_hand_score DECIMAL(5,2), -- 0-1 probability
    confidence_interval_lower DECIMAL(5,2),
    confidence_interval_upper DECIMAL(5,2),
    
    -- Time context
    quarter INTEGER,
    game_clock VARCHAR(10),
    score_differential INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (possession_id) REFERENCES temporal_possession_stats(possession_id)
);

CREATE INDEX idx_momentum_game ON temporal_momentum_tracking(game_id);
CREATE INDEX idx_momentum_team ON temporal_momentum_tracking(team_id);
```

### **Table 4: temporal_clutch_performance**
```sql
CREATE TABLE temporal_clutch_performance (
    clutch_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50),
    
    -- Clutch definition: Last 5 minutes, score within 5
    possessions_clutch INTEGER,
    possessions_non_clutch INTEGER,
    
    -- Clutch efficiency
    clutch_off_rtg DECIMAL(6,2),
    clutch_def_rtg DECIMAL(6,2),
    clutch_net_rtg DECIMAL(6,2),
    
    -- Clutch four factors
    clutch_efg DECIMAL(5,3),
    clutch_tov_pct DECIMAL(5,3),
    clutch_orb_pct DECIMAL(5,3),
    clutch_ftr DECIMAL(5,3),
    
    -- Clutch shooting
    clutch_fg_pct DECIMAL(5,3),
    clutch_3p_pct DECIMAL(5,3),
    clutch_ft_pct DECIMAL(5,3),
    clutch_ts_pct DECIMAL(5,3),
    
    -- Comparison to non-clutch
    clutch_vs_regular_diff DECIMAL(6,2),
    
    -- Season aggregate
    season INTEGER NOT NULL,
    total_clutch_possessions INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    UNIQUE (game_id, team_id, player_id)
);

CREATE INDEX idx_clutch_game ON temporal_clutch_performance(game_id);
CREATE INDEX idx_clutch_player ON temporal_clutch_performance(player_id, season);
```

### **Table 5: temporal_context_splits**
```sql
CREATE TABLE temporal_context_splits (
    split_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    
    -- Context type
    context_type VARCHAR(30) NOT NULL, -- margin/time/transition/garbage
    context_value VARCHAR(50) NOT NULL, -- e.g., "blowout_leading", "Q4_clutch"
    
    -- Performance in context
    possessions INTEGER,
    off_rtg DECIMAL(6,2),
    def_rtg DECIMAL(6,2),
    net_rtg DECIMAL(6,2),
    pace DECIMAL(6,2),
    
    -- Four factors in context
    efg DECIMAL(5,3),
    tov_pct DECIMAL(5,3),
    orb_pct DECIMAL(5,3),
    ftr DECIMAL(5,3),
    
    -- Shooting in context
    fg_pct DECIMAL(5,3),
    fg3_pct DECIMAL(5,3),
    ft_pct DECIMAL(5,3),
    ts_pct DECIMAL(5,3),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE INDEX idx_context_game ON temporal_context_splits(game_id);
CREATE INDEX idx_context_type ON temporal_context_splits(context_type, context_value);
```

### **Table 6: temporal_advanced_metrics**
```sql
CREATE TABLE temporal_advanced_metrics (
    metric_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50),
    
    -- Advanced impact (if calculated)
    epm DECIMAL(6,3),
    offensive_epm DECIMAL(6,3),
    defensive_epm DECIMAL(6,3),
    
    rapm DECIMAL(6,3),
    offensive_rapm DECIMAL(6,3),
    defensive_rapm DECIMAL(6,3),
    
    lebron DECIMAL(6,3),
    o_lebron DECIMAL(6,3),
    d_lebron DECIMAL(6,3),
    
    -- Adjusted efficiency
    adj_off_rtg DECIMAL(6,2),
    adj_def_rtg DECIMAL(6,2),
    adj_net_rtg DECIMAL(6,2),
    
    -- Player tracking (if available)
    speed_mph DECIMAL(4,1),
    distance_miles DECIMAL(5,2),
    touches INTEGER,
    
    -- Season aggregate
    season INTEGER NOT NULL,
    games_played INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE INDEX idx_advanced_game ON temporal_advanced_metrics(game_id);
CREATE INDEX idx_advanced_player ON temporal_advanced_metrics(player_id, season);
```

---

## 🛠️ Implementation Priority & Timeline

### **Phase 0.00011: Possession Extraction (Weeks 1-2)**

**Priority:** ⭐⭐⭐ CRITICAL FOUNDATION

```
Week 1: Possession Detection
├── Day 1-2: Design possession detection algorithm
├── Day 3-4: Implement extraction from temporal_events
├── Day 5: Test on sample games (100 games)
└── Day 6-7: Validation & bug fixes

Week 2: Validation & Loading
├── Day 8-9: Compare to Dean Oliver estimates
├── Day 10-11: Database schema creation & loading
├── Day 12: Integration with temporal_events
├── Day 13-14: Full dataset processing (14.1M events → 2-3M possessions)
```

**Deliverables:**
- [x] `temporal_possession_stats` table populated
- [x] Possession extraction validated
- [x] Documentation complete

---

### **Phase 0.00012: Temporal Feature Engineering (Weeks 3-8)**

#### **Sub-phase 0.00012.1: Rolling Window Infrastructure (Week 3)**

**Priority:** ⭐⭐⭐ CRITICAL

```
Day 1-2: Design rolling window calculator
Day 3-4: Implement efficient computation (avoid O(n²))
Day 5: Test multiple window sizes
Day 6-7: Database integration
```

**Metrics to Implement:**
- Rolling OffRtg/DefRtg/NetRtg (L5, L10, L20, L50)
- Rolling Four Factors (L5, L10, L20)
- Rolling shooting percentages
- Z-scores vs season average

---

#### **Sub-phase 0.00012.2: KenPom Metrics (Weeks 4-5)**

**Priority:** ⭐⭐⭐ CRITICAL

```
Week 4: Four Factors & Basic Efficiency
├── eFG% calculation
├── TOV% calculation
├── ORB% calculation
├── FTR calculation
├── OffRtg calculation
├── DefRtg calculation
└── NetRtg calculation

Week 5: Adjusted Metrics & Tempo
├── Adjusted Efficiency (iterative calculation)
├── Strength of schedule adjustments
├── Tempo calculations
└── Pace adjustments
```

---

#### **Sub-phase 0.00012.3: Momentum & Hot Hand (Week 6)**

**Priority:** ⭐⭐ HIGH

```
Day 1-2: Momentum scoring algorithm
Day 3-4: Hot hand statistical tests
Day 5: Streak detection
Day 6-7: Database integration & validation
```

**Metrics to Implement:**
- Momentum score (weighted recent performance)
- Hot hand probability (Bayesian)
- Streak tracking (scoring/defensive)
- Run tracking (unanswered points)

---

#### **Sub-phase 0.00012.4: Clutch & Context (Week 7)**

**Priority:** ⭐⭐ HIGH

```
Day 1-2: Clutch situation detection
Day 3-4: Garbage time filtering
Day 5: Context splits (transition/half-court)
Day 6-7: Score differential analysis
```

**Metrics to Implement:**
- Clutch performance (last 5 min, ±5 points)
- Garbage time filter
- Transition vs half-court splits
- Performance by score margin

---

#### **Sub-phase 0.00012.5: Advanced Impact (Week 8)**

**Priority:** ⭐ MEDIUM (Can defer if needed)

```
Day 1-3: APM/RAPM implementation (ridge regression)
Day 4-5: EPM approximation (public methodology)
Day 6-7: LEBRON approximation (partial methodology)
```

**Note:** These are computationally intensive and can be Phase 2 if needed.

---

#### **Sub-phase 0.00012.6: ML Integration (Week 8)**

**Priority:** ⭐⭐⭐ CRITICAL

```
Day 1-2: Feature dataset generation
Day 3-4: Training/validation/test splits
Day 5: Feature importance analysis
Day 6-7: Documentation & handoff to Phase 5 (ML)
```

**Deliverables:**
- ML-ready feature datasets
- Feature catalog documentation
- Integration with Phase 5 pipelines

---

## 📦 Package Structure

```
nba_simulator/
│
├── etl/
│   └── transformers/
│       ├── possession_transformer.py       # Phase 0.00011
│       └── temporal_feature_transformer.py # Phase 0.00012
│
├── features/                                # NEW MODULE
│   ├── __init__.py
│   │
│   ├── possession/
│   │   ├── __init__.py
│   │   ├── extractor.py                    # Possession detection
│   │   ├── validator.py                    # Validation against Oliver
│   │   └── loader.py                       # Database loading
│   │
│   ├── temporal/
│   │   ├── __init__.py
│   │   ├── rolling_windows.py              # Window calculations
│   │   ├── kenpom_metrics.py               # Four Factors, Efficiency
│   │   ├── momentum_tracking.py            # Momentum & streaks
│   │   ├── clutch_performance.py           # Clutch metrics
│   │   ├── context_splits.py               # Transition, garbage time
│   │   └── advanced_metrics.py             # EPM, RAPM, LEBRON
│   │
│   └── validation/
│       ├── __init__.py
│       ├── four_factors_validator.py
│       ├── efficiency_validator.py
│       └── temporal_validator.py
│
└── database/
    └── schemas/
        ├── temporal_possession_stats.sql
        ├── temporal_rolling_features.sql
        ├── temporal_momentum_tracking.sql
        ├── temporal_clutch_performance.sql
        ├── temporal_context_splits.sql
        └── temporal_advanced_metrics.sql
```

---

## 📊 Expected Output Datasets

### **1. Possession-Level Dataset**
```
Rows: ~2-3 million possessions (from 14.1M events)
Columns: ~50 (possession attributes + box score stats)
Size: ~500 MB
Use: Foundation for all temporal features
```

### **2. Rolling Features Dataset**
```
Rows: ~10-15 million (multiple windows per possession)
Columns: ~30 per window size
Size: ~2-3 GB
Use: ML training, momentum detection
```

### **3. Clutch Performance Dataset**
```
Rows: ~50,000 clutch situations
Columns: ~25
Size: ~50 MB
Use: Late-game prediction, player evaluation
```

### **4. Context Splits Dataset**
```
Rows: ~200,000 game-context combinations
Columns: ~20
Size: ~100 MB
Use: Situation-aware predictions
```

### **5. Advanced Metrics Dataset**
```
Rows: ~300,000 (player-seasons + game-level)
Columns: ~15
Size: ~50 MB
Use: Player evaluation, roster construction
```

---

## ✅ Validation Strategy

### **1. Four Factors Validation**
```python
# Compare to published leaderboards
test_seasons = [2019, 2020, 2021, 2022, 2023]

for season in test_seasons:
    our_results = calculate_four_factors(season)
    nba_com_results = fetch_nba_com_four_factors(season)
    
    correlation = pearsonr(our_results, nba_com_results)
    assert correlation > 0.99, "Four Factors don't match!"
```

### **2. Efficiency Validation**
```python
# Compare OffRtg/DefRtg to NBA.com
# Should be nearly identical (within 0.5 points)

our_offrtg = calculate_offensive_rating(team, season)
nba_offrtg = fetch_nba_official_ortg(team, season)

assert abs(our_offrtg - nba_offrtg) < 0.5
```

### **3. Possession Count Validation**
```python
# Dean Oliver formula vs our exact count
oliver_estimate = calculate_oliver_possessions(game)
our_exact_count = count_exact_possessions(game)

# Should be within 2-3 possessions
assert abs(oliver_estimate - our_exact_count) < 3
```

### **4. Hot Hand Validation**
```python
# Test against known hot/cold streaks
# Use famous performances (Klay 37-point quarter, etc.)

famous_performances = [
    {"player": "Klay Thompson", "game": "2015-01-23", "expected": "HOT"},
    {"player": "LeBron James", "game": "2012-06-06", "expected": "HOT"},
]

for performance in famous_performances:
    hot_hand_score = calculate_hot_hand(performance)
    assert hot_hand_score > 0.8, f"Failed to detect hot hand!"
```

---

## 🎯 Success Criteria

### **Phase 0.00011 Complete When:**
- [x] `temporal_possession_stats` table has 2-3M rows
- [x] Possession counts within 3 of Dean Oliver estimates
- [x] Box score stats match source data
- [x] Temporal ordering is correct
- [x] 95%+ test coverage
- [x] Documentation complete

### **Phase 0.00012 Complete When:**
- [x] All 6 database tables populated
- [x] Four Factors match NBA.com (r > 0.99)
- [x] Efficiency metrics match NBA.com (±0.5)
- [x] Rolling windows calculate correctly
- [x] Hot hand detection validated on known cases
- [x] Clutch metrics calculated
- [x] ML training datasets generated
- [x] 95%+ test coverage
- [x] Documentation complete

---

## 💰 Cost Analysis

### **Free Data Sources Used:**
- ✅ Basketball-Reference (already scraping)
- ✅ NBA.com Stats (already have)
- ✅ Dean Oliver formulas (public)
- ✅ KenPom methodology (public)

### **Optional Paid Sources (Not Required):**
- ⚠️ Cleaning the Glass ($10/mo) - For methodology reference only
- ⚠️ PBPStats ($10/mo) - We can calculate this ourselves
- ⚠️ BBall Index ($5/mo) - LEBRON is nice-to-have

**Total Cost: $0** (We calculate everything ourselves!)

---

## 🚀 Quick Start Commands

### **Start Phase 0.00011:**
```bash
# Create directories
mkdir -p docs/phases/phase_0/0.00011_possession_extraction
mkdir -p scripts/0_00011
mkdir -p nba_simulator/features/possession

# Run possession extraction
python scripts/0_00011/extract_possessions.py \
    --source temporal_events \
    --output possession_stats \
    --validate

# Validate results
python scripts/0_00011/validate_possessions.py \
    --compare-to-oliver
```

### **Start Phase 0.00012:**
```bash
# Create directories
mkdir -p docs/phases/phase_0/0.00012_temporal_features
mkdir -p scripts/0_00012
mkdir -p nba_simulator/features/temporal

# Calculate Four Factors
python scripts/0_00012/calculate_four_factors.py \
    --source possession_stats \
    --output temporal_features

# Calculate Rolling Windows
python scripts/0_00012/calculate_rolling_features.py \
    --windows 5,10,20,50 \
    --metrics OffRtg,DefRtg,eFG,TOV

# Generate ML datasets
python scripts/0_00012/generate_training_datasets.py \
    --output ml_features/ \
    --split train:0.7,val:0.15,test:0.15
```

---

## 📚 References

### **Methodologies (Public)**
1. Dean Oliver - "Basketball on Paper" (2004)
2. KenPom.com - Adjusted Efficiency methodology
3. Dunks & Threes - EPM methodology (public blog posts)
4. Cleaning the Glass - Garbage time filtering (methodology documented)

### **Data Sources (Already Have)**
1. Basketball-Reference - Phase 0.0004
2. NBA.com Stats - NBA API extractor
3. ESPN - Phase 0.0001
4. hoopR - Phase 0.0002
5. temporal_events table - 14.1M records

### **Tools & Libraries**
```python
# Required
pandas
numpy
scipy
sklearn
sqlalchemy
psycopg2

# Optional (for advanced metrics)
cvxpy  # For RAPM optimization
statsmodels  # For regression
```

---

## 🎉 Conclusion

**We have everything we need!**

- ✅ 14.1M play-by-play events with timestamps
- ✅ Complete game context (score, time, situation)
- ✅ Public methodologies for all major metrics
- ✅ No paid subscriptions required
- ✅ Better temporal granularity than any analytics site
- ✅ Perfect phase placement (0.00011-0.00012)

**This implementation will give you:**
- Professional-grade KenPom-style analytics
- Unique temporal rolling features
- ML-ready training datasets
- Foundation for advanced simulation
- Competitive advantage over commercial analytics

**Ready to begin implementation!** 🚀

---

**Document Status:** ✅ COMPLETE  
**Next Step:** Update KENPOM_TEMPORAL_FEATURES_IMPLEMENTATION_GUIDE.md with these datasets  
**Estimated Implementation:** 8 weeks (Phase 0.00011: 2 weeks, Phase 0.00012: 6 weeks)

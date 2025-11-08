# 🏀 KenPom-Style Temporal Features Implementation Guide
## Phase 0.0005-0.0006: Possession Extraction & Advanced Analytics

**Created:** November 5, 2025  
**Status:** 📋 READY FOR IMPLEMENTATION  
**Phase Placement:** 0.0005-0.0006 in Phase 0 (between 0.0004 and 0.0007)  
**Based on:** KenPom methodology, Dean Oliver's "Basketball on Paper", NBA Analytics Sites Research

---

## 📋 Progress Log

### Planning Complete ✅
- [x] Analyzed Phase 0 structure (23 sub-phases, all complete)
- [x] Determined optimal placement: 0.0005-0.0006 (after 0.0004, before 0.0007)
- [x] Researched 15+ NBA analytics sites for methodologies
- [x] Identified all free public formulas (Dean Oliver, KenPom)
- [x] Designed complete database schema (6 tables)
- [x] Cataloged 100+ metrics across 7 categories
- [x] Created 8-week implementation timeline

### Implementation Pending ⏸️
- [ ] Create Phase 0.0005 directory structure
- [ ] Create Phase 0.0006 directory structure
- [ ] Implement possession extraction (Week 1-2)
- [ ] Implement temporal features (Week 3-8)

---

## 🎯 Executive Summary

**Goal:** Transform raw play-by-play data into advanced KenPom-style analytics with unique temporal rolling features

**Why Now:** Phase 0.0001 just uploaded 14.1M temporal events. Transform this data immediately before adding more sources.

**What We're Building:**
1. **Phase 0.0005:** Extract 2-3M possessions from 14.1M events
2. **Phase 0.0006:** Calculate 100+ advanced metrics (Four Factors, Rolling Windows, Momentum, Clutch)

**Unique Advantage:** Rolling temporal features at possession-level granularity (no commercial site offers this)

**Cost:** $0 (all methodologies are public, we calculate ourselves)

**Timeline:** 8 weeks total (2 weeks possession extraction + 6 weeks feature engineering)

---

## 📍 Phase 0 Placement Strategy

### Current Phase 0 Structure

```
Phase 0: Data Collection (23 sub-phases COMPLETE)

0.0001 - Initial Data Collection ✅
    ↓ 14.1M temporal events uploaded
    ↓ 172,719 files, 118 GB
    ↓
0.0005 - Possession Extraction ⭐ NEW (Week 1-2)
    ↓ Extract 2-3M possessions
    ↓ Validate against Dean Oliver
    ↓
0.0006 - Temporal Features ⭐ NEW (Week 3-8)
    ↓ Calculate 100+ metrics
    ↓ Generate ML training datasets
    ↓
0.0002 - hoopR Data Collection ✅
0.0003 - Kaggle Historical Database ✅
0.0004 - Basketball Reference ✅
...
0.0025 - Daily ESPN Update Workflow ✅
```

### Why Between 0.0001 and 0.0002?

**Perfect Chronological Flow:**
1. ✅ 0.0001 uploads ESPN data (14.1M events)
2. ⭐ 0.0005 immediately transforms that data into possessions
3. ⭐ 0.0006 calculates features from possessions
4. ✅ 0.0002 adds hoopR data (can later process this too)

**Separation of Concerns:**
- **4-digit phases (0.000X)** = Data upload/collection
- **5-digit phases (0.000XX)** = Data transformation/processing

**Clear to Users:**
Reading Phase 0 documentation shows:
- "First we uploaded data" (0.0001)
- "Then we transformed it" (0.0005-0.0006)
- "Then we added more sources" (0.0002+)

---

## 📊 Data Foundation

### What We Already Have

From Phase 0.0001 (Initial Data Collection):

| Data Source | Records | Coverage | Quality |
|-------------|---------|----------|---------|
| **temporal_events** | 14.1M events | 1946-2025 | ✅ Validated |
| **ESPN Data** | 172,719 files | 146K files | ✅ Complete |
| **Play-by-Play** | 6.8M plays | 14,798 games | ✅ Temporal |
| **Wall Clock Timestamps** | Yes | Millisecond precision | ✅ Aligned |

**Key Insight:** We have BETTER data than any commercial analytics site:
- ✅ 14.1M temporal events (exact timestamps)
- ✅ Complete game context (score, time, situation)
- ✅ Millisecond-precision reconstruction
- ✅ Historical coverage back to 1946

Most analytics sites work with aggregated box scores. We have raw events.

---

## 🎯 Phase 0.0005: Possession Extraction

**Status:** ⏸️ PENDING  
**Duration:** 2 weeks  
**Prerequisites:** 0.0001 (Initial Data Collection)  
**Output:** 2-3M possessions with full temporal context

### Overview

Extract possession-level data from 14.1M temporal events. A possession is a continuous sequence of plays by one team until they score, turn it over, or the quarter ends.

### Sub-Phases

#### **0.0005.1: Possession Detection Algorithm** (Days 1-2)
```python
# nba_simulator/features/possession/extractor.py

class PossessionExtractor:
    """
    Extract possessions from temporal_events table.
    
    Possession Definition (Dean Oliver):
    - Starts: Team gains control (rebound, steal, inbound)
    - Ends: Team scores, turnover, opponent rebound, quarter end
    """
    
    def detect_possession_start(self, event):
        """Identify possession-starting events"""
        start_events = [
            'rebound_defensive',
            'steal',
            'inbound',
            'jump_ball_won',
            'quarter_start'
        ]
        return event['event_type'] in start_events
    
    def detect_possession_end(self, event):
        """Identify possession-ending events"""
        end_events = [
            'field_goal_made',
            'free_throw_made',
            'turnover',
            'rebound_defensive',  # By opponent
            'quarter_end',
            'game_end'
        ]
        return event['event_type'] in end_events
    
    def extract_possessions(self, game_id):
        """
        Extract all possessions for a game.
        
        Algorithm:
        1. Load temporal_events for game (chronological)
        2. Initialize possession = None
        3. For each event:
           - If possession_start: Create new possession
           - If possession_end: Close current possession
           - Otherwise: Add event to current possession
        4. Validate possessions
        5. Return possession list
        """
        pass
```

**Deliverables:**
- Possession detection algorithm
- Edge case handling (fast breaks, offensive rebounds)
- Unit tests (100 games)

---

#### **0.0005.2: Possession Validation** (Days 3-4)

**Validation Against Dean Oliver Formula:**
```python
# Dean Oliver's possession estimate
def oliver_possessions(game_stats):
    """
    Possessions ≈ FGA + 0.44*FTA - ORB + TOV
    
    Our exact count should be within 2-3 possessions
    """
    estimate = (
        game_stats['fga'] + 
        0.44 * game_stats['fta'] - 
        game_stats['oreb'] + 
        game_stats['tov']
    )
    return estimate

# Validation
def validate_possession_count(game_id):
    our_count = count_exact_possessions(game_id)
    oliver_estimate = oliver_possessions(get_game_stats(game_id))
    
    diff = abs(our_count - oliver_estimate)
    assert diff < 3, f"Possession count off by {diff}"
```

**Test Cases:**
- Normal games (no OT)
- Overtime games
- Fast break heavy games
- Slow tempo games
- Games with technical fouls

**Deliverables:**
- Validation framework
- Test suite (1,000 games)
- Error analysis report

---

#### **0.0005.3: Database Schema & Loading** (Days 5-7)

**Database Table: `temporal_possession_stats`**

```sql
CREATE TABLE temporal_possession_stats (
    -- Primary Key
    possession_id VARCHAR(100) PRIMARY KEY,  -- Format: {game_id}_{team_id}_P{num}
    
    -- Foreign Keys
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    opponent_id VARCHAR(50) NOT NULL,
    
    -- Temporal Context
    quarter INTEGER NOT NULL,
    game_clock_start VARCHAR(10),  -- MM:SS format
    game_clock_end VARCHAR(10),
    wall_clock_start TIMESTAMP WITH TIME ZONE,
    wall_clock_end TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(6,2),
    
    -- Game Situation
    score_differential_start INTEGER,
    score_differential_end INTEGER,
    is_home_team BOOLEAN NOT NULL,
    is_garbage_time BOOLEAN DEFAULT FALSE,
    
    -- Possession Type
    possession_type VARCHAR(20),  -- 'offensive', 'defensive', 'transition'
    possession_result VARCHAR(20),  -- 'score', 'turnover', 'miss', 'end_quarter'
    
    -- Scoring
    points_scored INTEGER DEFAULT 0,
    
    -- Box Score Stats (Team Total for Possession)
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
    
    -- Derived Metrics
    efg DECIMAL(5,3),  -- (FGM + 0.5*3PM) / FGA
    ts_pct DECIMAL(5,3),  -- Points / (2*(FGA + 0.44*FTA))
    
    -- Play Sequence
    play_sequence JSONB,  -- Array of event objects
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_game FOREIGN KEY (game_id) REFERENCES games(game_id),
    CONSTRAINT fk_team FOREIGN KEY (team_id) REFERENCES teams(team_id),
    CONSTRAINT fk_opponent FOREIGN KEY (opponent_id) REFERENCES teams(team_id),
    CONSTRAINT chk_quarter CHECK (quarter >= 1 AND quarter <= 10),  -- Up to 6 OT
    CONSTRAINT chk_points CHECK (points_scored >= 0 AND points_scored <= 10),  -- Max possession points
    CONSTRAINT chk_duration CHECK (duration_seconds >= 0 AND duration_seconds <= 240)  -- 4 min max
);

-- Indexes for Performance
CREATE INDEX idx_possession_game ON temporal_possession_stats(game_id);
CREATE INDEX idx_possession_team ON temporal_possession_stats(team_id);
CREATE INDEX idx_possession_quarter ON temporal_possession_stats(quarter);
CREATE INDEX idx_possession_wall_clock ON temporal_possession_stats(wall_clock_start);
CREATE INDEX idx_possession_garbage ON temporal_possession_stats(is_garbage_time);
CREATE INDEX idx_possession_type ON temporal_possession_stats(possession_type);
CREATE INDEX idx_possession_result ON temporal_possession_stats(possession_result);

-- Performance: Partitioning by Season (Optional)
-- For 2-3M possessions, single table is fine
-- If we grow beyond 10M, partition by season_year
```

**Loading Process:**
```python
def load_possessions_to_database(possessions_df):
    """
    Batch insert possessions to database.
    
    Process:
    1. Validate dataframe schema
    2. Calculate derived metrics (eFG, TS%)
    3. Convert to SQL-ready format
    4. Batch insert (1000 rows at a time)
    5. Verify row counts
    """
    pass
```

**Deliverables:**
- Database schema SQL file
- ETL loading script
- Validation queries
- Performance tests

---

#### **0.0005.4: Integration with temporal_events** (Days 8-14)

**Link Possessions Back to Raw Events:**
```sql
-- Add possession_id to temporal_events
ALTER TABLE temporal_events 
ADD COLUMN possession_id VARCHAR(100);

-- Create index
CREATE INDEX idx_temporal_events_possession 
ON temporal_events(possession_id);

-- Update with possession IDs
UPDATE temporal_events te
SET possession_id = tps.possession_id
FROM temporal_possession_stats tps
WHERE te.game_id = tps.game_id
  AND te.wall_clock BETWEEN tps.wall_clock_start AND tps.wall_clock_end;
```

**Full Dataset Processing:**
```bash
# Process all 14.1M events → 2-3M possessions
python scripts/0_0005/extract_possessions.py \
    --source temporal_events \
    --output temporal_possession_stats \
    --batch-size 1000 \
    --validate

# Expected output:
# - 2-3M possession records
# - ~500 MB database table
# - 95%+ test coverage
# - Documentation complete
```

**Deliverables:**
- Full dataset processing
- Performance optimization
- Monitoring integration
- Complete documentation

---

### Success Criteria for Phase 0.0005

- [ ] `temporal_possession_stats` table has 2-3M rows
- [ ] Possession counts within 3 of Dean Oliver estimates (95% of games)
- [ ] Box score stats match source data (100%)
- [ ] Temporal ordering is correct (chronological)
- [ ] 95%+ test coverage
- [ ] Documentation complete
- [ ] Integration with DIMS monitoring

---

## 🎯 Phase 0.0006: Temporal Feature Engineering

**Status:** ⏸️ PENDING  
**Duration:** 6 weeks  
**Prerequisites:** 0.0005 (Possession Extraction)  
**Output:** 100+ advanced metrics, ML-ready datasets

### Overview

Calculate comprehensive KenPom-style analytics from possession data, including unique temporal rolling features unavailable on any commercial site.

---

### Sub-Phase 0.0006.1: Rolling Window Infrastructure (Week 3)

**Goal:** Implement efficient rolling calculations across multiple window sizes

#### **Rolling Window Calculator**

```python
# nba_simulator/features/temporal/rolling_windows.py

class RollingWindowCalculator:
    """
    Calculate metrics over rolling windows of possessions.
    
    Window Sizes: 5, 10, 20, 50, 100 possessions
    Metrics: OffRtg, DefRtg, eFG%, TOV%, etc.
    """
    
    def __init__(self, window_sizes=[5, 10, 20, 50]):
        self.window_sizes = window_sizes
    
    def calculate_rolling_efficiency(self, possessions_df, window=5):
        """
        Calculate rolling offensive/defensive rating.
        
        OffRtg = (Points / Possessions) * 100
        DefRtg = (Points Allowed / Possessions) * 100
        """
        # Use pandas rolling window
        possessions_df['rolling_off_rtg'] = (
            possessions_df['points_scored']
            .rolling(window=window, min_periods=1)
            .sum() / window * 100
        )
        return possessions_df
    
    def calculate_rolling_four_factors(self, possessions_df, window=5):
        """Calculate Four Factors over rolling window"""
        # eFG%
        rolling_fgm = possessions_df['fgm'].rolling(window).sum()
        rolling_fg3m = possessions_df['fg3m'].rolling(window).sum()
        rolling_fga = possessions_df['fga'].rolling(window).sum()
        
        possessions_df['rolling_efg'] = (
            (rolling_fgm + 0.5 * rolling_fg3m) / rolling_fga
        )
        
        # TOV%
        rolling_tov = possessions_df['tov'].rolling(window).sum()
        rolling_fta = possessions_df['fta'].rolling(window).sum()
        
        possessions_df['rolling_tov_pct'] = (
            rolling_tov / (rolling_fga + 0.44*rolling_fta + rolling_tov)
        )
        
        # Continue for ORB%, FTR
        return possessions_df
```

**Database Table: `temporal_rolling_features`**

```sql
CREATE TABLE temporal_rolling_features (
    -- Primary Key
    feature_id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    possession_id VARCHAR(100) NOT NULL,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50),  -- NULL for team-level
    
    -- Window Metadata
    window_size INTEGER NOT NULL,  -- 5, 10, 20, 50 possessions
    window_type VARCHAR(20),  -- 'offensive', 'defensive', 'both'
    
    -- Efficiency Metrics
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
    
    -- Comparison to Baseline
    rolling_vs_season_avg DECIMAL(6,2),  -- Rolling - Season Avg
    rolling_z_score DECIMAL(6,3),  -- Standard deviations from mean
    
    -- Binary Flags
    is_hot_shooter BOOLEAN,  -- rolling > season_avg + 1 SD
    is_cold_shooter BOOLEAN,  -- rolling < season_avg - 1 SD
    has_positive_momentum BOOLEAN,  -- rolling_net_rtg > 0
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_possession FOREIGN KEY (possession_id) 
        REFERENCES temporal_possession_stats(possession_id),
    CONSTRAINT fk_game FOREIGN KEY (game_id) 
        REFERENCES games(game_id),
    CONSTRAINT fk_team FOREIGN KEY (team_id) 
        REFERENCES teams(team_id),
    CONSTRAINT chk_window CHECK (window_size IN (5, 10, 20, 50, 100))
);

-- Indexes
CREATE INDEX idx_rolling_possession ON temporal_rolling_features(possession_id);
CREATE INDEX idx_rolling_window ON temporal_rolling_features(window_size);
CREATE INDEX idx_rolling_team_player ON temporal_rolling_features(team_id, player_id);
CREATE INDEX idx_rolling_hot_cold ON temporal_rolling_features(is_hot_shooter, is_cold_shooter);
```

**Deliverables:**
- Rolling window calculator
- Database schema & loading
- Performance optimization (avoid O(n²))
- Test suite

---

### Sub-Phase 0.0006.2: KenPom Metrics (Weeks 4-5)

**Goal:** Implement Four Factors and Tempo-Free Statistics

#### **Category 1: Four Factors (Dean Oliver)**

```python
# nba_simulator/features/temporal/kenpom_metrics.py

class FourFactors:
    """
    Dean Oliver's Four Factors of Basketball Success.
    
    Published: "Basketball on Paper" (2004)
    Weights: eFG% (40%), TOV% (25%), ORB% (20%), FTR (15%)
    """
    
    def effective_fg_percentage(self, fgm, fga, fg3m):
        """
        eFG% = (FGM + 0.5 * 3PM) / FGA
        
        Adjusts FG% to account for 3-pointers being worth more.
        """
        if fga == 0:
            return 0.0
        return (fgm + 0.5 * fg3m) / fga
    
    def turnover_rate(self, tov, fga, fta):
        """
        TOV% = TOV / (FGA + 0.44 * FTA + TOV)
        
        Estimate of turnovers per 100 possessions.
        """
        possessions = fga + 0.44 * fta + tov
        if possessions == 0:
            return 0.0
        return tov / possessions
    
    def offensive_rebound_percentage(self, orb, team_orb, opp_drb):
        """
        ORB% = ORB / (ORB + Opp DRB)
        
        Percentage of available offensive rebounds grabbed.
        """
        available = team_orb + opp_drb
        if available == 0:
            return 0.0
        return team_orb / available
    
    def free_throw_rate(self, fta, fga):
        """
        FT Rate = FTA / FGA
        
        How often team gets to the free throw line.
        """
        if fga == 0:
            return 0.0
        return fta / fga
```

#### **Category 2: Tempo-Free Statistics**

```python
class TempoFreeStats:
    """
    KenPom-style tempo-free statistics.
    
    Makes teams comparable regardless of pace.
    """
    
    def offensive_rating(self, points, possessions):
        """
        OffRtg = (Points / Possessions) * 100
        
        Points scored per 100 possessions.
        """
        if possessions == 0:
            return 0.0
        return (points / possessions) * 100
    
    def defensive_rating(self, points_allowed, possessions):
        """
        DefRtg = (Points Allowed / Possessions) * 100
        
        Points allowed per 100 possessions.
        Lower is better.
        """
        if possessions == 0:
            return 0.0
        return (points_allowed / possessions) * 100
    
    def net_rating(self, off_rtg, def_rtg):
        """
        NetRtg = OffRtg - DefRtg
        
        Overall team efficiency.
        Highly predictive of win percentage.
        """
        return off_rtg - def_rtg
    
    def tempo(self, possessions, minutes):
        """
        Tempo = (Possessions / Minutes) * 40
        
        Possessions per 40 minutes.
        Pace-neutral comparison.
        """
        if minutes == 0:
            return 0.0
        return (possessions / minutes) * 40
    
    def adjusted_efficiency(self, off_rtg, opp_def_quality):
        """
        AdjO = OffRtg * (League_Avg_DefRtg / Opp_DefRtg)
        
        Adjust for opponent strength.
        Requires iterative calculation across all teams.
        """
        league_avg_def = 110.0  # Example
        return off_rtg * (league_avg_def / opp_def_quality)
```

**Database Storage:**

All metrics stored in `temporal_rolling_features` table with `window_size=0` for full-game stats.

**Deliverables:**
- Four Factors calculator
- Tempo-Free stats calculator
- Adjusted efficiency (iterative)
- Validation against NBA.com

---

### Sub-Phase 0.0006.3: Momentum & Hot Hand (Week 6)

**Goal:** Detect momentum shifts and hot/cold streaks

#### **Momentum Tracking**

```python
# nba_simulator/features/temporal/momentum_tracking.py

class MomentumTracker:
    """
    Track team/player momentum using weighted recent performance.
    """
    
    def calculate_momentum_score(self, recent_possessions, weights=None):
        """
        Momentum = Σ(weight_i * performance_i)
        
        Default weights: Exponential decay
        - Last 5 possessions: High weight
        - Last 10 possessions: Medium weight
        - Last 20 possessions: Low weight
        """
        if weights is None:
            # Exponential decay
            weights = np.exp(-0.1 * np.arange(len(recent_possessions)))
            weights = weights / weights.sum()  # Normalize
        
        performances = [p['net_rtg'] for p in recent_possessions]
        momentum = np.dot(weights, performances)
        return momentum
    
    def detect_run(self, possessions):
        """
        Detect scoring runs (unanswered points).
        
        Example: 10-0 run, 8-2 run
        """
        current_run = 0
        max_run = 0
        
        for p in possessions:
            if p['points_scored'] > 0:
                current_run += p['points_scored']
                max_run = max(max_run, current_run)
            elif p['opp_points'] > 0:
                current_run = 0  # Run broken
        
        return max_run
```

#### **Hot Hand Detection**

```python
class HotHandDetector:
    """
    Statistical test for "hot hand" effect.
    
    Methods:
    1. Simple threshold (>1 SD above mean)
    2. Binomial test (consecutive makes)
    3. Bayesian updating (prior + recent data)
    """
    
    def simple_hot_hand_test(self, recent_fg_pct, season_avg, season_std):
        """
        Hot if recent_fg_pct > season_avg + 1*SD
        """
        threshold = season_avg + season_std
        return recent_fg_pct > threshold
    
    def binomial_hot_hand_test(self, makes, attempts, expected_pct):
        """
        Binomial test: Is this streak statistically significant?
        """
        from scipy.stats import binom
        
        p_value = binom.cdf(makes, attempts, expected_pct)
        return p_value < 0.05  # 95% confidence
    
    def bayesian_hot_hand(self, recent_makes, recent_attempts, 
                          prior_mean, prior_std):
        """
        Bayesian updating of shooting probability.
        
        Prior: Season average (mean, std)
        Data: Recent performance
        Posterior: Updated belief
        """
        # Beta-Binomial conjugate prior
        alpha_prior = prior_mean * 100  # Convert to Beta params
        beta_prior = (1 - prior_mean) * 100
        
        alpha_post = alpha_prior + recent_makes
        beta_post = beta_prior + (recent_attempts - recent_makes)
        
        posterior_mean = alpha_post / (alpha_post + beta_post)
        posterior_std = np.sqrt(
            alpha_post * beta_post / 
            ((alpha_post + beta_post)**2 * (alpha_post + beta_post + 1))
        )
        
        return posterior_mean, posterior_std
```

**Database Table: `temporal_momentum_tracking`**

```sql
CREATE TABLE temporal_momentum_tracking (
    -- Primary Key
    tracking_id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    possession_id VARCHAR(100) NOT NULL,
    
    -- Momentum Metrics
    momentum_score DECIMAL(6,2),  -- Weighted recent performance
    momentum_direction VARCHAR(10),  -- 'positive', 'negative', 'neutral'
    momentum_strength INTEGER,  -- 1-10 scale
    
    -- Streak Tracking
    current_scoring_streak INTEGER DEFAULT 0,
    current_defensive_stops INTEGER DEFAULT 0,
    longest_scoring_streak_game INTEGER DEFAULT 0,
    longest_defensive_streak_game INTEGER DEFAULT 0,
    
    -- Run Tracking
    current_run_points INTEGER DEFAULT 0,  -- Unanswered points
    largest_run_game INTEGER DEFAULT 0,
    
    -- Hot Hand Indicators
    hot_hand_score DECIMAL(5,2),  -- 0-1 probability
    confidence_interval_lower DECIMAL(5,2),
    confidence_interval_upper DECIMAL(5,2),
    
    -- Time Context
    quarter INTEGER,
    game_clock VARCHAR(10),
    score_differential INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT fk_game FOREIGN KEY (game_id) REFERENCES games(game_id),
    CONSTRAINT fk_team FOREIGN KEY (team_id) REFERENCES teams(team_id),
    CONSTRAINT fk_possession FOREIGN KEY (possession_id) 
        REFERENCES temporal_possession_stats(possession_id)
);

-- Indexes
CREATE INDEX idx_momentum_game ON temporal_momentum_tracking(game_id);
CREATE INDEX idx_momentum_team ON temporal_momentum_tracking(team_id);
CREATE INDEX idx_momentum_score ON temporal_momentum_tracking(momentum_score DESC);
```

**Deliverables:**
- Momentum calculator
- Hot hand detector (3 methods)
- Streak detection
- Run tracking
- Database integration

---

### Sub-Phase 0.0006.4: Clutch & Context (Week 7)

**Goal:** Analyze performance in clutch situations and different game contexts

#### **Clutch Performance**

```python
# nba_simulator/features/temporal/clutch_performance.py

class ClutchAnalyzer:
    """
    Analyze performance in clutch situations.
    
    Clutch Definition: Last 5 minutes, score within 5 points
    """
    
    def is_clutch_situation(self, time_remaining, score_diff):
        """
        Clutch = Last 5 minutes AND score within ±5
        """
        return time_remaining <= 5*60 and abs(score_diff) <= 5
    
    def calculate_clutch_metrics(self, possessions_df):
        """
        Calculate all metrics separately for clutch vs non-clutch.
        """
        clutch_mask = possessions_df.apply(
            lambda p: self.is_clutch_situation(
                p['time_remaining'], 
                p['score_differential']
            ), 
            axis=1
        )
        
        clutch_poss = possessions_df[clutch_mask]
        regular_poss = possessions_df[~clutch_mask]
        
        clutch_metrics = {
            'clutch_off_rtg': self.calculate_off_rtg(clutch_poss),
            'clutch_efg': self.calculate_efg(clutch_poss),
            'clutch_tov_pct': self.calculate_tov_pct(clutch_poss),
            'regular_off_rtg': self.calculate_off_rtg(regular_poss),
            'diff_clutch_vs_regular': clutch_off_rtg - regular_off_rtg
        }
        
        return clutch_metrics
```

#### **Context Splits**

```python
class ContextSplitAnalyzer:
    """
    Analyze performance in different game contexts.
    """
    
    def classify_score_margin(self, score_diff):
        """
        Classify possession by score margin.
        """
        if score_diff > 15:
            return 'blowout_leading'
        elif 5 < score_diff <= 15:
            return 'leading_close'
        elif -5 <= score_diff <= 5:
            return 'tie_game'
        elif -15 <= score_diff < -5:
            return 'trailing_close'
        else:
            return 'blowout_trailing'
    
    def classify_possession_type(self, time_to_shot):
        """
        Classify by possession pace.
        """
        if time_to_shot < 8:
            return 'transition'
        elif 8 <= time_to_shot < 15:
            return 'early_offense'
        else:
            return 'half_court'
    
    def is_garbage_time(self, time_remaining, score_diff):
        """
        Garbage time filter (Cleaning the Glass methodology).
        """
        if score_diff > 25:
            return True
        if score_diff > 20 and time_remaining < 8*60:
            return True
        if score_diff > 15 and time_remaining < 5*60:
            return True
        return False
```

**Database Tables:**

```sql
-- Clutch Performance
CREATE TABLE temporal_clutch_performance (
    clutch_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    player_id VARCHAR(50),
    
    -- Clutch Stats
    possessions_clutch INTEGER,
    possessions_non_clutch INTEGER,
    clutch_off_rtg DECIMAL(6,2),
    clutch_def_rtg DECIMAL(6,2),
    clutch_efg DECIMAL(5,3),
    clutch_tov_pct DECIMAL(5,3),
    
    -- Comparison
    clutch_vs_regular_diff DECIMAL(6,2),
    
    -- Season Aggregate
    season INTEGER NOT NULL,
    total_clutch_possessions INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_game FOREIGN KEY (game_id) REFERENCES games(game_id),
    CONSTRAINT fk_team FOREIGN KEY (team_id) REFERENCES teams(team_id),
    UNIQUE (game_id, team_id, player_id)
);

-- Context Splits
CREATE TABLE temporal_context_splits (
    split_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    
    -- Context Classification
    context_type VARCHAR(30) NOT NULL,  -- 'margin', 'time', 'transition', 'garbage'
    context_value VARCHAR(50) NOT NULL,  -- 'blowout_leading', 'Q4_clutch', etc.
    
    -- Performance in Context
    possessions INTEGER,
    off_rtg DECIMAL(6,2),
    def_rtg DECIMAL(6,2),
    net_rtg DECIMAL(6,2),
    efg DECIMAL(5,3),
    tov_pct DECIMAL(5,3),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_game FOREIGN KEY (game_id) REFERENCES games(game_id),
    CONSTRAINT fk_team FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE INDEX idx_context_type ON temporal_context_splits(context_type, context_value);
CREATE INDEX idx_clutch_player ON temporal_clutch_performance(player_id, season);
```

**Deliverables:**
- Clutch analyzer
- Context classifier
- Garbage time filter
- Database integration

---

### Sub-Phase 0.0006.5: Advanced Impact Metrics (Week 8)

**Goal:** Implement EPM, RAPM, LEBRON (optional, can defer)

#### **Plus-Minus Variants**

```python
# nba_simulator/features/temporal/advanced_metrics.py

class PlusMinusCalculator:
    """
    Calculate various plus-minus metrics.
    """
    
    def simple_plus_minus(self, player_id, game_id):
        """
        PM = Points_For - Points_Against (while player on court)
        """
        # Query possessions where player was on court
        on_court = get_possessions_with_player(player_id, game_id)
        
        points_for = on_court['points_scored'].sum()
        points_against = on_court['points_allowed'].sum()
        
        return points_for - points_against
    
    def adjusted_plus_minus(self, season_possessions):
        """
        APM using ridge regression.
        
        Solves: PM = β₁(Player₁) + β₂(Player₂) + ... + ε
        
        Controls for teammates and opponents.
        """
        from sklearn.linear_model import Ridge
        
        # Build design matrix (players on court)
        X = build_lineup_matrix(season_possessions)
        y = season_possessions['point_differential']
        
        model = Ridge(alpha=1.0)
        model.fit(X, y)
        
        player_impacts = dict(zip(player_names, model.coef_))
        return player_impacts
```

**Note:** EPM, RAPM, LEBRON are computationally intensive. Can implement in future phases if needed.

**Deliverables:**
- Plus-minus calculator
- APM/RAPM skeleton (to be completed later)
- Documentation on methodologies

---

### Sub-Phase 0.0006.6: ML Integration & Datasets (Week 8)

**Goal:** Generate ML-ready training datasets

#### **Feature Dataset Generation**

```python
# scripts/0_00012/generate_training_datasets.py

class MLDatasetGenerator:
    """
    Generate ML training datasets from temporal features.
    """
    
    def generate_possession_features(self, season):
        """
        Generate feature matrix for ML models.
        
        Features (100+ columns):
        - Current possession stats
        - Rolling windows (L5, L10, L20)
        - Four Factors
        - Momentum scores
        - Hot hand indicators
        - Context variables
        - Team quality indicators
        """
        query = """
        SELECT
            tps.*,
            trf.rolling_off_rtg_l5,
            trf.rolling_off_rtg_l10,
            trf.rolling_efg_l5,
            trf.rolling_tov_pct_l5,
            tmt.momentum_score,
            tmt.hot_hand_score,
            tcp.clutch_vs_regular_diff,
            tcs.off_rtg as context_off_rtg
        FROM temporal_possession_stats tps
        LEFT JOIN temporal_rolling_features trf 
            ON tps.possession_id = trf.possession_id
        LEFT JOIN temporal_momentum_tracking tmt
            ON tps.possession_id = tmt.possession_id
        LEFT JOIN temporal_clutch_performance tcp
            ON tps.game_id = tcp.game_id AND tps.team_id = tcp.team_id
        LEFT JOIN temporal_context_splits tcs
            ON tps.game_id = tcs.game_id AND tps.team_id = tcs.team_id
        WHERE tps.season = :season
        """
        
        df = pd.read_sql(query, engine, params={'season': season})
        return df
    
    def create_train_val_test_split(self, df, splits=(0.7, 0.15, 0.15)):
        """
        Split into train/val/test sets.
        
        Important: Time-based split (not random)
        - Train: First 70% of season
        - Val: Next 15%
        - Test: Last 15%
        """
        n = len(df)
        train_end = int(n * splits[0])
        val_end = int(n * (splits[0] + splits[1]))
        
        train = df.iloc[:train_end]
        val = df.iloc[train_end:val_end]
        test = df.iloc[val_end:]
        
        return train, val, test
```

**Output Datasets:**

```
ml_features/
├── train/
│   ├── 2020_train.parquet
│   ├── 2021_train.parquet
│   ├── 2022_train.parquet
│   ├── 2023_train.parquet
│   └── 2024_train.parquet
├── val/
│   └── ...
├── test/
│   └── ...
└── feature_catalog.yaml  # Feature descriptions
```

**Deliverables:**
- ML dataset generator
- Feature catalog documentation
- Train/val/test splits
- Integration with Phase 5 (ML Pipeline)

---

## 📁 Complete File Organization

### Directory Structure

```
nba-simulator-aws/
│
├── docs/
│   └── phases/
│       └── phase_0/
│           ├── 0.0001_initial_data_collection/  (COMPLETE)
│           ├── 0.00011_possession_extraction/    ⭐ NEW
│           │   ├── README.md
│           │   ├── ARCHITECTURE.md
│           │   ├── VALIDATION.md
│           │   └── EXAMPLES.md
│           ├── 0.00012_temporal_features/        ⭐ NEW
│           │   ├── README.md
│           │   ├── FOUR_FACTORS.md
│           │   ├── ROLLING_WINDOWS.md
│           │   ├── MOMENTUM_TRACKING.md
│           │   ├── CLUTCH_PERFORMANCE.md
│           │   └── ML_INTEGRATION.md
│           └── 0.0002_hoopr_data_collection/  (COMPLETE)
│
├── scripts/
│   ├── 0_00011/                                 ⭐ NEW
│   │   ├── __init__.py
│   │   ├── extract_possessions.py
│   │   ├── validate_possessions.py
│   │   ├── load_to_database.py
│   │   └── run_pipeline.py
│   ├── 0_00012/                                 ⭐ NEW
│   │   ├── __init__.py
│   │   ├── calculate_four_factors.py
│   │   ├── calculate_rolling_features.py
│   │   ├── calculate_momentum.py
│   │   ├── calculate_clutch.py
│   │   ├── generate_training_datasets.py
│   │   └── run_pipeline.py
│   └── ...
│
├── nba_simulator/                               # Refactored Package
│   ├── etl/
│   │   └── transformers/
│   │       ├── possession_transformer.py        ⭐ NEW
│   │       └── temporal_feature_transformer.py  ⭐ NEW
│   │
│   ├── features/                                ⭐ NEW MODULE
│   │   ├── __init__.py
│   │   ├── possession/
│   │   │   ├── __init__.py
│   │   │   ├── extractor.py
│   │   │   └── validator.py
│   │   └── temporal/
│   │       ├── __init__.py
│   │       ├── rolling_windows.py
│   │       ├── kenpom_metrics.py
│   │       ├── momentum_tracking.py
│   │       ├── clutch_performance.py
│   │       └── advanced_metrics.py
│   │
│   └── database/
│       └── schemas/
│           ├── temporal_possession_stats.sql    ⭐ NEW
│           ├── temporal_rolling_features.sql    ⭐ NEW
│           ├── temporal_momentum_tracking.sql   ⭐ NEW
│           ├── temporal_clutch_performance.sql  ⭐ NEW
│           └── temporal_context_splits.sql      ⭐ NEW
│
└── tests/
    └── phases/
        └── phase_0/
            ├── test_0_00011_possession_extraction.py  ⭐ NEW
            └── test_0_00012_temporal_features.py       ⭐ NEW
```

---

## 📊 Complete Database Schema Summary

### 6 New Tables

1. **temporal_possession_stats** - 2-3M possessions with full context
2. **temporal_rolling_features** - 10-15M rolling calculations (multiple windows)
3. **temporal_momentum_tracking** - Real-time momentum scores
4. **temporal_clutch_performance** - Clutch situation analysis
5. **temporal_context_splits** - Performance by game context
6. **temporal_advanced_metrics** - EPM, RAPM, LEBRON (future)

**Total Expected Storage:**
- temporal_possession_stats: ~500 MB
- temporal_rolling_features: ~2-3 GB
- temporal_momentum_tracking: ~200 MB
- temporal_clutch_performance: ~50 MB
- temporal_context_splits: ~100 MB
- **Total: ~3-4 GB**

---

## 📅 8-Week Implementation Timeline

### **Weeks 1-2: Phase 0.00011 (Possession Extraction)**

| Week | Days | Task | Deliverable |
|------|------|------|-------------|
| 1 | 1-2 | Possession detection algorithm | Algorithm + unit tests |
| 1 | 3-4 | Possession validation | Validation framework |
| 1 | 5-7 | Database schema & loading | Schema SQL + ETL script |
| 2 | 8-10 | Integration with temporal_events | Link tables |
| 2 | 11-14 | Full dataset processing | 2-3M possessions loaded |

**Checkpoint:** temporal_possession_stats table populated, validated

---

### **Weeks 3-8: Phase 0.00012 (Temporal Features)**

| Week | Task | Deliverable |
|------|------|-------------|
| 3 | Rolling window infrastructure | Efficient calculation |
| 4 | Four Factors implementation | eFG%, TOV%, ORB%, FTR |
| 5 | Tempo-free stats | OffRtg, DefRtg, NetRtg, Tempo |
| 6 | Momentum & hot hand | Momentum scores, streak detection |
| 7 | Clutch & context | Clutch metrics, garbage time filter |
| 8 | ML integration | Training datasets, feature catalog |

**Checkpoint:** All 6 tables populated, ML datasets generated

---

## ✅ Success Criteria

### Phase 0.00011 Complete When:
- [ ] temporal_possession_stats table has 2-3M rows
- [ ] Possession counts within 3 of Dean Oliver estimates (95% of games)
- [ ] Box score stats match source data (100%)
- [ ] Temporal ordering is correct
- [ ] 95%+ test coverage
- [ ] Documentation complete

### Phase 0.0006 Complete When:
- [ ] All 6 database tables populated
- [ ] Four Factors match NBA.com (correlation > 0.99)
- [ ] Efficiency metrics match NBA.com (±0.5 points)
- [ ] Rolling windows calculate correctly
- [ ] Hot hand detection validated on known cases
- [ ] Clutch metrics calculated
- [ ] ML training datasets generated
- [ ] 95%+ test coverage
- [ ] Documentation complete

---

## 🚀 Quick Start Commands

### Phase 0.00011: Possession Extraction

```bash
# Create directories
mkdir -p docs/phases/phase_0/0.00011_possession_extraction
mkdir -p scripts/0_00011
mkdir -p nba_simulator/features/possession

# Extract possessions
python scripts/0_00011/extract_possessions.py \
    --source temporal_events \
    --output temporal_possession_stats \
    --batch-size 1000 \
    --validate

# Validate
python scripts/0_00011/validate_possessions.py \
    --compare-to-oliver
```

### Phase 0.00012: Temporal Features

```bash
# Create directories
mkdir -p docs/phases/phase_0/0.00012_temporal_features
mkdir -p scripts/0_00012
mkdir -p nba_simulator/features/temporal

# Calculate Four Factors
python scripts/0_00012/calculate_four_factors.py \
    --source temporal_possession_stats \
    --output temporal_rolling_features

# Calculate Rolling Windows
python scripts/0_00012/calculate_rolling_features.py \
    --windows 5,10,20,50 \
    --metrics OffRtg,DefRtg,eFG,TOV

# Generate ML Datasets
python scripts/0_0006/generate_training_datasets.py \
    --output ml_features/ \
    --split train:0.7,val:0.15,test:0.15
```

---

## 💰 Cost Analysis

### Free Resources (What We're Using)
- ✅ Dean Oliver formulas (public)
- ✅ KenPom methodology (public)
- ✅ Four Factors (published 2004)
- ✅ Tempo-free stats (widely documented)
- ✅ Our own temporal_events data (14.1M records)

**Total Cost: $0** 🎉

### Optional Paid Resources (For Reference Only)
- ⚠️ Cleaning the Glass ($10/mo) - Methodology reference
- ⚠️ PBPStats ($10/mo) - We can calculate this ourselves
- ⚠️ BBall Index ($5/mo) - LEBRON is nice-to-have

**We don't need these!** We're calculating everything ourselves.

---

## 📚 References & Methodologies

### Published Formulas (Free)
1. **Dean Oliver** - "Basketball on Paper" (2004)
   - Four Factors
   - Possession estimation
   - Tempo-free statistics
   
2. **KenPom.com** - Publicly documented methodology
   - Adjusted Efficiency
   - Strength of schedule
   
3. **Dunks & Threes** - EPM methodology (public blog posts)
   
4. **Cleaning the Glass** - Garbage time filtering (documented)

### Data Sources (Already Have)
1. Basketball-Reference - Phase 0.0004
2. NBA.com Stats - NBA API extractor
3. ESPN - Phase 0.0001 (14.1M events)
4. hoopR - Phase 0.0002
5. temporal_events table - Our gold mine

---

## 🎯 Integration with Existing System

### Phase 0 Update Required

Update `PHASE_0_INDEX.md`:

```markdown
| **0.0005** | [Possession Extraction](0.0005_possession_extraction/README.md) | ⏸️ PENDING | ⭐ CRITICAL | TBD | Extract 2-3M possessions from 14.1M events (Dean Oliver methodology) |
| **0.0006** | [Temporal Features](0.0006_temporal_features/README.md) | ⏸️ PENDING | ⭐ CRITICAL | TBD | Calculate 100+ KenPom metrics, rolling windows, momentum (8 weeks) |
```

### Package Integration

Add to `nba_simulator/`:
```python
from nba_simulator.features.possession import PossessionExtractor
from nba_simulator.features.temporal import (
    FourFactors,
    TempoFreeStats,
    RollingWindowCalculator,
    MomentumTracker,
    HotHandDetector,
    ClutchAnalyzer
)
```

### Phase 5 (ML) Integration

Phase 5 will consume the datasets generated by 0.0006:
```python
from nba_simulator.features.temporal import MLDatasetGenerator

# Load ML-ready features
train_df = pd.read_parquet('ml_features/train/2024_train.parquet')
```

---

## 🎉 What This Enables

### 1. Professional-Grade Analytics
- Four Factors analysis (Dean Oliver)
- Tempo-free statistics (KenPom)
- Adjusted efficiency ratings
- Advanced impact metrics

### 2. Unique Temporal Features
**No commercial site offers:**
- Rolling 5/10/20 possession windows
- Real-time momentum tracking
- Hot hand detection algorithms
- Possession-level context analysis

### 3. ML-Ready Datasets
- 100+ features per possession
- Temporal ordering preserved
- Train/val/test splits
- Feature catalog documentation

### 4. Simulation Foundation
- Context-aware predictions
- Momentum-based adjustments
- Clutch performance modeling
- Era-neutral comparisons

---

## 🚨 Critical Reminders

### What We're NOT Doing
- ❌ Scraping external analytics sites
- ❌ Paying for subscriptions
- ❌ Reproducing proprietary metrics exactly
- ❌ Using undocumented methodologies

### What We ARE Doing
- ✅ Using public formulas (Dean Oliver, KenPom)
- ✅ Calculating from our own data
- ✅ Building unique temporal features
- ✅ Creating ML-ready datasets
- ✅ Zero cost implementation

### Key Principles
1. **Calculate, don't scrape** - We have better data
2. **Public methodologies only** - Respect IP
3. **Test thoroughly** - Validate against NBA.com
4. **Document everything** - Future maintainability
5. **Temporal is our advantage** - Rolling windows unique

---

## 📞 Next Steps

**Ready to begin?** Here's what to do:

1. **Review this guide** - Understand full scope
2. **Update Phase 0 index** - Add 0.00011 and 0.00012
3. **Create directory structure** - Folders for both phases
4. **Start with 0.00011** - Possession extraction first
5. **Progress to 0.00012** - Features second

**Questions?**
- Check references (Dean Oliver book, KenPom site)
- Review database schemas
- Examine code examples

**Let's build professional NBA analytics!** 🏀

---

**Document Version:** 1.0  
**Status:** ✅ READY FOR IMPLEMENTATION  
**Estimated Completion:** 8 weeks from start  
**Expected Output:** 3-4 GB of advanced analytics data, 100+ ML features

---

**Generated:** November 5, 2025  
**Author:** NBA Simulator AWS Team  
**Reference Chat:** KenPom Basketball Statistics Implementation Strategy  
**Phase Placement:** Phase 0.00011-0.00012 (between 0.0001 and 0.0002)
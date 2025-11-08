# Sub-Phase 0.0006: Temporal Feature Engineering

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ⏸️ PENDING
**Priority:** ⭐ CRITICAL
**Implementation ID:** `temporal_data_transformation_0.0006`
**Started:** TBD
**Completed:** TBD

---

## Overview

Calculates 100+ advanced basketball analytics features from possession-level data, including KenPom-style tempo-free metrics, Dean Oliver's Four Factors, and unique rolling temporal features. This phase transforms possessions into ML-ready feature datasets for game simulation and prediction.

**Data Foundation:**
- **Input:** `temporal_possession_stats` table (2-3M possessions from Phase 0.0005)
- **Output:** 6 new feature tables (~3.8 GB total)
- **Methodologies:** KenPom tempo-free stats, Dean Oliver Four Factors, custom temporal features

**Key Capabilities:**
- Calculates 100+ advanced metrics (AdjO, AdjD, tempo, eFG%, TO%, OR%, FTR)
- Creates rolling window features (5/10/20-game windows)
- Generates momentum indicators (hot streaks, cold streaks)
- Produces ML-ready datasets with temporal context

---

## Capabilities

### Core Feature Categories

#### 1. **KenPom Tempo-Free Statistics**

**Offensive Ratings:**
- **AdjO (Adjusted Offensive Efficiency):** Points per 100 possessions, adjusted for opponent strength
- **eFG% (Effective Field Goal Percentage):** (FGM + 0.5 × 3PM) / FGA
- **TO% (Turnover Percentage):** Turnovers per 100 possessions
- **OR% (Offensive Rebound Percentage):** ORB / (ORB + Opp DRB)
- **FTR (Free Throw Rate):** FTA / FGA

**Defensive Ratings:**
- **AdjD (Adjusted Defensive Efficiency):** Opponent points per 100 possessions
- **Opp eFG%:** Opponent effective field goal percentage
- **Opp TO%:** Opponent turnover percentage
- **DR% (Defensive Rebound Percentage):** DRB / (DRB + Opp ORB)
- **Opp FTR:** Opponent free throw rate

**Tempo Metrics:**
- **Tempo:** Possessions per 40 minutes
- **Pace Factor:** Team possessions per game
- **Average Possession Length:** Seconds per possession

#### 2. **Dean Oliver's Four Factors**

**Offensive Four Factors:**
1. **Shooting (eFG%):** 40% weight
2. **Turnovers (TO%):** 25% weight
3. **Rebounding (OR%):** 20% weight
4. **Free Throws (FTR):** 15% weight

**Defensive Four Factors:**
1. **Opponent Shooting:** 40% weight
2. **Forcing Turnovers:** 25% weight
3. **Defensive Rebounding:** 20% weight
4. **Limiting Free Throws:** 15% weight

**Four Factors Score:**
```
FF_Score = 0.40 × eFG% + 0.25 × TO% + 0.20 × OR% + 0.15 × FTR
```

#### 3. **Rolling Window Features**

**5-Game Windows:**
- Recent form indicators
- Short-term momentum
- Lineup-specific metrics

**10-Game Windows:**
- Medium-term trends
- Matchup-specific patterns
- Player development tracking

**20-Game Windows:**
- Season-long trends
- Regression to mean analysis
- Sustainable performance metrics

**Calculated for each window:**
- Mean, median, std dev
- Min/max bounds
- Trend direction (improving/declining)
- Volatility metrics

#### 4. **Temporal Context Features**

**Game Context:**
- Days rest (0-10+)
- Back-to-back indicator
- Time zone travel distance
- Home/away streaks
- Win/loss streaks

**Season Context:**
- Days since season start
- Games remaining in season
- Playoff positioning
- Elimination scenarios

**Historical Context:**
- Head-to-head record
- Historical performance vs opponent
- Venue-specific performance
- Month/day-of-week effects

#### 5. **Momentum & Streak Features**

**Hot/Cold Indicators:**
- Shooting hot streaks (3+ games >45% FG)
- Scoring surges (3+ games >110 PPG)
- Defensive lockdowns (3+ games <100 PPG allowed)
- Turnover reduction streaks

**Momentum Metrics:**
- Point differential trend (last 5 games)
- Winning/losing momentum
- Fourth quarter performance trend
- Clutch performance trend

#### 6. **Situational Features**

**Score Context:**
- Leading performance (when ahead by 10+)
- Trailing performance (when behind by 10+)
- Close game performance (within 5 points)
- Blowout tendencies

**Time Context:**
- First quarter stats
- Second quarter stats
- Third quarter stats
- Fourth quarter stats
- Overtime stats
- Clutch time stats (last 5 minutes, close game)

#### 7. **Advanced Analytics**

**Shot Quality:**
- Expected points per possession
- Shot selection quality
- Three-point attempt rate
- Paint points per possession

**Pace-Adjusted Stats:**
- True shooting percentage (TS%)
- Usage rate (USG%)
- Player efficiency rating (PER)
- Win shares per 48 minutes

---

## Quick Start

### Basic Usage

```bash
# Calculate features for entire database
cd /Users/ryanranft/nba-simulator-aws
python scripts/workflows/temporal_features_cli.py

# Calculate for specific season
python scripts/workflows/temporal_features_cli.py --season 2024

# Calculate for specific team
python scripts/workflows/temporal_features_cli.py --team-id 1610612738

# Dry run (validation only)
python scripts/workflows/temporal_features_cli.py --dry-run --validate

# Generate ML dataset
python scripts/workflows/temporal_features_cli.py --export-ml-dataset

# Calculate rolling windows only
python scripts/workflows/temporal_features_cli.py --features rolling_windows
```

### Programmatic Usage

```python
from docs.phases.phase_0.temporal_features.temporal_features import TemporalFeaturesEngine
from docs.phases.phase_0.temporal_features.kenpom_metrics import KenPomCalculator

# Load configuration
config = TemporalFeaturesConfig.from_yaml("config/default_config.yaml")

# Create feature engine
engine = TemporalFeaturesEngine(config=config)

# Initialize
if engine.initialize():
    # Calculate KenPom metrics for a team-season
    kenpom_calc = KenPomCalculator(engine.db_connection)
    metrics = kenpom_calc.calculate_season_metrics(
        team_id=1610612738,  # Boston Celtics
        season=2024
    )
    
    print(f"AdjO: {metrics['adj_offensive_efficiency']:.2f}")
    print(f"AdjD: {metrics['adj_defensive_efficiency']:.2f}")
    print(f"Tempo: {metrics['tempo']:.2f}")
    
    # Calculate rolling windows
    rolling_features = engine.calculate_rolling_windows(
        team_id=1610612738,
        season=2024,
        windows=[5, 10, 20]
    )
    
    # Export ML dataset
    ml_dataset = engine.export_ml_dataset(
        seasons=[2023, 2024],
        include_features=[
            'kenpom_metrics',
            'four_factors',
            'rolling_windows',
            'momentum_indicators'
        ]
    )
    
    ml_dataset.to_csv('data/ml_features/temporal_features_2024.csv')
    
    # Shutdown
    engine.shutdown()
```

---

## Architecture

### Data Flow

```
temporal_possession_stats (2-3M possessions)
    ↓
[1] Aggregation to Game Level
    - Sum possessions per game
    - Calculate shooting percentages
    - Compute rebound percentages
    ↓
[2] KenPom Tempo-Free Calculations
    - Points per 100 possessions
    - Adjust for opponent strength
    - Calculate tempo metrics
    ↓
[3] Dean Oliver Four Factors
    - Weight factors (40/25/20/15)
    - Calculate offensive score
    - Calculate defensive score
    ↓
[4] Rolling Window Features
    - 5-game windows (recent form)
    - 10-game windows (trends)
    - 20-game windows (season baseline)
    ↓
[5] Temporal Context Addition
    - Days rest, travel distance
    - Streaks, momentum indicators
    - Historical matchup data
    ↓
[6] ML Dataset Export
    - Feature engineering complete
    - Normalization/scaling
    - Train/validation/test splits
    ↓
6 Feature Tables (~3.8 GB)
```

### Feature Calculation Pipeline

```
START
  ↓
Initialize Engine
  ↓
Load Possession Data → [temporal_possession_stats]
  ↓
┌─────────────────────────────────────┐
│ Game-Level Aggregation               │
│ - Sum stats per game                 │
│ - Calculate percentages              │
│ → temporal_team_game_stats          │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ Season-Level Aggregation             │
│ - Average across all games           │
│ - Calculate season totals            │
│ → temporal_team_season_stats        │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ KenPom Calculations                  │
│ - AdjO, AdjD (tempo-free)           │
│ - Strength of schedule adjustment    │
│ → temporal_kenpom_metrics           │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ Four Factors Calculations            │
│ - eFG%, TO%, OR%, FTR               │
│ - Weighted scores                    │
│ → temporal_four_factors             │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ Rolling Windows                      │
│ - 5/10/20 game windows              │
│ - Trend calculations                 │
│ → temporal_rolling_features         │
└─────────────────────────────────────┘
  ↓
┌─────────────────────────────────────┐
│ Context & Momentum                   │
│ - Streaks, rest days                │
│ - Matchup history                    │
│ → temporal_context_features         │
└─────────────────────────────────────┘
  ↓
Export ML Datasets
  ↓
Report DIMS Metrics
  ↓
END
```

### Database Schema

**New Tables (6 total):**

#### 1. `temporal_team_game_stats`
Game-level aggregated statistics.

```sql
CREATE TABLE temporal_team_game_stats (
    stat_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    game_date DATE NOT NULL,
    
    -- Basic Stats
    possessions INTEGER,
    points INTEGER,
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    three_pointers_made INTEGER,
    three_pointers_attempted INTEGER,
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    
    -- Rebound Stats
    offensive_rebounds INTEGER,
    defensive_rebounds INTEGER,
    total_rebounds INTEGER,
    
    -- Other Stats
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    personal_fouls INTEGER,
    
    -- Percentages
    field_goal_pct NUMERIC(5,3),
    three_point_pct NUMERIC(5,3),
    free_throw_pct NUMERIC(5,3),
    effective_fg_pct NUMERIC(5,3),
    true_shooting_pct NUMERIC(5,3),
    
    -- Context
    is_home BOOLEAN,
    opponent_team_id INTEGER,
    days_rest INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(game_id, team_id)
);

CREATE INDEX idx_team_game_team_season ON temporal_team_game_stats(team_id, season);
CREATE INDEX idx_team_game_date ON temporal_team_game_stats(game_date);
```

**Size:** ~150 MB

#### 2. `temporal_team_season_stats`
Season-level aggregated statistics.

```sql
CREATE TABLE temporal_team_season_stats (
    stat_id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    
    -- Games Played
    games_played INTEGER,
    wins INTEGER,
    losses INTEGER,
    
    -- Aggregate Stats (season totals)
    total_possessions INTEGER,
    total_points INTEGER,
    total_fgm INTEGER,
    total_fga INTEGER,
    total_3pm INTEGER,
    total_3pa INTEGER,
    -- ... (all stats from game level)
    
    -- Season Averages (per game)
    avg_possessions NUMERIC(6,2),
    avg_points NUMERIC(6,2),
    avg_fgm NUMERIC(6,2),
    -- ... (all averages)
    
    -- Season Percentages
    season_fg_pct NUMERIC(5,3),
    season_3p_pct NUMERIC(5,3),
    season_ft_pct NUMERIC(5,3),
    season_efg_pct NUMERIC(5,3),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(team_id, season)
);
```

**Size:** ~50 MB

#### 3. `temporal_kenpom_metrics`
KenPom-style tempo-free statistics.

```sql
CREATE TABLE temporal_kenpom_metrics (
    metric_id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    as_of_date DATE,  -- NULL for full season, or specific date for rolling
    
    -- Offensive Metrics
    adj_offensive_efficiency NUMERIC(7,3),  -- AdjO
    offensive_efficiency_raw NUMERIC(7,3),  -- Raw O (unadjusted)
    effective_fg_pct NUMERIC(5,3),
    turnover_pct NUMERIC(5,3),
    offensive_rebound_pct NUMERIC(5,3),
    free_throw_rate NUMERIC(5,3),
    
    -- Defensive Metrics
    adj_defensive_efficiency NUMERIC(7,3),  -- AdjD
    defensive_efficiency_raw NUMERIC(7,3),  -- Raw D (unadjusted)
    opp_effective_fg_pct NUMERIC(5,3),
    opp_turnover_pct NUMERIC(5,3),
    defensive_rebound_pct NUMERIC(5,3),
    opp_free_throw_rate NUMERIC(5,3),
    
    -- Tempo Metrics
    tempo NUMERIC(6,2),                     -- Possessions per 40 min
    pace_factor NUMERIC(6,2),               -- Possessions per game
    avg_possession_length NUMERIC(5,2),     -- Seconds
    
    -- Strength Adjustments
    strength_of_schedule NUMERIC(7,3),
    opponent_adj_o_avg NUMERIC(7,3),
    opponent_adj_d_avg NUMERIC(7,3),
    
    -- Net Rating
    net_rating NUMERIC(7,3),                -- AdjO - AdjD
    
    -- Metadata
    games_included INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(team_id, season, as_of_date)
);

CREATE INDEX idx_kenpom_team_season ON temporal_kenpom_metrics(team_id, season);
CREATE INDEX idx_kenpom_date ON temporal_kenpom_metrics(as_of_date);
```

**Size:** ~500 MB

#### 4. `temporal_four_factors`
Dean Oliver's Four Factors.

```sql
CREATE TABLE temporal_four_factors (
    factor_id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    as_of_date DATE,
    
    -- Offensive Four Factors
    offensive_efg NUMERIC(5,3),             -- Shooting (40% weight)
    offensive_to_pct NUMERIC(5,3),          -- Turnovers (25% weight)
    offensive_orb_pct NUMERIC(5,3),         -- Rebounding (20% weight)
    offensive_ftr NUMERIC(5,3),             -- Free Throws (15% weight)
    offensive_ff_score NUMERIC(7,3),        -- Weighted sum
    
    -- Defensive Four Factors
    defensive_efg NUMERIC(5,3),             -- Opp Shooting
    defensive_to_pct NUMERIC(5,3),          -- Force Turnovers
    defensive_drb_pct NUMERIC(5,3),         -- Def Rebounding
    defensive_ftr NUMERIC(5,3),             -- Limit FTs
    defensive_ff_score NUMERIC(7,3),        -- Weighted sum
    
    -- Net Four Factors
    net_ff_score NUMERIC(7,3),              -- Off FF - Def FF
    
    -- Metadata
    games_included INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(team_id, season, as_of_date)
);
```

**Size:** ~300 MB

#### 5. `temporal_rolling_features`
Rolling window features (5/10/20 games).

```sql
CREATE TABLE temporal_rolling_features (
    feature_id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    as_of_date DATE NOT NULL,
    window_size INTEGER NOT NULL,           -- 5, 10, or 20
    
    -- Rolling Averages
    avg_points NUMERIC(6,2),
    avg_points_allowed NUMERIC(6,2),
    avg_point_differential NUMERIC(6,2),
    avg_possessions NUMERIC(6,2),
    avg_offensive_efficiency NUMERIC(7,3),
    avg_defensive_efficiency NUMERIC(7,3),
    
    -- Rolling Shooting
    avg_fg_pct NUMERIC(5,3),
    avg_3p_pct NUMERIC(5,3),
    avg_efg_pct NUMERIC(5,3),
    
    -- Rolling Four Factors
    avg_to_pct NUMERIC(5,3),
    avg_orb_pct NUMERIC(5,3),
    avg_ftr NUMERIC(5,3),
    
    -- Volatility Metrics
    std_point_differential NUMERIC(6,2),
    std_offensive_efficiency NUMERIC(7,3),
    min_points INTEGER,
    max_points INTEGER,
    
    -- Trend Indicators
    trend_direction VARCHAR(20),            -- improving, declining, stable
    trend_strength NUMERIC(5,3),            -- -1 to +1
    
    -- Win/Loss in Window
    wins_in_window INTEGER,
    losses_in_window INTEGER,
    win_pct_in_window NUMERIC(5,3),
    
    -- Metadata
    games_included INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(team_id, season, as_of_date, window_size)
);

CREATE INDEX idx_rolling_team_date ON temporal_rolling_features(team_id, as_of_date);
CREATE INDEX idx_rolling_window ON temporal_rolling_features(window_size);
```

**Size:** ~2 GB (largest table due to daily updates)

#### 6. `temporal_context_features`
Contextual and situational features.

```sql
CREATE TABLE temporal_context_features (
    context_id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    team_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    game_date DATE NOT NULL,
    
    -- Rest Context
    days_rest INTEGER,
    is_back_to_back BOOLEAN,
    is_3_in_4_nights BOOLEAN,
    is_4_in_5_nights BOOLEAN,
    
    -- Travel Context
    travel_distance_miles INTEGER,
    time_zone_change INTEGER,
    is_long_road_trip BOOLEAN,            -- 4+ game road trip
    
    -- Streak Context
    current_win_streak INTEGER,
    current_loss_streak INTEGER,
    home_win_streak INTEGER,
    away_win_streak INTEGER,
    
    -- Season Context
    days_since_season_start INTEGER,
    games_remaining INTEGER,
    is_playoff_race BOOLEAN,
    playoff_position INTEGER,
    
    -- Matchup Context
    head_to_head_wins_season INTEGER,
    head_to_head_losses_season INTEGER,
    head_to_head_wins_alltime INTEGER,
    avg_point_diff_vs_opponent NUMERIC(6,2),
    
    -- Momentum Indicators
    is_hot_shooting BOOLEAN,               -- 3+ games >45% FG
    is_cold_shooting BOOLEAN,              -- 3+ games <40% FG
    is_scoring_surge BOOLEAN,              -- 3+ games >110 PPG
    is_defensive_lockdown BOOLEAN,         -- 3+ games <100 PPG allowed
    
    -- Created
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(game_id, team_id)
);

CREATE INDEX idx_context_team_season ON temporal_context_features(team_id, season);
CREATE INDEX idx_context_date ON temporal_context_features(game_date);
```

**Size:** ~800 MB

**Total Database Growth:** ~3.8 GB across 6 tables

---

## Configuration Schema

```yaml
# config/default_config.yaml

project_dir: /Users/ryanranft/nba-simulator-aws
log_dir: logs/temporal_features
reports_dir: reports/temporal_features
ml_export_dir: data/ml_features

database:
  host: localhost
  port: 5432
  dbname: nba_data
  user: nba_admin

# Source tables
source_tables:
  possessions: temporal_possession_stats
  games: games
  teams: teams

# Target tables (will be created)
target_tables:
  team_game_stats: temporal_team_game_stats
  team_season_stats: temporal_team_season_stats
  kenpom_metrics: temporal_kenpom_metrics
  four_factors: temporal_four_factors
  rolling_features: temporal_rolling_features
  context_features: temporal_context_features

# KenPom calculations
kenpom:
  # Adjustment methodology
  adjustment_method: iterative        # iterative or regression
  adjustment_iterations: 10
  
  # Tempo normalization
  tempo_baseline: 100.0               # Possessions per 40 min
  
  # Strength of schedule
  calculate_sos: true
  sos_weight: 0.5

# Four Factors weights
four_factors:
  shooting_weight: 0.40
  turnover_weight: 0.25
  rebounding_weight: 0.20
  free_throw_weight: 0.15

# Rolling windows
rolling_windows:
  enabled: true
  window_sizes: [5, 10, 20]
  
  # Update frequency
  update_daily: true
  recalculate_historical: false       # Set true for full rebuild
  
  # Minimum games required
  min_games_for_window:
    5: 3                               # Need 3+ games for 5-game window
    10: 6
    20: 12

# Context features
context:
  # Rest days
  track_rest_days: true
  max_rest_days: 10
  
  # Travel
  calculate_travel_distance: true
  time_zone_threshold: 2               # Flag if 2+ time zones
  
  # Streaks
  track_streaks: true
  min_streak_length: 3
  
  # Momentum
  momentum_indicators:
    hot_shooting_threshold: 0.45       # >45% FG for 3 games
    cold_shooting_threshold: 0.40      # <40% FG for 3 games
    scoring_surge_threshold: 110       # >110 PPG for 3 games
    defensive_lockdown_threshold: 100  # <100 PPG allowed for 3 games

# ML export
ml_export:
  enabled: true
  
  # Feature groups to include
  include_features:
    - kenpom_metrics
    - four_factors
    - rolling_windows
    - context_features
    - momentum_indicators
  
  # Data splits
  train_test_split: 0.80
  validation_split: 0.10
  
  # Normalization
  normalize: true
  normalization_method: standard        # standard, minmax, robust
  
  # File formats
  export_formats:
    - csv
    - parquet
    - json

# Processing
processing:
  batch_size: 100                      # Games per batch
  parallel_teams: 8
  max_retries: 3
  retry_delay_seconds: 5

# DIMS integration
dims:
  enabled: true
  report_metrics: true
  metrics:
    - features_calculated
    - games_processed
    - tables_updated
    - processing_duration
    - ml_dataset_size
    - avg_features_per_game

# Performance
performance:
  connection_pool_size: 20
  use_prepared_statements: true
  enable_query_cache: true
  verify_indexes_on_startup: true
```

---

## Implementation Files

| File | Purpose | Lines | Tests |
|------|---------|-------|-------|
| `temporal_features.py` | Main feature engine | ~1200 | 100% |
| `kenpom_metrics.py` | KenPom calculations | ~600 | 100% |
| `four_factors.py` | Four Factors calculations | ~400 | 100% |
| `rolling_windows.py` | Rolling window features | ~500 | 100% |
| `context_features.py` | Context & momentum | ~600 | 100% |
| `ml_exporter.py` | ML dataset export | ~400 | 100% |
| `config/default_config.yaml` | Configuration | ~300 | N/A |
| `test_temporal_features.py` | Tests | ~1000 | 150 tests |
| CLI: `scripts/workflows/temporal_features_cli.py` | CLI | ~300 | N/A |

**Total Production Code:** ~4,000 lines  
**Total Test Code:** ~1,000 lines  
**Test Coverage Target:** 95%+

---

## Testing

### Run Tests

```bash
# Run all temporal feature tests
pytest tests/phases/phase_0/test_0_0006_temporal_features.py -v

# Run with coverage
pytest tests/phases/phase_0/test_0_0006_temporal_features.py \
    --cov=docs.phases.phase_0.temporal_features \
    --cov-report=html
```

---

## DIMS Integration

### Metrics Reported

| Metric | Description |
|--------|-------------|
| `features_calculated` | Total features calculated |
| `games_processed` | Games analyzed |
| `kenpom_calculations` | KenPom metrics calculated |
| `ml_dataset_size_mb` | ML dataset size |

---

## Implementation Timeline

**Week 3-4:** KenPom & Four Factors (10 days)  
**Week 5:** Rolling windows & context (5 days)  
**Week 6:** Testing & ML export (5 days)  

**Total:** 20 working days (4 weeks)

---

## Success Criteria

### Must Have
- ✅ KenPom metrics for all teams/seasons
- ✅ Four Factors for all teams/seasons
- ✅ Rolling windows (5/10/20)
- ✅ ML dataset export
- ✅ All 150 tests passing

---

## Navigation

**Parent:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)  
**Prerequisites:** [0.0005: Possession Extraction](../0.0005_possession_extraction/README.md)  
**Enables:** [Phase 2: Feature Engineering](../../phase_2/PHASE_2_INDEX.md)

---

**Last Updated:** November 5, 2025  
**Version:** 1.0.0  
**Estimated Effort:** 4 weeks (160 hours)  
**Estimated Cost:** $0.50/month storage

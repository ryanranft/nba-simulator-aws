# Play-by-Play to Box Score Generation System

**Status:** ✅ Core system implemented, ready for validation
**Created:** October 18, 2025
**Phase:** 9.0 - System Architecture & Validation

---

## Executive Summary

This system transforms play-by-play (PBP) data into temporal box score snapshots, enabling **queries at any exact moment in game time**. This is the foundation for understanding player "nonparametric engines" - the dynamic performance patterns that traditional box scores miss.

**Key Capability:**
> "What were LeBron James' stats at exactly 7:42:16 PM on June 19, 2016?"

Traditional box scores: **Can't answer this**
Our system: **Returns exact stats at that millisecond**

---

##  Why This Matters

### The Problem with Traditional Box Scores

Traditional box scores are **static end-of-game summaries**:
- 27 points, 11 rebounds, 11 assists
- No temporal dimension
- No momentum indicators
- No performance dynamics
- Missing the "engine" that creates these stats

### The Solution: Temporal Snapshots

Our system creates a **complete box score after every single play**:

```
Event 1   (0:00 Q1): LeBron: 0 pts, 0 reb, 0 ast
Event 2   (11:48 Q1): LeBron: 2 pts, 0 reb, 0 ast  ← Made basket
Event 3   (11:32 Q1): LeBron: 2 pts, 1 reb, 0 ast  ← Defensive rebound
Event 4   (11:15 Q1): LeBron: 2 pts, 1 reb, 1 ast  ← Assisted teammate
...
Event 538 (0:00 Q4): LeBron: 27 pts, 11 reb, 11 ast ← Final stats
```

**Now we can answer:**
- "What were his stats at halftime?" → Query snapshot at end of Q2
- "When did he score his 20th point?" → Find first snapshot where points >= 20
- "How many points in the 4th quarter?" → Diff between Q4 start and Q4 end
- "What was his shooting% at 7:42 PM?" → Query exact timestamp snapshot

---

## Understanding "Nonparametric Engines"

### What Are Player Performance Engines?

Traditional stats assume players are **linear scoring machines**:
- "He averages 25 ppg" assumes consistent 6.25 points per quarter
- Reality: Players have **dynamic performance patterns** (engines)

**Example: Two players with identical 24-point games**

**Player A (Steady Engine):**
```
Q1: 6 points  |████████
Q2: 6 points  |████████
Q3: 6 points  |████████
Q4: 6 points  |████████
Total: 24
```

**Player B (Explosive Engine):**
```
Q1: 2 points  |██
Q2: 4 points  |████
Q3: 18 points |██████████████████ ← EXPLOSION
Q4: 0 points  |
Total: 24
```

**Same box score, completely different engines!**

ML models need to understand:
- When does Player B explode? (3rd quarter pattern)
- What triggers the explosion? (fatigue? matchups? score differential?)
- Can we predict it? (YES - with temporal snapshots!)

### Extracting Nonparametric Engines

Our system creates a **time-series dataset** for every player:

```python
# Player Performance Timeline
game_id  player      event  period  time   points  fgm  fga  momentum
401589   LeBron      1      1       12:00  0       0    0    0.0
401589   LeBron      12     1       9:34   2       1    2    +2.0
401589   LeBron      24     1       6:12   7       3    5    +5.0
401589   LeBron      89     2       3:45   15      6    10   +8.0   ← Hot streak!
401589   LeBron      156    3       8:21   15      6    12   -2.0   ← Cold streak
401589   LeBron      298    4       1:23   27      11   18   +12.0  ← Clutch mode
```

**ML Features Extracted:**
- **Momentum** - Recent scoring rate (rolling window)
- **Efficiency** - FG% trajectory over time
- **Usage** - Shot attempts per period
- **Fatigue** - Performance degradation late game
- **Clutch** - Stats when score is close
- **Matchup** - Performance vs specific defenders (when on court together)

These features reveal the **nonparametric engine** - the pattern of HOW and WHEN players score, not just HOW MUCH.

---

## System Architecture

### Data Flow

```
ESPN PBP JSON (S3)
        ↓
    Load game data
        ↓
    Parse each event sequentially
        ↓
    Update running box score
        ↓
    Create snapshot (immutable)
        ↓
    Store snapshot list
        ↓
Temporal Query Engine
        ↓
ML Feature Extraction
```

### Core Components

**1. Box Score Snapshot (Immutable)**
```python
@dataclass(frozen=True)
class BoxScoreSnapshot:
    game_id: str
    sequence_number: int  # Event number (1, 2, 3, ...)
    period: int           # Quarter
    game_clock: str       # "7:42" remaining
    timestamp: datetime   # Actual real-world time

    home_team_stats: TeamStats
    away_team_stats: TeamStats
    home_players: Dict[str, PlayerStats]
    away_players: Dict[str, PlayerStats]
```

**2. Player Stats (Cumulative)**
```python
@dataclass(frozen=True)
class PlayerStats:
    player_id: str
    points: int          # Cumulative points SO FAR
    fgm, fga: int        # Field goals made/attempted
    fg3m, fg3a: int      # Three-pointers
    ftm, fta: int        # Free throws
    reb, ast, stl, blk, tov, pf: int
    plus_minus: int
    on_court: bool       # Is player currently on court?
```

**3. Processor (PBP → Snapshots)**
```python
class ESPNPlayByPlayProcessor:
    def process_game(self, game_id: str) -> List[BoxScoreSnapshot]:
        """
        Process PBP events into snapshots.

        Returns:
            List of snapshots (one per event)
        """
        # Load PBP data from S3
        game_data = self.load_game_data(game_id)

        # Initialize empty box score
        current_state = self.get_initial_state(game_data)

        snapshots = []
        for event in game_data['events']:
            # Update box score based on event
            current_state = self.process_event(event, current_state)

            # Create immutable snapshot
            snapshot = self.create_snapshot(current_state, event)
            snapshots.append(snapshot)

        return snapshots
```

---

## Temporal Query Capabilities

### Query Types

**1. Point-in-Time Queries**
```python
# What were team stats at halftime?
halftime_snapshot = find_snapshot(period=2, is_period_end=True)
print(f"Halftime: {halftime_snapshot.home_team_stats.points} - {halftime_snapshot.away_team_stats.points}")
```

**2. Range Queries**
```python
# How many points did Player X score in Q3?
q3_start = find_snapshot(period=3, sequence_number=min)
q3_end = find_snapshot(period=3, sequence_number=max)
q3_points = q3_end.player_stats['X'].points - q3_start.player_stats['X'].points
```

**3. Event-Based Queries**
```python
# When did home team take the lead?
for snapshot in snapshots:
    if snapshot.home_team_stats.points > snapshot.away_team_stats.points:
        print(f"Home team took lead at {snapshot.game_clock} in Q{snapshot.period}")
        break
```

**4. Momentum Queries**
```python
# Find the biggest scoring run
max_run = 0
run_start = None
for i in range(10, len(snapshots)):
    last_10 = snapshots[i-10:i]
    home_run = snapshots[i].home_team_stats.points - snapshots[i-10].home_team_stats.points
    if home_run > max_run:
        max_run = home_run
        run_start = snapshots[i-10]

print(f"Biggest run: {max_run} points starting at {run_start.game_clock}")
```

---

## Validation Against Actual Box Scores

### Why Validation Matters

PBP data can have errors:
- Missing events
- Incorrect attribution
- Timing issues
- Substitution tracking errors

**Solution:** Compare final snapshot against actual box score

### Validation Process

```python
# 1. Process PBP to final snapshot
snapshots = processor.process_game(game_id)
final_snapshot = snapshots[-1]

# 2. Load actual box score (from ESPN/NBA API)
actual_boxscore = load_actual_boxscore(game_id)

# 3. Compare stats
for stat in ['points', 'fgm', 'fga', 'reb', 'ast']:
    generated = final_snapshot.home_team_stats[stat]
    actual = actual_boxscore['home'][stat]

    if generated != actual:
        print(f"Discrepancy in {stat}: generated={generated}, actual={actual}")
```

### Quality Grading

| Accuracy | Grade | Meaning |
|----------|-------|---------|
| 99.9%+ | A | Perfect, use for all ML |
| 99.0-99.9% | B | Very good, minor discrepancies |
| 95.0-99.0% | C | Good, use with caution |
| 90.0-95.0% | D | Fair, validation recommended |
| <90.0% | F | Poor, do not use |

**Grade A games** are critical for ML training - we know the data is accurate.

---

## ML Integration: Player Dynamics

### Feature Extraction Pipeline

```python
# 1. Extract time-series for all players
player_dynamics = extract_player_dynamics(snapshots)

# Result: DataFrame with one row per player per event
#   game_id | player_id | event | period | points | fgm | fga | ...

# 2. Calculate momentum features
player_dynamics['recent_points'] = (
    player_dynamics
    .groupby('player_id')['points']
    .diff()
    .rolling(10)
    .sum()
)

# 3. Calculate efficiency features
player_dynamics['fg_pct'] = (
    player_dynamics['fgm'] / player_dynamics['fga']
)

# 4. Calculate fatigue indicators
player_dynamics['points_degradation'] = (
    player_dynamics.groupby(['player_id', 'period'])['points']
    .diff()
    .rolling(5)
    .mean()
)

# 5. Identify clutch situations
player_dynamics['is_clutch'] = (
    (player_dynamics['period'] == 4) &
    (player_dynamics['time'] < '5:00') &
    (abs(player_dynamics['score_diff']) < 5)
)

# 6. Extract clutch performance
clutch_stats = player_dynamics[player_dynamics['is_clutch']].groupby('player_id').agg({
    'points': 'sum',
    'fg_pct': 'mean',
    'recent_points': 'mean'
})
```

### Understanding Player Engines

**Example: Identifying a "3rd Quarter Specialist"**

```python
# Calculate scoring by quarter for each player
quarter_scoring = player_dynamics.groupby(['player_id', 'period'])['points'].max()

# Find players who score disproportionately in Q3
for player_id in player_dynamics['player_id'].unique():
    q3_pts = quarter_scoring[player_id, 3]
    avg_pts = quarter_scoring[player_id].mean()

    if q3_pts > avg_pts * 1.5:
        print(f"{player_id}: 3rd Quarter Specialist!")
        print(f"  Q3: {q3_pts} points vs avg {avg_pts}")
```

**Example: Detecting "Slow Starters"**

```python
# Compare Q1 vs later quarters
q1_efficiency = player_dynamics[player_dynamics['period'] == 1].groupby('player_id')['fg_pct'].mean()
q234_efficiency = player_dynamics[player_dynamics['period'] > 1].groupby('player_id')['fg_pct'].mean()

slow_starters = q234_efficiency - q1_efficiency
print(slow_starters[slow_starters > 0.10])  # 10%+ better after Q1
```

---

## Quarter-Level Snapshots for Betting Models

### Why Quarter Snapshots?

Betting markets offer:
- Halftime bets (based on Q1-Q2 performance)
- Quarter spreads (Q3 point differential)
- Live betting (adjusts based on current quarter)

**Traditional approach:** Only have full-game stats

**Our approach:** Extract quarter-level box scores from snapshots

### Extracting Quarter Snapshots

```python
def extract_quarter_snapshots(snapshots: List[BoxScoreSnapshot]) -> Dict[int, BoxScoreSnapshot]:
    """
    Get final snapshot for each quarter.
    """
    quarter_snapshots = {}

    for snapshot in snapshots:
        period = snapshot.period

        # Keep the last snapshot for each period
        if period not in quarter_snapshots:
            quarter_snapshots[period] = snapshot
        elif snapshot.sequence_number > quarter_snapshots[period].sequence_number:
            quarter_snapshots[period] = snapshot

    return quarter_snapshots

# Usage
quarters = extract_quarter_snapshots(snapshots)

print(f"Q1 Final: {quarters[1].home_team_stats.points}")
print(f"Q2 Final: {quarters[2].home_team_stats.points}")
print(f"Q3 Final: {quarters[3].home_team_stats.points}")
print(f"Q4 Final: {quarters[4].home_team_stats.points}")

# Calculate quarter differentials
q1_diff = quarters[1].home_team_stats.points - quarters[1].away_team_stats.points
q2_diff = (quarters[2].home_team_stats.points - quarters[2].away_team_stats.points) - q1_diff
q3_diff = (quarters[3].home_team_stats.points - quarters[3].away_team_stats.points) - q1_diff - q2_diff
```

### Betting Model Features

```python
# Train model to predict Q3 performance based on Q1-Q2
features = pd.DataFrame({
    'q1_diff': q1_diffs,
    'q2_diff': q2_diffs,
    'q1_home_fg_pct': [q[1].home_team_stats.fgm / q[1].home_team_stats.fga for q in quarters],
    'q2_home_fg_pct': [q[2].home_team_stats.fgm / q[2].home_team_stats.fga for q in quarters],
    'home_momentum': [calculate_momentum(q[1], q[2]) for q in quarters],
})

target = pd.Series(q3_diffs, name='q3_diff')

# Train model
model = GradientBoostingRegressor()
model.fit(features, target)

# At halftime of a live game, predict Q3 outcome
halftime_features = extract_features_from_quarters(live_game_quarters)
predicted_q3_diff = model.predict(halftime_features)
```

---

## Current Implementation Status

### ✅ Completed

1. **Core Architecture**
   - `box_score_snapshot.py` - Immutable snapshot data structures
   - `base_processor.py` - Abstract base processor
   - `espn_processor.py` - ESPN PBP processor

2. **Validation Framework**
   - `validate_pbp_to_boxscore.py` - Validation script
   - Comparison against actual box scores
   - Quality grading system (A-F)

3. **ML Integration**
   - Player dynamics extraction
   - Time-series feature generation
   - Momentum/efficiency/fatigue calculations

4. **Quarter Snapshots**
   - Quarter boundary extraction
   - Quarter-level box scores
   - Betting model features

### ⏸️ Pending

1. **Validation Testing**
   - Run validation on 100+ games
   - Document accuracy rates
   - Identify common discrepancies

2. **Storage System**
   - Save snapshots to RDS
   - Export to Parquet for ML
   - Optimize query performance

3. **Batch Processing**
   - Process full 2023-2025 seasons (~3,000 games)
   - Parallel processing
   - Progress tracking

4. **Advanced Metrics**
   - Plus/minus calculation
   - On-court/off-court analysis
   - Lineup effectiveness

---

## Usage Examples

### Example 1: Process Single Game

```python
from pbp_to_boxscore.espn_processor import ESPNPlayByPlayProcessor

# Initialize processor
processor = ESPNPlayByPlayProcessor(
    s3_bucket="nba-sim-raw-data-lake",
    local_cache_dir="/tmp/pbp_cache"
)

# Process game
game_id = "401584903"  # 2024 Finals Game 1
snapshots = processor.process_game(game_id)

print(f"Generated {len(snapshots)} snapshots")

# Query halftime score
halftime = [s for s in snapshots if s.period == 2][-1]
print(f"Halftime: {halftime.home_team_stats.points} - {halftime.away_team_stats.points}")
```

### Example 2: Extract Player Dynamics

```python
from pbp_to_boxscore.validate_pbp_to_boxscore import PBPValidator

validator = PBPValidator()

# Process game
result = validator.process_game(game_id)
snapshots = result['snapshots']

# Extract player time-series
player_dynamics = validator.extract_player_dynamics(game_id, snapshots)

# Generate ML features
ml_features = validator.generate_ml_features(player_dynamics)

# Save for training
ml_features.to_csv("player_dynamics_ml_features.csv")
```

### Example 3: Validate Accuracy

```python
# Process game to final snapshot
final_snapshot = snapshots[-1]

# Load actual box score
actual_boxscore = {
    'home_team': {'points': 105, 'fgm': 42, 'fga': 88, 'reb': 45, 'ast': 25},
    'away_team': {'points': 98, 'fgm': 38, 'fga': 85, 'reb': 42, 'ast': 22}
}

# Validate
validation = validator.validate_against_actual_boxscore(
    game_id, final_snapshot, actual_boxscore
)

print(f"Accuracy: {validation['accuracy']:.2f}%")
print(f"Grade: {validation['grade']}")
```

---

## Files Created

| File | Purpose | Status |
|------|---------|--------|
| `scripts/pbp_to_boxscore/box_score_snapshot.py` | Snapshot data structures | ✅ Complete |
| `scripts/pbp_to_boxscore/base_processor.py` | Abstract processor | ✅ Complete |
| `scripts/pbp_to_boxscore/espn_processor.py` | ESPN processor | ✅ Complete |
| `scripts/pbp_to_boxscore/validate_pbp_to_boxscore.py` | Validation & demo | ✅ Complete |
| `docs/PBP_TO_BOXSCORE_SYSTEM.md` | This documentation | ✅ Complete |

---

## Next Steps

**Immediate (This Week):**
1. Test validation script on sample ESPN games
2. Fix any data parsing issues
3. Document accuracy rates

**Short Term (This Month):**
1. Process 100 sample games (2023-2025)
2. Calculate average accuracy
3. Identify grade A games for ML training
4. Extract player dynamics for top 50 players

**Medium Term (Next 2-3 Months):**
1. Process full 2023-2025 seasons (~3,000 games)
2. Store snapshots in RDS + Parquet
3. Train ML models on player dynamics
4. Build betting models with quarter snapshots

---

## Summary

**The PBP-to-Box-Score system enables:**

✅ **Temporal Queries** - Stats at any exact moment
✅ **Validation** - Compare against actual box scores
✅ **Player Engines** - Extract nonparametric performance patterns
✅ **ML Features** - Momentum, efficiency, fatigue, clutch
✅ **Quarter Snapshots** - Betting model inputs
✅ **Performance Dynamics** - Understand HOW players score, not just HOW MUCH

**This transforms static box scores into dynamic temporal data, unlocking ML capabilities that traditional analytics can't access.**

---

**Ready to validate and extract player "engines"!** 🔥

**Next command:** `python scripts/pbp_to_boxscore/validate_pbp_to_boxscore.py`

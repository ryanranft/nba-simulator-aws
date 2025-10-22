# 5.20: Panel Data Processing System

**Sub-Phase:** 5.20 (Panel Data & Temporal Features)
**Parent Phase:** [Phase 5: Machine Learning Pipeline](../PHASE_5_INDEX.md)
**Status:** ✅ COMPLETE
**Priority:** ⭐ CRITICAL (Required for 5.1)
**Implementation ID:** rec_22
**Source:** Econometric Analysis of Cross Section and Panel Data (Wooldridge)
**Completed:** October 17, 2025

**Implementation:** `implement_rec_22.py`
**Tests:** `test_rec_22.py` (33/33 passing)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core Concepts](#core-concepts)
3. [Usage Examples](#usage-examples)
4. [Integration Patterns](#integration-patterns)
5. [Advanced Features](#advanced-features)
6. [Performance Tips](#performance-tips)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Installation

The panel data processing system is already installed. All dependencies are in `requirements.txt`:

```bash
# Activate environment
conda activate nba-aws

# Dependencies (already installed):
# - pandas >= 2.0
# - numpy >= 1.20
# - boto3 (for S3)
```

### Basic Usage

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd
from datetime import datetime

# Initialize the system
system = PanelDataProcessingSystem()
system.setup()

# Load your NBA data
df = pd.read_csv('player_game_stats.csv')

# Create panel structure
panel_df = system.create_panel_index(df)

# Generate temporal features
panel_df = system.generate_lags(panel_df, variables=['points', 'rebounds'], lags=[1, 2, 3])
panel_df = system.generate_rolling_stats(panel_df, variables=['points'], windows=[5, 10])
panel_df = system.generate_cumulative_stats(panel_df, variables=['points', 'games'])

# Query player stats at specific time
stats = system.query_stats_at_time(
    player_id=2544,  # LeBron James
    timestamp=datetime(2023, 6, 12, 21, 0, 0),
    cumulative_cols=['points']
)
print(f"LeBron's career points through June 12, 2023: {stats['points_cumulative']}")
```

---

## Core Concepts

### 1. Panel Data Structure

Panel data has two dimensions: **entities** (players) and **time** (games/timestamps).

**Multi-Index Structure:**
```
(player_id, game_id, timestamp) → statistics
```

**Example:**
```
player_id  game_id  timestamp            points  rebounds
2544       1001     2023-01-01 19:00:00  25      7
2544       1002     2023-01-03 19:00:00  30      8
2544       1003     2023-01-05 19:00:00  28      6
2546       1001     2023-01-01 20:00:00  22      5
```

### 2. Temporal Features

**Lag Variables** - Previous game statistics:
- `points_lag1` = points from 1 game ago
- `points_lag2` = points from 2 games ago
- Use case: "How did player perform last game?"

**Rolling Windows** - Last N games statistics:
- `points_rolling_5_mean` = average points over last 5 games
- `points_rolling_5_std` = standard deviation over last 5 games
- Use case: "What's player's recent form?"

**Cumulative Statistics** - Career totals through each game:
- `points_cumulative` = total career points at that moment
- `games_cumulative` = total career games at that moment
- Use case: "What were career stats at exact timestamp?"

### 3. Panel Transformations

**Within Transformation** - Remove player-specific effects:
```python
# Demean by player (y_it - ȳ_i)
within_points = system.within_transform(panel_df, 'points')
# Result: player deviations from their own average
```

**Between Transformation** - Extract player averages:
```python
# Player means (ȳ_i)
between_points = system.between_transform(panel_df, 'points')
# Result: each player's career average
```

**First-Difference** - Game-to-game changes:
```python
# Change from previous game (Δy_it = y_it - y_{i,t-1})
diff_points = system.first_difference(panel_df, 'points')
# Result: how much points changed from last game
```

---

## Usage Examples

### Example 1: Creating Panel Data from Flat CSV

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd

# Load flat game stats
df = pd.read_csv('/path/to/player_game_stats.csv')

# Required columns: player_id, game_id, game_date
# game_date should be 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'

# Initialize system
system = PanelDataProcessingSystem()
system.setup()

# Create panel index
panel = system.create_panel_index(df)

print(f"Panel shape: {panel.shape}")
print(f"Players: {panel.index.get_level_values('player_id').nunique()}")
print(f"Games per player: {panel.groupby('player_id').size().mean():.1f}")
```

### Example 2: Feature Engineering Pipeline

```python
from implement_rec_22 import create_panel_from_dataframe, generate_temporal_features
import pandas as pd

# Load data
df = pd.read_csv('nba_games.csv')

# Step 1: Create panel structure
panel = create_panel_from_dataframe(df)

# Step 2: Generate all temporal features in one call
panel_with_features = generate_temporal_features(
    panel,
    lag_vars=['points', 'rebounds', 'assists', 'fg_pct'],
    lag_periods=[1, 2, 3],
    rolling_vars=['points', 'rebounds', 'assists'],
    rolling_windows=[5, 10, 20],
    cumulative_vars=['points', 'rebounds', 'assists', 'games']
)

print(f"Original features: {df.shape[1]}")
print(f"Features after temporal engineering: {panel_with_features.shape[1]}")
print(f"New features created: {panel_with_features.shape[1] - df.shape[1]}")

# Features created:
# - 4 variables × 3 lags = 12 lag features
# - 3 variables × 3 windows × 2 stats (mean, std) = 18 rolling features
# - 4 cumulative features
# Total: 34 new features
```

### Example 3: Temporal Query - Player Stats at Exact Moment

```python
from implement_rec_22 import PanelDataProcessingSystem
from datetime import datetime
import pandas as pd

system = PanelDataProcessingSystem()
system.setup()

# Load and prepare data
df = pd.read_csv('nba_games.csv')
panel = system.create_panel_index(df)
panel = system.generate_cumulative_stats(panel, ['points', 'rebounds', 'assists'])

# Query: "What were Kobe Bryant's career stats on June 19, 2016 at 7:02 PM CT?"
kobe_stats = system.query_stats_at_time(
    player_id=977,  # Kobe Bryant
    timestamp=datetime(2016, 6, 19, 19, 2, 0),
    cumulative_cols=['points', 'rebounds', 'assists']
)

print(f"Kobe Bryant's career statistics as of June 19, 2016 at 7:02 PM:")
print(f"  Points: {kobe_stats['points_cumulative']:,}")
print(f"  Rebounds: {kobe_stats['rebounds_cumulative']:,}")
print(f"  Assists: {kobe_stats['assists_cumulative']:,}")
print(f"  Games played: {kobe_stats['games_cumulative']}")

# Use case: Answer historical questions with millisecond precision
# "What were player X's stats at the exact moment of event Y?"
```

### Example 4: Player Form Analysis with Rolling Windows

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd
import matplotlib.pyplot as plt

system = PanelDataProcessingSystem()
system.setup()

# Load data
df = pd.read_csv('lebron_games_2023.csv')
panel = system.create_panel_index(df)

# Generate rolling averages for different windows
panel = system.generate_rolling_stats(
    panel,
    variables=['points'],
    windows=[5, 10, 20],
    stats=['mean']
)

# Extract for plotting
lebron_data = panel.xs(2544, level='player_id')  # LeBron = 2544

# Plot form over season
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(lebron_data.index.get_level_values('timestamp'),
        lebron_data['points'],
        label='Game Points', alpha=0.5)
ax.plot(lebron_data.index.get_level_values('timestamp'),
        lebron_data['points_rolling_5_mean'],
        label='5-Game Average')
ax.plot(lebron_data.index.get_level_values('timestamp'),
        lebron_data['points_rolling_10_mean'],
        label='10-Game Average')
ax.plot(lebron_data.index.get_level_values('timestamp'),
        lebron_data['points_rolling_20_mean'],
        label='20-Game Average')
ax.set_xlabel('Date')
ax.set_ylabel('Points')
ax.set_title("LeBron James - Scoring Form 2023 Season")
ax.legend()
plt.savefig('lebron_form_2023.png', dpi=150)

# Identify hot/cold streaks
print("Hottest 5-game stretch:")
print(lebron_data.nlargest(5, 'points_rolling_5_mean')[['points_rolling_5_mean']])
```

### Example 5: Machine Learning Feature Preparation

```python
from implement_rec_22 import create_panel_from_dataframe, generate_temporal_features
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load game data with outcomes
df = pd.read_csv('games_with_outcomes.csv')
# Columns: player_id, game_id, game_date, points, rebounds, assists, ..., win (target)

# Create panel with temporal features
panel = create_panel_from_dataframe(df)
panel = generate_temporal_features(
    panel,
    lag_vars=['points', 'rebounds', 'assists', 'fg_pct', 'plus_minus'],
    lag_periods=[1, 2, 3],
    rolling_vars=['points', 'plus_minus'],
    rolling_windows=[5, 10],
    cumulative_vars=['points', 'games']
)

# Reset index for ML
ml_df = panel.reset_index()

# Separate features and target
feature_cols = [c for c in ml_df.columns if c not in ['player_id', 'game_id', 'timestamp', 'win']]
X = ml_df[feature_cols]
y = ml_df['win']

# Drop rows with NaN (due to lags)
valid_idx = ~X.isna().any(axis=1)
X = X[valid_idx]
y = y[valid_idx]

print(f"Original features: ~16")
print(f"Panel features: {len(feature_cols)}")
print(f"Training samples: {len(X):,}")

# Train model
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print(f"Model accuracy: {model.score(X_test, y_test):.1%}")

# Expected improvement: 63% (flat) → 68-71% (panel features)
```

### Example 6: Panel Transformations for Econometric Analysis

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd
import statsmodels.api as sm

system = PanelDataProcessingSystem()
system.setup()

# Load data
df = pd.read_csv('player_games.csv')
panel = system.create_panel_index(df)

# Within transformation - Remove player fixed effects
within_points = system.within_transform(panel, 'points')
within_minutes = system.within_transform(panel, 'minutes')

# Now regress demeaned points on demeaned minutes
# This removes player-specific effects (like talent level)
X = sm.add_constant(within_minutes)
model = sm.OLS(within_points, X).fit()
print(model.summary())

# Interpretation: Effect of minutes played on points,
# controlling for player-specific ability

# Between transformation - Cross-sectional analysis
between_points = system.between_transform(panel, 'points')
between_minutes = system.between_transform(panel, 'minutes')

# Regress player averages
X_between = sm.add_constant(between_minutes)
model_between = sm.OLS(between_points, X_between).fit()
print(model_between.summary())

# Interpretation: Do high-minute players score more on average?
```

### Example 7: First-Difference for Trend Analysis

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd

system = PanelDataProcessingSystem()
system.setup()

# Load season data
df = pd.read_csv('season_2023.csv')
panel = system.create_panel_index(df)

# Calculate game-to-game changes
panel['points_change'] = system.first_difference(panel, 'points')
panel['minutes_change'] = system.first_difference(panel, 'minutes')

# Find players with most improvement over season
improvement = panel.groupby('player_id')['points_change'].mean()
most_improved = improvement.nlargest(10)

print("Most Improved Players (Points Per Game Change):")
print(most_improved)

# Identify consistency vs volatility
volatility = panel.groupby('player_id')['points_change'].std()
most_consistent = volatility.nsmallest(10)

print("\nMost Consistent Players (Smallest Game-to-Game Variance):")
print(most_consistent)
```

---

## Integration Patterns

### Pattern 1: S3 Data Pipeline

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd
import boto3

system = PanelDataProcessingSystem()
system.setup()

# Load from S3
s3 = boto3.client('s3')
obj = s3.get_object(Bucket='nba-sim-raw-data-lake', Key='merged/player_games_all.csv')
df = pd.read_csv(obj['Body'])

# Create panel
panel = system.create_panel_index(df)
panel = system.generate_lags(panel, ['points', 'rebounds', 'assists'], [1, 2, 3])

# Save back to S3
output_buffer = panel.to_parquet()
s3.put_object(Bucket='nba-sim-raw-data-lake', Key='panel/player_panel_features.parquet', Body=output_buffer)
```

### Pattern 2: PostgreSQL Integration

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd
from sqlalchemy import create_engine

system = PanelDataProcessingSystem()
system.setup()

# Load from PostgreSQL
engine = create_engine('postgresql://user:pass@host:5432/nba_db')
df = pd.read_sql("SELECT * FROM player_game_stats WHERE season >= 2020", engine)

# Create panel features
panel = system.create_panel_index(df)
panel = generate_temporal_features(
    panel,
    lag_vars=['points', 'rebounds', 'assists'],
    lag_periods=[1, 2, 3],
    rolling_vars=['points'],
    rolling_windows=[5, 10],
    cumulative_vars=['points', 'games']
)

# Save to new table
panel.reset_index().to_sql('player_panel_features', engine, if_exists='replace', index=False)
```

### Pattern 3: MLflow Experiment Integration

```python
from implement_rec_22 import create_panel_from_dataframe, generate_temporal_features
from implement_ml_systems_1 import MLflowModelVersioning
import pandas as pd
import mlflow

# Setup MLflow
mlflow_system = MLflowModelVersioning()
mlflow_system.setup()
mlflow.set_experiment("nba-panel-data-experiments")

# Load data
df = pd.read_csv('games.csv')

# Create panel features
panel = create_panel_from_dataframe(df)
panel_with_features = generate_temporal_features(
    panel,
    lag_vars=['points', 'rebounds', 'assists'],
    lag_periods=[1, 2, 3],
    rolling_vars=['points'],
    rolling_windows=[5, 10],
    cumulative_vars=['points', 'games']
)

# Log panel data characteristics
with mlflow.start_run(run_name="panel-data-creation"):
    mlflow.log_param("players", panel.index.get_level_values('player_id').nunique())
    mlflow.log_param("games", panel.index.get_level_values('game_id').nunique())
    mlflow.log_param("features_original", df.shape[1])
    mlflow.log_param("features_panel", panel_with_features.shape[1])
    mlflow.log_param("features_added", panel_with_features.shape[1] - df.shape[1])

    # Save panel dataset as artifact
    panel_with_features.to_parquet('/tmp/panel_features.parquet')
    mlflow.log_artifact('/tmp/panel_features.parquet')
```

### Pattern 4: Real-Time Feature Generation

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd

class RealTimePanelFeatures:
    """Generate panel features for incoming game data."""

    def __init__(self):
        self.system = PanelDataProcessingSystem()
        self.system.setup()
        self.historical_panel = None

    def load_historical(self, path: str):
        """Load historical panel data."""
        df = pd.read_csv(path)
        self.historical_panel = self.system.create_panel_index(df)
        self.historical_panel = self.system.generate_cumulative_stats(
            self.historical_panel,
            ['points', 'rebounds', 'assists']
        )

    def generate_features_for_new_game(self, player_id: int, game_date: str,
                                       current_stats: dict) -> dict:
        """Generate features for new game using historical context."""
        from datetime import datetime

        # Query historical cumulative stats
        query_time = datetime.strptime(game_date, '%Y-%m-%d')
        hist_stats = self.system.query_stats_at_time(
            player_id,
            query_time,
            cumulative_cols=['points', 'rebounds', 'assists']
        )

        # Get recent games for rolling stats
        player_history = self.historical_panel.xs(player_id, level='player_id')
        recent_games = player_history.tail(10)

        features = {
            # Current game stats
            **current_stats,

            # Career cumulative
            'career_points': hist_stats.get('points_cumulative', 0),
            'career_rebounds': hist_stats.get('rebounds_cumulative', 0),
            'career_assists': hist_stats.get('assists_cumulative', 0),
            'career_games': hist_stats.get('games_cumulative', 0),

            # Recent form (last 10 games)
            'points_l10_mean': recent_games['points'].mean(),
            'points_l10_std': recent_games['points'].std(),
            'rebounds_l10_mean': recent_games['rebounds'].mean(),
            'assists_l10_mean': recent_games['assists'].mean(),
        }

        return features

# Usage
feature_gen = RealTimePanelFeatures()
feature_gen.load_historical('historical_games.csv')

# New game comes in
new_game_features = feature_gen.generate_features_for_new_game(
    player_id=2544,
    game_date='2024-01-15',
    current_stats={'points': 28, 'rebounds': 7, 'assists': 9}
)
print(new_game_features)
```

---

## Advanced Features

### Multi-Level Panel Data

For more complex panel structures (e.g., player-team-season):

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd

# Create multi-level panel
df = pd.read_csv('player_team_season_games.csv')

# Custom multi-index
panel = df.set_index(['player_id', 'team_id', 'season', 'game_id', 'timestamp'])
panel = panel.sort_index()

# Generate lags within player-team-season groups
panel['points_lag1'] = panel.groupby(level=['player_id', 'team_id', 'season'])['points'].shift(1)

# Rolling stats within groups
panel['points_rolling_5'] = (
    panel.groupby(level=['player_id', 'team_id', 'season'])['points']
    .rolling(window=5, min_periods=1)
    .mean()
    .reset_index(level=[0, 1, 2], drop=True)
)
```

### Custom Aggregation Functions

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd
import numpy as np

system = PanelDataProcessingSystem()
system.setup()

df = pd.read_csv('games.csv')
panel = system.create_panel_index(df)

# Custom rolling aggregations
panel['points_rolling_5_median'] = (
    panel.groupby(level='player_id')['points']
    .rolling(window=5, min_periods=1)
    .median()
    .reset_index(level=0, drop=True)
)

panel['points_rolling_5_q75'] = (
    panel.groupby(level='player_id')['points']
    .rolling(window=5, min_periods=1)
    .quantile(0.75)
    .reset_index(level=0, drop=True)
)

# Exponentially-weighted moving average (more recent games weighted higher)
panel['points_ewma'] = (
    panel.groupby(level='player_id')['points']
    .ewm(span=10, adjust=False)
    .mean()
    .reset_index(level=0, drop=True)
)
```

### Time-Varying Features

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd
import numpy as np

system = PanelDataProcessingSystem()
system.setup()

df = pd.read_csv('games.csv')
panel = system.create_panel_index(df)

# Add age at each game
panel['age_days'] = (
    panel.index.get_level_values('timestamp') -
    panel.groupby('player_id')['birthdate'].first()
).dt.days
panel['age_years'] = panel['age_days'] / 365.25

# Add games since injury
panel['days_since_injury'] = (
    panel.index.get_level_values('timestamp') -
    panel.groupby('player_id')['last_injury_date'].first()
).dt.days

# Add experience level
panel['games_cumulative'] = panel.groupby('player_id').cumcount() + 1
panel['experience_level'] = pd.cut(
    panel['games_cumulative'],
    bins=[0, 82, 328, 820, np.inf],
    labels=['Rookie', 'Sophomore-Year4', 'Veteran', 'Elite']
)
```

---

## Performance Tips

### 1. Use Parquet for Large Panel Data

```python
# Save panel as Parquet (much faster than CSV for panel data)
panel.to_parquet('panel_features.parquet', compression='snappy')

# Load (10-50x faster than CSV)
panel = pd.read_parquet('panel_features.parquet')
```

### 2. Batch Process by Player

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd

system = PanelDataProcessingSystem()
system.setup()

df = pd.read_csv('huge_dataset.csv')

# Process players in batches to reduce memory
player_ids = df['player_id'].unique()
batch_size = 100
results = []

for i in range(0, len(player_ids), batch_size):
    batch_players = player_ids[i:i+batch_size]
    batch_df = df[df['player_id'].isin(batch_players)]

    # Create panel for batch
    batch_panel = system.create_panel_index(batch_df)
    batch_panel = system.generate_lags(batch_panel, ['points'], [1, 2, 3])

    results.append(batch_panel)
    print(f"Processed players {i} to {i+batch_size}")

# Combine all batches
final_panel = pd.concat(results)
```

### 3. Cache Rolling Stats

```python
from implement_rec_22 import PanelDataProcessingSystem
import pandas as pd
import os

system = PanelDataProcessingSystem()
system.setup()

cache_path = '/tmp/panel_cache/rolling_stats.parquet'

if os.path.exists(cache_path):
    # Load cached
    panel = pd.read_parquet(cache_path)
    print("Loaded from cache")
else:
    # Compute
    df = pd.read_csv('games.csv')
    panel = system.create_panel_index(df)
    panel = system.generate_rolling_stats(panel, ['points'], [5, 10, 20])

    # Save to cache
    panel.to_parquet(cache_path)
    print("Computed and cached")
```

### 4. Use Dask for Very Large Datasets

```python
import dask.dataframe as dd
from implement_rec_22 import PanelDataProcessingSystem

system = PanelDataProcessingSystem()
system.setup()

# Load huge dataset with Dask (lazy loading)
ddf = dd.read_csv('massive_dataset_*.csv')

# Partition by player_id for parallel processing
ddf = ddf.set_index('player_id')

# Define panel processing function
def process_player_panel(player_df):
    system = PanelDataProcessingSystem()
    system.setup()
    panel = system.create_panel_index(player_df.reset_index())
    panel = system.generate_lags(panel, ['points'], [1, 2, 3])
    return panel

# Apply to each partition (parallel)
result = ddf.map_partitions(process_player_panel)

# Compute (triggers parallel execution)
final_panel = result.compute()
```

---

## Troubleshooting

### Issue 1: "Missing required columns"

```python
# Error: KeyError: 'player_id'

# Solution: Ensure your DataFrame has required columns
required_cols = ['player_id', 'game_id', 'game_date']
print(f"Your columns: {list(df.columns)}")
print(f"Missing: {set(required_cols) - set(df.columns)}")

# Rename if needed
df = df.rename(columns={'PLAYER_ID': 'player_id', 'GAME_ID': 'game_id', 'GAME_DATE': 'game_date'})
```

### Issue 2: "Duplicate indices"

```python
# Warning: Found N duplicate indices

# Check for duplicates
dupes = panel[panel.index.duplicated(keep=False)]
print(f"Duplicate games:\n{dupes}")

# Solution 1: Keep first occurrence
panel = panel[~panel.index.duplicated(keep='first')]

# Solution 2: Average duplicates
panel = panel.groupby(level=['player_id', 'game_id', 'timestamp']).mean()
```

### Issue 3: "NaN values in lag variables"

```python
# Lags create NaN for first N games (expected)

# Check NaN count
print(f"NaN in points_lag1: {panel['points_lag1'].isna().sum()}")

# Solution 1: Drop rows with NaN
panel_clean = panel.dropna(subset=['points_lag1'])

# Solution 2: Fill with 0
panel['points_lag1'] = panel['points_lag1'].fillna(0)

# Solution 3: Forward-fill (use last valid value)
panel['points_lag1'] = panel.groupby('player_id')['points_lag1'].ffill()
```

### Issue 4: "Memory error with large dataset"

```python
# Error: MemoryError

# Solution: Process in chunks or use Dask (see Performance Tips)

# Or reduce data size
# 1. Filter to specific seasons
df_recent = df[df['season'] >= 2020]

# 2. Sample players
sample_players = df['player_id'].unique()[:100]
df_sample = df[df['player_id'].isin(sample_players)]

# 3. Select key variables only
key_vars = ['player_id', 'game_id', 'game_date', 'points', 'rebounds', 'assists']
df_slim = df[key_vars]
```

### Issue 5: "Incorrect rolling window values"

```python
# Rolling stats seem wrong

# Check sorting (CRITICAL - must sort by timestamp within player)
panel = panel.sort_index(level=['player_id', 'timestamp'])

# Verify with manual calculation
player_1 = panel.xs(1, level='player_id')
manual_rolling = player_1['points'].rolling(5, min_periods=1).mean()
system_rolling = player_1['points_rolling_5_mean']
print(f"Match: {manual_rolling.equals(system_rolling)}")
```

### Issue 6: "Temporal query returns None"

```python
# Query returns None or empty result

# Debug
from datetime import datetime

player_id = 2544
query_time = datetime(2023, 1, 15, 19, 0, 0)

# Check if player exists
if player_id not in panel.index.get_level_values('player_id'):
    print(f"Player {player_id} not found in panel")

# Check timestamp range
player_data = panel.xs(player_id, level='player_id')
print(f"Player's first game: {player_data.index.get_level_values('timestamp').min()}")
print(f"Player's last game: {player_data.index.get_level_values('timestamp').max()}")
print(f"Query time: {query_time}")

# Solution: Ensure query_time is within player's career
```

---

## Next Steps

After mastering rec_22 (Panel Data Processing), you can:

1. **rec_11: Advanced Feature Engineering**
   - Build 50-100+ features using panel data foundation
   - Feature selection and importance analysis
   - Dimensionality reduction techniques

2. **Enhance ml_systems_1 & ml_systems_2**
   - Retrain models on panel data (expected: 63% → 68-71% accuracy)
   - Track experiments with temporal features
   - Monitor drift on expanded feature set

3. **Economic Analysis**
   - Fixed effects models
   - Random effects models
   - Difference-in-differences analysis
   - Granger causality tests

4. **Time Series Forecasting**
   - ARIMA on player performance
   - LSTM models with panel features
   - Prophet for seasonality detection

---

## Additional Resources

**Source Books:**
- Wooldridge - Econometric Analysis of Cross Section and Panel Data (Chapters 10-11)
- Baltagi - Econometric Analysis of Panel Data (Chapters 2-3)
- Greene - Econometric Analysis (Chapter 9: Panel Data)

**Implementation Files:**
- `/Users/ryanranft/nba-simulator-aws/docs/phases/phase_0/implement_rec_22.py` (621 lines)
- `/Users/ryanranft/nba-simulator-aws/docs/phases/phase_0/test_rec_22.py` (33 tests)

**Related Documentation:**
- `/Users/ryanranft/nba-simulator-aws/docs/ml_systems/book_recommendations/TRACKER.md`
- `/Users/ryanranft/nba-simulator-aws/docs/MASTER_IMPLEMENTATION_SEQUENCE.md`

**Questions or Issues?**
- Check test file for usage examples
- Review implementation code for method signatures
- See TROUBLESHOOTING.md for common issues

---

**Last Updated:** October 16, 2025
**Status:** ✅ Complete (33/33 tests passing)
**Version:** 1.0

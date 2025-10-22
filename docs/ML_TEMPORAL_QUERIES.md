# ML Temporal Query Guide

**Purpose:** Use temporal box score snapshots for machine learning
**Created:** October 18, 2025
**Database:** SQLite partitioned temporal snapshots

---

## Overview

The temporal box score snapshot system stores **player and team stats at every moment** in game time. This enables ML queries that traditional box scores can't answer.

**Tables:**
- `player_box_score_snapshots` - Player stats at each event
- `team_box_score_snapshots` - Team stats at each event
- Views for quick access (halftime, quarters, clutch moments)

---

## Quick Start for ML

### Load Data in Python

```python
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('/tmp/basketball_reference_boxscores.db')

# Load player snapshots for a game
df = pd.read_sql_query("""
    SELECT *
    FROM player_box_score_snapshots
    WHERE game_id = '202306120DEN'
    ORDER BY event_number
""", conn)

print(df.head())
```

### Load Data in R

```r
library(DBI)
library(RSQLite)

# Connect to database
conn <- dbConnect(SQLite(), "/tmp/basketball_reference_boxscores.db")

# Load player snapshots
df <- dbGetQuery(conn, "
    SELECT *
    FROM player_box_score_snapshots
    WHERE game_id = '202306120DEN'
    ORDER BY event_number
")

head(df)
```

---

## Common ML Queries

### 1. Player Stats at Halftime

**Use case:** Train models to predict 2nd half performance based on 1st half

```sql
-- Get all players' halftime stats
SELECT
    game_id,
    player_id,
    player_name,
    points as halftime_points,
    fgm,
    fga,
    fg_pct as halftime_fg_pct,
    reb as halftime_reb,
    ast as halftime_ast
FROM player_box_score_snapshots
WHERE period = 2
AND event_number IN (
    SELECT MAX(event_number)
    FROM player_box_score_snapshots p2
    WHERE p2.game_id = player_box_score_snapshots.game_id
    AND p2.period = 2
    AND p2.player_id = player_box_score_snapshots.player_id
)
ORDER BY game_id, player_id;
```

**ML Application:**
```python
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

# Load halftime stats
halftime_df = pd.read_sql_query(halftime_query, conn)

# Load final stats (end of game)
final_df = pd.read_sql_query("""
    SELECT game_id, player_id, points as final_points
    FROM player_box_score_snapshots
    WHERE period = 4
    AND event_number IN (
        SELECT MAX(event_number)
        FROM player_box_score_snapshots p2
        WHERE p2.game_id = player_box_score_snapshots.game_id
        AND p2.player_id = player_box_score_snapshots.player_id
    )
""", conn)

# Merge
df = halftime_df.merge(final_df, on=['game_id', 'player_id'])

# Calculate 2nd half points
df['second_half_points'] = df['final_points'] - df['halftime_points']

# Train model
X = df[['halftime_points', 'halftime_fg_pct', 'halftime_reb', 'halftime_ast']]
y = df['second_half_points']

model = GradientBoostingRegressor()
model.fit(X, y)

# Predict 2nd half performance
predictions = model.predict(X)
```

---

### 2. Quarter-by-Quarter Performance

**Use case:** Identify players who are "3rd quarter specialists"

```sql
-- Player performance by quarter
SELECT
    player_id,
    player_name,
    period,
    MAX(points) - COALESCE(LAG(MAX(points)) OVER (
        PARTITION BY game_id, player_id ORDER BY period
    ), 0) as quarter_points
FROM player_box_score_snapshots
GROUP BY game_id, player_id, period
ORDER BY player_id, period;
```

**ML Application:**
```python
# Load quarter-by-quarter data
quarters_df = pd.read_sql_query(quarter_query, conn)

# Pivot to wide format
pivot = quarters_df.pivot_table(
    index=['player_id', 'player_name'],
    columns='period',
    values='quarter_points',
    aggfunc='mean'
)

# Identify 3rd quarter specialists
pivot['q3_specialist_score'] = pivot[3] / pivot[[1, 2, 3, 4]].mean(axis=1)

# Players who score 50%+ more in Q3
q3_specialists = pivot[pivot['q3_specialist_score'] > 1.5]
print(q3_specialists)
```

---

### 3. Momentum Indicators

**Use case:** Detect hot/cold streaks in real-time

```sql
-- Calculate recent scoring momentum (last 10 events)
SELECT
    game_id,
    player_id,
    event_number,
    period,
    game_clock,
    points,
    points - LAG(points, 10) OVER (
        PARTITION BY game_id, player_id ORDER BY event_number
    ) as recent_points_10_events,
    fg_pct,
    fg_pct - LAG(fg_pct, 10) OVER (
        PARTITION BY game_id, player_id ORDER BY event_number
    ) as fg_pct_trend
FROM player_box_score_snapshots
WHERE game_id = '202306120DEN'
ORDER BY event_number;
```

**ML Application:**
```python
# Load momentum features
momentum_df = pd.read_sql_query(momentum_query, conn)

# Create features
momentum_df['is_hot_streak'] = momentum_df['recent_points_10_events'] >= 10
momentum_df['is_cold_streak'] = (
    (momentum_df['recent_points_10_events'] <= 2) &
    (momentum_df['fg_pct_trend'] < -10)
)

# Train model to predict next 10 events
X = momentum_df[['recent_points_10_events', 'fg_pct_trend', 'period']]
y = momentum_df['recent_points_10_events'].shift(-10)

# Model will learn: "When player is hot, how long does it last?"
```

---

### 4. Clutch Performance

**Use case:** Identify clutch performers (Q4, <5 min, <5 point diff)

```sql
-- Extract clutch moments
SELECT
    p.game_id,
    p.player_id,
    p.player_name,
    p.event_number,
    p.period,
    p.game_clock,
    p.points,
    p.fg_pct,
    t.score_diff
FROM player_box_score_snapshots p
JOIN team_box_score_snapshots t
    ON p.game_id = t.game_id
    AND p.event_number = t.event_number
    AND p.team_id = t.team_id
WHERE p.period = 4
AND p.time_elapsed_seconds >= (48 * 60 - 5 * 60)  -- Last 5 minutes
AND ABS(t.score_diff) <= 5                         -- Close game
ORDER BY p.game_id, p.event_number;
```

**ML Application:**
```python
# Load clutch data
clutch_df = pd.read_sql_query(clutch_query, conn)

# Calculate clutch stats
clutch_stats = clutch_df.groupby('player_id').agg({
    'points': 'sum',
    'fg_pct': 'mean',
    'event_number': 'count'
}).rename(columns={'event_number': 'clutch_events'})

clutch_stats['clutch_ppg'] = clutch_stats['points'] / clutch_stats['clutch_events']

# Identify clutch performers (>50 clutch events, >45% FG)
clutch_performers = clutch_stats[
    (clutch_stats['clutch_events'] > 50) &
    (clutch_stats['fg_pct'] > 45)
]

print("Clutch Performers:")
print(clutch_performers.sort_values('clutch_ppg', ascending=False))
```

---

### 5. Fatigue Analysis

**Use case:** Detect performance degradation over time

```sql
-- Compare Q1 vs Q4 performance
WITH q1_stats AS (
    SELECT
        player_id,
        AVG(fg_pct) as q1_fg_pct,
        AVG(points) as q1_avg_points
    FROM player_box_score_snapshots
    WHERE period = 1
    GROUP BY player_id
),
q4_stats AS (
    SELECT
        player_id,
        AVG(fg_pct) as q4_fg_pct,
        AVG(points) as q4_avg_points
    FROM player_box_score_snapshots
    WHERE period = 4
    GROUP BY player_id
)
SELECT
    q1.player_id,
    q1.q1_fg_pct,
    q4.q4_fg_pct,
    q4.q4_fg_pct - q1.q1_fg_pct as fg_pct_drop,
    CASE
        WHEN q4.q4_fg_pct - q1.q1_fg_pct < -10 THEN 'High Fatigue'
        WHEN q4.q4_fg_pct - q1.q1_fg_pct < -5 THEN 'Moderate Fatigue'
        ELSE 'No Fatigue'
    END as fatigue_level
FROM q1_stats q1
JOIN q4_stats q4 ON q1.player_id = q4.player_id
ORDER BY fg_pct_drop;
```

**ML Application:**
```python
# Load fatigue data
fatigue_df = pd.read_sql_query(fatigue_query, conn)

# Players with high fatigue need rest/rotation
high_fatigue_players = fatigue_df[fatigue_df['fatigue_level'] == 'High Fatigue']

# Train model to predict fatigue based on minutes played
# This can inform coaching decisions
```

---

### 6. Lineup Effectiveness

**Use case:** Find most effective 5-player lineups

```sql
-- Players on court together at each moment
-- (Simplified - in production, track substitutions)
SELECT
    game_id,
    event_number,
    team_id,
    GROUP_CONCAT(player_id) as lineup,
    MAX(points) as points_at_moment,
    score_diff
FROM player_box_score_snapshots
WHERE on_court = 1
GROUP BY game_id, event_number, team_id
HAVING COUNT(*) = 5;  -- Full lineup
```

---

### 7. Temporal Feature Engineering

**Use case:** Create time-series features for ML

```sql
-- Create lag features for prediction
SELECT
    game_id,
    player_id,
    event_number,
    period,
    game_clock,

    -- Current stats
    points,
    fg_pct,
    reb,
    ast,

    -- Lag features (10 events ago)
    LAG(points, 10) OVER w as points_lag_10,
    LAG(fg_pct, 10) OVER w as fg_pct_lag_10,

    -- Lag features (20 events ago)
    LAG(points, 20) OVER w as points_lag_20,
    LAG(fg_pct, 20) OVER w as fg_pct_lag_20,

    -- Rolling averages
    AVG(points) OVER (PARTITION BY game_id, player_id
                     ORDER BY event_number
                     ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) as points_rolling_10,

    AVG(fg_pct) OVER (PARTITION BY game_id, player_id
                      ORDER BY event_number
                      ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) as fg_pct_rolling_10

FROM player_box_score_snapshots
WINDOW w AS (PARTITION BY game_id, player_id ORDER BY event_number)
ORDER BY game_id, player_id, event_number;
```

**ML Application:**
```python
# Load features
features_df = pd.read_sql_query(feature_query, conn)

# Create additional features
features_df['momentum'] = (
    features_df['points'] - features_df['points_lag_10']
)
features_df['efficiency_trend'] = (
    features_df['fg_pct'] - features_df['fg_pct_lag_10']
)

# Train model
X = features_df[[
    'points_lag_10', 'points_lag_20',
    'fg_pct_rolling_10', 'momentum', 'efficiency_trend',
    'period'
]]
y = features_df['points'].shift(-10)  # Predict next 10 events

from sklearn.ensemble import RandomForestRegressor
model = RandomForestRegressor()
model.fit(X.dropna(), y.dropna())
```

---

## Advanced ML Patterns

### Pattern 1: Player "Engines" Extraction

```python
def extract_player_engine(player_id, conn):
    """
    Extract the nonparametric performance engine for a player.

    Returns:
        DataFrame with quarter-level patterns, fatigue indicators,
        clutch performance, momentum dynamics
    """
    query = f"""
    WITH quarters AS (
        SELECT
            game_id,
            period,
            MAX(points) - COALESCE(LAG(MAX(points)) OVER (
                PARTITION BY game_id ORDER BY period
            ), 0) as quarter_points,
            AVG(fg_pct) as quarter_fg_pct
        FROM player_box_score_snapshots
        WHERE player_id = '{player_id}'
        GROUP BY game_id, period
    ),
    clutch AS (
        SELECT
            game_id,
            AVG(fg_pct) as clutch_fg_pct,
            SUM(points) as clutch_points
        FROM player_box_score_snapshots p
        JOIN team_box_score_snapshots t USING (game_id, event_number, team_id)
        WHERE player_id = '{player_id}'
        AND period = 4 AND time_elapsed_seconds >= 2700
        AND ABS(t.score_diff) <= 5
        GROUP BY game_id
    )
    SELECT
        q.*,
        c.clutch_fg_pct,
        c.clutch_points
    FROM quarters q
    LEFT JOIN clutch c USING (game_id)
    """

    df = pd.read_sql_query(query, conn)

    return {
        'avg_quarter_pattern': df.groupby('period')['quarter_points'].mean(),
        'clutch_fg_pct': df['clutch_fg_pct'].mean(),
        'fatigue_indicator': df.groupby('period')['quarter_fg_pct'].mean().diff().mean(),
        'consistency': df['quarter_points'].std()
    }

# Use for all players
player_engines = {
    player_id: extract_player_engine(player_id, conn)
    for player_id in df['player_id'].unique()
}
```

### Pattern 2: Game State Prediction

```python
def predict_game_outcome_at_halftime(game_id, conn):
    """
    Predict final outcome using halftime snapshots.
    """
    # Load halftime state
    halftime = pd.read_sql_query(f"""
        SELECT *
        FROM team_box_score_snapshots
        WHERE game_id = '{game_id}'
        AND period = 2
        AND event_number = (
            SELECT MAX(event_number)
            FROM team_box_score_snapshots
            WHERE game_id = '{game_id}' AND period = 2
        )
    """, conn)

    # Features: halftime score diff, shooting %, momentum
    features = {
        'halftime_diff': halftime['score_diff'].iloc[0],
        'halftime_fg_pct': halftime['fg_pct'].iloc[0],
        'halftime_3p_pct': halftime['fg3_pct'].iloc[0],
        # ... more features
    }

    # Load model trained on historical halftime -> final outcomes
    # model = load_model('halftime_predictor.pkl')
    # prediction = model.predict([list(features.values())])

    return features
```

---

## Exporting for ML Frameworks

### Export to CSV

```python
# Export all snapshots for a season
df = pd.read_sql_query("""
    SELECT *
    FROM player_box_score_snapshots
    WHERE game_id LIKE '2023%'
""", conn)

df.to_csv('player_snapshots_2023.csv', index=False)
```

### Export to Parquet (Efficient for ML)

```python
df.to_parquet('player_snapshots_2023.parquet', compression='snappy')
```

### Export to TensorFlow Dataset

```python
import tensorflow as tf

# Create TensorFlow dataset
dataset = tf.data.Dataset.from_tensor_slices({
    'features': df[['points', 'fg_pct', 'reb', 'ast']].values,
    'labels': df['points'].shift(-10).fillna(0).values
})

# Save
tf.data.experimental.save(dataset, 'tf_dataset')
```

---

## Common Patterns Summary

| Pattern | Query Time | Use Case |
|---------|------------|----------|
| Halftime stats | <1s | Predict 2nd half |
| Quarter breakdown | <1s | Identify specialists |
| Momentum | 1-2s | Detect hot/cold streaks |
| Clutch | 1-2s | Find clutch performers |
| Fatigue | 1-2s | Rotation optimization |
| Lag features | 2-5s | Time-series ML |

---

## Performance Tips

1. **Index by game_id + event_number** for fast queries
2. **Partition by game_id** for large datasets
3. **Use views** for common queries (halftime, quarters, clutch)
4. **Export to Parquet** for large-scale ML training
5. **Create materialized views** for frequently-used aggregations

---

## Next Steps

1. **Generate snapshots** - Run `sqlite_pbp_processor.py`
2. **Explore data** - Use example queries above
3. **Extract features** - Create lag features, momentum indicators
4. **Train models** - Use patterns above for ML training
5. **Deploy** - Integrate with betting models, game predictions

---

**The temporal snapshot system transforms static box scores into queryable time-series data, enabling ML to understand player "engines" and game dynamics.**

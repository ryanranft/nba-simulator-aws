# Shot Chart Temporal Integration Guide

**Created:** October 18, 2025
**Purpose:** Link shot charts to temporal box score snapshots for spatial + temporal basketball analytics

---

## Overview

The shot chart temporal integration system combines **spatial data** (where shots were taken) with **temporal data** (when and under what circumstances) to enable advanced basketball analytics that traditional systems can't answer.

**Traditional shot charts:** Static images showing all shots from a game
**Temporal shot charts:** Queryable database of shots with full game context

---

## What This Enables

### Questions You Can Answer

**Spatial + Temporal:**
- "Show LeBron's shot chart in Q4 clutch moments"
- "Where did Curry shoot from when his team was trailing by 5+?"
- "How did Kobe's shot selection change from Q1 to Q4?"
- "What's Harden's 3PT% from the top of the key when leading vs trailing?"

**Game State Analysis:**
- "Do players take more 3-pointers when trailing?"
- "How does shot distance change in the final 2 minutes?"
- "Are contested shots more common in clutch situations?"

**Player Dynamics:**
- "Does Player A shoot better when assisted?"
- "How does efficiency change by shot zone and quarter?"
- "What's the correlation between momentum and shot selection?"

### ML Applications

1. **Shot Selection Prediction:** Predict shot location based on game state
2. **Efficiency Optimization:** Find optimal shot zones by situation
3. **Clutch Performance:** Identify clutch shooters by zone
4. **Defensive Strategy:** Understand how opponents shoot under pressure
5. **Lineup Analysis:** How lineups affect shot distribution

---

## System Architecture

### Data Flow

```
Basketball Reference PBP
         ↓
game_play_by_play (shot events with x,y coordinates)
         ↓
SQLitePBPProcessor → player_box_score_snapshots
                  → team_box_score_snapshots
         ↓
ShotChartTemporalProcessor → shot_event_snapshots
         ↓
ML Queries (spatial + temporal analytics)
```

### Database Tables

#### 1. `shot_event_snapshots` (Main Table)

**Purpose:** Every shot with full temporal + spatial context

**Key fields:**
```sql
shot_event_snapshots:
  -- Identifiers
  game_id, event_number, shot_id, player_id

  -- Spatial (WHERE)
  shot_x, shot_y, shot_distance, shot_zone

  -- Temporal (WHEN)
  period, game_clock, time_elapsed_seconds

  -- Context (UNDER WHAT CIRCUMSTANCES)
  score_diff, is_leading, is_clutch
  player_points_before, player_fg_pct_before
  player_recent_points, team_run

  -- Shot details
  shot_made, shot_type, is_assisted
```

**Shot zones:**
- `paint` - 0-5 feet from basket
- `short_mid` - 5-10 feet
- `long_mid` - 10-16 feet
- `corner_three` - 3PT from corners
- `above_break_three` - 3PT from top
- `free_throw` - Free throws
- `deep_two` - Long 2-pointers (16+ feet)

#### 2. `player_shooting_zones` (Aggregation Table)

**Purpose:** Pre-computed shooting efficiency by zone for fast ML queries

**Key fields:**
- Paint FG%
- Mid-range FG%
- Corner 3 FG%
- Above-break 3 FG%
- Clutch FG%
- Assisted vs unassisted FG%

#### 3. Views for Quick Access

- `vw_shot_chart_by_quarter` - Shot charts by quarter
- `vw_clutch_shot_charts` - Clutch shooting only
- `vw_shots_by_game_state` - Shots when leading/trailing
- `vw_shots_by_momentum` - Shots during hot/cold streaks

---

## Court Coordinate System

### NBA Court Dimensions

```
Court: 50 feet wide × 47 feet long
Basket location: (25, 5.25)

         0                      25                      50
     0   +------------------------+------------------------+
         |                        |                        |
         |         Corner         |         Corner         |
         |         Three          |         Three          |
    10   |                        |                        |
         |                       ◉  ← Basket (25, 5.25)   |
         |        Paint           |                        |
    20   |                        |                        |
         |      Mid-Range         |                        |
         |                        |                        |
    30   |                        |                        |
         |      Above-Break       |                        |
         |      Three-Point       |                        |
    40   |                        |                        |
         |                        |                        |
    47   +------------------------+------------------------+

3-point line:
  - 22 feet in corners (x < 10 or x > 40)
  - 23.75 feet at top of key
```

---

## Usage Examples

### 1. Create Tables

```bash
cd /Users/ryanranft/nba-simulator-aws

# Create shot chart tables
sqlite3 /tmp/basketball_reference_boxscores.db < sql/shot_chart_temporal_integration.sql
```

### 2. Process Shot Events

```python
from scripts.pbp_to_boxscore.shot_chart_temporal_processor import ShotChartTemporalProcessor

processor = ShotChartTemporalProcessor()

# Process single game
shots_processed = processor.process_game('202306120DEN')
print(f"Processed {shots_processed} shots")

# Process all games
games = processor.get_available_games()
for game_id in games:
    processor.process_game(game_id)

processor.close()
```

### 3. Run Demo

```bash
cd /Users/ryanranft/nba-simulator-aws

# Create sample data and demonstrate capabilities
python3 scripts/pbp_to_boxscore/demo_shot_chart_temporal.py
```

**Demo output:**
- 17 sample shots with coordinates
- 6 query demonstrations
- Spatial + temporal analytics examples

---

## ML Query Examples

### Query 1: Shot Chart by Quarter

```sql
-- Get player's shot distribution by quarter
SELECT
    period as quarter,
    shot_zone,
    COUNT(*) as shots,
    SUM(CASE WHEN shot_made THEN 1 ELSE 0 END) as makes,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct
FROM shot_event_snapshots
WHERE player_id = 'jamesle01'
GROUP BY period, shot_zone
ORDER BY period, shot_zone;
```

**ML Application:** Identify quarter-specific shot selection patterns (e.g., "LeBron shoots more 3s in Q1")

### Query 2: Clutch Shot Chart

```sql
-- Where do players shoot in clutch moments?
SELECT
    player_id,
    player_name,
    shot_x,
    shot_y,
    shot_zone,
    COUNT(*) as clutch_shots,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as clutch_fg_pct
FROM shot_event_snapshots
WHERE is_clutch = 1  -- Q4, <5 min, <5 pt diff
GROUP BY player_id, shot_x, shot_y, shot_zone
HAVING clutch_shots >= 5
ORDER BY clutch_fg_pct DESC;
```

**ML Application:** Build clutch performer models, predict shot success in critical moments

### Query 3: Shot Selection by Game State

```sql
-- How does shot selection change when leading vs trailing?
SELECT
    is_leading,
    shot_zone,
    shot_type,
    COUNT(*) as shots,
    AVG(shot_distance) as avg_distance,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct
FROM shot_event_snapshots
WHERE ABS(score_diff) <= 10  -- Close games only
GROUP BY is_leading, shot_zone, shot_type
ORDER BY is_leading DESC, shots DESC;
```

**ML Application:** Understand strategic adjustments, predict shot selection based on score

### Query 4: Assisted vs Unassisted Efficiency

```sql
-- Where are players most efficient with/without assists?
SELECT
    player_id,
    shot_zone,
    is_assisted,
    COUNT(*) as shots,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct
FROM shot_event_snapshots
WHERE shot_type != 'FT'
GROUP BY player_id, shot_zone, is_assisted
HAVING shots >= 10
ORDER BY player_id, shot_zone, is_assisted;
```

**ML Application:** Optimize offensive schemes, identify players who need ball movement

### Query 5: Momentum-Based Shooting

```sql
-- How does recent performance affect shot selection?
SELECT
    CASE
        WHEN player_recent_fg_pct >= 60 THEN 'Hot'
        WHEN player_recent_fg_pct >= 40 THEN 'Average'
        ELSE 'Cold'
    END as momentum,
    shot_zone,
    COUNT(*) as shots,
    AVG(shot_distance) as avg_distance,
    ROUND(AVG(CASE WHEN shot_made THEN 1.0 ELSE 0.0 END) * 100, 1) as fg_pct
FROM shot_event_snapshots
WHERE player_recent_fg_pct IS NOT NULL
GROUP BY momentum, shot_zone
ORDER BY momentum, shots DESC;
```

**ML Application:** Detect "hot hand" effects, predict when players will force shots

### Query 6: Shot Coordinates for Heatmaps

```python
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

conn = sqlite3.connect('/tmp/basketball_reference_boxscores.db')

# Get shot coordinates for visualization
df = pd.read_sql_query("""
    SELECT
        shot_x,
        shot_y,
        shot_made,
        shot_zone,
        is_clutch
    FROM shot_event_snapshots
    WHERE player_id = 'curryst01'
    AND period = 4
""", conn)

# Create heatmap
plt.figure(figsize=(10, 9))
plt.hexbin(df['shot_x'], df['shot_y'],
           C=df['shot_made'],
           gridsize=20,
           cmap='RdYlGn')
plt.colorbar(label='FG%')
plt.title("Steph Curry Q4 Shot Chart")
plt.xlabel("Court Width (feet)")
plt.ylabel("Court Length (feet)")
plt.show()
```

---

## Advanced ML Features

### Extract Spatial Features

```python
def extract_spatial_features(game_id, player_id, conn):
    """
    Extract spatial shooting features for ML models.

    Returns features like:
    - Zone-based FG%
    - Shot distance distribution
    - Assisted % by zone
    - Clutch efficiency by zone
    """
    query = f"""
    SELECT
        -- Paint shooting
        AVG(CASE WHEN shot_zone = 'paint' AND shot_made THEN 1.0 ELSE 0.0 END) as paint_fg_pct,
        COUNT(CASE WHEN shot_zone = 'paint' THEN 1 END) as paint_attempts,

        -- Mid-range shooting
        AVG(CASE WHEN shot_zone LIKE '%mid%' AND shot_made THEN 1.0 ELSE 0.0 END) as mid_fg_pct,
        COUNT(CASE WHEN shot_zone LIKE '%mid%' THEN 1 END) as mid_attempts,

        -- Three-point shooting
        AVG(CASE WHEN shot_zone LIKE '%three%' AND shot_made THEN 1.0 ELSE 0.0 END) as three_fg_pct,
        COUNT(CASE WHEN shot_zone LIKE '%three%' THEN 1 END) as three_attempts,

        -- Clutch efficiency
        AVG(CASE WHEN is_clutch = 1 AND shot_made THEN 1.0 ELSE 0.0 END) as clutch_fg_pct,

        -- Assisted rate
        AVG(CASE WHEN is_assisted THEN 1.0 ELSE 0.0 END) as assisted_rate,

        -- Average distance
        AVG(shot_distance) as avg_shot_distance

    FROM shot_event_snapshots
    WHERE game_id = '{game_id}' AND player_id = '{player_id}'
    """

    return pd.read_sql_query(query, conn)
```

### Time-Series Shot Analysis

```python
def analyze_shot_selection_over_time(player_id, conn):
    """
    Analyze how shot selection changes over the course of a game.

    Reveals patterns like:
    - "Player shoots more 3s when tired (Q4)"
    - "Shot distance decreases in 2nd half"
    - "Paint penetration drops in clutch"
    """
    query = f"""
    SELECT
        period,
        time_elapsed_seconds,
        shot_zone,
        AVG(shot_distance) as avg_distance,
        COUNT(*) as shot_frequency
    FROM shot_event_snapshots
    WHERE player_id = '{player_id}'
    GROUP BY period, time_elapsed_seconds, shot_zone
    ORDER BY time_elapsed_seconds
    """

    df = pd.read_sql_query(query, conn)

    # Plot shot selection over time
    import seaborn as sns

    sns.lineplot(data=df, x='time_elapsed_seconds',
                 y='avg_distance', hue='shot_zone')
    plt.title(f"{player_id} - Shot Distance Over Time")
    plt.show()
```

---

## Integration with Temporal Box Scores

### Combined Spatial + Temporal Query

```sql
-- Find players who shoot better from certain zones when hot
SELECT
    p.player_id,
    p.player_name,
    s.shot_zone,

    -- Recent performance (from player_box_score_snapshots)
    p.fg_pct as current_fg_pct,

    -- Shot details (from shot_event_snapshots)
    COUNT(*) as shots,
    AVG(s.shot_made) as zone_fg_pct,

    -- Score context (from team_box_score_snapshots)
    AVG(t.score_diff) as avg_score_diff

FROM shot_event_snapshots s
JOIN player_box_score_snapshots p
    ON s.game_id = p.game_id
    AND s.event_number = p.event_number
    AND s.player_id = p.player_id
JOIN team_box_score_snapshots t
    ON s.game_id = t.game_id
    AND s.event_number = t.event_number
    AND s.team_id = t.team_id

WHERE p.fg_pct >= 50  -- Only when player is shooting well
GROUP BY p.player_id, s.shot_zone
HAVING shots >= 5
ORDER BY zone_fg_pct DESC;
```

---

## Performance Considerations

### Indexing Strategy

The following indexes are created automatically:

```sql
-- Fast game lookups
CREATE INDEX idx_shot_snapshots_game
  ON shot_event_snapshots(game_id, event_number);

-- Fast player lookups
CREATE INDEX idx_shot_snapshots_player
  ON shot_event_snapshots(player_id, game_id);

-- Fast spatial queries
CREATE INDEX idx_shot_snapshots_location
  ON shot_event_snapshots(shot_x, shot_y, shot_made);

-- Fast clutch queries
CREATE INDEX idx_shot_snapshots_clutch
  ON shot_event_snapshots(is_clutch, shot_made);

-- Fast zone queries
CREATE INDEX idx_shot_snapshots_zone
  ON shot_event_snapshots(shot_zone, shot_type);
```

### Query Optimization Tips

1. **Use views for common queries** - Pre-defined views are faster
2. **Filter by game_id first** - Reduces dataset size
3. **Use aggregation tables** - `player_shooting_zones` for season-level queries
4. **Limit spatial precision** - Round coordinates for heatmaps
5. **Cache common results** - Store frequently-used aggregations

---

## Data Quality

### Shot Coordinate Availability

**Basketball Reference:**
- **1946-2000:** No shot coordinates (only PBP descriptions)
- **2000-2010:** Limited coordinates (some games)
- **2010-present:** Full coordinates available

**ESPN/NBA API:**
- **1996-2010:** Partial coordinates
- **2010-present:** Full coordinates with defender tracking

### Handling Missing Coordinates

```python
def classify_shot_zone_from_description(description: str) -> str:
    """
    Classify shot zone from PBP description when coordinates unavailable.

    Examples:
    - "makes layup" → paint
    - "makes 3-pt jump shot from 25 ft" → above_break_three
    - "makes 15-ft jump shot" → long_mid
    """
    desc_lower = description.lower()

    if 'layup' in desc_lower or 'dunk' in desc_lower:
        return 'paint'
    elif '3-pt' in desc_lower or 'three' in desc_lower:
        if 'corner' in desc_lower:
            return 'corner_three'
        return 'above_break_three'
    elif 'free throw' in desc_lower:
        return 'free_throw'
    else:
        # Parse distance if available
        distance_match = re.search(r'(\d+)-ft', desc_lower)
        if distance_match:
            dist = int(distance_match.group(1))
            if dist <= 5:
                return 'paint'
            elif dist <= 10:
                return 'short_mid'
            elif dist <= 16:
                return 'long_mid'
        return 'unknown'
```

---

## Next Steps

1. **Run demo** - `python3 scripts/pbp_to_boxscore/demo_shot_chart_temporal.py`
2. **Process real data** - Wait for Basketball Reference PBP scrapers
3. **Build visualizations** - Create heatmap generators
4. **Train ML models** - Use spatial + temporal features
5. **Integrate with betting** - Link to betting models

---

## Related Documentation

- **Temporal Box Scores:** `docs/ML_TEMPORAL_QUERIES.md`
- **System Comparison:** `docs/TEMPORAL_BOX_SCORE_SYSTEMS_COMPARISON.md`
- **PBP Processing:** `docs/PBP_TO_BOXSCORE_SYSTEM.md`
- **Basketball Reference:** `docs/BASKETBALL_REFERENCE_PBP_SYSTEM.md`

---

## Summary

The shot chart temporal integration system transforms static shot charts into **queryable spatial + temporal data**, enabling:

✅ Shot charts at any game moment (halftime, clutch, etc.)
✅ Shot selection by game state (leading/trailing)
✅ Zone-based efficiency analysis
✅ Assisted vs unassisted breakdowns
✅ Clutch shooting identification
✅ Spatial + temporal ML features

**This unlocks player "spatial engines" - understanding not just WHERE players shoot, but WHEN and UNDER WHAT CIRCUMSTANCES.**

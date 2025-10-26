# NBA Temporal Panel Data - Query Guide

> **⚠️ LARGE FILE WARNING (996 lines)**
>
> **For Claude Code:** Only read this file when:
> - Implementing temporal query functionality
> - Writing database query code for temporal features
> - Debugging temporal query performance issues
>
> **DO NOT read at session start** - this file is an implementation reference, not initialization documentation.
>
> **Best practice:** Read specific sections as needed (check Table of Contents), don't read entire file.

**Version:** 1.0
**Last Updated:** October 7, 2025
**Audience:** Developers, data analysts, researchers

---

## Overview

This guide provides **practical SQL examples and Python code** for querying the NBA Temporal Panel Data System.

**Core capability:** Query cumulative NBA statistics at any exact moment in time with millisecond precision.

**Example questions this system can answer:**
- "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"
- "What was the league average pace at 11:23:45 PM on March 15, 2023?"
- "Show me all games happening at exactly 9:00 PM ET on any date"
- "What was LeBron's age (to the second) when he scored his 30,000th point?"

---

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [Database Schema Overview](#database-schema-overview)
3. [Common Query Patterns](#common-query-patterns)
4. [Python Helper Functions](#python-helper-functions)
5. [Performance Optimization](#performance-optimization)
6. [Data Precision Levels](#data-precision-levels)
7. [Advanced Use Cases](#advanced-use-cases)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start Examples

### Example 1: Get Player Snapshot at Exact Timestamp

**Question:** "What were Kobe Bryant's career stats at exactly 7:02:34.56 PM CT on June 19, 2016?"

**SQL Query:**
```sql
-- Get Kobe's snapshot at exact timestamp
SELECT
    ps.snapshot_time,
    ps.games_played,
    ps.career_points,
    ps.career_rebounds,
    ps.career_assists,
    ps.career_fg_pct,
    ps.career_3pt_pct,
    pb.birth_date,
    EXTRACT(EPOCH FROM (ps.snapshot_time - pb.birth_date)) / (365.25 * 24 * 60 * 60) AS age_years
FROM
    get_player_snapshot_at_time(
        (SELECT player_id FROM players WHERE name = 'Kobe Bryant'),
        '2016-06-19 19:02:34.560-05:00'::TIMESTAMPTZ
    ) AS ps
JOIN
    player_biographical pb ON ps.player_id = pb.player_id;
```

**Expected Output:**
```
snapshot_time          | games_played | career_points | age_years
-----------------------+--------------+---------------+-----------
2016-06-19 19:02:34.56 | 1,346        | 33,636        | 37.8145
```

**Python Code:**
```python
import psycopg2
from datetime import datetime
import pytz

def get_player_stats_at_time(player_name, timestamp_str, timezone='America/Chicago'):
    """
    Get player cumulative statistics at exact timestamp.

    Args:
        player_name: Full player name (e.g., "Kobe Bryant")
        timestamp_str: ISO format timestamp (e.g., "2016-06-19T19:02:34.560")
        timezone: Timezone name (default: Chicago)

    Returns:
        dict: Player statistics snapshot
    """
    conn = psycopg2.connect(
        host="your-db-host.rds.amazonaws.com",
        database="nba_temporal_db",
        user="your_user",
        password="your_password"
    )

    # Convert to timezone-aware timestamp
    tz = pytz.timezone(timezone)
    dt = datetime.fromisoformat(timestamp_str)
    dt_aware = tz.localize(dt)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            ps.snapshot_time,
            ps.games_played,
            ps.career_points,
            ps.career_rebounds,
            ps.career_assists,
            ps.career_fg_pct,
            EXTRACT(EPOCH FROM (ps.snapshot_time - pb.birth_date)) / (365.25 * 24 * 60 * 60) AS age_years
        FROM
            get_player_snapshot_at_time(
                (SELECT player_id FROM players WHERE name = %s),
                %s
            ) AS ps
        JOIN
            player_biographical pb ON ps.player_id = pb.player_id
    """, (player_name, dt_aware))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return {
            'snapshot_time': result[0],
            'games_played': result[1],
            'career_points': result[2],
            'career_rebounds': result[3],
            'career_assists': result[4],
            'career_fg_pct': result[5],
            'age_years': float(result[6])
        }
    return None

# Usage
stats = get_player_stats_at_time("Kobe Bryant", "2016-06-19T19:02:34.560")
print(f"At {stats['snapshot_time']}, Kobe had {stats['career_points']} career points")
print(f"He was {stats['age_years']:.4f} years old")
```

---

### Example 2: Get All Games at Exact Timestamp

**Question:** "What games were being played at exactly 9:00 PM ET on March 15, 2023?"

**SQL Query:**
```sql
-- Find all games active at specific timestamp
SELECT
    g.game_id,
    g.home_team,
    g.away_team,
    gs.current_score_home,
    gs.current_score_away,
    gs.quarter,
    gs.game_clock_seconds,
    gs.game_state
FROM
    games g
JOIN
    game_states gs ON g.game_id = gs.game_id
WHERE
    gs.state_time = (
        SELECT MAX(state_time)
        FROM game_states
        WHERE game_id = g.game_id
          AND state_time <= '2023-03-15 21:00:00.000-04:00'::TIMESTAMPTZ
    )
    AND g.game_date = '2023-03-15'
ORDER BY
    g.game_id;
```

**Python Code:**
```python
def get_active_games_at_time(timestamp_str, timezone='America/New_York'):
    """
    Get all NBA games active at exact timestamp.

    Returns:
        list: List of active games with current scores
    """
    conn = psycopg2.connect(...)

    tz = pytz.timezone(timezone)
    dt = datetime.fromisoformat(timestamp_str)
    dt_aware = tz.localize(dt)

    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            g.game_id,
            g.home_team,
            g.away_team,
            gs.current_score_home,
            gs.current_score_away,
            gs.quarter,
            gs.game_clock_seconds,
            gs.game_state
        FROM
            games g
        JOIN
            game_states gs ON g.game_id = gs.game_id
        WHERE
            gs.state_time = (
                SELECT MAX(state_time)
                FROM game_states
                WHERE game_id = g.game_id
                  AND state_time <= %s
            )
            AND g.game_date = %s
        ORDER BY
            g.game_id
    """, (dt_aware, dt_aware.date()))

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            'game_id': r[0],
            'matchup': f"{r[2]} @ {r[1]}",
            'score': f"{r[4]}-{r[3]}",
            'quarter': r[5],
            'time_remaining': r[6],
            'status': r[7]
        }
        for r in results
    ]

# Usage
games = get_active_games_at_time("2023-03-15T21:00:00.000")
for game in games:
    print(f"{game['matchup']}: {game['score']} (Q{game['quarter']})")
```

---

### Example 3: Calculate Player Age at Event

**Question:** "How old was LeBron James (to the second) when he scored his 30,000th point?"

**SQL Query:**
```sql
-- Find timestamp when LeBron reached 30,000 career points
WITH lebron_events AS (
    SELECT
        te.wall_clock_utc,
        te.event_data,
        SUM((te.event_data->>'points_scored')::INTEGER) OVER (
            ORDER BY te.wall_clock_utc
        ) AS cumulative_points
    FROM
        temporal_events te
    WHERE
        te.player_id = (SELECT player_id FROM players WHERE name = 'LeBron James')
        AND te.event_type = 'made_shot'
    ORDER BY
        te.wall_clock_utc
)
SELECT
    le.wall_clock_utc AS milestone_time,
    le.cumulative_points,
    pb.birth_date,
    calculate_player_age(
        (SELECT player_id FROM players WHERE name = 'LeBron James'),
        le.wall_clock_utc
    ) AS age_at_milestone
FROM
    lebron_events le
JOIN
    player_biographical pb ON pb.player_id = (SELECT player_id FROM players WHERE name = 'LeBron James')
WHERE
    le.cumulative_points >= 30000
ORDER BY
    le.wall_clock_utc
LIMIT 1;
```

**Expected Output:**
```
milestone_time         | cumulative_points | age_at_milestone
-----------------------+-------------------+------------------
2018-01-23 20:37:22.45 | 30,001            | 33 years, 154 days, 8 hours, 37 minutes, 22 seconds
```

**Python Code:**
```python
def get_milestone_age(player_name, milestone_type, milestone_value):
    """
    Calculate player age when reaching career milestone.

    Args:
        player_name: Full player name
        milestone_type: 'points', 'rebounds', 'assists', etc.
        milestone_value: Milestone value (e.g., 30000)

    Returns:
        dict: Milestone timestamp and age
    """
    conn = psycopg2.connect(...)
    cursor = conn.cursor()

    cursor.execute(f"""
        WITH player_events AS (
            SELECT
                te.wall_clock_utc,
                te.event_data,
                SUM((te.event_data->>'{milestone_type}')::INTEGER) OVER (
                    ORDER BY te.wall_clock_utc
                ) AS cumulative_{milestone_type}
            FROM
                temporal_events te
            WHERE
                te.player_id = (SELECT player_id FROM players WHERE name = %s)
            ORDER BY
                te.wall_clock_utc
        )
        SELECT
            pe.wall_clock_utc,
            pe.cumulative_{milestone_type},
            calculate_player_age(
                (SELECT player_id FROM players WHERE name = %s),
                pe.wall_clock_utc
            )
        FROM
            player_events pe
        WHERE
            pe.cumulative_{milestone_type} >= %s
        ORDER BY
            pe.wall_clock_utc
        LIMIT 1
    """, (player_name, player_name, milestone_value))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return {
            'milestone_time': result[0],
            'cumulative_value': result[1],
            'age': result[2]
        }
    return None

# Usage
milestone = get_milestone_age("LeBron James", "points", 30000)
print(f"LeBron reached 30,000 points at {milestone['milestone_time']}")
print(f"He was {milestone['age']}")
```

---

## Database Schema Overview

### Core Temporal Tables

**1. `temporal_events`** (500M+ rows)
- Event-level timestamps with millisecond precision
- Full play-by-play data in JSONB
- Wall clock + game clock dual timestamps
- Data source and precision tracking

**2. `player_snapshots`** (50M+ rows)
- Pre-computed cumulative statistics at checkpoints
- Updated after each game/quarter
- Fast snapshot queries (< 1 second)

**3. `game_states`** (10M+ rows)
- Game state reconstruction at timestamps
- Current scores, quarter, time remaining
- Active lineups at any moment

**4. `player_biographical`** (5K+ rows)
- Birth dates for age calculations
- Birth date precision flags
- Career start/end dates

**See `docs/phases/PHASE_3_DATABASE.md` Sub-3.0005 for complete schemas.**

---

## Common Query Patterns

### Pattern 1: Player Snapshot Queries

**Use the stored procedure for fast lookups:**

```sql
-- Get snapshot at exact time (uses pre-computed checkpoints)
SELECT * FROM get_player_snapshot_at_time(
    player_id := 123,
    timestamp := '2016-06-19 19:02:34.560-05:00'::TIMESTAMPTZ
);
```

**Behind the scenes:**
1. Looks for nearest pre-computed snapshot before timestamp
2. If found (< 1 second), returns immediately
3. If not found, aggregates events from nearest checkpoint (2-5 seconds)

### Pattern 2: Time Range Queries

**Get all events in time window:**

```sql
-- All shots in last 2 minutes of game
SELECT
    te.wall_clock_utc,
    te.player_id,
    te.event_data->>'shot_distance' AS distance,
    te.event_data->>'shot_made' AS made
FROM
    temporal_events te
WHERE
    te.game_id = '401234567'
    AND te.event_type = 'shot'
    AND te.quarter = 4
    AND te.game_clock_seconds <= 120
ORDER BY
    te.wall_clock_utc DESC;
```

**Performance tip:** BRIN indexes are optimized for sequential time-range scans.

### Pattern 3: Cross-Game Temporal Queries

**Compare multiple players at same career stage:**

```sql
-- Compare LeBron vs Jordan at age 28
WITH player_stats AS (
    SELECT
        ps.player_id,
        p.name,
        ps.career_points,
        ps.career_fg_pct,
        EXTRACT(EPOCH FROM (ps.snapshot_time - pb.birth_date)) / (365.25 * 24 * 60 * 60) AS age_years
    FROM
        player_snapshots ps
    JOIN
        players p ON ps.player_id = p.player_id
    JOIN
        player_biographical pb ON ps.player_id = pb.player_id
    WHERE
        p.name IN ('LeBron James', 'Michael Jordan')
)
SELECT
    name,
    MIN(career_points) FILTER (WHERE age_years >= 28 AND age_years < 28.1) AS points_at_age_28
FROM
    player_stats
GROUP BY
    name;
```

### Pattern 4: Event Sequence Analysis

**Find momentum shifts (scoring runs):**

```sql
-- Find all 10-0 runs in last 2 minutes
WITH scored_events AS (
    SELECT
        game_id,
        wall_clock_utc,
        team_id,
        event_data->>'points_scored' AS points,
        SUM(CASE WHEN team_id = home_team THEN points ELSE -points END)
            OVER (PARTITION BY game_id ORDER BY wall_clock_utc
                  ROWS BETWEEN 10 PRECEDING AND CURRENT ROW) AS score_diff_10_events
    FROM
        temporal_events
    WHERE
        quarter = 4
        AND game_clock_seconds <= 120
)
SELECT
    game_id,
    wall_clock_utc,
    score_diff_10_events
FROM
    scored_events
WHERE
    ABS(score_diff_10_events) >= 10;
```

---

## Python Helper Functions

### Timestamp Conversion Utilities

```python
import pytz
from datetime import datetime, timedelta

def parse_timestamp(timestamp_str, timezone='America/Chicago'):
    """
    Convert timestamp string to timezone-aware datetime.

    Args:
        timestamp_str: ISO format or common formats
        timezone: IANA timezone name

    Returns:
        datetime: Timezone-aware datetime object
    """
    tz = pytz.timezone(timezone)

    # Try ISO format first
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return tz.localize(dt) if dt.tzinfo is None else dt.astimezone(tz)
    except ValueError:
        pass

    # Try common formats
    formats = [
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            return tz.localize(dt)
        except ValueError:
            continue

    raise ValueError(f"Could not parse timestamp: {timestamp_str}")


def timestamp_to_game_clock(timestamp, game_start_time, quarter_length=720):
    """
    Convert wall clock timestamp to game clock.

    Args:
        timestamp: Wall clock timestamp
        game_start_time: Game start timestamp
        quarter_length: Seconds per quarter (default: 12 min = 720s)

    Returns:
        tuple: (quarter, seconds_remaining)
    """
    elapsed = (timestamp - game_start_time).total_seconds()

    # Estimate quarter (rough approximation)
    quarter = min(int(elapsed / quarter_length) + 1, 4)

    # Seconds remaining in quarter
    quarter_elapsed = elapsed % quarter_length
    seconds_remaining = quarter_length - quarter_elapsed

    return quarter, int(seconds_remaining)
```

### Batch Query Utilities

```python
def get_snapshots_for_multiple_players(player_names, timestamp):
    """
    Get snapshots for multiple players at same timestamp.

    Args:
        player_names: List of player names
        timestamp: Timestamp to query

    Returns:
        dict: Player name -> snapshot dict
    """
    conn = psycopg2.connect(...)
    cursor = conn.cursor()

    placeholders = ','.join(['%s'] * len(player_names))

    cursor.execute(f"""
        SELECT
            p.name,
            ps.career_points,
            ps.career_rebounds,
            ps.career_assists,
            ps.career_fg_pct
        FROM
            players p
        CROSS JOIN LATERAL
            get_player_snapshot_at_time(p.player_id, %s) AS ps
        WHERE
            p.name IN ({placeholders})
    """, [timestamp] + player_names)

    results = cursor.fetchall()
    cursor.close()
    conn.close()

    return {
        name: {
            'points': points,
            'rebounds': rebounds,
            'assists': assists,
            'fg_pct': fg_pct
        }
        for name, points, rebounds, assists, fg_pct in results
    }

# Usage
snapshots = get_snapshots_for_multiple_players(
    ["LeBron James", "Stephen Curry", "Kevin Durant"],
    "2023-03-15T21:00:00"
)
```

---

## Performance Optimization

### 1. Use Pre-Computed Snapshots

**Fast (< 1 second):**
```sql
-- Use stored procedure (checks pre-computed snapshots first)
SELECT * FROM get_player_snapshot_at_time(player_id, timestamp);
```

**Slow (2-5 seconds):**
```sql
-- Direct aggregation (scans all events)
SELECT SUM(points) FROM temporal_events WHERE player_id = 123 AND wall_clock_utc <= timestamp;
```

### 2. Leverage BRIN Indexes

**Efficient (sequential scan):**
```sql
-- Query in time order (BRIN index friendly)
SELECT * FROM temporal_events
WHERE wall_clock_utc BETWEEN '2023-01-01' AND '2023-01-31'
ORDER BY wall_clock_utc;
```

**Inefficient (random access):**
```sql
-- Random time lookups (defeats BRIN index)
SELECT * FROM temporal_events
WHERE wall_clock_utc IN ('2023-01-05 14:23:11', '2021-03-15 19:45:33', ...);
```

### 3. Filter by Precision Level

**For high-precision analysis:**
```sql
-- Only use millisecond-precision data
SELECT * FROM temporal_events
WHERE precision_level = 'millisecond'
  AND wall_clock_utc >= '2020-01-01';  -- Recent data only
```

**For broader analysis:**
```sql
-- Accept minute-level precision
SELECT * FROM temporal_events
WHERE precision_level IN ('millisecond', 'second', 'minute');
```

### 4. Partition by Year (Future Optimization)

**If queries become slow, partition `temporal_events` by year:**
```sql
CREATE TABLE temporal_events_2023 PARTITION OF temporal_events
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
```

---

## Data Precision Levels

### Understanding Precision Flags

Every event has a `precision_level` field:

| Level | Description | Timestamp Example | Data Source | Era |
|-------|-------------|-------------------|-------------|-----|
| `millisecond` | Millisecond precision | `2021-01-16T00:40:31.300Z` | NBA Live API | 2020+ (future) |
| `second` | Second precision | `2019-06-19T19:02:34Z` | NBA Stats API | 2013-2019 |
| `minute` | Minute precision | `2015-03-15T19:37:00Z` | NBA Stats PlayByPlayV2 | 1993-2012 |
| `game` | Game-level only | `2010-01-15T00:00:00Z` | Basketball Reference | 1946-1992 |
| `unknown` | Unknown precision | `NULL` | Legacy data | Various |

### Querying by Precision

**Filter to high-confidence data:**
```sql
-- Research requiring millisecond precision
SELECT * FROM temporal_events
WHERE precision_level = 'millisecond'
  AND wall_clock_utc >= '2020-01-01';
```

**Aggregate with precision grouping:**
```sql
-- Count events by precision level
SELECT
    precision_level,
    COUNT(*) AS event_count,
    MIN(wall_clock_utc) AS earliest_event,
    MAX(wall_clock_utc) AS latest_event
FROM
    temporal_events
GROUP BY
    precision_level
ORDER BY
    earliest_event;
```

### Birth Date Precision

Players have birth date precision flags:

```sql
SELECT
    p.name,
    pb.birth_date,
    pb.birth_date_precision,
    CASE
        WHEN pb.birth_date_precision = 'day' THEN 'Age accurate to seconds'
        WHEN pb.birth_date_precision = 'month' THEN 'Age accurate to ~15 days'
        WHEN pb.birth_date_precision = 'year' THEN 'Age accurate to ~6 months'
        ELSE 'Age unknown'
    END AS age_accuracy
FROM
    players p
JOIN
    player_biographical pb ON p.player_id = pb.player_id
WHERE
    p.name = 'Kobe Bryant';
```

---

## Advanced Use Cases

### Use Case 1: Video Frame Synchronization

**Goal:** Sync video feed (30fps) with player stats

**30fps = 33.33ms per frame**

```python
def get_stats_for_video_frame(player_id, frame_timestamp):
    """
    Get player stats at exact video frame timestamp.

    Args:
        player_id: Player ID
        frame_timestamp: Frame timestamp (millisecond precision)

    Returns:
        dict: Player snapshot at frame time
    """
    conn = psycopg2.connect(...)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM get_player_snapshot_at_time(%s, %s)
    """, (player_id, frame_timestamp))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    return {
        'timestamp': frame_timestamp,
        'career_points': result[2],
        'age_years': calculate_age(result[0], frame_timestamp)
    }

# Video sync loop
video_start = datetime(2016, 6, 19, 19, 0, 0)
fps = 30
frame_duration = timedelta(milliseconds=1000/fps)

for frame_num in range(1000):  # 1000 frames
    frame_time = video_start + frame_num * frame_duration
    stats = get_stats_for_video_frame(kobe_id, frame_time)
    overlay_stats_on_frame(frame_num, stats)
```

### Use Case 2: High-Frequency Panel Regression

**Goal:** Statistical analysis like financial markets data

```python
import pandas as pd
import statsmodels.api as sm

def create_panel_dataframe(player_ids, start_time, end_time, freq='1S'):
    """
    Create panel dataframe at regular intervals.

    Args:
        player_ids: List of player IDs
        start_time: Start timestamp
        end_time: End timestamp
        freq: Pandas frequency ('1S' = 1 second, '1min' = 1 minute)

    Returns:
        pd.DataFrame: Panel data with MultiIndex (player_id, timestamp)
    """
    # Generate timestamp grid
    timestamps = pd.date_range(start_time, end_time, freq=freq)

    # Query snapshots for all players at all timestamps
    data = []
    for player_id in player_ids:
        for ts in timestamps:
            snapshot = get_player_snapshot_at_time(player_id, ts)
            if snapshot:
                data.append({
                    'player_id': player_id,
                    'timestamp': ts,
                    'career_points': snapshot['career_points'],
                    'career_fg_pct': snapshot['career_fg_pct'],
                    'age_years': snapshot['age_years']
                })

    df = pd.DataFrame(data)
    df.set_index(['player_id', 'timestamp'], inplace=True)
    return df

# Panel regression
panel_df = create_panel_dataframe([23, 456, 789], '2016-06-19 18:00:00', '2016-06-19 22:00:00', freq='1min')

# Fixed effects regression
model = sm.OLS.from_formula('career_fg_pct ~ age_years + C(player_id)', data=panel_df)
results = model.fit()
print(results.summary())
```

### Use Case 3: Real-Time Stat Tracking (Future)

**Goal:** Track stats in real-time during live games

```python
import asyncio

async def live_stat_tracker(game_id, players_to_track):
    """
    Track player stats in real-time during live game.

    Args:
        game_id: Live game ID
        players_to_track: List of player names

    Yields:
        dict: Updated stats every second
    """
    while True:
        current_time = datetime.now(pytz.UTC)

        stats = {}
        for player_name in players_to_track:
            snapshot = get_player_stats_at_time(player_name, current_time.isoformat())
            stats[player_name] = snapshot

        yield {
            'timestamp': current_time,
            'game_id': game_id,
            'stats': stats
        }

        await asyncio.sleep(1)  # Update every second

# Usage
async for update in live_stat_tracker('401234567', ['LeBron James', 'Stephen Curry']):
    print(f"[{update['timestamp']}] LeBron: {update['stats']['LeBron James']['career_points']} pts")
```

---

## Troubleshooting

### Issue 1: Slow Snapshot Queries

**Symptom:** `get_player_snapshot_at_time()` takes > 10 seconds

**Diagnosis:**
```sql
-- Check if pre-computed snapshots exist
SELECT COUNT(*) FROM player_snapshots WHERE player_id = 123;
```

**Solutions:**
1. **Generate snapshots:** Run snapshot generation script (see 3.0005)
2. **Check BRIN indexes:** `VACUUM ANALYZE temporal_events;`
3. **Partition by year:** If > 500M events, partition table

### Issue 2: Wrong Timezone Results

**Symptom:** Timestamps are off by several hours

**Diagnosis:**
```sql
-- Check current database timezone
SHOW timezone;

-- Check if timestamps are timezone-aware
SELECT wall_clock_utc, pg_typeof(wall_clock_utc) FROM temporal_events LIMIT 1;
```

**Solutions:**
1. **Always use `TIMESTAMPTZ` type** (not `TIMESTAMP`)
2. **Specify timezone in queries:** `'2016-06-19 19:02:34-05:00'::TIMESTAMPTZ`
3. **Set session timezone:** `SET timezone = 'America/Chicago';`

### Issue 3: Missing Events

**Symptom:** Expected event not found at timestamp

**Diagnosis:**
```sql
-- Check data source and precision for game
SELECT DISTINCT data_source, precision_level
FROM temporal_events
WHERE game_id = '401234567';

-- Check nearest events around timestamp
SELECT wall_clock_utc, event_type, precision_level
FROM temporal_events
WHERE game_id = '401234567'
  AND wall_clock_utc BETWEEN '2016-06-19 19:00:00' AND '2016-06-19 19:10:00'
ORDER BY wall_clock_utc;
```

**Solutions:**
1. **Check data source coverage:** Some eras only have minute-level precision
2. **Widen time window:** Use range query instead of exact match
3. **Filter by precision:** Exclude low-precision data if needed

### Issue 4: Incorrect Age Calculations

**Symptom:** Player age is NULL or wrong

**Diagnosis:**
```sql
-- Check birth date availability and precision
SELECT
    p.name,
    pb.birth_date,
    pb.birth_date_precision
FROM
    players p
LEFT JOIN
    player_biographical pb ON p.player_id = pb.player_id
WHERE
    p.name = 'Kobe Bryant';
```

**Solutions:**
1. **Birth date missing:** NULL age is expected, document limitation
2. **Wrong precision flag:** Update `birth_date_precision` in database
3. **Timezone mismatch:** Ensure birth date uses player's birth timezone

---

## Next Steps

**For implementation:**
- See `docs/phases/PHASE_3_DATABASE.md` Sub-3.0005 for database setup
- See `docs/adr/009-temporal-panel-data-architecture.md` for architecture details
- See `docs/phases/PHASE_4_SIMULATION_ENGINE.md` Sub-4.0005 for temporal simulation
- See `docs/phases/PHASE_5_MACHINE_LEARNING.md` Sub-5.0005 for temporal ML features

**For testing:**
- Create validation test suite (see `docs/phases/PHASE_3_DATABASE.md`)
- Test query performance with sample datasets
- Verify timestamp precision across data sources

**For cost optimization:**
- Monitor RDS storage growth (temporal tables add ~200-300 GB)
- Adjust snapshot frequency based on query patterns
- Consider archiving old snapshots to S3

---

**Questions or issues?** See `docs/TROUBLESHOOTING.md` or create an issue in the GitHub repository.

---

*Last updated: October 7, 2025*
*Version: 1.0*
*Maintained by: NBA Temporal Panel Data Team*

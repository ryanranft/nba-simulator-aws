# Temporal Box Score Systems Comparison

**Created:** October 18, 2025
**Purpose:** Understand the two temporal box score systems and when to use each

---

## Overview

You have **two temporal box score systems** that serve different purposes:

1. **PostgreSQL RDS** - Production cloud database
2. **SQLite Local** - Development/testing database

Both store temporal snapshots (player/team stats at every moment), but have different structures and purposes.

---

## System 1: PostgreSQL RDS (Production)

### Tables

**`nba_simulator.public.game_state_snapshots`**
```sql
CREATE TABLE game_state_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    event_num INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    time_remaining VARCHAR(10),
    game_clock_seconds INTEGER,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    data_source VARCHAR(50) NOT NULL,  -- 'espn', 'hoopr', 'nba_api'
    verification_passed BOOLEAN DEFAULT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(game_id, event_num, data_source)
);
```

**`nba_simulator.public.player_snapshot_stats`**
```sql
CREATE TABLE player_snapshot_stats (
    snapshot_id BIGINT REFERENCES game_state_snapshots(snapshot_id),
    player_id VARCHAR(50) NOT NULL,
    player_name VARCHAR(100),
    team_id VARCHAR(10) NOT NULL,
    points INTEGER DEFAULT 0,
    fgm, fga, fg3m, fg3a, ftm, fta INTEGER DEFAULT 0,
    oreb, dreb, reb, ast, stl, blk, tov, pf INTEGER DEFAULT 0,
    plus_minus INTEGER DEFAULT 0,
    minutes DECIMAL(5,2) DEFAULT 0,
    on_court BOOLEAN DEFAULT false,
    PRIMARY KEY(snapshot_id, player_id)
);
```

**`nba_simulator.public.quarter_box_scores`**
```sql
CREATE TABLE quarter_box_scores (
    game_id VARCHAR(50) NOT NULL,
    quarter INTEGER NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    -- Quarter stats (NOT cumulative)
    points, fgm, fga, ... INTEGER DEFAULT 0,
    PRIMARY KEY(game_id, quarter, player_id, data_source)
);
```

### Characteristics

- **Normalized:** Snapshots reference separate player stats table
- **Multi-source:** Tracks ESPN, hoopR, NBA API separately
- **Cloud:** Accessible from anywhere
- **Scalable:** PostgreSQL handles millions of rows efficiently
- **Cost:** ~$29/month (RDS)

### When to Use

✅ **Production ML training**
✅ **Multi-source data validation**
✅ **Cloud-based queries**
✅ **Large-scale batch processing**
✅ **Real-time model serving**

---

## System 2: SQLite Local (Development)

### Tables

**`player_box_score_snapshots`**
```sql
CREATE TABLE player_box_score_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    event_number INTEGER NOT NULL,
    player_id TEXT NOT NULL,
    player_name TEXT,
    team_id TEXT NOT NULL,
    period INTEGER NOT NULL,
    game_clock TEXT,
    time_elapsed_seconds INTEGER,
    -- All stats in one row (denormalized)
    points, fgm, fga, fg_pct, ... INTEGER/REAL,
    UNIQUE(game_id, event_number, player_id)
);
```

**`team_box_score_snapshots`**
```sql
CREATE TABLE team_box_score_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    event_number INTEGER NOT NULL,
    team_id TEXT NOT NULL,
    is_home BOOLEAN NOT NULL,
    period INTEGER NOT NULL,
    -- Team stats (denormalized)
    points, fgm, fga, score_diff, is_leading, ...
    UNIQUE(game_id, event_number, team_id)
);
```

### Characteristics

- **Denormalized:** All data in single row (faster queries)
- **Single-source:** Basketball Reference only
- **Local:** SQLite file on disk
- **Portable:** Can copy database file anywhere
- **Cost:** $0

### When to Use

✅ **Local development**
✅ **Quick prototyping**
✅ **Historical data (pre-1993)**
✅ **Basketball Reference specific queries**
✅ **Testing without AWS costs**

---

## Data Flow Comparison

### PostgreSQL Flow (Production)

```
ESPN PBP (S3) → ESPNProcessor → game_state_snapshots
                                       ↓
                                player_snapshot_stats
                                       ↓
                                  PostgreSQL RDS
                                       ↓
                                  ML Training
```

### SQLite Flow (Development)

```
Basketball Ref PBP (SQLite) → SQLiteProcessor → player_box_score_snapshots
                                                        ↓
                                                  Local SQLite
                                                        ↓
                                                  Local Testing
```

---

## Query Comparison

### PostgreSQL (Normalized)

```sql
-- Get player stats at halftime
SELECT
    p.player_id,
    p.player_name,
    p.points,
    p.fg_pct,
    g.quarter,
    g.time_remaining
FROM player_snapshot_stats p
JOIN game_state_snapshots g ON p.snapshot_id = g.snapshot_id
WHERE g.game_id = '401584903'
AND g.quarter = 2
AND g.event_num = (
    SELECT MAX(event_num)
    FROM game_state_snapshots
    WHERE game_id = '401584903' AND quarter = 2
);
```

**Advantages:**
- Multi-source support
- Data integrity (foreign keys)
- Standard PostgreSQL features

**Disadvantages:**
- Requires JOIN (slower for large datasets)
- More complex queries

### SQLite (Denormalized)

```sql
-- Get player stats at halftime
SELECT
    player_id,
    player_name,
    points,
    fg_pct,
    period,
    game_clock
FROM player_box_score_snapshots
WHERE game_id = '202306120DEN'
AND period = 2
AND event_number = (
    SELECT MAX(event_number)
    FROM player_box_score_snapshots
    WHERE game_id = '202306120DEN' AND period = 2
);
```

**Advantages:**
- No JOINs needed (faster)
- Simpler queries
- All data in one row

**Disadvantages:**
- Data duplication
- Single source only
- Limited to SQLite features

---

## Migration Strategy

### Option 1: Keep Both (Recommended)

**Use PostgreSQL for:**
- Production ML training
- ESP/hoopR/NBA API data
- Cloud queries

**Use SQLite for:**
- Local development
- Basketball Reference data
- Quick testing

**No migration needed** - they complement each other

### Option 2: Consolidate to PostgreSQL

**Steps:**
1. Create Basketball Reference source in PostgreSQL
2. Migrate SQLite schema to PostgreSQL
3. Import Basketball Reference snapshots
4. Update processors to write to PostgreSQL

**Pros:**
- Single system
- Cloud accessible
- Better for production

**Cons:**
- Higher cost (~$30/month vs $0)
- More complex setup
- Network dependency

### Option 3: Unify Schema

Create a **hybrid schema** that works for both:

```sql
-- Unified player snapshots (works in both PostgreSQL and SQLite)
CREATE TABLE unified_player_snapshots (
    id BIGINT PRIMARY KEY,  -- BIGSERIAL in PostgreSQL, INTEGER in SQLite
    game_id VARCHAR(50) NOT NULL,
    event_number INTEGER NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    data_source VARCHAR(20) NOT NULL,  -- 'espn', 'hoopr', 'basketball_reference'

    -- Game context (denormalized for speed)
    period INTEGER,
    game_clock VARCHAR(10),
    time_elapsed_seconds INTEGER,

    -- Stats (all in one row)
    points, fgm, fga, ... INTEGER,

    UNIQUE(game_id, event_number, player_id, data_source)
);
```

---

## Recommendations

### For Your Current Project

**Keep both systems:**

1. **PostgreSQL (RDS)** - Use for:
   - ESPN/hoopR/NBA API data (1993-2025)
   - Production ML models
   - Cloud-based queries
   - Multi-source validation

2. **SQLite (Local)** - Use for:
   - Basketball Reference data (1946-2025)
   - Local development
   - Historical analysis (pre-1993)
   - Cost-free testing

### Future Roadmap

**Phase 1 (Current):**
- ✅ SQLite for Basketball Reference
- ✅ PostgreSQL for ESPN/hoopR/NBA API

**Phase 2 (After Historical Backfill):**
- Evaluate if Basketball Reference should go to PostgreSQL
- Decision based on query patterns and cost

**Phase 3 (Production):**
- Migrate high-value Basketball Reference data to PostgreSQL
- Keep SQLite for development/testing

---

## Cost Analysis

| System | Monthly Cost | Data Volume | Query Speed |
|--------|-------------|-------------|-------------|
| PostgreSQL RDS | $29 | 50M+ rows | Fast (cloud) |
| SQLite Local | $0 | 10M+ rows | Very fast (local) |
| **Combined** | **$29** | **60M+ rows** | **Best of both** |

---

## ML Query Examples

### PostgreSQL (Multi-Source)

```python
import psycopg2
import pandas as pd

conn = psycopg2.connect("postgresql://...")

# Query across multiple sources
df = pd.read_sql_query("""
    SELECT
        p.player_id,
        p.points,
        g.data_source,
        g.quarter
    FROM player_snapshot_stats p
    JOIN game_state_snapshots g ON p.snapshot_id = g.snapshot_id
    WHERE g.game_id = '401584903'
    AND g.data_source IN ('espn', 'hoopr')  -- Compare sources
""", conn)
```

### SQLite (Single-Source)

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('/tmp/basketball_reference_boxscores.db')

# Simple query (no JOIN)
df = pd.read_sql_query("""
    SELECT
        player_id,
        points,
        period
    FROM player_box_score_snapshots
    WHERE game_id = '202306120DEN'
""", conn)
```

---

## Summary

**You have two complementary systems:**

| Feature | PostgreSQL (RDS) | SQLite (Local) |
|---------|------------------|----------------|
| **Purpose** | Production | Development |
| **Data** | ESPN/hoopR/NBA API | Basketball Reference |
| **Structure** | Normalized (JOINs) | Denormalized (fast) |
| **Location** | Cloud | Local file |
| **Cost** | $29/month | $0 |
| **Coverage** | 1993-2025 | 1946-2025 |
| **Best For** | Production ML | Local testing |

**Recommendation:** Keep both! They serve different needs and complement each other perfectly.

- Use **PostgreSQL** for production ML training on modern data (1993+)
- Use **SQLite** for historical analysis (1946+) and cost-free development

**Total cost:** $29/month (same as before - SQLite is free!)

# 0.10: PostgreSQL JSONB Storage

**Sub-Phase:** 0.10 (Data Storage)
**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)
**Status:** 🔵 PLANNED
**Priority:** ⭐ CRITICAL
**Implementation ID:** rec_033_postgresql

---

## Overview

Store raw NBA data using PostgreSQL JSONB columns for flexible schema storage. This provides document-like flexibility while maintaining ACID guarantees and native integration with our temporal panel data system.

**Supersedes:** MongoDB NoSQL Storage (see `../archive/mongodb_superseded/0.1_nosql_mongodb_SUPERSEDED/`) - archived October 22, 2025

**Key Capabilities:**
- Flexible schema storage using JSONB columns
- Fast JSON queries with GIN indexes
- Document-like flexibility with relational benefits
- ACID transactions for data consistency
- Native joins with temporal data
- Zero additional infrastructure cost

**Impact:**
Unified data storage, flexible schema evolution, simplified architecture, $300-600/year cost savings vs MongoDB.

---

## Quick Start

```python
import psycopg2
from psycopg2.extras import Json
import os

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv('RDS_HOST'),
    database=os.getenv('RDS_DATABASE'),
    user=os.getenv('RDS_USER'),
    password=os.getenv('RDS_PASSWORD')
)

# Create table with JSONB column
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS raw_nba_data (
        id SERIAL PRIMARY KEY,
        source VARCHAR(50) NOT NULL,
        game_id VARCHAR(50),
        collected_at TIMESTAMP DEFAULT NOW(),
        data JSONB NOT NULL
    );

    -- Create GIN index for fast JSON queries
    CREATE INDEX IF NOT EXISTS idx_raw_data_gin
    ON raw_nba_data USING GIN (data);

    -- Create index on specific JSON field
    CREATE INDEX IF NOT EXISTS idx_game_date
    ON raw_nba_data ((data->>'game_date'));
""")

# Insert raw data with flexible schema
game_data = {
    'game_id': '401359859',
    'game_date': '2022-01-15',
    'home_team': 'LAL',
    'away_team': 'GSW',
    'play_by_play': [...],
    'box_score': {...},
    'advanced_stats': {...}
}

cur.execute("""
    INSERT INTO raw_nba_data (source, game_id, data)
    VALUES (%s, %s, %s)
    RETURNING id;
""", ('espn', game_data['game_id'], Json(game_data)))

# Query with JSON operators
cur.execute("""
    SELECT data->>'home_team' as home,
           data->>'away_team' as away,
           data->'box_score'->'home_stats' as home_stats
    FROM raw_nba_data
    WHERE data->>'game_date' = '2022-01-15'
      AND data->>'home_team' = 'LAL';
""")

results = cur.fetchall()
conn.commit()
```

---

## Architecture

### PostgreSQL JSONB Benefits

**vs MongoDB:**
- ✅ **ACID transactions** - Data consistency guaranteed
- ✅ **Native joins** - Combine with temporal tables
- ✅ **Single connection pool** - Simplified architecture
- ✅ **GIN indexes** - Fast JSON queries
- ✅ **Zero additional cost** - Using existing RDS
- ✅ **Proven reliability** - PostgreSQL track record

**JSONB Storage Strategy:**

```sql
-- Raw data table (flexible schema)
CREATE TABLE raw_nba_data (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'game', 'player', 'team'
    entity_id VARCHAR(100),
    season INTEGER,
    collected_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data JSONB NOT NULL,
    metadata JSONB  -- Source-specific metadata
);

-- Indexes for common queries
CREATE INDEX idx_raw_data_source ON raw_nba_data(source);
CREATE INDEX idx_raw_data_entity ON raw_nba_data(entity_type, entity_id);
CREATE INDEX idx_raw_data_season ON raw_nba_data(season);
CREATE INDEX idx_raw_data_gin ON raw_nba_data USING GIN (data);
CREATE INDEX idx_raw_data_metadata ON raw_nba_data USING GIN (metadata);

-- Specific field indexes for frequent queries
CREATE INDEX idx_game_date ON raw_nba_data ((data->>'game_date'))
    WHERE entity_type = 'game';
CREATE INDEX idx_player_name ON raw_nba_data ((data->>'player_name'))
    WHERE entity_type = 'player';
```

### Integration with Temporal System

```python
# Join raw JSONB data with temporal tables
query = """
    SELECT
        r.data->>'player_name' as player,
        r.data->'stats' as raw_stats,
        t.cumulative_points,
        t.career_games_played,
        t.snapshot_timestamp
    FROM raw_nba_data r
    JOIN player_snapshots t ON
        r.data->>'player_id' = t.player_id::text
        AND (r.data->>'game_date')::date = t.snapshot_timestamp::date
    WHERE r.entity_type = 'player'
      AND t.snapshot_timestamp BETWEEN %s AND %s
    ORDER BY t.snapshot_timestamp;
"""
```

---

## Implementation Steps

### 1. Database Schema Setup (1-2 hours)

```sql
-- Create schema for raw data
CREATE SCHEMA IF NOT EXISTS raw_data;

-- Main raw data table
CREATE TABLE raw_data.nba_games (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) UNIQUE NOT NULL,
    source VARCHAR(50) NOT NULL,
    season INTEGER,
    game_date DATE,
    collected_at TIMESTAMP DEFAULT NOW(),
    data JSONB NOT NULL
);

CREATE TABLE raw_data.nba_players (
    id SERIAL PRIMARY KEY,
    player_id VARCHAR(50),
    source VARCHAR(50) NOT NULL,
    season INTEGER,
    collected_at TIMESTAMP DEFAULT NOW(),
    data JSONB NOT NULL,
    UNIQUE(player_id, source, season)
);

CREATE TABLE raw_data.nba_teams (
    id SERIAL PRIMARY KEY,
    team_id VARCHAR(50),
    source VARCHAR(50) NOT NULL,
    season INTEGER,
    collected_at TIMESTAMP DEFAULT NOW(),
    data JSONB NOT NULL,
    UNIQUE(team_id, source, season)
);
```

### 2. Data Migration Script (2-3 hours)

```python
# scripts/db/migrate_s3_to_jsonb.py
import boto3
import psycopg2
from psycopg2.extras import Json
import json
from datetime import datetime

def migrate_espn_data_to_jsonb():
    """Migrate ESPN JSON files from S3 to PostgreSQL JSONB"""
    s3 = boto3.client('s3')
    conn = psycopg2.connect(...)

    bucket = 'nba-sim-raw-data-lake'
    prefix = 'nba_pbp/'

    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            # Download JSON
            response = s3.get_object(Bucket=bucket, Key=obj['Key'])
            data = json.loads(response['Body'].read())

            # Extract metadata
            game_id = data.get('gameId')
            game_date = data.get('gameDate')
            season = data.get('season', {}).get('year')

            # Insert into PostgreSQL
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO raw_data.nba_games
                (game_id, source, season, game_date, data)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (game_id)
                DO UPDATE SET
                    data = EXCLUDED.data,
                    collected_at = NOW();
            """, (game_id, 'espn', season, game_date, Json(data)))

            conn.commit()
```

### 3. Query Helper Functions (1-2 hours)

```python
# scripts/db/jsonb_helpers.py
class JSONBQueryHelper:
    """Helper class for querying JSONB data"""

    def __init__(self, conn):
        self.conn = conn

    def get_game_data(self, game_id: str, fields: list = None):
        """Retrieve specific fields from game data"""
        cur = self.conn.cursor()

        if fields:
            field_selects = [f"data->'{f}' as {f}" for f in fields]
            select_clause = ", ".join(field_selects)
        else:
            select_clause = "data"

        cur.execute(f"""
            SELECT {select_clause}
            FROM raw_data.nba_games
            WHERE game_id = %s;
        """, (game_id,))

        return cur.fetchone()

    def search_players(self, name_pattern: str):
        """Search players by name pattern"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                player_id,
                data->>'player_name' as name,
                data->>'team' as team,
                season
            FROM raw_data.nba_players
            WHERE data->>'player_name' ILIKE %s
            ORDER BY season DESC;
        """, (f'%{name_pattern}%',))

        return cur.fetchall()

    def aggregate_by_field(self, table: str, json_field: str):
        """Aggregate counts by a JSON field"""
        cur = self.conn.cursor()
        cur.execute(f"""
            SELECT
                data->>%s as field_value,
                COUNT(*) as count
            FROM raw_data.{table}
            GROUP BY data->>%s
            ORDER BY count DESC;
        """, (json_field, json_field))

        return cur.fetchall()
```

### 4. Performance Optimization (1-2 hours)

```sql
-- Analyze query performance
EXPLAIN ANALYZE
SELECT data->'box_score'->'home_stats'
FROM raw_data.nba_games
WHERE data->>'game_date' BETWEEN '2022-01-01' AND '2022-12-31';

-- Create materialized view for frequently accessed data
CREATE MATERIALIZED VIEW raw_data.games_summary AS
SELECT
    game_id,
    source,
    season,
    data->>'game_date' as game_date,
    data->>'home_team' as home_team,
    data->>'away_team' as away_team,
    data->'home_score' as home_score,
    data->'away_score' as away_score
FROM raw_data.nba_games;

CREATE INDEX idx_games_summary_date ON raw_data.games_summary(game_date);
CREATE INDEX idx_games_summary_teams ON raw_data.games_summary(home_team, away_team);

-- Refresh periodically
REFRESH MATERIALIZED VIEW raw_data.games_summary;
```

---

## Configuration

### Database Connection

```python
# config/postgresql_jsonb_config.yaml
database:
  host: ${RDS_HOST}
  port: 5432
  database: ${RDS_DATABASE}
  user: ${RDS_USER}
  password: ${RDS_PASSWORD}

jsonb_settings:
  # Maximum JSONB size (25MB default)
  max_jsonb_size: 26214400

  # GIN index settings
  gin_pending_list_limit: 4MB

  # Tables to create
  tables:
    - name: nba_games
      partition_by: season
      indexes:
        - type: gin
          column: data
        - type: btree
          column: "(data->>'game_date')"

    - name: nba_players
      partition_by: season
      indexes:
        - type: gin
          column: data
        - type: btree
          column: "(data->>'player_name')"

migration:
  batch_size: 1000
  sources:
    - espn
    - nba_stats
    - basketball_reference
```

---

## Performance Characteristics

**Estimated Time:** 1 week (implementation + migration)
- Schema design: 4-6 hours
- Migration scripts: 8-12 hours
- Query helpers: 6-8 hours
- Testing & optimization: 10-15 hours
- Documentation: 3-5 hours

**Storage:**
- ESPN data: ~119 GB (existing in S3)
- PostgreSQL JSONB: ~120-140 GB (10-20% overhead)
- Indexes: ~20-30 GB additional

**Query Performance:**
- Simple JSON field access: <1ms
- GIN index lookups: 1-5ms
- Complex nested queries: 10-50ms
- Aggregations: 100ms-1s (depending on dataset)

**Cost:**
- Additional storage: ~140 GB × $0.115/GB = ~$16/month
- RDS already provisioned: $0 marginal cost for compute
- Total: ~$16/month vs $15-30/month for MongoDB Atlas

---

## Dependencies

**Prerequisites:**
- PostgreSQL RDS instance running (already provisioned)
- PostgreSQL 13+ with JSONB support
- S3 data available (Phase 0.0-0.5 complete)

**Enables:**
- [0.8: RAG Pipeline with pgvector](../0.8_rag_pipeline_pgvector/README.md)
- [0.9: RAG + LLM Integration](../0.9_rag_llm_integration/README.md)
- Phase 1: Data Quality analysis with JSONB

---

## Integration with Temporal Panel Data

```python
# Example: Join raw JSONB with temporal snapshots
def get_player_performance_with_context(player_id, timestamp):
    """Get player stats with historical context"""
    query = """
        WITH raw_stats AS (
            SELECT
                data->'stats' as game_stats,
                data->>'game_date' as game_date
            FROM raw_data.nba_games
            WHERE data->'players' @> %s::jsonb
        ),
        temporal_context AS (
            SELECT
                cumulative_points,
                cumulative_assists,
                games_played,
                snapshot_timestamp
            FROM player_snapshots
            WHERE player_id = %s
              AND snapshot_timestamp <= %s
            ORDER BY snapshot_timestamp DESC
            LIMIT 1
        )
        SELECT
            r.game_stats,
            r.game_date,
            t.cumulative_points,
            t.cumulative_assists,
            t.games_played
        FROM raw_stats r
        CROSS JOIN temporal_context t
        ORDER BY r.game_date DESC;
    """

    player_filter = json.dumps([{"player_id": player_id}])
    return execute_query(query, (player_filter, player_id, timestamp))
```

---

## Testing

### Unit Tests

```python
# tests/test_jsonb_storage.py
import pytest
from scripts.db.jsonb_helpers import JSONBQueryHelper

def test_jsonb_insert():
    """Test inserting JSON data"""
    data = {
        'game_id': 'test_001',
        'game_date': '2022-01-15',
        'home_team': 'LAL'
    }
    # Test insertion
    assert insert_game_data(data) is not None

def test_jsonb_query():
    """Test querying JSON fields"""
    results = query_games_by_date('2022-01-15')
    assert len(results) > 0
    assert results[0]['home_team'] == 'LAL'

def test_gin_index_performance():
    """Test GIN index query performance"""
    import time
    start = time.time()
    results = query_with_json_field('home_team', 'LAL')
    duration = time.time() - start
    assert duration < 0.1  # Should be under 100ms
```

### Integration Tests

```bash
# Run integration tests
cd /Users/ryanranft/nba-simulator-aws
python tests/test_jsonb_integration.py -v
```

---

## Troubleshooting

### Common Issues

**1. JSONB size limit exceeded**
```
ERROR: JSONB value too large
```
Solution: Split large JSON documents into chunks or normalize data

**2. Slow GIN index creation**
```
CREATE INDEX is taking hours...
```
Solution: Use `CONCURRENTLY` option, increase `maintenance_work_mem`

**3. Poor query performance**
```sql
-- Add missing indexes
CREATE INDEX idx_specific_field ON table ((data->>'field_name'));

-- Analyze table statistics
ANALYZE raw_data.nba_games;
```

---

## Migration from MongoDB (If Previously Used)

If you have existing MongoDB data:

```python
# scripts/db/migrate_mongodb_to_postgresql.py
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import Json

def migrate_from_mongodb():
    """Migrate data from MongoDB to PostgreSQL JSONB"""
    mongo_client = MongoClient('mongodb://localhost:27017/')
    mongo_db = mongo_client['nba_data']

    pg_conn = psycopg2.connect(...)
    pg_cur = pg_conn.cursor()

    # Migrate games collection
    for doc in mongo_db.games.find():
        # Remove MongoDB _id
        doc.pop('_id', None)

        pg_cur.execute("""
            INSERT INTO raw_data.nba_games (game_id, source, data)
            VALUES (%s, %s, %s);
        """, (doc['game_id'], 'mongodb_migration', Json(doc)))

    pg_conn.commit()
```

---

## Related Documentation

- **[PHASE_0_INDEX.md](../../PHASE_0_INDEX.md)** - Phase 0 overview
- **[MongoDB Archive](../archive/mongodb_superseded/README.md)** - Why MongoDB was superseded
- **[0.8: RAG Pipeline](../0.8_rag_pipeline_pgvector/README.md)** - Next step: pgvector
- **[PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)** - Official docs

---

## Navigation

**Return to:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
**Prerequisites:** Phase 0.1-0.6 (Data Collection complete)
**Next Steps:** [0.8: RAG Pipeline with pgvector](../0.8_rag_pipeline_pgvector/README.md)

---

**Last Updated:** October 23, 2025
**Maintained By:** NBA Simulator AWS Team
**Source:** LLM Engineers Handbook (rec_033, adapted for PostgreSQL)


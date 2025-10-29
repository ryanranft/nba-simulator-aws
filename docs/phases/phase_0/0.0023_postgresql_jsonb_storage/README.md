# 0.1: Store Raw Data in PostgreSQL with JSONB

**Status:** 🔵 **PLANNED** (Priority 3 - Weeks 5-6)
**Phase:** 0 (Data Collection)
**Priority:** Medium (AI Features)
**Implementation ID:** rec_033 (PostgreSQL replacement for MongoDB)

---

## Overview

Implement PostgreSQL with JSONB columns for flexible schema storage of raw NBA data, replacing the need for MongoDB while maintaining the same flexibility benefits.

### Why PostgreSQL JSONB Instead of MongoDB?

**Technical Superiority:**
- ✅ **Flexible Schema:** JSONB columns provide the same flexibility as MongoDB
- ✅ **JSON Indexing:** GIN indexes enable fast JSON queries
- ✅ **ACID Transactions:** Full transactional support with automatic rollback
- ✅ **Better Integration:** Native joins with temporal panel data
- ✅ **Single Database:** No separate connection pool or infrastructure

**Cost Savings:**
- MongoDB Atlas: $15-30/month
- PostgreSQL RDS: Already paying $29/month
- pgvector: FREE (extension)
- **Savings: $15-30/month ($180-360/year)**

**Operational Benefits:**
- Single connection pool
- One backup strategy
- Unified monitoring
- Lower complexity
- Existing infrastructure

---

## Capabilities

### 1. Flexible Schema Storage

Store varying data structures without predefined schemas:

```sql
-- Flexible raw data storage
CREATE TABLE nba_raw_data (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    collected_at TIMESTAMP NOT NULL,

    -- Flexible JSONB storage (same as MongoDB)
    raw_data JSONB NOT NULL,

    -- Structured fields for common queries
    game_date DATE,
    home_team VARCHAR(50),
    away_team VARCHAR(50),

    CONSTRAINT unique_game_source_type UNIQUE (game_id, source, data_type)
);
```

### 2. Fast JSON Queries

Query nested JSON fields efficiently:

```sql
-- GIN index for JSONB queries
CREATE INDEX idx_raw_data_jsonb ON nba_raw_data USING GIN (raw_data);

-- Query JSON fields (same syntax as MongoDB queries)
SELECT * FROM nba_raw_data
WHERE raw_data->>'home_score' = '108'
  AND raw_data->'home_team'->>'name' = 'Lakers';

-- Index specific JSON paths for even faster queries
CREATE INDEX idx_raw_data_home_score ON nba_raw_data
    USING btree ((raw_data->>'home_score'));
```

### 3. ACID Transactions

Ensure data consistency across operations:

```python
# Atomic multi-source data insert
with conn.begin():
    conn.execute("""
        INSERT INTO nba_raw_data (game_id, source, data_type, raw_data)
        VALUES (%s, 'basketball_reference', 'box_score', %s)
    """, [game_id, br_data])

    conn.execute("""
        INSERT INTO nba_raw_data (game_id, source, data_type, raw_data)
        VALUES (%s, 'nba_api', 'box_score', %s)
    """, [game_id, nba_data])

    # Both succeed or both rollback automatically
```

### 4. Complex Joins with Temporal Data

Combine flexible JSON storage with structured temporal queries:

```sql
-- Join raw JSONB data with temporal snapshots
SELECT
    r.game_id,
    r.raw_data->>'final_score' as score,
    t.cumulative_points,
    t.season_avg_ppg
FROM nba_raw_data r
JOIN temporal_player_stats t ON r.game_id = t.game_id
WHERE r.source = 'basketball_reference'
  AND t.timestamp <= r.collected_at;
```

---

## Implementation Plan

### Week 1: Foundation (Days 25-28)

**Day 25-26: Schema Design**
- [ ] Design PostgreSQL schema with JSONB columns
- [ ] Create indexes for performance
- [ ] Design migration strategy from S3
- [ ] Plan dual-write capability

**Day 27-28: Database Setup**
- [ ] Create tables and indexes
- [ ] Test JSONB query performance
- [ ] Benchmark vs S3 reads
- [ ] Document query patterns

### Week 2: Migration & Integration (Days 29-31)

**Day 29: Migration Scripts**
- [ ] Build S3 → PostgreSQL migration tool
- [ ] Test with sample data (1000 games)
- [ ] Validate data integrity
- [ ] Measure migration performance

**Day 30: Dual-Write Integration**
- [ ] Add dual-write to ADCE scrapers
- [ ] Test with Basketball Reference scraper
- [ ] Validate S3 and PostgreSQL consistency
- [ ] Monitor performance impact

**Day 31: Testing & Documentation**
- [ ] End-to-end integration testing
- [ ] Performance benchmarks
- [ ] Query optimization guide
- [ ] Complete documentation

---

## PostgreSQL Schema

```sql
-- Main raw data table with JSONB
CREATE TABLE nba_raw_data (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    collected_at TIMESTAMP NOT NULL,

    -- Flexible JSONB storage (MongoDB equivalent)
    raw_data JSONB NOT NULL,

    -- Structured fields for common queries
    game_date DATE,
    home_team VARCHAR(50),
    away_team VARCHAR(50),

    -- Metadata
    file_size_bytes INTEGER,
    s3_path TEXT,

    CONSTRAINT unique_game_source_type UNIQUE (game_id, source, data_type)
);

-- Indexes for performance
CREATE INDEX idx_raw_data_season ON nba_raw_data (season);
CREATE INDEX idx_raw_data_source ON nba_raw_data (source);
CREATE INDEX idx_raw_data_game_date ON nba_raw_data (game_date);
CREATE INDEX idx_raw_data_jsonb ON nba_raw_data USING GIN (raw_data);

-- Index specific JSON paths for common queries
CREATE INDEX idx_raw_data_home_score ON nba_raw_data
    USING btree ((raw_data->>'home_score'));
CREATE INDEX idx_raw_data_away_score ON nba_raw_data
    USING btree ((raw_data->>'away_score'));
```

---

## Integration Points

### ADCE Integration

```python
# Add to scrapers: dual-write to S3 and PostgreSQL
async def save_game_data(game_id: str, data: dict):
    # Write to S3 (existing)
    await s3_client.put_object(
        Bucket='nba-sim-raw-data-lake',
        Key=f'games/{game_id}.json',
        Body=json.dumps(data)
    )

    # Write to PostgreSQL (new)
    await db.execute("""
        INSERT INTO nba_raw_data
        (game_id, source, data_type, season, raw_data, game_date, home_team, away_team)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (game_id, source, data_type)
        DO UPDATE SET raw_data = EXCLUDED.raw_data
    """, [
        game_id,
        'basketball_reference',
        'box_score',
        data['season'],
        json.dumps(data),
        data['game_date'],
        data['home_team'],
        data['away_team']
    ])
```

### DIMS Integration

Track PostgreSQL storage metrics:

```python
# Update DIMS with PostgreSQL metrics
dims_client.update_metric('postgresql_raw_data_count', count)
dims_client.update_metric('postgresql_storage_mb', size_mb)
dims_client.update_metric('postgresql_query_performance_ms', avg_query_time)
```

---

## Performance Benchmarks

**Target Metrics:**
- Query Performance: < 100ms for single game retrieval
- Bulk Insert: > 1000 records/second
- JSON Index Queries: < 200ms for complex filters
- Migration Speed: > 100 games/second from S3

**Monitoring:**
- Query execution time (pg_stat_statements)
- Index usage (pg_stat_user_indexes)
- Table size growth (pg_total_relation_size)
- Connection pool utilization

---

## Documentation

### Query Examples

```sql
-- Get all box scores for Lakers in 2023-24 season
SELECT
    game_id,
    game_date,
    raw_data->'home_team' as home,
    raw_data->'away_team' as away,
    raw_data->>'final_score' as score
FROM nba_raw_data
WHERE (home_team = 'Lakers' OR away_team = 'Lakers')
  AND season = '2023-24'
  AND data_type = 'box_score'
ORDER BY game_date DESC;

-- Find games with specific player stats
SELECT game_id, raw_data
FROM nba_raw_data
WHERE raw_data @> '{"players": [{"name": "LeBron James"}]}'::jsonb;

-- Aggregate JSON data
SELECT
    season,
    COUNT(*) as game_count,
    AVG((raw_data->>'home_score')::int) as avg_home_score
FROM nba_raw_data
WHERE data_type = 'box_score'
GROUP BY season;
```

---

## Related Sub-Phases

**Prerequisites:**
- ✅ 0.0001: Basketball Reference Scraper (data source)
- ✅ 0.0018: Autonomous Data Collection (ADCE for automation)

**Integrates With:**
- 🔄 0.0024: RAG Pipeline with pgvector (uses JSONB data)
- 🔄 0.0025: RAG + LLM Integration (queries JSONB data)
- 🔄 0.0013: Dispatcher Pipeline (stores task results)

**Supersedes:**
- 🗄️ archive/mongodb_superseded/0.1_nosql_mongodb_SUPERSEDED/

---

## Navigation

**Return to:** [Phase 0 Index](../PHASE_0_INDEX.md)
**Next:** [0.0024 RAG Pipeline with pgvector](../0.0024_rag_pipeline_pgvector/README.md)
**Related:** [PostgreSQL Setup Guide](../../../SETUP.md)

---

**Implementation Status:** 🔵 PLANNED (Ready to implement - Priority 3, Weeks 5-6)


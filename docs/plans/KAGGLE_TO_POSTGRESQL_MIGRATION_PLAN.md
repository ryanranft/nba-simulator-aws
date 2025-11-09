# Kaggle SQLite to PostgreSQL Migration Plan

**Created:** November 9, 2025
**Status:** Planning Phase
**Target Databases:** `nba_simulator`, `nba_mcp_synthesis`
**Migration Version:** 0.20

---

## Executive Summary

This plan outlines the migration of Kaggle NBA historical data (1946-2023, 65,698 games, 13.6M play-by-play events) from SQLite to PostgreSQL, creating a new `kaggle` schema following the established ESPN schema pattern.

**Key Objectives:**
1. Create `kaggle` schema in both `nba_simulator` and `nba_mcp_synthesis` databases
2. Migrate 16 SQLite tables with `_nba_kaggle` suffix naming convention
3. Maintain referential integrity and add appropriate indexes
4. Enable temporal queries on historical NBA data (1946-2023)
5. Preserve all 2.2 GB of historical data with zero data loss

---

## Source Data Overview

**SQLite Database:** `/Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite`
- **Size:** 2.2 GB
- **Format:** SQLite 3.x
- **Temporal Coverage:** 1946-2023 (77 years)
- **Games:** 65,698 games
- **Play-by-Play Events:** 13,592,899 events
- **Players:** ~4,800 unique players

### Tables to Migrate (16 tables)

| # | SQLite Table | PostgreSQL Table | Est. Rows | Priority |
|---|--------------|------------------|-----------|----------|
| 1 | `game` | `kaggle.game_nba_kaggle` | 65,698 | CRITICAL |
| 2 | `play_by_play` | `kaggle.play_by_play_nba_kaggle` | 13,592,899 | CRITICAL |
| 3 | `player` | `kaggle.player_nba_kaggle` | 4,800 | HIGH |
| 4 | `team` | `kaggle.team_nba_kaggle` | 30 | HIGH |
| 5 | `common_player_info` | `kaggle.common_player_info_nba_kaggle` | 3,600 | HIGH |
| 6 | `game_info` | `kaggle.game_info_nba_kaggle` | 58,000 | MEDIUM |
| 7 | `game_summary` | `kaggle.game_summary_nba_kaggle` | 58,000 | MEDIUM |
| 8 | `line_score` | `kaggle.line_score_nba_kaggle` | 58,000 | MEDIUM |
| 9 | `inactive_players` | `kaggle.inactive_players_nba_kaggle` | 110,000 | MEDIUM |
| 10 | `officials` | `kaggle.officials_nba_kaggle` | 71,000 | MEDIUM |
| 11 | `other_stats` | `kaggle.other_stats_nba_kaggle` | 28,000 | MEDIUM |
| 12 | `draft_history` | `kaggle.draft_history_nba_kaggle` | 8,200 | LOW |
| 13 | `draft_combine_stats` | `kaggle.draft_combine_stats_nba_kaggle` | 1,600 | LOW |
| 14 | `team_details` | `kaggle.team_details_nba_kaggle` | 27 | LOW |
| 15 | `team_history` | `kaggle.team_history_nba_kaggle` | 50 | LOW |
| 16 | `team_info_common` | `kaggle.team_info_common_nba_kaggle` | 0 | LOW |

**Total Estimated Rows:** ~14,117,904 rows

---

## Design Decisions

### Naming Convention

Following the pattern established for ESPN schema:

```
Database: nba_simulator
Schema: kaggle
Table Pattern: {table_name}_nba_kaggle

Example:
  - nba_simulator.kaggle.game_nba_kaggle
  - nba_simulator.kaggle.play_by_play_nba_kaggle
  - nba_simulator.kaggle.player_nba_kaggle
```

**Rationale:**
- Consistent with ESPN schema approach (`espn.espn_games`, `espn.espn_plays`)
- Suffix `_nba_kaggle` clearly identifies data source
- Schema namespace prevents naming conflicts
- Easy to query: `SELECT * FROM kaggle.game_nba_kaggle WHERE season = 2020`

### Schema Architecture

**Hybrid Approach:** Combine relational structure with JSONB flexibility

```sql
CREATE TABLE kaggle.{table_name}_nba_kaggle (
    id SERIAL PRIMARY KEY,
    -- Denormalized key columns for fast queries
    game_id VARCHAR(50),
    season INTEGER,
    game_date TIMESTAMP WITH TIME ZONE,

    -- Full data preservation in JSONB
    data JSONB NOT NULL,

    -- Metadata for tracking
    metadata JSONB,

    -- Timestamps
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Benefits:**
1. **Fast queries:** Indexed columns (game_id, season, etc.) enable efficient filtering
2. **Data preservation:** Full SQLite row data stored in `data` JSONB column
3. **Flexibility:** No data loss, can add computed columns later
4. **Consistency:** Matches ESPN schema pattern

### Indexing Strategy

**Primary Indexes:**
- B-tree indexes on frequently queried columns (game_id, season, player_id)
- GIN indexes on JSONB columns for flexible queries
- Composite indexes for common query patterns (game_id + period)

**Temporal Indexes:**
- BRIN indexes on timestamp columns for time-series queries
- Partial indexes on high-cardinality columns

---

## Migration Phases

### Phase 1: Schema Creation (0_20_kaggle_schema.sql)

**Deliverable:** SQL migration script
**Duration:** 2-3 hours development, <5 seconds execution

**Tasks:**
1. Create `kaggle` schema
2. Create 16 tables with appropriate columns and constraints
3. Add comments to all tables and key columns
4. Create indexes for performance
5. Add foreign key relationships where applicable
6. Grant permissions to user `ryanranft`

**Files to Create:**
- `scripts/db/migrations/0_20_kaggle_schema.sql`

**Dependencies:**
- PostgreSQL 14+
- Existing `nba_simulator` database
- User `ryanranft` with CREATE SCHEMA privileges

---

### Phase 2: Schema Analysis Script

**Deliverable:** Python script to analyze SQLite schema
**Duration:** 1-2 hours development, <1 minute execution

**Purpose:** Extract schema information from SQLite to inform table creation

```python
# scripts/analysis/analyze_kaggle_schema.py
"""
Analyze Kaggle SQLite schema and generate PostgreSQL DDL

Output:
1. Schema report (table structures, row counts, data types)
2. Suggested PostgreSQL table definitions
3. Foreign key relationships
4. Index recommendations
"""
```

**Files to Create:**
- `scripts/analysis/analyze_kaggle_schema.py`
- `docs/schemas/KAGGLE_SQLITE_SCHEMA_REPORT.md` (output)

---

### Phase 3: Data Migration Script (0_21_kaggle_data_migration.py)

**Deliverable:** Python ETL script
**Duration:** 4-6 hours development, 30-60 minutes execution

**Approach:** Batch processing with checkpointing

```python
# Pseudo-code
for table in KAGGLE_TABLES:
    print(f"Migrating {table}...")

    # Read from SQLite in chunks
    for chunk in read_sqlite_chunked(table, batch_size=10000):
        # Transform to PostgreSQL format
        pg_rows = transform_to_jsonb(chunk)

        # Bulk insert using COPY
        bulk_insert_postgres(pg_rows, f"kaggle.{table}_nba_kaggle")

        # Checkpoint progress
        save_checkpoint(table, chunk_number)

    print(f"✓ {table} migrated ({row_count:,} rows)")
```

**Features:**
1. **Chunked processing:** Handle 13.6M play-by-play rows without memory overflow
2. **Progress tracking:** Resume from checkpoint if interrupted
3. **Data validation:** Row count verification, data type checks
4. **Error handling:** Transaction rollback on failure, detailed error logging
5. **Performance:** PostgreSQL COPY command for bulk inserts

**Files to Create:**
- `scripts/db/migrations/0_21_kaggle_data_migration.py`
- `scripts/etl/kaggle_sqlite_to_postgres.py` (reusable ETL module)

**Estimated Migration Time:**
- Small tables (<1K rows): <1 second each (6 tables)
- Medium tables (1K-100K rows): 5-30 seconds each (9 tables)
- Large table (play_by_play, 13.6M rows): 20-40 minutes
- **Total:** 30-60 minutes

---

### Phase 4: Data Validation Script

**Deliverable:** Validation script
**Duration:** 2-3 hours development, 5-10 minutes execution

**Validation Checks:**

1. **Row Count Validation**
   ```sql
   -- Compare SQLite vs PostgreSQL row counts
   SELECT COUNT(*) FROM sqlite.game;           -- 65,698
   SELECT COUNT(*) FROM kaggle.game_nba_kaggle; -- 65,698 (should match)
   ```

2. **Data Integrity Validation**
   - Check for NULL values in required fields
   - Verify foreign key relationships
   - Validate data types and ranges
   - Spot check random samples (100 games)

3. **Temporal Coverage Validation**
   ```sql
   -- Verify temporal range (1946-2023)
   SELECT MIN(season), MAX(season), COUNT(DISTINCT season)
   FROM kaggle.game_nba_kaggle;
   -- Expected: 1946, 2022, 77 seasons
   ```

4. **Play-by-Play Validation**
   ```sql
   -- Verify play counts per game match
   SELECT game_id, COUNT(*) as play_count
   FROM kaggle.play_by_play_nba_kaggle
   GROUP BY game_id
   ORDER BY play_count DESC
   LIMIT 10;
   ```

**Files to Create:**
- `validators/phases/phase_0/validate_0_20_kaggle_postgres.py`
- Uses Workflow #58 validation framework

**Success Criteria:**
- 100% row count match (all 16 tables)
- Zero NULL values in critical fields
- All foreign key constraints valid
- Temporal coverage: 1946-2023

---

### Phase 5: Documentation & Testing

**Duration:** 2-3 hours

**Documentation:**
1. Schema reference guide
2. Query examples
3. Migration report
4. Troubleshooting guide

**Files to Create:**
- `docs/schemas/KAGGLE_POSTGRES_SCHEMA.md`
- `docs/migration/KAGGLE_MIGRATION_REPORT.md`
- `docs/examples/KAGGLE_QUERY_EXAMPLES.md`

**Testing:**
- Integration tests with pytest
- Performance benchmarks
- Query examples validation

---

## Detailed Implementation

### Table Definitions

#### 1. kaggle.game_nba_kaggle (CRITICAL)

**Purpose:** Game-level data (65,698 games from 1946-2023)

```sql
CREATE TABLE IF NOT EXISTS kaggle.game_nba_kaggle (
    id SERIAL PRIMARY KEY,
    game_id VARCHAR(50) UNIQUE NOT NULL,
    season INTEGER NOT NULL,
    game_date DATE,
    season_id VARCHAR(20),  -- Format: "22023" for 2022-23 season
    home_team_id INTEGER,
    away_team_id INTEGER,
    home_score INTEGER,
    away_score INTEGER,
    game_status TEXT,
    attendance INTEGER,

    -- Full game data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT game_nba_kaggle_season_check CHECK (season BETWEEN 1946 AND 2030)
);

COMMENT ON TABLE kaggle.game_nba_kaggle IS
'Kaggle NBA game data (1946-2023). 65,698 games across 77 seasons. Source: Kaggle Basketball Database (wyattowalsh/basketball).';

COMMENT ON COLUMN kaggle.game_nba_kaggle.season_id IS
'Season identifier in format "XYYYY" where X=1 or 2 and YYYY is year (e.g., "22023" = 2022-23 season)';

-- Indexes
CREATE INDEX idx_kaggle_game_game_id ON kaggle.game_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_game_season ON kaggle.game_nba_kaggle(season);
CREATE INDEX idx_kaggle_game_date ON kaggle.game_nba_kaggle(game_date);
CREATE INDEX idx_kaggle_game_teams ON kaggle.game_nba_kaggle(home_team_id, away_team_id);
CREATE INDEX idx_kaggle_game_data_gin ON kaggle.game_nba_kaggle USING GIN(data);
```

#### 2. kaggle.play_by_play_nba_kaggle (CRITICAL)

**Purpose:** Play-by-play events (13.6M rows for temporal queries)

```sql
CREATE TABLE IF NOT EXISTS kaggle.play_by_play_nba_kaggle (
    id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(50) NOT NULL,
    event_num INTEGER,
    event_msg_type INTEGER,
    event_msg_action_type INTEGER,
    period INTEGER,
    wc_time_string VARCHAR(20),  -- Wall clock time
    pc_time_string VARCHAR(20),  -- Period clock time
    home_description TEXT,
    neutral_description TEXT,
    visitor_description TEXT,
    score VARCHAR(20),
    score_margin VARCHAR(10),
    person1_type INTEGER,
    player1_id INTEGER,
    player1_name VARCHAR(100),
    player1_team_id INTEGER,

    -- Full play data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    FOREIGN KEY (game_id) REFERENCES kaggle.game_nba_kaggle(game_id) ON DELETE CASCADE
);

COMMENT ON TABLE kaggle.play_by_play_nba_kaggle IS
'Play-by-play events from Kaggle dataset. 13.6M individual plays across 65,698 games (1946-2023). Enables temporal panel queries at millisecond precision.';

-- Indexes optimized for temporal queries
CREATE INDEX idx_kaggle_pbp_game_id ON kaggle.play_by_play_nba_kaggle(game_id);
CREATE INDEX idx_kaggle_pbp_event_num ON kaggle.play_by_play_nba_kaggle(event_num);
CREATE INDEX idx_kaggle_pbp_period ON kaggle.play_by_play_nba_kaggle(period);
CREATE INDEX idx_kaggle_pbp_player1_id ON kaggle.play_by_play_nba_kaggle(player1_id);
CREATE INDEX idx_kaggle_pbp_game_period ON kaggle.play_by_play_nba_kaggle(game_id, period);
CREATE INDEX idx_kaggle_pbp_data_gin ON kaggle.play_by_play_nba_kaggle USING GIN(data);

-- BRIN index for time-series queries (created after data load)
-- CREATE INDEX idx_kaggle_pbp_collected_brin ON kaggle.play_by_play_nba_kaggle USING BRIN(collected_at);
```

#### 3. kaggle.player_nba_kaggle (HIGH)

**Purpose:** Player biographical data (~4,800 players)

```sql
CREATE TABLE IF NOT EXISTS kaggle.player_nba_kaggle (
    id SERIAL PRIMARY KEY,
    player_id INTEGER UNIQUE NOT NULL,
    full_name VARCHAR(100),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    display_first_last VARCHAR(100),
    birthdate DATE,
    school VARCHAR(100),
    country VARCHAR(50),
    height VARCHAR(10),
    weight INTEGER,
    season_exp INTEGER,
    jersey VARCHAR(10),
    position VARCHAR(20),
    roster_status VARCHAR(20),
    team_id INTEGER,

    -- Full player data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.player_nba_kaggle IS
'NBA player biographical data from Kaggle. ~4,800 players from NBA history (1946-2023).';

-- Indexes
CREATE INDEX idx_kaggle_player_id ON kaggle.player_nba_kaggle(player_id);
CREATE INDEX idx_kaggle_player_name ON kaggle.player_nba_kaggle(display_first_last);
CREATE INDEX idx_kaggle_player_team ON kaggle.player_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_player_data_gin ON kaggle.player_nba_kaggle USING GIN(data);
```

#### 4. kaggle.team_nba_kaggle (HIGH)

**Purpose:** Team reference data (30 teams)

```sql
CREATE TABLE IF NOT EXISTS kaggle.team_nba_kaggle (
    id SERIAL PRIMARY KEY,
    team_id INTEGER UNIQUE NOT NULL,
    full_name VARCHAR(100),
    abbreviation VARCHAR(5),
    nickname VARCHAR(50),
    city VARCHAR(50),
    state VARCHAR(50),
    year_founded INTEGER,

    -- Full team data from SQLite
    data JSONB NOT NULL,

    -- Metadata
    metadata JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE kaggle.team_nba_kaggle IS
'NBA team information. 30 current teams plus historical franchises.';

-- Indexes
CREATE INDEX idx_kaggle_team_id ON kaggle.team_nba_kaggle(team_id);
CREATE INDEX idx_kaggle_team_abbrev ON kaggle.team_nba_kaggle(abbreviation);
CREATE INDEX idx_kaggle_team_name ON kaggle.team_nba_kaggle(full_name);
```

**Note:** Remaining 12 tables follow similar pattern. Full DDL will be in `0_20_kaggle_schema.sql`.

---

## Migration Script Architecture

### ETL Script Structure

```python
# scripts/db/migrations/0_21_kaggle_data_migration.py

import sqlite3
import psycopg2
import psycopg2.extras
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys

# Configuration
SQLITE_DB = Path("/Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite")
CHECKPOINT_FILE = Path("/tmp/kaggle_migration_checkpoint.json")

# PostgreSQL connection
PG_CONFIG = {
    "host": "localhost",
    "database": "nba_simulator",
    "user": "ryanranft",
    "password": "",
    "port": 5432
}

# Table migration order (dependencies first)
MIGRATION_ORDER = [
    # Core reference tables first
    ("team", "kaggle.team_nba_kaggle", 1000),
    ("team_details", "kaggle.team_details_nba_kaggle", 1000),
    ("team_history", "kaggle.team_history_nba_kaggle", 1000),
    ("team_info_common", "kaggle.team_info_common_nba_kaggle", 1000),

    # Player tables
    ("player", "kaggle.player_nba_kaggle", 5000),
    ("common_player_info", "kaggle.common_player_info_nba_kaggle", 5000),

    # Draft tables
    ("draft_history", "kaggle.draft_history_nba_kaggle", 5000),
    ("draft_combine_stats", "kaggle.draft_combine_stats_nba_kaggle", 5000),

    # Game tables (foreign keys to team)
    ("game", "kaggle.game_nba_kaggle", 10000),
    ("game_info", "kaggle.game_info_nba_kaggle", 10000),
    ("game_summary", "kaggle.game_summary_nba_kaggle", 10000),
    ("line_score", "kaggle.line_score_nba_kaggle", 10000),

    # Game-related tables
    ("inactive_players", "kaggle.inactive_players_nba_kaggle", 10000),
    ("officials", "kaggle.officials_nba_kaggle", 10000),
    ("other_stats", "kaggle.other_stats_nba_kaggle", 10000),

    # Large tables last (foreign keys to game)
    ("play_by_play", "kaggle.play_by_play_nba_kaggle", 50000),  # 13.6M rows
]


class KaggleMigrator:
    """Migrate Kaggle SQLite data to PostgreSQL"""

    def __init__(self):
        self.sqlite_conn = None
        self.pg_conn = None
        self.checkpoint = self.load_checkpoint()

    def load_checkpoint(self):
        """Load migration checkpoint"""
        if CHECKPOINT_FILE.exists():
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_checkpoint(self, table, rows_migrated):
        """Save migration progress"""
        self.checkpoint[table] = {
            'rows_migrated': rows_migrated,
            'timestamp': datetime.now().isoformat()
        }
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    def connect_databases(self):
        """Connect to SQLite and PostgreSQL"""
        print("Connecting to databases...")
        self.sqlite_conn = sqlite3.connect(SQLITE_DB)
        self.sqlite_conn.row_factory = sqlite3.Row

        self.pg_conn = psycopg2.connect(**PG_CONFIG)
        self.pg_conn.autocommit = False
        print("✓ Connected\n")

    def migrate_table(self, sqlite_table, pg_table, batch_size):
        """Migrate one table from SQLite to PostgreSQL"""
        print(f"Migrating {sqlite_table} → {pg_table}...")

        # Check if already migrated
        if sqlite_table in self.checkpoint:
            print(f"  ⚠ Already migrated ({self.checkpoint[sqlite_table]['rows_migrated']:,} rows)")
            return

        cursor_sqlite = self.sqlite_conn.cursor()
        cursor_pg = self.pg_conn.cursor()

        # Get row count
        cursor_sqlite.execute(f"SELECT COUNT(*) FROM {sqlite_table}")
        total_rows = cursor_sqlite.fetchone()[0]
        print(f"  Total rows: {total_rows:,}")

        if total_rows == 0:
            print(f"  ✓ Skipped (empty table)\n")
            self.save_checkpoint(sqlite_table, 0)
            return

        # Get all column names
        cursor_sqlite.execute(f"PRAGMA table_info({sqlite_table})")
        columns = [col[1] for col in cursor_sqlite.fetchall()]

        # Migrate in batches
        migrated = 0
        start_time = datetime.now()

        for offset in range(0, total_rows, batch_size):
            # Read batch from SQLite
            query = f"SELECT * FROM {sqlite_table} LIMIT {batch_size} OFFSET {offset}"
            cursor_sqlite.execute(query)
            rows = cursor_sqlite.fetchall()

            if not rows:
                break

            # Transform to PostgreSQL format
            pg_rows = []
            for row in rows:
                # Convert SQLite row to dict
                row_dict = dict(zip(columns, row))

                # Create JSONB data field
                data_jsonb = json.dumps(row_dict)

                # Extract key fields for denormalized columns
                # (This will be table-specific in actual implementation)
                pg_rows.append({
                    'data': data_jsonb,
                    'metadata': json.dumps({
                        'source': 'kaggle',
                        'sqlite_table': sqlite_table,
                        'migrated_at': datetime.now().isoformat()
                    })
                })

            # Bulk insert to PostgreSQL using COPY
            # (Actual COPY command implementation here)

            migrated += len(rows)

            # Progress update
            if migrated % (batch_size * 10) == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = migrated / elapsed if elapsed > 0 else 0
                print(f"    {migrated:,}/{total_rows:,} rows ({migrated/total_rows*100:.1f}%) - {rate:.0f} rows/sec")

        # Commit transaction
        self.pg_conn.commit()

        # Save checkpoint
        self.save_checkpoint(sqlite_table, migrated)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"  ✓ Migrated {migrated:,} rows in {elapsed:.1f}s ({migrated/elapsed:.0f} rows/sec)\n")

    def run_migration(self):
        """Execute full migration"""
        print("="*70)
        print("Kaggle SQLite → PostgreSQL Migration")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.connect_databases()

        total_start = datetime.now()

        for sqlite_table, pg_table, batch_size in MIGRATION_ORDER:
            try:
                self.migrate_table(sqlite_table, pg_table, batch_size)
            except Exception as e:
                print(f"ERROR migrating {sqlite_table}: {e}")
                self.pg_conn.rollback()
                raise

        total_elapsed = (datetime.now() - total_start).total_seconds()

        print("="*70)
        print("Migration Complete!")
        print("="*70)
        print(f"Total time: {total_elapsed/60:.1f} minutes")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Cleanup
        self.sqlite_conn.close()
        self.pg_conn.close()


if __name__ == "__main__":
    migrator = KaggleMigrator()
    migrator.run_migration()
```

---

## Query Examples

### Example 1: Get all games from 2020 season

```sql
SELECT
    game_id,
    season,
    game_date,
    data->>'home_team' as home_team,
    data->>'away_team' as away_team,
    home_score,
    away_score
FROM kaggle.game_nba_kaggle
WHERE season = 2020
ORDER BY game_date
LIMIT 10;
```

### Example 2: Find all play-by-play events for a specific game

```sql
SELECT
    event_num,
    period,
    pc_time_string as clock,
    neutral_description as description,
    score
FROM kaggle.play_by_play_nba_kaggle
WHERE game_id = '0021900001'
ORDER BY event_num;
```

### Example 3: Player career statistics

```sql
SELECT
    display_first_last as player_name,
    birthdate,
    height,
    weight,
    position,
    school,
    data->>'draft_year' as draft_year
FROM kaggle.player_nba_kaggle
WHERE display_first_last LIKE '%LeBron%'
LIMIT 5;
```

### Example 4: Cross-schema join (Kaggle + ESPN)

```sql
-- Compare game counts: Kaggle (1946-2023) vs ESPN (2015+)
SELECT
    k.season,
    COUNT(DISTINCT k.game_id) as kaggle_games,
    COUNT(DISTINCT e.game_id) as espn_games
FROM kaggle.game_nba_kaggle k
FULL OUTER JOIN espn.espn_games e ON k.game_id = e.game_id
WHERE k.season >= 2015
GROUP BY k.season
ORDER BY k.season;
```

---

## Timeline & Effort Estimates

| Phase | Deliverable | Dev Time | Execution Time |
|-------|-------------|----------|----------------|
| 1 | Schema analysis script | 1-2 hours | <1 min |
| 2 | SQL migration (0_20_kaggle_schema.sql) | 2-3 hours | <5 sec |
| 3 | ETL migration script | 4-6 hours | 30-60 min |
| 4 | Validation script | 2-3 hours | 5-10 min |
| 5 | Documentation & tests | 2-3 hours | 10-15 min |
| **Total** | **Complete migration** | **11-17 hours** | **45-75 min** |

**Execution Timeline (once scripts are ready):**
1. Run schema creation: 5 seconds
2. Run data migration: 30-60 minutes
3. Run validation: 5-10 minutes
4. Review results: 10 minutes
5. **Total execution: ~1 hour**

---

## Success Criteria

**Migration is successful when:**

✅ **Schema Creation**
- [  ] `kaggle` schema created in both databases
- [  ] All 16 tables created with correct structure
- [  ] All indexes created
- [  ] All comments added
- [  ] Foreign keys established

✅ **Data Migration**
- [  ] 100% row count match (all 16 tables)
- [  ] Zero data loss
- [  ] All JSONB data valid
- [  ] Migration completes in <90 minutes

✅ **Data Validation**
- [  ] Row counts match SQLite exactly
- [  ] Temporal coverage: 1946-2023 (77 seasons)
- [  ] 65,698 games validated
- [  ] 13,592,899 play-by-play events validated
- [  ] Spot checks pass (100 random samples)
- [  ] Foreign key constraints valid

✅ **Performance**
- [  ] Query performance acceptable (<100ms for simple queries)
- [  ] Indexes improve query speed by >10x
- [  ] Database size reasonable (<3 GB)

✅ **Documentation**
- [  ] Schema reference complete
- [  ] Query examples provided
- [  ] Migration report generated
- [  ] Troubleshooting guide available

---

## Risks & Mitigation

### Risk 1: Data Type Mismatches

**Risk:** SQLite vs PostgreSQL data type differences
**Impact:** Medium
**Mitigation:**
- Analyze schema first with analysis script
- Store everything in JSONB as backup
- Use explicit type casting in ETL

### Risk 2: Memory Overflow

**Risk:** 13.6M play-by-play rows exceed memory
**Impact:** High
**Mitigation:**
- Chunked processing (50K rows per batch)
- PostgreSQL COPY command (not INSERT)
- Stream processing, not in-memory

### Risk 3: Foreign Key Violations

**Risk:** Referential integrity issues
**Impact:** Medium
**Mitigation:**
- Migrate parent tables first (teams, players)
- Defer constraint checking
- Validate before final commit

### Risk 4: Long Migration Time

**Risk:** Migration takes >2 hours
**Impact:** Low
**Mitigation:**
- Checkpointing system (resume on failure)
- Parallel table migration (where possible)
- Optimize batch sizes

---

## Rollback Plan

If migration fails, rollback is simple:

```sql
-- Drop kaggle schema entirely
DROP SCHEMA IF EXISTS kaggle CASCADE;

-- Or drop individual tables
DROP TABLE IF EXISTS kaggle.game_nba_kaggle CASCADE;
DROP TABLE IF EXISTS kaggle.play_by_play_nba_kaggle CASCADE;
-- ... (all 16 tables)
```

**SQLite data remains untouched** - zero risk to source data.

---

## Next Steps

**To proceed with migration:**

1. **Review this plan** - User approval required
2. **Create schema analysis script** - Understand SQLite structure
3. **Write 0_20_kaggle_schema.sql** - Table definitions
4. **Write 0_21_kaggle_data_migration.py** - ETL script
5. **Write validation script** - Data integrity checks
6. **Execute migration** - Run on `nba_simulator` first
7. **Validate results** - 100% data integrity
8. **Replicate to `nba_mcp_synthesis`** - Second database
9. **Document** - Schema guide, query examples
10. **Close ticket** - Mark Phase 0.0003 PostgreSQL migration complete

---

**Questions for User:**

1. Should we create identical schemas in both `nba_simulator` and `nba_mcp_synthesis`, or different structures?
2. Are there specific query patterns we should optimize for?
3. Do you want to preserve SQLite-specific columns (like ROWID) or only migrate semantic data?
4. Should we add any computed columns (e.g., game_duration_minutes)?
5. Priority: Should we migrate all 16 tables or focus on critical tables first?

---

**Ready to proceed?** Let me know and I'll start with Phase 1 (schema analysis).

# hoopR Schema Inspection Results

**Date:** November 9, 2025
**Database:** nba_mcp_synthesis.hoopr_raw
**Tool:** scripts/etl/inspect_hoopr_schema.py

---

## Executive Summary

Inspection of `nba_mcp_synthesis.hoopr_raw` schema revealed critical differences from the schema created in `nba_simulator.hoopr`:

**Key Findings:**
1. ❌ **No Primary Keys** - Tables have no PK constraints (expected to have)
2. ⚠️ **ID Type Mismatch** - IDs are `double precision` not `bigint`
3. ✅ **Existing Data** - 13M+ plays already loaded (from prior sessions)
4. ⚠️ **Duplicate Columns** - schedule table has duplicate game_id

**Impact:** Loader v2's UPSERT strategy fails because ON CONFLICT requires a PK or unique constraint.

---

## Detailed Findings

### Table 1: play_by_play_hoopr_nba

**Primary Key:** None (expected `id`)

**Row Count:** 13,074,829

**Key Columns:**
```
id                    double precision    NOT NULL
game_id               double precision    NOT NULL
season                integer             NULL       ⚠️ Can be NULL
game_date             date                NOT NULL
type_text             text                NULL
description           text                NULL
athlete_id_1          double precision    NULL
athlete_id_2          double precision    NULL
home_score            integer             NULL
away_score            integer             NULL
coordinate_x          double precision    NULL
coordinate_y          double precision    NULL
```

**Issues Found:**
- No primary key (loader v2 expects to use event_id for ON CONFLICT)
- id is double precision, not bigint as created in nba_simulator
- season can be NULL (nba_simulator schema has NOT NULL)

---

### Table 2: player_box_hoopr_nba

**Primary Key:** None (expected composite: game_id + athlete_id)

**Row Count:** 785,505

**Key Columns:**
```
game_id               double precision    NOT NULL
athlete_id            double precision    NOT NULL
season                integer             NULL
game_date             date                NOT NULL
athlete_name          text                NULL
team_abbrev           text                NULL
minutes               text                NULL
fgm                   integer             NULL
fga                   integer             NULL
fg3m                  integer             NULL
fg3a                  integer             NULL
ftm                   integer             NULL
fta                   integer             NULL
pts                   integer             NULL
reb                   integer             NULL
ast                   integer             NULL
```

**Issues Found:**
- No primary key (loader v2 expects game_id + athlete_id for ON CONFLICT)
- IDs are double precision, not bigint

---

### Table 3: team_box_hoopr_nba

**Primary Key:** None (expected composite: game_id + team_id)

**Row Count:** 59,670

**Key Columns:**
```
game_id               double precision    NOT NULL
team_id               double precision    NOT NULL
season                integer             NULL
game_date             date                NOT NULL
team_abbrev           text                NULL
fgm                   integer             NULL
fga                   integer             NULL
fg_pct                double precision    NULL
fg3m                  integer             NULL
fg3a                  integer             NULL
fg3_pct               double precision    NULL
pts                   integer             NULL
```

**Issues Found:**
- No primary key (loader v2 expects game_id + team_id for ON CONFLICT)
- IDs are double precision, not bigint

---

### Table 4: schedule_hoopr_nba

**Primary Key:** None (expected game_id)

**Row Count:** 30,758

**Key Columns:**
```
game_id               double precision    NOT NULL   ⚠️ DUPLICATE
id                    double precision    NULL       ⚠️ Also game_id
season                integer             NULL
game_date             date                NOT NULL
home_team_id          double precision    NULL
away_team_id          double precision    NULL
home_score            integer             NULL
away_score            integer             NULL
status_type           text                NULL
```

**Issues Found:**
- No primary key (loader v2 expects game_id for ON CONFLICT)
- **DUPLICATE game_id column** - Both `id` and `game_id` exist
  - Caused by column mapping: id → game_id creates duplicate
- IDs are double precision, not bigint

---

## Implications for Loader v3

### Critical Changes Needed

1. **Remove ON CONFLICT Clauses**
   - Tables have no primary keys
   - ON CONFLICT requires PK or unique constraint
   - Must use alternative de-duplication strategy

2. **Change De-duplication Strategy**

   **Option A: DELETE + INSERT (Recommended)**
   ```python
   # For each game_id in new data:
   DELETE FROM table WHERE game_id = %s;
   INSERT INTO table VALUES (...);
   ```
   - Pros: Simple, guarantees no duplicates
   - Cons: Slower than UPSERT

   **Option B: Check Existence First**
   ```python
   SELECT game_id FROM table WHERE game_id = %s;
   if exists:
       UPDATE table SET ... WHERE game_id = %s;
   else:
       INSERT INTO table VALUES (...);
   ```
   - Pros: Preserves existing data
   - Cons: Two queries per row

   **Option C: Just INSERT (Fastest but risky)**
   ```python
   INSERT INTO table VALUES (...);
   ```
   - Pros: Fastest
   - Cons: Creates duplicates on re-run

3. **Fix Data Types**
   ```python
   # Change from:
   id_col = int(value)  # Fails for double precision

   # To:
   id_col = float(value) if value else None
   ```

4. **Fix schedule Table Mapping**
   ```python
   # Current (creates duplicate):
   'id': 'game_id'  # Mapping creates second game_id column

   # Fixed:
   # Don't map id to game_id - schedule already has game_id column
   # Or check if game_id exists before mapping
   ```

5. **Handle NULL season Values**
   ```python
   # Current fails if season is NULL and table has NOT NULL constraint
   # Fixed: Allow NULL in schema or coalesce to default
   ```

---

## Recommendations

### For nba_mcp_synthesis (Existing Schema)

**Use DELETE + INSERT strategy:**
```python
def load_batch(conn, schema, table, df, key_column='game_id'):
    # Get unique game_ids
    game_ids = df[key_column].unique()

    # Delete existing rows
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {schema}.{table} WHERE {key_column} = ANY(%s)", (list(game_ids),))

    # Insert new rows
    execute_batch(cursor, insert_query, data)
    conn.commit()
```

**Advantages:**
- Works without primary keys
- Guarantees no duplicates
- Simple to implement

**Disadvantages:**
- Slower than UPSERT
- Loses data if INSERT fails after DELETE

### For nba_simulator.hoopr (New Schema)

**Add primary keys to schema:**
```sql
-- play_by_play
ALTER TABLE hoopr.play_by_play_hoopr_nba ADD PRIMARY KEY (event_id);

-- player_box
ALTER TABLE hoopr.player_box_hoopr_nba ADD PRIMARY KEY (game_id, athlete_id);

-- team_box
ALTER TABLE hoopr.team_box_hoopr_nba ADD PRIMARY KEY (game_id, team_id);

-- schedule
ALTER TABLE hoopr.schedule_hoopr_nba ADD PRIMARY KEY (game_id);
```

**Use DOUBLE PRECISION for IDs:**
```sql
-- Change from BIGINT to DOUBLE PRECISION
event_id DOUBLE PRECISION PRIMARY KEY,
game_id DOUBLE PRECISION NOT NULL,
athlete_id_1 DOUBLE PRECISION,
```

**Allow NULL season:**
```sql
season INTEGER NULL,  -- Not NOT NULL
```

---

## Next Steps

1. **Create loader v3** with DELETE + INSERT strategy
2. **Test loader v3** on nba_mcp_synthesis (should work now)
3. **Fix nba_simulator schema** (add PKs, change types)
4. **Load to nba_simulator** using loader v3
5. **Test daily collection** with working loader

---

## Files Modified

**Created:**
- `docs/HOOPR_SCHEMA_INSPECTION_RESULTS.md` (this file)

**Needs Update:**
- `scripts/etl/load_hoopr_parquet_v2.py` → v3 (remove ON CONFLICT, add DELETE + INSERT)
- `scripts/db/migrations/0_20_hoopr_schema.sql` → v2 (add PKs, change types, allow NULL)

**Working As-Is:**
- `scripts/etl/inspect_hoopr_schema.py` ✅
- `scripts/etl/collect_hoopr_daily.py` ✅ (not tested yet)
- `scripts/etl/run_hoopr_daily.sh` ✅ (not tested yet)

---

**Status:** Schema inspection complete, loader v3 design ready
**Next:** Implement DELETE + INSERT strategy in loader v3

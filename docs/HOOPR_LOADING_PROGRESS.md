# hoopR Data Loading Status

**Last Updated:** November 9, 2025
**Status:** ⚠️ In Progress - Schema Compatibility Issues Found

---

## Current Situation

✅ **Completed:**
- Created hoopr schema in nba_simulator (Step 3.1)
- 4 tables created, 21 indexes, triggers configured

⚠️ **Issue Found (Step 3.2):**
- Schema mismatch between created tables and actual parquet file structure
- `load_hoopr_parquet_v2.py` has column mapping issues

🎯 **Current Strategy:**
- Load to nba_mcp_synthesis ONLY (known working schema)
- Inspect what actually works
- Fix nba_simulator schema based on reality
- Then load to nba_simulator

---

## Issues Identified

### 1. Primary Key Mismatch
- **Created schema:** Uses `event_id` as PK for play_by_play
- **Actual data:** Uses `id` in parquet files
- **Impact:** INSERT fails on conflict detection

### 2. Column Mapping Conflicts
- **Schedule table:** `id` → `game_id` mapping creates duplicate columns
- **Impact:** Column appears twice in INSERT

### 3. NOT NULL Constraints
- **Created schema:** `season` is NOT NULL
- **Actual data:** Some records missing season values
- **Impact:** INSERT violates constraint

### 4. Data Type Issues
- **Created schema:** Uses BIGINT for IDs
- **Actual data:** Some IDs exceed BIGINT range or come as TEXT
- **Impact:** Type conversion errors

---

## Action Plan

### Phase 1: Load to nba_mcp_synthesis ✅ READY

**Why this works:**
- Schema already exists and matches parquet structure
- Used successfully in prior sessions
- Known compatible with hoopR data format

**Commands:**
```bash
conda activate nba-aws

# Load 2024 season
python scripts/etl/load_hoopr_parquet_v2.py --database nba_mcp_synthesis --season 2024

# Load 2025 season
python scripts/etl/load_hoopr_parquet_v2.py --database nba_mcp_synthesis --season 2025
```

**Expected Result:**
- 1.19M play-by-play rows loaded
- 67K player box scores loaded
- 5K team box scores loaded
- 2.5K schedule entries loaded

**Verification:**
```bash
psql -U ryanranft -d nba_mcp_synthesis -c "
SELECT
    'play_by_play' AS table,
    COUNT(*) AS rows,
    MAX(game_date) AS latest
FROM hoopr_raw.play_by_play_hoopr_nba
UNION ALL
SELECT 'player_box', COUNT(*), MAX(game_date) FROM hoopr_raw.player_box_hoopr_nba
UNION ALL
SELECT 'team_box', COUNT(*), MAX(game_date) FROM hoopr_raw.team_box_hoopr_nba
UNION ALL
SELECT 'schedule', COUNT(*), MAX(game_date) FROM hoopr_raw.schedule_hoopr_nba;
"
```

---

### Phase 2: Inspect Actual Schema ⏳ NEXT

**Purpose:** Learn what actually works

**Tool created:** `scripts/etl/inspect_hoopr_schema.py`

**Commands:**
```bash
python scripts/etl/inspect_hoopr_schema.py > /tmp/hoopr_schema_actual.txt
cat /tmp/hoopr_schema_actual.txt
```

**What we'll learn:**
- Actual column names and types
- Actual primary keys
- Actual indexes
- Actual data samples
- What column mappings work

---

### Phase 3: Fix nba_simulator Schema ⏳ PENDING

**Based on inspection results:**

1. Create `scripts/db/migrations/0_20_hoopr_schema_v2.sql` with:
   - Correct primary key columns (probably `id` not `event_id`)
   - Correct column types (TEXT vs BIGINT vs NUMERIC)
   - Nullable constraints matching actual data
   - No conflicting column mappings

2. Drop and recreate nba_simulator.hoopr:
   ```bash
   psql -U ryanranft -d nba_simulator -c "DROP SCHEMA IF EXISTS hoopr CASCADE;"
   psql -U ryanranft -d nba_simulator -f scripts/db/migrations/0_20_hoopr_schema_v2.sql
   ```

3. Create `load_hoopr_parquet_v3.py` with:
   - Corrected column mappings
   - Better type handling
   - Proper conflict detection

---

### Phase 4: Load to nba_simulator ⏳ PENDING

**After schema is corrected:**

```bash
python scripts/etl/load_hoopr_parquet_v3.py --database nba_simulator --season 2024
python scripts/etl/load_hoopr_parquet_v3.py --database nba_simulator --season 2025
```

**Verification:**
```bash
psql -U ryanranft -d nba_simulator -c "
SELECT COUNT(*) FROM hoopr.play_by_play_hoopr_nba;
SELECT COUNT(*) FROM hoopr.player_box_hoopr_nba;
SELECT COUNT(*) FROM hoopr.team_box_hoopr_nba;
SELECT COUNT(*) FROM hoopr.schedule_hoopr_nba;
"
```

---

## Files Status

**Working:**
- ✅ `scripts/etl/collect_hoopr_daily.py` - Daily collector (not tested yet)
- ✅ `scripts/etl/run_hoopr_daily.sh` - Cron wrapper
- ✅ `scripts/etl/inspect_hoopr_schema.py` - Schema inspector (NEW)
- ✅ `docs/HOOPR_AUTONOMOUS_SETUP.md` - Setup guide

**Needs Fixes:**
- ⚠️ `scripts/db/migrations/0_20_hoopr_schema.sql` - Wrong column names/types
- ⚠️ `scripts/etl/load_hoopr_parquet_v2.py` - Column mapping conflicts

**Will Create:**
- 🔜 `scripts/db/migrations/0_20_hoopr_schema_v2.sql` - Corrected schema
- 🔜 `scripts/etl/load_hoopr_parquet_v3.py` - Corrected loader

---

## Lessons Learned

1. **Don't guess schemas** - Inspect existing working schemas first
2. **Test incrementally** - Load to one database before both
3. **Dry run everything** - Catch issues before production
4. **Use existing patterns** - nba_mcp_synthesis schema already worked

---

## Next Immediate Action

**YOU:** Run Phase 1 commands to load to nba_mcp_synthesis

```bash
conda activate nba-aws
python scripts/etl/load_hoopr_parquet_v2.py --database nba_mcp_synthesis --season 2024
python scripts/etl/load_hoopr_parquet_v2.py --database nba_mcp_synthesis --season 2025
```

**THEN:** Run schema inspector and share results

```bash
python scripts/etl/inspect_hoopr_schema.py
```

**THEN:** I'll create corrected schema and loader v3 based on actual structure

---

**Branch:** claude/hoopr-data-work-011CUwmmNAjLymzZwKdHzhit
**Status:** Waiting for Phase 1 completion
**Priority:** Get nba_mcp_synthesis loaded first (the main goal)

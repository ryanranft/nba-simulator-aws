# Kaggle SQLite → PostgreSQL Migration - Quick Start Guide

**Migration Version:** 0.20
**Created:** November 9, 2025
**Status:** Ready for Execution

## Overview

This guide provides step-by-step instructions to migrate 2.2 GB of Kaggle NBA historical data (1946-2023) from SQLite to PostgreSQL.

**What gets migrated:**
- 16 tables → `kaggle` schema
- 65,698 games (1946-2023)
- 13.6M play-by-play events
- Player, team, and draft data
- Total: ~14.1M rows

**Execution time:** ~1 hour (30-60 minutes)

---

## Prerequisites

**✅ Before you start:**

1. **SQLite database** exists at:
   ```
   /Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite
   ```

2. **PostgreSQL** is running:
   ```bash
   # Test connection
   psql -U ryanranft -d nba_simulator -c "\conninfo"
   ```

3. **Python packages** installed:
   ```bash
   pip install psycopg2-binary  # PostgreSQL adapter
   ```

4. **Disk space:** At least 4 GB free in PostgreSQL data directory

---

## Step 1: Create Schema (5 seconds)

Create the `kaggle` schema and all 16 tables:

```bash
cd /Users/ryanranft/nba-simulator-aws

psql -U ryanranft -d nba_simulator -f scripts/db/migrations/0_20_kaggle_schema.sql
```

**Expected output:**
```
CREATE SCHEMA
CREATE TABLE
CREATE TABLE
...
(16 tables created)
(60+ indexes created)
NOTICE: Kaggle Schema Migration 0.20 - COMPLETE
```

**Verify:**
```bash
psql -U ryanranft -d nba_simulator -c "\dt kaggle.*"
```

You should see 16 tables listed.

---

## Step 2: Analyze Schema (Optional, 1 minute)

Generate a detailed schema report:

```bash
python scripts/analysis/analyze_kaggle_schema.py
```

This creates:
- `docs/schemas/KAGGLE_SQLITE_SCHEMA_REPORT.md` - Human-readable report
- `docs/schemas/kaggle_schema.json` - Machine-readable schema

**Skip if:** You want to proceed directly to migration.

---

## Step 3: Run Migration (30-60 minutes)

### Option A: Full Migration (Recommended)

Migrate all 16 tables:

```bash
python scripts/db/migrations/0_21_kaggle_data_migration.py
```

**What happens:**
- Migrates tables in dependency order (teams → players → games → plays)
- Shows real-time progress with ETA
- Creates checkpoints every batch (resume on failure)
- Validates data during migration

**Expected output:**
```
======================================================================
Kaggle SQLite → PostgreSQL Migration (v0.21)
======================================================================
Started: 2025-11-09 10:30:00

Connecting to databases...
  ✓ SQLite: /Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite
  ✓ PostgreSQL: nba_simulator at localhost

Verifying kaggle schema...
✓ kaggle schema exists

======================================================================
Migrating: team → kaggle.team_nba_kaggle
Priority: HIGH
======================================================================
Total rows: 30
Columns: 7
Batch size: 1,000

  [        30/        30] 100.0% |     300 rows/s | ETA: 00:00:00    | Batch: 0.10s

✓ Migrated: 30 rows in 0.1s (300 rows/s)

...

======================================================================
Migrating: play_by_play → kaggle.play_by_play_nba_kaggle
Priority: CRITICAL
======================================================================
Total rows: 13,592,899
Columns: 34
Batch size: 50,000

  [    50,000/13,592,899]   0.4% |   8,500 rows/s | ETA: 00:26:40    | Batch: 5.88s
  [   100,000/13,592,899]   0.7% |   9,200 rows/s | ETA: 00:24:30    | Batch: 5.43s
  ...
  [13,592,899/13,592,899] 100.0% |  10,100 rows/s | ETA: 00:00:00    | Batch: 4.95s

✓ Migrated: 13,592,899 rows in 1,346.8s (10,090 rows/s)

======================================================================
Migration Summary
======================================================================

Total rows migrated: 14,117,904
Total errors: 0
Total duration: 45.3 minutes
Overall rate: 5,193 rows/second
Tables migrated: 16

Per-table breakdown:
Table                            Rows    Duration        Rate Status
------------------------------------------------------------------------------------------
team                               30      0.1s      300 rows/s completed
player                          4,800      1.2s    4,000 rows/s completed
game                           65,698     12.5s    5,256 rows/s completed
play_by_play               13,592,899  1,346.8s   10,090 rows/s completed
...

======================================================================

Completed: 2025-11-09 11:15:18
```

### Option B: Dry Run (Test without writing)

Test the migration without actually writing data:

```bash
python scripts/db/migrations/0_21_kaggle_data_migration.py --dry-run
```

**Use when:** You want to verify the script works before committing to full migration.

### Option C: Partial Migration (Specific tables)

Migrate only specific tables:

```bash
# Migrate just game and player tables
python scripts/db/migrations/0_21_kaggle_data_migration.py --tables game,player

# Migrate only critical tables
python scripts/db/migrations/0_21_kaggle_data_migration.py --tables game,play_by_play
```

### Option D: Resume Migration (After interruption)

Resume from last checkpoint:

```bash
python scripts/db/migrations/0_21_kaggle_data_migration.py --resume
```

**Use when:** Migration was interrupted (Ctrl+C, network issue, etc.)

---

## Step 4: Validate Migration (5-10 minutes)

Verify data integrity:

```bash
python validators/phases/phase_0/validate_0_20_kaggle_postgres.py --verbose
```

**Validation checks:**
1. ✓ Schema exists
2. ✓ All 16 tables exist
3. ✓ Row counts match SQLite
4. ✓ Temporal coverage (1946-2023)
5. ✓ JSONB data valid
6. ✓ Foreign keys valid
7. ✓ Indexes created
8. ✓ Spot checks (10 random games)

**Expected output:**
```
=== 0.20 Validator: Kaggle PostgreSQL Migration ===

  Checking schema existence...
  ✓ kaggle schema exists
  Checking table existence...
  ✓ All 16 tables exist
  Checking row counts...
  ✓ Table 'game_nba_kaggle': 65,698 rows (exact match)
  ✓ Table 'play_by_play_nba_kaggle': 13,592,899 rows (within 20% of 13,592,899)
  ...
  Checking temporal coverage...
  ✓ Min season: 1946
  ✓ Max season: 2022
  ✓ Seasons: 77 (1946-2023 coverage)
  Checking JSONB data integrity...
  ✓ All rows have valid JSONB data
  Checking foreign keys...
  ✓ Foreign key constraints valid
  Checking indexes...
  ✓ Found 65 indexes
  Running spot checks (10 random games)...
  ✓ Spot checks passed (10/10 games match)

=== Validation Summary ===

Passed:   8/8
Failed:   0/8
Warnings: 0

✓ All 0.20 validations passed!
```

**Quick validation** (skip expensive checks):
```bash
python validators/phases/phase_0/validate_0_20_kaggle_postgres.py --quick
```

---

## Step 5: Verify Query Performance

Test some queries to ensure indexes work:

```sql
-- Connect to database
psql -U ryanranft -d nba_simulator

-- Query 1: Count games by season
SELECT season, COUNT(*) as games
FROM kaggle.game_nba_kaggle
WHERE season >= 2020
GROUP BY season
ORDER BY season;

-- Query 2: Find all games for Lakers in 2020
SELECT game_id, game_date, team_name_home, team_name_away, pts_home, pts_away
FROM kaggle.game_nba_kaggle
WHERE season = 2020
  AND (team_abbreviation_home = 'LAL' OR team_abbreviation_away = 'LAL')
ORDER BY game_date
LIMIT 10;

-- Query 3: Count play-by-play events
SELECT COUNT(*) as total_plays
FROM kaggle.play_by_play_nba_kaggle;

-- Query 4: Get player information
SELECT display_first_last, birthdate, height, weight, position
FROM kaggle.player_nba_kaggle
WHERE display_first_last LIKE '%LeBron%'
LIMIT 5;

-- Query 5: Test JSONB querying
SELECT game_id, data->>'season_type' as season_type, pts_home, pts_away
FROM kaggle.game_nba_kaggle
WHERE season = 2020
LIMIT 10;
```

**Expected performance:**
- Simple queries: <100ms
- Complex joins: <1 second
- Full table scans: 2-5 seconds

---

## Troubleshooting

### Error: "kaggle schema does not exist"

**Solution:**
```bash
# Run schema creation first
psql -U ryanranft -d nba_simulator -f scripts/db/migrations/0_20_kaggle_schema.sql
```

### Error: "SQLite database not found"

**Solution:**
```bash
# Verify database exists
ls -lh /Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite

# If missing, download from Kaggle
python scripts/etl/download_kaggle_basketball.py
```

### Error: "could not connect to server"

**Solution:**
```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Start if needed
brew services start postgresql

# Verify connection
psql -U ryanranft -d nba_simulator -c "SELECT version();"
```

### Migration is slow (>2 hours)

**Possible causes:**
1. **Low disk I/O:** Check disk space and I/O performance
2. **Network latency:** Use localhost connection (not remote)
3. **Too many indexes:** Indexes are created upfront (this is normal)

**Solution:**
```bash
# Monitor progress - migration will complete eventually
# Check PostgreSQL logs for errors
tail -f /usr/local/var/log/postgres.log
```

### Migration interrupted

**Solution:**
```bash
# Resume from checkpoint
python scripts/db/migrations/0_21_kaggle_data_migration.py --resume
```

Checkpoints are saved after each table, so you'll skip already-completed tables.

### Validation fails

**Solution:**
```bash
# Run verbose validation to see specific errors
python validators/phases/phase_0/validate_0_20_kaggle_postgres.py --verbose

# Check specific table
psql -U ryanranft -d nba_simulator -c "SELECT COUNT(*) FROM kaggle.game_nba_kaggle;"

# Compare with SQLite
sqlite3 /Users/ryanranft/nba-simulator-aws/data/kaggle/nba.sqlite "SELECT COUNT(*) FROM game;"
```

---

## Rollback (If needed)

If something goes wrong, you can easily rollback:

```sql
-- Connect to database
psql -U ryanranft -d nba_simulator

-- Drop entire kaggle schema (deletes all tables)
DROP SCHEMA IF EXISTS kaggle CASCADE;

-- Verify removal
\dn
```

**SQLite data remains untouched** - you can re-run migration anytime.

---

## Next Steps

After successful migration:

1. **Update nba_mcp_synthesis database** (if needed):
   ```bash
   # Repeat steps 1-4 for second database
   psql -U ryanranft -d nba_mcp_synthesis -f scripts/db/migrations/0_20_kaggle_schema.sql
   python scripts/db/migrations/0_21_kaggle_data_migration.py  # Update DB config first
   ```

2. **Create views or materialized views** (optional):
   ```sql
   -- Example: Create view for recent games
   CREATE VIEW kaggle.recent_games AS
   SELECT * FROM kaggle.game_nba_kaggle
   WHERE season >= 2020
   ORDER BY game_date DESC;
   ```

3. **Set up backup schedule** (recommended):
   ```bash
   # Backup kaggle schema
   pg_dump -U ryanranft -d nba_simulator -n kaggle -f backup_kaggle_$(date +%Y%m%d).sql
   ```

4. **Update PROGRESS.md**:
   - Mark Phase 0.0003 as "PostgreSQL migration complete"
   - Update "Current Session Context"

5. **Create pull request** (if using Git):
   ```bash
   git add scripts/db/migrations/0_20_kaggle_schema.sql
   git add scripts/db/migrations/0_21_kaggle_data_migration.py
   git add validators/phases/phase_0/validate_0_20_kaggle_postgres.py
   git commit -m "feat: Complete Kaggle to PostgreSQL migration (0.20)"
   git push
   ```

---

## Summary

**Timeline:**
- Schema creation: 5 seconds
- Data migration: 30-60 minutes
- Validation: 5-10 minutes
- **Total: ~1 hour**

**What you get:**
- ✅ 14.1M rows migrated to PostgreSQL
- ✅ Fast queries with proper indexes
- ✅ JSONB flexibility for future enhancements
- ✅ Historical NBA data (1946-2023) in production database
- ✅ Zero data loss (SQLite preserved)

**Files created:**
- `kaggle` schema (16 tables, 65 indexes)
- Checkpoint file (for resume capability)
- Validation report

---

## Questions?

Refer to:
- **Detailed plan:** `docs/plans/KAGGLE_TO_POSTGRESQL_MIGRATION_PLAN.md`
- **Schema reference:** `scripts/db/migrations/0_20_kaggle_schema.sql`
- **Migration script:** `scripts/db/migrations/0_21_kaggle_data_migration.py`
- **Validator:** `validators/phases/phase_0/validate_0_20_kaggle_postgres.py`

---

**Last Updated:** November 9, 2025
**Migration Version:** 0.20
**Status:** Ready for Execution

# ESPN Database Sync Guide

**Purpose:** Make nba_simulator and nba_mcp_synthesis databases identical
**Created:** November 9, 2025
**Status:** Ready to execute

---

## Current State

### nba_simulator (espn schema) - PRIMARY/SOURCE

| Table | Rows | Status |
|-------|------|--------|
| `espn.espn_games` | 45,129 | ✅ Complete |
| `espn.espn_team_stats` | 86,470 | ✅ Complete |
| `espn.espn_plays` | 14,180,218 | ✅ Complete |
| `espn.espn_schedules` | 6,917 | ✅ Complete |

**Total:** 14,312,734 records

### nba_mcp_synthesis (espn_raw schema) - SECONDARY/TARGET

| Table | Rows | Status | Issue |
|-------|------|--------|-------|
| `espn_raw.box_score_nba_espn` | 45,129 | ✅ Complete | Same as source |
| `espn_raw.team_stats_nba_espn` | 258 | ⚠️ Partial | Missing 86,212 rows |
| `espn_raw.pbp_nba_espn` | 14,180,696 | ⚠️ Extra | Has 478 extra rows |
| `espn_raw.schedule_nba_espn` | 0 | ❌ Missing | Table doesn't exist |

**Total:** 14,226,083 records (discrepancies exist)

---

## Discrepancies to Fix

1. **Team Stats:** 86,212 rows missing from nba_mcp_synthesis
2. **Play-by-Play:** 478 extra rows in nba_mcp_synthesis (investigate or delete)
3. **Schedules:** Entire table missing in nba_mcp_synthesis (6,917 rows to add)
4. **Box Scores:** ✅ Already identical

---

## Step-by-Step Sync Process

### Step 1: Inspect Table Schemas

**Run the schema inspection script:**

```bash
cd /Users/ryanranft/nba-simulator-aws

# Activate environment
conda activate nba-aws

# Run inspection
python scripts/migration/inspect_espn_schemas.py
```

**Output:**
- `espn_schemas_inspection.json` - Detailed schema data
- `espn_schemas_comparison_report.md` - Human-readable comparison

**Review the report** to understand:
- Column differences between tables
- Data type mappings needed
- Which database has correct data

---

### Step 2: Dry-Run Comparison

**Run sync script in dry-run mode to see what would change:**

```bash
python scripts/migration/sync_espn_databases.py --dry-run
```

**Expected output:**
```
Comparing Row Counts:
  espn.espn_games → espn_raw.box_score_nba_espn
    Source: 45,129
    Target: 45,129
    Diff: 0 ✓

  espn.espn_team_stats → espn_raw.team_stats_nba_espn
    Source: 86,470
    Target: 258
    Diff: +86,212 ⚠️

  espn.espn_plays → espn_raw.pbp_nba_espn
    Source: 14,180,218
    Target: 14,180,696
    Diff: -478 ⚠️

  espn.espn_schedules → espn_raw.schedule_nba_espn
    Source: 6,917
    Target: 0
    Diff: +6,917 ⚠️
```

---

### Step 3: Investigate Discrepancies

Before syncing, understand why differences exist:

#### A. Why 478 extra PBP rows in nba_mcp_synthesis?

```sql
-- Connect to nba_mcp_synthesis
\c nba_mcp_synthesis

-- Find game_ids that exist in nba_mcp but not in nba_simulator
SELECT DISTINCT game_id
FROM espn_raw.pbp_nba_espn
WHERE game_id NOT IN (
    -- You'll need to query nba_simulator from a different connection
    -- Or export game_id list to compare
);
```

**Possible causes:**
- Extra games loaded to nba_mcp_synthesis
- Duplicate plays
- Different filtering logic

**Decision needed:** Keep extra rows or delete them?

#### B. Why 86,212 missing team_stats in nba_mcp_synthesis?

```sql
-- Check what's in the 258 rows
\c nba_mcp_synthesis
SELECT COUNT(*), MIN(game_date), MAX(game_date)
FROM espn_raw.team_stats_nba_espn;

-- Check if it's just recent games or specific subset
SELECT season, COUNT(*)
FROM espn_raw.team_stats_nba_espn
GROUP BY season
ORDER BY season;
```

**Possible causes:**
- Only loaded current season
- Partial load that was interrupted
- Different table structure/purpose

---

### Step 4: Create Backup

**Before making any changes, backup nba_mcp_synthesis:**

```bash
# Backup entire database
pg_dump -U ryanranft -d nba_mcp_synthesis -F c -f backup_nba_mcp_synthesis_$(date +%Y%m%d_%H%M%S).backup

# Or backup just espn_raw schema
pg_dump -U ryanranft -d nba_mcp_synthesis -n espn_raw -F c -f backup_espn_raw_schema_$(date +%Y%m%d_%H%M%S).backup
```

**Backup size estimate:** ~5-10 GB

---

### Step 5: Execute Sync

**Option A: Sync All Tables (Recommended)**

```bash
# Full sync from nba_simulator → nba_mcp_synthesis
python scripts/migration/sync_espn_databases.py

# This will:
# 1. Delete all data in nba_mcp_synthesis espn_raw tables
# 2. Copy all data from nba_simulator espn tables
# 3. Create schedule table if missing
# 4. Verify row counts match
```

**Option B: Sync Specific Tables**

```bash
# Only sync team_stats and schedules (leave pbp as-is)
python scripts/migration/sync_espn_databases.py --tables team_stats,schedules
```

**Option C: Reverse Sync (Use with CAUTION)**

```bash
# If nba_mcp_synthesis has correct data, sync TO nba_simulator
python scripts/migration/sync_espn_databases.py --reverse --dry-run

# Only do this if you're certain nba_mcp_synthesis is correct!
```

---

### Step 6: Validate Sync

**After sync completes, verify both databases are identical:**

```bash
# Re-run comparison
python scripts/migration/sync_espn_databases.py --dry-run

# Should show all differences = 0
```

**Manual verification:**

```sql
-- nba_simulator counts
\c nba_simulator
SELECT 'espn_games' as table, COUNT(*) FROM espn.espn_games
UNION ALL
SELECT 'espn_team_stats', COUNT(*) FROM espn.espn_team_stats
UNION ALL
SELECT 'espn_plays', COUNT(*) FROM espn.espn_plays
UNION ALL
SELECT 'espn_schedules', COUNT(*) FROM espn.espn_schedules;

-- nba_mcp_synthesis counts
\c nba_mcp_synthesis
SELECT 'box_score_nba_espn' as table, COUNT(*) FROM espn_raw.box_score_nba_espn
UNION ALL
SELECT 'team_stats_nba_espn', COUNT(*) FROM espn_raw.team_stats_nba_espn
UNION ALL
SELECT 'pbp_nba_espn', COUNT(*) FROM espn_raw.pbp_nba_espn
UNION ALL
SELECT 'schedule_nba_espn', COUNT(*) FROM espn_raw.schedule_nba_espn;
```

**Expected result after sync:**

| Metric | nba_simulator | nba_mcp_synthesis | Status |
|--------|---------------|-------------------|--------|
| Games | 45,129 | 45,129 | ✅ Match |
| Team Stats | 86,470 | 86,470 | ✅ Match |
| Plays | 14,180,218 | 14,180,218 | ✅ Match |
| Schedules | 6,917 | 6,917 | ✅ Match |

---

## Rollback Procedure

**If sync fails or produces unexpected results:**

```bash
# Restore from backup
pg_restore -U ryanranft -d nba_mcp_synthesis -c backup_nba_mcp_synthesis_YYYYMMDD_HHMMSS.backup

# Or restore just espn_raw schema
pg_restore -U ryanranft -d nba_mcp_synthesis -n espn_raw backup_espn_raw_schema_YYYYMMDD_HHMMSS.backup
```

---

## Decisions Needed Before Sync

**Please decide:**

1. **Which database is source of truth?**
   - Recommendation: `nba_simulator` (has more complete data)
   - Alternative: `nba_mcp_synthesis` (if you know it has newer/better data)

2. **What to do with 478 extra PBP rows in nba_mcp_synthesis?**
   - Option A: Delete them (assume nba_simulator is correct)
   - Option B: Copy them to nba_simulator (assume nba_mcp has extra games)
   - Option C: Investigate first to understand what they are

3. **Should schedules table be created in nba_mcp_synthesis?**
   - Recommendation: Yes (for consistency)
   - Alternative: No if nba_mcp_synthesis doesn't need schedules

---

## Current Script Status

### ✅ Completed
- [x] Schema inspection script (`inspect_espn_schemas.py`)
- [x] Sync framework with connection and comparison (`sync_espn_databases.py`)
- [x] Dry-run mode for safe testing

### ⏳ TODO (Needs Your Input)
- [ ] Run schema inspection to get column mappings
- [ ] Complete sync logic with proper column mapping
- [ ] Test sync on small subset first
- [ ] Execute full sync

---

## Next Steps

**Immediate:**
1. Run `inspect_espn_schemas.py` to understand table structures
2. Review the generated comparison report
3. Decide on source of truth (nba_simulator recommended)
4. Create backup of nba_mcp_synthesis
5. Run sync in dry-run mode

**After confirming plan:**
6. Execute sync
7. Validate results
8. Update documentation

---

## Questions?

If you encounter issues:
1. Check logs for detailed error messages
2. Verify database connections work
3. Ensure you have write permissions on both databases
4. Review backup before making destructive changes

**Status:** Ready to begin - awaiting your decision on source of truth

---

**Last Updated:** November 9, 2025

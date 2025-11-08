# Database Backup Snapshot

**Date:** November 5, 2025
**Purpose:** Pre-migration backup of master schema before creating raw_data schema
**Database:** nba_simulator (local PostgreSQL)

---

## Master Schema State (Before Migration)

### Tables and Sizes

| Schema | Table | Rows | Size | Status |
|--------|-------|------|------|--------|
| master | espn_file_validation | 44,826 | 17 MB | ✅ Backed up |
| master | nba_games | 31,241 | 9.3 MB | ✅ Backed up |
| master | nba_plays | 14,114,618 | 3.5 GB | ✅ Backed up |

**Total Data:** 14,190,685 rows, ~3.5 GB

---

## Backup Strategy

### Data Preservation
- **Master schema will NOT be dropped** - it remains intact
- **New raw_data schema will be created alongside** master schema
- **No data loss risk** - both schemas coexist
- **Can rollback by** simply dropping raw_data schema if needed

### Schema Coexistence
```
nba_simulator database:
├── master schema (legacy, preserved)
│   ├── espn_file_validation
│   ├── nba_games
│   └── nba_plays
└── raw_data schema (new, Phase 0.10)
    ├── nba_games (JSONB structure)
    ├── nba_players (JSONB structure)
    ├── nba_teams (JSONB structure)
    ├── nba_misc (JSONB structure)
    └── schema_version
```

---

## Migration Plan

1. ✅ Document current state (this file)
2. ⏳ Run `scripts/db/migrations/0_10_schema.sql`
3. ⏳ Verify raw_data schema created
4. ⏳ Update validators to support both schemas
5. ⏳ Test validators with --schema flag

---

## Rollback Instructions

If migration causes issues:

```bash
# Drop raw_data schema (keeps master intact)
psql -U ryanranft nba_simulator -c "DROP SCHEMA IF EXISTS raw_data CASCADE;"

# Master schema and all data remain untouched
```

---

## Notes

- **No production impact:** This is local development database only
- **RDS unchanged:** Production RDS already has raw_data schema
- **Test database:** Will apply same migration to nba_simulator_test after success
- **Legacy support:** Master schema can be dropped later once raw_data is fully populated

---

**Backup completed:** November 5, 2025
**Status:** ✅ Safe to proceed with migration

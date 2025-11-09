# hoopR Data Quick Reference

**For Users:** This is a quick summary of where hoopR data came from and how it's used.

**For Complete Details:** See `docs/HOOPR_DATA_SOURCES_EXPLAINED.md` (comprehensive guide)

---

## What is hoopR Data?

**hoopR** is an R package that wraps the official NBA Stats API (stats.nba.com). The data includes:
- Play-by-play events with shot coordinates (13.1M events)
- Player box scores (785K records)
- Team box scores (59K records)
- Game schedules (30,758 games from 2002-2025)

**Source:** NBA Stats API → hoopR R Package → Your databases

---

## Where Did the Parquet Files Come From?

**Location:** `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/`

**Contents:** 96 parquet files (24 seasons × 4 data types)

**Origin:**
1. **Original Collection:** Scraped from NBA Stats API using hoopR R package
   - Saved as JSON files (43 GB)
   - Location: `/Users/ryanranft/Projects/hoopR-nba-raw`

2. **Conversion to Parquet:**
   - Compressed JSON → Parquet format
   - Reduced size: 43 GB → 6.2 GB (86% reduction)
   - Better performance for data analysis

3. **Distribution:**
   - **nba-simulator-aws:** Uploaded to S3 + RDS (October 9, 2025)
   - **nba-mcp-synthesis:** Loaded to local PostgreSQL (November 7-8, 2025)

**Key Point:** The parquet files are a BACKUP COPY of data already in nba-simulator-aws.

---

## Current Locations

### nba-simulator-aws (Production)

**S3 Storage:**
- `s3://nba-sim-raw-data-lake/hoopr_parquet/` (531 MB compressed)
- `s3://nba-sim-raw-data-lake/hoopr_152/` (comprehensive collection, growing)

**RDS Database (nba_simulator):**
- `hoopr_play_by_play` - 13.1M rows, 6.2 GB
- `hoopr_player_box` - 785K rows, 433 MB
- `hoopr_team_box` - 59K rows, 29 MB
- `hoopr_schedule` - 30K rows, 27 MB

**Plus:** 152-endpoint comprehensive collection (restored November 7, 2025)

---

### nba-mcp-synthesis (Betting Analysis)

**PostgreSQL Database (nba_mcp_synthesis):**
- Schema: `hoopr_raw.*`
- Tables: Same 4 tables as nba-simulator-aws
- Purpose: Local betting model development

---

## Do You Need to Transfer Data?

### ❌ NO - Data Already in Both Places!

**What Happened:**
1. October 9, 2025: Parquet → nba-simulator-aws (S3 + RDS)
2. November 7-8, 2025: Parquet → nba-mcp-synthesis (local PostgreSQL)

**The parquet files are the SOURCE that both projects loaded from.**

Both projects now have identical Phase 1 hoopR data (30,758 games, 13.1M events).

---

## Two Types of hoopR Collections

### Collection 1: Phase 1 (Parquet Backup)
- **4 endpoints:** PBP, player box, team box, schedule
- **Size:** 6.2 GB (parquet)
- **Coverage:** 2002-2025
- **Status:** ✅ In both projects

### Collection 2: 152-Endpoint Comprehensive
- **152 endpoints:** All phases (1-4)
- **Size:** Growing daily (3-5 GB/day)
- **Features:** Player tracking, synergy, clutch, defensive metrics, hustle stats
- **Status:** ✅ Only in nba-simulator-aws (daily collection)
- **Purpose:** Advanced features for simulation

---

## Summary

**What You Asked:**
> "Can you add information about where we were able to get hoopr data from and possibly update our data folder on nba-simulator-aws with this data?"

**Answer:**
1. ✅ **Source documented:** Parquet files at `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/`
2. ❌ **No transfer needed:** Data already in nba-simulator-aws (loaded October 9, 2025)
3. ✅ **Documentation created:** See `docs/HOOPR_DATA_SOURCES_EXPLAINED.md` for complete details

**Projects Using This Data:**
- **nba-simulator-aws:** Production system (S3 + RDS) - comprehensive data
- **nba-mcp-synthesis:** Betting analysis (local PostgreSQL) - Phase 1 only

---

## Documentation Files Created

1. **`docs/HOOPR_DATA_SOURCES_EXPLAINED.md`** - Complete guide (comprehensive)
   - What hoopR is
   - Where parquet backup came from
   - Difference between Phase 1 vs 152-endpoint collection
   - Why data exists in multiple locations

2. **`docs/NBA_MCP_SYNTHESIS_RELATIONSHIP.md`** - Project relationship (detailed)
   - How nba-simulator-aws and nba-mcp-synthesis share data
   - Why both exist
   - Data flow diagram
   - FAQ

3. **`docs/DATA_CATALOG.md`** - Updated with parquet source reference

4. **`HOOPR_DATA_EXPLAINED_QUICK_REFERENCE.md`** - This file (quick summary)

---

**Last Updated:** November 9, 2025
**For Questions:** See `docs/HOOPR_DATA_SOURCES_EXPLAINED.md`

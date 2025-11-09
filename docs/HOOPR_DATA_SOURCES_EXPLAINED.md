# hoopR Data Sources - Complete Explanation

**Created:** November 9, 2025
**Purpose:** Clarify where hoopR data comes from and how it relates across projects

---

## Executive Summary

**What is hoopR?**

hoopR is an R package that provides a wrapper around the official NBA Stats API (stats.nba.com). It allows programmatic access to NBA data including:
- Play-by-play events with shot coordinates
- Player and team box scores
- Game schedules and metadata
- Advanced statistics and tracking data

**Data Lineage:**
```
NBA Stats API (stats.nba.com)
    ↓
hoopR R Package (wrapper)
    ↓
Parquet Backup Files (/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/)
    ↓
Multiple Destinations:
    1. nba-simulator-aws (S3 + RDS) ← Primary production
    2. nba-mcp-synthesis (Local PostgreSQL) ← Betting analysis
```

---

## hoopR Data Collections: Two Different Scopes

### Collection 1: Phase 1 Bulk Data (Parquet Backup)

**What:** 4 basic endpoints providing core game data

**Endpoints:**
1. `load_nba_pbp` - Play-by-play events
2. `load_nba_player_box` - Player box scores
3. `load_nba_team_box` - Team box scores
4. `load_nba_schedule` - Game schedules

**Coverage:**
- **Seasons:** 2002-2025 (24 complete seasons)
- **Games:** 30,758 total
- **Play-by-Play Events:** 13,074,829
- **Player Box Scores:** 785,505
- **Team Box Scores:** 59,670

**Storage Locations:**
- **Original Collection:** `/Users/ryanranft/Projects/hoopR-nba-raw` (43 GB JSON)
- **Parquet Backup:** `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/` (6.2 GB parquet)
- **S3:** `s3://nba-sim-raw-data-lake/hoopr_parquet/` (531 MB)
- **RDS (nba-simulator-aws):** 4 tables, 6.7 GB
- **PostgreSQL (nba-mcp-synthesis):** `hoopr_raw.*` schema, 13.95M rows

**Data Format:**
```
/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/
├── play_by_play/
│   ├── nba_play_by_play_2002.parquet
│   ├── nba_play_by_play_2003.parquet
│   └── ... (24 files, one per season)
├── player_box/
│   ├── nba_player_box_2002.parquet
│   └── ... (24 files)
├── team_box/
│   ├── nba_team_box_2002.parquet
│   └── ... (24 files)
└── schedule/
    ├── nba_schedule_2002.parquet
    └── ... (24 files)
```

**Total:** 96 parquet files (24 seasons × 4 data types)

---

### Collection 2: Comprehensive 152-Endpoint Collection (November 2025)

**What:** Complete NBA Stats API access across 152 unique endpoints

**Endpoint Breakdown:**
- **Phase 1:** 4 bulk loaders (same as parquet backup)
- **Phase 2:** 25 static/reference endpoints (league leaders, player profiles, draft data)
- **Phase 3:** 40 per-season dashboards (clutch stats, tracking, hustle)
- **Phase 4:** 87 per-game box scores (advanced metrics, synergy, defense)

**Features Added (Beyond Parquet Data):**
- Player tracking (speed, distance, touches)
- Synergy play types (transition, isolation, pick & roll)
- Clutch performance splits
- Defensive impact metrics
- Hustle stats (deflections, charges, screens)
- Shot charts and shooting zones
- Lineup combinations and effectiveness
- Passing networks

**Daily Collection:**
- Runs at 3:00 AM daily
- 2-3 hour runtime
- 3-5 GB data per day
- Autonomous via ADCE system

**Storage:**
- S3: `s3://nba-sim-raw-data-lake/hoopr_152/`
- RDS: Multiple tables (schema to be determined)

**Status:** ✅ Restored November 7, 2025 (previously reduced to incremental-only)

---

## Where the Parquet Data Came From

### Original Collection Process

**Timeline:**
1. **2023-2024:** Initial collection using hoopR R package
   - Scraped from NBA Stats API
   - Saved as JSON files
   - Location: `/Users/ryanranft/Projects/hoopR-nba-raw` (43 GB)

2. **Processing to Parquet:**
   - Converted JSON → Parquet for efficiency
   - Reduced size: 43 GB → 6.2 GB (86% reduction)
   - Location: `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/`
   - 96 parquet files (24 seasons × 4 data types)

3. **October 9, 2025:** Loaded to nba-simulator-aws RDS
   - Script: `scripts/db/load_hoopr_to_rds.py`
   - Created 4 tables in RDS
   - 6.7 GB database size
   - 10-minute load time (33,416 rows/sec)

4. **November 7-8, 2025:** Loaded to nba-mcp-synthesis
   - Script: `scripts/load_parquet_to_postgres.py`
   - Created `hoopr_raw.*` schema
   - 13.95M rows total
   - Used for betting model development

### Why Parquet Format?

**Advantages:**
- **Size:** 86% smaller than JSON (43 GB → 6.2 GB)
- **Speed:** Columnar format = faster queries
- **Compatibility:** Works with R, Python, SQL
- **Compression:** Built-in compression without quality loss
- **Schema:** Self-describing (includes data types)

**Trade-offs:**
- Not human-readable (vs JSON)
- Requires special libraries to read
- Fixed schema (can't easily add fields)

---

## Data Flow: From NBA API to Multiple Projects

### Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ NBA Stats API (stats.nba.com)                               │
│ - Official NBA data source                                  │
│ - 152+ endpoints available                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ hoopR R Package                                             │
│ - Wrapper around NBA Stats API                              │
│ - Handles authentication, rate limiting                     │
│ - Returns R data frames                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────┴──────────────────────┐
         ▼                               ▼
┌──────────────────────┐      ┌──────────────────────────┐
│ Collection 1         │      │ Collection 2             │
│ Phase 1 Only         │      │ All 152 Endpoints        │
│ (4 endpoints)        │      │ (Comprehensive)          │
└─────────┬────────────┘      └──────────┬───────────────┘
          │                              │
          ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────┐
│ Parquet Backup       │      │ Daily CSV Collection     │
│ 96 files, 6.2 GB     │      │ 3-5 GB/day               │
│ 2002-2025            │      │ All phases               │
└─────────┬────────────┘      └──────────┬───────────────┘
          │                              │
    ┌─────┴─────┐                  ┌─────┴─────┐
    ▼           ▼                  ▼           ▼
┌─────────┐ ┌──────────┐     ┌─────────┐ ┌──────────┐
│ S3      │ │ RDS      │     │ S3      │ │ RDS      │
│ Parquet │ │ 4 tables │     │ hoopr_  │ │ (future) │
│ 531 MB  │ │ 6.7 GB   │     │ 152/    │ │          │
└─────────┘ └────┬─────┘     └─────────┘ └──────────┘
                 │
          ┌──────┴──────────┐
          ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│ nba-simulator    │  │ nba-mcp-         │
│ -aws             │  │ synthesis        │
│ (Production)     │  │ (Betting)        │
└──────────────────┘  └──────────────────┘
```

---

## Project-Specific Usage

### nba-simulator-aws (Production System)

**Purpose:** Temporal panel data system for NBA historical analysis and simulation

**hoopR Data Used:**
- **Source:** Both Collection 1 (parquet) AND Collection 2 (152 endpoints)
- **Storage:** S3 + RDS (AWS cloud)
- **Tables:**
  - `hoopr_play_by_play` - 13.1M events, 6.2 GB
  - `hoopr_player_box` - 785K rows, 433 MB
  - `hoopr_team_box` - 59K rows, 29 MB
  - `hoopr_schedule` - 30K games, 27 MB
- **Integration:** Combined with ESPN data via unified views
- **Usage:** ML model training, game simulation, econometric analysis

**Collection Method:**
- Phase 1: Loaded from parquet backup (October 9, 2025)
- Phase 2-4: Daily autonomous collection (November 7, 2025+)

---

### nba-mcp-synthesis (Betting Analysis)

**Purpose:** Local betting model development and analysis

**hoopR Data Used:**
- **Source:** Collection 1 only (parquet backup)
- **Storage:** Local PostgreSQL database (`nba_mcp_synthesis`)
- **Schema:** `hoopr_raw.*`
- **Tables:**
  - `hoopr_raw.nba_play_by_play` - 13.1M rows
  - `hoopr_raw.nba_player_box` - 785K rows
  - `hoopr_raw.nba_team_box` - 59K rows
  - `hoopr_raw.nba_schedule` - 30K rows

**Loading Process (November 7-8, 2025):**
1. Day 1: Loaded parquet → PostgreSQL
2. Day 2: Reorganized `raw.*` → `hoopr_raw.*` for clarity
3. Generated ML features for betting models

**Why Not Use 152 Endpoints?**
- Betting models only need Phase 1 data
- 152-endpoint collection is 500+ GB (unnecessary for local analysis)
- Parquet data sufficient for feature engineering

---

## Should You Transfer Parquet Data to nba-simulator-aws?

### Short Answer: **No, it's already there!**

### Explanation:

The parquet files at `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/` are a **backup copy** of data that's already in nba-simulator-aws.

**Current State:**
- ✅ Parquet data loaded to S3: October 2025
- ✅ Parquet data loaded to RDS: October 9, 2025
- ✅ RDS tables created and indexed
- ✅ Unified views combining ESPN + hoopR

**What Happened:**
1. Original collection → JSON (43 GB)
2. Converted → Parquet (6.2 GB) for backup
3. Uploaded → S3 (531 MB compressed)
4. Loaded → RDS (6.7 GB with indexes)
5. Also loaded → nba-mcp-synthesis for local analysis

**The parquet files are a portable backup, not a separate data source.**

---

## Data Not in Parquet Files (152-Endpoint Collection)

### What's Missing from Parquet Backup:

**Phase 2: Static/Reference Data (25 endpoints)**
- League leaders, standings
- Player profiles, awards, college stats
- Draft history, combine stats
- Coaching staff

**Phase 3: Per-Season Dashboards (40 endpoints)**
- Clutch performance splits
- Player tracking (shots, defense, rebounding)
- Hustle stats by team/player
- Lineup combinations

**Phase 4: Per-Game Box Scores (87 endpoints)**
- Traditional/advanced box scores
- Tracking data (speed, distance, touches)
- Defensive impact metrics
- Shooting dashboard by zone
- Passing networks
- Synergy play types

**Why Not in Parquet?**
- These endpoints weren't included in original Phase 1 collection
- Total data would be ~500 GB (vs 6.2 GB for Phase 1)
- Collected separately via daily autonomous scraper (November 2025+)

---

## Recommendations

### For nba-simulator-aws:

**✅ Current Setup is Correct:**
1. Phase 1 data (parquet backup) → Already in S3 + RDS
2. Phase 2-4 data (152 endpoints) → Daily collection via ADCE
3. No action needed to "transfer" parquet data

**✅ Maintain Both Collections:**
1. Keep parquet backup for disaster recovery
2. Keep 152-endpoint daily collection running
3. Phase 1 provides foundation, Phase 2-4 adds depth

### For nba-mcp-synthesis:

**✅ Current Setup is Appropriate:**
1. Phase 1 parquet data sufficient for betting models
2. Local PostgreSQL faster than network calls to RDS
3. No need for 152-endpoint collection (betting models don't need it)

**Optional Enhancements:**
- If you need advanced features, connect to nba-simulator-aws RDS
- Or run selective Phase 2/3 endpoints locally (not full 152)

---

## File Locations Reference

### Production Data (nba-simulator-aws)

**S3 Locations:**
```
s3://nba-sim-raw-data-lake/
├── hoopr_parquet/           # Phase 1 backup (531 MB)
│   ├── play_by_play/        # 24 files
│   ├── player_box/          # 24 files
│   ├── team_box/            # 24 files
│   └── schedule/            # 24 files
└── hoopr_152/               # Comprehensive collection (growing)
    ├── phase1_bulk/
    ├── phase2_static/
    ├── phase3_dashboards/
    └── phase4_boxscores/
```

**RDS Tables:**
```
nba_simulator database:
├── hoopr_play_by_play       # 13.1M rows, 6.2 GB
├── hoopr_player_box         # 785K rows, 433 MB
├── hoopr_team_box           # 59K rows, 29 MB
└── hoopr_schedule           # 30K rows, 27 MB
```

### Local Backups

**Parquet Files (Primary Backup):**
```
/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/
├── play_by_play/            # 24 parquet files
├── player_box/              # 24 parquet files
├── team_box/                # 24 parquet files
└── schedule/                # 24 parquet files
Total: 96 files, 6.2 GB
```

**Original JSON Collection:**
```
/Users/ryanranft/Projects/hoopR-nba-raw/
└── [29,688 JSON files, 43 GB]
```

**Processed Structured Data:**
```
/Users/ryanranft/Projects/hoopR-nba-data/
└── [235 files, 8.6 GB]
```

---

## Frequently Asked Questions

### Q: Is the parquet data the same as what's in RDS?
**A:** Yes, exactly the same. The parquet files are a backup copy.

### Q: Should I load the parquet files to nba-simulator-aws?
**A:** No, they're already there (loaded October 9, 2025).

### Q: Why do I have multiple copies?
**A:**
- S3: Cloud storage, accessible from anywhere
- RDS: Fast queries, production use
- Parquet backup: Disaster recovery
- nba-mcp-synthesis: Local analysis without cloud costs

### Q: What's the difference between parquet and 152-endpoint collection?
**A:**
- Parquet = Phase 1 only (4 endpoints, basic data)
- 152-endpoint = All phases (152 endpoints, comprehensive)

### Q: Do I need the 152-endpoint collection?
**A:**
- For nba-simulator-aws: Yes (for advanced features)
- For nba-mcp-synthesis: No (betting models don't need it)

### Q: How much does hoopR data cost in S3?
**A:**
- Phase 1 parquet: $0.012/month (531 MB)
- 152-endpoint collection: ~$3.45/month (150 GB/month growth)
- Total: ~$3.50/month (well within $150 budget)

---

## Summary

**What You Have:**
1. ✅ Parquet backup (6.2 GB) at `/Users/ryanranft/Desktop/sports_data_backup/hoopR/nba/`
2. ✅ Same data in S3 (`hoopr_parquet/`)
3. ✅ Same data in RDS (`hoopr_*` tables)
4. ✅ Same data in nba-mcp-synthesis (`hoopr_raw.*` schema)
5. ✅ Comprehensive 152-endpoint collection (daily, ongoing)

**What You Don't Need To Do:**
- ❌ Transfer parquet to nba-simulator-aws (already there)
- ❌ Re-upload to S3 (already uploaded)
- ❌ Re-load to RDS (already loaded)

**What You Should Do:**
- ✅ Keep parquet backup for disaster recovery
- ✅ Keep 152-endpoint collection running daily
- ✅ Use parquet data in nba-mcp-synthesis for betting analysis
- ✅ Use RDS data in nba-simulator-aws for production

---

**Last Updated:** November 9, 2025
**Status:** ✅ Complete - All hoopR data sources documented and clarified

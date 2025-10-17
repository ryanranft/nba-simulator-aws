# NBA Simulator Data Catalog

**Version:** 1.0
**Last Updated:** October 9, 2025
**Status:** ✅ AUTHORITATIVE - Single source of truth for all data collection information

**⚠️ IMPORTANT:** This file is the **ONLY** authoritative source for data collection statistics. All other documentation files should reference this catalog, not duplicate its information.

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Data Sources Overview](#data-sources-overview)
3. [Source 1: ESPN API](#source-1-espn-api)
4. [Source 2: hoopR](#source-2-hoopr)
5. [Source 3: NBA.com Stats API](#source-3-nbacom-stats-api)
6. [Source 4: Basketball Reference](#source-4-basketball-reference)
7. [Source 5: Kaggle Database](#source-5-kaggle-database)
8. [Source 6: SportsDataverse](#source-6-sportsdataverse)
9. [Data Quality Metrics](#data-quality-metrics)
10. [Cross-Source ID Mapping](#cross-source-id-mapping)
11. [Coverage Comparison Matrix](#coverage-comparison-matrix)
12. [Auto-Update Integration](#auto-update-integration)
13. [Change Log](#change-log)

---

## Quick Reference

**Last Full Update:** October 09, 2025 03:45 PM CT

| Source | Date Range | Status | Games | PBP Events | Files | Size | Location |
|--------|-----------|--------|-------|-----------|-------|------|----------|
| ESPN API | 1993-2025 | ✅ COMPLETE | 44,826 | 14,114,618 | 70,522 (S3) / 147,382 (local) | 55 GB (S3) / 119 GB (local) | S3 + Local + RDS |
| hoopR | 2002-2025 | ✅ COMPLETE | 30,758 | 13,074,829 | 410 | 8.2 GB | S3 + Local + RDS |
| NBA.com API | 1996-2025 | ⏸️ PAUSED | 0 | 0 | 0 | 0 GB | Not started |
| Basketball Ref | 1950-2025 | ✅ COMPLETE | N/A | N/A | 42 | 156 MB | S3 |
| Kaggle | 2004-2020 | ✅ COMPLETE | 26,496 | 0 | 17 tables | 280 MB | Local DB |
| SportsDataverse | 2002-2023 | ❌ DEPRECATED | 0 | 0 | 0 | 0 GB | Not used |

**RDS Database (nba_simulator):**
- **Total Size:** 13.9 GB (7.2 GB ESPN + 6.7 GB hoopR)
- **ESPN Tables:** `temporal_events` (5.6 GB, 14.1M rows) + 15 tables
- **hoopR Tables:** `hoopr_play_by_play` (6.2 GB, 13.1M rows) + 3 tables
- **Unified Views:** 3 views combining ESPN + hoopR (40,652 games, 1993-2025)

**Total Collection:**
- **Combined Files:** 165,614+ files
- **Combined Size:** 127+ GB
- **Combined Games:** 76,000+ unique games
- **Combined PBP Events:** 28,000,000+ events

---

## Data Sources Overview

### Primary Sources (Production Quality)

1. **ESPN API** - Most comprehensive PBP data (1993-2025), already in RDS
2. **hoopR** - Modern era validation (2002-2025), R package, 21% complete
3. **NBA.com Stats API** - Official NBA data (1996-2025), advanced metrics

### Secondary Sources (Validation & Historical)

4. **Basketball Reference** - Historical depth (1950-2025), aggregated stats
5. **Kaggle Database** - Pre-cleaned dataset (2004-2020), quality benchmark
6. **SportsDataverse** - DEPRECATED (redundant with hoopR)

### Data Integration Strategy

**Priority Hierarchy (for deduplication):**
1. ESPN API (highest quality, most complete)
2. NBA.com Stats API (official source)
3. hoopR (modern era validation)
4. Basketball Reference (historical fill)
5. Kaggle (validation only)

**Quality Score Calculation:**
- 100 pts: Millisecond-precision timestamps
- 90 pts: Second-precision timestamps
- 80 pts: Minute-precision timestamps
- 70 pts: Quarter-level aggregation
- 60 pts: Game-level aggregation
- 50 pts: Season-level aggregation

---

## Source 1: ESPN API

**Official Name:** ESPN API (Play-by-Play JSON)
**Status:** ✅ COMPLETE
**Coverage:** 1993-09-30 to 2025-present
**Last Updated:** Daily (automatic overnight scraper)

### Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Games** | 44,826 | All regular season + playoffs |
| **Games with PBP** | 31,241 | 69.7% coverage |
| **Total PBP Events** | 14,114,618 | In RDS `temporal_events` table |
| **S3 Files** | 70,522 | JSON format |
| **S3 Size** | 119 GB | `s3://nba-sim-raw-data-lake/espn/` |
| **Local Database** | 1.7 GB | `/tmp/espn_local.db` (SQLite) |

### Coverage by Era

| Era | Date Range | Games | PBP Coverage | Events/Game | Quality |
|-----|-----------|-------|--------------|-------------|---------|
| **Early Digital** | 1993-2001 | 11,210 | 5.3% (594 games) | ~22 events | Low |
| **Transition** | 2002-2010 | 14,464 | 86.9% (12,569 games) | ~382 events | Medium |
| **Modern** | 2011-2025 | 19,152 | 94.4% (18,078 games) | ~435 events | High |

**Key Insights:**
- PBP quality dramatically improves after 2001 (5.3% → 86.9%)
- Modern era has near-complete coverage (94.4%)
- Early era (1993-2001) has metadata but sparse PBP events

### File Structure

```
s3://nba-sim-raw-data-lake/espn/
├── {season}/          # e.g., "2024", "2023"
│   └── {game_id}/     # e.g., "401584800"
│       ├── boxscore.json      # Team/player box scores
│       ├── gameinfo.json      # Game metadata
│       ├── playbyplay.json    # PBP events
│       ├── rosters.json       # Team rosters
│       └── summary.json       # Game summary
```

### Data Quality

- ✅ **Timestamps:** Second-precision (90 pts quality score)
- ✅ **Event Types:** 200+ unique action types
- ✅ **Player IDs:** Consistent ESPN IDs
- ✅ **Team IDs:** Consistent ESPN abbreviations
- ⚠️ **Early Era:** Sparse PBP in 1993-2001

### Scraper Information

- **Location:** `~/0espn/` (external repository)
- **Language:** Python 3.x
- **Cadence:** Daily overnight scraper
- **Runtime:** ~2-4 hours for daily updates
- **S3 Upload:** Automatic after each game

**Documentation:** See `docs/ESPN_SCRAPER_GUIDE.md` for complete scraper details.

### RDS Integration

- **Table:** `temporal_events` (5.6 GB, 14,114,618 rows)
- **Load Date:** October 2, 2025
- **Load Script:** `scripts/db/load_espn_events.py`
- **Status:** ✅ Complete and indexed

### Validation Baseline

**2023-2024 Season Validation:**
- Games: 1,230 regular season + 88 playoffs = 1,318 total
- Players: 530 active roster
- Teams: 30 NBA teams
- Expected PBP events: ~575,000 (1,318 games × 435 avg events/game)

---

## Source 2: hoopR

**Official Name:** hoopR R Package (nbahoopR functions)
**Status:** ✅ COMPLETE (Local + S3 + RDS)
**Coverage:** 2002-2025 (24 complete seasons)
**Last Updated:** October 9, 2025 (~6:00 PM)

### Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Seasons** | 24 seasons | 2002-2025 (complete) |
| **Total Games** | 30,758 | Verified from RDS schedule table |
| **PBP Events** | 13,074,829 | Loaded to RDS `hoopr_play_by_play` |
| **Player Box Scores** | 785,505 | Loaded to RDS `hoopr_player_box` |
| **Team Box Scores** | 59,670 | Loaded to RDS `hoopr_team_box` |
| **Schedules** | 30,758 | Loaded to RDS `hoopr_schedule` |
| **S3 Parquet Files** | 96 files | 531 MB in `hoopr_parquet/` |
| **S3 CSV Files** | 314 files | 7.7 GB in `hoopr_phase1/` |
| **Total S3 Size** | 8.2 GB | Combined parquet + CSV |
| **RDS Size** | 6.7 GB | 4 tables + indexes |

### Scraper Phases

#### Phase 1A: Bulk Loaders (✅ COMPLETE)
- **Play-by-Play:** 13.9M events (96 CSV files, 2.5 GB)
- **Player Box Scores:** 810K rows
- **Team Box Scores:** 63K rows
- **Schedule:** 31K games

#### Phase 1B: League Dashboards (✅ COMPLETE)
- **League Player Stats:** Per-season aggregates
- **League Team Stats:** Per-season aggregates
- **Standings:** Per-season standings
- **Files:** 218 CSV files (5.24 GB)

#### Phase 2: Per-Game Endpoints (⏸️ PLANNED)
- ~30 endpoints requiring game_ids
- Shot charts, matchup data, game logs
- Estimated: 50 GB, 100 hours runtime

#### Phase 3: Per-Player/Team (⏸️ PLANNED)
- ~70 endpoints requiring player/team IDs
- Career stats, advanced metrics, tracking data
- Estimated: 100 GB, 150 hours runtime

### Data Quality

- ✅ **Timestamps:** Minute-precision (80 pts quality score)
- ✅ **Event Types:** Standard NBA event codes
- ✅ **Player IDs:** NBA official IDs
- ✅ **Team IDs:** NBA official IDs
- ⚠️ **Coverage Gap:** Pre-2002 not available

### Local Data Locations

**Discovery:** October 9, 2025 - Found 57.8 GB of hoopR data already collected locally

1. **Primary:** `/Users/ryanranft/Projects/hoopR-nba-raw` (43 GB - 29,688 JSON files)
2. **Structured:** `/Users/ryanranft/Projects/hoopR-nba-data` (8.6 GB - 235 files)
3. **Analysis-Ready:** `/Users/ryanranft/Desktop/sports_data_backup/hoopR` (6.2 GB - 120 parquet files)

### S3 Locations

- **Parquet (uploaded Oct 9):** `s3://nba-sim-raw-data-lake/hoopr_parquet/`
  - `play_by_play/` - 24 files (393 MB) - 2002-2025 seasons
  - `player_box/` - 24 files (15 MB) - 2002-2025 seasons
  - `schedule/` - 24 files (3.4 MB) - 2002-2025 seasons
  - `team_box/` - 24 files (3.1 MB) - 2002-2025 seasons
- **CSV (uploaded Oct 8):** `s3://nba-sim-raw-data-lake/hoopr_phase1/` (7.7 GB, 314 files)

### Scraper Information

- **Location:** `scripts/etl/scrape_hoopr_phase1_foundation.R`
- **Language:** R (hoopR package v2.0+)
- **Status:** ✅ COMPLETE - Data collected and loaded to RDS

### RDS Integration

- **Load Date:** October 9, 2025 (~4:30 PM)
- **Load Script:** `scripts/db/load_hoopr_to_rds.py`
- **Load Time:** 10 minutes (13.1M rows at 33,416 rows/sec)
- **Tables Created:**
  - `hoopr_play_by_play` (6.2 GB, 13,074,829 rows, 63 columns)
  - `hoopr_player_box` (433 MB, 785,505 rows, 56 columns)
  - `hoopr_team_box` (29 MB, 59,670 rows, 56 columns)
  - `hoopr_schedule` (27 MB, 30,758 rows, 77 columns)
- **Indexes:** 6 indexes on game_id and game_date columns
- **Status:** ✅ Complete and indexed

### Unified ESPN + hoopR Views

Created October 9, 2025 to provide seamless 33-year coverage (1993-2025):

**View: `unified_play_by_play`**
- ESPN data: Pre-2002 (1993-2001)
- hoopR data: 2002+ (modern era with 100% coverage)
- Combined: Seamless play-by-play events across all eras

**View: `unified_schedule`**
- Total games: 40,652 (1993-2025)
- ESPN games: 11,210 (1993-2001, 27.2%)
- hoopR games: 29,442 (2002-2025, 72.8%)

**View: `data_source_coverage`**
- Documentation view showing year-by-year source coverage
- Enables analysis of data quality by era

**Creation Script:** `scripts/db/create_unified_espn_hoopr_view.py`

**Schema Mappings:**
- ESPN `clock_display` → hoopR `clock_display_value`
- ESPN `play_text` → hoopR `text`
- ESPN `game_id` (VARCHAR) → hoopR `game_id` (INTEGER, cast to TEXT)
- ESPN `home_team_id` → hoopR `home_id`

### Validation Strategy

**Cross-validation with ESPN:**
- Match on date + team abbreviations
- Validate PBP event counts (hoopR typically +2-5% vs ESPN)
- Check for systematic gaps by season
- Compare player/team IDs for consistency

---

## Source 3: NBA.com Stats API

**Official Name:** NBA.com Official Stats API
**Status:** ⏸️ PAUSED (rate limiting issues)
**Coverage:** 1996-present (official NBA data)
**Last Attempt:** October 6, 2025

### Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| **Planned Seasons** | 30 seasons | 1996-2025 |
| **Estimated Games** | 38,000+ | All games since 1996 |
| **Features** | 269-289 | After Tier 1 implementation |
| **Current Status** | ⏸️ PAUSED | Rate limiting (429 errors) |
| **Files Collected** | 0 | Testing only |
| **Estimated Runtime** | 750-900 hours | Full production run |

### Endpoint Tiers

#### Tier 1: Advanced Box Scores (✅ IMPLEMENTED)
- `BoxScoreAdvancedV2` - Efficiency metrics
- `BoxScoreDefensiveV2` - Defensive stats
- `BoxScoreFourFactorsV2` - Four factors
- `BoxScoreMiscV2` - Miscellaneous stats
- `BoxScorePlayerTrackV2` - Player tracking
- `BoxScoreScoringV2` - Scoring breakdown
- `BoxScoreTraditionalV2` - Traditional stats
- `BoxScoreUsageV2` - Usage rates

#### Tier 1: Player Tracking (✅ IMPLEMENTED)
- `PlayerDashPtPass` - Passing stats
- `PlayerDashPtReb` - Rebounding stats
- `PlayerDashPtShotDefend` - Shot defense
- `PlayerDashPtShots` - Shot tracking

#### Tier 2: Advanced Analytics (⏸️ PLANNED)
- Shot charts, hustle stats, defense dashboards
- Estimated: +50 features
- Requires careful rate limiting

### Known Issues

- **Rate Limiting:** 429 "Too Many Requests" errors
- **Inconsistent Responses:** Some endpoints return empty data pre-2010
- **Testing Configuration:** Current script uses 100 games/season limit
- **Production Estimate:** 31-37 days runtime (requires EC2 deployment)

### Scraper Information

- **Location:** `scripts/etl/scrape_nba_api_comprehensive.py`
- **Language:** Python 3.x (nba_api package)
- **Rate Limit:** 0.6-1.0 seconds between requests
- **Status:** Paused pending rate limit resolution
- **Overnight Wrapper:** `scripts/etl/overnight_nba_api_comprehensive.sh`

### Recommended Strategy

1. **Start with test run:** 10 games, verify all endpoints work
2. **Deploy to EC2:** Run full production scraper remotely
3. **Implement checkpoint recovery:** Resume on failure
4. **Monitor rate limits:** Adjust delays dynamically
5. **Validate against ESPN:** Cross-check event counts

---

## Source 4: Basketball Reference

**Official Name:** Basketball Reference Web Scraper
**Status:** ✅ COMPLETE
**Coverage:** 1950-2025 (75 NBA seasons)
**Last Updated:** October 8, 2025

### Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Seasons** | 75 seasons | 1950-2025 (BAA 1947-1949 not available) |
| **Files Collected** | 42 files | Season schedules, totals, standings |
| **S3 Size** | 156 MB | `s3://nba-sim-raw-data-lake/basketball_reference/` |
| **Data Types** | 7 types | Schedules, box scores, totals, PBP, standings |
| **Estimated Records** | 2,200,000+ | Player box scores + aggregates |

### Data Types Captured

#### 1. Schedules (79 files expected)
- Game schedules per season
- Coverage: 1950-2025

#### 2. Player Box Scores (~1.9M records)
- Daily player statistics
- All 75 seasons

#### 3. Team Box Scores (~190K records)
- Daily team statistics
- All 75 seasons

#### 4. Season Totals (~35,500 records)
- Player season aggregates
- Per-season summaries

#### 5. Advanced Totals (~35,500 records)
- Advanced metrics (PER, TS%, etc.)
- Modern era statistical categories

#### 6. Play-by-Play (~30,750 games)
- Event-level data
- Coverage: 2000-2025 only

#### 7. Standings (79 files expected)
- Final season standings
- All 75 seasons

### Coverage Gaps

- **BAA Years (1947-1949):** Not supported by `basketball_reference_web_scraper` library
- **Play-by-Play:** Only 2000-2025 (not available pre-2000)
- **Advanced Stats:** Limited availability pre-1980

### Known Issues

- **Old Team Names:** Parser errors for 1950s teams (TRI-CITIES BLACKHAWKS, FORT WAYNE PISTONS)
- **Mid-Season Trades:** Fixed with `include_combined_values=True` parameter

### Scraper Information

- **Location:** `scripts/etl/scrape_basketball_reference_complete.py`
- **Language:** Python 3.x (`basketball_reference_web_scraper` library)
- **Rate Limit:** 5.0 seconds between requests
- **Runtime:** 42 files collected in overnight run
- **Overnight Wrapper:** `scripts/etl/overnight_basketball_reference_comprehensive.sh`

### Data Quality

- ✅ **Aggregation Level:** Game-level and season-level (60-70 pts quality score)
- ✅ **Historical Depth:** Best source for 1950-1995 data
- ✅ **Player IDs:** Basketball Reference IDs (requires mapping)
- ⚠️ **PBP Availability:** Modern era only (2000+)

---

## Source 5: Kaggle Database

**Official Name:** Kaggle NBA Database (2004-2020)
**Status:** ✅ COMPLETE (validation source)
**Coverage:** 2004-2020 (17 NBA seasons)
**Last Updated:** October 2, 2025 (one-time download)

### Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Seasons** | 17 seasons | 2004-2020 |
| **Games** | 26,496 | Regular season + playoffs |
| **Tables** | 17 tables | Pre-cleaned SQLite database |
| **Database Size** | 280 MB | Local file only (not in S3) |
| **Location** | Local | `/Users/ryanranft/nba-simulator-aws/data/kaggle/` |

### Database Schema (17 Tables)

1. **game** - Game metadata and scores
2. **team** - Team information
3. **player** - Player biographical data
4. **game_summary** - Game-level statistics
5. **line_score** - Quarter-by-quarter scoring
6. **officials** - Referee assignments
7. **other_stats** - Additional game statistics
8. **game_info** - Game context (attendance, duration)
9. **inactive_players** - Injury/inactive lists
10. **play_by_play** - Event-level data
11. **player_track** - Player tracking metrics
12. **team_details** - Team season details
13. **team_history** - Historical team data
14. **draft_combine_stats** - NBA Combine measurements
15. **draft_history** - Draft pick history
16. **common_player_info** - Extended player info
17. **team_info_common** - Extended team info

### Data Quality

- ✅ **Pre-cleaned:** High quality, minimal missing data
- ✅ **Consistent IDs:** NBA official IDs
- ✅ **Complete Coverage:** 2004-2020 with no major gaps
- ⚠️ **Static Dataset:** Not updated (ends at 2020 season)

### Use Cases

1. **Validation Benchmark:** Compare against ESPN/hoopR for 2004-2020
2. **Quality Baseline:** Pre-cleaned data for quality scoring
3. **Historical Reference:** Static snapshot for reproducibility
4. **Feature Engineering:** Pre-calculated advanced metrics

### Download Information

- **Source:** Kaggle.com (public dataset)
- **Download Script:** `scripts/etl/download_kaggle_basketball.py`
- **One-time Download:** No ongoing updates
- **RDS Integration:** Loaded to RDS via `scripts/db/load_kaggle_to_rds.py`

---

## Source 6: SportsDataverse

**Official Name:** SportsDataverse R Package
**Status:** ❌ DEPRECATED (redundant with hoopR)
**Coverage:** N/A
**Recommendation:** Use hoopR instead

### Deprecation Rationale

- **Redundancy:** SportsDataverse uses hoopR as backend for NBA data
- **Same Data:** Both sources pull from same NBA Stats API
- **Overhead:** Additional package dependency with no benefit
- **Maintenance:** hoopR is better maintained for NBA-specific use

### Migration Path

If you have existing SportsDataverse scripts:
1. Replace with hoopR Phase 1 endpoints
2. Use `scripts/etl/scrape_hoopr_phase1_foundation.R`
3. See migration guide in `docs/SCRAPER_MANAGEMENT.md`

**Archived Script:** `scripts/archive/deprecated/scrape_sportsdataverse.py`

---

## Data Quality Metrics

### Quality Score Formula

```
Quality Score = Base Score + Bonuses - Penalties

Base Score (Temporal Precision):
- 100: Millisecond timestamps (ESPN modern era)
- 90:  Second timestamps (ESPN transition era)
- 80:  Minute timestamps (hoopR)
- 70:  Quarter-level aggregation
- 60:  Game-level aggregation (Bball Ref, Kaggle)
- 50:  Season-level aggregation

Bonuses:
+ 5:  Complete player tracking data
+ 5:  Advanced metrics available
+ 5:  Official NBA IDs
+ 5:  No missing games in season
+ 5:  Validated against multiple sources

Penalties:
- 10: >5% missing games in season
- 10: >10% missing player IDs
- 10: Systematic data quality issues
- 10: No cross-source validation possible
```

### Quality Rankings by Source

| Source | Quality Score | Temporal Precision | Completeness | Use Case |
|--------|--------------|-------------------|--------------|----------|
| ESPN (modern) | 100 | Millisecond | 94.4% | Primary PBP source |
| ESPN (transition) | 90 | Second | 86.9% | Primary PBP source |
| NBA.com API | 90 | Second | TBD | Advanced metrics |
| hoopR | 80 | Minute | 100%* | Validation |
| Kaggle | 70 | Game-level | 100% | Benchmark |
| Basketball Ref | 60 | Game/Season | 100% | Historical fill |
| ESPN (early) | 50 | Sparse | 5.3% | Metadata only |

*For 2002+ coverage range only

---

## Cross-Source ID Mapping

### ID Types by Source

| Source | Game ID Format | Player ID Format | Team ID Format |
|--------|---------------|-----------------|---------------|
| ESPN | Numeric (9 digits) | Numeric (7 digits) | 3-letter abbrev |
| hoopR | NBA Stats format | NBA Stats ID | NBA Stats ID |
| NBA.com API | NBA Stats format | NBA Stats ID | NBA Stats ID |
| Basketball Ref | YYYYMMDD format | BBRef slug | 3-letter abbrev |
| Kaggle | Numeric | NBA Stats ID | NBA Stats ID |

### Mapping Strategy

**Primary Key:** ESPN Game ID (most comprehensive coverage)

**Mapping Tables:**
1. `game_id_mapping` - Cross-source game ID lookup
2. `player_id_mapping` - Cross-source player ID lookup
3. `team_id_mapping` - Cross-source team ID lookup

**Mapping Script:** `scripts/utils/create_id_mappings.py` (⏸️ TODO)

### Matching Rules

#### Game Matching
1. **Exact ID match:** If sources share ID format
2. **Date + teams match:** `game_date` + `home_team` + `away_team`
3. **Fuzzy date match:** ±1 day (for timezone issues)
4. **Manual resolution:** For ambiguous matches

#### Player Matching
1. **Exact ID match:** If sources share ID format
2. **Name + DOB match:** `player_name` + `date_of_birth`
3. **Name + debut season:** For players with common names
4. **Manual resolution:** For name variations (J. Smith vs John Smith)

#### Team Matching
1. **Abbreviation match:** BOS, LAL, etc.
2. **Handle relocations:** SEA → OKC, NJN → BKN, etc.
3. **Historical names:** TRI-CITIES → ATL lineage

---

## Coverage Comparison Matrix

### By Season Range

| Season Range | ESPN | hoopR | NBA API | BBRef | Kaggle | Best Source |
|-------------|------|-------|---------|-------|--------|-------------|
| 1947-1949 (BAA) | ❌ | ❌ | ❌ | ❌ | ❌ | **None** |
| 1950-1992 | Metadata | ❌ | ❌ | ✅ | ❌ | **BBRef** |
| 1993-2001 | Sparse PBP | ❌ | ❌ | ✅ | ❌ | **ESPN + BBRef** |
| 2002-2003 | ✅ Full PBP | ✅ | ❌ | ✅ | ❌ | **ESPN** |
| 2004-2020 | ✅ Full PBP | ✅ | ⏸️ | ✅ | ✅ | **ESPN + Kaggle** |
| 2021-2025 | ✅ Full PBP | ✅ | ⏸️ | ✅ | ❌ | **ESPN** |

### By Data Type

| Data Type | ESPN | hoopR | NBA API | BBRef | Kaggle |
|-----------|------|-------|---------|-------|--------|
| **Play-by-Play** | ✅ Best | ✅ Good | ⏸️ | Partial | ✅ |
| **Box Scores** | ✅ | ✅ | ⏸️ | ✅ | ✅ |
| **Advanced Stats** | Basic | ✅ Good | ⏸️ Best | ✅ | ✅ |
| **Player Tracking** | ❌ | ✅ | ⏸️ Best | ❌ | ✅ |
| **Shot Charts** | ❌ | ✅ | ⏸️ Best | ❌ | ❌ |
| **Historical (pre-1993)** | ❌ | ❌ | ❌ | ✅ Best | ❌ |

### Gap Analysis Summary

#### Coverage Gaps
1. **1947-1949 (BAA years):** No automated source (requires manual scraping)
2. **1950-1992 (early NBA):** Only aggregated stats, no PBP
3. **1993-2001 (early ESPN):** Sparse PBP (5.3% coverage)

#### Data Type Gaps
1. **Player Tracking:** NBA API paused, need to resume
2. **Shot Charts:** NBA API paused, need to resume
3. **Hustle Stats:** Not yet implemented

#### Quality Gaps
1. **Early Era PBP:** Only 594 games with PBP in 1993-2001
2. **hoopR RDS Load:** Parquet files ready, need to load to RDS for cross-validation
3. **NBA API:** Paused due to rate limiting

---

## Auto-Update Integration

### Automatic Catalog Updates

All scrapers automatically update this catalog upon completion using the `update_data_catalog()` function.

**Update Script:** `scripts/utils/update_data_catalog.py` (⏸️ TODO - Task #4)

### Update Triggers

1. **Scraper Completion:** Called at end of every scraper run
2. **Database Load:** Called after RDS load operations
3. **Manual Update:** Can be run standalone for verification
4. **Session Startup:** Displays freshness in session manager

### Update Procedure

```bash
# Automatic (called by scrapers)
python scripts/utils/update_data_catalog.py --source espn --action update

# Manual verification
python scripts/utils/update_data_catalog.py --verify

# Force full refresh
python scripts/utils/update_data_catalog.py --refresh-all
```

### Session Startup Integration

**Enhanced session manager output:**
```
▶ DATA FRESHNESS
  ESPN: ✅ Current (last updated: 2 hours ago)
  hoopR: 🔄 21% complete (48 hours remaining)
  NBA API: ⏸️ Paused (rate limiting)
  Basketball Ref: ✅ Complete
  Kaggle: ✅ Complete (static dataset)
```

**Implementation:** Workflow #1 update (⏸️ TODO - Task #11)

---

## Change Log

### Version 1.0 (October 9, 2025)

**Initial Release**
- Created master data catalog as single source of truth
- Documented all 6 data sources with complete statistics
- Added ESPN local database analysis (44,826 games, 14.1M events)
- Added hoopR progress tracking (21% complete)
- Added quality scoring formula and cross-source comparison matrix
- Added auto-update integration plan
- Established as authoritative reference for all documentation

**Data Corrections Applied:**
- ✅ ESPN coverage: "1999-2025" → **"1993-2025"** (actual range from analysis)
- ✅ ESPN games: "~32,000" → **44,826** (actual count)
- ✅ ESPN PBP events: "~6.8M" → **14,114,618** (actual count from RDS)
- ✅ hoopR progress: "In progress" → **21% complete** (5/24 seasons)

**Next Version (1.1) Planned Changes:**
- Add NBA API actual statistics when scraper resumes
- Add hoopR completion statistics when Phase 1 finishes
- Add cross-source ID mapping tables when implemented
- Add data validation results section

---

## Maintenance Notes

**Update Frequency:**
- **Daily:** ESPN stats (automatic scraper)
- **Real-time:** hoopR progress percentage (during active scraping)
- **Weekly:** Overall statistics refresh
- **Monthly:** Full catalog audit and validation

**Validation Checks:**
- Cross-source game counts should align within ±2% (timezone/cancellation differences)
- PBP event counts should increase monotonically (never decrease)
- File counts should match S3 inventory exactly
- RDS table row counts should match source statistics

**Automated Tests:**
- `tests/test_data_catalog_consistency.py` (⏸️ TODO)
- CI/CD validation on every commit
- Alert on >2% deviation from expected values

---

**End of Data Catalog**

**For detailed scraper documentation, see:**
- `docs/ESPN_SCRAPER_GUIDE.md` (ESPN API details)
- `docs/SCRAPER_MANAGEMENT.md` (hoopR + NBA API + Basketball Reference)
- `docs/DATA_SOURCES.md` (⚠️ DEPRECATED - Use this catalog instead)
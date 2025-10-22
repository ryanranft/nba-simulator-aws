# ETL Scrapers - Active Scraper Guide

**Last Updated:** October 21, 2025
**Status:** Production-ready
**Deprecated Files:** See `scripts/archive/deprecated/`

This directory contains all active ETL (Extract, Transform, Load) scrapers for the NBA Simulator project. This guide helps you identify which scraper to use for each data source and task.

---

## Quick Reference

| Data Source | Primary Scraper | Purpose | Status |
|------------|----------------|---------|--------|
| **Basketball Reference** | `basketball_reference_async_scraper.py` | Full async scraper for all stats | ✅ Active |
| **ESPN** | `espn_async_scraper.py` | Full async scraper for play-by-play | ✅ Active |
| **NBA API** | `nba_api_async_scraper.py` | Full async scraper for official stats | ✅ Active |
| **hoopR** | `hoopr_incremental_scraper.py` | NCAA/NBA college data | ✅ Active |
| **Kaggle** | `download_kaggle_basketball.py` | Historical datasets | ✅ Active |

---

## Basketball Reference Scrapers

### Primary Scrapers
- **`basketball_reference_async_scraper.py`** - Modern async scraper
  - **Use for:** Full data collection (2020-2025)
  - **Features:** Rate limiting, retry logic, S3 upload, telemetry
  - **Data types:** Draft, awards, per_game, shooting, play_by_play, team_ratings, playoffs, coaches, standings
  - **Expected runtime:** ~1.9 hours for 6 seasons × 9 data types
  - **Rate limit:** 12 seconds between requests

- **`basketball_reference_incremental_scraper.py`** - Delta updates
  - **Use for:** Daily/weekly incremental updates
  - **Features:** Only scrapes new/updated games since last run
  - **Expected runtime:** 5-10 minutes per day

- **`bbref_tier_1_agent.py`** - Autonomous agent
  - **Use for:** Complex multi-phase workflows
  - **Features:** State persistence, checkpoint recovery, parallel processing
  - **Expected runtime:** 2-4 hours for comprehensive collection

### Specialized Scrapers
- **`basketball_reference_box_score_scraper.py`** - Box score extraction
- **`basketball_reference_daily_box_scores.py`** - Daily box scores
- **`basketball_reference_daily_pbp.py`** - Daily play-by-play
- **`basketball_reference_pbp_backfill.py`** - Historical PBP gap filling
- **`basketball_reference_pbp_discovery.py`** - PBP availability detection

### Integration Scripts
- **`integrate_basketball_reference.py`** - Single source integration
- **`integrate_basketball_reference_aggregate.py`** - Multi-source aggregation

### Testing
- **`test_basketball_reference_api.py`** - API validation tests

### Deprecated
- ❌ 10 deprecated scrapers moved to `scripts/archive/deprecated/basketball_reference/`

---

## ESPN Scrapers

### Primary Scrapers
- **`espn_async_scraper.py`** - Modern async scraper
  - **Use for:** Full play-by-play data collection
  - **Features:** Rate limiting, retry logic, S3 upload
  - **Data types:** Play-by-play, box scores, game summaries
  - **Expected runtime:** 15-20 hours for 44,826 games

- **`espn_incremental_scraper.py`** - Delta updates
  - **Use for:** Daily game updates
  - **Expected runtime:** 10-30 minutes per day

### Specialized Scrapers
- **`espn_missing_pbp_scraper.py`** - Gap filling
  - **Use for:** Filling missing play-by-play data

### Utility Scripts
- **`analyze_espn_coverage.py`** - Coverage analysis
- **`validate_espn_pbp_files.py`** - Data validation
- **`load_espn_pbp_to_rds.py`** - Database loading
- **`load_validated_espn_pbp.py`** - Validated data loading

### Processing Scripts
- **`create_possession_panel_from_espn.py`** - Possession-level panel data

### Deprecated
- ❌ 6 deprecated scrapers moved to `scripts/archive/deprecated/espn/`

---

## NBA API Scrapers

### Primary Scrapers
- **`nba_api_async_scraper.py`** - Modern async scraper
  - **Use for:** Official NBA statistics
  - **Features:** Rate limiting, retry logic, S3 upload
  - **Data types:** Player stats, team stats, game logs, advanced metrics

- **`nba_api_incremental_scraper.py`** - Delta updates
  - **Use for:** Daily stat updates
  - **Expected runtime:** 5-15 minutes per day

### Specialized Endpoint Scrapers
- **`scrape_nba_api_game_advanced.py`** - Advanced game metrics
- **`scrape_nba_api_player_dashboards.py`** - Player dashboards
- **`scrape_nba_api_player_tracking.py`** - Player tracking data
- **`scrape_nba_api_team_dashboards.py`** - Team dashboards

### Agent Scripts
- **`phase_1_7_nba_stats_agent.py`** - Multi-phase autonomous agent

### Utility Scripts
- **`create_possession_panel_from_nba_api.py`** - Possession panel data
- **`verify_with_nba_stats.py`** - Cross-validation with official stats
- **`scrape_nba_lineups.py`** - Lineup data

### Deprecated
- ❌ 7 deprecated scrapers moved to `scripts/archive/deprecated/nba_api/`

---

## hoopR Scrapers

### Primary Scrapers
- **`hoopr_incremental_scraper.py`** - College basketball data
  - **Use for:** NCAA and college-to-NBA data
  - **Features:** 24 seasons of historical data
  - **Data types:** 248 CSV files covering college stats

### Agent Scripts
- **`phase_9_2_hoopr_agent.py`** - Autonomous hoopR collection

---

## Kaggle Scrapers

### Primary Scripts
- **`download_kaggle_basketball.py`** - Dataset download
- **`process_kaggle_historical.py`** - Data processing

---

## Shared Infrastructure

### Base Classes
- **`async_scraper_base.py`** (489 lines) - Modern async base class
  - **Adoption:** 8% of scrapers → **Goal: 50%**

### Configuration
- **`scraper_config.py`** (575 lines) - YAML-based configuration
  - **Adoption:** 12% of scrapers → **Goal: 80%**

### Monitoring
- **`scraper_telemetry.py`** (609 lines) - Prometheus metrics
  - **Adoption:** 10% of scrapers → **Goal: 100%**

### Error Handling
- **`scraper_error_handler.py`** - Centralized error handling

### Utilities
- **`modular_tools.py`** - Shared utility functions
- **`provenance_tracker.py`** - Data lineage tracking

---

## Naming Conventions

### Active Scrapers (USE THESE)
- **Primary:** `{source}_async_scraper.py`
- **Incremental:** `{source}_incremental_scraper.py`
- **Agents:** `{phase}_{task}_agent.py`
- **Specialized:** `{source}_{task}_scraper.py`

### Deprecated Patterns (DO NOT USE)
- ❌ `scrape_{source}.py`
- ❌ `scrape_{source}_fixed.py`
- ❌ `scrape_{source}_additional.py`
- ❌ `scrape_{source}_comprehensive.py`
- ❌ `{source}_v2.py` or `{source}_optimized.py`

---

## Usage Examples

### Basketball Reference (Full Collection)
```bash
python scripts/etl/basketball_reference_async_scraper.py \
  --start-year 2020 \
  --end-year 2025 \
  --data-types all \
  --upload-s3
```

### ESPN (Incremental Updates)
```bash
python scripts/etl/espn_incremental_scraper.py \
  --date-range 2025-10-20,2025-10-21 \
  --upload-s3
```

### NBA API (Specific Endpoints)
```bash
python scripts/etl/scrape_nba_api_player_dashboards.py \
  --season 2024-25 \
  --upload-s3
```

---

## Summary Statistics

**Total ETL Scripts:** 84 active files (down from 107, 21% reduction)
**Archived:** 23 deprecated scrapers

**By Data Source:**
- Basketball Reference: 8 active + 10 archived
- ESPN: 6 active + 6 archived
- NBA API: 9 active + 7 archived
- hoopR: 2 active
- Kaggle: 2 active
- Shared Infrastructure: 7 active

---

## Related Documentation

- **Scraper Management:** `docs/data_collection/scrapers/MANAGEMENT.md`
- **Async Infrastructure:** `README_ASYNC_INFRASTRUCTURE.md`
- **Deployment Checklist:** `docs/data_collection/scrapers/ASYNC_DEPLOYMENT_CHECKLIST.md`
- **Monitoring System:** `docs/data_collection/scrapers/MONITORING_SYSTEM.md`

---

**Last Updated:** October 21, 2025
**Maintained By:** NBA Simulator AWS Team

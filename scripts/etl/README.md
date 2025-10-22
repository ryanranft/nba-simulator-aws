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

- **`basketball_reference_incremental_scraper.py`** - Delta updates ✅ **Migrated to AsyncBaseScraper**
  - **Pattern:** Incremental Scraper (wraps synchronous library client)
  - **Migration Date:** October 22, 2025
  - **Use for:** Daily/weekly incremental updates (current season aggregate stats)
  - **Features:** Rate limiting (12s), retry logic, S3 upload, telemetry
  - **Data types:** Season totals, advanced totals
  - **Expected runtime:** ~1 minute during season, <10 seconds off-season

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

- **`espn_incremental_scraper.py`** - Delta updates ✅ **Migrated to AsyncBaseScraper**
  - **Pattern:** Incremental Scraper with database integration
  - **Migration Date:** October 22, 2025
  - **Use for:** Daily game updates (last 14 days)
  - **Features:** Async HTTP, retry logic (new!), rate limiting (0.5s), S3 backup (new!), SQLite database
  - **Expected runtime:** ~5 minutes during season, <1 minute off-season

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

## Naming Conventions & Policy

**Policy Effective:** October 21, 2025
**Purpose:** Ensure consistent, discoverable scraper naming across all data sources

### Active Naming Patterns (REQUIRED)

#### 1. Primary Async Scrapers
**Pattern:** `{source}_async_scraper.py`
**Use for:** Full async data collection from a data source
**Examples:**
- `basketball_reference_async_scraper.py`
- `espn_async_scraper.py`
- `nba_api_async_scraper.py`

**Requirements:**
- Must inherit from `AsyncBaseScraper` (or implement equivalent async pattern)
- Must include rate limiting via `scraper_config.py`
- Must upload to S3 by default
- Must include telemetry via `scraper_telemetry.py`

#### 2. Incremental Scrapers
**Pattern:** `{source}_incremental_scraper.py`
**Use for:** Delta updates since last run (daily/weekly updates)
**Examples:**
- `basketball_reference_incremental_scraper.py`
- `espn_incremental_scraper.py`

**Requirements:**
- Must track last run timestamp
- Must only scrape new/updated data
- Must be compatible with primary scraper's output format

#### 3. Autonomous Agents
**Pattern:** `{phase}_{task}_agent.py`
**Use for:** Multi-phase autonomous workflows with state persistence
**Examples:**
- `bbref_tier_1_agent.py`
- `phase_1_7_nba_stats_agent.py`
- `phase_9_2_hoopr_agent.py`

**Requirements:**
- Must implement checkpoint/recovery logic
- Must track state between sessions
- Must support parallel processing where applicable

#### 4. Specialized Scrapers
**Pattern:** `{source}_{specific_task}_scraper.py`
**Use for:** Endpoint-specific or task-specific scrapers
**Examples:**
- `basketball_reference_box_score_scraper.py`
- `espn_missing_pbp_scraper.py`
- `scrape_nba_api_player_dashboards.py`

**Requirements:**
- Task name must be specific and descriptive
- Must not duplicate functionality of primary scraper

---

### Deprecated Patterns (DO NOT USE)

| Pattern | Problem | Use Instead |
|---------|---------|-------------|
| `scrape_{source}.py` | Generic, unclear purpose | `{source}_async_scraper.py` |
| `scrape_{source}_fixed.py` | Suggests bug fix, not version | Use git history for fixes |
| `scrape_{source}_additional.py` | Unclear what's "additional" | `{source}_incremental_scraper.py` |
| `scrape_{source}_comprehensive.py` | Redundant with primary | `{source}_async_scraper.py` |
| `{source}_v2.py` | Version numbers in filename | Use git tags/branches |
| `{source}_optimized.py` | "Optimized" is subjective | Optimize existing scraper |

---

### Policy Rules

#### Creating New Scrapers

**✅ Create a new scraper when:**
1. Adding a new data source not yet covered
2. Adding specialized endpoint not covered by primary scraper
3. Implementing incremental updates for existing source
4. Building multi-phase autonomous agent

**❌ Do NOT create a new scraper when:**
1. Fixing bugs in existing scraper → Fix the existing file
2. Optimizing existing scraper → Refactor existing file
3. Adding features to existing scraper → Extend existing file
4. Temporary testing → Use notebooks or test files

#### Modifying Existing Scrapers

**Before modifying an active scraper:**
1. Check if it's used in production (grep for imports)
2. Review git history for context
3. Add tests if not present
4. Update documentation in this README

**When to deprecate a scraper:**
1. New scraper fully replaces functionality
2. Data source no longer available
3. Scraper abandoned for >6 months

#### Deprecation Process

1. Move to `scripts/archive/deprecated/{source}/`
2. Update this README's "Deprecated" section
3. Create git commit documenting deprecation reason
4. Verify no broken imports (`grep -r "from scripts.etl.{filename}"`)

---

### Examples

#### Good Naming ✅

```bash
# Primary scrapers - clear purpose
basketball_reference_async_scraper.py
espn_async_scraper.py

# Incremental updates - clear differentiation
basketball_reference_incremental_scraper.py

# Specialized tasks - specific and descriptive
basketball_reference_box_score_scraper.py
espn_missing_pbp_scraper.py
```

#### Bad Naming ❌

```bash
# Too generic
scrape_bball_ref.py
get_espn_data.py

# Version numbers
basketball_reference_v2.py
espn_scraper_new.py

# Subjective adjectives
basketball_reference_better.py
espn_fast_scraper.py

# Bug fix indicators
basketball_reference_fixed.py
espn_working.py
```

---

### Enforcement

**Code Reviews:** All new scrapers must follow naming conventions
**Automated Checks:** DIMS verification checks for deprecated patterns
**Grandfathering:** Existing specialized scrapers (pre-Oct 2025) are allowed until refactored

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

## Testing Standards & Coverage

**Policy Effective:** October 21, 2025
**Goal:** Ensure all active scrapers have basic test coverage

### Current Test Coverage

**Shared Infrastructure (Good Coverage):**
- ✅ `async_scraper_base.py` - Tested in `tests/test_async_scrapers.py`
- ✅ `scraper_config.py` - Tested in `tests/test_new_scraper_components.py`
- ✅ `scraper_telemetry.py` - Tested in `tests/test_new_scraper_components.py`
- ✅ `scraper_error_handler.py` - Tested in `tests/test_new_scraper_components.py`

**Individual Scrapers (Minimal Coverage):**
- ⚠️ Basketball Reference: `test_basketball_reference_api.py` (API validation only)
- ⚠️ ESPN: `test_espn_processor.py` (processor only, not full scraper)
- ❌ NBA API: No dedicated tests
- ❌ hoopR: No dedicated tests
- ❌ Kaggle: No dedicated tests

**Current Stats:**
- Shared infrastructure coverage: ~80%
- Individual scraper coverage: ~20%
- Integration tests: 5 test files
- Total test files: 8

### Testing Standards for New Scrapers

**Minimum Requirements:**

All new scrapers must include:

1. **Basic Functionality Test**
   ```python
   def test_scraper_initialization():
       """Test scraper can be initialized with config."""
       scraper = YourAsyncScraper(config)
       assert scraper is not None
   ```

2. **Rate Limiting Test**
   ```python
   def test_rate_limiting():
       """Test rate limiter respects configured limits."""
       # Verify requests_per_second honored
   ```

3. **Retry Logic Test**
   ```python
   def test_retry_on_failure():
       """Test scraper retries on transient failures."""
       # Mock 503 error, verify retry attempt
   ```

4. **Data Validation Test**
   ```python
   def test_output_schema():
       """Test scraped data matches expected schema."""
       # Verify required fields present
   ```

5. **S3 Upload Test** (mocked)
   ```python
   @mock_s3
   def test_s3_upload():
       """Test data successfully uploads to S3."""
       # Mock S3, verify upload called
   ```

### Testing Recommendations

**For Existing Scrapers:**
- Prioritize testing primary async scrapers first
- Focus on integration tests (does it actually work?)
- Mock external HTTP calls to avoid rate limits
- Use pytest fixtures for common test data

**Test File Locations:**
- Shared infrastructure tests: `tests/test_*.py`
- Scraper-specific tests: `tests/scrapers/test_{source}_scraper.py`
- Integration tests: `tests/integration/`

**Running Tests:**
```bash
# All tests
pytest tests/ -v

# Specific scraper
pytest tests/scrapers/test_basketball_reference_scraper.py -v

# With coverage
pytest tests/ --cov=scripts/etl --cov-report=html
```

### Future Improvements

**Short-term (Next Month):**
- [ ] Add basic tests for primary async scrapers (ESPN, Basketball Reference, NBA API)
- [ ] Create test fixtures for common mock data
- [ ] Set up CI/CD to run tests automatically

**Medium-term (Next Quarter):**
- [ ] Achieve 50% coverage for individual scrapers
- [ ] Add integration tests for full scraper workflows
- [ ] Create automated test data generation

**Long-term (Next Year):**
- [ ] Achieve 80% coverage for all active scrapers
- [ ] Performance regression testing
- [ ] Contract testing for external APIs

---

## Related Documentation

- **Scraper Management:** `docs/data_collection/scrapers/MANAGEMENT.md`
- **Async Infrastructure:** `README_ASYNC_INFRASTRUCTURE.md`
- **Deployment Checklist:** `docs/data_collection/scrapers/ASYNC_DEPLOYMENT_CHECKLIST.md`
- **Monitoring System:** `docs/data_collection/scrapers/MONITORING_SYSTEM.md`
- **Testing Guide:** See above testing standards

---

**Last Updated:** October 21, 2025
**Maintained By:** NBA Simulator AWS Team

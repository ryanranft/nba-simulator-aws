# Scraper Framework Migration Plan

**Created:** October 22, 2025
**Status:** Phase 1 Complete (Planning & Templates)
**Estimated Completion:** 2-10 additional sessions (1-2 weeks)

This document tracks the systematic migration of 84 active NBA data scrapers to modern shared infrastructure (AsyncBaseScraper + scraper_config.py).

---

## Executive Summary

**Goal:** Migrate 50%+ scrapers to shared infrastructure, reduce code duplication by 3,000-5,000 lines

**Current State:**
- 84 active scraper files
- 39,290 total lines of code
- 3 already using AsyncBaseScraper (8%)
- 10 using scraper_config.py (12%)
- Shared infrastructure: 1,664 lines (async_scraper_base.py: 490 lines, scraper_config.py: 576 lines, scraper_telemetry.py: 609 lines)

**Target State:**
- 50%+ using AsyncBaseScraper (42+ scrapers)
- 80%+ using scraper_config.py (67+ scrapers)
- Estimated reduction: 3,000-5,000 lines of duplicate code
- Standardized error handling, rate limiting, telemetry

---

## Migration Categories

### Already Migrated (3 files) ✅
1. `basketball_reference_async_scraper.py`
2. `espn_async_scraper.py`
3. `nba_api_async_scraper.py`

**Status:** Production-ready, serving as migration templates

### High Priority - Primary Scrapers (6 files)
**Impact:** High - These are core production scrapers
**Effort:** 2-3 hours each
**Session:** 2-3

1. `basketball_reference_incremental_scraper.py` (incremental updates)
2. `espn_incremental_scraper.py` (daily updates)
3. `espn_missing_pbp_scraper.py` (gap filling)
4. `hoopr_incremental_scraper.py` (NCAA data)
5. `nba_api_async_scraper.py` (already async, needs config adoption)
6. `basketball_reference_box_score_scraper.py` (box scores)

### Medium Priority - Specialized Scrapers (12 files)
**Impact:** Medium - Used for specific tasks
**Effort:** 1-2 hours each
**Session:** 4-6

**Basketball Reference:**
7. `basketball_reference_daily_box_scores.py`
8. `basketball_reference_daily_pbp.py`
9. `basketball_reference_pbp_backfill.py`
10. `basketball_reference_pbp_discovery.py`

**NBA API:**
11. `scrape_nba_api_game_advanced.py`
12. `scrape_nba_api_player_dashboards.py`
13. `scrape_nba_api_player_tracking.py`
14. `scrape_nba_api_team_dashboards.py`

**hoopR:**
15. `hoopr_incremental_simple.py`
16. `scrape_hoopr_complete_all_endpoints.py`
17. `scrape_hoopr_nba_stats.py`
18. `scrape_missing_hoopr_games.py`

### Lower Priority - Autonomous Agents (7 files)
**Impact:** Low - Complex multi-phase agents, may need custom approach
**Effort:** 3-4 hours each
**Session:** 7-9

19. `bbref_tier_1_agent.py`
20. `master_data_collection_agent.py`
21. `phase_1_0_quality_agent.py`
22. `phase_1_11_deduplication_agent.py`
23. `phase_1_1_integration_agent.py`
24. `phase_1_7_nba_stats_agent.py`
25. `phase_1c_historical_agent.py`
26. `phase_9_2_hoopr_agent.py`

### Utility Scripts - Config Adoption Only (19 files)
**Impact:** Low - Utility scripts, only need config adoption
**Effort:** 30 minutes each
**Session:** 10

**Analysis:**
27. `analyze_data_coverage.py`
28. `analyze_espn_coverage.py`

**Data Processing:**
29. `build_master_game_list.py`
30. `build_master_game_list_robust.py`
31. `create_possession_panel_from_espn.py`
32. `create_possession_panel_from_kaggle.py`
33. `create_possession_panel_from_nba_api.py`
34. `create_possession_panel_from_pbpstats.py`
35. `create_possession_panel_with_hoopr_lineups.py`
36. `create_possession_panel_with_lineups.py`

**Extraction:**
37. `extract_boxscores_local.py`
38. `extract_kaggle_to_temporal.py`
39. `extract_pbp_local.py`
40. `extract_schedule_local.py`
41. `extract_teams_by_year.py`

**Loading:**
42. `load_espn_pbp_to_rds.py`
43. `load_local_json_to_rds.py`
44. `load_validated_espn_pbp.py`

**Integration:**
45. `integrate_basketball_reference.py`
46. `integrate_basketball_reference_aggregate.py`
47. `merge_all_sources.py`

**Validation:**
48. `validate_espn_pbp_files.py`
49. `validate_lineup_tracking.py`
50. `verify_with_nba_stats.py`

### No Migration Needed - Infrastructure (7 files)
**Status:** These ARE the shared infrastructure

51. `async_scraper_base.py` ✅
52. `scraper_config.py` ✅
53. `scraper_telemetry.py` ✅
54. `scraper_error_handler.py` ✅
55. `data_validators.py` ✅
56. `deduplication_manager.py` ✅
57. `modular_tools.py` ✅

### Other - Special Cases (27 files)
**Status:** Needs case-by-case evaluation

**Kaggle:**
58. `download_kaggle_basketball.py`
59. `process_kaggle_historical.py`

**Simple Incrementals (ESPN):**
60. `espn_incremental_simple.py`

**NBA API Incrementals:**
61. `nba_api_incremental_simple.py`

**Basketball Reference:**
62. `scrape_bref_tier1_incremental.py`

**Specialized:**
63. `scrape_failed_games_by_id.py`
64. `scrape_kaggle_database_expansion.py`
65. `scrape_missing_games.py`
66. `scrape_nba_lineups.py`

**Infrastructure (Specialized):**
67. `adaptive_rate_limiter.py`
68. `complete_schema_update.py`
69. `create_glue_etl_job.py`
70. `create_player_id_mapping.py`
71. `fill_historical_gaps.py`
72. `game_id_decoder.py`
73. `glue_etl_extract_schedule.py`
74. `identify_missing_games.py`
75. `intelligent_extraction.py`
76. `partition_by_year.py`
77. `provenance_tracker.py`
78. `smart_retry_strategies.py`
79. `structured_output_framework.py`

**Build/Deploy:**
80. `build_unified_database.py`

---

## Migration Patterns

### Pattern 1: Primary Async Scraper
**When:** Scraper already does full async data collection
**Difficulty:** Medium
**Example:** `espn_async_scraper.py` (already migrated)

**Steps:**
1. Inherit from `AsyncBaseScraper`
2. Move configuration to `scraper_config.py`
3. Replace custom rate limiting with `rate_limiter.acquire()`
4. Replace custom retry logic with `fetch_url()` method
5. Replace custom S3 upload with `store_data()` method
6. Implement `scrape()` abstract method
7. Add telemetry integration

**Estimated Lines Saved:** 100-200 per scraper

### Pattern 2: Incremental Scraper
**When:** Scraper does delta updates since last run
**Difficulty:** Medium
**Example:** `basketball_reference_incremental_scraper.py`

**Steps:**
1. Inherit from `AsyncBaseScraper`
2. Add last_run timestamp tracking
3. Use `custom_settings` in config for incremental state
4. Leverage shared `fetch_url()` with custom params
5. Implement `scrape()` with delta logic

**Estimated Lines Saved:** 80-150 per scraper

### Pattern 3: Specialized Task Scraper
**When:** Scraper targets specific endpoint/task
**Difficulty:** Easy-Medium
**Example:** `basketball_reference_box_score_scraper.py`

**Steps:**
1. Inherit from `AsyncBaseScraper`
2. Configure single endpoint in `custom_settings`
3. Implement focused `scrape()` method
4. Leverage all shared infrastructure

**Estimated Lines Saved:** 60-100 per scraper

### Pattern 4: Autonomous Agent
**When:** Multi-phase workflows with state persistence
**Difficulty:** Hard
**Example:** `bbref_tier_1_agent.py`

**Steps:**
1. Consider extending `AsyncBaseScraper` as base
2. Add custom state management on top
3. Use shared infrastructure for HTTP/storage
4. Keep custom orchestration logic

**Estimated Lines Saved:** 50-100 per agent (less due to custom logic)

### Pattern 5: Utility Script (Config Only)
**When:** Script doesn't do async HTTP scraping
**Difficulty:** Easy
**Example:** Analysis, extraction, loading scripts

**Steps:**
1. Adopt `scraper_config.py` for configuration management only
2. No need to inherit from `AsyncBaseScraper`
3. Use shared error handling and telemetry

**Estimated Lines Saved:** 20-40 per script

---

## Migration Workflow (Per Scraper)

### Step 1: Analyze (15 min)
- Read current scraper
- Identify pattern (async, incremental, specialized, agent, utility)
- Note custom logic that must be preserved
- Estimate effort and lines saved

### Step 2: Create Config (10 min)
- Add scraper entry to `config/scraper_config.yaml`
- Set appropriate rate limits
- Configure retry behavior
- Set S3 bucket and output directories

### Step 3: Migrate Code (30-90 min)
- Create new file or refactor in place
- Inherit from `AsyncBaseScraper`
- Replace HTTP logic with `fetch_url()` / `fetch_urls()`
- Replace storage logic with `store_data()`
- Move rate limiting to config
- Preserve custom business logic

### Step 4: Test (15-30 min)
- Run scraper with `dry_run=True`
- Verify rate limiting works
- Verify retry logic works
- Verify S3 upload works (if enabled)
- Check telemetry output

### Step 5: Document (10 min)
- Update scraper docstring
- Update this migration plan
- Update scripts/etl/README.md if needed

### Step 6: Commit (5 min)
- Git commit with migration details
- Reference this plan in commit message

**Total per scraper:** 1.5-2.5 hours

---

## Session Plan (10 Sessions)

### Session 1 (TODAY) ✅
**Duration:** 2-3 hours
**Goal:** Planning, templates, proof of concept

- [x] Create migration plan document
- [ ] Create scraper templates
- [ ] Migrate 1 proof-of-concept scraper
- [ ] Document process

**Files:** 1 migrated (proof of concept)
**Progress:** 1/84 scrapers (1%)

### Session 2-3 (Days 2-3)
**Duration:** 2-3 hours each
**Goal:** High priority primary scrapers

- [ ] `basketball_reference_incremental_scraper.py`
- [ ] `espn_incremental_scraper.py`
- [ ] `espn_missing_pbp_scraper.py`
- [ ] `hoopr_incremental_scraper.py`
- [ ] `basketball_reference_box_score_scraper.py`

**Files:** 5 migrated
**Progress:** 6/84 scrapers (7%)

### Session 4-6 (Days 4-6)
**Duration:** 2-3 hours each
**Goal:** Medium priority specialized scrapers

- [ ] Basketball Reference specialized (4 files)
- [ ] NBA API specialized (4 files)
- [ ] hoopR specialized (4 files)

**Files:** 12 migrated
**Progress:** 18/84 scrapers (21%)

### Session 7-9 (Days 7-9)
**Duration:** 3-4 hours each
**Goal:** Autonomous agents

- [ ] `bbref_tier_1_agent.py`
- [ ] `master_data_collection_agent.py`
- [ ] Phase agents (6 files)

**Files:** 7 migrated
**Progress:** 25/84 scrapers (30%)

### Session 10 (Day 10)
**Duration:** 2-3 hours
**Goal:** Utility scripts config adoption

- [ ] Batch migrate 19 utility scripts (config only)
- [ ] Update documentation
- [ ] Create final summary

**Files:** 19 migrated
**Progress:** 44/84 scrapers (52%) ✅ TARGET REACHED

**Remaining:** 40 files (special cases, evaluated separately)

---

## Success Metrics

### Code Quality
- [ ] 50%+ scrapers using AsyncBaseScraper (42+ files)
- [ ] 80%+ scrapers using scraper_config.py (67+ files)
- [ ] 3,000-5,000 lines of duplicate code removed
- [ ] 100% of migrated scrapers have tests

### Performance
- [ ] Rate limiting consistent across all scrapers
- [ ] Retry logic standardized
- [ ] S3 upload consistent
- [ ] Telemetry enabled for all scrapers

### Documentation
- [ ] Migration plan complete and updated
- [ ] All migrated scrapers documented
- [ ] Templates created and available
- [ ] Future migration guide written

---

## Risk Assessment

### Low Risk
- Primary async scrapers (already proven pattern)
- Specialized scrapers (straightforward migration)
- Utility scripts (config adoption only)

### Medium Risk
- Incremental scrapers (must preserve state tracking)
- Autonomous agents (complex state management)

### High Risk
- Legacy scrapers with unusual patterns
- Scrapers with tight coupling to old infrastructure

**Mitigation:**
- Test thoroughly with `dry_run=True`
- Keep old scraper files until verified
- Incremental deployment (don't migrate everything at once)
- Rollback plan: Keep deprecated scrapers in archive

---

## Dependencies

### Required Before Migration
- [x] AsyncBaseScraper implemented and tested
- [x] scraper_config.py implemented and tested
- [x] scraper_telemetry.py implemented and tested
- [x] 3 proof-of-concept scrapers working in production

### Required During Migration
- [ ] Test environment with S3 access
- [ ] Monitoring dashboard for telemetry
- [ ] Backup of all scrapers before migration

### Required After Migration
- [ ] Updated documentation
- [ ] Team training on new infrastructure
- [ ] Deprecation of old patterns

---

## Progress Tracking

**Last Updated:** October 22, 2025

| Category | Total | Migrated | Remaining | % Complete |
|----------|-------|----------|-----------|------------|
| **Already Migrated** | 3 | 3 | 0 | 100% |
| **High Priority** | 6 | 0 | 6 | 0% |
| **Medium Priority** | 12 | 0 | 12 | 0% |
| **Low Priority (Agents)** | 7 | 0 | 7 | 0% |
| **Utility (Config Only)** | 19 | 0 | 19 | 0% |
| **Infrastructure** | 7 | 7 | 0 | 100% |
| **Special Cases** | 27 | 0 | 27 | 0% |
| **Other** | 3 | 0 | 3 | 0% |
| **TOTAL** | 84 | 10 | 74 | 12% |

**Target:** 52% (44 files)
**Projected Completion:** Session 10 (10 sessions over 1-2 weeks)

---

## Completed Migrations

### Session 1 (October 22, 2025) ✅
**Status:** Complete
**Duration:** 2 hours

1. Migration plan created (672 lines) ✅
2. Templates created (662 lines) ✅
3. Migration process guide created (682 lines) ✅

### Session 2 (October 22, 2025) ✅
**Status:** Complete
**Duration:** 1.5 hours

1. **basketball_reference_incremental_scraper.py** - ✅ Migrated
   - **Pattern:** Incremental Scraper (wraps synchronous library client)
   - **Lines before:** 405
   - **Lines after:** 400
   - **Infrastructure removed:** ~70 lines (rate limiting, retry, S3 upload, manual error handling)
   - **Integration added:** ~65 lines (async wrappers, AsyncBaseScraper integration)
   - **Net reduction:** 5 lines (but vastly improved maintainability)
   - **Time taken:** 1.5 hours
   - **Benefits:**
     - Standardized rate limiting (12s between requests, configurable)
     - Retry logic with exponential backoff (via base class)
     - S3 upload integration (via store_data() method)
     - Telemetry integration (Prometheus metrics)
     - Configuration via scraper_config.yaml
   - **Testing:**
     - ✅ Dry run successful
     - ✅ Rate limiting verified
     - ✅ S3 upload configured
     - ✅ AsyncBaseScraper integration working
     - ✅ Telemetry enabled
   - **Documentation:**
     - ✅ Scraper docstring updated
     - ✅ scripts/etl/README.md updated
     - ✅ Migration plan updated

---

## Notes

- Migration is incremental and reversible
- Old scrapers archived, not deleted
- Each migration is a separate commit
- Testing is mandatory before marking complete
- Documentation updates with each migration

---

**Maintained By:** NBA Simulator AWS Team
**Next Review:** After Session 2 (verify approach working)

# Multi-Source Implementation Checklist

**Created:** October 6, 2025
**Purpose:** Track progress implementing 209-feature ML dataset
**Total time:** 28 hours over 4 weeks

---

## 📋 Week 1: Critical Advanced Features (12 hours)

### Sub-Phase 1.10: Basketball Reference Scraper (8 hours)

**Prerequisites:**
- [ ] Review TOS compliance requirements (1 req/3 sec, bot User-Agent)
- [ ] Create database table `player_advanced_stats`
- [ ] Set up error logging

**Implementation:**
- [ ] Create `scripts/etl/scrape_basketball_reference.py`
  - [ ] Implement base scraper class
  - [ ] Add rate limiting (3-second delay)
  - [ ] Implement URL constructor (YYYYMMDD0TEAM format)
  - [ ] Parse HTML tables (BeautifulSoup/pandas)
  - [ ] Extract basic box score table
  - [ ] Extract advanced stats table
  - [ ] Extract four factors table
  - [ ] Extract shooting table (NEW - shot location data)
  - [ ] Extract hustle stats table (NEW)
  - [ ] Add error handling and retry logic

**Testing:**
- [ ] Test on 1 game (validate HTML parsing)
- [ ] Test on 1 week (validate rate limiting)
- [ ] Test on 1 month (validate error handling)
- [ ] Verify TOS compliance (check delay between requests)

**Storage:**
- [ ] Upload to S3: `s3://nba-sim-raw-data-lake/bref/`
- [ ] Insert into `player_advanced_stats` table
- [ ] Verify 47 features per game

**Validation:**
- [ ] Compare sample with Basketball Reference website
- [ ] Check for NULL rates (should be <10%)
- [ ] Verify advanced metrics calculations (TS%, eFG%, PER)

**Completion criteria:**
- [ ] 47 features extracted per game
- [ ] TOS compliant (1 req/3 sec verified)
- [ ] Error rate <5%
- [ ] Sample validation passed

---

### Sub-Phase 1.7: NBA.com Stats ALL Endpoints (4 hours)

**Prerequisites:**
- [ ] Review existing `verify_with_nba_stats.py` script
- [ ] Create database table `player_tracking_stats`
- [ ] Create database table `shot_chart`

**Implementation:**
- [ ] Expand `scripts/etl/scrape_nba_stats_api.py`
  - [ ] Add `boxscoreadvancedv2` endpoint
  - [ ] Add `boxscoreplayertrackv2` endpoint
  - [ ] Add `hustlestatsboxscore` endpoint
  - [ ] Add `shotchartdetail` endpoint
  - [ ] Add `boxscorematchupsv3` endpoint
  - [ ] Add `boxscoreusagev2` endpoint
  - [ ] Add `boxscorefourfactorsv2` endpoint
  - [ ] Add `boxscoremiscv2` endpoint
  - [ ] Add `boxscorescoringv2` endpoint
  - [ ] Implement rate limiting (600ms delay)
  - [ ] Add exponential backoff on failures

**Testing:**
- [ ] Test each endpoint individually (1 game)
- [ ] Test all endpoints together (10 games)
- [ ] Verify rate limits (no timeouts)
- [ ] Check response formats

**Storage:**
- [ ] Upload to S3: `s3://nba-sim-raw-data-lake/nba_stats/`
- [ ] Insert into `player_tracking_stats` table
- [ ] Insert into `shot_chart` table
- [ ] Verify 92 features per game

**Validation:**
- [ ] Compare tracking data with NBA.com website
- [ ] Verify shot chart coordinates
- [ ] Check hustle stats accuracy

**Completion criteria:**
- [ ] 92 tracking/hustle features extracted per game
- [ ] All 11 endpoints working
- [ ] Error rate <5%
- [ ] Sample validation passed

---

## 📋 Week 2: Historical & Storage (8 hours)

### Sub-Phase 1.8: Kaggle Database Integration (4 hours)

**Prerequisites:**
- [ ] Kaggle account created
- [ ] Kaggle API credentials configured (~/.kaggle/kaggle.json)
- [ ] Install kaggle CLI: `pip install kaggle`

**Implementation:**
- [ ] Create `scripts/etl/download_kaggle_database.py`
  - [ ] Download basketball.sqlite database
  - [ ] Verify database integrity (check file size 2-5GB)

- [ ] Create `scripts/etl/extract_kaggle_games.py`
  - [ ] Connect to SQLite database
  - [ ] Query pre-1999 games (1946-1998)
  - [ ] Convert to canonical format
  - [ ] Add `era_indicator` field (early/golden/modern)

**Testing:**
- [ ] Verify database download complete
- [ ] Test extraction on 1 season (e.g., 1987)
- [ ] Validate field mapping

**Storage:**
- [ ] Upload to S3: `s3://nba-sim-raw-data-lake/kaggle/`
- [ ] Insert into `games` table with `data_source='kaggle'`
- [ ] Verify 12 historical features per game

**Validation:**
- [ ] Check historical game count (~50,000+ games)
- [ ] Verify date range (1946-1998)
- [ ] Compare sample with historical records

**Completion criteria:**
- [ ] 50,000+ historical games extracted
- [ ] 12 features per historical game
- [ ] Coverage: 1946-1998
- [ ] Sample validation passed

---

### Sub-Phase 1.11: Multi-Source Storage (4 hours)

**Prerequisites:**
- [ ] All sources scraped (ESPN, BRef, NBA.com, Kaggle)
- [ ] Database migration scripts ready

**Implementation:**
- [ ] Create `games_multi_source` table
  ```sql
  CREATE TABLE games_multi_source (
      composite_key VARCHAR(100) PRIMARY KEY,
      game_date DATE,
      home_team_abbr VARCHAR(3),
      away_team_abbr VARCHAR(3),
      espn_data JSONB,
      nba_data JSONB,
      bref_data JSONB,
      kaggle_data JSONB,
      final_home_score INTEGER,
      final_away_score INTEGER,
      confidence_score DECIMAL(3,2),
      sources_count INTEGER
  );
  ```

- [ ] Create `scripts/etl/store_multi_source.py`
  - [ ] Group games by composite key (date + teams)
  - [ ] Store all source data (don't merge)
  - [ ] Calculate "best estimate" fields
  - [ ] Calculate confidence scores
  - [ ] Track source count per game

**Testing:**
- [ ] Test on 100 games with multiple sources
- [ ] Verify all source data preserved
- [ ] Check confidence score calculation

**Storage:**
- [ ] Populate `games_multi_source` table
- [ ] Verify JSONB fields contain all source data

**Validation:**
- [ ] Check games with 4+ sources (should be majority)
- [ ] Verify no data loss during storage
- [ ] Validate confidence scores (avg ≥0.80)

**Completion criteria:**
- [ ] All games stored with all source data
- [ ] Confidence scores calculated
- [ ] No data loss verified
- [ ] Multi-source table populated

---

## 📋 Week 3: Feature Engineering (6 hours)

### Sub-Phase 1.13: ML Feature Engineering (4 hours)

**Prerequisites:**
- [ ] All sources in database
- [ ] `games_multi_source` table populated

**Implementation:**
- [ ] Create `scripts/ml/engineer_features.py`
  - [ ] Implement `combine_sources()` function
  - [ ] Implement `calculate_derived_features()` function
  - [ ] Add efficiency metrics (pts_per_touch, etc.)
  - [ ] Add contextual features (days_rest, back_to_back)
  - [ ] Add momentum features (last_5_wins, streak)
  - [ ] Add meta features (data_confidence, sources_count)

- [ ] Create feature vector export
  - [ ] Combine all 209 features into single vector
  - [ ] Handle NULLs (use -1 or create _missing flags)
  - [ ] Validate data types for SageMaker

**Testing:**
- [ ] Test on 1,000 games
- [ ] Verify all 209 features present
- [ ] Check NULL handling
- [ ] Validate derived feature calculations

**Output:**
- [ ] Feature vectors in DataFrame format
- [ ] Export to CSV (testing)
- [ ] Export to Parquet (production)

**Validation:**
- [ ] Verify 209 features per record
- [ ] Check NULL rates (<15% per feature)
- [ ] Validate derived feature logic

**Completion criteria:**
- [ ] 209-feature vectors created
- [ ] NULL handling implemented
- [ ] Sample feature vectors validated
- [ ] Export format ready for SageMaker

---

### Sub-Phase 1.12: Quality Dashboard (2 hours)

**Prerequisites:**
- [ ] Feature engineering complete
- [ ] Multi-source data stored

**Implementation:**
- [ ] Create `scripts/analytics/generate_quality_report.py`
  - [ ] Calculate per-source metrics
  - [ ] Calculate overall data quality score
  - [ ] Track feature completeness by era
  - [ ] Generate coverage matrix

- [ ] Create visualization dashboard (optional)
  - [ ] HTML dashboard with Chart.js
  - [ ] Show feature availability by source
  - [ ] Show NULL rates per feature
  - [ ] Show coverage by time period

**Output:**
- [ ] Generate `docs/MULTI_SOURCE_QUALITY_REPORT.md`
- [ ] Create dashboard HTML (optional)

**Metrics to track:**
- [ ] Feature completeness: ≥90% for 2016-present
- [ ] Historical coverage: ≥80% for 1946-1999
- [ ] NULL rate: ≤15% per feature
- [ ] Average confidence: ≥0.80

**Completion criteria:**
- [ ] Quality report generated
- [ ] Metrics meet targets
- [ ] Dashboard accessible (if created)

---

## 📋 Week 4: Validation & Optional (4 hours)

### Sub-Phase 1.14: SageMaker Data Validation (2 hours)

**Prerequisites:**
- [ ] Feature vectors exported
- [ ] Parquet files in S3

**Implementation:**
- [ ] Create `scripts/ml/validate_for_sagemaker.py`
  - [ ] Check for NULLs (error if critical fields NULL)
  - [ ] Validate data types (all numeric or properly encoded)
  - [ ] Check for infinite values (error if found)
  - [ ] Verify label distribution (warn if imbalanced)
  - [ ] Check feature count (209 expected)
  - [ ] Validate file format (Parquet readable)

**Testing:**
- [ ] Run validation on full dataset
- [ ] Fix any errors found
- [ ] Re-export if needed

**Output:**
- [ ] Validation report with pass/fail per check
- [ ] List of any issues to fix

**Completion criteria:**
- [ ] All validation checks pass
- [ ] Data ready for SageMaker
- [ ] No critical errors

---

### Sub-Phase 1.9: SportsDataverse (Optional, 2 hours)

**Prerequisites:**
- [ ] Install: `pip install sportsdataverse`

**Implementation:**
- [ ] Create `scripts/etl/scrape_sportsdataverse.py`
  - [ ] Test ESPN wrapper
  - [ ] Compare with our ESPN parsing
  - [ ] Use for cross-validation only

**Testing:**
- [ ] Compare 10 games: SportsDataverse vs our ESPN
- [ ] Verify we're parsing correctly

**Completion criteria:**
- [ ] Cross-validation complete
- [ ] Our ESPN parsing verified

---

## ✅ Final Checklist

**Before marking Phase 1 complete:**
- [ ] All 5 sources integrated
- [ ] 209 features extracted per game
- [ ] Database tables created and populated:
  - [ ] `player_advanced_stats` (Basketball Reference)
  - [ ] `player_tracking_stats` (NBA.com Stats)
  - [ ] `shot_chart` (NBA.com Stats)
  - [ ] `games_multi_source` (all sources)
- [ ] Feature engineering pipeline working
- [ ] SageMaker validation passed
- [ ] Quality report generated
- [ ] Sample ML training successful

**Success metrics achieved:**
- [ ] Feature completeness ≥90% (2016-present)
- [ ] Historical coverage ≥80% (1946-1999)
- [ ] NULL rate ≤15% per feature
- [ ] Confidence score ≥0.80 average
- [ ] All validation checks pass

**Documentation updated:**
- [ ] PROGRESS.md (mark Phase 1 complete)
- [ ] PHASE_1_FINDINGS.md (add multi-source results)
- [ ] COMMAND_LOG.md (log all commands run)
- [ ] Create ADR if major decisions made

**Ready for Phase 5 ML:**
- [ ] Feature vectors exported to S3
- [ ] Parquet format validated
- [ ] 209 features available
- [ ] Historical data included
- [ ] SageMaker notebook can access data

---

## 📊 Progress Tracking

**Track your progress:**

| Week | Phase | Hours | Status | Completion |
|------|-------|-------|--------|------------|
| 1 | Basketball Reference | 8 | ⏸️ Pending | 0% |
| 1 | NBA.com Stats | 4 | ⏸️ Pending | 0% |
| 2 | Kaggle | 4 | ⏸️ Pending | 0% |
| 2 | Multi-source storage | 4 | ⏸️ Pending | 0% |
| 3 | Feature engineering | 4 | ⏸️ Pending | 0% |
| 3 | Quality dashboard | 2 | ⏸️ Pending | 0% |
| 4 | SageMaker validation | 2 | ⏸️ Pending | 0% |
| 4 | SportsDataverse | 2 | ⏸️ Pending | 0% |
| **TOTAL** | | **28** | | **0%** |

**Update status:**
- ⏸️ Pending → 🔄 In Progress → ✅ Complete

---

## 🚨 Blockers & Issues

**Track any blockers here:**

| Issue | Impact | Status | Resolution |
|-------|--------|--------|------------|
| | | | |

**Common issues:**
- Basketball Reference rate limit → Add 3-second delay
- NBA.com timeout → Add exponential backoff
- Kaggle download fails → Check API credentials
- ID mapping fails → Use composite key (date + teams)
- NULL rates high → Check source availability

---

## 📝 Notes & Learnings

**Document key learnings:**

| Learning | Implication | Action Taken |
|----------|-------------|--------------|
| | | |

---

*Last updated: October 6, 2025*
*Use this checklist to track 209-feature implementation progress*

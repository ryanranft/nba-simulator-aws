# Changelog

All notable changes to the NBA Simulator AWS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed - ETL Script Cleanup & Organization

**Date:** October 8, 2025

**Phase 2: Documentation Consolidation**

**Changes Applied:**
1. **Deprecated script archival:**
   - Archived `extract_espn_local_to_temporal.py` (v1) → `scripts/archive/deprecated/`
   - Archived `extract_espn_local_to_temporal_UPDATED.py` → `scripts/archive/deprecated/`
   - Archived `download_kaggle_database.py` → `scripts/archive/deprecated/`
   - Archived `scrape_sportsdataverse.py` → `scripts/archive/deprecated/`

2. **Added deprecation notices:**
   - All 4 archived files now have clear deprecation warnings at top of docstring
   - Includes deprecation date, reason, and pointer to active replacement

3. **Created ETL directory README:**
   - New `scripts/etl/README.md` (5.7KB) provides comprehensive guide
   - Lists all active scrapers (5 core scrapers)
   - Documents deprecated scripts with explanations
   - Includes quick start commands and monitoring procedures
   - References Workflow #42 for complete documentation

4. **Updated documentation references:**
   - `docs/DATA_SOURCES.md`: Updated Kaggle and SportsDataverse script references
   - Marked deprecated files with strikethrough and ❌ status
   - Added pointers to active replacements

**Benefits:**
- ✅ Clear separation of active vs deprecated scripts
- ✅ Single source of truth for ETL script usage
- ✅ Eliminated confusion about which scripts to use
- ✅ Improved discoverability with comprehensive README
- ✅ Preserved deprecated code for reference

**Active Scripts After Cleanup:**
- `download_kaggle_basketball.py` (replaces download_kaggle_database.py)
- `extract_espn_local_to_temporal_v2.py` (replaces v1 and UPDATED)
- `extract_kaggle_to_temporal.py`
- `scrape_hoopr_phase1b_only.R` (replaces scrape_sportsdataverse.py)

---

### Fixed - Basketball Reference Rate Limit Issues

**Date:** October 8, 2025

**Problem:** Basketball Reference scraper was getting 429 "Too Many Requests" errors on every request with 3-second rate limit.

**Root Cause:**
- 3-second rate limit was too aggressive for Basketball Reference servers
- Exponential backoff started at only 1s (10^0) for 429 errors, insufficient to recover from rate limiting
- Argparse default was not updated when __init__ default was changed

**Solution Applied:**
1. **Increased base rate limit:** 3.0s → 5.0s (67% increase)
   - Updated `__init__` default parameter (line 53)
   - Updated argparse default (line 623)
   - Updated overnight script documentation and estimates

2. **Enhanced 429-specific backoff:** 1s/10s/120s → 30s/60s/120s
   - First retry: 30 seconds (was 1s)
   - Second retry: 60 seconds (was 10s)
   - Third retry: 120 seconds (unchanged)
   - Formula: `min(120, 30 * (2 ** attempt))` for rate limits

3. **429 Detection working correctly:**
   - Detection: `'429' in str(e) or 'Too Many Requests' in str(e)`
   - Passes `is_rate_limit=True` to use longer backoff times

**Testing Results:**
- **Before fix:** 6 requests, 0 successes, 6 errors (100% failure rate)
- **After fix:** 2 requests, 2 successes, 0 errors, 0 retries (100% success rate)
- Test seasons: 2024 (1,319 games), 2025 (1,321 games)
- No 429 errors observed

**Files Modified:**
- `scripts/etl/scrape_basketball_reference_complete.py` (3 changes)
- `scripts/etl/overnight_basketball_reference_comprehensive.sh` (7 time estimates updated)

**Impact on Overnight Scraper:**
- Estimated runtime increase: +67% (due to 5s vs 3s rate limit)
- Player box scores: 79 hours → 132 hours
- Team box scores: 79 hours → 132 hours
- Play-by-play: 26 hours → 43 hours
- Schedules/totals/standings: 5 min → 7 min each

**Strategic Value:** Enables reliable overnight scraping of complete 75-year NBA historical dataset without rate limit failures.

### Added - Basketball Reference Complete Historical Scraper

**Date:** October 7, 2025

**Implementation:**
- Created comprehensive Python scraper using `basketball_reference_web_scraper` library
- 7 data types implemented for complete historical NBA coverage (1950-2025)
- 3-second rate limiting with exponential backoff retry logic
- Checkpoint/resume functionality for interrupted scraper recovery
- S3 upload integration to `s3://nba-sim-raw-data-lake/basketball_reference/`

**Scripts Created:**
- `scripts/etl/scrape_basketball_reference_complete.py` - Complete scraper (737 lines)
- `scripts/etl/overnight_basketball_reference_comprehensive.sh` - Overnight wrapper script

**Data Types Captured:**
1. **Schedules** - Game schedules per season (79 files expected)
2. **Player Box Scores** - Daily player statistics (~1.9M records)
3. **Team Box Scores** - Daily team statistics (~190K records)
4. **Season Totals** - Player season aggregates (~35,500 records)
5. **Advanced Totals** - Advanced metrics (~35,500 records)
6. **Play-by-Play** - Event-level data for modern era 2000-2025 (~30,750 games)
7. **Standings** - Final season standings (79 files expected)

**Critical Fix Applied:**
- Error: Missing combined statistics for mid-season traded players
- Root cause: `include_combined_values=True` parameter not set in advanced totals
- Solution: Added parameter to `players_advanced_season_totals()` call
- Impact: +78 records (12% more data) for 2024 season validation test

**Coverage:**
- **Seasons:** 1950-2025 (75 NBA seasons)
- **Library Limitation:** BAA years (1947-1949) not supported by library
- **Note:** Basketball Reference website HAS BAA data but requires custom scraper

**Testing Results:**
- 2024 season schedule: 1,319 games ✓
- 2024 season totals: 657 players ✓
- 2024 advanced totals (with fix): 735 records ✓
- 1950 season (earliest): 269 players ✓
- 1947 season (BAA): Not supported by library ✗

**Deployment Status:**
- Overnight scraper started: October 7, 2025 - 10:50 PM CDT
- Master PID: 57075
- Estimated runtime: Several days for complete historical coverage
- Monitor logs: `/tmp/bbref_*.log`

**Known Issues:**
- Old team name parsing errors in early NBA years (1950s)
- Teams like 'TRI-CITIES BLACKHAWKS', 'FORT WAYNE PISTONS', etc. cause parser errors
- Scraper continues with next season (error handling works)
- May require library patch or custom parser for complete early-era coverage

**Strategic Value:**
- Enables SageMaker training on complete 75-year NBA historical dataset
- Captures data evolution patterns (rule changes, pace changes, etc.)
- Provides maximum feature richness for panel data transformation
- User directive: "GET ALL DATA POSSIBLE" - implemented with 7 data types

**Documentation Updates:**
- `docs/SESSION_HANDOFF_20251007_BASKETBALL_REF.md` - Implementation results
- `CHANGELOG.md` - This entry

### Added - hoopR Phase 1 Foundation Data Scraper

**Date:** October 7, 2025

**Implementation:**
- Created comprehensive R-based scraper using hoopR package (151 total endpoints available)
- Phase 1 focuses on ~50 high-value foundation endpoints (95% of data value)
- Fixed `save_csv()` function to handle hoopR's list return values instead of just data frames
- CSV output format (avoids R's 2GB JSON string limit)
- Per-season saves to prevent memory exhaustion

**Scripts Created:**
- `scripts/etl/scrape_hoopr_phase1_foundation.R` - Full Phase 1 scraper
- `scripts/etl/scrape_hoopr_phase1b_only.R` - Phase 1B standalone (league dashboards)
- `scripts/etl/run_hoopr_phase1.sh` - Phase 1 wrapper script
- `scripts/etl/run_hoopr_phase1b.sh` - Phase 1B wrapper script

**Phase 1A (Bulk Loaders) - COMPLETE:**
- 96 CSV files, 2.5 GB
- Coverage: 2002-2025 (24 seasons × 4 endpoints)
- Play-by-play: 13.9M events
- Player box scores: 810K rows
- Team box scores: 63K rows
- Schedule: 31K games
- Uploaded to S3: `s3://nba-sim-raw-data-lake/hoopr_phase1/`

**Phase 1B (League Dashboards) - IN PROGRESS:**
- League player stats (per-season)
- League team stats (per-season)
- Standings (per-season)
- Expected: ~200 additional CSV files
- Note: Lineups, player tracking, hustle stats not available pre-2013

**Future Phases:**
- Phase 2: Per-game endpoints (~30 endpoints requiring game_ids)
- Phase 3: Per-player/team endpoints (~70 endpoints requiring player/team IDs)

**Fix Applied:**
- Error: `missing value where TRUE/FALSE needed` in save_csv()
- Root cause: hoopR returns lists containing data frames, not direct data frames
- Solution: Extract first valid data frame from list before validation

### Added - NBA API Comprehensive Scraper (Tier 1)

**Date:** October 6, 2025

**Implementation:**
- Fixed import errors in `scrape_nba_api_comprehensive.py`:
  - Changed to module-level import: `from nba_api.stats import endpoints as nba_endpoints`
  - Fixed all undefined function references by adding `nba_endpoints.` prefix
- Enabled Tier 1 endpoints (lines 360-362):
  - Advanced box scores (8 endpoints): 40-50 features
  - Player tracking (4 endpoints): 20-30 features

**Endpoints Enabled:**

*Advanced Box Scores (8 types):*
- `BoxScoreAdvancedV2` - Advanced efficiency metrics
- `BoxScoreDefensiveV2` - Defensive statistics
- `BoxScoreFourFactorsV2` - Four factors breakdown
- `BoxScoreMiscV2` - Miscellaneous stats
- `BoxScorePlayerTrackV2` - Player tracking metrics
- `BoxScoreScoringV2` - Scoring breakdown
- `BoxScoreTraditionalV2` - Traditional box scores
- `BoxScoreUsageV2` - Usage rates

*Player Tracking (4 types):*
- `PlayerDashPtPass` - Passing stats (passes made, potential assists)
- `PlayerDashPtReb` - Rebounding stats (contested rebounds, chances)
- `PlayerDashPtShotDefend` - Shot defense (contests, DFG%)
- `PlayerDashPtShots` - Shot tracking (touch time, dribbles)

**Scraper Status:**
- Overnight scraper started: October 6, 2025 - 10:56 PM
- PID: 50691
- Expected completion: 4-5 AM (5-6 hours runtime)
- Coverage: 30 seasons (1996-2025)
- Output: `/tmp/nba_api_comprehensive/` and `s3://nba-sim-raw-data-lake/nba_api_comprehensive/`

**Testing Configuration:**
- Advanced box scores: 100 games per season (testing limit)
- Player tracking: 50 players per season (testing limit)
- Shot charts: 20 players per season
- Runtime: ~10 minutes per season

**Feature Impact:**
- Previous feature count: 209
- Tier 1 features added: 60-80
- **New total: 269-289 features** (+29-38%)

**Production Notes:**
- Current run uses testing limits for validation
- Production run (all games, all players) would take: 750-900 hours (31-37 days)
- Recommend EC2 deployment for production run

**Documentation Updates:**
- `docs/MISSING_ENDPOINTS_ANALYSIS.md` - Marked Tier 1 as implemented
- `docs/DATA_SOURCES.md` - Updated NBA API status to ACTIVE
- `docs/SCRAPER_TEST_RESULTS.md` - Added comprehensive test results
- `scripts/etl/overnight_nba_api_comprehensive.sh` - Updated runtime estimates
- `scripts/etl/scrape_nba_api_comprehensive.py` - Added implementation notes

### Changed
- NBA API scraper: PENDING → ACTIVE (LIMITED)
- Feature count: 209 → 269-289 (+29-38%)
- Total endpoints: 21 → 33 (+12 Tier 1 endpoints)

---

## [1.4.0] - 2025-10-03

### Added - Phase 4: EC2 Simulation Engine

**Infrastructure:**
- EC2 t3.small instance deployed (i-0b8bbe4cdff7ae2d2) running Amazon Linux 2023
- SSH key pair created: `nba-simulator-ec2-key` with 400 permissions
- Security group configured (sg-0b9ca09f4a041e1c8) for SSH access from specific IP
- RDS security group updated to allow EC2 connections via source-group reference
- Python 3.11.13 installed with scientific computing packages (boto3, pandas, psycopg2, numpy, scipy)
- PostgreSQL 15.14 client installed for database testing

**Simulation Engine:**
- `db_connection.py`: Database interface class with methods for team statistics, head-to-head matchups, and recent games
- `simulate_game.py`: Monte Carlo simulator using normal distribution scoring model
  - Home court advantage: +3.0 points
  - Standard deviation: 12.0 points
  - Command-line interface with argparse
  - CSV result export functionality
- `~/nba-simulation/README.md`: Complete simulation methodology documentation (3.9 KB)
- Environment configuration with auto-loading credentials from `~/.env`

**Testing & Validation:**
- Tested LAL vs BOS simulation: 54.1% win probability (1,000 iterations)
- Tested GSW vs MIA simulation: 58.1% win probability (5,000 iterations)
- Database connectivity verified: 44,828 games, 6,781,155 play-by-play rows
- Performance validated: 5,000 iterations complete in ~5-8 seconds

**Workflows:**
- Created Workflow #37: Credential Management
  - Step-by-step guide for adding AWS resource credentials
  - Templates for EC2, RDS, S3, SageMaker credentials
  - Security best practices (chmod 600, .gitignore, rotation schedules)
  - Troubleshooting section for common credential issues

**Documentation:**
- Updated `PHASE_4_SIMULATION_ENGINE.md` with comprehensive "What Actually Happened" section
  - Actual commands executed with real resource IDs
  - Critical insights: what worked well vs. what didn't
  - Lessons learned for Phase 5
  - Actual time breakdown (3 hours total)
- Updated `PROGRESS.md`:
  - Phase 4 marked as COMPLETE (Oct 3, 2025)
  - Current cost updated to $38.33/month (S3 + RDS + EC2)
  - Executive summary updated with Phase 4 accomplishments
  - Success criteria marked complete
- Updated `/Users/ryanranft/nba-sim-credentials.env` with EC2 configuration section

**Cost Impact:**
- Added $6.59/month for EC2 t3.small (8 hrs/day usage pattern)
- Total project cost: $38.33/month (within $150 budget)

### Changed
- Phase 4 status: PENDING → COMPLETE
- System now has 37 workflows (added Workflow #37)
- 4 of 6 phases complete (Phases 1-4)

### Technical Details
- **Database Schema Validation:** Verified actual column names (`home_team_abbrev`, not `home_team_abbreviation`)
- **Security Groups:** Used source-group references instead of IP ranges for EC2-RDS communication
- **Package Installation:** Used `--user` flag for pip to avoid permission issues
- **Environment Persistence:** Auto-load `~/.env` in `.bashrc` for persistent environment

### Lessons Learned
1. Always check database schema with `\d table_name` before writing queries
2. Use `aws ec2 wait` commands for instance state changes
3. Security groups work better with source-group references than IP ranges
4. Test database connections with both psql AND Python before deploying code
5. Document all resource IDs immediately after creation

---

## [1.3.0] - 2025-10-02

### Added
- Modular workflow system (36 workflows)
- Phase-based documentation structure
- Navigation integration between PROGRESS.md and phase files

### Changed
- Reorganized CLAUDE.md from 436 to 216 lines (50% reduction)
- Streamlined workflow documentation into modular files

---

## [1.2.0] - 2025-10-01 to 2025-10-02

### Added - Phases 1-3 Complete

**Phase 1: S3 Data Lake**
- S3 bucket created: `nba-sim-raw-data-lake`
- 146,115 JSON files uploaded (119 GB)
- Cost: $2.74/month

**Phase 2: ETL Pipeline**
- Local data extraction (bypassed AWS Glue)
- 46,595 games extracted (1993-2025)
- 6,781,155 play-by-play rows loaded
- 408,833 player stats loaded
- Cost: $0 (local execution)

**Phase 3: Database Infrastructure**
- RDS PostgreSQL db.t3.small deployed
- Database: `nba_simulator` with 58-column schema
- All tables created and indexed
- Cost: $29/month

---

## [1.1.0] - 2025-09-29 to 2025-09-30

### Added
- Initial project setup
- AWS account configuration
- GitHub repository initialized
- Development environment (conda)

---

## [1.0.0] - 2025-09-29

### Added
- Project inception
- Architecture planning
- Cost estimation ($95-130/month projected)
- 6-phase implementation plan

---

**Legend:**
- 🚀 New feature
- ✅ Completed phase
- 🔧 Technical improvement
- 📝 Documentation update
- 💰 Cost impact
- 🔒 Security enhancement
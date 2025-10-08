# Changelog

All notable changes to the NBA Simulator AWS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
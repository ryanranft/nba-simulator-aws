# Changelog

All notable changes to the NBA Simulator AWS project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
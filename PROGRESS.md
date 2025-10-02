# NBA Game Simulator & ML Platform - Setup Progress Log

<!-- AUTO-UPDATE TRIGGER: After completing ANY task, mark ✅ COMPLETE immediately -->
<!-- LAST STATUS CHANGE: 2025-10-02 -->
<!-- CURRENT PHASE: Phase 1 & 2 Complete, Phase 3 (RDS) Complete, Phase 4+ Pending -->
<!-- REMINDER: Update costs after creating AWS resources, run `make sync-progress` after phase completion -->

**Date Started:** September 29, 2025  
**Project Goal:** Configure NBA Game Simulator & ML Platform on AWS with proper local development environment

---

## DOCUMENTATION NAVIGATION

**This document tracks project status, phases, timeline, and next steps.**

**For detailed information, see:**
- **Architecture decisions:** `docs/adr/README.md` (ADRs 001-005)
- **Setup instructions:** `docs/SETUP.md` (11-step guide)
- **Quick reference:** `QUICKSTART.md` (commands, file locations, daily workflow)
- **Troubleshooting:** `docs/TROUBLESHOOTING.md` (28 issues + solutions)
- **Code style:** `docs/STYLE_GUIDE.md` (Python/SQL standards)
- **Testing:** `docs/TESTING.md` (pytest strategy)
- **LLM guidelines:** `CLAUDE.md` (instructions for Claude Code)
- **Environment variables:** `.env.example` (35 variables template)
- **Maintenance:** `docs/DOCUMENTATION_MAINTENANCE.md` (weekly/monthly tasks)

---

## EXECUTIVE SUMMARY

**Project Status:** Phase 1 & 2 COMPLETE - S3 Data Lake + Local ETL Extraction Operational
**Date Completed:** October 2, 2025

### INSTRUCTIONS FOR LLM CONTINUING THIS PROJECT:

1. Read through this entire progress log to understand what has been completed
2. Follow the steps laid out chronologically, starting from the first "⏸️ PENDING" or "⏳ IN PROGRESS" item
3. **CRITICAL:** Only mark steps as "✅ COMPLETE" when you receive:
   - Code output from the user showing successful execution, OR
   - Explicit verbal confirmation from the user that the step is complete
4. Do NOT assume steps are complete without user confirmation
5. Update this progress log after each completed step
6. If a step fails or encounters errors, document the issue and work with the user to resolve it before proceeding
7. Maintain the same format and detail level when updating the log

### Quick Start for New Chat

Before beginning any new work, verify the current environment state:

```bash
# Verify conda environment
conda activate nba-aws

# Verify S3 data
aws s3 ls s3://nba-sim-raw-data-lake/

# Navigate to project directory
cd /Users/ryanranft/nba-simulator-aws

# Check git status
git status

# Verify Python packages
pip list | grep boto3
pip list | grep pandas
```

### What's Been Accomplished:

- Local development environment fully configured (Python 3.11, conda, 146K+ files)
- AWS S3 raw data lake created and populated with 119 GB of NBA data (1999-2025)
- All infrastructure foundations in place for ETL pipeline

### Current State:

- **Working:** AWS credentials verified, S3 bucket `nba-sim-raw-data-lake` with 146,115 files
- **Environment:** Conda env `nba-aws`, Python 3.11.13, all dependencies installed
- **Git:** Repository synced with GitHub (SSH authentication, 3 commits pushed)
- **Cost:** Currently ~$2.74/month for S3 storage only

### Critical Paths:

- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **Original Data:** `/Users/ryanranft/0espn/data/nba/`
- **S3 Bucket:** `s3://nba-sim-raw-data-lake`
- **Conda Env:** `nba-aws` at `/Users/ryanranft/miniconda3/envs/nba-aws`

### Data Details:

- **Time Period:** NBA games 1999-2025
- **File Count:** 146,115 JSON files
- **Total Size:** 119 GB raw / ~12 GB after 10% extraction (estimated)
- **Types:** Box scores (44,828), Play-by-play (44,826), Schedule (11,633), Team stats (44,828)

### Known Issues:

- PyCharm may be slow (data folder should be marked as "Excluded")

### IMPORTANT NOTES:

- AWS CLI is installed system-wide, NOT in conda environment
- Do not install awscli via pip (causes conflicts)
- Data folder MUST remain in .gitignore (too large for GitHub)

### Phase 2 Completion Summary (October 2, 2025):

**Approach Taken:** Implemented local Python extraction scripts (bypassing AWS Glue ETL) to extract data directly from S3 to RDS PostgreSQL.

**Results Achieved:**
- ✅ **Schedule Data:** 46,595 games with 53 fields (1993-2025) - **488% increase** from original 9 fields
- ✅ **Play-by-Play Data:** 6,781,155 plays (1997-2021)
- ✅ **Box Scores Data:** 408,833 player stats + 15,900 team stats (1997-2021)
- ✅ **Schema Enhancement:** 58 columns in games table (25 new columns added)
- ✅ **Automation Success:** All 4 overnight processes completed with zero critical errors
- ✅ **User Requirement Fulfilled:** Schedule data made "as rich as possible" with full metadata extraction

**Cost Impact:** No AWS Glue charges (saved $13/month), RDS operational at ~$29/month

**Database Final State:**
- games: 44,828 rows with 58 columns
- play_by_play: 6,781,155 rows
- teams: 87 rows

See `OVERNIGHT_SUCCESS_SUMMARY.md` for complete extraction details.

### Next Immediate Steps:

1. ~~Set up AWS Glue Crawler to discover data schema~~ (Bypassed - using local extraction)
2. ~~Create Glue ETL job to extract 10% of relevant fields~~ (Bypassed - using local extraction)
3. ✅ Provision RDS PostgreSQL database (operational)
4. ✅ Complete data transformation and loading (Phase 2 COMPLETE)

### Key Decisions Made:

- Skipped Redshift initially to minimize costs (save $600-8,000/month)
- Extract only 10% of JSON fields needed for simulations (reduces storage/processing)
- Using Python 3.11 for AWS Glue compatibility
- Data folder excluded from PyCharm indexing due to 146K+ files

**Architecture:** Following 5-phase plan (S3 → Glue → RDS → EC2 → SageMaker)

**Estimated Monthly AWS Cost (when fully deployed):** $95-130/month

---

## PROJECT STATUS OVERVIEW

### ✅ COMPLETED WORK

**Phase 1 - Infrastructure:**
- Local development environment (Python 3.11, conda)
- AWS S3 raw data lake with 146,115 files (119 GB)
- Project directory structure
- Git repository with GitHub sync (SSH authentication)

**Phase 1 - Configuration:**
- AWS CLI verified and configured
- IAM permissions confirmed (AdministratorAccess)
- Conda environment `nba-aws` created
- PyCharm project initialized

**Phase 1 - Data:**
- All NBA data (1999-2025) uploaded to S3
- Local data copy maintained
- Backup strategy established

**Phase 2 - Local ETL Extraction (October 2, 2025):**
- ✅ RDS PostgreSQL database created (db.t3.small, 58-column schema)
- ✅ Enhanced schedule extraction: 46,595 games with 53 fields (1993-2025)
- ✅ Play-by-play extraction: 6,781,155 plays (1997-2021)
- ✅ Box scores extraction: 408,833 player stats + 15,900 team stats (1997-2021)
- ✅ Schema enhancement: 25 new columns added to games table
- ✅ Automated overnight pipeline with auto-start monitoring
- ✅ Zero critical errors across all 4 extraction processes
- ✅ User requirement fulfilled: Schedule data "as rich as possible" (488% increase)

### ⏸️ PENDING WORK

**Next Immediate Tasks:**
1. Set up AWS Glue Crawler to discover data schema
2. Create Glue ETL job to extract 10% of relevant fields
3. Provision RDS PostgreSQL database (adds ~$29/month)
4. Begin data transformation and loading

**Remaining Infrastructure:**
- AWS Glue (Crawler + ETL Job)
- RDS PostgreSQL Database
- EC2 Simulation Engine
- SageMaker ML Pipeline (Notebooks + Training)
- Optional: S3 Analytics Lake, Athena, CloudWatch

**Blockers:**
- Must complete Glue Crawler + RDS before ETL job can run

---

## ARCHITECTURE DECISION RECORDS

**For complete architectural decisions, see:** `docs/adr/README.md`

**Key decisions made:**
- **ADR-001:** Redshift exclusion (save $200-600/month, use RDS PostgreSQL)
- **ADR-002:** Extract 10% of JSON fields (119 GB → 12 GB, 90% storage savings)
- **ADR-003:** Python 3.11 (AWS Glue 4.0 compatibility, 10-60% faster than 3.9)
- **ADR-005:** Git SSH authentication (security + no password prompts)

**Total estimated savings:** $600-8,000/month vs. original full-scale architecture

---

## CRITICAL DECISIONS & BLOCKERS

**Purpose:** Track key decisions that must be made before proceeding with implementation. These are blockers that require user input.

### Pre-ETL Decisions (Must Resolve Before Phase 2.2)

**Decision Status:** ⏸️ PENDING

These decisions must be finalized before starting the Glue ETL job:

**1. JSON Field Extraction Mapping**
- **Action Required:** Examine sample JSON files and document exact field paths
- **Output:** Create `scripts/etl/field_mapping.yaml`
- **Impact:** Determines which 10% of data gets extracted
- **Timeline:** 1 hour
- **Blocking:** Cannot write ETL script without this

**2. Missing Data Handling Strategy**
- **Decision:** How to handle missing/malformed data?
- **Options:** 
  - Skip records with missing required fields
  - Use default values (specify defaults)
  - Partial record insertion (with NULL values)
- **Impact:** Data quality and completeness
- **Recommendation:** Skip records missing required fields, allow NULLs for optional fields

**3. ETL Refresh Strategy**
- **Decision:** Incremental vs. full refresh?
- **Options:**
  - Full refresh: Delete all, reload all (simpler, safer)
  - Incremental: Only process new/changed files (complex, efficient)
- **Impact:** Processing time and cost
- **Recommendation:** Full refresh initially, consider incremental after validation

**4. Data Validation Rules**
- **Decision:** What validation rules should be enforced?
- **Examples:**
  - Foreign key constraints (player_id → players table)
  - Required fields cannot be NULL
  - Date ranges must be valid
  - Numeric values must be within realistic bounds
- **Impact:** Data integrity and error handling
- **Action Required:** Define validation rules before ETL development

### Configuration Decisions

**GitHub Integration:** ✅ COMPLETE - See ADR-005

---

## WHAT STILL NEEDS CONFIGURATION

**Purpose:** Detailed roadmap of remaining AWS infrastructure components with time estimates, cost projections, prerequisites, and implementation order.

**Important Notes:**
- All time estimates assume working 4 hours per day
- Costs shown are monthly recurring unless marked "one-time"
- Data transfer costs between AWS services are typically negligible for this project size
- All estimates in USD, us-east-1 region pricing

---

### DEPENDENCY CHAIN

**Must Complete in This Order:**

1. **Phase 2.1:** Glue Crawler (discover schema) - ⏸️ PENDING
2. **Phase 3.1:** RDS Database (create tables) - ⏸️ PENDING
3. **Phase 2.2:** Glue ETL Job (populate database) - ⏸️ PENDING
4. **Phase 4.1:** EC2 Simulation Engine (run simulations) - ⏸️ PENDING
5. **Phase 5.1:** SageMaker Notebooks (ML development) - ⏸️ PENDING
6. **Phase 5.2:** SageMaker Training (model training) - ⏸️ PENDING

**⚠️ CRITICAL:** Cannot proceed to Phase 2.2 until Phases 2.1 AND 3.1 are complete.

---

### DEPENDENCY VISUAL DIAGRAM

**Purpose:** Show the critical path and dependencies between phases to understand what must be completed before proceeding.

```
PHASE DEPENDENCY FLOW:

Phase 1: S3 Data Lake
    ✅ COMPLETE
    └── 146,115 JSON files uploaded (119 GB)

Phase 2.1: Glue Crawler ⏸️
    ├── Prerequisite: Phase 1 ✅
    ├── Duration: 45 min
    └── Output: Data catalog schema
         │
         ├──────────────────┐
         │                  │
         ▼                  ▼
    Phase 3.1: RDS      BLOCKER: Must complete BOTH
    PostgreSQL ⏸️       Phase 2.1 AND 3.1 before
    ├── Prerequisite:   proceeding to Phase 2.2
    │   None (parallel)
    ├── Duration: 2-3 hrs
    └── Output: Empty   
         database with     
         schema            
         │                  
         └──────────────────┘
                │
                ▼
         Phase 2.2: Glue ETL Job ⏸️
         ├── Prerequisites: 
         │   • Phase 2.1 ✅ (schema discovered)
         │   • Phase 3.1 ✅ (database ready)
         │   • Critical Decisions resolved
         ├── Duration: 6-8 hrs + 3 hrs runtime
         └── Output: Populated RDS database
                │
                ▼
         Phase 4.1: EC2 Simulation Engine ⏸️
         ├── Prerequisites: Phase 2.2 ✅ (data loaded)
         ├── Duration: 2-3 hrs
         └── Output: Working simulation
                │
                ├──────────────────┐
                │                  │
                ▼                  ▼
         Phase 5.1:          Phase 5.2:
         SageMaker           SageMaker
         Notebooks ⏸️        Training ⏸️
         ├── Prereq: 2.2 ✅  ├── Prereq: 5.1 ✅
         ├── Duration: 2h    ├── Duration: 4-8h
         └── Output: ML env  └── Output: Models
```

**Critical Path Summary:**

Sequential Dependencies (cannot parallelize):
1. Phase 1 (S3) → Phase 2.1 (Glue Crawler)
2. Phases 2.1 + 3.1 → Phase 2.2 (Glue ETL)
3. Phase 2.2 → Phase 4.1 (EC2)
4. Phase 2.2 → Phase 5.1 (SageMaker Notebooks)
5. Phase 5.1 → Phase 5.2 (SageMaker Training)

Parallel Opportunities:
- Phase 2.1 (Glue Crawler) can run in parallel with Phase 3.1 (RDS setup)
- Phase 5.1 (SageMaker Notebooks) can run in parallel with Phase 4.1 (EC2)

Current Blocker:
Phase 2.1 (Glue Crawler) and Phase 3.1 (RDS) must both complete before Phase 2.2 (Glue ETL) can begin.

Estimated Time to Full Deployment:
- If working 4 hours/day: ~4 weeks
- If working 8 hours/day: ~2 weeks
- Critical path: ~25-30 hours of active work

---

### Phase 2: AWS Glue - Data Discovery & ETL

#### Component 2.1: AWS Glue Crawler (Year-Based Partitioning Approach)

**Status:** ⏸️ READY TO EXECUTE - Year-based partitioning strategy developed
**Decision Date:** 2025-10-01 22:00 EST
**Strategy:** Partition S3 by year, then run separate crawlers per year (365-366 files each)
**Estimated Success Rate:** 100% (each year well under 50K file limit)

**Evolution of Approach:**
1. ❌ **Single crawler** (146,115 files) → OutOfMemoryError after 90 min
2. ❌ **4 data-type crawlers** (11K-45K files each) → Internal Service Exception after 12 min
3. ✅ **Year-based crawlers** (365-366 files per year) → Expected to succeed

**Why Year-Based Approach Works:**
- Schedule files use YYYYMMDD format (easy year extraction)
- Game files use YYMMDD### format (1980 offset decoding)
- Each year has only 365-366 files (well under 50K limit)
- 33 years of data (1993-2025) = 33 crawlers per data type
- Total: ~132 crawlers (33 years × 4 data types)
- Each crawler expected to succeed in 2-5 minutes

**Implementation Steps:**

1. **Partition S3 data by year** ⏸️ (Run once)
   - Script: `scripts/etl/partition_by_year.py`
   - Command: `python scripts/etl/partition_by_year.py --execute`
   - Time: ~30-60 minutes (146K S3 copy operations)
   - Cost: ~$0.10 (S3 copy requests)
   - Output: `s3://.../schedule/year=1997/`, `s3://.../pbp/year=1998/`, etc.

2. **Create year-based crawlers** ⏸️
   - Script: `scripts/etl/create_year_crawlers.sh`
   - Command: `./scripts/etl/create_year_crawlers.sh --all`
   - Time: 5-10 minutes (AWS API calls)
   - Output: 132 crawlers (nba-schedule-1997-crawler, nba-pbp-1998-crawler, etc.)

3. **Run crawlers** ⏸️ (Can run multiple in parallel)
   - Start with one year to validate approach
   - Then run all crawlers for specific data type
   - Finally run all crawlers for all data types
   - Monitor progress and success rate

4. **Review discovered schemas** ⏸️
   - Validate schema matches expected structure
   - Check that year partitions are recognized by Glue
   - Verify table metadata is correct

5. **Clean up old failed crawlers** ⏸️
   - Delete: nba-data-crawler (146K files - failed)
   - Delete: nba-schedule-crawler (11K files - failed)
   - Delete: nba-pbp-crawler (45K files - created but not run)
   - Delete: nba-boxscores-crawler (45K files - created but not run)
   - Delete: nba-teamstats-crawler (45K files - created but not run)

**Prerequisites:**
- S3 bucket with data: ✅ COMPLETE
- IAM permissions: AdministratorAccess ✅
- Glue database exists: ✅ COMPLETE (nba_raw_data)
- IAM role exists: ✅ COMPLETE (AWSGlueServiceRole-NBASimulator)

**Estimated Time:** 2-3 hours total
- Cleanup old crawler: 5 minutes
- Create 4 new crawlers: 20 minutes
- Run schedule crawler: 5-10 minutes (guaranteed success)
- Run PBP crawler: 15-30 minutes (test if 45K works)
- Run remaining crawlers: 30-60 minutes (if PBP succeeds)
- Review schemas: 15 minutes

**Previous Failure Analysis (Single Crawler):**
```
[23:34:03] BENCHMARK: Running Start Crawl (146,115 files)
[23:52:52] BENCHMARK: Classification complete, writing results
[23:58:04] WARN: OutOfMemoryError - Submit AWS Support ticket
[00:03:17] ERROR: Internal Service Exception
```

**Root Cause:** 146K+ files exceeded default DPU allocation

**New Strategy - File Count per Crawler:**
| Crawler | S3 Path | File Count | Expected Result |
|---------|---------|------------|-----------------|
| nba-schedule-crawler | s3://.../schedule/ | 11,633 | ✅ Will succeed (well under 50K) |
| nba-pbp-crawler | s3://.../pbp/ | 44,826 | ⚠️ Should succeed (~45K safe zone) |
| nba-boxscores-crawler | s3://.../box_scores/ | 44,828 | ⚠️ Run if PBP succeeds |
| nba-teamstats-crawler | s3://.../team_stats/ | 44,828 | ⚠️ Run if PBP succeeds |

**Thresholds (from LESSONS_LEARNED.md):**
- **Safe:** 0-50,000 files → Crawler should work
- **Risky:** 50,000-100,000 files → May fail
- **Fail:** 100,000+ files → Guaranteed failure

**Strategy:** All crawlers are in "Safe" zone (under 50K files each)

**Estimated Cost:** ~$1/month
- Crawler DPU cost: $0.44 per DPU-hour
- First run: ~10 DPUs × 0.25 hours = $1.10 (one-time)
- Monthly runs: 1 run/month = $1.10/month
- Data Catalog storage: First 1M objects free
- Recurring: ~$1/month

**Commands to Execute:**

```bash
# Verify S3 bucket access
aws s3 ls s3://nba-sim-raw-data-lake/

# Create Glue database
aws glue create-database \
  --database-input '{"Name":"nba_raw_data","Description":"NBA raw JSON data catalog"}'

# Create crawler via AWS Console (recommended) or CLI
# Then start crawler:
aws glue start-crawler --name nba-data-crawler

# Check crawler status
aws glue get-crawler --name nba-data-crawler
```

**Success Criteria:**
- Crawler status shows "READY" (not RUNNING or FAILED)
- 4 tables created: box_scores, pbp, schedule, team_stats
- Schemas accurately reflect JSON structure
- No errors in CloudWatch logs

**Verification Commands:**

```bash
# List discovered tables
aws glue get-tables --database-name nba_raw_data

# View schema for box_scores table
aws glue get-table --database-name nba_raw_data --name box_scores
```

**Rollback/Cleanup:**

```bash
# Delete crawler
aws glue delete-crawler --name nba-data-crawler

# Delete database (removes all tables)
aws glue delete-database --name nba_raw_data
```

---

#### Component 2.2: AWS Glue ETL Job

**Status:** ⏸️ Not Started  
**Purpose:** Extract 10% of fields from JSON, transform, and load into RDS

**Configuration Steps:**

1. Examine sample JSON files to identify exact field paths (1 hour)
2. Write PySpark ETL script in local environment (2-3 hours)
3. Test script locally with sample data (30 min)
4. Create Glue job definition in AWS Console (15 min)
5. Configure RDS connection in Glue (15 min)
6. Test job with 100 files (30 min)
7. Run full ETL job on all 146,115 files (2-4 hours runtime)
8. Validate data quality in RDS (30 min)

**Prerequisites:**
- Glue Crawler completed: ⏸️ Must complete 2.1 first
- RDS database created: ⏸️ Must complete 3.1 first
- RDS connection string and credentials
- Python 3.11 local environment: ✅ COMPLETE

**Estimated Time:** 6-8 hours of work + 3 hours job runtime
- JSON examination: 1 hour
- Script development: 2-3 hours
- Testing and debugging: 2 hours
- Configuration in AWS: 30 minutes
- Full ETL job runtime: 3 hours (automated)
- Validation: 30 minutes

**Estimated Cost Breakdown:**
- Development/testing runs: $5-10 (one-time, first week)
- Full production run: 10 DPUs × 3 hours × $0.44 = $13.20 per run
- If run monthly: $13.20/month
- If run weekly: $52.80/month
- **Recommendation:** Run monthly initially = $13/month

**Key Decisions Required:**

See **CRITICAL DECISIONS & BLOCKERS** section above for pre-ETL decisions that must be resolved before starting this component.

**Script Location:** `/Users/ryanranft/nba-simulator-aws/scripts/etl/glue_etl_job.py`

**Sample JSON Inspection Commands:**

```bash
# Download sample files for examination
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json ./sample_box_score.json
aws s3 cp s3://nba-sim-raw-data-lake/pbp/131105001.json ./sample_pbp.json
aws s3 cp s3://nba-sim-raw-data-lake/schedule/19930825.json ./sample_schedule.json
aws s3 cp s3://nba-sim-raw-data-lake/team_stats/131105001.json ./sample_team_stats.json

# View structure
cat sample_box_score.json | python -m json.tool | head -50
```

**Success Criteria:**
- ETL job completes for all 146,115 files without errors
- Data loaded into RDS with expected ~90% size reduction
- Row counts match expected values
- No NULL values in required fields
- Foreign key relationships valid
- Can query data successfully via SQL

**Verification Commands:**

```bash
# Connect to RDS and check row counts
psql -h nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com -U postgres -d nba_simulator

# In psql:
SELECT COUNT(*) FROM games;
SELECT COUNT(*) FROM players;
SELECT COUNT(*) FROM player_game_stats;
SELECT COUNT(*) FROM plays;
```

**Rollback/Cleanup:**

```bash
# Delete Glue job
aws glue delete-job --job-name nba-etl-job

# Truncate tables in RDS (if needed to re-run)
# Connect via psql and run: TRUNCATE TABLE table_name CASCADE;
```

---

### Phase 3: Database Infrastructure

#### Component 3.1: RDS PostgreSQL Database

**Status:** ✅ COMPLETE
**Purpose:** Relational database for simulation queries and analytics (OLTP + OLAP)
**Started:** 2025-10-01 19:13 EST
**Completed:** 2025-10-01 20:50 EST
**Total Time:** 1 hour 37 minutes

**Configuration Steps:**

1. Create SQL schema files locally (1 hour) ✅
2. Launch RDS PostgreSQL instance via AWS Console (20 min) ✅
3. Configure security group rules (15 min) ✅
4. Test connection from local machine (10 min) ✅
5. Run SQL scripts to create tables (15 min) ✅
6. Create indexes for performance (15 min) ✅
7. Configure automated backups (5 min) ✅ (auto-enabled)
8. Document connection details (5 min) ✅

**Prerequisites:**
- VPC configuration: Use default VPC ✅
- SQL schema design: ✅ COMPLETE (see sql/create_tables.sql, sql/create_indexes.sql)
- psql client installed locally: ✅ Available

**Actual Time Breakdown:**
- SQL script creation: 30 minutes ✅
- Security group creation: 10 minutes ✅
- RDS instance creation attempts: 15 minutes ✅
  - First attempt (db.t3.micro): Deleted due to account upgrade
  - Second attempt (db.t3.small): Successfully created
- Wait for instance availability: 10 minutes ✅
- Database schema creation: 5 minutes ✅
- Index creation: 2 minutes ✅
- Verification: 2 minutes ✅

**Final Configuration:**
- Instance: nba-sim-db (db.t3.small, PostgreSQL 15.14)
- Endpoint: nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com
- Database: nba_simulator
- Tables created: 6 (teams, players, games, player_game_stats, plays, team_game_stats)
- Indexes created: 33 (23 performance + 10 constraints)
- Status: Available and ready for ETL

**Estimated Cost:** ~$29/month (db.t3.small)

**Option A: db.t3.small (Recommended for Development)**
- 2 vCPUs, 2 GB RAM
- Compute: $0.034/hour × 730 hours = $24.82/month
- Storage: 20 GB GP3 SSD = $2.30/month
- Backup storage: 20 GB = $1.80/month
- **Total: $28.92/month (~$29/month)**
- **Best for:** Learning, development, testing

**Option B: db.t3.medium (Production-Ready)**
- 2 vCPUs, 4 GB RAM
- Compute: $0.068/hour × 730 hours = $49.64/month
- Storage: 50 GB GP3 SSD = $5.75/month
- Backup storage: 50 GB = $4.50/month
- **Total: $59.89/month (~$60/month)**
- **Best for:** Production use, faster queries, more concurrent connections

**Recommendation:** Start with db.t3.small ($29/month), can upgrade later with 5 minutes downtime

**Configuration Details:**

- **Engine:** PostgreSQL 15.x
- **Instance class:** db.t3.small
- **Storage:** 20 GB GP3 SSD
- **Multi-AZ:** No (single instance for cost savings)
- **Backup retention:** 7 days automated backups
- **Public accessibility:** Yes (for development - can restrict later)
- **Database name:** nba_simulator
- **Master username:** postgres
- **Master password:** [Create strong password]
- **Port:** 5432
- **Region:** us-east-1 (same as S3)

**Security Group Rules:**

```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: 
  - Your home IP (for local development)
  - EC2 security group (for simulation engine)
  - Glue service (for ETL job)
```

**SQL Scripts Needed:**

Location: `/Users/ryanranft/nba-simulator-aws/sql/`

Create these files:

1. `create_tables.sql` - Table definitions (teams, players, games, player_game_stats, plays, play_participants)
2. `create_indexes.sql` - Performance indexes on foreign keys, dates, player_id, game_id
3. `create_foreign_keys.sql` - Referential integrity constraints

**Connection String Format:**

```
postgresql://postgres[REDACTED]@nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com:5432/nba_simulator
```

**Success Criteria:**
- RDS status shows "Available"
- Can connect from local machine using psql
- All tables created successfully
- Indexes created
- Foreign keys enforced
- Test query executes in <1 second

**Verification Commands:**

```bash
# Test connection
psql -h nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com -U postgres -d nba_simulator

# In psql, verify setup:
\dt  -- List tables
\di  -- List indexes
SELECT version();  -- Check PostgreSQL version
```

**Rollback/Cleanup:**

```bash
# Delete RDS instance (stops billing immediately)
aws rds delete-db-instance \
  --db-instance-identifier nba-sim-db \
  --skip-final-snapshot

# Or take final snapshot:
aws rds delete-db-instance \
  --db-instance-identifier nba-sim-db \
  --final-db-snapshot-identifier nba-sim-db-final-snapshot
```

---

### Phase 4: Simulation Engine

#### Component 4.1: EC2 Instance for Simulations

**Status:** ⏸️ Not Started  
**Purpose:** Run NBA game simulations using data from RDS

**Configuration Steps:**

1. Launch EC2 instance (10 min)
2. Configure security group for SSH (5 min)
3. Connect via SSH and verify (5 min)
4. Install Python 3.11 and system dependencies (20 min)
5. Install Python packages (10 min)
6. Configure environment variables (10 min)
7. Upload simulation code (10 min)
8. Test database connection from EC2 (10 min)
9. Run test simulation (20 min)
10. Document instance details (10 min)

**Prerequisites:**
- RDS database populated: ⏸️ Must complete Phases 2.2 and 3.1
- Simulation Python code developed
- SSH key pair created (or use existing)

**Estimated Time:** 2-3 hours
- Instance launch and configuration: 30 minutes
- Software installation: 1 hour
- Testing and troubleshooting: 1 hour
- Documentation: 30 minutes

**Estimated Cost:** ~$10-30/month (usage-dependent)

**Option A: t3.small (Recommended - On-Demand)**
- 2 vCPUs, 2 GB RAM, $0.0208/hour
- If run 8 hours/day: $0.0208 × 8 × 30 = $4.99/month (~$5/month)
- If run 24/7: $0.0208 × 730 = $15.18/month (~$15/month)
- **Recommendation:** Start/stop as needed = $5-10/month

**Option B: t3.micro (Minimal Testing)**
- 2 vCPUs, 1 GB RAM, $0.0104/hour
- If run 4 hours/day: $0.0104 × 4 × 30 = $1.25/month (~$1/month)
- **Best for:** Minimal testing only

**Option C: Spot Instance t3.small (70% Discount)**
- Same specs as t3.small
- Cost: ~$0.006/hour (varies by availability)
- If run 24/7: ~$4.40/month
- **Risk:** Can be interrupted with 2-min warning
- **Best for:** Non-critical, interruptible workloads

**Recommendation:** Use t3.small on-demand, start when needed, stop when idle = $5-10/month

**Launch Configuration:**

- **AMI:** Amazon Linux 2023 (free tier eligible)
- **Instance type:** t3.small
- **Storage:** 20 GB GP3 (minimum)
- **Key pair:** Select existing or create new
- **Security group:** Allow SSH (port 22) from your IP

**Software Installation Commands:**

```bash
# Connect to instance
ssh -i your-key.pem ec2-user@ec2-xx-xx-xx-xx.compute-1.amazonaws.com

# Update system
sudo yum update -y

# Install Python 3.11
sudo yum install python3.11 python3.11-pip git -y

# Install PostgreSQL client
sudo yum install postgresql15 -y

# Install Python packages
pip3.11 install boto3 pandas psycopg2-binary sqlalchemy numpy

# Verify installations
python3.11 --version
psql --version
```

**Environment Variables:**

```bash
# Create ~/.env file
cat > ~/.env << 'EOF'
DB_HOST=nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=nba_simulator
DB_USER=postgres
DB_PASSWORD=your_password_here
EOF

# Load environment variables
source ~/.env
```

**Success Criteria:**
- Can SSH into instance without errors
- Python 3.11 installed and working
- Can connect to RDS from EC2 using psql
- Simulation code runs successfully
- Query response time acceptable (<5 seconds for typical queries)

**Verification Commands:**

```bash
# Test database connection from EC2
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM games;"

# Test Python connection
python3.11 -c "import psycopg2; print('Success')"
```

**Start/Stop Commands:**

```bash
# Stop instance when not in use (stops billing for compute, not storage)
aws ec2 stop-instances --instance-ids i-xxxxxxxxx

# Start instance when needed
aws ec2 start-instances --instance-ids i-xxxxxxxxx

# Get public IP after start
aws ec2 describe-instances --instance-ids i-xxxxxxxxx --query 'Reservations[0].Instances[0].PublicIpAddress'
```

**Rollback/Cleanup:**

```bash
# Terminate instance (stops all billing)
aws ec2 terminate-instances --instance-ids i-xxxxxxxxx
```

---

### Phase 5: Machine Learning Infrastructure

#### Component 5.1: SageMaker Notebook Instance

**Status:** ⏸️ Not Started  
**Purpose:** Jupyter environment for ML model development and experimentation

**Configuration Steps:**

1. Create IAM role for SageMaker with S3/RDS access (10 min)
2. Launch SageMaker notebook instance (10 min)
3. Open JupyterLab and verify (5 min)
4. Install custom packages in notebook (15 min)
5. Create test notebook for data access (30 min)
6. Test RDS connection (15 min)
7. Test S3 data access (15 min)

**Prerequisites:**
- RDS database with data: ⏸️ Must complete Phase 2.2
- S3 bucket with data: ✅ COMPLETE

**Estimated Time:** 2 hours
- Instance creation: 15 minutes
- IAM configuration: 15 minutes
- Environment setup and package installation: 30 minutes
- Testing data access: 30 minutes
- Initial notebook creation: 30 minutes

**Estimated Cost:** ~$2-25/month (usage-dependent)

**Option A: ml.t3.medium (Recommended for Development)**
- 2 vCPUs, 4 GB RAM
- Cost: $0.058/hour
- If run 40 hours/month: $0.058 × 40 = $2.32/month
- If run 100 hours/month: $0.058 × 100 = $5.80/month
- If run 24/7: $0.058 × 730 = $42.34/month
- **Recommendation:** Only run when actively developing = $2-10/month

**Option B: ml.t3.xlarge (For Larger Datasets)**
- 4 vCPUs, 16 GB RAM
- Cost: $0.232/hour
- If run 100 hours/month: $0.232 × 100 = $23.20/month
- **Best for:** Working with full dataset in memory

**Recommendation:** Use ml.t3.medium, stop when not in use = $2-5/month

**Configuration:**

- **Notebook instance name:** nba-ml-notebook
- **Instance type:** ml.t3.medium
- **Platform identifier:** Amazon Linux 2, Jupyter Lab 3
- **Volume size:** 20 GB
- **IAM role:** Create new role with S3/RDS access
- **VPC:** Same as RDS (for direct connection)

**Package Installation (in notebook):**

```bash
# In Jupyter terminal
pip install psycopg2-binary sqlalchemy pandas numpy scikit-learn matplotlib seaborn
```

**Success Criteria:**
- Notebook instance shows "InService" status
- Can access JupyterLab via browser
- Can query RDS data from notebook
- Can read S3 files from notebook
- Python kernel starts without errors

**Verification (in Jupyter notebook):**

```python
# Test RDS connection
import psycopg2
conn = psycopg2.connect(
    host='nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com',
    database='nba_simulator',
    user='postgres',
    password='your_password'
)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM games')
print(cursor.fetchone())

# Test S3 access
import boto3
s3 = boto3.client('s3')
response = s3.list_objects_v2(Bucket='nba-sim-raw-data-lake', MaxKeys=10)
print(f"Found {len(response['Contents'])} objects")
```

**Start/Stop:**

```bash
# Stop notebook when not in use
aws sagemaker stop-notebook-instance --notebook-instance-name nba-ml-notebook

# Start when needed
aws sagemaker start-notebook-instance --notebook-instance-name nba-ml-notebook
```

**Rollback/Cleanup:**

```bash
# Delete notebook instance
aws sagemaker delete-notebook-instance --notebook-instance-name nba-ml-notebook
```

---

#### Component 5.2: SageMaker Training Jobs

**Status:** ⏸️ Not Started  
**Purpose:** Train ML models on NBA data for game outcome predictions

**Prerequisites:**
- Feature engineering completed in notebooks: ⏸️
- Training data prepared and stored in S3: ⏸️
- Model training code written (Python sklearn/tensorflow/pytorch): ⏸️

**Estimated Time:** Variable by model complexity
- First model development: 4-8 hours
- Training script preparation: 2 hours
- First training job: 30-60 minutes (runtime)
- Hyperparameter tuning: 2-4 hours (multiple runs)

**Estimated Cost:** ~$5-50/month (highly variable based on experimentation)

- **ml.m5.xlarge:** $0.269/hour
- **Typical training job:** 30-60 minutes
- **Per training run:** $0.13-0.27
- **10 experiments:** ~$2.70
- **Monthly (moderate use):** $5-20
- **Monthly (heavy experimentation):** $20-50

**Training Instance Options:**
- **ml.m5.large:** $0.134/hour (smaller datasets)
- **ml.m5.xlarge:** $0.269/hour (recommended)
- **ml.m5.2xlarge:** $0.538/hour (large datasets)

**Recommendation:** Start with ml.m5.xlarge, $5-15/month for typical monthly experimentation

**Success Criteria:**
- Training job completes without errors
- Model metrics (accuracy, loss) logged to CloudWatch
- Model artifacts saved to S3
- Can load and test trained model
- Inference endpoint deployable (if needed)

---

### Phase 6: Optional Enhancements

#### Component 6.1: S3 Analytics Lake (Simulation Outputs)

**Status:** ⏸️ Not Started  
**Purpose:** Store simulation results in Parquet format for analysis

**Prerequisites:**
- Simulation engine running: ⏸️ (Phase 4.1)

**Estimated Time:** 1 hour
- Configure simulation code to write to S3: 30 min
- Test output format: 15 min
- Verify data accessible: 15 min

**Estimated Cost:** $0.50-5/month
- Storage: $0.023/GB/month
- If 10 GB outputs: $0.23/month
- If 100 GB outputs: $2.30/month
- Projection after 1 year: $5-10/month as data accumulates

---

#### Component 6.2: AWS Athena (SQL on S3)

**Status:** ⏸️ Not Started  
**Purpose:** Run ad-hoc SQL queries directly on S3 data without loading into database

**Prerequisites:**
- S3 analytics data in structured format (Parquet): ⏸️ (Phase 6.1)

**Estimated Time:** 30 minutes
- Create Athena database: 5 min
- Define tables pointing to S3: 15 min
- Run test queries: 10 min

**Estimated Cost:** Pay-per-query
- $5.00 per TB of data scanned
- Typical query scans: 10-100 MB
- Cost per query: $0.00005-0.0005 (~$0.0001)
- 100 queries/month: ~$0.01
- 1000 queries/month: ~$0.10
- **Monthly estimate:** $0.50-2/month for moderate use

**Benefit:** Cheaper than keeping RDS running 24/7 for occasional analytical queries

---

#### Component 6.3: CloudWatch Dashboards & Alarms

**Status:** ⏸️ Not Started  
**Purpose:** Monitor AWS resource usage, costs, and performance

**Estimated Time:** 1-2 hours
- Create cost alarm: 15 min
- Create performance dashboard: 30 min
- Set up error alerts: 30 min

**Estimated Cost:** ~$3/month
- Dashboards: $3/month per dashboard
- Alarms: Free for first 10 alarms
- Custom metrics: $0.30 per metric/month

**Recommended Alarms:**
- Monthly cost exceeds $150
- RDS CPU > 80% for 5 minutes
- EC2 instance stopped unexpectedly
- Glue job fails
- S3 storage exceeds 200 GB

---

## IMPLEMENTATION PRIORITY & TIMELINE

### Week 1 (Estimated: 8-10 hours of work):

1. ⏸️ Day 1-2: AWS Glue Crawler (45 min) - START: $1/month
2. ⏸️ Day 2-3: Examine JSON files, document field extraction plan (1 hour)
3. ⏸️ Day 3-5: RDS PostgreSQL setup (2 hours) - START: +$29/month

### Week 2 (Estimated: 6-8 hours of work):

4. ⏸️ Write Glue ETL script locally (3 hours)
5. ⏸️ Test ETL script with sample data (1 hour)
6. ⏸️ Create Glue job in AWS (1 hour)
7. ⏸️ Run full ETL job (3 hours runtime, monitor) - START: +$13/month

### Week 3 (Estimated: 4-6 hours of work):

8. ⏸️ Validate data in RDS (1 hour)
9. ⏸️ Set up EC2 simulation engine (2 hours) - START: +$5/month (occasional use)
10. ⏸️ Test simulations (2 hours)

### Week 4 (Estimated: 3-4 hours of work):

11. ⏸️ Set up SageMaker notebook (1 hour) - START: +$2/month (occasional use)
12. ⏸️ Create initial ML notebooks (2 hours)
13. ⏸️ Test ML workflows (1 hour)

### Optional (Month 2+):

14. ⏸️ S3 Analytics Lake + Athena setup (1.5 hours) - START: +$1/month
15. ⏸️ CloudWatch monitoring (1 hour) - START: +$3/month
16. ⏸️ Advanced ML training jobs (ongoing) - START: +$5-20/month

**Total Setup Time:** ~25-30 hours of work over 4 weeks

---

## TOTAL ESTIMATED COSTS SUMMARY

### Current Actual Cost (October 2, 2025):
- S3 Storage (raw data): $2.74/month
- RDS db.t3.small (operational): $29/month
- **Total: $31.74/month**

### After Phase 2 & 3 (Development Mode) - BYPASSED GLUE:
- S3 Storage: $2.74
- ~~Glue Crawler: $1~~ (Not used - local extraction)
- ~~Glue ETL (monthly runs): $13~~ (Not used - local extraction)
- RDS db.t3.small: $29
- **Total: $31.74/month** (Saved $14/month by using local extraction)

### Minimum Monthly Cost (Occasional Use):
- S3 Storage: $3
- Glue: $1
- Glue ETL (monthly): $13
- RDS db.t3.small: $29
- EC2 t3.small (40 hrs/month): $5
- SageMaker (40 hrs/month): $2
- **Total: ~$53/month**

### Standard Monthly Cost (Regular Development):
- S3 Storage: $3
- Glue Crawler: $1
- Glue ETL (monthly): $13
- RDS db.t3.medium: $60
- EC2 t3.small (100 hrs/month): $12
- SageMaker ml.t3.medium (100 hrs/month): $6
- SageMaker Training: $15
- CloudWatch: $3
- **Total: ~$113/month**

### Maximum Monthly Cost (Heavy Production Use):
- S3 Storage (with outputs): $10
- Glue ETL (weekly): $53
- RDS db.t3.large (24/7): $100
- EC2 t3.small (24/7): $15
- SageMaker ml.t3.xlarge (200 hrs): $46
- SageMaker Training (heavy): $50
- Athena: $2
- CloudWatch: $5
- **Total: ~$281/month**

### Cost Growth Projection:
- **Month 1:** $2.74 (S3 only)
- **Month 2:** $46 (+ Glue + RDS)
- **Month 3:** $53 (+ EC2 + SageMaker occasional)
- **Month 4-6:** $113 (regular development)
- **Month 6+:** $113-281 (depends on usage intensity)

### Cost Optimization Tips:

1. Stop EC2/SageMaker instances when not in use (saves 70-90%)
2. Run Glue ETL monthly instead of weekly (saves $40/month)
3. Start with db.t3.small, upgrade only if needed (saves $31/month)
4. Use Spot instances for non-critical workloads (saves 70%)
5. Set up billing alarms at $50, $100, $150 thresholds
6. Review costs weekly in AWS Cost Explorer

## CRITICAL PATHS & FILE LOCATIONS

**Project:** `/Users/ryanranft/nba-simulator-aws`
**Original Data:** `/Users/ryanranft/0espn/data/nba/` (119 GB)
**S3 Bucket:** `s3://nba-sim-raw-data-lake` (146,115 files)
**Conda Env:** `nba-aws` at `/Users/ryanranft/miniconda3/envs/nba-aws`

**For complete file locations, commands, and environment setup, see:** `QUICKSTART.md`
**For environment variables template, see:** `.env.example`

---

## 🔧 CONFIGURATION DETAILS

### AWS Configuration

- **Account ID:** <your-aws-account-id>
- **IAM User:** iam
- **Region:** us-east-1
- **Permissions:** AdministratorAccess

### Local Environment

- **OS:** macOS (Darwin 24.6.0, ARM64)
- **Python:** 3.11 (via Conda)
- **AWS CLI:** 2.28.16
- **Project Path:** /Users/ryanranft/nba-simulator-aws
- **Data Source Path:** /Users/ryanranft/0espn/data/nba/

### Tools Used

- PyCharm IDE
- Conda package manager
- Git version control
- AWS CLI

---

**Last Updated:** Awaiting PyCharm project creation confirmation
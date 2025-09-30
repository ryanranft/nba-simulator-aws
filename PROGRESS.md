# NBA Game Simulator & ML Platform - Setup Progress Log

**Date Started:** September 29, 2025  
**Project Goal:** Configure NBA Game Simulator & ML Platform on AWS with proper local development environment

---

## EXECUTIVE SUMMARY

**Project Status:** Phase 1 Complete - S3 Data Lake Operational

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
- **Git:** Local repository initialized with first commit (GitHub push pending)
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

- GitHub push blocked (needs Personal Access Token, not password)
- PyCharm may be slow (data folder should be marked as "Excluded")

### IMPORTANT NOTES:

- AWS CLI is installed system-wide, NOT in conda environment
- Do not install awscli via pip (causes conflicts)
- Data folder MUST remain in .gitignore (too large for GitHub)

### Next Immediate Steps:

1. Set up AWS Glue Crawler to discover data schema
2. Create Glue ETL job to extract 10% of relevant fields
3. Provision RDS PostgreSQL database (adds ~$29/month)
4. Begin data transformation and loading

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

**Infrastructure:**
- Local development environment (Python 3.11, conda)
- AWS S3 raw data lake with 146,115 files (119 GB)
- Project directory structure
- Git repository (local)

**Configuration:**
- AWS CLI verified and configured
- IAM permissions confirmed (AdministratorAccess)
- Conda environment `nba-aws` created
- PyCharm project initialized

**Data:**
- All NBA data (1999-2025) uploaded to S3
- Local data copy maintained
- Backup strategy established

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
- GitHub push requires Personal Access Token setup
- Must complete Glue Crawler + RDS before ETL job can run

---

## ARCHITECTURE DECISION RECORDS (ADR)

**Purpose:** Document critical architectural and technical decisions made during project setup to provide context for future development and prevent revisiting settled questions.

### ADR-001: Redshift Exclusion for Initial Development

**Date:** September 29, 2025  
**Status:** Accepted  
**Decision Maker:** Project team based on cost-benefit analysis

**Context:** The original architecture plan (v4) included Amazon Redshift as a data warehouse for analytical queries and ML feature engineering. Redshift offers columnar storage, massive parallel processing, and is optimized for OLAP workloads.

**Decision:** Exclude Redshift from initial implementation. Use RDS PostgreSQL for both OLTP and OLAP workloads during development and learning phases.

**Rationale:**

1. **Cost Optimization:**
   - Redshift Serverless: $270-660/month with conservative usage (16-32 RPUs)
   - Redshift Provisioned: $180-783/month minimum
   - RDS PostgreSQL db.t3.medium: $35-71/month
   - Savings: $200-600/month during development

2. **Data Size:**
   - Extracted data: ~12 GB (after 10% field extraction)
   - RDS handles this size efficiently with acceptable query performance
   - Redshift benefits only materialize at 50+ GB with complex analytical queries

3. **Learning Objectives:**
   - Primary goal is learning AWS architecture, not production-scale analytics
   - RDS provides sufficient functionality to understand ETL patterns and database design
   - Redshift can be added later if/when needed

4. **Query Complexity:**
   - Initial use case: Simulation queries (single-game lookups) - RDS excels at this
   - Analytical queries: Occasional, not real-time - RDS acceptable performance
   - No concurrent analyst users requiring parallel query processing

**Consequences:**

- **Positive:** Lower monthly costs, simpler architecture, faster setup
- **Negative:** Slower analytical queries (2-5 sec vs 0.5-1 sec), limited to single-node processing
- **Mitigation:** Use AWS Athena ($5/TB scanned) for ad-hoc complex queries if RDS becomes bottleneck

**Migration Path:** If future requirements demand Redshift:

1. Keep RDS for OLTP (simulation queries)
2. Add Redshift Serverless for OLAP (analytics)
3. Use AWS Glue to replicate RDS data to Redshift nightly
4. Estimated migration time: 2-4 hours
5. Note: Adding Redshift later will increase monthly cost by $270-660

**Review Date:** After 3 months of usage or when analytical query latency exceeds 30 seconds

---

### ADR-002: 10% Data Extraction Strategy

**Date:** September 29, 2025  
**Status:** Accepted  
**Decision Maker:** User requirement based on use case analysis

**Context:** Raw ESPN JSON files contain extensive metadata, commentary, broadcast information, and historical context. Each file averages 800 KB with hundreds of fields. Total raw storage: 119 GB across 146,115 files.

**Decision:** Extract only ~10% of fields from each JSON file during ETL process. Load only essential simulation and analysis fields into RDS.

**Fields to Extract (by file type):**

**Box Scores:**
- **Player:** player_id, player_name, team_id, position
- **Stats:** minutes, points, rebounds, assists, steals, blocks, turnovers, FG/3PT/FT made/attempted
- **Exclude:** Player photos, biographical details, career stats, commentary

**Play-by-Play:**
- **Core:** game_id, period, clock, play_type, scoring_play (boolean)
- **Participants:** player_id, team_id
- **Score:** home_score, away_score
- **Exclude:** Play descriptions/text, coordinate data, video links, detailed shot charts

**Schedule:**
- **Game:** game_id, game_date, home_team_id, away_team_id, home_score, away_score
- **Venue:** venue_name, attendance (optional)
- **Exclude:** Broadcast details, ticket links, weather, odds, pre-game analysis

**Team Stats:**
- **Aggregate:** team_id, game_id, points, rebounds, assists, turnovers, FG%
- **Exclude:** Historical comparisons, season narratives, coaching details

**Note:** Exact JSON field paths to be documented after examining sample files in next session.

**Rationale:**

1. **Storage Efficiency:**
   - Raw: 119 GB → Extracted: ~12 GB (90% reduction)
   - RDS storage cost: $11.50/month → $2-3/month
   - Faster queries due to smaller table sizes

2. **Processing Efficiency:**
   - Glue ETL processes only relevant fields (reduced compute time/cost)
   - Simulations query only necessary data (faster performance)
   - Reduced data transfer costs between S3 and RDS

3. **Use Case Alignment:**
   - Simulation engine needs: Game outcomes, player stats, play sequences
   - ML features need: Statistical aggregates, temporal patterns, player performance
   - Neither needs: Commentary, images, broadcast metadata, narrative text

4. **Maintainability:**
   - Smaller database easier to backup, restore, and version
   - Schema changes impact fewer fields
   - Debugging and data quality checks faster

**Consequences:**

- **Positive:** 90% storage savings, faster queries, lower costs, cleaner schema
- **Negative:** Must re-process S3 data if additional fields needed later
- **Mitigation:** Raw data preserved in S3, can always extract more fields via new Glue job

**Data Retention:**
- **Raw JSON files:** Permanent storage in S3 (source of truth)
- **Extracted data:** In RDS, can be regenerated from S3 anytime
- **Cost:** S3 storage ($2.74/month) provides complete historical archive

**Review Date:** After initial ETL job completion, verify 10% extraction meets all simulation and ML requirements

---

### ADR-003: Python 3.11 for Development Environment

**Date:** September 29, 2025  
**Status:** Accepted  
**Decision Maker:** Technical constraint (AWS Glue compatibility)

**Context:** Need to select Python version for local development, AWS Glue ETL jobs, and data processing. Options: Python 3.9, 3.10, 3.11, 3.12, 3.13.

**Decision:** Use Python 3.11.13 for all project components.

**Rationale:**

1. **AWS Glue Compatibility:**
   - AWS Glue 4.0 (latest): Supports Python 3.10 and 3.11 only
   - Python 3.12+ not yet supported by Glue as of September 2025
   - Using 3.11 ensures local development matches Glue environment exactly

2. **Library Compatibility:**
   - All required packages available for 3.11: boto3, pandas 2.0.3, numpy 1.24.3, psycopg2, sqlalchemy
   - Python 3.12+ introduced changes that broke some packages (e.g., setuptools, distutils)
   - Python 3.11 has mature, stable package ecosystem

3. **Performance:**
   - Python 3.11 introduced significant performance improvements (10-60% faster than Python 3.9)
   - Benefits ETL processing of 146K files
   - Stable and battle-tested (released October 2022)

4. **Future-Proofing:**
   - AWS typically adds new Python version support 6-12 months after release
   - Python 3.11 will be supported for years to come
   - Easy upgrade path to 3.12+ when Glue adds support

**Environment Setup:**
- **Conda environment:** nba-aws with Python 3.11.13
- **Isolated from system Python and other projects**
- **Matches AWS Glue 4.0 runtime exactly for development/testing parity**

**Consequences:**

- **Positive:** Maximum compatibility, stable libraries, good performance, matches AWS Glue
- **Negative:** Cannot use Python 3.12+ features (not a concern for this project)
- **Risk:** None - AWS Glue 4.0 will support 3.11 for minimum 2-3 years

**Alternative Considered:**
- **Python 3.10:** Also Glue-compatible but slower, missing 3.11 performance improvements
- **Python 3.12:** Not Glue-compatible, would require version switching between local and AWS

**Review Date:** When AWS Glue announces Python 3.12+ support (likely 2026)

---

### ADR-004: Git Without GitHub Push (Deferred)

**Date:** September 29, 2025  
**Status:** Deferred  
**Decision:** Initialize Git locally, defer GitHub remote push

**Context:** GitHub authentication now requires Personal Access Token (PAT), not password. Setting up PAT requires additional steps outside core project setup.

**Decision:**
- Initialize Git repository locally ✅
- Make initial commit with core files ✅
- Defer GitHub push to future session
- Document that GitHub integration is pending

**Rationale:**
- Local Git provides version control benefits immediately
- GitHub push is non-blocking for AWS development
- Avoids session delay for PAT setup
- User can complete GitHub setup independently

**Consequences:**
- **Positive:** Project progresses without auth delays, local version control active
- **Negative:** No remote backup until GitHub connected
- **Mitigation:** Local Git prevents data loss, S3 contains data backup

**Completion Steps (For Future):**
1. Create GitHub Personal Access Token at github.com/settings/tokens
2. Use token as password: `git push -u origin main`
3. Or configure credential helper: `git config credential.helper store`

---

**Summary of Decisions:** These ADRs optimize for cost-efficiency during learning phase while maintaining flexibility to scale up production capabilities later. Total estimated savings: $600-8,000/month vs. original full-scale architecture.

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

**GitHub Integration (ADR-004)**
- **Status:** Deferred
- **Action Required:** Create Personal Access Token at github.com/settings/tokens
- **Blocking:** Remote backup, but not blocking AWS development
- **Priority:** Low

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

#### Component 2.1: AWS Glue Crawler

**Status:** ⏸️ Not Started  
**Purpose:** Automatically discover and catalog the schema of JSON files in S3

**Configuration Steps:**

1. Create AWS Glue Data Catalog database
2. Create IAM role for Glue with S3 read permissions
3. Configure Glue Crawler to scan S3 bucket folders
4. Run crawler to generate schema tables
5. Review and validate discovered schemas

**Prerequisites:**
- S3 bucket with data: ✅ COMPLETE
- IAM permissions: AdministratorAccess ✅

**Estimated Time:** 30-45 minutes
- Setup via console: 15 minutes
- First crawler run: 10-15 minutes (scanning 146,115 files)
- Schema review: 10 minutes

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

**Status:** ⏸️ Not Started  
**Purpose:** Relational database for simulation queries and analytics (OLTP + OLAP)

**Configuration Steps:**

1. Create SQL schema files locally (1 hour)
2. Launch RDS PostgreSQL instance via AWS Console (20 min)
3. Configure security group rules (15 min)
4. Test connection from local machine (10 min)
5. Run SQL scripts to create tables (15 min)
6. Create indexes for performance (15 min)
7. Configure automated backups (5 min)
8. Document connection details (5 min)

**Prerequisites:**
- VPC configuration: Use default VPC ✅
- SQL schema design: Need to create
- psql client installed locally: Check with `psql --version`

**Estimated Time:** 2-3 hours
- SQL script creation: 1 hour
- RDS instance creation: 20 minutes (AWS provisioning time)
- Security configuration: 30 minutes
- Testing and validation: 30 minutes
- Documentation: 30 minutes

**Estimated Cost:** ~$29-60/month (depending on instance size)

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

### Current Actual Cost:
- S3 Storage (raw data): $2.74/month
- **Total: $2.74/month**

### After Phase 2 & 3 (Development Mode):
- S3 Storage: $2.74
- Glue Crawler: $1
- Glue ETL (monthly runs): $13
- RDS db.t3.small: $29
- **Total: $45.74/month**

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

---

## FILE PATHS REFERENCE

**Purpose:** Complete directory structure and file location reference for quick navigation and troubleshooting.

### Local Development Environment

#### Project Root:

```
/Users/ryanranft/nba-simulator-aws/
```

#### Directory Structure:

```
/Users/ryanranft/nba-simulator-aws/
├── .git/                           # Git repository metadata
├── .gitignore                      # Git ignore rules (excludes data/)
├── .idea/                          # PyCharm IDE configuration (100-500 MB cache)
│   └── nba-simulator-aws.iml      # Module config (data folder excluded)
├── README.md                       # Project documentation
├── requirements.txt                # Python dependencies (boto3, pandas, etc.)
├── .env                            # Environment variables (⚠️ NOT IN GIT)
├── config/
│   └── aws_config.yaml            # AWS configuration (placeholder)
├── data/                           # Local NBA data (119 GB, EXCLUDED from Git)
│   ├── nba_box_score/             # 44,828 box score JSON files
│   ├── nba_pbp/                   # 44,826 play-by-play JSON files
│   ├── nba_schedule_json/         # 11,633 schedule JSON files
│   └── nba_team_stats/            # 44,828 team stats JSON files
├── docs/                           # Documentation files
├── notebooks/                      # Jupyter notebooks (for analysis)
├── scripts/                        # Python scripts
│   ├── aws/                       # AWS infrastructure scripts
│   ├── etl/                       # ETL processing scripts
│   │   ├── glue_etl_job.py       # Main Glue ETL script (⏸️ TO BE CREATED)
│   │   ├── field_mapping.yaml    # JSON field extraction map (⏸️ TO BE CREATED)
│   │   └── test_output/          # ETL test outputs (⏸️ TO BE CREATED)
│   └── simulation/                # Simulation engine scripts
├── sql/                            # Database schema files
│   ├── create_tables.sql          # Table definitions (⏸️ TO BE CREATED)
│   ├── create_indexes.sql         # Performance indexes (⏸️ TO BE CREATED)
│   └── create_foreign_keys.sql    # FK constraints (⏸️ TO BE CREATED)
└── logs/                           # Application logs (⏸️ TO BE CREATED)
```

#### Local Disk Space Requirements:

- Project files: ~500 MB
- Local data copy: 119 GB
- Git repository: ~50 MB
- PyCharm cache: ~100-500 MB (if not excluded)
- Python packages: ~200 MB
- **Minimum required:** 130 GB free disk space

#### Important Local Files:

- Configuration: `/Users/ryanranft/nba-simulator-aws/requirements.txt`
- Git ignore: `/Users/ryanranft/nba-simulator-aws/.gitignore`
- Project docs: `/Users/ryanranft/nba-simulator-aws/README.md`
- Temp samples: `/Users/ryanranft/nba-simulator-aws/sample_*.json`

---

### Original Data Source

#### Source Directory:

```
/Users/ryanranft/0espn/data/nba/
├── nba_box_score/       # Original box score files (44,828 files)
├── nba_pbp/             # Original play-by-play files (44,826 files)
├── nba_schedule_json/   # Original schedule files (11,633 files)
└── nba_team_stats/      # Original team stats files (44,828 files)
```

#### Data Specifications:

- **Total Files:** 146,115 JSON files
- **Total Size:** ~119 GB
- **Time Period:** NBA games 1999-2025
- **File Format:** JSON, UTF-8 encoded
- **Naming Convention:** Game IDs (numeric) and dates (YYYYMMDD)
- **Purpose:** Source of truth, preserved for reference
- **Status:** ✅ Complete, backed up to S3

#### Sample Files:

- Box score: `/Users/ryanranft/0espn/data/nba/nba_box_score/131105001.json`
- Play-by-play: `/Users/ryanranft/0espn/data/nba/nba_pbp/131105001.json`
- Schedule: `/Users/ryanranft/0espn/data/nba/nba_schedule_json/19930825.json`
- Team stats: `/Users/ryanranft/0espn/data/nba/nba_team_stats/131105001.json`

---

### AWS S3 Storage

#### Primary S3 Bucket:

```
s3://nba-sim-raw-data-lake/
```

#### S3 Folder Structure:

```
s3://nba-sim-raw-data-lake/
├── box_scores/          # 44,828 files (mapped from nba_box_score/)
├── pbp/                 # 44,826 files (mapped from nba_pbp/)
├── schedule/            # 11,633 files (mapped from nba_schedule_json/)
└── team_stats/          # 44,828 files (mapped from nba_team_stats/)
```

#### S3 Details:

- **Region:** us-east-1 (US East - N. Virginia)
- **Storage Class:** STANDARD
- **Total Objects:** 146,115
- **Total Size:** 119,098,344,984 bytes (119 GB)
- **Monthly Cost:** ~$2.74
- **Upload Date:** September 29-30, 2025

#### Access S3:

```bash
# List bucket contents
aws s3 ls s3://nba-sim-raw-data-lake/

# List specific folder
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/

# Download sample file
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json ./sample.json

# Get bucket summary
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize
```

#### S3 Analytics Bucket (⏸️ TO BE CREATED):

```
s3://nba-sim-analytics-lake/
├── simulation_results/              # Parquet files from simulations
└── ml_training_data/                # Prepared ML datasets
```

---

### AWS Glue (⏸️ TO BE CREATED)

#### Glue Database:

- **Database name:** nba_raw_data
- **Purpose:** Data Catalog for S3 JSON files
- **Status:** ⏸️ Not yet created

#### Glue Tables (⏸️ TO BE CREATED):

- `nba_raw_data.box_scores` → points to `s3://nba-sim-raw-data-lake/box_scores/`
- `nba_raw_data.pbp` → points to `s3://nba-sim-raw-data-lake/pbp/`
- `nba_raw_data.schedule` → points to `s3://nba-sim-raw-data-lake/schedule/`
- `nba_raw_data.team_stats` → points to `s3://nba-sim-raw-data-lake/team_stats/`

#### Glue ETL Job Script:

- **Local:** `/Users/ryanranft/nba-simulator-aws/scripts/etl/glue_etl_job.py`
- **AWS:** To be uploaded to S3 when job is created

---

### AWS RDS (⏸️ TO BE CREATED)

#### RDS Endpoint (example format):

- **Host:** `nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com`
- **Port:** 5432
- **Database:** nba_simulator
- **Username:** postgres
- **Password:** [Secure password to be created]

#### Connection String Template:

```
postgresql://postgres[REDACTED]@nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com:5432/nba_simulator
```

#### Database Tables (⏸️ TO BE CREATED):

- `public.teams` - Team master data
- `public.players` - Player master data
- `public.games` - Game master data
- `public.player_game_stats` - Box score statistics
- `public.plays` - Play-by-play events
- `public.play_participants` - Player participation in plays

---

### AWS EC2 (⏸️ TO BE CREATED)

#### EC2 Instance (example format):

- **Instance ID:** i-xxxxxxxxx (to be created)
- **Public IP:** ec2-xx-xx-xx-xx.compute-1.amazonaws.com
- **Instance Type:** t3.small
- **AMI:** Amazon Linux 2023
- **SSH Key:** your-key.pem

#### EC2 Connection Template:

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@ec2-xx-xx-xx-xx.compute-1.amazonaws.com
```

#### EC2 File Locations (⏸️ TO BE CREATED):

```
/home/ec2-user/
├── simulation_code/     # Simulation engine code
├── .env                 # Environment variables (DB credentials)
└── logs/                # Simulation logs
```

---

### AWS SageMaker (⏸️ TO BE CREATED)

#### SageMaker Notebook:

- **Name:** nba-ml-notebook
- **Instance Type:** ml.t3.medium
- **Status:** ⏸️ To be created

#### SageMaker Model Artifacts (⏸️ TO BE CREATED):

```
s3://sagemaker-us-east-1-[ACCOUNT]/nba-models/
└── [model-name]/
    ├── model.tar.gz                 # Trained model
    └── training_metrics.json        # Performance metrics
```

---

### AWS Resource ARNs (⏸️ TO BE CREATED)

#### ARN Format Examples:

- **S3 Bucket:** `arn:aws:s3:::nba-sim-raw-data-lake`
- **RDS Instance:** `arn:aws:rds:us-east-1:[ACCOUNT]:db:nba-sim-db`
- **Glue Database:** `arn:aws:glue:us-east-1:[ACCOUNT]:database/nba_raw_data`
- **Glue Crawler:** `arn:aws:glue:us-east-1:[ACCOUNT]:crawler/nba-data-crawler`
- **EC2 Instance:** `arn:aws:ec2:us-east-1:[ACCOUNT]:instance/i-xxxxxxxxx`
- **SageMaker Notebook:** `arn:aws:sagemaker:us-east-1:[ACCOUNT]:notebook-instance/nba-ml-notebook`

**Note:** `[ACCOUNT]` placeholder represents your AWS account ID

---

### Conda Environment

#### Environment Location:

```
/Users/ryanranft/miniconda3/envs/nba-aws/
```

#### Python Executable:

```
/Users/ryanranft/miniconda3/envs/nba-aws/bin/python
```

#### Python Packages Location:

```
/Users/ryanranft/miniconda3/envs/nba-aws/lib/python3.11/site-packages/
```

#### Activate Environment:

```bash
conda activate nba-aws
```

#### Environment Details:

- **Python Version:** 3.11.13
- **Packages:** boto3, pandas, numpy, psycopg2-binary, sqlalchemy, etc.
- **Location:** Isolated from other conda environments
- **Size:** ~200 MB

---

### System Tools

#### AWS CLI:

- **Location:** `/usr/local/bin/aws` (system-wide, NOT in conda)
- **Version:** 2.28.16
- **Configuration:** `~/.aws/config` and `~/.aws/credentials`
- **Region:** us-east-1

#### AWS Configuration Files:

- `~/.aws/config` - AWS CLI configuration (region, output format)
- `~/.aws/credentials` - AWS access keys (⚠️ SENSITIVE - DO NOT COMMIT)

#### Git Repository:

- **Remote:** https://github.com/ryanranft/nba-simulator-aws.git
- **Branch:** main
- **Status:** Local commits made, GitHub push pending (needs PAT)

---

### Log File Locations

#### System Logs:

- `~/.aws/cli/cache/` - AWS CLI cache and logs
- `~/Library/Logs/JetBrains/PyCharm*/` - PyCharm IDE logs

#### Application Logs (⏸️ TO BE CREATED):

```
/Users/ryanranft/nba-simulator-aws/logs/
├── etl.log              # Glue ETL job logs
├── simulation.log       # Simulation engine logs
└── error.log            # Error tracking
```

---

### Environment Variables (⏸️ TO BE CREATED)

#### Local Development (.env file):

```bash
# File: /Users/ryanranft/nba-simulator-aws/.env
# ⚠️ CRITICAL: DO NOT COMMIT TO GIT (already protected by .gitignore)
# ⚠️ CRITICAL: Never run 'git add .env' - verify before any git add commands

# AWS
AWS_REGION=us-east-1
# Note: AWS Account ID can be found via: aws sts get-caller-identity

# S3
S3_BUCKET=nba-sim-raw-data-lake
S3_ANALYTICS_BUCKET=nba-sim-analytics-lake  # ⏸️ TO BE CREATED

# RDS (⏸️ TO BE CREATED)
DB_HOST=nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=nba_simulator
DB_USER=postgres
DB_PASSWORD=your_secure_password_here  # ⚠️ SENSITIVE

# Glue (⏸️ TO BE CREATED)
GLUE_DATABASE=nba_raw_data
GLUE_ETL_JOB=nba-etl-job
```

---

### Quick Navigation Commands

#### Navigate to Project:

```bash
cd /Users/ryanranft/nba-simulator-aws
```

#### View Local Data:

```bash
ls -lh data/nba_box_score/ | head -10
```

#### Access Original Data:

```bash
cd /Users/ryanranft/0espn/data/nba/
```

#### View S3 Data:

```bash
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ | head -10
```

#### Connect to RDS (When Created):

```bash
psql -h nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com -U postgres -d nba_simulator
```

#### SSH to EC2 (When Created):

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@ec2-xx-xx-xx-xx.compute-1.amazonaws.com
```

---

### File Size Reference

#### Local Data Sizes:

```
data/nba_box_score/      ~33 GB (44,828 files)
data/nba_pbp/            ~40 GB (44,826 files)
data/nba_schedule_json/  ~9 GB  (11,633 files)
data/nba_team_stats/     ~31 GB (44,828 files)
Total:                   ~119 GB (146,115 files)
```

#### Expected RDS Data Sizes (After 10% Extraction):

```
Estimated total:         ~12 GB (90% reduction from raw data)
teams table:             <1 MB
players table:           ~5 MB
games table:             ~10 MB
player_game_stats:       ~8 GB
plays:                   ~4 GB (from 40 GB pbp data)
play_participants:       ~1 GB
```

---

### Verify All Paths Exist

#### Path Verification Commands:

```bash
# Check project directory
test -d /Users/ryanranft/nba-simulator-aws && echo "✅ Project exists" || echo "❌ Project missing"

# Check conda environment  
conda env list | grep nba-aws && echo "✅ Conda env exists" || echo "❌ Conda env missing"

# Check S3 bucket
aws s3 ls s3://nba-sim-raw-data-lake/ &>/dev/null && echo "✅ S3 bucket exists" || echo "❌ S3 bucket missing"

# Check data folders
test -d /Users/ryanranft/nba-simulator-aws/data/nba_box_score && echo "✅ Data copied" || echo "❌ Data missing"

# Check original data source
test -d /Users/ryanranft/0espn/data/nba && echo "✅ Original data exists" || echo "❌ Original data missing"

# Check AWS CLI
which aws &>/dev/null && echo "✅ AWS CLI installed" || echo "❌ AWS CLI missing"

# Check Python environment
conda activate nba-aws && python --version | grep "3.11" && echo "✅ Python 3.11 active" || echo "❌ Wrong Python version"
```

---

### Backup & Recovery Paths

#### Git Backup:

- **Local:** `/Users/ryanranft/nba-simulator-aws/.git/`
- **Remote:** https://github.com/ryanranft/nba-simulator-aws.git (⏸️ push pending)

#### Data Backup:

- **Original:** `/Users/ryanranft/0espn/data/nba/` (preserved)
- **S3 Copy:** `s3://nba-sim-raw-data-lake/` (permanent backup)
- **Local Copy:** `/Users/ryanranft/nba-simulator-aws/data/` (working copy)

#### RDS Backup (⏸️ When Created):

- **Automated snapshots:** 7-day retention
- **Manual snapshots:** User-initiated
- **Location:** AWS RDS Snapshots (us-east-1)

---

### Critical Path Summary

#### Must Exist (✅ Complete):

- ✅ `/Users/ryanranft/nba-simulator-aws/` - Project directory
- ✅ `/Users/ryanranft/miniconda3/envs/nba-aws/` - Conda environment
- ✅ `s3://nba-sim-raw-data-lake/` - S3 raw data
- ✅ `/usr/local/bin/aws` - AWS CLI
- ✅ `/Users/ryanranft/nba-simulator-aws/data/` - Local data copy
- ✅ `/Users/ryanranft/nba-simulator-aws/requirements.txt` - Dependencies

#### Must Create (⏸️ Pending):

- ⏸️ `nba_raw_data` - Glue database
- ⏸️ `nba-sim-db` - RDS instance
- ⏸️ `/Users/ryanranft/nba-simulator-aws/sql/create_tables.sql` - SQL schemas
- ⏸️ `/Users/ryanranft/nba-simulator-aws/scripts/etl/glue_etl_job.py` - ETL script
- ⏸️ `/Users/ryanranft/nba-simulator-aws/.env` - Environment variables
- ⏸️ `s3://nba-sim-analytics-lake/` - Analytics bucket

## 💡 IMPORTANT PROJECT INSIGHT - Data Optimization

**User Note:** The JSON files contain much more data than needed for the database. Only ~10% of each file's content needs to be extracted and loaded into RDS. This means:

### Storage Implications:

- **Raw data in S3:** ~50,000+ JSON files (full data)
- **Processed data in RDS:** Only 10% of relevant fields extracted
- **This significantly reduces:**
  - RDS storage requirements (likely <10 GB instead of 100 GB)
  - Data transfer costs
  - Query performance (smaller tables)
  - Overall AWS costs

### ETL Process:

The AWS Glue ETL job will:

1. Read full JSON files from S3
2. Extract only the 10% of fields needed for simulations/ML
3. Transform and clean the data
4. Load only the essential data into RDS

### Cost Impact:

- RDS storage: $11.50/month → ~$2-3/month (90% reduction)
- Faster queries due to smaller dataset
- Lower compute costs for processing

This optimization should be built into the Glue ETL script design.

---

## 🔧 CONFIGURATION DETAILS

### AWS Configuration

- **Account ID:** ************
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
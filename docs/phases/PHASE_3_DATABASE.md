# Phase 3: Database Infrastructure (RDS PostgreSQL)

**Status:** ✅ COMPLETE
**Prerequisites:** Phase 1 complete (S3 data lake operational)
**Estimated Time:** 2-3 hours
**Estimated Cost:** $29/month
**Started:** October 1, 2025 19:13 EST
**Completed:** October 1, 2025 20:50 EST
**Total Time:** 1 hour 37 minutes

---

## Overview

Set up AWS RDS PostgreSQL database as the relational data store for NBA game simulations and analytics. This phase creates the database schema, indexes, and connections needed to support both OLTP (simulation queries) and OLAP (analytics) workloads.

**This phase includes:**
- RDS PostgreSQL instance provisioning
- Database schema creation (6 tables)
- Performance indexes creation (33 indexes)
- Security group configuration
- Connection verification

---

## Prerequisites

Before starting this phase:
- [x] AWS account with RDS permissions
- [x] SQL schema designed (see `sql/create_tables.sql`)
- [x] psql client installed locally
- [x] VPC configured (used default VPC)

**See workflow #32 (RDS Connection) for connection procedures.**

---

## Implementation Steps

### Sub-Phase 3.1: SQL Schema Design

**Status:** ✅ COMPLETE
**Time Estimate:** 1 hour
**Actual Time:** 30 minutes

**Follow these workflows:**
- Workflow #3 ([Decision Workflow](../claude_workflows/workflow_descriptions/03_decision_workflow.md))
  - **When to run:** When making schema design decisions (58 columns, index strategy, foreign keys)
  - **Purpose:** Document schema architecture decisions as ADRs

- Workflow #6 ([File Creation](../claude_workflows/workflow_descriptions/06_file_creation.md))
  - **When to run:** When creating SQL files (`create_tables.sql`, `create_indexes.sql`)
  - **Purpose:** Follow file creation best practices for SQL scripts, ensure proper structure and documentation

- Workflow #25 ([Database Migration](../claude_workflows/workflow_descriptions/25_database_migration.md))
  - **When to run:** Before writing SQL scripts
  - **Purpose:** Follow database migration best practices, plan rollback procedures

- Workflow #29 ([Style Enforcement](../claude_workflows/workflow_descriptions/29_style_enforcement.md))
  - **When to run:** After writing SQL scripts
  - **Purpose:** Ensure SQL follows naming conventions, formatting standards

**Completed tasks:**
1. ✅ Created `sql/create_tables.sql` (6 tables)
2. ✅ Created `sql/create_indexes.sql` (33 indexes)
3. ✅ Designed foreign key relationships
4. ✅ Planned for 120K+ games, 5K+ players, 15M+ plays

**Tables created:**
- `teams` (87 rows) - NBA team metadata
- `players` (5,000+ rows) - Player information
- `games` (44,828 rows with 58 columns) - Game metadata and scores
- `player_game_stats` (408,833 rows) - Player box scores
- `team_game_stats` (15,900 rows) - Team statistics
- `plays` / `play_by_play` (6,781,155 rows) - Play-by-play data

**Validation:**
- [x] Schema supports all simulation queries
- [x] Indexes cover common query patterns
- [x] Foreign keys enforce referential integrity

---

### Sub-Phase 3.2: RDS Instance Provisioning

**Status:** ✅ COMPLETE
**Time Estimate:** 30 minutes
**Actual Time:** 25 minutes (includes one retry)

**Follow these workflows:**
- Workflow #34 ([Lessons Learned Review](../claude_workflows/workflow_descriptions/34_lessons_learned_review.md))
  - **When to run:** BEFORE creating RDS instance
  - **Purpose:** Read LESSONS_LEARNED.md Issues #2-7 to avoid known RDS configuration problems
  - **Key lessons:** PostgreSQL 15.14 (not 16), password character restrictions, security group setup

- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
  - **When to run:** BEFORE creating RDS instance
  - **Purpose:** Estimate monthly costs (~$29/month for db.t3.small), get user approval

- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
  - **When to run:** When creating RDS instance
  - **Purpose:** Follow best practices for RDS provisioning (encryption, backups, Multi-AZ evaluation)

- Workflow #28 ([ADR Creation](../claude_workflows/workflow_descriptions/28_adr_creation.md))
  - **When to run:** After making RDS configuration decisions (db.t3.small vs micro, Single-AZ vs Multi-AZ, PostgreSQL 15.14)
  - **Purpose:** Document infrastructure decisions as ADRs

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After running AWS CLI commands to create RDS instance
  - **Purpose:** Log RDS creation commands to COMMAND_LOG.md for reproducibility

**Configuration attempts:**
1. ❌ First attempt: db.t3.micro (deleted during account upgrade)
2. ✅ Second attempt: db.t3.small (successful)

**Final configuration:**
- **Instance ID:** `nba-sim-db`
- **Class:** db.t3.small (2 vCPUs, 2 GB RAM)
- **Engine:** PostgreSQL 15.14
- **Storage:** 20 GB GP3 SSD
- **Multi-AZ:** No (cost savings)
- **Backup retention:** 7 days (automated)
- **Public accessibility:** Yes (for development)
- **Endpoint:** `nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com`

**Lessons learned (from workflow #34):**
- PostgreSQL 16 not available for db.t3.* in us-east-1 (use 15.14)
- Avoid special characters in passwords: `/`, `@`, `"`, spaces
- Security group must allow port 5432 from your IP

**Validation:**
- [x] Instance status: Available
- [x] Endpoint accessible
- [x] 7-day automated backups configured

---

### Sub-Phase 3.3: Security Group Configuration

**Status:** ✅ COMPLETE
**Time Estimate:** 15 minutes
**Actual Time:** 10 minutes

**Follow these workflows:**
- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
  - **When to run:** When creating security group
  - **Purpose:** Configure security group with proper rules (port 5432, specific IP, not 0.0.0.0/0)

- Workflow #23 ([Credential Rotation](../claude_workflows/workflow_descriptions/23_credential_rotation.md))
  - **When to run:** After security group creation
  - **Purpose:** Document current IP address, schedule IP rotation updates when home IP changes

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After creating security group and rules
  - **Purpose:** Log security group commands for documentation

**Completed tasks:**
1. ✅ Created security group: `nba-rds-sg`
2. ✅ Added inbound rule: PostgreSQL (TCP 5432) from home IP
3. ✅ Documented IP address for rotation tracking

**Security group rules:**
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: <HOME_IP>/32 (your specific IP)
```

**Best practices applied:**
- Specific IP (not 0.0.0.0/0)
- Port 5432 for PostgreSQL
- Documented in `docs/RDS_CONNECTION.md`
- IP rotation scheduled (see workflow #23)

**Validation:**
- [x] Security group attached to RDS instance
- [x] Port 5432 accessible from home IP
- [x] Connection test successful

---

### Sub-Phase 3.4: Database Schema Creation

**Status:** ✅ COMPLETE
**Time Estimate:** 30 minutes
**Actual Time:** 7 minutes

**Follow these workflows:**
- Workflow #32 ([RDS Connection](../claude_workflows/workflow_descriptions/32_rds_connection.md))
  - **When to run:** Before connecting to RDS for first time
  - **Purpose:** Verify connection methods (psql, Python), troubleshoot connection issues

- Workflow #25 ([Database Migration](../claude_workflows/workflow_descriptions/25_database_migration.md))
  - **When to run:** When executing SQL scripts on RDS
  - **Purpose:** Apply migrations safely, verify objects created, plan rollback if needed

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After executing SQL scripts
  - **Purpose:** Log SQL execution commands and results

- Workflow #21 ([Data Validation](../claude_workflows/workflow_descriptions/21_data_validation.md))
  - **When to run:** After creating tables and indexes
  - **Purpose:** Validate schema creation, verify all objects exist, test basic queries

**Completed tasks:**
1. ✅ Connected via psql client
2. ✅ Executed `sql/create_tables.sql` (6 tables)
3. ✅ Executed `sql/create_indexes.sql` (33 indexes)
4. ✅ Verified all objects created

**Connection command:**
```bash
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d nba_simulator
```

**Objects created:**
- 6 tables
- 33 indexes (23 performance + 10 constraints)
- Foreign key relationships

**Verification queries:**
```sql
-- List tables
\dt

-- List indexes
\di

-- Check PostgreSQL version
SELECT version();
-- Result: PostgreSQL 15.14

-- Verify table structure
\d games
```

**Validation:**
- [x] All 6 tables exist
- [x] All 33 indexes created
- [x] Foreign keys enforced
- [x] Test queries execute < 1 second

---

## Schema Enhancement (Phase 2 Integration)

**Status:** ✅ COMPLETE (Enhanced during Phase 2)

During Phase 2 overnight extraction, the schema was enhanced:
- ✅ Added 25 new columns to `games` table (total: 58 columns)
- ✅ Populated with 46,595 games (1993-2025)
- ✅ Loaded 6.7M plays to `play_by_play` table
- ✅ Loaded 408K player stats to `player_game_stats` table

**Final database state:**
| Table | Rows | Columns | Notes |
|-------|------|---------|-------|
| `teams` | 87 | 8 | NBA team metadata |
| `players` | ~5,000 | 10+ | Player information |
| `games` | 44,828 | 58 | Enhanced with full metadata |
| `player_game_stats` | 408,833 | 25+ | Individual player box scores |
| `team_game_stats` | 15,900 | 30+ | Team statistics |
| `play_by_play` | 6,781,155 | 13 | Play-by-play actions |

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| RDS Instance | db.t3.small | $24.82 | 2 vCPUs, 2 GB RAM |
| GP3 Storage | 20 GB | $2.30 | SSD storage |
| Backup Storage | 20 GB (7 days) | $1.80 | Automated backups |
| **Total Phase Cost** | | **$28.92/month** | ~$29/month |

**Future scaling options:**
- db.t3.medium (4 GB RAM): ~$60/month (for production)
- db.t3.large (8 GB RAM): ~$120/month (for high concurrency)

**Upgrade path:** 5 minutes downtime to resize instance class

---

## Troubleshooting

**Common issues encountered:**

1. **PostgreSQL 16 not available**
   - Error: `InvalidParameterCombination: RDS does not support... EngineVersion=16.4`
   - Solution: Use PostgreSQL 15.14 instead
   - See `docs/LESSONS_LEARNED.md` Issue #4

2. **Password rejected**
   - Error: `InvalidParameterValue: The parameter MasterUserPassword is not a valid password`
   - Solution: Avoid `/`, `@`, `"`, spaces in password
   - See `docs/LESSONS_LEARNED.md` Issue #2

3. **Connection refused**
   - Error: `could not connect to server`
   - Solution: Security group must allow port 5432 from your IP
   - See `docs/LESSONS_LEARNED.md` Issue #7

4. **Free Tier not applicable**
   - db.t3.small not Free Tier eligible
   - Only db.t3.micro and db.t2.micro are free
   - See `docs/LESSONS_LEARNED.md` Issue #3

---

## Success Criteria

All criteria met:
- [x] RDS instance status: Available
- [x] Connection successful from local machine
- [x] All 6 tables created
- [x] All 33 indexes created
- [x] Foreign keys enforced
- [x] Test queries execute < 1 second
- [x] Cost within budget ($29/month < $35/month target)
- [x] 7-day automated backups enabled
- [x] Security group configured correctly
- [x] Data loaded successfully (Phase 2 integration)

---

## Key Decisions

**Configuration decisions made:**
- db.t3.small over db.t3.micro (better performance)
- PostgreSQL 15.14 (vs 16 - not available)
- 20 GB storage (adequate for 6.7M plays + indexes)
- Single-AZ deployment (save ~$30/month vs Multi-AZ)
- Public accessibility for development (restrict in production)

**See `docs/adr/README.md` for architecture decisions.**

---

## Next Steps

After completing this phase:
1. ✅ Update PROGRESS.md status (marked complete Oct 1, 2025)
2. ✅ Data loaded via Phase 2 local extraction (Oct 2, 2025)
3. ✅ Follow Workflow #14 ([Session End](../claude_workflows/workflow_descriptions/14_session_end.md)) to properly end session and prepare for Phase 4
4. ⏸️ Proceed to [Phase 4: Simulation Engine](PHASE_4_SIMULATION_ENGINE.md)

**Phase 3 successfully completed. Database operational with 6.7M plays loaded.**

---

## Connection Reference

**For future connections, see `docs/RDS_CONNECTION.md`**

**Quick connection methods:**

1. **psql (command line):**
```bash
psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d nba_simulator
```

2. **Python (psycopg2):**
```python
import psycopg2
conn = psycopg2.connect(
    host="nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com",
    database="nba_simulator",
    user="postgres",
    password="<password>"
)
```

3. **SQLAlchemy:**
```python
from sqlalchemy import create_engine
engine = create_engine(
    "postgresql://postgres:<password>@nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com:5432/nba_simulator"
)
```

**See workflow #32 for complete connection procedures and troubleshooting.**

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md) | **Workflows:** [Workflow Index](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related phases:**
- Previous: [Phase 2: AWS Glue ETL](PHASE_2_AWS_GLUE.md)
- Next: [Phase 4: Simulation Engine](PHASE_4_SIMULATION_ENGINE.md) or [Phase 5: Machine Learning](PHASE_5_MACHINE_LEARNING.md)

---

*For Claude Code: See CLAUDE.md for navigation instructions and context management strategies.*

---

*Last updated: 2025-10-02*
*Completed by: Phase 3 team*
*Total time: 1 hour 37 minutes*

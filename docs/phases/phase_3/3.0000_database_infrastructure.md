# Phase 3: Database Infrastructure (RDS PostgreSQL)

**Status:** ✅ COMPLETE
**Prerequisites:** Phase 0 complete (S3 data uploaded)
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

**Tables created (traditional schema):**
- `teams` (87 rows) - NBA team metadata
- `players` (5,000+ rows) - Player information
- `games` (44,828 rows with 58 columns) - Game metadata and scores
- `player_game_stats` (408,833 rows) - Player box scores
- `team_game_stats` (15,900 rows) - Team statistics
- `plays` / `play_by_play` (6,781,155 rows) - Play-by-play data

**Tables needed (temporal schema - PENDING):**
- `temporal_events` (500M+ rows projected) - Event-level timestamps with millisecond precision
- `player_snapshots` (50M+ rows projected) - Cumulative player statistics at temporal checkpoints
- `game_states` (10M+ rows projected) - Game state reconstruction data
- `player_biographical` (5K+ rows) - Birth dates and biographical data for age calculations

**Validation:**
- [x] Traditional schema supports simulation queries
- [x] Indexes cover common query patterns
- [x] Foreign keys enforce referential integrity
- [ ] **PENDING:** Temporal schema design and implementation

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

### Sub-Phase 3.5: Temporal Database Schema (PENDING)

**Status:** ⏸️ PENDING
**Prerequisites:** Sub-Phase 3.1-3.4 complete, Phase 0 temporal data collection complete
**Time Estimate:** 6-8 hours
**Estimated Cost:** +$15-25/month (storage for 500M+ temporal events)

**Follow these workflows:**
- Workflow #25 ([Database Migration](../claude_workflows/workflow_descriptions/25_database_migration.md))
  - **When to run:** Before creating temporal schema
  - **Purpose:** Plan migration strategy, test rollback procedures

- Workflow #28 ([ADR Creation](../claude_workflows/workflow_descriptions/28_adr_creation.md))
  - **When to run:** When making temporal schema decisions
  - **Purpose:** Document ADR-009 (Temporal Panel Data Architecture)

**Overview:**

This sub-phase adds temporal panel data capabilities to the database, enabling snapshot queries at exact timestamps with millisecond precision.

**Core capability:** Query "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"

**Tasks:**
1. ⏸️ Design and create `temporal_events` table
2. ⏸️ Design and create `player_snapshots` table
3. ⏸️ Design and create `game_states` table
4. ⏸️ Design and create `player_biographical` table
5. ⏸️ Create temporal indexes (BRIN for time-series optimization)
6. ⏸️ Implement snapshot query stored procedures
7. ⏸️ Create age calculation functions
8. ⏸️ Test temporal queries with validation suite

#### Table 1: temporal_events

**Purpose:** Store every play-by-play event with precise timestamps

**Schema:**
```sql
CREATE TABLE temporal_events (
    event_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,

    -- Temporal precision
    wall_clock_utc TIMESTAMP(3) NOT NULL,      -- Millisecond precision
    wall_clock_local TIMESTAMP(3),             -- Local timezone
    game_clock_seconds INTEGER,                -- Seconds remaining in quarter
    quarter INTEGER,
    precision_level VARCHAR(10) NOT NULL,      -- 'millisecond', 'second', 'minute', 'game'

    -- Event details
    event_type VARCHAR(50),                    -- shot, foul, turnover, etc.
    event_subtype VARCHAR(50),                 -- 3pt shot, technical foul, etc.
    player_id INTEGER,
    team_id INTEGER,

    -- Event data
    event_data JSONB,                          -- Full play-by-play JSON

    -- Data provenance
    data_source VARCHAR(20) NOT NULL,          -- 'nba_live', 'nba_stats', 'espn', 'hoopr'
    ingestion_timestamp TIMESTAMP DEFAULT NOW(),

    -- Foreign keys
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- BRIN indexes for time-series data (more efficient than B-tree for timestamps)
CREATE INDEX idx_temporal_events_time_brin ON temporal_events
    USING BRIN (wall_clock_utc);

CREATE INDEX idx_temporal_events_game ON temporal_events (game_id, wall_clock_utc);
CREATE INDEX idx_temporal_events_player ON temporal_events (player_id, wall_clock_utc);
CREATE INDEX idx_temporal_events_precision ON temporal_events (precision_level);
```

**Projected size:** 500M+ rows, ~200-300 GB

#### Table 2: player_snapshots

**Purpose:** Pre-computed cumulative statistics at temporal checkpoints for fast queries

**Schema:**
```sql
CREATE TABLE player_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    snapshot_time TIMESTAMP(3) NOT NULL,

    -- Player age at this moment
    age_years DECIMAL(10,4),                   -- Precise age (e.g., 37.6412 years)
    age_days INTEGER,                           -- Age in days

    -- Cumulative career statistics
    career_points INTEGER,
    career_assists INTEGER,
    career_rebounds INTEGER,
    career_steals INTEGER,
    career_blocks INTEGER,
    career_turnovers INTEGER,
    career_field_goals_made INTEGER,
    career_field_goals_attempted INTEGER,
    career_three_pointers_made INTEGER,
    career_three_pointers_attempted INTEGER,
    career_free_throws_made INTEGER,
    career_free_throws_attempted INTEGER,
    career_games_played INTEGER,
    career_minutes_played INTEGER,

    -- Metadata
    precision_level VARCHAR(10) NOT NULL,
    data_completeness DECIMAL(5,2),            -- % of games with data

    -- Foreign key
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX idx_player_snapshots_lookup ON player_snapshots (player_id, snapshot_time);
CREATE INDEX idx_player_snapshots_time ON player_snapshots USING BRIN (snapshot_time);
```

**Projected size:** 50M+ rows, ~10-20 GB

#### Table 3: game_states

**Purpose:** Reconstruct complete game state at any timestamp

**Schema:**
```sql
CREATE TABLE game_states (
    state_id BIGSERIAL PRIMARY KEY,
    game_id VARCHAR(20) NOT NULL,
    state_time TIMESTAMP(3) NOT NULL,

    -- Score and clock
    home_score INTEGER,
    away_score INTEGER,
    quarter INTEGER,
    game_clock_seconds INTEGER,

    -- Possession
    possession_team_id INTEGER,

    -- Lineups (JSON arrays of player IDs)
    home_lineup JSONB,
    away_lineup JSONB,

    -- Metadata
    precision_level VARCHAR(10),

    -- Foreign keys
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (possession_team_id) REFERENCES teams(team_id)
);

CREATE INDEX idx_game_states_lookup ON game_states (game_id, state_time);
```

**Projected size:** 10M+ rows, ~2-5 GB

#### Table 4: player_biographical

**Purpose:** Store birth dates and biographical data for precise age calculations

**Schema:**
```sql
CREATE TABLE player_biographical (
    player_id INTEGER PRIMARY KEY,

    -- Birth date with precision flag
    birth_date DATE,
    birth_date_precision VARCHAR(10),          -- 'day', 'month', 'year', 'unknown'
    birth_date_source VARCHAR(50),             -- 'nba_api', 'basketball_ref', 'kaggle'

    -- Name variations
    full_name VARCHAR(100),
    display_name VARCHAR(100),

    -- Physical attributes
    height_inches INTEGER,
    weight_pounds INTEGER,

    -- Career metadata
    draft_year INTEGER,
    draft_round INTEGER,
    draft_pick INTEGER,
    rookie_season INTEGER,

    -- Foreign key
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE INDEX idx_player_bio_birth_date ON player_biographical (birth_date);
```

**Projected size:** 5,000+ rows, <1 MB

#### Snapshot Query Functions

**Function: get_player_snapshot_at_time**

```sql
CREATE OR REPLACE FUNCTION get_player_snapshot_at_time(
    p_player_id INTEGER,
    p_timestamp TIMESTAMP(3)
)
RETURNS TABLE (
    player_id INTEGER,
    snapshot_time TIMESTAMP(3),
    age_years DECIMAL(10,4),
    career_points INTEGER,
    career_assists INTEGER,
    -- ... all cumulative stats
    precision_level VARCHAR(10)
) AS $$
BEGIN
    -- Look for pre-computed snapshot
    RETURN QUERY
    SELECT *
    FROM player_snapshots ps
    WHERE ps.player_id = p_player_id
      AND ps.snapshot_time <= p_timestamp
    ORDER BY ps.snapshot_time DESC
    LIMIT 1;

    -- If no snapshot found, compute on-the-fly from temporal_events
    IF NOT FOUND THEN
        -- Aggregate all events before timestamp
        RETURN QUERY
        SELECT
            p_player_id,
            p_timestamp,
            calculate_player_age(p_player_id, p_timestamp),
            SUM(CASE WHEN event_type = 'shot' AND (event_data->>'made')::boolean THEN (event_data->>'points')::int ELSE 0 END),
            SUM(CASE WHEN event_type = 'assist' THEN 1 ELSE 0 END),
            -- ... compute all stats
            'computed' as precision_level
        FROM temporal_events
        WHERE player_id = p_player_id
          AND wall_clock_utc <= p_timestamp
        GROUP BY player_id;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

**Function: calculate_player_age**

```sql
CREATE OR REPLACE FUNCTION calculate_player_age(
    p_player_id INTEGER,
    p_timestamp TIMESTAMP(3)
)
RETURNS DECIMAL(10,4) AS $$
DECLARE
    v_birth_date DATE;
    v_age_years DECIMAL(10,4);
BEGIN
    SELECT birth_date INTO v_birth_date
    FROM player_biographical
    WHERE player_id = p_player_id;

    IF v_birth_date IS NULL THEN
        RETURN NULL;
    END IF;

    -- Calculate precise age in years (with decimal precision)
    v_age_years := EXTRACT(EPOCH FROM (p_timestamp::timestamp - v_birth_date::timestamp)) / (365.25 * 24 * 60 * 60);

    RETURN v_age_years;
END;
$$ LANGUAGE plpgsql;
```

#### Example Queries

**Query 1: Kobe's stats at exact timestamp**
```sql
SELECT * FROM get_player_snapshot_at_time(
    977,  -- Kobe Bryant's player_id
    '2016-06-19 19:02:34.560-05'::TIMESTAMP
);
```

**Query 2: League pace at exact timestamp**
```sql
SELECT
    AVG(possessions_per_48) as league_pace
FROM game_states gs
JOIN games g ON gs.game_id = g.game_id
WHERE gs.state_time <= '2023-03-15 23:23:45.678'::TIMESTAMP
  AND gs.state_time >= '2023-03-15 23:23:45.678'::TIMESTAMP - INTERVAL '5 minutes'
  AND g.season = 2023;
```

**Validation:**
- [ ] temporal_events table created and indexed
- [ ] player_snapshots table created
- [ ] game_states table created
- [ ] player_biographical table loaded with birth dates
- [ ] Snapshot query functions working
- [ ] Age calculation accurate to seconds
- [ ] Query performance < 5 seconds for single player snapshot
- [ ] BRIN indexes reducing storage by 70%+

**Cost Impact:**
- Storage: +$15-25/month (500M rows at $0.10/GB)
- IOPS: Negligible (BRIN indexes very efficient)
- Backups: +$5/month (additional storage)
- **Total: ~$20-30/month additional**

**See also:**
- `docs/PROJECT_VISION.md` - Temporal panel data architecture
- `docs/ADR/009-temporal-panel-data-architecture.md` - Architecture decisions (to be created)
- `docs/TEMPORAL_QUERY_GUIDE.md` - Query examples and performance tips (to be created)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md) | **Workflows:** [Workflow Index](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related phases:**
- Previous: [Phase 2: AWS Glue ETL](PHASE_2_AWS_GLUE.md)
- Next: [Phase 4: Simulation Engine](PHASE_4_SIMULATION_ENGINE.md) or [Phase 5: Machine Learning](PHASE_5_MACHINE_LEARNING.md)

---

*For Claude Code: See CLAUDE.md for navigation instructions and context management strategies.*

---

*Last updated: 2025-10-07* (Added Sub-Phase 3.5: Temporal Database Schema)
*Completed by: Phase 3 team*
*Total time: 1 hour 37 minutes (traditional schema) + pending (temporal schema)*

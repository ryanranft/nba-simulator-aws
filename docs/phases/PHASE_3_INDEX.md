# Phase 3: Database Infrastructure

**Status:** ✅ COMPLETE (📚 1 enhancement recommendation available)
**Priority:** HIGH
**Prerequisites:** Phase 0 complete (data in S3)
**Estimated Time:** 4-5 hours
**Cost Impact:** $29/month (RDS PostgreSQL)
**Started:** October 1, 2025
**Completed:** October 1, 2025

---

## Overview

Set up RDS PostgreSQL database with temporal indexing for millisecond-precision queries. This phase creates the database infrastructure that enables cumulative statistics queries at any exact moment in time.

**This phase delivers:**
- RDS PostgreSQL instance (db.t3.micro, 20GB)
- Temporal database schema with event-time indexing
- Cumulative statistics support
- Security configuration (security groups, IAM)
- Database connection setup
- Backup and recovery configuration

**Why temporal database matters:**
- Query any cumulative stat at exact moment in time
- Support millisecond-precision temporal joins
- Enable "what were Kobe's stats at 7:02:34 PM on June 19, 2016?" queries
- Foundation for temporal panel data analysis

---

## Sub-Phases

| Sub-Phase | Name | Status | Time | File |
|-----------|------|--------|------|------|
| **3.0** | Database Infrastructure Setup | ✅ COMPLETE | 4-5h | [3.0_database_infrastructure.md](phase_3/3.0_database_infrastructure.md) |

---

## Sub-Phase 3.0: Database Infrastructure Setup

**Status:** ✅ COMPLETE (October 1, 2025)

**What was completed:**
- Created RDS PostgreSQL 15.4 instance
- Configured security groups for access
- Designed temporal schema with event_time indexing
- Created tables for games, players, play-by-play
- Set up cumulative statistics views
- Tested temporal queries
- Documented database schema

**Key Tables Created:**
1. **games** - Game metadata with temporal indexes
2. **play_by_play** - Every game event with wall_clock_time
3. **player_stats** - Per-game player statistics
4. **team_stats** - Per-game team statistics
5. **cumulative_stats** - Real-time cumulative views

**Temporal Indexing:**
- All tables indexed on event_time for temporal queries
- Support for millisecond-precision lookups
- Cumulative aggregation optimized

**See:** [Sub-Phase 3.0 Details](phase_3/3.0_database_infrastructure.md)

---

## Success Criteria

- [x] RDS instance created (db.t3.micro)
- [x] PostgreSQL 15.4 running
- [x] Security groups configured
- [x] Temporal schema implemented
- [x] Event-time indexing working
- [x] Cumulative queries tested
- [x] Backup enabled (7-day retention)
- [x] Connection string documented
- [x] Cost under $30/month

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| RDS PostgreSQL | db.t3.micro, 20GB | $29/month | Single-AZ, standard storage |
| Backup Storage | 7-day retention | Included | Up to 20GB free |
| **Total Phase Cost** | | **$29/month** | Can upgrade to t3.small for $58/month |

**Cost Optimization:**
- Start with db.t3.micro (sufficient for development)
- Upgrade to db.t3.small or db.t3.medium for production
- Consider Aurora Serverless for variable workloads

---

## Prerequisites

**Before starting Phase 3:**
- [x] Phase 0 complete (S3 data available)
- [x] AWS account with RDS permissions
- [ ] VPC and subnet configuration
- [ ] Security group rules defined

**Note:** Phase 3 can be done before Phase 2 (ETL), or in parallel.

---

## Key Architecture Decisions

**ADRs created in Phase 3:**
- **ADR-006:** PostgreSQL over MySQL (temporal features, JSON support)
- **ADR-007:** Single-AZ deployment (cost optimization for dev)
- Temporal schema design documented

**See:** `docs/adr/README.md`

---

## Multi-Sport Replication

**When adding a new sport (NFL, MLB, NHL, Soccer):**

This phase is **sport-agnostic** - the same RDS instance can host multiple sports:

**Option A: Single database, multiple schemas**
```sql
CREATE SCHEMA nba;
CREATE SCHEMA nfl;
CREATE SCHEMA mlb;
-- Tables: nba.games, nfl.games, mlb.games
```

**Option B: Multiple databases (recommended for isolation)**
```bash
# Use same RDS instance, create multiple databases
CREATE DATABASE nba_temporal;
CREATE DATABASE nfl_temporal;
CREATE DATABASE mlb_temporal;
```

**Temporal schema pattern is reusable** - same event_time indexing works for all sports.

---

## Key Workflows

**For Sub-Phase 3.0:**
- Workflow #24: AWS Resource Setup
- Workflow #18: Cost Management
- Workflow #28: ADR Creation
- Workflow #2: Command Logging

---

## Troubleshooting

**Common issues:**

1. **Cannot connect to RDS**
   - Solution: Check security group allows your IP
   - Verify RDS is publicly accessible (if needed)
   - Check VPC/subnet configuration

2. **Slow temporal queries**
   - Solution: Ensure event_time is indexed
   - Use EXPLAIN ANALYZE to check query plan
   - Consider partitioning large tables by date

3. **High RDS costs**
   - Solution: Start with db.t3.micro
   - Stop instance when not in use (development)
   - Use Reserved Instances for production

4. **Storage full**
   - Solution: Enable autoscaling storage
   - Increase allocated storage (20GB → 50GB)

---

## Next Steps

**After Phase 3 complete:**
- ✅ RDS database operational
- → Proceed to [Phase 2: AWS Glue ETL](PHASE_2_INDEX.md) (if not already done)
- → Or proceed to [Phase 4: Simulation Engine](PHASE_4_INDEX.md)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md)
**Previous Phase:** [Phase 2: AWS Glue ETL](PHASE_2_INDEX.md)
**Next Phase:** [Phase 4: Simulation Engine](PHASE_4_INDEX.md)
**Workflow Index:** [CLAUDE_WORKFLOW_ORDER.md](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related Documentation:**
- [Temporal Query Guide](../TEMPORAL_QUERY_GUIDE.md)
- [Database Schema Diagram](../DATABASE_SCHEMA.md)
- [RDS Connection Guide](../SETUP.md)

---

*For Claude Code: This phase has a single sub-phase. Read the sub-phase file for database setup and schema details.*

---

**Last Updated:** October 11, 2025
**Phase Owner:** Database Team
**Total Sub-Phases:** 1
**Status:** 100% complete (1 of 1 sub-phases done)

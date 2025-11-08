# CLAUDE.md

**Version:** 4.0 (v2.0 Refactoring Complete)  
**Last Updated:** November 5, 2025  
**Status:** ✅ Production Ready

This file provides core guidance to Claude Code when working in this repository. **For detailed explanations, see `docs/CLAUDE_DETAILED_GUIDE.md`.**

**🎊 v2.0 COMPLETE (November 4, 2025):**
- ✅ Clean package (`nba_simulator/`) - 10,000+ lines production code
- ✅ Comprehensive tests (216+ cases, 95%+ coverage)
- ✅ Zero data loss & downtime (35M+ records safe)
- ✅ Production ready (complete deployment guides)

---

## Quick Start - Every Session

**Read these 3 files at session start:**
1. **CLAUDE.md** (this file, ~270 lines) - Core instructions
2. **PROGRESS.md** (~390 lines) - Current project state  
3. **docs/README.md** (~100 lines) - Documentation index

**Total: ~760 lines (3.8% context)** - Leaves 96.2% for actual work

**Session startup:**
1. Run `bash scripts/shell/session_manager.sh start` (auto-checks system)
2. Ask user what completed since last session
3. Update "Current Session Context" in PROGRESS.md
4. Ask what to work on today
5. Read relevant phase/workflow files as needed

---

## 🏗️ v2.0 Quick Reference

**Main Package:** `/Users/ryanranft/nba-simulator-aws/nba_simulator/`

**Key Imports:**
```python
from nba_simulator.config import config
from nba_simulator.database import execute_query
from nba_simulator.agents import MasterAgent
from nba_simulator.workflows import WorkflowOrchestrator, ADCECoordinator
```

**Run Tests:**
```bash
pytest tests/ -v --cov                    # All 216+ tests
pytest tests/unit/ -v                     # Unit tests (150+)
pytest tests/integration/ -v              # Integration (66+)
python scripts/system_validation.py       # System health
```

**Package Status:**
- Database: 54 tables, 35M+ records, 13.5+ GB
- S3: 146,115+ files, 119+ GB
- Tests: 216+ cases, 95%+ coverage
- Legacy systems: All maintained and operational

**Docs:** See `FINAL_DOCUMENTATION.md`, `PRODUCTION_DEPLOYMENT_GUIDE.md`, `QUICK_REFERENCE_GUIDE.md`

---

## Critical Paths

- **Project Root:** `/Users/ryanranft/nba-simulator-aws`
- **Package:** `/Users/ryanranft/nba-simulator-aws/nba_simulator/`
- **Tests:** `/Users/ryanranft/nba-simulator-aws/tests/`
- **S3:** `s3://nba-sim-raw-data-lake`

**Activate environment:**
```bash
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws
```

---

## Database Credentials

**Credentials managed using hierarchical secrets structure**
See: `/Users/ryanranft/Desktop/++/big_cat_bets_assets/SECRETS_STRUCTURE.md`

**Location:** `/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-simulator-aws/`

**Contexts:**
- **Production (WORKFLOW):** AWS RDS PostgreSQL
  - Directory: `.env.nba_simulator_aws.production/`
  - Naming: `RDS_*_NBA_SIMULATOR_AWS_WORKFLOW.env`
  - Database: `nba_simulator` @ RDS (35M+ records)

- **Development (DEVELOPMENT):** Local PostgreSQL or RDS Dev
  - Directory: `.env.nba_simulator_aws.development/`
  - Naming: `POSTGRES_*_NBA_SIMULATOR_AWS_DEVELOPMENT.env` (local) or `RDS_*_NBA_SIMULATOR_AWS_DEVELOPMENT.env` (RDS)
  - Local databases: `nba_simulator` (15 tables), `nba_unified` (10 tables)

- **Test (TEST):** Local PostgreSQL test database
  - Directory: `.env.nba_simulator_aws.test/`
  - Naming: `POSTGRES_*_NBA_SIMULATOR_AWS_TEST.env`
  - Database: `nba_simulator_test`

**Loading credentials:**
```bash
# Auto-load with session manager
bash scripts/shell/session_manager.sh start

# Manual load
source /Users/ryanranft/load_secrets_universal.sh

# Python (auto-detects context from ENVIRONMENT variable)
python3 -c "from nba_simulator.config import config; print(config.load_database_config())"
```

**Context switching:**
```bash
# Use local PostgreSQL (default)
export ENVIRONMENT=development

# Use production RDS
export ENVIRONMENT=production
```

**Available credentials:**
- `RDS_HOST_NBA_SIMULATOR_AWS_WORKFLOW` - RDS endpoint
- `RDS_DATABASE_NBA_SIMULATOR_AWS_WORKFLOW` - Database name
- `RDS_USERNAME_NBA_SIMULATOR_AWS_WORKFLOW` - Username
- `RDS_PASSWORD_NBA_SIMULATOR_AWS_WORKFLOW` - Password
- `RDS_PORT_NBA_SIMULATOR_AWS_WORKFLOW` - Port (5432)
- `POSTGRES_HOST_NBA_SIMULATOR_AWS_DEVELOPMENT` - Local host (localhost)
- `POSTGRES_DB_NBA_SIMULATOR_AWS_DEVELOPMENT` - Local database name
- `POSTGRES_USER_NBA_SIMULATOR_AWS_DEVELOPMENT` - Local user
- `POSTGRES_PASSWORD_NBA_SIMULATOR_AWS_DEVELOPMENT` - Local password (empty for trust auth)
- `POSTGRES_PORT_NBA_SIMULATOR_AWS_DEVELOPMENT` - Local port (5432)

**Never commit:**
- `.env` files in project root
- `/Users/ryanranft/nba-sim-credentials.env` (legacy file)
- Any files in `.env.nba_simulator_aws.*` directories
- Credentials are outside Git repo ✅

---

## Database Schema Architecture

**Production Standard:** `raw_data` schema (Phase 0.10+)

**Local databases now match production** with `raw_data` schema alongside legacy `master` schema.

### Schema Overview

| Schema | Purpose | Status | Tables |
|--------|---------|--------|--------|
| `raw_data` | **Production standard** - JSONB storage for multi-source data | ✅ Active | nba_games, nba_players, nba_teams, nba_misc, schema_version |
| `rag` | RAG/embeddings pipeline (Phase 0.11) | ✅ Active | nba_embeddings, play_embeddings, document_embeddings |
| `master` | Legacy development schema | ⚠️ Deprecated | nba_games, nba_plays, espn_file_validation |

### Design Philosophy

**raw_data schema:**
- Document-oriented with JSONB `data` column
- Flexible for multi-source ingestion (hoopR, ESPN, nba_api)
- ACID guarantees with PostgreSQL benefits
- Created by: `scripts/db/migrations/0_10_schema.sql`

**rag schema:**
- Specialized for embeddings and semantic search
- pgvector extension with HNSW indexes
- Separate from raw_data for performance isolation
- Created by: `scripts/db/migrations/0_11_schema.sql`

### Running Migrations

**Create raw_data schema locally:**
```bash
export POSTGRES_DB=nba_simulator
export POSTGRES_USER=ryanranft
export POSTGRES_HOST=localhost
psql -U $POSTGRES_USER $POSTGRES_DB -f scripts/db/migrations/0_10_schema.sql
```

**Create rag schema locally:**
```bash
psql -U $POSTGRES_USER $POSTGRES_DB -f scripts/db/migrations/0_11_schema.sql
```

### Schema-Agnostic Validators

**Phase 0 validators support multiple schemas:**

```bash
# Validate raw_data schema (default)
python validators/phases/phase_0/validate_0_0010.py

# Validate with --schema flag
python validators/phases/phase_0/validate_0_0010.py --schema=raw_data
python validators/phases/phase_0/validate_0_0010.py --schema=master

# RAG validator (defaults to rag schema)
python validators/phases/phase_0/validate_0_0011.py
python validators/phases/phase_0/validate_0_0011.py --schema=rag
```

**Validators with --schema support:**
- `validate_0_0010.py` - PostgreSQL JSONB Storage (raw_data/master)
- `validate_0_0011.py` - RAG Pipeline (rag)

### Migration Status

**✅ Migration Complete (November 5, 2025):**
- ✅ **31,241 games** migrated from `master` → `raw_data`
- ✅ **44,826 file validations** migrated
- ✅ **14.1M play-by-play records** summarized and embedded
- ✅ **100% validation** pass rate (row counts, data quality, play counts, spot checks)
- ✅ **23 seconds** migration time (1,331.6 games/sec)
- ✅ **Zero errors** during migration
- ✅ Both schemas coexist (raw_data + master preserved for rollback)
- ✅ Validators support both schemas

**See:** `docs/MIGRATION_REPORT.md` for complete migration details

---

## Session Workflow

**Every new session:**
1. Read CLAUDE.md + PROGRESS.md + docs/README.md
2. Check "Current Session Context" 
3. Ask: "What did you complete?"
4. Update context in PROGRESS.md
5. Ask: "What to work on today?"
6. Read PHASE_N_INDEX.md if needed
7. Read phase_N/N.M_name.md if needed
8. Check for "⚠️ IMPORTANT" notes
9. Begin work

**Update hierarchy:**
- Sub-phase completes → Update phase file, then phase index
- Full phase completes → Update phase index, then PROGRESS.md
- Session ends → Update PROGRESS.md "Current Session Context"

**Session end checklist:**
- [ ] Sub-phase file status matches completion
- [ ] Phase index matches sub-phases
- [ ] PROGRESS.md matches phase indexes
- [ ] "Current Session Context" updated
- [ ] COMMAND_LOG.md updated
- [ ] All files saved & committed

**Navigation pattern:**
```
PROGRESS.md → PHASE_N_INDEX.md → phase_N/N.M_name.md → workflows → execute
```

**Phase completion:** Always run Workflow #58 before marking phase ✅ COMPLETE

---

## Navigation & Context

**Read as needed:**
- Phase indexes: ~150 lines (0.75% context)
- Sub-phase files: 300-800 lines (1.5-4% context)  
- Workflows: 200-400 lines (1-2% context)

**Grep only (don't read fully):**
- TROUBLESHOOTING.md (1,025 lines)
- LESSONS_LEARNED.md (1,002 lines)
- TEMPORAL_QUERY_GUIDE.md (996 lines)

**Context budgets:**
- Minimal: 760 lines (3.8%) - Just core files
- Light: 1,410 lines (7%) - + 1 phase + 1 sub-phase
- Moderate: 2,060 lines (10.3%) - + workflows
- Maximum: 4,000 lines (20%)

**Context approaching 90%?**
→ Stop reading → Commit work → Update PROGRESS.md → End session → Start fresh

**Detailed context strategies:** See `docs/CONTEXT_MANAGEMENT_GUIDE.md`

---

## Safety Protocols

### Git & Security

**CRITICAL - Before ANY Git Operation:**
- **Before commit:** Run security scan
- **Before push:** Run `scripts/shell/pre_push_inspector.sh full`
- **NEVER commit:** `.env`, credentials, AWS keys, secrets, IPs
- **NEVER push without user approval** - always ask first
- **If hook blocks:** Show flagged lines, explain, get explicit approval

### Data Safety

- **NEVER delete/modify S3** without explicit request
- **NEVER drop database tables** without confirmation
- **Backup before destructive operations**
- **35M+ records in production** - zero data loss maintained

### Cost Awareness

- **Current cost:** $2.74/month (S3 only)
- **Budget:** $150/month
- **ALWAYS warn before creating:** RDS (~$29/mo), EC2 (~$5-15/mo), Glue (~$13/mo)

**See:** `docs/SECURITY_PROTOCOLS.md` for complete procedures

---

## Quick Commands

**Session management:**
```bash
bash scripts/shell/session_manager.sh start    # Start session
bash scripts/shell/session_manager.sh end      # End session
```

**Testing:**
```bash
pytest tests/ -v --cov                         # All tests
python scripts/system_validation.py            # System health
```

**Automation Triad (self-maintaining systems):**
```bash
python scripts/monitoring/dims_cli.py verify       # DIMS
python scripts/autonomous/autonomous_cli.py status # ADCE
python scripts/maintenance/prms_cli.py scan        # PRMS
```

**Database:**
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM games;"
```

**S3:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --human-readable
```

**Complete commands:** See `QUICKSTART.md`

---

## Key Resources

**Core Documentation:**
- `PROGRESS.md` - Current project state
- `docs/README.md` - Documentation index
- `docs/CLAUDE_DETAILED_GUIDE.md` - Detailed explanations (reference only)

**v2.0 Documentation:**
- `FINAL_DOCUMENTATION.md` - Complete architecture & API
- `PRODUCTION_DEPLOYMENT_GUIDE.md` - Deployment procedures
- `PROJECT_COMPLETION_REPORT.md` - Project history
- `QUICK_REFERENCE_GUIDE.md` - Quick access guide

**System Documentation:**
- `QUICKSTART.md` - All commands
- `docs/SETUP.md` - Complete setup
- `docs/SECURITY_PROTOCOLS.md` - Security procedures
- `docs/CONTEXT_MANAGEMENT_GUIDE.md` - Context strategies
- `docs/EMERGENCY_RECOVERY.md` - Emergency procedures

**Workflows:**
- `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md` - 54 workflows index
- `docs/claude_workflows/workflow_descriptions/` - Individual workflows

---

## Project Core

**Mission:** Temporal panel data system for NBA (not traditional sports analytics)

**Core capability:** Query cumulative NBA statistics at any exact moment in history with millisecond precision.

**Example:** "What were Kobe Bryant's career statistics at exactly 7:02:34.56 PM CT on June 19, 2016?"

**Architecture:** 5-phase pipeline (collection → storage → transformation → modeling → simulation)

**Complete architecture:** See `README.md` and `docs/PROJECT_VISION.md`

---

## Important Notes

**Project scope:** NBA-only. Other sports = separate projects.

**54 modular workflows** covering session operations, git/security, testing, cost management, backup/recovery, data validation, troubleshooting, AWS resource setup, scraper monitoring, overnight handoffs, and autonomous operations.

**The Automation Triad:** Three self-maintaining systems working 24/7:
1. **DIMS** - Data Inventory Management (metrics tracking)
2. **ADCE** - Autonomous Data Collection (self-healing scrapers)
3. **PRMS** - Path Reference Management (code quality)

**See `docs/CLAUDE_DETAILED_GUIDE.md` for:**
- Complete phase index system explanation
- ML framework navigation (13 frameworks)
- Background agent operations details
- Automation Triad deep dive
- Complete development examples
- Testing framework details

---

**Next Steps:** See `PROGRESS.md` for detailed phase-by-phase plan

**Last Updated:** November 5, 2025  
**Version:** 4.0 (v2.0 Refactoring Complete)  
**Status:** ✅ Production Ready

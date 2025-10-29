# Quick Start: NBA Simulator Refactoring (New Chat)

Hi! I need help continuing my NBA Simulator AWS refactoring project.

## Context
I have a production data platform with:
- 4,055+ files (1,672 Python scripts, 643 tests, 1,720 docs)
- 20M+ database records (40 tables, 13.5 GB)
- 75+ active ETL scrapers
- 8 autonomous agents running 24/7

We need to refactor scattered scripts into a proper Python package while maintaining zero data loss and zero downtime.

## What We've Done
Created three comprehensive planning documents in the project files:
1. **COMPREHENSIVE_FILE_INVENTORY.md** - Maps all 4,055+ files
2. **COMPLETE_REFACTORING_EXECUTION_PLAN.md** - 14-week master plan
3. **CLAUDE_CODE_REFACTORING_INSTRUCTIONS.md** - Phase 1 execution guide

## What We Need Next
**Complete Phase 0 Discovery before starting execution:**

1. **Investigate `temporal_events` table** (5.8 GB - purpose unknown)
   - Use MCP: `nba-mcp-server:query_database`
   - Query: `SELECT COUNT(*), pg_size_pretty(pg_total_relation_size('temporal_events')) FROM temporal_events;`

2. **Check for scheduled jobs** (cron/systemd/launchd)
   - What scrapers run automatically?
   - Which scripts are in production use?

3. **Verify Phase 8 status** (box score generation)
   - Is it actively running or paused?

4. **Create safety backups** (database + git tags)

## Instructions
Please:
1. Read the three planning documents from project files
2. Use MCP tools to help investigate the items above
3. Help me complete Phase 0 discovery, then we can execute Phase 1

## MCP Tools Available
- `nba-mcp-server:query_database` - Query PostgreSQL
- `nba-mcp-server:list_tables` - List all tables
- `nba-mcp-server:get_table_schema` - Get table schema
- `nba-mcp-server:list_s3_files` - List S3 files

Project location: `/Users/ryanranft/nba-simulator-aws`

Ready to continue!

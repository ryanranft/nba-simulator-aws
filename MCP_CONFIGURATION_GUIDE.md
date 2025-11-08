# NBA MCP Server Configuration - Complete Guide

**Last Updated:** 2025-01-06
**Version:** 2.0 (Enhanced DDL Server)

---

## 🎯 Overview

This document describes the complete MCP (Model Context Protocol) server configuration for the NBA analytics and database management system. There are **3 MCP servers** providing different capabilities for database operations, DDL management, and file operations.

---

## 📋 MCP Servers Summary

| Server Name | Purpose | Tools Available | Status |
|-------------|---------|-----------------|--------|
| **nba-mcp-server** | Database queries and S3 operations | 4 tools | ✅ Active |
| **nba-ddl-server** | Schema management and DDL operations | 11 tools | ✅ Active (Enhanced) |
| **filesystem** | File system operations | Standard MCP | ✅ Active |

---

## 🔧 Server 1: nba-mcp-server (Database Queries)

### Purpose
Read-only database access for querying NBA statistics, player data, and game information.

### Location
```
/Users/ryanranft/nba-mcp-synthesis/mcp_server/server_simple.py
```

### Credentials
Uses hierarchical secrets management from:
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

### Configuration
```json
{
  "nba-mcp-server": {
    "command": "/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3",
    "args": ["/Users/ryanranft/nba-mcp-synthesis/mcp_server/server_simple.py"],
    "cwd": "/Users/ryanranft/nba-mcp-synthesis",
    "env": {
      "AWS_REGION": "us-east-1",
      "S3_BUCKET": "nba-sim-raw-data-lake"
    }
  }
}
```

### Available Tools

#### 1. `query_database(sql: str) -> dict`
Execute SELECT queries on the NBA database.

**Parameters:**
- `sql` (string, required): SELECT query to execute

**Limitations:**
- SELECT queries only (no INSERT/UPDATE/DELETE)
- Maximum 100 rows returned
- Automatic timeout after 30 seconds

**Example Usage:**
```python
# Query player statistics
query_database("SELECT player_name, points, rebounds FROM player_stats WHERE season = '2024-25' LIMIT 10")

# Aggregate queries
query_database("SELECT team_id, AVG(points) as avg_points FROM team_stats GROUP BY team_id")

# Join queries
query_database("""
    SELECT p.player_name, t.team_name, s.points
    FROM player_stats s
    JOIN players p ON s.player_id = p.player_id
    JOIN teams t ON s.team_id = t.team_id
    WHERE s.season = '2024-25'
""")
```

**Returns:**
```json
{
  "success": true,
  "rows": [...],
  "row_count": 10,
  "columns": ["player_name", "points", "rebounds"]
}
```

---

#### 2. `list_tables() -> dict`
List all tables in the NBA database.

**Parameters:** None

**Example Usage:**
```python
list_tables()
```

**Returns:**
```json
{
  "tables": [
    {"schema": "public", "name": "player_stats", "type": "BASE TABLE"},
    {"schema": "public", "name": "team_stats", "type": "BASE TABLE"},
    {"schema": "public", "name": "games", "type": "BASE TABLE"}
  ],
  "count": 50
}
```

---

#### 3. `get_table_schema(table_name: str) -> dict`
Get detailed schema information for a specific table.

**Parameters:**
- `table_name` (string, required): Name of the table

**Example Usage:**
```python
get_table_schema("player_stats")
```

**Returns:**
```json
{
  "success": true,
  "table": "public.player_stats",
  "columns": [
    {
      "name": "player_id",
      "type": "integer",
      "nullable": false,
      "default": null
    },
    {
      "name": "points",
      "type": "numeric",
      "nullable": true,
      "default": "0"
    }
  ],
  "indexes": [
    {
      "name": "player_stats_pkey",
      "definition": "CREATE UNIQUE INDEX player_stats_pkey ON player_stats USING btree (player_id, game_id)"
    }
  ]
}
```

---

#### 4. `list_s3_files(prefix: str = "", max_keys: int = 100) -> dict`
List files in the S3 bucket.

**Parameters:**
- `prefix` (string, optional): Filter by prefix (e.g., "raw_data/2024/")
- `max_keys` (integer, optional): Maximum files to return (default: 100)

**Example Usage:**
```python
# List all files
list_s3_files()

# List files in specific directory
list_s3_files(prefix="raw_data/player_stats/")

# Limit results
list_s3_files(prefix="processed/", max_keys=50)
```

**Returns:**
```json
{
  "success": true,
  "files": [
    {
      "key": "raw_data/player_stats/2024-01-01.csv",
      "size": 1024000,
      "last_modified": "2024-01-01T12:00:00Z"
    }
  ],
  "count": 25
}
```

---

## 🛠️ Server 2: nba-ddl-server (Schema Management)

### Purpose
Enterprise-grade DDL (Data Definition Language) management with migration tracking, audit logging, and safety features.

### Location
```
/Users/ryanranft/nba-simulator-aws/ddl_server_enhanced.py
```

### Configuration File
```
/Users/ryanranft/nba-simulator-aws/ddl_config.json
```

### Credentials
Uses same hierarchical secrets as nba-mcp-server (shared database).

### Configuration
```json
{
  "nba-ddl-server": {
    "command": "/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3",
    "args": ["/Users/ryanranft/nba-simulator-aws/ddl_server_enhanced.py"],
    "cwd": "/Users/ryanranft/nba-simulator-aws",
    "env": {}
  }
}
```

### Safety Features

**All DDL operations have these safety mechanisms:**

1. **Dry-Run by Default** - All operations default to `dry_run=true`, requiring explicit `dry_run=false` to execute
2. **Two-Step Confirmation** - DROP operations require confirmation token from dry-run
3. **Audit Logging** - Every operation (including dry-runs) logged to `ddl_audit_log` table
4. **Migration Tracking** - All changes tracked in `ddl_migration_history` with version numbers
5. **Dependent Object Detection** - Shows views, foreign keys, indexes before destructive operations
6. **Large Table Warnings** - Warns for operations on tables >1M rows
7. **CONCURRENT Indexes** - Index creation is non-blocking by default
8. **Schema Diffing** - Shows before/after comparison for ALTER operations

### Available Tools (11 Total)

See separate document: `DDL_SERVER_COMPLETE_GUIDE.md`

---

## 📁 Server 3: filesystem (File Operations)

### Purpose
Standard MCP filesystem server for reading and managing files.

### Configuration
```json
{
  "filesystem": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "/Users/ryanranft/nba-simulator-aws"
    ]
  }
}
```

### Scope
Limited to `/Users/ryanranft/nba-simulator-aws` directory for security.

### Available Tools
Standard MCP filesystem tools:
- Read files
- Write files
- List directories
- Search files

---

## 🔐 Security & Credentials

### Hierarchical Secrets Management

**All database credentials are stored in hierarchical structure:**

```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/
  sports_assets/big_cat_bets_simulators/NBA/
    nba-mcp-synthesis/
      .env.nba_mcp_synthesis.production/
        RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env
        RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env
        RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env
        RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW.env
        RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env
```

**Key Features:**
- ✅ No plaintext passwords in config files
- ✅ File permissions: 600 (owner read/write only)
- ✅ Automatic credential loading via `unified_secrets_manager`
- ✅ Shared credentials between nba-mcp-server and nba-ddl-server

### Database Sharing

**Important:** `nba-mcp-synthesis` and `nba-simulator-aws` projects share the **same PostgreSQL database**:
- Host: AWS RDS endpoint (loaded from hierarchical secrets)
- Database: `nba_simulator`
- Port: 5432

---

## 📊 Database Tables Created by DDL Server

The DDL server creates and maintains these tables for tracking:

### 1. ddl_migration_history
Tracks all schema migrations with version control.

**Key Columns:**
- `migration_id` - Unique ID
- `version_number` - Timestamp-based version (YYYYMMDDHHMMSSn)
- `migration_name` - Descriptive name
- `ddl_statement` - The DDL executed
- `rollback_statement` - Statement to undo the migration
- `status` - CREATED, SUCCESS, FAILED, ROLLBACK_SUCCESS, etc.
- `executed_at` - Execution timestamp
- `execution_duration_ms` - Performance metric

**Example Query:**
```sql
SELECT migration_id, version_number, migration_name, status, executed_at
FROM ddl_migration_history
ORDER BY version_number DESC
LIMIT 10;
```

### 2. ddl_audit_log
Immutable audit trail for compliance (365-day retention).

**Key Columns:**
- `audit_id` - Unique ID (bigserial)
- `execution_id` - UUID for this execution
- `operation_type` - CREATE_TABLE, ALTER_TABLE, DROP_TABLE, etc.
- `ddl_statement` - The DDL executed
- `is_dry_run` - Whether this was a dry-run
- `success` - Whether it succeeded
- `duration_ms` - Performance metric
- `executed_by` - Who executed it
- `schema_diff` - JSON before/after comparison

**Example Query:**
```sql
SELECT operation_type, object_name, is_dry_run, success, duration_ms, execution_started
FROM ddl_audit_log
WHERE success = true AND is_dry_run = false
ORDER BY execution_started DESC
LIMIT 20;
```

### 3. ddl_schema_version
Schema state snapshots over time.

**Key Columns:**
- `version_id` - Unique ID
- `version_number` - Version timestamp
- `schema_hash` - SHA256 hash of schema
- `applied_migrations` - Array of migration IDs
- `tags` - Array of tags (production, stable, etc.)

---

## 🎯 Common Workflows

### Workflow 1: Query Database for Analysis

```
1. Use list_tables() to see available tables
2. Use get_table_schema("table_name") to understand structure
3. Use query_database("SELECT ...") to get data
4. Analyze results
```

### Workflow 2: Modify Database Schema

```
1. Use validate_ddl_statement() to check DDL syntax
2. Use execute_alter_table() with dry_run=true to preview changes
3. Review schema_diff and warnings
4. Execute with dry_run=false to apply changes
5. Use get_audit_log() to verify execution
```

### Workflow 3: Create Tracked Migration

```
1. Use create_migration() to create versioned migration
2. System validates and assigns version number
3. Use execute_migration() with dry_run=true to test
4. Execute with dry_run=false to apply
5. If needed: use rollback_migration() to undo
```

### Workflow 4: Drop Table Safely

```
1. Use execute_drop_table_or_view() with dry_run=true
2. System returns confirmation_token + dependent objects list
3. Review impact (rows to delete, dependent views, etc.)
4. Call again with dry_run=false + confirmation_token to execute
5. Operation logged in audit trail
```

---

## 🔧 Configuration Files

### Main MCP Config
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### DDL Server Config
```
/Users/ryanranft/nba-simulator-aws/ddl_config.json
```

**Key Settings:**
- `safety_settings.default_dry_run`: true
- `audit_settings.retention_days`: 365
- `safety_settings.large_table_threshold_rows`: 1000000
- `safety_settings.confirmation_token_ttl_minutes`: 15

### Secrets Location
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

---

## 📈 Performance Considerations

### Query Performance
- `query_database()` has 100-row limit - use pagination for large results
- Complex queries timeout after 30 seconds
- Use indexes for frequently queried columns

### DDL Performance
- ALTER TABLE on large tables (>1M rows) may take minutes
- CREATE INDEX CONCURRENTLY is non-blocking but slower
- DROP operations are instant but require confirmation

### Audit Log Growth
- Audit log grows over time (~1-2 KB per operation)
- 365-day retention with automatic archival (configurable)
- Query with pagination for performance

---

## 🐛 Troubleshooting

### Issue: "Credentials not loading"
**Solution:** Verify hierarchical secrets exist and have correct permissions (600)

### Issue: "Query timeout"
**Solution:** Simplify query or add LIMIT clause

### Issue: "DDL operation failed with 'permission denied'"
**Solution:** Check database user has required permissions (CREATE, ALTER, DROP)

### Issue: "Cannot find MCP tools"
**Solution:** Start a NEW conversation in Claude Desktop after config changes

### Issue: "Confirmation token expired"
**Solution:** Tokens expire in 15 minutes - run dry-run again to get new token

---

## 📚 Additional Resources

**Detailed DDL Documentation:**
- `/Users/ryanranft/nba-simulator-aws/DDL_SERVER_COMPLETE_GUIDE.md`

**Claude Desktop Instructions:**
- `/Users/ryanranft/nba-mcp-synthesis/.claude/CLAUDE.md`

**Configuration:**
- `/Users/ryanranft/nba-simulator-aws/ddl_config.json`

**Database Schema:**
- `/Users/ryanranft/nba-simulator-aws/ddl_schema_setup.sql`

---

## 🔄 Version History

**Version 2.0 (2025-01-06):**
- Enhanced DDL server with 11 tools (vs 3 basic)
- Migration tracking system
- Audit logging (365-day retention)
- Two-step confirmation for destructive operations
- Dry-run mode for all DDL operations

**Version 1.0 (2025-01-05):**
- Basic DDL server with 3 tools
- Query-only database server
- Filesystem server

---

## 🎯 Quick Reference

**Query Database:**
```python
query_database("SELECT * FROM player_stats LIMIT 10")
```

**List Tables:**
```python
list_tables()
```

**Get Schema:**
```python
get_table_schema("player_stats")
```

**Create Index:**
```python
execute_create_index(
    index_name="idx_player_season",
    table_name="player_stats",
    columns="player_id, season",
    dry_run=false  # After dry-run validation
)
```

**Alter Table:**
```python
execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ADD COLUMN efficiency_rating FLOAT",
    dry_run=false  # After reviewing schema_diff
)
```

**Query Audit Log:**
```python
get_audit_log(limit=50, success_only=true)
```

---

*This configuration provides enterprise-grade database management with comprehensive safety, audit, and migration tracking capabilities.*
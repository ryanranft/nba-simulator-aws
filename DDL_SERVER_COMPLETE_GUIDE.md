# NBA DDL Server - Complete Tool Reference

**Version:** 2.0 (Enhanced)
**Last Updated:** 2025-01-06
**Server:** `ddl_server_enhanced.py`

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Safety Philosophy](#safety-philosophy)
3. [Execution Tools](#execution-tools)
4. [Validation & Intelligence Tools](#validation--intelligence-tools)
5. [Migration Management Tools](#migration-management-tools)
6. [Observability Tools](#observability-tools)
7. [Legacy Tools](#legacy-tools)
8. [Complete Workflows](#complete-workflows)
9. [Error Codes Reference](#error-codes-reference)
10. [Best Practices](#best-practices)

---

## 🎯 Overview

The Enhanced DDL Server provides **11 MCP tools** for comprehensive schema management:

| Category | Tools | Purpose |
|----------|-------|---------|
| **Execution** | 4 tools | ALTER, CREATE INDEX, DROP, CREATE operations |
| **Validation** | 2 tools | Syntax/semantic validation, schema diffing |
| **Migration** | 3 tools | Version-tracked migrations with rollback |
| **Observability** | 2 tools | Audit log and migration history queries |
| **Legacy** | 2 tools | Backward compatibility (list_tables, get_table_schema) |

---

## 🛡️ Safety Philosophy

### Core Principles

1. **Dry-Run by Default** - ALL operations default to `dry_run=true`
2. **Explicit Execution** - User must explicitly set `dry_run=false` to execute
3. **Two-Step Destructive Operations** - DROP requires confirmation token
4. **Complete Audit Trail** - Every operation logged (including dry-runs)
5. **Dependent Object Protection** - Shows impact before destructive operations
6. **Large Table Warnings** - Alerts for operations on tables >1M rows
7. **Non-Blocking Indexes** - CREATE INDEX CONCURRENTLY by default

### Safety Flags

Every execution tool accepts these common parameters:

- `dry_run` (boolean, default: `true`) - If true, validates without executing
- `schema_name` (string, default: `"public"`) - Target schema

---

## 🔧 Execution Tools

### 1. execute_alter_table

Modify table structure with comprehensive validation and schema diffing.

#### Function Signature
```python
execute_alter_table(
    table_name: str,              # Required: Table to alter
    alter_statement: str,         # Required: Complete ALTER TABLE statement
    schema_name: str = "public",  # Optional: Schema name
    dry_run: bool = True,         # Optional: Validate without executing
    show_schema_diff: bool = True # Optional: Show before/after comparison
) -> str  # Returns JSON
```

#### Parameters

**table_name** (string, required)
- Name of the table to alter
- Example: `"player_stats"`, `"team_games"`

**alter_statement** (string, required)
- Complete ALTER TABLE statement
- Can include multiple operations
- Examples:
  ```sql
  ALTER TABLE player_stats ADD COLUMN efficiency_rating FLOAT
  ALTER TABLE player_stats ADD COLUMN position VARCHAR(10) DEFAULT 'UNKNOWN'
  ALTER TABLE player_stats DROP COLUMN old_metric
  ALTER TABLE player_stats ALTER COLUMN points TYPE BIGINT
  ```

**schema_name** (string, optional, default: "public")
- Target schema
- Example: `"public"`, `"analytics"`, `"staging"`

**dry_run** (boolean, optional, default: true)
- `true`: Validates and previews without executing (rolled back)
- `false`: Actually executes the ALTER statement

**show_schema_diff** (boolean, optional, default: true)
- `true`: Returns before/after schema comparison
- `false`: Skips schema diff (faster)

#### Return Value

**Success (dry_run=true):**
```json
{
  "success": true,
  "message": "✅ Dry-run successful - changes NOT applied (rolled back)",
  "dry_run": true,
  "table": "public.player_stats",
  "duration_ms": 145,
  "table_stats": {
    "row_count": 150000,
    "size_mb": 45.2
  },
  "warnings": [
    "⚠️ Large table (150,000 rows, 45.20 MB) - operation may take significant time"
  ],
  "schema_diff": {
    "before": {
      "columns": [...],
      "indexes": [...]
    },
    "after": {
      "columns": [...],  // Includes new column
      "indexes": [...]
    }
  }
}
```

**Success (dry_run=false):**
```json
{
  "success": true,
  "message": "✅ ALTER TABLE executed successfully",
  "dry_run": false,
  "table": "public.player_stats",
  "duration_ms": 3420,
  "table_stats": {
    "row_count": 150000,
    "size_mb": 45.5  // Slightly larger after adding column
  },
  "warnings": [],
  "schema_diff": {
    "before": {...},
    "after": {...}
  }
}
```

**Error:**
```json
{
  "success": false,
  "error_code": "42P01",  // PostgreSQL error code
  "error": "relation \"player_stats\" does not exist",
  "statement": "ALTER TABLE player_stats ADD COLUMN..."
}
```

#### Workflow

**Step 1: Dry-Run and Review**
```python
# First, validate the operation
result = execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ADD COLUMN efficiency_rating FLOAT",
    dry_run=True  # Default
)

# Review:
# - schema_diff: See exactly what changes
# - warnings: Check for large table warnings
# - table_stats: Understand table size
```

**Step 2: Execute if Satisfied**
```python
# After reviewing, execute for real
result = execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ADD COLUMN efficiency_rating FLOAT",
    dry_run=False  # Explicit execution
)
```

#### Safety Features

- ✅ Validates syntax before execution
- ✅ Shows before/after schema comparison
- ✅ Warns for large tables (>1M rows)
- ✅ Warns for data type changes (potential data loss)
- ✅ Warns for NOT NULL without DEFAULT (will fail on existing rows)
- ✅ Logs to audit table (both dry-run and actual)
- ✅ Measures execution time

#### Common Use Cases

**Add Column:**
```python
execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ADD COLUMN per_36_minutes FLOAT",
    dry_run=False
)
```

**Add Column with Default:**
```python
execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ADD COLUMN is_starter BOOLEAN DEFAULT false",
    dry_run=False
)
```

**Modify Column Type:**
```python
# Dry-run first to check for data loss warnings
execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ALTER COLUMN points TYPE BIGINT",
    dry_run=True
)
```

**Drop Column:**
```python
execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats DROP COLUMN deprecated_metric",
    dry_run=False
)
```

**Add Constraint:**
```python
execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ADD CONSTRAINT positive_points CHECK (points >= 0)",
    dry_run=False
)
```

#### Error Handling

Common errors and solutions:

**Error: "relation does not exist"**
- Table name is incorrect or table doesn't exist
- Check with `list_tables()` first

**Error: "column already exists"**
- Column name conflicts with existing column
- Use `get_table_schema()` to see current columns

**Error: "cannot alter type of a column used by a view"**
- Views depend on this column
- Use `get_schema_diff()` to see dependent objects

---

### 2. execute_create_index

Create database indexes with performance estimation and safety checks.

#### Function Signature
```python
execute_create_index(
    index_name: str,                    # Required: Index name
    table_name: str,                    # Required: Table to index
    columns: str,                       # Required: Comma-separated columns
    schema_name: str = "public",        # Optional: Schema
    unique: bool = False,               # Optional: Unique constraint
    concurrent: bool = True,            # Optional: Non-blocking creation
    index_type: str = "BTREE",         # Optional: Index type
    where_clause: Optional[str] = None, # Optional: Partial index
    dry_run: bool = True                # Optional: Validate first
) -> str
```

#### Parameters

**index_name** (string, required)
- Name for the new index
- Convention: `idx_tablename_columns`
- Example: `"idx_player_stats_player_season"`, `"idx_games_date"`

**table_name** (string, required)
- Table to create index on
- Example: `"player_stats"`, `"games"`

**columns** (string, required)
- Comma-separated list of columns
- Example: `"player_id"`, `"player_id, season"`, `"game_date DESC"`

**schema_name** (string, optional, default: "public")
- Target schema

**unique** (boolean, optional, default: false)
- `true`: Create UNIQUE INDEX (enforces uniqueness)
- `false`: Create regular INDEX

**concurrent** (boolean, optional, default: true)
- `true`: CREATE INDEX CONCURRENTLY (non-blocking, recommended)
- `false`: Regular creation (locks table for writes)

**index_type** (string, optional, default: "BTREE")
- Index algorithm
- Options: `"BTREE"`, `"HASH"`, `"GIN"`, `"GIST"`, `"BRIN"`
- BTREE is most common and versatile

**where_clause** (string, optional, default: null)
- Optional WHERE clause for partial index
- Example: `"WHERE season = '2024-25'"`, `"WHERE active = true"`

**dry_run** (boolean, optional, default: true)
- `true`: Validates without creating
- `false`: Actually creates the index

#### Return Value

**Success:**
```json
{
  "success": true,
  "message": "✅ Index 'idx_player_season' created successfully",
  "dry_run": false,
  "index_name": "idx_player_season",
  "table": "public.player_stats",
  "columns": "player_id, season",
  "index_type": "BTREE",
  "unique": false,
  "concurrent": true,
  "duration_ms": 5420,
  "estimated_size_mb": 13.5,
  "table_rows": 150000
}
```

**Error:**
```json
{
  "success": false,
  "error_code": "DDL003",
  "error": "Index 'idx_player_season' already exists"
}
```

#### Workflow

**Step 1: Dry-Run**
```python
result = execute_create_index(
    index_name="idx_player_season",
    table_name="player_stats",
    columns="player_id, season",
    dry_run=True
)
# Check: estimated_size_mb, any warnings
```

**Step 2: Execute**
```python
result = execute_create_index(
    index_name="idx_player_season",
    table_name="player_stats",
    columns="player_id, season",
    concurrent=True,  // Non-blocking
    dry_run=False
)
```

#### Safety Features

- ✅ CONCURRENT by default (non-blocking)
- ✅ Checks if index already exists
- ✅ Estimates index size based on table size
- ✅ Validates column existence
- ✅ Logs to audit table

#### Common Use Cases

**Simple Single-Column Index:**
```python
execute_create_index(
    index_name="idx_player_id",
    table_name="player_stats",
    columns="player_id",
    dry_run=False
)
```

**Composite Index:**
```python
execute_create_index(
    index_name="idx_player_season_team",
    table_name="player_stats",
    columns="player_id, season, team_id",
    dry_run=False
)
```

**Unique Index:**
```python
execute_create_index(
    index_name="idx_unique_player_game",
    table_name="player_stats",
    columns="player_id, game_id",
    unique=True,
    dry_run=False
)
```

**Partial Index:**
```python
execute_create_index(
    index_name="idx_active_players",
    table_name="players",
    columns="player_id",
    where_clause="WHERE active = true",
    dry_run=False
)
```

**GIN Index (for JSON/Arrays):**
```python
execute_create_index(
    index_name="idx_metadata_gin",
    table_name="player_stats",
    columns="metadata_jsonb",
    index_type="GIN",
    dry_run=False
)
```

---

### 3. execute_drop_table_or_view

Drop tables or views with two-step confirmation for safety.

#### Function Signature
```python
execute_drop_table_or_view(
    object_name: str,                       # Required: Object to drop
    object_type: str = "TABLE",             # Optional: TABLE/VIEW/MATERIALIZED_VIEW
    schema_name: str = "public",            # Optional: Schema
    cascade: bool = False,                  # Optional: Drop dependents
    confirmation_token: Optional[str] = None, # Optional: Token from dry-run
    dry_run: bool = True                    # Optional: Analyze first
) -> str
```

#### Two-Step Process

This is **the only tool that requires a two-step process** for safety:

**Step 1: Dry-Run (Generate Token)**
```python
result = execute_drop_table_or_view(
    object_name="old_test_table",
    object_type="TABLE",
    dry_run=True  # Default
)

# Returns:
# - confirmation_token: "abc123..."
# - dependent_objects: [list of views, FKs, etc.]
# - impact: rows to delete, size, etc.
# - warnings: potential issues
```

**Step 2: Execute with Token**
```python
result = execute_drop_table_or_view(
    object_name="old_test_table",
    object_type="TABLE",
    confirmation_token="abc123...",  # From step 1
    dry_run=False  # Explicit execution
)
```

#### Parameters

**object_name** (string, required)
- Name of table/view to drop
- Example: `"old_table"`, `"deprecated_view"`

**object_type** (string, optional, default: "TABLE")
- Type of object
- Options: `"TABLE"`, `"VIEW"`, `"MATERIALIZED_VIEW"`

**schema_name** (string, optional, default: "public")
- Target schema

**cascade** (boolean, optional, default: false)
- `false`: Fails if dependent objects exist (RESTRICT mode)
- `true`: Also drops dependent objects (CASCADE mode)

**confirmation_token** (string, optional, default: null)
- Token received from dry-run step
- Required for actual execution (dry_run=false)
- Expires in 15 minutes

**dry_run** (boolean, optional, default: true)
- `true`: Analyzes impact and generates confirmation token
- `false`: Executes DROP (requires confirmation_token)

#### Return Value

**Dry-Run (Step 1):**
```json
{
  "success": true,
  "dry_run": true,
  "message": "⚠️ DRY-RUN: Object NOT dropped. Review impact below.",
  "object": "public.old_test_table",
  "object_type": "TABLE",
  "impact": {
    "rows_to_delete": 50000,
    "size_mb": 15.3,
    "dependent_objects": [
      {"object": "public.vw_player_summary", "dependency_type": "normal"},
      {"object": "public.idx_player_stats_fk", "dependency_type": "normal"}
    ],
    "cascade_enabled": false
  },
  "warnings": [
    "⚠️ Will delete 50,000 rows (15.30 MB)",
    "⚠️ 2 dependent objects exist - use cascade=true to drop them"
  ],
  "next_steps": [
    "1. Review dependent objects and impact above",
    "2. Export data if needed for backup",
    "3. To proceed, call again with:",
    "   - dry_run=false",
    "   - confirmation_token=\"abc123...\""
  ],
  "confirmation_token": "abc123def456...",
  "token_expires_at": "2025-01-06T01:18:45.123Z"
}
```

**Execution (Step 2):**
```json
{
  "success": true,
  "message": "✅ TABLE 'old_test_table' dropped successfully",
  "dry_run": false,
  "object": "public.old_test_table",
  "object_type": "TABLE",
  "cascade_used": false,
  "dependent_objects_dropped": 0,
  "rows_deleted": 50000,
  "duration_ms": 234
}
```

**Error (Missing Token):**
```json
{
  "success": false,
  "error_code": "DDL011",
  "error": "confirmation_token required for actual DROP execution. Run with dry_run=true first to get token."
}
```

**Error (Invalid Token):**
```json
{
  "success": false,
  "error_code": "DDL012",
  "error": "Invalid or expired confirmation token"
}
```

#### Workflow Example

**Complete Workflow:**
```python
# STEP 1: Analyze impact (dry-run)
result1 = execute_drop_table_or_view(
    object_name="old_test_table",
    dry_run=True
)

# Parse result to get token and review impact
import json
data = json.loads(result1)
print(f"Rows to delete: {data['impact']['rows_to_delete']}")
print(f"Dependent objects: {len(data['impact']['dependent_objects'])}")
token = data['confirmation_token']

# STEP 2: If satisfied, execute with token
result2 = execute_drop_table_or_view(
    object_name="old_test_table",
    confirmation_token=token,
    dry_run=False
)
```

#### Safety Features

- ✅ Two-step process prevents accidental deletion
- ✅ Shows all dependent objects before dropping
- ✅ Token expires in 15 minutes (prevents stale executions)
- ✅ Logs both dry-run and execution to audit table
- ✅ Reports rows deleted and duration
- ✅ CASCADE requires explicit flag

#### Common Use Cases

**Drop Simple Table:**
```python
# Step 1
result = execute_drop_table_or_view(
    object_name="temp_calculations",
    object_type="TABLE",
    dry_run=True
)

# Step 2 (after review)
result = execute_drop_table_or_view(
    object_name="temp_calculations",
    object_type="TABLE",
    confirmation_token="...",
    dry_run=False
)
```

**Drop View:**
```python
execute_drop_table_or_view(
    object_name="vw_old_report",
    object_type="VIEW",
    dry_run=True
)
# Then execute with token...
```

**Drop with CASCADE:**
```python
# Careful! This drops dependent objects too
execute_drop_table_or_view(
    object_name="parent_table",
    cascade=True,  # Will also drop dependent views/FKs
    dry_run=True  # Review first!
)
```

---

### 4. execute_ddl

Enhanced backward-compatible DDL execution (CREATE operations).

#### Function Signature
```python
execute_ddl(
    ddl_statement: str,  # Required: DDL statement
    dry_run: bool = True # Optional: Validate first
) -> str
```

#### Purpose

Executes CREATE TABLE, CREATE VIEW, CREATE MATERIALIZED VIEW operations.
This is the **backward-compatible** version of the original DDL server, now enhanced with dry-run mode.

#### Parameters

**ddl_statement** (string, required)
- Complete DDL statement
- Supported: CREATE TABLE, CREATE VIEW, CREATE MATERIALIZED VIEW, CREATE OR REPLACE VIEW
- Blocked: DROP, DELETE, TRUNCATE (use execute_drop_table_or_view instead)

**dry_run** (boolean, optional, default: true)
- `true`: Validates syntax without executing
- `false`: Actually executes the DDL

#### Return Value

**Success:**
```json
{
  "success": true,
  "message": "✅ DDL executed successfully",
  "dry_run": false,
  "object_type": "TABLE",
  "object_name": "player_efficiency",
  "statement": "CREATE TABLE player_efficiency...",
  "duration_ms": 234,
  "warnings": []
}
```

**Error:**
```json
{
  "success": false,
  "error_code": "DDL001",
  "error": "Dangerous operation 'DROP' is not allowed",
  "statement": "DROP TABLE..."
}
```

#### Common Use Cases

**Create Table:**
```python
execute_ddl(
    ddl_statement="""
        CREATE TABLE player_efficiency (
            player_id INT PRIMARY KEY,
            season VARCHAR(10),
            efficiency_rating FLOAT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """,
    dry_run=False
)
```

**Create View:**
```python
execute_ddl(
    ddl_statement="""
        CREATE VIEW vw_top_scorers AS
        SELECT player_name, AVG(points) as avg_points
        FROM player_stats
        GROUP BY player_name
        ORDER BY avg_points DESC
    """,
    dry_run=False
)
```

**Create Materialized View:**
```python
execute_ddl(
    ddl_statement="""
        CREATE MATERIALIZED VIEW mv_season_summary AS
        SELECT season, team_id, AVG(points) as avg_points
        FROM player_stats
        GROUP BY season, team_id
    """,
    dry_run=False
)
```

---

## 🧪 Validation & Intelligence Tools

### 5. validate_ddl_statement

Comprehensive DDL validation without execution.

#### Function Signature
```python
validate_ddl_statement(
    ddl_statement: str  # Required: DDL to validate
) -> str
```

#### Purpose

Validates DDL syntax, semantics, and safety **without executing anything**. Use this before any DDL operation to catch errors early.

#### Parameters

**ddl_statement** (string, required)
- Any DDL statement
- Can be CREATE, ALTER, DROP, etc.

#### Return Value

**Valid:**
```json
{
  "valid": true,
  "syntax_valid": true,
  "semantic_valid": true,
  "safety_valid": true,
  "errors": [],
  "warnings": [
    "Changing column type may cause data loss or require table rewrite"
  ],
  "validation_duration_ms": 45,
  "next_steps": [
    "Validation passed",
    "Review warnings and adjust if needed",
    "Execute with execute_ddl or specific operation tool"
  ]
}
```

**Invalid:**
```json
{
  "valid": false,
  "syntax_valid": false,
  "semantic_valid": true,
  "safety_valid": true,
  "errors": [
    "Syntax error: column \"player_id\" specified more than once"
  ],
  "warnings": [],
  "validation_duration_ms": 32,
  "next_steps": [
    "Fix any errors listed above"
  ]
}
```

#### Validation Layers

1. **Syntax Validation** - PostgreSQL parser check
2. **Semantic Validation** - Referenced objects exist
3. **Safety Validation** - No dangerous operations
4. **Performance Validation** - Potential performance issues

#### Use Cases

**Validate Before Execute:**
```python
# Step 1: Validate
result = validate_ddl_statement(
    ddl_statement="ALTER TABLE player_stats ADD COLUMN efficiency FLOAT"
)

# Step 2: If valid, execute
if json.loads(result)['valid']:
    execute_alter_table(...)
```

**Catch Errors Early:**
```python
# This will catch syntax errors before attempting execution
validate_ddl_statement(
    ddl_statement="ALTER TABLE player_stats ADD COLUMN player_id INT"  # Error: column exists
)
```

---

### 6. get_schema_diff

Get current schema snapshot or compare schemas.

#### Function Signature
```python
get_schema_diff(
    table_name: str,                     # Required: Table to analyze
    target_ddl: Optional[str] = None,    # Optional: DDL to compare
    schema_name: str = "public"          # Optional: Schema
) -> str
```

#### Purpose

Retrieves current schema structure (columns, indexes) for a table. Useful for understanding table structure before modifications.

#### Parameters

**table_name** (string, required)
- Table to analyze
- Example: `"player_stats"`, `"games"`

**target_ddl** (string, optional, default: null)
- Optional DDL to compare against
- **Note:** Full comparison not yet implemented - shows current schema only

**schema_name** (string, optional, default: "public")
- Target schema

#### Return Value

```json
{
  "table": "public.player_stats",
  "current_schema": {
    "columns": [
      {
        "column_name": "player_id",
        "data_type": "integer",
        "character_maximum_length": null,
        "is_nullable": "NO",
        "column_default": null
      },
      {
        "column_name": "points",
        "data_type": "numeric",
        "character_maximum_length": null,
        "is_nullable": "YES",
        "column_default": "0"
      }
    ],
    "indexes": [
      {
        "indexname": "player_stats_pkey",
        "indexdef": "CREATE UNIQUE INDEX player_stats_pkey ON public.player_stats USING btree (player_id, game_id)"
      },
      {
        "indexname": "idx_player_season",
        "indexdef": "CREATE INDEX idx_player_season ON public.player_stats USING btree (player_id, season)"
      }
    ]
  }
}
```

#### Use Cases

**Understand Table Structure:**
```python
get_schema_diff(table_name="player_stats")
```

**Before ALTER Operations:**
```python
# Check current schema before altering
schema = get_schema_diff(table_name="player_stats")
# Review columns to avoid conflicts
execute_alter_table(...)
```

---

## 📦 Migration Management Tools

### 7. create_migration

Create a version-tracked schema migration.

#### Function Signature
```python
create_migration(
    migration_name: str,                  # Required: Descriptive name
    ddl_statement: str,                   # Required: DDL to execute
    description: Optional[str] = None,    # Optional: Detailed description
    rollback_statement: Optional[str] = None, # Optional: Rollback DDL
    tags: Optional[str] = None            # Optional: Comma-separated tags
) -> str
```

#### Purpose

Creates a **tracked migration** in the `ddl_migration_history` table with:
- Automatic version numbering (timestamp-based: YYYYMMDDHHMMSSn)
- Validation results
- Optional rollback statement
- Tags for organization

#### Parameters

**migration_name** (string, required)
- Short descriptive name
- Convention: `"add_efficiency_column"`, `"create_summary_view"`
- Example: `"phase2_add_player_metrics"`

**ddl_statement** (string, required)
- The DDL to execute
- Any valid DDL (CREATE, ALTER, DROP, etc.)

**description** (string, optional, default: null)
- Longer description of changes
- Example: `"Adding efficiency rating column for Phase 2 analytics"`

**rollback_statement** (string, optional, default: null)
- DDL to undo this migration
- If not provided, rollback may not be possible
- Example: `"ALTER TABLE player_stats DROP COLUMN efficiency_rating"`

**tags** (string, optional, default: null)
- Comma-separated tags
- Example: `"phase2,analytics,production"`

#### Return Value

```json
{
  "success": true,
  "message": "Migration created successfully",
  "migration_id": 123,
  "version_number": 20250106011234,
  "migration_name": "add_efficiency_column",
  "status": "CREATED",
  "validation": {
    "syntax_valid": true,
    "safety_valid": true,
    "errors": [],
    "warnings": []
  },
  "next_steps": [
    "Review validation results above",
    "Execute migration: execute_migration(migration_id=123)",
    "Or query history: get_migration_history()"
  ]
}
```

#### Version Numbering

Migrations use **timestamp-based versioning**: `YYYYMMDDHHMMSSn`

Example: `20250106011234` =
- 2025-01-06 (date)
- 01:12:34 (time)
- Sequential number for same-second migrations

#### Use Cases

**Create Migration:**
```python
create_migration(
    migration_name="add_efficiency_column",
    ddl_statement="ALTER TABLE player_stats ADD COLUMN efficiency_rating FLOAT",
    description="Adding player efficiency metric for advanced analytics",
    rollback_statement="ALTER TABLE player_stats DROP COLUMN efficiency_rating",
    tags="phase2,analytics"
)
```

**Migration Without Rollback:**
```python
create_migration(
    migration_name="create_summary_view",
    ddl_statement="""
        CREATE VIEW vw_player_summary AS
        SELECT player_id, AVG(points) as avg_points
        FROM player_stats
        GROUP BY player_id
    """,
    rollback_statement="DROP VIEW vw_player_summary"
)
```

---

### 8. execute_migration

Execute a migration from the history table.

#### Function Signature
```python
execute_migration(
    migration_id: int,    # Required: Migration ID to execute
    dry_run: bool = True  # Optional: Test first
) -> str
```

#### Purpose

Executes a previously created migration, updating its status in the `ddl_migration_history` table.

#### Parameters

**migration_id** (integer, required)
- ID of migration to execute
- Get from `create_migration()` or `get_migration_history()`

**dry_run** (boolean, optional, default: true)
- `true`: Validates without executing (status: VALIDATED)
- `false`: Actually executes (status: SUCCESS or FAILED)

#### Return Value

**Success:**
```json
{
  "success": true,
  "message": "✅ Migration executed successfully",
  "migration_id": 123,
  "version_number": 20250106011234,
  "migration_name": "add_efficiency_column",
  "status": "SUCCESS",
  "dry_run": false,
  "duration_ms": 1234
}
```

**Error:**
```json
{
  "success": false,
  "error_code": "42701",
  "error": "column \"efficiency_rating\" of relation \"player_stats\" already exists",
  "migration_id": 123
}
```

#### Workflow

```python
# Step 1: Create migration
result1 = create_migration(
    migration_name="add_column",
    ddl_statement="ALTER TABLE player_stats ADD COLUMN new_col FLOAT",
    rollback_statement="ALTER TABLE player_stats DROP COLUMN new_col"
)
migration_id = json.loads(result1)['migration_id']

# Step 2: Dry-run
result2 = execute_migration(migration_id=migration_id, dry_run=True)

# Step 3: Execute
result3 = execute_migration(migration_id=migration_id, dry_run=False)
```

#### Status Tracking

Migrations progress through states:
- `CREATED` → `VALIDATED` → `EXECUTING` → `SUCCESS`
- Or: `CREATED` → `EXECUTING` → `FAILED`

---

### 9. rollback_migration

Rollback a migration using its stored rollback statement.

#### Function Signature
```python
rollback_migration(
    migration_id: int,     # Required: Migration to rollback
    confirm: bool = False  # Required: Must be true to execute
) -> str
```

#### Purpose

Undoes a migration by executing its `rollback_statement`. Updates migration status to `ROLLBACK_SUCCESS` or `ROLLBACK_FAILED`.

#### Parameters

**migration_id** (integer, required)
- ID of migration to rollback
- Must have a `rollback_statement`

**confirm** (boolean, required, default: false)
- **Must be true** to execute rollback
- Safety mechanism to prevent accidental rollbacks

#### Return Value

**Success:**
```json
{
  "success": true,
  "message": "Migration rolled back successfully",
  "migration_id": 123,
  "version_number": 20250106011234
}
```

**Error (No Confirmation):**
```json
{
  "success": false,
  "error": "Rollback requires confirm=true for safety"
}
```

**Error (No Rollback Statement):**
```json
{
  "success": false,
  "error": "No rollback statement available for this migration"
}
```

#### Use Cases

**Rollback Recent Migration:**
```python
# First, find the migration ID
history = get_migration_history(limit=10)

# Then rollback with confirmation
rollback_migration(
    migration_id=123,
    confirm=True  # Explicit confirmation required
)
```

**Safety:**
- Requires explicit `confirm=True`
- Only works if rollback statement was provided
- Updates migration status to track rollback
- Logs rollback to audit table

---

## 📊 Observability Tools

### 10. get_migration_history

Query migration history with filtering and pagination.

#### Function Signature
```python
get_migration_history(
    limit: int = 50,                   # Optional: Max results
    offset: int = 0,                   # Optional: Pagination offset
    status_filter: Optional[str] = None # Optional: Filter by status
) -> str
```

#### Purpose

Query the `ddl_migration_history` table to see all schema migrations.

#### Parameters

**limit** (integer, optional, default: 50)
- Maximum number of results
- Range: 1-500

**offset** (integer, optional, default: 0)
- Pagination offset
- For page 2: offset=50 (if limit=50)

**status_filter** (string, optional, default: null)
- Filter by status
- Options: `"CREATED"`, `"SUCCESS"`, `"FAILED"`, `"ROLLBACK_SUCCESS"`, etc.

#### Return Value

```json
{
  "success": true,
  "migrations": [
    {
      "migration_id": 123,
      "version_number": 20250106011234,
      "migration_name": "add_efficiency_column",
      "object_type": "TABLE",
      "object_name": "player_stats",
      "status": "SUCCESS",
      "executed_at": "2025-01-06T01:12:45Z",
      "execution_duration_ms": 1234,
      "error_message": null,
      "created_at": "2025-01-06T01:12:30Z"
    },
    // ... more migrations
  ],
  "pagination": {
    "total_count": 157,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

#### Use Cases

**Recent Migrations:**
```python
get_migration_history(limit=10)
```

**Failed Migrations:**
```python
get_migration_history(status_filter="FAILED")
```

**Paginate Results:**
```python
# Page 1
get_migration_history(limit=50, offset=0)

# Page 2
get_migration_history(limit=50, offset=50)

# Page 3
get_migration_history(limit=50, offset=100)
```

---

### 11. get_audit_log

Query the audit log with filtering and pagination.

#### Function Signature
```python
get_audit_log(
    limit: int = 100,                    # Optional: Max results
    offset: int = 0,                     # Optional: Pagination offset
    operation_type: Optional[str] = None, # Optional: Filter by operation
    success_only: Optional[bool] = None   # Optional: Filter by success
) -> str
```

#### Purpose

Query the `ddl_audit_log` table to see all DDL operations (including dry-runs).

#### Parameters

**limit** (integer, optional, default: 100)
- Maximum number of results
- Range: 1-1000

**offset** (integer, optional, default: 0)
- Pagination offset

**operation_type** (string, optional, default: null)
- Filter by operation type
- Options: `"ALTER_TABLE"`, `"CREATE_INDEX"`, `"DROP_TABLE"`, `"CREATE_TABLE"`, etc.

**success_only** (boolean, optional, default: null)
- `true`: Only successful operations
- `false`: Only failed operations
- `null`: All operations

#### Return Value

```json
{
  "success": true,
  "audit_records": [
    {
      "audit_id": 456,
      "execution_id": "a1b2c3d4-...",
      "operation_type": "ALTER_TABLE",
      "object_name": "player_stats",
      "is_dry_run": false,
      "success": true,
      "duration_ms": 1234,
      "error_message": null,
      "execution_started": "2025-01-06T01:12:45Z"
    },
    // ... more records
  ],
  "pagination": {
    "total_count": 523,
    "limit": 100,
    "offset": 0,
    "has_more": true
  }
}
```

#### Use Cases

**Recent Operations:**
```python
get_audit_log(limit=50)
```

**Recent ALTER TABLE Operations:**
```python
get_audit_log(
    operation_type="ALTER_TABLE",
    limit=20
)
```

**Failed Operations:**
```python
get_audit_log(
    success_only=False,
    limit=50
)
```

**Successful Operations Only:**
```python
get_audit_log(
    success_only=True,
    limit=100
)
```

**Paginate Results:**
```python
# Page 1
get_audit_log(limit=100, offset=0)

# Page 2
get_audit_log(limit=100, offset=100)
```

---

## 🔄 Legacy Tools (Backward Compatible)

### list_tables()
List all tables in the database. (Same as nba-mcp-server version)

### get_table_schema(table_name: str, schema_name: str = "public")
Get schema for a table. (Enhanced version with indexes)

---

## 🎯 Complete Workflows

### Workflow 1: Add a New Column

```python
# Step 1: Check current schema
schema = get_schema_diff(table_name="player_stats")

# Step 2: Validate DDL
validation = validate_ddl_statement(
    ddl_statement="ALTER TABLE player_stats ADD COLUMN efficiency_rating FLOAT"
)

# Step 3: Dry-run ALTER
dry_result = execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ADD COLUMN efficiency_rating FLOAT",
    dry_run=True
)
# Review schema_diff and warnings

# Step 4: Execute if satisfied
execute_alter_table(
    table_name="player_stats",
    alter_statement="ALTER TABLE player_stats ADD COLUMN efficiency_rating FLOAT",
    dry_run=False
)

# Step 5: Verify
get_audit_log(limit=1, operation_type="ALTER_TABLE")
```

### Workflow 2: Create Index for Performance

```python
# Step 1: Check table size
schema = get_table_schema(table_name="player_stats")

# Step 2: Dry-run index creation
dry_result = execute_create_index(
    index_name="idx_player_season",
    table_name="player_stats",
    columns="player_id, season",
    concurrent=True,
    dry_run=True
)
# Review estimated_size_mb

# Step 3: Create index
execute_create_index(
    index_name="idx_player_season",
    table_name="player_stats",
    columns="player_id, season",
    concurrent=True,  # Non-blocking
    dry_run=False
)
```

### Workflow 3: Drop Old Table Safely

```python
# Step 1: Analyze impact
dry_result = execute_drop_table_or_view(
    object_name="old_test_table",
    object_type="TABLE",
    dry_run=True
)
# Parse to get confirmation_token and review dependent_objects

# Step 2: Export data if needed (outside DDL server)
# SELECT * FROM old_test_table INTO backup_file

# Step 3: Execute DROP with token
execute_drop_table_or_view(
    object_name="old_test_table",
    object_type="TABLE",
    confirmation_token="abc123...",  # From step 1
    dry_run=False
)

# Step 4: Verify in audit log
get_audit_log(limit=1, operation_type="DROP_TABLE")
```

### Workflow 4: Create Tracked Migration with Rollback

```python
# Step 1: Create migration
create_result = create_migration(
    migration_name="phase2_add_analytics_columns",
    ddl_statement="""
        ALTER TABLE player_stats
        ADD COLUMN efficiency_rating FLOAT,
        ADD COLUMN per_36_minutes FLOAT
    """,
    description="Phase 2: Adding advanced analytics columns",
    rollback_statement="""
        ALTER TABLE player_stats
        DROP COLUMN efficiency_rating,
        DROP COLUMN per_36_minutes
    """,
    tags="phase2,analytics,production"
)
migration_id = json.loads(create_result)['migration_id']

# Step 2: Dry-run migration
execute_migration(migration_id=migration_id, dry_run=True)

# Step 3: Execute migration
execute_migration(migration_id=migration_id, dry_run=False)

# Step 4: If issues, rollback
if something_wrong:
    rollback_migration(migration_id=migration_id, confirm=True)

# Step 5: Check migration history
get_migration_history(limit=5)
```

---

## ⚠️ Error Codes Reference

| Code | Meaning | Common Cause |
|------|---------|--------------|
| DDL001 | Syntax Error | Invalid SQL syntax |
| DDL002 | Object Not Found | Table/column doesn't exist |
| DDL003 | Duplicate Object | Index/column already exists |
| DDL004 | Invalid Data Type | Unsupported data type |
| DDL005 | Missing Object | Required object doesn't exist |
| DDL006 | Foreign Key Violation | FK constraint prevents operation |
| DDL007 | Duplicate Index | Index with same definition exists |
| DDL008 | Insufficient Privileges | Database permissions issue |
| DDL009 | Table Too Large | Operation risky on large table |
| DDL010 | Dependent Objects Exist | Need CASCADE to drop |
| DDL011 | Confirmation Required | DROP needs confirmation token |
| DDL012 | Invalid Token | Token expired or incorrect |
| DDL013 | Breaking Change | Would break existing views |
| DDL014 | Rollback Not Available | No rollback statement provided |
| DDL015 | Performance Impact High | Operation may be slow |
| DDL999 | Unexpected Error | System error |

---

## ✅ Best Practices

### 1. Always Dry-Run First
```python
# GOOD
result = execute_alter_table(..., dry_run=True)  # Review first
result = execute_alter_table(..., dry_run=False) # Then execute

# BAD
result = execute_alter_table(..., dry_run=False) # Skip validation
```

### 2. Use Migrations for Production
```python
# GOOD - Trackable and reversible
create_migration(
    migration_name="add_column",
    ddl_statement="ALTER TABLE...",
    rollback_statement="ALTER TABLE DROP..."
)

# BAD - No tracking or rollback
execute_alter_table(..., dry_run=False)
```

### 3. Always Provide Rollback Statements
```python
# GOOD
create_migration(
    ...,
    rollback_statement="ALTER TABLE DROP COLUMN new_col"
)

# BAD
create_migration(
    ...,
    rollback_statement=None  # Can't undo!
)
```

### 4. Use CONCURRENT for Indexes
```python
# GOOD - Non-blocking
execute_create_index(..., concurrent=True)

# BAD - Blocks writes
execute_create_index(..., concurrent=False)
```

### 5. Check Audit Log After Operations
```python
# After any DDL operation
get_audit_log(limit=1, operation_type="ALTER_TABLE")
```

### 6. Tag Migrations for Organization
```python
create_migration(
    ...,
    tags="phase2,analytics,production"  # Easy to find later
)
```

### 7. Export Data Before Drops
```python
# GOOD
# 1. Export data (use query_database from nba-mcp-server)
# 2. execute_drop_table_or_view(...)

# BAD
# 1. execute_drop_table_or_view(...)  # Data lost!
```

---

## 📚 Additional Resources

**Configuration:**
- `/Users/ryanranft/nba-simulator-aws/ddl_config.json`

**Database Schema:**
- `/Users/ryanranft/nba-simulator-aws/ddl_schema_setup.sql`

**MCP Configuration:**
- `~/Library/Application Support/Claude/claude_desktop_config.json`

**Main Documentation:**
- `/Users/ryanranft/nba-simulator-aws/MCP_CONFIGURATION_GUIDE.md`

---

*Complete reference for all 11 DDL server tools with comprehensive examples and workflows.*
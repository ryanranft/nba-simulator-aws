# NBA DDL Server - MCP Integration Guide

**Created:** 2025-01-06
**Status:** ✅ Ready to Deploy

---

## 🎉 What Was Built

Your MCP configuration has been enhanced with:

1. **New DDL Server** - Execute CREATE TABLE and CREATE VIEW operations securely
2. **Hierarchical Secrets Migration** - Removed hardcoded database credentials
3. **Automated Deployment** - One-command installation

---

## 📁 Files Created

| File | Location | Purpose |
|------|----------|---------|
| `ddl_server.py` | `/Users/ryanranft/nba-simulator-aws/` | MCP server with execute_ddl tool |
| `claude_desktop_config_UPDATED.json` | `/Users/ryanranft/nba-simulator-aws/` | Updated MCP configuration |
| `migrate_mcp_config.sh` | `/Users/ryanranft/nba-simulator-aws/` | Automated deployment script |

---

## 🚀 Quick Start - Deploy Now

### Option 1: Automated Deployment (Recommended)

```bash
# Run the migration script
bash /Users/ryanranft/nba-simulator-aws/migrate_mcp_config.sh
```

**What it does:**
- ✅ Installs psycopg2-binary dependency
- ✅ Backs up your current config (timestamped)
- ✅ Validates new config and DDL server
- ✅ Deploys updated configuration
- ✅ Restarts Claude Desktop automatically

**Time:** ~1 minute

---

### Option 2: Manual Deployment

If you prefer manual control:

```bash
# 1. Install dependency
conda activate mcp-synthesis
pip install psycopg2-binary

# 2. Backup current config
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup

# 3. Deploy new config
cp /Users/ryanranft/nba-simulator-aws/claude_desktop_config_UPDATED.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 4. Restart Claude Desktop
osascript -e 'quit app "Claude"'
sleep 2
open -a Claude
```

---

## 🔧 What Changed

### Before (Old Config)
```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "env": {
        "RDS_HOST": "your-rds-endpoint.amazonaws.com",  ← Hardcoded!
        "RDS_PASSWORD": "your-plaintext-password"       ← Plaintext!
      }
    }
  }
}
```

### After (New Config)
```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "env": {
        "AWS_REGION": "us-east-1",
        "S3_BUCKET": "nba-sim-raw-data-lake"
      }
      // RDS credentials loaded from hierarchical secrets ✅
    },
    "nba-ddl-server": {
      "command": "python3",
      "args": ["ddl_server.py"]
      // Uses hierarchical secrets automatically ✅
    }
  }
}
```

---

## 🛠️ New DDL Server Tools

After deployment, you'll have these new MCP tools:

### 1. `execute_ddl` - Create Tables and Views

**Purpose:** Execute CREATE TABLE and CREATE VIEW operations

**Safety Features:**
- ✅ Only allows CREATE operations
- ❌ Blocks DROP, DELETE, TRUNCATE
- ✅ Validates SQL before execution
- ✅ Returns detailed error messages

**Example Usage:**

```sql
-- Create a new table
CREATE TABLE temporal_possession_stats (
    game_id INT,
    team_id INT,
    possession_count INT,
    avg_possession_duration FLOAT,
    PRIMARY KEY (game_id, team_id)
);

-- Create a materialized view
CREATE MATERIALIZED VIEW player_season_summary AS
SELECT
    player_id,
    season,
    AVG(points) as avg_points,
    AVG(rebounds) as avg_rebounds,
    COUNT(*) as games_played
FROM player_game_stats
GROUP BY player_id, season;
```

### 2. `list_tables` - View Database Tables

Lists all tables and views in the database.

### 3. `get_table_schema` - Inspect Table Structure

Shows column definitions for any table.

---

## 📝 Testing Your Installation

After deployment, start a **NEW conversation** in Claude Desktop and try:

### Test 1: Verify MCP Tools
```
Can you show me all available MCP tools?
```

**Expected:** You should see `execute_ddl`, `list_tables`, and `get_table_schema` from nba-ddl-server.

### Test 2: List Tables
```
Use list_tables to show all tables in the database
```

**Expected:** List of tables from your NBA database.

### Test 3: Create Test Table
```
Execute this DDL:
CREATE TABLE mcp_test_table (
    id SERIAL PRIMARY KEY,
    test_data TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Expected:** Success message with table created.

### Test 4: Verify Table Created
```
Use get_table_schema to show the schema for mcp_test_table
```

**Expected:** Column definitions for the new table.

---

## 🔐 Security Improvements

### Old System (Insecure)
- ❌ Passwords in plaintext in config file
- ❌ Credentials visible in Claude Desktop logs
- ❌ Risk of accidental exposure

### New System (Secure)
- ✅ Credentials in hierarchical secrets structure
- ✅ File permissions: 600 (owner read/write only)
- ✅ No plaintext passwords anywhere
- ✅ Automatic credential loading

**Credentials Location:**
```
/Users/ryanranft/Desktop/++/big_cat_bets_assets/
  sports_assets/big_cat_bets_simulators/NBA/
    nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
      RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env
      RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env
      ...
```

---

## 🔄 Rollback Instructions

If something goes wrong, rollback is easy:

```bash
# Find your backup (use actual timestamp)
ls -lt ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup.*

# Restore it
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup.20250106_123456 ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop
osascript -e 'quit app "Claude"'
sleep 2
open -a Claude
```

---

## 📊 MCP Servers Overview

After deployment, you'll have **3 MCP servers** running:

| Server | Purpose | Tools |
|--------|---------|-------|
| **nba-mcp-server** | Query database (read-only) | query_database, list_tables, get_table_schema, list_s3_files |
| **nba-ddl-server** | Schema management (DDL) | execute_ddl, list_tables, get_table_schema |
| **filesystem** | File operations | read, write, list files |

---

## 🎯 Use Cases

### Create Analytics Tables
```sql
CREATE TABLE game_analytics_summary AS
SELECT
    game_id,
    home_team_id,
    away_team_id,
    home_score,
    away_score,
    possession_diff,
    tempo_rating
FROM game_stats
WHERE season = '2024-25';
```

### Create Materialized Views for Reports
```sql
CREATE MATERIALIZED VIEW player_efficiency_ratings AS
SELECT
    player_id,
    player_name,
    AVG(per) as avg_per,
    AVG(ts_pct) as avg_ts_pct
FROM player_advanced_stats
GROUP BY player_id, player_name;
```

### Create Temporal Analytics Tables
```sql
CREATE TABLE temporal_possession_stats (
    game_id INT,
    team_id INT,
    quarter INT,
    possession_count INT,
    avg_possession_duration FLOAT,
    pace_factor FLOAT,
    PRIMARY KEY (game_id, team_id, quarter)
);
```

---

## 🛡️ Safety Features

### What's Allowed
- ✅ CREATE TABLE
- ✅ CREATE VIEW
- ✅ CREATE MATERIALIZED VIEW
- ✅ CREATE OR REPLACE VIEW
- ✅ CREATE INDEX

### What's Blocked
- ❌ DROP (tables, views, etc.)
- ❌ DELETE (data deletion)
- ❌ TRUNCATE (table truncation)
- ❌ ALTER COLUMN (data loss risk)
- ❌ RENAME (prevents confusion)

**If you need destructive operations, use a direct SQL client like `psql` or DBeaver.**

---

## 🐛 Troubleshooting

### Issue: "Failed to load database credentials"

**Solution:** Verify hierarchical secrets exist:
```bash
ls -la /Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production/
```

Expected files:
- `RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env`
- `RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env`
- `RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env`
- `RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW.env`
- `RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env`

---

### Issue: "execute_ddl tool not found"

**Solution:** Ensure you started a NEW conversation in Claude Desktop after deployment. MCP tools only load in new conversations.

---

### Issue: "Permission denied" when executing DDL

**Solution:** Verify database user has CREATE permissions:
```sql
-- Check permissions
SELECT has_table_privilege('your_username', 'pg_catalog.pg_class', 'CREATE');
```

---

### Issue: "Server connection timeout"

**Solution:**
1. Check database is accessible
2. Verify RDS security group allows connections
3. Test connection manually:
```bash
conda activate mcp-synthesis
python3 -c "
from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
config = get_database_config()
print(config)
"
```

---

## 📚 Additional Documentation

- **Hierarchical Secrets:** `nba-mcp-synthesis/.claude/CLAUDE.md`
- **MCP Server Code:** `nba-simulator-aws/ddl_server.py`
- **Updated Config:** `nba-simulator-aws/claude_desktop_config_UPDATED.json`

---

## ✅ Summary

**What you got:**
- 🎯 DDL execution capability in Claude Desktop
- 🔐 Secure credential management (hierarchical secrets)
- 🛡️ Safety validations (CREATE only, no destructive ops)
- 🚀 One-command deployment
- 🔄 Easy rollback

**Next steps:**
1. Run `bash /Users/ryanranft/nba-simulator-aws/migrate_mcp_config.sh`
2. Start NEW conversation in Claude Desktop
3. Try: "Use execute_ddl to create a test table"

---

**Questions or issues?** Check the troubleshooting section above or review the migration script output for details.

🎉 **Happy schema building!**
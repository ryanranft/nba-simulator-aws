# 🚀 DDL Server - Ready to Deploy!

## ✅ What's Been Built

1. **DDL Server** (`ddl_server.py`)
   - MCP server with `execute_ddl` tool
   - Supports CREATE TABLE and CREATE VIEW
   - Uses hierarchical secrets (secure)
   - Safety validations (blocks destructive operations)

2. **Updated MCP Config** (`claude_desktop_config_UPDATED.json`)
   - Adds nba-ddl-server
   - Migrates nba-mcp-server to hierarchical secrets
   - Removes hardcoded credentials

3. **Migration Script** (`migrate_mcp_config.sh`)
   - Automated deployment
   - Backs up current config
   - Validates new setup
   - Restarts Claude Desktop

---

## 🎯 Deploy Now - Copy/Paste This

```bash
# Single command deployment
bash /Users/ryanranft/nba-simulator-aws/migrate_mcp_config.sh
```

**That's it!** The script will:
- Install psycopg2-binary
- Backup your config
- Deploy new configuration
- Restart Claude Desktop

**Time:** ~1 minute

---

## 📝 After Deployment

**Start a NEW conversation** in Claude Desktop and say:

```
Can you show me all available MCP tools?
```

You should see these new tools:
- ✅ `execute_ddl` - Create tables and views
- ✅ `list_tables` - View database tables
- ✅ `get_table_schema` - Inspect table structure

---

## 🧪 Test It

Try creating a test table:

```
Execute this DDL:
CREATE TABLE mcp_test_table (
    id SERIAL PRIMARY KEY,
    test_data TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📚 Full Documentation

See: `/Users/ryanranft/nba-simulator-aws/DDL_SERVER_README.md`

---

## 🔄 Rollback (If Needed)

```bash
# Find your backup
ls -lt ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup.*

# Restore it (use actual timestamp)
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup.20250106_HHMMSS ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude
osascript -e 'quit app "Claude"'
open -a Claude
```

---

## 🎉 Ready!

All files created successfully:
- ✅ `/Users/ryanranft/nba-simulator-aws/ddl_server.py`
- ✅ `/Users/ryanranft/nba-simulator-aws/claude_desktop_config_UPDATED.json`
- ✅ `/Users/ryanranft/nba-simulator-aws/migrate_mcp_config.sh`
- ✅ `/Users/ryanranft/nba-simulator-aws/DDL_SERVER_README.md`

**Your existing MCP setup will continue working - this just adds DDL capability!**
# MCP Setup Instructions for Claude Desktop

**Purpose:** Enable Claude Desktop to access your NBA database and S3 bucket  
**Time Required:** 5-10 minutes  
**Status:** USER ACTION REQUIRED

---

## What is MCP?

Model Context Protocol (MCP) allows Claude Desktop to directly query your database and S3 bucket, enabling:
- Real-time database validation during refactoring
- Data integrity checks
- Production health monitoring
- Zero-risk testing (read-only by default)

---

## Setup Steps

### Step 1: Locate Your Config Template

The template is in your `nba-mcp-synthesis` project:
```
/Users/ryanranft/nba-mcp-synthesis/claude_desktop_config_TEMPLATE.json
```

### Step 2: Create System Config Directory

```bash
mkdir -p ~/Library/Application\ Support/Claude/
```

### Step 3: Copy Template to System Location

```bash
cp /Users/ryanranft/nba-mcp-synthesis/claude_desktop_config_TEMPLATE.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Step 4: Edit Configuration

Open the config file:
```bash
open -e ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Replace these placeholders with your actual values:
- `YOUR_DATABASE_HOST` → Your RDS endpoint
- `YOUR_DATABASE_NAME` → `nba_simulator`
- `YOUR_USERNAME` → Your database username
- `YOUR_PASSWORD` → Your database password
- `YOUR_S3_BUCKET` → `nba-sim-raw-data-lake`

### Step 5: Restart Claude Desktop

1. Quit Claude Desktop completely (⌘Q)
2. Wait 5 seconds
3. Relaunch Claude Desktop
4. Wait 15 seconds for MCP to initialize

### Step 6: Verify MCP Tools

Start a NEW conversation in Claude Desktop and ask:
```
What tools do you have available?
```

You should see 4 MCP tools:
- ✅ `query_database` - Execute SQL queries
- ✅ `list_tables` - List all database tables
- ✅ `get_table_schema` - Get table structure
- ✅ `list_s3_files` - Browse S3 bucket

---

## Test Your Setup

In Claude Desktop, try:

```sql
query_database("SELECT COUNT(*) FROM games")
```

Expected result: `44828` (or similar)

```
list_tables()
```

Expected: List of 40 tables

---

## Troubleshooting

### Issue: "Connection refused"
**Solution:** Check your database credentials and RDS endpoint

### Issue: "No MCP tools available"
**Solution:** 
1. Ensure config file is in correct location
2. Check JSON syntax is valid
3. Restart Claude Desktop

### Issue: "Permission denied"
**Solution:** Check database user has SELECT permission

---

## Security Note

The MCP configuration grants **read-only** access by default. Database writes require explicit permission in the config file.

---

## Next Steps

Once MCP is configured:
1. Use it to monitor refactoring health
2. Validate data integrity during changes
3. Run production tests safely

See: `docs/refactoring/REFACTORING_GUIDE.md` for usage during refactoring.

---

**Created:** October 28, 2025  
**For:** NBA Simulator AWS Production Refactoring


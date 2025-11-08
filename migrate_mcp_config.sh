#!/bin/bash
# MCP Configuration Migration Script
# Adds nba-ddl-server and migrates to hierarchical secrets

set -e  # Exit on error

echo "================================================================================"
echo "MCP Configuration Migration"
echo "================================================================================"
echo
echo "This script will:"
echo "  1. Install required dependencies (psycopg2-binary)"
echo "  2. Backup your current MCP config"
echo "  3. Deploy updated config with:"
echo "     - New nba-ddl-server (with execute_ddl)"
echo "     - Hierarchical secrets (removes hardcoded credentials)"
echo "  4. Restart Claude Desktop"
echo
echo "Press ENTER to continue, or Ctrl+C to cancel..."
read

# Configuration
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CURRENT_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
NEW_CONFIG="/Users/ryanranft/nba-simulator-aws/claude_desktop_config_UPDATED.json"
BACKUP_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json.backup.$(date +%Y%m%d_%H%M%S)"

# Step 1: Install dependencies
echo "Step 1: Installing dependencies..."
echo "--------------------------------------------------------------------------------"

# Activate conda environment
if [ -d "/Users/ryanranft/miniconda3/envs/mcp-synthesis" ]; then
    echo "✅ Conda environment 'mcp-synthesis' found"

    # Check if psycopg2-binary is installed
    if /Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/pip show psycopg2-binary &> /dev/null; then
        echo "✅ psycopg2-binary already installed"
    else
        echo "Installing psycopg2-binary..."
        /Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/pip install psycopg2-binary
        echo "✅ psycopg2-binary installed"
    fi
else
    echo "❌ Conda environment 'mcp-synthesis' not found"
    echo "   Please create it first: conda create -n mcp-synthesis python=3.11"
    exit 1
fi

echo

# Step 2: Backup current config
echo "Step 2: Backing up current config..."
echo "--------------------------------------------------------------------------------"

if [ -f "$CURRENT_CONFIG" ]; then
    cp "$CURRENT_CONFIG" "$BACKUP_CONFIG"
    echo "✅ Backup created: $BACKUP_CONFIG"
else
    echo "⚠️  No existing config found - this is a fresh install"
fi

echo

# Step 3: Validate new config
echo "Step 3: Validating new config..."
echo "--------------------------------------------------------------------------------"

if [ ! -f "$NEW_CONFIG" ]; then
    echo "❌ Updated config not found: $NEW_CONFIG"
    exit 1
fi

# Check if it's valid JSON
if ! python3 -c "import json; json.load(open('$NEW_CONFIG'))" 2>/dev/null; then
    echo "❌ Invalid JSON in new config"
    exit 1
fi

echo "✅ New config validated"

# Check DDL server exists
DDL_SERVER="/Users/ryanranft/nba-simulator-aws/ddl_server.py"
if [ ! -f "$DDL_SERVER" ]; then
    echo "❌ DDL server not found: $DDL_SERVER"
    exit 1
fi

echo "✅ DDL server found"

# Check hierarchical secrets exist
SECRETS_DIR="/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production"

if [ ! -d "$SECRETS_DIR" ]; then
    echo "⚠️  Warning: Hierarchical secrets directory not found: $SECRETS_DIR"
    echo "   The servers may not work until secrets are configured"
else
    echo "✅ Hierarchical secrets directory found"

    # Check for required secret files
    REQUIRED_SECRETS=(
        "RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env"
    )

    MISSING_SECRETS=()
    for secret in "${REQUIRED_SECRETS[@]}"; do
        if [ ! -f "$SECRETS_DIR/$secret" ]; then
            MISSING_SECRETS+=("$secret")
        fi
    done

    if [ ${#MISSING_SECRETS[@]} -gt 0 ]; then
        echo "⚠️  Warning: Missing secret files:"
        for secret in "${MISSING_SECRETS[@]}"; do
            echo "     - $secret"
        done
        echo "   You may need to configure these before the servers work"
    else
        echo "✅ All required secrets found"
    fi
fi

echo

# Step 4: Deploy new config
echo "Step 4: Deploying new config..."
echo "--------------------------------------------------------------------------------"

cp "$NEW_CONFIG" "$CURRENT_CONFIG"
echo "✅ Config deployed to: $CURRENT_CONFIG"

echo

# Step 5: Restart Claude Desktop
echo "Step 5: Restarting Claude Desktop..."
echo "--------------------------------------------------------------------------------"

# Check if Claude is running
if pgrep -x "Claude" > /dev/null; then
    echo "Closing Claude Desktop..."
    osascript -e 'quit app "Claude"' 2>/dev/null || true
    sleep 2
    echo "✅ Claude Desktop closed"
else
    echo "ℹ️  Claude Desktop was not running"
fi

echo "Starting Claude Desktop..."
open -a Claude
sleep 2
echo "✅ Claude Desktop started"

echo

# Step 6: Show summary
echo "================================================================================"
echo "✅ MIGRATION COMPLETE"
echo "================================================================================"
echo
echo "🎉 Your MCP configuration has been updated!"
echo
echo "What changed:"
echo "  ✅ nba-mcp-server: Now uses hierarchical secrets (secure)"
echo "  ✅ nba-ddl-server: New server added with execute_ddl tool"
echo "  ✅ filesystem: Unchanged"
echo
echo "Backup saved to:"
echo "  $BACKUP_CONFIG"
echo
echo "To test the new DDL server:"
echo "  1. Start a NEW conversation in Claude Desktop"
echo "  2. Say: 'List all tables in the database using list_tables'"
echo "  3. Then: 'Can you show me the available MCP tools?'"
echo "  4. You should see execute_ddl in the list"
echo
echo "Example DDL command to try:"
echo "  'Execute this DDL: CREATE TABLE test_table (id INT PRIMARY KEY, name TEXT)'"
echo
echo "To rollback if needed:"
echo "  cp '$BACKUP_CONFIG' '$CURRENT_CONFIG'"
echo "  Then restart Claude Desktop"
echo
echo "================================================================================"
echo "✨ Ready to use! Start a new conversation in Claude Desktop."
echo "================================================================================"
#!/bin/bash
# Deploy Enhanced DDL Server - Complete Deployment Script
#
# This script:
# 1. Deploys database schema (3 tables for migration/audit tracking)
# 2. Updates MCP config to use enhanced server
# 3. Restarts Claude Desktop
#
# Usage: bash deploy_enhanced_ddl.sh

set -e  # Exit on error

echo "================================================================================"
echo "Enhanced DDL Server Deployment"
echo "================================================================================"
echo
echo "This will deploy the enterprise DDL management system with:"
echo "  - ALTER TABLE, CREATE INDEX, DROP operations"
echo "  - Two-step confirmation for destructive operations"
echo "  - Complete migration tracking with rollback capability"
echo "  - Full audit logging for compliance"
echo "  - Schema diffing and validation"
echo "  - 11 MCP tools (vs 3 in basic version)"
echo
echo "Press ENTER to continue, or Ctrl+C to cancel..."
read

# ============================================================================
# STEP 1: Deploy Database Schema
# ============================================================================

echo ""
echo "Step 1: Deploying database schema..."
echo "--------------------------------------------------------------------------------"

# Load database credentials from hierarchical secrets
SECRETS_DIR="/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production"

if [ ! -d "$SECRETS_DIR" ]; then
    echo "❌ Secrets directory not found: $SECRETS_DIR"
    exit 1
fi

# Read credentials
DB_HOST=$(cat "$SECRETS_DIR/RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env" 2>/dev/null || echo "")
DB_PORT=$(cat "$SECRETS_DIR/RDS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env" 2>/dev/null || echo "5432")
DB_NAME=$(cat "$SECRETS_DIR/RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW.env" 2>/dev/null || echo "")
DB_USER=$(cat "$SECRETS_DIR/RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW.env" 2>/dev/null || echo "")
DB_PASS=$(cat "$SECRETS_DIR/RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env" 2>/dev/null || echo "")

if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASS" ]; then
    echo "❌ Failed to load database credentials from hierarchical secrets"
    exit 1
fi

echo "✅ Database credentials loaded from hierarchical secrets"
echo "   Host: ${DB_HOST:0:20}..."
echo "   Database: $DB_NAME"

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "⚠️  psql not found in PATH"
    echo "   Installing via conda..."

    conda activate mcp-synthesis 2>/dev/null || true
    conda install -y postgresql 2>/dev/null || pip install psycopg2-binary

    if ! command -v psql &> /dev/null; then
        echo "❌ Failed to install psql. Please install PostgreSQL client manually."
        echo "   macOS: brew install postgresql"
        echo "   Linux: sudo apt-get install postgresql-client"
        exit 1
    fi
fi

echo "✅ psql found"

# Deploy schema
echo ""
echo "Deploying schema (creating 3 tables, 4 views, 2 functions)..."

export PGPASSWORD="$DB_PASS"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f /Users/ryanranft/nba-simulator-aws/ddl_schema_setup.sql

if [ $? -eq 0 ]; then
    echo "✅ Database schema deployed successfully"
else
    echo "❌ Schema deployment failed"
    exit 1
fi

unset PGPASSWORD

# Verify tables created
echo ""
echo "Verifying deployment..."

PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt ddl_*" -t | wc -l > /tmp/table_count.txt
TABLE_COUNT=$(cat /tmp/table_count.txt | tr -d '[:space:]')

unset PGPASSWORD

if [ "$TABLE_COUNT" -ge "3" ]; then
    echo "✅ Verified: $TABLE_COUNT DDL tracking tables created"
else
    echo "⚠️  Warning: Expected 3 tables, found $TABLE_COUNT"
fi

# ============================================================================
# STEP 2: Update MCP Configuration
# ============================================================================

echo ""
echo "Step 2: Updating MCP configuration..."
echo "--------------------------------------------------------------------------------"

CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CURRENT_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
BACKUP_CONFIG="$CLAUDE_CONFIG_DIR/claude_desktop_config.json.backup.enhanced.$(date +%Y%m%d_%H%M%S)"

# Backup current config
if [ -f "$CURRENT_CONFIG" ]; then
    cp "$CURRENT_CONFIG" "$BACKUP_CONFIG"
    echo "✅ Config backed up to: $BACKUP_CONFIG"
fi

# Update config to use enhanced server
python3 << 'EOF'
import json
import sys

config_path = sys.argv[1]

# Read current config
with open(config_path) as f:
    config = json.load(f)

# Update nba-ddl-server to use enhanced version
if 'nba-ddl-server' in config['mcpServers']:
    config['mcpServers']['nba-ddl-server']['args'] = [
        '/Users/ryanranft/nba-simulator-aws/ddl_server_enhanced.py'
    ]
    print("✅ Updated nba-ddl-server to use enhanced version")
else:
    print("⚠️  nba-ddl-server not found in config")
    sys.exit(1)

# Write updated config
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

EOF "$CURRENT_CONFIG"

if [ $? -eq 0 ]; then
    echo "✅ MCP config updated successfully"
else
    echo "❌ Failed to update MCP config"
    exit 1
fi

# ============================================================================
# STEP 3: Restart Claude Desktop
# ============================================================================

echo ""
echo "Step 3: Restarting Claude Desktop..."
echo "--------------------------------------------------------------------------------"

if pgrep -x "Claude" > /dev/null; then
    echo "Closing Claude Desktop..."
    osascript -e 'quit app "Claude"' 2>/dev/null || true
    sleep 3
    echo "✅ Claude Desktop closed"
else
    echo "ℹ️  Claude Desktop was not running"
fi

echo "Starting Claude Desktop..."
open -a Claude
sleep 2
echo "✅ Claude Desktop started"

# ============================================================================
# DEPLOYMENT COMPLETE
# ============================================================================

echo ""
echo "================================================================================"
echo "✅ ENHANCED DDL SERVER DEPLOYED SUCCESSFULLY"
echo "================================================================================"
echo ""
echo "🎉 Your DDL server has been upgraded with enterprise features!"
echo ""
echo "What's New:"
echo "  ✅ 11 MCP tools (vs 3 basic tools)"
echo "  ✅ ALTER TABLE operations with validation"
echo "  ✅ CREATE INDEX with performance estimation"
echo "  ✅ DROP operations with two-step confirmation"
echo "  ✅ Complete migration tracking system"
echo "  ✅ Full audit logging (365-day retention)"
echo "  ✅ Schema diffing and validation"
echo "  ✅ Dry-run mode for ALL operations by default"
echo ""
echo "Database Tables Created:"
echo "  - ddl_migration_history (migration tracking)"
echo "  - ddl_audit_log (audit trail)"
echo "  - ddl_schema_version (schema snapshots)"
echo ""
echo "Configuration:"
echo "  - Safety: dry_run=true by default"
echo "  - Audit: 365-day retention"
echo "  - Versioning: Timestamp-based (YYYYMMDDHHMISS)"
echo "  - Confirmation: Required for destructive ops"
echo ""
echo "Backup saved to:"
echo "  $BACKUP_CONFIG"
echo ""
echo "================================================================================"
echo "Next Steps - Testing Your New DDL Server"
echo "================================================================================"
echo ""
echo "1. Start a NEW conversation in Claude Desktop"
echo ""
echo "2. Test ALTER TABLE:"
echo '   Say: "Use execute_alter_table to add a test column to a table"'
echo ""
echo "3. Test CREATE INDEX:"
echo '   Say: "Use execute_create_index to create an index"'
echo ""
echo "4. Test DROP with confirmation:"
echo '   Say: "Use execute_drop_table_or_view to analyze dropping a test table"'
echo ""
echo "5. Create a migration:"
echo '   Say: "Use create_migration to create a tracked schema migration"'
echo ""
echo "6. Query audit log:"
echo '   Say: "Use get_audit_log to show recent DDL operations"'
echo ""
echo "================================================================================"
echo "Documentation"
echo "================================================================================"
echo ""
echo "Full documentation:"
echo "  /Users/ryanranft/nba-simulator-aws/DDL_SERVER_README.md"
echo ""
echo "Configuration:"
echo "  /Users/ryanranft/nba-simulator-aws/ddl_config.json"
echo ""
echo "Schema SQL:"
echo "  /Users/ryanranft/nba-simulator-aws/ddl_schema_setup.sql"
echo ""
echo "================================================================================"
echo "Rollback Instructions (if needed)"
echo "================================================================================"
echo ""
echo "To rollback to basic DDL server:"
echo "  cp '$BACKUP_CONFIG' '$CURRENT_CONFIG'"
echo "  osascript -e 'quit app \"Claude\"'"
echo "  open -a Claude"
echo ""
echo "================================================================================"
echo "🚀 All set! Start a new conversation in Claude Desktop to begin using"
echo "   your enhanced DDL management system!"
echo "================================================================================"
echo ""
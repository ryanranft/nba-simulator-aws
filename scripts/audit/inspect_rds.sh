#!/bin/bash

##############################################################################
# RDS Deep Inspection Module
##############################################################################
#
# Purpose: Validate RDS PostgreSQL table health and row counts
# Output: Table validation report with anomaly detection
# Cost: $0 (minimal RDS queries)
#
# Usage:
#   bash scripts/audit/inspect_rds.sh [--test]
#
# Options:
#   --test    Test RDS connection only (no validation)
#
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/ryanranft/nba-simulator-aws"

# Parse arguments
TEST_MODE=false
if [ "$1" == "--test" ]; then
    TEST_MODE=true
fi

# Load RDS credentials from environment (support both RDS_* and DB_* naming)
export DB_HOST="${DB_HOST:-$RDS_HOST}"
export DB_USER="${DB_USER:-$RDS_USERNAME}"
export DB_PASSWORD="${DB_PASSWORD:-$RDS_PASSWORD}"
export DB_NAME="${DB_NAME:-${RDS_DATABASE:-nba_simulator}}"

if [ -z "$DB_HOST" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}❌ RDS credentials not found${NC}"
    echo "Expected environment variables:"
    echo "  RDS_HOST, RDS_USERNAME, RDS_PASSWORD, RDS_DATABASE"
    echo "  OR: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME"
    echo ""
    echo "Load with: source /Users/ryanranft/nba-sim-credentials.env"
    exit 1
fi

##############################################################################
# Test RDS Connection
##############################################################################

if [ "$TEST_MODE" = true ]; then
    echo -e "${BLUE}Testing RDS connection...${NC}"

    if python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=5432,
        database=os.environ.get('DB_NAME', 'nba_simulator'),
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        sslmode='require',
        connect_timeout=10
    )
    print('✅ Connection successful')
    conn.close()
    exit(0)
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
" 2>&1; then
        echo -e "${GREEN}✅ RDS connection test passed${NC}"
        exit 0
    else
        echo -e "${RED}❌ RDS connection test failed${NC}"
        exit 1
    fi
fi

##############################################################################
# Define Expected Baselines
##############################################################################

# Expected row counts (from MASTER_DATA_INVENTORY.md as of Oct 11, 2025)
declare -A EXPECTED_COUNTS=(
    ["temporal_events"]="14114617"
    ["unified_play_by_play"]="13074829"
    ["hoopr_play_by_play"]="13074829"
    ["play_by_play"]="6781155"
    ["hoopr_player_box"]="785505"
    ["box_score_players"]="408833"
    ["hoopr_team_box"]="59670"
    ["games"]="44828"
    ["unified_schedule"]="40652"
    ["hoopr_schedule"]="30758"
    ["box_score_teams"]="15900"
    ["player_biographical"]="3632"
    ["team_seasons"]="952"
    ["teams"]="87"
    ["data_source_coverage"]="33"
)

# Critical tables that should have data
CRITICAL_EMPTY=(
    "game_states"
    "player_game_stats"
    "players"
    "team_game_stats"
)

##############################################################################
# Query RDS for Actual Row Counts
##############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}RDS Deep Inspection${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Querying RDS for table statistics..."
echo ""

# Use Python with psycopg2 to query row counts
(python3 <<'PYTHON_SCRIPT'
import psycopg2
import os
import sys

try:
    # Connect to RDS
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=5432,
        database=os.environ.get('DB_NAME', 'nba_simulator'),
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        sslmode='require'
    )

    cur = conn.cursor()

    # Query all table row counts
    cur.execute("""
        SELECT
            schemaname,
            relname AS tablename,
            n_live_tup AS row_count
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC;
    """)

    results = cur.fetchall()

    # Output in format: table_name|row_count
    for schema, table, count in results:
        print(f"{table}|{count}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"ERROR|{e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT
) > /tmp/rds_row_counts.txt 2>&1

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to query RDS${NC}"
    exit 1
fi

# Check for errors
if grep -q "^ERROR|" /tmp/rds_row_counts.txt; then
    echo -e "${RED}❌ RDS query failed:${NC}"
    cat /tmp/rds_row_counts.txt | grep "^ERROR|" | cut -d'|' -f2
    exit 1
fi

##############################################################################
# Validate Row Counts
##############################################################################

ISSUES_FOUND=0

echo -e "${BLUE}Validating populated tables:${NC}"
echo ""

# Validate each expected table
for table in "${!EXPECTED_COUNTS[@]}"; do
    expected="${EXPECTED_COUNTS[$table]}"

    # Get actual count from query results
    actual=$(grep "^${table}|" /tmp/rds_row_counts.txt | cut -d'|' -f2)

    if [ -z "$actual" ]; then
        echo -e "${YELLOW}⚠️  $table: Table not found in RDS${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        continue
    fi

    # Calculate difference
    diff=$((actual - expected))

    # Calculate percentage difference
    if [ $expected -gt 0 ]; then
        pct_diff=$(awk "BEGIN {printf \"%.1f\", ($diff / $expected) * 100}")
    else
        pct_diff="N/A"
    fi

    # Format numbers with commas
    actual_fmt=$(printf "%'d" $actual)
    expected_fmt=$(printf "%'d" $expected)

    # Check for significant differences (>10%)
    if [ "$pct_diff" != "N/A" ]; then
        abs_pct=$(echo $pct_diff | tr -d -)
        if (( $(echo "$abs_pct > 10" | bc -l) )); then
            echo -e "${YELLOW}⚠️  $table: $actual_fmt rows (expected: $expected_fmt) ${pct_diff}%${NC}"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
        else
            echo -e "${GREEN}✅ $table: $actual_fmt rows${NC}"
        fi
    else
        echo -e "${GREEN}✅ $table: $actual_fmt rows${NC}"
    fi
done

echo ""
echo -e "${BLUE}Checking critical empty tables:${NC}"
echo ""

# Check critical tables that should be populated
for table in "${CRITICAL_EMPTY[@]}"; do
    actual=$(grep "^${table}|" /tmp/rds_row_counts.txt | cut -d'|' -f2)

    if [ -z "$actual" ]; then
        echo -e "${YELLOW}⚠️  $table: Table not found in RDS${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        continue
    fi

    if [ "$actual" -eq 0 ]; then
        echo -e "${RED}❌ $table: EMPTY (expected data) - CRITICAL${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
    else
        actual_fmt=$(printf "%'d" $actual)
        echo -e "${GREEN}✅ $table: $actual_fmt rows (populated)${NC}"
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Summary
if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ RDS Deep Inspection: All checks passed${NC}"
    echo -e "${GREEN}   All tables have expected row counts${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  RDS Deep Inspection: $ISSUES_FOUND issue(s) detected${NC}"
    echo -e "${YELLOW}   Review warnings above${NC}"
    exit 1
fi

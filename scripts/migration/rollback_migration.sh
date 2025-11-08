#!/bin/bash
#
# Rollback Migration Script
#
# Removes all migrated data from raw_data schema.
# Master schema remains untouched.
#
# Usage:
#   bash scripts/migration/rollback_migration.sh
#   bash scripts/migration/rollback_migration.sh --confirm
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for --confirm flag
CONFIRMED=false
if [[ "$1" == "--confirm" ]]; then
    CONFIRMED=true
fi

echo -e "${YELLOW}======================================================================${NC}"
echo -e "${YELLOW}Migration Rollback Script${NC}"
echo -e "${YELLOW}======================================================================${NC}"
echo ""

# Load database credentials
export POSTGRES_HOST=${POSTGRES_HOST:-localhost}
export POSTGRES_PORT=${POSTGRES_PORT:-5432}
export POSTGRES_DB=${POSTGRES_DB:-nba_simulator}
export POSTGRES_USER=${POSTGRES_USER:-ryanranft}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-}

echo "Database: $POSTGRES_DB @ $POSTGRES_HOST:$POSTGRES_PORT"
echo ""

# Check counts before rollback
echo -e "${YELLOW}Current state:${NC}"
psql -U $POSTGRES_USER -d $POSTGRES_DB -h $POSTGRES_HOST -p $POSTGRES_PORT -c "\
SELECT
    'raw_data.nba_games' as table_name,
    COUNT(*) as row_count
FROM raw_data.nba_games
UNION ALL
SELECT
    'raw_data.nba_misc',
    COUNT(*)
FROM raw_data.nba_misc
WHERE entity_type = 'file_validation';
"

echo ""

if [ "$CONFIRMED" = false ]; then
    echo -e "${RED}⚠️  WARNING: This will DELETE all migrated data from raw_data schema!${NC}"
    echo -e "${RED}⚠️  Master schema will remain untouched.${NC}"
    echo ""
    read -p "Are you sure you want to proceed? (type 'yes' to confirm): " response

    if [[ "$response" != "yes" ]]; then
        echo ""
        echo -e "${GREEN}Rollback cancelled.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}Starting rollback...${NC}"
echo ""

# Delete migrated games
echo "Deleting migrated games..."
psql -U $POSTGRES_USER -d $POSTGRES_DB -h $POSTGRES_HOST -p $POSTGRES_PORT -c "\
DELETE FROM raw_data.nba_games
WHERE metadata->'migration'->>'migration_version' = '1.0.0';
"

# Delete migrated file validations
echo "Deleting migrated file validations..."
psql -U $POSTGRES_USER -d $POSTGRES_DB -h $POSTGRES_HOST -p $POSTGRES_PORT -c "\
DELETE FROM raw_data.nba_misc
WHERE metadata->'migration'->>'migration_version' = '1.0.0';
"

# Verify rollback
echo ""
echo -e "${YELLOW}After rollback:${NC}"
psql -U $POSTGRES_USER -d $POSTGRES_DB -h $POSTGRES_HOST -p $POSTGRES_PORT -c "\
SELECT
    'raw_data.nba_games' as table_name,
    COUNT(*) as row_count
FROM raw_data.nba_games
UNION ALL
SELECT
    'raw_data.nba_misc',
    COUNT(*)
FROM raw_data.nba_misc
WHERE entity_type = 'file_validation';
"

echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}✅ Rollback complete!${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo "Master schema remains untouched. You can re-run migration at any time."
echo ""

# Remove checkpoint file if exists
if [ -f "migration_checkpoint.json" ]; then
    echo "Removing checkpoint file..."
    rm migration_checkpoint.json
    echo "✓ Checkpoint file removed"
fi

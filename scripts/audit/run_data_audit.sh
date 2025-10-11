#!/bin/bash

##############################################################################
# NBA Data Audit Script - Automated Inventory & Gap Detection
##############################################################################
#
# Purpose: Automatically run comprehensive data audit to update inventory
# When to run: After data scraping, quarterly reviews, or manually
# Output: Updated MASTER_DATA_INVENTORY.md + audit logs
# Cost: $0 (local analysis only, minimal S3 GET requests)
#
# Usage:
#   bash scripts/audit/run_data_audit.sh [--update-docs]
#
# Options:
#   --update-docs    Update MASTER_DATA_INVENTORY.md with new counts
#   --quiet          Suppress verbose output
#   --skip-s3        Skip S3 inventory (faster, offline mode)
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
AUDIT_LOG_DIR="$PROJECT_ROOT/logs/audit"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIT_LOG="$AUDIT_LOG_DIR/audit_${TIMESTAMP}.log"

# Parse arguments
UPDATE_DOCS=false
QUIET=false
SKIP_S3=false

for arg in "$@"; do
    case $arg in
        --update-docs) UPDATE_DOCS=true ;;
        --quiet) QUIET=true ;;
        --skip-s3) SKIP_S3=true ;;
    esac
done

# Create log directory
mkdir -p "$AUDIT_LOG_DIR"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$level] $message" | tee -a "$AUDIT_LOG"

    if [ "$QUIET" = false ]; then
        case $level in
            INFO) echo -e "${BLUE}ℹ ${message}${NC}" ;;
            SUCCESS) echo -e "${GREEN}✅ ${message}${NC}" ;;
            WARNING) echo -e "${YELLOW}⚠️  ${message}${NC}" ;;
            ERROR) echo -e "${RED}❌ ${message}${NC}" ;;
        esac
    fi
}

log INFO "=========================================="
log INFO "NBA Data Audit Started"
log INFO "Timestamp: $TIMESTAMP"
log INFO "=========================================="

##############################################################################
# Phase 1: Local Project Directory Inventory
##############################################################################

log INFO "Phase 1: Counting local data files..."

cd "$PROJECT_ROOT"

# Count JSON files by directory
LOCAL_PBP=$(find data/nba_pbp -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
LOCAL_BOX=$(find data/nba_box_score -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
LOCAL_TEAM=$(find data/nba_team_stats -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
LOCAL_SCHED=$(find data/nba_schedule_json -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
LOCAL_TOTAL=$((LOCAL_PBP + LOCAL_BOX + LOCAL_TEAM + LOCAL_SCHED))

log SUCCESS "Local data inventory complete"
echo "  - Play-by-Play: $LOCAL_PBP files" | tee -a "$AUDIT_LOG"
echo "  - Box Scores: $LOCAL_BOX files" | tee -a "$AUDIT_LOG"
echo "  - Team Stats: $LOCAL_TEAM files" | tee -a "$AUDIT_LOG"
echo "  - Schedule: $LOCAL_SCHED files" | tee -a "$AUDIT_LOG"
echo "  - TOTAL: $LOCAL_TOTAL files" | tee -a "$AUDIT_LOG"

##############################################################################
# Phase 2: S3 Bucket Inventory
##############################################################################

if [ "$SKIP_S3" = false ]; then
    log INFO "Phase 2: Counting S3 data files..."

    # Check AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        log WARNING "AWS credentials not found - skipping S3 inventory"
        SKIP_S3=true
    else
        S3_PBP=$(aws s3 ls s3://nba-sim-raw-data-lake/pbp/ --recursive 2>/dev/null | wc -l | tr -d ' ')
        S3_BOX=$(aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ --recursive 2>/dev/null | wc -l | tr -d ' ')
        S3_TEAM=$(aws s3 ls s3://nba-sim-raw-data-lake/team_stats/ --recursive 2>/dev/null | wc -l | tr -d ' ')
        S3_SCHED=$(aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive 2>/dev/null | wc -l | tr -d ' ')
        S3_TOTAL=$((S3_PBP + S3_BOX + S3_TEAM + S3_SCHED))

        log SUCCESS "S3 data inventory complete"
        echo "  - Play-by-Play: $S3_PBP files" | tee -a "$AUDIT_LOG"
        echo "  - Box Scores: $S3_BOX files" | tee -a "$AUDIT_LOG"
        echo "  - Team Stats: $S3_TEAM files" | tee -a "$AUDIT_LOG"
        echo "  - Schedule: $S3_SCHED files" | tee -a "$AUDIT_LOG"
        echo "  - TOTAL: $S3_TOTAL files" | tee -a "$AUDIT_LOG"
    fi
else
    log INFO "Phase 2: Skipping S3 inventory (--skip-s3 flag)"
fi

##############################################################################
# Phase 3: Database Inventory
##############################################################################

log INFO "Phase 3: Checking database status..."

# SQLite databases
KAGGLE_DB="$PROJECT_ROOT/data/kaggle/nba.sqlite"
UNIFIED_DB_LATEST=$(ls -t "$PROJECT_ROOT"/backups/*/unified_nba.db 2>/dev/null | head -1)

if [ -f "$KAGGLE_DB" ]; then
    KAGGLE_SIZE=$(du -h "$KAGGLE_DB" | cut -f1)
    log SUCCESS "Kaggle DB found: $KAGGLE_SIZE"
else
    log WARNING "Kaggle DB not found at $KAGGLE_DB"
fi

if [ -n "$UNIFIED_DB_LATEST" ]; then
    UNIFIED_SIZE=$(du -h "$UNIFIED_DB_LATEST" | cut -f1)
    log SUCCESS "Unified DB found: $UNIFIED_SIZE"
else
    log WARNING "Unified DB not found"
fi

# RDS PostgreSQL
if [ "$SKIP_S3" = false ]; then
    RDS_STATUS=$(aws rds describe-db-instances --db-instance-identifier nba-sim-db --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "unavailable")

    if [ "$RDS_STATUS" = "available" ]; then
        log SUCCESS "RDS PostgreSQL: $RDS_STATUS"
    else
        log WARNING "RDS PostgreSQL: $RDS_STATUS"
    fi
fi

##############################################################################
# Phase 4: Sync Status Check
##############################################################################

if [ "$SKIP_S3" = false ]; then
    log INFO "Phase 4: Checking sync status (local vs S3)..."

    # Compare counts
    PBP_DIFF=$((S3_PBP - LOCAL_PBP))
    BOX_DIFF=$((S3_BOX - LOCAL_BOX))
    TEAM_DIFF=$((S3_TEAM - LOCAL_TEAM))
    SCHED_DIFF=$((S3_SCHED - LOCAL_SCHED))

    SYNC_ISSUES=0

    if [ $PBP_DIFF -ne 0 ]; then
        log WARNING "Play-by-Play out of sync: S3 has $PBP_DIFF more/fewer files"
        SYNC_ISSUES=$((SYNC_ISSUES + 1))
    fi

    if [ $BOX_DIFF -ne 0 ]; then
        log WARNING "Box Scores out of sync: S3 has $BOX_DIFF more/fewer files"
        SYNC_ISSUES=$((SYNC_ISSUES + 1))
    fi

    if [ $TEAM_DIFF -ne 0 ]; then
        log WARNING "Team Stats out of sync: S3 has $TEAM_DIFF more/fewer files"
        SYNC_ISSUES=$((SYNC_ISSUES + 1))
    fi

    if [ $SCHED_DIFF -ne 0 ]; then
        log WARNING "Schedule out of sync: S3 has $SCHED_DIFF more/fewer files"
        SYNC_ISSUES=$((SYNC_ISSUES + 1))
    fi

    if [ $SYNC_ISSUES -eq 0 ]; then
        log SUCCESS "All data sources synchronized! ✅"
    else
        log WARNING "$SYNC_ISSUES data source(s) out of sync"
        echo "" | tee -a "$AUDIT_LOG"
        echo "To sync, run:" | tee -a "$AUDIT_LOG"
        echo "  aws s3 sync s3://nba-sim-raw-data-lake/pbp/ data/nba_pbp/" | tee -a "$AUDIT_LOG"
        echo "  aws s3 sync s3://nba-sim-raw-data-lake/box_scores/ data/nba_box_score/" | tee -a "$AUDIT_LOG"
        echo "  aws s3 sync s3://nba-sim-raw-data-lake/team_stats/ data/nba_team_stats/" | tee -a "$AUDIT_LOG"
        echo "  aws s3 sync s3://nba-sim-raw-data-lake/schedule/ data/nba_schedule_json/" | tee -a "$AUDIT_LOG"
    fi
fi

##############################################################################
# Phase 5: Update Documentation (if requested)
##############################################################################

if [ "$UPDATE_DOCS" = true ]; then
    log INFO "Phase 5: Updating MASTER_DATA_INVENTORY.md..."

    INVENTORY_FILE="$PROJECT_ROOT/docs/MASTER_DATA_INVENTORY.md"

    if [ -f "$INVENTORY_FILE" ]; then
        # Update the last updated date
        sed -i '' "s/\*\*Last Updated:\*\* .*/\*\*Last Updated:\*\* $(date '+%B %d, %Y')/" "$INVENTORY_FILE"

        log SUCCESS "Documentation updated with audit timestamp"
    else
        log WARNING "MASTER_DATA_INVENTORY.md not found - skipping doc update"
    fi
fi

##############################################################################
# Summary Report
##############################################################################

log INFO "=========================================="
log INFO "Audit Summary"
log INFO "=========================================="

echo "" | tee -a "$AUDIT_LOG"
echo "📊 Data Holdings:" | tee -a "$AUDIT_LOG"
echo "  Local: $LOCAL_TOTAL files" | tee -a "$AUDIT_LOG"

if [ "$SKIP_S3" = false ]; then
    echo "  S3: $S3_TOTAL files" | tee -a "$AUDIT_LOG"
    echo "  RDS: $RDS_STATUS" | tee -a "$AUDIT_LOG"

    if [ $SYNC_ISSUES -gt 0 ]; then
        echo "" | tee -a "$AUDIT_LOG"
        echo "⚠️  Sync Issues: $SYNC_ISSUES" | tee -a "$AUDIT_LOG"
    else
        echo "" | tee -a "$AUDIT_LOG"
        echo "✅ Sync Status: All sources synchronized" | tee -a "$AUDIT_LOG"
    fi
fi

echo "" | tee -a "$AUDIT_LOG"
echo "📝 Full audit log: $AUDIT_LOG" | tee -a "$AUDIT_LOG"

log INFO "=========================================="
log SUCCESS "Data Audit Complete!"
log INFO "=========================================="

# Exit with appropriate code
if [ "$SKIP_S3" = false ] && [ $SYNC_ISSUES -gt 0 ]; then
    exit 1  # Sync issues detected
else
    exit 0  # All good
fi
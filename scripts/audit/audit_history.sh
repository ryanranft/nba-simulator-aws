#!/bin/bash

##############################################################################
# Audit History Tracker
##############################################################################
#
# Purpose: Track audit results over time to identify trends and anomalies
# Output: CSV log + trend analysis
# Cost: $0 (local analysis only)
#
# Usage:
#   bash scripts/audit/audit_history.sh [--summary|--compare|--alert]
#
# Options:
#   --summary    Show overall summary statistics
#   --compare    Compare current vs last audit
#   --alert      Alert on anomalies (file count drops >5%)
#   (no option)  Log current audit results
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
HISTORY_FILE="$PROJECT_ROOT/logs/audit/audit_history.csv"
TIMESTAMP=$(date +%Y-%m-%d\ %H:%M:%S)

# Create history file if doesn't exist
mkdir -p "$(dirname "$HISTORY_FILE")"
if [ ! -f "$HISTORY_FILE" ]; then
    echo "timestamp,local_pbp,local_box,local_team,local_sched,local_total,s3_pbp,s3_box,s3_team,s3_sched,s3_total,rds_status,sync_status" > "$HISTORY_FILE"
fi

# Parse mode
MODE="log"
if [ "$1" == "--summary" ]; then
    MODE="summary"
elif [ "$1" == "--compare" ]; then
    MODE="compare"
elif [ "$1" == "--alert" ]; then
    MODE="alert"
elif [ "$1" == "--diff" ]; then
    # Diff mode - delegate to audit_diff.sh
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    bash "$SCRIPT_DIR/audit_diff.sh" "$2"
    exit $?
fi

##############################################################################
# Mode: Log Current Audit Results
##############################################################################

if [ "$MODE" == "log" ]; then
    cd "$PROJECT_ROOT"

    # Count local files
    LOCAL_PBP=$(find data/nba_pbp -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    LOCAL_BOX=$(find data/nba_box_score -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    LOCAL_TEAM=$(find data/nba_team_stats -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    LOCAL_SCHED=$(find data/nba_schedule_json -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    LOCAL_TOTAL=$((LOCAL_PBP + LOCAL_BOX + LOCAL_TEAM + LOCAL_SCHED))

    # Count S3 files (if credentials available)
    if aws sts get-caller-identity &>/dev/null; then
        S3_PBP=$(aws s3 ls s3://nba-sim-raw-data-lake/pbp/ --recursive 2>/dev/null | wc -l | tr -d ' ')
        S3_BOX=$(aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ --recursive 2>/dev/null | wc -l | tr -d ' ')
        S3_TEAM=$(aws s3 ls s3://nba-sim-raw-data-lake/team_stats/ --recursive 2>/dev/null | wc -l | tr -d ' ')
        S3_SCHED=$(aws s3 ls s3://nba-sim-raw-data-lake/schedule/ --recursive 2>/dev/null | wc -l | tr -d ' ')
        S3_TOTAL=$((S3_PBP + S3_BOX + S3_TEAM + S3_SCHED))
        RDS_STATUS=$(aws rds describe-db-instances --db-instance-identifier nba-sim-db --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null || echo "unavailable")
    else
        S3_PBP="N/A"
        S3_BOX="N/A"
        S3_TEAM="N/A"
        S3_SCHED="N/A"
        S3_TOTAL="N/A"
        RDS_STATUS="N/A"
    fi

    # Determine sync status
    if [ "$S3_TOTAL" == "N/A" ]; then
        SYNC_STATUS="unknown"
    elif [ $LOCAL_TOTAL -eq $S3_TOTAL ]; then
        SYNC_STATUS="synchronized"
    else
        SYNC_STATUS="out_of_sync"
    fi

    # Append to history
    echo "$TIMESTAMP,$LOCAL_PBP,$LOCAL_BOX,$LOCAL_TEAM,$LOCAL_SCHED,$LOCAL_TOTAL,$S3_PBP,$S3_BOX,$S3_TEAM,$S3_SCHED,$S3_TOTAL,$RDS_STATUS,$SYNC_STATUS" >> "$HISTORY_FILE"

    echo -e "${GREEN}✅ Audit results logged to $HISTORY_FILE${NC}"
    exit 0
fi

##############################################################################
# Mode: Summary Statistics
##############################################################################

if [ "$MODE" == "summary" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Audit History Summary${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Count total audits
    TOTAL_AUDITS=$(($(wc -l < "$HISTORY_FILE") - 1))
    echo -e "Total audits recorded: ${GREEN}$TOTAL_AUDITS${NC}"

    # First and last audit dates
    FIRST_AUDIT=$(tail -n +2 "$HISTORY_FILE" | head -1 | cut -d',' -f1)
    LAST_AUDIT=$(tail -1 "$HISTORY_FILE" | cut -d',' -f1)
    echo -e "First audit: ${BLUE}$FIRST_AUDIT${NC}"
    echo -e "Last audit: ${BLUE}$LAST_AUDIT${NC}"
    echo ""

    # Latest file counts
    LATEST=$(tail -1 "$HISTORY_FILE")
    LATEST_LOCAL=$(echo "$LATEST" | cut -d',' -f6)
    LATEST_S3=$(echo "$LATEST" | cut -d',' -f11)
    LATEST_SYNC=$(echo "$LATEST" | cut -d',' -f13)

    echo "Latest counts:"
    echo -e "  Local: ${GREEN}$LATEST_LOCAL${NC} files"
    echo -e "  S3: ${GREEN}$LATEST_S3${NC} files"
    echo -e "  Sync status: ${GREEN}$LATEST_SYNC${NC}"
    echo ""

    # Calculate growth (first vs last)
    FIRST=$(tail -n +2 "$HISTORY_FILE" | head -1)
    FIRST_LOCAL=$(echo "$FIRST" | cut -d',' -f6)
    GROWTH=$((LATEST_LOCAL - FIRST_LOCAL))

    if [ $GROWTH -gt 0 ]; then
        echo -e "Total growth: ${GREEN}+$GROWTH${NC} files since first audit"
    elif [ $GROWTH -lt 0 ]; then
        echo -e "Total change: ${RED}$GROWTH${NC} files since first audit"
    else
        echo -e "Total growth: ${YELLOW}0${NC} files (no change)"
    fi

    # Sync issues count
    SYNC_ISSUES=$(grep -c "out_of_sync" "$HISTORY_FILE" || true)
    if [ $SYNC_ISSUES -eq 0 ]; then
        echo -e "Sync issues: ${GREEN}0${NC} (excellent!)"
    else
        echo -e "Sync issues: ${YELLOW}$SYNC_ISSUES${NC} out of $TOTAL_AUDITS audits"
    fi

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
fi

##############################################################################
# Mode: Compare Current vs Last Audit
##############################################################################

if [ "$MODE" == "compare" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Audit Comparison (Latest vs Previous)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Get last two audits
    LAST=$(tail -1 "$HISTORY_FILE")
    PREV=$(tail -2 "$HISTORY_FILE" | head -1)

    LAST_DATE=$(echo "$LAST" | cut -d',' -f1)
    PREV_DATE=$(echo "$PREV" | cut -d',' -f1)

    echo -e "Previous audit: ${BLUE}$PREV_DATE${NC}"
    echo -e "Latest audit: ${BLUE}$LAST_DATE${NC}"
    echo ""

    # Compare local counts
    LAST_LOCAL=$(echo "$LAST" | cut -d',' -f6)
    PREV_LOCAL=$(echo "$PREV" | cut -d',' -f6)
    DIFF=$((LAST_LOCAL - PREV_LOCAL))

    echo "Local file changes:"
    if [ $DIFF -gt 0 ]; then
        echo -e "  ${GREEN}+$DIFF${NC} files added"
    elif [ $DIFF -lt 0 ]; then
        echo -e "  ${RED}$DIFF${NC} files removed"
    else
        echo -e "  ${YELLOW}0${NC} files (no change)"
    fi

    # Compare S3 counts
    LAST_S3=$(echo "$LAST" | cut -d',' -f11)
    PREV_S3=$(echo "$PREV" | cut -d',' -f11)

    if [ "$LAST_S3" != "N/A" ] && [ "$PREV_S3" != "N/A" ]; then
        DIFF_S3=$((LAST_S3 - PREV_S3))
        echo ""
        echo "S3 file changes:"
        if [ $DIFF_S3 -gt 0 ]; then
            echo -e "  ${GREEN}+$DIFF_S3${NC} files added"
        elif [ $DIFF_S3 -lt 0 ]; then
            echo -e "  ${RED}$DIFF_S3${NC} files removed"
        else
            echo -e "  ${YELLOW}0${NC} files (no change)"
        fi
    fi

    # Compare sync status
    LAST_SYNC=$(echo "$LAST" | cut -d',' -f13)
    PREV_SYNC=$(echo "$PREV" | cut -d',' -f13)

    echo ""
    echo "Sync status:"
    echo -e "  Previous: ${BLUE}$PREV_SYNC${NC}"
    echo -e "  Latest: ${BLUE}$LAST_SYNC${NC}"

    if [ "$LAST_SYNC" == "synchronized" ] && [ "$PREV_SYNC" == "out_of_sync" ]; then
        echo -e "  ${GREEN}✅ Sync issue resolved!${NC}"
    elif [ "$LAST_SYNC" == "out_of_sync" ] && [ "$PREV_SYNC" == "synchronized" ]; then
        echo -e "  ${RED}⚠️  New sync issue detected!${NC}"
    fi

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
fi

##############################################################################
# Mode: Alert on Anomalies
##############################################################################

if [ "$MODE" == "alert" ]; then
    # Get last two audits
    LAST=$(tail -1 "$HISTORY_FILE")
    PREV=$(tail -2 "$HISTORY_FILE" | head -1)

    LAST_LOCAL=$(echo "$LAST" | cut -d',' -f6)
    PREV_LOCAL=$(echo "$PREV" | cut -d',' -f6)

    # Calculate percentage change
    if [ $PREV_LOCAL -gt 0 ]; then
        DIFF=$((LAST_LOCAL - PREV_LOCAL))
        PCT_CHANGE=$(awk "BEGIN {printf \"%.2f\", ($DIFF / $PREV_LOCAL) * 100}")

        # Alert if drop >5%
        if (( $(echo "$PCT_CHANGE < -5" | bc -l) )); then
            echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${RED}⚠️  ALERT: Significant file count drop detected!${NC}"
            echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo -e "Previous count: ${BLUE}$PREV_LOCAL${NC} files"
            echo -e "Current count: ${RED}$LAST_LOCAL${NC} files"
            echo -e "Change: ${RED}$DIFF${NC} files (${RED}$PCT_CHANGE%${NC})"
            echo ""
            echo "Possible causes:"
            echo "  - Files were accidentally deleted"
            echo "  - Data corruption"
            echo "  - Directory permissions issue"
            echo "  - Disk space issue"
            echo ""
            echo "Action required:"
            echo "  1. Verify file system integrity"
            echo "  2. Check recent deletion history: git log --diff-filter=D"
            echo "  3. Restore from S3 if needed: aws s3 sync s3://bucket/ data/"
            exit 1
        elif (( $(echo "$PCT_CHANGE > 10" | bc -l) )); then
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}✅ Significant growth detected${NC}"
            echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo -e "Previous count: ${BLUE}$PREV_LOCAL${NC} files"
            echo -e "Current count: ${GREEN}$LAST_LOCAL${NC} files"
            echo -e "Change: ${GREEN}+$DIFF${NC} files (${GREEN}+$PCT_CHANGE%${NC})"
            exit 0
        else
            echo -e "${GREEN}✅ No anomalies detected${NC}"
            echo -e "Change: $DIFF files ($PCT_CHANGE%)"
            exit 0
        fi
    fi
fi

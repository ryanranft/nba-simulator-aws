#!/bin/bash
#
# Batch Implement Recommendations
#
# Implements multiple recommendations in sequence (overnight mode).
# Stops on first failure and logs detailed error information.
#
# Usage:
#   bash scripts/automation/batch_implement_recommendations.sh --count 10
#   bash scripts/automation/batch_implement_recommendations.sh --all
#   bash scripts/automation/batch_implement_recommendations.sh rec_001 rec_002 rec_003
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Default values
COUNT=10
MODE="next"  # next, all, or specific
SPECIFIC_RECS=()

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --count|-c)
            COUNT="$2"
            shift 2
            ;;
        --all|-a)
            MODE="all"
            COUNT=999
            shift
            ;;
        rec_*)
            MODE="specific"
            SPECIFIC_RECS+=("$1")
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--count N | --all | rec_XXX rec_YYY ...]"
            exit 1
            ;;
    esac
done

# Initialize counters
TOTAL_ATTEMPTED=0
TOTAL_SUCCESS=0
TOTAL_FAILED=0
TOTAL_SKIPPED=0

# Log file
LOG_DIR="${WORKSPACE_ROOT}/logs/recommendations"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/batch_${TIMESTAMP}.log"

# Redirect all output to log file and console
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo -e "${MAGENTA}==============================================================================${NC}"
echo -e "${MAGENTA}BATCH RECOMMENDATION IMPLEMENTATION${NC}"
echo -e "${MAGENTA}==============================================================================${NC}"
echo ""
echo "Started: $(date)"
echo "Mode: $MODE"
echo "Target Count: $COUNT"
echo "Log File: $LOG_FILE"
echo ""

# Get list of recommendations to implement
if [[ "$MODE" == "specific" ]]; then
    RECS_TO_IMPLEMENT=("${SPECIFIC_RECS[@]}")
    echo "Implementing specific recommendations: ${RECS_TO_IMPLEMENT[*]}"
elif [[ "$MODE" == "all" || "$MODE" == "next" ]]; then
    echo "Getting next available recommendations..."

    # Use Python script to get next available
    RECS_JSON=$(python3 scripts/automation/check_recommendation_status.py --next --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
recs = [item['rec_id'] for item in data[:${COUNT}]]
print(' '.join(recs))
")

    if [[ -z "$RECS_JSON" ]]; then
        echo -e "${YELLOW}No recommendations available to implement${NC}"
        exit 0
    fi

    # Convert to array
    read -ra RECS_TO_IMPLEMENT <<< "$RECS_JSON"
    echo "Found ${#RECS_TO_IMPLEMENT[@]} recommendations to implement"
fi

echo ""
echo -e "${BLUE}Recommendations to implement:${NC}"
for rec in "${RECS_TO_IMPLEMENT[@]}"; do
    echo "  - $rec"
done
echo ""

# Confirm before proceeding
echo -e "${YELLOW}Proceed with batch implementation? [y/N] ${NC}"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Cancelled by user"
    exit 0
fi

echo ""
echo -e "${GREEN}Starting batch implementation...${NC}"
echo ""

# Track start time
START_TIME=$(date +%s)

# Implement each recommendation
for rec in "${RECS_TO_IMPLEMENT[@]}"; do
    TOTAL_ATTEMPTED=$((TOTAL_ATTEMPTED + 1))

    echo ""
    echo -e "${BLUE}------------------------------------------------------------------------------${NC}"
    echo -e "${BLUE}[${TOTAL_ATTEMPTED}/${#RECS_TO_IMPLEMENT[@]}] Implementing: $rec${NC}"
    echo -e "${BLUE}------------------------------------------------------------------------------${NC}"
    echo ""

    # Run implementation script
    REC_START_TIME=$(date +%s)

    if bash "${SCRIPT_DIR}/implement_recommendation.sh" "$rec"; then
        REC_END_TIME=$(date +%s)
        REC_DURATION=$((REC_END_TIME - REC_START_TIME))

        echo ""
        echo -e "${GREEN}✓ SUCCESS: $rec completed in ${REC_DURATION}s${NC}"
        TOTAL_SUCCESS=$((TOTAL_SUCCESS + 1))
    else
        REC_END_TIME=$(date +%s)
        REC_DURATION=$((REC_END_TIME - REC_START_TIME))

        echo ""
        echo -e "${RED}✗ FAILED: $rec failed after ${REC_DURATION}s${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))

        # Ask if should continue
        echo ""
        echo -e "${YELLOW}Continue with remaining recommendations? [y/N] ${NC}"
        read -r continue_response

        if [[ ! "$continue_response" =~ ^[Yy]$ ]]; then
            echo "Stopping batch implementation"
            break
        fi
    fi
done

# Calculate statistics
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
MINUTES=$((TOTAL_DURATION / 60))
SECONDS=$((TOTAL_DURATION % 60))

echo ""
echo -e "${MAGENTA}==============================================================================${NC}"
echo -e "${MAGENTA}BATCH IMPLEMENTATION COMPLETE${NC}"
echo -e "${MAGENTA}==============================================================================${NC}"
echo ""
echo "Finished: $(date)"
echo "Total Duration: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Results:"
echo "  Attempted: $TOTAL_ATTEMPTED"
echo "  ✓ Success: $TOTAL_SUCCESS"
echo "  ✗ Failed: $TOTAL_FAILED"
echo "  ⊘ Skipped: $TOTAL_SKIPPED"
echo ""

if [[ $TOTAL_SUCCESS -gt 0 ]]; then
    AVG_TIME=$((TOTAL_DURATION / TOTAL_SUCCESS))
    echo "Average Time per Recommendation: ${AVG_TIME}s"
fi

echo ""
echo "Log File: $LOG_FILE"
echo ""

# Generate updated status report
echo -e "${BLUE}Current Status:${NC}"
python3 scripts/automation/check_recommendation_status.py | head -n 20

echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Review log file: $LOG_FILE"
echo "2. Check failed recommendations (if any)"
echo "3. Run: python3 scripts/automation/check_recommendation_status.py --next"
echo "4. Continue with next batch or individual recommendations"
echo ""

# Exit with appropriate code
if [[ $TOTAL_FAILED -gt 0 ]]; then
    exit 1
else
    exit 0
fi










#!/bin/bash
#
# Implement Tier 1 Recommendations
#
# Implements all Tier 1 recommendations (0 dependencies).
# These are safe to implement in parallel or sequence.
#
# Usage:
#   bash scripts/automation/implement_tier_1.sh
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}TIER 1: Zero Dependencies (23 recommendations)${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Get Tier 1 recommendations (those with 0 dependencies)
echo "Identifying Tier 1 recommendations..."

TIER1_RECS=$(python3 -c "
import sys
sys.path.insert(0, '${WORKSPACE_ROOT}/scripts/automation')
from check_recommendation_status import RecommendationStatusChecker

checker = RecommendationStatusChecker('${WORKSPACE_ROOT}')
checker.scan_statuses()

# Find all with 0 dependencies and not complete
tier1 = []
for rec_id, info in checker.statuses.items():
    status = info.get('status')
    dependencies = info.get('dependencies', [])
    
    if status != 'COMPLETE' and len(dependencies) == 0:
        tier1.append(rec_id)

# Sort by priority and rec_id
def priority_score(rec_id):
    info = checker.statuses[rec_id]
    priority = info.get('priority', '')
    if 'CRITICAL' in priority or '⭐' in priority:
        return 0
    elif 'HIGH' in priority or '🟡' in priority:
        return 1
    elif 'MEDIUM' in priority:
        return 2
    else:
        return 3

tier1.sort(key=lambda r: (priority_score(r), r))

for rec_id in tier1:
    print(rec_id, end=' ')
")

if [[ -z "$TIER1_RECS" ]]; then
    echo -e "${GREEN}All Tier 1 recommendations already complete!${NC}"
    exit 0
fi

# Convert to array
read -ra TIER1_ARRAY <<< "$TIER1_RECS"

echo "Found ${#TIER1_ARRAY[@]} Tier 1 recommendations to implement:"
for rec in "${TIER1_ARRAY[@]}"; do
    # Get title
    TITLE=$(python3 scripts/automation/check_recommendation_status.py --rec "$rec" 2>/dev/null | grep "Priority:" | head -n 1 || echo "Unknown")
    echo "  - $rec"
done
echo ""

# Call batch implementation
echo "Calling batch implementation script..."
echo ""

exec bash "${SCRIPT_DIR}/batch_implement_recommendations.sh" "${TIER1_ARRAY[@]}"


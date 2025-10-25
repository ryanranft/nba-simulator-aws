#!/bin/bash
#
# Implement Tier 3 Recommendations
#
# Implements all Tier 3 recommendations (3+ dependencies).
# Requires Tier 1 and Tier 2 to be substantially complete.
#
# Usage:
#   bash scripts/automation/implement_tier_3.sh
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo -e "${BLUE}==============================================================================${NC}"
echo -e "${BLUE}TIER 3: High Dependencies (3+ prerequisites)${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Get Tier 3 recommendations (those with 3+ dependencies, all met)
echo "Identifying Tier 3 recommendations..."

TIER3_RECS=$(python3 -c "
import sys
sys.path.insert(0, '${WORKSPACE_ROOT}/scripts/automation')
from check_recommendation_status import RecommendationStatusChecker

checker = RecommendationStatusChecker('${WORKSPACE_ROOT}')
checker.scan_statuses()

# Find completed recommendations
completed = set([
    rec_id for rec_id, info in checker.statuses.items()
    if info.get('status') == 'COMPLETE'
])

# Find Tier 3 (3+ dependencies, all met)
tier3 = []
for rec_id, info in checker.statuses.items():
    status = info.get('status')
    dependencies = info.get('dependencies', [])

    if status == 'COMPLETE':
        continue

    if len(dependencies) >= 3:
        # Check if all dependencies are met
        unmet = [d for d in dependencies if d not in completed]
        if not unmet:
            tier3.append(rec_id)

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

tier3.sort(key=lambda r: (priority_score(r), r))

for rec_id in tier3:
    print(rec_id, end=' ')
")

if [[ -z "$TIER3_RECS" ]]; then
    echo -e "${YELLOW}No Tier 3 recommendations available.${NC}"
    echo "Either all complete, or dependencies not met yet."
    echo ""
    echo "Complete Tier 1 and Tier 2 first:"
    echo "  bash scripts/automation/implement_tier_1.sh"
    echo "  bash scripts/automation/implement_tier_2.sh"
    exit 0
fi

# Convert to array
read -ra TIER3_ARRAY <<< "$TIER3_RECS"

echo "Found ${#TIER3_ARRAY[@]} Tier 3 recommendations to implement:"
for rec in "${TIER3_ARRAY[@]}"; do
    echo "  - $rec"
done
echo ""

# Call batch implementation
echo "Calling batch implementation script..."
echo ""

exec bash "${SCRIPT_DIR}/batch_implement_recommendations.sh" "${TIER3_ARRAY[@]}"








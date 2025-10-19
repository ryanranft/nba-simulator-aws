#!/bin/bash
#
# Implement Tier 2 Recommendations
#
# Implements all Tier 2 recommendations (1-2 dependencies).
# Requires Tier 1 to be complete first.
#
# Usage:
#   bash scripts/automation/implement_tier_2.sh
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
echo -e "${BLUE}TIER 2: Low Dependencies (1-2 prerequisites)${NC}"
echo -e "${BLUE}==============================================================================${NC}"
echo ""

# Get Tier 2 recommendations (those with 1-2 dependencies, all met)
echo "Identifying Tier 2 recommendations..."

TIER2_RECS=$(python3 -c "
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

# Find Tier 2 (1-2 dependencies, all met)
tier2 = []
for rec_id, info in checker.statuses.items():
    status = info.get('status')
    dependencies = info.get('dependencies', [])
    
    if status == 'COMPLETE':
        continue
    
    dep_count = len(dependencies)
    if dep_count >= 1 and dep_count <= 2:
        # Check if all dependencies are met
        unmet = [d for d in dependencies if d not in completed]
        if not unmet:
            tier2.append(rec_id)

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

tier2.sort(key=lambda r: (priority_score(r), r))

for rec_id in tier2:
    print(rec_id, end=' ')
")

if [[ -z "$TIER2_RECS" ]]; then
    echo -e "${YELLOW}No Tier 2 recommendations available.${NC}"
    echo "Either all complete, or dependencies not met yet."
    echo ""
    echo "Run Tier 1 first if not yet complete:"
    echo "  bash scripts/automation/implement_tier_1.sh"
    exit 0
fi

# Convert to array
read -ra TIER2_ARRAY <<< "$TIER2_RECS"

echo "Found ${#TIER2_ARRAY[@]} Tier 2 recommendations to implement:"
for rec in "${TIER2_ARRAY[@]}"; do
    echo "  - $rec"
done
echo ""

# Call batch implementation
echo "Calling batch implementation script..."
echo ""

exec bash "${SCRIPT_DIR}/batch_implement_recommendations.sh" "${TIER2_ARRAY[@]}"


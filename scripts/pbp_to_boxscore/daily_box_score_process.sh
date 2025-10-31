#!/bin/bash
#
# Daily Box Score Generation Script
# Runs automatically at 3 AM daily via LaunchAgent
#
# Processes yesterday's games into temporal box score snapshots
#

set -e

# Change to project directory
cd /Users/ryanranft/nba-simulator-aws

# Activate conda environment
source /Users/ryanranft/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

# Get current season (October-June = season starting that year)
CURRENT_MONTH=$(date +%m)
CURRENT_YEAR=$(date +%Y)

if [ "$CURRENT_MONTH" -ge 10 ]; then
    # October-December: use current year
    SEASON=$CURRENT_YEAR
else
    # January-September: use previous year
    SEASON=$((CURRENT_YEAR - 1))
fi

echo "==================================="
echo "Daily Box Score Generation"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Season: $SEASON"
echo "==================================="

# Process current season with limit (recent games only)
# Limit to 5 games to keep processing fast
python scripts/pbp_to_boxscore/batch_process_espn.py \
    --season $SEASON \
    --limit 5 \
    --verbose

echo "==================================="
echo "Box Score Generation Complete"
echo "==================================="

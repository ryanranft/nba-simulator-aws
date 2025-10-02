#!/bin/bash
#
# Automated Overnight S3 Partitioning
#
# Partitions all 4 data types (schedule, pbp, box_scores, team_stats) by year.
# Designed to run unattended overnight.
#
# Usage: nohup ./scripts/etl/partition_all_overnight.sh > partition_overnight.log 2>&1 &
#
# Author: Ryan Ranft
# Date: 2025-10-01

set -e

LOG_FILE="/Users/ryanranft/nba-simulator-aws/partition_overnight.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "================================================================================"
echo "AUTOMATED S3 PARTITIONING - OVERNIGHT RUN"
echo "================================================================================"
echo "Started: $TIMESTAMP"
echo "Log file: $LOG_FILE"
echo ""

# Function to partition a single data type
partition_data_type() {
    local data_type=$1
    echo ""
    echo "================================================================================"
    echo "Partitioning: $data_type"
    echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================================================================"

    # Auto-answer "yes" to confirmation prompt
    echo "yes" | python scripts/etl/partition_by_year.py \
        --data-types "$data_type" \
        --execute

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo ""
        echo "✅ SUCCESS: $data_type partitioning completed"
        echo "Completed: $(date '+%Y-%m-%d %H:%M:%S')"
    else
        echo ""
        echo "❌ FAILED: $data_type partitioning failed with exit code $exit_code"
        echo "Failed at: $(date '+%Y-%m-%d %H:%M:%S')"
        return $exit_code
    fi
}

# Partition all 4 data types
partition_data_type "schedule"
partition_data_type "pbp"
partition_data_type "box_scores"
partition_data_type "team_stats"

echo ""
echo "================================================================================"
echo "ALL PARTITIONING COMPLETE"
echo "================================================================================"
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Verify results
echo "Verifying S3 structure..."
echo ""
echo "Schedule years:"
aws s3 ls s3://nba-sim-raw-data-lake/schedule/ | grep "year=" | wc -l

echo ""
echo "PBP years:"
aws s3 ls s3://nba-sim-raw-data-lake/pbp/ | grep "year=" | wc -l

echo ""
echo "Box scores years:"
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ | grep "year=" | wc -l

echo ""
echo "Team stats years:"
aws s3 ls s3://nba-sim-raw-data-lake/team_stats/ | grep "year=" | wc -l

echo ""
echo "✅ Partitioning complete! Ready to create year-based crawlers."
echo ""
echo "Next steps:"
echo "1. Create year-based crawlers:"
echo "   ./scripts/etl/create_year_crawlers.sh --all"
echo ""
echo "2. Run crawlers for a test year:"
echo "   aws glue start-crawler --name nba-schedule-1997-crawler"
echo ""

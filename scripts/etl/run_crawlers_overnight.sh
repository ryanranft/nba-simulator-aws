#!/bin/bash
#
# Automated Overnight Glue Crawler Execution
#
# Creates and runs Glue Crawlers as S3 partitions become available.
# Runs crawlers in batches to avoid AWS service limits (max 10 concurrent).
#
# Usage: nohup ./scripts/etl/run_crawlers_overnight.sh > crawler_overnight.log 2>&1 &
#
# Author: Ryan Ranft
# Date: 2025-10-01

set -e

LOG_FILE="/Users/ryanranft/nba-simulator-aws/crawler_overnight.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Color codes (for terminal output)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "AUTOMATED GLUE CRAWLER EXECUTION - OVERNIGHT RUN"
echo "================================================================================"
echo "Started: $TIMESTAMP"
echo "Log file: $LOG_FILE"
echo ""

# Function to check if S3 partition exists and has files
check_partition_ready() {
    local data_type=$1
    local year=$2

    # Check if year folder exists in S3
    local s3_path="s3://nba-sim-raw-data-lake/${data_type}/year=${year}/"
    local file_count=$(aws s3 ls "$s3_path" 2>/dev/null | grep ".json" | wc -l | tr -d ' ')

    if [ "$file_count" -gt 0 ]; then
        return 0  # Ready
    else
        return 1  # Not ready
    fi
}

# Function to create crawler if it doesn't exist
create_crawler_if_missing() {
    local data_type=$1
    local year=$2

    local crawler_name="nba-${data_type}-${year}-crawler"

    # Check if crawler exists
    if aws glue get-crawler --name "$crawler_name" &>/dev/null; then
        echo "  ✓ Crawler exists: $crawler_name"
        return 0
    else
        echo "  Creating crawler: $crawler_name"
        ./scripts/etl/create_year_crawlers.sh --data-type "$data_type" --years "${year}-${year}" &>/dev/null
        return 0
    fi
}

# Function to start crawler
start_crawler() {
    local crawler_name=$1

    # Check current state
    local state=$(aws glue get-crawler --name "$crawler_name" --query 'Crawler.State' --output text 2>/dev/null || echo "UNKNOWN")

    if [ "$state" == "RUNNING" ]; then
        echo "  ⏳ Already running: $crawler_name"
        return 0
    elif [ "$state" == "READY" ] || [ "$state" == "UNKNOWN" ]; then
        echo "  ▶️  Starting: $crawler_name"
        aws glue start-crawler --name "$crawler_name" &>/dev/null || true
        return 0
    else
        echo "  ⚠️  State $state: $crawler_name"
        return 1
    fi
}

# Function to wait for running crawlers to complete
wait_for_crawlers() {
    local max_concurrent=10

    while true; do
        # Count running crawlers
        local running_count=$(aws glue list-crawlers --query 'CrawlerNames' --output text 2>/dev/null | \
            tr '\t' '\n' | \
            xargs -I {} aws glue get-crawler --name {} --query 'Crawler.State' --output text 2>/dev/null | \
            grep "RUNNING" | wc -l | tr -d ' ' || echo "0")

        if [ "$running_count" -lt "$max_concurrent" ]; then
            # Space available
            return 0
        else
            echo "  ⏳ $running_count crawlers running, waiting 60 seconds..."
            sleep 60
        fi
    done
}

# Function to process all years for a data type
process_data_type() {
    local data_type=$1
    local start_year=${2:-1993}
    local end_year=${3:-2025}

    echo ""
    echo "================================================================================"
    echo "Processing: $(echo ${data_type} | tr '[:lower:]' '[:upper:]')"
    echo "================================================================================"

    local crawlers_started=0
    local crawlers_skipped=0

    for year in $(seq $start_year $end_year); do
        echo ""
        echo "Year $year:"

        # Wait for partition to be ready (check every 60 seconds, max 60 minutes)
        local attempts=0
        local max_attempts=60

        while ! check_partition_ready "$data_type" "$year"; do
            if [ $attempts -ge $max_attempts ]; then
                echo "  ⏭️  Timeout waiting for partition (${data_type}/year=${year})"
                crawlers_skipped=$((crawlers_skipped + 1))
                break
            fi

            echo "  ⏳ Waiting for partition to be ready... (attempt $((attempts + 1))/$max_attempts)"
            sleep 60
            attempts=$((attempts + 1))
        done

        # If partition ready, create and start crawler
        if check_partition_ready "$data_type" "$year"; then
            create_crawler_if_missing "$data_type" "$year"

            # Wait if too many crawlers running
            wait_for_crawlers

            # Start crawler
            local crawler_name="nba-${data_type}-${year}-crawler"
            if start_crawler "$crawler_name"; then
                crawlers_started=$((crawlers_started + 1))
            fi

            # Small delay to avoid API throttling
            sleep 2
        fi
    done

    echo ""
    echo "Summary for $data_type:"
    echo "  Started: $crawlers_started crawlers"
    echo "  Skipped: $crawlers_skipped crawlers"
}

# Main execution

echo "Strategy:"
echo "  1. Wait for each year partition to be ready in S3"
echo "  2. Create crawler if it doesn't exist"
echo "  3. Start crawler (max 10 concurrent)"
echo "  4. Repeat for all years (1993-2025) and all data types"
echo ""
echo "Expected timeline:"
echo "  - Schedule: 33 years × ~5 min = ~2.5 hours"
echo "  - PBP: 25 years × ~5 min = ~2 hours"
echo "  - Box Scores: 25 years × ~5 min = ~2 hours"
echo "  - Team Stats: 25 years × ~5 min = ~2 hours"
echo "  Total: ~8-10 hours (with parallelization: ~3-4 hours)"
echo ""

# Process all data types
# Schedule data: 1993-2025 (all years have schedule data)
process_data_type "schedule" 1993 2025

# PBP data: 1997-2021 (game data only available from 1997+)
process_data_type "pbp" 1997 2021

# Box scores: 1997-2021
process_data_type "box_scores" 1997 2021

# Team stats: 1997-2021
process_data_type "team_stats" 1997 2021

echo ""
echo "================================================================================"
echo "ALL CRAWLERS STARTED"
echo "================================================================================"
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Wait for all crawlers to complete
echo "Waiting for all crawlers to complete..."
echo ""

while true; do
    running_count=$(aws glue list-crawlers --query 'CrawlerNames' --output text 2>/dev/null | \
        xargs -I {} aws glue get-crawler --name {} --query 'Crawler.State' --output text 2>/dev/null | \
        grep -c "RUNNING" || echo "0")

    if [ "$running_count" -eq 0 ]; then
        echo "✅ All crawlers completed!"
        break
    else
        echo "⏳ $running_count crawlers still running... (checking again in 2 minutes)"
        sleep 120
    fi
done

echo ""
echo "================================================================================"
echo "FINAL SUMMARY"
echo "================================================================================"
echo ""

# Count created tables
echo "Glue Tables Created:"
for data_type in schedule pbp box_scores team_stats; do
    table_count=$(aws glue get-tables --database-name nba_raw_data --query "TableList[?starts_with(Name, '${data_type}')].Name" --output text 2>/dev/null | wc -w | tr -d ' ')
    echo "  ${data_type}: ${table_count} tables"
done

echo ""
echo "✅ Crawler execution complete! Ready for 2.0002 (Glue ETL)."
echo ""

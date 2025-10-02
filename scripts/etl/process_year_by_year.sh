#!/bin/bash
#
# Year-by-Year S3 Partitioning and Crawler Execution
#
# Processes one year at a time: partition all 4 data types, then crawl all 4.
# More sequential than the parallel approach.
#
# Usage: nohup ./scripts/etl/process_year_by_year.sh > year_by_year.log 2>&1 &
#
# Author: Ryan Ranft
# Date: 2025-10-01

set -e

LOG_FILE="/Users/ryanranft/nba-simulator-aws/year_by_year.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
BUCKET="nba-sim-raw-data-lake"
DATABASE="nba_raw_data"
ROLE="AWSGlueServiceRole-NBASimulator"

echo "================================================================================"
echo "YEAR-BY-YEAR S3 PARTITIONING AND CRAWLER EXECUTION"
echo "================================================================================"
echo "Started: $TIMESTAMP"
echo ""

# Function to partition one year for one data type
partition_year() {
    local data_type=$1
    local year=$2

    echo "  Partitioning ${data_type} for year ${year}..."

    # Create a temporary Python script to partition just this year
    python3 - <<EOF
import boto3
import sys
from pathlib import Path

sys.path.append('/Users/ryanranft/nba-simulator-aws/scripts/etl')
from game_id_decoder import extract_year_from_filename

s3_client = boto3.client('s3')
bucket = '${BUCKET}'
data_type = '${data_type}'
target_year = ${year}

# List files in flat structure
paginator = s3_client.get_paginator('list_objects_v2')
copied = 0

for page in paginator.paginate(Bucket=bucket, Prefix=f'{data_type}/'):
    if 'Contents' not in page:
        continue

    for obj in page['Contents']:
        key = obj['Key']

        # Skip if already partitioned
        if 'year=' in key:
            continue

        # Only .json files
        if not key.endswith('.json'):
            continue

        filename = key.split('/')[-1]
        year = extract_year_from_filename(filename)

        if year == target_year:
            new_key = f'{data_type}/year={year}/{filename}'
            copy_source = {'Bucket': bucket, 'Key': key}
            s3_client.copy_object(CopySource=copy_source, Bucket=bucket, Key=new_key)
            copied += 1
            if copied % 50 == 0:
                print(f'    Copied {copied} files...', flush=True)

print(f'  ✅ Copied {copied} files for {data_type}/year={target_year}')
EOF
}

# Function to create and run crawler
crawl_year() {
    local data_type=$1
    local year=$2

    local crawler_name="nba-${data_type}-${year}-crawler"
    local s3_path="s3://${BUCKET}/${data_type}/year=${year}/"

    # Create crawler if doesn't exist
    if ! aws glue get-crawler --name "$crawler_name" &>/dev/null; then
        echo "  Creating crawler: $crawler_name"
        aws glue create-crawler \
            --name "$crawler_name" \
            --targets "{\"S3Targets\":[{\"Path\":\"${s3_path}\"}]}" \
            --database-name "$DATABASE" \
            --role "$ROLE" \
            --description "Crawler for NBA ${data_type} data - Year ${year}" \
            --output text > /dev/null
    fi

    # Start crawler
    echo "  Starting crawler: $crawler_name"
    aws glue start-crawler --name "$crawler_name" 2>/dev/null || true

    # Wait for crawler to complete
    echo "  Waiting for crawler to complete..."
    local attempts=0
    while [ $attempts -lt 60 ]; do
        local state=$(aws glue get-crawler --name "$crawler_name" --query 'Crawler.State' --output text 2>/dev/null || echo "UNKNOWN")

        if [ "$state" == "READY" ]; then
            echo "  ✅ Crawler completed: $crawler_name"
            return 0
        elif [ "$state" == "RUNNING" ]; then
            sleep 10
            attempts=$((attempts + 1))
        else
            echo "  ⏳ Crawler state: $state (waiting...)"
            sleep 10
            attempts=$((attempts + 1))
        fi
    done

    echo "  ⚠️  Crawler timeout (may still be running): $crawler_name"
}

# Function to process one year completely
process_year() {
    local year=$1
    local data_types=("$@")
    shift  # Remove first argument (year)

    echo ""
    echo "================================================================================"
    echo "YEAR $year"
    echo "================================================================================"
    echo ""

    # Step 1: Partition all data types for this year
    echo "--- Step 1: Partitioning data for year $year ---"
    for data_type in "${data_types[@]}"; do
        partition_year "$data_type" "$year"
    done
    echo ""

    # Step 2: Crawl all data types for this year
    echo "--- Step 2: Crawling data for year $year ---"
    for data_type in "${data_types[@]}"; do
        crawl_year "$data_type" "$year"
    done
    echo ""

    echo "✅ Year $year complete!"
}

# Main execution

echo "Strategy: Process one year at a time"
echo "  1. Partition all 4 data types for year N"
echo "  2. Crawl all 4 data types for year N"
echo "  3. Move to year N+1"
echo ""
echo "Data types: schedule, pbp, box_scores, team_stats"
echo "Years: 1993-2025"
echo ""

# Process each year
for year in {1993..2025}; do
    # Determine which data types have data for this year
    if [ $year -lt 1997 ]; then
        # Only schedule data before 1997
        process_year $year "schedule"
    elif [ $year -le 2021 ]; then
        # All data types 1997-2021
        process_year $year "schedule" "pbp" "box_scores" "team_stats"
    else
        # Only schedule after 2021
        process_year $year "schedule"
    fi
done

echo ""
echo "================================================================================"
echo "ALL YEARS PROCESSED"
echo "================================================================================"
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Summary
echo "Summary:"
echo "  Year folders created:"
for data_type in schedule pbp box_scores team_stats; do
    count=$(aws s3 ls s3://nba-sim-raw-data-lake/${data_type}/ 2>/dev/null | grep "year=" | wc -l | tr -d ' ')
    echo "    ${data_type}: ${count}"
done
echo ""
echo "  Glue tables created:"
for data_type in schedule pbp box_scores team_stats; do
    table_count=$(aws glue get-tables --database-name nba_raw_data --query "TableList[?starts_with(Name, '${data_type}')].Name" --output text 2>/dev/null | wc -w | tr -d ' ')
    echo "    ${data_type}: ${table_count}"
done
echo ""
echo "✅ Complete! Ready for Phase 2.2 (Glue ETL)."
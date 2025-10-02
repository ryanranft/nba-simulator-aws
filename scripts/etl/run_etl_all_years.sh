#!/bin/bash
#
# Run Glue ETL Job for All Years (1993-2025)
#
# Processes schedule data year by year, extracting game information
# from S3 JSON files and loading to RDS PostgreSQL.
#
# Usage: nohup ./scripts/etl/run_etl_all_years.sh > etl_all_years.log 2>&1 &
#
# Author: Ryan Ranft
# Date: 2025-10-01
# Phase: 2.2 - Glue ETL

set -e

LOG_FILE="/Users/ryanranft/nba-simulator-aws/etl_all_years.log"
JOB_NAME="nba-schedule-etl-job"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "================================================================================"
echo "GLUE ETL JOB EXECUTION - ALL YEARS"
echo "================================================================================"
echo "Started: $TIMESTAMP"
echo ""
echo "Job: $JOB_NAME"
echo "Years: 1993-2025"
echo ""

# Function to start ETL job for one year
run_etl_year() {
    local year=$1

    echo "--- Year $year ---"
    echo "  Starting job run..."

    # Start the job
    run_id=$(aws glue start-job-run \
        --job-name "$JOB_NAME" \
        --arguments "{\"--year\":\"$year\"}" \
        --query 'JobRunId' \
        --output text 2>&1)

    if [ $? -ne 0 ]; then
        echo "  ❌ Failed to start job for year $year"
        echo "  Error: $run_id"
        return 1
    fi

    echo "  ▶️  Job started: $run_id"

    # Wait for job to complete
    local attempts=0
    local max_attempts=120  # 20 minutes max (10 sec intervals)

    while [ $attempts -lt $max_attempts ]; do
        # Get job status
        status=$(aws glue get-job-run \
            --job-name "$JOB_NAME" \
            --run-id "$run_id" \
            --query 'JobRun.JobRunState' \
            --output text 2>/dev/null || echo "UNKNOWN")

        case "$status" in
            SUCCEEDED)
                # Get execution time and records processed
                exec_time=$(aws glue get-job-run \
                    --job-name "$JOB_NAME" \
                    --run-id "$run_id" \
                    --query 'JobRun.ExecutionTime' \
                    --output text 2>/dev/null || echo "N/A")

                echo "  ✅ Job completed successfully!"
                echo "     Execution time: ${exec_time}s"
                return 0
                ;;
            FAILED|TIMEOUT|STOPPED)
                error_msg=$(aws glue get-job-run \
                    --job-name "$JOB_NAME" \
                    --run-id "$run_id" \
                    --query 'JobRun.ErrorMessage' \
                    --output text 2>/dev/null || echo "Unknown error")

                echo "  ❌ Job failed!"
                echo "     Status: $status"
                echo "     Error: $error_msg"
                return 1
                ;;
            RUNNING|STARTING|STOPPING)
                echo "  ⏳ Job $status (${attempts}0s elapsed)..."
                sleep 10
                attempts=$((attempts + 1))
                ;;
            *)
                echo "  ⚠️  Unknown status: $status"
                sleep 10
                attempts=$((attempts + 1))
                ;;
        esac
    done

    echo "  ⚠️  Job timeout after ${max_attempts}0 seconds"
    return 1
}

# Main execution - process all years
success_count=0
fail_count=0

for year in {1993..2025}; do
    echo ""
    echo "================================================================================"
    echo "PROCESSING YEAR $year"
    echo "================================================================================"
    echo ""

    if run_etl_year $year; then
        success_count=$((success_count + 1))
        echo "✅ Year $year complete!"
    else
        fail_count=$((fail_count + 1))
        echo "❌ Year $year failed!"

        # Continue with next year even if this one fails
        echo "   Continuing to next year..."
    fi

    # Brief pause between years
    sleep 5
done

echo ""
echo "================================================================================"
echo "ETL PROCESSING COMPLETE"
echo "================================================================================"
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "Summary:"
echo "  ✅ Successful: $success_count years"
echo "  ❌ Failed: $fail_count years"
echo "  📊 Total: $((success_count + fail_count)) years"
echo ""

# Check database to see total games loaded
echo "Checking database for loaded games..."

# Require DB_PASSWORD environment variable
if [ -z "$DB_PASSWORD" ]; then
    echo "ERROR: DB_PASSWORD environment variable not set"
    echo "Run: source /Users/ryanranft/nba-sim-credentials.env"
    exit 1
fi

psql_cmd="PGPASSWORD='$DB_PASSWORD' psql -h nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com -U postgres -d nba_simulator"

if command -v psql &> /dev/null; then
    echo ""
    echo "Database Statistics:"
    $psql_cmd -c "SELECT
        season_year,
        COUNT(*) as game_count,
        MIN(game_date) as first_game,
        MAX(game_date) as last_game
    FROM games
    GROUP BY season_year
    ORDER BY season_year;" 2>/dev/null || echo "Unable to connect to database"

    echo ""
    $psql_cmd -c "SELECT
        COUNT(*) as total_games,
        COUNT(DISTINCT season_year) as seasons,
        MIN(game_date) as earliest_game,
        MAX(game_date) as latest_game
    FROM games;" 2>/dev/null || echo "Unable to connect to database"
else
    echo "psql not available - skipping database check"
fi

echo ""
echo "✅ All years processed!"

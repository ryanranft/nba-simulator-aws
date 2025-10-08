#!/bin/bash
#
# Basketball Reference Incremental Year-by-Year Scraper
# Scrapes one season at a time in the background
# Can be resumed if interrupted - won't re-scrape completed seasons
#
# Usage: ./scrape_bbref_incremental.sh [start_year] [end_year]
# Example: ./scrape_bbref_incremental.sh 2020 2025
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_YEAR=${1:-1950}
END_YEAR=${2:-2025}
S3_BUCKET="nba-sim-raw-data-lake"
OUTPUT_DIR="/tmp/basketball_reference_incremental"
LOG_DIR="/tmp/bbref_incremental_logs"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$LOG_DIR"

echo "=============================================="
echo "Basketball Reference Incremental Scraper"
echo "=============================================="
echo "Seasons: $START_YEAR to $END_YEAR"
echo "Output: $OUTPUT_DIR"
echo "Logs: $LOG_DIR"
echo "S3: s3://$S3_BUCKET/basketball_reference/"
echo "Start Time: $(date)"
echo "=============================================="
echo

# Data types to scrape (all 7 types)
DATA_TYPES=(
    "schedules"
    "season-totals"
    "advanced-totals"
    "standings"
    "player-box-scores"
    "team-box-scores"
    "play-by-play"
)

# Function to check if a season/data-type combination is already complete
is_complete() {
    local season=$1
    local data_type=$2
    local marker_file="$OUTPUT_DIR/${data_type}_${season}.complete"

    if [ -f "$marker_file" ]; then
        return 0  # Already complete
    else
        return 1  # Not complete
    fi
}

# Function to mark a season/data-type as complete
mark_complete() {
    local season=$1
    local data_type=$2
    local marker_file="$OUTPUT_DIR/${data_type}_${season}.complete"

    touch "$marker_file"
    echo "$(date) - Marked $data_type season $season as complete" >> "$LOG_DIR/completion.log"
}

# Loop through each season
for season in $(seq $START_YEAR $END_YEAR); do
    echo "================================================"
    echo "Processing season $season ($(date))"
    echo "================================================"

    # Loop through each data type
    for data_type in "${DATA_TYPES[@]}"; do
        # Skip if already complete
        if is_complete $season $data_type; then
            echo "  ✓ $data_type already complete for season $season (skipping)"
            continue
        fi

        # Special handling for play-by-play (only 2000+)
        if [ "$data_type" = "play-by-play" ] && [ $season -lt 2000 ]; then
            echo "  ⊘ Skipping play-by-play for season $season (not available before 2000)"
            mark_complete $season $data_type
            continue
        fi

        echo "  → Scraping $data_type for season $season..."
        LOG_FILE="$LOG_DIR/${data_type}_${season}.log"

        # Run scraper for this season + data type
        if python "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
            --data-type "$data_type" \
            --start-season $season \
            --end-season $season \
            --upload-to-s3 \
            --s3-bucket "$S3_BUCKET" \
            --output-dir "$OUTPUT_DIR" \
            > "$LOG_FILE" 2>&1; then

            # Success - mark as complete
            echo "  ✓ $data_type for season $season complete"
            mark_complete $season $data_type
        else
            # Failed - log error but continue with next
            echo "  ❌ $data_type for season $season FAILED (see $LOG_FILE)"
            echo "$(date) - FAILED: $data_type season $season" >> "$LOG_DIR/errors.log"
        fi

        # Small delay between data types to be nice to the server
        sleep 2
    done

    echo "  Season $season complete"
    echo
done

echo "=============================================="
echo "Incremental scraping complete!"
echo "End Time: $(date)"
echo "=============================================="
echo
echo "Summary:"
echo "  Completed seasons: $START_YEAR - $END_YEAR"
echo "  Output directory: $OUTPUT_DIR"
echo "  Completion markers: $OUTPUT_DIR/*.complete"
echo "  Logs: $LOG_DIR/"
echo "  Errors: $LOG_DIR/errors.log"
echo
echo "To check progress:"
echo "  ls $OUTPUT_DIR/*.complete | wc -l"
echo "  tail -f $LOG_DIR/errors.log"
echo

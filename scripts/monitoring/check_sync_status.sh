#!/bin/bash
# NBA Simulator - Local to S3 Sync Status Checker
# Part of DIMS Workflow Integration (Phase 3)
# Checks synchronization status between local files and S3 bucket

set -euo pipefail

# Configuration
S3_BUCKET="s3://nba-sim-raw-data-lake"
LOCAL_DATA_DIRS=(
    "$HOME/0espn"
    "$HOME/nba-sim-temp"
    "$HOME/sports-simulator-archives/nba"
)

# Parse arguments
MODE="full"  # full or brief
if [[ "${1:-}" == "--brief" ]]; then
    MODE="brief"
fi

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    if [[ "$MODE" == "brief" ]]; then
        echo "unknown"
    else
        echo "ERROR: AWS CLI not installed"
    fi
    exit 1
fi

# Check S3 bucket accessibility
if ! aws s3 ls "$S3_BUCKET" &> /dev/null; then
    if [[ "$MODE" == "brief" ]]; then
        echo "unknown"
    else
        echo "ERROR: Cannot access S3 bucket $S3_BUCKET"
    fi
    exit 1
fi

# Count files in S3
s3_total=$(aws s3 ls "$S3_BUCKET" --recursive 2>/dev/null | wc -l | tr -d ' ')

# Count files in local directories
local_total=0
for dir in "${LOCAL_DATA_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        count=$(find "$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
        local_total=$((local_total + count))
    fi
done

# Calculate drift percentage
if [[ $s3_total -eq 0 ]]; then
    drift_pct=0
else
    drift_pct=$(python3 -c "print(abs($local_total - $s3_total) * 100.0 / $s3_total)")
fi

# Determine sync status
if (( $(echo "$drift_pct < 5" | bc -l) )); then
    status="synced"
elif (( $(echo "$drift_pct < 15" | bc -l) )); then
    status="minor_drift"
elif (( $(echo "$drift_pct < 30" | bc -l) )); then
    status="moderate_drift"
else
    status="major_drift"
fi

# Output based on mode
if [[ "$MODE" == "brief" ]]; then
    echo "$status"
else
    echo "==================================================================="
    echo "LOCAL TO S3 SYNC STATUS"
    echo "==================================================================="
    echo "S3 Files:      $s3_total"
    echo "Local Files:   $local_total"
    echo "Difference:    $((local_total - s3_total))"
    echo "Drift:         ${drift_pct}%"
    echo "Status:        $status"
    echo "==================================================================="
    echo ""
    echo "Local directories checked:"
    for dir in "${LOCAL_DATA_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            count=$(find "$dir" -type f 2>/dev/null | wc -l | tr -d ' ')
            echo "  - $dir: $count files"
        else
            echo "  - $dir: NOT FOUND"
        fi
    done
    echo ""

    # Recommendations based on status
    case "$status" in
        "synced")
            echo "✅ Local and S3 are well synchronized (<5% drift)"
            ;;
        "minor_drift")
            echo "⚠️  Minor drift detected (5-15%). Consider running sync if recent changes made."
            ;;
        "moderate_drift")
            echo "⚠️  Moderate drift detected (15-30%). Recommend running full sync."
            ;;
        "major_drift")
            echo "🔴 MAJOR drift detected (>30%). URGENT: Run full sync to prevent data loss."
            ;;
    esac
fi

exit 0

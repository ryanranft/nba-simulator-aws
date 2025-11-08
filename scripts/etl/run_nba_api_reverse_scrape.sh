#!/bin/bash
#
# NBA API Reverse Scraper
# Tests recent seasons first to validate API connectivity
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="/tmp/nba_api_reverse"
S3_BUCKET="nba-sim-raw-data-lake"
START_YEAR=$(date +%Y)  # Current year
END_YEAR=${1:-1996}     # Default to 1996, can override with first argument

echo "=============================================="
echo "NBA API Reverse Chronological Scraper"
echo "=============================================="
echo "Start Year: $START_YEAR"
echo "End Year: $END_YEAR"
echo "Output: $OUTPUT_DIR"
echo "S3: s3://$S3_BUCKET/nba_api_reverse/"
echo "Start Time: $(date)"
echo "=============================================="
echo

# Check if nba_api is installed
if ! python3 -c "import nba_api" 2>/dev/null; then
    echo "❌ nba_api package not installed"
    echo "Installing nba_api..."
    pip install nba_api
fi

# Check if boto3 is installed (for S3 upload)
if ! python3 -c "import boto3" 2>/dev/null; then
    echo "⚠️ boto3 not installed - S3 upload will be disabled"
    echo "Install with: pip install boto3"
    UPLOAD_TO_S3=""
else
    UPLOAD_TO_S3="--upload-to-s3"
fi

# Run the reverse scraper
echo "Starting NBA API reverse scraper..."
python3 "$SCRIPT_DIR/nba_api_reverse_scraper.py" \
    --start-year $START_YEAR \
    --end-year $END_YEAR \
    --output-dir "$OUTPUT_DIR" \
    $UPLOAD_TO_S3 \
    --s3-bucket "$S3_BUCKET" \
    --test-mode

# Check exit status
if [ $? -eq 0 ]; then
    echo
    echo "✅ NBA API reverse scraper completed successfully!"
    echo "📁 Check output directory: $OUTPUT_DIR"
    if [ -n "$UPLOAD_TO_S3" ]; then
        echo "☁️  Files uploaded to S3: s3://$S3_BUCKET/nba_api_reverse/"
    fi
else
    echo
    echo "❌ NBA API reverse scraper failed!"
    echo "Check the output above for error details."
    exit 1
fi

echo
echo "End Time: $(date)"
echo "=============================================="












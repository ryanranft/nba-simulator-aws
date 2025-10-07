#!/bin/bash
#
# Run ESPN Scraper for Missing Data (2022-2025)
#
# This script scrapes ESPN for missing NBA data and uploads to S3.
# Files are saved in small individual JSONs (ideal for AWS Glue processing).
#
# Usage:
#   bash scripts/etl/run_espn_scraper.sh          # Scrape 2022-01-01 to today
#   bash scripts/etl/run_espn_scraper.sh --test   # Test with 7 days of data
#   bash scripts/etl/run_espn_scraper.sh --custom 2024-01-01 2024-12-31  # Custom range

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
START_DATE="2022-01-01"
END_DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="/tmp/espn_data"
S3_BUCKET="nba-sim-raw-data-lake"
UPLOAD_TO_S3="--upload-to-s3"

# Parse arguments
if [ "$1" == "--test" ]; then
    echo -e "${YELLOW}📝 TEST MODE: Scraping last 7 days only${NC}"
    START_DATE=$(date -v-7d +%Y-%m-%d 2>/dev/null || date -d '7 days ago' +%Y-%m-%d)
    END_DATE=$(date +%Y-%m-%d)
elif [ "$1" == "--custom" ]; then
    if [ -z "$2" ] || [ -z "$3" ]; then
        echo -e "${RED}❌ Custom mode requires start and end dates${NC}"
        echo "Usage: $0 --custom YYYY-MM-DD YYYY-MM-DD"
        exit 1
    fi
    START_DATE="$2"
    END_DATE="$3"
elif [ "$1" == "--local-only" ]; then
    echo -e "${YELLOW}📝 LOCAL ONLY MODE: Files will not be uploaded to S3${NC}"
    UPLOAD_TO_S3=""
fi

# Print configuration
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ESPN Data Scraper - Fill Missing Data (2022-2025)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}📅 Date range:${NC}      $START_DATE to $END_DATE"
echo -e "${GREEN}💾 Output dir:${NC}      $OUTPUT_DIR"
echo -e "${GREEN}☁️  S3 bucket:${NC}       $S3_BUCKET"
echo -e "${GREEN}📤 Upload to S3:${NC}    $([ -n "$UPLOAD_TO_S3" ] && echo 'Yes' || echo 'No')"
echo ""

# Calculate total days
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DAYS=$(( ( $(date -j -f "%Y-%m-%d" "$END_DATE" +%s) - $(date -j -f "%Y-%m-%d" "$START_DATE" +%s) ) / 86400 + 1 ))
else
    # Linux
    DAYS=$(( ( $(date -d "$END_DATE" +%s) - $(date -d "$START_DATE" +%s) ) / 86400 + 1 ))
fi

echo -e "${YELLOW}⏱️  Estimated time:${NC}  $(( DAYS * 3 / 60 )) minutes (${DAYS} days × ~3 sec/day)"
echo ""

# Confirm before proceeding
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Cancelled${NC}"
    exit 1
fi

# Activate conda environment
if command -v conda &> /dev/null; then
    echo -e "${GREEN}🐍 Activating conda environment...${NC}"
    eval "$(conda shell.bash hook)"
    conda activate nba-aws
fi

# Check for required Python packages
echo -e "${GREEN}📦 Checking dependencies...${NC}"
python -c "import requests, boto3" 2>/dev/null || {
    echo -e "${RED}❌ Missing required packages${NC}"
    echo "Install with: pip install requests boto3"
    exit 1
}

# Clean output directory if exists
if [ -d "$OUTPUT_DIR" ]; then
    echo -e "${YELLOW}🗑️  Cleaning old output directory...${NC}"
    rm -rf "$OUTPUT_DIR"
fi

# Run scraper
echo -e "${GREEN}🚀 Starting scraper...${NC}"
echo ""

python scripts/etl/scrape_missing_espn_data.py \
    --start-date "$START_DATE" \
    --end-date "$END_DATE" \
    --output-dir "$OUTPUT_DIR" \
    --s3-bucket "$S3_BUCKET" \
    $UPLOAD_TO_S3

# Check result
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Scraping completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Next steps:${NC}"
    echo "1. Review files in: $OUTPUT_DIR"

    if [ -n "$UPLOAD_TO_S3" ]; then
        echo "2. Verify S3 upload:"
        echo "   aws s3 ls s3://$S3_BUCKET/schedule/ | tail -20"
        echo "3. Run AWS Glue ETL to extract data to RDS:"
        echo "   python scripts/etl/extract_schedule_local.py"
    else
        echo "2. Upload to S3:"
        echo "   bash scripts/etl/run_espn_scraper.sh  # Re-run without --local-only"
    fi
else
    echo ""
    echo -e "${RED}❌ Scraping failed - check errors above${NC}"
    exit 1
fi
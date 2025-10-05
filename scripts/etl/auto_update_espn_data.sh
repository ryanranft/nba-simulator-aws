#!/bin/bash
# Automated ESPN Data Gap Detection & Scraping Workflow
# Checks for missing data and automatically runs ESPN scraper to fill gaps

set -e

echo "========================================="
echo "ESPN DATA GAP DETECTION & AUTO-UPDATE"
echo "========================================="
echo ""

# Configuration
ESPN_SCRAPER_DIR="/Users/ryanranft/0espn"
NBA_SCHEDULE_SCRIPT="$ESPN_SCRAPER_DIR/espn/nba/nba_schedule.py"
S3_BUCKET="s3://nba-sim-raw-data-lake"
PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
ETL_SCRIPT="$PROJECT_DIR/scripts/etl/extract_schedule_local.py"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Step 1: Checking today's date..."
TODAY=$(date +%Y-%m-%d)
echo "  Today: $TODAY"
echo ""

echo "Step 2: Finding last date with data in S3..."
LAST_S3_FILE=$(aws s3 ls $S3_BUCKET/schedule/ --recursive | grep "\.json$" | tail -1)

if [ -z "$LAST_S3_FILE" ]; then
    echo -e "${RED}✗ Error: Could not find any JSON files in S3${NC}"
    echo "  Bucket: $S3_BUCKET/schedule/"
    exit 1
fi

# Extract date from filename (format: schedule/YYYYMMDD.json)
LAST_S3_DATE_RAW=$(echo "$LAST_S3_FILE" | grep -oE '[0-9]{8}' | tail -1)
LAST_S3_DATE=$(date -j -f "%Y%m%d" "$LAST_S3_DATE_RAW" "+%Y-%m-%d" 2>/dev/null || echo "unknown")

echo "  Last file: $(echo $LAST_S3_FILE | awk '{print $4}')"
echo "  Last date: $LAST_S3_DATE"
echo ""

echo "Step 3: Calculating data gap..."
# Convert dates to timestamps for comparison
TODAY_TS=$(date -j -f "%Y-%m-%d" "$TODAY" "+%s")
LAST_TS=$(date -j -f "%Y-%m-%d" "$LAST_S3_DATE" "+%s")
GAP_DAYS=$(( ($TODAY_TS - $LAST_TS) / 86400 ))

echo "  Days missing: $GAP_DAYS"
echo ""

# Check if update needed
if [ $GAP_DAYS -le 0 ]; then
    echo -e "${GREEN}✓ Data is up to date! No scraping needed.${NC}"
    echo ""
    echo "Current coverage: up to $LAST_S3_DATE"
    echo "Next update needed: $(date -j -v+1d -f "%Y-%m-%d" "$LAST_S3_DATE" "+%Y-%m-%d")"
    exit 0
fi

echo -e "${YELLOW}⚠ Gap detected: $GAP_DAYS days of missing data${NC}"
echo "  From: $LAST_S3_DATE (exclusive)"
echo "  To:   $TODAY (inclusive)"
echo ""

# Ask for confirmation
read -p "Proceed with ESPN scraping? (y/n): " -n 1 -r
echo
if [[ ! $REPLAY =~ ^[Yy]$ ]]; then
    echo "Aborted by user."
    exit 0
fi

echo ""
echo "========================================="
echo "Step 4: Updating ESPN scraper date range..."
echo "========================================="
echo ""

# Parse today's date components
TODAY_YEAR=$(date +%Y)
TODAY_MONTH=$(date +%m)
TODAY_DAY=$(date +%d)

# Backup original file
BACKUP_FILE="$NBA_SCHEDULE_SCRIPT.bak.$(date +%Y%m%d_%H%M%S)"
cp "$NBA_SCHEDULE_SCRIPT" "$BACKUP_FILE"
echo "  Backed up: $BACKUP_FILE"

# Update end_date in scraper (line 142)
# Original: end_date = datetime.date(2025, 6, 30)
# New:      end_date = datetime.date(YYYY, MM, DD)
sed -i '' "s/end_date = datetime\.date([0-9]\{4\}, [0-9]\{1,2\}, [0-9]\{1,2\})/end_date = datetime.date($TODAY_YEAR, $TODAY_MONTH, $TODAY_DAY)/" "$NBA_SCHEDULE_SCRIPT"

echo -e "${GREEN}✓ Updated end_date to: datetime.date($TODAY_YEAR, $TODAY_MONTH, $TODAY_DAY)${NC}"
echo ""

echo "========================================="
echo "Step 5: Running ESPN scraper..."
echo "========================================="
echo ""

cd "$ESPN_SCRAPER_DIR"

echo "  Working directory: $(pwd)"
echo "  Running: python espn/nba/nba_schedule.py"
echo ""

# Run scraper and capture output
if python espn/nba/nba_schedule.py; then
    echo ""
    echo -e "${GREEN}✓ ESPN scraper completed successfully${NC}"
else
    echo ""
    echo -e "${RED}✗ ESPN scraper failed${NC}"
    echo "  Restoring backup..."
    cp "$BACKUP_FILE" "$NBA_SCHEDULE_SCRIPT"
    exit 1
fi

echo ""
echo "========================================="
echo "Step 6: Uploading new files to S3..."
echo "========================================="
echo ""

# Count files before sync
LOCAL_DIR="$ESPN_SCRAPER_DIR/data/nba"
BEFORE_COUNT=$(aws s3 ls $S3_BUCKET/schedule/ --recursive | grep "\.json$" | wc -l | xargs)
echo "  Files in S3 before sync: $BEFORE_COUNT"

# Sync only new JSON files
aws s3 sync "$LOCAL_DIR/" "$S3_BUCKET/schedule/" \
    --exclude "*" --include "*.json" --size-only

AFTER_COUNT=$(aws s3 ls $S3_BUCKET/schedule/ --recursive | grep "\.json$" | wc -l | xargs)
NEW_FILES=$((AFTER_COUNT - BEFORE_COUNT))

echo ""
echo "  Files in S3 after sync:  $AFTER_COUNT"
echo -e "${GREEN}✓ Uploaded $NEW_FILES new files${NC}"
echo ""

echo "========================================="
echo "Step 7: Extracting to RDS database..."
echo "========================================="
echo ""

cd "$PROJECT_DIR"

# Determine year range for extraction
LAST_YEAR=$(date -j -f "%Y-%m-%d" "$LAST_S3_DATE" "+%Y")
CURRENT_YEAR=$(date +%Y)

echo "  Working directory: $(pwd)"
echo "  Running: python scripts/etl/extract_schedule_local.py --year-range $LAST_YEAR-$CURRENT_YEAR"
echo ""

if python "$ETL_SCRIPT" --year-range "$LAST_YEAR-$CURRENT_YEAR"; then
    echo ""
    echo -e "${GREEN}✓ ETL extraction completed successfully${NC}"
else
    echo ""
    echo -e "${RED}✗ ETL extraction failed${NC}"
    echo "  Note: S3 files were uploaded successfully, but RDS extraction failed"
    echo "  You can manually run: python $ETL_SCRIPT --year-range $LAST_YEAR-$CURRENT_YEAR"
    exit 1
fi

echo ""
echo "========================================="
echo "Step 8: Verification..."
echo "========================================="
echo ""

# Load RDS credentials
if [ -f ~/nba-sim-credentials.env ]; then
    source ~/nba-sim-credentials.env
else
    echo -e "${YELLOW}⚠ Warning: Could not load RDS credentials from ~/nba-sim-credentials.env${NC}"
    echo "  Skipping database verification"
    echo ""
    echo "========================================="
    echo "UPDATE COMPLETE"
    echo "========================================="
    echo ""
    echo -e "${GREEN}✓ ESPN data updated successfully${NC}"
    echo ""
    echo "Summary:"
    echo "  - Gap filled: $GAP_DAYS days"
    echo "  - New files uploaded: $NEW_FILES"
    echo "  - Date range: $LAST_S3_DATE to $TODAY"
    echo "  - S3 files: $AFTER_COUNT total"
    echo ""
    echo "Note: Database verification skipped (credentials not found)"
    exit 0
fi

echo "Checking RDS database for new games..."
GAME_COUNT=$(psql -h $NBA_SIM_DB_HOST -U $NBA_SIM_DB_USER -d $NBA_SIM_DB_NAME -t -c \
    "SELECT COUNT(*) FROM games WHERE game_date >= '$LAST_S3_DATE';" 2>/dev/null | xargs || echo "0")

echo "  Games added since $LAST_S3_DATE: $GAME_COUNT"
echo ""

# Check latest date in database
LATEST_DB_DATE=$(psql -h $NBA_SIM_DB_HOST -U $NBA_SIM_DB_USER -d $NBA_SIM_DB_NAME -t -c \
    "SELECT MAX(game_date) FROM games;" 2>/dev/null | xargs || echo "unknown")

echo "  Latest date in database: $LATEST_DB_DATE"
echo ""

echo "========================================="
echo "UPDATE COMPLETE"
echo "========================================="
echo ""

echo -e "${GREEN}✓ ESPN data updated successfully${NC}"
echo ""
echo "Summary:"
echo "  - Gap filled: $GAP_DAYS days"
echo "  - New files uploaded: $NEW_FILES"
echo "  - Date range: $LAST_S3_DATE to $TODAY"
echo "  - S3 files: $AFTER_COUNT total"
echo "  - Database games: $GAME_COUNT new"
echo "  - Latest DB date: $LATEST_DB_DATE"
echo ""
echo "Backup saved: $BACKUP_FILE"
echo ""
echo "========================================="
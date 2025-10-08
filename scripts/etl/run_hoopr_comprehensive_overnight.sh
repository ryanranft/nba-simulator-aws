#!/usr/bin/bash
#
# Overnight hoopR Comprehensive NBA Stats API Scraper (R Version)
#
# Uses the R version of hoopR which has ALL 152 NBA Stats API endpoints
# Coverage: 2002-2025 (24 seasons)
# Runtime estimate: 10-15 hours for full historical pull
# Data size estimate: 10-20 GB total
#
# This script calls ALL available hoopR/NBA Stats API endpoints:
# - 4 bulk data loaders (pbp, player_box, team_box, schedule)
# - 152 NBA Stats API endpoints (shot charts, tracking, hustle, synergy, lineups, etc.)
#

set -e

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/tmp/hoopr_complete"
LOG_DIR="$PROJECT_DIR/logs/hoopr_complete_$TIMESTAMP"
FULL_LOG="/tmp/hoopr_complete_full.log"

mkdir -p "$LOG_DIR"

echo "================================================" | tee "$FULL_LOG"
echo "hoopR Comprehensive NBA Stats API Scraper (R)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Coverage: 2002-2025 (24 seasons)" | tee -a "$FULL_LOG"
echo "Endpoints: 152 NBA Stats API functions" | tee -a "$FULL_LOG"
echo "Log directory: $LOG_DIR" | tee -a "$FULL_LOG"
echo "Output directory: $OUTPUT_DIR" | tee -a "$FULL_LOG"
echo "Started: $(date)" | tee -a "$FULL_LOG"
echo "" | tee -a "$FULL_LOG"

cd "$PROJECT_DIR"

# Check if R and hoopR are available
echo "🔧 Checking R environment..." | tee -a "$FULL_LOG"
if ! command -v Rscript &> /dev/null; then
    echo "❌ Rscript not found. Please install R." | tee -a "$FULL_LOG"
    exit 1
fi

Rscript -e "library(hoopR); cat('✅ hoopR version:', as.character(packageVersion('hoopR')), '\n')" 2>&1 | tee -a "$FULL_LOG"

# Run the comprehensive R scraper
echo "" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "🏀 Starting comprehensive hoopR scraper..." | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "" | tee -a "$FULL_LOG"

Rscript scripts/etl/scrape_hoopr_complete_all_endpoints.R "$OUTPUT_DIR" --upload-to-s3 \
    2>&1 | tee -a "$LOG_DIR/hoopr_complete.log" | tee -a "$FULL_LOG"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "✅ hoopR comprehensive scraping complete" | tee -a "$FULL_LOG"
else
    echo "❌ hoopR scraping failed (exit code: ${PIPESTATUS[0]})" | tee -a "$FULL_LOG"
fi

echo "" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"
echo "Completed: $(date)" | tee -a "$FULL_LOG"
echo "================================================" | tee -a "$FULL_LOG"

# Show output summary
echo "" | tee -a "$FULL_LOG"
echo "📁 Output files created:" | tee -a "$FULL_LOG"
find "$OUTPUT_DIR" -type f -name "*.json" | wc -l | xargs echo "  Total JSON files:" | tee -a "$FULL_LOG"
du -sh "$OUTPUT_DIR" | awk '{print "  Total size: " $1}' | tee -a "$FULL_LOG"

echo "" | tee -a "$FULL_LOG"
echo "📋 File breakdown by category:" | tee -a "$FULL_LOG"
for category_dir in "$OUTPUT_DIR"/*; do
    if [ -d "$category_dir" ]; then
        category=$(basename "$category_dir")
        file_count=$(find "$category_dir" -type f -name "*.json" | wc -l)
        echo "  $category: $file_count files" | tee -a "$FULL_LOG"
    fi
done

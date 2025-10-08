#!/usr/bin/bash
#
# hoopR Phase 1 Foundation Data Scraper Runner
#
# Gets ~50 high-value endpoints (2002-2025)
# Runtime: 2-4 hours
# Data: 10-20 GB
# Format: CSV (avoids R's 2GB JSON limit)
#

set -e

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/tmp/hoopr_phase1"
LOG_FILE="/tmp/hoopr_phase1_${TIMESTAMP}.log"

cd "$PROJECT_DIR"

echo "================================================" | tee "$LOG_FILE"
echo "hoopR Phase 1: Foundation Data Scraper" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"
echo "Coverage: 2002-2025 (24 seasons)" | tee -a "$LOG_FILE"
echo "Endpoints: ~50 foundation endpoints" | tee -a "$LOG_FILE"
echo "Output: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check R and hoopR
echo "🔧 Checking environment..." | tee -a "$LOG_FILE"
Rscript -e "library(hoopR); cat('✅ hoopR version:', as.character(packageVersion('hoopR')), '\n')" 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "🏀 Starting Phase 1 scraper..." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Run scraper
Rscript scripts/etl/scrape_hoopr_phase1_foundation.R "$OUTPUT_DIR" --upload-to-s3 \
    2>&1 | tee -a "$LOG_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "✅ Phase 1 scraping complete!" | tee -a "$LOG_FILE"
else
    echo "" | tee -a "$LOG_FILE"
    echo "❌ Scraping failed (exit code: ${PIPESTATUS[0]})" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"
echo "Completed: $(date)" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"

# Summary
echo "" | tee -a "$LOG_FILE"
echo "📁 Output summary:" | tee -a "$LOG_FILE"
find "$OUTPUT_DIR" -name "*.csv" | wc -l | xargs echo "  Total CSV files:" | tee -a "$LOG_FILE"
du -sh "$OUTPUT_DIR" 2>/dev/null | awk '{print "  Total size: " $1}' | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "📋 Files by category:" | tee -a "$LOG_FILE"
for dir in "$OUTPUT_DIR"/*; do
    if [ -d "$dir" ]; then
        category=$(basename "$dir")
        count=$(find "$dir" -name "*.csv" | wc -l)
        echo "  $category: $count files" | tee -a "$LOG_FILE"
    fi
done

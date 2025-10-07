#!/bin/bash
#
# Overnight NBA API Play-by-Play Scraper
#
# Scrapes ONLY play-by-play data for possession panel generation
# Much faster than comprehensive scraper (3-4 hours vs 750+ hours)
#
# Coverage: 1996-2024 (29 seasons)
# Endpoint: PlayByPlayV2 only
# Runtime estimate: 3-4 hours for all seasons
# Data size estimate: ~500MB-1GB
#
# Monitor progress:
#   tail -f /tmp/nba_api_playbyplay_overnight.log
#

set -e

PROJECT_DIR="/Users/ryanranft/nba-simulator-aws"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/nba_api_playbyplay_overnight.log"

echo "================================================" | tee "$LOG_FILE"
echo "NBA API Play-by-Play Overnight Scraper" | tee -a "$LOG_FILE"
echo "================================================" | tee -a "$LOG_FILE"
echo "Coverage: 1996-2024 (29 seasons)" | tee -a "$LOG_FILE"
echo "Endpoint: PlayByPlayV2 only" | tee -a "$LOG_FILE"
echo "Purpose: Possession panel data" | tee -a "$LOG_FILE"
echo "Estimated runtime: 3-4 hours" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Activate conda environment
echo "🔧 Activating conda environment..." | tee -a "$LOG_FILE"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nba-aws

# Verify nba_api installation
echo "📦 Checking nba_api installation..." | tee -a "$LOG_FILE"
python -c "from nba_api.stats.endpoints import PlayByPlayV2; print('✅ nba_api available')" 2>&1 | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

# Run scraper for all seasons (1996-2024)
echo "" | tee -a "$LOG_FILE"
echo "🚀 Starting play-by-play scraper..." | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

python scripts/etl/scrape_nba_api_playbyplay_only.py \
    --start-season 1996 \
    --end-season 2024 \
    --output-dir "/tmp/nba_api_playbyplay" \
    --upload-to-s3 \
    --s3-bucket "nba-sim-raw-data-lake" \
    --rate-limit 0.6 \
    2>&1 | tee -a "$LOG_FILE"

exit_code=${PIPESTATUS[0]}

if [ $exit_code -eq 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "================================================" | tee -a "$LOG_FILE"
    echo "✅ Overnight scraper completed successfully" | tee -a "$LOG_FILE"
    echo "================================================" | tee -a "$LOG_FILE"
    echo "Completed: $(date)" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "📊 Output:" | tee -a "$LOG_FILE"
    echo "  Local: /tmp/nba_api_playbyplay/" | tee -a "$LOG_FILE"
    echo "  S3: s3://nba-sim-raw-data-lake/nba_api_playbyplay/" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Next steps:" | tee -a "$LOG_FILE"
    echo "  1. Run: python scripts/etl/create_possession_panel_from_nba_api.py --data-dir /tmp/nba_api_playbyplay/play_by_play" | tee -a "$LOG_FILE"
    echo "  2. This will generate possession panels for all seasons" | tee -a "$LOG_FILE"
else
    echo "" | tee -a "$LOG_FILE"
    echo "❌ Overnight scraper failed (exit code: $exit_code)" | tee -a "$LOG_FILE"
    echo "Check log for details: $LOG_FILE" | tee -a "$LOG_FILE"
fi

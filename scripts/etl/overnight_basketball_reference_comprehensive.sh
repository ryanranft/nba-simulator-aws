#!/bin/bash
#
# Basketball Reference Complete Historical Scraper
# Overnight run for 1946-2025 (79 seasons)
#
# This script scrapes ALL available data from Basketball Reference:
# - Schedules (fast)
# - Player box scores (LARGEST - runs overnight)
# - Team box scores
# - Player season totals
# - Player advanced season totals
# - Play-by-play (modern era only - 2000+)
# - Standings
#
# Rate limit: 5 seconds between requests (Basketball Reference rate limit protection)
#

set -e

SEASON_START=1950  # Library does NOT support BAA years (1947-1949) - starts with first NBA season
SEASON_END=2025
S3_BUCKET="nba-sim-raw-data-lake"
OUTPUT_DIR="/tmp/basketball_reference_complete"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=============================================="
echo "Basketball Reference Complete Historical Scraper"
echo "=============================================="
echo "Seasons: $SEASON_START-$SEASON_END (75 NBA seasons)"
echo "Note: BAA years (1947-1949) not supported by library"
echo "S3 Bucket: $S3_BUCKET"
echo "Output Directory: $OUTPUT_DIR"
echo "Script Directory: $SCRIPT_DIR"
echo "Start Time: $(date)"
echo "=============================================="
echo

# Create output directory
mkdir -p "$OUTPUT_DIR"

# 1. Schedules (fast - gets game list for all seasons)
echo "[1/7] Scraping schedules..."
echo "Estimated time: ~7 minutes (79 seasons × 5s rate limit)"
python "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
  --data-type schedules \
  --start-season $SEASON_START \
  --end-season $SEASON_END \
  --upload-to-s3 \
  --s3-bucket $S3_BUCKET \
  --output-dir $OUTPUT_DIR \
  2>&1 | tee /tmp/bbref_schedules.log

echo
echo "✓ Schedules complete at $(date)"
echo "=============================================="
echo

# 2. Player box scores (LARGEST - run in background overnight)
echo "[2/7] Scraping player box scores (BACKGROUND)..."
echo "Estimated time: ~132 hours (95,000 games × 5s rate limit)"
echo "This will run in the background while we continue with other data types"
nohup python "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
  --data-type player-box-scores \
  --start-season $SEASON_START \
  --end-season $SEASON_END \
  --upload-to-s3 \
  --s3-bucket $S3_BUCKET \
  --output-dir $OUTPUT_DIR \
  > /tmp/bbref_player_box_scores.log 2>&1 &
PID_PLAYER=$!
echo "Player box scores running in background (PID: $PID_PLAYER)"
echo "Monitor with: tail -f /tmp/bbref_player_box_scores.log"
echo

# 3. Team box scores
echo "[3/7] Scraping team box scores..."
echo "Estimated time: ~132 hours (95,000 games × 5s rate limit)"
python "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
  --data-type team-box-scores \
  --start-season $SEASON_START \
  --end-season $SEASON_END \
  --upload-to-s3 \
  --s3-bucket $S3_BUCKET \
  --output-dir $OUTPUT_DIR \
  2>&1 | tee /tmp/bbref_team_box_scores.log

echo
echo "✓ Team box scores complete at $(date)"
echo "=============================================="
echo

# 4. Season totals
echo "[4/7] Scraping player season totals..."
echo "Estimated time: ~7 minutes (79 seasons × 5s rate limit)"
python "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
  --data-type season-totals \
  --start-season $SEASON_START \
  --end-season $SEASON_END \
  --upload-to-s3 \
  --s3-bucket $S3_BUCKET \
  --output-dir $OUTPUT_DIR \
  2>&1 | tee /tmp/bbref_season_totals.log

echo
echo "✓ Season totals complete at $(date)"
echo "=============================================="
echo

# 5. Advanced totals
echo "[5/7] Scraping player advanced totals..."
echo "Estimated time: ~7 minutes (79 seasons × 5s rate limit)"
python "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
  --data-type advanced-totals \
  --start-season $SEASON_START \
  --end-season $SEASON_END \
  --upload-to-s3 \
  --s3-bucket $S3_BUCKET \
  --output-dir $OUTPUT_DIR \
  2>&1 | tee /tmp/bbref_advanced_totals.log

echo
echo "✓ Advanced totals complete at $(date)"
echo "=============================================="
echo

# 6. Play-by-play (modern era only - start from 2000)
echo "[6/7] Scraping play-by-play data (modern era: 2000-2025)..."
echo "Estimated time: ~43 hours (31,250 games × 5s rate limit)"
python "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
  --data-type play-by-play \
  --start-season 2000 \
  --end-season $SEASON_END \
  --upload-to-s3 \
  --s3-bucket $S3_BUCKET \
  --output-dir $OUTPUT_DIR \
  2>&1 | tee /tmp/bbref_play_by_play.log

echo
echo "✓ Play-by-play complete at $(date)"
echo "=============================================="
echo

# 7. Standings
echo "[7/7] Scraping standings..."
echo "Estimated time: ~7 minutes (79 seasons × 5s rate limit)"
python "$SCRIPT_DIR/scrape_basketball_reference_complete.py" \
  --data-type standings \
  --start-season $SEASON_START \
  --end-season $SEASON_END \
  --upload-to-s3 \
  --s3-bucket $S3_BUCKET \
  --output-dir $OUTPUT_DIR \
  2>&1 | tee /tmp/bbref_standings.log

echo
echo "✓ Standings complete at $(date)"
echo "=============================================="
echo

# Wait for background player box scores to complete
echo
echo "Waiting for player box scores to complete (PID: $PID_PLAYER)..."
echo "This may take several days. Monitor progress with:"
echo "  tail -f /tmp/bbref_player_box_scores.log"
echo "  ps aux | grep $PID_PLAYER"
echo
wait $PID_PLAYER
echo "✓ Player box scores complete!"
echo

# Summary
echo "=============================================="
echo "Basketball Reference complete historical scrape finished!"
echo "End Time: $(date)"
echo "=============================================="
echo
echo "Log files:"
echo "  - Schedules:          /tmp/bbref_schedules.log"
echo "  - Player box scores:  /tmp/bbref_player_box_scores.log"
echo "  - Team box scores:    /tmp/bbref_team_box_scores.log"
echo "  - Season totals:      /tmp/bbref_season_totals.log"
echo "  - Advanced totals:    /tmp/bbref_advanced_totals.log"
echo "  - Play-by-play:       /tmp/bbref_play_by_play.log"
echo "  - Standings:          /tmp/bbref_standings.log"
echo
echo "Local data: $OUTPUT_DIR"
echo "S3 data: s3://$S3_BUCKET/basketball_reference/"
echo
echo "Summary statistics:"
echo "  - Estimated schedules:      79 files"
echo "  - Estimated player box:     ~1.9M records"
echo "  - Estimated team box:       ~190K records"
echo "  - Estimated season totals:  ~35,500 records"
echo "  - Estimated advanced:       ~35,500 records"
echo "  - Estimated play-by-play:   ~30,750 games"
echo "  - Estimated standings:      79 files"
echo
echo "Next steps:"
echo "  1. Verify S3 uploads: aws s3 ls s3://$S3_BUCKET/basketball_reference/"
echo "  2. Check data completeness"
echo "  3. Load into database for panel data transformation"
echo "=============================================="

#!/bin/bash
# Monitor Phase 1: NBA API Player Dashboards progress

LOG_FILE="logs/nba_api_player_dashboards.log"
OUTPUT_DIR="/tmp/nba_api_player_dashboards"

echo "======================================================================"
echo "Phase 1: NBA API Player Dashboards - Progress Monitor"
echo "======================================================================"
echo ""

# Check if process is running
PID=$(ps aux | grep "scrape_nba_api_player_dashboards" | grep "2020-21" | grep -v grep | awk '{print $2}')
if [ -z "$PID" ]; then
    echo "❌ Scraper not running!"
else
    echo "✅ Scraper running (PID: $PID)"
fi
echo ""

# Current season
CURRENT_SEASON=$(tail -n 100 "$LOG_FILE" | grep "Starting season" | tail -1 | awk '{print $NF}')
echo "Current season: $CURRENT_SEASON"
echo ""

# Player progress
CURRENT_PLAYER=$(tail -n 100 "$LOG_FILE" | grep "Processing player" | tail -1)
echo "Latest: $CURRENT_PLAYER"
echo ""

# Files collected
echo "Files collected by season:"
for season_dir in "$OUTPUT_DIR"/*; do
    if [ -d "$season_dir" ]; then
        season=$(basename "$season_dir")
        count=$(ls -1 "$season_dir" 2>/dev/null | wc -l | tr -d ' ')
        echo "  $season: $count files"
    fi
done
echo ""

# Recent activity (last 5 players)
echo "Recent activity (last 5 players):"
tail -n 200 "$LOG_FILE" | grep "Saved player" | tail -5
echo ""

# Errors
ERROR_COUNT=$(grep -c "❌ Error" "$LOG_FILE")
echo "Errors encountered: $ERROR_COUNT"
if [ $ERROR_COUNT -gt 0 ]; then
    echo "Recent errors:"
    grep "❌ Error" "$LOG_FILE" | tail -5
fi
echo ""

# Success rate
SUCCESS_COUNT=$(grep -c "✅.*records" "$LOG_FILE")
TOTAL_ATTEMPTS=$(grep -c "Scraping.*for player" "$LOG_FILE")
if [ $TOTAL_ATTEMPTS -gt 0 ]; then
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($SUCCESS_COUNT/$TOTAL_ATTEMPTS)*100}")
    echo "Success rate: $SUCCESS_RATE% ($SUCCESS_COUNT/$TOTAL_ATTEMPTS requests)"
fi
echo ""

# Disk usage
echo "Disk usage:"
du -sh "$OUTPUT_DIR" 2>/dev/null || echo "  No data yet"
echo ""

# Estimated completion
COMPLETED_PLAYERS=$(grep -c "Saved player" "$LOG_FILE")
if [ $COMPLETED_PLAYERS -gt 0 ]; then
    echo "Progress: $COMPLETED_PLAYERS players completed"

    # Rough estimate (assumes 500 players per season with data)
    ESTIMATED_TOTAL=$((500 * 5))  # 500 players × 5 seasons
    if [ $COMPLETED_PLAYERS -lt $ESTIMATED_TOTAL ]; then
        PERCENT=$(awk "BEGIN {printf \"%.1f\", ($COMPLETED_PLAYERS/$ESTIMATED_TOTAL)*100}")
        echo "Estimated progress: $PERCENT% of active players"
    fi
fi
echo ""

echo "======================================================================"
echo "Monitor command: bash scripts/monitoring/monitor_phase_1_progress.sh"
echo "Full logs: tail -f logs/nba_api_player_dashboards.log"
echo "Stop scraper: kill $PID"
echo "======================================================================"

#!/bin/bash
# Quick check of nba-simulator-aws hoopR coverage

echo "========================================"
echo "NBA-SIMULATOR-AWS DATABASE CHECK"
echo "========================================"
echo ""

# Check if we can connect
if ! psql -d nba_simulator -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Cannot connect to nba_simulator database"
    echo ""
    echo "Try one of these:"
    echo "  1. Start local PostgreSQL: brew services start postgresql"
    echo "  2. Use RDS: export POSTGRES_HOST=<your-rds-endpoint>"
    exit 1
fi

echo "📊 Database: nba_simulator"
echo "📅 Today: $(date +%Y-%m-%d)"
echo ""

# Check coverage
psql -d nba_simulator -c "
SELECT
    MIN(game_date) as earliest_game,
    MAX(game_date) as latest_game,
    COUNT(*) as total_games,
    COUNT(*) FILTER (WHERE game_date >= '2024-12-02') as games_since_dec_2024,
    COUNT(*) FILTER (WHERE game_date >= '2025-10-01') as current_season_games,
    CURRENT_DATE - MAX(game_date)::date as days_behind
FROM hoopr_schedule;
"

echo ""
echo "========================================"
echo "INTERPRETATION"
echo "========================================"
echo ""

LATEST=$(psql -d nba_simulator -t -c "SELECT MAX(game_date)::date FROM hoopr_schedule;")
DAYS_BEHIND=$(psql -d nba_simulator -t -c "SELECT CURRENT_DATE - MAX(game_date)::date FROM hoopr_schedule;")

if [ "$DAYS_BEHIND" -eq 0 ]; then
    echo "✅ UP TO DATE - Latest game is today!"
elif [ "$DAYS_BEHIND" -le 2 ]; then
    echo "✅ CURRENT - Only $DAYS_BEHIND days behind"
elif [ "$DAYS_BEHIND" -le 7 ]; then
    echo "⚠️  NEEDS UPDATE - $DAYS_BEHIND days behind"
else
    echo "❌ STALE DATA - $DAYS_BEHIND days behind (latest: $LATEST)"
    echo ""
    echo "Action needed:"
    echo "  1. Start autonomous collection: python scripts/autonomous/autonomous_cli.py start"
    echo "  2. Or run manual sync: Rscript scripts/etl/scrape_hoopr_all_152_endpoints.R --season 2025"
fi

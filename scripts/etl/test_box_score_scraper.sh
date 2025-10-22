#!/bin/bash
set -e

echo "Basketball Reference Box Score Scraper - Test Suite"
echo "===================================================="
echo ""

# Step 1: Insert test games
echo "[1/5] Inserting 10 test games into database..."
sqlite3 /tmp/basketball_reference_boxscores.db << 'EOF'
INSERT OR IGNORE INTO scraping_progress (game_id, game_date, season, home_team, away_team, priority, status)
VALUES
  ('194611010TRH', '1946-11-01', 1947, 'TRH', 'NYK', 9, 'pending'),
  ('194910290TRI', '1949-10-29', 1950, 'TRI', 'FTW', 9, 'pending'),
  ('195412050SYR', '1954-12-05', 1955, 'SYR', 'FTW', 8, 'pending'),
  ('196203020PHW', '1962-03-02', 1962, 'PHW', 'NYK', 7, 'pending'),
  ('197310120BOS', '1973-10-12', 1974, 'BOS', 'BUF', 6, 'pending'),
  ('197910120BOS', '1979-10-12', 1980, 'BOS', 'CLE', 5, 'pending'),
  ('199806140UTA', '1998-06-14', 1998, 'UTA', 'CHI', 4, 'pending'),
  ('201106120DAL', '2011-06-12', 2011, 'DAL', 'MIA', 3, 'pending'),
  ('201606190CLE', '2016-06-19', 2016, 'CLE', 'GSW', 2, 'pending'),
  ('202306120DEN', '2023-06-12', 2023, 'DEN', 'MIA', 1, 'pending');
EOF

echo "✓ Test games inserted"
echo ""

# Step 2: Run scraper
echo "[2/5] Running box score scraper (10 games, ~2 minutes)..."
python scripts/etl/basketball_reference_box_score_scraper.py --max-games 10

echo ""

# Step 3: Check results
echo "[3/5] Checking scraping results..."
scraped_count=$(sqlite3 /tmp/basketball_reference_boxscores.db "SELECT COUNT(*) FROM scraping_progress WHERE status = 'scraped' AND game_id IN ('194611010TRH', '194910290TRI', '195412050SYR', '196203020PHW', '197310120BOS', '197910120BOS', '199806140UTA', '201106120DAL', '201606190CLE', '202306120DEN');")

echo "Games scraped: $scraped_count / 10"

if [ "$scraped_count" -eq 10 ]; then
    echo "✅ All 10 games scraped successfully!"
else
    echo "⚠️  Only $scraped_count games scraped"
fi

echo ""

# Step 4: Verify Wilt's 100-point game
echo "[4/5] Verifying Wilt Chamberlain's 100-point game..."
wilt_points=$(sqlite3 /tmp/basketball_reference_boxscores.db "SELECT points FROM player_box_scores WHERE game_id = '196203020PHW' AND player_name LIKE '%Chamberlain%';" || echo "0")

if [ "$wilt_points" = "100" ]; then
    echo "✅ Wilt scored 100 points (correct!)"
elif [ "$wilt_points" = "0" ]; then
    echo "⚠️  Game not found in database"
else
    echo "⚠️  Wilt's points: $wilt_points (expected 100)"
fi

echo ""

# Step 5: Show summary
echo "[5/5] Summary"
echo "============="
sqlite3 /tmp/basketball_reference_boxscores.db << 'EOF'
SELECT
    game_id,
    game_date,
    status,
    CASE WHEN status = 'scraped' THEN '✅' ELSE '❌' END as result
FROM scraping_progress
WHERE game_id IN (
  '194611010TRH', '194910290TRI', '195412050SYR', '196203020PHW',
  '197310120BOS', '197910120BOS', '199806140UTA', '201106120DAL',
  '201606190CLE', '202306120DEN'
)
ORDER BY game_date;
EOF

echo ""
echo "Test complete!"

# Basketball Reference Box Score Scraper - Test Plan

**Purpose:** Validate the box score scraper across different eras before launching the full 10-day historical backfill.

**Test Date:** To be run after master game list builder completes
**Duration:** ~2 minutes (10 games × 12s rate limit)

---

## Test Games Selection

We'll test 10 carefully selected games spanning all eras of basketball, from the BAA's first game to modern playoffs:

### 1. BAA First Game (1946)
**Game ID:** `194611010TRH`
**Date:** November 1, 1946
**Teams:** New York Knickerbockers @ Toronto Huskies
**URL:** https://www.basketball-reference.com/boxscores/194611010TRH.html
**Why:** BAA's very first game, minimal stats era
**Expected data:** Basic box score only (no steals/blocks/3PT)

### 2. NBA First Game (1949)
**Game ID:** `194910290TRI`
**Date:** October 29, 1949
**Teams:** Fort Wayne Pistons @ Tri-Cities Blackhawks
**URL:** https://www.basketball-reference.com/boxscores/194910290TRI.html
**Why:** First NBA game after BAA-NBL merger
**Expected data:** Basic box score, defunct team names

### 3. Pre-Shot-Clock Era (1954)
**Game ID:** `195412050SYR`
**Date:** December 5, 1954
**Teams:** Fort Wayne Pistons @ Syracuse Nationals
**URL:** https://www.basketball-reference.com/boxscores/195412050SYR.html
**Why:** Before 24-second clock (1955), low-scoring era
**Expected data:** Basic stats, slower pace

### 4. Wilt's 100-Point Game (1962)
**Game ID:** `196203020PHW`
**Date:** March 2, 1962
**Teams:** New York Knicks @ Philadelphia Warriors
**URL:** https://www.basketball-reference.com/boxscores/196203020PHW.html
**Why:** Most famous individual performance in NBA history
**Expected data:** Complete basic stats (but no steals/blocks yet)

### 5. First Season with Steals/Blocks (1974)
**Game ID:** `197310120BOS`
**Date:** October 12, 1974
**Teams:** Buffalo Braves @ Boston Celtics
**URL:** https://www.basketball-reference.com/boxscores/197310120BOS.html
**Why:** First year steals/blocks tracked
**Expected data:** Full basic stats including steals/blocks

### 6. 3-Point Era Begins (1980)
**Game ID:** `197910120BOS`
**Date:** October 12, 1979
**Teams:** Cleveland Cavaliers @ Boston Celtics
**URL:** https://www.basketball-reference.com/boxscores/197910120BOS.html
**Why:** First season with 3-point line
**Expected data:** Basic stats + 3PT attempts/makes

### 7. Modern Stats Era (1998)
**Game ID:** `199806140UTA`
**Date:** June 14, 1998
**Teams:** Chicago Bulls @ Utah Jazz (Finals Game 6)
**URL:** https://www.basketball-reference.com/boxscores/199806140UTA.html
**Why:** Jordan's "Last Shot", modern era stats
**Expected data:** Full stats + some advanced metrics

### 8. Advanced Stats Era (2011)
**Game ID:** `201106120DAL`
**Date:** June 12, 2011
**Teams:** Miami Heat @ Dallas Mavericks (Finals Game 6)
**URL:** https://www.basketball-reference.com/boxscores/201106120DAL.html
**Why:** Modern era with advanced stats
**Expected data:** Full basic + advanced stats

### 9. Play-by-Play Era (2016)
**Game ID:** `201606190CLE`
**Date:** June 19, 2016
**Teams:** Golden State Warriors @ Cleveland Cavaliers (Finals Game 7)
**URL:** https://www.basketball-reference.com/boxscores/201606190CLE.html
**Why:** Historic comeback, full play-by-play available
**Expected data:** Full stats + detailed play-by-play

### 10. Most Recent Finals (2023)
**Game ID:** `202306120DEN`
**Date:** June 12, 2023
**Teams:** Miami Heat @ Denver Nuggets (Finals Game 5)
**URL:** https://www.basketball-reference.com/boxscores/202306120DEN.html
**Why:** Most recent championship-clinching game
**Expected data:** Complete modern data (all tables)

---

## Test Execution

### Step 1: Create Test Game List

First, manually insert these 10 games into the scraping_progress table:

```bash
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
```

### Step 2: Run Box Score Scraper

```bash
# Test on just these 10 games
python scripts/etl/basketball_reference_box_score_scraper.py --max-games 10
```

Expected runtime: ~2 minutes (10 games × 12s)

### Step 3: Verify Results

Check database:

```bash
sqlite3 /tmp/basketball_reference_boxscores.db << 'EOF'
-- Check scraping progress
SELECT game_id, game_date, status, attempts
FROM scraping_progress
WHERE game_id IN (
  '194611010TRH', '194910290TRI', '195412050SYR', '196203020PHW',
  '197310120BOS', '197910120BOS', '199806140UTA', '201106120DAL',
  '201606190CLE', '202306120DEN'
)
ORDER BY game_date;

-- Check games table
SELECT game_id, game_date, home_team, away_team, home_score, away_score
FROM games
WHERE game_id IN (
  '194611010TRH', '194910290TRI', '195412050SYR', '196203020PHW',
  '197310120BOS', '197910120BOS', '199806140UTA', '201106120DAL',
  '201606190CLE', '202306120DEN'
)
ORDER BY game_date;

-- Check player stats count
SELECT g.game_id, g.game_date, COUNT(p.id) as player_count
FROM games g
LEFT JOIN player_box_scores p ON g.game_id = p.game_id
WHERE g.game_id IN (
  '194611010TRH', '194910290TRI', '195412050SYR', '196203020PHW',
  '197310120BOS', '197910120BOS', '199806140UTA', '201106120DAL',
  '201606190CLE', '202306120DEN'
)
GROUP BY g.game_id, g.game_date
ORDER BY g.game_date;
EOF
```

### Step 4: Verify S3 Uploads

```bash
# Check if JSON files were uploaded
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/1946/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/1949/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/1954/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/1962/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/1973/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/1979/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/1998/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/2011/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/2016/ --recursive
aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/box_scores/2023/ --recursive
```

### Step 5: Manual Spot Checks

Verify specific data points from famous games:

**Wilt's 100-point game:**
```sql
SELECT player_name, points, total_rebounds, assists
FROM player_box_scores
WHERE game_id = '196203020PHW' AND player_name LIKE '%Chamberlain%';
-- Expected: Wilt Chamberlain, 100 points
```

**Jordan's Last Shot:**
```sql
SELECT player_name, points, field_goals_made, field_goals_attempted
FROM player_box_scores
WHERE game_id = '199806140UTA' AND player_name LIKE '%Jordan%';
-- Expected: Michael Jordan, 45 points
```

**LeBron's Finals Game 7:**
```sql
SELECT player_name, points, total_rebounds, assists, blocks
FROM player_box_scores
WHERE game_id = '201606190CLE' AND player_name LIKE '%James%';
-- Expected: LeBron James, 27 points, 11 rebounds, 11 assists, 3 blocks
```

---

## Success Criteria

### Must Pass (Critical)
- ✅ All 10 games scraped without errors
- ✅ Status = 'scraped' for all 10 games in scraping_progress
- ✅ Scores in `games` table match Basketball Reference
- ✅ Player counts reasonable (20-30 players per game)
- ✅ All 10 JSON files uploaded to S3
- ✅ Wilt Chamberlain has 100 points in game 196203020PHW

### Should Pass (Important)
- ✅ Team stats populated for all 10 games
- ✅ Advanced stats present for modern games (2011+)
- ✅ Play-by-play data present for recent games (2016+)
- ✅ 3PT stats present for games 1980+
- ✅ Steals/blocks present for games 1974+

### Nice to Have (Optional)
- ✅ Historical team names preserved (Toronto Huskies, etc.)
- ✅ Player slugs extracted from links
- ✅ Location/attendance data captured
- ✅ No Python warnings or errors in log

---

## Expected Issues & Mitigations

### Issue 1: Historical team codes not standardized
**Example:** Toronto Huskies may use different codes
**Mitigation:** Parser extracts team codes from href links, fallback to text

### Issue 2: Missing data in early eras
**Example:** 1946 games won't have steals/blocks
**Mitigation:** Dynamic SQL inserts only available fields

### Issue 3: Play-by-play may not exist for older games
**Example:** 1946-2000 games may have no PBP table
**Mitigation:** Parser gracefully handles missing tables

### Issue 4: Rate limiting during test
**Mitigation:** 12-second delays built in, test only 10 games

---

## Post-Test Actions

### If All Tests Pass:
1. Update todo list (mark task 6 complete)
2. Document any quirks found in historical data
3. Proceed to launch full historical backfill (~10 days)

### If Some Tests Fail:
1. Review error messages in logs
2. Check which eras failed (early vs modern)
3. Fix parser for specific table structures
4. Re-run failed games
5. Only proceed when all 10 pass

### If All Tests Fail:
1. Check if rate-limited (wait longer)
2. Verify database schema matches expectations
3. Test on single game manually
4. Review HTML structure of box score pages
5. May need to adjust table parsing logic

---

## Quick Test Script

Save this as `scripts/etl/test_box_score_scraper.sh`:

```bash
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
wilt_points=$(sqlite3 /tmp/basketball_reference_boxscores.db "SELECT points FROM player_box_scores WHERE game_id = '196203020PHW' AND player_name LIKE '%Chamberlain%';")

if [ "$wilt_points" = "100" ]; then
    echo "✅ Wilt scored 100 points (correct!)"
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
```

Make executable:
```bash
chmod +x scripts/etl/test_box_score_scraper.sh
```

---

**Ready to run:** After master game list builder completes, run `bash scripts/etl/test_box_score_scraper.sh`

# Basketball Reference Box Score Scraping System

**Status:** 🔄 IN DEVELOPMENT
**Version:** 1.0
**Created:** October 18, 2025
**Database:** `/tmp/basketball_reference_boxscores.db`
**Coverage:** BAA (1946-1949) + NBA (1949-2025) = ~70,718 games

---

## Overview

Complete system to scrape and store **ALL** Basketball Reference box scores from the first BAA game (November 1, 1946) through today. Includes player stats, team stats, advanced metrics, four factors, and play-by-play data where available.

**Key URLs:**
- BAA's first game: https://www.basketball-reference.com/boxscores/194611010TRH.html
- NBA's first game: https://www.basketball-reference.com/boxscores/194910290TRI.html
- Example modern box score: https://www.basketball-reference.com/boxscores/195412050SYR.html

---

## System Components

### 1. Database Schema
**File:** `sql/basketball_reference_boxscores_schema.sql`
**Location:** `/tmp/basketball_reference_boxscores.db` (128 KB)

**Tables:**
- `games` - Game metadata (date, teams, scores, location, attendance, etc.)
- `team_box_scores` - Team-level statistics per game
- `player_box_scores` - Player-level statistics per game
- `game_play_by_play` - Play-by-play events (if available)
- `scraping_progress` - Track scraping status with resume capability

**Views:**
- `complete_games` - Games with full data
- `scraping_progress_by_season` - Progress summary
- `player_career_totals` - Aggregated player stats

### 2. Master Game List Builder
**File:** `scripts/etl/build_master_game_list_robust.py`
**Purpose:** Build complete list of all game IDs from 1946-2025

**How it works:**
1. Scrapes Basketball Reference schedule pages for each season
2. Tries both main schedule page AND month-specific pages:
   - `/leagues/NBA_2023_games.html` (main page)
   - `/leagues/NBA_2023_games-october.html` (October)
   - `/leagues/NBA_2023_games-november.html` (November)
   - ... through June
3. Extracts game IDs from box score links
4. Populates `scraping_progress` table with all games
5. Assigns priority (recent = high priority, BAA = low priority)

**Usage:**
```bash
# Test single season (dry run)
python scripts/etl/build_master_game_list_robust.py --start-season 2023 --end-season 2023 --dry-run

# Build complete list (all 79 seasons)
python scripts/etl/build_master_game_list_robust.py

# Build specific range
python scripts/etl/build_master_game_list_robust.py --start-season 1990 --end-season 2000
```

**Priority System:**
```
Priority 1: 2020-2025 (most recent, highest priority)
Priority 2: 2010-2020
Priority 3: 2000-2010
Priority 4: 1990-2000
Priority 5: 1980-1990
Priority 6: 1970-1980
Priority 7: 1960-1970
Priority 8: 1950-1960
Priority 9: 1946-1950 (BAA years, lowest priority)
```

**Estimated Runtime:**
- Per season: ~2 minutes (main page + 9 month pages × 12s rate limit)
- Full run (79 seasons): ~2.6 hours

### 3. Historical Backfill Scraper
**File:** `scripts/etl/basketball_reference_box_score_scraper.py`
**Status:** ✅ CREATED
**Purpose:** Scrape individual box scores for all games in `scraping_progress` table

**Features:**
- Read game IDs from `scraping_progress` table (ordered by priority)
- Scrape each box score page
- Extract all available data:
  - Basic box score (points, rebounds, assists, etc.)
  - Team-level statistics
  - Player-level statistics
  - Advanced stats (where available)
  - Play-by-play (if available)
- Upload raw JSON to S3: `s3://nba-sim-raw-data-lake/basketball_reference/box_scores/{YYYY}/{game_id}.json`
- Load structured data into SQLite tables
- Update `scraping_progress` status
- Resume capability (can be stopped and restarted)
- Error handling (retry failed games up to 3 times)
- Dynamic SQL inserts (handles varying data availability across eras)

**Usage:**
```bash
# Test on single game (dry run)
python scripts/etl/basketball_reference_box_score_scraper.py --max-games 1 --dry-run

# Scrape 100 games (for testing)
python scripts/etl/basketball_reference_box_score_scraper.py --max-games 100

# Scrape all priority 1 games (2020-2025)
python scripts/etl/basketball_reference_box_score_scraper.py --priority 1

# Full run (all pending games)
python scripts/etl/basketball_reference_box_score_scraper.py

# Database only (no S3 uploads)
python scripts/etl/basketball_reference_box_score_scraper.py --no-s3
```

**Estimated Runtime:**
- Per game: ~12 seconds (rate limit)
- 100 games: ~20 minutes
- 1,000 games: ~3.3 hours
- 10,000 games: ~1.4 days
- 70,718 games: ~10 days continuous

### 4. Incremental Daily Scraper
**File:** `scripts/etl/basketball_reference_incremental_scraper.py`
**Status:** ✅ EXISTS (but for aggregate stats, not box scores)
**Purpose:** Scrape new games daily

**To be enhanced:**
- Check for yesterday's games
- Scrape new box scores
- Add to database and S3
- Integrate with overnight 3-source validation workflow

---

## Current Status

### ✅ Completed
1. Database schema designed and created
2. Master game list builder created with:
   - Support for BAA (1946-1949) and NBA (1949-2025)
   - Month-by-month schedule scraping
   - Game ID extraction from HTML
   - Priority assignment
   - Resume capability via `scraping_progress` table

### ✅ Completed
1. Database schema designed and created
2. Master game list builder created with:
   - Support for BAA (1946-1949) and NBA (1949-2025)
   - Month-by-month schedule scraping
   - Game ID extraction from HTML
   - Priority assignment
   - Resume capability via `scraping_progress` table
3. **Historical backfill scraper created** (`basketball_reference_box_score_scraper.py`)
   - Fetches individual box score pages
   - Extracts all available data (basic stats, advanced, four factors, play-by-play)
   - Uploads raw JSON to S3
   - Loads structured data into SQLite
   - Resume capability
   - Error handling with retry logic

### 🔄 In Progress
1. **Testing master game list builder**
   - Validation test running in background
   - Test script: `scripts/etl/test_master_game_list.py`

### 🔜 To Do
1. Complete validation test and verify results
2. Run master game list builder to populate database (~2.6 hours)
3. Test box score scraper on 10 games (different eras)
4. Launch overnight historical backfill (~10 days)
5. Enhance incremental scraper for daily box scores
6. Integrate with overnight 3-source workflow

---

## Rate Limiting

Basketball Reference enforces strict rate limiting:

**Requirements:**
- **12 seconds** between requests (enforced by their servers)
- User-Agent header required
- Cloudflare protection (blocks suspicious requests)

**Our Implementation:**
- Built-in 12-second delay between requests
- Proper User-Agent headers
- Graceful error handling for 429 (Too Many Requests)
- Can handle temporary IP blocks (resume when limits reset)

**Testing Guidelines:**
- Test on 1-2 seasons only (not all 79 at once)
- Use `--dry-run` flag during development
- Wait 5-10 minutes between test runs
- If rate-limited, wait overnight for limits to reset

---

## Game ID Format

Basketball Reference uses consistent game IDs:

**Format:** `YYYYMMDD0XXX`
- `YYYY` = Year (4 digits)
- `MM` = Month (2 digits)
- `DD` = Day (2 digits)
- `0` = Literal "0" separator
- `XXX` = Home team 3-letter code

**Examples:**
- `194611010TRH` = November 1, 1946 at Toronto Huskies (BAA's first game)
- `194910290TRI` = October 29, 1949 at Tri-Cities Blackhawks (NBA's first game)
- `202306120DEN` = June 12, 2023 at Denver Nuggets

**Team Codes:**
Historical teams use Basketball Reference's standardized 3-letter codes (e.g., TRH = Toronto Huskies, FTW = Fort Wayne Pistons).

---

## Data Coverage by Era

| Era | Years | Approx Games | Data Available |
|-----|-------|--------------|----------------|
| **BAA** | 1946-1949 | ~300 | Basic box scores, limited stats |
| **Pre-Shot Clock** | 1950-1954 | ~500 | Basic box scores, scoring, rebounds |
| **Classic NBA** | 1955-1973 | ~12,000 | Basic stats, no steals/blocks until 1973 |
| **Modern Stats** | 1974-1983 | ~10,000 | Basic + steals/blocks/turnovers |
| **3-Point Era** | 1984-1999 | ~20,000 | Basic + 3PT stats |
| **Advanced Era** | 2000-2012 | ~17,000 | Basic + some advanced stats |
| **Modern NBA** | 2013-2025 | ~16,000 | Full stats + play-by-play |

**Total:** ~75,800 games (includes playoffs, play-ins, etc.)

**Note:** Playoff games and special events (All-Star, Christmas) are included.

---

## Storage

### SQLite Database
**Location:** `/tmp/basketball_reference_boxscores.db`
**Purpose:** Structured queries, aggregations, analysis
**Size (when complete):** ~500 MB (estimated)

**Advantages:**
- Fast queries
- Built-in indexes
- SQL aggregations
- Resume capability via `scraping_progress` table

### S3 (Raw JSON)
**Location:** `s3://nba-sim-raw-data-lake/basketball_reference/box_scores/{YYYY}/{game_id}.json`
**Purpose:** Raw data archive, reprocessing capability
**Size (when complete):** ~5-10 GB (estimated)

**Advantages:**
- Original scraped data preserved
- Can reprocess if schema changes
- Backup of all data
- Integration with existing data lake

---

## Integration with Overnight Workflow

Once complete, Basketball Reference box scores will be added to the overnight 3-source validation:

**Current sources:**
1. ESPN API (play-by-play, last 3 days)
2. hoopR (play-by-play, last 3 days)
3. NBA API (play-by-play, last 3 days)

**Will add:**
4. Basketball Reference (box scores, daily incremental)

**Cross-validation:**
- Compare final scores across all 4 sources
- Identify discrepancies
- Track data quality over time

---

## Validation Queries

Once populated, verify data with these queries:

```sql
-- Total games in database
SELECT COUNT(*) FROM games;
-- Expected: ~70,718

-- Games by season
SELECT season, COUNT(*) FROM games GROUP BY season ORDER BY season;

-- Scraping progress
SELECT status, COUNT(*) FROM scraping_progress GROUP BY status;
-- Expected: Most should be 'scraped'

-- Top scorers all-time (sample)
SELECT player_name, SUM(points) as career_points, COUNT(*) as games
FROM player_box_scores
GROUP BY player_name
ORDER BY career_points DESC
LIMIT 10;

-- Data completeness by era
SELECT
    CASE
        WHEN season <= 1949 THEN 'BAA'
        WHEN season <= 1973 THEN 'Classic NBA'
        WHEN season <= 1999 THEN '3-Point Era'
        ELSE 'Modern NBA'
    END as era,
    COUNT(*) as games,
    SUM(has_basic_stats) as with_basic,
    SUM(has_advanced_stats) as with_advanced,
    SUM(has_play_by_play) as with_pbp
FROM games
GROUP BY era
ORDER BY MIN(season);
```

---

## Troubleshooting

### Problem: Rate Limited (429 errors)
**Symptoms:** Scraper returns "429 Too Many Requests"
**Cause:** Too many requests to Basketball Reference in short time
**Solution:**
1. Stop scraping
2. Wait 5-10 minutes (or overnight for heavy rate limiting)
3. Resume - scraper will pick up where it left off

### Problem: Missing games for season
**Symptoms:** Found 102 games for 2023, should be ~1,320
**Possible causes:**
1. Basketball Reference uses different URL structure than expected
2. Some games in JavaScript-rendered content (invisible to BeautifulSoup)
3. Month-based pages don't exist for that year
**Solution:** Run validation test on that specific season with verbose output

### Problem: Historical teams not found
**Symptoms:** Team codes like "FTW" (Fort Wayne) not recognized
**Cause:** Basketball Reference uses special codes for defunct franchises
**Solution:** Extract team codes from hrefs (already implemented in robust scraper)

### Problem: Database locked
**Symptoms:** "Database is locked" error
**Cause:** Another process is using the database
**Solution:** Check for other running scrapers, close connections

---

## Testing Plan

1. **Validate master game list builder** (when rate limits reset)
   ```bash
   python scripts/etl/test_master_game_list.py --verbose
   ```

2. **Test single season thoroughly**
   ```bash
   python scripts/etl/build_master_game_list_robust.py --start-season 2000 --end-season 2000
   ```

3. **Verify database population**
   ```bash
   sqlite3 /tmp/basketball_reference_boxscores.db "SELECT COUNT(*) FROM scraping_progress WHERE season = 2000;"
   ```

4. **Test box score scraper on sample games** (once created)
   ```bash
   # Test on 10 games across different eras
   # BAA (1947), Classic (1965), Modern (1985), Recent (2023)
   ```

5. **Run overnight backfill** (full 79 seasons, ~10 days)

---

## Next Steps

1. **Tonight/Tomorrow:** Run `test_master_game_list.py` when rate limits reset
2. **After validation:** Run full master game list builder (2.6 hours)
3. **Create box score scraper:** Extract data from individual game pages
4. **Test on 10 games:** Verify data extraction across eras
5. **Launch overnight:** Full historical backfill (~10 days)
6. **Add to workflow:** Integrate with overnight 3-source validation

---

## Related Documentation

- Database Schema: `sql/basketball_reference_boxscores_schema.sql`
- Aggregate Stats (current): `docs/phases/phase_0/0.0001_basketball_reference/`
- Overnight Workflow: `docs/OVERNIGHT_3_SOURCE_VALIDATION.md`
- Data Collection Inventory: `docs/DATA_COLLECTION_INVENTORY.md`

---

**For Claude Code:** This system scrapes individual game box scores (different from aggregate season stats). Master game list builder is complete but rate-limited during testing. Next: run validation test overnight, then create historical backfill scraper.

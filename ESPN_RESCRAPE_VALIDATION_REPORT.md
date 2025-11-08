# ESPN Data Re-scraping Validation Report

**Date:** November 8, 2025
**Games Re-scraped:** 400975770, 401070722
**Status:** ✅ **100% SUCCESSFUL**

---

## Executive Summary

Successfully re-scraped 2 missing games using the correct ESPN web scraping format (XHR endpoints) from the 0espn package. All 8 JSON files (4 data types × 2 games) were scraped, validated, and saved to the correct directories in nba-simulator-aws/data/.

**Key Achievement:** Fixed corrupted PBP file for game 400975770 that was missing the 'pbp' key in gamepackage.

---

## Problem Identified

### Game 400975770 - Corrupted PBP File
- **Issue:** Original PBP file in `/Users/ryanranft/0espn/data/nba/nba_pbp/400975770.json` was missing the 'pbp' key
- **Root Cause:** File was scraped using direct API calls instead of XHR web scraping format
- **Impact:** Could not extract play-by-play data for database loading

### Game 401070722 - Incorrect Scraping Method
- **Issue:** Scraped using direct API calls instead of proper web format
- **Impact:** Potential structure inconsistencies with rest of dataset

---

## Re-scraping Process

### Phase 1: Backup API-Scraped Files ✅
**Action:** Converted incorrect API-scraped files to CSV for backup

**Files Backed Up:**
- `backup_api_scrapes/400975770_api.csv` - 836,085 bytes
- `backup_api_scrapes/401070722_api.csv` - 833,656 bytes

**Status:** Complete - Original files preserved for reference

---

### Phase 2: Create ESPN Web Scraper ✅
**Script Created:** `scripts/etl/espn_web_scraper.py`

**Features:**
- ESPN XHR endpoint format (`&_xhr=1`)
- Proper Chrome User-Agent headers
- Rate limiting (0.75s + random 0-0.25s between requests)
- Supports all 4 data types (box_score, pbp, team_stats, schedule)
- Automatic structure validation during scraping
- Comprehensive error handling

**Format Based On:** `/Users/ryanranft/0espn/espn/nba/nba_box_score_json.py` pattern

---

### Phase 3: Re-scrape Games ✅

**Scraping Results:**

#### Game 400975770 (MEM vs CHI, 2018-03-16)
| Data Type | File Size | Status | Details |
|-----------|-----------|--------|---------|
| Box Score | 763,199 bytes | ✅ Success | Complete box score data |
| Play-by-Play | 1,154,803 bytes | ✅ Success | **477 plays** extracted |
| Team Stats | 733,311 bytes | ✅ Success | Team leaders included |
| Schedule | 1,055,864 bytes | ✅ Success | 6 games on 2018-03-16 |

#### Game 401070722 (TOR vs CHA, 2018-10-22)
| Data Type | File Size | Status | Details |
|-----------|-----------|--------|---------|
| Box Score | 782,356 bytes | ✅ Success | Complete box score data |
| Play-by-Play | 1,153,082 bytes | ✅ Success | **444 plays** extracted |
| Team Stats | 771,098 bytes | ✅ Success | Team leaders included |
| Schedule | 1,021,248 bytes | ✅ Success | 9 games on 2018-10-22 |

**Total Scraped:** 8 files, 100% success rate

---

### Phase 4: Validation ✅

**Validation Script:** `scripts/validation/validate_espn_scrape.py`

**Validation Checks:**
1. ✅ File existence
2. ✅ JSON parsability
3. ✅ Top-level structure (`page.content`)
4. ✅ Required gamepackage keys:
   - Box Score: `bxscr`
   - Play-by-Play: `pbp` with `playGrps`
   - Team Stats: `gmLdrs`
   - Schedule: Date-based `events`
5. ✅ Play count validation (300-600 plays per game)
6. ✅ File size sanity checks

**Validation Results:**
```
Total files validated: 8
Passed: 8 (100.0%)
Failed: 0 (0.0%)
```

**✅ All files validated successfully!**

---

### Phase 5: Cleanup ✅

**Deleted Temporary Scripts:**
- `scripts/etl/fetch_missing_pbp.py` (API scraper)
- `scripts/etl/load_missing_pbp_to_espn.py` (Database loader)

**Reason:** These scripts used direct API calls instead of proper web scraping format

**Deleted from 0espn:**
- `/Users/ryanranft/0espn/data/nba/nba_pbp/400975770.json` (corrupted)
- `/Users/ryanranft/0espn/data/nba/nba_pbp/401070722.json` (incorrect format)

---

## Data Storage Locations

All re-scraped data stored in `/Users/ryanranft/nba-simulator-aws/data/`:

### Box Score Files
```
nba_box_score/400975770.json - 763,199 bytes
nba_box_score/401070722.json - 782,356 bytes
```

### Play-by-Play Files
```
nba_pbp/400975770.json - 1,154,803 bytes (477 plays)
nba_pbp/401070722.json - 1,153,082 bytes (444 plays)
```

### Team Stats Files
```
nba_team_stats/400975770.json - 733,311 bytes
nba_team_stats/401070722.json - 771,098 bytes
```

### Schedule Files
```
nba_schedule_json/20180316.json - 1,055,864 bytes (6 games)
nba_schedule_json/20181022.json - 1,021,248 bytes (9 games)
```

---

## Play-by-Play Validation

### Game 400975770 (477 plays)
- **Structure:** ✅ Correct - has `page.content.gamepackage.pbp` key
- **Play Groups:** ✅ 4 quarters of data
- **Play Count:** ✅ 477 plays (within normal range)
- **Data Quality:** ✅ All plays have id, period, clock, text, scores

### Game 401070722 (444 plays)
- **Structure:** ✅ Correct - has `page.content.gamepackage.pbp` key
- **Play Groups:** ✅ 4 quarters of data
- **Play Count:** ✅ 444 plays (within normal range)
- **Data Quality:** ✅ All plays have id, period, clock, text, scores

---

## Comparison: API vs Web Scraping

### API Scraping (Incorrect)
- ❌ Missing 'pbp' key in gamepackage for game 400975770
- ❌ Direct API responses may have different structure
- ❌ Not aligned with 0espn package format
- ❌ Could not be processed by standard loaders

### Web Scraping (Correct - XHR Format)
- ✅ Consistent structure across all games
- ✅ Matches 0espn package format exactly
- ✅ Has all required keys (pbp, playGrps, etc.)
- ✅ Compatible with existing processing pipelines
- ✅ Includes full ESPN web context (ads, analytics, routing, etc.)

---

## Files Created/Modified

### New Scripts
1. `scripts/etl/espn_web_scraper.py` - Production-ready ESPN web scraper
2. `scripts/etl/backup_api_files.py` - JSON to CSV converter for backups
3. `scripts/validation/validate_espn_scrape.py` - ESPN data structure validator

### Backup Files
1. `backup_api_scrapes/400975770_api.csv` - 836,085 bytes
2. `backup_api_scrapes/401070722_api.csv` - 833,656 bytes

### Data Files (8 total)
- 2 box score JSON files
- 2 play-by-play JSON files
- 2 team stats JSON files
- 2 schedule JSON files

### Deleted Files
- `scripts/etl/fetch_missing_pbp.py`
- `scripts/etl/load_missing_pbp_to_espn.py`
- `/Users/ryanranft/0espn/data/nba/nba_pbp/400975770.json`
- `/Users/ryanranft/0espn/data/nba/nba_pbp/401070722.json`

---

## Success Metrics

✅ **100% Scraping Success** - All 8 files downloaded successfully
✅ **100% Validation Pass** - All files have correct structure
✅ **100% Play Count Accuracy** - Both games have valid play counts (477, 444)
✅ **100% Key Presence** - All required gamepackage keys present
✅ **Zero Data Loss** - Original API files backed up as CSV
✅ **Zero Errors** - No exceptions during scraping or validation

---

## Technical Details

### ESPN XHR Endpoints Used
```
Box Score:    https://www.espn.com/nba/boxscore/_/gameId/{game_id}&_xhr=1
Play-by-Play: https://www.espn.com/nba/playbyplay/_/gameId/{game_id}&_xhr=1
Team Stats:   https://www.espn.com/nba/matchup/_/gameId/{game_id}&_xhr=1
Schedule:     https://www.espn.com/nba/schedule/_/date/{YYYYMMDD}&_xhr=1
```

### HTTP Headers
```python
{
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}
```

### Rate Limiting
- Base delay: 0.75 seconds
- Random jitter: 0-0.25 seconds
- Inter-game delay: 1.0 second
- Total scraping time: ~15 seconds for 2 games

---

## Next Steps

1. ✅ **Re-scraping Complete** - All data collected with correct format
2. ⏳ **Database Loading** - Load corrected JSON files into PostgreSQL
3. ⏳ **Coverage Verification** - Re-run coverage analysis to confirm 100%
4. ⏳ **DIMS Update** - Update metrics with new play counts

---

## Conclusion

The ESPN data re-scraping was **100% successful**, fixing the corrupted PBP file for game 400975770 and ensuring both games have complete, correctly formatted data across all 4 data types. The new ESPN web scraper (`espn_web_scraper.py`) is production-ready and follows the exact format used by the 0espn package, ensuring consistency with the existing dataset.

**Critical Fix:** Game 400975770 now has a valid PBP file with 477 plays and the correct `page.content.gamepackage.pbp` structure, resolving the original issue that prevented play-by-play data extraction.

---

**Report Generated:** November 8, 2025
**Validated By:** ESPN Web Scraper v1.0
**Report Version:** 1.0

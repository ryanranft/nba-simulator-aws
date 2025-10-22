# build_master_game_list.py - DEPRECATED

**Status:** Superseded by build_master_game_list_robust.py
**Deprecated:** October 22, 2025
**Reason:** Unable to handle historical BAA (1946-1949) teams and defunct franchises

---

## Why Deprecated

This script used the `basketball_reference_web_scraper` library which has limitations:
- ❌ Cannot handle BAA (Basketball Association of America) years 1946-1949
- ❌ Fails on defunct franchises and historical team names
- ❌ Library doesn't support all team enums from historical eras
- ⏱️ Runtime: 3-5 minutes (faster but incomplete)

## Replacement

**Use instead:** `scripts/etl/build_master_game_list_robust.py`

The robust version:
- ✅ Handles all 79 seasons (1946-2025)
- ✅ Direct HTML parsing of Basketball Reference schedule pages
- ✅ Works with BAA, NBA, and all defunct franchises
- ✅ Extracts game IDs directly from box score links
- ⏱️ Runtime: 15-20 minutes (slower but comprehensive)

## Migration Path

If you were using:
```bash
python scripts/etl/build_master_game_list.py
```

Replace with:
```bash
python scripts/etl/build_master_game_list_robust.py
```

All command-line arguments are identical:
- `--start-season` - Starting season (default: 1947)
- `--end-season` - Ending season (default: 2025)
- `--dry-run` - Test mode

## Technical Details

### What Was Removed
- **File:** build_master_game_list.py (283 lines)
- **Library dependency:** basketball_reference_web_scraper (client.season_schedule)
- **Approach:** Library-based API calls
- **Coverage:** Partial (failed on BAA years)

### What Replaced It
- **File:** build_master_game_list_robust.py (471 lines)
- **Approach:** Direct HTML parsing with BeautifulSoup
- **Coverage:** Complete (all 79 seasons, all 70,718+ games)
- **Rate limiting:** 12 seconds (same as original)

## Historical Context

Created: October 18, 2025 (Version 2.0)
- Initial implementation using basketball_reference_web_scraper library
- Faster execution (3-5 minutes)
- Worked well for modern NBA (1950+)

Superseded: October 18, 2025 (by Version 3.0 robust)
- Discovered library limitations with historical data
- Created robust HTML parser to handle all years
- Slower but comprehensive (15-20 minutes)

## Archived Location

Original file archived at:
- `scripts/archive/deprecated/build_master_game_list.py` (283 lines)

## Impact

- **Scrapers affected:** 0 (robust version already in use)
- **Active scrapers:** 82 (down from 83)
- **Code reduction:** 283 lines of superseded code
- **Functionality lost:** None (all functionality in robust version)

## Related Files

- ✅ **Active:** build_master_game_list_robust.py (471 lines)
- ✅ **Active:** basketball_reference_box_score_scraper.py (uses scraping_progress table)
- 📚 **Documentation:** docs/data_collection/scrapers/FRAMEWORK_MIGRATION_PLAN.md

---

**Generated with [Claude Code](https://claude.com/claude-code)**
**Session 7: Redundancy Analysis**
**October 22, 2025**

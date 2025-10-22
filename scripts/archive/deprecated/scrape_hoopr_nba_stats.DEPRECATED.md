# scrape_hoopr_nba_stats.py - DEPRECATED

**Deprecated:** October 22, 2025 (Session 7)
**Reason:** Duplicate functionality - replaced by scrape_hoopr_complete_all_endpoints.py

## Why Deprecated

This scraper only implements the 4 bulk data loaders:
- load_nba_pbp
- load_nba_team_boxscore  
- load_nba_player_boxscore
- load_nba_schedule

`scrape_hoopr_complete_all_endpoints.py` has the EXACT SAME bulk loader functionality (in its `scrape_bulk_loaders()` method, lines 269-332) PLUS 150+ additional NBA Stats API endpoints.

## Replacement

Use `scrape_hoopr_complete_all_endpoints.py` instead:

```bash
# Old approach (deprecated):
python scripts/etl/scrape_hoopr_nba_stats.py --season 2024 --all-endpoints

# New approach (recommended):
python scripts/etl/scrape_hoopr_complete_all_endpoints.py --seasons 2024
```

## Migration Impact

- **Code reduction:** 408 lines of duplicate code eliminated
- **No functionality lost:** All capabilities preserved in comprehensive scraper
- **No workflow breakage:** No active scripts referenced this file

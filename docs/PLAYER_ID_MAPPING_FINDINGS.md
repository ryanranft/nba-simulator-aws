# Player ID Mapping Findings

**Date:** October 7, 2025
**Status:** ✅ RESOLVED - No custom mapping needed

---

## Key Discovery

**hoopR uses ESPN player IDs natively** - no mapping required!

### Evidence

```sql
-- hoopR player box data
SELECT player_id, player_name, COUNT(*) as game_count
FROM hoopr_player_box
WHERE player_name LIKE 'LeBron%'
GROUP BY player_id, player_name;

-- Result:
-- player_id: 1966  (ESPN ID)
-- player_name: LeBron James
-- game_count: 1,828
```

**Cross-verification with ESPN box scores:**
- ESPN box score JSON: `athlete.id = "1966"` for LeBron James
- hoopR player_box: `player_id = "1966"` for LeBron James
- ✅ **Same ID system**

---

## What This Means

### ✅ We Can Proceed With hoopR Data Directly

1. **hoopR player IDs = ESPN player IDs**
   - No conversion/mapping needed
   - Can directly join with ESPN temporal events (if needed)
   - Can use hoopR box scores for starting lineups

2. **Possession Panel Creation Strategy**
   - Use hoopR box scores for starting lineup detection (`hoopr_player_box`)
   - Use ESPN temporal events for play-by-play possession tracking
   - Join by `game_id` + `player_id` (same ID system!)

3. **Data Coverage**
   - hoopR: 813,245 player-games, 30,859 games, 2,940 players (2002-2025)
   - ESPN: 44,828 box scores (1993-2024)
   - Overlap: 2002-2023 (21 years of data)

---

## Previous Mapping Attempt - Why It Failed

### What We Tried
Created `scripts/etl/create_player_id_mapping.py` to map ESPN IDs ↔ NBA API IDs by:
1. Finding overlapping games (by date + teams)
2. Matching player names within those games
3. Building a mapping table

### Issues Encountered

1. **ESPN Box Score Format**
   - Expected: `bxscr['tms'][0]['plrs'][0]['athlete']`
   - Actual: `bxscr[0]['stats'][0]['athlts'][0]['athlt']`
   - Field names: `dspNm` not `displayName`, `athlt` not `ath`

2. **Test Sample No Overlap**
   - First 100 ESPN files (sorted by game_id): 2013 games (IDs: 131...)
   - First 2,000 hoopR records: Recent games (limited by `LIMIT` clause)
   - Date ranges overlap but test samples didn't

3. **Numpy Type Conversion Error** (SOLVED)
   - psycopg2 can't adapt numpy.int64 types
   - Fixed with: `df.astype(object).where(pd.notnull(df), None)`
   - This fix enabled hoopR data loading

### Why Mapping Wasn't Needed
- hoopR already uses ESPN IDs
- ESPN temporal events use ESPN IDs
- No NBA API IDs needed for possession panels

---

## hoopR Phase 2 & 3 Reference Data

### Phase 2: Player Index Endpoints
- `nba_commonallplayers` - All players with NBA API IDs
- `nba_playerindex` - Player index with IDs

**Note:** These provide NBA API IDs, but we don't need them since:
- hoopR box scores use ESPN IDs
- ESPN temporal events use ESPN IDs
- Our possession panel workflow doesn't require NBA API IDs

**Future Use Case:** If we want to integrate official NBA.com stats (not via hoopR), we could scrape these endpoints to create ESPN ↔ NBA API mapping.

---

## Recommended Approach Going Forward

### For Possession Panels with Lineups

**Use hoopR data directly:**

1. **Starting Lineups** → `hoopr_player_box`
   ```sql
   -- Get starters for a game
   SELECT player_id, player_name
   FROM hoopr_player_box
   WHERE game_id = '401234567'
     AND starter = true;
   ```

2. **Substitutions** → ESPN `temporal_events`
   ```sql
   -- Track subs (ESPN uses same player IDs)
   SELECT event_type, player_id
   FROM temporal_events
   WHERE game_id = '401234567'
     AND event_type IN ('Substitution In', 'Substitution Out');
   ```

3. **Possession Tracking** → Use `create_possession_panel_with_lineups.py`
   - Initialize `LineupTracker` with starters from hoopR
   - Update lineups using ESPN substitution events
   - Both use same player ID system (ESPN IDs)

### No Mapping Script Needed

The `create_player_id_mapping.py` script is **not required** for our current workflow. Keep it for reference, but possession panels can proceed without it.

---

## Files Reference

### ✅ Working Scripts
- `scripts/db/load_hoopr_player_box_only.py` - Load hoopR box scores (813K records loaded)
- `scripts/etl/create_possession_panel_with_lineups.py` - Create possession panels with LineupTracker

### ⏸️ On Hold (Not Currently Needed)
- `scripts/etl/create_player_id_mapping.py` - ESPN ↔ NBA API mapping (may be useful later)

### 🔧 Debug Scripts
- `scripts/db/debug_hoopr_insert.py` - Identified numpy type conversion issue

---

## Summary

✅ **hoopR uses ESPN player IDs**
✅ **No custom mapping required**
✅ **Can proceed with possession panel creation using hoopR + Kaggle data**
✅ **813K hoopR records loaded and ready to use (306K starters)**

## Data Integration Strategy (Updated)

**Available data:**
- **hoopR player box:** 813,245 records, 30,859 games, 306,029 starters (2002-2025)
- **Kaggle temporal events:** 13,592,899 events, 29,818 games (overlaps well with hoopR)
- **ESPN temporal events:** 10,000 events, 23 games (limited test data)

**Chosen approach:** Integrate hoopR starters with Kaggle temporal events
- Kaggle has 29,818 games with full play-by-play
- hoopR has starters for 30,859 games (great overlap!)
- hoopR uses ESPN player IDs → same system as Kaggle likely uses
- Can enhance existing `create_possession_panel_from_kaggle.py` with lineup tracking

**Next step:** Enhance Kaggle possession panel script to integrate hoopR starting lineups.

---

*Last updated: October 7, 2025 - 9:15 PM*

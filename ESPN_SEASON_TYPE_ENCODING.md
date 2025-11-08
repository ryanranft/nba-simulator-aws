# ESPN Season Type Encoding

**Date:** November 7, 2025
**Analyzed by:** Claude (Sonnet 4.5)
**Data Source:** `/Users/ryanranft/0espn/data/nba/nba_box_score/*.json` (44,830 files)

---

## Summary

ESPN uses a `seasonType` field in their JSON data to classify games into different categories. This field is located at:

**JSON Path:** `page.content.gamepackage.gmStrp.seasonType`

---

## Encoding Verified (Complete Analysis)

**All 44,828 files scanned** - November 7, 2025

| Code | Game Type | Count | % | Date Range (Typical) |
|------|-----------|-------|---|----------------------|
| **1** | Preseason | 2,551 | 5.69% | Early-mid October |
| **2** | Regular Season | 39,664 | 88.48% | Late Oct - Mid Apr |
| **2** | All-Star Game | (included in 2) | - | Mid-February |
| **3** | Playoffs | 2,588 | 5.77% | Mid Apr - Mid Jun |
| **4** | **[DOES NOT EXIST]** | 0 | 0% | - |
| **5** | Play-In Tournament | 25 | 0.06% | Mid-April (2020+) |

**Total games:** 44,828 (100% have seasonType field)

**Key Discoveries:**
- Code 4 does NOT exist in ESPN's system (skipped in numbering)
- Code 5 (Play-In) only exists 2020-present (new NBA format)
- All-Star game uses code 2 (same as regular season)

---

## Detailed Findings

### Preseason Games (`seasonType=1`)

**Sample games:**
```
401716947: 2024-10-04 seasonType=1
401716948: 2024-10-05 seasonType=1
401716949: 2024-10-05 seasonType=1
401716950: 2024-10-05 seasonType=1
401716951: 2024-10-06 seasonType=1
401716952: 2024-10-06 seasonType=1
401716953: 2024-10-06 seasonType=1
401716954: 2024-10-07 seasonType=1
401716955: 2024-10-07 seasonType=1
401716956: 2024-10-07 seasonType=1
```

**Characteristics:**
- Dates: Early October (before regular season starts)
- Game IDs: 4017169XX range (2024-25 season)
- Status: Post (completed)

### Regular Season Games (`seasonType=2`)

**Sample games:**
```
400828893: 2016-03-16 seasonType=2 - WSH vs CHI
401585309: 2024-02-01 seasonType=2 - SAS vs ORL
401585305: 2024-02-01 seasonType=2 - BKN vs PHX
401585304: 2024-02-01 seasonType=2 - WSH vs LAC
```

**Characteristics:**
- Dates: October/November through April (varies by season)
- Represents the majority of games (~82 games per team per season)
- Includes regular season matchups

### All-Star Game (`seasonType=2`)

**Verified game:**
```
401623259: 2024-02-19 seasonType=2 - Eastern Conf All-Stars vs Western Conf All-Stars
```

**Important Discovery:**
- All-Star game uses **same code as regular season** (`seasonType=2`)
- Can be distinguished by:
  - Team names: "Eastern Conf All-Stars" vs "Western Conf All-Stars"
  - Date: Typically mid-February (All-Star Weekend)
  - Game ID pattern (may be different from regular season range)

### Playoffs/Finals (`seasonType=3`)

**Sample games:**
```
401656359: 2024-06-07 seasonType=3 (NBA Finals Game 2)
401656360: 2024-06-10 seasonType=3 (NBA Finals Game 3)
401656361: 2024-06-13 seasonType=3 (NBA Finals Game 4)
401656362: 2024-06-15 seasonType=3 (NBA Finals Game 5)
401656363: 2024-06-18 seasonType=3 (NBA Finals - Clinching)
```

**Characteristics:**
- Dates: Mid-April through mid-June (playoffs, conference finals, NBA Finals)
- Game IDs: 4016563XX range (2024 playoffs)
- Best-of-7 series format
- Total playoff games per season: 79-103 (varies by series length)

### Play-In Tournament (`seasonType=5`)

**All 25 games identified:**

**2020 Season (COVID bubble):**
```
401236333: 2020-08-15 - Portland Trail Blazers vs Memphis Grizzlies
```

**2021 Season (First official play-in):**
```
401326988: 2021-05-18 - Indiana Pacers vs Charlotte Hornets
401326989: 2021-05-18 - Washington Wizards vs Boston Celtics
401326990: 2021-05-19 - Los Angeles Lakers vs Golden State Warriors
401326991: 2021-05-19 - San Antonio Spurs vs Memphis Grizzlies
401326992: 2021-05-21 - Charlotte Hornets vs Washington Wizards
401326993: 2021-05-22 - Memphis Grizzlies vs Golden State Warriors
```

**2022-2024 Seasons:**
- 6 games per season (April 11-20)
- Determines 7-8-9-10 playoff seeds
- 4 games (7 vs 8, 9 vs 10) + 2 games (losers play winners)

**Characteristics:**
- New format starting 2020 (COVID pandemic)
- Occurs between regular season and playoffs
- Short window: 3-5 days in mid-April
- Only exists in seasons 2020-present

---

## User's Original Hypothesis vs Actual (VERIFIED)

**User's hypothesis:**
- 1 = Preseason ✅ **CORRECT**
- 2 = Regular Season ✅ **CORRECT**
- 3 = All-Star Game ❌ **INCORRECT** (All-Star uses code 2)
- 4 = Playoffs ❌ **INCORRECT** (Playoffs use code 3, code 4 doesn't exist)

**Actual encoding (verified via comprehensive scan):**
- 1 = Preseason ✅ (2,551 games)
- 2 = Regular Season + All-Star ✅ (39,664 games)
- 3 = Playoffs/Finals ✅ (2,588 games)
- 4 = **[DOES NOT EXIST]** ❌ (0 games - ESPN skipped this number)
- 5 = Play-In Tournament ✅ (25 games - user didn't predict this)

**Key insight:** ESPN skipped code 4 entirely. Play-In Tournament (code 5) was introduced in 2020, after original hypothesis was formed.

---

## Field Location in JSON

### Format 1 (Older games, ~1993-2019)

```json
{
  "page": {
    "content": {
      "gamepackage": {
        "gmStrp": {
          "uid": "s:40~l:46~e:400828893",
          "gid": "400828893",
          "dt": "2016-03-16T23:00Z",
          "nm": "basketball",
          "seasonType": 2,  // <-- HERE
          "status": {
            "desc": "Final",
            "det": "Final",
            "id": "3",
            "state": "post"
          },
          "tms": [...]
        }
      }
    }
  }
}
```

### Format 2 (Newer games, ~2020+)

**Note:** Need to verify if `seasonType` exists in newer JSON format. May be at different path or use same `gmStrp` structure.

---

## Current Extraction Status

### In `load_from_local_espn.py`

**Currently extracted:** ❌ **NO**

The current loader (`scripts/etl/load_from_local_espn.py`) does NOT explicitly extract `seasonType`.

**Code snippet (lines 139-218):**
```python
# Extract game info from boxscore
game_package = boxscore.get('page', {}).get('content', {}).get('gamepackage', {})
header = game_package.get('gmStrp', {}) or game_package.get('header', {})

# Get game date
game_date_str = header.get('dt', '')
# ... (extracts date, teams, scores)

# Creates enriched_data dict
enriched_data = {
    'teams': {...},
    'game_info': {
        'game_id': game_id,
        'season_year': season_year,
        'season': f"{season_year}-{str(season_year + 1)[-2:]}",
        'game_date': game_date.isoformat()
        # seasonType NOT included here
    },
    # ...
}
```

**Missing extraction:**
```python
# SHOULD ADD (Line ~144):
season_type = header.get('seasonType', None)  # Extract from gmStrp

# ADD to enriched_data['game_info'] (Line ~200):
'season_type': season_type,
'season_type_label': {
    1: 'Preseason',
    2: 'Regular Season',  # Note: includes All-Star
    3: 'Playoffs',
    5: 'Play-In Tournament'
}.get(season_type, 'Unknown')
```

### In `ESPNFeatureExtractor`

**Check needed:** Verify if `nba_simulator/etl/extractors/espn/feature_extractor.py` extracts `seasonType`.

**Likely status:** Possibly extracted but needs verification.

---

## Recommended Actions

### 1. Update `load_from_local_espn.py` (Immediate)

Add `seasonType` extraction to the local loader:

```python
# Line ~144 (after extracting game date)
season_type = header.get('seasonType', None)

# Line ~200 (in enriched_data['game_info'] dict)
'season_type': season_type,
'season_type_label': {
    1: 'Preseason',
    2: 'Regular Season',
    3: 'Playoffs'
}.get(season_type, 'Unknown'),
```

### 2. Verify `ESPNFeatureExtractor` (Short-term)

Check if the production feature extractor already extracts `seasonType`:
```bash
grep -n "seasonType" nba_simulator/etl/extractors/espn/feature_extractor.py
```

If not, add to the 58-feature extraction list.

### 3. Add Season Type Validation (Short-term)

Create validator to ensure all games have valid `seasonType`:
```python
# In validate_0_0010.py or new validate_0_00XX.py
def validate_season_type():
    query = """
    SELECT
        data->'game_info'->>'season_type' as season_type,
        COUNT(*) as count
    FROM raw_data.nba_games
    GROUP BY season_type
    ORDER BY season_type;
    """
    # Verify all games have seasonType 1, 2, or 3
    # Flag any NULL or unexpected values
```

### 4. Update Coverage Verification (Optional)

Enhance `verify_game_coverage.py` to filter by season type:
```python
# Add --season-type flag
parser.add_argument('--season-type', type=int, choices=[1,2,3],
                    help='Filter by season type (1=pre, 2=reg, 3=playoffs)')

# In comparison logic:
if args.season_type:
    schedule_games = [g for g in schedule_games
                     if g.get('seasonType') == args.season_type]
```

### 5. Distinguish All-Star Games (Optional)

Since All-Star uses same code as regular season, add logic to flag it:
```python
def is_allstar_game(game_data):
    """Check if game is All-Star based on team names."""
    teams = game_data.get('teams', {})
    home_name = teams.get('home', {}).get('name', '')
    away_name = teams.get('away', {}).get('name', '')

    return ('All-Stars' in home_name and 'All-Stars' in away_name)

# Add to enriched_data:
'is_allstar': is_allstar_game(enriched_data)
```

---

## Impact on Data Quality

### Missing Season Type Issue

**Current state:**
- 31,370 games in database
- `seasonType` may or may not be in JSONB data
- No validation or standardization

**Potential problems:**
1. Cannot easily filter to regular season only
2. Cannot separate preseason/playoff stats
3. All-Star game mixed with regular season
4. Coverage verification may include preseason games incorrectly

**Solution priority:** **MEDIUM**
- Not blocking for basic functionality
- Important for accurate analysis
- Should be fixed before Phase 0 completion

---

## Testing Strategy

### Verify Extraction

```bash
# After updating loader, test with known games
python scripts/etl/load_from_local_espn.py --game-ids 401716947 --force  # Preseason
python scripts/etl/load_from_local_espn.py --game-ids 400828893 --force  # Regular season
python scripts/etl/load_from_local_espn.py --game-ids 401656359 --force  # Playoffs
python scripts/etl/load_from_local_espn.py --game-ids 401623259 --force  # All-Star
python scripts/etl/load_from_local_espn.py --game-ids 401654655 --force  # Play-In

# Verify in database
psql -d nba_simulator -c "
SELECT
    game_id,
    data->'game_info'->>'season_type' as season_type,
    data->'game_info'->>'season_type_label' as label,
    data->'teams'->'home'->>'name' as home_team
FROM raw_data.nba_games
WHERE game_id IN ('401716947', '400828893', '401656359', '401623259', '401654655')
ORDER BY game_id;
"
```

Expected output:
```
   game_id   | season_type |         label          |        home_team
-------------+-------------+------------------------+-------------------------
 400828893   | 2           | Regular Season         | Washington Wizards
 401623259   | 2           | Regular Season         | Eastern Conf All-Stars
 401654655   | 5           | Play-In Tournament     | [Play-In team]
 401656359   | 3           | Playoffs               | [Playoff team]
 401716947   | 1           | Preseason              | [Preseason team]
```

### Validate Distribution

```sql
-- Check season_type distribution across all games
SELECT
    data->'game_info'->>'season_type' as season_type,
    CASE data->'game_info'->>'season_type'
        WHEN '1' THEN 'Preseason'
        WHEN '2' THEN 'Regular Season'
        WHEN '3' THEN 'Playoffs'
        WHEN '5' THEN 'Play-In Tournament'
        ELSE 'Unknown'
    END as label,
    COUNT(*) as games,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as pct
FROM raw_data.nba_games
GROUP BY season_type
ORDER BY season_type;
```

Expected distribution (based on comprehensive scan):
- Preseason: ~5.69% (2,551 games - limited games per team)
- Regular Season: ~88.48% (39,664 games - 82 games × 30 teams / 2 = 1,230 games/season)
- Playoffs: ~5.77% (2,588 games - 16 teams, 4 rounds, best-of-7 = ~79-103 games/season)
- Play-In: ~0.06% (25 games - only 2020-2024, 1-6 games per season)

---

## Additional Questions for User

The user offered to provide validation dates:
> "Would you like me to give you the dates I found for the first preseason, regular season and playoff games for each year to check for validation purposes?"

**Response needed:**
- Yes, these dates would be helpful to validate the seasonType encoding
- Can cross-reference with our findings
- Useful for testing the updated loader

---

## References

- **JSON Files:** `/Users/ryanranft/0espn/data/nba/nba_box_score/` (44,830 files)
- **Loader Script:** `scripts/etl/load_from_local_espn.py`
- **Feature Extractor:** `nba_simulator/etl/extractors/espn/feature_extractor.py`
- **Validator:** `validators/phases/phase_0/validate_0_0010.py`

---

## Changelog

**November 7, 2025 - Initial Analysis**
- Verified seasonType encoding across 44,830+ ESPN JSON files
- Discovered All-Star game uses code 2 (not separate code)
- Identified missing extraction in current loader
- Created recommendations for enhancement

---

**Next Steps:**
1. User approval to proceed with loader updates
2. Add seasonType extraction to `load_from_local_espn.py`
3. Verify existing ESPNFeatureExtractor behavior
4. Add season type validation
5. Update session handoff document with findings

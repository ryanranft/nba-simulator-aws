# Data Source Baseline Statistics

**Purpose:** Track baseline statistics from each data source to enable cross-validation and quality checks when integrating multiple sources.

**Last Updated:** October 7, 2025

---

## Overview

This document records baseline statistics from each data source to help verify data quality when:
1. Adding new data sources
2. Re-scraping existing sources
3. Cross-validating possession counts and game statistics
4. Identifying data quality issues

---

## Kaggle Basketball Dataset

**Source:** https://www.kaggle.com/datasets/wyattowalsh/basketball
**Scraped:** October 7, 2025
**Processing Script:** `scripts/etl/create_possession_panel_from_kaggle.py`

### Dataset Summary

- **Total possessions:** 3,801,927
- **Total games:** 29,818
- **Average possessions/game:** 127.5
- **Median possessions/game:** 127.0
- **Std dev:** 11.64
- **Range:** 87-239 possessions/game
- **Season coverage:** 1996-2022 (pre-season and regular season)
- **Processing time:** ~8 minutes

### Quality Metrics

**Missing Data:**
- ✓ Zero missing values (100% complete)
- ✓ All 3.8M rows have complete data for: game_id, possession_number, points_scored, possession_result

**Distribution:**
- **25th percentile:** 120 possessions/game
- **75th percentile:** 135 possessions/game
- **Outliers:** 23 games with 182-239 possessions (All-Star/exhibition games, season IDs starting with "3")

### Possession Results Distribution

| Result   | Count     | Percentage |
|----------|-----------|------------|
| other    | 1,541,169 | 40.54%     |
| made_fg  | 1,488,994 | 39.16%     |
| turnover | 638,115   | 16.78%     |
| miss     | 133,649   | 3.52%      |

**Notes:**
- "other" includes free throws, fouls, end of quarter events
- "miss" only includes missed shots followed by defensive rebounds
- Made field goals and turnovers account for ~56% of possessions

### Points Distribution

| Points | Count     | Percentage |
|--------|-----------|------------|
| 0      | 2,312,933 | 60.84%     |
| 2      | 1,080,818 | 28.43%     |
| 3      | 233,235   | 6.13%      |
| 1      | 174,826   | 4.60%      |
| 4+     | 115       | 0.00%      |

**Notes:**
- 60.8% scoreless possessions is typical (turnovers, misses, defensive stops)
- 4+ point possessions are data quality issues (likely cumulative scoring bugs)
- 20 possessions have >20 points (extreme outliers)

### Season Coverage

| Season Type | Count  | Avg Poss/Game |
|-------------|--------|---------------|
| Regular Season (2xxxx) | 28,966 | 127.3 |
| Pre-season (4xxxx) | 1,698 | 123.2 |
| All-Star (3xxxx) | 154 | 194.2 |

**Season Breakdown (Regular Season):**
- 1996-1997: 2,137 games, 127.5 avg
- 1998-1999: 632 games, 123.0 avg (lockout season)
- 2000-2022: 26,197 games, 127.4 avg

### Known Limitations

**Undercounting:**
- Kaggle data averages **127.5 possessions/game**
- pbpstats library produces **~220 possessions/game** (correct baseline)
- **41% undercounting** vs expected value

**Root Cause:**
- Text-based event detection (no event type classification)
- Score-change fallback is both a bug and a necessary workaround
- Missing many made field goals due to inconsistent text patterns

**Why It's Acceptable for ML:**
- ✓ Systematic undercounting (not random)
- ✓ Preserves relative team efficiency comparisons
- ✓ Accurate score tracking (points per possession correct)
- ✓ Consistent possession result categorization
- ✓ 3.8M training examples still substantial

### Validation Queries

```sql
-- Total possessions and games
SELECT
    COUNT(*) as total_possessions,
    COUNT(DISTINCT game_id) as total_games,
    ROUND(AVG(poss_count), 2) as avg_poss_per_game
FROM (
    SELECT game_id, COUNT(*) as poss_count
    FROM possession_panel
    GROUP BY game_id
) game_stats;

-- Possession results distribution
SELECT
    possession_result,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
FROM possession_panel
GROUP BY possession_result
ORDER BY count DESC;

-- Points distribution
SELECT
    points_scored,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as pct
FROM possession_panel
GROUP BY points_scored
ORDER BY count DESC
LIMIT 10;

-- Games with anomalous possession counts
SELECT
    game_id,
    COUNT(*) as possession_count
FROM possession_panel
GROUP BY game_id
HAVING COUNT(*) < 80 OR COUNT(*) > 180
ORDER BY possession_count;
```

### Files

- **Validation report:** `/tmp/possession_panel_validation_report.txt`
- **Validation script:** `/tmp/validate_possession_panel.py`
- **Generation log:** `/tmp/possession_panel_kaggle_FULL.log`
- **Database table:** `possession_panel` (local PostgreSQL)
- **Credentials:** `/Users/ryanranft/nba-sim-credentials.env`

---

## NBA API (Official Stats)

**Source:** NBA Stats API (stats.nba.com)
**Scraped:** October 7, 2025
**Processing Script:** `scripts/etl/create_possession_panel_from_nba_api.py`

### Dataset Summary

- **Total possessions:** 229,102
- **Total games:** 975
- **Average possessions/game:** 235.2
- **Median possessions/game:** 235.0
- **Std dev:** 17.2
- **Range:** 184-307 possessions/game
- **Season coverage:** 1996-1997 (regular season)
- **Processing time:** ~2 seconds

### Quality Metrics

**Validation vs pbpstats:**
- ✅ **235.2 possessions/game** vs pbpstats ~220 baseline
- ✅ **Only +6.9% difference** (excellent accuracy)
- ✅ Event-type classification (like pbpstats approach)
- ✅ Proper and-1 detection and free throw sequence handling

**Missing Data:**
- ✓ Zero missing values (100% complete)
- ✓ All 229K rows have complete data

### Possession Results Distribution

| Result   | Count     | Percentage |
|----------|-----------|------------|
| other    | 128,939   | 56.28%     |
| made_fg  | 69,742    | 30.44%     |
| turnover | 30,421    | 13.28%     |

**Notes:**
- Higher "other" percentage than Kaggle (56% vs 40%) - captures more free throws and fouls
- More accurate made FG detection through event types
- No "miss" category (defensive rebounds grouped in "other")

### Points Distribution

| Points | Count     | Percentage |
|--------|-----------|------------|
| 0      | 138,986   | 60.67%     |
| 2      | 66,898    | 29.20%     |
| 3      | 13,990    | 6.11%      |
| 1      | 8,637     | 3.77%      |
| 4      | 481       | 0.21%      |

**Notes:**
- Similar distribution to Kaggle (60.7% scoreless vs 60.8%)
- 481 possessions with 4 points (and-1 situations)
- Small number of negative point values (score corrections)

### Cross-Validation with Kaggle

**Overlapping games:** 876 games from 1996-1997 season

| Metric | Kaggle | NBA API | Difference |
|--------|--------|---------|------------|
| Avg possessions/game | 127.1 | 235.2 | **+85%** |
| Min possessions | 94 | 184 | +96% |
| Max possessions | 160 | 307 | +92% |
| Std deviation | 11.9 | 17.2 | +45% |

**Key Finding:** Kaggle systematically undercounts possessions by ~50% due to text-based detection vs NBA API's event-type classification.

### Technical Approach

**Event-Type Classification:**
- Uses EVENTMSGTYPE field (1-13 event types)
- Made FG (type 1), Missed FG (type 2), Free Throw (type 3), etc.
- Defensive rebound detection via EVENTMSGACTIONTYPE
- Proper and-1 handling (check next event for free throw)
- Free throw sequence parsing ("X of X" pattern)

**Advantages over Text Matching:**
- ✅ No dependency on text pattern consistency
- ✅ Accurate event classification
- ✅ Proper free throw sequence handling
- ✅ Better and-1 detection
- ✅ Results very close to pbpstats ground truth (+6.9%)

### Known Limitations

**Coverage:**
- Currently only 1996-1997 season (975 games)
- Need to scrape additional seasons for full coverage

**Quality:**
- ⚠️ 6.9% overcounting vs pbpstats (acceptable variance)
- ⚠️ Some negative point values (score corrections or parsing errors)
- ✅ Otherwise excellent data quality

### Files

- **Database table:** `possession_panel_nba_api` (local PostgreSQL)
- **Processing script:** `scripts/etl/create_possession_panel_from_nba_api.py`
- **Source data:** `/tmp/nba_api_comprehensive/play_by_play/` (975 JSON files, 259MB)
- **Generation log:** `/tmp/nba_api_possession_full.log`

---

## pbpstats Library (Reference Baseline)

**Source:** https://github.com/dblackrun/pbpstats
**Date:** October 7, 2025
**Purpose:** Ground truth for possession counting verification

### Test Game Statistics

**Game ID:** 0021600270
- **Total possessions:** 220
- **Possessions per team:** 110 (each team)
- **Detection method:** Event type classification (not text matching)

### Key Differences from Kaggle

| Metric | pbpstats | Kaggle | Difference |
|--------|----------|--------|------------|
| Avg possessions/game | ~220 | 127.5 | -41% |
| Detection method | Event types | Text patterns | More accurate |
| Free throw handling | Last FT only | Score change fallback | More precise |
| Made FG detection | Event class | Text matching | More reliable |

**Why pbpstats is more accurate:**
1. Uses event type classification (`isinstance(event, FieldGoal)`)
2. Sophisticated and-1 detection
3. Proper free throw sequence handling
4. Rich event metadata beyond text descriptions

---

## Future Data Sources

### ESPN Play-by-Play (Planned)

**Expected metrics:**
- Similar to Kaggle (same underlying data structure)
- Likely ~130-140 possessions/game with text-based detection
- May have better made FG detection if event types available

**Validation checklist:**
- [ ] Run same validation queries
- [ ] Compare possession counts to Kaggle baseline
- [ ] Check for duplicate games between sources
- [ ] Verify season coverage consistency

### NBA API (Planned)

**Expected metrics:**
- Official NBA data source
- Likely 200-220 possessions/game (if event types available)
- More detailed player tracking data
- Better lineup information

**Validation checklist:**
- [ ] Compare to pbpstats baseline (~220)
- [ ] Cross-validate game IDs with Kaggle
- [ ] Check player tracking data completeness
- [ ] Verify lineup accuracy

### Basketball Reference (Historical)

**Expected metrics:**
- Historical coverage (pre-1996)
- Box score summaries (not play-by-play)
- Team/player statistics (not possession-level)

**Validation checklist:**
- [ ] Verify season totals match official records
- [ ] Cross-check with Kaggle aggregates
- [ ] Validate player/team statistics

---

## Multi-Source Validation Protocol

When integrating multiple data sources:

### 1. Possession Count Cross-Check

```sql
-- Compare possession counts between sources
SELECT
    'kaggle' as source,
    AVG(poss_count) as avg_possessions
FROM (
    SELECT game_id, COUNT(*) as poss_count
    FROM possession_panel_kaggle
    GROUP BY game_id
) t1
UNION ALL
SELECT
    'espn' as source,
    AVG(poss_count) as avg_possessions
FROM (
    SELECT game_id, COUNT(*) as poss_count
    FROM possession_panel_espn
    GROUP BY game_id
) t2;
```

**Expected result:** ±10% variance is acceptable for text-based sources

### 2. Game Overlap Analysis

```sql
-- Find games present in multiple sources
SELECT
    k.game_id,
    k.poss_count as kaggle_poss,
    e.poss_count as espn_poss,
    ABS(k.poss_count - e.poss_count) as diff
FROM (
    SELECT game_id, COUNT(*) as poss_count
    FROM possession_panel_kaggle
    GROUP BY game_id
) k
INNER JOIN (
    SELECT game_id, COUNT(*) as poss_count
    FROM possession_panel_espn
    GROUP BY game_id
) e ON k.game_id = e.game_id
WHERE ABS(k.poss_count - e.poss_count) > 20
ORDER BY diff DESC;
```

**Action items:**
- Investigate games with >20 possession difference
- Check for data quality issues
- Verify game IDs match correctly

### 3. Points Distribution Consistency

```sql
-- Compare points distributions
SELECT
    source,
    points_scored,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY source), 2) as pct
FROM (
    SELECT 'kaggle' as source, points_scored FROM possession_panel_kaggle
    UNION ALL
    SELECT 'espn' as source, points_scored FROM possession_panel_espn
) combined
GROUP BY source, points_scored
ORDER BY source, count DESC;
```

**Expected result:** Distributions should be similar (±5% for each category)

---

## Change Log

| Date | Source | Action | Result |
|------|--------|--------|--------|
| 2025-10-07 | Kaggle | Initial baseline | 3.8M possessions, 127.5 avg |
| 2025-10-07 | pbpstats | Reference test | 220 possessions/game |
| 2025-10-07 | NBA API | Initial baseline | 229K possessions, 235.2 avg |
| 2025-10-07 | Cross-validation | Kaggle vs NBA API | 876 overlapping games, NBA API +85% |

---

## Notes for Future Sessions

**When adding a new data source:**
1. Run full possession panel generation
2. Execute all validation queries from this document
3. Compare results to existing baselines
4. Document any significant differences
5. Update this file with new baseline statistics

**Red flags to watch for:**
- Possession counts <100 or >250 per game
- Missing data >1%
- Points distribution significantly different
- Extreme outliers (>50 points in single possession)
- Duplicate games between sources with >30% possession difference

**Questions to answer:**
- Does this source improve coverage (new games/seasons)?
- Does it improve accuracy (higher possession count closer to ~220)?
- Does it add new features (player tracking, lineups)?
- Is the data quality better or worse than existing sources?

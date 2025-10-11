# Phase 0: Basketball Reference Data Expansion

**Phase:** 0 (Data Collection Enhancement)
**Sub-Phase:** 0.X - Basketball Reference Comprehensive Data Collection
**Status:** ⏸️ PENDING
**Priority:** HIGH (Tier 1), MEDIUM (Tier 2), LOW (Tier 3-4)
**Estimated Time:** 40-60 hours total (spread across tiers)
**Cost Impact:** +$0.10-0.20/month S3 storage
**Dependencies:** Comprehensive scraper already created ✅

---

## Overview

**Purpose:** Expand Basketball Reference data collection from 12 data types to 32 data types, adding ~350,000-10M additional records depending on tier selection.

**Current Status:** We have 12 data types collected (127,000 records):
- ✅ Season Totals, Advanced Totals, Standings, Transactions
- ✅ Draft, Per-Game, Shooting, Play-by-Play, Team Ratings, Playoffs, Coaches, Awards

**This Expansion Adds:** 20 additional data types across 4 tiers

---

## Why This Matters

### For Machine Learning
- **Tier 1:** Era-adjusted metrics, pace-independent stats, schedule context
- **Tier 2:** Lineup chemistry, team trends, efficiency metrics
- **Tier 3:** Legacy tracking, front office effectiveness
- **Tier 4:** Granular player performance for deep analysis

### For Data Quality
- **Cross-validation:** Multiple data sources for same metrics
- **Historical gaps:** Fill pre-2000 data not available from ESPN/hoopR
- **Feature richness:** 400+ features vs current 200+

### For Temporal Analysis
- **Game-by-game:** Complete schedule with attendance, arena, OT
- **Lineup tracking:** Starting combinations and W-L by lineup
- **Progression:** Rookie development, shooting improvement curves

---

## Implementation Tiers

### ✅ Already Collected (Baseline)
- Season Totals, Advanced Totals, Team Standings, Transactions
- Draft, Per-Game, Shooting, Play-by-Play, Team Ratings, Playoffs, Coaches, Awards
- **Total:** 127,000 records across 12 data types

---

## TIER 1 - High Value Data (PRIORITY: IMMEDIATE)

**Estimated Time:** 15-20 hours
**Records Added:** ~150,000
**S3 Storage:** +100 MB
**Why First:** Highest analytical value, easy to scrape, manageable volume

### Sub-Phase 0.1: Adjusted Shooting Stats ⏸️
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_adj_shooting.html`
**Table ID:** `adj_shooting`
**Coverage:** 2000-2025 (26 years)
**Records:** ~19,000 player-seasons

**Data Included:**
- League-adjusted shooting percentages (FG+, 3P+, FT+, TS+)
- True Shooting % (TS%) - accounts for 3-pointers and free throws
- Effective Field Goal % (eFG%) - adjusts for 3-point value
- Comparative metrics vs. league average
- FG Add and TS Add (overall shooting contribution)
- Free throw rate (FTr) and 3-point attempt rate (3PAr)

**Value:**
- Better cross-era comparisons (adjusts for league shooting trends)
- Identifies truly elite shooters vs. volume scorers
- ML feature: Shooting efficiency relative to era
- Quality metric for player valuation

**Implementation Steps:**
1. Add `adj_shooting` to DATA_TYPE_CONFIGS in comprehensive scraper
2. Create `scrape_adj_shooting()` method using generic table parser
3. Test on single season (2024)
4. Run collection for 2000-2025 (26 years)
5. Upload to S3: `basketball_reference/adj_shooting/{season}/adj_shooting_stats.json`

**Estimated Time:** 3-4 hours (1 hour coding, 30 min testing, 2-3 hours runtime)

---

### Sub-Phase 0.2: Per 100 Possessions Stats ⏸️
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_per_poss.html`
**Table ID:** `per_poss`
**Coverage:** 1974-2025 (52 years)
**Records:** ~38,000 player-seasons

**Data Included:**
- All stats normalized per 100 team possessions
- Points, rebounds, assists, etc. per 100 possessions
- Pace-adjusted metrics (controls for game speed)
- Cross-era comparisons (1970s vs. modern era)

**Value:**
- Fairer comparisons across different pace eras
- Controls for team style (fast-break vs. half-court)
- Better evaluation of player impact independent of team pace
- Standard metric for advanced basketball analysis

**Implementation Steps:**
1. Add `per_poss` to DATA_TYPE_CONFIGS
2. Create `scrape_per_poss()` method
3. Test on 2024
4. Run collection for 1974-2025 (52 years)
5. Upload to S3: `basketball_reference/per_poss/{season}/per_poss_stats.json`

**Estimated Time:** 3-4 hours (similar to adjusted shooting)

---

### Sub-Phase 0.3: Game-by-Game Results (Schedule) ⏸️
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_games.html`
**Table ID:** `schedule`
**Coverage:** 1947-2025 (79 years)
**Records:** ~70,000 games

**Data Included:**
- Complete season schedule with outcomes
- Date, teams, scores, OT periods
- Attendance data
- Arena information
- Game duration (LOG column)
- Box score links

**Value:**
- Schedule difficulty analysis
- Home/away splits
- Back-to-back game identification
- Temporal patterns (travel, rest days)
- Attendance trends
- Arena effects

**Implementation Steps:**
1. Add `schedule` to DATA_TYPE_CONFIGS
2. Create `scrape_schedule()` method
3. Handle monthly sub-pages (schedule broken into months)
4. Test on 2024
5. Run collection for 1947-2025 (79 years)
6. Upload to S3: `basketball_reference/schedule/{season}/games.json`

**Estimated Time:** 5-6 hours (2 hours coding for monthly navigation, 1 hour testing, 3-4 hours runtime)

---

### Sub-Phase 0.4: Rookies Stats ⏸️
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_rookies.html`
**Table ID:** `rookies`
**Coverage:** 1947-2025 (79 years)
**Records:** ~6,000 rookie seasons

**Data Included:**
- Filtered view of all rookies for a season
- Debut date tracking
- First-year performance metrics
- Easier rookie identification than filtering per-game stats

**Value:**
- Rookie progression analysis
- Draft class evaluation
- ROY (Rookie of the Year) prediction
- Player development curves
- Cross-validation with draft data

**Implementation Steps:**
1. Add `rookies` to DATA_TYPE_CONFIGS
2. Create `scrape_rookies()` method (same as per-game structure)
3. Test on 2024
4. Run collection for 1947-2025 (79 years)
5. Upload to S3: `basketball_reference/rookies/{season}/rookie_stats.json`

**Estimated Time:** 2-3 hours (simple, uses existing per-game structure)

---

### Sub-Phase 0.5: All-Rookie Teams ⏸️
**URL:** `https://www.basketball-reference.com/awards/all_rookie.html`
**Format:** Single page with all years
**Coverage:** 1962-2025 (64 years)
**Records:** ~640 total (10 players per year × 64 years)

**Data Included:**
- 1st Team and 2nd Team All-Rookie selections (5 players each)
- Historical rookie recognition
- Voting details (when available)

**Value:**
- Quality indicator for rookies
- Historical context for draft success
- Cross-validation with rookie stats
- Career trajectory predictor

**Implementation Steps:**
1. Create specialized scraper (single page, multiple years)
2. Parse table with year sections
3. Extract team designation (1st/2nd)
4. Test extraction
5. Run once (single page)
6. Upload to S3: `basketball_reference/all_rookie_teams/all_years.json`

**Estimated Time:** 2-3 hours (specialized parser needed)

---

**TIER 1 SUMMARY:**
- **Sub-Phases:** 5 (0.1-0.5)
- **Total Time:** 15-20 hours
- **Total Records:** ~150,000
- **Priority:** Execute immediately, highest analytical value

---

## TIER 2 - Strategic Value Data (PRIORITY: NEAR-TERM)

**Estimated Time:** 20-25 hours
**Records Added:** ~200,000
**S3 Storage:** +150 MB
**Why Second:** Team-level insights, moderate complexity, high ML value

### Sub-Phase 0.6: Team Starting Lineups ⏸️
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/{season}_start.html`
**Tables:** Multiple (game-by-game lineups, lineup combinations)
**Coverage:** ~2000-2025 (30 teams × 25 years = 750 team-seasons)
**Records:** ~60,000 lineup records

**Data Included:**
- Game-by-game starting lineups
- Lineup combinations with W-L records
- Most frequently used lineups
- Win percentage by lineup
- Playoff lineups (separate section)

**Value:**
- Lineup optimization analysis
- Chemistry identification
- Rotation pattern tracking
- Lineup effectiveness metrics
- Injury impact on lineups
- Coach decision analysis

**Implementation Steps:**
1. Create team iterator (30 current teams + historical)
2. Add `team_lineups` scraper with team parameter
3. Parse both tables: game-by-game + combinations
4. Test on single team (LAL 2024)
5. Run for all teams, 2000-2025
6. Upload to S3: `basketball_reference/team_lineups/{team}/{season}/lineups.json`

**Estimated Time:** 8-10 hours (complex iteration, multiple tables)

---

### Sub-Phase 0.7: Team Game Logs ⏸️
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/{season}_games.html`
**Tables:** `games` (regular), `games_playoffs` (playoffs)
**Coverage:** All teams, all seasons (30 teams × 79 years)
**Records:** ~195,000 team-game records

**Data Included:**
- Team game-by-game results
- Opponent, score, location
- Four factors (eFG%, TOV%, ORB%, FTr)
- Team and opponent stats per game
- Separate playoff section

**Value:**
- Team performance trends
- Win streak/loss streak analysis
- Schedule strength
- Four factors analysis
- Home/away splits by team

**Implementation Steps:**
1. Create team game log scraper
2. Parse both regular season and playoff tables
3. Test on single team
4. Run for all teams and seasons
5. Upload to S3: `basketball_reference/team_game_logs/{team}/{season}/games.json`

**Estimated Time:** 6-8 hours (team iteration, two tables per team)

---

### Sub-Phase 0.8: Per Minute Stats ⏸️
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_per_minute.html`
**Table ID:** `per_minute`
**Coverage:** 1952-2025 (74 years)
**Records:** ~55,000 player-seasons

**Data Included:**
- Stats per minute played
- Bench player evaluation
- Efficiency independent of playing time

**Value:**
- Bench impact assessment
- Per-minute efficiency rankings
- Rotational player evaluation

**Implementation Steps:**
1. Add `per_minute` to DATA_TYPE_CONFIGS
2. Create `scrape_per_minute()` method
3. Test on 2024
4. Run for 1952-2025 (74 years)
5. Upload to S3: `basketball_reference/per_minute/{season}/per_minute_stats.json`

**Estimated Time:** 3-4 hours (similar to other stat tables)

---

### Sub-Phase 0.9: Season Leaders ⏸️
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_leaders.html`
**Tables:** Multiple (one per stat category)
**Coverage:** 1947-2025 (79 years)
**Records:** ~7,900 (79 years × 10 categories × 10 players)

**Data Included:**
- Top 10 players in each major category
- PPG, RPG, APG, SPG, BPG leaders
- Shooting percentage leaders
- Advanced metric leaders

**Value:**
- Historical dominance tracking
- Statistical milestones
- Award prediction
- Era comparison

**Implementation Steps:**
1. Create season leaders scraper (multiple tables per page)
2. Parse each stat category table
3. Test on 2024
4. Run for 1947-2025
5. Upload to S3: `basketball_reference/season_leaders/{season}/leaders.json`

**Estimated Time:** 3-4 hours (multiple tables, simple structure)

---

**TIER 2 SUMMARY:**
- **Sub-Phases:** 4 (0.6-0.9)
- **Total Time:** 20-25 hours
- **Total Records:** ~200,000
- **Priority:** Execute after Tier 1, high strategic value

---

## TIER 3 - Specialized Data (PRIORITY: LONG-TERM)

**Estimated Time:** 5-7 hours
**Records Added:** ~5,000
**S3 Storage:** +10 MB
**Why Third:** Lower volume, specialized use cases

### Sub-Phase 0.10: Hall of Fame Inductees ⏸️
**URL:** `https://www.basketball-reference.com/awards/hof.html`
**Table ID:** `hof`
**Coverage:** Complete HOF history (~400 inductees)
**Records:** ~400

**Implementation:** 2 hours (single page, simple table)

---

### Sub-Phase 0.11: Executive Stats ⏸️
**URL:** `https://www.basketball-reference.com/executives/NBA_stats.html`
**Coverage:** All GMs/Presidents
**Records:** ~500-1,000

**Implementation:** 2-3 hours

---

### Sub-Phase 0.12: Team Referee Stats ⏸️
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/{season}_referees.html`
**Coverage:** Recent years (availability TBD)
**Records:** Variable

**Implementation:** 2-3 hours

---

### Sub-Phase 0.13: Jersey Numbers ⏸️
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_numbers.html`
**Coverage:** Recent years
**Records:** ~2,000-3,000

**Implementation:** 2 hours

---

**TIER 3 SUMMARY:**
- **Sub-Phases:** 4 (0.10-0.13)
- **Total Time:** 5-7 hours
- **Total Records:** ~5,000
- **Priority:** Execute if time permits, specialized value

---

## TIER 4 - Player Granularity (PRIORITY: OPTIONAL/FUTURE)

**Estimated Time:** 50-100 hours (highly variable)
**Records Added:** 5-10 MILLION
**S3 Storage:** +5-10 GB
**Why Last:** Extreme volume, selective collection recommended

### Sub-Phase 0.14: Player Game Logs ⏸️
**URL:** `https://www.basketball-reference.com/players/{X}/{player_slug}/gamelog/{season}`
**Coverage:** ALL players, ALL games (career-long)
**Records:** ~5 million+ individual games

**Recommendation:** Selective collection
- Top 500 players only (HOF, All-Stars, current stars)
- Recent era only (2000-2025)
- Estimated: 500 players × 1,000 games avg = 500,000 records

**Implementation:** 20-40 hours (requires player iteration)

---

### Sub-Phase 0.15: Player Career Splits ⏸️
**URL:** `https://www.basketball-reference.com/players/{X}/{player_slug}/splits/`
**Coverage:** ALL players (career splits)
**Records:** ~5,000 players × multiple split categories

**Recommendation:** Selective collection
- Top 500 players only
- Focus on most impactful splits (home/away, clutch, opponent strength)

**Implementation:** 30-60 hours (requires player iteration, complex table structure)

---

**TIER 4 SUMMARY:**
- **Sub-Phases:** 2 (0.14-0.15)
- **Total Time:** 50-100 hours (if selective collection)
- **Total Records:** 500,000-10M (depending on selection)
- **Priority:** Evaluate necessity before implementing

---

## Complete Implementation Plan

### Phase Schedule

**Week 1-2: Tier 1 (HIGH PRIORITY)**
- Day 1-2: Sub-Phase 0.1 - Adjusted Shooting (3-4 hours)
- Day 3-4: Sub-Phase 0.2 - Per 100 Possessions (3-4 hours)
- Day 5-7: Sub-Phase 0.3 - Game Results/Schedule (5-6 hours)
- Day 8: Sub-Phase 0.4 - Rookies Stats (2-3 hours)
- Day 9: Sub-Phase 0.5 - All-Rookie Teams (2-3 hours)
- **Total: 15-20 hours, ~150,000 records**

**Week 3-4: Tier 2 (MEDIUM PRIORITY)**
- Day 10-12: Sub-Phase 0.6 - Team Starting Lineups (8-10 hours)
- Day 13-14: Sub-Phase 0.7 - Team Game Logs (6-8 hours)
- Day 15: Sub-Phase 0.8 - Per Minute Stats (3-4 hours)
- Day 16: Sub-Phase 0.9 - Season Leaders (3-4 hours)
- **Total: 20-25 hours, ~200,000 records**

**Week 5: Tier 3 (LOW PRIORITY) - Optional**
- Day 17: Sub-Phases 0.10-0.13 (5-7 hours total)
- **Total: 5-7 hours, ~5,000 records**

**Future: Tier 4 (OPTIONAL) - Evaluate First**
- Sub-Phases 0.14-0.15 (50-100 hours if selective)
- **Decision point:** Assess ML model needs before implementing

---

### Execution Workflow

**For Each Sub-Phase:**

1. **Preparation** (15 min)
   - Read sub-phase description
   - Verify URL and table ID
   - Check current scraper capabilities

2. **Implementation** (varies)
   - Add data type to `DATA_TYPE_CONFIGS` in comprehensive scraper
   - Create/modify scraper method
   - Add any specialized parsing logic

3. **Testing** (30-60 min)
   - Test on single season (usually 2024)
   - Verify data structure
   - Check record counts
   - Validate S3 upload

4. **Collection** (varies)
   - Run for specified year range
   - Monitor progress
   - Verify completion

5. **Validation** (15-30 min)
   - Check S3 for all expected files
   - Verify record counts match expectations
   - Sample data quality checks

6. **Documentation** (15 min)
   - Update PROGRESS.md status
   - Mark sub-phase complete
   - Note any issues/deviations

---

## Technical Implementation Details

### Extending Comprehensive Scraper

**File:** `scripts/etl/scrape_basketball_reference_comprehensive.py`

**Add to DATA_TYPE_CONFIGS:**
```python
DATA_TYPE_CONFIGS = {
    # ... existing configs ...

    # TIER 1
    'adj_shooting': {
        'url_pattern': '/leagues/NBA_{season}_adj_shooting.html',
        'min_year': 2000,
        's3_prefix': 'basketball_reference/adj_shooting',
        'filename': 'adj_shooting_stats.json'
    },
    'per_poss': {
        'url_pattern': '/leagues/NBA_{season}_per_poss.html',
        'min_year': 1974,
        's3_prefix': 'basketball_reference/per_poss',
        'filename': 'per_poss_stats.json'
    },
    # ... add remaining configs
}
```

**Add Scraper Methods:**
```python
def scrape_adj_shooting(self, season: int) -> Optional[Dict]:
    """Scrape adjusted shooting stats for a season"""
    url = f"{self.BASE_URL}/leagues/NBA_{season}_adj_shooting.html"
    html = self._make_request_with_retry(url)

    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')
    players = self._parse_table_generic(soup, 'adj_shooting')

    self.stats['adj_shooting']['records'] += len(players)

    return {
        'season': season,
        'players': players
    }

# Add similar methods for other data types
```

---

### Team-Level Data Collection

**For team-specific URLs (lineups, game logs, referee stats):**

```python
def scrape_team_lineups(self, team: str, season: int) -> Optional[Dict]:
    """Scrape team starting lineups for a season"""
    url = f"{self.BASE_URL}/teams/{team}/{season}_start.html"
    html = self._make_request_with_retry(url)

    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')

    # Parse game-by-game lineups
    game_lineups = self._parse_table_generic(soup, 'starting_lineups')

    # Parse lineup combinations
    lineup_combos = self._parse_table_generic(soup, 'lineup_combos')

    return {
        'team': team,
        'season': season,
        'game_lineups': game_lineups,
        'combinations': lineup_combos
    }

# Wrapper to iterate all teams
def scrape_all_team_lineups(self, season: int) -> List[Dict]:
    """Scrape lineups for all teams in a season"""
    teams = self._get_teams_for_season(season)
    all_data = []

    for team in teams:
        data = self.scrape_team_lineups(team, season)
        if data:
            all_data.append(data)
        time.sleep(self.rate_limit)  # Rate limiting

    return all_data
```

---

### Schedule/Game Results (Monthly Navigation)

**Handle monthly sub-pages:**

```python
def scrape_schedule(self, season: int) -> Optional[Dict]:
    """Scrape complete season schedule (handles monthly pages)"""
    all_games = []

    # Basketball Reference breaks schedule into months
    months = self._get_schedule_months(season)

    for month in months:
        month_url = f"{self.BASE_URL}/leagues/NBA_{season}_games-{month}.html"
        html = self._make_request_with_retry(month_url)

        if html:
            soup = BeautifulSoup(html, 'lxml')
            games = self._parse_table_generic(soup, 'schedule')
            all_games.extend(games)

        time.sleep(self.rate_limit)

    return {
        'season': season,
        'games': all_games
    }

def _get_schedule_months(self, season: int) -> List[str]:
    """Get list of months for a season's schedule"""
    # NBA season typically runs October-June
    return ['october', 'november', 'december', 'january',
            'february', 'march', 'april', 'may', 'june']
```

---

## Testing Strategy

### Single Season Test (2024)

```bash
# Test Tier 1 data types on 2024
python scripts/etl/scrape_basketball_reference_comprehensive.py \
    --season 2024 \
    --adj-shooting --per-poss --schedule --rookies \
    --upload-to-s3

# Expected output:
# - adj_shooting: ~736 records
# - per_poss: ~736 records
# - schedule: ~1,230 games
# - rookies: ~60 records
```

### Full Collection Test (Single Data Type)

```bash
# Test one data type across all years
python scripts/etl/scrape_basketball_reference_comprehensive.py \
    --start-season 2000 \
    --end-season 2025 \
    --adj-shooting \
    --upload-to-s3

# Expected: 26 years × ~700 records/year = ~18,200 records
```

---

## Data Quality Checks

**For each data type collected:**

1. **Record count validation**
   ```bash
   # Check S3 files exist
   aws s3 ls s3://nba-sim-raw-data-lake/basketball_reference/adj_shooting/ --recursive

   # Should see files for each year in coverage range
   ```

2. **Data structure validation**
   ```bash
   # Download and inspect a sample
   aws s3 cp s3://nba-sim-raw-data-lake/basketball_reference/adj_shooting/2024/adj_shooting_stats.json /tmp/

   # Check JSON structure
   cat /tmp/adj_shooting_stats.json | python -m json.tool | head -50
   ```

3. **Record count spot-check**
   ```python
   # Count records in a season
   import json

   with open('/tmp/adj_shooting_stats.json') as f:
       data = json.load(f)
       print(f"Season: {data['season']}")
       print(f"Records: {len(data['players'])}")
       # Expected: 700-750 for modern seasons
   ```

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/
├── adj_shooting/
│   ├── 2000/adj_shooting_stats.json
│   ├── 2001/adj_shooting_stats.json
│   └── .../2025/adj_shooting_stats.json
├── per_poss/
│   ├── 1974/per_poss_stats.json
│   └── .../2025/per_poss_stats.json
├── schedule/
│   ├── 1947/games.json
│   └── .../2025/games.json
├── rookies/
│   ├── 1947/rookie_stats.json
│   └── .../2025/rookie_stats.json
├── all_rookie_teams/
│   └── all_years.json
├── team_lineups/
│   ├── LAL/
│   │   ├── 2000/lineups.json
│   │   └── .../2025/lineups.json
│   └── .../[other teams]/
├── team_game_logs/
│   ├── LAL/
│   │   ├── 1947/games.json
│   │   └── .../2025/games.json
│   └── .../[other teams]/
└── [other data types]/
```

---

## Cost Management

### S3 Storage Costs

| Tier | Data Volume | Monthly Cost |
|------|-------------|--------------|
| Tier 1 | ~100 MB | $0.0023 |
| Tier 2 | ~150 MB | $0.0035 |
| Tier 3 | ~10 MB | $0.0002 |
| Tier 4 | ~5-10 GB | $0.12-0.23 |
| **Total (1-3)** | **~260 MB** | **$0.006** |

**Conclusion:** Negligible cost increase (<$0.01/month for Tiers 1-3)

---

## Success Criteria

### Tier 1 Complete ✅
- [ ] Adjusted Shooting: 26 years, ~19,000 records
- [ ] Per 100 Possessions: 52 years, ~38,000 records
- [ ] Schedule: 79 years, ~70,000 games
- [ ] Rookies: 79 years, ~6,000 records
- [ ] All-Rookie Teams: 64 years, ~640 records
- [ ] **Total: ~150,000 records added**

### Tier 2 Complete ✅
- [ ] Team Lineups: 750 team-seasons, ~60,000 records
- [ ] Team Game Logs: 2,400 team-seasons, ~195,000 records
- [ ] Per Minute: 74 years, ~55,000 records
- [ ] Season Leaders: 79 years, ~7,900 records
- [ ] **Total: ~200,000 additional records**

### Tier 3 Complete ✅
- [ ] Hall of Fame: ~400 records
- [ ] Executives: ~500-1,000 records
- [ ] Team Referee Stats: Variable
- [ ] Jersey Numbers: ~2,000-3,000 records
- [ ] **Total: ~5,000 additional records**

---

## Integration with Existing System

### Update DATA_CATALOG.md
After each tier completion:
```bash
python scripts/utils/update_data_catalog.py
```

### Database Integration
Create tables for new data types:
```sql
CREATE TABLE basketball_reference_adj_shooting (
    season INTEGER,
    player_slug TEXT,
    -- ... columns from JSON
);

-- Similar for other data types
```

### ML Feature Engineering
New features available:
- **From Adjusted Shooting:** TS+, eFG+, era_adjusted_fg_pct
- **From Per 100 Poss:** pace_adjusted_ppg, pace_adjusted_ast
- **From Schedule:** schedule_strength, rest_days, travel_distance
- **From Lineups:** lineup_chemistry, lineup_win_pct

---

## Troubleshooting

### Common Issues

**Issue:** Table ID not found
- **Solution:** Use `curl` to verify actual table ID on page
```bash
curl -s "https://www.basketball-reference.com/leagues/NBA_2024_adj_shooting.html" | grep '<table[^>]*id='
```

**Issue:** Monthly schedule pages don't exist for early years
- **Solution:** Handle 404 gracefully, skip missing months

**Issue:** Team abbreviations change over time
- **Solution:** Maintain historical team mapping dictionary

**Issue:** Rate limiting (HTTP 429)
- **Solution:** Already handled with 12s rate limit + exponential backoff

---

## Next Steps After Completion

**Phase 1 Integration:**
1. Load all new data into database tables
2. Create unified views across data sources
3. Update ML feature engineering pipeline
4. Run cross-validation checks

**Phase 4 Enhancement:**
1. Use schedule data for schedule strength analysis
2. Use lineup data for chemistry modeling
3. Use adjusted stats for era-normalized predictions

**Phase 5 ML:**
1. Add 100+ new features from expanded data
2. Retrain models with richer feature set
3. Improve prediction accuracy

---

## Documentation Updates Required

After each tier completion:
- [ ] Update `docs/DATA_CATALOG.md`
- [ ] Update `docs/DATA_SOURCE_BASELINES.md`
- [ ] Update this phase file (mark ✅)
- [ ] Update `PROGRESS.md` Current Session Context
- [ ] Create completion summary report

---

## Workflow References

- **Workflow #1:** Session Start Protocol
- **Workflow #2:** Command Logging (log all scraper runs)
- **Workflow #5:** Git Commit (commit after each tier)
- **Workflow #6:** Git Push (push after testing)
- **Workflow #14:** Session End Protocol

---

## Related Documentation

- **Data Source Analysis:** `docs/data_sources/basketball_reference_additional_sources_2025-10-10.md`
- **Comprehensive Scraper:** `scripts/etl/scrape_basketball_reference_comprehensive.py`
- **Scraper Summary:** `docs/data_sources/basketball_reference_comprehensive_scraper_summary.md`
- **ESPN Schema Fix:** `docs/fixes/espn_scraper_schema_fix_2025-10-10.md`

---

**Phase Owner:** Data Collection Team
**Last Updated:** October 10, 2025
**Status:** Ready to execute - Tier 1 recommended as immediate next step

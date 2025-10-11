# Basketball Reference - Additional Data Sources (Extended Analysis)

**Date:** October 10, 2025
**Purpose:** Comprehensive identification of ALL additional valuable data sources beyond current collection
**Status:** Investigation Complete

---

## Already Collected ✅

1. **Season Totals** - Basic counting stats (75 years, 1947-2025)
2. **Advanced Totals** - Advanced metrics (PER, WS, BPM, VORP) (67 years, 1953-2025)
3. **Team Standings** - Win/loss records (29 years, 1971-2025)
4. **Transactions** - Trades, signings, waivers (25 years, 2001-2025)
5. **Draft Data** - Pick position, college, career stats (25 years, 2001-2025)
6. **Per-Game Stats** - Normalized by games played (25 years, 2001-2025)
7. **Shooting Stats** - Shot location and distribution (25 years, 2001-2025)
8. **Play-by-Play** - On/off court, positional data (25 years, 2001-2025)
9. **Team Ratings** - Offensive/defensive efficiency (25 years, 2001-2025)
10. **Playoff Stats** - Postseason performance (25 years, 2001-2025)
11. **Coach Records** - Coaching records (25 years, 2001-2025)
12. **Awards** - MVP, All-NBA, All-Star, etc. (tested 2024, ready for full collection)

---

## NEW High-Priority Additions 🎯

### 1. **Adjusted Shooting Stats** (2000-present)
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_adj_shooting.html`
**Table ID:** `adj_shooting`

**Value:**
- League-adjusted shooting percentages (FG+, 3P+, FT+, TS+)
- True Shooting % (TS%) - accounts for 3-pointers and free throws
- Effective Field Goal % (eFG%) - adjusts for 3-point value
- Comparative metrics vs. league average
- FG Add and TS Add (overall shooting contribution)
- Free throw rate (FTr) and 3-point attempt rate (3PAr)

**Why Important:**
- Better cross-era comparisons (adjusts for league shooting trends)
- Identifies truly elite shooters vs. volume scorers
- ML feature: Shooting efficiency relative to era
- Quality metric for player valuation

**Coverage:** 2000-2025 (26 years)

**Use Cases:**
- Era-adjusted player rankings
- Shooting efficiency models
- Player development tracking
- Contract value analysis

---

### 2. **Per 100 Possessions Stats** (1974-present)
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_per_poss.html`
**Table ID:** `per_poss`

**Value:**
- Pace-adjusted stats (controls for game speed)
- Cross-era comparisons (1970s vs. modern era)
- All stats normalized per 100 team possessions
- Points, rebounds, assists, etc. per 100 possessions

**Why Important:**
- Fairer comparisons across different pace eras
- Controls for team style (fast-break vs. half-court)
- Better evaluation of player impact independent of team pace
- Standard metric for advanced basketball analysis

**Coverage:** 1974-2025 (52 years)

**Use Cases:**
- Cross-era player comparisons
- Pace-independent efficiency metrics
- Team style analysis
- ML features for tempo-adjusted stats

---

### 3. **Game-by-Game Results** (1947-present)
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_games.html`
**Table ID:** `schedule`

**Value:**
- Complete season schedule with outcomes
- Date, teams, scores, OT periods
- Attendance data
- Arena information
- Game duration (LOG)
- Box score links

**Why Important:**
- Schedule difficulty analysis
- Home/away splits
- Back-to-back game identification
- Temporal patterns (travel, rest days)
- Attendance trends
- Arena effects

**Coverage:** 1947-2025 (79 years, ~70,000 games)

**Use Cases:**
- Schedule strength calculations
- Fatigue modeling (back-to-backs, long road trips)
- Home court advantage quantification
- Attendance pattern analysis
- Game outcome prediction

---

### 4. **Rookies Stats** (1947-present)
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_rookies.html`
**Table ID:** `rookies`

**Value:**
- Filtered view of all rookies for a season
- Debut date tracking
- First-year performance metrics
- Easier rookie identification than filtering per-game stats

**Why Important:**
- Rookie progression analysis
- Draft class evaluation
- ROY (Rookie of the Year) prediction
- Player development curves
- Cross-validation with draft data

**Coverage:** 1947-2025 (79 years)

**Use Cases:**
- Rookie performance vs. draft position
- First-year impact identification
- Development trajectory modeling
- Draft class strength evaluation

---

### 5. **All-Rookie Teams** (1962-present)
**URL:** `https://www.basketball-reference.com/awards/all_rookie.html`
**Table IDs:** Multiple (one per year)

**Value:**
- 1st Team and 2nd Team All-Rookie selections
- Historical rookie recognition
- 5 players per team, per year
- Voting details (when available)

**Why Important:**
- Quality indicator for rookies
- Historical context for draft success
- Cross-validation with rookie stats
- Career trajectory predictor

**Coverage:** 1962-2025 (64 years)

**Use Cases:**
- Rookie accolades tracking
- Draft success validation
- Career outcome prediction
- Historical player ranking

---

### 6. **Injury Reports** (Current season only)
**URL:** `https://www.basketball-reference.com/friv/injuries.fcgi`
**Format:** Dynamic page (current injuries only)

**Value:**
- Player name, team, injury description
- Update date
- Specific body parts injured
- Expected recovery timelines

**Why Important:**
- Explains player absences
- Data quality validation (missing games)
- Injury proneness tracking
- Load management patterns

**Coverage:** Current season (rolling ~30 days)

**Limitations:**
- Historical injury data NOT available on this page
- Would need to scrape daily and archive
- Already captured in transactions for some injuries

**Use Cases:**
- Real-time roster availability
- Injury pattern analysis (if archived)
- Game availability prediction
- Player health tracking

---

## NEW Medium-Priority Additions 📊

### 7. **Per Minute Stats** (1952-present)
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_per_minute.html`
**Table ID:** `per_minute`

**Value:**
- Stats per minute played
- Bench player evaluation
- Efficiency independent of playing time

**Coverage:** 1952-2025 (74 years)

**Use Cases:**
- Bench impact assessment
- Per-minute efficiency rankings
- Rotational player evaluation

---

### 8. **Season Leaders** (1947-present)
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_leaders.html`
**Table IDs:** Multiple (one per stat category)

**Value:**
- Top 10 players in each major category
- PPG, RPG, APG, SPG, BPG leaders
- Shooting percentage leaders
- Advanced metric leaders

**Coverage:** 1947-2025 (79 years)

**Use Cases:**
- Historical dominance tracking
- Statistical milestones
- Award prediction
- Era comparison

---

### 9. **Jersey Numbers** (Recent years)
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_numbers.html`
**Table ID:** `numbers`

**Value:**
- Jersey number assignments by team
- Number retirement tracking
- Player identifier

**Coverage:** Recent years (TBD)

**Use Cases:**
- Player identification
- Number retirement analysis
- Historical jersey tracking

---

## NEW Team-Specific Data 🏀

### 10. **Team Starting Lineups** (2000-present)
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/{season}_start.html`
**Table IDs:** Multiple (lineups, combinations)

**Value:**
- Game-by-game starting lineups
- Lineup combinations with W-L records
- Most frequently used lineups
- Win percentage by lineup

**Why Important:**
- Lineup optimization analysis
- Chemistry identification
- Rotation pattern tracking
- Lineup effectiveness metrics

**Coverage:** ~2000-2025 (30 teams × 25 years = 750 team-seasons)

**Use Cases:**
- Lineup synergy modeling
- Optimal lineup identification
- Injury impact on lineups
- Coach decision analysis

---

### 11. **Team Game Logs** (1947-present)
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/{season}_games.html`
**Table IDs:** `games`, `games_playoffs`

**Value:**
- Team game-by-game results
- Opponent, score, location
- Four factors (eFG%, TOV%, ORB%, FTr)
- Team and opponent stats per game

**Coverage:** All teams, all seasons (30 teams × 79 years)

**Use Cases:**
- Team performance trends
- Win streak/loss streak analysis
- Schedule strength
- Four factors analysis

---

### 12. **Team Referee Stats** (Recent years)
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/{season}_referees.html`
**Table ID:** `referees`

**Value:**
- Performance by referee crew
- W-L record by referee
- Per-48-minute stats with each referee
- Fouls called, pace of play

**Coverage:** Recent years (availability TBD)

**Use Cases:**
- Referee bias analysis
- Home court advantage factors
- Foul rate patterns
- Pace impact by officiating crew

---

### 13. **Team Transactions** (2001-present)
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/{season}_transactions.html`
**Table:** Transaction list

**Value:**
- Team-specific transactions only
- Filtered view of league transactions
- Team roster changes

**Coverage:** 2001-2025 (30 teams × 25 years)

**Note:** We already have league-wide transactions, this is just a filtered view

---

### 14. **Team Depth Charts** (Recent years)
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/{season}_depth.html`
**Format:** Positional depth chart

**Value:**
- Positional depth by team
- Starter vs. backup designation
- Roster organization

**Coverage:** Recent years (availability TBD)

**Use Cases:**
- Roster construction analysis
- Positional depth evaluation
- Backup quality assessment

---

## NEW Player-Specific Data 👤

### 15. **Player Game Logs** (Career-long)
**URL:** `https://www.basketball-reference.com/players/{X}/{player_slug}/gamelog/{season}`
**Table IDs:** `pgl_basic`, `pgl_advanced`

**Value:**
- Every game a player has played
- Full box score stats per game
- Game Score (GmSc)
- Plus/Minus (+/-)
- Home/away designation
- Result (W/L)

**Why Important:**
- Granular performance tracking
- Streak analysis (hot/cold periods)
- Opponent matchup analysis
- Consistency metrics

**Coverage:** All active and historical players (career-long)

**Challenges:**
- Millions of individual games
- Would need to scrape player-by-player
- Very large dataset

**Use Cases:**
- Player consistency analysis
- Clutch performance identification
- Matchup-specific stats
- Injury impact evaluation

---

### 16. **Player Career Splits** (Career-long)
**URL:** `https://www.basketball-reference.com/players/{X}/{player_slug}/splits/`
**Table IDs:** Multiple (career splits table)

**Value:**
- Home/away splits
- Month-by-month performance
- Day of week splits
- Pre/Post All-Star break
- Clutch stats (close games)
- Opponent strength splits

**Why Important:**
- Situational performance patterns
- Clutch ability identification
- Travel/rest impacts
- Matchup tendencies

**Coverage:** All active and historical players

**Use Cases:**
- Clutch performance metrics
- Home court advantage per player
- Schedule fatigue analysis
- Opponent difficulty adjustments

---

## Lower-Priority / Specialized 📑

### 17. **Hall of Fame Inductees**
**URL:** `https://www.basketball-reference.com/awards/hof.html`
**Table ID:** `hof`

**Value:**
- HOF induction year
- Player name and career summary
- Historical importance indicator

**Coverage:** Complete HOF history

**Use Cases:**
- Legacy metrics
- Career achievement tracking
- GOAT debates

---

### 18. **Executive Stats**
**URL:** `https://www.basketball-reference.com/executives/NBA_stats.html`
**Table:** Executive records

**Value:**
- GM/President records
- Years with teams
- Playoff appearances
- Championships

**Coverage:** TBD

**Use Cases:**
- Front office effectiveness
- Team-building success
- Organizational stability

---

### 19. **Preseason Odds**
**URL:** `https://www.basketball-reference.com/leagues/NBA_{season}_preseason_odds.html`
**Format:** Betting odds

**Value:**
- Championship odds
- Division/conference odds
- Over/under win totals
- Market expectations

**Coverage:** Recent years

**Use Cases:**
- Prediction baseline
- Market sentiment analysis
- Expectations vs. results

---

### 20. **Individual Team Seasons** (Franchise history)
**URL:** `https://www.basketball-reference.com/teams/{TEAM}/`
**Format:** Franchise history table

**Value:**
- Year-by-year team records
- Playoff results
- Attendance
- Coaching changes

**Coverage:** All franchises, all years

**Use Cases:**
- Franchise trajectory analysis
- Rebuild success tracking
- Historical team performance

---

## Data Density Comparison

### Extremely High Volume (Player-level granularity)
- Player Game Logs: ~5 million+ individual games (all players × all games)
- Player Splits: ~5,000 players × multiple split categories

### High Volume (Season × League)
- Game-by-Game Results: ~70,000 games (79 years × ~900 games/year)
- Adjusted Shooting: ~60,000 player-seasons
- Per 100 Possessions: ~65,000 player-seasons

### Medium Volume (Team-level)
- Team Starting Lineups: ~750 team-seasons × ~82 games = 61,500 lineup records
- Team Game Logs: ~2,400 team-seasons × 82 games = 196,800 records
- Team Referee Stats: TBD

### Low Volume (Awards/Recognition)
- All-Rookie Teams: ~64 years × 10 players = 640 records
- Season Leaders: ~79 years × 10 categories × 10 players = 7,900 records
- Hall of Fame: ~400 inductees

---

## Recommended Implementation Priority

### Phase 1 - High Value, Manageable Volume (Immediate)
1. **Adjusted Shooting** - Better shooting metrics (26 years)
2. **Per 100 Possessions** - Pace-adjusted stats (52 years)
3. **Game Results (Schedule)** - Schedule context (79 years, ~70,000 games)
4. **Rookies** - First-year tracking (79 years)
5. **All-Rookie Teams** - Rookie recognition (64 years)

**Estimated:** ~150,000 additional records

---

### Phase 2 - Team-Level Insights (Near-term)
6. **Team Starting Lineups** - Lineup combinations (750 team-seasons)
7. **Team Game Logs** - Team performance trends (2,400 team-seasons)
8. **Per Minute Stats** - Efficiency metrics (74 years)
9. **Season Leaders** - Top performers (79 years)

**Estimated:** ~200,000 additional records

---

### Phase 3 - Specialized/Historical (Long-term)
10. **Hall of Fame** - Legacy tracking (~400 records)
11. **Executive Stats** - Front office effectiveness (TBD)
12. **Team Referee Stats** - Officiating impact (TBD)
13. **Jersey Numbers** - Player identification (TBD)

**Estimated:** ~5,000 additional records

---

### Phase 4 - Player Granularity (Future/Optional)
14. **Player Game Logs** - Game-by-game performance (5M+ games)
15. **Player Splits** - Situational stats (~5,000 players)

**Estimated:** 5-10 million records
**Note:** Extremely high volume, consider selective collection or aggregation

---

## Storage Impact

**Current Basketball Reference:** ~127,000 records

**Phase 1 Additional:** ~150,000 records (118% increase)
**Phase 2 Additional:** ~200,000 records (157% increase)
**Phase 3 Additional:** ~5,000 records (4% increase)
**Phase 4 Additional:** 5-10M records (3,900-7,800% increase)

**Total Estimated (Phases 1-3):** ~482,000 records (279% increase)
**Total with Player Granularity:** 5-10M records

**S3 Storage:**
- Phases 1-3: ~300 MB additional (current is ~662 MB → 962 MB total)
- Phase 4: ~5-10 GB (player-level granularity)

**Still very manageable for S3 ($0.023/GB/month)**

---

## Technical Considerations

### Scraping Complexity

**Easy (Standard table scraping):**
- Adjusted Shooting ✅
- Per 100 Possessions ✅
- Game Results ✅
- Rookies ✅
- Per Minute ✅
- Season Leaders ✅

**Medium (Multiple tables per page):**
- Team Starting Lineups (2 tables)
- Team Game Logs (2 tables: regular + playoffs)
- All-Rookie Teams (multiple years per page)

**Complex (Per-player iteration):**
- Player Game Logs (need player list × seasons)
- Player Splits (need player list)

**Dynamic/Limited:**
- Injury Reports (current only, would need daily archiving)
- Preseason Odds (limited historical data)

---

## Highest Value Additions

**For ML/Analytics:**
1. **Adjusted Shooting** - Era-adjusted efficiency
2. **Per 100 Possessions** - Pace-independent metrics
3. **Game Results** - Schedule/opponent context
4. **Team Starting Lineups** - Lineup synergy

**For Data Quality:**
1. **Rookies** - Cross-validation with draft data
2. **All-Rookie Teams** - Quality indicators
3. **Game Results** - Temporal validation

**For Advanced Analysis:**
1. **Player Game Logs** - Granular performance (if volume acceptable)
2. **Player Splits** - Situational tendencies
3. **Team Game Logs** - Team trends

---

## Next Steps

### Immediate (This Session)
1. ✅ Comprehensive investigation complete
2. ⏸️ Decide which Phase 1 data types to prioritize
3. ⏸️ Extend comprehensive scraper to include new data types

### Short-term
4. Implement Phase 1 data types (adjusted shooting, per 100, games, rookies)
5. Test on single season (2024)
6. Run full collection for modern era (2001-2025)

### Long-term
7. Extend to Phase 2 (team-level insights)
8. Evaluate Phase 4 (player granularity) necessity
9. Implement selective player collection (only top players)

---

## Conclusion

Basketball Reference contains significantly more data than initially documented. The most valuable additions are:

**Tier 1 (Immediate Value):**
- Adjusted Shooting (shooting efficiency)
- Per 100 Possessions (pace-adjusted)
- Game Results (schedule context)
- Rookies (first-year tracking)
- All-Rookie Teams (quality indicators)

**Tier 2 (Strategic Value):**
- Team Starting Lineups (chemistry)
- Team Game Logs (trends)
- Per Minute Stats (efficiency)
- Season Leaders (dominance tracking)

**Tier 3 (Deep Analysis):**
- Player Game Logs (granular, very high volume)
- Player Splits (situational, very high volume)

**Total Potential:** 5-10M additional records if including player-level granularity, or ~350,000 records for Phases 1-3 (more manageable).

**Recommendation:** Focus on Phases 1-2 first (350,000 records, high value, manageable volume), then evaluate Phase 4 based on ML model needs.

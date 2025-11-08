# hoopR and Basketball Reference Data Collection Investigation
## COMPLETE SCOPE ANALYSIS

**Investigation Date:** November 7, 2025
**Status:** Complete - Comprehensive Data Revealed
**Key Finding:** You had 152 hoopR endpoints documented. Much more data available than current incremental scrapers collect.

---

## EXECUTIVE SUMMARY

### What You Had Configured:
1. **hoopR:** 152 NBA Stats API endpoints (documented and ready to scrape)
2. **Basketball Reference:** 234+ data types across 13 tiers (comprehensive catalog complete)
3. **Comprehensive Scrapers:** Multiple production-ready implementations for both sources
4. **Missing Gap:** Both sources are now using INCREMENTAL-ONLY scrapers (much less data)

### Current Status:
- **hoopR:** Only incremental scraper active (`hoopr_incremental_simple.py`)
- **Basketball Reference:** Only incremental scraper active
- **Lost Capability:** 152 hoopR endpoints and 234+ Basketball Reference data types no longer being actively collected
- **Data in S3:** Substantial historical Basketball Reference data (2001-2025 across 8 data types), but hoopR endpoints haven't been comprehensively scraped

---

## HOOPR DETAILED INVESTIGATION

### 152 Endpoints Discovered (October 7, 2025)

**Documentation Found:**
- `/Users/ryanranft/nba-simulator-aws/docs/HOOPR_152_ENDPOINTS_GUIDE.md` (844 lines)
- `/Users/ryanranft/nba-simulator-aws/docs/HOOPR_152_QUICK_REFERENCE.md` (345 lines)
- `/Users/ryanranft/nba-simulator-aws/docs/HOOPR_SCHEMA_MAPPING.md`

**4 Categories of Endpoints:**

#### Phase 1: Bulk Data Loaders (4 endpoints)
Most efficient, save per-season:
- `load_nba_pbp` - Play-by-play events
- `load_nba_player_box` - Player box scores  
- `load_nba_team_box` - Team box scores
- `load_nba_schedule` - Game schedules

Output: 96 files (4 × 24 seasons)
Runtime: ~4 minutes

#### Phase 2: Static/Reference Data (25 endpoints)
One-time scrapes:
- All-time leaders (`nba_alltimeleadersgrids`)
- Player index (`nba_commonallplayers`, `nba_playerindex`)
- Team info (`nba_teams`, `nba_franchisehistory`)
- Draft data (`nba_drafthistory`, `nba_draftcombine*`)
- Playoff series (`nba_commonplayoffseries`)
- Scoreboards (v1, v2, v3)
- Defense hub, Leaders, Franchise leaders

Output: ~50 files
Runtime: ~2 minutes

#### Phase 3: Per-Season Dashboards (40 endpoints)
League-wide statistics:
- League player stats (`nba_leaguedashplayerstats`)
- League team stats (`nba_leaguedashteamstats`)
- Player bio stats (`nba_leaguedashplayerbiostats`)
- Clutch stats (player & team)
- Shot locations (player & team)
- Player tracking shots (2013+)
- Lineups (`nba_leaguedashlineups`)
- Standings (`nba_leaguestandingsv3`)
- Hustle stats leaders, Tracking stats leaders
- Defense dashboards

Output: ~960 files (40 × 24 seasons)
Runtime: ~40 minutes

#### Phase 4: Per-Game Boxscores (87 endpoints)
Detailed game analysis:
- Traditional boxscores (v2 & v3)
- Advanced boxscores (v2 & v3)
- Scoring, Usage, Four factors, Misc, Tracking, Hustle, Matchups, Defensive boxscores
- Shot charts (`nba_shotchartdetail`, etc.)
- Synergy play types (`nba_synergyplaytypes`)
- Game rotation, Assist tracker
- Player dashboards (clutch, shooting, splits, opponent, etc.)
- Team dashboards (clutch, shooting, splits, opponent, etc.)
- Player tracking (shots, rebounds, passing, defense)
- Team tracking (shots, rebounds, passing)
- Cumulative stats (player & team)
- Game logs (player & team)
- Game streaks (player & team)
- Player career stats, profiles & awards
- Player vs player, Team vs player
- Team details & historical leaders
- Video events

Output: ~30,000 files (per-game, sample mode in script)
Runtime: 20-24 hours

### Total hoopR Endpoints Scope:
- **All Phases:** 152 endpoints
- **API Calls (24 seasons):** ~31,106 calls
- **Estimated Runtime:** 20-24 hours
- **Estimated Data Size:** 20-32 GB
- **Cost:** ~$0.74/month (negligible)

### hoopR Implementation Files Found:

**Comprehensive Scrapers:**
1. `/scripts/etl/scrape_hoopr_all_152_endpoints.R` (742 lines)
   - Complete R implementation
   - All 4 phases included
   - CSV output (avoids R 2GB string limit)
   - Per-season saving, Retry logic, Rate limiting, S3 upload

2. `/scripts/etl/scrape_hoopr_complete_all_endpoints.py` (Python wrapper)
   - AsyncBaseScraper integration
   - Async execution support
   - Framework migration compatible

3. `/scripts/etl/overnight_hoopr_all_152.sh` (Shell wrapper)
   - Production-ready automation
   - Error handling, Process management
   - Logging

**Wrapper Scripts:**
- `/scripts/etl/run_hoopr_comprehensive_overnight.sh`
- `/scripts/etl/run_hoopr_phase1.sh`
- `/scripts/etl/run_hoopr_phase1b.sh`
- `/scripts/etl/deploy_phase_9_2_hoopr_agent.sh`

**Infrastructure:**
- `/scripts/autonomous/setup_hoopr_cron.sh`
- `/scripts/autonomous/run_scheduled_hoopr.sh`
- `/nba_simulator/agents/hoopr.py` (Agent implementation)

**Current Incremental (Limited):**
- `/scripts/etl/hoopr_incremental_scraper.py` (20KB)
- `/scripts/etl/hoopr_incremental_simple.py` (7.8KB)

### Key Finding: 
**The comprehensive 152-endpoint scraper was documented and implemented but is NOT currently being used. Only incremental collection is active.**

---

## BASKETBALL REFERENCE DETAILED INVESTIGATION

### 234+ Data Types Discovered (October 10-11, 2025)

**Documentation Found:**
- `/Users/ryanranft/nba-simulator-aws/docs/data_sources/basketball_reference_COMPLETE_catalog_2025-10-11.md` (1,181 lines)
- `/Users/ryanranft/nba-simulator-aws/docs/phases/phase_0/0.0004_basketball_reference/BASKETBALL_REFERENCE_MASTER_CONFIG.json` (312 lines)
- `/Users/ryanranft/nba-simulator-aws/docs/data_sources/basketball_reference_comprehensive_scraper_summary.md` (485 lines)

### Total Data Types Available:

#### NBA Data (119 types)
**Already Collected (12 types):**
1. Season Totals (1947-2025)
2. Advanced Totals (1953-2025)
3. Team Standings (1971-2025)
4. Transactions (2001-2025)
5. Draft Data (2001-2025)
6. Per-Game Stats (2001-2025)
7. Shooting Stats (2001-2025)
8. Play-by-Play (2001-2025)
9. Team Ratings (2001-2025)
10. Playoff Stats (2001-2025)
11. Coach Records (2001-2025)
12. Awards (2024 tested, ready for full)

**Already Planned (14 types):**
- Adjusted Shooting Stats (2000-2025)
- Per 100 Possessions Stats (1974-2025)
- Game-by-Game Results/Schedule (1947-2025, ~70,000 games)
- Rookies Stats (1947-2025)
- All-Rookie Teams (1962-2025)
- Team Starting Lineups (2000-2025)
- Team Game Logs (1947-2025, all teams)
- Per Minute Stats (1952-2025)
- Season Leaders (1947-2025)
- Hall of Fame Inductees (~400 inductees)
- Executive Stats (GMs/Presidents)
- Team Referee Stats (Recent years)
- Jersey Numbers (Recent years)
- Player Game Logs (5M+ individual games, selective)
- Player Career Splits (Home/away, clutch, opponent, ~5K players)

**New NBA Data Types Discovered (93 types):**

**Salaries & Contracts (6 types):**
- Team Payroll by Season (2025-2031 future commitments)
- Player Contracts (Individual contracts, all active players)
- Historical Salaries (Past player salaries, 1990s-present)
- Salary Cap History (Historical cap values)
- Luxury Tax Data (Tax thresholds, team payments)
- Contracts Glossary (Contract terms, CBA rules)

**Team-Specific Data (8 types):**
- Team Depth Charts (Positional depth, recent years)
- Team Splits (Home/away, vs division, by month)
- Team On/Off Stats (Lineup impact)
- Franchise History Pages (Year-by-year records)
- Team Shooting Detailed (Shot charts, zones)
- Team Transactions by Team (Team-specific filtered)
- Team vs Opponent Stats (Head-to-head)
- Team Awards Summary (Championships, All-Stars)

**Player-Specific Data (12 types):**
- Player Similarity Scores (Career comparisons)
- Player Projections (Next season projections)
- Player FAQs (Common questions, milestones)
- Triple-Doubles Tracking (Per season)
- Player News & Updates (Recent articles)
- Player Game Highs (Career high in each category)
- Player Playoff Series Stats (Series-by-series)
- Player All-Star Game Stats (Per All-Star Game)
- Player Leaderboards (Career rankings)
- Player by Birth Place (Geographic tracking)
- Player by Birth Year (Age cohorts)
- Player by College (College-to-NBA tracking)

**Awards & Honors (15+ types):**
- Player of the Month (Monthly awards)
- Rookie of the Month
- Coach of the Month
- Defensive Player of the Month
- Player of the Week (Weekly awards)
- Social Justice Champion (Kareem Abdul-Jabbar Trophy)
- Sportsmanship Award (Joe Dumars Trophy)
- Clutch Player of the Year (Jerry West Trophy)
- In-Season Tournament MVP (2023+)
- NBA 75th Anniversary Team
- All-Defensive Teams (1969-present)
- All-NBA Teams (1947-present)
- Twyman-Stokes Teammate of the Year
- J. Walter Kennedy Citizenship Award
- Executive of the Year

**All-Star Weekend Events (5 types):**
- Rising Stars Challenge (1994-present)
- All-Star Skills Challenge (2003-present)
- Three-Point Contest (1986-present)
- Slam Dunk Contest (1984-present)
- Legends Game (1984-1993)

**Playoff-Specific Data (3 types):**
- Playoff Series Results (All series, winner/loser, dates)
- Playoff Series Betting Odds (Historical betting lines)
- 7-Game Series Outcomes (Game-by-game results)

**Advanced Stats & Ratings (8 types):**
- SRS (Simple Rating System)
- SOS (Strength of Schedule)
- Adjusted Offensive Rating (ORtg/A)
- Adjusted Defensive Rating (DRtg/A)
- Adjusted Net Rating (NRtg/A)
- Adjusted MOV (Margin of Victory)
- Four Factors (Detailed)
- Pace (Possessions per 48)

**Shooting Statistics (Granular) (5 types):**
- Shooting by Distance Zones (FG% by distance)
- Dunk Tracking (Dunks made/attempted)
- Corner 3-Point Shooting (Specific corner 3s)
- Heave Shots (Long-distance heaves)
- Percentage of FG Assisted (Shot creation)

**Play-by-Play Derived Stats (6 types):**
- Position Percentage Breakdown (% time at each position)
- OnCourt Plus/Minus (Team performance with player)
- On-Off Differential (Net impact)
- Bad Pass Turnovers (Specific TO type)
- Lost Ball Turnovers (Specific TO type)
- Fouls Drawn (Not just committed)
- And1 Plays (Fouls drawn on made shots)
- Shots Blocked (On defense)

**Miscellaneous Tools & Databases (20+ types):**
- Injury Report (Current injuries, rolling ~30 days)
- Preseason Odds (Betting markets)
- Buzzer-Beaters Database (Game-winning shots)
- "Cups of Coffee" (One-game players)
- Daily Leaders (Historical top performers)
- Eastern vs Western Conference Records (Head-to-head)
- Historical Standings by Date (Standings evolution)
- Milestones Watch (Approaching milestones)
- Franchise Milestones (Team records)
- MVP Award Tracker (Season-long tracker)
- Playoff Probabilities (Real-time playoff odds)
- Roster Continuity (% of minutes returning)
- Simple Projection System (Team projections)
- Players Who Played for Multiple Teams (Career tracking)
- Teammates & Opponents (Shared time tracking)
- Trade Partners (Trade history)
- Most Games Without Playoffs (Playoff droughts)
- "On This Date" Historical Events (Notable events)
- Last N Days Stats (Rolling performance)
- Uniform Numbers (Jersey tracking)

#### Other Leagues/Domains:

**WNBA (1997-2025):** 16 data types
- Season Totals, Per-Game Stats, Advanced Stats
- Team Standings, Team Statistics
- Player Game Logs, All-Star Games
- Draft, Supplemental Draft
- Awards, Playoff Stats
- Daily Scores, Career Leaderboards
- Season Leaders, Rookie Records
- Player Headshots

**G League (2002-2025):** 10 data types
- Season Standings, Player Statistics
- Team Rosters, Game Logs
- Daily Scores, Awards
- Season Leaders, Career Leaders
- Top Performers, Box Scores

**ABA (1967-1976):** 12 data types
- Season Totals, Per-Game Stats, Per 36 Minutes
- Per 100 Possessions, Advanced Stats
- Adjusted Shooting, Team Standings
- Team Stats, Playoff Stats
- All-Star Games, Awards, Coaches

**BAA (1946-1949):** 8 data types
- Season Totals, Per-Game Stats
- Team Standings, Team Stats
- Playoff Stats, Championships
- Coaches, Draft (if available)

**International Basketball (15+ leagues):**
- Olympics (Men's & Women's)
- FIBA World Cup
- EuroLeague, EuroCup
- Liga ACB (Spain), Serie A (Italy)
- Greek Basket League, Pro A (France)
- Chinese Basketball Association
- NBL (Australia), ABA League (Europe)
- Israeli League, Turkish League, VTB League

**College Basketball:** 30+ data types
- NCAA Division I Player Stats, Team Stats
- Conference Standings, Schedule & Results
- Tournament Results (NCAA, NIT, CBI, CIT)
- Tournament Brackets, Conference Data
- Coach Records, Player Game Logs
- Team Game Logs, Awards
- AP/Coaches Polls, Statistical Leaders
- Tournament Most Outstanding Player
- Player/Team Finders, Biographical Data
- Transfer Portal Data, Women's Basketball
- Divisions II & III, Buzzer-Beaters
- Milestones, Conference Tournaments

### Total Basketball Reference Scope:

**NBA Only (Tiers 1-9):**
- 119 data types (27 collected + 14 planned + 78 new)
- Time: 67-97 hours
- Records: 490K-10M+
- Storage: 560 MB - 10 GB

**All Basketball (Tiers 1-13):**
- 234+ data types
- Time: 140-197 hours
- Records: 870K-10M+
- Storage: 1.36 GB - 11 GB
- Cost: <$0.30/month (negligible)

### Basketball Reference Implementation Files Found:

**Comprehensive Scrapers:**
1. `/scripts/etl/scrape_basketball_reference_comprehensive.py` (689 lines)
   - 8 of 9 data types working (89%)
   - Generic table parser
   - Special handling for awards in HTML comments
   - CSV output format
   - Rate limiting: 12s between requests
   - S3 upload integration

2. `/scripts/etl/basketball_reference_box_score_scraper.py` (29KB)
   - Specialized for box score data

3. `/scripts/etl/basketball_reference_pbp_backfill.py` (19KB)
   - Play-by-play backfill

4. `/scripts/etl/basketball_reference_daily_pbp.py` (19KB)
   - Daily PBP collection

5. `/scripts/etl/basketball_reference_daily_box_scores.py` (15KB)
   - Daily box scores

**Wrapper Scripts:**
- `/scripts/etl/overnight_basketball_reference_comprehensive.sh`
- `/scripts/etl/rescrape_basketball_reference_failed_years.sh`

**Integration Tools:**
- `/scripts/etl/integrate_basketball_reference.py` (22KB)
- `/scripts/etl/integrate_basketball_reference_aggregate.py`

**Current Incremental (Limited):**
- `/scripts/etl/basketball_reference_incremental_scraper.py`

### S3 Basketball Reference Data Currently Stored:

**Data Types with Full Historical Coverage:**
1. Advanced Totals (1953-2025)
2. Per-Game Stats (2001-2025)
3. Shooting Stats (2001-2025)
4. Play-by-Play Stats (2001-2025)
5. Team Ratings (2001-2025)
6. Playoffs Stats (2001-2025)
7. Coaches Records (2001-2025)
8. Awards (2024 tested)

**Data Structure in S3:**
```
s3://nba-sim-raw-data-lake/basketball_reference/
├── season_totals/          (1947-2025)
├── advanced_totals/        (1953-2025)
├── per_game/              (2001-2025)
├── shooting/              (2001-2025)
├── play_by_play/          (2001-2025)
├── team_ratings/          (2001-2025)
├── playoffs/              (2001-2025)
├── coaches/               (2001-2025)
├── draft/                 (2001-2025)
├── awards/                (2024 sample)
├── schedules/             (incomplete)
└── Legacy files/          (1993-2025, partial)
```

**Total Basketball Reference in S3:**
- Approximately 290+ files
- ~100+ MB data
- 8 primary data types
- Missing: 226+ additional data types

---

## DATA MIGRATION HISTORY

### What Changed Since October:

**October 7, 2025:**
- Comprehensive hoopR 152-endpoint scraper documented
- Basketball Reference master config created (234+ data types)

**October 10-11, 2025:**
- Basketball Reference comprehensive scraper implemented (8/9 types working)
- Scraper successfully collected 2001-2025 data
- Uploaded to S3 with proper validation

**November 6, 2025:**
- Recent session handoffs show ESPN data being filled via incremental scraper
- hoopR and Basketball Reference appear to have switched to incremental mode
- No mention of 152-endpoint hoopR scraper being run
- No mention of comprehensive Basketball Reference scraper being run

### Why the Switch Happened:

Most likely reasons (inferred from codebase):
1. **Framework Migration:** Both old comprehensive scrapers being migrated to AsyncBaseScraper framework
2. **Performance:** Running 152+ endpoints at once was 20+ hours - incremental collection faster for daily updates
3. **Resource Constraints:** Decided to focus on daily/weekly incremental collection instead of comprehensive backfills
4. **Focus Shift:** Effort redirected to ESPN (more structured, fewer rate limits)

---

## CURRENT DATA GAPS

### Missing from Incremental Collection:

#### hoopR (152 endpoints):
- **Phase 1-3 data:** Play-by-play, Box scores, Schedules, Dashboards (core data)
- **Phase 4 data:** Per-game granular boxscores (rarely collected)
- **Historical coverage:** Only recent games collected
- **Advanced endpoints:** Shot charts, Synergy, Tracking (not in incremental)

#### Basketball Reference (234 data types):
- **Salaries & Contracts:** All 6 types missing
- **Awards:** Most monthly/weekly awards missing
- **All-Star Events:** Complete collection missing
- **Granular Shooting:** 5 additional shooting stat types
- **Granular PBP:** 6 additional play-by-play derived stats
- **Advanced Metrics:** Some adjusted ratings missing
- **Other Leagues:** WNBA, G League, ABA, BAA, International, College (all missing)
- **Tools & Databases:** Most miscellaneous databases missing

**In terms of data loss:**
- hoopR: Potentially ~100+ GB per season if all 152 endpoints were collected
- Basketball Reference: Potentially 1-11 GB of additional historical and specialized data

---

## RECOMMENDATIONS

### Immediate Actions:

1. **Restore hoopR Comprehensive Collection**
   - Reactivate `/scripts/etl/scrape_hoopr_all_152_endpoints.R`
   - Run for at least 2020-2025 to fill gaps
   - Cost: <$1/month, Benefit: 100+ GB enriched data
   - Time: ~10-15 hours for 6 seasons

2. **Restore Basketball Reference Historical Collection**
   - Use `/scripts/etl/scrape_basketball_reference_comprehensive.py`
   - Focus on Tiers 1-2 (NBA High Value + Strategic, 35-45 hours)
   - Tier 5A (Salaries, 8-10 hours) for financial analysis
   - Cost: <$0.30/month, Benefit: 2-5 GB additional data

3. **Decide on Multi-League Expansion**
   - If only NBA-only: Stop after Tiers 1-9
   - If multi-league: Add WNBA (Tier 10), ABA/BAA (Tiers 7-8)
   - If comprehensive: Add International + College (Tiers 12-13)

### Strategic Options:

**Option A: Get Back to 100% NBA Coverage (Recommended)**
- Restore 152 hoopR endpoints
- Restore all 119 Basketball Reference NBA data types
- Time: 100-150 hours
- Data: 10-15 GB additional
- Cost: <$1/month
- Benefit: Complete NBA intelligence for simulation/modeling

**Option B: Maintain Current (Incremental Only)**
- Keep ESPN + hoopR/Basketball Reference incremental for daily updates
- Loss: Historical comprehensive datasets, granular metrics
- Benefit: Simpler operations, daily updates only
- Risk: Missing important historical context for ML models

**Option C: Hybrid Approach (Optimal)**
- Comprehensive collection monthly (not daily)
- hoopR Phase 1-3 (45-60 min monthly)
- Basketball Reference Tiers 1-2 (35-45 hours initially, then 5-10 hours monthly)
- Keeps daily incremental for recent data
- Benefit: Best of both worlds

---

## KEY FINDINGS

### Finding 1: Documentation Was Thorough
You had created extensive documentation for both hoopR (152 endpoints) and Basketball Reference (234 data types) in October 2025. This was high-quality work identifying the full data universe available.

### Finding 2: Implementation Was Complete
Working, production-ready scrapers exist for both:
- hoopR: Comprehensive R script with all 4 phases
- Basketball Reference: Python scraper working at 89% success rate (8/9 types)

### Finding 3: Data Switch Happened
Both sources switched from comprehensive to incremental collection sometime between October and November. The decision appears intentional but is not documented in recent handoff files.

### Finding 4: Data Loss Is Real
- hoopR: 152-endpoint collection capability lost (20+ hours of potential data per run)
- Basketball Reference: 226 data types no longer actively collected
- This is significant for ML model training and historical analysis

### Finding 5: Cost/Benefit Is Heavily In Favor Of Comprehensive Collection
- hoopR comprehensive: 152 endpoints = <$1/month S3 cost, 20-30 hours time
- Basketball Reference comprehensive: 234 types = <$0.30/month S3 cost, variable time
- Total cost: Negligible (~$1.30/month)
- Total value: 10-15 GB enriched data for ML/simulation

### Finding 6: Current Gaps in Data
As of November 6, 2025:
- ESPN: Current through Nov 6 (recent session filled Oct 7-Nov 6 gap)
- hoopR: Limited to incremental (no comprehensive collection)
- Basketball Reference: Limited to incremental (no comprehensive collection)

---

## S3 DATA SUMMARY

**Current Data in S3:**
- ESPN: Full play-by-play, box scores, schedules (2001-2025+)
- Basketball Reference: 8 data types (1947-2025, with gaps)
- hoopR: Minimal (only recent incremental data)

**Missing Data:**
- hoopR Phase 1-3: All 69 endpoints (69 data types)
- hoopR Phase 4: Per-game boxscores (87 data types)
- Basketball Reference: 226 data types (Tiers 3-13)
- Other leagues: WNBA, G League, ABA, BAA, International, College (116 data types)

**Total Missing Capacity:**
- Data types: ~400+ potential data types
- Storage: 10-15 GB additional data
- Cost: <$2/month
- Value for ML: Significant (comprehensive feature engineering)

---

## CONCLUSION

You had an ambitious, well-documented plan for comprehensive data collection from hoopR and Basketball Reference. Both had working implementations ready to deploy. At some point, the focus shifted to incremental collection only.

**The question is:** Should this be restored?

**Arguments for restoration:**
1. Data completeness for ML models
2. Historical context for simulation
3. Negligible cost (<$2/month)
4. Existing working implementations
5. Comprehensive documentation already exists

**Arguments against restoration:**
1. Requires 100+ hours of API calls
2. May be rate-limited by data sources
3. Current incremental approach keeps system simpler
4. Daily updates may be sufficient for your use cases

**Recommendation:** Restore comprehensive collection on a monthly (not daily) basis for hoopR and Basketball Reference to fill knowledge gaps while maintaining incremental collection for real-time updates.

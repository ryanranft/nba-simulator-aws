# Phase 0 - TIERS 11-13: Multi-League Basketball Collection

**Phase:** 0 (Data Collection - Multi-League)
**Sub-Phases:** 0.11 (G League), 0.12 (International), 0.13 (College)
**Status:** ⏸️ PENDING
**Scope:** G League + International + College Basketball
**Estimated Time:** 58-80 hours total
**Records:** ~280,000
**Cost Impact:** +$0.007/month S3 storage
**Priority:** EXECUTE (Option C selected)

---

## TIER 11: G LEAGUE (NBA Development League)

**Coverage:** 2002-2025 (23 seasons)
**Time:** 8-10 hours
**Records:** ~30,000
**Cost:** +$0.001/month

### Overview

The G League (formerly NBA Development League, D-League) is the NBA's official minor league. Collecting this data provides developmental player tracking and prospect analysis.

### Sub-Phase 0.11: G League Data Types (10 types)

#### 0.11.1: G League Season Standings (2002-2025)
- **URL:** `/gleague/years/NBA-D-League_{season}.html` (or `/NBA-G-League_{season}.html` for recent years)
- **Data:** Team records, playoff seeds
- **Records:** ~450 (23 seasons × ~20 teams)
- **Time:** 30 min

#### 0.11.2: G League Player Statistics (2002-2025)
- **URL:** Same as standings page
- **Tables:** Per-game, totals, advanced
- **Records:** ~15,000 player-seasons
- **Time:** 3 hours

#### 0.11.3: G League Team Rosters (2002-2025)
- **URL:** `/gleague/teams/{TEAM}/{season}.html`
- **Data:** Player rosters by team/season
- **Records:** ~450 team rosters
- **Time:** 1 hour

#### 0.11.4: G League Game Logs (2002-2025)
- **URL:** `/gleague/players/{X}/{player_slug}/gamelog/{season}`
- **Data:** Player game-by-game stats
- **Records:** ~10,000 (selective: top prospects only)
- **Time:** 2 hours (selective) or 8-10 hours (all players)

#### 0.11.5: G League Daily Scores (2002-2025)
- **URL:** `/gleague/years/NBA-D-League_{season}_games.html`
- **Data:** Game results by date
- **Records:** ~5,000 games
- **Time:** 30 min

#### 0.11.6: G League Awards (2002-2025)
- **Awards:** MVP, Rookie of the Year, All-League Teams
- **Records:** ~500 awards
- **Time:** 1 hour

#### 0.11.7: G League Season Leaders (2002-2025)
- **Data:** Top performers in each category per season
- **Records:** ~2,000
- **Time:** 30 min

#### 0.11.8: G League Career Leaders (All-time)
- **Data:** Career statistical leaders
- **Records:** ~500
- **Time:** 30 min

#### 0.11.9: G League Top Performers (Current season)
- **Data:** Recent standout performances
- **Records:** Variable
- **Time:** 15 min

#### 0.11.10: G League Box Scores (2002-2025)
- **URL:** Game-specific pages
- **Data:** Game-level statistics
- **Records:** ~5,000 games
- **Time:** 1 hour (if collecting detailed box scores)

### Implementation

**Scraper Configuration:**
```python
G_LEAGUE_DATA_TYPES = {
    'season_stats': {
        'url_pattern': '/gleague/years/NBA-D-League_{season}.html',
        'min_year': 2002,
        'max_year': 2017,
        's3_prefix': 'basketball_reference/gleague/season_stats'
    },
    'season_stats_modern': {
        'url_pattern': '/gleague/years/NBA-G-League_{season}.html',
        'min_year': 2018,  # Rebranded to G League
        'max_year': 2025,
        's3_prefix': 'basketball_reference/gleague/season_stats'
    }
}
```

**Key Considerations:**
- League renamed from "D-League" to "G League" in 2017-18
- URL patterns change: `NBA-D-League` → `NBA-G-League`
- Fewer teams in early years (~8) vs modern (~30)

### Success Criteria
- [ ] 10 data types collected
- [ ] 23 seasons covered (2002-2025)
- [ ] ~30,000 records total
- [ ] Time: 8-10 hours

---

## TIER 12: INTERNATIONAL BASKETBALL

**Coverage:** 1936-2025 (varies by competition)
**Time:** 20-30 hours (selective)
**Records:** ~50,000 (selective)
**Cost:** +$0.001/month

### Overview

International basketball data includes Olympics, FIBA World Cup, and major professional leagues (EuroLeague, Liga ACB, etc.). **Selective collection recommended** - focus on Olympics, FIBA, and EuroLeague.

### Sub-Phase 0.12: International Data (40 types, collect 10-15 selectively)

#### PRIORITY 1: Olympics (5 types) - 2-3 hours

**0.12.1: Men's Olympics Player Stats (1936-2024)**
- **URL:** `/international/olympics/` or `/international/olympics/{year}-men.html`
- **Data:** Player statistics by tournament
- **Records:** ~5,000
- **Value:** Elite international competition

**0.12.2: Women's Olympics Player Stats (1936-2024)**
- **URL:** `/international/olympics/{year}-women.html`
- **Data:** Women's tournament statistics
- **Records:** ~3,000

**0.12.3-0.12.5: Olympics Team Stats & Medal Standings**
- **Data:** Team performance, medal counts
- **Records:** ~500

**Implementation:**
- Scrape Olympics index
- Iterate tournament years (every 4 years: 1936, 1948, ..., 2024)
- Extract player/team stats, medal results

---

#### PRIORITY 2: FIBA World Cup (3 types) - 1-2 hours

**0.12.6: FIBA Player Stats (2010-2023)**
- **URL:** `/international/fiba-world-cup/` or tournament-specific pages
- **Data:** World Cup player statistics
- **Records:** ~2,000
- **Value:** International competition outside Olympics

**0.12.7-0.12.8: FIBA Team Stats & Standings**
- **Records:** ~200

**Implementation:**
- Scrape FIBA World Cup pages
- Tournaments: 2010, 2014, 2019, 2023
- Extract player/team stats

---

#### PRIORITY 3: EuroLeague (4 types) - 4-5 hours

**0.12.9: EuroLeague Player Stats (2000-2025)**
- **URL:** `/international/euroleague/`
- **Data:** Top European club competition
- **Records:** ~15,000 player-seasons
- **Value:** European prospect scouting

**0.12.10-0.12.12: EuroLeague Team Stats, Standings, Playoffs**
- **Records:** ~1,500

**Implementation:**
- Scrape EuroLeague season pages (2000-2025, 26 seasons)
- Extract player/team statistics
- Playoff results

---

#### OPTIONAL: Other Leagues (28 types) - 12-18 hours

**Select 2-3 leagues based on interest:**

**0.12.13-0.12.15: EuroCup** (2002-2025)
- Records: ~5,000

**0.12.16-0.12.18: Liga ACB - Spain** (1983-2025)
- Records: ~10,000
- Value: Top Spanish league

**0.12.19-0.12.21: Lega Serie A - Italy** (1998-2025)
- Records: ~5,000

**0.12.22-0.12.24: Greek Basket League** (2001-2025)
- Records: ~3,000

**0.12.25-0.12.27: LNB Pro A - France** (2002-2025)
- Records: ~5,000

**0.12.28-0.12.30: CBA - China** (2011-2025)
- Records: ~3,000

**0.12.31-0.12.33: NBL - Australia** (2011-2025)
- Records: ~3,000

**0.12.34-0.12.37: Other leagues** (ABA First Division, Israeli, Turkish, VTB)
- Records: ~2,000

### Recommended Selective Approach

**Tier 12A: Essential (10 hours)**
- Olympics (all)
- FIBA World Cup (all)
- EuroLeague (all)
- **Records:** ~26,000

**Tier 12B: Extended (10 hours)**
- Add Liga ACB, Lega Serie A, Greek League
- **Records:** +18,000

**Tier 12C: Comprehensive (10 hours)**
- Add all remaining leagues
- **Records:** +6,000

**Recommended: Tier 12A (10 hours, 26K records)**

### Implementation

**Scraper Configuration:**
```python
INTERNATIONAL_DATA_TYPES = {
    'olympics_men': {
        'url_pattern': '/international/olympics/{year}-men.html',
        'years': [1936, 1948, 1952, ..., 2024],  # Every 4 years
        's3_prefix': 'basketball_reference/international/olympics'
    },
    'fiba_world_cup': {
        'url_pattern': '/international/fiba-world-cup/{year}.html',
        'years': [2010, 2014, 2019, 2023],
        's3_prefix': 'basketball_reference/international/fiba'
    },
    'euroleague': {
        'url_pattern': '/international/euroleague/{season}.html',
        'min_year': 2000,
        'max_year': 2025,
        's3_prefix': 'basketball_reference/international/euroleague'
    }
}
```

### Success Criteria (Selective - Tier 12A)
- [ ] 10 data types collected (Olympics, FIBA, EuroLeague)
- [ ] ~26,000 records
- [ ] Time: 10 hours

---

## TIER 13: COLLEGE BASKETBALL

**Coverage:** 1891-2025 (selective: focus on modern era + NCAA Tournament)
**Time:** 30-40 hours (selective)
**Records:** ~200,000 (selective)
**Cost:** +$0.005/month

### Overview

College basketball data is on a separate site (sports-reference.com/cbb/). **Selective collection recommended** - focus on NCAA Division I, tournaments, and recent decades.

### Sub-Phase 0.13: College Data (30 types, collect 10-15 selectively)

#### PRIORITY 1: NCAA Tournament (5 types) - 8-10 hours

**0.13.1: NCAA Tournament Results - Men's (1939-2025)**
- **URL:** `/cbb/postseason/` or tournament-specific pages
- **Data:** Complete tournament brackets, game results
- **Records:** ~5,000 games
- **Value:** March Madness complete history

**0.13.2: NCAA Tournament Results - Women's (1982-2025)**
- **Data:** Women's tournament history
- **Records:** ~2,500 games

**0.13.3: NCAA Tournament Most Outstanding Player**
- **Data:** MOP award winners
- **Records:** ~85

**0.13.4: Final Four History**
- **Data:** Final Four teams and results
- **Records:** ~350

**0.13.5: NCAA Bracket History**
- **Data:** Seeding, upsets, Cinderella runs
- **Value:** Tournament analytics

**Implementation:**
- Scrape NCAA Tournament index
- Extract brackets for each year (1939-2025)
- Parse game results, winners, scores

---

#### PRIORITY 2: NCAA Division I Stats - Modern Era (5 types) - 10-12 hours

**Focus:** 2000-2025 (26 seasons) for manageable scope

**0.13.6: NCAA D1 Player Stats (2000-2025)**
- **URL:** `/cbb/seasons/{season}-player-stats.html`
- **Data:** Season statistics (totals, per-game, advanced)
- **Records:** ~80,000 player-seasons (26 years × ~3,000 D1 players/year)
- **Value:** College player performance

**0.13.7: NCAA D1 Team Stats (2000-2025)**
- **URL:** `/cbb/seasons/{season}-team-stats.html`
- **Data:** Team statistics
- **Records:** ~9,000 team-seasons (26 years × 350 teams)

**0.13.8: NCAA D1 Conference Standings (2000-2025)**
- **Data:** Conference records
- **Records:** ~900 (26 years × ~35 conferences)

**0.13.9: NCAA D1 Schedule & Results (2000-2025)**
- **Data:** Game-by-game results
- **Records:** ~300,000 games (26 years × ~11,500 games/year)
- **Note:** Very large dataset, consider sampling

**0.13.10: College Coach Records (2000-2025)**
- **Data:** Coaching records by season
- **Records:** ~3,000

---

#### PRIORITY 3: College Awards (5 types) - 4-5 hours

**0.13.11: Player of the Year Awards**
- **Awards:** AP, Wooden, Naismith, Oscar Robertson, etc.
- **Records:** ~500

**0.13.12: All-America Teams**
- **Data:** First Team, Second Team, Third Team
- **Records:** ~1,500

**0.13.13: Conference Player of the Year**
- **Data:** Awards by conference
- **Records:** ~1,000

**0.13.14: NCAA Tournament MOP** (duplicate of 0.13.3)

**0.13.15: Conference Awards** (various)

---

#### PRIORITY 4: Additional College Data (15 types) - 8-13 hours

**Polls (2 types):**
- **0.13.16:** AP Poll history (2000-2025)
- **0.13.17:** Coaches Poll history (2000-2025)

**Leaders (2 types):**
- **0.13.18:** Season statistical leaders (2000-2025)
- **0.13.19:** Career leaders (all-time)

**Tools (2 types):**
- **0.13.20:** Player Season Finder (query tool)
- **0.13.21:** Team Season Finder (query tool)

**Additional Tournaments (3 types):**
- **0.13.22:** NIT Results (1938-2025)
- **0.13.23:** CBI Tournament (2008-2025)
- **0.13.24:** CIT Tournament (2009-2018, discontinued)

**Women's College Basketball (3 types):**
- **0.13.25:** Women's Player Stats (1981-2025)
- **0.13.26:** Women's Team Stats (1981-2025)
- **0.13.27:** Women's NCAA Tournament (1982-2025)

**Miscellaneous (3 types):**
- **0.13.28:** Conference Tournament Results (2000-2025)
- **0.13.29:** College Buzzer-Beaters
- **0.13.30:** College Milestones

### Recommended Selective Approach

**Tier 13A: Essential - NCAA Tournament Focus (10 hours)**
- NCAA Tournament (men's & women's) - all years
- Tournament awards, Final Four history
- **Records:** ~8,000

**Tier 13B: Modern Stats (12 hours)**
- Add NCAA D1 player/team stats (2000-2025)
- Conference standings, coach records
- **Records:** +92,000

**Tier 13C: Awards & Polls (5 hours)**
- Add all college awards
- Polls history
- **Records:** +3,000

**Tier 13D: Comprehensive (3 hours)**
- Add NIT, women's basketball, misc
- **Records:** +7,000

**Recommended: Tier 13A + 13B (22 hours, 100K records)**

### Implementation

**Scraper Configuration:**
```python
# Different domain: sports-reference.com/cbb/

COLLEGE_DATA_TYPES = {
    'ncaa_tournament': {
        'url_pattern': 'https://www.sports-reference.com/cbb/postseason/{year}-ncaa.html',
        'min_year': 1939,
        'max_year': 2025,
        's3_prefix': 'basketball_reference/college/ncaa_tournament'
    },
    'player_stats': {
        'url_pattern': 'https://www.sports-reference.com/cbb/seasons/{season}-player-stats.html',
        'min_year': 2000,  # Selective: modern era only
        'max_year': 2025,
        's3_prefix': 'basketball_reference/college/player_stats'
    },
    'team_stats': {
        'url_pattern': 'https://www.sports-reference.com/cbb/seasons/{season}-team-stats.html',
        'min_year': 2000,
        'max_year': 2025,
        's3_prefix': 'basketball_reference/college/team_stats'
    }
}
```

**Key Considerations:**
- **Different domain:** sports-reference.com/cbb/ (not basketball-reference.com)
- **Large dataset:** NCAA D1 has ~350 teams, ~11,500 games/year
- **Recommend selective years:** 2000-2025 (26 seasons) vs all-time (100+ seasons)
- **Tournament focus:** Highest value data for draft pipeline analysis

### Success Criteria (Selective - Tiers 13A + 13B)
- [ ] 10 data types collected (tournament + modern stats)
- [ ] ~100,000 records
- [ ] Time: 22 hours

---

## COMBINED IMPLEMENTATION TIMELINE

### Tiers 11-13 Complete Schedule

**Month 1: G League + International (3-4 weeks)**
- Week 1: G League season stats, standings, awards (4-5 hours)
- Week 2: G League game logs, leaders, box scores (4-5 hours)
- Week 3: International - Olympics & FIBA (3-4 hours)
- Week 4: International - EuroLeague (4-5 hours)

**Month 2: College Basketball (4-5 weeks)**
- Week 5: NCAA Tournament - Men's (4-5 hours)
- Week 6: NCAA Tournament - Women's & Awards (4-5 hours)
- Week 7: NCAA D1 Player Stats 2000-2025 (6-7 hours)
- Week 8: NCAA D1 Team Stats, Standings, Coaches (4-5 hours)
- Week 9: NCAA Polls, Awards, NIT (if desired) (3-4 hours)

**Total: 36-48 hours over 9 weeks (4-5 hours/week)**

---

## Technical Implementation

### Multi-Domain Scraper

```python
class MultiLeagueScraper:
    """
    Scraper supporting multiple basketball leagues and domains
    """

    DOMAINS = {
        'nba': 'https://www.basketball-reference.com',
        'wnba': 'https://www.basketball-reference.com',
        'gleague': 'https://www.basketball-reference.com',
        'aba': 'https://www.basketball-reference.com',
        'baa': 'https://www.basketball-reference.com',
        'international': 'https://www.basketball-reference.com',
        'college': 'https://www.sports-reference.com'  # Different domain!
    }

    def __init__(self, league='nba'):
        self.league = league.lower()
        self.BASE_URL = self.DOMAINS[self.league]
        self.rate_limit = 12  # seconds

    def scrape_league(self, data_types, start_year, end_year):
        """Scrape specified data types for a league"""
        for data_type in data_types:
            for year in range(start_year, end_year + 1):
                self.scrape_data_type(data_type, year)
                time.sleep(self.rate_limit)
```

### Running Multi-League Collection

```bash
# G League
python scripts/etl/scrape_basketball_reference_comprehensive.py \
    --league gleague \
    --start-season 2002 \
    --end-season 2025 \
    --upload-to-s3

# International (selective)
python scripts/etl/scrape_basketball_reference_comprehensive.py \
    --league international \
    --competitions olympics,fiba,euroleague \
    --upload-to-s3

# College (selective - tournament + modern stats)
python scripts/etl/scrape_basketball_reference_comprehensive.py \
    --league college \
    --data-types ncaa_tournament,player_stats,team_stats \
    --start-season 2000 \
    --end-season 2025 \
    --upload-to-s3
```

---

## Success Criteria - Tiers 11-13 Complete

### Tier 11: G League ✅
- [ ] 10 data types collected
- [ ] 23 seasons (2002-2025)
- [ ] ~30,000 records
- [ ] Time: 8-10 hours

### Tier 12: International ✅
- [ ] 10 data types collected (selective: Olympics, FIBA, EuroLeague)
- [ ] ~26,000 records
- [ ] Time: 10 hours

### Tier 13: College ✅
- [ ] 10 data types collected (selective: Tournament + modern stats)
- [ ] ~100,000 records
- [ ] Time: 22 hours

**Total Tiers 11-13: 30 data types, ~156K records, 40-42 hours**

---

## S3 Storage Structure

```
s3://nba-sim-raw-data-lake/basketball_reference/
├── gleague/
│   ├── season_stats/
│   │   ├── 2002/...
│   │   └── 2025/...
│   ├── awards/
│   └── game_logs/
├── international/
│   ├── olympics/
│   │   ├── 1936_men.json
│   │   └── .../2024_men.json
│   ├── fiba/
│   │   ├── 2010.json
│   │   └── .../2023.json
│   └── euroleague/
│       ├── 2000/...
│       └── 2025/...
└── college/
    ├── ncaa_tournament/
    │   ├── 1939/...
    │   └── 2025/...
    ├── player_stats/
    │   ├── 2000/...
    │   └── 2025/...
    └── team_stats/
        ├── 2000/...
        └── 2025/...
```

---

## Integration with Existing System

### Database Tables

```sql
-- G League
CREATE TABLE gleague_season_stats (...);
CREATE TABLE gleague_awards (...);

-- International
CREATE TABLE olympics_player_stats (...);
CREATE TABLE fiba_player_stats (...);
CREATE TABLE euroleague_player_stats (...);

-- College
CREATE TABLE ncaa_tournament_games (...);
CREATE TABLE ncaa_player_stats (...);
CREATE TABLE ncaa_team_stats (...);
```

---

## Next Steps After Completion

1. **Load data to RDS PostgreSQL**
2. **Create unified multi-league views**
3. **Update ML pipelines for multi-league features**
4. **Cross-league analytics**
5. **Draft pipeline analysis (college → G League → NBA → International)**

---

**Tier Owner:** Data Collection Team
**Last Updated:** October 11, 2025
**Status:** Ready for execution (Option C selected)
**Next Action:** Begin Tier 11 (G League) after completing Tiers 1-10
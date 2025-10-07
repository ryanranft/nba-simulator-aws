# NBA Data Sources - Multi-Source Strategy

**Last Updated:** October 7, 2025
**Status:** Active - 5 sources configured (with temporal precision tracking)

---

## Overview

This project uses a **multi-source data strategy** to ensure data quality, completeness, and redundancy. Each source serves a specific purpose and fills gaps in the others.

**Philosophy:**
- **Primary source:** ESPN (already uploaded to S3, 1999-2025)
- **Verification sources:** 4 additional sources for cross-validation and gap-filling
- **Goal:** Achieve 95%+ data completeness and accuracy

---

## Data Source Registry

### 1. ESPN API (Primary Source)

**Status:** ✅ ACTIVE (146,115 files in S3)

**API Endpoints:**
- Schedule: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard`
- Box Score: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={game_id}`
- Play-by-play: `https://site.api.espn.com/apis/site/v2/sports/basketball/nba/playbyplay?event={game_id}`

**Coverage:**
- Date range: 1999-2025
- Data quality: 83% valid files
- Missing: 17% empty files (future/cancelled games)

**Fields Available:**
- Games: 53 fields
- Play-by-play: Full event stream
- Box scores: Player and team stats
- Team stats: Per-game statistics

**Use Cases:**
- Primary data source for all historical games
- Real-time updates for current season
- Complete play-by-play history

**Scripts:**
- `scripts/etl/scrape_missing_espn_data.py` - Scrape missing data (2022-2025)
- `scripts/etl/run_espn_scraper.sh` - Wrapper for easy execution

---

### 2. NBA.com Stats API (Verification Source #1)

**Status:** ✅ ACTIVE (LIMITED - Testing Phase)

**API Type:** Official NBA Stats API via `nba_api` Python package

**Implementation:** `nba_api` (Python wrapper for stats.nba.com)

**Key Endpoints (Tier 1 - ENABLED):**

**Advanced Box Scores (8 endpoints):**
- `boxscoreadvancedv2` - Advanced efficiency metrics
- `boxscoredefensivev2` - Defensive statistics
- `boxscorefourfactorsv2` - Four factors breakdown
- `boxscoremiscv2` - Miscellaneous stats
- `boxscoreplayertrackv2` - Player tracking metrics
- `boxscorescoringv2` - Scoring breakdown
- `boxscoretraditionalv2` - Traditional box scores
- `boxscoreusagev2` - Usage rates

**Player Tracking (4 endpoints):**
- `playerdashptpass` - Passing stats (passes made, potential assists)
- `playerdashptreb` - Rebounding stats (contested, chances)
- `playerdashptshotdefend` - Shot defense (contests, DFG%)
- `playerdashptshots` - Shot tracking (touch time, dribbles)

**League Dashboards (7 endpoints):**
- `leaguedashplayerstats` - Player statistics
- `leaguedashteamstats` - Team statistics
- `leaguedashlineups` - Lineup combinations
- `leaguedashptdefend` - Player tracking defense
- `leaguedashptstats` - Player tracking stats
- `leaguedashptteamdefend` - Team tracking defense
- `leagueleaders` - League leaders

**Additional Endpoints:**
- `leaguehustlestatsplayer` / `leaguehustlestatsteam` - Hustle stats
- `draftcombinestats` / `drafthistory` - Draft data
- `shotchartdetail` - Shot chart data
- `synergyplaytypes` - Synergy play types (10 categories)

**Coverage:**
- Date range: 1996-2025 (30 seasons)
- Data quality: 100% (official NBA source)
- **Current scrape:** Testing limits (100 games, 50 players per season)
- **Production capability:** All games (~1,230/season), all players (~500/season)

**Rate Limiting:**
- 600ms between API calls
- ~1.67 requests per second
- Enforced via `_rate_limit()` method

**Features Added:**
- Tier 1 endpoints: 60-80 advanced features
- Total features: 269-289 (up from 209)

**Current Status:**
- ✅ Scraper running overnight (started 10:56 PM, Oct 6)
- ✅ Expected completion: 4-5 AM (5-6 hours for 30 seasons)
- ✅ Output: `/tmp/nba_api_comprehensive/`
- ✅ S3 upload: `s3://nba-sim-raw-data-lake/nba_api_comprehensive/`

**Scripts:**
- `scripts/etl/scrape_nba_api_comprehensive.py` - ✅ ACTIVE
- `scripts/etl/overnight_nba_api_comprehensive.sh` - ✅ RUNNING

**Cost:** $0/month (free, rate-limited)

---

### 3. Kaggle Basketball Database (Verification Source #2)

**Status:** 🔄 PENDING IMPLEMENTATION

**Source:** https://www.kaggle.com/datasets/wyattowalsh/basketball/data

**Description:**
Comprehensive SQLite database with NBA data from 1946-present. Includes games, players, teams, and advanced statistics.

**Database Schema:**
- `game` - Game results and metadata
- `team` - Team information
- `player` - Player profiles
- `team_game_stats` - Team statistics per game
- `player_game_stats` - Player statistics per game
- And more (see Kaggle page for full schema)

**Coverage:**
- Date range: 1946-2024 (historical completeness)
- Update frequency: Monthly/seasonal updates
- Data quality: High (community-maintained)

**Access Method:**
1. Download SQLite database from Kaggle (requires Kaggle account)
2. Load into RDS or query locally
3. Extract specific tables/fields
4. Upload to S3 for processing

**Use Cases:**
- Historical data validation (pre-1999)
- Fill gaps in ESPN data
- Advanced statistics not in ESPN
- Player/team metadata enrichment

**Implementation Notes:**
- One-time download (~2-5 GB database)
- Can be queried directly with SQL
- Update periodically (monthly)

**Scripts:**
- `scripts/etl/download_kaggle_database.py` - ⏸️ TO BE CREATED
- `scripts/etl/extract_kaggle_data.py` - ⏸️ TO BE CREATED

**Cost:** $0/month (free download)

---

### 4. SportsDataverse (Verification Source #3)

**Status:** 🔄 PENDING IMPLEMENTATION

**Source:** https://www.sportsdataverse.org/

**Description:**
Open-source sports data aggregator with R and Python packages. Provides unified access to multiple sports APIs.

**Python Package:** `sportsdataverse`

**Installation:**
```bash
pip install sportsdataverse
```

**Key Functions:**
```python
from sportsdataverse.nba import nba_schedule, nba_pbp, nba_player_box

# Get schedule
schedule = nba_schedule.espn_nba_schedule(season=2024)

# Get play-by-play
pbp = nba_pbp.espn_nba_pbp(game_id='401234567')

# Get box scores
box = nba_player_box.espn_nba_player_box(game_id='401234567')
```

**Coverage:**
- Date range: Varies by data type (typically 2002-present)
- Data sources: ESPN, NBA.com, other APIs
- Update frequency: Real-time

**Use Cases:**
- Unified API for multiple sources
- Cross-validation with ESPN
- Alternative download method
- Multi-sport expansion (NFL, MLB, NHL, CFB)

**Implementation Notes:**
- Wrapper around ESPN and other APIs
- May have same limitations as direct ESPN scraping
- Good for prototyping and testing
- Consider for multi-sport replication

**Scripts:**
- `scripts/etl/scrape_sportsdataverse.py` - ⏸️ TO BE CREATED

**Cost:** $0/month (free, open-source)

---

### 5. Basketball Reference (Verification Source #4)

**Status:** 🔄 PENDING IMPLEMENTATION

**Source:** https://www.basketball-reference.com/

**Description:**
Comprehensive historical basketball statistics site. Most complete source for historical NBA data.

**Coverage:**
- Date range: 1946-present (BAA/NBA history)
- Data quality: Highest (gold standard for historical stats)
- Update frequency: Real-time during season

**Data Available:**
- Game logs (box scores)
- Player statistics (career, season, game)
- Team statistics
- Advanced metrics (PER, WS, BPM, etc.)
- Shot charts (recent seasons)
- Playoff data
- All-Star games

**Access Method:**
- HTML scraping (no official API)
- Structured HTML tables (easy to parse)
- Respectful rate limiting required

**Terms of Service:**
- No commercial scraping without permission
- Rate limit: 1 request per 3 seconds
- Must identify bot in User-Agent
- Academic/personal use generally acceptable

**Implementation Notes:**
- Use `BeautifulSoup` or `pandas.read_html()`
- Cache responses in S3
- Scrape incrementally (new games only)
- Respect robots.txt

**Use Cases:**
- Historical data validation (1946-1999)
- Advanced statistics not in ESPN
- Player/team career statistics
- Playoff and All-Star data

**Scripts:**
- `scripts/etl/scrape_basketball_reference.py` - ⏸️ TO BE CREATED

**Cost:** $0/month (free, with rate limiting)

---

## Data Source Comparison Matrix

### Basic Feature Comparison

| Feature | ESPN | NBA.com Stats | Kaggle DB | SportsDataverse | Basketball Reference |
|---------|------|---------------|-----------|-----------------|----------------------|
| **Coverage** | 1999-2025 | 1996-present | 1946-2024 | 2002-present | 1946-present |
| **Format** | JSON | JSON | SQLite | Python API | HTML |
| **Cost** | Free | Free | Free | Free | Free |
| **Rate Limit** | None (files) | ~20/min | N/A | Varies | 1/3sec |
| **Official** | Yes | Yes | No | No | No |
| **Real-time** | Yes | Yes | No | Yes | Yes |
| **Play-by-play** | Yes | Yes | Limited | Yes | No |
| **Advanced Stats** | Limited | Yes | Yes | Limited | Yes |
| **Historical** | 1999+ | 1996+ | 1946+ | 2002+ | 1946+ |
| **Reliability** | High | Highest | High | Medium | Highest |

---

### Temporal Data Quality Matrix

**This matrix shows temporal precision capabilities for the NBA Temporal Panel Data System.**

| Data Source | Time Period | Temporal Precision | Wall Clock Timestamps | Birth Dates | Data Quality Flag |
|-------------|-------------|--------------------|-----------------------|-------------|-------------------|
| **NBA Live API** | 2020-2025 (future) | **Millisecond** | ✅ Full ISO8601 | ✅ Day precision | `precision_level: 'millisecond'` |
| **NBA.com Stats API** | 2013-2019 | **Second** | ✅ Unix timestamps | ✅ Day precision | `precision_level: 'second'` |
| **ESPN API** | 1999-2025 | **Minute** | ⚠️ Minute-level only | ✅ Day precision | `precision_level: 'minute'` |
| **Basketball Ref** | 1946-1992 | **Game-level** | ❌ Game date only | ⚠️ Year precision | `precision_level: 'game'` |
| **Kaggle DB** | 1946-2024 | **Game-level** | ❌ Game date only | ⚠️ Varies | `precision_level: 'game'` or `'unknown'` |
| **SportsDataverse** | 2002-present | **Minute** | ⚠️ Minute-level | ✅ Day precision | `precision_level: 'minute'` |
| **hoopR** | 2002-present | **Minute** | ⚠️ Minute-level | ✅ Day precision | `precision_level: 'minute'` |

**Legend:**
- ✅ **Full support** - Data available with high precision
- ⚠️ **Limited support** - Data available but lower precision
- ❌ **Not available** - Data not provided by source

**Quality Flags (stored in database):**
- `'millisecond'` - Timestamp accurate to ±0.001 seconds (future NBA Live API)
- `'second'` - Timestamp accurate to ±1 second (NBA Stats API 2013-2019)
- `'minute'` - Timestamp accurate to ±60 seconds (ESPN, most historical data)
- `'game'` - Only game date available, no intra-game timestamps (pre-1993 data)
- `'unknown'` - Precision unknown or inconsistent

**Temporal Data Availability by Era:**

| Era | Best Source | Precision Level | Wall Clock Available | Use Cases |
|-----|-------------|-----------------|----------------------|-----------|
| **2020-2025** | NBA Live API (future) | Millisecond | ✅ Yes | Video sync (30fps), real-time ML, high-frequency analysis |
| **2013-2019** | NBA.com Stats API | Second | ✅ Yes | Temporal queries, snapshot analysis, ML features |
| **1999-2012** | ESPN API | Minute | ⚠️ Minute-level | General temporal queries, trend analysis |
| **1946-1998** | Basketball Reference | Game-level | ❌ Date only | Career aggregates, seasonal trends, historical analysis |

**Birth Date Precision by Source:**

| Source | Birth Date Format | Example | Age Calculation Accuracy | Database Flag |
|--------|-------------------|---------|--------------------------|---------------|
| **NBA.com Stats** | YYYY-MM-DD | `1978-08-23` | ±1 day | `birth_date_precision: 'day'` |
| **Basketball Ref** | YYYY-MM-DD (modern) | `1978-08-23` | ±1 day | `birth_date_precision: 'day'` |
| **Basketball Ref** | YYYY-MM (historical) | `1960-03` | ±15 days | `birth_date_precision: 'month'` |
| **Basketball Ref** | YYYY (very old) | `1945` | ±6 months | `birth_date_precision: 'year'` |
| **ESPN API** | Not provided | N/A | N/A | `birth_date_precision: 'unknown'` |

**Data Quality Recommendations:**

1. **For millisecond-precision queries:**
   - Filter: `WHERE precision_level = 'millisecond' AND wall_clock_utc >= '2020-01-01'`
   - Source: NBA Live API (future implementation)
   - Use case: Video frame synchronization, real-time tracking

2. **For second-precision queries:**
   - Filter: `WHERE precision_level IN ('millisecond', 'second') AND wall_clock_utc >= '2013-01-01'`
   - Source: NBA.com Stats API
   - Use case: Temporal snapshots, ML feature engineering

3. **For minute-precision queries:**
   - Filter: `WHERE precision_level IN ('millisecond', 'second', 'minute')`
   - Source: ESPN API + NBA.com Stats
   - Use case: General temporal analysis, trend detection

4. **For game-level analysis:**
   - Filter: `WHERE precision_level != 'unknown'`
   - Source: All sources
   - Use case: Career statistics, historical comparisons

**Cross-Source Validation Strategy:**

| Validation Type | Primary Source | Verification Source | Discrepancy Resolution |
|-----------------|----------------|---------------------|------------------------|
| **Timestamps (2013+)** | NBA.com Stats (second) | ESPN (minute) | Use NBA.com Stats (higher precision) |
| **Timestamps (1999-2012)** | ESPN (minute) | SportsDataverse (minute) | Cross-validate, flag conflicts |
| **Birth Dates** | NBA.com Stats | Basketball Reference | Use Basketball Ref if NBA.com missing |
| **Game Scores** | ESPN | NBA.com Stats | Flag if differ, manual review |
| **Historical (pre-1999)** | Basketball Reference | Kaggle DB | Cross-validate, prefer Basketball Ref |

**Implementation Notes:**

- Store `precision_level` and `data_source` with every `temporal_events` row
- Store `birth_date_precision` in `player_biographical` table
- Create `data_quality_log` table for cross-source discrepancies
- Use precision flags in queries to filter by confidence level
- Document precision limitations in query results

**See also:**
- `docs/adr/009-temporal-panel-data-architecture.md` - Temporal architecture decisions
- `docs/TEMPORAL_QUERY_GUIDE.md` - Query examples with precision filtering
- `docs/phases/PHASE_3_DATABASE.md` Sub-Phase 3.5 - Temporal table schemas

---

## Multi-Source Strategy

### Data Flow

```
1. Primary Source (ESPN)
   ↓
2. Upload to S3
   ↓
3. Extract to RDS (Phase 2)
   ↓
4. Verification (Phases to be created)
   ├─→ NBA.com Stats (scores, official IDs)
   ├─→ Kaggle DB (historical validation)
   ├─→ SportsDataverse (cross-check)
   └─→ Basketball Reference (advanced stats)
   ↓
5. Discrepancy Resolution
   ├─→ Flag conflicts
   ├─→ Log to database table
   └─→ Manual review or auto-fix
   ↓
6. Final Clean Dataset
```

### Verification Workflow

**For each game in RDS:**

1. **Check completeness:**
   - All required fields present?
   - Game date valid?
   - Scores > 0?

2. **Cross-validate with NBA.com Stats:**
   - Scores match?
   - Date/time match?
   - Team IDs match?

3. **Fill gaps from other sources:**
   - Missing advanced stats → Basketball Reference
   - Historical games (pre-1999) → Kaggle DB or Basketball Reference
   - Player metadata → SportsDataverse

4. **Log discrepancies:**
   - Create `data_quality_log` table in RDS
   - Store: game_id, field, source1_value, source2_value, severity, resolved

5. **Auto-fix or manual review:**
   - Low severity: Auto-fix (e.g., formatting)
   - Medium severity: Flag for review
   - High severity: Block game from use until resolved

---

## Implementation Roadmap

### Phase 1: ESPN Scraper (Current)
- ✅ Create scraper for missing data (2022-2025)
- ⏸️ Run scraper and upload to S3
- ⏸️ Extract to RDS

### Phase 2: NBA.com Stats Verification
- ⏸️ Create NBA.com Stats scraper
- ⏸️ Scrape subset for verification (2022-2025)
- ⏸️ Compare ESPN vs NBA.com Stats
- ⏸️ Log discrepancies

### Phase 3: Historical Gap Filling
- ⏸️ Download Kaggle database
- ⏸️ Extract pre-1999 games
- ⏸️ Upload to S3 and RDS

### Phase 4: SportsDataverse Integration
- ⏸️ Install sportsdataverse package
- ⏸️ Test API for alternative downloads
- ⏸️ Use for spot-checking

### Phase 5: Basketball Reference
- ⏸️ Create Basketball Reference scraper
- ⏸️ Scrape advanced statistics
- ⏸️ Merge with RDS data

---

## Scripts Summary

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/etl/scrape_missing_espn_data.py` | ESPN scraper (2022-2025) | ✅ CREATED |
| `scripts/etl/run_espn_scraper.sh` | ESPN scraper wrapper | ✅ CREATED |
| `scripts/etl/scrape_nba_stats_api.py` | NBA.com Stats scraper | ⏸️ PENDING |
| `scripts/etl/download_kaggle_database.py` | Kaggle DB downloader | ⏸️ PENDING |
| `scripts/etl/extract_kaggle_data.py` | Kaggle DB extractor | ⏸️ PENDING |
| `scripts/etl/scrape_sportsdataverse.py` | SportsDataverse scraper | ⏸️ PENDING |
| `scripts/etl/scrape_basketball_reference.py` | Basketball Reference scraper | ⏸️ PENDING |
| `scripts/etl/verify_data_quality.py` | Cross-source validation | ⏸️ PENDING |

---

## Cost Summary

| Source | Monthly Cost | Notes |
|--------|--------------|-------|
| ESPN | $0 | Free API (already in S3) |
| NBA.com Stats | $0 | Free (rate-limited) |
| Kaggle DB | $0 | One-time download |
| SportsDataverse | $0 | Open-source |
| Basketball Reference | $0 | Free (rate-limited) |
| **Total** | **$0/month** | All sources free |

**AWS Costs:**
- S3 storage for scraped data: ~$1-2/month
- Lambda for automated scraping: ~$0-1/month
- **Total AWS cost:** ~$1-3/month

---

## Next Steps

1. ✅ Complete ESPN scraper
2. ⏸️ Run ESPN scraper for 2022-2025
3. ⏸️ Create NBA.com Stats scraper
4. ⏸️ Create Kaggle DB extractor
5. ⏸️ Create SportsDataverse scraper
6. ⏸️ Create Basketball Reference scraper
7. ⏸️ Implement verification workflow

---

*For implementation details, see individual phase files and scripts.*
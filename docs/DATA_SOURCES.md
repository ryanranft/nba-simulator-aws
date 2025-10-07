# NBA Data Sources - Multi-Source Strategy

**Last Updated:** October 4, 2025
**Status:** Active - 5 sources configured

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

**Status:** 🔄 PENDING IMPLEMENTATION

**API Type:** Unofficial (reverse-engineered)

**Base URL:** `https://stats.nba.com/stats/`

**Key Endpoints:**
- `scoreboardV2` - Daily games and scores
- `boxscoretraditionalv2` - Box scores
- `playbyplayv2` - Play-by-play data
- `leaguegamefinder` - Historical game search
- `commonteamroster` - Team rosters
- `commonplayerinfo` - Player information

**Coverage:**
- Date range: 1996-present (official NBA data)
- Data quality: 100% (official source)
- Update frequency: Real-time during games

**Authentication:**
- No API key required
- Requires User-Agent header
- Rate limit: ~10-20 requests/minute (unofficial)

**Use Cases:**
- Verify game scores against ESPN
- Cross-check player statistics
- Official team and player IDs
- Advanced statistics (TS%, eFG%, etc.)

**Implementation Notes:**
- Use exponential backoff for rate limiting
- Store responses in S3 for caching
- Primary use: Validation, not bulk download

**Scripts:**
- `scripts/etl/scrape_nba_stats_api.py` - ⏸️ TO BE CREATED

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
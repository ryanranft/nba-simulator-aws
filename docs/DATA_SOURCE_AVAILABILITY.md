# Data Source Availability - Complete Historical Coverage Analysis

**Created:** October 6, 2025
**Purpose:** Document maximum available historical coverage from each data source
**Status:** Research complete - actionable recommendations provided

---

## Executive Summary

### Maximum Available Coverage by Source:

| Source | Earliest Year | Latest Year | Total Years | Data Quality |
|--------|--------------|-------------|-------------|--------------|
| **Basketball Reference** | **1946** (BAA) | 2025 | **79 years** | Variable by era |
| **NBA.com Stats API** | **1996** | 2025 | **30 years** | Consistent (official) |
| **ESPN** (you have) | **1993** | 2025 | **33 years** | 83% complete |

### Your Current Scraping Plan:

| Scraper | Coverage | Status | Optimal? |
|---------|----------|--------|----------|
| overnight_scrape.sh | 2016-2025 (10 yrs) | 🔄 Running | ✅ Good for recent |
| remainder_scrape.sh | 1993-2015 (23 yrs) | 🔄 Running | ⚠️ Missing 1946-1992 |

**Opportunity:** Basketball Reference has **46 additional years** (1946-1992) available!

---

## Basketball Reference - Detailed Coverage

### Historical Data Availability: **1946-2025 (79 years)**

Basketball Reference provides comprehensive data going back to the founding of professional basketball:

#### **Era 1: BAA/Early NBA (1946-1983)**
- **Coverage:** 1946-47 season through 1982-83
- **Available stats:**
  - Basic box scores: Points, FG, FT, Assists (complete)
  - Team standings and records (complete)
  - Basic player statistics (complete)
  - Advanced stats: **LIMITED** (calculated retroactively)
- **Limitations:**
  - No 3-point shooting stats (3-point line introduced 1979-80)
  - No steals/blocks (not recorded until 1973-74)
  - No offensive/defensive rebounds separate (not recorded until 1973-74)
  - Advanced metrics (TS%, PER, BPM) calculated from available data but less accurate

#### **Era 2: Complete Box Scores (1983-1996)**
- **Coverage:** 1983-84 season through 1995-96
- **Available stats:**
  - Complete box scores (all traditional stats)
  - Offensive/Defensive Ratings
  - True Shooting % (TS%)
  - Effective Field Goal % (eFG%)
  - Pace and Four Factors
  - Advanced team metrics
- **Limitations:**
  - Play-by-play data: **NOT AVAILABLE**
  - Shot location data: **NOT AVAILABLE**
  - Lineup data: **NOT AVAILABLE**
  - Some advanced player metrics calculated retroactively

#### **Era 3: Modern Analytics (1996-2025)**
- **Coverage:** 1996-97 season through 2024-25
- **Available stats:**
  - **ALL** traditional and advanced stats
  - Play-by-play data (complete)
  - Shot location and type
  - Lineup data (from 2007-08 forward)
  - Player Efficiency Rating (PER)
  - Box Plus/Minus (BPM)
  - Win Shares (WS)
  - Usage Rate
  - Value Over Replacement Player (VORP)
- **Quality:** Highest completeness and accuracy

---

## NBA.com Stats API - Detailed Coverage

### Historical Data Availability: **1996-2025 (30 years)**

NBA.com's official Stats API (stats.nba.com) has strict data availability limits:

#### **Hard Start Date: October 1996 (1996-97 season)**
- **Reason:** NBA digitization project began 1996-97 season
- **Before 1996:** API returns no data or empty responses
- **Quality:** Official NBA data, highest accuracy for available years

#### **Available Endpoints and Coverage:**

**Basic Endpoints (1996-present):**
- `scoreboardV2` - Daily games and scores
- `boxscoretraditionalv2` - Complete box scores
- `playbyplayv2` - Play-by-play sequences

**Advanced Endpoints (Variable start dates):**
- `leaguedashplayerstats` - 1996-present
- `leaguedashteamstats` - 1996-present
- `hustlestatsboxscore` - **2015-present** (hustle stats introduced)
- `trackingdefense` - **2013-present** (player tracking cameras)
- `trackingspeed` - **2013-present** (player tracking cameras)
- Lineup data - **2007-present**

#### **Key Limitations:**
- No data before 1996-97 season
- Tracking stats (hustle, defensive, speed) only from 2013-14 forward
- API rate limiting: ~10-20 requests/minute (unofficial)
- No historical data reconstruction for pre-1996 seasons

---

## ESPN - Your Existing Coverage

### Historical Data Availability: **1993-2025 (33 years)**

**What you have in PostgreSQL:**
- **Earliest game:** November 6, 1993
- **Latest game:** April 13, 2025
- **Total games:** 44,828 games
- **Quality:** 83% valid files (17% empty/future games)

**Feature set:**
- 58 features per game
- Complete box scores (player and team)
- Play-by-play sequences
- Game metadata (venue, attendance, officials)

**Gap analysis:**
- **Missing 1946-1992:** 46 years not in ESPN data
- **Missing 1993-1995:** Could enhance with Basketball Reference

---

## Opportunity Analysis

### Option 1: Match ESPN Coverage (Current Plan) ✅

**Scraping:**
- Basketball Reference: 1993-2025 (33 years)
- NBA.com Stats: 1996-2025 (30 years)

**Result:**
- 1993-1995: ESPN (58) + Basketball Reference (47) = **105 features**
- 1996-2025: ESPN (58) + Basketball Reference (47) + NBA.com (92) = **209 features**
- **ML-ready years:** 30 years with 209 features

**Status:** ✅ Already running (overnight_scrape.sh + remainder_scrape.sh)

---

### Option 2: Maximum Basketball Reference Coverage (Recommended) 🎯

**Add historical scraping:**
- Basketball Reference: **1946-1992** (46 additional years)

**What you'd gain:**
- **79 total years** of Basketball Reference data (1946-2025)
- Historical context for ML models (championship eras, rule changes)
- Feature engineering across different NBA eras
- Robustness testing across vastly different play styles

**Limitations:**
- Advanced stats quality decreases before 1984
- No play-by-play before 1997
- No shot location before 1997
- 3-point shooting only from 1979 forward
- Steals/blocks only from 1973 forward

**Estimated scraping time:**
- 46 seasons × 3 requests × 3.5 sec = **~8 minutes**

**Use cases:**
- Historical analysis and visualization
- Long-term trend analysis
- Era-adjusted player comparisons
- Rule change impact studies
- Training ML models on feature subsets

---

## Recommended Action Plan

### Phase 1: Complete Current Scraping ✅
- Let overnight_scrape.sh finish (2016-2025)
- Let remainder_scrape.sh finish (1993-2015)
- **Result:** Full 1993-2025 coverage across all 3 sources

### Phase 2: Add Historical Basketball Reference (Optional)
- Create `historical_bref_scrape.sh` for 1946-1992
- Run when convenient (~8 minutes)
- **Result:** 79 years of Basketball Reference data

### Phase 3: Feature Engineering Strategy

**Tier 1 Features (1996-2025, 30 years):**
- All 209 features available
- Maximum ML model accuracy
- Primary training dataset

**Tier 2 Features (1993-1995, 3 years):**
- 105 features (ESPN + Basketball Reference)
- Test data or supplementary training

**Tier 3 Features (1946-1992, 46 years - if scraped):**
- Variable feature count (basic stats only)
- Historical analysis and visualization
- Feature subset ML experiments

---

## Implementation Recommendations

### 1. For Maximum ML Accuracy: ✅ Current Plan
- Focus on 1996-2025 (30 years, 209 features)
- This is what you're already scraping

### 2. For Historical Completeness: Add 1946-1992
- Scrape Basketball Reference back to 1946
- Use for visualization, historical analysis, trend studies
- Create feature subsets for different eras

### 3. For Both: Recommended
- Keep current scrapers running (1993-2025)
- Add historical scraper (1946-1992) tomorrow
- Total Basketball Reference coverage: 79 years
- ML training: 30 years (1996-2025) with 209 features
- Historical analysis: Full 79 years with variable features

---

## Data Quality Matrix

| Year Range | ESPN | Basketball Ref | NBA.com Stats | Total Features | Best Use |
|------------|------|---------------|---------------|----------------|----------|
| 1946-1992 | ❌ | ✅ Basic | ❌ | 30-47 | Historical viz |
| 1993-1995 | ✅ | ✅ | ❌ | 105 | Supplementary |
| 1996-2015 | ✅ | ✅ | ✅ | 209 | Primary ML |
| 2016-2025 | ✅ | ✅ | ✅ | 209 | Primary ML |

**Legend:**
- ✅ = Full data available
- ⚠️ = Partial/limited data
- ❌ = No data available

---

## Cost Impact

### Current Scraping (1993-2025):
- Basketball Reference: ~6 min (33 seasons)
- NBA.com Stats: ~12 hours (30 seasons)
- **Total time:** ~12 hours
- **S3 cost:** Negligible (+$0.10/month for additional files)

### Adding Historical (1946-1992):
- Basketball Reference: ~8 min (46 seasons)
- **Total time:** 8 minutes
- **S3 cost:** Negligible (+$0.05/month)

**Total impact:** ~$0.15/month S3 storage, 8 additional minutes

---

## Conclusion

**Current scrapers are optimal for ML training** (1993-2025 coverage).

**Opportunity exists** to scrape Basketball Reference back to 1946 for:
- Historical analysis
- Visualization dashboards
- Era comparison studies
- Comprehensive NBA dataset

**Recommendation:**
1. ✅ Complete current scraping (already running)
2. 🎯 Add 1946-1992 Basketball Reference scraping tomorrow (8 minutes)
3. 📊 Use 1996-2025 (209 features) for ML, full 1946-2025 for historical analysis

---

**Last Updated:** October 6, 2025
**Research Sources:** Basketball-Reference.com, NBA.com Stats API documentation, nba_api GitHub
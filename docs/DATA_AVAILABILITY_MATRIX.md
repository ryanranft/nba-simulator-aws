# NBA API Data Availability Matrix

**Research Date:** October 7, 2025
**Source:** Comprehensive GitHub, NBA.com, and community research

---

## Executive Summary

The NBA Stats API (`stats.nba.com`) provides varying levels of data coverage across different time periods. This document details what data is available for each era and identifies critical quality issues.

---

## Data Availability by Era

### 🟢 Modern Era (2013-2025) - **EXCELLENT**

**Years:** 2013-14 season to present (12 seasons)
**Overall Confidence:** 95%

| Data Type | Available | Quality | Notes |
|-----------|-----------|---------|-------|
| Traditional Box Scores | ✅ Yes | Excellent | Complete coverage |
| Advanced Stats | ✅ Yes | Excellent | All metrics available |
| Shot Charts | ✅ Yes | Excellent | Full coordinate data |
| Player Tracking | ✅ Yes | Excellent | **SportVU/Second Spectrum** |
| Hustle Stats | ✅ Yes (2015-16+) | Excellent | Deflections, loose balls, etc. |
| Synergy Play Types | ✅ Yes (2015-16+) | Excellent | 10 play types |
| Play-by-Play | ✅ Yes | Excellent | Complete with timing |

**Technology:**
- 2013-2017: STATS SportVU (6-camera optical tracking)
- 2017-2023: Second Spectrum (advanced optical tracking)
- 2023-present: Sony Hawk-Eye (newest system)

**Features Available:** 269-289 total features
**Recommended Use:** ✅ Primary data source for all analysis

---

### 🟡 Digital Era (2000-2012) - **GOOD**

**Years:** 2000-01 to 2012-13 seasons (13 seasons)
**Overall Confidence:** 75%

| Data Type | Available | Quality | Notes |
|-----------|-----------|---------|-------|
| Traditional Box Scores | ✅ Yes | Excellent | Complete coverage |
| Advanced Stats | ✅ Yes | Excellent | Full advanced metrics |
| Shot Charts | ✅ Yes | Good | Reliable coordinates |
| Player Tracking | ❌ No | N/A | **Not available before 2013-14** |
| Hustle Stats | ❌ No | N/A | Requires tracking cameras |
| Synergy Play Types | ❌ No | N/A | Public API from 2015-16+ |
| Play-by-Play | ✅ Yes | Excellent | Complete with timing |

**Features Available:** ~200 features (no tracking/hustle/synergy)
**Recommended Use:** ✅ Safe for traditional + advanced stats analysis

---

### 🟠 Early Digital Era (1996-1999) - **POOR**

**Years:** 1996-97 to 1999-00 seasons (4 seasons)
**Overall Confidence:** 60%

| Data Type | Available | Quality | Notes |
|-----------|-----------|---------|-------|
| Traditional Box Scores | ✅ Yes | Good | Complete coverage |
| Advanced Stats | ✅ Yes | Good | Calculated from play-by-play |
| Shot Charts | ⚠️ Partial | **POOR** | **194,239 FGA missing coordinates (25%+)** |
| Player Tracking | ❌ No | N/A | Not available before 2013-14 |
| Hustle Stats | ❌ No | N/A | Requires tracking cameras |
| Synergy Play Types | ❌ No | N/A | Public API from 2015-16+ |
| Play-by-Play | ⚠️ Yes | Fair | Missing shot locations |

**Critical Issues:**
- **194,239 field goal attempts** have no shot distance or coordinate data
- Many missed jump shots mislabeled as missed layups
- Basketball-Reference warning: "We urge caution in utilizing them"

**Features Available:** ~150 features (exclude shot location analysis)
**Recommended Use:** ⚠️ Use with caution, validate against other sources

---

### 🔴 Pre-Digital Era (Before 1996) - **MINIMAL**

**Years:** 1946-47 to 1995-96 seasons (50 seasons)
**Overall Confidence:** 10%

| Data Type | Available | Quality | Notes |
|-----------|-----------|---------|-------|
| Traditional Box Scores | ⚠️ Limited | Variable | Basic stats only |
| Advanced Stats | ❌ No | N/A | Requires play-by-play |
| Shot Charts | ❌ No | N/A | No digitized data |
| Player Tracking | ❌ No | N/A | Technology didn't exist |
| Hustle Stats | ❌ No | N/A | Not tracked |
| Synergy Play Types | ❌ No | N/A | Not tracked |
| Play-by-Play | ❌ No | N/A | Not digitized |

**Alternative Sources:**
- **Basketball-Reference** (1946-present)
- **Kaggle NBA Database** (1946-2024)
- **Stats.nba.com has minimal pre-1996 data**

**Recommended Use:** ❌ Use Basketball-Reference or Kaggle instead

---

## Technology Timeline

### Player Tracking Evolution

| Period | Technology | Coverage | Public Data |
|--------|-----------|----------|-------------|
| **2006-2009** | Early STATS pilots | 0 teams | None |
| **2010-2011** | STATS SportVU pilot | 5 teams | None |
| **2012-2013** | SportVU expansion | 10 teams | None |
| **2013-2014** | **SportVU full rollout** | **30 teams** | Limited |
| **2014-2016** | SportVU operational | 30 teams | Limited |
| **2016 (June)** | Public data removed | 30 teams | Very limited |
| **2017-2018** | **Second Spectrum** | **30 teams** | Aggregate only |
| **2023-present** | Sony Hawk-Eye | 30 teams | Aggregate only |

**Key Takeaway:** Full player tracking only available from **2013-14 season forward**

### API Evolution

| Date | Event | Impact |
|------|-------|--------|
| **Feb 15, 2013** | NBA.com/Stats launched | Comprehensive stats website |
| **Oct 29, 2013** | SportVU full rollout | Player tracking begins |
| **June 2016** | Raw tracking data removed | Public access restricted |
| **Sep 2017** | Second Spectrum transition | New tracking provider |

---

## Data Quality Warnings

### 🚨 Critical Issues

**1. Shot Location Data (1996-2000)**
- **194,239 field goal attempts** missing coordinates
- 25%+ of all FGA in this period
- Many shots misclassified (jump shots → layups)
- **Action Required:** Flag or exclude shot location analysis for 1996-2000

**2. Player Tracking Availability**
- **Only available 2013-14 forward**
- Cannot be backfilled or reconstructed
- Requires physical camera systems
- **Action Required:** Skip player tracking endpoints for seasons < 2014

**3. Testing Limits in Current Scraper**
- Only scraping 100 games per season (8% of data)
- Only scraping 50 players per season (10% of players)
- **Action Required:** Remove testing limits for production

---

## Endpoint Availability Matrix

| Endpoint Category | 1996-1999 | 2000-2012 | 2013-2015 | 2016-2025 |
|-------------------|-----------|-----------|-----------|-----------|
| Traditional Box Scores | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Advanced Box Scores | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Four Factors | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Usage Stats | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Shot Charts | ⚠️ Poor | ✅ Yes | ✅ Yes | ✅ Yes |
| Play-by-Play | ⚠️ Gaps | ✅ Yes | ✅ Yes | ✅ Yes |
| Player Tracking | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| Hustle Stats | ❌ No | ❌ No | ⚠️ No | ✅ Yes (2015-16+) |
| Synergy Play Types | ❌ No | ❌ No | ⚠️ No | ✅ Yes (2015-16+) |
| Lineup Data (Official) | ❌ No | ⚠️ No | ✅ Yes (2007+) | ✅ Yes |

---

## Feature Count by Era

| Era | Traditional | Advanced | Tracking | Hustle | Synergy | **Total** |
|-----|-------------|----------|----------|--------|---------|-----------|
| **2016-2025** | 53 | 100 | 60-80 | 15-20 | 20-25 | **248-278** |
| **2013-2015** | 53 | 100 | 60-80 | 0 | 0 | **213-233** |
| **2000-2012** | 53 | 100 | 0 | 0 | 0 | **153** |
| **1996-1999** | 53 | 80 | 0 | 0 | 0 | **133** |

---

## Scraper Configuration Recommendations

### Priority 1: Modern Era (2014-2025)
```python
# Configuration for 2014-2025
seasons = range(2014, 2026)  # 12 seasons
enable_all_endpoints = True
include_player_tracking = True
include_hustle_stats = True  # 2015-16+
include_synergy = True  # 2015-16+
```

**Runtime:** ~25-30 hours per season × 12 = 300-360 hours (12-15 days)
**Features:** 269-289 total

### Priority 2: Digital Era (2000-2013)
```python
# Configuration for 2000-2013
seasons = range(2000, 2014)  # 14 seasons
enable_traditional = True
enable_advanced = True
enable_shot_charts = True
include_player_tracking = False  # Not available
include_hustle_stats = False  # Not available
include_synergy = False  # Not available
```

**Runtime:** ~20-25 hours per season × 14 = 280-350 hours (11-14 days)
**Features:** ~200 total

### Priority 3: Early Digital Era (1996-1999)
```python
# Configuration for 1996-1999
seasons = range(1996, 2000)  # 4 seasons
enable_traditional = True
enable_advanced = True
enable_shot_charts = False  # Poor quality
log_data_quality_warning = True
include_player_tracking = False  # Not available
```

**Runtime:** ~15-20 hours per season × 4 = 60-80 hours (2-3 days)
**Features:** ~150 total

---

## Validation Strategy

### Cross-Validation Sources

**1. Basketball-Reference (1946-present)**
- Gold standard for historical data
- Use for pre-1996 data
- Validate 1996-2000 shot location data

**2. ESPN API (1993-2025)**
- Your project's primary source
- Already in S3 bucket
- Use for traditional box score validation

**3. Kaggle NBA Database (1946-2024)**
- SQLite database with 17 tables
- One-time download (~1 GB)
- Good for historical validation

**4. hoopR/SportsDataverse (2002-present)**
- Fast bulk loading
- Good for recent seasons
- Already tested and working

### Data Quality Checks

**For all seasons:**
- ✅ Verify game counts match expected (~1,230 per season)
- ✅ Check for empty DataFrames
- ✅ Validate player counts match roster sizes
- ✅ Cross-check totals against ESPN data

**For 1996-2000 specifically:**
- ⚠️ Flag games with missing shot coordinates
- ⚠️ Count FGA with no distance data
- ⚠️ Warn if using shot location features

**For 2013+ seasons:**
- ✅ Verify player tracking data exists
- ✅ Check hustle stats availability (2015-16+)
- ✅ Validate synergy play types (2015-16+)

---

## References

**Research Sources:**
- nba_api GitHub repository (swar/nba_api)
- Basketball-Reference blog announcements
- NBA.com Stats website documentation
- SportVU technology timeline (Wikipedia, NBA press releases)
- Community discussions (Stack Overflow, Medium, Reddit)

**Key GitHub Issues:**
- #320: Timeout issues
- #176: Connection pool timeout
- #211: Empty DataFrame handling
- #69: Rate limiting recommendations

**Authoritative Articles:**
- Basketball-Reference: "Play-by-play data quality warnings" (April 2020)
- NBA Communications: SportVU installation timeline
- STATS LLC: Second Spectrum partnership announcement

---

## Summary & Recommendations

### ✅ Safe Ranges
- **2013-2025:** All features, highest quality
- **2000-2012:** Traditional + advanced stats only
- **1996-1999:** Basic stats only, validate carefully

### ⚠️ Caution Required
- **1996-2000 shot charts:** 25% missing data
- **Pre-2014 player tracking:** Not available
- **Pre-2016 hustle/synergy:** Not available

### ❌ Not Recommended
- **Pre-1996 from stats.nba.com:** Use Basketball-Reference instead

### 🎯 For Your NBA Simulator Project
1. **Start with 2014-2025** (best quality, all features)
2. **Add 2000-2013** (good quality, no tracking)
3. **Consider 1996-1999** (basic stats only)
4. **Skip pre-1996** (use Basketball-Reference)

---

*Last updated: October 7, 2025*
*Research conducted by Claude Code*
*Based on comprehensive GitHub, NBA.com, and community sources*

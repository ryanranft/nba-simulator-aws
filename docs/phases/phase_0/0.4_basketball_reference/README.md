# Basketball Reference - Complete Data Collection

**Phase:** 0 (Data Collection)
**Project:** Basketball Reference Complete Expansion (Option C)
**Status:** ⏸️ PENDING
**Total Scope:** 234 data types across 7 basketball domains
**Total Time:** 140-197 hours
**Total Records:** 865K-10.88M records
**Last Updated:** October 11, 2025

---

## Overview

This directory contains the complete implementation plan for collecting ALL basketball data from Basketball Reference across 7 domains:

- **NBA** (National Basketball Association, 1946-2025)
- **WNBA** (Women's National Basketball Association, 1997-2025)
- **G League** (NBA Development League, 2002-2025)
- **ABA** (American Basketball Association, 1967-1976)
- **BAA** (Basketball Association of America, 1946-1949)
- **International** (FIBA, EuroLeague, Olympics, World Cup)
- **College** (NCAA Men's & Women's basketball)

**Implementation approach:** 13 tiers organized by priority, domain, and dependencies.

---

## 13-Tier Structure

| Tier | Domain | Data Types | Records | Time | Priority | Status | File |
|------|--------|------------|---------|------|----------|--------|------|
| 1 | NBA High Value | 5 | 150K | 15-20h | IMMEDIATE | ⏸️ | [TIER_1_NBA_HIGH_VALUE.md](TIER_1_NBA_HIGH_VALUE.md) |
| 2 | NBA Strategic | 4 | 200K | 20-25h | IMMEDIATE | ⏸️ | [TIER_2_NBA_STRATEGIC.md](TIER_2_NBA_STRATEGIC.md) |
| 3 | NBA Historical | 3 | 75K | 10-15h | HIGH | ⏸️ | [TIER_3_NBA_HISTORICAL.md](TIER_3_NBA_HISTORICAL.md) |
| 4 | NBA Performance | 4 | 250K | 15-20h | HIGH | ⏸️ | [TIER_4_NBA_PERFORMANCE.md](TIER_4_NBA_PERFORMANCE.md) |
| 5 | NBA Advanced | 3 | 50K | 8-12h | MEDIUM | ⏸️ | [TIER_5_NBA_ADVANCED.md](TIER_5_NBA_ADVANCED.md) |
| 6 | NBA Comparative | 4 | 100K | 12-15h | MEDIUM | ⏸️ | [TIER_6_NBA_COMPARATIVE.md](TIER_6_NBA_COMPARATIVE.md) |
| 7 | NBA Situational | 4 | 75K | 10-15h | MEDIUM | ⏸️ | [TIER_7_NBA_SITUATIONAL.md](TIER_7_NBA_SITUATIONAL.md) |
| 8 | NBA Complete | 3 | 50K | 8-12h | LOW | ⏸️ | [TIER_8_NBA_COMPLETE.md](TIER_8_NBA_COMPLETE.md) |
| 9 | Historical Leagues | 3 | 15K | 5-8h | LOW | ⏸️ | [TIER_9_HISTORICAL_LEAGUES.md](TIER_9_HISTORICAL_LEAGUES.md) |
| 10 | WNBA Complete | 16 | 100K | 15-20h | EXECUTE | ⏸️ | [TIER_10_WNBA.md](../PHASE_0_TIER_10_WNBA.md) |
| 11 | G League Complete | 10 | 50K | 8-10h | EXECUTE | ⏸️ | [TIER_11_GLEAGUE.md](TIER_11_GLEAGUE.md) |
| 12 | International Select | 40 | 100K | 10-30h | OPTIONAL | ⏸️ | [TIER_12_INTERNATIONAL.md](TIER_12_INTERNATIONAL.md) |
| 13 | College Select | 10 | 200K | 30-40h | OPTIONAL | ⏸️ | [TIER_13_COLLEGE.md](TIER_13_COLLEGE.md) |

**Total:** 109 data types (Tiers 1-11) + 50 optional types (Tiers 12-13) = 159-234 types

---

## Quick Navigation

### By Priority
- **IMMEDIATE (Tiers 1-2):** 35-45 hours, 350K records, 9 types
- **HIGH (Tiers 3-4):** 25-35 hours, 325K records, 7 types
- **MEDIUM (Tiers 5-7):** 30-42 hours, 225K records, 11 types
- **LOW (Tiers 8-9):** 13-20 hours, 65K records, 6 types
- **EXECUTE (Tiers 10-11):** 23-30 hours, 150K records, 26 types
- **OPTIONAL (Tiers 12-13):** 40-70 hours, 300K records, 50 types

### By Domain
- **NBA (Tiers 1-8):** 30 types, 950K records, 98-119 hours
- **Historical Leagues (Tier 9):** 3 types, 15K records, 5-8 hours
- **WNBA (Tier 10):** 16 types, 100K records, 15-20 hours
- **G League (Tier 11):** 10 types, 50K records, 8-10 hours
- **International (Tier 12):** 40 types, 100K records, 10-30 hours
- **College (Tier 13):** 10 types, 200K records, 30-40 hours

---

## Implementation Sequence

**Week 1-8: IMMEDIATE Priority (Tiers 1-2)**
- Focus: High-value NBA data with immediate ML/simulation utility
- Data types: Game logs, play-by-play, shot charts, player tracking, lineups
- Output: 350K records, ready for feature engineering

**Week 9-14: HIGH Priority (Tiers 3-4)**
- Focus: Historical context and performance depth
- Data types: Historical data, awards, playoffs, streaks
- Output: 325K records, enhanced historical analysis

**Week 15-20: MEDIUM Priority (Tiers 5-7)**
- Focus: Advanced analytics and specialized metrics
- Data types: Synergy, hustle, defensive tracking, splits, clutch
- Output: 225K records, advanced feature set

**Week 21-24: LOW Priority (Tiers 8-9)**
- Focus: Completeness and historical leagues
- Data types: Referees, transactions, ABA, BAA
- Output: 65K records, complete NBA/historical context

**Week 25-28: EXECUTE Priority (Tiers 10-11)**
- Focus: Multi-league expansion (WNBA, G League)
- Data types: Complete WNBA and G League datasets
- Output: 150K records, multi-league panel data

**Week 29+: OPTIONAL (Tiers 12-13)**
- Focus: International and college basketball
- Data types: FIBA, EuroLeague, NCAA data
- Output: 300K records, global basketball coverage

---

## File Structure

Each tier file contains:
1. **Overview** - Purpose, data types, time estimate, record count
2. **Sub-Phases** - Detailed breakdown of each data type
3. **Implementation Steps** - Scraper configuration, URL patterns, table IDs
4. **Data Quality Checks** - Validation rules, coverage verification
5. **Success Criteria** - Completion checkboxes
6. **S3 Storage Structure** - Upload paths and file organization
7. **Integration Notes** - Database schemas, ML features

**Target size:** 300-800 lines per tier file

---

## Progress Tracking

**Current Status (October 11, 2025):**
- ✅ Complete data audit: 234 types identified
- ✅ 13-tier structure designed
- ✅ Documentation framework created (Workflow #45)
- ⏸️ Tier files creation: 0 of 13 complete
- ⏸️ Data collection: 0 of 234 types collected
- ⏸️ S3 uploads: 0 KB uploaded

**Next Action:** Create individual tier files (TIER_1 through TIER_13)

---

## Context Budget

**Reading this index:** ~300 lines (1.5% context)

**Reading a single tier file:** ~300-800 lines (1.5-4% context)

**Session startup recommendations:**
- **Quick orientation:** Read this index only (~300 lines)
- **Working on specific tier:** Read index + that tier file (~600-1,100 lines)
- **Planning next phase:** Read index + PROGRESS.md (~985 lines)

**Do NOT read all 13 tier files at once** - would consume 3,900-10,400 lines (20-52% context)

---

## Related Documentation

**Master documents:**
- **PROGRESS.md** - Overall project status and phase tracking
- **docs/data_sources/basketball_reference_COMPLETE_catalog_2025-10-11.md** - Exhaustive data catalog (6,800 lines)

**Implementation guides:**
- **docs/archive/superseded_documentation/PHASE_0_BASKETBALL_REFERENCE_COMPLETE_EXPANSION.md** - Full expansion plan (archived, superseded by 13-tier structure)
- **docs/archive/superseded_documentation/PHASE_0_TIER_10_WNBA.md** - WNBA detailed implementation (archived)
- **docs/archive/superseded_documentation/PHASE_0_TIERS_11_12_13_MULTI_LEAGUE.md** - Multi-league expansion (archived)

**Workflows:**
- **Workflow #45** - Documentation Organization Protocol
- **Workflow #38** - Overnight Scraper Handoff Protocol
- **Workflow #39** - Scraper Monitoring Automation

**Data sources:**
- **docs/DATA_SOURCES.md** - Multi-source data strategy
- **docs/DATA_SOURCE_BASELINES.md** - Verified baselines for cross-validation

---

## Technical Notes

**Rate Limiting:**
- Basketball Reference: 12 seconds between requests
- Sports Reference (college): Different rate limits, verify first

**S3 Storage Structure:**
```
s3://nba-sim-raw-data-lake/basketball_reference/
├── nba/           # Tiers 1-8
├── wnba/          # Tier 10
├── gleague/       # Tier 11
├── aba/           # Tier 9
├── baa/           # Tier 9
├── international/ # Tier 12
└── college/       # Tier 13
```

**Data Quality Standards:**
- Record count validation (±5% of estimate)
- Coverage verification (no missing years)
- JSON structure validation
- Cross-reference checks against catalog

---

## Questions?

**"Which tier should I start with?"**
→ Tier 1 (NBA High Value) unless user specifies otherwise

**"How long will this take?"**
→ 140-197 hours total, 14-37 weeks at 10-20 hours/week

**"Can I skip tiers?"**
→ Yes, but verify prerequisites first (e.g., Tier 4 needs Tier 3 awards data)

**"How do I know when a tier is complete?"**
→ Each tier file has "Success Criteria" checklist at bottom

**"What if I find more data types?"**
→ Update the catalog, add to appropriate tier, notify user

---

**Tier Index Owner:** Data Collection Team
**Last Updated:** October 21, 2025 (Added documentation/ subdirectory)
**Next Review:** When first tier file is created

---

## Additional Documentation

**Location:** [documentation/](documentation/)

Comprehensive technical documentation for Basketball Reference systems:

1. **[BOX_SCORE_SYSTEM.md](documentation/BOX_SCORE_SYSTEM.md)** - Box score data structure and extraction
2. **[COMPARISON.md](documentation/COMPARISON.md)** - Comparison with other data sources (ESPN, NBA API)
3. **[PBP_DISCOVERY.md](documentation/PBP_DISCOVERY.md)** - Play-by-play data discovery process
4. **[PBP_SYSTEM.md](documentation/PBP_SYSTEM.md)** - Play-by-play extraction system
5. **[SCRAPING_NOTES.md](documentation/SCRAPING_NOTES.md)** - Technical scraping notes and best practices
6. **[TEST_PLAN.md](documentation/TEST_PLAN.md)** - Testing strategy and validation
7. **[OVERNIGHT_WORKFLOW_INTEGRATION.md](documentation/OVERNIGHT_WORKFLOW_INTEGRATION.md)** - Autonomous scraping workflows
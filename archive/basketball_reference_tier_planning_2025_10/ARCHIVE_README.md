# Basketball Reference Tier Planning Archive

**Archived:** October 25, 2025
**Reason:** Implementation completed with different scope than originally planned
**Archived By:** Autonomous ADCE Integration Process

---

## What Was Archived

Detailed tier planning documents (TIER_1.md through TIER_13.md) that outlined collection of all 234 Basketball Reference data types across 7 basketball domains.

**Files archived:** 13 tier planning documents
- TIER_1_NBA_HIGH_VALUE.md
- TIER_2_NBA_STRATEGIC.md
- TIER_3_NBA_HISTORICAL.md
- TIER_4_NBA_PERFORMANCE.md
- TIER_5_NBA_ADVANCED.md
- TIER_6_NBA_COMPARATIVE.md
- TIER_7_NBA_SITUATIONAL.md
- TIER_8_NBA_COMPLETE.md
- TIER_9_HISTORICAL_LEAGUES.md
- TIER_10_WNBA.md
- TIER_11_GLEAGUE.md
- TIER_12_INTERNATIONAL.md
- TIER_13_COLLEGE.md

---

## What Was Actually Implemented

**43 data types** via automated extraction and ADCE integration:
- **NBA (Tiers 1-9):** 33 types - Complete modern NBA + historical leagues (ABA/BAA/Early NBA)
- **G League (Tier 11):** 10 types - Complete G League ecosystem (2002-2025)

**Priority Order (Option A):**
1. NBA Modern (Tiers 1-4): 16 types → 3-4 weeks
2. NBA Advanced (Tiers 5-8): 14 types → 2-3 weeks
3. Historical Leagues (Tier 9): 3 types (ABA/BAA) → 1 week
4. G League (Tier 11): 10 types → 1 week

**Total:** 6-9 weeks autonomous 24/7 collection

---

## Why Different From Plan

The automated extraction process (`extract_bbref_data_types.py` and `generate_bbref_scrapers.py`) focused on currently available and high-value data types rather than the complete 234-type catalog originally envisioned.

**Strategic decision:** Prioritize NBA + G League (highest ML/simulation value) to avoid rate limiting on initial deployment.

---

## What Was NOT Implemented (Future Expansion)

These data types were identified in the original tier planning but NOT included in the automated extraction:

- **Tier 10 (WNBA):** 16 types - Complete WNBA data (1997-2025)
- **Tier 12 (International):** 40 types - FIBA, EuroLeague, Olympics, World Cup
- **Tier 13 (NCAA):** 10 types - NCAA Men's & Women's basketball

**Future addition:** Can be integrated using the same extraction/configuration pipeline when ready (estimated 2-3 hours additional work per tier).

---

## Current Documentation

**Primary documentation:**
- **Main README:** [docs/phases/phase_0/0.4_basketball_reference/README.md](../../docs/phases/phase_0/0.4_basketball_reference/README.md)
- **Deployment Guide:** [BASKETBALL_REFERENCE_ADCE_DEPLOYMENT.md](../../BASKETBALL_REFERENCE_ADCE_DEPLOYMENT.md)
- **Data Catalog:** [config/basketball_reference_data_types_catalog.json](../../config/basketball_reference_data_types_catalog.json)
- **Scraper Config:** [config/basketball_reference_scrapers.yaml](../../config/basketball_reference_scrapers.yaml)

**Testing:**
- **Test Suite:** [tests/test_basketball_reference_comprehensive.py](../../tests/test_basketball_reference_comprehensive.py)
- **Results:** 9/9 tests passing (100% success rate)

---

## Why Archive Instead of Delete

These tier planning documents contain valuable research and planning that may be useful for:
1. Future expansion to WNBA/NCAA/International data
2. Understanding the original vision and scope
3. Reference for data type identification and categorization
4. Historical record of planning decisions

---

## How to Use This Archive

**If you need to implement WNBA/NCAA/International:**
1. Review the corresponding TIER_*.md file for data type details
2. Run extraction/configuration scripts with those tiers included
3. Follow the same ADCE integration pattern used for NBA + G League

**If you're maintaining the current system:**
- Ignore these files - they're superseded by current documentation
- Refer to primary documentation links above instead

---

**Archived Date:** October 25, 2025
**Archived From:** docs/phases/phase_0/0.4_basketball_reference/
**Archive Location:** archive/basketball_reference_tier_planning_2025_10/
**Status:** Superseded by ADCE integration (Option A - NBA + G League focus)

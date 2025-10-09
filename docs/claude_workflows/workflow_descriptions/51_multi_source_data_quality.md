# Workflow #51: Multi-Source Data Quality Validation

**Version:** 1.0
**Created:** October 9, 2025
**Status:** Active
**Frequency:** Run for each new data source pair

## Purpose

Validate data quality across multiple independent NBA data sources while maintaining data integrity. This workflow ensures each source database remains pure (no cross-contamination) while building a comprehensive unified database that tracks discrepancies for machine learning.

## Critical Principles

### ⚠️ NEVER Cross-Contaminate Data Sources

**Rule:** Each source database contains ONLY data from that source.

**Why:**
- Multi-source validation requires independent observations
- Cross-contamination hides discrepancies
- ML models need to know true data quality
- Can't determine which source is more reliable if they're mixed

**See:** `docs/DATA_INTEGRITY_PRINCIPLES.md`

## Workflow Overview

```
┌─────────────┐
│  Phase 1    │ Gap Detection (identify missing games)
└──────┬──────┘
       │
┌──────▼──────┐
│  Phase 2    │ Scrape from ORIGINAL Source Only
└──────┬──────┘
       │
┌──────▼──────┐
│  Phase 3    │ Load to Source Database (keep pure)
└──────┬──────┘
       │
┌──────▼──────┐
│  Phase 4    │ Build Unified Database
└──────┬──────┘
       │
┌──────▼──────┐
│  Phase 5    │ Document Discrepancies
└──────┬──────┘
       │
┌──────▼──────┐
│  Phase 6    │ Generate Quality Report
└─────────────┘
```

## Phase 1: Gap Detection

### Objective
Identify games missing from each source without contaminating data.

### Steps

1. **Extract Game ID Mappings**
   ```bash
   # For ESPN ↔ hoopR
   python scripts/mapping/extract_espn_hoopr_game_mapping.py --output-format both
   ```

   **Output:**
   - `scripts/mapping/espn_hoopr_game_mapping.csv`
   - `scripts/mapping/espn_hoopr_game_mapping.json`

2. **Run Cross-Validation**
   ```bash
   python scripts/utils/cross_validate_espn_hoopr_with_mapping.py --export-gaps
   ```

   **Output:**
   - `/tmp/missing_from_hoopr.csv` - Games Source A has but Source B doesn't
   - `/tmp/missing_from_espn.csv` - Games Source B has but Source A doesn't
   - `/tmp/event_discrepancies.csv` - Games with different event counts

3. **Analyze Gap Patterns**
   ```bash
   # By year
   awk -F',' 'NR>1 {split($3,d,"-"); print d[1]}' /tmp/missing_from_hoopr.csv | sort | uniq -c

   # Sample gaps
   head -20 /tmp/missing_from_hoopr.csv
   ```

### Success Criteria
- [ ] Gap lists exported to CSV
- [ ] Gap patterns analyzed by year, team, game type
- [ ] Estimated scraping time calculated
- [ ] No data modification (read-only phase)

## Phase 2: Scrape Missing Games from ORIGINAL Source

### Objective
Fill gaps by scraping from the source that should have the data, NOT from other sources.

### Critical Decision Tree

```
Game missing from hoopR?
├─ YES → Scrape from hoopR API (NOT from ESPN)
└─ NO  → Move to next game

Game missing from ESPN?
├─ YES → Scrape from ESPN API (NOT from hoopR)
└─ NO  → Move to next game

Game missing from BOTH?
├─ Try → NBA API or Basketball Reference
└─ Document → Unavailable in all sources
```

### Steps

1. **Create Source-Specific Scraper**
   ```python
   # Example: scripts/etl/scrape_missing_hoopr_games.py

   def scrape_missing_from_hoopr_api(gap_list):
       """Scrape from hoopR API for games missing in hoopR database."""
       for gap in gap_list:
           game_id = gap['hoopr_game_id']
           game_date = gap['game_date']

           # Scrape from hoopR's ORIGINAL source
           hoopr_data = hoopR.load_nba_pbp(game_id=game_id)

           # Load to hoopR database ONLY
           load_to_hoopr_database(hoopr_data)  # NOT to ESPN!
   ```

2. **Run Scraper with Rate Limiting**
   ```bash
   # hoopR gaps (2,464 games)
   python scripts/etl/scrape_missing_hoopr_games.py \
       --gap-list /tmp/missing_from_hoopr.csv \
       --rate-limit 0.6 \
       --batch-size 100

   # ESPN gaps (2 games)
   python scripts/etl/scrape_missing_espn_games.py \
       --gap-list /tmp/missing_from_espn.csv \
       --rate-limit 1.0
   ```

3. **Handle Scraping Failures**
   ```python
   # If hoopR API fails for a game
   if scrape_failed:
       # Option 1: Try NBA API (different source)
       nba_api_data = scrape_from_nba_api(game_id)
       load_to_nba_api_database(nba_api_data)  # NOT to hoopR!

       # Option 2: Document as unavailable
       log_unavailable_game(game_id, source='hoopR', reason='API error')
   ```

### Success Criteria
- [ ] All gaps scraped from ORIGINAL source only
- [ ] No cross-contamination occurred
- [ ] Failures documented with reasons
- [ ] Scraping logs saved

## Phase 3: Load to Source Database (Keep Pure)

### Objective
Load scraped data ONLY to its native source database.

### Rules

**Allowed ✅:**
```python
espn_data → ESPN database
hoopr_data → hoopR database
nba_api_data → NBA API database
bbref_data → Basketball Reference database
```

**FORBIDDEN ❌:**
```python
espn_data → hoopR database  # WRONG!
hoopr_data → ESPN database  # WRONG!
ANY cross-loading            # WRONG!
```

### Steps

1. **Verify Database Before Loading**
   ```bash
   # Check row count before
   sqlite3 /tmp/hoopr_local.db "SELECT COUNT(*) FROM play_by_play;"
   # Should be 13,074,829
   ```

2. **Load to Correct Database**
   ```python
   # Load hoopR scraped data to hoopR database
   hoopr_conn = sqlite3.connect('/tmp/hoopr_local.db')
   load_play_by_play(hoopr_conn, hoopr_scraped_data)
   hoopr_conn.close()
   ```

3. **Verify Row Count After Loading**
   ```bash
   # Check row count after
   sqlite3 /tmp/hoopr_local.db "SELECT COUNT(*) FROM play_by_play;"
   # Should be 13,074,829 + new_events
   ```

4. **Sync to RDS (Same Source)**
   ```bash
   # Load hoopR gaps to RDS hoopR tables (NOT to ESPN tables!)
   python scripts/db/sync_hoopr_gaps_to_rds.py
   ```

### Success Criteria
- [ ] Data loaded to correct source database
- [ ] Row counts verified and increased as expected
- [ ] No foreign source data in database
- [ ] RDS synced with same source data

## Phase 4: Build Unified Database

### Objective
Create comprehensive database combining ALL sources with metadata tracking.

### Unified Database Schema

```sql
-- Main unified table
CREATE TABLE unified_play_by_play (
    id SERIAL PRIMARY KEY,
    game_id TEXT NOT NULL,
    source TEXT NOT NULL,  -- 'ESPN', 'hoopR', 'NBA_API', 'BBRef', 'Kaggle'

    -- Common fields (mapped from all sources)
    game_date DATE NOT NULL,
    period_number INTEGER,
    clock_display TEXT,
    event_description TEXT,
    home_score INTEGER,
    away_score INTEGER,
    scoring_play BOOLEAN,

    -- Source-specific fields preserved
    raw_json JSONB,  -- All original fields from source

    -- Metadata
    quality_score NUMERIC,  -- 0-100 based on completeness
    is_primary BOOLEAN,     -- TRUE if this is the recommended source
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coverage tracking
CREATE TABLE source_coverage (
    game_id TEXT PRIMARY KEY,
    game_date DATE NOT NULL,

    -- Which sources have this game?
    has_espn BOOLEAN DEFAULT FALSE,
    has_hoopr BOOLEAN DEFAULT FALSE,
    has_nba_api BOOLEAN DEFAULT FALSE,
    has_bbref BOOLEAN DEFAULT FALSE,
    has_kaggle BOOLEAN DEFAULT FALSE,

    -- Recommended source
    primary_source TEXT,
    backup_sources TEXT[],

    -- Quality
    total_sources INTEGER,
    has_discrepancies BOOLEAN DEFAULT FALSE
);

-- Discrepancy tracking (see Phase 5)
CREATE TABLE data_quality_discrepancies (
    -- Schema in Phase 5
);
```

### Steps

1. **Create Unified Database**
   ```bash
   # Local
   python scripts/db/create_unified_database.py --create-local

   # RDS
   python scripts/db/create_unified_database.py --create-rds
   ```

2. **Build Unified Data from All Sources**
   ```bash
   python scripts/etl/build_unified_database.py \
       --espn-db /tmp/espn_local.db \
       --hoopr-db /tmp/hoopr_local.db \
       --nba-api-db /tmp/nba_api_local.db \
       --bbref-db /tmp/bbref_local.db \
       --output-db /tmp/unified_nba.db
   ```

3. **Verify Unified Database**
   ```bash
   # Check all sources represented
   sqlite3 /tmp/unified_nba.db "
       SELECT source, COUNT(*)
       FROM unified_play_by_play
       GROUP BY source;
   "
   ```

### Success Criteria
- [ ] Unified database created (local + RDS)
- [ ] All source data imported with `source` tag
- [ ] Source-specific fields preserved in `raw_json`
- [ ] Coverage table populated
- [ ] No data loss from any source

## Phase 5: Document Discrepancies

### Objective
Identify and log when sources disagree on the same game data.

### Discrepancy Detection Schema

```sql
CREATE TABLE data_quality_discrepancies (
    id SERIAL PRIMARY KEY,
    game_id TEXT NOT NULL,
    field_name TEXT NOT NULL,  -- e.g., 'event_count', 'home_score', 'coordinate_x'

    -- Values from each source (NULL if source doesn't have game)
    espn_value TEXT,
    hoopr_value TEXT,
    nba_api_value TEXT,
    bbref_value TEXT,
    kaggle_value TEXT,

    -- Analysis
    difference NUMERIC,
    pct_difference NUMERIC,
    severity TEXT CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),

    -- Resolution
    recommended_source TEXT,
    recommended_value TEXT,
    ml_impact_notes TEXT,

    -- Metadata
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolution_status TEXT DEFAULT 'UNRESOLVED'
);
```

### Severity Levels

- **LOW:** <5% difference (e.g., 456 vs 477 events = 4.6% diff)
- **MEDIUM:** 5-10% difference
- **HIGH:** >10% difference or critical field mismatch

### Steps

1. **Run Discrepancy Detection**
   ```bash
   python scripts/validation/detect_data_discrepancies.py \
       --unified-db /tmp/unified_nba.db \
       --min-severity LOW \
       --export-report
   ```

2. **Example Discrepancies Detected**
   ```sql
   -- Event count mismatch
   INSERT INTO data_quality_discrepancies VALUES (
       1, '220612017', 'event_count',
       '456', '477', NULL, NULL, NULL,  -- ESPN vs hoopR
       21, 4.6, 'LOW',
       'hoopR', '477',
       'ESPN missing 21 events in Q4. Use hoopR for this game.'
   );

   -- Coordinate mismatch
   INSERT INTO data_quality_discrepancies VALUES (
       2, '230315001', 'shot_coordinate_x',
       '145', '152', '150', NULL, NULL,  -- 3 sources disagree
       NULL, NULL, 'MEDIUM',
       'NBA_API', '150',
       'ESPN and hoopR differ slightly. NBA API likely most accurate for coordinates.'
   );
   ```

3. **Generate Discrepancy Report**
   ```bash
   # Summary by severity
   sqlite3 /tmp/unified_nba.db "
       SELECT severity, COUNT(*) as count
       FROM data_quality_discrepancies
       GROUP BY severity;
   "

   # Export for ML
   python scripts/validation/export_quality_report.py \
       --format csv \
       --output reports/data_quality_$(date +%Y%m%d).csv
   ```

### Success Criteria
- [ ] All discrepancies logged to database
- [ ] Severity levels assigned
- [ ] Recommended source determined per discrepancy
- [ ] ML impact notes documented
- [ ] Report exported for analysis

## Phase 6: Generate Data Quality Report

### Objective
Create ML-ready quality assessment for model training.

### Report Contents

1. **Summary Statistics**
   ```
   Total Games: 31,243
   Total Sources: 5

   Coverage by Source:
   - ESPN: 31,241 games (99.99%)
   - hoopR: 28,779 games (92.1%)
   - NBA API: 15,432 games (49.4%)
   - BBRef: 22,456 games (71.9%)
   - Kaggle: 9,852 games (31.5%)

   Multi-Source Games: 18,234 (58.4%)
   Single-Source Games: 12,009 (41.6%)
   ```

2. **Discrepancy Summary**
   ```
   Total Discrepancies: 1,234
   - LOW: 987 (80%)
   - MEDIUM: 189 (15%)
   - HIGH: 58 (5%)

   Top Discrepancy Types:
   1. event_count (456 cases)
   2. coordinate_x (234 cases)
   3. coordinate_y (198 cases)
   4. player_id (156 cases)
   5. clock_seconds (92 cases)
   ```

3. **Recommended Sources by Game Type**
   ```
   Regular Season:
   - Primary: hoopR (best coverage)
   - Backup: ESPN

   Playoffs:
   - Primary: ESPN (better historical)
   - Backup: NBA API

   Pre-2002:
   - Primary: ESPN (exclusive)
   - Backup: None

   2002-2025:
   - Primary: hoopR (100% coverage)
   - Backup: ESPN
   ```

4. **ML Model Guidance**
   ```python
   # Quality scores per game
   {
       '220612017': {
           'recommended_source': 'hoopR',
           'quality_score': 95,
           'uncertainty': 'LOW',
           'notes': 'ESPN missing 21 events, use hoopR'
       },
       '230315001': {
           'recommended_source': 'NBA_API',
           'quality_score': 88,
           'uncertainty': 'MEDIUM',
           'notes': 'Coordinate discrepancies across sources'
       }
   }
   ```

### Steps

1. **Generate Report**
   ```bash
   python scripts/validation/generate_quality_report.py \
       --unified-db /tmp/unified_nba.db \
       --output-format markdown \
       --output reports/data_quality_report_$(date +%Y%m%d).md
   ```

2. **Export ML-Ready JSON**
   ```bash
   python scripts/validation/export_ml_quality_scores.py \
       --unified-db /tmp/unified_nba.db \
       --output data/quality/ml_quality_scores.json
   ```

3. **Update Documentation**
   ```bash
   # Update DATA_CATALOG.md with quality findings
   python scripts/utils/update_catalog_with_quality.py
   ```

### Success Criteria
- [ ] Comprehensive quality report generated
- [ ] ML guidance JSON exported
- [ ] Recommended sources documented per game
- [ ] Uncertainty estimates provided
- [ ] Documentation updated

## Automation Integration

### Nightly Orchestrator Updates

Add to `scripts/workflows/overnight_multi_source_scraper.sh`:

```bash
#!/bin/bash

# 1. Scrape each source independently
scrape_espn_updates
scrape_hoopr_updates
scrape_nba_api_updates
scrape_bbref_updates

# 2. Load to correct source databases (NO CROSS-LOADING!)
load_espn_to_espn_db
load_hoopr_to_hoopr_db
load_nba_api_to_nba_api_db
load_bbref_to_bbref_db

# 3. Run gap detection for each source pair
python scripts/utils/cross_validate_espn_hoopr_with_mapping.py --export-gaps
python scripts/utils/cross_validate_espn_nba_api.py --export-gaps
# ... other pairs

# 4. Scrape missing games from ORIGINAL sources
python scripts/etl/scrape_missing_hoopr_games.py
python scripts/etl/scrape_missing_espn_games.py
# ... other sources

# 5. Rebuild unified database
python scripts/etl/build_unified_database.py

# 6. Run discrepancy detection
python scripts/validation/detect_data_discrepancies.py

# 7. Generate quality reports
python scripts/validation/generate_quality_report.py

# 8. Update catalogs
python scripts/utils/update_data_catalog.py
```

### Success Criteria
- [ ] Automation runs all 6 phases nightly
- [ ] No manual intervention required
- [ ] Quality reports generated automatically
- [ ] Discrepancies tracked over time
- [ ] Alerts sent for HIGH severity issues

## Validation Checklist

**Before Starting:**
- [ ] Read `docs/DATA_INTEGRITY_PRINCIPLES.md`
- [ ] Understand NO CROSS-CONTAMINATION rule
- [ ] Have gap lists from Phase 1
- [ ] Backup all databases

**During Execution:**
- [ ] Only scrape from original sources
- [ ] Only load to same source database
- [ ] Track all discrepancies found
- [ ] Document scraping failures

**After Completion:**
- [ ] Verify source databases remain pure
- [ ] Check unified database completeness
- [ ] Review discrepancy report
- [ ] Update ML feature pipeline with quality scores

**Contamination Check:**
```bash
# Verify no cross-contamination
./scripts/validation/check_database_purity.sh

# Expected output:
# ✅ ESPN database: 100% ESPN data
# ✅ hoopR database: 100% hoopR data
# ✅ NBA API database: 100% NBA API data
# ✅ No foreign source markers found
```

## Success Metrics

### Data Purity (Critical)
- [ ] ESPN database: 100% ESPN data
- [ ] hoopR database: 100% hoopR data
- [ ] Each source database pristine
- [ ] No cross-contamination detected

### Data Completeness
- [ ] All gaps filled from original sources
- [ ] Missing games documented if unavailable
- [ ] Unified database spans all years
- [ ] All sources represented in unified DB

### Data Quality
- [ ] All discrepancies logged
- [ ] Severity levels assigned
- [ ] Recommended sources determined
- [ ] ML impact documented

### Automation
- [ ] Workflow runs nightly
- [ ] Quality reports auto-generated
- [ ] Alerts sent for issues
- [ ] No manual intervention needed

## Common Issues & Solutions

### Issue 1: Source API Unavailable
**Problem:** hoopR API returns 503 for a game
**Solution:**
- ✅ Log as unavailable in hoopR
- ✅ Try alternative hoopR endpoint
- ✅ Document in discrepancy table
- ❌ DO NOT load from ESPN (contamination!)

### Issue 2: Discrepancy Too Large
**Problem:** ESPN and hoopR differ by 50% on event count
**Solution:**
1. Investigate both sources manually
2. Try third source (NBA API) as tiebreaker
3. Mark as HIGH severity
4. Exclude from ML training until resolved
5. Document in `ml_impact_notes`

### Issue 3: Accidental Cross-Loading
**Problem:** Realized ESPN data was loaded to hoopR
**Solution:**
1. **STOP ALL PROCESSES**
2. Restore hoopR database from backup
3. Delete contaminated records if backup unavailable
4. Review automation scripts for cross-loading logic
5. Update `docs/DATA_INTEGRITY_PRINCIPLES.md` with incident

## Related Workflows

- **Workflow #1:** Session Start Protocol
- **Workflow #38:** Overnight Scraper Handoff
- **Workflow #39:** Scraper Monitoring Automation
- **Cross-Validation:** `scripts/utils/cross_validate_espn_hoopr_with_mapping.py`

## References

- **Data Integrity:** `docs/DATA_INTEGRITY_PRINCIPLES.md`
- **Gap Analysis:** `reports/espn_hoopr_gap_analysis_20251009.md`
- **Scraper Management:** `docs/SCRAPER_MANAGEMENT.md`

---

**Remember:** Data integrity is non-negotiable. Keep sources pure, document discrepancies, guide ML models.

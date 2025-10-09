# Data Integrity Principles

**Created:** October 9, 2025
**Last Updated:** October 9, 2025

## Core Principle: Never Cross-Contaminate Data Sources

### ⚠️ Critical Rule
**NEVER load data from one source into another source's database.**

Each data source must remain pure and pristine for validation purposes.

### Why This Matters

1. **Data Quality Validation**
   - Can only validate by comparing independent sources
   - Contaminated data defeats the purpose of multi-source validation
   - ML models need to know true data quality

2. **Discrepancy Detection**
   - Must compare apples-to-apples from original sources
   - Cross-contamination hides discrepancies
   - Cannot determine which source is more reliable

3. **Scientific Integrity**
   - Each source represents independent observation
   - Mixing sources creates circular validation
   - Loses ability to detect systematic errors

### Correct Architecture

#### Source Databases (Keep Pure)
```
ESPN Database     → Only ESPN data
hoopR Database    → Only hoopR data
NBA API Database  → Only NBA API data
Basketball Ref DB → Only Basketball Reference data
Kaggle Database   → Only Kaggle data
```

#### Unified Database (Our Comprehensive Database)
```
Unified Database → Combines ALL sources with metadata
                  → Tracks source for each record
                  → Documents discrepancies
                  → ML-ready quality scores
```

### Gap-Filling Strategy

**INCORRECT ❌:**
```python
# BAD: Loading ESPN data into hoopR database
espn_events = extract_from_espn(game_id)
load_to_hoopr_database(espn_events)  # WRONG!
```

**CORRECT ✅:**
```python
# GOOD: Scrape missing game from hoopR's original source
if game_missing_in_hoopr:
    hoopr_events = scrape_from_hoopr_api(game_id)  # Original source
    load_to_hoopr_database(hoopr_events)  # Same source

# GOOD: Build unified database from all pure sources
unified_data = combine_sources(
    espn_db.get_events(game_id),
    hoopr_db.get_events(game_id),
    nba_api_db.get_events(game_id)
)
load_to_unified_database(unified_data)  # Separate database
```

### Historical Context: Contamination Near-Miss

**Date:** October 9, 2025

**What Almost Happened:**
- Created script `fill_hoopr_gaps_from_espn.py`
- Would have loaded 2,464 ESPN games into hoopR database
- Would have destroyed data integrity

**How We Caught It:**
- User recognized the integrity violation
- Script was created but never executed
- Databases remain clean (verified by timestamps and row counts)

**Action Taken:**
- Deleted contamination script
- Created this documentation
- Implemented Workflow #51 (proper multi-source validation)

**Lesson Learned:**
When a game is missing from hoopR, **scrape it from hoopR's API**, not from ESPN.

### Data Quality Discrepancy Tracking

When sources disagree, document in `data_quality_discrepancies` table:

```sql
CREATE TABLE data_quality_discrepancies (
    id SERIAL PRIMARY KEY,
    game_id TEXT NOT NULL,
    field_name TEXT NOT NULL,

    -- Values from each source
    espn_value TEXT,
    hoopr_value TEXT,
    nba_api_value TEXT,
    bbref_value TEXT,

    -- Analysis
    difference NUMERIC,
    pct_difference NUMERIC,
    severity TEXT CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),

    -- ML guidance
    recommended_source TEXT,
    ml_impact_notes TEXT,

    -- Metadata
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolution_status TEXT DEFAULT 'UNRESOLVED'
);
```

**Example Discrepancy:**
```sql
INSERT INTO data_quality_discrepancies VALUES (
    1,
    '220612017',  -- Game ID
    'event_count', -- Field
    456,          -- ESPN: 456 events
    477,          -- hoopR: 477 events
    NULL,         -- NBA API: no data
    NULL,         -- BBRef: no data
    21,           -- Difference
    4.6,          -- % difference
    'LOW',        -- Severity
    'hoopR',      -- Recommended (more events)
    'ESPN missing 21 events in Q4. Use hoopR for this game.'
);
```

### Unified Database Builder Pattern

**Workflow:**
1. Read from each pure source database
2. Add `source` metadata field
3. Preserve source-specific fields in `raw_json`
4. Load to unified database
5. Run discrepancy detection
6. Generate quality report

**Code Pattern:**
```python
def build_unified_database(game_id):
    # Get from each pure source
    espn_data = espn_db.get_game(game_id)
    hoopr_data = hoopr_db.get_game(game_id)
    nba_api_data = nba_api_db.get_game(game_id)

    # Combine with metadata
    unified_record = {
        'game_id': game_id,
        'espn_events': espn_data if espn_data else None,
        'hoopr_events': hoopr_data if hoopr_data else None,
        'nba_api_events': nba_api_data if nba_api_data else None,
        'primary_source': select_primary_source(),
        'has_discrepancies': detect_discrepancies()
    }

    # Load to unified database (separate from sources)
    unified_db.insert(unified_record)
```

### Automation Checklist

**Nightly Scraper Orchestrator Must:**
- [ ] Scrape each source independently
- [ ] Load to correct source database only
- [ ] Rebuild unified database from all sources
- [ ] Run discrepancy detection
- [ ] Generate data quality report
- [ ] NEVER cross-load between sources

### Violation Detection

**Signs of Contamination:**
```bash
# Check for foreign source markers in database
sqlite3 /tmp/hoopr_local.db "SELECT * FROM play_by_play WHERE text LIKE '%ESPN%' LIMIT 5;"

# Verify row counts haven't changed unexpectedly
sqlite3 /tmp/hoopr_local.db "SELECT COUNT(*) FROM play_by_play;" # Should be 13,074,829

# Check database modification times
ls -lh /tmp/*_local.db
```

**If Contamination Detected:**
1. Stop all processes immediately
2. Restore from last clean backup
3. Document incident
4. Review automation scripts for cross-loading logic
5. Update this document with lessons learned

### References

- **Workflow #51:** Multi-Source Data Quality Validation
- **Architecture Doc:** `docs/PROJECT_VISION.md`
- **Gap Analysis:** `reports/espn_hoopr_gap_analysis_20251009.md`

---

**Remember:** Data integrity is non-negotiable. When in doubt, keep sources separate.

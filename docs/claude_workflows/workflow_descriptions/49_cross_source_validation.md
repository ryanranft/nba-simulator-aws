# Workflow #49: Cross-Source Data Validation (Local-First Pattern)

**Version:** 1.0
**Created:** October 9, 2025
**Category:** Data Validation
**Estimated Time:** 1-2 hours
**Cost:** $0 (local validation only)
**Reusability:** Template for all future data sources

---

## Overview

**Purpose:** Validate new data sources locally before expensive cloud operations by cross-validating against existing trusted sources.

**When to Use:**
- Adding new data source (hoopR, NBA API, Basketball Reference, etc.)
- Before loading data to RDS
- Before expensive cloud operations
- When validating data quality

**Pattern Established:** Local validation → Cloud operations (saves time & cost)

**Evidence:**
- `scripts/utils/compare_espn_databases.py` - ESPN local vs RDS validation
- `docs/ESPN_SCRAPER_GUIDE.md` - Documents local-first approach
- October 2025: Extended pattern to cross-source validation

---

## Prerequisites

**Before starting this workflow:**

1. ✅ New data source collected and available locally (parquet/CSV/JSON)
2. ✅ At least one existing trusted data source in local database
3. ✅ Python environment active (`conda activate nba-aws`)
4. ✅ Sufficient disk space for local SQLite database (~500 MB per source)

**Required Files:**
- Source data files (parquet, CSV, or JSON)
- Existing local database for comparison (e.g., `/tmp/espn_local.db`)

**Cost Check:**
- ✅ $0 - All operations are local
- ⚠️ Only costs occur when loading to RDS (Phase 4)

---

## Workflow Steps

### Phase 1: Create Local Database for New Source (15-30 min)

**Goal:** Convert source data files to SQLite for fast local queries

**Step 1.1: Create database builder script**

Template: `scripts/db/create_local_{source}_database.py`

```python
#!/usr/bin/env python3
"""
Create Local {SOURCE_NAME} SQLite Database

Convert {source} data files to SQLite for fast local validation.

Input:  {source} parquet/CSV files (X GB, Y data types)
Output: /tmp/{source}_local.db (SQLite, ~Z MB)

Pattern: Local validation before cloud load
"""

import sqlite3
import pandas as pd
from pathlib import Path

class {Source}DatabaseCreator:
    """Create local SQLite database from {source} data files."""

    def __init__(self, source_dir: str, output_db: str):
        self.source_dir = Path(source_dir)
        self.output_db = output_db
        self.conn = None

    def create_database(self):
        """Main entry point - create complete database."""
        # 1. Remove existing database
        # 2. Create connection
        # 3. Create tables
        # 4. Load data
        # 5. Create indexes
        # 6. Print summary
        # 7. Close connection

    def _create_tables(self):
        """Create database tables matching {source} schema."""
        # Define tables based on source schema

    def _load_data_type_1(self):
        """Load first data type (e.g., play-by-play)."""
        # Find parquet/CSV files
        # Load in batches with progress tracking
        # Use pandas.to_sql() for insertion

    def _create_indexes(self):
        """Create indexes for common queries."""
        # game_id, season, game_date, team_id, athlete_id

    def _print_summary(self):
        """Print database summary statistics."""
        # Table counts, date ranges, seasons, database size
```

**Key Implementation Details:**

1. **Table Schema:**
   - Match source data schema exactly
   - Add common indexes (game_id, season, date)
   - Use TEXT for IDs (consistent with ESPN pattern)

2. **Data Loading:**
   - Process files in batches (5 at a time for progress)
   - Use `pandas.to_sql()` with `if_exists='append'`
   - Print progress every 5 files

3. **Summary Statistics:**
   - Table row counts
   - Date range coverage
   - Season count
   - Database size in MB

**Example (hoopR):**
```bash
python scripts/db/create_local_hoopr_database.py
# Output: /tmp/hoopr_local.db (~500 MB from 6.2 GB parquet)
```

**Step 1.2: Test database creation**

```bash
# Run script
python scripts/db/create_local_{source}_database.py

# Verify database created
ls -lh /tmp/{source}_local.db

# Quick validation query
sqlite3 /tmp/{source}_local.db "SELECT COUNT(*) FROM play_by_play;"
```

**Expected Output:**
```
======================================================================
CREATE LOCAL {SOURCE} DATABASE
======================================================================

Source: /path/to/source/data
Output: /tmp/{source}_local.db

✅ Created database: /tmp/{source}_local.db
📋 Creating tables...
  ✅ Created 4 tables (play_by_play, player_box, team_box, schedule)

📊 Loading play-by-play data...
  Found 24 parquet files
  Progress: 24/24 files (8,450,123 rows)
  ✅ Loaded 8,450,123 play-by-play events

[... similar for other data types ...]

🔍 Creating indexes...
  ✅ Created 10 indexes

======================================================================
DATABASE SUMMARY
======================================================================

📊 Data Summary:
  Play-by-play events:  8,450,123
  Player box scores:    525,000
  Team box scores:      62,000
  Schedule games:       31,000

📅 Coverage:
  Date range:           2002-10-29 to 2025-04-15
  Seasons:              24 seasons

💾 Database:
  Size:                 485.2 MB
  Location:             /tmp/{source}_local.db

✅ SUCCESS - Ready for local validation!
```

---

### Phase 2: Cross-Validate Against Existing Source (30-45 min)

**Goal:** Compare new source against trusted existing source to identify overlap, gaps, and complementary data

**Step 2.1: Create comparison script**

Template: `scripts/utils/compare_{source1}_{source2}_local.py`

```python
#!/usr/bin/env python3
"""
Compare {Source1} and {Source2} Local Databases

Cross-validate two data sources using local SQLite databases.

Identifies:
1. Overlap period (games covered by both sources)
2. Complementary data (unique to each source)
3. Data quality differences
4. Event count discrepancies

Pattern: Cross-source validation before RDS load
"""

import sqlite3
from datetime import datetime
from typing import Dict

class CrossSourceComparator:
    """Compare two local SQLite databases for validation."""

    def __init__(self, source1_db: str, source2_db: str):
        self.source1_db = source1_db
        self.source2_db = source2_db
        self.source1_conn = None
        self.source2_conn = None

    def compare_summary(self) -> Dict:
        """Fast summary comparison (recommended)."""
        # 1. Get statistics from both sources
        # 2. Identify overlap period
        # 3. Compare overlap coverage
        # 4. Identify complementary data
        # 5. Flag discrepancies

    def compare_detailed(self, season: int = None) -> Dict:
        """Detailed game-by-game comparison (slower)."""
        # Compare every game in overlap period
        # Identify missing games, event count differences
        # Export discrepancies for manual review

    def _get_source1_statistics(self) -> Dict:
        """Query source1 for key statistics."""
        # Date range, game count, event count, seasons

    def _identify_overlap_period(self, s1_stats, s2_stats) -> Dict:
        """Find period covered by both sources."""
        # Intersection of date ranges

    def _compare_overlap_coverage(self, overlap) -> Dict:
        """Compare game counts in overlap period."""
        # Game counts, event counts, missing games
```

**Key Validation Checks:**

1. **Overlap Identification:**
   ```sql
   -- Find common date range
   SELECT
     MAX(s1.min_date, s2.min_date) as overlap_start,
     MIN(s1.max_date, s2.max_date) as overlap_end
   FROM source1_stats s1, source2_stats s2;
   ```

2. **Game Count Comparison:**
   ```sql
   -- Games in overlap period
   SELECT COUNT(DISTINCT game_id)
   FROM schedule
   WHERE game_date BETWEEN :overlap_start AND :overlap_end;
   ```

3. **Event Count Comparison:**
   ```sql
   -- PBP events per game
   SELECT game_id, COUNT(*) as event_count
   FROM play_by_play
   WHERE game_date BETWEEN :overlap_start AND :overlap_end
   GROUP BY game_id;
   ```

4. **Expected Differences:**
   - Document known differences between sources
   - Example: hoopR typically +2-5% more events than ESPN
   - Flag only unexpected discrepancies

**Step 2.2: Run comparison**

```bash
# Summary comparison (fast - 30 seconds)
python scripts/utils/compare_{source1}_{source2}_local.py

# Detailed comparison (slower - 2-3 minutes)
python scripts/utils/compare_{source1}_{source2}_local.py --detailed

# Export report for analysis
python scripts/utils/compare_{source1}_{source2}_local.py --export-report overlap_analysis.csv
```

**Expected Output:**
```
======================================================================
CROSS-SOURCE VALIDATION: {SOURCE1} ↔ {SOURCE2}
======================================================================

Timestamp: 2025-10-09 14:30:00

📊 {SOURCE1} Statistics:
  Date range:           1993-11-05 to 2025-04-15
  Total games:          45,678
  PBP events:           18,234,567
  Seasons:              32 seasons
  Quality score:        90/100 (second precision)

📊 {SOURCE2} Statistics:
  Date range:           2002-10-29 to 2025-04-15
  Total games:          31,234
  PBP events:           12,567,890
  Seasons:              24 seasons
  Quality score:        80/100 (minute precision)

======================================================================
OVERLAP ANALYSIS (2002-2025)
======================================================================

📅 Overlap Period:
  Start date:           2002-10-29
  End date:             2025-04-15
  Duration:             23 years

🎯 Coverage Comparison:
  {Source1} games:      30,123
  {Source2} games:      31,234
  Common games:         29,890
  {Source1} only:       233 games
  {Source2} only:       1,344 games

📊 Event Count Analysis:
  {Source1} avg/game:   410 events
  {Source2} avg/game:   420 events
  Difference:           +2.4% ({Source2})
  ✅ Within expected range (+2-5%)

======================================================================
COMPLEMENTARY DATA
======================================================================

🔍 Unique to {Source1}:
  Pre-2002 data:        15,555 games (1993-2001)
  Historical value:     HIGH (ESPN is primary source)

🔍 Unique to {Source2}:
  Complete 2002-2025:   Better PBP coverage
  Coordinate data:      Shot location (x, y)
  Additional columns:   63 vs 45 columns

======================================================================
VALIDATION RESULT
======================================================================

✅ PASS - Sources are complementary

Recommendation:
  1. Use {Source1} for 1993-2001 (exclusive coverage)
  2. Use both sources for 2002-2025 (cross-validation)
  3. Priority: {Source2} for shot location data
  4. Quality: {Source1} has second-precision timestamps

Next Steps:
  1. Run local-cloud sync check (Workflow #50)
  2. Load both sources to RDS
  3. Create unified view combining best of both
```

**Step 2.3: Document findings**

Update `docs/DATA_CATALOG.md` with:
- Overlap period identified
- Complementary data summary
- Expected differences (for future reference)
- Validation result (PASS/FAIL)

---

### Phase 3: Verify Local-Cloud Sync (15-30 min)

**Goal:** Ensure local validation databases accurately reflect cloud data

**Why Important:** Local validation is only valuable if local matches cloud!

**Step 3.1: Run sync verification**

```bash
# Full verification (hoopR + ESPN)
python scripts/utils/verify_local_cloud_sync.py

# Skip ESPN RDS check (faster, no RDS connection)
python scripts/utils/verify_local_cloud_sync.py --skip-espn-rds

# Detailed output with sample checksums
python scripts/utils/verify_local_cloud_sync.py --detailed
```

**Checks Performed:**

1. **New Source Local ↔ S3:**
   - File count comparison
   - Total size comparison (allow 1% variance)
   - Sample checksum verification (--detailed mode)

2. **Existing Source Local ↔ RDS:**
   - Run existing comparison script
   - Verify tables match
   - Check row counts

**Expected Output:**
```
======================================================================
LOCAL-CLOUD SYNCHRONIZATION VERIFICATION
======================================================================

Timestamp: 2025-10-09 15:00:00

======================================================================
CHECK 1: {Source} Local Parquet ↔ S3 Sync
======================================================================

📁 Scanning local {source} parquet files...
  Found: 96 files (531.2 MB)

☁️  Scanning S3 {source} parquet files...
  Found: 96 files (531.5 MB)

  ✅ Size variance: 0.06% (acceptable)

✅ {Source} local ↔ S3 sync: VERIFIED

======================================================================
CHECK 2: ESPN Local SQLite ↔ RDS Sync
======================================================================

🔍 Running ESPN database comparison...
  Script: scripts/utils/compare_espn_databases.py
  ✅ ESPN local SQLite ↔ RDS: SYNCED

======================================================================
VERIFICATION SUMMARY
======================================================================

📊 {Source} Local ↔ S3 Sync:
  Status:       SYNCED
  Local files:  96 (531.2 MB)
  S3 files:     96 (531.5 MB)

📊 ESPN Local ↔ RDS Sync:
  Status:       SYNCED

🎯 Overall Status: PASSED

✅ All checks passed - Local validation will accurately reflect cloud data

======================================================================
NEXT STEPS
======================================================================

✅ Proceed with cross-source validation:
  1. python scripts/db/create_local_{source}_database.py
  2. python scripts/utils/compare_{source1}_{source2}_local.py
  3. Load to RDS (if validation passes)
```

**Step 3.2: Fix sync issues (if any)**

If verification fails:

1. **File count mismatch:**
   - Re-upload missing files to S3
   - Re-download from S3 if local is missing

2. **Size variance >1%:**
   - Check for corrupted uploads
   - Re-upload affected files
   - Verify with `aws s3 ls --recursive`

3. **ESPN RDS out of sync:**
   - Re-run ESPN database load script
   - Check RDS connection
   - Verify credentials

---

### Phase 4: Decision Point - Load to RDS

**Only proceed if:**
- ✅ Cross-source validation PASSED
- ✅ Local-cloud sync verification PASSED
- ✅ User has reviewed findings and approved
- ✅ Cost estimate provided and approved

**Cost Estimate:**
- RDS load time: 3-4 hours @ $0.017/hr = ~$0.06-0.07
- Data transfer: Free (same region)
- Storage: +$0.10/month per GB

**Load Script Template:**
```bash
python scripts/db/load_{source}_to_rds.py
```

**Expected Duration:** 3-4 hours for 6-8 GB of data

---

## Success Criteria

**Phase 1 Success:**
- ✅ Local database created successfully
- ✅ All data types loaded with expected row counts
- ✅ Indexes created for performance
- ✅ Database size within expected range

**Phase 2 Success:**
- ✅ Overlap period identified clearly
- ✅ Complementary data documented
- ✅ Event count differences within expected range
- ✅ No unexpected discrepancies

**Phase 3 Success:**
- ✅ Local files match S3 (count and size)
- ✅ Existing source local matches RDS
- ✅ Overall sync status: PASSED

**Overall Success:**
- ✅ All 3 phases completed successfully
- ✅ Validation report shows sources are complementary
- ✅ User has approved proceeding to RDS load
- ✅ Findings documented in DATA_CATALOG.md

---

## Template Variables for Future Sources

**When adapting this workflow for new source:**

| Variable | hoopR Example | NBA API Example | Basketball Ref Example |
|----------|---------------|-----------------|------------------------|
| `{source}` | hoopr | nba_api | basketball_reference |
| `{SOURCE_NAME}` | hoopR | NBA API | Basketball Reference |
| `source_dir` | `~/Desktop/.../hoopR/nba` | `~/Desktop/.../nba_api` | `~/Desktop/.../bbref` |
| `output_db` | `/tmp/hoopr_local.db` | `/tmp/nba_api_local.db` | `/tmp/bbref_local.db` |
| Data types | 4 (pbp, player, team, sched) | 5+ | 3+ |
| Expected size | 6.2 GB → 500 MB | TBD | TBD |
| Quality score | 80/100 (minute) | TBD | 85/100 (second) |
| Overlap start | 2002-10-29 | TBD | 1946-11-01 |

**Scripts to Create:**
1. `scripts/db/create_local_{source}_database.py`
2. `scripts/utils/compare_{source1}_{source2}_local.py`
3. `scripts/db/load_{source}_to_rds.py` (Phase 4)

---

## Troubleshooting

**Issue: Database creation fails**
- Check source directory path exists
- Verify parquet files are readable
- Check disk space (need 2x source size)
- Review error traceback for specific pandas/sqlite errors

**Issue: Comparison shows huge discrepancies**
- Verify date range overlap is correct
- Check if comparing same seasons
- Review data type compatibility (PBP vs box scores)
- Check for timezone differences in timestamps

**Issue: Local-cloud sync fails**
- Re-upload to S3 with `aws s3 cp --recursive`
- Verify AWS credentials are current
- Check S3 bucket permissions
- Test with single file first

**Issue: Validation passes but data looks wrong**
- Sample manual queries to verify data quality
- Check date formats match expected schema
- Verify game IDs are consistent
- Review data type conversions (text vs integer)

---

## Benefits of This Pattern

**Time Savings:**
- Local queries: milliseconds vs network latency
- Iterate quickly on validation logic
- No waiting for RDS connections

**Cost Savings:**
- $0 local validation vs RDS connection costs
- Catch issues before expensive 3-4 hour RDS loads
- No wasted RDS compute time on bad data

**Confidence:**
- Cross-validate before cloud operations
- Verify local matches cloud (local-cloud sync)
- Document expected differences for future reference
- Establish baseline for quality scoring

**Reusability:**
- Template pattern works for any data source
- 3 scripts cover full validation pipeline
- Documented variables for quick adaptation
- Examples guide future implementations

---

## Related Workflows

- **Workflow #21:** Data Validation Framework (parent workflow)
- **Workflow #50:** Local-Cloud Sync Verification (detailed procedures)
- **Workflow #38:** Overnight Scraper Handoff (monitoring pattern)
- **Workflow #39:** Scraper Monitoring Automation (completion checks)

---

## Change Log

**v1.0 - October 9, 2025:**
- Initial workflow creation
- Codified local-first validation pattern
- Extended ESPN pattern to cross-source validation
- Created reusable templates for future sources
- Documented hoopR vs ESPN validation as reference example

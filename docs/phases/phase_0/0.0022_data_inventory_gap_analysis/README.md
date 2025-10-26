# Phase 0.0022: Data Inventory & Gap Analysis

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ✅ COMPLETE (Migrated from Phase 8)
**Priority:** 🟡 IMPORTANT
**Migrated From:** Phase 8 (Data Audit & Inventory)
**First Execution:** October 11, 2025
**Second Execution:** October 11, 2025 (gaps verified resolved)

---

## Overview

Comprehensive recursive data audit system that discovers, catalogs, and analyzes ALL data holdings across all storage locations (S3, RDS, SQLite, local files, external repositories). This phase creates a complete inventory and identifies gaps, duplicates, and sync issues.

**This sub-phase delivers:**
- Complete data inventory across all locations
- Data gap identification with severity ratings
- Multi-source reconciliation
- Quality analysis and validation
- Master inventory documentation
- Reusable audit workflows for future data acquisitions

**Why data audits matter:**
- Prevents "lost" data across multiple storage locations
- Identifies critical gaps before they impact analysis
- Ensures sync status between local, S3, and RDS
- Provides complete picture of data holdings
- Establishes baseline for future comparisons

---

## Sub-Components

### 1. Recursive Data Discovery

**Goal:** Find ALL data across all storage locations

**Storage Locations to Audit:**

#### A. S3 Bucket (Primary Data Lake)
```bash
# scripts/audit/discover_s3_data.sh
#!/bin/bash

echo "=== S3 Data Discovery ===" | tee -a audit_log.txt

# Total object count
S3_TOTAL=$(aws s3 ls s3://nba-sim-raw-data-lake/ --recursive | wc -l)
echo "Total S3 objects: $S3_TOTAL" | tee -a audit_log.txt

# Breakdown by data source
for source in espn nba_api hoopr basketball_reference kaggle odds_api; do
    COUNT=$(aws s3 ls s3://nba-sim-raw-data-lake/$source/ --recursive | wc -l)
    echo "  $source: $COUNT files" | tee -a audit_log.txt
done

# Total size
SIZE=$(aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize | grep "Total Size" | awk '{print $3}')
SIZE_GB=$(echo "scale=2; $SIZE / 1073741824" | bc)
echo "Total size: ${SIZE_GB} GB" | tee -a audit_log.txt
```

#### B. RDS PostgreSQL Database
```sql
-- scripts/audit/discover_rds_data.sql
-- Get row counts for all tables

SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Get database size
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE datname = 'nba_simulator';

-- Get table sizes
SELECT
    schemaname || '.' || tablename AS table_full_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;
```

#### C. SQLite Databases (Local)
```bash
# scripts/audit/discover_sqlite_data.sh
#!/bin/bash

echo "=== SQLite Database Discovery ===" | tee -a audit_log.txt

# Find all .db files
find . -name "*.db" -o -name "*.sqlite" | while read db; do
    echo "Database: $db" | tee -a audit_log.txt

    # Get table counts
    sqlite3 "$db" "SELECT name FROM sqlite_master WHERE type='table';" | while read table; do
        COUNT=$(sqlite3 "$db" "SELECT COUNT(*) FROM $table;")
        echo "  $table: $COUNT rows" | tee -a audit_log.txt
    done
done
```

#### D. Local Project Files
```bash
# scripts/audit/discover_local_data.sh
#!/bin/bash

echo "=== Local File Discovery ===" | tee -a audit_log.txt

# Count data files by type
for ext in json csv parquet db sqlite; do
    COUNT=$(find data/ -name "*.$ext" 2>/dev/null | wc -l)
    echo "$ext files: $COUNT" | tee -a audit_log.txt
done

# Find large files (>100MB)
echo "Large files (>100MB):" | tee -a audit_log.txt
find data/ -type f -size +100M -exec ls -lh {} \; | awk '{print $9, $5}' | tee -a audit_log.txt
```

#### E. External Repositories
```bash
# scripts/audit/discover_external_data.sh
#!/bin/bash

echo "=== External Data Discovery ===" | tee -a audit_log.txt

# Check 0espn multi-sport repo
if [ -d "/Users/ryanranft/0espn" ]; then
    ESPN_COUNT=$(find /Users/ryanranft/0espn -name "*.json" | wc -l)
    ESPN_SIZE=$(du -sh /Users/ryanranft/0espn | awk '{print $1}')
    echo "0espn repository: $ESPN_COUNT files, $ESPN_SIZE" | tee -a audit_log.txt
fi

# Check Downloads folder for recent acquisitions
if [ -d "$HOME/Downloads" ]; then
    RECENT=$(find "$HOME/Downloads" -name "*nba*" -o -name "*basketball*" -mtime -30 2>/dev/null | wc -l)
    echo "Recent NBA files in Downloads: $RECENT" | tee -a audit_log.txt
fi
```

### 2. Deep Content Analysis

**Goal:** Validate data quality and identify gaps

#### A. Quality Sampling
```python
# scripts/audit/sample_data_quality.py
import random
import json
from pathlib import Path

def sample_espn_data(sample_size=100):
    """Sample ESPN data files to verify quality"""

    # Get all ESPN files
    espn_files = list(Path('data/espn').rglob('*.json'))

    # Random sample
    sample = random.sample(espn_files, min(sample_size, len(espn_files)))

    results = {
        'total_files': len(espn_files),
        'sample_size': len(sample),
        'valid': 0,
        'empty': 0,
        'malformed': 0,
        'errors': []
    }

    for file_path in sample:
        try:
            with open(file_path) as f:
                data = json.load(f)

            if not data or data == {}:
                results['empty'] += 1
            else:
                results['valid'] += 1

        except json.JSONDecodeError as e:
            results['malformed'] += 1
            results['errors'].append(str(file_path))

    results['quality_pct'] = (results['valid'] / results['sample_size']) * 100

    return results
```

#### B. Date Range Analysis
```python
# scripts/audit/analyze_date_ranges.py
import re
from pathlib import Path
from datetime import datetime

def extract_game_dates():
    """Extract game dates from file names to understand coverage"""

    date_pattern = r'(\d{8})'  # YYYYMMDD format
    dates = set()

    for json_file in Path('data/espn').rglob('*.json'):
        match = re.search(date_pattern, json_file.name)
        if match:
            try:
                date_str = match.group(1)
                date = datetime.strptime(date_str, '%Y%m%d')
                dates.add(date)
            except ValueError:
                pass

    if dates:
        return {
            'earliest': min(dates),
            'latest': max(dates),
            'total_dates': len(dates),
            'years_covered': max(dates).year - min(dates).year + 1
        }
    return None
```

#### C. Multi-Source Reconciliation
```python
# scripts/audit/reconcile_sources.py
from collections import defaultdict

def reconcile_game_coverage():
    """Identify which sources have which games"""

    sources = ['espn', 'nba_api', 'hoopr', 'basketball_reference']
    game_coverage = defaultdict(set)

    for source in sources:
        source_path = Path(f'data/{source}')
        if source_path.exists():
            for game_file in source_path.rglob('*.json'):
                # Extract game ID from filename
                game_id = extract_game_id(game_file.name)
                if game_id:
                    game_coverage[game_id].add(source)

    # Analyze coverage
    coverage_stats = {
        'total_unique_games': len(game_coverage),
        'single_source': 0,
        'multi_source': 0,
        'all_sources': 0,
        'gaps': []
    }

    for game_id, sources_found in game_coverage.items():
        if len(sources_found) == 1:
            coverage_stats['single_source'] += 1
        elif len(sources_found) >= 2:
            coverage_stats['multi_source'] += 1
        if len(sources_found) == 4:
            coverage_stats['all_sources'] += 1

        # Identify games missing from primary source (ESPN)
        if 'espn' not in sources_found:
            coverage_stats['gaps'].append({
                'game_id': game_id,
                'sources': list(sources_found)
            })

    return coverage_stats
```

### 3. Gap Identification

**Goal:** Identify critical data gaps with severity ratings

**Gap Categories:**

```python
# scripts/audit/identify_gaps.py

GAP_CATEGORIES = {
    'CRITICAL': {
        'description': 'Missing data that blocks core functionality',
        'examples': [
            'Play-by-play data for recent seasons (2023-2025)',
            'Box score data for playoff games',
            'Player stats for active players'
        ],
        'severity_score': 10
    },
    'HIGH': {
        'description': 'Missing data that significantly impacts analysis',
        'examples': [
            'Historical data gaps (missing seasons)',
            'Incomplete lineup data',
            'Missing advanced stats'
        ],
        'severity_score': 7
    },
    'MEDIUM': {
        'description': 'Missing data that limits some features',
        'examples': [
            'Pre-2000 data gaps',
            'G League data',
            'International stats'
        ],
        'severity_score': 5
    },
    'LOW': {
        'description': 'Nice-to-have data that is not essential',
        'examples': [
            'Pre-1950 data',
            'Summer League games',
            'All-Star game details'
        ],
        'severity_score': 2
    }
}

def identify_gaps():
    """Identify data gaps with severity ratings"""
    gaps = []

    # Check for temporal gaps in play-by-play
    pbp_coverage = analyze_pbp_coverage()
    for gap in pbp_coverage['gaps']:
        if gap['years'] >= [2020, 2025]:
            severity = 'CRITICAL'
        elif gap['years'] >= [2010, 2020]:
            severity = 'HIGH'
        elif gap['years'] >= [2000, 2010]:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'

        gaps.append({
            'category': 'play_by_play',
            'severity': severity,
            'description': f"Missing PBP data for {gap['years']}",
            'impact': calculate_impact(gap),
            'resolution': 'Scrape from ESPN or NBA API'
        })

    return gaps
```

### 4. Master Inventory Document

**Goal:** Single source of truth for all data holdings

**Create:** `docs/MASTER_DATA_INVENTORY.md`

Structure:
```markdown
# Master Data Inventory

**Last Updated:** 2025-10-25
**Total Data:** 172,719 files (118 GB)

---

## Executive Summary

- **S3 Bucket:** 172,719 files (118 GB)
- **RDS PostgreSQL:** 48.4M rows (23 tables)
- **SQLite Databases:** 3 databases (13.6M rows)
- **Local Files:** 146,150 files
- **External (0espn):** 1.2M files (mostly duplicate)

**Data Quality:** 93.1% success rate
**Temporal Coverage:** 1946-2025 (79 years)
**Critical Gaps:** 0 (all resolved via hoopR)

---

## S3 Bucket Breakdown

### nba-sim-raw-data-lake/

| Data Source | Files | Size | Date Range | Status |
|-------------|-------|------|------------|--------|
| **ESPN** | 146,115 | 95 GB | 1993-2025 | ✅ Complete |
| **hoopR** | 96 | 8.2 GB | 2002-2025 | ✅ Complete |
| **NBA API** | 22,000 | 10 GB | 1995-2006 | ✅ Complete |
| **Basketball Reference** | 444 | 2 GB | 1946-2025 | 🔄 Collecting (ADCE) |
| **Kaggle** | 1 | 500 MB | 1946-2023 | ✅ Complete |
| **Odds API** | 64 | 50 MB | 2024-2025 | 🔄 Live updates |
| **TOTAL** | **172,719** | **118 GB** | **1946-2025** | **✅ Operational** |

---

## RDS PostgreSQL

### Database: nba_simulator

| Table | Rows | Size | Purpose |
|-------|------|------|---------|
| game_events | 13.6M | 8.2 GB | Play-by-play data |
| player_box_scores | 2.1M | 1.5 GB | Player stats |
| team_box_scores | 65K | 120 MB | Team stats |
| games | 66K | 80 MB | Game metadata |
| ... | ... | ... | ... |

---

## Data Gaps

### Resolved Gaps ✅

1. ~~Box score players missing 2006-2025~~ → Found in hoopR (Oct 11)
2. ~~Lineup data missing 2007-2025~~ → Found in hoopR (Oct 11)

### Remaining Gaps 🟡

1. **MEDIUM:** S3 has 1,265 MORE team_stats files than local (sync needed)
2. **MEDIUM:** 8 RDS tables empty (need population from existing data)
3. **LOW:** Pre-1993 play-by-play incomplete (expected)

---

## Sync Status

| Location | S3 | RDS | Local | Status |
|----------|----|----|-------|--------|
| ESPN data | ✅ 146,115 | 🔄 Loading | ✅ 146,115 | In sync |
| hoopR data | ✅ 96 | ✅ 13.6M rows | ⚠️ 410 | Partial |
| Basketball Reference | ✅ 444 | 🔄 Loading | ✅ 444 | In sync |

---

## Action Items

| Priority | Action | Timeline | Owner |
|----------|--------|----------|-------|
| 🔴 HIGH | Sync 1,265 team_stats files from S3 to local | 1-2 hours | Data Ops |
| 🟡 MEDIUM | Populate 8 empty RDS tables | 1 week | DB Admin |
| 🟢 LOW | Archive pre-1993 incomplete data | 1 day | Data Ops |

\`\`\`

---

## Execution History

### First Audit (October 11, 2025)

**What was completed:**
- Phase 1: Internal project search (146,150 files found)
- Phase 2: External location discovery (1,223,071 files in 0espn repo)
- Phase 3: Database discovery (RDS + 3 SQLite databases)
- Phase 4: S3 complete inventory (172,600 files)

**Key Findings:**
- S3: 172,600 files (ESPN, NBA API, hoopR, Basketball Reference)
- RDS: 48.4M rows across 23 tables
- Local: 146,150 files + 3 databases
- External (0espn): 1.2M files (mostly duplicate + 151 unique)

**Critical Gaps Identified:**
1. 🔴 CRITICAL: Box score players missing 2006-2025 (19 seasons)
2. 🔴 CRITICAL: Lineup data missing 2007-2025 (18 seasons)

### Second Audit (October 11, 2025)

**Gap Resolution:**
- **Player Box Scores 2006-2025:** Found in hoopR (24 files parquet + 24 CSV, 2002-2025)
- **Lineup Data 2007-2024:** Found in hoopR (18 files CSV, 2007-2024)
- **Complete Coverage Achieved:** Player box scores (1995-2025), Lineups (1996-2024)

**Data Quality:**
- ESPN data: 100% valid (0% empty in sample)
- File consistency: All JSON files well-formed
- Database integrity: All tables accessible, no corruption

---

## Success Criteria

All criteria met:
- [x] All storage locations searched (local, S3, RDS, external)
- [x] Complete file inventory across all sources
- [x] Database row counts and schema documented
- [x] Data quality sampled and analyzed
- [x] Critical gaps identified with severity ratings
- [x] Sync status verified (local vs S3 vs RDS)
- [x] Master inventory documentation created
- [x] Reusable workflow documented for future audits
- [x] Zero cost (local analysis only)

---

## When to Run This Audit

**Execute Phase 0.0022:**
1. **After any new data acquisition** - Verify what was collected
2. **Before starting analysis** - Ensure you have complete data picture
3. **When planning scrapers** - Identify gaps to fill
4. **During troubleshooting** - Understand what data is actually available
5. **Quarterly reviews** - Verify sync status and identify drift
6. **Before cost optimization** - Identify duplicate data to clean up

**Expected frequency:**
- Initial: Once per sport/project
- Maintenance: Quarterly or after major data acquisitions
- Ad-hoc: When data completeness questions arise

---

## Integration with Existing Systems

### DIMS (Data Inventory Management System)
- Audit feeds DIMS metrics (inventory/metrics.yaml)
- DIMS tracks S3 object counts, file sizes
- Auto-verification detects drift

### ADCE (Autonomous Data Collection Ecosystem)
- Audit identifies gaps → ADCE fills gaps
- Gap resolution tracked in ADCE task queue
- Success measured by gap closure rate

### Phase 0.0020 (Monitoring)
- Audit metrics published to CloudWatch
- Alarms trigger on data quality drops
- Dashboard shows inventory trends

---

## Files to Create

**Audit Scripts:**
```
scripts/audit/discover_s3_data.sh           # S3 inventory
scripts/audit/discover_rds_data.sql         # RDS inventory
scripts/audit/discover_sqlite_data.sh       # SQLite inventory
scripts/audit/discover_local_data.sh        # Local file inventory
scripts/audit/discover_external_data.sh     # External repos
scripts/audit/sample_data_quality.py        # Quality sampling
scripts/audit/analyze_date_ranges.py        # Temporal coverage
scripts/audit/reconcile_sources.py          # Multi-source reconciliation
scripts/audit/identify_gaps.py              # Gap identification
scripts/audit/run_full_audit.sh             # Master script
```

**Documentation:**
```
docs/MASTER_DATA_INVENTORY.md               # Complete inventory (500+ lines)
docs/audit/AUDIT_RUNBOOK.md                 # How to run audits
docs/audit/GAP_RESOLUTION_GUIDE.md          # How to fill gaps
```

---

## Cost Breakdown

| Component | Configuration | Monthly Cost | Notes |
|-----------|--------------|--------------|-------|
| Local Analysis | MacBook Pro M2 Max | $0 | Existing hardware |
| S3 LIST Requests | ~50 requests | ~$0.00 | Minimal listing |
| RDS Connection | Existing db.t3.small | $0 | No additional cost |
| **Total Phase Cost** | | **$0/month** | Zero incremental cost |

**Development Time:** 2-4 hours per audit execution

---

## Prerequisites

**Before starting Phase 0.0022:**
- [x] At least one data collection phase complete (Phase 0)
- [x] AWS credentials configured
- [x] RDS instance accessible (if applicable)
- [ ] Knowledge of all potential data storage locations

**Note:** This phase can be run at any time to audit current data holdings.

---

## Common Issues & Solutions

### Issue 1: S3 LIST operations timeout
**Cause:** Too many objects (172K+)
**Solution:**
- Use `--page-size` parameter to reduce memory
```bash
aws s3 ls s3://bucket/ --recursive --page-size 1000 | wc -l
```

### Issue 2: RDS connection fails during audit
**Cause:** Security group or credentials issue
**Solution:**
- Check security group allows inbound from current IP
- Verify credentials in environment file
- Test with simple query first

### Issue 3: Local file count differs across runs
**Cause:** Files being added/modified during audit
**Solution:**
- Run audit during quiet periods
- Take snapshot with `rsync` before counting
- Document timestamp of audit

### Issue 4: External locations unknown
**Cause:** Data scattered across multiple locations
**Solution:**
- Search common locations (~/Downloads, ~/Desktop, external drives)
- Ask team members about data locations
- Check project documentation for old paths

---

## Workflows Referenced

- **Workflow #21:** Data Validation - Validation procedures
- **Workflow #2:** Command Logging - Documenting audit commands
- **Workflow #56:** DIMS Management - Metrics integration

---

## Related Documentation

**Inventory:**
- [DATA_CATALOG.md](../../../DATA_CATALOG.md) - Data source catalog
- [DATA_STRUCTURE_GUIDE.md](../../../DATA_STRUCTURE_GUIDE.md) - S3 bucket layout
- [DATA_SOURCE_BASELINES.md](../../../DATA_SOURCE_BASELINES.md) - Verified statistics

**Operations:**
- [AUTONOMOUS_OPERATION.md](../../../AUTONOMOUS_OPERATION.md) - ADCE system
- [SCRAPER_MONITORING_SYSTEM.md](../../../SCRAPER_MONITORING_SYSTEM.md) - Monitoring

---

## Navigation

**Return to:** [Phase 0 Index](../PHASE_0_INDEX.md)

**Prerequisites:** Phase 0.0001-0.0018 (Data collection complete)

**Integrates with:**
- Phase 0.0018: Autonomous Data Collection - Gap filling
- Phase 0.0020: Monitoring & Observability - Metrics publishing
- All data collection sub-phases - Validates completeness

---

## How This Enables the Simulation Vision

This sub-phase provides **data completeness assurance** that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this sub-phase enables:**

### 1. Econometric Causal Inference
From this sub-phase's audits, we can:
- **Ensure complete panel data** (no missing years/games that bias estimates)
- **Validate data quality** for regression (detect outliers/errors)
- **Document coverage** for robustness checks (which seasons are complete)

### 2. Nonparametric Event Modeling
From this sub-phase's inventory, we build:
- **Complete event sequences** (verified no gaps in play-by-play)
- **Quality-validated training data** (100% valid JSON in sample)
- **Multi-source cross-validation** (reconcile discrepancies across sources)

### 3. Context-Adaptive Simulations
Using this sub-phase's gap analysis, simulations can:
- **Adapt to data availability** (use alternate sources when primary missing)
- **Maintain accuracy** (detect and avoid incomplete/low-quality data)
- **Scale systematically** (identify which eras/teams have best coverage)

**See [main README](../../../README.md) for complete methodology.**

---

**Last Updated:** October 25, 2025 (Migrated from Phase 8)
**Status:** ✅ COMPLETE - Two audits executed successfully
**Migrated By:** Comprehensive Phase Reorganization (ADR-010)

**Next Execution:** After next major data acquisition or quarterly review

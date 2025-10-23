# Reconciliation Engine - ADCE Phase 2A MVP

**Status:** ✅ **MVP Complete** (Phase 2A)
**Created:** October 22, 2025
**Phase:** Autonomous Data Collection Ecosystem (ADCE) Phase 2

## Overview

The **Reconciliation Engine** is the core of the self-healing autonomous data collection system. It continuously compares what data we **SHOULD** have against what we **HAVE**, detects gaps, assigns priorities, and generates actionable collection tasks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              RECONCILIATION PIPELINE                         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  1. S3 Scanner      │  Scan S3 bucket → Build inventory
│  (HAVE)             │  MVP: 10% sample, Phase 2B: Full scan
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  2. Coverage        │  Compare HAVE vs SHOULD
│  Analyzer           │  Calculate completeness %
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  3. Gap Detector    │  Identify missing/stale data
│                     │  Assign priorities (CRITICAL → LOW)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  4. Task Generator  │  Convert gaps → scraper tasks
│                     │  Output: inventory/gaps.json
└─────────────────────┘
           │
           ▼
    (Phase 3: Orchestrator reads task queue)
```

## Quick Start

### Run Full Pipeline (Recommended)

```bash
# Run complete reconciliation (MVP with 10% sampling)
python scripts/reconciliation/run_reconciliation.py

# Use cached inventory (fast, skip S3 scan)
python scripts/reconciliation/run_reconciliation.py --use-cache

# Dry run (don't save task queue)
python scripts/reconciliation.py --dry-run
```

### Run Individual Components

```bash
# 1. Scan S3 (10% sample for MVP)
python scripts/reconciliation/scan_s3_inventory.py --sample-rate 0.1

# 2. Analyze coverage
python scripts/reconciliation/analyze_coverage.py

# 3. Detect gaps
python scripts/reconciliation/detect_data_gaps.py

# 4. Generate task queue
python scripts/reconciliation/generate_task_queue.py
```

## Components

### 1. S3 Inventory Scanner
**File:** `scan_s3_inventory.py`

Scans S3 bucket and builds structured inventory.

**Features:**
- Sample-based scanning (MVP: 10%)
- Full scan support (Phase 2B)
- Parse S3 paths to extract metadata
- Aggregate by source, season, data type
- Cache results (24-hour TTL)

**Output:** `inventory/cache/current_inventory.json`

```json
{
  "metadata": {
    "scan_timestamp": "2025-10-22T19:30:00Z",
    "total_objects_scanned": 172726,
    "total_objects_kept": 17273,
    "scan_mode": "sample"
  },
  "by_source": {"espn": {...}, "basketball_reference": {...}},
  "by_season": {"2024-25": {...}, "2023-24": {...}},
  "by_type": {"play_by_play": {...}, "box_scores": {...}}
}
```

---

### 2. Coverage Analyzer
**File:** `analyze_coverage.py`

Compares expected coverage (SHOULD) vs actual inventory (HAVE).

**Input:**
- Expected: `inventory/data_inventory.yaml`
- Actual: `inventory/cache/current_inventory.json`

**Output:** `inventory/cache/coverage_analysis.json`

```json
{
  "summary": {
    "overall_completeness_pct": 87.5,
    "sources_complete": 1,
    "sources_incomplete": 0,
    "total_missing_files": 450
  },
  "by_source": {
    "espn": {
      "completeness_pct": 87.5,
      "expected_files": 2640,
      "actual_files": 2310,
      "missing_files": 330
    }
  }
}
```

---

### 3. Gap Detector
**File:** `detect_data_gaps.py`

Identifies specific missing data and assigns priorities.

**Priority Levels:**
- **CRITICAL** (🔴): Recent games (< 7 days), urgent collection
- **HIGH** (🟡): Current season incomplete (< 95%)
- **MEDIUM** (🟢): Recent season gaps (2023-24)
- **LOW** (⚪): Historical backfill

**Output:** `inventory/cache/detected_gaps.json`

```json
{
  "summary": {
    "total_gaps": 15,
    "by_priority": {"critical": 3, "high": 5, "medium": 5, "low": 2}
  },
  "gaps": {
    "critical": [
      {
        "gap_type": "season_incomplete",
        "source": "espn",
        "season": "2024-25",
        "missing_files": 25,
        "stale_files": 10,
        "reason": "Current season has 10 stale files (>7 days old)"
      }
    ]
  }
}
```

---

### 4. Task Queue Generator
**File:** `generate_task_queue.py`

Converts gaps into executable scraper tasks.

**Output:** `inventory/gaps.json` (consumed by Phase 3 Orchestrator)

```json
{
  "generated_at": "2025-10-22T19:30:00Z",
  "total_tasks": 450,
  "by_priority": {"critical": 25, "high": 120, "medium": 205, "low": 100},
  "estimated_total_minutes": 900,
  "tasks": [
    {
      "id": "task_000001",
      "priority": "CRITICAL",
      "source": "espn",
      "season": "2024-25",
      "data_type": "play_by_play",
      "scraper": "espn_async_scraper",
      "missing_files": 25,
      "estimated_time_minutes": 50,
      "reason": "Current season has 10 stale files (>7 days old)",
      "status": "pending"
    }
  ]
}
```

---

## Configuration

**File:** `config/reconciliation_config.yaml`

```yaml
s3:
  bucket: nba-sim-raw-data-lake
  sample_rate: 0.1  # MVP: 10% sample
  cache_ttl_hours: 24

gap_detection:
  critical_threshold_days: 7
  high_priority_seasons: [2024-25]

task_queue:
  max_tasks_per_run: 1000
  output_file: inventory/gaps.json

dry_run:
  enabled: true  # MVP: Don't trigger actions
```

---

## Expected Coverage Definition

**File:** `inventory/data_inventory.yaml`

Defines what data we SHOULD have:

```yaml
expected_coverage:
  espn:
    seasons: [2023-24, 2024-25]
    data_types:
      play_by_play:
        required: true
        freshness_days: 7
        path_pattern: "nba_pbp/espn/{season}/play_by_play_{game_id}.json"
        completeness_threshold: 0.95

expected_game_counts:
  regular_season: 1230
  playoffs_max: 105
  total_max: 1335
```

---

## Output Files

| File | Purpose | Used By |
|------|---------|---------|
| `inventory/data_inventory.yaml` | Expected coverage definition | Coverage Analyzer |
| `inventory/cache/current_inventory.json` | S3 scan results (HAVE) | Coverage Analyzer |
| `inventory/cache/coverage_analysis.json` | HAVE vs SHOULD comparison | Gap Detector |
| `inventory/cache/detected_gaps.json` | Identified gaps with priorities | Task Generator |
| `inventory/gaps.json` | **Task queue for orchestrator** | **Phase 3 Orchestrator** |

---

## Performance

**MVP Targets (Phase 2A):**
- S3 scan (10% sample): < 5 minutes
- Coverage analysis: < 30 seconds
- Gap detection: < 60 seconds
- Task generation: < 30 seconds
- **Full cycle: < 10 minutes**

**Phase 2B Targets (Full Implementation):**
- S3 scan (AWS Inventory): < 2 minutes
- Full cycle: < 5 minutes

---

## Testing

```bash
# Test S3 scanner
python scripts/reconciliation/scan_s3_inventory.py --sample-rate 0.01 --dry-run

# Test coverage analyzer (requires inventory)
python scripts/reconciliation/analyze_coverage.py --dry-run

# Test gap detector (requires coverage analysis)
python scripts/reconciliation/detect_data_gaps.py --dry-run

# Test task generator (requires gaps)
python scripts/reconciliation/generate_task_queue.py --dry-run

# Test full pipeline
python scripts/reconciliation/run_reconciliation.py --use-cache --dry-run
```

---

## Integration with DIMS

The reconciliation engine integrates with the Data Inventory Management System (DIMS):

```bash
# DIMS will track these metrics:
- reconciliation.last_run
- reconciliation.total_gaps
- reconciliation.critical_gaps
- reconciliation.task_queue_size
- reconciliation.estimated_time_minutes
```

---

## Phase Roadmap

### ✅ Phase 2A: MVP (Current)
- ESPN data only
- Sample-based S3 scanning (10%)
- Manual execution
- Dry-run mode (no automation)
- **Status:** Complete

### Phase 2B: Full Implementation (Next)
- All 4 sources (ESPN, Basketball Reference, NBA API, Hoopr)
- AWS S3 Inventory integration
- Automated reconciliation loop
- DIMS event integration
- Live task queue updates

### Phase 3: Scraper Orchestrator (Future)
- Read `inventory/gaps.json`
- Schedule scrapers by priority
- Execute collection tasks
- Update inventory after completion
- Trigger new reconciliation

### Phase 4: Autonomous Loop (Future)
- 24/7 self-healing cycle
- Zero manual intervention
- Automatic gap detection & collection
- Comprehensive monitoring

---

## Troubleshooting

**Error: "No cached inventory found"**
```bash
# Run S3 scan first
python scripts/reconciliation/scan_s3_inventory.py
```

**Error: "Coverage analysis file not found"**
```bash
# Run full pipeline instead of individual components
python scripts/reconciliation/run_reconciliation.py
```

**Slow S3 scan (> 5 minutes)**
```bash
# Use lower sample rate for MVP
python scripts/reconciliation/scan_s3_inventory.py --sample-rate 0.05

# Or use cached inventory
python scripts/reconciliation/run_reconciliation.py --use-cache
```

**Task queue not generated**
```bash
# Check dry-run mode
python scripts/reconciliation/generate_task_queue.py  # Without --dry-run
```

---

## Related Documentation

- `reports/dims_phase2_readiness_report.md` - Phase 2 readiness assessment
- `inventory/data_inventory.yaml` - Expected coverage schemas
- `config/reconciliation_config.yaml` - Configuration reference
- `docs/ADCE_ROADMAP.md` - Full ADCE architecture

---

## Support

For issues or questions:
1. Check logs: `logs/reconciliation/`
2. Review configuration: `config/reconciliation_config.yaml`
3. Validate expected schemas: `inventory/data_inventory.yaml`
4. Test individual components with `--dry-run`

---

**Last Updated:** October 22, 2025
**Version:** 0.1-MVP (Phase 2A)
**Next Phase:** 2B - Full Implementation


# Sub-Phase 0.0024: 3-Source Validation Workflow

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ✅ COMPLETE
**Priority:** ⭐ HIGH
**Implementation ID:** `workflow_modernization_0.0024`
**Completed:** [Date TBD]

---

## Overview

Simplified overnight workflow for cross-validating 3 data sources: ESPN, hoopR, and NBA API. This workflow replaces the shell script `scripts/workflows/overnight_3_source_validation.sh` with a production-grade Python implementation.

**Migration Details:**
- **Original:** `overnight_3_source_validation.sh` (259 lines)
- **New:** `validation_workflow.py` (Python class-based)
- **Benefits:** Graceful degradation, better error tracking, DIMS integration

---

## Capabilities

### Core Workflow Steps

1. **Scrape ESPN Data** - Last 3 days of games
2. **Scrape hoopR Data** - Last 3 days of games
3. **Scrape NBA API Data** - Last 3 days of games
4. **Scrape Basketball Reference** - Current season aggregates
5. **Cross-Validate All Sources** - Detect discrepancies across all 3 sources

### Graceful Degradation

- **All scraping steps are non-fatal** - Workflow continues even if sources fail
- **Cross-validation requires ≥2 sources** - Skips validation if too many sources fail
- **Failure threshold:** 2 sources (workflow continues if ≤2 sources fail)

---

## Quick Start

```bash
# Run workflow
python scripts/workflows/validation_cli.py

# Dry run
python scripts/workflows/validation_cli.py --dry-run

# Custom days back
python scripts/workflows/validation_cli.py --days 7
```

---

## Architecture

### Task Graph

```
Initialize
    ↓
├─ ESPN Scrape (3 days) ──────┐
├─ hoopR Scrape (3 days) ─────┤
├─ NBA API Scrape (3 days) ───┤
└─ Basketball Ref Scrape ─────┤
                               ↓
                    Cross-Validate (requires ≥2 sources)
                               ↓
                          Shutdown
```

---

## Configuration

```yaml
# config/default_config.yaml
project_dir: /Users/ryanranft/nba-simulator-aws
log_dir: logs/overnight
reports_dir: reports/validation

scraping:
  days_back: 3  # Always 3 days for validation

dims:
  enabled: true
```

---

## Implementation Files

| File | Purpose | Lines |
|------|---------|-------|
| `validation_workflow.py` | Main workflow class | ~400 |
| `config/default_config.yaml` | Default configuration | ~20 |
| `test_validation.py` | Tests | ~200 |
| CLI: `scripts/workflows/validation_cli.py` | Command-line interface | ~150 |

---

## Related Documentation

- [0.0023: Overnight Unified Workflow](../0.0023_overnight_unified/README.md)
- [Workflow #39: Scraper Monitoring](../../../claude_workflows/workflow_descriptions/39_monitoring_automation.md)

---

## Navigation

**Parent:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)
**Prerequisites:** [0.0001](../0.0001_initial_data_collection/README.md), [0.0002](../0.0002_hoopr_data_collection/README.md)
**Integrates With:** [0.0018 (ADCE)](../0.0018_autonomous_data_collection/README.md)

---

**Last Updated:** [Date TBD]
**Version:** 2.0.0 (Python migration from shell v2.0)
**Maintained By:** NBA Simulator AWS Team

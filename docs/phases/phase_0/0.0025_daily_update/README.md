# Sub-Phase 0.0025: Daily ESPN Update Workflow

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ✅ COMPLETE
**Priority:** ⭐ HIGH
**Implementation ID:** `workflow_modernization_0.0025`
**Completed:** [Date TBD]

---

## Overview

Automated daily ESPN data collection, processing, and catalog updates. This workflow replaces the shell script `scripts/workflows/daily_espn_update.sh` with a production-grade Python implementation.

**Migration Details:**
- **Original:** `daily_espn_update.sh` (391 lines)
- **New:** `daily_update_workflow.py` (Python class-based)
- **Benefits:** Better error handling, Slack integration, structured logging

---

## Capabilities

### Core Workflow Steps

1. **Pre-Flight Checks** - Validate environment, paths, conda activation
2. **Trigger ESPN Scraper** (Optional) - Scrape last 2 days of games
3. **Update Local Database** - Rebuild SQLite from S3 data
4. **Update Data Catalog** - Update DATA_CATALOG.md with latest statistics
5. **Git Commit** (Optional) - Auto-commit catalog changes
6. **Cleanup** - Remove old logs (7-day retention)

### Features

- **Slack Notifications** - Send updates via webhook (optional)
- **Database Diff Tracking** - Log before/after game/event counts
- **Catalog Verification** - Validate catalog consistency
- **Auto-Commit** - Optional git commit with timestamp
- **Colored Output** - Visual feedback in terminal

---

## Quick Start

```bash
# Run workflow
python scripts/workflows/daily_update_cli.py

# Dry run
python scripts/workflows/daily_update_cli.py --dry-run

# Enable scraper trigger
python scripts/workflows/daily_update_cli.py --trigger-scraper

# Enable auto-commit
python scripts/workflows/daily_update_cli.py --auto-commit
```

---

## Configuration

```yaml
# config/default_config.yaml
project_dir: /Users/ryanranft/nba-simulator-aws
log_dir: /tmp
espn_scraper_dir: ~/0espn
local_db: /tmp/espn_local.db

catalog:
  file: docs/DATA_CATALOG.md
  update_script: scripts/utils/update_data_catalog.py

git:
  auto_commit: false  # Enable to auto-commit catalog changes

notification:
  slack_webhook: ""  # Optional Slack webhook URL

cleanup:
  log_retention_days: 7
```

---

## Implementation Files

| File | Purpose | Lines |
|------|---------|-------|
| `daily_update_workflow.py` | Main workflow class | ~500 |
| `config/default_config.yaml` | Default configuration | ~30 |
| CLI: `scripts/workflows/daily_update_cli.py` | Command-line interface | ~150 |

---

## Related Documentation

- [0.0023: Overnight Unified Workflow](../0.0023_overnight_unified/README.md)
- [DATA_CATALOG.md](../../../../docs/DATA_CATALOG.md)

---

## Navigation

**Parent:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)
**Prerequisites:** [0.0001](../0.0001_initial_data_collection/README.md)
**Integrates With:** [0.0018 (ADCE)](../0.0018_autonomous_data_collection/README.md)

---

**Last Updated:** [Date TBD]
**Version:** 2.0.0 (Python migration from shell)
**Maintained By:** NBA Simulator AWS Team

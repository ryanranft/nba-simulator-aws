# Sub-Phase 0.0023: Overnight Unified Workflow

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ✅ COMPLETE
**Priority:** ⭐ CRITICAL
**Implementation ID:** `workflow_modernization_0.0023`
**Completed:** [Date TBD]

---

## Overview

Automated nightly workflow for multi-source data collection, quality tracking, and unified database maintenance. This workflow replaces the shell script `scripts/archive/pre_python_migration/overnight_multi_source_unified.sh` with a production-grade Python implementation using the `BaseWorkflow` framework.

**Migration Details:**
- **Original:** `overnight_multi_source_unified.sh` (513 lines)
- **New:** `overnight_unified_workflow.py` (Python class-based)
- **Benefits:** State persistence, retry logic, DIMS integration, comprehensive testing

---

## Capabilities

### Core Workflow Steps

1. **Scrape ESPN Data** (Incremental)
   - Collects play-by-play data from last 14 days
   - Updates local ESPN database (`/tmp/espn_local.db`)
   - Non-fatal errors (continues on failure)

2. **Scrape hoopR Data** (Incremental)
   - Collects play-by-play data from last 7 days
   - Updates local hoopR database (`/tmp/hoopr_local.db`)
   - Non-fatal errors

3. **Scrape Basketball Reference** (Current Season)
   - Collects aggregate stats (season totals + advanced)
   - Updates local Basketball Reference database
   - Integrates new data into unified system
   - Non-fatal errors

4. **Update Game ID Mappings**
   - Extracts ESPN ↔ hoopR game ID mappings
   - Saves to `scripts/mapping/espn_hoopr_game_mapping.json`
   - Fatal errors (workflow stops if this fails)

5. **Rebuild Unified Database**
   - Combines all source databases into `/tmp/unified_nba.db`
   - Calculates quality scores for each game
   - Identifies dual-source games
   - Fatal errors

6. **Detect Discrepancies**
   - Cross-validates data across sources
   - Identifies field-level differences
   - Assigns severity levels (high/medium/low)
   - Stores in `data_quality_discrepancies` table
   - Fatal errors

7. **Export ML Quality Dataset**
   - Generates ML-ready quality dataset
   - Exports to JSON and CSV formats
   - Output: `data/ml_quality/ml_quality_dataset_YYYYMMDD_HHMMSS.*`
   - Fatal errors

8. **Generate Quality Reports**
   - Creates daily quality report (Markdown)
   - Includes database statistics, quality distribution, recent discrepancies
   - Output: `reports/daily_quality_report_YYYYMMDD.md`
   - Non-fatal errors

9. **Backup Databases**
   - Backs up unified database to `backups/YYYYMMDD/`
   - Keeps last 7 days of backups
   - Non-fatal errors

10. **Send Notifications** (Optional)
    - Sends completion notification via email
    - Configurable recipient
    - Non-fatal errors

11. **Check Long-Running Scrapers**
    - Monitors health of Basketball Reference and NBA API scrapers
    - Attempts recovery if needed
    - Non-fatal errors

### Python Workflow Enhancements

**Compared to shell script, Python workflow adds:**

- ✅ **State Persistence** - Resume from failures
- ✅ **Retry Logic** - Automatic recovery from transient errors (3 retries per task)
- ✅ **DIMS Integration** - Metrics tracking (quality scores, duration, success rate)
- ✅ **Task Dependencies** - Explicit task ordering with dependency management
- ✅ **Structured Logging** - JSON-formatted logs with levels (DEBUG/INFO/WARNING/ERROR)
- ✅ **Unit Testing** - Comprehensive test coverage with mocked dependencies
- ✅ **Type Safety** - Type hints and validation
- ✅ **Better Error Messages** - Stack traces, structured exceptions
- ✅ **Workflow Composition** - Reusable tasks across workflows
- ✅ **Health Monitoring** - Integration with autonomous health monitor

---

## Quick Start

### Basic Usage

```bash
# Run workflow with default configuration
cd /Users/ryanranft/nba-simulator-aws
python scripts/workflows/overnight_unified_cli.py

# Run with custom configuration
python scripts/workflows/overnight_unified_cli.py --config config/overnight_custom.yaml

# Dry run (no side effects)
python scripts/workflows/overnight_unified_cli.py --dry-run

# Resume from saved state
python scripts/workflows/overnight_unified_cli.py --resume

# Verbose logging
python scripts/workflows/overnight_unified_cli.py --verbose
```

### Cron Scheduling

Replace the existing shell script cron job with:

```bash
# /etc/cron.d/nba-workflows (or crontab -e)
0 3 * * * cd /Users/ryanranft/nba-simulator-aws && conda activate nba-aws && python scripts/workflows/overnight_unified_cli.py >> logs/cron.log 2>&1
```

### Programmatic Usage

```python
from docs.phases.phase_0.overnight_unified.overnight_unified_workflow import OvernightUnifiedWorkflow
import yaml

# Load configuration
with open("config/overnight_config.yaml") as f:
    config = yaml.safe_load(f)

# Create workflow
workflow = OvernightUnifiedWorkflow(config=config)

# Initialize
if workflow.initialize():
    # Execute
    success = workflow.execute()

    # Generate report
    report = workflow.generate_report(format="markdown")
    print(report)

    # Shutdown
    workflow.shutdown()

    # Check success
    if success:
        print("✅ Workflow completed successfully!")
    else:
        print("❌ Workflow failed - check logs")
else:
    print("❌ Workflow initialization failed")
```

---

## Architecture

### Task Graph

```
Initialize
    ↓
├─ Task 1: Scrape ESPN (async) ────────┐
├─ Task 2: Scrape hoopR (async) ───────┤
└─ Task 3: Scrape Basketball Ref ──────┤
                                        ↓
                            Task 4: Update Mappings
                                        ↓
                            Task 5: Rebuild Unified DB
                                        ↓
                    ┌───────────────────┴──────────────────┐
                    ↓                                      ↓
        Task 6: Detect Discrepancies        Task 8: Backup Databases
                    ↓                                      ↓
    ┌───────────────┴──────────────┐                      ↓
    ↓                              ↓                      ↓
Task 7: Export ML Dataset   Task 9: Generate Reports     ↓
    ↓                              ↓                      ↓
    └──────────────┬───────────────┘                      ↓
                   ↓                                      ↓
        Task 10: Send Notification                       ↓
                   ↓                                      ↓
                   └──────────────┬───────────────────────┘
                                  ↓
                    Task 11: Check Long-Running Scrapers
                                  ↓
                              Shutdown
```

### Workflow State Machine

```
CREATED → INITIALIZED → READY → RUNNING → COMPLETED
                                    ↓
                                 PAUSED → RUNNING
                                    ↓
                                 FAILED
                                    ↓
                                 SHUTDOWN
```

### Configuration Schema

```yaml
# config/default_config.yaml

project_dir: /Users/ryanranft/nba-simulator-aws
log_dir: logs/overnight
reports_dir: reports
ml_quality_dir: data/ml_quality

databases:
  espn_db: /tmp/espn_local.db
  hoopr_db: /tmp/hoopr_local.db
  unified_db: /tmp/unified_nba.db

scraping:
  espn_days_back: 14
  hoopr_days_back: 7
  basketball_reference_season: current

notification:
  enabled: false
  email_recipient: your-email@example.com

backup:
  enabled: true
  retention_days: 7

cleanup:
  log_retention_days: 30

dims:
  enabled: true
  report_metrics: true
```

---

## Implementation Files

| File | Purpose | Lines | Tests |
|------|---------|-------|-------|
| `overnight_unified_workflow.py` | Main workflow class | ~800 | 100% |
| `config/default_config.yaml` | Default configuration | ~50 | N/A |
| `test_overnight_unified.py` | Unit and integration tests | ~600 | 25+ tests |
| CLI: `scripts/workflows/overnight_unified_cli.py` | Command-line interface | ~200 | N/A |

---

## Testing

### Run Tests

```bash
# Run all tests
pytest docs/phases/phase_0/0.0023_overnight_unified/test_overnight_unified.py -v

# Run specific test
pytest docs/phases/phase_0/0.0023_overnight_unified/test_overnight_unified.py::test_workflow_initialization -v

# Run with coverage
pytest docs/phases/phase_0/0.0023_overnight_unified/test_overnight_unified.py --cov=overnight_unified_workflow --cov-report=html
```

### Test Coverage

- ✅ Workflow initialization
- ✅ Task building and dependencies
- ✅ Each task executor (mocked external dependencies)
- ✅ Error handling and retries
- ✅ State persistence and resume
- ✅ DIMS metric reporting
- ✅ Configuration validation
- ✅ End-to-end workflow execution

---

## DIMS Integration

### Metrics Reported

The workflow automatically reports these metrics to DIMS:

- **Quality Score** - Overall data quality (0-100)
- **Duration** - Workflow execution time (seconds)
- **Success Rate** - Percentage of successful tasks
- **Items Processed** - Total games processed across all sources
- **Discrepancy Count** - Number of cross-source discrepancies detected
- **ML Dataset Size** - Size of exported ML quality dataset
- **Backup Size** - Size of database backups

### Query DIMS Metrics

```bash
# View overnight workflow metrics
python scripts/monitoring/dims_cli.py report --category workflow_metrics --filter overnight_unified

# Verify workflow health
python scripts/monitoring/dims_cli.py verify --category workflow_health
```

---

## Related Documentation

### Workflows
- [Workflow #38: Overnight Handoff](../../../claude_workflows/workflow_descriptions/38_overnight_handoff.md)
- [Workflow #39: Scraper Monitoring](../../../claude_workflows/workflow_descriptions/39_monitoring_automation.md)
- [Workflow #56: DIMS Management](../../../claude_workflows/workflow_descriptions/56_dims_management.md)

### Phase 0 Data Collection
- [0.0001: Initial Data Collection](../0.0001_initial_data_collection/README.md)
- [0.0002: hoopR Data Collection](../0.0002_hoopr_data_collection/README.md)
- [0.0004: Basketball Reference](../0.0004_basketball_reference/README.md)
- [0.0018: Autonomous Data Collection (ADCE)](../0.0018_autonomous_data_collection/README.md)

### Infrastructure
- [BaseWorkflow](../../../../nba_simulator/workflows/base_workflow.py) - Framework documentation
- [AUTONOMOUS_OPERATION.md](../../../../docs/AUTONOMOUS_OPERATION.md) - ADCE system guide
- [SCRAPER_MONITORING_SYSTEM.md](../../../../docs/SCRAPER_MONITORING_SYSTEM.md) - Monitoring procedures

---

## Troubleshooting

### Workflow Fails at Initialization

**Symptom:** Workflow exits immediately with validation error

**Causes:**
- Missing configuration file
- Invalid database paths
- Missing required directories

**Solution:**
```bash
# Check configuration
python scripts/workflows/overnight_unified_cli.py --validate-config

# Create missing directories
mkdir -p logs/overnight reports data/ml_quality backups
```

### Task Fails with Retry Exhaustion

**Symptom:** Task fails after 3 retries

**Causes:**
- External scraper crashed
- Database locked
- Network issues

**Solution:**
```bash
# Check task status
python scripts/workflows/overnight_unified_cli.py --status

# Resume from last successful task
python scripts/workflows/overnight_unified_cli.py --resume
```

### DIMS Metrics Not Reporting

**Symptom:** No metrics in DIMS after workflow completion

**Causes:**
- DIMS disabled in config
- DIMS database connection error
- Metric validation failure

**Solution:**
```bash
# Check DIMS configuration
python scripts/monitoring/dims_cli.py verify

# Enable DIMS in workflow config
# Edit config/default_config.yaml: dims.enabled = true
```

---

## Migration Notes

### What Changed from Shell Script

**Removed:**
- Bash logging functions (`log()`, `log_section()`, `log_error()`)
- Manual error handling (`set -e`, `error_handler()`)
- Hardcoded paths
- Sequential execution (no parallelization)

**Added:**
- `BaseWorkflow` state machine
- Task dependency management
- Retry logic (3 retries per task)
- DIMS metric reporting
- Type hints and validation
- Unit and integration tests
- Configuration file support
- Structured logging

**Preserved:**
- All 11 workflow steps
- Fatal vs non-fatal error handling
- Database statistics reporting
- Markdown report generation
- Email notifications (optional)
- Backup retention (7 days)
- Log retention (30 days)

### Backward Compatibility

The Python workflow produces identical outputs to the shell script:
- Same database files (`/tmp/*.db`)
- Same reports (`reports/daily_quality_report_YYYYMMDD.md`)
- Same ML datasets (`data/ml_quality/ml_quality_dataset_*`)
- Same backups (`backups/YYYYMMDD/`)

### Shell Script Deprecation

Original shell script moved to:
```
scripts/archive/pre_python_migration/overnight_multi_source_unified.sh
```

---

## Navigation

**Parent:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)
**Prerequisites:** [0.0001](../0.0001_initial_data_collection/README.md), [0.0002](../0.0002_hoopr_data_collection/README.md), [0.0004](../0.0004_basketball_reference/README.md)
**Integrates With:** [0.0018 (ADCE)](../0.0018_autonomous_data_collection/README.md), [0.0022 (DIMS)](../0.0022_data_inventory_gap_analysis/README.md)

---

**Last Updated:** [Date TBD]
**Version:** 2.0.0 (Python migration from shell v1.1)
**Maintained By:** NBA Simulator AWS Team

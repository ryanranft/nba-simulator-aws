# Workflow #41: Testing Framework

**Purpose:** Execute test suites for data validation, monitoring system verification, and feature engineering readiness

**When to use:**
- Before deploying new scrapers (monitoring tests)
- After completing data loads (temporal query tests)
- Before running SageMaker notebooks (feature engineering tests)
- During validation phases (data quality checks)

---

## Overview

This workflow integrates three comprehensive test suites that validate different aspects of the NBA temporal panel data system:

1. **Scraper Monitoring System Tests** - Validate overnight scraper workflow end-to-end
2. **Temporal Panel Data Query Tests** - Validate millisecond-precision temporal queries
3. **Feature Engineering Validation Tests** - Pre-flight validation for SageMaker deployment

Each test suite serves a specific purpose and should be run at appropriate points in the development workflow.

---

## Test Suite 1: Scraper Monitoring System Tests

### Purpose
Validate the hybrid monitoring system for long-running overnight scrapers, ensuring completions are never missed and context is preserved across sessions.

### Location
```bash
scripts/monitoring/test_monitoring_system.sh
```

### Usage

**Standard mode:**
```bash
bash scripts/monitoring/test_monitoring_system.sh
```

**Verbose mode (recommended for first run):**
```bash
bash scripts/monitoring/test_monitoring_system.sh --verbose
```

### What It Tests (10 Categories)

**1. Daemon Script Validation**
- Script existence at expected location
- Execute permissions set correctly
- Command interface responds correctly (start/stop/status commands)

**2. Reminder File Creation**
- Reminder file created with unique run ID
- Required fields present (SCRAPER, PID, LOG, START_TIME, EXPECTED_COMPLETION)
- File format validation

**3. Alert File Creation**
- Alert file created on scraper completion
- Required fields present (SCRAPER, COMPLETION_TIME, STATUS, ERRORS, LOG)
- File format validation

**4. Alert Checking Functionality**
- `check_scraper_alerts.sh` detects completed scrapers
- Shows completion time
- Displays scraper names correctly

**5. Completion Analysis**
- `analyze_scraper_completion.sh` provides recommendations
- Analyzes error count correctly
- Returns COMPLETE for successful runs
- Returns INVESTIGATE for runs with errors

**6. Error Handling & Recommendations**
- Detects errors in scraper logs
- Recommends INVESTIGATE when errors present
- Shows correct error count (e.g., "2 errors")

**7. Context Preservation**
- `save_work_context.sh` creates JSON file
- Valid JSON format validation (using Python json.tool)
- Required fields present (task, current_step, next_step, timestamp)

**8. Script Permissions**
- All 6 monitoring scripts are executable:
  - check_scraper_alerts.sh
  - analyze_scraper_completion.sh
  - save_work_context.sh
  - scraper_watcher_daemon.sh
  - launch_scraper.sh
  - monitor_scrapers_inline.sh

**9. Directory Structure**
- `/tmp/scraper_alerts/` exists
- `/tmp/scraper_reminders/` exists

**10. End-to-End Integration**
- Full workflow: reminder → log → alert → analysis → context
- 6-step integration test validates complete lifecycle

### Test Architecture

**Test Isolation:**
- Uses unique run IDs (`test_$(date +%s)_$$`) to prevent file conflicts
- Backs up existing alerts/reminders before tests
- Non-destructive (removed `set -e` to allow test failures without aborting suite)
- Automatic cleanup with pkill safety checks (uses pgrep first)

**Output:**
- Color-coded results (GREEN for pass, RED for fail, CYAN for headers)
- Pass rate calculation
- Per-test status reporting
- Summary at end with total passed/failed

### Pass Criteria
- All 10 test categories pass
- 100% pass rate expected
- If any tests fail, review output and fix before using monitoring system

### Runtime
30-60 seconds

### When to Run

**Before:**
- Launching first overnight scraper
- Deploying monitoring infrastructure changes
- Making changes to alert/reminder file formats

**After:**
- Making changes to monitoring scripts
- Updating daemon logic
- Modifying completion analysis recommendations

**Frequency:** Once per deployment, or when modifying monitoring system

---

## Test Suite 2: Temporal Panel Data Query Tests

### Purpose
Validate that temporal query functionality works correctly with millisecond-precision timestamps, snapshot queries, and age calculations. Ensures data quality and query performance meet requirements.

### Location
```bash
tests/test_temporal_queries.py
```

### Prerequisites

**Required tables:**
- `temporal_events` (populated with event data)
- `player_snapshots` (populated with snapshot data)
- `game_states` (populated with game state data)
- `player_biographical` (populated with player metadata)

**Configuration:**
Update `TEST_DB_CONFIG` in the test file with your RDS credentials:
```python
TEST_DB_CONFIG = {
    'host': 'nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com',
    'database': 'nba_simulator',
    'user': 'your_user',
    'password': 'your_password'
}
```

**Test data:**
- Test player: Kobe Bryant (ID 977, last game 2016-06-19)
- Requires at least one complete game with events

### Usage

**Run all tests:**
```bash
pytest tests/test_temporal_queries.py -v
```

**Run specific test class:**
```bash
pytest tests/test_temporal_queries.py::TestSnapshotQueries -v
```

**Run with detailed output:**
```bash
pytest tests/test_temporal_queries.py -v --tb=short
```

### What It Tests (25+ Tests Across 8 Classes)

**Class 1: TestTemporalDataAvailability**
- `temporal_events` table exists
- `player_snapshots` table exists
- `game_states` table exists
- `player_biographical` table exists
- Tables contain data (COUNT(*) > 0)

**Class 2: TestBRINIndexes**
- BRIN index on `temporal_events.wall_clock_utc` exists
- BRIN index on `player_snapshots.snapshot_time` exists
- Indexes improve query performance for time-range queries

**Class 3: TestStoredProcedures**
- `get_player_snapshot_at_time()` function exists
- `calculate_player_age()` function exists
- Functions can be called successfully

**Class 4: TestSnapshotQueries**
- Retrieve player snapshot at exact timestamp
- Snapshot time <= requested time (temporal consistency)
- Games played > 0 (data sanity)
- Career points > 0 (data sanity)
- Query performance < 5 seconds
- Snapshot monotonicity (career stats never decrease over time)

**Class 5: TestPrecisionLevels**
- Precision level values are valid (millisecond, second, minute, game, unknown)
- Modern data (2020+) has >80% second or better precision
- Data source tracking populated correctly (nba_live, nba_stats, espn, hoopr, basketball_ref, kaggle)

**Class 6: TestAgeCalculations**
- Birth date available for test player
- Birth date precision valid (day, month, year)
- Age calculation returns valid string (contains "years")
- Age precision matches birth date precision

**Class 7: TestTimestampConsistency**
- Wall clock and game clock relationship valid
- Game clock seconds in range 0-720 (12-minute quarters)
- Quarter numbers valid (1-4 or higher for overtime)
- Timestamps are timezone-aware (TIMESTAMPTZ)

**Class 8: TestGameStateReconstruction**
- Retrieve game state at specific timestamp
- Home score >= 0
- Away score >= 0
- Quarter numbers valid

**Class 9: TestDataQualityValidation**
- No duplicate events at same timestamp
- Snapshot consistency with raw events (5% tolerance allowed)

**Class 10: TestPerformanceBenchmarks**
- Time-range query performance < 10 seconds (benefits from BRIN index)
- Career aggregation performance < 15 seconds

### Test Architecture

**Fixtures:**
- Module-scope database connection (reused across tests)
- Cursor creation and cleanup
- Timezone-aware datetime handling using `pytz`

**Performance Targets:**
- Snapshot queries: < 5 seconds
- Time-range queries: < 10 seconds
- Career aggregation: < 15 seconds

**Data Validation:**
- Valid data sources: `{nba_live, nba_stats, espn, hoopr, basketball_ref, kaggle}`
- Precision levels: millisecond, second, minute, game, unknown
- Birth date precision: day, month, year

### Pass Criteria
- All pytest tests pass
- Performance benchmarks met
- No data quality issues detected

### Runtime
1-3 minutes (depending on database size and query complexity)

### When to Run

**Before:**
- Running temporal queries in production
- Building snapshot-based ML features
- Deploying temporal data pipeline changes

**After:**
- Loading `temporal_events` data
- Creating new snapshot generation jobs
- Database schema changes affecting temporal tables

**Frequency:** Weekly during active temporal development, monthly in maintenance mode

---

## Test Suite 3: Feature Engineering Validation Tests

### Purpose
Pre-flight validation for SageMaker notebook deployment. Ensures all dependencies are available, connections work, and feature calculation logic is correct before running expensive cloud operations.

### Location
```bash
notebooks/test_feature_engineering.py
```

### Prerequisites

**Environment variables:**
```bash
export NBA_SIM_DB_PASSWORD="your_rds_password"
```

**AWS credentials:**
- Configured in `~/.aws/credentials`
- Access to `nba-sim-raw-data-lake` S3 bucket

**Database:**
- RDS instance running
- `games` table populated with data

### Usage

**Run validation:**
```bash
python notebooks/test_feature_engineering.py
```

**Check exit code:**
```bash
python notebooks/test_feature_engineering.py
echo $?  # 0 = success, 1 = failure
```

### What It Tests (5 Categories)

**1. Import Test**
Required packages:
- pandas
- numpy
- psycopg2
- sqlalchemy
- boto3

Shows ✓ for available packages, ✗ for missing packages with install command.

**2. Database Connection Test**
- Connects to RDS PostgreSQL
- Verifies `games` table is accessible
- Shows row count
- Uses 5-second connection timeout
- Skips test if `NBA_SIM_DB_PASSWORD` not set (warns instead of failing)

**3. S3 Access Test**
- Tests read access to `s3://nba-sim-raw-data-lake`
- Lists objects with prefix `schedule/`
- Verifies at least one object found
- Shows object count

**4. Feature Logic Test**
Creates sample data and validates:
- Rolling stats calculation (10-game window, no NaN values)
- Rest days calculation (no negative values, fillna(7) for first game)
- Categorical encoding (month 1-12, day_of_week valid)

**5. Parquet I/O Test**
- Creates sample DataFrame
- Writes to temporary Parquet file
- Reads back and validates equality
- Uses pyarrow engine
- Cleans up temp file

### Test Results Output

```
======================================================================
FEATURE ENGINEERING NOTEBOOK - VALIDATION TESTS
======================================================================

Testing imports...
  ✓ pandas
  ✓ numpy
  ✓ psycopg2
  ✓ sqlalchemy
  ✓ boto3
✓ All imports available

Testing database connection...
  ✓ Connected to RDS
  ✓ Games table accessible (44,828 rows)

Testing S3 access...
  ✓ S3 read access confirmed
  ✓ Found 5 objects

Testing feature engineering logic...
  ✓ Rolling stats calculation works
  ✓ Rest days calculation works
  ✓ Categorical encoding works
  ✓ All feature logic validated

Testing Parquet write capability...
  ✓ Parquet write/read works

======================================================================
TEST SUMMARY
======================================================================
✓ PASS   - Import Test
✓ PASS   - Database Connection
✓ PASS   - S3 Access
✓ PASS   - Feature Logic
✓ PASS   - Parquet Write

Results: 5/5 tests passed

✓ All tests passed - notebook is ready for SageMaker
```

### Key Validations

**Rolling stats:**
- 10-game window calculation
- No NaN values in results
- Correct moving average computation

**Rest days:**
- Difference in game dates (days apart)
- Subtract 1 to get rest days
- fillna(7) for first game of season (no previous game)
- No negative values allowed

**Categorical encoding:**
- Month extraction (1-12)
- Day of week extraction (0-6)
- Valid ranges verified

**Parquet roundtrip:**
- DataFrame equality after write/read
- No data loss
- No type coercion issues

### Exit Codes
- **0**: All tests passed, ready for SageMaker deployment
- **1**: Failures detected, fix issues before running notebook

### Runtime
10-30 seconds

### When to Run

**Before:**
- Launching SageMaker notebooks
- Deploying feature engineering pipelines
- Making changes to feature calculation logic

**After:**
- Database schema updates
- S3 bucket permission changes
- Library version updates (pandas, numpy, pyarrow)

**Frequency:** Before each SageMaker session, after environment changes

---

## Integration with Existing Workflows

### Workflow #16 (Testing)
- Update to reference Workflow #41 for detailed test procedures
- Add links to these specific test scripts
- Include test result documentation templates

### Workflow #35 (Pre-Deployment Testing)
- Add test script execution steps
- Reference Workflow #41 for phase-specific validation
- Include pass/fail criteria

### Workflow #38 (Overnight Scraper Handoff)
- Add validation step: "Run monitoring tests before first scraper launch"
- Reference test script location
- Include expected output

### Workflow #27 (TDD)
- Reference these test suites as examples of good test structure
- Link to test architecture patterns

---

## Test Results Documentation

### Document in PROGRESS.md "Current Session Context"

```markdown
**Last completed:** Test suite validation
  - ✅ Scraper monitoring tests: 10/10 passed (100% pass rate)
  - ✅ Temporal query tests: 25/25 passed
  - ✅ Feature engineering tests: 5/5 passed
  - **Result:** All systems validated, ready for [NEXT_STEP]
```

### Document in COMMAND_LOG.md

```markdown
## Test Execution - [DATE]

### Scraper Monitoring Tests
```bash
bash scripts/monitoring/test_monitoring_system.sh --verbose
```
**Result:** 10 passed, 0 failed (100% pass rate)
**Runtime:** 45 seconds

### Temporal Query Tests
```bash
pytest tests/test_temporal_queries.py -v
```
**Result:** 25 passed, 0 failed
**Runtime:** 2 minutes 14 seconds

### Feature Engineering Tests
```bash
python notebooks/test_feature_engineering.py
```
**Result:** 5/5 tests passed - Ready for SageMaker
**Runtime:** 18 seconds
```

### Update Phase Files (When Relevant)

**Phase 3 (Database):**
- Add sub-phase: "Validate temporal query performance"
- Reference Workflow #41, Test Suite 2
- Include pass criteria (all tests pass, performance < thresholds)

**Phase 5 (Machine Learning):**
- Add sub-phase: "Validate feature engineering readiness"
- Reference Workflow #41, Test Suite 3
- Include SageMaker deployment checklist

**Data Collection Phases:**
- Add validation step after scraper completion
- Reference Workflow #41, Test Suite 1
- Include monitoring system verification

---

## Troubleshooting

### Scraper Monitoring Tests Failing

**Common issues:**
1. Missing execute permissions on scripts
   - Fix: `chmod +x scripts/monitoring/*.sh`

2. Directory doesn't exist
   - Fix: `mkdir -p /tmp/scraper_alerts /tmp/scraper_reminders`

3. Python not available for JSON validation
   - Fix: Install Python 3

### Temporal Query Tests Failing

**Common issues:**
1. Connection refused
   - Fix: Check RDS endpoint, verify security group allows connection

2. Table doesn't exist
   - Fix: Create temporal tables, load data first

3. No data in tables
   - Fix: Run data loading scripts, verify with `SELECT COUNT(*)`

4. Performance tests timeout
   - Fix: Check BRIN indexes exist, analyze query plans, vacuum/analyze tables

### Feature Engineering Tests Failing

**Common issues:**
1. Import error
   - Fix: `pip install pandas numpy psycopg2 sqlalchemy boto3 pyarrow`

2. Database connection fails
   - Fix: Set `NBA_SIM_DB_PASSWORD` environment variable

3. S3 access denied
   - Fix: Check AWS credentials, verify IAM permissions

4. Parquet write fails
   - Fix: Install pyarrow (`pip install pyarrow`)

---

## Best Practices

**1. Run tests in order of dependency:**
- Feature engineering tests (fastest, no data required)
- Scraper monitoring tests (requires directories only)
- Temporal query tests (requires database populated)

**2. Document all test failures:**
- Save test output to file
- Include in troubleshooting documentation
- Update test suites if test is flaky

**3. Update tests when schemas change:**
- Temporal query tests: Update when adding new temporal tables
- Feature engineering tests: Update when adding new feature calculations
- Monitoring tests: Update when changing alert/reminder formats

**4. Run full test suite before major deployments:**
- Before overnight scraper launches
- Before SageMaker sessions
- After database schema changes
- After library upgrades

**5. Use verbose mode for debugging:**
- Scraper tests: `--verbose` flag shows detailed output
- Temporal tests: `-v` flag shows test names
- Feature tests: Already verbose by default

---

## Quick Reference Card

**Test everything before deployment:**
```bash
# 1. Feature engineering readiness (fastest)
python notebooks/test_feature_engineering.py

# 2. Scraper monitoring system (medium)
bash scripts/monitoring/test_monitoring_system.sh

# 3. Temporal query functionality (slowest)
pytest tests/test_temporal_queries.py -v
```

**Expected runtimes:**
- Feature engineering: 10-30 seconds
- Scraper monitoring: 30-60 seconds
- Temporal queries: 1-3 minutes

**Total test suite:** 2-5 minutes

---

*Last updated: October 8, 2025*

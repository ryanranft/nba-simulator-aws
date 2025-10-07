# Temporal Data Validation Guide

**Version:** 1.0
**Last Updated:** October 7, 2025
**Purpose:** Validate temporal panel data integrity, precision, and performance

---

## Overview

This guide provides comprehensive validation procedures for the NBA Temporal Panel Data System.

**Validation areas:**
1. Data availability and completeness
2. Temporal precision tracking
3. Snapshot accuracy
4. Age calculation correctness
5. Query performance benchmarks
6. Cross-source consistency

**Test suite location:** `tests/test_temporal_queries.py`

---

## Running the Test Suite

### Prerequisites

```bash
# Activate environment
conda activate nba-aws

# Install test dependencies
pip install pytest psycopg2-binary pytz

# Update database credentials in test file
# Edit: tests/test_temporal_queries.py
# Update: TEST_DB_CONFIG dictionary
```

### Run All Tests

```bash
# Run full test suite
pytest tests/test_temporal_queries.py -v

# Run with coverage
pytest tests/test_temporal_queries.py --cov=temporal --cov-report=html

# Run specific test class
pytest tests/test_temporal_queries.py::TestSnapshotQueries -v

# Run single test
pytest tests/test_temporal_queries.py::TestSnapshotQueries::test_get_player_snapshot_at_exact_time -v
```

### Expected Output

```
tests/test_temporal_queries.py::TestTemporalDataAvailability::test_temporal_events_table_exists PASSED
tests/test_temporal_queries.py::TestTemporalDataAvailability::test_player_snapshots_table_exists PASSED
tests/test_temporal_queries.py::TestTemporalDataAvailability::test_temporal_events_has_data PASSED
...
======================== 25 passed in 45.2s ========================
```

---

## Test Coverage

### 1. Data Availability Tests (6 tests)

**What they validate:**
- Temporal tables exist
- Tables contain data
- Minimum row counts met

**Critical tests:**
- `test_temporal_events_table_exists` - Core event table exists
- `test_temporal_events_has_data` - Events loaded (> 0 rows)
- `test_player_snapshots_has_data` - Snapshots generated

**Success criteria:**
- All 4 temporal tables exist
- temporal_events: > 10M rows (2004-2021 minimum)
- player_snapshots: > 100K rows (sample)

### 2. Index Performance Tests (2 tests)

**What they validate:**
- BRIN indexes created
- Indexes on correct columns
- Index type verification

**Critical tests:**
- `test_temporal_events_brin_index_exists` - Time-series index
- `test_player_snapshots_brin_index_exists` - Snapshot index

**Success criteria:**
- BRIN index on `temporal_events.wall_clock_utc`
- BRIN index on `player_snapshots.snapshot_time`

### 3. Stored Procedure Tests (2 tests)

**What they validate:**
- Functions exist and are callable
- Return types correct

**Critical tests:**
- `test_get_player_snapshot_function_exists`
- `test_calculate_player_age_function_exists`

**Success criteria:**
- Both functions exist in pg_proc
- Functions accept correct parameter types

### 4. Snapshot Query Tests (3 tests)

**What they validate:**
- Snapshot queries return correct data
- Performance < 5 seconds
- Career stats are monotonic (never decrease)

**Critical tests:**
- `test_get_player_snapshot_at_exact_time` - Accuracy
- `test_snapshot_query_performance` - Speed
- `test_snapshot_monotonicity` - Logic correctness

**Success criteria:**
- Snapshot found for test player
- Query completes in < 5 seconds
- Career points never decrease over time

### 5. Precision Tracking Tests (3 tests)

**What they validate:**
- Precision levels are valid enums
- Precision matches data era
- Data sources tracked

**Critical tests:**
- `test_precision_level_values` - No invalid values
- `test_precision_by_era` - 2020+ data has high precision
- `test_data_source_tracking` - Source field populated

**Success criteria:**
- Only valid precision_level values: 'millisecond', 'second', 'minute', 'game', 'unknown'
- 80%+ of 2020+ data has 'second' or 'millisecond' precision
- All valid data_source values

### 6. Age Calculation Tests (3 tests)

**What they validate:**
- Birth dates available
- Age calculations accurate
- Precision matches birth date precision

**Critical tests:**
- `test_birth_date_available` - Test player has birth date
- `test_calculate_age_at_timestamp` - Function returns age string
- `test_age_precision_by_birth_date_precision` - Age format matches birth date precision

**Success criteria:**
- Test player (Kobe Bryant) has birth date with 'day' precision
- Age calculation returns formatted string (e.g., "37 years, 297 days, 5 hours")
- Day-precision birth dates show age down to days/hours

### 7. Timestamp Consistency Tests (2 tests)

**What they validate:**
- Wall clock and game clock aligned
- Timestamps are timezone-aware

**Critical tests:**
- `test_wall_clock_vs_game_clock` - Game clock in valid range
- `test_timestamp_timezone_aware` - TIMESTAMPTZ type used

**Success criteria:**
- game_clock_seconds: 0-720 (12 minutes)
- quarter: 1-4 or > 4 (OT)
- wall_clock_utc is TIMESTAMPTZ (not TIMESTAMP)

### 8. Game State Tests (1 test)

**What they validate:**
- Game state reconstruction works
- Scores and quarter values valid

**Critical tests:**
- `test_game_state_at_timestamp` - Retrieve game state

**Success criteria:**
- Game states exist for test games
- Scores >= 0
- Quarter in valid range

### 9. Data Quality Tests (2 tests)

**What they validate:**
- No duplicate events
- Snapshots consistent with raw events

**Critical tests:**
- `test_no_duplicate_events` - Uniqueness
- `test_snapshot_consistency` - Aggregate accuracy

**Success criteria:**
- No duplicate (game_id, player_id, wall_clock_utc)
- Snapshot career points within 5% of event sum

### 10. Performance Benchmarks (2 tests)

**What they validate:**
- Time-range queries performant
- Career aggregations complete in reasonable time

**Critical tests:**
- `test_time_range_query_performance` - Month query < 10s
- `test_player_career_aggregation_performance` - Full career < 15s

**Success criteria:**
- 1-month range query: < 10 seconds
- Full career aggregation: < 15 seconds

---

## Manual Validation Procedures

### Validate Temporal Events Data

```sql
-- Check event count by precision level
SELECT
    precision_level,
    COUNT(*) AS events,
    MIN(wall_clock_utc) AS earliest,
    MAX(wall_clock_utc) AS latest
FROM
    temporal_events
GROUP BY
    precision_level
ORDER BY
    earliest;

-- Expected output:
-- 'minute'     | 6,500,000 | 2004-01-01 | 2019-12-31
-- 'second'     |   500,000 | 2013-01-01 | 2021-12-31
-- 'millisecond'|       100 | 2020-01-01 | 2021-12-31 (future)
```

### Validate Player Snapshots

```sql
-- Check snapshot coverage
SELECT
    DATE_TRUNC('year', snapshot_time) AS year,
    COUNT(DISTINCT player_id) AS players,
    COUNT(*) AS snapshots
FROM
    player_snapshots
GROUP BY
    year
ORDER BY
    year;

-- Expected: ~500 players per year, ~18M snapshots total
```

### Validate Age Calculations

```sql
-- Test age calculation for known players
SELECT
    p.name,
    pb.birth_date,
    pb.birth_date_precision,
    calculate_player_age(p.player_id, '2016-06-19 19:02:34-05:00'::TIMESTAMPTZ) AS age
FROM
    players p
JOIN
    player_biographical pb ON p.player_id = pb.player_id
WHERE
    p.name IN ('Kobe Bryant', 'LeBron James', 'Michael Jordan')
ORDER BY
    p.name;

-- Verify ages match known values
```

### Validate Query Performance

```sql
-- Benchmark snapshot query
EXPLAIN ANALYZE
SELECT * FROM get_player_snapshot_at_time(977, '2016-06-19 19:02:34'::TIMESTAMPTZ);

-- Check for:
-- - BRIN index scan (not sequential scan)
-- - Execution time < 5000ms
-- - Rows returned: 1
```

### Validate Cross-Source Consistency

```sql
-- Compare ESPN vs NBA.com Stats for same game
SELECT
    te1.game_id,
    te1.data_source AS source1,
    te2.data_source AS source2,
    te1.event_type,
    te1.wall_clock_utc AS time1,
    te2.wall_clock_utc AS time2,
    EXTRACT(EPOCH FROM (te1.wall_clock_utc - te2.wall_clock_utc)) AS time_diff_sec
FROM
    temporal_events te1
JOIN
    temporal_events te2
    ON te1.game_id = te2.game_id
    AND te1.event_type = te2.event_type
    AND ABS(EXTRACT(EPOCH FROM (te1.wall_clock_utc - te2.wall_clock_utc))) < 120
WHERE
    te1.data_source = 'espn'
    AND te2.data_source = 'nba_stats'
LIMIT 100;

-- Flag discrepancies > 60 seconds
```

---

## Validation Failure Handling

### Common Failures and Solutions

#### 1. No Data in Temporal Tables

**Symptom:**
```
AssertionError: temporal_events table is empty (expected > 0 rows, got 0)
```

**Cause:** Temporal tables not populated yet

**Solution:**
1. Run ETL pipeline to load temporal_events
2. Generate player_snapshots with batch job
3. Re-run tests

#### 2. Snapshot Query Too Slow

**Symptom:**
```
AssertionError: Snapshot query took 12.3s (expected < 5s)
```

**Cause:** BRIN indexes not created or need VACUUM

**Solution:**
```sql
-- Create indexes
CREATE INDEX idx_temporal_events_time_brin ON temporal_events USING BRIN (wall_clock_utc);
CREATE INDEX idx_player_snapshots_time_brin ON player_snapshots USING BRIN (snapshot_time);

-- Update statistics
VACUUM ANALYZE temporal_events;
VACUUM ANALYZE player_snapshots;
```

#### 3. Precision Level Mismatch

**Symptom:**
```
AssertionError: Modern data precision too low (45.2%)
```

**Cause:** Missing second-precision data from NBA.com Stats

**Solution:**
1. Verify NBA.com Stats scraper ran successfully
2. Check data_source field: Should have 'nba_stats' entries
3. Re-scrape 2013-2019 data from NBA.com Stats API

#### 4. Age Calculation Returns NULL

**Symptom:**
```
AssertionError: Age calculation returned NULL
```

**Cause:** Missing birth date in player_biographical table

**Solution:**
```sql
-- Check birth date availability
SELECT
    player_id,
    birth_date,
    birth_date_precision
FROM
    player_biographical
WHERE
    player_id = 977;

-- If NULL, populate from NBA.com Stats API
```

#### 5. Snapshot vs Events Mismatch

**Symptom:**
```
AssertionError: Snapshot vs events mismatch: 33646 vs 33000 (1.9%)
```

**Cause:** Snapshots not regenerated after event data updated

**Solution:**
```sql
-- Regenerate snapshots for player
DELETE FROM player_snapshots WHERE player_id = 977;

-- Re-run snapshot generation script
python scripts/generate_player_snapshots.py --player_id 977
```

---

## Continuous Validation

### Daily Validation Checks

**Run every morning (automated):**
```bash
# Quick validation (5 min)
pytest tests/test_temporal_queries.py::TestTemporalDataAvailability -v
pytest tests/test_temporal_queries.py::TestPrecisionLevels -v
pytest tests/test_temporal_queries.py::TestDataQualityValidation -v

# Check for failures
if [ $? -ne 0 ]; then
    echo "Temporal data validation FAILED - investigate immediately"
    # Send alert
fi
```

### Weekly Validation Checks

**Run every Sunday:**
```bash
# Full test suite (30-60 min)
pytest tests/test_temporal_queries.py -v --tb=short > weekly_validation_$(date +%Y%m%d).log

# Performance benchmarks
pytest tests/test_temporal_queries.py::TestPerformanceBenchmarks -v

# Generate coverage report
pytest tests/test_temporal_queries.py --cov=temporal --cov-report=html
```

### Monthly Validation Checks

**Run first day of month:**
1. Run full test suite
2. Manual SQL validation procedures
3. Cross-source consistency checks
4. Review and update test cases
5. Benchmark against previous month

---

## Success Metrics

**Passing criteria (production-ready):**
- ✅ 100% of data availability tests pass
- ✅ 100% of stored procedure tests pass
- ✅ 90%+ of snapshot query tests pass
- ✅ 95%+ of precision tracking tests pass
- ✅ 90%+ of age calculation tests pass
- ✅ 100% of timestamp consistency tests pass
- ✅ 100% of data quality tests pass
- ✅ 80%+ of performance benchmarks pass

**Data quality thresholds:**
- temporal_events: > 10M rows (2004-2021 minimum)
- player_snapshots: > 100K rows
- Precision coverage (2020+): > 80% second/millisecond
- Birth date coverage: > 90% day precision (modern players)
- Snapshot accuracy: < 5% error vs raw events
- Query performance: 80% of queries < target time

**Monthly validation report should show:**
- All test pass rates
- Performance trends (query times over time)
- Data completeness by era
- Precision coverage by source
- Cross-source consistency rate

---

## Troubleshooting Guide

### Issue: Tests Hang or Timeout

**Possible causes:**
1. Database connection issues
2. Large table sequential scans
3. Missing indexes

**Diagnostic steps:**
```sql
-- Check active queries
SELECT pid, query, state, query_start
FROM pg_stat_activity
WHERE state = 'active';

-- Kill hanging query
SELECT pg_terminate_backend(pid);

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE tablename IN ('temporal_events', 'player_snapshots');
```

### Issue: Inconsistent Results

**Possible causes:**
1. Concurrent data updates
2. Snapshot staleness
3. Timezone issues

**Diagnostic steps:**
```sql
-- Check last snapshot update time
SELECT MAX(snapshot_time) FROM player_snapshots WHERE player_id = 977;

-- Check timezone settings
SHOW timezone;

-- Verify TIMESTAMPTZ usage
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'temporal_events'
  AND column_name = 'wall_clock_utc';
```

---

## Next Steps After Validation

**If all tests pass:**
1. Document validation results
2. Proceed with Phase 4 (Temporal Simulation) or Phase 5 (Temporal ML)
3. Enable production queries

**If tests fail:**
1. Review failure logs
2. Follow troubleshooting guide
3. Fix data/schema issues
4. Re-run tests
5. Do NOT proceed until all critical tests pass

**See also:**
- `docs/TEMPORAL_QUERY_GUIDE.md` - Query examples
- `docs/phases/PHASE_3_DATABASE.md` Sub-Phase 3.5 - Temporal schema
- `docs/adr/009-temporal-panel-data-architecture.md` - Architecture decisions

---

*Last updated: October 7, 2025*
*Version: 1.0*
*Maintained by: NBA Temporal Panel Data Team*

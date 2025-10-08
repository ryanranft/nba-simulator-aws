# Testing Strategy

> **⚠️ LARGE FILE WARNING (862 lines)**
>
> **For Claude Code:** Only read this file when:
> - Writing new tests for the project
> - Debugging test failures
> - Understanding testing philosophy and strategy
>
> **DO NOT read at session start** - this file is a reference for writing tests, not initialization documentation.
>
> **Best practice:** Reference Workflow #41 for testing procedures instead of reading this entire file.

**Project:** NBA Game Simulator & ML Platform
**Purpose:** Document testing approach for AWS data pipeline and ML components

---

## Testing Philosophy

**Core Principles:**
1. **Test early, test often** - Catch issues before AWS deployment
2. **Test locally first** - Faster feedback than testing in cloud
3. **Data quality is critical** - Most bugs come from bad data, not bad code
4. **Pragmatic over perfect** - Learning project, not mission-critical system
5. **Document failures** - Failed tests teach more than passing tests

**Balance:**
- ✅ **DO:** Test critical data transformations, ETL logic, simulation algorithms
- ❌ **DON'T:** Over-test simple CRUD operations, obvious utility functions
- ✅ **DO:** Validate data quality and schema compliance
- ❌ **DON'T:** Aim for 100% code coverage on exploratory code

---

## Testing Phases

### Phase 1: Local Development (Current)

**Status:** ⏸️ No formal tests yet
**Priority:** Medium (implement as components are built)

**What to test:**
- ETL field extraction logic
- Data transformation functions
- SQL query correctness
- Game simulation algorithms

**What NOT to test yet:**
- AWS infrastructure (test manually)
- End-to-end pipelines (too complex for initial phase)
- Performance optimization (premature)

### Phase 2: ETL Development (Upcoming)

**When:** Before running full ETL on 146,115 files

**Critical tests:**
1. Field extraction from sample JSON files
2. Data type validation
3. Schema compliance
4. Error handling for malformed data

### Phase 3: Production Deployment (Future)

**When:** After Phase 4 (EC2 Simulation) is complete

**Additional tests:**
- Integration tests with real RDS
- Performance tests with large datasets
- Simulation accuracy validation

---

## Test Types

### 1. Unit Tests

**Purpose:** Test individual functions in isolation

**Tools:**
```bash
pip install pytest pytest-cov
```

**Location:** `tests/unit/`

**Structure:**
```
tests/
├── unit/
│   ├── test_etl_extraction.py
│   ├── test_field_mapping.py
│   ├── test_game_simulator.py
│   └── test_data_validation.py
├── integration/
│   ├── test_etl_to_rds.py
│   └── test_simulation_queries.py
└── fixtures/
    ├── sample_box_score.json
    ├── sample_pbp.json
    └── sample_schedule.json
```

**Example:**
```python
# tests/unit/test_field_extraction.py
import pytest
from scripts.etl.field_mapping import extract_player_stats

def test_extract_player_stats_with_valid_data():
    """Test extraction with complete, valid JSON"""
    # Arrange
    raw_data = {
        "players": [{
            "id": "12345",
            "displayName": "LeBron James",
            "statistics": {"points": 25, "rebounds": 8, "assists": 10}
        }]
    }

    # Act
    result = extract_player_stats(raw_data)

    # Assert
    assert result["player_id"] == "12345"
    assert result["player_name"] == "LeBron James"
    assert result["points"] == 25
    assert result["rebounds"] == 8


def test_extract_player_stats_with_missing_field():
    """Test handling of missing optional fields"""
    raw_data = {
        "players": [{
            "id": "12345",
            "displayName": "LeBron James",
            # Missing statistics
        }]
    }

    result = extract_player_stats(raw_data)

    # Should use default values or None
    assert result["player_id"] == "12345"
    assert result["points"] == 0 or result["points"] is None


def test_extract_player_stats_raises_on_missing_required_field():
    """Test error handling for missing required fields"""
    raw_data = {
        "players": [{
            # Missing id (required field)
            "displayName": "LeBron James"
        }]
    }

    with pytest.raises(KeyError):
        extract_player_stats(raw_data)
```

**Run tests:**
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_field_extraction.py

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run verbose
pytest -v

# Run only tests matching pattern
pytest -k "extract"
```

### 2. Data Validation Tests

**Purpose:** Ensure data quality and schema compliance

**Critical for this project** - Most bugs will be data-related

**Example:**
```python
# tests/unit/test_data_validation.py
import pytest
import pandas as pd

def test_game_scores_are_non_negative():
    """Scores must be >= 0"""
    df = load_sample_games()

    assert (df["home_score"] >= 0).all()
    assert (df["away_score"] >= 0).all()


def test_game_dates_are_valid_range():
    """Games should be between 1999 and 2025"""
    df = load_sample_games()

    dates = pd.to_datetime(df["game_date"])
    assert dates.min() >= pd.Timestamp("1999-01-01")
    assert dates.max() <= pd.Timestamp("2025-12-31")


def test_player_minutes_not_exceed_48():
    """Players can't play more than 48 minutes (NBA regulation)"""
    df = load_sample_player_stats()

    # Allow slight buffer for overtime (up to 63 minutes = 3 OT)
    assert (df["minutes_played"] <= 63).all()


def test_required_fields_not_null():
    """Required fields must not be null"""
    df = load_sample_games()

    required_fields = ["game_id", "game_date", "home_team_id", "away_team_id"]
    for field in required_fields:
        assert df[field].notna().all(), f"{field} has null values"


def test_foreign_key_relationships():
    """Player IDs must exist in players table"""
    df_stats = load_sample_player_stats()
    df_players = load_sample_players()

    # All player_ids in stats should exist in players table
    invalid_ids = set(df_stats["player_id"]) - set(df_players["player_id"])
    assert len(invalid_ids) == 0, f"Invalid player IDs: {invalid_ids}"
```

### 3. Integration Tests

**Purpose:** Test interaction between components

**Location:** `tests/integration/`

**Example:**
```python
# tests/integration/test_etl_to_rds.py
import pytest
import psycopg2
from scripts.etl.glue_etl_job import run_etl

@pytest.fixture
def test_db_connection():
    """Create temporary test database"""
    conn = psycopg2.connect(
        host="localhost",  # Use local test DB
        database="nba_test",
        user="test_user",
        password="test_pass"
    )
    yield conn
    conn.close()


def test_etl_loads_data_into_database(test_db_connection):
    """Test full ETL pipeline with sample files"""
    # Arrange
    sample_files = ["fixtures/sample_box_score.json"]

    # Act
    run_etl(sample_files, test_db_connection)

    # Assert
    cursor = test_db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM player_game_stats")
    count = cursor.fetchone()[0]

    assert count > 0, "No data loaded into database"


def test_etl_handles_duplicate_records(test_db_connection):
    """Test idempotency - running ETL twice shouldn't duplicate data"""
    sample_files = ["fixtures/sample_box_score.json"]

    # Act - run twice
    run_etl(sample_files, test_db_connection)
    run_etl(sample_files, test_db_connection)

    # Assert - should only have one set of data
    cursor = test_db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM player_game_stats")
    count = cursor.fetchone()[0]

    # Verify no duplicates (exact count depends on sample data)
    assert count == 10  # Expected number from sample file
```

### 4. SQL Tests

**Purpose:** Verify SQL queries return correct results

**Example:**
```python
# tests/unit/test_sql_queries.py
import pytest

def test_player_average_points_query():
    """Test aggregation query correctness"""
    # Sample data
    player_stats = [
        {"player_id": 1, "points": 20},
        {"player_id": 1, "points": 30},
        {"player_id": 2, "points": 15},
    ]

    # Expected: Player 1 avg = 25, Player 2 avg = 15

    # Load into temp table and run query
    result = run_query("""
        SELECT
            player_id,
            AVG(points) AS avg_points
        FROM player_game_stats
        GROUP BY player_id
    """)

    assert result[0]["avg_points"] == 25
    assert result[1]["avg_points"] == 15
```

### 5. Simulation Tests

**Purpose:** Verify game simulation logic

**Example:**
```python
# tests/unit/test_game_simulator.py
import pytest
from scripts.simulation.game_simulator import GameSimulator

def test_simulation_produces_valid_scores():
    """Simulated scores should be realistic (50-150 range)"""
    simulator = GameSimulator(random_seed=42)

    result = simulator.simulate_game(home_team_id=1, away_team_id=2)

    assert 50 <= result["home_score"] <= 150
    assert 50 <= result["away_score"] <= 150


def test_simulation_is_deterministic_with_seed():
    """Same seed should produce same results"""
    sim1 = GameSimulator(random_seed=42)
    sim2 = GameSimulator(random_seed=42)

    result1 = sim1.simulate_game(home_team_id=1, away_team_id=2)
    result2 = sim2.simulate_game(home_team_id=1, away_team_id=2)

    assert result1["home_score"] == result2["home_score"]
    assert result1["away_score"] == result2["away_score"]


def test_simulation_uses_team_statistics():
    """Better team should win more often"""
    simulator = GameSimulator()

    # Simulate 100 games
    wins = 0
    for _ in range(100):
        result = simulator.simulate_game(
            home_team_id=1,  # Strong team
            away_team_id=30  # Weak team
        )
        if result["home_score"] > result["away_score"]:
            wins += 1

    # Strong team should win at least 70% of games
    assert wins >= 70
```

### 6. Snapshot Tests

**Purpose:** Detect unexpected changes in data transformations

**Example:**
```python
# tests/unit/test_etl_snapshots.py
import json
from scripts.etl.field_mapping import extract_all_fields

def test_extraction_matches_snapshot():
    """ETL output should match saved snapshot"""
    # Load sample input
    with open("fixtures/sample_box_score.json") as f:
        raw_data = json.load(f)

    # Extract fields
    result = extract_all_fields(raw_data)

    # Load expected output
    with open("fixtures/expected_extraction.json") as f:
        expected = json.load(f)

    # Compare
    assert result == expected, "Extraction output changed - review changes or update snapshot"
```

---

## Test Data Strategy

### Sample Files

**Location:** `tests/fixtures/`

**Contents:**
```
tests/fixtures/
├── sample_box_score.json        # Representative box score
├── sample_pbp.json              # Representative play-by-play
├── sample_schedule.json         # Representative schedule
├── malformed_data.json          # Missing fields, invalid values
├── edge_cases.json              # Overtime games, zero stats, etc.
└── expected_extraction.json     # Expected ETL output
```

**Create fixtures:**
```bash
# Download real samples from S3
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json tests/fixtures/sample_box_score.json

# Create edge cases manually
# Edit sample_box_score.json to create malformed_data.json, edge_cases.json
```

### Test Database

**Option 1: SQLite (Recommended for early testing)**
```python
# Fast, no setup required
import sqlite3

conn = sqlite3.connect(":memory:")  # In-memory database
# Create tables, insert test data, run tests
```

**Option 2: PostgreSQL Local (More realistic)**
```bash
# Install PostgreSQL locally
brew install postgresql  # macOS
sudo apt-get install postgresql  # Linux

# Create test database
createdb nba_test

# Run migrations
psql nba_test < sql/create_tables.sql
```

**Option 3: Docker PostgreSQL (Best isolation)**
```bash
# Start test database
docker run --name nba-test-db \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=nba_test \
  -p 5433:5432 \
  -d postgres:15

# Run tests against localhost:5433

# Clean up
docker stop nba-test-db
docker rm nba-test-db
```

---

## Testing Workflow

### Before Writing Code

1. **Review requirements** - What should this function do?
2. **Write test cases** - Document expected behavior
3. **Create fixtures** - Prepare sample data

### While Writing Code

4. **Run tests frequently** - `pytest -v`
5. **Use TDD if helpful** - Write test first, then implementation
6. **Test edge cases** - Null values, empty lists, extreme numbers

### Before Committing

7. **Run all tests** - `pytest`
8. **Check coverage** - `pytest --cov=scripts`
9. **Fix failing tests** - Don't commit broken tests
10. **Update fixtures** - If behavior intentionally changed

### Before AWS Deployment

11. **Integration tests** - Test with local database
12. **Sample data validation** - Run ETL on 100 sample files
13. **Manual verification** - Check outputs make sense

---

## What to Test (Priority Order)

### Priority 1: Critical Path (Must Test)

1. **ETL field extraction** - Core business logic
2. **Data validation** - Schema compliance, data types
3. **Database loading** - Correct table insertion
4. **Simulation algorithms** - Core game logic

### Priority 2: Important (Should Test)

5. **Error handling** - Malformed data, missing fields
6. **SQL queries** - Aggregations, joins
7. **Edge cases** - Overtime games, extreme stats
8. **Data transformations** - Type conversions, calculations

### Priority 3: Nice to Have (Can Test)

9. **Utility functions** - Helper methods
10. **Configuration loading** - YAML parsing
11. **Logging** - Error messages
12. **Performance** - Query optimization

### Don't Test (Not Worth It)

- ❌ AWS service configuration (test manually)
- ❌ Third-party libraries (trust they work)
- ❌ Obvious getters/setters
- ❌ Exploratory notebook code

---

## Success Criteria

**ETL Testing:**
- ✅ Extracts correct fields from sample JSON files
- ✅ Handles missing/malformed data gracefully
- ✅ Validates data types and ranges
- ✅ Loads into database without errors
- ✅ Idempotent (running twice doesn't duplicate data)

**Simulation Testing:**
- ✅ Produces realistic scores (50-150 range)
- ✅ Deterministic with random seed
- ✅ Better teams win more often
- ✅ All required fields populated

**Data Quality:**
- ✅ No null values in required fields
- ✅ Foreign key relationships valid
- ✅ Dates within expected range (1999-2025)
- ✅ Statistics within realistic bounds

---

## Testing Tools

### Core Tools

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock

# Install data validation tools
pip install pandas numpy

# Install database testing tools
pip install psycopg2-binary sqlalchemy
```

### Optional Tools

```bash
# Hypothesis - property-based testing
pip install hypothesis

# Great Expectations - data validation
pip install great-expectations

# Faker - generate test data
pip install faker
```

### Test Configuration

**`pytest.ini`:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

**`.coveragerc`:**
```ini
[run]
source = scripts
omit =
    tests/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## Manual Testing Checklist

**Before ETL Full Run:**
- [ ] Test with 10 sample files
- [ ] Test with 100 sample files
- [ ] Check data quality in RDS
- [ ] Verify row counts match expectations
- [ ] Check for null values in required fields
- [ ] Validate foreign key relationships
- [ ] Review sample records manually

**Before Simulation Deployment:**
- [ ] Run 10 test simulations
- [ ] Verify scores are realistic
- [ ] Check simulation runs without errors
- [ ] Validate output format
- [ ] Test with different team matchups

**Before ML Training:**
- [ ] Verify feature engineering produces valid data
- [ ] Check for null/infinite values
- [ ] Validate training data size
- [ ] Test model training on sample data
- [ ] Verify model can make predictions

---

## Automated Test Suites

**See Workflow #41 for complete documentation:** `docs/claude_workflows/workflow_descriptions/41_testing_framework.md`

The project includes three comprehensive test suites that validate different aspects of the temporal panel data system:

### 1. Scraper Monitoring System Tests

**Location:** `scripts/monitoring/test_monitoring_system.sh`

**Purpose:** Validate overnight scraper workflow end-to-end (10 test categories)

**Usage:**
```bash
bash scripts/monitoring/test_monitoring_system.sh --verbose
```

**What it tests:**
- Daemon validation, permissions, command interface
- Reminder/alert file creation and format
- Completion analysis (COMPLETE vs INVESTIGATE)
- Error handling and recommendations
- Context preservation (JSON validation)
- Script permissions (all 6 monitoring scripts)
- Directory structure
- End-to-end integration workflow

**Runtime:** 30-60 seconds
**When to run:** Before launching overnight scrapers, after monitoring system changes

### 2. Temporal Panel Data Query Tests

**Location:** `tests/test_temporal_queries.py`

**Purpose:** Validate millisecond-precision temporal queries and snapshot accuracy (25+ tests)

**Usage:**
```bash
pytest tests/test_temporal_queries.py -v
```

**What it tests:**
- Table availability and data population
- BRIN indexes for performance
- Stored procedures (`get_player_snapshot_at_time`, `calculate_player_age`)
- Snapshot query accuracy and performance (<5s)
- Precision levels (millisecond/second/minute/game)
- Age calculations and birth date precision
- Timestamp consistency (timezone-aware)
- Game state reconstruction
- Data quality validation (no duplicates, 5% tolerance)
- Performance benchmarks (time-range <10s, aggregation <15s)

**Prerequisites:** RDS connection, temporal tables populated
**Runtime:** 1-3 minutes
**When to run:** Weekly during temporal development, after schema changes

### 3. Feature Engineering Validation Tests

**Location:** `notebooks/test_feature_engineering.py`

**Purpose:** Pre-flight validation for SageMaker deployment (5 test categories)

**Usage:**
```bash
python notebooks/test_feature_engineering.py
```

**What it tests:**
- Import availability (pandas, numpy, psycopg2, sqlalchemy, boto3)
- Database connection (RDS connectivity, games table access)
- S3 access (read permissions on data lake)
- Feature logic (rolling stats, rest days, categorical encoding)
- Parquet I/O (write/read roundtrip validation)

**Exit codes:**
- 0 = All tests passed, ready for SageMaker
- 1 = Failures detected, fix before deployment

**Runtime:** 10-30 seconds
**When to run:** Before each SageMaker session, after environment changes

### Quick Test Suite Execution

**Run all test suites:**
```bash
# 1. Feature engineering readiness (fastest)
python notebooks/test_feature_engineering.py

# 2. Scraper monitoring system (medium)
bash scripts/monitoring/test_monitoring_system.sh

# 3. Temporal query functionality (slowest)
pytest tests/test_temporal_queries.py -v
```

**Total runtime:** 2-5 minutes

**For detailed usage, troubleshooting, and integration:** See Workflow #41

---

## Testing Anti-Patterns (Avoid These)

### ❌ Testing Implementation Details
```python
# Bad - testing internal method
def test_internal_calculation():
    obj = Calculator()
    assert obj._internal_helper() == 5

# Good - test public interface
def test_calculate_result():
    calc = Calculator()
    assert calc.calculate(2, 3) == 5
```

### ❌ Brittle Tests (Over-Specified)
```python
# Bad - breaks if order changes
assert result == [1, 2, 3, 4, 5]

# Good - tests what matters
assert len(result) == 5
assert 3 in result
```

### ❌ Testing Multiple Things
```python
# Bad - multiple assertions, hard to debug
def test_player_stats():
    stats = get_player_stats(player_id=1)
    assert stats["points"] == 25
    assert stats["rebounds"] == 10
    assert stats["assists"] == 8  # If this fails, which one?

# Good - separate tests
def test_player_points():
    stats = get_player_stats(player_id=1)
    assert stats["points"] == 25

def test_player_rebounds():
    stats = get_player_stats(player_id=1)
    assert stats["rebounds"] == 10
```

### ❌ Tests Without Assertions
```python
# Bad - no assertion, just checks it doesn't crash
def test_etl_runs():
    run_etl(sample_files)

# Good - verify expected outcome
def test_etl_loads_data():
    run_etl(sample_files)
    count = db.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    assert count > 0
```

---

## Future Enhancements

**Phase 2 (After ETL Complete):**
- Add integration tests with real RDS
- Implement data quality monitoring
- Add performance benchmarks

**Phase 3 (After Simulation Complete):**
- Add simulation accuracy metrics
- Implement backtesting framework
- Add statistical validation tests

**Phase 4 (Production):**
- Add end-to-end tests
- Implement continuous testing in CI/CD
- Add load testing for APIs

---

## Resources

**Documentation:**
- [pytest documentation](https://docs.pytest.org/)
- [Great Expectations](https://greatexpectations.io/) - Data validation
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing

**Best Practices:**
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
- [Data Testing](https://www.getdbt.com/blog/how-we-test-our-data)

---

## Getting Started

**Quick start:**
```bash
# 1. Create tests directory
mkdir -p tests/unit tests/integration tests/fixtures

# 2. Install pytest
pip install pytest pytest-cov

# 3. Create first test
cat > tests/unit/test_example.py << 'EOF'
def test_example():
    assert 1 + 1 == 2
EOF

# 4. Run tests
pytest -v

# 5. See coverage
pytest --cov=scripts --cov-report=html
open htmlcov/index.html
```

---

**Last Updated:** 2025-10-08
**Status:** Testing strategy documented, 3 automated test suites integrated (see Workflow #41)

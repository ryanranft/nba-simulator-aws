# Workflow #27: TDD (Test-Driven Development) Workflow

**Category:** Development Practice
**Priority:** Medium
**When to Use:** When implementing new ETL logic, simulation algorithms, or data validation functions
**Related Workflows:** #5 (Task Execution), #16 (Testing)

---

## Overview

Test-Driven Development (TDD) workflow for writing production code with automated tests. This workflow ensures code quality by writing tests before implementation.

**Core Principle:** Write failing tests first, then implement code to make them pass.

---

## When to Use This Workflow

✅ **USE for:**
- ETL field extraction logic
- Data transformation functions
- Simulation algorithms
- Critical business logic
- Functions that process user data

❌ **DON'T USE for:**
- Exploratory notebook code
- One-off scripts
- Simple utility functions
- Prototype/spike code

---

## TDD Workflow Steps

### Phase 1: Before Writing Code

#### Step 1: Review Requirements
```markdown
**Ask yourself:**
- What should this function do?
- What inputs does it accept?
- What outputs should it produce?
- What edge cases exist?
```

#### Step 2: Write Test Cases
```python
# tests/unit/test_field_extraction.py
import pytest
from scripts.etl.field_mapping import extract_player_stats

def test_extract_player_stats_with_valid_data():
    """Test extraction with complete, valid JSON"""
    # Arrange - prepare test data
    raw_data = {
        "players": [{
            "id": "12345",
            "displayName": "LeBron James",
            "statistics": {"points": 25, "rebounds": 8, "assists": 10}
        }]
    }

    # Act - call the function
    result = extract_player_stats(raw_data)

    # Assert - verify expected behavior
    assert result["player_id"] == "12345"
    assert result["player_name"] == "LeBron James"
    assert result["points"] == 25
```

**Test should FAIL at this point** (function doesn't exist yet)

#### Step 3: Create Fixtures
```bash
# Prepare sample data files
mkdir -p tests/fixtures/
cp sample_data.json tests/fixtures/
```

**Required fixtures:**
- Valid data (happy path)
- Missing fields (error handling)
- Edge cases (null values, extreme numbers)
- Malformed data (invalid JSON, wrong types)

---

### Phase 2: While Writing Code

#### Step 4: Run Tests Frequently
```bash
# Run tests to see them fail first
pytest tests/unit/test_field_extraction.py -v

# Expected output: FAILED (function not implemented)
```

#### Step 5: Implement Minimum Code to Pass
```python
# scripts/etl/field_mapping.py
def extract_player_stats(raw_data):
    """Extract player statistics from raw JSON data."""
    player = raw_data["players"][0]

    return {
        "player_id": player["id"],
        "player_name": player["displayName"],
        "points": player["statistics"]["points"],
        "rebounds": player["statistics"]["rebounds"],
        "assists": player["statistics"]["assists"]
    }
```

#### Step 6: Run Tests Again
```bash
pytest tests/unit/test_field_extraction.py -v

# Expected output: PASSED
```

#### Step 7: Test Edge Cases
```python
def test_extract_player_stats_with_missing_field():
    """Test handling of missing optional fields"""
    raw_data = {
        "players": [{
            "id": "12345",
            "displayName": "LeBron James",
            # Missing statistics field
        }]
    }

    result = extract_player_stats(raw_data)

    # Should use default values
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

#### Step 8: Refine Implementation
```python
def extract_player_stats(raw_data):
    """Extract player statistics from raw JSON data.

    Args:
        raw_data: Dictionary containing player data from API

    Returns:
        Dictionary with standardized player statistics

    Raises:
        KeyError: If required fields are missing
    """
    player = raw_data["players"][0]

    # Required fields (will raise KeyError if missing)
    player_id = player["id"]
    player_name = player["displayName"]

    # Optional fields (use .get() with defaults)
    stats = player.get("statistics", {})
    points = stats.get("points", 0)
    rebounds = stats.get("rebounds", 0)
    assists = stats.get("assists", 0)

    return {
        "player_id": player_id,
        "player_name": player_name,
        "points": points,
        "rebounds": rebounds,
        "assists": assists
    }
```

---

### Phase 3: Before Committing

#### Step 9: Run All Tests
```bash
# Run all tests to ensure nothing broke
pytest

# Run with coverage
pytest --cov=scripts --cov-report=term-missing
```

**Success criteria:**
- ✅ All tests pass
- ✅ Coverage > 80% for new code
- ✅ No unexpected failures in other tests

#### Step 10: Check Code Quality
```bash
# Optional: Run linting
black scripts/etl/field_mapping.py
pylint scripts/etl/field_mapping.py

# Optional: Type checking
mypy scripts/etl/field_mapping.py
```

#### Step 11: Fix Failing Tests
If any tests fail:
1. Read error message carefully
2. Check what assertion failed
3. Fix implementation (NOT the test)
4. Re-run tests
5. Repeat until all pass

**NEVER commit broken tests**

#### Step 12: Update Fixtures if Needed
If behavior intentionally changed:
```bash
# Update expected output fixtures
cp new_output.json tests/fixtures/expected_extraction.json

# Document why fixture changed in commit message
```

---

## Test Types to Write

### 1. Happy Path Tests
```python
def test_function_with_valid_input():
    """Test normal operation with valid data"""
    result = my_function(valid_input)
    assert result == expected_output
```

### 2. Edge Case Tests
```python
def test_function_with_empty_input():
    """Test with empty/null input"""
    result = my_function([])
    assert result == []

def test_function_with_extreme_values():
    """Test with boundary values"""
    result = my_function(999999)
    assert result is not None
```

### 3. Error Handling Tests
```python
def test_function_raises_on_invalid_input():
    """Test that function raises appropriate error"""
    with pytest.raises(ValueError):
        my_function(invalid_input)
```

### 4. Data Validation Tests
```python
def test_output_data_types():
    """Verify output has correct types"""
    result = my_function(input_data)
    assert isinstance(result["score"], int)
    assert isinstance(result["name"], str)
```

---

## Common Testing Patterns

### Pattern 1: Arrange-Act-Assert (AAA)
```python
def test_example():
    # Arrange - set up test data
    input_data = create_test_data()

    # Act - call the function
    result = function_under_test(input_data)

    # Assert - verify result
    assert result == expected
```

### Pattern 2: Fixtures for Reusable Data
```python
@pytest.fixture
def sample_game_data():
    """Reusable test data"""
    return {
        "game_id": "12345",
        "home_score": 100,
        "away_score": 95
    }

def test_with_fixture(sample_game_data):
    result = process_game(sample_game_data)
    assert result["winner"] == "home"
```

### Pattern 3: Parametrized Tests
```python
@pytest.mark.parametrize("score,expected", [
    (100, "win"),
    (95, "loss"),
    (100, "tie")
])
def test_game_outcome(score, expected):
    result = determine_outcome(score)
    assert result == expected
```

---

## Testing Checklist

**Before writing code:**
- [ ] Requirements clearly defined
- [ ] Test cases written (should fail)
- [ ] Fixtures created

**While writing code:**
- [ ] Tests run frequently (`pytest -v`)
- [ ] Minimum code to pass tests
- [ ] Edge cases covered

**Before committing:**
- [ ] All tests pass (`pytest`)
- [ ] Coverage checked (`pytest --cov`)
- [ ] No broken tests elsewhere
- [ ] Code quality validated (optional: black, pylint)

---

## Integration with Project Workflow

### After Writing Tests and Code
```bash
# 1. Run tests
pytest -v

# 2. Log code snippet to COMMAND_LOG.md (see workflow #30)
# Document: What you wrote, outcome (pass/fail), lessons learned

# 3. Run file inventory
make inventory

# 4. Commit with test results
git add tests/ scripts/
git commit -m "Add player stats extraction with tests

- Implemented extract_player_stats() function
- Added 5 test cases (happy path, edge cases, error handling)
- All tests passing
- Coverage: 95%

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## When TDD is Overkill

**Skip TDD for:**
- ❌ Exploratory data analysis (notebooks)
- ❌ One-time migration scripts
- ❌ Simple getters/setters
- ❌ Prototype code (spike solutions)
- ❌ Code that will be deleted soon

**Use TDD for:**
- ✅ Core business logic (ETL, simulation)
- ✅ Data validation functions
- ✅ Complex algorithms
- ✅ Code that will be reused
- ✅ Production pipelines

---

## Troubleshooting

### Tests Won't Run
```bash
# Check pytest is installed
pip list | grep pytest

# Install if missing
pip install pytest pytest-cov

# Verify test discovery
pytest --collect-only
```

### Tests Pass Locally, Fail in CI
- Check Python version consistency
- Verify dependencies installed
- Check for hardcoded paths
- Review environment variables

### Can't Mock AWS Services
```bash
# Install moto for AWS mocking
pip install moto[all]

# Use in tests
from moto import mock_s3

@mock_s3
def test_s3_upload():
    # Test code here
    pass
```

---

## Resources

**Testing Tools:**
```bash
pip install pytest pytest-cov pytest-mock
pip install moto[all]  # AWS mocking
pip install hypothesis  # Property-based testing
```

**References:**
- `docs/TESTING.md` - Complete testing strategy
- Workflow #16 - Testing workflow overview
- `tests/fixtures/` - Sample test data

---

**Last Updated:** 2025-10-02
**Source:** docs/TESTING.md (lines 466-490)

# Resume Instructions: Phase 5 Testing (After Refactoring)

**Created:** November 4, 2025
**Status:** Phase 5 at 70% complete, 3 test files remaining
**Priority:** High - Complete testing infrastructure before simulator rebuild

---

## Current Status

### Completed Work ✅
- **Day 1:** Test fixtures & conftest.py (100%)
- **Day 2:** Database tests - 54 tables covered (100%)
- **Day 3:** Config & ETL tests (70% complete)
  - ✅ `tests/unit/test_config/` - All config tests done
  - ✅ `tests/unit/test_etl/test_espn_scraper.py` - 600+ lines, 8 test classes
  - ✅ `tests/unit/test_etl/test_error_handler.py`
  - ✅ `tests/unit/test_etl/test_validators.py`

### Remaining Work ⏳
- **Day 4:** Create 3 remaining scraper test files
- **Day 5:** Integration tests
- **Day 6-7:** Coverage improvement to 100%

---

## Next Task: Create Remaining Scraper Tests

### Files to Create (Day 4 - Estimated 3-4 hours)

#### 1. `tests/unit/test_etl/test_basketball_reference_scraper.py` (~850 lines)

**Purpose:** Test Basketball Reference scraper functionality

**Test Classes to Implement:**
```python
class TestBasketballReferenceScraper:
    """Test Basketball Reference scraper initialization and basic functionality"""

class TestBasketballReferenceBoxScoreScraping:
    """Test box score data extraction"""

class TestBasketballReferencePlayByPlayScraping:
    """Test play-by-play data extraction"""

class TestBasketballReferencePlayerStatsScraping:
    """Test player stats extraction (13-tier system)"""

class TestBasketballReferenceTeamStatsScraping:
    """Test team stats extraction"""

class TestBasketballReferenceErrorHandling:
    """Test error handling and retry logic"""

class TestBasketballReferenceRateLimiting:
    """Test rate limiting compliance"""

class TestBasketballReferenceDataValidation:
    """Test data validation against schema"""
```

**Key Features to Test:**
- 13-tier data extraction system
- HTML parsing with BeautifulSoup
- Rate limiting (20 requests/min)
- Error handling and retries
- Data validation
- Mock HTTP responses

**Pattern:** Follow `test_espn_scraper.py` structure

---

#### 2. `tests/unit/test_etl/test_nba_api_scraper.py` (~700 lines)

**Purpose:** Test NBA Stats API scraper functionality

**Test Classes to Implement:**
```python
class TestNBAAPIScraper:
    """Test NBA API scraper initialization"""

class TestNBAAPIBoxScoreScraping:
    """Test box score retrieval from NBA Stats API"""

class TestNBAAPIPlayByPlayScraping:
    """Test play-by-play data extraction"""

class TestNBAAPIPlayerTrackingScraping:
    """Test player tracking data (advanced stats)"""

class TestNBAAPITeamStatsScraping:
    """Test team statistics extraction"""

class TestNBAAPIErrorHandling:
    """Test error handling for API failures"""

class TestNBAAPIRateLimiting:
    """Test rate limiting and backoff"""

class TestNBAAPIDataValidation:
    """Test JSON response validation"""
```

**Key Features to Test:**
- JSON API response parsing
- Player tracking data (hustle stats, speed, distance)
- Advanced metrics (PIE, NetRtg, etc.)
- Rate limiting compliance
- Authentication handling
- Error recovery

**Pattern:** Follow `test_espn_scraper.py` async patterns

---

#### 3. `tests/unit/test_etl/test_hoopr_scraper.py` (~600 lines)

**Purpose:** Test hoopR (R package) scraper integration

**Test Classes to Implement:**
```python
class TestHoopRScraper:
    """Test hoopR scraper initialization and R integration"""

class TestHoopRDataExtraction:
    """Test data extraction from R hoopR package"""

class TestHoopRBoxScoreScraping:
    """Test box score retrieval"""

class TestHoopRPlayByPlayScraping:
    """Test play-by-play data extraction"""

class TestHoopRErrorHandling:
    """Test error handling for R process failures"""

class TestHoopRDataValidation:
    """Test data validation and transformation"""
```

**Key Features to Test:**
- R process integration (rpy2)
- CSV data parsing
- Data type conversions (R → Python)
- Error handling for R failures
- Data validation
- Mock R package responses

**Pattern:** Follow `test_espn_scraper.py` with additional R-specific tests

---

## Implementation Guide

### Step 1: Set Up Test Environment (15 min)

```bash
# Activate environment
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws

# Verify test infrastructure
pytest tests/unit/test_etl/test_espn_scraper.py -v

# Expected: All tests pass (reference implementation works)
```

---

### Step 2: Create Basketball Reference Tests (90 min)

**File:** `tests/unit/test_etl/test_basketball_reference_scraper.py`

**Template Structure:**
```python
"""
Tests for Basketball Reference scraper module.

This module tests the Basketball Reference scraper's ability to extract
data from Basketball-Reference.com including box scores, play-by-play,
and player statistics using the 13-tier extraction system.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from nba_simulator.etl.extractors.basketball_reference.scraper import (
    BasketballReferenceScraper
)

# Test fixtures
@pytest.fixture
def mock_basketball_reference_response():
    """Mock HTML response from Basketball Reference"""
    return """<html>...</html>"""

@pytest.fixture
def scraper():
    """Create scraper instance for testing"""
    return BasketballReferenceScraper()

# Test classes (8 classes, ~100 lines each)
class TestBasketballReferenceScraper:
    # 10-12 test methods
    pass

# ... (7 more test classes)
```

**Key Test Patterns:**
- Use `@pytest.mark.asyncio` for async tests
- Mock HTTP responses with `responses` library
- Mock BeautifulSoup parsing
- Test rate limiting with `pytest-mock`
- Validate against schema

**Run Tests:**
```bash
pytest tests/unit/test_etl/test_basketball_reference_scraper.py -v --cov
```

---

### Step 3: Create NBA API Tests (90 min)

**File:** `tests/unit/test_etl/test_nba_api_scraper.py`

**Key Differences from ESPN:**
- JSON responses (not HTML)
- More advanced metrics (player tracking)
- Different rate limiting rules
- Authentication headers

**Run Tests:**
```bash
pytest tests/unit/test_etl/test_nba_api_scraper.py -v --cov
```

---

### Step 4: Create hoopR Tests (60 min)

**File:** `tests/unit/test_etl/test_hoopr_scraper.py`

**Key Differences:**
- R process integration testing
- CSV parsing instead of JSON/HTML
- Mock rpy2 calls
- Test R error handling

**Run Tests:**
```bash
pytest tests/unit/test_etl/test_hoopr_scraper.py -v --cov
```

---

### Step 5: Run Full Test Suite (15 min)

```bash
# Run all ETL tests
pytest tests/unit/test_etl/ -v --cov=nba_simulator.etl --cov-report=term-missing

# Expected Coverage: 85-90%

# Run complete test suite
pytest tests/ -v --cov=nba_simulator --cov-report=html

# Check coverage report
open htmlcov/index.html
```

---

### Step 6: Update Progress (15 min)

**Edit PROGRESS.md:**
```markdown
### Phase 5: Testing Infrastructure ✅ COMPLETE

**Status:** 100% complete
**Completed:** November X, 2025

#### Summary:
- Created comprehensive test infrastructure
- 54 database table tests (100% coverage)
- 4 scraper test suites (ESPN, Basketball Reference, NBA API, hoopR)
- Config and ETL validation tests
- Total test coverage: 90%+

#### Test Files Created:
- `tests/unit/test_config/` (5 files)
- `tests/unit/test_database/` (5 files)
- `tests/unit/test_etl/` (7 files)
- Total: 17 test files, ~5,500 lines

#### Next Phase:
- Phase 6: Agent Migration OR
- Phase 4: Rebuild Simulator (proper implementation)
```

---

## Success Criteria

- [ ] All 3 scraper test files created (~2,150 lines total)
- [ ] All tests pass (100% success rate)
- [ ] Code coverage ≥ 85% for ETL modules
- [ ] No regressions in existing tests
- [ ] Tests follow async patterns from ESPN scraper
- [ ] Mock responses cover edge cases
- [ ] Documentation complete

---

## After Completion: Next Steps

Once Phase 5 testing is complete, you have two options:

### Option A: Continue Refactoring (Phase 6-7)
- Phase 6: Migrate autonomous agents
- Phase 7: Workflow orchestration
- Estimated: 10-14 days

### Option B: Rebuild Simulator (Proper Implementation)
- Phase 4 enhancement with advanced models
- ARIMA, VAR, State-Space, Kalman Filters
- Target accuracy: 75-80% (up from 63%)
- Estimated: 20-30 hours

**Recommendation:** Complete Phase 5 testing first to ensure proper test infrastructure exists for whatever you build next.

---

## Troubleshooting

### Problem: Import errors after refactoring
**Solution:** Update imports to match new module structure:
```python
from nba_simulator.etl.extractors.basketball_reference.scraper import BasketballReferenceScraper
```

### Problem: Tests fail with module not found
**Solution:** Ensure `__init__.py` files exist in all directories:
```bash
find nba_simulator/etl -name "__init__.py"
```

### Problem: Coverage below 85%
**Solution:** Run with missing report to identify untested code:
```bash
pytest --cov-report=term-missing
```

### Problem: Async tests fail
**Solution:** Ensure `@pytest.mark.asyncio` decorator is used:
```python
@pytest.mark.asyncio
async def test_scraper_async():
    result = await scraper.fetch_data()
    assert result is not None
```

---

## Quick Reference

### Commands
```bash
# Run single test file
pytest tests/unit/test_etl/test_basketball_reference_scraper.py -v

# Run with coverage
pytest tests/unit/test_etl/ -v --cov=nba_simulator.etl --cov-report=html

# Run specific test class
pytest tests/unit/test_etl/test_basketball_reference_scraper.py::TestBasketballReferenceScraper -v

# Run in parallel (faster)
pytest tests/unit/test_etl/ -n auto
```

### File Locations
- **Test files:** `tests/unit/test_etl/`
- **Scraper implementations:** `nba_simulator/etl/extractors/{source}/scraper.py`
- **Template:** `tests/unit/test_etl/test_espn_scraper.py` (600 lines reference)

### Time Estimates
- Basketball Reference tests: 90 minutes
- NBA API tests: 90 minutes
- hoopR tests: 60 minutes
- Integration & cleanup: 30 minutes
- **Total:** 3-4 hours

---

## Important Notes

1. **Test Coverage is Critical:** Don't skip tests - they prevent regressions during continued refactoring
2. **Follow Async Patterns:** All scrapers use `asyncio` - tests must too
3. **Mock External APIs:** Never hit real APIs in tests (use `responses` library)
4. **Validate Data Schemas:** Test output matches expected database schemas
5. **Rate Limiting Matters:** Test that rate limiters work correctly

---

**Good luck! You're 70% done with Phase 5. Just 3 more test files to go! 🚀**

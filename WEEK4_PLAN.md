# Week 4 Implementation Plan - Integration Tests & Transformers

**Date:** October 28, 2025
**Phase:** Phase 2 - ETL Framework (continued)
**Duration:** Week 4 of 14-week refactoring plan
**Status:** 🔄 IN PROGRESS

---

## 🎯 Week 4 Objectives

Test extractors with real production data and implement transformation layer for data normalization.

**Goal:** Validate ETL framework with actual data and create unified data model across all sources.

**Priority:** Testing first (validate extractors), then transformers (standardize output).

---

## 📊 Context from Week 3

**ETL Framework Status:**
- 9 extractors implemented and operational
- 27+ scripts consolidated
- 100% validation test pass rate
- Zero breaking changes

**Database Baseline:**
- 15 tables, 28.5M records, 7.51 GB
- hoopR = 99% of data (primary source)
- temporal_events = 13.6M events (critical)

**Key Insight:** Can now test extractors against actual database to validate wrapper pattern.

---

## 📋 Week 4 Tasks

### Task 1: Create Integration Test Framework
**Estimated Time:** 1 hour
**Priority:** HIGH

**Action Items:**
- [ ] Create `tests/integration/` directory structure
- [ ] Create base integration test class
- [ ] Implement test utilities (database connections, data comparison)
- [ ] Set up test configuration
- [ ] Create test fixtures

**Structure:**
```
tests/integration/
├── __init__.py
├── base_integration_test.py
├── test_hoopr_extractors.py
├── test_espn_extractors.py
├── test_basketball_reference_extractors.py
├── test_nba_api_extractors.py
└── fixtures/
    └── sample_data.json
```

---

### Task 2: Test hoopR Extractors (PRIORITY)
**Estimated Time:** 1.5 hours
**Priority:** HIGH (Primary data source)

**Action Items:**
- [ ] Test HooprPlayByPlayExtractor with sample season
- [ ] Validate output format matches database schema
- [ ] Test HooprPlayerBoxExtractor
- [ ] Compare wrapper output with direct script output
- [ ] Measure performance (time, memory)
- [ ] Document any discrepancies

**Success Criteria:**
- Extractor produces valid output
- Output matches database schema
- Performance acceptable (within 10% of direct script)
- Zero data loss

---

### Task 3: Test Other Extractors
**Estimated Time:** 1.5 hours
**Priority:** MEDIUM

**Action Items:**
- [ ] Test ESPN extractors (3 extractors)
- [ ] Test Basketball Reference extractors (2 extractors)
- [ ] Test NBA API extractors (2 extractors)
- [ ] Document performance metrics
- [ ] Identify any issues

---

### Task 4: Create Transformation Layer
**Estimated Time:** 2 hours
**Priority:** HIGH

**Action Items:**
- [ ] Create `nba_simulator/etl/transformers/` structure
- [ ] Implement BaseTransformer class
- [ ] Create data normalization transformers
- [ ] Implement schema validation
- [ ] Create unified data model

**Transformers to Create:**
```
nba_simulator/etl/transformers/
├── __init__.py
├── base.py                    # BaseTransformer
├── normalize.py               # Data normalization
├── schema_validator.py        # Schema validation
└── unified_model.py           # Unified data model
```

---

### Task 5: Implement Data Quality Framework
**Estimated Time:** 1.5 hours
**Priority:** MEDIUM

**Action Items:**
- [ ] Create quality check framework
- [ ] Implement data completeness checks
- [ ] Implement data consistency checks
- [ ] Create quality metrics
- [ ] Build quality reporting

---

### Task 6: Documentation & Validation
**Estimated Time:** 1 hour
**Priority:** MEDIUM

**Action Items:**
- [ ] Document integration test results
- [ ] Create transformer usage guide
- [ ] Update Week 4 completion report
- [ ] Run full validation suite

---

## 🏗️ Implementation Details

### Integration Test Framework Design

```python
# tests/integration/base_integration_test.py

import unittest
from nba_simulator.database.connection import execute_query
from nba_simulator.config.loader import config

class BaseIntegrationTest(unittest.TestCase):
    """
    Base class for integration tests.

    Provides:
    - Database connection utilities
    - Data comparison methods
    - Performance measurement
    - Test data cleanup
    """

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.db_available = cls._check_database_connection()
        if not cls.db_available:
            raise unittest.SkipTest("Database not available")

    @classmethod
    def _check_database_connection(cls):
        """Check if database is accessible"""
        try:
            result = execute_query("SELECT 1;", fetch_one=True)
            return result is not None
        except Exception:
            return False

    def compare_outputs(self, extractor_output, database_output):
        """Compare extractor output with database data"""
        pass

    def measure_performance(self, func, *args, **kwargs):
        """Measure execution time and memory"""
        pass
```

---

### Transformer Design

```python
# nba_simulator/etl/transformers/base.py

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTransformer(ABC):
    """
    Base class for data transformers.

    Transforms raw data from extractors into standardized format.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def transform(self, data: Any) -> Dict[str, Any]:
        """
        Transform data to standardized format.

        Args:
            data: Raw data from extractor

        Returns:
            Transformed data in standard format
        """
        pass

    @abstractmethod
    def validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        Validate transformed data against schema.

        Args:
            data: Transformed data

        Returns:
            True if valid, False otherwise
        """
        pass

    def get_quality_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate data quality metrics.

        Returns:
            Dictionary of quality metrics
        """
        return {
            'completeness': self._check_completeness(data),
            'consistency': self._check_consistency(data),
            'validity': self.validate_schema(data)
        }
```

---

### Unified Data Model

**Goal:** Single format for all data sources

**Key Fields:**
- `game_id` (standardized across sources)
- `event_id` (unique identifier)
- `timestamp` (ISO format)
- `event_type` (standardized values)
- `player_id` (mapped to unified ID)
- `team_id` (mapped to unified ID)
- `event_data` (JSONB with source-specific data)
- `data_source` (hoopR, ESPN, BBRef, NBA_API)

**Schema:**
```python
UNIFIED_SCHEMA = {
    'game_id': 'string',
    'event_id': 'string',
    'timestamp': 'datetime',
    'event_type': 'string',  # SHOT, REBOUND, FOUL, etc.
    'player_id': 'string',
    'team_id': 'string',
    'event_data': 'dict',
    'data_source': 'string',
    'created_at': 'datetime'
}
```

---

## 🔒 Production Safety

### Testing Strategy

1. **Read-Only Operations:** All integration tests are read-only
2. **No Database Writes:** Tests query existing data, don't modify
3. **Sample Data:** Test with small subsets first
4. **Performance Bounds:** Set acceptable performance limits
5. **Rollback Ready:** Can revert to direct scripts instantly

### Risk Mitigation

**Risk:** Integration tests slow down development
**Mitigation:** Use small sample sizes, parallel execution

**Risk:** Extractors fail with real data
**Mitigation:** Wrapper pattern allows instant fallback to scripts

**Risk:** Performance regression
**Mitigation:** Measure and compare with baseline

---

## 📊 Success Metrics

### Technical Metrics

- [ ] Integration test framework created
- [ ] All 9 extractors tested with real data
- [ ] Transformation layer implemented
- [ ] Data quality framework operational
- [ ] All tests passing (≥95%)

### Data Quality Metrics

- [ ] Output format matches schema (100%)
- [ ] Data completeness ≥ 95%
- [ ] Data consistency ≥ 98%
- [ ] Performance within 10% of baseline

### Operational Metrics

- [ ] Test execution time < 10 minutes
- [ ] Zero breaking changes
- [ ] Documentation complete
- [ ] Ready for production use

---

## ⚠️ Risk Assessment

### High Risk Items

1. **Integration Tests May Reveal Issues**
   - Risk: Extractors fail with real data
   - Mitigation: Wrapper pattern allows fallback

2. **Performance Issues**
   - Risk: Extractors slower than direct scripts
   - Mitigation: Measure and optimize

### Medium Risk Items

1. **Schema Mismatches**
   - Risk: Output doesn't match database schema
   - Mitigation: Schema validation layer

2. **Data Quality Issues**
   - Risk: Data from extractors has quality problems
   - Mitigation: Quality framework catches issues

---

## 📅 Week 4 Timeline

**Day 1 (Today - continued):**
- Task 1: Integration test framework (1 hour)
- Task 2: Test hoopR extractors (1.5 hours)

**Day 2:**
- Task 3: Test other extractors (1.5 hours)
- Task 4: Start transformation layer (1 hour)

**Day 3:**
- Complete Task 4: Transformation layer (1 hour)
- Task 5: Data quality framework (1.5 hours)
- Task 6: Documentation (1 hour)

**Total Week 4 Effort:** ~8.5 hours

---

## 🚦 Go/No-Go Criteria for Week 5

**Must Pass ALL:**

✅ **Integration Tests:**
- [ ] Framework operational
- [ ] All 9 extractors tested
- [ ] ≥95% tests passing

✅ **Transformers:**
- [ ] Transformation layer implemented
- [ ] Schema validation working
- [ ] Unified data model defined

✅ **Data Quality:**
- [ ] Quality framework operational
- [ ] Metrics tracking working
- [ ] Issues documented

✅ **Performance:**
- [ ] Within 10% of baseline
- [ ] No memory leaks
- [ ] Acceptable execution time

**If ANY fails:** Fix before proceeding to Week 5.

---

## 📚 References

**Week 3 Results:**
- WEEK3_COMPLETION_REPORT.md
- 9 extractors operational
- 27+ scripts consolidated

**Database Baseline:**
- backups/week2_baseline_20251028_054049.json
- 28.5M records validated

**Refactoring Plan:**
- docs/refactoring/EXECUTION_PLAN.md

---

**Status:** Ready to begin Week 4 implementation
**Next:** Create integration test framework


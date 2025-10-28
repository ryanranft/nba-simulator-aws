# Week 3 Implementation Plan - Phase 2: ETL Framework

**Date:** October 28, 2025
**Phase:** Phase 2 - ETL Framework Consolidation
**Duration:** Week 3 of 14-week refactoring plan (Week 3-5 for full Phase 2)
**Status:** 🔄 IN PROGRESS

---

## 🎯 Week 3 Objectives

Create organized ETL package structure and consolidate hoopR scrapers (priority data source).

**Goal:** Establish ETL foundation and migrate primary data collection pipeline without disruption.

**Priority:** hoopR scrapers first (13.6M records = 47.5% of database)

---

## 📊 Context from Week 2

**Database Baseline:**
- 15 tables, 28.5M records, 7.51 GB
- hoopR = 99% of data (13.6M PBP + 813K box scores)
- temporal_events = 13.6M events (critical for Phase 8)
- Zero breaking changes confirmed

**Key Insight:** hoopR is the primary data source. Must prioritize and preserve this pipeline.

---

## 📋 Week 3 Tasks

### Task 1: Create ETL Package Structure
**Estimated Time:** 30 minutes
**Priority:** HIGH

**Action Items:**
- [ ] Create `nba_simulator/etl/` package
- [ ] Create `nba_simulator/etl/base/` for base classes
- [ ] Create `nba_simulator/etl/extractors/` for source-specific extractors
- [ ] Create `nba_simulator/etl/extractors/hoopr/` (priority)
- [ ] Create `nba_simulator/etl/transformers/` for data transformation
- [ ] Create `nba_simulator/etl/loaders/` for database loading

**Structure:**
```
nba_simulator/etl/
├── __init__.py
├── base/
│   ├── __init__.py
│   ├── scraper.py         # Base scraper class
│   ├── extractor.py       # Base extractor class
│   └── loader.py          # Base loader class
├── extractors/
│   ├── __init__.py
│   └── hoopr/
│       ├── __init__.py
│       ├── play_by_play.py
│       ├── player_box.py
│       └── schedule.py
├── transformers/
│   ├── __init__.py
│   └── normalize.py
└── loaders/
    ├── __init__.py
    └── postgres.py
```

---

### Task 2: Create Base Scraper Classes
**Estimated Time:** 45 minutes
**Priority:** HIGH

**Action Items:**
- [ ] Create `BaseScraper` abstract class
- [ ] Add retry logic (reuse from reconciliation)
- [ ] Add rate limiting
- [ ] Add error handling
- [ ] Add logging integration
- [ ] Add health check method

**Features:**
- Configurable retry with exponential backoff
- Rate limiting for API compliance
- Structured error handling
- Integration with nba_simulator.utils.logging
- Health monitoring

---

### Task 3: Consolidate hoopR Scrapers
**Estimated Time:** 2 hours
**Priority:** HIGH (PRIMARY DATA SOURCE)

**Current hoopR Scripts:**
1. `scripts/etl/hoopr_async_scraper.py`
2. `scripts/etl/hoopr_incremental_scraper.py`
3. `scripts/etl/load_hoopr_to_rds.py`
4. `scripts/etl/hoopr_pbp_scraper.py`

**Migration Strategy:**
- Create wrapper classes that CALL existing scripts
- Test equivalence with baseline (13.6M PBP records)
- Validate temporal_events integration
- Keep old scripts as fallback

**New Structure:**
```python
# nba_simulator/etl/extractors/hoopr/play_by_play.py
class HooprPlayByPlayExtractor(BaseExtractor):
    def extract(self):
        # Calls existing hoopr_pbp_scraper.py
        # Returns standardized data format
        pass
```

---

### Task 4: Create ETL Integration Tests
**Estimated Time:** 1 hour
**Priority:** MEDIUM

**Action Items:**
- [ ] Create `tests/etl/` directory
- [ ] Test base scraper functionality
- [ ] Test hoopR extractor equivalence
- [ ] Test data format standardization
- [ ] Test error handling

**Test Coverage:**
- Base class functionality
- hoopR extractor output matches baseline
- Error recovery works
- Logging captures events

---

### Task 5: Validate Against Database Baseline
**Estimated Time:** 30 minutes
**Priority:** HIGH

**Action Items:**
- [ ] Run new hoopR extractors
- [ ] Compare output with baseline
- [ ] Verify record counts match
- [ ] Validate temporal_events population
- [ ] Check data quality

**Success Criteria:**
- New extractors produce identical data to old scripts
- 13.6M PBP records maintained
- temporal_events integration preserved
- No data loss

---

### Task 6: Document ETL Architecture
**Estimated Time:** 30 minutes
**Priority:** MEDIUM

**Action Items:**
- [ ] Create ETL architecture diagram
- [ ] Document base classes
- [ ] Document hoopR integration
- [ ] Create migration guide
- [ ] Update EXECUTION_PLAN.md

---

## 🏗️ Implementation Details

### Base Scraper Class Design

```python
# nba_simulator/etl/base/scraper.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from ...utils.logging import setup_logging

class BaseScraper(ABC):
    """
    Base class for all data scrapers.

    Provides:
    - Retry logic with exponential backoff
    - Rate limiting
    - Error handling
    - Health checks
    - Logging integration
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.logger = setup_logging(f"etl.{name}")
        self._setup()

    @abstractmethod
    def extract(self) -> Any:
        """Extract data from source"""
        pass

    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate extracted data"""
        pass

    def health_check(self) -> bool:
        """Check if scraper is operational"""
        pass
```

---

### hoopR Wrapper Pattern

```python
# nba_simulator/etl/extractors/hoopr/play_by_play.py

import subprocess
import sys
from pathlib import Path
from ...base.scraper import BaseScraper

class HooprPlayByPlayExtractor(BaseScraper):
    """
    hoopR play-by-play data extractor.

    Wraps existing hoopr_pbp_scraper.py for backward compatibility
    while providing new interface.
    """

    def __init__(self, config=None):
        super().__init__("hoopr_pbp", config)
        self.legacy_script = Path("scripts/etl/hoopr_pbp_scraper.py")

    def extract(self, season: str = None, force: bool = False):
        """
        Extract play-by-play data from hoopR.

        Currently calls legacy script. Future versions will
        implement direct extraction.
        """
        self.logger.info(f"Extracting hoopR PBP for season {season}")

        # Call legacy script
        cmd = [sys.executable, str(self.legacy_script)]
        if season:
            cmd.extend(["--season", season])
        if force:
            cmd.append("--force")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode != 0:
            self.logger.error(f"Legacy script failed: {result.stderr}")
            raise RuntimeError(f"hoopR extraction failed")

        self.logger.info("hoopR PBP extraction complete")
        return self._parse_output(result.stdout)

    def validate(self, data):
        """Validate hoopR data meets expectations"""
        # Check record count
        # Validate schema
        # Check for duplicates
        pass
```

---

## 🔒 Production Safety

### Parallel Operation Rules

1. **NEVER delete old scripts** - Keep as fallback
2. **Test equivalence** - New must match old exactly
3. **Gradual cutover** - Run both in parallel first
4. **Monitor metrics** - Track record counts, data quality
5. **Easy rollback** - Can revert to old scripts instantly

### Validation Checklist

Before marking any scraper as migrated:

- [ ] New extractor produces identical output to old script
- [ ] Record counts match baseline
- [ ] Data quality checks pass
- [ ] temporal_events integration preserved
- [ ] Error handling tested
- [ ] Rollback procedure documented

---

## 📊 Success Metrics

### Technical Metrics

- [ ] ETL package structure created
- [ ] Base classes implemented
- [ ] hoopR extractors operational
- [ ] Tests passing (100%)
- [ ] No data loss (28.5M records preserved)

### Data Quality Metrics

- [ ] hoopR PBP: 13.6M records maintained
- [ ] hoopR player_box: 813K records maintained
- [ ] temporal_events: 13.6M events maintained
- [ ] Data quality score ≥ baseline

### Operational Metrics

- [ ] Old scripts still work (fallback ready)
- [ ] New extractors faster or same speed
- [ ] Error rate ≤ baseline
- [ ] Monitoring dashboards updated

---

## ⚠️ Risk Assessment

### High Risk Items

1. **hoopR Pipeline Disruption**
   - Risk: Breaking primary data source (99% of data)
   - Mitigation: Parallel operation, keep old scripts

2. **temporal_events Integration**
   - Risk: Breaking event-level data population
   - Mitigation: Explicit tests for temporal_events

3. **Data Quality Degradation**
   - Risk: New extractors produce lower quality data
   - Mitigation: Equivalence testing, quality metrics

### Medium Risk Items

1. **Performance Regression**
   - Risk: New extractors slower than old
   - Mitigation: Benchmark testing, optimization

2. **Configuration Changes**
   - Risk: Breaking existing configuration
   - Mitigation: Backward-compatible config loader

### Mitigation Strategy

**For Each Risk:**
1. Document current behavior
2. Test new implementation against baseline
3. Run both in parallel
4. Compare outputs
5. Monitor metrics
6. Keep rollback ready

---

## 📅 Week 3 Timeline

**Day 1 (Today):**
- Task 1: Create ETL package structure (30 min)
- Task 2: Create base classes (45 min)
- Start Task 3: hoopR consolidation (1 hour)

**Day 2:**
- Complete Task 3: hoopR consolidation (1 hour)
- Task 4: Create integration tests (1 hour)

**Day 3:**
- Task 5: Validate against baseline (30 min)
- Task 6: Documentation (30 min)
- Week 3 completion report

**Total Week 3 Effort:** ~5.5 hours

---

## 🚦 Go/No-Go Criteria for Week 4

**Must Pass ALL:**

✅ **ETL Structure:**
- [ ] Package created and importable
- [ ] Base classes working
- [ ] hoopR extractors operational

✅ **Data Integrity:**
- [ ] hoopR PBP: 13.6M records maintained
- [ ] temporal_events: 13.6M events maintained
- [ ] No data corruption

✅ **Backward Compatibility:**
- [ ] Old scripts still work
- [ ] Easy rollback available
- [ ] Parallel operation tested

✅ **Testing:**
- [ ] All ETL tests passing
- [ ] Equivalence tests passing
- [ ] Integration tests passing

**If ANY fails:** Fix before proceeding to Week 4.

---

## 📚 References

**Week 2 Baseline:**
- WEEK2_COMPLETION_REPORT.md
- backups/week2_baseline_20251028_054049.json

**Refactoring Plan:**
- docs/refactoring/EXECUTION_PLAN.md

**Current hoopR Scripts:**
- scripts/etl/hoopr_async_scraper.py
- scripts/etl/hoopr_incremental_scraper.py
- scripts/etl/load_hoopr_to_rds.py
- scripts/etl/hoopr_pbp_scraper.py

---

**Status:** Ready to begin Week 3 implementation
**Next:** Create ETL package structure and base classes


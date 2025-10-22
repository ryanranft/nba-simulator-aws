# Automated Scraper Migration Agent - System Design

**Status:** 🏗️ Design Phase
**Created:** October 22, 2025
**Objective:** Autonomously migrate 63 remaining scrapers to AsyncBaseScraper framework overnight

---

## Executive Summary

**Goal:** Create a background agent that autonomously migrates all remaining scrapers (63 of 82) to the AsyncBaseScraper framework, similar to how the recommendation implementation agent completed 214 implementations in 12 minutes.

**Inspiration:** `scripts/automation/batch_implement_recommendations.sh` (224 lines, 100% success rate)

**Expected Results:**
- 📊 **Target:** 63 scrapers migrated
- ⏱️ **Duration:** 5-6 hours autonomous overnight
- ✅ **Success Rate:** 85-90% (54-57 scrapers)
- 🔧 **Manual Review:** 10-15% (6-9 scrapers with complex patterns)
- 📈 **Progress:** 23% → 100% AsyncBaseScraper adoption

---

## System Architecture

### Component 1: Batch Migration Orchestrator

**File:** `scripts/automation/batch_migrate_scrapers.sh`

**Purpose:** Main entry point that coordinates the entire migration process

**Functions:**
```bash
main() {
    parse_args "$@"
    load_migration_plan
    identify_remaining_scrapers
    for scraper in "${remaining_scrapers[@]}"; do
        migrate_single_scraper "$scraper"
    done
    generate_final_report
}
```

**Workflow:**
1. Parse command-line arguments (--count N, --pattern REGEX, --dry-run)
2. Load FRAMEWORK_MIGRATION_PLAN.md
3. Identify scrapers not yet migrated
4. For each scraper:
   - Detect pattern (async, incremental, specialized, agent, utility)
   - Generate migration code
   - Run tests
   - Commit if successful
   - Update migration plan
5. Generate final report with success/failure stats

---

### Component 2: Pattern Detection Analyzer

**File:** `scripts/automation/detect_scraper_pattern.py`

**Purpose:** Analyze a scraper's code to determine its migration pattern

**Detection Logic:**

#### Pattern 1: Primary Async Scraper
**Indicators:**
- Has `async def` functions
- Uses `aiohttp` or `asyncio`
- Main purpose: Async data collection
- Example: `espn_async_scraper.py`

**Detection:**
```python
def is_primary_async(file_content):
    return (
        'async def' in file_content and
        ('aiohttp' in file_content or 'asyncio' in file_content) and
        'class' in file_content and
        'scrape' in file_content.lower()
    )
```

#### Pattern 2: Incremental Scraper
**Indicators:**
- Tracks last run date/timestamp
- Queries database for "latest" or "last_updated"
- Scrapes delta since last run
- Example: `espn_incremental_scraper.py`

**Detection:**
```python
def is_incremental(file_content):
    return (
        ('last_run' in file_content or 'last_updated' in file_content) and
        ('since' in file_content or 'delta' in file_content) and
        ('SELECT MAX' in file_content or 'ORDER BY' in file_content.lower())
    )
```

#### Pattern 3: Specialized Task Scraper
**Indicators:**
- Targets specific endpoint/task
- Uses synchronous library (requests, BeautifulSoup)
- Focused scope (one data type)
- Example: `basketball_reference_box_score_scraper.py`

**Detection:**
```python
def is_specialized(file_content):
    return (
        'requests' in file_content and
        ('BeautifulSoup' in file_content or 'json.loads' in file_content) and
        len(file_content.split('def ')) < 15  # Less than 15 functions
    )
```

#### Pattern 4: Autonomous Agent
**Indicators:**
- Multi-phase workflow
- State persistence
- Checkpoint recovery
- Complex orchestration
- Example: `bbref_tier_1_agent.py`

**Detection:**
```python
def is_agent(file_content):
    return (
        ('checkpoint' in file_content.lower() or 'resume' in file_content.lower()) and
        ('phase' in file_content.lower() or 'stage' in file_content.lower()) and
        len(file_content.split('class ')) > 3  # Multiple classes
    )
```

#### Pattern 5: Utility Script (Config Only)
**Indicators:**
- No async HTTP scraping
- Data processing/analysis
- One-off execution
- Example: `analyze_espn_coverage.py`

**Detection:**
```python
def is_utility(file_content):
    return (
        'scrape' not in file_content.lower() and
        ('analyze' in file_content.lower() or
         'extract' in file_content.lower() or
         'load' in file_content.lower() or
         'validate' in file_content.lower())
    )
```

---

### Component 3: Migration Code Generator

**File:** `scripts/automation/generate_migration.py`

**Purpose:** Generate AsyncBaseScraper-compatible code based on detected pattern

**Templates:**

#### Template 1: Primary Async Migration
```python
def generate_primary_async_migration(scraper_info):
    return f"""#!/usr/bin/env python3
'''
{scraper_info['name']} - Migrated to AsyncBaseScraper
...
'''

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager

class {scraper_info['class_name']}(AsyncBaseScraper):
    def __init__(self, config_name="{scraper_info['config_name']}"):
        super().__init__(config_name)
        # Preserve original initialization logic
        {scraper_info['init_code']}

    async def scrape(self):
        '''Main scraping method'''
        # Migrate original scrape logic here
        {scraper_info['scrape_code']}

async def main():
    async with {scraper_info['class_name']}() as scraper:
        await scraper.scrape()

if __name__ == "__main__":
    asyncio.run(main())
"""
```

#### Template 2: Incremental Migration
```python
def generate_incremental_migration(scraper_info):
    return f"""#!/usr/bin/env python3
'''
{scraper_info['name']} - Incremental Scraper (Migrated to AsyncBaseScraper)
...
'''

import asyncio
import sqlite3
from datetime import datetime, timedelta

from scripts.etl.async_scraper_base import AsyncBaseScraper

class {scraper_info['class_name']}(AsyncBaseScraper):
    def __init__(self, days_back=7, config_name="{scraper_info['config_name']}"):
        super().__init__(config_name)
        self.days_back = days_back
        self.db_path = "{scraper_info['db_path']}"

    async def get_last_run_date(self):
        '''Get last successful run date from database'''
        # Wrap synchronous DB query in asyncio.to_thread
        return await asyncio.to_thread(self._get_last_run_date_sync)

    def _get_last_run_date_sync(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(game_date) FROM games")
        result = cursor.fetchone()[0]
        conn.close()
        return result

    async def scrape(self):
        last_date = await self.get_last_run_date()
        # Scrape games since last_date
        {scraper_info['scrape_code']}
"""
```

#### Template 3: Specialized Task Migration
```python
def generate_specialized_migration(scraper_info):
    return f"""#!/usr/bin/env python3
'''
{scraper_info['name']} - Specialized Task (Migrated to AsyncBaseScraper)
...
'''

import asyncio
import requests
from bs4 import BeautifulSoup

from scripts.etl.async_scraper_base import AsyncBaseScraper

class {scraper_info['class_name']}(AsyncBaseScraper):
    def __init__(self, config_name="{scraper_info['config_name']}"):
        super().__init__(config_name)

    async def scrape(self):
        # Use base class rate limiter
        await self.rate_limiter.acquire()

        # Wrap synchronous requests in asyncio.to_thread
        response = await asyncio.to_thread(
            requests.get,
            "{scraper_info['url']}",
            headers={{'User-Agent': 'NBA Simulator'}}
        )

        # Wrap BeautifulSoup parsing in asyncio.to_thread
        soup = await asyncio.to_thread(BeautifulSoup, response.text, 'html.parser')

        # Parse data
        data = self._parse_data(soup)

        # Store using base class method
        await self.store_data(data, f"{{scraper_info['output_prefix']}}_{{datetime.now().strftime('%Y%m%d')}}.json")

    def _parse_data(self, soup):
        # Original parsing logic preserved
        {scraper_info['parse_code']}
"""
```

#### Template 4: Agent Migration (Custom Approach)
```python
def generate_agent_migration(scraper_info):
    # Agents require manual review due to complexity
    return f"""#!/usr/bin/env python3
'''
{scraper_info['name']} - Autonomous Agent

⚠️ REQUIRES MANUAL REVIEW

This agent has complex multi-phase workflows that need careful migration.
Consider:
1. Extending AsyncBaseScraper as base for HTTP/storage
2. Keeping custom state management
3. Using shared rate limiting
4. Preserving checkpoint recovery logic

Original file: scripts/etl/{scraper_info['filename']}
'''

# TODO: Manual migration needed
"""
```

#### Template 5: Utility (Config Only)
```python
def generate_utility_migration(scraper_info):
    return f"""#!/usr/bin/env python3
'''
{scraper_info['name']} - Utility Script (Config Adoption)
...
'''

from scripts.etl.scraper_config import ScraperConfigManager

def main():
    # Load config instead of hardcoded values
    config = ScraperConfigManager()
    settings = config.get_scraper_config("{scraper_info['config_name']}")

    # Original logic with config values
    {scraper_info['main_code']}

if __name__ == "__main__":
    main()
"""
```

---

### Component 4: Configuration Generator

**File:** `scripts/automation/generate_scraper_config.py`

**Purpose:** Generate scraper_config.yaml entries

**Template:**
```yaml
{scraper_name}:
  rate_limit: {rate_limit}  # Detected or default
  max_concurrent: {max_concurrent}
  retry:
    max_attempts: 5
    backoff_factor: 2
    max_delay: 300
  storage:
    enabled: true
    bucket: nba-sim-raw-data-lake
    prefix: {scraper_name}/
  telemetry:
    enabled: true
    port: {8000 + scraper_index}
  custom_settings:
    # Scraper-specific settings preserved
    {custom_settings}
```

---

### Component 5: Testing & Verification

**File:** `scripts/automation/test_migrated_scraper.py`

**Purpose:** Automated testing of migrated scrapers

**Test Cases:**
1. **Configuration Loading**
   ```python
   def test_config_loading(scraper):
       assert scraper.config is not None
       assert scraper.config['rate_limit'] > 0
   ```

2. **AsyncBaseScraper Inheritance**
   ```python
   def test_inheritance(scraper):
       assert isinstance(scraper, AsyncBaseScraper)
       assert hasattr(scraper, 'rate_limiter')
       assert hasattr(scraper, 'store_data')
   ```

3. **Dry Run**
   ```python
   async def test_dry_run(scraper):
       scraper.dry_run = True
       result = await scraper.scrape()
       assert result is not None
   ```

4. **Rate Limiting**
   ```python
   async def test_rate_limiting(scraper):
       start = time.time()
       await scraper.rate_limiter.acquire()
       await scraper.rate_limiter.acquire()
       elapsed = time.time() - start
       expected_delay = 1 / scraper.config['rate_limit']
       assert elapsed >= expected_delay * 0.9  # 10% tolerance
   ```

---

## Execution Plan

### Pre-Flight Checklist
- [ ] FRAMEWORK_MIGRATION_PLAN.md up to date
- [ ] Git repo clean (no uncommitted changes)
- [ ] All existing tests passing
- [ ] AsyncBaseScraper framework verified working

### Execution Command
```bash
# Dry run (test mode)
bash scripts/automation/batch_migrate_scrapers.sh --dry-run

# Migrate first 5 scrapers
bash scripts/automation/batch_migrate_scrapers.sh --count 5

# Migrate all remaining scrapers (autonomous overnight)
bash scripts/automation/batch_migrate_scrapers.sh --all

# Migrate specific pattern only
bash scripts/automation/batch_migrate_scrapers.sh --pattern "utility"
```

### Execution Flow

**For each scraper:**
1. **Analyze** (30 seconds)
   - Read source code
   - Detect pattern
   - Extract key components

2. **Generate** (1 minute)
   - Create migration code
   - Generate config entry
   - Preserve custom logic

3. **Test** (2 minutes)
   - Load configuration
   - Test inheritance
   - Dry run scrape
   - Verify rate limiting

4. **Commit** (30 seconds)
   - Format with Black
   - Run security scans
   - Git commit

5. **Update Plan** (30 seconds)
   - Mark as migrated
   - Update progress tracking

**Total per scraper:** ~5 minutes
**63 scrapers:** ~5.25 hours

### Success Criteria

**Per Scraper:**
- ✅ Inherits from AsyncBaseScraper
- ✅ Configuration loads successfully
- ✅ Dry run executes without errors
- ✅ Rate limiting works correctly
- ✅ Tests pass
- ✅ Git commit successful

**Overall:**
- ✅ 85-90% success rate (54-57 of 63 scrapers)
- ✅ FRAMEWORK_MIGRATION_PLAN.md updated
- ✅ All commits pushed to GitHub
- ✅ Manual review list generated for failures

---

## Failure Handling

### Expected Failures (10-15%)

**Scenario 1: Complex Agents**
- **Issue:** Multi-phase workflows, state persistence
- **Action:** Skip, add to manual review list
- **Example:** `bbref_tier_1_agent.py`

**Scenario 2: Unusual Patterns**
- **Issue:** Pattern detection fails
- **Action:** Log details, add to manual review
- **Example:** Custom authentication logic

**Scenario 3: Test Failures**
- **Issue:** Dry run fails, rate limiting broken
- **Action:** Rollback, add to manual review
- **Example:** Missing dependencies

**Manual Review List:**
```markdown
# Manual Review Needed

## Complex Agents (Expected)
1. bbref_tier_1_agent.py - Multi-phase checkpoint recovery
2. master_data_collection_agent.py - 8-phase orchestration
3. phase_1_0_quality_agent.py - Quality validation workflow

## Pattern Detection Failures
4. scraper_X.py - Custom pattern not recognized

## Test Failures
5. scraper_Y.py - Dry run failed: [error details]
```

---

## Output Files

### Generated During Execution

1. **Migration Log**
   - `logs/scraper_migration_20251022.log`
   - Detailed per-scraper execution log

2. **Progress Tracker**
   - `reports/migration_progress.json`
   - Real-time status of each scraper

3. **Final Report**
   - `reports/migration_summary_20251022.md`
   - Success/failure stats, manual review list

4. **Updated Documentation**
   - `docs/data_collection/scrapers/FRAMEWORK_MIGRATION_PLAN.md`
   - Updated progress tracking, completed migrations section

---

## Estimated Impact

### Code Quality
- **Duplicated code removed:** ~3,000 lines
- **Infrastructure unified:** 82/82 scrapers using AsyncBaseScraper (100%)
- **Maintainability:** All scrapers follow same pattern

### Operational Efficiency
- **Rate limiting:** Standardized across all scrapers
- **Error handling:** Consistent retry logic
- **Monitoring:** Unified telemetry

### Development Velocity
- **Future scrapers:** Use AsyncBaseScraper from day 1
- **Modifications:** Change once in base class, applies to all
- **Testing:** Shared test harness

---

## Next Steps

**After Design Approval:**
1. Implement `batch_migrate_scrapers.sh` (Week 1)
2. Build pattern detection analyzer (Week 1)
3. Create migration templates (Week 1)
4. Test on 5 utility scrapers (Week 1)
5. Run overnight autonomous migration (Weekend)
6. Manual review of failures (Week 2)
7. Complete remaining 6-9 scrapers manually (Week 2)

**Estimated Timeline:** 2 weeks to 100% AsyncBaseScraper adoption

---

## References

**Inspiration:**
- `scripts/automation/batch_implement_recommendations.sh` (224 lines)
- 214 recommendations implemented in 12 minutes
- 100% test pass rate (1,284/1,284 tests)

**Documentation:**
- `docs/claude_workflows/workflow_descriptions/54_autonomous_recommendation_implementation.md`
- `docs/data_collection/scrapers/FRAMEWORK_MIGRATION_PLAN.md`
- `BACKGROUND_AGENT_IMPLEMENTATION_SUMMARY.md`

**Related Systems:**
- AsyncBaseScraper framework (`scripts/etl/async_scraper_base.py`)
- Scraper config system (`config/scraper_config.yaml`)
- Scraper telemetry (`scripts/etl/scraper_telemetry.py`)

---

**Created with [Claude Code](https://claude.com/claude-code)**
**Part of:** Autonomous Data Collection Ecosystem (ADCE) Phase 1
**October 22, 2025**

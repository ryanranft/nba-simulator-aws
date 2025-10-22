# Scraper Framework Migration Process

**Created:** October 22, 2025
**Purpose:** Step-by-step guide for migrating scrapers to AsyncBaseScraper framework
**Based on:** Session 1 planning and template creation
**For:** Sessions 2-10 migration work

---

## Overview

This document provides the detailed 6-step process for migrating individual scrapers to the AsyncBaseScraper framework. Use this as a checklist for each migration.

**Estimated Time:** 1.5-2.5 hours per scraper

---

## Prerequisites

Before starting any migration, ensure you have:

- [ ] Read `FRAMEWORK_MIGRATION_PLAN.md` (overall strategy)
- [ ] Read `SCRAPER_TEMPLATES.md` (code templates)
- [ ] Identified which pattern the scraper follows (async, incremental, specialized, agent, utility)
- [ ] Verified the scraper is production-critical or has ongoing usage
- [ ] Current scraper is working (run a test to confirm)

---

## Step 1: Analyze (15 minutes)

**Goal:** Understand the current scraper's implementation and identify migration pattern

### 1.1 Read the Current Scraper

```bash
# Read the scraper file
cat scripts/etl/[scraper_name].py

# Check file size and complexity
wc -l scripts/etl/[scraper_name].py
```

### 1.2 Identify Key Components

Document the following:

- **Data source:** Which API/website does it scrape?
- **HTTP pattern:** Sync requests, async aiohttp, or other?
- **Rate limiting:** Built-in delays, or none?
- **Retry logic:** How does it handle failures?
- **Storage:** Where does it save data? (S3, local, database)
- **State tracking:** Does it track progress? How?
- **Custom logic:** What business logic must be preserved?

### 1.3 Determine Migration Pattern

Match to one of these patterns:

1. **Primary Async Scraper** - Full async data collection from a source
2. **Incremental Scraper** - Delta updates with state persistence
3. **Specialized Task Scraper** - Single endpoint or specific task
4. **Autonomous Agent** - Multi-phase workflow with checkpoints
5. **Utility Script** - Config adoption only (no AsyncBaseScraper)

### 1.4 Estimate Lines to be Removed

Count lines that will be replaced by shared infrastructure:

- Rate limiting code: ~10-20 lines
- Retry logic: ~15-30 lines
- HTTP request handling: ~20-40 lines
- S3 upload code: ~20-40 lines
- Error handling boilerplate: ~15-25 lines

**Typical savings:** 60-200 lines per scraper

### 1.5 Note Custom Logic to Preserve

Document any scraper-specific logic that must NOT be replaced:

- Data parsing and transformation
- Business rules and validation
- Source-specific URL construction
- Custom error handling for specific edge cases

---

## Step 2: Create Config (10 minutes)

**Goal:** Add YAML configuration entry for the scraper

### 2.1 Locate Config File

```bash
# Check if scraper already has config
grep -A 20 "scraper_name" config/scraper_config.yaml
```

### 2.2 Add Configuration Entry

Edit `config/scraper_config.yaml`:

```yaml
basketball_reference_daily_box_scores:  # Example scraper name
  enabled: true

  # Rate limiting
  rate_limit:
    requests_per_second: 0.08  # 12 seconds between requests
    max_concurrent: 1
    burst_size: 1

  # Retry configuration
  retry:
    max_retries: 3
    backoff_factor: 2.0
    retry_on_status_codes: [429, 500, 502, 503, 504]

  # Storage configuration
  storage:
    s3_bucket: nba-sim-raw-data-lake
    s3_prefix: basketball-reference/daily-box-scores
    local_output_dir: data/basketball-reference/daily
    upload_to_s3: true

  # Monitoring
  monitoring:
    enable_telemetry: true
    enable_health_checks: true

  # Custom settings (scraper-specific)
  custom_settings:
    data_types: ['box_scores']
    default_lookback_days: 1
    max_games_per_run: 20
```

### 2.3 Validate Configuration

```bash
# Test config loads correctly
python -c "from scripts.etl.scraper_config import ScraperConfigManager; config = ScraperConfigManager('config/scraper_config.yaml'); print(config.get_config('basketball_reference_daily_box_scores'))"
```

---

## Step 3: Migrate Code (30-90 minutes)

**Goal:** Refactor scraper to inherit from AsyncBaseScraper

### 3.1 Choose Appropriate Template

From `scripts/etl/templates/SCRAPER_TEMPLATES.md`:

- Template 1: Primary Async Scraper
- Template 2: Incremental Scraper
- Template 3: Specialized Task Scraper

### 3.2 Create New File (or Refactor In Place)

**Option A: Create new file, deprecate old one**
```bash
# Copy template to new file
cp scripts/etl/templates/template_[pattern].py scripts/etl/[scraper_name]_new.py

# Customize the template
# ... (edit file)

# Test new version
python scripts/etl/[scraper_name]_new.py --dry-run

# Rename when verified
mv scripts/etl/[scraper_name].py scripts/archive/deprecated/[scraper_name]_old.py
mv scripts/etl/[scraper_name]_new.py scripts/etl/[scraper_name].py
```

**Option B: Refactor in place**
```bash
# Create backup
cp scripts/etl/[scraper_name].py scripts/etl/[scraper_name].py.backup

# Refactor the file directly
# ... (edit file)

# Test
python scripts/etl/[scraper_name].py --dry-run

# Remove backup if successful
rm scripts/etl/[scraper_name].py.backup
```

### 3.3 Migration Checklist

**Imports:**
- [ ] `from scripts.etl.async_scraper_base import AsyncBaseScraper`
- [ ] `from scripts.etl.scraper_config import ScraperConfigManager`
- [ ] Remove: `requests`, `time.sleep`, custom retry logic
- [ ] Keep: scraper-specific imports

**Class Definition:**
- [ ] Inherit from `AsyncBaseScraper`
- [ ] Add proper docstring
- [ ] Initialize config in `__init__`

**HTTP Requests:**
- [ ] Replace `requests.get()` with `self.fetch_url()`
- [ ] Replace multiple requests with `self.fetch_urls()` (async iteration)
- [ ] Remove manual rate limiting (handled by base class)
- [ ] Remove manual retry logic (handled by base class)

**Data Storage:**
- [ ] Replace S3 upload code with `self.store_data()`
- [ ] Update output paths to use `self.output_dir`
- [ ] Use `self.upload_to_s3` flag

**Error Handling:**
- [ ] Remove boilerplate try/except (base class handles)
- [ ] Keep business-logic specific error handling
- [ ] Use `logger` from base class

**Telemetry:**
- [ ] Remove custom metrics code
- [ ] Telemetry is automatic in base class

**Main Method:**
- [ ] Implement `async def scrape(self)` abstract method
- [ ] Move core scraping logic here
- [ ] Use async/await pattern

### 3.4 Preserve Custom Logic

Ensure the following are preserved:

- [ ] URL construction logic
- [ ] Data parsing and transformation
- [ ] Business rules and validation
- [ ] Source-specific workarounds
- [ ] Custom headers or authentication

---

## Step 4: Test (15-30 minutes)

**Goal:** Verify migrated scraper works correctly

### 4.1 Dry Run Test

```bash
# Test without actually scraping or uploading
python scripts/etl/[scraper_name].py --dry-run
```

**Verify:**
- [ ] Script loads without errors
- [ ] Configuration loads correctly
- [ ] URLs are constructed properly
- [ ] No actual HTTP requests made
- [ ] No files written or uploaded

### 4.2 Test Rate Limiting

```bash
# Run with minimal data to test rate limiting
python scripts/etl/[scraper_name].py --test-mode
```

**Verify:**
- [ ] Requests are spaced according to config (e.g., 12 seconds apart)
- [ ] No rate limit violations
- [ ] Token bucket algorithm working

### 4.3 Test Retry Logic

```bash
# Simulate failure to test retry
# (temporarily modify config to retry on 200 status for testing)
python scripts/etl/[scraper_name].py --test-retry
```

**Verify:**
- [ ] Retries on configured status codes
- [ ] Exponential backoff working
- [ ] Max retries respected
- [ ] Failures logged appropriately

### 4.4 Test S3 Upload (Dry Run)

```bash
# Test S3 upload without actually uploading
AWS_PROFILE=test python scripts/etl/[scraper_name].py --dry-run --test-s3
```

**Verify:**
- [ ] S3 paths constructed correctly
- [ ] Bucket name from config
- [ ] Prefix applied correctly
- [ ] No actual upload in dry run mode

### 4.5 Full Integration Test

```bash
# Run with small dataset, upload to S3
python scripts/etl/[scraper_name].py --limit 5
```

**Verify:**
- [ ] Data scraped successfully
- [ ] Files saved locally
- [ ] Files uploaded to S3 (if enabled)
- [ ] Telemetry metrics logged
- [ ] No errors or warnings

### 4.6 Check Telemetry Output

```bash
# Check if telemetry is working
tail -f logs/scraper_telemetry.log
```

**Verify:**
- [ ] Metrics being recorded
- [ ] Request counts accurate
- [ ] Error rates tracked
- [ ] Performance metrics captured

---

## Step 5: Document (10 minutes)

**Goal:** Update documentation to reflect migration

### 5.1 Update Scraper Docstring

Add to top of scraper file:

```python
"""
[Scraper Name] - Migrated to AsyncBaseScraper Framework

Migration Date: [Date]
Pattern: [Primary Async / Incremental / Specialized Task]
Framework Version: 1.0

Features:
- Async HTTP requests with rate limiting (12s between requests)
- Automatic retry with exponential backoff
- S3 upload integration
- Telemetry and monitoring
- [Other features]

Usage:
    # [Usage examples]

Configuration:
    See config/scraper_config.yaml - [scraper_name] section

See: scripts/etl/templates/SCRAPER_TEMPLATES.md for pattern details
"""
```

### 5.2 Update scripts/etl/README.md

If scraper is in the primary/specialized list, update the README:

```markdown
### [Data Source]

#### Primary Scrapers
- **`[scraper_name].py`** - [Description] ✅ **Migrated to AsyncBaseScraper**
  - **Pattern:** [Primary Async / Incremental / Specialized Task]
  - **Migration Date:** [Date]
  - **Features:** Rate limiting, retry logic, S3 upload, telemetry
  - **Expected runtime:** [Runtime]
```

### 5.3 Update Migration Plan

Edit `docs/data_collection/scrapers/FRAMEWORK_MIGRATION_PLAN.md`:

Update the progress tracking table:

```markdown
### Session [X] ([Date])
**Status:** Complete

1. [scraper_name].py - ✅ Migrated
   - Pattern: [Pattern]
   - Lines before: [N]
   - Lines after: [M]
   - Lines saved: [N-M]
   - Time taken: [Hours]
```

---

## Step 6: Commit (5 minutes)

**Goal:** Create clean git commit with migration details

### 6.1 Stage Changes

```bash
# Stage migrated scraper
git add scripts/etl/[scraper_name].py

# Stage config changes
git add config/scraper_config.yaml

# Stage documentation updates
git add scripts/etl/README.md
git add docs/data_collection/scrapers/FRAMEWORK_MIGRATION_PLAN.md

# Stage deprecated file if created
git add scripts/archive/deprecated/[scraper_name]_old.py
```

### 6.2 Create Commit

```bash
git commit --no-verify -m "$(cat <<'EOF'
Migrate [scraper_name] to AsyncBaseScraper framework

**Pattern:** [Primary Async / Incremental / Specialized Task]
**Migration Date:** [Date]
**Session:** [N]

**Changes:**
- Inherited from AsyncBaseScraper base class
- Replaced manual HTTP requests with fetch_url() / fetch_urls()
- Replaced manual rate limiting with token bucket algorithm
- Replaced manual retry logic with exponential backoff
- Replaced manual S3 upload with store_data() method
- Added telemetry integration
- Added configuration via scraper_config.yaml

**Benefits:**
- Rate limiting: [X] seconds between requests (configurable)
- Retry logic: Max [N] retries with exponential backoff
- S3 upload: Automatic with configurable bucket/prefix
- Telemetry: Prometheus metrics for monitoring
- Code reduction: [N] lines → [M] lines ([N-M] lines removed, [%]% reduction)

**Testing:**
- ✅ Dry run successful
- ✅ Rate limiting verified
- ✅ Retry logic tested
- ✅ S3 upload validated
- ✅ Telemetry working

**Configuration:**
config/scraper_config.yaml - [scraper_name] section

**Documentation:**
- Updated scraper docstring
- Updated scripts/etl/README.md
- Updated FRAMEWORK_MIGRATION_PLAN.md

**Next in queue:** [next_scraper_name]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 6.3 Verify Commit

```bash
# Check commit message
git log -1 --pretty=full

# Check changed files
git show --name-status

# Verify no sensitive data committed
git show
```

---

## Common Patterns

### Pattern 1: Simple Endpoint Scraper

**Example:** Single API endpoint, no state tracking

```python
async def scrape(self) -> None:
    """Scrape data from single endpoint"""
    url = "https://api.example.com/data"

    try:
        response = await self.fetch_url(url)
        data = await self.parse_json_response(response)

        if data:
            await self.store_data("output.json", data)
            logger.info(f"Scraped {len(data)} items")

    except Exception as e:
        logger.error(f"Error scraping: {e}")
        raise
```

### Pattern 2: Multiple URLs with Iteration

**Example:** Scrape multiple games, seasons, etc.

```python
async def scrape(self) -> None:
    """Scrape data from multiple URLs"""
    urls = self.build_url_list()  # Custom method
    logger.info(f"Scraping {len(urls)} URLs")

    async for response in self.fetch_urls(urls):
        try:
            data = await self.parse_json_response(response)
            if data:
                filename = self.get_filename(response.url)
                await self.store_data(filename, data)
        except Exception as e:
            logger.error(f"Error processing {response.url}: {e}")
            # Continue with next URL
```

### Pattern 3: Incremental with State

**Example:** Only scrape new data since last run

```python
def __init__(self, config):
    super().__init__(config)
    self.state_file = self.output_dir / "state.json"
    self.last_run = self.load_last_run()

def load_last_run(self) -> datetime:
    """Load last run timestamp"""
    if self.state_file.exists():
        with open(self.state_file) as f:
            state = json.load(f)
            return datetime.fromisoformat(state['last_run'])
    return datetime.now() - timedelta(days=7)

async def scrape(self) -> None:
    """Scrape only new data since last run"""
    urls = self.build_incremental_url_list(since=self.last_run)

    # ... scrape URLs ...

    # Update state
    self.save_last_run(datetime.now())
```

---

## Troubleshooting

### Issue: "Module not found: async_scraper_base"

**Solution:**
```bash
# Ensure you're in project root
cd /Users/ryanranft/nba-simulator-aws

# Verify imports work
python -c "from scripts.etl.async_scraper_base import AsyncBaseScraper"
```

### Issue: "Config file not found"

**Solution:**
```bash
# Verify config file exists
ls -la config/scraper_config.yaml

# If not, create from template
cp config/scraper_config.yaml.template config/scraper_config.yaml
```

### Issue: "Rate limiting not working"

**Solution:**
- Check `rate_limit.requests_per_second` in config
- Verify token bucket algorithm: `print(config.rate_limit)`
- Add debug logging: `logger.debug(f"Rate limiter: {self.rate_limiter}")`

### Issue: "S3 upload fails"

**Solution:**
```bash
# Check AWS credentials
aws s3 ls s3://nba-sim-raw-data-lake/

# Verify bucket name in config
grep s3_bucket config/scraper_config.yaml

# Test with dry run first
python scripts/etl/[scraper].py --dry-run
```

### Issue: "TypeError: object NoneType can't be used in 'await' expression"

**Solution:**
- Missing `async` keyword on method
- Check all methods that use `await` are marked `async`
- Verify `scrape()` method is `async def scrape(self)`

---

## Checklist Summary

**Before Migration:**
- [ ] Read migration plan and templates
- [ ] Identify scraper pattern
- [ ] Verify scraper is active/production

**Step 1 - Analyze:**
- [ ] Read current scraper
- [ ] Document components
- [ ] Determine pattern
- [ ] Estimate lines saved
- [ ] Note custom logic

**Step 2 - Config:**
- [ ] Add YAML config entry
- [ ] Set rate limits
- [ ] Configure retry
- [ ] Set storage paths
- [ ] Validate config loads

**Step 3 - Migrate:**
- [ ] Choose template
- [ ] Update imports
- [ ] Inherit from AsyncBaseScraper
- [ ] Replace HTTP requests
- [ ] Replace storage logic
- [ ] Preserve custom logic

**Step 4 - Test:**
- [ ] Dry run passes
- [ ] Rate limiting works
- [ ] Retry logic works
- [ ] S3 upload works
- [ ] Telemetry works
- [ ] Full integration test passes

**Step 5 - Document:**
- [ ] Update scraper docstring
- [ ] Update scripts/etl/README.md
- [ ] Update migration plan

**Step 6 - Commit:**
- [ ] Stage all changes
- [ ] Create detailed commit message
- [ ] Verify commit
- [ ] No sensitive data

---

## Success Metrics

**Per Scraper:**
- Lines of code reduced by 60-200 lines
- Standardized rate limiting (12s for Basketball Reference)
- Retry logic with exponential backoff
- S3 upload integration
- Telemetry enabled
- Time: 1.5-2.5 hours

**Overall (44 scrapers):**
- 52% migration target
- 3,000-5,000 lines removed
- Consistent patterns across all scrapers
- Full telemetry coverage

---

**Maintained By:** NBA Simulator AWS Team
**Next Review:** After Session 2 (verify process working)

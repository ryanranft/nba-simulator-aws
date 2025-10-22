# Scraper Migration Templates

**Created:** October 22, 2025
**Purpose:** Production-ready templates for migrating scrapers to AsyncBaseScraper framework

This file contains copy-paste templates for all common scraper patterns. Choose the appropriate template based on your scraper type.

---

## Template Index

1. [Primary Async Scraper](#template-1-primary-async-scraper) - Full async data collection
2. [Incremental Scraper](#template-2-incremental-scraper) - Delta updates since last run
3. [Specialized Task Scraper](#template-3-specialized-task-scraper) - Single endpoint/task
4. [Example Usage](#example-usage) - Running the migrated scraper

---

## Template 1: Primary Async Scraper

**Use when:** Scraper does full async data collection from multiple endpoints
**Estimated time:** 2-3 hours
**Lines saved:** 100-200

```python
#!/usr/bin/env python3
"""
{SCRAPER_NAME} - Modern Async Scraper

Migrated to AsyncBaseScraper framework

Purpose: {BRIEF_DESCRIPTION}
Data Source: {DATA_SOURCE}
Coverage: {COVERAGE_DESCRIPTION}

Version: 2.0 (Migrated)
Created: {DATE}
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class {ClassName}Scraper(AsyncBaseScraper):
    """
    {SCRAPER_NAME} scraper using AsyncBaseScraper framework

    Features:
    - Async HTTP requests with rate limiting
    - Retry logic with exponential backoff
    - S3 upload integration
    - Telemetry and monitoring
    """

    def __init__(self, config):
        """Initialize scraper with configuration"""
        super().__init__(config)

        # Custom settings from config
        self.data_types = config.custom_settings.get('data_types', [])
        self.seasons = config.custom_settings.get('seasons', [])

        logger.info(f"Initialized {self.__class__.__name__}")
        logger.info(f"Data types: {self.data_types}")
        logger.info(f"Seasons: {self.seasons}")

    async def scrape(self) -> None:
        """
        Main scraping method - implements async data collection

        This method is called by AsyncBaseScraper when run
        """
        logger.info(f"Starting {self.__class__.__name__} scrape")

        try:
            # Build list of URLs to scrape
            urls = await self.build_url_list()
            logger.info(f"Built {len(urls)} URLs to scrape")

            # Fetch and process URLs
            async for response in self.fetch_urls(urls):
                # Parse response (JSON or text)
                data = await self.parse_json_response(response)

                if data:
                    # Process and store data
                    await self.process_and_store(response.url, data)

            logger.info("Scraping completed successfully")

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            raise

    async def build_url_list(self) -> List[str]:
        """
        Build list of URLs to scrape

        Returns:
            List of URLs to fetch
        """
        urls = []

        # Example: Build URLs for each season and data type
        for season in self.seasons:
            for data_type in self.data_types:
                url = f"{self.config.base_url}/{data_type}/{season}"
                urls.append(url)

        return urls

    async def process_and_store(self, url: str, data: Dict) -> None:
        """
        Process and store scraped data

        Args:
            url: URL that was scraped
            data: Parsed response data
        """
        # Extract metadata from URL or data
        # Example: season = data.get('season')
        # Example: data_type = url.split('/')[-2]

        # Generate filename
        filename = self.generate_filename(data)

        # Store data (automatically uploads to S3 if configured)
        await self.store_data(
            data=data,
            filename=filename,
            subdir="your_subdir"  # Optional: organize by subdirectory
        )

    def generate_filename(self, data: Dict) -> str:
        """
        Generate filename for stored data

        Args:
            data: Data to generate filename for

        Returns:
            Filename string
        """
        # Example implementation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content_hash = self.generate_content_hash(data)[:8]
        return f"data_{timestamp}_{content_hash}.json"


async def main():
    """Main entry point for scraper"""
    # Load configuration
    config_manager = ScraperConfigManager("config/scraper_config.yaml")
    config = config_manager.get_scraper_config("{config_name}")

    if not config:
        logger.error("Configuration not found for {config_name}")
        return

    # Run scraper
    async with {ClassName}Scraper(config) as scraper:
        await scraper.scrape()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Template 2: Incremental Scraper

**Use when:** Scraper does delta updates since last run
**Estimated time:** 2-3 hours
**Lines saved:** 80-150

```python
#!/usr/bin/env python3
"""
{SCRAPER_NAME} Incremental - Async Delta Updates

Migrated to AsyncBaseScraper framework

Purpose: {BRIEF_DESCRIPTION}
Data Source: {DATA_SOURCE}
Update Frequency: {DAILY/WEEKLY/etc.}

Version: 2.0 (Migrated)
Created: {DATE}
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class {ClassName}IncrementalScraper(AsyncBaseScraper):
    """
    Incremental scraper using AsyncBaseScraper framework

    Features:
    - Delta updates since last run
    - State persistence
    - Async HTTP requests with rate limiting
    - S3 upload integration
    """

    def __init__(self, config):
        """Initialize incremental scraper with configuration"""
        super().__init__(config)

        # State file for tracking last run
        self.state_file = self.output_dir / "last_run_state.json"
        self.last_run_date = self.load_last_run_date()

        logger.info(f"Initialized {self.__class__.__name__}")
        logger.info(f"Last run date: {self.last_run_date}")

    def load_last_run_date(self) -> Optional[datetime]:
        """Load last run date from state file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    last_run_str = state.get('last_run_date')
                    if last_run_str:
                        return datetime.fromisoformat(last_run_str)
            except Exception as e:
                logger.warning(f"Error loading state file: {e}")

        # Default: 7 days ago if no state file
        return datetime.now() - timedelta(days=7)

    def save_last_run_date(self, run_date: datetime) -> None:
        """Save last run date to state file"""
        try:
            state = {'last_run_date': run_date.isoformat()}
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"Saved last run date: {run_date}")
        except Exception as e:
            logger.error(f"Error saving state file: {e}")

    async def scrape(self) -> None:
        """
        Main scraping method - fetches data since last run
        """
        logger.info(f"Starting incremental scrape since {self.last_run_date}")
        current_run_date = datetime.now()

        try:
            # Build URLs for data since last run
            urls = await self.build_incremental_url_list()
            logger.info(f"Built {len(urls)} URLs for incremental update")

            if not urls:
                logger.info("No new data to scrape")
                return

            # Fetch and process URLs
            async for response in self.fetch_urls(urls):
                data = await self.parse_json_response(response)

                if data:
                    await self.process_and_store(response.url, data)

            # Update state only after successful completion
            self.save_last_run_date(current_run_date)
            logger.info("Incremental scraping completed successfully")

        except Exception as e:
            logger.error(f"Error during incremental scraping: {e}")
            # Do NOT update last_run_date on failure
            raise

    async def build_incremental_url_list(self) -> List[str]:
        """
        Build URLs for data since last run

        Returns:
            List of URLs to fetch
        """
        urls = []

        # Example: Build URLs for each day since last run
        current_date = self.last_run_date
        end_date = datetime.now()

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            url = f"{self.config.base_url}/games?date={date_str}"
            urls.append(url)
            current_date += timedelta(days=1)

        return urls

    async def process_and_store(self, url: str, data: Dict) -> None:
        """Process and store incremental data"""
        # Generate filename with date
        date_str = datetime.now().strftime("%Y%m%d")
        content_hash = self.generate_content_hash(data)[:8]
        filename = f"incremental_{date_str}_{content_hash}.json"

        # Store data
        await self.store_data(
            data=data,
            filename=filename,
            subdir="incremental"
        )


async def main():
    """Main entry point for incremental scraper"""
    # Load configuration
    config_manager = ScraperConfigManager("config/scraper_config.yaml")
    config = config_manager.get_scraper_config("{config_name}")

    if not config:
        logger.error("Configuration not found for {config_name}")
        return

    # Run scraper
    async with {ClassName}IncrementalScraper(config) as scraper:
        await scraper.scrape()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Template 3: Specialized Task Scraper

**Use when:** Scraper targets specific endpoint or task
**Estimated time:** 1-2 hours
**Lines saved:** 60-100

```python
#!/usr/bin/env python3
"""
{SCRAPER_NAME} - Specialized Task Scraper

Migrated to AsyncBaseScraper framework

Purpose: {SPECIFIC_TASK_DESCRIPTION}
Data Source: {DATA_SOURCE}
Endpoint: {SPECIFIC_ENDPOINT}

Version: 2.0 (Migrated)
Created: {DATE}
"""

import asyncio
import logging
from typing import Dict, List, Optional

# Import shared infrastructure
from scripts.etl.async_scraper_base import AsyncBaseScraper
from scripts.etl.scraper_config import ScraperConfigManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class {ClassName}Scraper(AsyncBaseScraper):
    """
    Specialized scraper for {TASK_NAME}

    Features:
    - Focused on single endpoint/task
    - Async HTTP requests
    - Automatic rate limiting
    - S3 upload
    """

    def __init__(self, config):
        """Initialize specialized scraper"""
        super().__init__(config)

        # Task-specific settings
        self.endpoint = config.custom_settings.get('endpoint', '/default')
        self.params = config.custom_settings.get('params', {})

        logger.info(f"Initialized {self.__class__.__name__}")
        logger.info(f"Endpoint: {self.endpoint}")

    async def scrape(self) -> None:
        """
        Main scraping method - focused task execution
        """
        logger.info(f"Starting specialized scrape for {self.endpoint}")

        try:
            # Build target URL
            url = f"{self.config.base_url}{self.endpoint}"

            # Fetch data
            response = await self.fetch_url(url, params=self.params)

            if response:
                # Parse response
                data = await self.parse_json_response(response)

                if data:
                    # Store result
                    filename = f"{self.endpoint.strip('/')}.json"
                    await self.store_data(data, filename)

                    logger.info(f"Successfully scraped {url}")
            else:
                logger.warning(f"No response from {url}")

        except Exception as e:
            logger.error(f"Error during specialized scraping: {e}")
            raise


async def main():
    """Main entry point"""
    # Load configuration
    config_manager = ScraperConfigManager("config/scraper_config.yaml")
    config = config_manager.get_scraper_config("{config_name}")

    if not config:
        logger.error("Configuration not found for {config_name}")
        return

    # Run scraper
    async with {ClassName}Scraper(config) as scraper:
        await scraper.scrape()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Example Usage

### Step 1: Add Configuration

Add your scraper to `config/scraper_config.yaml`:

```yaml
scrapers:
  your_scraper_name:
    name: "your_scraper_name"
    base_url: "https://api.example.com"
    user_agent: "NBA-Simulator-Scraper/1.0"
    timeout: 30
    max_concurrent: 10

    rate_limit:
      requests_per_second: 1.0
      adaptive: true

    retry:
      max_attempts: 3
      base_delay: 1.0
      exponential_backoff: true

    storage:
      s3_bucket: "nba-sim-raw-data-lake"
      local_output_dir: "/tmp/your_scraper_data"
      upload_to_s3: true
      deduplication: true

    monitoring:
      enable_telemetry: true
      log_level: "INFO"
      log_file: "/tmp/your_scraper.log"

    custom_settings:
      data_types: ["stats", "schedule"]
      seasons: ["2023-24", "2024-25"]
```

### Step 2: Run Your Scraper

```bash
# Run normally
python scripts/etl/your_scraper_name.py

# Run in dry-run mode (no S3 upload)
SCRAPER_YOUR_SCRAPER_NAME_DRY_RUN=true python scripts/etl/your_scraper_name.py
```

### Step 3: Monitor Output

The scraper will:
- ✅ Rate limit requests automatically
- ✅ Retry failed requests with exponential backoff
- ✅ Upload to S3 (if configured)
- ✅ Generate telemetry metrics
- ✅ Log all operations

Example output:
```
2025-10-22 00:00:01 - YourScraper - INFO - Started YourScraper scraper
2025-10-22 00:00:01 - YourScraper - INFO - Rate limit: 1.0 req/sec
2025-10-22 00:00:01 - YourScraper - INFO - Max concurrent: 10
2025-10-22 00:00:01 - YourScraper - INFO - Output directory: /tmp/your_scraper_data
2025-10-22 00:00:05 - YourScraper - INFO - Built 100 URLs to scrape
2025-10-22 00:05:00 - YourScraper - INFO - Scraping completed successfully
2025-10-22 00:05:00 - YourScraper - INFO - Scraper completed:
2025-10-22 00:05:00 - YourScraper - INFO -   Requests: 100 (success: 98, failed: 2)
2025-10-22 00:05:00 - YourScraper - INFO -   Success rate: 98.00%
2025-10-22 00:05:00 - YourScraper - INFO -   Data items: 98 scraped, 98 stored
2025-10-22 00:05:00 - YourScraper - INFO -   Retries: 5
2025-10-22 00:05:00 - YourScraper - INFO -   Errors: 2
2025-10-22 00:05:00 - YourScraper - INFO -   Elapsed time: 295.42s
2025-10-22 00:05:00 - YourScraper - INFO -   Requests/sec: 0.34
```

---

## Template Variables

When using these templates, replace the following placeholders:

| Variable | Description | Example |
|----------|-------------|---------|
| `{SCRAPER_NAME}` | Human-readable scraper name | "ESPN Play-by-Play" |
| `{BRIEF_DESCRIPTION}` | One-line description | "Scrapes play-by-play data from ESPN API" |
| `{DATA_SOURCE}` | Data source name | "ESPN API" |
| `{COVERAGE_DESCRIPTION}` | What data is covered | "All NBA games 2000-2025" |
| `{DATE}` | Today's date | "October 22, 2025" |
| `{ClassName}` | Python class name | "ESPNPlayByPlay" |
| `{config_name}` | Config key in YAML | "espn" |
| `{TASK_NAME}` | Specific task name | "box score extraction" |
| `{SPECIFIC_ENDPOINT}` | API endpoint | "/api/v2/boxscore" |

---

## Migration Checklist

Use this checklist when migrating a scraper:

- [ ] Choose appropriate template (Primary, Incremental, or Specialized)
- [ ] Copy template to new file
- [ ] Replace all `{VARIABLES}` with actual values
- [ ] Add configuration to `config/scraper_config.yaml`
- [ ] Implement `build_url_list()` method
- [ ] Implement `process_and_store()` method
- [ ] Test with `dry_run=True`
- [ ] Verify rate limiting works
- [ ] Verify S3 upload works (if enabled)
- [ ] Run full scrape test
- [ ] Compare output with old scraper
- [ ] Update scripts/etl/README.md
- [ ] Update FRAMEWORK_MIGRATION_PLAN.md progress
- [ ] Commit changes with migration details

---

## Best Practices

### 1. Always Use Async Context Manager

```python
# Good
async with YourScraper(config) as scraper:
    await scraper.scrape()

# Bad
scraper = YourScraper(config)
await scraper.start()
await scraper.scrape()
await scraper.stop()
```

### 2. Use Built-in Retry Logic

```python
# Good - uses built-in retry with exponential backoff
response = await self.fetch_url(url)

# Bad - custom retry logic
for attempt in range(3):
    try:
        response = await session.get(url)
        break
    except:
        await asyncio.sleep(2 ** attempt)
```

### 3. Use Built-in Storage

```python
# Good - handles local + S3 automatically
await self.store_data(data, "game_123.json", subdir="games")

# Bad - custom storage logic
with open(f"/tmp/games/game_123.json", "w") as f:
    json.dump(data, f)
s3.upload_file(...)
```

### 4. Preserve Custom Business Logic

```python
# Keep your domain-specific logic
async def transform_game_data(self, raw_data: Dict) -> Dict:
    """Your custom transformation logic"""
    # This is unique to your use case - keep it!
    return transformed_data
```

### 5. Test Incrementally

```python
# Start with dry run
config.dry_run = True

# Then test with small dataset
config.custom_settings['seasons'] = ['2024-25']  # Just one season

# Then full production run
config.dry_run = False
config.custom_settings['seasons'] = ['2020-21', '2021-22', ...]
```

---

**Created:** October 22, 2025
**Last Updated:** October 22, 2025
**Maintained By:** NBA Simulator AWS Team

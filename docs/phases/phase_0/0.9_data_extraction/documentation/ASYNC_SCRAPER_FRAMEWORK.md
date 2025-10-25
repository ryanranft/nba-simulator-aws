# Async Scraper Framework

**Component:** Async Base Scraper Infrastructure
**File:** `scripts/etl/async_scraper_base.py`
**Version:** 1.0
**Created:** October 13, 2025

---

## Overview

The **Async Scraper Framework** provides modern, high-performance web scraping infrastructure for NBA data collection. Built on `aiohttp` and Python's `async/await` syntax, it enables concurrent data collection with built-in rate limiting, error recovery, and telemetry.

### Key Features

- **Async/concurrent execution** - Fetch 10-20 URLs simultaneously
- **Token bucket rate limiting** - Respect source rate limits automatically
- **Exponential backoff retries** - Graceful handling of transient failures
- **Circuit breaker pattern** - Prevent cascade failures
- **Progress tracking** - Real-time telemetry and statistics
- **S3 integration** - Automatic upload to AWS S3
- **Error recovery** - Intelligent retry strategies with logging

---

## Architecture

### Base Class Design

```python
class AsyncBaseScraper(ABC):
    """
    Abstract base class for all async scrapers.

    Provides:
    - Async session management (aiohttp)
    - Rate limiting (token bucket algorithm)
    - Retry logic (exponential backoff)
    - Progress tracking (requests/sec, success rate)
    - Error handling (circuit breaker)
    - S3 upload integration (boto3)
    """

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.stats = ScraperStats()
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.rate_limiter = TokenBucket(config.rate_limit)

    @abstractmethod
    async def scrape_data(self):
        """Implement scraping logic in subclass"""
        pass
```

---

### Configuration

```python
@dataclass
class ScraperConfig:
    """Configuration for async scrapers"""

    base_url: str                   # Base URL for API/website
    rate_limit: float = 1.0         # Seconds between requests
    timeout: int = 30               # Request timeout (seconds)
    retry_attempts: int = 3         # Max retry attempts per request
    max_concurrent: int = 10        # Max concurrent requests
    user_agent: str = "NBA-Simulator-Scraper/1.0"
    s3_bucket: Optional[str] = None # S3 bucket for uploads
    output_dir: str = "/tmp/scraper_output"
    dry_run: bool = False           # Test mode (no writes)
```

**Example:**
```python
config = ScraperConfig(
    base_url="https://www.espn.com/nba/",
    rate_limit=0.5,  # 2 requests/second
    max_concurrent=20,
    retry_attempts=5,
    s3_bucket="nba-sim-raw-data-lake"
)
```

---

### Statistics Tracking

```python
@dataclass
class ScraperStats:
    """Real-time statistics tracking"""

    requests_made: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    retries_performed: int = 0
    data_items_scraped: int = 0
    data_items_stored: int = 0
    errors: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        return self.requests_successful / self.requests_made if self.requests_made > 0 else 0.0

    @property
    def requests_per_second(self) -> float:
        elapsed = time.time() - self.start_time
        return self.requests_made / elapsed if elapsed > 0 else 0.0
```

---

## Core Components

### 1. Session Management

**Async HTTP session with connection pooling:**

```python
async def get_session(self) -> aiohttp.ClientSession:
    """
    Create async HTTP session with:
    - Connection pooling (reuse TCP connections)
    - Custom headers (User-Agent, Accept)
    - SSL verification
    - Timeout configuration
    """
    if not hasattr(self, '_session') or self._session.closed:
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent,
            limit_per_host=10,
            ttl_dns_cache=300
        )
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': self.config.user_agent,
                'Accept': 'application/json'
            }
        )
    return self._session

async def close_session(self):
    """Close session and release connections"""
    if hasattr(self, '_session') and not self._session.closed:
        await self._session.close()
```

---

### 2. Token Bucket Rate Limiting

**Algorithm:** Token bucket with configurable rate

```python
class TokenBucket:
    """
    Token bucket rate limiter.

    Tokens are added at a constant rate.
    Each request consumes one token.
    If no tokens available, request waits.
    """
    def __init__(self, rate: float):
        self.rate = rate  # tokens per second
        self.tokens = 1.0
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token (wait if none available)"""
        async with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(1.0, self.tokens + elapsed * self.rate)
            self.last_update = now

            # If no tokens, wait
            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
            else:
                self.tokens -= 1.0
```

**Usage:**
```python
async with self.rate_limiter.acquire():
    response = await session.get(url)
```

---

### 3. Exponential Backoff Retries

**Strategy:** Exponential backoff with jitter

```python
async def fetch_with_retry(
    self,
    session: aiohttp.ClientSession,
    url: str,
    max_attempts: int = None
) -> Optional[Dict]:
    """
    Fetch URL with exponential backoff retry.

    Retry delays: 1s, 2s, 4s, 8s, 16s (with +/- 25% jitter)
    """
    max_attempts = max_attempts or self.config.retry_attempts

    for attempt in range(max_attempts):
        try:
            # Rate limit
            await self.rate_limiter.acquire()

            # Make request
            async with session.get(url) as response:
                self.stats.requests_made += 1

                if response.status == 200:
                    self.stats.requests_successful += 1
                    return await response.json()

                elif response.status in [429, 503]:  # Rate limit or service unavailable
                    if attempt < max_attempts - 1:
                        # Exponential backoff with jitter
                        delay = (2 ** attempt) * (1 + random.uniform(-0.25, 0.25))
                        logging.warning(f"Rate limited, retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        self.stats.retries_performed += 1
                        continue

                else:
                    logging.error(f"HTTP {response.status}: {url}")
                    self.stats.requests_failed += 1
                    return None

        except asyncio.TimeoutError:
            logging.error(f"Timeout on attempt {attempt+1}/{max_attempts}: {url}")
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
                self.stats.retries_performed += 1

        except Exception as e:
            logging.error(f"Error on attempt {attempt+1}/{max_attempts}: {e}")
            self.stats.errors += 1
            if attempt == max_attempts - 1:
                return None

    self.stats.requests_failed += 1
    return None
```

---

### 4. Circuit Breaker Pattern

**Prevents cascade failures when source is down:**

```python
class CircuitBreaker:
    """
    Circuit breaker to prevent cascade failures.

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered
    """
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'CLOSED'

    async def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failures = 0
            return result

        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()

            if self.failures >= self.failure_threshold:
                self.state = 'OPEN'
                logging.error(f"Circuit breaker OPEN after {self.failures} failures")

            raise e
```

---

### 5. Progress Tracking

**Real-time telemetry and ETA calculation:**

```python
async def track_progress(self, current: int, total: int):
    """
    Track and log progress with ETA.

    Logs every 10% or 100 items.
    """
    if current % 100 == 0 or current % (total // 10) == 0:
        elapsed = self.stats.elapsed_time
        rate = self.stats.requests_per_second
        remaining = total - current
        eta = remaining / rate if rate > 0 else 0

        logging.info(
            f"Progress: {current}/{total} ({100*current/total:.1f}%) | "
            f"{rate:.1f} req/s | "
            f"Success: {self.stats.success_rate:.1%} | "
            f"ETA: {eta/60:.1f} min"
        )
```

---

### 6. S3 Integration

**Automatic upload to S3:**

```python
async def upload_to_s3(self, data: Dict, key: str):
    """
    Upload data to S3 bucket.

    Args:
        data: JSON-serializable data
        key: S3 object key (e.g., 'espn/box_scores/401584893.json')
    """
    if not self.config.s3_bucket:
        logging.warning("S3 bucket not configured, skipping upload")
        return

    if self.config.dry_run:
        logging.info(f"[DRY RUN] Would upload to s3://{self.config.s3_bucket}/{key}")
        return

    try:
        import boto3
        s3 = boto3.client('s3')

        s3.put_object(
            Bucket=self.config.s3_bucket,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType='application/json'
        )

        self.stats.data_items_stored += 1
        logging.debug(f"Uploaded to s3://{self.config.s3_bucket}/{key}")

    except Exception as e:
        logging.error(f"S3 upload failed for {key}: {e}")
        self.stats.errors += 1
```

---

## Scraper Implementations

### 1. ESPN Async Scraper

**File:** `scripts/etl/espn_async_scraper.py`

```python
class ESPNAsyncScraper(AsyncBaseScraper):
    """
    Async scraper for ESPN NBA data.

    Data types:
    - Schedule (11,633 files)
    - Box scores (44,828 files)
    - Play-by-play (44,826 files)
    - Team stats (44,828 files)
    """

    def __init__(self):
        config = ScraperConfig(
            base_url="https://www.espn.com/nba/",
            rate_limit=0.5,  # 2 req/sec (conservative)
            max_concurrent=10,
            retry_attempts=5,
            s3_bucket="nba-sim-raw-data-lake"
        )
        super().__init__(config)

    async def scrape_season(self, season: int):
        """Scrape entire season of games"""
        # Get game IDs from schedule
        game_ids = await self.fetch_schedule(season)

        # Fetch box scores concurrently
        tasks = [
            self.fetch_box_score(game_id)
            for game_id in game_ids
        ]

        async for result in self.process_tasks(tasks):
            if result:
                await self.upload_to_s3(
                    result,
                    f"espn/box_scores/{result['game_id']}.json"
                )
```

**Performance:**
- **Throughput:** 100-200 files/minute (rate limited)
- **Concurrency:** 10 concurrent requests
- **Rate:** 0.5 second intervals (2 req/sec)
- **Coverage:** 70,522 files, 55 GB

---

### 2. Basketball Reference Async Scraper

**File:** `scripts/etl/basketball_reference_async_scraper.py`

```python
class BasketballReferenceAsyncScraper(AsyncBaseScraper):
    """
    Async scraper for Basketball Reference.

    Data types:
    - 14 categories across 234 data types
    - 13-tier collection system
    """

    def __init__(self):
        config = ScraperConfig(
            base_url="https://www.basketball-reference.com/",
            rate_limit=1.0,  # 1 req/sec (strict rate limit)
            max_concurrent=5,
            retry_attempts=3,
            s3_bucket="nba-sim-raw-data-lake"
        )
        super().__init__(config)

    async def scrape_tier(self, tier: int):
        """Scrape specific tier of data types"""
        # Basketball Reference is stricter with rate limits
        # Use lower concurrency and longer delays
        pass
```

**Performance:**
- **Throughput:** 30-60 files/minute (strictly rate limited)
- **Concurrency:** 5 concurrent requests (conservative)
- **Rate:** 1.0 second intervals (1 req/sec)
- **Coverage:** 444 files, 99.9 MB

---

### 3. NBA API Async Scraper

**File:** `scripts/etl/nba_api_async_scraper.py`

```python
class NBAAPIAsyncScraper(AsyncBaseScraper):
    """
    Async scraper for NBA.com Stats API.

    Endpoints:
    - 60+ endpoints across 6 categories
    - Player tracking, team dashboards, game stats

    Status: PAUSED (aggressive rate limits)
    """

    def __init__(self):
        config = ScraperConfig(
            base_url="https://stats.nba.com/stats/",
            rate_limit=2.0,  # 0.5 req/sec (very conservative)
            max_concurrent=3,
            retry_attempts=5,
            timeout=60  # Longer timeout for API
        )
        super().__init__(config)
```

**Performance:**
- **Status:** Paused (infrastructure ready)
- **Concurrency:** 3 concurrent requests (very conservative)
- **Rate:** 2.0 second intervals (0.5 req/sec)
- **Endpoints:** 60+ available

---

### 4. hoopR Incremental Scraper

**File:** `scripts/etl/hoopr_incremental_scraper.py`

```python
class HoopRAsyncScraper(AsyncBaseScraper):
    """
    Async scraper for hoopR R package data.

    Data types:
    - Play-by-play (13.1M events)
    - Player box scores (785K records)
    - Team box scores (59,670 records)
    - Schedules (30,758 games)
    """

    def __init__(self):
        config = ScraperConfig(
            base_url="https://raw.githubusercontent.com/sportsdataverse/hoopR-data/",
            rate_limit=0.3,  # 3 req/sec (GitHub raw content is fast)
            max_concurrent=20,
            retry_attempts=3
        )
        super().__init__(config)
```

**Performance:**
- **Throughput:** 50-100 files/minute
- **Concurrency:** 20 concurrent requests
- **Rate:** 0.3 second intervals (3 req/sec)
- **Coverage:** 410 files, 8.2 GB

---

## Usage Examples

### Example 1: Basic Scraper

```python
from async_scraper_base import AsyncBaseScraper, ScraperConfig

class MyNBAScraper(AsyncBaseScraper):
    def __init__(self):
        config = ScraperConfig(
            base_url="https://api.example.com/",
            rate_limit=1.0,
            max_concurrent=10
        )
        super().__init__(config)

    async def scrape_data(self):
        urls = self.get_urls_to_scrape()

        async with self.get_session() as session:
            tasks = [self.fetch_with_retry(session, url) for url in urls]

            results = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result:
                    results.append(result)
                    await self.track_progress(len(results), len(urls))

        return results

# Run scraper
scraper = MyNBAScraper()
results = asyncio.run(scraper.scrape_data())
```

---

### Example 2: With S3 Upload

```python
async def scrape_and_upload(self):
    """Scrape data and upload to S3"""
    async with self.get_session() as session:
        for game_id in self.game_ids:
            data = await self.fetch_with_retry(session, f"/games/{game_id}")

            if data:
                # Upload to S3
                await self.upload_to_s3(
                    data,
                    f"games/{game_id}.json"
                )

                # Track progress
                await self.track_progress(
                    self.stats.data_items_stored,
                    len(self.game_ids)
                )
```

---

### Example 3: Error Handling

```python
async def scrape_with_error_handling(self):
    """Scrape with comprehensive error handling"""
    circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    try:
        async with self.get_session() as session:
            for url in self.urls:
                try:
                    # Use circuit breaker
                    result = await circuit_breaker.call(
                        self.fetch_with_retry,
                        session,
                        url
                    )

                    if result:
                        await self.process_result(result)

                except Exception as e:
                    logging.error(f"Failed to fetch {url}: {e}")
                    continue

    finally:
        await self.close_session()
        self.print_stats()

def print_stats(self):
    """Print final statistics"""
    print(f"Requests: {self.stats.requests_made}")
    print(f"Success rate: {self.stats.success_rate:.1%}")
    print(f"Throughput: {self.stats.requests_per_second:.1f} req/sec")
    print(f"Retries: {self.stats.retries_performed}")
    print(f"Errors: {self.stats.errors}")
```

---

## Performance Tuning

### Concurrency Optimization

```python
# Low concurrency (conservative, strict rate limits)
config = ScraperConfig(
    rate_limit=1.0,
    max_concurrent=5
)
# Use for: Basketball Reference, NBA API

# Medium concurrency (balanced)
config = ScraperConfig(
    rate_limit=0.5,
    max_concurrent=10
)
# Use for: ESPN

# High concurrency (fast sources)
config = ScraperConfig(
    rate_limit=0.3,
    max_concurrent=20
)
# Use for: GitHub raw content, hoopR
```

---

### Rate Limiting Strategies

**1. Adaptive Rate Limiting:**
```python
# Monitor 429 (rate limit) responses
if response.status == 429:
    # Slow down
    self.config.rate_limit *= 1.5
    logging.warning(f"Rate limit hit, slowing to {self.config.rate_limit}s")

# If no 429s for 100 requests, speed up
if self.stats.requests_successful % 100 == 0:
    self.config.rate_limit *= 0.9
```

**2. Respect Retry-After Header:**
```python
if response.status == 429:
    retry_after = response.headers.get('Retry-After', 60)
    await asyncio.sleep(int(retry_after))
```

---

### Memory Optimization

**Stream large responses:**
```python
async def fetch_large_file(self, session, url):
    """Stream large file to avoid memory issues"""
    async with session.get(url) as response:
        async with aiofiles.open('output.json', 'wb') as f:
            async for chunk in response.content.iter_chunked(8192):
                await f.write(chunk)
```

**Process results as they complete:**
```python
async def process_concurrent(self, urls):
    """Process results as they complete (don't wait for all)"""
    tasks = [self.fetch_with_retry(session, url) for url in urls]

    # as_completed yields results as they finish
    for coro in asyncio.as_completed(tasks):
        result = await coro
        # Process immediately
        await self.process_result(result)
```

---

## Best Practices

1. **Always use rate limiting** - Even if source doesn't enforce it, be respectful
2. **Log all errors** - Track failures for debugging and monitoring
3. **Track statistics** - Monitor success rate, throughput for optimization
4. **Close sessions properly** - Use `async with` or call `close_session()` in `finally`
5. **Use circuit breakers** - Prevent cascade failures when source is down
6. **Implement retries** - Transient failures are common, retry with backoff
7. **Test with dry_run** - Test logic without making actual requests
8. **Monitor 429 responses** - Adjust rate limits dynamically
9. **Chunk large operations** - Process 100-1000 items at a time
10. **Set reasonable timeouts** - 30-60 seconds for API calls

---

## Troubleshooting

### Common Issues

**1. Too Many Open Files**
```bash
# Increase file descriptor limit
ulimit -n 4096
```

**2. Rate Limited (429 Responses)**
```python
# Increase rate_limit (slower)
config.rate_limit = 2.0  # 0.5 req/sec

# Decrease concurrency
config.max_concurrent = 5
```

**3. Timeouts**
```python
# Increase timeout
config.timeout = 60

# Or implement custom timeout per request
async with asyncio.timeout(120):
    result = await fetch_with_retry(session, url)
```

**4. Memory Issues**
```python
# Process in smaller chunks
for chunk in chunked(urls, 1000):
    results = await scrape_urls(chunk)
    await process_results(results)
    # Clear memory
    del results
```

---

## Related Documentation

- **[Phase 0.9 Main README](../README.md)** - Data extraction overview
- **[DATA_SOURCE_ADAPTERS.md](DATA_SOURCE_ADAPTERS.md)** - Adapter pattern for cross-source normalization
- **[ORCHESTRATION.md](ORCHESTRATION.md)** - Task scheduling and orchestration
- **[ESPN_EXTRACTION.md](ESPN_EXTRACTION.md)** - ESPN-specific extraction details

---

**Last Updated:** October 23, 2025
**Maintained By:** NBA Simulator AWS Team
**Version:** 1.0

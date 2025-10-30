#!/usr/bin/env python3
"""
Async Base Scraper - Modern Web Scraping Infrastructure

Provides async base class for all NBA data scrapers with:
- Async HTTP requests using aiohttp
- Built-in rate limiting (token bucket algorithm)
- Retry logic with exponential backoff
- Progress tracking and telemetry
- Error handling and recovery

Based on Crawl4AI MCP server best practices.

Usage:
    class MyScraper(AsyncBaseScraper):
        async def scrape_data(self):
            async with self.get_session() as session:
                async for response in self.fetch_urls(urls):
                    data = await self.parse_response(response)
                    await self.store_data(data)

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import aiohttp
import aiofiles
import ssl
import time
import logging
import json
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from pathlib import Path
import sys
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class ScraperConfig:
    """Configuration for async scrapers"""

    base_url: str
    rate_limit: float = 1.0  # seconds between requests
    timeout: int = 30
    retry_attempts: int = 3
    max_concurrent: int = 10
    user_agent: str = "NBA-Simulator-Scraper/1.0"
    s3_bucket: Optional[str] = None
    output_dir: str = "/tmp/scraper_output"
    dry_run: bool = False


@dataclass
class ScraperStats:
    """Statistics tracking for scrapers"""

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
        if self.requests_made == 0:
            return 0.0
        return self.requests_successful / self.requests_made

    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time

    @property
    def requests_per_second(self) -> float:
        if self.elapsed_time == 0:
            return 0.0
        return self.requests_made / self.elapsed_time


class RateLimiter:
    """Token bucket rate limiter for async requests"""

    def __init__(self, rate_limit: float):
        self.rate_limit = rate_limit
        self.tokens = rate_limit
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary"""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            self.tokens = min(self.rate_limit, self.tokens + elapsed)
            self.last_update = now

            if self.tokens >= 1.0:
                self.tokens -= 1.0
            else:
                # Need to wait for more tokens
                wait_time = 1.0 - self.tokens
                await asyncio.sleep(wait_time)
                self.tokens = 0.0


class AsyncBaseScraper(ABC):
    """Base class for async NBA data scrapers"""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.stats = ScraperStats()
        self.rate_limiter = RateLimiter(1.0 / config.rate_limit.requests_per_second)
        self.s3_client = None

        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # Setup S3 if configured
        if config.storage.s3_bucket and HAS_BOTO3:
            self.s3_client = boto3.client("s3")

        # Create output directory
        self.output_dir = Path(config.storage.local_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Session for HTTP requests
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self) -> None:
        """Initialize the scraper"""
        # Create SSL context for ESPN API
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent, ssl=ssl_context
        )
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        self._session = aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers=headers
        )

        self.logger.info(f"Started {self.__class__.__name__} scraper")
        self.logger.info(
            f"Rate limit: {self.config.rate_limit.requests_per_second} req/sec"
        )
        self.logger.info(f"Max concurrent: {self.config.max_concurrent}")
        self.logger.info(f"Output directory: {self.output_dir}")

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get the current HTTP session"""
        if self._session is None:
            raise RuntimeError(
                "Scraper not started. Use async with scraper: or call await scraper.start()"
            )
        return self._session

    async def stop(self) -> None:
        """Cleanup the scraper"""
        if self._session:
            await self._session.close()

        # Log final statistics
        self.logger.info(f"Scraper completed:")
        self.logger.info(
            f"  Requests: {self.stats.requests_made} (success: {self.stats.requests_successful}, failed: {self.stats.requests_failed})"
        )
        self.logger.info(f"  Success rate: {self.stats.success_rate:.2%}")
        self.logger.info(
            f"  Data items: {self.stats.data_items_scraped} scraped, {self.stats.data_items_stored} stored"
        )
        self.logger.info(f"  Retries: {self.stats.retries_performed}")
        self.logger.info(f"  Errors: {self.stats.errors}")
        self.logger.info(f"  Elapsed time: {self.stats.elapsed_time:.2f}s")
        self.logger.info(f"  Requests/sec: {self.stats.requests_per_second:.2f}")

    async def get_session(self) -> aiohttp.ClientSession:
        """Get the HTTP session"""
        if not self._session:
            await self.start()
        return self._session

    async def fetch_url(
        self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Optional[aiohttp.ClientResponse]:
        """Fetch a single URL with rate limiting and retry logic"""
        if not self._session:
            await self.start()

        # Apply rate limiting
        await self.rate_limiter.acquire()

        # Merge headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        for attempt in range(self.config.retry.max_attempts):
            try:
                self.stats.requests_made += 1

                async with self._session.get(
                    url, params=params, headers=request_headers
                ) as response:
                    if response.status == 200:
                        self.stats.requests_successful += 1
                        return response
                    elif response.status == 429:
                        # Rate limited - wait longer
                        wait_time = 60 * (2**attempt)  # Exponential backoff
                        self.logger.warning(f"Rate limited (429), waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        self.stats.retries_performed += 1
                        continue
                    elif response.status >= 500:
                        # Server error - retry
                        wait_time = 2**attempt
                        self.logger.warning(
                            f"Server error {response.status}, retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        self.stats.retries_performed += 1
                        continue
                    else:
                        # Client error - don't retry
                        self.logger.error(f"Client error {response.status} for {url}")
                        self.stats.requests_failed += 1
                        self.stats.errors += 1
                        return None

            except asyncio.TimeoutError:
                wait_time = 2**attempt
                self.logger.warning(f"Timeout for {url}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
                self.stats.retries_performed += 1
                continue
            except Exception as e:
                wait_time = 2**attempt
                self.logger.error(
                    f"Error fetching {url}: {e}, retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)
                self.stats.retries_performed += 1
                continue

        # All retries failed
        self.logger.error(
            f"Failed to fetch {url} after {self.config.retry.max_attempts} attempts"
        )
        self.stats.requests_failed += 1
        self.stats.errors += 1
        return None

    async def fetch_urls(
        self, urls: List[str], params_list: Optional[List[Dict]] = None
    ) -> AsyncGenerator[aiohttp.ClientResponse, None]:
        """Fetch multiple URLs concurrently"""
        if not urls:
            return

        if params_list and len(params_list) != len(urls):
            raise ValueError("params_list length must match urls length")

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config.max_concurrent)

        async def fetch_with_semaphore(url: str, params: Optional[Dict] = None):
            async with semaphore:
                return await self.fetch_url(url, params)

        # Create tasks
        tasks = []
        for i, url in enumerate(urls):
            params = params_list[i] if params_list else None
            task = fetch_with_semaphore(url, params)
            tasks.append(task)

        # Process results as they complete
        for task in asyncio.as_completed(tasks):
            response = await task
            if response:
                yield response

    async def parse_json_response(
        self, response: aiohttp.ClientResponse
    ) -> Optional[Dict]:
        """Parse JSON response"""
        try:
            data = await response.json()
            self.stats.data_items_scraped += 1
            return data
        except Exception as e:
            self.logger.error(f"Error parsing JSON: {e}")
            self.stats.errors += 1
            return None

    async def parse_text_response(
        self, response: aiohttp.ClientResponse
    ) -> Optional[str]:
        """Parse text response"""
        try:
            text = await response.text()
            self.stats.data_items_scraped += 1
            return text
        except Exception as e:
            self.logger.error(f"Error parsing text: {e}")
            self.stats.errors += 1
            return None

    async def store_data(self, data: Any, filename: str, subdir: str = "") -> bool:
        """Store data to local file and optionally S3"""
        if self.config.dry_run:
            self.logger.info(f"DRY RUN: Would store {filename} in {subdir}")
            self.stats.data_items_stored += 1
            return True

        try:
            # Create subdirectory if specified
            store_dir = self.output_dir / subdir if subdir else self.output_dir
            store_dir.mkdir(parents=True, exist_ok=True)

            file_path = store_dir / filename

            # Write to local file
            if isinstance(data, (dict, list)):
                async with aiofiles.open(file_path, "w") as f:
                    await f.write(json.dumps(data, indent=2))
            else:
                async with aiofiles.open(file_path, "w") as f:
                    await f.write(str(data))

            # Upload to S3 if configured
            if self.s3_client and self.config.s3_bucket:
                s3_key = f"{subdir}/{filename}" if subdir else filename
                await self._upload_to_s3(file_path, s3_key)

            self.stats.data_items_stored += 1
            self.logger.debug(f"Stored {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error storing {filename}: {e}")
            self.stats.errors += 1
            return False

    async def _upload_to_s3(self, file_path: Path, s3_key: str) -> None:
        """Upload file to S3"""
        try:
            # Run S3 upload in thread pool since boto3 is synchronous
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.s3_client.upload_file,
                str(file_path),
                self.config.s3_bucket,
                s3_key,
            )
            self.logger.debug(f"Uploaded {s3_key} to S3")
        except Exception as e:
            self.logger.error(f"Error uploading {s3_key} to S3: {e}")
            self.stats.errors += 1

    def generate_content_hash(self, data: Any) -> str:
        """Generate SHA256 hash of content for deduplication"""
        if isinstance(data, (dict, list)):
            content = json.dumps(data, sort_keys=True)
        else:
            content = str(data)

        return hashlib.sha256(content.encode()).hexdigest()

    @abstractmethod
    async def scrape(self) -> None:
        """Main scraping method - must be implemented by subclasses"""
        pass


class ScraperFactory:
    """Factory for creating scrapers with configuration"""

    @staticmethod
    def create_config_from_yaml(config_path: str) -> Dict[str, ScraperConfig]:
        """Load scraper configurations from YAML file"""
        if not HAS_YAML:
            raise ImportError("PyYAML not installed")

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        configs = {}
        for scraper_name, config_dict in config_data.get("scrapers", {}).items():
            configs[scraper_name] = ScraperConfig(**config_dict)

        return configs

    @staticmethod
    def create_config_from_env() -> ScraperConfig:
        """Create configuration from environment variables"""
        import os

        return ScraperConfig(
            base_url=os.getenv("SCRAPER_BASE_URL", ""),
            rate_limit=float(os.getenv("SCRAPER_RATE_LIMIT", "1.0")),
            timeout=int(os.getenv("SCRAPER_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("SCRAPER_RETRY_ATTEMPTS", "3")),
            max_concurrent=int(os.getenv("SCRAPER_MAX_CONCURRENT", "10")),
            user_agent=os.getenv("SCRAPER_USER_AGENT", "NBA-Simulator-Scraper/1.0"),
            s3_bucket=os.getenv("SCRAPER_S3_BUCKET"),
            output_dir=os.getenv("SCRAPER_OUTPUT_DIR", "/tmp/scraper_output"),
            dry_run=os.getenv("SCRAPER_DRY_RUN", "false").lower() == "true",
        )


# Example usage
if __name__ == "__main__":

    class ExampleScraper(AsyncBaseScraper):
        async def scrape(self):
            urls = [
                "https://httpbin.org/json",
                "https://httpbin.org/json",
                "https://httpbin.org/json",
            ]

            async for response in self.fetch_urls(urls):
                data = await self.parse_json_response(response)
                if data:
                    filename = f"data_{int(time.time())}.json"
                    await self.store_data(data, filename)

    # Example usage
    config = ScraperConfig(
        base_url="https://httpbin.org",
        rate_limit=0.5,  # 2 requests per second
        max_concurrent=3,
    )

    async def main():
        async with ExampleScraper(config) as scraper:
            await scraper.scrape()

    asyncio.run(main())

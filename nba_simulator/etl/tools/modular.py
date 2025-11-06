#!/usr/bin/env python3
"""
Modular Tool Components - Reusable Scraper Components

Provides modular, reusable components for NBA data scrapers with:
- Fetch component for HTTP requests
- Parse component for content processing
- Store component for data persistence
- Checkpoint component for progress tracking
- Tool composition patterns

Based on Crawl4AI MCP server modular architecture patterns.

Usage:
    from nba_simulator.etl.tools import FetchTool, ParseTool, StoreTool, CheckpointTool

    # Compose tools
    fetch_tool = FetchTool(config)
    parse_tool = ParseTool(config)
    store_tool = StoreTool(config)
    checkpoint_tool = CheckpointTool(config)

    # Use in scraper
    async with fetch_tool:
        response = await fetch_tool.fetch_url(url)
        data = await parse_tool.parse_response(response)
        await store_tool.store_data(data, filename)
        await checkpoint_tool.save_progress(game_id)

Version: 2.0 (Migrated to nba_simulator package)
Created: October 13, 2025
Migrated: November 6, 2025
"""

import asyncio
import aiohttp
import aiofiles
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from datetime import datetime, timezone

# Import from new package structure
from nba_simulator.etl.base import ScraperConfig, RateLimiter, ScraperErrorHandler
from nba_simulator.etl.monitoring import ScraperTelemetry

# NOTE: intelligent_extraction not yet migrated, conditional import
try:
    from nba_simulator.etl.extractors.intelligent import (
        ExtractionManager,
        ESPNExtractionStrategy,
        BasketballReferenceExtractionStrategy,
    )
except ImportError:
    # Fallback to legacy import during migration
    try:
        from scripts.etl.intelligent_extraction import (
            ExtractionManager,
            ESPNExtractionStrategy,
            BasketballReferenceExtractionStrategy,
        )
    except ImportError:
        # Create stub if not available
        ExtractionManager = None
        ESPNExtractionStrategy = None
        BasketballReferenceExtractionStrategy = None


@dataclass
class ToolConfig:
    """Configuration for modular tools"""

    name: str
    config: ScraperConfig
    error_handler: ScraperErrorHandler
    telemetry: ScraperTelemetry
    extraction_manager: Optional[Any] = (
        None  # ExtractionManager type hint when available
    )


class BaseTool(ABC):
    """Base class for modular tools"""

    def __init__(self, tool_config: ToolConfig):
        self.config = tool_config.config
        self.error_handler = tool_config.error_handler
        self.telemetry = tool_config.telemetry
        self.logger = logging.getLogger(f"tool.{tool_config.name}")
        self.stats = {
            "operations": 0,
            "successes": 0,
            "failures": 0,
            "start_time": time.time(),
        }

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the tool operation"""
        pass

    def _record_operation(self, success: bool) -> None:
        """Record operation statistics"""
        self.stats["operations"] += 1
        if success:
            self.stats["successes"] += 1
        else:
            self.stats["failures"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get tool statistics"""
        elapsed = time.time() - self.stats["start_time"]
        return {
            **self.stats,
            "elapsed_time": elapsed,
            "success_rate": self.stats["successes"] / max(1, self.stats["operations"]),
            "operations_per_second": self.stats["operations"] / max(1, elapsed),
        }


class FetchTool(BaseTool):
    """Modular HTTP fetching tool"""

    def __init__(self, tool_config: ToolConfig):
        super().__init__(tool_config)
        self.rate_limiter = RateLimiter(1.0 / self.config.rate_limit)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()

    async def start(self) -> None:
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=self.config.max_concurrent)
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

        self.logger.info(f"Started {self.__class__.__name__}")

    async def stop(self) -> None:
        """Cleanup HTTP session"""
        if self._session:
            await self._session.close()

        self.logger.info(f"Stopped {self.__class__.__name__}")
        self.logger.info(f"Stats: {self.get_stats()}")

    async def execute(
        self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Optional[aiohttp.ClientResponse]:
        """Execute HTTP fetch operation"""
        return await self.fetch_url(url, params, headers)

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
                async with self._session.get(
                    url, params=params, headers=request_headers
                ) as response:
                    if response.status == 200:
                        self._record_operation(True)
                        return response
                    elif response.status == 429:
                        # Rate limited - wait longer
                        wait_time = 60 * (2**attempt)
                        self.logger.warning(f"Rate limited (429), waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status >= 500:
                        # Server error - retry
                        wait_time = 2**attempt
                        self.logger.warning(
                            f"Server error {response.status}, retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Client error - don't retry
                        self.logger.error(f"Client error {response.status} for {url}")
                        self._record_operation(False)
                        return None

            except asyncio.TimeoutError:
                wait_time = 2**attempt
                self.logger.warning(f"Timeout for {url}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
                continue
            except Exception as e:
                wait_time = 2**attempt
                self.logger.error(
                    f"Error fetching {url}: {e}, retrying in {wait_time}s"
                )
                await asyncio.sleep(wait_time)
                continue

        # All retries failed
        self.logger.error(
            f"Failed to fetch {url} after {self.config.retry.max_attempts} attempts"
        )
        self._record_operation(False)
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


class ParseTool(BaseTool):
    """Modular content parsing tool"""

    def __init__(self, tool_config: ToolConfig):
        super().__init__(tool_config)
        self.extraction_manager = tool_config.extraction_manager
        if self.extraction_manager is None and ExtractionManager is not None:
            self.extraction_manager = ExtractionManager()
            self._setup_extraction_strategies()

    def _setup_extraction_strategies(self) -> None:
        """Setup extraction strategies"""
        if ExtractionManager is None:
            self.logger.warning(
                "ExtractionManager not available, skipping strategy setup"
            )
            return

        self.extraction_manager.add_strategy("espn", ESPNExtractionStrategy())
        self.extraction_manager.add_strategy(
            "basketball_reference", BasketballReferenceExtractionStrategy()
        )

    async def execute(
        self,
        response: aiohttp.ClientResponse,
        content_type: str = "json",
        extraction_strategy: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute content parsing operation"""
        return await self.parse_response(response, content_type, extraction_strategy)

    async def parse_response(
        self,
        response: aiohttp.ClientResponse,
        content_type: str = "json",
        extraction_strategy: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Parse HTTP response content"""
        try:
            if content_type == "json":
                content = await response.text()
                if self.extraction_manager:
                    result = await self.extraction_manager.extract_with_fallback(
                        content, "json", extraction_strategy
                    )
                else:
                    # Fallback to simple JSON parsing
                    return await self.parse_json(content)
            elif content_type == "html":
                content = await response.text()
                if self.extraction_manager:
                    result = await self.extraction_manager.extract_with_fallback(
                        content, "html", extraction_strategy
                    )
                else:
                    # Fallback to text parsing
                    return await self.parse_text(content)
            else:
                self.logger.error(f"Unsupported content type: {content_type}")
                self._record_operation(False)
                return None

            if hasattr(result, "success") and result.success:
                self._record_operation(True)
                return result.data
            else:
                if hasattr(result, "errors"):
                    self.logger.error(f"Parsing failed: {result.errors}")
                self._record_operation(False)
                return None

        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            self._record_operation(False)
            return None

    async def parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON content directly"""
        try:
            data = json.loads(content)
            self._record_operation(True)
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            self._record_operation(False)
            return None

    async def parse_text(self, content: str) -> Optional[str]:
        """Parse text content"""
        try:
            self._record_operation(True)
            return content
        except Exception as e:
            self.logger.error(f"Text parsing error: {e}")
            self._record_operation(False)
            return None


class StoreTool(BaseTool):
    """Modular data storage tool"""

    def __init__(self, tool_config: ToolConfig):
        super().__init__(tool_config)
        self.s3_client = None

        # Setup S3 if configured
        if self.config.storage.s3_bucket:
            try:
                import boto3

                self.s3_client = boto3.client("s3")
            except ImportError:
                self.logger.warning("boto3 not available, S3 upload disabled")

        # Create output directory
        self.output_dir = Path(self.config.storage.local_output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, data: Any, filename: str, subdir: str = "") -> bool:
        """Execute data storage operation"""
        return await self.store_data(data, filename, subdir)

    async def store_data(self, data: Any, filename: str, subdir: str = "") -> bool:
        """Store data to local file and optionally S3"""
        if self.config.dry_run:
            self.logger.info(f"DRY RUN: Would store {filename} in {subdir}")
            self._record_operation(True)
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
            if self.s3_client and self.config.storage.s3_bucket:
                s3_key = f"{subdir}/{filename}" if subdir else filename
                await self._upload_to_s3(file_path, s3_key)

            self._record_operation(True)
            self.logger.debug(f"Stored {filename}")
            return True

        except Exception as e:
            self.logger.error(f"Error storing {filename}: {e}")
            self._record_operation(False)
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
                self.config.storage.s3_bucket,
                s3_key,
            )
            self.logger.debug(f"Uploaded {s3_key} to S3")
        except Exception as e:
            self.logger.error(f"Error uploading {s3_key} to S3: {e}")

    async def store_batch(
        self,
        data_items: List[Dict[str, Any]],
        filename_template: str = "data_{index}.json",
        subdir: str = "",
    ) -> int:
        """Store multiple data items"""
        stored_count = 0

        for i, data in enumerate(data_items):
            filename = filename_template.format(index=i)
            success = await self.store_data(data, filename, subdir)
            if success:
                stored_count += 1

        return stored_count


class CheckpointTool(BaseTool):
    """Modular progress checkpoint tool"""

    def __init__(self, tool_config: ToolConfig):
        super().__init__(tool_config)
        self.checkpoint_file = (
            Path(self.config.storage.local_output_dir) / "checkpoints.json"
        )
        self.checkpoints: Dict[str, Any] = {}
        self._load_checkpoints()

    def _load_checkpoints(self) -> None:
        """Load existing checkpoints"""
        try:
            if self.checkpoint_file.exists():
                with open(self.checkpoint_file, "r") as f:
                    self.checkpoints = json.load(f)
                self.logger.info(f"Loaded {len(self.checkpoints)} checkpoints")
        except Exception as e:
            self.logger.error(f"Error loading checkpoints: {e}")
            self.checkpoints = {}

    async def execute(self, key: str, data: Any) -> bool:
        """Execute checkpoint save operation"""
        return await self.save_checkpoint(key, data)

    async def save_checkpoint(self, key: str, data: Any) -> bool:
        """Save checkpoint data"""
        try:
            self.checkpoints[key] = {
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool": self.__class__.__name__,
            }

            # Save to file
            async with aiofiles.open(self.checkpoint_file, "w") as f:
                await f.write(json.dumps(self.checkpoints, indent=2))

            self._record_operation(True)
            self.logger.debug(f"Saved checkpoint: {key}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving checkpoint {key}: {e}")
            self._record_operation(False)
            return False

    async def load_checkpoint(self, key: str) -> Optional[Any]:
        """Load checkpoint data"""
        try:
            if key in self.checkpoints:
                self._record_operation(True)
                return self.checkpoints[key]["data"]
            else:
                self.logger.debug(f"Checkpoint not found: {key}")
                return None
        except Exception as e:
            self.logger.error(f"Error loading checkpoint {key}: {e}")
            self._record_operation(False)
            return None

    async def has_checkpoint(self, key: str) -> bool:
        """Check if checkpoint exists"""
        return key in self.checkpoints

    async def remove_checkpoint(self, key: str) -> bool:
        """Remove checkpoint"""
        try:
            if key in self.checkpoints:
                del self.checkpoints[key]

                # Save updated checkpoints
                async with aiofiles.open(self.checkpoint_file, "w") as f:
                    await f.write(json.dumps(self.checkpoints, indent=2))

                self._record_operation(True)
                self.logger.debug(f"Removed checkpoint: {key}")
                return True
            else:
                self.logger.debug(f"Checkpoint not found for removal: {key}")
                return False

        except Exception as e:
            self.logger.error(f"Error removing checkpoint {key}: {e}")
            self._record_operation(False)
            return False

    def get_all_checkpoints(self) -> Dict[str, Any]:
        """Get all checkpoints"""
        return self.checkpoints.copy()


class ToolComposer:
    """Composes multiple tools for complex operations"""

    def __init__(
        self,
        config: ScraperConfig,
        error_handler: ScraperErrorHandler,
        telemetry: ScraperTelemetry,
    ):
        self.config = config
        self.error_handler = error_handler
        self.telemetry = telemetry

        # Create tool configurations
        tool_config = ToolConfig(
            name="composer",
            config=config,
            error_handler=error_handler,
            telemetry=telemetry,
        )

        # Initialize tools
        self.fetch_tool = FetchTool(tool_config)
        self.parse_tool = ParseTool(tool_config)
        self.store_tool = StoreTool(tool_config)
        self.checkpoint_tool = CheckpointTool(tool_config)

    async def fetch_and_store(
        self, url: str, filename: str, content_type: str = "json", subdir: str = ""
    ) -> bool:
        """Fetch URL and store parsed data"""
        try:
            async with self.fetch_tool:
                # Fetch data
                response = await self.fetch_tool.fetch_url(url)
                if not response:
                    return False

                # Parse data
                data = await self.parse_tool.parse_response(response, content_type)
                if not data:
                    return False

                # Store data
                success = await self.store_tool.store_data(data, filename, subdir)
                return success

        except Exception as e:
            self.telemetry.logger.error(f"Fetch and store failed: {e}")
            return False

    async def batch_fetch_and_store(
        self,
        urls: List[str],
        filename_template: str = "data_{index}.json",
        content_type: str = "json",
        subdir: str = "",
    ) -> int:
        """Fetch multiple URLs and store parsed data"""
        stored_count = 0

        async with self.fetch_tool:
            async for response in self.fetch_tool.fetch_urls(urls):
                if response:
                    # Parse data
                    data = await self.parse_tool.parse_response(response, content_type)
                    if data:
                        # Store data
                        filename = filename_template.format(index=stored_count)
                        success = await self.store_tool.store_data(
                            data, filename, subdir
                        )
                        if success:
                            stored_count += 1

        return stored_count

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics from all tools"""
        return {
            "fetch_tool": self.fetch_tool.get_stats(),
            "parse_tool": self.parse_tool.get_stats(),
            "store_tool": self.store_tool.get_stats(),
            "checkpoint_tool": self.checkpoint_tool.get_stats(),
        }


# Example usage
if __name__ == "__main__":

    async def example_usage():
        from nba_simulator.etl.config import ScraperConfigManager

        # Create configuration
        config = ScraperConfig(
            name="example",
            base_url="https://httpbin.org",
            rate_limit=1.0,
            timeout=10,
            max_concurrent=3,
            dry_run=True,
        )

        # Create tools
        error_handler = ScraperErrorHandler()
        telemetry = ScraperTelemetry("example_composer")

        composer = ToolComposer(config, error_handler, telemetry)

        # Example: fetch and store single URL
        success = await composer.fetch_and_store(
            "https://httpbin.org/json", "example.json", "json"
        )

        print(f"Single fetch success: {success}")

        # Example: batch fetch and store
        urls = [
            "https://httpbin.org/json",
            "https://httpbin.org/json",
            "https://httpbin.org/json",
        ]

        stored_count = await composer.batch_fetch_and_store(
            urls, "batch_data_{index}.json"
        )

        print(f"Batch stored: {stored_count} files")

        # Print statistics
        stats = composer.get_all_stats()
        print("Tool statistics:")
        for tool_name, tool_stats in stats.items():
            print(f"  {tool_name}: {tool_stats['success_rate']:.2%} success rate")

    asyncio.run(example_usage())

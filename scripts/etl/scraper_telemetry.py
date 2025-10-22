#!/usr/bin/env python3
"""
Scraper Telemetry System - Monitoring and Metrics

Provides comprehensive telemetry for NBA data scrapers with:
- Structured logging with context
- Performance metrics collection
- Real-time monitoring dashboard
- Alert thresholds and notifications
- Data quality metrics

Based on Crawl4AI MCP server telemetry patterns.

Usage:
    from scraper_telemetry import ScraperTelemetry, MetricsCollector

    telemetry = ScraperTelemetry("espn_scraper")
    metrics = MetricsCollector()

    # Track operations
    async with telemetry.track_operation("fetch_schedule"):
        # Scraping operation
        pass

    # Record metrics
    metrics.record_request_success()
    metrics.record_data_quality_score(0.95)

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False


class LogLevel(Enum):
    """Log levels for telemetry"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(Enum):
    """Types of metrics"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class TelemetryEvent:
    """Telemetry event data"""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scraper_name: str = ""
    operation: str = ""
    level: LogLevel = LogLevel.INFO
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["level"] = self.level.value
        return data


@dataclass
class PerformanceMetrics:
    """Performance metrics for scrapers"""

    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    requests_per_second: float = 0.0
    average_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    data_items_scraped: int = 0
    data_items_stored: int = 0
    storage_success_rate: float = 0.0
    errors_total: int = 0
    retries_total: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        if self.requests_total == 0:
            return 0.0
        return self.requests_successful / self.requests_total

    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time

    @property
    def throughput_items_per_second(self) -> float:
        if self.elapsed_time == 0:
            return 0.0
        return self.data_items_scraped / self.elapsed_time


@dataclass
class DataQualityMetrics:
    """Data quality metrics"""

    total_items_validated: int = 0
    items_passed_validation: int = 0
    items_failed_validation: int = 0
    schema_validation_errors: int = 0
    completeness_errors: int = 0
    consistency_errors: int = 0
    duplicate_items: int = 0

    @property
    def validation_pass_rate(self) -> float:
        if self.total_items_validated == 0:
            return 0.0
        return self.items_passed_validation / self.total_items_validated

    @property
    def duplicate_rate(self) -> float:
        if self.total_items_validated == 0:
            return 0.0
        return self.duplicate_items / self.total_items_validated


class MetricsCollector:
    """Collects and aggregates metrics from scrapers"""

    def __init__(self):
        self.performance = PerformanceMetrics()
        self.data_quality = DataQualityMetrics()
        self.response_times: List[float] = []
        self.custom_metrics: Dict[str, Any] = {}

        # Prometheus metrics (if available)
        if HAS_PROMETHEUS:
            self.prometheus_metrics = self._init_prometheus_metrics()
        else:
            self.prometheus_metrics = None

    def _init_prometheus_metrics(self) -> Dict[str, Any]:
        """Initialize Prometheus metrics"""
        return {
            "requests_total": Counter(
                "scraper_requests_total", "Total requests", ["scraper", "status"]
            ),
            "request_duration": Histogram(
                "scraper_request_duration_seconds", "Request duration", ["scraper"]
            ),
            "data_items": Counter(
                "scraper_data_items_total", "Data items processed", ["scraper", "type"]
            ),
            "errors_total": Counter(
                "scraper_errors_total", "Total errors", ["scraper", "error_type"]
            ),
            "success_rate": Gauge("scraper_success_rate", "Success rate", ["scraper"]),
            "throughput": Gauge(
                "scraper_throughput_items_per_second", "Throughput", ["scraper"]
            ),
        }

    def record_request(
        self, success: bool, duration_ms: float, scraper_name: str = "unknown"
    ) -> None:
        """Record a request"""
        self.performance.requests_total += 1
        if success:
            self.performance.requests_successful += 1
        else:
            self.performance.requests_failed += 1

        self.response_times.append(duration_ms)

        # Update average response time
        self.performance.average_response_time_ms = sum(self.response_times) / len(
            self.response_times
        )

        # Update percentiles
        if len(self.response_times) >= 10:
            sorted_times = sorted(self.response_times)
            n = len(sorted_times)
            self.performance.p95_response_time_ms = sorted_times[int(0.95 * n)]
            self.performance.p99_response_time_ms = sorted_times[int(0.99 * n)]

        # Update requests per second
        self.performance.requests_per_second = (
            self.performance.requests_total / self.performance.elapsed_time
        )

        # Prometheus metrics
        if self.prometheus_metrics:
            status = "success" if success else "failure"
            self.prometheus_metrics["requests_total"].labels(
                scraper=scraper_name, status=status
            ).inc()
            self.prometheus_metrics["request_duration"].labels(
                scraper=scraper_name
            ).observe(duration_ms / 1000.0)
            self.prometheus_metrics["success_rate"].labels(scraper=scraper_name).set(
                self.performance.success_rate
            )
            self.prometheus_metrics["throughput"].labels(scraper=scraper_name).set(
                self.performance.throughput_items_per_second
            )

    def record_data_item(self, item_type: str, scraper_name: str = "unknown") -> None:
        """Record a data item processed"""
        self.performance.data_items_scraped += 1

        if self.prometheus_metrics:
            self.prometheus_metrics["data_items"].labels(
                scraper=scraper_name, type=item_type
            ).inc()

    def record_data_stored(self, success: bool) -> None:
        """Record data storage attempt"""
        if success:
            self.performance.data_items_stored += 1

        # Update storage success rate
        total_storage_attempts = self.performance.data_items_scraped
        if total_storage_attempts > 0:
            self.performance.storage_success_rate = (
                self.performance.data_items_stored / total_storage_attempts
            )

    def record_error(self, error_type: str, scraper_name: str = "unknown") -> None:
        """Record an error"""
        self.performance.errors_total += 1

        if self.prometheus_metrics:
            self.prometheus_metrics["errors_total"].labels(
                scraper=scraper_name, error_type=error_type
            ).inc()

    def record_retry(self) -> None:
        """Record a retry attempt"""
        self.performance.retries_total += 1

    def record_validation(self, passed: bool, error_type: Optional[str] = None) -> None:
        """Record data validation result"""
        self.data_quality.total_items_validated += 1

        if passed:
            self.data_quality.items_passed_validation += 1
        else:
            self.data_quality.items_failed_validation += 1

            if error_type:
                if error_type == "schema":
                    self.data_quality.schema_validation_errors += 1
                elif error_type == "completeness":
                    self.data_quality.completeness_errors += 1
                elif error_type == "consistency":
                    self.data_quality.consistency_errors += 1

    def record_duplicate(self) -> None:
        """Record a duplicate item"""
        self.data_quality.duplicate_items += 1

    def set_custom_metric(self, name: str, value: Any) -> None:
        """Set a custom metric"""
        self.custom_metrics[name] = value

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        return {
            "performance": asdict(self.performance),
            "data_quality": asdict(self.data_quality),
            "custom_metrics": self.custom_metrics.copy(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class ScraperTelemetry:
    """Main telemetry system for scrapers"""

    def __init__(
        self,
        scraper_name: str,
        log_file: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        enable_prometheus: bool = False,
    ):
        self.scraper_name = scraper_name
        self.log_file = log_file
        self.s3_bucket = s3_bucket
        self.s3_client = None

        # Setup logging
        self.logger = logging.getLogger(f"telemetry.{scraper_name}")
        self.logger.setLevel(logging.INFO)

        # Setup file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(file_handler)

        # Setup S3 if configured
        if s3_bucket and HAS_BOTO3:
            self.s3_client = boto3.client("s3")

        # Metrics collector
        self.metrics = MetricsCollector()

        # Prometheus server (if enabled)
        if enable_prometheus and HAS_PROMETHEUS:
            self.prometheus_port = 8000
            start_http_server(self.prometheus_port)
            self.logger.info(
                f"Prometheus metrics server started on port {self.prometheus_port}"
            )

        # Event storage
        self.events: List[TelemetryEvent] = []
        self.max_events = 10000  # Keep last 10k events in memory

    def log_event(
        self,
        operation: str,
        message: str,
        level: LogLevel = LogLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> None:
        """Log a telemetry event"""
        event = TelemetryEvent(
            scraper_name=self.scraper_name,
            operation=operation,
            level=level,
            message=message,
            data=data or {},
            success=success,
            error=error,
            duration_ms=duration_ms,
        )

        # Add to events list
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        # Log to logger
        log_level = getattr(logging, level.value)
        self.logger.log(log_level, f"[{operation}] {message}", extra=event.data)

        # Upload to S3 if configured
        if self.s3_client and self.s3_bucket:
            asyncio.create_task(self._upload_event_to_s3(event))

    async def _upload_event_to_s3(self, event: TelemetryEvent) -> None:
        """Upload event to S3"""
        try:
            key = f"telemetry/{self.scraper_name}/{event.timestamp.strftime('%Y/%m/%d')}/{event.event_id}.json"

            # Run S3 upload in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.s3_client.put_object,
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(event.to_dict()),
                ContentType="application/json",
            )
        except Exception as e:
            self.logger.error(f"Failed to upload event to S3: {e}")

    @asynccontextmanager
    async def track_operation(self, operation: str, **kwargs):
        """Context manager to track operation timing and success"""
        start_time = time.time()
        success = None
        error = None

        try:
            self.log_event(operation, f"Starting {operation}", LogLevel.INFO, kwargs)
            yield
            success = True
            self.log_event(
                operation,
                f"Completed {operation}",
                LogLevel.INFO,
                success=success,
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            success = False
            error = str(e)
            self.log_event(
                operation,
                f"Failed {operation}: {error}",
                LogLevel.ERROR,
                success=success,
                error=error,
                duration_ms=(time.time() - start_time) * 1000,
            )
            raise
        finally:
            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_request(success, duration_ms, self.scraper_name)

    def record_data_quality_score(self, score: float) -> None:
        """Record data quality score"""
        self.metrics.set_custom_metric("data_quality_score", score)
        self.log_event(
            "data_quality",
            f"Quality score: {score:.3f}",
            LogLevel.INFO,
            {"quality_score": score},
        )

    def record_rate_limit_hit(self, retry_after: int) -> None:
        """Record rate limit hit"""
        self.metrics.record_error("rate_limit", self.scraper_name)
        self.log_event(
            "rate_limit",
            f"Rate limited, retry after {retry_after}s",
            LogLevel.WARNING,
            {"retry_after": retry_after},
        )

    def record_circuit_breaker_open(self, endpoint: str) -> None:
        """Record circuit breaker opening"""
        self.metrics.record_error("circuit_breaker_open", self.scraper_name)
        self.log_event(
            "circuit_breaker",
            f"Circuit breaker opened for {endpoint}",
            LogLevel.ERROR,
            {"endpoint": endpoint},
        )

    def get_health_status(self) -> Dict[str, Any]:
        """Get scraper health status"""
        performance = self.metrics.performance
        quality = self.metrics.data_quality

        # Determine health status
        if performance.success_rate < 0.8:
            status = "unhealthy"
        elif performance.success_rate < 0.95:
            status = "degraded"
        elif quality.validation_pass_rate < 0.9:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "scraper_name": self.scraper_name,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "performance": {
                "success_rate": performance.success_rate,
                "requests_per_second": performance.requests_per_second,
                "average_response_time_ms": performance.average_response_time_ms,
                "throughput_items_per_second": performance.throughput_items_per_second,
            },
            "data_quality": {
                "validation_pass_rate": quality.validation_pass_rate,
                "duplicate_rate": quality.duplicate_rate,
            },
            "errors": {
                "total_errors": performance.errors_total,
                "retries_total": performance.retries_total,
            },
        }

    def export_metrics(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Export all metrics to file or return as dict"""
        metrics_data = {
            "scraper_name": self.scraper_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": self.metrics.get_summary(),
            "events": [
                event.to_dict() for event in self.events[-100:]
            ],  # Last 100 events
            "health": self.get_health_status(),
        }

        if file_path:
            with open(file_path, "w") as f:
                json.dump(metrics_data, f, indent=2)

        return metrics_data


class TelemetryManager:
    """Manages telemetry for multiple scrapers"""

    def __init__(self, s3_bucket: Optional[str] = None):
        self.scrapers: Dict[str, ScraperTelemetry] = {}
        self.s3_bucket = s3_bucket
        self.s3_client = None

        if s3_bucket and HAS_BOTO3:
            self.s3_client = boto3.client("s3")

    def get_scraper_telemetry(self, scraper_name: str) -> ScraperTelemetry:
        """Get or create telemetry for a scraper"""
        if scraper_name not in self.scrapers:
            log_file = f"/tmp/telemetry_{scraper_name}.log"
            self.scrapers[scraper_name] = ScraperTelemetry(
                scraper_name, log_file, self.s3_bucket
            )
        return self.scrapers[scraper_name]

    def get_all_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all scrapers"""
        return {
            name: telemetry.get_health_status()
            for name, telemetry in self.scrapers.items()
        }

    def export_all_metrics(self, output_dir: str = "/tmp/telemetry_export") -> None:
        """Export metrics for all scrapers"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for name, telemetry in self.scrapers.items():
            file_path = output_path / f"{name}_metrics.json"
            telemetry.export_metrics(str(file_path))


# Example usage
if __name__ == "__main__":

    async def example_usage():
        # Create telemetry manager
        manager = TelemetryManager()

        # Get telemetry for a scraper
        telemetry = manager.get_scraper_telemetry("example_scraper")

        # Track an operation
        async with telemetry.track_operation("fetch_data"):
            await asyncio.sleep(0.1)  # Simulate work
            telemetry.metrics.record_data_item("player_stats")
            telemetry.metrics.record_data_stored(True)

        # Record some metrics
        telemetry.record_data_quality_score(0.95)
        telemetry.record_rate_limit_hit(60)

        # Get health status
        health = telemetry.get_health_status()
        print("Health status:", health)

        # Export metrics
        metrics = telemetry.export_metrics()
        print("Metrics exported:", len(metrics["events"]), "events")

    asyncio.run(example_usage())






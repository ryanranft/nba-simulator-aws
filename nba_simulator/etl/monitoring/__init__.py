"""
Monitoring and telemetry for NBA data scrapers

Provides comprehensive monitoring with:
- Performance metrics (requests, response times, throughput)
- Data quality metrics (validation, duplicates)
- Real-time health status
- Structured logging
- Prometheus integration (optional)
- S3 event logging (optional)

Usage:
    from nba_simulator.etl.monitoring import ScraperTelemetry, TelemetryManager

    # Single scraper
    telemetry = ScraperTelemetry("espn_scraper")

    async with telemetry.track_operation("fetch_data"):
        # Your scraping code
        pass

    # Multiple scrapers
    manager = TelemetryManager()
    espn_telemetry = manager.get_scraper_telemetry("espn")

Version: 2.0
"""

from .telemetry import (
    ScraperTelemetry,
    TelemetryManager,
    MetricsCollector,
    TelemetryEvent,
    PerformanceMetrics,
    DataQualityMetrics,
    LogLevel,
    MetricType,
)

__all__ = [
    "ScraperTelemetry",
    "TelemetryManager",
    "MetricsCollector",
    "TelemetryEvent",
    "PerformanceMetrics",
    "DataQualityMetrics",
    "LogLevel",
    "MetricType",
]

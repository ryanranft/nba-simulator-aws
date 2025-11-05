"""
NBA Simulator Monitoring Module

Provides comprehensive monitoring and health management:
- DIMS (Data Inventory Management System)
- Scraper health monitoring
- System telemetry collection
- CloudWatch metrics integration
- Real-time dashboards

Components:
- dims: Data inventory verification and tracking
- health: Scraper and system health checks
- telemetry: Metrics collection and aggregation
- cloudwatch: AWS CloudWatch integration
- dashboards: Monitoring visualization

Usage:
    from nba_simulator.monitoring import DIMS, HealthMonitor

    # DIMS verification
    dims = DIMS()
    results = dims.verify_all_metrics()

    # Health monitoring
    health = HealthMonitor()
    status = await health.check_scraper('espn')
"""

from .dims import DIMS, DIMSCore, DIMSCache

# TODO: Fix health and telemetry module imports
# from .health import HealthMonitor, ScraperHealthCheck
# from .telemetry import TelemetryCollector, MetricsPublisher

__all__ = [
    # DIMS
    "DIMS",
    "DIMSCore",
    "DIMSCache",
    # Health (TODO: re-enable after fixing imports)
    # 'HealthMonitor',
    # 'ScraperHealthCheck',
    # Telemetry (TODO: re-enable after fixing imports)
    # 'TelemetryCollector',
    # 'MetricsPublisher',
]

__version__ = "1.0.0"

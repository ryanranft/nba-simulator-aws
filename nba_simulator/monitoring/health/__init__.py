"""
Health Monitoring Module

Provides comprehensive health monitoring for NBA data scrapers and systems:
- Scraper health checks
- System resource monitoring
- Performance metrics
- Alert management

Components:
- HealthMonitor: Main health monitoring class
- ScraperHealthCheck: Individual scraper health checks
- SystemHealth: System-wide health metrics
- AlertManager: Health-based alerting

Usage:
    from nba_simulator.monitoring.health import HealthMonitor
    
    monitor = HealthMonitor()
    await monitor.start_monitoring()
    
    # Check scraper health
    health = await monitor.check_scraper('espn')
"""

from .monitor import ScraperHealthMonitor, HealthCheckManager, HealthStatus, HealthMetrics
from .alert_manager import AlertManager, Alert, AlertSeverity, AlertStatus
# from .scraper_health import ScraperHealthCheck  # Stub

# Backwards compatibility aliases
HealthMonitor = ScraperHealthMonitor

__all__ = [
    'ScraperHealthMonitor',
    'HealthMonitor',  # Alias
    'HealthCheckManager',
    'HealthStatus',
    'HealthMetrics',
    'AlertManager',
    'Alert',
    'AlertSeverity',
    'AlertStatus',
    # 'ScraperHealthCheck',
]

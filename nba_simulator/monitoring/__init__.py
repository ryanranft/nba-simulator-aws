"""
NBA Simulator Monitoring Module

Provides comprehensive monitoring and health management:
- DIMS (Data Inventory Management System)
- Quality Monitoring (Data quality checks and reporting)
- Alert System (Multi-channel notifications and escalation)
- Scraper health monitoring
- System telemetry collection
- CloudWatch metrics integration
- Real-time dashboards

Components:
- dims: Data inventory verification and tracking
- quality: Data quality checks, metrics, and reporting
- alerts: Multi-channel alerting with escalation
- health: Scraper and system health checks
- telemetry: Metrics collection and aggregation
- cloudwatch: AWS CloudWatch integration
- dashboards: Monitoring visualization

Usage:
    from nba_simulator.monitoring import (
        # DIMS
        DIMS,
        # Quality
        QualityMonitor,
        DataQualityChecker,
        QualityReportGenerator,
        # Alerts
        AlertManager,
        EmailNotifier,
        SlackNotifier
    )

    # DIMS verification
    dims = DIMS()
    results = dims.verify_all_metrics()

    # Quality monitoring
    quality = QualityMonitor("nba_data")
    checker = DataQualityChecker(quality)
    check_result = checker.run_check()

    # Alert management
    alert_manager = AlertManager()
    alert_manager.send_alert(
        alert_type="data_quality_issue",
        severity="high",
        message="Quality dropped below threshold"
    )
"""

from .dims import DIMS, DIMSCore, DIMSCache
from .quality import (
    QualityMonitor,
    QualityStatus,
    QualityMetric,
    DataQualityChecker,
    DataQualityConfig,
    QualityMetricsTracker,
    QualityThreshold,
    QualityReportGenerator,
    ReportFormat,
)
from .alerts import (
    AlertManager,
    AlertConfig,
    EmailNotifier,
    SlackNotifier,
    WebhookNotifier,
    NotificationChannel,
    AlertDeduplicator,
    EscalationPolicy,
    AlertHistory,
)

# TODO: Fix health and telemetry module imports
# from .health import HealthMonitor, ScraperHealthCheck
# from .telemetry import TelemetryCollector, MetricsPublisher

__all__ = [
    # DIMS
    "DIMS",
    "DIMSCore",
    "DIMSCache",
    # Quality Monitoring
    "QualityMonitor",
    "QualityStatus",
    "QualityMetric",
    "DataQualityChecker",
    "DataQualityConfig",
    "QualityMetricsTracker",
    "QualityThreshold",
    "QualityReportGenerator",
    "ReportFormat",
    # Alert System
    "AlertManager",
    "AlertConfig",
    "EmailNotifier",
    "SlackNotifier",
    "WebhookNotifier",
    "NotificationChannel",
    "AlertDeduplicator",
    "EscalationPolicy",
    "AlertHistory",
    # Health (TODO: re-enable after fixing imports)
    # 'HealthMonitor',
    # 'ScraperHealthCheck',
    # Telemetry (TODO: re-enable after fixing imports)
    # 'TelemetryCollector',
    # 'MetricsPublisher',
]

__version__ = "1.0.0"

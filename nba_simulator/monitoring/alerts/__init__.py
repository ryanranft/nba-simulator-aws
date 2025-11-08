"""
Alert System Module

Comprehensive alert management and notification system:
- Alert creation and management
- Multi-channel notifications (Email, Slack, Webhooks)
- Alert grouping and deduplication
- Escalation policies
- Alert history and resolution tracking
- Integration with monitoring systems

Components:
- AlertManager: Main alert orchestration
- NotificationChannel: Base for all notification channels
- EmailNotifier: Email notifications
- SlackNotifier: Slack notifications
- WebhookNotifier: Generic webhook notifications
- AlertDeduplicator: Prevent duplicate alerts
- EscalationPolicy: Alert escalation logic

Created: November 5, 2025
Phase: 4 (Monitoring)
"""

from .manager import AlertManager, AlertConfig
from .channels import (
    NotificationChannel,
    EmailNotifier,
    SlackNotifier,
    WebhookNotifier,
    NotificationConfig,
)
from .deduplicator import AlertDeduplicator, DeduplicationConfig
from .escalation import EscalationPolicy, EscalationLevel
from .history import AlertHistory, AlertResolution

__all__ = [
    # Manager
    "AlertManager",
    "AlertConfig",
    # Channels
    "NotificationChannel",
    "EmailNotifier",
    "SlackNotifier",
    "WebhookNotifier",
    "NotificationConfig",
    # Deduplication
    "AlertDeduplicator",
    "DeduplicationConfig",
    # Escalation
    "EscalationPolicy",
    "EscalationLevel",
    # History
    "AlertHistory",
    "AlertResolution",
]

__version__ = "1.0.0"

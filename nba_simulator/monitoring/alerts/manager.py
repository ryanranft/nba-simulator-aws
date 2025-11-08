"""
Alert Manager

Main orchestrator for the alert system:
- Coordinates all alert components
- Manages notification routing
- Handles deduplication
- Manages escalation
- Tracks history

Created: November 5, 2025
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from .channels import NotificationChannel, NotificationResult, ConsoleNotifier
from .deduplicator import AlertDeduplicator, DeduplicationConfig
from .escalation import EscalationPolicy, EscalationLevel, create_default_policy
from .history import AlertHistory, ResolutionStatus
from ...utils import setup_logging


@dataclass
class AlertConfig:
    """
    Configuration for alert manager.

    Attributes:
        enabled: Whether alerting is enabled
        default_channels: Default notification channels
        enable_deduplication: Enable alert deduplication
        enable_escalation: Enable alert escalation
        deduplication_config: Deduplication configuration
    """

    enabled: bool = True
    default_channels: Set[str] = field(default_factory=lambda: {"console"})
    enable_deduplication: bool = True
    enable_escalation: bool = True
    deduplication_config: Optional[DeduplicationConfig] = None


class AlertManager:
    """
    Main alert management orchestrator.

    Coordinates:
    - Notification channels
    - Alert deduplication
    - Escalation policies
    - Alert history

    Features:
    - Send alerts through multiple channels
    - Automatic deduplication
    - Time-based escalation
    - Resolution tracking
    - Statistics and reporting
    """

    def __init__(
        self,
        config: Optional[AlertConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize alert manager.

        Args:
            config: Alert configuration
            logger: Optional logger instance
        """
        self.config = config or AlertConfig()
        self.logger = logger or setup_logging("nba_simulator.monitoring.alerts.manager")

        # Components
        self.channels: Dict[str, NotificationChannel] = {}
        self.deduplicator: Optional[AlertDeduplicator] = None
        self.escalation_policy: Optional[EscalationPolicy] = None
        self.history = AlertHistory(logger=self.logger)

        # Initialize deduplicator
        if self.config.enable_deduplication:
            dedup_config = self.config.deduplication_config or DeduplicationConfig()
            self.deduplicator = AlertDeduplicator(dedup_config, self.logger)

        # Initialize escalation policy
        if self.config.enable_escalation:
            self.escalation_policy = create_default_policy()

        # Add default console channel
        self.add_channel("console", ConsoleNotifier())

        self.logger.info("Alert manager initialized")

    def add_channel(self, name: str, channel: NotificationChannel):
        """
        Add notification channel.

        Args:
            name: Channel name
            channel: Notification channel instance
        """
        self.channels[name] = channel
        self.logger.info(f"Added notification channel: {name}")

    def remove_channel(self, name: str):
        """
        Remove notification channel.

        Args:
            name: Channel name
        """
        if name in self.channels:
            del self.channels[name]
            self.logger.info(f"Removed notification channel: {name}")

    def set_escalation_policy(self, policy: EscalationPolicy):
        """
        Set custom escalation policy.

        Args:
            policy: Escalation policy
        """
        self.escalation_policy = policy
        self.logger.info(f"Set escalation policy: {policy.policy_name}")

    def send_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        channels: Optional[Set[str]] = None,
        **metadata,
    ) -> Dict[str, any]:
        """
        Send alert through notification channels.

        Args:
            alert_type: Type of alert
            severity: Severity level (info, low, medium, high, critical)
            message: Alert message
            channels: Optional channel override
            **metadata: Additional alert metadata

        Returns:
            Dictionary with alert results
        """
        if not self.config.enabled:
            return {"success": False, "message": "Alerting disabled", "alert_id": None}

        # Generate alert ID
        alert_id = str(uuid.uuid4())[:8]

        # Check deduplication
        should_send = True
        dedup_reason = None

        if self.deduplicator:
            should_send, dedup_reason = self.deduplicator.should_send_alert(
                alert_type=alert_type, severity=severity, message=message, **metadata
            )

        if not should_send:
            self.logger.debug(
                f"Alert suppressed due to deduplication: {alert_type} "
                f"[{severity}] - {dedup_reason}"
            )
            return {
                "success": False,
                "message": f"Suppressed: {dedup_reason}",
                "alert_id": alert_id,
                "suppressed": True,
            }

        # Record in history
        self.history.record_alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            **metadata,
        )

        # Register for escalation if enabled
        if self.escalation_policy:
            self.escalation_policy.register_alert(
                alert_id=alert_id, alert_type=alert_type, severity=severity
            )

        # Determine channels to use
        target_channels = channels or self.config.default_channels

        # Send notifications
        results = []
        for channel_name in target_channels:
            if channel_name not in self.channels:
                self.logger.warning(f"Channel not found: {channel_name}")
                continue

            channel = self.channels[channel_name]

            # Add severity to metadata for channel-specific formatting
            metadata["severity"] = severity
            metadata["alert_type"] = alert_type
            metadata["alert_id"] = alert_id

            # Determine color for Slack (if applicable)
            if channel_name == "slack":
                metadata["color"] = self._get_severity_color(severity)

            # Send notification
            result = channel.send(
                subject=f"[{severity.upper()}] {alert_type}",
                message=message,
                **metadata,
            )

            results.append(result)

            if result.success:
                self.history.record_notification(alert_id)

        # Determine overall success
        success = any(r.success for r in results)

        self.logger.info(
            f"Alert sent: {alert_id} [{severity}] {alert_type} - "
            f"{len([r for r in results if r.success])}/{len(results)} channels succeeded"
        )

        return {
            "success": success,
            "message": "Alert sent",
            "alert_id": alert_id,
            "channels": [r.to_dict() for r in results],
            "suppressed": False,
        }

    def check_escalations(self):
        """
        Check for alerts that need escalation.

        Should be called periodically (e.g., every 5 minutes).
        """
        if not self.escalation_policy:
            return

        active_alerts = self.escalation_policy.get_active_alerts()

        for alert in active_alerts:
            escalation_result = self.escalation_policy.check_escalation(alert.alert_id)

            if escalation_result:
                level, channels = escalation_result

                # Record escalation
                self.history.record_escalation(alert.alert_id, level.value)

                # Send escalated notification
                self.send_alert(
                    alert_type=f"{alert.alert_type}_escalated",
                    severity=alert.severity,
                    message=f"[ESCALATED to {level.value}] {alert.alert_type}",
                    channels=channels,
                    original_alert_id=alert.alert_id,
                    escalation_level=level.value,
                )

    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str = "system",
        status: ResolutionStatus = ResolutionStatus.RESOLVED,
        notes: str = "",
    ):
        """
        Resolve an alert.

        Args:
            alert_id: Alert identifier
            resolved_by: Who resolved it
            status: Resolution status
            notes: Resolution notes
        """
        # Mark as resolved in history
        self.history.resolve_alert(
            alert_id=alert_id, resolved_by=resolved_by, status=status, notes=notes
        )

        # Remove from escalation tracking
        if self.escalation_policy:
            self.escalation_policy.resolve_alert(alert_id)

        # Clear deduplication fingerprint
        if self.deduplicator:
            alert = self.history.get_alert(alert_id)
            if alert:
                self.deduplicator.clear_fingerprint(
                    alert.alert_type, alert.severity, alert.message
                )

        self.logger.info(f"Alert resolved: {alert_id}")

    def get_active_alerts(self, severity: Optional[str] = None) -> List:
        """
        Get active alerts.

        Args:
            severity: Optional severity filter

        Returns:
            List of active alerts
        """
        alerts = self.history.get_active_alerts()

        if severity:
            alerts = [a for a in alerts if a.severity == severity.lower()]

        return alerts

    def get_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive alert statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "manager": {
                "enabled": self.config.enabled,
                "channels": len(self.channels),
                "deduplication_enabled": self.config.enable_deduplication,
                "escalation_enabled": self.config.enable_escalation,
            },
            "history": self.history.get_statistics(hours=24),
            "channels": {},
        }

        # Channel statistics
        for name, channel in self.channels.items():
            stats["channels"][name] = channel.get_statistics()

        # Deduplication statistics
        if self.deduplicator:
            stats["deduplication"] = self.deduplicator.get_suppression_stats()

        # Escalation statistics
        if self.escalation_policy:
            stats["escalation"] = self.escalation_policy.get_statistics()

        return stats

    @staticmethod
    def _get_severity_color(severity: str) -> str:
        """
        Get color for severity (for Slack).

        Args:
            severity: Severity level

        Returns:
            Hex color code
        """
        colors = {
            "info": "#36a64f",  # Green
            "low": "#2196F3",  # Blue
            "medium": "#FFC107",  # Amber
            "high": "#FF9800",  # Orange
            "critical": "#F44336",  # Red
        }
        return colors.get(severity.lower(), "#808080")  # Gray default

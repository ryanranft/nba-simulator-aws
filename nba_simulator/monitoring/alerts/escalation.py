"""
Escalation Policies

Alert escalation system based on severity and time:
- Multi-level escalation
- Time-based escalation
- Severity-based routing
- Escalation chains

Created: November 5, 2025
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from ...utils import setup_logging


class EscalationLevel(Enum):
    """Escalation severity levels"""

    LEVEL_1 = "level_1"  # Normal
    LEVEL_2 = "level_2"  # Elevated
    LEVEL_3 = "level_3"  # Critical
    LEVEL_4 = "level_4"  # Emergency


@dataclass
class EscalationRule:
    """
    Rule for alert escalation.

    Attributes:
        severity_threshold: Minimum severity to trigger
        time_threshold_minutes: Minutes before escalating
        target_level: Target escalation level
        notification_channels: Channels to notify
        repeat_interval_minutes: How often to repeat notifications
    """

    severity_threshold: str
    time_threshold_minutes: int
    target_level: EscalationLevel
    notification_channels: Set[str]
    repeat_interval_minutes: Optional[int] = None


@dataclass
class EscalatedAlert:
    """
    Alert with escalation tracking.

    Attributes:
        alert_id: Unique alert identifier
        alert_type: Type of alert
        severity: Current severity
        created_at: When alert was created
        escalation_level: Current escalation level
        last_escalated: When last escalated
        escalation_count: Number of escalations
        notified_channels: Channels that were notified
    """

    alert_id: str
    alert_type: str
    severity: str
    created_at: datetime
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_1
    last_escalated: Optional[datetime] = None
    escalation_count: int = 0
    notified_channels: Set[str] = field(default_factory=set)

    def escalate(self, new_level: EscalationLevel):
        """Escalate to new level"""
        self.escalation_level = new_level
        self.last_escalated = datetime.now(timezone.utc)
        self.escalation_count += 1


class EscalationPolicy:
    """
    Manages alert escalation based on time and severity.

    Features:
    - Define escalation rules
    - Track alert age
    - Automatic escalation
    - Repeat notifications
    - Channel routing by level
    """

    def __init__(self, policy_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize escalation policy.

        Args:
            policy_name: Name of this policy
            logger: Optional logger instance
        """
        self.policy_name = policy_name
        self.logger = logger or setup_logging(
            f"nba_simulator.monitoring.alerts.escalation.{policy_name}"
        )

        # Escalation rules by level
        self.rules: Dict[EscalationLevel, List[EscalationRule]] = {
            level: [] for level in EscalationLevel
        }

        # Track active alerts
        self.active_alerts: Dict[str, EscalatedAlert] = {}

        # Default severity ordering (for comparison)
        self.severity_order = {
            "info": 1,
            "low": 2,
            "medium": 3,
            "high": 4,
            "critical": 5,
        }

    def add_rule(self, rule: EscalationRule):
        """
        Add escalation rule.

        Args:
            rule: Escalation rule to add
        """
        self.rules[rule.target_level].append(rule)
        self.logger.info(
            f"Added escalation rule: {rule.severity_threshold}+ after "
            f"{rule.time_threshold_minutes}min -> {rule.target_level.value}"
        )

    def register_alert(
        self, alert_id: str, alert_type: str, severity: str
    ) -> EscalatedAlert:
        """
        Register new alert for escalation tracking.

        Args:
            alert_id: Unique alert identifier
            alert_type: Type of alert
            severity: Alert severity

        Returns:
            EscalatedAlert object
        """
        alert = EscalatedAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity.lower(),
            created_at=datetime.now(timezone.utc),
        )

        self.active_alerts[alert_id] = alert

        self.logger.info(f"Registered alert for escalation: {alert_id} [{severity}]")

        return alert

    def check_escalation(
        self, alert_id: str
    ) -> Optional[tuple[EscalationLevel, Set[str]]]:
        """
        Check if alert should be escalated.

        Args:
            alert_id: Alert identifier

        Returns:
            Tuple of (escalation_level, notification_channels) if should escalate,
            None otherwise
        """
        if alert_id not in self.active_alerts:
            return None

        alert = self.active_alerts[alert_id]
        current_time = datetime.now(timezone.utc)

        # Calculate alert age
        alert_age_minutes = (current_time - alert.created_at).total_seconds() / 60

        # Get severity value for comparison
        severity_value = self.severity_order.get(alert.severity, 0)

        # Check each escalation level (in order)
        for level in [
            EscalationLevel.LEVEL_2,
            EscalationLevel.LEVEL_3,
            EscalationLevel.LEVEL_4,
        ]:
            # Skip if already at or above this level
            if alert.escalation_level.value >= level.value:
                continue

            # Check rules for this level
            for rule in self.rules[level]:
                # Check severity threshold
                rule_severity = self.severity_order.get(
                    rule.severity_threshold.lower(), 0
                )
                if severity_value < rule_severity:
                    continue

                # Check time threshold
                if alert_age_minutes < rule.time_threshold_minutes:
                    continue

                # Should escalate!
                alert.escalate(level)

                self.logger.warning(
                    f"Escalating alert {alert_id} to {level.value} "
                    f"(age: {alert_age_minutes:.1f}min, severity: {alert.severity})"
                )

                return level, rule.notification_channels

        # Check for repeat notifications
        if alert.last_escalated:
            for rule in self.rules[alert.escalation_level]:
                if rule.repeat_interval_minutes:
                    time_since_last = (
                        current_time - alert.last_escalated
                    ).total_seconds() / 60

                    if time_since_last >= rule.repeat_interval_minutes:
                        alert.last_escalated = current_time

                        self.logger.info(
                            f"Repeating notification for alert {alert_id} "
                            f"(interval: {rule.repeat_interval_minutes}min)"
                        )

                        return alert.escalation_level, rule.notification_channels

        return None

    def resolve_alert(self, alert_id: str):
        """
        Mark alert as resolved.

        Args:
            alert_id: Alert identifier
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]

            self.logger.info(
                f"Resolved alert {alert_id} at {alert.escalation_level.value} "
                f"(escalations: {alert.escalation_count})"
            )

            del self.active_alerts[alert_id]

    def get_active_alerts(
        self, level: Optional[EscalationLevel] = None
    ) -> List[EscalatedAlert]:
        """
        Get active alerts, optionally filtered by level.

        Args:
            level: Optional escalation level filter

        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())

        if level:
            alerts = [a for a in alerts if a.escalation_level == level]

        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def get_statistics(self) -> Dict[str, any]:
        """
        Get escalation statistics.

        Returns:
            Dictionary with statistics
        """
        # Count alerts by level
        by_level = {}
        for level in EscalationLevel:
            count = sum(
                1 for a in self.active_alerts.values() if a.escalation_level == level
            )
            by_level[level.value] = count

        # Total escalations
        total_escalations = sum(a.escalation_count for a in self.active_alerts.values())

        return {
            "policy_name": self.policy_name,
            "active_alerts": len(self.active_alerts),
            "by_level": by_level,
            "total_escalations": total_escalations,
            "rules_count": sum(len(rules) for rules in self.rules.values()),
        }


def create_default_policy() -> EscalationPolicy:
    """
    Create default escalation policy.

    Returns:
        EscalationPolicy with sensible defaults
    """
    policy = EscalationPolicy("default")

    # Level 2: Elevated (after 30 min for high+ severity)
    policy.add_rule(
        EscalationRule(
            severity_threshold="high",
            time_threshold_minutes=30,
            target_level=EscalationLevel.LEVEL_2,
            notification_channels={"email", "slack"},
        )
    )

    # Level 3: Critical (after 1 hour for high+ or 30 min for critical)
    policy.add_rule(
        EscalationRule(
            severity_threshold="high",
            time_threshold_minutes=60,
            target_level=EscalationLevel.LEVEL_3,
            notification_channels={"email", "slack", "webhook"},
            repeat_interval_minutes=30,
        )
    )

    policy.add_rule(
        EscalationRule(
            severity_threshold="critical",
            time_threshold_minutes=30,
            target_level=EscalationLevel.LEVEL_3,
            notification_channels={"email", "slack", "webhook"},
            repeat_interval_minutes=30,
        )
    )

    # Level 4: Emergency (after 2 hours unresolved critical)
    policy.add_rule(
        EscalationRule(
            severity_threshold="critical",
            time_threshold_minutes=120,
            target_level=EscalationLevel.LEVEL_4,
            notification_channels={"email", "slack", "webhook"},
            repeat_interval_minutes=15,  # More frequent for emergencies
        )
    )

    return policy

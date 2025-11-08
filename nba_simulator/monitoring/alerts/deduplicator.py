"""
Alert Deduplicator

Prevents duplicate alerts from flooding notification channels:
- Time-based deduplication
- Content-based deduplication
- Fingerprint generation
- Suppression tracking

Created: November 5, 2025
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Set

from ...utils import setup_logging


@dataclass
class DeduplicationConfig:
    """
    Configuration for alert deduplication.

    Attributes:
        enabled: Whether deduplication is enabled
        window_minutes: Time window for deduplication
        max_suppressed: Maximum alerts to suppress before forcing
        fingerprint_fields: Fields to include in fingerprint
    """

    enabled: bool = True
    window_minutes: int = 60  # 1 hour default
    max_suppressed: int = 10  # Force send after 10 suppressions
    fingerprint_fields: Set[str] = field(
        default_factory=lambda: {"alert_type", "severity", "message"}
    )


@dataclass
class AlertFingerprint:
    """
    Unique identifier for an alert.

    Attributes:
        fingerprint: Hash of alert characteristics
        alert_type: Type of alert
        severity: Severity level
        first_seen: When first seen
        last_seen: When last seen
        count: Number of times seen
    """

    fingerprint: str
    alert_type: str
    severity: str
    first_seen: datetime
    last_seen: datetime
    count: int = 1

    def update(self):
        """Update fingerprint with new occurrence"""
        self.last_seen = datetime.now(timezone.utc)
        self.count += 1


class AlertDeduplicator:
    """
    Deduplicates alerts to prevent notification flooding.

    Features:
    - Generates fingerprints from alert characteristics
    - Tracks recent alerts in time window
    - Suppresses duplicate alerts
    - Forces alerts after threshold
    - Provides suppression statistics
    """

    def __init__(
        self,
        config: Optional[DeduplicationConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize deduplicator.

        Args:
            config: Deduplication configuration
            logger: Optional logger instance
        """
        self.config = config or DeduplicationConfig()
        self.logger = logger or setup_logging(
            "nba_simulator.monitoring.alerts.deduplicator"
        )

        # Track recent alerts by fingerprint
        self.recent_alerts: Dict[str, AlertFingerprint] = {}

        # Statistics
        self.total_alerts = 0
        self.suppressed_alerts = 0
        self.forced_alerts = 0

    def should_send_alert(
        self, alert_type: str, severity: str, message: str, **metadata
    ) -> tuple[bool, Optional[str]]:
        """
        Determine if alert should be sent.

        Args:
            alert_type: Type of alert
            severity: Severity level
            message: Alert message
            **metadata: Additional alert metadata

        Returns:
            Tuple of (should_send, reason)
        """
        self.total_alerts += 1

        if not self.config.enabled:
            return True, "deduplication_disabled"

        # Generate fingerprint
        fingerprint = self._generate_fingerprint(
            alert_type=alert_type, severity=severity, message=message, **metadata
        )

        # Clean up old fingerprints
        self._cleanup_old_fingerprints()

        # Check if we've seen this alert recently
        if fingerprint in self.recent_alerts:
            alert_fp = self.recent_alerts[fingerprint]

            # Check if we've suppressed too many
            if alert_fp.count >= self.config.max_suppressed:
                # Force send after threshold
                self.forced_alerts += 1
                alert_fp.count = 0  # Reset counter
                alert_fp.update()

                self.logger.info(
                    f"Forcing alert after {self.config.max_suppressed} suppressions: "
                    f"{alert_type} [{severity}]"
                )

                return True, f"forced_after_{self.config.max_suppressed}_suppressions"

            # Suppress duplicate
            alert_fp.update()
            self.suppressed_alerts += 1

            self.logger.debug(
                f"Suppressing duplicate alert (count: {alert_fp.count}): "
                f"{alert_type} [{severity}]"
            )

            return False, f"duplicate_within_{self.config.window_minutes}min"

        # New alert - add to tracking
        self.recent_alerts[fingerprint] = AlertFingerprint(
            fingerprint=fingerprint,
            alert_type=alert_type,
            severity=severity,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
        )

        return True, "new_alert"

    def _generate_fingerprint(self, **kwargs) -> str:
        """
        Generate unique fingerprint for alert.

        Args:
            **kwargs: Alert fields

        Returns:
            Fingerprint hash
        """
        # Extract fields for fingerprint
        fingerprint_data = {}
        for field in self.config.fingerprint_fields:
            if field in kwargs:
                fingerprint_data[field] = kwargs[field]

        # Create stable string representation
        fingerprint_str = "&".join(
            f"{k}={v}" for k, v in sorted(fingerprint_data.items())
        )

        # Generate hash
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]

    def _cleanup_old_fingerprints(self):
        """Remove fingerprints outside the time window"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=self.config.window_minutes
        )

        # Find expired fingerprints
        expired = [
            fp
            for fp, alert_fp in self.recent_alerts.items()
            if alert_fp.last_seen < cutoff_time
        ]

        # Remove expired
        for fp in expired:
            del self.recent_alerts[fp]

    def get_suppression_stats(self) -> Dict[str, any]:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with statistics
        """
        suppression_rate = (
            (self.suppressed_alerts / self.total_alerts * 100)
            if self.total_alerts > 0
            else 0
        )

        return {
            "total_alerts": self.total_alerts,
            "suppressed_alerts": self.suppressed_alerts,
            "forced_alerts": self.forced_alerts,
            "sent_alerts": self.total_alerts - self.suppressed_alerts,
            "suppression_rate": suppression_rate,
            "active_fingerprints": len(self.recent_alerts),
            "window_minutes": self.config.window_minutes,
        }

    def clear_fingerprint(self, alert_type: str, severity: str, message: str):
        """
        Manually clear a specific alert fingerprint.

        Args:
            alert_type: Alert type
            severity: Severity level
            message: Alert message
        """
        fingerprint = self._generate_fingerprint(
            alert_type=alert_type, severity=severity, message=message
        )

        if fingerprint in self.recent_alerts:
            del self.recent_alerts[fingerprint]
            self.logger.debug(f"Cleared fingerprint: {fingerprint}")

    def reset_statistics(self):
        """Reset deduplication statistics"""
        self.total_alerts = 0
        self.suppressed_alerts = 0
        self.forced_alerts = 0
        self.logger.info("Deduplication statistics reset")

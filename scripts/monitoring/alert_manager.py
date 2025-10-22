#!/usr/bin/env python3
"""
Alert Manager - Email/Slack Notifications with Deduplication

Provides comprehensive alert management for NBA data scrapers:
- Email alerts via AWS SES
- Slack webhook notifications
- Alert deduplication to prevent spam
- Escalation policies for critical issues
- Alert history and analytics
- Integration with health monitoring

Based on Crawl4AI MCP server alerting patterns.

Usage:
    from alert_manager import AlertManager, AlertChannel

    # Alert manager
    alert_manager = AlertManager()
    await alert_manager.send_alert("espn_scraper", "critical", "Scraper failed")

    # Email channel
    email_channel = EmailAlertChannel(ses_region="us-east-1")
    await email_channel.send_alert(alert_data)

Version: 1.0
Created: October 13, 2025
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import aiohttp

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert status"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Alert data structure"""

    alert_id: str
    scraper_name: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.PENDING
    channels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "scraper_name": self.scraper_name,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "channels": self.channels,
            "metadata": self.metadata,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
        }

    def generate_hash(self) -> str:
        """Generate hash for deduplication"""
        content = (
            f"{self.scraper_name}:{self.severity.value}:{self.title}:{self.message}"
        )
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class AlertChannel:
    """Base alert channel"""

    channel_name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert through this channel"""
        raise NotImplementedError


class EmailAlertChannel(AlertChannel):
    """Email alert channel using AWS SES"""

    def __init__(
        self,
        ses_region: str = "us-east-1",
        from_email: str = "alerts@nba-simulator.com",
        to_emails: List[str] = None,
    ):
        super().__init__("email")
        self.ses_region = ses_region
        self.from_email = from_email
        self.to_emails = to_emails or ["admin@nba-simulator.com"]
        self.logger = logging.getLogger("email_alert_channel")

        # Initialize SES client
        if HAS_BOTO3:
            self.ses_client = boto3.client("ses", region_name=ses_region)
        else:
            self.ses_client = None
            self.logger.warning("boto3 not available, email alerts disabled")

    async def send_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        if not self.ses_client:
            self.logger.error("SES client not available")
            return False

        try:
            # Create email content
            subject = (
                f"[{alert.severity.value.upper()}] NBA Scraper Alert: {alert.title}"
            )

            body_text = f"""
NBA Scraper Alert

Scraper: {alert.scraper_name}
Severity: {alert.severity.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Title: {alert.title}

Message:
{alert.message}

Alert ID: {alert.alert_id}

---
NBA Simulator Alert System
            """.strip()

            body_html = f"""
            <html>
            <body>
                <h2>NBA Scraper Alert</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr><td><strong>Scraper:</strong></td><td>{alert.scraper_name}</td></tr>
                    <tr><td><strong>Severity:</strong></td><td style="color: {'red' if alert.severity == AlertSeverity.CRITICAL else 'orange' if alert.severity == AlertSeverity.WARNING else 'blue'}">{alert.severity.value.upper()}</td></tr>
                    <tr><td><strong>Time:</strong></td><td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
                    <tr><td><strong>Title:</strong></td><td>{alert.title}</td></tr>
                </table>

                <h3>Message:</h3>
                <p>{alert.message.replace(chr(10), '<br>')}</p>

                <p><small>Alert ID: {alert.alert_id}</small></p>
                <hr>
                <p><small>NBA Simulator Alert System</small></p>
            </body>
            </html>
            """

            # Send email
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": self.to_emails},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": body_text, "Charset": "UTF-8"},
                        "Html": {"Data": body_html, "Charset": "UTF-8"},
                    },
                },
            )

            self.logger.info(f"Email alert sent successfully: {response['MessageId']}")
            return True

        except ClientError as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending email alert: {e}")
            return False


class SlackAlertChannel(AlertChannel):
    """Slack alert channel using webhooks"""

    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        super().__init__("slack")
        self.webhook_url = webhook_url
        self.channel = channel
        self.logger = logging.getLogger("slack_alert_channel")

    async def send_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        if not HAS_AIOHTTP:
            self.logger.error("aiohttp not available for Slack alerts")
            return False

        try:
            # Determine color based on severity
            color_map = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.CRITICAL: "danger",
                AlertSeverity.EMERGENCY: "danger",
            }

            # Create Slack message
            slack_message = {
                "channel": self.channel,
                "username": "NBA Scraper Bot",
                "icon_emoji": ":basketball:",
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "good"),
                        "title": f"[{alert.severity.value.upper()}] {alert.title}",
                        "fields": [
                            {
                                "title": "Scraper",
                                "value": alert.scraper_name,
                                "short": True,
                            },
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True,
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime(
                                    "%Y-%m-%d %H:%M:%S UTC"
                                ),
                                "short": True,
                            },
                            {
                                "title": "Alert ID",
                                "value": alert.alert_id,
                                "short": True,
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False,
                            },
                        ],
                        "footer": "NBA Simulator Alert System",
                        "ts": int(alert.timestamp.timestamp()),
                    }
                ],
            }

            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        self.logger.info("Slack alert sent successfully")
                        return True
                    else:
                        self.logger.error(f"Slack webhook failed: {response.status}")
                        return False

        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False


class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self, deduplication_window_minutes: int = 30):
        self.deduplication_window_minutes = deduplication_window_minutes
        self.logger = logging.getLogger("alert_manager")
        self.channels: Dict[str, AlertChannel] = {}
        self.alert_history: List[Alert] = []
        self.deduplication_cache: Dict[str, datetime] = {}

        # Register default channels
        self._register_default_channels()

    def _register_default_channels(self) -> None:
        """Register default alert channels"""
        # Email channel (if SES is configured)
        try:
            email_channel = EmailAlertChannel()
            self.channels["email"] = email_channel
        except Exception as e:
            self.logger.warning(f"Email channel not available: {e}")

        # Slack channel (if webhook URL is configured)
        slack_webhook = self._get_slack_webhook_url()
        if slack_webhook:
            try:
                slack_channel = SlackAlertChannel(slack_webhook)
                self.channels["slack"] = slack_channel
            except Exception as e:
                self.logger.warning(f"Slack channel not available: {e}")

    def _get_slack_webhook_url(self) -> Optional[str]:
        """Get Slack webhook URL from environment or config"""
        import os

        return os.getenv("SLACK_WEBHOOK_URL")

    def register_channel(self, channel_name: str, channel: AlertChannel) -> None:
        """Register a new alert channel"""
        self.channels[channel_name] = channel
        self.logger.info(f"Registered alert channel: {channel_name}")

    async def send_alert(
        self,
        scraper_name: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        channels: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send alert through specified channels"""
        # Create alert
        alert_id = self._generate_alert_id()
        alert = Alert(
            alert_id=alert_id,
            scraper_name=scraper_name,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(timezone.utc),
            channels=channels or list(self.channels.keys()),
            metadata=metadata or {},
        )

        # Check for deduplication
        if self._is_duplicate(alert):
            self.logger.info(f"Alert deduplicated: {alert_id}")
            return alert_id

        # Send through channels
        sent_channels = []
        failed_channels = []

        for channel_name in alert.channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                if channel.enabled:
                    try:
                        success = await channel.send_alert(alert)
                        if success:
                            sent_channels.append(channel_name)
                        else:
                            failed_channels.append(channel_name)
                    except Exception as e:
                        self.logger.error(
                            f"Error sending alert through {channel_name}: {e}"
                        )
                        failed_channels.append(channel_name)
                else:
                    self.logger.info(f"Channel {channel_name} is disabled")
            else:
                self.logger.warning(f"Unknown channel: {channel_name}")

        # Update alert status
        if sent_channels:
            alert.status = AlertStatus.SENT
        else:
            alert.status = AlertStatus.FAILED

        # Store in history
        self.alert_history.append(alert)

        # Update deduplication cache
        alert_hash = alert.generate_hash()
        self.deduplication_cache[alert_hash] = alert.timestamp

        # Clean old deduplication entries
        self._cleanup_deduplication_cache()

        self.logger.info(f"Alert {alert_id} sent through {len(sent_channels)} channels")
        return alert_id

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        random_suffix = str(int(time.time() * 1000))[-6:]
        return f"ALERT_{timestamp}_{random_suffix}"

    def _is_duplicate(self, alert: Alert) -> bool:
        """Check if alert is duplicate"""
        alert_hash = alert.generate_hash()

        if alert_hash in self.deduplication_cache:
            last_sent = self.deduplication_cache[alert_hash]
            time_diff = alert.timestamp - last_sent

            if time_diff.total_seconds() < (self.deduplication_window_minutes * 60):
                return True

        return False

    def _cleanup_deduplication_cache(self) -> None:
        """Clean up old deduplication cache entries"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=self.deduplication_window_minutes * 2
        )

        expired_hashes = [
            hash_key
            for hash_key, timestamp in self.deduplication_cache.items()
            if timestamp < cutoff_time
        ]

        for hash_key in expired_hashes:
            del self.deduplication_cache[hash_key]

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.now(timezone.utc)

                self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                return True

        return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now(timezone.utc)

                self.logger.info(f"Alert {alert_id} resolved")
                return True

        return False

    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for specified hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent_alerts = [
            alert for alert in self.alert_history if alert.timestamp >= cutoff_time
        ]

        return [alert.to_dict() for alert in recent_alerts]

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        if not self.alert_history:
            return {"total_alerts": 0}

        total_alerts = len(self.alert_history)

        # Count by severity
        severity_counts = {}
        for alert in self.alert_history:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by status
        status_counts = {}
        for alert in self.alert_history:
            status = alert.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # Count by scraper
        scraper_counts = {}
        for alert in self.alert_history:
            scraper = alert.scraper_name
            scraper_counts[scraper] = scraper_counts.get(scraper, 0) + 1

        # Recent alerts (last 24 hours)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_alerts = sum(
            1 for alert in self.alert_history if alert.timestamp >= recent_cutoff
        )

        return {
            "total_alerts": total_alerts,
            "recent_alerts_24h": recent_alerts,
            "severity_counts": severity_counts,
            "status_counts": status_counts,
            "scraper_counts": scraper_counts,
            "active_channels": len([c for c in self.channels.values() if c.enabled]),
        }


# Example usage
if __name__ == "__main__":

    async def example_usage():
        # Create alert manager
        alert_manager = AlertManager()

        # Send test alert
        alert_id = await alert_manager.send_alert(
            scraper_name="espn_scraper",
            severity=AlertSeverity.CRITICAL,
            title="Scraper Failure",
            message="ESPN scraper has failed 3 consecutive times",
            metadata={"error_count": 3, "last_error": "Connection timeout"},
        )

        print(f"Alert sent: {alert_id}")

        # Get alert stats
        stats = alert_manager.get_alert_stats()
        print(f"Alert stats: {stats}")

        # Get recent alerts
        recent = alert_manager.get_alert_history(hours=1)
        print(f"Recent alerts: {len(recent)}")

    asyncio.run(example_usage())






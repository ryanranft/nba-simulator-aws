"""
Notification Channels

Multi-channel notification system for alerts:
- Email notifications (SMTP)
- Slack notifications (webhooks)
- Generic webhooks
- SMS notifications (future)
- PagerDuty integration (future)

Created: November 5, 2025
"""

import json
import logging
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional
import requests

from ...utils import setup_logging


@dataclass
class NotificationConfig:
    """
    Configuration for notification channels.

    Attributes:
        enabled: Whether notifications are enabled
        retry_attempts: Number of retry attempts
        retry_delay_seconds: Delay between retries
        timeout_seconds: Request timeout
    """

    enabled: bool = True
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    timeout_seconds: int = 10


@dataclass
class NotificationResult:
    """
    Result of a notification attempt.

    Attributes:
        success: Whether notification succeeded
        channel: Channel that sent notification
        message: Result message
        timestamp: When notification was sent
        error: Error message if failed
    """

    success: bool
    channel: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "channel": self.channel,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


class NotificationChannel(ABC):
    """
    Base class for notification channels.

    Provides common functionality for all notification channels:
    - Retry logic
    - Error handling
    - Logging
    - Rate limiting (future)
    """

    def __init__(
        self,
        channel_name: str,
        config: Optional[NotificationConfig] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize notification channel.

        Args:
            channel_name: Name of this channel
            config: Channel configuration
            logger: Optional logger instance
        """
        self.channel_name = channel_name
        self.config = config or NotificationConfig()
        self.logger = logger or setup_logging(
            f"nba_simulator.monitoring.alerts.{channel_name}"
        )

        self.sent_count = 0
        self.failed_count = 0

    def send(self, subject: str, message: str, **kwargs) -> NotificationResult:
        """
        Send notification with retry logic.

        Args:
            subject: Notification subject/title
            message: Notification message
            **kwargs: Channel-specific parameters

        Returns:
            NotificationResult
        """
        if not self.config.enabled:
            return NotificationResult(
                success=False,
                channel=self.channel_name,
                message="Channel disabled",
                error="Channel is not enabled",
            )

        # Try sending with retries
        for attempt in range(self.config.retry_attempts):
            try:
                self._send_notification(subject, message, **kwargs)

                self.sent_count += 1
                self.logger.info(
                    f"Notification sent via {self.channel_name}: {subject}"
                )

                return NotificationResult(
                    success=True, channel=self.channel_name, message=f"Sent: {subject}"
                )

            except Exception as e:
                self.logger.warning(
                    f"Notification attempt {attempt + 1}/{self.config.retry_attempts} "
                    f"failed for {self.channel_name}: {str(e)}"
                )

                if attempt == self.config.retry_attempts - 1:
                    self.failed_count += 1
                    return NotificationResult(
                        success=False,
                        channel=self.channel_name,
                        message=f"Failed: {subject}",
                        error=str(e),
                    )

                # Wait before retry
                import time

                time.sleep(self.config.retry_delay_seconds)

        return NotificationResult(
            success=False,
            channel=self.channel_name,
            message=f"Failed after {self.config.retry_attempts} attempts",
            error="All retry attempts exhausted",
        )

    @abstractmethod
    def _send_notification(self, subject: str, message: str, **kwargs):
        """
        Send notification (implemented by subclasses).

        Args:
            subject: Notification subject
            message: Notification message
            **kwargs: Channel-specific parameters
        """
        raise NotImplementedError("Subclasses must implement _send_notification()")

    def get_statistics(self) -> Dict[str, int]:
        """Get channel statistics"""
        return {
            "sent_count": self.sent_count,
            "failed_count": self.failed_count,
            "success_rate": (
                self.sent_count / (self.sent_count + self.failed_count) * 100
                if (self.sent_count + self.failed_count) > 0
                else 0
            ),
        }


class EmailNotifier(NotificationChannel):
    """
    Email notification channel using SMTP.

    Supports:
    - Plain text and HTML emails
    - Multiple recipients
    - CC and BCC
    - Attachments (future)
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        from_email: str,
        to_emails: List[str],
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        config: Optional[NotificationConfig] = None,
    ):
        """
        Initialize email notifier.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            from_email: Sender email address
            to_emails: List of recipient email addresses
            smtp_username: SMTP username (if required)
            smtp_password: SMTP password (if required)
            use_tls: Whether to use TLS
            config: Notification configuration
        """
        super().__init__("email", config)

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.to_emails = to_emails
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls

    def _send_notification(self, subject: str, message: str, **kwargs):
        """Send email notification"""
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails)

        # Add CC if provided
        cc_emails = kwargs.get("cc", [])
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)

        # Check if HTML content provided
        html_content = kwargs.get("html")
        if html_content:
            # Add both plain text and HTML
            part1 = MIMEText(message, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)
        else:
            # Plain text only
            msg.attach(MIMEText(message, "plain"))

        # Connect to SMTP server and send
        recipients = self.to_emails + cc_emails

        with smtplib.SMTP(
            self.smtp_host, self.smtp_port, timeout=self.config.timeout_seconds
        ) as server:
            if self.use_tls:
                server.starttls()

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.sendmail(self.from_email, recipients, msg.as_string())


class SlackNotifier(NotificationChannel):
    """
    Slack notification channel using webhooks.

    Supports:
    - Rich message formatting
    - Attachments
    - Custom colors
    - Mentions
    """

    def __init__(
        self,
        webhook_url: str,
        channel: Optional[str] = None,
        username: str = "NBA Simulator",
        icon_emoji: str = ":basketball:",
        config: Optional[NotificationConfig] = None,
    ):
        """
        Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL
            channel: Optional channel override
            username: Bot username
            icon_emoji: Bot icon emoji
            config: Notification configuration
        """
        super().__init__("slack", config)

        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji

    def _send_notification(self, subject: str, message: str, **kwargs):
        """Send Slack notification"""
        # Build Slack message
        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "text": subject,
        }

        # Add channel if specified
        if self.channel:
            payload["channel"] = self.channel

        # Check for color (severity-based)
        color = kwargs.get("color", "#36a64f")  # Default green

        # Create attachment with message
        attachment = {
            "color": color,
            "text": message,
            "ts": int(datetime.now(timezone.utc).timestamp()),
        }

        # Add fields if provided
        fields = kwargs.get("fields", [])
        if fields:
            attachment["fields"] = fields

        payload["attachments"] = [attachment]

        # Send to Slack
        response = requests.post(
            self.webhook_url, json=payload, timeout=self.config.timeout_seconds
        )

        response.raise_for_status()


class WebhookNotifier(NotificationChannel):
    """
    Generic webhook notification channel.

    Supports:
    - POST/PUT/PATCH requests
    - Custom headers
    - JSON payload
    - Authentication
    """

    def __init__(
        self,
        webhook_url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None,
        config: Optional[NotificationConfig] = None,
    ):
        """
        Initialize webhook notifier.

        Args:
            webhook_url: Webhook URL
            method: HTTP method (POST, PUT, PATCH)
            headers: Custom headers
            auth_token: Optional bearer token
            config: Notification configuration
        """
        super().__init__("webhook", config)

        self.webhook_url = webhook_url
        self.method = method.upper()
        self.headers = headers or {}

        # Add auth token if provided
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

        # Ensure Content-Type is set
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

    def _send_notification(self, subject: str, message: str, **kwargs):
        """Send webhook notification"""
        # Build payload
        payload = {
            "subject": subject,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add any additional data
        additional_data = kwargs.get("data", {})
        payload.update(additional_data)

        # Send webhook
        response = requests.request(
            method=self.method,
            url=self.webhook_url,
            headers=self.headers,
            json=payload,
            timeout=self.config.timeout_seconds,
        )

        response.raise_for_status()


class ConsoleNotifier(NotificationChannel):
    """
    Console notification channel (for testing/development).

    Prints notifications to console with formatting.
    """

    def __init__(self, config: Optional[NotificationConfig] = None):
        """Initialize console notifier"""
        super().__init__("console", config)

    def _send_notification(self, subject: str, message: str, **kwargs):
        """Print notification to console"""
        severity = kwargs.get("severity", "INFO")

        print("\n" + "=" * 60)
        print(f"🔔 NOTIFICATION [{severity}]")
        print("=" * 60)
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")

        # Print any additional fields
        for key, value in kwargs.items():
            if key not in ["severity", "data", "html", "color", "fields"]:
                print(f"{key.title()}: {value}")

        print("=" * 60 + "\n")

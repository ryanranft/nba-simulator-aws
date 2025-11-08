"""
Alert System Usage Examples

Demonstrates how to use the comprehensive alert system.

Run with:
    python -m nba_simulator.monitoring.alerts.example

Created: November 5, 2025
"""

import asyncio
import time
from pathlib import Path

from nba_simulator.monitoring.alerts import (
    AlertManager,
    AlertConfig,
    EmailNotifier,
    SlackNotifier,
    WebhookNotifier,
    NotificationConfig,
    AlertDeduplicator,
    DeduplicationConfig,
    EscalationPolicy,
    EscalationRule,
    EscalationLevel,
    ResolutionStatus,
)


def basic_alert_example():
    """Basic alert sending example"""
    print("=" * 60)
    print("BASIC ALERT EXAMPLE")
    print("=" * 60)

    # Create alert manager with default config
    manager = AlertManager()

    # Send simple alert
    result = manager.send_alert(
        alert_type="data_quality_issue",
        severity="high",
        message="JSON quality dropped to 85% (threshold: 95%)",
    )

    print(f"\n✅ Alert sent!")
    print(f"   Alert ID: {result['alert_id']}")
    print(f"   Success: {result['success']}")
    print(f"   Suppressed: {result['suppressed']}")

    return manager


def multi_channel_example():
    """Multi-channel notification example"""
    print("\n" + "=" * 60)
    print("MULTI-CHANNEL NOTIFICATION EXAMPLE")
    print("=" * 60)

    # Create manager
    config = AlertConfig(
        enabled=True,
        default_channels={"console", "slack", "email"},
        enable_deduplication=True,
    )
    manager = AlertManager(config)

    # Add Slack channel (example - would need real webhook)
    slack = SlackNotifier(
        webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        channel="#nba-alerts",
        username="NBA Simulator",
        icon_emoji=":basketball:",
    )
    manager.add_channel("slack", slack)

    # Add email channel (example - would need real SMTP)
    email = EmailNotifier(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        from_email="nba-simulator@example.com",
        to_emails=["admin@example.com"],
        smtp_username="your_email@gmail.com",
        smtp_password="your_app_password",  # pragma: allowlist secret
        use_tls=True,
    )
    manager.add_channel("email", email)

    # Add webhook channel
    webhook = WebhookNotifier(
        webhook_url="https://api.example.com/alerts",
        method="POST",
        auth_token="your_token_here",
    )
    manager.add_channel("webhook", webhook)

    print(f"\n✅ Configured {len(manager.channels)} channels:")
    for name in manager.channels.keys():
        print(f"   - {name}")

    # Send alert through all channels
    result = manager.send_alert(
        alert_type="file_count_anomaly",
        severity="critical",
        message="Schedule files decreased by 25% (500 files missing)",
        channels={"console", "slack", "email", "webhook"},
    )

    print(f"\n✅ Multi-channel alert sent!")
    print(f"   Alert ID: {result['alert_id']}")
    print(f"   Channels attempted: {len(result.get('channels', []))}")

    return manager


def deduplication_example():
    """Alert deduplication example"""
    print("\n" + "=" * 60)
    print("DEDUPLICATION EXAMPLE")
    print("=" * 60)

    # Configure with aggressive deduplication
    dedup_config = DeduplicationConfig(
        enabled=True, window_minutes=30, max_suppressed=5
    )

    config = AlertConfig(enable_deduplication=True, deduplication_config=dedup_config)

    manager = AlertManager(config)

    # Send same alert multiple times
    print("\n📊 Sending same alert 10 times...")

    for i in range(10):
        result = manager.send_alert(
            alert_type="database_slow",
            severity="medium",
            message="Database query taking >5 seconds",
        )

        status = "SUPPRESSED" if result["suppressed"] else "SENT"
        print(f"   Alert {i+1}: {status} (ID: {result['alert_id']})")

        time.sleep(0.1)  # Small delay

    # Get statistics
    stats = manager.deduplicator.get_suppression_stats()
    print(f"\n📈 Deduplication Statistics:")
    print(f"   Total alerts: {stats['total_alerts']}")
    print(f"   Suppressed: {stats['suppressed_alerts']}")
    print(f"   Sent: {stats['sent_alerts']}")
    print(f"   Suppression rate: {stats['suppression_rate']:.1f}%")

    return manager


def escalation_example():
    """Alert escalation example"""
    print("\n" + "=" * 60)
    print("ESCALATION EXAMPLE")
    print("=" * 60)

    # Create custom escalation policy
    policy = EscalationPolicy("custom_policy")

    # Add escalation rules
    policy.add_rule(
        EscalationRule(
            severity_threshold="high",
            time_threshold_minutes=1,  # Escalate after 1 minute for demo
            target_level=EscalationLevel.LEVEL_2,
            notification_channels={"console", "email"},
        )
    )

    policy.add_rule(
        EscalationRule(
            severity_threshold="critical",
            time_threshold_minutes=2,  # Escalate after 2 minutes
            target_level=EscalationLevel.LEVEL_3,
            notification_channels={"console", "email", "slack"},
            repeat_interval_minutes=1,  # Repeat every minute
        )
    )

    # Create manager with escalation
    config = AlertConfig(enable_escalation=True)
    manager = AlertManager(config)
    manager.set_escalation_policy(policy)

    print(f"\n✅ Configured escalation policy:")
    print(f"   Policy: {policy.policy_name}")
    print(f"   Rules: {len([r for rules in policy.rules.values() for r in rules])}")

    # Send high-severity alert
    result = manager.send_alert(
        alert_type="system_critical",
        severity="high",
        message="System experiencing critical errors",
    )

    print(f"\n🚨 Critical alert sent:")
    print(f"   Alert ID: {result['alert_id']}")

    # Simulate checking for escalations (would normally be scheduled)
    print(f"\n⏰ Simulating escalation checks...")
    for i in range(3):
        time.sleep(1)
        print(f"   Check {i+1}...")
        manager.check_escalations()

    # Get escalation statistics
    esc_stats = manager.escalation_policy.get_statistics()
    print(f"\n📈 Escalation Statistics:")
    print(f"   Active alerts: {esc_stats['active_alerts']}")
    print(f"   Total escalations: {esc_stats['total_escalations']}")

    return manager


def resolution_tracking_example():
    """Alert resolution tracking example"""
    print("\n" + "=" * 60)
    print("RESOLUTION TRACKING EXAMPLE")
    print("=" * 60)

    manager = AlertManager()

    # Send alert
    result = manager.send_alert(
        alert_type="data_sync_failed",
        severity="high",
        message="Data synchronization failed for ESPN scraper",
    )

    alert_id = result["alert_id"]
    print(f"\n🚨 Alert created: {alert_id}")

    # Simulate some time passing
    time.sleep(1)

    # Resolve alert
    manager.resolve_alert(
        alert_id=alert_id,
        resolved_by="john_doe",
        status=ResolutionStatus.RESOLVED,
        notes="Restarted scraper, sync successful",
    )

    print(f"✅ Alert resolved: {alert_id}")

    # Get alert history
    alert = manager.history.get_alert(alert_id)
    if alert:
        print(f"\n📊 Alert Details:")
        print(f"   Type: {alert.alert_type}")
        print(f"   Severity: {alert.severity}")
        print(f"   Created: {alert.created_at}")
        print(f"   Resolved: {alert.resolved_at}")
        print(f"   Resolution time: {alert.resolution_time_minutes:.2f} minutes")
        print(f"   Notifications: {alert.notifications_sent}")

    return manager


def comprehensive_example():
    """Comprehensive alert system workflow"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE ALERT SYSTEM WORKFLOW")
    print("=" * 60)

    # Configure full system
    config = AlertConfig(
        enabled=True,
        default_channels={"console"},
        enable_deduplication=True,
        enable_escalation=True,
        deduplication_config=DeduplicationConfig(window_minutes=60),
    )

    manager = AlertManager(config)

    print("\n1️⃣  Sending multiple alerts...")

    # Send various alerts
    alerts = [
        ("json_quality_low", "medium", "JSON quality at 92%"),
        ("file_count_drop", "high", "File count decreased 15%"),
        ("database_slow", "low", "Database response time elevated"),
        ("scraper_error", "critical", "ESPN scraper failed to start"),
    ]

    alert_ids = []
    for alert_type, severity, message in alerts:
        result = manager.send_alert(
            alert_type=alert_type, severity=severity, message=message
        )
        alert_ids.append(result["alert_id"])
        print(f"   ✅ {severity.upper()}: {alert_type}")

    print(f"\n2️⃣  Getting active alerts...")
    active = manager.get_active_alerts()
    print(f"   Active alerts: {len(active)}")

    print(f"\n3️⃣  Checking escalations...")
    manager.check_escalations()

    print(f"\n4️⃣  Resolving some alerts...")
    for alert_id in alert_ids[:2]:  # Resolve first 2
        manager.resolve_alert(alert_id, resolved_by="automated_system")
        print(f"   ✅ Resolved: {alert_id}")

    print(f"\n5️⃣  Getting comprehensive statistics...")
    stats = manager.get_statistics()

    print(f"\n📊 System Statistics:")
    print(f"   Manager enabled: {stats['manager']['enabled']}")
    print(f"   Channels: {stats['manager']['channels']}")

    if "history" in stats:
        print(f"\n   📈 History (24h):")
        print(f"      Total: {stats['history']['total_alerts']}")
        print(f"      Active: {stats['history']['active_alerts']}")
        print(f"      Resolved: {stats['history']['resolved_alerts']}")
        print(
            f"      Avg resolution: {stats['history']['avg_resolution_time_minutes']:.2f}min"
        )

    if "deduplication" in stats:
        print(f"\n   🔄 Deduplication:")
        print(
            f"      Suppression rate: {stats['deduplication']['suppression_rate']:.1f}%"
        )
        print(
            f"      Active fingerprints: {stats['deduplication']['active_fingerprints']}"
        )

    return manager


def main():
    """Main execution"""
    print("\n🚀 NBA ALERT SYSTEM EXAMPLES\n")

    try:
        # Run examples
        basic_alert_example()
        multi_channel_example()
        deduplication_example()
        escalation_example()
        resolution_tracking_example()
        comprehensive_example()

        print("\n" + "=" * 60)
        print("🎉 ALL EXAMPLES COMPLETE!")
        print("=" * 60)
        print("\n✅ Alert system is ready for production use!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

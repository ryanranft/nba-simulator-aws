"""
Quality Monitoring Usage Example

Demonstrates how to use the quality monitoring system.

Run with:
    python -m nba_simulator.monitoring.quality.example

Created: November 5, 2025
"""

import asyncio
from pathlib import Path

from nba_simulator.monitoring import (
    QualityMonitor,
    DataQualityChecker,
    DataQualityConfig,
    QualityMetricsTracker,
    QualityThreshold,
    QualityReportGenerator,
    ReportFormat,
)


async def basic_quality_check():
    """Basic quality check example"""
    print("=" * 60)
    print("BASIC QUALITY CHECK EXAMPLE")
    print("=" * 60)

    # Create quality monitor
    monitor = QualityMonitor("nba_data_quality")

    # Configure quality checker
    config = DataQualityConfig(
        s3_bucket="nba-sim-raw-data-lake",
        file_count_threshold=10.0,  # 10% change alert
        json_quality_threshold=95.0,  # 95% valid JSON
        freshness_days_threshold=3,  # 3 days max staleness
        sample_size=50,
        enable_s3_checks=True,
        enable_db_checks=True,
    )

    # Create checker
    checker = DataQualityChecker(monitor, config)

    # Run check
    print("\n📊 Running quality checks...")
    check_result = checker.run_check()

    # Print results
    print(f"\n✅ Check Complete!")
    print(f"   Status: {check_result.status.value}")
    print(f"   Passed: {check_result.passed}")
    print(f"   Warnings: {check_result.warnings}")
    print(f"   Failed: {check_result.failed}")
    print(f"   Duration: {check_result.duration_seconds:.2f}s")

    # Show metrics
    print(f"\n📈 Metrics Collected: {len(check_result.metrics)}")
    for metric in check_result.metrics[:5]:  # Show first 5
        print(
            f"   - {metric.metric_name}: {metric.metric_value:.2f} [{metric.status.value}]"
        )

    # Show active alerts
    active_alerts = monitor.get_active_alerts()
    if active_alerts:
        print(f"\n🚨 Active Alerts: {len(active_alerts)}")
        for alert in active_alerts[:3]:  # Show first 3
            print(f"   - [{alert.severity.value}] {alert.message}")
    else:
        print("\n✅ No active alerts")

    return monitor


async def metrics_tracking_example():
    """Metrics tracking example"""
    print("\n" + "=" * 60)
    print("METRICS TRACKING EXAMPLE")
    print("=" * 60)

    # Create monitor and tracker
    monitor = QualityMonitor("nba_metrics")
    tracker = QualityMetricsTracker()

    # Register thresholds
    tracker.register_threshold(
        QualityThreshold(
            metric_name="json_quality_percent",
            warning_threshold=90.0,
            critical_threshold=85.0,
            comparison="lt",  # Lower is worse
        )
    )

    tracker.register_threshold(
        QualityThreshold(
            metric_name="data_freshness_days",
            warning_threshold=3.0,
            critical_threshold=7.0,
            comparison="gt",  # Higher is worse
        )
    )

    print("\n✅ Registered quality thresholds")

    # Get metric history (if available)
    history = tracker.get_metric_history("json_quality_percent", hours=24)
    if history:
        print(f"\n📊 JSON Quality History (last 24h): {len(history)} samples")

        # Calculate trend
        trend = tracker.calculate_trend("json_quality_percent", hours=24)
        if trend:
            print(f"   Current: {trend.current_value:.2f}")
            print(f"   Previous: {trend.previous_value:.2f}")
            print(f"   Change: {trend.percent_change:+.1f}%")
            print(f"   Trend: {trend.trend_direction}")
            print(f"   Improving: {trend.is_improving}")

        # Get summary statistics
        stats = tracker.get_summary_statistics("json_quality_percent", hours=24)
        if stats:
            print(f"\n   Statistics:")
            print(f"   - Min: {stats.get('min', 0):.2f}")
            print(f"   - Max: {stats.get('max', 0):.2f}")
            print(f"   - Mean: {stats.get('mean', 0):.2f}")
            print(f"   - Median: {stats.get('median', 0):.2f}")
    else:
        print("\n⚠️  No historical data available yet")

    return tracker


async def report_generation_example(monitor):
    """Report generation example"""
    print("\n" + "=" * 60)
    print("REPORT GENERATION EXAMPLE")
    print("=" * 60)

    # Create report generator
    report_gen = QualityReportGenerator(monitor)

    # Generate markdown report
    print("\n📝 Generating Markdown report...")
    markdown_report = report_gen.generate_daily_report(ReportFormat.MARKDOWN)
    print(f"   Report size: {len(markdown_report)} characters")

    # Preview first 500 characters
    print("\n   Preview:")
    print("-" * 60)
    print(markdown_report[:500])
    print("-" * 60)

    # Generate JSON report
    print("\n📄 Generating JSON report...")
    json_report = report_gen.generate_daily_report(ReportFormat.JSON)
    print(f"   Report size: {len(json_report)} characters")

    # Save reports
    output_dir = Path("/tmp/quality_reports")
    output_dir.mkdir(exist_ok=True)

    print(f"\n💾 Saving reports to {output_dir}...")

    md_path = report_gen.save_report(
        markdown_report, output_dir, format=ReportFormat.MARKDOWN
    )
    print(f"   ✅ Markdown report: {md_path}")

    json_path = report_gen.save_report(
        json_report, output_dir, format=ReportFormat.JSON
    )
    print(f"   ✅ JSON report: {json_path}")

    return report_gen


async def comprehensive_monitoring_example():
    """Comprehensive monitoring workflow"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE MONITORING WORKFLOW")
    print("=" * 60)

    # Initialize all components
    monitor = QualityMonitor("comprehensive_monitor")
    tracker = QualityMetricsTracker()
    config = DataQualityConfig()
    checker = DataQualityChecker(monitor, config)

    print("\n1️⃣  Running quality checks...")
    check_result = checker.run_check()

    print("\n2️⃣  Analyzing metrics...")
    summary = monitor.get_summary()
    print(f"   Total checks: {summary['total_checks']}")
    print(f"   Total metrics: {summary['total_metrics']}")
    print(f"   Active alerts: {summary['active_alerts']}")

    print("\n3️⃣  Generating reports...")
    report_gen = QualityReportGenerator(monitor, tracker)
    report = report_gen.generate_daily_report()

    print("\n4️⃣  Saving results...")
    output_dir = Path("/tmp/quality_monitoring")
    report_path = report_gen.save_report(report, output_dir)
    print(f"   Report saved: {report_path}")

    print("\n✅ Comprehensive monitoring complete!")

    return {
        "monitor": monitor,
        "tracker": tracker,
        "checker": checker,
        "report_gen": report_gen,
        "check_result": check_result,
    }


async def main():
    """Main execution"""
    print("\n🚀 NBA QUALITY MONITORING EXAMPLES\n")

    try:
        # Run examples
        monitor = await basic_quality_check()
        await metrics_tracking_example()
        await report_generation_example(monitor)
        await comprehensive_monitoring_example()

        print("\n" + "=" * 60)
        print("🎉 ALL EXAMPLES COMPLETE!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

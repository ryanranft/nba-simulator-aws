#!/usr/bin/env python3
"""
Quality Monitoring Verification Script

Quick test to verify all quality monitoring components work correctly.

Run with:
    python verify_quality_monitoring.py

Created: November 5, 2025
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_imports():
    """Verify all imports work"""
    print("=" * 60)
    print("VERIFYING QUALITY MONITORING IMPORTS")
    print("=" * 60)

    try:
        from nba_simulator.monitoring import (
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

        print("\n✅ All imports successful!")
        print("\nAvailable Components:")
        print(f"  - QualityMonitor: {QualityMonitor}")
        print(f"  - QualityStatus: {QualityStatus}")
        print(f"  - QualityMetric: {QualityMetric}")
        print(f"  - DataQualityChecker: {DataQualityChecker}")
        print(f"  - DataQualityConfig: {DataQualityConfig}")
        print(f"  - QualityMetricsTracker: {QualityMetricsTracker}")
        print(f"  - QualityThreshold: {QualityThreshold}")
        print(f"  - QualityReportGenerator: {QualityReportGenerator}")
        print(f"  - ReportFormat: {ReportFormat}")

        return True

    except Exception as e:
        print(f"\n❌ Import failed: {str(e)}")
        return False


def verify_basic_usage():
    """Verify basic usage works"""
    print("\n" + "=" * 60)
    print("VERIFYING BASIC USAGE")
    print("=" * 60)

    try:
        from nba_simulator.monitoring import (
            QualityMonitor,
            QualityMetric,
            QualityStatus,
            QualitySeverity,
            DataQualityConfig,
        )

        # Create monitor
        monitor = QualityMonitor("test_monitor")
        print("\n✅ QualityMonitor created")

        # Create a test metric
        metric = QualityMetric(
            metric_name="test_metric",
            metric_value=95.5,
            metric_type="test",
            status=QualityStatus.PASS,
            severity=QualitySeverity.INFO,
        )
        print("✅ QualityMetric created")

        # Log metric
        monitor.log_metric(metric)
        print("✅ Metric logged")

        # Create alert
        alert = monitor.create_alert(
            alert_type="test_alert",
            severity=QualitySeverity.LOW,
            message="Test alert message",
            metric=metric,
        )
        print("✅ Alert created")

        # Get summary
        summary = monitor.get_summary()
        print(f"\n✅ Monitor Summary:")
        print(f"   - Total metrics: {summary['total_metrics']}")
        print(f"   - Active alerts: {summary['active_alerts']}")

        # Create config
        config = DataQualityConfig(
            s3_bucket="test-bucket",
            file_count_threshold=10.0,
            json_quality_threshold=95.0,
        )
        print("\n✅ DataQualityConfig created")
        print(f"   - S3 Bucket: {config.s3_bucket}")
        print(f"   - File Count Threshold: {config.file_count_threshold}%")
        print(f"   - JSON Quality Threshold: {config.json_quality_threshold}%")

        return True

    except Exception as e:
        print(f"\n❌ Usage test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def verify_report_generation():
    """Verify report generation works"""
    print("\n" + "=" * 60)
    print("VERIFYING REPORT GENERATION")
    print("=" * 60)

    try:
        from nba_simulator.monitoring import (
            QualityMonitor,
            QualityMetric,
            QualityStatus,
            QualitySeverity,
            QualityReportGenerator,
            ReportFormat,
        )

        # Create monitor with some data
        monitor = QualityMonitor("report_test")

        for i in range(5):
            metric = QualityMetric(
                metric_name=f"test_metric_{i}",
                metric_value=90.0 + i,
                metric_type="test",
                status=QualityStatus.PASS if i < 4 else QualityStatus.WARNING,
                severity=QualitySeverity.INFO,
            )
            monitor.log_metric(metric)

        print(f"\n✅ Created monitor with {len(monitor.metrics)} metrics")

        # Generate report
        report_gen = QualityReportGenerator(monitor)
        print("✅ QualityReportGenerator created")

        # Generate markdown report
        report = report_gen.generate_daily_report(ReportFormat.MARKDOWN)
        print(f"\n✅ Markdown report generated ({len(report)} characters)")

        # Show preview
        print("\n📄 Report Preview (first 300 chars):")
        print("-" * 60)
        print(report[:300])
        print("-" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Report generation failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main verification"""
    print("\n🚀 QUALITY MONITORING VERIFICATION SCRIPT\n")

    results = []

    # Run verifications
    results.append(("Imports", verify_imports()))
    results.append(("Basic Usage", verify_basic_usage()))
    results.append(("Report Generation", verify_report_generation()))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("\n✅ Quality monitoring system is ready to use!")
        return 0
    else:
        print("\n⚠️  Some verifications failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

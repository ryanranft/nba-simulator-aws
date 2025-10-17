#!/usr/bin/env python3
"""
Phase 1.0: Ongoing Data Quality Monitoring System

This script provides continuous monitoring of data quality:
- Daily quality checks
- Alert system for quality issues
- Trend analysis
- Automated reporting

Created: October 13, 2025
Phase: 1.0 (Data Quality Checks)
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import json
import boto3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import sqlite3
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class DataQualityMonitor:
    """Ongoing data quality monitoring system"""

    def __init__(
        self,
        s3_bucket: str = "nba-sim-raw-data-lake",
        db_path: str = "/tmp/data_quality_monitor.db",
    ):
        self.s3_bucket = s3_bucket
        self.s3_client = boto3.client("s3")
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        """Setup SQLite database for monitoring data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create monitoring tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quality_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                check_type TEXT NOT NULL,
                data_type TEXT,
                metric_name TEXT,
                metric_value REAL,
                status TEXT,
                details TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quality_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                severity TEXT,
                message TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_date TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_type TEXT NOT NULL,
                file_count INTEGER,
                total_size_gb REAL
            )
        """
        )

        conn.commit()
        conn.close()

    def log_quality_check(
        self,
        check_type: str,
        data_type: str,
        metric_name: str,
        metric_value: float,
        status: str,
        details: str = "",
    ):
        """Log a quality check result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO quality_checks
            (check_type, data_type, metric_name, metric_value, status, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (check_type, data_type, metric_name, metric_value, status, details),
        )

        conn.commit()
        conn.close()

    def log_alert(self, alert_type: str, severity: str, message: str):
        """Log a quality alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO quality_alerts (alert_type, severity, message)
            VALUES (?, ?, ?)
        """,
            (alert_type, severity, message),
        )

        conn.commit()
        conn.close()

        # Print alert
        print(f"🚨 ALERT [{severity}]: {message}")

    def log_file_counts(self, data_type: str, file_count: int, total_size_gb: float):
        """Log file count metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO file_counts (data_type, file_count, total_size_gb)
            VALUES (?, ?, ?)
        """,
            (data_type, file_count, total_size_gb),
        )

        conn.commit()
        conn.close()

    def check_file_counts(self) -> Dict[str, Any]:
        """Check file counts and detect anomalies"""
        print("📊 Checking file counts...")

        file_counts = {}
        total_files = 0

        # Get current file counts
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.s3_bucket)

        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    key = obj["Key"]
                    size = obj["Size"]

                    # Extract data type from path
                    if "/" in key:
                        data_type = key.split("/")[0]
                    else:
                        data_type = "root"

                    if data_type not in file_counts:
                        file_counts[data_type] = {"count": 0, "size": 0}

                    file_counts[data_type]["count"] += 1
                    file_counts[data_type]["size"] += size
                    total_files += 1

        # Convert to GB and log
        for data_type, counts in file_counts.items():
            size_gb = counts["size"] / (1024 * 1024 * 1024)
            self.log_file_counts(data_type, counts["count"], size_gb)

            # Check for anomalies (significant changes)
            self.check_file_count_anomaly(data_type, counts["count"])

        print(f"✅ Total files: {total_files:,}")
        return file_counts

    def check_file_count_anomaly(self, data_type: str, current_count: int):
        """Check for file count anomalies"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get previous count
        cursor.execute(
            """
            SELECT file_count FROM file_counts
            WHERE data_type = ?
            ORDER BY check_date DESC
            LIMIT 1 OFFSET 1
        """,
            (data_type,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            previous_count = result[0]
            change_percent = ((current_count - previous_count) / previous_count) * 100

            # Alert on significant changes
            if abs(change_percent) > 10:  # 10% change threshold
                if change_percent > 0:
                    self.log_alert(
                        "file_count_increase",
                        "warning",
                        f"{data_type} files increased by {change_percent:.1f}% ({current_count - previous_count} files)",
                    )
                else:
                    self.log_alert(
                        "file_count_decrease",
                        "critical",
                        f"{data_type} files decreased by {abs(change_percent):.1f}% ({previous_count - current_count} files)",
                    )

    def check_json_quality(self, sample_size: int = 50) -> Dict[str, Any]:
        """Quick JSON quality check"""
        print("🔍 Checking JSON quality...")

        # Get random sample
        all_files = []
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.s3_bucket)

        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    if obj["Key"].endswith(".json"):
                        all_files.append(obj["Key"])

        import random

        sample_files = random.sample(all_files, min(sample_size, len(all_files)))

        valid_count = 0
        invalid_count = 0
        empty_count = 0

        for file_path in sample_files:
            try:
                response = self.s3_client.get_object(
                    Bucket=self.s3_bucket, Key=file_path
                )
                content = response["Body"].read()

                if len(content) == 0:
                    empty_count += 1
                    continue

                json.loads(content.decode("utf-8"))
                valid_count += 1

            except Exception:
                invalid_count += 1

        total_sampled = len(sample_files)
        valid_percent = (valid_count / total_sampled) * 100

        # Log results
        self.log_quality_check(
            "json_validation",
            "all",
            "valid_percent",
            valid_percent,
            "pass" if valid_percent > 95 else "fail",
            f"Valid: {valid_count}, Invalid: {invalid_count}, Empty: {empty_count}",
        )

        # Alert on quality issues
        if valid_percent < 95:
            self.log_alert(
                "json_quality_degradation",
                "critical",
                f"JSON quality dropped to {valid_percent:.1f}% (threshold: 95%)",
            )

        print(f"✅ JSON quality: {valid_percent:.1f}% valid")
        return {
            "valid_percent": valid_percent,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
        }

    def check_recent_data_freshness(self) -> Dict[str, Any]:
        """Check if recent data is being added"""
        print("📅 Checking data freshness...")

        # Check schedule files for recent dates
        recent_files = []
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.s3_bucket, Prefix="schedule/")

        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    if obj["Key"].endswith(".json"):
                        # Extract date from filename
                        filename = Path(obj["Key"]).stem
                        try:
                            if len(filename) == 8 and filename.isdigit():
                                file_date = datetime.strptime(filename, "%Y%m%d")
                                if file_date >= datetime.now() - timedelta(days=7):
                                    recent_files.append(file_date)
                        except ValueError:
                            continue

        if recent_files:
            latest_date = max(recent_files)
            days_old = (datetime.now() - latest_date).days

            self.log_quality_check(
                "data_freshness",
                "schedule",
                "days_since_latest",
                days_old,
                "pass" if days_old <= 3 else "warning",
                f"Latest data: {latest_date.strftime('%Y-%m-%d')}",
            )

            if days_old > 3:
                self.log_alert(
                    "stale_data",
                    "warning",
                    f"Latest schedule data is {days_old} days old",
                )

            print(
                f"✅ Latest data: {latest_date.strftime('%Y-%m-%d')} ({days_old} days ago)"
            )
        else:
            self.log_alert(
                "no_recent_data", "critical", "No recent schedule data found"
            )
            print("❌ No recent schedule data found")

        return {
            "latest_date": max(recent_files) if recent_files else None,
            "recent_files_count": len(recent_files),
        }

    def generate_daily_report(self) -> str:
        """Generate daily quality report"""
        print("📝 Generating daily report...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get today's metrics
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            """
            SELECT check_type, data_type, metric_name, metric_value, status
            FROM quality_checks
            WHERE DATE(check_date) = ?
            ORDER BY check_date DESC
        """,
            (today,),
        )

        today_checks = cursor.fetchall()

        cursor.execute(
            """
            SELECT alert_type, severity, message, resolved
            FROM quality_alerts
            WHERE DATE(alert_date) = ?
            ORDER BY alert_date DESC
        """,
            (today,),
        )

        today_alerts = cursor.fetchall()

        conn.close()

        # Generate report
        report = f"""
# Daily Data Quality Report
**Date:** {today}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Quality Checks Today
"""

        for check in today_checks:
            report += f"- **{check[0]}** ({check[1]}): {check[2]} = {check[3]:.2f} [{check[4]}]\n"

        if today_alerts:
            report += f"""
## Alerts Today ({len(today_alerts)})
"""
            for alert in today_alerts:
                status = "RESOLVED" if alert[3] else "ACTIVE"
                report += f"- **{alert[0]}** [{alert[1]}] {status}: {alert[2]}\n"
        else:
            report += "\n## Alerts Today\n- No alerts\n"

        report += f"""
## Summary
- Quality checks: {len(today_checks)}
- Active alerts: {len([a for a in today_alerts if not a[3]])}
- Resolved alerts: {len([a for a in today_alerts if a[3]])}
"""

        return report

    def run_daily_check(self):
        """Run daily quality check"""
        print(
            f"🔄 Running daily quality check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("=" * 60)

        # Run all checks
        self.check_file_counts()
        print()

        self.check_json_quality()
        print()

        self.check_recent_data_freshness()
        print()

        # Generate report
        report = self.generate_daily_report()

        # Save report
        report_path = Path(
            f'/tmp/daily_quality_report_{datetime.now().strftime("%Y%m%d")}.md'
        )
        with open(report_path, "w") as f:
            f.write(report)

        print(f"✅ Daily report saved to: {report_path}")
        print("🎉 Daily quality check complete!")

    def start_monitoring(self):
        """Start continuous monitoring"""
        print("🚀 Starting data quality monitoring...")
        print("   - Running checks every hour")
        print("   - Press Ctrl+C to stop")

        # Run initial check
        self.run_daily_check()

        # Keep running with hourly checks
        try:
            while True:
                time.sleep(3600)  # Wait 1 hour
                self.run_daily_check()
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped")


def main():
    """Main execution function"""
    monitor = DataQualityMonitor()

    # Run single check
    monitor.run_daily_check()

    # Uncomment to start continuous monitoring
    # monitor.start_monitoring()


if __name__ == "__main__":
    main()

# 🎯 Quality Monitoring Quick Reference

## 🚀 Quick Start (30 seconds)

```python
from nba_simulator.monitoring import (
    QualityMonitor,
    DataQualityChecker,
    QualityReportGenerator
)

# Create and run
monitor = QualityMonitor("nba_data")
checker = DataQualityChecker(monitor)
result = checker.run_check()

# Generate report
report = QualityReportGenerator(monitor).generate_daily_report()
print(report)
```

## 📦 What's Included

```
quality/
├── base.py           - Core framework (398 lines)
├── data_quality.py   - Quality checks (640 lines)
├── metrics.py        - Metrics tracking (280 lines)
├── reports.py        - Report generation (415 lines)
└── example.py        - Usage examples (205 lines)
```

## ✨ Key Features

### Quality Checks
- ✅ S3 file count monitoring + anomaly detection
- ✅ JSON validation (sampling-based)
- ✅ Data freshness checks
- ✅ Database NULL detection

### Metrics Tracking
- ✅ Historical storage (PostgreSQL)
- ✅ Trend calculation (24h windows)
- ✅ Anomaly detection (statistical)
- ✅ Summary statistics

### Reporting
- ✅ Markdown reports with emoji
- ✅ JSON export
- ✅ Plain text output
- ✅ Auto-generated recommendations

### Alert System
- ✅ Alert creation with severity
- ✅ Resolution tracking
- ✅ Active alert queries
- ✅ Alert history

## 🔧 Configuration

```python
from nba_simulator.monitoring import DataQualityConfig

config = DataQualityConfig(
    s3_bucket="nba-sim-raw-data-lake",
    file_count_threshold=10.0,      # % change alert
    json_quality_threshold=95.0,     # % valid JSON
    freshness_days_threshold=3,      # days staleness
    sample_size=50,                  # files to check
    enable_s3_checks=True,
    enable_db_checks=True
)
```

## 📊 Status Levels

### QualityStatus
- `PASS` - ✅ All checks passed
- `WARNING` - ⚠️ Minor issues
- `FAIL` - ❌ Quality degraded
- `ERROR` - 🔴 Check failed
- `UNKNOWN` - ❓ Status unclear

### QualitySeverity
- `INFO` - ℹ️ Informational
- `LOW` - 🔵 Minor issue
- `MEDIUM` - 🟡 Moderate issue
- `HIGH` - 🟠 Serious issue
- `CRITICAL` - 🔴 Urgent issue

## 🧪 Verification

```bash
# Run verification script
python verify_quality_monitoring.py

# Expected output:
# ✅ PASSED: Imports
# ✅ PASSED: Basic Usage  
# ✅ PASSED: Report Generation
# 🎉 ALL VERIFICATIONS PASSED!
```

## 📖 Examples

### Basic Check
```python
monitor = QualityMonitor("test")
checker = DataQualityChecker(monitor)
result = checker.run_check()
print(f"Status: {result.status.value}")
print(f"Passed: {result.passed}, Failed: {result.failed}")
```

### With Thresholds
```python
from nba_simulator.monitoring import QualityThreshold, QualityMetricsTracker

tracker = QualityMetricsTracker()
tracker.register_threshold(
    QualityThreshold(
        metric_name="json_quality_percent",
        warning_threshold=90.0,
        critical_threshold=85.0,
        comparison="lt"
    )
)
```

### Generate Reports
```python
from pathlib import Path
from nba_simulator.monitoring import ReportFormat

report_gen = QualityReportGenerator(monitor)
report = report_gen.generate_daily_report(ReportFormat.MARKDOWN)

output_dir = Path("/tmp/reports")
path = report_gen.save_report(report, output_dir)
print(f"Report saved: {path}")
```

## 🎯 Common Tasks

### Check Alert Status
```python
active_alerts = monitor.get_active_alerts()
critical = [a for a in active_alerts if a.severity == QualitySeverity.CRITICAL]
print(f"Critical alerts: {len(critical)}")
```

### Analyze Trends
```python
trend = tracker.calculate_trend("json_quality_percent", hours=24)
if trend:
    print(f"Change: {trend.percent_change:+.1f}%")
    print(f"Improving: {trend.is_improving}")
```

### Get Statistics
```python
stats = tracker.get_summary_statistics("json_quality_percent", hours=24)
print(f"Mean: {stats['mean']:.2f}")
print(f"Current: {stats['current']:.2f}")
```

## 📚 Documentation

- **Full Summary:** `QUALITY_MONITORING_COMPLETE.md`
- **Progress Log:** `PHASE_4_SESSION_2_PROGRESS_LOG.md`
- **Examples:** `nba_simulator/monitoring/quality/example.py`
- **Docstrings:** Inline in all modules

## 🔗 Integration

```python
# Integrates with:
from nba_simulator.database import get_database_connection  # PostgreSQL
from nba_simulator.utils import setup_logging              # Logging
import boto3                                                # AWS S3
```

## 📈 Metrics

- **Files:** 6
- **Lines:** 1,985
- **Classes:** 10
- **Dataclasses:** 5
- **Enums:** 3
- **Type Hints:** 100%

## ✅ Production Ready

The quality monitoring system is:
- ✅ Fully functional
- ✅ Type-safe
- ✅ Well-documented
- ✅ Tested (verification script)
- ✅ Integrated with package
- ✅ Production-ready

## 🚀 Next Steps

1. **Alert System** - Add email/Slack notifications
2. **CloudWatch** - AWS monitoring integration  
3. **Dashboard** - Real-time visualization
4. **Testing** - Comprehensive test suite

---

**Phase 4 Status:** 60% Complete (Quality Monitoring ✅)

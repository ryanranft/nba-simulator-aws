# Phase 0.0020: Monitoring & Observability

**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)

**Status:** ⏸️ PENDING
**Priority:** 🟡 IMPORTANT
**Migrated From:** Phase 6.1 (Optional Enhancements)
**Timeline:** 1-2 weeks
**Cost Impact:** +$1.50-3.00/month (CloudWatch)

---

## Overview

Establish comprehensive monitoring and observability infrastructure to track system health, performance, costs, and data quality in real-time. This transforms reactive troubleshooting into proactive system management.

**This sub-phase delivers:**
- CloudWatch metrics for all critical systems
- Custom dashboards for monitoring data collection
- Automated alarms for failures and anomalies
- Performance tracking and optimization
- Cost monitoring and budget alerts
- DIMS integration for metrics publishing

**Why this is foundational, not optional:**
- Detects ADCE failures before data gaps occur
- Prevents cost overruns ($2.71/mo baseline, $150/mo budget)
- Tracks S3 growth (172,719 files → continuous monitoring)
- Identifies performance bottlenecks early
- Enables data-driven optimization decisions

---

## Current Monitoring State

**Existing Infrastructure (from Phase 0.1-0.18):**
- DIMS (Data Inventory Management System) - `inventory/metrics.yaml`
- DIMS CLI - `scripts/monitoring/dims_cli.py verify`
- Scraper monitoring - `scripts/monitoring/monitor_scrapers_inline.sh`
- Manual validation scripts

**Gaps to Address:**
- No centralized CloudWatch dashboards
- No automated alarms for failures
- No performance profiling infrastructure
- No cost tracking automation
- Manual intervention required for anomalies

---

## Sub-Phase Components

### 1. CloudWatch Metrics Implementation

**Goal:** Real-time system health and performance metrics

**Metrics to Publish:**

#### Data Collection Metrics
```python
# scripts/monitoring/publish_collection_metrics.py
import boto3
from datetime import datetime

def publish_s3_metrics():
    """Publish S3 bucket metrics to CloudWatch"""
    cloudwatch = boto3.client('cloudwatch')
    s3 = boto3.client('s3')

    # Count objects in bucket
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket='nba-sim-raw-data-lake')

    total_objects = 0
    total_size = 0

    for page in pages:
        if 'Contents' in page:
            total_objects += len(page['Contents'])
            total_size += sum(obj['Size'] for obj in page['Contents'])

    metrics = [
        {
            'MetricName': 'S3ObjectCount',
            'Value': total_objects,
            'Unit': 'Count',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Bucket', 'Value': 'nba-sim-raw-data-lake'}
            ]
        },
        {
            'MetricName': 'S3TotalSizeGB',
            'Value': total_size / (1024**3),
            'Unit': 'Gigabytes',
            'Timestamp': datetime.utcnow(),
            'Dimensions': [
                {'Name': 'Bucket', 'Value': 'nba-sim-raw-data-lake'}
            ]
        }
    ]

    cloudwatch.put_metric_data(
        Namespace='NBA-Simulator/DataCollection',
        MetricData=metrics
    )
```

#### ADCE (Autonomous Data Collection) Metrics
```python
def publish_adce_metrics(orchestrator_stats):
    """Publish ADCE system health metrics"""
    metrics = [
        {
            'MetricName': 'ADCETasksCompleted',
            'Value': orchestrator_stats['tasks_completed'],
            'Unit': 'Count'
        },
        {
            'MetricName': 'ADCETasksFailed',
            'Value': orchestrator_stats['tasks_failed'],
            'Unit': 'Count'
        },
        {
            'MetricName': 'ADCEQueueDepth',
            'Value': orchestrator_stats['queue_depth'],
            'Unit': 'Count'
        },
        {
            'MetricName': 'ADCESuccessRate',
            'Value': orchestrator_stats['success_rate'],
            'Unit': 'Percent'
        }
    ]

    cloudwatch.put_metric_data(
        Namespace='NBA-Simulator/ADCE',
        MetricData=metrics
    )
```

#### Performance Metrics
```python
def publish_performance_metrics(operation, duration, status):
    """Publish performance metrics for operations"""
    metrics = [
        {
            'MetricName': f'{operation}Duration',
            'Value': duration,
            'Unit': 'Seconds',
            'Dimensions': [
                {'Name': 'Status', 'Value': status}
            ]
        }
    ]

    cloudwatch.put_metric_data(
        Namespace='NBA-Simulator/Performance',
        MetricData=metrics
    )
```

#### Cost Metrics
```python
def publish_cost_metrics():
    """Publish AWS cost metrics"""
    ce = boto3.client('ce')  # Cost Explorer

    # Get current month's costs
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': datetime.now().strftime('%Y-%m-01'),
            'End': datetime.now().strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    total_cost = float(response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

    metrics = [
        {
            'MetricName': 'MonthlyAWSCost',
            'Value': total_cost,
            'Unit': 'None',  # Dollars
            'Timestamp': datetime.utcnow()
        },
        {
            'MetricName': 'BudgetUtilization',
            'Value': (total_cost / 150.0) * 100,  # $150 budget
            'Unit': 'Percent'
        }
    ]

    cloudwatch.put_metric_data(
        Namespace='NBA-Simulator/Costs',
        MetricData=metrics
    )
```

### 2. CloudWatch Dashboards

**Goal:** Centralized visualization of all system metrics

**Dashboard 1: Data Collection Overview**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "NBA-Simulator/DataCollection", "S3ObjectCount" ],
          [ ".", "S3TotalSizeGB" ]
        ],
        "period": 3600,
        "stat": "Average",
        "region": "us-east-1",
        "title": "S3 Bucket Growth"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "NBA-Simulator/ADCE", "ADCETasksCompleted", { "stat": "Sum" } ],
          [ ".", "ADCETasksFailed", { "stat": "Sum" } ]
        ],
        "period": 300,
        "stat": "Sum",
        "title": "ADCE Task Execution"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "NBA-Simulator/ADCE", "ADCESuccessRate" ]
        ],
        "period": 300,
        "stat": "Average",
        "title": "ADCE Success Rate",
        "yAxis": { "left": { "min": 0, "max": 100 } }
      }
    }
  ]
}
```

**Dashboard 2: Performance & Costs**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "NBA-Simulator/Performance", "DataExtractionDuration" ],
          [ ".", "S3UploadDuration" ],
          [ ".", "ValidationDuration" ]
        ],
        "period": 300,
        "stat": "Average",
        "title": "Operation Performance"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "NBA-Simulator/Costs", "MonthlyAWSCost" ],
          [ { "expression": "150", "label": "Budget Limit", "id": "budget" } ]
        ],
        "period": 86400,
        "stat": "Maximum",
        "title": "AWS Costs vs Budget"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "NBA-Simulator/Costs", "BudgetUtilization" ]
        ],
        "period": 86400,
        "stat": "Maximum",
        "title": "Budget Utilization %",
        "yAxis": { "left": { "min": 0, "max": 100 } }
      }
    }
  ]
}
```

**Create Dashboards:**
```bash
# scripts/monitoring/create_dashboards.sh
aws cloudwatch put-dashboard \
  --dashboard-name NBA-Simulator-DataCollection \
  --dashboard-body file://dashboards/data_collection_dashboard.json

aws cloudwatch put-dashboard \
  --dashboard-name NBA-Simulator-Performance \
  --dashboard-body file://dashboards/performance_dashboard.json
```

### 3. CloudWatch Alarms

**Goal:** Automated alerts for critical issues

**Alarm 1: ADCE Failure Rate**
```python
# scripts/monitoring/create_alarms.py
import boto3

def create_adce_failure_alarm():
    """Alert when ADCE success rate drops below 95%"""
    cloudwatch = boto3.client('cloudwatch')

    cloudwatch.put_metric_alarm(
        AlarmName='ADCE-HighFailureRate',
        ComparisonOperator='LessThanThreshold',
        EvaluationPeriods=2,
        MetricName='ADCESuccessRate',
        Namespace='NBA-Simulator/ADCE',
        Period=300,
        Statistic='Average',
        Threshold=95.0,
        ActionsEnabled=True,
        AlarmDescription='ADCE success rate dropped below 95%',
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789:nba-simulator-alerts'
        ]
    )
```

**Alarm 2: Cost Budget Exceeded**
```python
def create_cost_alarm():
    """Alert when monthly costs exceed 80% of budget"""
    cloudwatch.put_metric_alarm(
        AlarmName='AWS-CostBudgetExceeded',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='BudgetUtilization',
        Namespace='NBA-Simulator/Costs',
        Period=86400,
        Statistic='Maximum',
        Threshold=80.0,
        ActionsEnabled=True,
        AlarmDescription='AWS costs exceeded 80% of $150 budget',
        AlarmActions=[
            'arn:aws:sns:us-east-1:123456789:nba-simulator-alerts'
        ]
    )
```

**Alarm 3: S3 Upload Failures**
```python
def create_upload_failure_alarm():
    """Alert when S3 uploads fail repeatedly"""
    cloudwatch.put_metric_alarm(
        AlarmName='S3-UploadFailures',
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName='S3UploadFailures',
        Namespace='NBA-Simulator/DataCollection',
        Period=300,
        Statistic='Sum',
        Threshold=5,
        ActionsEnabled=True,
        AlarmDescription='More than 5 S3 upload failures in 10 minutes'
    )
```

**Alarm 4: Data Quality Issues**
```python
def create_quality_alarm():
    """Alert when data validation fails"""
    cloudwatch.put_metric_alarm(
        AlarmName='Data-QualityIssues',
        ComparisonOperator='LessThanThreshold',
        EvaluationPeriods=1,
        MetricName='ValidationPassRate',
        Namespace='NBA-Simulator/DataQuality',
        Period=3600,
        Statistic='Average',
        Threshold=95.0,
        ActionsEnabled=True,
        AlarmDescription='Data validation pass rate below 95%'
    )
```

### 4. SNS Topic for Alerts

**Goal:** Receive notifications via email/SMS

**Setup:**
```bash
# Create SNS topic
aws sns create-topic --name nba-simulator-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789:nba-simulator-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Subscribe SMS (optional)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:123456789:nba-simulator-alerts \
  --protocol sms \
  --notification-endpoint +1234567890
```

### 5. DIMS Integration

**Goal:** Publish DIMS metrics to CloudWatch automatically

**Enhanced DIMS CLI:**
```python
# scripts/monitoring/dims_cli.py (enhancement)

def publish_dims_to_cloudwatch(metrics):
    """Publish DIMS metrics to CloudWatch"""
    cloudwatch = boto3.client('cloudwatch')

    cloudwatch_metrics = []

    for category, values in metrics.items():
        if category == 's3_storage':
            cloudwatch_metrics.append({
                'MetricName': 'DIMS_S3Objects',
                'Value': values['total_objects']['value'],
                'Unit': 'Count',
                'Dimensions': [{'Name': 'Source', 'Value': 'DIMS'}]
            })
            cloudwatch_metrics.append({
                'MetricName': 'DIMS_S3SizeGB',
                'Value': values['total_size_gb']['value'],
                'Unit': 'Gigabytes',
                'Dimensions': [{'Name': 'Source', 'Value': 'DIMS'}]
            })

        elif category == 'code_base':
            cloudwatch_metrics.append({
                'MetricName': 'DIMS_PythonFiles',
                'Value': values['python_files']['value'],
                'Unit': 'Count'
            })
            cloudwatch_metrics.append({
                'MetricName': 'DIMS_TestFiles',
                'Value': values['test_files']['value'],
                'Unit': 'Count'
            })

    cloudwatch.put_metric_data(
        Namespace='NBA-Simulator/DIMS',
        MetricData=cloudwatch_metrics
    )
```

**Cron job to auto-publish:**
```bash
# Add to crontab
0 */6 * * * cd /Users/ryanranft/nba-simulator-aws && python scripts/monitoring/dims_cli.py verify --all --publish-cloudwatch
```

### 6. Performance Profiling

**Goal:** Identify bottlenecks and optimize critical paths

**Decorator for automatic profiling:**
```python
# scripts/monitoring/profiler.py
import time
import boto3
from functools import wraps

def profile_performance(operation_name):
    """Decorator to profile function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                status = 'success'
                return result
            except Exception as e:
                status = 'failure'
                raise
            finally:
                duration = time.time() - start_time

                # Publish to CloudWatch
                cloudwatch = boto3.client('cloudwatch')
                cloudwatch.put_metric_data(
                    Namespace='NBA-Simulator/Performance',
                    MetricData=[{
                        'MetricName': f'{operation_name}Duration',
                        'Value': duration,
                        'Unit': 'Seconds',
                        'Dimensions': [
                            {'Name': 'Status', 'Value': status}
                        ]
                    }]
                )

        return wrapper
    return decorator
```

**Usage example:**
```python
from scripts.monitoring.profiler import profile_performance

@profile_performance('DataExtraction')
def extract_game_data(game_id):
    # ... extraction logic ...
    pass

@profile_performance('S3Upload')
def upload_to_s3(file_path, bucket, key):
    # ... upload logic ...
    pass
```

---

## Success Criteria

**Minimum Viable Product (MVP):**
- ✅ CloudWatch metrics published for S3, ADCE, costs
- ✅ 2 dashboards created (Data Collection, Performance)
- ✅ 4 critical alarms configured
- ✅ SNS topic with email notifications
- ✅ DIMS integration with auto-publish

**Full Success:**
- ✅ All critical paths profiled
- ✅ Automated anomaly detection
- ✅ Cost optimization recommendations
- ✅ Performance regression detection
- ✅ Integration with Phase 0.0019 (CI/CD)

---

## Implementation Plan

### Week 1: Metrics & Dashboards
**Days 1-2:**
- Create CloudWatch metrics publishing scripts
- Test metrics publication (S3, ADCE, performance, costs)
- Validate data appears in CloudWatch console

**Days 3-4:**
- Create dashboard JSON configurations
- Deploy dashboards via AWS CLI
- Customize widget layouts and queries

**Day 5:**
- Create alarms for critical metrics
- Set up SNS topic and subscriptions
- Test alarm notifications

### Week 2: Integration & Automation
**Days 1-2:**
- Integrate DIMS CLI with CloudWatch publishing
- Add profiling decorators to critical functions
- Test end-to-end metrics flow

**Days 3-4:**
- Set up automated metrics publishing (cron jobs)
- Create runbooks for alarm responses
- Document dashboard usage

**Day 5:**
- End-to-end validation
- Performance baseline establishment
- User training on dashboards

---

## Cost Breakdown

| Component | Configuration | Monthly Cost | Notes |
|-----------|--------------|--------------|-------|
| CloudWatch Metrics | ~30 custom metrics | $0.90 | $0.30 per metric |
| CloudWatch Alarms | 10 alarms | $1.00 | $0.10 per alarm |
| CloudWatch Dashboards | 3 dashboards | $0.00 | First 3 free |
| SNS Notifications | ~100 emails/month | $0.00 | First 1,000 free |
| CloudWatch Logs (optional) | 1 GB/month | $0.50 | $0.50/GB |
| **Total** | | **$1.90-2.40/month** | Minimal cost increase |

**Development Time:** 2 weeks (80 hours)

---

## Prerequisites

**Before starting Phase 0.0020:**
- [x] AWS CloudWatch access configured
- [x] DIMS system operational (Phase 0.16+)
- [x] ADCE operational (Phase 0.18)
- [ ] Email for SNS notifications
- [ ] Cost Explorer API enabled

---

## Integration with Existing Systems

### DIMS (Data Inventory Management System)
- Auto-publish metrics to CloudWatch every 6 hours
- Dashboard widget showing DIMS verification status
- Alarm when metrics drift detected

### ADCE (Autonomous Data Collection Ecosystem)
- Real-time task execution metrics
- Success rate tracking and trending
- Queue depth monitoring for capacity planning

### CI/CD (Phase 0.0019)
- Test results published to CloudWatch
- CI/CD pipeline duration tracking
- Pre-commit hook performance profiling

---

## Files to Create

**Scripts:**
```
scripts/monitoring/publish_collection_metrics.py   # S3, ADCE metrics
scripts/monitoring/publish_performance_metrics.py  # Operation profiling
scripts/monitoring/publish_cost_metrics.py         # AWS cost tracking
scripts/monitoring/create_dashboards.sh            # Dashboard deployment
scripts/monitoring/create_alarms.py                # Alarm configuration
scripts/monitoring/profiler.py                     # Performance decorator
```

**Dashboards:**
```
dashboards/data_collection_dashboard.json          # S3, ADCE overview
dashboards/performance_dashboard.json              # Performance, costs
dashboards/adce_health_dashboard.json              # ADCE detailed view
```

**Documentation:**
```
docs/monitoring/MONITORING_GUIDE.md                # How to use dashboards
docs/monitoring/ALARM_RUNBOOKS.md                  # Alarm response procedures
docs/monitoring/COST_OPTIMIZATION.md               # Cost tracking guide
```

---

## Common Issues & Solutions

### Issue 1: CloudWatch metrics not appearing
**Cause:** IAM permissions insufficient or namespace typo
**Solution:**
- Check IAM role has `cloudwatch:PutMetricData` permission
- Verify namespace spelling exactly matches (case-sensitive)
- Check metric timestamp is within 2 weeks of current time

### Issue 2: Alarms not triggering
**Cause:** SNS topic not subscribed or threshold incorrect
**Solution:**
- Verify SNS subscription confirmed (check email)
- Test SNS topic with `aws sns publish --topic-arn ... --message "test"`
- Manually trigger alarm with metric value

### Issue 3: Dashboard shows no data
**Cause:** Incorrect metric query or time range
**Solution:**
- Check metric namespace and name match exactly
- Adjust dashboard time range (last 1h → last 24h)
- Verify metrics exist in CloudWatch console

### Issue 4: Cost metrics delayed
**Cause:** Cost Explorer has 24-hour lag
**Solution:**
- Expect 1-day delay in cost data
- Use billing alerts for real-time cost tracking
- Check AWS Budgets for current spend estimate

---

## Workflows Referenced

- **Workflow #39:** Monitoring Automation - Scraper monitoring setup
- **Workflow #56:** DIMS Management - DIMS CLI and metrics
- **Workflow #6:** File Creation - Creating monitoring scripts
- **Workflow #2:** Command Logging - Documenting monitoring commands

---

## Related Documentation

**Monitoring:**
- [SCRAPER_MONITORING_SYSTEM.md](../../../SCRAPER_MONITORING_SYSTEM.md) - Existing monitoring
- [Workflow #56: DIMS Management](../../../claude_workflows/workflow_descriptions/56_dims_management.md)

**Cost Management:**
- [PROGRESS.md](../../../PROGRESS.md) - Budget tracking ($150/month)
- Cost breakdown sections in phase indexes

**Performance:**
- [LESSONS_LEARNED.md](../../../LESSONS_LEARNED.md) - Optimization learnings

---

## Navigation

**Return to:** [Phase 0 Index](../PHASE_0_INDEX.md)

**Prerequisites:** None (foundational)

**Integrates with:**
- Phase 0.0016: Robust Architecture - Multi-source monitoring
- Phase 0.0018: Autonomous Data Collection - ADCE health tracking
- Phase 0.0019: Testing Infrastructure & CI/CD - Test metrics publishing

---

## How This Enables the Simulation Vision

This sub-phase provides **observability infrastructure** that powers the **hybrid econometric + nonparametric simulation system** described in the [main README](../../../README.md#simulation-methodology).

**What this sub-phase enables:**

### 1. Econometric Causal Inference
From this sub-phase's monitoring, we can:
- **Track data quality** for panel data regression (ensure no missing covariates)
- **Monitor PPP estimation** performance (identify slow queries)
- **Detect data drift** that could bias causal estimates

### 2. Nonparametric Event Modeling
From this sub-phase's metrics, we build:
- **Validated event sequences** (monitor play-by-play completeness)
- **Performance-optimized** kernel density estimation (profile bottlenecks)
- **High-quality** training data (alarm on validation failures)

### 3. Context-Adaptive Simulations
Using this sub-phase's observability, simulations can:
- **Adapt to system load** (scale based on queue depth metrics)
- **Maintain accuracy** (detect when model performance degrades)
- **Optimize costs** (track compute spend per simulation run)

**See [main README](../../../README.md) for complete methodology.**

---

**Last Updated:** October 25, 2025 (Migrated from Phase 6.1)
**Status:** ⏸️ PENDING - Ready for implementation
**Migrated By:** Comprehensive Phase Reorganization (ADR-010)

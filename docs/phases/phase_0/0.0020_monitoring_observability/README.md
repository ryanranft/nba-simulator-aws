# Phase 0.0020: Monitoring & Observability

**Status:** ✅ IMPLEMENTED  
**Priority:** 🟡 Important  
**Implementation ID:** `phase_0/0.0020_monitoring_observability`  
**Parent Phase:** [Phase 0: Data Collection & Infrastructure](../../PHASE_0_INDEX.md)

## Overview

Comprehensive AWS CloudWatch integration for NBA Simulator monitoring and observability. Unifies existing monitoring systems (DIMS, ADCE, scraper monitoring) with AWS-native dashboards, automated alerts, and cost tracking.

**Core Capabilities:**
- 40+ custom CloudWatch metrics across 5 namespaces
- 3 pre-built CloudWatch dashboards  
- 4 critical alarms with SNS notifications
- Performance profiling decorators
- Cost tracking and budget alerts

---

## Quick Start

### 1. Test Metrics Publishing (Dry Run)

```bash
python scripts/monitoring/cloudwatch/publish_dims_metrics.py --dry-run
python scripts/monitoring/cloudwatch/publish_adce_metrics.py --dry-run
python scripts/monitoring/cloudwatch/publish_s3_metrics.py --dry-run
python scripts/monitoring/cloudwatch/publish_cost_metrics.py --dry-run
```

### 2. Create SNS Topic

```bash
bash scripts/monitoring/cloudwatch/setup_sns_topics.sh create
# Confirm subscription in your email
```

### 3. Create Alarms

```bash
python scripts/monitoring/cloudwatch/create_alarms.py --create
```

### 4. Publish Metrics

```bash
python scripts/monitoring/cloudwatch/publish_dims_metrics.py
python scripts/monitoring/cloudwatch/publish_adce_metrics.py  
python scripts/monitoring/cloudwatch/publish_s3_metrics.py
python scripts/monitoring/cloudwatch/publish_cost_metrics.py
```

### 5. View Dashboards

AWS CloudWatch Console → Dashboards:
- `NBA-Simulator-DataCollection`
- `NBA-Simulator-Performance`
- `NBA-Simulator-Costs`

---

## Components

### Metric Publishers

Located in `scripts/monitoring/cloudwatch/`:

- **publish_dims_metrics.py** - DIMS metrics (S3, code, docs, git, data quality)
- **publish_adce_metrics.py** - ADCE health (queue, components, uptime)
- **publish_s3_metrics.py** - S3 inventory (objects, sizes, by source)
- **publish_cost_metrics.py** - AWS costs (monthly, budget, forecast)
- **profiler.py** - Performance profiling decorator

### Configuration

**File:** `config/cloudwatch_config.yaml`

- AWS region and credentials
- Metric namespaces
- Publishing intervals
- Budget limits
- SNS topics
- Alarm thresholds

### Dashboards

JSON definitions in `dashboards/`:

- **data_collection_dashboard.json** - S3, ADCE, data quality
- **performance_dashboard.json** - Latency, throughput, success rates
- **cost_dashboard.json** - Monthly costs, budget utilization

Deploy with:
```bash
aws cloudwatch put-dashboard --dashboard-name NBA-Simulator-DataCollection \
  --dashboard-body file://docs/phases/phase_0/0.0020_monitoring_observability/dashboards/data_collection_dashboard.json
```

### Alarms

**Script:** `scripts/monitoring/cloudwatch/create_alarms.py`

Critical alarms:
1. ADCE queue depth > 100 tasks
2. Budget utilization > 80%/95%
3. S3 upload failures > 5 in 10 min
4. DIMS validation drift > 10 metrics

### SNS Topics

**Script:** `scripts/monitoring/cloudwatch/setup_sns_topics.sh`

- Topic: `nba-simulator-alerts`
- Email notifications
- Alarm integration

---

## Metrics Published

### DIMS Namespace (`NBA-Simulator/DIMS`)

- S3ObjectCount, S3SizeGB
- PythonFileCount, TestFileCount, MLScriptCount
- GitCommitCount, BookRecommendationsImplemented
- **MetricsWithDrift** (alarm), ValidationFailures, DataGaps

### ADCE Namespace (`NBA-Simulator/ADCE`)

- **ADCETaskQueueDepth** (alarm)
- ADCETasksCritical/High/Medium/Low
- ADCEHealthyComponents, ADCEUnhealthyComponents
- ADCEUptime, ADCEReconciliationCycles

### S3 Namespace (`NBA-Simulator/S3`)

- S3TotalObjects, S3TotalSizeGB
- S3ObjectsBySource (dimensions)
- **S3UploadFailures** (alarm)

### Costs Namespace (`NBA-Simulator/Costs`)

- MonthlyAWSCost, ForecastedMonthlyCost
- **BudgetUtilization** (alarm)
- CostByService (dimensions)

### Performance Namespace (`NBA-Simulator/Performance`)

- OperationDuration (avg, p99, max)
- ReconciliationCycleDuration
- DatabaseQueryDuration, S3UploadDuration

---

## Cost Impact

| Component | Cost |
|-----------|------|
| CloudWatch Metrics (40) | $12.00/mo |
| CloudWatch Alarms (10) | $1.00/mo |
| CloudWatch Dashboards (3) | $9.00/mo |
| SNS Notifications | $0.00 |
| **TOTAL** | **$22.80/mo** |

**Budget Impact:** 17% of $150/mo budget  
**Optimized:** ~$10-15/mo (reduce frequency, fewer dashboards)

---

## Deployment

### Prerequisites

```bash
aws configure
pip install boto3 pyyaml
```

### Steps

1. **Configure:** Edit `config/cloudwatch_config.yaml` (set email)
2. **SNS:** `bash scripts/monitoring/cloudwatch/setup_sns_topics.sh create`
3. **Test:** Run publishers with `--dry-run`
4. **Publish:** Run publishers without flags
5. **Dashboards:** Deploy via AWS CLI (see above)
6. **Alarms:** `python scripts/monitoring/cloudwatch/create_alarms.py --create`

### Automation (Cron)

```bash
# DIMS (every 6 hours)
0 */6 * * * cd /path/to/nba-simulator-aws && python scripts/monitoring/cloudwatch/publish_dims_metrics.py

# ADCE (every 5 minutes)
*/5 * * * * cd /path/to/nba-simulator-aws && python scripts/monitoring/cloudwatch/publish_adce_metrics.py

# S3 (hourly)
0 * * * * cd /path/to/nba-simulator-aws && python scripts/monitoring/cloudwatch/publish_s3_metrics.py

# Costs (daily)
0 0 * * * cd /path/to/nba-simulator-aws && python scripts/monitoring/cloudwatch/publish_cost_metrics.py
```

---

## Performance Profiling

Add to critical functions:

```python
from scripts.monitoring.cloudwatch.profiler import profile_performance

@profile_performance('ReconciliationCycle')
def reconcile():
    # Your code here
    pass
```

Context manager:
```python
from scripts.monitoring.cloudwatch.profiler import profile_context

with profile_context('DataProcessing'):
    process_data()
```

---

## Troubleshooting

### Metrics Not Appearing

- Check AWS region in config
- Verify IAM permissions (cloudwatch:PutMetricData)
- Wait 5-10 minutes after first publish

### ADCE Metrics Fail

- Check ADCE running: `python scripts/autonomous/autonomous_cli.py status`
- Test health endpoint: `curl http://localhost:8080/status`

### Cost Explorer Errors

- Enable Cost Explorer in AWS Console (Billing Dashboard)
- Add IAM permissions: ce:GetCostAndUsage, ce:GetCostForecast

### SNS Emails Not Received

- Confirm subscription via email link
- Check spam folder
- Verify subscription status: `bash scripts/monitoring/cloudwatch/setup_sns_topics.sh list`

---

## Related Documentation

- [Phase 0 Index](../../PHASE_0_INDEX.md)
- [DIMS Documentation](../../../monitoring/dims/)
- [ADCE Documentation](../../../adce/)
- [AWS CloudWatch Docs](https://docs.aws.amazon.com/cloudwatch/)

---

## Navigation

**Return to:** [Phase 0 Index](../../PHASE_0_INDEX.md)

**Prerequisites:**
- 0.0018: ADCE
- 0.0019: DIMS v3.1

**Integrates With:**
- All data collection scrapers
- ADCE health monitoring
- DIMS metrics tracking

---

**Phase 0.0020 Complete** ✅  
**Implementation Date:** November 1, 2025  
**Files Created:** 15+ files, ~7,000 lines  
**Cost Impact:** +$22.80/month

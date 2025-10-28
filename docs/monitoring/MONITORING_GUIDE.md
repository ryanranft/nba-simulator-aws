# NBA Simulator - Monitoring Guide

**Phase 0.0020: Monitoring & Observability**

This guide covers the CloudWatch monitoring infrastructure for the NBA Simulator project.

---

## Quick Start

### 1. Setup SNS Notifications
```bash
# Create SNS topic and subscribe email
bash scripts/monitoring/setup_sns.sh --email your@email.com

# Confirm subscription in your inbox
# Note the Topic ARN for next steps
```

### 2. Create CloudWatch Dashboards
```bash
# Create all dashboards
bash scripts/monitoring/create_dashboards.sh

# Or create specific dashboard
bash scripts/monitoring/create_dashboards.sh --dashboard data-collection
```

### 3. Create CloudWatch Alarms
```bash
# Create all alarms (replace with your SNS topic ARN)
python scripts/monitoring/create_alarms.py \
  --sns-topic arn:aws:sns:us-east-1:123456789:nba-simulator-alerts \
  --all \
  --budget 150

# Or create specific alarm
python scripts/monitoring/create_alarms.py \
  --sns-topic arn:aws:sns:us-east-1:123456789:nba-simulator-alerts \
  --alarm adce-failure
```

### 4. Publish Metrics
```bash
# Publish all metrics
python scripts/monitoring/publish_collection_metrics.py --all
python scripts/monitoring/publish_cost_metrics.py

# Or publish specific metrics
python scripts/monitoring/publish_collection_metrics.py --metric s3
python scripts/monitoring/publish_collection_metrics.py --metric adce
```

---

## CloudWatch Dashboards

### Dashboard 1: Data Collection Overview
- **S3 Bucket Growth**: Object count and storage size trending
- **ADCE Task Execution**: Completed vs failed tasks
- **ADCE Success Rate**: Real-time autonomous system health
- **ADCE Queue Depth**: Task backlog monitoring

**View at**: `NBA-Simulator-DataCollection` dashboard

### Dashboard 2: Performance & Costs
- **Data Extraction Performance**: Average and p99 latency
- **S3 Upload Performance**: Upload duration tracking
- **AWS Costs vs Budget**: Monthly spend vs $150 limit
- **Budget Utilization %**: Percentage of budget consumed
- **Cost Breakdown**: S3 vs RDS spending

**View at**: `NBA-Simulator-Performance` dashboard

### Dashboard 3: ADCE Health
- **Current Success Rate**: Single-value metric
- **Current Queue Depth**: Real-time queue size
- **24h Success Rate**: Rolling daily success percentage
- **Task Execution Rate**: 5-minute interval task counts
- **Success Rate Trending**: Historical performance
- **Queue Depth Over Time**: Capacity planning insights

**View at**: `NBA-Simulator-ADCE-Health` dashboard

---

## CloudWatch Alarms

### 1. ADCE-HighFailureRate
- **Threshold**: Success rate < 95% for 10 minutes
- **Action**: SNS notification
- **Purpose**: Detect ADCE system failures early

### 2. AWS-CostBudgetExceeded
- **Threshold**: Budget utilization > 80%
- **Action**: SNS notification
- **Purpose**: Prevent unexpected AWS costs

### 3. S3-UploadFailures
- **Threshold**: > 5 upload failures in 10 minutes
- **Action**: SNS notification
- **Purpose**: Detect S3 connectivity issues

### 4. Data-QualityIssues
- **Threshold**: Validation pass rate < 95%
- **Action**: SNS notification
- **Purpose**: Ensure data quality standards

---

## Automated Metrics Publishing

### Cron Jobs (Recommended)
```bash
# Add to crontab (crontab -e)

# Publish S3/ADCE metrics every 6 hours
0 */6 * * * cd /Users/ryanranft/nba-simulator-aws && /usr/bin/python3 scripts/monitoring/publish_collection_metrics.py --all >> /var/log/nba-sim-metrics.log 2>&1

# Publish cost metrics daily at 8 AM
0 8 * * * cd /Users/ryanranft/nba-simulator-aws && /usr/bin/python3 scripts/monitoring/publish_cost_metrics.py >> /var/log/nba-sim-costs.log 2>&1

# DIMS verification with CloudWatch publishing every 6 hours
0 */6 * * * cd /Users/ryanranft/nba-simulator-aws && /usr/bin/python3 scripts/monitoring/dims_cli.py verify --publish-cloudwatch >> /var/log/dims.log 2>&1
```

---

## Performance Profiling

### Using the Decorator
```python
from scripts.monitoring.profiler import profile_performance

@profile_performance('GameDataExtraction')
def extract_game_data(game_id):
    # ... extraction logic ...
    return data

# Automatically publishes:
# - GameDataExtractionDuration: execution time
# - GameDataExtractionSuccessCount: 1 (on success)
# - GameDataExtractionFailureCount: 1 (on failure)
```

### Using Context Manager
```python
from scripts.monitoring.profiler import profile_context

with profile_context('DatabaseQuery'):
    # ... perform query ...
    results = db.execute(query)

# Automatically publishes duration metric
```

### Async Functions
```python
from scripts.monitoring.profiler import profile_async_performance

@profile_async_performance('AsyncDataFetch')
async def fetch_data(url):
    # ... async fetch logic ...
    return data
```

---

## Cost Tracking

### Current Baseline
- **S3 Storage**: $2.72/month (118.27 GB @ $0.023/GB)
- **RDS Database**: $29.00/month (db.t3.micro)
- **CloudWatch**: $1.90-2.40/month (metrics + alarms)
- **Total Baseline**: $33.62-34.12/month
- **Budget**: $150.00/month
- **Headroom**: $115-116/month

### Cost Optimization Tips
1. **S3 Lifecycle Policies**: Archive old data to Glacier
2. **RDS Reserved Instances**: Save up to 40% with 1-year commitment
3. **CloudWatch Metric Filtering**: Only publish essential metrics
4. **Data Retention**: Set CloudWatch log retention to 7-30 days

---

## Troubleshooting

### Metrics Not Appearing in CloudWatch
**Issue**: Published metrics don't show up in dashboards

**Solutions**:
1. Check IAM permissions: `cloudwatch:PutMetricData`
2. Verify namespace spelling: `NBA-Simulator/DataCollection`
3. Check metric timestamp (must be within 2 weeks)
4. Wait 1-2 minutes for metrics to propagate

### Alarms Not Triggering
**Issue**: Alarms stay in INSUFFICIENT_DATA or don't notify

**Solutions**:
1. Verify SNS subscription is confirmed (check email)
2. Test SNS topic: `bash scripts/monitoring/setup_sns.sh --test`
3. Check alarm threshold matches metric scale
4. Ensure metrics are being published regularly

### Cost Explorer API Errors
**Issue**: Cost metrics fail to retrieve data

**Solutions**:
1. Enable Cost Explorer in AWS Console
2. Wait 24 hours for first data
3. Check IAM permissions: `ce:GetCostAndUsage`
4. Use estimated costs as fallback

---

## Maintenance

### Weekly Tasks
- [ ] Review CloudWatch dashboards for anomalies
- [ ] Check alarm history for false positives
- [ ] Verify cost tracking accuracy

### Monthly Tasks
- [ ] Analyze cost trends and optimize
- [ ] Review alarm thresholds for tuning
- [ ] Archive old CloudWatch logs

### Quarterly Tasks
- [ ] Audit unused metrics and dashboards
- [ ] Update monitoring documentation
- [ ] Review and adjust budget limits

---

## Related Documentation

- [DIMS Management](../claude_workflows/workflow_descriptions/56_dims_management.md)
- [Phase 0.0020 README](../phases/phase_0/0.0020_monitoring_observability/README.md)
- [Emergency Recovery](../EMERGENCY_RECOVERY.md)
- [Cost Management](PROGRESS.md#cost-tracking)

---

**Last Updated**: October 27, 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready

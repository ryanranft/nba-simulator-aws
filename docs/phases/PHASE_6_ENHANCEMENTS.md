# Phase 6: Optional Enhancements

**Status:** ⏸️ PENDING (Optional)
**Prerequisites:** Phases 1-5 complete (full pipeline operational)
**Estimated Time:** 3-5 hours
**Estimated Cost:** $4-10/month
**Started:** TBD
**Completed:** TBD

---

## Overview

Optional enhancements to improve analytics capabilities, monitoring, and operational efficiency. These components are not required for core functionality but add value for production deployments.

**This phase includes:**
- S3 Analytics Lake for simulation outputs
- AWS Athena for SQL on S3
- CloudWatch Dashboards & Alarms

---

## Prerequisites

Before starting this phase:
- [ ] Phases 1-3 complete (data pipeline operational)
- [ ] Phase 4 or 5 in progress (generating outputs)
- [ ] AWS cost monitoring in place

**See workflow #18 (Cost Management) for budget tracking.**

---

## Implementation Steps

### Sub-Phase 6.1: S3 Analytics Lake (Simulation Outputs)

**Status:** ⏸️ PENDING
**Time Estimate:** 1 hour
**Cost:** $0.50-5/month

**Follow these workflows:**
- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
- Workflow #21 ([Data Validation](../claude_workflows/workflow_descriptions/21_data_validation.md))

**Purpose:**
Store simulation results in Parquet format for efficient analytical queries without loading data into RDS.

**Configuration steps:**
1. [ ] Modify simulation code to write outputs to S3
2. [ ] Use Parquet format for compression and performance
3. [ ] Partition by date/season for efficient queries
4. [ ] Test output format and accessibility

**S3 structure:**
```
s3://nba-sim-raw-data-lake/simulation-outputs/
├── season=2024-25/
│   ├── date=2024-10-15/
│   │   ├── game_predictions.parquet
│   │   └── player_predictions.parquet
│   └── date=2024-10-16/
│       └── ...
└── season=2023-24/
    └── ...
```

**Simulation code modification:**
```python
import pandas as pd
from datetime import datetime

# Run simulation
results_df = simulate_games(...)

# Save to S3 in Parquet format
season = "2024-25"
date = datetime.now().strftime("%Y-%m-%d")
output_path = f"s3://nba-sim-raw-data-lake/simulation-outputs/season={season}/date={date}/predictions.parquet"

results_df.to_parquet(output_path, compression='snappy')
print(f"Results saved to {output_path}")
```

**Validation:**
- [ ] Outputs written to S3 successfully
- [ ] Parquet files readable
- [ ] Partitioning works correctly
- [ ] Compression reduces file size (50-80% reduction)

---

### Sub-Phase 6.2: AWS Athena (SQL on S3)

**Status:** ⏸️ PENDING
**Time Estimate:** 30 minutes
**Cost:** $0.50-2/month (pay-per-query)

**Follow these workflows:**
- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))

**Purpose:**
Run SQL queries directly on S3 data without loading into RDS. Cheaper for occasional analytical queries.

**Configuration steps:**
1. [ ] Create Athena database
2. [ ] Define external tables pointing to S3
3. [ ] Run test queries
4. [ ] Document query patterns

**Create Athena database:**
```sql
CREATE DATABASE nba_simulations;
```

**Define table on S3 Parquet data:**
```sql
CREATE EXTERNAL TABLE nba_simulations.game_predictions (
    game_id STRING,
    home_team STRING,
    away_team STRING,
    home_win_prob DOUBLE,
    predicted_home_score INT,
    predicted_away_score INT
)
PARTITIONED BY (
    season STRING,
    date STRING
)
STORED AS PARQUET
LOCATION 's3://nba-sim-raw-data-lake/simulation-outputs/';

-- Load partitions
MSCK REPAIR TABLE nba_simulations.game_predictions;
```

**Example queries:**
```sql
-- Average win probability for home teams
SELECT AVG(home_win_prob) as avg_home_advantage
FROM nba_simulations.game_predictions
WHERE season = '2024-25';

-- Top predicted scores
SELECT home_team, AVG(predicted_home_score) as avg_score
FROM nba_simulations.game_predictions
WHERE season = '2024-25'
GROUP BY home_team
ORDER BY avg_score DESC
LIMIT 10;
```

**Cost calculation:**
- $5.00 per TB of data scanned
- Typical query: 10-100 MB scanned
- Cost per query: $0.00005-0.0005
- 100 queries/month: ~$0.01
- 1000 queries/month: ~$0.10

**Validation:**
- [ ] Athena database created
- [ ] Tables defined and partitions loaded
- [ ] Test queries return results
- [ ] Query performance acceptable (<10 seconds)

---

### Sub-Phase 6.3: CloudWatch Dashboards & Alarms

**Status:** ⏸️ PENDING
**Time Estimate:** 1-2 hours
**Cost:** ~$3-5/month

**Follow these workflows:**
- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
- Workflow #11 ([Error Handling](../claude_workflows/workflow_descriptions/11_error_handling.md))

**Purpose:**
Monitor AWS resource usage, costs, and performance. Set up alarms for budget overruns and operational issues.

**Configuration steps:**
1. [ ] Create cost alarm (budget threshold)
2. [ ] Create performance dashboard
3. [ ] Set up error alerts
4. [ ] Test alarm notifications

**Create cost alarm:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name nba-simulator-monthly-cost \
  --alarm-description "Alert when monthly cost exceeds $150" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --threshold 150 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:billing-alerts
```

**Recommended alarms:**
| Alarm | Threshold | Action |
|-------|-----------|--------|
| Monthly cost | > $150 | Email notification |
| RDS CPU | > 80% for 5 min | Email + scale up |
| EC2 stopped | Unexpected stop | Email notification |
| S3 storage | > 200 GB | Review data retention |
| Glue job failure | Any failure | Email + investigate |

**Create dashboard:**
```bash
aws cloudwatch put-dashboard \
  --dashboard-name nba-simulator-metrics \
  --dashboard-body file://dashboard-config.json
```

**Dashboard widgets:**
- Monthly cost trend (last 30 days)
- RDS CPU/Memory utilization
- EC2 instance status
- S3 storage usage
- Simulation job success rate

**Validation:**
- [ ] Alarms created and active
- [ ] Dashboard displays metrics
- [ ] Test alarm triggers (set low threshold temporarily)
- [ ] Notifications received

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| **S3 Analytics Lake** | 20-100 GB | $0.50-2.30 | Simulation outputs in Parquet |
| **AWS Athena** | 100-1000 queries | $0.01-0.10 | Pay-per-query ($5/TB scanned) |
| **CloudWatch Dashboard** | 1 dashboard | $3.00 | First 3 dashboards |
| **CloudWatch Alarms** | 5-10 alarms | $0 | First 10 alarms free |
| **Custom Metrics** | 5 metrics | $1.50 | $0.30/metric/month |
| **SNS Notifications** | 100 emails/month | $0 | First 1000 free |
| **Total Phase Cost** | | **$4-7/month** | Analytics + monitoring |

**Recommendation:** Implement gradually as needed

---

## Benefits

### S3 Analytics Lake
- ✅ Cheaper storage than RDS for historical data ($0.023/GB vs $0.115/GB)
- ✅ Scalable to petabytes
- ✅ Queryable via Athena without loading
- ✅ Supports multiple output formats (Parquet, ORC, JSON)

### AWS Athena
- ✅ No infrastructure to manage
- ✅ Pay only for queries run ($5/TB)
- ✅ Supports standard SQL
- ✅ Integrates with BI tools (QuickSight, Tableau)
- ✅ Cheaper than RDS for occasional analytical queries

### CloudWatch Monitoring
- ✅ Proactive cost management (alerts before overspending)
- ✅ Performance visibility (identify bottlenecks)
- ✅ Error detection (catch failures early)
- ✅ Operational dashboards (single pane of glass)

---

## Troubleshooting

**Common issues:**

1. **Athena query fails**
   - Check S3 path is correct
   - Verify partition format matches table definition
   - Run `MSCK REPAIR TABLE` to load new partitions

2. **CloudWatch alarm not triggering**
   - Verify SNS topic subscription confirmed
   - Check alarm threshold and evaluation periods
   - Review CloudWatch Logs for alarm state changes

3. **Parquet files corrupted**
   - Ensure simulation code closes files properly
   - Use `compression='snappy'` for better compatibility
   - Validate with `pd.read_parquet()` after writing

---

## Success Criteria

Phase complete when:
- [ ] Simulation outputs stored in S3 (Parquet format)
- [ ] Athena database and tables created
- [ ] Test queries run successfully
- [ ] Cost alarm configured and tested
- [ ] Performance dashboard operational
- [ ] All alarms active and notifications working
- [ ] Cost within budget ($4-10/month)

---

## Next Steps

After completing this phase:
1. [ ] Update PROGRESS.md status
2. [ ] Document query patterns for Athena
3. [ ] Monitor dashboards for optimization opportunities
4. [ ] Consider additional enhancements:
   - QuickSight for visualization ($9/user/month)
   - Lambda functions for automation
   - Step Functions for workflow orchestration
   - API Gateway for external access

---

## Future Enhancements (Beyond Phase 6)

**Potential additions:**

1. **AWS QuickSight** ($9/user/month)
   - Visual dashboards and BI reports
   - Interactive data exploration
   - ML-powered insights

2. **AWS Lambda** (pay-per-invocation)
   - Automated data processing
   - Event-driven workflows
   - Serverless APIs

3. **AWS Step Functions** ($25 per million state transitions)
   - Orchestrate complex workflows
   - Coordinate ML pipelines
   - Error handling and retries

4. **API Gateway** (pay-per-request)
   - REST API for predictions
   - Public/private endpoints
   - Rate limiting and authentication

5. **AWS Glue DataBrew** ($1/node-hour)
   - Visual data preparation
   - No-code transformations
   - Data quality rules

---

*Last updated: 2025-10-02*
*Status: Optional enhancements, implement as needed*
*Total time: 3-5 hours*
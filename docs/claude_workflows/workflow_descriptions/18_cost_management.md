## 💰 Cost Management Workflows

### Automated Cost Reporting (Recommended)

**Purpose:** Get real-time AWS cost breakdown with budget alerts and optimization recommendations

**Script:** `scripts/aws/check_costs.sh`

**Usage:**
```bash
bash scripts/aws/check_costs.sh

# Or via Makefile:
make check-costs
```

**What this report includes:**

#### 1. Total Cost (Month-to-Date)
Shows current month spending from start of month to today:
```
💰 Total Cost (Month-to-Date):
   $12.34 USD
```

#### 2. Cost by Service (Top 10)
Breaks down spending by AWS service, sorted by cost:
```
📊 Cost by Service:
   Amazon Simple Storage Service (S3)    2.74 USD
   Amazon Relational Database Service    8.50 USD
   AWS Glue                              1.10 USD
```

**Key services monitored:**
- **S3:** Storage costs (currently $2.74/month for 146K files)
- **RDS:** Database instance hours (~$29/month for db.t3.small)
- **Glue:** ETL job DPU-hours (~$0.44/DPU-hour)
- **EC2:** Compute instances (~$5-15/month for t2.micro)
- **SageMaker:** Notebook instances (~$50/month for ml.t3.medium)

#### 3. S3 Storage Analysis
Calculates S3 bucket size and estimated monthly cost:
```
🗄️  S3 Storage:
   Size: 119.23 GB
   Estimated monthly cost: $2.74
```

**Cost calculation:** `Size (GB) × $0.023/GB` (S3 Standard storage)

#### 4. RDS Status
Shows RDS instance status and estimated cost:
```
🗃️  RDS Status:
   Status: available
   Instance: db.t3.small
   Estimated cost: ~$29/month
```

**Possible statuses:**
- `available` - Running (incurring costs)
- `stopped` - Stopped (minimal costs)
- `Not created yet (⏸️ Pending)` - No RDS resources

#### 5. EC2 Instances
Lists EC2 instances tagged with Project=nba-simulator:
```
🖥️  EC2 Instances:
   i-0123456789abcdef0: running (t2.micro)
```

**Note:** Only shows instances tagged properly. Untagged instances won't appear.

#### 6. Glue Jobs
Lists Glue ETL jobs:
```
⚙️  Glue Jobs:
   Jobs: extract-schedule extract-pbp process-game-data
```

**Status:** Shows "Not created yet (⏸️ Pending)" if Phase 2.2 ETL not started

#### 7. Cost Forecast
Projects end-of-month total based on current spending rate:
```
📈 Cost Forecast:
   Projected month-end total: $18.67 USD
```

**Uses:** AWS Cost Explorer forecast API to predict month-end total

#### 8. Budget Alert
Warns if spending exceeds budget threshold:
```
⚠️  WARNING: Month-to-date costs exceed budget threshold of $150
```

**Budget threshold:** $150/month (configured in script line 148)

#### 9. Cost Summary & Recommendations
Provides context-aware optimization tips:

**Low costs (<$10/month):**
```
✅ Costs are low (Phase 0: S3 only)
```

**Moderate costs ($10-50/month):**
```
✅ Costs are within expected range (S3 + minimal services)
```

**High costs ($50-100/month):**
```
⚠️  Costs are moderate - monitor RDS/EC2 usage
```

**Very high costs (>$100/month):**
```
⚠️  Costs are high - review running services
   Consider stopping unused RDS/EC2 instances
```

#### 10. Cost Optimization Tips
Always displays practical optimization strategies:
```
💡 Cost Optimization Tips:
   1. Stop RDS when not in use (saves ~$29-60/month)
   2. Stop EC2 when not in use (saves ~$5-15/month)
   3. Use Spot Instances for non-critical workloads
   4. Run Glue ETL monthly instead of daily
   5. Monitor with: aws ce get-cost-and-usage --help
```

### When to Run Cost Report

**Run `check_costs.sh` when:**

1. **Before creating new AWS resources** (RDS, EC2, Glue jobs, SageMaker)
   - Establishes baseline before change
   - Helps calculate marginal cost increase

2. **Weekly (every Monday)** as part of maintenance routine
   - Track spending trends
   - Catch unexpected cost increases early

3. **After deploying new infrastructure** (same day and next day)
   - Verify expected cost increase
   - Detect provisioning errors (e.g., wrong instance size)

4. **When approaching end of month** (last week)
   - Check if forecast exceeds budget
   - Time to optimize if needed

5. **After receiving AWS cost alert emails**
   - Investigate which service caused spike
   - Take immediate action if needed

### Integration with Other Workflows

**Before Creating AWS Resources Workflow:**
```bash
# Step 1: Check current costs
bash scripts/aws/check_costs.sh

# Step 2: Review PROGRESS.md cost estimates for new resource
# Step 3: Calculate monthly impact
# Step 4: Warn user with explicit approval
# Step 5: Create resource
# Step 6: Run check_costs.sh again to verify
```

**Weekly Maintenance Workflow (update_docs.sh):**
The weekly documentation update script also fetches costs and updates PROGRESS.md automatically. The `check_costs.sh` script provides the detailed breakdown.

**Session End Workflow (session_end.sh):**
Consider running cost check at end of sessions where AWS resources were created/modified.

### Cost Tracking Workflow (Weekly)

**Run every Monday or after creating resources:**

1. **Check AWS Cost Explorer (detailed breakdown)**
   ```bash
   bash scripts/aws/check_costs.sh
   ```

2. **Review by service:**
   - S3 storage costs (from report section 3)
   - RDS instance hours (from report section 4)
   - Glue job DPU-hours (from report section 6)
   - EC2 instance hours (from report section 5)
   - SageMaker notebook hours (not yet tracked)

3. **Update PROGRESS.md** with actual costs (lines 1145-1206)
   ```bash
   # Compare actual costs from report to estimates in PROGRESS.md
   # Update if variance >20%
   ```

4. **Compare actual vs. estimated:**
   - If >20% over estimate → investigate why
   - If consistently under → update estimates

### Cost Optimization Workflow

**Run when approaching budget limit:**

1. **Identify highest costs** (Cost Explorer breakdown)
2. **Optimization strategies:**
   - **RDS:** Stop when not in use, reduce instance size
   - **Glue:** Reduce DPUs (2 minimum), optimize job runtime
   - **EC2:** Stop instances, use smaller instance types
   - **SageMaker:** Stop notebooks when not in use
   - **S3:** Review Intelligent-Tiering, lifecycle policies
3. **Calculate savings:** Before vs. after optimization
4. **Update PROGRESS.md** with new estimates
5. **Document optimization** in COMMAND_LOG.md

**Cost estimate reference (from PROGRESS.md):**
- S3 storage: $2.74/month (current)
- RDS db.t3.micro: ~$29/month
- Glue jobs (2 DPU): ~$13/month
- EC2 t2.micro: ~$8-15/month
- SageMaker ml.t3.medium: ~$50/month
- **Total full deployment:** $95-130/month
- **Budget target:** $150/month

---


# Workflow #37: Shutdown Compute Instances

**Purpose:** Stop EC2 and SageMaker instances to save costs during periods of inactivity

**When to use:**
- Before extended absences (vacation, travel)
- End of work sessions
- When not actively using simulation or ML training

**Estimated time:** 2-3 minutes

**Cost impact:** Saves $6.59/month (EC2) + $50/month (SageMaker if running 24/7)

---

## Prerequisites

- AWS CLI configured
- Active AWS session

---

## Steps

### 1. Check Current Instance Status

```bash
echo "=== Checking running instances ==="
echo ""

# Check EC2 instances
echo "EC2 Instances:"
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*nba*" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,Tags[?Key==`Name`].Value|[0]]' \
  --output table

echo ""

# Check SageMaker notebooks
echo "SageMaker Notebooks:"
aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[?NotebookInstanceStatus==`InService`].[NotebookInstanceName,NotebookInstanceStatus,InstanceType]' \
  --output table
```

### 2. Stop EC2 Instance (Simulation Engine)

```bash
echo ""
echo "=== Stopping EC2 Instance ==="

# Get instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=nba-simulation-engine" "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].InstanceId' \
  --output text)

if [ -n "$INSTANCE_ID" ]; then
  echo "Stopping EC2 instance: $INSTANCE_ID"
  aws ec2 stop-instances --instance-ids $INSTANCE_ID
  echo "✓ EC2 instance stopping (saves ~$6.59/month)"
else
  echo "No running EC2 instances found"
fi
```

### 3. Stop SageMaker Notebook

```bash
echo ""
echo "=== Stopping SageMaker Notebook ==="

# Get notebook name and status
NOTEBOOK_NAME=$(aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[?NotebookInstanceStatus==`InService`].NotebookInstanceName' \
  --output text | head -1)

if [ -n "$NOTEBOOK_NAME" ]; then
  echo "Stopping SageMaker notebook: $NOTEBOOK_NAME"
  aws sagemaker stop-notebook-instance --notebook-instance-name "$NOTEBOOK_NAME"
  echo "✓ SageMaker notebook stopping (saves ~$50/month if running 24/7)"
else
  echo "No running SageMaker notebooks found"
fi
```

### 4. Verify Shutdown

Wait 30 seconds, then verify:

```bash
echo ""
echo "=== Verification (waiting 30 seconds) ==="
sleep 30

echo ""
echo "EC2 Status:"
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=nba-simulation-engine" \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' \
  --output table

echo ""
echo "SageMaker Status:"
aws sagemaker list-notebook-instances \
  --query 'NotebookInstances[*].[NotebookInstanceName,NotebookInstanceStatus]' \
  --output table
```

**Expected output:**
- EC2: `stopping` or `stopped`
- SageMaker: `Stopping` or `Stopped`

---

## Quick Script

For convenience, use the automated script:

```bash
bash scripts/aws/shutdown_compute.sh
```

---

## Cost Savings

**Monthly savings when stopped:**

| Resource | Running Cost | Stopped Cost | Savings |
|----------|-------------|--------------|---------|
| EC2 (t3.small) | $6.59/month | $0 | $6.59 |
| SageMaker (ml.t3.medium, 24/7) | ~$50/month | $0 | ~$50 |
| **Total** | **~$56.59/month** | **$0** | **~$56.59** |

**Note:** You still pay for:
- S3 storage: $2.74/month
- RDS database: $29/month (unless also stopped)
- Lambda/API Gateway: ~$0.20/month (pay-per-request)

---

## Restart Instances

To restart instances when you return:

### Restart EC2:
```bash
aws ec2 start-instances --instance-ids i-0b8bbe4cdff7ae2d2
```

### Restart SageMaker:
```bash
aws sagemaker start-notebook-instance --notebook-instance-name nba-ml-notebook
```

Or use the startup script:
```bash
bash scripts/aws/startup_compute.sh
```

---

## Optional: Stop RDS Database

**For trips longer than 7 days, consider RDS:**

### Temporary Stop (up to 7 days):
```bash
aws rds stop-db-instance --db-instance-identifier nba-sim-db
```

**Note:** AWS automatically restarts RDS after 7 days.

### For Longer Trips (Snapshot + Delete):

1. **Create snapshot:**
```bash
aws rds create-db-snapshot \
  --db-instance-identifier nba-sim-db \
  --db-snapshot-identifier nba-sim-db-snapshot-$(date +%Y%m%d)
```

2. **Wait for snapshot (takes 5-10 minutes):**
```bash
aws rds wait db-snapshot-available \
  --db-snapshot-identifier nba-sim-db-snapshot-$(date +%Y%m%d)
```

3. **Delete database:**
```bash
aws rds delete-db-instance \
  --db-instance-identifier nba-sim-db \
  --skip-final-snapshot
```

4. **Restore when back:**
```bash
# See workflow #38 (RDS Restore from Snapshot)
```

**Savings:** $29/month

---

## Troubleshooting

### Instance won't stop
- **EC2:** Check if instance has termination protection enabled
- **SageMaker:** May take 2-3 minutes to transition to "Stopping"

### Already stopped
- If instances are already stopped, script will report "No running instances found"

### Can't find instance
- Verify instance exists: `aws ec2 describe-instances --instance-ids i-0b8bbe4cdff7ae2d2`
- Check correct AWS region: `--region us-east-1`

---

## Related Workflows

- **Workflow #38:** Startup Compute Instances
- **Workflow #39:** RDS Snapshot & Restore
- **Workflow #19:** Cost Monitoring

---

## Notes

- **Stopped EC2 instances:** No compute charges, but you still pay for EBS volumes (~$1/month per 10GB)
- **Stopped SageMaker notebooks:** No charges while stopped
- **Lambda/API Gateway:** Continue to work even with EC2/SageMaker stopped (serverless)
- **Best practice:** Stop instances at end of each work session, start when needed

---

*Last updated: October 3, 2025*
*Saves: ~$6-56/month depending on usage patterns*
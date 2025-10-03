# Phase 5: Machine Learning Infrastructure (SageMaker)

**Status:** ⏸️ PENDING
**Prerequisites:** Phase 2 & 3 complete (RDS populated with 6.7M plays)
**Estimated Time:** 6-12 hours
**Estimated Cost:** $7-75/month (usage-dependent)
**Started:** TBD
**Completed:** TBD

---

## Overview

Set up AWS SageMaker for machine learning model development and training. Use historical NBA data to build predictive models for game outcomes, player performance, and playoff predictions.

**This phase includes:**
- SageMaker Notebook instance for development
- SageMaker Training jobs for model training
- Feature engineering pipelines
- Model deployment (optional)

---

## Prerequisites

Before starting this phase:
- [ ] Phase 2 complete (6.7M plays in RDS)
- [ ] Phase 3 complete (RDS operational)
- [ ] S3 data lake accessible (Phase 1)
- [ ] IAM role with SageMaker/S3/RDS permissions

**See workflow #24 (AWS Resource Setup) for SageMaker provisioning.**

---

## Implementation Steps

### Sub-Phase 5.1: SageMaker Notebook Instance

**Status:** ⏸️ PENDING
**Time Estimate:** 2 hours
**Cost:** $2-10/month (stop when not in use)

**Follow these workflows:**
- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
- Workflow #32 ([RDS Connection](../claude_workflows/workflow_descriptions/32_rds_connection.md))

**Configuration steps:**
1. [ ] Create IAM role for SageMaker with S3/RDS access
2. [ ] Launch SageMaker notebook instance
3. [ ] Open JupyterLab and verify
4. [ ] Install custom packages
5. [ ] Test RDS and S3 connections

**Recommended configuration:**
- **Instance name:** `nba-ml-notebook`
- **Instance type:** ml.t3.medium (2 vCPUs, 4 GB RAM)
- **Platform:** Amazon Linux 2, Jupyter Lab 3
- **Volume size:** 20 GB
- **IAM role:** SageMaker execution role with S3/RDS access
- **VPC:** Same as RDS (for direct connection)
- **Cost:** $0.058/hour

**Package installation (in Jupyter terminal):**
```bash
pip install psycopg2-binary sqlalchemy pandas numpy \
            scikit-learn matplotlib seaborn tensorflow \
            xgboost lightgbm shap
```

**Test connections (in notebook):**
```python
# Test RDS connection
import psycopg2
conn = psycopg2.connect(
    host='nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com',
    database='nba_simulator',
    user='postgres',
    password='your_password'
)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM play_by_play')
print(f"Play-by-play rows: {cursor.fetchone()[0]:,}")
# Expected: 6,781,155

# Test S3 access
import boto3
s3 = boto3.client('s3')
response = s3.list_objects_v2(Bucket='nba-sim-raw-data-lake', MaxKeys=10)
print(f"S3 objects found: {len(response['Contents'])}")
# Expected: 10
```

**Validation:**
- [ ] Notebook status: InService
- [ ] JupyterLab accessible via browser
- [ ] RDS connection successful
- [ ] S3 access successful
- [ ] Python kernel starts without errors

---

### Sub-Phase 5.2: Feature Engineering

**Status:** ⏸️ PENDING
**Time Estimate:** 4-6 hours

**Follow these workflows:**
- Workflow #27 ([TDD Workflow](../claude_workflows/workflow_descriptions/27_tdd_workflow.md))
- Workflow #21 ([Data Validation](../claude_workflows/workflow_descriptions/21_data_validation.md))

**Feature engineering tasks:**
1. [ ] Extract team performance metrics (win rate, points per game, etc.)
2. [ ] Calculate player statistics (usage rate, efficiency, etc.)
3. [ ] Create time-series features (momentum, streaks, rest days)
4. [ ] Encode categorical variables (home/away, opponent, venue)
5. [ ] Store processed features in S3

**Example features to engineer:**
- Team stats: Win%, PPG, FG%, 3P%, FT%, Rebounds, Assists, Turnovers
- Player stats: PER, True Shooting%, Usage Rate, Win Shares
- Situational: Home/Away, Rest days, Back-to-back, Travel distance
- Historical: Head-to-head record, Recent form (last 10 games)

**Store features:**
```python
# Save engineered features to S3
import pandas as pd

features_df.to_parquet('s3://nba-sim-raw-data-lake/ml-features/game_features.parquet')
```

**Validation:**
- [ ] Features stored in S3
- [ ] No missing values in critical features
- [ ] Feature distributions reasonable
- [ ] Train/test split prepared

---

### Sub-Phase 5.3: Model Development

**Status:** ⏸️ PENDING
**Time Estimate:** 4-8 hours

**Follow these workflows:**
- Workflow #27 ([TDD Workflow](../claude_workflows/workflow_descriptions/27_tdd_workflow.md))
- Workflow #16 ([Testing](../claude_workflows/workflow_descriptions/16_testing.md))

**Model development steps:**
1. [ ] Baseline model (logistic regression)
2. [ ] Tree-based models (XGBoost, LightGBM)
3. [ ] Neural networks (TensorFlow/PyTorch)
4. [ ] Ensemble methods
5. [ ] Model evaluation and selection

**Example training code:**
```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

# Load features
X = features_df.drop('home_win', axis=1)
y = features_df['home_win']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])

print(f"Accuracy: {accuracy:.3f}")
print(f"AUC: {auc:.3f}")
```

**Validation:**
- [ ] Model trains without errors
- [ ] Accuracy > 60% (better than random)
- [ ] AUC > 0.65
- [ ] Feature importance makes sense

---

### Sub-Phase 5.4: SageMaker Training Jobs

**Status:** ⏸️ PENDING
**Time Estimate:** 4-8 hours
**Cost:** $5-50/month (varies by experimentation)

**Follow these workflows:**
- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
- Workflow #16 ([Testing](../claude_workflows/workflow_descriptions/16_testing.md))

**Training job setup:**
1. [ ] Prepare training script (`train.py`)
2. [ ] Upload training data to S3
3. [ ] Create SageMaker training job
4. [ ] Monitor training progress
5. [ ] Retrieve model artifacts

**Training instance options:**
- **ml.m5.large:** $0.134/hour (small datasets)
- **ml.m5.xlarge:** $0.269/hour (recommended)
- **ml.m5.2xlarge:** $0.538/hour (large datasets)

**Recommendation:** ml.m5.xlarge for typical training

**Create training job (CLI):**
```bash
aws sagemaker create-training-job \
  --training-job-name nba-game-predictor-001 \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/SageMakerRole \
  --algorithm-specification TrainingImage=sklearn,TrainingInputMode=File \
  --input-data-config \
    '[{"ChannelName":"training","DataSource":{"S3DataSource":{"S3Uri":"s3://nba-sim-raw-data-lake/ml-features/"}}}]' \
  --output-data-config S3OutputPath=s3://nba-sim-raw-data-lake/ml-models/ \
  --resource-config InstanceType=ml.m5.xlarge,InstanceCount=1,VolumeSizeInGB=20 \
  --stopping-condition MaxRuntimeInSeconds=3600
```

**Monitor training:**
```bash
# Check status
aws sagemaker describe-training-job --training-job-name nba-game-predictor-001

# View logs
aws logs tail /aws/sagemaker/TrainingJobs nba-game-predictor-001 --follow
```

**Validation:**
- [ ] Training job completes successfully
- [ ] Model artifacts saved to S3
- [ ] Metrics logged to CloudWatch
- [ ] Cost within budget

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| **SageMaker Notebook** | ml.t3.medium | $2-10 | Stop when not in use |
| (40 hrs/month) | 2 vCPUs, 4 GB RAM | $2.32 | $0.058/hr × 40 hrs |
| (100 hrs/month) | 2 vCPUs, 4 GB RAM | $5.80 | $0.058/hr × 100 hrs |
| | | | |
| **Training Jobs** | ml.m5.xlarge | $5-50 | Varies by experimentation |
| (10 jobs × 30 min) | 4 vCPUs, 16 GB RAM | $1.35 | $0.269/hr × 5 hrs |
| (100 jobs × 30 min) | 4 vCPUs, 16 GB RAM | $13.45 | $0.269/hr × 50 hrs |
| | | | |
| **Storage** | S3 for features/models | ~$0.50 | ~20 GB × $0.023/GB |
| | | | |
| **Total (Light Use)** | | **~$7/month** | Notebook + few training jobs |
| **Total (Moderate Use)** | | **~$20/month** | Regular experimentation |
| **Total (Heavy Use)** | | **~$65/month** | Intensive development |

**Recommendation:** Start with light use ($7-10/month), scale as needed

---

## Instance Management

**SageMaker Notebook:**
```bash
# Stop when not in use
aws sagemaker stop-notebook-instance --notebook-instance-name nba-ml-notebook

# Start when needed
aws sagemaker start-notebook-instance --notebook-instance-name nba-ml-notebook

# Check status
aws sagemaker describe-notebook-instance --notebook-instance-name nba-ml-notebook
```

**Cost optimization:**
- Stop notebook when not actively developing
- Use Spot instances for training (70% discount, may be interrupted)
- Store only essential data in S3 (delete intermediate files)

---

## ML Workflows

**Typical development cycle:**

1. **Feature engineering** (in notebook):
   - Query RDS for raw data
   - Transform and create features
   - Save to S3 as Parquet

2. **Model prototyping** (in notebook):
   - Load features from S3
   - Train models locally
   - Evaluate performance

3. **Production training** (SageMaker job):
   - Scale to full dataset
   - Hyperparameter tuning
   - Save best model

4. **Model deployment** (optional):
   - Create SageMaker endpoint
   - Real-time predictions

---

## Troubleshooting

**Common issues:**

1. **Notebook won't start**
   - Check IAM role has SageMaker permissions
   - Verify VPC/subnet configuration
   - Check service quotas (default: 2 instances)

2. **Can't connect to RDS from notebook**
   - RDS security group must allow SageMaker security group
   - Or allow VPC CIDR range
   - See workflow #32 for connection troubleshooting

3. **Training job fails**
   - Check training script for errors
   - Verify S3 paths are correct
   - Review CloudWatch logs for details

4. **Out of memory**
   - Use larger instance type (ml.m5.2xlarge)
   - Or reduce batch size in training script
   - Or sample data for development

---

## Success Criteria

Phase complete when:
- [ ] SageMaker notebook operational
- [ ] Features engineered and stored in S3
- [ ] Baseline model trained (accuracy > 60%)
- [ ] Training job completes successfully
- [ ] Model artifacts saved to S3
- [ ] Can load and test trained model
- [ ] Cost within budget ($7-75/month)
- [ ] Documentation complete

---

## Next Steps

After completing this phase:
1. [ ] Update PROGRESS.md status
2. [ ] Document model performance metrics
3. [ ] Optionally proceed to [Phase 6: Enhancements](PHASE_6_ENHANCEMENTS.md)
4. [ ] Or deploy models for production use

---

## Model Use Cases

**Potential ML applications:**

1. **Game outcome prediction**
   - Input: Team stats, home/away, rest days
   - Output: Win probability, predicted score

2. **Player performance prediction**
   - Input: Player stats, opponent, minutes
   - Output: Points, rebounds, assists

3. **Playoff prediction**
   - Input: Regular season stats
   - Output: Playoff probability, seeding

4. **Injury risk prediction**
   - Input: Minutes played, back-to-backs, age
   - Output: Injury probability

5. **Trade value analysis**
   - Input: Player stats, contract, age
   - Output: Fair trade value, impact on team

---

*Last updated: 2025-10-02*
*Status: Planning complete, ready for implementation*
*Estimated implementation time: 6-12 hours*
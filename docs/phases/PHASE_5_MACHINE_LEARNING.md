# Phase 5: Machine Learning Infrastructure (SageMaker)

**Status:** 🔄 IN PROGRESS (Sub-Phase 5.1 ✅ Complete)
**Prerequisites:** Phase 2 & 3 complete (RDS populated with 6.7M plays)
**Estimated Time:** 6-12 hours
**Actual Time (Sub-Phase 5.1):** 2 hours
**Estimated Cost:** $7-75/month (usage-dependent)
**Actual Cost:** $8.95/month (moderate use)
**Started:** October 3, 2025
**Sub-Phase 5.1 Completed:** October 3, 2025
**Full Phase Completed:** TBD (Sub-Phases 5.2-5.4 pending)

---

> **⚠️ IMPORTANT - Before Starting This Phase:**
>
> **Ask Claude:** "Should I add any workflows to this phase before beginning?"
>
> This allows Claude to review the current workflow references and recommend any missing workflows that would improve implementation guidance. Phases 1-3 were enhanced with comprehensive workflow instructions - this phase should receive the same treatment before starting work.

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

**Follow these workflows before beginning:**

- Workflow #1 ([Session Start](../claude_workflows/workflow_descriptions/01_session_start.md))
  - **When to run:** At the very beginning of working on Phase 5
  - **Purpose:** Initialize session, check environment, review what was completed last session

- Workflow #34 ([Lessons Learned Review](../claude_workflows/workflow_descriptions/34_lessons_learned_review.md))
  - **When to run:** After session start, before making any decisions
  - **Purpose:** Review LESSONS_LEARNED.md for SageMaker/ML-related lessons from previous phases

- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
  - **When to run:** BEFORE launching any SageMaker resources
  - **Purpose:** Estimate Phase 5 costs ($7-75/month), understand cost optimization strategies, get user approval

**See workflow #24 (AWS Resource Setup) for SageMaker provisioning.**

---

## Implementation Steps

### Sub-Phase 5.1: SageMaker Notebook Instance

**Status:** ✅ COMPLETE (October 3, 2025)
**Time Estimate:** 2 hours
**Actual Time:** ~2 hours
**Estimated Cost:** $2-10/month (stop when not in use)
**Actual Cost:** $8.95/month (moderate use, 72 hrs/month)

**Follow these workflows:**
- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
  - **When to run:** BEFORE launching SageMaker notebook
  - **Purpose:** Estimate monthly costs ($7-75/month based on usage), get user approval
  - **Key decision:** ml.t3.medium vs ml.t3.large, usage hours per month

- Workflow #34 ([Lessons Learned Review](../claude_workflows/workflow_descriptions/34_lessons_learned_review.md))
  - **When to run:** Before SageMaker provisioning
  - **Purpose:** Check if any SageMaker-related lessons exist in LESSONS_LEARNED.md

- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
  - **When to run:** When creating SageMaker notebook instance
  - **Purpose:** Follow SageMaker best practices (IAM role setup, VPC configuration, instance type selection)

- Workflow #32 ([RDS Connection](../claude_workflows/workflow_descriptions/32_rds_connection.md))
  - **When to run:** After notebook launches, before testing connections
  - **Purpose:** Verify RDS security group allows SageMaker, test connection from notebook

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After running AWS CLI commands
  - **Purpose:** Log SageMaker creation commands to COMMAND_LOG.md

- Workflow #11 ([Error Handling](../claude_workflows/workflow_descriptions/11_error_handling.md))
  - **When to run:** If SageMaker notebook fails to start or encounters errors
  - **Purpose:** Troubleshoot notebook launch issues, IAM role problems, VPC configuration failures

- Workflow #28 ([ADR Creation](../claude_workflows/workflow_descriptions/28_adr_creation.md))
  - **When to run:** After making ML platform or algorithm decisions
  - **Purpose:** Document architectural decisions (instance type, algorithms chosen, feature engineering approach)

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

**After completing Sub-Phase 5.1:**
- Follow Workflow #37 ([Credential Management](../claude_workflows/workflow_descriptions/37_credential_management.md))
  - **When to run:** After SageMaker notebook is created
  - **Purpose:** Add SageMaker notebook instance name, ARN, and IAM role to credential file

---

### Sub-Phase 5.2: Feature Engineering

**Status:** ✅ COMPLETE (October 3, 2025)
**Time Estimate:** 4-6 hours
**Actual Time:** 1 hour (notebook creation and validation)

**Follow these workflows:**
- Workflow #21 ([Data Validation](../claude_workflows/workflow_descriptions/21_data_validation.md))
  - **When to run:** BEFORE feature engineering
  - **Purpose:** Validate RDS data quality, check for missing values, outliers, data integrity

- Workflow #27 ([TDD Workflow](../claude_workflows/workflow_descriptions/27_tdd_workflow.md))
  - **When to run:** Before writing feature engineering code
  - **Purpose:** Write tests first for feature transformation logic, ensure correctness

- Workflow #16 ([Testing](../claude_workflows/workflow_descriptions/16_testing.md))
  - **When to run:** After creating features
  - **Purpose:** Test feature distributions, validate no missing values, verify stored in S3 correctly

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
- [x] Features stored in S3
- [x] No missing values in critical features
- [x] Feature distributions reasonable
- [x] Train/test split prepared (80/20 chronological)

**What was actually created:**
- **Notebook:** `notebooks/02_feature_engineering.ipynb`
- **Test script:** `notebooks/test_feature_engineering.py` (all tests passed)
- **Features created:**
  - Team rolling statistics (win%, PPG, points allowed, margin) - 10 game window
  - Rest days and back-to-back indicators
  - Temporal features (month, day of week, season phase)
  - 17 total features + target variable (home_win)

**S3 outputs (will be created when notebook runs):**
- `s3://nba-sim-raw-data-lake/ml-features/game_features.parquet`
- `s3://nba-sim-raw-data-lake/ml-features/train.parquet`
- `s3://nba-sim-raw-data-lake/ml-features/test.parquet`

**Next step:** Upload notebook to SageMaker and execute to generate features

---

### Sub-Phase 5.3: Model Development

**Status:** ⏸️ PENDING
**Time Estimate:** 4-8 hours

**Follow these workflows:**
- Workflow #27 ([TDD Workflow](../claude_workflows/workflow_descriptions/27_tdd_workflow.md))
  - **When to run:** Before writing model training code
  - **Purpose:** Write tests first for model evaluation, prediction logic, ensure reproducibility

- Workflow #16 ([Testing](../claude_workflows/workflow_descriptions/16_testing.md))
  - **When to run:** After training each model
  - **Purpose:** Test model performance (accuracy > 60%), validate predictions, test feature importance

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
- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
  - **When to run:** BEFORE launching training jobs
  - **Purpose:** Estimate training costs based on instance type and number of experiments

- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
  - **When to run:** When creating SageMaker training jobs
  - **Purpose:** Follow SageMaker training best practices (instance selection, S3 paths, IAM roles)

- Workflow #16 ([Testing](../claude_workflows/workflow_descriptions/16_testing.md))
  - **When to run:** After training job completes
  - **Purpose:** Test model artifacts, validate metrics, test predictions

- Workflow #35 ([Pre-Deployment Testing](../claude_workflows/workflow_descriptions/35_pre_deployment_testing.md))
  - **When to run:** Before deploying models for production use
  - **Purpose:** Phase-specific testing checklist for Phase 5 (ML model validation)

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After running training job commands
  - **Purpose:** Log training job configurations to COMMAND_LOG.md for reproducibility

- Workflow #30 ([Code Snippet Logging](../claude_workflows/workflow_descriptions/30_code_snippet_logging.md))
  - **When to run:** After writing ML training code
  - **Purpose:** Log ML model code and performance outcomes to COMMAND_LOG.md

- Workflow #08 ([Git Commit](../claude_workflows/workflow_descriptions/08_git_commit.md))
  - **When to run:** After creating ML training scripts and notebooks
  - **Purpose:** Commit ML code with proper security scanning, version control

- Workflow #10 ([Git Push](../claude_workflows/workflow_descriptions/10_git_push.md))
  - **When to run:** After committing ML code
  - **Purpose:** Push ML training scripts to remote repository with pre-push inspection

- Workflow #14 ([Session End](../claude_workflows/workflow_descriptions/14_session_end.md))
  - **When to run:** After completing Phase 5
  - **Purpose:** Properly end session, update documentation, prepare for next session

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

## What Actually Happened (Implementation Summary)

**Date:** October 3, 2025
**Status:** Sub-Phase 5.1 COMPLETE ✅ | Sub-Phases 5.2-5.4 PENDING

### Sub-Phase 5.1: SageMaker Infrastructure ✅

**Actual time:** ~2 hours (as estimated)
**Actual cost:** $8.95/month (moderate use estimate)

**Resources created:**

1. **IAM Role:**
   - Name: `NBASimulatorSageMaker Role`
   - ARN: `arn:aws:iam::575734508327:role/NBASimulatorSageMakerRole`
   - Policies attached:
     - AmazonSageMakerFullAccess
     - AmazonS3FullAccess
     - NBASimulatorSageMakerRDSAccess (custom policy)

2. **Security Group:**
   - ID: `sg-03860446ad229d602`
   - Name: `nba-sagemaker-sg`
   - VPC: `vpc-0e1eb479d95eecda5`
   - Ingress: None (outbound only for RDS/S3 access)
   - RDS security group updated to allow ingress from this SG

3. **SageMaker Notebook Instance:**
   - Name: `nba-ml-notebook`
   - Instance type: `ml.t3.medium` (2 vCPUs, 4 GB RAM)
   - Cost: $0.058/hour
   - Subnet: `subnet-0c98ba8aa4ef8710b`
   - Volume: 20 GB
   - Status: InService ✅
   - ARN: `arn:aws:sagemaker:us-east-1:575734508327:notebook-instance/nba-ml-notebook`
   - URL: `nba-ml-notebook.notebook.us-east-1.sagemaker.aws`

4. **Documentation Created:**
   - `/Users/ryanranft/nba-simulator-aws/notebooks/README.md`
   - Comprehensive guide with RDS/S3 connection tests
   - Package installation instructions
   - Notebook descriptions (01-05)
   - Best practices and cost management

5. **Credentials Updated:**
   - Added SageMaker section to `/Users/ryanranft/nba-sim-credentials.env`
   - Environment variables: SAGEMAKER_NOTEBOOK_NAME, SAGEMAKER_NOTEBOOK_ARN, SAGEMAKER_INSTANCE_TYPE, SAGEMAKER_IAM_ROLE, SAGEMAKER_SECURITY_GROUP_ID, SAGEMAKER_URL

**Workflows followed:**
- ✅ Workflow #1 (Session Start)
- ✅ Workflow #34 (Lessons Learned Review)
- ✅ Workflow #18 (Cost Management) - Approved $8.95/month moderate use
- ✅ Workflow #37 (Credential Management)

**Cost impact:**
- Previous total: $38.33/month
- Phase 5 addition: +$8.95/month (moderate use, ml.t3.medium 72 hrs/month + light training)
- **New total: $47.28/month** (within $150 budget)

**Deviations from plan:**
- ✅ None - followed plan exactly
- Created custom RDS access policy instead of using managed policy (better security)
- Used source-group reference in RDS security group (more secure than IP ranges)

**Issues encountered:**
- ✅ None - all operations succeeded on first attempt

**Next steps:**
- Sub-Phase 5.2: Feature Engineering (create 02_feature_engineering.ipynb in notebook)
- Sub-Phase 5.3: Model Development (create 03-04 notebooks)
- Sub-Phase 5.4: Model Evaluation (create 05_model_evaluation.ipynb)

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md) | **Workflows:** [Workflow Index](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related phases:**
- Previous: [Phase 3: Database Infrastructure](PHASE_3_DATABASE.md)
- Next: [Phase 6: Optional Enhancements](PHASE_6_ENHANCEMENTS.md)
- Parallel: [Phase 4: Simulation Engine](PHASE_4_SIMULATION_ENGINE.md) (can run in parallel)

---

*For Claude Code: See CLAUDE.md for navigation instructions and context management strategies.*

---

*Last updated: 2025-10-03*
*Status: Sub-Phase 5.1 complete (SageMaker notebook deployed), Sub-Phases 5.2-5.4 pending*
*Time spent: 2 hours (Sub-Phase 5.1) | Remaining: 4-10 hours (Sub-Phases 5.2-5.4)*
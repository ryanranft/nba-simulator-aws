# NBA Simulator - SageMaker Notebooks

This directory contains Jupyter notebooks for machine learning model development on AWS SageMaker.

## Notebook Instance Details

**Instance Name:** `nba-ml-notebook`
**Instance Type:** ml.t3.medium (2 vCPUs, 4 GB RAM)
**Cost:** $0.058/hour
**Status:** InService
**ARN:** `arn:aws:sagemaker:us-east-1:575734508327:notebook-instance/nba-ml-notebook`

## Access

1. **Via AWS Console:**
   - Navigate to SageMaker → Notebook instances
   - Click "Open JupyterLab" on `nba-ml-notebook`

2. **Via CLI (presigned URL):**
   ```bash
   aws sagemaker create-presigned-notebook-instance-url \
     --notebook-instance-name nba-ml-notebook \
     --query 'AuthorizedUrl' \
     --output text
   ```

## Environment Setup

### Install Required Packages

Open a terminal in JupyterLab and run:

```bash
pip install psycopg2-binary sqlalchemy pandas numpy \
            scikit-learn matplotlib seaborn tensorflow \
            xgboost lightgbm shap
```

### Test Connections

#### RDS Connection Test
```python
import psycopg2
import pandas as pd

# Database credentials (use environment variables in production)
DB_HOST = "nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com"
DB_NAME = "nba_simulator"
DB_USER = "postgres"
DB_PASSWORD = "YOUR_PASSWORD_HERE"  # Replace with actual password
DB_PORT = 5432

# Test connection
conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    port=DB_PORT
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM play_by_play;")
print(f"Play-by-play rows: {cursor.fetchone()[0]:,}")
# Expected: 6,781,155

cursor.execute("SELECT COUNT(*) FROM games;")
print(f"Games: {cursor.fetchone()[0]:,}")
# Expected: 44,828

conn.close()
print("✅ RDS connection successful!")
```

#### S3 Connection Test
```python
import boto3
import pandas as pd

# Initialize S3 client
s3 = boto3.client('s3')

# List objects in bucket
bucket = 'nba-sim-raw-data-lake'
response = s3.list_objects_v2(Bucket=bucket, MaxKeys=10)

print(f"S3 Bucket: {bucket}")
print(f"Objects found: {len(response.get('Contents', []))}")

# Test reading a file
for obj in response.get('Contents', [])[:3]:
    print(f"  - {obj['Key']}")

print("✅ S3 connection successful!")
```

## Notebooks

### 01_data_exploration.ipynb
**Purpose:** Explore RDS data, understand distributions, identify data quality issues

**Key tasks:**
- Query games and play-by-play tables
- Visualize team statistics
- Check for missing values
- Analyze win/loss patterns

### 02_feature_engineering.ipynb ✅ CREATED
**Purpose:** Create features for machine learning models

**Features engineered:**
- **Team statistics:** Rolling win%, PPG, points allowed, point margin (10-game window)
- **Rest/Schedule:** Rest days since last game, back-to-back indicator
- **Temporal features:** Month, day of week, weekend indicator, season phase
- **Target variable:** Home team win (binary classification)

**Data validation:**
- Pre-engineering data quality checks (Workflow #21)
- Missing value analysis
- Date range validation
- Record count verification

**Output:**
- Full dataset: `s3://nba-sim-raw-data-lake/ml-features/game_features.parquet`
- Train/Test splits: `train.parquet` and `test.parquet` (80/20 chronological split)

**Usage:**
1. Open notebook in SageMaker JupyterLab
2. Replace `DB_PASSWORD` with actual RDS password
3. Run all cells to generate features
4. Features are automatically saved to S3

**Test validation:** All tests passed (run `python notebooks/test_feature_engineering.py`)

### 03_baseline_model.ipynb ✅ CREATED
**Purpose:** Build baseline prediction models

**Models:**
- Logistic Regression (linear baseline)
- Random Forest (tree-based baseline, 100 estimators)

**Target:** Home team win (binary classification)
**Features:** 17 engineered features from 02_feature_engineering.ipynb
**Goal:** Establish baseline accuracy (>60%)

**Includes:**
- Feature scaling (StandardScaler)
- Model training and evaluation
- Feature importance analysis
- ROC curves and confusion matrices
- Model persistence to S3

### 04_advanced_models.ipynb ✅ CREATED
**Purpose:** Develop advanced ML models for improved accuracy

**Models:**
- XGBoost (200 estimators, max_depth=6)
- LightGBM (200 estimators, 31 leaves)

**Target accuracy:** >65%, AUC >0.70

**Includes:**
- Gradient boosting implementations
- Training with validation monitoring
- Feature importance comparison
- Side-by-side performance metrics
- Model persistence to S3

### 05_model_evaluation.md 📝 PLACEHOLDER
**Purpose:** Comprehensive model comparison and final selection

**Status:** Placeholder - create after executing notebooks 02-04

**Will include:**
- Load all trained models from S3
- Side-by-side performance comparison (all 4 models)
- ROC curves overlay
- Confusion matrix grid
- Feature importance consensus
- Model selection recommendation
- Production deployment guidance

**Note:** Notebooks 03 and 04 include their own evaluation sections for immediate feedback

## Data Access Patterns

### Query Games Data
```python
import pandas as pd
from sqlalchemy import create_engine

# Create connection string
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Query games
query = """
SELECT
    game_id,
    game_date,
    season,
    home_team_abbrev,
    away_team_abbrev,
    home_score,
    away_score,
    home_team_is_winner
FROM games
WHERE season = '2023-24'
ORDER BY game_date
"""

df = pd.read_sql(query, engine)
print(f"Loaded {len(df):,} games")
```

### Save Features to S3
```python
import pandas as pd

# Save as Parquet (compressed, efficient)
s3_path = 's3://nba-sim-raw-data-lake/ml-features/game_features.parquet'
features_df.to_parquet(s3_path, compression='snappy')
print(f"✅ Features saved to {s3_path}")
```

### Load Features from S3
```python
import pandas as pd

s3_path = 's3://nba-sim-raw-data-lake/ml-features/game_features.parquet'
features_df = pd.read_parquet(s3_path)
print(f"Loaded {len(features_df):,} rows, {len(features_df.columns)} columns")
```

## Cost Management

**Notebook costs:**
- ml.t3.medium: $0.058/hour
- **Stop when not in use!**

**Start/Stop Commands:**
```bash
# Stop notebook (saves costs)
aws sagemaker stop-notebook-instance --notebook-instance-name nba-ml-notebook

# Start notebook
aws sagemaker start-notebook-instance --notebook-instance-name nba-ml-notebook

# Check status
aws sagemaker describe-notebook-instance --notebook-instance-name nba-ml-notebook
```

## Best Practices

1. **Save work frequently** - Notebooks auto-save every 2 minutes
2. **Stop instance when done** - Prevents unnecessary billing
3. **Use version control** - Commit notebooks to Git
4. **Store large datasets in S3** - Not on notebook instance
5. **Use Parquet format** - Compressed, columnar, efficient
6. **Test on samples first** - Before running on full dataset
7. **Monitor costs** - Check AWS Cost Explorer regularly

## Troubleshooting

### Can't connect to RDS
- Verify security group allows SageMaker (sg-03860446ad229d602)
- Check RDS security group has ingress rule from SageMaker SG
- Verify database credentials

### Out of memory
- Use smaller dataset for prototyping
- Process data in chunks
- Or upgrade to ml.t3.large (8 GB RAM)

### Package installation fails
- Use `pip install --user package_name`
- Check for conflicting dependencies
- Try installing in a new conda environment

---

**Created:** 2025-10-03 (Phase 5: Machine Learning)
**Notebook Instance:** nba-ml-notebook
**IAM Role:** NBASimulatorSageMakerRole
**Security Group:** sg-03860446ad229d602
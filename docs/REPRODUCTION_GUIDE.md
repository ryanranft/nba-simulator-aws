# Multi-Sport Data Pipeline Reproduction Guide

<!-- AUTO-UPDATE TRIGGER: When adapting this project for new sports (NHL, NCAA Basketball, etc.) -->
<!-- LAST UPDATED: 2025-10-01 -->

**Purpose:** Step-by-step guide to reproduce this NBA pipeline for other sports (NHL, NCAA Basketball, NFL, MLB, etc.)

**Estimated Time:** 2-3 days per sport (assuming similar data volume)

**Cost per Sport:** ~$95-130/month per active pipeline

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: S3 Data Lake Setup](#phase-1-s3-data-lake-setup)
3. [Phase 2: AWS Glue Configuration](#phase-2-aws-glue-configuration)
4. [Phase 3: RDS PostgreSQL Database](#phase-3-rds-postgresql-database)
5. [Phase 4: EC2 Simulation Engine](#phase-4-ec2-simulation-engine)
6. [Phase 5: SageMaker ML Pipeline](#phase-5-sagemaker-ml-pipeline)
7. [Sport-Specific Considerations](#sport-specific-considerations)
8. [Common Issues & Solutions](#common-issues--solutions)

---

## Prerequisites

### 1. AWS Account Setup
```bash
# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)

# Verify configuration
aws sts get-caller-identity
```

### 2. Local Environment Setup
```bash
# Install Miniconda (if not already installed)
# Download from: https://docs.conda.io/en/latest/miniconda.html

# Create conda environment (use Python 3.11 for AWS Glue 4.0 compatibility)
conda create -n <sport>-aws python=3.11
conda activate <sport>-aws

# Install required packages
pip install boto3 pandas pytest moto python-dotenv

# Verify Python version
python --version  # Should show 3.11.x
```

### 3. Project Structure Setup
```bash
# Clone this repository as template
cd ~/Desktop
git clone git@github.com:ryanranft/nba-simulator-aws.git <sport>-simulator-aws
cd <sport>-simulator-aws

# Update repository name
git remote set-url origin git@github.com:ryanranft/<sport>-simulator-aws.git

# Create initial commit
git add .
git commit -m "Initial commit: Adapted from NBA simulator template

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Phase 1: S3 Data Lake Setup

**Time:** 4-8 hours (depending on data volume)
**Cost:** ~$2.74/month for 120 GB (S3 Standard, us-east-1)

### Step 1.1: Prepare Source Data

```bash
# Organize your source data into logical folders
# Example structure:
/Users/username/data/<sport>/
├── games/           # Game schedules and results
├── player_stats/    # Player statistics
├── team_stats/      # Team statistics
└── play_by_play/    # Play-by-play data (if available)

# Count total files and estimate size
find /Users/username/data/<sport>/ -type f | wc -l
du -sh /Users/username/data/<sport>/
```

### Step 1.2: Create S3 Bucket

```bash
# Choose a unique bucket name
BUCKET_NAME="<sport>-sim-raw-data-lake"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Enable versioning (optional but recommended)
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Verify bucket creation
aws s3 ls | grep $BUCKET_NAME
```

### Step 1.3: Upload Data to S3

```bash
# Upload with progress tracking
aws s3 sync /Users/username/data/<sport>/ s3://$BUCKET_NAME/ \
  --storage-class STANDARD \
  --no-progress

# Verify upload
aws s3 ls s3://$BUCKET_NAME/ --recursive --summarize | tail -2
```

**Expected Output:**
```
Total Objects: XXXXX
Total Size: XXX GB
```

---

## Phase 2: AWS Glue Configuration

**Time:** 2-4 hours (setup) + 2-3 hours (crawler runtime for large datasets)
**Cost:** ~$13/month

### Step 2.1: Create Glue Database

```bash
# Create database for raw data
aws glue create-database \
  --database-input "{
    \"Name\": \"<sport>_raw_data\",
    \"Description\": \"Raw <SPORT> game data from ESPN/source\"
  }"

# Verify database creation
aws glue get-databases --query 'DatabaseList[*].Name' --output table
```

### Step 2.2: Create IAM Role for Glue

```bash
# Create trust policy file
cat > /tmp/glue-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name AWSGlueServiceRole-<SPORT>Simulator \
  --assume-role-policy-document file:///tmp/glue-trust-policy.json

# Attach AWS managed policy for Glue
aws iam attach-role-policy \
  --role-name AWSGlueServiceRole-<SPORT>Simulator \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole

# Create S3 access policy
cat > /tmp/s3-access-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::$BUCKET_NAME",
        "arn:aws:s3:::$BUCKET_NAME/*"
      ]
    }
  ]
}
EOF

# Create and attach S3 policy
aws iam put-role-policy \
  --role-name AWSGlueServiceRole-<SPORT>Simulator \
  --policy-name S3Access \
  --policy-document file:///tmp/s3-access-policy.json

# Get role ARN (save this for next step)
aws iam get-role \
  --role-name AWSGlueServiceRole-<SPORT>Simulator \
  --query 'Role.Arn' \
  --output text
```

### Step 2.3: Create Glue Crawler

**IMPORTANT:** For datasets >100K files, the crawler may encounter OutOfMemoryError. See [Common Issues](#glue-crawler-out-of-memory-error) for solutions.

```bash
# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

# Define S3 targets (adjust paths based on your data structure)
cat > /tmp/crawler-targets.json << EOF
{
  "S3Targets": [
    {"Path": "s3://$BUCKET_NAME/games/"},
    {"Path": "s3://$BUCKET_NAME/player_stats/"},
    {"Path": "s3://$BUCKET_NAME/team_stats/"},
    {"Path": "s3://$BUCKET_NAME/play_by_play/"}
  ]
}
EOF

# Create crawler
aws glue create-crawler \
  --name <sport>-data-crawler \
  --role arn:aws:iam::$ACCOUNT_ID:role/AWSGlueServiceRole-<SPORT>Simulator \
  --database-name <sport>_raw_data \
  --targets file:///tmp/crawler-targets.json \
  --table-prefix raw_ \
  --schema-change-policy '{"UpdateBehavior":"UPDATE_IN_DATABASE","DeleteBehavior":"LOG"}' \
  --recrawl-policy '{"RecrawlBehavior":"CRAWL_EVERYTHING"}'

# Start crawler
aws glue start-crawler --name <sport>-data-crawler

# Monitor crawler status (check every 30 seconds)
watch -n 30 'aws glue get-crawler --name <sport>-data-crawler --query "Crawler.State" --output text'
```

**Expected States:**
- `RUNNING` - Crawler is scanning data
- `READY` - Crawler finished successfully
- `FAILED` - See [Common Issues](#glue-crawler-out-of-memory-error)

---

## Phase 3: RDS PostgreSQL Database

**Time:** 3-4 hours
**Cost:** ~$29/month (db.t3.small) or ~$15/month (db.t3.micro)

### Step 3.1: Design Database Schema

Create `sql/create_tables.sql` based on your sport's data structure.

**Template for common sports tables:**

```sql
-- Teams Table (universal for all sports)
CREATE TABLE IF NOT EXISTS teams (
    team_id VARCHAR(50) PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_abbreviation VARCHAR(10),
    conference VARCHAR(20),
    division VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Players Table (universal)
CREATE TABLE IF NOT EXISTS players (
    player_id VARCHAR(50) PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    position VARCHAR(10),
    jersey_number VARCHAR(10),
    team_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE SET NULL
);

-- Games Table (universal)
CREATE TABLE IF NOT EXISTS games (
    game_id VARCHAR(50) PRIMARY KEY,
    game_date DATE NOT NULL,
    season VARCHAR(20),
    home_team_id VARCHAR(50) NOT NULL,
    away_team_id VARCHAR(50) NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    venue VARCHAR(200),
    attendance INTEGER,
    game_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id) ON DELETE CASCADE
);

-- Sport-specific stats tables will vary
-- See sport-specific sections below for examples
```

### Step 3.2: Create Performance Indexes

Create `sql/create_indexes.sql`:

```sql
-- Universal indexes (apply to all sports)
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_season ON games(season);
CREATE INDEX IF NOT EXISTS idx_games_home_team ON games(home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away_team ON games(away_team_id);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(player_name);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(team_name);
```

### Step 3.3: Launch RDS Instance

```bash
# Get default VPC ID
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)

# Get your public IP (for security group)
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name <sport>-rds-access \
  --description "PostgreSQL access for <SPORT> simulator" \
  --vpc-id $VPC_ID \
  --query 'GroupId' \
  --output text)

# Allow PostgreSQL access from your IP
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 5432 \
  --cidr $MY_IP/32

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier <sport>-sim-db \
  --db-instance-class db.t3.small \
  --engine postgres \
  --engine-version 15.14 \
  --master-username postgres \
  --master-user-password '<YourSecurePassword>' \
  --allocated-storage 20 \
  --storage-type gp3 \
  --vpc-security-group-ids $SG_ID \
  --db-name <sport>_simulator \
  --backup-retention-period 7 \
  --publicly-accessible \
  --no-multi-az \
  --region us-east-1

# Monitor instance creation (takes ~10-15 minutes)
watch -n 30 'aws rds describe-db-instances --db-instance-identifier <sport>-sim-db --query "DBInstances[0].DBInstanceStatus" --output text'

# Get endpoint when ready
aws rds describe-db-instances \
  --db-instance-identifier <sport>-sim-db \
  --query 'DBInstances[0].[Endpoint.Address,Endpoint.Port]' \
  --output table
```

### Step 3.4: Initialize Database Schema

```bash
# Get RDS endpoint
ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier <sport>-sim-db --query 'DBInstances[0].Endpoint.Address' --output text)

# Test connection
psql -h $ENDPOINT -U postgres -d <sport>_simulator -c "\l"

# Run table creation
psql -h $ENDPOINT -U postgres -d <sport>_simulator -f sql/create_tables.sql

# Create indexes
psql -h $ENDPOINT -U postgres -d <sport>_simulator -f sql/create_indexes.sql

# Verify tables
psql -h $ENDPOINT -U postgres -d <sport>_simulator -c "\dt"
```

---

## Phase 4: EC2 Simulation Engine

**Time:** 4-6 hours
**Cost:** ~$5-15/month (t3.medium, running 8 hrs/day)

*(Complete implementation coming soon)*

---

## Phase 5: SageMaker ML Pipeline

**Time:** 8-12 hours
**Cost:** ~$50/month (ml.t3.medium notebooks)

*(Complete implementation coming soon)*

---

## Sport-Specific Considerations

### NBA (This Project)
- **Data Volume:** 146,115 files, 119 GB
- **Seasons:** 1999-2025
- **Key Stats:** Points, rebounds, assists, steals, blocks, turnovers, shooting percentages
- **Special Considerations:** 48-minute games (4x 12-min quarters), 3-point line

### NHL (Hockey)
- **Expected Volume:** ~100K files, ~80 GB
- **Key Stats:** Goals, assists, plus/minus, shots, saves, penalties, faceoffs
- **Special Considerations:** 60-minute games (3x 20-min periods), power plays, goalie stats
- **Schema Changes:**
  - Add `goalie_stats` table
  - Add `penalties` table
  - Track ice time, not minutes played

### NCAA Basketball (Men's)
- **Expected Volume:** ~200K files, ~150 GB (more teams than NBA)
- **Key Stats:** Similar to NBA
- **Special Considerations:** 40-minute games (2x 20-min halves), different 3-point distance
- **Schema Changes:**
  - Add `conferences` and `tournament` tracking
  - Track eligibility years

### NFL (Football)
- **Expected Volume:** ~50K files, ~100 GB
- **Key Stats:** Passing yards, rushing yards, receptions, tackles, sacks, interceptions
- **Special Considerations:** Position-specific stats (QB vs RB vs WR)
- **Schema Changes:**
  - Separate tables by position group
  - Track drives and possessions
  - Add `downs` table for play-by-play

### MLB (Baseball)
- **Expected Volume:** ~300K files, ~200 GB (162-game seasons)
- **Key Stats:** Batting average, home runs, RBIs, ERA, strikeouts, walks
- **Special Considerations:** Pitcher vs batter stats
- **Schema Changes:**
  - Add `pitching_stats` table
  - Add `batting_stats` table
  - Track innings, not time

---

## Common Issues & Solutions

### Glue Crawler Out of Memory Error

**Symptom:** Crawler fails with "OutOfMemoryError" or "Internal Service Exception"

**Cause:** Default crawler configuration cannot handle 100K+ files

**Solutions:**

**Option 1: Partition S3 data and crawl incrementally**
```bash
# Instead of crawling all data at once, partition by season/year
aws glue create-crawler --name <sport>-crawler-2024 \
  --targets '{"S3Targets":[{"Path":"s3://<bucket>/games/2024/"}]}'

# Run separate crawlers for each year, then merge tables
```

**Option 2: Increase crawler DPU (Data Processing Units)**
```bash
# Update crawler configuration (requires AWS Support ticket)
# Request increase from default 2 DPU to 10 DPU
# Cost: ~$0.44/hour per DPU (so 10 DPU = $4.40/hour)
```

**Option 3: Skip Glue Crawler, manually define schemas**
```python
# Create Glue tables manually using boto3
import boto3

glue = boto3.client('glue')
glue.create_table(
    DatabaseName='<sport>_raw_data',
    TableInput={
        'Name': 'games',
        'StorageDescriptor': {
            'Columns': [...],
            'Location': 's3://<bucket>/games/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'SerdeInfo': {'SerializationLibrary': 'org.openx.data.jsonserde.JsonSerDe'}
        }
    }
)
```

**Recommended:** Use Option 1 for datasets >100K files.

### RDS Connection Timeout

**Symptom:** `psql: could not connect to server: Connection timed out`

**Solutions:**
1. Verify security group allows your IP on port 5432
2. Ensure `--publicly-accessible` was set during creation
3. Check your IP hasn't changed (use `curl https://checkip.amazonaws.com`)

### Cost Overruns

**Symptom:** AWS bill exceeds budget

**Prevention:**
```bash
# Set up billing alerts
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query 'Account' --output text) \
  --budget file://budget-config.json

# Stop non-essential resources when not in use
aws ec2 stop-instances --instance-ids <instance-id>
aws rds stop-db-instance --db-instance-identifier <db-id>
```

---

## Cost Summary by Sport

| Sport | Data Size | S3 | Glue | RDS | EC2 | SageMaker | **Total/Month** |
|-------|-----------|-----|------|-----|-----|-----------|-----------------|
| NBA | 119 GB | $2.74 | $13 | $29 | $10 | $50 | **$104.74** |
| NHL | ~80 GB | $1.84 | $13 | $29 | $10 | $50 | **$103.84** |
| NCAA BB | ~150 GB | $3.45 | $13 | $29 | $10 | $50 | **$105.45** |
| NFL | ~100 GB | $2.30 | $13 | $29 | $10 | $50 | **$104.30** |
| MLB | ~200 GB | $4.60 | $13 | $29 | $10 | $50 | **$106.60** |

**Notes:**
- Costs assume us-east-1 region
- EC2 cost assumes 8 hours/day usage
- RDS cost is for db.t3.small, always-on
- Multiply by number of sports you run simultaneously

---

## Next Steps

1. Adapt `PROGRESS.md` for your sport
2. Update `.env.example` with sport-specific variables
3. Modify `docs/STYLE_GUIDE.md` for sport-specific conventions
4. Create ADR-001 documenting why you chose this sport
5. Run `make inventory` to generate FILE_INVENTORY.md

---

**Last Updated:** 2025-10-01
**Maintained By:** Ryan Ranft
**Template Version:** 1.0 (based on NBA simulator v1.0)

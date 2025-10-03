# Workflow #33: Multi-Sport Pipeline Reproduction

**Category:** Project Setup
**Priority:** Low (only for new sport pipelines)
**When to Use:** When adapting this NBA pipeline for other sports (NHL, NCAA, NFL, MLB)
**Related Workflows:** #17 (Environment Setup), #24 (AWS Resource Setup)

---

## Overview

This workflow provides a complete guide to reproduce the entire NBA simulator pipeline for other sports. Use this when you want to create a similar data pipeline for hockey, football, baseball, etc.

**Purpose:** Systematically adapt existing NBA infrastructure for new sports with minimal rework.

---

## When to Use This Workflow

✅ **USE when:**
- Starting a new sport analytics project
- Building similar ETL pipeline for different sport
- Replicating architecture for client/team
- Teaching others how to build sports data pipelines
- Creating portfolio of multi-sport simulators

❌ **DON'T USE when:**
- Just adding more NBA data (use existing pipeline)
- Building completely different type of project
- One-off data analysis (overkill for simple tasks)

---

## Prerequisites

### Before Starting

**Required:**
- [ ] AWS Account with billing enabled
- [ ] Source data available (ESPN, API, web scraping)
- [ ] Understanding of target sport's data structure
- [ ] Budget: ~$95-130/month per sport pipeline
- [ ] Time: 2-3 days for initial setup

**Recommended:**
- [ ] Completed NBA pipeline (to understand architecture)
- [ ] Read this project's README.md and PROGRESS.md
- [ ] Review docs/LESSONS_LEARNED.md (avoid known pitfalls)

---

## Estimated Costs Per Sport

**Monthly costs (full deployment):**
- S3 storage: $2-5/month (depends on data volume)
- RDS db.t3.small: $29/month
- Glue ETL jobs: $10-20/month (depends on frequency)
- EC2 t2.micro: $8-15/month
- SageMaker ml.t3.medium: $40-60/month
- **Total: $95-130/month**

**One-time setup:**
- Development time: 2-3 days
- Testing: 1-2 days
- **Total: 3-5 days**

---

## Phase 1: Local Environment Setup

### Step 1: Clone Template Repository

```bash
cd ~/Desktop

# Clone NBA project as template
git clone git@github.com:ryanranft/nba-simulator-aws.git <sport>-simulator-aws

cd <sport>-simulator-aws

# Update remote to new repository
git remote set-url origin git@github.com:ryanranft/<sport>-simulator-aws.git

# Create new repo on GitHub first, then push
git push -u origin main
```

### Step 2: Create Conda Environment

```bash
# Create environment (use Python 3.11 for AWS Glue 4.0 compatibility)
conda create -n <sport>-aws python=3.11

# Activate
conda activate <sport>-aws

# Install dependencies
pip install boto3 pandas pytest moto python-dotenv psycopg2-binary sqlalchemy

# Verify Python version
python --version
# Expected: Python 3.11.x
```

### Step 3: Update Project Files

**Files to update:**
- `README.md` - Change "NBA" to your sport name
- `PROGRESS.md` - Update phases with sport-specific tasks
- `.gitignore` - Add sport-specific patterns
- `environment.yml` - Rename environment

**Find and replace:**
```bash
# Replace all instances of "nba" with your sport
find . -type f -name "*.md" -exec sed -i '' 's/nba/<sport>/g' {} +
find . -type f -name "*.py" -exec sed -i '' 's/nba/<sport>/g' {} +

# Replace "NBA" with uppercase sport name
find . -type f -name "*.md" -exec sed -i '' 's/NBA/<SPORT>/g' {} +
```

---

## Phase 2: S3 Data Lake Setup

**Time:** 4-8 hours (depends on data volume)
**Cost:** ~$2-5/month

### Step 1: Prepare Source Data

**Organize your data:**
```bash
# Create data directory structure
mkdir -p data/<sport>/{games,player_stats,team_stats,play_by_play}

# Example for NHL:
data/nhl/
├── games/           # Game schedules and results
├── player_stats/    # Player statistics by game
├── team_stats/      # Team statistics by game
└── play_by_play/    # Play-by-play events (if available)
```

**Analyze data volume:**
```bash
# Count files
find data/<sport>/ -type f | wc -l

# Check total size
du -sh data/<sport>/

# Estimate S3 cost: size_in_GB × $0.023/GB/month
```

### Step 2: Create S3 Bucket

```bash
# Choose unique bucket name
BUCKET_NAME="<sport>-sim-raw-data-lake"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Enable versioning (recommended)
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Verify
aws s3 ls | grep $BUCKET_NAME
```

### Step 3: Upload Data to S3

```bash
# Upload all data
aws s3 sync data/<sport>/ s3://$BUCKET_NAME/raw-data/ \
  --storage-class STANDARD

# Monitor progress
aws s3 ls s3://$BUCKET_NAME/raw-data/ --recursive --summarize | tail -2
```

**Expected output:**
```
Total Objects: XXXXX
Total Size: XXX GB
```

---

## Phase 3: Data Quality Analysis

**Time:** 1-2 hours
**Purpose:** Understand your data before building ETL

### Step 1: Analyze Data Structure

```python
# Create script: scripts/analysis/analyze_<sport>_data.py
import json
from pathlib import Path
import random

def analyze_data_quality(data_dir, sample_size=200):
    """Analyze data quality for sport data files."""
    files = list(Path(data_dir).rglob('*.json'))
    sample = random.sample(files, min(sample_size, len(files)))

    valid_count = 0
    empty_count = 0
    error_count = 0

    for file_path in sample:
        try:
            with open(file_path) as f:
                data = json.load(f)

            # CUSTOMIZE THIS: Check for sport-specific data
            # Example for NHL:
            if 'plays' in data and len(data['plays']) > 0:
                valid_count += 1
            else:
                empty_count += 1

        except Exception as e:
            error_count += 1

    print(f"Sample size: {len(sample)}")
    print(f"Valid files: {valid_count} ({valid_count/len(sample)*100:.1f}%)")
    print(f"Empty files: {empty_count} ({empty_count/len(sample)*100:.1f}%)")
    print(f"Error files: {error_count} ({error_count/len(sample)*100:.1f}%)")

    return {
        'total_files': len(files),
        'valid_pct': valid_count / len(sample),
        'empty_pct': empty_count / len(sample)
    }

# Run analysis
results = analyze_data_quality('data/<sport>/play_by_play')
```

### Step 2: Document Data Structure

Create `docs/DATA_STRUCTURE_GUIDE.md`:

```markdown
# <SPORT> Data Structure Guide

## JSON File Structure

### Play-by-Play Files

**Path:** `data/<sport>/play_by_play/*.json`

**Structure:**
```json
{
  "game_id": "12345",
  "plays": [
    {
      "period": 1,
      "time": "12:34",
      "description": "Player X scored",
      "home_score": 1,
      "away_score": 0
    }
  ]
}
```

### Box Score Files

[Document your sport's box score structure]
```

---

## Phase 4: AWS Glue Configuration

**Time:** 2-4 hours setup + runtime
**Cost:** ~$10-20/month

### Step 1: Create Glue Database

```bash
aws glue create-database \
  --database-input "{
    \"Name\": \"<sport>_raw_data\",
    \"Description\": \"Raw <SPORT> game data\"
  }"

# Verify
aws glue get-database --name <sport>_raw_data
```

### Step 2: Create Glue Crawler (Optional)

**Note:** For large datasets (>50K files), skip crawler and use custom ETL script instead (see NBA lessons learned)

```bash
# Only if dataset is small (<50K files)
aws glue create-crawler \
  --name <sport>-data-crawler \
  --role AWSGlueServiceRole-<sport> \
  --database-name <sport>_raw_data \
  --targets "{
    \"S3Targets\": [{
      \"Path\": \"s3://<sport>-sim-raw-data-lake/raw-data/\"
    }]
  }"

# Run crawler
aws glue start-crawler --name <sport>-data-crawler

# Monitor status
aws glue get-crawler --name <sport>-data-crawler \
  --query 'Crawler.State'
```

### Step 3: Create Custom ETL Script

**For large datasets, create custom PySpark script:**

```python
# scripts/etl/glue_etl_<sport>.py
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

## Customize for your sport's data structure
def process_<sport>_data(glueContext, source_path):
    """Process <SPORT> data from S3."""

    # Read JSON files
    datasource = glueContext.create_dynamic_frame.from_options(
        connection_type="s3",
        connection_options={"paths": [source_path]},
        format="json"
    )

    # Filter empty files (customize based on data quality analysis)
    # Example: Keep only files with plays
    filtered = Filter.apply(
        frame=datasource,
        f=lambda x: x["plays"] is not None and len(x["plays"]) > 0
    )

    # Transform data (customize field extraction)
    # Example: Extract play-by-play events
    mapped = ApplyMapping.apply(
        frame=filtered,
        mappings=[
            ("game_id", "string", "game_id", "string"),
            ("plays", "array", "plays", "array"),
            # Add your sport-specific field mappings
        ]
    )

    return mapped

# Main job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Process data
processed_data = process_<sport>_data(
    glueContext,
    "s3://<sport>-sim-raw-data-lake/raw-data/"
)

# Write to RDS (after RDS setup)
glueContext.write_dynamic_frame.from_jdbc_conf(
    frame=processed_data,
    catalog_connection="<sport>-rds-connection",
    connection_options={
        "dbtable": "plays",
        "database": "<sport>_simulator"
    }
)

job.commit()
```

---

## Phase 5: RDS PostgreSQL Database

**Time:** 1-2 hours
**Cost:** ~$29/month (db.t3.small)

### Step 1: Create RDS Instance

```bash
# Create PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier <sport>-sim-db \
  --db-instance-class db.t3.small \
  --engine postgres \
  --engine-version 15.14 \
  --master-username postgres \
  --master-user-password '<your-password>' \
  --allocated-storage 20 \
  --storage-type gp3 \
  --vpc-security-group-ids <security-group-id> \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --publicly-accessible \
  --tags Key=Project,Value=<sport>-simulator

# Wait for creation (5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier <sport>-sim-db

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier <sport>-sim-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

### Step 2: Create Database Schema

**Customize schema for your sport:**

```sql
-- scripts/sql/<sport>_schema.sql
CREATE DATABASE <sport>_simulator;

\c <sport>_simulator

-- Example tables (customize for your sport)
CREATE TABLE games (
  game_id VARCHAR(50) PRIMARY KEY,
  season INTEGER NOT NULL,
  game_date DATE NOT NULL,
  home_team VARCHAR(50) NOT NULL,
  away_team VARCHAR(50) NOT NULL,
  home_score INTEGER,
  away_score INTEGER
);

CREATE TABLE player_stats (
  stat_id SERIAL PRIMARY KEY,
  game_id VARCHAR(50) REFERENCES games(game_id),
  player_id VARCHAR(50) NOT NULL,
  player_name VARCHAR(255),
  team VARCHAR(50),
  -- Add sport-specific stats (goals, assists, shots for hockey, etc.)
  points INTEGER,
  assists INTEGER
);

-- Add indexes
CREATE INDEX idx_games_season ON games(season);
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_player_stats_game ON player_stats(game_id);
```

**Run schema:**
```bash
psql -h <endpoint> -U postgres -d <sport>_simulator -f scripts/sql/<sport>_schema.sql
```

---

## Phase 6: Testing & Validation

### Step 1: Test ETL Pipeline

```bash
# Run Glue job with small sample
aws glue start-job-run \
  --job-name <sport>-etl-job \
  --arguments '{"--input_path":"s3://<sport>-sim-raw-data-lake/raw-data/sample/"}'

# Monitor job
aws glue get-job-run \
  --job-name <sport>-etl-job \
  --run-id <run-id> \
  --query 'JobRun.JobRunState'
```

### Step 2: Verify Data in RDS

```sql
-- Check row counts
SELECT COUNT(*) FROM games;
SELECT COUNT(*) FROM player_stats;

-- Sample data
SELECT * FROM games LIMIT 10;

-- Verify data quality
SELECT
  season,
  COUNT(*) as game_count,
  MIN(game_date) as earliest,
  MAX(game_date) as latest
FROM games
GROUP BY season
ORDER BY season;
```

---

## Sport-Specific Considerations

### NHL (Hockey)

**Data structure differences:**
- 3 periods instead of 4 quarters
- Overtime/shootout rules
- Power play tracking
- Shot locations (ice coordinates)
- Goalie statistics

**Key metrics:**
- Goals, Assists, Plus/Minus
- Shots on Goal, Save Percentage
- Power Play %, Penalty Kill %
- Faceoff Wins, Hits, Blocks

### NFL (Football)

**Data structure differences:**
- 4 quarters, possession-based
- Downs and distance tracking
- Field position (yard line)
- Play types (run, pass, kick)

**Key metrics:**
- Passing yards, Rushing yards
- Touchdowns, Turnovers
- Completion %, QB Rating
- Sacks, Tackles, Interceptions

### MLB (Baseball)

**Data structure differences:**
- 9 innings (no time limit)
- Pitch-by-pitch data
- Batter-pitcher matchups
- Base running situations

**Key metrics:**
- Batting Average, OBP, Slugging
- ERA, WHIP, Strikeouts
- Home Runs, RBIs, Stolen Bases
- Pitch velocity, Spin rate

### NCAA Basketball

**Data structure differences:**
- 2 halves instead of 4 quarters
- Different shot clock (30 sec)
- Bonus free throw rules
- More teams (350+)

**Key metrics:**
- Similar to NBA
- Consider conference-based analysis
- Tournament seeding data

---

## Common Issues & Solutions

### Issue 1: Data Source API Changes

**Problem:** ESPN/data source changes JSON structure

**Solution:**
- Version your extraction scripts
- Save sample JSON for each API version
- Update ETL mappings when structure changes
- Document API versions in DATA_STRUCTURE_GUIDE.md

### Issue 2: Large Dataset Glue Crawler OOM

**Problem:** Glue crawler fails with >50K files

**Solution:**
- Skip crawler entirely (learned from NBA project)
- Write custom PySpark ETL script
- Partition data by year/season
- Process incrementally

### Issue 3: RDS Storage Fills Up

**Problem:** Database grows too large

**Solution:**
```sql
-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Archive old data
-- Delete pre-2010 data if not needed
DELETE FROM player_stats WHERE game_id IN (
  SELECT game_id FROM games WHERE season < 2010
);

-- Or increase RDS storage
aws rds modify-db-instance \
  --db-instance-identifier <sport>-sim-db \
  --allocated-storage 50 \
  --apply-immediately
```

---

## Post-Setup Checklist

**After completing all phases:**

- [ ] S3 bucket created and data uploaded
- [ ] Data quality analysis documented
- [ ] Glue database and jobs configured
- [ ] RDS instance running and accessible
- [ ] Database schema created
- [ ] Sample ETL run completed successfully
- [ ] Data verified in RDS
- [ ] Costs monitored (check AWS Cost Explorer)
- [ ] Documentation updated (README, PROGRESS, DATA_STRUCTURE)
- [ ] Repository committed to GitHub
- [ ] README.md updated with sport-specific details

---

## Maintenance Schedule

**Daily:**
- Check Glue job status (if automated)
- Monitor RDS connections

**Weekly:**
- Check AWS costs
- Backup RDS (automatic, verify)
- Review error logs

**Monthly:**
- Rotate credentials (workflow #23)
- Review and optimize queries
- Update documentation

---

## Cost Optimization Tips

1. **Stop RDS when not in use:**
   ```bash
   aws rds stop-db-instance --db-instance-identifier <sport>-sim-db
   ```

2. **Use Glue bookmark to avoid reprocessing:**
   - Enables incremental processing
   - Saves ~30-50% on Glue costs

3. **Archive old data to S3 Glacier:**
   - S3 Lifecycle policies
   - Move data >1 year old to Glacier
   - Saves ~70% on storage costs

4. **Use Spot instances for EC2:**
   - 50-90% cheaper than on-demand
   - Good for simulation workloads

---

## Resources

**Templates from NBA Project:**
- `PROGRESS.md` - Phase-by-phase plan template
- `docs/DATA_STRUCTURE_GUIDE.md` - Data structure documentation
- `docs/LESSONS_LEARNED.md` - Avoid known pitfalls
- `scripts/analysis/` - Data quality analysis scripts
- `scripts/etl/` - ETL script templates

**External Resources:**
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [ESPN API Documentation](https://gist.github.com/akeaswaran/b48b02f1c94f873c6655e7129910fc3b)
- [Sports Data Sources](https://github.com/datasets/sports-data)

---

**Last Updated:** 2025-10-02
**Source:** docs/REPRODUCTION_GUIDE.md
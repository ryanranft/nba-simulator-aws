# Troubleshooting Guide

**Project:** NBA Game Simulator & ML Platform
**Purpose:** Common issues and solutions for development and AWS operations

---

## Quick Diagnosis

**Run the verification script first:**
```bash
cd /Users/ryanranft/nba-simulator-aws
conda activate nba-aws
./scripts/shell/verify_setup.sh
```

This will identify most common issues automatically.

---

## Table of Contents

1. [Environment Issues](#environment-issues)
2. [AWS Issues](#aws-issues)
3. [Git/GitHub Issues](#gitgithub-issues)
4. [Database Issues](#database-issues)
5. [ETL Issues](#etl-issues)
6. [Python/Conda Issues](#pythonconda-issues)
7. [Performance Issues](#performance-issues)

---

## Environment Issues

### ❌ Conda environment not found

**Symptom:**
```bash
conda activate nba-aws
# CondaEnvironmentError: environment 'nba-aws' not found
```

**Solution:**
```bash
# List available environments
conda env list

# If nba-aws doesn't exist, create it
conda create -n nba-aws python=3.11.13 -y
conda activate nba-aws

# Install dependencies
pip install boto3 pandas numpy psycopg2-binary sqlalchemy
```

**Verify:**
```bash
conda activate nba-aws
python --version  # Should show Python 3.11.13
```

---

### ❌ Wrong Python version

**Symptom:**
```bash
python --version
# Python 3.9.x or Python 3.12.x (not 3.11)
```

**Cause:** Wrong conda environment or system Python being used

**Solution:**
```bash
# Check which Python is running
which python

# Should show: ~/miniconda3/envs/nba-aws/bin/python
# If not, environment isn't activated

# Activate correct environment
conda activate nba-aws

# Verify
python --version  # Should show Python 3.11.13
which python      # Should show conda path
```

**If environment has wrong Python version:**
```bash
# Remove and recreate environment
conda deactivate
conda env remove -n nba-aws
conda create -n nba-aws python=3.11.13 -y
conda activate nba-aws
```

---

### ❌ AWS CLI in conda environment

**Symptom:**
```bash
which aws
# Shows: ~/miniconda3/envs/nba-aws/bin/aws
```

**Problem:** AWS CLI should be system-wide, not in conda

**Solution:**
```bash
# Remove AWS CLI from conda
conda deactivate
conda activate nba-aws
pip uninstall awscli -y

# Verify system AWS CLI is used
which aws
# Should show: /usr/local/bin/aws

# If system AWS CLI not installed:
# macOS:
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Linux:
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Why this matters:** AWS CLI version conflicts, conda packaging issues

---

### ❌ Missing Python packages

**Symptom:**
```python
import boto3
# ModuleNotFoundError: No module named 'boto3'
```

**Solution:**
```bash
# Make sure conda environment is activated
conda activate nba-aws

# Install missing package
pip install boto3

# Or install all dependencies
pip install boto3 pandas numpy psycopg2-binary sqlalchemy

# Verify
python -c "import boto3; print(boto3.__version__)"
```

**For psycopg2 installation errors:**
```bash
# Use binary version (easier)
pip install psycopg2-binary

# If you get compilation errors with psycopg2 (not -binary):
# macOS:
brew install postgresql
pip install psycopg2

# Linux:
sudo apt-get install libpq-dev
pip install psycopg2
```

---

## AWS Issues

### ❌ AWS credentials not configured

**Symptom:**
```bash
aws s3 ls
# Unable to locate credentials. You can configure credentials by running "aws configure"
```

**Solution:**
```bash
# Configure AWS credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: [Your access key from AWS Console]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1
# Default output format: json

# Verify
aws sts get-caller-identity
# Should show your account ID and user ARN
```

**Find your access keys:**
1. Go to AWS Console: https://console.aws.amazon.com
2. Click your username → Security credentials
3. Under "Access keys", click "Create access key"
4. Save the access key ID and secret access key

---

### ❌ Permission denied (AWS)

**Symptom:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/
# An error occurred (AccessDenied): Access Denied
```

**Causes:**
1. Wrong AWS account
2. Insufficient IAM permissions
3. Bucket doesn't exist

**Solution:**

**Check account:**
```bash
aws sts get-caller-identity
# Verify Account ID is correct: ************
```

**Check permissions:**
```bash
# Check your IAM user permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME

# Should have AdministratorAccess or sufficient S3 permissions
```

**Check bucket exists:**
```bash
# List all buckets
aws s3 ls

# Look for: nba-sim-raw-data-lake
```

**If bucket doesn't exist**, see PROGRESS.md Phase 1 (may need to recreate)

---

### ❌ Wrong AWS region

**Symptom:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/
# Bucket is in this region: us-east-1. Please use this region to retry the request
```

**Solution:**
```bash
# Check current region
aws configure get region

# Set to us-east-1
aws configure set region us-east-1

# Or reconfigure
aws configure
# Enter: us-east-1 for region
```

---

### ❌ AWS CLI command not found

**Symptom:**
```bash
aws --version
# bash: aws: command not found
```

**Solution:**

**macOS:**
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
rm AWSCLIV2.pkg

# Verify
which aws  # Should show: /usr/local/bin/aws
aws --version
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# Verify
which aws
aws --version
```

---

### ❌ S3 bucket is empty

**Symptom:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/
# (no output, bucket is empty)
```

**Cause:** Data hasn't been uploaded yet, or wrong bucket

**Solution:**

**Check object count:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize | grep "Total Objects"
# Should show: Total Objects: 146115
```

**If empty:** Data needs to be uploaded (see PROGRESS.md Phase 1)

---

## Git/GitHub Issues

### ❌ Permission denied (publickey)

**Symptom:**
```bash
git push origin main
# git@github.com: Permission denied (publickey).
# fatal: Could not read from remote repository.
```

**Cause:** SSH keys not configured with GitHub

**Solution:**

**Check if SSH key exists:**
```bash
ls -la ~/.ssh
# Look for: id_ed25519 or id_rsa
```

**If no key exists, create one:**
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Press Enter to accept defaults
```

**Add key to ssh-agent:**
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

**Copy public key:**
```bash
cat ~/.ssh/id_ed25519.pub
# Copy the entire output
```

**Add to GitHub:**
1. Go to https://github.com/settings/keys
2. Click "New SSH key"
3. Paste the public key
4. Click "Add SSH key"

**Test connection:**
```bash
ssh -T git@github.com
# Should see: "Hi [username]! You've successfully authenticated..."
```

**See also:** docs/adr/005-git-ssh-authentication.md

---

### ❌ Repository not found

**Symptom:**
```bash
git push origin main
# ERROR: Repository not found.
# fatal: Could not read from remote repository.
```

**Cause:** Wrong remote URL or no access to repository

**Solution:**

**Check remote URL:**
```bash
git remote -v
# Should show: git@github.com:ryanranft/nba-simulator-aws.git
```

**Fix remote URL:**
```bash
git remote set-url origin git@github.com:ryanranft/nba-simulator-aws.git
git remote -v  # Verify
```

**Verify GitHub access:**
```bash
ssh -T git@github.com
```

---

### ❌ Merge conflicts

**Symptom:**
```bash
git pull origin main
# CONFLICT (content): Merge conflict in filename
# Automatic merge failed; fix conflicts and then commit the result.
```

**Solution:**

**View conflicted files:**
```bash
git status
# Look for: both modified: filename
```

**Open conflicted file:**
```
<<<<<<< HEAD
Your local changes
=======
Remote changes
>>>>>>> branch_name
```

**Resolve conflict:**
1. Edit the file, choose which changes to keep
2. Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
3. Save the file

**Complete merge:**
```bash
git add filename
git commit -m "Resolve merge conflict in filename"
git push origin main
```

**To avoid conflicts:**
```bash
# Always pull before making changes
git pull origin main

# Use rebase for cleaner history
git pull origin main --rebase
```

---

### ❌ Diverged branches

**Symptom:**
```bash
git push origin main
# ! [rejected]        main -> main (non-fast-forward)
# hint: Updates were rejected because the tip of your current branch is behind
```

**Cause:** Remote has commits you don't have locally

**Solution:**

**Option 1: Rebase (recommended):**
```bash
git pull origin main --rebase
git push origin main
```

**Option 2: Merge:**
```bash
git pull origin main
git push origin main
```

**If rebase has conflicts:**
```bash
# Fix conflicts in each file
git add filename
git rebase --continue

# Or abort and use merge instead
git rebase --abort
git pull origin main
```

**See also:** COMMAND_LOG.md (GitHub session examples)

---

## Database Issues

### ❌ Cannot connect to RDS

**Symptom:**
```python
psycopg2.OperationalError: could not connect to server: Connection timed out
```

**Causes:**
1. RDS not created yet (⏸️ Pending in PROGRESS.md)
2. Security group blocks your IP
3. Wrong connection details
4. RDS instance stopped

**Solution:**

**Check if RDS exists:**
```bash
aws rds describe-db-instances --db-instance-identifier nba-sim-db
# If error: RDS not created yet
```

**Check security group:**
```bash
# Get your public IP
curl ifconfig.me

# Check RDS security group rules
aws rds describe-db-instances --db-instance-identifier nba-sim-db --query 'DBInstances[0].VpcSecurityGroups'

# Add your IP to security group (if needed)
# Do this via AWS Console → RDS → Security Groups
```

**Check RDS is running:**
```bash
aws rds describe-db-instances --db-instance-identifier nba-sim-db --query 'DBInstances[0].DBInstanceStatus'
# Should show: "available"
```

**If RDS is stopped:**
```bash
aws rds start-db-instance --db-instance-identifier nba-sim-db
```

---

### ❌ Authentication failed (database)

**Symptom:**
```python
psycopg2.OperationalError: FATAL: password authentication failed for user "postgres"
```

**Solution:**

**Check connection string:**
```python
# Correct format:
connection = psycopg2.connect(
    host="nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com",
    port=5432,
    database="nba_simulator",
    user="postgres",
    password="your_actual_password"
)
```

**Reset RDS password (if forgotten):**
```bash
aws rds modify-db-instance \
    --db-instance-identifier nba-sim-db \
    --master-user-password "new_password" \
    --apply-immediately
```

---

## ETL Issues

### ❌ Glue job fails

**Symptom:**
```bash
aws glue get-job-run --job-name nba-etl-job --run-id jr_xxx
# Status: FAILED
```

**Solution:**

**Check CloudWatch logs:**
```bash
# Get log stream name from job run details
aws glue get-job-run --job-name nba-etl-job --run-id jr_xxx

# View logs in CloudWatch
# Go to: CloudWatch → Log Groups → /aws-glue/jobs/output
```

**Common errors:**

**Out of memory:**
- Increase DPU count in Glue job settings
- Process data in smaller batches

**Module not found:**
- Add required libraries to Glue job dependencies
- Use `--additional-python-modules` parameter

**S3 access denied:**
- Check Glue IAM role has S3 read permissions
- Verify bucket name and paths are correct

---

### ❌ JSON parsing errors

**Symptom:**
```python
json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Cause:** Malformed JSON file or empty file

**Solution:**

**Validate JSON:**
```bash
# Check if file is valid JSON
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json - | python -m json.tool
```

**Handle errors in code:**
```python
import json

try:
    with open('file.json') as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    print(f"Invalid JSON in {filename}: {e}")
    # Skip file or use default values
```

**Check for empty files:**
```python
import os

if os.path.getsize('file.json') == 0:
    print(f"Empty file: {filename}")
    # Skip or handle appropriately
```

---

### ❌ Missing fields in JSON

**Symptom:**
```python
KeyError: 'player_id'
```

**Cause:** JSON structure varies between files

**Solution:**

**Use .get() with defaults:**
```python
# Bad - raises KeyError
player_id = data['player_id']

# Good - returns None if missing
player_id = data.get('player_id')

# Best - returns default value
player_id = data.get('player_id', 'UNKNOWN')
```

**Check if field exists:**
```python
if 'player_id' in data:
    player_id = data['player_id']
else:
    print(f"Missing player_id in {filename}")
    # Skip or use default
```

---

## Python/Conda Issues

### ❌ Conda command not found

**Symptom:**
```bash
conda --version
# bash: conda: command not found
```

**Solution:**

**Check if conda is installed:**
```bash
ls ~/miniconda3/bin/conda
# If exists, conda is installed but not in PATH
```

**Add conda to PATH:**
```bash
# For bash:
~/miniconda3/bin/conda init bash
source ~/.bashrc

# For zsh:
~/miniconda3/bin/conda init zsh
source ~/.zshrc

# Verify
conda --version
```

**If conda not installed:**
```bash
# Download and install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda3
~/miniconda3/bin/conda init
exec $SHELL
```

---

### ❌ Package conflicts

**Symptom:**
```bash
pip install somepackage
# ERROR: pip's dependency resolver does not currently take into account all the packages
```

**Solution:**

**Option 1: Install packages one at a time:**
```bash
pip install boto3
pip install pandas
pip install numpy
```

**Option 2: Create fresh environment:**
```bash
conda deactivate
conda env remove -n nba-aws
conda create -n nba-aws python=3.11.13 -y
conda activate nba-aws
pip install boto3 pandas numpy psycopg2-binary sqlalchemy
```

**Option 3: Use conda instead of pip (for some packages):**
```bash
conda install -c conda-forge pandas numpy
pip install boto3 psycopg2-binary
```

---

### ❌ ImportError despite package installed

**Symptom:**
```python
import pandas
# ImportError: No module named 'pandas'

# But:
pip list | grep pandas
# pandas  2.0.3
```

**Cause:** Using wrong Python interpreter

**Solution:**

**Check which Python:**
```bash
which python
# Should show: ~/miniconda3/envs/nba-aws/bin/python

# If shows system Python:
conda activate nba-aws
which python  # Verify conda Python
```

**Verify package location:**
```bash
python -c "import sys; print(sys.path)"
# Should include: ~/miniconda3/envs/nba-aws/lib/python3.11/site-packages
```

---

## Performance Issues

### ❌ PyCharm is slow

**Cause:** PyCharm indexing 146K+ data files

**Solution:**

**Mark data folder as excluded:**
1. Open PyCharm
2. Right-click `data/` folder
3. Select "Mark Directory as" → "Excluded"
4. Wait for re-indexing (may take a few minutes)

**Check indexing status:**
- Look at bottom-right corner of PyCharm
- Should show "Indexing finished"

---

### ❌ ETL is very slow

**Symptom:** Processing 146K files takes >6 hours

**Causes:**
1. Sequential processing (not using parallelism)
2. Small DPU count in Glue
3. Inefficient data transformations

**Solution:**

**Increase Glue DPU count:**
```bash
# Update Glue job
aws glue update-job \
    --job-name nba-etl-job \
    --job-update NumberOfWorkers=20,WorkerType=G.1X
```

**Use batch processing:**
```python
# Process files in batches instead of one at a time
batch_size = 1000
for batch in batched(file_list, batch_size):
    process_batch(batch)
```

**Optimize Spark operations:**
- Use DataFrame operations instead of loops
- Minimize shuffles
- Cache intermediate results if reused

---

### ❌ Queries are slow

**Symptom:** Simple queries take >10 seconds

**Cause:** Missing indexes or unoptimized queries

**Solution:**

**Add indexes:**
```sql
-- Check existing indexes
SELECT * FROM pg_indexes WHERE tablename = 'player_game_stats';

-- Add indexes for frequently queried columns
CREATE INDEX idx_player_game_stats_player_id ON player_game_stats(player_id);
CREATE INDEX idx_player_game_stats_game_id ON player_game_stats(game_id);
CREATE INDEX idx_games_game_date ON games(game_date);
```

**Analyze query performance:**
```sql
EXPLAIN ANALYZE
SELECT * FROM player_game_stats WHERE player_id = 12345;
```

**See query execution plan and optimize accordingly**

---

## Getting Help

### Check Documentation

1. **PROGRESS.md** - Current project status and next steps
2. **CLAUDE.md** - Quick reference for Claude Code usage
3. **docs/adr/** - Architecture decisions and rationale
4. **COMMAND_LOG.md** - Historical command executions and solutions

### Run Diagnostics

```bash
# Verify environment
./scripts/shell/verify_setup.sh

# Check AWS access
aws sts get-caller-identity
aws s3 ls s3://nba-sim-raw-data-lake/

# Check Git status
git status
git remote -v

# Check Python environment
conda env list
python --version
pip list
```

### Enable Debug Logging

**AWS CLI:**
```bash
aws s3 ls s3://nba-sim-raw-data-lake/ --debug
```

**Python:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Glue:**
```python
# In Glue script
logger = glueContext.get_logger()
logger.info("Debug message here")
```

---

## Quick Reference

### Most Common Issues

1. ❌ **Wrong conda environment** → `conda activate nba-aws`
2. ❌ **AWS credentials not configured** → `aws configure`
3. ❌ **SSH keys not set up** → See [Git/GitHub Issues](#gitgithub-issues)
4. ❌ **Wrong Python version** → Recreate conda environment
5. ❌ **Package not found** → `pip install package_name`

### Useful Commands

```bash
# Environment
conda activate nba-aws
./scripts/shell/verify_setup.sh

# AWS
aws sts get-caller-identity
aws s3 ls s3://nba-sim-raw-data-lake/

# Git
git status
git pull origin main --rebase
git push origin main

# Python
python --version
pip list
python -c "import boto3; print(boto3.__version__)"
```

---

**Last Updated:** 2025-09-30

**Note:** This guide will be updated as new issues are encountered. Check COMMAND_LOG.md for recent solutions to specific problems.

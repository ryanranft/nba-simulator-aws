# Phase 4: Simulation Engine (EC2)

**Status:** ✅ COMPLETE
**Prerequisites:** Phase 2 & 3 complete (RDS populated with 6.7M plays)
**Actual Time:** 3 hours
**Actual Cost:** $6.59/month (t3.small 8hrs/day)
**Started:** October 3, 2025
**Completed:** October 3, 2025

---

> **⚠️ IMPORTANT - Before Starting This Phase:**
>
> **Ask Claude:** "Should I add any workflows to this phase before beginning?"
>
> This allows Claude to review the current workflow references and recommend any missing workflows that would improve implementation guidance. Phases 1-3 were enhanced with comprehensive workflow instructions - this phase should receive the same treatment before starting work.

---

## Overview

Set up AWS EC2 instance to run NBA game simulations using historical data from RDS PostgreSQL. The simulation engine will use Monte Carlo methods and statistical models to predict game outcomes based on team/player performance patterns.

**This phase includes:**
- EC2 instance provisioning
- Python 3.11 + dependencies installation
- Simulation code deployment
- RDS connection from EC2
- Test simulation execution

---

## Prerequisites

Before starting this phase:
- [ ] Phase 2 complete (data loaded to RDS)
- [ ] Phase 3 complete (RDS operational with 6.7M plays)
- [ ] Simulation code developed (Python scripts)
- [ ] SSH key pair created or available

**Follow these workflows before beginning:**

- Workflow #1 ([Session Start](../claude_workflows/workflow_descriptions/01_session_start.md))
  - **When to run:** At the very beginning of working on Phase 4
  - **Purpose:** Initialize session, check environment, review what was completed last session

- Workflow #34 ([Lessons Learned Review](../claude_workflows/workflow_descriptions/34_lessons_learned_review.md))
  - **When to run:** After session start, before making any decisions
  - **Purpose:** Review LESSONS_LEARNED.md for EC2-related lessons from previous phases

- Workflow #3 ([Decision Workflow](../claude_workflows/workflow_descriptions/03_decision_workflow.md))
  - **When to run:** When making major Phase 4 decisions (EC2 instance type, simulation architecture)
  - **Purpose:** Document key architectural decisions as ADRs before implementing

**See workflow #24 (AWS Resource Setup) for EC2 provisioning.**

---

## What Actually Happened (October 3, 2025)

**Actual execution details from completed implementation:**

### Key Decisions Made
1. **No pre-written simulation code:** Developed simulation scripts from scratch during phase
2. **SSH key created fresh:** No existing key pair - created `nba-simulator-ec2-key`
3. **Used t3.small 8hrs/day:** Final cost: $6.59/month ($4.99 compute + $1.60 storage)
4. **Created Workflow #37:** New workflow for credential management (added to system)

### Actual Steps Executed

**1. Prerequisites (15 min)**
- Followed Workflow #1 (Session Start) ✅
- Followed Workflow #34 (Lessons Learned Review) - found security group lessons ✅
- Followed Workflow #18 (Cost Management) - approved $6.59/month ✅

**2. SSH Key Creation (5 min)**
```bash
aws ec2 create-key-pair --key-name nba-simulator-ec2-key --query 'KeyMaterial' --output text > ~/.ssh/nba-simulator-ec2-key.pem
chmod 400 ~/.ssh/nba-simulator-ec2-key.pem
# Result: Successfully created and secured
```

**3. Security Group Creation (5 min)**
```bash
# Get current IP
MY_IP=$(curl -s https://checkip.amazonaws.com)

# Create security group
aws ec2 create-security-group --group-name nba-ec2-sg --description "SSH access for NBA simulator EC2"
# Result: sg-0b9ca09f4a041e1c8

# Add SSH rule
aws ec2 authorize-security-group-ingress --group-id sg-0b9ca09f4a041e1c8 --protocol tcp --port 22 --cidr ${MY_IP}/32
```

**4. EC2 Instance Launch (10 min)**
```bash
# Get latest Amazon Linux 2023 AMI
AMI_ID=$(aws ec2 describe-images --owners amazon --filters "Name=name,Values=al2023-ami-2023.*-x86_64" --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' --output text)
# Result: ami-052064a798f08f0d3

# Launch instance
aws ec2 run-instances --image-id ami-052064a798f08f0d3 --instance-type t3.small --key-name nba-simulator-ec2-key --security-group-ids sg-0b9ca09f4a041e1c8 --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=nba-simulation-engine}]'
# Result: i-0b8bbe4cdff7ae2d2

# Wait for running state
aws ec2 wait instance-running --instance-ids i-0b8bbe4cdff7ae2d2

# Get public IP
aws ec2 describe-instances --instance-ids i-0b8bbe4cdff7ae2d2 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
# Result: 54.165.99.80
```

**5. Software Installation (20 min)**
```bash
# SSH into instance
ssh -i ~/.ssh/nba-simulator-ec2-key.pem ec2-user@54.165.99.80

# Update system
sudo yum update -y

# Install Python 3.11, PostgreSQL client, git
sudo yum install python3.11 python3.11-pip git postgresql15 -y

# Install Python packages (use --user flag)
pip3.11 install boto3 pandas psycopg2-binary sqlalchemy numpy scipy --user

# Verify versions
python3.11 --version  # Python 3.11.13
psql --version        # PostgreSQL 15.14
pip3.11 list | grep -E "boto3|pandas|psycopg2"
# boto3 1.40.44, pandas 2.3.3, psycopg2-binary 2.9.10, numpy 2.3.3, scipy 1.16.2
```

**6. RDS Security Group Update (5 min)**
```bash
# Add EC2 security group to RDS ingress rules
aws ec2 authorize-security-group-ingress --group-id sg-079ed470e0caaca44 --protocol tcp --port 5432 --source-group sg-0b9ca09f4a041e1c8
# Result: EC2 can now connect to RDS
```

**7. Environment Configuration (10 min)**
```bash
# Create ~/.env file on EC2
cat > ~/.env << 'EOF'
DB_HOST=nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=nba_simulator
DB_USER=postgres
DB_PASSWORD=NbaSimulator2025!SecurePass
AWS_REGION=us-east-1
EOF

chmod 600 ~/.env

# Add auto-load to .bashrc
echo "if [ -f ~/.env ]; then source ~/.env; fi" >> ~/.bashrc

# Test psql connection
source ~/.env
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM games;"
# Result: 44,828 ✅

# Test Python connection
python3.11 -c "import psycopg2; conn = psycopg2.connect(host='nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com', database='nba_simulator', user='postgres', password='NbaSimulator2025!SecurePass'); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM play_by_play'); print(f'Rows: {cur.fetchone()[0]:,}'); conn.close()"
# Result: Rows: 6,781,155 ✅
```

**8. Simulation Code Development (60 min)**

Created directory structure:
```bash
mkdir -p ~/nba-simulation/{scripts,data,results}
```

**Created files:**

`~/nba-simulation/scripts/db_connection.py` (120 lines)
- NBADatabase class with connection pooling
- Methods: `get_team_stats()`, `get_head_to_head()`, `get_recent_games()`
- **Important fix:** Used correct column names from actual schema:
  - `home_team_abbrev`, `away_team_abbrev` (NOT home_team_abbreviation)
  - `home_score`, `away_score` (verified with `\d games`)
  - `home_team_is_winner`, `away_team_is_winner`

`~/nba-simulation/scripts/simulate_game.py` (200+ lines)
- GameSimulator class with Monte Carlo methods
- Normal distribution scoring model
- Command-line interface with argparse
- CSV result export
- **Key parameters:**
  - Home advantage: +3.0 points
  - Standard deviation: 12.0 points
  - Default iterations: 1000

`~/nba-simulation/README.md` (3.9 KB)
- Complete documentation of simulation methodology
- Usage examples
- Database schema reference
- Performance benchmarks

**9. Testing & Validation (20 min)**
```bash
cd ~/nba-simulation/scripts

# Test 1: Lakers vs Celtics (1,000 iterations)
python3.11 simulate_game.py --home-team LAL --away-team BOS --iterations 1000
# Result: LAL 54.1% win prob, predicted 106.4-104.1 ✅

# Test 2: Warriors vs Heat (5,000 iterations)
python3.11 simulate_game.py --home-team GSW --away-team MIA --iterations 5000 --season 2022-23
# Result: GSW 58.1% win prob, predicted 107.8-103.4 ✅

# Performance: 5,000 iterations completed in ~5-8 seconds ✅
```

**10. Credential Management (15 min)**

**Created Workflow #37:** `/Users/ryanranft/nba-simulator-aws/docs/claude_workflows/workflow_descriptions/37_credential_management.md`

Updated `/Users/ryanranft/nba-sim-credentials.env`:
```bash
# ============================================================================
# EC2 Configuration (Phase 4 - Simulation Engine)
# ============================================================================
export EC2_INSTANCE_ID="i-0b8bbe4cdff7ae2d2"
export EC2_PUBLIC_IP="54.165.99.80"
export EC2_INSTANCE_TYPE="t3.small"
export EC2_KEY_NAME="nba-simulator-ec2-key"
export EC2_KEY_PATH="/Users/ryanranft/.ssh/nba-simulator-ec2-key.pem"
export EC2_SECURITY_GROUP_ID="sg-0b9ca09f4a041e1c8"
export EC2_SSH_USER="ec2-user"
```

### Critical Insights

**What worked well:**
1. ✅ AWS CLI automation for all infrastructure (no console usage)
2. ✅ Security group source-group reference (EC2 → RDS) instead of IP ranges
3. ✅ `--user` flag for pip install (avoids permission issues)
4. ✅ Auto-load ~/.env in .bashrc (persistent environment)
5. ✅ Checking table schema first (`\d games`, `\d play_by_play`)

**What didn't work initially:**
1. ❌ Python connection using environment variables in heredoc (variables not passed)
   - **Fix:** Use explicit credentials or pass variables differently
2. ❌ Wrong column names (homedescription, visitordescription)
   - **Fix:** Queried actual schema with `\d table_name`
3. ❌ pandas warnings about psycopg2 connection
   - **Solution:** Warnings are cosmetic, can ignore or use SQLAlchemy in future

**Lessons for Phase 5:**
1. Always check database schema before writing queries
2. Use `aws ec2 wait` commands for instance state changes
3. Security groups are better with source-group references than IP ranges
4. Test database connections with both psql AND Python before deploying code
5. Document all resource IDs immediately (instance ID, security group IDs)

### Actual Resource IDs
- **EC2 Instance:** i-0b8bbe4cdff7ae2d2
- **EC2 Public IP:** 54.165.99.80 (changes on restart!)
- **EC2 Security Group:** sg-0b9ca09f4a041e1c8
- **RDS Security Group:** sg-079ed470e0caaca44
- **SSH Key:** ~/.ssh/nba-simulator-ec2-key.pem (400 permissions)
- **AMI Used:** ami-052064a798f08f0d3 (Amazon Linux 2023)

### Actual Time Breakdown
- Setup & prerequisites: 35 min
- Infrastructure provisioning: 20 min
- Software installation: 20 min
- Database configuration: 15 min
- Code development: 60 min
- Testing & validation: 20 min
- Documentation: 30 min
- **Total: ~3 hours** (matches estimate!)

---

## Implementation Steps

### Sub-Phase 4.1: EC2 Instance Launch

**Status:** ✅ COMPLETE
**Time Estimate:** 30 minutes
**Cost:** $5-15/month

**Follow these workflows:**
- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
  - **When to run:** BEFORE launching EC2 instance
  - **Purpose:** Estimate monthly costs ($5-15/month based on usage), get user approval
  - **Key decision:** t3.small on-demand vs spot instance vs 8hrs/day vs 24/7

- Workflow #34 ([Lessons Learned Review](../claude_workflows/workflow_descriptions/34_lessons_learned_review.md))
  - **When to run:** Before EC2 provisioning
  - **Purpose:** Check if any EC2-related lessons exist in LESSONS_LEARNED.md

- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
  - **When to run:** When launching EC2 instance
  - **Purpose:** Follow EC2 best practices (AMI selection, security group setup, SSH key management)

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After running AWS CLI commands
  - **Purpose:** Log EC2 launch commands to COMMAND_LOG.md for future reference

- Workflow #11 ([Error Handling](../claude_workflows/workflow_descriptions/11_error_handling.md))
  - **When to run:** If EC2 launch fails
  - **Purpose:** Troubleshoot instance launch issues, security group problems, SSH connection failures

- Workflow #28 ([ADR Creation](../claude_workflows/workflow_descriptions/28_adr_creation.md))
  - **When to run:** After making instance type or configuration decisions
  - **Purpose:** Document architectural decisions (instance type, spot vs on-demand, usage schedule)

**Configuration:**
1. [ ] Launch EC2 instance via AWS Console
2. [ ] Configure security group for SSH access
3. [ ] Connect via SSH and verify
4. [ ] Document instance details

**Recommended configuration:**
- **AMI:** Amazon Linux 2023 (free tier eligible)
- **Instance type:** t3.small
- **vCPUs:** 2
- **RAM:** 2 GB
- **Storage:** 20 GB GP3
- **Key pair:** Select existing or create new
- **Security group:** Allow SSH (port 22) from your IP

**Launch command (CLI alternative):**
```bash
aws ec2 run-instances \
  --image-id ami-xxxxxxxxx \
  --instance-type t3.small \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=nba-simulation-engine}]'
```

**Validation:**
- [ ] Instance status: Running
- [ ] Public IP assigned
- [ ] SSH connection successful

---

### Sub-Phase 4.2: Software Installation

**Status:** ⏸️ PENDING
**Time Estimate:** 1 hour

**Follow these workflows:**
- Workflow #17 ([Environment Setup](../claude_workflows/workflow_descriptions/17_environment_setup.md))
  - **When to run:** After connecting to EC2 instance
  - **Purpose:** Verify Python 3.11 installation, set up environment correctly on EC2

- Workflow #2 ([Command Logging](../claude_workflows/workflow_descriptions/02_command_logging.md))
  - **When to run:** After running installation commands
  - **Purpose:** Log installation commands to COMMAND_LOG.md for reproducibility

**Installation steps:**
1. [ ] Connect to EC2 instance via SSH
2. [ ] Update system packages
3. [ ] Install Python 3.11
4. [ ] Install PostgreSQL client
5. [ ] Install Python packages
6. [ ] Verify installations

**Commands to execute:**
```bash
# Connect to instance
ssh -i your-key.pem ec2-user@ec2-xx-xx-xx-xx.compute-1.amazonaws.com

# Update system
sudo yum update -y

# Install Python 3.11
sudo yum install python3.11 python3.11-pip git -y

# Install PostgreSQL client
sudo yum install postgresql15 -y

# Install Python packages
pip3.11 install boto3 pandas psycopg2-binary sqlalchemy numpy scipy

# Verify installations
python3.11 --version
# Expected: Python 3.11.x

psql --version
# Expected: psql (PostgreSQL) 15.x

pip3.11 list | grep -E "boto3|pandas|psycopg2|sqlalchemy|numpy"
```

**Validation:**
- [ ] Python 3.11 installed
- [ ] PostgreSQL client installed
- [ ] All required packages installed
- [ ] No dependency errors

---

### Sub-Phase 4.3: Environment Configuration

**Status:** ⏸️ PENDING
**Time Estimate:** 15 minutes

**Follow these workflows:**
- Workflow #32 ([RDS Connection](../claude_workflows/workflow_descriptions/32_rds_connection.md))
  - **When to run:** Before testing database connection from EC2
  - **Purpose:** Verify RDS security group allows EC2, test connection methods

- Workflow #23 ([Credential Rotation](../claude_workflows/workflow_descriptions/23_credential_rotation.md))
  - **When to run:** After creating ~/.env file with database credentials
  - **Purpose:** Ensure ~/.env has proper permissions (600), document credential location

- Workflow #16 ([Testing](../claude_workflows/workflow_descriptions/16_testing.md))
  - **When to run:** After environment configuration
  - **Purpose:** Test database connection with sample queries, verify row counts

**Configuration steps:**
1. [ ] Create environment variables file
2. [ ] Set RDS connection details
3. [ ] Load environment variables
4. [ ] Test database connection

**Create ~/.env file:**
```bash
cat > ~/.env << 'EOF'
DB_HOST=nba-sim-db.ck96ciigs7fy.us-east-1.rds.amazonaws.com
DB_PORT=5432
DB_NAME=nba_simulator
DB_USER=postgres
DB_PASSWORD=your_password_here
AWS_REGION=us-east-1
EOF

# Set permissions
chmod 600 ~/.env

# Load variables
source ~/.env
```

**Test connection:**
```bash
# Test psql connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM games;"
# Expected: 44,828

# Test Python connection
python3.11 << 'EOF'
import psycopg2
import os

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM play_by_play;")
print(f"Play-by-play rows: {cursor.fetchone()[0]:,}")
conn.close()
EOF
# Expected: Play-by-play rows: 6,781,155
```

**Validation:**
- [ ] Environment variables set
- [ ] psql connection successful
- [ ] Python connection successful
- [ ] Can query all tables

---

### Sub-Phase 4.4: Simulation Code Deployment

**Status:** ⏸️ PENDING
**Time Estimate:** 30 minutes

**Follow these workflows:**
- Workflow #6 ([File Creation](../claude_workflows/workflow_descriptions/06_file_creation.md))
  - **When to run:** When creating new simulation script files
  - **Purpose:** Follow file creation best practices, ensure proper structure and documentation

- Workflow #27 ([TDD Workflow](../claude_workflows/workflow_descriptions/27_tdd_workflow.md))
  - **When to run:** Before writing simulation code (if not already written)
  - **Purpose:** Write tests first for simulation logic, Monte Carlo methods

- Workflow #16 ([Testing](../claude_workflows/workflow_descriptions/16_testing.md))
  - **When to run:** After deploying simulation code to EC2
  - **Purpose:** Run test simulation, verify results are reasonable, test query performance

- Workflow #35 ([Pre-Deployment Testing](../claude_workflows/workflow_descriptions/35_pre_deployment_testing.md))
  - **When to run:** Before running full-scale simulations
  - **Purpose:** Phase-specific testing checklist for Phase 4 (simulation engine validation)

- Workflow #30 ([Code Snippet Logging](../claude_workflows/workflow_descriptions/30_code_snippet_logging.md))
  - **When to run:** After writing simulation code
  - **Purpose:** Log simulation algorithms and outcomes to COMMAND_LOG.md

- Workflow #08 ([Git Commit](../claude_workflows/workflow_descriptions/08_git_commit.md))
  - **When to run:** After deploying and testing simulation code
  - **Purpose:** Commit simulation scripts with proper security scanning, version control

- Workflow #10 ([Git Push](../claude_workflows/workflow_descriptions/10_git_push.md))
  - **When to run:** After committing simulation code
  - **Purpose:** Push simulation code to remote repository with pre-push inspection

- Workflow #14 ([Session End](../claude_workflows/workflow_descriptions/14_session_end.md))
  - **When to run:** After completing Phase 4
  - **Purpose:** Properly end session, update documentation, prepare for next session

**Deployment steps:**
1. [ ] Clone repository to EC2 (or upload code)
2. [ ] Verify simulation scripts
3. [ ] Run test simulation
4. [ ] Document results

**Clone repository:**
```bash
# If using Git
git clone git@github.com:ryanranft/nba-simulator-aws.git
cd nba-simulator-aws

# Or upload specific files via SCP
scp -i your-key.pem scripts/simulation/*.py ec2-user@ec2-xx-xx-xx-xx:~/
```

**Run test simulation:**
```bash
# Example: Simulate Lakers vs Celtics
python3.11 scripts/simulation/simulate_game.py \
  --home-team LAL \
  --away-team BOS \
  --iterations 1000

# Expected output:
# Lakers win probability: 52.3%
# Celtics win probability: 47.7%
# Average score: LAL 108.5 - BOS 106.2
```

**Validation:**
- [ ] Code uploaded successfully
- [ ] Test simulation runs without errors
- [ ] Results are reasonable (based on historical data)
- [ ] Query performance acceptable (<5 seconds)

---

## Cost Breakdown

| Resource | Configuration | Monthly Cost | Notes |
|----------|--------------|--------------|-------|
| **Option A: t3.small (Recommended)** | | | |
| Compute (8 hrs/day) | 2 vCPUs, 2 GB RAM | $4.99 | $0.0208/hr × 240 hrs |
| Compute (24/7) | 2 vCPUs, 2 GB RAM | $15.18 | $0.0208/hr × 730 hrs |
| Storage | 20 GB GP3 | $1.60 | Always charged |
| **Total (8 hrs/day)** | | **~$7/month** | Start/stop as needed |
| **Total (24/7)** | | **~$17/month** | Always running |
| | | | |
| **Option B: t3.micro (Minimal)** | | | |
| Compute (4 hrs/day) | 2 vCPUs, 1 GB RAM | $1.25 | $0.0104/hr × 120 hrs |
| Storage | 20 GB GP3 | $1.60 | Always charged |
| **Total (4 hrs/day)** | | **~$3/month** | Testing only |
| | | | |
| **Option C: Spot Instance t3.small** | | | |
| Compute (24/7) | 2 vCPUs, 2 GB RAM | $4.40 | ~$0.006/hr (70% discount) |
| Storage | 20 GB GP3 | $1.60 | Always charged |
| **Total (24/7)** | | **~$6/month** | Can be interrupted |

**Recommendation:** t3.small on-demand, start when needed, stop when idle = **$5-10/month**

---

## Instance Management

**Start/Stop Commands:**

```bash
# Stop instance when not in use (stops compute billing)
aws ec2 stop-instances --instance-ids i-xxxxxxxxx

# Start instance when needed
aws ec2 start-instances --instance-ids i-xxxxxxxxx

# Get public IP after start (IP changes on restart)
aws ec2 describe-instances \
  --instance-ids i-xxxxxxxxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text

# Check instance status
aws ec2 describe-instances \
  --instance-ids i-xxxxxxxxx \
  --query 'Reservations[0].Instances[0].State.Name' \
  --output text
```

**Cost optimization:**
- Stop instance when not in use (saves compute costs)
- Storage costs continue even when stopped ($1.60/month)
- Public IP changes on restart (document new IP each time)

---

## Simulation Workflows

**Typical simulation tasks:**

1. **Single game simulation:**
   ```bash
   python3.11 scripts/simulation/simulate_game.py \
     --home-team LAL --away-team BOS --iterations 1000
   ```

2. **Playoff series simulation:**
   ```bash
   python3.11 scripts/simulation/simulate_series.py \
     --team1 LAL --team2 BOS --series-format "2-2-1-1-1"
   ```

3. **Season prediction:**
   ```bash
   python3.11 scripts/simulation/simulate_season.py \
     --season 2024-25 --iterations 10000
   ```

4. **Player impact analysis:**
   ```bash
   python3.11 scripts/simulation/player_impact.py \
     --player "LeBron James" --games 82
   ```

---

## Troubleshooting

**Common issues:**

1. **SSH connection refused**
   - Check security group allows port 22 from your IP
   - Verify instance is running
   - Use correct key pair (.pem file)

2. **Database connection timeout**
   - RDS security group must allow EC2 security group
   - Or allow EC2's IP range
   - See workflow #32 for connection troubleshooting

3. **Python package installation fails**
   - Run `sudo yum install python3.11-devel` first
   - PostgreSQL dev libraries: `sudo yum install postgresql-devel`

4. **Out of memory during simulation**
   - Reduce iteration count
   - Or upgrade to t3.medium (4 GB RAM)

---

## Success Criteria

Phase complete when:
- [ ] EC2 instance running
- [ ] Python 3.11 + all dependencies installed
- [ ] Database connection from EC2 verified
- [ ] Test simulation runs successfully
- [ ] Results are reasonable and reproducible
- [ ] Query performance acceptable (<5 seconds)
- [ ] Cost within budget ($5-15/month)
- [ ] Start/stop procedures documented

---

## Next Steps

After completing this phase:
1. [ ] Update PROGRESS.md status
2. [ ] Document simulation results
3. [ ] Proceed to [Phase 5: Machine Learning](PHASE_5_MACHINE_LEARNING.md)

**Note:** Phase 4 and Phase 5 can run in parallel if desired (both depend on RDS data).

---

## Security Best Practices

**Follow these workflows:**
- Workflow #23 ([Credential Rotation](../claude_workflows/workflow_descriptions/23_credential_rotation.md))
- Workflow #19 ([Backup & Recovery](../claude_workflows/workflow_descriptions/19_backup_recovery.md))

**Security checklist:**
- [ ] SSH key pair stored securely (not in repository)
- [ ] Security group restricts SSH to your IP only
- [ ] Database password in ~/.env (not hardcoded)
- [ ] ~/.env file permissions set to 600 (owner read/write only)
- [ ] Stop instance when not in use
- [ ] Regular AMI snapshots for backup

---

## Navigation

**Return to:** [PROGRESS.md](../../PROGRESS.md) | **Workflows:** [Workflow Index](../claude_workflows/CLAUDE_WORKFLOW_ORDER.md)

**Related phases:**
- Previous: [Phase 3: Database Infrastructure](PHASE_3_DATABASE.md)
- Next: [Phase 5: Machine Learning](PHASE_5_MACHINE_LEARNING.md) (can run in parallel)

---

*For Claude Code: See CLAUDE.md for navigation instructions and context management strategies.*

---

*Last updated: 2025-10-03*
*Status: ✅ COMPLETE - Implementation successful*
*Actual implementation time: 3 hours*

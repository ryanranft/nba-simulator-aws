# Phase 4: Simulation Engine (EC2)

**Status:** ⏸️ PENDING
**Prerequisites:** Phase 2 & 3 complete (RDS populated with 6.7M plays)
**Estimated Time:** 2-3 hours
**Estimated Cost:** $5-15/month (usage-dependent)
**Started:** TBD
**Completed:** TBD

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

**See workflow #24 (AWS Resource Setup) for EC2 provisioning.**

---

## Implementation Steps

### Sub-Phase 4.1: EC2 Instance Launch

**Status:** ⏸️ PENDING
**Time Estimate:** 30 minutes
**Cost:** $5-15/month

**Follow these workflows:**
- Workflow #24 ([AWS Resource Setup](../claude_workflows/workflow_descriptions/24_aws_resource_setup.md))
- Workflow #18 ([Cost Management](../claude_workflows/workflow_descriptions/18_cost_management.md))
- Workflow #34 ([Lessons Learned Review](../claude_workflows/workflow_descriptions/34_lessons_learned_review.md))

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
- Workflow #32 ([RDS Connection](../claude_workflows/workflow_descriptions/32_rds_connection.md))

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
- Workflow #23 ([Credential Rotation](../claude_workflows/workflow_descriptions/23_credential_rotation.md))
- Workflow #32 ([RDS Connection](../claude_workflows/workflow_descriptions/32_rds_connection.md))

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
- Workflow #27 ([TDD Workflow](../claude_workflows/workflow_descriptions/27_tdd_workflow.md))

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

*Last updated: 2025-10-02*
*Status: Planning complete, ready for implementation*
*Estimated implementation time: 2-3 hours*

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Instructions for Claude

**CRITICAL - Progress Tracking Protocol:**

1. **Always read PROGRESS.md first** to understand what has been completed and what's next
2. **Follow PROGRESS.md sequentially** - start from the first "⏸️ PENDING" or "⏳ IN PROGRESS" task
3. **If the plan changes**, update PROGRESS.md BEFORE proceeding with new work:
   - Document what changed and why
   - Update task descriptions, time estimates, or dependencies
   - Add new tasks or remove obsolete ones
   - Mark changed sections with date and reason
   - Get user confirmation before proceeding with the updated plan
4. **Only mark tasks as "✅ COMPLETE" when you receive:**
   - Terminal output showing successful execution, OR
   - Explicit verbal confirmation from the user that the task is complete
5. **Do NOT assume completion** - even if a command runs without errors, wait for user confirmation
6. **Update PROGRESS.md immediately** after each completed step
7. **If errors occur**, document them in PROGRESS.md and work with user to resolve before proceeding
8. **Maintain the same format and detail level** when updating PROGRESS.md

**Your workflow should be:**
- Read PROGRESS.md to understand current state
- **If user requests changes to the plan**: Update PROGRESS.md first, get confirmation, then proceed
- Execute the next pending task
- Wait for confirmation (terminal output or user saying "done")
- Update PROGRESS.md to mark task as ✅ COMPLETE
- Move to next task

**Command Logging:**
9. **When executing terminal commands**, encourage user to use the command logging system:
   - Source the logging script: `source scripts/shell/log_command.sh`
   - Execute commands with: `log_cmd <command>`
   - Example: `log_cmd aws s3 ls s3://nba-sim-raw-data-lake/`
10. **Reference COMMAND_LOG.md** when debugging similar issues to learn from past solutions
11. **Add solutions to errors** using `log_solution <description>` helper function
12. **CRITICAL - Before committing COMMAND_LOG.md to Git:**
   - Always review for sensitive information (credentials, API keys, passwords, tokens)
   - Sanitize AWS account IDs if sharing publicly
   - Replace sensitive IPs/endpoints with placeholders
   - Remove or redact any Personal Access Tokens (PATs)
   - Remind user to review before any `git add` or `git commit` that includes COMMAND_LOG.md

## Project Overview

NBA Game Simulator & ML Platform - A Python-based AWS data pipeline that:
- Ingests 146K+ historical NBA game JSON files (1999-2025, 119 GB) from ESPN
- Extracts 10% of relevant fields via AWS Glue ETL
- Stores processed data in RDS PostgreSQL (~12 GB after extraction)
- Simulates NBA games using statistical models on EC2
- Trains ML prediction models using SageMaker

**Current Status:** Phase 1 Complete - S3 data lake operational with 119 GB uploaded

## Essential Setup

**Environment activation:**
```bash
# CRITICAL: This project uses Conda, NOT venv
conda activate nba-aws

# Navigate to project
cd /Users/ryanranft/nba-simulator-aws
```

**Verify environment:**
```bash
python --version           # Should show Python 3.11.13
aws --version             # System-wide AWS CLI 2.x (NOT in conda)
aws s3 ls s3://nba-sim-raw-data-lake/
```

## Critical Paths

- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **Original Data:** `/Users/ryanranft/0espn/data/nba/` (119 GB source)
- **S3 Bucket:** `s3://nba-sim-raw-data-lake` (146,115 files)
- **Conda Env:** `/Users/ryanranft/miniconda3/envs/nba-aws`

## Architecture

**5-Phase Pipeline:**

```
Phase 1 (✅): S3 Data Lake
  └─ 146,115 JSON files uploaded

Phase 2 (⏸️): AWS Glue
  ├─ 2.1: Crawler discovers JSON schema
  └─ 2.2: ETL job extracts 10% of fields

Phase 3 (⏸️): RDS PostgreSQL
  └─ Stores extracted data (~12 GB)

Phase 4 (⏸️): EC2 Simulation Engine
  └─ Runs game simulations

Phase 5 (⏸️): SageMaker ML Pipeline
  ├─ Jupyter notebooks for development
  └─ Training jobs for models
```

**Key Architectural Decision:** Extract only 10% of JSON fields during ETL to reduce costs and improve performance (119 GB → 12 GB).

## Git & GitHub Configuration

**Remote URL:** `git@github.com:ryanranft/nba-simulator-aws.git`
**Authentication:** SSH (not HTTPS)
**Branch:** `main` (tracks `origin/main`)
**Repository (web):** https://github.com/ryanranft/nba-simulator-aws

### Important Notes

- This repository uses **SSH authentication**, not HTTPS
- SSH keys are already configured on your system
- No Personal Access Token (PAT) needed for push/pull operations
- Git commands work seamlessly without password prompts
- **Current status:** ✅ Configured and operational

### Common Git Commands

```bash
# Check current status
git status

# View remote configuration
git remote -v
# Should show: git@github.com:ryanranft/nba-simulator-aws.git

# Pull latest changes
git pull origin main

# Add and commit changes
git add <files>
git commit -m "Your commit message"

# Push to GitHub
git push origin main

# View commit history
git log --oneline --graph --all

# View current branch and tracking info
git branch -vv
```

### Creating Commits

**Follow the commit message format:**
```bash
git commit -m "$(cat <<'EOF'
Brief description of changes

Detailed explanation if needed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Troubleshooting

**If you encounter "Permission denied (publickey)" error:**
```bash
# Test SSH connection to GitHub
ssh -T git@github.com
# Should output: "Hi ryanranft! You've successfully authenticated..."

# If this fails, SSH keys may need to be re-added to ssh-agent
ssh-add ~/.ssh/id_rsa  # or your key file name
```

**If remote URL is wrong (shows HTTPS instead of SSH):**
```bash
# Check current remote
git remote -v

# Fix if it shows https:// instead of git@
git remote set-url origin git@github.com:ryanranft/nba-simulator-aws.git

# Verify the change
git remote -v
```

**If you see "diverged branches" error:**
```bash
# Fetch remote changes
git fetch origin

# Rebase your local commits on top of remote
git pull origin main --rebase

# Then push
git push origin main
```

**If push is rejected (non-fast-forward):**
```bash
# Fetch and check what's different
git fetch origin
git log origin/main..main  # Your commits
git log main..origin/main  # Remote commits

# Rebase (recommended) or merge
git pull origin main --rebase
git push origin main
```

## Common Commands

**Access S3 data:**
```bash
# List bucket contents
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/

# Download sample for inspection
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json ./sample.json

# View JSON structure
cat sample.json | python -m json.tool | head -50
```

**Database (when RDS is created):**
```bash
# Connect to RDS
psql -h nba-sim-db.xxxxx.us-east-1.rds.amazonaws.com -U postgres -d nba_simulator

# In psql: check row counts
SELECT COUNT(*) FROM games;
SELECT COUNT(*) FROM player_game_stats;
```

**AWS Resource Management:**
```bash
# Check Glue crawler status
aws glue get-crawler --name nba-data-crawler

# List Glue tables
aws glue get-tables --database-name nba_raw_data

# Start/stop EC2 instance
aws ec2 stop-instances --instance-ids i-xxxxxxxxx
aws ec2 start-instances --instance-ids i-xxxxxxxxx
```

## Data Structure

**S3 Bucket Layout:**
```
s3://nba-sim-raw-data-lake/
├── box_scores/    # 44,828 files - player statistics per game
├── pbp/           # 44,826 files - play-by-play sequences
├── schedule/      # 11,633 files - game schedules by date (YYYYMMDD.json)
└── team_stats/    # 44,828 files - team-level statistics per game
```

**Data Extraction Strategy:**
- **Box Scores:** Extract player_id, player_name, team_id, position, minutes, points, rebounds, assists, steals, blocks, turnovers, FG/3PT/FT stats
- **Play-by-Play:** Extract game_id, period, clock, play_type, scoring_play, player_id, team_id, scores
- **Schedules:** Extract game_id, game_date, home/away team_ids, scores, venue
- **Team Stats:** Extract team_id, game_id, aggregate statistics

**Exclude:** Commentary, photos, broadcast details, video links, historical narratives

## Important Notes

**AWS Configuration:**
- Account: ************
- Region: us-east-1
- IAM User: iam (AdministratorAccess)

**Critical Constraints:**
- AWS CLI is system-wide, NOT in conda (do not `pip install awscli`)
- Data folder (119 GB) is gitignored - never commit to Git
- Python 3.11 required for AWS Glue 4.0 compatibility
- Git/GitHub configured with SSH authentication (operational)

**Cost Awareness:**
- Current: $2.74/month (S3 storage only)
- After Glue + RDS: ~$46/month
- Full deployment: $95-130/month

## Next Steps

See `PROGRESS.md` for detailed phase-by-phase implementation plan with time estimates, cost breakdowns, and step-by-step instructions.

**Immediate next tasks:**
1. Set up AWS Glue Crawler (~45 min, adds $1/month)
2. Provision RDS PostgreSQL (~2-3 hrs, adds $29/month)
3. Create Glue ETL job (~6-8 hrs dev, adds $13/month)

## Development Workflow

**Before starting work:**
```bash
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws
git status
```

**When AWS credentials fail:**
```bash
aws configure
# Enter: access key, secret key, region (us-east-1), output format (json)
```

**PyCharm performance tip:** Mark `data/` folder as "Excluded" in Project Structure settings to prevent indexing 146K+ files.
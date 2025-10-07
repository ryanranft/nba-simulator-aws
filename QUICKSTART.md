# Quick Start Guide

<!-- AUTO-UPDATE TRIGGER: When daily workflow changes (new commands, file locations, workflow shortcuts) -->
<!-- LAST UPDATED: 2025-10-01 -->
<!-- FREQUENCY: As needed (when workflow evolves) -->
<!-- REMINDER: Update when new daily commands added, file locations changed, or common troubleshooting steps identified -->

**One-page reference for common tasks**

---

## Daily Workflow

```bash
# 1. Navigate to project
cd /Users/ryanranft/nba-simulator-aws

# 2. Activate environment
conda activate nba-aws

# 3. Run session startup (recommended at start of each session)
bash scripts/shell/session_startup.sh

# 4. Check Git status
git status

# 5. Start working!

# 6. At session end
bash scripts/shell/session_end.sh
```

---

## Common Commands

### Environment
```bash
# Activate conda environment
conda activate nba-aws

# Check Python version
python --version  # Should be 3.11.13

# Check installed packages
pip list
```

### AWS
```bash
# Check who you're logged in as
aws sts get-caller-identity

# List S3 bucket contents
aws s3 ls s3://nba-sim-raw-data-lake/

# Check current AWS costs
./scripts/aws/check_costs.sh

# Download sample file
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/131105001.json ./sample.json
```

### Git
```bash
# Check status
git status

# Pull latest changes
git pull origin main --rebase

# Stage and commit changes
git add filename
git commit -m "Your message"

# Push to GitHub
git push origin main

# View commit history
git log --oneline -10
```

### Command Logging
```bash
# Load logging functions
source scripts/shell/log_command.sh

# Execute and log command
log_cmd aws s3 ls s3://nba-sim-raw-data-lake/

# Add note to last command
log_note This command lists all S3 folders

# Add solution to last error
log_solution Fixed by updating AWS credentials
```

### Conversation Tracking
```bash
# RECOMMENDED WORKFLOW (captures conversation → commit linkage):

# 1. Export Claude Code conversation
#    - In Claude Code, export this conversation
#    - Save as: CHAT_LOG.md in project root

# 2. Commit your changes
git add .
git commit -m "Your commit message"

# 3. Archive conversation with commit SHA
bash scripts/maintenance/archive_chat_by_next_sha.sh
#    - Saves as: chat-<SHA>-original.md (with credentials)
#    - Saves as: chat-<SHA>-sanitized.md (safe to share)
#    - Archive location: ~/sports-simulator-archives/nba/conversations/

# 4. Clean up (optional)
rm CHAT_LOG.md  # Remove temporary file

# Session end checklist (shows reminders)
bash scripts/shell/session_end.sh
```

---

## Key File Locations

```
/Users/ryanranft/nba-simulator-aws/
├── CLAUDE.md                    # Quick reference for Claude Code
├── PROGRESS.md                  # Detailed project status
├── COMMAND_LOG.md               # Command execution history
├── .env.example                 # Environment variables template
├── docs/
│   ├── SETUP.md                 # Complete setup guide
│   ├── STYLE_GUIDE.md           # Code style preferences
│   ├── TESTING.md               # Testing strategy
│   ├── TROUBLESHOOTING.md       # Common issues & solutions
│   └── adr/                     # Architecture decisions
├── scripts/
│   ├── shell/
│   │   ├── session_startup.sh    # Session initialization checklist
│   │   ├── session_end.sh        # Session end reminder
│   │   ├── check_chat_log.sh     # Verify CHAT_LOG.md before commits
│   │   ├── check_machine_health.sh  # Comprehensive health check
│   │   ├── log_command.sh        # Command logging
│   │   └── sanitize_command_log.sh  # Security sanitization
│   ├── aws/
│   │   └── check_costs.sh        # AWS cost tracking
│   └── etl/                      # ETL scripts (⏸️ to be created)
├── sql/                         # Database schemas (⏸️ to be created)
└── tests/                       # Test files (⏸️ to be created)
```

---

## Quick Checks

### Is my environment set up correctly?
```bash
./scripts/shell/check_machine_health.sh
```

### Can I access AWS?
```bash
aws sts get-caller-identity
aws s3 ls s3://nba-sim-raw-data-lake/
```

### Is GitHub SSH working?
```bash
ssh -T git@github.com
# Should see: "Hi [username]! You've successfully authenticated..."
```

### What are my AWS costs?
```bash
./scripts/aws/check_costs.sh
```

---

## Troubleshooting Quick Fixes

**Problem: Conda environment not found**
```bash
conda create -n nba-aws python=3.11.13 -y
conda activate nba-aws
pip install boto3 pandas numpy psycopg2-binary sqlalchemy
```

**Problem: AWS credentials not configured**
```bash
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1), Output (json)
```

**Problem: SSH permission denied**
```bash
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com
```

**Problem: Git push rejected**
```bash
git pull origin main --rebase
git push origin main
```

**Full troubleshooting guide:** See `docs/TROUBLESHOOTING.md`

---

## Next Steps

**Current Phase:** Phase 0 Complete (Data Collection), All 6 core phases complete

**Next Tasks:**
1. Set up AWS Glue Crawler (45 min) - See PROGRESS.md Phase 2.1
2. Provision RDS PostgreSQL (2-3 hrs) - See PROGRESS.md Phase 3.1
3. Create Glue ETL job (6-8 hrs) - See PROGRESS.md Phase 2.2

**Detailed plan:** See `PROGRESS.md`

---

## Documentation Map

| Need... | Read... |
|---------|---------|
| Claude Code guidelines | `CLAUDE.md` |
| Project status & roadmap | `PROGRESS.md` |
| Setup instructions | `docs/SETUP.md` |
| Code style rules | `docs/STYLE_GUIDE.md` |
| Testing approach | `docs/TESTING.md` |
| Common errors | `docs/TROUBLESHOOTING.md` |
| Why we made decisions | `docs/adr/README.md` |
| Command history | `COMMAND_LOG.md` |

---

## Cost Tracking

**Current:** ~$2.74/month (S3 storage only)

**After Phase 2 & 3:** ~$46/month (+ Glue + RDS)

**Full deployment:** $95-130/month

**Check costs:** `./scripts/aws/check_costs.sh`

**Budget alerts:** Set up in AWS Console → Budgets

---

## Getting Help

1. **Environment issues?** → `./scripts/shell/check_machine_health.sh`
2. **Common errors?** → `docs/TROUBLESHOOTING.md`
3. **How to...?** → `docs/SETUP.md` or `PROGRESS.md`
4. **Why did we...?** → `docs/adr/README.md`
5. **Past solutions?** → `COMMAND_LOG.md`

---

**Last Updated:** 2025-10-02
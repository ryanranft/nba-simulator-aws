# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Decision Tree

**When user asks to do something:**
1. **Is it the next pending task in PROGRESS.md?** → Proceed
2. **Is it skipping ahead?** → Check prerequisites first, warn if missing
3. **Is it changing the plan?** → Update PROGRESS.md first, get approval
4. **Will it cost money?** → Warn user with estimate, get confirmation
5. **Could it break something?** → Explain risk, suggest backup/test approach

**During the session:**
1. **Is context at 75%+?** → Auto-save conversation to CHAT_LOG.md immediately
2. **Is context at 90%+?** → Strongly urge user to commit NOW
3. **User says "save this conversation"?** → Write verbatim transcript to CHAT_LOG.md

**When a command fails:**
1. Check `TROUBLESHOOTING.md` for known solution
2. If unknown, STOP and ask user for guidance
3. Don't attempt multiple fixes automatically
4. Log solution with `log_solution` after resolving

## Critical Workflows (See Detailed Docs)

**Security & Git:** See `docs/SECURITY_PROTOCOLS.md`
- Pre-commit security scans
- Pre-push inspection workflow (automated via `scripts/shell/pre_push_inspector.sh`)
- Credential rotation schedules
- GitHub secret scanning setup

**Archiving & Conversation History:** See `docs/ARCHIVE_PROTOCOLS.md`
- File deletion protocol (archive first)
- Conversation archiving (auto at 75%/90% context)
- Finding past conversations
- Auto-generated commit logs

**Session Startup:** See `docs/SESSION_INITIALIZATION.md`
- Run `session_manager.sh start` automatically
- Progress tracking protocol
- When to update documentation
- Command logging procedures

**Documentation System:** See `docs/DOCUMENTATION_SYSTEM.md`
- Documentation trigger system
- Update schedules (manual vs automated)
- Monthly review checklist
- Workflow documentation system

## Instructions for Claude

**Session Initialization & Daily Workflows:** See `docs/CLAUDE_SESSION_INIT.md`

**Progress Tracking:** See `docs/CLAUDE_PROGRESS_TRACKING.md`

**Command Logging:** See `docs/CLAUDE_COMMAND_LOGGING.md`

**Documentation Quick Reference:** See `docs/CLAUDE_DOCUMENTATION_QUICK_REF.md`

## Project Overview

NBA Game Simulator & ML Platform - A Python-based AWS data pipeline that:
- Ingests 146K+ historical NBA game JSON files (1999-2025, 119 GB) from ESPN
- Extracts 10% of relevant fields via AWS Glue ETL
- Stores processed data in RDS PostgreSQL (~12 GB after extraction)
- Simulates NBA games using statistical models on EC2
- Trains ML prediction models using SageMaker

**Current Status:** Phase 1 Complete - S3 data lake operational with 119 GB uploaded

**Development Machine:** MacBook Pro 16-inch, 2023 (M2 Max, 96GB RAM, macOS Sequoia 15.6.1)
- See `MACHINE_SPECS.md` for complete hardware/software specifications
- Code is optimized for Apple Silicon (ARM64) architecture
- Uses Homebrew for system packages and Miniconda for Python environment

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
- **Conversation Archives:** `~/sports-simulator-archives/nba/<commit-sha>/CHAT_LOG_*.md`
- **Quick Reference:** `QUICKSTART.md` (one-page command reference)
- **Machine Specs:** `MACHINE_SPECS.md` (hardware, software versions, compatibility notes)
- **File Inventory:** `FILE_INVENTORY.md` (auto-generated summaries of 28 documented files)
- **Config Files:** `config/aws_config.yaml` (AWS resource definitions - minimal, to be populated in Phase 2+)
- **Maintenance Scripts:** `scripts/maintenance/` (generate_inventory.py, sync_progress.py, update_docs.sh, archive_chat_log.sh)
- **Shell Utilities:** `scripts/shell/` (session_manager.sh, pre_push_inspector.sh, log_command.sh, sanitize_command_log.sh, save_conversation.sh)
- **AWS Scripts:** `scripts/aws/` (check_costs.sh)
- **Cost Tracking:** `scripts/aws/check_costs.sh` (AWS spending monitor)

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

**Status:** ✅ Configured with SSH authentication
**Remote:** `git@github.com:ryanranft/nba-simulator-aws.git`
**Branch:** `main` (tracks `origin/main`)
**Repository:** https://github.com/ryanranft/nba-simulator-aws

**Key points:**
- Uses SSH (not HTTPS), no password prompts needed
- SSH keys already configured
- See `QUICKSTART.md` lines 56-73 for common commands
- See `docs/TROUBLESHOOTING.md` lines 336-508 for Git issues
- See `ADR-005` for full SSH vs HTTPS rationale

**CRITICAL - Security Protocol Before ANY Git Commit:**

Before running `git commit`, ALWAYS perform automatic security scan:

```bash
# Step 1: Check staged files for sensitive data (comprehensive pattern)
git diff --staged | grep -E "(AWS_ACCESS_KEY[A-Z0-9]{16}|aws_secret|secret_access_key|aws_session_token|password|api[_-]?key|Bearer [A-Za-z0-9_-]+|BEGIN [REDACTED] KEY|ghp_[A-Za-z0-9]{36}|github_pat|postgres:|postgresql://.*:.*@|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)" -i

# Step 2: Check commit message for sensitive data
grep -E "(AWS_ACCESS_KEY|aws_secret|password|192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)" .git/COMMIT_EDITMSG -i

# Step 3: If ANY matches found:
#   - STOP immediately
#   - Show matches to user
#   - NEVER commit AWS keys, secrets, or private IPs under any circumstances
#   - Remove sensitive data or abort commit

# Step 4: What to check for:
#   ❌ AWS access keys (AWS_ACCESS_KEY[A-Z0-9]{16})
#   ❌ AWS secret keys (aws_secret_access_key)
#   ❌ AWS session tokens (aws_session_token)
#   ❌ Private IP addresses (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
#   ❌ ANY IP addresses (per user requirement)
#   ❌ Passwords, API keys, Bearer tokens
#   ❌ SSH private keys (BEGIN + PRIVATE + KEY)
#   ❌ GitHub tokens (ghp_..., github_pat_...)
#   ❌ Database connection strings with passwords (postgresql://user:pass@host)
```

**Whitelist - Safe patterns (don't trigger false positives):**
```bash
# These are OK in documentation:
✅ Placeholder examples: "<YOUR_AWS_ACCESS_KEY_HERE>", "your-access-key-here", "<INSERT_KEY_HERE>"
✅ Documentation keywords: describing what to check for (like this list)
✅ Redacted credentials: [REDACTED], [Private network], [Router]
✅ Environment variable format: AWS_ACCESS_KEY_ID= (without value)
✅ Public DNS: Not allowed per user requirement (remove ALL IPs)

# NEVER use these placeholders (trigger security scanners):
❌ AWS_ACCESS_KEY**************** (still contains AWS_ACCESS_KEY prefix)
❌ Any pattern starting with AWS_ACCESS_KEY, even if redacted
```

**Security Check Protocol:**
1. Run grep scan BEFORE staging files
2. **If matches found: STOP immediately and show user:**
   ```bash
   # Save diff to temp file
   git diff --staged > /tmp/staged_diff.txt

   # Show ALL flagged lines with line numbers
   grep -n -E "(pattern)" -i /tmp/staged_diff.txt

   # Show FULL CONTEXT (10 lines before/after each match)
   grep -E "(pattern)" -i -B 10 -A 10 /tmp/staged_diff.txt
   ```
3. **Present to user:**
   - Show flagged line numbers
   - Show full context around each match
   - Explain what was detected (pattern definitions vs actual secrets)
   - Explain if deletions (safe) or additions (review needed)
   - **Ask explicitly:** "Do you approve bypassing pre-commit hook? [YES/NO]"
4. **Wait for user's explicit YES or NO response**
5. Only proceed with `--no-verify` if user responds YES
6. NEVER assume approval - always ask first

**CRITICAL: NEVER use --no-verify without:**
- ✅ Showing user ALL flagged lines with full context
- ✅ Explaining what was flagged and why
- ✅ Getting explicit YES approval from user

**NEVER commit without this security check.**

**Commit format (include co-authorship footer):**
```bash
git commit -m "$(cat <<'EOF'
Brief description of changes

Detailed explanation if needed

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
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

**Note:** Local data folder names differ from S3 folder names:
- Local: `data/nba_box_score/`, `data/nba_pbp/`, `data/nba_schedule_json/`, `data/nba_team_stats/`
- S3: `box_scores/`, `pbp/`, `schedule/`, `team_stats/`

**Data Extraction Strategy:**
- **Box Scores:** Extract player_id, player_name, team_id, position, minutes, points, rebounds, assists, steals, blocks, turnovers, FG/3PT/FT stats
- **Play-by-Play:** Extract game_id, period, clock, play_type, scoring_play, player_id, team_id, scores
- **Schedules:** Extract game_id, game_date, home/away team_ids, scores, venue
- **Team Stats:** Extract team_id, game_id, aggregate statistics

**Exclude:** Commentary, photos, broadcast details, video links, historical narratives

**Data File Characteristics:**
- **File Size:** Each JSON file is ~700KB and contains 17,000-19,000 lines
- **Content Warning:** Files contain full ESPN web scraping data including:
  - CDN paths, JavaScript chunks, CSS assets (majority of file size)
  - Actual game data embedded within web page metadata
- **ETL Implication:** Glue ETL must parse deeply nested JSON to extract relevant game statistics
- **First file date:** 131105001.json (November 5, 2013 season start)

## Important Notes

**AWS Configuration:**
- Account: <your-aws-account-id>
- Region: us-east-1
- IAM User: iam (AdministratorAccess)

**AWS Credentials Storage (CRITICAL):**
- **Primary Location:** `~/.aws/credentials` (AWS CLI standard, chmod 600)
- **Backup Location:** Store encrypted backups outside project directory (never commit)
- **NEVER:**
  - Copy credentials into project directory
  - Store credentials in environment variables
  - Reference credentials in code (boto3 auto-reads from ~/.aws/credentials)
  - Commit credential files to Git
  - Document exact paths to credential backups (security risk)

**Critical Constraints:**
- AWS CLI is system-wide, NOT in conda (do not `pip install awscli`)
- Data folder (119 GB) is gitignored - never commit to Git
- Python 3.11 required for AWS Glue 4.0 compatibility
- Git/GitHub configured with SSH authentication (operational)
- **Python Dependencies:** 10 packages in requirements.txt (boto3, pandas, numpy, pyarrow, psycopg2-binary, sqlalchemy, pytest, jupyter, python-dotenv, pyyaml, tqdm)
- **Key Libraries:** boto3 (AWS SDK), pandas (data processing), pytest (testing), jupyter (analysis)

**Cost Awareness (IMPORTANT):**
- **Current:** $2.74/month (S3 storage only)
- **After Glue + RDS:** ~$46/month
- **Full deployment:** $95-130/month
- **Monthly budget target:** $150 (alert if approaching)
- **ALWAYS warn user before:**
  - Creating RDS instances (~$29/month)
  - Creating EC2 instances (~$5-15/month)
  - Creating Glue jobs (~$13/month)
  - Creating SageMaker notebooks (~$50/month)
- **Suggest cost estimates** before proceeding
- **Remind to stop/delete** resources when done testing

**Data Safety Protocol:**
- NEVER delete or modify S3 bucket contents without explicit user request
- NEVER drop database tables without user confirmation
- NEVER commit `.env`, credentials, or sensitive data
- ALWAYS run `sanitize_command_log.sh` before committing COMMAND_LOG.md
- Backup before destructive operations (provide backup command)

**For detailed procedures, see:**
- `docs/ARCHIVE_PROTOCOLS.md` - File deletion, conversation archiving, finding past work
- `docs/SECURITY_PROTOCOLS.md` - Credential rotation, GitHub secret scanning, security layers

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

**Weekly maintenance:**
```bash
# Update documentation automatically
make update-docs

# Check if PROGRESS.md matches AWS reality
make sync-progress

# Monitor AWS costs
make check-costs
```

**Archive Management:**
```bash
# View archive git history
git -C ~/sports-simulator-archives/nba log --oneline

# Search archived conversations
git -C ~/sports-simulator-archives/nba grep "keyword" -- "*/CHAT_LOG_*.md"

# Check archive storage size
du -sh ~/sports-simulator-archives/nba
du -sh ~/sports-simulator-archives/nba/.git

# List all archived commits
ls -1 ~/sports-simulator-archives/nba/ | grep -E '^[0-9a-f]{40}$'
```

**Makefile Commands (Recommended):**
```bash
# View all available commands
make help

# Note: Run `make help` to see currently implemented commands
# Some commands listed below may be added in future phases

# File inventory and summaries
make inventory              # Generate FILE_INVENTORY.md with file summaries
make describe FILE=path     # Show detailed info about specific file

# Verification
make verify-all             # Run all checks (env + AWS + files)
make verify-env             # Check conda environment
make verify-aws             # Check AWS credentials and S3

# Utilities
make stats                  # Show project statistics
make backup                 # Create backup of critical files
make clean                  # Remove temporary files
make git-status             # Show git status and recent commits
```

**PyCharm performance tip:** Mark `data/` folder as "Excluded" in Project Structure settings to prevent indexing 146K+ files.

## Known Documentation Gaps

- **README.md:** Currently empty - should contain project overview for GitHub visitors
  - Suggest: Quick description, setup link, architecture diagram, current status
  - Recommend creating after Phase 2 completion for more complete project overview
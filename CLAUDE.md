# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Decision Tree

**When user asks to do something:**
1. **Is it the next pending task in PROGRESS.md?** → Proceed
2. **Is it skipping ahead?** → Check prerequisites first, warn if missing
3. **Is it changing the plan?** → Update PROGRESS.md first, get approval
4. **Will it cost money?** → Warn user with estimate, get confirmation
5. **Could it break something?** → Explain risk, suggest backup/test approach

**When a command fails:**
1. Check `TROUBLESHOOTING.md` for known solution
2. If unknown, STOP and ask user for guidance
3. Don't attempt multiple fixes automatically
4. Log solution with `log_solution` after resolving

## Instructions for Claude

**Session Initialization:**
- Run `make verify-all` to check environment, AWS, and files
- Or individually: `make verify-env`, `make verify-aws`
- Review recent commits: `git log --oneline -5` or `make git-status`
- Check current costs: `make check-costs`
- Identify current phase from PROGRESS.md
- View all available commands: `make help`

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
   - Terminal output showing successful execution (exit code 0, expected output), AND
   - Either: User says "done", "complete", "looks good", or similar affirmation
   - OR: User proceeds to ask about the next task (implicit confirmation)
   - **Exception:** Minor tasks (<5 min) can be auto-marked if command succeeds with clear success output
5. **Do NOT assume completion** - even if a command runs without errors, wait for user confirmation
6. **Update PROGRESS.md immediately** after each completed step
7. **If errors occur**, document them in PROGRESS.md and work with user to resolve before proceeding
8. **Maintain the same format and detail level** when updating PROGRESS.md

**Update PROGRESS.md when:**
- ✅ Completing any phase or sub-phase
- ⏸️ Discovering blockers or missing prerequisites
- 📝 Changing approach or architecture
- ❌ Encountering errors that delay timeline
- ✅ User explicitly confirms task completion
- 💰 Actual costs differ significantly from estimates

**Error Handling Protocol:**
- If a command fails, STOP and report to user immediately
- Do NOT attempt multiple fixes without user guidance
- Check `TROUBLESHOOTING.md` for known solutions first
- If unknown error, log with `log_solution` after resolving
- Update PROGRESS.md with error details and resolution

**Context Awareness:**
- Check what phase we're in before suggesting commands
- Don't suggest Phase 3 commands if Phase 2 isn't complete
- Verify prerequisites exist before executing dependent tasks
- Use `python scripts/maintenance/sync_progress.py` if unsure of current state

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

**Documentation System (Quick Reference):**

**Architecture & Decisions:**
- **ADRs** (`docs/adr/README.md`) - Why we made key technical decisions
  - ADR-001: Redshift exclusion (saves $200-600/month)
  - ADR-002: 10% data extraction (119 GB → 12 GB)
  - ADR-003: Python 3.11 (Glue compatibility)
  - ADR-005: Git SSH authentication
  - Use `docs/adr/template.md` for new decisions

**Code Quality:**
- **Style Guide** (`docs/STYLE_GUIDE.md`) - Required for all code
  - Python: PEP 8, snake_case, type hints required
  - SQL: Uppercase keywords, explicit JOINs
  - Docstrings required for all functions
- **Testing** (`docs/TESTING.md`) - pytest strategy
  - Priority: Data validation (scores, dates, required fields)
  - Mock AWS with moto library
- **Troubleshooting** (`docs/TROUBLESHOOTING.md`) - **Check FIRST when errors occur**
  - 28 documented issues with solutions
  - 7 categories: Environment, AWS, Git, ETL, Database, Performance, Security

**Environment & Setup:**
- **Setup Guide** (`docs/SETUP.md`) - Fresh environment setup (11 steps)
- **Environment Variables** (`.env.example`) - 35 variables, NEVER commit `.env`
- **verify_setup.sh** - Quick health check script

**Operational:**
- **QUICKSTART.md** - Daily commands, file locations, quick fixes
- **check_costs.sh** - AWS spending monitor (run weekly)
- **Documentation Maintenance** (`docs/DOCUMENTATION_MAINTENANCE.md`)
  - Weekly: `update_docs.sh` (auto-updates costs, timestamps, stats)
  - Weekly: `sync_progress.py` (checks AWS vs PROGRESS.md)
  - Monthly: Review checklist for stale docs
  - **NEVER auto-commit** - always review changes

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
- **Quick Reference:** `QUICKSTART.md` (one-page command reference)
- **Maintenance Scripts:** `scripts/maintenance/` (doc automation)
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

**Makefile Commands (Recommended):**
```bash
# View all available commands
make help

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
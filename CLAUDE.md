# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Order - Follow This Sequence

**See `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md` for workflow index and execution order.**

**All detailed workflows are in: `docs/claude_workflows/workflow_descriptions/`**

**System now contains 26 modular workflows:**
- 🚀 Session Start & End workflows
- 📋 Decision & Plan Change workflows
- 💻 Task Execution & File Creation workflows
- 🔒 Git Commit & Push workflows (security protocols)
- 🧪 Testing workflows (TDD, unit, integration, pre-deployment)
- 🔧 Environment Setup & Verification workflows
- 💰 Cost Management workflows (before creating, tracking, optimization)
- 💾 Backup & Recovery workflows
- 🔄 Maintenance Schedule workflows (weekly, monthly)
- 📊 Data Validation workflows (pre-ETL, pre-simulation, pre-ML)
- 🔍 Systematic Troubleshooting Protocol
- 🔐 Credential Rotation workflows
- ☁️ AWS Resource Setup workflows (Glue, RDS, EC2, SageMaker)
- 🗄️ Database Migration workflows
- 🔧 Makefile Quick Reference

**Navigation pattern:**
```
1. Read PROGRESS.md (identify current task/phase)
2. Read docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md (find relevant workflow number)
3. Read docs/claude_workflows/workflow_descriptions/XX_workflow_name.md (get detailed steps)
4. Execute workflow steps
```

**Quick reference - Every session follows this order:**
1. Initialize session (`session_manager.sh start`) - show output to user
2. Orient to current state (read PROGRESS.md)
3. Ask about completed work
4. Wait for user's task request
5. Follow decision workflow (check plan, prerequisites, costs, risks)
6. Execute task → Document outcome → Wait for confirmation
7. Update PROGRESS.md → Suggest next action
8. Follow security protocol for commits/pushes
9. Monitor context (auto-save at 75%, warn at 90%)

**Critical decision points:**
- **Skipping ahead?** → Check prerequisites, warn if missing
- **Changing the plan?** → Update PROGRESS.md first, get approval
- **Will it cost money?** → Warn with estimate, get confirmation
- **Could it break something?** → Explain risk, suggest backup/test approach
- **Command fails?** → Check TROUBLESHOOTING.md, stop, ask for guidance

**How workflows integrate with PROGRESS.md:**

**✅ NEW MODULAR STRUCTURE (Implemented Oct 2, 2025):**
- PROGRESS.md is now a lightweight index (~350 lines, was 1,244 lines)
- Individual phase files in `docs/phases/` contain detailed implementation steps
- Phase files explicitly reference workflow numbers (e.g., "Follow workflow #24")
- Clear hierarchy: PROGRESS.md → Phase file → Workflow file

**Phase files:**
- PHASE_1_S3_DATA_LAKE.md (complete)
- PHASE_2_AWS_GLUE.md (complete)
- PHASE_3_DATABASE.md (complete)
- PHASE_4_SIMULATION_ENGINE.md (pending)
- PHASE_5_MACHINE_LEARNING.md (pending)
- PHASE_6_ENHANCEMENTS.md (optional)

**Benefits:**
- ✅ Read only what you need (72% reduction in PROGRESS.md size)
- ✅ Faster file operations (350 lines vs 1,244)
- ✅ Reduced context usage (90%+ savings)
- ✅ Easier maintenance (update one phase without affecting others)
- ✅ Scalable (easy to add new phases)
- ✅ Clear separation of concerns

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

See `README.md` for complete project description, architecture, current status, and development machine specifications.

## Essential Setup

See `docs/SETUP.md` for complete environment setup and verification.

**Quick activation:**
```bash
conda activate nba-aws
cd /Users/ryanranft/nba-simulator-aws
```

## Critical Paths

See `docs/SETUP.md` for complete project paths and directory structure.

**Most critical:**
- **Project:** `/Users/ryanranft/nba-simulator-aws`
- **S3 Bucket:** `s3://nba-sim-raw-data-lake` (146,115 files)
- **Archives:** `~/sports-simulator-archives/nba/`

## Architecture

See `README.md` for complete 5-phase pipeline architecture and key architectural decisions.

## Git & GitHub Configuration

See `QUICKSTART.md` for Git commands and `docs/SECURITY_PROTOCOLS.md` for complete security procedures.

**CRITICAL - Before ANY Git Operation:**

- **Before commit:** Run security scan (see `docs/SECURITY_PROTOCOLS.md` for scan commands and protocols)
- **Before push:** Run `scripts/shell/pre_push_inspector.sh full` (7-step automated workflow)
- **NEVER commit without security scan** - check for AWS keys, secrets, IPs, passwords
- **NEVER push without user approval** - always ask "Ready to push to GitHub?"
- **If hook blocks commit/push:** Show user flagged lines, explain findings, get explicit bypass approval

See `docs/SECURITY_PROTOCOLS.md` for:
- Complete security scan bash commands
- Whitelist patterns (safe vs unsafe)
- Security check protocol (step-by-step)
- Pre-push inspection workflow (repository cleanup)
- Credential rotation schedules
- GitHub secret scanning setup

## Common Commands

See `QUICKSTART.md` for all common commands (S3, database, AWS resources, daily workflow).

## Data Structure

See `docs/DATA_STRUCTURE_GUIDE.md` for complete S3 bucket layout, data extraction strategy, and file characteristics.

## Important Notes

**AWS Configuration & Credentials:** See `docs/SETUP.md`

**Cost Awareness (IMPORTANT):**
- **Current:** $2.74/month (S3 storage only)
- **Full deployment:** $95-130/month
- **Budget target:** $150/month
- **ALWAYS warn user before creating:**
  - RDS instances (~$29/month)
  - EC2 instances (~$5-15/month)
  - Glue jobs (~$13/month)
  - SageMaker notebooks (~$50/month)

See `PROGRESS.md` for complete cost breakdowns.

**Data Safety Protocol:**
- NEVER delete or modify S3 bucket contents without explicit user request
- NEVER drop database tables without user confirmation
- NEVER commit `.env`, credentials, or sensitive data
- Backup before destructive operations

See `docs/SECURITY_PROTOCOLS.md` for complete security procedures.

## Next Steps

See `PROGRESS.md` for detailed phase-by-phase implementation plan with time estimates, cost breakdowns, and step-by-step instructions.

## Development Workflow

See `QUICKSTART.md` for complete daily workflow, maintenance commands, archive management, and Makefile commands.
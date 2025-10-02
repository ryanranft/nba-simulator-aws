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

See `QUICKSTART.md` for Git commands and `docs/SECURITY_PROTOCOLS.md` for security procedures.

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
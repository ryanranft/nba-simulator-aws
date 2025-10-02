# Documentation System

This document contains the documentation trigger system, update schedules, and maintenance procedures.

## Documentation Trigger System

This project uses an automated documentation update trigger system. Each key documentation file has an embedded HTML comment trigger that signals when it needs updating.

**Read these files to understand the system:**
1. `.documentation-triggers.md` - Central registry of all documentation update triggers
2. `session_manager.sh start` output - Shows documentation status checks automatically

**Key documentation files with triggers:**
- `CHAT_LOG.md` - **Auto-updated at 75% and 90% context** (Claude handles automatically)
- `COMMAND_LOG.md` - Update after EVERY code change
- `FILE_INVENTORY.md` - Run `make inventory` before every `git add .`
- `PROGRESS.md` - Update after completing ANY task
- `.session-history.md` - Append after every commit
- `MACHINE_SPECS.md` - Verify at session start

**The triggers tell you:**
- ✅ When each file should be updated (triggering event)
- ✅ How often (frequency)
- ✅ What command to run (if automated)
- ✅ Last update date

**At session start, `session_manager.sh start` automatically checks:**
- FILE_INVENTORY.md age (warns if > 7 days)
- Session history status
- Command log status
- PROGRESS.md task counts
- Stale documentation (> 30 days)

**See `.documentation-triggers.md` for complete documentation trigger system reference.**

## Documentation Update Triggers

The following documentation requires MANUAL updates (cannot be automated):

| Document | Update When | How to Update |
|----------|-------------|---------------|
| **MACHINE_SPECS.md** | Daily (start of each session) | Run session startup checklist, update version table with current software versions |
| **PROGRESS.md** | After completing phase/task | Change ⏸️ PENDING → ✅ COMPLETE, update "Last Updated" |
| **PROGRESS.md** | After creating AWS resources | Run `make check-costs`, update cost estimates with actuals |
| **TROUBLESHOOTING.md** | After solving new error | Add new section with problem/solution, run `make inventory` |
| **ADRs** | After architectural decision | Create `docs/adr/00X-name.md` from template, update `docs/adr/README.md` |
| **STYLE_GUIDE.md** | When code style preference emerges | Add rule with example, explain reasoning |
| **QUICKSTART.md** | When daily workflow changes | Update relevant command section |
| **TESTING.md** | When testing strategy evolves | Update approach, add examples |
| **.env.example** | When new env variables needed | Add variable with description |
| **COMMAND_LOG.md** | After every significant command OR code change | Use `log_cmd`, `log_note`, `log_solution` for commands; manually log all code snippets with outcomes (success/failure, errors, lessons learned) |

## Automated Documentation (Run Weekly)

- `make update-docs` - Updates timestamps, costs, stats, validates links
- `make sync-progress` - Checks PROGRESS.md vs actual AWS resources
- `make inventory` - Updates FILE_INVENTORY.md with file summaries
- `make check-costs` - Reports current AWS spending

## Monthly Documentation Review Checklist

1. Run all automation: `make update-docs`, `make sync-progress`, `make check-costs`
2. Review stale files (30+ days old) - update or mark as reviewed
3. Verify PROGRESS.md phases match reality (✅/⏸️ status)
4. Check cost estimates vs actuals in PROGRESS.md
5. Commit: `git commit -m "Monthly documentation refresh - $(date +%Y-%m)"`

## Documentation System (Quick Reference)

### Architecture & Decisions

**ADRs** (`docs/adr/README.md`) - Why we made key technical decisions
- ADR-001: Redshift exclusion (saves $200-600/month)
- ADR-002: 10% data extraction (119 GB → 12 GB)
- ADR-003: Python 3.11 (Glue compatibility)
- ADR-004: Git without GitHub push (superseded by ADR-005)
- ADR-005: Git SSH authentication
- ADR-006: Session initialization automation
- Use `docs/adr/template.md` for new decisions
- See `docs/SESSION_INITIALIZATION.md` for when to create ADRs

### Code Quality

**Style Guide** (`docs/STYLE_GUIDE.md`) - Required for all code
- Python: PEP 8, snake_case, type hints required
- SQL: Uppercase keywords, explicit JOINs
- Docstrings required for all functions

**Testing** (`docs/TESTING.md`) - pytest strategy
- Priority: Data validation (scores, dates, required fields)
- Mock AWS with moto library

**Troubleshooting** (`docs/TROUBLESHOOTING.md`) - **Check FIRST when errors occur**
- 28 documented issues with solutions
- 7 categories: Environment, AWS, Git, ETL, Database, Performance, Security

### Environment & Setup

**Setup Guide** (`docs/SETUP.md`) - Fresh environment setup (11 steps)

**Environment Variables** (`.env.example`) - 35 variables, NEVER commit `.env`

**check_machine_health.sh** - Comprehensive 14-point health check script (replaces verify_setup.sh)

### Operational

**QUICKSTART.md** - Daily commands, file locations, quick fixes

**check_costs.sh** - AWS spending monitor (run weekly)

**Documentation Maintenance** (`docs/DOCUMENTATION_MAINTENANCE.md`)
- Weekly: `update_docs.sh` (auto-updates costs, timestamps, stats)
- Weekly: `sync_progress.py` (checks AWS vs PROGRESS.md)
- Monthly: Review checklist for stale docs
- **NEVER auto-commit** - always review changes

## Workflow Documentation System

**CRITICAL - Workflow Documentation System:**

User will provide specific instructions when needed. All workflow documentation methodology and procedures are documented in local-only files (never committed to GitHub) for security.

**WORKFLOW AUTOMATION SYSTEM:**

This project uses TWO automated documentation systems:

1. **Conversation Archiving** (see `docs/ARCHIVE_PROTOCOLS.md`)
   - Saves Claude conversations automatically at 75%/90% context
   - Archives to SHA-based directories: `~/sports-simulator-archives/nba/<commit-sha>/`
   - Zero conversation loss design (verbatim transcripts)
   - Links conversations to code changes via commit SHA

2. **Workflow Documentation** (local only, NEVER on GitHub)
   - Read: `~/sports-simulator-archives/nba/conversations/mappings/CLAUDE_INSTRUCTIONS.md`
   - Session summaries and aggregation logs
   - Uses recipe-manager-dev-logs as example patterns
   - Local index files translate references to actual workflow execution logs

**These systems work together:**
- **Conversation archiving** captures raw discussions (complete verbatim exchanges)
- **Workflow documentation** provides curated summaries (high-level session reports)

**Instructions are stored locally only (NEVER on GitHub):**
- Read: `~/sports-simulator-archives/nba/conversations/mappings/CLAUDE_INSTRUCTIONS.md`
- This file contains complete instructions for the workflow automation and log aggregation system
- All implementation details are kept local for security

**When user references past work:**
- User may say: "Check the workflow from October" or "Review the automation logs"
- Follow the instructions in CLAUDE_INSTRUCTIONS.md to access the workflow documentation system
- The system uses a reference examples repository (recipe-manager-dev-logs) with example workflow patterns
- Local index files translate references to actual workflow execution logs

**Quick reference:**
- Public repository: https://github.com/ryanranft/recipe-manager-dev-logs (example patterns only)
- Local index files: Connect public examples to real workflow logs
- User will provide access to configuration guide when needed
# Claude Progress Tracking Protocol

This file contains the complete protocol for how Claude tracks and updates progress in PROGRESS.md.

## CRITICAL - Progress Tracking Protocol

### 1. Always Read PROGRESS.md First

Understand what has been completed and what's next before starting any work.

### 2. Follow PROGRESS.md Sequentially

Start from the first "⏸️ PENDING" or "⏳ IN PROGRESS" task. Do not skip ahead unless explicitly instructed.

### 3. If the Plan Changes

Update PROGRESS.md BEFORE proceeding with new work:
- Document what changed and why
- Update task descriptions, time estimates, or dependencies
- Add new tasks or remove obsolete ones
- Mark changed sections with date and reason
- Get user confirmation before proceeding with the updated plan

### 4. Only Mark Tasks as "✅ COMPLETE" When You Receive

- Terminal output showing successful execution (exit code 0, expected output), AND
- Either: User says "done", "complete", "looks good", or similar affirmation
- OR: User proceeds to ask about the next task (implicit confirmation)
- **Exception:** Minor tasks (<5 min) can be auto-marked if command succeeds with clear success output

### 5. Do NOT Assume Completion

Even if a command runs without errors, wait for user confirmation.

### 6. Update PROGRESS.md Immediately

After each completed step.

### 7. If Errors Occur

Document them in PROGRESS.md and work with user to resolve before proceeding.

### 8. Maintain the Same Format and Detail Level

When updating PROGRESS.md.

## Update PROGRESS.md When

- ✅ Completing any phase or sub-phase
- ⏸️ Discovering blockers or missing prerequisites
- 📝 Changing approach or architecture
- ❌ Encountering errors that delay timeline
- ✅ User explicitly confirms task completion
- 💰 Actual costs differ significantly from estimates

## Proactively Suggest Running Maintenance Tasks When

- **After completing a phase:** "Phase X.Y complete! Should I run `make sync-progress` to verify AWS resources match PROGRESS.md?"
- **After creating/modifying scripts:** "New scripts created. Should I run `make inventory` to update FILE_INVENTORY.md?"
- **After solving a new error:** "This error isn't in TROUBLESHOOTING.md yet. Should I add it? (Then run `make inventory`)"
- **After making architectural decisions:** "Should I create an ADR for this decision? (See docs/adr/template.md)"
- **After creating AWS resources:** "New AWS resources created. Should I run `make check-costs` to see the cost impact?"
- **Monday morning or start of week:** "It's a new week! Should I run `make update-docs` for weekly maintenance?"
- **After 5+ commits:** "Several commits made. Should I run `make backup` to create a backup?"

## Error Handling Protocol

- If a command fails, STOP and report to user immediately
- Do NOT attempt multiple fixes without user guidance
- Check `TROUBLESHOOTING.md` for known solutions first
- If unknown error, log with `log_solution` after resolving
- Update PROGRESS.md with error details and resolution

## Context Awareness

- Check what phase we're in before suggesting commands
- Don't suggest Phase 3 commands if Phase 2 isn't complete
- Verify prerequisites exist before executing dependent tasks
- Use `python scripts/maintenance/sync_progress.py` if unsure of current state

## Your Workflow Should Be

1. Read PROGRESS.md to understand current state
2. **If user requests changes to the plan**: Update PROGRESS.md first, get confirmation, then proceed
3. Execute the next pending task
4. Wait for confirmation (terminal output or user saying "done")
5. Update PROGRESS.md to mark task as ✅ COMPLETE
6. Move to next task
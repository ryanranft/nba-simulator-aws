# Emergency Recovery Procedures

**Last Updated:** October 8, 2025
**Purpose:** Recovery procedures when Claude Code encounters issues mid-session

---

## Quick Reference Card

**When uncertain about state, use this checklist:**

```
Session orientation checklist:
[ ] Read CLAUDE.md ✓
[ ] Read PROGRESS.md ✓
[ ] Read docs/README.md ✓
[ ] Asked user what they completed
[ ] Updated "Current Session Context"
[ ] Asked user what they want to work on
[ ] Read relevant phase file
[ ] Checked for workflow recommendations
[ ] Ready to begin work
```

**Decision points:**
- User wants to work on [task] → Which phase? → Read that phase file
- Phase file says "Follow workflow #X" → Read workflow #X
- Workflow says "Log to COMMAND_LOG.md" → Use Workflow #2
- Task complete → Update PROGRESS.md → Run Workflow #14
- Session ending → Consistency check → Update context → Commit if needed

---

## Emergency Scenarios

### 1. Lost Context / Confused About State

**Symptoms:**
- Don't remember what task we're working on
- Unclear which files have been modified
- Don't know current project state

**Recovery procedure:**

1. **Stop immediately** - Don't make any changes
2. **Re-read PROGRESS.md "Current Session Context"** (just this section, not entire file)
3. **Re-read current phase file** (the one mentioned in Current Session Context)
4. **Check git status:**
   ```bash
   git status
   git diff
   ```
5. **Ask user:** "Where were we? What's the current state?"
6. **Resume from known-good checkpoint** once oriented

---

### 2. Made Changes to Wrong File

**Symptoms:**
- Edited file X when should have edited file Y
- Committed changes to wrong file
- Accidentally modified important file

**Recovery procedure:**

1. **Check git status:**
   ```bash
   git status
   ```

2. **Review changes:**
   ```bash
   git diff <file>
   ```

3. **If changes not committed yet:**
   ```bash
   # Revert single file
   git checkout -- <file>

   # Or revert all unstaged changes
   git checkout -- .
   ```

4. **If already committed (but not pushed):**
   ```bash
   # Revert last commit (keeps changes as unstaged)
   git reset HEAD~1

   # Or hard reset (discards changes entirely)
   git reset --hard HEAD~1
   ```

5. **Apologize to user, explain what happened**

6. **Start over with correct file**

---

### 3. Updated PROGRESS.md Incorrectly

**Symptoms:**
- Marked sub-phase complete when it wasn't
- Status doesn't match actual state
- Dates/times incorrect

**Recovery procedure:**

1. **Check git diff for PROGRESS.md:**
   ```bash
   git diff PROGRESS.md
   ```

2. **Compare against phase file status:**
   - Read current phase file
   - Verify what's actually complete

3. **If mismatch found:**
   ```bash
   # If not committed yet
   git checkout -- PROGRESS.md

   # If committed
   git revert HEAD  # or git reset HEAD~1
   ```

4. **Update PROGRESS.md correctly:**
   - Always update PROGRESS.md **last** (after phase work complete)
   - Match status to actual completion state
   - Only mark ✅ COMPLETE when truly done

5. **Commit with corrected state**

---

### 4. Forgot to Log Commands

**Symptoms:**
- Ran important commands without logging
- COMMAND_LOG.md missing recent work
- Can't recreate what was done

**Recovery procedure:**

1. **Recreate command history from bash history:**
   ```bash
   history | tail -50
   ```

2. **Add to COMMAND_LOG.md retroactively:**
   ```markdown
   ## [Date] [Task] - Commands (Added Retroactively)

   **Note:** These commands were run but not logged in real-time.

   ```bash
   # Command 1
   # Command 2
   ```

   **Results:** [What happened]
   ```

3. **Note that it was added retroactively** (for audit trail)

4. **Set reminder:** Log commands in real-time next time

---

### 5. Context Usage Approaching 90%

**Symptoms:**
- Auto-compact warning appears
- "Context left until auto-compact: 10%"
- Running out of room for work

**Recovery procedure:**

1. **Stop reading files immediately** - No more file reads

2. **Commit current work** if any changes exist:
   ```bash
   git status
   git add .
   # Follow Workflow #3 (Git Commit Protocol)
   ```

3. **Update PROGRESS.md** with current state:
   - Update "Current Session Context"
   - Document what was completed
   - Note what needs to continue next session

4. **End session** - Follow Workflow #14 (Session End)

5. **Start fresh session** - 0% context, continue work from where left off

**Prevention:**
- Commit at 75% context (not 90%)
- Break large tasks into multiple sessions
- Don't read files "just in case"

---

### 6. Workflow Execution Error

**Symptoms:**
- Workflow command fails
- Expected file not found
- Permission denied errors

**Recovery procedure:**

1. **Check TROUBLESHOOTING.md** for this specific error:
   ```bash
   grep -i "error keyword" docs/TROUBLESHOOTING.md
   ```

2. **If found in TROUBLESHOOTING.md:**
   - Follow documented solution
   - Continue workflow

3. **If not found:**
   - Stop workflow execution
   - Ask user for guidance
   - Don't try to guess fix

4. **After resolving:**
   - Consider adding to TROUBLESHOOTING.md (see CLAUDE_OPERATIONAL_GUIDE.md)
   - Resume workflow from step that failed

---

### 7. Multiple File Changes Pending, Unclear State

**Symptoms:**
- Many files modified (`git status` shows 10+ files)
- Don't remember what each change was for
- Unclear commit message to write

**Recovery procedure:**

1. **Review changes file by file:**
   ```bash
   git diff --name-only  # List changed files
   git diff <file>       # Review each file's changes
   ```

2. **Group changes by purpose:**
   - Documentation updates
   - Code changes
   - Configuration changes
   - Test files

3. **Consider committing in stages:**
   ```bash
   # Commit related files together
   git add docs/*.md
   git commit -m "docs: update documentation X"

   git add scripts/file1.py scripts/file2.py
   git commit -m "feat: add feature Y"
   ```

4. **If too complex:**
   - Ask user: "Should I commit these changes in separate commits or all together?"
   - Get clarification on purpose of changes

---

### 8. Pre-commit Hook Blocks Commit

**Symptoms:**
- Security scan finds sensitive data
- Pre-commit hook rejects commit
- Can't complete commit

**Recovery procedure:**

1. **Review flagged lines** (hook will show them)

2. **Explain findings to user:**
   - What was flagged
   - Why it's considered sensitive
   - Potential risk if committed

3. **Options:**

   **Option A: Fix the issue (recommended)**
   ```bash
   # Remove sensitive data from files
   # Commit without sensitive data
   ```

   **Option B: Whitelist if false positive**
   - Ask user: "This appears to be a false positive. Should I add to whitelist?"
   - Get explicit approval before bypassing

   **Option C: User bypass (requires approval)**
   - Ask user: "Security scan flagged these lines. Ready to bypass?"
   - Only proceed with explicit user confirmation

4. **Never bypass without user approval**

---

### 9. Accidental Deletion of Important File

**Symptoms:**
- File missing that should exist
- `rm` command ran on wrong file
- Important data lost

**Recovery procedure:**

1. **Check if file is tracked by git:**
   ```bash
   git log -- <filename>
   ```

2. **If tracked, restore from git:**
   ```bash
   # Restore from last commit
   git checkout HEAD -- <filename>

   # Or restore from specific commit
   git checkout <commit-sha> -- <filename>
   ```

3. **If not in git but in archive:**
   - Check ~/sports-simulator-archives/nba/ for backup
   - Check docs/archive/ for documentation backups

4. **If not recoverable:**
   - Apologize to user
   - Explain what was lost
   - Discuss how to recreate

**Prevention:**
- Always follow Workflow #9 (Archive Management) before deleting files
- Use git mv instead of rm when possible

---

### 10. Session Interrupted / Claude Code Crashed

**Symptoms:**
- Claude Code closed unexpectedly
- Session ended mid-task
- Work not committed

**Recovery procedure (when restarting):**

1. **Check git status** to see uncommitted changes:
   ```bash
   git status
   git diff
   ```

2. **Read PROGRESS.md "Current Session Context"**
   - This should say what was being worked on
   - May not reflect very latest work

3. **Ask user:**
   - "What were you working on when the session ended?"
   - "Were there any uncommitted changes you want to keep?"

4. **Options:**

   **Keep changes:**
   ```bash
   # Review and commit
   git add .
   git commit -m "session recovery: [describe work]"
   ```

   **Discard changes:**
   ```bash
   # Revert all uncommitted work
   git checkout -- .
   ```

5. **Resume from last known-good state**

---

## Prevention Best Practices

### Commit Frequently
- ✅ Commit after each sub-task completion
- ✅ Commit at 75% context (not 90%)
- ✅ Small commits are better than large commits

### Update PROGRESS.md Regularly
- ✅ Update "Current Session Context" when switching tasks
- ✅ Update at session end (Workflow #14)
- ✅ Keep status in sync with actual state

### Log Commands in Real-Time
- ✅ Use `log_command` function (auto-sourced by session_manager.sh)
- ✅ Document commands as you run them
- ✅ Note results and any errors

### Read Files Incrementally
- ✅ Start with docs/README.md to find right file
- ✅ Read only files relevant to current task
- ✅ Don't read entire large files, grep first

### Ask When Uncertain
- ✅ "Should I [action]?" before major changes
- ✅ "Where were we?" if lost context
- ✅ "Is this correct?" when verifying state

---

## Consistency Check Before Session End

**Before running Workflow #14 (Session End), verify:**

- [ ] PROGRESS.md status matches actual completion state
- [ ] Phase file status matches PROGRESS.md
- [ ] "Current Session Context" in PROGRESS.md is updated
- [ ] New workflow references added to phase files if needed
- [ ] COMMAND_LOG.md updated with session commands
- [ ] All files saved and no unsaved changes

**If inconsistencies found:**
1. Update PROGRESS.md first (master index)
2. Then update phase files to match
3. Then commit changes with clear message

---

## Related Documentation

- **CLAUDE.md** - Core instructions and navigation
- **docs/CLAUDE_OPERATIONAL_GUIDE.md** - Session procedures
- **docs/CONTEXT_MANAGEMENT_GUIDE.md** - Context optimization strategies
- **docs/TROUBLESHOOTING.md** - Specific error solutions (grep, don't read fully)
- **Workflow #14** - Session End procedures

---

*For prevention strategies, see docs/CONTEXT_MANAGEMENT_GUIDE.md and CLAUDE.md*

# Workflow #31: QUICKSTART.md Update Protocol

**Category:** Documentation
**Priority:** Medium
**When to Use:** When daily workflows or common commands change
**Related Workflows:** #12 (Documentation Triggers), #5 (Task Execution)

---

## Overview

QUICKSTART.md is the daily reference guide for common commands and workflows. This workflow defines when and how to update it.

**Purpose:** Keep quick reference accurate and useful for daily operations.

---

## What is QUICKSTART.md?

**Target audience:** Developers working on project daily
**Content:** Frequently used commands (>1x per week)
**Not included:** One-time setup, rare operations, experimental commands

**Structure:**
- Environment activation
- Common AWS commands (S3, RDS, Glue)
- Git operations
- Database queries
- Make targets
- Daily workflow steps
- Archive management

---

## When to Update QUICKSTART.md

### ✅ UPDATE When:

#### 1. New Daily Commands Added
```markdown
**Trigger:** Command used >1x per week
**Example:**
- New make target for common operation
- AWS CLI shortcut for frequent task
- Database query template used daily
```

**Frequency check:**
```bash
# If you run a command 5+ times, consider adding it
```

#### 2. File Locations Changed
```markdown
**Trigger:** Files or directories moved/reorganized
**Example:**
- Scripts moved to different directory
- Log files relocated
- Config files restructured
```

**Update:**
- All file paths in examples
- Directory structure references
- Archive locations

#### 3. Workflow Shortcuts Discovered
```markdown
**Trigger:** Found faster way to do common task
**Example:**
- Alias that saves time
- One-liner combining multiple commands
- Make target replacing manual steps
```

**Add:**
- Shortcut command
- Explanation of what it does
- When to use it vs manual approach

#### 4. Common Troubleshooting Steps Identified
```markdown
**Trigger:** Same fix needed multiple times
**Example:**
- Conda environment activation issues
- AWS credentials expiring
- Database connection problems
```

**Add:**
- Quick fix command
- When to use it
- Link to TROUBLESHOOTING.md for details

---

### ❌ DON'T UPDATE When:

#### 1. Rarely-Used Commands
```markdown
**Threshold:** Less than weekly usage
**Reason:** Belongs in detailed docs, not quick reference
**Example:**
- Annual credential rotation
- One-time AWS resource setup
- Infrastructure migration commands
```

**Alternative:** Document in relevant workflow file instead

#### 2. One-Time Setup Steps
```markdown
**Reason:** Belongs in docs/SETUP.md
**Example:**
- Initial Conda environment creation
- First-time AWS configuration
- SSH key generation
```

#### 3. Experimental Commands
```markdown
**Reason:** Not proven/stable yet
**Example:**
- Testing new approach
- Debugging-only commands
- Prototype scripts
```

**Wait:** Until command is proven and used regularly

#### 4. Already Documented Elsewhere
```markdown
**Reason:** Avoid duplication
**Example:**
- Full workflow already in workflow file
- Detailed setup in SETUP.md
- Architecture in README.md
```

**Instead:** Link to detailed docs

---

## QUICKSTART.md Update Workflow

### Step 1: Identify Update Trigger

Ask yourself:
- [ ] Is this command used >1x per week?
- [ ] Would I need this command tomorrow?
- [ ] Is this a shortcut/improvement to existing workflow?
- [ ] Is this a common fix needed repeatedly?

If **YES to any**, proceed with update.

---

### Step 2: Determine Section

**QUICKSTART.md sections:**
```markdown
1. Environment Setup (activation commands)
2. Common AWS Commands (S3, RDS, Glue)
3. Database Operations (connections, queries)
4. Git Operations (commit, push, status)
5. Make Targets (automation commands)
6. Daily Workflow (session start to end)
7. Archive Management (finding past conversations)
8. Troubleshooting Quick Fixes (common issues)
```

**Find appropriate section** for your addition.

---

### Step 3: Write Command Entry

**Standard format:**
```markdown
### [Command Name or Task]

**Purpose:** [One-line description]

**Command:**
```bash
actual_command --with-flags
```

**When to use:**
- [Scenario 1]
- [Scenario 2]

**Example:**
```bash
# Specific example with real values
```

**Notes:**
- [Important details]
- [Common gotchas]
```

---

### Step 4: Add Examples

**Good examples:**
```markdown
# Check S3 bucket contents
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ --human-readable --summarize

# Count files in directory
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ --recursive | wc -l

# Download sample file
aws s3 cp s3://nba-sim-raw-data-lake/box_scores/401584893.json ./sample.json
```

**Include:**
- Real paths (not placeholders)
- Expected output (if helpful)
- Common variations

---

### Step 5: Update Related Sections

**If command replaces old approach:**
```markdown
# Old approach (deprecated)
# aws s3api list-objects --bucket nba-sim-raw-data-lake

# New approach (faster)
aws s3 ls s3://nba-sim-raw-data-lake/ --summarize
```

**If command is part of workflow:**
```markdown
### Daily Workflow

1. Activate environment: `conda activate nba-aws`
2. Check system status: `make status`  # [NEW COMMAND]
3. Review PROGRESS.md
4. Begin work
```

---

### Step 6: Test Commands

**Before committing:**
```bash
# Test each command in QUICKSTART.md update
# Ensure they work as documented

# Run from project root
cd /Users/ryanranft/nba-simulator-aws

# Test command
[your command here]

# Verify output matches documentation
```

**Common issues:**
- Hardcoded paths (use project root)
- Missing prerequisites (note requirements)
- Environment-specific details (generalize)

---

### Step 7: Commit Update

```bash
# Stage changes
git add QUICKSTART.md

# Commit with descriptive message
git commit -m "Update QUICKSTART.md: Add [command name]

Added: [brief description of what was added]

Reason: [why this command is useful daily]

Usage: [when to use this command]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Update Examples

### Example 1: New Make Target

```markdown
**Change:** Added `make check-health` target

**Section:** Make Targets

**Addition:**
```markdown
### Check System Health

**Command:**
```bash
make check-health
```

**What it checks:**
- Conda environment status
- AWS credentials validity
- Database connectivity
- S3 bucket access
- Python package versions

**When to use:**
- Start of each session
- After system updates
- When debugging environment issues
```

**Commit Message:**
```
Update QUICKSTART.md: Add make check-health target

Added: System health check command to Make Targets section

Reason: Combines multiple diagnostic commands into one
        Useful at start of every session

Usage: Run `make check-health` to verify environment
```

---

### Example 2: Workflow Shortcut

```markdown
**Change:** Discovered one-liner for S3 file counting

**Section:** Common AWS Commands

**Addition:**
```markdown
### Count Files in S3 Bucket

**Command:**
```bash
# Count all files in bucket
aws s3 ls s3://nba-sim-raw-data-lake/ --recursive --summarize | grep "Total Objects" | awk '{print $3}'

# Count files in specific directory
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/ --recursive | wc -l
```

**Output:**
```
146115  # Total files in bucket
```

**When to use:**
- Verify S3 sync completed
- Check data extraction progress
- Validate file counts before processing
```

**Commit Message:**
```
Update QUICKSTART.md: Add S3 file counting shortcut

Added: One-liner to count S3 objects quickly

Reason: Previously required multiple commands or AWS Console
        Used 3+ times this week

Usage: Verify file counts during ETL operations
```

---

### Example 3: Common Troubleshooting Fix

```markdown
**Change:** AWS credentials expire daily, need quick reset

**Section:** Troubleshooting Quick Fixes

**Addition:**
```markdown
### Fix Expired AWS Credentials

**Problem:** "ExpiredToken" error when running AWS commands

**Quick Fix:**
```bash
# Re-source credentials
source scripts/shell/load_nba_credentials.sh

# Verify working
aws sts get-caller-identity
```

**When to use:**
- After session longer than 12 hours
- "ExpiredToken" errors appear
- AWS commands suddenly fail

**Permanent fix:** See docs/TROUBLESHOOTING.md for credential rotation
```

**Commit Message:**
```
Update QUICKSTART.md: Add AWS credential reset fix

Added: Quick fix for expired AWS tokens

Reason: Happens daily with temporary credentials
        Common error, simple fix

Usage: Run when AWS commands return ExpiredToken error
```

---

## QUICKSTART.md Quality Checklist

**Before committing:**
- [ ] Command tested and works
- [ ] Real paths used (not placeholders)
- [ ] Appropriate section selected
- [ ] Clear purpose stated
- [ ] "When to use" explained
- [ ] Example output shown (if helpful)
- [ ] Common gotchas noted
- [ ] Links to detailed docs (if applicable)

**After committing:**
- [ ] File inventory updated: `make inventory`
- [ ] Command actually works from project root
- [ ] No sensitive information included

---

## What Belongs in QUICKSTART vs Other Docs

### QUICKSTART.md (Quick Reference)
```markdown
✅ Daily commands (>1x per week)
✅ Common shortcuts
✅ Workflow summaries
✅ Quick troubleshooting
✅ Make targets
```

### docs/SETUP.md (One-Time Setup)
```markdown
❌ Environment creation
❌ AWS account setup
❌ Initial configuration
❌ Installation steps
```

### Workflow Files (Detailed Procedures)
```markdown
❌ Step-by-step workflows
❌ Decision criteria
❌ Security protocols
❌ Complete procedures
```

### TROUBLESHOOTING.md (Detailed Fixes)
```markdown
❌ Root cause analysis
❌ Multiple solution approaches
❌ Debugging procedures
❌ Error categories
```

---

## Maintenance Schedule

### Weekly Review
```bash
# Check if QUICKSTART.md is outdated
# During Monday maintenance (workflow #20)

# Questions to ask:
- Any commands used frequently this week not documented?
- Any paths changed that need updating?
- Any shortcuts discovered?
```

### After Major Changes
```bash
# Update QUICKSTART.md when:
- Reorganizing project structure
- Adding new automation (make targets)
- Changing daily workflow
- Discovering common issues
```

---

## Integration with Other Workflows

**Workflow order:**
1. Discover new command or shortcut
2. Use it 3+ times (establish pattern)
3. **Add to QUICKSTART.md** (this workflow)
4. Update file inventory (workflow #13)
5. Commit changes (workflow #8)

**Cross-references:**
- Link to workflow files for detailed procedures
- Link to TROUBLESHOOTING.md for complete solutions
- Link to SETUP.md for setup-related commands

---

## Advanced: Command Categories

### Category 1: Must-Know (Daily)
```markdown
Commands you'll run every single day:
- conda activate nba-aws
- git status
- make [common-target]
```

### Category 2: Frequently Used (Weekly)
```markdown
Commands you'll run weekly:
- aws s3 sync
- make update-docs
- Database queries
```

### Category 3: Troubleshooting (As Needed)
```markdown
Commands for when things break:
- Credential resets
- Connection fixes
- Environment repairs
```

### Category 4: Convenience (Nice to Have)
```markdown
Shortcuts that save time:
- One-liners
- Aliases
- Automated scripts
```

---

## Example QUICKSTART.md Structure

```markdown
# NBA Simulator AWS - Quick Reference

## Environment Setup
[Daily activation commands]

## Common AWS Commands
### S3 Operations
[Frequent S3 commands]

### RDS Operations
[Frequent database commands]

## Daily Workflow
[Session start to end]

## Make Targets
[Automation commands]

## Troubleshooting Quick Fixes
[Common issues and quick solutions]

## Archive Management
[Finding past conversations]
```

---

## Tips for Effective QUICKSTART Updates

### Tip 1: Real Examples Only
```markdown
# Good - real paths
aws s3 ls s3://nba-sim-raw-data-lake/box_scores/

# Bad - placeholders
aws s3 ls s3://YOUR_BUCKET_NAME/YOUR_DIRECTORY/
```

### Tip 2: Include Expected Output
```markdown
**Output:**
```
2024-01-15 14:30:45  12345 401584893.json
Total Objects: 146115
```
```

### Tip 3: Explain When to Use
```markdown
**When to use:**
- [Specific scenario]
- NOT: "Whenever you need to..." (too vague)
```

### Tip 4: One Command, One Purpose
```markdown
Don't combine unrelated commands in one section
Each entry should be standalone
```

---

## Removing Outdated Commands

**When to remove:**
- Command no longer works
- Better alternative exists
- No longer used (>3 months)
- Project structure changed

**How to remove:**
```markdown
# Option 1: Delete entirely (if truly obsolete)

# Option 2: Mark as deprecated
### [Old Command] (Deprecated)

**Deprecated:** Use `new_command` instead (see below)

**Old approach:**
[old command for reference]
```

**Document removal:**
```bash
git commit -m "Remove outdated command from QUICKSTART.md

Removed: [old command]

Reason: [why it's obsolete]

Replacement: [new command or N/A]
```

---

## Resources

**Related Documentation:**
- `QUICKSTART.md` - The file itself
- Workflow #12 - Documentation triggers
- `docs/SESSION_INITIALIZATION.md` (lines 141-154)
- `docs/SETUP.md` - One-time setup commands

**References:**
```bash
# View current QUICKSTART.md
cat QUICKSTART.md

# Search for command
grep -i "s3" QUICKSTART.md

# Check last update
git log -1 --format="%ai" QUICKSTART.md
```

---

**Last Updated:** 2025-10-02
**Source:** docs/SESSION_INITIALIZATION.md (lines 141-154)
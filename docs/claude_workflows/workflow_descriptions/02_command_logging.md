## 📝 Command Logging Workflow

**Automatically log terminal commands for debugging and documentation**

### Purpose

The `log_command.sh` script provides automatic command logging with categorization, output capture, and helper functions for documentation.

**Loaded automatically by:** `session_manager.sh start` (Session Start Workflow Step 1)

### Step 1: Load Command Logging Functions (AUTOMATIC)

**Already done in Session Start Workflow:**
```bash
source scripts/shell/session_manager.sh start
```

This sources `log_command.sh` automatically, making all logging functions available.

**Verify functions loaded:**
```bash
type log_cmd
# Should output: log_cmd is a function
```

### Step 2: Use Command Logging Functions

**Available functions:**

| Function | Purpose | Example |
|----------|---------|---------|
| `log_cmd` | Log and execute command with output | `log_cmd git status` |
| `log_note` | Add note/comment to log | `log_note "Starting Phase 3 setup"` |
| `log_solution` | Document error solution | `log_solution "Fixed by installing psycopg2-binary"` |

#### Function 1: log_cmd (Execute and Log)

**Syntax:**
```bash
log_cmd <command> [arguments...]
```

**What it does:**
1. Categorizes command by type (GIT, AWS, CONDA, PYTHON, DATABASE, MAKE, BASH)
2. Executes command
3. Captures stdout and stderr
4. Records exit code
5. Appends to COMMAND_LOG.md with timestamp

**Example usage:**
```bash
# Git commands
log_cmd git status
log_cmd git diff HEAD~1

# AWS commands
log_cmd aws s3 ls s3://nba-sim-raw-data-lake/
log_cmd aws rds describe-db-instances

# Database commands
log_cmd psql -h endpoint -U admin -d nba_sim -c "SELECT COUNT(*) FROM games"

# Python scripts
log_cmd python scripts/etl/extract_data.py

# Make targets
log_cmd make inventory
log_cmd make verify-all
```

**Log entry format:**
```markdown
## [2025-10-02 18:30:45] GIT: git status

**Command:**
```bash
git status
```

**Output:**
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

**Exit Code:** 0
**Duration:** 0.12s
```

#### Function 2: log_note (Add Commentary)

**Syntax:**
```bash
log_note "Your note text here"
```

**Use when:**
- Starting new phase of work
- Explaining why running commands
- Adding context for future reference
- Marking significant milestones

**Example usage:**
```bash
log_note "Beginning Phase 3: RDS setup and ETL pipeline"
log_cmd aws rds create-db-instance ...

log_note "Testing connection with sample query"
log_cmd psql -h endpoint -c "SELECT 1"

log_note "Setup complete - moving to data validation"
```

**Log entry format:**
```markdown
## [2025-10-02 18:35:20] NOTE

Beginning Phase 3: RDS setup and ETL pipeline
```

#### Function 3: log_solution (Document Error Fixes)

**Syntax:**
```bash
log_solution "Brief description of error and fix"
```

**Use when:**
- Solved an error that took >5 minutes
- Found non-obvious solution
- Want to document for future reference

**Example usage:**
```bash
log_solution "psycopg2 import error - fixed by installing psycopg2-binary instead"

log_solution "AWS credentials expired - rotated keys in IAM console"

log_solution "Conda environment conflicts - created fresh environment from environment.yml"
```

**Log entry format:**
```markdown
## [2025-10-02 18:40:15] SOLUTION

**Problem:** psycopg2 import error
**Solution:** Fixed by installing psycopg2-binary instead

**Context:**
- Error occurred during: database connection testing
- Resolution time: ~15 minutes
- Related commands: pip install psycopg2-binary
```

### Command Categories

**Auto-categorized by pattern matching:**

| Category | Patterns | Examples |
|----------|----------|----------|
| **GIT** | `git`, `gh` | git status, git commit, gh pr create |
| **AWS** | `aws`, `boto3` | aws s3 ls, aws rds describe-db-instances |
| **CONDA** | `conda`, `mamba` | conda activate, conda install |
| **PYTHON** | `python`, `pip`, `pytest` | python script.py, pip install, pytest tests/ |
| **DATABASE** | `psql`, `pg_dump`, `createdb` | psql -h endpoint, pg_dump nba_sim |
| **MAKE** | `make` | make inventory, make verify-all |
| **BASH** | All others | ls, cd, grep, find |

### Log File Location

**Primary log:** `COMMAND_LOG.md` (project root)

**Archive locations:**
- After commit: `~/sports-simulator-archives/nba/<SHA>/COMMAND_LOG.md`
- Manual backups: `COMMAND_LOG.md.backup` (after sanitization)

### Viewing Logs

**Recent commands:**
```bash
tail -50 COMMAND_LOG.md
```

**Search for specific command:**
```bash
grep -A 10 "aws s3" COMMAND_LOG.md
```

**Search for errors:**
```bash
grep -i "error\|failed" COMMAND_LOG.md
```

**Count commands by category:**
```bash
grep "##.*GIT:" COMMAND_LOG.md | wc -l
grep "##.*AWS:" COMMAND_LOG.md | wc -l
```

### Best Practices

**✅ DO:**
- Use `log_cmd` for all non-trivial commands
- Add `log_note` before starting new phases
- Use `log_solution` for debugging wins
- Review COMMAND_LOG.md before committing
- Keep as permanent debugging/audit trail

**❌ DON'T:**
- Log passwords or secrets directly (sanitization handles this)
- Delete COMMAND_LOG.md (it's archived automatically)
- Log trivial commands (ls, cd, etc.) unless relevant
- Manually edit COMMAND_LOG.md entries (breaks formatting)

### Integration with Other Workflows

**Session Start (Step 1):**
- Functions loaded automatically
- Ready to use immediately

**Git Commit Workflow (Step 0):**
- COMMAND_LOG.md automatically sanitized before commit
- Backup created at COMMAND_LOG.md.backup

**Archive Management (after commit):**
- COMMAND_LOG.md archived to `~/sports-simulator-archives/nba/<SHA>/`
- Preserved for each commit

**Error Handling Workflow (Step 4-5):**
- Use `log_solution` to document fixes
- Helps with TROUBLESHOOTING.md entries

### Troubleshooting

**Functions not available:**
```bash
# Re-source session manager
source scripts/shell/session_manager.sh start
```

**COMMAND_LOG.md missing:**
```bash
# Create empty log
touch COMMAND_LOG.md
echo "# Command Log" > COMMAND_LOG.md
```

**Log too large (>10MB):**
```bash
# Archive current log
mv COMMAND_LOG.md COMMAND_LOG_$(date +%Y%m%d).md
touch COMMAND_LOG.md
```

**Need to find old command:**
```bash
# Search archives
grep -r "command_keyword" ~/sports-simulator-archives/nba/*/COMMAND_LOG.md
```

### Manual Command Logging (Alternative)

**If functions not available, log manually:**

```bash
# Execute command
git status

# Append to log manually
cat >> COMMAND_LOG.md << EOF

## [$(date '+%Y-%m-%d %H:%M:%S')] GIT: git status

**Command:**
\`\`\`bash
git status
\`\`\`

**Output:**
\`\`\`
$(git status 2>&1)
\`\`\`

**Exit Code:** $?

EOF
```

**But prefer using `log_cmd` for consistency**

---


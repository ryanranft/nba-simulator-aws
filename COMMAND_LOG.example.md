# Command Execution Log (Example Template)

**Purpose:** This is an example template showing how to use the command logging system. Your actual COMMAND_LOG.md will contain real command outputs.

---

## ⚠️ SECURITY REMINDER

**Before committing COMMAND_LOG.md to Git:**
- Review for exposed credentials, API keys, passwords, tokens
- Sanitize AWS account IDs if sharing publicly
- Replace sensitive IPs/endpoints with placeholders (e.g., `xxx.xxx.xxx.xxx`)
- Remove or redact any Personal Access Tokens (PATs)
- Check for database passwords or connection strings

---

## How to Use This Log

**Automated Logging (Recommended):**
```bash
# Source the logging function
source scripts/shell/log_command.sh

# Use log_cmd to automatically execute and log
log_cmd git status
log_cmd aws s3 ls s3://nba-sim-raw-data-lake/

# Add notes to the last logged command
log_note This command shows the current branch

# Add solution to the last logged command (for errors)
log_solution Used git remote set-url to fix the issue
```

---

## Log Entry Example

### [GIT] Check Git status
**Time:** 2025-09-30 14:30:00
**Directory:** `/Users/ryanranft/nba-simulator-aws`
**Conda Env:** nba-aws
**Command:** `git status`
**Output:**
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```
**Result:** ✅ SUCCESS
**Exit Code:** 0
**Notes:** Verified working directory is clean before starting new work
**Related:** PROGRESS.md Phase 1

---

### [AWS] List S3 objects
**Time:** 2025-09-30 14:35:00
**Directory:** `/Users/ryanranft/nba-simulator-aws`
**Conda Env:** nba-aws
**Command:** `aws s3 ls s3://nba-sim-raw-data-lake/`
**Output:**
```
                           PRE box_scores/
                           PRE pbp/
                           PRE schedule/
                           PRE team_stats/
```
**Result:** ✅ SUCCESS
**Exit Code:** 0
**Notes:** Verified S3 bucket contains all expected folders
**Related:** PROGRESS.md Phase 1 - S3 Data Lake

---

### [GIT] Push to remote - authentication error
**Time:** 2025-09-30 14:40:00
**Directory:** `/Users/ryanranft/nba-simulator-aws`
**Conda Env:** nba-aws
**Command:** `git push -u origin main`
**Output:**
```
To github.com:username/nba-simulator-aws.git
 ! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to 'github.com:username/nba-simulator-aws.git'
hint: Updates were rejected because the tip of your current branch is behind
hint: its remote counterpart. Integrate the remote changes (e.g.
hint: 'git pull ...') before pushing again.
```
**Result:** ❌ ERROR
**Exit Code:** 1
**Notes:** Remote branch has commits not present locally
**Solution:** Used `git pull origin main --rebase` to rebase local commits on remote, then `git push -u origin main` succeeded
**Related:** PROGRESS.md ADR-005

---

### [AWS] Start Glue Crawler
**Time:** 2025-10-01 10:00:00
**Directory:** `/Users/ryanranft/nba-simulator-aws`
**Conda Env:** nba-aws
**Command:** `aws glue start-crawler --name nba-data-crawler`
**Output:**
```
{
    "Message": "Crawler started"
}
```
**Result:** ✅ SUCCESS
**Exit Code:** 0
**Notes:** First run of crawler to discover JSON schema
**Related:** PROGRESS.md Phase 2.1 - Glue Crawler

---

### [PYTHON] Run ETL script with warnings
**Time:** 2025-10-01 15:30:00
**Directory:** `/Users/ryanranft/nba-simulator-aws`
**Conda Env:** nba-aws
**Command:** `python scripts/etl/test_etl.py`
**Output:**
```
Processing 100 files...
Warning: Missing field 'player_id' in 3 records, skipping
Warning: Invalid date format in 1 record, using default
Successfully processed 96/100 files
Output written to: test_output/
```
**Result:** ⚠️ WARNING
**Exit Code:** 0
**Notes:** Script succeeded but encountered data quality issues in sample files
**Solution:** Added validation logic to handle missing fields gracefully
**Related:** PROGRESS.md Phase 2.2 - Glue ETL Job Development

---

## Status Indicators

- ✅ **SUCCESS** - Command executed successfully (exit code 0)
- ❌ **ERROR** - Command failed (non-zero exit code)
- ⚠️ **WARNING** - Command succeeded but produced warnings
- 🔄 **RETRY** - Command was retried after initial failure
- 🔍 **DEBUG** - Diagnostic/investigation command
- 🚀 **DEPLOY** - Production/critical deployment command

---

## Command Categories

- `[GIT]` - Git/GitHub operations
- `[AWS]` - AWS CLI commands (S3, Glue, RDS, EC2, etc.)
- `[CONDA]` - Conda environment management
- `[PYTHON]` - Python script execution
- `[DATABASE]` - Database operations (psql, SQL queries)
- `[DOCKER]` - Docker operations
- `[NODE]` - Node/npm operations
- `[OTHER]` - Miscellaneous commands

---

## Tips for Using the Command Log

1. **Start each work session** by logging `git status` and `conda list` to document environment state
2. **Log failed commands immediately** - they're the most valuable learning data
3. **Add "Solution" field** after you resolve an error - helps future debugging
4. **Reference PROGRESS.md sections** to connect commands with project phases
5. **Use categories** consistently to make searching easier
6. **Review before committing** - check for secrets/credentials every time
7. **Add context in Notes** - explain why you ran the command, not just what it does

---

## Available Helper Functions

```bash
# Execute and log a command
log_cmd <command>

# Add a note to the last logged command
log_note <your note text>

# Add a solution to the last logged command
log_solution <solution description>
```

---

**This is an example file. Your actual COMMAND_LOG.md will be created when you start using `log_cmd`.**

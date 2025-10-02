# Claude Command Logging & Code Snippet Tracking

This file contains the complete protocol for how Claude logs commands and code changes to COMMAND_LOG.md.

## CRITICAL: Log ALL Code Changes and Outcomes to COMMAND_LOG.md

Command logging serves as a learning database - tracking what works, what fails, and why. This helps avoid repeating mistakes and reference successful solutions.

## When Writing/Editing Code Files

Manually document in COMMAND_LOG.md:
- **What you created/changed:** File path, function/class name, purpose
- **Code snippet:** The actual code written (if short) or summary (if long)
- **Outcome:** Did it work? Any errors? What was learned?

### Format

```markdown
## [Timestamp] Code Change: [Brief Description]
**File:** `path/to/file.py`
**Purpose:** What this code does and why

**Code:**
```python
# Actual code snippet or summary
```

**Outcome:**
- ✅ Success / ❌ Failed
- Error messages (if any)
- What worked / what didn't
- Lessons learned
```

### When to Log

- ✅ New functions/classes created
- ✅ Bug fixes (what was broken, how you fixed it)
- ✅ Refactoring (what changed, why)
- ✅ Failed attempts (what didn't work, why)
- ✅ Performance improvements

### Why This Matters

- Learn from past mistakes (avoid repeating failed approaches)
- Track what patterns work well in this codebase
- Build institutional knowledge of trial and error
- Reference successful solutions for similar problems

## When Executing Terminal Commands

Encourage user to use the command logging system:
- Source the logging script: `source scripts/shell/log_command.sh`
- Execute commands with: `log_cmd <command>`
- Example: `log_cmd aws s3 ls s3://nba-sim-raw-data-lake/`

## Reference COMMAND_LOG.md When Debugging

Learn from past solutions:
- **Before writing new code:** Check if similar code was written before
- **When errors occur:** Search for similar error messages in log
- **When choosing approaches:** Review what worked/failed previously
- Use as a learning database of what works in this project

## Add Solutions to Errors

Use `log_solution <description>` helper function after resolving unknown errors.

## CRITICAL - Before Committing COMMAND_LOG.md to Git

- Always review for sensitive information (credentials, API keys, passwords, tokens)
- Sanitize AWS account IDs if sharing publicly
- Replace sensitive IPs/endpoints with placeholders
- Remove or redact any Personal Access Tokens (PATs)
- Remind user to review before any `git add` or `git commit` that includes COMMAND_LOG.md
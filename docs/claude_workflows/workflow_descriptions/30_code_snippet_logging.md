# Workflow #30: Code Snippet Logging

**Category:** Documentation & Learning
**Priority:** High
**When to Use:** Every time you write, modify, or debug code
**Related Workflows:** #2 (Command Logging), #5 (Task Execution)

---

## Overview

This workflow documents all code changes and their outcomes in COMMAND_LOG.md. Unlike command logging (workflow #2), this focuses on **code snippets, outcomes, and lessons learned**.

**Purpose:** Build institutional knowledge of what works, what fails, and why.

---

## Why Code Snippet Logging Matters

### Benefits

**Learning from mistakes:**
- Track failed attempts and why they didn't work
- Avoid repeating the same bugs
- Understand error patterns

**Building knowledge:**
- Reference successful solutions
- See evolution of approaches
- Track what patterns work in this codebase

**Debugging aid:**
- Search for similar past errors
- Find working examples of similar code
- Understand what was already tried

---

## What to Log

### ✅ ALWAYS Log:

#### 1. New Functions/Classes
```markdown
**What:** Every new function or class you create
**Why:** Documents initial approach and intent
**Include:** Code snippet, purpose, expected behavior
```

#### 2. Bug Fixes
```markdown
**What:** Code changes that fix bugs
**Why:** Documents what was broken and how you fixed it
**Include:** Error message, root cause, solution
```

#### 3. Refactoring
```markdown
**What:** Code restructuring or improvements
**Why:** Documents why old approach was insufficient
**Include:** Before/after code, reason for change
```

#### 4. Failed Attempts
```markdown
**What:** Code that didn't work
**Why:** Most valuable for learning - documents dead ends
**Include:** What you tried, why it failed, what you learned
```

#### 5. Performance Improvements
```markdown
**What:** Optimization changes
**Why:** Documents performance impact
**Include:** Before/after timing, improvement metrics
```

### ❌ DON'T Log:

- Tiny typo fixes (unless they caused significant errors)
- Whitespace changes
- Comment updates only
- Auto-generated code (unless you modified it)

---

## Logging Format

### Standard Template

```markdown
## [Timestamp] Code Change: [Brief Description]

**File:** `path/to/file.py`
**Function/Class:** `function_name()` or `ClassName`
**Purpose:** [What this code does and why you're writing it]

**Code:**
```python
# Actual code snippet or summary if long
def example_function(param: str) -> Dict:
    """Docstring."""
    # Implementation
    pass
```

**Outcome:**
- ✅ Success / ❌ Failed / ⚠️ Partial
- [Error messages if any]
- [What worked / what didn't]
- [Lessons learned]

**Notes:**
[Additional context, references, decisions made]
```

---

## Examples

### Example 1: Successful Function Creation

```markdown
## 2025-10-02 14:30 Code Change: Add player stats extraction

**File:** `scripts/etl/field_mapping.py`
**Function:** `extract_player_stats()`
**Purpose:** Extract player statistics from ESPN API JSON for database loading

**Code:**
```python
def extract_player_stats(raw_data: Dict, season: str = "2023-24") -> Dict[str, int]:
    """Extract player statistics from raw JSON data.

    Args:
        raw_data: Dictionary containing player data from API
        season: NBA season (e.g., "2023-24")

    Returns:
        Dictionary with player_id and statistics
    """
    player_id = raw_data["id"]
    stats = raw_data.get("statistics", {})

    return {
        "player_id": player_id,
        "points": stats.get("points", 0),
        "rebounds": stats.get("rebounds", 0),
        "assists": stats.get("assists", 0)
    }
```

**Outcome:**
- ✅ Success
- Tested with 5 sample JSON files
- All tests passing
- Handles missing fields gracefully with .get() defaults

**Notes:**
- Used .get() instead of direct access to handle missing fields
- Added type hints for clarity
- Defaulting missing stats to 0 (discussed with user)
```

---

### Example 2: Bug Fix

```markdown
## 2025-10-02 15:15 Bug Fix: Handle None values in statistics

**File:** `scripts/etl/field_mapping.py`
**Function:** `extract_player_stats()`
**Problem:** KeyError when statistics field is None instead of missing

**Error:**
```
TypeError: argument of type 'NoneType' is not iterable
File "field_mapping.py", line 15, in extract_player_stats
    stats = raw_data.get("statistics", {})
```

**Root Cause:**
- API returns `"statistics": None` for DNP (Did Not Play) players
- .get() returns None, then .get("points") on None fails

**Solution:**
```python
# Before
stats = raw_data.get("statistics", {})

# After
stats = raw_data.get("statistics") or {}
```

**Outcome:**
- ✅ Fixed
- Tested with DNP player data
- Now handles None, missing, and valid statistics

**Lessons Learned:**
- Always test with edge cases (None vs missing vs empty)
- API can return None for optional fields, not just omit them
```

---

### Example 3: Failed Attempt

```markdown
## 2025-10-02 16:45 Failed Attempt: Async batch processing

**File:** `scripts/etl/batch_processor.py`
**Function:** `async_process_files()`
**Purpose:** Speed up ETL by processing multiple files concurrently

**Code:**
```python
async def async_process_files(file_list: List[str]) -> List[Dict]:
    """Process files concurrently using asyncio."""
    tasks = [process_single_file(f) for f in file_list]
    results = await asyncio.gather(*tasks)
    return results
```

**Outcome:**
- ❌ Failed
- Error: "RuntimeError: Event loop is already running"
- Conflict with Jupyter notebook event loop
- Performance gain only 5% (not worth complexity)

**Lessons Learned:**
- Async in Jupyter is problematic (nested event loops)
- File I/O is already fast on M2 Max with SSD
- Bottleneck is parsing JSON, not file reading
- Simpler solution: multiprocessing.Pool instead

**Next Steps:**
- Try multiprocessing instead of async
- Profile to confirm JSON parsing is bottleneck
```

---

### Example 4: Refactoring

```markdown
## 2025-10-02 17:20 Refactor: Extract validation logic

**File:** `scripts/etl/field_mapping.py`
**Change:** Split `extract_player_stats()` into extract + validate

**Before:**
```python
def extract_player_stats(raw_data: Dict) -> Dict:
    # 50 lines mixing extraction and validation
    pass
```

**After:**
```python
def extract_player_stats(raw_data: Dict) -> Dict:
    """Extract stats from raw data."""
    # 20 lines, focused on extraction
    stats = _parse_statistics(raw_data)
    return stats

def validate_player_stats(stats: Dict) -> bool:
    """Validate extracted stats."""
    # 30 lines, focused on validation
    return _check_required_fields(stats) and _check_data_types(stats)
```

**Reason:**
- Original function doing too much (violates SRP)
- Hard to test validation logic separately
- Easier to understand with separation

**Outcome:**
- ✅ Success
- Tests now clearer (separate test files)
- Validation reusable for other data sources
- Code more maintainable
```

---

## Logging Workflow

### Step 1: Before Writing Code

```markdown
## [Timestamp] Starting: [Task description]

**Goal:** [What you're trying to achieve]
**Approach:** [High-level plan]
```

### Step 2: While Writing Code

Write code normally, but keep notes:
- What you're trying
- Why you made certain decisions
- What errors you encounter

### Step 3: After Code Works (or Fails)

```markdown
## [Timestamp] Code Change: [What you did]

**File:** `path/to/file.py`
**Code:** [snippet or summary]
**Outcome:** ✅/❌/⚠️
**Lessons:** [What you learned]
```

### Step 4: Before Committing

Review COMMAND_LOG.md:
- [ ] All code changes documented
- [ ] Outcomes recorded (success/failure)
- [ ] Error messages included (if any)
- [ ] Lessons learned captured

---

## Integration with COMMAND_LOG.md

### COMMAND_LOG.md Structure

```markdown
# Command Log

## Session: 2025-10-02

### Environment Check
[Terminal commands with outputs]

### Code Changes
[Code snippets with this workflow]

### Solutions to Errors
[Problems and fixes]

### Commands Executed
[AWS CLI, git, make commands]
```

**Code snippets go in "Code Changes" section**

---

## Searching Past Code Changes

### Find Similar Code
```bash
# Search for function implementations
grep -A 20 "def extract_" COMMAND_LOG.md

# Find error patterns
grep -B 5 "KeyError" COMMAND_LOG.md

# Find successful approaches
grep -A 10 "✅ Success" COMMAND_LOG.md
```

### Reference When Debugging

**Before writing new code:**
1. Search COMMAND_LOG.md for similar functions
2. Check what worked in the past
3. Avoid patterns that failed before

**When errors occur:**
1. Search for similar error messages
2. Check how you solved it before
3. Try documented solutions first

---

## What to Include in Code Snippets

### ✅ Include:

- **Function signature** (with type hints)
- **Docstring** (if you wrote one)
- **Key logic** (critical lines)
- **Error handling** (try/except blocks)

### ❌ Don't Include:

- Entire file contents (too long)
- Boilerplate imports (unless relevant)
- Trivial helper functions
- Auto-generated code

### Summary if Code is Long

```markdown
**Code:** (Summary - full implementation in scripts/etl/processor.py:45-120)

Key components:
1. Load JSON from S3 (lines 50-60)
2. Extract fields with error handling (lines 65-85)
3. Validate data types (lines 90-100)
4. Return standardized dict (lines 105-120)
```

---

## Code Snippet Logging Checklist

**When creating new function:**
- [ ] Log function name and purpose
- [ ] Include code snippet or summary
- [ ] Document expected behavior
- [ ] Note any design decisions

**When fixing bug:**
- [ ] Log error message (exact text)
- [ ] Explain root cause
- [ ] Show before/after code
- [ ] Confirm fix works

**When refactoring:**
- [ ] Explain why refactoring was needed
- [ ] Show before/after comparison
- [ ] Document improvements
- [ ] Confirm tests still pass

**When attempt fails:**
- [ ] Document what you tried
- [ ] Explain why it failed
- [ ] Note what you learned
- [ ] Suggest alternatives to try

---

## Before Committing COMMAND_LOG.md

**CRITICAL - Security Check:**

Always review COMMAND_LOG.md for sensitive information:
- [ ] No AWS credentials or keys
- [ ] No passwords or tokens
- [ ] No private IP addresses
- [ ] No sensitive file paths
- [ ] No API keys

Use sanitization script:
```bash
bash scripts/shell/sanitize_command_log.sh
```

See workflow #8 (Git Commit) for complete security protocol.

---

## Tips for Effective Code Logging

### Tip 1: Log in Real-Time
```markdown
Don't wait until end of day - log as you code
- Fresh in memory
- Accurate error messages
- Capture decision-making process
```

### Tip 2: Include Context
```markdown
Not just "Fixed bug"
But: "Fixed KeyError in extract_stats() when API returns None for DNP players"
```

### Tip 3: Be Honest About Failures
```markdown
Failed attempts are MORE valuable than successes
- Shows what doesn't work
- Prevents wasting time on same approach
- Documents project evolution
```

### Tip 4: Use Consistent Format
```markdown
Always include:
- File path
- Function/class name
- Purpose
- Code snippet
- Outcome (✅/❌/⚠️)
- Lessons learned
```

---

## Integration with Other Workflows

**Workflow order:**
1. Write code (follow style guide, workflow #29)
2. Test code (TDD workflow #27)
3. **Log code snippet** (this workflow #30)
4. Update file inventory (workflow #13)
5. Commit changes (workflow #8)

**Cross-references:**
- Link to ADRs if architectural decision
- Reference TROUBLESHOOTING.md for known issues
- Cite STYLE_GUIDE.md for style choices

---

## Advanced: Code Change Categories

### Category 1: Exploration
```markdown
**Type:** Exploration
**Status:** Spike/prototype, may be discarded
```

### Category 2: Production
```markdown
**Type:** Production code
**Status:** Tested, ready for deployment
```

### Category 3: Debugging
```markdown
**Type:** Debugging
**Status:** Temporary code for investigation
```

### Category 4: Performance
```markdown
**Type:** Performance optimization
**Status:** Benchmarked, X% improvement
```

---

## Example COMMAND_LOG.md Entry

```markdown
# Command Log - Session 2025-10-02

## Code Changes

### 14:30 - Add player stats extraction function

**File:** `scripts/etl/field_mapping.py`
**Function:** `extract_player_stats()`
**Purpose:** Extract player statistics from ESPN API JSON for database loading

**Code:**
```python
def extract_player_stats(raw_data: Dict, season: str = "2023-24") -> Dict[str, int]:
    """Extract player statistics from raw JSON data."""
    player_id = raw_data["id"]
    stats = raw_data.get("statistics") or {}

    return {
        "player_id": player_id,
        "points": stats.get("points", 0),
        "rebounds": stats.get("rebounds", 0),
        "assists": stats.get("assists", 0)
    }
```

**Outcome:**
- ✅ Success
- All tests passing (5/5)
- Handles None and missing fields correctly

### 15:15 - Fix None handling bug

**File:** `scripts/etl/field_mapping.py`
**Bug:** TypeError when statistics field is None
**Fix:** Changed `get("statistics", {})` to `get("statistics") or {}`
**Outcome:** ✅ Fixed - tested with DNP players

### 16:45 - Failed async attempt

**File:** `scripts/etl/batch_processor.py`
**Attempted:** Async file processing with asyncio
**Outcome:** ❌ Failed - RuntimeError with Jupyter event loop
**Lesson:** Try multiprocessing instead of async
```

---

## Resources

**Related Documentation:**
- Workflow #2 - Command Logging (terminal commands)
- Workflow #29 - Style Guide (code formatting)
- Workflow #27 - TDD (testing approach)
- `docs/SESSION_INITIALIZATION.md` (lines 267-321)

**Sanitization:**
- `scripts/shell/sanitize_command_log.sh`
- Workflow #8 (Git Commit Security)

---

**Last Updated:** 2025-10-02
**Source:** docs/SESSION_INITIALIZATION.md (lines 267-321)
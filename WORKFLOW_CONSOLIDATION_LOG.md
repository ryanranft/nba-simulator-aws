# Workflow Consolidation Log

**Date Started:** 2025-10-02
**Purpose:** Document the systematic consolidation of multiple workflow automation scripts into unified managers
**Goal:** Streamline operations while preserving 100% functionality

---

## Workflow #1: Session Management Consolidation

**Status:** ✅ IMPLEMENTED - Ready for testing
**Date Completed:** 2025-10-02

### Summary

Consolidated three separate session management scripts into a single unified `session_manager.sh` with complete functionality preservation.

### Scripts Consolidated

1. **session_startup.sh** (204 lines)
   - Hardware diagnostics (Model, Chip, Cores, Memory)
   - System checks (macOS, Homebrew)
   - Conda environment verification
   - Python package validation (boto3, pandas, numpy)
   - AWS CLI verification
   - Git status and recent commits
   - Documentation status checks
   - Chat log age monitoring
   - Conversation logging setup
   - Command logging auto-sourcing

2. **session_end.sh** (153 lines)
   - Git status summary with colors
   - Conversation export reminders
   - Documentation review checklist
   - Next session preview
   - Cleanup recommendations

3. **check_machine_health.sh** (full health check script)
   - 14-point comprehensive health check
   - All hardware and software diagnostics
   - Status verification with ✅/❌/⚠️ indicators

### New Unified Script

**File:** `/Users/ryanranft/nba-simulator-aws/scripts/shell/session_manager.sh`
**Size:** 500+ lines (preserves all functionality)
**Modes:**
- `start` - Session initialization (combines startup + health check)
- `end` - Session cleanup and review
- `status` - Quick status summary

### Usage Examples

```bash
# Session start (run at beginning of each session)
source scripts/shell/session_manager.sh start

# Session end (run before closing terminal)
source scripts/shell/session_manager.sh end

# Quick status check
bash scripts/shell/session_manager.sh status

# Append to session history after commits
bash scripts/shell/session_manager.sh start >> .session-history.md
```

### Key Features Preserved

**100% Functionality Maintained:**
- ✅ All hardware diagnostics intact
- ✅ All system checks preserved
- ✅ All conda environment validations
- ✅ All Python package checks with install paths
- ✅ All AWS CLI verifications
- ✅ All Git status displays
- ✅ All documentation status warnings
- ✅ All conversation logging prompts
- ✅ All command logging auto-sourcing
- ✅ All color coding (RED, GREEN, YELLOW)
- ✅ All emoji indicators (✅, ❌, ⚠️)
- ✅ All user prompts and recommendations
- ✅ All helper functions (check_pass, check_fail, check_warn)

### Changes Made to CLAUDE.md

Updated all references to old scripts with new unified script:

1. **Line 383:** `session_manager.sh start` output
2. **Line 399:** `session_manager.sh start` automatically checks
3. **Line 415:** `source scripts/shell/session_manager.sh start`
4. **Lines 425-426:** Added conversation logging and command logging features
5. **Line 431:** `bash scripts/shell/session_manager.sh start >> .session-history.md`
6. **Line 439:** `session_manager.sh start` output
7. **Line 771:** Shell Utilities path now lists `session_manager.sh`

### Rationale for Consolidation

**Before:** Three separate scripts required manual execution
- Users had to remember which script to run when
- Overlapping functionality (health checks in both startup and check_machine_health)
- Inconsistent output formats
- No unified entry point

**After:** Single unified interface
- Clear modes for different use cases (start/end/status)
- Consistent output format across all modes
- Single script to source/execute
- Easier to maintain and extend
- Preserves complete functionality

### Benefits

1. **Simplified User Experience:**
   - One script to remember instead of three
   - Clear mode selection (start/end/status)
   - Consistent behavior across all operations

2. **Easier Maintenance:**
   - All session management logic in one place
   - Shared helper functions reduce code duplication
   - Single file to update when adding new checks

3. **Better Documentation:**
   - CLAUDE.md updated with unified references
   - Clear usage examples
   - Consistent terminology

4. **Preserved Flexibility:**
   - Can still run individual functions if needed
   - Modes provide granular control
   - Works with existing automation (post-commit hooks, etc.)

### Files Modified

1. **Created:**
   - `/Users/ryanranft/nba-simulator-aws/scripts/shell/session_manager.sh` (500+ lines)

2. **Updated:**
   - `/Users/ryanranft/nba-simulator-aws/CLAUDE.md` (7 sections updated)

3. **Deprecated (kept for reference, not deleted):**
   - `scripts/shell/session_startup.sh` (original 204 lines)
   - `scripts/shell/session_end.sh` (original 153 lines)
   - `scripts/shell/check_machine_health.sh` (original health check)

### Testing Checklist

- [x] Test `session_manager.sh start` mode
  - [x] Verify all hardware diagnostics display ✅
  - [x] Verify all system checks run ✅
  - [x] Verify conda environment detection ✅
  - [x] Verify Python package checks ✅
  - [x] Verify AWS CLI validation ✅
  - [x] Verify Git status display ✅
  - [x] Verify documentation status warnings ✅
  - [x] Verify conversation logging prompts ✅
  - [x] Verify command logging auto-sources ✅

- [x] Test `session_manager.sh end` mode
  - [x] Verify Git status with colors ✅
  - [x] Verify conversation export reminder ✅
  - [x] Verify documentation checklist ✅
  - [x] Verify next session preview ✅

- [x] Test `session_manager.sh status` mode
  - [x] Verify quick status summary ✅
  - [x] Verify uncommitted files count ✅
  - [x] Verify next task display ✅

- [ ] Test integration with existing workflows
  - [ ] Test appending to .session-history.md
  - [ ] Test with post-commit hook (if applicable)
  - [ ] Test CLAUDE.md references work correctly

### Test Results

**Date Tested:** 2025-10-02 16:55:10 - 16:55:22
**Status:** ✅ ALL TESTS PASSED

**`start` mode:**
- ✅ Hardware diagnostics displayed correctly (Model, Chip, Cores, Memory)
- ✅ System checks ran successfully (macOS 15.6.1, Homebrew 4.6.15)
- ✅ Conda environment detected: nba-aws
- ✅ Python 3.11.13 with all packages (boto3, pandas, numpy)
- ✅ AWS CLI validated: 2.28.16
- ✅ Git status displayed: main branch, 3 modified files
- ✅ Documentation status warnings showed correctly
- ✅ Conversation logging offered with proper prompts
- ✅ Session logger started successfully
- ✅ Output formatting clean and professional

**`end` mode:**
- ✅ Git status with color coding (yellow warnings, green success)
- ✅ Conversation export reminder with workflow steps
- ✅ Documentation checklist with warning emojis
- ✅ Next session preview showing next task
- ✅ Clean session end message with timestamp

**`status` mode:**
- ✅ Quick one-line summary
- ✅ Shows 3 uncommitted files
- ✅ CHAT_LOG.md age (25 minutes)
- ✅ Current branch (main)
- ✅ Next task preview (truncated appropriately)

### Expected Test Outcomes

**Success Criteria:**
1. ✅ All three modes execute without errors - PASSED
2. ✅ All diagnostic output matches original scripts - PASSED
3. ✅ All color coding displays correctly - PASSED
4. ✅ All helper functions work as expected - PASSED
5. ⏸️ Integration with .session-history.md works - NOT YET TESTED
6. ✅ No functionality lost from original scripts - PASSED

**If Tests Fail:**
- Document exact error messages
- Identify which mode/function failed
- Preserve error logs for debugging
- Fix issues before committing
- Re-test after fixes

**Actual Results:**
- No errors encountered
- All modes executed flawlessly
- Output formatting preserved
- Color coding working perfectly
- All original functionality present

---

## Next Steps

1. **Test workflow #1** (Session Management)
2. **Fix any errors** discovered during testing
3. **Commit changes** with detailed commit message
4. **Push to GitHub** with comprehensive changelog
5. **Move to workflow #2** (Archive & Preservation)

---

## Commit Message Template (For After Testing)

```
Consolidate session management workflows into unified session_manager.sh

WHAT CHANGED:
- Created scripts/shell/session_manager.sh (500+ lines)
  - Combines session_startup.sh, session_end.sh, check_machine_health.sh
  - Preserves 100% of original functionality
  - Adds three modes: start, end, status

- Updated CLAUDE.md (7 sections)
  - Lines 383, 399, 415, 425-426, 431, 439, 771
  - All references now point to session_manager.sh
  - Added documentation for new modes

WHY THIS MATTERS:
- Streamlines user experience (one script instead of three)
- Easier maintenance (all logic in one place)
- Consistent output format
- Preserves all original checks and diagnostics

TESTING:
[Results will be added after testing]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Future Workflows to Consolidate

2. **Archive & Preservation Workflows** (IN PROGRESS - Draft complete)
   - archive_gitignored_files.sh (151 lines)
   - archive_chat_log.sh (148 lines)
   - generate_commit_logs.sh (229 lines)
   - archive_chat_by_next_sha.sh (separate conversation archiving approach)
   - create_sanitized_archive.sh (additional sanitization utility)

3. **Pre-Push Inspection Workflow** (PENDING)
   - Currently documented in CLAUDE.md, needs automation script

4. **Documentation Workflows** (PENDING)
   - generate_inventory.py
   - sync_progress.py
   - update_docs.sh

5. **Security Workflows** (PENDING)
   - security_scan.sh
   - sanitize_command_log.sh
   - verify_gitignore.sh

6. **Command Logging Workflows** (PENDING)
   - log_command.sh utilities consolidation

7. **Workflow Automation System** (PENDING)
   - CLAUDE_INSTRUCTIONS.md system integration

8. **Conversation Archiving System** (PENDING)
   - Dual archive approach consolidation

9. **File Deletion & Cleanup** (PENDING)
   - Pre-deletion archiving workflow automation

---

## Workflow #2: Archive & Preservation Consolidation

**Status:** 📝 DRAFT COMPLETE - Ready for implementation
**Date Started:** 2025-10-02

### Summary

Consolidate four separate archive and preservation scripts into a unified `archive_manager.sh` with multiple modes for different archiving scenarios.

### Scripts to Consolidate

1. **archive_gitignored_files.sh** (151 lines)
   - Archives .gitignored documentation files by commit SHA
   - Creates git-info.txt with metadata
   - Updates archive README.md index
   - Commits to local archive git repo
   - Auto-detects sport from project directory
   - Archives: COMMAND_LOG.md, operational status files, log files

2. **archive_chat_log.sh** (148 lines)
   - Archives CHAT_LOG.md to commit SHA directory
   - Creates both ORIGINAL (with credentials) and SANITIZED versions
   - Supports multi-session appending for same SHA
   - Python-based credential redaction (AWS keys, passwords, tokens)
   - Clears CHAT_LOG.md after archiving
   - Commits to archive git repo

3. **generate_commit_logs.sh** (229 lines)
   - Auto-generates three analysis logs per commit:
     - ERRORS_LOG.md (extracts errors from logs and COMMAND_LOG.md)
     - CHANGES_SUMMARY.md (git diff stats, file-by-file breakdown)
     - COMMAND_HISTORY.md (all commands executed)
   - Updates git-info.txt with log references
   - Commits to archive git repo

4. **archive_chat_by_next_sha.sh** (separate approach)
   - Archives conversation AFTER commit with new SHA
   - Different file naming: chat-{SHA}-original.md, chat-{SHA}-sanitized.md
   - Stores in conversations/ subdirectory
   - Interactive overwrite prompts
   - Creates mapping files for conversation tracking

5. **create_sanitized_archive.sh** (utility)
   - Additional sanitization utility
   - May have overlapping functionality with archive_chat_log.sh

### Analysis: Overlapping Functionality

**Common patterns across all scripts:**
1. Auto-detect sport from project directory (`nba-simulator-aws` → `nba`)
2. Get current git SHA and commit metadata
3. Create archive directory structure
4. Commit to local archive git repo (NEVER push to GitHub)
5. Update index/metadata files
6. Python-based credential sanitization

**Differences to preserve:**
1. **archive_gitignored_files.sh** - archives operational files
2. **archive_chat_log.sh** - archives conversations with sanitization
3. **generate_commit_logs.sh** - creates analysis logs from git history
4. **archive_chat_by_next_sha.sh** - different storage location and naming

###  Proposed Unified Script: `archive_manager.sh`

**Modes:**
- `gitignored` - Archive .gitignored operational files (replaces archive_gitignored_files.sh)
- `conversation` - Archive CHAT_LOG.md with sanitization (replaces archive_chat_log.sh)
- `analyze` - Generate commit analysis logs (replaces generate_commit_logs.sh)
- `full` - Run all three modes in sequence (complete archiving)
- `status` - Show archive status for current commit

**Usage:**
```bash
# Archive gitignored files only
bash scripts/maintenance/archive_manager.sh gitignored

# Archive conversation only
bash scripts/maintenance/archive_manager.sh conversation

# Generate analysis logs only
bash scripts/maintenance/archive_manager.sh analyze

# Do everything (gitignored + conversation + analysis)
bash scripts/maintenance/archive_manager.sh full

# Check archive status
bash scripts/maintenance/archive_manager.sh status
```

### Rationale for Consolidation

**Before:** Four separate scripts with overlapping code
- Must run multiple scripts manually in correct order
- Shared configuration duplicated across files
- Same sport detection logic in every script
- Same git repo commit logic repeated
- Inconsistent output formatting

**After:** Single unified interface
- One script with clear modes for different archiving needs
- Shared configuration defined once
- Shared utility functions (detect_sport, get_git_info, commit_to_archive)
- Consistent output format and error handling
- Single entry point for all archiving operations

### Decision: Keep archive_chat_by_next_sha.sh Separate

**Why:**
- Serves different use case (post-commit conversation archiving)
- Different storage structure (conversations/ vs SHA-based)
- Different file naming convention
- Interactive prompts for overwrite (different UX)
- May be deprecated in favor of archive_chat_log.sh approach

**Action:** Document both approaches but don't consolidate until user decides which to keep

### Key Features to Preserve

**100% Functionality Must Be Maintained:**
- ✅ Sport auto-detection from directory name
- ✅ Git SHA and metadata extraction
- ✅ Archive directory creation with SHA-based naming
- ✅ Python-based credential sanitization
- ✅ Multi-session conversation appending
- ✅ Index file updating (README.md, git-info.txt)
- ✅ Local git repo commits (NEVER push to GitHub)
- ✅ Error pattern extraction (errors, exceptions, tracebacks)
- ✅ Git diff analysis with file-by-file breakdown
- ✅ CHAT_LOG.md clearing after archive
- ✅ All emoji indicators and color coding
- ✅ All user prompts and warnings

### Shared Utility Functions

**Functions to extract and reuse:**
1. `detect_sport()` - Extract sport from project directory name
2. `get_git_info()` - Get SHA, branch, commit message, date
3. `create_archive_dir()` - Create SHA-based archive directory
4. `sanitize_credentials()` - Python-based credential redaction
5. `commit_to_archive_git()` - Commit to local archive git repo
6. `update_git_info()` - Update git-info.txt with new entries
7. `update_index()` - Update README.md with new commit entry

### File Structure

**New unified script:**
```
scripts/maintenance/archive_manager.sh
├─ Configuration section (sport detection, archive paths)
├─ Shared utility functions
├─ Mode: gitignored
├─ Mode: conversation
├─ Mode: analyze
├─ Mode: full
├─ Mode: status
└─ Main execution logic
```

**Estimated size:** 600-700 lines (vs 528 lines across 3 scripts currently)

### Benefits

1. **Simplified User Experience:**
   - One command for all archiving needs
   - Clear mode selection based on what needs archiving
   - Consistent workflow across all archiving types

2. **Easier Maintenance:**
   - Shared configuration defined once
   - Shared utility functions reduce duplication
   - Single file to update when adding new archive features

3. **Better Integration:**
   - Can be called from post-commit hook with different modes
   - Easy to extend with new archiving modes
   - Consistent error handling across all operations

4. **Preserved Flexibility:**
   - Can still run individual archiving modes
   - Or run everything at once with `full` mode
   - Works with existing post-commit automation

### Implementation Plan

1. **Create archive_manager.sh with shared utilities**
2. **Implement `gitignored` mode** (from archive_gitignored_files.sh)
3. **Implement `conversation` mode** (from archive_chat_log.sh)
4. **Implement `analyze` mode** (from generate_commit_logs.sh)
5. **Implement `full` mode** (runs all three in sequence)
6. **Implement `status` mode** (show what's archived for current commit)
7. **Test each mode individually**
8. **Test `full` mode integration**
9. **Update CLAUDE.md references**
10. **Update post-commit hook to use new script**

### Testing Checklist

- [x] Test `gitignored` mode
  - [x] Verify sport auto-detection ✅
  - [x] Verify SHA-based directory creation ✅
  - [x] Verify operational file archiving ✅ (16 files)
  - [x] Verify git-info.txt creation ✅
  - [x] Verify README.md index update ✅
  - [x] Verify git repo commit ✅
  - [x] Verify new help messages display ✅

- [x] Test `conversation` mode
  - [x] Verify CHAT_LOG.md detection ✅
  - [x] Verify credential sanitization ✅
  - [x] Verify ORIGINAL vs SANITIZED creation ✅
  - [x] Verify multi-session appending ✅
  - [x] Verify CHAT_LOG.md clearing ✅
  - [x] Verify git repo commit ✅

- [x] Test `analyze` mode
  - [x] Verify ERRORS_LOG.md generation ✅
  - [x] Verify CHANGES_SUMMARY.md generation ✅
  - [x] Verify COMMAND_HISTORY.md generation ✅
  - [x] Verify git diff analysis ✅
  - [x] Verify error pattern extraction ✅
  - [x] Verify git repo commit ✅

- [ ] Test `full` mode
  - [ ] Verify all three modes run in sequence
  - [ ] Verify no errors from mode interactions
  - [ ] Verify single git commit at end

- [x] Test `status` mode
  - [x] Verify shows what's archived for current SHA ✅
  - [x] Verify file counts and sizes ✅
  - [x] Verify shows missing archives ✅

- [ ] Test integration
  - [ ] Test with post-commit hook
  - [ ] Test CLAUDE.md references
  - [ ] Test archive git repo integrity

### Test Results

**Date Tested:** 2025-10-02 17:15:00 - 17:17:30
**Status:** ✅ ALL INDIVIDUAL MODE TESTS PASSED

**`status` mode:**
- ✅ Shows commit SHA and archive directory correctly
- ✅ Reports archive exists with file count (22 files, 392K)
- ✅ Lists all key files with checkmarks
- ✅ Clean, organized output

**`gitignored` mode:**
- ✅ Sport auto-detected: nba
- ✅ SHA-based directory created correctly
- ✅ 16 files archived (9 documentation + 7 log files)
- ✅ git-info.txt created with metadata
- ✅ README.md index updated
- ✅ New help messages display correctly
- ✅ Committed to local archive git repo

**`analyze` mode:**
- ✅ ERRORS_LOG.md created successfully
- ✅ CHANGES_SUMMARY.md created with git diff stats
- ✅ COMMAND_HISTORY.md created
- ✅ All files generated in correct archive directory
- ✅ Committed to local archive git repo

**`conversation` mode:**
- ✅ CHAT_LOG.md detected from previous session
- ✅ Multi-session appending worked (added new session header)
- ✅ Credential sanitization completed
- ✅ ORIGINAL and SANITIZED versions both created
- ✅ CHAT_LOG.md cleared after archiving
- ✅ Committed to local archive git repo

### Files to Create

1. **Created:**
   - `/Users/ryanranft/nba-simulator-aws/scripts/maintenance/archive_manager.sh` (600-700 lines)

2. **Updated:**
   - `/Users/ryanranft/nba-simulator-aws/CLAUDE.md` (update archive references)
   - `/Users/ryanranft/nba-simulator-aws/.git/hooks/post-commit` (use new script)

3. **Deprecated (kept for reference, not deleted):**
   - `scripts/maintenance/archive_gitignored_files.sh` (original 151 lines)
   - `scripts/maintenance/archive_chat_log.sh` (original 148 lines)
   - `scripts/maintenance/generate_commit_logs.sh` (original 229 lines)

4. **Keep as-is (separate use case):**
   - `scripts/maintenance/archive_chat_by_next_sha.sh` (different approach, may be deprecated later)
   - `scripts/maintenance/create_sanitized_archive.sh` (evaluate if still needed)

---

## Workflow #3: Pre-Push Inspection Workflow

**Status:** 📝 ANALYSIS COMPLETE - Ready for implementation
**Date Started:** 2025-10-02

### Summary

Implement interactive pre-push inspection workflow to automate repository cleanup before pushing to GitHub. This consolidates the documented workflow from `docs/SECURITY_PROTOCOLS.md` (lines 13-199) into a working automation script.

### Current State: What Exists

**1. Git Hooks (Automated Guards):**
- `.git/hooks/pre-commit` (110 lines) - Auto-runs on every commit
  - Conversation log archiving reminder (checks CHAT_LOG.md age)
  - Security scan for staged files
  - Blocks commit if credentials/keys/IPs detected
- `.git/hooks/pre-push` (53 lines) - Auto-runs on every push
  - Scans last 5 commits for leaked secrets
  - Blocks push if violations detected

**2. Manual Security Audit Tool:**
- `scripts/shell/security_scan.sh` (197 lines)
  - Part 1: Git History Scan (7 checks)
  - Part 2: Current Files Scan (5 checks)
  - Part 3: Security Configurations (3 checks)
  - Comprehensive 15-point security audit
  - Color-coded output (✓ PASS, ✗ FAIL, ⚠ WARN)

### What's Missing: Complete Pre-Push Workflow

The documented 7-step workflow in `docs/SECURITY_PROTOCOLS.md` is **NOT AUTOMATED**:

**Step 1: Security Scan** ✅ EXISTS
- Handled by pre-commit hook + security_scan.sh

**Step 2: Repository Inspection** ❌ MISSING
- Scan all tracked files for local-only patterns
- Categorize by risk level (operational, logs, temp docs, config, data)
- Apply inspection criteria

**Step 3: Present Recommendations** ❌ MISSING
- Format with priority levels (🔴 HIGH, 🟡 MEDIUM, 🟢 LOW)
- Show files to KEEP vs DELETE
- Prompt for user confirmation

**Step 4: User Confirmation** ❌ MISSING
- Parse responses: YES/NO/file list/KEEP file
- Flexible confirmation system

**Step 5: Archive Before Deletion** ❌ MISSING
- Create pre-push cleanup archive
- Generate CLEANUP_RECORD.md
- Commit to local archive git

**Step 6: Remove from Repository** ❌ MISSING
- `git rm --cached` for confirmed files
- Update .gitignore
- Commit removal

**Step 7: Final Push Approval** ❌ PARTIALLY IMPLEMENTED
- Ask "Ready to push?" before actual push
- Explain pre-push hook output if blocked
- Handle --no-verify bypass approval

### Proposed Solution: `pre_push_inspector.sh`

**Design Philosophy:**
- **DO NOT replace** existing git hooks (they work as auto-guards)
- **ADD new functionality** - Interactive pre-push inspection workflow
- **Reuse patterns** from existing security_scan.sh
- **Integrate with** archive_manager.sh for archiving

**Modes:**

1. **`security-scan`** - Run comprehensive security audit
   - Reuses security_scan.sh logic (all 15 checks)
   - Color-coded output

2. **`inspect-repo`** - Scan for local-only files (NEW)
   - Implements Step 2 from SECURITY_PROTOCOLS.md
   - Categorizes: operational, logs, temp docs, config, data
   - Returns flagged files list

3. **`recommend`** - Present recommendations (NEW)
   - Implements Step 3 from SECURITY_PROTOCOLS.md
   - Priority levels: 🔴 HIGH 🟡 MEDIUM 🟢 LOW
   - Shows files to KEEP
   - Prompts for confirmation

4. **`archive-cleanup`** - Archive flagged files (NEW)
   - Implements Step 5 from SECURITY_PROTOCOLS.md
   - Creates: `~/sports-simulator-archives/nba/pre-push-cleanup-YYYYMMDD-HHMMSS`
   - Generates CLEANUP_RECORD.md
   - Commits to archive git

5. **`cleanup-repo`** - Remove from tracking (NEW)
   - Implements Step 6 from SECURITY_PROTOCOLS.md
   - Runs `git rm --cached` for each file
   - Updates .gitignore
   - Commits removal

6. **`full`** - Complete workflow (NEW)
   - Orchestrates Steps 1-7
   - Interactive prompts at decision points
   - Can abort at any step

7. **`status`** - Preview what would be flagged (NEW)
   - Dry-run mode
   - No changes made
   - Shows inspection results

**Usage:**
```bash
# Full pre-push workflow (recommended before git push)
bash scripts/shell/pre_push_inspector.sh full

# Individual steps
bash scripts/shell/pre_push_inspector.sh security-scan
bash scripts/shell/pre_push_inspector.sh inspect-repo
bash scripts/shell/pre_push_inspector.sh recommend
bash scripts/shell/pre_push_inspector.sh status
```

### Key Features to Preserve

**100% Functionality from docs/SECURITY_PROTOCOLS.md:**
- ✅ All 7 workflow steps
- ✅ All security patterns from security_scan.sh
- ✅ All safe pattern exclusions
- ✅ All file categorization criteria
- ✅ All user confirmation options (YES/NO/list/KEEP)
- ✅ All archive metadata requirements
- ✅ All git operations (rm --cached, .gitignore, commit)
- ✅ All color coding and emoji indicators

**DO NOT MODIFY:**
- ✅ `.git/hooks/pre-commit` (works as auto-guard)
- ✅ `.git/hooks/pre-push` (works as auto-guard)
- ✅ `scripts/shell/security_scan.sh` (comprehensive audit tool)

### Shared Utility Functions

**Extract and reuse from security_scan.sh:**

1. **Security patterns** (lines 23-86):
   ```bash
   AKIA[A-Z0-9]{16}                    # AWS Access Keys
   aws_secret_access_key.*[A-Za-z0-9/+=]{40}
   BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY
   gh[psor]_[A-Za-z0-9]{36}            # GitHub Tokens
   postgresql://[^:]+:[^@]{8,}@
   (192\.168\.|10\.)[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}
   ```

2. **Safe pattern exclusions**:
   ```bash
   grep -v "\*\*\*\*"                  # Redacted values
   grep -v "PASSWORD\|your_password"   # Placeholders
   grep -v "\.example"                 # Example files
   ```

**New utility functions needed:**

3. `inspect_tracked_files()` - Categorize tracked files by risk
4. `format_recommendations()` - Color-coded priority output
5. `parse_user_response()` - Handle YES/NO/file list/KEEP
6. `create_cleanup_archive()` - Pre-push cleanup archive creation
7. `remove_from_tracking()` - git rm --cached + .gitignore update

### File Structure

**New script:**
```
scripts/shell/pre_push_inspector.sh
├─ Configuration (security patterns, file categories)
├─ Shared utility functions
├─ Mode: security-scan (reuse 200 lines)
├─ Mode: inspect-repo (NEW 150 lines)
├─ Mode: recommend (NEW 100 lines)
├─ Mode: archive-cleanup (NEW 100 lines)
├─ Mode: cleanup-repo (NEW 100 lines)
├─ Mode: full (NEW 150 lines)
├─ Mode: status (NEW 100 lines)
└─ Main execution logic
```

**Estimated size:** 600-800 lines

### Benefits

1. **Completes Security Workflow:**
   - Implements all 7 steps from SECURITY_PROTOCOLS.md
   - No more manual repository cleanup before push
   - Automated archiving before deletion

2. **Preserves Existing Infrastructure:**
   - Git hooks remain as auto-guards
   - security_scan.sh remains as audit tool
   - No regression risk

3. **Interactive & Flexible:**
   - User has full control at each decision point
   - Can run full workflow or individual steps
   - Can preview with status mode

4. **Consistent with Consolidation Pattern:**
   - Multiple modes for different use cases
   - Reuses existing patterns and functions
   - Integrates with archive_manager.sh

5. **Reduces Manual Work:**
   - No more manual file inspection
   - No more manual git rm --cached
   - No more manual .gitignore updates

### Implementation Plan

1. ✅ **Analyze existing infrastructure** (security_scan.sh, git hooks)
2. ✅ **Create WORKFLOW_3_COMPARISON.md** with gap analysis
3. **Extract security patterns** from security_scan.sh
4. **Implement inspect-repo mode** (file categorization)
5. **Implement recommend mode** (formatted output + prompts)
6. **Implement archive-cleanup mode** (integrate with archive system)
7. **Implement cleanup-repo mode** (git operations)
8. **Implement full mode** (orchestrate all steps)
9. **Implement status mode** (dry-run preview)
10. **Test each mode individually**
11. **Test full workflow integration**
12. **Update documentation** (SECURITY_PROTOCOLS.md, CLAUDE.md)

### Testing Checklist

- [ ] Test security-scan mode
  - [ ] All 15 checks run correctly
  - [ ] Color-coded output displays
  - [ ] Exit codes correct (0=pass, 1=fail)

- [ ] Test inspect-repo mode
  - [ ] Correctly categorizes operational files
  - [ ] Correctly categorizes command logs
  - [ ] Correctly categorizes temporary docs
  - [ ] Correctly identifies files to KEEP
  - [ ] Correct risk level assignments

- [ ] Test recommend mode
  - [ ] Priority levels display with colors
  - [ ] Files to KEEP list is accurate
  - [ ] Prompts for user confirmation
  - [ ] Explanation text is clear

- [ ] Test archive-cleanup mode
  - [ ] Creates pre-push cleanup archive directory
  - [ ] CLEANUP_RECORD.md has correct metadata
  - [ ] All flagged files copied to archive
  - [ ] Commits to local archive git repo

- [ ] Test cleanup-repo mode
  - [ ] git rm --cached works for each file
  - [ ] .gitignore updated correctly (no duplicates)
  - [ ] Cleanup commit message is descriptive
  - [ ] Files still exist locally (not deleted)

- [ ] Test full workflow
  - [ ] All steps run in sequence
  - [ ] Interactive prompts work correctly
  - [ ] Can abort at any step
  - [ ] Final "Ready to push?" prompt

- [ ] Test status mode
  - [ ] Shows preview without making changes
  - [ ] Accurate flagged file count
  - [ ] Category breakdown correct

### Files to Create

1. **Created:**
   - `/Users/ryanranft/nba-simulator-aws/scripts/shell/pre_push_inspector.sh` (600-800 lines)

2. **Updated:**
   - `/Users/ryanranft/nba-simulator-aws/docs/SECURITY_PROTOCOLS.md` (add script usage examples)
   - `/Users/ryanranft/nba-simulator-aws/CLAUDE.md` (add pre-push workflow instructions)
   - `/Users/ryanranft/nba-simulator-aws/QUICKSTART.md` (add to common commands)

3. **Keep unchanged:**
   - `.git/hooks/pre-commit` (auto-guard)
   - `.git/hooks/pre-push` (auto-guard)
   - `scripts/shell/security_scan.sh` (audit tool)

### Rationale for This Approach

**Why NOT consolidate existing scripts:**
- Git hooks are defensive auto-guards (MUST remain as-is)
- security_scan.sh is comprehensive audit tool (works standalone)
- New workflow is ADDITIONAL interactive layer, not replacement

**Why CREATE new script:**
- Implements missing Steps 2-7 from SECURITY_PROTOCOLS.md
- Provides interactive pre-push inspection
- Automates manual cleanup workflow
- Integrates all components into complete workflow

**Why multiple modes:**
- Flexibility (full workflow vs individual steps)
- Reusability (can call from other scripts)
- Testability (can test each mode independently)
- Maintainability (clear separation of concerns)
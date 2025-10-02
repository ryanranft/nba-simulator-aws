# Workflow #3 Comparison: Pre-Push Inspection Workflow

**Date:** 2025-10-02
**Purpose:** Document existing pre-push security infrastructure vs complete workflow requirements from docs/SECURITY_PROTOCOLS.md

---

## Current State: Existing Scripts & Hooks

### 1. Git Hooks (Automated)

#### `.git/hooks/pre-commit` (110 lines)
**Functionality:**
- Conversation log archiving reminder (lines 9-68)
  - Checks CHAT_LOG.md age (warns if >30 minutes)
  - Prompts user to archive before commit
  - Provides skip option
- Security scan (lines 70-110)
  - Checks staged files for sensitive data
  - Filters out safe documentation patterns
  - Blocks commit if credentials/keys/IPs found
  - Auto-run on every `git commit`

#### `.git/hooks/pre-push` (53 lines)
**Functionality:**
- Secondary security scan on last 5 commits
- Checks commit history for leaked secrets
- Similar pattern matching to pre-commit
- Blocks push if secrets detected in recent commits
- Auto-run on every `git push`

### 2. Manual Security Scan Script

#### `scripts/shell/security_scan.sh` (197 lines)
**Functionality:**
- Comprehensive 15-point security audit
- **Part 1: Git History Scan** (lines 17-89)
  - AWS Access Keys (AKIA pattern)
  - AWS Secret Keys (40 char base64)
  - Private SSH/RSA Keys
  - GitHub Personal Access Tokens
  - Passwords in connection strings
  - Private IP addresses
  - Credential backup paths
- **Part 2: Current Files Scan** (lines 92-144)
  - Tracked files - AWS keys
  - Tracked files - Private keys
  - Tracked files - .env files
  - Tracked files - AWS credentials
  - Tracked files - Sensitive patterns
- **Part 3: Security Configurations** (lines 147-175)
  - .gitignore exists and has .env
  - Pre-commit hook exists
  - Pre-push hook exists
- Color-coded output (✓ PASS, ✗ FAIL, ⚠ WARN)
- Exit code 0 (pass) or 1 (fail)

---

## Required State: Complete Pre-Push Workflow (docs/SECURITY_PROTOCOLS.md)

### Complete 7-Step Pre-Push Workflow (lines 13-199)

**Step 1: Security Scan** (existing)
- ✅ Check staged files for credentials/secrets
- ✅ Display any flagged lines to user
- ✅ Get explicit approval before proceeding
- **Current:** Handled by pre-commit hook + security_scan.sh

**Step 2: Repository Inspection for Local-Only Files** (NOT IMPLEMENTED)
- ❌ Scan all tracked files: `git ls-files | grep -E "\.(md|log|txt|json|csv)$"`
- ❌ Flag files by category:
  1. Operational/Status Files (*_STATUS.md, *_PROGRESS.md, *_SUMMARY.md)
  2. Command/Execution Logs (COMMAND_LOG.md, COMMAND_HISTORY.md)
  3. Temporary Documentation (COMMIT_VERIFICATION.md, EXTRACTION_*.md)
  4. Configuration with Sensitive Paths (local absolute paths)
  5. Large Data Files (.csv, .json, .parquet in data directories)
- ❌ Apply inspection criteria (lines 54-72)
- ❌ Present categorized recommendations (lines 73-101)

**Step 3: Present Recommendations to User** (NOT IMPLEMENTED)
- ❌ Format output with priority levels:
  - 🔴 HIGH PRIORITY (contains sensitive/operational data)
  - 🟡 MEDIUM PRIORITY (operational data, no immediate risk)
  - 🟢 LOW PRIORITY (consider for cleanup)
- ❌ List files to KEEP on GitHub
- ❌ Ask for user confirmation

**Step 4: User Confirmation** (NOT IMPLEMENTED)
- ❌ Parse user response:
  - `YES` - Archive and delete all flagged files
  - `NO` - Skip deletion, proceed with push
  - `file1, file3` - Only delete specified files
  - `KEEP file2` - Remove file2 from deletion list

**Step 5: Archive Before Deletion** (NOT IMPLEMENTED)
- ❌ Create pre-push cleanup archive:
  - Archive directory: `~/sports-simulator-archives/nba/pre-push-cleanup-YYYYMMDD-HHMMSS`
  - Copy all confirmed files to archive
  - Create CLEANUP_RECORD.md with metadata
  - Commit to local archive git repo

**Step 6: Remove from Repository** (NOT IMPLEMENTED)
- ❌ `git rm --cached` for each confirmed file
- ❌ Add to .gitignore
- ❌ Commit removal with detailed message

**Step 7: Final Push Approval** (PARTIALLY IMPLEMENTED)
- ✅ Pre-push hook blocks with security violations
- ❌ Ask user "Ready to push to GitHub?" before push
- ❌ Explain flagged lines from hook output
- ❌ Handle --no-verify bypass approval

---

## Gap Analysis: What's Missing

### 🔴 CRITICAL MISSING FUNCTIONALITY

**1. Repository Inspection System** (Step 2)
- No automated scan for local-only files
- No category-based file classification
- No inspection criteria checks
- Must be MANUALLY done by user

**2. User Confirmation & Parsing** (Steps 3-4)
- No formatted recommendation output
- No interactive confirmation system
- No flexible response parsing (YES/NO/file list/KEEP)

**3. Pre-Push Archive Workflow** (Step 5)
- No pre-push cleanup archive creation
- No CLEANUP_RECORD.md generation
- Separate from existing archive system

**4. Repository Cleanup** (Step 6)
- No automated `git rm --cached` for flagged files
- No .gitignore update automation
- No cleanup commit generation

**5. Final Push Approval Flow** (Step 7)
- No "Ready to push?" prompt before actual push
- No pre-push hook output explanation
- No bypass approval workflow

### ✅ EXISTING FUNCTIONALITY (Keep & Reuse)

**1. Security Pattern Detection**
- `security_scan.sh` has comprehensive patterns
- Pre-commit/pre-push hooks have working filters
- Can extract and reuse pattern definitions

**2. Archive System**
- `archive_manager.sh` handles SHA-based archiving
- Can extend with new "pre-push-cleanup" mode

**3. Git Hook Integration**
- Working pre-commit and pre-push hooks
- Can call new unified script from hooks

---

## Proposed Unified Script: `pre_push_inspector.sh`

### Design Philosophy

**DO NOT replace existing hooks** - They work well as auto-guards.
**ADD new functionality** - Interactive pre-push inspection workflow.

### Modes

**1. `security-scan`** - Run comprehensive security audit
- Calls existing `security_scan.sh` logic
- Preserves all 15 checks
- Color-coded output

**2. `inspect-repo`** - Scan for local-only files (NEW)
- Implements Step 2 from SECURITY_PROTOCOLS.md
- Categorizes tracked files
- Applies inspection criteria
- Returns list of flagged files

**3. `recommend`** - Present recommendations (NEW)
- Implements Step 3 from SECURITY_PROTOCOLS.md
- Formats output with priority levels
- Shows files to keep vs delete
- Prompts for user confirmation

**4. `archive-cleanup`** - Archive flagged files (NEW)
- Implements Step 5 from SECURITY_PROTOCOLS.md
- Creates pre-push cleanup archive
- Generates CLEANUP_RECORD.md
- Commits to local archive git

**5. `cleanup-repo`** - Remove from tracking (NEW)
- Implements Step 6 from SECURITY_PROTOCOLS.md
- Runs `git rm --cached` for confirmed files
- Updates .gitignore
- Commits removal

**6. `full`** - Complete workflow (NEW)
- Runs all steps in sequence (1-7)
- Interactive prompts at each decision point
- Comprehensive pre-push inspection

**7. `status`** - Show what would be flagged
- Dry-run mode
- No changes made
- Preview inspection results

### Usage Examples

```bash
# Full pre-push workflow (before running git push)
bash scripts/shell/pre_push_inspector.sh full

# Just security scan
bash scripts/shell/pre_push_inspector.sh security-scan

# Preview what would be flagged
bash scripts/shell/pre_push_inspector.sh status

# Individual steps (advanced)
bash scripts/shell/pre_push_inspector.sh inspect-repo
bash scripts/shell/pre_push_inspector.sh recommend
bash scripts/shell/pre_push_inspector.sh archive-cleanup file1.md file2.log
bash scripts/shell/pre_push_inspector.sh cleanup-repo file1.md file2.log
```

---

## Integration Plan

### 1. Keep Existing Infrastructure

**DO NOT MODIFY:**
- `.git/hooks/pre-commit` - Works as auto-guard
- `.git/hooks/pre-push` - Works as auto-guard
- `scripts/shell/security_scan.sh` - Comprehensive audit tool

**WHY:** These are defensive layers that auto-run. New script is INTERACTIVE layer for deliberate pre-push reviews.

### 2. Create New Script

**CREATE:** `scripts/shell/pre_push_inspector.sh`
- Implements missing Steps 2-7 from SECURITY_PROTOCOLS.md
- Reuses security patterns from security_scan.sh
- Integrates with archive_manager.sh for archiving
- Can be called manually or from automation

### 3. Update Documentation

**UPDATE:**
- `docs/SECURITY_PROTOCOLS.md` - Add script usage examples
- `CLAUDE.md` - Add pre-push workflow instructions
- `QUICKSTART.md` - Add to common commands

---

## Shared Utility Functions (Extract & Reuse)

### From `security_scan.sh`:

**1. Security Patterns** (lines 23-86)
```bash
AKIA[A-Z0-9]{16}                    # AWS Access Keys
aws_secret_access_key.*[A-Za-z0-9/+=]{40}  # AWS Secret Keys
BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY     # Private Keys
gh[psor]_[A-Za-z0-9]{36}            # GitHub Tokens
postgresql://[^:]+:[^@]{8,}@        # Database connection strings
(192\.168\.|10\.)[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}  # Private IPs
```

**2. Safe Pattern Exclusions** (lines 33, 63, 72, 133)
```bash
grep -v "\*\*\*\*"                  # Redacted values
grep -v "PASSWORD\|your_password"   # Placeholders
grep -v "\.example"                 # Example files
```

### From `pre-commit` hook:

**3. Context-Aware Filtering** (lines 74-82)
```bash
grep -v "grep -E"                   # grep command examples
grep -v "❌"                         # Documentation checkmarks
grep -v "What to check for:"        # Documentation headings
grep -v "password_here\|your_password"  # Placeholders
```

### New Functions Needed:

**4. `inspect_tracked_files()`** - Categorize tracked files
**5. `format_recommendations()`** - Color-coded priority output
**6. `parse_user_response()`** - Handle YES/NO/file list/KEEP
**7. `create_cleanup_archive()`** - Pre-push cleanup archive
**8. `remove_from_tracking()`** - git rm --cached + .gitignore

---

## File Structure Comparison

### BEFORE (Current State)
```
.git/hooks/
├── pre-commit (auto-run, security scan)
└── pre-push (auto-run, history scan)

scripts/shell/
└── security_scan.sh (manual comprehensive audit)

# MISSING: Interactive pre-push inspection workflow
# MISSING: Repository cleanup automation
# MISSING: Pre-push archive system
```

### AFTER (Proposed State)
```
.git/hooks/
├── pre-commit (auto-run, security scan) ✅ UNCHANGED
└── pre-push (auto-run, history scan) ✅ UNCHANGED

scripts/shell/
├── security_scan.sh (manual audit) ✅ UNCHANGED
└── pre_push_inspector.sh (NEW - interactive workflow) ⭐ NEW

scripts/maintenance/
└── archive_manager.sh (extend with cleanup mode) 🔧 ENHANCED
```

---

## Estimated Implementation Size

**New unified script:** 600-800 lines
- Mode: security-scan (reuse existing 200 lines)
- Mode: inspect-repo (NEW 150 lines)
- Mode: recommend (NEW 100 lines)
- Mode: archive-cleanup (NEW 100 lines)
- Mode: cleanup-repo (NEW 100 lines)
- Mode: full (NEW 150 lines - orchestrates all)
- Mode: status (NEW 100 lines)
- Shared utilities (50 lines)

---

## Benefits of This Approach

### 1. Preserves Existing Security Layers
- Git hooks remain as auto-guards
- security_scan.sh remains as audit tool
- No regression risk

### 2. Adds Missing Interactive Workflow
- Step-by-step pre-push inspection
- User has full control at each decision point
- Clear recommendations with reasoning

### 3. Automates Manual Cleanup
- No more manual `git rm --cached`
- No more manual .gitignore updates
- Automated archiving before deletion

### 4. Consistent with Consolidation Pattern
- Multiple modes for different use cases
- Reuses existing utility functions
- Integrates with archive_manager.sh

### 5. Flexible Usage
- Can run full workflow or individual steps
- Can preview with status mode
- Can be called from automation or manually

---

## Testing Checklist

- [ ] Test security-scan mode (reuse existing tests)
- [ ] Test inspect-repo mode (NEW)
  - [ ] Correctly categorizes operational files
  - [ ] Correctly categorizes command logs
  - [ ] Correctly categorizes temporary docs
  - [ ] Correctly identifies files to KEEP
- [ ] Test recommend mode (NEW)
  - [ ] Color-coded priority levels display
  - [ ] Files to KEEP list is accurate
  - [ ] Prompts for user confirmation
- [ ] Test archive-cleanup mode (NEW)
  - [ ] Creates pre-push cleanup archive
  - [ ] CLEANUP_RECORD.md has correct metadata
  - [ ] Commits to local archive git
- [ ] Test cleanup-repo mode (NEW)
  - [ ] git rm --cached works for each file
  - [ ] .gitignore updated correctly
  - [ ] Cleanup commit message is descriptive
- [ ] Test full workflow (NEW)
  - [ ] All steps run in sequence
  - [ ] Interactive prompts work
  - [ ] Can abort at any step
- [ ] Test status mode (NEW)
  - [ ] Shows preview without changes
  - [ ] Accurate flagged file count

---

## Summary

### What Exists: ✅
- Git hooks (pre-commit, pre-push) - **197 lines total**
- Security scan script - **197 lines**
- Archive system - **archive_manager.sh**

### What's Missing: ❌
- Repository inspection for local-only files
- Interactive recommendation system
- Pre-push cleanup archive workflow
- Automated repository cleanup (git rm --cached)
- Final push approval flow

### What to Build: ⭐
- **New:** `scripts/shell/pre_push_inspector.sh` (~700 lines)
- **Enhance:** `archive_manager.sh` (add cleanup mode)
- **Update:** Documentation references

### 100% Functionality Coverage: ✅
- All 7 steps from docs/SECURITY_PROTOCOLS.md lines 13-199
- All existing security patterns preserved
- All git hooks remain unchanged
- Complete interactive pre-push workflow
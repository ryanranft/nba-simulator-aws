## 🔍 Automatic Reference Path Validator

**Workflow #44: Reference Path Validator**

**When to use:**
- Before committing file moves, renames, or deletions
- Before pushing to GitHub (automated check)
- After archiving documentation files
- When consolidating multiple files into one
- ANY time you move, rename, or delete files referenced elsewhere
- As part of pre-push inspection (automated)

**Why this exists:**
- Prevents broken documentation links
- Catches stale references to moved/archived files
- Ensures documentation stays synchronized
- Saves debugging time (no more 404s)
- Automates tedious reference checking
- Works for docs, code, and scripts

**Integration points:**
- Manual: Run on-demand when needed
- Pre-push: Automatic check before pushing to GitHub
- Pre-commit: Validate before committing changes
- Post-commit: Auto-fix references after commit

---

## Quick Reference

**Full workflow in order:**
1. Detect changed files in current commit/staging area
2. Categorize changes (moved, deleted, renamed, created)
3. Search project for references to changed files
4. Generate reference update report
5. Update references (manual or automatic)
6. Verify no broken links remain
7. Commit reference updates (if any)

**Quick commands:**
```bash
# Manual validation (before commit)
bash scripts/shell/validate_references.sh

# Validate specific commit
bash scripts/shell/validate_references.sh c363ed5

# Validate and auto-fix (with confirmation)
bash scripts/shell/validate_references.sh --fix

# Dry run (show what would be updated)
bash scripts/shell/validate_references.sh --dry-run
```

---

## Step 1: Detect Changed Files

**Goal:** Identify all files that were moved, renamed, deleted, or created.

### Method 1: Staged Changes (Before Commit)

```bash
# Show staged files (ready to commit)
git diff --cached --name-status

# Output format:
# A    new/file.md              (Added)
# M    existing/file.md         (Modified)
# D    old/file.md              (Deleted)
# R100 old/path.md new/path.md (Renamed)
```

### Method 2: Last Commit (After Commit)

```bash
# Show files changed in last commit
git diff --name-status HEAD~1 HEAD

# Show files changed in specific commit
git diff --name-status <commit-sha>~1 <commit-sha>
```

### Method 3: Uncommitted Changes

```bash
# Show all modified/deleted files (not staged)
git diff --name-status

# Show untracked files
git ls-files --others --exclude-standard
```

### Categorize Changes

**Parse git output to categorize:**
```bash
# Files added (new files)
git diff --cached --name-status | grep '^A' | awk '{print $2}'

# Files deleted
git diff --cached --name-status | grep '^D' | awk '{print $2}'

# Files renamed/moved
git diff --cached --name-status | grep '^R' | awk '{print $2, $3}'

# Files modified (content changed)
git diff --cached --name-status | grep '^M' | awk '{print $2}'
```

---

## Step 2: Search for References

**Goal:** Find all files that reference the changed files.

### Search Strategy

**For documentation files (*.md):**
```bash
# Search for direct file references
grep -r "FILENAME\.md" . \
  --include="*.md" \
  --exclude-dir=".git" \
  --exclude-dir="node_modules" \
  --exclude-dir="__pycache__" \
  -l  # List files with matches only

# Example: Find all references to IMPLEMENTATION_CHECKLIST.md
grep -r "IMPLEMENTATION_CHECKLIST\.md" . --include="*.md" -l
```

**For code files (*.py, *.sh, *.R):**
```bash
# Search Python files
grep -r "FILENAME" . --include="*.py" -l

# Search shell scripts
grep -r "FILENAME" . --include="*.sh" -l

# Search R scripts
grep -r "FILENAME" . --include="*.R" -l
```

### Build Reference Map

**Create a mapping of changed files → referencing files:**
```bash
# For each changed file, find who references it
for file in $(git diff --cached --name-status | grep '^D' | awk '{print $2}'); do
  echo "=== References to $file ==="
  grep -r "$(basename $file)" . --include="*.md" -l
done
```

**Example output:**
```
=== References to IMPLEMENTATION_CHECKLIST.md ===
./PROGRESS.md
./PROJECT_STATUS.md
./docs/NEXT_STEPS_OPTIONS.md
./README_ENHANCEMENTS.md
```

---

## Step 3: Determine Required Updates

**Goal:** Identify what needs to be updated for each reference.

### Update Patterns

**Pattern 1: File Moved to Archive**
```
Old: docs/IMPLEMENTATION_CHECKLIST.md
New: docs/archive/planning/IMPLEMENTATION_CHECKLIST.md

Update all references:
- [Checklist](docs/IMPLEMENTATION_CHECKLIST.md)
  → [Checklist](docs/archive/planning/IMPLEMENTATION_CHECKLIST.md)
```

**Pattern 2: File Consolidated/Deleted**
```
Old: docs/CLAUDE_SESSION.md (deleted)
New: docs/CLAUDE_OPERATIONAL_GUIDE.md (consolidated into)

Update all references:
- See CLAUDE_SESSION.md for details
  → See CLAUDE_OPERATIONAL_GUIDE.md for details
```

**Pattern 3: File Renamed**
```
Old: scrape_nba_api_playbyplay_only.py
New: scrape_nba_api_comprehensive.py

Update all references:
- scripts/etl/scrape_nba_api_playbyplay_only.py
  → scripts/etl/scrape_nba_api_comprehensive.py
```

**Pattern 4: New File Created (No Updates Needed)**
```
New: docs/WORKFLOW_44.md
Action: No updates needed (new file, no existing references)
```

---

## Step 4: Generate Update Report

**Goal:** Show user what will be updated before making changes.

### Report Format

```markdown
# Reference Update Report
**Generated:** 2025-10-08 18:30:00
**Commit:** c363ed5 (or "staged changes")

## Summary
- Files moved: 3
- Files deleted: 2
- Files renamed: 1
- Total references found: 14
- Files requiring updates: 6

## Details

### 1. File Moved: IMPLEMENTATION_CHECKLIST.md
**Old path:** docs/IMPLEMENTATION_CHECKLIST.md
**New path:** docs/archive/planning/IMPLEMENTATION_CHECKLIST.md

**References to update (4 files):**
- PROGRESS.md (2 references)
- PROJECT_STATUS.md (1 reference)
- docs/NEXT_STEPS_OPTIONS.md (1 reference)

### 2. File Deleted: CLAUDE_SESSION.md
**Deleted:** docs/CLAUDE_SESSION.md
**Replacement:** docs/CLAUDE_OPERATIONAL_GUIDE.md

**References to update (2 files):**
- CLAUDE.md (1 reference)
- docs/README.md (1 reference)

## Recommended Actions
1. Review changes above
2. Run with --fix to auto-update references
3. Manually verify critical documentation links
4. Commit reference updates
```

---

## Step 5: Update References

**Goal:** Update all references to point to new paths.

### Manual Update (Safest)

**Use Edit tool for each file:**
```bash
# Example: Update PROGRESS.md
# Old: docs/IMPLEMENTATION_CHECKLIST.md
# New: docs/archive/planning/IMPLEMENTATION_CHECKLIST.md
```

### Semi-Automatic Update (Recommended)

**Use sed with confirmation:**
```bash
# Generate sed commands for review
echo "sed -i '' 's|docs/IMPLEMENTATION_CHECKLIST\.md|docs/archive/planning/IMPLEMENTATION_CHECKLIST.md|g' PROGRESS.md"

# Review command, then execute if correct
sed -i '' 's|docs/IMPLEMENTATION_CHECKLIST\.md|docs/archive/planning/IMPLEMENTATION_CHECKLIST.md|g' PROGRESS.md
```

### Fully Automatic Update (Advanced)

**Script handles all updates:**
```bash
# Auto-update with confirmation prompt
bash scripts/shell/validate_references.sh --fix

# Auto-update without prompts (dangerous)
bash scripts/shell/validate_references.sh --fix --no-confirm
```

---

## Step 6: Verify Updates

**Goal:** Ensure all references are valid and no broken links remain.

### Verification Checks

**1. Check all updated files exist:**
```bash
# For each referenced path, verify file exists
test -f "docs/archive/planning/IMPLEMENTATION_CHECKLIST.md" && echo "✅ Exists" || echo "❌ Missing"
```

**2. Search for old references:**
```bash
# Should return no results if all updated
grep -r "docs/IMPLEMENTATION_CHECKLIST\.md" . --include="*.md"
```

**3. Check for broken Markdown links:**
```bash
# Find all Markdown links
grep -r '\[.*\](.*\.md)' . --include="*.md" -o

# Test each link exists
# (requires custom script)
```

**4. Review git diff:**
```bash
# Show what was changed
git diff

# Verify changes are correct
git diff --word-diff
```

---

## Step 7: Commit Reference Updates

**Goal:** Commit updated references as a separate, clean commit.

### Commit Message Format

**If references updated in same commit:**
```bash
git add .
git commit -m "docs(refs): update references to archived files

- Fix paths to IMPLEMENTATION_CHECKLIST.md → archive/planning/
- Fix paths to QUICK_START_MULTI_SOURCE.md → archive/planning/
- Update PROGRESS.md, PROJECT_STATUS.md, README_ENHANCEMENTS.md

Relates to: Previous commit moving files to archive/"
```

**If references updated in separate commit:**
```bash
git add .
git commit -m "docs(refs): fix broken references from file consolidation

Files updated:
- PROGRESS.md (2 references)
- PROJECT_STATUS.md (1 reference)
- docs/NEXT_STEPS_OPTIONS.md (1 reference)

All references now point to correct archived locations."
```

---

## Automation Options

### Option 1: Manual Workflow (Current)

**When:** Run manually when consolidating/moving files

**Process:**
1. Move/archive files
2. Run `validate_references.sh`
3. Review report
4. Update references manually or with `--fix`
5. Commit updates

**Pros:** Full control, safe
**Cons:** Easy to forget, manual work

---

### Option 2: Pre-Push Integration (Recommended)

**When:** Automatic check before every `git push`

**Implementation:**
```bash
# Add to scripts/shell/pre_push_inspector.sh

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: Validate File References"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

bash scripts/shell/validate_references.sh --check-only

if [ $? -ne 0 ]; then
  echo "❌ FAILED: Broken references detected"
  echo "Run: bash scripts/shell/validate_references.sh --fix"
  exit 1
fi

echo "✅ PASSED: All file references valid"
```

**Pros:** Automatic, catches issues before push
**Cons:** Blocks push if references broken (good thing!)

---

### Option 3: Pre-Commit Hook

**When:** Automatic check before every `git commit`

**Implementation:**
```bash
# .git/hooks/pre-commit

#!/bin/bash

echo "Validating file references..."
bash scripts/shell/validate_references.sh --check-only --staged

if [ $? -ne 0 ]; then
  echo "❌ Broken references detected in staged files"
  echo "Fix references or commit with: git commit --no-verify"
  exit 1
fi

exit 0
```

**Pros:** Catches issues immediately
**Cons:** May slow down commits, can be bypassed with `--no-verify`

---

### Option 4: Post-Commit Hook

**When:** Auto-fix references after commit

**Implementation:**
```bash
# .git/hooks/post-commit

#!/bin/bash

# Check if last commit moved/deleted files
if git diff HEAD~1 HEAD --name-status | grep -E '^(R|D)' > /dev/null; then
  echo "Files moved/deleted in last commit, checking references..."

  bash scripts/shell/validate_references.sh --fix --auto-commit

  if [ $? -eq 0 ]; then
    echo "✅ References auto-updated and committed"
  fi
fi
```

**Pros:** Fully automatic, no manual intervention
**Cons:** Creates extra commits, may update more than intended

---

## Helper Script: validate_references.sh

**Location:** `scripts/shell/validate_references.sh`

### Usage

```bash
# Check staged changes (before commit)
bash scripts/shell/validate_references.sh

# Check specific commit
bash scripts/shell/validate_references.sh c363ed5

# Check and auto-fix with confirmation
bash scripts/shell/validate_references.sh --fix

# Dry run (show what would change)
bash scripts/shell/validate_references.sh --dry-run

# Check only (exit code 0 = good, 1 = broken refs)
bash scripts/shell/validate_references.sh --check-only

# Auto-commit fixes
bash scripts/shell/validate_references.sh --fix --auto-commit
```

### Script Features

**Detection:**
- Automatically detects moved, renamed, deleted files
- Works with staged changes or specific commits
- Supports git mv, git rm, manual moves

**Search:**
- Searches all *.md, *.py, *.sh, *.R files
- Finds direct references, markdown links, imports
- Builds comprehensive reference map

**Reporting:**
- Generates detailed update report
- Shows old → new path mappings
- Lists all files requiring updates

**Updates:**
- Manual mode: Shows sed commands to run
- Semi-automatic: Prompts for each update
- Fully automatic: Updates all references
- Creates backup before updating (`.bak` files)

**Verification:**
- Checks updated paths exist
- Searches for remaining old references
- Validates markdown links
- Shows git diff of changes

---

## Integration with Existing Workflows

### Workflow #43: Documentation Consolidation

**Add to Step 6 (After moving files):**
```markdown
6. Move files (use `git mv` to preserve history)
   - Stage moves: `git add .`

7. **NEW: Validate references before committing**
   bash scripts/shell/validate_references.sh --fix
   - Review reference update report
   - Confirm updates or make manual adjustments
   - Stage reference updates: `git add .`

8. Commit with detailed message
```

### Pre-Push Inspector

**Add as Step 8 in pre_push_inspector.sh:**
```bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 8: Reference Path Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

bash scripts/shell/validate_references.sh --check-only

if [ $? -ne 0 ]; then
  echo "❌ FAILED: Broken documentation references detected"
  echo ""
  echo "Run this to see details:"
  echo "  bash scripts/shell/validate_references.sh"
  echo ""
  echo "Run this to auto-fix:"
  echo "  bash scripts/shell/validate_references.sh --fix"
  echo ""
  exit 1
fi

echo "✅ PASSED: All documentation references valid"
echo ""
```

---

## Common Scenarios

### Scenario 1: Moving Files to Archive

**Example:** Move `IMPLEMENTATION_CHECKLIST.md` to `docs/archive/planning/`

```bash
# 1. Move file
git mv docs/IMPLEMENTATION_CHECKLIST.md docs/archive/planning/IMPLEMENTATION_CHECKLIST.md

# 2. Stage change
git add .

# 3. Validate and fix references
bash scripts/shell/validate_references.sh --fix

# Output:
# Found 4 references to IMPLEMENTATION_CHECKLIST.md:
#   - PROGRESS.md (2 references)
#   - PROJECT_STATUS.md (1 reference)
#   - docs/NEXT_STEPS_OPTIONS.md (1 reference)
#
# Update all references? (y/n): y
#
# ✅ Updated PROGRESS.md
# ✅ Updated PROJECT_STATUS.md
# ✅ Updated docs/NEXT_STEPS_OPTIONS.md

# 4. Review changes
git diff

# 5. Commit
git add .
git commit -m "docs(archive): move IMPLEMENTATION_CHECKLIST to archive/planning/

Also updated 3 files with broken references."
```

---

### Scenario 2: Consolidating Multiple Files

**Example:** Merge `CLAUDE_SESSION.md` and `CLAUDE_CONTEXT.md` into `CLAUDE_OPERATIONAL_GUIDE.md`

```bash
# 1. Create new consolidated file (manually)
# ... merge content ...

# 2. Delete old files
git rm docs/CLAUDE_SESSION.md
git rm docs/CLAUDE_CONTEXT.md

# 3. Add new file
git add docs/CLAUDE_OPERATIONAL_GUIDE.md

# 4. Validate references
bash scripts/shell/validate_references.sh --dry-run

# Output:
# Found 6 references to deleted files:
#   CLAUDE_SESSION.md:
#     - CLAUDE.md (2 references)
#     - docs/README.md (1 reference)
#   CLAUDE_CONTEXT.md:
#     - PROGRESS.md (1 reference)
#     - docs/README.md (2 references)
#
# Recommended replacement: docs/CLAUDE_OPERATIONAL_GUIDE.md
#
# Manual updates needed:
# - CLAUDE.md: Update 2 references
# - docs/README.md: Update 3 references
# - PROGRESS.md: Update 1 reference

# 5. Update references manually (script can't auto-detect consolidated file)
# Use Edit tool for each file

# 6. Commit
git add .
git commit -m "docs(consolidate): merge session/context guides into operational guide

- Merged CLAUDE_SESSION.md + CLAUDE_CONTEXT.md → CLAUDE_OPERATIONAL_GUIDE.md
- Updated 6 references across 3 files"
```

---

### Scenario 3: Renaming a Script

**Example:** Rename `scrape_nba_api_playbyplay_only.py` → `scrape_nba_api_comprehensive.py`

```bash
# 1. Rename file
git mv scripts/etl/scrape_nba_api_playbyplay_only.py \
       scripts/etl/scrape_nba_api_comprehensive.py

# 2. Validate references
bash scripts/shell/validate_references.sh --fix

# Output:
# Found 8 references to scrape_nba_api_playbyplay_only.py:
#   Documentation (*.md): 3 files
#   Shell scripts (*.sh): 2 files
#
# Update all? (y/n): y
#
# ✅ Updated docs/DATA_SOURCES.md
# ✅ Updated docs/data_collection/scrapers/MANAGEMENT.md
# ✅ Updated PROGRESS.md
# ✅ Updated scripts/etl/overnight_nba_api.sh
# ✅ Updated scripts/monitoring/monitor_scrapers.sh

# 3. Commit
git add .
git commit -m "refactor(etl): rename play-by-play scraper to comprehensive

- Renamed scrape_nba_api_playbyplay_only.py → scrape_nba_api_comprehensive.py
- Updated 5 files with script references"
```

---

## Best Practices

### 1. Always Use Git Commands for Moves

**Good:**
```bash
git mv old/path.md new/path.md
```

**Bad:**
```bash
mv old/path.md new/path.md  # Git loses track of rename
```

**Why:** Git tracks renames automatically with `git mv`, making detection easier.

---

### 2. Run Validation Before Committing

**Workflow:**
```bash
# 1. Make changes (move, rename, delete files)
# 2. Stage changes
git add .

# 3. Validate BEFORE committing
bash scripts/shell/validate_references.sh --fix

# 4. Review and commit
git diff
git commit -m "message"
```

---

### 3. Use Descriptive Commit Messages

**Include:**
- What files were moved/renamed/deleted
- How many references were updated
- Which files were updated

**Example:**
```
docs(archive): move 3 planning docs to archive/planning/

Files moved:
- IMPLEMENTATION_CHECKLIST.md
- QUICK_START_MULTI_SOURCE.md
- SESSION_SUMMARY.md

Updated 6 files with broken references:
- PROGRESS.md (3 references)
- PROJECT_STATUS.md (2 references)
- README_ENHANCEMENTS.md (1 reference)
```

---

### 4. Check Before Pushing

**Always run pre-push inspector:**
```bash
bash scripts/shell/pre_push_inspector.sh full
```

**This will:**
- Run security scan
- Validate references (if integrated)
- Check for sensitive data
- Verify file sizes
- Review all changes

---

### 5. Keep Archive Paths Consistent

**Standard archive locations:**
```
docs/archive/
├── scraper_reports/    # Point-in-time scraper status reports
├── session_handoffs/   # Session summary documents
└── planning/           # Historical planning documents
```

**When adding new categories:**
1. Document in `docs/archive/README.md`
2. Update this workflow with new pattern
3. Ensure consistent naming

---

## Troubleshooting

### Issue 1: Script Not Finding References

**Symptom:** Reference validation reports no references, but you know they exist.

**Causes:**
- File extension not included in search (e.g., `.txt`, `.json`)
- File in excluded directory (e.g., `node_modules/`)
- Reference uses different filename format

**Solution:**
```bash
# Expand search to more file types
grep -r "FILENAME" . --include="*.md" --include="*.txt" --include="*.json"

# Search without exclusions
grep -r "FILENAME" . --include="*.md"

# Search for partial filename
grep -r "IMPLEMENT" . --include="*.md"
```

---

### Issue 2: Too Many False Positives

**Symptom:** Script reports references that aren't actually file paths.

**Examples:**
- "implementation checklist" (text mention, not file reference)
- Variable names containing filename

**Solution:**
- Manually review reference report
- Use more specific search patterns:
  ```bash
  # Search for markdown links only
  grep -r '\[.*\](.*FILENAME\.md)' . --include="*.md"

  # Search for exact file paths
  grep -r 'docs/FILENAME\.md' . --include="*.md"
  ```

---

### Issue 3: Automatic Updates Break Formatting

**Symptom:** sed command breaks markdown formatting.

**Causes:**
- Special characters in path not escaped
- sed delimiter conflicts with path characters

**Solution:**
```bash
# Use different sed delimiter
sed -i '' 's|old/path|new/path|g'  # Use | instead of /

# Escape special characters
sed -i '' 's/old\/path/new\/path/g'  # Escape /

# Use perl for complex replacements
perl -i -pe 's|old/path|new/path|g' file.md
```

---

### Issue 4: Git Doesn't Detect Renames

**Symptom:** `git diff` shows delete + add instead of rename.

**Causes:**
- File content changed significantly
- Used `mv` instead of `git mv`
- Staged changes incorrectly

**Solution:**
```bash
# Always use git mv
git mv old.md new.md

# If already moved with mv, tell git it's a rename
git add -A  # Stages deletes and adds, git auto-detects renames

# Verify git detected rename
git diff --cached --name-status | grep '^R'
```

---

## Performance Considerations

### For Large Repositories

**Problem:** Searching thousands of files is slow.

**Optimizations:**
1. **Limit search scope:**
   ```bash
   # Search only docs/ directory
   grep -r "FILENAME" docs/ --include="*.md"
   ```

2. **Use parallel search:**
   ```bash
   # Search multiple patterns in parallel
   find . -name "*.md" -exec grep -l "FILENAME" {} +
   ```

3. **Cache file list:**
   ```bash
   # Generate file list once
   find . -name "*.md" > /tmp/md_files.txt

   # Search cached list
   cat /tmp/md_files.txt | xargs grep -l "FILENAME"
   ```

4. **Skip generated directories:**
   ```bash
   --exclude-dir=".git" \
   --exclude-dir="node_modules" \
   --exclude-dir="__pycache__" \
   --exclude-dir="venv" \
   --exclude-dir=".venv"
   ```

---

## Related Workflows

- **Workflow #43:** Documentation Consolidation - Moving and archiving files
- **Workflow #9:** Archive Protocols - File deletion and preservation
- **Workflow #12:** Security Protocols - Pre-push inspection
- **Workflow #2:** Command Logging - Track validation commands

---

## Quick Checklist

**Before moving/archiving files:**
- [ ] Identify all files to be moved
- [ ] Run `validate_references.sh --dry-run`
- [ ] Review reference report
- [ ] Plan reference updates

**After moving files:**
- [ ] Stage file moves: `git add .`
- [ ] Run `validate_references.sh --fix`
- [ ] Confirm automatic updates or update manually
- [ ] Stage reference updates: `git add .`
- [ ] Review all changes: `git diff --cached`
- [ ] Commit with descriptive message
- [ ] Run pre-push inspector
- [ ] Push to GitHub

**Integration (one-time setup):**
- [ ] Create `scripts/shell/validate_references.sh`
- [ ] Add to `pre_push_inspector.sh` (recommended)
- [ ] Optional: Set up pre-commit hook
- [ ] Optional: Set up post-commit hook
- [ ] Test on sample file move

---

**Last updated:** 2025-10-08
**Related files:**
- `scripts/shell/validate_references.sh` (helper script)
- `scripts/shell/pre_push_inspector.sh` (integration point)
- `docs/archive/README.md` (archive structure)

## 📚 Documentation Consolidation & Path Update Workflow

**Workflow #43: Documentation Consolidation**

**When to use:**
- Consolidating multiple documentation files into one
- Moving files to archive/ or other directories
- Reorganizing documentation structure
- Deleting deprecated files after consolidation
- ANY time you move or rename documentation files

**Why this exists:**
- Prevents broken documentation links
- Ensures all references point to correct paths
- Saves 30-60 minutes per consolidation task
- Provides systematic approach to file reorganization

---

## Quick Reference

**Full workflow in order:**
1. Plan consolidation (identify files to merge/move/delete)
2. Search for all references to files being moved
3. Create new consolidated file (if consolidating)
4. Move files (use `git mv` to preserve history)
5. Update all references in documentation
6. Verify no broken links remain
7. Delete old files (use `git rm` if consolidating)
8. Commit with detailed message
9. Document changes in CHANGELOG.md

---

## Step 1: Plan Consolidation

**Before moving/consolidating ANY files, answer these questions:**

1. **What files are being consolidated/moved?**
   - List all files involved
   - Note their current paths
   - Note their destination paths

2. **Why is this consolidation happening?**
   - Reducing duplication?
   - Organizing by topic?
   - Archiving historical documents?
   - Moving to better location?

3. **What is the expected outcome?**
   - Single consolidated file?
   - Organized archive structure?
   - Cleaner top-level docs/?

**Document your plan:**
```markdown
## Consolidation Plan

**Goal:** [What you're trying to achieve]

**Files to consolidate:**
- File 1: /path/to/file1.md → /new/path/file1.md (MOVED)
- File 2: /path/to/file2.md → DELETED (content merged into X.md)
- File 3: /path/to/file3.md → /new/path/consolidated.md (MERGED)

**Expected impact:**
- Reduction in file count: X → Y
- Reduction in duplication: Z% less
- Better organization: [Explain]
```

---

## Step 2: Search for All References

**CRITICAL: Find ALL references before making changes**

### Method 1: Grep for Each File (Recommended)

**For files being moved:**
```bash
# Search for references to file being moved
grep -r "FILENAME\.md" /Users/ryanranft/nba-simulator-aws/ \
  --include="*.md" \
  --exclude-dir=".git" \
  --exclude-dir="node_modules" \
  | tee references_to_update.txt
```

**Example:**
```bash
# Find all references to IMPLEMENTATION_CHECKLIST.md
grep -r "IMPLEMENTATION_CHECKLIST\.md" . --include="*.md" --exclude-dir=".git"
```

### Method 2: Batch Search for Multiple Files

```bash
# Search for multiple files at once
grep -rE "(FILE1\.md|FILE2\.md|FILE3\.md)" . --include="*.md" --exclude-dir=".git"
```

### Method 3: Search for Directory Paths

```bash
# Find references to old directory path
grep -r "docs/OLD_PATH/" . --include="*.md" --exclude-dir=".git"
```

**Document findings:**
```markdown
## References Found

**FILENAME.md referenced in:**
- FILE_A.md (line 45, 67, 123)
- FILE_B.md (line 12)
- FILE_C.md (line 234)

**Total references to update:** X files, Y total references
```

---

## Step 3: Create New Consolidated File (If Consolidating)

**Skip this step if you're just moving files**

### For File Consolidation:

1. **Create new file with combined content:**
   ```bash
   # Template for consolidated file header
   cat > docs/NEW_CONSOLIDATED_FILE.md <<'EOF'
   # Consolidated Documentation Title

   **Last Updated:** YYYY-MM-DD
   **Purpose:** [What this consolidates]

   This file consolidates guidance from:
   - OLD_FILE_1.md (topic 1)
   - OLD_FILE_2.md (topic 2)
   - OLD_FILE_3.md (topic 3)

   ---

   ## Table of Contents

   1. [Section from File 1](#section-1)
   2. [Section from File 2](#section-2)
   3. [Section from File 3](#section-3)

   ---

   [Insert consolidated content here]
   EOF
   ```

2. **Merge content from old files:**
   - Copy relevant sections
   - Remove duplication
   - Reorganize for clarity
   - Add cross-references

3. **Add "See X.md" references to old files (before deletion):**
   - Update old files to point to new location
   - This provides grace period for transition

---

## Step 4: Move Files (Use git mv)

**IMPORTANT: Always use `git mv` to preserve git history**

### For Simple Moves:

```bash
# Move single file
git mv docs/OLD_FILE.md docs/archive/planning/OLD_FILE.md

# Move multiple files to same destination
git mv docs/FILE1.md docs/FILE2.md docs/FILE3.md docs/archive/planning/
```

### For Directory Moves:

```bash
# Create destination directory if needed
mkdir -p docs/archive/scraper_reports

# Move files to archive
git mv docs/SCRAPER_STATUS.md docs/archive/scraper_reports/
git mv docs/SCRAPER_TEST_RESULTS.md docs/archive/scraper_reports/
```

### For Archiving Planning Docs:

```bash
# Standard archive structure
mkdir -p docs/archive/planning
mkdir -p docs/archive/scraper_reports
mkdir -p docs/archive/session_handoffs

# Move files to appropriate archive category
git mv docs/IMPLEMENTATION_CHECKLIST.md docs/archive/planning/
git mv docs/QUICK_START_GUIDE.md docs/archive/planning/
```

**Verify moves:**
```bash
git status
# Should show:
#   renamed: docs/OLD.md -> docs/archive/NEW.md
```

---

## Step 5: Update All References

**Now fix all broken links you found in Step 2**

### Method 1: Manual Edit (Safest for Critical Files)

**Use Edit tool for important files:**
- CLAUDE.md
- PROGRESS.md
- README.md
- Workflow files

**Example:**
```
Old: docs/IMPLEMENTATION_CHECKLIST.md
New: docs/archive/planning/IMPLEMENTATION_CHECKLIST.md
```

### Method 2: Sed Batch Update (Faster for Many Files)

**For consistent path updates across many files:**

```bash
# Update single path across all markdown files
sed -i '' 's|docs/OLD_FILE\.md|docs/archive/planning/OLD_FILE.md|g' FILE.md

# Update across multiple specific files
for file in PROGRESS.md CHANGELOG.md PROJECT_STATUS.md; do
  sed -i '' 's|docs/OLD_FILE\.md|docs/archive/planning/OLD_FILE.md|g' "$file"
  echo "✅ Updated $file"
done
```

**Important sed notes:**
- macOS requires `sed -i ''` (empty string after -i)
- Linux uses `sed -i` (no empty string)
- Always escape dots: `\.md` not `.md`
- Use `|` delimiter to avoid escaping slashes in paths

### Method 3: Verification After Updates

**After updating, verify no broken links:**

```bash
# Search for old paths (should return nothing)
grep -r "docs/OLD_FILE\.md" . --include="*.md" --exclude-dir=".git"

# If empty output: ✅ All references updated
# If finds matches: ❌ Still have broken links
```

---

## Step 6: Verify No Broken Links

**Run comprehensive link check:**

```bash
# Check for references to files you moved/deleted
echo "Checking for broken references..."

# For each file moved, verify old path doesn't exist in docs
for file in "IMPLEMENTATION_CHECKLIST.md" "QUICK_START_MULTI_SOURCE.md"; do
  count=$(grep -r "docs/$file" . --include="*.md" --exclude-dir=".git" | wc -l)
  if [ $count -eq 0 ]; then
    echo "✅ No broken references to $file"
  else
    echo "❌ Found $count references to old path $file"
    grep -rn "docs/$file" . --include="*.md" --exclude-dir=".git"
  fi
done
```

**Verify new paths are correct:**

```bash
# For each moved file, check new path exists
for file in docs/archive/planning/*.md; do
  if [ -f "$file" ]; then
    echo "✅ File exists: $file"
  else
    echo "❌ File missing: $file"
  fi
done
```

---

## Step 7: Delete Old Files (If Consolidating)

**ONLY do this if you consolidated content into a new file**

### Option A: Delete After Consolidation

```bash
# Use git rm (preserves history)
git rm docs/OLD_FILE_1.md
git rm docs/OLD_FILE_2.md
git rm docs/OLD_FILE_3.md
```

### Option B: Move to Archive Instead of Delete

**Safer option: archive rather than delete**

```bash
# Move to archive instead of deleting
mkdir -p docs/archive/deprecated
git mv docs/OLD_FILE.md docs/archive/deprecated/

# Add deprecation notice to archived file (prepend to file)
cat > temp.md <<'EOF'
> **⚠️ DEPRECATED - This file has been consolidated**
>
> **Deprecated on:** YYYY-MM-DD
> **Reason:** Content merged into docs/NEW_CONSOLIDATED_FILE.md
> **See instead:** [NEW_CONSOLIDATED_FILE.md](../../NEW_CONSOLIDATED_FILE.md)

---

EOF

cat docs/archive/deprecated/OLD_FILE.md >> temp.md
mv temp.md docs/archive/deprecated/OLD_FILE.md
```

---

## Step 8: Commit with Detailed Message

**Template for consolidation commits:**

```bash
git add .
git commit -m "docs(consolidation): [brief description]

[DETAILED DESCRIPTION]

Files consolidated/moved:
- OLD_FILE_1.md → NEW_LOCATION/FILE_1.md (moved)
- OLD_FILE_2.md → DELETED (merged into CONSOLIDATED.md)
- OLD_FILE_3.md → NEW_LOCATION/FILE_3.md (moved)

References updated:
- FILE_A.md (3 references)
- FILE_B.md (1 reference)
- FILE_C.md (2 references)

Impact:
- File count reduced: X → Y (-Z%)
- Documentation organization improved
- All links verified working

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Example real commit:**

```bash
git commit -m "docs(refs): fix archived file paths and add consolidation workflow

Updated 7 files with broken references to archived files:
- PROGRESS.md (5 references fixed)
- CHANGELOG.md (1 reference fixed)
- PROJECT_STATUS.md (3 references fixed)
- README_ENHANCEMENTS.md (2 references fixed)
- ENHANCEMENT_ROADMAP.md (1 reference fixed)
- NEXT_STEPS_OPTIONS.md (1 reference fixed)
- Workflow 40 (1 reference fixed)

Path updates:
- docs/IMPLEMENTATION_CHECKLIST.md → docs/archive/planning/IMPLEMENTATION_CHECKLIST.md
- docs/QUICK_START_MULTI_SOURCE.md → docs/archive/planning/QUICK_START_MULTI_SOURCE.md
- docs/SCRAPER_TEST_RESULTS.md → docs/archive/scraper_reports/SCRAPER_TEST_RESULTS.md

Created Workflow #43: Documentation Consolidation
- Systematic process for future consolidations
- Prevents broken links
- Includes verification steps

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Step 9: Document in CHANGELOG.md

**Add entry to CHANGELOG.md:**

```markdown
## [Unreleased]

### Changed - Documentation Consolidation

**Date:** YYYY-MM-DD

**Changes:**
1. **File consolidation:**
   - Consolidated X files into Y
   - Moved Z files to archive
   - Deleted N deprecated files

2. **Path updates:**
   - Updated references in M files
   - Total references fixed: P

3. **New structure:**
   - docs/archive/planning/ - Planning documents
   - docs/archive/scraper_reports/ - Historical scraper status
   - docs/archive/session_handoffs/ - Old session notes

**Benefits:**
- ✅ Cleaner docs/ directory (X files → Y files)
- ✅ Better organization by topic
- ✅ No broken documentation links
- ✅ Easier navigation for new users

**Files modified:** [list files]
**Files created:** [list new files]
**Files deleted/archived:** [list old files]
```

---

## Common Consolidation Patterns

### Pattern 1: Archive Historical Documents

**When:** Session handoffs, scraper reports, planning docs from previous phases

**Structure:**
```
docs/archive/
├── planning/              # Phase planning documents
│   ├── IMPLEMENTATION_CHECKLIST.md
│   └── QUICK_START_MULTI_SOURCE.md
├── scraper_reports/       # Point-in-time scraper status
│   ├── SCRAPER_STATUS_REPORT.md
│   └── SCRAPER_TEST_RESULTS.md
└── session_handoffs/      # Historical session notes
    ├── SESSION_HANDOFF_20251006.md
    └── SESSION_SUMMARY_2025_10_06.md
```

### Pattern 2: Consolidate Multiple Files into One

**When:** 4+ files covering same topic, lots of duplication

**Example: CLAUDE_*.md consolidation**
```
Before:
- CLAUDE_SESSION_INIT.md (162 lines)
- CLAUDE_PROGRESS_TRACKING.md (87 lines)
- CLAUDE_COMMAND_LOGGING.md (74 lines)
- CLAUDE_DOCUMENTATION_QUICK_REF.md (83 lines)
Total: 406 lines across 4 files

After:
- docs/CLAUDE_OPERATIONAL_GUIDE.md (200 lines)
Total: 200 lines (51% reduction)
```

### Pattern 3: Split Large File into Focused Files

**When:** One file > 800 lines covering multiple topics

**Example: PROGRESS.md → Phase index system**
```
Before:
- PROGRESS.md (9,533 lines) - everything in one file

After (October 2025):
- PROGRESS.md (391 lines) - master index only
- docs/phases/PHASE_0_INDEX.md (150 lines) - phase overview + sub-phase table
- docs/phases/phase_0/0.0_initial_data_collection.md (300 lines)
- docs/phases/phase_0/0.1_basketball_reference/ (13-tier structure)
- docs/phases/PHASE_1_INDEX.md through PHASE_7_INDEX.md
- [etc.]

Result: 96% context savings (read only what's needed, 4-level hierarchy)
```

---

## Troubleshooting

### Issue: sed command fails with "invalid command code"

**Cause:** macOS vs Linux sed syntax difference

**Solution:**
```bash
# macOS (requires empty string after -i)
sed -i '' 's|old|new|g' file.md

# Linux (no empty string)
sed -i 's|old|new|g' file.md
```

### Issue: Still finding broken references after update

**Cause:** Missed some files or incomplete pattern match

**Solution:**
```bash
# Search again with more specific pattern
grep -rn "docs/OLD_FILE" . --include="*.md" --exclude-dir=".git"

# Check for partial path matches
grep -rn "OLD_FILE\.md" . --include="*.md" --exclude-dir=".git"

# Look for references without path
grep -rn "\[.*\](OLD_FILE\.md)" . --include="*.md" --exclude-dir=".git"
```

### Issue: git mv says "destination exists"

**Cause:** File already exists at destination

**Solution:**
```bash
# Check if file exists
ls -la docs/archive/planning/FILE.md

# If it's identical, just remove old one
git rm docs/FILE.md

# If different, rename with suffix
git mv docs/FILE.md docs/archive/planning/FILE_OLD.md
```

### Issue: Lost git history after consolidation

**Cause:** Used `mv` instead of `git mv`, or deleted before moving

**Prevention:**
```bash
# ALWAYS use git mv for moves
git mv OLD.md NEW.md

# NEVER use:
mv OLD.md NEW.md  # ❌ Loses history
rm OLD.md         # ❌ Loses history
```

**Recovery (if you haven't committed yet):**
```bash
# Reset changes
git reset --hard HEAD

# Start over with git mv
git mv OLD.md NEW.md
```

---

## Checklist for This Workflow

**Before starting:**
- [ ] Created consolidation plan
- [ ] Searched for all references to files being moved
- [ ] Documented expected impact (file count reduction, etc.)

**During consolidation:**
- [ ] Created new consolidated file (if consolidating)
- [ ] Used `git mv` for all file moves (NOT regular `mv`)
- [ ] Updated all references found in Step 2
- [ ] Verified no broken links remain

**After consolidation:**
- [ ] Deleted old files with `git rm` (if consolidating)
- [ ] Committed with detailed message
- [ ] Updated CHANGELOG.md
- [ ] All tests pass (if applicable)
- [ ] Documentation builds without warnings (if applicable)

---

## Integration with Other Workflows

**Before consolidation:**
- Workflow #9 (Archive Management) - Archive files before moving
- Workflow #19 (Backup & Recovery) - Backup before large changes

**During consolidation:**
- This workflow (#43)

**After consolidation:**
- Workflow #8 (Git Commit) - Commit changes
- Workflow #12 (Documentation Triggers) - Update file inventory
- Workflow #13 (File Inventory) - Run `make inventory`

---

## Success Criteria

**Consolidation is successful when:**
- ✅ All files moved to intended locations
- ✅ Git history preserved (used `git mv`)
- ✅ Zero broken links (grep confirms)
- ✅ All references point to correct new paths
- ✅ CHANGELOG.md updated
- ✅ Commit message documents all changes
- ✅ File count reduced (or better organized)

---

## Related Documentation

- **Workflow #9:** Archive Management - Archiving before deletion
- **Workflow #12:** Documentation Triggers - When to update docs
- **Workflow #36:** Pre-Push Repository Cleanup - Large-scale cleanup
- **docs/ARCHIVE_PROTOCOLS.md:** Archive system policies

---

*Created: October 8, 2025*
*Purpose: Prevent broken links during documentation reorganization*
*Last used: October 8, 2025 - Fixed 14 broken references across 7 files*

# ADR-010 Migration Guide

**Purpose:** Guide for contributors with branches created before October 2025 ADR-010 implementation
**Created:** October 26, 2025
**ADR Reference:** [ADR-010](../adr/010-four-digit-subphase-numbering.md)

---

## Overview

As of October 26, 2025, the project uses **4-digit zero-padded sub-phase numbering** (ADR-010). If you have a feature branch created before this date, follow this guide to update your branch.

**Format change:**
- **Old:** `N.M_name` (variable-length: 0.1, 0.10, 0.11, etc.)
- **New:** `N.MMMM_name` (4-digit: 0.0001, 0.0010, 0.0011, etc.)

---

## Who Needs This Guide?

**You need to migrate if:**
- ✅ Your branch was created before October 26, 2025
- ✅ Your branch adds/modifies phase directories or documentation
- ✅ Your branch references phase numbers in file paths or documentation
- ✅ Your branch has merge conflicts with main on PHASE_N_INDEX.md files

**You DON'T need this if:**
- ❌ Your branch only modifies scripts, tests, or non-phase code
- ❌ Your branch was created after October 26, 2025
- ❌ Your changes don't involve phase organization or documentation

---

## Quick Migration (3 Steps)

### Step 1: Merge Latest Main

```bash
# Save your work
git add .
git commit -m "WIP: Save changes before ADR-010 merge"

# Fetch latest
git fetch origin

# Merge main into your branch
git checkout your-feature-branch
git merge origin/main

# If merge conflicts occur, see "Handling Merge Conflicts" section below
```

### Step 2: Update Your Changes

**If you added new phase directories:**

```bash
# Example: You created 0.18_my_feature
# Rename to 4-digit format
mv docs/phases/phase_0/0.18_my_feature docs/phases/phase_0/0.0018_my_feature

# Update test files
mv tests/phases/phase_0/test_0_18_my_feature.py tests/phases/phase_0/test_0_0018_my_feature.py

# Update validator files
mv validators/phases/phase_0/validate_0_18_my_feature.py validators/phases/phase_0/validate_0_0018_my_feature.py
```

**If you modified phase indexes:**

```bash
# Your PHASE_N_INDEX.md likely has conflicts
# Accept incoming (main branch) version for the structure
# Then manually re-add your specific sub-phase row using 4-digit format
```

**If you referenced phases in documentation:**

```bash
# Find all old-format references in your changes
git diff main --name-only | xargs grep -n "0\.[0-9]\{1,2\}_"

# Update each reference to 4-digit format
# Example: Phase 0.18 → Phase 0.0018
```

### Step 3: Validate Compliance

```bash
# Run ADR-010 validation
bash scripts/maintenance/validate_phase_numbering.sh

# Should output:
# ✅ ALL CHECKS PASSING

# If validation fails, fix the reported issues and re-run
```

---

## Common Scenarios

### Scenario A: Added New Sub-Phase

**Example:** You added Phase 0.18 (old format)

**What to do:**

1. **Rename directory:**
   ```bash
   git mv docs/phases/phase_0/0.18_my_feature docs/phases/phase_0/0.0018_my_feature
   ```

2. **Rename tests:**
   ```bash
   git mv tests/phases/phase_0/test_0_18.py tests/phases/phase_0/test_0_0018.py
   ```

3. **Rename validators:**
   ```bash
   git mv validators/phases/phase_0/validate_0_18.py validators/phases/phase_0/validate_0_0018.py
   ```

4. **Update phase index:**
   - Edit `docs/phases/PHASE_0_INDEX.md`
   - Change `| 0.18 |` to `| 0.0018 |`
   - Update file link: `[0.18_...](...)` → `[0.0018_...](...)`

5. **Update references in your files:**
   ```bash
   # Find all references to your old sub-phase number
   grep -r "0\.18" docs/phases/phase_0/0.0018_my_feature/

   # Replace each with 0.0018
   ```

6. **Validate:**
   ```bash
   bash scripts/maintenance/validate_phase_numbering.sh
   ```

### Scenario B: Modified Existing Sub-Phase

**Example:** You modified Phase 0.1 documentation (now 0.0001)

**What to do:**

1. **Check current directory name:**
   ```bash
   ls docs/phases/phase_0/ | grep 0001
   # Should show: 0.0001_basketball_reference
   ```

2. **Update your documentation references:**
   - If your changes reference "Phase 0.1", change to "Phase 0.0001"
   - If your changes link to `0.1_name`, change to `0.0001_name`

3. **No directory renaming needed** - main branch already renamed it

### Scenario C: Added Tests for Existing Phase

**Example:** You added tests for Phase 0.1 (now 0.0001)

**What to do:**

1. **Rename your test file:**
   ```bash
   # Old name (what you created)
   tests/phases/phase_0/test_0_1_new_test.py

   # New name (4-digit format)
   git mv tests/phases/phase_0/test_0_1_new_test.py \
         tests/phases/phase_0/test_0_0001_new_test.py
   ```

2. **Update imports if referencing phase number:**
   ```python
   # Update any imports or references from 0_1 to 0_0001
   ```

3. **Validate:**
   ```bash
   pytest tests/phases/phase_0/test_0_0001_new_test.py -v
   ```

### Scenario D: Documentation Only Changes

**Example:** You updated README.md or other docs mentioning phases

**What to do:**

1. **Find old references:**
   ```bash
   # Search your modified files for old format
   git diff main --name-only | xargs grep -n "Phase 0\.[0-9]\{1,2\}\>"
   git diff main --name-only | xargs grep -n "phase_0/0\.[0-9]\{1,2\}_"
   ```

2. **Update each reference:**
   - `Phase 0.1` → `Phase 0.0001`
   - `phase_0/0.10_name` → `phase_0/0.0010_name`
   - `0.2_description` → `0.0002_description`

3. **Validate:**
   ```bash
   # Check your files manually
   cat your-modified-file.md
   ```

---

## Handling Merge Conflicts

### Conflict in PHASE_N_INDEX.md

**Common cause:** You and main both modified the phase index

**Resolution:**

1. **Accept incoming (main branch) version:**
   ```bash
   git checkout --theirs docs/phases/PHASE_0_INDEX.md
   ```

2. **Review what you changed:**
   ```bash
   git show HEAD~1:docs/phases/PHASE_0_INDEX.md > /tmp/your_version.md
   cat /tmp/your_version.md
   ```

3. **Manually re-add your changes using 4-digit format:**
   - Open `docs/phases/PHASE_0_INDEX.md`
   - Add your sub-phase row with 4-digit numbering
   - Update status, links as needed

4. **Commit resolution:**
   ```bash
   git add docs/phases/PHASE_0_INDEX.md
   git commit -m "Merge conflict resolved: Updated phase index to ADR-010 format"
   ```

### Conflict in Sub-Phase Directory Name

**Common cause:** You created 0.18 but main now expects 0.0018

**Resolution:**

1. **Delete conflict markers:**
   ```bash
   # Conflicts show as:
   # <<<<<<< HEAD (your branch)
   # 0.18_my_feature
   # =======
   # 0.0018_other_feature
   # >>>>>>> main
   ```

2. **Keep your feature, use 4-digit format:**
   ```bash
   # Rename to 4-digit
   mv docs/phases/phase_0/0.18_my_feature docs/phases/phase_0/0.0018_my_feature
   ```

3. **Resolve conflict:**
   ```bash
   git add docs/phases/phase_0/
   git commit -m "Resolved conflict: Renamed to ADR-010 4-digit format"
   ```

---

## Validation Commands

### Full Validation Suite

```bash
# 1. Validate phase numbering format
bash scripts/maintenance/validate_phase_numbering.sh

# 2. Run pre-commit hooks
pre-commit run validate-phase-numbering --all-files

# 3. Test your changes
pytest tests/ -v

# 4. Validate phase (if applicable)
python scripts/automation/validate_phase.py 0  # Replace 0 with your phase number
```

### Quick Checks

```bash
# Check for old format in your changes
git diff main | grep -E "0\.[0-9]{1,2}_"

# List phase directories (should all be 4-digit)
ls docs/phases/phase_0/ | grep -E "^0\.[0-9]+"

# Verify test file names
ls tests/phases/phase_0/ | grep "test_0_"
```

---

## Pre-Commit Hook Behavior

The pre-commit hook will **automatically block** commits with old format:

**Example error:**
```
❌ ERROR: Old phase numbering format detected (ADR-010 violation)

File: docs/phases/phase_0/0.18_my_feature/README.md
Issue: Directory name uses old format (0.18 instead of 0.0018)

Action: Rename directory to 4-digit format before committing
```

**To fix:**
1. Rename the flagged directory/file
2. Update references
3. Re-run commit

---

## Getting Help

### If Validation Fails

```bash
# View detailed error output
bash scripts/maintenance/validate_phase_numbering.sh 2>&1 | less

# Check specific directory
ls -la docs/phases/phase_0/0.*
```

### If Merge Conflicts Persist

1. **Create backup branch:**
   ```bash
   git branch backup-before-adr-010-merge
   ```

2. **Start fresh merge:**
   ```bash
   git merge --abort  # Abort current merge
   git fetch origin
   git merge origin/main
   ```

3. **Resolve one conflict at a time**

### If Tests Fail After Migration

```bash
# Check if test files were renamed correctly
ls tests/phases/phase_N/ | grep -E "test_[0-9]_[0-9]+"

# Should show 4-digit format: test_0_0001.py, test_0_0010.py

# Run specific test to see error
pytest tests/phases/phase_0/test_0_XXXX.py -v
```

---

## Examples

### Example 1: Feature Branch with New Sub-Phase

**Before (your branch):**
```
docs/phases/phase_0/0.18_api_integration/
tests/phases/phase_0/test_0_18_api.py
```

**Migration commands:**
```bash
# Merge main
git merge origin/main

# Rename directories
git mv docs/phases/phase_0/0.18_api_integration docs/phases/phase_0/0.0018_api_integration
git mv tests/phases/phase_0/test_0_18_api.py tests/phases/phase_0/test_0_0018_api.py

# Update phase index
# Edit docs/phases/PHASE_0_INDEX.md
# Change: | 0.18 | API Integration | ... |
# To:     | 0.0018 | API Integration | ... |

# Validate
bash scripts/maintenance/validate_phase_numbering.sh

# Commit
git add .
git commit -m "refactor: Migrate to ADR-010 4-digit format"
```

**After (migrated):**
```
docs/phases/phase_0/0.0018_api_integration/
tests/phases/phase_0/test_0_0018_api.py
```

### Example 2: Documentation Update with Phase References

**Before (your changes):**
```markdown
See Phase 0.1 for data collection details.
Implementation in `phase_0/0.10_postgresql/`.
```

**Migration:**
```bash
# Find references
grep -n "Phase 0\.[0-9]" docs/my-doc.md
grep -n "phase_0/0\.[0-9]" docs/my-doc.md

# Update manually:
# Phase 0.1 → Phase 0.0001
# phase_0/0.10_postgresql → phase_0/0.0010_postgresql
```

**After (migrated):**
```markdown
See Phase 0.0001 for data collection details.
Implementation in `phase_0/0.0010_postgresql/`.
```

---

## Checklist

Before marking migration complete:

- [ ] Merged latest main into feature branch
- [ ] Resolved all merge conflicts
- [ ] Renamed all phase directories to 4-digit format
- [ ] Renamed all test files to 4-digit format
- [ ] Renamed all validator files to 4-digit format
- [ ] Updated PHASE_N_INDEX.md entries to 4-digit format
- [ ] Updated all documentation references to 4-digit format
- [ ] Ran `validate_phase_numbering.sh` - all checks passing
- [ ] Ran pre-commit hooks - validation passing
- [ ] Ran tests - all passing
- [ ] Committed migration changes with clear message

---

## FAQs

**Q: Do I need to migrate if my branch doesn't touch phase files?**

A: No, if you're only modifying scripts, configuration, or non-phase code, no migration needed.

**Q: What if I want to create a NEW sub-phase after migration?**

A: Always use 4-digit format: `0.0023_my_new_feature`, not `0.23_my_new_feature`. The pre-commit hook will enforce this.

**Q: Can I use the old format temporarily and migrate later?**

A: No, the pre-commit hook will block commits with old format. You must use 4-digit format going forward.

**Q: What happens to git history after renaming?**

A: Git tracks renames, so `git log --follow` will show full history across the rename.

**Q: Do I need to update imports in Python code?**

A: Only if your Python code references phase numbers as strings or paths. Most code shouldn't need changes.

**Q: What if I have multiple feature branches?**

A: Migrate each branch individually following this guide. Start with branches closest to merging first.

---

## Additional Resources

- **ADR-010:** [docs/adr/010-four-digit-subphase-numbering.md](../adr/010-four-digit-subphase-numbering.md)
- **CONTRIBUTING.md:** [CONTRIBUTING.md](../../CONTRIBUTING.md)
- **Validation script:** `scripts/maintenance/validate_phase_numbering.sh`
- **Pre-commit config:** `.pre-commit-config.yaml`
- **Templates:** `docs/templates/`

---

**Questions?** Open an issue on GitHub with label `adr-010-migration`

**Last Updated:** October 26, 2025

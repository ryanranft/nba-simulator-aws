# Workflow #55: Phase Reorganization & Renaming

**Version:** 1.0
**Created:** October 23, 2025
**Purpose:** Systematic process for reorganizing phase structures and updating references
**Trigger:** When renaming sub-phases, restructuring phase directories, or consolidating documentation
**Frequency:** As needed during project evolution
**Related Workflows:** #09 (Archive Management), #53 (Test/Validator Organization), #52 (Phase Index Management)

---

## Overview

This workflow provides a systematic process for reorganizing phase structures, renaming sub-phases, and ensuring all cross-references remain valid. It was created during the Phase 0 complete reorganization (October 23, 2025) when PHASE_0_INDEX.md was rewritten to match actual directory structure.

**Key Principle:** When you rename or reorganize ANY file/directory, you MUST find and update ALL references to it.

---

## When to Use This Workflow

Use this workflow when:
1. **Renaming sub-phases** (e.g., `0.1_old_name` → `0.1_new_name`)
2. **Restructuring phase directories** (e.g., moving files between sub-phases)
3. **Consolidating duplicate phase indexes** (e.g., removing `/docs/phases/PHASE_X_INDEX.md` duplicates)
4. **Archiving superseded implementations** (e.g., MongoDB → PostgreSQL transitions)
5. **Migrating tests/validators** to new directory structure
6. **Updating phase numbering** (e.g., when sub-phases are added/removed)

---

## Step-by-Step Process

### Step 1: Identify the Change Scope

**Before making any changes:**

```bash
# Find all references to the old name/path
grep -r "old_phase_name" docs/ --include="*.md"
grep -r "old/path/to/file" docs/ --include="*.md"

# Count affected files
grep -r "old_phase_name" docs/ --include="*.md" | wc -l
```

**Document:**
- What is being renamed/reorganized
- How many files will be affected
- Expected impact on navigation

---

### Step 2: Update Phase Index

**For phase-level changes:**

1. **Read current phase index** (e.g., `docs/phases/phase_0/PHASE_0_INDEX.md`)
2. **Verify actual directory structure:**
   ```bash
   ls -1 docs/phases/phase_0/ | grep "^0\." | sort -V
   ```
3. **Rewrite phase index** with correct sub-phase names and statuses
4. **Remove duplicate indexes** if they exist:
   ```bash
   # Check for duplicates
   find docs/phases/ -name "PHASE_*_INDEX.md" -maxdepth 1

   # Remove duplicates (keep only phase_X/PHASE_X_INDEX.md)
   rm docs/phases/PHASE_X_INDEX.md
   ```

**Phase Index Must Include:**
- ✅ Correct sub-phase names matching actual directories
- ✅ Current status for each sub-phase (✅ COMPLETE, ⏸️ PENDING, 🔵 PLANNED)
- ✅ Completion dates where applicable
- ✅ Brief descriptions
- ✅ Navigation links (parent, previous, next)
- ✅ Cost summaries if relevant
- ✅ Related documentation links

---

### Step 3: Find All References

**Use multiple search methods:**

```bash
# Method 1: Find files referencing old path
find docs/ -type f -name "*.md" -exec grep -l "old_phase_name" {} \;

# Method 2: Find with context (see surrounding lines)
grep -r "old_phase_name" docs/ --include="*.md" -n -C 2

# Method 3: Count references per file
grep -r "old_phase_name" docs/ --include="*.md" -c | grep -v ":0$"
```

**Create checklist of files to update:**
```
[ ] docs/README.md
[ ] docs/phases/phase_X/sub_phase/README.md
[ ] docs/claude_workflows/workflow_descriptions/*.md
[ ] Related documentation files
```

---

### Step 4: Update Cross-References

**Two approaches:**

#### Approach A: Manual (safer for complex changes)
1. Read each file
2. Use Edit tool to update references
3. Verify change is correct
4. Move to next file

#### Approach B: Batch (faster for simple path changes)
```bash
# Find-and-replace across multiple files
for file in $(find docs/ -type f -name "*.md" -exec grep -l "old_path" {} \;); do
    echo "Updating: $file"
    sed -i '' 's|old_path|new_path|g' "$file"
done
```

**Always verify batch changes:**
```bash
git diff docs/
```

---

### Step 5: Update Sub-Phase Headers

**If renaming sub-phases, update sub-phase README headers:**

Example: Renaming `0.8` → `0.11`

**OLD:**
```markdown
# 0.8: RAG Pipeline with pgvector

**Sub-Phase:** 0.8 (RAG Infrastructure)
**Parent Phase:** [Phase 0: Data Collection](../../PHASE_0_INDEX.md)
```

**NEW:**
```markdown
# 0.11: RAG Pipeline with pgvector

**Sub-Phase:** 0.11 (RAG Infrastructure)
**Parent Phase:** [Phase 0: Data Collection](../PHASE_0_INDEX.md)
```

**Also update:**
- Sub-phase numbers in headers
- Parent phase links (check `../` vs `../../` depth)
- Navigation links at bottom
- Status and priority if changed

---

### Step 6: Handle Archived/Superseded Files

**For archived implementations (e.g., MongoDB → PostgreSQL):**

1. **Move to archive directory:**
   ```bash
   mkdir -p docs/phases/phase_0/archive/mongodb_superseded/
   mv docs/phases/phase_0/0.X_old_mongo/ docs/phases/phase_0/archive/mongodb_superseded/0.X_old_mongo_SUPERSEDED/
   ```

2. **Update archived README:**
   ```markdown
   # 0.X: Old Implementation (SUPERSEDED)

   **Status:** 🗄️ ARCHIVED (October 22, 2025)
   **Superseded By:** [0.Y: New Implementation](../../0.Y_new_implementation/README.md)

   ## Why Superseded
   - Reason 1 (e.g., cost savings)
   - Reason 2 (e.g., simplified architecture)
   - Reason 3 (e.g., better integration)
   ```

3. **Update references in active files:**
   ```markdown
   **Supersedes:** MongoDB Implementation (see `../archive/mongodb_superseded/0.X_old_mongo_SUPERSEDED/`) - archived October 22, 2025
   ```

4. **Follow Workflow #09 (Archive Management)** for deletion records

---

### Step 7: Verify No Broken Links

**Check for broken references:**

```bash
# Find all markdown links
grep -r "\[.*\](.*\.md)" docs/ --include="*.md" > all_links.txt

# Check each link exists (manual verification)
# Or use a link checker tool
```

**Common broken link patterns after reorganization:**
- `../../PHASE_X_INDEX.md` should be `../PHASE_X_INDEX.md` (depth changed)
- `0.X_old_name/` should be `0.X_new_name/`
- Absolute paths broken after directory moves

---

### Step 8: Update Related Workflows

**If phase reorganization affects workflows:**

1. **Find affected workflows:**
   ```bash
   grep -r "PHASE_0" docs/claude_workflows/workflow_descriptions/ -l
   ```

2. **Update workflow references:**
   - File paths in examples
   - Phase numbers in instructions
   - Navigation links

3. **Affected workflows typically include:**
   - #52 (Phase Index Management)
   - #53 (Test/Validator Organization)
   - Phase-specific workflows

---

### Step 9: Migrate Python Files (if applicable)

**If reorganization includes test/validator migration:**

**Follow Workflow #53 for:**
- Moving `test_*.py` from `docs/phases/` to `tests/phases/`
- Moving `validate_*.py` from `docs/phases/` to `validators/phases/`
- Updating imports
- Adding deprecation notices to old files

**Example migration:**
```bash
# Create target directory
mkdir -p tests/phases/phase_0/

# Copy test file with proper naming
cp docs/phases/phase_0/0.X_name/test_*.py tests/phases/phase_0/test_0_X_name.py

# Update imports in new file
# Run tests to verify
pytest tests/phases/phase_0/test_0_X_name.py -v

# Add deprecation notice to old file
# Remove old file after verification
```

---

### Step 10: Test & Verify

**Run comprehensive checks:**

```bash
# 1. Verify all tests still pass
pytest tests/phases/phase_0/ -v

# 2. Run all validators
for validator in validators/phases/phase_0/*.py; do
    echo "Running: $validator"
    python "$validator" || echo "FAILED: $validator"
done

# 3. Check for remaining old references
grep -r "old_phase_name" docs/ --include="*.md"

# 4. Verify git status looks correct
git status
git diff --stat

# 5. Check file count changes
find docs/phases/phase_0/ -name "*.md" | wc -l
```

**Verification Checklist:**
- [ ] Phase index matches actual directories
- [ ] All sub-phase READMEs have correct headers
- [ ] All cross-references point to correct paths
- [ ] No broken markdown links
- [ ] Tests pass from new locations
- [ ] Validators run successfully
- [ ] No old references remain (except in archives)
- [ ] Git diff shows expected changes

---

### Step 11: Git Commit Strategy

**Commit changes in logical sequence:**

```bash
# Commit 1: Fix phase index
git add docs/phases/phase_0/PHASE_0_INDEX.md
git add docs/phases/PHASE_0_INDEX.md  # (deletion if duplicate)
git commit -m "docs: Rewrite PHASE_0_INDEX.md to match actual directory structure

- 16 sub-phases listed (0.1-0.4, 0.7-0.18)
- Correct statuses: 4 complete, 1 pending, 11 planned
- Remove duplicate /docs/phases/PHASE_0_INDEX.md
- Update navigation links and cost summaries"

# Commit 2: Update cross-references
git add docs/README.md
git add docs/claude_workflows/
git add docs/data_collection/
git add docs/ml_systems/
git add docs/phases/phase_0/0.*/README.md
git commit -m "docs: Update all references to PHASE_0_INDEX.md location

- Updated 9 files referencing old path
- Fixed Phase 0 sub-phase navigation links
- Corrected parent phase references in 0.10-0.12"

# Commit 3: Create workflow
git add docs/claude_workflows/workflow_descriptions/55_*.md
git commit -m "docs: Add Workflow #55 - Phase Reorganization process

Document systematic process for reorganizing phases and updating references"

# Commit 4: Python file migrations (if applicable)
git add tests/phases/ validators/phases/
git commit -m "refactor: Migrate Phase 0.X tests and validators

- Move test files to tests/phases/phase_0/
- Move validators to validators/phases/phase_0/
- Update imports and add ADCE tracking"
```

---

## Integration with Other Workflows

### Workflow #09: Archive Management
**Use when:**
- Moving files to archive directories
- Creating deletion records
- Documenting why implementations were superseded

### Workflow #52: Phase Index Management
**Use when:**
- Creating new phase indexes
- Updating phase completion status
- Managing sub-phase tables

### Workflow #53: Test & Validator Organization
**Use when:**
- Migrating test files during reorganization
- Moving validators to new structure
- Creating conftest.py fixtures

---

## Common Reorganization Scenarios

### Scenario 1: Renaming a Sub-Phase

**Example:** `0.8_old_security` → `0.8_security_implementation`

```bash
# 1. Rename directory
mv docs/phases/phase_0/0.0008_old_security/ docs/phases/phase_0/0.0008_security_implementation/

# 2. Update phase index
# (Edit PHASE_0_INDEX.md with new name)

# 3. Find and replace references
grep -r "0.8_old_security" docs/ --include="*.md" -l | xargs sed -i '' 's|0.8_old_security|0.8_security_implementation|g'

# 4. Verify and commit
git diff docs/
git add docs/phases/
git commit -m "refactor: Rename 0.8_old_security to 0.8_security_implementation"
```

### Scenario 2: Renumbering Sub-Phases

**Example:** Book recommendation implementations moving from Phase 0 to Phase 5

1. Move directories: `phase_0/rec_11/` → `phase_5/5.0001_feature_engineering/`
2. Update all phase indexes (PHASE_0_INDEX.md and PHASE_5_INDEX.md)
3. Find all references to `phase_0/rec_11` and update to `phase_5/5.0001_feature_engineering`
4. Update navigation links in related sub-phases
5. Add migration notes to both phase indexes

### Scenario 3: Consolidating Duplicate Indexes

**Example:** `/docs/phases/PHASE_X_INDEX.md` and `/docs/phases/phase_X/PHASE_X_INDEX.md`

```bash
# 1. Compare files
diff docs/phases/PHASE_X_INDEX.md docs/phases/phase_X/PHASE_X_INDEX.md

# 2. Keep the more detailed one (usually in phase_X/)
# 3. Find all references to top-level file
grep -r "phases/PHASE_X_INDEX.md" docs/ -l

# 4. Update all references
sed -i '' 's|phases/PHASE_X_INDEX.md|phases/phase_X/PHASE_X_INDEX.md|g' <files>

# 5. Remove duplicate
rm docs/phases/PHASE_X_INDEX.md

# 6. Commit
git add docs/phases/
git commit -m "docs: Remove duplicate PHASE_X_INDEX.md, consolidate in phase_X/"
```

### Scenario 4: Archiving Superseded Implementations

**Example:** MongoDB implementations superseded by PostgreSQL

```bash
# 1. Create archive directory
mkdir -p docs/phases/phase_0/archive/mongodb_superseded/

# 2. Move old implementations with SUPERSEDED suffix
mv docs/phases/phase_0/0.0001_nosql_mongodb/ \
   docs/phases/phase_0/archive/mongodb_superseded/0.1_nosql_mongodb_SUPERSEDED/

# 3. Update archived README with supersession notice
# 4. Update new PostgreSQL implementations with "Supersedes:" note
# 5. Find and update all references
# 6. Follow Workflow #09 for deletion record
```

---

## Troubleshooting

### Problem: Broken Links After Reorganization

**Cause:** Relative path depth changed (e.g., `../../` → `../`)

**Solution:**
```bash
# Find broken parent phase links
grep -r "Parent Phase.*PHASE_._INDEX.md" docs/phases/ -n

# Check actual depth
ls -d docs/phases/phase_0/0.*/  # See how deep files are

# Fix path depth
sed -i '' 's|(../../PHASE_0_INDEX.md)|(../PHASE_0_INDEX.md)|g' <file>
```

### Problem: Tests Fail After Migration

**Cause:** Import paths broken after moving test files

**Solution:**
```python
# Before (in docs/phases/phase_0/0.X_name/test_file.py)
from validate_something import validate_function

# After (in tests/phases/phase_0/test_0_X_name.py)
import sys
from pathlib import Path
validators_path = Path(__file__).parent.parent.parent.parent / "validators" / "phases" / "phase_0"
sys.path.insert(0, str(validators_path))
from validate_0_X_something import validate_function
```

### Problem: Old References Still Exist

**Cause:** Missed some references during grep

**Solution:**
```bash
# More comprehensive search
grep -r "old_name" . --include="*.md" --include="*.py" --include="*.yaml"

# Search in hidden files too
grep -r "old_name" . --include=".*"

# Search case-insensitively
grep -ri "old_name" docs/
```

---

## Success Criteria

**Reorganization is complete when:**
- [ ] Phase index accurately reflects directory structure
- [ ] All sub-phase headers have correct numbers/names
- [ ] No broken markdown links
- [ ] All cross-references point to correct paths
- [ ] Tests pass from new locations
- [ ] Validators run successfully
- [ ] Old references only exist in archives
- [ ] Duplicate files removed
- [ ] Git history shows logical commit sequence
- [ ] Documentation is self-consistent

---

## Related Documentation

- [Workflow #09: Archive Management](09_archive_management.md) - File archiving procedures
- [Workflow #52: Phase Index Management](52_phase_index_management.md) - Phase index creation
- [Workflow #53: Test & Validator Organization](53_phase_test_validator_organization.md) - Test migration
- [docs/ARCHIVE_PROTOCOLS.md](../../ARCHIVE_PROTOCOLS.md) - Deletion and archiving protocols

---

**Last Updated:** October 23, 2025
**Maintained By:** NBA Simulator AWS Team
**Version:** 1.0 (Initial creation during Phase 0 reorganization)

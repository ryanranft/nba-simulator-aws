# ADR-010: Four-Digit Sub-Phase Numbering System

**Date:** 2025-10-25
**Status:** ✅ Implemented
**Implementation Date:** 2025-10-26
**Decision Maker:** Ryan Ranft + Claude Code

## Context

The project uses a hierarchical phase/sub-phase organization system to manage complex development across multiple domains (data collection, ETL, ML, etc.). Sub-phases are numbered using a decimal notation: Phase N, Sub-phase M → `N.M_name`.

### Current Situation

**Phase 0:** 16 sub-phases (0.1, 0.2, ..., 0.10, ..., 0.18)
**Phase 5:** 196 sub-phases (5.1, 5.2, ..., 5.121, ..., 5.196)

### Problem Statement

1. **Sorting Ambiguity:**
   - Filesystem alphabetical sort: `0.1`, `0.10`, `0.11`, `0.2`, `0.3` (incorrect logical order)
   - Logical order: `0.1`, `0.2`, `0.3`, ..., `0.10`, `0.11` (requires natural sort)
   - Confusion between `0.1` (single digit) and `0.10` (double digit)

2. **Scalability Issues:**
   - Phase 5 already has 196 sub-phases
   - Will soon reach `5.100+`, creating 3-digit vs 1-digit confusion
   - Variable-length numbering makes navigation inconsistent

3. **Reference Confusion:**
   - Documentation references to `0.1` could mean sub-phase 1 or 10
   - Test file `test_0_0001.py` vs `test_0_0010.py` - unclear at a glance
   - Validator naming similarly ambiguous

### Constraints

- Must maintain human-readability
- Must support at least 100+ sub-phases per phase (Phase 5 needs 200+)
- Must work with filesystem sorting (no special tools required)
- Must minimize breaking changes during migration

## Decision

**Adopt a zero-padded 4-digit sub-phase numbering system:**

**Format:** `{phase}.{sub-phase:04d}_{name}`

**Examples:**
- `0.1_initial_data_collection` → `0.0001_initial_data_collection`
- `0.10_postgresql_jsonb_storage` → `0.0010_postgresql_jsonb_storage`
- `5.121_implement_ab_testing` → `5.0121_implement_ab_testing`
- `5.196_last_current_phase` → `5.0196_implement_last_technique`

**Scope:**
- All phase directories in `docs/phases/phase_*/`
- All test files in `tests/phases/phase_*/`
- All validator files in `validators/phases/phase_*/`
- All documentation references

## Rationale

### 1. Eliminates Sorting Ambiguity
- Filesystem sort now matches logical sort
- `0.0001`, `0.0002`, `0.0010`, `0.0011` (both sorts identical)
- No special natural-sort tools required

### 2. Future-Proof Scalability
- Supports up to 9,999 sub-phases per phase
- Phase 5 at 196 can grow to 9,999 without renumbering
- Consistent width prevents future migrations

### 3. Visual Clarity
- Zero-padding creates visual alignment in directory listings
- Unambiguous at a glance: `0.0001` vs `0.0010`
- Test/validator files immediately recognizable

### 4. Industry Standard
- Many projects use zero-padded numbering (e.g., `001_migration.sql`)
- Familiar pattern for developers
- Compatible with version control systems

## Alternatives Considered

### Alternative 1: Variable-Length Numbering (Current System)
- **Pros:** Shorter names, human-readable
- **Cons:** Sorting ambiguity, confusion between 0.1/0.10, doesn't scale
- **Why rejected:** Already causing problems at 196 sub-phases

### Alternative 2: Three-Digit Numbering (0.001)
- **Pros:** Shorter than 4-digit, supports 999 sub-phases
- **Cons:** Insufficient for Phase 5 (currently 196, growing)
- **Why rejected:** Would require future migration when hitting 999

### Alternative 3: Hierarchical Nested Structure (0.1.1, 0.1.2)
- **Pros:** Supports unlimited depth
- **Cons:** More complex, harder to navigate, excessive nesting
- **Why rejected:** Over-engineered for current needs

### Alternative 4: UUID or Hash-Based Naming
- **Pros:** Guaranteed uniqueness
- **Cons:** Not human-readable, doesn't convey order
- **Why rejected:** Sacrifices usability

## Consequences

### Positive

✅ **Unambiguous Sorting:**
- Filesystem and logical order now match
- No more confusion between `0.1` and `0.10`

✅ **Scalability:**
- Supports 9,999 sub-phases per phase
- No future renumbering required

✅ **Consistency:**
- All phases use identical naming convention
- Tests, validators, docs all aligned

✅ **Readability:**
- Zero-padding creates visual alignment
- Easier to scan directory listings

### Negative

⚠️ **One-Time Migration Cost:**
- ~212 directories to rename (Phase 0: 16, Phase 5: 196)
- ~58 test/validator files to rename
- ~100+ documentation references to update
- Estimated 1.5-2 hours of work

⚠️ **Longer Names:**
- `0.0001` vs `0.1` (3 extra characters)
- Minimal impact on readability

⚠️ **Git History:**
- File renames show as delete + add in history
- Can use `git log --follow` to track across renames

### Mitigation

- **Migration Script:** Automated renaming script with dry-run mode
- **Atomic Commit:** Single commit for entire migration
- **Validation:** Run full test suite post-migration
- **Documentation:** ADR + commit message provide context

## Implementation

### Phase 1: Preparation (Completed)
1. ✅ Create this ADR
2. ✅ Create feature branch: `refactor/4digit-subphase-numbering`
3. ✅ Generate renaming script: `scripts/maintenance/rename_subphases_to_4digit.sh`

### Phase 2: Execution (In Progress)
1. Dry-run preview of all changes
2. Backup current state
3. Execute renaming:
   - Phase 0: 16 directories
   - Phase 5: 196 directories
   - Test files: 39 files
   - Validator files: 19 files
4. Update documentation references
5. Update workflows (#52, #53, #58)

#### STEP 5B: Smart Phase Reference Cleanup (Planned)

**Status:** Pending (follows STEP 5)

**Context:**
STEP 5 updated 1,300 phase references across 427 files. Verification check found ~500 remaining instances of old patterns ("0.1", "0.10", "0.11", etc.). However, not all these instances are phase references:
- ✅ **Phase references** (need updating): "Phase 0.1", "phase_0/0.1_", "Sub-Phase 0.10"
- ❌ **Statistical values** (leave alone): "0.1 blocks per game", "$0.50/month", "averages 0.16 points"
- ❌ **Legitimate decimals** (leave alone): Version numbers, percentages, costs

**Solution:**
Create context-aware Python script that distinguishes phase references from numerical values.

**Implementation:** `scripts/maintenance/smart_phase_reference_cleanup.py`

**Features:**

1. **Pattern Detection**
   - Search patterns: `0.1`, `0.10` through `0.99`
   - File types: `.md`, `.py`, `.yaml`, `.txt`
   - Directories: `docs/`, `scripts/`, `tests/`, `validators/`, `inventory/`
   - Exclude: `data/`, `synthesis_output/`, `.git/`, `docs/archive/`

2. **Context Classification**

   For each match, analyze surrounding text (±50 characters) to classify as:

   - **A. Phase References** (UPDATE these):
     - Patterns: `Phase 0.1`, `phase_0/0.1_`, `Sub-Phase 0.10`, `Phase 0.16-0.18`
     - Context keywords: "Phase", "Sub-Phase", "phase_", "PHASE_"
     - Path patterns: `docs/phases/phase_0/0.X_name/`

   - **B. Statistical Values** (SKIP these):
     - Patterns: `0.1 blocks`, `averages 0.16`, `+$0.50`
     - Context keywords: "blocks", "points", "averages", "per", "$", "%"
     - Unit patterns: `0.X [unit]` where unit is: blocks, points, dollars, percent

   - **C. Archive Files** (SKIP these):
     - Any file in: `docs/archive/`
     - Rationale: Archives preserve historical references intentionally

   - **D. Ambiguous Cases** (FLAG for manual review):
     - Cannot determine with confidence
     - Present to user for decision

3. **Safe Replacement Rules**

   Phase 0 (2-digit sub-phases):
   ```
   Phase 0.1 → Phase 0.0001
   Phase 0.10 → Phase 0.0010
   phase_0/0.1_ → phase_0/0.0001_
   Sub-Phase 0.16-0.18 → Sub-Phase 0.0016-0.0018
   ```

   Phase 5 (3-digit sub-phases):
   ```
   Phase 5.5 → Phase 5.0005
   phase_5/5.27_ → phase_5/5.0027_
   ```

4. **Output Reports**

   - **Summary Report:** Total counts by category (phase refs, statistical, archive, ambiguous)
   - **Detailed Classification:** Line-by-line breakdown with context
   - **Change Preview:** Git-style diffs for each file
   - **Logs:** All actions logged to `phase_cleanup.log`

5. **Execution Modes**

   - `--analyze` (default): Find all matches, classify, generate reports, no changes
   - `--dry-run`: Show exactly what would change, preview diffs, no changes
   - `--execute`: Make the changes (only classified phase references)
   - `--interactive`: Show each ambiguous case, ask user for decision

6. **Safety Features**

   - ✅ Creates git backup branch before any changes
   - ✅ Never modifies archive files (`docs/archive/`)
   - ✅ Never modifies data files (`data/`, `synthesis_output/`)
   - ✅ Validates regex before applying
   - ✅ Preserves file permissions and encoding
   - ✅ Comprehensive logging

**Core Algorithm:**

```python
class PhaseReferenceClassifier:
    """Classify 0.X patterns as phase references or other values"""

    PHASE_KEYWORDS = [
        'Phase', 'phase_', 'Sub-Phase', 'PHASE_',
        'docs/phases/', '/phase_'
    ]

    STATISTICAL_KEYWORDS = [
        'blocks', 'points', 'averages', 'per', 'average',
        '$', '%', 'percent', 'rate', 'ratio'
    ]

    ARCHIVE_PATHS = [
        'docs/archive/', '/archive/', '_archive'
    ]

    def classify(self, match, context_before, context_after, file_path):
        """Returns: 'phase', 'statistical', 'archive', or 'ambiguous'"""

        # Check archive first (highest priority skip)
        if any(arch in file_path for arch in self.ARCHIVE_PATHS):
            return 'archive'

        # Check for phase keywords
        full_context = context_before + match + context_after
        has_phase_keyword = any(kw in full_context for kw in self.PHASE_KEYWORDS)

        # Check for statistical keywords
        has_stat_keyword = any(kw in full_context for kw in self.STATISTICAL_KEYWORDS)

        # Decision logic
        if has_phase_keyword and not has_stat_keyword:
            return 'phase'
        elif has_stat_keyword and not has_phase_keyword:
            return 'statistical'
        elif has_phase_keyword and has_stat_keyword:
            return 'ambiguous'  # Both detected - needs review
        else:
            return 'ambiguous'  # Neither detected - needs review
```

**Execution Steps:**

```bash
# Step 1: Create the script
touch scripts/maintenance/smart_phase_reference_cleanup.py
chmod +x scripts/maintenance/smart_phase_reference_cleanup.py

# Step 2: Run analysis
python scripts/maintenance/smart_phase_reference_cleanup.py --analyze

# Step 3: Review detailed classification
python scripts/maintenance/smart_phase_reference_cleanup.py --analyze --verbose

# Step 4: Dry-run
python scripts/maintenance/smart_phase_reference_cleanup.py --dry-run

# Step 5: Handle ambiguous cases
python scripts/maintenance/smart_phase_reference_cleanup.py --interactive

# Step 6: Execute
git branch backup-before-smart-cleanup
python scripts/maintenance/smart_phase_reference_cleanup.py --execute
git diff --stat
git diff | less

# Step 7: Commit if good
git add -A
git commit -m "refactor: STEP 5B - Smart phase reference cleanup (ADR-010)"
```

**Expected Outcomes:**

Based on initial scan of ~500 matches:

| Category | Count | Percentage | Action |
|----------|-------|------------|--------|
| Phase references | 45-60 | 10-12% | Update |
| Statistical values | 400-430 | 80-86% | Skip |
| Archive files | ~20 | 4% | Skip |
| Ambiguous | 5-10 | 1-2% | Manual review |

**Files to Update:** ~15-20 files

**Examples of What Gets Fixed:**
- ✅ `docs/TEST_VALIDATOR_MIGRATION_GUIDE.md` - Path reference `phase_0/0.1.../`
- ✅ `scripts/automation/extract_bbref_data_types.py` - Default path `phase_0/0.4_`
- ✅ `tests/phases/phase_0/test_0_0002_hoopr_data_collection.py` - Path strings `0.2_hoopr`
- ✅ `docs/data_collection/scrapers/README.md` - Link to Phase 0.1

**Examples of What Gets Skipped:**
- ❌ `docs/archive/*` - All archive files (preserved for history)
- ❌ `"$0.50/month"` - Currency value
- ❌ `"averages 0.1 blocks"` - Statistical metric
- ❌ `"0.16-0.18"` in context of version numbers

**Success Criteria:**

- ✅ Script correctly identifies 90%+ of phase references automatically
- ✅ Zero false positives (no statistical values incorrectly changed)
- ✅ Clear reports showing classification reasoning
- ✅ All archive files left untouched
- ✅ Interactive mode for ambiguous cases
- ✅ Git backup created before changes
- ✅ Comprehensive logging of all actions

**Estimated Time:** 1-2 hours (script creation + testing + execution)

### Phase 3: Validation
1. Run test suite: `pytest tests/phases/ -v`
2. Run validators manually
3. Validate documentation links
4. Check phase index files

### Phase 4: Commit & Merge
1. Single atomic commit
2. Push to feature branch
3. Merge to main after validation

### Timeline
- **Preparation:** 30 minutes
- **Execution:** 45-60 minutes
- **Validation:** 15-20 minutes
- **Total:** 1.5-2 hours

## Success Metrics

1. **Zero Sorting Ambiguity:**
   - `ls docs/phases/phase_0/` shows logical order
   - No confusion between single/double digit numbers

2. **All Tests Pass:**
   - `pytest tests/phases/ -v` → 100% pass rate
   - No broken imports or references

3. **Documentation Links Work:**
   - All phase index links functional
   - Cross-references resolve correctly

4. **Future-Proof:**
   - System supports growth to 9,999 sub-phases
   - No planned future renumbering

## Review Date

**Review Trigger:** When any phase approaches 1,000 sub-phases

**Expected:** Not needed (4-digit supports 9,999)

## References

- **Current Phase Structure:** `docs/phases/PHASE_0_INDEX.md`, `docs/phases/PHASE_5_INDEX.md`
- **Renaming Script:** `scripts/maintenance/rename_subphases_to_4digit.sh`
- **Related Issues:**
  - Phase 5 has 196 sub-phases (documented in PHASE_5_INDEX.md)
  - Confusion between 0.1 and 0.10 in navigation

## Notes

### Migration Strategy

This is a **one-time breaking change** that prevents future confusion. The migration is timed strategically:

1. **After Phase 0 completion** - Validates solid foundation before major refactor
2. **Before Phase 5 hits 200+** - Prevents further growth with broken numbering
3. **During active development** - Easier to fix issues while system is evolving

### Communication Plan

- ADR documents rationale and decision
- Commit message provides context for git history
- Updated CLAUDE.md reflects new naming convention
- Workflows updated to use new format going forward

### Rollback Plan

If critical issues discovered:
```bash
git revert HEAD  # Atomic commit makes rollback clean
```

All changes in single commit enable clean rollback if needed.

### Detailed Rollback Procedure

If critical issues are discovered after deployment, follow one of these rollback strategies:

#### Option 1: Simple Revert (Recommended for Single-Commit Rollback)

If the migration was done in a single atomic commit:

```bash
# Identify the commit to revert
git log --oneline | head -5

# Revert the ADR-010 implementation commit
git revert <commit-sha>

# Example:
# git revert 6fb4ec3

# Push to remote
git push origin main
```

**Pros:**
- Clean git history (shows revert explicitly)
- Preserves original commit for future reference
- Safe and reversible

**Cons:**
- Creates a new revert commit
- May conflict with subsequent commits

#### Option 2: Forward Fix (Recommended for Production)

Instead of full rollback, fix the specific issue:

**If breaking imports:**
```bash
# Fix import paths in affected files
# Update to correct format
git add .
git commit -m "fix: Correct phase import paths after ADR-010"
```

**If failing tests:**
```bash
# Update test discovery patterns
# Fix test file references
pytest tests/ -v  # Verify fixes
git add .
git commit -m "fix: Update test patterns for ADR-010 format"
```

**If broken links:**
```bash
# Find broken links
grep -r "\[.*\](phase_[0-9]/[0-9]\.[0-9]_" docs/

# Update documentation links
git add .
git commit -m "docs: Fix documentation links for ADR-010"
```

**Pros:**
- Maintains ADR-010 benefits
- Fixes specific issue without full rollback
- Preserves work already done

**Cons:**
- Requires identifying root cause
- May take longer than revert

#### Option 3: Hard Reset (Emergency Only - Destructive)

**⚠️ WARNING:** This is destructive and should only be used in emergencies.

```bash
# Create backup first
git branch emergency-backup-$(date +%Y%m%d-%H%M%S)

# Hard reset to before ADR-010
git reset --hard <commit-before-adr-010>

# Force push (DANGEROUS - requires team coordination)
git push origin main --force

# Notify all contributors immediately
```

**When to use:**
- Repository is completely broken
- No other option works
- Team has been notified and agrees

**Never use if:**
- Other contributors have pulled the changes
- Changes have been deployed to production
- There's any alternative solution

#### Rollback Testing Procedure

Before executing any rollback:

```bash
# 1. Test current state
pytest tests/ -v
python -m py_compile scripts/**/*.py

# 2. Create test branch
git checkout -b test-rollback-adr-010

# 3. Perform rollback on test branch
git revert <commit-sha>

# 4. Validate rollback
pytest tests/ -v
bash scripts/maintenance/validate_phase_numbering.sh
python scripts/automation/validate_phase.py 0

# 5. If tests pass, apply to main
git checkout main
git merge test-rollback-adr-010

# 6. If tests fail, investigate before rollback
git checkout main
git branch -D test-rollback-adr-010
```

#### Post-Rollback Actions

After successful rollback:

1. **Update PROGRESS.md:**
   ```markdown
   ## Recent Changes
   - **ADR-010 Rollback (Date):** Reverted 4-digit format due to [reason]
   - **Status:** Using old format (N.M) until issues resolved
   ```

2. **Update ADR-010 status:**
   ```markdown
   **Status:** ❌ Rolled Back
   **Rollback Date:** [Date]
   **Reason:** [Specific issue that required rollback]
   ```

3. **Disable validation hooks:**
   ```bash
   # Temporarily disable ADR-010 pre-commit hook
   # Edit .pre-commit-config.yaml
   # Comment out validate-phase-numbering hook
   ```

4. **Notify contributors:**
   - Create GitHub issue explaining rollback
   - Update documentation
   - Communicate timeline for re-attempt

#### Prevention of Rollback Necessity

To minimize rollback risk:

- ✅ Test thoroughly before merging
- ✅ Use feature branch for migration
- ✅ Run full test suite before push
- ✅ Validate all phase numbering
- ✅ Check documentation links
- ✅ Review with team before merge
- ✅ Deploy during low-activity period
- ✅ Have backup branch ready

---

## Implementation Summary

**Status:** ✅ COMPLETE
**Implementation Date:** October 26, 2025
**Time to Implement:** ~2 hours
**Commits:** 3 (6fb4ec3, 52cbf5f, and this final update)

### What Was Implemented

**Tier 1: Critical Path (REQUIRED)** ✅ COMPLETE
- ✅ Updated CLAUDE.md with 4-digit format examples and ADR-010 references (9 changes)
- ✅ Verified all 6 PHASE_N_INDEX.md files use 4-digit format in file paths
- ✅ Updated scripts/automation/validate_phase.py usage examples (7 changes)
- ✅ Updated QUICKSTART.md phase references (4 changes)
- ✅ Comprehensive validation checks passed

**Tier 2: Prevention & Automation (RECOMMENDED)** ✅ COMPLETE
- ✅ Added pre-commit hook for automatic phase numbering validation
- ✅ Created scripts/maintenance/validate_phase_numbering.sh validation script
- ✅ Created permanent documentation templates (docs/templates/)
- ⏸️ Optional tasks deferred: Standalone Python validator, regression test suite

**Tier 3: Documentation (OPTIONAL)** - Not implemented
- Future documentation improvements can be added as needed

**Tier 4: Future Enhancements (OPTIONAL)** - Not implemented
- Auto-generators and session manager improvements can be added later

### Files Modified

**Documentation (20 changes):**
- CLAUDE.md - Sub-phase format, examples, ML frameworks
- QUICKSTART.md - Phase references updated to 4-digit
- docs/adr/010-four-digit-subphase-numbering.md - Status updated to "Implemented"

**Scripts (7 changes):**
- scripts/automation/validate_phase.py - Usage examples and docstrings

**Automation (NEW):**
- .pre-commit-config.yaml - Added phase numbering validation hook
- scripts/maintenance/validate_phase_numbering.sh - Validation script (NEW, 102 lines)

**Templates (NEW):**
- docs/templates/phase-index-template.md - Phase index template (NEW)
- docs/templates/sub-phase-template.md - Sub-phase template (NEW)

### Migration Scope

**Phases Migrated:**
- ✅ Phase 0: 22 subdirectories (previously 18, grew during implementation)
- ✅ Phase 5: 196 subdirectories

**Phases NOT Migrated (Future Work):**
- Phases 1-4, 6-9: Will be migrated when they become active phases

**Why Phased Migration:**
- Phase 0 and 5 are the only active phases with significant sub-phases
- Other phases have minimal sub-phases and can be migrated as they grow
- Validation script focuses on migrated phases to avoid false positives

### Validation Results

**All checks passing:**
- ✅ Phase 0 directories use 4-digit format
- ✅ Phase 5 directories use 4-digit format
- ✅ All test files (Phase 0 & 5) use 4-digit format
- ✅ All validator files (Phase 0 & 5) use 4-digit format
- ✅ Key documentation files use 4-digit references
- ✅ Pre-commit hook tested and passing
- ✅ Validation script tested standalone - all checks pass

### Success Metrics Achievement

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| Zero Sorting Ambiguity | All phases sort correctly | ✅ Yes | PASS |
| All Tests Pass | 100% pass rate | ✅ Yes | PASS |
| Documentation Links Work | All links functional | ✅ Yes | PASS |
| Future-Proof | Support 9,999 sub-phases | ✅ Yes | PASS |
| Automation | Prevent future violations | ✅ Yes | PASS |

### Lessons Learned

1. **Incremental Migration Works:** Migrating Phase 0 and 5 first was the right call
2. **Automation is Essential:** Pre-commit hook prevents accidental old format usage
3. **Templates Improve Consistency:** Templates ensure new phases follow format
4. **Display vs. Path Format:** It's acceptable to use shortened format (1.0) in display text as long as paths use 4-digit (1.0000)
5. **Validation Before Implementation:** Having clear ADR saved significant debugging time

### Future Work

**Optional Enhancements (If Needed):**
- Standalone Python validation script (more detailed reporting)
- Regression test suite (automated testing)
- Migration of Phases 1-4, 6-9 (when they become active)
- CI/CD integration for validation

**Maintenance:**
- Pre-commit hook will automatically validate new changes
- Templates available in docs/templates/ for new phases
- Validation script can be run manually anytime: `bash scripts/maintenance/validate_phase_numbering.sh`

### Implementation Tracking

**Full implementation details:** `docs/refactoring/adr-010/00-MASTER-TRACKER.md`

**Note:** The tracking system (docs/refactoring/adr-010/) can be deleted after confirming this implementation is stable. Consider archiving instead of deletion for historical reference.

---

**Related ADRs:**
- ADR-008: Phase Reorganization (phase numbering strategy)

**Supersedes:**
- None (first decision on sub-phase numbering format)

**Superseded By:**
- None (current standard)

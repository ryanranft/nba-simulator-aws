# ADR-010: Four-Digit Sub-Phase Numbering System

**Date:** 2025-10-25
**Status:** Accepted
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
   - Test file `test_0_1.py` vs `test_0_10.py` - unclear at a glance
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

---

**Related ADRs:**
- ADR-008: Phase Reorganization (phase numbering strategy)

**Supersedes:**
- None (first decision on sub-phase numbering format)

**Superseded By:**
- None (current standard)

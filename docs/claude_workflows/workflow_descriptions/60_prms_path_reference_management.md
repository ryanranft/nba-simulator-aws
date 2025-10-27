# Workflow #60: PRMS Path Reference Management

**Version:** 1.0.0
**Created:** October 26, 2025
**Status:** ✅ Production
**Integration:** Pre-commit hooks, Session Manager, DIMS

---

## Overview

PRMS (Path Reference Management System) is an automated system for detecting, classifying, and fixing outdated path references across the codebase. It prevents technical debt from accumulating after major refactorings (like the October 2025 Phase Reorganization where phases 6, 8, 9 were reorganized into phases 0, 2).

**Core Capabilities:**
- Automated scanning of 2,800+ files for path references
- Intelligent classification with confidence scoring (≥80% auto-fix threshold)
- Pre-commit hook integration to prevent new violations
- Session manager integration for automatic validation
- DIMS integration for health metrics tracking
- Multi-format reporting (Markdown, JSON, HTML)

---

## When to Use PRMS

### Automatic Usage (No Manual Intervention)

PRMS runs automatically in these scenarios:

1. **Pre-commit Hook** - Blocks commits with outdated path references
2. **Session Start** - Validates path references during `session_manager.sh start`
3. **Session End** - Reports path reference health during `session_manager.sh end`

### Manual Usage (Explicit Commands)

Use PRMS manually for:

1. **After Major Refactoring** - Scan and fix path references after reorganizing phases/directories
2. **Generating Audit Reports** - Create comprehensive reports for documentation
3. **Investigating Specific Files** - Check individual files for path references
4. **Dry-Run Testing** - Preview fixes before applying them

---

## Commands & Usage

### Basic Commands

```bash
# Scan for path references
python scripts/maintenance/prms_cli.py scan

# Scan and classify references
python scripts/maintenance/prms_cli.py scan --classify

# Scan, classify, and generate report
python scripts/maintenance/prms_cli.py scan --classify --report

# Generate reports from existing scan
python scripts/maintenance/prms_cli.py report

# Validate path references (check if paths exist)
python scripts/maintenance/prms_cli.py validate

# Fix outdated references (dry-run mode)
python scripts/maintenance/prms_cli.py fix --dry-run

# Fix outdated references (apply changes)
python scripts/maintenance/prms_cli.py fix

# Fix with automatic confirmation
python scripts/maintenance/prms_cli.py fix --yes

# Check specific file
python scripts/maintenance/prms_cli.py check docs/README.md
```

### Integration Commands

```bash
# Session manager (automatic PRMS validation)
bash scripts/shell/session_manager.sh start  # Runs PRMS scan
bash scripts/shell/session_manager.sh end    # Validates PRMS status

# DIMS integration (view path reference health)
python scripts/monitoring/dims_cli.py verify  # Includes PRMS metrics

# Pre-commit hook (automatic)
git commit -m "message"  # Hook runs validate_path_references.sh
```

---

## How PRMS Works

### 1. Scanning Phase

**What it does:**
- Scans configured directories (`docs/`, `scripts/`, `tests/`, `validators/`, etc.)
- Detects path reference patterns:
  - Directory references: `docs/phases/phase_6/`
  - Prose references: `Phase 6`, `phase 6.1`
  - Code references: `phase_6`, `PHASE_6`
  - File names: `phase_6_*.py`, `test_6_1.py`
- Uses parallel scanning (4 workers) for speed
- Processes ~2,800 files in <3 seconds

**Configuration:** `config/prms_config.yaml` → `scan` section

### 2. Classification Phase

**What it does:**
- Categorizes each reference into one of three categories:

  1. **MUST_UPDATE** - Outdated references in active code/docs (auto-fixable)
  2. **SKIP** - Historical documentation (archives, migrations, ADRs)
  3. **MANUAL_REVIEW** - Context-dependent references requiring human judgment

**Classification Rules:**

**MUST_UPDATE criteria:**
- File in `always_update` paths (docs/, scripts/, tests/, validators/)
- NOT in `exclude` paths (archives, migrations, ADRs)
- High confidence (≥80%) that fix is correct
- Clear mapping available (phase 6 → phase 0, phase 9 → phase 2)

**SKIP criteria:**
- File in `docs/archive/`, `docs/migrations/`, `docs/adr/`
- Historical documentation that should preserve old format
- Backup files (*.backup, *.bak)

**MANUAL_REVIEW criteria:**
- Workflow step names (e.g., `phase_6_completion`)
- Ambiguous context
- Low confidence (<80%)
- Special case handling needed

**Configuration:** `config/prms_config.yaml` → `classification` section

### 3. Validation Phase

**What it does:**
- Verifies that referenced paths actually exist
- Checks for broken symlinks
- Validates file references point to real files

**Configuration:** `config/prms_config.yaml` → `validation` section

### 4. Fix Phase

**What it does:**
- Auto-corrects MUST_UPDATE references with ≥80% confidence
- Creates backups before modifying files (`.prms_backup` suffix)
- Applies fixes in reverse line order (preserves line numbers)
- Supports dry-run mode to preview changes

**Safety Features:**
- Backup creation (enabled by default)
- Confirmation prompt (unless `--yes` flag used)
- Maximum files per run limit (100 by default)
- Dry-run mode for testing

**Configuration:** `config/prms_config.yaml` → `fix` section

### 5. Reporting Phase

**What it does:**
- Generates multi-format reports (Markdown, JSON, HTML)
- Groups references by category and file type
- Shows suggested fixes with file:line references
- Creates audit trail for compliance

**Report Locations:**
- `inventory/outputs/prms/prms_audit_report.md`
- `inventory/outputs/prms/prms_audit_report.json`
- `inventory/outputs/prms/prms_audit_report.html`

**Configuration:** `config/prms_config.yaml` → `report` section

---

## Pre-commit Hook Behavior

### How It Works

When you run `git commit`, the pre-commit hook:

1. Gets list of staged files
2. Runs PRMS scan and classification
3. Checks if any staged files contain MUST_UPDATE references (≥80% confidence)
4. If violations found:
   - **Blocks the commit** (exit code 1)
   - Shows file:line references with suggested fixes
   - Provides commands to fix the issue
5. If no violations: commit proceeds normally

### Example Output

**Success (no violations):**
```bash
$ git commit -m "Add new feature"
🔍 Validating path references with PRMS...
   Scanning staged files for path references...
   ✓ No outdated path references found in staged files
[main abc1234] Add new feature
```

**Failure (violations found):**
```bash
$ git commit -m "Update documentation"
🔍 Validating path references with PRMS...
   Scanning staged files for path references...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✗ Path reference validation FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 3 outdated path reference(s) in staged files:
docs/README.md:
  Line 42: phase_6 → phase_0
  Line 58: Phase 6.1 → Phase 0.0019
  Line 73: docs/phases/phase_9/ → docs/phases/phase_2/

💡 To fix these references:
   1. Review suggestions above
   2. Run: python scripts/maintenance/prms_cli.py fix --dry-run
   3. Review changes, then run: python scripts/maintenance/prms_cli.py fix
   4. Stage fixed files and commit again

💡 To see full report:
   python scripts/maintenance/prms_cli.py report

See: docs/claude_workflows/workflow_descriptions/60_prms_path_reference_management.md
```

### Bypassing the Hook (Not Recommended)

If you absolutely need to commit despite violations:

```bash
# Skip all pre-commit hooks (use with extreme caution)
git commit --no-verify -m "message"
```

**⚠️ Warning:** Only bypass the hook if:
1. You're committing documentation about the old format
2. You're working on PRMS itself and testing
3. You have explicit approval to commit with violations

---

## Session Manager Integration

### Session Start

When you run `bash scripts/shell/session_manager.sh start`, PRMS:

1. Runs quick scan and classification
2. Counts MUST_UPDATE references (≥80% confidence)
3. Reports status:
   - ✓ All path references up to date (0 violations)
   - ⚠️ Found X outdated path reference(s) (suggestions provided)

**Example Output:**
```bash
▶ PATH REFERENCES (PRMS)
  ⚠️  Found 5 outdated path reference(s)
  💡 Run: python scripts/maintenance/prms_cli.py report
  💡 Fix: python scripts/maintenance/prms_cli.py fix
```

### Session End

When you run `bash scripts/shell/session_manager.sh end`, PRMS:

1. Checks for any new path reference violations
2. Reminds you to fix before next session
3. Integrated with documentation checklist

**Example Output:**
```bash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 3. DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ COMMAND_LOG.md updated today
✓ PROGRESS.md updated today
✓ FILE_INVENTORY.md is current
⚠️  PRMS: 3 outdated path reference(s) detected
   💡 Fix before next session: python scripts/maintenance/prms_cli.py fix

💡 Consider updating documentation before next session
```

---

## DIMS Integration

### Metrics Tracked

PRMS integrates with DIMS to track path reference health:

**Metrics in `inventory/metrics.yaml`:**
```yaml
code_quality:
  path_references:
    total_scanned: 2844      # Total references found
    must_update: 0           # High-confidence fixes needed
    manual_review: 3290      # Low-confidence, needs human review
    skipped: 409             # Intentionally skipped (archives)
    health_status: clean     # clean | needs_attention | unknown
```

### Viewing PRMS Metrics

```bash
# Full DIMS verification (includes PRMS)
python scripts/monitoring/dims_cli.py verify

# DIMS report (shows all metrics including PRMS)
python scripts/monitoring/dims_cli.py report

# Update DIMS metrics (after running PRMS)
python scripts/monitoring/dims_cli.py update
```

### Health Status Values

- **clean** - 0 MUST_UPDATE references
- **needs_attention** - 1+ MUST_UPDATE references found
- **unknown** - PRMS scan not yet run or failed

---

## Configuration Reference

### Key Configuration Sections

**`config/prms_config.yaml` structure:**

```yaml
# Pattern detection
patterns:
  phase_directories: ["docs/phases/phase_{N}/"]
  phase_prose: ["Phase {N}", "phase {N}.{M}"]
  phase_code: ["phase_{N}", "PHASE_{N}"]

# Classification rules
classification:
  always_update:
    paths: ["docs/*.md", "scripts/**/*.py", ...]
  always_skip:
    paths: ["docs/archive/**", "docs/migrations/**", ...]
  manual_review:
    patterns: ["phase_{N}_completion", ...]

# Phase mappings (from reorganizations)
mappings:
  phase_0:
    new_phase: "0"
    sub_phase_map:
      "6.0": "0.0019"  # Old phase 6.0 → New phase 0.0019
      "8.0": "0.0022"  # Old phase 8.0 → New phase 0.0022
  phase_2:
    new_phase: "2"
    sub_phase_map:
      "9.0": "2.0000"  # Old phase 9.0 → New phase 2.0000
      "9.1": "2.0001"  # Old phase 9.1 → New phase 2.0001

# Confidence scoring
confidence:
  auto_fix_threshold: 0.8  # Only auto-fix if ≥80% confident
```

**See full configuration:** `config/prms_config.yaml`

---

## Common Workflows

### Workflow 1: After Major Refactoring

**Scenario:** You just reorganized phases or renamed directories.

```bash
# 1. Update PRMS mappings in config/prms_config.yaml
vim config/prms_config.yaml

# 2. Run full scan with classification and reporting
python scripts/maintenance/prms_cli.py scan --classify --report

# 3. Review the report
less inventory/outputs/prms/prms_audit_report.md

# 4. Preview fixes (dry-run)
python scripts/maintenance/prms_cli.py fix --dry-run

# 5. Apply fixes
python scripts/maintenance/prms_cli.py fix

# 6. Verify all fixes applied
python scripts/maintenance/prms_cli.py scan --classify

# 7. Commit the changes
git add .
git commit -m "refactor: Fix path references after reorganization"
```

### Workflow 2: Investigating Pre-commit Hook Failure

**Scenario:** Your commit was blocked by PRMS.

```bash
# 1. See what references are outdated
python scripts/maintenance/prms_cli.py report

# 2. Fix automatically (if confidence is high)
python scripts/maintenance/prms_cli.py fix

# 3. OR fix manually (if you disagree with suggestions)
vim <file_with_violation>

# 4. Re-stage fixed files
git add <fixed_files>

# 5. Try committing again
git commit -m "your message"
```

### Workflow 3: Weekly Maintenance

**Scenario:** Regular health check during weekly maintenance.

```bash
# 1. Run PRMS scan
python scripts/maintenance/prms_cli.py scan --classify

# 2. Check DIMS for path reference health
python scripts/monitoring/dims_cli.py verify

# 3. If violations found, generate report
python scripts/maintenance/prms_cli.py report

# 4. Fix violations
python scripts/maintenance/prms_cli.py fix

# 5. Update DIMS metrics
python scripts/monitoring/dims_cli.py update
```

### Workflow 4: Checking Specific File

**Scenario:** You're editing a file and want to check for path references.

```bash
# Check specific file
python scripts/maintenance/prms_cli.py check docs/README.md

# Example output:
# Found 3 references in docs/README.md:
#   Line 42: phase_6 (phase_code)
#   Line 58: Phase 6.1 (phase_subphase)
#   Line 73: docs/phases/phase_9/ (phase_dir)
```

---

## Troubleshooting

### Issue: Pre-commit hook fails but scan shows no violations

**Cause:** Stale scan results, or scan missed staged files.

**Solution:**
```bash
# Re-run scan explicitly
python scripts/maintenance/prms_cli.py scan --classify

# Check scan output file
cat inventory/outputs/prms/prms_audit_report.json

# Verify pre-commit hook is up to date
pre-commit install
```

### Issue: PRMS suggests wrong fix

**Cause:** Confidence threshold too low, or incorrect mapping.

**Solution:**
```bash
# 1. Review the suggestion
python scripts/maintenance/prms_cli.py report

# 2. If wrong, update config/prms_config.yaml mappings
vim config/prms_config.yaml

# 3. Re-run classification
python scripts/maintenance/prms_cli.py classify

# 4. OR fix manually
vim <file>

# 5. Mark as SKIP in config if intentionally old format
# Add to classification.always_skip.files in config/prms_config.yaml
```

### Issue: Session manager PRMS check is slow

**Cause:** Full scan running at every session start.

**Solution:**
- PRMS scan runs in background with quiet mode
- If still slow, check scan configuration in `config/prms_config.yaml`
- Consider adjusting `scan.max_workers` (default: 4)

### Issue: "PRMS scan output not found"

**Cause:** PRMS hasn't been run yet in this session.

**Solution:**
```bash
# Run initial scan
python scripts/maintenance/prms_cli.py scan --classify
```

### Issue: Fix applies incorrect changes

**Cause:** High confidence score but incorrect context.

**Solution:**
```bash
# 1. Restore from backup
cp <file>.prms_backup <file>

# 2. Update classification rules
vim config/prms_config.yaml
# Add pattern to classification.manual_review.patterns

# 3. Re-classify
python scripts/maintenance/prms_cli.py classify

# 4. Fix manually
vim <file>
```

---

## Best Practices

### 1. Run PRMS After Major Refactorings

Whenever you:
- Reorganize phase directories
- Rename sub-phases
- Move documentation files
- Refactor code structure

**Always:**
1. Update `config/prms_config.yaml` mappings
2. Run PRMS scan and fix
3. Commit PRMS changes separately from refactoring

### 2. Trust the Pre-commit Hook

- Don't bypass the hook unless absolutely necessary
- If hook fails, fix the violations before committing
- Hook saves you from future technical debt

### 3. Review Dry-Run Before Fixing

```bash
# Always preview first
python scripts/maintenance/prms_cli.py fix --dry-run

# Review output carefully

# Then apply
python scripts/maintenance/prms_cli.py fix
```

### 4. Keep Configuration Current

- Update `mappings` section after reorganizations
- Adjust `confidence.auto_fix_threshold` based on accuracy
- Add new patterns to `always_skip` for historical docs

### 5. Monitor DIMS Metrics

- Check `code_quality.path_references.health_status` weekly
- Goal: maintain "clean" status (0 MUST_UPDATE)
- Treat MANUAL_REVIEW items as backlog

### 6. Archive PRMS Reports

```bash
# After major fix, archive the report
cp inventory/outputs/prms/prms_audit_report.md \
   docs/archive/prms_reports/prms_audit_$(date +%Y-%m-%d).md
```

---

## Files Modified by This Workflow

**Created:**
- `scripts/maintenance/prms_cli.py` - Core PRMS automation
- `scripts/maintenance/validate_path_references.sh` - Pre-commit hook
- `config/prms_config.yaml` - PRMS configuration
- `inventory/outputs/prms/` - Report output directory

**Modified:**
- `.pre-commit-config.yaml` - Added PRMS hook
- `scripts/shell/session_manager.sh` - Added PRMS checks (session start/end)
- `inventory/metrics.yaml` - Added PRMS metrics
- `CLAUDE.md` - Added Automation Triad section

**Documentation:**
- `docs/claude_workflows/workflow_descriptions/60_prms_path_reference_management.md` (this file)
- `docs/claude_workflows/CLAUDE_WORKFLOW_ORDER.md` - Workflow index

---

## Related Workflows

- **#8 (Git Commit)** - PRMS pre-commit hook runs automatically
- **#14 (Session End)** - PRMS validation check
- **#52 (Phase Index Management)** - Phase reorganization triggers PRMS
- **#55 (Phase Reorganization)** - Update PRMS mappings after reorganization
- **#56 (DIMS Management)** - PRMS metrics integration

---

## Success Metrics

**System is working correctly when:**
- ✅ Pre-commit hook blocks commits with violations (100% catch rate)
- ✅ Session start/end shows accurate path reference counts
- ✅ DIMS `health_status` is "clean" (0 MUST_UPDATE)
- ✅ Classification accuracy ≥95% for MUST_UPDATE category
- ✅ Zero false positives in SKIP category
- ✅ Scan completes in <5 seconds for 2,800+ files

**Red flags:**
- ❌ Pre-commit hook frequently bypassed (--no-verify)
- ❌ MUST_UPDATE count increasing over time
- ❌ Incorrect fixes being applied (review mappings)
- ❌ Scan taking >10 seconds (check parallel workers)

---

## Version History

**v1.0.0 (October 26, 2025):**
- Initial PRMS deployment
- Pre-commit hook integration
- Session manager integration
- DIMS integration
- October 2025 Phase Reorganization mappings (phase 6, 8, 9 → 0, 2)
- Fixed 116 outdated path references across 26 files
- 100% classification accuracy achieved

---

*For configuration details, see `config/prms_config.yaml`*
*For PRMS CLI source code, see `scripts/maintenance/prms_cli.py`*
*For DIMS integration, see Workflow #56*
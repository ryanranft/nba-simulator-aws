# Documentation Maintenance Guide

**Purpose:** Keep documentation synchronized with actual project state

---

## Overview

This guide explains how to keep documentation up-to-date automatically and manually.

---

## Automated Updates

### Weekly Automation (Recommended)

Run this script weekly to update documentation:

```bash
./scripts/maintenance/update_docs.sh
```

**What it updates:**
- ✅ Current AWS costs in QUICKSTART.md
- ✅ ADR count in docs/adr/README.md
- ✅ "Last Updated" timestamps in all docs
- ✅ Project statistics (commits, files, etc.)
- ✅ Validates internal documentation links
- ✅ Identifies stale documentation (30+ days old)

**Output:** Shows what was updated, suggests next steps

---

### Progress Synchronization

Check if PROGRESS.md reflects actual AWS resources:

```bash
python scripts/maintenance/sync_progress.py
```

**What it checks:**
- ✅ S3 bucket status (Phase 1)
- ✅ RDS database status (Phase 3.1)
- ✅ Glue crawler status (Phase 2.1)
- ✅ Glue ETL job status (Phase 2.2)
- ✅ Project statistics

**Modes:**
```bash
# Preview changes without applying
python scripts/maintenance/sync_progress.py --dry-run

# See suggestions (currently detection-only)
python scripts/maintenance/sync_progress.py
```

---

### Cost Tracking (Weekly)

Check AWS costs:

```bash
./scripts/aws/check_costs.sh
```

**Updates these files:**
- QUICKSTART.md (manual update if costs changed significantly)

---

## Manual Updates Required

Some documentation requires human judgment and should NOT be auto-updated:

### When to Manually Update

| File | When to Update | How Often |
|------|----------------|-----------|
| **ADRs** | New architectural decision made | As needed |
| **STYLE_GUIDE.md** | Code style preferences change | Rarely |
| **TESTING.md** | Testing strategy evolves | As needed |
| **TROUBLESHOOTING.md** | New issue encountered + solved | As needed |
| **SETUP.md** | Setup process changes | Rarely |
| **PROGRESS.md** | Complete a major phase | After each phase |
| **CLAUDE.md** | Instructions for Claude change | Rarely |

---

## Documentation Update Checklist

### After Completing a Phase

When you finish a major phase (e.g., Phase 2.1: Glue Crawler):

**1. Update PROGRESS.md:**
```markdown
# Find the phase section
### Phase 2.1: AWS Glue Crawler

# Change status from ⏸️ PENDING to ✅ COMPLETE
**Status:** ✅ COMPLETE
```

**2. Update cost estimates:**
```bash
# Check actual costs
./scripts/aws/check_costs.sh

# Update QUICKSTART.md if significantly different from estimates
# Update PROGRESS.md cost projections if needed
```

**3. Run documentation sync:**
```bash
./scripts/maintenance/update_docs.sh
```

**4. Commit changes:**
```bash
git add PROGRESS.md QUICKSTART.md
git commit -m "Update progress: Phase 2.1 complete"
```

---

### After Encountering a New Issue

When you solve a new problem:

**1. Add to TROUBLESHOOTING.md:**
```markdown
### ❌ [Problem Description]

**Symptom:**
```bash
error message here
```

**Solution:**
```bash
solution steps here
```
```

**2. Log the command:**
```bash
source scripts/shell/log_command.sh
log_cmd [the command that fixed it]
log_solution [description of solution]
```

**3. Commit:**
```bash
git add docs/TROUBLESHOOTING.md COMMAND_LOG.md
git commit -m "Add troubleshooting: [problem description]"
```

---

### After Making an Architectural Decision

When you make a significant technical decision:

**1. Create new ADR:**
```bash
# Copy template
cp docs/adr/template.md docs/adr/006-your-decision.md

# Fill in all sections:
# - Context: Why are we making this decision?
# - Decision: What are we doing?
# - Rationale: Why this approach?
# - Alternatives: What else did we consider?
# - Consequences: What are the trade-offs?
```

**2. Update ADR index:**
```bash
# Edit docs/adr/README.md
# Add entry to the "Active ADRs" table
```

**3. Update relevant docs:**
- PROGRESS.md if decision affects roadmap
- QUICKSTART.md if decision changes workflow
- STYLE_GUIDE.md if decision affects code style

**4. Run automation:**
```bash
./scripts/maintenance/update_docs.sh
```

**5. Commit:**
```bash
git add docs/adr/
git commit -m "Add ADR-006: [decision title]"
```

---

### Monthly Documentation Review

**Schedule:** Last day of each month

**Checklist:**

```bash
# 1. Run all automation scripts
./scripts/maintenance/update_docs.sh
python scripts/maintenance/sync_progress.py
./scripts/aws/check_costs.sh

# 2. Review stale documentation
# (update_docs.sh shows files not updated in 30+ days)

# 3. Verify PROGRESS.md accuracy
# - Are completed phases marked ✅?
# - Are pending phases marked ⏸️?
# - Are costs still accurate?

# 4. Check for broken links
# (update_docs.sh validates this)

# 5. Update statistics
# - Commit count
# - Documentation lines
# - Test coverage (when tests exist)

# 6. Commit monthly update
git add -u
git commit -m "Monthly documentation refresh - $(date +%Y-%m)"
```

---

## Automation Schedule

### Daily (Automated via cron - optional)

```bash
# Add to crontab (optional):
# 0 9 * * * cd /Users/ryanranft/nba-simulator-aws && ./scripts/aws/check_costs.sh > /tmp/daily_costs.txt
```

### Weekly (Manual)

```bash
# Every Monday morning:
cd /Users/ryanranft/nba-simulator-aws
./scripts/maintenance/update_docs.sh
python scripts/maintenance/sync_progress.py
git add -u
git commit -m "Weekly docs update - $(date +%Y-%m-%d)"
git push origin main
```

### Monthly (Manual)

Follow "Monthly Documentation Review" checklist above.

---

## What NOT to Automate

**Never auto-commit documentation changes.** Always review before committing.

**Why:**
- Automation might make incorrect assumptions
- Human review catches errors
- Architectural decisions need thoughtful documentation
- Security: Avoid accidentally committing sensitive data

**Safe workflow:**
1. Run automation scripts
2. Review changes: `git diff`
3. Edit manually if needed
4. Commit when satisfied

---

## Documentation Quality Checks

### Before Committing Documentation

Run these checks:

```bash
# 1. Syntax check all shell scripts
for script in scripts/**/*.sh; do
    bash -n "$script" && echo "✅ $script" || echo "❌ $script"
done

# 2. Check Python syntax
python -m py_compile scripts/**/*.py

# 3. Validate Markdown (optional - requires markdownlint)
# npm install -g markdownlint-cli
# markdownlint docs/**/*.md

# 4. Check for sensitive data
grep -r "password\|secret\|token\|key" docs/ | grep -v "example\|placeholder\|your_"

# 5. Verify internal links
./scripts/maintenance/update_docs.sh  # Includes link validation
```

---

## Claude Code Integration

### Keeping Claude's Context Current

**Claude Code reads these files automatically:**
- CLAUDE.md (instructions)
- PROGRESS.md (project status)
- COMMAND_LOG.md (historical context)
- docs/adr/README.md (architecture decisions)
- TROUBLESHOOTING.md (known issues)

**To update Claude's knowledge:**

1. **After completing work:**
   ```bash
   # Update PROGRESS.md status
   # Run update_docs.sh
   # Commit changes
   ```

2. **New session:**
   - Claude reads updated docs automatically
   - Mention if something major changed: "I just completed Phase 2.1"

3. **When Claude seems outdated:**
   - Ask: "Can you check PROGRESS.md for the current phase?"
   - Run: `./scripts/maintenance/sync_progress.py`
   - Share output with Claude

---

## Troubleshooting Automation

### Update script fails

**Problem:** `update_docs.sh` errors

**Solution:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check file permissions
ls -la scripts/maintenance/update_docs.sh

# Run with debug output
bash -x scripts/maintenance/update_docs.sh
```

---

### Python script fails

**Problem:** `sync_progress.py` errors

**Solution:**
```bash
# Check Python version
python --version  # Should be 3.11

# Check dependencies
python -c "import subprocess, re, sys; print('OK')"

# Run with verbose output
python -v scripts/maintenance/sync_progress.py
```

---

### Stale documentation warnings

**Problem:** Docs not updated in 30+ days

**Solution:**
```bash
# Review flagged files
./scripts/maintenance/update_docs.sh | grep "Stale"

# Decide if update needed:
# - Content still accurate? Just touch file: touch docs/file.md
# - Content outdated? Edit and update
# - File no longer needed? Delete and remove references
```

---

## Best Practices

### DO:
- ✅ Run `update_docs.sh` weekly
- ✅ Review changes before committing
- ✅ Update PROGRESS.md after each phase
- ✅ Document new issues in TROUBLESHOOTING.md
- ✅ Create ADRs for significant decisions
- ✅ Keep COMMAND_LOG.md via `log_cmd`

### DON'T:
- ❌ Auto-commit without review
- ❌ Let docs go stale for >30 days
- ❌ Skip ADRs for major decisions
- ❌ Forget to update costs after AWS changes
- ❌ Commit sensitive data in documentation

---

## Quick Reference

```bash
# Weekly maintenance
./scripts/maintenance/update_docs.sh

# Check project progress
python scripts/maintenance/sync_progress.py

# Check costs
./scripts/aws/check_costs.sh

# Verify environment
./scripts/shell/verify_setup.sh

# Log command
source scripts/shell/log_command.sh && log_cmd [command]
```

---

**Last Updated:** 2025-09-30
**Maintenance Schedule:** Weekly (Monday mornings)
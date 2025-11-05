# Archive Location

**Date Relocated:** November 5, 2025
**Reason:** Phase 0 cleanup - remove cross-contamination risk between archived and active code

---

## ⚠️ Archives Moved to External Location

All archived code and documentation has been relocated to:

```
~/sports-simulator-archives/nba/
```

This includes:
- **Scripts:** Deprecated ETL scrapers, pre-Python migration shell workflows
- **Documentation:** MongoDB implementations, historical proposals
- **Conversations:** Claude conversation archives (per Workflow #09)
- **Per-Commit Archives:** Automated snapshots via `archive_manager.sh`

---

## What Was Removed from Project

The following directories were removed from the project repository:

| Removed Directory | Now At | Reason |
|-------------------|--------|--------|
| `scripts/archive/` | `~/sports-simulator-archives/nba/scripts/` | Moved to external archive |
| `docs/phases/phase_0/archive/` | `~/sports-simulator-archives/nba/docs/phase_0/` | Moved to external archive |
| `archive/` | Removed (empty) | Empty directory |
| `docs/archive/` | Removed (empty) | Empty directory |
| `docs/phases/archive/` | Removed (empty) | Empty directory |
| `logs/archive/` | Removed (empty) | Empty directory |

---

## How to Access Archives

**View archive structure:**
```bash
ls -la ~/sports-simulator-archives/nba/
```

**Read archive documentation:**
```bash
cat ~/sports-simulator-archives/nba/README.md
```

**Search archived content:**
```bash
grep -r "search_term" ~/sports-simulator-archives/nba/
```

**Restore archived file:**
```bash
cp ~/sports-simulator-archives/nba/scripts/deprecated/old_script.py scripts/
```

---

## Git History Preserved

All archived content is still accessible in git history:

```bash
# View file history
git log --follow -- scripts/archive/deprecated/old_script.py

# Restore from specific commit
git checkout <commit-sha> -- path/to/file
```

---

## Related Workflows

- **Workflow #09:** `docs/claude_workflows/workflow_descriptions/09_archive_management.md`
- **Workflow #36:** `docs/claude_workflows/workflow_descriptions/36_pre_push_repo_cleanup.md`

---

## Archive Procedures

**Create new archive (after commits):**
```bash
bash scripts/maintenance/archive_manager.sh full
```

**Status:**
```bash
bash scripts/maintenance/archive_manager.sh status
```

---

For complete archive documentation, see:
```
~/sports-simulator-archives/nba/README.md
```

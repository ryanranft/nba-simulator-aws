## 💾 Backup & Recovery Workflows

### Regular Backup Workflow

**Run after significant work sessions or before risky operations:**

```bash
make backup
```

**What this backs up:**
- All uncommitted changes (git diff)
- Untracked files (git ls-files --others)
- Current branch state (git branch status)
- Working tree snapshot (tar archive)

**Backup location:** `~/sports-simulator-archives/nba/backups/backup-YYYYMMDD-HHMMSS/`

**When to run backup:**
- ✅ Before destructive operations (database drops, file deletions)
- ✅ After multiple hours of work (>2 hours without commit)
- ✅ Before risky refactoring
- ✅ After 5+ commits
- ✅ End of productive session (if uncommitted changes exist)

### File Deletion Protocol

**CRITICAL: ALWAYS archive before deleting files**

1. **Identify file(s) to delete**
2. **Check if tracked by git:**
   ```bash
   git ls-files | grep <filename>
   ```
3. **Archive the file(s):**
   ```bash
   # Create archive directory
   ARCHIVE_DIR=~/sports-simulator-archives/nba/deleted-files-$(date +%Y%m%d-%H%M%S)
   mkdir -p "$ARCHIVE_DIR"

   # Copy file(s) to archive
   cp <file> "$ARCHIVE_DIR/"
   ```
4. **Create deletion record:**
   ```bash
   cat > "$ARCHIVE_DIR/DELETION_RECORD.md" << EOF
   # File Deletion Record

   **Date:** $(date)
   **Files Deleted:** <list>
   **Reason:** <why deleted>
   **Recovery:** Archive at $ARCHIVE_DIR
   EOF
   ```
5. **Remove from git tracking:**
   ```bash
   git rm --cached <file>
   echo "<file>" >> .gitignore
   ```
6. **Commit removal:**
   ```bash
   git add .gitignore
   git commit -m "Remove <file> - archived to $ARCHIVE_DIR"
   ```
7. **Delete local file** (optional - only if not needed)
   ```bash
   rm <file>
   ```

### Archive Search Workflow

**When you need to find past conversations or deleted files:**

**Method 1: Directory Structure Search**
```bash
# Find by date
ls -lt ~/sports-simulator-archives/nba/ | head -20

# Find chat logs
find ~/sports-simulator-archives/nba/chat-logs -name "*.md"

# Find deleted files
find ~/sports-simulator-archives/nba/deleted-files* -type f
```

**Method 2: Git-Based Search**
```bash
cd ~/sports-simulator-archives/nba
git log --all --oneline | grep <keyword>
git show <commit-hash>:path/to/file
```

**Archive categories:**
- `chat-logs/` - Saved conversations
- `backups/` - Working tree snapshots
- `deleted-files-*/` - Pre-deletion archives
- `pre-push-cleanup-*/` - Files removed before GitHub push

---


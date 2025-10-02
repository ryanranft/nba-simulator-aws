# How to Verify Chat Log Archives

## Quick Check

```bash
# 1. Find the most recent archive (uses latest git commit SHA)
LATEST_SHA=$(git rev-parse HEAD)
ARCHIVE_DIR="$HOME/sports-simulator-archives/nba/$LATEST_SHA"

# 2. Check if archive exists
if [ -d "$ARCHIVE_DIR" ]; then
    echo "✅ Archive exists: $ARCHIVE_DIR"
    ls -lh "$ARCHIVE_DIR"/CHAT_LOG*.md 2>/dev/null || echo "❌ No chat logs found"
else
    echo "❌ Archive not found: $ARCHIVE_DIR"
fi
```

## Step-by-Step Verification

### 1. Check What Archives Exist

```bash
# List all NBA archives by date (newest first)
ls -lt ~/sports-simulator-archives/nba/

# View the archive index
cat ~/sports-simulator-archives/nba/README.md
```

### 2. Check Specific Archive for Chat Logs

```bash
# Get current commit SHA
CURRENT_SHA=$(git rev-parse HEAD)
echo "Current commit: $CURRENT_SHA"

# Check if chat logs exist in current archive
ls -lh ~/sports-simulator-archives/nba/$CURRENT_SHA/CHAT_LOG*.md
```

**Expected output if chat logs are archived:**
```
CHAT_LOG_ORIGINAL.md    # Full conversation with credentials
CHAT_LOG_SANITIZED.md   # Redacted version safe for sharing
```

### 3. Verify Chat Log Contents

```bash
# View first 50 lines of original chat log
head -50 ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG_ORIGINAL.md

# Check file sizes (both should be substantial if conversation was archived)
du -h ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG*.md
```

### 4. Check Archive Metadata

```bash
# View git-info.txt to see what was archived
cat ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/git-info.txt
```

**Expected to see:**
```
✅ CHAT_LOG_ORIGINAL.md
✅ CHAT_LOG_SANITIZED.md
```

## Common Scenarios

### Scenario 1: No Chat Logs Found

**Problem:** Archive exists but no `CHAT_LOG*.md` files

**Cause:** Chat log archiving script wasn't run for this commit

**Solution:**
```bash
# 1. Create CHAT_LOG.md in project root (copy conversation from terminal)
# 2. Run chat log archiving script
bash scripts/maintenance/archive_chat_log.sh
# 3. Verify again
ls -lh ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG*.md
```

### Scenario 2: Archive Directory Doesn't Exist

**Problem:** No archive folder for current commit SHA

**Cause:** Archive script wasn't run after this commit

**Solution:**
```bash
# Create archive for current commit
bash scripts/maintenance/archive_gitignored_files.sh

# Then archive chat log
bash scripts/maintenance/archive_chat_log.sh
```

### Scenario 3: Want to Check Older Archive

**Problem:** Need to verify chat logs from previous commit

**Solution:**
```bash
# Find specific commit SHA (e.g., from git log)
git log --oneline -10

# Check that archive
ls -lh ~/sports-simulator-archives/nba/{SPECIFIC_SHA}/CHAT_LOG*.md
```

## Archive Workflow (Reference)

**Complete workflow for archiving chat logs:**

```bash
# 1. Make sure you have commits to archive
git log --oneline -1

# 2. Create CHAT_LOG.md in project root
#    (Manually copy conversation from terminal/Claude interface)

# 3. Create base archive if it doesn't exist
bash scripts/maintenance/archive_gitignored_files.sh

# 4. Archive the chat log (creates both versions)
bash scripts/maintenance/archive_chat_log.sh

# 5. Verify it worked
ls -lh ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG*.md
```

## Security Verification

**Before sharing sanitized chat log, verify credentials were redacted:**

```bash
# Check sanitized version for credential patterns (should find NONE)
SANITIZED="~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG_SANITIZED.md"

# These should return NO matches:
grep -i "aws_access_key" "$SANITIZED"
grep -i "NbaSimulator2025" "$SANITIZED"
grep -E "Bearer [A-Za-z0-9_-]{20,}" "$SANITIZED"

# If any matches found, DO NOT share the sanitized version
```

## Troubleshooting

### Archive script says "CHAT_LOG.md not found"

**Solution:** Create `CHAT_LOG.md` in project root first:
```bash
# Navigate to project root
cd /Users/ryanranft/nba-simulator-aws

# Create chat log (paste conversation here)
# Then run archive script
bash scripts/maintenance/archive_chat_log.sh
```

### Can't find archive directory

**Solution:** Check if $HOME is set correctly:
```bash
echo $HOME  # Should show /Users/ryanranft
ls ~/sports-simulator-archives/nba/
```

### Want to view difference between original and sanitized

**Solution:**
```bash
SHA=$(git rev-parse HEAD)
diff ~/sports-simulator-archives/nba/$SHA/CHAT_LOG_ORIGINAL.md \
     ~/sports-simulator-archives/nba/$SHA/CHAT_LOG_SANITIZED.md
```

**Expected:** Lines with `[REDACTED]` in sanitized version

## Quick Reference Commands

```bash
# List all archives
ls -lt ~/sports-simulator-archives/nba/

# View archive index
cat ~/sports-simulator-archives/nba/README.md

# Check current commit's archive
ls -lh ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/

# View chat logs for current commit
ls -lh ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG*.md

# Read original chat log
less ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG_ORIGINAL.md

# Read sanitized chat log
less ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG_SANITIZED.md

# Count lines in chat logs
wc -l ~/sports-simulator-archives/nba/$(git rev-parse HEAD)/CHAT_LOG*.md
```

---

**See also:**
- `docs/ARCHIVE_SYSTEM.md` - Complete archive system documentation
- `CHAT_LOG_INSTRUCTIONS.md` - How to create and archive chat logs
- `scripts/maintenance/archive_chat_log.sh` - Chat log archiving script
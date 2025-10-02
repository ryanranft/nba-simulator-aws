# Chat Log Archiving Instructions

## Purpose

Archive complete conversation history with Claude Code to SHA-based archive folders while maintaining strict security protocols.

## Why Archive Chat Logs?

- **Preserve LLM reasoning** - Future assistants can understand why decisions were made
- **Document troubleshooting** - See exact error messages and solutions
- **Track evolution** - Understand how the project developed over time
- **Enable cross-sport replication** - Copy workflows to NFL/MLB/NHL projects

## How It Works

### Two Versions Created:

1. **CHAT_LOG_ORIGINAL.md** - Complete verbatim conversation with passwords preserved
2. **CHAT_LOG_SANITIZED.md** - Redacted version safe for sharing

### Security Protocol:

```bash
# What gets redacted in sanitized version:
- AWS credentials (access keys, secret keys, tokens)
- Database passwords
- API keys and bearer tokens
- GitHub tokens (PATs)
- Connection strings with passwords
```

## Usage Instructions

### Step 1: Export Your Chat from Claude Code

Unfortunately, Claude Code doesn't provide a direct export feature yet. You'll need to manually create the chat log:

**Option A: Manual Copy (Recommended for now)**
1. In your terminal, select and copy the conversation output
2. Create a file: `CHAT_LOG.md` in project root
3. Paste the conversation
4. Save the file

**Option B: Use macOS Script Recorder (for automation)**
```bash
# Record terminal output to file
script -a CHAT_LOG.md
# Now all terminal output is captured
# When done, press Ctrl+D to stop recording
```

### Step 2: Run Archive Script

```bash
# First, create the main archive structure
bash scripts/maintenance/archive_gitignored_files.sh

# Then, archive the chat log
bash scripts/maintenance/archive_chat_log.sh
```

### Step 3: Verify Archive

```bash
# Check what was created
ls -la ~/sports-simulator-archives/nba/{SHA}/CHAT_LOG*

# View sanitized version (safe)
cat ~/sports-simulator-archives/nba/{SHA}/CHAT_LOG_SANITIZED.md | head -50

# View original with passwords (careful!)
cat ~/sports-simulator-archives/nba/{SHA}/CHAT_LOG_ORIGINAL.md | head -50
```

## Archive Structure

```
~/sports-simulator-archives/nba/{SHA}/
├── git-info.txt                      # Git metadata
├── CHAT_LOG_ORIGINAL.md              # ⚠️ Contains passwords - local only
├── CHAT_LOG_SANITIZED.md             # ✅ Safe for sharing
├── PYCHARM_DATABASE_SETUP.md         # Database credentials
├── COMMAND_LOG.md                    # Command history with credentials
└── ... (other .gitignored files)
```

## Security Guarantees

✅ **Original log stays local** - Never added to .gitignore, never committed
✅ **Sanitized version safe** - All credentials redacted
✅ **Archive outside git** - Located in `~/sports-simulator-archives/`
✅ **Script in git** - Only the tool is committed, not the data

## For Future Sports (NFL/MLB/NHL)

When creating a new sport simulator:

1. Copy the archive scripts from this repo
2. Run them in the new project directory
3. Creates separate archive: `~/sports-simulator-archives/nfl/`
4. Tell future LLM: "Reference NBA chat logs at ~/sports-simulator-archives/nba/{SHA}/CHAT_LOG_ORIGINAL.md"

## Troubleshooting

**"Archive directory not found"**
- Run `archive_gitignored_files.sh` first to create the SHA folder

**"No CHAT_LOG.md found"**
- Create CHAT_LOG.md in project root with conversation text
- Or use script recorder to capture terminal output

**"Want to update existing archive"**
- Just run the script again - it will overwrite CHAT_LOG files
- Other archived files remain unchanged

## Examples

### Example 1: Archive After Completing Phase 2

```bash
# Commit your work
git add . && git commit -m "Complete Phase 2"

# Archive all .gitignored files
bash scripts/maintenance/archive_gitignored_files.sh

# Create chat log from terminal output
# (manually copy conversation to CHAT_LOG.md)

# Archive the chat
bash scripts/maintenance/archive_chat_log.sh
```

### Example 2: Reference Past Conversation

```bash
# Find the SHA from git history
git log --oneline | head -5

# Open archived chat for that commit
cat ~/sports-simulator-archives/nba/{SHA}/CHAT_LOG_ORIGINAL.md | less
```

## Important Notes

⚠️ **CHAT_LOG.md should be in .gitignore** - Add it if not already there
⚠️ **Original logs contain real passwords** - Never commit, never share
✅ **Sanitized logs are safe** - Can be shared or committed to private repos
✅ **Each SHA gets its own archive** - Complete snapshot at each milestone

## Future Enhancement Ideas

- Auto-capture Claude Code conversation output
- CLI command to export conversation directly
- Automatic sanitization when copying
- Integration with git hooks to auto-archive on commit
# Archive System - Dual Approach Documentation

## Overview

This project uses a **dual archive system** to preserve work history while maintaining strict security:

1. **Local Private Archive** - Complete files with all credentials (never goes to GitHub)
2. **Sanitized Public Archive** - Redacted files safe for GitHub (optional)

---

## System Architecture

```
Project Directory (~/nba-simulator-aws/)
├── .git/              # Git repository (goes to GitHub)
├── scripts/           # Archive scripts (goes to GitHub)
└── docs/              # This documentation (goes to GitHub)

External Archive (~/sports-simulator-archives/)
├── nba/
│   ├── README.md                          # Index of all commits
│   └── {full-sha}/                        # One folder per commit
│       ├── git-info.txt                   # Git metadata
│       ├── CHAT_LOG_ORIGINAL.md           # ⚠️ Contains passwords
│       ├── CHAT_LOG_SANITIZED.md          # ✅ Safe to share
│       ├── PYCHARM_DATABASE_SETUP.md      # ⚠️ Contains passwords
│       ├── COMMAND_LOG.md                 # ⚠️ Contains passwords
│       └── ... (other .gitignored files)
└── nfl/               # Future sport simulators
    └── {full-sha}/
```

---

## Archive Location Strategy

### Why External Archive?

**Location:** `~/sports-simulator-archives/{sport}/{sha}/`

**Benefits:**
- ✅ **Never accidentally committed** - Outside git repository
- ✅ **Survives git operations** - Safe from `git clean`, resets, etc.
- ✅ **Sport-specific organization** - Easy to reference NBA when building NFL
- ✅ **SHA-based snapshots** - Exact correlation to git commits
- ✅ **Preserves credentials** - Complete context for future LLMs

### Directory Structure Explained:

```
~/sports-simulator-archives/
└── nba/                                    # Sport name (auto-detected)
    ├── README.md                           # Index: SHA → Date → Description
    └── 4fc708470c73582b6ca41f30d9863e951eb75326/  # Full git SHA
        ├── git-info.txt                    # Commit metadata
        ├── CHAT_LOG_ORIGINAL.md            # Verbatim conversation
        ├── CHAT_LOG_SANITIZED.md           # Redacted version
        ├── PYCHARM_DATABASE_SETUP.md       # DB credentials
        ├── COMMAND_LOG.md                  # Command history
        ├── EXTRACTION_STATUS.md            # Process status
        └── logs/                           # Small log files
            ├── schema_update.log
            └── teams_extraction.log
```

---

## Approach 1: Local Private Archive (RECOMMENDED)

### Purpose

Preserve **EVERYTHING** including passwords, credentials, and IP addresses for future reference. Never goes to GitHub.

### What Gets Archived

✅ All `.gitignored` documentation files
✅ Database passwords (plain text)
✅ AWS credentials (if present)
✅ Private IP addresses
✅ Connection strings with passwords
✅ Small log files (< 10 MB)
✅ Chat logs with full context

### Usage

```bash
# After completing a milestone or phase
git commit -m "Complete Phase X"

# Archive everything to SHA-based folder
bash scripts/maintenance/archive_gitignored_files.sh

# Manually create chat log (copy from terminal)
# Paste into CHAT_LOG.md in project root

# Archive chat log
bash scripts/maintenance/archive_chat_log.sh
```

### Script: `archive_gitignored_files.sh`

**What it does:**
1. Detects sport from project directory name (e.g., `nba-simulator-aws` → `nba`)
2. Gets current git commit SHA
3. Creates `~/sports-simulator-archives/nba/{SHA}/`
4. Copies all `.gitignored` files with credentials intact
5. Copies small log files (skips massive extraction logs)
6. Creates `git-info.txt` with commit metadata
7. Updates `README.md` index

**Security guarantees:**
- ✅ Files stay on your local machine only
- ✅ Archive directory is outside git repository
- ✅ No sanitization - preserves exact state
- ✅ Safe from accidental git commits

### Script: `archive_chat_log.sh`

**What it does:**
1. Requires `CHAT_LOG.md` in project root (manual export)
2. Creates two versions:
   - `CHAT_LOG_ORIGINAL.md` - Verbatim with passwords
   - `CHAT_LOG_SANITIZED.md` - Credentials redacted
3. Adds entries to `git-info.txt`

**Python sanitization patterns:**
- AWS credentials (access keys, secret keys, tokens)
- Database passwords
- API keys and bearer tokens
- GitHub tokens (PATs)
- Connection strings with passwords

---

## Approach 2: Sanitized Public Archive (OPTIONAL)

### Purpose

Create a sanitized snapshot safe to commit to a **private GitHub repository** for team collaboration or backup.

### Location

```
~/nba-simulator-aws/archived-docs/
└── {short-sha}/                    # 7-character SHA
    ├── git-info.txt                # Git metadata
    ├── CHAT_LOG_SANITIZED.md       # Redacted conversation
    ├── EXTRACTION_STATUS.md        # Process status (sanitized)
    └── README.md                   # What was redacted
```

### What Gets Sanitized

**Replaced with `[REDACTED]`:**
- AWS access keys (AWS_ACCESS_KEY...)
- AWS secret keys
- AWS session tokens
- Database passwords
- API keys
- Bearer tokens
- GitHub tokens
- Connection strings with passwords

**Removed entirely:**
- Private IP addresses (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
- Public IP addresses
- Hostnames

### Creating Sanitized Archive

```bash
# Create sanitized snapshot for team sharing
bash scripts/maintenance/create_sanitized_archive.sh

# Review sanitized files
ls archived-docs/{short-sha}/

# Verify no credentials present
grep -ri "password\|secret\|192.168" archived-docs/{short-sha}/

# Commit to GitHub (only if verified safe)
git add archived-docs/
git commit -m "Add sanitized archive snapshot for {short-sha}"
git push origin main
```

### When to Use Sanitized Archives

**Use sanitized archives when:**
- ✅ Working with a team on a private repository
- ✅ Backing up to cloud storage
- ✅ Sharing specific troubleshooting context (without credentials)
- ✅ Creating public examples or tutorials

**DO NOT use sanitized archives when:**
- ❌ Public repository (use private repo only)
- ❌ Uncertain about sanitization completeness
- ❌ Files contain customer data or PII
- ❌ Compliance requirements prohibit any sharing

---

## Comparison: Private vs. Sanitized

| Feature | Private Archive | Sanitized Archive |
|---------|----------------|-------------------|
| **Location** | `~/sports-simulator-archives/` | `project/archived-docs/` |
| **Passwords** | ✅ Preserved | ❌ [REDACTED] |
| **IP Addresses** | ✅ Preserved | ❌ Removed |
| **Git Status** | Outside repo | Inside repo |
| **GitHub Safe** | ❌ Never commit | ✅ Private repos only |
| **Future LLMs** | ✅ Full context | ⚠️ Limited context |
| **Team Sharing** | ❌ Manual only | ✅ Via git |
| **SHA Format** | Full (64 chars) | Short (7 chars) |

---

## Using Archives with Future Sports

### When Creating NFL Simulator:

```bash
# 1. Clone NBA repo as template
git clone git@github.com:ryanranft/nba-simulator-aws.git nfl-simulator-aws
cd nfl-simulator-aws

# 2. Archive scripts work automatically (detect sport from directory)
bash scripts/maintenance/archive_gitignored_files.sh
# Creates ~/sports-simulator-archives/nfl/{sha}/

# 3. Reference NBA archives for guidance
cat ~/sports-simulator-archives/nba/{sha}/CHAT_LOG_ORIGINAL.md | less

# 4. Tell future LLM:
# "Reference NBA implementation at ~/sports-simulator-archives/nba/{sha}/"
```

### Archive Index Format

`~/sports-simulator-archives/nba/README.md` contains:

```markdown
# NBA Simulator Archive - Gitignored Files

## Folders

- **4fc7084** - main - 2025-10-02 - Add .gitignore entries (16 files)
- **2d8a03b** - main - 2025-10-02 - Add sport-specific archive script (16 files)
- **a51809d** - main - 2025-10-02 - Add chat log archiving (18 files)
```

Easy to find specific milestones and reference them!

---

## Security Best Practices

### For Private Archives

1. **Never commit** - Archive directory is outside git repo
2. **Backup securely** - Use encrypted external drive or cloud storage
3. **Restrict permissions** - `chmod 700 ~/sports-simulator-archives/`
4. **Regular cleanup** - Remove old archives after verifying newer ones
5. **Rotate credentials** - After sharing archives (even manually), rotate passwords

### For Sanitized Archives

1. **Review before commit** - Always verify sanitization worked
2. **Private repos only** - Never push sanitized archives to public GitHub
3. **Test patterns** - Run security scan on sanitized files before committing
4. **Document redactions** - Note what was redacted in README.md
5. **Compliance check** - Ensure sanitized archives meet your security policies

---

## Troubleshooting

### "Archive directory not found"

Run `archive_gitignored_files.sh` first to create the directory structure.

### "No CHAT_LOG.md found"

Create `CHAT_LOG.md` in project root by:
1. Copying terminal output to file, OR
2. Using `script -a CHAT_LOG.md` to record session

### "Want to update existing archive"

Run the scripts again - they overwrite files in the same SHA folder.

### "How do I know if sanitization worked?"

```bash
# Check for credentials in sanitized files
grep -ri "password.*=.*[a-z0-9]" archived-docs/{sha}/
grep -ri "aws_secret_access_key.*=.*[a-zA-Z0-9/+]{40}" archived-docs/{sha}/

# If no output, sanitization worked
```

### "Archive taking too much space"

```bash
# Check archive size
du -sh ~/sports-simulator-archives/

# Clean old archives (keep last 5)
cd ~/sports-simulator-archives/nba/
ls -t | tail -n +6 | xargs rm -rf
```

---

## Maintenance

### Weekly

- Archive after completing major features or phases
- Verify archives are being created in the correct location
- Check archive index (`README.md`) for completeness

### Monthly

- Review archive directory size
- Backup archives to external encrypted storage
- Test archive restoration process
- Clean up very old archives (>6 months)

### Before Starting New Sport

- Create final NBA archive snapshot
- Document any lessons learned in archive README
- Test that archive scripts work for new sport directory name
- Verify all critical work is archived

---

## Reference Commands

```bash
# Create private archive (full credentials)
bash scripts/maintenance/archive_gitignored_files.sh

# Archive chat log (creates both versions)
bash scripts/maintenance/archive_chat_log.sh

# View archive index
cat ~/sports-simulator-archives/nba/README.md

# List all archives
ls ~/sports-simulator-archives/nba/

# Find specific commit archive
git log --oneline | grep "Phase 2"
ls ~/sports-simulator-archives/nba/{SHA}/

# Check archive size
du -sh ~/sports-simulator-archives/

# Backup archives (encrypted)
tar czf nba-archives-backup.tar.gz ~/sports-simulator-archives/nba/
gpg -c nba-archives-backup.tar.gz  # Encrypt with password
```

---

## Summary

✅ **Use Private Archives** for complete preservation with all credentials
✅ **Archive at milestones** (phase completions, major features)
✅ **Reference archives** when building future sports simulators
✅ **Sanitized archives** are optional for team sharing (private repos only)
✅ **Never commit** private archives to GitHub
✅ **Test restoration** periodically to ensure archives work

Your work is preserved, secure, and reusable! 🎉
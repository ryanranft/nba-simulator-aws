# Complete Git History Rewrite Workflow with SHA Mapping

**Purpose:** Remove AWS account ID from Git history while preserving SHA references in documentation
**Created:** 2025-10-01
**Solo Developer:** Yes (simplified workflow)

---

## Quick Summary

1. ✅ **SHA mapping prepared** - SHA_MAPPING.md lists all current commit SHAs
2. ✅ **SHA references found** - 4 files contain commit SHA references
3. ✅ **Automated script ready** - generate_sha_mapping.sh will update all files
4. 🔧 **Execute rewrite** - Follow steps below
5. 🔄 **Update docs** - Run script to update SHA references

---

## Files With SHA References (Found 4)

| File | SHAs Referenced | Count |
|------|-----------------|-------|
| `HISTORY_REWRITE_GUIDE.md` | b6dac89 | 1 |
| `SECURITY_AUDIT_REPORT.md` | e315e48, 12d960a, d9432d8, 5261543, 2134b36, 3b49d36, d6fc458 | 7 |
| `docs/adr/005-git-ssh-authentication.md` | f026047, 5457d5a, 2f019c1, b418883 | 4 |
| `COMMAND_LOG.md` | f026047, 5457d5a, 2f019c1 | 3 |

**Total unique SHAs to remap:** 15 commits

---

## Complete Workflow

### Phase 1: Pre-Flight (Already Done ✅)

```bash
# ✅ DONE - SHA mapping file created
# ✅ DONE - SHA references identified
# ✅ DONE - Automated update script created
```

---

### Phase 2: Backup (CRITICAL - Do This First!)

```bash
cd /Users/ryanranft/nba-simulator-aws

# Create backup with timestamp
DATE=$(date +%Y%m%d_%H%M%S)

# Backup entire directory
tar -czf ~/Desktop/nba-backup-${DATE}.tar.gz .

# Backup just .git
cp -r .git .git.backup-${DATE}

# Verify backups
ls -lh ~/Desktop/nba-backup-${DATE}.tar.gz
ls -lh .git.backup-${DATE}/config

echo "✅ Backups created at:"
echo "   ~/Desktop/nba-backup-${DATE}.tar.gz"
echo "   .git.backup-${DATE}/"
```

**Estimated time:** 2 minutes

---

### Phase 3: Install git-filter-repo

```bash
# Check if already installed
git filter-repo --version

# If not installed:
brew install git-filter-repo

# Verify
git filter-repo --version
# Expected: git-filter-repo 2.x.x
```

**Estimated time:** 1 minute

---

### Phase 4: Execute git-filter-repo

```bash
cd /Users/ryanranft/nba-simulator-aws

# Make sure working tree is clean
git status
# Expected: working tree clean

# Create replacement file
echo "************==>************" > /tmp/replacements.txt

# POINT OF NO RETURN - Rewrite history
echo "⚠️  About to rewrite Git history..."
echo "Press Ctrl+C within 10 seconds to cancel"
sleep 10

# Execute rewrite
git filter-repo --replace-text /tmp/replacements.txt --force

# Output will show:
# Parsed X commits
# New history written in X.XX seconds...
# Completely finished after X.XX seconds.

echo "✅ History rewritten"
```

**Estimated time:** 30 seconds

---

### Phase 5: Verify Rewrite

```bash
# 1. Check account ID is gone
git log --all -p | grep "************"
# Expected: No matches

# 2. Check replacements are present
git log --all -p | grep "\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*" | head -3
# Expected: Shows ************

# 3. Count commits (should be same)
git log --oneline --all | wc -l
# Expected: 27 commits

# 4. Check recent commits
git log --oneline -10
# Should show commits with NEW SHAs

echo "✅ Verification passed"
```

**Estimated time:** 1 minute

---

### Phase 6: Generate SHA Mapping

```bash
cd /Users/ryanranft/nba-simulator-aws

# Run automated mapping script
./scripts/shell/generate_sha_mapping.sh

# This will:
# 1. Extract old SHAs from SHA_MAPPING.md
# 2. Get new SHAs from git log
# 3. Match by commit message
# 4. Display Old → New mapping
# 5. Ask if you want to auto-update files

# When prompted "Update these files automatically? (y/n)"
# Answer: y

# Output will show:
# Old SHA → New SHA : Commit Message
# ============================================
# ccf9499 → a1b2c3d : Add comprehensive security audit report
# b6dac89 → e4f5g6h : Sanitize AWS account ID...
# ... (for all 27 commits)

# Files will be automatically updated!

echo "✅ SHA references updated"
```

**Estimated time:** 1 minute

---

### Phase 7: Verify Documentation Updates

```bash
# Check that old SHAs have been replaced
git diff SECURITY_AUDIT_REPORT.md
git diff HISTORY_REWRITE_GUIDE.md
git diff docs/adr/005-git-ssh-authentication.md
git diff COMMAND_LOG.md

# Verify no old SHAs remain
grep -r "b6dac89" . --exclude-dir=.git
grep -r "e315e48" . --exclude-dir=.git
grep -r "2134b36" . --exclude-dir=.git

# Expected: No matches (except in SHA_MAPPING.md "before" section)

echo "✅ All SHA references updated"
```

**Estimated time:** 1 minute

---

### Phase 8: Commit Updated Documentation

```bash
# Stage updated files
git add SECURITY_AUDIT_REPORT.md
git add HISTORY_REWRITE_GUIDE.md
git add docs/adr/005-git-ssh-authentication.md
git add COMMAND_LOG.md
git add SHA_MAPPING.md

# Commit
git commit -m "Update SHA references after git-filter-repo

Updated commit SHA references in documentation files to reflect new commit
hashes after removing AWS account ID from Git history.

Old SHAs → New SHAs mapped in SHA_MAPPING.md

Files updated:
- SECURITY_AUDIT_REPORT.md (7 SHAs)
- HISTORY_REWRITE_GUIDE.md (1 SHA)
- docs/adr/005-git-ssh-authentication.md (4 SHAs)
- COMMAND_LOG.md (3 SHAs)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
"

echo "✅ Documentation updates committed"
```

**Estimated time:** 1 minute

---

### Phase 9: Re-add Remote and Force Push

```bash
# filter-repo removes remote for safety
# Re-add it
git remote add origin git@github.com:ryanranft/nba-simulator-aws.git

# Verify remote
git remote -v

# Check current status
git status

# FORCE PUSH (overwrites GitHub history)
echo "⚠️  About to force push to GitHub"
echo "This will overwrite remote history - CANNOT BE UNDONE"
echo "Press Ctrl+C within 10 seconds to cancel"
sleep 10

# Execute force push
git push origin main --force

# If you have other branches:
# git push origin --all --force

# If you have tags:
# git push origin --tags --force

echo "✅ Pushed to GitHub"
```

**Estimated time:** 2 minutes

---

### Phase 10: Final Verification

```bash
# Check GitHub
open https://github.com/ryanranft/nba-simulator-aws

# Manual checks on GitHub:
# 1. Browse commits - verify no account ID
# 2. Search repository for "************" - should find nothing
# 3. Check a few commits - SHAs should be different from before
# 4. Verify all files are intact

# From command line:
# Check an old SHA no longer exists (use one from SHA_MAPPING.md)
git show b6dac89
# Expected: fatal: bad object (SHA doesn't exist anymore)

# Check new SHA exists
# (Use new SHA from mapping)
git show <new-sha>
# Expected: Shows commit with ************ instead of account ID

echo "✅ GitHub history verified"
```

**Estimated time:** 2 minutes

---

### Phase 11: Cleanup

```bash
# Clean up local repository
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Check repository size (optional)
du -sh .git

# Keep backups for 30 days, then delete:
# rm ~/Desktop/nba-backup-${DATE}.tar.gz
# rm -rf .git.backup-${DATE}

echo "✅ Cleanup complete"
```

**Estimated time:** 1 minute

---

## Total Time Estimate

| Phase | Time | Complexity |
|-------|------|------------|
| Backup | 2 min | Easy |
| Install tool | 1 min | Easy |
| Execute rewrite | 30 sec | Easy |
| Verify rewrite | 1 min | Easy |
| Generate mapping | 1 min | **Automated!** |
| Verify docs | 1 min | Easy |
| Commit updates | 1 min | Easy |
| Force push | 2 min | Easy |
| Final verification | 2 min | Easy |
| Cleanup | 1 min | Easy |

**Total:** ~12 minutes

---

## Rollback Procedure (If Needed)

If something goes wrong **before force push**:

```bash
# Option 1: Restore from .git backup
cd /Users/ryanranft/nba-simulator-aws
rm -rf .git
cp -r .git.backup-${DATE} .git

# Option 2: Restore from tar backup
cd /Users/ryanranft
rm -rf nba-simulator-aws
tar -xzf ~/Desktop/nba-backup-${DATE}.tar.gz
cd nba-simulator-aws

# Verify restoration
git log --oneline -5
# Should show old SHAs
```

If something goes wrong **after force push**:

```bash
# You'll need to force push the old history back
cd /Users/ryanranft
tar -xzf ~/Desktop/nba-backup-${DATE}.tar.gz -C nba-temp
cd nba-temp

# Force push old history back
git push origin main --force

# Then re-clone
cd /Users/ryanranft
rm -rf nba-simulator-aws
git clone git@github.com:ryanranft/nba-simulator-aws.git
```

---

## Automated One-Liner (For Experienced Users)

```bash
# Complete workflow in one command (CAREFUL!)
cd /Users/ryanranft/nba-simulator-aws && \
DATE=$(date +%Y%m%d_%H%M%S) && \
tar -czf ~/Desktop/nba-backup-${DATE}.tar.gz . && \
echo "************==>************" > /tmp/replacements.txt && \
git filter-repo --replace-text /tmp/replacements.txt --force && \
./scripts/shell/generate_sha_mapping.sh && \
git add . && \
git commit -m "Update SHA references after git-filter-repo" && \
git remote add origin git@github.com:ryanranft/nba-simulator-aws.git && \
git push origin main --force && \
git reflog expire --expire=now --all && \
git gc --prune=now --aggressive && \
echo "✅ Complete!"
```

**NOT RECOMMENDED** - Use step-by-step workflow instead for safety!

---

## Checklist

### Before Starting:
- [ ] Read this entire document
- [ ] Understand you're the only collaborator (no one to notify)
- [ ] Accept that commit SHAs will change
- [ ] Ready to spend 12 minutes on this

### During Execution:
- [ ] Phase 2: Backups created and verified
- [ ] Phase 3: git-filter-repo installed
- [ ] Phase 4: History rewritten
- [ ] Phase 5: Rewrite verified
- [ ] Phase 6: SHA mapping generated
- [ ] Phase 7: Documentation updated
- [ ] Phase 8: Updates committed
- [ ] Phase 9: Force pushed to GitHub
- [ ] Phase 10: GitHub verified
- [ ] Phase 11: Cleanup complete

### After Completion:
- [ ] Account ID gone from all commits
- [ ] SHA references updated in all docs
- [ ] SHA_MAPPING.md completed
- [ ] GitHub history clean
- [ ] No broken references in documentation
- [ ] Backups kept for 30 days

---

## Questions?

**Q: What if the automated script fails?**
A: You can manually update files using SHA_MAPPING.md as reference

**Q: What if I find a SHA reference after pushing?**
A: Update it in a new commit, it's not critical

**Q: How long does GitHub keep old commits cached?**
A: Usually 1-2 weeks, then they're garbage collected

**Q: Can I undo this after force pushing?**
A: Yes, but difficult. Restore from backup and force push old history back

**Q: Will this affect my local development?**
A: No, you're the only developer, just you updating your own machine

---

**Last Updated:** 2025-10-01
**Status:** Ready to execute
**Estimated Total Time:** 12 minutes
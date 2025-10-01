# Git History Rewrite Guide - Remove AWS Account ID

**⚠️ WARNING:** This is a DESTRUCTIVE operation. Only proceed if you understand the risks.

**Current Status:** NOT RECOMMENDED for this repository (account ID is low-risk)

---

## Pre-Flight Checklist

Before proceeding, verify:

- [ ] No active collaborators (or they're prepared to re-clone)
- [ ] No open pull requests (or they can be recreated)
- [ ] Repository is private (or you accept public history change)
- [ ] You have 1-2 hours for this process
- [ ] You understand all commit SHAs will change
- [ ] You have reviewed the cons in this guide

**If ANY checkbox is unchecked, STOP and reconsider.**

---

## Step 1: Complete Backup (CRITICAL)

```bash
# Navigate to project
cd /Users/ryanranft/nba-simulator-aws

# Create multiple backup types
DATE=$(date +%Y%m%d_%H%M%S)

# 1. Backup entire directory
tar -czf ~/Desktop/nba-sim-backup-${DATE}.tar.gz .

# 2. Backup just .git directory
cp -r .git .git.backup-${DATE}

# 3. Create a backup clone
cd ~/Desktop
git clone git@github.com:ryanranft/nba-simulator-aws.git nba-simulator-backup-${DATE}

# 4. Verify backups exist
ls -lh ~/Desktop/nba-sim-backup-${DATE}.tar.gz
ls -lh /Users/ryanranft/nba-simulator-aws/.git.backup-${DATE}
ls -lh ~/Desktop/nba-simulator-backup-${DATE}/.git

echo "✅ Backups created successfully"
```

---

## Step 2: Install git-filter-repo

```bash
# Check if already installed
git filter-repo --version

# If not installed:
brew install git-filter-repo

# Verify installation
git filter-repo --version
# Expected: git-filter-repo 2.x.x
```

---

## Step 3: Test Run (Dry Run)

```bash
cd /Users/ryanranft/nba-simulator-aws

# Create test directory
cd /tmp
git clone /Users/ryanranft/nba-simulator-aws nba-test
cd nba-test

# Test the replacement on the clone
echo "************==>************" > /tmp/replacements.txt
git filter-repo --replace-text /tmp/replacements.txt --force

# Verify it worked
git log --all -p | grep "************"
# Expected: No matches

git log --all -p | grep "\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*"
# Expected: Shows replacements

# Check that nothing else broke
git log --oneline --all | head -10
# Should show commits with new SHAs

echo "✅ Test successful - safe to proceed with real repository"
```

---

## Step 4: Prepare Repository

```bash
cd /Users/ryanranft/nba-simulator-aws

# 1. Make sure everything is committed
git status
# Expected: working tree clean

# 2. Record current commit SHAs for reference
git log --oneline --all > ~/Desktop/old-commit-shas-${DATE}.txt

# 3. Check for any uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "❌ ERROR: Uncommitted changes detected. Commit or stash them first."
    exit 1
fi

echo "✅ Repository ready for rewrite"
```

---

## Step 5: Run git-filter-repo (THE POINT OF NO RETURN)

```bash
cd /Users/ryanranft/nba-simulator-aws

# Create replacements file
cat > /tmp/replacements.txt <<EOF
************==>************
EOF

# ⚠️ POINT OF NO RETURN - This will rewrite all commits
echo "⚠️  About to rewrite Git history. Press Ctrl+C within 10 seconds to cancel..."
sleep 10

# Run filter-repo
git filter-repo --replace-text /tmp/replacements.txt --force

# Output will show:
# Parsed X commits
# Rewriting and filtering commits...
# Completely finished after X seconds.

echo "✅ History rewritten"
```

---

## Step 6: Verify Changes

```bash
# 1. Check account ID is gone
git log --all -p | grep "************"
# Expected: No matches

# 2. Check replacements are present
git log --all -p | grep "\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*\\*" | head -5
# Expected: Shows replaced text

# 3. Check commit count is the same
OLD_COUNT=$(wc -l < ~/Desktop/old-commit-shas-${DATE}.txt)
NEW_COUNT=$(git log --oneline --all | wc -l)
echo "Old commits: $OLD_COUNT"
echo "New commits: $NEW_COUNT"
# Should be equal

# 4. Verify files are intact
ls -la
# Should show all expected files

# 5. Check recent commits
git log --oneline -10

echo "✅ Verification passed"
```

---

## Step 7: Re-add Remote and Force Push

```bash
# filter-repo removes remotes for safety
# Re-add remote
git remote add origin git@github.com:ryanranft/nba-simulator-aws.git

# Verify remote
git remote -v

# ⚠️ FORCE PUSH - This will overwrite GitHub history
echo "⚠️  About to force push to GitHub. This CANNOT be undone."
echo "Press Ctrl+C within 10 seconds to cancel..."
sleep 10

# Force push main branch
git push origin main --force

# If you have other branches:
git push origin --all --force

# If you have tags:
git push origin --tags --force

echo "✅ Pushed to GitHub"
```

---

## Step 8: Verify on GitHub

```bash
# Open repository in browser
open https://github.com/ryanranft/nba-simulator-aws

# Manual checks:
# 1. Browse recent commits - check for account ID
# 2. Use GitHub search: press "/" and search "************"
# 3. Check commit history - all SHAs should be different
# 4. Verify files are intact

# From command line, check a known old commit
# (use SHA from old-commit-shas file)
git show <old-sha>
# Expected: fatal: bad object (old SHA no longer exists)

echo "✅ GitHub history rewritten successfully"
```

---

## Step 9: Clean Up Old References

```bash
# Clean up local repository
cd /Users/ryanranft/nba-simulator-aws

# Remove reflog (contains old SHAs)
git reflog expire --expire=now --all

# Garbage collect old objects
git gc --prune=now --aggressive

# Verify size reduction (optional)
du -sh .git
# Should be similar or smaller than before

echo "✅ Local cleanup complete"
```

---

## Step 10: Notify Collaborators (If Applicable)

**If others have cloned the repository:**

Send this message:
```
Subject: URGENT - Git history rewritten for nba-simulator-aws

The Git history of nba-simulator-aws has been rewritten to remove sensitive data.

ACTION REQUIRED:
1. Delete your local clone
2. Re-clone from GitHub: git clone git@github.com:ryanranft/nba-simulator-aws.git
3. DO NOT merge old branches - they will cause conflicts

Timeline: Complete by [date]

Questions? Contact [you]
```

---

## Rollback Procedure (If Something Goes Wrong)

**If you need to undo the changes:**

```bash
# Option 1: Restore from .git backup
cd /Users/ryanranft/nba-simulator-aws
rm -rf .git
cp -r .git.backup-${DATE} .git
git remote -v  # Verify remote is still there

# Option 2: Restore from tar backup
cd /Users/ryanranft
rm -rf nba-simulator-aws
tar -xzf ~/Desktop/nba-sim-backup-${DATE}.tar.gz -C nba-simulator-aws
cd nba-simulator-aws
git status

# Option 3: Re-clone from GitHub (if you haven't force-pushed yet)
cd /Users/ryanranft
rm -rf nba-simulator-aws
git clone git@github.com:ryanranft/nba-simulator-aws.git
cd nba-simulator-aws

# After rollback, force push old history back to GitHub
git push origin main --force

echo "✅ Rollback complete"
```

---

## Post-Rewrite Checklist

- [ ] Verified account ID removed from all commits
- [ ] Verified files are intact
- [ ] GitHub history updated
- [ ] Collaborators notified (if applicable)
- [ ] Backups kept for 30 days
- [ ] Updated any commit references in documentation
- [ ] Recreated any tags if needed
- [ ] Verified CI/CD pipelines still work

---

## Common Issues and Solutions

### Issue 1: Force push rejected

```bash
# Error: refusing to update checked out branch
# Solution: Temporarily disable branch protection

# Go to: GitHub → Settings → Branches → Branch protection rules
# Delete or disable rule for 'main'
# After force push, re-enable protection
```

### Issue 2: Remote not found after filter-repo

```bash
# filter-repo removes remotes for safety
git remote add origin git@github.com:ryanranft/nba-simulator-aws.git
```

### Issue 3: Old commits still visible on GitHub

```bash
# GitHub caches commits for ~2 weeks
# Contact GitHub support to purge cache:
# https://support.github.com/contact
# Select: "Remove sensitive data"
```

### Issue 4: Collaborator has merge conflicts

```bash
# They need to abandon old clone and re-clone
cd /Users/collaborator/projects
rm -rf nba-simulator-aws
git clone git@github.com:ryanranft/nba-simulator-aws.git
```

---

## Final Recommendation

**FOR THIS REPOSITORY: Don't do this** ❌

**Reasons:**
1. Account ID is not a credential (low risk)
2. AWS says account IDs are not secrets
3. Already sanitized going forward
4. Risk of history rewriting outweighs benefit

**Alternative:** Keep current approach:
- ✅ Current files sanitized (commit 40ed145)
- ✅ Future commits will be clean
- ✅ Security hooks prevent future exposure
- ⚠️ Account ID in old commits (acceptable for this low-risk data)

---

## When to Actually Do This

Rewrite history ONLY if:
- ✅ Actual credentials exposed (AWS keys, passwords, tokens)
- ✅ SSH private keys committed
- ✅ Corporate policy requires it
- ✅ Legal/compliance requirement
- ❌ NOT for account IDs (low risk)

---

**Last Updated:** 2025-10-01
**Author:** Claude Code
**Status:** Documentation only - NOT RECOMMENDED for execution
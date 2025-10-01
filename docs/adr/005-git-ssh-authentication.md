# ADR-005: Git Remote Configuration (SSH vs HTTPS)

**Date:** September 30, 2025
**Status:** Resolved
**Supersedes:** ADR-004 (GitHub Integration)

## Context

Git supports two primary protocols for remote repository operations:

**HTTPS:**
- URL format: `https://github.com/user/repo.git`
- Requires authentication: Username + Personal Access Token (PAT)
- GitHub deprecated password authentication in August 2021

**SSH:**
- URL format: `git@github.com:user/repo.git`
- Requires: SSH keys configured with GitHub
- Uses public-key cryptography

**Initial situation:**
- Git remote was set to placeholder HTTPS URL
- Attempted to push with PAT but failed
- User had SSH keys already configured with GitHub account

## Problem Encountered

**HTTPS Authentication Failure:**
```bash
git push -u origin main
# Failed with: "Invalid username or token"
# Error: "could not locate repository"
```

**Root causes:**
1. Git remote URL was placeholder: `https://github.com/YOUR-USERNAME/nba-simulator-aws.git`
2. Even with correct URL, HTTPS requires PAT token management
3. GitHub deprecated password authentication
4. User already had SSH keys set up (simpler solution available)

## Decision

**Configure Git remote to use SSH protocol instead of HTTPS.**

```bash
git remote set-url origin git@github.com:ryanranft/nba-simulator-aws.git
```

## Implementation

### Step 1: Update Remote URL
```bash
# Change from HTTPS to SSH
git remote set-url origin git@github.com:ryanranft/nba-simulator-aws.git

# Verify change
git remote -v
# Output:
# origin  git@github.com:ryanranft/nba-simulator-aws.git (fetch)
# origin  git@github.com:ryanranft/nba-simulator-aws.git (push)
```

### Step 2: Verify SSH Authentication
```bash
ssh -T git@github.com
# Output: "Hi ryanranft! You've successfully authenticated, but GitHub does not provide shell access."
# Exit code: 1 (expected - this is normal for GitHub SSH test)
```

### Step 3: Sync with Remote
```bash
# Fetch remote content
git fetch origin

# Rebase local commits on top of remote initial commit
git pull origin main --rebase

# Push to GitHub
git push -u origin main
```

## Rationale

### 1. SSH Keys Already Configured
- User's system already had SSH keys set up with GitHub
- No additional setup required
- No need to create and manage PAT tokens
- More secure than storing tokens in config

### 2. Simpler Workflow
**SSH:**
- ✅ No password/token prompts for push/pull
- ✅ Keys managed by SSH agent
- ✅ One-time setup per machine
- ✅ Works seamlessly once configured

**HTTPS:**
- ❌ Requires entering PAT token for each operation
- ❌ Or storing credentials (security risk)
- ❌ Token management overhead (expiration, rotation)
- ❌ PAT creation requires GitHub web interface

### 3. Security
**SSH advantages:**
- Public-key cryptography (more secure)
- Keys never transmitted over network
- Can use passphrase-protected keys
- Can be revoked per-device on GitHub
- No credentials stored in Git config

**HTTPS concerns:**
- PAT tokens are passwords
- If exposed, full account access
- Must be stored somewhere (credential helper or plaintext)
- Token rotation requires updating stored credentials

### 4. Standard Practice
- SSH is the recommended method for regular development
- HTTPS is better for:
  - CI/CD automated systems
  - Scripts running on servers
  - Environments where SSH is blocked
- For personal development: SSH is preferred

## Alternatives Considered

### Alternative 1: HTTPS with PAT Token
- **Pros:** Works in environments where SSH is blocked
- **Cons:**
  - Requires creating PAT on GitHub
  - Must enter token for each operation OR store it (security risk)
  - Token management overhead
  - User already had SSH configured
- **Why rejected:** SSH is simpler when keys already configured

### Alternative 2: HTTPS with Credential Helper
- **Pros:** One-time token entry, stored securely by OS
- **Cons:**
  - Still requires PAT creation
  - Additional setup step
  - Less secure than SSH keys
- **Why rejected:** More complex than using existing SSH keys

### Alternative 3: GitHub CLI (gh auth)
- **Pros:** Modern, integrated authentication
- **Cons:**
  - Additional tool to install
  - Still uses HTTPS under the hood
  - Unnecessary when SSH works
- **Why rejected:** Adds complexity without benefit

## Consequences

### Positive
- ✅ Seamless push/pull operations without password prompts
- ✅ More secure authentication method
- ✅ No PAT token to manage or rotate
- ✅ Standard development practice
- ✅ Works immediately (keys already configured)
- ✅ No credentials stored in Git config

### Negative
- ❌ Requires SSH keys on any new machine (one-time setup)
- ❌ SSH port (22) must be open (usually not an issue)
- ❌ Won't work in environments that block SSH

### Neutral
- Claude Code desktop app uses GitHub API (unaffected by local SSH/HTTPS choice)
- Can still clone public repos via HTTPS
- Can switch back to HTTPS anytime if needed

## Initial Push Resolution

**Problem:** Diverged branch history on first push
```
! [rejected]        main -> main (non-fast-forward)
```

**Cause:**
- Remote had GitHub's initial commit (c965e4e)
- Local had two commits not based on remote
- Git histories had diverged

**Solution:**
```bash
git pull origin main --rebase
git push -u origin main
```

**Result:** All three commits now in proper order:
- c965e4e: Initial commit (GitHub)
- 8dce343: Initial project setup
- abbb707: Add documentation

## Final Configuration

```bash
# Remote URL
git remote -v
# origin  git@github.com:ryanranft/nba-simulator-aws.git (fetch)
# origin  git@github.com:ryanranft/nba-simulator-aws.git (push)

# Branch tracking
git branch -vv
# * main 5e1e039 [origin/main] Update PROGRESS.md

# Repository
# Web: https://github.com/ryanranft/nba-simulator-aws
# SSH: git@github.com:ryanranft/nba-simulator-aws.git
```

## Success Metrics

This decision is successful if:
- ✅ Can push/pull without password prompts
- ✅ No authentication errors
- ✅ SSH connection works reliably
- ✅ No need to manage PAT tokens
- ✅ Git operations are seamless

**Status:** All metrics met ✅

## Setting Up SSH Keys (Reference)

If setting up on a new machine:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Start ssh-agent
eval "$(ssh-agent -s)"

# Add key to ssh-agent
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub
# Copy output

# Add to GitHub:
# 1. Go to github.com/settings/keys
# 2. Click "New SSH key"
# 3. Paste public key
# 4. Save

# Test connection
ssh -T git@github.com
```

## Troubleshooting

### Permission denied (publickey)
```bash
# Check if keys are loaded
ssh-add -l

# If empty, add keys
ssh-add ~/.ssh/id_ed25519

# Test connection
ssh -T git@github.com
```

### Wrong remote URL
```bash
# Check current remote
git remote -v

# Fix if showing HTTPS
git remote set-url origin git@github.com:ryanranft/nba-simulator-aws.git
```

## Review Date

No review needed - configuration is working correctly and will remain stable.

**Re-evaluation triggers:**
- SSH keys need to be rotated
- Moving to new machine (one-time SSH setup)
- Environment blocks SSH (switch to HTTPS temporarily)

## References

- GitHub documentation: SSH authentication
- Git documentation: Remote repositories
- PROGRESS.md: ADR-005 (original detailed version)
- COMMAND_LOG.md: GitHub configuration session logs

## Notes

### Why HTTPS Failed Initially
1. Remote URL was placeholder (YOUR-USERNAME)
2. Even with correct URL, would need PAT
3. PAT creation adds friction
4. SSH keys already configured (simpler path)

### SSH vs HTTPS Decision Tree
```
Do you have SSH keys configured?
├─ Yes → Use SSH ✅
└─ No
   ├─ Personal development → Set up SSH keys
   └─ CI/CD or restricted environment → Use HTTPS with PAT
```

### Claude Code Integration
- Claude Code uses GitHub API (separate authentication)
- Local Git SSH/HTTPS choice doesn't affect Claude Code
- Both can coexist happily

---

**Related ADRs:**
- ADR-004: Git Without GitHub Push (superseded by this ADR)

**Supersedes:**
- ADR-004: GitHub integration deferred (now complete)

**Superseded By:** None
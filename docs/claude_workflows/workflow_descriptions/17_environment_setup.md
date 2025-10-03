## 🔧 Environment Setup & Verification Workflows

### Fresh Environment Setup (12-Step Process)

**Use when setting up new development machine or recovering from system failure**

1. **Install system dependencies** (Homebrew, Xcode tools)
2. **Install Miniconda** (Python environment management)
3. **Install AWS CLI** (v2)
4. **Configure AWS credentials** (`~/.aws/credentials`)
5. **Set up SSH keys** (GitHub authentication)
6. **Clone repository** (via SSH)
7. **Install git hooks** (pre-commit, pre-push, commit template)

   **Script:** `scripts/shell/setup_git_hooks.sh`

   **Purpose:** Automates installation of Git hooks for session history tracking and commit automation

   **Usage:**
   ```bash
   bash scripts/shell/setup_git_hooks.sh
   ```

   **What this installs:**

   #### Hook 1: post-commit (Automatic Session History Logging)

   **Location:** `.git/hooks/post-commit`

   **What it does:**
   - Automatically runs after every `git commit`
   - Executes `session_startup.sh` to capture environment snapshot
   - Appends snapshot to `.session-history.md`
   - Enables correlation of commits with exact software versions

   **Information captured per commit:**
   - Hardware specs (MacBook model, chip, memory)
   - macOS version and build
   - Python version and location
   - Conda environment and package count
   - Git status (branch, recent commits)
   - Timestamp of commit

   **Hook script contents:**
   ```bash
   #!/bin/bash
   # Post-commit hook: Automatically log session snapshot after every commit

   # Change to project root directory
   cd "$(git rev-parse --show-toplevel)"

   # Append session snapshot to .session-history.md
   bash scripts/shell/session_startup.sh >> .session-history.md

   # Silent success
   exit 0
   ```

   **Script output during installation:**
   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   NBA Simulator AWS - Git Hooks Setup
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Project root: /Users/ryanranft/nba-simulator-aws

   Installing Git hooks...

   Installing post-commit hook...
   ✅ post-commit installed successfully

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Summary:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   ✅ Hooks installed: 1

   Installed hooks in .git/hooks:
     post-commit

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   What these hooks do:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   post-commit:
     - Automatically appends environment snapshot to .session-history.md
     - Logs: hardware, Python version, conda env, git status, packages
     - Enables correlation of commits with exact software versions

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Testing:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   To test the post-commit hook:
     1. Make a test commit:
        touch test.txt
        git add test.txt
        git commit -m "Test post-commit hook"

     2. Verify .session-history.md was updated:
        tail -20 .session-history.md

     3. Clean up:
        git rm test.txt
        git commit -m "Remove test file"

   ✓ All hooks installed successfully!
   ```

   **Testing the installation:**
   ```bash
   # 1. Make a test commit
   touch test.txt
   git add test.txt
   git commit -m "Test post-commit hook"

   # 2. Verify .session-history.md was updated
   tail -20 .session-history.md
   # Should show new snapshot with current timestamp

   # 3. Clean up
   git rm test.txt
   git commit -m "Remove test file"
   ```

   **Expected .session-history.md format:**
   ```markdown
   # Session History

   This file is automatically updated by the post-commit hook.

   ---

   ## Session: 2025-10-02 19:30:45

   **Commit:** abc1234 - "Add feature X"

   **Hardware:**
   - Device: MacBook Pro 16-inch, 2023
   - Chip: Apple M2 Max
   - Memory: 96 GB

   **Software:**
   - macOS: 14.6 (23G93)
   - Python: 3.11.9
   - Conda: 24.7.1
   - Environment: nba-aws (127 packages)

   **Git Status:**
   - Branch: main
   - Last 3 commits:
     abc1234 - Add feature X
     def5678 - Update docs
     ghi9012 - Fix bug Y

   ---
   ```

   **Why this is useful:**
   - **Debugging:** "This worked in commit abc123 but broke in def456 - what changed?"
   - **Environment tracking:** Compare exact Python/package versions between commits
   - **Onboarding:** New team members see complete environment evolution
   - **Troubleshooting:** "Code worked on commit X with Python 3.11.8, now fails on 3.11.9"
   - **Audit trail:** Complete record of software versions for compliance

   **What gets logged automatically:**
   - ✅ Every commit triggers post-commit hook
   - ✅ Environment snapshot appended to `.session-history.md`
   - ✅ No manual intervention required
   - ✅ Zero impact on commit speed (<1 second overhead)

   **Hook management commands:**
   ```bash
   # List installed hooks
   ls -lh .git/hooks/

   # View post-commit hook contents
   cat .git/hooks/post-commit

   # Temporarily disable hook (remove execute permission)
   chmod -x .git/hooks/post-commit

   # Re-enable hook
   chmod +x .git/hooks/post-commit

   # Remove hook completely
   rm .git/hooks/post-commit

   # Reinstall all hooks
   bash scripts/shell/setup_git_hooks.sh
   ```

   **Troubleshooting:**

   **Hook not running:**
   ```bash
   # Check if hook is executable
   ls -l .git/hooks/post-commit
   # Should show: -rwxr-xr-x

   # If not executable, make it so
   chmod +x .git/hooks/post-commit
   ```

   **session_startup.sh not found:**
   ```bash
   # Verify script exists
   ls -l scripts/shell/session_startup.sh

   # If missing, check git status
   git status

   # Script should be in repo - restore if needed
   git checkout scripts/shell/session_startup.sh
   ```

   **.session-history.md not updating:**
   ```bash
   # Test hook manually
   bash .git/hooks/post-commit

   # Check for errors in output
   # Verify .session-history.md was modified
   git status
   ```

   **Integration with other workflows:**
   - **Git Commit Workflow Step 4:** Post-commit hook runs automatically after commit
   - **Session Start Workflow:** `session_manager.sh` reads `.session-history.md` to show recent snapshots
   - **Archive Management:** `.session-history.md` archived with each commit
   - **Troubleshooting:** Use `.session-history.md` to correlate issues with environment changes

   **Best practices:**
   1. ✅ Run setup script once during initial environment setup (Step 7)
   2. ✅ Verify hooks installed: `ls .git/hooks/post-commit`
   3. ✅ Test with dummy commit after installation
   4. ✅ Keep `.session-history.md` in `.gitignore` (already configured)
   5. ✅ Archive `.session-history.md` regularly (automatic via archive_manager.sh)
   6. ✅ Review `.session-history.md` when debugging environment issues

   **Future hooks (not yet implemented):**
   The script is designed to easily add more hooks in the future:
   - `pre-commit`: Security scanning, linting, formatting
   - `pre-push`: Run tests, check for TODOs, validate documentation
   - `commit-msg`: Enforce commit message format, add issue tracking links

   To add a new hook, edit `setup_git_hooks.sh` and add a new case in the `create_hook()` function.

8. **Verify .gitignore security settings** (NEW - security hardening)
   ```bash
   bash scripts/shell/verify_gitignore.sh
   ```

   **What this checks:**
   - ✅ `.env$` pattern exists (environment files)
   - ✅ `*.key` pattern exists (private keys)
   - ✅ `*.pem` pattern exists (PEM certificates)
   - ✅ `credentials.yaml` pattern exists (credential files)
   - ✅ `*credentials*` pattern exists (any credential files)
   - ✅ `.aws/` directory pattern exists (AWS config)
   - ✅ `*.log` pattern exists (log files with potential secrets)

   **If verification fails:**
   - Script will show missing patterns
   - Add missing patterns to .gitignore:
     ```bash
     echo "<missing_pattern>" >> .gitignore
     ```
   - Re-run verification until all checks pass
   - Commit updated .gitignore:
     ```bash
     git add .gitignore
     git commit -m "Add missing .gitignore security patterns"
     ```

9. **Create conda environment** (`conda env create -f environment.yml`)
10. **Install Python dependencies** (boto3, pandas, psycopg2, etc.)
11. **Configure .env file** (project-specific settings)
12. **Verify S3 access** (list bucket contents)

**Complete setup instructions:** See `docs/SETUP.md` lines 1-558

### Environment Verification Workflow

**Run whenever environment issues suspected:**

```bash
# Comprehensive verification
make verify-all

# Individual checks
make verify-env    # Conda environment
make verify-aws    # AWS credentials and connectivity
make verify-files  # Check expected files exist
```

**Health check script:**
```bash
source scripts/shell/session_manager.sh start
```

**What it verifies:**
- Hardware specs (model, chip, cores, memory)
- System versions (macOS, Homebrew)
- Conda environment (version, active env, packages)
- Python environment (version, location, key packages)
- AWS CLI (version, credentials)
- Git status (branch, commits, modified files)
- Documentation status (inventory age, stale docs)

**If verification fails:**
1. Check error message for specific issue
2. Consult `TROUBLESHOOTING.md` for common environment issues
3. Re-run specific verification (e.g., `make verify-aws`)
4. If persistent, consider fresh setup (see above)

---


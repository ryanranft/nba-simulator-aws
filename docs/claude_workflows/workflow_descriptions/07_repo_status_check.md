## 📊 Quick Repository Status Check (make git-status)

**Purpose:** Fast overview of repository state combining working tree status and recent commit history

**When to use:**
- Before starting work (see what's uncommitted from last session)
- Before committing (quick status check)
- After pulling from remote (see recent changes)
- During session to check current state
- When context-switching between branches

### Single Command

```bash
make git-status
```

**What this does (2 operations):**

#### 1. Short Git Status
Shows compact view of working tree changes:

```bash
git status --short
```

**Output format:**
```
M  docs/CLAUDE_WORKFLOW_ORDER.md    # Modified file
A  scripts/new_script.sh             # Added file (staged)
?? temp_notes.md                     # Untracked file
D  old_file.md                       # Deleted file
```

**Status codes:**
- `M` = Modified (changes staged or unstaged)
- `A` = Added (new file staged)
- `D` = Deleted (file removed)
- `??` = Untracked (not in git)
- `MM` = Modified in index and working tree (staged + unstaged changes)

#### 2. Recent Commit History
Shows last 5 commits in one-line format:

```bash
git log --oneline -5
```

**Output format:**
```
3b7521c Streamline CLAUDE.md from 436 to 216 lines
029c8f4 Mark workflow consolidation project as complete
83c35f2 Add CLAUDE.md consolidation documentation files
d0badab Implement workflow #3: Automated pre-push inspection
7d73259 Consolidate archive workflows into unified archive_manager.sh
```

### Example Output

```bash
$ make git-status
M  docs/CLAUDE_WORKFLOW_ORDER.md
?? temp_analysis.md

Recent commits:
3b7521c Streamline CLAUDE.md from 436 to 216 lines
029c8f4 Mark workflow consolidation project as complete
83c35f2 Add CLAUDE.md consolidation documentation files
d0badab Implement workflow #3: Automated pre-push inspection
7d73259 Consolidate archive workflows into unified archive_manager.sh
```

**Interpretation:**
- 1 modified file ready to stage/commit
- 1 untracked file (needs `git add` or can ignore)
- Recent work shows workflow documentation improvements

### Integration with Other Workflows

**Before Git Commit:**
```bash
# 1. Quick status check
make git-status

# 2. Review what changed
git diff docs/CLAUDE_WORKFLOW_ORDER.md

# 3. Proceed with commit workflow
git add docs/CLAUDE_WORKFLOW_ORDER.md
git commit -m "Add make git-status workflow documentation"
```

**After Session Work:**
```bash
# 1. Check what you worked on
make git-status

# 2. Review changes
git diff

# 3. Run session end checklist
bash scripts/shell/session_end.sh
```

**Before Context Switch:**
```bash
# Check if current work is committed
make git-status

# If uncommitted:
# - Either commit: git add . && git commit -m "WIP: description"
# - Or stash: git stash save "description"
```

### Comparison to Full git status

| Command | Output Length | Shows Untracked? | Shows Recent Commits? | Use Case |
|---------|---------------|------------------|----------------------|----------|
| `git status` | Verbose (15+ lines) | ✅ YES (detailed) | ❌ NO | Full details needed |
| `git status --short` | Compact (1 line per file) | ✅ YES (minimal) | ❌ NO | Quick file list |
| `make git-status` | Compact + history | ✅ YES (minimal) | ✅ YES (last 5) | **Quick overview** |
| `git log --oneline` | Commit history only | ❌ NO | ✅ YES | Review history |

### Best Practices

**Use `make git-status` when:**
- ✅ Want quick overview without verbose output
- ✅ Need both current state AND recent history
- ✅ Starting work session (see what's uncommitted)
- ✅ Ending work session (verify everything committed)
- ✅ Context-switching between features/bugs

**Use full `git status` when:**
- ✅ Need detailed explanations (branch status, upstream tracking)
- ✅ Want git's helpful suggestions (how to unstage, discard changes)
- ✅ First time using git in a project
- ✅ Debugging git issues (detached HEAD, merge conflicts)

### Troubleshooting

**Problem: Shows files you expected to be committed**
```bash
# Solution: Commit them
git add <files>
git commit -m "description"

# Verify clean
make git-status  # Should show nothing
```

**Problem: Shows untracked files you want to ignore**
```bash
# Solution: Add to .gitignore
echo "temp_notes.md" >> .gitignore
git add .gitignore
git commit -m "Add temp files to gitignore"
```

**Problem: Shows modified files you didn't change**
```bash
# Solution: Check line endings or permissions
git diff <file>  # See what changed

# If just whitespace/line endings:
git config core.autocrlf true  # Fix line endings
```

**Problem: No recent commits shown**
```bash
# Solution: This is a new repository or orphan branch
git log --all --oneline -5  # Check all branches
```

### Alternative: Manual Commands

If you prefer not to use Makefile:

```bash
# Show short status
git status --short

# Show recent commits
git log --oneline -5

# Show both with separator
git status --short && echo "" && echo "Recent commits:" && git log --oneline -5
```

### Shell Alias (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Quick git status + recent commits
alias gst='git status --short && echo "" && echo "Recent commits:" && git log --oneline -5'
```

Then use:
```bash
gst  # Same as make git-status
```

---


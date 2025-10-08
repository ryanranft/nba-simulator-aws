# Context Management Guide for Claude Code

**Last Updated:** October 8, 2025
**Purpose:** Strategies for extending Claude Code session length and optimizing token usage

---

## Why Context Management Matters

**Claude Code token limit:** 200,000 tokens per session
- **Comfortable working range:** 0-40,000 tokens (0-20%)
- **Monitoring range:** 40,000-150,000 tokens (20-75%)
- **Auto-compact warning:** 150,000-180,000 tokens (75-90%)
- **Critical range:** 180,000-200,000 tokens (90-100%)

**Average file size impact:**
- 1,000 lines ≈ 4,000-5,000 tokens
- Reading 5 large files (1,000 lines each) = 20,000-25,000 tokens (10-12% context)

---

## Context-Efficient Reading Strategy

### Always Read (Session Start) - Tier 1
**Total: ~1,085 lines (5% context)**

1. **CLAUDE.md** (300 lines) - Core instructions
2. **PROGRESS.md** (685 lines) - Current project state
3. **docs/README.md** (100 lines) - Documentation index

### Read When Needed (Task-Specific) - Tier 2
**Total: +900-1,000 lines per task**

- Specific phase file for current work (~400-500 lines)
- Referenced workflows for current sub-phase (~300 lines each)
- CLAUDE_OPERATIONAL_GUIDE.md (~200 lines) - only if doing session management

### Search First, Read Selectively (Reference Only) - Tier 3

- **TROUBLESHOOTING.md** - Use grep to find error, read that section only
- **Large guides (>500 lines)** - Read specific sections, not entire file
- **QUICKSTART.md** - Only when user asks "what's the command for X?"

### Never Read Unless Explicitly Requested - Tier 4

- **LESSONS_LEARNED.md** (1,002 lines) - Historical context only
- **TEMPORAL_QUERY_GUIDE.md** (996 lines) - Implementation reference (read sections)
- **TESTING.md** (862 lines) - Read when writing tests
- **STYLE_GUIDE.md** (846 lines) - Read when style question arises

---

## Example Session Context Usage

### Inefficient Approach (Old Way)
**❌ Total: 22,745 lines ≈ 90,000-114,000 tokens (45-57% context)**

- Read all of PROGRESS.md: 9,533 lines (old version)
- Read all workflows at once: 13,212 lines (36 workflows)
- Read multiple large guides "just in case"

### Efficient Approach (New Way)
**✅ Total: 1,721-2,021 lines ≈ 6,900-8,100 tokens (3-4% context)**

- Read CLAUDE.md: 300 lines
- Read PROGRESS.md: 685 lines
- Read docs/README.md: 100 lines
- Read relevant phase file: 450 lines
- Read 2 relevant workflows: 600 lines

**Context savings: 91-92%**

---

## Modular Documentation System Benefits

### Old PROGRESS.md (Before Oct 2, 2025)
- **Size:** 9,533 lines (massive context usage)
- **Problem:** All phase details in one file
- **Impact:** Must read entire file to find current task

### New System (After Oct 2, 2025)
- **PROGRESS.md:** 685 lines (lightweight index)
- **Phase files:** 300-500 lines each (read only what's needed)
- **Workflow files:** 200-400 lines each (reference when mentioned)

**Benefits:**
- ✅ Read only what you need (72% reduction in PROGRESS.md size)
- ✅ Faster file operations (685 lines vs 9,533)
- ✅ Reduced context usage (90%+ savings)
- ✅ Easier maintenance (update one phase without affecting others)

---

## File Reading Efficiency Metrics

### Context Budget Planning

| Session Type | Files Read | Lines | Token Est. | % Context |
|--------------|-----------|-------|------------|-----------|
| **Minimal** (orientation only) | CLAUDE.md + PROGRESS.md + README | 1,085 | ~4,300 | 2% |
| **Light work** (1 task) | + 1 phase + 1 workflow | 1,985 | ~7,900 | 4% |
| **Moderate work** (multiple tasks) | + 1 phase + 3 workflows | 2,585 | ~10,300 | 5% |
| **Heavy work** (complex task) | + 2 phases + 3 workflows | 3,485 | ~13,900 | 7% |
| **Maximum recommended** | Stay under this limit | 4,000 | ~16,000 | 8% |

**Target:** Keep session start under 8% context (16,000 tokens) to leave room for work

---

## Reading Protocol Rules

### Do Read
- ✅ Files directly relevant to current task
- ✅ Workflows referenced in current phase file
- ✅ Error documentation when debugging specific error

### Don't Read
- ❌ Files "just in case" they're useful
- ❌ All phase files when working on one
- ❌ All workflows upfront
- ❌ Large guides (>500 lines) without specific need
- ❌ Files you already read in this session

---

## Common Pitfalls to Avoid

### Context Management Mistakes

**❌ Reading all 8 phase files when user wants to work on Phase 4**
- Impact: 3,200+ lines = 12,800+ tokens (6% context wasted)
- ✅ Solution: Only read PHASE_4 file

**❌ Reading workflows 1-38 at session start "just in case"**
- Impact: 7,600-15,200 lines = 30,400-60,800 tokens (15-30% context!)
- ✅ Solution: Read workflows only when referenced in current sub-phase

**❌ Re-reading files you already read in this session**
- Impact: Doubles context usage unnecessarily
- ✅ Solution: Keep track of what you've read, don't re-read

**❌ Reading TROUBLESHOOTING.md (1,025 lines) to find one error**
- Impact: 4,100 tokens for one answer
- ✅ Solution: `grep -i "error keyword" docs/TROUBLESHOOTING.md`, read matching section only

---

## Decision Tree for File Reading

### User says "let's work on [task]"
1. Is it a new session? → Run `session_manager.sh start` first
2. Read PROGRESS.md → Find which phase contains this task
3. Read **only** that specific phase file
4. Check for workflow recommendations in phase file
5. Execute task following phase file + workflows
6. Update PROGRESS.md status when phase/sub-phase completes

### User says "continue where we left off"
1. Run `session_manager.sh start`
2. Read PROGRESS.md → Find first 🔄 IN PROGRESS or ⏸️ PENDING phase
3. Read **only** that phase file
4. Ask user what they completed since last session
5. Update status accordingly
6. Suggest next sub-phase to work on

### User says "start Phase X"
1. Read `docs/phases/PHASE_X_NAME.md` completely
2. Check for "⚠️ IMPORTANT" note at top
3. If present, ask: "Should I add any workflows to this phase before beginning?"
4. Wait for approval before proceeding
5. Follow phase file instructions step by step

---

## When to Read Multiple Files

### ✅ Safe to Run Simultaneously
- User explicitly asks to review all phases
- Working on cross-phase documentation updates
- Creating new workflows that span multiple phases

### ⚠️ Avoid Unless Necessary
- Reading multiple large files (>500 lines) at once
- Reading all workflows before starting task
- Reading reference documentation without specific need

---

## Workflow Integration with Context Management

### Navigation Pattern (Optimized for Low Context Usage)

```
1. Read PROGRESS.md (685 lines) - Identify current task/phase
   ↓
2. Read docs/README.md (100 lines) - Find documentation location
   ↓
3. Read specific phase file (400-500 lines) - Get detailed steps
   ↓
4. Read workflows referenced in current sub-phase ONLY (200-400 lines each)
   ↓
5. Execute workflow steps
   ↓
6. Update PROGRESS.md status when complete
```

**Total context for typical task:** 1,385-1,985 lines ≈ 5,500-7,900 tokens (3-4% context)

---

## PROGRESS.md Update Protocol

### When to Update PROGRESS.md
- ✅ When completing a sub-phase (update status from ⏸️ to ✅)
- ✅ When starting a new phase (update status from ⏸️ to 🔄)
- ✅ At session end (update "Current Session Context")
- ❌ Don't update for minor tasks or intermediate steps

### What to Update in PROGRESS.md
1. Phase/sub-phase status emoji (⏸️ → 🔄 → ✅)
2. "Started" and "Completed" dates in phase summary
3. "Current Session Context" section
4. Link to newly created phase file (if applicable)

### What NOT to Update in PROGRESS.md
- ❌ Detailed implementation steps (those belong in phase files)
- ❌ Workflow procedures (those belong in workflow files)
- ❌ Command outputs (those belong in COMMAND_LOG.md)

---

## File Size Reference Table

**Know before you read:**

| File | Lines | Context Impact | When to Read |
|------|-------|----------------|--------------|
| CLAUDE.md | ~300 | Low (1%) | Every session start |
| PROGRESS.md | ~685 | Low (2-3%) | Every session start |
| docs/README.md | ~100 | Minimal (<1%) | Every session start |
| Phase files | ~400-500 | Low (2%) | Working on that phase |
| Workflow files | ~200-400 | Low (1-2%) | Referenced in phase |
| TROUBLESHOOTING.md | 1,025 | High (5%) | Grep only, read sections |
| LESSONS_LEARNED.md | 1,002 | High (5%) | Only when requested |
| TEMPORAL_QUERY_GUIDE.md | 996 | High (4-5%) | Only when implementing |
| TESTING.md | 862 | Medium (3-4%) | Only when writing tests |
| STYLE_GUIDE.md | 846 | Medium (3-4%) | Only when style question |

---

## Session Commit Strategy

### Commit at 75% Context (150,000 tokens)
**Why:** Leaves comfortable room (50,000 tokens) for:
- Commit message drafting
- PROGRESS.md updates
- Session end procedures
- Unexpected file reads

**Auto-save triggers:**
- Conversation auto-saves at 75% context
- Proactive commit recommendation appears
- CHAT_LOG.md automatically archived

### Don't Wait Until 90% Context
**Why 90% is risky:**
- Only 20,000 tokens (5,000 lines) left
- May not have room for git operations
- Risk of hitting 100% mid-commit
- Stressful session end

---

## Break Large Tasks into Multiple Sessions

### Single Large Session (Inefficient)
**❌ Problem:** Trying to implement entire phase in one session
- Read 8 phase files = 3,200 lines
- Read 12 workflows = 2,400-4,800 lines
- Implement code, test, document
- **Risk:** Hit 90% context before completion

### Multiple Focused Sessions (Efficient)
**✅ Solution:** Break into 3-4 smaller sessions
- **Session 1:** Plan and setup (read 1 phase, 2 workflows, setup environment)
- **Session 2:** Implement core functionality (read 1 workflow, write code)
- **Session 3:** Testing and debugging (read testing workflow, run tests)
- **Session 4:** Documentation and cleanup (update docs, commit)

**Each session:** Stay under 4,000 lines (16,000 tokens, 8% context)

---

## Grep Instead of Reading

### ❌ Inefficient: Read Entire File
```bash
# Claude reads TROUBLESHOOTING.md (1,025 lines = 4,100 tokens)
# Searches for error
# Uses 5% context for one answer
```

### ✅ Efficient: Grep First
```bash
# Claude runs: grep -i "error keyword" docs/TROUBLESHOOTING.md
# Reads only the 10-20 line matching section
# Uses <1% context for same answer
```

**Files to grep, not read:**
- TROUBLESHOOTING.md
- LESSONS_LEARNED.md
- Large guides (>500 lines)

---

## Leverage Existing Workflows

### ❌ Inefficient: Re-explain Procedures
**Claude types out:**
- How to commit (security scan, message format, etc.) - 200 tokens
- How to push (pre-push inspection, user approval) - 150 tokens
- How to update PROGRESS.md - 100 tokens
- **Total:** 450 tokens per task

### ✅ Efficient: Reference Workflows
**Claude says:**
- "Following Workflow #3 (Git Commit Protocol)" - 10 tokens
- "Following Workflow #4 (Git Push Protocol)" - 10 tokens
- "Updating PROGRESS.md per Workflow #14" - 10 tokens
- **Total:** 30 tokens per task

**Savings:** 93% reduction by referencing vs re-explaining

---

## Quick Reference Card

**Copy this mental checklist at session start:**

```
Session context checklist:
[ ] Read CLAUDE.md ✓ (300 lines)
[ ] Read PROGRESS.md ✓ (685 lines)
[ ] Read docs/README.md ✓ (100 lines)
[ ] Total so far: 1,085 lines (4,300 tokens, 2% context)
[ ] Asked user what they completed
[ ] Updated "Current Session Context"
[ ] Asked user what they want to work on
[ ] Read ONLY relevant phase file (not all phases)
[ ] Checked for workflow recommendations
[ ] Ready to begin work under 4,000 line budget
```

---

## Emergency Recovery

**If context usage approaching 90%:**

1. **Stop immediately** - Don't read more files
2. **Commit current work** - Save progress
3. **End session** - Follow Workflow #14
4. **Start fresh session** - 0% context, continue work

**If lost context mid-session:**

1. Stop immediately
2. Re-read PROGRESS.md "Current Session Context" (only this section)
3. Ask user: "Where were we? What's the current state?"
4. Resume from known-good checkpoint

---

*For additional strategies, see CLAUDE.md navigation sections and docs/DOCUMENTATION_SYSTEM.md*

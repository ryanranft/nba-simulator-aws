## 📝 File Creation/Modification Workflow

**CRITICAL: Follow this sequence when creating or editing files**

### 1. Create/Edit Files
Write the code or documentation

### 2. Run File Inventory (AUTOMATIC - Don't Ask)
```bash
make inventory
```
This updates FILE_INVENTORY.md with new/changed files

### 3. Document Changes in COMMAND_LOG.md
**Format:**
```markdown
## [Timestamp] File Change: [Brief Description]

**Files Created/Modified:**
- `path/to/file.py` - Purpose: [What and why]

**Problem Solved:**
[Error message or requirement being addressed]

**Outcome:**
- ✅ Success / ❌ Failed
- [Details about what worked/didn't]
```

### 4. Review Git Status
```bash
git status
```
Verify what files changed

### 5. Proceed to Git Commit Workflow (see below)

---


## 🧪 Error Handling Workflow

**When any command fails:**

### 1. Stop Immediately
Don't attempt multiple fixes automatically

### 2. Check TROUBLESHOOTING.md
Look for known solution

### 3. If Unknown Error
- Show error to user
- Ask for guidance: "This error isn't documented. How would you like to proceed?"

### 4. After Resolving Error
- Document solution in COMMAND_LOG.md
- Ask: "Should I add this solution to TROUBLESHOOTING.md?" (if meets criteria)
- Use `log_solution` helper function if applicable

### 5. Update PROGRESS.md
- Document error details
- Update time estimates if impacted
- Mark task status appropriately

---


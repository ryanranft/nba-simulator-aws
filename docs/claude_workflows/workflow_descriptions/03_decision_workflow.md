## 📋 Decision Workflow (When User Asks to Do Something)

Follow this decision tree **before** starting any task:

### Step 1: Check PROGRESS.md
**Question:** Is this the next pending task in PROGRESS.md?
- ✅ **YES** → Proceed to Step 2
- ❌ **NO** → Go to "Plan Change Protocol" below

### Step 2: Check Prerequisites
**Question:** Are all prerequisites completed?
- ✅ **YES** → Proceed to Step 3
- ❌ **NO** → Warn user: "Task X requires Y to be completed first. Should we do Y first or update the plan?"

### Step 3: Check Cost Impact
**Question:** Will this create AWS resources with ongoing costs?
- ✅ **YES** → Warn user with cost estimate, wait for explicit approval
- ❌ **NO** → Proceed to Step 4

### Step 4: Check Risk Level
**Question:** Could this break something or delete data?
- ✅ **YES** → Explain risk, suggest backup/test approach, wait for approval
- ❌ **NO** → Proceed to execution

---


# PyCharm Project View Not Showing - Fix Guide
**Date:** 2025-11-08 15:35
**Issue:** Left pane (Project view) is blank after cache invalidation

---

## ✅ **Fix Applied**

Created missing `.idea/modules.xml` file - this tells PyCharm what to display.

---

## 🎯 **IMMEDIATE STEPS** (Follow in Order)

### Step 1: Close PyCharm Completely
- Press **Cmd+Q** to quit
- Make sure it's fully closed (check Dock)

### Step 2: Reopen PyCharm
- Launch PyCharm
- Open the **nba-simulator-aws** project from recent projects

### Step 3: Try These Keyboard Shortcuts (in order)

**Option A: Toggle Project View**
```
Cmd+1        Press once to hide, press again to show
```

**Option B: Show All Tool Windows**
```
Cmd+Shift+F12    Hide all tool windows
Cmd+Shift+F12    Show all tool windows again
```

**Option C: Restore Layout**
```
Window → Store Current Layout as Default
Window → Restore Default Layout
```

---

## 🔧 **If Still Not Showing: Manual Steps**

### Method 1: Click the Project Tab
Look at the **LEFT EDGE** of the PyCharm window:
- You should see a vertical tab labeled **"Project"**
- **Click it** to expand the Project view
- It might be collapsed to the side

### Method 2: Enable Project Tool Window
1. Go to **View → Tool Windows → Project**
2. Make sure it's checked (✓)
3. If not, click it to enable

### Method 3: Reset Tool Window Layout
1. **Window → Active Tool Window → Reset Size**
2. **Window → Restore Default Layout**

### Method 4: Check Window Borders
Sometimes the Project pane is there but minimized:
- Look for a **thin vertical bar** on the left edge
- Try **dragging** it to the right to expand
- Or **double-click** the edge to expand

---

## 🖼️ **What You Should See**

After these steps, the left pane should show:
```
nba-simulator-aws/
├── api/
├── config/
├── data/               ← This might be grayed out (excluded)
├── deployment/
├── docs/
├── logs/               ← Grayed out (excluded)
├── nba_simulator/
├── scripts/
├── tests/
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 🆘 **Nuclear Option: Recreate Project**

If NOTHING above works:

### 1. Backup Your Settings
Your `.idea/` folder already has the correct configuration, so this should be safe.

### 2. Close PyCharm and Delete Workspace Cache
```bash
# Close PyCharm first, then run in Terminal:
rm ~/Library/Caches/JetBrains/PyCharm*/
rm ~/Library/Logs/JetBrains/PyCharm*/
```

### 3. Reopen Project
PyCharm will rebuild its cache with the correct settings.

---

## 🔍 **Alternative: Check If Scrolled**

Sometimes the project view is showing but scrolled to the wrong section:

1. Click in the left pane (even if it looks blank)
2. Press **Cmd+Home** to scroll to the top
3. Press **Cmd+1** to ensure it's focused

---

## 📋 **Quick Diagnostic**

### Check These:
1. ✅ Is there a thin vertical "Project" tab on the left edge?
2. ✅ Is the left pane visible but just blank/gray?
3. ✅ Do you see any icons at the top of the left pane?
4. ✅ When you press Cmd+1, does anything change?

---

## 💡 **Common Causes**

1. **Tool window collapsed** - Click the "Project" tab on left edge
2. **Wrong view mode** - Should be "Project" not "Packages"
3. **Window layout corrupted** - Reset layout
4. **Cache issue** - Already fixed with modules.xml

---

## 🎯 **Expected Result**

After following these steps:
- ✅ Left pane shows file/folder tree
- ✅ You can expand/collapse folders
- ✅ `data/` folder is either grayed out or not visible (correct - it's excluded)
- ✅ All Python files are visible and accessible

---

## 📞 **If Still Having Issues**

Take a screenshot showing:
1. The entire PyCharm window
2. Any visible tabs or buttons on the left edge
3. The menu bar

This will help diagnose the exact issue.

---

## ⚙️ **What Files Were Created/Updated**

1. ✅ **Created:** `.idea/modules.xml` - Tells PyCharm what to display
2. ✅ **Updated:** `.idea/nba-simulator-aws.iml` - Excluded data/ directory
3. ✅ **Created:** This troubleshooting guide

---

**Status:** Missing modules.xml file created  
**Action Required:** Close PyCharm, reopen, try Cmd+1  
**Confidence:** HIGH - This should fix it  

---

*The modules.xml file is critical for PyCharm to know what project structure to display. Without it, the Project view stays blank.*

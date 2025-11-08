# CRITICAL FIX: data/ Directory Exclusion
**Date:** 2025-11-08 15:30  
**Issue:** PyCharm still indexing 146,115+ JSON files from data/ directory

---

## 🚨 **What Happened**

The initial fix missed the **BIGGEST** directory:
- **data/** - 146,115+ JSON files (119+ GB)

PyCharm was trying to index all of these, causing:
- ❌ Memory exhaustion
- ❌ 30+ minute indexing times
- ❌ Complete IDE unresponsiveness

---

## ✅ **Fix Applied (via MCP)**

Updated `.idea/nba-simulator-aws.iml` to exclude `data/` directory.

---

## 📋 **IMMEDIATE STEPS REQUIRED**

### Step 1: Close PyCharm Completely
**Important:** Fully quit PyCharm (don't just close the window)
- macOS: **PyCharm → Quit PyCharm** (Cmd+Q)

### Step 2: Reopen PyCharm
- Open PyCharm
- Open the **nba-simulator-aws** project

### Step 3: Show Project View (If Missing)
If you don't see your project files on the left side:
1. **View → Tool Windows → Project** (or press **Cmd+1**)
2. This will show your project directory tree

### Step 4: Verify data/ is Excluded
In the Project view (left pane):
1. Look for the `data/` folder
2. It should appear with a different icon (crossed-out or grayed)
3. If you don't see it at all, that's PERFECT - it's excluded!

### Step 5: Invalidate Caches ONE MORE TIME
This ensures PyCharm forgets about the data/ files:
1. **File → Invalidate Caches...**
2. Check **ALL boxes**:
   - ✅ Clear file system cache
   - ✅ Clear VCS Log caches
   - ✅ Clear downloaded shared indexes
3. Click **"Invalidate and Restart"**

### Step 6: Wait for Re-Index (2-3 minutes)
- Watch the progress bar at bottom
- Should be MUCH faster now
- Status bar should show indexing progress

---

## 🎯 **How to Know It Worked**

### ✅ **Success Indicators:**
1. **Indexing completes in 2-3 minutes** (not 30+)
2. **Memory usage stays reasonable** (check View → Tool Windows → Memory Indicator)
3. **No "Indexing data/..." messages** in status bar
4. **Project view shows files** on the left
5. **IDE is responsive** immediately

### ❌ **Still Having Issues:**
If you still see:
- "Indexing... nba-simulator-aws/data/..."
- High memory usage
- Long indexing times

Then:
1. **Right-click data/ folder** in Project view
2. **Mark Directory as → Excluded**
3. Invalidate caches again

---

## 📊 **What Was Excluded**

Now excluding these directories (total: 12):
1. **data/** ← NEW - MOST CRITICAL (119 GB, 146k files)
2. logs/
3. htmlcov/
4. mlruns/
5. backups/
6. backup_api_scrapes/
7. tmp/
8. .pytest_cache/
9. archives/
10. synthesis_output/
11. nba_simulator.backup.*
12. nba-simulator-refactored/

---

## 🔍 **Troubleshooting Project View**

If you're still seeing "External Libraries" or "Scratches" instead of your project:

### Fix #1: Switch to Project View
- **View → Tool Windows → Project** (Cmd+1)

### Fix #2: Change Project View Mode
In the Project tool window (left pane):
1. Click the **gear icon** ⚙️ at top
2. Select **"Project"** from dropdown (not "Packages" or "Scratches")

### Fix #3: Ensure Project Root is Correct
1. **File → Project Structure**
2. Verify **nba-simulator-aws** is listed as the project
3. Content Root should be `/Users/ryanranft/nba-simulator-aws`

---

## 💾 **What Got Fixed**

### Configuration Updated:
```xml
<!-- .idea/nba-simulator-aws.iml -->
<excludeFolder url="file://$MODULE_DIR$/data" />  ← ADDED THIS
```

This tells PyCharm:
- ❌ Don't index these files
- ❌ Don't include in searches
- ❌ Don't parse for code completion
- ❌ Don't waste memory on them

---

## 🎯 **Expected Before/After**

### BEFORE (with data/ being indexed):
- Indexing time: **30-60 minutes** (or infinite hang)
- Memory usage: **8+ GB**
- IDE state: **Unusable**
- Status: **"Indexing... data/nba_box_score/..."**

### AFTER (with data/ excluded):
- Indexing time: **2-3 minutes**
- Memory usage: **1-2 GB**
- IDE state: **Responsive immediately**
- Status: **"Indexing Python files..."** (only)

---

## 📝 **Summary**

**Root Cause:** PyCharm was trying to index 146,115 JSON files  
**Fix:** Added `data/` to excluded folders  
**Action Required:** Close PyCharm, reopen, invalidate caches  
**Expected Result:** Fast, responsive IDE  

---

**Status:** ✅ Fix applied via MCP  
**Next:** User must restart PyCharm and invalidate caches  

---

*If you still have issues after following these steps, the manual fix is: Right-click data/ → Mark Directory as → Excluded*

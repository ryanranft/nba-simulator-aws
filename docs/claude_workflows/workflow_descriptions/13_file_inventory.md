## 📋 Generate File Inventory Workflow (make inventory)

**Purpose:** Automatically generate comprehensive FILE_INVENTORY.md with metadata and summaries of all project files

**Script:** `scripts/maintenance/generate_inventory.py` (called by `make inventory`)

**When to run:**
- After adding new scripts or documentation files
- FILE_INVENTORY.md is >7 days old (checked by `session_end.sh`)
- After major refactoring or file reorganization
- Monthly as part of documentation maintenance
- Before sharing project structure with collaborators

### Single Command

```bash
make inventory
```

**Equivalent direct call:**
```bash
python scripts/maintenance/generate_inventory.py
```

### What This Does

**4-step automated process:**

#### Step 1: Scan Project Files

Searches for all files matching these patterns:
- `scripts/**/*.py` - All Python scripts
- `scripts/**/*.sh` - All shell scripts
- `sql/**/*.sql` - SQL migration/query scripts
- `docs/**/*.md` - Documentation files
- `*.md` - Root markdown files (README, PROGRESS, etc.)
- `Makefile` - Build automation
- `.env.example` - Configuration template

**Excludes:**
- `__pycache__/` - Python cache
- `.git/` - Git metadata
- `data/` - Raw data files (too large)
- `.idea/` - IDE settings
- `backups/` - Backup directories

#### Step 2: Extract File Metadata

For each file, extracts:

**Basic metadata:**
- Relative path from project root
- File type (Python script, Bash script, etc.)
- Last modified date
- Line count
- File size

**Content analysis:**
- **Purpose** - Extracted from docstrings/comments
  - Python: Module-level `"""docstring"""`
  - Shell: First `# comment` after shebang
  - Markdown: First non-heading line
  - SQL: First `-- comment` line

- **Key Functions/Classes** - Parsed from code
  - Python: `def function_name()` and `class ClassName`
  - Bash: `function_name() { ... }`
  - Limits to top 8 functions/classes

- **Dependencies** - Identified imports
  - Python: `import` and `from` statements (external packages only)
  - Shell: Detects AWS CLI, psql, conda, git usage

- **Usage Example** - How to run the script
  - Python: Extracted from usage comments or inferred from `__main__`
  - Shell: Extracted from "Usage:" comment or inferred

#### Step 3: Organize by Category

Groups files into 9 categories:

1. **Root Documentation** - README.md, PROGRESS.md, QUICKSTART.md, etc.
2. **Scripts - AWS** - `scripts/aws/*.sh` (cost checking, resource management)
3. **Scripts - Shell Utilities** - `scripts/shell/*.sh` (session management, git hooks)
4. **Scripts - ETL** - `scripts/etl/*.{py,sh}` (data extraction, Glue jobs)
5. **Scripts - Maintenance** - `scripts/maintenance/*.{py,sh}` (archiving, inventory)
6. **Documentation** - `docs/*.md` (detailed guides, protocols)
7. **Architecture Decision Records** - `docs/adr/*.md` (numbered ADRs)
8. **SQL Scripts** - `sql/*.sql` (schema, migrations)
9. **Configuration** - Makefile, .env.example, etc.

#### Step 4: Generate Markdown Output

Creates `FILE_INVENTORY.md` with:

**File listings** for each category:
```markdown
### scripts/maintenance/generate_inventory.py

**Type:** Python script (341 lines)
**Last Modified:** 2025-10-02
**Purpose:** Automatically generate FILE_INVENTORY.md with summaries of all project files.

**Key Functions:**
- `get_file_info()`
- `extract_purpose()`
- `extract_functions()`
- `extract_dependencies()`
- `scan_project()`

**Dependencies:** subprocess

**Usage:** `python scripts/maintenance/generate_inventory.py`
```

**Summary statistics** at end:
```markdown
## Summary Statistics

**Total files documented:** 87
**Total lines of code/docs:** 45,231

**Files by type:**
- Python script: 23
- Bash script: 19
- Markdown documentation: 32
- SQL script: 8
- YAML configuration: 5
```

### Example Output

```bash
$ make inventory
🔍 Scanning project files...
   Found 87 files to document

📝 Generating inventory...

💾 Writing to /Users/ryanranft/nba-simulator-aws/FILE_INVENTORY.md...

✅ FILE_INVENTORY.md generated successfully!
   Total files: 87
   Location: /Users/ryanranft/nba-simulator-aws/FILE_INVENTORY.md
```

### Integration with Other Workflows

**After adding new scripts:**
```bash
# 1. Create new script
vim scripts/etl/new_extraction_script.py

# 2. Add docstring explaining purpose
# 3. Commit changes
git add scripts/etl/new_extraction_script.py
git commit -m "Add new extraction script for team rosters"

# 4. Update inventory
make inventory

# 5. Commit updated inventory
git add FILE_INVENTORY.md
git commit -m "Update inventory with new script"
```

**Session end workflow integration:**
```bash
# Session end checklist checks if FILE_INVENTORY.md is stale
bash scripts/shell/session_end.sh

# If >7 days old:
# ⚠️  FILE_INVENTORY.md is 9 days old (consider: make inventory)

# Update it:
make inventory
```

**Monthly maintenance:**
```bash
# First Monday of month
make inventory                # Refresh all metadata
git add FILE_INVENTORY.md
git commit -m "Monthly inventory refresh"
```

### File Inventory Use Cases

**1. Onboarding New Developers**
```bash
# New developer joins project
cat FILE_INVENTORY.md    # Quick overview of all files
```

**2. Finding Right Script**
```bash
# Search inventory for specific functionality
grep -i "cost" FILE_INVENTORY.md
# Finds: check_costs.sh - AWS cost reporting workflow
```

**3. Documentation Completeness Check**
```bash
# Find scripts without purpose documentation
grep "No description available" FILE_INVENTORY.md
# Returns scripts missing docstrings/comments
```

**4. Dependency Audit**
```bash
# Check which scripts use specific tools
grep -A 1 "Dependencies:" FILE_INVENTORY.md | grep "AWS CLI"
# Lists all scripts requiring AWS CLI
```

**5. Code Quality Review**
```bash
# Find large scripts that may need refactoring
grep "Python script" FILE_INVENTORY.md | grep -E "[0-9]{3,} lines"
# Finds Python scripts >100 lines
```

### Comparison to Manual Documentation

| Approach | Time Required | Accuracy | Maintenance | Use Case |
|----------|---------------|----------|-------------|----------|
| **Manual FILE_INVENTORY.md** | 2-3 hours initially | 📉 Degrades over time | ⚠️ Requires discipline | Legacy projects |
| **make inventory** | <10 seconds | ✅ Always current | ✅ Single command | **Active development** |
| **No inventory** | 0 seconds | ❌ N/A | ❌ N/A | Small projects |
| **README only** | 30 minutes | 📉 High-level only | ⚠️ Manual | Simple projects |

### Best Practices

**Update inventory when:**
- ✅ Adding 3+ new files in one session
- ✅ Renaming or reorganizing file structure
- ✅ FILE_INVENTORY.md is >7 days old (per session_end.sh)
- ✅ Before monthly documentation review
- ✅ Before creating pull request (ensure inventory current)

**Don't worry about updating if:**
- ✅ Only editing existing file contents (no new files)
- ✅ Just updated yesterday (<24 hours)
- ✅ Only changed data files (excluded from inventory)

### Troubleshooting

**Problem: "No such file or directory" error**
```bash
# Cause: Running from wrong directory
# Solution: Must run from project root
cd /Users/ryanranft/nba-simulator-aws
make inventory
```

**Problem: "No module named 'X'" error**
```bash
# Cause: Script depends on external Python package
# Solution: Activate conda environment first
conda activate nba-aws
make inventory
```

**Problem: FILE_INVENTORY.md missing expected files**
```bash
# Cause: Files in excluded directories or patterns
# Solution: Check script's exclude_patterns list (lines 202-208)
# Excluded: __pycache__, .git, data/, .idea, backups

# If file should be included, move out of excluded directory
```

**Problem: Purpose shows "No description available"**
```bash
# Cause: Script missing docstring/header comment
# Solution: Add documentation to script

# For Python scripts:
"""
Purpose: One-line description of what this script does
"""

# For shell scripts:
# Purpose: One-line description of what this script does
```

**Problem: Inventory shows stale "Last Modified" dates**
```bash
# Cause: FILE_INVENTORY.md not regenerated after file changes
# Solution: Run make inventory (it's fast!)
make inventory
```

### Alternative: Manual Execution

If Makefile not available:

```bash
# Direct Python execution
cd /Users/ryanranft/nba-simulator-aws
python scripts/maintenance/generate_inventory.py
```

**With virtual environment:**
```bash
conda activate nba-aws
python scripts/maintenance/generate_inventory.py
```

### Technical Details

**Performance:**
- Scans ~87 files in <10 seconds
- Uses parallel file reading (async I/O)
- Memory efficient (processes one file at a time)

**Output format:**
- GitHub-flavored Markdown
- UTF-8 encoded
- Consistent heading structure (searchable)
- Auto-generated timestamp at top

**Limitations:**
- Python/Bash-centric (other languages need custom parsers)
- Docstring extraction uses regex (may miss complex formats)
- Function count limited to 8 per file (prevents clutter)
- Dependency detection is heuristic (not AST-based)

**Future enhancements (potential):**
- Add file complexity metrics (cyclomatic complexity)
- Detect unused scripts (no imports, no git history)
- Generate dependency graph (which scripts call which)
- Include test coverage % for each script

---


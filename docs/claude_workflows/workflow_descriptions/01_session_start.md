## 🚀 Session Start Workflow (Every Session)

### 1. Initialize Session (AUTOMATIC - Don't Ask)
```bash
bash scripts/shell/session_manager.sh start
```

**What this does:**
- ✅ Checks system diagnostics (hardware, software, environment)
- ✅ Reviews git status and recent commits
- ✅ Identifies documentation status (stale docs, pending tasks)
- ✅ Sources command logging functions
- ✅ **NEW:** Verifies NBA simulator credentials loaded
- ✅ **NEW:** Auto-checks overnight scraper jobs (if applicable)
- ✅ **NEW:** Displays session context summary (last session, next task, pending commits)
- ✅ **NEW:** DIMS verification (Data Inventory Management System - checks metric drift)

**Note:** Path is `scripts/shell/session_manager.sh` (not `scripts/session_manager.sh`)

**Output includes:**
- Hardware/system info
- Git status and recent commits
- Documentation age checks
- **Credentials status:** ✅ or ⚠️
- **Overnight jobs status:** Running/completed/N/A (auto-detected from PROGRESS.md)
- **Session context:** Last session date, last completed work, next planned task, pending commits

**Show output to user - no need to separately read PROGRESS.md for orientation**

### 1.5. Standalone Health Check (OPTIONAL - Deep System Verification)

**Purpose:** Comprehensive 14-point system health verification for troubleshooting or fresh environment setup

**When to use:**
- Setting up fresh development environment
- After system updates/upgrades
- Troubleshooting environment issues
- Monthly comprehensive verification
- When `session_manager.sh` reports issues

**Script:** `scripts/shell/check_machine_health.sh`

**Usage:**
```bash
bash scripts/shell/check_machine_health.sh
```

**What this checks (14 comprehensive categories):**

#### 1️⃣ System Information
```bash
# Displays:
- macOS version (sw_vers)
- Device model (MacBook Pro 16-inch, 2023)
- Processor (Apple M2 Max)
- Memory (96 GB)
- Storage availability
```

#### 2️⃣ Disk Space
```bash
# Thresholds:
- >90% usage → ❌ FAIL (critical)
- >80% usage → ⚠️  WARN (high)
- <80% usage → ✅ PASS

# Displays available space and usage percentage
```

#### 3️⃣ Homebrew
```bash
# Checks:
- ✅ Homebrew installed
- ✅ Correct location (/opt/homebrew/bin/brew for Apple Silicon)
- ℹ️  Outdated packages count
- Recommends: brew upgrade if packages outdated
```

#### 4️⃣ Miniconda
```bash
# Checks:
- ✅ Conda installed and version
- ✅ Conda base directory
- ✅ nba-aws environment exists
```

#### 5️⃣ Python Environment (nba-aws)
```bash
# Activates nba-aws environment and checks:
- ✅ Python 3.11 (required for AWS Glue 4.0)
- ✅ Python location in conda env
- ✅ Package count (warns if <50 packages)
```

#### 6️⃣ Core Python Packages
**Verifies 10 required packages:**
```python
REQUIRED_PACKAGES = [
    "boto3",          # AWS SDK
    "pandas",         # Data manipulation
    "numpy",          # Numerical computing
    "psycopg2-binary", # PostgreSQL driver
    "sqlalchemy",     # ORM
    "pytest",         # Testing
    "jupyter",        # Notebooks
    "python-dotenv",  # Environment variables
    "pyyaml",         # YAML parsing
    "tqdm"            # Progress bars
]

# Shows version for each installed package
# ❌ Fails if any missing
```

#### 7️⃣ AWS CLI
```bash
# Checks:
- ✅ AWS CLI installed and version
- ✅ Correct location (/opt/homebrew/bin/aws)
- ✅ ~/.aws/credentials exists with permissions 600
- ✅ S3 connectivity test (ls s3://nba-sim-raw-data-lake/)

# Warns if:
- Credentials file has wrong permissions
- Cannot connect to S3 bucket
```

#### 8️⃣ Git
```bash
# Checks:
- ✅ Git installed and version
- ✅ GitHub SSH authentication (ssh -T git@github.com)
- ✅ Git user.name and user.email configured globally
```

#### 9️⃣ Project Files
**Verifies project structure:**
```bash
CRITICAL_FILES = [
    "requirements.txt",
    "Makefile",
    "CLAUDE.md",
    "PROGRESS.md",
    "README.md",
    "COMMAND_LOG.md"
]

DOC_FILES = [
    "docs/STYLE_GUIDE.md",
    "docs/TROUBLESHOOTING.md",
    "docs/SETUP.md"
]

REQUIRED_DIRS = [
    "scripts/",
    "sql/",
    "docs/",
    "config/"
]

# ❌ Fails if critical files missing
# ⚠️  Warns if doc files or .env missing
```

#### 🔟 Data Directory
```bash
# Checks local data directory:
DATA_ROOT = "/Users/ryanranft/0espn/data/nba"

# Counts JSON files (may take time for 146K files)
- ✅ PASS: >140,000 files
- ⚠️  WARN: 100,000-140,000 files
- ❌ FAIL: <100,000 files

# ⚠️  Warns if directory not found (okay if data in S3)
```

#### 1️⃣1️⃣ Network & AWS Connectivity
```bash
# Checks:
- ✅ Internet connectivity (ping 8.8.8.8)
- ✅ AWS S3 endpoint reachable (ping s3.us-east-1.amazonaws.com)
- ✅ DNS resolution working (nslookup)
```

#### 1️⃣2️⃣ Security Settings
```bash
# Checks:
- ✅ System Integrity Protection (SIP) enabled
- ✅ FileVault disk encryption enabled
- ✅ SSH private key permissions 600 (checks id_rsa or id_ed25519)
```

#### 1️⃣3️⃣ System Resources
```bash
# Monitors:
- Free memory (warns if <1 GB)
- CPU idle percentage
```

#### 1️⃣4️⃣ Optional Tools
**Checks availability (not required):**
```bash
OPTIONAL_TOOLS = [
    "jq - JSON processor",
    "psql - PostgreSQL client",
    "tree - Directory viewer",
    "tmux - Terminal multiplexer"
]

# ⚠️  Shows as optional if not installed
```

**Sample Output:**
```
╔════════════════════════════════════════════════════════════════╗
║  NBA Simulator AWS - Machine Health Check                     ║
║  Date: 2025-10-02 19:45:23                                     ║
╚════════════════════════════════════════════════════════════════╝

1️⃣  SYSTEM INFORMATION
─────────────────────────────────────
    ProductName:		macOS
    ProductVersion:		14.6
    BuildVersion:		23G93

    Device: MacBook Pro 16-inch, 2023
    Processor: Apple M2 Max
    Memory: 96 GB
    Storage: 450 GB available of 1 TB

────────────────────────────────────────────────────────────────

2️⃣  DISK SPACE
─────────────────────────────────────
    Available: 450 GB
    Usage: 55%
✅ Disk space OK

────────────────────────────────────────────────────────────────

3️⃣  HOMEBREW
─────────────────────────────────────
    Version: Homebrew 4.3.15
    Location: /opt/homebrew/bin/brew
✅ Homebrew installed correctly (Apple Silicon)
ℹ️  3 outdated packages (run 'brew upgrade')

────────────────────────────────────────────────────────────────

4️⃣  MINICONDA
─────────────────────────────────────
    Version: conda 24.7.1
    Base: /Users/ryanranft/miniconda3
✅ Conda installed
✅ nba-aws environment exists

────────────────────────────────────────────────────────────────

5️⃣  PYTHON ENVIRONMENT (nba-aws)
─────────────────────────────────────
    Version: Python 3.11.9
    Location: /Users/ryanranft/miniconda3/envs/nba-aws/bin/python
✅ Python 3.11 (required for AWS Glue 4.0)
    Packages installed: 127
✅ Packages installed

────────────────────────────────────────────────────────────────

6️⃣  CORE PYTHON PACKAGES
─────────────────────────────────────
    ✅ boto3 (1.34.162)
    ✅ pandas (2.2.2)
    ✅ numpy (2.0.1)
    ✅ psycopg2-binary (2.9.9)
    ✅ sqlalchemy (2.0.32)
    ✅ pytest (8.3.2)
    ✅ jupyter (1.1.1)
    ✅ python-dotenv (1.0.1)
    ✅ pyyaml (6.0.2)
    ✅ tqdm (4.66.5)

────────────────────────────────────────────────────────────────

[... continues through all 14 checks ...]

╔════════════════════════════════════════════════════════════════╗
║  HEALTH CHECK SUMMARY                                          ║
╚════════════════════════════════════════════════════════════════╝

✅ ALL CHECKS PASSED - System ready for development

Next steps:
  1. Run: cd /Users/ryanranft/nba-simulator-aws
  2. Run: conda activate nba-aws
  3. Run: make verify-all (for additional checks)

Health check completed at 2025-10-02 19:45:45
```

**Exit Codes:**
- `0` - All checks passed (system healthy)
- `1` - One or more checks failed (review errors)

**Comparison to session_manager.sh:**

| Feature | session_manager.sh | check_machine_health.sh |
|---------|-------------------|-------------------------|
| **Scope** | Quick session start check | Comprehensive system verification |
| **Categories** | 6 quick checks | 14 detailed checks |
| **Runtime** | <2 seconds | 5-15 seconds (file counting) |
| **Package verification** | Basic (counts) | Detailed (10 required packages) |
| **Network tests** | No | Yes (ping, DNS, S3) |
| **Security checks** | Basic | Detailed (SIP, FileVault, SSH perms) |
| **Data verification** | No | Yes (counts local JSON files) |
| **Optional tools** | No | Yes (jq, psql, tree, tmux) |
| **Exit code** | Informational | Pass/Fail (usable in scripts) |
| **When to use** | Every session start | Troubleshooting, fresh setup |

**When to Use Each:**

**Use `session_manager.sh start` (Step 1):**
- ✅ Every session start (automatic)
- ✅ Quick orientation check
- ✅ Sources command logging functions
- ✅ Fast (<2 sec)

**Use `check_machine_health.sh`:**
- ✅ Setting up fresh environment
- ✅ After macOS/Homebrew updates
- ✅ Troubleshooting "it works on my machine" issues
- ✅ Monthly comprehensive verification
- ✅ When session_manager reports problems
- ✅ Before major deployments
- ✅ After installing new packages/tools

**Troubleshooting with Health Check:**

If health check fails, common fixes:

```bash
# Missing packages
pip install -r requirements.txt

# AWS credentials issues
aws configure
chmod 600 ~/.aws/credentials

# Git configuration
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Conda environment
conda env create -f environment.yml
conda activate nba-aws

# Disk space issues
# Clean conda caches:
conda clean --all

# Clean Homebrew:
brew cleanup

# Archive old data:
bash scripts/maintenance/archive_manager.sh full
```

**Integration Points:**
- **Session Start Workflow Step 1.5:** Deep verification alternative (this location)
- **Environment Setup Workflow:** Run after Step 12 to verify all components
- **Troubleshooting Workflow Step 1:** First diagnostic tool
- **Monthly Maintenance:** Part of comprehensive review checklist

**Best Practices:**
1. ✅ Run before starting major work after system changes
2. ✅ Run if session_manager.sh shows warnings
3. ✅ Save output for comparison: `bash check_machine_health.sh > health_check.log`
4. ✅ Re-run after fixing failures to verify fixes worked
5. ✅ Include in onboarding checklist for new team members

### 2. Orient to Current State (AUTOMATIC - Don't Ask)

**Session manager now provides all context automatically!**

Previously required reading PROGRESS.md separately - now all context displayed in session output:
- ✅ Last session date/time
- ✅ Last completed work
- ✅ Overnight jobs status (if applicable)
- ✅ Pending commits count
- ✅ Next planned task

**Only read PROGRESS.md if user asks specific questions not answered by session summary.**

### 3. Ask User One Focused Question (AUTOMATIC - Always Ask)

"What did you complete since last session? (or 'none' to continue where we left off)"

**Why this matters:**
- User may have worked between sessions
- Claude needs to know what's already done to avoid duplicate work
- Updates context for accurate task selection

**After user responds:**
- If work was completed → Update PROGRESS.md status
- If "none" → Proceed with "Next planned task" from session summary

### 4. Offer Time-Based Maintenance (Conditional - Ask Only If Applicable)

**Note:** Steps 1-3 are AUTOMATIC (don't ask). Step 4 is CONDITIONAL (ask only if condition met).

- **If Monday or 7+ days since last update:** "Would you like me to run `make update-docs` for weekly maintenance?"
- **If 7+ days since last inventory:** "Should I run `make inventory` to update file summaries?"
- **If new AWS resources may exist:** "Should I run `make sync-progress` to check PROGRESS.md matches AWS?"
- **If .md files were modified:** "After these changes, should I run `make inventory` to update FILE_INVENTORY.md?"

### DIMS Integration

**DIMS (Data Inventory Management System)** runs automatically during session startup to verify project metrics.

**What DIMS checks:**
- S3 storage (object counts, size, hoopr files)
- Code metrics (Python files, test files, ML scripts)
- Documentation metrics (markdown files, size)
- SQL schemas, workflows, git metrics

**Manual DIMS operations:**
- Full verification: `python scripts/monitoring/dims_cli.py verify`
- Update metrics: `python scripts/monitoring/dims_cli.py verify --update`
- View trends: `python scripts/monitoring/dims_cli.py history METRIC_PATH --days 30`

**See:** Workflow #56 (`56_dims_management.md`) for complete DIMS documentation

---


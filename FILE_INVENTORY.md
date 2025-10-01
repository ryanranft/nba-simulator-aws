# FILE_INVENTORY.md

**Auto-generated:** 2025-10-01 18:23:25

**Purpose:** Comprehensive inventory of all project files with automatic summaries.

---

## Root Documentation

### .documentation-triggers.md

**Type:** Markdown documentation (180 lines)
**Last Modified:** 2025-10-01
**Purpose:** <!-- AUTO-UPDATE TRIGGER: When new documentation files are created OR trigger logic changes -->

### .session-history.md

**Type:** Markdown documentation (451 lines)
**Last Modified:** 2025-10-01
**Purpose:** <!-- AUTO-UPDATE TRIGGER: Run `bash scripts/shell/session_startup.sh >> .session-history.md` AFTER every commit -->

### CLAUDE.md

**Type:** Markdown documentation (773 lines)
**Last Modified:** 2025-10-01
**Purpose:** This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### COMMAND_LOG.example.md

**Type:** Markdown documentation (190 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Purpose:** This is an example template showing how to use the command logging system. Your actual COMMAND_LOG.md will contain real command outputs.

### COMMAND_LOG.md

**Type:** Markdown documentation (399 lines)
**Last Modified:** 2025-10-01
**Purpose:** <!-- AUTO-UPDATE TRIGGER: After EVERY code file creation/modification, failed command, or error resolution -->

### FILE_INVENTORY.md

**Type:** Markdown documentation (305 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Auto-generated:** 2025-10-01 18:15:06

### MACHINE_SPECS.md

**Type:** Markdown documentation (4474 lines)
**Last Modified:** 2025-10-01
**Purpose:** <!-- AUTO-UPDATE TRIGGER: Run session_startup.sh at start of EVERY session -->

### PROGRESS.md

**Type:** Markdown documentation (1127 lines)
**Last Modified:** 2025-10-01
**Purpose:** <!-- AUTO-UPDATE TRIGGER: After completing ANY task, mark ✅ COMPLETE immediately -->

### QUICKSTART.md

**Type:** Markdown documentation (234 lines)
**Last Modified:** 2025-10-01
**Purpose:** <!-- AUTO-UPDATE TRIGGER: When daily workflow changes (new commands, file locations, workflow shortcuts) -->

### README.md

**Type:** Markdown documentation (0 lines)
**Last Modified:** 2025-10-01
**Purpose:** No description available

---

## Scripts - AWS

### scripts/aws/check_costs.sh

**Type:** Bash script (184 lines)
**Last Modified:** 2025-10-01
**Purpose:** scripts/aws/check_costs.sh
**Key Functions:**
- `format_currency()`
**Dependencies:** AWS CLI
**Usage:** `./scripts/aws/check_costs.sh`

---

## Scripts - Shell Utilities

### scripts/shell/check_machine_health.sh

**Type:** Bash script (446 lines)
**Last Modified:** 2025-10-01
**Purpose:** Master health check script for NBA Simulator AWS project
**Key Functions:**
- `check_pass()`
- `check_fail()`
- `check_warn()`
- `check_info()`
- `separator()`
**Dependencies:** AWS CLI, PostgreSQL client, Conda, Git
**Usage:** `./scripts/shell/check_machine_health.sh`

### scripts/shell/log_command.sh

**Type:** Bash script (197 lines)
**Last Modified:** 2025-10-01
**Purpose:** log_command.sh
**Key Functions:**
- `get_category()`
- `get_description()`
- `log_cmd()`
- `log_note()`
- `log_solution()`
**Dependencies:** AWS CLI, PostgreSQL client, Conda, Git
**Usage:** `#   source scripts/shell/log_command.sh`

### scripts/shell/sanitize_command_log.sh

**Type:** Bash script (113 lines)
**Last Modified:** 2025-10-01
**Purpose:** sanitize_command_log.sh
**Usage:** `#   ./scripts/shell/sanitize_command_log.sh`

### scripts/shell/security_scan.sh

**Type:** Bash script (196 lines)
**Last Modified:** 2025-10-01
**Purpose:** Color codes
**Dependencies:** Git
**Usage:** `./scripts/shell/security_scan.sh`

### scripts/shell/session_startup.sh

**Type:** Bash script (125 lines)
**Last Modified:** 2025-10-01
**Purpose:** Session startup - Full diagnostics with concise output
**Dependencies:** AWS CLI, Conda, Git
**Usage:** `./scripts/shell/session_startup.sh`

### scripts/shell/setup_git_hooks.sh

**Type:** Bash script (146 lines)
**Last Modified:** 2025-10-01
**Purpose:** Setup Git Hooks for NBA Simulator AWS Project
**Key Functions:**
- `create_hook()`
**Dependencies:** AWS CLI, Conda, Git
**Usage:** `./scripts/shell/setup_git_hooks.sh`

### scripts/shell/verify_gitignore.sh

**Type:** Bash script (47 lines)
**Last Modified:** 2025-10-01
**Purpose:** verify_gitignore.sh
**Usage:** `./scripts/shell/verify_gitignore.sh`

---

## Scripts - Maintenance

### scripts/maintenance/generate_inventory.py

**Type:** Python script (341 lines)
**Last Modified:** 2025-09-30
**Purpose:** Automatically generate FILE_INVENTORY.md with summaries of all project files.
**Key Functions:**
- `FileInventory (class)`
**Dependencies:** subprocess
**Usage:** `python scripts/maintenance/generate_inventory.py`

### scripts/maintenance/sync_progress.py

**Type:** Python script (217 lines)
**Last Modified:** 2025-09-30
**Purpose:** Synchronize PROGRESS.md with actual project state.
**Key Functions:**
- `ProgressSync (class)`
**Dependencies:** subprocess
**Usage:** `python scripts/maintenance/sync_progress.py`

### scripts/maintenance/update_docs.sh

**Type:** Bash script (209 lines)
**Last Modified:** 2025-10-01
**Purpose:** scripts/maintenance/update_docs.sh
**Key Functions:**
- `update_section()`
**Dependencies:** AWS CLI, Git
**Usage:** `./scripts/maintenance/update_docs.sh`

---

## Documentation

### docs/COMMAND_LOG_SANITIZATION.md

**Type:** Markdown documentation (235 lines)
**Last Modified:** 2025-10-01
**Purpose:** This project includes an automated sanitization system that removes sensitive information from `COMMAND_LOG.md` before Git commits.

### docs/DOCUMENTATION_MAINTENANCE.md

**Type:** Markdown documentation (439 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Purpose:** Keep documentation synchronized with actual project state

### docs/SETUP.md

**Type:** Markdown documentation (556 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Project:** NBA Game Simulator & ML Platform

### docs/STYLE_GUIDE.md

**Type:** Markdown documentation (846 lines)
**Last Modified:** 2025-10-01
**Purpose:** <!-- AUTO-UPDATE TRIGGER: When code style pattern used 3+ times (establishes precedent) -->

### docs/TESTING.md

**Type:** Markdown documentation (760 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Project:** NBA Game Simulator & ML Platform

### docs/TROUBLESHOOTING.md

**Type:** Markdown documentation (1025 lines)
**Last Modified:** 2025-10-01
**Purpose:** <!-- AUTO-UPDATE TRIGGER: After solving new error that took >10 minutes OR has non-obvious solution -->

### docs/adr/README.md

**Type:** Markdown documentation (199 lines)
**Last Modified:** 2025-10-01
**Purpose:** This directory contains Architecture Decision Records for the NBA Game Simulator & ML Platform project.

### docs/adr/template.md

**Type:** Markdown documentation (116 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Date:** YYYY-MM-DD

---

## Architecture Decision Records

### docs/adr/001-redshift-exclusion.md

**Type:** Markdown documentation (165 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Date:** September 29, 2025

### docs/adr/002-data-extraction-strategy.md

**Type:** Markdown documentation (262 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Date:** September 29, 2025

### docs/adr/003-python-version.md

**Type:** Markdown documentation (249 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Date:** September 29, 2025

### docs/adr/004-git-without-github-push.md

**Type:** Markdown documentation (114 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Date:** September 30, 2025

### docs/adr/005-git-ssh-authentication.md

**Type:** Markdown documentation (320 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Date:** September 30, 2025

### docs/adr/006-session-initialization-automation.md

**Type:** Markdown documentation (195 lines)
**Last Modified:** 2025-10-01
**Purpose:** **Date:** 2025-10-01

---

## Configuration

### .env.example

**Type:** EXAMPLE file (190 lines)
**Last Modified:** 2025-10-01
**Purpose:** No description available

### Makefile

**Type:** File (205 lines)
**Last Modified:** 2025-09-30
**Purpose:** No description available

---

## Summary Statistics

**Total files documented:** 37
**Total lines of code/docs:** 16,230

**Files by type:**
- Markdown documentation: 24
- Bash script: 9
- Python script: 2
- File: 1
- EXAMPLE file: 1

---

**Note:** This file is auto-generated. To update, run: `make inventory`

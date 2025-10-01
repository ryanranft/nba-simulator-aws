# FILE_INVENTORY.md

**Auto-generated:** 2025-09-30 20:22:47

**Purpose:** Comprehensive inventory of all project files with automatic summaries.

---

## Root Documentation

### CLAUDE.md

**Type:** Markdown documentation (426 lines)
**Last Modified:** 2025-09-30
**Purpose:** This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### COMMAND_LOG.example.md

**Type:** Markdown documentation (190 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Purpose:** This is an example template showing how to use the command logging system. Your actual COMMAND_LOG.md will contain real command outputs.

### COMMAND_LOG.md

**Type:** Markdown documentation (198 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Purpose:** Track all terminal commands executed during project development, including outputs, errors, and solutions. This log helps future LLM instances learn from past mistakes and successes.

### FILE_INVENTORY.md

**Type:** Markdown documentation (243 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Auto-generated:** 2025-09-30 20:13:29

### PROGRESS.md

**Type:** Markdown documentation (1122 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Date Started:** September 29, 2025

### QUICKSTART.md

**Type:** Markdown documentation (229 lines)
**Last Modified:** 2025-09-30
**Purpose:** **One-page reference for common tasks**

### README.md

**Type:** Markdown documentation (0 lines)
**Last Modified:** 2025-09-30
**Purpose:** No description available

---

## Scripts - AWS

### scripts/aws/check_costs.sh

**Type:** Bash script (184 lines)
**Last Modified:** 2025-09-30
**Purpose:** scripts/aws/check_costs.sh
**Key Functions:**
- `format_currency()`
**Dependencies:** AWS CLI
**Usage:** `./scripts/aws/check_costs.sh`

---

## Scripts - Shell Utilities

### scripts/shell/log_command.sh

**Type:** Bash script (197 lines)
**Last Modified:** 2025-09-30
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
**Last Modified:** 2025-09-30
**Purpose:** sanitize_command_log.sh
**Usage:** `#   ./scripts/shell/sanitize_command_log.sh`

### scripts/shell/verify_setup.sh

**Type:** Bash script (170 lines)
**Last Modified:** 2025-09-30
**Purpose:** scripts/shell/verify_setup.sh
**Key Functions:**
- `check_command()`
- `check_version()`
**Dependencies:** AWS CLI, Conda, Git
**Usage:** `./scripts/shell/verify_setup.sh`

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
**Last Modified:** 2025-09-30
**Purpose:** scripts/maintenance/update_docs.sh
**Key Functions:**
- `update_section()`
**Dependencies:** AWS CLI, Git
**Usage:** `./scripts/maintenance/update_docs.sh`

---

## Documentation

### docs/COMMAND_LOG_SANITIZATION.md

**Type:** Markdown documentation (235 lines)
**Last Modified:** 2025-09-30
**Purpose:** This project includes an automated sanitization system that removes sensitive information from `COMMAND_LOG.md` before Git commits.

### docs/DOCUMENTATION_MAINTENANCE.md

**Type:** Markdown documentation (439 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Purpose:** Keep documentation synchronized with actual project state

### docs/SETUP.md

**Type:** Markdown documentation (492 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Project:** NBA Game Simulator & ML Platform

### docs/STYLE_GUIDE.md

**Type:** Markdown documentation (841 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Project:** NBA Game Simulator & ML Platform

### docs/TESTING.md

**Type:** Markdown documentation (760 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Project:** NBA Game Simulator & ML Platform

### docs/TROUBLESHOOTING.md

**Type:** Markdown documentation (981 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Project:** NBA Game Simulator & ML Platform

### docs/adr/README.md

**Type:** Markdown documentation (194 lines)
**Last Modified:** 2025-09-30
**Purpose:** This directory contains Architecture Decision Records for the NBA Game Simulator & ML Platform project.

### docs/adr/template.md

**Type:** Markdown documentation (116 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Date:** YYYY-MM-DD

---

## Architecture Decision Records

### docs/adr/001-redshift-exclusion.md

**Type:** Markdown documentation (165 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Date:** September 29, 2025

### docs/adr/002-data-extraction-strategy.md

**Type:** Markdown documentation (262 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Date:** September 29, 2025

### docs/adr/003-python-version.md

**Type:** Markdown documentation (249 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Date:** September 29, 2025

### docs/adr/005-git-ssh-authentication.md

**Type:** Markdown documentation (320 lines)
**Last Modified:** 2025-09-30
**Purpose:** **Date:** September 30, 2025

---

## Configuration

### .env.example

**Type:** EXAMPLE file (190 lines)
**Last Modified:** 2025-09-30
**Purpose:** No description available

### Makefile

**Type:** File (205 lines)
**Last Modified:** 2025-09-30
**Purpose:** No description available

---

## Summary Statistics

**Total files documented:** 28
**Total lines of code/docs:** 9,288

**Files by type:**
- Markdown documentation: 19
- Bash script: 5
- Python script: 2
- File: 1
- EXAMPLE file: 1

---

**Note:** This file is auto-generated. To update, run: `make inventory`

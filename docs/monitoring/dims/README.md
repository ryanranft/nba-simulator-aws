# DIMS - Data Inventory Management System

**Version:** 3.1.0
**Status:** ✅ Production Ready
**Location:** `docs/monitoring/dims/`

---

## Quick Start

DIMS is a comprehensive data inventory and verification system for the NBA Temporal Panel Data System.

**Features:**
- PostgreSQL-backed metrics history
- Event-driven updates (git hooks, S3 uploads, cron)
- 3-tier approval workflow for critical metrics
- Interactive Jupyter notebook for exploration
- CLI for metrics verification and updates
- Integration with 5 existing data workflows

---

## Documentation Index

### Core Documentation

1. **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Phase 1: Foundational implementation
   - Metrics configuration system
   - YAML-based metric definitions
   - CLI tool development
   - Initial verification framework

2. **[PHASE_2_SUMMARY.md](PHASE_2_SUMMARY.md)** - PostgreSQL backend integration
   - Database schema (4 tables)
   - Event-driven architecture
   - Approval workflow
   - Historical metrics tracking

3. **[PHASE_3_SUMMARY.md](PHASE_3_SUMMARY.md)** - Jupyter notebook integration
   - Interactive exploration
   - 12 analysis sections (46 cells)
   - Trend visualization
   - Excel export capability

4. **[WORKFLOW_INTEGRATION_SUMMARY.md](WORKFLOW_INTEGRATION_SUMMARY.md)** - Integration with existing workflows
   - Workflow #13: File Inventory
   - Workflow #45: Local Data Inventory
   - Workflow #46: Data Gap Analysis
   - Workflow #47: AWS Data Inventory
   - Workflow #49: Automated Data Audit

### User Guides

5. **[JUPYTER_GUIDE.md](JUPYTER_GUIDE.md)** - Jupyter notebook usage guide
   - How to launch and use the interactive notebook
   - Example queries and visualizations
   - Custom analysis patterns

6. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - CLI command reference
   - Quick command examples
   - Common verification tasks
   - Troubleshooting tips

---

## Quick Start Commands

### Basic Verification
```bash
# Verify all metrics
python scripts/monitoring/dims_cli.py verify

# Update metrics history
python scripts/monitoring/dims_cli.py verify --update

# Run specific workflow
python scripts/monitoring/dims_cli.py workflow sync-status
```

### Interactive Analysis
```bash
# Launch Jupyter notebook
python scripts/monitoring/dims_cli.py notebook

# Then navigate to: notebooks/dims_explorer.ipynb
```

### Export Reports
```bash
# From Jupyter notebook (Section 12, last cell)
# Exports all workflow results to Excel with multiple sheets
```

---

## System Architecture

**Configuration:** `inventory/config.yaml`
**CLI Tool:** `scripts/monitoring/dims_cli.py`
**Core Modules:** `scripts/monitoring/dims/`
**Jupyter Notebook:** `notebooks/dims_explorer.ipynb`
**Database Tables:**
- `dims_metrics_history` - Historical metric values
- `dims_verification_runs` - Verification execution log
- `dims_approval_requests` - Critical changes requiring approval
- `dims_event_log` - Event-driven update history

---

## Metrics Tracked

**40+ metrics across 11 categories:**
- S3 Storage (objects, size, specific file counts)
- Prediction System (code lines, components)
- Plus/Minus System (implementation size)
- Code Base (Python files, ML scripts, tests)
- Documentation (markdown files, size)
- Git (book recommendation commits)
- Workflows (total workflow files)
- SQL Schemas (schema line counts)
- Local Data (archives, temp data)
- File Inventory (documented files, age)
- AWS Inventory (RDS size, cost estimates)
- Data Gaps (missing games, PBP gaps)
- Sync Status (local vs S3 drift)

---

## Event-Driven Updates

**Automatic metric updates triggered by:**
- `git post-commit` - Updates code/doc metrics
- `s3_upload_complete` - Updates S3 metrics
- `scraper_complete` - Runs gap analysis and sync check
- `monthly_audit` (cron: 0 0 1 * *) - Comprehensive audit
- `daily_sync_check` (cron: 0 9 * * *) - Daily sync verification

---

## Approval Workflow

**Critical metrics requiring approval (15% drift threshold):**
- AWS cost estimate changes
- Data gap increases
- Sync status changes
- Large storage changes
- S3 object count changes

---

## Navigation

**Return to:** [Monitoring Documentation](../)
**Parent:** [Main Documentation Index](../../README.md)
**Related:**
- [Scraper Monitoring](../../SCRAPER_MONITORING_SYSTEM.md)
- [Workflow Descriptions](../../claude_workflows/workflow_descriptions/)
- [Phase Documentation](../../phases/)

---

**Last Updated:** October 21, 2025
**Maintainer:** DIMS Development Team
**Support:** See workflow descriptions for detailed usage
